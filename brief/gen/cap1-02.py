import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ledger/src"
P = "java/workbench/ledger/l02"
DJ = "java/workbench/ledger/l02/demo"
DK = "kotlin/workbench/ledger/l02/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ledger:demo -Pmain=workbench.ledger.l02.demo."


def demo(name):
    """A Java demo with its runnable Kotlin twin, both read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": RUN + name, "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt"}}


FIGURE = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="The ledger pool: transfers arrive, 8 named threads run them, 80 queue slots wait, '
    'and the rest are counted and turned away; each thread writes the journal first, then applies">'
    '<text class="t-s t-m" x="20" y="24">payday peak: 1,600 transfers a second, 5 ms each</text>'
    '<rect class="box" x="20" y="100" width="110" height="44" rx="8"/><text class="t" x="75" y="127" text-anchor="middle">transfers</text>'
    '<line class="ln" x1="130" y1="122" x2="168" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="170" y="96" width="170" height="52" rx="8"/>'
    '<text class="t" x="255" y="118" text-anchor="middle">queue: 80 slots</text>'
    '<text class="t-s t-m" x="255" y="138" text-anchor="middle">1,600/s x 50 ms</text>'
    '<line class="ln" x1="340" y1="122" x2="378" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="380" y="50" width="150" height="40" rx="8"/><text class="t t-code" x="455" y="75" text-anchor="middle">ledger-0</text>'
    '<rect class="box-a" x="380" y="102" width="150" height="40" rx="8"/><text class="t t-code" x="455" y="127" text-anchor="middle">ledger-1 ...</text>'
    '<rect class="box-a" x="380" y="154" width="150" height="40" rx="8"/><text class="t t-code" x="455" y="179" text-anchor="middle">ledger-7</text>'
    '<text class="t-s t-m" x="455" y="214" text-anchor="middle">8 threads: 1,600/s x 5 ms</text>'
    '<line class="ln" x1="530" y1="122" x2="558" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="560" y="74" width="105" height="40" rx="8"/><text class="t" x="612" y="99" text-anchor="middle">1. journal</text>'
    '<rect class="box-ok" x="560" y="130" width="105" height="40" rx="8"/><text class="t" x="612" y="155" text-anchor="middle">2. apply</text>'
    '<line class="ln" x1="612" y1="114" x2="612" y2="128" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="255" y1="148" x2="255" y2="218" marker-end="url(#arr)"/>'
    '<rect class="box-bad" x="170" y="220" width="170" height="40" rx="8"/><text class="t" x="255" y="245" text-anchor="middle">turned away, counted</text>'
    '<text class="t-s t-bad" x="80" y="245" text-anchor="middle">"busy, try again"</text>'
    '</svg>')

DUMP = """"ledger-0" #19 [5741] prio=5 os_prio=0 cpu=1.33ms elapsed=1.74s ... waiting on condition
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@21.0.12.1/Native Method)
	- parking to wait for  <0x00000006f79ef530> (a java.util.concurrent.FutureTask)
	at java.util.concurrent.locks.LockSupport.park(java.base@21.0.12.1/LockSupport.java:221)
	at java.util.concurrent.FutureTask.awaitDone(java.base@21.0.12.1/FutureTask.java:500)
	at java.util.concurrent.FutureTask.get(java.base@21.0.12.1/FutureTask.java:190)
	at workbench.ledger.l02.demo.PoolHangDemo.statement(PoolHangDemo.java:33)
	at workbench.ledger.l02.demo.PoolHangDemo.lambda$main$0(PoolHangDemo.java:21)
	...
	at java.util.concurrent.ThreadPoolExecutor.runWorker(java.base@21.0.12.1/ThreadPoolExecutor.java:1144)
	...
   Locked ownable synchronizers:
	- <0x00000006f79650b8> (a java.util.concurrent.ThreadPoolExecutor$Worker)

"ledger-1" #20 [5742] prio=5 os_prio=0 cpu=0.83ms elapsed=1.74s ... waiting on condition
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@21.0.12.1/Native Method)
	- parking to wait for  <0x00000006f7602c18> (a java.util.concurrent.FutureTask)
	...
	at workbench.ledger.l02.demo.PoolHangDemo.statement(PoolHangDemo.java:33)
	...
   Locked ownable synchronizers:
	- <0x00000006f79bb838> (a java.util.concurrent.ThreadPoolExecutor$Worker)"""

L = {
 "id": "cap1-02",
 "title": "Run it on a pool you can reason about",
 "minutes": 40,
 "goal": "By the end you can run the ledger on a bounded pool whose every setting you can defend (sizes from Little's law, named threads, a rejection rule chosen on purpose), shut it down without losing a transfer, publish a snapshot of all balances that always adds up, and find a stuck pool in a thread dump.",
 "opening": """Picture the bank at lunchtime on payday. Transfers arrive at 1,600 a second. Before the ledger changes any balance, it writes each transfer into a journal, a record on disk that survives a crash, and each write takes about 5 ms. The writing needs threads, paths of work that run side by side, so the ledger gets a thread pool: a fixed team of threads that take tasks from a queue, like the cooks and the order rail in Thread pools and executors.

How big should the team be, and how long the rail? One line, `Executors.newFixedThreadPool(8)`, answers "eight cooks and a rail with no end". It passes every test. On the day the disk slows down, the rail grows by thousands of transfers a second, and each of them was told "accepted". At closing time, a plain `shutdownNow()` drops nearly all of them without a word.

