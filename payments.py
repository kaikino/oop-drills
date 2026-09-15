"""Out-of-Order Payment Events

A payment service receives events for orders. Each event is (timestamp, order_id, type) 
where type is one of AUTH, CAPTURE, REFUND. Events arrive over the network and may be 
delivered out of timestamp order, but each event's timestamp is correct.

Rules for a single order:

AUTH must be processed before CAPTURE, and CAPTURE before REFUND.
An event that arrives before its prerequisite has been processed is held.
It is processed immediately when its prerequisite is processed.
If an event arrives and its prerequisite has already been processed, it is processed immediately.
Duplicate events (same order_id and type) after the first are ignored.
Any CAPTURE or REFUND whose prerequisite has still not arrived after the entire stream is dropped.

Given the events in arrival order, return the list of (order_id, type) in the order they were actually processed. 
When processing one event unblocks several held events for the same order, process them in prerequisite order (CAPTURE then REFUND).

Function

process(events: list[tuple[int, str, str]]) -> list[tuple[str, str]]

Example

events = [
  (5,  "o1", "CAPTURE"),
  (1,  "o1", "AUTH"),
  (9,  "o2", "REFUND"),
  (3,  "o2", "AUTH"),
  (6,  "o1", "REFUND"),
  (2,  "o1", "AUTH"),      # duplicate
  (7,  "o2", "CAPTURE"),
]
return = [("o1","AUTH"), ("o1","CAPTURE"), ("o2","AUTH"), ("o1","REFUND"), ("o2","CAPTURE"), ("o2","REFUND")]

Constraints: up to 10⁵ events, up to 10⁴ distinct orders. Target O(n)."""

def process(events: list[tuple[int, str, str]]) -> list[tuple[str, str]]:
    typeidx = {"AUTH": 0, "CAPTURE": 1, "REFUND": 2}
    idxtype = ["AUTH", "CAPTURE", "REFUND"]
    # dict:   order_id -> [received_set, next_idx]
    orders = {}
    out = []
    for ts, id, type in events:
        idx = typeidx[type]
        if id not in orders: 
            orders[id] = [{}, 0]
        order = orders[id]
        if idx not in order[0]:
            order[0].add(idx)
            if idx == order[1]: # filled gap
                while idx in order[0]:
                    out.append((id, idxtype[idx]))
                    idx += 1
                    order[1] += 1

                    

        
