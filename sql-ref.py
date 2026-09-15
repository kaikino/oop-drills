from __future__ import annotations

"""SQL practice (sqlite3 in-memory) - reference solution. See sql.py for the
problem text, schema and seed data description.

Every q.. function returns SQL text. The harness at the bottom runs it against
the seeded DB and asserts exact rows. SQLite dialect only (no ILIKE, no
DATE_SUB, no TOP): window functions need SQLite >= 3.25 (2018); we detect the
version and skip window-only tasks on older builds.

Conventions in this file:
  - "revenue" = SUM(qty * unit_price_cents) over items of orders whose
    status <> 'CANCELLED'. Note it is the *item* price, not products.price.
  - datetimes are stored as 'YYYY-MM-DD HH:MM:SS' text; SQLite compares text,
    so '2024-03-01' < '2024-03-01 00:00:00' - always compare like with like.
  - NOW is a fixed literal so results are deterministic.
"""

import sqlite3
from typing import Any, List, Sequence, Tuple

NOW = "2024-03-31 00:00:00"
HAS_WINDOW = sqlite3.sqlite_version_info >= (3, 25, 0)


# ---------------------------------------------------------------------------
# Schema + seed (given; identical in sql.py)
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE users       (id INTEGER PRIMARY KEY, name TEXT, region TEXT, created_at TEXT);
CREATE TABLE sellers     (id INTEGER PRIMARY KEY, name TEXT, region TEXT);
CREATE TABLE products    (id INTEGER PRIMARY KEY, seller_id INTEGER, name TEXT, price_cents INTEGER, category TEXT);
CREATE TABLE orders      (id INTEGER PRIMARY KEY, user_id INTEGER, created_at TEXT, status TEXT);
CREATE TABLE order_items (order_id INTEGER, product_id INTEGER, qty INTEGER, unit_price_cents INTEGER);
CREATE TABLE videos      (id INTEGER PRIMARY KEY, creator_id INTEGER, views INTEGER, created_at TEXT);
CREATE TABLE creators    (id INTEGER PRIMARY KEY, name TEXT, region TEXT);
CREATE TABLE likes       (user_id INTEGER, video_id INTEGER, created_at TEXT);   -- no unique key: duplicates allowed

INSERT INTO users VALUES
 (1,'Ann','US','2024-01-05 00:00:00'),(2,'Bob','US','2024-01-10 00:00:00'),
 (3,'Cai','SG','2024-02-01 00:00:00'),(4,'Dee','UK','2024-02-15 00:00:00'),
 (5,'Eve','US','2024-03-01 00:00:00'),(6,'Fay','SG','2024-03-10 00:00:00'),
 (7,'Gus','UK','2024-03-20 00:00:00');
INSERT INTO sellers VALUES (1,'Alpha','US'),(2,'Beta','SG'),(3,'Gamma','UK'),(4,'Delta','US'),(5,'Epsilon','SG');
INSERT INTO products VALUES
 (1,1,'Phone Case',1500,'Accessories'),(2,1,'Charger',2500,'Accessories'),
 (3,2,'T-Shirt',2000,'Apparel'),(4,2,'Hoodie',4500,'Apparel'),
 (5,3,'Lipstick',1200,'Beauty'),(6,3,'Serum',3000,'Beauty'),
 (7,1,'Earbuds',6000,'Accessories'),(8,2,'Cap',1500,'Apparel'),
 (9,3,'Mascara',1200,'Beauty'),(10,4,'Sticker',300,'Stationery'),
 (11,1,'Cable',800,'Accessories');
INSERT INTO orders VALUES
 (1,1,'2024-01-10 10:00:00','SHIPPED'),  (2,2,'2024-01-15 09:00:00','SHIPPED'),
 (3,1,'2024-02-02 12:00:00','PAID'),     (4,3,'2024-02-03 08:00:00','CANCELLED'),
 (5,1,'2024-03-01 10:00:00','PAID'),     (6,1,'2024-03-02 10:00:00','PAID'),
 (7,1,'2024-03-03 10:00:00','SHIPPED'),  (8,2,'2024-03-02 11:00:00','PAID'),
 (9,2,'2024-03-04 11:00:00','CANCELLED'),(10,4,'2024-03-05 15:00:00','PAID'),
 (11,5,'2024-03-06 16:00:00','CREATED'), (12,3,'2024-03-20 09:00:00','CREATED'),
 (13,2,'2024-02-20 09:00:00','CREATED'), (14,4,'2024-03-29 10:00:00','SHIPPED'),
 (15,5,'2024-01-20 10:00:00','CREATED'), (16,3,'2024-03-06 10:00:00','PAID'),
 (17,3,'2024-03-07 10:00:00','PAID'),    (18,3,'2024-03-08 10:00:00','CANCELLED'),
 (19,1,'2024-03-01 18:00:00','PAID');
