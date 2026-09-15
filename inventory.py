from __future__ import annotations

"""Inventory Reservation (TikTok Shop: flash-sale stock holds)

Time is injected: the constructor takes `now`, a callable returning the current
time in seconds (float or int). Tests use a FakeClock so results are
deterministic. Time never goes backwards.

Part 1 - reserve / confirm / release with a TTL hold
    Inventory(ttl_sec, now) tracks stock per SKU.
        add_stock(sku, qty)                    add physical units (qty > 0)
        reserve(sku, qty, order_id) -> bool    hold qty units for ttl_sec seconds
        confirm(order_id) -> bool              turn the hold into a sale (stock leaves)
        release(order_id) -> bool              give the hold back early
        available(sku) -> int                  units not sold and not held
    A hold that is neither confirmed nor released within ttl_sec expires and its
    units become available again (expiry <= now counts as expired). Expiry is
    lazy: no background thread; keep a min-heap keyed by expiry and pop it at
    the start of every call. reserve is idempotent per order_id: calling it
    again for an order that already holds (or confirmed) returns True and holds
    nothing extra; an order whose hold expired or was released returns False
    (the client must start a new order). A *failed* reserve (not enough stock)
    records nothing, so the same order_id may retry after a restock. confirm /
    release return False when there is no live hold (unknown, expired,
    released, or - for release - already confirmed); confirm on an already
    confirmed order returns True.

    Example (ttl 60):
        t=0   add_stock("A", 5); reserve("A", 3, "o1") -> True; available("A") -> 2
        t=0   reserve("A", 3, "o1") -> True (replay), available("A") -> 2
        t=0   reserve("A", 3, "o2") -> False; reserve("A", 2, "o2") -> True
        t=0   release("o2") -> True; available("A") -> 2
        t=59  available("A") -> 2
        t=60  available("A") -> 5     # o1 expired
        t=60  confirm("o1") -> False

    Required: reserve O(log n), confirm / release O(1), available O(1)
    amortized. Name the data structures before coding.

Part 2 - multi-SKU atomic reserve, oversell invariant
    reserve_many(items: dict sku->qty, order_id) -> bool holds every SKU or
    none of them (a cart with 3 items must not half-reserve). Refactor reserve
    to delegate to it. State the invariant that makes "oversell" impossible
    (available(sku) >= 0, and held[sku] equals the sum over live holds) and
    make sure every code path preserves it: the test replays 2000 random ops
    and checks it after each one.

    Example:
        add_stock("X", 1)
        reserve_many({"X": 1, "Y": 1}, "m1") -> False; available("X") -> 1
        add_stock("Y", 1)
        reserve_many({"X": 1, "Y": 1}, "m1") -> True

Part 3 - N threads reserving at once
    ConcurrentInventory: 8 threads each fire 20 reserve() calls at a SKU with
    50 units. Exactly 50 must succeed. Add a lock; in a comment explain the
    exact interleaving that oversells without it (and why the GIL does not
    prevent it). Also: all 8 threads replay the *same* order_id for SKU B ->
    every call returns True and only one hold exists.

    Required: correct under any interleaving; the test must be deterministic.

Part 4 - discussion (written answer, no code)
    "Now the flash sale runs on 200 app servers." Cover: the DB conditional
    update `UPDATE stock SET qty = qty - 1 WHERE sku = ? AND qty >= 1` and
    reading affected rows; Redis DECR (and the negative-result problem) vs a
    Lua script for check-and-decrement; queue-based throttling of buy
    requests; pre-warming stock into Redis and the CDN; accept-then-reject-
    at-payment (over-admit, hard check at payment); how the TTL hold maps to a
    Redis TTL / delayed message.
"""

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


class Inventory:
    """Parts 1-2: per-SKU stock with TTL holds, lazy expiry via a heap."""

    def __init__(self, ttl_sec: int, now: Callable[[], float]) -> None:
        pass

    def add_stock(self, sku: str, qty: int) -> None:
        pass

    def available(self, sku: str) -> int:
        pass

    def reserve(self, sku: str, qty: int, order_id: str) -> bool:
        pass

    def reserve_many(self, items: Dict[str, int], order_id: str) -> bool:
        pass

    def confirm(self, order_id: str) -> bool:
        pass

    def release(self, order_id: str) -> bool:
        pass


class ConcurrentInventory(Inventory):
    """Part 3: same API, safe to call from many threads."""

    def __init__(self, ttl_sec: int, now: Callable[[], float]) -> None:
        super().__init__(ttl_sec, now)


def check_invariants(inv: Inventory) -> None:
    """Test helper for Part 2: adapt the attribute names to your implementation."""
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
