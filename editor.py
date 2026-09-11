"""We're building a small piece of a code editor. Part 1: given the text of a source file
 as a single string, write check_brackets(text) that returns None if every (, [, { is
   closed by the matching bracket in the right order, and otherwise returns the 1-based
     line number where the first problem is. A 'problem' is either a closing bracket that
       doesn't match the most recent open one, or an opening bracket that's never closed
         — for that second case, report the line the unclosed bracket is on."""


def check_brackets(text: str):
    lbracks = {"(", "[", "{"}
    rbracks = {")": "(", "]": "[", "}": "{"}
    stack = []
    line = 1
    unclosed = -1
    for c in text:
        if c == "\n":
            line += 1
        elif c in lbracks:
            if not stack:
                unclosed = line
            stack.append(c)
        elif c in rbracks:
            if not stack or stack.pop() != rbracks[c]:
                return line
    if stack:
        return unclosed
    return None

def fold_brackets(text: str):
    stack = []
    line = 1
    order = []
    for c in text:
        if c == "\n":
            line += 1
        elif c == "{":
            stack.append(len(order))
            order.append((line, -1))
        elif c ==  "}":
            l = stack.pop()
            order[l] = (order[l][0], line)
    out = []
    for o in order:
        if o[0] != o[1]:
            out.append(o)
    return out

class Editor:
    def __init__(self, text):
        assert check_brackets(text) is None
        starts = fold_brackets(text) # (start, end) must skip inner regions
        lines = [""] + text.split("\n")
        self.regions = {} # start -> (text, nextregion, isFolded, nextafterfold)   we only go to nextafterfold if this region is folded
                    # start is start,   nextregion is min(next start, my_end + 1),   nextafterfold = my_end + 1
        text_start = 1
        text_block = ""
        cur_starts_idx = 0
        line_num = 1
        while line_num < len(lines):
            while line_num > starts[cur_starts_idx][0]:
                cur_starts_idx += 1 # find next region start
            if line_num == starts[cur_starts_idx][0]: # region starts here
                # add text region, if it is at least 1 line
                if text_start != line_num:
                    self.regions[text_start] = (text_block, line_num, False, -1)
                    text_block = ""
                    
                start = line_num
                nextafterfold = starts[cur_starts_idx][1] + 1
                nextregion = min(nextafterfold, starts[cur_starts_idx + 1][0])
                while line_num < nextregion:

                    text_block += "\n"+lines[line_num]
                    line_num += 1

                self.regions[start] = (text_block, nextregion, False, nextafterfold)
                text_block = ""
                text_start = line_num
            else:
                text_block += "\n"+lines[line_num]
                line_num += 1

    def render(self):
        output = ""
        cur = 1
        while cur != -1:
            region = self.regions[cur]
            if region[2]:
                output += "{ … }\n"
                cur = region[3]
            else:
                output += region[0]
                cur = region[1]
        print(output)

    def fold(self, line):
        if line in self.regions and self.regions[line][3] > 0:
            self.regions[line][2] = True

    def unfold(self, line):
        if line in self.regions and self.regions[line][3] > 0:
            self.regions[line][2] = False

    # lines: list of lines
    # regions: list of foldable regions
    # starts: set

    # starts should be ordered, and we insert 
