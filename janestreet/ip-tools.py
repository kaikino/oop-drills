"""
ip-tools -- IPv4/IPv6 addressing toolkit.

Interviewer: "We provision a lot of networks. Let's build the small addressing
library you'd want on hand -- by hand, no `ipaddress` module for the IPv4 parts,
because I want to see you handle the bits. We'll start simple and keep adding."

PART 1 -- Parse and contain.
  parse_ipv4("10.1.2.3") -> 0x0A010203 (an int).
  parse_cidr("10.1.2.3/24") -> (0x0A010200, 24)  -- host bits zeroed.
  Validation: exactly four octets 0..255, no leading zeros ("10.01.2.3" is
  invalid), prefix length 0..32. Raise ValueError; provide is_valid_ipv4/is_valid_cidr.
  contains("10.0.0.0/8", "10.255.1.1") -> True; contains("10.0.0.0/8", "11.0.0.1") -> False.

PART 2 -- Subnet arithmetic.
  subnet_info("192.168.1.130/26") -> network 192.168.1.128, broadcast
  192.168.1.191, first host .129, last host .190, host_count 62.
  Handle /31 (RFC 3021: both addresses usable, 2 hosts) and /32 (1 host).
  split_subnet("10.0.0.0/24", 4) -> ["10.0.0.0/26", "10.0.0.64/26",
  "10.0.0.128/26", "10.0.0.192/26"]. n must be a power of two; ValueError if
  the split would exceed /32.

PART 3 -- Summarize.
  summarize(list_of_cidrs) returns the minimal set of prefixes covering
  exactly the same addresses, sorted by address:
    ["10.0.0.0/24", "10.0.1.0/24"] -> ["10.0.0.0/23"]
    ["10.0.1.0/24", "10.0.2.0/24"] -> unchanged (not siblings: 1 and 2 differ in bit 7)
    ["10.0.0.0/8", "10.1.0.0/16"]  -> ["10.0.0.0/8"] (covered prefixes removed)
    four consecutive /24s starting at an aligned address -> one /22 (merging cascades)
  Aim for O(n log n).

PART 4 -- Longest-prefix-match routing table.
  RoutingTable with add(cidr, next_hop), remove(cidr) -> bool, lookup(ip) ->
  Optional[next_hop]. "0.0.0.0/0" is the default route. With 0/0 -> "gw",
  10/8 -> "core", 10.1/16 -> "dc1", 10.1.2/24 -> "rack7":
    lookup("10.1.2.99") -> "rack7", lookup("10.200.0.1") -> "core",
    lookup("8.8.8.8") -> "gw". Removing 10.1.2/24 makes 10.1.2.99 -> "dc1".
  A binary trie is the intended answer; a dict of sets per prefix length is acceptable.
  Explain the lookup cost either way.

PART 5 -- IPv6 text forms.
  expand_ipv6("2001:db8::1") -> "2001:0db8:0000:0000:0000:0000:0000:0001".
  compress_ipv6(s) produces the RFC 5952 canonical form: lowercase, no leading
  zeros in a group, '::' replaces the longest run of two or more zero groups,
  leftmost run on a tie, and a single zero group is never compressed:
    "2001:db8:0:0:1:0:0:1" -> "2001:db8::1:0:0:1"
    "1:0:0:2:0:0:0:3"      -> "1:0:0:2::3"
    "0:0:0:0:0:0:0:0"      -> "::"
  Reject more than one '::', wrong group counts, >4 hex digits per group.

PART 6 -- Discussion (no code).
  Why longest-prefix match rather than first match? How does a router do LPM in
  hardware (TCAM)? What are its limits? What actually happens to traffic when
  two overlapping prefixes have different next hops -- and why can that be a
  security problem?
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

MAX32 = 0xFFFFFFFF


# ----------------------------------------------------------------- Part 1

def parse_ipv4(s: str) -> int:
    pass


def format_ipv4(n: int) -> str:
    pass


def netmask(prefix_len: int) -> int:
    pass


def parse_cidr(s: str) -> Tuple[int, int]:
    pass


def format_cidr(net: int, prefix_len: int) -> str:
    pass


def is_valid_ipv4(s: str) -> bool:
    pass


def is_valid_cidr(s: str) -> bool:
    pass


def contains(cidr: str, ip: str) -> bool:
    pass


# ----------------------------------------------------------------- Part 2

@dataclass(frozen=True)
class SubnetInfo:
    network: str
    broadcast: str
    first_host: str
    last_host: str
    host_count: int


def subnet_info(cidr: str) -> SubnetInfo:
    pass


def split_subnet(cidr: str, n: int) -> List[str]:
    pass


# ----------------------------------------------------------------- Part 3

def summarize(cidrs: List[str]) -> List[str]:
    pass


# ----------------------------------------------------------------- Part 4

class RoutingTable:
    def __init__(self) -> None:
        pass

    def add(self, cidr: str, next_hop: str) -> None:
        pass

    def remove(self, cidr: str) -> bool:
        pass

    def lookup(self, ip: str) -> Optional[str]:
        pass

    def routes(self) -> List[Tuple[str, str]]:
        """Sorted list of (cidr, next_hop)."""
        pass


# ----------------------------------------------------------------- Part 5

def parse_ipv6(s: str) -> List[int]:
    """Return the 8 16-bit groups. ValueError on malformed input."""
    pass


def expand_ipv6(s: str) -> str:
    pass


def compress_ipv6(s: str) -> str:
    pass


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
