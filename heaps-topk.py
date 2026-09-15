"""
HEAPS / TOP-K / STREAMING ORDER STATISTICS.

Interviewer:

PART 1 -- Kth largest element (LC215).
  kth_largest_heap(nums, k): keep a MIN-heap of size k. O(n log k).
  kth_largest_quickselect(nums, k): average O(n), worst O(n^2) -- explain why
  and how random pivot helps. Both return the value, k is 1-indexed.

PART 2 -- Top K frequent hashtags (LC347).
  tags is a list of strings; return the k most frequent in any order.
  top_k_frequent_heap: O(n log k) with heapq.nlargest or a size-k heap.
  top_k_frequent_bucket: O(n) bucket sort by frequency (index = count).
  Tests use inputs with a unique answer set.

PART 3 -- K closest warehouses to origin (LC973).
  points = [(x, y)], return any order of the k closest by Euclidean distance.
  Max-heap of size k on squared distance (no sqrt).  O(n log k).

PART 4 -- Median from a data stream (LC295).
  class MedianFinder: add_num(x), find_median() -> float. Two heaps: max-heap
  of the low half, min-heap of the high half, sizes differ by at most 1.
  Follow-up to discuss (no code): sliding window median (LC480) -- same two
  heaps plus lazy deletion with a "to remove" counter, or a SortedList.

PART 5 -- Merge K sorted lists (LC23) as plain Python lists.
  merge_k_sorted([[1,4,5],[1,3,4],[2,6]]) -> [1,1,2,3,4,4,5,6]
  Heap of (value, list_index, position). O(N log k). Pitfall: tuple ties.

PART 6 -- Task scheduler with cooldown (LC621).
  tasks like ["A","A","A","B","B","B"], cooldown n between same tasks;
  return the minimum number of CPU intervals (idle allowed).
    n = 2 -> 8   ("A B idle A B idle A B")
  Either the max-heap + cooldown queue simulation or the closed-form
  max(len(tasks), (max_count - 1) * (n + 1) + #tasks_with_max_count).

PART 7 -- Kth largest in a stream (LC703).
  class KthLargest(k, nums): add(val) -> int returns the kth largest so far.
  O(log k) per add.

PART 8 -- Top K sellers by revenue in the last N minutes (streaming).
  class SellerLeaderboard(window: int, k: int)
      add(ts: int, seller: str, amount: float)   events arrive in non-decreasing ts
      query(now: int) -> List[Tuple[str, float]]  top k by revenue over (now-window, now]
                                                   ties broken by seller id ascending;
                                                   sellers with 0 revenue are omitted
  Use a deque of events for expiry + dict of running sums; on query, expire
  the front, then heapq.nlargest over the dict (O(S log k), S = active sellers).
  Be ready to explain why a "lazy max-heap with stale skips" is NOT a clean fix
  here: revenue DECREASES when events expire, so the heap top can be stale
  and the seller's true value has no fresh entry unless you push on every
  expiry -- the heap grows with every event and validation still needs the
  dict. (A sorted container / balanced tree keyed by revenue is the O(log S)
  update answer.)

PART 9 -- Reorganize string (LC767).
  Rearrange so no two adjacent characters are equal; return "" if impossible.
  Max-heap by count, always place the most frequent that is not the previous
  char. O(n log 26).

PART 10 -- IPO / maximize capital (LC502), briefly.
  You may pick at most k projects; project i needs capital[i] and yields
  profits[i]; starting capital w. Return the final capital. Min-heap on
  capital to unlock, max-heap on profit to pick. O(n log n).
"""
from __future__ import annotations

from typing import List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def kth_largest_heap(nums: List[int], k: int) -> int:
    pass


def kth_largest_quickselect(nums: List[int], k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 2
def top_k_frequent_heap(tags: List[str], k: int) -> List[str]:
    pass


def top_k_frequent_bucket(tags: List[str], k: int) -> List[str]:
    pass


# ---------------------------------------------------------------- Part 3
def k_closest(points: List[Tuple[int, int]], k: int) -> List[Tuple[int, int]]:
    pass


# ---------------------------------------------------------------- Part 4
class MedianFinder:
    def __init__(self) -> None:
        pass

    def add_num(self, x: int) -> None:
        pass

    def find_median(self) -> float:
        pass


# ---------------------------------------------------------------- Part 5
def merge_k_sorted(lists: List[List[int]]) -> List[int]:
    pass


# ---------------------------------------------------------------- Part 6
def least_interval(tasks: List[str], n: int) -> int:
    pass


# ---------------------------------------------------------------- Part 7
class KthLargest:
    def __init__(self, k: int, nums: List[int]) -> None:
        pass

    def add(self, val: int) -> int:
        pass


# ---------------------------------------------------------------- Part 8
class SellerLeaderboard:
    def __init__(self, window: int, k: int) -> None:
        pass

    def add(self, ts: int, seller: str, amount: float) -> None:
        pass

    def query(self, now: int) -> List[Tuple[str, float]]:
        pass


# ---------------------------------------------------------------- Part 9
def reorganize_string(s: str) -> str:
    pass


# ---------------------------------------------------------------- Part 10
def find_maximized_capital(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    pass


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