Design the ledger and make it correct made the ledger right on any threads. This lesson chooses the threads. We'll size the pool from the bank's own numbers, close it without losing a transfer, publish balances that always add up, and find a stuck pool in a thread dump. Before we start, make a guess, and keep it in mind.""",
 "warmup": {
  "q": "The ledger pool has 8 threads (core and max), a queue with room for 80 transfers, and a rule that turns the rest away. Each transfer takes 5 ms. 300 transfers arrive within a few milliseconds. About how many are accepted?",
  "options": ["All 300: the queue makes room", "About 88: 8 running and 80 waiting", "About 8: one per thread", "About 80: the size of the queue"],
  "answer": 1,
  "why": "From Inside ThreadPoolExecutor: core, max, queue, rejection: the 8 threads take the first 8 tasks, the next 80 fill the queue, and with core equal to max the pool can't add threads, so the other 212 are turned away. The demo in this lesson accepts 88 in most runs, because submitting 300 tasks takes less time than the first 5 ms transfer. On a very busy machine it can accept only 80, when the threads haven't picked up their first tasks before the queue fills."
 },
 "sections": [
  {
   "h": "Every setting is a decision: sizing the pool from the bank's own numbers",
   "body": """Lesson 1's ledger is correct on any number of threads. Now it needs threads to run on. A real transfer does more than change two numbers. It first goes into the **journal**, a log on disk that the ledger writes before it changes anything in memory. If the program crashes, the journal still says which transfers were accepted, so none of them is lost. Say a journal write takes 5 ms.

Thread pools and executors pictured a pool as a kitchen: a team of cooks (the threads) taking tickets off a rail (the queue). The one-line pools each get one part of that kitchen wrong. `Executors.newFixedThreadPool(8)` has a rail with no end, so a slow disk turns into millions of waiting transfers and, finally, a program that runs out of memory. `Executors.newCachedThreadPool()` hires a new cook for every ticket, so the same slow disk turns into thousands of threads.

So we build the pool ourselves, and write down a reason for every setting:

```java
PoolPlan plan = PoolPlan.fromLittlesLaw(1_600, Duration.ofMillis(5), Duration.ofMillis(50));   // 8 and 80
ThreadPoolExecutor pool = new ThreadPoolExecutor(
        plan.threads(), plan.threads(),                    // core == max: no extra threads in a rush
        0, TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(plan.queueCapacity()),    // bounded: a full queue says no
        Thread.ofPlatform().name("ledger-", 0).factory(),  // ledger-0, ledger-1, ... in every dump
        new CountingAbortPolicy());                        // counted, then thrown at the caller
pool.prestartAllCoreThreads();
```

```kotlin
val plan = PoolPlan.fromLittlesLaw(1_600, Duration.ofMillis(5), Duration.ofMillis(50))      // 8 and 80
val pool = ThreadPoolExecutor(
    plan.threads(), plan.threads(),                        // core == max: no extra threads in a rush
    0, TimeUnit.MILLISECONDS,
    ArrayBlockingQueue(plan.queueCapacity()),              // bounded: a full queue says no
    Thread.ofPlatform().name("ledger-", 0).factory(),      // ledger-0, ledger-1, ... in every dump
    CountingAbortPolicy())                                 // counted, then thrown at the caller
pool.prestartAllCoreThreads()
```

The sizes come from Little's law, from Sizing a pool: CPU-bound, IO-bound and Little's law. It says the number of things inside a system equals the rate at which they arrive times how long each one stays. At the payday peak of 1,600 transfers a second, each holding a thread for 5 ms, that's 1,600 x 0.005 = 8 transfers in flight, that is, in progress at once. So we need 8 threads. With fewer, the queue grows at every peak. With many more, we only add threads that wait on the same disk.

The queue gets the same law. A busy pool finishes 1,600 transfers a second, so 80 queued transfers drain in 80 / 1,600 = 50 ms. If 50 ms is the longest a transfer should wait for a thread, 80 slots is the most the queue should hold. A queue of 10,000 would hide six seconds of waiting, long after the customer's app has given up.

A pool has a core size, the threads it keeps, and a maximum size, the most it may ever have. Core equals max here because, as Inside ThreadPoolExecutor showed, a pool adds threads past its core only when the queue is full. Extra threads would only add waiters on the same journal, so the right answer to a full queue is no.

That leaves the last decision: what happens to a transfer when the queue is full. That's the **rejection policy**. `DiscardPolicy` and `DiscardOldestPolicy` drop a transfer without telling anyone, so they are never right for money. `CallerRunsPolicy` makes the thread that submitted the transfer write the journal itself. That suits a nightly import, and it's wrong for a thread serving a customer who is waiting.

So the lab counts and throws. The counting policy is the bank's doorman. When the waiting area is full, he turns the next customer away politely and makes a mark on his clipboard. The customer gets a fast "busy, try again in a moment" (web servers send it as status 503) and tries again with the same transfer id. The marks show up on the bank's dashboard, the screen where its staff watch the program's numbers.

The thread factory gives each thread a name tag, `ledger-0` to `ledger-7`, as Pools in production did for the kitchen's cooks. Those name tags will matter at the end of this lesson.

**A pool you can't explain is a pool you can't trust. Write down a reason for every number.**

The pool can take transfers now. The harder moment comes when it has to stop.""",
   "figure": {"svg": FIGURE, "caption": "Little's law sizes both halves of the pool: 8 threads for the transfers in flight, 80 slots for 50 ms of waiting. Whatever doesn't fit is turned away and counted."},
   "try": {
    "title": "Send a burst at the pool",
    "minutes": 4,
    "steps": [
     "Run `BurstDemo`: 300 transfers of 5 ms each arrive at once at the pool above. Predict how many are accepted, and how long submitting takes.",
     "Run it with `-Pargs=callerRuns`. Predict how many transfers the submitting thread runs itself, and how long submitting takes now."
    ],
    "code": demo("BurstDemo"),
    "expect": "With the counting policy, 88 are accepted (8 running, 80 waiting) and 212 are turned away within a few milliseconds. On a very busy machine you may see 80, if the threads hadn't taken their first tasks before the queue filled. The accepted ones are done after roughly 60 to 70 ms (88 x 5 ms / 8 threads, plus start-up). With `CallerRunsPolicy`, nothing is turned away, but the submitting thread ran 24 or 25 transfers itself, and submitting took 131 to 141 ms instead of 5 to 8. While that thread writes a journal entry, it can't submit anything, which slows the stream down. If it were serving a customer, that customer would have waited the whole time for other people's transfers."
   },
   "refs": [
    {"title": "ThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html", "kind": "docs"}
   ]
  },
  {
   "h": "Closing time: shutting down without losing a transfer",
   "body": """A new version of the bank's program goes live, and the old one has to stop while transfers are still queued. Each of them belongs to a customer who was told "accepted". So the rule for shutdown is simple to say. When it ends, every accepted transfer has been applied, has failed with an error its caller saw, or has been handed back to us by id. None may vanish.

