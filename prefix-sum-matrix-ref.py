"""
PREFIX SUMS & MATRICES -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "Precompute something once so that every position or every query is
O(1). For the in-place matrix parts, say out loud which cells you are
allowed to overwrite and at what point they stop being needed."

------------------------------------------------------------------------------
Part 1  Subarray sum equals k (LC560). Count CONTIGUOUS subarrays whose sum
        is exactly k. Values may be negative or zero, so a sliding window
        does not work. Flavour: `nums[i]` = net change in a seller's daily
        balance; count the day-ranges that net to exactly k.
        Example: [1,1,1], k=2 -> 2;  [1,2,3], k=3 -> 2;  [0,0,0], k=0 -> 6
        Constraints: 1 <= n <= 2e4, |nums[i]| <= 1000.
        Target: O(n) time, O(n) space (hashmap of prefix-sum counts).

Part 2  Product of array except self (LC238). `out[i]` = product of all
        elements except nums[i]. NO division, O(n) time, O(1) extra space
        (the output array does not count). Zeros must work.
        Example: [1,2,3,4] -> [24,12,8,6];  [-1,1,0,-3,3] -> [0,0,9,0,0]
        Constraints: 2 <= n <= 1e5.

Part 3  Set matrix zeroes (LC73) -- asked in a TikTok backend first round.
        If a cell is 0, set its entire row and column to 0, IN PLACE.
        Warm-up: O(m+n) extra with a row-set and a column-set. Then O(1)
        extra: use row 0 and column 0 as the marker arrays.
        Example: [[1,1,1],[1,0,1],[1,1,1]] -> [[1,0,1],[0,0,0],[1,0,1]]
        Constraints: 1 <= m, n <= 200.
        Target: O(mn) time, O(1) extra space.

Part 4  Range sum query 2D, immutable (LC304). Build once, then answer
        `sum_region(r1, c1, r2, c2)` (inclusive corners) in O(1).
        Example: matrix [[3,0,1,4,2],[5,6,3,2,1],[1,2,0,1,5],[4,1,0,1,7],
                 [1,0,3,0,5]]: sum_region(2,1,4,3) -> 8,
                 sum_region(1,1,2,2) -> 11, sum_region(1,2,2,4) -> 12
        Constraints: m, n <= 200, up to 1e4 queries.
        Target: O(mn) build, O(1) query, O(mn) space.

Part 5  Spiral order (LC54) and rotate image 90 degrees clockwise IN PLACE
        (LC48). Spiral must handle non-square, single-row and single-column
        inputs without duplicating cells.
        Example: [[1,2,3],[4,5,6],[7,8,9]] -> spiral [1,2,3,6,9,8,7,4,5];
                 rotate -> [[7,4,1],[8,5,2],[9,6,3]]
        Target: O(mn) time; rotate uses O(1) extra space.
------------------------------------------------------------------------------
"""
from __future__ import annotations

from collections import Counter
from typing import List


# ---------------------------------------------------------------- Part 1
def subarray_sum(nums: List[int], k: int) -> int:
    # prefix[j] - prefix[i] == k  <=>  prefix[i] == prefix[j] - k.
    # Count how many earlier prefixes equal (current - k). Seed {0: 1} so a
    # subarray starting at index 0 counts. Pitfall: update the count AFTER
    # the lookup, otherwise k == 0 counts the empty subarray.
    seen: Counter = Counter({0: 1})
    total = count = 0
    for x in nums:
        total += x
        count += seen[total - k]  # Counter returns 0 without inserting
        seen[total] += 1
    return count  # O(n) time, O(n) space


# ---------------------------------------------------------------- Part 2
def product_except_self(nums: List[int]) -> List[int]:
    # Pass 1: out[i] = product of everything LEFT of i.
    # Pass 2: multiply by a running product of everything RIGHT of i.
    n = len(nums)
    out = [1] * n
    run = 1
    for i in range(n):
        out[i] = run
        run *= nums[i]
    run = 1
    for i in range(n - 1, -1, -1):
        out[i] *= run
        run *= nums[i]
    return out  # O(n) time, O(1) extra space


# ---------------------------------------------------------------- Part 3
def set_zeroes(matrix: List[List[int]]) -> None:
    # Use row 0 / col 0 as the marker arrays. Their own zero-status must be
    # remembered SEPARATELY before they get overwritten with marks, and
    # they must be zeroed LAST (otherwise the marks poison everything).
    m, n = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][j] == 0 for j in range(n))
    first_col_zero = any(matrix[i][0] == 0 for i in range(m))
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][j] == 0:
                matrix[i][0] = 0
                matrix[0][j] = 0
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][0] == 0 or matrix[0][j] == 0:
                matrix[i][j] = 0
    if first_row_zero:
        for j in range(n):
            matrix[0][j] = 0
    if first_col_zero:
        for i in range(m):
            matrix[i][0] = 0
    # O(mn) time, O(1) extra space


