# Design scenarios for a TikTok e-commerce backend intern (5–15 minute verbal answers)

These are the "no code, just talk" prompts reported in TikTok/ByteDance intern rounds. For each:
the prompt, a 60-second answer, then the deep dive an interviewer pushes toward, then the
traps. Practice by talking for 5 minutes per scenario with a timer.

---

## 1. Design a like / repost / save counter (asked verbatim in a TikTok backend intern round 2)

**60-second answer.** Two paths: a *write* path (user likes a video) and a *read* path (show the count, and "did I like this?"). Writes go to a `likes` table (user_id, video_id, created_at, unique(user_id, video_id)) for truth and idempotency, and increment a Redis counter `like:count:{video_id}` (INCR). Reads hit Redis; miss → count from DB (or a `video_stats` summary row) → backfill. Async: the like event goes to Kafka; a consumer updates the DB summary table and other derived data (feeds, notifications). "Did I like" → Redis Set or Bloom filter per user, or the unique DB lookup.

**Deep dive.**
- *High concurrency on one video (hot key)*: shard the counter into N sub-keys (`like:count:{vid}:{0..N-1}`), INCR a random shard, sum on read (cache the sum for 1 s). Or local in-process aggregation flushed every 100 ms.
- *Robustness*: if Redis loses data, rebuild from DB/binlog; counts are allowed to be eventually consistent, likes themselves are not lost because DB/Kafka is the source of truth.
- *Idempotency*: unique index on (user_id, video_id); unlike = delete + DECR; retries safe.
- *Read amplification*: batch-get counters for a feed page (MGET), pre-aggregate.
- *Hot vs cold*: cold videos' counters expire from Redis; use DB summary row.
- *Exact vs approximate*: display counts can be approximate; billing/creator payouts must be exact → reconcile nightly.

**Traps.** Updating a DB row per like (row lock contention on hot videos); reading count with `SELECT COUNT(*)`; forgetting the unlike path; forgetting per-user "liked?" state.

---

## 2. Flash sale / limited-stock drop without overselling (Global E-Commerce classic)

**60-second answer.** Separate "reserve stock" from "create order" from "pay". Stock lives in Redis as a counter pre-loaded from DB; a Lua script does check-and-decrement atomically so at most `stock` requests pass. Winners get a token and their order is enqueued to Kafka; the order service writes the order in MySQL and decrements the DB stock with a conditional update (`UPDATE ... SET qty=qty-1 WHERE sku=? AND qty>0`) as a second guard. Payment must complete within a TTL or the reservation is released (delayed message / ZSET scan). Losers get an immediate "sold out" from the gateway.

**Deep dive.**
- Traffic shaping: CDN + static page, gateway rate limit per user and IP, button enabled by server time, answer-a-question to spread clicks.
- Per-user purchase limit: Redis Set/`SADD` returns 0 for repeat.
- Hot single SKU key: split stock into buckets (10 buckets of 100) and pick a random bucket, retry another bucket if empty.
- Consistency between Redis stock and DB stock: Redis is the fast gate, DB is the truth; reconcile job; on Redis failure fail closed (reject) for this SKU.
- Idempotent order creation keyed by (user_id, sku, sale_id).
- Payment timeout → release both Redis and DB stock; make release idempotent.
- Observability: QPS at gate, pass rate, MQ lag, payment conversion.

**Traps.** Read-then-write on stock (race); locking the DB row for the whole checkout; not releasing reservations; synchronous everything.

---

## 3. Payment idempotency / TCC (the "explain TCC" question was asked at TikTok round 2)

**60-second answer.** A payment request carries an idempotency key. The service first inserts a `payment_request` row with a unique index on the key; a duplicate insert means "already processed → return stored result". State machine: INIT → PROCESSING → SUCCESS/FAILED; a PROCESSING row with a stale heartbeat is retried. Cross-service (order + wallet + inventory): TCC — Try reserves resources in each service (freeze funds, reserve stock), Confirm applies, Cancel releases; the coordinator retries Confirm/Cancel until they succeed, so Confirm/Cancel must be idempotent, and Cancel must tolerate a Try that never arrived (empty rollback) and a Try arriving after Cancel (suspension).

**Alternatives.** Saga (local txn + compensation), transactional outbox + MQ (most common), 2PC (avoid). Mention that "at-least-once + idempotent consumer" is the everyday answer.

---

## 4. Order timeout auto-cancel (unpaid orders after 30 min)

Options: delayed message (RocketMQ delay level / Kafka delayed topic), Redis ZSET with score = deadline polled every second, DB cron scan `WHERE status=CREATED AND created_at < now-30m` in batches, timing wheel in memory (single node only). Requirements: idempotent cancel (order may have been paid at 29:59 — check the state under a conditional update), release stock, notify. See `delayed-queue.py`, `order-state-machine.py`.

---

## 5. Shopping cart service

Cart per user in Redis Hash (`cart:{uid}` → sku → qty) with TTL for guests, persisted to MySQL for logged-in users; merge guest cart on login. Price is *not* stored in the cart; fetched at render/checkout (price changes). Checkout snapshot: freeze prices and promotions into the order. Promotion engine evaluates coupons deterministically (see `cart-pricing.py`). Inventory check at checkout, not at add-to-cart.

---

## 6. Product search / autocomplete

Inverted index (Elasticsearch) fed from MySQL via binlog → Kafka → indexer; prefix autocomplete from a trie or ES completion suggester with top-K by popularity cached in Redis per prefix (`search-autocomplete.py`); personalization and ranking as a later stage; typo tolerance via n-grams/edit distance.

---

## 7. Rate limiting an API gateway

Token bucket per user/API key in Redis via Lua (atomic read-modify-write), with local in-memory buckets as a first filter; return 429 with Retry-After; separate limits per tier; sliding window for accurate "1000/day". See `token-bucket.py`.

---

## 8. Ticketing / high-speed-rail seat sale (ByteDance e-commerce round asked this)

Same skeleton as the flash sale but with *segments*: a seat is bookable for a route if free on every segment; represent seat availability as a bitmask per seat over segments; check `mask & route_mask == 0` then set; contention on hot trains → per-train shard/queue; overselling prevention identical.

---

## 9. Feed / notification fan-out (in case they ask a TikTok-generic one)

Fan-out on write for normal creators (push to followers' inbox lists in Redis), fan-out on read for celebrities (merge at read time); hybrid; pagination by (timestamp, id) cursor, not offset.

---

## 10. Design a URL shortener (the default "easy design" question)

Base62 of a snowflake id (or counter ranges per node), 301 vs 302 (302 keeps analytics), Redis cache for hot codes, DB keyed on code, expiry, abuse rate limits. See `math-misc.py` base62 and `id-generator.py`.

---

## How to answer any design prompt in this round (interns are graded on structure, not scale)

1. Clarify: reads vs writes, exactness needed, scale (QPS, data size), latency.
2. API: name 2–3 endpoints with parameters.
3. Data model: tables/keys with the unique index that gives idempotency.
4. Happy path with a diagram in words: client → gateway → service → cache → DB → MQ → consumers.
5. The one hard part (hot key / consistency / ordering) and its fix.
6. Failure modes: cache down, MQ lag, duplicate requests, partial failure.
7. What you'd measure.
