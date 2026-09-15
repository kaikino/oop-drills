"""
TIKTOK OA (Sept 2026) -- reconstructed problem set (interviewer script)

Setup: "These are the OA-style mediums TikTok has been sending. The titles
are real; the specs below are fully pinned down so tests are unambiguous.
Read the spec back before coding -- OA problems hide their edge cases in
the wording."

------------------------------------------------------------------------------
Part A  Local maxima in sensor data.
        `a[i]` is a sensor reading. Index i is a local maximum if a[i] is
        STRICTLY greater than every neighbour it has: interior indices have
        two neighbours, the two edges have one. A single-element array has
        one local maximum; an empty array has none.
        A1: count_local_maxima(a) -> int
            Example: [1,3,2,4,1] -> 2;  [5,4,3] -> 1;  [2,2,2] -> 0
        A2: local_maxima_per_window(a, k) -> List[int]: for every window
            a[i..i+k-1] (1 <= k <= n) count the local maxima of that window
            CONSIDERED ON ITS OWN (window edges have one neighbour).
            Example: [1,3,2,4,1], k=3 -> [1,2,1]
        Constraints: n <= 1e5.  Target: A1 O(n); A2 O(n) total (prefix sums
        over interior peaks + O(1) edge checks per window), not O(nk).

Part B  Alternating tile groups. `s` is a string over {'B','W'}.
        B1: count_alternating_groups(s): split s into MAXIMAL runs in which
            every adjacent pair differs; return how many runs have length
            >= 2 (a lone tile is not a group).
            Example: "BWBWWBW" -> 2;  "BBB" -> 0;  "BWWBWWB" -> 3
        B2: longest_alternating_one_repaint(s): you may repaint at most
            ONE tile to the other colour; return the length of the longest
            alternating substring achievable.
            Example: "BBWB" -> 4;  "BBBB" -> 3;  "BWBW" -> 4
        Constraints: len(s) <= 1e5.  Target: O(n) each (B2: for each of the
        two ideal patterns, longest window with <= 1 mismatch).

Part C  Lowest number in an open range.
        `taken` is a SORTED list of ints (duplicates possible). For each
        query (lo, hi) return the smallest integer x with lo < x < hi that is
        not in `taken`, or -1 if none exists.
        Example: taken=[1,2,3,5,7,8]: (0,5) -> 4; (0,4) -> -1; (5,7) -> 6;
                 (7,9) -> -1; (-5,1) -> -4
        Constraints: n, q <= 1e5, values up to 1e9 (so no marking arrays).
        Target: O((n + q) log n) -- precompute the end of each consecutive
        run, bisect per query.

Part D  Count one-swap number pairs.
        Non-negative ints `nums`. A pair (i, j), i < j, is good if nums[i]
        and nums[j] are equal, OR swapping two digit positions inside ONE of
        them produces the other. Numbers are compared as decimal strings
        without leading zeros (so 1000 and 1 are NOT a pair; 120 and 102
        are). Return the number of good pairs.
        Example: [12,21,12] -> 3;  [123,132,213,321] -> 3;  [1,10,100] -> 0
        Constraints: n <= 1e5, each number < 1e10.
        Target: O(n * L^2) with a hashmap of seen strings; careful not to
        double-count when a swap reproduces the same string.

Part E  Catch fish with reusable baits.
        `fish` = list of (bait_type, value). `baits` = list of bait types
        you own (a multiset). Each bait can be used at most r times, and
        each fish needs one use of a bait of ITS type. Maximise the total
        value of fish caught.
        Example: fish=[(1,10),(1,5),(1,7),(2,3)], baits=[1], r=2 -> 17
                 same fish, baits=[1,2], r=1 -> 13
        Constraints: |fish|, |baits| <= 1e5, values >= 0.
        Target: O(F log F) -- per type, take the top (count * r) values.

Part F  Minimum sum after making all elements distinct.
        You may only INCREMENT elements (by any amount). Make all values
        distinct and return the minimum possible sum.
        Example: [1,2,2] -> 6;  [3,2,1,2,1,7] -> 22;  [1,1,1,1] -> 10
        Target: O(n log n) -- sort, push each value up to max(v, prev+1).

Part G  Grid paths with obstacles.
        Lattice points (x, y) with 0 <= x <= n, 0 <= y <= m. Start at
        (0, 0), reach (n, m), each step is right (x+1) or up (y+1). Some
        points are obstacles and cannot be visited. Count the paths (if the
        start or end is an obstacle the answer is 0).
        Example: n=2, m=2, no obstacles -> 6;  with obstacle (1,1) -> 2
        Constraints: n, m <= 1000.  Target: O(nm) DP.

Part H  Build blocks from a starting position.
        `heights` is an m x n grid; from a cell you may step to a 4-adjacent
        cell if its height <= current height + 1 (any descent is free).
        Return how many cells are reachable from `start`, including start.
        Example: [[0,1,2],[5,4,3],[9,9,9]], start (0,0) -> 6
        Constraints: m, n <= 1000.  Target: O(mn) BFS.
------------------------------------------------------------------------------
"""
from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict, deque
from typing import Dict, List, Set, Tuple


