from __future__ import annotations

"""Cart Pricing - reference solution. See cart-pricing.py for the problem text."""

from typing import Dict, List, Optional, Sequence, Tuple
import random

Line = Tuple[str, int, int]   # (sku, unit_cents, qty)


def round_half_up(num: int, den: int) -> int:
    """round(num / den) with ties going UP, in pure integer arithmetic.
    floor(num/den + 1/2) == floor((2*num + den) / (2*den)). num >= 0, den > 0."""
    return (2 * num + den) // (2 * den)


# ---------------------------------------------------------------------------
# Part 1
# DATA SHAPE: dict: sku -> [unit_cents, qty]  (insertion ordered = display order)
# INVARIANT:  qty >= 1 for every stored line; a line with qty 0 is deleted.
# COMPLEXITY: add / remove O(1); total O(lines). All money is int cents.
# PITFALL:    adding the same SKU again merges qty and takes the *latest* unit
#             price (the catalog is the source of truth, see Part 4).
# ---------------------------------------------------------------------------
class Cart:
    def __init__(self) -> None:
        self.lines: Dict[str, List[int]] = {}

    def add(self, sku: str, unit_cents: int, qty: int = 1) -> None:
        if qty <= 0 or unit_cents < 0:
            raise ValueError("bad qty / price")
        line = self.lines.get(sku)
        if line is None:
            self.lines[sku] = [unit_cents, qty]
        else:
            line[0] = unit_cents
            line[1] += qty

    def remove(self, sku: str, qty: Optional[int] = None) -> None:
        line = self.lines.get(sku)
        if line is None:
            raise KeyError(sku)
        if qty is None or qty >= line[1]:
            del self.lines[sku]
        else:
            line[1] -= qty

    def items(self) -> List[Line]:
        return [(sku, u, q) for sku, (u, q) in self.lines.items()]

    def subtotal(self) -> int:
        return sum(u * q for u, q in self.lines.values())

    def total(self) -> int:
        return self.subtotal()


# ---------------------------------------------------------------------------
# Part 2
# DATA SHAPE: Coupon.discount(lines) -> int cents; PercentOff(pct, cap),
#             FixedOff(amount, min_spend), BuyNGetOne(sku, n).
# INVARIANT:  0 <= discount <= subtotal(lines); everything is integer.
# COMPLEXITY: O(lines) per coupon; best_coupon O(coupons * lines).
# PITFALLS:   percent is rounded per LINE (unit*qty*pct / 100, half up), then
#             summed, then capped - not rounded once on the cart total (the
#             per-line amounts must be explainable on the invoice). Fixed-off
#             is clamped to the subtotal so the total never goes negative.
#             Buy-N-get-1: free = qty // (n + 1) - buy 1 get 1 with qty 3 gives
#             1 free, not 2. Never touch floats: 0.1 + 0.2 != 0.3.
# ---------------------------------------------------------------------------
class Coupon:
    def discount(self, lines: Sequence[Line]) -> int:
        raise NotImplementedError


class PercentOff(Coupon):
    def __init__(self, pct: int, cap_cents: Optional[int] = None) -> None:
        if not 0 <= pct <= 100:
            raise ValueError("pct")
        self.pct = pct
        self.cap = cap_cents

    def discount(self, lines: Sequence[Line]) -> int:
        d = sum(round_half_up(u * q * self.pct, 100) for _, u, q in lines)
        if self.cap is not None:
            d = min(d, self.cap)
        return min(d, sum(u * q for _, u, q in lines))


class FixedOff(Coupon):
    def __init__(self, amount_cents: int, min_spend_cents: int = 0) -> None:
        self.amount = amount_cents
        self.min_spend = min_spend_cents

    def discount(self, lines: Sequence[Line]) -> int:
        sub = sum(u * q for _, u, q in lines)
        if sub < self.min_spend:
            return 0
        return min(self.amount, sub)


