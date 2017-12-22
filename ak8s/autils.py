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

import asyncio


def aiter(aseq):
    if not hasattr(aseq, '__aiter__') and hasattr(aseq, '__iter__'):
        # Should this have a check to guard against errant aiter(awaitable) ?
        # Coerce a sync iterator to an async one.
        return _aiter(aseq)
    return aseq.__aiter__()


async def _aiter(seq):
    '''Coerce a sync iterator to an async iterator.'''
    for x in seq:
        yield x


async def anext(ai, *dflt):
    if len(dflt) > 1:
        raise TypeError(
                f'anext expected at most 2 arguments, got {len(dflt)+1}')
    try:
        return await ai.__anext__()
    except StopAsyncIteration:
        if dflt:
            return dflt[0]
        raise


async def athrottle(aseq, secs):
    ai = aiter(aseq)

    get = None
    timeout = None
    pending = set()
    value = None
    value_is_ready = False
    ended = False

    while True:
        if value_is_ready and timeout is None:
            yield value
            value_is_ready = False
            timeout = asyncio.ensure_future(asyncio.sleep(secs))
            pending.add(timeout)

        if get is None and not ended:
            get = asyncio.ensure_future(anext(ai))
            pending.add(get)

        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        if timeout in done:
            await timeout
            timeout = None

        if get in done:
            try:
                value = await get
            except StopAsyncIteration:
                ended = True
            else:
                value_is_ready = True
            get = None

        if ended and not value_is_ready:
            break


class amingle:
    '''Mingle async sequences.

    >>> async for x in amingle((
    ...         adrip(arange(5), 0.1),
    ...         adrip(arange(10), 0.03))):
    ...     print(x)
    Something would happen here.  I am certain of it.
    '''

    def __init__(self, aseqs=None):
        self.pending = set()
        if aseqs is not None:
            for aseq in aseqs:
                self.add(aseq)

    def add(self, aseq):
        ai = aiter(aseq)
        self.pending.add(astaple(ai, anext(ai)))

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if not self.pending:
                raise StopAsyncIteration
            done, self.pending = await asyncio.wait(
                    self.pending, return_when=asyncio.FIRST_COMPLETED)

            while done:
                try:
                    ai, x = await done.pop()
                except StopAsyncIteration:
                    continue # defiantly!
                if done:
                    # This potentially will cause reordering of results, it
                    # might be better to just save as self.done.
                    self.pending.update(done)
                self.pending.add(asyncio.ensure_future(astaple(ai, anext(ai))))
                return x

    async def aclose(self):
        while self.pending:
            self.pending.pop().cancel()


async def astaple(fixed, pending):
    return fixed, await pending


async def azip(*aseqs):
    ais = tuple( aiter(aseq) for aseq in aseqs )

    while True:
        vals = [None] * len(aseqs)
        # Resolve futures in the order they are ready in.  This is more
        # complicated than waiting for all to be ready, but canceling after the
        # first StopAsyncIteration should avoid some exception was never
        # received warnings.
        pending = { astaple(i,anext(ai)) for i,ai in enumerate(ais) }
        while pending:
            done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED)
            while done:
                try:
                    i,v = await done.pop()
                except StopAsyncIteration:
                    while pending:
                        pending.pop().cancel()
                    return
                vals[i] = v
        yield tuple(vals)
