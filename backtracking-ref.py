"""Reference solutions for backtracking.py -- see that file for the problem statements."""
from __future__ import annotations

from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------- Part 1
def subsets(nums: List[int]) -> List[List[int]]:
    # Invariant: `path` is a subset of nums[:start] chosen so far; every call
    # emits it, then extends with each nums[i], i >= start, so each subset is
    # produced exactly once (elements are taken in index order). O(n * 2^n).
    res: List[List[int]] = []
    path: List[int] = []

    def bt(start: int) -> None:
        res.append(path[:])  # copy! path is mutated afterwards
        for i in range(start, len(nums)):
            path.append(nums[i])
            bt(i + 1)
            path.pop()

    bt(0)
    return res


def subsets_with_dup(nums: List[int]) -> List[List[int]]:
    # Sort so equal values are adjacent. At one recursion level, among a run
    # of equal values only the FIRST may start a new branch: `i > start and
    # nums[i] == nums[i-1]` means "same value as a sibling branch already
    # explored at this level" -> skip. (Compare with i-1 == start-1 being the
    # parent's pick, which is allowed: that is how [2,2] gets generated.)
    nums = sorted(nums)
    res: List[List[int]] = []
    path: List[int] = []

    def bt(start: int) -> None:
        res.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue
            path.append(nums[i])
            bt(i + 1)
            path.pop()

    bt(0)
    return res


# ---------------------------------------------------------------- Part 2
def permute(nums: List[int]) -> List[List[int]]:
    # used[] marks which indices are on the path. O(n * n!) output-bound.
    res: List[List[int]] = []
    path: List[int] = []
    used = [False] * len(nums)

    def bt() -> None:
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            bt()
            path.pop()
            used[i] = False

    bt()
    return res


def permute_unique(nums: List[int]) -> List[List[int]]:
    # Sort, and force equal values to be consumed left-to-right: if nums[i]
    # equals nums[i-1] and nums[i-1] is NOT currently used, then picking
    # nums[i] now would produce the same permutation as picking nums[i-1]
    # first -- skip. Pitfall: writing `used[i-1]` (used) instead of `not
    # used[i-1]` still dedups but prunes far less.
    nums = sorted(nums)
    res: List[List[int]] = []
    path: List[int] = []
    used = [False] * len(nums)

    def bt() -> None:
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i in range(len(nums)):
            if used[i] or (i > 0 and nums[i] == nums[i - 1] and not used[i - 1]):
                continue
            used[i] = True
            path.append(nums[i])
            bt()
            path.pop()
            used[i] = False

    bt()
    return res


# ---------------------------------------------------------------- Part 3
def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    # Unlimited reuse => recurse with the SAME index i (not i+1). Sorting lets
    # us break as soon as a candidate exceeds the remaining target.
    candidates = sorted(candidates)
    res: List[List[int]] = []
    path: List[int] = []

    def bt(start: int, remaining: int) -> None:
        if remaining == 0:
            res.append(path[:])
            return
        for i in range(start, len(candidates)):
            c = candidates[i]
            if c > remaining:
                break
            path.append(c)
            bt(i, remaining - c)
            path.pop()

    bt(0, target)
    return res


def combination_sum2(candidates: List[int], target: int) -> List[List[int]]:
    # Each element once => recurse with i+1; duplicates in input => the same
    # sibling-skip as subsets_with_dup.
    candidates = sorted(candidates)
    res: List[List[int]] = []
    path: List[int] = []

    def bt(start: int, remaining: int) -> None:
        if remaining == 0:
            res.append(path[:])
            return
        for i in range(start, len(candidates)):
            c = candidates[i]
            if c > remaining:
                break
            if i > start and c == candidates[i - 1]:
                continue
            path.append(c)
            bt(i + 1, remaining - c)
            path.pop()

    bt(0, target)
    return res


# ---------------------------------------------------------------- Part 4
def total_n_queens(n: int) -> int:
    # Place one queen per row. A square (r, c) is attacked iff its column,
    # its "\" diagonal (r - c constant) or its "/" diagonal (r + c constant)
    # already holds a queen -- three sets give O(1) checks. Rows are implicit.
    cols: Set[int] = set()
    diag: Set[int] = set()
    anti: Set[int] = set()

    def bt(r: int) -> int:
        if r == n:
            return 1
        total = 0
        for c in range(n):
            if c in cols or (r - c) in diag or (r + c) in anti:
                continue
            cols.add(c)
            diag.add(r - c)
            anti.add(r + c)
            total += bt(r + 1)
            cols.remove(c)
            diag.remove(r - c)
            anti.remove(r + c)
        return total

    return bt(0)


