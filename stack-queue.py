"""
STACKS & QUEUES -- interviewer script (45-60 min; 3-4 parts typical)

Setup: "A few classic problems that show up in our order-processing and
config-parsing services. Use only lists / collections.deque."

------------------------------------------------------------------------------
Part 1  MinStack (LC155): push, pop, top, get_min -- all O(1).
        Follow-up: can you do it storing only the differences (O(1) extra)?
        Not required; explain the idea.

Part 2  Queue using two stacks (LC232): push, pop, peek, empty.
        Every operation must be AMORTISED O(1). Explain the amortised
        argument (each element moves between stacks at most once).

Part 3  Evaluate Reverse Polish Notation (LC150).
        ["2","1","+","3","*"] -> 9 ; ["4","13","5","/","+"] -> 6
        Division truncates toward zero: 6 / -132 = 0, -7 / 2 = -3.

Part 4  Basic Calculator II (LC227): "3+2*2" -> 7, " 3/2 " -> 1,
        " 3+5 / 2 " -> 5. Non-negative ints, + - * /, spaces, no parens.
        Target O(n) time; O(n) stack, then O(1) if you can.
Part 4b Basic Calculator (LC224 + LC772 flavour): now WITH parentheses.
        "(1+(4+5+2)-3)+(6+8)" -> 23 ; "2*(5+5*2)/3+(6/2+8)" -> 21
        Recursion or a stack of (result, sign) frames.

Part 5  Decode string (LC394): "3[a2[c]]" -> "accaccacc",
        "2[abc]3[cd]ef" -> "abcabccdcdcdef". Digits may be multi-char.

Part 6  Simplify Unix path (LC71): "/a/./b/../../c/" -> "/c",
        "/../" -> "/", "/home//foo/" -> "/home/foo".

Part 7  Valid parentheses (LC20) for ()[]{}.
        Follow-up (LC921 style): given only '(' and ')', the minimum number
        of insertions to make the string valid: "())" -> 1, "(((" -> 3,
        "()))((" -> 4.

Part 8  Asteroid collision (LC735). "Atoms move along a line; positive
        = right, negative = left, |value| = size. When two meet the smaller
        explodes; equal sizes both explode. Same direction never meets."
        [5,10,-5] -> [5,10] ; [8,-8] -> [] ; [10,2,-5] -> [10]
        [1,2,3,-1,-4,5] -> [-4,5]     (asked verbatim at a TikTok intern round)
------------------------------------------------------------------------------
"""
from __future__ import annotations

from typing import List, Optional


# ----------------------------------------------------------------- Part 1
class MinStack:
    def __init__(self) -> None:
        pass

    def push(self, val: int) -> None:
        pass

    def pop(self) -> None:
        pass

    def top(self) -> int:
        pass

    def get_min(self) -> int:
        pass


# ----------------------------------------------------------------- Part 2
class MyQueue:
    def __init__(self) -> None:
        pass

    def push(self, x: int) -> None:
        pass

    def pop(self) -> int:
        pass

    def peek(self) -> int:
        pass

    def empty(self) -> bool:
        pass


# ----------------------------------------------------------------- Part 3
def eval_rpn(tokens: List[str]) -> int:
    pass


# ----------------------------------------------------------------- Part 4
def calculate_ii(s: str) -> int:
    """+ - * / with precedence, no parentheses."""
    pass


def calculate(s: str) -> int:
    """+ - * / with precedence AND parentheses."""
    pass


# ----------------------------------------------------------------- Part 5
def decode_string(s: str) -> str:
    pass


# ----------------------------------------------------------------- Part 6
def simplify_path(path: str) -> str:
    pass


# ----------------------------------------------------------------- Part 7
def is_valid(s: str) -> bool:
    pass


def min_insertions_to_balance(s: str) -> int:
    """Only '(' and ')'. Each insertion adds one char."""
    pass


