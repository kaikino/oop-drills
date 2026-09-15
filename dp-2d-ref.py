from __future__ import annotations

"""
2-D dynamic programming — reference solutions.

Part 1 — Unique paths, then with obstacles.
    "A picking robot in an m x n warehouse grid starts top-left and may only
    move right or down. How many distinct routes reach bottom-right?"
    unique_paths(m, n).  Example: m=3, n=7 -> 28.  1 <= m, n <= 100.
    Then some cells hold pallets (grid[i][j] == 1 is blocked):
    unique_paths_with_obstacles(grid).  [[0,0,0],[0,1,0],[0,0,0]] -> 2.
    TikTok OA note: plain recursion is O(2^(m+n)) and TLEs at 100x100; memoise
    or tabulate.  Target O(m*n) time, O(n) space.

Part 2 — Minimum path sum.
    "Each cell costs grid[i][j] seconds to cross; same moves.  Cheapest route?"
    min_path_sum(grid).  [[1,3,1],[1,5,1],[4,2,1]] -> 7.  O(m*n) time, O(n) space.

Part 3 — Longest common subsequence AND longest common substring.
    "Two users' watch histories a and b (strings of item ids).  How long is the
    longest common subsequence?"  lcs_length(a, b), then reconstruct one:
    lcs_string(a, b).  "abcde","ace" -> 3, "ace".
    ByteDance follow-up: contiguous version.  longest_common_substring_length(a, b)
    and longest_common_substring(a, b).  "abcdxyz","xyzabcd" -> 4, "abcd".
    Both O(len(a)*len(b)).  Be ready to explain why the substring transition
    resets to 0 instead of taking a max.

Part 4 — Edit distance.
    "Minimum single-character insert/delete/replace ops to turn a into b"
    (typo-tolerant search).  edit_distance("horse","ros") -> 3.

Part 5 — Longest palindromic subsequence.
    longest_palindromic_subsequence("bbbab") -> 4.  O(n^2).  Mention the
    LCS(s, reverse(s)) equivalence.

Part 6 — Regular expression matching (LC10).
    '.' matches any single char, '*' matches zero or more of the PRECEDING char.
    Whole-string match.  is_match("aab", "c*a*b") -> True.
    is_match("mississippi", "mis*is*p*.") -> False.  O(len(s)*len(p)).

Part 7 — Interleaving string.
    "Was merged log s3 produced by interleaving s1 and s2 preserving each one's
    order?"  is_interleave("aabcc","dbbca","aadbbcbcac") -> True.
    O(len(s1)*len(s2)) time, O(len(s2)) space.

Part 8 — Maximal square.
    "Binary grid of available ad slots; largest all-1 square's AREA."
    maximal_square([[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]) -> 4.

Part 9 — Burst balloons (interval DP, LC312).
    Burst balloon i to earn nums[i-1]*nums[i]*nums[i+1] (out of range = 1);
    neighbours then become adjacent.  Max coins.  max_coins([3,1,5,8]) -> 167.
    O(n^3).  Key idea: choose the LAST balloon burst in an interval.

Part 10 — Weighted interval scheduling.
    "Ad campaigns (start, end, weight); campaigns cannot overlap (end <= next
    start is fine).  Maximise total weight."  max_weight_intervals(intervals).
    [(1,3,5),(2,5,6),(4,6,5),(6,7,4),(5,8,11),(7,9,2)] -> 17.
    Sort by end + DP + bisect: O(n log n).

Part 11 — Distinct subsequences (LC115).
    "How many distinct subsequences of s equal t?"  num_distinct("rabbbit",
    "rabbit") -> 3.  O(len(s)*len(t)) time, O(len(t)) space.
"""

from bisect import bisect_right
from typing import List, Tuple


# ---------------------------------------------------------------- Part 1
def unique_paths(m: int, n: int) -> int:
    # state: dp[j] = ways to reach (current row, j).
    # transition: dp[i][j] = dp[i-1][j] + dp[i][j-1]; base: first row/col = 1.
    # Rolling row: dp[j] already holds "from above"; add dp[j-1] "from left".
    dp = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j - 1]
    return dp[n - 1]
    # Closed form C(m+n-2, m-1).  Naive recursion recomputes subproblems
    # exponentially many times -> TLE; memoisation fixes it, tabulation is cleaner.


def unique_paths_with_obstacles(grid: List[List[int]]) -> int:
    m, n = len(grid), len(grid[0])
    dp = [0] * n
    dp[0] = 0 if grid[0][0] == 1 else 1   # pitfall: blocked start/end -> 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                dp[j] = 0                  # an obstacle kills every path through it
            elif j > 0:
                dp[j] += dp[j - 1]
    return dp[n - 1]


