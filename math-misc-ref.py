from __future__ import annotations

"""
Math and miscellaneous — reference solutions.

Part 1 — Digit-sum inverse (TikTok intern round 1).
    "Given b, find every non-negative a with a + digitsum(a) == b."
    digit_sum_inverse(b) -> sorted list.  Example: b=21 -> [15]; b=101 -> [91, 100];
    b=20 -> [].  b <= 1e18.  Brute force over [0, b] is far too slow: explain
    the bound  a >= b - 9 * len(str(b))  and search only that window.

Part 2 — Valid square (TikTok first round), then "any 4 of N points".
    valid_square(p1, p2, p3, p4) -> bool for integer points in any order.
    Use the 6 pairwise squared distances.  Then count_squares(points): how
    many squares have all 4 corners in the set?  N <= 2000 so O(N^2)-ish:
    treat each pair as a diagonal and look up the other two corners.
    3x3 lattice -> 6 squares.

Part 3 — rand10 from rand7.
    rand10(rand7) where rand7() is uniform on 1..7.  Rejection sampling:
    build a uniform 1..49, reject > 40.  State the expected number of rand7
    calls (2 * 49/40 = 2.45).

Part 4 — Fisher-Yates shuffle and reservoir sampling.
    fisher_yates(arr, rng) shuffles in place uniformly.
    reservoir_sample(stream, k, rng) returns k items uniformly from an
    iterable of unknown length in one pass.  Sketch the k/n proof.

Part 5 — Random pick with weight (weighted A/B split).
    WeightedPicker(weights).pick(rng) -> index i with probability w_i / sum.
    Prefix sums + bisect; O(n) build, O(log n) pick.  Zero weights allowed.

Part 6 — Fast power and integer sqrt.
    fast_pow(base, exp, mod=None) in O(log exp).  isqrt(n) = floor(sqrt(n))
    exactly, for n up to 1e18 (no floats).

Part 7 — gcd / lcm and "pair with maximum gcd".
    gcd(a, b), lcm(a, b).  max_gcd_pair(nums): values in 1..1e5, n up to 1e5;
    return the largest gcd over all pairs.  [2,3,4,5,6] -> 3.  O(n^2) is too
    slow: iterate g descending and count multiples of g.

Part 8 — Excel column titles, base conversion, base62 short URLs.
    column_number("AB") -> 28, column_title(28) -> "AB" (bijective base 26).
    to_base(n, base) / from_base(s, base) with digits 0-9A-Z (base <= 36).
    base62_encode(n) / base62_decode(s) with alphabet 0-9a-zA-Z.

Part 9 — Roman numerals both ways.  int_to_roman(1994) -> "MCMXCIV".

Part 10 — Count primes below n with a sieve.  count_primes(10) -> 4.

Part 11 — Happy number with Floyd cycle detection (no set).  is_happy(19) -> True.

Part 12 — atoi with 32-bit overflow clamp.  my_atoi("   -42") -> -42,
    my_atoi("-91283472332") -> -2147483648, my_atoi("words 987") -> 0.

Part 13 — Multiply two numeric strings without int().  multiply("123","456") -> "56088".

Part 14 — add_binary("11","1") -> "100"; add_strings("123","989") -> "1112".
"""

from bisect import bisect_right
from itertools import accumulate
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

Point = Tuple[int, int]


# ---------------------------------------------------------------- Part 1
def digit_sum(a: int) -> int:
    return sum(int(c) for c in str(a))


def digit_sum_inverse(b: int) -> List[int]:
    # Bound: a <= b, so a has at most len(str(b)) digits, so digitsum(a) <= 9*len(str(b)).
    # From a = b - digitsum(a) we get a >= b - 9*len(str(b)).  The window has at most
    # 9*len(str(b)) + 1 candidates (~170 for b ~ 1e18), each checked in O(len).
    lo = max(0, b - 9 * len(str(b)))
    return [a for a in range(lo, b + 1) if a + digit_sum(a) == b]


