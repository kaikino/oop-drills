from __future__ import annotations

"""Weighted Round-Robin Seller Task Scheduler (ByteDance, Sept 2026) -- REFERENCE

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


# ---------------------------------------------------------------------------
# Part 1
# Data shape: list `order` of seller ids + integer cursor `i` = index of the
# NEXT seller to serve. Invariant: 0 <= i < len(order) whenever order is
# non-empty. Remove: if the removed index is before the cursor, shift the
# cursor left by one so it still points at the same seller; if the removed
# index is at/after the cursor nothing moves (and we wrap if we fell off).
# ---------------------------------------------------------------------------
class RoundRobin:
    def __init__(self, sellers: List[str]) -> None:
        self.order: List[str] = list(sellers)
        self.i = 0

    def next(self) -> str:
        if not self.order:
            raise IndexError("no sellers")
        s = self.order[self.i]
        self.i = (self.i + 1) % len(self.order)
        return s

    def add(self, seller: str) -> None:
        if seller in self.order:
            return
        self.order.append(seller)          # goes at the end of the cycle

    def remove(self, seller: str) -> None:
        idx = self.order.index(seller)     # O(n); a dict seller->idx would need
        self.order.pop(idx)                # re-indexing anyway on pop
        if idx < self.i:
            self.i -= 1
        if self.order and self.i >= len(self.order):
            self.i = 0


# ---------------------------------------------------------------------------
# Part 2
# Data shape: parallel lists `sellers`, `weights` (insertion order) + cursor
# `i` + `served` = how many times sellers[i] has been served in this pass.
# Invariant: 0 <= served < weights[i]. next: emit sellers[i], served += 1,
# advance when served hits the weight. O(1), no expanded schedule.
# Pitfall: after set_weight lowers weights[i] below `served`, clamp/advance.
# ---------------------------------------------------------------------------
class WeightedRoundRobin:
    def __init__(self, weights: Dict[str, int]) -> None:
        self.sellers: List[str] = []
        self.weights: List[int] = []
        for s, w in weights.items():
            if w > 0:
                self.sellers.append(s)
                self.weights.append(w)
        self.i = 0
        self.served = 0

    def next(self) -> str:
        if not self.sellers:
            raise IndexError("no sellers")
        s = self.sellers[self.i]
        self.served += 1
        if self.served >= self.weights[self.i]:
            self.served = 0
            self.i = (self.i + 1) % len(self.sellers)
        return s

    def set_weight(self, seller: str, w: int) -> None:
        if seller in self.sellers:
            idx = self.sellers.index(seller)
            if w <= 0:
                self.sellers.pop(idx)
                self.weights.pop(idx)
                if idx < self.i:
                    self.i -= 1
                elif idx == self.i:
                    self.served = 0
                if self.sellers and self.i >= len(self.sellers):
                    self.i = 0
            else:
                self.weights[idx] = w
                if idx == self.i and self.served >= w:
                    self.served = 0
                    self.i = (self.i + 1) % len(self.sellers)
        elif w > 0:
            self.sellers.append(seller)
            self.weights.append(w)


# ---------------------------------------------------------------------------
# Part 3
# Data shape: dict seller -> [weight, current] (insertion-ordered dict gives
# deterministic tie-breaking: first inserted wins). total = sum of weights.
# Invariant (nginx): sum of all current weights is 0 after every pick, and
# every current weight stays within (-total, total). Over any window of
# `total` picks each seller is chosen exactly `weight` times.
# Complexity: O(n) per pick (must touch every seller). Fine for n ~ 10^3
# sellers; for 10^6 you would shard sellers across dispatchers (Part 5).
# ---------------------------------------------------------------------------
class SmoothWeightedRoundRobin:
    def __init__(self, weights: Dict[str, int]) -> None:
        self.state: Dict[str, List[int]] = {s: [w, 0] for s, w in weights.items() if w > 0}

    def next(self) -> str:
        if not self.state:
            raise IndexError("no sellers")
        total = 0
        best: Optional[str] = None
        for s, st in self.state.items():
            st[1] += st[0]
            total += st[0]
            if best is None or st[1] > self.state[best][1]:   # strict > keeps first on ties
                best = s
        self.state[best][1] -= total
        return best

    def set_weight(self, seller: str, w: int) -> None:
        if w <= 0:
            self.state.pop(seller, None)
        elif seller in self.state:
            self.state[seller][0] = w
        else:
            self.state[seller] = [w, 0]


# ---------------------------------------------------------------------------
# Part 4
# Data shape: queues: dict seller -> deque of tasks; state: dict seller ->
# [weight, current]. dispatch runs one smooth-WRR step over the ELIGIBLE
# sellers only (non-empty queue), with total = sum of eligible weights, exactly
# like nginx skipping "down" peers. Current weights of ineligible sellers are
# left untouched, so a seller that was owed service keeps its credit.
# ---------------------------------------------------------------------------
class TaskDispatcher:
    def __init__(self, weights: Dict[str, int]) -> None:
        self.state: Dict[str, List[int]] = {s: [w, 0] for s, w in weights.items() if w > 0}
        self.queues: Dict[str, Deque[object]] = {s: deque() for s in self.state}

    def submit(self, seller: str, task: object) -> None:
        if seller not in self.state:
            raise KeyError(seller)
        self.queues[seller].append(task)

    def dispatch(self) -> Optional[object]:
        total = 0
        best: Optional[str] = None
        for s, st in self.state.items():
            if not self.queues[s]:
                continue
            st[1] += st[0]
            total += st[0]
            if best is None or st[1] > self.state[best][1]:
                best = s
        if best is None:
            return None
        self.state[best][1] -= total
        return self.queues[best].popleft()


# ---------------------------------------------------------------------------
# Part 5 - model answer
# (a) Smooth WRR and classic WRR both guarantee every seller with weight >= 1
#     is served at least once per `total` picks: no starvation, bounded delay
#     of `total` picks. A strict priority queue (always serve the highest tier)
#     starves low tiers under sustained load; WRR is "proportional share", not
#     priority. Smooth WRR additionally bounds burstiness: a seller is never
#     served more than ceil(weight/total * k) + 1 times in any k picks.
# (b) Weights from SLA tiers are static config; dynamic weights (queue depth,
#     error rate) turn WRR into a feedback loop. Changing weights every tick
#     breaks the "exactly weight times per cycle" invariant and can oscillate;
#     damp them (change at most every N seconds, clamp to [1, max]).
# (c) Each dispatcher instance running its own smooth WRR gives correct
#     proportions in expectation and exact proportions per instance, so the
#     global mix is right as long as the load is spread evenly. For strict
#     global fairness: partition sellers across instances by consistent hash
#     (each seller has one owner, no shared state), or keep the current
#     weights in Redis and pick with a Lua script (one round trip per pick,
#     single point of contention). Partitioning is the usual answer.
# ---------------------------------------------------------------------------


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


# INTERVIEWER FOLLOW-UPS
# Q: Why does smooth WRR give the same counts per cycle as classic WRR?
# A: Sum of currents is invariant (0) and each pick subtracts `total`; after
#    `total` picks every seller has been added weight*total and must have been
#    subtracted total*weight times -> exactly `weight` picks each.
# Q: Make next() O(log n) for smooth WRR?
# A: Not directly (every current changes each tick). Trick: store
#    current - k*weight lazily, i.e. keep a global tick k and compare
#    base[s] + k*weight[s]; then the max is over lines, needs a kinetic heap.
#    In practice: shard sellers, n is small per shard.
# Q: A seller is removed while it has queued tasks - what happens to them?
# A: Decide explicitly: drain them (keep serving until empty, then drop the
#    seller) or reassign; never silently lose tasks.
# Q: Sellers have equal weight but very different task durations?
# A: WRR counts picks, not work. Weight by expected cost, or switch to
#    deficit round robin (DRR): each seller gets `quantum` credits per round
#    and pays task cost from its deficit counter.
# Q: How would you test the scheduler without flakiness?
# A: Pure functions of call order (no clock, no randomness); assert exact
#    sequences and the per-cycle count invariant.
