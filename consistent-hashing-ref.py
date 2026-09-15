from __future__ import annotations

"""Consistent Hashing (cache / shard routing for a fleet of Redis nodes) -- REFERENCE

You are routing keys (product ids, cart ids) to a set of cache nodes. Nodes are
added and removed while the system runs, and we want as few keys as possible to
change owner when that happens. Everything must be deterministic: hash with
hashlib.md5 (first 4 bytes, big endian) or zlib.crc32 so tests are repeatable.

Part 1 - the ring
    HashRing() with add_node(node), remove_node(node), get_node(key) -> Optional[str].
    Each node is hashed to one point on a ring of size 2^32. A key is owned by
    the first node point clockwise from hash(key) (wrapping around to the
    smallest point). get_node on an empty ring returns None.

    Example:
        r = HashRing()
        r.add_node("a"); r.add_node("b"); r.add_node("c")
        r.get_node("cart:42") -> some node, always the same one for the same key
        r.remove_node(owner)  -> keys owned by other nodes do not move

    Required: get_node O(log P) with P = number of points (bisect on a sorted
    list); add/remove O(P) (list insert/delete) is fine.

Part 2 - virtual nodes
    HashRing(replicas=R) places R points per node: hash(f"{node}#{i}"). With
    one point per node, 10 nodes can own wildly different arc lengths; with
    R ~ 100-200 the load evens out. Write a helper distribution(ring, keys)
    -> {node: count} and show, with 10 nodes and 20_000 keys, that the
    coefficient of variation (std / mean) of the counts is far smaller with
    replicas=150 than with replicas=1.

    Required: same complexities; P = nodes * R.

Part 3 - what moves when a node leaves
    With N nodes, removing one must reassign only the keys that node owned:
    about 1/N of all keys, and no key owned by a surviving node may change
    owner. Write a test that checks both (fraction within a tolerance, the
    second property exactly).

Part 4 - rendezvous (highest random weight) hashing
    RendezvousHash() with the same API but no ring: get_node(key) returns the
    node maximizing hash(f"{node}|{key}"). O(N) per lookup, no virtual nodes
    needed, perfectly even in expectation, and removing a node moves exactly
    its keys. Implement it and run the Part 3 check against it.

    Example:
        h = RendezvousHash(); h.add_node("a"); h.add_node("b")
        h.get_node("k") -> "a" or "b", deterministic

Part 5 - discussion (written answer, no code)
    (a) Why is mod-N sharding (node = hash(key) % N) bad when N changes? How
        many keys move going from N to N+1?
    (b) Hot keys: a viral product id hashes to one node regardless of the
        scheme. What do you do? (Replicate the key to K nodes and pick one
        randomly on read; local in-process cache; "bounded loads" variant that
        skips a node at > c * average load and walks clockwise.)
    (c) Ring vs rendezvous: when would you choose each? (Ring: O(log P) with
        thousands of nodes, natural "next node" for replication. Rendezvous:
        small N, simplest code, no virtual nodes, weighted variant is easy.)
"""

import bisect
import hashlib
from typing import Dict, List, Optional


def _hash(s: str) -> int:
    """Deterministic 32-bit hash: first 4 bytes of md5."""
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:4], "big")