`pool.shutdownNow()` on its own breaks that rule. It interrupts the running tasks, that is, asks them to stop, and returns the queued ones as a `List<Runnable>`. Ignore the list, and those transfers are gone. Worse, their futures never complete. A **future** is the takeaway ticket from Callable, Future, cancellation and interruption: the caller holds it, and waits on it with `get()` until the result is ready. Here is what this section's demo printed with a bare `shutdownNow()`:

```text
naive, grace 100 ms: accepted 1,000 | applied 0 | interrupted 8 | handed back 0 | lost 992
futures that will never complete: 992
```

Out of 1,000 accepted transfers, 992 simply vanished, and each one left a ticket that will never be called. A customer waiting on one of them would wait, very patiently, forever.

Pools in production closed the kitchen at night in order: stop taking orders, let the cooks finish within a deadline, then stop what's left and write it down. Here is that order for the ledger:

```java
public ShutdownReport shutdown(Duration grace) throws InterruptedException {
    pool.shutdown();                                              // 1. no new transfers; the queue drains
    if (pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS))
        return new ShutdownReport(true, List.of());               // 2. everything accepted was applied
    List<Transfer> neverStarted = new ArrayList<>();
    for (Runnable r : pool.shutdownNow()) {                       // 3. interrupt, take back the queue
        TransferTask task = (TransferTask) r;
        task.cancel(false);                                       //    wakes a caller blocked in get()
        neverStarted.add(task.transfer());
    }
    pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS);
    return new ShutdownReport(false, List.copyOf(neverStarted));  // 4. log them, or replay them
}
```

```kotlin
fun shutdown(grace: Duration): ShutdownReport {
    pool.shutdown()                                               // 1. no new transfers; the queue drains
    if (pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS))
        return ShutdownReport(true, emptyList())                  // 2. everything accepted was applied
    val neverStarted = pool.shutdownNow().map { r ->              // 3. interrupt, take back the queue
        val task = r as TransferTask
        task.cancel(false)                                        //    wakes a caller blocked in get()
        task.transfer
    }
    pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)
    return ShutdownReport(false, neverStarted)                    // 4. log them, or replay them
}
```

First, `shutdown()` closes the door to new transfers, while the queue keeps draining (1). Then we wait up to the grace period, the time we allow for draining. If the pool finished, everything accepted was applied (2). If not, `shutdownNow()` interrupts the running transfers and hands back the queue (3). We cancel each queued task, which completes its future, so a caller blocked in `get()` wakes up with a `CancellationException` instead of waiting forever. Finally, we wait once more and report the transfers that never started, so someone can log them or run them again later (4).

Two details make this work. First, the queue must hold objects that know their transfer. `pool.submit(callable)` wraps your work in an anonymous `FutureTask`, so the lab's `submit` builds a `TransferTask`, a `FutureTask` that remembers its transfer, and hands it to `execute`. Then `shutdownNow()` gives back transfers, not mystery `Runnable`s.

Second, an interrupted task must leave nothing half done. Each task writes the journal first and changes memory second. An interrupt during the journal write means the transfer was never applied: its future fails, and no balance changed. And `apply` itself never waits for anything, so once it starts, it finishes.

The grace period comes from the same numbers as the pool. A full queue of 80 drains in 50 ms, so a few seconds of grace is plenty. The system that stops a program for a new version usually waits about 30 seconds before it stops it by force, and the drain fits easily inside that. With the drain in place, the same demo printed:

```text
drain, grace 100 ms: accepted 1,000 | applied 157 | interrupted 8 | handed back 835 | lost 0
futures that will never complete: 0
```

The arithmetic holds: 100 ms is 20 rounds of 5 ms on 8 threads, about 160 transfers. Eight were stopped in the middle of their journal write, and the other 835 came back by id.

**Shutdown is part of the program. Drain first, then hand back what never ran.**

No transfer goes missing at closing time now. But a customer who asks for every balance at once can still see a number that never existed.""",
   "try": {
    "title": "Lose transfers, then stop losing them",
    "minutes": 4,
    "steps": [
     "Run `ShutdownDemo -Pargs=naive`: 1,000 accepted transfers, then a bare `shutdownNow()`. Read the `lost` column and the last line.",
     "Run it with no arguments (drain, 100 ms of grace), then with `-Pargs='drain 5000'`. Before each run, predict how many transfers are applied."
    ],
    "code": demo("ShutdownDemo"),
    "expect": "Naive: about 990 lost (987 and 992 in runs here), and as many futures that will never complete, so their callers would wait forever. Drain with 100 ms: about 160 applied (8 threads x 20 rounds of 5 ms), 7 or 8 interrupted in the middle of their journal write, 835 handed back, and 0 lost. With 5 s of grace, all 1,000 are applied, because they need only about 625 ms on 8 threads."
   },
   "refs": [
    {"title": "ExecutorService (Java SE 25 API): the shutdown idiom", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html", "kind": "docs"}
   ]
  },
  {
   "h": "A snapshot of every balance, published so nobody sees it torn",
   "body": """The bank's app has a page that shows every balance at once, and rule 1 says they must add up to the opening total. Let's try the obvious way on a small ledger: 50 accounts with 1,000 cents each, so 50,000 in total. A reader walks the accounts in id order. It locks one account, reads it, adds it and moves on:

```java
long sum = 0;
for (Account a : accounts) {
    a.lock().lock();
    try { sum += a.balance(); } finally { a.lock().unlock(); }   // each read is safe...
}                                                                  // ...the sum is not
```

