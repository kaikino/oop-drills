from __future__ import annotations

"""Weighted Round-Robin Seller Task Scheduler (ByteDance, Sept 2026)

We run one dispatcher that hands seller work (order syncs, price updates) to a
worker pool. Sellers are added and removed while it runs. No clock is needed
here: everything is a function of call order.

Part 1 - plain round robin with dynamic membership
    RoundRobin(sellers) with next() -> seller id, cycling in insertion order.
    add(seller) appends to the end of the cycle; remove(seller) drops it. Neither
    may disturb the position of the cycle: if we were about to serve C, we still
    serve C after A is removed.

    Example:
        rr = RoundRobin(["A", "B", "C"])
        rr.next() -> "A"; rr.next() -> "B"
        rr.remove("A")
        rr.next() -> "C"; rr.next() -> "B"       # cycle continues from C
        rr.add("D")
        rr.next() -> "C"; rr.next() -> "D"; rr.next() -> "B"

    Required: next O(1); add O(1); remove O(n) is acceptable (n = #sellers).
    next() on an empty scheduler raises IndexError.

Part 2 - classic (interleaved) weighted round robin
    WeightedRoundRobin(weights) where weights = {seller: positive int}. Each
    seller is served `weight` times per cycle, sellers in insertion order:
    {A:5, B:1, C:1} -> A A A A A B C A A A A A B C ...
    set_weight(seller, w) changes a weight (w == 0 removes the seller).

    Example:
        w = WeightedRoundRobin({"A": 5, "B": 1, "C": 1})
        [w.next() for _ in range(7)] -> ["A","A","A","A","A","B","C"]

    Required: next O(1); no expanded schedule list (weights can be 10^6).

Part 3 - smooth weighted round robin (nginx)
    The classic sequence bursts (AAAAA then BC). The nginx algorithm spreads it
    out. State: current_weight[s] starts at 0. next():
        for every s: current[s] += weight[s]
        pick the s with the largest current (first inserted wins ties)
        current[pick] -= total_weight
        return pick
    {A:5, B:1, C:1} must yield exactly: A A B A C A A, then repeats, and all
    current weights return to 0 at the end of each cycle of total_weight picks.
    The nginx docs example {A:4, B:2, C:1} yields A B A C A B A.

    Example:
        s = SmoothWeightedRoundRobin({"A": 5, "B": 1, "C": 1})
        [s.next() for _ in range(7)] -> ["A","A","B","A","C","A","A"]

    Required: next O(n) per pick. Say why it is O(n) and whether that matters.

Part 4 - dispatching queued tasks
    TaskDispatcher(weights): submit(seller, task) appends to that seller's FIFO
    queue; dispatch() -> Optional[task] picks a seller by smooth WRR considering
    ONLY sellers with a non-empty queue (total_weight = sum of their weights, as
    nginx does for "up" peers), pops the head of that queue and returns it.
    Returns None if every queue is empty. Tasks of one seller must be served in
    FIFO order.

    Example (weights A:5 B:1 C:1):
        d.submit("A","a1"); d.submit("A","a2"); d.submit("A","a3")
        d.submit("B","b1"); d.submit("B","b2"); d.submit("C","c1")
        [d.dispatch() for _ in range(7)]
            -> ["a1","a2","b1","a3","c1","b2",None]

    Required: submit O(1); dispatch O(n) in the number of sellers.

Part 5 - discussion (written answer, no code)
    (a) Fairness vs starvation: can a weight-1 seller starve under smooth WRR?
        Under classic WRR? Under a pure priority queue?
    (b) Where do weights come from: SLA tiers (e.g. platinum=8, gold=4, free=1),
        recent error rates, queue depth (dynamic weights) - and what breaks if
        you change weights every tick?
    (c) Multiple dispatcher instances: how do you keep global proportions when
        each instance runs its own WRR state? (Independent per-instance WRR is
        fine statistically; for strict global fairness you need a shared
        counter, e.g. Redis, or partition sellers across instances by hash.)
"""

from collections import deque
from typing import Deque, Dict, List, Optional


