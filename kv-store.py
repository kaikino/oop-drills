



class KVstore:
    def __init__(self, now):
        self.now = now  
        self.table = {} # key -> (value, expiry)

    def set(self, key, value, ttl=None):
        if ttl is None:
            self.table[key] = (value, float("inf"))
        else:
            self.table[key] = (value, self.now() + ttl)

    def get(self, key):
        if key not in self.table:
            return None
        item = self.table[key]
        if item[1] < self.now():
            del self.table[key]
            return None
        else:
            return item[0]
