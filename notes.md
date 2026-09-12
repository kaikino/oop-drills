# Coding round prep — progress log (as of 13 Sep 2026)

Files live in Keita's connected folder `~/research/prep` (kv-store.py, drills.py, editor.py, limiter.py, units.py, lru-dll.py, playback.py, logs.py, plus *-ref.py reference solutions written by Claude).

## Problems completed (mock format, Claude as interviewer, code read from the folder)
1. KV store with TTL → heap-based reclaim with stale-entry check → bounded reclaim in get. Parts 1–2 coded, 3 discussed.
2. Fluency drills: OrderedDict LRU, dataclass, BFS/DFS, heapq tiebreaker, Counter/defaultdict/bisect.
3. Bracket checker → fold regions → stateful Editor. Parts 1–2 clean; part 3 over-engineered (segment linked list, 7 bugs); simple 20-line version never typed (Keita chose to skip).
4. Rate limiter: per-client deque → config + global window → idle-client reclaim (OrderedDict discussion). Parts 1–2 coded with one bug each; 3 discussed well.
5. Unit conversion: direct → DFS chain → contradiction check (relative tolerance, reject) → O(1) via weighted union-find with path compression. Union-find coded and passing after two logic fixes (re-parent root not unit; None instead of assert). Strongest code of the week.
6. Hand-rolled doubly-linked-list LRU: passing after four rounds (data-shape/bookkeeping bugs, pointer logic right first time).
7. Adaptive playback controller: choose → tick with buffer model → flapping/hysteresis → EWMA smoothing. Coded parts 1–2; discussion 3–4. (Claude's original buffer model was inconsistent; Keita caught it.)
8. BGP log parser: parse_line/parse coded; Store (per-device bisect, Counter, outage sweep) had 6 line-level bugs, reference written by Claude. Parts 3–4 (quarantine, idempotency, out-of-memory) not yet discussed.

## Recurring bug categories (Keita's ledger)
- Method attribute not called (`self.now` vs `self.now()`) — ×2
- Comparison direction inverted (`<`/`>`, `min`/`max`) — ×4
- Tuple mutation (`t[1] = x`) — ×2
- Data shape undecided before typing (dict value type, sentinel vs pointer) — ×3, causes cascades
- Changed a variable's shape, left an old use (`cur[0]` on a string) — ×2
- Index vs value confusion (ladder index vs bitrate) — ×1
- Unflushed trailing buffer / unreached loop exit — ×1 each
- `list.join` vs `" ".join(list)`; `typing.cast` is a no-op — ×1 each

## Assessment
Design/discussion is consistently strong (catches spec flaws, proposes O(1) structures, names trade-offs). Gap is plan-to-lines fidelity under a clock; single trace questions catch most bugs. Clarifying questions are good and sometimes exposed flawed specs — don't count them against him.

## Plan going forward
Coding: 20-min daily typing drill only (LRU / Store / limiter from blank). Shift main effort to the networking + Linux rounds (master guide), starting with the five directly-reported topics: TCP header fields, BGP local preference, Linux "used to work" debugging, shell one-liners, project story. Run the guide's mock sets A–F in the same ask/answer/push format.