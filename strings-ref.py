"""
STRINGS -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "Short, well-known string problems; I care about edge cases (empty,
length 1, all-identical) and about doing the in-place ones genuinely in
place. Say the spec back to me before you code."

------------------------------------------------------------------------------
Part 1  Reverse words in place (LC186). `s` is a LIST of chars holding
        words separated by single spaces, no leading/trailing spaces.
        Reverse the word order in place, O(1) extra space.
        Example: list("the sky is blue") -> list("blue is sky the")
        Target: O(n) time (reverse all, then reverse each word).

Part 2  Repeated substring pattern (LC459). Can `s` be written as some
        substring repeated 2+ times? Two solutions expected:
        (a) the doubled-string trick, (b) the KMP failure function -- also
        implement `kmp_failure(s)` itself (fail[i] = length of the longest
        proper prefix of s[:i+1] that is also its suffix).
        Example: "abab" -> True;  "aba" -> False;  "abcabcabcabc" -> True
                 kmp_failure("aabaaab") -> [0,1,0,1,2,2,3]
        Constraints: 1 <= len(s) <= 1e4.  Target: O(n) for (b).

Part 3  Group anagrams (LC49). Lowercase words; group them. Order of the
        groups and within a group does not matter (tests sort).
        Example: ["eat","tea","tan","ate","nat","bat"]
                 -> [["ate","eat","tea"],["bat"],["nat","tan"]]
        Target: O(N*K) with a 26-count key (O(N K log K) with sorted key is
        the warm-up).

Part 4  String compression (LC443). `chars` is a list; replace each run of
        a char with the char followed by the run length IF the length > 1.
        Write the result into the front of `chars`, return the new length.
        O(1) extra space; counts >= 10 take several slots.
        Example: ["a","a","b","b","c","c","c"] -> 6, prefix "a2b2c3"
                 ["a"] + ["b"]*12 -> 4, prefix "ab12"

Part 5  Longest palindromic substring (LC5). Return any longest one.
        Example: "babad" -> "bab" or "aba";  "cbbd" -> "bb"
        Constraints: 0 <= len(s) <= 1000.
        Target: O(n^2) time, O(1) space (expand around 2n-1 centres).

Part 6  Restore IP addresses (LC93), generalised -- ByteDance Sept 2026.
        Split digit string `s` into exactly k segments (default 4), each an
        integer 0..255 with no leading zeros ("0" itself is fine). Return
        all valid dotted strings, any order (tests sort).
        Example: "25525511135" -> ["255.255.11.135","255.255.111.35"]
                 "0000" -> ["0.0.0.0"];  "1111", k=2 -> ["1.111","11.11","111.1"]
        Constraints: 1 <= k <= 20, len(s) <= 3k.
        Target: backtracking with pruning (remaining length must be within
        [remaining_segments, 3*remaining_segments]).

Part 7  Valid palindrome II (LC680). Can `s` become a palindrome by
        deleting at most ONE character?
        Example: "abca" -> True;  "abc" -> False
        Target: O(n).

Part 8  Longest common prefix (LC14).
        Example: ["flower","flow","flight"] -> "fl";  ["dog","racecar","car"] -> ""
        Target: O(total chars).

Part 9  Reverse letters in pairs -- TikTok OA, Sept 2026. Spec:
        Consider only the LETTERS of `s` (ch.isalpha()), in order. Swap the
        1st with the 2nd, the 3rd with the 4th, and so on; if the letter
        count is odd the last letter stays. Non-letters keep their exact
        positions. Return the new string.
        Example: "abcd" -> "badc";  "a-bcd" -> "b-adc";  "ab1cde" -> "ba1dce"
                 "hello world" -> "ehllw orodl"
        Target: O(n).
------------------------------------------------------------------------------
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple


# ---------------------------------------------------------------- Part 1
def reverse_words(chars: List[str]) -> None:
    # Reverse the whole array, then reverse each word back. Both steps are
    # in place. Pitfall: remember to flush the LAST word (no trailing space).
    def rev(i: int, j: int) -> None:
        while i < j:
            chars[i], chars[j] = chars[j], chars[i]
            i += 1
            j -= 1

    n = len(chars)
    rev(0, n - 1)
    start = 0
    for i in range(n + 1):
        if i == n or chars[i] == " ":
            rev(start, i - 1)
            start = i + 1
    # O(n) time, O(1) space


# ---------------------------------------------------------------- Part 2
def repeated_substring_pattern(s: str) -> bool:
    # If s = p*k (k >= 2), then s appears in (s+s) at offset len(p), which is
    # strictly inside. Cutting the first and last char removes the two
    # trivial matches at offsets 0 and n.
    return len(s) > 1 and s in (s + s)[1:-1]  # O(n) with a linear find


def kmp_failure(s: str) -> List[int]:
    # fail[i] = length of the longest proper prefix of s[:i+1] that is also
    # a suffix. `k` = current candidate length; on mismatch fall back to
    # fail[k-1] (the next-longest border), never restart from 0 blindly.
    fail = [0] * len(s)
    k = 0
    for i in range(1, len(s)):
        while k and s[i] != s[k]:
            k = fail[k - 1]
        if s[i] == s[k]:
            k += 1
        fail[i] = k
    return fail  # O(n) amortised


def repeated_substring_kmp(s: str) -> bool:
    # Smallest period p = n - fail[n-1]. s is periodic with a whole number of
    # repeats iff fail[n-1] > 0 and p divides n.
    n = len(s)
    if n < 2:
        return False
    border = kmp_failure(s)[-1]
    return border > 0 and n % (n - border) == 0


# ---------------------------------------------------------------- Part 3
def group_anagrams(strs: List[str]) -> List[List[str]]:
    # Key = tuple of 26 letter counts (hashable). Sorted-string key also
    # works but costs O(K log K) per word.
    groups: Dict[Tuple[int, ...], List[str]] = defaultdict(list)
    for w in strs:
        counts = [0] * 26
        for ch in w:
            counts[ord(ch) - 97] += 1
        groups[tuple(counts)].append(w)
    return list(groups.values())  # O(N*K)


# ---------------------------------------------------------------- Part 4
def compress(chars: List[str]) -> int:
    # Read pointer i scans runs, write pointer w writes. Safe because
    # w <= i always: a run of length L >= 2 writes 1 + len(str(L)) <= L slots.
    n = len(chars)
    w = i = 0
    while i < n:
        ch = chars[i]
        j = i
        while j < n and chars[j] == ch:
            j += 1
        chars[w] = ch
        w += 1
        if j - i > 1:
            for d in str(j - i):
                chars[w] = d
                w += 1
        i = j
    return w  # O(n) time, O(1) space


# ---------------------------------------------------------------- Part 5
def longest_palindrome(s: str) -> str:
    # Every palindrome has a centre: a char (odd length) or a gap between
    # two chars (even length). Expand from each of the 2n-1 centres.
    n = len(s)
    if n == 0:
        return ""

    def expand(l: int, r: int) -> Tuple[int, int]:
        while l >= 0 and r < n and s[l] == s[r]:
            l -= 1
            r += 1
        return l + 1, r - 1  # inclusive bounds of the palindrome

    best_l = best_r = 0
    for i in range(n):
        for l, r in (expand(i, i), expand(i, i + 1)):
            if r - l > best_r - best_l:
                best_l, best_r = l, r
    return s[best_l:best_r + 1]  # O(n^2) time, O(1) space


# ---------------------------------------------------------------- Part 6
def restore_ip(s: str, k: int = 4) -> List[str]:
    # Backtrack over segment lengths 1..3. Prune by remaining length. Stop a
    # branch as soon as a segment has a leading zero or exceeds 255 -- any
    # longer segment from the same start is invalid too.
    n = len(s)
    out: List[str] = []

    def rec(i: int, parts: List[str]) -> None:
        remaining = k - len(parts)
        if remaining == 0:
            if i == n:
                out.append(".".join(parts))
            return
        if not (remaining <= n - i <= 3 * remaining):
            return
        for length in (1, 2, 3):
            if i + length > n:
                break
            seg = s[i:i + length]
            if (length > 1 and seg[0] == "0") or int(seg) > 255:
                break
            parts.append(seg)
            rec(i + length, parts)
            parts.pop()

    rec(0, [])
    return out  # O(3^k * n) worst case; tiny in practice thanks to pruning


# ---------------------------------------------------------------- Part 7
def valid_palindrome_ii(s: str) -> bool:
    # Two pointers; on the FIRST mismatch try skipping either side, and that
    # remaining check must be an exact palindrome (only one deletion).
    def is_pal(l: int, r: int) -> bool:
        while l < r:
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True

    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return is_pal(l + 1, r) or is_pal(l, r - 1)
        l += 1
        r -= 1
    return True  # O(n)


# ---------------------------------------------------------------- Part 8
def longest_common_prefix(strs: List[str]) -> str:
    # Vertical scan: compare column i across all words; stop at the first
    # column that disagrees or when the shortest word runs out.
    if not strs:
        return ""
    shortest = min(strs, key=len)
    for i, ch in enumerate(shortest):
        for w in strs:
            if w[i] != ch:
                return shortest[:i]
    return shortest  # O(total chars)


# ---------------------------------------------------------------- Part 9
def swap_letter_pairs(s: str) -> str:
    # Collect the positions of letters, then swap positions pairwise. Strings
    # are immutable, so work on a list. Non-letters are never touched.
    chars = list(s)
    pos = [i for i, ch in enumerate(chars) if ch.isalpha()]
    for a in range(0, len(pos) - 1, 2):
        i, j = pos[a], pos[a + 1]
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)  # O(n)


if __name__ == "__main__":
    # Part 1
    a = list("the sky is blue"); reverse_words(a); assert a == list("blue is sky the")
    a = list("a"); reverse_words(a); assert a == list("a")
    a = list("hello world"); reverse_words(a); assert a == list("world hello")
    a = []; reverse_words(a); assert a == []
    a = list("ab cd ef"); reverse_words(a); assert a == list("ef cd ab")

    # Part 2
    for f in (repeated_substring_pattern, repeated_substring_kmp):
        assert f("abab") is True
        assert f("aba") is False
        assert f("abcabcabcabc") is True
        assert f("a") is False
        assert f("aa") is True
        assert f("abac") is False
        assert f("aaaaab") is False
        assert f("abaababaab") is True
    assert kmp_failure("aabaaab") == [0, 1, 0, 1, 2, 2, 3]
    assert kmp_failure("abcabc") == [0, 0, 0, 1, 2, 3]
    assert kmp_failure("aaaa") == [0, 1, 2, 3]
    assert kmp_failure("abcd") == [0, 0, 0, 0]
    assert kmp_failure("") == []

    # Part 3
    def _norm(groups: List[List[str]]) -> List[List[str]]:
        return sorted(sorted(g) for g in groups)

    assert _norm(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    assert _norm(group_anagrams([""])) == [[""]]
    assert _norm(group_anagrams(["a"])) == [["a"]]
    assert _norm(group_anagrams(["ab", "ba", "abc"])) == [["ab", "ba"], ["abc"]]
    assert _norm(group_anagrams([])) == []

    # Part 4
    a = ["a", "a", "b", "b", "c", "c", "c"]; L = compress(a); assert (L, a[:L]) == (6, list("a2b2c3"))
    a = ["a"]; L = compress(a); assert (L, a[:L]) == (1, ["a"])
    a = ["a"] + ["b"] * 12; L = compress(a); assert (L, a[:L]) == (4, list("ab12"))
    a = ["a", "a", "a", "b", "b", "a", "a"]; L = compress(a); assert (L, a[:L]) == (6, list("a3b2a2"))
    a = []; assert compress(a) == 0
    a = ["a", "b", "c"]; L = compress(a); assert (L, a[:L]) == (3, list("abc"))
    a = ["a"] * 100; L = compress(a); assert (L, a[:L]) == (4, list("a100"))

    # Part 5
    assert longest_palindrome("babad") in ("bab", "aba")
    assert longest_palindrome("cbbd") == "bb"
    assert longest_palindrome("a") == "a"
    assert longest_palindrome("") == ""
    assert longest_palindrome("ac") in ("a", "c")
    assert longest_palindrome("forgeeksskeegfor") == "geeksskeeg"
    assert longest_palindrome("abacdfgdcaba") == "aba"
    assert longest_palindrome("aaaa") == "aaaa"

    # Part 6
    assert sorted(restore_ip("25525511135")) == ["255.255.11.135", "255.255.111.35"]
    assert sorted(restore_ip("0000")) == ["0.0.0.0"]
    assert sorted(restore_ip("101023")) == ["1.0.10.23", "1.0.102.3", "10.1.0.23", "10.10.2.3", "101.0.2.3"]
    assert sorted(restore_ip("1111", 2)) == ["1.111", "11.11", "111.1"]
    assert sorted(restore_ip("2552", 2)) == ["25.52", "255.2"]
    assert restore_ip("255", 1) == ["255"]
    assert restore_ip("256", 1) == []
    assert restore_ip("", 4) == []
    assert restore_ip("1", 4) == []
    assert restore_ip("010010") == ["0.10.0.10", "0.100.1.0"]
    assert sorted(restore_ip("12", 2)) == ["1.2"]

    # Part 7
    assert valid_palindrome_ii("aba") is True
    assert valid_palindrome_ii("abca") is True
    assert valid_palindrome_ii("abc") is False
    assert valid_palindrome_ii("") is True
    assert valid_palindrome_ii("deeee") is True
    assert valid_palindrome_ii("abcdba") is True
    assert valid_palindrome_ii("cbbcc") is True
    assert valid_palindrome_ii("abcdef") is False
    assert valid_palindrome_ii("eedede") is True

    # Part 8
    assert longest_common_prefix(["flower", "flow", "flight"]) == "fl"
    assert longest_common_prefix(["dog", "racecar", "car"]) == ""
    assert longest_common_prefix([]) == ""
    assert longest_common_prefix(["a"]) == "a"
    assert longest_common_prefix(["ab", "ab"]) == "ab"
    assert longest_common_prefix(["", "a"]) == ""
    assert longest_common_prefix(["abc", "ab", "a"]) == "a"

    # Part 9
    assert swap_letter_pairs("abcd") == "badc"
    assert swap_letter_pairs("a-bcd") == "b-adc"
    assert swap_letter_pairs("ab1cde") == "ba1dce"
    assert swap_letter_pairs("hello world") == "ehllw orodl"
    assert swap_letter_pairs("") == ""
    assert swap_letter_pairs("a") == "a"
    assert swap_letter_pairs("1a2b3") == "1b2a3"
    assert swap_letter_pairs("!!!") == "!!!"
    assert swap_letter_pairs("abc") == "bac"
    assert swap_letter_pairs("Ab, Cd!") == "bA, dC!"

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part 1 -- what if there can be multiple spaces or leading/trailing ones?
# A: Add a first pass that compacts spaces in place (write pointer), then
#    apply the same reverse-all / reverse-each-word.
# Q: Part 2 -- why is `s in (s+s)[1:-1]` correct, and what is its cost?
# A: If s has period p < n dividing n, shifting s by p inside s+s gives s;
#    conversely a match at offset 0 < d < n implies period d dividing n. Cost
#    is O(n) only if the substring search is linear (CPython's is, in
#    practice); KMP guarantees it.
# Q: Part 3 -- what if the words were Unicode, not a-z?
# A: Key on tuple(sorted(word)) or a frozenset of Counter items; the 26-slot
#    array no longer applies.
# Q: Part 4 -- why is it safe to write digits while still reading?
# A: The write pointer never passes the start of the run being read: a run
#    of length L >= 2 needs 1 + digits(L) <= L output slots.
# Q: Part 5 -- can you do better than O(n^2)?
# A: Manacher's algorithm is O(n); interviewers rarely expect it, but know
#    that it exists and what the "mirror" idea is.
# Q: Part 6 -- why prune on remaining length, and how many results can there be?
# A: Without pruning you explore 3^k branches regardless of feasibility; with
#    it, dead branches die immediately. The count of valid outputs is small
#    (at most a few dozen for k=4).
# Q: Part 9 -- what if the string is a list of bytes (in place)?
# A: Same algorithm: collect letter indices, swap pairs in place; O(1) extra
#    if you walk with two pointers looking for the next two letters instead
#    of materialising `pos`.
