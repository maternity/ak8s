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
import re
import textwrap
from urllib.parse import urlencode
from urllib.parse import urlunsplit
import sys

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
    def __init_subclass__(cls, *, name, registry, **kw):
        super().__init_subclass__(**kw)

        apidesc, opdesc = registry._get_api_desc(name)

        cls.__qualname__ = cls.__name__ = opdesc['nickname']
        cls.method = opdesc['method']
        cls.path = apidesc['path']
        cls._consumes = set(opdesc['consumes'])
        cls._produces = set(opdesc['produces'])

        path_param_names = [
                m.group(1)
                for m in re.finditer(r'{(\w+)(?::\*)?}', apidesc['path']) ]
        cls._path_params = {
                p['name']: p for p in opdesc['parameters']
                if p['paramType'] == 'path' }
        body_params = [
                p for p in opdesc['parameters'] if p['paramType'] == 'body' ]
        if body_params:
            # Expect exactly one.  If there's more than one, we're going home.
            # And by home I mean we're going to crash.
            cls._body_param, = body_params
        else:
            cls._body_param = None
        cls._query_params = {
                p['name']: p for p in opdesc['parameters']
                if p['paramType'] == 'query' }

        args = [ cls._path_params[name] for name in path_param_names ]
        if cls._body_param:
            args.append(cls._body_param)

        opts = cls._query_params.values()

        cls.__signature__ = Signature([
                *( Parameter(p['name'], Parameter.POSITIONAL_OR_KEYWORD)
                        for p in args ),
                *( Parameter(p['name'], Parameter.KEYWORD_ONLY)
                        for p in opts ) ])

        if opdesc['type'] == 'string':
            cls.response_model = None

        else:
            cls.response_model = registry.get_model(opdesc['type'])

        cls.__doc__ = f'{opdesc["summary"]}\n\n'
        cls.__doc__ += f'    {opdesc["method"]} {apidesc["path"]} -> {opdesc["type"]}\n\n'

        if args:
            cls.__doc__ += 'ARGUMENTS\n\n'
            cls.__doc__ += ''.join( format_param_doc(p) for p in args )

        if opts:
            cls.__doc__ += 'OPTIONS\n\n'
            cls.__doc__ += ''.join( format_param_doc(p) for p in opts )

        registry._register_api(cls)

    def __init__(self, *a, **kw):
        # Not using Signature.bind() here because we want to treat the query
        # params as optional, without using a default.
        bound = self.__signature__.bind_partial(*a, **kw)
        if self._body_param:
            body = bound.arguments.pop(self._body_param['name'])
        else:
            body = None

        for k,v in kw.items():
            if k not in self._query_params:
                raise TypeError(f'got an unexpected keyword argument {k!r}')

        try:
            path_ = re.sub(
                    r'{(\w+)(?::\*)?}',
                    lambda m: bound.arguments.pop(m.group(1)),
                    self.path)
        except KeyError as e:
            raise TypeError(f'missing required argument {e!s}')
        query = urlencode(kw)
        self.uri = urlunsplit(('', '', path_, query, ''))
        self.body = body

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.uri}>'

    def body_as(self, content_type=None):
        '''Returns (headers, body).'''

        if self.body is None:
            raise TypeError('no body')

        headers = {}

        json_type_re = r'(?:application/json|[^;]+\+json)(?:;.*)?'

        if not {content_type, '*/*'} & self._consumes:
            msg = (
                    f'{content_type!r} is unsupported or not implemented; '+
                    f'possibilities are: {self._consumes}')
            raise ValueError(msg)

        if content_type is None:
            # TODO: pick something?
            msg = "missing required keyword argument 'content_type'"
            raise TypeError(msg)

        elif re.fullmatch(json_type_re, content_type):
            # TODO: dispatch on body?
            body = json.dumps(self.body._data).encode('ascii')

        headers['content-type'] = content_type
        headers['content-length'] = len(body)

        return headers, iter([body])


class APIRegistry(ModelRegistry):
    '''Registry of swagger spec derived models and APIs.

    >>> registry = APIRegistry()
    >>> with open('v1.json') as fh:
    ...     spec = json.load(fh)
    >>> registry.add_spec(spec)
    >>> registry.models.v1.Container
    <class 'models.v1.Container'>
    >>> registry.apis.listNamespacedPod
    <class 'apis.listNamespacedPod'>
    '''

    def __init__(self):
        super().__init__()
        self.apis = NS(missing=self._get_api)
        self._api_desc = {}

    def __repr__(self):
        apis = []
        for name in self._api_desc:
            flag = '*' if name in self.apis else ''
            apis.append(f'{flag}{name}')
        return f'<{self.__class__.__qualname__} [{" ".join(apis)}]>'

    def add_spec(self, spec):
        super().add_spec(spec)
        for apidesc in spec['apis']:
            for opdesc in apidesc['operations']:
                self.add_api_desc(apidesc, opdesc)

    def add_api_desc(self, apidesc, opdesc):
        name = camel2snake(opdesc['nickname'])
        if name in self._api_desc:
            raise KeyError('Spec for {name} is already registered')
        self._api_desc[name] = apidesc, opdesc
        self.apis._declare_lazy(name)

    def _get_api_desc(self, name):
        return self._api_desc[name]

    def _register_api(self, api):
        if not issubclass(api, K8sAPIOperation):
            raise TypeError('Only K8sAPIOperation derived APIs can be registered.')
        name = camel2snake(api.__name__)
        if name in self.apis:
            raise KeyError('A {name!r} api already exists.')
        self.apis[name] = api
        return api

    def _get_api(self, name):
        if name not in self.apis:
            class API(K8sAPIOperation,
                    registry=self,
                    name=name):
                pass
        return self.apis[name]


def format_param_doc(desc):
    if desc.get('description'):
        doc = desc['description']
        doc = textwrap.fill(
                doc, 64,
                # Avoid breaking up urls.
                break_long_words=False,
                break_on_hyphens=False)
        doc = textwrap.indent(doc, '        ')
        return f'    {desc["name"]} ({desc["type"]}):\n{doc}\n\n'
    return f'    {desc["name"]} ({desc["type"]})\n\n'


def fixup_path_path_params(spec):
    for apidesc in spec['apis']:
        if '{path}' in apidesc['path']:
            # Change {path} to {path_} and update corresponding parameters.
            apidesc['path'] = apidesc['path'].replace('{path}', '{path_}')
            params = (
                    param
                    for opdesc in apidesc['operations']
                    for param in opdesc['parameters'] )
            for param in params:
                if param['paramType'] == 'path' and param['name'] == 'path':
                    param['name'] = 'path_'


def camel2snake(s):
    return re.sub(r'(?<=[a-z])([A-Z]+)', lambda m: '_'+m.group(0), s).lower()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', metavar='SPEC')
    args = parser.parse_args()

    registry = APIRegistry()

    with open(args.spec) as fh:
        spec = json.load(fh)
    fixup_path_path_params(spec)

    registry.add_spec(spec)
