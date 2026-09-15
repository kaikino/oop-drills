from __future__ import annotations

"""Leftmost Memory Block Allocator (TikTok OA, Sept 2026; LC2502) -- REFERENCE

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


# ---------------------------------------------------------------------------
# Part 1
# DATA SHAPE: mem: List[int] of length n; 0 = free, else the owning id.
# COMPLEXITY: allocate O(n) single left-to-right scan counting the current
#             free run; free O(n).
# PITFALL:    reset the run counter on a used cell; the block starts at
#             i - size + 1 when the run reaches `size`. Return -1 without any
#             side effect.
# ---------------------------------------------------------------------------
class Allocator:
    def __init__(self, n: int) -> None:
        self.mem = [0] * n

    def allocate(self, size: int, id: int) -> int:
        run = 0
        for i, v in enumerate(self.mem):
            run = run + 1 if v == 0 else 0
            if run == size:
                start = i - size + 1
                for j in range(start, i + 1):
                    self.mem[j] = id
                return start
        return -1

    def free(self, id: int) -> int:
        freed = 0
        for i, v in enumerate(self.mem):
            if v == id:
                self.mem[i] = 0
                freed += 1
        return freed


# ---------------------------------------------------------------------------
# Part 2 + 3
# DATA SHAPE: starts: sorted List[int] of free-run starts;
#             length: Dict[int, int] start -> run length;
#             owned: Dict[int, List[Tuple[int, int]]] id -> [(start, size)].
# INVARIANT:  free runs are disjoint, sorted, and maximal (no two adjacent
#             free runs: coalescing on free keeps this). Every cell is in
#             exactly one free run or one owned block.
# COMPLEXITY: allocate O(#runs) scan (first fit stops early, best fit scans
#             all); free O(log #runs) bisect per block + list insert.
#             A balanced tree / sortedcontainers would make inserts O(log).
# PITFALL:    carving from the LEFT of a run keeps "leftmost" semantics;
#             coalescing must check both the predecessor (pred_end == start)
#             and the successor (end == succ_start).
# ---------------------------------------------------------------------------
class RunAllocator:
    def __init__(self, n: int) -> None:
        self.n = n
        self.starts: List[int] = [0] if n > 0 else []
        self.length: Dict[int, int] = {0: n} if n > 0 else {}
        self.owned: Dict[int, List[Tuple[int, int]]] = {}

    def _pick(self, size: int, policy: str) -> int:
        """Index into self.starts of the run to carve, or -1."""
        if policy == "first":
            for i, s in enumerate(self.starts):
                if self.length[s] >= size:
                    return i
            return -1
        best, best_len = -1, 0
        for i, s in enumerate(self.starts):
            L = self.length[s]
            if L >= size and (best == -1 or L < best_len):   # strict < keeps leftmost tie
                best, best_len = i, L
        return best

    def allocate(self, size: int, id: int, policy: str = "first") -> int:
        i = self._pick(size, policy)
        if i == -1:
            return -1
        s = self.starts[i]
        L = self.length.pop(s)
        if L == size:
            del self.starts[i]
        else:                                   # carve from the left
            self.starts[i] = s + size
            self.length[s + size] = L - size
        self.owned.setdefault(id, []).append((s, size))
        return s

    def _insert_free(self, start: int, size: int) -> None:
        i = bisect.bisect_left(self.starts, start)
        end = start + size
        # merge with successor
        if i < len(self.starts) and self.starts[i] == end:
            size += self.length.pop(end)
            del self.starts[i]
        # merge with predecessor
        if i > 0:
            p = self.starts[i - 1]
            if p + self.length[p] == start:
                self.length[p] += size
                return
        self.starts.insert(i, start)
        self.length[start] = size

    def free(self, id: int) -> int:
        blocks = self.owned.pop(id, [])
        for s, size in blocks:
            self._insert_free(s, size)
        return sum(size for _, size in blocks)

    def fragmentation(self) -> float:
        total = sum(self.length.values())
        if total == 0:
            return 0.0
        return 1.0 - max(self.length.values()) / total


# ---------------------------------------------------------------------------
# Part 4 - model answer
# A linear first-fit scan is O(#runs) per call and, worse, first-fit on one
# global list scatters small blocks everywhere (external fragmentation: total
# free memory is enough but no run is large enough).
# Size classes / slab: keep a free list per size class (8, 16, 32, ... or per
#   kernel object type). alloc = pop, free = push, O(1); pages are dedicated
#   to one class so freed slots are reused by the same class. No external
#   fragmentation, but internal fragmentation (a 33-byte request gets 48).
#   glibc's tcache/fastbins, jemalloc, and the Linux SLUB allocator do this.
# Buddy: memory is split into power-of-two blocks; a request of size s gets
#   the smallest 2^k >= s, splitting a bigger block recursively; on free, a
#   block merges with its "buddy" (the other half of the block it was split
#   from, address ^ size) while the buddy is free. O(log n) both ways, cheap
#   coalescing, bounded external fragmentation, internal fragmentation up to
#   50%. Linux uses it for physical pages.
# First/best fit stays useful for large, variable-size regions where waste
#   matters more than speed: GPU/device memory arenas, file-system extents,
#   VM address space. Best-fit lowers waste per allocation but leaves tiny
#   slivers; "next fit" and "worst fit" exist for the same reasons.
# Internal fragmentation = wasted space inside an allocated block (rounding
#   up). External = free space that exists but is not contiguous. Slabs:
#   internal only. First/best fit: external mainly. Buddy: both, bounded.
# ---------------------------------------------------------------------------


def _same_state(a: Allocator, b: RunAllocator) -> bool:
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


# INTERVIEWER FOLLOW-UPS
# Q: allocate(size, id) with size == 0?
#    A: Define it: return -1 or 0 without allocating; say which and why
#       (LC guarantees size >= 1).
# Q: Part 2 allocate is O(#runs). Can first-fit be O(log #runs)?
#    A: Keep a segment tree / balanced tree over runs keyed by start with the
#       max run length in each subtree; descend left-first to the first
#       subtree with max >= size. Best-fit: a second ordered structure keyed
#       by (length, start).
# Q: Many allocations of the same size (e.g. 4 KB pages)?
#    A: Size-class free lists: O(1) push/pop and no scanning at all.
# Q: What does free(id) cost if one id owns thousands of blocks?
#    A: O(blocks * log #runs); acceptable, or cap blocks per id, or keep the
#       blocks list sorted and merge adjacent ones on free.
# Q: Thread safety?
#    A: One lock around the run structure, or per-arena allocators with
#       thread-local caches (what jemalloc does) to avoid contention.
