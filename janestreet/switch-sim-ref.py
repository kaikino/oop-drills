"""Reference solution: learning L2 switch simulator.  See switch-sim.py for the prompt."""
from __future__ import annotations

import hashlib
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, FrozenSet, List, Optional, Tuple, Union

BROADCAST = "ff:ff:ff:ff:ff:ff"
Clock = Callable[[], float]


def _is_flood_dst(mac: str) -> bool:
    """Broadcast, or any group address (low bit of first octet set) is flooded."""
    if mac == BROADCAST:
        return True
    return bool(int(mac.split(":")[0], 16) & 1)


# ---------------------------------------------------------------------------
# Part 2: aged, bounded MAC table.
# Data shape: OrderedDict[key -> (port, last_seen)].  The dict is kept ordered by
# last_seen (refresh = move_to_end), so the FRONT is always the oldest entry.
# That single invariant gives both O(1) LRU eviction and cheap expiry sweeps.
# key is a str (mac) for the plain switch and a (vlan, mac) tuple for VLAN mode.
# ---------------------------------------------------------------------------
class MacTable:
    def __init__(self, now: Clock, age: float = 300.0, max_entries: Optional[int] = None) -> None:
        self._now = now
        self.age = age
        self.max_entries = max_entries
        self._entries: "OrderedDict[object, Tuple[str, float]]" = OrderedDict()

    def _expire(self) -> None:
        t = self._now()
        while self._entries:
            _, (_, seen) = next(iter(self._entries.items()))
            if t - seen > self.age:
                self._entries.popitem(last=False)
            else:
                break  # everything after the front is newer

    def learn(self, key: object, port: str) -> Optional[str]:
        """Record key on port.  Returns the previous port if the entry moved."""
        self._expire()
        t = self._now()
        prev: Optional[str] = None
        if key in self._entries:
            prev = self._entries[key][0]
            self._entries[key] = (port, t)
            self._entries.move_to_end(key)  # refresh
        else:
            if self.max_entries is not None and len(self._entries) >= self.max_entries:
                self._entries.popitem(last=False)  # evict oldest
            self._entries[key] = (port, t)
        return prev if prev is not None and prev != port else None

    def lookup(self, key: object) -> Optional[str]:
        self._expire()
        entry = self._entries.get(key)
        return entry[0] if entry else None

    def __len__(self) -> int:
        self._expire()
        return len(self._entries)


# ---------------------------------------------------------------------------
# Part 1 + 2 + 5: plain learning switch.
# Data shape: ports (list of names), a MacTable keyed by mac, an optional flap
# detector, and a list of alarm strings raised so far.
# Complexity: receive is O(1) amortised for unicast, O(P) for floods.
# ---------------------------------------------------------------------------
class Switch:
    def __init__(
        self,
        ports: List[str],
        now: Optional[Clock] = None,
        age: float = 300.0,
        max_entries: Optional[int] = None,
        flap_detector: Optional["MacFlapDetector"] = None,
    ) -> None:
        self.ports = list(ports)
        self.table = MacTable(now or (lambda: 0.0), age, max_entries)
        self.flap_detector = flap_detector
        self.alarms: List[str] = []

    def receive(self, port: str, src_mac: str, dst_mac: str) -> List[str]:
        if port not in self.ports:
            raise ValueError(f"unknown port {port}")
        self.table.learn(src_mac, port)
        if self.flap_detector is not None:
            alarm = self.flap_detector.observe(src_mac, port)
            if alarm:
                self.alarms.append(alarm)
        if _is_flood_dst(dst_mac):
            return self._flood(port)
        out = self.table.lookup(dst_mac)
        if out is None:
            return self._flood(port)
        if out == port:
            return []  # destination is on the ingress segment: filter, don't echo
        return [out]

    def _flood(self, ingress: str) -> List[str]:
        return [p for p in self.ports if p != ingress]


