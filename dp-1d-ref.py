from __future__ import annotations

"""
1-D dynamic programming — reference solutions.

Part 1 — Climbing stairs.
    "A creator's follower count climbs by 1 or 2 each day. How many distinct
    day-by-day paths reach exactly n?"  climb_stairs(n) -> int.
    Example: n=3 -> 3 (1+1+1, 1+2, 2+1).  1 <= n <= 45.  Target O(n) time, O(1) space.

Part 2 — House robber I and II.
    "Each shop on a street holds nums[i] cash; you cannot hit two adjacent shops.
    Max haul?"  rob(nums).  Then the street is a circle (first and last are
    adjacent): rob_circular(nums).
    Example: [2,7,9,3,1] -> 12.  Circular [2,3,2] -> 3.  O(n) time, O(1) space.

Part 3 — Coin change (min coins) and coin change II (count ways).
    "Coupon denominations coins[], target amount. Fewest coupons that sum
    exactly to amount, or -1."  coin_change(coins, amount).
    Then: "How many distinct combinations (order does not matter) sum to amount?"
    coin_change_ways(coins, amount).  Explain the loop order difference.
    Example: coins=[1,2,5], amount=11 -> 3 (5+5+1).  ways(amount=5) -> 4.
    O(len(coins) * amount) time, O(amount) space.

Part 4 — Longest increasing subsequence.
    lis_quadratic(nums) in O(n^2), then lis_nlogn(nums) using patience sorting
    with bisect.  Example: [10,9,2,5,3,7,101,18] -> 4.

Part 5 — Word break.
    "Can s be segmented into a sequence of dictionary words (reuse allowed)?"
    word_break(s, words).  Example: "leetcode", ["leet","code"] -> True.
    O(n^2) with a set (or O(n * max_word_len)).

Part 6 — Decode ways, then with '*' wildcard.
    'A'..'Z' map to 1..26.  num_decodings("226") -> 3.  Then '*' stands for
    any digit 1..9: num_decodings_wildcard("1*") -> 18, answer mod 1e9+7.

Part 7 — Buy/sell stock: I, II (unlimited), with cooldown, with fee, at most K.
    max_profit_one(prices), max_profit_unlimited(prices),
    max_profit_cooldown(prices), max_profit_fee(prices, fee),
    max_profit_k(k, prices).  Present the state machine: hold / not-hold
    (/ cooling).  Examples: [7,1,5,3,6,4] -> 5 (I), 7 (II).
    [1,2,3,0,2] cooldown -> 3.  [1,3,2,8,4,9] fee=2 -> 8.  k=2 [3,2,6,5,0,3] -> 7.

Part 8 — Partition equal subset sum.
    "Split nums into two groups of equal sum?"  can_partition(nums).
    Example: [1,5,11,5] -> True.  0/1 knapsack over sum/2; mention the bitset
    trick (an int as a bitset: bits |= bits << x).

Part 9 — Make strictly increasing / make distinct by incrementing.
    min_ops_strictly_increasing(nums): min number of +1 operations so nums is
    strictly increasing (order fixed).  [1,1,1] -> 3.
    min_sum_after_distinct(nums): you may only increment; make all values
    distinct; return the minimum possible total sum.  [3,2,1,2,1,7] -> 22.

Part 10 — Jump game I, II, and jump game with energy.
    can_jump(nums) -> bool, jump(nums) -> min jumps (greedy).
    min_starting_energy(delta): platforms 0..n-1; landing on i changes your
    energy by delta[i] (negative = cost, positive = boost).  From i you may
    jump to i+1 or i+2.  Energy must be >= 0 after every landing (including
    platform 0).  Return the minimum starting energy to reach platform n-1.
    Example: [-5,-2,-3] -> 8 (land 0: 3, jump to 2: 0).  O(n).
"""

from bisect import bisect_left
from typing import List

MOD = 10**9 + 7


# ---------------------------------------------------------------- Part 1
def climb_stairs(n: int) -> int:
    # state: f[i] = ways to reach step i; f[i] = f[i-1] + f[i-2]; f[0]=f[1]=1
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a  # O(n) time, O(1) space


