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
    'and the rest are counted and rejected; each thread journals first, then applies">'
    '<text class="t-s t-m" x="20" y="24">peak: 1,600 transfers a second, 5 ms each</text>'
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
    '<rect class="box-bad" x="170" y="220" width="170" height="40" rx="8"/><text class="t" x="255" y="245" text-anchor="middle">rejected, counted</text>'
    '<text class="t-s t-bad" x="75" y="245" text-anchor="middle">503, Retry-After</text>'
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
 "goal": "By the end you can run the ledger on a bounded ThreadPoolExecutor whose every setting you can defend (sizes from Little's law, named threads, a rejection policy chosen on purpose), shut it down without losing a transfer, publish a balance snapshot that is never torn, and find a hung pool in a thread dump.",
 "warmup": {
  "q": "The ledger pool has 8 threads (core and max), a bounded queue of 80 slots and a policy that throws. Each transfer takes 5 ms. 300 transfers arrive within a few milliseconds. About how many are accepted?",
  "options": ["All 300: the queue makes room", "About 88: 8 running and 80 waiting", "About 8: one per thread", "About 80: the size of the queue"],
  "answer": 1,
  "why": "From *Inside ThreadPoolExecutor: core, max, queue, rejection*: the 8 core threads take the first 8 tasks, the next 80 fill the queue, and with core equal to max the pool can't grow, so the other 212 go to the rejection policy. The demo in this lesson accepts exactly 88, because submitting 300 tasks takes less time than the first 5 ms transfer."
 },
 "sections": [
  {
   "h": "Every pool setting is a decision",
   "body": """Lesson 1's ledger is correct on any number of threads. Now it needs threads to run on. In production a transfer does more than change two numbers. It first appends to a **journal**, a write-ahead log on disk, so a crash can't lose a transfer that a caller was told was accepted. Say that write takes 5 ms. The ledger needs a pool for that work, and the default pools are each wrong in their own way. `Executors.newFixedThreadPool(8)` has an unbounded queue, so a slow disk turns into millions of queued transfers and an out-of-memory error. `Executors.newCachedThreadPool()` has no thread limit, so the same slow disk turns into thousands of threads.

Build the pool yourself and write down a reason for each setting:

```java
PoolPlan plan = PoolPlan.fromLittlesLaw(1_600, Duration.ofMillis(5), Duration.ofMillis(50));   // 8 and 80
ThreadPoolExecutor pool = new ThreadPoolExecutor(
        plan.threads(), plan.threads(),                    // core == max: no burst threads
        0, TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(plan.queueCapacity()),    // bounded: a full queue pushes back
        Thread.ofPlatform().name("ledger-", 0).factory(),  // ledger-0, ledger-1, ... in every dump
        new CountingAbortPolicy());                        // counted, then thrown at the caller
pool.prestartAllCoreThreads();
```

```kotlin
val plan = PoolPlan.fromLittlesLaw(1_600, Duration.ofMillis(5), Duration.ofMillis(50))      // 8 and 80
val pool = ThreadPoolExecutor(
    plan.threads(), plan.threads(),                        // core == max: no burst threads
    0, TimeUnit.MILLISECONDS,
    ArrayBlockingQueue(plan.queueCapacity()),              // bounded: a full queue pushes back
    Thread.ofPlatform().name("ledger-", 0).factory(),      // ledger-0, ledger-1, ... in every dump
    CountingAbortPolicy())                                 // counted, then thrown at the caller
pool.prestartAllCoreThreads()
```

The sizes come from Little's law, from *Sizing a pool: CPU-bound, IO-bound and Little's law*: in flight = arrival rate x time in the system. At a peak of 1,600 transfers a second, each holding a thread for 5 ms, 1,600 x 0.005 = 8 transfers are in flight, so 8 threads. With fewer, the queue grows at every peak. With many more, you only add threads that wait on the same disk.

The queue gets the same law. A busy pool finishes 1,600 transfers a second, so 80 queued transfers drain in 80 / 1,600 = 50 ms. If 50 ms is the longest a transfer should wait for a thread, 80 slots is the most the queue should hold. A queue of 10,000 would hide six seconds of waiting behind a client's timeout.

Core equals max because extra threads would only add waiters on the same journal, and the pool grows past core only when the queue is full. Here, the right answer to a full queue is no.

That makes the rejection policy the last decision. `DiscardPolicy` and `DiscardOldestPolicy` drop a transfer, so they are never right for money. `CallerRunsPolicy` makes the submitting thread write the journal itself: fine for a batch importer, wrong for an HTTP thread with a client waiting. For the API path, count and throw. The handler answers 503 with `Retry-After`, the client retries with the same transfer id, and the counter shows on the dashboard.""",
   "figure": {"svg": FIGURE, "caption": "Little's law sizes both halves of the pool: 8 threads for the transfers in flight, 80 slots for 50 ms of waiting. Whatever doesn't fit is rejected and counted."},
   "try": {
    "title": "Send a burst at the pool",
    "minutes": 4,
    "steps": [
     "Run `BurstDemo`: 300 transfers of 5 ms each arrive at once at the pool above. Predict how many are accepted and how long submitting takes.",
     "Run it with `-Pargs=callerRuns`. Predict how many transfers the submitting thread runs itself, and how long submitting takes now."
    ],
    "code": demo("BurstDemo"),
    "expect": "With the counting abort policy, 88 are accepted (8 running, 80 queued) and 212 are rejected within a few milliseconds; the accepted ones are done after roughly 60 to 120 ms (88 x 5 ms / 8 threads, plus start-up). With `CallerRunsPolicy` nothing is rejected, but the submitting thread ran 24 transfers itself and submitting took about 130 ms instead of 4. While it writes a journal entry it can't submit, which is the back-pressure. If that thread were serving an HTTP request, its client would have waited all that time for other people's transfers."
   },
   "refs": [
    {"title": "ThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html", "kind": "docs"}
   ]
  },
  {
   "h": "Shut down by draining, and account for every transfer",
   "body": """A deploy stops the ledger while transfers are queued, and each of them belongs to a caller who was told "accepted". So the rule for shutdown is this: when it ends, every accepted transfer has been applied, has failed with an error its caller saw, or has been handed back to you by id. None may vanish.

`pool.shutdownNow()` on its own breaks that rule. It interrupts the running tasks and returns the queued ones as a `List<Runnable>`. Ignore the list and those transfers are gone. Worse, their futures never complete, so a caller blocked in `get()` waits forever. In this section's demo a bare `shutdownNow()` loses 992 of 1,000 transfers.

The order from *Pools in production: names, errors, context, shutdown* fixes it:

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

Two details make this work. First, the queue must hold objects that know their transfer. `pool.submit(callable)` wraps your work in an anonymous `FutureTask`, so the lab's `submit` builds a `TransferTask`, a `FutureTask` subclass with a `transfer()` accessor, and hands it to `execute`. Then `shutdownNow()` gives you back transfers instead of mystery `Runnable`s.

Second, an interrupted task must leave nothing half-done. Each task writes the journal first and changes memory second. An interrupt during the write means the transfer was never applied: its future fails with the `InterruptedException`, and no balance changed. `apply` itself never blocks, so once it starts, it finishes.

Size the grace period from the same numbers as the pool. A full queue of 80 drains in 50 ms, so a few seconds of grace fits easily inside the 30 seconds Kubernetes gives a pod by default.""",
   "try": {
    "title": "Lose transfers, then stop losing them",
    "minutes": 4,
    "steps": [
     "Run `ShutdownDemo -Pargs=naive`: 1,000 accepted transfers, then a bare `shutdownNow()`. Read the `lost` column and the last line.",
     "Run it with no arguments (drain, 100 ms of grace), then with `-Pargs='drain 5000'`. Before each run, predict how many transfers are applied."
    ],
    "code": demo("ShutdownDemo"),
    "expect": "Naive: about 990 lost, and as many futures that will never complete, so their callers would hang. Drain with 100 ms: about 160 applied (8 threads x 20 rounds of 5 ms), 8 interrupted in the middle of their journal write, the rest handed back, and 0 lost. With 5 s of grace all 1,000 are applied, because they need only about 625 ms on 8 threads."
   },
   "refs": [
    {"title": "ExecutorService (Java SE 25 API): the shutdown idiom", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html", "kind": "docs"}
   ]
  },
  {
   "h": "Publish a snapshot nobody can tear",
   "body": """The balances endpoint wants every balance at once, and invariant 1 says they must add up to the opening total. Reading the accounts one at a time, each under its own lock, doesn't give you that:

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

A transfer from account 40 to account 3 can run after you read 3 and before you read 40. Then you counted that money in neither account. In the other direction you count it twice. In the demo, a large share of such sums were wrong, by up to 13,957 cents, although no transfer ever broke an invariant. A sum like that is **torn**: it mixes two moments.

A consistent snapshot needs one instant at which no transfer is half done. Lock every account, in the same id order that `apply` uses so the snapshot can't deadlock with a transfer, copy the balances, then release:

```java
public BalanceSnapshot snapshot() {
    for (Account a : inLockOrder) a.lock().lock();                 // 1. every lock, in id order
    try {
        Map<String, Long> copy = new HashMap<>();
        long total = 0;
        for (Account a : inLockOrder) { copy.put(a.id(), a.balance()); total += a.balance(); }
        BalanceSnapshot s = new BalanceSnapshot(copy, total, ++version);   // 2. immutable
        latest = s;                                                // 3. volatile write: published whole
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
        val s = BalanceSnapshot(copy, copy.values.sum(), ++version) // 2. immutable
        latest = s                                                 // 3. @Volatile write: published whole
        return s
    } finally {
        inLockOrder.asReversed().forEach { it.lock.unlock() }
    }
}
```

For 50 accounts this pauses transfers for microseconds, and readers call `latestSnapshot()` without taking any lock. *Happens-before, the rules that matter* asked you to name the edge for every shared field. Here they are:

| Field | Why every reader sees it correctly |
|---|---|
| `Account.balance` | the account's lock: each release happens-before the next acquire |
| `accounts`, `inLockOrder` | final fields, set in the constructor, never changed |
| `version` | written only while every account lock is held |
| `latest` | volatile: its write happens-before every later read |
| a snapshot's `balances` and `total` | final fields of a record, holding a map that `Map.copyOf` made unmodifiable |
| a `Transfer` in the pool | immutable, and `execute` happens-before the task runs |
| a transfer's outcome | the task's completion happens-before `Future.get()` returns |

Writing `latest` before the locks are released keeps snapshots in version order: two snapshots can't overlap, because each needs every lock.""",
   "try": {
    "title": "Tear a snapshot, then make it whole",
    "minutes": 3,
    "steps": [
     "Run `TornSnapshotDemo`. Four threads move money while the main thread adds up all 50 balances, one locked account at a time. Predict how many sums come out wrong.",
     "Run it with `-Pargs=locked`, where the reader holds every lock while it adds."
    ],
    "code": demo("TornSnapshotDemo"),
    "expect": "One account at a time, many sums are wrong (7,241 of 9,456 in one Java run here, 1,226 of 6,239 in a Kotlin run), some by thousands of cents, while every transfer kept the books balanced. With every lock held, no sum is torn. A real service wouldn't let every request take all the locks: it takes one snapshot every few hundred milliseconds and lets readers share it through `latestSnapshot()`."
   }
  },
  {
   "h": "Find a hung pool in a thread dump",
   "body": """Here is a bug that passes every test with a small batch. A month-end statement job runs on the ledger pool, and each statement asks the same pool for a balance:

```java
pool.submit(() -> {
    Future<Long> balance = pool.submit(() -> balanceOf(merchant));   // a task inside a task
    return merchant + ": " + balance.get();                          // waits for it
});
```

```kotlin
pool.submit(Callable {
    val balance = pool.submit(Callable { balanceOf(merchant) })      // a task inside a task
    "$merchant: ${balance.get()}"                                    // waits for it
})
```

With 2 threads and 3 merchants, the first two statements take both threads. Each submits a balance lookup, which queues behind the third statement. Now both threads wait for tasks that need a free thread, and no thread will ever be free. *Pools in production: names, errors, context, shutdown* called this pool-induced deadlock. This section is about finding it in a running process.

Start `PoolHangDemo` with a long hang, then dump its threads from a second terminal:

```bash
jcmd                          # lists Java processes and their PIDs
jcmd <pid> Thread.print -l    # -l adds the java.util.concurrent locks each thread holds
```

Here is the part that matters, from a real run on JDK 21, trimmed:

```text
""" + DUMP + """
```

Read each thread in the same order. The name says which pool: both `ledger-` threads are stuck, which is why the factory names them. The state, `WAITING (parking)`, means `java.util.concurrent` parked them; a thread stuck on `synchronized` would say `BLOCKED`. The `parking to wait for` line names the object they wait on: a `FutureTask`, so they are inside `get()`. The first frame from your own code, `statement` at line 33, is that `get()` call. And under `Locked ownable synchronizers` each worker holds its own `ThreadPoolExecutor$Worker`, a lock a worker holds while it runs a task. Both threads are busy, and busy waiting.

Notice what is missing: the dump never says `Found one Java-level deadlock`. The JVM's detector looks for cycles of monitors and `ReentrantLock`s, and here nobody holds a lock that anybody else wants. Every worker of one pool parked on a `FutureTask` of that same pool, with tasks still queued, is the signature to learn. The fixes come from that lesson: do the lookup inline, compose with `thenApply` instead of blocking, or give lookups their own pool.""",
   "try": {
    "title": "Take the dump yourself",
    "minutes": 5,
    "steps": [
     "Run `PoolHangDemo` with `-Pargs=60` so it stays hung for a minute. It prints its PID.",
     "In a second terminal, run `jcmd <pid> Thread.print -l`. For both `ledger-` threads, find the state, the `parking to wait for` line, the first frame from `workbench.ledger`, and the `Locked ownable synchronizers`. Then find `main`.",
     "Scroll to the end of the dump. Is there a deadlock report? Explain why not.",
     "Change `statement` to call `balanceOf(merchant)` directly instead of submitting it, and run the demo again."
    ],
    "code": demo("PoolHangDemo"),
    "expect": "Both `ledger-0` and `ledger-1` are `WAITING (parking)` on a `FutureTask` inside `PoolHangDemo.statement`, each holding its `ThreadPoolExecutor$Worker`, and `main` is `TIMED_WAITING (sleeping)` in `Thread.sleep`. There is no deadlock report, because no thread holds a lock another thread wants. When the sleep ends the demo prints `active=2, queued=3, completed=0`: the third statement and both lookups never ran. With the lookup inline, it prints `completed=3`. The Kotlin twin shows the same dump with `PoolHangDemoKt.statement` as your frame."
   }
  }
 ],
 "analogy": "A pool is a bank branch with eight tellers and a waiting area with eighty chairs. When every chair is taken, the guard at the door tells the next customer to come back in a minute and makes a tally mark (the counting rejection). Hiring a teller for every customer, or letting the queue spill out into the street, only looks kind. At closing time the guard locks the door, the tellers finish the people already seated, and anyone still waiting at the deadline gets a numbered ticket for tomorrow instead of being sent home with nothing. The analogy breaks at the statement job: a real teller who needs a colleague's help walks over and asks. A pool thread that waits for a task in its own queue just stands at its desk, and so do all the others.",
 "in_your_world": "Quarkus runs blocking endpoints on a worker pool whose size you set with `quarkus.thread-pool.max-threads`, and the argument for that number is this lesson's: in flight = rate x time, with the time measured under load. When Kubernetes stops a pod it sends `SIGTERM` and waits `terminationGracePeriodSeconds` (30 by default), so fail the readiness probe first, drain the ledger pool within a deadline inside that window, and log the ids of any transfer handed back so someone can replay it. A Temporal worker's limit on concurrent activities is a pool size too: size it from the activity's rate and duration in the same way, and watch for activities that block waiting on work that needs the same slots.",
 "mistake": "The most common mistake is an unbounded queue: `Executors.newFixedThreadPool(n)`, or a `LinkedBlockingQueue` with no capacity. Nothing is ever rejected, so tests and dashboards look healthy while a slow disk or database grows the queue by thousands of transfers a second. Latency climbs to minutes, clients time out and retry, which adds more work, and the pod finally dies of memory with its queue full of transfers that callers were told were accepted. People choose it because it is the default and because rejecting feels worse than waiting. Bound the queue from Little's law, and turn the overflow into a counted, visible rejection.",
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
  "note": "Nothing here is specific to either language: `ThreadPoolExecutor`, `ArrayBlockingQueue` and `Thread.ofPlatform()` are the same JDK classes, with the same rules. Kotlin shortens the `FutureTask` subclass to one line, because the constructor parameter `work` goes straight to the superclass in the class header, and a trailing lambda converts to the Java `Callable`. When you call `pool.submit` with a bare lambda, Kotlin has to choose between `submit(Runnable)` and `submit(Callable)`; writing `Callable { ... }` says which you mean. In coroutine code, `Dispatchers.IO.limitedParallelism(8)` caps parallelism like this pool, but it queues without a bound and never rejects, so it can't replace the back-pressure."
 },
 "worked": {
  "title": "Size the pool for a new peak",
  "steps": [
   {"say": "The sales forecast for a promotion day is 4,000 transfers a second. Under load the journal's write takes 4 ms. You want no transfer to wait more than 100 ms for a thread. Start with Little's law, for both halves of the pool.",
    "code": """// 1. peak rate, time each transfer holds a thread, longest acceptable queue wait
PoolPlan plan = PoolPlan.fromLittlesLaw(4_000, Duration.ofMillis(4), Duration.ofMillis(100));
// 2. 4,000/s x 0.004 s = 16 in flight; 4,000/s x 0.1 s = 400 waiting
System.out.println(plan);   // PoolPlan[threads=16, queueCapacity=400]""",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": """// 1. peak rate, time each transfer holds a thread, longest acceptable queue wait
val plan = PoolPlan.fromLittlesLaw(4_000, Duration.ofMillis(4), Duration.ofMillis(100))
// 2. 4,000/s x 0.004 s = 16 in flight; 4,000/s x 0.1 s = 400 waiting
println(plan)   // PoolPlan[threads=16, queueCapacity=400]"""},
   {"say": "Now check the downstream, as *Sizing a pool: CPU-bound, IO-bound and Little's law* insisted. The storage team says the journal volume handles 12 concurrent writes before each one slows down. With 16 threads, the extra 4 just queue inside the journal and make every write slower. The real ceiling is the journal's: 12 writes / 0.004 s = 3,000 transfers a second, whatever the forecast says.", "code": "", "lang": ""},
   {"say": "Size from the scarce resource, and let the rejection policy handle the rest. At 3,000 a second, 100 ms of queue is 300 slots. Above that rate the pool rejects and counts, and the API answers 503 with `Retry-After`.",
    "code": """// 3. the journal takes 12 writes at once: that sets the threads, and the throughput
PoolPlan capped = new PoolPlan(12, 300);   // 12 / 0.004 s = 3,000 a second; 3,000 x 0.1 s = 300 slots
LedgerService service = LedgerService.start(ledger, journal, capped);""",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": """// 3. the journal takes 12 writes at once: that sets the threads, and the throughput
val capped = PoolPlan(12, 300)   // 12 / 0.004 s = 3,000 a second; 3,000 x 0.1 s = 300 slots
val service = LedgerService.start(ledger, journal, capped)"""},
   {"say": "If 3,000 isn't enough, more threads won't help, because the journal is the bottleneck. Make each write do more: group commit (one disk flush for a batch of transfers) raises what 12 concurrent writes can carry. Then check shutdown again: 300 queued transfers on 12 threads at 4 ms drain in 100 ms, so a 5 s grace period still fits well inside Kubernetes' 30 s.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Put the ledger on a pool, drain it, and publish snapshots",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/PoolPlan.java", f"{lab}/main/{P}/LedgerService.java", f"{lab}/main/{P}/Ledger.java",
            f"{lab}/main/{P}/BalanceSnapshot.java", f"{lab}/main/{P}/Journal.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l02.*'",
  "steps": [
   "Run the tests once. All eight fail. `Ledger.apply` is already lesson 1's solution. Read the field comments at the top of `Ledger`: they name the happens-before edge for every field.",
   "Write `PoolPlan.fromLittlesLaw`: `Math.ceilDiv(perSecond * d.toNanos(), 1_000_000_000L)` for both numbers, and never less than 1.",
   "Write `LedgerService.start` (the pool from section 1), `submit` (a `TransferTask` that appends to the journal and then applies, passed to `pool.execute`) and `CountingAbortPolicy.rejectedExecution` (count, then throw).",
   "Write `LedgerService.shutdown` in the order from section 2: `shutdown`, `awaitTermination`, then `shutdownNow`, cancel and collect each `TransferTask`, wait once more, and report.",
   "Write `Ledger.snapshot`: lock every account in `inLockOrder`, copy the balances, build the snapshot with `++version`, write `latest`, and release in reverse order in a `finally`.",
   "Run the tests until all eight pass, then twice more."
  ],
  "hints": [
   "Use `pool.execute(task)`, not `pool.submit(task)`. `submit` would wrap your `TransferTask` in another `FutureTask`, and `shutdownNow()` would hand back that wrapper.",
   "The shutdown test's journal blocks until it is interrupted. If your `shutdown` hangs, check that you call `shutdownNow()` when the first `awaitTermination` returns `false`.",
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
  "Size a pool with Little's law: threads = peak rate x time per task, queue = peak rate x the longest wait you accept. Then check the downstream's own limit, which may be lower.",
  "Bound the queue, set core equal to max, name the threads, and choose the rejection policy on purpose: for money on the API path, count and throw, never discard.",
  "Shut down in order: `shutdown`, `awaitTermination` with a deadline, then `shutdownNow`; cancel what it returns and log or replay those transfers. None may vanish.",
  "Journal first, apply second, and never block inside `apply`. Then an interrupt can only stop a transfer that hasn't changed anything yet.",
  "A sum of separately locked reads is torn. A consistent snapshot holds every lock in the global order, copies, and publishes an immutable record through a volatile field.",
  "A pool hung on its own tasks shows every named worker `WAITING (parking)` on a `FutureTask` in `get()`, each holding its `Worker` lock, and no deadlock report."
 ],
 "quiz": [
  {"q": "A teammate builds the ledger pool as `new ThreadPoolExecutor(8, 32, 60, SECONDS, new LinkedBlockingQueue<>())`. The journal slows from 5 ms to 500 ms per write. What happens?",
   "options": ["The pool grows to 32 threads and keeps up", "The pool stays at 8 threads and the queue grows without limit",
               "Transfers are rejected once 32 are running", "The pool shrinks back to 8 threads after 60 seconds"],
   "answer": 1,
   "why": "The pool grows past core only when the queue refuses a task, and an unbounded `LinkedBlockingQueue` never refuses. So the 32 is dead code, nothing is ever rejected, and every transfer waits behind a queue that only grows. Option 1 is what most people expect from \"max 32\".",
   "from": "exec-02"},
  {"q": "Peak traffic is 1,200 transfers a second, and each holds a ledger thread for 10 ms. How many threads does Little's law ask for?",
   "options": ["12", "120", "1,200", "10"],
   "answer": 0,
   "why": "In flight = 1,200/s x 0.010 s = 12. 120 would mean 100 ms per transfer, and 1,200 forgets the time entirely. After that, check that the journal can take 12 writes at once; if not, its limit is your ceiling.",
   "from": "exec-03"},
  {"q": "The snapshot refresher writes `latest = new BalanceSnapshot(copy, total, v)` to a plain field, not a volatile one, and request threads read `latest` without locks. What can a reader see?",
   "options": ["Always the newest snapshot, because reference writes are atomic",
               "A snapshot with some balances missing, because `Map.copyOf` copies lazily",
               "An exception, because two threads touch the same field",
               "An old snapshot, possibly for a long time, because no happens-before edge links the write to the read"],
   "answer": 3,
   "why": "Without `volatile` nothing orders the refresher's write before the readers' reads, so the JIT may keep an old reference in a register, and a reader may not see a newer snapshot for a long time. The record's final fields make whatever snapshot a reader does see complete, so the risk is staleness, not a half-built map. `Map.copyOf` copies at once. Make the field `volatile`.",
   "from": "jmm-04"},
  {"q": "Four statement tasks run on a 4-thread pool. Each submits a balance lookup to the same pool and calls `get()`. A dump shows all four workers `WAITING (parking)` on a `FutureTask`. Which fix does NOT work?",
   "options": ["Do the lookup inline in the statement task",
               "Compose with `supplyAsync(lookup, pool).thenApply(render)` and join only at the caller",
               "Give the pool a fifth thread",
               "Run the lookups on a separate pool that never waits for the statement pool"],
   "answer": 2,
   "why": "A fifth thread only moves the hang to the fifth statement running at once, and at month-end there are hundreds. The other three remove the wait: inline needs no second task, composition never holds a thread while it waits, and a separate lookup pool can't be starved by statements.",
   "from": "exec-09"},
  {"q": "Which rejection policy fits the ledger pool when the submitting thread is an HTTP request thread with a client waiting?",
   "options": ["`DiscardPolicy`, because the client can retry",
               "A policy that counts and throws, so the handler answers 503 with Retry-After",
               "`DiscardOldestPolicy`, because the newest transfer matters most",
               "`CallerRunsPolicy`, so the request thread writes the journal itself"],
   "answer": 1,
   "why": "A counted, thrown rejection tells the caller at once: the client retries with the same transfer id, and the counter shows the overload on a dashboard. The discard policies drop a transfer without telling anyone, and its future never completes. `CallerRunsPolicy` suits a batch importer; here it makes one client wait for other clients' journal writes."}
 ],
 "flashcards": [
  {"front": "Little's law for the ledger pool's thread count?", "back": "threads = peak rate x time each transfer holds a thread. 1,600/s x 5 ms = 8."},
  {"front": "How big should the ledger pool's queue be?", "back": "Peak rate x the longest queue wait you accept: 1,600/s x 50 ms = 80 slots. A bigger queue only hides latency."},
  {"front": "Why is `DiscardPolicy` never right for the ledger pool?", "back": "It silently drops a transfer, and the future of a dropped `submit` never completes, so a waiting caller hangs."},
  {"front": "What does `shutdownNow()` return, and what must you do with it?", "back": "The queued tasks that never started. Cancel the futures so waiting callers wake up, then log or replay the transfers."},
  {"front": "Why is a sum of separately locked balance reads torn?", "back": "A transfer can run between two reads and move money from an unread account to a read one, or back, so the sum mixes two moments."},
  {"front": "Thread-dump signature of a pool-induced deadlock?", "back": "Every worker of one pool `WAITING (parking)` on a `FutureTask` inside `get()`, tasks still queued, and no \"Found one Java-level deadlock\"."},
  {"front": "Why hand a `TransferTask` to `execute` and not `submit`?", "back": "`submit` wraps it in another `FutureTask`, so `shutdownNow()` would return the wrapper instead of your task and its transfer."}
 ],
 "terms": [
  {"term": "Bounded queue", "plain": "A queue with a fixed capacity. When it is full, new work is rejected instead of waiting without limit."},
  {"term": "Rejection policy", "plain": "What a `ThreadPoolExecutor` does with a task it can't take: throw, run it on the caller's thread, or drop it."},
  {"term": "Write-ahead journal", "plain": "A log the ledger writes to disk before it changes anything in memory, so a crash can't lose an accepted transfer."},
  {"term": "Graceful shutdown", "plain": "Stopping a service so that accepted work finishes, or is handed back, within a deadline."},
  {"term": "Torn read", "plain": "A result built from reads taken at different moments, matching no state the data was ever in."},
  {"term": "Pool-induced deadlock", "plain": "Every thread of a pool waits for tasks queued in that same pool, so none can run. No lock is involved."},
  {"term": "Thread dump", "plain": "Every thread's name, state and stack at one moment, printed by `jcmd <pid> Thread.print`."}
 ],
 "explain_back": {
  "prompt": "An on-call engineer asks why the ledger pool has only 8 threads and 80 queue slots when the machine has memory for thousands. Explain where both numbers come from, and what happens when traffic goes above the plan.",
  "answer": "Both come from Little's law. At the planned peak of 1,600 transfers a second, each transfer holds a thread for about 5 ms while the journal writes it, so 1,600 x 0.005 = 8 transfers are in flight. Eight threads keep up, and more would only wait on the same journal. The queue absorbs bursts, but every queued transfer waits: a busy pool finishes 1,600 a second, so 80 queued transfers wait at most 50 ms, the longest wait we accept. A bigger queue would hide seconds of latency until clients time out and retry. Above the plan the queue fills, and the counting policy rejects the extra transfers at once: the API answers 503 with Retry-After, the client retries with the same transfer id, and the rejection counter shows the overload. If that happens often, we measure the journal again and resize, or make each journal write cheaper."
 },
 "deeper": {
  "minutes": 10,
  "body": """Locking every account costs time in proportion to the number of accounts, and it stops every writer while it copies. At 50 accounts that is microseconds. At five million accounts it is a pause your clients feel. Three designs avoid it.

Snapshot per shard. Split the accounts into shards, route every transfer to one shard, and snapshot each shard on its own. The grand total is the sum of the shard totals, which is only consistent while no transfer crosses a shard.

Copy-on-write state. Keep all balances in an immutable map behind an `AtomicReference`, and make every transfer a compare-and-set of a new map. Readers get a consistent snapshot for free with `get()`. Writers pay for the copy and retry when another writer won, so this fits read-heavy books with modest write rates. It is the snapshot idea from *Don't share: immutability, confinement, ThreadLocal*, used for writes too:

```java
private final AtomicReference<Map<String, Long>> balances =
        new AtomicReference<>(Map.of("alice", 100L, "bob", 0L));

boolean transfer(String from, String to, long cents) {
    while (true) {
        Map<String, Long> now = balances.get();                   // a consistent snapshot, for free
        if (now.get(from) < cents) return false;
        Map<String, Long> next = new HashMap<>(now);              // copy, change two entries
        next.merge(from, -cents, Long::sum);
        next.merge(to, cents, Long::sum);
        if (balances.compareAndSet(now, Map.copyOf(next))) return true;   // retry if another writer won
    }
}
```

```kotlin
private val balances = AtomicReference(mapOf("alice" to 100L, "bob" to 0L))

fun transfer(from: String, to: String, cents: Long): Boolean {
    while (true) {
        val now = balances.get()                                  // a consistent snapshot, for free
        if (now.getValue(from) < cents) return false
        val next = now + mapOf(from to now.getValue(from) - cents, to to now.getValue(to) + cents)
        if (balances.compareAndSet(now, next)) return true        // retry if another writer won
    }
}
```

Event sourcing. Treat the journal as the truth and a snapshot as the result of applying it up to a position. You can build snapshots on a replica that reads the journal, and the live ledger never stops for them.

For dumps, `jcmd <pid> Thread.dump_to_file -format=json <file>` writes the same information as JSON, which tools can group and count. Lesson 3 of this track uses it on 10,000 virtual threads."""
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
