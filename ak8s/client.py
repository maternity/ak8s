#   Copyright 2018 Kai Groner
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import ssl
from urllib.parse import urljoin

import aiohttp
import yaml

from .apis import APIRegistry
from .models import ModelBase


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', metavar='SPEC')
    parser.add_argument('kubeconfig', metavar='KUBECONFIG', nargs='?')
    args = parser.parse_args()

    registry = APIRegistry()
    registry.load_spec(args.spec)

    async with AK8sClient.from_kubeconfig(
            args.kubeconfig,
            registry=registry) as ak8s:
        apis = ak8s.bind_api_group(registry.apis)

        async for ev, obj in apis.core_v1.watch_pod_list_for_all_namespaces(
                includeUninitialized=True):
            print(ev, f'{obj.metadata.name:55}  {obj.metadata.namespace:20}  {obj.status.phase}')


class AK8sClient:
    def __init__(
            self, url, *,
            ca_file,
            client_cert_file,
            client_key_file,
            registry):
        sslcontext = ssl.create_default_context(cafile=ca_file)
        sslcontext.load_cert_chain(client_cert_file, client_key_file)
        self._url = url
        self._sslcontext = sslcontext
        self._session = None
        self._models = registry.models_by_gvk
        self._logger = logging.getLogger(self.__class__.__qualname__)

    #TODO: service account config

    # > Accessing the API from a Pod
    # >
    # > When accessing the API from a pod, locating and
    # > authenticating to the apiserver are somewhat different.
    # >
    # > The recommended way to locate the apiserver within the pod
    # > is with the kubernetes DNS name, which resolves to a
    # > Service IP which in turn will be routed to an apiserver.
    # >
    # > The recommended way to authenticate to the apiserver is
    # > with a service account credential. By kube-system, a pod is
    # > associated with a service account, and a credential (token)
    # > for that service account is placed into the filesystem tree
    # > of each container in that pod, at
    # > /var/run/secrets/kubernetes.io/serviceaccount/token.
    # >
    # > If available, a certificate bundle is placed into the
    # > filesystem tree of each container at
    # > /var/run/secrets/kubernetes.io/serviceaccount/ca.crt, and
    # > should be used to verify the serving certificate of the
    # > apiserver.
    # >
    # > Finally, the default namespace to be used for namespaced
    # > API operations is placed in a file at
    # > /var/run/secrets/kubernetes.io/serviceaccount/namespace in
    # > each container.

    @classmethod
    def from_kubeconfig(cls, kubeconfig=None, context=None, **kw):
        if kubeconfig is None:
            kubeconfig = os.environ.get('KUBECONFIG')
            if kubeconfig is None:
                kubeconfig = Path.home().joinpath('.kube/config')

        kubeconfig = Path(kubeconfig)

        with kubeconfig.open() as fh:
            doc = yaml.safe_load(fh)

        if context is None:
            context = doc['current-context']

        for d in doc['contexts']:
            if d['name'] == context:
                ctx = d['context']
                break
        else:
            raise RuntimeError(f'Context {context} was not found in {kubeconfig}')

        for d in doc['clusters']:
            if d['name'] == ctx['cluster']:
                cluster = d['cluster']
                break
        else:
            raise RuntimeError(f'Cluster {ctx["cluster"]} was not found in {kubeconfig}')

        for d in doc['users']:
            if d['name'] == ctx['user']:
                user = d['user']
                break
        else:
            raise RuntimeError(f'User {ctx["user"]} was not found in {kubeconfig}')

        return cls(
                cluster['server'],
                ca_file=kubeconfig.parent/cluster['certificate-authority'],
                client_cert_file=kubeconfig.parent/user['client-certificate'],
                client_key_file=kubeconfig.parent/user['client-key'],
                **kw)

    async def __aenter__(self):
        self._session = await aiohttp.ClientSession(
                conn_timeout=60).__aenter__()
        return self

    async def __aexit__(self, *exc):
        await self._session.__aexit__(*exc)
        self._session = None

    def bind_api_group(self, api_group):
        return AK8sClientAPIGroupBinding(self, api_group)

    async def op(self, op):
        body, headers = None, {}

        if op.body is not None:
            body = ak8s_payload(op.body)

        if 'application/json' in op.produces:
            headers['accept'] = 'application/json'

        url = urljoin(self._url, op.uri)

        self._logger.debug('%(method)s %(path)s', dict(method=op.method, path=op.uri))

        async with self._session.request(
                op.method, url,
                headers=headers,
                data=body,
                ssl_context=self._sslcontext) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if resp.content_type == 'application/json':
                    e.detail = self._load_model(await resp.json())
                    #from pprint import pprint
                    #pprint(e.detail)
                    if e.detail.reason == 'NotFound':
                        raise AK8sNotFound(e.detail) from None
                raise

            if resp.content_type == 'application/json':
                return self._load_model(await resp.json())

            if resp.content_type == 'text/plain':
                return resp.text()

            raise NotImplementedError(f'What do with resp={resp} to op={op}')

        self._logger.debug('end %(method)s %(path)s', dict(method=op.method, path=op.uri))

    async def stream_op(self, op):
        headers = {}

        if 'application/json;stream=watch' in op.produces:
            headers['accept'] = 'application/json;stream=watch'

        url = urljoin(self._url, op.uri)

        self._logger.debug('%(method)s %(path)s', dict(method=op.method, path=op.uri))

        async with self._session.request(
                op.method, url,
                headers=headers,
                timeout=None,
                ssl_context=self._sslcontext) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if resp.content_type == 'application/json':
                    e.detail = self._load_model(await resp.json())
                    #from pprint import pprint
                    #pprint(e.detail)
                    if e.detail.reason == 'NotFound':
                        raise AK8sNotFound(e.detail) from None
                raise

            if resp.content_type == 'application/json':
                async for line in resp.content:
                    ev = json.loads(line)
                    type_ = ev['type']
                    data = ev.get('object')
                    if data is not None:
                        obj = self._load_model(data)
                        yield type_, obj
                    else:
                        yield type_, None
                self._logger.debug('end %(method)s %(path)s',
                        dict(method=op.method, path=op.uri))
                return

            elif resp.content_type == 'text/plain':
                # async yield from, where are you?
                async for line in resp.content:
                    yield line
                self._logger.debug('end %(method)s %(path)s',
                        dict(method=op.method, path=op.uri))
                return

        raise NotImplementedError(f'What do with resp={resp} to op={op}')

    async def watch(self, op):
        if not op.stream:
            raise ValueError(f'Cannot watch {op}')

        # The k8s documentation on concurrency and consistency has a bunch of
        # caveats about treating resourceVersion opaquely.
        # From https://git.k8s.io/community/contributors/devel/api-conventions.md#concurrency-control-and-consistency
        # """
        # Clients should not assume that the resource version has meaning
        # across namespaces, different kinds of resources, or different
        # servers.
        # """
        # In order to use the watch APIs, it seems we have to violate this
        # somewhat.  Although list endpoints use list types that have a
        # collective resourceVersion, when watch=True that endpoint returns
        # watch events for each record.  The initial batch of events has no
        # particular order, so we need to select the greatest one to continue
        # from when the current request times out or ends.  This means we are
        # potentially comparing resources across namespaces.  The document does
        # hint that versions are used for ordering, but it makes no guarantee
        # that they can be compared, numerically, lexicographically, or
        # otherwise.  For the moment, versions are just an etcd serial, but
        # this potentially breaks if sharding is implemented, or possibly with
        # federation (if different regions have different etcd clusters).  I
        # suspect k8s will address this at some point, and likely some API
        # changes will result.  It's notable that `kubectl get -w` does not
        # implement retries, so it may be that k8s does not think these
        # continuations are supportable at all.
        #
        # And I just figured out that the openapi spec (swagger 2.0) is what I
        # should be using instaed of the 1.2 spec.  We'll use the 1.2 spec for
        # now, but the 2.0 spec should provide a bit more structure, as well as
        # useful names for api groups (from tags).

        last_version = op.args.get('resourceVersion') or None
        too_old_version = None

        while True:
            if last_version:
                if too_old_version and last_version == too_old_version:
                    last_version = None
                op = op.replace(resourceVersion=last_version)

            try:
                async for ev, obj in self.stream_op(op):
                    if ev == 'ERROR':
                        if obj.status == 'Failure' and obj.reason == 'Gone':
                            # too old resource version
                            # In this situation, either there is a newer
                            # version or there isn't.  If there isn't a newer
                            # version, then the error seems to be bogus.  If
                            # there is a newer version, then the error means we
                            # might miss continuity.  Either way, we should
                            # resume from whatever is current.
                            too_old_version = last_version
                            self._logger.debug(
                                    'Restarting %r because version '
                                    '%r is too old',
                                    op.uri, last_version)
                            break
                        self._logger.error('Watch %r: %s', op.uri, obj.message)

                    else:
                        if not last_version or int(obj.metadata.resourceVersion) > int(last_version):
                            last_version = obj.metadata.resourceVersion

                        # I think the first event will always be 'ADDED', but
                        # I'm not sure.
                        if ev == 'ADDED' and too_old_version and int(obj.metadata.resourceVersion) <= int(too_old_version):
                            # If the resource version is too old and we had to
                            # resume without, then discard the repeat events.
                            continue

                    yield ev, obj

            except asyncio.TimeoutError:
                pass # retry

            except aiohttp.ClientPayloadError as err:
                self._logger.exception('Watch %r', op.uri)
                await asyncio.sleep(1) # retry

    def _model_for_kind(self, data):
        group, _, version = data['apiVersion'].rpartition('/')
        kind = data['kind']
        return self._models[group, version, kind]

    def _load_model(self, data):
        model = self._model_for_kind(data)
        return model._project(data)


