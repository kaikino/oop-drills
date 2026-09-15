# CS fundamentals Q&A for the TikTok backend intern round (八股文, short answers)

Format: question → the 2–4 sentence answer an interviewer wants, then a likely follow-up.
Cover these out loud without reading. If you can only do one section, do Networking + MySQL + Redis.

---

## 1. Networking

**TCP three-way handshake. Why three, not two?**
Client SYN(seq=x) → server SYN-ACK(seq=y, ack=x+1) → client ACK(ack=y+1). Three because both sides must confirm the other's initial sequence number and that the other can receive; with two, a delayed stale SYN could open a half-connection on the server that the client never uses (wasted resources, wrong ISN).
Follow-up: *SYN flood?* Attacker sends SYNs without ACKing; server's half-open queue fills. Mitigation: SYN cookies (encode state in the ISN), shorter timeouts, backlog tuning.

**Four-way close. Why four? What is TIME_WAIT?**
Each direction closes independently: FIN → ACK, then the other side FIN → ACK. The passive side may still have data to send after ACKing the first FIN, so its FIN comes separately. The active closer waits 2×MSL in TIME_WAIT so the last ACK can be retransmitted if lost and so stale segments die before the 4-tuple is reused. Many TIME_WAITs on a server means the *server* is closing first (e.g. short-lived connections); fix with keep-alive/connection pooling or `tcp_tw_reuse`.

**TCP vs UDP.**
TCP: connection, ordered, reliable (ACK + retransmit), flow control (rwnd), congestion control (cwnd; slow start, congestion avoidance, fast retransmit/recovery), byte stream. UDP: connectionless, datagrams, no guarantees, lower latency, less header (8 B vs 20 B). Use UDP for DNS, video/voice, QUIC (HTTP/3 builds reliability on UDP in user space).

**How does TCP guarantee reliability?**
Sequence numbers + cumulative ACKs, retransmission on timeout (RTO from RTT estimates) and on 3 duplicate ACKs (fast retransmit), checksum, sliding window for flow control, congestion control.

**Flow control vs congestion control.**
Flow control protects the *receiver* (advertised window). Congestion control protects the *network* (cwnd, AIMD: additive increase, multiplicative decrease on loss).

**Sticky packets / message boundaries ("粘包").**
TCP is a byte stream; the application must frame messages: length prefix, delimiter, or fixed size.

**HTTP vs HTTPS.**
HTTPS = HTTP over TLS. TLS handshake: client hello (ciphers, random) → server hello + certificate (public key signed by a CA) → client verifies the cert chain, generates a pre-master secret (RSA-encrypted with server pubkey, or ECDHE key exchange), both derive symmetric session keys → encrypted traffic. Asymmetric crypto only for key exchange, symmetric (AES) for data because it's fast. Cert verification: CA signature, domain match, validity, revocation.
Follow-up: *Why not just symmetric?* Key distribution. *Why not just asymmetric?* Too slow.

**HTTP methods and idempotency.**
GET (safe, idempotent, cacheable), POST (create/act, not idempotent), PUT (replace, idempotent), PATCH (partial), DELETE (idempotent), HEAD, OPTIONS. POST on `/orders` creates a new member of the collection; a retry of POST can create a duplicate, which is why payment APIs use an idempotency key header.

**Common status codes.**
200 OK, 201 Created, 204 No Content, 301/302 redirect (permanent/temporary), 304 Not Modified, 400 Bad Request, 401 Unauthorized (not authenticated), 403 Forbidden (authenticated but not allowed), 404, 409 Conflict, 429 Too Many Requests, 500, 502 Bad Gateway, 503 Unavailable, 504 Gateway Timeout.

**HTTP/1.1 vs HTTP/2 vs HTTP/3.**
1.1: keep-alive, pipelining (rarely used), head-of-line blocking per connection. 2: binary framing, multiplexing streams on one TCP connection, header compression (HPACK), server push; still TCP HOL blocking on loss. 3: QUIC over UDP, per-stream loss recovery, 0-RTT resumption, connection migration.

