# Troubleshooting scenarios (problem-based questions for the Jane Street tech round)

Method to state up front, every time:
1. **Define "broken"**: which host, which destination, which protocol/port, since when, how many affected, intermittent or hard-down.
2. **What changed**: deploys, config pushes, cabling, maintenance, DNS, certs, package updates, time of day (market open?).
3. **Localize by layer, from the host outward**: link → IP/ARP → route → DNS → transport (TCP connect) → application. Bisect the path hop by hop.
4. **Compare with a working peer**.
5. **Fix, verify with the same test that showed the failure, write the root cause.**

Say the commands you would run and what each result would tell you. Interviewers grade the *process*.

---

## S1. "Host A can't reach host B (same data center). Ping fails."

Walk: `ip -br link` on A (up? carrier?), `ip -br addr` (right IP/mask? duplicate?), `ip route get B`
(which interface/gateway), `ip neigh` (gateway MAC resolved? FAILED → L2 problem: wrong VLAN, port
down, ACL blocking ARP), `ping gateway`, `mtr -n B` (where does it stop?), on B: `ss`, firewall
(`iptables -L -v -n`), `rp_filter` with asymmetric routes, does B ping A? `tcpdump -ni eth0 icmp and host A`
on B: if echo requests arrive but no replies → B-side (firewall, rp_filter, wrong return route).
Root causes seen in practice: VLAN mismatch on the switch port, wrong subnet mask (A thinks B is
local and ARPs for it), gateway ACL, B's default route missing, host firewall, duplicate IP.

## S2. "It used to work yesterday. Nothing changed." (★ reported)

Nothing *you know of* changed. Find it: `last -x | head` (reboots), `journalctl --since yesterday -p warning`,
`rpm -qa --last | head` / `/var/log/apt/history.log`, `find /etc -newermt '-1 day' -type f`,
`systemctl list-timers` (cron/timers ran overnight?), certificate expiry (`openssl s_client`),
DNS TTL rolled over to a new answer, disk full (`df -h`, `df -i`), `dmesg -T` (link flaps, NIC
resets, OOM), upstream switch config change (ask/check change log, `lldpctl` to see if you moved
ports), DHCP lease renewed with a new address, time jumped (Kerberos/TLS fail on clock skew;
`chronyc tracking`). Then compare with a still-working host.

## S3. "TCP connects fine but large transfers hang / SSH works but `scp` stalls."

Classic PMTUD blackhole. Small packets (handshake, banner) pass; full-MTU segments with DF set
are dropped by a hop with a smaller MTU whose ICMP "frag needed" is filtered or never sent
(tunnel/VPN/VXLAN added encapsulation). Test: `ping -M do -s 1472 B` (1500 MTU) then smaller sizes;
`tracepath B` reports pmtu; `ss -tin` shows retransmits growing with no progress; `tcpdump`
shows repeated retransmission of the same big segment. Fix: allow ICMP type 3/4 through, clamp
MSS at the tunnel edge, raise MTU consistently on all hops, or `tcp_mtu_probing`.

## S4. "BGP session to the upstream keeps flapping."

Check: `show bgp neighbor` (state history, last reset reason: hold timer expired, peer closed,
notification code), the physical link (errors, flaps in logs), BFD state, MTU (large UPDATEs
after session establishment fail while keepalives pass → session drops right after Established →
MTU mismatch; verify with a full-size DF ping), CPU on the router (control plane starved), max-prefix
limit exceeded (peer sends more routes than allowed → teardown), MD5/TCP-AO mismatch after a key
rotation, TTL for multihop peers, control-plane policing dropping BGP packets under load,
route dampening on the other side. Isolate: does the link flap (L1) or only the session (L3/L4)?

## S5. "Prefix X is being routed the wrong way / out the expensive link." (★ local pref reported)

`show ip bgp X`: list all paths, best path marker, and *why* (weight, local pref, AS path length,
origin, MED, eBGP/iBGP, IGP metric, router ID). Common findings: an inbound route-map didn't match
(wrong prefix-list, community not matched), local pref defaulting to 100 on both, a more-specific
prefix learned elsewhere wins by LPM before BGP tie-breaks even apply, next-hop unreachable so the
preferred path is invalid, iBGP path losing to eBGP by rule 7. For *inbound* traffic you don't
control the decision: use prepending/MED/communities/more-specifics and check what the neighbour
actually sees (looking glass).

## S6. "OSPF adjacency stuck in ExStart / Exchange."

MTU mismatch between the two interfaces (DBD packets exceed the smaller MTU): compare interface MTUs,
`ip ospf mtu-ignore` as a stopgap, fix MTU properly. If stuck in Init: one side's hellos aren't
received (ACL, unidirectional link, mismatched authentication). If no neighbour at all: area ID,
hello/dead timers, network type (broadcast vs p2p), subnet mask mismatch, passive interface.
If Full but no routes: wrong area type (stub blocks externals), filtering, or the routes exist but
lose to a lower AD.

## S7. "Half the servers in a rack see gaps on a multicast market-data feed; the other half are fine."

