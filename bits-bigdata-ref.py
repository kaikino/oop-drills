from __future__ import annotations

"""
Bit manipulation and big-data tricks — reference solutions.

Part 1 — Single number I, II, III.
    single_number(nums): every value appears twice except one.  [4,1,2,1,2] -> 4.
    single_number_ii(nums): every value appears THREE times except one.  [2,2,3,2] -> 3.
    single_number_iii(nums): exactly two values appear once; return them sorted.
    [1,2,1,3,2,5] -> [3,5].  All O(n) time, O(1) extra space, negatives allowed.

Part 2 — Bit basics.
    count_bits(n) -> [popcount(i) for i in 0..n] in O(n) (LC338).
    hamming_distance(a, b), reverse_bits(n) on 32 bits, is_power_of_two(n).

Part 3 — Bitmap (TikTok backend round).
    "10 billion unsigned 32-bit ints on disk, 4 GB of RAM: is x among them?"
    Answer: a bitmap of 2^32 bits = 512 MB fits easily; one pass sets bits,
    lookup is O(1).  bitmap_bytes(bits) -> bytes needed.
    Bitmap(nbits) over a bytearray with set / clear / get / count.
    Follow-up "which ints appear more than once?": TwoBitBitmap (00 = never,
    01 = once, 10 = 2+), 1 GB.  find_duplicates(nums, universe) -> sorted list.

Part 4 — Bloom filter.
    BloomFilter(n_expected, fp_rate) sizes m and k from the formulas; add(item),
    might_contain(item).  k hashes via double hashing on md5 / sha1 digests.
    "Has this user already seen this video?" at scale.  No false negatives.

Part 5 — Maximum XOR of two numbers (LC421).
    find_maximum_xor([3,10,5,25,2,8]) -> 28 (5 ^ 25).  Bit trie, O(32 n).

Part 6 — Shortest subarray with bitwise OR >= K (LC3097).
    shortest_subarray_or_at_least_k([2,1,8], 10) -> 3; [1,2,3], 7 -> -1.
    Sliding window with a per-bit count so you can REMOVE from an OR.

Part 7 — Top-K frequent words from a huge file with little RAM.
    top_k_frequent_words_external(words, k, num_buckets): hash-partition the
    stream into num_buckets "files" (a word always lands in the same bucket),
    count each bucket in memory, keep each bucket's top k, merge with a heap.
    Ties: higher count first, then lexicographically smaller word.

Part 8 — Linear counting (HyperLogLog-lite) for live viewer counts.
    LinearCounter(m): bitmap of m bits; add(item) sets bit hash(item) % m;
    estimate() = -m * ln(V / m) where V = number of zero bits.  merge(other)
    for unions across shards (bitwise OR).  Within ~10% at 1000 distinct / 8192 bits.

Part 9 — Gray code.  gray_code(2) -> [0,1,3,2]; adjacent (and last/first) differ by one bit.
"""

import hashlib
import heapq
import io
import math
import zlib
from collections import Counter
from itertools import islice
from typing import Dict, Iterable, List, Tuple


# ---------------------------------------------------------------- Part 1
def single_number(nums: List[int]) -> int:
    # x ^ x = 0 and ^ is commutative, so all pairs cancel.
    acc = 0
    for x in nums:
        acc ^= x
    return acc


def single_number_ii(nums: List[int]) -> int:
    # Per-bit counter mod 3 held in two ints: `ones` has bit b set if b has been seen
    # 1 (mod 3) times, `twos` if 2 (mod 3).  Seeing a bit a third time clears both.
    # Works for negatives in Python because & ^ ~ act on infinite two's complement.
    ones = twos = 0
    for x in nums:
        ones = (ones ^ x) & ~twos
        twos = (twos ^ x) & ~ones
    return ones
    # Alternative: for each of 32 bits count set bits mod 3, then sign-extend bit 31.


