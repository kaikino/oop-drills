"""
ip-tools -- REFERENCE SOLUTION.

See ip-tools.py for the interviewer's problem statement. Same tests at the bottom.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Part 1: parsing and containment (no ipaddress module)
# ---------------------------------------------------------------------------
# Data shape: an IPv4 address is a plain int in [0, 2^32). A CIDR is (network_int,
# prefix_len). Working in ints makes containment a single mask-and-compare and
# makes everything below (split, summarize, trie) a matter of bit arithmetic.

MAX32 = 0xFFFFFFFF


def parse_ipv4(s: str) -> int:
    """'10.1.2.3' -> int. Strict: exactly 4 octets, 0..255, no leading zeros
    (leading zeros are ambiguous: some libcs read '010' as octal)."""
    parts = s.split(".")
    if len(parts) != 4:
        raise ValueError("expected 4 octets: %r" % s)
    value = 0
    for p in parts:
        if not p.isdigit() or len(p) > 3 or (len(p) > 1 and p[0] == "0"):
            raise ValueError("bad octet %r in %r" % (p, s))
        octet = int(p)
        if octet > 255:
            raise ValueError("octet out of range %r in %r" % (p, s))
        value = (value << 8) | octet
    return value


def format_ipv4(n: int) -> str:
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def netmask(prefix_len: int) -> int:
    """/24 -> 0xFFFFFF00. Note /0 must produce 0, hence the & MAX32."""
    if not 0 <= prefix_len <= 32:
        raise ValueError("bad prefix length %d" % prefix_len)
    return (MAX32 << (32 - prefix_len)) & MAX32


def parse_cidr(s: str) -> Tuple[int, int]:
    """'10.1.2.3/24' -> (network_int, 24). Host bits are zeroed."""
    ip_str, sep, plen = s.partition("/")
    if not sep or not plen.isdigit():
        raise ValueError("expected a/b/c/d/len: %r" % s)
    prefix_len = int(plen)
    mask = netmask(prefix_len)  # validates range
    return parse_ipv4(ip_str) & mask, prefix_len


def format_cidr(net: int, prefix_len: int) -> str:
    return "%s/%d" % (format_ipv4(net), prefix_len)


def is_valid_ipv4(s: str) -> bool:
    try:
        parse_ipv4(s)
        return True
    except ValueError:
        return False


def is_valid_cidr(s: str) -> bool:
    try:
        parse_cidr(s)
        return True
    except ValueError:
        return False


def contains(cidr: str, ip: str) -> bool:
    net, plen = parse_cidr(cidr)
    return (parse_ipv4(ip) & netmask(plen)) == net


# ---------------------------------------------------------------------------
# Part 2: subnet arithmetic
# ---------------------------------------------------------------------------
# Data shape: SubnetInfo is a read-only summary. /31 (RFC 3021 point-to-point)
# and /32 are the classic edge cases: they have no "network/broadcast" reserved.


@dataclass(frozen=True)
class SubnetInfo:
    network: str
    broadcast: str
    first_host: str
    last_host: str
    host_count: int


def subnet_info(cidr: str) -> SubnetInfo:
    net, plen = parse_cidr(cidr)
    bcast = net | (~netmask(plen) & MAX32)
    if plen >= 31:
        # /31: both addresses usable. /32: net == bcast, one host.
        first, last, count = net, bcast, bcast - net + 1
    else:
        first, last, count = net + 1, bcast - 1, bcast - net - 1
    return SubnetInfo(format_ipv4(net), format_ipv4(bcast), format_ipv4(first),
                      format_ipv4(last), count)


def split_subnet(cidr: str, n: int) -> List[str]:
    """Split into n equal subnets; n must be a power of two. /24 into 4 -> four /26."""
    if n <= 0 or n & (n - 1):
        raise ValueError("n must be a power of two, got %d" % n)
    net, plen = parse_cidr(cidr)
    extra_bits = n.bit_length() - 1
    new_plen = plen + extra_bits
    if new_plen > 32:
        raise ValueError("cannot split %s into %d subnets" % (cidr, n))
    block = 1 << (32 - new_plen)
    return [format_cidr(net + i * block, new_plen) for i in range(n)]


# ---------------------------------------------------------------------------
# Part 3: summarization
# ---------------------------------------------------------------------------
# Invariant on the stack: sorted by address, pairwise disjoint, and no two
# adjacent entries are mergeable siblings. Sorting by (net, plen) guarantees a
# covering block is seen before anything it covers, so "covered?" is a single
# check against the stack top. Complexity O(n log n).


def _covers(outer: Tuple[int, int], inner: Tuple[int, int]) -> bool:
    onet, oplen = outer
    inet, iplen = inner
    return iplen >= oplen and (inet & netmask(oplen)) == onet


def _siblings(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """Same length, differ only in the last network bit, and a is the lower half."""
    if a[1] != b[1] or a[1] == 0:
        return False
    plen = a[1]
    return a[0] ^ b[0] == (1 << (32 - plen)) and (a[0] & netmask(plen - 1)) == a[0]


def summarize(cidrs: List[str]) -> List[str]:
    entries = sorted({parse_cidr(c) for c in cidrs})
    stack: List[Tuple[int, int]] = []
    for cur in entries:
        if stack and _covers(stack[-1], cur):
            continue
        stack.append(cur)
        # Merging can create a block that is itself a sibling of the previous one.
        while len(stack) >= 2 and _siblings(stack[-2], stack[-1]):
            lo = stack[-2]
            stack.pop()
            stack.pop()
            stack.append((lo[0], lo[1] - 1))
    return [format_cidr(net, plen) for net, plen in stack]


# ---------------------------------------------------------------------------
# Part 4: longest-prefix-match table (binary trie)
# ---------------------------------------------------------------------------
# Data shape: each trie node has two children (bit 0 / bit 1) and an optional
# next hop. A route of length L lives at depth L. Lookup walks the destination's
# bits MSB-first and remembers the deepest next hop passed -- that is exactly
# "longest prefix match". The default route is the root node's next hop.
# Lookup is O(32) regardless of table size; a dict-per-prefix-length alternative
# is O(33) hash probes and easier to write but slower to iterate/remove.


class _TrieNode:
    __slots__ = ("children", "next_hop")

    def __init__(self) -> None:
        self.children: List[Optional[_TrieNode]] = [None, None]
        self.next_hop: Optional[str] = None


class RoutingTable:
    def __init__(self) -> None:
        self._root = _TrieNode()
        self._routes: Dict[Tuple[int, int], str] = {}

    def add(self, cidr: str, next_hop: str) -> None:
        net, plen = parse_cidr(cidr)
        node = self._root
        for i in range(plen):
            bit = (net >> (31 - i)) & 1
            if node.children[bit] is None:
                node.children[bit] = _TrieNode()
            node = node.children[bit]  # type: ignore[assignment]
        node.next_hop = next_hop
        self._routes[(net, plen)] = next_hop

    def remove(self, cidr: str) -> bool:
        net, plen = parse_cidr(cidr)
        if (net, plen) not in self._routes:
            return False
        del self._routes[(net, plen)]
        node: Optional[_TrieNode] = self._root
        for i in range(plen):
            node = node.children[(net >> (31 - i)) & 1]  # type: ignore[union-attr]
        node.next_hop = None  # type: ignore[union-attr]
        # Not pruning empty nodes keeps remove O(32) and simple; pruning is a
        # memory optimisation you would add when churn is high.
        return True

    def lookup(self, ip: str) -> Optional[str]:
        addr = parse_ipv4(ip)
        node: Optional[_TrieNode] = self._root
        best = node.next_hop if node is not None else None
        for i in range(32):
            node = node.children[(addr >> (31 - i)) & 1]  # type: ignore[union-attr]
            if node is None:
                break
            if node.next_hop is not None:
                best = node.next_hop
        return best

    def routes(self) -> List[Tuple[str, str]]:
        return sorted((format_cidr(n, p), nh) for (n, p), nh in self._routes.items())


# ---------------------------------------------------------------------------
# Part 5: IPv6 parse / expand / compress (RFC 5952)
# ---------------------------------------------------------------------------
# Data shape: a list of 8 ints (16-bit groups). Parsing handles at most one '::'.
# RFC 5952 canonical form: lowercase hex, no leading zeros, '::' replaces the
# LONGEST run of >=2 zero groups, leftmost on ties, never a single zero group.


def parse_ipv6(s: str) -> List[int]:
    if s.count("::") > 1:
        raise ValueError("more than one '::' in %r" % s)

    def groups(part: str) -> List[int]:
        if part == "":
            return []
        out = []
        for g in part.split(":"):
            if not 1 <= len(g) <= 4 or any(c not in "0123456789abcdefABCDEF" for c in g):
                raise ValueError("bad group %r in %r" % (g, s))
            out.append(int(g, 16))
        return out

    if "::" in s:
        left, right = s.split("::")
        lg, rg = groups(left), groups(right)
        if len(lg) + len(rg) > 7:
            raise ValueError("too many groups in %r" % s)
        return lg + [0] * (8 - len(lg) - len(rg)) + rg
    g = groups(s)
    if len(g) != 8:
        raise ValueError("expected 8 groups in %r" % s)
    return g


def expand_ipv6(s: str) -> str:
    return ":".join("%04x" % g for g in parse_ipv6(s))


def compress_ipv6(s: str) -> str:
    groups = parse_ipv6(s)
    # Find the longest run of zeros (leftmost wins ties because we use strict >).
    best_start, best_len = -1, 0
    i = 0
    while i < 8:
        if groups[i] != 0:
            i += 1
            continue
        j = i
        while j < 8 and groups[j] == 0:
            j += 1
        if j - i > best_len:
            best_start, best_len = i, j - i
        i = j
    hexs = ["%x" % g for g in groups]
    if best_len < 2:
        return ":".join(hexs)
    left = ":".join(hexs[:best_start])
    right = ":".join(hexs[best_start + best_len:])
    return left + "::" + right


# ---------------------------------------------------------------------------
# Part 6: discussion
# ---------------------------------------------------------------------------
# Why longest-prefix match?  Prefixes overlap by design: a /8 aggregate covers a
# region, a /24 inside it is a more specific announcement (a customer, a
# datacentre). The most specific prefix is the most authoritative knowledge we
# have about that destination, so it wins. It is also what makes aggregation
# work: you can announce a summary and still punch holes in it.
#
# How hardware does it: TCAM (ternary CAM) stores value/mask pairs and compares a
# destination against EVERY entry in one clock. Entries are ordered longest
# prefix first; a priority encoder returns the first hit. Fixed latency, but
# expensive, power hungry, and finite (tens of thousands to ~1M entries). Many
# ASICs instead use multi-bit tries / hashed prefix-length tables in SRAM with a
# few pipelined lookups. The full IPv4 DFZ table (~1M routes) is why older
# hardware with 512k TCAM entries fell over in 2014.
#
# Overlapping prefixes with different next hops: traffic to addresses in the
# more specific goes to its next hop, the rest of the aggregate goes to the
# aggregate's next hop. Nothing is "wrong", but it is the classic source of
# surprise: a /24 leak from a peer can hijack traffic that the /16 owner
# expected to receive. Equal-length duplicates are resolved by admin distance
# / protocol preference, then ECMP if the same protocol.

if __name__ == "__main__":
    # Part 1
    assert parse_ipv4("10.1.2.3") == 0x0A010203
    assert format_ipv4(0x0A010203) == "10.1.2.3"
    assert parse_cidr("10.1.2.3/24") == (0x0A010200, 24)
    assert parse_cidr("0.0.0.0/0") == (0, 0)
    for bad in ["10.1.2", "10.1.2.256", "10.01.2.3", "a.b.c.d", "1.2.3.4.5", ""]:
        assert not is_valid_ipv4(bad), bad
    for bad in ["10.0.0.0/33", "10.0.0.0", "10.0.0.0/-1", "10.0.0.0/x"]:
        assert not is_valid_cidr(bad), bad
    assert contains("10.0.0.0/8", "10.255.1.1")
    assert not contains("10.0.0.0/8", "11.0.0.1")
    assert contains("0.0.0.0/0", "8.8.8.8")
    assert contains("192.168.1.7/32", "192.168.1.7")
    assert not contains("192.168.1.7/32", "192.168.1.8")

    # Part 2
    info = subnet_info("192.168.1.130/26")
    assert info == SubnetInfo("192.168.1.128", "192.168.1.191", "192.168.1.129",
                              "192.168.1.190", 62), info
    assert subnet_info("10.0.0.0/31").host_count == 2
    assert subnet_info("10.0.0.0/31").first_host == "10.0.0.0"
    assert subnet_info("10.0.0.5/32") == SubnetInfo("10.0.0.5", "10.0.0.5", "10.0.0.5",
                                                     "10.0.0.5", 1)
    assert split_subnet("10.0.0.0/24", 4) == ["10.0.0.0/26", "10.0.0.64/26",
                                              "10.0.0.128/26", "10.0.0.192/26"]
    assert split_subnet("10.0.0.0/24", 1) == ["10.0.0.0/24"]
    try:
        split_subnet("10.0.0.0/24", 3)
        assert False
    except ValueError:
        pass
    try:
        split_subnet("10.0.0.0/31", 4)
        assert False
    except ValueError:
        pass

    # Part 3
    assert summarize(["10.0.0.0/24", "10.0.1.0/24"]) == ["10.0.0.0/23"]
    assert summarize(["10.0.1.0/24", "10.0.2.0/24"]) == ["10.0.1.0/24", "10.0.2.0/24"]
    assert summarize(["10.0.0.0/8", "10.1.0.0/16", "10.0.0.0/24"]) == ["10.0.0.0/8"]
    assert summarize(["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]) == ["10.0.0.0/22"]
    assert summarize(["10.0.3.0/24", "10.0.2.0/24", "10.0.1.0/24", "10.0.0.0/24"]) == ["10.0.0.0/22"]
    assert summarize(["10.0.0.0/25", "10.0.0.128/25", "10.0.1.0/24"]) == ["10.0.0.0/23"]
    assert summarize(["10.0.0.7/24", "10.0.0.9/24"]) == ["10.0.0.0/24"]  # host bits ignored
    assert summarize([]) == []
    assert summarize(["0.0.0.0/1", "128.0.0.0/1"]) == ["0.0.0.0/0"]

    # Part 4
    rt = RoutingTable()
    assert rt.lookup("1.2.3.4") is None
    rt.add("0.0.0.0/0", "default-gw")
    rt.add("10.0.0.0/8", "core")
    rt.add("10.1.0.0/16", "dc1")
    rt.add("10.1.2.0/24", "rack7")
    assert rt.lookup("10.1.2.99") == "rack7"
    assert rt.lookup("10.1.9.9") == "dc1"
    assert rt.lookup("10.200.0.1") == "core"
    assert rt.lookup("8.8.8.8") == "default-gw"
    assert rt.remove("10.1.2.0/24") is True
    assert rt.remove("10.1.2.0/24") is False
    assert rt.lookup("10.1.2.99") == "dc1"
    rt.add("10.1.2.0/24", "rack8")  # re-add / overwrite
    assert rt.lookup("10.1.2.1") == "rack8"
    assert rt.routes()[0] == ("0.0.0.0/0", "default-gw")

    # Part 5
    assert expand_ipv6("2001:db8::1") == "2001:0db8:0000:0000:0000:0000:0000:0001"
    assert compress_ipv6("2001:0db8:0000:0000:0000:0000:0000:0001") == "2001:db8::1"
    assert compress_ipv6("2001:db8:0:0:1:0:0:1") == "2001:db8::1:0:0:1"  # leftmost tie
    assert compress_ipv6("2001:db8:0:1:1:1:1:1") == "2001:db8:0:1:1:1:1:1"  # no single-0 ::
    assert compress_ipv6("0:0:0:0:0:0:0:0") == "::"
    assert compress_ipv6("::1") == "::1"
    assert compress_ipv6("FE80::0001") == "fe80::1"
    assert compress_ipv6("1:0:0:2:0:0:0:3") == "1:0:0:2::3"  # longest run wins
    assert expand_ipv6("::") == "0000:0000:0000:0000:0000:0000:0000:0000"
    for bad in ["1::2::3", "1:2:3:4:5:6:7", "1:2:3:4:5:6:7:8:9", "12345::", "g::1", ":::"]:
        try:
            parse_ipv6(bad)
            assert False, bad
        except ValueError:
            pass
    print("ok")

# ---------------------------------------------------------------------------
# INTERVIEWER FOLLOW-UPS
# ---------------------------------------------------------------------------
# Q: Your summarize is O(n log n). Can it miss a merge because of ordering?
# A: No -- the stack invariant (sorted, disjoint, no mergeable adjacent pair) is
#    restored after every push, and merging only ever produces a block that
#    starts at the same address as the lower sibling, so earlier entries stay valid.
# Q: How would you make the trie use less memory for a full DFZ table?
# A: Path-compressed (Patricia) trie or a multibit stride trie (e.g. 8-8-8-8 or
#    16-8-8) -- trades memory for fewer lookups; that is what Linux fib_trie does.
# Q: Why do you zero host bits in parse_cidr rather than reject them?
# A: Routers accept "10.0.0.7/24" and store the network; rejecting is stricter
#    and fine for config validation. Say which you chose and why.
# Q: What is different for IPv6 in the routing table?
# A: 128-bit keys, so depth 128 in a binary trie; stride tries matter more.
#    Also /64 dominates so hash tables per length become attractive.
# Q: /31 point-to-point: why does it exist?
# A: RFC 3021 -- conserves addresses on router links; no broadcast needed on p2p.
