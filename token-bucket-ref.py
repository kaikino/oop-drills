from __future__ import annotations

"""Token Bucket & friends - reference solution. See token-bucket.py for the problem."""

from collections import deque
from typing import Callable, Deque, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Part 1 - Token bucket
# DATA SHAPE: two floats: tokens (current level), last (time of last refill),
#             plus the constants capacity, rate.
# INVARIANT:  0 <= tokens <= capacity; after _refill(), `last == now()`.
# COMPLEXITY: O(1) time, O(1) memory per bucket. No background thread: refill
#             is computed lazily from elapsed time on each allow().
# PITFALLS:   cap at capacity (an idle bucket must not accumulate a huge burst);
#             clock going backwards -> treat elapsed as 0; cost > capacity can
#             never succeed (reject, don't spin).
# ---------------------------------------------------------------------------
class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float, now: Callable[[], float]) -> None:
        self.capacity = capacity
        self.rate = refill_rate_per_sec
        self.now = now
        self.tokens: float = float(capacity)   # start full: allow an initial burst
        self.last: float = now()

    def _refill(self) -> None:
        t = self.now()
        elapsed = max(0.0, t - self.last)
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.rate)
        self.last = t

    def allow(self, cost: int = 1) -> bool:
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def available(self) -> int:
        self._refill()
        return int(self.tokens)


# ---------------------------------------------------------------------------
# Part 2 - Per-key buckets with idle eviction
# DATA SHAPE: dict: key -> [TokenBucket, last_seen_ts]. Eviction sweeps the dict
#             on allow() at most once per `sweep_every` seconds (amortized), and
#             removes keys idle for >= idle_ttl.
# WHY OK:     a bucket that has been idle for >= capacity/rate seconds is full
#             again; recreating it fresh (full) is indistinguishable to the
#             client as long as idle_ttl >= capacity/rate. State that condition!
# COMPLEXITY: allow O(1) amortized; memory O(active keys within idle_ttl).
# ---------------------------------------------------------------------------
class KeyedLimiter:
    def __init__(self, capacity: int, refill_rate_per_sec: float, now: Callable[[], float],
                 idle_ttl: float = 60.0, sweep_every: float = 10.0) -> None:
        self.capacity = capacity
        self.rate = refill_rate_per_sec
        self.now = now
        self.idle_ttl = idle_ttl
        self.sweep_every = sweep_every
        self.buckets: Dict[str, list] = {}        # key -> [bucket, last_seen]
        self.last_sweep: float = now()

    def _sweep(self) -> None:
        t = self.now()
        if t - self.last_sweep < self.sweep_every:
            return
        self.last_sweep = t
        dead = [k for k, (_, seen) in self.buckets.items() if t - seen >= self.idle_ttl]
        for k in dead:
            del self.buckets[k]

    def allow(self, key: str, cost: int = 1) -> bool:
        self._sweep()
        entry = self.buckets.get(key)
        if entry is None:
            entry = self.buckets[key] = [TokenBucket(self.capacity, self.rate, self.now), 0.0]
        entry[1] = self.now()
        return entry[0].allow(cost)

    def size(self) -> int:
        return len(self.buckets)


# ---------------------------------------------------------------------------
# Part 3a - Leaky bucket as a queue
# DATA SHAPE: deque of queued request ids + `last_drain` timestamp + fractional
#             `credit` (how much drain time has accumulated).
# SEMANTICS:  offer() enqueues if len < capacity else rejects; drain() releases
#             floor(elapsed * rate) items at a constant rate. Output is smooth
#             (no bursts) but latency is added; token bucket allows bursts.
# ---------------------------------------------------------------------------
class LeakyBucketQueue:
    def __init__(self, capacity: int, leak_rate_per_sec: float, now: Callable[[], float]) -> None:
        self.capacity = capacity
        self.rate = leak_rate_per_sec
        self.now = now
        self.q: Deque[str] = deque()
        self.last: float = now()
        self.credit: float = 0.0

    def offer(self, req_id: str) -> bool:
        if len(self.q) >= self.capacity:
            return False
        if not self.q:                 # leak clock starts when the bucket stops being empty
            self.last = self.now()
            self.credit = 0.0
        self.q.append(req_id)
        return True

    def drain(self) -> list:
        t = self.now()
        self.credit += max(0.0, t - self.last) * self.rate
        self.last = t
        out = []
        while self.q and self.credit >= 1.0:
            out.append(self.q.popleft())
            self.credit -= 1.0
        return out