# ---------------------------------------------------------------- Part A
def count_local_maxima(a: List[int]) -> int:
    # Edge indices only need to beat their single neighbour.
    n = len(a)
    if n == 0:
        return 0
    if n == 1:
        return 1
    count = 0
    for i in range(n):
        left_ok = i == 0 or a[i] > a[i - 1]
        right_ok = i == n - 1 or a[i] > a[i + 1]
        if left_ok and right_ok:
            count += 1
    return count  # O(n)


def local_maxima_per_window(a: List[int], k: int) -> List[int]:
    # Whether an INTERIOR index of a window is a local max does not depend
    # on the window (it needs to beat both array neighbours), so precompute
    # a prefix count of interior peaks. Only the two window EDGES need an
    # explicit check per window.
    n = len(a)
    if k < 1 or k > n:
        return []
    if k == 1:
        return [1] * n
    pre = [0] * (n + 1)
    for i in range(n):
        peak = 0 < i < n - 1 and a[i] > a[i - 1] and a[i] > a[i + 1]
        pre[i + 1] = pre[i] + (1 if peak else 0)
    out: List[int] = []
    for l in range(n - k + 1):
        r = l + k - 1
        count = pre[r] - pre[l + 1]  # interior indices l+1 .. r-1
        if a[l] > a[l + 1]:
            count += 1
        if a[r] > a[r - 1]:
            count += 1
        out.append(count)
    return out  # O(n)


# ---------------------------------------------------------------- Part B
def count_alternating_groups(s: str) -> int:
    # Walk maximal alternating runs; count those of length >= 2.
    n = len(s)
    groups = 0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and s[j + 1] != s[j]:
            j += 1
        if j - i + 1 >= 2:
            groups += 1
        i = j + 1
    return groups  # O(n)


def longest_alternating_one_repaint(s: str) -> int:
    # An alternating substring matches one of two ideal patterns (BWBW... or
    # WBWB...) exactly. One repaint fixes one mismatch, so for each pattern
    # find the longest window with at most 1 mismatch (sliding window).
    other = {"B": "W", "W": "B"}
    n = len(s)
    best = 0
    for first in "BW":
        def expected(i: int) -> str:
            return first if i % 2 == 0 else other[first]

        left = bad = 0
        for right in range(n):
            if s[right] != expected(right):
                bad += 1
            while bad > 1:
                if s[left] != expected(left):
                    bad -= 1
                left += 1
            best = max(best, right - left + 1)
    return best  # O(n)


# ---------------------------------------------------------------- Part C
def lowest_in_open_range(taken: List[int], queries: List[Tuple[int, int]]) -> List[int]:
    # Dedupe, then run_end[i] = last value of the consecutive run starting
    # at vals[i]. Query: candidate = lo + 1; if it is taken, jump to the end
    # of its run + 1. Then check it is still < hi.
    vals = sorted(set(taken))
    n = len(vals)
    run_end = [0] * n
    for i in range(n - 1, -1, -1):
        if i + 1 < n and vals[i + 1] == vals[i] + 1:
            run_end[i] = run_end[i + 1]
        else:
            run_end[i] = vals[i]
    out: List[int] = []
    for lo, hi in queries:
        cand = lo + 1
        i = bisect_left(vals, cand)
        if i < n and vals[i] == cand:
            cand = run_end[i] + 1
        out.append(cand if cand < hi else -1)
    return out  # O((n + q) log n)


# ---------------------------------------------------------------- Part D
def count_one_swap_pairs(nums: List[int]) -> int:
    # For each number, generate the SET of strings reachable by <= 1 swap
    # (the set dedupes swaps of equal digits, which would otherwise count
    # the "equal" case twice). Add how many earlier numbers match any of
    # them, then record this number. Symmetry (x->y iff y->x) means looking
    # backwards only is enough.
    seen: Counter = Counter()
    total = 0
    for x in nums:
        s = str(x)
        length = len(s)
        variants: Set[str] = {s}
        for i in range(length):
            for j in range(i + 1, length):
                if s[i] != s[j]:
                    t = list(s)
                    t[i], t[j] = t[j], t[i]
                    variants.add("".join(t))
        for v in variants:
            total += seen[v]  # a variant with a leading zero never matches
        seen[s] += 1
    return total  # O(n * L^2)


