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

import textwrap

from ..boilerplate import boilerplate

from .lens import mklens


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