class AK8sClientAPIGroupBinding:
    def __init__(self, ak8s, api_group):
        self._ak8s = ak8s
        self._api_group = api_group

    def __getattr__(self, k):
        api = getattr(self._api_group, k)
        if callable(api):
            return AK8sClientAPIBinding(self._ak8s, api)
        return self.__class__(self._ak8s, api)

    def __dir__(self):
        yield from dir(self._api_group)


class AK8sClientAPIBinding:
    __slots__ = ('_ak8s', '_api', '_method')

    def __init__(self, ak8s, api, method=None):
        self._ak8s = ak8s
        self._api = api
        self._method = method

    def __call__(self, *a, **kw):
        op = self._api(*a, **kw)
        if self._method is not None:
            method = getattr(self._ak8s, self._method)
        elif op.stream:
            method = self._ak8s.stream_op
        else:
            method = self._ak8s.op
        return method(op)

    @property
    def __doc__(self):
        return self._api.__doc__

    @property
    def __signature__(self):
        return self._api.__signature__

    def __getattr__(self, k):
        if hasattr(self._ak8s, k):
            return self.__class__(self._ak8s, self._api, k)
        raise AttributeError(k)


class AK8sNotFound(Exception):
    def __init__(self, detail):
        self.detail = detail

    def __str__(self):
        return self.detail.message


def ak8s_payload(obj, content_type='application/json'):
    if isinstance(obj, ModelBase):
        return aiohttp.JsonPayload(obj._data, content_type=content_type)
    raise TypeError(f'unsupported type for ak8s_payload: {obj.__class__}')


if __name__ == '__main__':
    try:
        exit(asyncio.get_event_loop().run_until_complete(main()) or 0)

    except KeyboardInterrupt as e:
        exit(1)
