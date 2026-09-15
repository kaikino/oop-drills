# Calculation drills (pen and paper; answers at the bottom)

Interviewers use these to check you can reason quantitatively about networks, not to test speed.
Say the formula, then the number, then the unit.

## A. Subnetting

1. 10.20.30.40/22 — network, broadcast, first/last usable, number of hosts.
2. Split 192.168.0.0/24 into subnets that each hold at least 50 hosts. How many, what are they?
3. Is 172.16.5.200 in 172.16.4.0/22?
4. Summarize 10.1.0.0/24, 10.1.1.0/24, 10.1.2.0/24, 10.1.3.0/24 into one prefix. Can you also summarize 10.1.4.0/24 with them?
5. Smallest prefix that contains both 10.0.0.0 and 10.0.255.255? And both 10.0.255.255 and 10.1.0.0?
6. /31 point-to-point link: what are the two addresses for 10.9.9.6/31?
7. How many /26 subnets in a /20?
8. A host has 10.0.1.5/23; is 10.0.0.200 on-link or via the gateway?
9. Write 255.255.248.0 as a prefix length; write /27 as a dotted mask.
10. IPv6: compress 2001:0db8:0000:0000:0001:0000:0000:0001. What's the /64 network?

## B. Throughput and delay

11. Serialization delay of a 1500-byte frame at 1 Gbit/s, 10 Gbit/s, 100 Gbit/s. (Include 20 B preamble+IFG? State your assumption.)
12. Propagation delay across 100 km of fibre (refractive index ≈ 1.47, c ≈ 3×10^8 m/s). New York to Chicago (~1200 km fibre route) one way?
13. Bandwidth-delay product for a 10 Gbit/s link with 80 ms RTT: bytes in flight needed to fill it. Can a TCP with no window scaling fill it?
14. Max TCP throughput with a 64 KB window and 20 ms RTT.
15. A 1 GB file over a 100 Mbit/s link, ignoring overhead: seconds? With 1500-byte frames and 40 bytes of TCP/IP headers per frame, what's the goodput ratio?
16. A switch is cut-through; how much latency does a 64-byte vs a 9000-byte frame add at 10G compared with store-and-forward?
17. A link shows 1% packet loss. Rough TCP throughput bound (Mathis: rate ≈ MSS/(RTT·√p)·1.22) with MSS 1460, RTT 50 ms.
18. A 25 Gbit/s NIC: how many 64-byte packets per second at line rate (with 20 B overhead per frame)? How long does the CPU have per packet?
19. Leaf with 48×25G downlinks and 8×100G uplinks: oversubscription ratio.
20. Market data at 2 million messages/s, 100 bytes each: bits per second? Fits on 1G? 10G?

## C. Timing and counters

21. A 64-bit byte counter at 100 Gbit/s: how long until it wraps? A 32-bit one at 1 Gbit/s?
22. Clock drifts 20 ppm; after 1 hour without sync, how far off? How long until 100 µs (the MiFID II threshold for some venues)?
23. NTP sample: t1 = 100.000, t2 = 100.050, t3 = 100.051, t4 = 100.011. Offset and delay?
24. A PTP path has 1 µs more delay in one direction than the other. What error does the naive offset have?
25. Polling a 10G interface counter every 60 s shows 50% average utilisation. Could there be drops? Why?

## D. Addressing arithmetic you should do mentally

26. 2^n table for n = 0..16; number of hosts in /8, /16, /24, /25, /28, /30.
27. Hex ↔ decimal for common octets: 0xff, 0xc0, 0xa8, 0x0a, 0x7f.
28. Multicast MAC for 239.1.2.3 (01:00:5e + low 23 bits).
29. Ephemeral port range on Linux (default) and how many concurrent connections to one dst IP:port that allows.
30. How many /24s does an ISP get with a /19?

---

## Answers