def solve_n_queens(n: int) -> List[List[str]]:
    # Same search, but record the column chosen per row and render at leaves.
    res: List[List[str]] = []
    queens: List[int] = []  # queens[r] = column of the queen in row r
    cols: Set[int] = set()
    diag: Set[int] = set()
    anti: Set[int] = set()

    def bt(r: int) -> None:
        if r == n:
            res.append(["." * c + "Q" + "." * (n - c - 1) for c in queens])
            return
        for c in range(n):
            if c in cols or (r - c) in diag or (r + c) in anti:
                continue
            cols.add(c)
            diag.add(r - c)
            anti.add(r + c)
            queens.append(c)
            bt(r + 1)
            queens.pop()
            cols.remove(c)
            diag.remove(r - c)
            anti.remove(r + c)

    bt(0)
    return res


# ---------------------------------------------------------------- Part 5
def generate_parenthesis(n: int) -> List[str]:
    # A prefix is extendable to a valid string iff open <= n and close <= open.
    # Every leaf reached is valid, so no validation is needed at the end.
    # Output size is Catalan(n) ~ 4^n / n^1.5.
    res: List[str] = []
    buf: List[str] = []

    def bt(open_: int, close: int) -> None:
        if len(buf) == 2 * n:
            res.append("".join(buf))
            return
        if open_ < n:
            buf.append("(")
            bt(open_ + 1, close)
            buf.pop()
        if close < open_:
            buf.append(")")
            bt(open_, close + 1)
            buf.pop()

    bt(0, 0)
    return res


# ---------------------------------------------------------------- Part 6
_PHONE = {
    "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
    "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
}


def letter_combinations(digits: str) -> List[str]:
    # Pitfall: "" must return [] not [""] -- the empty product has one element.
    if not digits:
        return []
    res: List[str] = []
    buf: List[str] = []

    def bt(i: int) -> None:
        if i == len(digits):
            res.append("".join(buf))
            return
        for ch in _PHONE[digits[i]]:
            buf.append(ch)
            bt(i + 1)
            buf.pop()

    bt(0)
    return res


# ---------------------------------------------------------------- Part 7
def partition(s: str) -> List[List[str]]:
    # is_pal[i][j] = s[i..j] palindrome, filled with i descending so that
    # is_pal[i+1][j-1] is ready. Then DFS over cut positions: at `start`, try
    # every palindromic piece s[start..end]. O(n * 2^n) worst case ("aaaa").
    n = len(s)
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            is_pal[i][j] = s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1])
    res: List[List[str]] = []
    path: List[str] = []

    def bt(start: int) -> None:
        if start == n:
            res.append(path[:])
            return
        for end in range(start, n):
            if is_pal[start][end]:
                path.append(s[start:end + 1])
                bt(end + 1)
                path.pop()

    bt(0)
    return res


# ---------------------------------------------------------------- Part 8
class _TrieNode:
    __slots__ = ("children", "word")

    def __init__(self) -> None:
        self.children: Dict[str, _TrieNode] = {}
        self.word: Optional[str] = None  # set on the terminal node of a word


def find_words(board: List[List[str]], words: List[str]) -> List[str]:
    # Walk the board and the trie in lockstep so one DFS from a cell searches
    # ALL words sharing that prefix. Three tricks:
    #   1. store the whole word at the terminal node (no path rebuild),
    #   2. set node.word = None on a hit => each word reported once,
    #   3. delete childless nodes on the way back (prune) so later starts
    #      never re-walk prefixes whose words are all found.
    # Cells are marked "#" while on the path and restored on return.
    root = _TrieNode()
    for w in words:
        node = root
        for ch in w:
            node = node.children.setdefault(ch, _TrieNode())
        node.word = w

    m, n = len(board), len(board[0])
    res: List[str] = []

    def dfs(r: int, c: int, parent: _TrieNode) -> None:
        ch = board[r][c]
        node = parent.children.get(ch)
        if node is None:
            return
        if node.word is not None:
            res.append(node.word)
            node.word = None
        board[r][c] = "#"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and board[nr][nc] != "#":
                dfs(nr, nc, node)
        board[r][c] = ch
        if not node.children and node.word is None:
            del parent.children[ch]  # prune dead leaf

    for r in range(m):
        for c in range(n):
            if root.children:
                dfs(r, c, root)
    return res


