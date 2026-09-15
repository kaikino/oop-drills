"""
SORTING -- reference solutions.  See sorting.py for the script.

Recurring pitfalls:
  * Hoare partition: the pivot must be the FIRST element of the range (or you
    must return i-1 style bounds), otherwise the recursion on [lo, j] can
    fail to shrink and loops forever.
  * Lomuto with `<` puts equal elements on the right; all-equal input then
    degenerates to O(n^2) no matter how the pivot is chosen.
  * Heap sort's build phase starts at n//2 - 1 (last internal node); the
    extraction phase sifts within a SHRINKING heap size.
  * Stability: `sorted(..., reverse=True)` is still stable (equal keys keep
    input order) -- it is NOT the same as sorting then reversing.
"""
from __future__ import annotations

import heapq
import random
from typing import List, Optional, Tuple

Order = Tuple[str, int, int]   # (order_id, priority, timestamp)


# ----------------------------------------------------------------- Part 1
def _lomuto_partition(a: List[int], lo: int, hi: int) -> int:
    # Random pivot moved to hi.  Invariant during the sweep:
    #   a[lo..i-1] < pivot,  a[i..j-1] >= pivot,  a[j..hi-1] unseen.
    p = random.randint(lo, hi)
    a[p], a[hi] = a[hi], a[p]
    pivot = a[hi]
    i = lo
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i   # pivot's final index


def quicksort_lomuto(a: List[int]) -> List[int]:
    # Recurse on the smaller side, loop on the larger: O(log n) stack even
    # in the O(n^2)-time worst case (all-equal input).
    def sort(lo: int, hi: int) -> None:
        while lo < hi:
            p = _lomuto_partition(a, lo, hi)
            if p - lo < hi - p:
                sort(lo, p - 1)
                lo = p + 1
            else:
                sort(p + 1, hi)
                hi = p - 1

    sort(0, len(a) - 1)
    return a
    # Worst cases: fixed pivot + sorted input -> every split is (0, n-1).
    # Random pivot fixes that in expectation but NOT all-equal input for
    # Lomuto: nothing is `< pivot`, so i stays at lo -> split (0, n-1) again.
    # 3-way partition (lt / eq / gt bands) makes all-equal input O(n).


def _hoare_partition(a: List[int], lo: int, hi: int) -> int:
    # Random pivot moved to lo (required: guarantees lo <= j < hi so both
    # halves shrink).  Returns j with a[lo..j] <= pivot <= a[j+1..hi].
    p = random.randint(lo, hi)
    a[p], a[lo] = a[lo], a[p]
    pivot = a[lo]
    i, j = lo - 1, hi + 1
    while True:
        i += 1
        while a[i] < pivot:
            i += 1
        j -= 1
        while a[j] > pivot:
            j -= 1
        if i >= j:
            return j
        a[i], a[j] = a[j], a[i]
    # Both scans STOP on equal elements and swap them -- that is why all-equal
    # input splits evenly under Hoare (unlike Lomuto).  ~3x fewer swaps.


def quicksort_hoare(a: List[int]) -> List[int]:
    def sort(lo: int, hi: int) -> None:
        while lo < hi:
            j = _hoare_partition(a, lo, hi)
            if j - lo < hi - j - 1:
                sort(lo, j)
                lo = j + 1
            else:
                sort(j + 1, hi)
                hi = j

    sort(0, len(a) - 1)
    return a


