from __future__ import annotations

"""Time-Based Key-Value Store -> Versioned Config Store -- REFERENCE

Timestamps are integers passed in explicitly (no wall clock). Values are
strings. "Latest value at time t" always means the value with the largest
timestamp <= t.

Part 1 - TimeMap (LC981)
    TimeMap() with set(key, value, ts) and get(key, ts) -> value with the
    largest ts' <= ts for that key, or "" if none. For a given key, set is
    called with strictly increasing ts.

    Example:
        m = TimeMap()
        m.set("price:sku1", "10", 1); m.set("price:sku1", "12", 5)
        m.get("price:sku1", 1) -> "10"; m.get("price:sku1", 4) -> "10"
        m.get("price:sku1", 5) -> "12"; m.get("price:sku1", 0) -> ""
        m.get("nope", 9)       -> ""

    Required: set O(1) amortized (append), get O(log n) (bisect).

Part 2 - out-of-order writes and windowed reads
    OrderedTimeMap: set may arrive with any ts (late events). Keep each key's
    history sorted (bisect.insort); if the same ts is written twice the later
    call wins. Add get_window(key, ts, w) -> latest value with ts' in
    [ts - w, ts], or "" if no value in that window.

    Example:
        o = OrderedTimeMap()
        o.set("k", "b", 5); o.set("k", "a", 1); o.set("k", "c", 9)
        o.get("k", 6)            -> "b"
        o.get_window("k", 6, 1)  -> ""        # nothing in [5, 6]? 5 is in it -> "b"
        (careful: [5, 6] contains ts 5, so the answer is "b"; use w = 0 for "")
        o.get_window("k", 6, 0)  -> ""
        o.get_window("k", 4, 3)  -> "a"
        o.set("k", "B", 5); o.get("k", 5) -> "B"

    Required: set O(n) worst case for the insert (say why that is acceptable
    for mostly-in-order data), get / get_window O(log n).

Part 3 - SnapshotArray (LC1146)
    SnapshotArray(length): all zeros. set(index, val); snap() -> snap_id
    (0, 1, 2, ...); get(index, snap_id) -> value of index at the time that
    snapshot was taken. Do NOT copy the array on snap.

    Example:
        s = SnapshotArray(3)
        s.set(0, 5); s.snap() -> 0; s.set(0, 6); s.get(0, 0) -> 5
        s.snap() -> 1; s.get(0, 1) -> 6; s.get(2, 1) -> 0

    Required: set O(1) amortized, snap O(1), get O(log #writes to that index).

Part 4 - versioned config store
    VersionedStore(): put(key, value) -> new global version (1, 2, 3, ...);
    delete(key) -> new version (a tombstone); get(key, version=None) -> value
    as of that version (latest put/delete with version' <= version) or None;
    `version` property = current version; diff(v1, v2) -> {key: (old, new)}
    for every key whose value differs between the two versions (None for
    absent). Each put/delete creates exactly one version.

    Example:
        v = VersionedStore()
        v.put("a", "1") -> 1; v.put("b", "2") -> 2; v.put("a", "3") -> 3
        v.delete("b")   -> 4
        v.get("a", 2) -> "1"; v.get("a") -> "3"; v.get("b", 3) -> "2"
        v.get("b", 4) -> None
        v.diff(1, 4) -> {"a": ("1", "3")}
        v.diff(0, 2) -> {"a": (None, "1"), "b": (None, "2")}

    Required: put/delete O(1) amortized; get O(log H) with H = versions of
    that key; diff O((v2 - v1) log H) via a global log of (version, key).

Part 5 - discussion (written answer, no code)
    Explain how this is exactly MVCC (multi-version concurrency control) in
    Postgres / InnoDB: every row version carries the transaction id that
    created it; a reader with snapshot S sees the latest version <= S without
    locks; writers append new versions. What are the costs (old versions pile
    up -> VACUUM / purge, i.e. compaction), how does an append-only history
    get compacted (drop versions older than the oldest active snapshot, keep
    the latest), and what does "read your own writes" look like here?
"""

import bisect
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Part 1
# DATA SHAPE: Dict[key, (List[int] timestamps, List[str] values)] parallel
#             lists so bisect can search the ints.
# INVARIANT:  timestamps strictly increasing per key.
# COMPLEXITY: set O(1) amortized; get O(log n).
# PITFALL:    bisect_right(ts) - 1 gives the last ts' <= ts; index -1 means
#             "nothing yet" -> "". Don't bisect a list of tuples with a
#             sentinel value; keep the parallel lists.
# ---------------------------------------------------------------------------
class TimeMap:
    def __init__(self) -> None:
        self.ts: Dict[str, List[int]] = {}
        self.vals: Dict[str, List[str]] = {}

    def set(self, key: str, value: str, ts: int) -> None:
        self.ts.setdefault(key, []).append(ts)
        self.vals.setdefault(key, []).append(value)

    def get(self, key: str, ts: int) -> str:
        t = self.ts.get(key)
        if not t:
            return ""
        i = bisect.bisect_right(t, ts) - 1
        return self.vals[key][i] if i >= 0 else ""


