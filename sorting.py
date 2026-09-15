"""
SORTING -- interviewer script (45-60 min; 3-4 parts typical, rest as follow-ups)

Setup: "Our ranking service re-orders product feeds and order queues a few
million times a day. I want to see that you can implement the classic sorts
from memory, know their trade-offs, and pick the right one under constraints."

Unless a part says otherwise, functions sort ints IN PLACE and also return the
list. No library sort unless the part says so.

------------------------------------------------------------------------------
Part 1  Quicksort with a RANDOMISED pivot, two ways:
        (a) Lomuto partition -- one index sweeps; pivot lands in its final
            slot p; recurse on [lo, p-1] and [p+1, hi].
        (b) Hoare partition  -- two indices walk toward each other; returns a
            split j with a[lo..j] <= a[j+1..hi]; the pivot is NOT guaranteed
            to sit at j; recurse on [lo, j] and [j+1, hi].
        Expected O(n log n); O(log n) stack if you recurse on the smaller
        half and loop on the larger.  Explain the O(n^2) worst case:
        adversarial order for a FIXED pivot (sorted / reversed input) -- fixed
        by randomisation -- and ALL-EQUAL input for Lomuto, which random
        pivots do NOT fix (fix: 3-way / Dutch-flag partition).

Part 2  Merge sort, returning a NEW list, stable:
        (a) top-down recursive, (b) bottom-up iterative, width doubling.
        O(n log n) always, O(n) extra.  When over quicksort?  (stability,
        linked lists, guaranteed bound, external sort.)

Part 3  Heap sort with a hand-written sift_down (no heapq).  Build the
        max-heap bottom-up in O(n) (Floyd), then swap root to the end n times.
        O(n log n) worst case, O(1) extra, NOT stable.

Part 4  Quickselect: k-th largest (LC215) in expected O(n), O(1) extra
        (do not mutate the caller's list).
        [3,2,1,5,6,4], k=2 -> 5 ; [3,2,3,1,2,4,5,5,6], k=4 -> 4
        Why is it O(n) on average when quicksort is O(n log n)?

Part 5  Linear-time sorts for bounded ints (return a new list):
        (a) counting_sort(a): values in a small range [min, max], negatives
            allowed.  O(n + range).  Make it STABLE (prefix sums, fill from
            the right) and say why stability matters (radix sort).
        (b) bucket_sort(a, bucket_size): values spread roughly uniformly;
            bucket = (x - min) // bucket_size; sort each bucket with
            insertion sort (Part 9); concatenate.  Expected O(n + k).

Part 6  Minimum number of swaps to sort an array of DISTINCT ints.
        [4,3,2,1] -> 2 ; [1,5,4,3,2] -> 2 ; [2,3,4,1,5] -> 3 ; [1,2,3] -> 0
        Hint: the permutation decomposes into cycles; a cycle of length L
        costs L-1 swaps.  O(n log n) for the argsort, O(n) space.

Part 7  Sort a k-sorted array: every element is at most k positions from its
        sorted position.  [6,5,3,2,8,10,9], k=3 -> [2,3,5,6,8,9,10]
        Target O(n log k) with a heap of size k+1 (heapq allowed).  Returns a
        new list.

Part 8  Orders are (order_id, priority, ts).  Sort by priority DESC, then ts
        ASC; orders tying on both keep their input order (stable).
        (a) sort_orders: one sorted() with a composite key;
        (b) sort_orders_two_pass: two passes relying on stability (ts first,
            then priority with reverse=True) -- explain why reverse=True keeps
            stability, and what to do when a DESC key is a string you cannot
            negate (two-pass trick or functools.cmp_to_key).

Part 9  Insertion sort of a[lo:hi] in place.  When is it the right choice?
        (tiny n -- Timsort runs use binary insertion below minrun 32-64;
        nearly-sorted input -> O(n + inversions); online input; stable, O(1)
        extra.)
------------------------------------------------------------------------------
"""
from __future__ import annotations

import heapq
import random
from typing import List, Optional, Tuple

Order = Tuple[str, int, int]   # (order_id, priority, timestamp)


# ----------------------------------------------------------------- Part 1
def quicksort_lomuto(a: List[int]) -> List[int]:
    pass


def quicksort_hoare(a: List[int]) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 2
def merge_sort_top_down(a: List[int]) -> List[int]:
    pass


def merge_sort_bottom_up(a: List[int]) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 3
def sift_down(a: List[int], i: int, n: int) -> None:
    """Restore the max-heap property for the subtree rooted at i in a[:n]."""
    pass


def heap_sort(a: List[int]) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 4
def find_kth_largest(nums: List[int], k: int) -> int:
    pass


# ----------------------------------------------------------------- Part 5
def counting_sort(a: List[int]) -> List[int]:
    pass


