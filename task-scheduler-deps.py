from __future__ import annotations

"""Task Scheduler with Dependencies (order pipeline: fraud check -> payment ->
inventory -> shipping label ...)

A job is a dict `tasks`: task id -> list of task ids it depends on (all of
which must finish before it may start). Every dependency id is also a key of
`tasks`. Durations, when needed, come from a dict `duration`: id -> int > 0.
No clock is injected: time is simulated.

Part 1 - topological order, deterministic
    topo_order(tasks) -> list of ids such that every task appears after all of
    its dependencies. Among all valid orders return the lexicographically
    smallest (by id), i.e. Kahn's algorithm with a min-heap of ready tasks.

    Example:
        tasks = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}
        topo_order(tasks) -> ["A", "B", "C", "D"]
        topo_order({"b": [], "a": ["b"], "c": []}) -> ["b", "a", "c"]

    Required: O((V + E) log V).

Part 2 - unlimited workers: makespan and critical path
    makespan(tasks, duration) -> (total_time, path). With unlimited workers a
    task starts as soon as its last dependency finishes; the makespan is the
    longest weighted path. `path` is one such longest path in execution order;
    break ties by choosing the smallest id at each step (start from the task
    with the latest finish, walk back through the dependency that finished
    last).

    Example:
        duration = {"A": 3, "B": 2, "C": 4, "D": 1}
        makespan(tasks, duration) -> (8, ["A", "C", "D"])

    Required: O((V + E) log V) via the topological order.

Part 3 - W workers: list scheduling
    schedule(tasks, duration, W) -> (total_time, start): start maps id ->
    start time. Simulate: at any moment, when a worker is free and tasks are
    ready, start the ready task with the LONGEST remaining critical path
    (its duration + longest path to any sink), ties by smallest id. Tasks are
    started at the current time; a worker becomes free when its task ends.

    Example:
        tasks = {"X": [], "Y": ["X"], "Z": ["Y"], "Q": ["Z"], "P": [], "R": []}
        duration = {"X": 1, "Y": 1, "Z": 1, "Q": 1, "P": 3, "R": 1}
        schedule(tasks, duration, 2)
            -> (4, {"X": 0, "P": 0, "Y": 1, "Z": 2, "Q": 3, "R": 3})
        (Starting tasks in id order instead would give makespan 5.)

    Required: O(V log V + E). With W >= V the total must equal Part 2.

Part 4 - cycles
    find_cycle(tasks) -> Optional[list]: a list of ids [t0, t1, ..., tk] such
    that t0 depends on t1, t1 depends on t2, ..., tk depends on t0; None if
    the graph is a DAG. Make topo_order raise ValueError (mentioning the
    cycle) instead of returning a partial order.

    Example:
        find_cycle({"A": ["B"], "B": ["C"], "C": ["A"], "D": []})
            -> ["A", "B", "C"] (any rotation is fine)

    Required: O(V + E), iterative or recursive DFS with three colours.

Part 5 - discussion (written answer, no code)
    How does a DAG scheduler such as Airflow run this at scale? Cover: the
    scheduler loop (find tasks whose upstreams succeeded, enqueue to workers),
    task state machine (queued/running/success/failed/up_for_retry), retries
    with backoff and why every task must be idempotent (a retried "charge the
    card" must not charge twice: idempotency keys), what happens when a
    worker dies mid-task (heartbeats, zombie detection), and per-task
    priority weights vs. pool slots (the W here).
"""

import heapq
from typing import Dict, List, Optional, Tuple

Graph = Dict[str, List[str]]


def topo_order(tasks: Graph) -> List[str]:
    """Part 1 (+ Part 4: raise ValueError('cycle ...') on a cycle)."""
    pass


def makespan(tasks: Graph, duration: Dict[str, int]) -> Tuple[int, List[str]]:
    """Part 2: (total_time, critical path in execution order)."""
    pass


def schedule(tasks: Graph, duration: Dict[str, int], W: int) -> Tuple[int, Dict[str, int]]:
    """Part 3: (total_time, {id: start_time}) with W workers, longest-tail first."""
    pass


def find_cycle(tasks: Graph) -> Optional[List[str]]:
    """Part 4: a dependency cycle [t0, t1, ..., tk] (t0 depends on t1, ...,
    tk depends on t0) or None."""
    pass


if __name__ == "__main__":
    tasks = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}
    # Part 1
    assert topo_order(tasks) == ["A", "B", "C", "D"]
    assert topo_order({"b": [], "a": ["b"], "c": []}) == ["b", "a", "c"]
    assert topo_order({}) == []
    assert topo_order({"x": ["y", "y"], "y": []}) == ["y", "x"]      # dup dep
    chain = {str(i): [str(i - 1)] if i else [] for i in range(50)}
    assert topo_order(chain) == [str(i) for i in range(50)]

    # Part 2
    duration = {"A": 3, "B": 2, "C": 4, "D": 1}
    assert makespan(tasks, duration) == (8, ["A", "C", "D"])
    assert makespan(tasks, {"A": 3, "B": 4, "C": 4, "D": 1}) == (8, ["A", "B", "D"])  # tie -> B
    assert makespan({"solo": []}, {"solo": 7}) == (7, ["solo"])
    assert makespan({}, {}) == (0, [])
    two = {"p": [], "q": []}
    assert makespan(two, {"p": 2, "q": 2}) == (2, ["p"])            # tie on sink -> smallest id

    # Part 3
    t3 = {"X": [], "Y": ["X"], "Z": ["Y"], "Q": ["Z"], "P": [], "R": []}
    d3 = {"X": 1, "Y": 1, "Z": 1, "Q": 1, "P": 3, "R": 1}
    assert schedule(t3, d3, 2) == (4, {"X": 0, "P": 0, "Y": 1, "Z": 2, "Q": 3, "R": 3})
    # W=1: at t=1 Y and P tie on tail 3 -> P by id
    assert schedule(t3, d3, 1) == (8, {"X": 0, "P": 1, "Y": 4, "Z": 5, "Q": 6, "R": 7})
    total, start = schedule(tasks, duration, 1)
    assert total == 10 and start == {"A": 0, "C": 3, "B": 7, "D": 9}
    total, start = schedule(tasks, duration, 2)
    assert total == 8 and start == {"A": 0, "B": 3, "C": 3, "D": 7}
    assert schedule(tasks, duration, 100)[0] == makespan(tasks, duration)[0]
    # validity: no task starts before its deps finish, never > W running
    total, start = schedule(t3, d3, 2)
    for t, deps in t3.items():
        for d in deps:
            assert start[d] + d3[d] <= start[t]
    for time in range(total):
        assert sum(1 for t in t3 if start[t] <= time < start[t] + d3[t]) <= 2
    assert schedule({}, {}, 3) == (0, {})

    # Part 4
    cyc = find_cycle({"A": ["B"], "B": ["C"], "C": ["A"], "D": []})
    assert cyc is not None and set(cyc) == {"A", "B", "C"} and len(cyc) == 3
    g = {"A": ["B"], "B": ["C"], "C": ["A"], "D": []}
    for i in range(3):
        assert cyc[(i + 1) % 3] in g[cyc[i]]
    assert find_cycle(tasks) is None
    assert find_cycle({"s": ["s"]}) == ["s"]
    assert find_cycle({"a": ["b"], "b": [], "c": ["d"], "d": ["e"], "e": ["c"]}) is not None
    try:
        topo_order({"A": ["B"], "B": ["A"]}); assert False
    except ValueError as e:
        assert "cycle" in str(e)
    print("ok")
