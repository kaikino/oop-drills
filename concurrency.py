from __future__ import annotations

"""Concurrency in Python (threading) - TikTok backend round

All stdlib. Every test is deterministic: it uses joins / Events / Conditions /
bounded timeouts, never a sleep for correctness. A test that hangs is a bug in
your code (a missed notify, a wrong predicate, a deadlock).

Part 1 - a thread-safe counter and the lost-update race
    Counter with incr() and value(). `self.n += 1` is LOAD / ADD / STORE; the
    GIL does not make that sequence atomic. Protect it with a threading.Lock.
    race_demo(counter, workers, steps) is given a harness that deliberately
    widens the read->write window (a Barrier between LOAD and STORE) for an
    UnsafeCounter, so all `workers` threads read the same value and only one
    increment per step survives; for your Counter it just calls incr().

    Example:
        race_demo(UnsafeCounter(), workers=8, steps=1000)  -> 1000   (7000 lost)
        race_demo(Counter(),       workers=8, steps=10000) -> 80000

    Required: incr O(1); value O(1).

Part 2 - BoundedBlockingQueue (LC1188)
    put(item) blocks while the queue is full; get() blocks while it is empty;
    size(). One Lock shared by two Conditions (not_full / not_empty).

    Example:
        q = BoundedBlockingQueue(3)
        producer puts 0..49; two consumers get 25 each
        -> every item consumed exactly once; size() never exceeded 3

    Required: put/get O(1). Explain why the wait must be in a `while` loop.

Part 3 - print in order (LC1114) and FizzBuzz (LC1195)
    Foo.first/second/third may be called from three threads in any start order;
    the callbacks must run first -> second -> third.
    FizzBuzz(n): four threads (fizz, buzz, fizzbuzz, number) share one counter
    and must emit the sequence 1..n in order; all four must exit when i > n.

    Example:
        FizzBuzz(15) -> ["1","2","fizz","4","buzz",...,"14","fizzbuzz"]

    Required: no busy-waiting (use Event / Condition / Semaphore).

Part 4 - ReadWriteLock with writer preference
    acquire_read / release_read / acquire_write / release_write. Many readers
    may hold the lock together; a writer is exclusive. A *waiting* writer must
    block new readers so that a stream of readers cannot starve writers. Expose
    `readers`, `writer`, `waiting_writers` for the test.

    Example:
        two readers hold it; a writer arrives and waits; a late reader must
        block; when both readers release, the writer runs; when it releases,
        the late reader runs.

    Required: O(1) per operation; not reentrant (say so).

Part 5 - a minimal thread pool with Future
    Future: set_result / set_exception / done / result(timeout) which re-raises
    the worker's exception in the caller and raises TimeoutError on timeout.
    SimpleThreadPool(workers): submit(fn, *args) -> Future; shutdown() joins all
    workers (use a sentinel per worker). A worker must survive a job that raises.

    Example:
        pool.submit(lambda x: x*x, 7).result(timeout=2) -> 49
        pool.submit(boom).result()  -> raises ValueError

Part 6 - dining philosophers without deadlock
    dine(n, rounds) -> list of meal counts. Each philosopher needs forks i and
    (i+1) % n. Break the circular wait by a global lock order. The harness also
    checks that no two neighbours ever eat at the same time.

    Example:
        dine(5, 20) -> [20, 20, 20, 20, 20]

Part 7 - discussion (written answer, no code)
    GIL and what it means for CPU- vs I/O-bound threads; process vs thread;
    the four deadlock conditions and how to break each; Lock vs RLock;
    Java `synchronized` vs `volatile` vs ReentrantLock; asyncio vs threads.

Part 7b - asyncio producer/consumer
    async_producer_consumer(n_items, n_consumers, capacity) -> list of squares
    of 0..n_items-1 in any order, using asyncio.Queue(maxsize=capacity) and one
    sentinel per consumer.
"""

import asyncio
import queue
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Part 1
# ---------------------------------------------------------------------------
class UnsafeCounter:
    """Given. `self.n += 1` is LOAD / ADD / STORE: not atomic."""

    def __init__(self) -> None:
        self.n = 0

    def incr(self) -> None:
        self.n += 1


