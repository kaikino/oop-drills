"""
UNION-FIND (Disjoint Set Union).

Interviewer:

PART 1 -- The data structure.
  Implement `DSU(n)` with `find(x)` (path compression), `union(a, b)` (union
  by rank/size; return True iff a and b were in different sets), and
  `size(x)` = size of x's set. Amortised near O(1) per op (inverse Ackermann).

PART 2 -- Connected components.
  count_components(n, edges) for an undirected graph, and
  find_circle_num(is_connected) where is_connected is an n x n 0/1 adjacency
  matrix of "provinces" (LC547).  Target: O(n^2 alpha) for the matrix.

PART 3 -- Largest follower network (TikTok HackerRank 2026).
  Raw input arrives on stdin as ONE string:
      T                      number of datasets
      M                      number of follow edges in dataset 1
      alice bob              M lines, "a follows b" (treat as undirected)
      ...                    next dataset
  Return a list with the size of the largest connected component of each
  dataset (a dataset with 0 edges has answer 0).
    "2\n3\na b\nb c\nd e\n1\nx y\n" -> [3, 2]
  Users are arbitrary strings; map them to ints on the fly.  Target: O(M alpha).

PART 4 -- Accounts merge (LC721).
  accounts[i] = [name, email1, email2, ...]. Two accounts belong to the same
  person iff they share an email. Return merged accounts as
  [name, sorted emails...]; any order of accounts is fine.
  Target: O(total emails * log) because of the sort.

PART 5 -- Redundant connection (LC684).
  A tree with one extra undirected edge. Return the edge whose removal restores
  a tree; if several, the one that appears LAST in the input.
    [[1,2],[1,3],[2,3]] -> [2,3]

PART 6 -- "Similar products" online.
  class SimilarProducts:
      add_similar(a: str, b: str) -> None      pairs arrive over time
      same_group(a: str, b: str) -> bool       may be asked between adds
      group_size(a: str) -> int                unknown product => 1
  Product ids are strings you have never seen before; create them lazily.
  Each op amortised near O(1).

PART 7 -- Evaluate division (LC399) with a weighted union-find.
  equations[i] = (a, b), values[i] = a / b. Answer queries (c, d) with c / d
  or -1.0 if unknown / unseen variable. Keep weight[x] = x / parent[x] and
  fold weights during path compression. (You already did unit conversion with
  BFS; this is the DSU flavour -- keep it brief.)
"""
from __future__ import annotations

from typing import Dict, List, Tuple


# ---------------------------------------------------------------- Part 1
class DSU:
    def __init__(self, n: int) -> None:
        pass

    def find(self, x: int) -> int:
        pass

    def union(self, a: int, b: int) -> bool:
        pass

    def size(self, x: int) -> int:
        pass


# ---------------------------------------------------------------- Part 2
def count_components(n: int, edges: List[Tuple[int, int]]) -> int:
    pass


def find_circle_num(is_connected: List[List[int]]) -> int:
    pass


# ---------------------------------------------------------------- Part 3
def largest_follower_networks(raw: str) -> List[int]:
    pass


# ---------------------------------------------------------------- Part 4
def accounts_merge(accounts: List[List[str]]) -> List[List[str]]:
    pass


# ---------------------------------------------------------------- Part 5
def find_redundant_connection(edges: List[List[int]]) -> List[int]:
    pass


# ---------------------------------------------------------------- Part 6
class SimilarProducts:
    def __init__(self) -> None:
        pass

    def add_similar(self, a: str, b: str) -> None:
        pass

    def same_group(self, a: str, b: str) -> bool:
        pass

    def group_size(self, a: str) -> int:
        pass


# ---------------------------------------------------------------- Part 7
def calc_equation(equations: List[Tuple[str, str]], values: List[float],
                  queries: List[Tuple[str, str]]) -> List[float]:
    pass


# ---------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    d = DSU(5)
    assert d.union(0, 1) is True
    assert d.union(1, 2) is True
    assert d.union(0, 2) is False
    assert d.find(0) == d.find(2) and d.find(0) != d.find(3)
    assert d.size(2) == 3 and d.size(4) == 1

    # Part 2
    assert count_components(5, [(0, 1), (1, 2), (3, 4)]) == 2
    assert count_components(5, [(0, 1), (1, 2), (2, 3), (3, 4)]) == 1
    assert count_components(3, []) == 3
    assert find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]) == 2
    assert find_circle_num([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 3

    # Part 3
    raw = "2\n3\na b\nb c\nd e\n1\nx y\n"
    assert largest_follower_networks(raw) == [3, 2]
    raw2 = "3\n0\n4\nu1 u2\nu3 u4\nu2 u3\nu9 u9\n2\np q\nq p\n"
    assert largest_follower_networks(raw2) == [0, 4, 2]

    # Part 4
    acc = [["John", "johnsmith@mail.com", "john_newyork@mail.com"],
           ["John", "johnsmith@mail.com", "john00@mail.com"],
           ["Mary", "mary@mail.com"],
           ["John", "johnnybravo@mail.com"]]
    got = sorted(accounts_merge(acc))
    want = sorted([["John", "john00@mail.com", "john_newyork@mail.com", "johnsmith@mail.com"],
                   ["Mary", "mary@mail.com"],
                   ["John", "johnnybravo@mail.com"]])
    assert got == want

    # Part 5
    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4]

    # Part 6
    sp = SimilarProducts()
    sp.add_similar("shoe-a", "shoe-b")
    assert sp.same_group("shoe-a", "shoe-b") is True
    assert sp.same_group("shoe-a", "hat-z") is False
    assert sp.group_size("never-seen") == 1
    sp.add_similar("hat-z", "shoe-b")
    assert sp.same_group("shoe-a", "hat-z") is True
    assert sp.group_size("hat-z") == 3

    # Part 7
    eq = [("a", "b"), ("b", "c")]
    vals = [2.0, 3.0]
    qs = [("a", "c"), ("b", "a"), ("a", "e"), ("a", "a"), ("x", "x")]
    got7 = calc_equation(eq, vals, qs)
    assert [round(v, 5) for v in got7] == [6.0, 0.5, -1.0, 1.0, -1.0]
    print("ok")
