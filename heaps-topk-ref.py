"""Reference solutions for heaps-topk.py -- see that file for the problem statements."""
from __future__ import annotations

import heapq
import random
from collections import Counter, deque
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def kth_largest_heap(nums: List[int], k: int) -> int:
    # Invariant: heap holds the k largest seen so far; heap[0] is the kth.
    # O(n log k), O(k) space. heapq.nlargest(k, nums)[-1] is the one-liner.
    heap: List[int] = []
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)  # pop-then-push in one sift
    return heap[0]


def kth_largest_quickselect(nums: List[int], k: int) -> int:
    # Average O(n): each round discards a constant fraction in expectation.
    # Worst O(n^2) with adversarial pivots -> random pivot. Three-way
    # partition handles duplicates without degrading.
    a = nums[:]
    target = len(a) - k  # index in ascending order
    lo, hi = 0, len(a) - 1
    while True:
        pivot = a[random.randint(lo, hi)]
        lt, i, gt = lo, lo, hi  # Dutch national flag
        while i <= gt:
            if a[i] < pivot:
                a[lt], a[i] = a[i], a[lt]
                lt += 1
                i += 1
            elif a[i] > pivot:
                a[gt], a[i] = a[i], a[gt]
                gt -= 1
            else:
                i += 1
        if target < lt:
            hi = lt - 1
        elif target > gt:
            lo = gt + 1
        else:
            return pivot


# ---------------------------------------------------------------- Part 2
def top_k_frequent_heap(tags: List[str], k: int) -> List[str]:
    cnt = Counter(tags)
    return heapq.nlargest(k, cnt, key=cnt.get)  # O(n log k)


def top_k_frequent_bucket(tags: List[str], k: int) -> List[str]:
    # A frequency can never exceed len(tags): bucket[f] = tags with count f.
    cnt = Counter(tags)
    buckets: List[List[str]] = [[] for _ in range(len(tags) + 1)]
    for t, f in cnt.items():
        buckets[f].append(t)
    out: List[str] = []
    for f in range(len(buckets) - 1, 0, -1):
        for t in buckets[f]:
            out.append(t)
            if len(out) == k:
                return out
    return out


# ---------------------------------------------------------------- Part 3
def k_closest(points: List[Tuple[int, int]], k: int) -> List[Tuple[int, int]]:
    # Max-heap of size k via negated distance; the top is the FARTHEST of the
    # k best so far, which is what we evict. O(n log k).
    heap: List[Tuple[int, int, int]] = []
    for x, y in points:
        d = -(x * x + y * y)
        if len(heap) < k:
            heapq.heappush(heap, (d, x, y))
        elif d > heap[0][0]:
            heapq.heapreplace(heap, (d, x, y))
    return [(x, y) for _, x, y in heap]


# ---------------------------------------------------------------- Part 4
class MedianFinder:
    # Invariant: every element of low <= every element of high, and
    # len(low) == len(high) or len(low) == len(high) + 1.
    def __init__(self) -> None:
        self.low: List[int] = []   # max-heap via negation
        self.high: List[int] = []  # min-heap

    def add_num(self, x: int) -> None:
        # Push through low, move its max to high, then rebalance: this order
        # guarantees the ordering invariant without comparing x to tops.
        heapq.heappush(self.low, -x)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def find_median(self) -> float:
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2.0
    # Sliding window median: same two heaps + Counter of "pending removals";
    # when a heap top is pending, pop it (lazy deletion). Track logical sizes
    # separately from physical sizes for rebalancing. O(n log n).


# ---------------------------------------------------------------- Part 5
def merge_k_sorted(lists: List[List[int]]) -> List[int]:
    # Heap entries (value, list_idx, pos): list_idx breaks value ties so the
    # comparison never falls through to something unorderable. O(N log k).
    heap: List[Tuple[int, int, int]] = []
    for i, lst in enumerate(lists):
        if lst:
            heap.append((lst[0], i, 0))
    heapq.heapify(heap)
    out: List[int] = []
    while heap:
        v, i, j = heapq.heappop(heap)
        out.append(v)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    return out


# ---------------------------------------------------------------- Part 6
def least_interval(tasks: List[str], n: int) -> int:
    # Simulation: each round takes up to n+1 DISTINCT tasks with the highest
    # remaining counts (max-heap of negative counts). If work remains after the
    # round the round costs a full n+1 slots (the missing ones are idle); the
    # LAST round costs only the tasks actually executed -- no trailing idle.
    # Pitfall (the original bug): charging the last round len(batch)+1 counts
    # tasks that finished (count hit 0) wrongly. O(T log 26).
    heap = [-c for c in Counter(tasks).values()]
    heapq.heapify(heap)
    time = 0
    while heap:
        done = 0
        batch: List[int] = []
        for _ in range(n + 1):
            if not heap:
                break
            c = heapq.heappop(heap) + 1  # negative counts: +1 means one done
            done += 1
            if c < 0:
                batch.append(c)
        for c in batch:
            heapq.heappush(heap, c)
        time += (n + 1) if heap else done
    return time


