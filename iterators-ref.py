"""
ITERATORS & GENERATORS -- reference solutions.  See iterators.py for the script.

Recurring pitfalls:
  * "Peek then forget": has_next()/peek() must CACHE what they pulled so the
    following next() returns it instead of the element after.
  * Use a private sentinel object, not None, for "no cached value" -- None
    can be a legitimate element.
  * Generators are lazy by construction: no code in the body runs until the
    first next().  A plain function that builds a list is not.
  * heapq tuples: put a unique tiebreaker (the source index) BEFORE the
    payload so the payload is never compared.
"""
from __future__ import annotations

import heapq
from collections import deque
from itertools import count, islice
from typing import Any, Callable, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

T = TypeVar("T")
_EMPTY = object()   # sentinel: "nothing cached"


class NestedInteger:
    """LC341's interface: holds either an int or a list of NestedInteger."""

    def __init__(self, value: Union[int, List["NestedInteger"]]) -> None:
        self._value = value

    def is_integer(self) -> bool:
        return isinstance(self._value, int)

    def get_integer(self) -> Optional[int]:
        return self._value if isinstance(self._value, int) else None

    def get_list(self) -> Optional[List["NestedInteger"]]:
        return None if isinstance(self._value, int) else self._value


def build_nested(obj: list) -> List[NestedInteger]:
    """[[1,1],2,[1,1]] -> List[NestedInteger] (helper for the tests)."""
    def convert(x: Any) -> NestedInteger:
        if isinstance(x, int):
            return NestedInteger(x)
        return NestedInteger([convert(y) for y in x])
    return [convert(x) for x in obj]


# ----------------------------------------------------------------- Part 1
class NestedIterator:
    # Stack of ITERATORS (one per list we are inside), not of elements.
    # Invariant: `_cached` is either _EMPTY or the next integer to return.
    # has_next() does the walking; next() just hands out the cache.
    def __init__(self, nested_list: List[NestedInteger]) -> None:
        self._stack: List[Iterator[NestedInteger]] = [iter(nested_list)]
        self._cached: Any = _EMPTY

    def has_next(self) -> bool:
        while self._cached is _EMPTY and self._stack:
            item = next(self._stack[-1], None)
            if item is None:                  # this list is exhausted
                self._stack.pop()
            elif item.is_integer():
                self._cached = item.get_integer()
            else:
                self._stack.append(iter(item.get_list()))   # descend
        return self._cached is not _EMPTY

    def next(self) -> int:
        if not self.has_next():
            raise StopIteration
        val = self._cached
        self._cached = _EMPTY
        return val
    # Amortised O(1) per element: each NestedInteger is visited once overall.
    # Space O(depth).  Eager alternative: flatten into a deque in __init__
    # (O(total) up front, fails the "lazy" requirement).


# ----------------------------------------------------------------- Part 2
class PeekingIterator:
    # One-element buffer filled on demand.  Only _fill() touches the source.
    def __init__(self, iterable: Iterable[T]) -> None:
        self._it = iter(iterable)
        self._buf: Any = _EMPTY
        self._done = False

    def _fill(self) -> None:
        if self._buf is _EMPTY and not self._done:
            self._buf = next(self._it, _EMPTY)
            if self._buf is _EMPTY:
                self._done = True

    def peek(self) -> T:
        self._fill()
        if self._buf is _EMPTY:
            raise StopIteration
        return self._buf

    def next(self) -> T:
        val = self.peek()
        self._buf = _EMPTY
        return val

    def has_next(self) -> bool:
        self._fill()
        return self._buf is not _EMPTY

    def __iter__(self) -> "PeekingIterator":
        return self

    def __next__(self) -> T:
        return self.next()
    # `_done` avoids calling next() on an exhausted generator repeatedly
    # (harmless for generators, but some iterators are not re-safe).


