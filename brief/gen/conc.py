import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

INTRO = """By the end of this track you can read concurrent Java and Kotlin code and say what can go wrong: which line races, which pair of locks can freeze each other, which wait can hang forever, and which test proves nothing. You can fix each problem with the smallest tool that works: one atomic library call, a lock around the whole job, a concurrent collection, a synchronizer, or no sharing at all. And you can show that the fix holds, with a test that makes threads collide, and find the cause of a hang or a slowdown with thread dumps and Java Flight Recorder.

You need everyday Java or Kotlin and nothing else. The track starts with what a thread is and adds one idea per lesson, each tried on a program you can picture: a shop adding up a year of sales, a mail-room helper that sends letters from a tray, a bank moving money between accounts, a kitchen where waiters pass orders to cooks on a rail, and a slow web service that takes 120 ms to answer. The memory model track comes next and explains why the visibility rules you use here work.

Every lesson has a lab in `labs/concurrency`, in the package `workbench.concurrency.lNN`. From `labs/`, run `./gradlew :concurrency:test --tests 'workbench.concurrency.lNN.*'`: the tests fail on the starting code and pass when your fix is right. Reference answers are in `src/solution`, and `./gradlew :concurrency:solutionTest` runs the same tests against them. The Try-it programs are in `src/demo`, in Java and Kotlin, and run with `./gradlew :concurrency:demo -Pmain=<class>`. The labs compile for JDK 21 and run on 21 or later; install JDK 25."""

J_LOCK = """lock.lock();                       // before the try
try {
    balance -= cents;
} finally {
    lock.unlock();                 // first line of finally
}"""
K_LOCK = """lock.withLock {                    // lock, try, finally unlock
    balance -= cents
}"""
J_WAIT = """synchronized (lock) {
    while (items.isEmpty()) lock.wait();   // a while, never an if
    return items.removeFirst();
}"""
K_WAIT = """lock.withLock {                            // ReentrantLock + Condition: Any has no wait()
    while (items.isEmpty()) notEmpty.await()
    items.removeFirst()
}"""
J_CAS = """long prev;
do {
    prev = max.get();
    if (amount <= prev) return;               // decide on what you read
} while (!max.compareAndSet(prev, amount));   // write only if nobody changed it"""
K_CAS = """var prev: Long
do {
    prev = max.get()
    if (amount <= prev) return                // decide on what you read
} while (!max.compareAndSet(prev, amount))    // write only if nobody changed it"""
J_TL = """USER.set(request.user());
try {
    handle(request);
} finally {
    USER.remove();                 // pool threads are reused
}"""
K_TL = """USER.set(request.user)
try {
    handle(request)
} finally {
    USER.remove()                  // pool threads are reused
}"""

