from collections import deque
import heapq, itertools


def bfs(graph, source):
    dist = {source: 0}                       # source at distance 0
    q = deque([source])
    while q:
        node = q.popleft()                   # left end = queue
        for adj in graph.get(node, []):
            if adj not in dist:              # dist doubles as visited
                dist[adj] = dist[node] + 1
                q.append(adj)
    return dist


def dfs(graph, source):
    order, visited, stack = [], set(), [source]
    while stack:
        node = stack.pop()                   # node is a str, not a tuple
        if node in visited:                  # mark on pop
            continue
        visited.add(node)
        order.append(node)
        for adj in reversed(graph.get(node, [])):   # reversed: visit in listed order
            if adj not in visited:
                stack.append(adj)
    return order


heap = []
counter = itertools.count()                  # ONE counter, created once
for prio, name in [(10, "backup"), (15, "rotate"), (12, "sync"), (15, "purge"), (15, "audit")]:
    heapq.heappush(heap, (prio, next(counter), {"name": name}))   # next() -> int
for _ in range(3):
    print(heapq.heappop(heap)[2]["name"])    # backup, sync, rotate (FIFO within 15)


if __name__ == "__main__":
    g = {"a": ["b", "c"], "b": ["d", "a"], "c": ["d"], "d": []}
    assert bfs(g, "a") == {"a": 0, "b": 1, "c": 1, "d": 2}
    assert dfs(g, "a") == ["a", "b", "d", "c"]
    print("ok")
