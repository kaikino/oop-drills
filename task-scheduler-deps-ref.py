from __future__ import annotations

"""Task Scheduler with Dependencies (order pipeline: fraud check -> payment ->
inventory -> shipping label ...) -- REFERENCE

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


# ---------------------------------------------------------------------------
# Part 1 + 4
# DATA SHAPE: indeg: Dict[id, int]; children: Dict[id, List[id]] (dep -> tasks
#             that depend on it); heap of ready ids.
# INVARIANT:  a task enters the heap exactly when its indegree hits 0.
# COMPLEXITY: O((V + E) log V).
# PITFALL:    duplicates in a dependency list would double-count indegree;
#             dedupe. If the output is shorter than V there is a cycle.
# ---------------------------------------------------------------------------
def _children(tasks: Graph) -> Dict[str, List[str]]:
    ch: Dict[str, List[str]] = {t: [] for t in tasks}
    for t, deps in tasks.items():
        for d in set(deps):
            ch[d].append(t)
    return ch


def topo_order(tasks: Graph) -> List[str]:
    indeg = {t: len(set(deps)) for t, deps in tasks.items()}
    children = _children(tasks)
    ready = [t for t, d in indeg.items() if d == 0]
    heapq.heapify(ready)
    order: List[str] = []
    while ready:
        t = heapq.heappop(ready)
        order.append(t)
        for c in children[t]:
            indeg[c] -= 1
            if indeg[c] == 0:
                heapq.heappush(ready, c)
    if len(order) != len(tasks):
        raise ValueError(f"cycle detected: {find_cycle(tasks)}")
    return order


def find_cycle(tasks: Graph) -> Optional[List[str]]:
    """Iterative 3-colour DFS along 'depends on' edges; returns the cycle."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {t: WHITE for t in tasks}
    for root in tasks:
        if colour[root] != WHITE:
            continue
        path: List[str] = []                       # current grey stack
        stack: List[Tuple[str, int]] = [(root, 0)]  # (node, next dep index)
        colour[root] = GREY
        path.append(root)
        while stack:
            node, i = stack[-1]
            deps = tasks[node]
            if i < len(deps):
                stack[-1] = (node, i + 1)
                d = deps[i]
                if colour[d] == GREY:               # back edge -> cycle
                    return path[path.index(d):]
                if colour[d] == WHITE:
                    colour[d] = GREY
                    path.append(d)
                    stack.append((d, 0))
            else:
                colour[node] = BLACK
                path.pop()
                stack.pop()
    return None


# ---------------------------------------------------------------------------
# Part 2
# DATA SHAPE: finish: Dict[id, int] earliest finish; via: Dict[id, Optional[id]]
#             = the dependency that determined finish (latest finish, then
#             smallest id).
# COMPLEXITY: one pass over the topological order: O((V + E) log V).
# PITFALL:    ties must be resolved with the same rule in both the forward
#             pass (which dep) and the final pick (which sink), otherwise
#             the path is not deterministic.
# ---------------------------------------------------------------------------
def makespan(tasks: Graph, duration: Dict[str, int]) -> Tuple[int, List[str]]:
    finish: Dict[str, int] = {}
    via: Dict[str, Optional[str]] = {}
    for t in topo_order(tasks):
        # latest finish, then smallest id (sorted + strict > keeps the first)
        best: Optional[str] = None
        for d in sorted(tasks[t]):
            if best is None or finish[d] > finish[best]:
                best = d
        via[t] = best
        finish[t] = duration[t] + (finish[best] if best else 0)
    if not finish:
        return 0, []
    end = min((t for t in finish), key=lambda t: (-finish[t], t))
    path = []
    cur: Optional[str] = end
    while cur is not None:
        path.append(cur)
        cur = via[cur]
    return finish[end], path[::-1]