# ----------------------------------------------------------------- Part 2
def _merge(left: List[int], right: List[int]) -> List[int]:
    # `<=` keeps left-side elements first on ties -> stable.
    out: List[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def merge_sort_top_down(a: List[int]) -> List[int]:
    if len(a) <= 1:
        return list(a)
    mid = len(a) // 2
    return _merge(merge_sort_top_down(a[:mid]), merge_sort_top_down(a[mid:]))
    # T(n) = 2T(n/2) + O(n) -> O(n log n); O(n) extra + O(log n) stack.


def merge_sort_bottom_up(a: List[int]) -> List[int]:
    # Pass with width w merges adjacent runs of length w.  log2(n) passes.
    src = list(a)
    n = len(src)
    width = 1
    while width < n:
        dst: List[int] = []
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            dst.extend(_merge(src[lo:mid], src[mid:hi]))
        src = dst
        width *= 2
    return src   # no recursion -> no stack-depth worry; natural for linked lists


# ----------------------------------------------------------------- Part 3
def sift_down(a: List[int], i: int, n: int) -> None:
    # Push a[i] down until both children (within a[:n]) are <= it.
    while True:
        left, right = 2 * i + 1, 2 * i + 2
        largest = i
        if left < n and a[left] > a[largest]:
            largest = left
        if right < n and a[right] > a[largest]:
            largest = right
        if largest == i:
            return
        a[i], a[largest] = a[largest], a[i]
        i = largest


def heap_sort(a: List[int]) -> List[int]:
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):   # Floyd build: O(n) total
        sift_down(a, i, n)
    for end in range(n - 1, 0, -1):       # max to the back, heap shrinks
        a[0], a[end] = a[end], a[0]
        sift_down(a, 0, end)
    return a
    # O(n log n) worst case, O(1) extra.  Not stable (long-range swaps).
    # Poor cache behaviour is why quicksort usually beats it in practice.


# ----------------------------------------------------------------- Part 4
def find_kth_largest(nums: List[int], k: int) -> int:
    # k-th largest == element at sorted index n-k.  Partition, then keep only
    # the side that contains the target index.  Expected work
    # n + n/2 + n/4 + ... = O(n).  Copy so the caller's list is untouched.
    a = list(nums)
    target = len(a) - k
    lo, hi = 0, len(a) - 1
    while True:
        p = _lomuto_partition(a, lo, hi)
        if p == target:
            return a[p]
        if p < target:
            lo = p + 1
        else:
            hi = p - 1
    # Alternatives: heap of size k -> O(n log k); sort -> O(n log n).
    # Worst case O(n^2) (all-equal with Lomuto); median-of-medians is O(n).


# ----------------------------------------------------------------- Part 5
def counting_sort(a: List[int]) -> List[int]:
    if not a:
        return []
    lo, hi = min(a), max(a)
    counts = [0] * (hi - lo + 1)
    for x in a:
        counts[x - lo] += 1
    for v in range(1, len(counts)):           # prefix sums: counts[v] =
        counts[v] += counts[v - 1]            #   number of elements <= v+lo
    out = [0] * len(a)
    for x in reversed(a):                     # right-to-left keeps ties stable
        counts[x - lo] -= 1
        out[counts[x - lo]] = x
    return out
    # O(n + range) time / space.  Stability is what lets LSD radix sort chain
    # digit-by-digit passes; for plain ints you could just emit counts.