# ---------------------------------------------------------------- Part E
def max_fish_value(fish: List[Tuple[int, int]], baits: List[int], r: int) -> int:
    # Types are independent: capacity(type) = (#baits of type) * r; take the
    # most valuable fish of that type up to capacity.
    by_type: Dict[int, List[int]] = defaultdict(list)
    for t, v in fish:
        by_type[t].append(v)
    bait_count = Counter(baits)
    total = 0
    for t, values in by_type.items():
        cap = bait_count[t] * r
        if cap <= 0:
            continue
        values.sort(reverse=True)
        total += sum(values[:cap])
    return total  # O(F log F)


# ---------------------------------------------------------------- Part F
def min_sum_distinct(nums: List[int]) -> int:
    # Sorted order: each value must be at least prev + 1; raising it to
    # exactly that is optimal (any higher only costs more).
    total = 0
    prev = None
    for x in sorted(nums):
        if prev is not None and x <= prev:
            x = prev + 1
        total += x
        prev = x
    return total  # O(n log n)


# ---------------------------------------------------------------- Part G
def count_grid_paths(n: int, m: int, obstacles: List[Tuple[int, int]]) -> int:
    # ways[x][y] = ways[x-1][y] + ways[x][y-1]; an obstacle cell is 0.
    blocked = set(obstacles)
    if (0, 0) in blocked or (n, m) in blocked:
        return 0
    ways = [[0] * (m + 1) for _ in range(n + 1)]
    ways[0][0] = 1
    for x in range(n + 1):
        for y in range(m + 1):
            if (x, y) in blocked:
                ways[x][y] = 0
                continue
            if x > 0:
                ways[x][y] += ways[x - 1][y]
            if y > 0:
                ways[x][y] += ways[x][y - 1]
    return ways[n][m]  # O(nm) time; O(m) with a rolling row


# ---------------------------------------------------------------- Part H
def count_reachable(heights: List[List[int]], start: Tuple[int, int]) -> int:
    # Plain BFS; the edge rule is directional (climb <= 1, descend freely),
    # so "reachable from start" is NOT the same as a connected component.
    m, n = len(heights), len(heights[0])
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) not in seen \
                    and heights[nr][nc] <= heights[r][c] + 1:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return len(seen)  # O(mn)