# ---------------------------------------------------------------------------
# Part 1 + 2
# DATA SHAPE: points: sorted List[int] of ring positions;
#             owner: Dict[int, str] point -> node; replicas per node.
# INVARIANT:  points is sorted and every point is a key in owner; each node
#             owns exactly `replicas` points (minus rare md5 collisions, which
#             we skip rather than overwrite).
# COMPLEXITY: get_node O(log P) via bisect_right; add/remove O(R log P + P)
#             for the list inserts; P = nodes * replicas.
# PITFALL:    wrap-around: bisect_right may return len(points) -> use index 0.
#             Removing a node must delete exactly its points, not "the point
#             at hash(node)" (that's only right for replicas == 1).
# ---------------------------------------------------------------------------
class HashRing:
    def __init__(self, replicas: int = 1) -> None:
        self.replicas = replicas
        self.points: List[int] = []
        self.owner: Dict[int, str] = {}

    def _points_of(self, node: str) -> List[int]:
        return [_hash(f"{node}#{i}") for i in range(self.replicas)]

    def add_node(self, node: str) -> None:
        for p in self._points_of(node):
            if p in self.owner:            # collision with an existing point
                continue
            self.owner[p] = node
            bisect.insort(self.points, p)

    def remove_node(self, node: str) -> None:
        for p in self._points_of(node):
            if self.owner.get(p) == node:
                del self.owner[p]
                i = bisect.bisect_left(self.points, p)
                del self.points[i]

    def get_node(self, key: str) -> Optional[str]:
        if not self.points:
            return None
        i = bisect.bisect_right(self.points, _hash(key))
        if i == len(self.points):
            i = 0                            # wrap around
        return self.owner[self.points[i]]


def distribution(ring: object, keys: List[str]) -> Dict[str, int]:
    """Part 2 helper: how many keys each node owns."""
    counts: Dict[str, int] = {}
    for k in keys:
        n = ring.get_node(k)                 # type: ignore[attr-defined]
        counts[n] = counts.get(n, 0) + 1
    return counts


def coefficient_of_variation(counts: Dict[str, int]) -> float:
    vals = list(counts.values())
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return var ** 0.5 / mean


# ---------------------------------------------------------------------------
# Part 4
# DATA SHAPE: a set of node ids. No positions to maintain.
# COMPLEXITY: get_node O(N) hashes; add/remove O(1).
# PITFALL:    tie-break deterministically (compare (score, node)) so two
#             processes with the same membership agree.
# ---------------------------------------------------------------------------
class RendezvousHash:
    def __init__(self) -> None:
        self.nodes: List[str] = []

    def add_node(self, node: str) -> None:
        if node not in self.nodes:
            self.nodes.append(node)

    def remove_node(self, node: str) -> None:
        self.nodes.remove(node)

    def get_node(self, key: str) -> Optional[str]:
        if not self.nodes:
            return None
        return max(self.nodes, key=lambda n: (_hash(f"{n}|{key}"), n))


def moved_fraction(ring: object, keys: List[str], node: str) -> float:
    """Part 3 helper: remove `node`, return the fraction of keys whose owner
    changed, asserting that only keys of `node` moved."""
    before = {k: ring.get_node(k) for k in keys}          # type: ignore[attr-defined]
    ring.remove_node(node)                                 # type: ignore[attr-defined]
    moved = 0
    for k in keys:
        after = ring.get_node(k)                           # type: ignore[attr-defined]
        if after != before[k]:
            assert before[k] == node, "a surviving node's key moved"
            moved += 1
    return moved / len(keys)


