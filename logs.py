"""Log parser, Day 6. `logs.py`, 50 minutes. This one is closest to the previous intern's 
actual project, so it doubles as prep for the project conversation.

Interviewer: "Our network devices ship syslog lines to a collector. Each line looks like this:

```
2026-09-16T09:31:02Z sw-core-1 bgp: neighbor 10.0.0.2 Down (Hold Timer Expired)
2026-09-16T09:31:40Z sw-core-1 bgp: neighbor 10.0.0.2 Up
2026-09-16T09:32:11Z sw-edge-3 bgp: neighbor 10.0.5.9 Down (BGP Notification Received)
```

That's an ISO timestamp, a device name, a literal `bgp:`, the words `neighbor` and an IP, 
a state that is `Up` or `Down`, and — only for `Down` — a reason in parentheses.

Part 1: write `parse_line(line)` that returns a record with fields `ts` (a `datetime`), 
`device`, `neighbor`, `state`, and `reason` (`None` for `Up`). Pick whatever record type 
you like. Then `parse(lines)` that takes an iterable of lines and returns a list of records.

Questions?"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional, cast

@dataclass
class Record:
    ts: datetime
    device: str
    neighbor: str
    up: bool
    reason: Optional[str]

def parse_line(line):
    w = line.split(" ")
    ts = datetime.fromisoformat(w[0][:-1] + "+00:00")
    device = w[1]
    neighbor = w[4]
    up = w[5] == "Up"
    reason = None if up else " ".join(w[6:])[1:-1]
    return Record(ts, device, neighbor, up, reason)

def parse(lines):
    records = []
    for line in lines:
        records.append(parse_line(line))
    return records


"""part 2: "Now the query side. Build a Store that takes the records and answers three questions:

events(device, start, end) — all records for that device with start <= ts < end, in time order.
top_reasons(n) — the n most common Down reasons with their counts, most common first.
outages() — for each (device, neighbor) pair, the longest gap between a Down and the next Up for 
that pair, as a timedelta. A Down with no following Up is still ongoing; report it as None for 
that pair if it's the longest.

Assume the records arrive in time order. Say what structures Store.__init__ builds and the cost of each query, then code."""

from collections import defaultdict, Counter
import bisect
class Store:

    def __init__(self, records):
        self.records = records

        self.eventsdict = defaultdict(list)
        for record in records:
            self.eventsdict[record.device].append((record.ts, record))

        self.reasons = Counter([record.reason for record in records if not record.up])

        last_down = {}
        self.outage_list = {} # (device, neighbor)
        for device, (ts, record) in self.eventsdict.items():
            if record.up and (device, record.neighbor) in last_down:
                gap = ts - last_down[(device, record.neighbor)]
                if self.outage_list.get((device, record.neighbor), -1) < gap:
                    self.outage_list[(device, record.neighbor)] = gap
                del last_down[(device, record.neighbor)]
            else:
                if (device, record.neighbor) not in last_down:
                    last_down[(device, record.neighbor)] = ts

        last_ts = records[-1].ts
        for (device, neighbor), ts in last_down:
            gap = last_ts - ts
            if self.outage_list.get((device, neighbor), -1) < gap:
                self.outage_list[(device, neighbor)] = gap
    
                


    def events(self, device, start, end): # binary search tree or sorted list: device -> (ts, record)
        times = self.eventsdict.get(device, [])
        startidx = bisect.bisect_left(times, (start,))
        endidx = bisect.bisect_right(times, (end,))
        out = []
        for i in range(startidx, endidx):
            out.append(times[i][1])
        return out

    def top_reasons(self, n):
        return self.reasons.most_common(n)

    def outages(self):
        return self.outage_list;