class Counter:
    """Part 1: lock-protected counter. Invariant: after k incr() calls value() == k."""

    def __init__(self) -> None:
        pass

    def incr(self) -> None:
        pass

    def value(self) -> int:
        pass


def race_demo(counter: Any, workers: int, steps: int) -> int:
    """Given harness. For UnsafeCounter it widens the LOAD->STORE window with a
    Barrier so exactly one increment per step survives; for Counter it calls incr()."""
    if isinstance(counter, Counter):
        def run() -> None:
            for _ in range(steps):
                counter.incr()
    else:
        barrier = threading.Barrier(workers)

        def run() -> None:
            for _ in range(steps):
                v = counter.n            # LOAD
                barrier.wait()           # everyone has loaded the same v
                counter.n = v + 1        # STORE: all write the same v+1
                barrier.wait()
    ts = [threading.Thread(target=run) for _ in range(workers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return counter.n


# ---------------------------------------------------------------------------
# Part 2
# ---------------------------------------------------------------------------
class BoundedBlockingQueue:
    """Part 2: one Lock, two Conditions. Invariant 0 <= len(buf) <= capacity."""

    def __init__(self, capacity: int) -> None:
        pass

    def put(self, item: Any) -> None:
        pass

    def get(self) -> Any:
        pass

    def size(self) -> int:
        pass


# ---------------------------------------------------------------------------
# Part 3
# ---------------------------------------------------------------------------
class Foo:
    """Part 3: LC1114 print in order."""

    def __init__(self) -> None:
        pass

    def first(self, print_first: Callable[[], None]) -> None:
        pass

    def second(self, print_second: Callable[[], None]) -> None:
        pass

    def third(self, print_third: Callable[[], None]) -> None:
        pass


class FizzBuzz:
    """Part 3: LC1195 multithreaded FizzBuzz."""

    def __init__(self, n: int) -> None:
        pass

    def fizz(self, print_fizz: Callable[[], None]) -> None:
        pass

    def buzz(self, print_buzz: Callable[[], None]) -> None:
        pass

    def fizzbuzz(self, print_fizzbuzz: Callable[[], None]) -> None:
        pass

    def number(self, print_number: Callable[[int], None]) -> None:
        pass


# ---------------------------------------------------------------------------
# Part 4
# ---------------------------------------------------------------------------
class ReadWriteLock:
    """Part 4: writer-preferring RW lock. Expose readers / writer / waiting_writers."""

    def __init__(self) -> None:
        self.readers = 0
        self.writer = False
        self.waiting_writers = 0

    def acquire_read(self) -> None:
        pass

    def release_read(self) -> None:
        pass

    def acquire_write(self) -> None:
        pass

    def release_write(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Part 5
# ---------------------------------------------------------------------------
class Future:
    """Part 5: one-shot result box."""

    def __init__(self) -> None:
        pass

    def set_result(self, value: Any) -> None:
        pass

    def set_exception(self, exc: BaseException) -> None:
        pass

    def done(self) -> bool:
        pass

    def result(self, timeout: Optional[float] = None) -> Any:
        pass


class SimpleThreadPool:
    """Part 5: N workers pulling from a queue.Queue; sentinel shutdown."""

    def __init__(self, workers: int) -> None:
        pass

    def submit(self, fn: Callable[..., Any], *args: Any) -> Future:
        pass

    def shutdown(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Part 6
# ---------------------------------------------------------------------------
def dine(n_philosophers: int, rounds: int) -> List[int]:
    """Part 6: return per-philosopher meal counts; must not deadlock; neighbours
    must never eat simultaneously (track an `eating` list under a state lock and
    count violations; assert 0)."""
    pass


# ---------------------------------------------------------------------------
# Part 7b
# ---------------------------------------------------------------------------
async def async_producer_consumer(n_items: int, n_consumers: int, capacity: int) -> List[int]:
    """Part 7b: asyncio.Queue(maxsize=capacity), one sentinel per consumer."""
    pass


if __name__ == "__main__":
    # Part 1
    unsafe = UnsafeCounter()
    lost = race_demo(unsafe, workers=8, steps=1000)
    assert lost == 1000, lost                 # 8*1000 increments, only 1000 survive
    safe = Counter()
    assert race_demo(safe, workers=8, steps=10_000) == 80_000
    assert safe.value() == 80_000

    # Part 2
    q = BoundedBlockingQueue(3)
    produced = list(range(50))
    consumed: List[int] = []
    consumed_lock = threading.Lock()
    max_seen = [0]

    def producer() -> None:
        for x in produced:
            q.put(x)
            with consumed_lock:
                max_seen[0] = max(max_seen[0], q.size())

    def consumer(n: int) -> None:
        for _ in range(n):
            x = q.get()
            with consumed_lock:
                consumed.append(x)

    ts = [threading.Thread(target=producer)] + [threading.Thread(target=consumer, args=(25,)) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=5)
    assert all(not t.is_alive() for t in ts)
    assert sorted(consumed) == produced
    assert max_seen[0] <= 3
    assert q.size() == 0

    # Part 3: LC1114
    order: List[str] = []
    foo = Foo()
    fs = [
        threading.Thread(target=foo.third, args=(lambda: order.append("third"),)),
        threading.Thread(target=foo.second, args=(lambda: order.append("second"),)),
        threading.Thread(target=foo.first, args=(lambda: order.append("first"),)),
    ]
    for t in fs:
        t.start()
    for t in fs:
        t.join(timeout=5)
    assert order == ["first", "second", "third"], order

    # Part 3: LC1195
    out: List[str] = []
    fb = FizzBuzz(15)
    fbt = [
        threading.Thread(target=fb.fizz, args=(lambda: out.append("fizz"),)),
        threading.Thread(target=fb.buzz, args=(lambda: out.append("buzz"),)),
        threading.Thread(target=fb.fizzbuzz, args=(lambda: out.append("fizzbuzz"),)),
        threading.Thread(target=fb.number, args=(lambda i: out.append(str(i)),)),
    ]
    for t in fbt:
        t.start()
    for t in fbt:
        t.join(timeout=5)
    assert all(not t.is_alive() for t in fbt)
    assert out == ["1", "2", "fizz", "4", "buzz", "fizz", "7", "8", "fizz", "buzz", "11", "fizz", "13", "14", "fizzbuzz"], out

    # Part 4: readers share; a waiting writer blocks new readers
    rw = ReadWriteLock()
    rw.acquire_read()
    rw.acquire_read()                          # two readers coexist
    assert rw.readers == 2
    writer_got = threading.Event()

    def writer() -> None:
        rw.acquire_write()
        writer_got.set()

    wt = threading.Thread(target=writer)
    wt.start()
    while rw.waiting_writers == 0:            # let the writer register itself
        time.sleep(0.001)
    assert not writer_got.is_set()
    late_reader_got = threading.Event()

    def late_reader() -> None:
        rw.acquire_read()
        late_reader_got.set()
        rw.release_read()

    lr = threading.Thread(target=late_reader)
    lr.start()
    assert not late_reader_got.wait(0.05)     # writer preference: new reader blocked
    rw.release_read()
    rw.release_read()
    assert writer_got.wait(2)                 # writer runs once readers drain
    assert not late_reader_got.wait(0.05)     # still blocked: writer active
    rw.release_write()
    assert late_reader_got.wait(2)
    wt.join(); lr.join()
    assert rw.readers == 0 and not rw.writer

    # Part 5
    pool = SimpleThreadPool(4)
    futs = [pool.submit(lambda x: x * x, i) for i in range(20)]
    assert [f.result(timeout=2) for f in futs] == [i * i for i in range(20)]

    def boom() -> None:
        raise ValueError("bad")

    ef = pool.submit(boom)
    try:
        ef.result(timeout=2)
        assert False, "should raise"
    except ValueError:
        pass
    gate = threading.Event()
    slow = pool.submit(gate.wait)
    try:
        slow.result(timeout=0.01)
        assert False
    except TimeoutError:
        pass
    gate.set()
    assert slow.result(timeout=2) is True
    pool.shutdown()
    with ThreadPoolExecutor(max_workers=4) as ex:
        assert list(ex.map(lambda x: x + 1, range(5))) == [1, 2, 3, 4, 5]
        assert ex.submit(pow, 2, 10).result() == 1024

    # Part 6
    assert dine(5, 20) == [20] * 5

    # Part 7b
    res = asyncio.run(async_producer_consumer(100, 3, capacity=5))
    assert sorted(res) == [i * i for i in range(100)]
    print("ok")