**What happens when you type a URL and hit enter?**
DNS (browser cache → OS cache → resolver → root → TLD → authoritative), TCP handshake (+ TLS), HTTP request, server (load balancer → gateway → service → cache/DB), response, browser parses HTML, fetches assets, renders. Mention CDN for static assets and cookies/session for auth.

**DNS runs on what?** UDP 53 for queries (TCP for zone transfers and responses > 512 B / DNS over TCP/TLS/HTTPS).

**Cookies vs session vs JWT.**
Cookie = client-stored key/value sent with each request. Session = server-side state keyed by a session id in a cookie. JWT = self-contained signed token; stateless, but revocation is hard (short expiry + refresh token, or a blacklist).

**What's in a TCP header?** Source/dest port, seq, ack, header length, flags (SYN/ACK/FIN/RST/PSH/URG), window, checksum, urgent pointer, options (MSS, window scale, SACK, timestamps).

**Load balancing at L4 vs L7.** L4 forwards by IP/port (fast, no content awareness). L7 parses HTTP (routing by path/header, TLS termination, sticky sessions). Algorithms: round robin, weighted RR, least connections, consistent hashing (see `consistent-hashing.py`, `weighted-round-robin.py`).

**Long polling vs WebSocket vs SSE.** Long polling holds the request until data; WebSocket is full-duplex over one upgraded TCP connection; SSE is one-way server→client over HTTP. Live-stream chat / like counters use WebSocket or long-poll with batching.

---

## 2. Operating systems

**Process vs thread.**
Process = resource container (address space, file descriptors); thread = unit of scheduling sharing the process's memory. Threads are cheaper to create/switch and share data directly (need locks); processes are isolated (a crash doesn't take others down) and communicate via IPC (pipes, sockets, shared memory, message queues). Coroutines are user-space scheduled and even cheaper.

**Context switch cost.** Save/restore registers, switch page tables (TLB flush for processes), cache pollution. Thread switches within the same process avoid the page-table switch.

**Deadlock: four necessary conditions, and how to avoid.**
Mutual exclusion, hold-and-wait, no preemption, circular wait. Avoid by breaking one: acquire locks in a global order (breaks circular wait), try-lock with timeout/back-off, acquire all at once, or detect and recover (kill/rollback). Banker's algorithm for avoidance in theory.

**Mutex vs spinlock vs semaphore vs RW lock vs reentrant lock.**
Mutex blocks (sleeps) the waiter; spinlock busy-waits (good for very short critical sections on multicore); semaphore counts N permits; RW lock lets many readers or one writer (watch writer starvation); reentrant lock can be re-acquired by the owner (Java `synchronized`, Python `RLock`).

**CPU scheduling algorithms.** FCFS, SJF (optimal average wait, needs prediction, starves long jobs → HRRN fixes with aging), Round Robin (time slice; too small = switch overhead, too large = FCFS), priority (+ aging), multilevel feedback queue (Linux CFS uses a red-black tree by virtual runtime).

