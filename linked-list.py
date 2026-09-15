"""
LINKED LISTS -- interviewer script (45-60 min, escalate as far as time allows)

Setup: "We store a customer's browsing history / cart as a singly linked list.
Each node has `val` and `next`. I'll give you a few operations to implement,
no external libraries. Talk through the invariants as you go."

------------------------------------------------------------------------------
Part 1  Reverse a singly linked list.
        Do it iteratively first, then recursively. Discuss the recursion depth
        problem for n ~ 1e5 in Python (default limit ~1000).
        Example: 1->2->3->4  =>  4->3->2->1
        Target: O(n) time, O(1) space iterative / O(n) stack recursive.

Part 2  Reverse nodes in k-group (LC25).
        Reverse every k consecutive nodes; a trailing group shorter than k
        is left untouched. O(1) extra space.
        Example: 1->2->3->4->5, k=2  =>  2->1->4->3->5
                 1->2->3->4->5, k=3  =>  3->2->1->4->5

Part 3  Reorder list (LC143).
        L0->L1->...->Ln  becomes  L0->Ln->L1->Ln-1->L2->Ln-2->...
        Must be in place, O(1) extra space.
        Example: 1->2->3->4->5  =>  1->5->2->4->3
        Hint if stuck: find the middle, reverse the second half, merge.

Part 4  Linked-list cycle II (LC142).
        Return the node where the cycle begins, or None. O(1) space
        (Floyd's tortoise and hare). Be ready to prove why it works.

Part 5  Merge two sorted lists; then merge K sorted lists (LC23).
        K lists, total N nodes: target O(N log K).

Part 6  Add two numbers (LC2). Digits stored in REVERSE order.
        342 + 465 -> (2->4->3) + (5->6->4) = 7->0->8  (807)
Part 6b Add two numbers II (LC445). Digits stored in FORWARD order,
        and you may not reverse the input lists. (Use stacks.)
        (7->2->4->3) + (5->6->4) = 7->8->0->7

Part 7  Remove Nth node from end (LC19) in ONE pass.
        1->2->3->4->5, n=2  =>  1->2->3->5

Part 8  Copy list with random pointer (LC138) in O(1) extra space
        (interleave copies, wire randoms, unweave). Do the dict version
        first if you like, then the O(1) one.

Part 9  Sort a linked list (LC148) in O(n log n) time and O(1) extra
        space -> bottom-up (iterative) merge sort. Top-down recursion is
        O(log n) stack; say why bottom-up is the "real" answer.

Part 10 Palindrome linked list (LC234) in O(n) time, O(1) space.
        Restore the list afterwards (interviewer may check).
------------------------------------------------------------------------------
"""
from __future__ import annotations

import heapq
from typing import Iterable, List, Optional


class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next

    def __repr__(self) -> str:  # handy in a debugger
        return f"ListNode({self.val})"


class RandomNode:
    def __init__(self, val: int, next: Optional["RandomNode"] = None,
                 random: Optional["RandomNode"] = None):
        self.val = val
        self.next = next
        self.random = random


# ----------------------------------------------------------------- helpers
def build_list(vals: Iterable[int]) -> Optional[ListNode]:
    dummy = ListNode()
    cur = dummy
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next


def to_list(head: Optional[ListNode], limit: int = 10_000) -> List[int]:
    out: List[int] = []
    while head is not None and len(out) < limit:
        out.append(head.val)
        head = head.next
    return out


