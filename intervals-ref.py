"""
INTERVALS -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "Almost everything here is 'sort by one endpoint, then sweep'. Before
you code, tell me which endpoint you sort by and why, and what 'overlap'
means at the boundary (touching intervals)."
Convention for ALL parts: intervals are [start, end] with start <= end;
[1,3] and [3,5] TOUCH. Merge/insert treat touching as overlapping; the
scheduling parts (3, 4, 7) treat touching as compatible.

------------------------------------------------------------------------------
Part 1  Merge intervals (LC56). Return the merged list sorted by start.
        Example: [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]]
                 [[1,4],[4,5]] -> [[1,5]]
        Constraints: 1 <= n <= 1e4.  Target: O(n log n).

Part 2  Insert interval (LC57). `intervals` is already sorted and
        non-overlapping; insert `new` and merge as needed. Return a NEW list.
        Example: [[1,3],[6,9]] + [2,5] -> [[1,5],[6,9]]
                 [[1,2],[3,5],[6,7],[8,10],[12,16]] + [4,8] -> [[1,2],[3,10],[12,16]]
        Target: O(n), no sort.

Part 3  Non-overlapping intervals (LC435) -- asked at ByteDance, Sept 2026.
        Minimum number of intervals to REMOVE so the rest do not overlap.
        Touching intervals ([1,2],[2,3]) do not overlap.
        Example: [[1,2],[2,3],[3,4],[1,3]] -> 1;  [[1,2],[1,2],[1,2]] -> 2
        Constraints: 1 <= n <= 1e5.
        Target: O(n log n) greedy -- be ready to say WHICH endpoint you sort
        by and why the greedy is optimal.

Part 4  Meeting rooms II (LC253), flavoured: each interval is a scheduled
        livestream [start, end); how many concurrent stream slots does the
        platform need at peak? A slot freed at time t can be reused at t.
        Example: [[0,30],[5,10],[15,20]] -> 2;  [[7,10],[2,4]] -> 1
        Constraints: 1 <= n <= 1e4.
        Target: O(n log n) with a min-heap of end times (or the two-sorted-
        arrays sweep).

Part 5  Interval list intersections (LC986). Two sorted, internally
        disjoint lists; return every intersection (closed intervals, so a
        single point [5,5] counts).
        Example: A=[[0,2],[5,10],[13,23],[24,25]], B=[[1,5],[8,12],[15,24],[25,26]]
                 -> [[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]
        Target: O(|A| + |B|) two pointers.

Part 6  Common free windows (LC759-style). Every seller has a sorted list
        of BUSY intervals. Given working hours [lo, hi] and a minimum
        window length `min_len` (>= 1), return every maximal window inside
        [lo, hi] where NO seller is busy and whose length is >= min_len,
        sorted by start.
        Example: [[[1,2],[5,6]],[[1,3]],[[4,10]]], lo=0, hi=12, min_len=1
                 -> [[0,1],[3,4],[10,12]];  same with min_len=2 -> [[10,12]]
        Target: O(N log N) over N total intervals (O(N log k) with a k-way
        heap merge is the follow-up).

Part 7  Maximum-weight non-overlapping intervals (LC1235, job scheduling).
        Parallel arrays start[i], end[i], profit[i]; choose a subset with no
        overlaps (touching allowed) maximising total profit.
        Example: start=[1,2,3,3], end=[3,4,5,6], profit=[50,10,40,70] -> 120
        Constraints: 1 <= n <= 5e4, 1 <= profit <= 1e4.
        Target: O(n log n) -- sort by end, DP over the sorted order, bisect
        for the latest compatible interval.
------------------------------------------------------------------------------
"""
from __future__ import annotations

import heapq
from bisect import bisect_right
from typing import List


# ---------------------------------------------------------------- Part 1
def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    # Sort by start. The current interval overlaps the last merged one iff
    # its start <= that end; then extend (max, not replace: [1,10],[2,3]).
    out: List[List[int]] = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])  # fresh list, never alias the input
    return out  # O(n log n)