CHEAT = """## Threads

| Call | What it does |
|---|---|
| `t.start()` | runs `t` on a new thread; `t.run()` runs it on the current one |
| `t.join()` | waits for `t` to end; everything `t` wrote is visible afterwards |
| `t.interrupt()` | asks `t` to stop; blocking calls throw `InterruptedException` and clear the flag |
| `setDaemon(true)` | the JVM may exit while this thread still runs |
| `Thread.stop()` | removed in JDK 26; cancellation is cooperative |

When you catch `InterruptedException`: rethrow it, or restore the flag with `Thread.currentThread().interrupt()` and stop.

## The two shapes of race

| Shape | Looks like | Fix |
|---|---|---|
| Read-modify-write | `count++`, `balance -= x`, `put(k, get(k) + 1)` | an atomic call, or a lock around read and write |
| Check-then-act | `if (!map.containsKey(k)) map.put(k, v)`, setting something up on first use | one call that checks and acts: `putIfAbsent`, `computeIfAbsent`, `Set.add`, a compare-and-set |

A thread-safe class makes single calls atomic, never two calls in a row.

## Pick the tool

| You need | Use | Picture it |
|---|---|---|
| A busy counter, read now and then | `LongAdder` | visits to a web page |
| One exact value with read-modify-write | `AtomicLong`: `updateAndGet`, `accumulateAndGet`, or a compare-and-set loop | the largest sale so far |
| Several fields that change together | one lock around both, or an `AtomicReference` to an immutable record | a balance and the time it last changed |
| A per-key update in a shared map | `ConcurrentHashMap.merge`, `compute`, `computeIfAbsent` | sales per item |
| A table replaced as a whole | a `volatile` field holding an immutable map | a new price board hung up in one move |
| Read-mostly data updated in place | `ReentrantReadWriteLock` (never upgrade read to write) | many readers, one person changing the board |
| A wait that can time out or be cancelled | `ReentrantLock.tryLock(timeout)`, `lockInterruptibly()` | a transfer that gives up instead of freezing |
| Two kinds of waiting threads on one lock | one `Condition` each, then `signal()` is enough | waiters wait for room, cooks for tickets |
| Hand work to other threads | a bounded `BlockingQueue`, such as `ArrayBlockingQueue(n)` | the kitchen's order rail |
| Wait for N events, once | `CountDownLatch` | the shop opens when three lists have loaded |
| N threads meeting every round | `CyclicBarrier` | three tills total each day together |
| At most N at once | `Semaphore` | a car park with five spaces |
| A group that changes size between phases | `Phaser` | a stocktake helper who goes home early |
| A small list, rarely changed, often read in a loop | `CopyOnWriteArrayList` | the listeners of a price board |
| Per-request context | `ThreadLocal` with `remove()` in `finally`; `ScopedValue` on JDK 25+ | the user a request runs for |

## Idioms

An explicit lock:

""" + pair(J_LOCK, K_LOCK) + """

A guarded wait:

""" + pair(J_WAIT, K_WAIT) + """

A compare-and-set loop:

""" + pair(J_CAS, K_CAS) + """

A thread-local on a pool thread:

""" + pair(J_TL, K_TL) + """

`semaphore.acquire()` also goes before the `try`, and `tryAcquire`'s result must be checked: permits have no owner, so a stray `release()` adds one.

## Locks

- `synchronized` gives mutual exclusion and visibility, and is reentrant. Lock on a `private final` object, never on a boxed number or a `String` literal.
- Keep the locked code short. Never call alien code, code you don't control (listeners, callbacks, other services), while holding a lock.
- Every access to shared mutable state, reads included, goes through the same lock or atomic.

## Deadlock

| Condition | Remove it with |
|---|---|
| Mutual exclusion | immutable data, one owner per resource |
| Hold and wait | take one lock at a time, or `acquire(n)` in one step |
| No preemption | `tryLock(timeout)`, release and retry with a random back-off |
| Circular wait | one global lock order, such as lower id first |

Livelock: busy threads that make no progress (fix: randomness). Starvation: one thread never gets its turn (fix: fairness, shorter holds).

## Concurrent collections

- `ConcurrentHashMap`: no null keys or values; compute functions run under the bin's lock, so keep them short and never touch the map inside one; `size()` is an estimate; iterators never throw.
- `ConcurrentModificationException` is a fail-fast iterator check. One thread can trip it; concurrent collections never throw it.
- `new LinkedBlockingQueue<>()` is unbounded. Always pass a capacity.

| BlockingQueue | Throws | Special value | Blocks | Times out |
|---|---|---|---|---|
| Insert | `add` | `offer` | `put` | `offer(e, t, unit)` |
| Remove | `remove` | `poll` | `take` | `poll(t, unit)` |

Shut consumers down with one poison pill each, after every producer has finished, compared by identity.

## Kotlin differences

| Java | Kotlin |
|---|---|
| `synchronized` method | `@Synchronized` |
| `synchronized (lock) { }` | `synchronized(lock) { }`, a standard library function |
| `volatile` | `@Volatile` |
| `lock(); try { } finally { unlock(); }` | `lock.withLock { }` |
| read and write locks | `rw.read { }`, `rw.write { }`: `write` releases read locks first, so re-check |
| `new Thread(r).start()` | `thread { }` |
| `wait()` / `notify()` on any object | `Any` has neither: use `ReentrantLock` and `Condition` |
| checked `InterruptedException` | not checked, but you still restore the flag |
| `computeIfAbsent` | `getOrPut` on a `ConcurrentMap` may run its default more than once |

## Testing and diagnosis

- Stress tests: a start latch, more threads than cores, many operations, many rounds, an invariant after `join()`, and a timeout on every test. A pass is not a proof.
- No `Thread.sleep` to wait in tests: use a latch, a future, or polling with a deadline.
- jcstress: `ACCEPTABLE`, `ACCEPTABLE_INTERESTING` (allowed, worth seeing), `FORBIDDEN` (fails the test).

| Command | Shows |
|---|---|
| `jcmd <pid> Thread.print -l` | every thread's state and stack, the `java.util.concurrent` locks each one owns, Java-level deadlocks |
| `jcmd <pid> Thread.dump_to_file -format=json f.json` | the same as JSON; state and lock fields from JDK 25 |
| `jcmd <pid> JFR.start duration=60s filename=r.jfr` | starts a flight recording |
| `jfr print --events jdk.JavaMonitorEnter r.jfr` | waits for `synchronized`, with duration and previous owner |

In a dump, `BLOCKED` means waiting for a monitor; `WAITING (parking)` means a `java.util.concurrent` lock, latch, queue or semaphore. Take several dumps a few seconds apart to tell stuck from busy."""

