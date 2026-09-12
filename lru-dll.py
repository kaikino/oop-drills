"""lru_dll.py — 15 minutes. An LRU(capacity) class with get(key) and put(key, value). 
Both operations count as a "use" and must be O(1). get on a missing key returns None. 
When put adds a new key beyond capacity, the least recently used key is evicted. 
No OrderedDict — build the ordering structure yourself. Test: capacity 2, put(1,1), 
put(2,2), get(1), put(3,3); then get(2) must be None and get(1) and get(3) must succeed."""

from __future__ import annotations

class Node:
    def __init__(self, key, prev: Node | None, next: Node | None):
        self.key = key
        self.prev = prev
        self.next = next

class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.head = Node(None, None, None)
        self.tail = Node(None, self.head, None)
        self.head.next = self.tail
        self.size = 0

        self.dict = {} # key -> (value, Node)

    def get(self, key):
        if key in self.dict:
            node = self.remove(key)
            self.append(node)
            return self.dict[key][0]
        else:
            return None

    def put(self, key, value):
        if key in self.dict:
            node = self.remove(key)
            self.append(node)
            self.dict[key] = (value, node)
        else:
            while self.size >= self.capacity: # minimum is 1
                assert self.head.next is not None
                toremove = self.head.next.key
                self.remove(toremove)
                del self.dict[toremove]
            node = Node(key, None, None)
            self.append(node)
            self.dict[key] = (value, node)


    def remove(self, key): # node must exist. return stripped Node
        node = self.dict[key][1]
        node.prev.next = node.next
        node.next.prev = node.prev
        node.next = None
        node.prev = None
        self.size -= 1
        return node

    def append(self, node):
        node.prev = self.tail.prev
        node.next = self.tail
        assert node.prev is not None
        node.prev.next = node
        self.tail.prev = node
        self.size += 1
