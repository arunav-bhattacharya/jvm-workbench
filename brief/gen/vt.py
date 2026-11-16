import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """This track follows one restaurant through six lessons. It starts with a personal waiter for every table, who spends most of the evening standing at the kitchen door. Then four waiters learn to carry order slips and clip a waiting slip to a board by the door. After that come 20 tokens on a hook by the grill, a hot pan a waiter can't put down, a head waiter who calls his helpers back, and a note pinned to the order. The last lesson moves an old restaurant over to slips without losing the limit its fixed team gave for free. Underneath runs one program, a shop's checkout of 200 ms: 40 ms at the stock service, 120 ms waiting for the bank, 35 ms in the database and 5 ms of real work.

By the end you can explain what a virtual thread is and what happens when it waits, run blocking code with one virtual thread per task, keep a database safe with one shared `Semaphore`, and find and fix the traps: pinning, `ThreadLocal` caches and work that only computes. You can also move a pool-based service to virtual threads and measure that it worked. On the way you meet two related features: structured concurrency, still a preview, and scoped values, final in JDK 25.

You need the basics from the first track (starting, joining and interrupting threads, locks and semaphores) and from the executors track (`ExecutorService`, `Future`, and sizing a pool with Little's law). Install JDK 25, the current long-term-support release. JDK 24 removed most pinning, and the advice changes with it, so the lessons always say which JDK a fact applies to. The labs live in `labs/vthreads`, one package per lesson (`workbench.vthreads.l01` to `l06`). They compile for JDK 21 and use only final JDK 21 APIs, so they run on 21 and on 25. Lessons 1 to 5 have Java labs, and lesson 6 is in Kotlin. Run `./gradlew :vthreads:test --tests 'workbench.vthreads.lNN.*'` from `labs/` until it passes, and use `solutionTest` to check the reference answers. The Try-it demos run with `./gradlew :vthreads:demo -Pmain=...`, and lesson 5's preview demos live in `labs/vthreads/preview/` and run outside Gradle on JDK 25."""