def single_number_iii(nums: List[int]) -> List[int]:
    # XOR of everything = a ^ b (pairs cancel).  Any set bit of it (lowest: x & -x)
    # separates a from b; XOR each group independently.
    xor = 0
    for x in nums:
        xor ^= x
    low = xor & -xor
    a = 0
    for x in nums:
        if x & low:
            a ^= x
    return sorted([a, xor ^ a])


# ---------------------------------------------------------------- Part 2
def count_bits(n: int) -> List[int]:
    # dp[i] = dp[i >> 1] + (i & 1): dropping the low bit is a smaller number.
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i >> 1] + (i & 1)
    return dp


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")     # or Kernighan: while x: x &= x - 1; c += 1


def reverse_bits(n: int) -> int:
    out = 0
    for _ in range(32):
        out = (out << 1) | (n & 1)
        n >>= 1
    return out


def is_power_of_two(n: int) -> bool:
    return n > 0 and n & (n - 1) == 0   # exactly one set bit; guard n <= 0


# ---------------------------------------------------------------- Part 3
def bitmap_bytes(bits: int) -> int:
    # 2^32 possible uint32 values -> 2^32 bits = 2^29 bytes = 512 MiB.
    return (bits + 7) // 8


_POPCOUNT = [bin(i).count("1") for i in range(256)]


