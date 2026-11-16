import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """In three sittings, you build one working program: a ledger, the bank's book of accounts and of every movement of money between them. Many threads move money at once, and not one cent may be lost or created. By the end, the ledger never deadlocks, closes without dropping a transfer it accepted, shows balances that always add up, and serves 10,000 customers at once on virtual threads, while a slow outside safety service sits behind a shared limit and a deadline. Then you defend the design in a review, and you can name the earlier lesson behind each line of it.

The capstone draws on all of Part 1, and calls back its pictures as it goes. Lesson 1 uses the bank's races, the vault key, Ana and Ben's frozen transfers and the stress test from Threads and the bugs they cause, and the sealed envelope from The Java Memory Model. Lesson 2 uses the kitchen with its cooks and order rail, Little's law and closing time from Thread pools and executors, and the cashier's key and the OPEN/CLOSED sign from the memory model. Lesson 3 uses the order slips, the grill tokens and the hot pan from Virtual threads. There is little new theory. Each section shows what breaks if you choose differently, then names the lesson that explains why.

The lab lives in `labs/ledger`, one package per lesson (`workbench.ledger.l01` to `l03`). Each lesson's starter code contains the previous lesson's solution, so you can start any sitting fresh. Lessons 1 and 2 are in Java; lesson 3 adds a Kotlin server on top of the same Java ledger, the way a Kotlin program calls a Java library. From `labs/`, run `./gradlew :ledger:test --tests 'workbench.ledger.lNN.*'` until it passes; `solutionTest` runs the same tests against the reference answers. The tests check what a real bank cares about (the rules under 8 threads, no lost transfer at shutdown, a limit that holds at 10,000 requests), never timings. The Try-it demos run with `./gradlew :ledger:demo -Pmain=...`, and two of them get stuck on purpose so you can read a thread dump. Install JDK 25, and keep `jcmd` (it comes with the JDK) and `jq` (a small, free tool for reading JSON) at hand."""

