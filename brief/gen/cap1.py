import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """In three sittings you build one working program: an in-memory payment ledger that applies transfers from many threads, never loses or creates money, never deadlocks, shuts down without dropping an accepted transfer, publishes balances that always add up, and serves 10,000 concurrent requests on virtual threads while a slow fraud service is held behind a bulkhead and a deadline. At the end you defend the design in a review, and you know which earlier lesson's mechanism decides each line of it.

The capstone draws on every track of Part 1. Lesson 1 uses races, deadlock and lock ordering, immutability and stress testing from *Threads and the bugs they cause*. Lesson 2 uses `ThreadPoolExecutor`, Little's law and production shutdown from *Thread pools and executors*, and happens-before and safe publication from *The Java Memory Model*. Lesson 3 uses one-thread-per-request, semaphores, pinning and fail-fast scopes from *Virtual threads*. There is little new theory: each section shows what breaks if you choose differently, then names the earlier lesson that explains why.

The lab lives in `labs/ledger`, one package per lesson (`workbench.ledger.l01` to `l03`). Each lesson's starter code contains the previous lesson's solution, so you can start any sitting fresh. Lessons 1 and 2 are in Java; lesson 3 adds a Kotlin server on top of the same Java ledger, the way a Kotlin service calls a Java library. Run `./gradlew :ledger:test --tests 'workbench.ledger.lNN.*'` from `labs/` until it passes; `solutionTest` runs the same tests against the reference answers. The tests check what production cares about (invariants under 8 threads, no lost transfer on shutdown, a bulkhead that holds at 10,000 requests), never timings. The Try-it demos run with `./gradlew :ledger:demo -Pmain=...`, and two of them hang on purpose so you can read a thread dump: install JDK 25, and keep `jcmd` and `jq` at hand."""

