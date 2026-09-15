"""
BINARY TREES -- reference solutions. See trees.py for the problem script.

Recurring pitfalls:
  * Recursion depth: a chain of 1e4 nodes exceeds Python's default limit.
    Every recursive solution here has an iterative counterpart worth knowing
    (explicit stack / BFS with a parent map).
  * Empty tree: `root is None` must be the very first check.
  * Mutating shared state during DFS (path lists): copy on record, pop on
    return (backtracking).
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional, Set


class TreeNode:
    def __init__(self, val: int = 0, left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"TreeNode({self.val})"


# ----------------------------------------------------------------- helpers
def build_tree(vals: List[Optional[int]]) -> Optional[TreeNode]:
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    q: Deque[TreeNode] = deque([root])
    i = 1
    while q and i < len(vals):
        node = q.popleft()
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i])
            q.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i])
            q.append(node.right)
        i += 1
    return root


def tree_to_list(root: Optional[TreeNode]) -> List[Optional[int]]:
    out: List[Optional[int]] = []
    q: Deque[Optional[TreeNode]] = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append(node.val)
            q.append(node.left)
            q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def find(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    if root is None:
        return None
    if root.val == val:
        return root
    return find(root.left, val) or find(root.right, val)


# ----------------------------------------------------------------- Part 1
def level_order(root: Optional[TreeNode]) -> List[List[int]]:
    # BFS, one level per outer iteration (snapshot len(q)).  O(n)/O(w).
    if root is None:
        return []
    out: List[List[int]] = []
    q: Deque[TreeNode] = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
        out.append(level)
    return out


def zigzag_level_order(root: Optional[TreeNode]) -> List[List[int]]:
    # Same BFS; reverse every other level on output.  Cheaper than a deque
    # of alternating directions and just as fast asymptotically.
    levels = level_order(root)
    return [lvl if i % 2 == 0 else lvl[::-1] for i, lvl in enumerate(levels)]


def right_side_view(root: Optional[TreeNode]) -> List[int]:
    # Last element of each BFS level.  NOT "follow right pointers":
    # a deep left subtree shows through when the right one is shorter.
    return [lvl[-1] for lvl in level_order(root)]


# ----------------------------------------------------------------- Part 2
def build_from_pre_in(preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
    # preorder[0] is the root; its index in inorder splits left/right.
    # Hashmap of inorder indices makes each split O(1) -> total O(n).
    # A shared preorder cursor avoids slicing (which would be O(n^2)).
    idx = {v: i for i, v in enumerate(inorder)}
    pre_i = 0

    def build(lo: int, hi: int) -> Optional[TreeNode]:   # inorder[lo:hi]
        nonlocal pre_i
        if lo >= hi:
            return None
        val = preorder[pre_i]
        pre_i += 1
        node = TreeNode(val)
        mid = idx[val]
        node.left = build(lo, mid)      # left first: matches preorder cursor
        node.right = build(mid + 1, hi)
        return node

    return build(0, len(inorder))
    # Recursion depth = tree height; a chain of 1e4 nodes will blow the
    # default limit.  Fix: sys.setrecursionlimit (risky) or the iterative
    # stack version (push nodes while preorder advances; pop when the top's
    # val equals inorder[i], then attach to the right).


# ----------------------------------------------------------------- Part 3
def width_of_binary_tree(root: Optional[TreeNode]) -> int:
    # Assign heap indices: left = 2i, right = 2i+1.  Width of a level =
    # last_index - first_index + 1.  Subtract the level's first index when
    # enqueueing children so indices stay small (matters in Java/C++ for
    # 64-bit overflow; free in Python but say it anyway).
    if root is None:
        return 0
    best = 0
    q: Deque[tuple] = deque([(root, 0)])
    while q:
        n = len(q)
        first = q[0][1]
        last = first
        for _ in range(n):
            node, i = q.popleft()
            i -= first            # normalise
            last = i
            if node.left is not None:
                q.append((node.left, 2 * i))
            if node.right is not None:
                q.append((node.right, 2 * i + 1))
        best = max(best, last + 1)
    return best   # O(n) time, O(w) space


# ----------------------------------------------------------------- Part 4
def path_sum_ii(root: Optional[TreeNode], target: int) -> List[List[int]]:
    # DFS with backtracking.  Record only at LEAVES (both children None).
    out: List[List[int]] = []
    path: List[int] = []

    def dfs(node: Optional[TreeNode], remaining: int) -> None:
        if node is None:
            return
        path.append(node.val)
        remaining -= node.val
        if node.left is None and node.right is None and remaining == 0:
            out.append(path[:])     # copy! path is mutated afterwards
        else:
            dfs(node.left, remaining)
            dfs(node.right, remaining)
        path.pop()

    dfs(root, target)
    return out   # O(n * h) worst case for the copies


def path_sum_iii(root: Optional[TreeNode], target: int) -> int:
    # Prefix sums along the root->node path, like subarray-sum-equals-k.
    # count[s] = how many ancestors (incl. root path) have prefix sum s.
    # A downward path ending at `node` with sum `target` exists for each
    # ancestor prefix equal to cur - target.  Remove on the way back up so
    # sibling subtrees don't see each other's prefixes.
    count: Dict[int, int] = defaultdict(int)
    count[0] = 1

    def dfs(node: Optional[TreeNode], cur: int) -> int:
        if node is None:
            return 0
        cur += node.val
        res = count[cur - target]
        count[cur] += 1
        res += dfs(node.left, cur) + dfs(node.right, cur)
        count[cur] -= 1     # backtrack
        return res

    return dfs(root, 0)   # O(n) time, O(h) space.  Naive is O(n^2).


# ----------------------------------------------------------------- Part 5
def lowest_common_ancestor(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    # Post-order: return p/q if found in this subtree, else whichever side
    # found something.  If both sides return non-None, this node is the LCA.
    # Relies on p and q both existing in the tree.
    if root is None or root is p or root is q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left is not None and right is not None:
        return root
    return left if left is not None else right   # O(n) time, O(h) stack


def lca_bst(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    # Walk down: the LCA is the first node whose value lies between p and q
    # (inclusive).  O(h) time, O(1) space.
    lo, hi = min(p.val, q.val), max(p.val, q.val)
    cur = root
    while cur is not None:
        if cur.val > hi:
            cur = cur.left
        elif cur.val < lo:
            cur = cur.right
        else:
            return cur
    return None


# ----------------------------------------------------------------- Part 6
def serialize(root: Optional[TreeNode]) -> str:
    # Preorder with '#' for null.  Preorder + null markers uniquely
    # determines the tree (no inorder needed).  Iterative to avoid depth.
    out: List[str] = []
    stack: List[Optional[TreeNode]] = [root]
    while stack:
        node = stack.pop()
        if node is None:
            out.append("#")
        else:
            out.append(str(node.val))
            stack.append(node.right)   # right first so left pops first
            stack.append(node.left)
    return ",".join(out)


def deserialize(data: str) -> Optional[TreeNode]:
    tokens = iter(data.split(","))

    def build() -> Optional[TreeNode]:
        tok = next(tokens)
        if tok == "#":
            return None
        node = TreeNode(int(tok))
        node.left = build()
        node.right = build()
        return node

    return build()   # O(n) both ways


# ----------------------------------------------------------------- Part 7
def is_valid_bst(root: Optional[TreeNode]) -> bool:
    # Carry an open interval (lo, hi) down the tree.  Strict inequalities
    # reject duplicates (LeetCode's definition).  Iterative to avoid depth.
    # Alternative: inorder traversal must be strictly increasing.
    stack: List[tuple] = [(root, float("-inf"), float("inf"))]
    while stack:
        node, lo, hi = stack.pop()
        if node is None:
            continue
        if not (lo < node.val < hi):
            return False
        stack.append((node.left, lo, node.val))
        stack.append((node.right, node.val, hi))
    return True   # O(n) time, O(h) space


# ----------------------------------------------------------------- Part 8
def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    # Iterative inorder; stop after k pops.  O(h + k) time, O(h) space.
    stack: List[TreeNode] = []
    cur = root
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        cur = cur.right
    raise ValueError("k out of range")
    # Follow-up for frequent queries: store subtree sizes in each node -> O(h).


# ----------------------------------------------------------------- Part 9
def diameter(root: Optional[TreeNode]) -> int:
    # Post-order: height(node) = 1 + max(hl, hr); the best path THROUGH node
    # has hl + hr edges.  Track the global max as a side effect.
    best = 0

    def height(node: Optional[TreeNode]) -> int:
        nonlocal best
        if node is None:
            return 0
        hl = height(node.left)
        hr = height(node.right)
        best = max(best, hl + hr)
        return 1 + max(hl, hr)

    height(root)
    return best   # O(n) time, O(h) stack


# ----------------------------------------------------------------- Part 10
def distance_k(root: Optional[TreeNode], target: TreeNode, k: int) -> List[int]:
    # Turn the tree into an undirected graph via a parent map, then BFS k
    # layers from target with a visited set (to not bounce back up).
    parent: Dict[TreeNode, Optional[TreeNode]] = {}
    stack: List[TreeNode] = [root] if root is not None else []
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child is not None:
                parent[child] = node
                stack.append(child)
    q: Deque[TreeNode] = deque([target])
    seen: Set[TreeNode] = {target}
    dist = 0
    while q and dist < k:
        for _ in range(len(q)):
            node = q.popleft()
            for nb in (node.left, node.right, parent.get(node)):
                if nb is not None and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        dist += 1
    return [n.val for n in q] if dist == k else []   # O(n) time and space


# ----------------------------------------------------------------- Part 11
def inorder_iterative(root: Optional[TreeNode]) -> List[int]:
    # Push the whole left spine, pop, visit, then go right.
    out: List[int] = []
    stack: List[TreeNode] = []
    cur = root
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        out.append(cur.val)
        cur = cur.right
    return out   # O(n) time, O(h) space


def inorder_morris(root: Optional[TreeNode]) -> List[int]:
    # Morris: for a node with a left child, find its inorder predecessor
    # (rightmost node of the left subtree).  If pred.right is None, thread
    # pred.right = cur and go left.  If pred.right is cur, we've come back:
    # unthread, visit cur, go right.  Every edge is walked at most twice
    # -> O(n) time, O(1) extra space; the tree is restored on exit.
    out: List[int] = []
    cur = root
    while cur is not None:
        if cur.left is None:
            out.append(cur.val)
            cur = cur.right
        else:
            pred = cur.left
            while pred.right is not None and pred.right is not cur:
                pred = pred.right
            if pred.right is None:
                pred.right = cur      # thread
                cur = cur.left
            else:
                pred.right = None     # restore
                out.append(cur.val)
                cur = cur.right
    return out


# ----------------------------------------------------------------- Part 12
def flatten(root: Optional[TreeNode]) -> None:
    # Morris-like O(1) space: for each node with a left subtree, hang the
    # right subtree off the rightmost node of the left subtree, then move
    # left subtree to the right.  Preorder is preserved.
    cur = root
    while cur is not None:
        if cur.left is not None:
            pred = cur.left
            while pred.right is not None:
                pred = pred.right
            pred.right = cur.right
            cur.right = cur.left
            cur.left = None
        cur = cur.right
    # O(n) time (each node visited as `pred` at most once), O(1) space.
    # Recursive alternative: flatten right, flatten left, then prev-pointer
    # trick in reverse preorder.


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    t = build_tree([3, 9, 20, None, None, 15, 7])

    # Part 1
    assert level_order(t) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    assert zigzag_level_order(t) == [[3], [20, 9], [15, 7]]
    assert zigzag_level_order(build_tree([1, 2, 3, 4, None, None, 5])) == [[1], [3, 2], [4, 5]]
    assert right_side_view(t) == [3, 20, 7]
    assert right_side_view(build_tree([1, 2, 3, 4])) == [1, 3, 4]
    assert right_side_view(None) == []

    # Part 2
    assert tree_to_list(build_from_pre_in([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])) == [3, 9, 20, None, None, 15, 7]
    assert build_from_pre_in([], []) is None
    assert tree_to_list(build_from_pre_in([1, 2], [2, 1])) == [1, 2]
    assert tree_to_list(build_from_pre_in([1, 2], [1, 2])) == [1, None, 2]

    # Part 3
    assert width_of_binary_tree(build_tree([1, 3, 2, 5, 3, None, 9])) == 4
    assert width_of_binary_tree(build_tree([1, 3, 2, 5, None, None, 9, 6, None, 7])) == 7
    assert width_of_binary_tree(build_tree([1, 3, 2, 5])) == 2
    assert width_of_binary_tree(build_tree([1])) == 1
    assert width_of_binary_tree(None) == 0

    # Part 4
    ps = path_sum_ii(build_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1]), 22)
    assert sorted(ps) == [[5, 4, 11, 2], [5, 8, 4, 5]]
    assert path_sum_ii(build_tree([1, 2]), 1) == []
    assert path_sum_ii(None, 0) == []
    assert path_sum_iii(build_tree([10, 5, -3, 3, 2, None, 11, 3, -2, None, 1]), 8) == 3
    assert path_sum_iii(build_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1]), 22) == 3
    assert path_sum_iii(build_tree([1, -2, -3, 1, 3, -2, None, -1]), -1) == 4
    assert path_sum_iii(None, 0) == 0

    # Part 5
    t5 = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    assert lowest_common_ancestor(t5, find(t5, 5), find(t5, 1)).val == 3
    assert lowest_common_ancestor(t5, find(t5, 5), find(t5, 4)).val == 5
    assert lowest_common_ancestor(t5, find(t5, 7), find(t5, 4)).val == 2
    bst = build_tree([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5])
    assert lca_bst(bst, find(bst, 2), find(bst, 8)).val == 6
    assert lca_bst(bst, find(bst, 2), find(bst, 4)).val == 2
    assert lca_bst(bst, find(bst, 3), find(bst, 5)).val == 4

    # Part 6
    for vals in ([1, 2, 3, None, None, 4, 5], [], [1], [1, None, 2, None, 3], [-1, 0, 10]):
        assert tree_to_list(deserialize(serialize(build_tree(vals)))) == tree_to_list(build_tree(vals))

    # Part 7
    assert is_valid_bst(build_tree([2, 1, 3])) is True
    assert is_valid_bst(build_tree([5, 1, 4, None, None, 3, 6])) is False
    assert is_valid_bst(build_tree([5, 4, 6, None, None, 3, 7])) is False
    assert is_valid_bst(build_tree([2, 2, 2])) is False
    assert is_valid_bst(build_tree([1])) is True
    assert is_valid_bst(None) is True

    # Part 8
    assert kth_smallest(build_tree([3, 1, 4, None, 2]), 1) == 1
    assert kth_smallest(build_tree([5, 3, 6, 2, 4, None, None, 1]), 3) == 3
    assert kth_smallest(build_tree([5, 3, 6, 2, 4, None, None, 1]), 6) == 6

    # Part 9
    assert diameter(build_tree([1, 2, 3, 4, 5])) == 3
    assert diameter(build_tree([1, 2])) == 1
    assert diameter(build_tree([1])) == 0
    assert diameter(build_tree([1, 2, None, 3, 4, 5, None, None, None, 6])) == 4
    assert diameter(None) == 0

    # Part 10
    t10 = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    assert sorted(distance_k(t10, find(t10, 5), 2)) == [1, 4, 7]
    assert sorted(distance_k(t10, find(t10, 5), 0)) == [5]
    assert sorted(distance_k(t10, find(t10, 5), 3)) == [0, 8]
    assert distance_k(t10, find(t10, 5), 10) == []

    # Part 11
    t11 = build_tree([1, None, 2, 3])
    assert inorder_iterative(t11) == [1, 3, 2]
    assert inorder_iterative(bst) == [0, 2, 3, 4, 5, 6, 7, 8, 9]
    assert inorder_iterative(None) == []
    assert inorder_morris(t11) == [1, 3, 2]
    assert inorder_morris(bst) == [0, 2, 3, 4, 5, 6, 7, 8, 9]
    assert tree_to_list(bst) == [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5]
    assert inorder_morris(None) == []

    # Part 12
    t12 = build_tree([1, 2, 5, 3, 4, None, 6])
    flatten(t12)
    out = []
    cur = t12
    while cur is not None:
        assert cur.left is None
        out.append(cur.val)
        cur = cur.right
    assert out == [1, 2, 3, 4, 5, 6]
    flatten(None)
    t12b = build_tree([0]); flatten(t12b); assert t12b.left is None and t12b.right is None

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Build-from-preorder/inorder on a 1e5-node chain -- what happens in Python?
# A: RecursionError (depth = height). Use the explicit-stack iterative build, or
#    accept sys.setrecursionlimit for a known-bounded input (mention the C-stack risk).
# Q: Why is checking node.left.val < node.val < node.right.val not enough for BST?
# A: A node deep in the left subtree can still exceed an ancestor; bounds must be
#    inherited from all ancestors (the (lo, hi) interval), not just the parent.
# Q: Path sum III -- why decrement the prefix count on the way back up?
# A: The hashmap must only contain prefixes on the CURRENT root path; otherwise a
#    node in a sibling subtree would be counted as a valid start point.
# Q: Max width: why normalise the index at each level?
# A: Indices double per level; at depth 60+ they overflow 64-bit in Java/C++. Only
#    the differences within a level matter, so subtract the level's first index.
# Q: Morris traversal -- what's the catch?
# A: It temporarily mutates the tree (threads), so it is not safe under concurrent
#    readers, and the constant factor is higher (each edge walked up to twice).
