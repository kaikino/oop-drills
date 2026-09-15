from __future__ import annotations

"""Consistent Hashing (cache / shard routing for a fleet of Redis nodes)

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
    """Deterministic 32-bit hash: first 4 bytes of md5 (tests rely on this)."""
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:4], "big")


class HashRing:
    """Parts 1-2: sorted list of points + dict point -> node. Tests read
    self.points (sorted list) and self.owner (point -> node)."""

    def __init__(self, replicas: int = 1) -> None:
        self.replicas = replicas
        self.points: List[int] = []
        self.owner: Dict[int, str] = {}

    def add_node(self, node: str) -> None:
        pass

    def remove_node(self, node: str) -> None:
        pass

    def get_node(self, key: str) -> Optional[str]:
        pass


def distribution(ring: object, keys: List[str]) -> Dict[str, int]:
    """Part 2 helper: node -> number of keys it owns."""
    pass


def coefficient_of_variation(counts: Dict[str, int]) -> float:
    """std / mean of the counts (population std)."""
    pass


class RendezvousHash:
    """Part 4: highest-random-weight hashing; O(N) lookup."""

    def __init__(self) -> None:
        pass

    def add_node(self, node: str) -> None:
        pass

    def remove_node(self, node: str) -> None:
        pass

    def get_node(self, key: str) -> Optional[str]:
        pass


def moved_fraction(ring: object, keys: List[str], node: str) -> float:
    """Part 3 helper: snapshot owners, remove `node`, return the fraction of
    keys whose owner changed; assert no key of a surviving node moved."""
    pass


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