Multicast-specific: which half? Same ToR? same VLAN? Check IGMP snooping tables on the switch
(`show ip igmp snooping groups`) — are the affected ports listed for the group? Is there an IGMP
querier on the VLAN (without one, snooping entries age out ~260 s after join → feed dies until the
next join)? On the host: `ethtool -S` for `rx_missed`/`rx_no_buffer` (ring overflow at market
open → increase ring, RSS/IRQ affinity, faster app), `netstat -su` / `nstat` for UDP
`RcvbufErrors` (socket buffer too small → `net.core.rmem_max`, `SO_RCVBUF`), CPU pinning, NIC on
the wrong NUMA node. Upstream: PIM RPF failure after a routing change (multicast arrives on the
"wrong" interface), oversubscribed uplink dropping bursts (interface output drops/queue counters),
TTL scoping. Compare a good and bad host's counters side by side.

## S8. "Latency to the exchange increased by 30 µs since last week."

Is it network or host? Hardware timestamps at the NIC vs application timestamps. Path change
(`traceroute`, routing table history, a link failed over to a longer fibre — 5 µs/km), new device
in path (store-and-forward switch vs cut-through adds serialization delay: 1.2 µs per 1500 B at
10G), queuing from new traffic sharing the link (interface utilisation, microbursts invisible at
1-minute polling), LAG rehash moving the flow to a congested member, host: CPU frequency scaling,
IRQ affinity changed, kernel update disabled busy polling, NUMA placement. Check timestamps at
each hop with a tap/mirror to attribute the delay.

## S9. "Packet loss on one link, 0.1%."

`ethtool -S`/`show interfaces` on both ends: CRC/FCS errors (bad optic/fibre/connector — check
light levels, clean/replace), input/output drops (congestion/queue overflow — look at microbursts,
QoS policy), giants/runts (MTU or duplex mismatch), symbol errors. Loss only in one direction points
at the receiving side's optic/fibre strand. Loss under load but not idle = congestion. Loss
constant regardless of load = physical. Move the link to another port/optic to bisect.

## S10. "DNS is slow: every command takes 5 seconds to start."

5 s = a resolver timeout. `/etc/resolv.conf` lists a dead first nameserver; or IPv6 AAAA lookups
timing out (`options single-request`); or a search domain causing multiple lookups; or the host's
own reverse DNS missing (sshd/`sudo` doing PTR lookups). Test `dig @each-server`, `time getent hosts X`,
`resolvectl statistics`. Fix the dead server, order, or `options timeout:1 attempts:1`.

## S11. "Duplicate IP address on the network."

Symptoms: intermittent connectivity, ARP cache flipping between MACs, "IP conflict" logs.
Find: `arping -D IP`, `ip neigh` history, switch MAC table for the two MACs → which ports;
check DHCP scope vs static assignments. Fix the offender; add DHCP snooping/DAI to prevent.

## S12. "After a firewall was inserted, some long-lived sessions die every ~hour."

Stateful firewall idle timeout dropping conntrack entries for quiet sessions; the endpoints don't
know and the next packet gets a RST or silently dropped. Fix: TCP keepalives below the timeout
(`net.ipv4.tcp_keepalive_time`), raise firewall timeouts for those flows, or make the app send
heartbeats. Also check asymmetric routing: return traffic bypassing the firewall → firewall never
sees the SYN-ACK → drops mid-session.

## S13. "A switch's CPU is at 100% and management is sluggish."

Control-plane storm: broadcast/multicast storm from an L2 loop (STP disabled/misconfigured — MAC
flaps everywhere), ARP storm from a scanner, punted traffic (packets hitting the CPU because of a
missing hardware route/ACL log action), SNMP polling too aggressive, a routing protocol churning.
Look at `show processes cpu`, CoPP counters, MAC move logs, interface input rates for broadcasts.

## S14. "Server can reach the internet but not the internal 10.0.0.0/8 hosts after a VPN client started."

The VPN pushed a route (or a default route) that captures 10/8; `ip route` shows the tunnel
interface as next hop for 10.0.0.0/8 or a more-specific. Split-tunnel misconfig. Compare routing
tables before/after; `ip route get 10.1.2.3`.

## S15. "New rack: everything is cabled, nothing comes up. Where do you start?"

Physical first: link lights, `show interfaces status` (notconnect vs err-disabled vs up), optics
seated/right type (LR vs SR, speed mismatch), fibre polarity (swap tx/rx), auto-negotiation,
port configuration (shutdown, wrong VLAN/trunk, speed hard-set), then L2 (LLDP neighbours as
expected? wrong patch panel mapping), then L3 (SVI up? IP/mask, gateway), then services (DHCP
relay, PXE/TFTP for ZTP). Keep a cable map and verify it with LLDP.

## S16. "Two ISPs, you want failover. Design it and tell me how you'd test it."

eBGP to both, receive default (or full table if you need path selection), advertise your prefix
to both; prefer A with local pref 200/100 outbound, and prepend on B / MED for inbound preference;
BFD to detect failure fast; max-prefix limits, prefix filters; test by shutting the A session in a
window and confirming inbound and outbound flip (looking glass + your own probes), and by pulling
the cable (does BFD/hold timer catch it in time?). Watch out: both ISPs must accept your prefix
(IRR/RPKI records), and asymmetric paths through a stateful firewall.
