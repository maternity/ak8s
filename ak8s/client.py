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

import asyncio
import os
import ssl

import aiohttp
import yaml


class AK8sClient:
    def __init__(self, url, *, ca_file, client_cert_file, client_key_file):
        sslcontext = ssl.create_default_context(cafile=ca_file)
        sslcontext.load_cert_chain(cert_file, key_file)
        self._url = url
        self._sslcontext = sslcontext
        self._session = None

    async def __aenter__(self):
        self._session = await aiohttp.ClientSession().__aenter__()
        return self

    async def __aexit__(self, *exc):
        await self._session.__aexit__(*exc)
        self._session = None

    async def op(self, op):
        if op.body is not None:
            headers, body = op.body_as('application/json')
        else:
            headers, body = {}, None

        if op.response_model:
            headers['accept'] = 'application/json'

        async with self._session.request(
                op.method,
                urljoin(self._url, op.uri),
                headers=headers,
                data=body,
                ssl_context=self._sslcontext) as resp:
            resp.raise_for_status()

            if op.response_model:
                if resp.content_type == 'application/json':
                    data = await resp.json()
                    return resp.response_model._project(data)

            if resp.content_type == 'text/plain':
                return resp.text()

            raise NotImplementedError(f'What do with resp={resp} to op={op}')

    async def watch(self, op):
        raise NotImplementedError('going to want this soon')

    @classmethod
    def from_kubeconfig(cls, fn=None, context=None):
        if fn is None:
            fn = os.get('KUBECONFIG') or Path.home().joinpath('.kube/config')

        with open(fn) as fh:
            doc = yaml.load_safe(fh)

        if context is None:
            context = doc['current-context']

        for d in doc['contexts']:
            if d['name'] == context:
                ctx = d['context']
                break
        else:
            raise RuntimeError(f'Context {context} was not found in {fn}')

        for d in doc['clusters']:
            if d['name'] == ctx['cluster']:
                cluster = d['cluster']
                break
        else:
            raise RuntimeError(f'Cluster {ctx["cluster"]} was not found in {fn}')

        for d in doc['users']:
            if d['name'] == ctx['user']:
                user = d['user']
                break
        else:
            raise RuntimeError(f'User {ctx["user"]} was not found in {fn}')

        return cls(
                cluster['server'],
                ca_file=cluster['certificate-authority'],
                client_cert_file=user['client-certificate'],
                client_key_file=user['client-key'])