```kotlin
var sum = 0L
for (a in accounts) {
    sum += a.lock.withLock { a.balance }                         // each read is safe...
}                                                                  // ...the sum is not
```

Trace the smallest case. The reader has already passed account 3. Now a transfer moves 300 cents from account 40 to account 3. The reader goes on and reads the rest, account 40 included, and gets 49,700. It saw account 3 before the money arrived, and account 40 after it left. Every read held a lock, and no transfer broke a rule. The sum still mixes two moments. A sum like that is **torn**: it matches no state the ledger was ever in. A transfer in the other direction makes the reader count the same money twice.

In one Java run of this section's demo, 7,241 of 9,456 sums were torn, some by thousands of cents. Runs on a busier machine tore fewer, 368 to 506 sums out of thousands, but never none.

A whole snapshot needs one moment at which no transfer is half done. Don't share: immutability, confinement, ThreadLocal gave us the picture. The shop owner doesn't erase prices while people read the board; she prints a new board and hangs it up in one move. For the ledger, that means taking every account's lock, in the same id order that `apply` uses, so a snapshot can never deadlock with a transfer. Then we copy the balances into a new record that never changes, publish it, and let go:

```java
public BalanceSnapshot snapshot() {
    for (Account a : inLockOrder) a.lock().lock();                 // 1. every lock, in id order
    try {
        Map<String, Long> copy = new HashMap<>();
        long total = 0;
        for (Account a : inLockOrder) { copy.put(a.id(), a.balance()); total += a.balance(); }
        BalanceSnapshot s = new BalanceSnapshot(copy, total, ++version);   // 2. a record that never changes
        latest = s;                                                // 3. one volatile write publishes it
        return s;
    } finally {
        for (int i = inLockOrder.size() - 1; i >= 0; i--) inLockOrder.get(i).lock().unlock();
    }
}
```

```kotlin
fun snapshot(): BalanceSnapshot {
    inLockOrder.forEach { it.lock.lock() }                         // 1. every lock, in id order
    try {
        val copy = inLockOrder.associate { it.id to it.balance }
        val s = BalanceSnapshot(copy, copy.values.sum(), ++version) // 2. a record that never changes
        latest = s                                                 // 3. one @Volatile write publishes it
        return s
    } finally {
        inLockOrder.asReversed().forEach { it.lock.unlock() }
    }
}
```

First we take every lock, in id order (1). Now no transfer can move money. Then we copy all 50 balances into a new record, with the total and a version number (2). Then one write to `latest` publishes it (3). The keyword `volatile` marks a field whose every read sees the latest write, from any thread. Last, the `finally` releases the locks in reverse order, and any transfer that was waiting runs.

Readers stop adding things up. They read one field, `latest`, which points to the last finished snapshot, and they take no lock at all. A reader who looks just before a new snapshot is published sees all of the old one: old, but whole. A reader who looks just after sees all of the new one. Old or new, never a mix.

Happens-before, the rules that matter, asked us to name the rule that makes each shared field safe to read. Here is the list for the whole ledger:

| Field | Why every reader sees it correctly |
|---|---|
| `Account.balance` | the account's lock: each release happens-before the next lock of the same account |
| `accounts`, `inLockOrder` | final fields, set in the constructor, never changed |
| `version` | written only while every account lock is held |
| `latest` | volatile: its write happens-before every later read |
| a snapshot's `balances` and `total` | final fields of a record, holding a map that `Map.copyOf` made unchangeable |
| a `Transfer` in the pool | it never changes, and `execute` happens-before the task runs |
| a transfer's outcome | the task's end happens-before `Future.get()` returns |

Three pictures from the memory model track sit in that table. The account locks are the cashier's key: whoever takes the same key next sees everything written before it was handed on. `latest` is the museum's OPEN/CLOSED sign, a `volatile` field that every reader checks fresh. And a finished `BalanceSnapshot` is a letter in a sealed envelope, whole for anyone who receives it.

Writing `latest` before the locks are released keeps snapshots in version order. Two snapshots can't overlap, because each one needs every lock.

**Build the whole snapshot while no transfer can run, then publish it with one volatile write.**

Every field now has a named rule behind it. One last kind of failure has no field at all: a pool that waits for itself.""",
   "aside": {
    "title": "Doesn't locking all 50 accounts stop the bank?",
    "body": "For a moment, yes, and the moment is short. Copying 50 balances takes microseconds, so a transfer that arrives meanwhile waits about as long as it would behind one busy account. The cost grows with the number of accounts, though, and at five million accounts holding every lock would be a pause customers feel. Real systems then take snapshots less often, or split the accounts into groups with a snapshot each, or build snapshots from the journal on another machine. Go deeper, at the end of this lesson, sketches all three."
   },
   "try": {
    "title": "Tear a snapshot, then make it whole",
    "minutes": 3,
    "steps": [
     "Run `TornSnapshotDemo`. Four threads move money while the main thread adds up all 50 balances, one locked account at a time. Predict how many sums come out wrong.",
     "Run it with `-Pargs=locked`, where the reader holds every lock while it adds."
    ],
    "code": demo("TornSnapshotDemo"),
    "expect": "One account at a time, a good share of the sums are wrong: 7,241 of 9,456 in one Java run, and 506 of 4,607 and 368 of 9,422 in Java and Kotlin runs on a busier machine, some off by more than 7,000 cents, while every transfer kept the books balanced. With every lock held, no sum is torn. A real bank wouldn't let every request take all the locks. It takes one snapshot every few hundred milliseconds and lets readers share it through `latestSnapshot()`."
   }
  },
  {
   "h": "A stuck pool, found in a thread dump",
   "body": """Here is a bug that passes every test with a small batch. At the end of each month, the bank prints a statement for every account, a page that shows its balance. The statement job runs on the ledger pool, and each statement asks the same pool for the balance:

