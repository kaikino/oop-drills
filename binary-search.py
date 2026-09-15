"""
BINARY SEARCH -- bounds / rotated arrays / search-on-answer / partitions.

Interviewer:

PART 1 -- lower_bound / upper_bound by hand.
  `a` is sorted ascending. Write
    lower_bound(a, x) -> first index i with a[i] >= x   (len(a) if none)
    upper_bound(a, x) -> first index i with a[i] >  x   (len(a) if none)
  State the loop invariant precisely and say why the loop terminates.
  Then show me the bisect one-liners (lower_bound_bisect / upper_bound_bisect).
    lower_bound([1,2,2,2,5], 2) -> 1 ; upper_bound([1,2,2,2,5], 2) -> 4
  Target: O(log n).  Note: count of x == upper - lower.

PART 2 -- Search in rotated sorted array (LC33 / LC81).
  A sorted array of distinct SKU ids was rotated at an unknown pivot.
    search_rotated([4,5,6,7,0,1,2], 0) -> 4 ; ... , 3) -> -1
  Then the same with duplicates allowed, returning bool:
    search_rotated_dups([2,5,6,0,0,1,2], 0) -> True
  Target: O(log n) distinct; O(n) worst case with duplicates -- explain why.

PART 3 -- Single element in a sorted array (LC540, ByteDance intern round).
  Every element appears exactly twice except one; the array is sorted.
    single_non_duplicate([1,1,2,3,3,4,4,8,8]) -> 2
  Target: O(log n), O(1). Hint: look at the parity of the index of the first
  copy of each pair before vs after the single element.

PART 4 -- Find peak element (LC162).
  nums[i] != nums[i+1]; treat nums[-1] = nums[n] = -inf. Return the index of
  any peak.  find_peak_element([1,2,3,1]) -> 2.  Target: O(log n).

PART 5 -- First bad version (LC278).
  Versions 1..n; once a version is bad all later ones are bad. You get a
  predicate `is_bad(v)`; minimise calls.  first_bad_version(5, v >= 4) -> 4.
  Target: O(log n) calls.

PART 6 -- Koko eating bananas (LC875).
  `piles` of bananas, `h` hours; eating speed k per hour, one pile per hour
  (a pile smaller than k still uses a full hour). Return the minimum integer k.
    min_eating_speed([3,6,7,11], 8) -> 4
  Binary search on the ANSWER: feasibility is monotone in k.
  Target: O(n log max(piles)).

PART 7 -- Daily shipping weight limit (LC1011).
  Orders `weights` must ship in the given order, one truck load per day, at
  most `days` days. What is the smallest daily weight limit that works?
    ship_within_days([1,2,3,4,5,6,7,8,9,10], 5) -> 15
  Target: O(n log sum).

PART 8 -- Split array largest sum (LC410).
  Split `nums` into `k` non-empty contiguous parts minimising the largest
  part sum.  split_array([7,2,5,10,8], 2) -> 18.  Same skeleton as Part 7.

PART 9 -- Median of two sorted arrays (LC4).
    find_median_sorted_arrays([1,3], [2]) -> 2.0 ; ([1,2], [3,4]) -> 2.5
  Target: O(log min(m, n)) -- binary search the partition of the shorter one.

PART 10 -- Find K closest elements (LC658).
  Sorted `arr`, return the k elements closest to x (ties -> smaller value),
  in ascending order.  find_closest_elements([1,2,3,4,5], 4, 3) -> [1,2,3,4]
  Target: O(log(n - k) + k) -- binary search the LEFT edge of the window.

PART 11 -- Search a 2D matrix I & II (LC74 / LC240).
  I : each row sorted, first element of a row > last of the previous row.
      Treat as one flat sorted array.  Target: O(log(m*n)).
  II: rows and columns each sorted ascending, nothing else.
      Start at the top-right corner (staircase).  Target: O(m + n).

PART 12 -- Price in effect at time t.
  A product's price history is an append-only list of (ts, price) sorted by ts.
  Return the price in effect at time t (the last change with ts <= t), or None
  if the product had no price yet.
    price_at([(1, 100), (5, 80), (9, 120)], 7) -> 80 ; ... , 0) -> None
  Then wrap it as a class PriceHistory with set(ts, price) / get(t) (LC981
  TimeMap flavour; equal ts overwrites; ts must never decrease).
  Target: O(log n) per get.  Pitfall: Python 3.9 bisect has no `key=`.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def lower_bound(a: List[int], x: int) -> int:
    pass


def upper_bound(a: List[int], x: int) -> int:
    pass


def lower_bound_bisect(a: List[int], x: int) -> int:
    pass


def upper_bound_bisect(a: List[int], x: int) -> int:
    pass


# ---------------------------------------------------------------- Part 2
def search_rotated(nums: List[int], target: int) -> int:
    pass


def search_rotated_dups(nums: List[int], target: int) -> bool:
    pass


# ---------------------------------------------------------------- Part 3
def single_non_duplicate(nums: List[int]) -> int:
    pass


# ---------------------------------------------------------------- Part 4
def find_peak_element(nums: List[int]) -> int:
    pass


# ---------------------------------------------------------------- Part 5
def first_bad_version(n: int, is_bad: Callable[[int], bool]) -> int:
    pass


# ---------------------------------------------------------------- Part 6
def min_eating_speed(piles: List[int], h: int) -> int:
    pass


# ---------------------------------------------------------------- Part 7
def ship_within_days(weights: List[int], days: int) -> int:
    pass


# ---------------------------------------------------------------- Part 8
def split_array(nums: List[int], k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 9
def find_median_sorted_arrays(a: List[int], b: List[int]) -> float:
    pass


# ---------------------------------------------------------------- Part 10
def find_closest_elements(arr: List[int], k: int, x: int) -> List[int]:
    pass


# ---------------------------------------------------------------- Part 11
def search_matrix(matrix: List[List[int]], target: int) -> bool:
    pass


def search_matrix_ii(matrix: List[List[int]], target: int) -> bool:
    pass


# ---------------------------------------------------------------- Part 12
def price_at(history: List[Tuple[int, int]], t: int) -> Optional[int]:
    pass


class PriceHistory:
    def __init__(self) -> None:
        pass

    def set(self, ts: int, price: int) -> None:
        pass

    def get(self, t: int) -> Optional[int]:
        pass


# ---------------------------------------------------------------- tests
def _is_peak(nums: List[int], i: int) -> bool:
    left = nums[i - 1] if i > 0 else float("-inf")
    right = nums[i + 1] if i + 1 < len(nums) else float("-inf")
    return nums[i] > left and nums[i] > right


if __name__ == "__main__":
    # Part 1
    a = [1, 2, 2, 2, 5]
    assert lower_bound(a, 2) == 1 and upper_bound(a, 2) == 4
    assert lower_bound(a, 3) == 4 and upper_bound(a, 3) == 4
    assert lower_bound(a, 0) == 0 and upper_bound(a, 0) == 0
    assert lower_bound(a, 9) == 5 and upper_bound(a, 9) == 5
    assert lower_bound([], 1) == 0 and upper_bound([], 1) == 0
    for x in range(-1, 8):
        assert lower_bound(a, x) == lower_bound_bisect(a, x)
        assert upper_bound(a, x) == upper_bound_bisect(a, x)
    assert upper_bound(a, 2) - lower_bound(a, 2) == 3  # count of 2s

    # Part 2
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search_rotated([1], 0) == -1
    assert search_rotated([1, 3], 3) == 1
    assert search_rotated([3, 1], 1) == 1
    assert search_rotated([1, 2, 3, 4, 5], 4) == 3  # not rotated at all
    assert search_rotated_dups([2, 5, 6, 0, 0, 1, 2], 0) is True
    assert search_rotated_dups([2, 5, 6, 0, 0, 1, 2], 3) is False
    assert search_rotated_dups([1, 0, 1, 1, 1], 0) is True
    assert search_rotated_dups([1, 1, 1, 0, 1], 0) is True
    assert search_rotated_dups([1, 1, 1, 1], 2) is False

    # Part 3
    assert single_non_duplicate([1, 1, 2, 3, 3, 4, 4, 8, 8]) == 2
    assert single_non_duplicate([3, 3, 7, 7, 10, 11, 11]) == 10
    assert single_non_duplicate([1]) == 1
    assert single_non_duplicate([1, 1, 2]) == 2
    assert single_non_duplicate([0, 1, 1]) == 0

    # Part 4
    assert find_peak_element([1, 2, 3, 1]) == 2
    for nums in ([1, 2, 1, 3, 5, 6, 4], [1], [1, 2], [2, 1], [1, 3, 2, 4]):
        assert _is_peak(nums, find_peak_element(nums))

    # Part 5
    calls = [0]

    def make_is_bad(first_bad: int) -> Callable[[int], bool]:
        def is_bad(v: int) -> bool:
            calls[0] += 1
            return v >= first_bad
        return is_bad

    assert first_bad_version(5, make_is_bad(4)) == 4
    assert first_bad_version(1, make_is_bad(1)) == 1
    assert first_bad_version(10, make_is_bad(10)) == 10
    calls[0] = 0
    assert first_bad_version(10 ** 9, make_is_bad(123456789)) == 123456789
    assert calls[0] <= 31

    # Part 6
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23
    assert min_eating_speed([1], 1) == 1

    # Part 7
    assert ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15
    assert ship_within_days([3, 2, 2, 4, 1, 4], 3) == 6
    assert ship_within_days([1, 2, 3, 1, 1], 4) == 3
    assert ship_within_days([10], 1) == 10
    assert ship_within_days([5, 5, 5], 3) == 5

    # Part 8
    assert split_array([7, 2, 5, 10, 8], 2) == 18
    assert split_array([1, 2, 3, 4, 5], 2) == 9
    assert split_array([1, 4, 4], 3) == 4
    assert split_array([1, 4, 4], 1) == 9

    # Part 9
    assert find_median_sorted_arrays([1, 3], [2]) == 2.0
    assert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5
    assert find_median_sorted_arrays([], [1]) == 1.0
    assert find_median_sorted_arrays([2], []) == 2.0
    assert find_median_sorted_arrays([1, 1, 1], [1, 1]) == 1.0
    assert find_median_sorted_arrays([1, 2, 3, 4, 5, 6], [7]) == 4.0
    assert find_median_sorted_arrays([100], [1, 2, 3, 4]) == 3.0

    # Part 10
    assert find_closest_elements([1, 2, 3, 4, 5], 4, 3) == [1, 2, 3, 4]
    assert find_closest_elements([1, 2, 3, 4, 5], 4, -1) == [1, 2, 3, 4]
    assert find_closest_elements([1, 2, 3, 4, 5], 4, 10) == [2, 3, 4, 5]
    assert find_closest_elements([1, 1, 2, 3, 3], 2, 2) == [1, 2]  # tie -> smaller
    assert find_closest_elements([1, 3, 5], 3, 4) == [1, 3, 5]

    # Part 11
    m1 = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(m1, 3) is True
    assert search_matrix(m1, 13) is False
    assert search_matrix(m1, 60) is True and search_matrix(m1, 1) is True
    assert search_matrix([], 1) is False and search_matrix([[]], 1) is False
    m2 = [[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]]
    assert search_matrix_ii(m2, 5) is True
    assert search_matrix_ii(m2, 20) is False
    assert search_matrix_ii(m2, 30) is True and search_matrix_ii(m2, 1) is True
    assert search_matrix_ii([[]], 1) is False

    # Part 12
    hist = [(1, 100), (5, 80), (9, 120)]
    assert price_at(hist, 7) == 80
    assert price_at(hist, 0) is None
    assert price_at(hist, 1) == 100
    assert price_at(hist, 5) == 80
    assert price_at(hist, 100) == 120
    assert price_at([], 3) is None
    ph = PriceHistory()
    assert ph.get(3) is None
    ph.set(1, 100)
    ph.set(5, 80)
    ph.set(5, 85)  # same ts overwrites
    ph.set(9, 120)
    assert ph.get(0) is None and ph.get(1) == 100 and ph.get(5) == 85
    assert ph.get(7) == 85 and ph.get(9) == 120 and ph.get(10 ** 9) == 120
    try:
        ph.set(4, 1)
        assert False, "ts must not decrease"
    except ValueError:
        pass
    print("ok")
