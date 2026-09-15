from __future__ import annotations

"""Concurrency in Python (threading) - reference solution.

See concurrency.py for the interviewer-voice problem statement. Everything
below is stdlib only; tests are deterministic (joins / Events / Conditions /
bounded timeouts, no sleeps for correctness).
"""

import asyncio
import queue
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Part 1: Counter + a deterministic lost-update demo
# ---------------------------------------------------------------------------
class UnsafeCounter:
    """`self.n += 1` is really: LOAD n; ADD 1; STORE n. The GIL makes each
    bytecode atomic, but not the three-instruction sequence: a thread switch
    between LOAD and STORE loses one update."""

    def __init__(self) -> None:
        self.n = 0

    def incr(self) -> None:
        self.n += 1


class Counter:
    """Part 1: a Lock makes the read-modify-write critical section atomic.
    Invariant: after k successful incr() calls, value() == k."""

    def __init__(self) -> None:
        self.n = 0
        self._lock = threading.Lock()

    def incr(self) -> None:
        with self._lock:          # acquire/release even on exception
            self.n += 1

    def value(self) -> int:
        with self._lock:
            return self.n


def race_demo(counter: Any, workers: int, steps: int) -> int:
    """Simulate the lost-update interleaving deterministically.

    Each "step" does an explicit read -> (yield to other threads) -> write. A
    real `n += 1` race depends on the OS scheduler, so instead we widen the
    window with a barrier between read and write: all `workers` threads read
    the same value, then all write value+1 -> exactly one increment per step
    survives. The locked Counter is passed as `counter` in the second test and
    is exact because incr() is atomic (we never widen *its* window).
    """
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
                barrier.wait()           # don't start next step until all stored
    ts = [threading.Thread(target=run) for _ in range(workers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return counter.n


# ---------------------------------------------------------------------------
# Part 2: BoundedBlockingQueue (LC1188) with Condition
# ---------------------------------------------------------------------------
class BoundedBlockingQueue:
    """One Lock, two Conditions sharing it (not_full / not_empty).
    Invariant: 0 <= len(buf) <= capacity. Always `while` (not `if`) around wait():
    spurious wakeups and notify_all can wake a thread whose predicate is false.
    put/get are O(1)."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.buf: Deque[Any] = deque()
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def put(self, item: Any) -> None:
        with self._not_full:
            while len(self.buf) >= self.capacity:
                self._not_full.wait()
            self.buf.append(item)
            self._not_empty.notify()

    def get(self) -> Any:
        with self._not_empty:
            while not self.buf:
                self._not_empty.wait()
            item = self.buf.popleft()
            self._not_full.notify()
            return item

    def size(self) -> int:
        with self._lock:
            return len(self.buf)


# ---------------------------------------------------------------------------
# Part 3: print in order (LC1114), FizzBuzz (LC1195)
# ---------------------------------------------------------------------------
class Foo:
    """Two Events form a chain: second waits for first's event, third for second's.
    An Event is a one-shot latch; Semaphore(0) would also work (release/acquire)."""

    def __init__(self) -> None:
        self.first_done = threading.Event()
        self.second_done = threading.Event()

    def first(self, print_first: Callable[[], None]) -> None:
        print_first()
        self.first_done.set()

    def second(self, print_second: Callable[[], None]) -> None:
        self.first_done.wait()
        print_second()
        self.second_done.set()

    def third(self, print_third: Callable[[], None]) -> None:
        self.second_done.wait()
        print_third()


class FizzBuzz:
    """Four threads share a Condition and a counter `i`. Each thread waits until
    `i` is *its* kind of number (or i > n, to exit), does its work, increments
    i, and notify_all()s. The single shared counter is the ordering invariant.
    Pitfall: every waiter must also wake on i > n or the threads never exit."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.i = 1
        self.cv = threading.Condition()

    def _run(self, mine: Callable[[int], bool], emit: Callable[[int], None]) -> None:
        while True:
            with self.cv:
                while self.i <= self.n and not mine(self.i):
                    self.cv.wait()
                if self.i > self.n:
                    return
                emit(self.i)
                self.i += 1
                self.cv.notify_all()

    def fizz(self, print_fizz: Callable[[], None]) -> None:
        self._run(lambda i: i % 3 == 0 and i % 5 != 0, lambda i: print_fizz())

    def buzz(self, print_buzz: Callable[[], None]) -> None:
        self._run(lambda i: i % 5 == 0 and i % 3 != 0, lambda i: print_buzz())

    def fizzbuzz(self, print_fizzbuzz: Callable[[], None]) -> None:
        self._run(lambda i: i % 15 == 0, lambda i: print_fizzbuzz())

    def number(self, print_number: Callable[[int], None]) -> None:
        self._run(lambda i: i % 3 != 0 and i % 5 != 0, print_number)


# ---------------------------------------------------------------------------
# Part 4: ReadWriteLock with writer preference
# ---------------------------------------------------------------------------
class ReadWriteLock:
    """State: readers (active), writer (bool), waiting_writers.
    Writer preference: a new reader blocks if a writer is active OR waiting, so
    a stream of readers cannot starve writers. (The flip side: readers can
    starve if writers keep arriving; fair variants use a FIFO ticket.)
    Not reentrant: a reader that calls acquire_write() would deadlock itself."""

    def __init__(self) -> None:
        self._cv = threading.Condition(threading.Lock())
        self.readers = 0
        self.writer = False
        self.waiting_writers = 0

    def acquire_read(self) -> None:
        with self._cv:
            while self.writer or self.waiting_writers > 0:
                self._cv.wait()
            self.readers += 1

    def release_read(self) -> None:
        with self._cv:
            self.readers -= 1
            if self.readers == 0:
                self._cv.notify_all()

    def acquire_write(self) -> None:
        with self._cv:
            self.waiting_writers += 1
            try:
                while self.writer or self.readers > 0:
                    self._cv.wait()
            finally:
                self.waiting_writers -= 1
            self.writer = True

    def release_write(self) -> None:
        with self._cv:
            self.writer = False
            self._cv.notify_all()


# ---------------------------------------------------------------------------
# Part 5: a minimal thread pool with Future
# ---------------------------------------------------------------------------
class Future:
    """A Future is a one-shot result box: Event for completion + stored value or
    exception. result(timeout) re-raises the worker's exception in the caller."""

    def __init__(self) -> None:
        self._done = threading.Event()
        self._result: Any = None
        self._exc: Optional[BaseException] = None

    def set_result(self, value: Any) -> None:
        self._result = value
        self._done.set()

    def set_exception(self, exc: BaseException) -> None:
        self._exc = exc
        self._done.set()

    def done(self) -> bool:
        return self._done.is_set()

    def result(self, timeout: Optional[float] = None) -> Any:
        if not self._done.wait(timeout):
            raise TimeoutError("future not done")
        if self._exc is not None:
            raise self._exc
        return self._result


class SimpleThreadPool:
    """N daemon workers pull (fn, args, future) from a queue.Queue (already
    thread-safe: it is a Condition-based blocking queue like Part 2). shutdown()
    pushes one sentinel per worker so each exits exactly once, then joins.
    Same shape as concurrent.futures.ThreadPoolExecutor, which additionally
    spawns workers lazily, supports map(), cancellation, and context manager."""

    _SENTINEL = object()

    def __init__(self, workers: int) -> None:
        self._q: "queue.Queue[Any]" = queue.Queue()
        self._threads = [threading.Thread(target=self._worker, daemon=True) for _ in range(workers)]
        for t in self._threads:
            t.start()

    def _worker(self) -> None:
        while True:
            job = self._q.get()
            if job is self._SENTINEL:
                return
            fn, args, fut = job
            try:
                fut.set_result(fn(*args))
            except BaseException as e:  # noqa: BLE001 - must not kill the worker
                fut.set_exception(e)

    def submit(self, fn: Callable[..., Any], *args: Any) -> Future:
        fut = Future()
        self._q.put((fn, args, fut))
        return fut

    def shutdown(self) -> None:
        for _ in self._threads:
            self._q.put(self._SENTINEL)
        for t in self._threads:
            t.join()


# ---------------------------------------------------------------------------
# Part 6: dining philosophers - ordered lock acquisition
# ---------------------------------------------------------------------------
def dine(n_philosophers: int, rounds: int) -> List[int]:
    """Deadlock arises when everyone holds their left fork and waits for the right
    (circular wait). Fix: impose a global order on the forks and always acquire
    the lower-numbered fork first. Then no cycle can form in the wait-for graph
    (the philosopher holding the highest-numbered fork can always proceed).
    Returns per-philosopher meal counts; the test asserts each ate `rounds`
    and that no two neighbours ever ate simultaneously."""
    forks = [threading.Lock() for _ in range(n_philosophers)]
    meals = [0] * n_philosophers
    eating = [False] * n_philosophers
    violations = [0]
    state_lock = threading.Lock()

    def philosopher(i: int) -> None:
        left, right = i, (i + 1) % n_philosophers
        first, second = min(left, right), max(left, right)   # the whole fix
        for _ in range(rounds):
            with forks[first]:
                with forks[second]:
                    with state_lock:
                        if eating[left] or eating[right] or eating[(i - 1) % n_philosophers] or eating[(i + 1) % n_philosophers]:
                            violations[0] += 1
                        eating[i] = True
                    meals[i] += 1
                    with state_lock:
                        eating[i] = False

    ts = [threading.Thread(target=philosopher, args=(i,)) for i in range(n_philosophers)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=10)
    assert all(not t.is_alive() for t in ts), "deadlock: a philosopher never finished"
    assert violations[0] == 0
    return meals


# ---------------------------------------------------------------------------
# Part 7b: asyncio producer / consumer
# ---------------------------------------------------------------------------
async def async_producer_consumer(n_items: int, n_consumers: int, capacity: int) -> List[int]:
    """asyncio.Queue is NOT thread-safe; it is for coroutines on one event loop.
    await q.put() suspends when full; q.get() suspends when empty. One sentinel
    per consumer ends them, like the thread-pool shutdown. No locks needed:
    coroutines only switch at `await`, so there is no data race on `out`."""
    q: "asyncio.Queue[Optional[int]]" = asyncio.Queue(maxsize=capacity)
    out: List[int] = []

    async def producer() -> None:
        for i in range(n_items):
            await q.put(i)
        for _ in range(n_consumers):
            await q.put(None)

    async def consumer() -> None:
        while True:
            item = await q.get()
            if item is None:
                return
            out.append(item * item)

    await asyncio.gather(producer(), *[consumer() for _ in range(n_consumers)])
    return out


# ---------------------------------------------------------------------------
# Part 7: discussion
# ---------------------------------------------------------------------------
# GIL: CPython has one Global Interpreter Lock; only one thread runs Python
#   bytecode at a time. Threads still help for I/O-bound work (the GIL is
#   released while blocking in socket/file/sleep, and in many C extensions),
#   but CPU-bound threads run serially and even slow down (lock contention).
#   Fixes: multiprocessing / ProcessPoolExecutor (separate interpreters, no
#   shared GIL, pay IPC/pickling), C extensions that release the GIL (numpy),
#   or asyncio for I/O concurrency with a single thread. (3.13+ has an
#   experimental free-threaded build.)
# Process vs thread: a process has its own address space, file table, and
#   crash isolation (one segfault kills only it); threads share the heap of
#   their process (cheap to create, cheap to communicate, but a bug in one
#   corrupts all). The scheduling unit of the OS kernel is the thread; a
#   process is a resource container. Context switch between threads of the
#   same process is cheaper (no page-table / TLB flush).
# Deadlock's four necessary conditions (Coffman): mutual exclusion, hold and
#   wait, no preemption, circular wait. Break any one: global lock ordering
#   (kills circular wait: Part 6), acquire all-or-nothing with try-lock +
#   backoff (kills hold-and-wait: lock.acquire(blocking=False)), timeouts
#   (lock.acquire(timeout=...)), or a lock hierarchy / single coarse lock.
#   Detection: wait-for graph cycle (databases do this and abort a victim).
# RLock: reentrant; the same thread may acquire it multiple times and must
#   release the same number of times. Use when a locked method calls another
#   locked method of the same object. A plain Lock would self-deadlock. RLock
#   is slightly slower and hides design smells; prefer private unlocked
#   helpers called from one locking entry point.
# Java `synchronized`: a monitor on an object (or class); mutual exclusion +
#   happens-before (memory visibility) at monitor exit/enter; reentrant.
#   `volatile`: no mutual exclusion; guarantees visibility (reads see the
#   latest write, no CPU/JIT reordering across it) - fine for a flag or a
#   single reference publish, NOT for i++ (still read-modify-write; use
#   AtomicInteger, which is CAS-based). ReentrantLock = explicit lock with
#   tryLock/timeouts/fairness/conditions; `synchronized` is simpler and JIT
#   optimised (biased/lightweight locking).
# asyncio vs threads: coroutines are cooperative (switch only at await), one
#   thread, no GIL contention, tens of thousands of connections; blocking calls
#   freeze the loop (use run_in_executor). Threads are preemptive; good for
#   blocking libraries; each ~8MB stack reservation.


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


# INTERVIEWER FOLLOW-UPS
# Q: Why `while` instead of `if` around Condition.wait()?
#    A: notify_all wakes everyone; another thread may consume the item first,
#       and spurious wakeups exist; re-check the predicate after every wake.
# Q: Why two Conditions on one Lock in the bounded queue?
#    A: So put() only wakes consumers and get() only wakes producers; with one
#       Condition you must notify_all and waste wakeups (still correct).
# Q: Is `n += 1` atomic in CPython thanks to the GIL?
#    A: No. The GIL serialises bytecodes; += is LOAD/ADD/STORE, and a switch
#       can happen between them. list.append / dict set are single bytecodes
#       into C code and are atomic in practice, but don't rely on it.
# Q: How would you make the thread pool cancellable / shut down gracefully?
#    A: Future.cancel sets a flag checked before running; shutdown(wait=True)
#       drains the queue then sends sentinels; use daemon threads so an
#       abandoned pool doesn't block interpreter exit.
# Q: Reader-writer lock: how to avoid starving readers?
#    A: Fair variant: FIFO of waiters (ticket lock) - a reader queued before a
#       writer proceeds first; or batch readers between writers.
