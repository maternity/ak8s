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

    def _project(self, data):
        self = self.__class__(itemlens=self._itemlens)
        if data is not None:
            self._data = data
        return self

    def _unwrap(self, value, *, gen=False):
        if isinstance(value, ListProxy):
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
