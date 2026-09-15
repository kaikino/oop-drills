from __future__ import annotations

"""Rate Limiting: Token Bucket and Friends (TikTok Shop API gateway)

Every class takes a `now` callable returning seconds as a float; tests set a
fake clock. Nothing may sleep or spawn threads; refill is computed lazily.

Part 1 - Token bucket
    TokenBucket(capacity, refill_rate_per_sec, now). allow(cost=1) -> bool.
    The bucket starts full. On every call, first add (now - last) * rate tokens,
    capped at capacity, then if tokens >= cost subtract and return True, else
    return False (a failed call consumes nothing). available() -> int tokens.
    A cost larger than capacity can never succeed. If the clock goes backwards,
    treat elapsed time as 0.

    Example (capacity=3, rate=1/s):
        t=0:   allow() x4    -> True, True, True, False
        t=0.5: allow()       -> False        (0.5 tokens refilled)
        t=1.0: allow()       -> True
        t=100: available()   -> 3            (capped, not 99)

    Required: O(1) time and O(1) memory per bucket.

Part 2 - Per-key buckets with idle eviction
    KeyedLimiter(capacity, rate, now, idle_ttl, sweep_every) with
    allow(key, cost=1) and size(). One TokenBucket per key, created on first
    use. Keys not seen for >= idle_ttl seconds are evicted; do the sweep lazily
    inside allow(), at most once every sweep_every seconds. Explain in a comment
    why evicting and later recreating a bucket is safe (hint: relate idle_ttl to
    capacity / rate).

    Example (capacity=2, rate=1, idle_ttl=5, sweep_every=1):
        t=0: allow("a") x3   -> True, True, False ; allow("b") -> True ; size() -> 2
        t=3: allow("b")      -> True
        t=6: allow("c")      -> True ; size() -> 2   ("a" idle since 0 -> evicted)

    Required: allow O(1) amortized; memory O(active keys).

Part 3 - The other three algorithms (compare, then implement each briefly)
    a) LeakyBucketQueue(capacity, leak_rate_per_sec, now): offer(req_id) -> bool
       enqueues unless full; drain() -> list of req_ids released so far at the
       constant leak rate (floor of elapsed * rate, carrying fractional credit).
       The leak clock starts when an empty bucket receives its first item.
         capacity=3, rate=2/s: t=0 offer x4 -> T,T,T,F; t=0.5 drain() -> ["0"];
         t=2.0 drain() -> ["1","2"]
    b) FixedWindowCounter(limit, window_sec, now): allow() -> bool. Show the
       boundary-burst problem in the test: limit=2/1s allows 2 at t=0.99 and 2
       more at t=1.01, i.e. 4 requests in 20 ms.
    c) SlidingWindowCounter(limit, window_sec, now): allow() -> bool using the
       weighted-previous-window estimate
           est = prev_count * (1 - fraction_elapsed_of_current_window) + cur_count
       allow iff est + 1 <= limit. If more than one window elapsed since the
       last call, prev_count is 0.
         limit=2/1s: 2 allowed at t=0.99; t=1.01 -> False (est=1.98);
         t=1.5 -> True (est=1.0) then False; t=5.0 -> True, True, False

    Required: all O(1) time and memory. Be ready to say which one you would
    pick for (i) an API gateway (ii) smoothing writes into a DB (iii) a coupon
    redemption endpoint.

Part 4 - discussion (written answer, no code)
    Rate limiting across 50 gateway instances: where does the bucket state
    live? Write the Redis approach: the Lua script that refills + decrements
    atomically, why atomicity matters, how you handle clock skew between app
    servers (use Redis TIME), hot keys (local pre-check, token batching,
    sub-buckets), fail-open vs fail-closed when Redis is down, and what you
    return to the client (429 + Retry-After).
"""

from collections import deque
from typing import Callable, Deque, Dict, Optional, Tuple


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float, now: Callable[[], float]) -> None:
        pass

    def allow(self, cost: int = 1) -> bool:
        pass

    def available(self) -> int:
        pass


class KeyedLimiter:
    def __init__(self, capacity: int, refill_rate_per_sec: float, now: Callable[[], float],
                 idle_ttl: float = 60.0, sweep_every: float = 10.0) -> None:
        pass

    def allow(self, key: str, cost: int = 1) -> bool:
        pass

    def size(self) -> int:
        pass


class LeakyBucketQueue:
    def __init__(self, capacity: int, leak_rate_per_sec: float, now: Callable[[], float]) -> None:
        pass

    def offer(self, req_id: str) -> bool:
        pass

    def drain(self) -> list:
        pass


class FixedWindowCounter:
    def __init__(self, limit: int, window_sec: float, now: Callable[[], float]) -> None:
        pass

    def allow(self) -> bool:
        pass


class SlidingWindowCounter:
    def __init__(self, limit: int, window_sec: float, now: Callable[[], float]) -> None:
        pass

    def allow(self) -> bool:
        pass


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