# ----------------------------------------------------------------- Part 3
class ZigzagIterator:
    # Queue of (list, index) cursors; pop-left, emit, re-append if more.
    # Exhausted lists are simply not re-appended, so they drop out.
    def __init__(self, lists: List[List[int]]) -> None:
        self._q: deque = deque((lst, 0) for lst in lists if lst)

    def has_next(self) -> bool:
        return bool(self._q)

    def next(self) -> int:
        lst, i = self._q.popleft()
        if i + 1 < len(lst):
            self._q.append((lst, i + 1))
        return lst[i]

    def __iter__(self) -> "ZigzagIterator":
        return self

    def __next__(self) -> int:
        if not self._q:
            raise StopIteration
        return self.next()
    # O(1) per element, O(K) extra.  For arbitrary iterables (not lists) wrap
    # each in a PeekingIterator so has_next() can still be answered.


# ----------------------------------------------------------------- Part 4
Fetch = Callable[[Optional[str]], Tuple[List[T], Optional[str]]]


def paginate(fetch: Fetch) -> Iterator[T]:
    # A generator: the body does not run until the first next(), so nothing
    # is fetched at creation.  `yield from` streams a page item by item.
    cursor: Optional[str] = None
    while True:
        items, cursor = fetch(cursor)
        yield from items
        if cursor is None:
            return
    # Memory O(page).  Production concerns: retries on transient errors,
    # a max-pages guard against cursor loops, and re-entrancy (a generator
    # cannot be shared between threads).


# ----------------------------------------------------------------- Part 5
def merge_sorted(*iterables: Iterable[T], key: Optional[Callable[[T], Any]] = None) -> Iterator[T]:
    # Heap of (key, source_index, value, iterator).  source_index breaks key
    # ties in argument order (stability) AND guarantees `value` is never
    # compared.  heapreplace = pop + push in one sift.
    keyf = key if key is not None else (lambda x: x)
    heap: List[Tuple[Any, int, Any, Iterator[T]]] = []
    for idx, it in enumerate(iterables):
        it = iter(it)
        first = next(it, _EMPTY)
        if first is not _EMPTY:
            heap.append((keyf(first), idx, first, it))
    heapq.heapify(heap)
    while heap:
        _, idx, val, it = heap[0]
        yield val
        nxt = next(it, _EMPTY)
        if nxt is _EMPTY:
            heapq.heappop(heap)
        else:
            heapq.heapreplace(heap, (keyf(nxt), idx, nxt, it))
    # O(N log K) total, O(K) memory, works on infinite inputs because we only
    # ever hold one element per source.


