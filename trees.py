"""
BINARY TREES -- interviewer script (45-60 min; pick 3-4 parts, escalate)

Setup: "Our product-category taxonomy is a binary tree. Node has `val`,
`left`, `right`. I'll build trees for you from a level-order list where
None marks a missing child, e.g. [3,9,20,None,None,15,7]."

------------------------------------------------------------------------------
Part 1  Traversals by level.
        a) level_order  -> [[3],[9,20],[15,7]]
        b) zigzag_level_order -> [[3],[20,9],[15,7]]  (alternate direction)
        c) right_side_view -> [3,20,7]  (last node of each level)
        Target: O(n) time, O(w) space (w = max width).

Part 2  Build a tree from preorder + inorder (LC105). Values are unique.
        preorder=[3,9,20,15,7], inorder=[9,3,15,20,7] -> the tree above.
        Target O(n) with a hashmap of inorder indices. Follow-up: what is the
        recursion depth for a degenerate (chain) tree of 1e4 nodes, and what
        would you do about it?

Part 3  Maximum width of a binary tree (LC662): width of a level counts
        the null slots between the leftmost and rightmost non-null nodes.
        [1,3,2,5,3,None,9] -> 4  (level 3 is 5,3,null,9)
        Hint: heap-style indices (2i, 2i+1). Normalise indices per level so
        they don't grow unbounded in a fixed-width language.

Part 4  Path sum II (LC113): all root-to-leaf paths that sum to target.
        [5,4,8,11,None,13,4,7,2,None,None,5,1], target=22
          -> [[5,4,11,2],[5,8,4,5]]
        Then path sum III (LC437): count downward paths (any start, any end,
        parent->child direction) that sum to target. O(n) with a prefix-sum
        hashmap on the current root path.
        [10,5,-3,3,2,None,11,3,-2,None,1], target=8 -> 3

Part 5  Lowest common ancestor (LC236) of two nodes in a binary tree.
        Then the BST variant (LC235) in O(h) without recursion.

Part 6  Serialize / deserialize (LC297). Preorder with a '#' sentinel and
        comma separators. Round-trip must be exact.

Part 7  Validate BST (LC98). Strict: left subtree < node < right subtree.
        [5,1,4,None,None,3,6] -> False.  Watch: duplicates are invalid, and
        checking only immediate children is the classic wrong answer.

Part 8  Kth smallest in a BST (LC230), iterative inorder, O(h + k).

Part 9  Diameter of a binary tree (LC543): longest path between any two
        nodes, in edges. [1,2,3,4,5] -> 3.

Part 10 All nodes at distance K from a target node (LC863).
        [3,5,1,6,2,0,8,None,None,7,4], target=5, k=2 -> {7,4,1}.
        Build a parent map, then BFS with a visited set.

Part 11 Inorder traversal: iterative with an explicit stack, then Morris
        traversal with O(1) extra space (threaded tree; restore links).

Part 12 Flatten binary tree to a linked list (LC114) in preorder, in place,
        using `right` pointers and left = None.  [1,2,5,3,4,None,6]
          -> 1->2->3->4->5->6
------------------------------------------------------------------------------
"""
from __future__ import annotations

from collections import deque
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
    """LeetCode-style level order with None for missing children."""
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
    """Inverse of build_tree (trailing Nones stripped)."""
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
    pass


def zigzag_level_order(root: Optional[TreeNode]) -> List[List[int]]:
    pass


def right_side_view(root: Optional[TreeNode]) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 2
def build_from_pre_in(preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
    pass


# ----------------------------------------------------------------- Part 3
def width_of_binary_tree(root: Optional[TreeNode]) -> int:
    pass


# ----------------------------------------------------------------- Part 4
def path_sum_ii(root: Optional[TreeNode], target: int) -> List[List[int]]:
    pass


def path_sum_iii(root: Optional[TreeNode], target: int) -> int:
    pass


# ----------------------------------------------------------------- Part 5
def lowest_common_ancestor(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    pass


def lca_bst(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    pass


# ----------------------------------------------------------------- Part 6
def serialize(root: Optional[TreeNode]) -> str:
    pass


def deserialize(data: str) -> Optional[TreeNode]:
    pass


# ----------------------------------------------------------------- Part 7
def is_valid_bst(root: Optional[TreeNode]) -> bool:
    pass


# ----------------------------------------------------------------- Part 8
def kth_smallest(root: Optional[TreeNode], k: int) -> int:
    pass


# ----------------------------------------------------------------- Part 9
def diameter(root: Optional[TreeNode]) -> int:
    pass


# ----------------------------------------------------------------- Part 10
def distance_k(root: Optional[TreeNode], target: TreeNode, k: int) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 11
def inorder_iterative(root: Optional[TreeNode]) -> List[int]:
    pass


def inorder_morris(root: Optional[TreeNode]) -> List[int]:
    pass


# ----------------------------------------------------------------- Part 12
def flatten(root: Optional[TreeNode]) -> None:
    """In place: preorder as a right-skewed list; every left must be None."""
    pass


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    t = build_tree([3, 9, 20, None, None, 15, 7])

    # Part 1
    assert level_order(t) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    assert zigzag_level_order(t) == [[3], [20, 9], [15, 7]]
    assert zigzag_level_order(build_tree([1, 2, 3, 4, None, None, 5])) == [[1], [3, 2], [4, 5]]
    assert right_side_view(t) == [3, 20, 7]
    assert right_side_view(build_tree([1, 2, 3, 4])) == [1, 3, 4]   # left child shows through
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
    assert path_sum_ii(build_tree([1, 2]), 1) == []       # 1 is not a leaf
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
    assert is_valid_bst(build_tree([5, 4, 6, None, None, 3, 7])) is False   # 3 < 5 in right subtree
    assert is_valid_bst(build_tree([2, 2, 2])) is False                    # duplicates
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
    assert diameter(build_tree([1, 2, None, 3, 4, 5, None, None, None, 6])) == 4  # path doesn't go through root
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
    assert tree_to_list(bst) == [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5]   # Morris restored the tree
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
