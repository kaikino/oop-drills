"""We get conversion facts from a data feed and need to answer conversion questions. 
Part 1: write a class Converter with add_fact(from_unit, to_unit, factor) meaning 1 
from_unit = factor to_unit, and convert(value, from_unit, to_unit) -> float | None. 
For part 1 you only need to handle direct facts, plus the two things that fall out of 
them: converting a unit to itself, and using a fact in reverse. 
So after add_fact("m", "cm", 100): convert(3, "m", "cm") == 300, 
convert(50, "cm", "m") == 0.5, convert(2, "m", "m") == 2, and convert(1, "m", "kg") is None"""


# from collections import defaultdict

# class Converter:
#     def __init__(self):
#         self.matrix = defaultdict(dict)

#     def add_fact(self, from_unit, to_unit, factor):
#         # meaning 1 from_unit = factor to_unit, and
#         self.matrix[from_unit][to_unit] = factor
#         self.matrix[to_unit][from_unit] = 1/factor

#     def convert(self, value, from_unit, to_unit):
#         if (from_unit == to_unit):
#             return value
#         if from_unit in self.matrix and to_unit in self.matrix[from_unit]:
#             return self.matrix[from_unit][to_unit] * value
#         return None

"""Now facts chain. After add_fact("m", "cm", 100) and add_fact("cm", "mm", 10), convert(1, "m", "mm") 
should be 1000, and convert(1, "mm", "m") should be 0.001. Facts can chain arbitrarily deep, and None 
still means no path exists. Two sentences on the approach and its cost, then code."""


from collections import defaultdict
from math import isclose
from typing import Tuple

class Converter:
    def __init__(self):
        self.matrix = defaultdict(dict)

    def add_fact(self, from_unit, to_unit, factor):
        self.matrix[from_unit][to_unit] = factor
        self.matrix[to_unit][from_unit] = 1/factor

    def convert(self, value, from_unit, to_unit):
        if (from_unit == to_unit):
            return value
        if from_unit in self.matrix:
            if to_unit in self.matrix[from_unit]:
                return self.matrix[from_unit][to_unit] * value

            stack = [(from_unit, value)] # unit, factor
            vis = set()
            while stack:
                cur = stack.pop()
                if cur[0] == to_unit:
                    return cur[1]
                if cur[0] not in vis:
                    vis.add(cur[0])
                    for neighbor in reversed(self.matrix[cur[0]].items()):
                        if neighbor[0] not in vis:
                            stack.append((neighbor[0], cur[1] * neighbor[1]))

        return None


"""FastConverter in the same file: root: dict[unit, unit], to_root: dict[unit, float] 
(how many root-units one of this unit equals), and members: dict[root, set] so you can 
walk the smaller component on a merge. convert is the identity check, 
then root[a] == root[b] check, then value * to_root[a] / to_root[b]. add_fact has four 
cases: both units new, one new, both known in the same component (contradiction check 
with math.isclose, raise on disagreement, otherwise ignore), both known in different 
components (re-root the smaller). Trace m→cm=100, cm→mm=10, kg→g=1000, then g→mm=7 
(nonsense but tests the merge), then convert(1,"kg","m") before you say check."""



class FastConverter:
    def __init__(self):
        self.units = dict() # unit -> (parent, factor to parent)
        self.ranks = dict()

    def find(self, unit) -> Tuple[str, int]: # -> (parent, factor to parent)
        if unit not in self.units:
            self.units[unit] = (unit, 1)
            self.ranks[unit] = 1
            return self.units[unit]
        parent = self.units[unit]
        if parent[0] == unit:
            return parent
        else:
            parentparent = self.find(parent[0])
            if parent[0] != parentparent[0]:
                self.units[unit] = (parentparent[0], parentparent[1] * parent[1])
            return self.units[unit]

    def add_fact(self, from_unit, to_unit, factor):
        from_parent = self.find(from_unit)
        to_parent = self.find(to_unit)
        if from_parent[0] == to_parent[0]:
            assert isclose(from_parent[1] / to_parent[1], factor)
        else:
            if self.ranks[from_parent[0]] > self.ranks[to_parent[0]]:
                self.units[to_parent[0]] = (from_parent[0], from_parent[1]/factor/to_parent[1])
            elif self.ranks[from_parent[0]] < self.ranks[to_parent[0]]:
                self.units[from_parent[0]] = (to_parent[0], to_parent[1]*factor/from_parent[1])
            else:
                self.units[from_parent[0]] = (to_parent[0], to_parent[1]*factor/from_parent[1])
                self.ranks[to_parent[0]] += 1


    def convert(self, value, from_unit, to_unit):
        from_parent = self.find(from_unit)
        to_parent = self.find(to_unit)
        if from_parent[0] != to_parent[0]:
            return None
        return value * from_parent[1] / to_parent[1]