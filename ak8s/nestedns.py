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

class NS:
    '''Nesting namespace.

    >>> ns = NS({ 'foo.bar': 1, 'duck.duck.goose': 101 })
    >>> ns.foo
    <NS: 'foo'>
    >>> ns.foo.bar
    1
    >>> ns.duck.duck
    <NS: 'duck.duck'>
    >>> ns.duck.duck.goose
    101
    >>> ns['foo.quux'] = 2
    >>> ns.foo.quux
    2
    '''

    def __init__(self, seq=None, *, missing=None):
        self._data = {}
        self._lazy = set()
        self._missing = missing
        self._prefixes = set()
        if seq is not None:
            if hasattr(seq, 'items'):
                seq = seq.items()
            for k,v in seq:
                self[k] = v

    def __repr__(self):
        return '<NS>'

    def _declare_lazy(self, k):
        '''Declare names that can be populated lazily.

        This is necessary to find namespace prefixes, and it also informs
        shell completions.
        '''
        if k in self._prefixes:
            raise KeyError(f'{k!r} conflicts with an existing prefix')
        for prefix in _prefixes_of(k):
            if prefix in self._data:
                raise KeyError(f'{k!r} conflicts with {prefix!r}')
            self._prefixes.add(prefix)
        self._lazy.add(k)

    def __setitem__(self, k, v):
        if k in self._prefixes:
            raise KeyError(f'{k!r} conflicts with an existing prefix')
        for prefix in _prefixes_of(k):
            if prefix in self._data:
                raise KeyError(f'{k!r} conflicts with {prefix!r}')
            self._prefixes.add(prefix)
        self._data[k] = v

    def __getitem__(self, k):
        if k in self._data:
            return self._data[k]
        if k not in self._prefixes and self._missing is not None:
            try:
                v = self._missing(k)
            except LookupError:
                pass
            else:
                self[k] = v
                return v
        raise KeyError(k)

    def __delitem__(self, k):
        del self._data[k]

    def __iter__(self):
        yield from self._lazy|set(self._data)

    def __contains__(self, k):
        return k in self._data or k in self._lazy

    def __getattr__(self, k):
        if k in self:
            return self[k]
        if k in self._prefixes:
            return SubNS(self, k)
        raise AttributeError(k)

    def __dir__(self):
        #yield from super().__dir__()
        yield from _of_prefix(self._prefixes, '')
        yield from _of_prefix(self, '')


class SubNS:
    def __init__(self, ns, prefix):
        self._ns = ns
        self._prefix = prefix

    def __repr__(self):
        return f'<NS: {self._prefix!r}>'

    def __getattr__(self, k):
        fqk = f'{self._prefix}.{k}'
        if fqk in self._ns:
            return self._ns[fqk]
        if fqk in self._ns._prefixes:
            return SubNS(self._ns, fqk)
        raise AttributeError(k)

    def __dir__(self):
        #yield from super().__dir__()
        yield from _of_prefix(self._ns._prefixes, self._prefix)
        yield from _of_prefix(self._ns, self._prefix)


def _prefixes_of(k):
    '''Generate namespace prefixes of `k`.

    >>> list(_prefixes_of('foo.bar.quux'))
    ['foo', 'foo.bar']
    '''

    i = -1
    while True:
        try:
            i = k.index('.', i+1)
        except ValueError:
            return
        yield k[:i]


def _of_prefix(seq, prefix):
    '''Generate suffixes of `seq` elements that are of a prefix (not nested).

    >>> list(_of_prefix(['foo.bar', 'foo.bar.quux', 'few.bar'], 'foo'))
    ['bar']
    '''

    if prefix and not prefix.endswith('.'):
        prefix += '.'
    start = len(prefix)
    for k in seq:
        if  k.startswith(prefix) and k.find('.', start) == -1:
            yield k[start:]
