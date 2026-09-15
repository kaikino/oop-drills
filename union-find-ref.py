"""Reference solutions for union-find.py -- see that file for the problem statements."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple


# ---------------------------------------------------------------- Part 1
class DSU:
    # Invariant: parent[root] == root; sz is only meaningful at roots.
    # Path compression + union by size => amortised O(alpha(n)) per op.
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.sz = [1] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # full path compression, iterative
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra  # small tree under big tree
        self.sz[ra] += self.sz[rb]
        return True

    def size(self, x: int) -> int:
        return self.sz[self.find(x)]


# ---------------------------------------------------------------- Part 2
def count_components(n: int, edges: List[Tuple[int, int]]) -> int:
    # Start with n components; every successful union removes one.
    d = DSU(n)
    comps = n
    for a, b in edges:
        if d.union(a, b):
            comps -= 1
    return comps


def find_circle_num(is_connected: List[List[int]]) -> int:
    n = len(is_connected)
    d = DSU(n)
    comps = n
    for i in range(n):
        for j in range(i + 1, n):  # matrix is symmetric, upper triangle suffices
            if is_connected[i][j] and d.union(i, j):
                comps -= 1
    return comps


# ---------------------------------------------------------------- Part 3
def largest_follower_networks(raw: str) -> List[int]:
    # Parse with an iterator over lines so we never index past the input.
    # Users get ints lazily via a dict; a DSU sized to 2*M is enough.
    lines = iter(raw.strip("\n").split("\n")) if raw.strip() else iter([])
    t = int(next(lines))
    out: List[int] = []
    for _ in range(t):
        m = int(next(lines))
        ids: Dict[str, int] = {}
        d = DSU(2 * m)
        best = 0
        for _ in range(m):
            a, b = next(lines).split()
            for u in (a, b):
                if u not in ids:
                    ids[u] = len(ids)
            d.union(ids[a], ids[b])
            best = max(best, d.size(ids[a]))
        out.append(best)
    return out


# ---------------------------------------------------------------- Part 4
def accounts_merge(accounts: List[List[str]]) -> List[List[str]]:
    # Union account INDICES (not emails) through the first email of each
    # account; email -> first account index that owned it.
    n = len(accounts)
    d = DSU(n)
    owner: Dict[str, int] = {}
    for i, acc in enumerate(accounts):
        for email in acc[1:]:
            if email in owner:
                d.union(i, owner[email])
            else:
                owner[email] = i
    groups: Dict[int, List[str]] = defaultdict(list)
    for email, i in owner.items():
        groups[d.find(i)].append(email)
    return [[accounts[r][0]] + sorted(emails) for r, emails in groups.items()]


# ---------------------------------------------------------------- Part 5
def find_redundant_connection(edges: List[List[int]]) -> List[int]:
    # Process edges in input order; the first edge whose endpoints are already
    # connected closes the (only) cycle and is by construction the last such
    # edge in the input. O(n alpha).
    d = DSU(len(edges) + 1)
    for a, b in edges:
        if not d.union(a, b):
            return [a, b]
    return []


# ---------------------------------------------------------------- Part 6
class SimilarProducts:
    # Dict-backed DSU so ids can be any hashable and appear lazily.
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}
        self.sz: Dict[str, int] = {}

    def _find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.sz[x] = 1
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def add_similar(self, a: str, b: str) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.sz[ra] += self.sz[rb]

    def same_group(self, a: str, b: str) -> bool:
        return self._find(a) == self._find(b)

    def group_size(self, a: str) -> int:
        return self.sz[self._find(a)]


# ---------------------------------------------------------------- Part 7
def calc_equation(equations: List[Tuple[str, str]], values: List[float],
                  queries: List[Tuple[str, str]]) -> List[float]:
    # weight[x] = x / parent[x]. After find(x) with compression,
    # weight[x] = x / root. Then a / b = weight[a] / weight[b] if same root.
    parent: Dict[str, str] = {}
    weight: Dict[str, float] = {}

    def find(x: str) -> str:
        if parent[x] != x:
            p = parent[x]
            root = find(p)                # recursion is fine: depth is small
            weight[x] *= weight[p]        # x/root = (x/p) * (p/root)
            parent[x] = root
        return parent[x]

    for (a, b), v in zip(equations, values):
        for x in (a, b):
            if x not in parent:
                parent[x] = x
                weight[x] = 1.0
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            # a/b = v, a/ra = weight[a], b/rb = weight[b]
            # ra/rb = (ra/a) * (a/b) * (b/rb) = v * weight[b] / weight[a]
            weight[ra] = v * weight[b] / weight[a]

    out: List[float] = []
    for c, dd in queries:
        if c not in parent or dd not in parent or find(c) != find(dd):
            out.append(-1.0)
        else:
            out.append(weight[c] / weight[dd])
    return out


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


# INTERVIEWER FOLLOW-UPS
# Q: Why do you need BOTH path compression and union by rank?
# A: Either alone gives O(log n) amortised; together inverse-Ackermann. In
#    practice compression alone is fine, but say why you chose it.
# Q: Can union-find delete an edge?
# A: Not directly. Offline you can process deletions in reverse as unions;
#    online you need link-cut trees or Euler tour trees.
# Q: Part 3 input is 10 GB and does not fit in memory -- what changes?
# A: The DSU only needs one int per distinct user, not per edge; stream the
#    lines, never materialise the list; if users don't fit either, shard by
#    hash and merge component ids across shards (or use external sort).
# Q: In Part 5, what if the graph were directed (LC685)?
# A: Two cases: a node with in-degree 2 (drop one of its two incoming edges,
#    prefer the one that also closes a cycle) or a pure cycle (last edge).
# Q: For Part 7, why weight[ra] = v * weight[b] / weight[a]?
# A: Derive it on the board: ra/rb = (ra/a)(a/b)(b/rb); each factor is known.
