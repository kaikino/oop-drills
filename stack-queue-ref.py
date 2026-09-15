"""
STACKS & QUEUES -- reference solutions. See stack-queue.py for the script.

Recurring pitfalls:
  * Integer division must truncate toward zero: use int(a / b), not a // b
    (Python floors: -7 // 2 == -4, but the problems want -3).
  * "Flush the last operand": after the loop over a string, the final number
    still has to be applied.
  * Stack of characters vs stack of frames: when a problem nests (decode
    string, calculator with parens), push a (state, multiplier/sign) frame,
    not individual chars.
"""
from __future__ import annotations

from typing import List, Optional, Tuple


# ----------------------------------------------------------------- Part 1
class MinStack:
    # Invariant: mins[i] = min(stack[:i+1]).  Pop both together.
    def __init__(self) -> None:
        self._stack: List[int] = []
        self._mins: List[int] = []

    def push(self, val: int) -> None:
        self._stack.append(val)
        self._mins.append(val if not self._mins else min(val, self._mins[-1]))

    def pop(self) -> None:
        self._stack.pop()
        self._mins.pop()

    def top(self) -> int:
        return self._stack[-1]

    def get_min(self) -> int:
        return self._mins[-1]
    # Space-saving variant: only push to `mins` when val <= current min, and
    # pop from `mins` only when the popped value equals mins[-1].
    # O(1)-extra variant: store val - min in one stack; a negative diff marks
    # a new minimum and you recover the old min as min - diff on pop.


# ----------------------------------------------------------------- Part 2
class MyQueue:
    # `inbox` receives pushes; `outbox` serves pops in reversed (FIFO) order.
    # Only refill outbox when it is EMPTY -- refilling early breaks order.
    # Amortised: each element is pushed to inbox once, moved once, popped
    # once -> 3 stack ops per element over its life -> O(1) amortised.
    def __init__(self) -> None:
        self._in: List[int] = []
        self._out: List[int] = []

    def push(self, x: int) -> None:
        self._in.append(x)

    def _shift(self) -> None:
        if not self._out:
            while self._in:
                self._out.append(self._in.pop())

    def pop(self) -> int:
        self._shift()
        return self._out.pop()

    def peek(self) -> int:
        self._shift()
        return self._out[-1]

    def empty(self) -> bool:
        return not self._in and not self._out


# ----------------------------------------------------------------- Part 3
def eval_rpn(tokens: List[str]) -> int:
    # Operand order matters: b is popped first, a second -> a op b.
    stack: List[int] = []
    for tok in tokens:
        if tok in ("+", "-", "*", "/"):
            b = stack.pop()
            a = stack.pop()
            if tok == "+":
                stack.append(a + b)
            elif tok == "-":
                stack.append(a - b)
            elif tok == "*":
                stack.append(a * b)
            else:
                stack.append(int(a / b))   # truncate toward zero
        else:
            stack.append(int(tok))       # int("-11") works; "-" alone is an op
    return stack[0]   # O(n) time / space


# ----------------------------------------------------------------- Part 4
def calculate_ii(s: str) -> int:
    # Stack of signed terms.  On '+'/'-' push the number with its sign; on
    # '*'/'/' pop the previous term and combine immediately (precedence).
    # Sum the stack at the end.  Process the pending number when we see an
    # operator OR reach the end of the string.
    stack: List[int] = []
    num = 0
    op = "+"
    for i, ch in enumerate(s):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if (not ch.isdigit() and ch != " ") or i == len(s) - 1:
            if op == "+":
                stack.append(num)
            elif op == "-":
                stack.append(-num)
            elif op == "*":
                stack.append(stack.pop() * num)
            else:
                stack.append(int(stack.pop() / num))
            op = ch
            num = 0
    return sum(stack)
    # O(1)-space variant: keep `total`, `last` (the last term).  '*'/'/'
    # modify `last` only; '+'/'-' do total += last, last = ±num.