if __name__ == "__main__":
    # Part A
    assert count_local_maxima([1, 3, 2, 4, 1]) == 2
    assert count_local_maxima([5, 4, 3]) == 1
    assert count_local_maxima([1, 2, 3]) == 1
    assert count_local_maxima([2, 2, 2]) == 0
    assert count_local_maxima([7]) == 1
    assert count_local_maxima([1, 3, 3, 1]) == 0
    assert count_local_maxima([]) == 0
    assert count_local_maxima([5, 1, 5, 1, 5]) == 3

    assert local_maxima_per_window([1, 3, 2, 4, 1], 3) == [1, 2, 1]
    assert local_maxima_per_window([1, 2, 3, 4], 2) == [1, 1, 1]
    assert local_maxima_per_window([4, 3, 2, 1], 2) == [1, 1, 1]
    assert local_maxima_per_window([1, 1, 1], 2) == [0, 0]
    assert local_maxima_per_window([5, 1, 5, 1, 5], 5) == [3]
    assert local_maxima_per_window([5, 1, 5, 1, 5], 1) == [1, 1, 1, 1, 1]
    assert local_maxima_per_window([2, 1, 3], 3) == [2]
    assert local_maxima_per_window([1, 3, 2, 4, 1], 5) == [2]
    assert local_maxima_per_window([1, 2], 3) == []

    # Part B
    assert count_alternating_groups("BWBWWBW") == 2
    assert count_alternating_groups("BBB") == 0
    assert count_alternating_groups("BW") == 1
    assert count_alternating_groups("") == 0
    assert count_alternating_groups("WBWBWB") == 1
    assert count_alternating_groups("BWWBWWB") == 3
    assert count_alternating_groups("B") == 0

    assert longest_alternating_one_repaint("BBWB") == 4
    assert longest_alternating_one_repaint("BWBW") == 4
    assert longest_alternating_one_repaint("BBBB") == 3
    assert longest_alternating_one_repaint("B") == 1
    assert longest_alternating_one_repaint("") == 0
    assert longest_alternating_one_repaint("BWBBWB") == 4
    assert longest_alternating_one_repaint("WBWBWB") == 6
    assert longest_alternating_one_repaint("BWWB") == 3
    assert longest_alternating_one_repaint("BB") == 2

    # Part C
    taken = [1, 2, 3, 5, 7, 8]
    qs = [(0, 5), (0, 4), (3, 7), (5, 7), (7, 9), (8, 10), (-5, 1), (10, 20), (2, 3), (3, 4), (3, 5)]
    assert lowest_in_open_range(taken, qs) == [4, -1, 4, 6, -1, 9, -4, 11, -1, -1, 4]
    assert lowest_in_open_range([], [(1, 3), (1, 2)]) == [2, -1]
    assert lowest_in_open_range([1, 1, 2], [(0, 3), (0, 4)]) == [-1, 3]
    assert lowest_in_open_range([5], [(4, 6), (4, 7), (5, 6), (6, 6)]) == [-1, 6, -1, -1]

    # Part D
    assert count_one_swap_pairs([12, 21, 12]) == 3
    assert count_one_swap_pairs([1, 10, 100]) == 0
    assert count_one_swap_pairs([123, 132, 213, 321]) == 3
    assert count_one_swap_pairs([11, 11, 11]) == 3
    assert count_one_swap_pairs([]) == 0
    assert count_one_swap_pairs([5]) == 0
    assert count_one_swap_pairs([1122, 2211, 1212]) == 2
    assert count_one_swap_pairs([100, 100, 10]) == 1
    assert count_one_swap_pairs([120, 102, 210, 201]) == 4
    assert count_one_swap_pairs([7, 7, 77]) == 1

    # Part E
    fish = [(1, 10), (1, 5), (1, 7), (2, 3)]
    assert max_fish_value(fish, [1], 2) == 17
    assert max_fish_value(fish, [1, 2], 1) == 13
    assert max_fish_value(fish, [1, 2], 0) == 0
    assert max_fish_value([], [1, 2], 5) == 0
    assert max_fish_value(fish, [1, 1], 1) == 17
    assert max_fish_value(fish, [3], 9) == 0
    assert max_fish_value(fish, [1, 2], 10) == 25
    assert max_fish_value(fish, [2, 2, 2], 1) == 3

    # Part F
    assert min_sum_distinct([1, 2, 2]) == 6
    assert min_sum_distinct([3, 2, 1, 2, 1, 7]) == 22
    assert min_sum_distinct([]) == 0
    assert min_sum_distinct([5]) == 5
    assert min_sum_distinct([1, 1, 1, 1]) == 10
    assert min_sum_distinct([0, 0]) == 1
    assert min_sum_distinct([4, 1, 3]) == 8

    # Part G
    assert count_grid_paths(2, 2, []) == 6
    assert count_grid_paths(2, 2, [(1, 1)]) == 2
    assert count_grid_paths(0, 0, []) == 1
    assert count_grid_paths(3, 0, []) == 1
    assert count_grid_paths(1, 1, [(0, 0)]) == 0
    assert count_grid_paths(2, 2, [(2, 2)]) == 0
    assert count_grid_paths(3, 3, [(1, 0), (0, 1)]) == 0
    assert count_grid_paths(3, 2, []) == 10
    assert count_grid_paths(3, 3, [(1, 1), (2, 2)]) == 4

    # Part H
    assert count_reachable([[0, 1, 2], [5, 4, 3], [9, 9, 9]], (0, 0)) == 6
    assert count_reachable([[0, 1, 2], [5, 5, 3], [9, 9, 4]], (0, 0)) == 5
    assert count_reachable([[9, 0], [0, 0]], (0, 0)) == 4
    assert count_reachable([[0, 9], [9, 9]], (0, 0)) == 1
    assert count_reachable([[3]], (0, 0)) == 1
    assert count_reachable([[1, 3, 1]], (0, 0)) == 1
    assert count_reachable([[1, 3, 1]], (0, 1)) == 3
    assert count_reachable([[1, 2, 3], [2, 3, 4], [3, 4, 5]], (0, 0)) == 9

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part A2 -- why is the interior/edge split the key to O(n)?
# A: An interior index's status is a property of the ARRAY, so it can be
#    prefix-summed once; only the two window edges change meaning per window.
# Q: Part B2 -- why does "<= 1 mismatch against an ideal pattern" equal "one
#    repaint"?
# A: A substring is alternating iff it equals one of the two ideal patterns
#    over its range; each repaint flips exactly one mismatch into a match.
# Q: Part C -- why not a set of taken values and a while loop?
# A: A query like (0, 1e9) with a long taken run would walk the whole run;
#    run_end jumps over it in O(1) after one bisect.
# Q: Part D -- where does the double-counting come from?
# A: Swapping two equal digits reproduces the number itself; with a LIST of
#    variants the equal-number case is counted once per such swap. A set
#    fixes it (and skipping s[i] == s[j] avoids generating them at all).
# Q: Part E -- what if a bait could be used on fish of ANY type?
# A: Then it is a single global capacity: sort all fish by value and take the
#    top (#baits * r).
# Q: Part G -- memory for n, m = 1000?
# A: Keep only the previous row (or a single row updated in place):
#    O(m) instead of O(nm). Also consider modular arithmetic if asked.
# Q: Part H -- DFS instead of BFS?
# A: Works, but recursion depth can hit 1e6 on a 1000x1000 grid; use an
#    explicit stack or BFS.