CHEATSHEET = """## The invariants, and what protects each

| Invariant | Protected by | How the tests check it |
|---|---|---|
| Money is conserved: the sum of balances never changes | debit and credit in one critical section holding both account locks | total after 8 threads x 100,000 transfers; snapshots taken while transfers run |
| No balance below zero | the balance check inside the same locks; `debit` refuses an overdraft | no negative balance, and `debit` throws at the moment a race would overdraw |
| A transfer is whole or not at all | one critical section; journal first, apply second, nothing blocking inside `apply` | an interrupted transfer leaves every balance unchanged |
| No deadlock | every multi-lock path locks in account id order | opposite transfers, 2 threads x 100,000, under a timeout |
| No accepted transfer vanishes | drain on shutdown; `shutdownNow()`'s list cancelled and handed back | every accepted future done; queued transfers returned by id |

## Every limit, and where its number comes from

| Limit | Value in the labs | Source |
|---|---|---|
| ledger pool threads | 8 | Little's law: 1,600 transfers/s x 5 ms journal write |
| ledger queue slots | 80 | 1,600/s x 50 ms longest acceptable wait |
| rejection | count, then throw: 503 + Retry-After | money is never discarded; the client retries with the same id |
| fraud bulkhead | 20 permits, shared | the fraud vendor's concurrency limit; 20 / 0.02 s = 1,000 checks/s |
| request deadline | 300 ms for all screening | the latency you promise; every wait uses what is left |
| stand-in limit | 50.00 | a risk decision: small amounts go through unchecked at the deadline |
| request threads | one new virtual thread each | unlimited on purpose: the limits above are on resources |

## The happens-before edge for every shared field

| Field | Edge |
|---|---|
| `Account.balance` | the account's `ReentrantLock` |
| `Ledger.accounts`, `inLockOrder` | final fields set in the constructor |
| `Ledger.version` | written only while every account lock is held |
| `Ledger.latest` | volatile write, then volatile read |
| `BalanceSnapshot` contents | final record fields; `Map.copyOf` |
| `Transfer` | immutable; `execute` happens-before the task runs |
| a transfer's outcome | task completion happens-before `Future.get()` returns |
| per-thread stress counts | `join()` |

## The four decisive pieces of code

```java
// 1. two accounts, one global order
Account first = from.id().compareTo(to.id()) < 0 ? from : to, second = first == from ? to : from;
first.lock().lock();
try {
    second.lock().lock();
    try {
        if (from.balance() < cents) return Outcome.INSUFFICIENT_FUNDS;   // check inside the locks
        from.debit(cents);
        to.credit(cents);
        return Outcome.APPLIED;
    } finally { second.lock().unlock(); }
} finally { first.lock().unlock(); }
```

```kotlin
// 1. two accounts, one global order
val first = if (from.id < to.id) from else to
val second = if (first === from) to else from
return first.lock.withLock {
    second.lock.withLock {
        if (from.balance < cents) return Outcome.INSUFFICIENT_FUNDS     // check inside the locks
        from.debit(cents)
        to.credit(cents)
        Outcome.APPLIED
    }
}
```

```java
// 2. shutdown that accounts for every transfer
pool.shutdown();
if (!pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)) {
    for (Runnable r : pool.shutdownNow()) {
        TransferTask task = (TransferTask) r;
        task.cancel(false);                       // wake waiting callers
        neverStarted.add(task.transfer());        // log or replay
    }
}
```

```kotlin
// 2. shutdown that accounts for every transfer
pool.shutdown()
if (!pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)) {
    for (r in pool.shutdownNow()) {
        val task = r as TransferTask
        task.cancel(false)                        // wake waiting callers
        neverStarted += task.transfer             // log or replay
    }
}
```

```java
// 3. a snapshot nobody can tear
for (Account a : inLockOrder) a.lock().lock();             // every lock, in id order
try {
    Map<String, Long> copy = new HashMap<>();
    long total = 0;
    for (Account a : inLockOrder) { copy.put(a.id(), a.balance()); total += a.balance(); }
    latest = new BalanceSnapshot(copy, total, ++version);       // volatile write, still locked
} finally {
    for (int i = inLockOrder.size() - 1; i >= 0; i--) inLockOrder.get(i).lock().unlock();
}
```

```kotlin
// 3. a snapshot nobody can tear
inLockOrder.forEach { it.lock.lock() }                       // every lock, in id order
try {
    val copy = inLockOrder.associate { it.id to it.balance }
    latest = BalanceSnapshot(copy, copy.values.sum(), ++version)  // @Volatile write, still locked
} finally {
    inLockOrder.asReversed().forEach { it.lock.unlock() }
}
```

```kotlin
// 4. screening: one deadline, a bulkhead, fail-fast, a fallback
val deadline = System.nanoTime() + budget.toNanos()
val perTask = Executors.newVirtualThreadPerTaskExecutor()
try {
    val done = ExecutorCompletionService<Boolean>(perTask)
    done.submit { bulkhead.call(deadline - System.nanoTime()) { fraud.passes(t) } }
    done.submit { limits.passes(t) }
    repeat(2) {
        val next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS) ?: return fallback(t)
        val ok = try { next.get() } catch (e: ExecutionException) {
            if (e.cause is TimeoutException) return fallback(t) else false
        }
        if (!ok) return Verdict.DECLINED
    }
    return Verdict.APPROVED
} finally {
    perTask.shutdownNow()                         // interrupt what still runs
    perTask.close()                               // and wait for those threads
}
```

```java
// 4. screening: one deadline, a bulkhead, fail-fast, a fallback
long deadline = System.nanoTime() + budget.toNanos();
ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();
try {
    CompletionService<Boolean> done = new ExecutorCompletionService<>(perTask);
    done.submit(() -> bulkhead.call(deadline - System.nanoTime(), () -> fraud.passes(t)));
    done.submit(() -> limits.passes(t));
    for (int i = 0; i < 2; i++) {
        Future<Boolean> next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
        if (next == null) return fallback(t);
        try {
            if (!next.get()) return Verdict.DECLINED;
        } catch (ExecutionException e) {
            return e.getCause() instanceof TimeoutException ? fallback(t) : Verdict.DECLINED;
        }
    }
    return Verdict.APPROVED;
} finally {
    perTask.shutdownNow();                        // interrupt what still runs
    perTask.close();                              // and wait for those threads
}
```

## Design checklist

1. Write the invariants down before the code, and name the lock or edge that protects each.
2. Make the values that cross threads immutable, and validate them in the constructor.
3. Lock several accounts only in one global id order; sort them when there are more than two.
4. Keep the check inside the critical section that acts on it.
5. Never block inside an account lock: journal, fraud calls and logging happen outside.
6. Size pools and queues with Little's law, then check the downstream's own limit.
7. Bound every queue; choose the rejection policy on purpose and count rejections.
8. Shut down in order, with one deadline, and hand back what never ran.
9. One new virtual thread per request; a shared semaphore per slow dependency.
10. One deadline per request; cancel what you stop waiting for; a fallback that is a business rule.
11. Fail fast in fan-outs, and let no subtask outlive its request.
12. Test invariants under collision, with latches and counts, never with timings.

## Diagnostics

| Question | Command |
|---|---|
| Which pool is stuck, and on what? | `jcmd <pid> Thread.print -l`: named threads, state, `parking to wait for`, `Locked ownable synchronizers` |
| Is it a lock cycle? | the same dump ends with `Found one Java-level deadlock` if it is |
| Where are 10,000 virtual threads? | `jcmd <pid> Thread.dump_to_file -format=json /tmp/t.json` (add `-overwrite` to replace a file) |
| How are they spread? | `jq` per container, then group stacks by the first frame of your code and `uniq -c` |
| Is anything pinned? | JFR event `jdk.VirtualThreadPinned` (20 ms threshold by default) |

Versions: virtual threads final in JDK 21 (JEP 444); `synchronized` stops pinning in JDK 24 (JEP 491), first LTS JDK 25; JSON dumps carry `state` and `virtual` from JDK 25; `StructuredTaskScope` is preview in JDK 25 to 27 and final in JDK 28 (JEP 543)."""

