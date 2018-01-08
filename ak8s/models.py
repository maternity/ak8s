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
import json
import re
import textwrap

from .nestedns import NS
from .boilerplate import boilerplate


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


class ModelRegistry:
    '''Registry of swagger spec derived models.

    >>> registry = ModelRegistry()
    >>> with open('v1.json') as fh:
    ...     spec = json.load(fh)
    >>> registry.add_spec(spec)
    >>> registry.models.v1.Container
    <class 'models.v1.Container'>
    '''

    def __init__(self):
        self.models = NS(missing=self._get_model)
        self._model_desc = {}
        self.models_by_gvk = NS(missing=self._get_model_by_gvk)
        self._gvk_names = {}

    def load_spec(self, pth):
        with open(pth) as fh:
            spec = json.load(fh)
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

        class Model(ModelBase, registry=self, name=name):
            __slots__ = ()

        return Model

    def _get_model_by_gvk(self, gvk):
        return self.models[self._gvk_names[gvk]]

    def _is_model(self, name):
        mdesc = self._get_model_desc(name)
        return 'type' not in mdesc


class ModelBase:
    __slots__ = '_data',

    def __init_subclass__(cls, *, registry, name, **kw):
        super().__init_subclass__(**kw)
        desc = registry._get_model_desc(name)
        cls.__qualname__ = cls.__name__ = name
        cls._desc = desc

        if 'description' in desc:
            doc = textwrap.fill(desc["description"])
        else:
            doc = "Doesn't look like anything to me."
        cls.__doc__ = f'{doc}\n\n'

        for pname,pdesc in desc['properties'].items():
            lens = mklens(pdesc, registry=registry)
            prop = LensProp(lens, pdesc)
            setattr(cls, pname, prop)
            # Apparently __init_subclass__ is too late for __set_name__ to
            # happen.  Have to do it manually.
            prop.__set_name__(cls, pname)
            if lens.__doc__:
                doc = lens.__doc__
                doc = textwrap.fill(
                        doc, 66,
                        # Avoid breaking up urls.
                        break_long_words=False,
                        break_on_hyphens=False)
                doc = textwrap.indent(doc, '    ')
                cls.__doc__ += f'{pname}:\n{doc}\n\n'
            else:
                cls.__doc__ += f'{pname}\n'

        registry._register_model(cls)

    def __init__(self, **kw):
        # values in kw are cooked
        self._data = boilerplate.get(self.__class__.__name__, dict)()
        for k,v in kw.items():
            setattr(self, k, v)

    def __getstate__(self):
        return self._data.copy()

    def __setstate__(self, data):
        self._data = data

    @classmethod
    def _project(cls, data):
        # elements of data are raw
        self = cls()
        if data is not None:
            self._data = data
        return self

    @classmethod
    def _unwrap(cls, value):
        return value._data

    def __repr__(self):
        preprs = []
        for pname in self._desc['properties']:
            if pname in self._data:
                try:
                    pval = getattr(self, pname)
                    preprs.append(f'{pname}={pval!r}')
                except Exception as e:
                    preprs.append(f'{pname}! {e!r}')

        return f'{self.__class__.__name__}({", ".join(preprs)})'

    def __eq__(self, them):
        if self.__class__ == them.__class__:
            return self._data == them._data
        return NotImplemented


class LensProp:
    def __init__(self, lens, pdesc):
        self.lens = lens
        if 'description' in pdesc:
            self.__doc__ = textwrap.fill(pdesc['description'])

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, them, owner):
        if them is None:
            return self
        if self.name in them._data:
            data = them._data[self.name]
            return self.lens.project(data)

    def __delete__(self, them):
        if self.name in them._data:
            del them._data[self.name]

    def __set__(self, them, values):
        them._data[self.name] = self.lens.unwrap(values)


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


