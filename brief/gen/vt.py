import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can explain what a virtual thread is and what happens when it blocks, run blocking code with one virtual thread per task, cap what reaches a database or partner API with a shared `Semaphore`, find and fix the traps (pinning, `ThreadLocal` caches, CPU-bound work), and move a real pool-based service to virtual threads while measuring that it worked. You also meet the two Loom features around them: structured concurrency, still preview, and scoped values, final in JDK 25.

You need the basics from the first track (starting, joining and interrupting threads, locks and semaphores) and from the executors track (`ExecutorService`, `Future`, and sizing a pool with Little's law). Install JDK 25, the current LTS. JDK 24 removed most pinning, and the advice changes with it, so the lessons always say which JDK a fact applies to.

The labs live in `labs/vthreads`, one package per lesson (`workbench.vthreads.l01` to `l06`). They compile for JDK 21 and use only final JDK 21 APIs, so they run on 21 and on 25. Lessons 1 to 5 have Java labs, and lesson 6 is in Kotlin. Run `./gradlew :vthreads:test --tests 'workbench.vthreads.lNN.*'` from `labs/` until it passes, and use `solutionTest` to check the reference answers. The Try-it demos run with `./gradlew :vthreads:demo -Pmain=...`. Lesson 5's preview demos live in `labs/vthreads/preview/` and run outside Gradle on JDK 25."""

CHEATSHEET = """## Versions

| Feature | JDK 21 (LTS) | JDK 24 | JDK 25 (LTS) | JDK 26 and 27 | JDK 28 |
|---|---|---|---|---|---|
| Virtual threads | final (JEP 444) | `synchronized` no longer pins (JEP 491) | final, with the fix | final | final |
| Scoped values | preview | preview | **final** (JEP 506) | final | final |
| Structured concurrency | preview, old subclass API | preview | preview, `open()` + `Joiner` (JEP 505) | preview (JEP 525, JEP 533) | final (JEP 543) |
| Pinning check | `-Djdk.tracePinnedThreads` or JFR | JFR only (the property was removed) | JFR only | JFR only | JFR only |

## Starting virtual threads

```java
Thread t = Thread.ofVirtual().name("auth-", 0).start(() -> settle(p));     // one named thread
try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Receipt>> fs = batch.stream().map(p -> perTask.submit(() -> issuer.authorize(p))).toList();
    for (Future<Receipt> f : fs) receipts.add(f.get());                      // fork all, then join
}                                                                            // close() waits for every task
```

```kotlin
val t = Thread.ofVirtual().name("auth-", 0).start { settle(p) }             // one named thread
Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
    val fs = batch.map { p -> perTask.submit(Callable { issuer.authorize(p) }) }
    fs.map { it.get() }                                                      // fork all, then join
}                                                                            // close() waits for every task
```

Never pool virtual threads. One task, one new virtual thread.

## Limiting a downstream

```java
private final Semaphore issuerLimit = new Semaphore(20, true);   // one per downstream, shared by all callers

Auth authorize(Payment p) throws InterruptedException {
    issuerLimit.acquire();                                       // outside the try
    try {
        return http.authorize(p);                                // only the call that needs the limit
    } finally {
        issuerLimit.release();
    }
}
```

```kotlin
private val issuerLimit = Semaphore(20, true)                    // one per downstream, shared by all callers

fun authorize(p: Payment): Auth {
    issuerLimit.acquire()                                        // outside the try
    try {
        return http.authorize(p)                                 // only the call that needs the limit
    } finally {
        issuerLimit.release()
    }
}
```

Use `tryAcquire(200, MILLISECONDS)` to fail fast with a 503 instead of waiting forever.

## Little's law

| Question | Formula | Example |
|---|---|---|
| How many in flight? | rate × time | 400/s × 0.12 s = 48 |
| How many threads did the old pool need? | rate × time per request | 200/s × 0.335 s = 67 |
| Most a limit can serve | permits / time each permit is held | 10 / 0.02 s = 500/s |

## What a blocking call does to the carrier

| Call | On JDK 21 | On JDK 25 |
|---|---|---|
| `Thread.sleep`, socket I/O, `LockSupport.park`, locks, queues, futures | unmounts | unmounts |
| Blocking inside `synchronized` or `Object.wait()` | **pins** | unmounts |
| Blocking inside a class initializer, or under a native frame | pins | **pins** |
| File I/O | captures the carrier; the scheduler adds a temporary one | same |
| Pure CPU work | keeps the carrier until it blocks (no time slicing) | same |

## Traps

| Trap | What you see | Fix |
|---|---|---|
| `synchronized` around I/O on JDK 21 to 23 | p99 jumps, CPU low, carriers all busy | JDK 25, or `ReentrantLock` |
| Slow `static {}` or Kotlin `object` init | one long pin per class | load at startup or lazily, not in `<clinit>` |
| `ThreadLocal` used as a cache | one object per request, more GC | share an immutable object (`DateTimeFormatter`) |
| CPU-heavy step on a virtual thread | other requests stall behind it | a bounded platform pool for CPU work |
| The old pool was your database limit | pool timeouts after the switch | a `Semaphore` sized to the pool, around DB calls only |
| Bigger connection pool "to match" | a slower database, session limits hit | keep the pool small; queue in the service |

## Finding problems

```bash
java -XX:StartFlightRecording=filename=rec.jfr,settings=profile -jar service.jar
jfr print --events jdk.VirtualThreadPinned rec.jfr                  # pins over 20 ms, with stacks
jcmd <pid> Thread.dump_to_file -format=json threads.json            # every virtual thread, grouped
```

After the switch, ignore the thread count. Watch requests in flight, each semaphore's queue length, and the pool's pending connections. A growing queue with flat throughput marks the saturated downstream.

## Structured concurrency (JDK 25, preview) and scoped values (JDK 25, final)

```java
static final ScopedValue<String> TENANT = ScopedValue.newInstance();

Quote quote(String id) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {                  // fail fast by default
        Subtask<Customer> customer = scope.fork(() -> crm.find(id));
        Subtask<Limit> limit = scope.fork(() -> limits.check(id));   // forks can read TENANT
        scope.join();                                               // JDK 25: FailedException; JDK 27: ExecutionException
        return new Quote(customer.get(), limit.get());
    }                                                               // close(): no subtask left running
}
// caller: ScopedValue.where(TENANT, "bank-a").call(() -> quote(id));   // call() may throw
```

```kotlin
val TENANT: ScopedValue<String> = ScopedValue.newInstance()

fun quote(id: String): Quote =
    StructuredTaskScope.open<Any>().use { scope ->                  // fail fast by default
        val customer = scope.fork(Callable { crm.find(id) })
        val limit = scope.fork(Callable { limits.check(id) })       // forks can read TENANT
        scope.join()                                                // JDK 25: FailedException; JDK 27: ExecutionException
        Quote(customer.get(), limit.get())
    }                                                               // close(): no subtask left running
// caller: ScopedValue.where(TENANT, "bank-a").run(Runnable { quote(id) })
```

Preview code needs `--enable-preview` and the matching JDK. In Kotlin coroutine code, use `coroutineScope` and a coroutine context element instead.

## Frameworks

| Framework | Switch | Note |
|---|---|---|
| Quarkus | `@RunOnVirtualThread` on an endpoint, class or `@Incoming` method | no global switch; `quarkus.thread-pool.max-threads` no longer caps those endpoints |
| Spring Boot 3.2+ | `spring.threads.virtual.enabled=true` | the web server and Spring's task executors use virtual threads |

Neither adds downstream limits. Those are your semaphores.

## Migration checklist

1. Run JDK 25.
2. Replace pools that run blocking work with one virtual thread per task.
3. Write down every limit the old pool gave you as a shared semaphore.
4. Keep connection pools small, sized from the database and multiplied by pods.
5. Replace `ThreadLocal` caches; move context to arguments or scoped values.
6. Keep CPU-heavy work on a bounded platform pool.
7. Put a deadline on every wait, then measure before and after with the same load test."""

RECAP = [
 "A platform thread is an OS thread, so a server gets thousands, not millions. Little's law (in flight = rate × time) says how many a blocking service needs.",
 "A virtual thread is a `Thread` that unmounts from its carrier at blocking calls. Its stack waits on the heap, and a few carriers (one per core) run all of them.",
 "Virtual threads give scale, not speed: one request is no faster, and CPU-bound work gains nothing because there is no time slicing.",
 "Use one new virtual thread per task, usually through `newVirtualThreadPerTaskExecutor()` in try-with-resources. Never pool them.",
 "Limit a scarce downstream with one shared `Semaphore`, held only around its calls, sized from what the downstream allows.",
 "On JDK 21 to 23, blocking inside `synchronized` pins the carrier. JDK 24 fixed it; on JDK 25 class initializers and native frames still pin. Find pins with JFR's `jdk.VirtualThreadPinned`.",
 "`ThreadLocal` caches become one object per task. Share immutable objects, and move request context to arguments or scoped values (final in JDK 25).",
 "Structured concurrency ties subtasks to a block, cancels siblings on failure and waits for all of them. `StructuredTaskScope` is preview until JDK 28.",
 "Migrating means writing down the limits the old pool gave you, keeping connection pools small, and measuring in-flight requests and queue lengths, not thread counts."
]

QUIZ = [
 {"q": "An endpoint receives 1,500 requests per second, and each one spends 200 ms waiting on a partner API. With one thread per request, about how many threads are busy at once?",
  "options": ["About 8", "About 300", "About 1,500", "About 7,500"], "answer": 1,
  "why": "Little's law: in flight = 1,500/s × 0.2 s = 300. With thread-per-request, that's also the number of threads. 7,500 multiplies by 5 instead of 0.2, and 1,500 forgets the time."},
 {"q": "Which workload gains the most from moving to virtual threads?",
  "options": [
   "8,000 concurrent requests that each wait 150 ms on HTTP and database calls",
   "Resizing 10,000 images on an 8-core machine",
   "A parallel stream that sums a large array",
   "One batch job that reads a single large file from start to end"
  ], "answer": 0,
  "why": "Virtual threads help when many tasks spend most of their time blocked. Image resizing and summing are CPU-bound, so at most one virtual thread per core computes at once, the same as a pool. A single sequential job has nothing to overlap."},
 {"q": "A virtual thread prints `Thread.currentThread()` before and after `Thread.sleep(10)`. What can differ between the two lines?",
  "options": [
   "The thread id, because a new virtual thread continues the work",
   "Nothing can differ: a virtual thread stays on one carrier for life",
   "The carrier worker shown after the `@`; the virtual thread itself is the same",
   "The second print never happens, because `sleep` throws on a virtual thread"
  ], "answer": 2,
  "why": "`currentThread()` always returns the virtual thread, so its id stays the same. The sleep unmounts it, and when it wakes, any free carrier can mount it, so the `ForkJoinPool-1-worker-N` part of `toString()` can change."},
 {"q": "10,000 virtual threads must call a fraud API that allows 50 concurrent calls. Which design is right?",
  "options": [
   "`Executors.newFixedThreadPool(50, Thread.ofVirtual().factory())` for all request handling",
   "A `new Semaphore(50)` created inside each request handler",
   "No limit: virtual threads are cheap, so the API copes",
   "One `Semaphore(50)` shared by all requests, held only around the fraud call"
  ], "answer": 3,
  "why": "The limit belongs to the fraud API, so one shared semaphore guards just that call. A pool of virtual threads caps the whole request and is the anti-pattern from lesson 3. A semaphore per request gives each request its own 50 permits, which limits nothing."},
 {"q": "On JDK 25, which of these still pins a virtual thread to its carrier?",
  "options": [
   "Blocking on a socket read inside a `synchronized` block",
   "Blocking inside a class's static initializer",
   "Waiting in `ReentrantLock.lock()`",
   "Waiting in `BlockingQueue.take()`"
  ], "answer": 1,
  "why": "JDK 24 (JEP 491) stopped `synchronized` from pinning, and `java.util.concurrent` locks and queues always parked properly. Class initializers run through VM frames, so blocking inside one still pins on JDK 25."},
 {"q": "You want to prove that a JDK 25 service has no pinning under load. What do you use?",
  "options": [
   "`-Djdk.tracePinnedThreads=full`, and check that nothing is printed",
   "`jstack <pid>`, looking for blocked carriers",
   "A JFR recording with `jdk.VirtualThreadPinned`, printed with `jfr print`",
   "`Thread.getAllStackTraces()` from a debug endpoint"
  ], "answer": 2,
  "why": "The JFR event is on by default with a 20 ms threshold and records the stack. `-Djdk.tracePinnedThreads` was removed in JDK 24, so its silence proves nothing. `jstack` and `getAllStackTraces()` don't show parked virtual threads."},
 {"q": "Which statement about JDK 25 is true?",
  "options": [
   "Scoped values are final; `StructuredTaskScope` is still a preview API",
   "Both scoped values and `StructuredTaskScope` are final",
   "`StructuredTaskScope` is final; scoped values are still preview",
   "Both are still preview and need `--enable-preview`"
  ], "answer": 0,
  "why": "JEP 506 made scoped values final in JDK 25. Structured concurrency stays in preview through JDK 25, 26 and 27, and JEP 543 makes it final in JDK 28."},
 {"q": "Inside `ScopedValue.where(TENANT, \"bank-a\").run(...)`, code starts `Thread.ofVirtual().start(task)`. What does `TENANT.isBound()` return inside `task`?",
  "options": [
   "`true`, because virtual threads inherit their creator's scoped values",
   "`true`, but only while `run()` is still active",
   "It throws `IllegalStateException`",
   "`false`, because only `StructuredTaskScope` forks inherit the binding"
  ], "answer": 3,
  "why": "A thread you start yourself could outlive the `run()` call, so it gets no binding. Only subtasks forked in a `StructuredTaskScope`, which must end before the scope does, see the parent's scoped values."},
 {"q": "A hand-built fail-fast scope cancels a slow sibling with `future.cancel(true)` and then calls `close()` on its `newVirtualThreadPerTaskExecutor()`. On JDK 21, what is the problem?",
  "options": [
   "`cancel(true)` doesn't interrupt virtual threads",
   "`close()` can return while the cancelled task is still running its `finally` block",
   "`close()` waits forever, because a cancelled task never finishes",
   "Nothing: this is exactly how `StructuredTaskScope` works inside"
  ], "answer": 1,
  "why": "`cancel(true)` interrupts the thread but marks the future done at once, and the JDK 21 executor counts the task as finished when its future is done. So `close()` stops waiting while cleanup still runs. `shutdownNow()` interrupts without completing the futures."},
 {"q": "A service ran on a fixed pool of 20 threads with a 20-connection database pool. After moving to one virtual thread per request, the pool times out at every peak. What is the right fix?",
  "options": [
   "Raise the connection pool to 2,000 connections",
   "Go back to the fixed pool of 20 threads for all request handling",
   "Add a shared `Semaphore(20)` around the database calls only, with a `tryAcquire` deadline",
   "Raise the pool's connection timeout to several minutes"
  ], "answer": 2,
  "why": "The fixed pool was an unwritten limit on the database. The semaphore puts it back where it belongs, without capping the calls that never needed it, and gives you a visible queue and a deadline. A huge pool overloads the database, and a long timeout turns overload into very slow requests."}
]

T = {"id": "vt", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/vt.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
