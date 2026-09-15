"""
BACKTRACKING -- subsets / permutations / combinations / constraint search.

Interviewer:

PART 1 -- Subsets (LC78 / LC90).
  All subsets of distinct `nums`, then of `nums` that may contain duplicates
  (no duplicate subsets in the output). Any order is fine.
    subsets([1,2,3]) -> [[],[1],[2],[3],[1,2],[1,3],[2,3],[1,2,3]]
    subsets_with_dup([1,2,2]) -> [[],[1],[2],[1,2],[2,2],[1,2,2]]
  Target: O(n * 2^n). The dedup trick is "sort, then skip nums[i] == nums[i-1]
  when i > start" -- explain why that condition is exactly right.

PART 2 -- Permutations (LC46 / LC47).
    permute([1,2,3]) -> 6 lists ; permute_unique([1,1,2]) -> [[1,1,2],[1,2,1],[2,1,1]]
  Target: O(n * n!). For unique: sort + skip when nums[i] == nums[i-1] and
  used[i-1] is False (equal values must be picked left-to-right).

PART 3 -- Combination sum I & II (LC39 / LC40).
  I : distinct candidates, unlimited reuse, target > 0.
        combination_sum([2,3,6,7], 7) -> [[2,2,3],[7]]
  II: candidates may repeat, each used at most once, no duplicate combos.
        combination_sum2([10,1,2,7,6,1,5], 8) -> [[1,1,6],[1,2,5],[1,7],[2,6]]
  Sort first so you can `break` (not `continue`) once a candidate exceeds
  the remaining target.

PART 4 -- N-queens (LC51 / LC52, asked at TikTok).
    total_n_queens(4) -> 2 ; solve_n_queens(4) -> [[".Q..","...Q","Q...","..Q."], ["..Q.","Q...","...Q",".Q.."]]
  One queen per row; O(1) conflict checks via sets keyed on col, r-c, r+c.
  Target: count n=8 (92 solutions) well under a second.

PART 5 -- Generate parentheses (LC22).
    generate_parenthesis(3) -> ["((()))","(()())","(())()","()(())","()()()"]
  Prune with the two counters: open < n, close < open.  Output ~ Catalan(n).

PART 6 -- Letter combinations of a phone number (LC17).
    letter_combinations("23") -> ["ad","ae","af","bd","be","bf","cd","ce","cf"]
    letter_combinations("") -> []
  Target: O(4^n * n).

PART 7 -- Palindrome partitioning (LC131).
  Every way to split s into palindromic substrings (order of pieces matters,
  order of the outer list does not).
    partition("aab") -> [["a","a","b"],["aa","b"]]
  Precompute is_pal[i][j] in O(n^2) so each cut check is O(1).

PART 8 -- Word search II (LC212).
  Given an m x n board of letters and a list of words, return every word that
  can be traced through 4-adjacent cells without reusing a cell. Words in the
  output must be unique; any order.
    board = [["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]]
    find_words(board, ["oath","pea","eat","rain"]) -> ["eat","oath"]
  Build a TRIE of the words and walk board + trie together; on a hit clear
  the word in the trie (dedup) and prune dead leaves so later DFS is cheaper.
  Target: O(m * n * 4 * 3^(L-1)) worst case, far better in practice.

PART 9 -- Sudoku solver (LC37).
  `board` is a 9x9 list of lists of "1".."9" or "."; solve it IN PLACE.
  Use row/col/box sets so each candidate check is O(1). Picking the empty
  cell with the fewest candidates (MRV) makes hard puzzles fast.

PART 10 -- Bundle builder (e-commerce).
  A promo lets a customer bundle catalogue items whose prices sum EXACTLY to
  the coupon value `budget`. Each SKU can be used at most once, but several
  SKUs may share a price; two bundles with the same multiset of prices are
  the same bundle and must be listed once. Return bundles as ascending price
  lists, in lexicographic order.
    build_bundles([10,1,2,7,6,1,5], 8) -> [[1,1,6],[1,2,5],[1,7],[2,6]]
  Extension: `max_items` -- the promo card shows at most k items.
    build_bundles([10,1,2,7,6,1,5], 8, max_items=2) -> [[1,7],[2,6]]
  Sort-based pruning: `break` when price > remaining; skip equal siblings.
  Constraints: len(prices) <= 30, prices >= 1, budget >= 1.
"""
from __future__ import annotations

