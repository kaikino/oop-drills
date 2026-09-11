import heapq


class KVstore:
    def __init__(self, now):
        self.now = now
        self.table = {}   # key -> (value, expiry)
        self.heap = []    # (expiry, key); may hold stale entries

    def set(self, key, value, ttl=None):
        self._reclaim()
        if ttl is None:
            expiry = float("inf")
        else:
            expiry = self.now() + ttl
            heapq.heappush(self.heap, (expiry, key))   # O(log n)
        self.table[key] = (value, expiry)

    def get(self, key):
        item = self.table.get(key)
        if item is None:
            return None
        value, expiry = item
        if expiry < self.now():
            del self.table[key]        # heap entry becomes stale; ignored later
            return None
        return value

    def _reclaim(self):
        """Pop every heap entry whose time has passed. Each entry is pushed once
        and popped at most once, so this is O(log n) amortized per set."""
        t = self.now()
        while self.heap and self.heap[0][0] < t:
            expiry, key = heapq.heappop(self.heap)
            item = self.table.get(key)
            # Only delete if the table still holds *this* expiry; otherwise the
            # key was re-set (or already removed) and this entry is stale.
            if item is not None and item[1] == expiry:
                del self.table[key]


if __name__ == "__main__":
    clock = {"t": 0}
    s = KVstore(now=lambda: clock["t"])
    s.set("a", "1", ttl=5)
    clock["t"] = 2
    s.set("a", "2", ttl=100)        # old heap entry (5, "a") is now stale
    clock["t"] = 6
    s.set("b", "x")                 # reclaim pops (5,"a") but table expiry is 102 -> keep
    assert s.get("a") == "2"
    clock["t"] = 200
    s.set("c", "y")                 # reclaim pops (102,"a") -> delete
    assert "a" not in s.table and s.get("a") is None
    print("ok")
