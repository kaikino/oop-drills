# TikTok Backend SWE Intern (Global E-Commerce, Seattle) — coding round 1 guide

Written 14 Sep 2026, interview is 15 Sep 2026. Everything below is from public interview
reports (Glassdoor, LeetCode Discuss, Nowcoder/牛客, 1point3acres, interviewfox, lodely,
the perixtar Tech-OA-Interview-Questions bank) plus the JD. Sources at the bottom.

## What round 1 actually looks like (consensus across ~20 reports)

| Segment | Time | What happens |
|---|---|---|
| Intro + resume | 10–15 min | "Walk me through a project." Expect 2–3 drill-down questions on a project on your resume (why this design, what broke, what you'd change). E-commerce team asks "any e-commerce experience?" — have an honest answer plus one thing you know about TikTok Shop. |
| CS fundamentals (八股) | 5–15 min | Short verbal questions. Most common: TCP 3-way handshake / 4-way close, HTTP vs HTTPS, HTTP status codes, process vs thread, deadlock, MySQL index / B+ tree / clustered index, ACID + isolation levels, Redis data structures + why it's fast + persistence, message queue basics, "what happens when you type a URL". |
| Coding | 30–40 min | **One LeetCode medium** with follow-ups, occasionally two mediums or one easy + one medium. Live in a shared editor (HackerRank CodePair / their own "Lark" doc-style editor), you must run it yourself against your own examples. Interviewer asks complexity, edge cases, then a twist. |
| Your questions | 3–5 min | Ask something about the team (see behavioral.md). |

Recurring facts from reports:
- **No question bank.** Interviewers pick freely. Classic mediums dominate; the same problem
  gets re-asked for years (LRU since 2019).
- Difficulty: "easy–medium" for intern rounds per Glassdoor; ByteDance-internal rounds skew
  medium–hard. Assume medium with a hard-ish extension.
- Coding is usually done in the interviewer's shared doc, **no autocomplete, no running**
  in some setups — practice typing from a blank file (you've been doing this).
- Rounds are unlocked one at a time; round 2 (if any) tends to be system-design-ish
  ("design a like counter", "design inventory for a flash sale") + more coding.

## Concrete problems reported at TikTok/ByteDance intern & backend rounds (2024–Sept 2026)

Coding (all have files in this folder):
- LRU cache (many reports) → follow-up "entries expire after 1 s" (`lru-ttl.py`), LFU
- Daily temperatures + follow-ups (`monotonic-stack.py`)
- Sliding window / two pointers (round 1), linked list with follow-ups (round 2) — Glassdoor intern report
- Set matrix zeroes LC73 (`prefix-sum-matrix.py`)
- Coin change LC322 (`dp-1d.py`)
- Best time to buy/sell stock IV LC188 (`dp-1d.py`)
- Build tree from preorder + inorder (`trees.py`); binary tree max width with nulls LC662
- Path existence in undirected graph; binary tree target-sum paths; alien dictionary;
  min removals for non-overlapping intervals; enumerate directed paths/cycles (all ByteDance, Sept 2026)
- Restore addresses with K segments (LC93 generalised) (`strings.py`)
- Weighted round-robin seller task scheduler (ByteDance, Sept 2026) (`weighted-round-robin.py`)
- Leftmost memory block allocator (TikTok, Sept 2026) (`memory-allocator.py`)
- Reverse letters in pairs; count alternating tile groups; local maxima in sensor data;
  lowest number in open range; count one-swap pairs; rhombic area sum (TikTok OA, Sept 2026)
- Do any 4 points form a square (`math-misc.py`); "atoms colliding" = asteroid collision (`stack-queue.py`)
- Digit-sum inverse: given b = a + digitsum(a), find a (`math-misc.py`)
- Queue from two stacks; reverse words O(1) space; eight queens; longest substring w/o repeats;
  repeated substring pattern; longest common substring; inorder traversal iterative
- Shortest path in 0-1 matrix; task dependencies with execution times (`task-scheduler-deps.py`)
- 10 billion ints in 4 GB: does x exist → bitmap (`bits-bigdata.py`)
- Sorted structure with a skiplist (`skiplist.py`); hashtag trend detector (`streaming.py`)
- Single element in sorted array LC540; linked-list sum variants
- SQL: rank rows 3–6 by score; creators with >= N videos by region (HAVING) (`sql.py`)

Design-ish (round 2, but be ready to talk for 5 minutes):
- Counting system for likes/reposts/saves under high concurrency (`hit-counter.py` Part 4, `design-scenarios.md`)
- Flash-sale inventory without overselling (`inventory.py`, `design-scenarios.md`)
- Payment idempotency / TCC (`order-state-machine.py`, `design-scenarios.md`)

## Topic weights (how to spend the remaining hours)

1. **Hash map + sliding window + two pointers** (25%) — `sliding-window.py`, `two-pointers.py`, `prefix-sum-matrix.py`
2. **Linked list + LRU/LFU family** (15%) — `linked-list.py`, `lru-ttl.py`, existing `lru-dll.py`, `lfu.py`
3. **Stack/queue/monotonic stack** (10%) — `monotonic-stack.py`, `stack-queue.py`
4. **Trees + BFS/DFS + graph** (15%) — `trees.py`, `graphs.py`, `matrix-bfs.py`, `union-find.py`
5. **Heap / top-K / binary search** (10%) — `heaps-topk.py`, `binary-search.py`
6. **DP + backtracking** (10%) — `dp-1d.py`, `dp-2d.py`, `backtracking.py`
7. **Design-a-class / backend sims** (10%) — `hit-counter.py`, `token-bucket.py`, `inventory.py`, `cart-pricing.py`, `order-state-machine.py`, `delayed-queue.py`, `event-dedup.py`, `id-generator.py`, `timemap.py`, `consistent-hashing.py`, `weighted-round-robin.py`, `memory-allocator.py`, `streaming.py`, `skiplist.py`, `search-autocomplete.py`
8. **Fundamentals talk** (5%) — `fundamentals.md`, `cache-patterns.py`, `mq-patterns.py`, `sql.py`, `concurrency.py`

## Tonight's plan (about 4 hours, in this order)

1. 60 min: `sliding-window.py` Parts 1,2,5; `two-pointers.py` Parts 2,4; `monotonic-stack.py` Part 1 with follow-ups. Timed, blank file, no autocomplete.
2. 40 min: `linked-list.py` Parts 2,3,4; `lru-ttl.py` Part 1 (this is *the* TikTok follow-up).
3. 40 min: `trees.py` Parts 2,3,4; `graphs.py` Parts 3,4; `matrix-bfs.py` Part 4.
4. 30 min: `intervals.py` Parts 1,3,4; `heaps-topk.py` Parts 2,4; `binary-search.py` Parts 2,3,7.
5. 30 min: read `fundamentals.md` out loud, answer each question in 2–3 sentences without looking.
6. 20 min: `behavioral.md` — write your 90-second project story and the e-commerce answer.
7. Sleep. Tomorrow morning: 20-min typing drill (`lru-dll.py` from blank, then `hit-counter.py` Part 1).

## How to run the coding segment (your ledger says this is where points leak)

1. Restate the problem in one sentence, ask at most 2–3 clarifying questions (input size, duplicates, empty input, return type).
2. Say the data shape out loud before typing: "dict: key -> [value, expiry]". Write it as a comment on line 1.
3. Say the approach and complexity, get a nod, then type.
4. Trace one small example by hand *before* saying "done". Check: comparison direction, `self.now` vs `self.now()`, tuple mutation, flush of the trailing window.
5. Volunteer edge cases and the follow-up you expect ("if the stream were infinite I'd…").

## Sources
- Glassdoor: TikTok Backend Developer Intern / Software Engineer Backend Intern interview pages (sliding window + two pointer round 1, linked list round 2; Redis/Kafka/networking questions; "e-commerce experience?")
- LeetCode Discuss: ByteDance/TikTok intern all-rounds threads; "Tiktok Backend Engineer interview experience"
- Nowcoder: 字节跳动 TikTok 后端实习 一面/二面 (LC73; like-counter design; MySQL execution, clustered index, Redis structures, LC662 width, OOP shapes, bitmap 10B ints, LRU + 1s TTL)
- Nowcoder: 字节TikTok暑期实习一二三面 (queue via two stacks, HTTP/HTTPS, digit-sum inverse, build tree from pre/inorder, atom collision)
- interviewguide.cn 字节电商后端 (HTTPS, idempotency, TCP, deadlock, clustered index, SQL rank 3–6, LRU, Redis single thread, AOF, reverse words O(1), eight queens, LCSubstring, high-speed-rail ticketing design)
- github.com/perixtar/Tech-OA-Interview-Questions (TikTok & ByteDance entries dated 2–12 Sep 2026)
- interviewfox.ai TikTok HackerRank 2026 (GC MCQ, HTTP MCQ, SQL HAVING, unique-digits sum, grid paths, largest follower network via stdin)
- lodely.com / aonecode.com TikTok OA lists (stock cooldown, decode ways II, sliding window max, remove K digits, K closest, round-robin load balancer, longest OR, max XOR)
- xiaolincoding.com 字节跳动 Java 面试 (MySQL/Redis/OS/网络 question list)
- codinginterview.com, algo.monster, tryexponent TikTok guides (process, 45-min rounds, CoderPad/HackerRank, no question bank)