CHEATSHEET = """## The pictures, and what they stand for

| Picture | What it stands for | Lesson |
|---|---|---|
| A personal waiter who stands at the kitchen door | thread-per-request on platform threads: a blocked thread does no work, but nobody else can use it | 1 |
| Four waiters and order slips | carrier threads and virtual threads; the slip's notes are the continuation | 2 |
| The board by the kitchen door | the heap, where an unmounted virtual thread's stack waits | 2 |
| A waiter chopping onions, slip in his pocket | no time slicing: a virtual thread that computes keeps its carrier | 2, 4 |
| 20 tokens on a hook by the grill | one shared `Semaphore(20)` in front of the database | 3 |
| A hot pan a waiter can't put down | pinning: on JDK 21 to 23 inside `synchronized`, on JDK 25 in static initializers and native frames | 4 |
| An apron pocket with a pen in it | a `ThreadLocal` cache: one object per thread, so one per task with virtual threads | 4 |
| A head waiter who calls his helpers back | a scope: the first failure cancels the rest, and close waits for every subtask | 5 |
| A note pinned to the order | a scoped value: everyone on the order can read it, nobody can change it | 5 |
| 10 waiters who quietly protected 10 burners | the old pool's hidden limit, written back as a semaphore | 6 |

## Versions

| Feature | JDK 21 (LTS) | JDK 24 | JDK 25 (LTS) | JDK 26 and 27 | JDK 28 |
|---|---|---|---|---|---|
| Virtual threads | final (JEP 444) | `synchronized` no longer pins (JEP 491) | final, with the fix | final | final |
| Scoped values | preview | preview | **final** (JEP 506) | final | final |
| Structured concurrency | preview, old subclass API | preview | preview, `open()` + `Joiner` (JEP 505) | preview (JEP 525, JEP 533) | final (JEP 543) |
| Pinning check | `-Djdk.tracePinnedThreads` or JFR | JFR only (the property was removed) | JFR only | JFR only | JFR only |

## Starting virtual threads

```java
Thread t = Thread.ofVirtual().name("checkout-", 0).start(() -> checkout(basket));   // one named thread
try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Receipt>> fs = baskets.stream().map(b -> perTask.submit(() -> checkout(b))).toList();
    for (Future<Receipt> f : fs) receipts.add(f.get());                                // fork all, then join
}                                                                                      // close() waits for every task
```

```kotlin
val t = Thread.ofVirtual().name("checkout-", 0).start { checkout(basket) }           // one named thread
Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
    val fs = baskets.map { b -> perTask.submit(Callable { checkout(b) }) }
    fs.map { it.get() }                                                                // fork all, then join
}                                                                                      // close() waits for every task
```

Never pool virtual threads. One task, one new virtual thread.

## Limiting a scarce resource

```java
private final Semaphore connections = new Semaphore(20, true);   // one per resource, shared by all callers

Receipt save(Order order) throws InterruptedException {
    connections.acquire();                                       // outside the try
    try {
        return database.save(order);                             // only the call that needs the limit
    } finally {
        connections.release();
    }
}
```

```kotlin
private val connections = Semaphore(20, true)                    // one per resource, shared by all callers

fun save(order: Order): Receipt {
    connections.acquire()                                        // outside the try
    try {
        return database.save(order)                              // only the call that needs the limit
    } finally {
        connections.release()
    }
}
```

Use `tryAcquire(200, MILLISECONDS)` to answer "busy, try again" fast instead of waiting forever.

## Little's law

| Question | Formula | Example |
|---|---|---|
| How many in flight? | rate × time | 400/s × 0.12 s = 48 |
| How many threads does thread-per-request need? | rate × time per request | 1,500/s × 0.2 s = 300 |
| Most a limit can serve | permits / time each permit is held | 10 / 0.02 s = 500/s |

## What a blocking call does to the carrier

| Call | On JDK 21 | On JDK 25 |
|---|---|---|
| `Thread.sleep`, socket I/O, `LockSupport.park`, locks, queues, futures | unmounts | unmounts |
| Blocking inside `synchronized` or `Object.wait()` | **pins** | unmounts |
| Blocking inside a static initializer, or under a native frame | pins | **pins** |
| File I/O | keeps the carrier; the scheduler adds a temporary one | same |
| Pure computing | keeps the carrier until it blocks (no time slicing) | same |

## Traps

| Trap | What you see | Fix |
|---|---|---|
| `synchronized` around a slow call on JDK 21 to 23 | slow requests, idle processor, every carrier busy | JDK 25, or `ReentrantLock` |
| Slow `static {}` or Kotlin `object` setup | one long pin per class | load at startup or lazily, not in `<clinit>` |
| `ThreadLocal` used as a cache | one object per request, more garbage collection | share an immutable object (`DateTimeFormatter`) |
| Heavy computing on a virtual thread | other requests stall behind it | a bounded platform pool for that work |
| The old pool was your database limit | connection pool timeouts after the switch | a `Semaphore` sized to the pool, around database calls only |
| A bigger connection pool "to match" | a slower database | keep the pool small; let requests wait in front of it |

## Finding problems

```bash
java -XX:StartFlightRecording=filename=rec.jfr,settings=profile -jar shop.jar
jfr print --events jdk.VirtualThreadPinned --stack-depth 20 rec.jfr   # pins over 20 ms, with stacks
jcmd <pid> Thread.dump_to_file -format=json threads.json              # every virtual thread, grouped
```

After the switch, ignore the thread count. Watch requests in flight, each semaphore's queue length, and the connection pool's waiting count. A growing queue with flat throughput marks the full resource.

## Structured concurrency (JDK 25, preview) and scoped values (JDK 25, final)

```java
static final ScopedValue<String> CUSTOMER = ScopedValue.newInstance();

Receipt checkout(Order order) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {                  // fail fast by default
        Subtask<Approval> bank = scope.fork(() -> theBank.approve(order));
        Subtask<Stock> stock = scope.fork(() -> stockService.check(order));   // forks can read CUSTOMER
        scope.join();                                               // JDK 25: FailedException; JDK 27: ExecutionException
        return new Receipt(stock.get(), bank.get());
    }                                                               // close(): no subtask left running
}
// caller: ScopedValue.where(CUSTOMER, "ann").call(() -> checkout(order));   // call() may throw
```

```kotlin
val CUSTOMER: ScopedValue<String> = ScopedValue.newInstance()

fun checkout(order: Order): Receipt =
    StructuredTaskScope.open<Any>().use { scope ->                  // fail fast by default
        val bank = scope.fork(Callable { theBank.approve(order) })
        val stock = scope.fork(Callable { stockService.check(order) })   // forks can read CUSTOMER
        scope.join()                                                // JDK 25: FailedException; JDK 27: ExecutionException
        Receipt(stock.get(), bank.get())
    }                                                               // close(): no subtask left running
// caller: ScopedValue.where(CUSTOMER, "ann").run(Runnable { checkout(order) })
```

Preview code needs `--enable-preview` and the matching JDK. In Kotlin coroutine code, use `coroutineScope` and a coroutine context element instead.

## Migration checklist

1. Run JDK 25.
2. Replace pools that run blocking work with one virtual thread per task.
3. Write down every limit the old pool gave you as a shared semaphore.
4. Keep connection pools small, sized from the database and multiplied by the copies of the service.
5. Replace `ThreadLocal` caches; move a request's details to arguments or scoped values.
6. Keep heavy computing on a bounded platform pool.
7. Put a deadline on every wait, then measure before and after with the same load test.

## If you use a web framework

| Framework | Switch | Note |
|---|---|---|
| Spring Boot 3.2+ | `spring.threads.virtual.enabled=true` | the web server and Spring's task executors use virtual threads |
| Quarkus | `@RunOnVirtualThread` on an endpoint or class | no global switch; `quarkus.thread-pool.max-threads` no longer caps those endpoints |

Neither adds your limits. Those are still your semaphores."""