INSERT INTO order_items VALUES
 (1,1,2,1500),(1,3,1,2000),(1,11,1,800),
 (2,7,1,6000),
 (3,5,3,1200),
 (4,4,1,4500),
 (5,2,1,2500),
 (6,6,1,3000),
 (7,8,2,1500),
 (8,4,1,4000),(8,11,3,800),
 (9,1,1,1500),
 (10,3,2,2000),(10,9,2,1200),
 (11,9,1,1200),
 (12,10,2,300),
 (13,5,1,1200),
 (14,6,2,3000),
 (15,10,5,300),
 (16,3,1,2000),
 (17,8,1,1500),
 (18,2,2,2500),
 (19,9,3,1200);
INSERT INTO creators VALUES (1,'Ava','US'),(2,'Ben','US'),(3,'Chen','CN'),(4,'Dana','US'),(5,'Eli','UK');
INSERT INTO videos VALUES
 (1,1,1000,'2024-03-05 00:00:00'),(2,1,5000,'2024-03-10 00:00:00'),
 (3,2,20000,'2024-03-15 00:00:00'),(4,2,9000,'2024-02-10 00:00:00'),
 (5,3,50000,'2024-03-20 00:00:00'),(6,3,40000,'2024-03-21 00:00:00'),
 (7,4,3000,'2024-03-01 00:00:00'),(8,4,3000,'2024-03-28 00:00:00'),
 (9,5,8000,'2024-03-02 00:00:00'),(10,5,8000,'2024-03-03 00:00:00'),
 (11,1,100,'2024-02-28 00:00:00'),(12,4,999999,'2024-01-01 00:00:00');
INSERT INTO likes VALUES
 (1,1,'2024-03-01 00:00:00'),(1,1,'2024-03-01 00:00:01'),(2,1,'2024-03-02 00:00:00'),
 (2,3,'2024-03-02 00:00:00'),(2,3,'2024-03-02 00:00:05'),(2,3,'2024-03-02 00:00:09'),
 (3,2,'2024-03-03 00:00:00');
