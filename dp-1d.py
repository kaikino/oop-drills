from __future__ import annotations

"""
1-D dynamic programming.

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
    pass


def rob(nums: List[int]) -> int:
    pass


def rob_circular(nums: List[int]) -> int:
    pass


def coin_change(coins: List[int], amount: int) -> int:
    pass


def coin_change_ways(coins: List[int], amount: int) -> int:
    pass


def lis_quadratic(nums: List[int]) -> int:
    pass


def lis_nlogn(nums: List[int]) -> int:
    pass


def word_break(s: str, words: List[str]) -> bool:
    pass


def num_decodings(s: str) -> int:
    pass


def num_decodings_wildcard(s: str) -> int:
    pass


def max_profit_one(prices: List[int]) -> int:
    pass


def max_profit_unlimited(prices: List[int]) -> int:
    pass


def max_profit_cooldown(prices: List[int]) -> int:
    pass


def max_profit_fee(prices: List[int], fee: int) -> int:
    pass


def max_profit_k(k: int, prices: List[int]) -> int:
    pass


def can_partition(nums: List[int]) -> bool:
    pass


def min_ops_strictly_increasing(nums: List[int]) -> int:
    pass


def min_sum_after_distinct(nums: List[int]) -> int:
    pass


def can_jump(nums: List[int]) -> bool:
    pass


def jump(nums: List[int]) -> int:
    pass


def min_starting_energy(delta: List[int]) -> int:
    pass


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