# ---------------------------------------------------------------- Part 2
def rob(nums: List[int]) -> int:
    # state: take = best ending by robbing i, skip = best not robbing i
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(skip, take)
    return max(take, skip)


def rob_circular(nums: List[int]) -> int:
    # Either house 0 is never robbed or house n-1 is never robbed.
    if len(nums) == 1:
        return nums[0]
    return max(rob(nums[1:]), rob(nums[:-1]))


# ---------------------------------------------------------------- Part 3
def coin_change(coins: List[int], amount: int) -> int:
    # dp[a] = fewest coins to make a; dp[0] = 0; dp[a] = min(dp[a-c]) + 1
    INF = amount + 1  # a safe "infinity": can never need more than `amount` coins of value>=1
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != INF else -1


def coin_change_ways(coins: List[int], amount: int) -> int:
    # dp[a] = number of combinations summing to a.  COINS IN THE OUTER LOOP so
    # each combination is counted once (in coin order).  Amount-outer would count
    # permutations (1+2 and 2+1 separately) -- that is the "combination sum IV" answer.
    dp = [1] + [0] * amount
    for c in coins:
        for a in range(c, amount + 1):  # ascending: unbounded knapsack (reuse coin)
            dp[a] += dp[a - c]
    return dp[amount]


# ---------------------------------------------------------------- Part 4
def lis_quadratic(nums: List[int]) -> int:
    # dp[i] = length of LIS ending at i
    if not nums:
        return 0
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)


def lis_nlogn(nums: List[int]) -> int:
    # tails[k] = smallest tail of any increasing subsequence of length k+1.
    # tails stays sorted; replace the first tail >= x (bisect_left => strict LIS;
    # use bisect_right for non-decreasing).
    tails: List[int] = []
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)


# ---------------------------------------------------------------- Part 5
def word_break(s: str, words: List[str]) -> bool:
    # dp[i] = s[:i] can be segmented; dp[0] = True
    wordset = set(words)
    max_len = max((len(w) for w in words), default=0)
    dp = [True] + [False] * len(s)
    for i in range(1, len(s) + 1):
        for j in range(max(0, i - max_len), i):
            if dp[j] and s[j:i] in wordset:
                dp[i] = True
                break
    return dp[len(s)]


# ---------------------------------------------------------------- Part 6
def num_decodings(s: str) -> int:
    # dp[i] = ways to decode s[:i]; dp[0] = 1.  Pitfall: '0' contributes nothing alone.
    if not s or s[0] == "0":
        return 0
    prev2, prev1 = 1, 1  # dp[i-2], dp[i-1]
    for i in range(1, len(s)):
        cur = 0
        if s[i] != "0":
            cur += prev1
        two = int(s[i - 1 : i + 1])
        if 10 <= two <= 26:
            cur += prev2
        prev2, prev1 = prev1, cur
    return prev1


def num_decodings_wildcard(s: str) -> int:
    # Same recurrence; each transition now has a multiplicity.
    def single(c: str) -> int:
        return 9 if c == "*" else (0 if c == "0" else 1)

    def double(a: str, b: str) -> int:
        if a == "*" and b == "*":
            return 15          # 11-19 (9) + 21-26 (6)
        if a == "*":
            return 2 if b <= "6" else 1   # 1b and 2b
        if b == "*":
            return 9 if a == "1" else (6 if a == "2" else 0)
        return 1 if 10 <= int(a + b) <= 26 else 0

    prev2, prev1 = 1, single(s[0])
    for i in range(1, len(s)):
        cur = (single(s[i]) * prev1 + double(s[i - 1], s[i]) * prev2) % MOD
        prev2, prev1 = prev1, cur
    return prev1 % MOD


# ---------------------------------------------------------------- Part 7
# State machine: hold = best cash while holding one share, free = best cash holding none.
def max_profit_one(prices: List[int]) -> int:
    best, lo = 0, float("inf")
    for p in prices:
        lo = min(lo, p)
        best = max(best, p - lo)
    return best


