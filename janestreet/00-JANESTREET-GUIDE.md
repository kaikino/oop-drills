# Jane Street Network Engineer Internship (NYC) — interview prep guide

Written 15 Sep 2026. Sources: the JD (janestreet.com position 8620793002), Blind threads on the
network-engineer intern process, Glassdoor pages for Jane Street Linux Engineer Intern /
Production Engineer / Network Engineer, Jane Street's own "how we interview SWEs" notes,
and the five topics already reported to you (TCP header fields, BGP local preference, Linux
"used to work" debugging, shell one-liners, project story — see `../notes.md`).

## What the JD says they test

- "Understand network protocols (ARP, BGP, OSPF) at a basic level."
- "Knowledgeable of operating system fundamentals and computer architecture."
- "Strong programmer" — coding round exists even for this track.
- "Comfortable at the command line of a *nix machine."
- Day to day: site expansions and colocation builds, debugging routing protocols, provisioning
  market data feeds and third-party connections, automating support tasks, monitoring.
- Soft: curious, collaborative, humble, admits mistakes, strong communicator.

## Format (from reports)

| Round | Length | Shape |
|---|---|---|
| Tech round (network-focused) | 45–60 min, 1–2 interviewers | Conceptual and problem-based, explicitly "not a vocab test". Expect a scenario ("a host can't reach X, what do you do?"), a protocol walk-through ("what happens when…"), a "what's in a TCP header and why" style deep dive, BGP path selection with local pref, Linux debugging of something that used to work, shell one-liners, and your project story. Interviewers push on *why* until you hit the edge of what you know; saying "I don't know, but here's how I'd find out" is expected and fine. |
| Coding round | 60 min, 1 interviewer | Jane Street style: one open-ended practical problem that grows in parts as you finish each part; no LeetCode puzzles, no brain teasers. Clean, runnable code in the language you know best (Python is fine). Graded on data modelling, correctness, incremental extension without rewrites, tests you write yourself, and clear narration. Reports from the Linux track add a "Linux scripting and debugging" round: search logs on a VM to find the issue. |

## Files in this folder

Coding round (each `<name>.py` is the problem with stubs + tests; `<name>-ref.py` is the reference):
- `ip-tools.py` — CIDR math, aggregation, longest-prefix match, IPv6 compression
- `packet-parse.py` — Ethernet/IPv4/TCP/UDP parsing with struct, checksums, flows, retransmissions, fragments
- `bgp-bestpath.py` — BGP decision process, RIB updates/withdraws, inbound/outbound policy
- `ospf-spf.py` — Dijkstra over an LSDB, ECMP, incremental recompute, areas
- `market-data-gaps.py` — multicast feed sequence gaps, A/B arbitration, retransmit requests
- `config-tree.py` — hierarchical config parse/diff/generate for a fleet
- `acl-eval.py` — first-match ACLs, shadowed rules, aggregation
- `switch-sim.py` — MAC learning, aging, VLANs, LAG hashing, MAC flaps
- `link-monitor.py` — counter rates with wrap/reset, hysteresis alerts, flap dampening, top talkers
- `dns-resolver.py` — zones, CNAME chasing, iterative resolution, caching, reverse DNS
- `clock-sync.py` — NTP offset/delay, clock filter, discipline loop, PTP asymmetry
- `topology-paths.py` — topology from traceroutes, SPOFs, diverse paths, maintenance impact
- `log-hunt.py` — syslog parsing, context grep, correlation, a tiny query language
- `ping-scheduler.py` — probe scheduling, loss/RTT stats, state machine, alert suppression

Tech round:
- `tech-round.md` — question bank with model answers (TCP/IP, L2, routing, BGP, OSPF, multicast, DNS, Linux, OS, architecture, timing, data-center design)
- `scenarios.md` — troubleshooting scenarios with a method and the likely root causes
- `linux-drills.md` — shell one-liners and Linux debugging questions with answers
- `calc-drills.md` — subnetting, bandwidth-delay, serialization/propagation, and timing arithmetic drills

## How to run the coding round the Jane Street way

1. Read Part 1, restate it, ask 1–2 questions (input format, sizes, what to do on malformed input).
2. Sketch the data model in a comment first: "Route = dataclass(prefix:int, plen:int, next_hop:str, ...)".
3. Write the smallest correct version, then a test with the interviewer's example. Run it.
4. When Part 2 arrives, extend, don't rewrite. If the model has to change, say why before changing it.
5. Narrate trade-offs briefly ("dict of sets keyed by prefix length is simpler than a trie; trie wins at 500k routes").
6. Name the edge cases you're not handling and how you'd handle them.

## How to run the tech round

- Answer in layers: one-sentence answer → mechanism → why it's designed that way → how it fails → how you'd observe it (which command/counter).
- When given a scenario, run the method in `scenarios.md`: define "works", find what changed, localize by layer/hop, bisect, verify, then explain root cause.
- Keep a mental map of "which tool shows this": `ip -br addr`, `ip route get`, `ip neigh`, `ss -tnpi`, `tcpdump -ni`, `ethtool -S`, `mtr`, `dig +trace`, `journalctl`, `dmesg -T`, `strace -p`, `perf top`, `nstat`, `/proc/net/snmp`.

## Plan (order of study)

1. `tech-round.md` sections 1–5 (TCP/IP, L2, ARP, BGP, OSPF) out loud.
2. `scenarios.md` — talk through 6 scenarios with a timer (5 min each).
3. `linux-drills.md` — type every one-liner, check output on your machine.
4. Coding: `ip-tools.py`, `bgp-bestpath.py`, `packet-parse.py`, `market-data-gaps.py` (the four most on-theme). Then `log-hunt.py`, `config-tree.py`.
5. `calc-drills.md` — do all with pen and paper.
6. Project story (see `../behavioral.md` section 2; for Jane Street emphasise measurement, root-causing, and honesty about what you didn't know).
