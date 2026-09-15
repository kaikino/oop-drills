"""
SLIDING WINDOW -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "All of these are 'keep a window [left, right] over an array or string
and maintain some summary of it' problems. Tell me what the window invariant
is before you code, and when you shrink vs. grow."

------------------------------------------------------------------------------
Part 1  Longest substring without repeating characters (LC3).
        Example: "abcabcbb" -> 3 ("abc"),  "pwwkew" -> 3 ("wke"),  "abba" -> 2
        Constraints: 0 <= len(s) <= 1e5, any ASCII.
        Target: O(n) time, O(alphabet) space.

Part 2  Minimum window substring (LC76), flavoured:
        A video transcript `s` and a set of required keyword characters `t`
        (with multiplicity). Return the SHORTEST span of `s` that contains
        every char of `t` at least as many times as it appears in `t`.
        Return "" if none. If several, any shortest one is fine (tests use
        the classic inputs where the answer is unique).
        Example: s="ADOBECODEBANC", t="ABC" -> "BANC"
        Constraints: len(s), len(t) <= 1e5.
        Target: O(|s| + |t|) time.

Part 3  Max consecutive ones III (LC1004).
        `nums` is a 0/1 array of "video delivered on time" flags; you may
        flip at most k zeros to ones. Longest run of ones achievable?
        Example: [1,1,1,0,0,0,1,1,1,1,0], k=2 -> 6
        Target: O(n) time, O(1) space.

Part 4  Maximum size subarray sum equals k (LC325). Values may be NEGATIVE,
        so the window cannot be shrunk greedily -- use prefix sums + a map
        of the FIRST index each prefix was seen.
        Example: [1,-1,5,-2,3], k=3 -> 4 ([1,-1,5,-2]);  [-2,-1,2,1], k=1 -> 2
        Return 0 if no subarray sums to k.
        Target: O(n) time, O(n) space.

Part 5  Sliding window maximum (LC239), flavoured:
        `viewers[i]` = concurrent viewers in minute i of a livestream. For
        every window of k consecutive minutes report the peak.
        Example: [1,3,-1,-3,5,3,6,7], k=3 -> [3,3,5,5,6,7]
        Constraints: 1 <= k <= n <= 1e5.
        Target: O(n) time with a monotonic deque (heap O(n log k) is the
        warm-up answer; the interviewer will push for the deque).
------------------------------------------------------------------------------
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Deque, Dict, List


# ---------------------------------------------------------------- Part 1
def length_of_longest_substring(s: str) -> int:
    pass


# ---------------------------------------------------------------- Part 2
def min_window(s: str, t: str) -> str:
    pass


# ---------------------------------------------------------------- Part 3
def longest_ones(nums: List[int], k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 4
def max_subarray_len(nums: List[int], k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 5
def max_sliding_window(nums: List[int], k: int) -> List[int]:
    pass


if __name__ == "__main__":
    # Part 1
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring("abba") == 2
    assert length_of_longest_substring("dvdf") == 3

    # Part 2
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""
    assert min_window("aa", "aa") == "aa"
    assert min_window("abc", "") == ""
    assert min_window("bba", "ab") == "ba"

    # Part 3
    assert longest_ones([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) == 6
    assert longest_ones([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3) == 10
    assert longest_ones([0, 0, 0], 0) == 0
    assert longest_ones([1, 1, 1], 0) == 3
    assert longest_ones([0, 0, 0], 5) == 3

    # Part 4
    assert max_subarray_len([1, -1, 5, -2, 3], 3) == 4
    assert max_subarray_len([-2, -1, 2, 1], 1) == 2
    assert max_subarray_len([1, 2, 3], 7) == 0
    assert max_subarray_len([0, 0, 0], 0) == 3
    assert max_subarray_len([1, 2, 3], 6) == 3
    assert max_subarray_len([3, -3, 3, -3], 0) == 4

    # Part 5
    assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert max_sliding_window([1], 1) == [1]
    assert max_sliding_window([9, 8, 7], 2) == [9, 8]
    assert max_sliding_window([1, 2, 3], 3) == [3]
    assert max_sliding_window([4, 4, 4, 1], 2) == [4, 4, 4]

    print("ok")