```java
pool.submit(() -> {
    Future<Long> balance = pool.submit(() -> balanceOf(account));    // a task inside a task
    return account + ": " + balance.get();                           // waits for it
});
```

```kotlin
pool.submit(Callable {
    val balance = pool.submit(Callable { balanceOf(account) })       // a task inside a task
    "$account: ${balance.get()}"                                     // waits for it
})
```

With 2 threads and 3 statements, the first two statements take both threads. Each one submits a balance lookup, which joins the queue behind the third statement. Now both threads wait for lookups that need a free thread, and no thread will ever be free. Pools in production called this pool-induced deadlock, and pictured it as cooks waiting for tickets that sit on the rail behind them. This section is about finding it in a running program.

The tool is `jcmd`, which comes with the JDK and sends commands to a running Java program. One of its commands prints a **thread dump**: every thread's name, state and stack (the chain of method calls it is in the middle of) at one moment. Start `PoolHangDemo` with a long hang, then run this from a second terminal:

```bash
jcmd                          # lists running Java programs and their process ids
jcmd <pid> Thread.print -l    # -l adds the java.util.concurrent locks each thread holds
```

Here's the part that matters, from a real run on JDK 21, trimmed:

```text
""" + DUMP + """
```

Read each thread in the same order. The name says which pool: both `ledger-` threads are stuck, and their name tags tell us so at once. The state, `WAITING (parking)`, means a `java.util.concurrent` tool put them to sleep; a thread stuck at a `synchronized` block would say `BLOCKED`. The `parking to wait for` line names the object they wait on, a `FutureTask`, so they are inside `get()`. The first line from our own code, `statement` at line 33, is that `get()` call. And under `Locked ownable synchronizers`, each thread holds its own `ThreadPoolExecutor$Worker`, a lock that a pool thread holds while it runs a task. Both threads are busy, and busy waiting.

Notice what's missing: the dump never says `Found one Java-level deadlock`. The JVM's detector looks for threads that hold locks other threads want, in a circle. Here nobody holds a lock that anybody else wants. So learn this signature instead: every thread of one pool parked on a `FutureTask` from that same pool, with tasks still queued. The fixes come from that lesson. Do the lookup inline, chain the next step with `thenApply` instead of waiting, or give lookups their own pool.

**A pool whose tasks wait on the same pool can stop without any lock. Never wait on your own pool from inside it.**