class BuyNGetOne(Coupon):
    def __init__(self, sku: str, n: int) -> None:
        if n < 1:
            raise ValueError("n")
        self.sku = sku
        self.n = n

    def discount(self, lines: Sequence[Line]) -> int:
        for sku, u, q in lines:
            if sku == self.sku:
                return (q // (self.n + 1)) * u
        return 0


def best_coupon(lines: Sequence[Line], coupons: Sequence[Coupon]) -> Tuple[Optional[Coupon], int]:
    """Single best coupon; ties -> first in the list; (None, 0) if nothing applies."""
    best: Optional[Coupon] = None
    best_d = 0
    for c in coupons:
        d = c.discount(lines)
        if d > best_d:
            best, best_d = c, d
    return best, best_d


# ---------------------------------------------------------------------------
# Part 3 - stacking
# ORDER:      seller coupon on the raw lines -> platform coupon on what is left
#             -> shipping decided on the merchandise total after both.
# TRICK:      the platform coupon sees the post-seller amount as ONE synthetic
#             line ("_cart", after_seller, 1): PercentOff rounds once on it,
#             FixedOff checks min_spend against it. So a platform "300 off over
#             4100" does NOT apply to a 4498 cart that a seller coupon brought
#             down to 4048 - the min spend is evaluated *after* the seller cut.
# PITFALL:    free-shipping threshold is compared with the discounted
#             merchandise total, not the subtotal (otherwise coupons + free
#             shipping stack into a loss for the platform).
# ---------------------------------------------------------------------------
def checkout(cart: Cart, seller: Optional[Coupon], platform: Optional[Coupon],
             shipping_cents: int, free_ship_threshold: int) -> Dict[str, int]:
    lines = cart.items()
    subtotal = cart.subtotal()
    seller_d = seller.discount(lines) if seller else 0
    after_seller = subtotal - seller_d
    platform_d = platform.discount([("_cart", after_seller, 1)]) if platform else 0
    merch = after_seller - platform_d
    shipping = 0 if merch >= free_ship_threshold else shipping_cents
    return {
        "subtotal": subtotal,
        "seller_discount": seller_d,
        "platform_discount": platform_d,
        "shipping": shipping,
        "total": merch + shipping,
    }


# ---------------------------------------------------------------------------
# Part 3b - allocate a cart-level discount across lines (largest remainder)
# METHOD:     share_i = discount * amount_i / S exactly as (floor_i, rem_i)
#             with integer divmod; give the leftover discount - sum(floor_i)
#             cents one at a time to the lines with the largest remainder
#             (ties: earlier line first).
# INVARIANTS: sum(parts) == discount; 0 <= part_i <= amount_i (needs
#             discount <= S); a line with amount 0 gets 0.
# COMPLEXITY: O(n log n) for the sort of remainders (O(n) with a select).
# PITFALL:    rounding each share independently (round_half_up) can be off by
#             +-1 in the sum; largest remainder is what invoices / refunds use.
# ---------------------------------------------------------------------------
def allocate(discount: int, amounts: Sequence[int]) -> List[int]:
    S = sum(amounts)
    if discount < 0 or discount > S:
        raise ValueError("discount must be within [0, sum(amounts)]")
    if S == 0:
        return [0] * len(amounts)
    parts: List[int] = []
    rems: List[Tuple[int, int]] = []          # (-remainder, index)
    for i, a in enumerate(amounts):
        q, r = divmod(discount * a, S)
        parts.append(q)
        rems.append((-r, i))
    leftover = discount - sum(parts)
    rems.sort()
    for _, i in rems[:leftover]:
        parts[i] += 1
    return parts


# ---------------------------------------------------------------------------
# Part 4 - model answer
#
# Money representation: integers in the currency's minor unit (cents) end to
#   end - DB column BIGINT/DECIMAL(19,4), API as int or string, never a JSON
#   float. Rounding mode is a product decision written down once (half up for
#   customer-facing, banker's only for internal aggregation) and tested.
#   Percentages are stored as integer basis points (1250 = 12.5%).
# Zero-decimal currencies (JPY, KRW, VND): the minor unit *is* the major unit;
#   keep a per-currency `exponent` (0, 2, 3 for KWD) and format with it. Never
#   assume 100. Multi-currency carts do not exist: one order = one currency;
#   FX conversion happens at display / settlement with a rate snapshot stored
#   on the order.
# Price changed between add-to-cart and checkout: the cart stores the SKU and
#   the price *seen*; checkout re-reads the catalog, and if the price differs
#   it returns a "price changed" error the client must acknowledge (the order
#   is created with the price the user confirmed). Never silently charge the
#   new price. Same for coupon validity and stock.
# Refund attribution: the order stores, per line, the allocated seller
#   discount and platform discount (Part 3b) so a partial refund of one line
#   refunds `unit*qty - allocated_seller - allocated_platform` to the buyer,
#   claws back the seller-funded part from the seller settlement and the
#   platform-funded part from the platform's marketing budget. Shipping is
#   refunded only when the whole order is returned. Store these at order time;
#   recomputing later with today's coupon rules gives different numbers.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # Part 1
    c = Cart()
    c.add("A", 1999, 2)
    c.add("B", 500)
    assert c.total() == 4498
    c.remove("A", 1)
    assert c.total() == 2499
    c.add("A", 1999, 1)
    assert c.items() == [("A", 1999, 2), ("B", 500, 1)]
    c.remove("B")
    assert c.total() == 3998 and c.items() == [("A", 1999, 2)]
    try:
        c.remove("Z")
        assert False
    except KeyError:
        pass
    c.remove("A", 99)                                   # more than qty -> line gone
    assert c.total() == 0 and c.items() == []
    assert round_half_up(5050, 100) == 51               # 50.5 -> 51
    assert round_half_up(5049, 100) == 50
    assert round_half_up(59970, 100) == 600             # 599.7 -> 600

    # Part 2
    c = Cart()
    c.add("A", 1999, 2)
    c.add("B", 500, 1)
    lines = c.items()
    assert PercentOff(15).discount(lines) == 675        # 600 + 75, rounded per line
    assert PercentOff(15, cap_cents=500).discount(lines) == 500
    assert FixedOff(600, min_spend_cents=4000).discount(lines) == 600
    assert FixedOff(600, min_spend_cents=5000).discount(lines) == 0
    assert FixedOff(10_000).discount(lines) == 4498     # clamped to subtotal
    assert BuyNGetOne("A", 1).discount(lines) == 1999   # buy 1 get 1: qty 2 -> 1 free
    assert BuyNGetOne("A", 2).discount(lines) == 0      # buy 2 get 1 needs qty 3
    assert BuyNGetOne("B", 1).discount(lines) == 0
    single = [("S", 1010, 1)]
    assert PercentOff(5).discount(single) == 51         # 50.5 rounds half up, not to even
    assert PercentOff(100).discount(single) == 1010
    coupons = [PercentOff(15, 500), FixedOff(600, 4000), BuyNGetOne("A", 1)]
    best, d = best_coupon(lines, coupons)
    assert isinstance(best, BuyNGetOne) and d == 1999
    best, d = best_coupon(lines, [FixedOff(600, 5000), BuyNGetOne("B", 1)])
    assert best is None and d == 0
    best, d = best_coupon(lines, [FixedOff(500), PercentOff(15, 500)])
    assert isinstance(best, FixedOff) and d == 500      # tie -> first listed

    # Part 3
    r = checkout(c, PercentOff(10), FixedOff(300, 4000), shipping_cents=599, free_ship_threshold=3000)
    assert r == {"subtotal": 4498, "seller_discount": 450, "platform_discount": 300,
                 "shipping": 0, "total": 3748}, r
    r = checkout(c, PercentOff(10), FixedOff(300, 4100), 599, 3000)
    assert r["platform_discount"] == 0 and r["total"] == 4048   # min spend checked after seller cut
    r = checkout(c, PercentOff(10), FixedOff(300, 4100), 599, 5000)
    assert r["shipping"] == 599 and r["total"] == 4647
    r = checkout(c, PercentOff(10), PercentOff(5), 599, 5000)
    assert r["platform_discount"] == 202 and r["total"] == 3846 + 599   # 202.4 -> 202 on 4048
    r = checkout(c, None, None, 599, 4498)
    assert r["total"] == 4498 and r["shipping"] == 0
    r = checkout(c, BuyNGetOne("A", 1), FixedOff(5000), 599, 100_000)
    assert r["seller_discount"] == 1999 and r["platform_discount"] == 2499 and r["total"] == 599

    # Part 3b
    assert allocate(100, [3333, 3333, 3334]) == [33, 33, 34]
    assert allocate(10, [1, 1, 1]) == [4, 3, 3]
    assert allocate(7, [100, 100, 100]) == [3, 2, 2]
    assert allocate(0, [5, 5]) == [0, 0]
    assert allocate(5, [0, 10]) == [0, 5]
    assert allocate(450, [3998, 500]) == [400, 50]      # matches the per-line 10% in Part 3
    assert allocate(0, []) == []
    try:
        allocate(11, [5, 5])
        assert False
    except ValueError:
        pass
    rng = random.Random(1)
    for _ in range(500):
        amounts = [rng.randint(0, 5000) for _ in range(rng.randint(1, 8))]
        disc = rng.randint(0, sum(amounts))
        parts = allocate(disc, amounts)
        assert sum(parts) == disc
        assert all(0 <= p <= a for p, a in zip(parts, amounts))
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Why not Decimal instead of int cents?
#    A: Decimal works (exact) but is ~50x slower, needs a context for rounding,
#       and serialises badly; ints are unambiguous. Decimal is fine for FX
#       math where you need fractional cents temporarily.
# Q: Percent 12.5%?
#    A: Store basis points: round_half_up(u*q*bps, 10_000).
# Q: A coupon applies to a subset of SKUs / categories?
#    A: Coupon gets an `applies(sku) -> bool`; PercentOff sums over eligible
#       lines only, FixedOff min_spend is over eligible lines, and allocation
#       (3b) distributes across eligible lines only.
# Q: Where is the discount validated, client or server?
#    A: Server only; the client displays what the server's price-quote endpoint
#       returns, and checkout re-quotes and compares (coupon may have expired
#       or hit its usage cap between quote and pay).
# Q: How does the seller vs platform split reach accounting?
#    A: Per line, per funding party, stored on the order at creation (3b) and
#       emitted as ledger entries; settlement to the seller subtracts only the
#       seller-funded part.
