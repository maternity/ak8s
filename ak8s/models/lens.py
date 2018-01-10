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

from .list import ListProxy


def mklens(pdesc, *, registry):
    if '$ref' in pdesc:
        if registry._is_model(pdesc['$ref']):
            # At this time, I haven't seen any model definitions that resolved
            # to an array type.
            return ModelLens(pdesc, registry=registry)

        description = pdesc.get('description')
        return SimpleLens(
                registry._get_model_desc(pdesc['$ref']),
                description=description)

    if 'type' in pdesc and pdesc['type'] == 'array':
        itemlens = mklens(pdesc['items'], registry=registry)
        return ListLens(pdesc, itemlens=itemlens)

    return SimpleLens(pdesc)


class SimpleLens:
    def __init__(self, desc, *, description=None):
        if description is None:
            description = desc.get('description')
        if description is not None:
            self.__doc__ = description
        self._type = desc['type']
        self._format = desc.get('format')

    def __repr__(self):
        if self._format:
            return f'<{self.__class__.__name__} {self._type}: {self._format}>'
        return f'<{self.__class__.__name__} {self._type}>'

    def project(self, data):
        return data

    def unwrap(self, value):
        return value


class ModelLens:
    def __init__(self, desc, *, registry):
        if 'description' in desc:
            self.__doc__ = desc['description']
        self._models = registry.models
        self._ref = re.sub(r'^#/definitions/', '', desc['$ref'])
        self._model = None

    def __repr__(self):
        return f'<{self.__class__.__name__} {self._ref}>'

    def project(self, data):
        if self._model is None:
            self._model = self._models[self._ref]
        obj = object.__new__(self._model)
        obj._data = data
        return obj

    def unwrap(self, value):
        # value should be an instance of the model
        return value._data


class ListLens:
    def __init__(self, desc, *, itemlens):
        self._itemlens = itemlens
        self._bound = ListProxy(itemlens=itemlens)
        if 'description' in desc:
            self.__doc__ = desc['description']

    def __repr__(self):
        return f'<{self.__class__.__name__} {self._itemlens}>'

    def project(self, data):
        return self._bound._project(data)

    def unwrap(self, value):
        return self._bound._unwrap(value)
