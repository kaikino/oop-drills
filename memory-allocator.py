from __future__ import annotations

"""Leftmost Memory Block Allocator (TikTok OA, Sept 2026; LC2502)

Memory is an array of n unit cells, all free at start. Callers allocate blocks
of consecutive cells tagged with an integer id, and later free everything that
carries an id. No clock is involved.

Part 1 - simple allocator
    Allocator(n) with
        allocate(size, id) -> start index of the LEFTMOST free run of `size`
                              consecutive cells, marking them with id; -1 if
                              no such run exists (nothing is changed then).
        free(id)           -> number of cells freed. An id may own several
                              blocks (allocate twice with the same id); all of
                              them are freed. Unknown id -> 0.

    Example (n = 10):
        allocate(1, 1) -> 0        # [1,_,_,_,_,_,_,_,_,_]
        allocate(1, 2) -> 1
        allocate(1, 3) -> 2
        free(2)        -> 1        # [1,_,3,_,_,_,_,_,_,_]
        allocate(3, 4) -> 3        # cell 1 is free but too small
        allocate(1, 1) -> 1
        allocate(1, 1) -> 6
        free(1)        -> 3        # cells 0, 1, 6
        allocate(10, 2) -> -1
        free(7)        -> 0

    Required: O(n) per operation with an n-cell array is acceptable here.
    size >= 1 always.

Part 2 - track free runs
    n is now 10^9 cells and the number of live blocks is small. Implement
    RunAllocator(n) with the same API and identical results, storing only the
    free runs (sorted by start) and a map id -> owned blocks. allocate scans
    runs in address order and carves the first fit; free re-inserts a run and
    coalesces with both neighbours.

    Required: allocate O(#runs); free O(#blocks of id * log #runs) for the
    search (list insertion cost aside). Memory O(#runs + #blocks), NOT O(n).
    Prove equivalence with a randomized comparison against Part 1.

Part 3 - best fit and fragmentation
    allocate(size, id, policy="first" | "best"): "best" chooses the smallest
    free run that fits (leftmost among equals). Add fragmentation() ->
    1 - largest_free_run / total_free (0.0 when nothing is free).

    Example (n = 10):
        allocate(3,1)->0; allocate(2,2)->3; allocate(2,3)->5; allocate(3,4)->7
        free(1) -> 3; free(3) -> 2          # free runs: [0,3) and [5,7)
        fragmentation() -> 0.4              # 1 - 3/5
        allocate(2, 5, "first") -> 0
        (on a fresh copy) allocate(2, 5, "best") -> 5

    Required: same complexity as Part 2.

Part 4 - discussion (written answer, no code)
    Why does malloc not do a linear first-fit scan? Describe size-class
    free lists / slab allocators (fixed-size objects, O(1) alloc/free, no
    external fragmentation, some internal), the buddy allocator (powers of
    two, split/merge in O(log n), used by the Linux page allocator), and
    when you would still want first-fit / best-fit (large contiguous
    regions, e.g. GPU memory or disk extents). What is the difference between
    internal and external fragmentation, and which does each scheme suffer?
"""

import bisect
import random
from typing import Dict, List, Tuple


class Allocator:
    """Part 1: n-cell array, 0 = free else owner id; O(n) per op."""

    def __init__(self, n: int) -> None:
        pass

    def allocate(self, size: int, id: int) -> int:
        pass

    def free(self, id: int) -> int:
        pass


class RunAllocator:
    """Parts 2-3: free runs only. Tests read self.starts (sorted list of free
    run starts) and self.length (dict start -> run length)."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.starts: List[int] = []
        self.length: Dict[int, int] = {}
        self.owned: Dict[int, List[Tuple[int, int]]] = {}   # id -> [(start, size)]

    def allocate(self, size: int, id: int, policy: str = "first") -> int:
        pass

    def free(self, id: int) -> int:
        pass

    def fragmentation(self) -> float:
        pass


def _same_state(a: Allocator, b: RunAllocator) -> bool:
    """Test helper: the set of free cells is identical in both allocators."""
    free_cells = {i for i, v in enumerate(a.mem) if v == 0}
    run_cells = set()
    for s in b.starts:
        run_cells.update(range(s, s + b.length[s]))
    return free_cells == run_cells


if __name__ == "__main__":
    # Part 1 (LC2502 example)
    a = Allocator(10)
    assert a.allocate(1, 1) == 0
    assert a.allocate(1, 2) == 1
    assert a.allocate(1, 3) == 2
    assert a.free(2) == 1
    assert a.allocate(3, 4) == 3
    assert a.allocate(1, 1) == 1
    assert a.allocate(1, 1) == 6
    assert a.free(1) == 3
    assert a.allocate(10, 2) == -1
    assert a.free(7) == 0
    # mem: [_,_,3,4,4,4,_,_,_,_] -> first 3-run starts at 6
    assert a.allocate(3, 9) == 6 and a.allocate(3, 9) == -1
    assert a.allocate(2, 9) == 0 and a.allocate(1, 9) == 9 and a.free(9) == 6

    # Part 2 - same script, run-based
    r = RunAllocator(10)
    assert r.allocate(1, 1) == 0
    assert r.allocate(1, 2) == 1
    assert r.allocate(1, 3) == 2
    assert r.free(2) == 1
    assert r.allocate(3, 4) == 3
    assert r.allocate(1, 1) == 1
    assert r.allocate(1, 1) == 6
    assert r.free(1) == 3
    assert r.allocate(10, 2) == -1
    assert r.free(7) == 0
    assert r.starts == [0, 6] and r.length == {0: 2, 6: 4}      # coalesced
    big = RunAllocator(10**9)
    assert big.allocate(10**8, 1) == 0 and big.allocate(10**9, 2) == -1
    assert big.free(1) == 10**8 and big.starts == [0] and big.length == {0: 10**9}
    # randomized equivalence
    rng = random.Random(7)
    a2, r2 = Allocator(64), RunAllocator(64)
    for _ in range(3000):
        if rng.random() < 0.6:
            size, id = rng.randint(1, 8), rng.randint(1, 12)
            assert a2.allocate(size, id) == r2.allocate(size, id)
        else:
            id = rng.randint(1, 12)
            assert a2.free(id) == r2.free(id)
        assert _same_state(a2, r2)
    # free runs are always maximal: no adjacent runs
    assert all(r2.starts[i] + r2.length[r2.starts[i]] < r2.starts[i + 1]
               for i in range(len(r2.starts) - 1))

    # Part 3 - best fit + fragmentation
    def setup() -> RunAllocator:
        x = RunAllocator(10)
        assert x.allocate(3, 1) == 0 and x.allocate(2, 2) == 3
        assert x.allocate(2, 3) == 5 and x.allocate(3, 4) == 7
        assert x.free(1) == 3 and x.free(3) == 2
        return x
    f = setup()
    assert abs(f.fragmentation() - 0.4) < 1e-9
    assert f.allocate(2, 5, "first") == 0
    g = setup()
    assert g.allocate(2, 5, "best") == 5
    assert abs(g.fragmentation() - 0.0) < 1e-9                  # one run left
    assert g.allocate(4, 6, "best") == -1
    assert RunAllocator(5).fragmentation() == 0.0
    h = RunAllocator(5)
    h.allocate(5, 1)
    assert h.fragmentation() == 0.0
    print("ok")