RECAP = [
 "A race condition is a result that depends on timing. Its two shapes are read-modify-write and check-then-act, and both need the whole compound action made atomic.",
 "A race needs state that is shared and changing. Reach for fixes in this order: don't share (immutability, confinement, hand-off), then one atomic library call, then a lock around the whole compound action, reads included.",
 "`synchronized` and `ReentrantLock` give one thread at a time and visibility. Release explicit locks in `finally`, lock on private objects, keep locked code short and never call alien code inside it.",
 "Waiting for a condition is always `while (!condition) wait()` or `await()`. Use `notifyAll()` with one wait set, or one `Condition` per kind of waiting thread.",
 "Deadlock needs all four Coffman conditions. A global lock order removes circular wait; `tryLock` with a random back-off removes no preemption. `jcmd Thread.print` finds monitor and `ReentrantLock` cycles.",
 "Atomics are compare-and-set underneath: read, decide, compare-and-set, retry. `LongAdder` for busy counters, `AtomicLong` for decisions, `AtomicReference` plus an immutable object for several fields.",
 "Concurrent collections make single calls safe. Use their atomic per-key methods, bound every queue, and don't read `size()` or an iteration as a snapshot.",
 "Latches wait for events once, barriers meet every round, semaphores cap how many run at once, phasers change size. Count down and release in `finally`, and give every wait a deadline.",
 "`ThreadLocal` values outlive the request on pool threads: remove them in `finally`, or use scoped values on JDK 25+. Stop consumers with one poison pill each, after the last producer.",
 "A concurrency test must make threads collide and check invariants with a timeout. Find hangs with thread dumps and lock waits with JFR."
]

