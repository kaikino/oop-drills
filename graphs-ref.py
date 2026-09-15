"""Reference solutions for graphs.py -- see that file for the problem statements."""
from __future__ import annotations

import heapq
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------- Part 1
def has_path(n: int, edges: List[Tuple[int, int]], src: int, dst: int) -> bool:
    # BFS, O(n + m). Pitfall: mark visited ON PUSH, not on pop, or nodes get
    # enqueued many times (worst case O(m) duplicates per node).
    adj: List[List[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen = [False] * n
    seen[src] = True
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            return True
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                q.append(v)
    return False


def has_path_uf(n: int, edges: List[Tuple[int, int]], src: int, dst: int) -> bool:
    # Union-find: near O((n + m) * alpha). Better than BFS when queries are
    # many and edges only get added (fully dynamic deletions need other tools).
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return find(src) == find(dst)


# ---------------------------------------------------------------- Part 2
class Node:
    def __init__(self, val: int, neighbors: Optional[List["Node"]] = None) -> None:
        self.val = val
        self.neighbors: List[Node] = neighbors if neighbors is not None else []


def clone_graph(node: Optional[Node]) -> Optional[Node]:
    # Invariant: `copies` maps every visited original to its clone; a clone is
    # created BEFORE we walk its neighbours, so cycles terminate. O(V + E).
    if node is None:
        return None
    copies: Dict[Node, Node] = {node: Node(node.val)}
    q = deque([node])
    while q:
        u = q.popleft()
        for v in u.neighbors:
            if v not in copies:
                copies[v] = Node(v.val)
                q.append(v)
            copies[u].neighbors.append(copies[v])
    return copies[node]


# ---------------------------------------------------------------- Part 3
def can_finish(num: int, prereqs: List[Tuple[int, int]]) -> bool:
    # Kahn: repeatedly pop in-degree-0 nodes. Cycle <=> fewer than num popped.
    adj: List[List[int]] = [[] for _ in range(num)]
    indeg = [0] * num
    for b, a in prereqs:  # a -> b
        adj[a].append(b)
        indeg[b] += 1
    q = deque(i for i in range(num) if indeg[i] == 0)
    done = 0
    while q:
        u = q.popleft()
        done += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return done == num


def find_order(num: int, prereqs: List[Tuple[int, int]]) -> List[int]:
    # DFS colouring: 0 = white (unvisited), 1 = grey (on the recursion stack),
    # 2 = black (finished). Meeting a GREY node is a back edge => cycle.
    # Post-order reversed is a topological order.
    adj: List[List[int]] = [[] for _ in range(num)]
    for b, a in prereqs:
        adj[a].append(b)
    color = [0] * num
    post: List[int] = []

    def dfs(u: int) -> bool:
        color[u] = 1
        for v in adj[u]:
            if color[v] == 1:
                return False
            if color[v] == 0 and not dfs(v):
                return False
        color[u] = 2
        post.append(u)
        return True

    for i in range(num):
        if color[i] == 0 and not dfs(i):
            return []
    post.reverse()
    return post


# ---------------------------------------------------------------- Part 4
def alien_order(words: List[str]) -> str:
    # Build edges from the FIRST differing character of adjacent words only;
    # then Kahn. Pitfall: ["abc", "ab"] has no differing char and the longer
    # word comes first => invalid. Every letter seen must be a node, even with
    # no edges. O(total chars).
    adj: Dict[str, Set[str]] = {c: set() for w in words for c in w}
    indeg = {c: 0 for c in adj}
    for w1, w2 in zip(words, words[1:]):
        for c1, c2 in zip(w1, w2):
            if c1 != c2:
                if c2 not in adj[c1]:
                    adj[c1].add(c2)
                    indeg[c2] += 1
                break
        else:
            if len(w1) > len(w2):
                return ""
    q = deque(sorted(c for c in indeg if indeg[c] == 0))  # sorted only for determinism
    out: List[str] = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in sorted(adj[u]):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return "".join(out) if len(out) == len(adj) else ""


# ---------------------------------------------------------------- Part 5
def all_paths(n: int, edges: List[Tuple[int, int]], s: int, t: int) -> List[List[int]]:
    # DFS with an explicit path list; a node is "on path" while we are inside
    # its frame, so we never revisit it => paths stay simple even with cycles.
    # Output can be exponential, so no better bound than O(paths * n).
    adj: List[List[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
    res: List[List[int]] = []
    path = [s]
    on_path = {s}

    def dfs(u: int) -> None:
        if u == t:
            res.append(path.copy())
            return
        for v in adj[u]:
            if v not in on_path:
                on_path.add(v)
                path.append(v)
                dfs(v)
                path.pop()
                on_path.remove(v)

    dfs(s)
    return res


def has_cycle(n: int, edges: List[Tuple[int, int]]) -> bool:
    # Same 3-colour DFS as find_order; grey means "on the current stack".
    # Pitfall: a plain visited set (2 states) finds cycles in UNDIRECTED graphs
    # but gives false positives on directed DAGs with shared descendants.
    adj: List[List[int]] = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
    color = [0] * n

    def dfs(u: int) -> bool:
        color[u] = 1
        for v in adj[u]:
            if color[v] == 1 or (color[v] == 0 and dfs(v)):
                return True
        color[u] = 2
        return False

    return any(color[i] == 0 and dfs(i) for i in range(n))


# ---------------------------------------------------------------- Part 6
def ladder_length(begin: str, end: str, word_list: List[str]) -> int:
    # Bucket "h*t" -> [hot, hit, ...]. BFS layer by layer; distance = words
    # on the path including begin and end. Mark visited on push. O(N * L^2).
    words = set(word_list)
    if end not in words:
        return 0
    L = len(begin)
    buckets: Dict[str, List[str]] = defaultdict(list)
    for w in words:
        for i in range(L):
            buckets[w[:i] + "*" + w[i + 1:]].append(w)
    q = deque([(begin, 1)])
    seen = {begin}
    while q:
        w, d = q.popleft()
        if w == end:
            return d
        for i in range(L):
            for nxt in buckets[w[:i] + "*" + w[i + 1:]]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, d + 1))
    return 0


# ---------------------------------------------------------------- Part 7
def network_delay_time(times: List[Tuple[int, int, int]], n: int, k: int) -> int:
    # Dijkstra with lazy deletion: the heap may hold several entries for the
    # same node; skip an entry when its distance is larger than what we already
    # know (stale). Never relax with negative weights. O(E log E).
    adj: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        adj[u].append((v, w))
    dist = {k: 0}
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue  # stale entry
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return max(dist.values()) if len(dist) == n else -1


# ---------------------------------------------------------------- Part 8
def find_cheapest_price(n: int, flights: List[Tuple[int, int, int]], src: int, dst: int, k: int) -> int:
    # Bellman-Ford limited to k+1 rounds. Relax from a SNAPSHOT of the previous
    # round so one round can only extend paths by exactly one edge; otherwise a
    # chain of relaxations inside one round would use more than k+1 edges.
    INF = float("inf")
    dist = [INF] * n
    dist[src] = 0
    for _ in range(k + 1):
        prev = dist[:]
        for u, v, w in flights:
            if prev[u] + w < dist[v]:
                dist[v] = prev[u] + w
    return -1 if dist[dst] == INF else int(dist[dst])


# ---------------------------------------------------------------- Part 9
def find_itinerary(tickets: List[Tuple[str, str]]) -> List[str]:
    # Hierholzer: greedily walk the smallest unused edge; when stuck, the node
    # is appended to the route (post-order). Reversed post-order is the Euler
    # path. Adjacency is sorted descending so pop() yields the smallest.
    adj: Dict[str, List[str]] = defaultdict(list)
    for a, b in sorted(tickets, reverse=True):
        adj[a].append(b)
    route: List[str] = []
    stack = ["JFK"]
    while stack:
        while adj[stack[-1]]:
            stack.append(adj[stack[-1]].pop())
        route.append(stack.pop())
    return route[::-1]


# ---------------------------------------------------------------- Part 10
def min_completion_time(n: int, duration: List[int], deps: List[Tuple[int, int]]) -> int:
    # Longest path in a DAG (critical path). Process in Kahn order, keeping
    # finish[v] = duration[v] + max finish of predecessors. Cycle => -1.
    adj: List[List[int]] = [[] for _ in range(n)]
    indeg = [0] * n
    for a, b in deps:
        adj[a].append(b)
        indeg[b] += 1
    finish = duration[:]  # start time 0 for sources
    q = deque(i for i in range(n) if indeg[i] == 0)
    done = 0
    while q:
        u = q.popleft()
        done += 1
        for v in adj[u]:
            finish[v] = max(finish[v], finish[u] + duration[v])
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if done != n:
        return -1
    return max(finish) if n else 0


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


# INTERVIEWER FOLLOW-UPS
# Q: Why mark visited on push and not on pop in BFS?
# A: On pop, a node can be enqueued once per incoming edge => O(E) queue size
#    and duplicated work; on push each node enters the queue exactly once.
# Q: Kahn vs DFS for topo sort -- when do you prefer which?
# A: Kahn is iterative (no recursion limit), naturally detects cycles by count,
#    and gives "level" information (parallel batches). DFS is shorter when you
#    also need to report the cycle itself (walk back the grey stack).
# Q: Why does Dijkstra fail with negative edges, and what do you use instead?
# A: The greedy "settled nodes are final" invariant breaks. Use Bellman-Ford
#    (O(VE)) or, for DAGs, one pass in topological order.
# Q: In Part 8 why not run Dijkstra with a (cost, stops) state?
# A: You can (state = node x stops), but the plain Dijkstra visited-set prunes
#    a cheaper-but-longer path; you need to allow revisits with fewer stops.
# Q: Part 10 with only P machines instead of unlimited parallelism?
# A: That is NP-hard in general (scheduling with precedence); list scheduling
#    with a heap of ready tasks is a common greedy approximation.