# ---------------------------------------------------------------- Part 9
def solve_sudoku(board: List[List[str]]) -> None:
    # Constraint sets per row / col / 3x3 box. At each step choose the empty
    # cell with the FEWEST legal digits (MRV heuristic): forced cells get
    # filled without branching and contradictions surface early. Backtrack by
    # undoing the three set insertions. Runs the LC37 puzzle in milliseconds.
    rows: List[Set[str]] = [set() for _ in range(9)]
    cols: List[Set[str]] = [set() for _ in range(9)]
    boxes: List[Set[str]] = [set() for _ in range(9)]
    empties: List[tuple] = []
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".":
                empties.append((r, c))
            else:
                rows[r].add(v)
                cols[c].add(v)
                boxes[(r // 3) * 3 + c // 3].add(v)

    def candidates(r: int, c: int) -> List[str]:
        b = (r // 3) * 3 + c // 3
        return [d for d in "123456789" if d not in rows[r] and d not in cols[c] and d not in boxes[b]]

    def solve() -> bool:
        if not empties:
            return True
        idx = min(range(len(empties)), key=lambda i: len(candidates(*empties[i])))
        r, c = empties[idx]
        cands = candidates(r, c)
        if not cands:
            return False
        empties[idx], empties[-1] = empties[-1], empties[idx]  # swap-remove (order is irrelevant)
        empties.pop()
        b = (r // 3) * 3 + c // 3
        for d in cands:
            board[r][c] = d
            rows[r].add(d)
            cols[c].add(d)
            boxes[b].add(d)
            if solve():
                return True
            rows[r].remove(d)
            cols[c].remove(d)
            boxes[b].remove(d)
        board[r][c] = "."
        empties.append((r, c))
        return False

    solve()


# ---------------------------------------------------------------- Part 10
def build_bundles(prices: List[int], budget: int, max_items: Optional[int] = None) -> List[List[int]]:
    # combination_sum2 with an item-count cap. Sorted input gives two prunes:
    #   * break once prices[i] > remaining (every later price is larger too),
    #   * skip prices[i] == prices[i-1] for i > start (same multiset as the
    #     sibling branch already explored) -- this is what keeps [1]*30 with
    #     budget 10 linear instead of C(30, 10).
    # Because we scan ascending and take in index order, the output is
    # already in lexicographic order with each bundle ascending.
    prices = sorted(prices)
    res: List[List[int]] = []
    path: List[int] = []

    def bt(start: int, remaining: int) -> None:
        if remaining == 0:
            res.append(path[:])
            return
        if max_items is not None and len(path) >= max_items:
            return
        for i in range(start, len(prices)):
            p = prices[i]
            if p > remaining:
                break
            if i > start and p == prices[i - 1]:
                continue
            path.append(p)
            bt(i + 1, remaining - p)
            path.pop()

    bt(0, budget)
    return res


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


# INTERVIEWER FOLLOW-UPS
# Q: What is the general backtracking template and where do the prunes go?
# A: choose -> recurse -> un-choose, with a copy of `path` at leaves. Prunes
#    are (a) feasibility (break on sorted overflow, conflict sets) and
#    (b) symmetry/duplicate (skip equal siblings). Both belong in the loop,
#    before `choose`, so you never pay the recursive call.
# Q: Why `break` rather than `continue` in combination sum?
# A: Only valid after sorting: if candidates[i] > remaining then every later
#    candidate is too, so the whole rest of the loop is dead. `continue` is
#    correct but does O(n) wasted iterations per node.
# Q: Iterative version of subsets / permutations?
# A: Subsets: bitmask 0..2^n-1, or "for each x: res += [s + [x] for s in res]".
#    Permutations: Heap's algorithm or next_permutation (swap-reverse); the
#    latter also gives lexicographic order and handles duplicates natively.
# Q: Word search II -- why is the trie better than running word search I
#    per word?
# A: Per word is O(W * m*n * 3^L). With a trie, one DFS from each cell
#    serves every word with that prefix, and pruning found leaves shrinks the
#    trie as the search proceeds; it is the difference between TLE and AC.
# Q: Part 10 at catalogue size 10^4 and budget 10^6 -- still backtracking?
# A: No: enumeration is exponential in the answer count. Count or test
#    feasibility with subset-sum DP (bitset over budget, O(n * budget / 64)),
#    or return the first bundle found; enumerate only when the answer is
#    known to be small (e.g. items capped by max_items).
