"""
LINKED LISTS -- reference solutions. See linked-list.py for the problem script.

General pitfalls this file guards against:
  * Relink order: save `nxt = cur.next` BEFORE you overwrite `cur.next`.
  * Losing the head: use a dummy node whenever the head can change
    (reverse-k-group, remove-nth, merge, sort).
  * Recursion depth: CPython's default limit is ~1000 frames; n = 1e5 nodes
    will blow the recursive versions. Prefer iteration in production.
"""
from __future__ import annotations

import heapq
from typing import Iterable, List, Optional


class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next

    def __repr__(self) -> str:
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
    nodes = [RandomNode(v) for v in vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    for i, r in enumerate(randoms):
        nodes[i].random = nodes[r] if r is not None else None
    return nodes[0] if nodes else None


def random_list_to_pairs(head: Optional[RandomNode]) -> List[tuple]:
    nodes: List[RandomNode] = []
    cur = head
    while cur is not None:
        nodes.append(cur)
        cur = cur.next
    idx = {id(n): i for i, n in enumerate(nodes)}
    return [(n.val, idx[id(n.random)] if n.random is not None else None) for n in nodes]


# ----------------------------------------------------------------- Part 1
def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    # Invariant: `prev` is the head of the already-reversed prefix,
    # `cur` is the head of the untouched suffix.  O(n) / O(1).
    prev: Optional[ListNode] = None
    cur = head
    while cur is not None:
        nxt = cur.next        # save first!
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


def reverse_list_recursive(head: Optional[ListNode]) -> Optional[ListNode]:
    # Base: empty or single node is its own reversal.
    # Recursive: reverse the tail, then hook `head` onto the end of it.
    # head.next is the *old* second node, which is the tail of the reversed rest.
    if head is None or head.next is None:
        return head
    new_head = reverse_list_recursive(head.next)
    head.next.next = head
    head.next = None      # otherwise we get a cycle
    return new_head       # O(n) time, O(n) stack -> RecursionError past ~1000


# ----------------------------------------------------------------- Part 2
def reverse_k_group(head: Optional[ListNode], k: int) -> Optional[ListNode]:
    # Invariant: `tail` is the last node of the already-processed prefix
    # (starts as dummy).  For each group: check k nodes exist, reverse them
    # in place, splice: tail -> new group head ... old group head -> rest.
    dummy = ListNode(0, head)
    tail = dummy
    while True:
        # 1. does a full group exist?
        probe = tail
        for _ in range(k):
            probe = probe.next
            if probe is None:
                return dummy.next
        group_next = probe.next
        # 2. reverse k nodes starting at tail.next
        prev, cur = group_next, tail.next
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # 3. splice: old group head (tail.next) is now the group's last node
        old_head = tail.next
        tail.next = prev
        tail = old_head
    # O(n) time, O(1) space.


# ----------------------------------------------------------------- Part 3
def reorder_list(head: Optional[ListNode]) -> None:
    # Three classic sub-routines: find middle (slow/fast), reverse second
    # half, alternate-merge.  O(n) time, O(1) space.
    if head is None or head.next is None:
        return
    # 1. middle: slow ends on the last node of the first half (for even n)
    #    or the exact middle (for odd n) -> second half is never longer.
    slow, fast = head, head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None            # cut the list, or the merge loops forever
    # 2. reverse second half
    prev = None
    while second is not None:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt
    second = prev
    # 3. merge alternately; first half is >= second half in length
    first = head
    while second is not None:
        n1, n2 = first.next, second.next
        first.next = second
        second.next = n1
        first, second = n1, n2


# ----------------------------------------------------------------- Part 4
def detect_cycle(head: Optional[ListNode]) -> Optional[ListNode]:
    # Floyd.  Phase 1: slow moves 1, fast moves 2; they meet inside the cycle
    # iff one exists.  Phase 2: reset one pointer to head, advance both by 1;
    # they meet at the cycle entry.
    #
    # Proof sketch: let a = distance head->entry, c = cycle length, and let
    # the pointers meet b steps past the entry.  slow travelled a+b, fast
    # travelled 2(a+b), and fast's extra distance is a whole number of loops:
    #   2(a+b) - (a+b) = a + b = m*c   for some m >= 1
    #   => a = m*c - b
    # So walking `a` steps from the meeting point (which is b past the entry)
    # lands exactly on the entry (b + a = m*c ≡ 0 mod c).  A pointer starting
    # from head also reaches the entry in `a` steps -> they meet there.
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            p = head
            while p is not slow:
                p = p.next
                slow = slow.next
            return p
    return None   # O(n) time, O(1) space


# ----------------------------------------------------------------- Part 5
def merge_two_lists(a: Optional[ListNode], b: Optional[ListNode]) -> Optional[ListNode]:
    dummy = ListNode()
    tail = dummy
    while a is not None and b is not None:
        if a.val <= b.val:      # <= keeps the merge stable
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a is not None else b
    return dummy.next


def merge_k_lists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    # Heap of (val, tie-breaker, node).  The tie-breaker is essential: ListNode
    # has no __lt__, so equal vals would raise TypeError without it.
    # O(N log K) time, O(K) heap.
    heap: List[tuple] = []
    for i, node in enumerate(lists):
        if node is not None:
            heapq.heappush(heap, (node.val, i, node))
    dummy = ListNode()
    tail = dummy
    while heap:
        _, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
    # Alternative: divide-and-conquer pairwise merging, also O(N log K).


# ----------------------------------------------------------------- Part 6
def add_two_numbers(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    # Reverse order = least significant first: just walk with a carry.
    # Pitfall: loop while ANY of l1, l2, carry is non-zero (handles 99+1).
    dummy = ListNode()
    tail = dummy
    carry = 0
    while l1 is not None or l2 is not None or carry:
        s = carry
        if l1 is not None:
            s += l1.val
            l1 = l1.next
        if l2 is not None:
            s += l2.val
            l2 = l2.next
        carry, digit = divmod(s, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    return dummy.next     # O(max(m, n))


def add_two_numbers_forward(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    # Forward order: push digits on two stacks, pop from the least significant
    # end, and build the result by prepending (head insertion) so we never
    # need to reverse anything.  O(m+n) time, O(m+n) space.
    s1: List[int] = []
    s2: List[int] = []
    while l1 is not None:
        s1.append(l1.val); l1 = l1.next
    while l2 is not None:
        s2.append(l2.val); l2 = l2.next
    head: Optional[ListNode] = None
    carry = 0
    while s1 or s2 or carry:
        s = carry + (s1.pop() if s1 else 0) + (s2.pop() if s2 else 0)
        carry, digit = divmod(s, 10)
        head = ListNode(digit, head)      # prepend
    return head


# ----------------------------------------------------------------- Part 7
def remove_nth_from_end(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    # Two pointers with a gap of n; when the leading one hits the end, the
    # trailing one is just before the node to delete.  Dummy handles n == len.
    dummy = ListNode(0, head)
    lead = trail = dummy
    for _ in range(n):
        lead = lead.next
    while lead.next is not None:
        lead = lead.next
        trail = trail.next
    trail.next = trail.next.next
    return dummy.next     # one pass, O(1) space


# ----------------------------------------------------------------- Part 8
def copy_random_list(head: Optional[RandomNode]) -> Optional[RandomNode]:
    # Interleave: A -> A' -> B -> B' -> ...   (copy sits right after original)
    # Then copy.random = orig.random.next  (the copy of the random target)
    # Then unweave.  O(n) time, O(1) extra space (excluding the output).
    if head is None:
        return None
    # 1. interleave
    cur = head
    while cur is not None:
        cur.next = RandomNode(cur.val, cur.next)
        cur = cur.next.next
    # 2. randoms
    cur = head
    while cur is not None:
        if cur.random is not None:
            cur.next.random = cur.random.next
        cur = cur.next.next
    # 3. unweave (must restore original list too)
    cur = head
    copy_head = head.next
    while cur is not None:
        cp = cur.next
        cur.next = cp.next
        cp.next = cp.next.next if cp.next is not None else None
        cur = cur.next
    return copy_head
    # Dict version: {orig: copy}, two passes -- O(n) space but simpler.


# ----------------------------------------------------------------- Part 9
def _split(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    """Detach the first n nodes; return the head of the remainder."""
    for _ in range(n - 1):
        if head is None:
            break
        head = head.next
    if head is None:
        return None
    rest = head.next
    head.next = None
    return rest


def _merge_into(tail: ListNode, a: Optional[ListNode], b: Optional[ListNode]) -> ListNode:
    """Merge a and b after `tail`; return the new tail."""
    while a is not None and b is not None:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a is not None else b
    while tail.next is not None:
        tail = tail.next
    return tail


def sort_list(head: Optional[ListNode]) -> Optional[ListNode]:
    # Bottom-up merge sort: merge runs of size 1, 2, 4, ... in passes.
    # log n passes * O(n) each = O(n log n); no recursion -> O(1) space.
    n = 0
    cur = head
    while cur is not None:
        n += 1
        cur = cur.next
    dummy = ListNode(0, head)
    size = 1
    while size < n:
        tail = dummy
        cur = dummy.next
        while cur is not None:
            left = cur
            right = _split(left, size)
            cur = _split(right, size)
            tail = _merge_into(tail, left, right)
        size *= 2
    return dummy.next
    # Top-down variant: find middle with slow/fast, recurse on halves, merge.
    # Same time, but O(log n) stack -- fine in practice, not "O(1) space".


# ----------------------------------------------------------------- Part 10
def is_palindrome(head: Optional[ListNode]) -> bool:
    # Find middle, reverse second half in place, compare, then restore.
    if head is None or head.next is None:
        return True
    slow, fast = head, head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    # reverse from slow.next
    prev, cur = None, slow.next
    while cur is not None:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    second_head = prev
    # compare (second half is <= first half in length)
    ok = True
    p, q = head, second_head
    while q is not None:
        if p.val != q.val:
            ok = False
            break
        p, q = p.next, q.next
    # restore
    prev, cur = None, second_head
    while cur is not None:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    slow.next = prev
    return ok   # O(n) time, O(1) space


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
    assert random_list_to_pairs(src) == [(7, None), (13, 0), (11, 4), (10, 2), (1, 0)]
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
    h = build_list([1, 2, 3, 2, 1]); is_palindrome(h); assert to_list(h) == [1, 2, 3, 2, 1]

    print("ok")

# INTERVIEWER FOLLOW-UPS
# Q: Your recursive reverse fails at n=1e5 -- what do you do?
# A: Use the iterative version; recursion depth is bounded by sys.getrecursionlimit
#    (~1000) and raising it risks a C-stack overflow. Iteration is O(1) space anyway.
# Q: Why does the fast pointer catch the slow one in Floyd's algorithm?
# A: Once both are in the cycle the gap shrinks by exactly 1 each step, so they
#    meet within c steps; the entry follows from a + b = m*c (see comments).
# Q: Why is merge-K with a heap O(N log K) rather than O(N log N)?
# A: The heap never holds more than K entries (one per list), so each push/pop
#    costs log K, and there are N of them.
# Q: Reorder-list: what breaks if you forget to cut the first half?
# A: The middle node still points into the second half; the alternating merge
#    then revisits nodes and loops forever / forms a cycle.
# Q: Why prefer bottom-up merge sort over top-down for linked lists?
# A: Top-down uses O(log n) stack frames; bottom-up is truly O(1) extra space
#    and also avoids the slow/fast middle-finding on every recursion level.
