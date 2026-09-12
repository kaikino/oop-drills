"""We're building the client-side logic for a video player that adapts quality to the network. 
There's a fixed ladder of quality levels, given as a list of bitrates in kbit/s, lowest first 
— say [400, 1000, 2500, 5000]. Part 1: write a class Controller(ladder) with one method, 
choose(bandwidth_kbps) -> int, returning the index of the highest level whose bitrate fits 
within the measured bandwidth. If even the lowest doesn't fit, return 0 anyway — we always play something."""


# class Controller:
#     def __init__(self, ladder):
#         self.ladder = ladder

#     def choose(self, bandwidth_kbps):
#         for i in range(len(self.ladder)-1, -1, -1):
#             if self.ladder[i] <= bandwidth_kbps:
#                 return i
#         return 0


"""Now the real controller. The player runs in ticks. Each tick it plays one segment (which 
drains one segment from a buffer) and downloads one segment at the quality level you choose 
(which, when it arrives, adds one to the buffer). Add tick(bandwidth_kbps) -> int that returns 
the level to download this tick, with two rules: never switch up unless the buffer holds at 
least min_buffer segments, and never move more than one level per tick in either direction. 
Keep the current level and buffer as state; construct with Controller(ladder, min_buffer), 
buffer starts at 0, level starts at 0. Before you code, tell me the state and the order of 
operations inside one tick."""


class Controller:
    def __init__(self, ladder, min_buffer):
        self.ladder = ladder
        self.min_buffer = min_buffer
        self.buffer = 0
        self.level = 0
        self.stalls = 0

    def choose(self, bandwidth_kbps):
        for i in range(len(self.ladder)-1, -1, -1):
            if self.ladder[i] <= bandwidth_kbps:
                return i
        return 0

    def tick(self, bandwidth_kbps):
        goal = self.choose(bandwidth_kbps)
        if goal > self.level and self.buffer >= self.min_buffer:
            self.level += 1
        elif goal < self.level:
            self.level = goal
        self.buffer += bandwidth_kbps / self.ladder[self.level]
        if self.buffer < 1:
            self.stalls += 1
        else:
            self.buffer = self.buffer - 1
        return self.level
