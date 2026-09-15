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
    # Invariant: s[left..right] has no repeats. `last[ch]` = last index of ch.
    # Pitfall: only jump `left` FORWARD (last[ch] >= left), otherwise "abba"
    # would move left backwards and over-count.
    last: Dict[str, int] = {}
    best = left = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best  # O(n) time, O(alphabet) space


# ---------------------------------------------------------------- Part 2
def min_window(s: str, t: str) -> str:
    # Invariant: `need[c]` = how many more c's the window still needs
    # (may go negative = surplus). `missing` = sum of positive needs.
    # Grow right until missing == 0, then shrink left while still valid.
    if not t or len(t) > len(s):
        return ""
    need: Dict[str, int] = Counter(t)
    missing = len(t)
    left = 0
    best_l, best_r = 0, -1  # inclusive; best_r < 0 means "none yet"
    for right, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        while missing == 0:  # window valid -> record, then shrink
            if best_r < 0 or right - left < best_r - best_l:
                best_l, best_r = left, right
            need[s[left]] += 1
            if need[s[left]] > 0:  # we just removed a required char
                missing += 1
            left += 1
    return s[best_l:best_r + 1] if best_r >= 0 else ""
    # O(|s| + |t|): each index enters and leaves the window once.


# ---------------------------------------------------------------- Part 3
def longest_ones(nums: List[int], k: int) -> int:
    # Invariant: window holds at most k zeros. Never need to re-grow, so
    # the window only ever moves right -> O(n).
    left = zeros = best = 0
    for right, x in enumerate(nums):
        if x == 0:
            zeros += 1
        while zeros > k:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


# ---------------------------------------------------------------- Part 4
def max_subarray_len(nums: List[int], k: int) -> int:
    # prefix[i] - prefix[j] == k  <=>  prefix[j] == prefix[i] - k.
    # Store the FIRST index of each prefix (longest subarray). Seed {0: -1}
    # so a subarray starting at index 0 counts.
    first: Dict[int, int] = {0: -1}
    total = best = 0
    for i, x in enumerate(nums):
        total += x
        if total - k in first:
            best = max(best, i - first[total - k])
        if total not in first:  # keep the earliest occurrence
            first[total] = i
    return best  # O(n) time, O(n) space


# ---------------------------------------------------------------- Part 5
def max_sliding_window(nums: List[int], k: int) -> List[int]:
    # Deque of INDICES whose values are strictly decreasing front->back.
    # Front is the current max. Pop back while <= new value (they can never
    # be a max again), pop front when it falls out of the window.
    dq: Deque[int] = deque()
    out: List[int] = []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:  # index left the window
            dq.popleft()
        if i >= k - 1:  # pitfall: first output only once the window is full
            out.append(nums[dq[0]])
    return out  # O(n): each index pushed/popped at most once


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

# INTERVIEWER FOLLOW-UPS
# Q: In Part 1, why can't you just do `left = last[ch] + 1` unconditionally?
# A: last[ch] may be BEFORE the current left ("abba": second 'a'); moving left
#    backwards re-admits duplicates. Always take max(left, last[ch] + 1).
# Q: Part 2 -- why a `missing` counter instead of comparing two Counters?
# A: Comparing dicts on every step costs O(alphabet); the counter makes each
#    step O(1), giving true O(|s| + |t|).
# Q: Part 4 -- why doesn't the two-pointer trick from Part 3 work here?
# A: Negative numbers break monotonicity: extending the window can DECREASE
#    the sum, so "shrink when too big" is no longer correct. Prefix sums fix it.
# Q: Part 4 -- what if the question were "shortest" instead of "longest"?
# A: Store the LAST index of each prefix (overwrite) instead of the first.
# Q: Part 5 -- why is the deque O(n) although there is a while loop inside?
# A: Amortised: each index is appended once and popped at most once.