class RoundRobin:
    """Part 1: list + cursor; add/remove must not disturb the cycle position."""

    def __init__(self, sellers: List[str]) -> None:
        pass

    def next(self) -> str:
        pass

    def add(self, seller: str) -> None:
        pass

    def remove(self, seller: str) -> None:
        pass


class WeightedRoundRobin:
    """Part 2: classic WRR; O(1) next without an expanded schedule."""

    def __init__(self, weights: Dict[str, int]) -> None:
        pass

    def next(self) -> str:
        pass

    def set_weight(self, seller: str, w: int) -> None:
        pass


class SmoothWeightedRoundRobin:
    """Part 3: nginx smooth WRR; O(n) per pick."""

    def __init__(self, weights: Dict[str, int]) -> None:
        # keep self.state: seller -> [weight, current] so the tests can check the invariant
        pass

    def next(self) -> str:
        pass

    def set_weight(self, seller: str, w: int) -> None:
        pass


class TaskDispatcher:
    """Part 4: per-seller FIFO queues + smooth WRR over sellers with work."""

    def __init__(self, weights: Dict[str, int]) -> None:
        pass

    def submit(self, seller: str, task: object) -> None:
        pass

    def dispatch(self) -> Optional[object]:
        pass


if __name__ == "__main__":
    # Part 1
    rr = RoundRobin(["A", "B", "C"])
    assert rr.next() == "A" and rr.next() == "B"
    rr.remove("A")
    assert rr.next() == "C" and rr.next() == "B"
    rr.add("D")
    assert [rr.next() for _ in range(3)] == ["C", "D", "B"]
    rr.remove("B")          # cursor is at index 0 (C); nothing shifts
    assert [rr.next() for _ in range(3)] == ["C", "D", "C"]
    rr.remove("C"); rr.remove("D")
    try:
        rr.next(); assert False
    except IndexError:
        pass

    # Part 2
    w = WeightedRoundRobin({"A": 5, "B": 1, "C": 1})
    assert [w.next() for _ in range(7)] == ["A", "A", "A", "A", "A", "B", "C"]
    assert [w.next() for _ in range(7)] == ["A", "A", "A", "A", "A", "B", "C"]
    w.set_weight("A", 2)
    w.set_weight("B", 0)
    assert [w.next() for _ in range(6)] == ["A", "A", "C", "A", "A", "C"]

    # Part 3 - exact nginx sequence
    s = SmoothWeightedRoundRobin({"A": 5, "B": 1, "C": 1})
    assert [s.next() for _ in range(7)] == ["A", "A", "B", "A", "C", "A", "A"]
    assert all(st[1] == 0 for st in s.state.values())          # cycle invariant
    assert [s.next() for _ in range(7)] == ["A", "A", "B", "A", "C", "A", "A"]
    # nginx docs example: {A:4, B:2, C:1} -> A B A C A B A
    s1 = SmoothWeightedRoundRobin({"A": 4, "B": 2, "C": 1})
    assert [s1.next() for _ in range(7)] == ["A", "B", "A", "C", "A", "B", "A"]
    assert all(st[1] == 0 for st in s1.state.values())
    s2 = SmoothWeightedRoundRobin({"A": 1, "B": 2, "C": 3})
    seq = [s2.next() for _ in range(60)]
    assert seq.count("A") == 10 and seq.count("B") == 20 and seq.count("C") == 30
    # by hand: C(3) B(4) A(3 ties C, first inserted wins) C(6) B(4) C(6)
    assert seq[:6] == ["C", "B", "A", "C", "B", "C"]
    s2.set_weight("C", 0)
    assert [s2.next() for _ in range(3)] == ["B", "A", "B"]

    # Part 4
    d = TaskDispatcher({"A": 5, "B": 1, "C": 1})
    for t in ["a1", "a2", "a3"]:
        d.submit("A", t)
    d.submit("B", "b1"); d.submit("B", "b2"); d.submit("C", "c1")
    assert [d.dispatch() for _ in range(7)] == ["a1", "a2", "b1", "a3", "c1", "b2", None]
    d.submit("C", "c2"); d.submit("B", "b3")
    out = [d.dispatch(), d.dispatch(), d.dispatch()]
    assert sorted(x for x in out if x) == ["b3", "c2"] and out[2] is None
    print("ok")
