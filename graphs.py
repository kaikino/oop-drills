"""
GRAPHS -- BFS / DFS / topological sort / shortest paths / Euler paths.

Interviewer:

PART 1 -- Path existence (undirected).
  We have `n` sellers labelled 0..n-1 and a list of undirected "co-listing"
  edges. Tell me whether seller `src` can reach seller `dst`.
  Do it twice: once with BFS over an adjacency list, once with union-find.
    has_path(4, [(0,1),(1,2)], 0, 2) -> True ; has_path(4, [(0,1)], 0, 3) -> False
  Constraints: n <= 1e5, edges <= 2e5.  Target: O(n + m).

PART 2 -- Clone graph.
  Given a reference to one node of a connected undirected graph (each node has
  `.val` and `.neighbors`), return a deep copy. Keep a map old->new.
  Target: O(V + E).

PART 3 -- Build dependencies (course schedule I & II).
  `num` build steps, `prereqs` is a list of (b, a) meaning "a must run before b".
    can_finish(num, prereqs) -> bool           (Kahn's algorithm)
    find_order(num, prereqs) -> List[int]      (DFS with 3 colours; [] if cycle)
  Any valid order is accepted by the tests.  Target: O(V + E).

PART 4 -- Alien dictionary (LC269).
  Product SKUs are sorted lexicographically under an unknown alphabet. Given
  the sorted list of words, return one valid ordering of all letters that
  appear, or "" if no valid order exists (cycle, or a word is followed by its
  own proper prefix, e.g. ["abc", "ab"]).
    alien_order(["wrt","wrf","er","ett","rftt"]) -> "wertf"
  Target: O(total characters).

PART 5 -- All simple paths + cycle detection (directed).
  Given a directed graph, (a) enumerate every simple path from s to t,
  (b) tell me whether the whole graph has any directed cycle.
    all_paths(4, [(0,1),(0,2),(1,3),(2,3)], 0, 3) -> [[0,1,3],[0,2,3]] (any order)
    has_cycle(3, [(0,1),(1,2),(2,0)]) -> True
  Use a DFS with an explicit path stack / on-stack set.

PART 6 -- Word ladder (LC127).
  Shortest transformation length from begin to end changing one letter at a
  time, every intermediate word in the list. Return 0 if impossible.
    ladder_length("hit","cog",["hot","dot","dog","lot","log","cog"]) -> 5
  Use the wildcard-bucket trick ("h*t") so each word expands in O(L) buckets.
  Target: O(N * L^2).

PART 7 -- Network delay time / Dijkstra (LC743).
  `times` is a list of (u, v, w) directed edges, nodes 1..n. Signal starts at k.
  Return the time until every node has received it, or -1.
  heapq with the "stale entry skip".  Target: O(E log E).

PART 8 -- Cheapest flights within K stops (LC787).
  Cheapest price from src to dst using at most k stops (k+1 edges), -1 if none.
  Bellman-Ford with exactly k+1 relaxation rounds over a COPY of dist.
  Target: O(k * E).

PART 9 -- Reconstruct itinerary (LC332).
  Tickets are (from, to). Use all of them exactly once starting at "JFK"; if
  several itineraries exist return the lexicographically smallest.
  Hierholzer's algorithm: sort adjacency reversed, pop from the end, append to
  route on post-order, reverse at the end.  Target: O(E log E).

PART 10 -- Minimum total completion time (TikTok screen).
  `n` tasks with `duration[i]`, and `deps` = list of (a, b) meaning a must
  finish before b starts. Unlimited parallelism. Return the minimum time until
  all tasks are done, or -1 if the dependency graph has a cycle.
    min_completion_time(4, [3,2,4,1], [(0,1),(0,2),(1,3),(2,3)]) -> 8   (0->2->3)
  Critical path: DP over a topological order, earliest_finish[v] =
  duration[v] + max(earliest_finish[u] for u -> v).  Target: O(V + E).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------- Part 1
def has_path(n: int, edges: List[Tuple[int, int]], src: int, dst: int) -> bool:
    pass


def has_path_uf(n: int, edges: List[Tuple[int, int]], src: int, dst: int) -> bool:
    pass


# ---------------------------------------------------------------- Part 2
class Node:
    def __init__(self, val: int, neighbors: Optional[List["Node"]] = None) -> None:
        self.val = val
        self.neighbors: List[Node] = neighbors if neighbors is not None else []


def clone_graph(node: Optional[Node]) -> Optional[Node]:
    pass


# ---------------------------------------------------------------- Part 3
def can_finish(num: int, prereqs: List[Tuple[int, int]]) -> bool:
    pass


def find_order(num: int, prereqs: List[Tuple[int, int]]) -> List[int]:
    pass


# ---------------------------------------------------------------- Part 4
def alien_order(words: List[str]) -> str:
    pass


# ---------------------------------------------------------------- Part 5
def all_paths(n: int, edges: List[Tuple[int, int]], s: int, t: int) -> List[List[int]]:
    pass


def has_cycle(n: int, edges: List[Tuple[int, int]]) -> bool:
    pass


# ---------------------------------------------------------------- Part 6
def ladder_length(begin: str, end: str, word_list: List[str]) -> int:
    pass


# ---------------------------------------------------------------- Part 7
def network_delay_time(times: List[Tuple[int, int, int]], n: int, k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 8
def find_cheapest_price(n: int, flights: List[Tuple[int, int, int]], src: int, dst: int, k: int) -> int:
    pass


# ---------------------------------------------------------------- Part 9
def find_itinerary(tickets: List[Tuple[str, str]]) -> List[str]:
    pass


# ---------------------------------------------------------------- Part 10
def min_completion_time(n: int, duration: List[int], deps: List[Tuple[int, int]]) -> int:
    pass


# ---------------------------------------------------------------- tests
def _valid_order(order: List[int], num: int, prereqs: List[Tuple[int, int]]) -> bool:
    if sorted(order) != list(range(num)):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[a] < pos[b] for b, a in prereqs)


def _graph_equal(a: Optional[Node], b: Optional[Node]) -> bool:
    seen: Dict[int, int] = {}
    stack = [(a, b)]
    while stack:
        x, y = stack.pop()
        if x is None or y is None:
            return x is y
        if x is y or x.val != y.val or len(x.neighbors) != len(y.neighbors):
            return False
        if id(x) in seen:
            if seen[id(x)] != id(y):
                return False
            continue
        seen[id(x)] = id(y)
        for p, q in zip(sorted(x.neighbors, key=lambda z: z.val), sorted(y.neighbors, key=lambda z: z.val)):
            stack.append((p, q))
    return True


if __name__ == "__main__":
    # Part 1
    assert has_path(4, [(0, 1), (1, 2)], 0, 2) is True
    assert has_path(4, [(0, 1)], 0, 3) is False
    assert has_path(1, [], 0, 0) is True
    assert has_path_uf(4, [(0, 1), (1, 2)], 0, 2) is True
    assert has_path_uf(4, [(0, 1)], 0, 3) is False

    # Part 2
    n1, n2, n3, n4 = Node(1), Node(2), Node(3), Node(4)
    n1.neighbors = [n2, n4]
    n2.neighbors = [n1, n3]
    n3.neighbors = [n2, n4]
    n4.neighbors = [n1, n3]
    c = clone_graph(n1)
    assert c is not n1 and _graph_equal(n1, c)
    assert clone_graph(None) is None
    single = Node(7)
    cs = clone_graph(single)
    assert cs is not single and cs.val == 7 and cs.neighbors == []

    # Part 3
    assert can_finish(2, [(1, 0)]) is True
    assert can_finish(2, [(1, 0), (0, 1)]) is False
    p = [(1, 0), (2, 0), (3, 1), (3, 2)]
    assert _valid_order(find_order(4, p), 4, p)
    assert find_order(2, [(1, 0), (0, 1)]) == []
    assert _valid_order(find_order(3, []), 3, [])

    # Part 4
    assert alien_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
    assert alien_order(["z", "x"]) == "zx"
    assert alien_order(["z", "x", "z"]) == ""
    assert alien_order(["abc", "ab"]) == ""
    assert sorted(alien_order(["z", "z"])) == ["z"]

    # Part 5
    paths = all_paths(4, [(0, 1), (0, 2), (1, 3), (2, 3)], 0, 3)
    assert sorted(paths) == [[0, 1, 3], [0, 2, 3]]
    paths = all_paths(3, [(0, 1), (1, 2), (0, 2), (2, 0)], 0, 2)  # graph has a cycle, paths still simple
    assert sorted(paths) == [[0, 1, 2], [0, 2]]
    assert has_cycle(3, [(0, 1), (1, 2), (2, 0)]) is True
    assert has_cycle(3, [(0, 1), (1, 2), (0, 2)]) is False
    assert has_cycle(2, [(0, 0)]) is True

    # Part 6
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]) == 5
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log"]) == 0
    assert ladder_length("a", "c", ["a", "b", "c"]) == 2

    # Part 7
    assert network_delay_time([(2, 1, 1), (2, 3, 1), (3, 4, 1)], 4, 2) == 2
    assert network_delay_time([(1, 2, 1)], 2, 1) == 1
    assert network_delay_time([(1, 2, 1)], 2, 2) == -1

    # Part 8
    fl = [(0, 1, 100), (1, 2, 100), (0, 2, 500)]
    assert find_cheapest_price(3, fl, 0, 2, 1) == 200
    assert find_cheapest_price(3, fl, 0, 2, 0) == 500
    fl2 = [(0, 1, 100), (1, 2, 100), (2, 0, 100), (1, 3, 600), (2, 3, 200)]
    assert find_cheapest_price(4, fl2, 0, 3, 1) == 700
    assert find_cheapest_price(4, fl2, 0, 3, 2) == 400  # needs the dist copy per round

    # Part 9
    assert find_itinerary([("MUC", "LHR"), ("JFK", "MUC"), ("SFO", "SJC"), ("LHR", "SFO")]) == \
        ["JFK", "MUC", "LHR", "SFO", "SJC"]
    assert find_itinerary([("JFK", "SFO"), ("JFK", "ATL"), ("SFO", "ATL"), ("ATL", "JFK"), ("ATL", "SFO")]) == \
        ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]
    assert find_itinerary([("JFK", "KUL"), ("JFK", "NRT"), ("NRT", "JFK")]) == ["JFK", "NRT", "JFK", "KUL"]

    # Part 10
    assert min_completion_time(4, [3, 2, 4, 1], [(0, 1), (0, 2), (1, 3), (2, 3)]) == 8
    assert min_completion_time(3, [5, 1, 1], []) == 5
    assert min_completion_time(3, [1, 1, 1], [(0, 1), (1, 2), (2, 0)]) == -1
    assert min_completion_time(1, [4], []) == 4
    print("ok")