def build_random_list(vals: List[int], randoms: List[Optional[int]]) -> Optional[RandomNode]:
    """randoms[i] is the index of the node that node i's `random` points to."""
    nodes = [RandomNode(v) for v in vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    for i, r in enumerate(randoms):
        nodes[i].random = nodes[r] if r is not None else None
    return nodes[0] if nodes else None


def random_list_to_pairs(head: Optional[RandomNode]) -> List[tuple]:
    """Serialise as [(val, random_index_or_None), ...]."""
    nodes: List[RandomNode] = []
    cur = head
    while cur is not None:
        nodes.append(cur)
        cur = cur.next
    idx = {id(n): i for i, n in enumerate(nodes)}
    return [(n.val, idx[id(n.random)] if n.random is not None else None) for n in nodes]


# ----------------------------------------------------------------- Part 1
def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    pass


def reverse_list_recursive(head: Optional[ListNode]) -> Optional[ListNode]:
    pass


# ----------------------------------------------------------------- Part 2
def reverse_k_group(head: Optional[ListNode], k: int) -> Optional[ListNode]:
    pass


# ----------------------------------------------------------------- Part 3
def reorder_list(head: Optional[ListNode]) -> None:
    """Modify in place; return nothing."""
    pass


# ----------------------------------------------------------------- Part 4
def detect_cycle(head: Optional[ListNode]) -> Optional[ListNode]:
    pass


# ----------------------------------------------------------------- Part 5
def merge_two_lists(a: Optional[ListNode], b: Optional[ListNode]) -> Optional[ListNode]:
    pass


def merge_k_lists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    pass


# ----------------------------------------------------------------- Part 6
def add_two_numbers(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    """Digits in reverse order (least significant first)."""
    pass


def add_two_numbers_forward(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    """Digits in forward order (most significant first). Do not reverse inputs."""
    pass


# ----------------------------------------------------------------- Part 7
def remove_nth_from_end(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    pass


# ----------------------------------------------------------------- Part 8
def copy_random_list(head: Optional[RandomNode]) -> Optional[RandomNode]:
    pass


# ----------------------------------------------------------------- Part 9
def sort_list(head: Optional[ListNode]) -> Optional[ListNode]:
    """Bottom-up merge sort, O(n log n) time, O(1) extra space."""
    pass


# ----------------------------------------------------------------- Part 10
def is_palindrome(head: Optional[ListNode]) -> bool:
    pass


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    assert to_list(reverse_list(build_list([1, 2, 3, 4]))) == [4, 3, 2, 1]
    assert to_list(reverse_list(build_list([1]))) == [1]
    assert reverse_list(None) is None
    assert to_list(reverse_list_recursive(build_list([1, 2, 3, 4]))) == [4, 3, 2, 1]
    assert reverse_list_recursive(None) is None

    # Part 2
    assert to_list(reverse_k_group(build_list([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert to_list(reverse_k_group(build_list([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
    assert to_list(reverse_k_group(build_list([1, 2, 3, 4, 5]), 1)) == [1, 2, 3, 4, 5]
    assert to_list(reverse_k_group(build_list([1, 2, 3, 4, 5, 6]), 3)) == [3, 2, 1, 6, 5, 4]
    assert to_list(reverse_k_group(build_list([1, 2]), 3)) == [1, 2]

    # Part 3
    h = build_list([1, 2, 3, 4, 5]); reorder_list(h); assert to_list(h) == [1, 5, 2, 4, 3]
    h = build_list([1, 2, 3, 4]); reorder_list(h); assert to_list(h) == [1, 4, 2, 3]
    h = build_list([1]); reorder_list(h); assert to_list(h) == [1]
    h = build_list([1, 2]); reorder_list(h); assert to_list(h) == [1, 2]

    # Part 4
    nodes = [ListNode(i) for i in range(6)]
    for i in range(5):
        nodes[i].next = nodes[i + 1]
    nodes[5].next = nodes[2]
    assert detect_cycle(nodes[0]) is nodes[2]
    nodes[5].next = nodes[5]
    assert detect_cycle(nodes[0]) is nodes[5]
    assert detect_cycle(build_list([1, 2, 3])) is None
    assert detect_cycle(None) is None
    one = ListNode(1); one.next = one
    assert detect_cycle(one) is one

    # Part 5
    assert to_list(merge_two_lists(build_list([1, 2, 4]), build_list([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    assert to_list(merge_two_lists(None, build_list([0]))) == [0]
    assert merge_two_lists(None, None) is None
    assert to_list(merge_k_lists([build_list([1, 4, 5]), build_list([1, 3, 4]), build_list([2, 6])])) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_lists([]) is None
    assert merge_k_lists([None]) is None
    assert to_list(merge_k_lists([None, build_list([1])])) == [1]

    # Part 6 / 6b
    assert to_list(add_two_numbers(build_list([2, 4, 3]), build_list([5, 6, 4]))) == [7, 0, 8]
    assert to_list(add_two_numbers(build_list([9, 9, 9, 9]), build_list([9, 9]))) == [8, 9, 0, 0, 1]
    assert to_list(add_two_numbers(build_list([0]), build_list([0]))) == [0]
    assert to_list(add_two_numbers_forward(build_list([7, 2, 4, 3]), build_list([5, 6, 4]))) == [7, 8, 0, 7]
    assert to_list(add_two_numbers_forward(build_list([9, 9]), build_list([1]))) == [1, 0, 0]
    assert to_list(add_two_numbers_forward(build_list([0]), build_list([0]))) == [0]

    # Part 7
    assert to_list(remove_nth_from_end(build_list([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]
    assert remove_nth_from_end(build_list([1]), 1) is None
    assert to_list(remove_nth_from_end(build_list([1, 2]), 2)) == [2]
    assert to_list(remove_nth_from_end(build_list([1, 2]), 1)) == [1]

    # Part 8
    src = build_random_list([7, 13, 11, 10, 1], [None, 0, 4, 2, 0])
    cp = copy_random_list(src)
    assert random_list_to_pairs(cp) == [(7, None), (13, 0), (11, 4), (10, 2), (1, 0)]
    assert random_list_to_pairs(src) == [(7, None), (13, 0), (11, 4), (10, 2), (1, 0)]  # original intact
    # deep copy: no shared nodes
    a, b = src, cp
    while a is not None:
        assert a is not b
        a, b = a.next, b.next
    assert copy_random_list(None) is None

    # Part 9
    assert to_list(sort_list(build_list([4, 2, 1, 3]))) == [1, 2, 3, 4]
    assert to_list(sort_list(build_list([-1, 5, 3, 4, 0]))) == [-1, 0, 3, 4, 5]
    assert sort_list(None) is None
    assert to_list(sort_list(build_list([1]))) == [1]
    import random
    for _ in range(50):
        arr = [random.randint(-50, 50) for _ in range(random.randint(0, 40))]
        assert to_list(sort_list(build_list(arr))) == sorted(arr)

    # Part 10
    assert is_palindrome(build_list([1, 2, 2, 1])) is True
    assert is_palindrome(build_list([1, 2, 3, 2, 1])) is True
    assert is_palindrome(build_list([1, 2])) is False
    assert is_palindrome(build_list([1])) is True
    assert is_palindrome(None) is True
    h = build_list([1, 2, 3, 2, 1]); is_palindrome(h); assert to_list(h) == [1, 2, 3, 2, 1]  # restored

    print("ok")
