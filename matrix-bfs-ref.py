"""
GRID BFS / DFS -- reference solutions.  See matrix-bfs.py for the script.

Recurring pitfalls:
  * Bounds check BEFORE indexing: 0 <= nr < R and 0 <= nc < C.
  * BFS: mark visited when you ENQUEUE.  Marking on dequeue lets the same
    cell enter the queue many times (still correct, but O(8) blow-up and
    wrong if you count levels by queue size).
  * Level-by-level BFS: either store (r, c, dist) in the queue or process
    len(queue) items per level -- don't mix the two.
  * Multi-source BFS is just BFS with every source enqueued at distance 0.
  * DFS + memo needs no visited set only when the move rule guarantees
    acyclicity (strictly increasing path).  Otherwise you must track it.
"""
from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

INF = 2 ** 31 - 1
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIRS8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def build_grid(rows: List[str]) -> List[List[str]]:
    """["110", "001"] -> [["1","1","0"], ["0","0","1"]]"""
    return [list(row) for row in rows]


# ----------------------------------------------------------------- Part 1
def num_islands_dfs(grid: List[List[str]]) -> int:
    # Explicit stack; `seen` is set when a cell is PUSHED so it is pushed
    # at most once -> O(R*C) time and stack size.
    if not grid or not grid[0]:
        return 0
    R, C = len(grid), len(grid[0])
    seen = [[False] * C for _ in range(R)]
    count = 0
    for r in range(R):
        for c in range(C):
            if grid[r][c] != "1" or seen[r][c]:
                continue
            count += 1
            seen[r][c] = True
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                for dr, dc in DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == "1" and not seen[nr][nc]:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
    return count
    # If mutation is allowed, "sink" visited land (grid[r][c] = "0") and
    # drop `seen`.  Union-Find is the answer when islands appear over time.


def num_islands_bfs(grid: List[List[str]]) -> int:
    # Identical structure; a deque with popleft() instead of a stack.
    if not grid or not grid[0]:
        return 0
    R, C = len(grid), len(grid[0])
    seen = [[False] * C for _ in range(R)]
    count = 0
    for r in range(R):
        for c in range(C):
            if grid[r][c] != "1" or seen[r][c]:
                continue
            count += 1
            seen[r][c] = True
            q: Deque[Tuple[int, int]] = deque([(r, c)])
            while q:
                cr, cc = q.popleft()
                for dr, dc in DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == "1" and not seen[nr][nc]:
                        seen[nr][nc] = True
                        q.append((nr, nc))
    return count
    # BFS's frontier is O(perimeter); DFS's stack can be O(area) on a snake.
    # For counting components it does not matter; for shortest paths BFS is
    # the only correct choice.


# ----------------------------------------------------------------- Part 2
def oranges_rotting(grid: List[List[int]]) -> int:
    # Multi-source BFS: all rotten cells start in the queue at minute 0.
    # Track `fresh` so the answer is -1 if any remain.  Work on a copy.
    if not grid or not grid[0]:
        return 0
    R, C = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    q: Deque[Tuple[int, int]] = deque()
    fresh = 0
    for r in range(R):
        for c in range(C):
            if g[r][c] == 2:
                q.append((r, c))
            elif g[r][c] == 1:
                fresh += 1
    minutes = 0
    while q and fresh:
        for _ in range(len(q)):            # one level == one minute
            r, c = q.popleft()
            for dr, dc in DIRS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and g[nr][nc] == 1:
                    g[nr][nc] = 2
                    fresh -= 1
                    q.append((nr, nc))
        minutes += 1
    return minutes if fresh == 0 else -1
    # `while q and fresh` avoids counting a final minute in which nothing
    # rots.  O(R*C) time and space.


