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
from inspect import Parameter
from inspect import Signature
import json
from pathlib import Path
import re
import textwrap
from types import MappingProxyType as mappingproxy
from urllib.parse import urlencode
from urllib.parse import urlunsplit

from .models import ModelRegistry
from .nestedns import NS


# Customization points (things that can't be inferred from the spec)
# - Gather arguments from context object (namespace and name don't have to be
#   specified separately).
# - Gather arguments from context object when that object is not the request
#   or the response (DELETE requests, item watch operations, other subresources
#   such as pod logs).
# - PATCH requests (maybe can be done generically)
#
# Direct subclassing probably works well here, because you can just implement
# __call__ and super with the adapted args.  The structure of the apilist is
# not convenient though, so being able to reference the api by name is
# desirable.
#
# Mixing explicitly defined classes with auto generated classes should be easy.
#
# The models form of this using mixins is ok, but I'd like to just define the
# class and use mixins there, if I want them.


class K8sAPIOperation:
    # class attrs
    name = None
    method = None
    path = None

    k8s_tag = None
    k8s_group = None
    k8s_version = None
    k8s_kind = None
    k8s_action = None

    def __init_subclass__(cls, *, name=None, registry=None, **kw):
        super().__init_subclass__(**kw)

        if not name and not registry:
            return

        path, pathparams, method, opdesc = registry._get_api_desc(name)

        cls.__qualname__ = cls.__name__ = cls.name = name
        cls.method = method
        cls.path = path
        cls.consumes = set(opdesc.get('consumes') or ())
        cls.produces = set(opdesc.get('produces') or ())

        if 'x-kubernetes-group-version-kind' in opdesc:
            cls.k8s_group = opdesc['x-kubernetes-group-version-kind']['group']
            cls.k8s_version = opdesc['x-kubernetes-group-version-kind']['version']
            cls.k8s_kind = opdesc['x-kubernetes-group-version-kind']['kind']
            cls.k8s_action = opdesc['x-kubernetes-action']
        cls.k8s_tag, = opdesc['tags']

        params = []
        if pathparams is not None:
            params.extend(pathparams)
        if 'parameters' in opdesc:
            params.extend(opdesc['parameters'])

        path_param_names = [
                m.group(1)
                for m in re.finditer(r'{(\w+)(?::\*)?}', path) ]
        cls._path_params = {
                p['name']: p for p in params if p['in'] == 'path' }
        body_params = [
                p for p in params if p['in'] == 'body' ]
        if body_params:
            # Expect exactly one.  If there's more than one, we're going home.
            # And by home I mean we're going to crash.
            cls._body_param, = body_params
        else:
            cls._body_param = None
        cls._query_params = {
                p['name']: p for p in params
                if p['in'] == 'query' }

        args = [ cls._path_params[name] for name in path_param_names ]
        if cls._body_param:
            args.append(cls._body_param)

        opts = [
                param for name, param in cls._query_params.items()
                if name not in cls._path_params ]

        cls.__signature__ = Signature([
                *( Parameter(p['name'], Parameter.POSITIONAL_OR_KEYWORD)
                        for p in args ),
                *( Parameter(p['name'], Parameter.KEYWORD_ONLY)
                        for p in opts ) ])

        try:
            response_model = re.sub(r'^#/definitions/', '',
                    opdesc['responses']['200']['schema']['$ref'])

        except KeyError:
            response_model = 'unknown'

        cls.__doc__ = f'{cls.k8s_group} {cls.k8s_action} {cls.k8s_version} {cls.k8s_kind}\n\n'
        cls.__doc__ += f'    {method} {path} -> {response_model}\n\n'

        if args:
            cls.__doc__ += 'ARGUMENTS\n\n'
            cls.__doc__ += ''.join( format_param_doc(p) for p in args )

        if opts:
            cls.__doc__ += 'OPTIONS\n\n'
            cls.__doc__ += ''.join( format_param_doc(p) for p in opts )

        registry._register_api(cls)

    # instance attrs
    stream = False
    uri = None
    body = None
    args = None

    def __init__(self, *a, **kw):
        # Not using Signature.bind() here because we want to treat the query
        # params as optional, without using a default.
        bound = self.__signature__.bind_partial(*a, **kw)

        self.args = mappingproxy(bound.arguments.copy())

        if self._body_param:
            body = bound.arguments.pop(self._body_param['name'])
        else:
            body = None

        try:
            path_ = re.sub(
                    r'{(\w+)(?::\*)?}',
                    lambda m: bound.arguments.pop(m.group(1)),
                    self.path)
        except KeyError as e:
            raise TypeError(f'missing required argument {e!s}')
        query = urlencode(bound.kwargs)
        self.uri = urlunsplit(('', '', path_, query, ''))
        self.body = body

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.uri}>'

    def __eq__(self, them):
        if isinstance(them, self.__class__):
            return self.args == them.args
        return NotImplemented

    def __hash__(self):
        return hash(tuple(self.args.items()))

    def replace(self, *a, **kw):
        '''Derive a copy of this operation with some arguments replaced.

        >>> registry.apis.list_namespaced_pod(namespace='default', watch=True)
        <listNamespacedPod: /api/v1/namespaces/default/pods?watch=True>
        >>> _.replace(resourceVersion='10')
        <listNamespacedPod: /api/v1/namespaces/default/pods?watch=True&resourceVersion=10>
        '''

        bound = self.__signature__.bind_partial(*a, **kw)
        # Remove kwargs set to None.  Unsetting positional args doesn't really
        # make sense, as it would cause later positional args to slide over,
        # and we don't have optional positional args anyway.
        args = {**self.args, **bound.arguments}
        for k,v in bound.kwargs.items():
            if v is None:
                del args[k]
        return self.__class__(**args)

    def body_as(self, content_type=None):
        '''Returns (headers, body).'''

        if self.body is None:
            raise TypeError('no body')

        headers = {}

        json_type_re = r'(?:application/json|[^;]+\+json)(?:;.*)?'

        if not {content_type, '*/*'} & self.consumes:
            msg = (
                    f'{content_type!r} is unsupported or not implemented; '+
                    f'possibilities are: {self.consumes}')
            raise ValueError(msg)

        if content_type is None:
            # TODO: pick something?
            msg = "missing required keyword argument 'content_type'"
            raise TypeError(msg)

        elif re.fullmatch(json_type_re, content_type):
            # TODO: dispatch on body?
            body = json.dumps(self.body._data).encode('ascii')

        headers['content-type'] = content_type
        headers['content-length'] = str(len(body))

        return headers, body