def least_interval_formula(tasks: List[str], n: int) -> int:
    cnt = Counter(tasks)
    mx = max(cnt.values())
    ties = sum(1 for c in cnt.values() if c == mx)
    return max(len(tasks), (mx - 1) * (n + 1) + ties)


# ---------------------------------------------------------------- Part 7
class KthLargest:
    def __init__(self, k: int, nums: List[int]) -> None:
        self.k = k
        self.heap = nums[:]
        heapq.heapify(self.heap)
        while len(self.heap) > k:
            heapq.heappop(self.heap)

    def add(self, val: int) -> int:
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, val)
        elif val > self.heap[0]:
            heapq.heapreplace(self.heap, val)
        return self.heap[0]


# ---------------------------------------------------------------- Part 8
class SellerLeaderboard:
    # events: deque of (ts, seller, amount) in arrival (= time) order.
    # sums: live revenue per seller within the window.
    # Expiry is amortised O(1) per event (each event is popped once).
    # Query: O(S log k) via nlargest over active sellers.
    def __init__(self, window: int, k: int) -> None:
        self.window = window
        self.k = k
        self.events: deque = deque()
        self.sums: Dict[str, float] = {}

    def add(self, ts: int, seller: str, amount: float) -> None:
        self.events.append((ts, seller, amount))
        self.sums[seller] = self.sums.get(seller, 0.0) + amount

    def _expire(self, now: int) -> None:
        cutoff = now - self.window  # keep ts > cutoff
        while self.events and self.events[0][0] <= cutoff:
            _, seller, amount = self.events.popleft()
            self.sums[seller] -= amount
            if self.sums[seller] <= 1e-9:  # drop empty sellers so S stays small
                del self.sums[seller]

    def query(self, now: int) -> List[Tuple[str, float]]:
        self._expire(now)
        # key: revenue desc, then seller id asc. Negate revenue and use
        # nsmallest so the tuple order gives both directions at once.
        best = heapq.nsmallest(self.k, self.sums.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(s, v) for s, v in best]
    # Why not a lazy max-heap? Lazy deletion works when a stale entry is
    # always DOMINATED by a fresh one (Dijkstra: keys only decrease, the fresh
    # smaller key surfaces first). Here revenue goes DOWN on expiry, so the
    # stale (higher) entry surfaces first and the fresh value is buried; you
    # must push on every expiry AND validate every popped entry against the
    # dict, and the heap grows with every event. Use a balanced tree /
    # SortedList keyed by (revenue, seller) for O(log S) updates instead.


# ---------------------------------------------------------------- Part 9
def reorganize_string(s: str) -> str:
    # Greedy: always emit the most frequent char that differs from the last
    # emitted. Hold the previous char out of the heap for one step.
    # Feasible iff max_count <= (n + 1) // 2.
    cnt = Counter(s)
    if max(cnt.values()) > (len(s) + 1) // 2:
        return ""
    heap = [(-c, ch) for ch, c in cnt.items()]
    heapq.heapify(heap)
    out: List[str] = []
    prev: Optional[Tuple[int, str]] = None
    while heap:
        c, ch = heapq.heappop(heap)
        out.append(ch)
        if prev is not None:
            heapq.heappush(heap, prev)
        prev = (c + 1, ch) if c + 1 < 0 else None
    return "".join(out)