# ---------------------------------------------------------------- Part 4
class NumMatrix:
    # P[i][j] = sum of matrix[0..i-1][0..j-1] (one extra row/col of zeros
    # avoids all boundary special-casing). Inclusion-exclusion for queries.
    def __init__(self, matrix: List[List[int]]) -> None:
        m = len(matrix)
        n = len(matrix[0]) if m else 0
        self._p = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            row, above = self._p[i + 1], self._p[i]
            for j in range(n):
                row[j + 1] = matrix[i][j] + row[j] + above[j + 1] - above[j]

    def sum_region(self, r1: int, c1: int, r2: int, c2: int) -> int:
        p = self._p
        return p[r2 + 1][c2 + 1] - p[r1][c2 + 1] - p[r2 + 1][c1] + p[r1][c1]
        # O(1) per query


# ---------------------------------------------------------------- Part 5
def spiral_order(matrix: List[List[int]]) -> List[int]:
    # Four shrinking boundaries. Pitfall: after the top row and right column,
    # re-check top <= bottom and left <= right or a single row/column gets
    # emitted twice.
    out: List[int] = []
    if not matrix or not matrix[0]:
        return out
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            out.append(matrix[top][j])
        top += 1
        for i in range(top, bottom + 1):
            out.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                out.append(matrix[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                out.append(matrix[i][left])
            left += 1
    return out  # O(mn)


def rotate(matrix: List[List[int]]) -> None:
    # Clockwise 90 = transpose, then reverse each row. (Counter-clockwise =
    # transpose, then reverse each column / reverse row order.)
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):  # only above the diagonal, or you undo it
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    # O(n^2) time, O(1) extra space


if __name__ == "__main__":
    # Part 1
    assert subarray_sum([1, 1, 1], 2) == 2
    assert subarray_sum([1, 2, 3], 3) == 2
    assert subarray_sum([1, -1, 0], 0) == 3
    assert subarray_sum([0, 0, 0], 0) == 6
    assert subarray_sum([-1, -1, 1], 0) == 1
    assert subarray_sum([3, 4, 7, 2, -3, 1, 4, 2], 7) == 4
    assert subarray_sum([1], 2) == 0

    # Part 2
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    assert product_except_self([2, 3]) == [3, 2]
    assert product_except_self([0, 0]) == [0, 0]
    assert product_except_self([5, 1, 1]) == [1, 5, 5]

    # Part 3
    g = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]; set_zeroes(g); assert g == [[1, 0, 1], [0, 0, 0], [1, 0, 1]]
    g = [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]; set_zeroes(g); assert g == [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]
    g = [[1, 2], [3, 4]]; set_zeroes(g); assert g == [[1, 2], [3, 4]]
    g = [[0]]; set_zeroes(g); assert g == [[0]]
    g = [[1, 0]]; set_zeroes(g); assert g == [[0, 0]]
    g = [[1], [0]]; set_zeroes(g); assert g == [[0], [0]]
    g = [[1, 2, 3], [4, 0, 6], [7, 8, 0]]; set_zeroes(g); assert g == [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    g = [[0, 1], [1, 1]]; set_zeroes(g); assert g == [[0, 0], [0, 1]]

    # Part 4
    nm = NumMatrix([[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]])
    assert nm.sum_region(2, 1, 4, 3) == 8
    assert nm.sum_region(1, 1, 2, 2) == 11
    assert nm.sum_region(1, 2, 2, 4) == 12
    assert nm.sum_region(0, 0, 0, 0) == 3
    assert nm.sum_region(0, 0, 4, 4) == 58
    assert nm.sum_region(4, 4, 4, 4) == 5
    nm = NumMatrix([[7]])
    assert nm.sum_region(0, 0, 0, 0) == 7

    # Part 5
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    assert spiral_order([[1]]) == [1]
    assert spiral_order([[1, 2], [3, 4]]) == [1, 2, 4, 3]
    assert spiral_order([[1], [2], [3]]) == [1, 2, 3]
    assert spiral_order([[1, 2, 3]]) == [1, 2, 3]
    assert spiral_order([]) == []
    assert spiral_order([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]

    g = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]; rotate(g); assert g == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    g = [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]; rotate(g)
    assert g == [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]
    g = [[1]]; rotate(g); assert g == [[1]]
    g = [[1, 2], [3, 4]]; rotate(g); assert g == [[3, 1], [4, 2]]

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Part 1 -- why can't the Part-3-of-sliding-window trick (grow/shrink) work?
# A: With negative numbers the window sum is not monotonic in the window
#    size, so "shrink when too big" can skip answers. Prefix sums + hashmap
#    handle any sign.
# Q: Part 1 -- what if I asked for the number of subarrays divisible by k?
# A: Key the map on prefix % k (normalise negatives with Python's % or add k).
# Q: Part 2 -- why is division ruled out, and what breaks with zeros?
# A: One zero makes every other product 0 and the zero's own slot the product
#    of the rest; two zeros make everything 0. Division by zero needs cases;
#    the prefix/suffix approach needs none.
# Q: Part 3 -- why must row 0 and column 0 be zeroed last?
# A: They store the marks. Zeroing them first would mark every column/row as
#    zero and wipe the whole matrix.
# Q: Part 4 -- what if the matrix were mutable (point updates + range sums)?
# A: 2D Fenwick tree (BIT): O(log m log n) per update and per query.
# Q: Part 5 -- how would you rotate a non-square (m x n) matrix?
# A: Cannot be done in place (shape changes); build the n x m result with
#    out[j][m-1-i] = matrix[i][j].