# ---------------------------------------------------------------------------
# Part 2
# DATA SHAPE: same parallel lists; set inserts at bisect_right position (or
#             overwrites when the ts already exists).
# COMPLEXITY: set O(log n) search + O(n) list shift (memmove, fast; for
#             mostly in-order data the shift is ~0). get_window: bisect for
#             the last ts' <= ts, then check ts' >= ts - w.
# PITFALL:    overwrite check: the element at i-1 has the same ts.
# ---------------------------------------------------------------------------
class OrderedTimeMap(TimeMap):
    def set(self, key: str, value: str, ts: int) -> None:
        t = self.ts.setdefault(key, [])
        v = self.vals.setdefault(key, [])
        i = bisect.bisect_right(t, ts)
        if i > 0 and t[i - 1] == ts:
            v[i - 1] = value                      # same ts: later write wins
        else:
            t.insert(i, ts)
            v.insert(i, value)

    def get_window(self, key: str, ts: int, w: int) -> str:
        t = self.ts.get(key)
        if not t:
            return ""
        i = bisect.bisect_right(t, ts) - 1
        if i < 0 or t[i] < ts - w:
            return ""
        return self.vals[key][i]


# ---------------------------------------------------------------------------
# Part 3
# DATA SHAPE: hist: List[List[Tuple[int, int]]]: per index a list of
#             (snap_id, value) pairs, snap_id non-decreasing; cur_snap: int.
#             Each index starts as [(0, 0)] so get always finds something.
# INVARIANT:  the last pair of an index has snap_id <= cur_snap; a set within
#             the same snapshot overwrites the last pair instead of appending.
# COMPLEXITY: set O(1) amortized, snap O(1), get O(log writes to index).
# PITFALL:    get(index, sid) must find the last pair with snap_id <= sid,
#             not == sid (the index may not have been written in that snap).
# ---------------------------------------------------------------------------
class SnapshotArray:
    def __init__(self, length: int) -> None:
        self.hist: List[List[Tuple[int, int]]] = [[(0, 0)] for _ in range(length)]
        self.cur = 0

    def set(self, index: int, val: int) -> None:
        h = self.hist[index]
        if h[-1][0] == self.cur:
            h[-1] = (self.cur, val)
        else:
            h.append((self.cur, val))

    def snap(self) -> int:
        self.cur += 1
        return self.cur - 1

    def get(self, index: int, snap_id: int) -> int:
        h = self.hist[index]
        i = bisect.bisect_right(h, (snap_id, float("inf"))) - 1
        return h[i][1]


# ---------------------------------------------------------------------------
# Part 4
# DATA SHAPE: per key: parallel lists versions[key], values[key] (None =
#             tombstone); log: List[Tuple[int, str]] = (version, key) in
#             version order; version counter.
# COMPLEXITY: put/delete O(1); get O(log H); diff O((v2 - v1) log H).
# PITFALL:    diff must dedupe keys touched several times in (v1, v2] and drop
#             keys whose value is the same at both ends (a put then a revert).
#             A tombstone is stored as None, so get returns None for deleted.
# ---------------------------------------------------------------------------
class VersionedStore:
    def __init__(self) -> None:
        self._versions: Dict[str, List[int]] = {}
        self._values: Dict[str, List[Optional[str]]] = {}
        self._log: List[Tuple[int, str]] = []
        self._version = 0

    @property
    def version(self) -> int:
        return self._version

    def _append(self, key: str, value: Optional[str]) -> int:
        self._version += 1
        self._versions.setdefault(key, []).append(self._version)
        self._values.setdefault(key, []).append(value)
        self._log.append((self._version, key))
        return self._version

    def put(self, key: str, value: str) -> int:
        return self._append(key, value)

    def delete(self, key: str) -> int:
        return self._append(key, None)

    def get(self, key: str, version: Optional[int] = None) -> Optional[str]:
        vs = self._versions.get(key)
        if not vs:
            return None
        if version is None:
            version = self._version
        i = bisect.bisect_right(vs, version) - 1
        return self._values[key][i] if i >= 0 else None

    def diff(self, v1: int, v2: int) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        if v1 > v2:
            v1, v2 = v2, v1
        lo = bisect.bisect_right(self._log, (v1, "￿"))
        hi = bisect.bisect_right(self._log, (v2, "￿"))
        touched = {key for _, key in self._log[lo:hi]}
        out: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        for key in sorted(touched):
            old, new = self.get(key, v1), self.get(key, v2)
            if old != new:
                out[key] = (old, new)
        return out


