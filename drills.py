# Day 2. Two blocks: fluency drills, then the KV store again from a blank file, timed.

# **Block 1 — fluency drills (~45 min).** New file `drills.py`, autocomplete off. Type each from memory, don't run until the end, then run and log every miss in the bug ledger:

# 1. An `LRU(capacity)` with `get`/`put` using `OrderedDict`. Then the same thing with a hand-rolled doubly linked list and a dict of key → node. Sentinel head and tail nodes make it far less fiddly.

# from collections import OrderedDict

# class LRU:
#     def __init__(self, capacity: int):
#         self.capacity = capacity
#         self.queue = OrderedDict()

#     def get(self, key: int):
#         if key in self.queue:
#             self.queue.move_to_end(key)
#             return self.queue.get(key)
#         return None

#     def set(self, key: int, value: int):
#         if key in self.queue:
#             self.queue.move_to_end(key)
#             self.queue[key] = value
#         else:
#             if self.capacity == len(self.queue):
#                 self.queue.popitem(last=False)
#             self.queue[key] = value

# from __future__ import annotations
# from typing import Optional

# class Node:
#     def __init__(self, value: int, prev: Optional[Node]=None, next: Optional[Node]=None):
#         self.value = value
#         self.prev = prev
#         self.next = next

# class LRU:
#     def __init__(self, capacity: int):
#         self.capacity = capacity
#         self.size = 0

#         self.head = Node(0, None, None)
#         self.tail =  Node(0, self.head, None)
#         self.head.next = self.tail

#         self.dict = {}  # key -> Node

#     def get(self, key: int):
#         if key in self.dict:
#             self.move_to_end(key)
#             return self.dict[key].value
#         return None


#     def set(self, key: int, value: int):
#         if key in self.dict:
#             self.move_to_end(key)
#             assert self.tail is not None
#             self.tail.value = value
#         else:            
#             while self.size >= self.capacity:
#                 assert self.tail is not None
#                 self.tail = self.tail.prev
#             cur = Node(value, self.tail, None)
#             assert self.tail is not None
#             self.tail.next = cur
#             self.tail = cur


#     def move_to_end(self, key: int):
#         cur = self.dict[key]
#         cur.prev.next = cur.next
#         cur.next.prev = cur.prev
#         assert self.tail is not None
#         self.tail.next = cur
#         cur.next = None
#         cur.prev = self.tail


# 2. A `@dataclass(frozen=True) Event(device, neighbor, state, ts)`; put two into a set; sort a list of them by `ts` with `sorted(events, key=lambda e: e.ts)`.
# from __future__ import annotations
# from dataclasses import dataclass

# @dataclass(frozen=True)
# class Event:
#     device: str
#     neighbor: str | None
#     state: str
#     ts: int


# event_set = {Event("one", "other", "listening", 10), Event("two", "other", "blocked", 14)}
# eventList = list(event_set)
# eventList.sort(key=lambda a: a.ts)

# 3. Iterative BFS on an adjacency dict `{node: [neighbors]}` returning distance from a source; then iterative DFS with an explicit stack.

# from collections import deque

# def bfs(graph: dict[str, list[str]], source):
#     out = {}
#     q = deque([(source, 0)])
#     vis = {source}
#     while q:
#         cur = q.popleft()
#         for adj in graph.get(cur[0], []):
#             if adj not in vis:
#                 dist = cur[1] + 1
#                 out[adj] = dist
#                 vis.add(adj)
#                 q.append((adj, dist))
#     return out

# def dfs(graph: dict[str, list[str]], source):
#     out = {}
#     stack = [source]
#     vis = set()
#     while stack:
#         cur = stack.pop()
#         for adj in graph.get(cur[0], []):
#             if adj not in vis:
#                 stack.append(adj)
#                 vis.add(adj)
    # return out




# 4. `heapq`: push `(priority, count, item)` tuples where `count` is a running `itertools.count()` so equal priorities never compare `item`s. Pop three and say why the counter is there.


# **Drill 4 — heapq with a tiebreaker.** Write a tiny scheduler: create `heap = []` and `counter = itertools.count()`, then push five jobs as `(priority, next(counter), job)` where `job` is a dict like `{"name": "backup"}` — something that can't be compared with `<`. Give at least two jobs the same priority. Then pop three with `heapq.heappop` and print the names. The point to be able to explain: tuples compare element by element, so when two priorities tie Python moves on to compare the second element; without the counter that would be the dicts, which raises `TypeError`. The counter is always unique and increasing, so ties resolve in insertion order (FIFO within a priority) and the third element is never compared. Bonus, if you have time: `heapq.nsmallest(2, heap)` and pushing a negative priority to get a max-heap.

import heapq
import itertools

heap = []

heapq.heappush(heap, (10, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (15, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (12, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (15, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (15, itertools.count(), {"name": "backup"}))

print(heapq.heappop(heap))
print(heapq.heappop(heap))
print(heapq.heappop(heap))

print(heapq.nsmallest(2, heap))

heapq.heappush(heap, (-12, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (-15, itertools.count(), {"name": "backup"}))
heapq.heappush(heap, (-15, itertools.count(), {"name": "backup"}))



# 5. `Counter(words).most_common(3)`, `defaultdict(list)` grouping, `bisect_left` on a sorted list, `str.partition(":")`.

# **Drill 5 — the one-liners.** Four small functions, each two to four lines:

# - `top_words(text)`: split on whitespace, lowercase, `Counter(...).most_common(3)`. Say what `most_common` returns (list of `(word, count)` tuples).
# - `group_by_device(events)`: `defaultdict(list)`, append each event under `event.device`, return it. Say why `defaultdict` beats `dict.setdefault` here (no key check).
# - `insert_position(sorted_list, x)`: `bisect.bisect_left(sorted_list, x)`; then also say what `bisect_right` would return for a value already in the list. Use `[1, 3, 3, 5]` with `x=3` as the example: left gives 1, right gives 3.
# - `parse_header(line)`: for `"Content-Type: text/html"`, `key, sep, value = line.partition(":")`, return `(key.strip(), value.strip())`; say what `partition` gives back when the separator is absent (`(line, "", "")`), which is why it's safer than `split(":")[1]`.

# Twenty minutes for both, then check.

from collections import Counter
import re

def top_words(text: str):
    count = Counter(map(str.lower, re.split(r"\s+", text.strip())))
    return count.most_common(3)

from collections import defaultdict

def group_by_device(events):
    event_count = defaultdict(list)
    for event in events:
        event_count[event.device].append(event)
    return event_count

import bisect

def insert_position(sorted_list, x):
    return bisect.bisect_left(sorted_list, x)
    # right would return the index to the right of the rightmost x element


