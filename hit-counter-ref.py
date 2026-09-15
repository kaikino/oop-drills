from __future__ import annotations

"""Hit Counter - reference solution. See hit-counter.py for the problem text."""

from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
import heapq

WINDOW = 300


# ---------------------------------------------------------------------------
# Part 1
# DATA SHAPE: deque of [ts, count] pairs, ts strictly increasing left->right,
#             plus an integer `total` = sum of counts in the deque.
# INVARIANT:  every pair in the deque has ts > (last_evict_ts - 300); pairs
#             older than the query window are popped from the left on access.
# COMPLEXITY: hit O(1) amortized, get_hits O(1) amortized (each pair is pushed
#             once and popped once). Memory O(distinct timestamps in window).
# PITFALL:    window is (ts-300, ts]; the boundary ts-300 is *excluded*.
#             Coalescing same-second hits into one pair keeps memory <= 300 pairs.
# ---------------------------------------------------------------------------
class HitCounter:
    def __init__(self) -> None:
        self.q: Deque[List[int]] = deque()   # [ts, count]
        self.total = 0

    def _evict(self, ts: int) -> None:
        while self.q and self.q[0][0] <= ts - WINDOW:
            self.total -= self.q.popleft()[1]

    def hit(self, ts: int) -> None:
        self._evict(ts)
        if self.q and self.q[-1][0] == ts:
            self.q[-1][1] += 1
        else:
            self.q.append([ts, 1])
        self.total += 1

    def get_hits(self, ts: int) -> int:
        self._evict(ts)
        return self.total


# ---------------------------------------------------------------------------
# Part 2
# DATA SHAPE: two fixed lists of length 300: times[i], counts[i]; slot i = ts % 300.
# INVARIANT:  counts[i] is the number of hits at exactly times[i]. A slot whose
#             times[i] is outside (ts-300, ts] is stale and contributes 0.
# COMPLEXITY: hit O(1); get_hits O(300) = O(1) constant; memory O(300).
# PITFALL:    timestamps can skip several full windows, so a slot may hold a
#             timestamp from 2+ windows ago. Never trust the slot index alone:
#             compare times[i] with ts before adding and before counting.
# ---------------------------------------------------------------------------
class BucketHitCounter:
    def __init__(self) -> None:
        self.times = [0] * WINDOW
        self.counts = [0] * WINDOW

    def hit(self, ts: int) -> None:
        i = ts % WINDOW
        if self.times[i] != ts:          # stale slot from an earlier lap
            self.times[i] = ts
            self.counts[i] = 0
        self.counts[i] += 1

    def get_hits(self, ts: int) -> int:
        lo = ts - WINDOW                  # window is (lo, ts]
        return sum(self.counts[i] for i in range(WINDOW) if lo < self.times[i] <= ts)


# ---------------------------------------------------------------------------
# Part 3
# DATA SHAPE: dict: video_id -> BucketHitCounter; plus dict: video_id -> last_hit_ts
#             so idle videos (> 300 s without a hit) can be evicted lazily.
# COMPLEXITY: top_n is O(V * 300) to compute counts + O(V log n) with a bounded
#             heap (heapq.nsmallest on the key (-hits, video_id)).
# PITFALL:    ties -> video_id ascending; exclude zero-hit videos; n == 0 -> [].
# EVICTION:   on each hit or top_n, drop videos whose last_hit_ts <= ts - 300
#             (their counter is all-zero anyway). Done here in top_n.
# ---------------------------------------------------------------------------
class VideoHitTracker:
    def __init__(self) -> None:
        self.counters: Dict[str, BucketHitCounter] = {}
        self.last_hit: Dict[str, int] = {}

    def hit(self, video_id: str, ts: int) -> None:
        c = self.counters.get(video_id)
        if c is None:
            c = self.counters[video_id] = BucketHitCounter()
        c.hit(ts)
        self.last_hit[video_id] = ts

    def top_n(self, n: int, ts: int) -> List[Tuple[str, int]]:
        if n <= 0:
            return []
        # lazy eviction of idle videos
        for vid in [v for v, t in self.last_hit.items() if t <= ts - WINDOW]:
            del self.counters[vid]
            del self.last_hit[vid]
        rows = []
        for vid, c in self.counters.items():
            h = c.get_hits(ts)
            if h > 0:
                rows.append((-h, vid))
        best = heapq.nsmallest(n, rows)          # O(V log n)
        return [(vid, -neg) for neg, vid in best]


# ---------------------------------------------------------------------------
# Part 4 - model answer: counting likes at TikTok scale
#
# Hot path (write): like event -> Kafka (partition by video_id) -> counter
#   service does Redis INCR like:{video_id}. Redis handles ~100k+ ops/s per
#   node; INCR is atomic so no lost updates. A batch job / consumer periodically
#   flushes deltas to the DB (async write-back); the DB is the source of truth
#   for reconciliation, Redis is the serving copy.
# Hot keys: a viral video's counter lives on one Redis node. Shard it into K
#   sub-keys like:{vid}:{rand K}; INCR one at random, read sums all K (MGET).
#   K ~ 8-32 spreads load; reads get more expensive, so cache the sum.
# Reads: the like count is displayed on every feed card, so reads >> writes.
#   Serve from a local in-process cache with ~1-5 s TTL, then Redis, then DB.
#   Display "1.2M": nobody notices staleness at that scale. Small counts (<1k)
#   can afford fresher reads.
# Consistency: eventual. The user's own action must be reflected immediately:
#   the client renders the optimistic +1 and the "liked" state; the server keeps
#   a per-user set (user_id -> liked video_ids) for the heart icon.
# Idempotency: a like is (user_id, video_id); store it in a set / DB unique
#   index, INCR only when the insert is new (SADD returns 1). Unlike = SREM
#   returns 1 -> DECR. Retries and duplicate Kafka deliveries then cannot double
#   count. Never let the count go negative (clamp / reconcile).
# Robustness: Redis loss -> rebuild from the DB (count(*) per video, or a
#   materialized count with the flushed deltas). Rate limit likes per user.
#   Reconciliation job compares Redis and DB nightly.
# ---------------------------------------------------------------------------


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


# INTERVIEWER FOLLOW-UPS
# Q: Why is the window (ts-300, ts] and not [ts-300, ts]?
#    A: LC convention: "past 5 minutes" = 300 distinct seconds ending at ts; a
#       hit at exactly ts-300 is the 301st second and falls out.
# Q: Part 2 get_hits is O(300); can it be O(1)?
#    A: Keep a running `total`; on hit, when resetting a stale slot subtract its
#       old count; but slots that silently aged out (no new hit on them) still
#       count, so you'd also need to advance a cursor over skipped slots ->
#       amortized O(1) per call, worst case O(300) when time skips. Same bound.
# Q: Timestamps arrive out of order (a few seconds late)?
#    A: Buckets still work: hit(ts) lands in its own slot as long as ts is within
#       the window; drop hits older than ts_max - 300.
# Q: Millisecond granularity / 1-hour window?
#    A: Slots = window / granularity; choose coarser slots (1 s) for a 1 h window
#       and accept +-1 slot error at the boundary.
# Q: Per-video counters for 10^8 videos?
#    A: Not in one process: shard by video_id across servers; each keeps counters
#       only for videos hit recently (lazy eviction); top-N merges per-shard
#       top-N candidates (each shard's top-N is a superset of its contribution).