class Bitmap:
    """nbits bits packed 8 per byte; bit i lives in buf[i >> 3] at position i & 7."""

    def __init__(self, nbits: int) -> None:
        self.nbits = nbits
        self.buf = bytearray((nbits + 7) // 8)

    def _check(self, i: int) -> None:
        if not 0 <= i < self.nbits:
            raise IndexError(i)

    def set(self, i: int) -> None:
        self._check(i)
        self.buf[i >> 3] |= 1 << (i & 7)

    def clear(self, i: int) -> None:
        self._check(i)
        self.buf[i >> 3] &= 0xFF ^ (1 << (i & 7))

    def get(self, i: int) -> bool:
        self._check(i)
        return (self.buf[i >> 3] >> (i & 7)) & 1 == 1

    def count(self) -> int:
        return sum(_POPCOUNT[b] for b in self.buf)   # table lookup, O(bytes)


class TwoBitBitmap:
    """Two bits per slot (4 slots per byte): 0 = unseen, 1 = seen once, 2 = seen 2+ times."""

    def __init__(self, nslots: int) -> None:
        self.nslots = nslots
        self.buf = bytearray((nslots + 3) // 4)

    def count_of(self, i: int) -> int:
        return (self.buf[i >> 2] >> ((i & 3) * 2)) & 3

    def add(self, i: int) -> None:
        byte, shift = i >> 2, (i & 3) * 2
        v = (self.buf[byte] >> shift) & 3
        if v < 2:                                       # saturate at 2
            self.buf[byte] = (self.buf[byte] & (0xFF ^ (3 << shift))) | ((v + 1) << shift)


def find_duplicates(nums: Iterable[int], universe: int) -> List[int]:
    # One pass to fill the 2-bit map (2 * universe bits), one pass over the universe.
    tb = TwoBitBitmap(universe)
    for x in nums:
        tb.add(x)
    return [i for i in range(universe) if tb.count_of(i) == 2]


# ---------------------------------------------------------------- Part 4
class BloomFilter:
    """m bits, k hash functions.  False-positive rate after n inserts:
        p ~= (1 - e^(-k n / m)) ** k
    Optimal sizing for target p:  m = -n ln p / (ln 2)^2,  k = (m / n) ln 2.
    Double hashing (Kirsch-Mitzenmacher): h_i(x) = h1(x) + i * h2(x) mod m gives k
    independent-enough indexes from two real hashes."""

    def __init__(self, n_expected: int, fp_rate: float) -> None:
        self.m = max(8, math.ceil(-n_expected * math.log(fp_rate) / (math.log(2) ** 2)))
        self.k = max(1, round(self.m / n_expected * math.log(2)))
        self.bits = Bitmap(self.m)
        self.n = 0

    def _indexes(self, item: str) -> List[int]:
        data = item.encode()
        h1 = int.from_bytes(hashlib.md5(data).digest()[:8], "big")
        h2 = int.from_bytes(hashlib.sha1(data).digest()[:8], "big") | 1   # odd -> full period
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, item: str) -> None:
        for idx in self._indexes(item):
            self.bits.set(idx)
        self.n += 1

    def might_contain(self, item: str) -> bool:
        return all(self.bits.get(idx) for idx in self._indexes(item))

    def estimated_fp_rate(self) -> float:
        return (1 - math.exp(-self.k * self.n / self.m)) ** self.k


# ---------------------------------------------------------------- Part 5
def find_maximum_xor(nums: List[int]) -> int:
    # Binary trie over the 31 value bits (nums < 2^31), MSB first.  For each x, walk
    # the trie preferring the OPPOSITE bit at every level: that greedily maximises the
    # XOR because a higher bit outweighs all lower bits.  O(31 n) time and space.
    root: Dict[int, dict] = {}
    best = 0
    for x in nums:
        node = root
        for b in range(30, -1, -1):                       # insert
            node = node.setdefault((x >> b) & 1, {})
        node, acc = root, 0
        for b in range(30, -1, -1):                       # query (x itself is present)
            bit = (x >> b) & 1
            if 1 - bit in node:
                acc |= 1 << b
                node = node[1 - bit]
            else:
                node = node[bit]
        best = max(best, acc)
    return best
    # Alternative without a trie: build the answer bit by bit with a prefix set,
    # checking if (candidate ^ prefix) is in the set.


# ---------------------------------------------------------------- Part 6
def shortest_subarray_or_at_least_k(nums: List[int], k: int) -> int:
    # OR only grows as the window grows, so a two-pointer window works -- but you
    # cannot "subtract" from an OR.  Keep a count per bit; a bit is in the OR iff its
    # count > 0.  For each right end shrink from the left while the OR still >= k.
    BITS = 32
    cnt = [0] * BITS
    cur = 0

    def update(x: int, delta: int) -> None:
        nonlocal cur
        for b in range(BITS):
            if (x >> b) & 1:
                cnt[b] += delta
                if cnt[b] > 0:
                    cur |= 1 << b
                else:
                    cur &= ~(1 << b)

    best = math.inf
    left = 0
    for right, x in enumerate(nums):
        update(x, +1)
        while left <= right and cur >= k:
            best = min(best, right - left + 1)
            update(nums[left], -1)
            left += 1
    return best if best != math.inf else -1
    # O(32 n).  Works for k = 0 (answer 1 if nums is non-empty).


# ---------------------------------------------------------------- Part 7
def top_k_frequent_words_external(words: Iterable[str], k: int, num_buckets: int = 8
                                  ) -> List[Tuple[str, int]]:
    # 1. Partition: hash(word) % num_buckets -> bucket file.  A word's ENTIRE count lives
    #    in one bucket, so the global top-k is a subset of the union of per-bucket top-k.
    #    Pick num_buckets so each bucket's distinct words fit in RAM (~ file / RAM * 2).
    # 2. Count each bucket with a hash map; keep its top-k with a size-k min-heap.
    # 3. k-way merge the sorted per-bucket lists with a heap; take the first k.
    # If a single bucket is still too big: split it again with a different hash, or
    # external-sort the bucket (sorted runs + k-way merge) and count adjacent equal lines.
    buckets = [io.StringIO() for _ in range(num_buckets)]        # stand-ins for files on disk
    for w in words:
        buckets[zlib.crc32(w.encode()) % num_buckets].write(w + "\n")
    per_bucket: List[List[Tuple[str, int]]] = []
    for f in buckets:
        f.seek(0)
        counts = Counter(line.rstrip("\n") for line in f)
        top = heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))
        per_bucket.append(top)                                   # already sorted by nsmallest
    merged = heapq.merge(*per_bucket, key=lambda kv: (-kv[1], kv[0]))
    return list(islice(merged, k))