**Virtual memory, paging, page fault.** Each process has a virtual address space mapped by page tables (multi-level) to physical frames; TLB caches translations. A page fault traps to the OS to load the page (from disk/swap) — replacement policies LRU (approximated by clock/second chance), FIFO (Belady's anomaly).

**What happens when a user program writes a file?** `write()` syscall → user→kernel mode switch → VFS → file system → data goes into the page cache (marked dirty) → returns; the kernel flushes dirty pages to the block device later (or on `fsync`). Reading: page cache hit, else block layer → disk → DMA into page cache → copy to user buffer. `mmap` and `sendfile` avoid copies (zero-copy; Kafka uses sendfile).

**I/O models.** Blocking, non-blocking (poll loop), I/O multiplexing (`select`/`poll`/`epoll`: one thread watches many fds; epoll is O(ready) not O(n)), signal-driven, asynchronous (`io_uring`, Windows IOCP). Redis and Nginx use an event loop over epoll. BIO for few long-lived connections, NIO/AIO for many connections.

**Zero-copy.** `sendfile`/`splice` move data kernel→socket without copying through user space; saves 2 copies and 2 context switches.

**What does Ctrl+C do?** Terminal driver sends SIGINT to the foreground process group; default action terminates; a handler can catch it for graceful shutdown (finish in-flight requests, close connections). SIGTERM is what orchestrators send; SIGKILL cannot be caught.

**Stack vs heap; what's in a stack frame?** Return address, saved frame pointer, arguments, locals; grows per call; overflow on deep recursion (Python default limit ~1000 — reason to prefer iterative BFS/DFS on big inputs). Heap: dynamic allocation, fragmentation, managed by malloc/GC.

**Garbage collection (Java asked in TikTok OA).** GC reclaims heap objects unreachable from GC roots (thread stacks, static fields, JNI refs). Mark-and-sweep, copying (young generation), mark-compact (old), generational hypothesis. Python: reference counting + a cycle collector.

**Memory: how does `malloc` work?** Free lists / size classes / arenas; `brk`/`mmap` for big blocks; fragmentation; see `memory-allocator.py`.

---

## 3. MySQL / databases

**ACID.** Atomicity (undo log; all-or-nothing), Consistency (constraints hold before/after), Isolation (locks + MVCC), Durability (redo log + WAL: write log before data, fsync on commit). Consistency example: transfer money — total balance unchanged even if the transaction fails halfway.

**Isolation levels and the anomalies.**
Read Uncommitted (dirty reads), Read Committed (no dirty; non-repeatable reads possible), Repeatable Read (MySQL default; same row reads the same within a txn via MVCC snapshot; InnoDB also mostly prevents phantoms with gap/next-key locks), Serializable (full locking). Phantom = a range query returns new rows on re-run.

**MVCC.** Each row has hidden trx_id and roll pointer to undo-log versions; a transaction takes a read view (active txn ids) and sees the newest version that was committed before its snapshot. Readers don't block writers. RC creates a new read view per statement; RR per transaction.

**Index: B+ tree, why not hash / BST / skiplist / B tree?**
B+ tree: high fan-out (hundreds of keys per 16 KB page) → 3–4 levels for billions of rows → few disk reads; leaves are a linked list → range scans; internal nodes hold only keys → more fan-out than a B tree. Hash: no range queries/ordering. BST/RB tree: too deep (one node per disk page). Skiplist: fine in memory (Redis), poor on disk locality.

**Clustered vs secondary index; 回表 (lookup back).**
InnoDB clusters the table on the primary key (leaf = whole row). A secondary index leaf stores the PK, so a lookup through it then goes to the clustered index unless the index *covers* the query (covering index → no lookback). Prefer short, monotonically increasing PKs (page splits with random UUIDs).

**Leftmost prefix rule.** Composite index (a, b, c) serves `WHERE a=`, `a= AND b=`, `a= AND b= AND c=`, `a= AND b>`, `a= ORDER BY b`; NOT `b=` alone. Range on `b` stops use of `c`.

**When is an index not used?** Function/arithmetic on the column, implicit type cast (`WHERE phone = 123` on a varchar), leading-wildcard `LIKE '%x'`, `OR` with a non-indexed column, low selectivity (optimizer prefers full scan), `!=`/`NOT IN` sometimes. Check with `EXPLAIN` (type: const/ref/range/index/ALL; key; rows; Extra: Using index / Using filesort / Using temporary).

**How a query executes in MySQL.** Connector → (query cache, removed in 8.0) → parser → optimizer (chooses index, join order) → executor calls the storage engine (InnoDB) → buffer pool pages → results. Writes: undo log (rollback + MVCC), redo log (crash recovery, WAL), binlog (replication, point-in-time recovery; three formats: STATEMENT, ROW, MIXED). Two-phase commit between redo and binlog.

**Locks.** Shared/exclusive row locks (`SELECT ... FOR UPDATE` = X lock; `LOCK IN SHARE MODE`), gap locks and next-key locks in RR to stop phantoms, table locks, intention locks. Deadlock detection rolls back the cheaper transaction. Optimistic locking = a `version` column and `UPDATE ... WHERE id=? AND version=?` (see `order-state-machine.py`).

**Transactions in practice for e-commerce.** Order + inventory + payment across services → not one DB transaction: use TCC (try/confirm/cancel), saga with compensations, or a message-based eventual consistency (outbox → MQ → idempotent consumer). Local transaction + outbox table is the pragmatic answer.

**Slow query, what do you do?** `EXPLAIN`, add/adjust index, avoid `SELECT *`, cover the index, paginate with a keyset (`WHERE id > ? LIMIT n`) instead of big `OFFSET`, split hot tables (sharding by user_id/order_id), read replicas, cache.

**Sharding.** Vertical (by table/column) vs horizontal (by rows on a shard key). Problems: cross-shard joins/transactions, global unique ids (snowflake, see `id-generator.py`), resharding (consistent hashing).

**Master–slave replication.** Binlog shipped to replicas, replayed (relay log); async by default → replication lag → read-your-own-writes issues (route to master after write, or wait for GTID).

**NoSQL vs SQL.** SQL for transactions and relations; document stores (MongoDB) for flexible schemas; wide-column (Cassandra/HBase) for write-heavy time series; key-value (Redis) for cache. CAP: under partition, choose consistency or availability; most e-commerce inventory is CP, product browsing AP.

---

## 4. Redis

**Data structures and uses.** String (counters INCR, session, cache), Hash (product fields), List (queue/timeline), Set (dedupe, tags; SINTER for common followers), ZSet (leaderboards, delayed queues by score = timestamp, rate limiting by sliding log), plus Bitmap (daily sign-in, bloom), HyperLogLog (UV count ~0.8% error in 12 KB), Geo, Streams (MQ-like).

**Why is Redis fast?** In-memory; single-threaded command execution (no lock contention, no context switches) with epoll I/O multiplexing; efficient encodings (ziplist/listpack, intset, skiplist + dict for ZSet); 6.0+ multi-threaded I/O for network parsing only. Bottleneck is network/memory, not CPU.

**ZSet implementation.** Dict (member → score, O(1)) + skiplist (ordered by score, O(log n) insert/range/rank). Skiplist over a balanced tree: simpler, easy range iteration, easy to implement rank, similar complexity. Small ZSets use a listpack.

**Persistence.** RDB = periodic snapshot (fork + copy-on-write; compact, fast restart, loses data since last snapshot). AOF = append every write command (fsync always / every second / never; bigger, slower restart; rewrite compaction). Hybrid (RDB preamble + AOF tail) is the usual choice.

**Expiry and eviction.** Expiry: lazy on access + active periodic sampling of keys. Eviction when maxmemory hit: noeviction, allkeys-lru / volatile-lru (approximate LRU by sampling), lfu, random, ttl.

**Cache-aside and consistency with the DB.** Read: cache → miss → DB → set cache. Write: update DB, then **delete** cache (not update, avoids stale-order writes). Race: a read that misses just before the DB write and fills the cache after the delete → stale; mitigations: delayed double delete, short TTL, or subscribe to binlog (Canal) to invalidate. See `cache-patterns.py`.

**Penetration / breakdown / avalanche (穿透/击穿/雪崩).**
Penetration: queries for keys that don't exist hit the DB → cache nulls with short TTL, bloom filter. Breakdown: one hot key expires, thundering herd → mutex/single-flight rebuild, logical expiry, never-expire hot keys. Avalanche: many keys expire together or Redis down → TTL jitter, multi-level cache, circuit breaker/rate limit, HA cluster.

**Distributed lock.** `SET key uuid NX PX ttl`; release with a Lua script comparing the uuid (don't delete someone else's lock); TTL renewal (watchdog) for long tasks; Redlock across masters is debated; for correctness across failover prefer ZooKeeper/etcd. Fencing tokens for the storage side.

**Hot key / big key.** Hot key: local cache + replicate the key to N copies (key_1..key_N) + read replicas. Big key: split; delete asynchronously (UNLINK).

**Redis vs Memcached.** Redis: rich types, persistence, replication, Lua, pub/sub; Memcached: multi-threaded simple KV strings.

**Cluster.** 16384 hash slots, each master owns a range; clients redirect (MOVED); replicas per master; gossip failover. Sentinel for HA without sharding.

---

## 5. Message queues

**Why use an MQ?** Decoupling (order service doesn't call inventory/notification directly), async (faster response), peak shaving (flash sale bursts queued), ordering per key, fan-out to multiple consumers.

**Kafka basics.** Topic → partitions (unit of parallelism and ordering) → offsets. Producer chooses partition by key hash (same key → same partition → ordered). Consumer group: each partition to exactly one consumer in the group. Broker persists to disk (sequential append + page cache + zero-copy). Replication with leader/ISR; `acks=all` for durability.

**Delivery semantics.** At-most-once (commit offset before processing), at-least-once (process then commit → duplicates on crash; the default you should assume), exactly-once (idempotent producer + transactions within Kafka; end-to-end you still make the consumer idempotent — unique key/DB constraint, dedup table, version check). See `event-dedup.py`, `mq-patterns.py`.

**How do messages get lost, and the fix at each hop?** Producer: no ack / fire-and-forget → `acks=all`, retries. Broker: leader dies before replication → min ISR ≥ 2, replication factor 3, flush policy. Consumer: auto-commit before processing → manual commit after processing.

**Ordering.** Only within a partition; global order needs one partition (throughput limit) — use per-order-id keys so events for one order are ordered.

**Backlog / consumer lag.** Scale consumers up to the partition count, batch processing, increase partitions (careful: key→partition mapping changes), skip/degrade, dead-letter queue for poison messages.

**Delayed messages.** RocketMQ delay levels, Kafka has none natively (use a delayed topic + scheduler, or Redis ZSET / timing wheel; see `delayed-queue.py`).

**Kafka vs RocketMQ vs RabbitMQ.** Kafka: log-based, highest throughput, streaming. RocketMQ: Kafka-like plus delayed/transactional messages (ByteDance/Alibaba heritage). RabbitMQ: AMQP broker, flexible routing, lower throughput, good for task queues.

---

## 6. Distributed systems & e-commerce specifics

**Idempotency.** Same request applied N times has the effect of once. Implement with an idempotency key (client-generated UUID) stored with the result; DB unique constraint; state-machine checks (only CREATED → PAID); version numbers. Payments/refunds must be idempotent because clients retry on timeout.

**Flash sale / seckill (秒杀) in one minute.** Static page + CDN; gateway rate limit and per-user limits; answer questions/captcha to spread traffic; stock pre-loaded into Redis, `DECR` (Lua for check-and-decrement) to filter the 99% that will fail; queue the winners to MQ; order service consumes and writes DB with `UPDATE stock SET n=n-1 WHERE id=? AND n>0`; short payment TTL and release on timeout; idempotent order creation. Accept "order placed" async, notify result. See `inventory.py`, `design-scenarios.md`.

**Oversell prevention.** Atomic decrement (Redis Lua or DB conditional update), never read-then-write; reservations with expiry; reconcile job.

**Distributed transactions.** 2PC (blocking, coordinator SPOF), TCC (try reserve → confirm → cancel; business-level compensations; asked at TikTok round 2), Saga (chain of local txns with compensations), transactional messages / outbox (eventual consistency). Rule: prefer eventual consistency with idempotent, retriable steps.

**CAP / BASE.** Partition tolerance is mandatory; choose C (refuse writes when unsure — inventory, payment) or A (serve possibly stale — feed, product page). BASE: basically available, soft state, eventual consistency.

**Distributed unique ids.** DB auto-increment (SPOF, not shardable), UUID (random, bad index locality), Snowflake (time + worker + seq; clock rollback problem), Leaf-segment (DB hands out ranges). See `id-generator.py`.

**Rate limiting.** Fixed window (burst at boundary), sliding log (exact, memory), sliding window counter (approx), token bucket (bursts allowed up to capacity), leaky bucket (smooth). Distributed: Redis + Lua. See `token-bucket.py`, `limiter.py`.

**Consistent hashing.** Ring + virtual nodes so adding/removing a node moves ~1/N keys. See `consistent-hashing.py`.

**Timeouts, retries, circuit breakers.** Always set timeouts; retry with exponential backoff + jitter only idempotent calls; circuit breaker opens after error rate threshold; bulkhead isolates thread pools; degrade non-core features (recommendations) under load.

**Observability.** Logs (structured, trace id), metrics (P50/P99 latency, QPS, error rate — a TikTok interviewer asked how the candidate measured P99 before/after), traces (OpenTelemetry). Know how to say "P99 went from 800 ms to 120 ms after adding an index / cache".

**Microservices communication.** REST/JSON vs gRPC/protobuf (binary, streaming, strongly typed, HTTP/2); service discovery; API gateway (auth, rate limit, routing). ByteDance uses Go + Kitex (RPC) + Hertz (HTTP) heavily — worth a sentence if asked "what do you know about our stack".

---

## 7. Language questions (Python; Java in case they ask, ByteDance likes Java/Go)

**Python.** GIL: one thread runs bytecode at a time → CPU-bound work uses multiprocessing; I/O-bound uses threads or asyncio. `list` is a dynamic array (amortized O(1) append), `dict` an open-addressing hash table with insertion order (3.7+), `set` similarly. `deque` O(1) both ends; `heapq` min-heap (negate for max); `bisect` for sorted lists; `OrderedDict.move_to_end` for LRU. Generators for lazy streams. `is` vs `==`. Mutable default argument pitfall. `__slots__` for memory. Decorators, context managers (`with` → `__enter__/__exit__`). Shallow vs deep copy. Exceptions are cheap for control flow in Python but don't swallow them silently.

**Java one-liners (only if asked).** `HashMap`: array of buckets, linked list → red-black tree when a bucket > 8 entries, resize at 0.75 load factor doubling; `ConcurrentHashMap` uses CAS + per-bin `synchronized`; `volatile` = visibility + ordering, not atomicity; `synchronized` is reentrant; thread states NEW/RUNNABLE/BLOCKED/WAITING/TIMED_WAITING/TERMINATED; `wait/notify` need the monitor; thread pool params (core, max, queue, keep-alive, rejection policy); JVM memory: heap (young/old), metaspace, stacks; GC roots.

**Go one-liners (ByteDance's main backend language).** Goroutines (M:N scheduled, ~2 KB stacks), channels (buffered/unbuffered, `select`), `sync.Mutex`/`RWMutex`/`WaitGroup`, `context` for cancellation/timeouts, `defer`, slices vs arrays, maps not concurrency-safe, error values not exceptions, GC is concurrent tri-color mark-sweep.

---

## 8. AI-assisted development (in the JD — expect one question)

"How do you use AI coding tools?" → Concrete: generate boilerplate/tests and then review every line, use it to explain unfamiliar code and to draft docs, ask it for edge cases, never paste secrets, verify claims by running tests, keep the design decisions yourself. Mention one time it was wrong and how you caught it. "Backend for AI features" → serving an LLM behind an API: async queue, timeouts, caching identical prompts, rate limits per user, logging prompts/outputs for evaluation, fallbacks when the model is slow.
