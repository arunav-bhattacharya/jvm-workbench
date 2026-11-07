import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ledger/src"
PK = "kotlin/workbench/ledger/l03"
PJ = "java/workbench/ledger/l03"
DJ = "java/workbench/ledger/l03/demo"
DK = "kotlin/workbench/ledger/l03/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ledger:demo -Pmain=workbench.ledger.l03.demo."


def demo(name):
    """A Kotlin demo with its runnable Java twin (FooJava.java), both read from disk."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


FIGURE = (
    '<svg viewBox="0 0 700 290" role="img" aria-label="Each request gets its own virtual thread with one 300 ms deadline. '
    'It calls the fraud service through a 20-permit bulkhead and the limits check at the same time, then hands the transfer '
    'to the bounded ledger pool, which journals and applies it">'
    '<rect class="box" x="20" y="110" width="120" height="44" rx="8"/><text class="t" x="80" y="137" text-anchor="middle">10,000 requests</text>'
    '<line class="ln" x1="140" y1="132" x2="168" y2="132" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="245" y="92" text-anchor="middle">one deadline: 300 ms</text>'
    '<rect class="box-a" x="170" y="100" width="150" height="64" rx="8"/>'
    '<text class="t" x="245" y="128" text-anchor="middle">virtual thread</text>'
    '<text class="t-s t-m" x="245" y="148" text-anchor="middle">one per request</text>'
    '<line class="ln" x1="320" y1="120" x2="348" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln" x1="320" y1="132" x2="348" y2="132" marker-end="url(#arr)"/>'
    '<line class="ln" x1="320" y1="148" x2="348" y2="222" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="350" y="32" width="160" height="48" rx="8"/><text class="t" x="430" y="61" text-anchor="middle">fraud: 20 permits</text>'
    '<rect class="box" x="350" y="108" width="160" height="48" rx="8"/><text class="t" x="430" y="137" text-anchor="middle">limits check</text>'
    '<rect class="box-a" x="350" y="198" width="160" height="48" rx="8"/><text class="t" x="430" y="227" text-anchor="middle">ledger pool 8 + 80</text>'
    '<line class="ln" x1="510" y1="56" x2="538" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="540" y="32" width="140" height="48" rx="8"/><text class="t" x="610" y="61" text-anchor="middle">fraud service</text>'
    '<line class="ln" x1="510" y1="222" x2="538" y2="222" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="540" y="198" width="140" height="48" rx="8"/><text class="t" x="610" y="227" text-anchor="middle">journal, apply</text>'
    '<text class="t-s t-bad" x="430" y="22" text-anchor="middle">late: stand-in or try again</text>'
    '<text class="t-s t-bad" x="430" y="270" text-anchor="middle">queue full: 503</text>'
    '<text class="t-s t-m" x="610" y="270" text-anchor="middle">per-account locks</text>'
    '</svg>')

JSON_DUMP = """{"threadDump": {
  "processId": "29205",
  "runtimeVersion": "21.0.12.1+1-1-24.04.4-Ubuntu",
  "threadContainers": [
    {"container": "<root>", "parent": null, "owner": null, "threadCount": "7",
     "threads": [{"tid": "1", "name": "main",
                  "stack": ["java.base/java.lang.Thread.sleep0(Native Method)", "..."]}, "..."]},
    {"container": "java.util.concurrent.ThreadPerTaskExecutor@7cded998", "parent": "<root>",
     "owner": null, "threadCount": "10000",
     "threads": [
       {"tid": "19", "name": "request-0", "stack": [
         "java.base/java.lang.VirtualThread.park(VirtualThread.java:596)",
         "...",
         "java.base/java.util.concurrent.CountDownLatch.await(CountDownLatch.java:230)",
         "workbench.ledger.l03.demo.ParkedRequestsDemoKt.handle(ParkedRequestsDemo.kt:14)",
         "..."]},
       "...",
       {"tid": "10025", "name": "request-9999", "stack": [
         "java.base/java.lang.VirtualThread.park(VirtualThread.java:596)",
         "...",
         "java.base/java.util.concurrent.Semaphore.acquire(Semaphore.java:318)",
         "workbench.ledger.l03.demo.ParkedRequestsDemoKt.handle(ParkedRequestsDemo.kt:12)",
         "..."]}]},
    {"container": "ForkJoinPool-1/jdk.internal.vm.SharedThreadContainer@3ee32429",
     "parent": "<root>", "owner": null, "threadCount": "4",
     "threads": [{"tid": "20", "name": "ForkJoinPool-1-worker-1", "stack": ["..."]}, "..."]},
    "... three empty containers ..."
  ]}}"""

JQ = """jq -r '.threadDump.threadContainers[] | "\\(.threads | length)\\t\\(.container)"' /tmp/requests.json

jq -r '.threadDump.threadContainers[].threads[].stack
       | (map(startswith("workbench.")) | index(true)) as $i
       | select($i != null and $i > 0)
       | "\\(.[$i-1]) <- \\(.[$i])"' /tmp/requests.json | sort | uniq -c | sort -rn"""

GROUPED = """   9980 java.base/java.util.concurrent.Semaphore.acquire(Semaphore.java:318) <- workbench.ledger.l03.demo.ParkedRequestsDemoKt.handle(ParkedRequestsDemo.kt:12)
     20 java.base/java.util.concurrent.CountDownLatch.await(CountDownLatch.java:230) <- workbench.ledger.l03.demo.ParkedRequestsDemoKt.handle(ParkedRequestsDemo.kt:14)
      1 java.base/java.lang.Thread.sleep(Thread.java:509) <- workbench.ledger.l03.demo.ParkedRequestsDemoKt.main(ParkedRequestsDemo.kt:34)"""

SCREEN_KT = """fun screen(t: Transfer): Verdict {
    val deadline = System.nanoTime() + budget.toNanos()                 // 1. one deadline for both checks
    val perTask = Executors.newVirtualThreadPerTaskExecutor()
    try {
        val done = ExecutorCompletionService<Boolean>(perTask)
        done.submit { fraudBulkhead.call(deadline - System.nanoTime()) { fraud.passes(t) } }   // 2. fork both
        done.submit { limits.passes(t) }
        repeat(2) {
            val next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)
                ?: return fallback(t)                                    // 3. deadline passed: stand-in rule
            val passed = try {
                next.get()
            } catch (e: ExecutionException) {
                if (e.cause is TimeoutException) return fallback(t)      //    no fraud permit in time
                return Verdict.DECLINED                                  // 4. a check failed: fail fast
            }
            if (!passed) return Verdict.DECLINED                         // 4. a check said no: fail fast
        }
        return Verdict.APPROVED
    } finally {
        perTask.shutdownNow()                                            // 5. interrupt whatever still runs...
        perTask.close()                                                  //    ...and wait until those threads end
    }
}"""