# ---------------------------------------------------------------- Part 2
def min_path_sum(grid: List[List[int]]) -> int:
    # dp[j] = cheapest cost to reach (current row, j); dp[i][j] = g + min(up, left)
    n = len(grid[0])
    dp = [0] * n
    for i, row in enumerate(grid):
        for j, g in enumerate(row):
            if i == 0 and j == 0:
                dp[j] = g
            elif i == 0:
                dp[j] = dp[j - 1] + g
            elif j == 0:
                dp[j] = dp[j] + g
            else:
                dp[j] = min(dp[j], dp[j - 1]) + g
    return dp[n - 1]


# ---------------------------------------------------------------- Part 3
def lcs_length(a: str, b: str) -> int:
    # dp[i][j] = LCS of a[:i], b[:j].  Match: diag+1; else max(up, left).  Base row/col 0.
    n, m = len(a), len(b)
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        cur = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev = cur
    return prev[m]


def lcs_string(a: str, b: str) -> str:
    # Reconstruction needs the full table: walk back from (n, m).
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    out: List[str] = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:   # follow whichever neighbour produced dp[i][j]
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))


def longest_common_substring_length(a: str, b: str) -> int:
    # dp[i][j] = length of the longest common SUFFIX of a[:i], b[:j].
    # Mismatch resets to 0 (contiguity); the answer is the max over all cells.
    m = len(b)
    prev = [0] * (m + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def longest_common_substring(a: str, b: str) -> str:
    m = len(b)
    prev = [0] * (m + 1)
    best, end_i = 0, 0                     # end_i = index in a just past the best substring
    for i in range(1, len(a) + 1):
        cur = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, end_i = cur[j], i
        prev = cur
    return a[end_i - best:end_i]
    # O(n*m); suffix automaton / suffix array give O(n+m) but are overkill here.


# ---------------------------------------------------------------- Part 4
def edit_distance(a: str, b: str) -> int:
    # dp[i][j] = ops to turn a[:i] into b[:j].  Base: dp[i][0]=i, dp[0][j]=j.
    # Match: diag.  Else 1 + min(diag=replace, up=delete from a, left=insert into a).
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1]
            else:
                cur[j] = 1 + min(prev[j - 1], prev[j], cur[j - 1])
        prev = cur
    return prev[m]


# ---------------------------------------------------------------- Part 5
def longest_palindromic_subsequence(s: str) -> int:
    # dp[i][j] = LPS inside s[i..j].  Base dp[i][i] = 1.
    # s[i]==s[j]: 2 + dp[i+1][j-1]; else max(dp[i+1][j], dp[i][j-1]).
    # Fill i descending so dp[i+1][*] is ready.  Equivalent: lcs_length(s, s[::-1]).
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        dp[i][i] = 1
        for j in range(i + 1, n):
            if s[i] == s[j]:
                dp[i][j] = 2 + (dp[i + 1][j - 1] if j - i > 1 else 0)
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# ---------------------------------------------------------------- Part 6
def is_match(s: str, p: str) -> bool:
    # dp[i][j] = s[:i] matches p[:j].  dp[0][0] = True.
    # dp[0][j] = p[j-1]=='*' and dp[0][j-2]   (x* can vanish)
    # p[j-1]=='*': dp[i][j] = dp[i][j-2]                         (zero copies of p[j-2])
    #                        or (p[j-2] matches s[i-1] and dp[i-1][j])  (one more copy)
    # else:        dp[i][j] = p[j-1] matches s[i-1] and dp[i-1][j-1]
    n, m = len(s), len(p)
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for j in range(2, m + 1):
        if p[j - 1] == "*":
            dp[0][j] = dp[0][j - 2]

    def ch_match(i: int, j: int) -> bool:   # s[i-1] vs p[j-1], 1-indexed
        return p[j - 1] == "." or p[j - 1] == s[i - 1]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if p[j - 1] == "*":
                dp[i][j] = dp[i][j - 2] or (ch_match(i, j - 1) and dp[i - 1][j])
            else:
                dp[i][j] = ch_match(i, j) and dp[i - 1][j - 1]
    return dp[n][m]
    # Pitfall: '*' never appears alone at p[0]; it always binds to p[j-2].


