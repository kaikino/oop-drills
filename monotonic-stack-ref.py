"""
MONOTONIC STACK -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "Every problem here is 'for each element, find the nearest element to
the left/right that is bigger/smaller'. Tell me what your stack holds, in
what order, and why an element that gets popped can never matter again."

------------------------------------------------------------------------------
Part 1  Days until the price next rises (LC739, daily temperatures).
        `prices[i]` is a product's price on day i. Return `wait[i]` = number
        of days until a STRICTLY higher price appears, 0 if it never does.
        Example: [73,74,75,71,69,72,76,73] -> [1,1,4,2,1,1,0,0]
        Constraints: 1 <= n <= 1e5.
        Target: O(n) time, O(n) stack. (Brute force O(n^2) is the warm-up.)

        Follow-up 1a  Return the INDEX of the next higher day instead
        (-1 if none):  same input -> [1,2,6,5,5,6,-1,-1].

        Follow-up 1b  Prices arrive one per day as a stream. Implement
        `RiseStream.push(price) -> List[int]`: the indices (0-based, in
        INCREASING order) of earlier days whose next rise is today. Each day
        is reported at most once; days that never rise are never reported.
        Example: pushes 73,74,75,71,69,72,76,73 return
                 [],[0],[1],[],[],[3,4],[2,5],[]
        Target: amortised O(1) per push, memory O(unresolved days).

Part 2  Next greater element II (LC503). CIRCULAR array: for each element
        return the first strictly greater element found walking right and
        wrapping around; -1 if none.
        Example: [1,2,1] -> [2,-1,2];  [5,4,3,2,1] -> [-1,5,5,5,5]
        Constraints: 1 <= n <= 1e4.
        Target: O(n) -- walk 2n indices modulo n with one stack.

Part 3  Remove K digits (LC402). `num` is a non-negative integer as a
        string; remove exactly k digits so the remaining number is as small
        as possible. Strip leading zeros; return "0" if nothing is left.
        Example: "1432219", k=3 -> "1219";  "10200", k=1 -> "200";
                 "10", k=2 -> "0"
        Constraints: 1 <= len(num) <= 1e5, 0 <= k <= len(num).
        Target: O(n) with a non-decreasing stack.

Part 4  Largest rectangle in histogram (LC84). `heights[i]` are bar heights
        of width 1; return the area of the largest axis-aligned rectangle
        fitting under the skyline.
        Example: [2,1,5,6,2,3] -> 10;  [2,4] -> 4
        Constraints: 0 <= n <= 1e5, 0 <= heights[i] <= 1e4.
        Target: O(n) with an increasing stack of indices; the O(n^2)
        "expand from each bar" solution is the warm-up.

Part 5  Online stock span (LC901). `StockSpanner.next(price)` returns the
        number of consecutive days ending today (inclusive) whose price is
        <= today's price. Calls arrive one at a time.
        Example: next(100)=1, next(80)=1, next(60)=1, next(70)=2,
                 next(60)=1, next(75)=4, next(85)=6
        Constraints: up to 1e4 calls.
        Target: amortised O(1) per call.
------------------------------------------------------------------------------
"""
from __future__ import annotations

from typing import List, Tuple


# ---------------------------------------------------------------- Part 1
def days_until_price_rises(prices: List[int]) -> List[int]:
    # Stack holds INDICES of days still waiting for a rise; their prices are
    # strictly decreasing bottom->top. A new price resolves every stacked day
    # with a smaller price -- once popped a day is done, hence O(n) total.
    n = len(prices)
    wait = [0] * n
    stack: List[int] = []
    for i, p in enumerate(prices):
        while stack and prices[stack[-1]] < p:
            j = stack.pop()
            wait[j] = i - j
        stack.append(i)
    return wait  # O(n) time, O(n) space


def next_rise_index(prices: List[int]) -> List[int]:
    # Identical scan; store the resolving index instead of the distance.
    n = len(prices)
    out = [-1] * n
    stack: List[int] = []
    for i, p in enumerate(prices):
        while stack and prices[stack[-1]] < p:
            out[stack.pop()] = i
        stack.append(i)
    return out


