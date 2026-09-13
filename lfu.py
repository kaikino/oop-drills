"""Implement the LFUCache class:

LFUCache(int capacity) — initializes the cache with a positive capacity.
int get(int key) — returns the value of the key if it exists, otherwise returns -1.
void put(int key, int value) — updates the value if the key exists, otherwise inserts
it. When the cache reaches capacity, it must invalidate and remove the least frequently
used key before inserting a new one. If there is a tie (two or more keys with the same
frequency), the least recently used of those keys is invalidated.

A key's use counter starts at 1 when inserted and increments by 1 on every get or put
that touches it. The counter is reset to 1 when a key is removed and later reinserted.

get and put must each run in O(1) average time."""

from __future__ import annotations
class Node:
    def __init__(self, key, value, prev: Node | None, next: Node | None, freq):
        self.key = key
        self.value = value
        self.prev = prev
        self.next = next
        self.freq = freq

class LinkedList:
    def __init__(self):
        self.head = Node(0, 0, None, None, 0)
        self.tail = Node(0, 0, self.head, None, 0)
        self.head.next = self.tail
        self.size = 0


class LFUCache:
    def __init__(self, capacity):
        # dict key -> node
        # freq -> linkedlist(nodes)  Node = (value, prev, next, freq)
        # min_freq
        self.capacity = capacity
        self.keydict = {}
        self.freqs = {}   # freq -> length, head (LRU), tail (to append)
        self.min_freq = 1

    def get(self, key):
        if key in self.keydict:
            node = self.keydict[key]
            self.inc_freq(node)
            return node.value
        return -1

    def put(self, key, value):
        if key in self.keydict:
            node = self.keydict[key]
            node.value = value
            self.inc_freq(node)
        else:
            if len(self.keydict) == self.capacity:
                lfu_node = self.freqs[self.min_freq].head.next
                self.remove_node(lfu_node)
                del self.keydict[lfu_node.key]
            self.min_freq = 1
            new_node = Node(key, value, None, None, 1)
            self.append_node(new_node)
            self.keydict[key] = new_node

    def inc_freq(self, node):
        if self.remove_node(node) and self.min_freq == node.freq:
            self.min_freq = node.freq + 1
        node.freq += 1
        self.append_node(node)

    # returns True if list is now empty
    def remove_node(self, node):
        llist = self.freqs[node.freq]
        llist.size -= 1
        node.prev.next = node.next
        node.next.prev = node.prev
        if llist.size == 0:
            del self.freqs[node.freq]
            return True
        return False

    def append_node(self, node):
        if node.freq in self.freqs:
            llist = self.freqs[node.freq]
        else:
            llist = LinkedList()
            self.freqs[node.freq] = llist
        llist.size += 1
        node.next = llist.tail
        node.prev = llist.tail.prev
        llist.tail.prev.next = node
        llist.tail.prev = node