"""


def make_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    return conn


# Reusable CTE: revenue per product over non-cancelled orders.
# PITFALL: an inner join drops products that never sold; if you need them use
# LEFT JOIN products->items and put the status filter in the ON clause of the
# orders join AND guard the SUM with CASE WHEN o.id IS NOT NULL (or pre-filter
# items in a CTE as q01 does). In this seed every product sold at least once.
PROD_REV = """
WITH prod_rev AS (
    SELECT p.id, p.name, p.category, p.seller_id,
           SUM(oi.qty * oi.unit_price_cents) AS revenue
    FROM products p
    JOIN order_items oi ON oi.product_id = p.id
    JOIN orders o       ON o.id = oi.order_id
    WHERE o.status <> 'CANCELLED'
    GROUP BY p.id, p.name, p.category, p.seller_id
)"""


# ---------------------------------------------------------------------------
# Part 1: revenue per seller, descending; sellers with no sales show 0
# PITFALL: filter cancelled orders in a CTE, not in WHERE (WHERE on the
# right side of a LEFT JOIN turns it into an INNER JOIN and drops Epsilon),
# and not only in ON (items of cancelled orders would keep their oi row with
# o NULL and still be summed).
# ---------------------------------------------------------------------------
def q01_revenue_per_seller() -> str:
    return """
    WITH items AS (
        SELECT oi.product_id, oi.qty * oi.unit_price_cents AS amount
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status <> 'CANCELLED'
    )
    SELECT s.id, s.name, COALESCE(SUM(i.amount), 0) AS revenue
    FROM sellers s
    LEFT JOIN products p ON p.seller_id = s.id
    LEFT JOIN items i    ON i.product_id = p.id
    GROUP BY s.id, s.name
    ORDER BY revenue DESC, s.id
    """


# ---------------------------------------------------------------------------
# Part 2: top 3 products by revenue per category (window function)
# ROW_NUMBER gives 1,2,3,4 (ties broken by ORDER BY -> add a tiebreaker!).
# RANK gives 1,1,3,4 (gaps); DENSE_RANK gives 1,1,2,3 (no gaps). "Top 3 with
# ties included" -> DENSE_RANK <= 3; "exactly 3 rows" -> ROW_NUMBER.
# ---------------------------------------------------------------------------
def q02_top3_products_per_category() -> str:
    return PROD_REV + """,
    ranked AS (
        SELECT category, name, revenue,
               ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC, id) AS rn
        FROM prod_rev
    )
    SELECT category, name, revenue, rn
    FROM ranked
    WHERE rn <= 3
    ORDER BY category, rn
    """


# ---------------------------------------------------------------------------
# Part 3: users with no orders - two idioms (anti-join)
# LEFT JOIN ... IS NULL: test a NOT NULL column of the right table (its PK).
# NOT EXISTS: correlated; usually the clearest and optimises to a semi-join.
# NOT IN (subquery) is the trap: if the subquery yields any NULL, NOT IN
# returns no rows at all (x NOT IN (1, NULL) is UNKNOWN).
# ---------------------------------------------------------------------------
def q03a_users_without_orders_left_join() -> str:
    return """
    SELECT u.id, u.name
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    WHERE o.id IS NULL
    ORDER BY u.id
    """


def q03b_users_without_orders_not_exists() -> str:
    return """
    SELECT u.id, u.name
    FROM users u
    WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)
    ORDER BY u.id
    """


# ---------------------------------------------------------------------------
# Part 4: products ranked 3rd..6th by revenue (the ByteDance question)
# LIMIT 4 OFFSET 2 is the quick answer; it needs a deterministic ORDER BY
# (tiebreaker) and OFFSET scans and discards the first rows (fine for small
# offsets; deep pagination should use a keyset: WHERE (revenue, id) < (?, ?)).
# The window version exposes the rank and handles ties explicitly.
# MySQL: LIMIT 2, 4 also works; standard SQL: OFFSET 2 ROWS FETCH NEXT 4 ROWS ONLY.
# ---------------------------------------------------------------------------
def q04a_ranked_3_to_6_limit_offset() -> str:
    return PROD_REV + """
    SELECT name, revenue
    FROM prod_rev
    ORDER BY revenue DESC, id
    LIMIT 4 OFFSET 2
    """


def q04b_ranked_3_to_6_window() -> str:
    return PROD_REV + """,
    ranked AS (
        SELECT name, revenue,
               ROW_NUMBER() OVER (ORDER BY revenue DESC, id) AS rn
        FROM prod_rev
    )
    SELECT rn, name, revenue
    FROM ranked
    WHERE rn BETWEEN 3 AND 6
    ORDER BY rn
    """


# ---------------------------------------------------------------------------
# Part 5: second highest price per category, NULL when there is none
# DENSE_RANK over DISTINCT prices; the category list must come from the
# outer side of a LEFT JOIN so a category with a single price still appears
# (with NULL). Beauty has two products at 1200 -> DENSE_RANK 2 for both, so
# aggregate (MAX) or DISTINCT before joining.
# Non-window alternative: correlated MAX(price) WHERE price < (SELECT MAX ...).
# ---------------------------------------------------------------------------
def q05_second_highest_price_per_category() -> str:
    return """
    WITH cats AS (SELECT DISTINCT category FROM products),
    ranked AS (
        SELECT category, price_cents,
               DENSE_RANK() OVER (PARTITION BY category ORDER BY price_cents DESC) AS rk
        FROM products
    ),
    second AS (SELECT category, MAX(price_cents) AS price_cents FROM ranked WHERE rk = 2 GROUP BY category)
    SELECT c.category, s.price_cents AS second_price
    FROM cats c
    LEFT JOIN second s ON s.category = c.category
    ORDER BY c.category
    """


# ---------------------------------------------------------------------------
# Part 6: monthly revenue with running total
# strftime('%Y-%m') buckets; SUM() OVER (ORDER BY month ROWS BETWEEN
# UNBOUNDED PRECEDING AND CURRENT ROW) is the running total. The default
# frame for ORDER BY is RANGE ... CURRENT ROW, which merges peer rows with
# equal month; months are unique here so both are equal, but say ROWS.
# ---------------------------------------------------------------------------
def q06_monthly_revenue_running_total() -> str:
    return """
    WITH monthly AS (
        SELECT strftime('%Y-%m', o.created_at) AS month,
               SUM(oi.qty * oi.unit_price_cents) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status <> 'CANCELLED'
        GROUP BY month
    )
    SELECT month, revenue,
           SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running
    FROM monthly
    ORDER BY month
    """


# ---------------------------------------------------------------------------
# Part 7: US creators with >= 2 videos in the last 30 days, by total views
# WHERE filters rows before grouping (region, date); HAVING filters groups
# after aggregation (COUNT >= 2). Boundary: the video at exactly NOW-30d is
# included by >=. Old videos must be excluded from SUM as well as COUNT, so
# the date filter goes in WHERE, not HAVING.
# ---------------------------------------------------------------------------
def q07_us_creators_two_recent_videos() -> str:
    return f"""
    SELECT c.id, c.name, COUNT(v.id) AS n_videos, SUM(v.views) AS total_views
    FROM creators c
    JOIN videos v ON v.creator_id = c.id
    WHERE c.region = 'US'
      AND v.created_at >= datetime('{NOW}', '-30 days')
    GROUP BY c.id, c.name
    HAVING COUNT(v.id) >= 2
    ORDER BY total_views DESC, c.id
    """


# ---------------------------------------------------------------------------
# Part 8: users who bought in BOTH categories (relational division, small)
# GROUP BY user HAVING COUNT(DISTINCT category) = 2 after restricting to the
# two categories. Alternatives: INTERSECT of two user sets; two EXISTS.
# Trap: Cai's only Accessories purchase is in a CANCELLED order.
# ---------------------------------------------------------------------------
def q08_users_bought_both_categories() -> str:
    return """
    SELECT u.id, u.name
    FROM users u
    JOIN orders o       ON o.user_id = u.id AND o.status <> 'CANCELLED'
    JOIN order_items oi ON oi.order_id = o.id
    JOIN products p     ON p.id = oi.product_id
    WHERE p.category IN ('Accessories', 'Apparel')
    GROUP BY u.id, u.name
    HAVING COUNT(DISTINCT p.category) = 2
    ORDER BY u.id
    """


# ---------------------------------------------------------------------------
# Part 9: daily active users (placed an order) in March + 7-row rolling avg
# ROWS BETWEEN 6 PRECEDING AND CURRENT ROW averages the last 7 *rows* that
# exist, not 7 calendar days: a gap (03-08 -> 03-20) is invisible. For true
# calendar windows join a calendar/dates table (or RANGE over julianday).
# ---------------------------------------------------------------------------
def q09_dau_rolling_7() -> str:
    return """
    WITH daily AS (
        SELECT date(created_at) AS day, COUNT(DISTINCT user_id) AS dau
        FROM orders
        WHERE created_at >= '2024-03-01 00:00:00'
        GROUP BY day
    )
    SELECT day, dau,
           ROUND(AVG(dau) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS avg7
    FROM daily
    ORDER BY day
    """


# ---------------------------------------------------------------------------
# Part 10: duplicate detection + dedupe keeping the earliest row
# GROUP BY the "should be unique" columns HAVING COUNT(*) > 1. To delete,
# keep MIN(rowid) per group. (MySQL: DELETE t1 FROM likes t1 JOIN likes t2
# ON same key AND t1.id > t2.id; or add a UNIQUE index with INSERT IGNORE.)
# ---------------------------------------------------------------------------
def q10a_find_duplicate_likes() -> str:
    return """
    SELECT user_id, video_id, COUNT(*) AS cnt
    FROM likes
    GROUP BY user_id, video_id
    HAVING COUNT(*) > 1
    ORDER BY user_id, video_id
    """


def q10b_delete_duplicate_likes() -> str:
    return """
    DELETE FROM likes
    WHERE rowid NOT IN (SELECT MIN(rowid) FROM likes GROUP BY user_id, video_id)
    """


# ---------------------------------------------------------------------------
# Part 11: users who ordered on 3 consecutive days
# Step 1 is DISTINCT (user, date): Ann has two orders on 03-01, and a naive
# LAG over orders would see 03-01, 03-01, 03-02 (diff 0 then 1) and miss her.
# LAG version: compare day with LAG 1 and LAG 2 using julianday differences.
# Self-join version: d, d+1, d+2 all exist. (Gaps-and-islands generalises to
# "N consecutive days": day - ROW_NUMBER() is constant within a run.)
# ---------------------------------------------------------------------------
def q11a_three_consecutive_days_lag() -> str:
    return """
    WITH days AS (SELECT DISTINCT user_id, date(created_at) AS day FROM orders),
    w AS (
        SELECT user_id, day,
               LAG(day, 1) OVER (PARTITION BY user_id ORDER BY day) AS d1,
               LAG(day, 2) OVER (PARTITION BY user_id ORDER BY day) AS d2
        FROM days
    )
    SELECT DISTINCT u.id, u.name
    FROM w
    JOIN users u ON u.id = w.user_id
    WHERE julianday(day) - julianday(d1) = 1
      AND julianday(d1) - julianday(d2) = 1
    ORDER BY u.id
    """


def q11b_three_consecutive_days_self_join() -> str:
    return """
    WITH days AS (SELECT DISTINCT user_id, date(created_at) AS day FROM orders)
    SELECT DISTINCT u.id, u.name
    FROM days a
    JOIN days b ON b.user_id = a.user_id AND b.day = date(a.day, '+1 day')
    JOIN days c ON c.user_id = a.user_id AND c.day = date(a.day, '+2 day')
    JOIN users u ON u.id = a.user_id
    ORDER BY u.id
    """


# ---------------------------------------------------------------------------
# Part 12: % cancelled orders per seller, 2 decimals
# An order is "the seller's" if it contains any of their products. Count
# DISTINCT orders: order 1 has two Alpha items (rows), one order. 100.0 * ...
# forces float division (100 * a / b would be integer division in SQLite and
# MySQL-with-DIV). CASE WHEN inside COUNT(DISTINCT ...) counts only matches
# (COUNT ignores NULLs).
# ---------------------------------------------------------------------------
def q12_pct_cancelled_per_seller() -> str:
    return """
    SELECT s.id, s.name,
           ROUND(100.0 * COUNT(DISTINCT CASE WHEN o.status = 'CANCELLED' THEN o.id END)
                       / COUNT(DISTINCT o.id), 2) AS pct_cancelled
    FROM sellers s
    JOIN products p     ON p.seller_id = s.id
    JOIN order_items oi ON oi.product_id = p.id
    JOIN orders o       ON o.id = oi.order_id
    GROUP BY s.id, s.name
    ORDER BY s.id
    """


# ---------------------------------------------------------------------------
# Part 13: pivot revenue per seller per status (CASE WHEN inside SUM)
# One column per status value; SUM(CASE WHEN status = X THEN amount END)
# yields NULL for a seller with no rows of that status -> COALESCE to 0.
# LEFT JOINs keep Epsilon. The cancelled column is shown here on purpose.
# ---------------------------------------------------------------------------
def q13_pivot_revenue_by_status() -> str:
    return """
    SELECT s.id, s.name,
           COALESCE(SUM(CASE WHEN o.status = 'CREATED'   THEN oi.qty * oi.unit_price_cents END), 0) AS created,
           COALESCE(SUM(CASE WHEN o.status = 'PAID'      THEN oi.qty * oi.unit_price_cents END), 0) AS paid,
           COALESCE(SUM(CASE WHEN o.status = 'SHIPPED'   THEN oi.qty * oi.unit_price_cents END), 0) AS shipped,
           COALESCE(SUM(CASE WHEN o.status = 'CANCELLED' THEN oi.qty * oi.unit_price_cents END), 0) AS cancelled
    FROM sellers s
    LEFT JOIN products p     ON p.seller_id = s.id
    LEFT JOIN order_items oi ON oi.product_id = p.id
    LEFT JOIN orders o       ON o.id = oi.order_id
    GROUP BY s.id, s.name
    ORDER BY s.id
    """


# ---------------------------------------------------------------------------
# Part 14: N-th highest distinct product price with a CTE (LC177 shape)
# Wrapping the LIMIT/OFFSET query in a scalar subquery makes it return one
# row with NULL when fewer than N distinct prices exist (a bare LIMIT query
# would return zero rows). DENSE_RANK() = N is the window alternative.
# ---------------------------------------------------------------------------
def q14_nth_highest_price(n: int) -> str:
    assert isinstance(n, int) and n >= 1          # never interpolate untrusted input
    return f"""
    WITH distinct_prices AS (SELECT DISTINCT price_cents FROM products)
    SELECT (
        SELECT price_cents FROM distinct_prices
        ORDER BY price_cents DESC
        LIMIT 1 OFFSET {n - 1}
    ) AS nth_highest
    """


# ---------------------------------------------------------------------------
# Part 15: expire stale CREATED orders (UPDATE; check rowcount)
# Always UPDATE with a WHERE on an indexed column and verify cursor.rowcount.
# In production: batch by id range to keep the transaction short (row locks
# + undo growth), and make it idempotent (re-running changes 0 rows).
# ---------------------------------------------------------------------------
def q15_cancel_stale_created_orders() -> str:
    return f"""
    UPDATE orders
    SET status = 'CANCELLED'
    WHERE status = 'CREATED'
      AND created_at < datetime('{NOW}', '-30 days')
    """


# ---------------------------------------------------------------------------
# Part 16: index choice (written answer)
# ---------------------------------------------------------------------------
def q16_index_choice() -> str:
    return """
    Query: SELECT ... FROM orders WHERE seller_id = ? AND created_at > ?
    Best index: a composite B+ tree index on (seller_id, created_at), in that
    order. Rule: equality columns first, then ONE range column, then columns
    needed for ORDER BY / covering. The index is sorted by seller_id, and
    within each seller by created_at, so the engine seeks to (seller_id, ts)
    and range-scans forward: O(log N + k). Reversing it to (created_at,
    seller_id) would scan every order after ts for all sellers, then filter.
    Leftmost prefix: (seller_id, created_at) also serves WHERE seller_id = ?
    alone, but NOT WHERE created_at > ? alone (the prefix is missing), and a
    third column after the range column cannot be used for seeking. Two
    single-column indexes are worse: the optimiser picks one and filters the
    rest (or does an index merge). Make it covering by appending the selected
    columns, e.g. (seller_id, created_at, status), to avoid the lookback to
    the clustered index.
    """


# ---------------------------------------------------------------------------
# DB theory - model answers
#
# JOIN types: INNER keeps matching pairs; LEFT keeps every left row (NULLs on
#   the right when unmatched) - a WHERE on a right column other than IS NULL
#   silently turns it inner; RIGHT is LEFT mirrored; FULL OUTER keeps both
#   sides (SQLite >= 3.39, MySQL: UNION of LEFT and RIGHT); CROSS is the
#   cartesian product; a self join joins a table to itself (Part 11).
# WHERE vs HAVING: WHERE filters rows before GROUP BY and cannot use
#   aggregates; HAVING filters groups after aggregation. Put non-aggregate
#   predicates in WHERE so fewer rows are grouped. Evaluation order:
#   FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY
#   -> LIMIT (so column aliases work in ORDER BY but not in WHERE, except in
#   SQLite/MySQL which relax it).
# COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col): COUNT(*) counts rows;
#   COUNT(col) counts rows where col IS NOT NULL; COUNT(DISTINCT col) counts
#   distinct non-NULL values. COUNT(1) == COUNT(*). In InnoDB COUNT(*) walks
#   the smallest index; it is not O(1) (MyISAM cached it).
# NULL semantics: three-valued logic. NULL = NULL is UNKNOWN, so use IS NULL;
#   WHERE drops UNKNOWN rows; NOT IN with a NULL in the list returns nothing;
#   aggregates ignore NULL (SUM of all NULLs is NULL, hence COALESCE);
#   GROUP BY and DISTINCT treat NULLs as equal; ORDER BY puts NULLs first
#   (SQLite/MySQL ASC) - use NULLS LAST or a CASE.
# B+ tree: balanced, high fan-out (hundreds per 16 KB page) so 3-4 levels
#   hold billions of rows; all records live in leaves which are linked for
#   range scans; internal nodes hold only keys, so they fit in the buffer
#   pool. Versus hash index: no range/prefix/ORDER BY support. Versus B-tree:
#   B-tree stores data in internal nodes too -> lower fan-out, no leaf chain.
# Clustered vs secondary index (InnoDB): the clustered index IS the table,
#   ordered by primary key (leaf = full row); choose a short, monotonically
#   increasing PK (auto-increment / snowflake id) so inserts append and
#   secondary indexes stay small. A secondary index leaf stores the indexed
#   columns + the PK; a lookup by secondary index finds the PK, then walks the
#   clustered index to fetch the row = lookback / 回表 (MySQL 5.6 batches
#   these: index condition pushdown, MRR). A UUID PK causes random inserts and
#   page splits.
# Covering index: the query's columns are all in the index (SELECT list +
#   WHERE), so no lookback ("Using index" in EXPLAIN). Append the selected
#   columns to the composite index; costs write amplification.
# Leftmost prefix: an index (a, b, c) can serve predicates on a; a,b; a,b,c;
#   also a + range on b (then c is unusable for seeking); NOT b alone, NOT c
#   alone, NOT a + c (c filtered inside the index only via ICP). Equality
#   columns first, range column last, most selective equality first.
# When an index is not used: function or arithmetic on the column
#   (WHERE YEAR(created_at) = 2024, WHERE id + 1 = 5), implicit type casting
#   (varchar column compared to an int), leading wildcard LIKE '%x', OR
#   across different columns without indexes on both, NOT / != (usually),
#   skipping the leftmost prefix, IS NULL on some engines, when the optimiser
#   estimates > ~20-30% of rows match (full scan is cheaper), stale
#   statistics (ANALYZE), and joins on columns with different collations.
# ACID: Atomicity (all-or-nothing, via undo log), Consistency (constraints
#   and invariants hold; a consequence of the other three plus app logic),
#   Isolation (concurrent transactions do not see each other's intermediate
#   state, via locks + MVCC), Durability (committed = survives crash, via
#   redo log / WAL flushed at commit: innodb_flush_log_at_trx_commit=1).
# Isolation levels and anomalies:
#   READ UNCOMMITTED: dirty reads (see uncommitted writes).
#   READ COMMITTED: no dirty reads; non-repeatable reads (same row differs
#     within a txn) and phantoms (new rows appear in a re-run range query).
#   REPEATABLE READ: stable row reads; standard SQL allows phantoms, but
#     InnoDB's RR mostly prevents them (snapshot for plain reads, gap locks
#     for locking reads). Write skew is still possible.
#   SERIALIZABLE: as if executed one after another; InnoDB implements it by
#     turning every SELECT into SELECT ... LOCK IN SHARE MODE.
#   MySQL default: REPEATABLE READ. PostgreSQL/Oracle/SQL Server default: RC.
# MySQL RR + MVCC: each row has hidden columns trx_id and roll_pointer to the
#   undo log chain of previous versions. A transaction takes a Read View
#   (list of active trx ids) at its first read (RR) or at every statement
#   (RC). To read a row, walk the undo chain until a version whose trx_id is
#   visible under the read view. So readers never block writers and writers
#   never block readers; consistent snapshot without locks. Long-running
#   transactions pin old undo logs (history list grows).
# Gap locks / next-key locks: under RR, locking reads (SELECT ... FOR UPDATE,
#   UPDATE, DELETE) lock the index records scanned plus the gaps between
#   them (next-key lock = record + gap before it), so no other transaction
#   can INSERT into the range -> no phantoms for locking reads. Cost:
#   deadlocks and blocked inserts on ranges; a range predicate without an
#   index locks the whole table's gaps. RC disables gap locks (only record
#   locks), which is why many shops run RC + row-based binlog.
# SELECT ... FOR UPDATE: pessimistic lock; takes exclusive (X) row locks
#   until commit; other FOR UPDATE / writes wait (or timeout at
#   innodb_lock_wait_timeout, default 50 s); plain snapshot reads still
#   proceed. Use for "read then decide then write" (stock deduction). Always
#   inside a transaction, lock rows in a consistent order to avoid deadlocks,
#   and keep the transaction short. FOR SHARE (LOCK IN SHARE MODE) is the
#   shared variant.
# Optimistic locking: no DB lock; add a version column;
#   UPDATE stock SET qty = qty - 1, version = version + 1
#   WHERE id = ? AND version = ?  -- affected rows 0 => someone else won, retry.
#   Great when conflicts are rare (most e-commerce reads); under a flash sale
#   on one hot SKU almost every retry fails, so fall back to pessimistic locks,
#   a queue, or pre-deducting inventory in Redis (DECR with a Lua check) and
#   persisting asynchronously. Also the CAS form without a version column:
#   UPDATE ... SET qty = qty - 1 WHERE id = ? AND qty >= 1 - atomic in one
#   statement, no version needed.
# ---------------------------------------------------------------------------


def fetch(conn: sqlite3.Connection, sql: str) -> List[Tuple[Any, ...]]:
    return [tuple(r) for r in conn.execute(sql).fetchall()]


def rows_equal(got: Sequence[Tuple[Any, ...]], want: Sequence[Tuple[Any, ...]]) -> bool:
    if len(got) != len(want):
        return False
    for g, w in zip(got, want):
        if len(g) != len(w):
            return False
        for a, b in zip(g, w):
            if isinstance(a, float) or isinstance(b, float):
                if a is None or b is None or abs(a - b) > 1e-9:
                    return False
            elif a != b:
                return False
    return True


def check(name: str, conn: sqlite3.Connection, sql: str, want: Sequence[Tuple[Any, ...]]) -> None:
    assert sql, f"{name}: not implemented"
    got = fetch(conn, sql)
    assert rows_equal(got, want), f"{name}:\n  got  {got}\n  want {want}"


if __name__ == "__main__":
    conn = make_db()

    check("q01", conn, q01_revenue_per_seller(),
          [(3, "Gamma", 21000), (2, "Beta", 16500), (1, "Alpha", 14700), (4, "Delta", 2100), (5, "Epsilon", 0)])

    if HAS_WINDOW:
        check("q02", conn, q02_top3_products_per_category(), [
            ("Accessories", "Earbuds", 6000, 1), ("Accessories", "Cable", 3200, 2), ("Accessories", "Phone Case", 3000, 3),
            ("Apparel", "T-Shirt", 8000, 1), ("Apparel", "Cap", 4500, 2), ("Apparel", "Hoodie", 4000, 3),
            ("Beauty", "Serum", 9000, 1), ("Beauty", "Mascara", 7200, 2), ("Beauty", "Lipstick", 4800, 3),
            ("Stationery", "Sticker", 2100, 1),
        ])

    check("q03a", conn, q03a_users_without_orders_left_join(), [(6, "Fay"), (7, "Gus")])
    check("q03b", conn, q03b_users_without_orders_not_exists(), [(6, "Fay"), (7, "Gus")])

    check("q04a", conn, q04a_ranked_3_to_6_limit_offset(),
          [("Mascara", 7200), ("Earbuds", 6000), ("Lipstick", 4800), ("Cap", 4500)])
    if HAS_WINDOW:
        check("q04b", conn, q04b_ranked_3_to_6_window(),
              [(3, "Mascara", 7200), (4, "Earbuds", 6000), (5, "Lipstick", 4800), (6, "Cap", 4500)])
        check("q05", conn, q05_second_highest_price_per_category(),
              [("Accessories", 2500), ("Apparel", 2000), ("Beauty", 1200), ("Stationery", None)])
        check("q06", conn, q06_monthly_revenue_running_total(),
              [("2024-01", 13300, 13300), ("2024-02", 4800, 18100), ("2024-03", 36200, 54300)])

    check("q07", conn, q07_us_creators_two_recent_videos(), [(1, "Ava", 2, 6000), (4, "Dana", 2, 6000)])
    check("q08", conn, q08_users_bought_both_categories(), [(1, "Ann"), (2, "Bob")])

    if HAS_WINDOW:
        check("q09", conn, q09_dau_rolling_7(), [
            ("2024-03-01", 1, 1.0), ("2024-03-02", 2, 1.5), ("2024-03-03", 1, 1.33), ("2024-03-04", 1, 1.25),
            ("2024-03-05", 1, 1.2), ("2024-03-06", 2, 1.33), ("2024-03-07", 1, 1.29), ("2024-03-08", 1, 1.29),
            ("2024-03-20", 1, 1.14), ("2024-03-29", 1, 1.14),
        ])

    check("q10a", conn, q10a_find_duplicate_likes(), [(1, 1, 2), (2, 3, 3)])
    sql = q10b_delete_duplicate_likes()
    assert sql, "q10b: not implemented"
    cur = conn.execute(sql)
    assert cur.rowcount == 3, cur.rowcount
    assert fetch(conn, "SELECT user_id, video_id FROM likes ORDER BY user_id, video_id") == [(1, 1), (2, 1), (2, 3), (3, 2)]
    check("q10a-after", conn, q10a_find_duplicate_likes(), [])

    if HAS_WINDOW:
        check("q11a", conn, q11a_three_consecutive_days_lag(), [(1, "Ann"), (3, "Cai")])
    check("q11b", conn, q11b_three_consecutive_days_self_join(), [(1, "Ann"), (3, "Cai")])

    check("q12", conn, q12_pct_cancelled_per_seller(),
          [(1, "Alpha", 33.33), (2, "Beta", 14.29), (3, "Gamma", 0.0), (4, "Delta", 0.0)])

    check("q13", conn, q13_pivot_revenue_by_status(), [
        (1, "Alpha", 0, 4900, 9800, 6500), (2, "Beta", 0, 11500, 5000, 4500),
        (3, "Gamma", 2400, 12600, 6000, 0), (4, "Delta", 2100, 0, 0, 0), (5, "Epsilon", 0, 0, 0, 0),
    ])

    check("q14-1", conn, q14_nth_highest_price(1), [(6000,)])
    check("q14-2", conn, q14_nth_highest_price(2), [(4500,)])
    check("q14-3", conn, q14_nth_highest_price(3), [(3000,)])
    check("q14-20", conn, q14_nth_highest_price(20), [(None,)])

    # Part 15 mutates: run last. Two CREATED orders are older than 30 days (13, 15).
    sql = q15_cancel_stale_created_orders()
    assert sql, "q15: not implemented"
    cur = conn.execute(sql)
    assert cur.rowcount == 2, cur.rowcount
    assert fetch(conn, "SELECT id FROM orders WHERE status = 'CREATED' ORDER BY id") == [(11,), (12,)]
    assert fetch(conn, "SELECT id FROM orders WHERE status = 'CANCELLED' ORDER BY id") == [(4,), (9,), (13,), (15,), (18,)]
    cur = conn.execute(sql)                       # idempotent
    assert cur.rowcount == 0
    conn.commit()

    ans = q16_index_choice()
    assert ans and "(seller_id, created_at)" in ans and "prefix" in ans.lower()
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: "Rows ranked 3-6" - what if two products tie at rank 6?
#    A: LIMIT/OFFSET with ORDER BY revenue alone is non-deterministic; add a
#       tiebreaker (id) or use RANK/DENSE_RANK and state which tie policy the
#       business wants (RANK <= 6 may return 7 rows).
# Q: Why does the LEFT JOIN in q01 need the status filter in a CTE?
#    A: In WHERE it turns the join inner (Epsilon disappears); in ON it keeps
#       the item row with a NULL order and the cancelled amount is still summed.
# Q: The rolling 7-day average in q09 ignores days without orders. Fix?
#    A: Generate a calendar (recursive CTE: WITH RECURSIVE d(day) AS (...)),
#       LEFT JOIN daily onto it with COALESCE(dau, 0), then window over it.
# Q: How would you paginate "next 20 orders" on a 100M-row table?
#    A: Keyset pagination: WHERE (created_at, id) < (?, ?) ORDER BY created_at
#       DESC, id DESC LIMIT 20 on an index (created_at, id); OFFSET n scans n rows.
# Q: Deduct stock for a flash sale safely?
#    A: UPDATE stock SET qty = qty - 1 WHERE sku = ? AND qty >= 1, check
#       rowcount = 1 (atomic CAS), or SELECT ... FOR UPDATE then update; for
#       hot SKUs pre-deduct in Redis with a Lua script and write back via MQ.