def max_profit_unlimited(prices: List[int]) -> int:
    # Sum of every positive daily delta == greedy; equivalent to the 2-state DP.
    return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, len(prices)))


def max_profit_cooldown(prices: List[int]) -> int:
    # states: hold, free (can buy tomorrow), cool (just sold; must wait a day)
    hold, free, cool = float("-inf"), 0, 0
    for p in prices:
        hold, free, cool = max(hold, free - p), max(free, cool), hold + p
    return max(free, cool)


def max_profit_fee(prices: List[int], fee: int) -> int:
    hold, free = float("-inf"), 0
    for p in prices:
        hold, free = max(hold, free - p), max(free, hold + p - fee)
    return free


def max_profit_k(k: int, prices: List[int]) -> int:
    n = len(prices)
    if n == 0 or k == 0:
        return 0
    if k >= n // 2:                      # enough for every up-tick: unlimited case
        return max_profit_unlimited(prices)
    # hold[j] / free[j] = best cash after at most j transactions (a buy opens a transaction)
    hold = [float("-inf")] * (k + 1)
    free = [0] * (k + 1)
    for p in prices:
        for j in range(k, 0, -1):        # descending so each day is used at most once per j
            free[j] = max(free[j], hold[j] + p)
            hold[j] = max(hold[j], free[j - 1] - p)
    return free[k]
    # O(n*k) time, O(k) space.


# ---------------------------------------------------------------- Part 8
def can_partition(nums: List[int]) -> bool:
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    # 0/1 knapsack: dp[s] = some subset sums to s.  Iterate s DESCENDING so each
    # item is used at most once (ascending would be unbounded).
    dp = [True] + [False] * target
    for x in nums:
        for s in range(target, x - 1, -1):
            if dp[s - x]:
                dp[s] = True
    return dp[target]
    # Bitset trick: bits = 1; for x in nums: bits |= bits << x; return bits >> target & 1


# ---------------------------------------------------------------- Part 9
def min_ops_strictly_increasing(nums: List[int]) -> int:
    # Greedy: each element only needs to beat the (already fixed) previous one by 1.
    ops, prev = 0, float("-inf")
    for x in nums:
        need = max(x, prev + 1)
        ops += need - x
        prev = need
    return ops


def min_sum_after_distinct(nums: List[int]) -> int:
    # Sort; then the same greedy. Order does not matter for distinctness, and
    # raising the smallest values first never hurts (exchange argument).
    total, prev = 0, float("-inf")
    for x in sorted(nums):
        cur = max(x, prev + 1)
        total += cur
        prev = cur
    return total


# ---------------------------------------------------------------- Part 10
def can_jump(nums: List[int]) -> bool:
    reach = 0
    for i, x in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + x)
    return True


def jump(nums: List[int]) -> int:
    # BFS-by-levels greedy: `end` is the edge of the current jump's range.
    jumps = end = farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == end:
            jumps += 1
            end = farthest
    return jumps


def min_starting_energy(delta: List[int]) -> int:
    # Backward DP (1-D "dungeon game"): need[i] = min energy on ARRIVAL at i so
    # that the end is reachable.  need[i] = max(0, min(need[i+1], need[i+2]) - delta[i]).
    # Forward DP does not work: you can't greedily know which branch is better.
    n = len(delta)
    need = [0] * (n + 2)
    need[n - 1] = max(0, -delta[n - 1])
    for i in range(n - 2, -1, -1):
        nxt = need[i + 1] if i + 2 >= n else min(need[i + 1], need[i + 2])
        need[i] = max(0, nxt - delta[i])
    return need[0]