RECAP = [
 "A platform thread is an operating system thread, so a server gets thousands, not millions. Little's law (in flight = rate × time) says how many a waiting service needs: the personal waiter at the kitchen door.",
 "A virtual thread is a `Thread` that unmounts from its carrier when it waits. Its stack waits on the heap, like a slip on the board, and a few carriers (one per core) run all of them.",
 "Virtual threads give scale, not speed: one request is no faster, and work that only computes gains nothing, because there is no time slicing.",
 "Use one new virtual thread per task, usually through `newVirtualThreadPerTaskExecutor()` in try-with-resources. Never pool them.",
 "Limit a scarce resource with one shared `Semaphore`, held only around its calls and sized from what the resource allows: the tokens at the grill.",
 "On JDK 21 to 23, blocking inside `synchronized` pins the carrier, the hot pan. JDK 24 fixed it; on JDK 25 static initializers and native frames still pin. Find pins with JFR's `jdk.VirtualThreadPinned`.",
 "A `ThreadLocal` cache becomes one object per task, a new pen for every order. Share immutable objects, and move a request's details to arguments or scoped values (final in JDK 25).",
 "Structured concurrency ties subtasks to a block, cancels the others on the first failure and waits for all of them, like a head waiter. `StructuredTaskScope` is a preview until JDK 28.",
 "Moving a service means writing down the limits the old pool gave you, keeping connection pools small, giving every wait a deadline, and measuring queues, not thread counts."
]

