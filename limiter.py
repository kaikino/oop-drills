"""Rate limiter, from Day 3. (The LRU and twenty-line `Editor` warm-ups are still owed; 
do them before tomorrow's session.) New file `limiter.py`, 50 minutes, same rules — and 
this time, aim for at most three clarifying questions and a two-sentence design before typing.

Interviewer: 
"We run an API gateway and want to stop any one client from hammering it.

Part 1: write a class `RateLimiter(limit, window, now)` — `limit` is the maximum number of 
requests a client may make in any rolling window of `window` seconds, and `now` is a clock 
function like before. It has one method, `allow(client_id) -> bool`: return `True` and 
count the request if the client is under the limit, otherwise return `False` without 
counting it. 'Rolling' means: with `limit=3, window=60`, a client who made requests at t=0, 
10, 20 is refused at t=30 and allowed again at t=60.0001, when the t=0 request has aged out.
"""
# from collections import deque, defaultdict

# class RateLimiter:
#     def __init__(self, limit, window, now):
#         self.qdict = defaultdict(deque) # client_id -> [expire_time, ...]
#         self.limit = limit
#         self.window = window
#         self.now = now

#     def allow(self, client_id):
#         q = self.qdict[client_id]
#         while q:
#             if q[0] < self.now():
#                 q.popleft()
#             else:
#                 break
#         if len(q) >= self.limit:
#             return False

#         q.append(self.now() + self.window)
#         return True

"""Ops wants two changes. Different clients get different limits — a config 
dict {client_id: (limit, window)} passed at construction, with a default for clients not 
in it. And there's a global cap: no more than global_limit allowed requests across all 
clients in any rolling global_window. A request must pass both checks to be allowed, and 
must count against both only if allowed. Plan in two sentences, then code."""


from collections import deque, defaultdict

class RateLimiter:
    def __init__(self, config, global_limit, global_window, limit, window, now):
        self.qdict = defaultdict(deque) # client_id -> [expire_time, ...]
        self.limit = limit
        self.window = window
        self.now = now

        self.config = config
        self.globalq = deque()
        self.global_limit = global_limit
        self.global_window = global_window

    def allow(self, client_id):
        q = self.qdict[client_id]
        now = self.now()
        while q:
            if q[0] < now:
                q.popleft()
            else:
                break
        while self.globalq:
            if self.globalq[0] < now:
                self.globalq.popleft()
            else:
                break

        limit, window = self.config.get(client_id, (self.limit, self.window))
        if len(q) >= limit or len(self.globalq) >= self.global_limit:
            return False

        self.globalq.append(now + self.global_window)
        q.append(now + window)
        return True