# ---------------------------------------------------------------- Part 7
def is_interleave(s1: str, s2: str, s3: str) -> bool:
    # dp[i][j] = s3[:i+j] is an interleaving of s1[:i] and s2[:j].
    # dp[i][j] = (dp[i-1][j] and s1[i-1]==s3[i+j-1]) or (dp[i][j-1] and s2[j-1]==s3[i+j-1])
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False                       # pitfall: length check first
    dp = [False] * (m + 1)
    dp[0] = True
    for j in range(1, m + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, m + 1):
            c = s3[i + j - 1]
            dp[j] = (dp[j] and s1[i - 1] == c) or (dp[j - 1] and s2[j - 1] == c)
    return dp[m]


# ---------------------------------------------------------------- Part 8
def maximal_square(matrix: List[List[int]]) -> int:
    # dp[i][j] = side of the largest all-1 square whose bottom-right corner is (i,j).
    # dp[i][j] = 1 + min(up, left, up-left) if cell is 1, else 0.
    if not matrix or not matrix[0]:
        return 0
    n = len(matrix[0])
    prev = [0] * (n + 1)                   # padded by one on the left/top
    best = 0
    for row in matrix:
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            if row[j - 1] == 1:
                cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])
                best = max(best, cur[j])
        prev = cur
    return best * best


# ---------------------------------------------------------------- Part 9
def max_coins(nums: List[int]) -> int:
    # Pad with 1s.  dp[i][j] = max coins from bursting everything strictly between
    # i and j (open interval), with a[i] and a[j] still standing.
    # Choose k = the LAST balloon burst in (i, j): its neighbours are then exactly i, j:
    #   dp[i][j] = max over k of dp[i][k] + dp[k][j] + a[i]*a[k]*a[j]
    # Fill by increasing interval length.  O(n^3) time, O(n^2) space.
    a = [1] + nums + [1]
    n = len(a)
    dp = [[0] * n for _ in range(n)]
    for length in range(2, n):             # j - i
        for i in range(0, n - length):
            j = i + length
            best = 0
            for k in range(i + 1, j):
                best = max(best, dp[i][k] + dp[k][j] + a[i] * a[k] * a[j])
            dp[i][j] = best
    return dp[0][n - 1]
    # Pitfall: choosing the FIRST balloon to burst does not decompose, because the
    # two sides then interact through the new adjacency.


# ---------------------------------------------------------------- Part 10
def max_weight_intervals(intervals: List[Tuple[int, int, int]]) -> int:
    # Sort by end.  dp[i] = best weight using only the first i intervals.
    # dp[i+1] = max(dp[i], w_i + dp[p]) where p = #intervals with end <= start_i
    # (found by bisect on the sorted end times).  O(n log n).
    iv = sorted(intervals, key=lambda t: t[1])
    ends = [e for _, e, _ in iv]
    dp = [0] * (len(iv) + 1)
    for i, (s, e, w) in enumerate(iv):
        p = bisect_right(ends, s, 0, i)    # last compatible interval index + 1
        dp[i + 1] = max(dp[i], dp[p] + w)
    return dp[len(iv)]
    # Unweighted version is plain greedy by end time; weights break the greedy.


# ---------------------------------------------------------------- Part 11
def num_distinct(s: str, t: str) -> int:
    # dp[j] = number of ways t[:j] appears as a subsequence of the prefix of s seen so far.
    # For each char of s, for j descending: if s_i == t[j-1]: dp[j] += dp[j-1].
    # Descending so dp[j-1] is still the value before this char (each char used once).
    # Base dp[0] = 1 (empty t matches once).
    m = len(t)
    dp = [1] + [0] * m
    for c in s:
        for j in range(m, 0, -1):
            if t[j - 1] == c:
                dp[j] += dp[j - 1]
    return dp[m]