SCREEN_JAVA = """Verdict screen(Transfer t) throws InterruptedException {
    long deadline = System.nanoTime() + budget.toNanos();                // 1. one deadline for both checks
    ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();
    try {
        CompletionService<Boolean> done = new ExecutorCompletionService<>(perTask);
        done.submit(() -> fraudBulkhead.call(deadline - System.nanoTime(), () -> fraud.passes(t)));   // 2. fork both
        done.submit(() -> limits.passes(t));
        for (int i = 0; i < 2; i++) {
            Future<Boolean> next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
            if (next == null) return fallback(t);                        // 3. deadline passed: stand-in rule
            try {
                if (!next.get()) return Verdict.DECLINED;                // 4. a check said no: fail fast
            } catch (ExecutionException e) {
                if (e.getCause() instanceof TimeoutException) return fallback(t);   // no fraud permit in time
                return Verdict.DECLINED;                                 // 4. a check failed: fail fast
            }
        }
        return Verdict.APPROVED;
    } finally {
        perTask.shutdownNow();                                           // 5. interrupt whatever still runs...
        perTask.close();                                                 //    ...and wait until those threads end
    }
}"""

L = {
 "id": "cap1-03",
 "title": "Serve it with virtual threads",
 "minutes": 40,
 "goal": "By the end you can serve the ledger with one virtual thread per request, cap the slow fraud check with a shared semaphore, give every request one deadline with a stand-in fallback, fan out two checks that fail fast, keep carriers free of pinning, read a JSON dump of 10,000 parked virtual threads, and defend the whole design in a review.",
 "warmup": {
  "q": "The transfer API gets 2,000 requests a second. Each spends about 150 ms waiting on the fraud service and almost nothing anywhere else. With one thread per request, about how many threads are busy at once?",
  "options": ["About 2", "About 300", "About 2,000", "About 150"],
  "answer": 1,
  "why": "Little's law from *The thread-per-request wall*: in flight = 2,000/s x 0.15 s = 300. If the fraud service slows to 2 s, the same traffic needs 4,000. Platform threads make that expensive; virtual threads make it cheap, which moves the question to what each of those requests is allowed to call."
 },
 "sections": [
  {
   "h": "One virtual thread per request, and every limit written down",
   "body": """Lesson 2's pool runs the journal writes. Requests need threads too, and they spend almost all their time waiting: on the fraud service, on the limits service, on the ledger pool. *The thread-per-request wall* gave you the number: in flight = rate x time. At 2,000 requests a second and 150 ms each, 300 requests are in flight. When the fraud service slows to 2 s, 4,000 are. A platform thread per request would mean 4,000 OS threads, each with a 1 MB stack reserved, created at the worst possible moment.

Virtual threads make that number cheap. A request that waits on a socket, a latch or a semaphore unmounts from its carrier, and its stack waits on the heap, as *How virtual threads work: carriers and continuations* showed. So the server starts one new virtual thread per request, and never pools them:

```java
List<Reply> serveAll(List<Transfer> requests) throws Exception {
    try (ExecutorService perRequest = Executors.newVirtualThreadPerTaskExecutor()) {
        List<Future<Reply>> replies = new ArrayList<>();
        for (Transfer t : requests) replies.add(perRequest.submit(() -> handle(t)));   // 1. start every request
        List<Reply> out = new ArrayList<>();
        for (Future<Reply> f : replies) out.add(f.get());                             // 2. then wait, in order
        return out;
    }                                                                                  // 3. close() waits for all
}
```

```kotlin
fun serveAll(requests: List<Transfer>): List<Reply> =
    Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
        val replies = requests.map { t -> perRequest.submit(Callable { handle(t) }) }   // 1. start every request
        replies.map { it.get() }                                                       // 2. then wait, in order
    }                                                                                   // 3. close() waits for all
```

In a real service the framework starts the threads: Quarkus with `@RunOnVirtualThread`, Spring Boot with `spring.threads.virtual.enabled=true`. What no framework does, as *Moving a blocking service to virtual threads* warned, is write your limits down. Unlimited threads mean unlimited calls to whatever sits behind them. So every scarce thing gets an explicit limit:

- the fraud service: one shared `Semaphore` of 20 permits, held only around the fraud call;
- the journal: lesson 2's bounded `ledger-` pool, 8 threads and 80 slots, which rejects with a 503 when it is full;
- each request: one deadline of 300 ms for all of its screening.

The ledger pool stays a pool of platform threads on purpose. It isn't there to save thread creation. It is a limit with a queue and a rejection policy, around work you want bounded. Request threads wait for it with `future.get()`, and a parked virtual thread costs a little heap.""",
   "figure": {"svg": FIGURE, "caption": "Threads are free, so every limit sits on a resource: 20 permits for the fraud service, 8 threads and 80 slots for the journal, and one deadline per request."},
   "try": {
    "title": "Do the arithmetic before the load test",
    "minutes": 3,
    "steps": [
     "The fraud bulkhead has 20 permits, and a fraud call normally takes 20 ms. How many fraud checks a second can it pass? Is that enough for 400 requests a second? For 2,000?",
     "During an outage each fraud call takes 2 s, but the request interrupts it at its 300 ms deadline. How many requests a second now get a permit at all, and what happens to the rest?",
     "Open `TransferServer.handle` in the lab. Find the one wait that has no timeout and explain why it has none."
    ],
    "expect": "Twenty permits at 20 ms pass at most 20 / 0.02 = 1,000 checks a second: plenty for 400, not enough for 2,000, so at 2,000 a second you'd need about 40 permits, if the fraud vendor allows that many. In the outage each permit is held for 300 ms, so only about 20 / 0.3 = 67 requests a second get one; the rest wait for a permit until their deadline and get the stand-in rule. The next section's demo shows exactly that. The wait without a timeout is `ledger.submit(t).get()`: once the ledger pool has accepted a transfer the money may move, and a timeout would end the wait but not the transfer."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444", "kind": "read"}
   ]
  },
  {
   "h": "A bulkhead and a deadline for the slow fraud check",
   "body": """The fraud service is the slow, shared dependency. When it slows down, two things must not follow: every request waiting as long as it does, and every request piling onto it at once. A deadline stops the first, a bulkhead the second.

The bulkhead is the shared semaphore from *Using virtual threads: one per task, limits with semaphores*, with one change: the wait for a permit is bounded by the time the request has left.

```java
<T> T call(long waitNanos, Callable<T> block) throws Exception {
    if (!inFlight.tryAcquire(waitNanos, TimeUnit.NANOSECONDS))   // 1. outside the try
        throw new TimeoutException("no permit in time");
    try {
        return block.call();                                      // 2. only the slow call holds it
    } finally {
        inFlight.release();                                       // 3. always given back
    }
}
```

```kotlin
fun <T> call(waitNanos: Long, block: () -> T): T {
    if (!inFlight.tryAcquire(waitNanos, TimeUnit.NANOSECONDS))   // 1. outside the try
        throw TimeoutException("no permit in time")
    try {
        return block()                                            // 2. only the slow call holds it
    } finally {
        inFlight.release()                                        // 3. always given back
    }
}
```

The **deadline** is one number, computed once per request: `System.nanoTime() + budget`. Every wait inside the request uses what is left of it: the wait for a permit and the wait for the fraud answer. When it runs out, the request stops waiting and falls back. The fallback is a business rule, borrowed from card processing, called **stand-in**: small transfers (up to 50.00 here) go through without a fraud answer, larger ones get a fast "try again". The limit is a risk decision, not a technical one.

Stopping the wait is not enough. *Callable, Future, cancellation and interruption* made the point: a timeout on `get` ends your wait, not the task. A fraud call that runs on after its request has answered still holds a permit, and during an outage those orphans fill the bulkhead, so new requests can't get a permit even for a call that would succeed. So at the deadline the request interrupts the call. The interrupted call's `finally` gives the permit back, and the next request can use it. Give the fraud HTTP client its own timeout of the same length as well, so a call that ignores the interrupt still ends.

In this section's demo, an outage that makes every fraud call take 2 s still answers every request within about 320 ms, and the fraud service never sees more than 20 calls at once.""",
   "try": {
    "title": "Take the fraud service down",
    "minutes": 4,
    "steps": [
     "Run `FraudOutageDemo` (or `FraudOutageDemoJava`): 400 requests a second for 3 seconds, fraud calls take 20 ms. Predict the verdicts and the most fraud calls in flight.",
     "Run it with `-Pargs=outage`, so every fraud call takes 2 s. Amounts are random up to 200.00 and the stand-in limit is 50.00. Predict the share of stand-ins and the slowest reply.",
     "Delete the `call.cancel(true)` line and run the outage again. Predict first: what changes, and why?"
    ],
    "code": demo("FraudOutageDemo"),
    "expect": "Normally all 1,200 are approved, with at most about 20 fraud calls in flight (Little's law says 400 x 0.02 = 8 on average; bursts go higher) and the slowest reply well under 100 ms. In the outage, about a quarter of the requests get the stand-in rule (290 of 1,200 in one run), the rest time out, the fraud service never sees more than 20 calls, and the slowest reply is about 320 ms. Without the cancel, the verdicts look the same, but the slowest reply is about 2,300 ms: each request's executor closes at the end of `use`, and `close()` waits for the fraud call nobody cancelled. With a shared executor instead, the replies would be on time and the orphaned calls would hold their permits for the full 2 s."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  },
  {
   "h": "Fail fast when one check says no",
   "body": """Screening calls two services: the fraud service, slow and behind the bulkhead, and the account limits service, which is fast. Run them at the same time and a request costs the slower of the two, not the sum. The trap is in how you collect the answers. *Structured concurrency and scoped values* showed it: call `get()` on the futures in the order you started them, and a fast "no" waits behind a slow "yes". In this section's demo the limits check says no at 10 ms, and the request still answers at about 600 ms.

Take the answers in the order they finish, and stop at the first no:

```kotlin
""" + SCREEN_KT + """
```

```java
""" + SCREEN_JAVA + """
```

`ExecutorCompletionService` hands you each future as it completes, so the first no is seen at once, and so is the first exception. Either one declines the transfer. The `finally` is what makes it fail fast: `shutdownNow()` interrupts the check that is still running, and `close()` waits until its thread has really ended. That order matters, as the lab in that lesson showed: `close()` after `shutdownNow()` waits for threads, not for futures. So no check outlives its request, still holding a permit or writing a log line for a request that has already answered.

This is structured concurrency built by hand from an executor. JDK 25 has `StructuredTaskScope` for exactly this job, but it is a preview API in JDK 25, 26 and 27, so it stays out of the labs. The deeper note shows the same screening with it.

One rule binds every check: it has to stop when interrupted. `sleep`, locks, queues, latches and semaphores do. A check that computes in a loop and never looks at the interrupt flag keeps running, and `close()` waits for it, deadline or not.""",
   "try": {
    "title": "Collect in order, then fail fast",
    "minutes": 3,
    "steps": [
     "Run `FailFastDemo`. One transfer, two checks: fraud answers yes after 500 ms, limits answers no after 10 ms. Predict when each half prints its verdict.",
     "In the fail-fast half, replace `done.take()` with the futures in submit order: keep the two futures that `done.submit` returns and call `get()` on them in that order. Run it again."
    ],
    "code": demo("FailFastDemo"),
    "expect": "Collected in order, the verdict comes after the fraud check answers, at about 500 to 600 ms, though the answer was known at 10 ms. Fail-fast prints `declined` at about 12 ms, and the fraud check reports `interrupted` 2 ms later, when `shutdownNow()` reaches it. After your change, the fail-fast half waits about 500 ms again: running checks in parallel only pays if you also collect them in completion order."
   }
  },
  {
   "h": "Keep the carriers free: nothing slow under an account lock",
   "body": """Lesson 1 chose `ReentrantLock` for the accounts, and this is where that choice matters. A virtual thread is **pinned** when it blocks but can't leave its carrier, as *Pinning, ThreadLocals and other traps* showed. On JDK 21 to 23, blocking inside `synchronized`, or waiting to enter a `synchronized` block another thread holds, pins. JDK 24 fixed both (JEP 491), and JDK 25 is the first LTS with the fix. These labs compile for JDK 21 and must run there too, so the ledger uses `ReentrantLock`, which has always let a waiting virtual thread unmount.

The lock type is the smaller half of the rule. The bigger half is that nothing slow happens while you hold an account lock. Here is what someone might write to make "journal and apply" one atomic step:

```java
synchronized (merchant) {          // or merchantLock.lock()
    journal.append(t);             // 20 ms of disk I/O while holding the lock
    merchant.credit(t.cents());
}
```

```kotlin
synchronized(merchant) {           // or merchantLock.withLock { }
    journal.append(t)              // 20 ms of disk I/O while holding the lock
    merchant.credit(t.cents)
}
```

The demo runs this with one carrier thread, 20 payments into one hot merchant account, and a ticker that wants to tick every 10 ms. With `synchronized` on JDK 21, the ticker missed 425 ms of ticks: the carrier was pinned the whole time, so nothing else ran. With `ReentrantLock` the ticker was fine, but the 20 payments still took 430 ms, one after another, because each held the lock for its whole disk write. That is Little's law again: a lock held for 20 ms lets through at most 50 payments a second. With the journal written first and the lock taken only for the credit, all 20 took 21 ms.

So the rule from *synchronized and intrinsic locks* holds in its strongest form. Inside an account lock, read and write the accounts, nothing else. The journal write, the fraud call and any logging that might block happen outside. That is why lesson 2's `LedgerService` writes the journal before `apply` takes a single lock.

To check a running service, keep JFR's `jdk.VirtualThreadPinned` event on; it records pins longer than 20 ms by default. The old `-Djdk.tracePinnedThreads` flag was removed in JDK 24.""",
   "try": {
    "title": "Pin a carrier, then free it",
    "minutes": 4,
    "steps": [
     "Run `LockScopeDemo` (or `LockScopeDemoJava`). It forces one carrier thread and runs three versions of the same 20 payments. Predict both columns for each row before you look.",
     "Explain the second row: no pinning, so why are the payments still slow?",
     "If you have JDK 24 or later installed, run Gradle on it and run the demo again. Which number changes?"
    ],
    "code": demo("LockScopeDemo"),
    "expect": "On JDK 21 (the run here): `synchronized` took 426 ms with a 425 ms gap in the ticks, because the pinned carrier couldn't run the ticker. `ReentrantLock` took 433 ms with a 19 ms gap: the carrier was free, but the payments queued behind a lock held across I/O. Journal first took 21 ms with a 16 ms gap. On JDK 24 and later, JEP 491 lets a virtual thread that holds a monitor unmount, so the first row's gap should drop to the second row's, while its time stays near 430 ms: the fix removes the pinning, not the queue behind the lock."
   },
   "refs": [
    {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491", "kind": "read"}
   ]
  },
  {
   "h": "Read 10,000 virtual threads in a JSON dump",
   "body": """Lesson 2 found a hung pool with `jcmd <pid> Thread.print`. Run that on the server during a fraud outage and the request threads are not there. On JDK 21, `Thread.print` lists platform threads only. JDK 24 added the virtual threads that are mounted at that moment, which during an outage is almost none. A parked virtual thread is a stack on the heap, not an OS thread, so the classic dump never sees it.

The dump for virtual threads is `Thread.dump_to_file`:

```bash
jcmd <pid> Thread.dump_to_file -format=json /tmp/requests.json
```

Here is the demo's dump of 10,000 parked requests on JDK 21, cut down to its shape:

```json
""" + JSON_DUMP + """
```

Threads sit in **thread containers**. A container is whatever started them: your executor, with its own entry and thread list, or `<root>` for ordinary platform threads such as `main`. The 10,000 requests are one container, the carriers another (`ForkJoinPool-1`, one worker per core). On JDK 21 each thread entry has only `tid`, `name` and `stack`. JDK 25 adds `state`, `virtual`, `parkBlocker` and `carrier`. The named factory, `Thread.ofVirtual().name("request-", 0)`, is what gives you `request-9999` instead of an empty name.

Ten thousand stacks can't be read one at a time, so group them. Count threads per container, then count stacks by the frame where your code starts and the JDK frame just above it:

```bash
""" + JQ + """
```

```text
""" + GROUPED + """
```

That is the outage in three lines: 20 requests are inside the fraud call, 9,980 wait for a fraud permit, and `main` sleeps. The bulkhead held, and the fraud service is the problem. A dump of 10,000 threads is about 12 MB, so write it to a file and read it with tools, never in a terminal.""",
   "try": {
    "title": "Dump 10,000 parked requests",
    "minutes": 5,
    "steps": [
     "Run `ParkedRequestsDemo` (or `ParkedRequestsDemoJava`) with `-Pargs=60`. It starts 10,000 requests on named virtual threads that all wait for a fraud service that hangs, and prints its PID.",
     "In a second terminal, run `jcmd <pid> Thread.print` and look for `request-` threads.",
     "Run `jcmd <pid> Thread.dump_to_file -format=json /tmp/requests.json`, then the two `jq` commands from this section. To take a second dump, delete the file first or add `-overwrite`.",
     "Before you read the counts, predict them: how many requests are inside the fraud call, and how many wait for a permit?"
    ],
    "code": demo("ParkedRequestsDemo"),
    "expect": "`Thread.print` shows no `request-` thread at all on JDK 21: only `main`, the four `ForkJoinPool-1-worker-N` carriers and JVM threads. The JSON file is about 12 MB with six containers: 10,000 threads under the `ThreadPerTaskExecutor`, four carriers under `ForkJoinPool-1`, `main` and a few JVM threads under `<root>`, and three empty ones. Grouped by stack: 9,980 in `Semaphore.acquire` at line 12, 20 in `CountDownLatch.await` at line 14, and `main` in `Thread.sleep`. The Java twin shows the same counts with `ParkedRequestsDemoJava.handle`. On JDK 25 every entry also carries its state and `\"virtual\": true`."
   },
   "refs": [
    {"title": "Thread dump JSON schema (JDK 25 source)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.schema.json", "kind": "docs"}
   ]
  }
 ],
 "analogy": "The server is a restaurant that seats every guest the moment they walk in, because chairs (virtual threads) cost almost nothing. What it rations is what sits behind the chairs. The sommelier (the fraud service) takes 20 guests at a time. The kitchen (the ledger pool) has 8 cooks and 80 order slips, and when the slips run out the door says \"kitchen full, try again in a minute\". Every guest is promised an answer within five minutes. A guest who has waited that long for the sommelier gets the house wine if the order is small and is asked to come back if it is large, and the sommelier is told to stop decanting for him. The analogy breaks at the chairs: a seated guest still takes floor space and a waiter's attention. A parked virtual thread takes a couple of kilobytes of heap and no thread at all until something wakes it.",
 "in_your_world": "This is the shape of a Quarkus payment endpoint with `@RunOnVirtualThread`: the request runs on a virtual thread and calls a fraud REST client, a limits client and the database. Quarkus adds neither the bulkhead nor the deadline. SmallRye Fault Tolerance's `@Bulkhead` and `@Timeout` are one way to declare them, and a shared `Semaphore` plus one deadline per request is another. Either way, size the bulkhead from the fraud vendor's concurrency limit and Little's law, and set the REST client's read timeout to the same budget. The stand-in limit is a risk decision: agree the amount with the risk team, and log every stand-in with its transfer id so it can be reviewed. During an incident, `jcmd <pid> Thread.dump_to_file -format=json` inside the pod tells you in a minute whether requests are stuck on your bulkhead or on something else.",
 "mistake": "The most common mistake is a timeout that ends the wait but not the work: `future.get(300, MILLISECONDS)` in a `try`, a fallback in the `catch`, and nothing that stops the call. Every request answers on time, so the dashboards look fine. Meanwhile each abandoned call keeps its bulkhead permit, its connection and its socket until the slow service answers, and during an outage those orphans fill the bulkhead, so even calls that would succeed can't get a permit. People make it because `get` with a timeout reads like a deadline. Cancel what you stopped waiting for (`cancel(true)`, or `shutdownNow()` on the request's executor), release the permit in the call's own `finally`, and give the client library a timeout of the same length as a backstop.",
 "compare": {
  "title": "The request handler and the fan-in, in both languages",
  "kotlin": {"title": "TransferServer.kt", "src": """fun handle(t: Transfer): Reply {
    val verdict = screening.screen(t)
    if (verdict == Verdict.DECLINED) return Reply(t.id(), Status.DECLINED)
    if (verdict == Verdict.TIMED_OUT) return Reply(t.id(), Status.TIMED_OUT)
    val outcome = try {
        ledger.submit(t).get()               // no timeout: the money may already be moving
    } catch (e: RejectedExecutionException) {
        return Reply(t.id(), Status.BUSY)
    }
    val status = if (outcome == Outcome.APPLIED) Status.APPLIED else Status.INSUFFICIENT_FUNDS
    return Reply(t.id(), status, standIn = verdict == Verdict.STAND_IN)
}

fun serveAll(requests: List<Transfer>): List<Reply> =
    Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
        val replies = requests.map { t -> perRequest.submit(Callable { handle(t) }) }
        replies.map { it.get() }
    }"""},
  "java": {"title": "TransferServer.java", "src": """Reply handle(Transfer t) throws InterruptedException, ExecutionException {
    Verdict verdict = screening.screen(t);
    if (verdict == Verdict.DECLINED) return new Reply(t.id(), Status.DECLINED, false);
    if (verdict == Verdict.TIMED_OUT) return new Reply(t.id(), Status.TIMED_OUT, false);
    Outcome outcome;
    try {
        outcome = ledger.submit(t).get();    // no timeout: the money may already be moving
    } catch (RejectedExecutionException e) {
        return new Reply(t.id(), Status.BUSY, false);
    }
    Status status = outcome == Outcome.APPLIED ? Status.APPLIED : Status.INSUFFICIENT_FUNDS;
    return new Reply(t.id(), status, verdict == Verdict.STAND_IN);
}

List<Reply> serveAll(List<Transfer> requests) throws Exception {
    try (ExecutorService perRequest = Executors.newVirtualThreadPerTaskExecutor()) {
        List<Future<Reply>> replies = new ArrayList<>();
        for (Transfer t : requests) replies.add(perRequest.submit(() -> handle(t)));
        List<Reply> out = new ArrayList<>();
        for (Future<Reply> f : replies) out.add(f.get());
        return out;
    }
}"""},
  "note": "The threads, executors and futures are the same JDK classes on both sides; what differs is how each language spells the edges. Kotlin has no checked exceptions, so `get()`'s `InterruptedException` and `ExecutionException` need no `throws` clause; an interrupted request thread still throws out of `handle`. A `try` is an expression in Kotlin, which lets `val outcome = try { ... }` replace Java's assign-in-try. `use` on an `ExecutorService` is Kotlin's try-with-resources, and both call `close()`, which waits for every request. Kotlin's default argument (`standIn = false`) saves the third constructor argument that the Java record needs every time. In the lab, the Kotlin server calls the Java ledger from lesson 2 directly: same package, same module, and records' accessors such as `t.id()` work as ordinary methods."
 },
 "worked": {
  "title": "Review a screening that passes the happy-path test",
  "steps": [
   {"say": "A teammate's first version of screening. It passes the test where both checks answer in 20 ms. Before reading on, find what goes wrong when the fraud service takes 2 s and when the limits check says no.",
    "code": """private val checkPool = Executors.newFixedThreadPool(20)          // "the bulkhead"

fun screen(t: Transfer): Verdict {
    val fraud = checkPool.submit(Callable { fraudClient.passes(t) })
    val limits = checkPool.submit(Callable { limitsClient.passes(t) })
    return try {
        if (fraud.get(300, TimeUnit.MILLISECONDS) && limits.get(300, TimeUnit.MILLISECONDS)) Verdict.APPROVED
        else Verdict.DECLINED
    } catch (e: TimeoutException) {
        Verdict.STAND_IN
    }
}""", "lang": "kotlin", "alt_lang": "java",
    "alt_code": """private final ExecutorService checkPool = Executors.newFixedThreadPool(20);   // "the bulkhead"

Verdict screen(Transfer t) throws Exception {
    Future<Boolean> fraud = checkPool.submit(() -> fraudClient.passes(t));
    Future<Boolean> limits = checkPool.submit(() -> limitsClient.passes(t));
    try {
        return fraud.get(300, TimeUnit.MILLISECONDS) && limits.get(300, TimeUnit.MILLISECONDS)
                ? Verdict.APPROVED : Verdict.DECLINED;
    } catch (TimeoutException e) {
        return Verdict.STAND_IN;
    }
}"""},
   {"say": "Five problems, each from an earlier lesson. The pool caps the whole task, so in a fraud outage the limits checks queue behind stuck fraud calls: put the limit on the resource, not on a pool. Two timeouts of 300 ms in a row allow 600 ms: there is no single deadline. A fast no from limits waits behind the fraud answer: no fail-fast. On timeout nothing is cancelled, so the orphaned calls keep all 20 pool threads busy and the next requests time out before they even start. And every timeout becomes a stand-in, whatever the amount.", "code": "", "lang": ""},
   {"say": "The fix is the lab's `screen`. Each numbered comment answers one problem: a deadline computed once (1), the fraud call alone behind a shared semaphore whose wait uses the time left (2), the stand-in rule only for small amounts (3), completion order and an early return for fail-fast (4), and `shutdownNow()` plus `close()` so nothing outlives the request (5).",
    "code": SCREEN_KT, "lang": "kotlin", "alt_lang": "java", "alt_code": SCREEN_JAVA},
   {"say": "Check it against the lab's tests, which are the production behaviours you care about. A stuck fraud call ends at the deadline, is interrupted, and gives its permit back. A no from either check declines at once and interrupts the other. A full bulkhead means the fallback without calling the fraud service at all. And 10,000 concurrent requests never put more than 50 calls into the fraud service, while every APPLIED reply, replayed on the opening balances, gives exactly the ledger's final snapshot.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Serve the ledger: a virtual thread per request, a bulkhead, a deadline, fail-fast",
  "minutes": 15,
  "files": [f"{lab}/main/{PK}/Bulkhead.kt", f"{lab}/main/{PK}/Screening.kt", f"{lab}/main/{PK}/TransferServer.kt",
            f"{lab}/main/{PJ}/LedgerService.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l03.*'",
  "steps": [
   "Run the tests once. All ten fail. This lab is in Kotlin. The ledger underneath is lesson 2's Java solution, unchanged, in the same package. Read `TransferServer.handle`: it is written for you, and its one wait without a timeout is deliberate.",
   "Write `Bulkhead.call`: `tryAcquire(waitNanos, TimeUnit.NANOSECONDS)` before the `try`, throw `TimeoutException` if it returns `false`, run `block()` inside the `try`, and `release()` in `finally`.",
   "Write `Screening.screen` in the four steps of its KDoc: one deadline, an `ExecutorCompletionService` over a fresh virtual-thread executor, two polls with the time left, and `shutdownNow()` then `close()` in a `finally`.",
   "Write `TransferServer.serveAll`: `Executors.newVirtualThreadPerTaskExecutor().use { }`, every request submitted before the first `get()`.",
   "Run the tests until all ten pass, then twice more. The slowest one sends 10,000 requests through the whole stack and replays every APPLIED reply against the final balances."
  ],
  "hints": [
   "`return` inside `repeat { }` or inside a `try` expression returns from `screen` itself, because `repeat` is inline. `?: return fallback(t)` after `poll` handles the deadline in one line.",
   "If the fail-fast tests time out, you are waiting for both checks. Take the futures from `poll` on the completion service, not the ones `submit` returned, in order.",
   "If a test says a permit didn't come back, check that `release()` is in a `finally` and that `tryAcquire` is outside the `try`.",
   "If the virtual-thread test reports hundreds of new platform threads, you used a pool. `Executors.newVirtualThreadPerTaskExecutor()` starts one new virtual thread per task."
  ],
  "done_when": "All ten tests in `TransferServerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the fail-fast fan-out with a deadline from memory",
  "minutes": 6,
  "prompt": "Close the lab. Write `fun firstNoWins(checks: List<() -> Boolean>, budget: Duration): Boolean?`. It runs every check on its own virtual thread and returns `false` at the first `false` or exception, `true` if all pass, and `null` if the budget runs out first. No check may still be running when it returns.",
  "answer": {"lang": "kotlin", "src": """fun firstNoWins(checks: List<() -> Boolean>, budget: Duration): Boolean? {
    val deadline = System.nanoTime() + budget.toNanos()            // 1. one deadline
    val perTask = Executors.newVirtualThreadPerTaskExecutor()
    try {
        val done = ExecutorCompletionService<Boolean>(perTask)
        checks.forEach { check -> done.submit { check() } }         // 2. fork them all
        repeat(checks.size) {
            val next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)
                ?: return null                                      // 3. out of time
            val ok = try { next.get() } catch (e: ExecutionException) { false }
            if (!ok) return false                                   // 4. the first no wins
        }
        return true
    } finally {
        perTask.shutdownNow()                                       // 5. stop the rest...
        perTask.close()                                             //    ...and wait until they have ended
    }
}""",
   "alt": {"lang": "java", "src": """Boolean firstNoWins(List<Callable<Boolean>> checks, Duration budget) throws InterruptedException {
    long deadline = System.nanoTime() + budget.toNanos();            // 1. one deadline
    ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();
    try {
        CompletionService<Boolean> done = new ExecutorCompletionService<>(perTask);
        for (Callable<Boolean> check : checks) done.submit(check);   // 2. fork them all
        for (int i = 0; i < checks.size(); i++) {
            Future<Boolean> next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
            if (next == null) return null;                           // 3. out of time
            boolean ok;
            try { ok = next.get(); } catch (ExecutionException e) { ok = false; }
            if (!ok) return false;                                   // 4. the first no wins
        }
        return true;
    } finally {
        perTask.shutdownNow();                                       // 5. stop the rest...
        perTask.close();                                             //    ...and wait until they have ended
    }
}"""}}
 },
 "recap": [
  "One new virtual thread per request, never pooled. Write every limit down instead: a shared semaphore per slow dependency, a bounded pool for the journal, one deadline per request.",
  "The bulkhead's permit wait and the call itself both use the time the request has left. At the deadline, interrupt the call, so its `finally` gives the permit back.",
  "Fail fast: take results in completion order, decline at the first no or failure, then `shutdownNow()` and `close()` so no check outlives its request.",
  "A fallback is a business rule: stand-in for small amounts, a fast \"try again\" for the rest. Never time out the wait for the ledger, because the money may already be moving.",
  "Nothing slow inside an account lock. On JDK 21, blocking under `synchronized` pins the carrier; `ReentrantLock` doesn't pin, but a lock held across I/O still queues everyone behind it.",
  "`Thread.print` doesn't show parked virtual threads. `Thread.dump_to_file -format=json` groups them by container; count them by stack with `jq`."
 ],
 "quiz": [
  {"q": "A colleague moves `val permits = Semaphore(20)` from the fraud client into `handle()`, so each request creates its own. What does the fraud service see during a spike of 5,000 concurrent requests?",
   "options": ["At most 20 calls at once, as before", "Up to 5,000 calls at once: every request has its own 20 permits",
               "At most 1 call at once", "An IllegalStateException from the second semaphore"],
   "answer": 1,
   "why": "A semaphore limits only the threads that share it. One per request hands every request a full set of permits, so the limit is gone. Keep one per dependency, in a field that every request uses.",
   "from": "vt-03"},
  {"q": "The ledger runs on JDK 21 and `apply` uses `synchronized` on both accounts, held for microseconds with no I/O inside. Ten thousand virtual threads pay into the same merchant account. What can happen?",
   "options": ["Nothing bad: the critical section is too short to matter",
               "The JVM throws IllegalMonitorStateException under that much contention",
               "Virtual threads waiting to enter the merchant's monitor pin their carriers, so heavy contention can leave no carrier free for other requests",
               "Each virtual thread gets its own copy of the monitor"],
   "answer": 2,
   "why": "On JDK 21 to 23, a virtual thread blocked entering a monitor can't unmount, so with one hot monitor every carrier can end up waiting at it, and requests that never touch the account stop too. JDK 24 fixed it (JEP 491). `ReentrantLock` parks its waiters and frees the carrier on every JDK. A short critical section makes each wait short; it doesn't make the pins harmless.",
   "from": "vt-04"},
  {"q": "`call.get(300, MILLISECONDS)` throws `TimeoutException`, the request answers with the stand-in rule, and the code does nothing else. What is the fraud call doing now?",
   "options": ["Still running and holding its bulkhead permit until the fraud service answers",
               "Cancelled, because `get` with a timeout cancels the task",
               "Interrupted, because its request thread moved on",
               "Finished, because its future is now done"],
   "answer": 0,
   "why": "A timeout on `get` ends your wait, nothing more. Nobody told the task to stop, so it runs on and keeps its permit, and its future is not done. Cancel it with `cancel(true)`, or `shutdownNow()` on its executor, so the call is interrupted and its `finally` releases the permit.",
   "from": "exec-04"},
  {"q": "In a hand-built fail-fast scope on JDK 21 you call `cancel(true)` on the slow check's future, then `close()` on the virtual-thread executor. Why can `close()` return while the check is still running its `finally` block?",
   "options": ["`cancel(true)` doesn't interrupt the thread",
               "`close()` never waits for tasks",
               "Virtual threads skip `finally` blocks after an interrupt",
               "The executor counts a task as finished once its future is done, and `cancel` marks the future done at once"],
   "answer": 3,
   "why": "On JDK 21 the per-task executor tracks tasks by their futures, and `cancel(true)` completes the future immediately while the thread is still unwinding. `shutdownNow()` interrupts the threads and leaves the futures alone, so `close()` keeps waiting until each thread has really ended. That is why `screen` calls `shutdownNow()` and then `close()`.",
   "from": "vt-05"},
  {"q": "Why does `TransferServer.handle` wait for `ledger.submit(t).get()` with no timeout?",
   "options": ["Because the ledger pool is so fast that it never matters",
               "Because once the pool has accepted the transfer it may be applied, and a timeout would report a failure for money that moved",
               "Because `Future.get` has no timeout version",
               "Because virtual threads can't be interrupted while they wait"],
   "answer": 1,
   "why": "The wait is already bounded by design: a full queue rejects at once with BUSY, and 80 queued transfers drain in about 50 ms. A timeout there would end the wait, not the transfer, so the client would retry a transfer that already happened. If you need a hard bound, answer 202 with the transfer id and let the client ask for the outcome."}
 ],
 "flashcards": [
  {"front": "Why one new virtual thread per request, not a pool of virtual threads?", "back": "Creating one is cheap, and a pool would cap the whole request. Cap the scarce resource with a shared semaphore instead."},
  {"front": "What must happen to a fraud call when its request's deadline passes?", "back": "Interrupt it (`cancel(true)` or `shutdownNow()`), so it stops and its `finally` releases the bulkhead permit. A timeout alone leaves an orphan holding the permit."},
  {"front": "What makes a fan-out fail fast?", "back": "Take results in completion order, stop at the first no or failure, then `shutdownNow()` to interrupt the rest and `close()` to wait for them."},
  {"front": "What is stand-in processing?", "back": "A fallback rule: when a check can't answer in time, small amounts go through unchecked and larger ones are turned away."},
  {"front": "On JDK 21, what pins a virtual thread in ledger code?", "back": "Blocking inside `synchronized`, or waiting to enter a contended `synchronized` block. `ReentrantLock` never pins. JDK 24 removed both cases (JEP 491)."},
  {"front": "Why don't parked virtual threads appear in `jcmd <pid> Thread.print`?", "back": "It lists platform threads, plus mounted virtual threads from JDK 24. Use `jcmd <pid> Thread.dump_to_file -format=json <file>`."},
  {"front": "How do you make 10,000 stacks in a JSON dump readable?", "back": "Group them: count threads per container, and count stacks by the frame where your code starts, with `jq ... | sort | uniq -c`."}
 ],
 "terms": [
  {"term": "Bulkhead", "plain": "A separate, shared limit on one dependency, so one slow service can't take every thread or connection."},
  {"term": "Deadline", "plain": "One point in time for the whole request. Every wait inside the request uses whatever is left of it."},
  {"term": "Stand-in", "plain": "A fallback for when a check can't answer in time: small amounts go through unchecked, larger ones are refused."},
  {"term": "Fail-fast fan-out", "plain": "Running several checks at once and stopping all of them at the first failure or no."},
  {"term": "Orphaned call", "plain": "Work that keeps running after the request that started it has already answered."},
  {"term": "Pinning", "plain": "A virtual thread that blocks but can't leave its carrier, so the carrier blocks with it."},
  {"term": "Thread container", "plain": "A group in a JSON thread dump: the executor or scope that started a set of threads."}
 ],
 "explain_back": {
  "prompt": "Design review. A sceptical principal engineer has read the whole ledger, all three lessons of it, and asks: \"Why virtual threads and a thread pool in the same service? Why 20 fraud permits and not 200? What happens to the money when the fraud service is down, when the pod is killed, and when two pods run this code?\" Defend your design, and say plainly what it does not handle.",
  "answer": "Requests mostly wait, on the fraud service, the limits service and the ledger, so each one gets its own virtual thread: Little's law says about 300 are in flight normally and thousands in an outage, and a parked virtual thread costs a little heap. The ledger pool is not there to save threads. It is the write path's limit: 8 platform threads because 1,600 transfers a second at 5 ms of journal write is 8 in flight, 80 queue slots because that is 50 ms of waiting, and a counted rejection that turns overload into a 503 the client retries with the same transfer id.\n\nThe 20 permits come from the fraud vendor's concurrency limit and Little's law: at 20 ms a call they pass about 1,000 checks a second, above our peak. If the vendor allows more, the number goes up; it belongs to the downstream, not to us. When the fraud service is down, every request still answers within its 300 ms deadline: the bulkhead caps what the vendor sees, the deadline interrupts calls so their permits come back, and the stand-in rule approves small amounts and refuses the rest. Money only moves through `apply`, which keeps the three invariants under per-account locks taken in id order, so a stand-in can't break the books; it only takes a fraud risk we chose on purpose.\n\nWhen the pod is killed, lesson 2's shutdown drains the pool or hands back the transfers that never started, so nothing accepted vanishes, as long as the journal is durable. What this design doesn't handle is everything that needs shared state. Two pods each have their own in-memory ledger, and their locks protect nothing across pods. A retry after a crash needs the journal replayed and an idempotency check on the transfer id. A production version keeps balances in the database, with row locks in id order or one owner per account, and keeps the rest of this design as it is."
 },
 "deeper": {
  "minutes": 12,
  "body": """What a production version of this ledger adds, roughly in the order I'd build it:

- Durable state: balances and the journal in a database, row locks taken in account id order or one owner per account, a `CHECK (balance >= 0)` constraint, and a unique key on the transfer id.
- Idempotent replies: store each transfer's outcome by id, so a retry after a 503 or a client timeout gets the original answer instead of a second transfer.
- Metrics on every limit: bulkhead permits in use and the wait for them, stand-ins, the ledger queue's size and rejections, time in queue, journal write latency, and JFR's `jdk.VirtualThreadPinned` events.
- A circuit breaker in front of the fraud service, so that during an outage requests go to the stand-in rule at once instead of each one waiting out its deadline.
- Request context, such as the request id, in a scoped value (final in JDK 25) or passed as a parameter, so it reaches every log line on every virtual thread.
- Load tests with real latency distributions, and a fault-injection run where the fraud service hangs, checked against the same invariants as the lab's tests.

Structured concurrency is the JDK's own version of `screen`. `StructuredTaskScope` is a preview API in JDK 25 (JEP 505) and still preview in JDK 26 and 27; JEP 543 makes it final in JDK 28 with the JDK 27 API. Here is the screening in the JDK 25 shape. It needs `--enable-preview`, which is why it isn't in the labs:

```java
// JDK 25, preview: javac --release 25 --enable-preview ... and java --enable-preview ...
Verdict screen(Transfer t) throws InterruptedException {
    try (var scope = StructuredTaskScope.open(Joiner.<Boolean>awaitAllSuccessfulOrThrow(),
            cf -> cf.withTimeout(budget))) {
        scope.fork(() -> { if (!fraudBulkhead.call(budget.toNanos(), () -> fraud.passes(t))) throw new Declined(); return true; });
        scope.fork(() -> { if (!limits.passes(t)) throw new Declined(); return true; });
        scope.join();                                  // the first failure cancels the other subtask
        return Verdict.APPROVED;
    } catch (StructuredTaskScope.TimeoutException e) {
        return fallback(t);                            // the scope has cancelled both subtasks
    } catch (StructuredTaskScope.FailedException e) {
        return e.getCause() instanceof TimeoutException ? fallback(t) : Verdict.DECLINED;
    }
}
```

```kotlin
// JDK 25, preview: compile and run with --enable-preview
fun screen(t: Transfer): Verdict = try {
    StructuredTaskScope.open(Joiner.awaitAllSuccessfulOrThrow<Boolean>()) { cf -> cf.withTimeout(budget) }.use { scope ->
        scope.fork(Callable { if (!fraudBulkhead.call(budget.toNanos()) { fraud.passes(t) }) throw Declined(); true })
        scope.fork(Callable { if (!limits.passes(t)) throw Declined(); true })
        scope.join()                                   // the first failure cancels the other subtask
        Verdict.APPROVED
    }
} catch (e: StructuredTaskScope.TimeoutException) {
    fallback(t)                                        // the scope has cancelled both subtasks
} catch (e: StructuredTaskScope.FailedException) {
    if (e.cause is TimeoutException) fallback(t) else Verdict.DECLINED
}
```

A "no" becomes an exception (`Declined`, your own small exception class), because the default joiner fails fast on exceptions, not on values. The scope's `close()` cancels and waits for every subtask, which is what your `finally` did by hand, and the JSON thread dump shows each scope as its own container under the request that opened it. In JDK 27 the built-in joiners throw `ExecutionException` instead of `FailedException`, so that `catch` changes when you move."""
 },
 "sources": [
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"},
  {"title": "JEP 505: Structured Concurrency (Fifth Preview)", "url": "https://openjdk.org/jeps/505"},
  {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html"},
  {"title": "Thread dump JSON schema (JDK 25 source)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.schema.json"}
 ]
}

out = ROOT / "content/lessons/cap1-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
