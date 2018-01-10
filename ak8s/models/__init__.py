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

import json
import re

from ..nestedns import NS
from ..data import load as load_data

from .base import ModelBase


class ModelRegistry:
    '''Registry of swagger spec derived models.

    >>> registry = ModelRegistry()
    >>> with open('v1.json') as fh:
    ...     spec = json.load(fh)
    >>> registry.add_spec(spec)
    >>> registry.models.v1.Container
    <class 'models.v1.Container'>
    '''

    def __init__(self, *, release=None):
        self.models = NS(missing=self._get_model)
        self._model_desc = {}
        self.models_by_gvk = NS(missing=self._get_model_by_gvk)
        self._gvk_names = {}

        if release is not None:
            self.load_release_spec(release)

    def load_spec(self, pth):
        with open(pth) as fh:
            spec = json.load(fh)
            self.add_spec(spec)

    def load_release_spec(self, release):
        spec = json.loads(load_data(f'release-{release}.json'))
        self.add_spec(spec)

    def add_spec(self, spec):
        for name,desc in spec['definitions'].items():
            self.add_model_desc(name, desc)

    def add_model_desc(self, name, desc):
        if name in self._model_desc:
            # Some models appear in multiple APIs, if the specs don't differ,
            # then ignore it.
            if desc == self._model_desc[name]:
                return
            raise KeyError(f'Spec for {name} is already registered')
        self._model_desc[name] = desc
        self.models._declare_lazy(name)
        if 'x-kubernetes-group-version-kind' in desc:
            for d in desc['x-kubernetes-group-version-kind']:
                # This name isn't useful as a variable name, but we're lacking
                # the tag aliases that map {group: '', version: 'v1'} ->
                # core_v1.  So, the models_by_gvk interface is only useful for
                # programattic access.
                gvk_name = d['group'], d['version'], d['kind']
                self._gvk_names[gvk_name] = name
                self.models_by_gvk._declare_lazy(gvk_name)

    def _get_model_desc(self, name, *, resolve=True):
        name = re.sub(r'^#/definitions/', '', name)
        desc = self._model_desc[name]
        if resolve:
            while '$ref' in desc:
                desc = self._get_model_desc(desc['$ref'], resolve=False)
        return desc

    def _register_model(self, model):
        if not issubclass(model, ModelBase):
            raise TypeError('Only ModelBase derived models can be registered.')
        self.models[model.__name__] = model
        return model

    def _get_model(self, name):
        desc = self._get_model_desc(name, resolve=False)

        if '$ref' in desc:
            ref = re.sub(r'^#/definitions/', '', desc['$ref'])
            return self.models[ref]

        if 'type' in desc:
            if desc['type'] == 'string':
                return str

        class Model(ModelBase, registry=self, name=name):
            __slots__ = ()

        return Model

    def _get_model_by_gvk(self, gvk):
        return self.models[self._gvk_names[gvk]]

    def _is_model(self, name):
        mdesc = self._get_model_desc(name)
        return 'type' not in mdesc