1. /22 → mask 255.255.252.0; 30 in binary 00011110, block of 4 in the 3rd octet → network 10.20.28.0, broadcast 10.20.31.255, usable 10.20.28.1–10.20.31.254, 2^10−2 = 1022 hosts.
2. ≥50 hosts → /26 (62 usable). Four: 192.168.0.0/26, .64/26, .128/26, .192/26.
3. 172.16.4.0/22 covers 172.16.4.0–172.16.7.255 → yes.
4. 10.1.0.0/22. Adding 10.1.4.0/24 would need 10.1.0.0/21, which also includes 10.1.5–7.0/24 (over-summarization) → not exactly; /21 only if you accept covering unused space.
5. 10.0.0.0/16. For 10.0.255.255 and 10.1.0.0: they differ at bit 16 of the 2nd octet (0 vs 1) → 10.0.0.0/15.
6. 10.9.9.6 and 10.9.9.7 (RFC 3021, no network/broadcast).
7. 2^(26−20) = 64.
8. /23 → 10.0.0.0–10.0.1.255 → on-link, host ARPs directly.
9. 255.255.248.0 = /21 (11111000 in 3rd octet). /27 = 255.255.255.224.
10. 2001:db8::1:0:0:1 (the longest zero run is the two groups after db8; the later run of two ties, leftmost wins). Network 2001:db8::/64.
11. 1500 B = 12,000 bits: 12 µs at 1G, 1.2 µs at 10G, 0.12 µs at 100G. With 20 B preamble/IFG → 1520 B = 12,160 bits: 12.16 µs / 1.216 µs / 0.1216 µs.
12. Speed in fibre ≈ c/1.47 ≈ 2.04×10^8 m/s ≈ 4.9 µs/km. 100 km ≈ 490 µs. 1200 km ≈ 5.9 ms one way (≈12 ms RTT).
13. 10 Gbit/s × 0.08 s = 0.8 Gbit = 100 MB in flight. No: 64 KB max window without scaling → 64 KB/0.08 s = 6.5 Mbit/s.
14. 65,535 B / 0.02 s ≈ 3.3 MB/s ≈ 26 Mbit/s.
15. 8×10^9 bits / 10^8 bit/s = 80 s. Goodput ratio ≈ 1460/1500 ≈ 97% (≈ 94% counting Ethernet header+FCS+preamble+IFG).
16. Store-and-forward must receive the whole frame before forwarding: 64 B → 51 ns, 9000 B → 7.2 µs at 10G. Cut-through forwards after the header (~64 B) so both cost ≈ 51 ns + fabric latency.
17. 1460 B × 1.22 / (0.05 × √0.01) = 1781 B / 0.005 = 356 KB/s ≈ 2.8 Mbit/s. Loss dominates throughput; that's why 1% loss "feels" much worse than 1%.
18. Frame on wire 64 + 20 = 84 B = 672 bits → 25×10^9/672 ≈ 37.2 Mpps; ≈ 27 ns per packet (≈ 80 cycles at 3 GHz). Hence kernel bypass for line-rate small packets.
19. Downlink 48×25 = 1200 G; uplink 8×100 = 800 G → 1.5:1.
20. 2×10^6 × 100 B × 8 = 1.6 Gbit/s → exceeds 1G, fits 10G (plus headers ~20% more; and bursts at open are several × average).
21. 2^64 B / (12.5×10^9 B/s) ≈ 1.48×10^9 s ≈ 47 years. 2^32 B at 125 MB/s ≈ 34 s → why 64-bit counters (and why 32-bit SNMP ifInOctets are useless at 1G+).
22. 20 ppm = 20 µs per second → 72 ms per hour. 100 µs / 20 µs/s = 5 s. (So holdover needs a better oscillator: OCXO ~0.01 ppm.)
23. offset = ((t2−t1)+(t3−t4))/2 = (0.050 + 0.040)/2 = 0.045 s (server ahead by 45 ms). delay = (t4−t1)−(t3−t2) = 0.011 − 0.001 = 0.010 s.
24. Half the asymmetry: 0.5 µs bias in the offset estimate (the algorithm assumes symmetric delay).
25. Yes. 60-second averages hide microbursts; a link can be 100% busy for 5 ms and drop from queue overflow while averaging 50%. Look at queue/drop counters or sub-second sampling.
26. Hosts: /8 → 16,777,214; /16 → 65,534; /24 → 254; /25 → 126; /28 → 14; /30 → 2. 2^10 = 1024, 2^16 = 65,536.
27. 0xff = 255, 0xc0 = 192, 0xa8 = 168, 0x0a = 10, 0x7f = 127.
28. 239.1.2.3 → low 23 bits of 1.2.3 (first octet's top bit dropped: 1 → 0x01) → 01:00:5e:01:02:03.
29. 32768–60999 → 28,232 ports → that many concurrent connections to one (dst IP, dst port) from one source IP; TIME_WAIT can exhaust it.
30. 2^(24−19) = 32.
