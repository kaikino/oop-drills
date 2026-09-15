from __future__ import annotations

"""Hit Counter (TikTok Shop: views / likes in the last 5 minutes)

We inject a clock: every method takes an explicit integer `ts` (seconds), and
timestamps are non-decreasing across calls. That keeps the tests deterministic.

Part 1 - basic hit counter (LC362)
    HitCounter() with hit(ts) and get_hits(ts) -> number of hits in the window
    (ts - 300, ts], i.e. the last 300 seconds inclusive of ts.

    Example:
        c = HitCounter()
        c.hit(1); c.hit(2); c.hit(3)
        c.get_hits(4)    -> 3
        c.hit(300)
        c.get_hits(300)  -> 4       # 1,2,3,300 all within (0, 300]
        c.get_hits(301)  -> 3       # ts=1 fell out: window is (1, 301]

    Required: hit O(1) amortized, get_hits O(1) amortized. Memory may grow with
    the number of hits in the window (a deque of timestamps is fine).

Part 2 - O(1) memory: circular buckets
    Now assume millions of hits per second. Keeping one entry per hit is not
    acceptable. Implement BucketHitCounter with exactly 300 slots:
    times[300], counts[300]. hit(ts) goes to slot ts % 300; if the slot's stored
    timestamp differs from ts, the slot is stale: reset it to (ts, 0) first.
    get_hits(ts) sums the slots whose stored timestamp is within (ts-300, ts].
    Timestamps may skip (e.g. no hits for 10 minutes then a burst), so a slot
    may hold a timestamp from 2 windows ago; that is why you compare the stored
    time rather than trusting the slot.

    Example:
        b = BucketHitCounter()
        b.hit(1); b.hit(1); b.hit(301)     # 301 lands on the slot of 1 -> resets it
        b.get_hits(301)  -> 1
        b.hit(2)  # (not allowed: timestamps are non-decreasing; ignore this line)

    Required: hit O(1); get_hits O(300) = O(1); memory O(300) independent of the
    hit rate. Also implement `total` so get_hits is O(1) for the common case?
    Only if time allows; a 300-slot scan is acceptable.

Part 3 - per-video counters, top-N in the last 5 minutes
    VideoHitTracker with hit(video_id, ts) and top_n(n, ts) -> list of
    (video_id, hits) sorted by hits desc, then video_id asc for ties. Use one
    BucketHitCounter per video. Videos with 0 hits in the window are excluded.

    Example:
        t = VideoHitTracker()
        t.hit("v1", 1); t.hit("v1", 2); t.hit("v2", 2); t.hit("v3", 3)
        t.top_n(2, 3)     -> [("v1", 2), ("v2", 1)]
        t.top_n(2, 301)   -> [("v1", 1), ("v2", 1)]   # v1@1 expired: window (1, 301]
        t.top_n(5, 1000)  -> []

    Required: top_n O(V log n) where V = number of tracked videos (heap of size n)
    or O(V log V) with a sort; state clearly which you chose. Discuss briefly in
    comments how you would evict videos that have had no hits for > 300 s.

Part 4 - discussion (written answer, no code)
    "Design a counting system for likes/reposts/saves at TikTok scale. Reads are
    extremely frequent; the system must be highly concurrent and robust."
    Cover: Redis INCR/HINCRBY as the hot path and async write-back to the DB;
    sharding a single hot key into K sub-counters (sum on read); read caching
    and staleness budget; eventual consistency vs. showing the user their own
    like immediately; idempotency of like events (user_id, video_id) and the
    unlike path; what happens when Redis loses data; approximate counts for
    display ("1.2M").
"""

from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
import heapq

WINDOW = 300


class HitCounter:
    """Part 1: deque of (ts, count) pairs; O(1) amortized ops, memory O(distinct ts in window)."""

    def __init__(self) -> None:
        pass

    def hit(self, ts: int) -> None:
        pass

    def get_hits(self, ts: int) -> int:
        pass


class BucketHitCounter:
    """Part 2: 300 circular slots; O(300) memory regardless of hit rate."""

    def __init__(self) -> None:
        pass

    def hit(self, ts: int) -> None:
        pass

    def get_hits(self, ts: int) -> int:
        pass


class VideoHitTracker:
    """Part 3: per-video BucketHitCounter + top-N."""

    def __init__(self) -> None:
        pass

    def hit(self, video_id: str, ts: int) -> None:
        pass

    def top_n(self, n: int, ts: int) -> List[Tuple[str, int]]:
        pass


if __name__ == "__main__":
    # Part 1
    c = HitCounter()
    c.hit(1); c.hit(2); c.hit(3)
    assert c.get_hits(4) == 3
    c.hit(300)
    assert c.get_hits(300) == 4
    assert c.get_hits(301) == 3
    assert c.get_hits(1000) == 0
    c.hit(1000); c.hit(1000)
    assert c.get_hits(1000) == 2

    # Part 2
    b = BucketHitCounter()
    b.hit(1); b.hit(1); b.hit(301)
    assert b.get_hits(301) == 1
    b2 = BucketHitCounter()
    for t in (1, 2, 3):
        b2.hit(t)
    assert b2.get_hits(4) == 3
    b2.hit(300)
    assert b2.get_hits(300) == 4
    assert b2.get_hits(301) == 3
    assert b2.get_hits(599) == 1          # only ts=300 is within (299, 599]
    assert b2.get_hits(600) == 0          # boundary excluded: (300, 600]
    b2.hit(901)                            # slot 1 held ts=1 from two windows ago
    assert b2.get_hits(901) == 1
    b3 = BucketHitCounter()
    for _ in range(10_000):
        b3.hit(5)
    assert b3.get_hits(5) == 10_000
    assert b3.get_hits(305) == 0

    # Part 3
    t = VideoHitTracker()
    t.hit("v1", 1); t.hit("v1", 2); t.hit("v2", 2); t.hit("v3", 3)
    assert t.top_n(2, 3) == [("v1", 2), ("v2", 1)]
    assert t.top_n(3, 3) == [("v1", 2), ("v2", 1), ("v3", 1)]
    assert t.top_n(2, 301) == [("v1", 1), ("v2", 1)]
    assert t.top_n(5, 1000) == []
    assert t.top_n(0, 3) == []
    print("ok")