# ---------------------------------------------------------------------------
# Part 3: VLAN-aware switch.
# Data shape: port name -> AccessPort(vlan) | TrunkPort(allowed).
# Learning key is (vlan, mac): the same MAC may legitimately live on different
# ports in different VLANs.  Egress tuples are (port, tag) with tag None on
# access ports (untagged) and the VLAN id on trunks.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AccessPort:
    vlan: int


@dataclass(frozen=True)
class TrunkPort:
    allowed: FrozenSet[int]


PortConfig = Union[AccessPort, TrunkPort]
Egress = Tuple[str, Optional[int]]


class VlanSwitch:
    def __init__(self, ports: Dict[str, PortConfig], now: Optional[Clock] = None, age: float = 300.0) -> None:
        self.ports = dict(ports)
        self.table = MacTable(now or (lambda: 0.0), age)

    def _ingress_vlan(self, port: str, tag: Optional[int]) -> Optional[int]:
        cfg = self.ports[port]
        if isinstance(cfg, AccessPort):
            return None if tag is not None else cfg.vlan  # tagged frame on access port: drop
        if tag is None or tag not in cfg.allowed:
            return None  # untagged on trunk (no native VLAN here) or disallowed VLAN: drop
        return tag

    def _carries(self, cfg: PortConfig, vlan: int) -> bool:
        return cfg.vlan == vlan if isinstance(cfg, AccessPort) else vlan in cfg.allowed

    def _egress(self, port: str, vlan: int) -> Egress:
        return (port, None) if isinstance(self.ports[port], AccessPort) else (port, vlan)

    def receive(self, port: str, src_mac: str, dst_mac: str, tag: Optional[int] = None) -> List[Egress]:
        vlan = self._ingress_vlan(port, tag)
        if vlan is None:
            return []
        self.table.learn((vlan, src_mac), port)
        if not _is_flood_dst(dst_mac):
            out = self.table.lookup((vlan, dst_mac))
            if out is not None:
                return [] if out == port else [self._egress(out, vlan)]
        return [self._egress(p, vlan) for p, cfg in self.ports.items() if p != port and self._carries(cfg, vlan)]


# ---------------------------------------------------------------------------
# Part 4: link aggregation with rendezvous (highest-random-weight) hashing.
# Data shape: ordered member list + set of members currently up.
# Each flow picks the up member with the highest hash(member, flow).  Removing
# a member only moves the flows that were on it (their max is gone; every other
# flow's argmax is unchanged) and restoring it puts them back exactly.
# Complexity: O(M) per selection; M is tiny (2-8 links).  A hash ring would give
# O(log M) but needs virtual nodes for balance; not worth it here.
# ---------------------------------------------------------------------------
FlowKey = Tuple[object, ...]


def flow_key(
    src_mac: str,
    dst_mac: str,
    src_ip: Optional[str] = None,
    dst_ip: Optional[str] = None,
    src_port: Optional[int] = None,
    dst_port: Optional[int] = None,
) -> FlowKey:
    return (src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port)