# ---------------------------------------------------------------------------
# Part 5 - model answer
# (a) hash % N: going N -> N+1 keeps a key in place only when
#     h % N == h % (N+1), which happens for roughly 1/(N+1) of keys, so about
#     N/(N+1) of all keys move (~91% for N=10). Every move is a cache miss and a
#     DB read; a fleet-wide resharding storm can take down the DB. Consistent
#     hashing moves ~1/N instead.
# (b) Hot keys: neither scheme helps, a single key maps to one node. Options:
#     - replicate the hot key to K nodes (key#0..key#K-1) and read a random
#       replica; writes fan out to K.
#     - short-TTL in-process (L1) cache in front of Redis for the top keys.
#     - consistent hashing with bounded loads (Google/Vimeo): cap each node at
#       c * average load (c ~ 1.25); if the owner is full walk clockwise to
#       the next node. Needs a load counter per node.
#     - detect hotness with a count-min sketch on the client, react per key.
# (c) Ring: O(log P) lookup, scales to thousands of nodes, and "next K points
#     clockwise" gives a natural replica set (Dynamo, Cassandra). Rendezvous:
#     O(N) per lookup so N should be small (tens), but the code is ~10 lines,
#     no virtual nodes to tune, and weighted nodes are trivial
#     (score = -w / ln(u) with u = hash mapped to (0,1)). For a client-side
#     cache router with 20 nodes I'd pick rendezvous; for a storage ring, ring.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    keys = [f"cart:{i}" for i in range(20_000)]

    # Part 1
    r = HashRing()
    assert r.get_node("x") is None
    for n in ("a", "b", "c"):
        r.add_node(n)
    owner = r.get_node("cart:42")
    assert owner in ("a", "b", "c")
    assert all(r.get_node("cart:42") == owner for _ in range(5))     # deterministic
    assert len(r.points) == 3 and sorted(r.points) == r.points
    # wrap-around: a key hashing past the last point goes to the first point
    big = next(k for k in keys if _hash(k) > r.points[-1])
    assert r.get_node(big) == r.owner[r.points[0]]
    small = next(k for k in keys if _hash(k) < r.points[0])
    assert r.get_node(small) == r.owner[r.points[0]]
    before = {k: r.get_node(k) for k in keys[:500]}
    r.remove_node(owner)
    assert len(r.points) == 2
    assert all(r.get_node(k) == v for k, v in before.items() if v != owner)
    r2 = HashRing()
    r2.add_node("only")
    assert r2.get_node("anything") == "only"
    r2.remove_node("only")
    assert r2.get_node("anything") is None

    # Part 2 - virtual nodes even out the load
    nodes = [f"node{i}" for i in range(10)]
    plain = HashRing(replicas=1)
    vnodes = HashRing(replicas=150)
    for n in nodes:
        plain.add_node(n); vnodes.add_node(n)
    assert len(vnodes.points) == 1500
    cv_plain = coefficient_of_variation(distribution(plain, keys))
    cv_v = coefficient_of_variation(distribution(vnodes, keys))
    assert cv_v < 0.15, cv_v
    assert cv_v < cv_plain / 2, (cv_plain, cv_v)
    assert sum(distribution(vnodes, keys).values()) == len(keys)

    # Part 3 - removal moves ~1/N of keys and only the removed node's keys
    frac = moved_fraction(vnodes, keys, "node3")
    assert 0.05 < frac < 0.16, frac
    assert "node3" not in set(vnodes.get_node(k) for k in keys)

    # Part 4 - rendezvous
    h = RendezvousHash()
    assert h.get_node("k") is None
    for n in nodes:
        h.add_node(n)
    assert h.get_node("k") in nodes and h.get_node("k") == h.get_node("k")
    assert coefficient_of_variation(distribution(h, keys)) < 0.1
    frac = moved_fraction(h, keys, "node7")
    assert 0.06 < frac < 0.14, frac
    assert "node7" not in set(h.get_node(k) for k in keys)
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Two nodes' virtual points collide - what happens?
#    A: With 32-bit md5 prefixes and 1500 points the chance is ~1500^2/2^33,
#       tiny but nonzero; we skip the colliding point (the node owns one fewer).
#       Using 64 bits or a full md5 compare removes the worry.
# Q: How do you pick the number of replicas?
#    A: Load std-dev shrinks ~ 1/sqrt(R); 100-200 gives ~5-10% variation with a
#       few dozen nodes. Memory is nodes*R points; 1000 nodes * 200 = 200k
#       ints, trivial.
# Q: Weighted nodes (a bigger box should get 2x keys)?
#    A: Ring: give it 2x the virtual points. Rendezvous: weighted score
#       -w / ln(u).
# Q: Replication: where does the 2nd copy of a key go?
#    A: Ring: next *distinct physical* node clockwise (skip points of the same
#       node). Rendezvous: the top-2 scoring nodes.
# Q: Clients disagree on membership (one saw the node leave, one did not)?
#    A: Brief double-writes / misses; routers need a membership source of
#       truth (ZooKeeper/etcd, gossip) and a version number on the ring so
#       stale routers can be detected.