from typing import List, Optional


# ---------------------------------------------------------------- Part 1
def subsets(nums: List[int]) -> List[List[int]]:
    pass


def subsets_with_dup(nums: List[int]) -> List[List[int]]:
    pass


# ---------------------------------------------------------------- Part 2
def permute(nums: List[int]) -> List[List[int]]:
    pass


def permute_unique(nums: List[int]) -> List[List[int]]:
    pass


# ---------------------------------------------------------------- Part 3
def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    pass


def combination_sum2(candidates: List[int], target: int) -> List[List[int]]:
    pass


# ---------------------------------------------------------------- Part 4
def total_n_queens(n: int) -> int:
    pass


def solve_n_queens(n: int) -> List[List[str]]:
    pass


# ---------------------------------------------------------------- Part 5
def generate_parenthesis(n: int) -> List[str]:
    pass


# ---------------------------------------------------------------- Part 6
def letter_combinations(digits: str) -> List[str]:
    pass


# ---------------------------------------------------------------- Part 7
def partition(s: str) -> List[List[str]]:
    pass


# ---------------------------------------------------------------- Part 8
def find_words(board: List[List[str]], words: List[str]) -> List[str]:
    pass


# ---------------------------------------------------------------- Part 9
def solve_sudoku(board: List[List[str]]) -> None:
    pass


# ---------------------------------------------------------------- Part 10
def build_bundles(prices: List[int], budget: int, max_items: Optional[int] = None) -> List[List[int]]:
    pass


# ---------------------------------------------------------------- tests
def _canon(groups: List[List[int]]) -> List[List[int]]:
    return sorted(sorted(g) for g in groups)


def _sudoku_ok(board: List[List[str]], puzzle: List[List[str]]) -> bool:
    full = set("123456789")
    for i in range(9):
        if set(board[i]) != full or set(board[r][i] for r in range(9)) != full:
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            if set(board[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)) != full:
                return False
    return all(puzzle[r][c] == "." or puzzle[r][c] == board[r][c] for r in range(9) for c in range(9))