RECAP = [
 "Start from invariants: money is conserved, no balance goes below zero, a transfer is whole or not at all. Every lock and edge in the program protects one of them.",
 "Per-account `ReentrantLock`s taken in one global id order give parallel transfers without deadlock; the balance check lives inside the same critical section as the move.",
 "A transfer is an immutable, validated value, so any thread can see it whole; a reused mutable object handed to a pool delivers the wrong data.",
 "Stress tests collide threads behind a start latch and check every invariant, at the end and at the point where it can break. A pass is evidence, not proof.",
 "The ledger pool is sized by Little's law (8 threads, 80 slots), bounded, named, and rejects by counting and throwing; overflow becomes a visible 503, never a lost transfer.",
 "Shutdown drains within a deadline, then cancels and hands back what never started; the journal is written before `apply`, so an interrupt never leaves half a transfer.",
 "A consistent snapshot holds every account lock in order, copies, and publishes an immutable record through a volatile field; readers never lock.",
 "Requests run on one new virtual thread each, behind written-down limits: a shared fraud semaphore, the bounded ledger pool, and one deadline per request with a stand-in fallback.",
 "Fail-fast screening takes results in completion order and ends with `shutdownNow()` and `close()`, so no call outlives its request or keeps a permit.",
 "Thread dumps find what tests can't: a pool parked on its own futures in `Thread.print -l`, and 10,000 virtual threads grouped by container and stack in the JSON dump."
]