# ---------------------------------------------------------------- Part 8
class LinearCounter:
    """Bitmap of m bits; each distinct item sets one pseudo-random bit.  With n distinct
    items the expected number of zero bits is V = m * e^(-n/m), so n ~= -m ln(V/m).
    Error ~ 1/sqrt(m) relative for n up to a few times m; beyond that switch to
    HyperLogLog (which stores max leading-zero counts per register instead of bits)."""

    def __init__(self, m: int) -> None:
        self.m = m
        self.bits = Bitmap(m)

    def add(self, item: str) -> None:
        h = int.from_bytes(hashlib.md5(item.encode()).digest()[:8], "big")
        self.bits.set(h % self.m)

    def estimate(self) -> float:
        zeros = self.m - self.bits.count()
        if zeros == 0:
            return float(self.m) * math.log(self.m)              # saturated: unreliable
        return -self.m * math.log(zeros / self.m)

    def merge(self, other: "LinearCounter") -> "LinearCounter":
        # Union of two shards' viewers is the OR of their bitmaps (same m, same hash).
        out = LinearCounter(self.m)
        out.bits.buf = bytearray(a | b for a, b in zip(self.bits.buf, other.bits.buf))
        return out


# ---------------------------------------------------------------- Part 9
def gray_code(n: int) -> List[int]:
    # i ^ (i >> 1): consecutive i differ in the trailing bits, and shifting collapses
    # that to a single flipped bit.  Reflect-and-prefix is the recursive construction.
    return [i ^ (i >> 1) for i in range(1 << n)]


