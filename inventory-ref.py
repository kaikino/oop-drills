from __future__ import annotations

"""Inventory (flash sale) - reference solution. See inventory.py for the problem text."""

from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple
import heapq
import random
import threading

HELD, CONFIRMED, RELEASED, EXPIRED = "held", "confirmed", "released", "expired"


class FakeClock:
    """Test clock: `now()` returns .t; advance() moves it forward."""

    def __init__(self, t: float = 0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, d: float) -> None:
        self.t += d


class Reservation:
    __slots__ = ("items", "expiry", "state")

    def __init__(self, items: Dict[str, int], expiry: float) -> None:
        self.items = items
        self.expiry = expiry
        self.state = HELD


# ---------------------------------------------------------------------------
# Part 1 + Part 2
# DATA SHAPE: on_hand: dict sku -> physical units not yet sold (confirmed)
#             held:    dict sku -> units inside live HELD reservations
#             res:     dict order_id -> Reservation(items: dict sku->qty, expiry, state)
#             heap:    min-heap of (expiry, order_id) for lazy expiry
# INVARIANTS: available(sku) = on_hand[sku] - held[sku] >= 0 at all times
#             held[sku] == sum of qty over reservations in state HELD (oversell check)
#             a reservation leaves HELD exactly once (confirm / release / expire)
# COMPLEXITY: reserve O(k log n) for k SKUs (k checks + 1 heap push), confirm /
#             release O(k), available O(1) amortized (each heap entry popped once).
# PITFALLS:   1) check ALL SKUs before taking ANY (all-or-none). 2) stale heap
#             entries: an order released or confirmed before its expiry is still
#             in the heap; when popped, skip it unless state == HELD and the
#             expiry matches. 3) idempotency: a repeated reserve for an order_id
#             that already holds stock must return True *without* holding more;
#             a failed attempt is not recorded so the client can retry after a
#             restock. 4) expiry is `expiry <= now` (a 60 s hold made at t=0 is
#             gone at t=60, exactly like a token bucket refill boundary).
# ---------------------------------------------------------------------------
class Inventory:
    def __init__(self, ttl_sec: int, now: Callable[[], float]) -> None:
        self.ttl = ttl_sec
        self.now = now
        self.on_hand: Dict[str, int] = defaultdict(int)
        self.held: Dict[str, int] = defaultdict(int)
        self.res: Dict[str, Reservation] = {}
        self.heap: List[Tuple[float, str]] = []

    # -- helpers ------------------------------------------------------------
    def _unhold(self, r: Reservation) -> None:
        for sku, q in r.items.items():
            self.held[sku] -= q

    def _expire(self) -> None:
        t = self.now()
        while self.heap and self.heap[0][0] <= t:
            exp, oid = heapq.heappop(self.heap)
            r = self.res.get(oid)
            if r is not None and r.state == HELD and r.expiry == exp:
                self._unhold(r)
                r.state = EXPIRED

    # -- API ----------------------------------------------------------------
    def add_stock(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        self.on_hand[sku] += qty

    def available(self, sku: str) -> int:
        self._expire()
        return self.on_hand.get(sku, 0) - self.held.get(sku, 0)

    def reserve(self, sku: str, qty: int, order_id: str) -> bool:
        return self.reserve_many({sku: qty}, order_id)

    def reserve_many(self, items: Dict[str, int], order_id: str) -> bool:
        """All-or-none hold of every (sku, qty) in `items` for TTL seconds."""
        self._expire()
        r = self.res.get(order_id)
        if r is not None:                       # idempotent replay
            return r.state in (HELD, CONFIRMED)
        if not items or any(q <= 0 for q in items.values()):
            raise ValueError("bad items")
        for sku, q in items.items():            # phase 1: check everything
            if self.on_hand.get(sku, 0) - self.held.get(sku, 0) < q:
                return False
        for sku, q in items.items():            # phase 2: take everything
            self.held[sku] += q
        exp = self.now() + self.ttl
        self.res[order_id] = Reservation(dict(items), exp)
        heapq.heappush(self.heap, (exp, order_id))
        return True

    def confirm(self, order_id: str) -> bool:
        self._expire()
        r = self.res.get(order_id)
        if r is None:
            return False
        if r.state == CONFIRMED:
            return True
        if r.state != HELD:
            return False
        for sku, q in r.items.items():
            self.held[sku] -= q
            self.on_hand[sku] -= q
        r.state = CONFIRMED
        return True

    def release(self, order_id: str) -> bool:
        self._expire()
        r = self.res.get(order_id)
        if r is None or r.state != HELD:
            return False
        self._unhold(r)
        r.state = RELEASED
        return True


# ---------------------------------------------------------------------------
# Part 3
# THE RACE WITHOUT A LOCK: reserve_many is check-then-act. Two threads both
#   read available("A") == 1, both pass the check, both do held["A"] += 1 ->
#   held == 2 > on_hand == 1: oversold. In CPython the GIL can switch threads
#   between any two bytecodes (and `held[sku] += q` is LOAD / BINARY_ADD /
#   STORE, three of them), so the GIL does NOT save you. Also the heap and the
#   `res` dict would be mutated concurrently.
# FIX: one RLock around every public method (RLock because reserve() calls
#   reserve_many()). Coarse but correct; per-SKU locks would need lock ordering
#   for multi-SKU reserves (sort the SKUs, acquire in order) to avoid deadlock.
# ---------------------------------------------------------------------------
class ConcurrentInventory(Inventory):
    def __init__(self, ttl_sec: int, now: Callable[[], float]) -> None:
        super().__init__(ttl_sec, now)
        self.lock = threading.RLock()

    def add_stock(self, sku: str, qty: int) -> None:
        with self.lock:
            super().add_stock(sku, qty)

    def available(self, sku: str) -> int:
        with self.lock:
            return super().available(sku)

    def reserve_many(self, items: Dict[str, int], order_id: str) -> bool:
        with self.lock:
            return super().reserve_many(items, order_id)

    def confirm(self, order_id: str) -> bool:
        with self.lock:
            return super().confirm(order_id)

    def release(self, order_id: str) -> bool:
        with self.lock:
            return super().release(order_id)


# ---------------------------------------------------------------------------
# Part 4 - model answer: flash sale across many servers
#
# The in-memory class only works on one box. Across N app servers the stock
# counter must live in one place with an atomic decrement:
#
# 1) DB conditional update (simplest correct thing):
#      UPDATE stock SET qty = qty - 1 WHERE sku = ? AND qty >= 1;
#    affected_rows == 1 means you got a unit, 0 means sold out. The row lock
#    serialises everyone; ~ a few thousand TPS per hot row max. Same idea for
#    multi-SKU: one transaction, SKUs updated in sorted order (deadlock
#    avoidance), any 0-row update -> rollback.
# 2) Redis: DECR stock:{sku}, if result < 0 then INCR back and reject. Cleaner:
#    a Lua script (atomic on the server) that checks `GET >= qty` then DECRBY
#    and SADD holders:{sku} order_id in one step; 100k+ ops/s per node. Redis is
#    a cache: write the confirmed deduction back to the DB asynchronously and
#    reconcile. Redis loses data -> reload counters from the DB.
# 3) Queue-based throttling: put every "buy" request on a queue (Kafka /
#    RocketMQ) and let a small pool of consumers do the DB update in order; the
#    DB never sees more than the consumers' rate. Users poll for their result
#    or get a push. Once the counter hits 0 the gateway short-circuits with
#    "sold out" without touching the queue.
# 4) Pre-warming: load the SKU's stock into Redis before the sale, pre-scale
#    app servers, pre-generate the static product page on the CDN; gate the
#    "buy" button by time so the burst is spread; per-user rate limit and
#    dedup (one order per user per SKU) at the gateway.
# 5) Accept-then-reject-at-payment: over-admit slightly (say 120% of stock)
#    into "pending payment", and let the hard check happen when the payment
#    service confirms (the DB conditional update above). Users past the real
#    stock get "sorry, sold out" at payment. Cheaper than being exact at the
#    edge, and unpaid holds time out via the TTL (Part 1's heap == Redis key
#    TTL / delayed message in production).
# ---------------------------------------------------------------------------


def check_invariants(inv: Inventory) -> None:
    live: Dict[str, int] = defaultdict(int)
    for r in inv.res.values():
        if r.state == HELD:
            for sku, q in r.items.items():
                live[sku] += q
    for sku in set(inv.on_hand) | set(inv.held):
        assert inv.on_hand[sku] >= 0
        assert inv.held[sku] == live[sku], (sku, inv.held[sku], live[sku])
        assert inv.on_hand[sku] - inv.held[sku] >= 0, "oversold"


if __name__ == "__main__":
    # Part 1
    clk = FakeClock(0)
    inv = Inventory(ttl_sec=60, now=clk)
    inv.add_stock("A", 5)
    assert inv.available("A") == 5
    assert inv.reserve("A", 3, "o1") is True
    assert inv.available("A") == 2
    assert inv.reserve("A", 3, "o1") is True          # idempotent: no double hold
    assert inv.available("A") == 2
    assert inv.reserve("A", 3, "o2") is False
    assert inv.available("A") == 2                    # failed attempt takes nothing
    assert inv.reserve("A", 2, "o2") is True          # retry with the same id is allowed
    assert inv.available("A") == 0
    assert inv.release("o2") is True
    assert inv.available("A") == 2
    assert inv.release("o2") is False                 # already released
    clk.advance(59)
    assert inv.available("A") == 2                    # o1 still held at t=59
    clk.advance(1)
    assert inv.available("A") == 5                    # expired at t=60 (lazy)
    assert inv.confirm("o1") is False                 # too late
    assert inv.reserve("A", 3, "o1") is False         # expired order cannot come back
    inv.add_stock("B", 2)
    assert inv.reserve("B", 2, "o3") is True
    clk.advance(59)
    assert inv.confirm("o3") is True
    assert inv.confirm("o3") is True                  # idempotent
    clk.advance(100)
    assert inv.available("B") == 0                    # sold, not returned by expiry
    assert inv.release("o3") is False                 # cannot release a sale
    assert inv.available("nope") == 0
    try:
        inv.reserve("A", 0, "o4")
        assert False
    except ValueError:
        pass

    # Part 2: multi-SKU all-or-none
    clk2 = FakeClock(0)
    inv2 = Inventory(ttl_sec=30, now=clk2)
    inv2.add_stock("X", 1)
    assert inv2.reserve_many({"X": 1, "Y": 1}, "m1") is False
    assert inv2.available("X") == 1                   # X was not taken
    inv2.add_stock("Y", 1)
    assert inv2.reserve_many({"X": 1, "Y": 1}, "m1") is True
    assert inv2.available("X") == 0 and inv2.available("Y") == 0
    assert inv2.reserve_many({"X": 1, "Y": 1}, "m1") is True
    clk2.advance(30)
    assert inv2.available("X") == 1 and inv2.available("Y") == 1
    check_invariants(inv2)
    # Part 2: oversell invariant under a random workload
    rng = random.Random(7)
    clk3 = FakeClock(0)
    inv3 = Inventory(ttl_sec=5, now=clk3)
    for s in "PQR":
        inv3.add_stock(s, 3)
    oid = 0
    for _ in range(2000):
        op = rng.random()
        if op < 0.5:
            oid += 1
            inv3.reserve_many({rng.choice("PQR"): rng.randint(1, 2) for _ in range(rng.randint(1, 2))}, f"r{oid}")
        elif op < 0.7:
            inv3.confirm(f"r{rng.randint(1, oid or 1)}")
        elif op < 0.85:
            inv3.release(f"r{rng.randint(1, oid or 1)}")
        elif op < 0.95:
            clk3.advance(rng.randint(0, 3))
        else:
            inv3.add_stock(rng.choice("PQR"), 1)
        check_invariants(inv3)

    # Part 3: concurrent reserves never oversell
    clk4 = FakeClock(0)
    cinv = ConcurrentInventory(ttl_sec=60, now=clk4)
    cinv.add_stock("A", 50)
    cinv.add_stock("B", 100)
    N, PER = 8, 20
    barrier = threading.Barrier(N)
    wins: List[int] = []
    dup_ok: List[bool] = []
    wl = threading.Lock()

    def worker(w: int) -> None:
        barrier.wait()
        ok = 0
        for i in range(PER):
            if cinv.reserve("A", 1, f"o-{w}-{i}"):
                ok += 1
        r = cinv.reserve("B", 5, "shared-order")      # same order from every thread
        with wl:
            wins.append(ok)
            dup_ok.append(r)

    ts = [threading.Thread(target=worker, args=(w,)) for w in range(N)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sum(wins) == 50, wins
    assert cinv.available("A") == 0
    assert all(dup_ok) and cinv.available("B") == 95  # one hold, not eight
    check_invariants(cinv)
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Why lazy expiry with a heap instead of a background thread?
#    A: No thread, no timer drift, no locking between the sweeper and requests;
#       cost is amortised O(log n) per reservation. A sweeper is needed only if
#       nobody calls the API for a long time and memory must be reclaimed.
# Q: res grows forever; when can an order_id be forgotten?
#    A: After the idempotency window (e.g. 24 h): push (expiry + window,
#       order_id) on a second heap, or store order ids in Redis with a TTL.
# Q: A customer reserves 2, then wants 3 with the same order_id?
#    A: Reservation is immutable per order_id; changing qty = release + new
#       order (or a new idempotency key). Otherwise replays become ambiguous.
# Q: How would you shard this across servers?
#    A: Shard by sku (one owner per SKU); multi-SKU reserve then needs 2PC / saga
#       (reserve each, compensate on any failure) - or keep hot flash-sale SKUs
#       on a single Redis node with a Lua script.
# Q: What if confirm() arrives after the hold expired and stock was resold?
#    A: Return False and fail the payment (or over-admit and refund). Choose the
#       TTL longer than the payment provider's p99 latency to make this rare.