def bucket_sort(a: List[int], bucket_size: int = 10) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 6
def min_swaps_to_sort(a: List[int]) -> int:
    pass


# ----------------------------------------------------------------- Part 7
def sort_k_sorted(a: List[int], k: int) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 8
def sort_orders(orders: List[Order]) -> List[Order]:
    pass


def sort_orders_two_pass(orders: List[Order]) -> List[Order]:
    pass


# ----------------------------------------------------------------- Part 9
def insertion_sort(a: List[int], lo: int = 0, hi: Optional[int] = None) -> List[int]:
    pass


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    random.seed(20240915)
    cases: List[List[int]] = [
        [], [1], [2, 1], [3, 1, 2], [5, 5, 5, 5], [1, 2, 3, 4, 5], [5, 4, 3, 2, 1],
        [-3, 0, -1, 7, 2, 2], [2, 1, 2, 1, 2, 1],
    ]
    for _ in range(25):
        cases.append([random.randint(-50, 50) for _ in range(random.randint(0, 60))])
    cases.append([7] * 300)               # all-equal: Lomuto's O(n^2) case
    cases.append(list(range(2000)))       # sorted: a fixed pivot would recurse 2000 deep
    cases.append(list(range(2000, 0, -1)))

    # Part 1, 3, 9 -- in-place sorts
    for fn in (quicksort_lomuto, quicksort_hoare, heap_sort, insertion_sort):
        for c in cases:
            a = c[:]
            out = fn(a)
            assert out == sorted(c), fn.__name__
            assert a == sorted(c), fn.__name__          # really in place
    b = [9, 1, 8, 2, 7, 3]
    assert insertion_sort(b, 1, 5) == [9, 1, 2, 7, 8, 3]  # only a[1:5] sorted

    # Part 2, 5 -- return-a-new-list sorts
    for fn in (merge_sort_top_down, merge_sort_bottom_up, counting_sort, bucket_sort):
        for c in cases:
            a = c[:]
            assert fn(a) == sorted(c), fn.__name__
            assert a == c, fn.__name__                   # input untouched
    assert bucket_sort([3, 1, 2], 1) == [1, 2, 3]
    assert bucket_sort([100, -100, 0], 1000) == [-100, 0, 100]

    # Part 3 -- sift_down alone
    h = [1, 9, 8, 3, 4, 7, 6]
    sift_down(h, 0, len(h))
    assert h == [9, 4, 8, 3, 1, 7, 6]
    h = [10, 9, 8, 3, 4, 7, 6]
    sift_down(h, 0, len(h))
    assert h == [10, 9, 8, 3, 4, 7, 6]

    # Part 4
    assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert find_kth_largest([1], 1) == 1
    assert find_kth_largest([7, 7, 7, 7], 3) == 7
    for c in cases:
        if c:
            k = random.randint(1, len(c))
            orig = c[:]
            assert find_kth_largest(c, k) == sorted(c)[-k]
            assert c == orig

    # Part 6
    assert min_swaps_to_sort([4, 3, 2, 1]) == 2
    assert min_swaps_to_sort([1, 5, 4, 3, 2]) == 2
    assert min_swaps_to_sort([2, 3, 4, 1, 5]) == 3
    assert min_swaps_to_sort([1, 2, 3]) == 0
    assert min_swaps_to_sort([]) == 0
    assert min_swaps_to_sort([10, -1, 5]) == 2   # 3-cycle -> 2 swaps

    # Part 7
    assert sort_k_sorted([6, 5, 3, 2, 8, 10, 9], 3) == [2, 3, 5, 6, 8, 9, 10]
    assert sort_k_sorted([1, 2, 3], 0) == [1, 2, 3]
    assert sort_k_sorted([], 5) == []
    assert sort_k_sorted([3, 2, 1], 2) == [1, 2, 3]
    assert sort_k_sorted([2, 1, 4, 3, 6, 5], 1) == [1, 2, 3, 4, 5, 6]
    assert sort_k_sorted([1], 10) == [1]                  # k > n must not crash

    # Part 8
    orders: List[Order] = [
        ("a", 1, 30), ("b", 3, 20), ("c", 3, 10), ("d", 2, 10), ("e", 3, 20), ("f", 1, 5),
    ]
    expected = [("c", 3, 10), ("b", 3, 20), ("e", 3, 20), ("d", 2, 10), ("f", 1, 5), ("a", 1, 30)]
    assert sort_orders(orders) == expected
    assert sort_orders_two_pass(orders) == expected
    assert orders[0] == ("a", 1, 30)                      # input untouched
    assert sort_orders([]) == [] and sort_orders_two_pass([]) == []

    print("ok")