class APIRegistry(ModelRegistry):
    '''Registry of swagger spec derived models and APIs.

    >>> registry = APIRegistry()
    >>> with open('v1.json') as fh:
    ...     spec = json.load(fh)
    >>> registry.add_spec(spec)
    >>> registry.models.v1.Container
    <class 'models.v1.Container'>
    >>> registry.apis['v1'].list_namespaced_pod
    <class 'apis.listNamespacedPod'>
    '''

    def __init__(self):
        super().__init__()
        self.apis = NS(missing=self._get_api)
        self._api_desc = {}
        self._api_bases = []

    def add_spec(self, spec):
        super().add_spec(spec)
        for pth, pthdesc in spec['paths'].items():
            pathparams = pthdesc.get('parameters')
            for method, opdesc in pthdesc.items():
                if method == 'parameters':
                    continue
                self.add_api_desc(pth, pathparams, method, opdesc)

    def add_api_desc(self, pth, pathparams, method, opdesc):
        tag, = opdesc['tags']
        tag = camel2snake(tag) # rbacAuthorization_v1
        name = camel2snake(opdesc['operationId'])
        if tag in name:
            # 'create_core_v1namespaced_pod' -> 'core_v1.create_namespaced_pod'
            name = re.sub(f'(\\w+)_{re.escape(tag)}_?(?!$)', f'{tag}.\\1_', name)
        if name in self._api_desc:
            raise KeyError(f'Spec for {name} is already registered')
        self._api_desc[name] = pth, pathparams, method, opdesc
        self.apis._declare_lazy(name)

    def _get_api_desc(self, name):
        return self._api_desc[name]

    def _register_api(self, api):
        if not issubclass(api, K8sAPIOperation):
            raise TypeError('Only K8sAPIOperation derived APIs can be registered.')
        self.apis[api.name] = api

        return api

    def _get_api(self, name):
        for predicate, base_class in self._api_bases:
            if predicate(self, name):
                break

        else:
            base_class = K8sAPIOperation

        class API(
                base_class,
                registry=self,
                name=name):
            pass

        return API

    def add_api_base(self, predicate, base_class=None):
        '''Register a base class to be used for APIs when predicate matches.

        The predicate signature is:

            predicate(registry, name)

        Predicates are evaluated in the reverse order they were registered in.
        '''

        if isinstance(predicate, str):
            predicate = (lambda regex: lambda reg, name: re.fullmatch(regex, name))(predicate)

        def register(base_class):
            self._api_bases.insert(0, (predicate, base_class))
            return base_class

        if base_class is not None:
            register(base_class)
        else:
            return register


class StreamingMixin:
    stream = True

    @classmethod
    def bind_stream_condition(cls, condition):
        class StreamingMixin(cls):
            @property
            def stream(self):
                return bool(condition(self))
        return StreamingMixin


def format_param_doc(desc):
    if 'schema' in desc:
        type_ = re.sub(r'^#/definitions/', '', desc['schema']['$ref'])
    else:
        type_ = desc['type']
    if desc.get('description'):
        doc = desc['description']
        doc = textwrap.fill(
                doc, 64,
                # Avoid breaking up urls.
                break_long_words=False,
                break_on_hyphens=False)
        doc = textwrap.indent(doc, '        ')
        return f'    {desc["name"]} ({type_}):\n{doc}\n\n'
    return f'    {desc["name"]} ({type_})\n\n'



def camel2snake(s):
    return re.sub(r'(?<=[a-z])([A-Z]+)', lambda m: '_'+m.group(0), s).lower()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', metavar='SPEC', type=Path, nargs='+')
    args = parser.parse_args()

    registry = APIRegistry()

    @registry.add_api_base(r'(?:\w+\.)?watch\w+')
    class K8sAPIWatchOperation(StreamingMixin, K8sAPIOperation):
        pass

    @registry.add_api_base(r'(?:\w+\.)?(?:read|list)\w+')
    class K8sAPIReadItemOrCollectionOperation(
            StreamingMixin.bind_stream_condition(lambda self: self.args.get('watch')),
            K8sAPIOperation):
        pass

    @registry.add_api_base(r'readNamespacedPodLogs')
    class K8sAPIPodLogOperation(
            StreamingMixin.bind_stream_condition(lambda self: self.args.get('watch')),
            K8sAPIOperation):
        pass

    for pth in args.spec:
        if pth.is_dir():
            for pth in pth.rglob('*.json'):
                registry.load_spec(pth)
        else:
            registry.load_spec(pth)