def bucket_sort(a: List[int], bucket_size: int = 10) -> List[int]:
    if not a:
        return []
    lo, hi = min(a), max(a)
    buckets: List[List[int]] = [[] for _ in range((hi - lo) // bucket_size + 1)]
    for x in a:
        buckets[(x - lo) // bucket_size].append(x)
    out: List[int] = []
    for b in buckets:
        insertion_sort(b)                     # tiny, near-uniform buckets
        out.extend(b)
    return out
    # Expected O(n + k) when values are uniform; O(n^2) if everything lands
    # in one bucket (skewed data) -- use a stronger inner sort then.


# ----------------------------------------------------------------- Part 6
def min_swaps_to_sort(a: List[int]) -> int:
    # pos[i] = where a[i] belongs.  Following i -> pos[i] traces a cycle;
    # a cycle of length L needs exactly L-1 swaps (each swap fixes >= 1).
    n = len(a)
    order = sorted(range(n), key=lambda i: a[i])   # order[k] = index of k-th smallest
    pos = [0] * n
    for k, i in enumerate(order):
        pos[i] = k
    seen = [False] * n
    swaps = 0
    for i in range(n):
        if seen[i] or pos[i] == i:
            continue
        length = 0
        j = i
        while not seen[j]:
            seen[j] = True
            j = pos[j]
            length += 1
        swaps += length - 1
    return swaps   # O(n log n); if values are 1..n, pos[i] = a[i]-1 -> O(n)


# ----------------------------------------------------------------- Part 7
def sort_k_sorted(a: List[int], k: int) -> List[int]:
    # The global minimum must be within the first k+1 elements; keep a
    # min-heap of that window and slide it.  heappushpop = push then pop.
    heap = a[:k + 1]
    heapq.heapify(heap)
    out: List[int] = []
    for x in a[k + 1:]:
        out.append(heapq.heappushpop(heap, x))
    while heap:
        out.append(heapq.heappop(heap))
    return out   # O(n log k) time, O(k) extra


# ----------------------------------------------------------------- Part 8
def sort_orders(orders: List[Order]) -> List[Order]:
    # Composite key: negate the numeric DESC field.  sorted() is Timsort ->
    # stable, so full ties keep input order.  O(n log n).
    return sorted(orders, key=lambda o: (-o[1], o[2]))


def sort_orders_two_pass(orders: List[Order]) -> List[Order]:
    # Sort by the LEAST significant key first, then by the most significant.
    # Stability of the second pass preserves the first pass's order among
    # equal priorities.  reverse=True flips the comparison, not the output,
    # so equal keys still keep their input order (documented guarantee).
    by_ts = sorted(orders, key=lambda o: o[2])
    return sorted(by_ts, key=lambda o: o[1], reverse=True)
    # DESC on a string key: this two-pass trick, or functools.cmp_to_key.
    # Timsort is O(n) on already-sorted / few-run input, so the second pass
    # is cheap when priorities are mostly grouped.


# ----------------------------------------------------------------- Part 9
def insertion_sort(a: List[int], lo: int = 0, hi: Optional[int] = None) -> List[int]:
    # Invariant: a[lo:i] sorted.  Shift larger elements right, drop x in.
    if hi is None:
        hi = len(a)
    for i in range(lo + 1, hi):
        x = a[i]
        j = i - 1
        while j >= lo and a[j] > x:       # `>` (not >=) keeps it stable
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = x
    return a
    # O(n + inversions): O(n) on nearly-sorted data, O(n^2) worst.  Right for
    # n <= ~32, streaming input, or as the base case of quick/merge sort.


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

# INTERVIEWER FOLLOW-UPS
# Q: Quicksort is O(n log n) expected -- what input still makes Lomuto O(n^2)?
# A: All-equal (or few-distinct) input: nothing is strictly less than the pivot,
#    so every split is (0, n-1).  Fix with 3-way partition; Hoare avoids it too.
# Q: Why does quickselect cost O(n) expected but quicksort O(n log n)?
# A: Quickselect recurses into ONE side: n + n/2 + n/4 + ... = 2n.  Quicksort
#    recurses into both sides, doing O(n) work at each of log n levels.
# Q: Which of these sorts are stable, and when do you care?
# A: Merge, insertion, counting (as written), Timsort: stable.  Quick, heap,
#    quickselect: not.  You care whenever records tie on the sort key but a
#    prior order (arrival time, an earlier sort pass) must survive.
# Q: Python's list.sort -- what is it and what is its best case?
# A: Timsort: merge sort over natural runs, insertion-sorted up to minrun
#    (32-64).  O(n) on sorted or reverse-sorted input, O(n log n) worst.
# Q: Sort 10^9 32-bit ints that don't fit in memory?
# A: External merge sort: sort chunks that fit in RAM, write them out, then
#    K-way merge with a heap (Part 7 flavour); or radix sort if range is bounded.