# ---------------------------------------------------------------------------
# Part 3
# DATA SHAPE: tail: Dict[id, int] = duration + longest path to a sink
#             (computed on the REVERSED topological order); ready: heap of
#             (-tail, id); running: heap of (finish_time, id); indeg counts.
# INVARIANT:  at time t every task in `ready` has all deps finished at <= t.
#             Events are processed in finish-time order so `t` never goes back.
# COMPLEXITY: each task is pushed/popped once from each heap: O(V log V + E).
# PITFALL:    when several tasks finish at the same time, release ALL of them
#             before assigning workers, or a higher-priority task that became
#             ready in the same instant may lose to a lower one.
# ---------------------------------------------------------------------------
def schedule(tasks: Graph, duration: Dict[str, int], W: int) -> Tuple[int, Dict[str, int]]:
    order = topo_order(tasks)
    children = _children(tasks)
    tail: Dict[str, int] = {}
    for t in reversed(order):
        tail[t] = duration[t] + max((tail[c] for c in children[t]), default=0)
    indeg = {t: len(set(deps)) for t, deps in tasks.items()}
    ready = [(-tail[t], t) for t, d in indeg.items() if d == 0]
    heapq.heapify(ready)
    running: List[Tuple[int, str]] = []
    start: Dict[str, int] = {}
    t = 0
    free = W
    while ready or running:
        while ready and free > 0:
            _, task = heapq.heappop(ready)
            start[task] = t
            heapq.heappush(running, (t + duration[task], task))
            free -= 1
        # advance to the next finish; release everything finishing then
        t = running[0][0]
        while running and running[0][0] == t:
            _, done = heapq.heappop(running)
            free += 1
            for c in children[done]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    heapq.heappush(ready, (-tail[c], c))
    return t, start


# ---------------------------------------------------------------------------
# Part 5 - model answer
# Scheduler loop: a DAG run is a table of task instances with states. The
#   scheduler process periodically (or on events) queries "tasks whose every
#   upstream is SUCCESS and whose state is NONE", flips them to QUEUED and
#   pushes them to a broker (Celery/Kubernetes executor). Workers pull, set
#   RUNNING, heartbeat, then SUCCESS/FAILED. This is Kahn's algorithm driven
#   by a database instead of an in-memory indegree map; W is the pool size.
# Retries: FAILED -> UP_FOR_RETRY with exponential backoff (1m, 2m, 4m ...)
#   up to max_retries. A retry re-executes the task from scratch, so the
#   task must be idempotent: "charge card" carries an idempotency key
#   (order_id) that the payment provider dedupes; "write partition" uses
#   overwrite-by-partition rather than append; "send email" checks a sent
#   log first. Non-idempotent side effects must be the last step and
#   guarded.
# Worker death: the task row keeps a last_heartbeat; a zombie reaper marks
#   tasks with stale heartbeats FAILED (then retry). The executor may also
#   use leases: a worker holds a lease it must renew; expiry returns the task.
# Priority: priority_weight (like our tail length, Airflow sums downstream
#   weights) orders the queue within a pool; pools cap concurrency per
#   resource (DB connections) - the W here. Cross-DAG limits: max_active_runs.
# Watch out: the scheduler DB is the bottleneck (thousands of tasks/minute);
#   keep task bodies small, do the heavy work elsewhere.
# ---------------------------------------------------------------------------


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


# INTERVIEWER FOLLOW-UPS
# Q: Why is list scheduling by longest tail not optimal?
#    A: Multiprocessor scheduling with precedence is NP-hard; critical-path
#       list scheduling is a 2 - 1/W approximation (Graham). Show a small
#       counterexample if asked: two long independent chains vs. many short
#       tasks can be packed better by looking ahead.
# Q: Tasks have different resource needs (CPU vs. GPU)?
#    A: One pool (W) per resource type; a task waits for a slot in each pool
#       it needs, or model workers as heterogeneous and pick by capability.
# Q: The DAG changes while running (a task adds a downstream task)?
#    A: Dynamic DAGs: recompute tails lazily; new tasks enter `ready` when
#       their deps are done. Airflow re-parses DAG files each loop.
# Q: How do you detect and report ALL cycles, not just one?
#    A: Tarjan's SCC: every SCC of size > 1 (or with a self-loop) is a cycle
#       group; report each SCC.
# Q: Lexicographically smallest order vs. "earliest possible" order?
#    A: Different objectives: Part 1 optimizes ids, Part 3 optimizes time. If
#       the interviewer wants both, use the heap key (-tail, id).
