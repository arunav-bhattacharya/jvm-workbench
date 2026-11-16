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
    'It calls the safety service through a 20-permit bulkhead and the daily-limit check at the same time, then hands the transfer '
    'to the bounded ledger pool, which writes the journal and applies it">'
    '<rect class="box" x="20" y="110" width="120" height="44" rx="8"/><text class="t" x="80" y="137" text-anchor="middle">10,000 requests</text>'
    '<line class="ln" x1="140" y1="132" x2="168" y2="132" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="245" y="92" text-anchor="middle">one deadline: 300 ms</text>'
    '<rect class="box-a" x="170" y="100" width="150" height="64" rx="8"/>'
    '<text class="t" x="245" y="128" text-anchor="middle">virtual thread</text>'
    '<text class="t-s t-m" x="245" y="148" text-anchor="middle">one per request</text>'
    '<line class="ln" x1="320" y1="120" x2="348" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln" x1="320" y1="132" x2="348" y2="132" marker-end="url(#arr)"/>'
    '<line class="ln" x1="320" y1="148" x2="348" y2="222" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="350" y="32" width="160" height="48" rx="8"/><text class="t" x="430" y="61" text-anchor="middle">safety: 20 permits</text>'
    '<rect class="box" x="350" y="108" width="160" height="48" rx="8"/><text class="t" x="430" y="137" text-anchor="middle">daily-limit check</text>'
    '<rect class="box-a" x="350" y="198" width="160" height="48" rx="8"/><text class="t" x="430" y="227" text-anchor="middle">ledger pool 8 + 80</text>'
    '<line class="ln" x1="510" y1="56" x2="538" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="540" y="32" width="140" height="48" rx="8"/><text class="t" x="610" y="61" text-anchor="middle">safety service</text>'
    '<line class="ln" x1="510" y1="222" x2="538" y2="222" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="540" y="198" width="140" height="48" rx="8"/><text class="t" x="610" y="227" text-anchor="middle">journal, apply</text>'
    '<text class="t-s t-bad" x="430" y="22" text-anchor="middle">late: small amounts pass, or try again</text>'
    '<text class="t-s t-bad" x="430" y="270" text-anchor="middle">queue full: busy</text>'
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