# ---------------------------------------------------------------- Part 2
def valid_square(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    # Six pairwise squared distances: four equal sides (> 0) and two equal diagonals.
    # Squared ints avoid sqrt/float issues.  A rhombus fails the diagonal test.
    pts = [p1, p2, p3, p4]
    d = sorted((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2
               for i in range(4) for j in range(i + 1, 4))
    return d[0] > 0 and d[0] == d[1] == d[2] == d[3] and d[4] == d[5] == 2 * d[0]


def count_squares(points: Sequence[Point]) -> int:
    # For every pair (p, q) treated as a DIAGONAL, the other two corners are
    # centre +/- rot90(half-diagonal).  With integer coordinates they exist only if
    # the parity works out.  Each square is found from both diagonals -> divide by 2.
    # O(N^2) pairs, O(1) set lookups.
    pset = set(points)
    pts = list(pset)
    count = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        for j in range(i + 1, len(pts)):
            x2, y2 = pts[j]
            sx, sy = x1 + x2, y1 + y2          # 2 * centre
            dx, dy = x2 - x1, y2 - y1          # full diagonal vector
            if (sx - dy) % 2 or (sy + dx) % 2:
                continue
            r = ((sx - dy) // 2, (sy + dx) // 2)
            s = ((sx + dy) // 2, (sy - dx) // 2)
            if r in pset and s in pset:
                count += 1
    return count // 2
    # Alternative: treat the pair as a SIDE and check both rotations; then divide by 4.


# ---------------------------------------------------------------- Part 3
def rand10(rand7: Callable[[], int]) -> int:
    # Two calls give a uniform value in 1..49 (7 * (r1-1) + r2).  Keep 1..40 (a multiple
    # of 10) and map with mod; reject 41..49.  Acceptance 40/49, so expected calls
    # = 2 / (40/49) = 2.45.  Rejected values can seed the next round (LC 470 follow-up).
    while True:
        idx = (rand7() - 1) * 7 + rand7()
        if idx <= 40:
            return (idx - 1) % 10 + 1


# ---------------------------------------------------------------- Part 4
def fisher_yates(arr: List[int], rng) -> None:
    # For i from n-1 down to 1 swap arr[i] with a uniform random arr[j], j in [0, i].
    # Every permutation has probability 1/n!: position n-1 is uniform over n items, then
    # n-2 is uniform over the remaining n-1, ...  Pitfall: j in [0, n-1] (the "naive
    # shuffle") is NOT uniform -- n^n outcomes cannot map evenly onto n! permutations.
    for i in range(len(arr) - 1, 0, -1):
        j = rng.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]


def reservoir_sample(stream: Iterable[int], k: int, rng) -> List[int]:
    # Keep the first k.  The i-th item (0-based, i >= k) replaces a random slot with
    # probability k/(i+1).  Proof sketch: P(item i survives to the end)
    #   = k/(i+1) * prod_{t=i+1}^{n-1} (1 - k/(t+1) * 1/k) = k/(i+1) * prod t/(t+1) = k/n.
    res: List[int] = []
    for i, x in enumerate(stream):
        if i < k:
            res.append(x)
        else:
            j = rng.randint(0, i)
            if j < k:
                res[j] = x
    return res


# ---------------------------------------------------------------- Part 5
class WeightedPicker:
    def __init__(self, weights: List[int]) -> None:
        self.prefix = list(accumulate(weights))   # prefix[i] = w_0 + ... + w_i
        self.total = self.prefix[-1]

    def pick(self, rng) -> int:
        # target uniform in [0, total); index i owns [prefix[i-1], prefix[i]).
        # bisect_right skips zero-weight buckets (their half-open range is empty).
        target = rng.random() * self.total
        return bisect_right(self.prefix, target)


# ---------------------------------------------------------------- Part 6
def fast_pow(base: int, exp: int, mod: Optional[int] = None) -> int:
    # Square-and-multiply over the bits of exp.  O(log exp) multiplications.
    result = 1
    if mod is not None:
        base %= mod
    while exp > 0:
        if exp & 1:
            result = result * base if mod is None else result * base % mod
        base = base * base if mod is None else base * base % mod
        exp >>= 1
    return result


def isqrt(n: int) -> int:
    # Binary search the largest r with r*r <= n.  Never use int(n ** 0.5): floats
    # lose precision above 2^53.  (math.isqrt exists in 3.8+, but know how.)
    if n < 0:
        raise ValueError("negative")
    if n < 2:
        return n
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


# ---------------------------------------------------------------- Part 7
def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else abs(a * b) // gcd(a, b)


def max_gcd_pair(nums: List[int]) -> int:
    # Counting trick: for g from max down to 1, count how many elements are multiples
    # of g; the first g with >= 2 multiples is the answer.  Sum over g of M/g = O(M log M).
    if len(nums) < 2:
        return 0
    mx = max(nums)
    cnt = [0] * (mx + 1)
    for x in nums:
        cnt[x] += 1
    for g in range(mx, 0, -1):
        c = 0
        for m in range(g, mx + 1, g):
            c += cnt[m]
            if c >= 2:
                return g
    return 1


# ---------------------------------------------------------------- Part 8
def column_number(s: str) -> int:
    n = 0
    for c in s:
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n


def column_title(n: int) -> str:
    # Bijective base 26: digits 1..26, no zero.  Subtract 1 before each divmod.
    out: List[str] = []
    while n > 0:
        n, r = divmod(n - 1, 26)
        out.append(chr(ord("A") + r))
    return "".join(reversed(out))


DIGITS36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def to_base(n: int, base: int) -> str:
    if n == 0:
        return "0"
    neg = n < 0
    n = abs(n)
    out: List[str] = []
    while n:
        n, r = divmod(n, base)
        out.append(DIGITS36[r])
    return ("-" if neg else "") + "".join(reversed(out))


def from_base(s: str, base: int) -> int:
    neg = s.startswith("-")
    n = 0
    for c in s.lstrip("-"):
        n = n * base + DIGITS36.index(c.upper())
    return -n if neg else n


BASE62 = "0123456789abcdefghijklmnopqrstuvwxyz" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(n: int) -> str:
    # Short URL: store the row, encode its auto-increment id; 62^7 ~ 3.5e12 ids in 7 chars.
    if n == 0:
        return BASE62[0]
    out: List[str] = []
    while n:
        n, r = divmod(n, 62)
        out.append(BASE62[r])
    return "".join(reversed(out))


def base62_decode(s: str) -> int:
    n = 0
    for c in s:
        n = n * 62 + BASE62.index(c)
    return n


# ---------------------------------------------------------------- Part 9
ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
         (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def int_to_roman(n: int) -> str:
    # Greedy over the 13 symbols (subtractive pairs included) -- greedy is exact here.
    out: List[str] = []
    for value, sym in ROMAN:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


def roman_to_int(s: str) -> int:
    # A symbol smaller than the one to its right is subtracted.
    val = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, c in enumerate(s):
        if i + 1 < len(s) and val[c] < val[s[i + 1]]:
            total -= val[c]
        else:
            total += val[c]
    return total


# ---------------------------------------------------------------- Part 10
def count_primes(n: int) -> int:
    # Sieve of Eratosthenes over [0, n).  Cross off multiples starting at p*p with a
    # slice assignment.  O(n log log n) time, O(n) space.
    if n < 3:
        return 0
    sieve = bytearray([1]) * n
    sieve[0] = sieve[1] = 0
    for p in range(2, isqrt(n - 1) + 1):
        if sieve[p]:
            sieve[p * p::p] = bytearray(len(range(p * p, n, p)))
    return sum(sieve)


# ---------------------------------------------------------------- Part 11
def is_happy(n: int) -> bool:
    # The digit-square-sum sequence either reaches 1 or falls into the 4-cycle;
    # Floyd's tortoise/hare finds a cycle with O(1) memory.
    def nxt(x: int) -> int:
        s = 0
        while x:
            x, d = divmod(x, 10)
            s += d * d
        return s

    slow, fast = n, nxt(n)
    while fast != 1 and slow != fast:
        slow = nxt(slow)
        fast = nxt(nxt(fast))
    return fast == 1


# ---------------------------------------------------------------- Part 12
def my_atoi(s: str) -> int:
    INT_MAX, INT_MIN = 2**31 - 1, -2**31
    i, n = 0, len(s)
    while i < n and s[i] == " ":            # 1. leading spaces only (not tabs)
        i += 1
    sign = 1
    if i < n and s[i] in "+-":              # 2. one optional sign
        sign = -1 if s[i] == "-" else 1
        i += 1
    val = 0
    while i < n and s[i].isdigit():         # 3. digits; stop at the first non-digit
        val = val * 10 + (ord(s[i]) - ord("0"))
        if sign * val > INT_MAX:            # 4. clamp (in C you'd check before multiplying)
            return INT_MAX
        if sign * val < INT_MIN:
            return INT_MIN
        i += 1
    return sign * val


# ---------------------------------------------------------------- Part 13
def multiply(a: str, b: str) -> str:
    # Schoolbook: digit a[i] * b[j] lands in position i+j+1 (with carry into i+j).
    # Result has at most len(a)+len(b) digits.  O(n*m).
    if a == "0" or b == "0":
        return "0"
    res = [0] * (len(a) + len(b))
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            prod = (ord(a[i]) - 48) * (ord(b[j]) - 48) + res[i + j + 1]
            res[i + j + 1] = prod % 10
            res[i + j] += prod // 10
    out = "".join(map(str, res)).lstrip("0")
    return out or "0"


# ---------------------------------------------------------------- Part 14
def add_binary(a: str, b: str) -> str:
    i, j, carry = len(a) - 1, len(b) - 1, 0
    out: List[str] = []
    while i >= 0 or j >= 0 or carry:
        total = carry
        if i >= 0:
            total += ord(a[i]) - 48
            i -= 1
        if j >= 0:
            total += ord(b[j]) - 48
            j -= 1
        out.append(str(total & 1))
        carry = total >> 1
    return "".join(reversed(out))


def add_strings(a: str, b: str) -> str:
    # Same loop, base 10.  Pitfall: don't forget the final carry.
    i, j, carry = len(a) - 1, len(b) - 1, 0
    out: List[str] = []
    while i >= 0 or j >= 0 or carry:
        total = carry
        if i >= 0:
            total += ord(a[i]) - 48
            i -= 1
        if j >= 0:
            total += ord(b[j]) - 48
            j -= 1
        carry, d = divmod(total, 10)
        out.append(str(d))
    return "".join(reversed(out))


if __name__ == "__main__":
    import math
    import random

    # Part 1
    assert digit_sum_inverse(21) == [15] and digit_sum_inverse(101) == [91, 100]
    assert digit_sum_inverse(20) == [] and digit_sum_inverse(0) == [0] and digit_sum_inverse(2) == [1]
    for b in (1, 9, 10, 11, 99, 100, 1000, 1234, 5000):
        assert digit_sum_inverse(b) == [a for a in range(b + 1) if a + digit_sum(a) == b]
    big = digit_sum_inverse(10**18)
    assert big and all(a + digit_sum(a) == 10**18 for a in big)
    # Part 2
    assert valid_square((0, 0), (1, 1), (1, 0), (0, 1)) is True
    assert valid_square((0, 0), (1, 1), (1, 0), (0, 12)) is False
    assert valid_square((1, 0), (-1, 0), (0, 1), (0, -1)) is True
    assert valid_square((0, 0), (0, 0), (0, 0), (0, 0)) is False
    assert valid_square((0, 0), (2, 1), (1, 3), (-1, 2)) is True      # tilted
    assert valid_square((0, 0), (2, 0), (3, 1), (1, 1)) is False      # rhombus-ish
    assert count_squares([(0, 0), (1, 0), (0, 1), (1, 1)]) == 1
    assert count_squares([(x, y) for x in range(3) for y in range(3)]) == 6
    assert count_squares([(0, 0), (1, 0), (2, 0)]) == 0
    assert count_squares([(0, 0), (2, 1), (1, 3), (-1, 2), (5, 5)]) == 1
    # Part 3
    rng = random.Random(0)
    counts = [0] * 11
    for _ in range(100000):
        v = rand10(lambda: rng.randint(1, 7))
        assert 1 <= v <= 10
        counts[v] += 1
    assert all(9000 < c < 11000 for c in counts[1:])
    feed = iter([1, 1, 6, 5, 7, 7, 1, 2])          # 1 -> 1; (6,5) -> 40 -> 10; (7,7)=49 reject; (1,2) -> 2
    assert rand10(lambda: next(feed)) == 1
    assert rand10(lambda: next(feed)) == 10
    assert rand10(lambda: next(feed)) == 2
    # Part 4
    rng = random.Random(42)
    pos = [[0] * 4 for _ in range(4)]
    for _ in range(20000):
        arr = [0, 1, 2, 3]
        fisher_yates(arr, rng)
        assert sorted(arr) == [0, 1, 2, 3]
        for p, v in enumerate(arr):
            pos[v][p] += 1
    assert all(4600 < c < 5400 for row in pos for c in row)
    freq = [0] * 10
    for _ in range(20000):
        sample = reservoir_sample(range(10), 3, rng)
        assert len(sample) == 3 and len(set(sample)) == 3 and all(0 <= x < 10 for x in sample)
        for x in sample:
            freq[x] += 1
    assert all(5500 < c < 6500 for c in freq)
    assert reservoir_sample(range(2), 5, rng) == [0, 1]
    # Part 5
    class FixedRng:
        def __init__(self, u: float) -> None:
            self.u = u

        def random(self) -> float:
            return self.u

    picker = WeightedPicker([1, 3])
    assert picker.pick(FixedRng(0.1)) == 0 and picker.pick(FixedRng(0.25)) == 1
    assert picker.pick(FixedRng(0.999)) == 1
    zero = WeightedPicker([0, 5, 0, 5])
    assert zero.pick(FixedRng(0.0)) == 1 and zero.pick(FixedRng(0.5)) == 3
    hits = [0, 0]
    for _ in range(20000):
        hits[picker.pick(rng)] += 1
    assert 14000 < hits[1] < 16000
    # Part 6
    assert fast_pow(2, 10) == 1024 and fast_pow(5, 0) == 1 and fast_pow(0, 5) == 0
    assert fast_pow(3, 200, 10**9 + 7) == pow(3, 200, 10**9 + 7)
    assert fast_pow(7, 12345, 1000) == pow(7, 12345, 1000)
    assert isqrt(0) == 0 and isqrt(1) == 1 and isqrt(8) == 2 and isqrt(9) == 3
    assert isqrt(10**18) == 10**9 and isqrt(10**18 - 1) == 10**9 - 1
    for n in list(range(2000)) + [2**53 + 1, 2**62, 10**17 + 3]:
        assert isqrt(n) == math.isqrt(n)
    # Part 7
    assert gcd(12, 18) == 6 and gcd(7, 0) == 7 and gcd(0, 0) == 0 and lcm(4, 6) == 12
    assert max_gcd_pair([2, 3, 4, 5, 6]) == 3 and max_gcd_pair([12, 18, 24]) == 12
    assert max_gcd_pair([7, 11]) == 1 and max_gcd_pair([5, 5]) == 5 and max_gcd_pair([5]) == 0
    for _ in range(50):
        xs = [rng.randint(1, 60) for _ in range(rng.randint(2, 8))]
        brute = max(gcd(xs[i], xs[j]) for i in range(len(xs)) for j in range(i + 1, len(xs)))
        assert max_gcd_pair(xs) == brute
    # Part 8
    assert column_number("A") == 1 and column_number("Z") == 26 and column_number("AB") == 28
    assert column_number("ZY") == 701
    assert column_title(1) == "A" and column_title(26) == "Z" and column_title(28) == "AB"
    assert column_title(52) == "AZ" and column_title(701) == "ZY"
    for n in range(1, 2000):
        assert column_number(column_title(n)) == n
    assert to_base(255, 16) == "FF" and to_base(0, 2) == "0" and to_base(-10, 2) == "-1010"
    assert from_base("FF", 16) == 255 and from_base("-1010", 2) == -10 and from_base("zz", 36) == 1295
    assert base62_encode(0) == "0" and base62_encode(61) == "Z" and base62_encode(62) == "10"
    for n in (1, 61, 62, 3843, 123456789, 2**40):
        assert base62_decode(base62_encode(n)) == n
    assert len(base62_encode(62**7 - 1)) == 7
    # Part 9
    assert int_to_roman(3) == "III" and int_to_roman(58) == "LVIII" and int_to_roman(1994) == "MCMXCIV"
    assert int_to_roman(3749) == "MMMDCCXLIX"
    assert roman_to_int("MCMXCIV") == 1994 and roman_to_int("LVIII") == 58 and roman_to_int("IX") == 9
    for n in range(1, 4000):
        assert roman_to_int(int_to_roman(n)) == n
    # Part 10
    assert count_primes(0) == 0 and count_primes(2) == 0 and count_primes(3) == 1
    assert count_primes(10) == 4 and count_primes(100) == 25 and count_primes(10**6) == 78498
    # Part 11
    assert is_happy(19) is True and is_happy(1) is True and is_happy(7) is True
    assert is_happy(2) is False and is_happy(4) is False and is_happy(20) is False
    # Part 12
    assert my_atoi("42") == 42 and my_atoi("   -42") == -42 and my_atoi("4193 with words") == 4193
    assert my_atoi("words and 987") == 0 and my_atoi("-91283472332") == -2147483648
    assert my_atoi("+-12") == 0 and my_atoi("  +0 123") == 0 and my_atoi("2147483648") == 2147483647
    assert my_atoi("") == 0 and my_atoi("-") == 0 and my_atoi("00000-42a1234") == 0
    # Part 13
    assert multiply("2", "3") == "6" and multiply("123", "456") == "56088"
    assert multiply("0", "12345") == "0" and multiply("999", "999") == "998001"
    assert multiply("123456789", "987654321") == str(123456789 * 987654321)
    # Part 14
    assert add_binary("11", "1") == "100" and add_binary("1010", "1011") == "10101"
    assert add_binary("0", "0") == "0"
    assert add_strings("123", "989") == "1112" and add_strings("0", "0") == "0"
    assert add_strings("99999999999999999999", "1") == "100000000000000000000"
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Digit-sum inverse: why can you stop at b - 9*len(str(b)) and not tighter?
# A: digitsum(a) <= 9 * digits(a) <= 9 * digits(b) since a <= b; any tighter bound needs
#    case analysis and buys nothing -- the window is already ~170 numbers for b <= 1e18.
# Q: Valid square with floating-point coordinates?
# A: Compare squared distances with a tolerance (abs(d1 - d2) <= eps * max(d1, d2)) and
#    the parity trick in count_squares no longer applies -- store points rounded to a
#    grid or use a tolerance-aware lookup.
# Q: rand10: can you beat 2.45 expected calls?
# A: Yes: recycle the rejected 41..49 as a uniform 1..9, combine with another rand7 for
#    1..63, keep 1..60; the LC470 editorial gets ~2.19.
# Q: Reservoir sampling across several machines?
# A: Each machine keeps its own reservoir plus its item count; merge by weighting each
#    reservoir by its count (or use the priority-key variant: keep the k largest
#    random keys, which merges trivially).
# Q: my_atoi -- what changes in a language with fixed-width ints?
# A: You must detect overflow BEFORE val*10 + d, e.g. val > (INT_MAX - d) // 10, since
#    the multiplication itself would wrap.
