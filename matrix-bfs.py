"""
GRID BFS / DFS -- interviewer script (45-60 min; 2-3 parts typical, the rest
                  are what the interviewer reaches for if you finish early)

Setup: "Warehouse floor plans, delivery-zone maps and image masks all end up
as 2-D grids.  Show me you can move around a grid without off-by-one errors,
and that you know when to use DFS, BFS, multi-source BFS and memoised DFS."

Conventions: grid[r][c]; R = len(grid), C = len(grid[0]); 4-directional
unless the part says 8.  build_grid(["110", "001"]) gives a list of lists of
single-char strings.  Python's recursion limit (1000) is a real problem on a
1000x1000 grid -- prefer an explicit stack, or say why recursion is fine.

------------------------------------------------------------------------------
Part 1  Number of islands (LC200): '1' land, '0' water, 4-directional.
        Once with an explicit-stack DFS, once with BFS.  O(R*C) time,
        O(R*C) worst-case extra.  Do NOT mutate the input (assume the caller
        still needs it) -- use a visited structure.
        ["11000","11000","00100","00011"] -> 3

Part 2  Rotting oranges (LC994): 0 empty, 1 fresh, 2 rotten; each minute
        every rotten orange rots its 4 neighbours.  Minutes until no fresh
        orange remains, or -1.  Multi-source BFS: seed the queue with ALL
        rotten cells at t=0.  Do not mutate the input.
        [[2,1,1],[1,1,0],[0,1,1]] -> 4 ; [[2,1,1],[0,1,1],[1,0,1]] -> -1 ;
        [[0,2]] -> 0

Part 3  01-matrix (LC542): for each cell, distance to the nearest 0.
        Seed the BFS from every 0.  Why not BFS from every 1?  (O((RC)^2).)
        [[0,0,0],[0,1,0],[1,1,1]] -> [[0,0,0],[0,1,0],[1,2,1]]

Part 4  Shortest path in a binary matrix (LC1091): 8-directional, 0 = open,
        from (0,0) to (R-1,C-1); length counts CELLS; -1 if none.
        [[0,1],[1,0]] -> 2 ; [[0,0,0],[1,1,0],[1,1,0]] -> 4 ;
        [[1,0,0],[1,1,0],[1,1,0]] -> -1 ; [[0]] -> 1
        (Asked at a TikTok intern round.)  Pitfalls: check the start AND
        end cells; mark visited on ENQUEUE, not on dequeue.

Part 5  Walls and gates (LC286): INF = 2**31-1 empty room, -1 wall, 0 gate.
        Fill each room IN PLACE with the distance to its nearest gate
        (unreachable rooms stay INF).  Returns None.

Part 6  Making a large island (LC827): grid of 0/1; flip at most one 0 to 1;
        return the largest island size.
        [[1,0],[0,1]] -> 3 ; [[1,1],[1,0]] -> 4 ; [[1,1],[1,1]] -> 4
        Target O(R*C): label each component with an id and size first, then
        for each 0 sum the sizes of the DISTINCT neighbouring ids + 1.

Part 7  Pacific Atlantic water flow (LC417): water flows from a cell to a
        4-neighbour of height <= its own.  Pacific touches the top and left
        edges, Atlantic the bottom and right.  Return the SORTED list of
        [r, c] that can reach both.  Idea: reverse the flow -- search from
        each ocean's border "uphill" (neighbour height >= current).

Part 8  Word search (LC79): can `word` be traced through 4-adjacent cells,
        each cell used at most once?  Backtracking with an in-place marker
        that you restore.  Prune before searching (letter counts).
        Board ABCE/SFCS/ADEE: "ABCCED" -> True, "SEE" -> True, "ABCB" -> False

Part 9  Longest strictly increasing path (LC329): DFS + memo.  Why is no
        visited set needed?  (Strictly increasing -> no cycles possible.)
        [[9,9,4],[6,6,8],[2,1,1]] -> 4 ; [[3,4,5],[3,2,6],[2,2,1]] -> 4
        Alternative to mention: topological "peeling" from cells with
        indegree 0 (no smaller neighbour) -- no recursion at all.
------------------------------------------------------------------------------
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
    pass


def num_islands_bfs(grid: List[List[str]]) -> int:
    pass


# ----------------------------------------------------------------- Part 2
def oranges_rotting(grid: List[List[int]]) -> int:
    pass


# ----------------------------------------------------------------- Part 3
def update_matrix(mat: List[List[int]]) -> List[List[int]]:
    pass


# ----------------------------------------------------------------- Part 4
def shortest_path_binary_matrix(grid: List[List[int]]) -> int:
    pass


# ----------------------------------------------------------------- Part 5
def walls_and_gates(rooms: List[List[int]]) -> None:
    pass


# ----------------------------------------------------------------- Part 6
def largest_island(grid: List[List[int]]) -> int:
    pass


# ----------------------------------------------------------------- Part 7
def pacific_atlantic(heights: List[List[int]]) -> List[List[int]]:
    pass


# ----------------------------------------------------------------- Part 8
def exist(board: List[List[str]], word: str) -> bool:
    pass


# ----------------------------------------------------------------- Part 9
def longest_increasing_path(matrix: List[List[int]]) -> int:
    pass


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
