"""
packet-parse -- REFERENCE SOLUTION.

See packet-parse.py for the interviewer's problem statement. Same tests at the bottom.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_VLAN = 0x8100
PROTO_ICMP, PROTO_TCP, PROTO_UDP = 1, 6, 17

# Bit positions in the TCP flags word (low 9 bits of the offset/flags field).
TCP_FLAG_BITS: Dict[str, int] = {
    "FIN": 0x001, "SYN": 0x002, "RST": 0x004, "PSH": 0x008, "ACK": 0x010,
    "URG": 0x020, "ECE": 0x040, "CWR": 0x080, "NS": 0x100,
}

ETH_FMT, ETH_LEN = "!6s6sH", 14
IPV4_FMT, IPV4_MIN = "!BBHHHBBH4s4s", 20
TCP_FMT, TCP_MIN = "!HHIIHHHH", 20
UDP_FMT, UDP_LEN = "!HHHH", 8


def mac_to_str(b: bytes) -> str:
    return ":".join("%02x" % x for x in b)


def mac_to_bytes(s: str) -> bytes:
    return bytes(int(x, 16) for x in s.split(":"))


def ip_to_str(b: bytes) -> str:
    return ".".join(str(x) for x in b)


def ip_to_bytes(s: str) -> bytes:
    return bytes(int(x) for x in s.split("."))


# ---------------------------------------------------------------------------
# Part 1: Ethernet II (+ one 802.1Q tag)
# ---------------------------------------------------------------------------
# Data shape: parsed headers are frozen dataclasses holding decoded fields plus
# the remaining `payload` bytes, so layers chain: parse_tcp(parse_ipv4(eth.payload).payload).
# Pitfall: the VLAN tag sits BETWEEN src MAC and the real ethertype, so the
# ethertype you read at offset 12 may be 0x8100 and the real one is at 16.


@dataclass(frozen=True)
class EthernetFrame:
    dst: str
    src: str
    ethertype: int
    vlan: Optional[int]
    payload: bytes


def parse_ethernet(data: bytes) -> EthernetFrame:
    if len(data) < ETH_LEN:
        raise ValueError("frame too short: %d bytes" % len(data))
    dst, src, ethertype = struct.unpack(ETH_FMT, data[:ETH_LEN])
    offset = ETH_LEN
    vlan: Optional[int] = None
    if ethertype == ETHERTYPE_VLAN:
        if len(data) < ETH_LEN + 4:
            raise ValueError("truncated 802.1Q tag")
        tci, ethertype = struct.unpack("!HH", data[ETH_LEN:ETH_LEN + 4])
        vlan = tci & 0x0FFF  # low 12 bits = VID; top 3 = PCP, next = DEI
        offset += 4
    return EthernetFrame(mac_to_str(dst), mac_to_str(src), ethertype, vlan, data[offset:])


# ---------------------------------------------------------------------------
# Part 2: IPv4 header + checksum
# ---------------------------------------------------------------------------
# Ones'-complement checksum: sum 16-bit big-endian words, fold carries back in,
# invert. Verifying = checksum over the header INCLUDING the checksum field is 0
# (equivalently, 0xFFFF before inversion). Pitfall: odd-length input is padded
# with a zero byte on the right, not the left.


def ones_complement_checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


@dataclass(frozen=True)
class IPv4Header:
    version: int
    ihl: int                # header length in 32-bit words
    total_length: int
    identification: int
    df: bool
    mf: bool
    fragment_offset: int    # in 8-byte units
    ttl: int
    protocol: int
    checksum: int
    checksum_ok: bool
    src: str
    dst: str
    options_length: int
    payload: bytes


def parse_ipv4(data: bytes) -> IPv4Header:
    if len(data) < IPV4_MIN:
        raise ValueError("IPv4 header too short")
    (ver_ihl, _tos, total_length, ident, flags_frag, ttl, proto, csum,
     src, dst) = struct.unpack(IPV4_FMT, data[:IPV4_MIN])
    version, ihl = ver_ihl >> 4, ver_ihl & 0x0F
    if version != 4:
        raise ValueError("not IPv4 (version=%d)" % version)
    hlen = ihl * 4
    if ihl < 5 or len(data) < hlen or total_length < hlen:
        raise ValueError("bad IHL/total length")
    header = data[:hlen]
    return IPv4Header(
        version=version, ihl=ihl, total_length=total_length, identification=ident,
        df=bool(flags_frag & 0x4000), mf=bool(flags_frag & 0x2000),
        fragment_offset=flags_frag & 0x1FFF, ttl=ttl, protocol=proto, checksum=csum,
        checksum_ok=ones_complement_checksum(header) == 0,
        src=ip_to_str(src), dst=ip_to_str(dst), options_length=hlen - IPV4_MIN,
        payload=data[hlen:total_length],  # trim Ethernet padding
    )


# ---------------------------------------------------------------------------
# Part 3: TCP and UDP
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TCPHeader:
    sport: int
    dport: int
    seq: int
    ack: int
    data_offset: int        # in 32-bit words
    flags: Set[str]
    window: int
    options_length: int
    payload: bytes


def parse_tcp(data: bytes) -> TCPHeader:
    if len(data) < TCP_MIN:
        raise ValueError("TCP header too short")
    sport, dport, seq, ack, off_flags, window, _csum, _urg = struct.unpack(TCP_FMT, data[:TCP_MIN])
    data_offset = off_flags >> 12
    hlen = data_offset * 4
    if data_offset < 5 or len(data) < hlen:
        raise ValueError("bad TCP data offset")
    flags = {name for name, bit in TCP_FLAG_BITS.items() if off_flags & bit}
    return TCPHeader(sport, dport, seq, ack, data_offset, flags, window, hlen - TCP_MIN, data[hlen:])


@dataclass(frozen=True)
class UDPHeader:
    sport: int
    dport: int
    length: int
    checksum: int
    payload: bytes


def parse_udp(data: bytes) -> UDPHeader:
    if len(data) < UDP_LEN:
        raise ValueError("UDP header too short")
    sport, dport, length, csum = struct.unpack(UDP_FMT, data[:UDP_LEN])
    if length < UDP_LEN or len(data) < length:
        raise ValueError("bad UDP length")
    return UDPHeader(sport, dport, length, csum, data[UDP_LEN:length])


# ---------------------------------------------------------------------------
# Builders (used by the tests; also the natural inverse of the parsers)
# ---------------------------------------------------------------------------


def build_ethernet(dst: str, src: str, ethertype: int, payload: bytes,
                   vlan: Optional[int] = None) -> bytes:
    head = struct.pack("!6s6s", mac_to_bytes(dst), mac_to_bytes(src))
    if vlan is not None:
        head += struct.pack("!HH", ETHERTYPE_VLAN, vlan & 0x0FFF)
    return head + struct.pack("!H", ethertype) + payload


def build_ipv4(src: str, dst: str, proto: int, payload: bytes, ttl: int = 64,
               ident: int = 0, df: bool = False, mf: bool = False,
               frag_offset: int = 0, options: bytes = b"") -> bytes:
    if len(options) % 4:
        options += b"\x00" * (4 - len(options) % 4)
    ihl = 5 + len(options) // 4
    flags_frag = (0x4000 if df else 0) | (0x2000 if mf else 0) | (frag_offset & 0x1FFF)
    total = ihl * 4 + len(payload)

    def pack(csum: int) -> bytes:
        return struct.pack(IPV4_FMT, (4 << 4) | ihl, 0, total, ident, flags_frag, ttl,
                           proto, csum, ip_to_bytes(src), ip_to_bytes(dst)) + options

    return pack(ones_complement_checksum(pack(0))) + payload


def build_tcp(sport: int, dport: int, seq: int, ack: int, flags: Set[str],
              payload: bytes = b"", window: int = 65535, options: bytes = b"") -> bytes:
    if len(options) % 4:
        options += b"\x00" * (4 - len(options) % 4)
    data_offset = 5 + len(options) // 4
    flag_word = sum(TCP_FLAG_BITS[f] for f in flags)
    # Checksum left 0: it needs the IP pseudo-header; out of scope for parsing.
    return struct.pack(TCP_FMT, sport, dport, seq, ack, (data_offset << 12) | flag_word,
                       window, 0, 0) + options + payload


def build_udp(sport: int, dport: int, payload: bytes) -> bytes:
    return struct.pack(UDP_FMT, sport, dport, UDP_LEN + len(payload), 0) + payload


def fragment_ipv4(src: str, dst: str, proto: int, ident: int, payload: bytes,
                  chunk: int) -> List[bytes]:
    """Split `payload` into IPv4 fragments of `chunk` bytes (chunk % 8 == 0)."""
    assert chunk % 8 == 0
    frags = []
    for start in range(0, len(payload), chunk):
        piece = payload[start:start + chunk]
        last = start + chunk >= len(payload)
        frags.append(build_ipv4(src, dst, proto, piece, ident=ident, mf=not last,
                                frag_offset=start // 8))
    return frags


# ---------------------------------------------------------------------------
# Part 4: flows
# ---------------------------------------------------------------------------
# Data shape: FlowKey = (proto, (ip, port) low, (ip, port) high) -- canonical
# order so both directions map to the same flow. Per-direction state tracks the
# highest seq+len seen and the set of payload-carrying seqs seen.
#   retransmission : payload segment whose seq we have already seen with payload
#   out-of-order   : payload segment with seq < next expected that we have NOT
#                    seen (a later segment arrived first)
# Pitfall: from a passive tap, a retransmission of a segment that was lost
# upstream of the tap looks identical to an out-of-order arrival. Wireshark
# disambiguates with timing (RTO-ish delay => retransmission). We don't.

Endpoint = Tuple[str, int]
FlowKey = Tuple[int, Endpoint, Endpoint]


@dataclass
class _DirState:
    next_seq: Optional[int] = None
    seen: Set[int] = field(default_factory=set)


@dataclass
class FlowStats:
    packets: int = 0
    bytes: int = 0
    syn: bool = False
    fin: bool = False
    retransmissions: int = 0
    out_of_order: int = 0
    _dirs: Dict[Endpoint, _DirState] = field(default_factory=dict, repr=False, compare=False)


def flow_key(proto: int, a: Endpoint, b: Endpoint) -> FlowKey:
    return (proto, a, b) if a <= b else (proto, b, a)


class FlowTracker:
    def __init__(self) -> None:
        self._flows: Dict[FlowKey, FlowStats] = {}

    def add(self, frame: bytes) -> Optional[FlowKey]:
        eth = parse_ethernet(frame)
        if eth.ethertype != ETHERTYPE_IPV4:
            return None
        ip = parse_ipv4(eth.payload)
        if ip.fragment_offset or ip.mf:
            return None  # fragments have no L4 header (except the first); see Part 5
        if ip.protocol == PROTO_TCP:
            tcp = parse_tcp(ip.payload)
            src, dst = (ip.src, tcp.sport), (ip.dst, tcp.dport)
        elif ip.protocol == PROTO_UDP:
            udp = parse_udp(ip.payload)
            src, dst = (ip.src, udp.sport), (ip.dst, udp.dport)
        else:
            return None
        key = flow_key(ip.protocol, src, dst)
        st = self._flows.setdefault(key, FlowStats())
        st.packets += 1
        st.bytes += len(frame)
        if ip.protocol == PROTO_TCP:
            self._track_tcp(st, src, tcp)
        return key

    @staticmethod
    def _track_tcp(st: FlowStats, src: Endpoint, tcp: TCPHeader) -> None:
        st.syn = st.syn or "SYN" in tcp.flags
        st.fin = st.fin or "FIN" in tcp.flags
        if not tcp.payload:
            return
        d = st._dirs.setdefault(src, _DirState())
        if tcp.seq in d.seen:
            st.retransmissions += 1
        elif d.next_seq is not None and tcp.seq < d.next_seq:
            st.out_of_order += 1
        d.seen.add(tcp.seq)
        end = (tcp.seq + len(tcp.payload)) & 0xFFFFFFFF
        d.next_seq = end if d.next_seq is None else max(d.next_seq, end)

    def flows(self) -> Dict[FlowKey, FlowStats]:
        return self._flows


# ---------------------------------------------------------------------------
# Part 5: IPv4 reassembly
# ---------------------------------------------------------------------------
# Data shape: buffers keyed by (src, dst, id, proto). Each buffer maps byte
# offset -> fragment bytes, plus total length once the MF=0 fragment arrives.
# Complete when total is known and the sorted pieces tile [0, total) exactly.
# Real stacks also enforce a reassembly timeout (and a memory cap) -- fragments
# are a classic DoS vector -- and tolerate overlapping fragments by policy
# (first-wins vs last-wins differs across OSes; IDS evasion lives here).

FragKey = Tuple[str, str, int, int]


@dataclass
class _FragBuffer:
    pieces: Dict[int, bytes] = field(default_factory=dict)
    total: Optional[int] = None


class Reassembler:
    def __init__(self) -> None:
        self._buf: Dict[FragKey, _FragBuffer] = {}

    @staticmethod
    def key_of(ip: IPv4Header) -> FragKey:
        return (ip.src, ip.dst, ip.identification, ip.protocol)

    def add(self, ip: IPv4Header) -> Optional[bytes]:
        """Feed one IPv4 packet; return the full payload once complete."""
        if not ip.mf and ip.fragment_offset == 0:
            return ip.payload  # not fragmented at all
        key = self.key_of(ip)
        buf = self._buf.setdefault(key, _FragBuffer())
        offset = ip.fragment_offset * 8
        buf.pieces[offset] = ip.payload
        if not ip.mf:
            buf.total = offset + len(ip.payload)
        if buf.total is None or self.missing(key):
            return None
        data = b"".join(buf.pieces[off] for off in sorted(buf.pieces))
        del self._buf[key]
        return data

    def missing(self, key: FragKey) -> List[Tuple[int, Optional[int]]]:
        """Byte ranges [start, end) not yet received; end None = last fragment unseen."""
        buf = self._buf.get(key)
        if buf is None:
            return []
        gaps: List[Tuple[int, Optional[int]]] = []
        cursor = 0
        for off in sorted(buf.pieces):
            if off > cursor:
                gaps.append((cursor, off))
            cursor = max(cursor, off + len(buf.pieces[off]))
        if buf.total is None:
            gaps.append((cursor, None))
        elif cursor < buf.total:
            gaps.append((cursor, buf.total))
        return gaps


# ---------------------------------------------------------------------------
# Part 6: discussion
# ---------------------------------------------------------------------------
# pcap file format: a 24-byte global header (magic 0xa1b2c3d4 -- its byte order
# tells you the writer's endianness; version 2.4; timezone/sigfigs (unused);
# snaplen; link-layer type e.g. 1 = Ethernet). Then per packet a 16-byte record
# header: ts_sec, ts_usec (or nsec with magic 0xa1b23c4d), incl_len (captured
# bytes), orig_len (on the wire). incl_len < orig_len means truncated by snaplen.
# pcapng adds interface blocks, per-interface timestamps, comments.
#
# BPF: a tiny register VM in the kernel; tcpdump compiles "tcp port 443 and host
# 10.0.0.1" into it so filtering happens before the copy to userspace. Cheap to
# run per packet, verified to terminate (no backward jumps). eBPF generalises it.
#
# "Connection hangs after handshake": the 3-way handshake is tiny packets; the
# first data segment is full-MTU. If a link in the path has a smaller MTU
# (tunnel/VPN/PPPoE adds overhead) and DF is set, that router must send ICMP
# "fragmentation needed"; if a firewall drops ICMP, the sender never learns and
# retransmits into a black hole. Look at: MSS in SYN options, size of the first
# stalled data segment, whether ICMP type 3 code 4 arrives, and test with
# `ping -D -s <size>`. Fixes: MSS clamping on the tunnel edge, allow ICMP, or
# PLPMTUD (RFC 4821).

if __name__ == "__main__":
    MAC_A, MAC_B = "aa:bb:cc:00:00:01", "aa:bb:cc:00:00:02"

    # Part 1
    eth = parse_ethernet(build_ethernet(MAC_B, MAC_A, ETHERTYPE_IPV4, b"payload"))
    assert (eth.dst, eth.src, eth.ethertype, eth.vlan, eth.payload) == (MAC_B, MAC_A, 0x0800, None, b"payload")
    tagged = parse_ethernet(build_ethernet(MAC_B, MAC_A, ETHERTYPE_IPV4, b"x", vlan=100))
    assert tagged.vlan == 100 and tagged.ethertype == 0x0800 and tagged.payload == b"x"
    try:
        parse_ethernet(b"\x00" * 10)
        assert False
    except ValueError:
        pass

    # Part 2
    assert ones_complement_checksum(b"\x00\x01\xf2\x03\xf4\xf5\xf6\xf7") == 0x220D
    assert ones_complement_checksum(b"\x00\x01\xf2\x03\xf4\xf5\xf6\xf7\x22\x0d") == 0
    raw_ip = build_ipv4("10.0.0.1", "10.0.0.2", PROTO_UDP, b"abc", ttl=7, ident=42, df=True)
    ip = parse_ipv4(raw_ip)
    assert (ip.version, ip.ihl, ip.total_length, ip.ttl, ip.protocol) == (4, 5, 23, 7, 17)
    assert (ip.src, ip.dst, ip.identification, ip.df, ip.mf) == ("10.0.0.1", "10.0.0.2", 42, True, False)
    assert ip.options_length == 0 and ip.checksum_ok and ip.payload == b"abc"
    corrupted = raw_ip[:8] + bytes([raw_ip[8] ^ 0x01]) + raw_ip[9:]  # flip a TTL bit
    assert not parse_ipv4(corrupted).checksum_ok
    with_opts = parse_ipv4(build_ipv4("1.1.1.1", "2.2.2.2", PROTO_TCP, b"", options=b"\x94\x04\x00\x00"))
    assert with_opts.ihl == 6 and with_opts.options_length == 4 and with_opts.checksum_ok
    padded = parse_ipv4(raw_ip + b"\x00" * 20)  # Ethernet min-frame padding
    assert padded.payload == b"abc"

    # Part 3
    tcp = parse_tcp(build_tcp(40000, 443, 1000, 2000, {"SYN", "ACK"}, options=b"\x02\x04\x05\xb4"))
    assert (tcp.sport, tcp.dport, tcp.seq, tcp.ack) == (40000, 443, 1000, 2000)
    assert tcp.flags == {"SYN", "ACK"} and tcp.data_offset == 6 and tcp.options_length == 4
    assert tcp.window == 65535 and tcp.payload == b""
    tcp2 = parse_tcp(build_tcp(1, 2, 0, 0, {"PSH", "ACK", "FIN"}, b"data"))
    assert tcp2.flags == {"PSH", "ACK", "FIN"} and tcp2.payload == b"data"
    udp = parse_udp(build_udp(5353, 53, b"query"))
    assert (udp.sport, udp.dport, udp.length, udp.payload) == (5353, 53, 13, b"query")

    # Part 4
    def frame(src_ip, dst_ip, proto, l4):
        return build_ethernet(MAC_B, MAC_A, ETHERTYPE_IPV4, build_ipv4(src_ip, dst_ip, proto, l4))

    C, S = "10.0.0.1", "10.0.0.2"
    frames = [
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 100, 0, {"SYN"})),
        frame(S, C, PROTO_TCP, build_tcp(80, 50000, 900, 101, {"SYN", "ACK"})),
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 101, 901, {"ACK"})),
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 101, 901, {"ACK", "PSH"}, b"GET / ")),   # 6 bytes
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 117, 901, {"ACK", "PSH"}, b"HTTP")),     # skipped 107..116
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 107, 901, {"ACK", "PSH"}, b"1234567890")),  # arrives late: out-of-order
        frame(C, S, PROTO_TCP, build_tcp(50000, 80, 101, 901, {"ACK", "PSH"}, b"GET / ")),   # retransmission
        frame(S, C, PROTO_TCP, build_tcp(80, 50000, 901, 121, {"ACK", "FIN"})),
        frame(C, S, PROTO_UDP, build_udp(5000, 53, b"q")),
        frame(S, C, PROTO_UDP, build_udp(53, 5000, b"r")),
    ]
    ft = FlowTracker()
    for f in frames:
        ft.add(f)
    flows = ft.flows()
    assert len(flows) == 2, flows
    tcp_key = flow_key(PROTO_TCP, (C, 50000), (S, 80))
    assert tcp_key == (PROTO_TCP, ("10.0.0.1", 50000), ("10.0.0.2", 80))
    t = flows[tcp_key]
    assert t.packets == 8 and t.syn and t.fin
    assert t.retransmissions == 1, t
    assert t.out_of_order == 1, t
    assert t.bytes == sum(len(f) for f in frames[:8])
    u = flows[flow_key(PROTO_UDP, (S, 53), (C, 5000))]
    assert u.packets == 2 and not u.syn and u.retransmissions == 0
    assert ft.add(build_ethernet(MAC_A, MAC_B, 0x0806, b"\x00" * 28)) is None  # ARP ignored

    # Part 5
    payload = bytes(range(256)) * 12  # 3072 bytes
    frags = fragment_ipv4(C, S, PROTO_UDP, 777, payload, 1024)
    assert len(frags) == 3
    hdrs = [parse_ipv4(f) for f in frags]
    assert [h.fragment_offset for h in hdrs] == [0, 128, 256]
    assert [h.mf for h in hdrs] == [True, True, False]
    ra = Reassembler()
    key = Reassembler.key_of(hdrs[0])
    assert ra.add(hdrs[2]) is None
    assert ra.missing(key) == [(0, 2048)]
    assert ra.add(hdrs[0]) is None
    assert ra.missing(key) == [(1024, 2048)]
    assert ra.add(hdrs[1]) == payload
    assert ra.missing(key) == []  # buffer released
    # last fragment unseen -> open-ended gap
    ra2 = Reassembler()
    assert ra2.add(hdrs[1]) is None
    assert ra2.missing(key) == [(0, 1024), (2048, None)]
    # duplicate fragment is harmless
    assert ra2.add(hdrs[1]) is None and ra2.add(hdrs[0]) is None
    assert ra2.add(hdrs[2]) == payload
    # unfragmented packet passes straight through
    assert ra2.add(parse_ipv4(build_ipv4(C, S, PROTO_UDP, b"whole"))) == b"whole"
    print("ok")

# ---------------------------------------------------------------------------
# INTERVIEWER FOLLOW-UPS
# ---------------------------------------------------------------------------
# Q: Why not compute the TCP checksum too?
# A: It covers a pseudo-header (src, dst, proto, length) from the IP layer, so
#    the TCP parser needs IP context; and NIC offload means captures on the
#    sending host often show a "wrong" checksum. Verify only on ingress captures.
# Q: Your seq comparison uses `<`. What about wraparound?
# A: Sequence numbers are mod 2^32; use signed 32-bit difference:
#    ((a - b) & 0xFFFFFFFF) < 0x80000000 means a >= b. Matters on long flows.
# Q: The seen-set grows without bound. Fix?
# A: Keep a bounded window (e.g. seqs within 64 KB of next_seq) or a ring; or
#    only track the last N segments -- retransmissions are recent by nature.
# Q: How would you handle overlapping fragments?
# A: Pick a policy (first-wins like Windows, last-wins like older Linux) and
#    document it; IDS should model the target OS. Also add a per-key timer.
# Q: What is the difference between a TCP flow ending with FIN vs RST?
# A: FIN is an orderly close (both sides FIN/ACK); RST aborts. Seeing RST right
#    after SYN means closed port or a middlebox; after data, often app crash/firewall.