CHEATSHEET = """## The three rules, and what protects each

| Rule | Protected by | How the tests check it |
|---|---|---|
| Money is conserved: the sum of balances never changes | debit and credit in one critical section that holds both account locks | the total after 8 threads x 100,000 transfers; snapshots taken while transfers run |
| No balance goes below zero | the balance check inside the same locks; `debit` refuses an overdraft | no negative balance, and `debit` throws at the moment a race would overdraw |
| A transfer is whole or not at all | one critical section; journal first, apply second, nothing that waits inside `apply` | an interrupted transfer leaves every balance unchanged |
| No deadlock | every path that takes several locks takes them in account id order | opposite transfers, 2 threads x 100,000, under a time limit |
| No accepted transfer vanishes | drain at shutdown; cancel what `shutdownNow()` returns and hand it back | every accepted future is done; queued transfers come back by id |

## The pictures behind the design

| Picture from Part 1 | What it became in the ledger |
|---|---|
| the vault key (synchronized and intrinsic locks) | one `ReentrantLock` per account, held for the debit, the credit and the check |
| Ana and Ben paying each other at once (Deadlock, livelock and starvation) | lower account id first, whichever way the money moves |
| the starting gun (Synchronizers) | a `CountDownLatch` start line in the stress test |
| the sealed envelope (Safe publication) | `Transfer` as a record, checked in its compact constructor |
| the cooks and the order rail (Why pools) | a `ThreadPoolExecutor` with 8 threads and 80 queue slots |
| closing the kitchen in order (Pools in production) | `shutdown`, wait, `shutdownNow`, cancel, hand back |
| the cashier's key and the OPEN/CLOSED sign (the memory model track) | account locks, and the `volatile` field `latest` that publishes snapshots |
| the printed price board (Don't share) | a `BalanceSnapshot` built whole, then swapped in with one write |
| cooks waiting for tickets behind them (Pools in production) | the statement job that waits on its own pool |
| order slips on the board (How virtual threads work) | one new virtual thread per request |
| the 20 grill tokens (Using virtual threads) | one shared `Semaphore(20)` in front of the safety service |
| the takeaway ticket and the kitchen timer (the executors track) | a timeout ends the wait, not the work, so interrupt the call |
| the head waiter who waits for every helper (Structured concurrency) | `screen`: answers in the order they finish, then `shutdownNow()` and `close()` |
| the hot pan (Pinning, ThreadLocals and other traps) | `ReentrantLock` instead of `synchronized` on JDK 21, and nothing slow under a lock |

## Every limit, and where its number comes from

| Limit | Value in the labs | Where the number comes from |
|---|---|---|
| ledger pool threads | 8 | Little's law: 1,600 transfers a second x 5 ms journal write |
| ledger queue slots | 80 | 1,600 a second x 50 ms, the longest wait we accept |
| rejection | count, then throw: a fast "busy, try again" (status 503 on the web) | money is never dropped; the customer tries again with the same id |
| safety bulkhead | 20 permits, shared by every request | what the safety service can take; 20 / 0.02 s = 1,000 checks a second |
| request deadline | 300 ms for all checks | the answer time you promise; every wait uses what is left |
| small-amount rule (stand-in) | 50.00 | a risk decision: at the deadline, small amounts go through unchecked |
| request threads | one new virtual thread each | unlimited on purpose: the limits above sit on resources |

## The happens-before rule for every shared field

| Field | Rule |
|---|---|
| `Account.balance` | the account's `ReentrantLock` |
| `Ledger.accounts`, `inLockOrder` | final fields set in the constructor |
| `Ledger.version` | written only while every account lock is held |
| `Ledger.latest` | volatile write, then volatile read |
| `BalanceSnapshot` contents | final record fields; `Map.copyOf` |
| `Transfer` | never changes; `execute` happens-before the task runs |
| a transfer's outcome | the task's end happens-before `Future.get()` returns |
| each stress thread's counts | `join()` |

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
// 2. a shutdown that accounts for every transfer
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
// 2. a shutdown that accounts for every transfer
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

```java
// 4. screening: one deadline, a bulkhead, fail fast, a fallback
long deadline = System.nanoTime() + budget.toNanos();
ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();
try {
    CompletionService<Boolean> done = new ExecutorCompletionService<>(perTask);
    done.submit(() -> bulkhead.call(deadline - System.nanoTime(), () -> safety.passes(t)));
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

```kotlin
// 4. screening: one deadline, a bulkhead, fail fast, a fallback
val deadline = System.nanoTime() + budget.toNanos()
val perTask = Executors.newVirtualThreadPerTaskExecutor()
try {
    val done = ExecutorCompletionService<Boolean>(perTask)
    done.submit { bulkhead.call(deadline - System.nanoTime()) { safety.passes(t) } }
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

## Design checklist

1. Write the rules down before the code, and name the lock or happens-before rule that protects each one.
2. Make the values that cross threads unchangeable, and check them in the constructor.
3. Lock several accounts only in one global id order; sort them when there are more than two.
4. Keep the check inside the critical section that acts on it.
5. Never wait inside an account lock: the journal, the safety call and logging happen outside.
6. Size pools and queues with Little's law, then check the limit of whatever sits behind them.
7. Bound every queue, choose the rejection policy on purpose, and count rejections.
8. Shut down in order, within one deadline, and hand back what never ran.
9. One new virtual thread per request, and one shared semaphore per slow outside service.
10. One deadline per request; cancel what you stop waiting for; make the fallback a business rule.
11. Fail fast in fan-outs, and let no check outlive its request.
12. Test the rules with threads that collide, using latches and counts, never timings.

## Diagnostics

| Question | Command |
|---|---|
| Which pool is stuck, and on what? | `jcmd <pid> Thread.print -l`: named threads, state, `parking to wait for`, `Locked ownable synchronizers` |
| Is it a lock cycle? | the same dump ends with `Found one Java-level deadlock` if it is |
| Where are 10,000 virtual threads? | `jcmd <pid> Thread.dump_to_file -format=json /tmp/t.json` (add `-overwrite` to replace a file) |
| How are they spread? | `jq` per container, then group stacks by the first line of your own code and count with `uniq -c` |
| Is anything pinned? | JFR's `jdk.VirtualThreadPinned` event (20 ms threshold by default) |

Versions: virtual threads are final in JDK 21 (JEP 444); `synchronized` stops pinning in JDK 24 (JEP 491), and JDK 25 is the first long-term-support release with that fix; JSON dumps carry `state` and `virtual` from JDK 25; `StructuredTaskScope` is a preview API in JDK 25 to 27 and final in JDK 28 (JEP 543)."""