class RiseStream:
    # Same stack, but we cannot afford the full price history: keep
    # (index, price) pairs for UNRESOLVED days only.
    def __init__(self) -> None:
        self._day = 0
        self._stack: List[Tuple[int, int]] = []

    def push(self, price: int) -> List[int]:
        resolved: List[int] = []
        while self._stack and self._stack[-1][1] < price:
            resolved.append(self._stack.pop()[0])
        self._stack.append((self._day, price))
        self._day += 1
        resolved.reverse()  # popped newest-first; spec wants increasing
        return resolved  # amortised O(1) per push


# ---------------------------------------------------------------- Part 2
def next_greater_circular(nums: List[int]) -> List[int]:
    # Walk i = 0..2n-1 and look at nums[i % n]; only PUSH during the first
    # lap (second lap exists only to resolve leftovers by wrapping around).
    n = len(nums)
    out = [-1] * n
    stack: List[int] = []
    for i in range(2 * n):
        x = nums[i % n]
        while stack and nums[stack[-1]] < x:
            out[stack.pop()] = x
        if i < n:
            stack.append(i)
    return out  # O(n): each index pushed once, popped at most once


# ---------------------------------------------------------------- Part 3
def remove_k_digits(num: str, k: int) -> str:
    # Greedy: a digit that is larger than the digit after it should be
    # removed first (it makes the higher-order position smaller). Keep the
    # stack non-decreasing; leftover k removes from the tail (largest end).
    stack: List[str] = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    if k:  # pitfall: stack[:-0] is EMPTY, so guard k == 0 explicitly
        stack = stack[:len(stack) - k]
    result = "".join(stack).lstrip("0")
    return result or "0"  # O(n)


# ---------------------------------------------------------------- Part 4
def largest_rectangle(heights: List[int]) -> int:
    # Stack of indices with non-decreasing heights. When a lower bar arrives,
    # every taller stacked bar has found its RIGHT boundary (i); its LEFT
    # boundary is the new stack top. Append a sentinel 0 to flush the stack.
    stack: List[int] = []
    best = 0
    n = len(heights)
    for i in range(n + 1):
        h = 0 if i == n else heights[i]
        while stack and heights[stack[-1]] >= h:
            top = stack.pop()
            left = stack[-1] if stack else -1
            best = max(best, heights[top] * (i - left - 1))
        stack.append(i)
    return best  # O(n) time, O(n) space


# ---------------------------------------------------------------- Part 5
class StockSpanner:
    # Stack of (price, span). A popped day is dominated by today's price, so
    # any later day that beats today also beats it -- its span is absorbed.
    def __init__(self) -> None:
        self._stack: List[Tuple[int, int]] = []

    def next(self, price: int) -> int:
        span = 1
        while self._stack and self._stack[-1][0] <= price:
            span += self._stack.pop()[1]
        self._stack.append((price, span))
        return span  # amortised O(1)