# ---------------------------------------------------------------------------
# Part 3b - Fixed window counter
# DATA SHAPE: (window_start, count). Window id = floor(now / window).
# PROBLEM:    boundary burst: `limit` requests at 0.99 and `limit` more at 1.01
#             both pass -> 2x the limit inside one real second.
# ---------------------------------------------------------------------------
class FixedWindowCounter:
    def __init__(self, limit: int, window_sec: float, now: Callable[[], float]) -> None:
        self.limit = limit
        self.window = window_sec
        self.now = now
        self.window_id: int = -1
        self.count = 0

    def allow(self) -> bool:
        wid = int(self.now() // self.window)
        if wid != self.window_id:
            self.window_id, self.count = wid, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


# ---------------------------------------------------------------------------
# Part 3c - Sliding window counter (Cloudflare approximation)
# DATA SHAPE: (cur_window_id, cur_count, prev_count).
# ESTIMATE:   est = prev_count * (1 - elapsed_fraction_of_current_window) + cur_count
#             assumes the previous window's requests were spread evenly.
# WHY:        O(1) memory like fixed window, but smooths the boundary burst;
#             error is small in practice (Cloudflare: 0.003% of requests wrongly
#             allowed/blocked). Exact alternative = sliding log (memory O(limit)).
# PITFALL:    if the current window is more than one window past the stored
#             one, prev_count must become 0 (not the old cur_count).
# ---------------------------------------------------------------------------
class SlidingWindowCounter:
    def __init__(self, limit: int, window_sec: float, now: Callable[[], float]) -> None:
        self.limit = limit
        self.window = window_sec
        self.now = now
        self.window_id: int = -1
        self.cur = 0
        self.prev = 0

    def _roll(self, t: float) -> None:
        wid = int(t // self.window)
        if wid == self.window_id:
            return
        if wid == self.window_id + 1:
            self.prev = self.cur
        else:
            self.prev = 0
        self.cur = 0
        self.window_id = wid

    def allow(self) -> bool:
        t = self.now()
        self._roll(t)
        frac = (t - self.window_id * self.window) / self.window      # in [0,1)
        est = self.prev * (1.0 - frac) + self.cur
        if est + 1 <= self.limit:
            self.cur += 1
            return True
        return False


# ---------------------------------------------------------------------------
# Part 4 - model answer: distributed rate limiting
#
# Where the state lives: every API gateway instance would otherwise have its own
#   bucket, so N instances allow N x the limit. Centralize the bucket in Redis
#   (one key per client), or accept per-instance limits scaled by 1/N (cheap but
#   uneven under sticky routing).
# Atomicity: read-tokens / compute / write-tokens is a race across instances.
#   Use a Lua script (EVAL): Redis executes scripts atomically, single-threaded:
#     local t = redis.call('HMGET', key, 'tokens', 'ts')
#     refill from (now - ts) * rate, cap at capacity, if tokens >= cost then
#     decrement and return 1 else 0; HSET both fields; PEXPIRE key idle_ttl.
#   Sliding-window-counter version: two INCR keys per window + MGET, or
#   ZADD/ZREMRANGEBYSCORE/ZCARD in one script for the exact sliding log.
# Clock skew: never use each app server's clock inside the script; pass
#   nothing and use redis.call('TIME') so a single clock orders all updates.
#   If the app clock must be used, tolerate small negative elapsed (clamp 0).
# Hot keys: one very active client hammers one Redis shard. Options: local
#   pre-check (a small per-instance bucket rejects obvious floods before Redis),
#   batching (ask Redis for 10 tokens at a time and spend them locally, trading
#   precision), or split the key into K sub-buckets each holding limit/K.
# Failure mode: Redis down -> fail open (allow, log) for user-facing APIs; fail
#   closed for abuse-sensitive endpoints (login, coupon redemption).
# Latency: one Redis round trip (~0.3 ms in-DC) per request is usually fine;
#   the gateway pipelines many clients' scripts.
# Response: return 429 with Retry-After = ceil((cost - tokens) / rate).
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    clock = {"t": 0.0}
    now = lambda: clock["t"]

    # Part 1
    tb = TokenBucket(capacity=3, refill_rate_per_sec=1.0, now=now)
    assert [tb.allow() for _ in range(4)] == [True, True, True, False]   # initial burst of 3
    clock["t"] = 0.5
    assert tb.allow() is False                     # only 0.5 token refilled
    clock["t"] = 1.0
    assert tb.allow() is True                      # 1 token refilled since t=0
    assert tb.allow() is False
    clock["t"] = 100.0
    assert tb.available() == 3                     # capped at capacity, not 99
    assert tb.allow(cost=3) is True
    assert tb.allow(cost=1) is False
    clock["t"] = 101.0
    assert tb.allow(cost=5) is False               # cost > capacity never succeeds
    assert tb.available() == 1                     # and did not consume anything
    clock["t"] = 50.0                              # clock went backwards
    assert tb.allow() is True                      # elapsed clamped to 0; still had 1 token
    assert tb.allow() is False

    # Part 2
    clock["t"] = 0.0
    kl = KeyedLimiter(capacity=2, refill_rate_per_sec=1.0, now=now, idle_ttl=5.0, sweep_every=1.0)
    assert kl.allow("a") and kl.allow("a") and not kl.allow("a")
    assert kl.allow("b")                           # independent bucket
    assert kl.size() == 2
    clock["t"] = 3.0
    assert kl.allow("b")                           # b seen at t=3
    clock["t"] = 6.0                               # a idle 6s >= 5 -> evicted on next sweep
    assert kl.allow("c")
    assert kl.size() == 2 and "a" not in kl.buckets and "b" in kl.buckets
    assert kl.allow("a")                           # recreated full (idle_ttl >= capacity/rate)

    # Part 3a leaky bucket queue
    clock["t"] = 0.0
    lb = LeakyBucketQueue(capacity=3, leak_rate_per_sec=2.0, now=now)
    assert [lb.offer(str(i)) for i in range(4)] == [True, True, True, False]
    assert lb.drain() == []                        # no time passed
    clock["t"] = 0.5
    assert lb.drain() == ["0"]                     # 0.5s * 2/s = 1 item
    clock["t"] = 2.0
    assert lb.drain() == ["1", "2"]                # 3 credits but only 2 queued
    clock["t"] = 10.0
    assert lb.offer("x") and lb.offer("y")
    assert lb.drain() == []                        # leak clock restarted at t=10 (was empty)
    clock["t"] = 10.5
    assert lb.drain() == ["x"]

    # Part 3b fixed window boundary burst
    clock["t"] = 0.0
    fw = FixedWindowCounter(limit=2, window_sec=1.0, now=now)
    clock["t"] = 0.99
    assert fw.allow() and fw.allow() and not fw.allow()
    clock["t"] = 1.01
    assert fw.allow() and fw.allow()               # 4 allowed within 0.02s: the problem

    # Part 3c sliding window counter
    clock["t"] = 0.0
    sw = SlidingWindowCounter(limit=2, window_sec=1.0, now=now)
    clock["t"] = 0.99
    assert sw.allow() and sw.allow() and not sw.allow()
    clock["t"] = 1.01
    assert not sw.allow()                          # est = 2*(1-0.01) + 0 = 1.98 -> +1 > 2
    clock["t"] = 1.5
    assert sw.allow()                              # est = 2*0.5 = 1 -> ok
    assert not sw.allow()                          # est = 1 + 1 = 2 -> +1 > 2
    clock["t"] = 5.0                               # skipped several windows -> prev = 0
    assert sw.allow() and sw.allow() and not sw.allow()
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Token bucket vs leaky bucket in one sentence each?
#    A: Token bucket bounds the *average* rate but permits bursts up to capacity;
#       leaky bucket (as a queue) forces a perfectly smooth output rate and adds
#       queueing latency (or drops when full).
# Q: Why start the bucket full?
#    A: A new client should get its burst allowance immediately; starting empty
#       makes the first requests fail, which surprises users. Either is defensible
#       if stated.
# Q: Float drift over days?
#    A: tokens is re-derived from elapsed*rate each call and clamped, so error
#       does not accumulate beyond one call's rounding. Could use integer
#       micro-tokens (tokens * 1e6) for exactness.
# Q: Memory of KeyedLimiter with 10M clients?
#    A: ~100 bytes per entry -> 1 GB; idle eviction bounds it to active clients;
#       or move to Redis with PEXPIRE on each key so Redis does the eviction.
# Q: How do you return the wait time to the client?
#    A: Retry-After = ceil((cost - tokens) / rate) seconds; for sliding window
#       counter, time until est drops below limit (solve prev*(1-frac) + cur < limit).