# ---------------------------------------------------------------------------
# Part 5 - model answer
# MVCC: a row is a chain of versions, each stamped with the creating
#   transaction id (xmin) and, when superseded, the deleting one (xmax).
#   A transaction takes a snapshot (a version number + the set of in-flight
#   txids); a read returns the newest version whose creator committed before
#   the snapshot: exactly VersionedStore.get(key, version). Readers never
#   block writers and vice versa; writers append a new version instead of
#   updating in place (Postgres) or keep the old version in an undo log
#   (InnoDB, Oracle).
# Costs: dead versions accumulate. Postgres VACUUM / InnoDB purge remove
#   versions no active snapshot can see. Compaction of an append-only
#   history: let S = the oldest snapshot still in use; for each key keep the
#   newest version <= S plus everything after S, drop the rest; if the kept
#   version is a tombstone and nothing newer exists drop the key. Same idea in
#   LSM trees (RocksDB compaction) and Kafka log compaction (keep last per key).
# Read your own writes: a transaction sees versions written by itself even
#   though they are not committed: the snapshot rule is "committed before my
#   snapshot OR written by me". In our store, a session that did put -> v=7
#   must read with version >= 7; read replicas that lag behind would show
#   the old value, so route the user to the primary (or wait for the
#   replica to reach v7) for a few seconds after a write.
# Long-lived snapshots (a report running for an hour) block cleanup and are
#   the classic cause of table bloat; likewise here memory grows until the
#   oldest reader finishes.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # Part 1
    m = TimeMap()
    m.set("price:sku1", "10", 1); m.set("price:sku1", "12", 5)
    assert m.get("price:sku1", 1) == "10"
    assert m.get("price:sku1", 4) == "10"
    assert m.get("price:sku1", 5) == "12"
    assert m.get("price:sku1", 100) == "12"
    assert m.get("price:sku1", 0) == ""
    assert m.get("nope", 9) == ""
    for i in range(1000):
        m.set("k", str(i), i * 2)
    assert m.get("k", 999) == "499" and m.get("k", 1998) == "999"

    # Part 2
    o = OrderedTimeMap()
    o.set("k", "b", 5); o.set("k", "a", 1); o.set("k", "c", 9)
    assert o.ts["k"] == [1, 5, 9]
    assert o.get("k", 6) == "b" and o.get("k", 0) == "" and o.get("k", 9) == "c"
    assert o.get_window("k", 6, 1) == "b"
    assert o.get_window("k", 6, 0) == ""
    assert o.get_window("k", 5, 0) == "b"
    assert o.get_window("k", 4, 3) == "a"
    assert o.get_window("k", 4, 2) == ""
    assert o.get_window("zzz", 4, 2) == ""
    o.set("k", "B", 5)
    assert o.get("k", 5) == "B" and o.ts["k"] == [1, 5, 9]

    # Part 3
    s = SnapshotArray(3)
    s.set(0, 5)
    assert s.snap() == 0
    s.set(0, 6)
    assert s.get(0, 0) == 5
    assert s.snap() == 1
    assert s.get(0, 1) == 6 and s.get(2, 1) == 0 and s.get(0, 0) == 5
    s.set(1, 7); s.set(1, 8)              # two sets in the same snapshot
    assert s.snap() == 2
    assert s.get(1, 2) == 8 and s.get(1, 1) == 0
    assert len(s.hist[1]) == 2
    assert s.snap() == 3 and s.get(1, 3) == 8       # no writes in snap 3

    # Part 4
    v = VersionedStore()
    assert v.version == 0 and v.get("a") is None
    assert v.put("a", "1") == 1
    assert v.put("b", "2") == 2
    assert v.put("a", "3") == 3
    assert v.delete("b") == 4
    assert v.version == 4
    assert v.get("a", 2) == "1" and v.get("a") == "3" and v.get("a", 0) is None
    assert v.get("b", 3) == "2" and v.get("b", 4) is None and v.get("b") is None
    assert v.diff(1, 4) == {"a": ("1", "3")}
    assert v.diff(0, 2) == {"a": (None, "1"), "b": (None, "2")}
    assert v.diff(2, 4) == {"a": ("1", "3"), "b": ("2", None)}
    assert v.diff(4, 1) == v.diff(1, 4)
    assert v.diff(3, 3) == {}
    assert v.put("a", "1") == 5
    assert v.diff(1, 5) == {}                     # put then revert: no diff
    assert v.put("b", "9") == 6 and v.get("b") == "9"
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Part 1 memory keeps growing; how do you bound it?
#    A: Keep only the last K versions per key (deque) or versions newer than
#       now - retention; on read, ts older than the oldest kept -> "".
#       Compaction is the same "oldest reader" rule as MVCC.
# Q: Why bisect_right and not bisect_left for "latest <= ts"?
#    A: bisect_right returns the index after any element == ts, so index-1
#       is the last element <= ts; bisect_left would miss an exact match.
# Q: SnapshotArray with 10^9 indices?
#    A: Store hist in a dict only for indices that were ever written; unset
#       indices return 0 without allocating.
# Q: Versioned store on disk / multiple servers?
#    A: The log is a write-ahead log; replicate it (Raft) and replay it to
#       rebuild the per-key indexes; version = log offset. This is etcd's
#       revision model (get with rev, watch since rev, compact).
# Q: diff(v1, v2) when v2 - v1 is huge (millions of versions)?
#    A: Keep periodic full snapshots of the key -> version map; diff two
#       nearest snapshots' maps plus replay the log tails. Or store per-key
#       last-changed pointers so unchanged keys are skipped.