QUIZ = [
 {"q": "A shop's checkout receives 1,500 requests a second, and each one spends 200 ms, mostly waiting for the bank. With one thread per request, about how many threads are busy at once?",
  "options": ["About 8", "About 300", "About 1,500", "About 7,500"], "answer": 1,
  "why": "Little's law: in flight = 1,500/s × 0.2 s = 300. With thread-per-request, that's also the number of threads. 7,500 multiplies by 5 instead of 0.2, and 1,500 forgets the time."},
 {"q": "Which program gains the most from moving to virtual threads?",
  "options": [
   "8,000 requests at once that each wait 150 ms for web services and the database",
   "Resizing 10,000 photos on an 8-core machine",
   "A parallel stream that adds up a large array",
   "One batch job that reads a single large file from start to end"
  ], "answer": 0,
  "why": "Virtual threads help when many tasks spend most of their time waiting. Resizing photos and adding numbers only compute, so at most one virtual thread per core works at once, the same as a pool. A single job that runs in order has nothing to overlap."},
 {"q": "A virtual thread prints `Thread.currentThread()` before and after `Thread.sleep(10)`. What can differ between the two lines?",
  "options": [
   "The thread id, because a new virtual thread carries on with the work",
   "Nothing can differ: a virtual thread stays on one carrier for life",
   "The carrier worker shown after the `@`; the virtual thread itself is the same",
   "The second print never happens, because `sleep` throws on a virtual thread"
  ], "answer": 2,
  "why": "`currentThread()` always returns the virtual thread, so its id stays the same. The sleep unmounts it, and when it wakes, any free carrier can mount it, so the `ForkJoinPool-1-worker-N` part of `toString()` can change."},
 {"q": "10,000 virtual threads must call the bank's web service, which allows 50 calls at once from the shop. Which design is right?",
  "options": [
   "`Executors.newFixedThreadPool(50, Thread.ofVirtual().factory())` for all request handling",
   "A `new Semaphore(50)` created inside each request handler",
   "No limit: virtual threads are cheap, so the bank copes",
   "One `Semaphore(50)` shared by all requests, held only around the bank call"
  ], "answer": 3,
  "why": "The limit belongs to the bank's service, so one shared semaphore guards just that call. A pool of virtual threads caps the whole request and is the trap from lesson 3. A semaphore per request gives each request its own 50 permits, which limits nothing."},
 {"q": "On JDK 25, which of these still pins a virtual thread to its carrier?",
  "options": [
   "Blocking on a socket read inside a `synchronized` block",
   "Blocking inside a class's static initializer",
   "Waiting in `ReentrantLock.lock()`",
   "Waiting in `BlockingQueue.take()`"
  ], "answer": 1,
  "why": "JDK 24 (JEP 491) stopped `synchronized` from pinning, and `java.util.concurrent` locks and queues always parked properly. Static initializers run through the JVM's own frames, so blocking inside one still pins on JDK 25."},
 {"q": "You want to prove that a program on JDK 25 has no pinning under load. What do you use?",
  "options": [
   "`-Djdk.tracePinnedThreads=full`, and check that nothing is printed",
   "`jstack <pid>`, looking for blocked carriers",
   "A JFR recording with `jdk.VirtualThreadPinned`, printed with `jfr print`",
   "`Thread.getAllStackTraces()` from a debug page"
  ], "answer": 2,
  "why": "The JFR event is on by default with a 20 ms threshold and records the stack. `-Djdk.tracePinnedThreads` was removed in JDK 24, so its silence proves nothing. `jstack` and `getAllStackTraces()` don't show parked virtual threads."},
 {"q": "Which statement about JDK 25 is true?",
  "options": [
   "Scoped values are final; `StructuredTaskScope` is still a preview API",
   "Both scoped values and `StructuredTaskScope` are final",
   "`StructuredTaskScope` is final; scoped values are still a preview",
   "Both are still previews and need `--enable-preview`"
  ], "answer": 0,
  "why": "JEP 506 made scoped values final in JDK 25. Structured concurrency stays a preview through JDK 25, 26 and 27, and JEP 543 makes it final in JDK 28."},
 {"q": "Inside `ScopedValue.where(CUSTOMER, \"ann\").run(...)`, code starts `Thread.ofVirtual().start(task)`. What does `CUSTOMER.isBound()` return inside `task`?",
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
  "why": "`cancel(true)` interrupts the thread but marks the future done at once, and the JDK 21 executor counts the task as finished when its future is done. So `close()` stops waiting while the cleanup still runs. `shutdownNow()` interrupts without completing the futures."},
 {"q": "A service ran on a fixed pool of 20 threads with a 20-connection database pool. After moving to one virtual thread per request, the connection pool times out at every busy hour. What is the right fix?",
  "options": [
   "Raise the connection pool to 2,000 connections",
   "Go back to the fixed pool of 20 threads for all request handling",
   "Add a shared `Semaphore(20)` around the database calls only, with a `tryAcquire` deadline",
   "Raise the pool's connection timeout to several minutes"
  ], "answer": 2,
  "why": "The fixed pool was an unwritten limit on the database. The semaphore puts it back where it belongs, without capping the calls that never needed it, and gives you a queue you can see and a deadline you choose. A huge pool overloads the database, and a long timeout turns overload into very slow requests."}
]

T = {"id": "vt", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/vt.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
