"""Reference solutions for binary-search.py -- see that file for the problem statements."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import Callable, List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def lower_bound(a: List[int], x: int) -> int:
    # Half-open search on [lo, hi).
    # LOOP INVARIANT: every element in a[:lo] is < x, every element in a[hi:]
    # is >= x, and 0 <= lo <= hi <= len(a). The answer is therefore always in
    # [lo, hi]. Termination: mid is in [lo, hi), so `lo = mid + 1` or
    # `hi = mid` strictly shrinks the interval each step => O(log n).
    # When lo == hi the invariant gives: a[:lo] < x <= a[lo:], i.e. lo is the
    # first index with a[lo] >= x.
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2  # Python ints do not overflow; in C use lo + (hi-lo)//2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(a: List[int], x: int) -> int:
    # Same skeleton; invariant: a[:lo] <= x and a[hi:] > x.
    # The only difference is `<=` instead of `<` in the test.
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def lower_bound_bisect(a: List[int], x: int) -> int:
    return bisect_left(a, x)


def upper_bound_bisect(a: List[int], x: int) -> int:
    return bisect_right(a, x)


# ---------------------------------------------------------------- Part 2
def search_rotated(nums: List[int], target: int) -> int:
    # Closed interval [lo, hi]. At every step at least ONE half is sorted
    # (compare nums[lo] with nums[mid]); check whether target lies inside that
    # sorted half's range, otherwise go to the other half. O(log n).
    # Pitfall: use `nums[lo] <= nums[mid]` (with equality) so that a 2-element
    # window like [3, 1] classifies mid=lo as "left sorted".
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:  # left half [lo, mid] is sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:  # right half [mid, hi] is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def search_rotated_dups(nums: List[int], target: int) -> bool:
    # With duplicates nums[lo] == nums[mid] == nums[hi] tells us nothing about
    # which side is sorted (e.g. [1,1,1,0,1] vs [1,0,1,1,1]); shrink both ends
    # by one and retry. That step is why the worst case degrades to O(n)
    # (all-equal array with a missing target).
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return True
        if nums[lo] == nums[mid] == nums[hi]:
            lo += 1
            hi -= 1
        elif nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return False


# ---------------------------------------------------------------- Part 3
def single_non_duplicate(nums: List[int]) -> int:
    # Before the single element pairs start at EVEN indices (0,1),(2,3),...;
    # after it they start at ODD indices. Force mid to be even and test whether
    # nums[mid] == nums[mid+1]: if yes the pair is intact so the single is to
    # the right (lo = mid + 2), else it is at or left of mid (hi = mid).
    # Invariant: lo is even, the single lies in [lo, hi], hi - lo is even.
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if mid % 2 == 1:
            mid -= 1
        if nums[mid] == nums[mid + 1]:
            lo = mid + 2
        else:
            hi = mid
    return nums[lo]


# ---------------------------------------------------------------- Part 4
def find_peak_element(nums: List[int]) -> int:
    # If nums[mid] < nums[mid+1] there is guaranteed a peak in (mid, n-1]
    # (the sequence rises and must eventually fall because nums[n] = -inf).
    # Otherwise a peak exists in [0, mid]. Invariant: [lo, hi] contains a peak.
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2  # mid < hi so mid + 1 is always valid
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo


# ---------------------------------------------------------------- Part 5
def first_bad_version(n: int, is_bad: Callable[[int], bool]) -> int:
    # Predicate is monotone (F...F T...T): classic "first True" lower bound.
    # Invariant: versions < lo are good, versions >= hi are bad (hi = n is
    # guaranteed bad by the problem). ceil(log2(n)) calls.
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        if is_bad(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- Part 6
def min_eating_speed(piles: List[int], h: int) -> int:
    # Binary search on the answer. feasible(k) = "can finish within h hours" is
    # monotone: F...F T...T over k in [1, max(piles)]. Find the first T.
    # Pitfall: ceil division (p + k - 1) // k, not round(). O(n log max).
    def feasible(k: int) -> bool:
        return sum((p + k - 1) // k for p in piles) <= h

    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- Part 7
def ship_within_days(weights: List[int], days: int) -> int:
    # Answer space [max(weights), sum(weights)]: lower end because every single
    # order must fit; upper end because everything in one day always works.
    # Greedy packing is optimal for a fixed capacity (fill until overflow).
    def feasible(cap: int) -> bool:
        used, cur = 1, 0
        for w in weights:
            if cur + w > cap:
                used += 1
                cur = 0
            cur += w
        return used <= days

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- Part 8
def split_array(nums: List[int], k: int) -> int:
    # Identical to Part 7 with "days" = k parts. The DP alternative is
    # O(k * n^2); binary search on answer is O(n log sum). Note that using
    # FEWER than k parts is always convertible to exactly k (split further
    # never raises the max), so `parts <= k` is the right test.
    def feasible(cap: int) -> bool:
        parts, cur = 1, 0
        for x in nums:
            if cur + x > cap:
                parts += 1
                cur = 0
            cur += x
        return parts <= k

    lo, hi = max(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- Part 9
def find_median_sorted_arrays(a: List[int], b: List[int]) -> float:
    # Partition a into a[:i] | a[i:] and b into b[:j] | b[j:] with
    # i + j = half = (m + n + 1) // 2 so the left side holds the lower half.
    # Correct partition <=> max(left) <= min(right), i.e. a[i-1] <= b[j] and
    # b[j-1] <= a[i]. Binary search i over the SHORTER array so j stays valid.
    # Sentinels +-inf handle i or j at the ends. O(log min(m, n)).
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    half = (m + n + 1) // 2
    INF = float("inf")
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2
        j = half - i
        a_left = a[i - 1] if i > 0 else -INF
        a_right = a[i] if i < m else INF
        b_left = b[j - 1] if j > 0 else -INF
        b_right = b[j] if j < n else INF
        if a_left <= b_right and b_left <= a_right:
            if (m + n) % 2 == 1:
                return float(max(a_left, b_left))
            return (max(a_left, b_left) + min(a_right, b_right)) / 2
        if a_left > b_right:
            hi = i - 1  # took too many from a
        else:
            lo = i + 1  # took too few from a
    raise ValueError("inputs not sorted")


# ---------------------------------------------------------------- Part 10
def find_closest_elements(arr: List[int], k: int, x: int) -> List[int]:
    # Search the left edge L of the answer window arr[L:L+k], L in [0, n-k].
    # Compare the element just outside on the left (arr[mid]) against the one
    # just outside on the right (arr[mid+k]): if x - arr[mid] > arr[mid+k] - x
    # the window must move right. Ties (equal distance) keep the smaller
    # value, which the `>` (not `>=`) gives for free. O(log(n-k) + k).
    lo, hi = 0, len(arr) - k
    while lo < hi:
        mid = (lo + hi) // 2
        if x - arr[mid] > arr[mid + k] - x:
            lo = mid + 1
        else:
            hi = mid
    return arr[lo:lo + k]


# ---------------------------------------------------------------- Part 11
def search_matrix(matrix: List[List[int]], target: int) -> bool:
    # Flatten virtually: index p -> matrix[p // n][p % n]. O(log(m*n)).
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n
    while lo < hi:
        mid = (lo + hi) // 2
        v = matrix[mid // n][mid % n]
        if v == target:
            return True
        if v < target:
            lo = mid + 1
        else:
            hi = mid
    return False


def search_matrix_ii(matrix: List[List[int]], target: int) -> bool:
    # Staircase from the top-right: moving left decreases, moving down
    # increases, so each comparison eliminates one full row or column.
    # O(m + n). (Binary search per row would be O(m log n) -- worse when m~n.)
    if not matrix or not matrix[0]:
        return False
    r, c = 0, len(matrix[0]) - 1
    while r < len(matrix) and c >= 0:
        v = matrix[r][c]
        if v == target:
            return True
        if v > target:
            c -= 1
        else:
            r += 1
    return False


# ---------------------------------------------------------------- Part 12
def price_at(history: List[Tuple[int, int]], t: int) -> Optional[int]:
    # "Last change with ts <= t" = bisect_right on ts, minus one.
    # 3.9 has no key= for bisect, so bisect on a tuple that sorts after every
    # (t, price): (t, inf). Alternative: keep a parallel list of timestamps.
    i = bisect_right(history, (t, float("inf"))) - 1
    return history[i][1] if i >= 0 else None


class PriceHistory:
    # Append-only log with parallel arrays; get is O(log n), set amortised O(1).
    # Equal timestamp overwrites (last write wins); decreasing ts is rejected so
    # the arrays stay sorted without a full re-sort.
    def __init__(self) -> None:
        self._ts: List[int] = []
        self._price: List[int] = []

    def set(self, ts: int, price: int) -> None:
        if self._ts and ts < self._ts[-1]:
            raise ValueError("timestamps must be non-decreasing")
        if self._ts and ts == self._ts[-1]:
            self._price[-1] = price
            return
        self._ts.append(ts)
        self._price.append(price)

    def get(self, t: int) -> Optional[int]:
        i = bisect_right(self._ts, t) - 1
        return self._price[i] if i >= 0 else None


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


# INTERVIEWER FOLLOW-UPS
# Q: `while lo < hi` with hi = mid, versus `while lo <= hi` with hi = mid - 1?
# A: Both work; half-open [lo, hi) never needs the "-1/+1 off-by-one dance"
#    and the loop ends with lo == hi as the answer. Use closed intervals when
#    you must return -1 on a miss (Part 2) and the half-open form when you
#    want an insertion point (Parts 1, 5-8).
# Q: How do you recognise "binary search on the answer"?
# A: The question asks for a min/max threshold and "is threshold X feasible?"
#    is monotone (once feasible, every larger/smaller X is too). Bounds come
#    from the problem (max element .. sum), feasibility is a greedy O(n) pass.
# Q: Why can't Part 2 with duplicates stay O(log n)?
# A: [1,1,1,1,0,1,1,1] -- any O(log n) algorithm reads o(n) cells and cannot
#    distinguish this from all-ones; an adversary hides the 0 where you did
#    not look. So O(n) worst case is a lower bound, not a weakness of the code.
# Q: Part 12 at scale -- millions of price changes per SKU, hot reads?
# A: Store the history in a sorted column (ts array) per SKU; bisect is cache
#    friendly. Cache the CURRENT price separately since most reads are "now".
#    For historical range replay use a time-series store with per-day chunks.
# Q: Part 9 -- why search the shorter array only?
# A: j = half - i must stay in [0, n]; that holds automatically for every
#    i in [0, m] only when m <= n. It also gives the log(min) bound.