# ---------------------------------------------------------------- Part 2
def insert_interval(intervals: List[List[int]], new: List[int]) -> List[List[int]]:
    # Three phases: everything strictly left of `new`, everything that
    # overlaps (absorb into new), everything strictly right.
    s, e = new
    out: List[List[int]] = []
    i, n = 0, len(intervals)
    while i < n and intervals[i][1] < s:
        out.append(intervals[i])
        i += 1
    while i < n and intervals[i][0] <= e:
        s = min(s, intervals[i][0])
        e = max(e, intervals[i][1])
        i += 1
    out.append([s, e])
    out.extend(intervals[i:])
    return out  # O(n)


# ---------------------------------------------------------------- Part 3
def erase_overlap_intervals(intervals: List[List[int]]) -> int:
    # Sort by END and greedily keep the interval that ends earliest: it
    # leaves the most room for the rest (classic activity selection).
    # Answer = n - (max number we can keep).
    kept = 0
    end = float("-inf")
    for s, e in sorted(intervals, key=lambda iv: iv[1]):
        if s >= end:  # touching is fine
            kept += 1
            end = e
    return len(intervals) - kept  # O(n log n)


# ---------------------------------------------------------------- Part 4
def min_slots(intervals: List[List[int]]) -> int:
    # Sort by start; heap holds end times of streams currently running.
    # If the earliest-ending stream has finished (end <= start) reuse its
    # slot; else open a new one. Heap size at the end = peak concurrency.
    heap: List[int] = []
    for s, e in sorted(intervals):
        if heap and heap[0] <= s:
            heapq.heapreplace(heap, e)
        else:
            heapq.heappush(heap, e)
    return len(heap)  # O(n log n)


