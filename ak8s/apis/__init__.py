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

import re

from ..models import ModelRegistry
from ..nestedns import NS

from .operation import K8sAPIOperation


__all__ = '''
    APIRegistry
'''.split()


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

    def __init__(self, *, release=None):
        super().__init__()
        self.apis = NS(missing=self._get_api)
        self._api_desc = {}
        self._api_bases = []

        if release is not None:
            self.load_release_spec(release)

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


def camel2snake(s):
    return re.sub(r'(?<=[a-z])([A-Z]+)', lambda m: '_'+m.group(0), s).lower()