def calculate(s: str) -> int:
    # Recursive-descent over an index.  Each call evaluates until ')' or end
    # using the same signed-terms stack; '(' recurses to get a number.
    # A leading '-' or "(-" is handled because op starts as '+' and num 0.
    n = len(s)
    i = 0

    def parse() -> int:
        nonlocal i
        stack: List[int] = []
        num = 0
        op = "+"
        while i < n:
            ch = s[i]
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == "(":
                i += 1
                num = parse()          # returns with i at the matching ')'
            if ch in "+-*/)" or i == n - 1:
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                elif op == "/":
                    stack.append(int(stack.pop() / num))
                if ch == ")":
                    return sum(stack)
                op = ch
                num = 0
            i += 1
        return sum(stack)

    return parse()
    # O(n) time, O(depth) stack.  LC224 (only + -) can be done iteratively
    # with a stack of (result_so_far, sign) pushed at '(' and popped at ')'.


# ----------------------------------------------------------------- Part 5
def decode_string(s: str) -> str:
    # Frame stack: at '[' push (current_string, repeat_count) and reset;
    # at ']' pop and do prev + cur * k.  Multi-digit counts accumulate.
    stack: List[Tuple[str, int]] = []
    cur: List[str] = []
    k = 0
    for ch in s:
        if ch.isdigit():
            k = k * 10 + int(ch)
        elif ch == "[":
            stack.append(("".join(cur), k))
            cur, k = [], 0
        elif ch == "]":
            prev, times = stack.pop()
            cur = [prev + "".join(cur) * times]
        else:
            cur.append(ch)
    return "".join(cur)   # O(output length)


# ----------------------------------------------------------------- Part 6
def simplify_path(path: str) -> str:
    # Split on '/', ignore '' and '.', pop on '..' (if possible), push else.
    stack: List[str] = []
    for part in path.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return "/" + "/".join(stack)   # O(n)


# ----------------------------------------------------------------- Part 7
def is_valid(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: List[str] = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack   # leftover openers -> invalid


def min_insertions_to_balance(s: str) -> int:
    # Greedy counter: `open` = unmatched '(' so far.  A ')' with no open
    # needs one '(' inserted before it.  Leftover opens each need a ')'.
    open_ = 0
    insertions = 0
    for ch in s:
        if ch == "(":
            open_ += 1
        elif open_ > 0:
            open_ -= 1
        else:
            insertions += 1
    return insertions + open_   # O(n) time, O(1) space


# ----------------------------------------------------------------- Part 8
def asteroid_collision(asteroids: List[int]) -> List[int]:
    # Stack of survivors.  Only a right-mover on the stack (top > 0) can
    # collide with an incoming left-mover (a < 0).  Loop while the incoming
    # one keeps winning; `alive` tracks whether it survives to be pushed.
    stack: List[int] = []
    for a in asteroids:
        alive = True
        while alive and a < 0 and stack and stack[-1] > 0:
            top = stack[-1]
            if top < -a:
                stack.pop()          # incoming destroys top, keep checking
            elif top == -a:
                stack.pop()
                alive = False        # both explode
            else:
                alive = False        # top survives, incoming dies
        if alive:
            stack.append(a)
    return stack   # O(n): each asteroid pushed/popped at most once

# Trace for [1,2,3,-1,-4,5]:  stack [1,2,3]; -1 vs 3 -> -1 dies;
# -4 vs 3,2,1 -> all popped, -4 pushed; 5 pushed -> [-4, 5].


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
    assert simplify_path("/...") == "/..."

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

# INTERVIEWER FOLLOW-UPS
# Q: Two-stack queue -- what is the worst-case cost of a single pop?
# A: O(n) when the outbox is empty and n items must be moved; but amortised O(1)
#    because each item is moved at most once in its lifetime (potential = |inbox|).
# Q: Why not refill the outbox on every push?
# A: It would move elements back and forth each time -> O(n) per op, and it
#    would also break FIFO order unless you moved everything both ways.
# Q: Calculator: how would you add unary minus and exponent (right-assoc)?
# A: Unary minus: treat "-x" as 0 - x when '-' follows '(' or is at start.
#    Exponent: shunting-yard with precedence table and right-associativity flag.
# Q: Asteroid collision -- why is it O(n) when there is a nested while loop?
# A: Each asteroid is pushed once and popped at most once; the inner loop's
#    total iterations across the whole run are bounded by the number of pops.
# Q: MinStack with O(1) extra space -- sketch it.
# A: Store diff = val - cur_min. Negative diff means val became the new min; on
#    pop, if diff < 0 restore cur_min = cur_min - diff. Needs unbounded ints.
