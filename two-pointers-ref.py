"""
TWO POINTERS -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "Sorted or partially-ordered arrays; two indices that move towards or
away from each other. For each one, tell me why moving the pointer you chose
can never skip the answer."

------------------------------------------------------------------------------
Part 1  Two sum on a SORTED array (LC167). Return the 0-based index pair
        (i, j) with i < j and nums[i] + nums[j] == target, or None.
        Example: [2,7,11,15], 9 -> (0, 1)
        Target: O(n) time, O(1) space (no hashmap).

Part 2  3Sum (LC15). All unique triplets summing to 0. Order of triplets and
        within a triplet does not matter (tests sort). No duplicate triplets.
        Example: [-1,0,1,2,-1,-4] -> [[-1,-1,2],[-1,0,1]]
        Constraints: n <= 3000. Target: O(n^2).

Part 3  Container with most water (LC11). `height[i]` are bar heights; pick
        two bars that with the x-axis hold the most water.
        Example: [1,8,6,2,5,4,8,3,7] -> 49
        Target: O(n). Be ready to argue why moving the shorter side is safe.

Part 4  Trapping rain water (LC42) in O(n) time and O(1) extra space
        (two pointers with running left-max / right-max; the two-array
        version is the warm-up).
        Example: [0,1,0,2,1,0,1,3,2,1,2,1] -> 6

Part 5  Sort colors / Dutch national flag (LC75). Array of 0/1/2 (e.g. order
        status: pending/shipped/delivered) -- sort in place, ONE pass, O(1)
        space. No counting sort.
        Example: [2,0,2,1,1,0] -> [0,0,1,1,2,2]

Part 6  Merge sorted array in place (LC88). nums1 has m real elements then n
        slots of padding; nums2 has n elements. Merge INTO nums1, O(m+n),
        O(1) extra space (fill from the back).
        Example: nums1=[1,2,3,0,0,0], m=3, nums2=[2,5,6], n=3
                 -> nums1 == [1,2,2,3,5,6]

Part 7  Remove duplicates from a sorted array so each value appears at most
        k times (LC80 with k=2, generalised). In place, return the new length;
        the first `length` slots must hold the result.
        Example: [1,1,1,2,2,3], k=2 -> 5, prefix [1,1,2,2,3]
        Target: O(n), O(1) space.
------------------------------------------------------------------------------
"""
from __future__ import annotations

from typing import List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def two_sum_sorted(nums: List[int], target: int) -> Optional[Tuple[int, int]]:
    # Invariant: the answer pair (if any) lies within [i, j].
    # If nums[i]+nums[j] < target, nums[i] can pair with nothing in range -> i++.
    i, j = 0, len(nums) - 1
    while i < j:
        s = nums[i] + nums[j]
        if s == target:
            return (i, j)
        if s < target:
            i += 1
        else:
            j -= 1
    return None  # O(n) time, O(1) space


# ---------------------------------------------------------------- Part 2
def three_sum(nums: List[int]) -> List[List[int]]:
    # Sort, fix the smallest element, run Part 1 on the rest.
    # Dedupe: skip equal `nums[i]`, and after a hit skip equal lo/hi values.
    nums = sorted(nums)
    n = len(nums)
    out: List[List[int]] = []
    for i in range(n - 2):
        if nums[i] > 0:  # everything after is larger -> no zero sum possible
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                out.append([nums[i], nums[lo], nums[hi]])
                lo += 1
                hi -= 1
                while lo < hi and nums[lo] == nums[lo - 1]:
                    lo += 1
                while lo < hi and nums[hi] == nums[hi + 1]:
                    hi -= 1
    return out  # O(n^2) time, O(1) extra (ignoring output / sort)


# ---------------------------------------------------------------- Part 3
def max_area(height: List[int]) -> int:
    # Move the SHORTER side inwards: keeping it can only shrink width while
    # the area is already capped by that shorter bar.
    i, j = 0, len(height) - 1
    best = 0
    while i < j:
        best = max(best, min(height[i], height[j]) * (j - i))
        if height[i] < height[j]:
            i += 1
        else:
            j -= 1
    return best  # O(n)


# ---------------------------------------------------------------- Part 4
def trap(height: List[int]) -> int:
    # Water at i = min(maxLeft, maxRight) - h[i]. Process the side whose
    # bar is lower: its bound is its own running max (the other side is
    # guaranteed to have something at least as high).
    l, r = 0, len(height) - 1
    l_max = r_max = 0
    water = 0
    while l < r:
        if height[l] < height[r]:
            l_max = max(l_max, height[l])
            water += l_max - height[l]
            l += 1
        else:
            r_max = max(r_max, height[r])
            water += r_max - height[r]
            r -= 1
    return water  # O(n) time, O(1) space


# ---------------------------------------------------------------- Part 5
def sort_colors(nums: List[int]) -> None:
    # Invariant: [0,lo) are 0s, [lo,mid) are 1s, (hi,n) are 2s, [mid,hi] unknown.
    # Pitfall: after swapping with `hi` do NOT advance mid (the swapped-in
    # value is unknown); after swapping with `lo` you may (it is a 1 or mid==lo).
    lo, mid, hi = 0, 0, len(nums) - 1
    while mid <= hi:
        if nums[mid] == 0:
            nums[lo], nums[mid] = nums[mid], nums[lo]
            lo += 1
            mid += 1
        elif nums[mid] == 2:
            nums[mid], nums[hi] = nums[hi], nums[mid]
            hi -= 1
        else:
            mid += 1