RECAP = [
 "Start from the rules: money is conserved, no balance goes below zero, a transfer is whole or not at all. Every lock and every happens-before rule in the program protects one of them.",
 "One `ReentrantLock` per account, taken in one global id order, lets transfers on different accounts overlap without deadlock; the balance check lives inside the same critical section as the move.",
 "A transfer is a value that can't change, checked when it's built, so any thread sees it whole; a reused, changeable row handed to a pool delivers the wrong data.",
 "Stress tests make threads collide behind a start latch and check every rule, at the end and where it can break. A pass is evidence, not proof.",
 "The ledger pool is sized by Little's law (8 threads, 80 slots), bounded and named, and it turns overflow away by counting and throwing: a visible \"busy, try again\", never a lost transfer.",
 "Shutdown drains within a deadline, then cancels and hands back what never started. The journal is written before `apply`, so an interrupt never leaves half a transfer.",
 "A whole snapshot holds every account lock in order, copies, and publishes a record that never changes through one volatile field; readers never lock.",
 "Requests run on one new virtual thread each, behind written-down limits: a shared semaphore for the safety service, the bounded ledger pool, and one deadline per request with the small-amount rule as its fallback.",
 "Fail-fast screening takes answers in the order they finish and ends with `shutdownNow()` and `close()`, so no call outlives its request or keeps a permit.",
 "Thread dumps find what tests can't: a pool parked on its own futures in `Thread.print -l`, and 10,000 virtual threads grouped by container and stack in the JSON dump."
]