import collections
class ListProxy(collections.MutableSequence):
    # TODO: subclass/instance checks?

    # FIXME: Some methods compare projected values for equality, others compare
    # raw values.  Need to be consistent, justify any exceptions.
    # Also, consider whether slice access should return a ListProxy instead of
    # a plain list.  The argument for doing this is that a plain list can't be
    # unwrapped.

    __slots__ = '_data', '_itemlens'

    def __init__(self, seq=None, *, itemlens):
        self._itemlens = itemlens
        self._data = []
        if seq is not None:
            self[:] = seq

    @classmethod
    def _binditem(cls, itemlens, desc):
        class BoundListLens(cls):
            if 'description' in desc:
                __doc__ = desc['description']
            __slots__ = ()
            _itemlens = itemlens
        return BoundListLens

    def _project(self, data):
        self = self.__class__(itemlens=self._itemlens)
        if data is not None:
            self._data = data
        return self

    def _unwrap(self, value, *, gen=False):
        if isinstance(value, ListLens):
            return value._data
        iunwrap = self._itemlens.unwrap
        if gen:
            return ( iunwrap(v) for v in value )
        return [ iunwrap(v) for v in value ]

    ### Mutators
    def __setitem__(self, key, value):
        if isinstance(key, slice):
            self._data[key] = self._unwrap(value, gen=True)
        else:
            self._data[key] = self._itemlens.unwrap(value)

    def insert(self, index, value):
        self._data.insert(index, self._itemlens.unwrap(value))

    def append(self, value):
        self._data.append(self._itemlens.unwrap(value))

    def extend(self, value):
        self._data.extend(self._unwrap(value, gen=True))

    def __delitem__(self, key):
        del self._data[key]

    def clear(self):
        self._data.clear()

    def remove(self, value):
        self._data.remove(self._itemlens.unwrap(value))

    def pop(self, *a):
        return self._data.pop(*a)

    def reverse(self):
        self._data.reverse()

    def sort(self, key=None, reverse=False):
        iproject = self._itemlens.project
        if key is None:
            lenskey = iproject
        else:
            lenskey = lambda d: key(iproject(d))
        self._data.sort(key=lenskey, reverse=reverse)

    def __iadd__(self, them):
        self.extend(them)

    def __imul__(self, n):
        self._data *= n

    ### Accessors
    def __iter__(self):
        iproject = self._itemlens.project
        return ( iproject(d) for d in self._data )

    def __getitem__(self, key):
        iproject = self._itemlens.project
        if isinstance(key, slice):
            return [ iproject(d) for d in self._data[key] ]
        else:
            return iproject(self._data[key])

    def __len__(self):
        return len(self._data)

    def __eq__(self, them):
        iproject = self._itemlens.project
        return len(self) == len(them) and all(
                iproject(a)==b for a,b in zip(self._data, them) )

    def __repr__(self):
        iproject = self._itemlens.project
        vreprs = ', '.join( repr(iproject(d)) for d in self._data )
        return f'[{vreprs}]'

    __hash__ = None

    def __contains__(self, value):
        iproject = self._itemlens.project
        return any( iproject(d)==value for d in self._data )

    def count(self, value):
        iproject = self._itemlens.project
        return sum( iproject(d)==value for d in self._data )

    def index(self, value):
        iproject = self._itemlens.project
        try:
            return next(
                    i for i,d in enumerate(self._data)
                    if iproject(d)==value )
        except StopIteration:
            raise ValueError(f'{value!r} is not in list')

    # Derive/generate
    def copy(self):
        return self._project(self._data.copy())

    def __reversed__(self):
        return self._project(reversed(self._data))

    def __add__(self, them):
        return self._project(self._data + self._unwrap(them))

    def __mul__(self, n):
        return self._project(self._data * n)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', metavar='SPEC')
    args = parser.parse_args()

    registry = ModelRegistry()
    with open(args.spec) as fh:
        spec = json.load(fh)
        registry.add_spec(spec)