if __name__ == "__main__":
    # Part 1
    assert _canon(subsets([1, 2, 3])) == _canon([[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]])
    assert subsets([]) == [[]]
    assert len(subsets(list(range(10)))) == 1024
    assert _canon(subsets_with_dup([1, 2, 2])) == _canon([[], [1], [2], [1, 2], [2, 2], [1, 2, 2]])
    assert _canon(subsets_with_dup([0])) == [[], [0]]
    assert len(subsets_with_dup([1, 1, 1, 1])) == 5
    assert len(subsets_with_dup([4, 4, 4, 1, 4])) == 10

    # Part 2
    assert sorted(permute([1, 2, 3])) == [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    assert permute([1]) == [[1]]
    assert len(permute(list(range(6)))) == 720
    assert sorted(permute_unique([1, 1, 2])) == [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
    assert len(permute_unique([1, 1, 1, 2, 2])) == 10
    assert sorted(permute_unique([1, 2, 3])) == sorted(permute([1, 2, 3]))
    assert permute_unique([7, 7, 7]) == [[7, 7, 7]]

    # Part 3
    assert _canon(combination_sum([2, 3, 6, 7], 7)) == [[2, 2, 3], [7]]
    assert _canon(combination_sum([2, 3, 5], 8)) == [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    assert combination_sum([2], 1) == []
    assert _canon(combination_sum2([10, 1, 2, 7, 6, 1, 5], 8)) == [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]
    assert _canon(combination_sum2([2, 5, 2, 1, 2], 5)) == [[1, 2, 2], [5]]
    assert combination_sum2([1], 2) == []

    # Part 4
    assert [total_n_queens(n) for n in range(1, 9)] == [1, 0, 0, 2, 10, 4, 40, 92]
    assert sorted(solve_n_queens(4)) == [["..Q.", "Q...", "...Q", ".Q.."], [".Q..", "...Q", "Q...", "..Q."]]
    assert solve_n_queens(1) == [["Q"]]
    assert solve_n_queens(3) == []
    assert len(solve_n_queens(6)) == 4
    for b in solve_n_queens(5):
        assert len(b) == 5 and all(row.count("Q") == 1 and len(row) == 5 for row in b)

    # Part 5
    assert sorted(generate_parenthesis(3)) == ["((()))", "(()())", "(())()", "()(())", "()()()"]
    assert generate_parenthesis(1) == ["()"]
    assert len(generate_parenthesis(5)) == 42
    assert len(set(generate_parenthesis(6))) == 132

    # Part 6
    assert sorted(letter_combinations("23")) == ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]
    assert letter_combinations("") == []
    assert sorted(letter_combinations("2")) == ["a", "b", "c"]
    assert len(letter_combinations("79")) == 16

    # Part 7
    assert sorted(partition("aab")) == [["a", "a", "b"], ["aa", "b"]]
    assert partition("a") == [["a"]]
    assert sorted(partition("aba")) == [["a", "b", "a"], ["aba"]]
    assert len(partition("aaaa")) == 8
    assert partition("abc") == [["a", "b", "c"]]

    # Part 8
    board = [["o", "a", "a", "n"], ["e", "t", "a", "e"], ["i", "h", "k", "r"], ["i", "f", "l", "v"]]
    snapshot = [row[:] for row in board]
    assert sorted(find_words(board, ["oath", "pea", "eat", "rain"])) == ["eat", "oath"]
    assert board == snapshot  # board restored
    assert find_words([["a", "b"], ["c", "d"]], ["abcb"]) == []
    assert sorted(find_words([["a", "b"], ["c", "d"]], ["ab", "cd", "ac", "bd", "abcd", "abdc"])) == \
        ["ab", "abdc", "ac", "bd", "cd"]
    assert find_words([["a"]], ["a", "a"]) == ["a"]  # no duplicate output
    assert find_words([["a", "a"]], ["aaa"]) == []  # cells cannot be reused
    assert sorted(find_words([["a", "b"], ["a", "a"]], ["aba", "baa", "bab", "aaab"])) == ["aaab", "aba", "baa"]

    # Part 9
    puzzle = [
        ["5", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ]
    solution = ["534678912", "672195348", "198342567", "859761423", "426853791",
                "713924856", "961537284", "287419635", "345286179"]
    sb = [row[:] for row in puzzle]
    solve_sudoku(sb)
    assert ["".join(r) for r in sb] == solution
    assert _sudoku_ok(sb, puzzle)
    empty = [["."] * 9 for _ in range(9)]
    eb = [row[:] for row in empty]
    solve_sudoku(eb)
    assert _sudoku_ok(eb, empty)

    # Part 10
    assert build_bundles([10, 1, 2, 7, 6, 1, 5], 8) == [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]
    assert build_bundles([10, 1, 2, 7, 6, 1, 5], 8, max_items=2) == [[1, 7], [2, 6]]
    assert build_bundles([10, 1, 2, 7, 6, 1, 5], 8, max_items=1) == []
    assert build_bundles([2, 4, 6], 5) == []
    assert build_bundles([5, 5, 5], 10) == [[5, 5]]
    assert build_bundles([3, 3, 3, 4], 7) == [[3, 4]]
    assert build_bundles([1] * 30, 10) == [[1] * 10]  # dedup makes this instant, not C(30,10)
    assert build_bundles([4, 2, 2, 4], 8) == [[2, 2, 4], [4, 4]]
    print("ok")
