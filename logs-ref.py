import bisect
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Record:
    ts: datetime
    device: str
    neighbor: str
    up: bool
    reason: Optional[str]


def parse_line(line):
    w = line.split(" ")
    ts = datetime.fromisoformat(w[0].replace("Z", "+00:00"))
    up = w[5] == "Up"
    reason = None if up else " ".join(w[6:])[1:-1]
    return Record(ts, w[1], w[4], up, reason)


def parse(lines):
    return [parse_line(l) for l in lines]


class Store:
    def __init__(self, records):
        self.records = records
        self.by_device = defaultdict(list)   # device -> [Record] in time order
        self.ts_by_device = defaultdict(list)  # device -> [ts] parallel, for bisect
        for r in records:
            self.by_device[r.device].append(r)
            self.ts_by_device[r.device].append(r.ts)
        self.reasons = Counter(r.reason for r in records if not r.up)

        # Longest Down->Up gap per (device, neighbor). First Down opens; repeat
        # Downs ignored; Up with nothing open ignored. Ongoing outage measured
        # to the last record; if that beats the longest closed gap, store None.
        self.longest = {}
        open_down = {}
        for r in records:
            key = (r.device, r.neighbor)
            if r.up:
                if key in open_down:
                    gap = r.ts - open_down.pop(key)
                    if gap > self.longest.get(key, timedelta(0)):
                        self.longest[key] = gap
            elif key not in open_down:
                open_down[key] = r.ts
        last_ts = records[-1].ts if records else None
        for key, ts in open_down.items():
            if last_ts - ts > (self.longest.get(key) or timedelta(0)):
                self.longest[key] = None

    def events(self, device, start, end):          # start <= ts < end
        ts = self.ts_by_device.get(device, [])
        lo, hi = bisect.bisect_left(ts, start), bisect.bisect_left(ts, end)
        return self.by_device[device][lo:hi]

    def top_reasons(self, n):
        return self.reasons.most_common(n)

    def outages(self):
        return dict(self.longest)


if __name__ == "__main__":
    L = """2026-09-16T09:31:02Z sw-core-1 bgp: neighbor 10.0.0.2 Down (Hold Timer Expired)
2026-09-16T09:31:40Z sw-core-1 bgp: neighbor 10.0.0.2 Up
2026-09-16T09:32:11Z sw-edge-3 bgp: neighbor 10.0.5.9 Down (BGP Notification Received)
2026-09-16T09:32:30Z sw-edge-3 bgp: neighbor 10.0.5.9 Down (BGP Notification Received)
2026-09-16T09:35:00Z sw-edge-3 bgp: neighbor 10.0.5.9 Up
2026-09-16T09:40:00Z sw-edge-3 bgp: neighbor 10.0.5.9 Down (Hold Timer Expired)
2026-09-16T09:41:00Z sw-core-1 bgp: neighbor 10.0.0.2 Up""".split("\n")
    s = Store(parse(L))
    from datetime import timezone
    t = lambda h, m: datetime(2026, 9, 16, h, m, tzinfo=timezone.utc)
    print([r.ts.strftime("%H:%M:%S") for r in s.events("sw-edge-3", t(9, 32), t(9, 40))])
    print(s.top_reasons(2))
    print(s.outages())
