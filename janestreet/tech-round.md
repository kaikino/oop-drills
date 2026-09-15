# Jane Street network engineer tech round — question bank with model answers

Answer style they want: mechanism → why → failure mode → how you'd observe it. Each item below
gives the short answer, then the depth an interviewer will push to. Questions marked ★ were
directly reported for this role.

---

## 1. TCP/IP core

**★ Walk me through the TCP header. Why is each field there?**
Source/destination ports (16 b each: demultiplex to sockets). Sequence number (32 b: byte offset
of the first payload byte; ISN randomised to stop spoofing/old-segment collisions). Acknowledgement
number (next byte expected; cumulative). Data offset (header length in 32-bit words; options make
it variable, min 20 B, max 60 B). Reserved bits. Flags: CWR/ECE (explicit congestion notification),
URG (urgent pointer valid; basically unused), ACK, PSH (push to app now), RST (abort; no such
socket, or refuse), SYN (sync ISNs; consumes one seq number), FIN (no more data; consumes one seq
number). Window (16 b: receiver's advertised free buffer, scaled by the window-scale option, so
max 2^30). Checksum (covers pseudo-header + header + data; mandatory in TCP). Urgent pointer.
Options: MSS (max segment size, sent in SYN only), window scale (SYN only), SACK-permitted/SACK
blocks (tell sender exactly which ranges arrived), timestamps (RTT measurement + PAWS to protect
against wrapped sequence numbers at high speed), NOP/EOL for padding.
Push: *Why is the window 16 bits?* 1981 design; window scale option fixes it (shift up to 14).
*What's the max throughput with no scaling on a 100 ms path?* 64 KB / 0.1 s ≈ 5 Mbit/s.
*Why does SYN consume a sequence number?* So the SYN itself can be acknowledged/retransmitted.

**Three-way handshake, states, and what each side allocates.**
CLOSED → client sends SYN (SYN_SENT); server in LISTEN replies SYN-ACK (SYN_RCVD, placed in the
SYN queue; with SYN cookies, no state); client ACKs (ESTABLISHED), server moves to the accept
queue (ESTABLISHED). `ss -ltn` shows Recv-Q = current accept queue length, Send-Q = backlog.
Overflow of the accept queue → SYN-ACK retransmits, "connection timed out" from clients even
though the server is up: check `nstat -az | grep -i listen` (ListenOverflows/ListenDrops).

**Four-way close and TIME_WAIT.**
Active closer sends FIN (FIN_WAIT_1) → ACK (FIN_WAIT_2) → peer FIN (peer in LAST_ACK) → ACK
(TIME_WAIT for 2×MSL, 60 s on Linux). Purpose: retransmit the last ACK if lost; let stray segments
die before the 4-tuple is reused. Lots of TIME_WAIT on a client doing many short connections can
exhaust ephemeral ports (~28k by default): fix with connection reuse, `tcp_tw_reuse`, larger
`ip_local_port_range`. CLOSE_WAIT piling up = *application* bug (it never called close()).