if __name__ == "__main__":
    # Part 1
    assert climb_stairs(1) == 1 and climb_stairs(2) == 2 and climb_stairs(3) == 3
    assert climb_stairs(10) == 89
    # Part 2
    assert rob([1, 2, 3, 1]) == 4 and rob([2, 7, 9, 3, 1]) == 12 and rob([]) == 0
    assert rob_circular([2, 3, 2]) == 3 and rob_circular([1, 2, 3, 1]) == 4
    assert rob_circular([1, 2, 3]) == 3 and rob_circular([1]) == 1
    # Part 3
    assert coin_change([1, 2, 5], 11) == 3 and coin_change([2], 3) == -1 and coin_change([1], 0) == 0
    assert coin_change_ways([1, 2, 5], 5) == 4 and coin_change_ways([2], 3) == 0
    assert coin_change_ways([10], 10) == 1
    # Part 4
    for f in (lis_quadratic, lis_nlogn):
        assert f([10, 9, 2, 5, 3, 7, 101, 18]) == 4
        assert f([0, 1, 0, 3, 2, 3]) == 4 and f([7, 7, 7]) == 1 and f([]) == 0
    # Part 5
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("applepenapple", ["apple", "pen"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    # Part 6
    assert num_decodings("12") == 2 and num_decodings("226") == 3
    assert num_decodings("06") == 0 and num_decodings("0") == 0 and num_decodings("10") == 1
    assert num_decodings_wildcard("*") == 9 and num_decodings_wildcard("1*") == 18
    assert num_decodings_wildcard("2*") == 15 and num_decodings_wildcard("**") == 96
    assert num_decodings_wildcard("226") == 3 and num_decodings_wildcard("0*") == 0
    # Part 7
    assert max_profit_one([7, 1, 5, 3, 6, 4]) == 5 and max_profit_one([7, 6, 4, 3, 1]) == 0
    assert max_profit_unlimited([7, 1, 5, 3, 6, 4]) == 7
    assert max_profit_cooldown([1, 2, 3, 0, 2]) == 3 and max_profit_cooldown([1]) == 0
    assert max_profit_fee([1, 3, 2, 8, 4, 9], 2) == 8
    assert max_profit_k(2, [3, 2, 6, 5, 0, 3]) == 7 and max_profit_k(2, [2, 4, 1]) == 2
    assert max_profit_k(100, [7, 1, 5, 3, 6, 4]) == 7 and max_profit_k(0, [1, 2]) == 0
    # Part 8
    assert can_partition([1, 5, 11, 5]) is True and can_partition([1, 2, 3, 5]) is False
    # Part 9
    assert min_ops_strictly_increasing([1, 1, 1]) == 3
    assert min_ops_strictly_increasing([1, 5, 2, 4, 1]) == 14
    assert min_ops_strictly_increasing([8]) == 0
    assert min_sum_after_distinct([3, 2, 1, 2, 1, 7]) == 22
    assert min_sum_after_distinct([1, 2, 2]) == 6
    # Part 10
    assert can_jump([2, 3, 1, 1, 4]) is True and can_jump([3, 2, 1, 0, 4]) is False
    assert jump([2, 3, 1, 1, 4]) == 2 and jump([2, 3, 0, 1, 4]) == 2 and jump([0]) == 0
    assert min_starting_energy([-5, -2, -3]) == 8
    assert min_starting_energy([0, -3, 5, -10, 2, -1]) == 0
    assert min_starting_energy([-1]) == 1 and min_starting_energy([4, -10]) == 6
    print("ok")


# INTERVIEWER FOLLOW-UPS
# Q: Why does coin_change_ways put coins in the outer loop?
# A: So each combination is built in a fixed coin order and counted once; amount-outer
#    counts ordered sequences (permutations).
# Q: In can_partition, why iterate the sum descending?
# A: dp[s-x] must still be the value from BEFORE item x was considered (0/1). Ascending
#    would let x be reused -> unbounded knapsack.
# Q: How would you reconstruct the LIS itself from the O(n log n) version?
# A: Store, for each element, its predecessor (the tail it was placed after) and its
#    slot index; walk back from the last element placed in the final slot.
# Q: max_profit_k when k is huge?
# A: k >= n/2 means you can take every up-tick, so fall back to the unlimited O(n) greedy.
# Q: Cooldown DP: why three states, not two?
# A: The day after a sell you may not buy, so "free" must know whether it became free
#    today (cool) or earlier (free).
