"""
ITERATORS & GENERATORS -- interviewer script (45-60 min; 3-4 parts typical)

Setup: "Our e-commerce backends stream data: paginated product listings,
merged feeds from several shards, nested category trees.  I want LAZY
iterators -- nothing materialised up front, and each next() does O(1)
amortised work (O(log K) where noted)."

Rules: stdlib only.  Do NOT list()/flatten the input in __init__; if you do it
as a warm-up, the interviewer will ask for the lazy version anyway.

------------------------------------------------------------------------------
Part 1  Flatten nested list iterator (LC341).  Input: List[NestedInteger]
        (small class below; build_nested() converts plain Python lists).
        Implement next() / has_next().
        [[1,1],2,[1,1]] -> 1,1,2,1,1 ; [1,[4,[6]]] -> 1,4,6
        Pitfall: empty inner lists -- [[],[[]],3] yields just 3, and
        has_next() must return False (not blow up) for [[],[[]]].
        Lazy version: a stack of Python iterators; has_next() advances until
        it finds an integer and caches it; calling has_next() twice must not
        skip anything.

Part 2  Peeking iterator (LC284) wrapping ANY Python iterator: peek(),
        next(), has_next().  peek() must not consume; has_next() is O(1).
        Bonus: don't pull the first element until someone asks for it (the
        underlying iterator may have side effects).

Part 3  Zigzag / cyclic iterator over K lists (LC281 generalised):
        [1,2,3],[4,5,6,7],[8,9] -> 1,4,8,2,5,9,3,6,7
        Exhausted lists drop out.  Also make it usable in a for loop
        (__iter__ / __next__).  O(1) per next().

Part 4  Paginated API iterator.  You are given
            fetch(cursor: Optional[str]) -> (items: List[T], next_cursor: Optional[str])
        fetch(None) returns the first page; next_cursor None marks the last
        page.  Write paginate(fetch) returning a lazy iterator over ALL items.
        Requirements: nothing is fetched until the first next(); an empty
        page that still has a cursor does not end the stream; each page is
        fetched exactly once; the final cursor None ends the stream.

Part 5  Lazy K-way merge of sorted iterables -- heapq.merge from scratch.
        merge_sorted([1,4,9], [2,3,10], [5]) -> 1,2,3,4,5,9,10
        Must work on INFINITE iterators (itertools.count) and be stable:
        ties come out in argument order.  Support key=.  O(log K) per item,
        O(K) memory.  Do not compare the payloads themselves (they might not
        be orderable) -- only keys.

Part 6  A Range class replicating range(start, stop, step) for ints:
        __iter__, __len__ and __contains__ in O(1), __getitem__ with
        negative indices and slices (a slice returns a Range), __reversed__,
        __eq__ (same sequence of values).
        Range(0, 10, 3) -> 0,3,6,9 ; len(Range(10, 0, -3)) == 4 ;
        7 in Range(1, 100, 3) -> True ; Range(0, 10)[-1] == 9 ;
        Range(0, 10)[2:8:2] == Range(2, 8, 2) ; Range(5) == Range(0, 5, 1)
------------------------------------------------------------------------------
"""
from __future__ import annotations

import heapq
from collections import deque
from itertools import count, islice
from typing import Any, Callable, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

T = TypeVar("T")


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
    def __init__(self, nested_list: List[NestedInteger]) -> None:
        pass

    def next(self) -> int:
        pass

    def has_next(self) -> bool:
        pass


# ----------------------------------------------------------------- Part 2
class PeekingIterator:
    def __init__(self, iterable: Iterable[T]) -> None:
        pass

    def peek(self) -> T:
        pass

    def next(self) -> T:
        pass

    def has_next(self) -> bool:
        pass


# ----------------------------------------------------------------- Part 3
class ZigzagIterator:
    def __init__(self, lists: List[List[int]]) -> None:
        pass

    def next(self) -> int:
        pass

    def has_next(self) -> bool:
        pass

    def __iter__(self) -> "ZigzagIterator":
        pass

    def __next__(self) -> int:
        pass


# ----------------------------------------------------------------- Part 4
Fetch = Callable[[Optional[str]], Tuple[List[T], Optional[str]]]


def paginate(fetch: Fetch) -> Iterator[T]:
    pass


# ----------------------------------------------------------------- Part 5
def merge_sorted(*iterables: Iterable[T], key: Optional[Callable[[T], Any]] = None) -> Iterator[T]:
    pass


# ----------------------------------------------------------------- Part 6
class Range:
    def __init__(self, start: int, stop: Optional[int] = None, step: int = 1) -> None:
        pass

    def __len__(self) -> int:
        pass

    def __iter__(self) -> Iterator[int]:
        pass

    def __contains__(self, x: object) -> bool:
        pass

    def __getitem__(self, i: Union[int, slice]) -> Union[int, "Range"]:
        pass

    def __reversed__(self) -> Iterator[int]:
        pass

    def __eq__(self, other: object) -> bool:
        pass

    def __repr__(self) -> str:
        pass


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