class Lag:
    def __init__(self, members: List[str]) -> None:
        self.members = list(members)
        self.up = set(members)

    @staticmethod
    def _weight(member: str, flow: FlowKey) -> int:
        # hashlib rather than hash(): stable across processes and seeds.
        digest = hashlib.sha1(f"{member}|{flow!r}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def select(self, flow: FlowKey) -> Optional[str]:
        if not self.up:
            return None
        return max(self.up, key=lambda m: self._weight(m, flow))

    def member_down(self, member: str) -> None:
        self.up.discard(member)

    def member_up(self, member: str) -> None:
        if member in self.members:
            self.up.add(member)


# ---------------------------------------------------------------------------
# Part 5: MAC flap detection.
# Data shape: mac -> last port; mac -> deque of move timestamps inside the window.
# A "move" is a learn on a different port than last time.  More than max_moves
# moves inside `window` seconds raises an alarm string (once per observation
# that crosses the line; a real system would also rate-limit the alarm).
# ---------------------------------------------------------------------------
class MacFlapDetector:
    def __init__(self, max_moves: int, window: float, now: Clock) -> None:
        self.max_moves = max_moves
        self.window = window
        self._now = now
        self._last_port: Dict[str, str] = {}
        self._moves: Dict[str, Deque[float]] = defaultdict(deque)

    def observe(self, mac: str, port: str) -> Optional[str]:
        t = self._now()
        prev = self._last_port.get(mac)
        self._last_port[mac] = port
        if prev is None or prev == port:
            return None
        moves = self._moves[mac]
        moves.append(t)
        while moves and t - moves[0] > self.window:
            moves.popleft()
        if len(moves) > self.max_moves:
            return f"MAC {mac} flapping: {len(moves)} moves in {self.window:g}s (latest {prev} -> {port})"
        return None


# ---------------------------------------------------------------------------
# Part 6 (discussion)
# * Broadcast storm: a physical loop with no STP means every flood is re-flooded
#   forever (Ethernet has no TTL); the MAC table thrashes too because the same
#   source is seen on several ports.  STP builds a loop-free tree by electing a
#   root bridge (lowest bridge priority, then lowest MAC), each switch picks its
#   least-cost root port, and redundant ports are blocked.  RSTP converges in
#   seconds instead of 30-50 s; BPDU guard / root guard protect the topology from
#   rogue switches.
# * Routed leaf-spine beats a big L2 domain: failure domain is one rack instead of
#   the building, ECMP uses every link (STP blocks half of them), no broadcast or
#   unknown-unicast flooding across the fabric, and troubleshooting uses
#   traceroute/BGP state rather than "which port is this MAC on".  Stretch L2 only
#   where you must (VXLAN/EVPN gives L2 semantics over a routed underlay).
# * A "MAC move" alarm usually means one of: a loop (moves are fast and constant,
#   many MACs), a duplicate host / misconfigured NIC teaming (same MAC, two real
#   places), or a legitimate VM migration or active/standby failover (one move,
#   then quiet).  Rate and number of MACs involved tell you which.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # ---- Part 1 -----------------------------------------------------------
    sw = Switch(["p1", "p2", "p3"])
    assert sw.receive("p1", "aa", "bb") == ["p2", "p3"]        # unknown dst: flood
    assert sw.receive("p2", "bb", "aa") == ["p1"]              # aa learned on p1
    assert sw.receive("p3", "cc", BROADCAST) == ["p1", "p2"]   # broadcast floods
    assert sw.receive("p1", "aa", "bb") == ["p2"]
    assert sw.receive("p1", "dd", "aa") == []                  # dst on ingress port: filtered
    try:
        sw.receive("p9", "aa", "bb")
        assert False
    except ValueError:
        pass

    # ---- Part 2 -----------------------------------------------------------
    t = {"now": 0.0}
    clock = lambda: t["now"]
    sw = Switch(["p1", "p2", "p3"], now=clock, age=300)
    sw.receive("p1", "aa", BROADCAST)
    t["now"] = 200
    assert sw.receive("p2", "bb", "aa") == ["p1"]
    t["now"] = 250
    sw.receive("p1", "aa", BROADCAST)                          # refresh aa
    t["now"] = 540
    assert sw.receive("p2", "bb", "aa") == ["p1"]              # 290s since refresh: still known
    t["now"] = 560
    assert sw.receive("p2", "bb", "aa") == ["p1", "p3"]        # 310s: expired, flood
    sw = Switch(["p1", "p2", "p3"], now=clock, max_entries=2)
    sw.receive("p1", "aa", BROADCAST)
    sw.receive("p2", "bb", BROADCAST)
    sw.receive("p3", "cc", BROADCAST)                          # evicts aa (oldest)
    assert len(sw.table) == 2
    assert sw.receive("p2", "bb", "aa") == ["p1", "p3"]
    assert sw.receive("p1", "aa", "cc") == ["p3"]

    # ---- Part 3 -----------------------------------------------------------
    vs = VlanSwitch({
        "e1": AccessPort(10), "e2": AccessPort(10), "e3": AccessPort(20),
        "t1": TrunkPort(frozenset({10, 20})), "t2": TrunkPort(frozenset({20})),
    })
    assert vs.receive("e1", "aa", "bb") == [("e2", None), ("t1", 10)]      # flood in vlan 10 only
    assert vs.receive("t1", "bb", "aa", tag=10) == [("e1", None)]           # learned aa in vlan 10
    assert vs.receive("e3", "cc", "aa") == [("t1", 20), ("t2", 20)]         # aa unknown in vlan 20
    assert vs.receive("t1", "aa", "cc", tag=20) == [("e3", None)]           # same mac, other vlan
    assert vs.receive("t2", "dd", "aa", tag=10) == []                       # vlan 10 not allowed on t2
    assert vs.receive("e1", "aa", "bb", tag=10) == []                       # tagged frame on access port
    assert vs.receive("e2", "ee", "aa") == [("e1", None)]

    # ---- Part 4 -----------------------------------------------------------
    lag = Lag(["m1", "m2", "m3", "m4"])
    flows = [flow_key(f"src{i}", f"dst{i % 7}", f"10.0.0.{i % 50}", "10.1.0.1", 10000 + i, 443) for i in range(400)]
    before = {f: lag.select(f) for f in flows}
    assert all(lag.select(f) == before[f] for f in flows)                    # deterministic
    counts = defaultdict(int)
    for m in before.values():
        counts[m] += 1
    assert all(counts[m] > 60 for m in lag.members), dict(counts)           # roughly balanced (100 expected)
    lag.member_down("m2")
    after = {f: lag.select(f) for f in flows}
    assert all(after[f] == before[f] for f in flows if before[f] != "m2")    # only m2's flows moved
    assert all(after[f] != "m2" for f in flows)
    lag.member_up("m2")
    assert all(lag.select(f) == before[f] for f in flows)                    # restored exactly
    for m in lag.members:
        lag.member_down(m)
    assert lag.select(flows[0]) is None

    # ---- Part 5 -----------------------------------------------------------
    t["now"] = 0.0
    det = MacFlapDetector(max_moves=3, window=10.0, now=clock)
    sw = Switch(["p1", "p2"], now=clock, flap_detector=det)
    for i in range(3):                                          # 3 moves in the window: quiet
        t["now"] = i
        sw.receive("p1" if i % 2 else "p2", "aa", BROADCAST)
    assert sw.alarms == []
    t["now"] = 3
    sw.receive("p2", "aa", BROADCAST)                            # 4th move: alarm
    assert len(sw.alarms) == 1 and "aa" in sw.alarms[0] and "4 moves" in sw.alarms[0]
    t["now"] = 100
    sw.receive("p1", "aa", BROADCAST)                            # old moves aged out of window
    assert len(sw.alarms) == 1
    sw.receive("p1", "aa", BROADCAST)                            # same port: not a move
    assert len(sw.alarms) == 1
    print("ok")

# ---------------------------------------------------------------------------
# INTERVIEWER FOLLOW-UPS
# Q: Your flood is O(P) per frame; a real switch has 48+ ports and 10M pps.  How?
# A: Hardware floods via a per-VLAN port bitmap; in software keep a precomputed
#    list per VLAN and copy-on-write when ports change.
# Q: Why key the VLAN table on (vlan, mac) and not just mac?
# A: Independent VLAN learning: one host (e.g. a router-on-a-stick) is legitimately
#    reachable in several VLANs on different ports; shared learning would flap.
# Q: What if two hosts really do share a MAC?
# A: The table flaps between ports; unicast alternates destinations, effectively
#    a loss for both.  That's exactly what the Part 5 detector surfaces.
# Q: Why rendezvous hashing rather than `hash(flow) % len(up)`?
# A: Modulo remaps almost every flow when membership changes (packet reordering
#    for TCP); rendezvous moves only the flows on the failed link.
# Q: Where does aging interact with eviction badly?
# A: Under a MAC-flood attack the table fills with garbage and evicts real hosts,
#    so all their traffic gets flooded; hence port-security limits per port.
# ---------------------------------------------------------------------------
