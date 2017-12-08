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
import textwrap

from .nestedns import NS


def import_models(types, spec):
    models = spec['models']
    for mname,mdesc in models.items():
        types.define(mname, mdesc)


def mklens(pdesc, *, types):
    if '$ref' in pdesc:
        return ModelLens(pdesc, types=types)
    
    if pdesc['type'] == 'array':
        itemlens = mklens(pdesc['items'], types=types)
        return ListLens._binditem(itemlens, pdesc)

    return SimpleLens(pdesc)


class SimpleLens:
    def __init__(self, desc):
        if 'description' in desc:
            self.__doc__ = desc['description']

    @classmethod
    def _project(cls, data):
        return data

    @classmethod
    def _unwrap(cls, value):
        return value


class ModelLens:
    def __init__(self, desc, *, types):
        if 'description' in desc:
            self.__doc__ = desc['description']
        self._types = types
        self._ref = desc['$ref']
        self._model = None

    def _project(self, data):
        if self._model is None:
            self._model = self._types.models[self._ref]
        lens = object.__new__(self._model)
        lens._data = data
        return lens

    def _unwrap(self, value):
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

    def __repr__(self):
        models = []
        for name in self._model_desc:
            flag = '*' if name in self.models else ''
            models.append(f'{flag}{name}')
        return f'<{self.__class__.__qualname__} [{" ".join(models)}]>'

    def add_spec(self, spec):
        for desc in spec['models'].values():
            self.add_model_desc(desc)

    def add_model_desc(self, desc):
        if desc['id'] in self._model_desc:
            raise KeyError('Spec for {desc["id"]} is already registered')
        self._model_desc[desc['id']] = desc
        self.models._declare_lazy(desc['id'])

    def _get_model_desc(self, name):
        return self._model_desc[name]

    def _register_model(self, model):
        if not issubclass(model, ModelBase):
            raise TypeError('Only ModelBase derived models can be registered.')
        if model.__name__ in self.models:
            raise KeyError('A {model.__name__!r} model already exists.')
        self.models[model.__name__] = model
        return model

    def _get_model(self, name):
        if name not in self.models:
            class Model(ModelBase, types=self, name=name):
                __slots__ = ()
        return self.models[name]


class ModelBase:
    __slots__ = '_data',

    def __init_subclass__(cls, *, types, name, **kw):
        super().__init_subclass__(**kw)
        desc = types._get_model_desc(name)
        cls.__qualname__ = cls.__name__ = name
        cls._desc = desc

        if 'description' in desc:
            doc = textwrap.fill(desc["description"])
        else:
            doc = "Doesn't look like anything to me."
        cls.__doc__ = f'{doc}\n\n'

        for pname,pdesc in desc['properties'].items():
            lens = mklens(pdesc, types=types)
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

        types._register_model(cls)

    def __init__(self, **kw):
        # values in kw are cooked
        self._data = {}
        for k,v in kw.items():
            setattr(self, k, v)

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
                pval = getattr(self, pname)
                preprs.append(f'{pname}={pval!r}')

        return f'{self.__class__.__name__}({", ".join(preprs)})'


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
            return self.lens._project(data)

    def __delete__(self, them):
        if self.name in them._data:
            del them._data[self.name]

    def __set__(self, them, values):
        them._data[self.name] = self.lens._unwrap(values)


# Three tools?
# descriptors
# lens configs
# lens instances
#
# The descriptor provides __get__, __set__ and __delete__
# The lens config provides project and unwrap functionality.
# The lens is the actual projection class.
# 
# What's a better word for lens config?

class ListLens:
    # FIXME: Some methods compare projected values for equality, others compare
    # raw values.  Need to be consistent, justify any exceptions.

    __slots__ = '_data',

    def __init__(self, seq=None):
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

    @classmethod
    def _project(cls, data):
        self = cls()
        if data is not None:
            self._data = data
        return self

    @classmethod
    def _unwrap(cls, value, *, gen=False):
        if isinstance(value, ListLens):
            return value._data
        iunwrap = cls._itemlens._unwrap
        if gen:
            return ( iunwrap(v) for v in value )
        return [ iunwrap(v) for v in value ]

    ### Mutators
    def __setitem__(self, key, value):
        if isinstance(key, slice):
            self._data[key] = self._unwrap(value, gen=True)
        else:
            self._data[key] = self._itemlens._unwrap(value)

    def insert(self, index, value):
        self._data.insert(index, self._itemlens._unwrap(value))

    def append(self, value):
        self._data.append(self._itemlens._unwrap(value))

    def extend(self, value):
        self._data.extend(self._unwrap(values, gen=True))

    def __delitem__(self, key):
        del self._data[key]

    def clear(self):
        self._data.clear()

    def remove(self, value):
        self._data.remove(self._itemlens._unwrap(value))

    def pop(self, *a):
        return self._data.pop(*a)

    def reverse(self):
        self._data.reverse()

    def sort(self, key=None, reverse=False):
        iproject = self._itemlens._project
        if key is None:
            lenskey = iproject
        else:
            lenskey = lambda d: key(iproject(d))
        self._data.sort(lenskey=key, reverse=reverse)

    def __iadd__(self, them):
        self.extend(them)

    def __imul__(self, n):
        self._data *= n

    ### Accessors
    def __iter__(self):
        iproject = self._itemlens._project
        return ( iproject(d) for d in self._data )

    def __getitem__(self, key):
        iproject = self._itemlens._project
        if isinstance(key, slice):
            return [ iproject(d) for d in self._data[key] ]
        else:
            return iproject(self._data[key])

    def __eq__(self, them):
        iproject = self._itemlens._project
        return len(self) == len(them) and all(
                iproject(a)==b for a,b in zip(self._data, them) )

    def __repr__(self):
        iproject = self._itemlens._project
        vreprs = ', '.join( repr(iproject(d)) for d in self._data )
        return f'[{vreprs}]'

    __hash__ = None

    def __contains__(self, value):
        iproject = self._itemlens._project
        return any( iproject(d)==value for d in self._data )

    def count(self, value):
        iproject = self._itemlens._project
        return sum( iproject(d)==value for d in self._data )

    def index(self, value):
        iproject = self._itemlens._project
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

    types = ModelRegistry()
    with open(args.spec) as fh:
        spec = json.load(fh)
        types.add_spec(spec)