# ---------------------------------------------------------------- Part 5
def interval_intersection(a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
    # Intersection of the current pair is [max starts, min ends] if non-
    # empty. Advance whichever interval ENDS first -- it cannot intersect
    # anything further in the other list.
    out: List[List[int]] = []
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if lo <= hi:
            out.append([lo, hi])
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out  # O(|a| + |b|)


# ---------------------------------------------------------------- Part 6
def free_windows(schedules: List[List[List[int]]], lo: int, hi: int, min_len: int = 1) -> List[List[int]]:
    # Flatten all busy intervals, sort by start, sweep with `cur` = the end
    # of everything busy so far. A gap between cur and the next start is a
    # free window; clip to [lo, hi].
    busy = sorted(iv for sched in schedules for iv in sched)
    out: List[List[int]] = []
    cur = lo
    for s, e in busy:
        if min(s, hi) - cur >= min_len:
            out.append([cur, min(s, hi)])
        cur = max(cur, e)
        if cur >= hi:
            break
    if hi - cur >= min_len:
        out.append([cur, hi])
    return out  # O(N log N)


# ---------------------------------------------------------------- Part 7
def max_profit(start: List[int], end: List[int], profit: List[int]) -> int:
    # Sort jobs by end. best[i] = max profit using the first i jobs (by end
    # order); ends[] mirrors the processed jobs so bisect_right(ends, s)
    # gives how many processed jobs end <= s (compatible with this job).
    jobs = sorted(zip(end, start, profit))
    ends: List[int] = []
    best = [0]
    for e, s, p in jobs:
        i = bisect_right(ends, s)  # touching allowed: end == s is compatible
        best.append(max(best[-1], best[i] + p))
        ends.append(e)
    return best[-1]  # O(n log n)


if __name__ == "__main__":
    # Part 1
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([]) == []
    assert merge_intervals([[1, 4], [2, 3]]) == [[1, 4]]
    assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]
    assert merge_intervals([[1, 10], [2, 3], [4, 5], [11, 12]]) == [[1, 10], [11, 12]]
    src = [[1, 3], [2, 6]]; merge_intervals(src); assert src == [[1, 3], [2, 6]]  # input untouched

    # Part 2
    assert insert_interval([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]
    assert insert_interval([], [5, 7]) == [[5, 7]]
    assert insert_interval([[1, 5]], [6, 8]) == [[1, 5], [6, 8]]
    assert insert_interval([[1, 5]], [0, 0]) == [[0, 0], [1, 5]]
    assert insert_interval([[3, 5], [12, 15]], [6, 6]) == [[3, 5], [6, 6], [12, 15]]
    assert insert_interval([[1, 5]], [2, 3]) == [[1, 5]]
    assert insert_interval([[1, 5]], [5, 7]) == [[1, 7]]

    # Part 3
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    assert erase_overlap_intervals([]) == 0
    assert erase_overlap_intervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2
    assert erase_overlap_intervals([[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]]) == 2

    # Part 4
    assert min_slots([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_slots([[7, 10], [2, 4]]) == 1
    assert min_slots([]) == 0
    assert min_slots([[1, 5], [2, 6], [3, 7], [4, 8]]) == 4
    assert min_slots([[1, 3], [3, 5]]) == 1
    assert min_slots([[1, 4], [2, 5], [4, 6]]) == 2
    assert min_slots([[9, 10], [4, 9], [4, 17]]) == 2

    # Part 5
    assert interval_intersection([[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]]) == \
        [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    assert interval_intersection([[1, 3], [5, 9]], []) == []
    assert interval_intersection([[1, 7]], [[3, 10]]) == [[3, 7]]
    assert interval_intersection([[1, 2]], [[3, 4]]) == []
    assert interval_intersection([[1, 10]], [[2, 3], [4, 5], [11, 12]]) == [[2, 3], [4, 5]]

    # Part 6
    assert free_windows([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]], 0, 12) == [[0, 1], [3, 4], [10, 12]]
    assert free_windows([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]], 0, 12, 2) == [[10, 12]]
    assert free_windows([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]], 1, 10) == [[3, 4]]
    assert free_windows([[[1, 3], [6, 7]], [[2, 4]], [[2, 5], [9, 12]]], 1, 12) == [[5, 6], [7, 9]]
    assert free_windows([], 9, 17) == [[9, 17]]
    assert free_windows([[[0, 24]]], 9, 17) == []
    assert free_windows([[[10, 11]]], 9, 17, 6) == [[11, 17]]
    assert free_windows([[[8, 10], [20, 22]]], 9, 17) == [[10, 17]]

    # Part 7
    assert max_profit([1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]) == 120
    assert max_profit([1, 2, 3, 4, 6], [3, 5, 10, 6, 9], [20, 20, 100, 70, 60]) == 150
    assert max_profit([1, 1, 1], [2, 3, 4], [5, 6, 4]) == 6
    assert max_profit([1], [2], [5]) == 5
    assert max_profit([1, 3], [3, 5], [10, 10]) == 20
    assert max_profit([1, 2], [3, 4], [10, 10]) == 10

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part 1 -- what changes if touching intervals should NOT merge?
# A: The overlap test becomes s < out[-1][1] (strict).
# Q: Part 3 -- why sort by end rather than by start?
# A: Keeping the interval that ends earliest maximises room for later ones;
#    sorting by start and keeping the shorter of two overlapping intervals is
#    an equivalent but messier argument.
# Q: Part 4 -- without a heap?
# A: Sort starts and ends separately; sweep starts, advancing an end pointer
#    whenever ends[j] <= starts[i]; track max(i - j + 1). Same O(n log n).
# Q: Part 4 -- how would you also report WHEN the peak happens?
# A: Sweep events (+1 at start, -1 at end, ends before starts on ties) and
#    record the time when the running count first reaches its maximum.
# Q: Part 6 -- k sellers, each with a very long sorted list; can you avoid
#    sorting everything?
# A: k-way merge with a heap keyed on start: O(N log k) instead of O(N log N).
# Q: Part 7 -- why is bisect needed; why not scan back?
# A: Scanning back for the latest compatible job is O(n) per job -> O(n^2).
#    With ends sorted, bisect_right(ends, start) is O(log n).