# ----------------------------------------------------------------- Part 6
class Range:
    # All the arithmetic hangs off len(): n = ceil((stop - start) / step)
    # clamped at 0.  Then the i-th element is start + i*step.
    def __init__(self, start: int, stop: Optional[int] = None, step: int = 1) -> None:
        if stop is None:
            start, stop = 0, start
        if step == 0:
            raise ValueError("step must not be zero")
        self.start, self.stop, self.step = start, stop, step

    def __len__(self) -> int:
        if self.step > 0:
            return max(0, (self.stop - self.start + self.step - 1) // self.step)
        return max(0, (self.start - self.stop - self.step - 1) // (-self.step))

    def __iter__(self) -> Iterator[int]:
        x = self.start
        if self.step > 0:
            while x < self.stop:
                yield x
                x += self.step
        else:
            while x > self.stop:
                yield x
                x += self.step

    def __contains__(self, x: object) -> bool:
        # O(1): in the half-open interval AND on the arithmetic lattice.
        if not isinstance(x, int) or isinstance(x, bool):
            return False
        if self.step > 0:
            return self.start <= x < self.stop and (x - self.start) % self.step == 0
        return self.stop < x <= self.start and (self.start - x) % (-self.step) == 0

    def __getitem__(self, i: Union[int, slice]) -> Union[int, "Range"]:
        n = len(self)
        if isinstance(i, slice):
            a, b, c = i.indices(n)        # normalises None / negatives / overflow
            return Range(self.start + a * self.step, self.start + b * self.step, self.step * c)
        if i < 0:
            i += n
        if not 0 <= i < n:
            raise IndexError("Range index out of range")
        return self.start + i * self.step

    def __reversed__(self) -> Iterator[int]:
        n = len(self)
        last = self.start + (n - 1) * self.step
        return iter(Range(last, self.start - self.step, -self.step))

    def __eq__(self, other: object) -> bool:
        # Same VALUES, not same parameters: Range(0,3,5) == Range(0,1).
        if not isinstance(other, Range):
            return NotImplemented
        n = len(self)
        if n != len(other):
            return False
        if n == 0:
            return True
        if n == 1:
            return self.start == other.start
        return self.start == other.start and self.step == other.step

    def __repr__(self) -> str:
        if self.step == 1:
            return f"Range({self.start}, {self.stop})"
        return f"Range({self.start}, {self.stop}, {self.step})"
    # __len__ makes `bool(Range(3, 3))` False for free.  Everything is O(1)
    # except iteration; builtin range has the same contract.


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    def drain(nested: list) -> List[int]:
        it = NestedIterator(build_nested(nested))
        out: List[int] = []
        while it.has_next():
            assert it.has_next()             # idempotent: must not skip
            out.append(it.next())
        assert it.has_next() is False
        return out

    assert drain([[1, 1], 2, [1, 1]]) == [1, 1, 2, 1, 1]
    assert drain([1, [4, [6]]]) == [1, 4, 6]
    assert drain([[], [[]], 3]) == [3]
    assert drain([[], [[]]]) == []
    assert drain([]) == []
    assert drain([[[[[7]]]], 8]) == [7, 8]
    it1 = NestedIterator(build_nested([1, [2]]))
    assert it1.next() == 1 and it1.next() == 2       # next() without has_next()
    assert it1.has_next() is False

    # Part 2
    pk = PeekingIterator(iter([1, 2, 3]))
    assert pk.next() == 1
    assert pk.peek() == 2
    assert pk.peek() == 2                             # peek does not consume
    assert pk.next() == 2
    assert pk.has_next() is True
    assert pk.next() == 3
    assert pk.has_next() is False
    assert PeekingIterator([]).has_next() is False
    pulls: List[int] = []

    def noisy() -> Iterator[int]:
        for i in range(3):
            pulls.append(i)
            yield i

    pk2 = PeekingIterator(noisy())
    assert pulls == []                                # bonus: nothing pulled yet
    assert pk2.peek() == 0 and pulls == [0]
    assert pk2.next() == 0 and pulls == [0]
    assert pk2.has_next() is True and pulls == [0, 1]
    assert [pk2.next(), pk2.next()] == [1, 2]
    assert pk2.has_next() is False

    # Part 3
    zz = ZigzagIterator([[1, 2, 3], [4, 5, 6, 7], [8, 9]])
    got: List[int] = []
    while zz.has_next():
        got.append(zz.next())
    assert got == [1, 4, 8, 2, 5, 9, 3, 6, 7]
    assert list(ZigzagIterator([[1, 2], [3], [], [4, 5, 6]])) == [1, 3, 4, 2, 5, 6]
    assert list(ZigzagIterator([[], []])) == []
    assert list(ZigzagIterator([])) == []
    assert list(ZigzagIterator([[1, 2, 3]])) == [1, 2, 3]

    # Part 4
    pages = {None: ([1, 2], "p2"), "p2": ([], "p3"), "p3": ([3], "p4"), "p4": ([4, 5], None)}
    calls: List[Optional[str]] = []

    def fetch(cursor: Optional[str]) -> Tuple[List[int], Optional[str]]:
        calls.append(cursor)
        return pages[cursor]

    pg = paginate(fetch)
    assert calls == []                                # lazy: nothing on creation
    assert next(pg) == 1 and calls == [None]
    assert next(pg) == 2 and calls == [None]
    assert next(pg) == 3 and calls == [None, "p2", "p3"]   # empty page skipped
    assert next(pg) == 4 and calls == [None, "p2", "p3", "p4"]
    assert next(pg) == 5
    assert next(pg, "done") == "done"
    assert next(pg, "done") == "done"
    assert calls == [None, "p2", "p3", "p4"]          # each page fetched once
    assert list(paginate(lambda c: ([], None))) == []
    assert list(paginate(lambda c: ([1, 2, 3], None))) == [1, 2, 3]
    assert list(islice(paginate(lambda c: ([len(c or "")], (c or "") + "x")), 5)) == [0, 1, 2, 3, 4]

    # Part 5
    assert list(merge_sorted([1, 4, 9], [2, 3, 10], [5])) == [1, 2, 3, 4, 5, 9, 10]
    assert list(merge_sorted()) == []
    assert list(merge_sorted([], [], [1])) == [1]
    assert list(islice(merge_sorted(count(0, 3), count(1, 3), count(2, 3)), 10)) == list(range(10))
    tagged = list(merge_sorted([(1, "a"), (2, "a")], [(1, "b")], [(1, "c"), (3, "c")], key=lambda t: t[0]))
    assert tagged == [(1, "a"), (1, "b"), (1, "c"), (2, "a"), (3, "c")]   # stable on ties
    assert list(merge_sorted([3, 2, 1], [2, 1], key=lambda x: -x)) == [3, 2, 2, 1, 1]
    import random
    random.seed(7)
    for _ in range(50):
        lists = [sorted(random.randint(0, 20) for _ in range(random.randint(0, 8))) for _ in range(random.randint(0, 5))]
        assert list(merge_sorted(*lists)) == list(heapq.merge(*lists))

    # Part 6
    assert list(Range(0, 10, 3)) == [0, 3, 6, 9]
    assert len(Range(10, 0, -3)) == 4 and list(Range(10, 0, -3)) == [10, 7, 4, 1]
    assert 7 in Range(1, 100, 3) and 8 not in Range(1, 100, 3)
    assert 100 not in Range(1, 100, 3) and 1 in Range(1, 100, 3)
    assert 2.0 not in Range(0, 5) and "2" not in Range(0, 5)
    assert Range(0, 10)[-1] == 9 and Range(0, 10)[0] == 0
    assert Range(0, 10)[2:8:2] == Range(2, 8, 2)
    assert Range(5) == Range(0, 5, 1)
    assert Range(0, 0) == Range(5, 5, -2)             # both empty
    assert Range(0, 3, 5) == Range(0, 1)              # both [0]
    assert Range(0, 5) != Range(0, 6)
    assert list(reversed(Range(0, 10, 3))) == [9, 6, 3, 0]
    assert not Range(3, 3) and Range(3, 4)
    try:
        Range(0, 1, 0)
        assert False, "step 0 must raise"
    except ValueError:
        pass
    try:
        Range(0, 3)[3]
        assert False, "must raise IndexError"
    except IndexError:
        pass
    specs = [(0, 10, 1), (0, 10, 3), (10, 0, -3), (5, 5, 1), (-7, 8, 4), (8, -7, -4), (0, 1, 7), (3, 2, 1), (2, 3, -1)]
    for s0, s1, s2 in specs:
        r, R = range(s0, s1, s2), Range(s0, s1, s2)
        assert list(R) == list(r) and len(R) == len(r) and list(reversed(R)) == list(reversed(r)), (s0, s1, s2)
        for x in range(-12, 15):
            assert (x in R) == (x in r), (s0, s1, s2, x)
        for i in range(-len(r), len(r)):
            assert R[i] == r[i]
        for sl in (slice(None), slice(1, None), slice(None, -1), slice(None, None, -1),
                   slice(1, 4), slice(-3, None, 2), slice(4, 1, -1), slice(10, 20)):
            assert list(R[sl]) == list(r[sl]), (s0, s1, s2, sl)
            assert isinstance(R[sl], Range)

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: What is the difference between an iterable, an iterator and a generator?
# A: Iterable: has __iter__ returning an iterator.  Iterator: has __next__ (and
#    __iter__ returning self); single pass.  Generator: an iterator produced by
#    a function with `yield`; its body is suspended between next() calls.
# Q: NestedIterator -- why a stack of iterators instead of a stack of elements?
# A: Pushing a list's elements reversed costs O(len) at push time and O(total)
#    memory up front; a stack of iterators costs O(depth) and each element is
#    touched once, exactly when it is needed.
# Q: Why must the heap tuple in merge_sorted carry the source index?
# A: Two reasons: it breaks ties deterministically in argument order (stable),
#    and it prevents Python from ever comparing the payloads, which might be
#    dicts or other unorderable objects.
# Q: paginate() -- what breaks if the API returns the same cursor twice?
# A: Infinite loop.  Guard with a seen-cursor set or a max-pages limit and
#    raise; also consider retries with backoff for transient failures.
# Q: Why is `x in Range(...)` O(1) but `x in list(range(...))` O(n)?
# A: Range checks the interval bounds and (x - start) % step arithmetically;
#    a list has no structure to exploit and must scan.