QUIZ = [
 {"q": "Two transfers run at once: acc-07 to acc-03, and acc-03 to acc-07. With the ledger's lock order, which lock does each take first?",
  "options": ["Each takes its `from` account first", "Both take acc-03 first", "Both take acc-07 first", "Whichever thread starts first decides"],
  "answer": 1,
  "why": "The order is by id, whichever way the money moves, so both lock acc-03 first. The second thread waits while holding nothing: a short wait, not a deadlock. \"`from` first\" is the order that freezes, the way Ana and Ben's transfers did.",
  "from": "cap1-01"},
 {"q": "A stress test of a ledger that checks the balance before taking the locks reports a total of 500,000 and no negative balances at the end. Why did it miss the bug?",
  "options": ["The race can't happen on Intel and AMD processors", "Accounts went below zero during the run, and later credits topped them up before the final check",
              "The JIT removed the check", "Eight threads are too few to cause a race"],
  "answer": 1,
  "why": "Each move was still one step under both locks, so the total held, and the overdrafts healed before the end. Check a rule where it can break as well: `debit` refusing an overdraft turns the race into an immediate failure.",
  "from": "cap1-01"},
 {"q": "Peak traffic is 3,000 transfers a second, and the journal write takes 4 ms. The disk allows 10 writes at once. What should the ledger pool's thread count be?",
  "options": ["12, from Little's law", "10: the journal's limit is lower than what Little's law asks for", "3,000", "As many as the machine has cores"],
  "answer": 1,
  "why": "Little's law asks for 3,000 x 0.004 = 12, but the journal takes only 10 writes at once, so the 11th and 12th threads would only queue inside it. Size from the scarce resource: 10 threads give at most 10 / 0.004 = 2,500 transfers a second, and the counting rejection handles the rest.",
  "from": "cap1-02"},
 {"q": "Which rejection policy can silently lose a transfer that a customer was told was accepted?",
  "options": ["A counting policy that throws", "`CallerRunsPolicy`", "`DiscardOldestPolicy`", "`AbortPolicy`"],
  "answer": 2,
  "why": "`DiscardOldestPolicy` drops the oldest queued task, which a caller already holds a future for, and that future never completes. A throwing policy turns the new transfer away before anyone is told it was accepted, and `CallerRunsPolicy` runs it on the thread that submitted it.",
  "from": "cap1-02"},
 {"q": "A balances page adds up the accounts one at a time, locking each account while it reads it. Transfers keep running. What can it show?",
  "options": ["Always the exact total, because every read holds a lock", "A total that is too high or too low, because a transfer can run between two reads",
              "An exception, because two locks are taken", "A total that is always too low"],
  "answer": 1,
  "why": "Money can move from an account not yet read to one already read (counted in neither) or the other way (counted twice). Only holding every lock at once, in the global order, gives one moment.",
  "from": "cap1-02"},
 {"q": "A thread dump shows every `ledger-` thread `WAITING (parking)` on a `FutureTask` inside your own `statement` method, and no deadlock report. What is wrong?",
  "options": ["A lock-order deadlock between two accounts", "Tasks waiting for other tasks queued in the same bounded pool",
              "The journal is slow", "The pool's threads are pinned"],
  "answer": 1,
  "why": "Threads parked on futures of their own pool, with tasks still queued, is pool-induced deadlock: cooks waiting for tickets behind them on the rail. There is no lock cycle, so the JVM's detector reports nothing. Do the work inline, chain the next step instead of waiting, or use a separate pool.",
  "from": "cap1-02"},
 {"q": "Which design caps what the safety service sees when 10,000 requests run on virtual threads?",
  "options": ["A fixed pool of 20 virtual threads for whole requests", "One `Semaphore(20)` field on the safety client, shared by every request",
              "A `Semaphore(20)` created in each request handler", "`newVirtualThreadPerTaskExecutor()` on its own"],
  "answer": 1,
  "why": "One shared semaphore limits only the safety call. A pool of virtual threads caps the whole request, the daily-limit check and the ledger wait included. A semaphore per handler limits nothing, and the per-task executor has no limit at all.",
  "from": "cap1-03"},
 {"q": "On a bad day, each safety call takes 2 s. The request stops waiting at its 300 ms deadline but never cancels the call, and it uses a shared executor. What happens to the bulkhead?",
  "options": ["Nothing: every request answers in 300 ms", "Its permits stay held by abandoned calls for 2 s each, so most new requests can't get one",
              "It grows to fit the extra calls", "The calls are interrupted automatically"],
  "answer": 1,
  "why": "A timeout ends the wait, not the work. Each abandoned call keeps its permit until the safety service answers. Cancel the call at the deadline, so its `finally` gives the permit back to the next request.",
  "from": "cap1-03"},
 {"q": "The ledger must run on JDK 21 and serve virtual threads. Why are the account locks `ReentrantLock`s?",
  "options": ["`synchronized` doesn't make writes visible to other threads", "On JDK 21, a virtual thread waiting to enter, or waiting inside, `synchronized` pins its carrier; `ReentrantLock` lets it step off",
              "`ReentrantLock` makes the critical section faster", "Kotlin can't use `synchronized`"],
  "answer": 1,
  "why": "JDK 24 (JEP 491) removed that pinning, but on JDK 21 to 23 a waiting `synchronized` block holds the carrier, like a waiter holding a hot pan. `ReentrantLock` has always let a waiting virtual thread step off. Either way, nothing slow belongs inside an account lock.",
  "from": "cap1-03"},
 {"q": "`jcmd <pid> Thread.print` on the server during the safety service's bad day shows no request threads at all. Where are they?",
  "options": ["They have all finished", "They are waiting virtual threads, which `Thread.print` doesn't list; `Thread.dump_to_file -format=json` does",
              "They are inside the carriers, under the name `ForkJoinPool-1-worker-N`", "The garbage collector removed them"],
  "answer": 1,
  "why": "A waiting virtual thread is a stack on the heap, not an operating-system thread. `Thread.print` lists platform threads (plus virtual threads on a carrier, from JDK 24). The JSON dump lists every thread, grouped by the container that started it.",
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