# ----------------------------------------------------------------- Part 3
def update_matrix(mat: List[List[int]]) -> List[List[int]]:
    # Seed from every 0 with dist 0; -1 marks "unvisited".  BFS layers give
    # exact Manhattan-through-cells distances.  O(R*C).
    R, C = len(mat), len(mat[0])
    dist = [[-1] * C for _ in range(R)]
    q: Deque[Tuple[int, int]] = deque()
    for r in range(R):
        for c in range(C):
            if mat[r][c] == 0:
                dist[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist
    # DP alternative: two sweeps (top-left then bottom-right) with
    # dist = min(dist, neighbour + 1); O(1) extra beyond the output.


# ----------------------------------------------------------------- Part 4
def shortest_path_binary_matrix(grid: List[List[int]]) -> int:
    # BFS with (r, c, length) in the queue; 8 directions.  Mark visited on
    # enqueue by writing into a copy (or a `seen` set).  O(R*C).
    n = len(grid)
    if n == 0 or grid[0][0] == 1 or grid[-1][-1] == 1:
        return -1
    if n == 1 and len(grid[0]) == 1:
        return 1
    R, C = n, len(grid[0])
    seen = [[False] * C for _ in range(R)]
    seen[0][0] = True
    q: Deque[Tuple[int, int, int]] = deque([(0, 0, 1)])
    while q:
        r, c, length = q.popleft()
        for dr, dc in DIRS8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 0 and not seen[nr][nc]:
                if nr == R - 1 and nc == C - 1:
                    return length + 1      # first time we SEE the target
                seen[nr][nc] = True
                q.append((nr, nc, length + 1))
    return -1
    # Follow-up: A* with Chebyshev distance max(|dr|, |dc|) as the
    # heuristic (admissible for 8-directional unit-cost moves).


# ----------------------------------------------------------------- Part 5
def walls_and_gates(rooms: List[List[int]]) -> None:
    # Multi-source BFS from all gates; the first time BFS reaches a room it
    # is via a shortest path, so only cells still == INF are updated.
    if not rooms or not rooms[0]:
        return
    R, C = len(rooms), len(rooms[0])
    q: Deque[Tuple[int, int]] = deque(
        (r, c) for r in range(R) for c in range(C) if rooms[r][c] == 0
    )
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and rooms[nr][nc] == INF:
                rooms[nr][nc] = rooms[r][c] + 1
                q.append((nr, nc))
    # The `== INF` test doubles as the visited check (walls are -1, gates 0).


# ----------------------------------------------------------------- Part 6
def largest_island(grid: List[List[int]]) -> int:
    # Pass 1: label components (id >= 1) and record sizes.
    # Pass 2: for each 0, sum sizes of DISTINCT neighbour ids, +1 for itself.
    # A grid with no 0 returns the biggest existing island.  O(R*C).
    R, C = len(grid), len(grid[0])
    comp = [[0] * C for _ in range(R)]
    sizes: Dict[int, int] = {0: 0}
    next_id = 1
    for r in range(R):
        for c in range(C):
            if grid[r][c] != 1 or comp[r][c]:
                continue
            cid = next_id
            next_id += 1
            comp[r][c] = cid
            stack = [(r, c)]
            size = 0
            while stack:
                cr, cc = stack.pop()
                size += 1
                for dr, dc in DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1 and not comp[nr][nc]:
                        comp[nr][nc] = cid
                        stack.append((nr, nc))
            sizes[cid] = size
    best = max(sizes.values())
    for r in range(R):
        for c in range(C):
            if grid[r][c] != 0:
                continue
            ids: Set[int] = set()
            for dr, dc in DIRS4:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and comp[nr][nc]:
                    ids.add(comp[nr][nc])
            best = max(best, 1 + sum(sizes[i] for i in ids))
    return best
    # Pitfall: the same island touching a 0 from two sides must be counted
    # once -- hence the set.  Naive "flip each 0 and re-flood" is O((RC)^2).


# ----------------------------------------------------------------- Part 7
def pacific_atlantic(heights: List[List[int]]) -> List[List[int]]:
    # Reverse the flow: from each ocean's border cells, BFS to neighbours of
    # height >= current.  The answer is the intersection.  O(R*C).
    if not heights or not heights[0]:
        return []
    R, C = len(heights), len(heights[0])

    def reach(sources: List[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        seen: Set[Tuple[int, int]] = set(sources)
        q: Deque[Tuple[int, int]] = deque(sources)
        while q:
            r, c = q.popleft()
            for dr, dc in DIRS4:
                nr, nc = r + dr, c + dc
                if (0 <= nr < R and 0 <= nc < C and (nr, nc) not in seen
                        and heights[nr][nc] >= heights[r][c]):
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return seen

    pacific = [(0, c) for c in range(C)] + [(r, 0) for r in range(1, R)]
    atlantic = [(R - 1, c) for c in range(C)] + [(r, C - 1) for r in range(R - 1)]
    both = reach(pacific) & reach(atlantic)
    return sorted([r, c] for r, c in both)
    # Forward simulation from every cell is O((RC)^2); reversing the flow
    # turns it into two multi-source searches.


# ----------------------------------------------------------------- Part 8
def exist(board: List[List[str]], word: str) -> bool:
    # Backtracking: mark the cell with a sentinel while exploring below it,
    # restore on return.  Prune: the board must contain enough of each letter.
    if word == "":
        return True
    if not board or not board[0]:
        return False
    R, C = len(board), len(board[0])
    from collections import Counter
    need = Counter(word)
    have = Counter(ch for row in board for ch in row)
    if any(have[ch] < n for ch, n in need.items()):
        return False
    # Search from the rarer end: fewer starting cells / earlier dead ends.
    if have[word[0]] > have[word[-1]]:
        word = word[::-1]
    L = len(word)

    def dfs(r: int, c: int, i: int) -> bool:
        if board[r][c] != word[i]:
            return False
        if i == L - 1:
            return True
        board[r][c] = "#"                 # visited marker (never a letter)
        found = False
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and dfs(nr, nc, i + 1):
                found = True
                break
        board[r][c] = word[i]             # restore
        return found

    return any(dfs(r, c, 0) for r in range(R) for c in range(C))
    # O(R*C*3^L) worst case (3 branches after the first step); recursion
    # depth = L, which is fine (L <= 15 in the LC constraints).


# ----------------------------------------------------------------- Part 9
def longest_increasing_path(matrix: List[List[int]]) -> int:
    # memo[r][c] = longest increasing path STARTING at (r, c).  Moves only go
    # to strictly larger values, so the move graph is a DAG: no cycles, no
    # visited set, and each cell is computed once -> O(R*C).
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    memo = [[0] * C for _ in range(R)]

    def dfs(r: int, c: int) -> int:
        if memo[r][c]:
            return memo[r][c]
        best = 1
        for dr, dc in DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and matrix[nr][nc] > matrix[r][c]:
                best = max(best, 1 + dfs(nr, nc))
        memo[r][c] = best
        return best

    return max(dfs(r, c) for r in range(R) for c in range(C))
    # Recursion depth can reach R*C on a spiral -- raise sys.setrecursionlimit
    # or use the topological alternative: compute indegree (number of smaller
    # neighbours), BFS-peel cells with indegree 0 level by level; the number
    # of levels is the answer.  Same O(R*C), no recursion.


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    g1 = build_grid(["11110", "11010", "11000", "00000"])
    g2 = build_grid(["11000", "11000", "00100", "00011"])
    g3 = build_grid(["10101", "01010", "10101"])
    for fn in (num_islands_dfs, num_islands_bfs):
        assert fn(g1) == 1, fn.__name__
        assert fn(g2) == 3, fn.__name__
        assert fn(g3) == 8, fn.__name__
        assert fn(build_grid(["0"])) == 0, fn.__name__
        assert fn(build_grid(["1"])) == 1, fn.__name__
        assert fn([]) == 0, fn.__name__
        assert fn(build_grid(["1111"])) == 1, fn.__name__
    assert g2 == build_grid(["11000", "11000", "00100", "00011"])   # not mutated
    big = build_grid(["1" * 300] * 300)          # a 90k-cell island: recursion would die
    assert num_islands_dfs(big) == 1 and num_islands_bfs(big) == 1

    # Part 2
    o1 = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
    assert oranges_rotting(o1) == 4
    assert o1 == [[2, 1, 1], [1, 1, 0], [0, 1, 1]]   # not mutated
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert oranges_rotting([[0, 2]]) == 0
    assert oranges_rotting([[0]]) == 0
    assert oranges_rotting([[1]]) == -1
    assert oranges_rotting([[2, 2], [1, 1], [0, 0], [2, 0]]) == 1
    assert oranges_rotting([[2], [1], [1], [1]]) == 3

    # Part 3
    assert update_matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    assert update_matrix([[0, 0, 0], [0, 1, 0], [1, 1, 1]]) == [[0, 0, 0], [0, 1, 0], [1, 2, 1]]
    assert update_matrix([[0]]) == [[0]]
    assert update_matrix([[1, 1, 1, 0]]) == [[3, 2, 1, 0]]
    assert update_matrix([[1, 0, 1, 1, 0, 0, 1, 0, 0, 1], [0, 1, 1, 0, 1, 0, 1, 0, 1, 1]])[0] == [1, 0, 1, 1, 0, 0, 1, 0, 0, 1]

    # Part 4
    assert shortest_path_binary_matrix([[0, 1], [1, 0]]) == 2
    assert shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 0]]) == 4
    assert shortest_path_binary_matrix([[1, 0, 0], [1, 1, 0], [1, 1, 0]]) == -1
    assert shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 1]]) == -1   # end blocked
    assert shortest_path_binary_matrix([[0]]) == 1
    assert shortest_path_binary_matrix([[1]]) == -1
    assert shortest_path_binary_matrix([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) == 4
    assert shortest_path_binary_matrix([[0, 1, 1, 0, 0, 0], [0, 1, 0, 1, 1, 0], [0, 1, 1, 0, 1, 0],
                                        [0, 0, 0, 1, 1, 0], [1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 1, 0]]) == 14

    # Part 5
    rooms = [[INF, -1, 0, INF], [INF, INF, INF, -1], [INF, -1, INF, -1], [0, -1, INF, INF]]
    assert walls_and_gates(rooms) is None
    assert rooms == [[3, -1, 0, 1], [2, 2, 1, -1], [1, -1, 2, -1], [0, -1, 3, 4]]
    rooms = [[INF, -1], [-1, INF]]
    walls_and_gates(rooms)
    assert rooms == [[INF, -1], [-1, INF]]            # unreachable stays INF
    rooms = [[0]]
    walls_and_gates(rooms)
    assert rooms == [[0]]
    rooms = []
    walls_and_gates(rooms)
    assert rooms == []

    # Part 6
    assert largest_island([[1, 0], [0, 1]]) == 3
    assert largest_island([[1, 1], [1, 0]]) == 4
    assert largest_island([[1, 1], [1, 1]]) == 4
    assert largest_island([[0, 0], [0, 0]]) == 1
    assert largest_island([[1, 0, 1], [0, 0, 0], [1, 0, 1]]) == 3   # distinct ids, not double-counted
    assert largest_island([[1, 1, 0, 1, 1], [1, 1, 0, 1, 1], [0, 0, 0, 0, 0], [1, 1, 0, 1, 1], [1, 1, 0, 1, 1]]) == 9
    assert largest_island([[1, 0, 1], [1, 0, 1]]) == 5   # (0,1) or (1,1) joins both columns
    assert largest_island([[0, 1, 0], [1, 1, 1], [0, 1, 0]]) == 6

    # Part 7
    heights = [[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]
    assert pacific_atlantic(heights) == [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]
    assert pacific_atlantic([[1]]) == [[0, 0]]
    assert pacific_atlantic([[1, 1], [1, 1]]) == [[0, 0], [0, 1], [1, 0], [1, 1]]
    assert pacific_atlantic([[1, 2, 3], [8, 9, 4], [7, 6, 5]]) == [[0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
    assert pacific_atlantic([[3, 3, 3], [3, 0, 3], [3, 3, 3]])[:3] == [[0, 0], [0, 1], [0, 2]]

    # Part 8
    board = build_grid(["ABCE", "SFCS", "ADEE"])
    assert exist(board, "ABCCED") is True
    assert exist(board, "SEE") is True
    assert exist(board, "ABCB") is False
    assert exist(board, "ABCESEEEFS") is True         # winds through most of the board
    assert exist(board, "ABCESEEEFSX") is False
    assert exist(board, "A") is True
    assert exist(board, "Z") is False
    assert exist(board, "") is True
    assert board == build_grid(["ABCE", "SFCS", "ADEE"])   # markers restored
    assert exist(build_grid(["a"]), "a") is True
    assert exist(build_grid(["ab"]), "ba") is True
    assert exist(build_grid(["aa"]), "aaa") is False   # no reuse of a cell

    # Part 9
    assert longest_increasing_path([[9, 9, 4], [6, 6, 8], [2, 1, 1]]) == 4
    assert longest_increasing_path([[3, 4, 5], [3, 2, 6], [2, 2, 1]]) == 4
    assert longest_increasing_path([[1]]) == 1
    assert longest_increasing_path([[7, 7, 7], [7, 7, 7]]) == 1
    assert longest_increasing_path([[1, 2, 3, 4, 5]]) == 5
    assert longest_increasing_path([[1, 2], [4, 3]]) == 4
    assert longest_increasing_path([]) == 0

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: When is DFS wrong and BFS the only choice on a grid?
# A: Any shortest-path / minimum-steps question with unit edge costs (rotting
#    oranges, 01-matrix, LC1091).  DFS finds A path, not the shortest one.
# Q: Why is multi-source BFS correct -- doesn't a cell need the nearest source?
# A: All sources start at distance 0 in the same queue, so the BFS wavefront
#    expands from every source simultaneously; the first wave to touch a cell
#    is from its nearest source.  Equivalent to adding a virtual super-source.
# Q: Islands on a 10^4 x 10^4 grid that does not fit in memory?
# A: Stream it row by row with Union-Find over the previous row's component
#    ids (connected-component labelling), or tile it and merge borders.
# Q: LC827 -- why can't you just try flipping every 0 and re-flood?
# A: That is O(R*C) work per 0 -> O((R*C)^2).  Labelling once and summing
#    distinct neighbour sizes is O(R*C).
# Q: Longest increasing path: why does DFS + memo need no visited set, and
#    what breaks if the path were non-decreasing (>=) instead?
# A: Strict increase means you can never return to a cell (DAG).  With >=,
#    equal neighbours form cycles: you would need a visited set and the
#    problem changes to components of equal cells collapsed into one node.