This pool is right for the journal writes, which are short and few at a time. It would be wrong for the customers' requests themselves. A request spends most of its time waiting on other services, and a pool of platform threads, the ordinary threads the operating system runs, can hold only a few hundred waiting requests. That's the next sitting's job.""",
   "try": {
    "title": "Take the dump yourself",
    "minutes": 5,
    "steps": [
     "Run `PoolHangDemo` with `-Pargs=60` so it stays stuck for a minute. It prints its process id.",
     "In a second terminal, run `jcmd <pid> Thread.print -l`. For both `ledger-` threads, find the state, the `parking to wait for` line, the first line from `workbench.ledger`, and the `Locked ownable synchronizers`. Then find `main`.",
     "Scroll to the end of the dump. Is there a deadlock report? Explain why not.",
     "Change `statement` to call `balanceOf(account)` directly instead of submitting it, and run the demo again."
    ],
    "code": demo("PoolHangDemo"),
    "expect": "Both `ledger-0` and `ledger-1` are `WAITING (parking)` on a `FutureTask` inside `PoolHangDemo.statement`, each holding its `ThreadPoolExecutor$Worker`, and `main` is `TIMED_WAITING (sleeping)` in `Thread.sleep`. There is no deadlock report, because no thread holds a lock another thread wants. When the sleep ends, the demo prints `active=2, queued=3, completed=0`: the third statement and both lookups never ran. With the lookup inline, it prints `completed=3`. The Kotlin twin shows the same dump, with `PoolHangDemoKt.statement` as your line."
   }
  }
 ],
 "compare": {
  "title": "Starting the pool and submitting a transfer",
  "java": {"title": "LedgerService.java", "src": """public static LedgerService start(Ledger ledger, Journal journal, PoolPlan plan) {
    CountingAbortPolicy rejections = new CountingAbortPolicy();
    ThreadPoolExecutor pool = new ThreadPoolExecutor(
            plan.threads(), plan.threads(), 0, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(plan.queueCapacity()),
            Thread.ofPlatform().name("ledger-", 0).factory(),
            rejections);
    pool.prestartAllCoreThreads();
    return new LedgerService(ledger, journal, pool, rejections);
}

public Future<Outcome> submit(Transfer t) {
    TransferTask task = new TransferTask(t, () -> {
        journal.append(t);
        return ledger.apply(t);
    });
    pool.execute(task);
    return task;
}

static final class TransferTask extends FutureTask<Outcome> {
    private final Transfer transfer;
    TransferTask(Transfer transfer, Callable<Outcome> work) { super(work); this.transfer = transfer; }
    Transfer transfer() { return transfer; }
}"""},
  "kotlin": {"title": "LedgerService.kt", "src": """fun start(ledger: Ledger, journal: Journal, plan: PoolPlan): LedgerService {
    val rejections = CountingAbortPolicy()
    val pool = ThreadPoolExecutor(
        plan.threads, plan.threads, 0, TimeUnit.MILLISECONDS,
        ArrayBlockingQueue(plan.queueCapacity),
        Thread.ofPlatform().name("ledger-", 0).factory(),
        rejections)
    pool.prestartAllCoreThreads()
    return LedgerService(ledger, journal, pool, rejections)
}

fun submit(t: Transfer): Future<Outcome> {
    val task = TransferTask(t) {
        journal.append(t)
        ledger.apply(t)
    }
    pool.execute(task)
    return task
}

class TransferTask(val transfer: Transfer, work: Callable<Outcome>) : FutureTask<Outcome>(work)"""},
  "note": "Nothing here is special to either language: `ThreadPoolExecutor`, `ArrayBlockingQueue` and `Thread.ofPlatform()` are the same JDK classes, with the same rules. Kotlin shortens the `FutureTask` subclass to one line, because the constructor parameter `work` goes straight to the parent class in the class header, and a trailing lambda becomes the Java `Callable`. One Kotlin detail matters. When you call `pool.submit` with a bare lambda, Kotlin has to choose between `submit(Runnable)` and `submit(Callable)`. Writing `Callable { ... }` says which one you mean, so the future carries your result."
 },
 "worked": {
  "title": "Size the pool for a busier payday",
  "steps": [
   {"say": "The bank expects a busier payday: 4,000 transfers a second at the peak. Under that load, a journal write takes 4 ms. We want no transfer to wait more than 100 ms for a thread. Start with Little's law, for both halves of the pool.",
    "code": """// 1. peak rate, time each transfer holds a thread, longest acceptable wait in the queue
PoolPlan plan = PoolPlan.fromLittlesLaw(4_000, Duration.ofMillis(4), Duration.ofMillis(100));
// 2. 4,000/s x 0.004 s = 16 in flight; 4,000/s x 0.1 s = 400 waiting
System.out.println(plan);   // PoolPlan[threads=16, queueCapacity=400]""",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": """// 1. peak rate, time each transfer holds a thread, longest acceptable wait in the queue
val plan = PoolPlan.fromLittlesLaw(4_000, Duration.ofMillis(4), Duration.ofMillis(100))
// 2. 4,000/s x 0.004 s = 16 in flight; 4,000/s x 0.1 s = 400 waiting
println(plan)   // PoolPlan[threads=16, queueCapacity=400]"""},
   {"say": "Now check what sits behind the pool, as Sizing a pool insisted. The disk that holds the journal handles 12 writes at once before each one slows down. With 16 threads, the extra 4 only queue inside the journal and make every write slower. The real ceiling is the journal's: 12 writes / 0.004 s = 3,000 transfers a second, whatever the forecast says.", "code": "", "lang": ""},
   {"say": "Size from the scarce resource, and let the rejection policy handle the rest. At 3,000 a second, 100 ms of waiting is 300 slots. Above that rate, the doorman turns transfers away and counts them, and customers get a fast \"busy, try again\".",
    "code": """// 3. the journal takes 12 writes at once: that sets the threads, and the throughput
PoolPlan capped = new PoolPlan(12, 300);   // 12 / 0.004 s = 3,000 a second; 3,000 x 0.1 s = 300 slots
LedgerService service = LedgerService.start(ledger, journal, capped);""",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": """// 3. the journal takes 12 writes at once: that sets the threads, and the throughput
val capped = PoolPlan(12, 300)   // 12 / 0.004 s = 3,000 a second; 3,000 x 0.1 s = 300 slots
val service = LedgerService.start(ledger, journal, capped)"""},
   {"say": "If 3,000 isn't enough, more threads won't help, because the journal is the bottleneck, the narrowest point everything passes through. Make each write carry more instead. Writing a batch of transfers to disk in one go (often called group commit) raises what 12 writes at once can carry. Then check shutdown again: 300 queued transfers on 12 threads at 4 ms drain in 100 ms, so a 5 s grace period still fits well inside the usual 30 s.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Put the ledger on a pool, drain it, and publish snapshots",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/PoolPlan.java", f"{lab}/main/{P}/LedgerService.java", f"{lab}/main/{P}/Ledger.java",
            f"{lab}/main/{P}/BalanceSnapshot.java", f"{lab}/main/{P}/Journal.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l02.*'",
  "steps": [
   "Run the tests once. All eight fail. `Ledger.apply` is already lesson 1's solution. Read the comments at the top of `Ledger`: they name the happens-before rule for every field, like the table in the snapshot section.",
   "Write `PoolPlan.fromLittlesLaw`, Little's law in whole numbers: `Math.ceilDiv(perSecond * d.toNanos(), 1_000_000_000L)` for both numbers, and never less than 1.",
   "Write `LedgerService.start` (the pool from the first section), `submit` (a `TransferTask` that writes the journal and then applies, passed to `pool.execute`) and `CountingAbortPolicy.rejectedExecution` (count, then throw).",
   "Write `LedgerService.shutdown` in the closing-time order: `shutdown`, `awaitTermination`, then `shutdownNow`; cancel and collect each `TransferTask`, wait once more, and report.",
   "Write `Ledger.snapshot`: lock every account in `inLockOrder`, copy the balances, build the snapshot with `++version`, write `latest`, and release the locks in reverse order in a `finally`.",
   "Run the tests until all eight pass, then twice more."
  ],
  "hints": [
   "Use `pool.execute(task)`, not `pool.submit(task)`. `submit` would wrap your `TransferTask` in another `FutureTask`, and `shutdownNow()` would hand back that wrapper.",
   "The shutdown test's journal waits until it is interrupted. If your `shutdown` hangs, check that you call `shutdownNow()` when the first `awaitTermination` returns `false`.",
   "If the torn-snapshot test fails, check that you take every lock before you read any balance, and release none until the snapshot is built and published.",
   "`perSecond * timePerTransfer.toNanos()` multiplies an `int` by a `long`, so Java computes it as a `long`. It doesn't overflow at these sizes."
  ],
  "done_when": "All eight tests in `LedgerServiceTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the drain-then-hand-back shutdown from memory",
  "minutes": 5,
  "prompt": "Close the lab. Write `List<Runnable> stop(ExecutorService pool, Duration grace)`: stop taking new work, let the queue drain for at most `grace`, then interrupt what is still running and return the tasks that never started, after cancelling any of them that are futures. If you are interrupted while waiting, keep the interrupt flag set.",
  "answer": {"lang": "java", "src": """List<Runnable> stop(ExecutorService pool, Duration grace) {
    pool.shutdown();                                         // no new work; the queue keeps draining
    try {
        if (pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)) return List.of();
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();                  // keep the flag, then stop hard
    }
    List<Runnable> neverStarted = pool.shutdownNow();        // interrupts the running tasks
    for (Runnable r : neverStarted) {
        if (r instanceof Future<?> f) f.cancel(false);       // a caller blocked in get() wakes up
    }
    return neverStarted;                                     // log them, or replay them
}""",
   "alt": {"lang": "kotlin", "src": """fun stop(pool: ExecutorService, grace: Duration): List<Runnable> {
    pool.shutdown()                                          // no new work; the queue keeps draining
    try {
        if (pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)) return emptyList()
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()                   // keep the flag, then stop hard
    }
    val neverStarted = pool.shutdownNow()                    // interrupts the running tasks
    neverStarted.forEach { (it as? Future<*>)?.cancel(false) }   // a caller blocked in get() wakes up
    return neverStarted                                      // log them, or replay them
}"""}}
 },
 "recap": [
  "Size a pool with Little's law: threads = peak rate x time per task, queue = peak rate x the longest wait you accept. Then check what sits behind the pool, whose own limit may be lower.",
  "Bound the queue, set core equal to max, name the threads, and choose the rejection policy on purpose: for money, count and throw, never drop.",
  "Shut down in order: `shutdown`, `awaitTermination` with a deadline, then `shutdownNow`. Cancel what it returns, and log or replay those transfers. None may vanish.",
  "Journal first, apply second, and never wait inside `apply`. Then an interrupt can only stop a transfer that hasn't changed anything yet.",
  "A sum of separately locked reads is torn. A whole snapshot holds every lock in the global order, copies, and publishes a record that never changes through one volatile write.",
  "Where this pool stops: it suits short journal writes, not requests that mostly wait. And a pool stuck waiting on itself shows only as named threads parked on a `FutureTask`, with no deadlock report."
 ],
 "closing": """We started at the bank's busy hour with a pool nobody could explain. Now every number has a reason: 8 threads for 1,600 transfers a second at 5 ms, 80 slots for 50 ms of waiting, and a doorman who counts. A closing routine loses nothing, and snapshots always add up.

Now search your own code for `Executors.newFixedThreadPool(`, and for `new LinkedBlockingQueue<>()` with no size. Each one is a rail with no end. Write down how long it may grow, and what happens when it does.

Next, we'll serve thousands of customers at once. When every request mostly waits on a slow outside check, how do we give each one its own thread and still keep every limit?""",
 "quiz": [
  {"q": "A teammate builds the ledger pool as `new ThreadPoolExecutor(8, 32, 60, SECONDS, new LinkedBlockingQueue<>())`. The journal slows from 5 ms to 500 ms per write. What happens?",
   "options": ["The pool grows to 32 threads and keeps up", "The pool stays at 8 threads and the queue grows without limit",
               "Transfers are turned away once 32 are running", "The pool shrinks back to 8 threads after 60 seconds"],
   "answer": 1,
   "why": "A pool adds threads past its core size only when the queue refuses a task, and a `LinkedBlockingQueue` with no size never refuses. So the 32 is dead code, nothing is ever turned away, and every transfer waits behind a queue that only grows. The first option is what most people expect from \"max 32\".",
   "from": "exec-02"},
  {"q": "Peak traffic is 1,200 transfers a second, and each holds a ledger thread for 10 ms. How many threads does Little's law ask for?",
   "options": ["12", "120", "1,200", "10"],
   "answer": 0,
   "why": "In flight = 1,200 a second x 0.010 s = 12. 120 would mean 100 ms per transfer, and 1,200 forgets the time entirely. After that, check that the journal can take 12 writes at once; if not, its limit is your ceiling.",
   "from": "exec-03"},
  {"q": "The snapshot job writes `latest = new BalanceSnapshot(copy, total, v)` to a plain field, not a volatile one, and request threads read `latest` without locks. What can a reader see?",
   "options": ["Always the newest snapshot, because a reference is written in one step",
               "A snapshot with some balances missing, because `Map.copyOf` copies lazily",
               "An exception, because two threads touch the same field",
               "An old snapshot, maybe for a long time, because no happens-before rule links the write to the read"],
   "answer": 3,
   "why": "Without `volatile`, nothing orders the job's write before the readers' reads, so the JIT, the part of the JVM that compiles busy code while it runs, may keep an old reference in a register, and a reader may not see a newer snapshot for a long time. The record's final fields make whatever snapshot a reader does see complete, so the risk is an old answer, not a half-built map. `Map.copyOf` copies at once. Make the field `volatile`.",
   "from": "jmm-04"},
  {"q": "Four statement tasks run on a 4-thread pool. Each submits a balance lookup to the same pool and calls `get()`. A dump shows all four threads `WAITING (parking)` on a `FutureTask`. Which fix does NOT work?",
   "options": ["Do the lookup inline in the statement task",
               "Chain with `supplyAsync(lookup, pool).thenApply(render)` and wait only at the caller",
               "Give the pool a fifth thread",
               "Run the lookups on a separate pool that never waits for the statement pool"],
   "answer": 2,
   "why": "A fifth thread only moves the hang to the fifth statement running at once, and at the end of the month there are hundreds. The other three remove the wait: inline needs no second task, chaining never holds a thread while it waits, and a separate lookup pool can't be filled up by statements.",
   "from": "exec-09"},
  {"q": "Which rejection policy fits the ledger pool when the submitting thread serves a customer who is waiting for the answer?",
   "options": ["`DiscardPolicy`, because the customer can try again",
               "A policy that counts and throws, so the customer gets a fast \"busy, try again\"",
               "`DiscardOldestPolicy`, because the newest transfer matters most",
               "`CallerRunsPolicy`, so the customer's thread writes the journal itself"],
   "answer": 1,
   "why": "A counted, thrown rejection tells the caller at once: the customer tries again with the same transfer id, and the count shows the overload on a dashboard. The discard policies drop a transfer without telling anyone, and its future never completes. `CallerRunsPolicy` suits a nightly import; here it makes one customer wait for other customers' journal writes."}
 ],
 "flashcards": [
  {"front": "Little's law for the ledger pool's thread count?", "back": "threads = peak rate x time each transfer holds a thread. 1,600 a second x 5 ms = 8."},
  {"front": "How big should the ledger pool's queue be?", "back": "Peak rate x the longest queue wait you accept: 1,600 a second x 50 ms = 80 slots. A bigger queue only hides waiting."},
  {"front": "Why is `DiscardPolicy` never right for the ledger pool?", "back": "It silently drops a transfer, and the future of a dropped `submit` never completes, so a waiting caller waits forever."},
  {"front": "What does `shutdownNow()` return, and what must you do with it?", "back": "The queued tasks that never started. Cancel their futures so waiting callers wake up, then log or replay the transfers."},
  {"front": "Why is a sum of separately locked balance reads torn?", "back": "A transfer can run between two reads and move money from an account not yet read to one already read, or back, so the sum mixes two moments."},
  {"front": "Thread-dump signature of a pool-induced deadlock?", "back": "Every thread of one pool `WAITING (parking)` on a `FutureTask` inside `get()`, tasks still queued, and no \"Found one Java-level deadlock\"."},
  {"front": "Why hand a `TransferTask` to `execute` and not `submit`?", "back": "`submit` wraps it in another `FutureTask`, so `shutdownNow()` would return the wrapper instead of your task and its transfer."}
 ],
 "terms": [
  {"term": "Journal", "plain": "A log the ledger writes to disk before it changes anything in memory, so a crash can't lose an accepted transfer. Also called a write-ahead log."},
  {"term": "Bounded queue", "plain": "A queue with a fixed size. When it is full, new work is turned away instead of waiting without limit."},
  {"term": "Rejection policy", "plain": "What a `ThreadPoolExecutor` does with a task it can't take: throw, run it on the caller's thread, or drop it."},
  {"term": "Graceful shutdown", "plain": "Stopping a program so that accepted work finishes, or is handed back, within a deadline."},
  {"term": "Torn read", "plain": "A result built from reads taken at different moments, matching no state the data was ever in."},
  {"term": "Pool-induced deadlock", "plain": "Every thread of a pool waits for tasks queued in that same pool, so none can run. No lock is involved."},
  {"term": "Thread dump", "plain": "Every thread's name, state and stack at one moment, printed by `jcmd <pid> Thread.print`."}
 ],
 "explain_back": {
  "prompt": "A colleague asks why the ledger pool has only 8 threads and 80 queue slots when the machine has memory for thousands. Explain where both numbers come from, and what happens when traffic goes above the plan.",
  "answer": "Both come from Little's law. At the planned peak of 1,600 transfers a second, each transfer holds a thread for about 5 ms while the journal writes it, so 1,600 x 0.005 = 8 transfers are in flight. Eight threads keep up, and more would only wait on the same journal. The queue absorbs bursts, but every queued transfer waits: a busy pool finishes 1,600 a second, so 80 queued transfers wait at most 50 ms, the longest wait we accept. A bigger queue would hide seconds of waiting until customers give up and try again. Above the plan, the queue fills, and the counting policy turns the extra transfers away at once: the customer gets a fast \"busy, try again\", sends the same transfer id again, and the count shows the overload on the dashboard. If that happens often, we measure the journal again and resize, or make each journal write carry more transfers."
 },
 "deeper": {
  "minutes": 10,
  "body": """Locking every account costs time in proportion to the number of accounts, and it stops every transfer while it copies. At 50 accounts that is microseconds. At five million accounts, it is a pause customers feel. Three designs avoid it.

A snapshot per group. Split the accounts into groups, send every transfer to one group, and snapshot each group on its own. The grand total is the sum of the group totals, which stays exact only while no transfer crosses from one group to another.

Copy-on-write state. Keep all balances in one map that never changes, behind an `AtomicReference`, and make every transfer a compare-and-set of a new map. Readers get a whole snapshot for free with `get()`. Writers pay for the copy and try again when another writer won, so this fits books that are read often and written rarely. It is the printed price board from Don't share: immutability, confinement, ThreadLocal, used for writes too:

```java
private final AtomicReference<Map<String, Long>> balances =
        new AtomicReference<>(Map.of("alice", 100L, "bob", 0L));

boolean transfer(String from, String to, long cents) {
    while (true) {
        Map<String, Long> now = balances.get();                   // a whole snapshot, for free
        if (now.get(from) < cents) return false;
        Map<String, Long> next = new HashMap<>(now);              // copy, change two entries
        next.merge(from, -cents, Long::sum);
        next.merge(to, cents, Long::sum);
        if (balances.compareAndSet(now, Map.copyOf(next))) return true;   // try again if another writer won
    }
}
```

```kotlin
private val balances = AtomicReference(mapOf("alice" to 100L, "bob" to 0L))

fun transfer(from: String, to: String, cents: Long): Boolean {
    while (true) {
        val now = balances.get()                                  // a whole snapshot, for free
        if (now.getValue(from) < cents) return false
        val next = now + mapOf(from to now.getValue(from) - cents, to to now.getValue(to) + cents)
        if (balances.compareAndSet(now, next)) return true        // try again if another writer won
    }
}
```

Building from the journal. Treat the journal as the truth, and a snapshot as the result of applying it up to some position. That style is called event sourcing. You can build snapshots on another machine that reads the journal, and the live ledger never stops for them.

For dumps, `jcmd <pid> Thread.dump_to_file -format=json <file>` writes the same information as JSON, a text format that tools can group and count. Lesson 3 of this track uses it on 10,000 virtual threads."""
 },
 "sources": [
  {"title": "ThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html"},
  {"title": "ExecutorService (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html"},
  {"title": "Java Language Specification, chapter 17: Threads and Locks", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "HotSpot diagnostic commands (diagnosticCommand.hpp, jdk-27-ga)", "url": "https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp"}
 ]
}

out = ROOT / "content/lessons/cap1-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