if __name__ == "__main__":
    # Part 1
    assert days_until_price_rises([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert days_until_price_rises([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert days_until_price_rises([30, 60, 90]) == [1, 1, 0]
    assert days_until_price_rises([5, 5, 5]) == [0, 0, 0]
    assert days_until_price_rises([9, 8, 7, 10]) == [3, 2, 1, 0]
    assert days_until_price_rises([]) == []

    assert next_rise_index([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 2, 6, 5, 5, 6, -1, -1]
    assert next_rise_index([5, 5, 5]) == [-1, -1, -1]
    assert next_rise_index([1, 2]) == [1, -1]

    rs = RiseStream()
    got = [rs.push(p) for p in [73, 74, 75, 71, 69, 72, 76, 73]]
    assert got == [[], [0], [1], [], [], [3, 4], [2, 5], []], got
    rs = RiseStream()
    assert [rs.push(p) for p in [3, 2, 1, 4]] == [[], [], [], [0, 1, 2]]
    rs = RiseStream()
    assert [rs.push(p) for p in [2, 2, 3]] == [[], [], [0, 1]]

    # Part 2
    assert next_greater_circular([1, 2, 1]) == [2, -1, 2]
    assert next_greater_circular([1, 2, 3, 4, 3]) == [2, 3, 4, -1, 4]
    assert next_greater_circular([5, 4, 3, 2, 1]) == [-1, 5, 5, 5, 5]
    assert next_greater_circular([1, 1, 1]) == [-1, -1, -1]
    assert next_greater_circular([3]) == [-1]
    assert next_greater_circular([2, 1, 3, 1]) == [3, 3, -1, 2]

    # Part 3
    assert remove_k_digits("1432219", 3) == "1219"
    assert remove_k_digits("10200", 1) == "200"
    assert remove_k_digits("10", 2) == "0"
    assert remove_k_digits("9", 1) == "0"
    assert remove_k_digits("112", 1) == "11"
    assert remove_k_digits("12345", 2) == "123"
    assert remove_k_digits("54321", 2) == "321"
    assert remove_k_digits("100", 1) == "0"
    assert remove_k_digits("10001", 1) == "1"
    assert remove_k_digits("12345", 0) == "12345"

    # Part 4
    assert largest_rectangle([2, 1, 5, 6, 2, 3]) == 10
    assert largest_rectangle([2, 4]) == 4
    assert largest_rectangle([1]) == 1
    assert largest_rectangle([]) == 0
    assert largest_rectangle([2, 2, 2]) == 6
    assert largest_rectangle([5, 4, 3, 2, 1]) == 9
    assert largest_rectangle([1, 2, 3, 4, 5]) == 9
    assert largest_rectangle([0, 0]) == 0
    assert largest_rectangle([3, 0, 3]) == 3

    # Part 5
    sp = StockSpanner()
    assert [sp.next(p) for p in [100, 80, 60, 70, 60, 75, 85]] == [1, 1, 1, 2, 1, 4, 6]
    sp = StockSpanner()
    assert [sp.next(p) for p in [1, 1, 1]] == [1, 2, 3]
    sp = StockSpanner()
    assert [sp.next(p) for p in [5, 4, 3, 2, 1]] == [1, 1, 1, 1, 1]
    sp = StockSpanner()
    assert [sp.next(p) for p in [1, 2, 3, 4]] == [1, 2, 3, 4]

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part 1 -- why is the while loop inside the for loop still O(n)?
# A: Each index is pushed exactly once and popped at most once; the pops are
#    paid for by the pushes (amortised analysis).
# Q: Part 1b -- what does the stream version have to store, and how much?
# A: Only the unresolved (index, price) pairs; that is the stack itself. In
#    the worst case (strictly decreasing prices) that is all of them, O(n).
# Q: Part 2 -- why not just concatenate nums + nums and run Part 1?
# A: That works but doubles memory; iterating i in range(2n) with i % n and
#    only pushing in the first lap gives the same effect in O(n) extra space.
# Q: Part 3 -- why does a non-DEcreasing stack ("pop while top > d") give the
#    minimum, and what if k is still > 0 at the end?
# A: The leftmost digit dominates the value, so replace a large high-order
#    digit with a smaller one as early as possible. If the digits are already
#    non-decreasing, no pop ever fires; the largest digits are at the tail, so
#    cut k from the end.
# Q: Part 4 -- what does each popped bar's rectangle look like, exactly?
# A: Height = the popped bar; right edge = current i (first shorter bar);
#    left edge = the new stack top (previous shorter-or-equal bar), so width
#    is i - left - 1. Equal heights: `>=` pops them early but the last equal
#    bar computes the full width, so no area is lost.
# Q: Part 5 -- why can days that were popped be forgotten forever?
# A: If today's price >= theirs, any future day that beats today's price also
#    beats theirs, and today's span already includes them.