QUIZ = [
 {"q": "Two transfers run at once: acc-07 to acc-03, and acc-03 to acc-07. With the ledger's lock order, which lock does each take first?",
  "options": ["Each takes its `from` account first", "Both take acc-03 first", "Both take acc-07 first", "Whichever thread starts first decides"],
  "answer": 1,
  "why": "The order is by id, whatever direction the money moves, so both lock acc-03 first. The second thread waits while holding nothing, which is contention, not deadlock. \"`from` first\" is the order that deadlocks.",
  "from": "cap1-01"},
 {"q": "A stress test of a ledger that checks the balance before taking the locks reports total 500,000 and no negative balances at the end. Why did it miss the bug?",
  "options": ["The race can't happen on x86", "Accounts went negative during the run and later credits topped them up before the final check",
              "The JIT removed the check", "Eight threads are too few to cause a race"],
  "answer": 1,
  "why": "Each move was still atomic, so the total held, and the overdrafts healed before the end. Check an invariant where it can break as well: `debit` refusing an overdraft turns the race into an immediate failure.",
  "from": "cap1-01"},
 {"q": "Peak traffic is 3,000 transfers a second and the journal write takes 4 ms. The storage allows 10 concurrent writes. What should the ledger pool's thread count be?",
  "options": ["12, from Little's law", "10: the journal's limit is lower than what Little's law asks for", "3,000", "As many as the machine has cores"],
  "answer": 1,
  "why": "Little's law asks for 3,000 x 0.004 = 12, but the journal handles 10 at once, so the 11th and 12th threads would only queue inside it. Size from the scarce resource: 10 threads give at most 10 / 0.004 = 2,500 a second, and the counting rejection handles the rest.",
  "from": "cap1-02"},
 {"q": "Which rejection policy may silently lose a transfer that a caller was told was accepted?",
  "options": ["A counting policy that throws", "`CallerRunsPolicy`", "`DiscardOldestPolicy`", "`AbortPolicy`"],
  "answer": 2,
  "why": "`DiscardOldestPolicy` drops the oldest queued task, which a caller already holds a future for, and that future never completes. A throwing policy rejects the new transfer before anyone is told it was accepted, and `CallerRunsPolicy` runs it on the submitter.",
  "from": "cap1-02"},
 {"q": "A balances endpoint adds up the accounts one at a time, locking each account while it reads it. Transfers keep running. What can it report?",
  "options": ["Always the exact total, because every read holds a lock", "A total that is too high or too low, because a transfer can run between two reads",
              "An exception, because two locks are taken", "A total that is always too low"],
  "answer": 1,
  "why": "Money can move from an account not yet read to one already read (counted in neither) or the other way (counted twice). Only holding every lock at once, in the global order, gives one instant.",
  "from": "cap1-02"},
 {"q": "A thread dump shows every `ledger-` thread `WAITING (parking)` on a `FutureTask` inside your own `statement` method, and no deadlock report. What is wrong?",
  "options": ["A lock-order deadlock between two accounts", "Tasks waiting for other tasks queued in the same bounded pool",
              "The journal is slow", "The pool's threads are pinned"],
  "answer": 1,
  "why": "Workers parked on futures of their own pool, with tasks still queued, is pool-induced deadlock. There is no lock cycle, so the detector reports nothing. Do the work inline, compose instead of blocking, or use a separate pool.",
  "from": "cap1-02"},
 {"q": "Which design caps what the fraud service sees when 10,000 requests run on virtual threads?",
  "options": ["A fixed pool of 20 virtual threads for whole requests", "One `Semaphore(20)` field on the fraud client, shared by every request",
              "A `Semaphore(20)` created in each request handler", "`newVirtualThreadPerTaskExecutor()` alone"],
  "answer": 1,
  "why": "One shared semaphore limits only the fraud call. A pool of virtual threads caps the whole request, including the limits check and the ledger wait. A semaphore per handler limits nothing, and the per-task executor has no limit at all.",
  "from": "cap1-03"},
 {"q": "During a fraud outage each call takes 2 s. The request stops waiting at its 300 ms deadline but never cancels the call, and uses a shared executor. What happens to the bulkhead?",
  "options": ["Nothing: every request answers in 300 ms", "Its permits stay held by abandoned calls for 2 s each, so most new requests can't get one",
              "It grows to fit the extra calls", "The calls are interrupted automatically"],
  "answer": 1,
  "why": "A timeout ends the wait, not the work. Each orphaned call keeps its permit until the fraud service answers. Cancel the call at the deadline so its `finally` gives the permit back to the next request.",
  "from": "cap1-03"},
 {"q": "The ledger must run on JDK 21 and serve virtual threads. Why are the account locks `ReentrantLock`s?",
  "options": ["`synchronized` doesn't give visibility", "On JDK 21 a virtual thread waiting to enter or blocking inside `synchronized` pins its carrier; `ReentrantLock` parks and frees it",
              "`ReentrantLock` makes the critical section faster", "Kotlin can't use `synchronized`"],
  "answer": 1,
  "why": "JDK 24 (JEP 491) removed monitor pinning, but on JDK 21 to 23 contended or blocking `synchronized` code holds the carrier. `ReentrantLock` has always let a waiting virtual thread unmount. Either way, nothing slow belongs inside an account lock.",
  "from": "cap1-03"},
 {"q": "`jcmd <pid> Thread.print` on the server during an outage shows no request threads at all. Where are they?",
  "options": ["They have all finished", "They are parked virtual threads, which `Thread.print` doesn't list; `Thread.dump_to_file -format=json` does",
              "They are inside the carriers, under the name `ForkJoinPool-1-worker-N`", "They were garbage collected"],
  "answer": 1,
  "why": "A parked virtual thread is a stack on the heap, not an OS thread. `Thread.print` lists platform threads (plus mounted virtual threads from JDK 24). The JSON dump lists every thread, grouped by the container that started it.",
  "from": "cap1-03"}
]

# vary the correct answer index: rotate the right option into different slots
targets = [1, 0, 2, 3, 1, 0, 3, 2, 0, 3]
for q, target in zip(QUIZ, targets):
    right = q["options"][q["answer"]]
    rest = [o for i, o in enumerate(q["options"]) if i != q["answer"]]
    rest.insert(target, right)
    q["options"], q["answer"] = rest, target

T = {"id": "cap1", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/cap1.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