JSON_25 = """{"tid": "10027", "virtual": true, "name": "request-9999", "state": "WAITING",
 "parkBlocker": {"object": "java.util.concurrent.Semaphore$NonfairSync@bebad46"},
 "stack": ["java.base/java.lang.VirtualThread.park(VirtualThread.java:745)", "...",
           "java.base/java.util.concurrent.Semaphore.acquire(Semaphore.java:318)",
           "workbench.ledger.l03.demo.ParkedRequestsDemoKt.handle(ParkedRequestsDemo.kt:12)", "..."]}"""

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
        done.submit { safetyBulkhead.call(deadline - System.nanoTime()) { safety.passes(t) } }   // 2. start both
        done.submit { limits.passes(t) }
        repeat(2) {
            val next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)
                ?: return fallback(t)                                    // 3. deadline passed: small-amount rule
            val passed = try {
                next.get()
            } catch (e: ExecutionException) {
                if (e.cause is TimeoutException) return fallback(t)      //    no safety permit in time
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
        done.submit(() -> safetyBulkhead.call(deadline - System.nanoTime(), () -> safety.passes(t)));   // 2. start both
        done.submit(() -> limits.passes(t));
        for (int i = 0; i < 2; i++) {
            Future<Boolean> next = done.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
            if (next == null) return fallback(t);                        // 3. deadline passed: small-amount rule
            try {
                if (!next.get()) return Verdict.DECLINED;                // 4. a check said no: fail fast
            } catch (ExecutionException e) {
                if (e.getCause() instanceof TimeoutException) return fallback(t);   // no safety permit in time
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
 "goal": "By the end you can serve the ledger with one virtual thread per request, cap a slow outside service with one shared semaphore, give every request one deadline with a fallback, run two checks at once that stop at the first no, keep slow work out of the account locks, read a JSON dump of 10,000 waiting virtual threads, and defend the whole design in a review.",
 "opening": """Picture the bank's app on a phone. A customer taps "send", and a request, one message asking the bank to move money, reaches the bank's program. Thousands of customers do this at once. Before any money moves, the bank asks two questions. A safety service, an outside program, says whether the transfer looks like theft. It usually answers in 20 ms; on a bad day it takes 2 seconds. A quick second check asks whether the transfer fits the account's daily limit.

Virtual threads, which a program can start by the thousand, make it easy to give every request its own thread. That's the trap. Unlimited threads mean unlimited calls to the safety service, and on its bad day every request waits as long as it does.

Run it on a pool you can reason about gave the journal a pool with a reason for every number. Requests are different: many, and mostly waiting. In this lesson, we'll give each request its own virtual thread, a written limit on every scarce thing and one deadline. Then we'll stop at the first no, keep slow work out of the locks, and read 10,000 waiting threads in one dump. Before we start, make a guess, and keep it in mind.""",
 "warmup": {
  "q": "The bank's server gets 2,000 transfer requests a second. Each spends about 150 ms waiting on the safety service and almost no time anywhere else. With one thread per request, about how many threads are busy at once?",
  "options": ["About 2", "About 300", "About 2,000", "About 150"],
  "answer": 1,
  "why": "Little's law from The thread-per-request wall: requests in flight = 2,000 a second x 0.15 s = 300. If the safety service slows to 2 s, the same traffic needs 4,000. Platform threads make that costly and virtual threads make it cheap, which moves the question to what each of those requests is allowed to call. 2,000 forgets that each request leaves after 150 ms, and 150 forgets the rate."
 },
 "sections": [
  {
   "h": "One request, one virtual thread, and every limit written down",
   "body": """Let's follow one request through the server. It spends almost all its time waiting: on the safety service, on the daily-limit check, on the ledger pool. The thread-per-request wall gave us the number for that: requests in flight = rate x time. At 2,000 requests a second and 150 ms each, 300 requests are in flight. When the safety service slows to 2 s, 4,000 are. A **platform thread** is a thread the operating system runs. One per request would mean 4,000 of them, each reserving about 1 MB for its stack, created at the worst moment.

That lesson's restaurant gave every table a personal waiter, who stood at the kitchen door the whole time. How virtual threads work kept only a few waiters, and clipped each table's order slip to a board while it waited. A **virtual thread** is that order slip: a thread the JVM manages itself. While it waits on a network call, a lock or a semaphore, it lets go of its **carrier**, the platform thread that runs it. Its stack waits on the heap, the memory where Java keeps its objects. So 4,000 waiting requests cost 4,000 small objects, not 4,000 operating-system threads.

So the server starts one new virtual thread for each request, and never pools them:

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

First we submit every request, each on its own new virtual thread (1). Then we wait for the replies, in order (2). Leaving the block calls `close()`, which waits for every request to finish (3).

Now the trap from the opening. Moving a blocking service to virtual threads warned that an old pool was also a limit nobody had written down. Take the pool away, and nothing stops 4,000 requests from calling the safety service at once. So every scarce thing gets a limit, written down where we can see it:

- The safety service (banks call this a fraud check): one shared `Semaphore`, a counter of permits that threads take and give back, with 20 permits held only during the safety call. These are the 20 grill tokens from Using virtual threads. A limit like this, on one slow outside service, is a **bulkhead**, named after the walls in a ship that stop one flooded room from sinking the rest.
- The journal: lesson 2's `ledger-` pool, 8 threads and 80 slots, which answers "busy" when it's full.
- Each request: one deadline of 300 ms for all of its checks.

The ledger pool stays a pool of platform threads on purpose. It isn't there to save threads; it's a limit with a queue and a rejection rule, around work we want bounded. Request threads wait for its answer with `future.get()`. A **future** is the takeaway ticket from Callable, Future, cancellation and interruption: a claim on a result that isn't ready yet. Waiting on one costs a virtual thread a little heap.

**Threads are free, so every limit sits on a resource. Write each one down.**

Twenty permits keep the safety service from being flooded. They don't stop a request from waiting as long as the service does on its bad day. That takes a deadline.""",
   "figure": {"svg": FIGURE, "caption": "Threads are free, so every limit sits on a resource: 20 permits for the safety service, 8 threads and 80 slots for the journal, and one deadline per request."},
   "aside": {
    "title": "If you write web services, who starts these threads?",
    "body": "Your framework does, once you ask it to. A web framework is the library that receives requests over the network and calls your code for each one. In Spring Boot, the setting `spring.threads.virtual.enabled=true` runs requests on virtual threads; in Quarkus, the `@RunOnVirtualThread` annotation does it for one endpoint. Neither adds the limits for you. The shared semaphore, the bounded pool and the deadline are still yours to write."
   },
   "try": {
    "title": "Do the arithmetic before the load test",
    "minutes": 3,
    "steps": [
     "The safety bulkhead has 20 permits, and a safety call normally takes 20 ms. How many safety checks a second can it pass? Is that enough for 400 requests a second? For 2,000?",
     "On a bad day, each safety call takes 2 s, but the request interrupts it at its 300 ms deadline. How many requests a second now get a permit at all, and what happens to the rest?",
     "Open `TransferServer.handle` in the lab. Find the one wait that has no timeout, and explain why it has none."
    ],
    "expect": "Twenty permits at 20 ms pass at most 20 / 0.02 = 1,000 checks a second: plenty for 400, not enough for 2,000. At 2,000 a second you'd need about 40 permits, if the safety service allows that many. On the bad day, each permit is held for 300 ms, so only about 20 / 0.3 = 67 requests a second get one; the rest wait for a permit until their deadline and fall back. The next section's demo shows exactly that. The wait without a timeout is `ledger.submit(t).get()`: once the ledger pool has accepted a transfer, the money may move, and a timeout would end the wait but not the transfer."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444", "kind": "read"}
   ]
  },
  {
   "h": "A shared limit and one deadline for the slow safety check",
   "body": """The safety service is the slow, shared dependency, an outside program the bank can't do without. When it slows down, two things must not follow: every request waiting as long as it does, and every request piling onto it at once. A deadline stops the first, and the bulkhead stops the second.

The bulkhead is the shared semaphore from Using virtual threads, with one change: the wait for a permit is bounded by the time the request has left.

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

First, `tryAcquire` waits for a permit, but no longer than `waitNanos` (1). It sits outside the `try`, so a thread that never got a permit never gives one back. Then only the slow call runs while holding the permit (2). Finally, the `finally` returns the permit on every path: success, failure or interrupt (3).

The **deadline** is one number, computed once per request: `System.nanoTime() + budget`. Every wait inside the request uses what is left of it: the wait for a permit, and the wait for the safety answer. When it runs out, the request stops waiting and falls back to a plain business rule. Small transfers, up to 50.00 here, go through without the safety answer, and larger ones get a fast "try again". Banks call this kind of fallback stand-in; we'll call it the small-amount rule. Where to draw the line is a decision about risk, not about code.

Stopping the wait is not enough, though. Remember the takeaway ticket: you give up and catch your bus, and nobody tells the kitchen. The kitchen timer from CompletableFuture: errors, timeouts and fan-out ended the wait, not the work. Here, an abandoned safety call keeps running and keeps its permit. On a bad day, abandoned calls fill all 20 permits, and new requests can't get one, even for a call that would succeed.

So at the deadline, the request interrupts its own call. An **interrupt** is Java's polite request to a thread to stop what it's waiting for. Trace the smallest case on a bad day. All 20 permits are held by calls that will take 2 s. A request for 40.00 arrives, and its wait for a permit starts. Meanwhile, another request reaches its deadline. It interrupts its own safety call, and that call's `finally` hands the permit back. Our request takes it. When our own deadline comes, it does the same: it interrupts its call, the permit goes back, and the small-amount rule lets 40.00 through.

Give the safety service's network client its own timeout of the same length as well, so a call that ignores the interrupt still ends.

This section's demo sends 400 requests a second for 3 seconds. Two runs printed, first on a normal day and then on a bad one:

```text
safety service takes 20 ms: {approved=1200}
most safety calls in flight: 16, slowest reply: 35 ms
safety service takes 2000 ms: {let through=312, timed out=888}
most safety calls in flight: 20, slowest reply: 326 ms
```

The safety service had a terrible afternoon, and no customer waited longer than a third of a second for an answer. It never saw more than 20 calls at once, and about a quarter of the requests, the small ones, went through anyway.

**A timeout ends the wait, not the work. Cancel what you stop waiting for.**

One check now has a limit and a deadline. Each request makes two checks, though, and the order in which we collect their answers decides how fast a no arrives.""",
   "try": {
    "title": "Give the safety service a bad day",
    "minutes": 4,
    "steps": [
     "Run `SafetyOutageDemo` (or `SafetyOutageDemoJava`): 400 requests a second for 3 seconds, and safety calls take 20 ms. Predict the verdicts and the most safety calls in flight.",
     "Run it with `-Pargs=outage`, so every safety call takes 2 s. Amounts are random up to 200.00, and the small-amount rule lets through up to 50.00. Predict the share let through, and the slowest reply.",
     "Delete the `call.cancel(true)` line and run the bad day again. Predict first: what changes, and why?"
    ],
    "code": demo("SafetyOutageDemo"),
    "expect": "Normally all 1,200 are approved, with at most about 16 to 20 safety calls in flight (Little's law says 400 x 0.02 = 8 on average; bursts go higher), and the slowest reply well under 100 ms. On the bad day, about a quarter of the requests are let through (291 and 312 of 1,200 in runs here), the rest time out, the safety service never sees more than 20 calls, and the slowest reply is about 320 ms. Without the cancel, the verdicts look the same, but the slowest reply is about 2,300 ms (2,296 ms here): each request's executor closes at the end of its block, and `close()` waits for the safety call nobody cancelled. With a shared executor instead, the replies would be on time, and the abandoned calls would hold their permits for the full 2 s."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  },
  {
   "h": "Two checks at once, and the first no wins",
   "body": """Each request runs two checks: the safety service, slow and behind the bulkhead, and the daily-limit check, which is fast. Run them at the same time, and a request costs the slower of the two, not the sum. Starting several pieces of work at once and gathering their answers is called a **fan-out**.

The trap is in how we gather the answers. Structured concurrency and scoped values pictured a head waiter who sends helpers to fetch the parts of one order, and doesn't leave until every helper is back. If he waits for the helpers in the order he sent them, a fast "no" waits behind a slow "yes". In this section's demo, the limit check says no after 10 ms, and the request still answers after about 600 ms:

```text
in order: get() the safety check, then the limits check
   541 ms  safety check answered
   592 ms  verdict: declined
```

The answer was known at 10 ms. The customer heard it at 592.

The fix is to take the answers in the order they finish, and stop at the first no:

```java
""" + SCREEN_JAVA + """
```

```kotlin
""" + SCREEN_KT + """
```

`ExecutorCompletionService` hands us each future as it completes, so the first no is seen at once, and so is the first exception. Either one declines the transfer. The `finally` is what makes it **fail fast**, that is, stop all the other work at the first failure. `shutdownNow()` interrupts the check that is still running, and `close()` waits until its thread has really ended. That order matters, as Structured concurrency and scoped values showed. On JDK 21, a future cancelled with `cancel(true)` counts as done at once, so `close()` could return while its thread is still running. After `shutdownNow()`, `close()` waits for the threads themselves, so no check outlives its request. The same demo, collecting in completion order, printed:

```text
fail fast: take results as they finish, stop the rest at the first no
    12 ms  verdict: declined
    14 ms  safety check interrupted
```

Our `screen` is that head waiter, built by hand from an executor. JDK 25 has `StructuredTaskScope` for exactly this job. It's a preview API there, one you must switch on with `--enable-preview`, so it stays out of the labs. Go deeper shows the same screening with it.

One rule binds every check: it has to stop when interrupted. `sleep`, locks, queues, latches and semaphores all do. A check that computes in a loop and never looks at the interrupt flag keeps running, and `close()` waits for it, deadline or not.

**Checks that run side by side pay off only if you collect them as they finish. Stop at the first no.**

Requests now wait cheaply and stop on time. One place could still hold a carrier thread captive: the account locks from lesson 1.""",
   "try": {
    "title": "Collect in order, then fail fast",
    "minutes": 3,
    "steps": [
     "Run `FailFastDemo`. One transfer, two checks: the safety check answers yes after 500 ms, and the limits check answers no after 10 ms. Predict when each half prints its verdict.",
     "In the fail-fast half, replace `done.take()` with the futures in submit order: keep the two futures that `done.submit` returns, and call `get()` on them in that order. Run it again."
    ],
    "code": demo("FailFastDemo"),
    "expect": "Collected in order, the verdict comes after the safety check answers, at about 550 to 620 ms, though the answer was known at 10 ms. Fail fast prints `declined` at about 12 ms, and the safety check reports `interrupted` about 2 ms later, when `shutdownNow()` reaches it. After your change, the fail-fast half waits about 500 ms again: running checks side by side only pays if you also collect them in the order they finish."
   }
  },
  {
   "h": "Nothing slow under an account lock: keeping the carriers free",
   "body": """Lesson 1 chose `ReentrantLock` for the accounts and promised a reason. Here it is. A virtual thread is **pinned** when it waits but can't let go of its carrier, so the carrier waits with it. Pinning, ThreadLocals and other traps pictured this as a waiter holding a hot pan. He can't clip his slip to the board, because he can't put the pan down.

On JDK 21 to 23, `synchronized` was that hot pan. A virtual thread that waited inside a `synchronized` block, or waited to enter one, held on to its carrier. JDK 24 cooled the pan (JEP 491), and JDK 25 is the first long-term-support release with that fix. Our labs compile for JDK 21 and must run there too, so the ledger uses `ReentrantLock`, which has always let a waiting virtual thread step off its carrier.

The lock type is the smaller half of the rule, though. The bigger half is that nothing slow happens while we hold an account lock. Here's what someone might write to make "write the journal and credit the account" one step:

```java
synchronized (shop) {              // or shopLock.lock()
    journal.append(t);             // 20 ms of disk writing while holding the lock
    shop.credit(t.cents());
}
```

```kotlin
synchronized(shop) {               // or shopLock.withLock { }
    journal.append(t)              // 20 ms of disk writing while holding the lock
    shop.credit(t.cents)
}
```

This section's demo runs exactly that with one carrier thread. Twenty customers pay into one busy shop's account. Meanwhile a ticker, a small thread that wants to wake every 10 ms, measures how long it really waited. A long gap between ticks means the carrier was stuck. On JDK 21 it printed:

```text
JDK 21.0.12.1+1-1-24.04.4-Ubuntu, 1 carrier thread
journal inside synchronized    20 transfers in  409 ms, longest gap between ticks: 414 ms
journal inside ReentrantLock   20 transfers in  423 ms, longest gap between ticks:  20 ms
journal first, then the lock   20 transfers in   22 ms, longest gap between ticks:  12 ms
```

Read the rows one at a time. With `synchronized`, the ticker missed 414 ms of ticks: the carrier was pinned the whole time, so nothing else ran. With `ReentrantLock`, the ticker was fine. But the 20 payments still took over 400 ms, one after another, because each held the lock for its whole disk write. That's Little's law again: a lock held for 20 ms lets through at most 50 payments a second. With the journal written first and the lock taken only for the credit, all 20 took 22 ms.

Here are the same compiled classes on JDK 25:

```text
JDK 25.0.5.0.3+1-1-24.04.1-Ubuntu, 1 carrier thread
journal inside synchronized    20 transfers in  411 ms, longest gap between ticks:  16 ms
journal inside ReentrantLock   20 transfers in  412 ms, longest gap between ticks:  16 ms
journal first, then the lock   20 transfers in   22 ms, longest gap between ticks:  12 ms
```

The pan cooled: the first row's gap dropped to the second row's. Its time didn't move, because the fix removes the pinning, not the line of payments waiting behind a slow lock.

So the rule from synchronized and intrinsic locks holds in its strongest form. Inside an account lock, read and write the accounts, and nothing else. The journal write, the safety call and any logging that might wait all happen outside. That's why lesson 2's `LedgerService` writes the journal before `apply` takes a single lock.

To check a running service, keep JFR's `jdk.VirtualThreadPinned` event switched on. JFR, the JDK Flight Recorder, is built into the JVM and logs events from a running program. This event records pins longer than 20 ms by default. The old `-Djdk.tracePinnedThreads` flag was removed in JDK 24.

**Inside an account lock, touch the accounts and nothing else. Write the journal first.**

Everything holds on paper now. When something does go wrong in a running server, though, we'll need to see 10,000 waiting threads at once.""",
   "try": {
    "title": "Pin a carrier, then free it",
    "minutes": 4,
    "steps": [
     "Run `LockScopeDemo` (or `LockScopeDemoJava`). It forces one carrier thread and runs three versions of the same 20 payments. Predict both columns for each row before you look.",
     "Explain the second row: nothing is pinned, so why are the payments still slow?",
     "If you have JDK 24 or later installed, point `JAVA_HOME` at it, run the demo through Gradle again, and compare. Which number changes, and which stays?"
    ],
    "code": demo("LockScopeDemo"),
    "expect": "On JDK 21 (the runs here): `synchronized` took 409 to 427 ms with a gap of over 400 ms in the ticks, because the pinned carrier couldn't run the ticker. `ReentrantLock` took 409 to 423 ms with a gap of 15 to 20 ms: the carrier was free, but the payments queued behind a lock held across a disk write. Journal first took 21 or 22 ms. On JDK 25, the first row's gap dropped to about 15 ms while its time stayed near 410 ms: JEP 491 removes the pinning, not the queue behind the lock."
   },
   "refs": [
    {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491", "kind": "read"}
   ]
  },
  {
   "h": "Reading 10,000 waiting threads in one JSON dump",
   "body": """Lesson 2 found a stuck pool with `jcmd <pid> Thread.print`. Run that on the bank's server while the safety service is having its bad day, and the request threads aren't there. Ten thousand requests are waiting, and the classic dump can't find a single one. On JDK 21, `Thread.print` lists platform threads only. JDK 24 added the virtual threads that are on a carrier at that moment, which on a bad day is almost none. A waiting virtual thread is a stack on the heap, not an operating-system thread, so the classic dump never sees it.

The dump for virtual threads is `Thread.dump_to_file`. It writes every thread to a file, as plain text or as **JSON**, a text format for structured data that tools can read:

```bash
jcmd <pid> Thread.dump_to_file -format=json /tmp/requests.json
```

Here is the demo's dump of 10,000 waiting requests on JDK 21, cut down to its shape:

```json
""" + JSON_DUMP + """
```

Threads sit in **thread containers**. A container is whatever started them: our executor, with its own entry and list of threads, or `<root>` for ordinary platform threads such as `main`. The 10,000 requests are one container, and the carriers are another (`ForkJoinPool-1`, one carrier per core). On JDK 21, each thread entry has only `tid`, `name` and `stack`. The named factory, `Thread.ofVirtual().name("request-", 0)`, is what gives us `request-9999` instead of an empty name, just as the `ledger-` name tags did in lesson 2.

JDK 25 says more about each thread. The same demo on JDK 25 wrote this entry, trimmed:

```json
""" + JSON_25 + """
```

It tells us the thread is virtual, that it's waiting, and what it waits for: a `Semaphore`, our bulkhead.

Ten thousand stacks can't be read one at a time, so we group them. **jq** is a small, free command-line tool for picking values out of JSON. The first command below counts the threads in each container. The second finds, in each stack, the first line of our own code and the JDK line just above it, then counts how many threads share each pair:

```bash
""" + JQ + """
```

```text
""" + GROUPED + """
```

That's the bad day in three lines: 20 requests are inside the safety call, 9,980 wait for a permit, and `main` sleeps. The bulkhead held, and the safety service is the problem. A dump of 10,000 threads is about 12 MB on JDK 21 and 15 MB on JDK 25. Write it to a file and read it with tools, never in a terminal.

**Ten thousand stacks say nothing one at a time. Group them by where your code waits.**

The dump also shows where this design stops: everything in it lives in one program's memory. Two copies of the program would each have their own ledger and locks, which protect nothing across the two. The design review below starts there.""",
   "try": {
    "title": "Dump 10,000 waiting requests",
    "minutes": 5,
    "steps": [
     "Run `ParkedRequestsDemo` (or `ParkedRequestsDemoJava`) with `-Pargs=60`. It starts 10,000 requests on named virtual threads that all wait for a safety service that hangs, and prints its process id.",
     "In a second terminal, run `jcmd <pid> Thread.print` and look for `request-` threads.",
     "Run `jcmd <pid> Thread.dump_to_file -format=json /tmp/requests.json`, then the two `jq` commands from this section. To take a second dump, delete the file first or add `-overwrite`.",
     "Before you read the counts, predict them: how many requests are inside the safety call, and how many wait for a permit?"
    ],
    "code": demo("ParkedRequestsDemo"),
    "expect": "`Thread.print` shows no `request-` thread at all: only `main`, the four `ForkJoinPool-1-worker-N` carriers and the JVM's own threads. On JDK 21 the JSON file is about 12 MB, with 10,000 threads under the `ThreadPerTaskExecutor`, four carriers under `ForkJoinPool-1`, `main` and a few JVM threads under `<root>`, and some empty containers. Grouped by stack: 9,980 in `Semaphore.acquire` at line 12, 20 in `CountDownLatch.await` at line 14, and `main` in `Thread.sleep`. The Java twin shows the same counts with `ParkedRequestsDemoJava.handle`. On JDK 25, every entry also carries `\"virtual\": true`, its state and what it is waiting for, and the file is about 15 MB."
   },
   "refs": [
    {"title": "Thread dump JSON schema (JDK 25 source)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.schema.json", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The request handler and the fan-in, in both languages",
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
    return new Reply(t.id(), status, verdict == Verdict.LET_THROUGH);
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
    return Reply(t.id(), status, letThrough = verdict == Verdict.LET_THROUGH)
}

fun serveAll(requests: List<Transfer>): List<Reply> =
    Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
        val replies = requests.map { t -> perRequest.submit(Callable { handle(t) }) }
        replies.map { it.get() }
    }"""},
  "note": "The threads, executors and futures are the same JDK classes on both sides; what differs is how each language writes the edges. Kotlin has no checked exceptions, so `get()`'s `InterruptedException` and `ExecutionException` need no `throws` clause, and an interrupted request thread still throws out of `handle`. A `try` is an expression in Kotlin, which lets `val outcome = try { ... }` replace Java's assign-inside-try. `use` on an `ExecutorService` is Kotlin's try-with-resources, and both call `close()`, which waits for every request. Kotlin's default argument (`letThrough = false`) saves the third constructor argument that the Java record needs every time. In the lab, the Kotlin server calls the Java ledger from lesson 2 directly: same package, same module, and a record's accessors, such as `t.id()`, work as ordinary methods."
 },
 "worked": {
  "title": "Review a screening that passes the quiet-day test",
  "steps": [
   {"say": "Here is a teammate's first version of screening. It passes the test where both checks answer in 20 ms. Before reading on, find what goes wrong when the safety service takes 2 s, and when the limits check says no.",
    "code": """private final ExecutorService checkPool = Executors.newFixedThreadPool(20);   // "the bulkhead"

Verdict screen(Transfer t) throws Exception {
    Future<Boolean> safety = checkPool.submit(() -> safetyClient.passes(t));
    Future<Boolean> limits = checkPool.submit(() -> limitsClient.passes(t));
    try {
        return safety.get(300, TimeUnit.MILLISECONDS) && limits.get(300, TimeUnit.MILLISECONDS)
                ? Verdict.APPROVED : Verdict.DECLINED;
    } catch (TimeoutException e) {
        return Verdict.LET_THROUGH;
    }
}""", "lang": "java", "alt_lang": "kotlin",
    "alt_code": """private val checkPool = Executors.newFixedThreadPool(20)          // "the bulkhead"

fun screen(t: Transfer): Verdict {
    val safety = checkPool.submit(Callable { safetyClient.passes(t) })
    val limits = checkPool.submit(Callable { limitsClient.passes(t) })
    return try {
        if (safety.get(300, TimeUnit.MILLISECONDS) && limits.get(300, TimeUnit.MILLISECONDS)) Verdict.APPROVED
        else Verdict.DECLINED
    } catch (e: TimeoutException) {
        Verdict.LET_THROUGH
    }
}"""},
   {"say": "There are five problems, each from an earlier lesson. The pool caps the whole task, so on a bad day the limits checks queue behind stuck safety calls: put the limit on the resource, not on a pool. Two timeouts of 300 ms in a row allow 600 ms, so there is no single deadline. A fast no from limits waits behind the safety answer, so it doesn't fail fast. On a timeout nothing is cancelled, so the abandoned calls keep all 20 pool threads busy, and the next requests time out before they even start. And every timeout lets the transfer through, whatever the amount.", "code": "", "lang": ""},
   {"say": "The fix is the lab's `screen`. Each numbered comment answers one problem: a deadline computed once (1); the safety call alone behind a shared semaphore whose wait uses the time left (2); the small-amount rule only for small amounts (3); completion order and an early return, to fail fast (4); and `shutdownNow()` plus `close()`, so nothing outlives the request (5).",
    "code": SCREEN_JAVA, "lang": "java", "alt_lang": "kotlin", "alt_code": SCREEN_KT},
   {"say": "Check it against the lab's tests, which test what a real bank cares about. A stuck safety call ends at the deadline, is interrupted, and gives its permit back. A no from either check declines at once and interrupts the other one. A full bulkhead means the fallback, without calling the safety service at all. And 10,000 requests at once never put more than 50 calls into the safety service, while every APPLIED reply, replayed on the opening balances, gives exactly the ledger's final snapshot.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Serve the ledger: a virtual thread per request, a bulkhead, a deadline, fail fast",
  "minutes": 15,
  "files": [f"{lab}/main/{PK}/Bulkhead.kt", f"{lab}/main/{PK}/Screening.kt", f"{lab}/main/{PK}/TransferServer.kt",
            f"{lab}/main/{PJ}/LedgerService.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l03.*'",
  "steps": [
   "Run the tests once. All ten fail. This lab is in Kotlin, and the ledger underneath is lesson 2's Java solution, unchanged, in the same package, so Kotlin calls it directly. Read `TransferServer.handle`. It's written for you, and its one wait without a timeout is there on purpose.",
   "Write `Bulkhead.call`, the grill tokens with a time limit: `tryAcquire(waitNanos, TimeUnit.NANOSECONDS)` before the `try`, throw `TimeoutException` if it returns `false`, run `block()` inside the `try`, and `release()` in `finally`.",
   "Write `Screening.screen` in the four steps of its KDoc: one deadline, an `ExecutorCompletionService` over a fresh virtual-thread executor, two polls with the time left, and `shutdownNow()` then `close()` in a `finally`.",
   "Write `TransferServer.serveAll`: `Executors.newVirtualThreadPerTaskExecutor().use { }`, with every request submitted before the first `get()`.",
   "Run the tests until all ten pass, then twice more. The slowest one sends 10,000 requests through the whole program and replays every APPLIED reply against the final balances."
  ],
  "hints": [
   "`return` inside `repeat { }` or inside a `try` expression returns from `screen` itself, because `repeat` is inline. `?: return fallback(t)` after `poll` handles the deadline in one line.",
   "If the fail-fast tests time out, you are waiting for both checks. Take the futures from `poll` on the completion service, not the ones `submit` returned in order.",
   "If a test says a permit didn't come back, check that `release()` is in a `finally` and that `tryAcquire` is outside the `try`.",
   "If the virtual-thread test reports hundreds of new platform threads, you used a pool. `Executors.newVirtualThreadPerTaskExecutor()` starts one new virtual thread per task."
  ],
  "done_when": "All ten tests in `TransferServerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the fail-fast fan-out with a deadline from memory",
  "minutes": 6,
  "prompt": "Close the lab. Write `fun firstNoWins(checks: List<() -> Boolean>, budget: Duration): Boolean?`. It runs every check on its own virtual thread, and returns `false` at the first `false` or exception, `true` if all pass, and `null` if the budget runs out first. No check may still be running when it returns.",
  "answer": {"lang": "kotlin", "src": """fun firstNoWins(checks: List<() -> Boolean>, budget: Duration): Boolean? {
    val deadline = System.nanoTime() + budget.toNanos()            // 1. one deadline
    val perTask = Executors.newVirtualThreadPerTaskExecutor()
    try {
        val done = ExecutorCompletionService<Boolean>(perTask)
        checks.forEach { check -> done.submit { check() } }         // 2. start them all
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
        for (Callable<Boolean> check : checks) done.submit(check);   // 2. start them all
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
  "One new virtual thread per request, never pooled. Write every limit down instead: a shared semaphore for each slow outside service, a bounded pool for the journal, one deadline per request.",
  "The wait for a permit and the call itself both use the time the request has left. At the deadline, interrupt the call, so its `finally` gives the permit back.",
  "Fail fast: take answers in the order they finish, decline at the first no or failure, then `shutdownNow()` and `close()`, so no check outlives its request.",
  "A fallback is a business rule: let small amounts through, and give the rest a fast \"try again\". Never put a timeout on the wait for the ledger, because the money may already be moving.",
  "Nothing slow inside an account lock. On JDK 21, waiting inside `synchronized` pins the carrier; `ReentrantLock` doesn't pin, but a lock held across a disk write still makes everyone queue.",
  "`Thread.print` doesn't show waiting virtual threads; `Thread.dump_to_file -format=json` does. Where the design stops: it lives in one program's memory, so two copies share no locks."
 ],
 "closing": """We started with a customer tapping "send" and a safety service having a bad day. Now each request has its own virtual thread, a deadline and written limits, and money moves only inside `apply`, under both locks.

That's Part 1 in one program: locks kept the books right, the memory model made every handover safe, a pool with reasons ran the journal, and virtual threads let thousands of customers wait cheaply.

Now search your own code for `get(` with a timeout, and ask what stops the work when the wait gives up.

Next, we'll start Part 2 with Reactive programming. Our ledger said "busy" once its queue was full. What if the receiver could tell the sender how much it can take, before it fills up?""",
 "quiz": [
  {"q": "A colleague moves `val permits = Semaphore(20)` from the safety client into `handle()`, so each request creates its own. What does the safety service see during a spike of 5,000 requests at once?",
   "options": ["At most 20 calls at once, as before", "Up to 5,000 calls at once: every request has its own 20 permits",
               "At most 1 call at once", "An IllegalStateException from the second semaphore"],
   "answer": 1,
   "why": "A semaphore limits only the threads that share it. One per request hands every request a full set of permits, so the limit is gone. Keep one per outside service, in a field that every request uses: one hook of grill tokens for the whole kitchen.",
   "from": "vt-03"},
  {"q": "The ledger runs on JDK 21, and `apply` uses `synchronized` on both accounts, held for microseconds with no disk writing inside. Ten thousand virtual threads pay into the same shop's account. What can happen?",
   "options": ["Nothing bad: the critical section is too short to matter",
               "The JVM throws IllegalMonitorStateException under that much contention",
               "Virtual threads waiting to enter the shop's `synchronized` block pin their carriers, so heavy contention can leave no carrier free for other requests",
               "Each virtual thread gets its own copy of the lock"],
   "answer": 2,
   "why": "On JDK 21 to 23, a virtual thread waiting to enter a `synchronized` block can't step off its carrier, so with one busy account every carrier can end up waiting there, and requests that never touch the account stop too. JDK 24 fixed it (JEP 491). `ReentrantLock` frees the carrier while its waiters wait, on every JDK. A short critical section makes each wait short; it doesn't make the pins harmless.",
   "from": "vt-04"},
  {"q": "`call.get(300, MILLISECONDS)` throws `TimeoutException`, the request answers with the small-amount rule, and the code does nothing else. What is the safety call doing now?",
   "options": ["Still running, and holding its bulkhead permit until the safety service answers",
               "Cancelled, because `get` with a timeout cancels the task",
               "Interrupted, because its request thread moved on",
               "Finished, because its future is now done"],
   "answer": 0,
   "why": "A timeout on `get` ends your wait, nothing more: the takeaway ticket again. Nobody told the task to stop, so it runs on and keeps its permit, and its future is not done. Cancel it with `cancel(true)`, or `shutdownNow()` on its executor, so the call is interrupted and its `finally` releases the permit.",
   "from": "exec-04"},
  {"q": "In a hand-built fail-fast fan-out on JDK 21, you call `cancel(true)` on the slow check's future, then `close()` on the virtual-thread executor. Why can `close()` return while the check is still running its `finally` block?",
   "options": ["`cancel(true)` doesn't interrupt the thread",
               "`close()` never waits for tasks",
               "Virtual threads skip `finally` blocks after an interrupt",
               "The executor counts a task as finished once its future is done, and `cancel` marks the future done at once"],
   "answer": 3,
   "why": "On JDK 21, the per-task executor tracks tasks by their futures, and `cancel(true)` completes the future at once while the thread is still finishing. `shutdownNow()` interrupts the threads and leaves the futures alone, so `close()` keeps waiting until each thread has really ended. That's why `screen` calls `shutdownNow()` and then `close()`.",
   "from": "vt-05"},
  {"q": "Why does `TransferServer.handle` wait for `ledger.submit(t).get()` with no timeout?",
   "options": ["Because the ledger pool is so fast that it never matters",
               "Because once the pool has accepted the transfer, it may be applied, and a timeout would report a failure for money that moved",
               "Because `Future.get` has no timeout version",
               "Because virtual threads can't be interrupted while they wait"],
   "answer": 1,
   "why": "The wait is already bounded by design: a full queue turns the transfer away at once with BUSY, and 80 queued transfers drain in about 50 ms. A timeout there would end the wait, not the transfer, so the customer would try again for a transfer that already happened. If you need a hard bound, answer \"accepted\" with the transfer id at once, and let the customer ask for the outcome later."}
 ],
 "flashcards": [
  {"front": "Why one new virtual thread per request, not a pool of virtual threads?", "back": "Creating one is cheap, and a pool would cap the whole request. Cap the scarce resource with a shared semaphore instead."},
  {"front": "What must happen to a safety call when its request's deadline passes?", "back": "Interrupt it (`cancel(true)` or `shutdownNow()`), so it stops and its `finally` releases the bulkhead permit. A timeout alone leaves an abandoned call holding the permit."},
  {"front": "What makes a fan-out fail fast?", "back": "Take results in the order they finish, stop at the first no or failure, then `shutdownNow()` to interrupt the rest and `close()` to wait for them."},
  {"front": "What is the small-amount rule (stand-in)?", "back": "A fallback: when a check can't answer in time, small amounts go through unchecked and larger ones are turned away."},
  {"front": "On JDK 21, what pins a virtual thread in ledger code?", "back": "Waiting inside `synchronized`, or waiting to enter a busy `synchronized` block. `ReentrantLock` never pins. JDK 24 removed both cases (JEP 491)."},
  {"front": "Why don't waiting virtual threads appear in `jcmd <pid> Thread.print`?", "back": "It lists platform threads, plus virtual threads mounted on a carrier from JDK 24. Use `jcmd <pid> Thread.dump_to_file -format=json <file>`."},
  {"front": "How do you make 10,000 stacks in a JSON dump readable?", "back": "Group them: count threads per container, and count stacks by the line where your code starts, with `jq ... | sort | uniq -c`."}
 ],
 "terms": [
  {"term": "Virtual thread", "plain": "A thread the JVM manages itself. While it waits, it lets go of its carrier, and its stack waits on the heap."},
  {"term": "Bulkhead", "plain": "A separate, shared limit on one outside service, so one slow service can't take every thread or connection."},
  {"term": "Deadline", "plain": "One point in time for the whole request. Every wait inside the request uses whatever is left of it."},
  {"term": "Small-amount rule", "plain": "This lab's fallback, which banks call stand-in: when a check can't answer in time, small amounts go through unchecked and larger ones are refused."},
  {"term": "Fail-fast fan-out", "plain": "Running several checks at once and stopping all of them at the first failure or no."},
  {"term": "Pinning", "plain": "A virtual thread that waits but can't let go of its carrier, so the carrier waits with it."},
  {"term": "Thread container", "plain": "A group in a JSON thread dump: the executor or scope that started a set of threads."}
 ],
 "explain_back": {
  "prompt": "Design review. A sceptical senior engineer has read the whole ledger, all three lessons of it, and asks: \"Why virtual threads and a thread pool in the same program? Why 20 safety permits and not 200? What happens to the money when the safety service is down, when the program is stopped, and when two copies of it run at once?\" Defend your design, and say plainly what it doesn't handle.",
  "answer": "Requests mostly wait, on the safety service, the limit check and the ledger, so each one gets its own virtual thread. Little's law says about 300 are in flight normally and thousands on a bad day, and a waiting virtual thread costs a little heap. The ledger pool is not there to save threads. It is the limit on the journal: 8 platform threads, because 1,600 transfers a second at 5 ms of journal writing is 8 in flight, and 80 queue slots, because that is 50 ms of waiting. When it is full, a counted rejection turns overload into a fast \"busy\" that the customer retries with the same transfer id.\n\nThe 20 permits come from what the safety service can take and from Little's law: at 20 ms a call, they pass about 1,000 checks a second, above our peak. If the service allows more, the number goes up; it belongs to the service, not to us. When the safety service is down, every request still answers within its 300 ms deadline. The bulkhead caps what the service sees, the deadline interrupts calls so their permits come back, and the small-amount rule lets small transfers through and turns the rest away. Money only moves through `apply`, which keeps the three rules under per-account locks taken in id order, so a fallback can't break the books; it only takes a risk we chose on purpose.\n\nWhen the program is stopped, lesson 2's shutdown drains the pool or hands back the transfers that never started, so nothing accepted vanishes, as long as the journal on disk survives. What this design doesn't handle is anything that needs shared state. Two copies of the program each have their own ledger in memory, and their locks protect nothing across the two. A transfer sent again after a crash needs the journal replayed and a check that each transfer id is applied only once. A production version keeps balances in a database, with row locks in id order or one owner per account, and keeps the rest of this design as it is."
 },
 "deeper": {
  "minutes": 12,
  "body": """What a production version of this ledger adds, roughly in the order I'd build it:

- Lasting state: balances and the journal in a database, row locks taken in account id order or one owner per account, a `CHECK (balance >= 0)` rule, and a unique key on the transfer id.
- The same answer for a repeated request: store each transfer's outcome by its id, so a customer who tries again after a "busy" reply or a lost connection gets the original answer, not a second transfer. This property is called idempotence.
- Numbers on every limit: permits in use and the wait for them, how often the small-amount rule fired, the ledger queue's size and rejections, time spent in the queue, journal write times, and JFR's `jdk.VirtualThreadPinned` events.
- A circuit breaker in front of the safety service: a switch that stops calling a service that keeps failing, for a while, so that on a bad day requests go straight to the fallback instead of each one waiting out its deadline.
- Request details, such as the request id, carried in a scoped value (final in JDK 25), the note pinned to the order from Structured concurrency and scoped values, or passed as a parameter, so it reaches every log line on every virtual thread.
- Load tests with realistic response times, and a test run where the safety service hangs on purpose, checked against the same rules as the lab's tests.

Structured concurrency is the JDK's own version of `screen`: the head waiter, built in. `StructuredTaskScope` is a preview API in JDK 25 (JEP 505), and still preview in JDK 26 and 27. JEP 543 makes it final in JDK 28, with the JDK 27 API. Here is the screening in the JDK 25 shape. It needs `--enable-preview`, which is why it isn't in the labs:

```java
// JDK 25, preview: javac --release 25 --enable-preview ... and java --enable-preview ...
Verdict screen(Transfer t) throws InterruptedException {
    try (var scope = StructuredTaskScope.open(Joiner.<Boolean>awaitAllSuccessfulOrThrow(),
            cf -> cf.withTimeout(budget))) {
        scope.fork(() -> { if (!safetyBulkhead.call(budget.toNanos(), () -> safety.passes(t))) throw new Declined(); return true; });
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
        scope.fork(Callable { if (!safetyBulkhead.call(budget.toNanos()) { safety.passes(t) }) throw Declined(); true })
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

A "no" becomes an exception (`Declined`, your own small exception class), because this joiner fails fast on exceptions, not on values. The scope's `close()` cancels and waits for every subtask, which is what your `finally` did by hand, and the JSON thread dump shows each scope as its own container under the request that opened it. In JDK 27, the built-in joiners throw `ExecutionException` instead of `FailedException`, so that `catch` changes when you move. On JDK 25 here, the Java version answered a small transfer with `LET_THROUGH` after 322 ms while the safety service hung, and declined in 4 ms when the limits check said no."""
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