# ---------------------------------------------------------------- Part 6
def merge(nums1: List[int], m: int, nums2: List[int], n: int) -> None:
    # Write from the back so we never overwrite unread nums1 elements.
    # Loop only while nums2 has elements: leftover nums1 is already in place.
    i, j, k = m - 1, n - 1, m + n - 1
    while j >= 0:
        if i >= 0 and nums1[i] > nums2[j]:
            nums1[k] = nums1[i]
            i -= 1
        else:
            nums1[k] = nums2[j]
            j -= 1
        k -= 1


# ---------------------------------------------------------------- Part 7
def remove_duplicates(nums: List[int], k: int = 2) -> int:
    # Write pointer w. Accept x if fewer than k written, or if the element
    # k slots back differs from x (array is sorted, so that means x has
    # appeared < k times so far).
    w = 0
    for x in nums:
        if w < k or nums[w - k] != x:
            nums[w] = x
            w += 1
    return w  # O(n), O(1)


if __name__ == "__main__":
    # Part 1
    assert two_sum_sorted([2, 7, 11, 15], 9) == (0, 1)
    assert two_sum_sorted([2, 3, 4], 6) == (0, 2)
    assert two_sum_sorted([-1, 0], -1) == (0, 1)
    assert two_sum_sorted([1, 2, 3], 7) is None
    assert two_sum_sorted([], 0) is None

    # Part 2
    def _norm(ts: List[List[int]]) -> List[List[int]]:
        return sorted(sorted(t) for t in ts)

    assert _norm(three_sum([-1, 0, 1, 2, -1, -4])) == [[-1, -1, 2], [-1, 0, 1]]
    assert _norm(three_sum([0, 0, 0, 0])) == [[0, 0, 0]]
    assert _norm(three_sum([1, 2, -2, -1])) == []
    assert _norm(three_sum([])) == []
    assert _norm(three_sum([-2, 0, 1, 1, 2])) == [[-2, 0, 2], [-2, 1, 1]]
    assert _norm(three_sum([3, -2, 1, 0])) == []

    # Part 3
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    assert max_area([4, 3, 2, 1, 4]) == 16
    assert max_area([1, 2, 1]) == 2

    # Part 4
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap([4, 2, 0, 3, 2, 5]) == 9
    assert trap([]) == 0
    assert trap([3, 0, 3]) == 3
    assert trap([1, 2, 3]) == 0
    assert trap([5, 4, 1, 2]) == 1

    # Part 5
    a = [2, 0, 2, 1, 1, 0]; sort_colors(a); assert a == [0, 0, 1, 1, 2, 2]
    a = [2, 0, 1]; sort_colors(a); assert a == [0, 1, 2]
    a = [0]; sort_colors(a); assert a == [0]
    a = [2, 2, 2, 0, 0]; sort_colors(a); assert a == [0, 0, 2, 2, 2]
    a = [1, 2, 0, 1, 2, 0, 1]; sort_colors(a); assert a == [0, 0, 1, 1, 1, 2, 2]
    a = []; sort_colors(a); assert a == []

    # Part 6
    a = [1, 2, 3, 0, 0, 0]; merge(a, 3, [2, 5, 6], 3); assert a == [1, 2, 2, 3, 5, 6]
    a = [1]; merge(a, 1, [], 0); assert a == [1]
    a = [0]; merge(a, 0, [1], 1); assert a == [1]
    a = [4, 5, 6, 0, 0, 0]; merge(a, 3, [1, 2, 3], 3); assert a == [1, 2, 3, 4, 5, 6]
    a = [1, 2, 3, 0, 0, 0]; merge(a, 3, [4, 5, 6], 3); assert a == [1, 2, 3, 4, 5, 6]

    # Part 7
    a = [1, 1, 1, 2, 2, 3]; L = remove_duplicates(a); assert (L, a[:L]) == (5, [1, 1, 2, 2, 3])
    a = [0, 0, 1, 1, 1, 1, 2, 3, 3]; L = remove_duplicates(a); assert (L, a[:L]) == (7, [0, 0, 1, 1, 2, 3, 3])
    a = [1, 1, 1, 1]; L = remove_duplicates(a, 1); assert (L, a[:L]) == (1, [1])
    a = [1, 1, 1, 1]; L = remove_duplicates(a, 3); assert (L, a[:L]) == (3, [1, 1, 1])
    a = []; assert remove_duplicates(a) == 0
    a = [1, 2, 3]; L = remove_duplicates(a); assert (L, a[:L]) == (3, [1, 2, 3])

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part 1 -- prove that moving `i` when the sum is too small never skips the answer.
# A: nums[i] + nums[j] < target and j is the largest index still in range, so
#    nums[i] cannot pair with ANY remaining j'. Discarding i is safe.
# Q: Part 2 -- what changes for 4Sum, or for "sum == target" instead of 0?
# A: One more outer loop (O(n^3)); use target-nums[i]-nums[j] in the inner
#    two-pointer, and keep the same dedupe skips at every level.
# Q: Part 3 -- why move the shorter side and not the taller one?
# A: Area is capped by the shorter bar; moving the taller bar can only shrink
#    width with the same (or lower) cap, so it can never improve the answer.
# Q: Part 4 -- what is the difference between the prefix-max arrays and the
#    two-pointer solution?
# A: Same O(n) time; the two-pointer version drops the two O(n) arrays to O(1)
#    because whichever side is lower is bounded by its OWN running max.
# Q: Part 5 -- why must `mid` stay put after swapping with `hi`?
# A: The value that came from `hi` has not been examined yet; it could be a 0
#    or a 2 that needs another swap.
# Q: Part 6 -- why is "while j >= 0" enough and not "while i >= 0 or j >= 0"?
# A: If nums2 is exhausted, the remaining nums1 prefix is already sorted and
#    in place; copying it to itself would be wasted work.