if __name__ == "__main__":
    import random

    # Part 1
    assert single_number([2, 2, 1]) == 1 and single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([-7]) == -7
    assert single_number_ii([2, 2, 3, 2]) == 3 and single_number_ii([0, 1, 0, 1, 0, 1, 99]) == 99
    assert single_number_ii([-2, -2, -2, 5]) == 5 and single_number_ii([-3, -3, -3, -7]) == -7
    assert single_number_iii([1, 2, 1, 3, 2, 5]) == [3, 5]
    assert single_number_iii([-1, 0]) == [-1, 0] and single_number_iii([0, 1]) == [0, 1]
    # Part 2
    assert count_bits(5) == [0, 1, 1, 2, 1, 2] and count_bits(0) == [0]
    assert hamming_distance(1, 4) == 2 and hamming_distance(3, 1) == 1
    assert reverse_bits(0b00000010100101000001111010011100) == 964176192
    assert reverse_bits(0xFFFFFFFD) == 3221225471 and reverse_bits(0) == 0
    assert is_power_of_two(1) and is_power_of_two(16) and not is_power_of_two(3)
    assert not is_power_of_two(0) and not is_power_of_two(-8)
    # Part 3
    assert bitmap_bytes(2**32) == 512 * 2**20
    bm = Bitmap(100)
    for i in (3, 64, 99):
        bm.set(i)
    assert bm.get(3) and bm.get(64) and bm.get(99) and not bm.get(4) and not bm.get(0)
    assert bm.count() == 3
    bm.set(3)
    assert bm.count() == 3
    bm.clear(64)
    assert not bm.get(64) and bm.count() == 2
    try:
        bm.get(100)
        assert False
    except IndexError:
        pass
    tb = TwoBitBitmap(16)
    for _ in range(3):
        tb.add(5)
    tb.add(7)
    assert tb.count_of(5) == 2 and tb.count_of(7) == 1 and tb.count_of(1) == 0 and tb.count_of(6) == 0
    assert find_duplicates([1, 5, 5, 9, 9, 9, 3], 16) == [5, 9]
    assert find_duplicates([], 8) == []
    # Part 4
    bf = BloomFilter(1000, 0.01)
    assert bf.m == 9586 and bf.k == 7
    for i in range(1000):
        bf.add("user:%d" % i)
    assert all(bf.might_contain("user:%d" % i) for i in range(1000))       # no false negatives
    fps = sum(bf.might_contain("other:%d" % i) for i in range(10000))
    assert fps < 300                                                        # ~1% expected
    assert 0.005 < bf.estimated_fp_rate() < 0.02
    # Part 5
    assert find_maximum_xor([3, 10, 5, 25, 2, 8]) == 28 and find_maximum_xor([0]) == 0
    assert find_maximum_xor([14, 70, 53, 83, 49, 91, 36, 80, 92, 51, 66, 70]) == 127
    rng = random.Random(7)
    for _ in range(30):
        xs = [rng.randint(0, 1000) for _ in range(rng.randint(1, 12))]
        assert find_maximum_xor(xs) == max(a ^ b for a in xs for b in xs)
    # Part 6
    assert shortest_subarray_or_at_least_k([1, 2, 3], 2) == 1
    assert shortest_subarray_or_at_least_k([2, 1, 8], 10) == 3
    assert shortest_subarray_or_at_least_k([1, 2], 0) == 1
    assert shortest_subarray_or_at_least_k([1, 2, 3], 7) == -1
    assert shortest_subarray_or_at_least_k([1, 2, 4], 7) == 3
    for _ in range(30):
        xs = [rng.randint(0, 15) for _ in range(rng.randint(1, 8))]
        kk = rng.randint(0, 16)
        brute = -1
        for i in range(len(xs)):
            acc = 0
            for j in range(i, len(xs)):
                acc |= xs[j]
                if acc >= kk and (brute == -1 or j - i + 1 < brute):
                    brute = j - i + 1
        assert shortest_subarray_or_at_least_k(xs, kk) == brute
    # Part 7
    corpus = (["cat"] * 5 + ["dog"] * 5 + ["emu"] * 3 + ["fox"] * 2 + ["ant"] * 2 + ["bee"])
    rng.shuffle(corpus)
    assert top_k_frequent_words_external(iter(corpus), 3, 4) == [("cat", 5), ("dog", 5), ("emu", 3)]
    assert top_k_frequent_words_external(iter(corpus), 5, 2) == [("cat", 5), ("dog", 5), ("emu", 3), ("ant", 2), ("fox", 2)]
    words = ["w%d" % rng.randint(0, 40) for _ in range(2000)]
    expect = sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))[:7]
    assert top_k_frequent_words_external(iter(words), 7, 5) == expect
    assert top_k_frequent_words_external(iter([]), 3) == []
    # Part 8
    lc = LinearCounter(8192)
    for i in range(1000):
        lc.add("viewer:%d" % i)
    assert 900 < lc.estimate() < 1100
    for i in range(1000):
        lc.add("viewer:%d" % i)                                          # duplicates: no change
    assert 900 < lc.estimate() < 1100
    other = LinearCounter(8192)
    for i in range(500, 1500):
        other.add("viewer:%d" % i)
    assert 1350 < lc.merge(other).estimate() < 1650
    assert LinearCounter(64).estimate() == 0
    # Part 9
    assert gray_code(2) == [0, 1, 3, 2] and gray_code(0) == [0] and gray_code(1) == [0, 1]
    g = gray_code(4)
    assert sorted(g) == list(range(16))
    assert all(bin(g[i] ^ g[(i + 1) % 16]).count("1") == 1 for i in range(16))
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: 10 billion ints but the values are 64-bit, not 32-bit -- bitmap still work?
# A: 2^64 bits is impossible; hash-partition the file into chunks that fit RAM and check
#    x's chunk only, or use a Bloom filter if a small false-positive rate is acceptable.
# Q: Why does a Bloom filter never give a false negative, and can you delete from one?
# A: Adding only sets bits, so every bit for a present item stays set.  Deletion needs a
#    counting Bloom filter (a small counter per slot instead of a bit).
# Q: single_number_ii for "every value appears k times except one appearing once"?
# A: Count each of the 32 bit positions mod k (32 * n), then reassemble and sign-extend.
# Q: Top-K words when one word dominates and its bucket alone exceeds RAM?
# A: The bucket's DISTINCT count is what matters, not its line count; counting streams
#    the file so a single hot word is cheap.  A bucket with too many distinct words gets
#    re-partitioned with a second hash.
# Q: Linear counting vs HyperLogLog?
# A: Linear counting needs O(n) bits and degrades when the bitmap fills; HLL uses a few
#    KB for billions of items with ~2% error.  Both merge by combining registers (OR / max).