if __name__ == "__main__":
    def is_subseq(sub: str, full: str) -> bool:
        it = iter(full)
        return all(ch in it for ch in sub)

    # Part 1
    assert unique_paths(3, 7) == 28 and unique_paths(3, 2) == 3 and unique_paths(1, 1) == 1
    assert unique_paths(10, 10) == 48620
    assert unique_paths_with_obstacles([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == 2
    assert unique_paths_with_obstacles([[0, 1], [0, 0]]) == 1
    assert unique_paths_with_obstacles([[1]]) == 0 and unique_paths_with_obstacles([[0]]) == 1
    assert unique_paths_with_obstacles([[0, 0], [1, 1], [0, 0]]) == 0
    # Part 2
    assert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    assert min_path_sum([[1, 2, 3], [4, 5, 6]]) == 12 and min_path_sum([[5]]) == 5
    # Part 3
    assert lcs_length("abcde", "ace") == 3 and lcs_length("abc", "def") == 0
    assert lcs_length("AGGTAB", "GXTXAYB") == 4 and lcs_length("", "abc") == 0
    assert lcs_string("abcde", "ace") == "ace" and lcs_string("abc", "def") == ""
    r = lcs_string("AGGTAB", "GXTXAYB")
    assert len(r) == 4 and is_subseq(r, "AGGTAB") and is_subseq(r, "GXTXAYB")
    assert longest_common_substring_length("abcdxyz", "xyzabcd") == 4
    assert longest_common_substring_length("abc", "def") == 0
    assert longest_common_substring_length("GeeksforGeeks", "GeeksQuiz") == 5
    assert longest_common_substring("abcdxyz", "xyzabcd") == "abcd"
    assert longest_common_substring("GeeksforGeeks", "GeeksQuiz") == "Geeks"
    assert longest_common_substring("abc", "def") == ""
    # Part 4
    assert edit_distance("horse", "ros") == 3 and edit_distance("intention", "execution") == 5
    assert edit_distance("", "abc") == 3 and edit_distance("same", "same") == 0
    # Part 5
    assert longest_palindromic_subsequence("bbbab") == 4
    assert longest_palindromic_subsequence("cbbd") == 2
    assert longest_palindromic_subsequence("a") == 1 and longest_palindromic_subsequence("") == 0
    # Part 6
    assert is_match("aa", "a") is False and is_match("aa", "a*") is True
    assert is_match("ab", ".*") is True and is_match("aab", "c*a*b") is True
    assert is_match("mississippi", "mis*is*p*.") is False
    assert is_match("", ".*") is True and is_match("", "a") is False
    assert is_match("ab", ".*c") is False and is_match("aaa", "a*a") is True
    # Part 7
    assert is_interleave("aabcc", "dbbca", "aadbbcbcac") is True
    assert is_interleave("aabcc", "dbbca", "aadbbbaccc") is False
    assert is_interleave("", "", "") is True and is_interleave("", "", "a") is False
    assert is_interleave("a", "", "a") is True
    # Part 8
    assert maximal_square([[1, 0, 1, 0, 0], [1, 0, 1, 1, 1], [1, 1, 1, 1, 1], [1, 0, 0, 1, 0]]) == 4
    assert maximal_square([[0, 1], [1, 0]]) == 1 and maximal_square([[0]]) == 0
    assert maximal_square([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) == 9
    # Part 9
    assert max_coins([3, 1, 5, 8]) == 167 and max_coins([1, 5]) == 10 and max_coins([]) == 0
    assert max_coins([7]) == 7
    # Part 10
    assert max_weight_intervals([(1, 3, 5), (2, 5, 6), (4, 6, 5), (6, 7, 4), (5, 8, 11), (7, 9, 2)]) == 17
    assert max_weight_intervals([(1, 2, 10), (2, 3, 10), (1, 3, 15)]) == 20
    assert max_weight_intervals([(1, 4, 3), (2, 6, 5), (5, 7, 3)]) == 6
    assert max_weight_intervals([]) == 0
    # Part 11
    assert num_distinct("rabbbit", "rabbit") == 3 and num_distinct("babgbag", "bag") == 5
    assert num_distinct("abc", "") == 1 and num_distinct("", "a") == 0
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: unique_paths with the closed form C(m+n-2, m-1) -- when would you NOT use it?
# A: As soon as obstacles or per-cell costs appear the combinatorial shortcut dies; the
#    DP generalises, the formula does not.
# Q: LCS vs longest common substring: what is the one-line difference in the transition?
# A: On a mismatch LCS takes max(up, left); the substring DP resets to 0 because the
#    common run must be contiguous, and the answer is the max cell rather than the corner.
# Q: How do you cut edit_distance to O(min(n, m)) space and still reconstruct the ops?
# A: Two rows give the distance only; reconstruction needs the full table or
#    Hirschberg's divide-and-conquer (O(nm) time, O(n+m) space).
# Q: Why does burst balloons pick the LAST balloon in an interval rather than the first?
# A: With the last balloon k fixed, its neighbours at burst time are exactly the interval
#    ends i and j, so the two sides are independent subproblems.
# Q: Weighted interval scheduling with 1e5 intervals and end times up to 1e18?
# A: Sorting plus bisect on the end array is O(n log n) and never touches the time range,
#    so it is unaffected; a time-indexed dp array would not be.