# ----------------------------------------------------------------- Part 8
def asteroid_collision(asteroids: List[int]) -> List[int]:
    pass


# ----------------------------------------------------------------- tests
if __name__ == "__main__":
    # Part 1
    ms = MinStack()
    ms.push(-2); ms.push(0); ms.push(-3)
    assert ms.get_min() == -3
    ms.pop()
    assert ms.top() == 0
    assert ms.get_min() == -2
    ms.push(-2); ms.push(5)
    assert ms.get_min() == -2
    ms.pop(); ms.pop()
    assert ms.get_min() == -2
    ms.pop(); ms.pop()
    ms.push(7)
    assert ms.get_min() == 7 and ms.top() == 7

    # Part 2
    q = MyQueue()
    q.push(1); q.push(2)
    assert q.peek() == 1
    assert q.pop() == 1
    assert q.empty() is False
    q.push(3)
    assert q.pop() == 2
    assert q.pop() == 3
    assert q.empty() is True

    # Part 3
    assert eval_rpn(["2", "1", "+", "3", "*"]) == 9
    assert eval_rpn(["4", "13", "5", "/", "+"]) == 6
    assert eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
    assert eval_rpn(["-7", "2", "/"]) == -3
    assert eval_rpn(["42"]) == 42

    # Part 4
    assert calculate_ii("3+2*2") == 7
    assert calculate_ii(" 3/2 ") == 1
    assert calculate_ii(" 3+5 / 2 ") == 5
    assert calculate_ii("14-3/2") == 13
    assert calculate_ii("1-1+1") == 1
    assert calculate_ii("100") == 100
    assert calculate_ii("2*3*4-8/2/2") == 22
    # Part 4b
    assert calculate("1 + 1") == 2
    assert calculate(" 2-1 + 2 ") == 3
    assert calculate("(1+(4+5+2)-3)+(6+8)") == 23
    assert calculate("2*(5+5*2)/3+(6/2+8)") == 21
    assert calculate("(2+6*3+5-(3*14/7+2)*5)+3") == -12
    assert calculate("-(3+2)") == -5
    assert calculate("((1))") == 1

    # Part 5
    assert decode_string("3[a]2[bc]") == "aaabcbc"
    assert decode_string("3[a2[c]]") == "accaccacc"
    assert decode_string("2[abc]3[cd]ef") == "abcabccdcdcdef"
    assert decode_string("10[a]") == "a" * 10
    assert decode_string("abc") == "abc"
    assert decode_string("") == ""

    # Part 6
    assert simplify_path("/home/") == "/home"
    assert simplify_path("/../") == "/"
    assert simplify_path("/home//foo/") == "/home/foo"
    assert simplify_path("/a/./b/../../c/") == "/c"
    assert simplify_path("/a/../../b/../c//.//") == "/c"
    assert simplify_path("/a//b////c/d//././/..") == "/a/b/c"
    assert simplify_path("/...") == "/..."   # '...' is a valid name

    # Part 7
    assert is_valid("()[]{}") is True
    assert is_valid("([)]") is False
    assert is_valid("{[]}") is True
    assert is_valid("(") is False
    assert is_valid(")") is False
    assert is_valid("") is True
    assert min_insertions_to_balance("())") == 1
    assert min_insertions_to_balance("(((") == 3
    assert min_insertions_to_balance("()") == 0
    assert min_insertions_to_balance("()))((") == 4
    assert min_insertions_to_balance("") == 0

    # Part 8
    assert asteroid_collision([5, 10, -5]) == [5, 10]
    assert asteroid_collision([8, -8]) == []
    assert asteroid_collision([10, 2, -5]) == [10]
    assert asteroid_collision([-2, -1, 1, 2]) == [-2, -1, 1, 2]
    assert asteroid_collision([1, 2, 3, -1, -4, 5]) == [-4, 5]
    assert asteroid_collision([1, -2, -2, -2]) == [-2, -2, -2]
    assert asteroid_collision([]) == []

    print("ok")