QUIZ = [
 {"q": "What does this print?\n\n```java\nThread t = new Thread(() -> System.out.println(Thread.currentThread().getName()), \"mail-room\");\nt.run();\n```\n\n```kotlin\nval t = Thread({ println(Thread.currentThread().name) }, \"mail-room\")\nt.run()\n```",
  "options": ["mail-room", "main", "Nothing: a thread must be started first", "It throws `IllegalThreadStateException`"],
  "answer": 1, "why": "`run()` is an ordinary method call, so the lambda runs on the calling thread, `main`. Only `start()` creates a new thread that then calls `run()`. Calling `run()` by mistake is a classic way to make concurrent code quietly single-threaded."},
 {"q": "A worker loops `while (true) { try { send(queue.take()); } catch (InterruptedException e) { log.warn(\"interrupted\", e); } }`. At shutdown, the thread pool's `shutdownNow()`, which interrupts its threads, doesn't stop it. Why?",
  "options": ["`shutdownNow()` never interrupts threads", "`take()` ignores interrupts", "The exception clears the interrupt flag, the catch only logs it, and the loop carries on", "The worker must be a daemon thread"],
  "answer": 2, "why": "`take()` throws `InterruptedException` and clears the flag. Logging isn't handling: the loop goes round and waits again. Restore the flag with `Thread.currentThread().interrupt()` and leave the loop, or let the exception travel up to the caller."},
 {"q": "Four threads record a bank's incoming payments with `if (!seen.contains(id)) { credit(p); seen.add(id); }`, where `seen = ConcurrentHashMap.newKeySet()`. The same payment arrives on two threads at once. What is the smallest correct fix?",
  "options": ["`if (seen.add(id)) credit(p);`, removing the id again if the credit fails", "Make `seen` a `volatile` field", "Switch to `Collections.synchronizedSet`", "Add `Thread.sleep(10)` before the check"],
  "answer": 0, "why": "It's check-then-act: both threads can pass `contains` before either adds. `Set.add` checks and inserts in one atomic step and returns `false` to the thread that lost. `volatile` and a synchronized wrapper leave the gap between the two calls."},
 {"q": "Two unrelated classes each declare `private static final Integer LOCK = 0;` and use `synchronized (LOCK)`. What happens?",
  "options": ["Each class gets its own lock, because the fields are private", "It doesn't compile", "The JVM copies the lock for each class", "Both share one lock object, because boxing 0 returns the cached `Integer`; javac warns about synchronizing on a value-based class"],
  "answer": 3, "why": "`Integer.valueOf(0)` comes from a cache shared by the whole JVM, so both fields point to the same object, and unrelated code waits for, or deadlocks over, one monitor. Lock on a `private final Object lock = new Object()` instead."},
 {"q": "A cook does `synchronized (rail) { if (rail.isEmpty()) rail.wait(); return rail.remove(); }`, with two cooks and `notifyAll()`. What can go wrong?",
  "options": ["Nothing: `notifyAll()` makes `if` safe", "A woken cook can find the rail empty again, because the other cook took the ticket or the wake-up was spurious, and `remove()` throws", "`wait()` keeps the monitor, so the waiter can never add a ticket", "`notifyAll()` wakes only one cook"],
  "answer": 1, "why": "Waking up only means \"something may have changed\". The other cook can get the monitor first and take the ticket, and the JVM allows spurious wake-ups, ones with no notify at all. Check again in a `while` loop."},
 {"q": "`transfer(from, to)` locks `from`, then `to`. Transfers run in both directions between the same two bank accounts, and the program sometimes freezes. Which fix removes the deadlock?",
  "options": ["Make the balance fields `volatile`", "Use fair locks", "Always lock the account with the lower id first, whichever way the money moves", "Add a short sleep between the two locks"],
  "answer": 2, "why": "Opposite orders make a cycle: each thread holds one account and waits for the other. With one global order, nobody can hold the second lock while waiting for the first, so circular wait is gone. Fairness and sleeps only change the odds."},
 {"q": "Fifty threads update an account's `balanceCents` and `lastUpdated` together, and readers must never see one without the other. Which design is correct?",
  "options": ["One `AtomicReference` to an immutable record holding both, updated with `updateAndGet`, or one lock around both", "Two `AtomicLong` fields", "Two `volatile` fields", "A `LongAdder` for the balance and an `AtomicLong` for the time"],
  "answer": 0, "why": "Each atomic protects one variable, so with two of them a reader can see the new balance with the old time. A compare-and-set on a reference to an immutable pair, or a single lock, makes both fields change as one step."},
 {"q": "A test checks a counter with 2 threads x 1,000 increments and has passed for a year. Which version of the test could actually catch a lost update?",
  "options": ["The same test with `@RepeatedTest(100)`", "The same test run on a faster machine", "The same test with `Thread.sleep(100)` before the assertion", "8 threads released together by a start latch, 100,000 increments each, over many rounds, with a timeout"],
  "answer": 3, "why": "With 1,000 increments the first thread often finishes before the second starts, so repeating the same test repeats the same lack of overlap. A start latch, more threads than cores, long runs and many rounds make the threads collide. The timeout keeps a deadlock from hanging the whole test run."},
 {"q": "The shop's gate in front of the bank's card service does `try { permits.acquire(); return bank.check(p); } finally { permits.release(); }` with `new Semaphore(20)`. Payments are often cancelled while they wait for a permit. What happens over a day?",
  "options": ["Nothing: `acquire()` gives up cleanly", "Each interrupted wait still releases a permit it never took, so the limit drifts above 20", "`release()` throws once permits pass 20", "The semaphore resets itself every hour"],
  "answer": 1, "why": "`acquire()` throws `InterruptedException` inside the `try`, so the `finally` runs `release()` anyway. Permits have no owner, so each stray release adds one for good. Call `acquire()` before the `try`."},
 {"q": "A web service's handler calls `USER.set(request.user())` on a `ThreadLocal` only when the request carries a user, and never removes it. What does a request without a user see on a reused pool thread?",
  "options": ["`null`, because each request gets a new thread", "It throws `IllegalStateException`", "The user of whichever request that thread served last", "A random user from another thread"],
  "answer": 2, "why": "Pool threads are reused, and a thread-local value stays on the thread until someone removes it. Set it, then `remove()` in `finally`, or use a scoped value on JDK 25 and later."}
]

T = {"id": "conc", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/conc.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