# ---------------------------------------------------------------- Part 10
def find_maximized_capital(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    # Min-heap by capital holds locked projects; move everything affordable
    # into a max-heap by profit; pick the top. O(n log n + k log n).
    locked = sorted(zip(capital, profits))
    i = 0
    avail: List[int] = []
    for _ in range(k):
        while i < len(locked) and locked[i][0] <= w:
            heapq.heappush(avail, -locked[i][1])
            i += 1
        if not avail:
            break
        w -= heapq.heappop(avail)
    return w


# ---------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    assert kth_largest_heap([3, 2, 1, 5, 6, 4], 2) == 5
    assert kth_largest_heap([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert kth_largest_quickselect([3, 2, 1, 5, 6, 4], 2) == 5
    assert kth_largest_quickselect([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert kth_largest_quickselect([1], 1) == 1

    # Part 2
    tags = ["#fyp"] * 5 + ["#ootd"] * 3 + ["#sale"] * 2 + ["#new"]
    assert sorted(top_k_frequent_heap(tags, 2)) == ["#fyp", "#ootd"]
    assert sorted(top_k_frequent_bucket(tags, 2)) == ["#fyp", "#ootd"]
    assert top_k_frequent_bucket(["a"], 1) == ["a"]
    assert sorted(top_k_frequent_bucket(tags, 4)) == ["#fyp", "#new", "#ootd", "#sale"]

    # Part 3
    assert sorted(k_closest([(1, 3), (-2, 2)], 1)) == [(-2, 2)]
    assert sorted(k_closest([(3, 3), (5, -1), (-2, 4)], 2)) == [(-2, 4), (3, 3)]

    # Part 4
    mf = MedianFinder()
    mf.add_num(1)
    mf.add_num(2)
    assert mf.find_median() == 1.5
    mf.add_num(3)
    assert mf.find_median() == 2.0
    mf.add_num(0)
    mf.add_num(0)
    assert mf.find_median() == 1.0

    # Part 5
    assert merge_k_sorted([[1, 4, 5], [1, 3, 4], [2, 6]]) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_sorted([]) == []
    assert merge_k_sorted([[], [1], []]) == [1]

    # Part 6
    assert least_interval(list("AAABBB"), 2) == 8
    assert least_interval(list("AAABBB"), 0) == 6
    assert least_interval(list("AAAAAABCDEFG"), 2) == 16
    assert least_interval(list("AAABBBCC"), 3) == 10  # (3-1)*(3+1) + 2 ties

    # Part 7
    kl = KthLargest(3, [4, 5, 8, 2])
    assert kl.add(3) == 4
    assert kl.add(5) == 5
    assert kl.add(10) == 5
    assert kl.add(9) == 8
    assert kl.add(4) == 8

    # Part 8
    lb = SellerLeaderboard(window=10, k=2)
    lb.add(1, "s1", 50.0)
    lb.add(2, "s2", 30.0)
    lb.add(3, "s3", 40.0)
    assert lb.query(3) == [("s1", 50.0), ("s3", 40.0)]
    lb.add(8, "s2", 25.0)  # s2 = 55
    assert lb.query(8) == [("s2", 55.0), ("s1", 50.0)]
    assert lb.query(11) == [("s2", 55.0), ("s3", 40.0)]  # ts=1 expired: window is (1, 11]
    assert lb.query(12) == [("s3", 40.0), ("s2", 25.0)]  # ts=2 expired, ts=3 still in (2, 12]
    assert lb.query(13) == [("s2", 25.0)]                # ts=3 expired: (3, 13] excludes 3
    assert lb.query(18) == []                            # ts=8 expired: (8, 18] excludes 8
    lb2 = SellerLeaderboard(window=5, k=3)
    lb2.add(0, "a", 1.0)
    lb2.add(0, "b", 1.0)
    assert lb2.query(0) == [("a", 1.0), ("b", 1.0)]  # tie -> id ascending

    # Part 9
    def _ok(s: str) -> bool:
        return all(s[i] != s[i + 1] for i in range(len(s) - 1))
    r = reorganize_string("aab")
    assert sorted(r) == list("aab") and _ok(r)
    assert reorganize_string("aaab") == ""
    r = reorganize_string("vvvlo")
    assert sorted(r) == sorted("vvvlo") and _ok(r)

    # Part 10
    assert find_maximized_capital(2, 0, [1, 2, 3], [0, 1, 1]) == 4
    assert find_maximized_capital(3, 0, [1, 2, 3], [0, 1, 2]) == 6
    assert find_maximized_capital(1, 0, [1, 2, 3], [1, 1, 1]) == 0
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Heap of size k vs quickselect vs sort -- when do you pick which?
# A: Streaming / n >> k / memory-bound: size-k heap (O(n log k), O(k) space).
#    Everything in memory, one-shot: quickselect O(n) avg. k ~ n: just sort.
# Q: How does heapq give a max-heap?
# A: Negate the key (or wrap in a class with __lt__). Never mutate an element
#    already inside the heap -- push a new entry and lazily skip the old one.
# Q: Part 8 at 1M events/sec across many machines?
# A: Per-shard leaderboards keyed by seller hash, each returns its top k, then
#    merge (a seller lives on exactly one shard so local top-k is exact).
#    Approximate: count-min sketch + heavy hitters, or time-bucketed sums
#    (e.g. 1-minute buckets) so expiry is O(#buckets) rather than O(events).
# Q: Why is the median trick two heaps rather than one sorted list?
# A: Insertion into a list is O(n); two heaps give O(log n) insert and O(1)
#    median. A balanced BST / SortedList also works and additionally supports
#    deletion (needed for the sliding window variant).
# Q: Stale entries in the KthLargest stream class?
# A: None -- values never change once inserted; the heap only ever evicts
#    from the top, so no laziness is required.