**Reliability: retransmission and RTO.**
RTT is sampled (Karn's algorithm: not from retransmitted segments unless timestamps), smoothed
(SRTT, RTTVAR), RTO = SRTT + 4·RTTVAR, min 200 ms on Linux, exponential backoff. Fast retransmit
on 3 duplicate ACKs (no need to wait RTO). SACK lets the sender fill exactly the holes. Tail-loss
probe and RACK are modern refinements. Observe: `ss -tin` shows rto, rtt, retrans, lost, cwnd;
`nstat` shows TcpRetransSegs.

**Flow control vs congestion control.**
Flow: receiver window, protects the receiver. Congestion: cwnd, protects the network. Sender sends
min(rwnd, cwnd). Slow start (cwnd doubles per RTT until ssthresh or loss), congestion avoidance
(+1 MSS per RTT), on loss: ssthresh = cwnd/2; timeout → cwnd = 1 MSS (Reno/NewReno). CUBIC (Linux
default) grows as a cubic function of time since last loss. BBR models bandwidth and RTT instead
of reacting to loss. Bandwidth-delay product = the bytes in flight needed to fill the pipe;
buffers must hold at least that (`net.ipv4.tcp_rmem/wmem`).

**Nagle and delayed ACK.**
Nagle: don't send a small segment while there's unacked data (coalesce). Delayed ACK: receiver
waits up to 40 ms to piggyback ACKs. Together they cause 40 ms stalls in request/response
protocols → trading apps set `TCP_NODELAY`. `TCP_QUICKACK` disables delayed ACK per call.

**MSS, MTU, fragmentation, PMTUD.**
MTU 1500 (Ethernet) → MSS 1460 for IPv4 (1440 for IPv6). DF bit set by default on Linux TCP;
a router with a smaller MTU must send ICMP "fragmentation needed" (type 3 code 4). If ICMP is
filtered → PMTUD blackhole: handshake works (small packets), bulk transfer hangs. Fixes: allow
ICMP, MSS clamping on the edge, `tcp_mtu_probing=1`. Jumbo frames (9000) reduce per-packet
overhead; every hop must agree or you get silent drops.

**IPv4 header.** Version/IHL, DSCP/ECN, total length, identification + flags (DF/MF) + fragment
offset, TTL (decremented per hop; 0 → ICMP time exceeded, which traceroute exploits), protocol
(6 TCP, 17 UDP, 1 ICMP, 89 OSPF, 2 IGMP, 47 GRE), header checksum (header only; recomputed
every hop), src/dst. IPv6 drops the checksum and fragmentation-by-routers, adds flow label and
extension headers; hop limit instead of TTL.

**UDP.** 8-byte header (ports, length, checksum). No connection, ordering, or retransmission —
the application does it (market data uses sequence numbers + retransmission requests). Why UDP
for market data: multicast is only possible with UDP; no head-of-line blocking; lowest latency.

**ICMP.** Echo (ping), destination unreachable (codes: net/host/port unreachable, frag needed),
time exceeded (traceroute), redirect. Routers rate-limit ICMP generation → traceroute shows loss at
intermediate hops that's not real loss ("only the last hop matters").

**How traceroute works.** Sends probes (UDP high ports on Linux, ICMP echo on Windows, TCP with
`-T`) with TTL 1, 2, 3…; each hop returns ICMP time exceeded from *its ingress interface* address.
Asymmetric paths: you see the forward path only. `mtr` does it continuously with loss stats.
`*` = hop doesn't respond (rate limited, filtered, or MPLS hidden).

**★ What happens when I `curl http://example.com` from a Linux box?** DNS (resolv.conf → resolver;
`getaddrinfo`), route lookup (`ip route get`), ARP for the next hop (`ip neigh`), socket → SYN
(ephemeral port), handshake, HTTP request, response, close. Each step has a failure mode and a
tool; walk them in order when debugging.

---

## 2. Layer 2, ARP, and the LAN

**★ ARP.** "Who has 10.0.0.1? Tell 10.0.0.5" broadcast (ff:ff:ff:ff:ff:ff, ethertype 0x0806);
owner replies unicast; both cache (`ip neigh`, states REACHABLE/STALE/DELAY/PROBE/FAILED;
base_reachable_time 30 s). Gratuitous ARP: announce your own IP (detect duplicates, update
switches after failover/VRRP). Proxy ARP: router answers for hosts behind it. ARP is unauthenticated
→ spoofing; mitigations: dynamic ARP inspection, static entries. IPv6 uses NDP (ICMPv6 NS/NA,
multicast solicited-node addresses) instead.
Push: *Host has the right IP but can't reach the gateway; ARP shows FAILED. Where do you look?*
Wrong VLAN on the port, port down, gateway ACL, duplicate IP elsewhere, MAC filtering.

**Switch forwarding.** Learn source MAC per (VLAN, port); forward to the learned port; flood
unknown unicast/broadcast/multicast within the VLAN; age entries (300 s default). Table overflow →
flooding everything (a MAC-flooding attack). "MAC move" between ports repeatedly = loop or
duplicate host.

**VLANs and trunks.** 802.1Q tag (4 B: TPID 0x8100, PCP, DEI, 12-bit VID → 4094 usable). Access
port = untagged, one VLAN; trunk = tagged, many VLANs, native VLAN untagged (mismatched native
VLAN is a classic misconfig). Inter-VLAN routing needs an L3 hop (SVI / router-on-a-stick).

**Spanning tree.** Prevents L2 loops (which cause broadcast storms because Ethernet has no TTL).
Root bridge election (lowest priority.MAC), root ports, designated ports, blocked ports. RSTP
converges in seconds; MSTP maps VLANs to instances. Modern data centers avoid STP by routing
(leaf-spine with BGP/OSPF to the ToR, or EVPN/VXLAN overlays). BPDU guard on edge ports.

**LACP / link aggregation.** Bundle N links as one logical link; hash per flow (L2/L3/L4 fields)
so a single flow uses one member (no reordering) → one elephant flow can't exceed one member's
bandwidth; polarization when the same hash is used at multiple tiers. LACP (802.3ad) negotiates
membership and detects unidirectional failures; static LAG doesn't.

**Duplex/speed mismatch, CRC errors, unidirectional links.** Auto-negotiation failure → half-duplex
→ late collisions; CRC/FCS errors → bad optics/fibre/patch cable, check light levels
(`show interfaces transceiver` / `ethtool -m`); UDLD/BFD to detect one-way links.

**MTU at L2 vs L3.** Interface MTU vs IP MTU; VXLAN adds 50 B, MPLS 4 B per label, Q-in-Q 4 B.

---

## 3. Routing fundamentals

**Longest prefix match.** The FIB picks the most specific route; ties broken by administrative
distance (connected 0, static 1, eBGP 20, OSPF 110, IS-IS 115, RIP 120, iBGP 200 on Cisco) and then
by metric within the protocol. `ip route get 10.1.2.3` shows the choice on Linux.

**Static vs dynamic; IGP vs EGP.** IGPs (OSPF, IS-IS) inside an AS: fast convergence, full
topology knowledge, link-state. EGP (BGP) between ASes: policy, scale, path vector. Inside a large
firm you'd typically run an IGP for loopback reachability and iBGP on top for services/prefixes.

**ECMP.** Multiple equal-cost next hops; per-flow hashing keeps ordering. Unequal-cost needs EIGRP
or weighted ECMP.

**Convergence.** Detect (BFD in ms vs hello timers in seconds) → propagate (LSA flood / BGP
UPDATE) → compute (SPF / best path) → install (FIB). Fast reroute / LFA precomputes backup paths.

**Asymmetric routing.** Forward and return paths differ; fine for stateless routing, breaks
stateful firewalls/NAT and confuses traceroute-based debugging.

**VRFs.** Separate routing tables on one router (management vs production vs customer).

**★ BGP local preference (reported question).** See section 4.

---

## 4. BGP

**What it is.** Path-vector protocol between ASes over TCP 179; advertises prefixes with
attributes; policy-driven. eBGP between different ASes (TTL 1 by default, next hop changed);
iBGP inside an AS (next hop unchanged, needs full mesh or route reflectors because iBGP-learned
routes aren't re-advertised to iBGP peers to avoid loops — no AS-path check inside the AS).

**Session states.** Idle → Connect → Active → OpenSent → OpenConfirm → Established. "Stuck in
Active" = TCP can't connect (reachability, ACL, wrong neighbor IP/AS, TTL for multihop).
"Flapping" = hold timer expiring (default 90 s hold / 30 s keepalive), MTU issues on large
UPDATEs, or the underlying link.

**★ Best-path decision order (Cisco-ish; know the first five cold).**
1. Highest **weight** (Cisco-local).
2. Highest **local preference** (iBGP-wide; set by inbound policy; "how much do *we* like this exit").
3. Locally originated (network/aggregate) over learned.
4. Shortest **AS path**.
5. Lowest **origin** (IGP < EGP < incomplete).
6. Lowest **MED** (compared only among routes from the same neighbouring AS unless always-compare;
   "how the *neighbour* wants us to enter their network").
7. **eBGP over iBGP**.
8. Lowest **IGP metric** to the next hop (hot-potato).
9. Oldest route (stability), then lowest router ID, then lowest neighbor address.
Push: *Two upstreams, you want all outbound traffic via ISP A unless it's down.* Set local pref 200
on routes from A, 100 from B. *You want ISP B to send you traffic for prefix P via link 2.*
You can only *influence* inbound: MED (if they honour it), AS-path prepending on link 1, more
specific prefixes on link 2, or communities the ISP publishes. *Why is local pref above AS path?*
Business policy (cost, capacity) must beat topology.

**Attributes.** Well-known mandatory: AS_PATH, NEXT_HOP, ORIGIN. Well-known discretionary:
LOCAL_PREF, ATOMIC_AGGREGATE. Optional transitive: AGGREGATOR, COMMUNITY. Optional non-transitive:
MED, ORIGINATOR_ID, CLUSTER_LIST.

**Communities.** 32-bit tags (ASN:value) carrying policy: no-export, no-advertise, blackhole
(65535:666), ISP-defined ("set local pref 80 in our network"). Large communities for 4-byte ASNs.

**Route reflectors.** Break the iBGP full mesh: RR reflects between clients; adds ORIGINATOR_ID /
CLUSTER_LIST for loop prevention; only the best path is reflected (add-path fixes that).

**Filtering and safety.** Prefix lists (max-prefix limits, reject default/bogons/your own
prefixes, reject > /24 in the DFZ), AS-path filters, RPKI/ROV (validate origin AS), GTSM (TTL 255
check), MD5/TCP-AO, BFD for fast failure detection, graceful restart, dampening (penalty per flap).

**Route leak / hijack.** Announcing prefixes you shouldn't (customer leaking provider routes to
another provider) → traffic diverted; filters + RPKI + IRR are the defences.

**Debugging "prefix not preferred".** `show ip bgp x.x.x.x/len`: see all paths, which is best and
the reason (the router prints "best" and the tie-break attribute), check local pref, AS path,
next-hop reachability (a route with an unreachable next hop is not valid), and inbound route-maps.

**BGP in a data center.** eBGP per rack with private ASNs (RFC 7938), ECMP, no IGP; simple,
scales, one protocol to debug.

---

## 5. OSPF (and a line on IS-IS)

**Basics.** Link-state IGP, IP protocol 89, multicast hellos to 224.0.0.5 (all routers) /
224.0.0.6 (DRs). Each router floods LSAs describing its links; every router in an area has the
same LSDB and runs Dijkstra (SPF) rooted at itself. Cost = reference bandwidth / interface
bandwidth (default ref 100 Mbit → every link ≥ 100M costs 1: raise `auto-cost reference-bandwidth`
to 100G or set costs explicitly).

**Neighbour states.** Down → Init (hello seen) → 2-Way (mutual hello; DR/BDR election here) →
ExStart (master/slave, DBD sequence) → Exchange (DBD summaries) → Loading (LSR/LSU) → Full.
Stuck in ExStart/Exchange = MTU mismatch (DBDs are big), stuck in Init = one-way hellos
(ACL, unidirectional link), no adjacency at all = mismatched area/hello timers/authentication/
network type/subnet mask.

**DR/BDR.** On broadcast/NBMA segments, routers form full adjacencies only with the DR and BDR
(reduces n² adjacencies); election by priority then router ID; not pre-emptive. Point-to-point
links skip it.

**Areas and LSA types.** Area 0 backbone; all other areas attach to it (ABRs). Type 1 router,
2 network (by DR), 3 summary (inter-area, by ABR), 4 ASBR summary, 5 external (redistributed),
7 NSSA external. Stub/totally-stubby/NSSA areas reduce LSDB size. Summarization only at ABR/ASBR.

**Why areas?** Bound SPF computation and flooding; a flap in one area doesn't trigger SPF
everywhere. Modern boxes can handle thousands of routers in one area, so many networks run one.

**IS-IS.** Same idea, runs directly over L2 (no IP dependency), levels instead of areas, TLV
extensibility → favoured by large ISPs and some data centers.

**OSPF vs BGP.** OSPF: topology-driven, fast, everyone knows everything, no policy. BGP: policy,
scale, slow-ish, opaque. Use OSPF/IS-IS to reach loopbacks; iBGP for everything else.

---

## 6. Multicast and market data (Jane Street specific)

**Why multicast.** Exchanges publish one stream to N subscribers; the network replicates.
UDP only. Group addresses 224.0.0.0/4 (239/8 admin-scoped). MAC = 01:00:5e + low 23 bits of the
group (so 32 groups share a MAC).

**IGMP.** Host ↔ first-hop router: join/leave reports (v2), v3 adds source filtering (SSM,
232/8). IGMP snooping on switches: forward only to ports that joined (otherwise flood the VLAN).
Querier needed on the segment or snooping tables time out → feed stops after ~260 s ("feed dies
a few minutes after it starts" = snooping without a querier).

**PIM.** Router ↔ router. PIM-SM: receivers' routers join toward a Rendezvous Point (shared tree,
*,G), then switch to the shortest-path tree (S,G). PIM-SSM: no RP, receiver specifies source
(S,G) directly — preferred for market data. RPF check: a multicast packet is accepted only if it
arrives on the interface toward the source (unicast routing table) → asymmetric routing or missing
routes silently drop multicast ("RPF failure").

**A/B feeds.** Exchanges send the same data on two groups via different paths; consumers
arbitrate by sequence number (take first arrival) and detect gaps; gap-fill via TCP retransmission
service or snapshot/recovery feeds. Exercise: `market-data-gaps.py`.

**Where multicast breaks.** No IGMP querier; snooping table missing entries; TTL too low (default
1 for many apps); RPF failures; rate limiting on the first-hop; oversubscribed links dropping
bursts (market open); host NIC ring buffer overflow (`ethtool -S | grep -i drop`, `rx_missed`);
socket buffer overflow (`netstat -su` RcvbufErrors, `net.core.rmem_max`).

**Latency for market data.** Kernel bypass (Solarflare/Onload, DPDK), busy polling, hardware
timestamps, cut-through switches (sub-µs port-to-port), avoiding queuing (no oversubscription),
L1 switches / taps for fan-out, colocation at the exchange, cross-connect length matters
(5 ns per metre in fibre).

---

## 7. DNS, DHCP, NAT, TLS (breadth)

**DNS.** Recursive resolver vs authoritative; root → TLD → authoritative; records A/AAAA/CNAME/
MX/NS/PTR/SOA/TXT/SRV; TTL caching; negative caching (SOA minimum); UDP 53 with TCP fallback on
truncation (>512 B without EDNS0); `dig +trace`, `dig @server`, `dig -x`. Linux order: nsswitch
(`files dns`), /etc/hosts, resolv.conf, systemd-resolved stub at 127.0.0.53. Failure modes: stale
cache, split-horizon confusion, missing glue, search-domain surprises.

**DHCP.** Discover/Offer/Request/Ack (broadcast; relay agent `ip helper-address` forwards across
subnets); lease times; options (router, DNS, NTP). Rogue DHCP servers → DHCP snooping.

**NAT.** Source NAT/PAT rewrites src IP:port and keeps a translation table; breaks end-to-end
(inbound needs port forwarding), embedded IPs (FTP, SIP need ALGs); conntrack table exhaustion.
Trading networks mostly avoid NAT; use it at the internet edge.

**TLS in 30 seconds.** ClientHello (versions, ciphers, SNI) → ServerHello + cert → key exchange
(ECDHE) → symmetric session keys; 1.3 does it in one RTT (0-RTT resumption). Certificates chain
to a CA; verify name, validity, chain, revocation.

**VPN/tunnels.** GRE (no crypto, carries multicast), IPsec (ESP, IKE), WireGuard; MTU shrinks
by header size; tunnels are how you'd carry multicast across a unicast-only path.

---

## 8. Linux networking and tooling (★ shell one-liners and "used to work" reported)

**Essential commands and what they show.**
- `ip -br addr`, `ip -br link`, `ip route`, `ip route get X`, `ip neigh`, `ip -s link` (counters)
- `ss -tnp` (TCP sockets + process), `ss -ltn` (listeners + queues), `ss -tin` (per-socket TCP info: rtt, cwnd, retrans), `ss -u`
- `tcpdump -ni eth0 'host X and port 179' -w f.pcap`, `-vvv`, `-e` (L2), `-s0`, filters (`vlan`, `icmp`, `tcp[tcpflags] & tcp-syn != 0`)
- `ethtool eth0` (speed/duplex/link), `-S` (NIC stats: rx_missed, rx_crc_errors), `-i` (driver), `-m` (optic DOM), `-k` (offloads), `-g` (ring sizes), `-c` (coalescing)
- `nstat -az`, `/proc/net/snmp`, `/proc/net/dev`, `/proc/net/softnet_stat` (dropped column = backlog overflow)
- `mtr -n`, `traceroute -T -p 443`, `ping -M do -s 1472` (PMTU test), `nc -zv host port`, `curl -v --resolve`
- `dig +short`, `dig +trace`, `dig -x`, `resolvectl status`
- `conntrack -L`, `iptables -L -v -n` / `nft list ruleset`
- `sysctl net.ipv4.ip_forward`, `rp_filter`, `tcp_rmem`, `somaxconn`, `netdev_max_backlog`
- `lldpctl` / `lldpcli show neighbors` (which switch port am I on)
- `journalctl -u NetworkManager --since -1h`, `dmesg -T | grep -i eth`

**Packet path in the kernel (for "where are drops?").** NIC → DMA to ring buffer → IRQ/NAPI poll →
softirq → netfilter → protocol → socket receive buffer → app `recv()`. Drops at: ring (rx_missed,
increase ring `ethtool -G`, IRQ affinity, RSS), softnet backlog (`netdev_max_backlog`), socket
buffer (`RcvbufErrors`, `SO_RCVBUF`), app too slow. Offloads: GRO/LRO/TSO/GSO, checksum offload —
tcpdump may show "bad checksum" and 64 KB segments because of them.

**Namespaces and virtual interfaces.** `ip netns`, veth pairs, bridges (`bridge link`), bonding
(`/proc/net/bonding/bond0`), VLAN subinterfaces (`ip link add link eth0 name eth0.100 type vlan id 100`), VRF on Linux.

**Process/system debugging (Linux Engineer round reports: hung process, out of memory).**
- Hung process: `cat /proc/PID/status` (State: D = uninterruptible I/O wait, T stopped), `/proc/PID/stack`, `/proc/PID/wchan`, `strace -p PID -f` (what syscall is it blocked in), `ls -l /proc/PID/fd`, `lsof -p`, `gdb -p` / `py-spy dump`.
- Out of memory: `free -m`, `vmstat 1` (si/so = swapping), `/proc/meminfo`, `dmesg | grep -i oom` (OOM killer chose by oom_score), `ps aux --sort=-rss | head`, `smem`, page cache vs RSS (buff/cache is reclaimable), `slabtop`, cgroup limits.
- CPU: `top` (%us/%sy/%wa/%si/%st), `mpstat -P ALL`, `pidstat`, `perf top`, `/proc/interrupts` (which core gets NIC IRQs), `irqbalance`.
- Disk: `iostat -x 1` (await, %util), `df -h`, `df -i` (inodes!), `du -xsh /* | sort -h`, deleted-but-open files (`lsof +L1`).
- Services: `systemctl status X`, `journalctl -xeu X`, `systemctl list-timers`.

**★ "It used to work" method.** (1) Define "work" precisely and reproduce. (2) What changed:
`last`, `journalctl --since`, package logs (`/var/log/dpkg.log`, `rpm -qa --last`), config
mtimes (`find /etc -newermt '-2 days'`), deploys, DNS, certs expiring, disk full, kernel update,
switch-side change. (3) Localize by layer: link up? IP/route? ARP? DNS? TCP connect? TLS? app?
(4) Compare with a working host (`diff` configs, `sysctl -a`, versions). (5) Bisect the change,
fix, verify, write it down. Say all of this out loud in the interview before touching anything.

---

## 9. Operating systems (JD: "OS fundamentals")

**Kernel vs user space, syscalls, interrupts.** Syscall = controlled entry into the kernel
(trap); interrupts from hardware (NIC, timer) run top halves quickly and defer work to softirqs/
tasklets/workqueues. Context switch cost ~1–5 µs; a trading process avoids it (pinning, busy-poll).

**Processes and threads.** Process = address space + fds; threads share it. `fork` + `exec`;
copy-on-write. Scheduler: CFS by virtual runtime; real-time classes SCHED_FIFO/RR; `nice`;
`taskset`/`isolcpus` to pin latency-sensitive threads; `SCHED_FIFO` risks starving the kernel.

**Memory.** Virtual memory, page tables, TLB, huge pages (2 MB/1 GB; fewer TLB misses for big
in-memory books), page cache, swap, mmap, NUMA (memory local to a socket is faster; `numactl`,
`numastat`; NIC on the wrong socket costs latency), OOM killer.

**Synchronisation.** Mutex/spinlock/RW lock/semaphore/condition variables; deadlock's four
conditions; lock-free queues for producer/consumer in low-latency systems; memory barriers.

**I/O.** Blocking/non-blocking, `select/poll/epoll` (epoll is O(ready)), `io_uring`; page cache
and `fsync`; direct I/O; zero-copy (`sendfile`, `splice`).

**File systems and storage.** Inodes (run out of inodes with many small files), journaling
(ext4/xfs), RAID levels, `fsck`, mount options (`noatime`).

**Boot.** BIOS/UEFI → bootloader → kernel → init (systemd) → targets/units. PXE boot for
provisioning fleets (DHCP option 66/67 → TFTP → kernel/initrd) — this is what "site expansion"
touches.

---

## 10. Computer architecture (JD: "computer architecture")

- Memory hierarchy: registers (~0.3 ns), L1 (~1 ns, 32–48 KB), L2 (~4 ns, 1–2 MB), L3 (~10–40 ns,
  tens of MB, shared), DRAM (~80–100 ns), NVMe (~10–100 µs), network hop (~µs to ms). Cache
  line 64 B; false sharing when two cores write the same line.
- Pipelining, superscalar, out-of-order execution, branch prediction (mispredict ~15–20 cycles;
  hot paths avoid unpredictable branches), SIMD.
- Virtual memory: TLB, page walks; huge pages reduce misses.
- PCIe: NIC ↔ CPU via DMA; lane counts and generations bound bandwidth (Gen4 x16 ≈ 32 GB/s);
  NUMA locality of the NIC matters.
- Interrupts vs polling: interrupts save CPU, polling saves latency (NAPI mixes them; kernel
  bypass polls).
- Clock domains and timestamps: TSC as a clock source (invariant TSC), `clock_gettime` vDSO.
- Serialization vs propagation delay (see `calc-drills.md`); a 1500 B frame at 10 Gbit/s takes
  1.2 µs to serialize; light in fibre ≈ 200,000 km/s → 5 µs/km.

---

## 11. Timing (NTP/PTP) — Jane Street asks because trading regulation requires it

NTP: client/server over UDP 123, offset/delay from four timestamps, ms accuracy over the
internet, sub-ms on a LAN; stratum levels; `chronyc tracking`, `chronyc sources`. PTP (IEEE 1588):
hardware timestamps at the PHY, sync/follow-up/delay-req/delay-resp, grandmaster with GPS/PPS,
boundary and transparent clocks in switches, sub-µs accuracy; `ptp4l`, `phc2sys`. Why: MiFID II /
CAT rules require timestamps within 100 µs (or 1 ms) of UTC; latency measurement; log correlation
across hosts. Failure: GM loss → holdover on the local oscillator drifts (ppm → µs/s); asymmetric
path delay biases the offset by half the asymmetry. Exercise: `clock-sync.py`.

---

## 12. Data-center and trading-network design

- Leaf-spine (Clos): every leaf connects to every spine; ECMP; predictable 3-hop latency;
  oversubscription ratio = downlink bw / uplink bw per leaf.
- Colocation: racks in exchange data centers; cross-connects to exchange handoffs; A/B feeds on
  diverse paths; out-of-band management network; console servers.
- Redundancy: dual ToRs (MLAG/EVPN multihoming), dual power, dual carriers, diverse fibre routes
  (verify *physical* diversity, not just logical) — exercise `topology-paths.py`.
- Management: OOB network, ZTP/PXE, config management (Ansible/NAPALM/Nornir), source of truth
  (NetBox), telemetry (gNMI/SNMP/sFlow), automated validation (pre/post checks) — exercise
  `config-tree.py`, `link-monitor.py`.
- Change safety: maintenance windows outside market hours, canaries, drain traffic first (cost-out
  the link / BGP graceful shutdown community 65535:0), verify, roll back plan.
- Security: management-plane ACLs, no default routes on trading VLANs, ACLs at the exchange
  handoff — exercise `acl-eval.py`.

---

## 13. Rapid-fire (answer in one line each)

- Difference between a hub, switch, router? Collision domain vs broadcast domain vs L3 boundary.
- What's a broadcast domain? All hosts that receive an L2 broadcast (a VLAN).
- /30 vs /31 for point-to-point? /31 (RFC 3021) has 2 usable addresses, no broadcast.
- Private ranges? 10/8, 172.16/12, 192.168/16; link-local 169.254/16; CGNAT 100.64/10.
- Why does ping work but SSH doesn't? ACL/firewall on port 22, service not listening (`ss -ltn`), TCP wrappers, MTU (if it hangs after banner).
- What's a default route? 0.0.0.0/0, the least-specific fallback.
- Administrative distance vs metric? Between protocols vs within a protocol.
- What's BFD? Sub-second liveness detection shared by routing protocols.
- What's an SFP DOM reading? Optical tx/rx power, temperature; low rx power → dirty/broken fibre.
- Layer 1 debugging order? Link light → `ethtool` link/speed → optic levels → swap cable/optic → swap port.
- 802.1X? Port-based authentication (EAP) before a port passes traffic.
- What's the difference between latency, jitter, and throughput? Delay, variance of delay, volume per time.
- What does `ss -s` show? Socket summary counts (TIME_WAIT etc.).
- Why can `tcpdump` show packets the app never sees? Captured before netfilter/socket drops.
- Difference between `netstat -r` and `ip route`? Legacy vs iproute2; `ip` shows multiple tables/policy routing.
