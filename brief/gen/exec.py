import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

INTRO = """This track runs one restaurant kitchen from opening time to closing time. A thread pool is its team of cooks: a few threads, made once, that take tasks from a queue the way cooks take tickets from a rail. By the end, you can hand work to a pool and close it without losing any. You can predict where `ThreadPoolExecutor` puts every task in a burst, and give it a queue that says no when the kitchen is full. Its size will come from measurements, not habit, for cooks who chop all day and for cooks who mostly wait for the oven. You can wait for a result with a time limit, cancel a task so that it really stops, and keep a repeating job alive when one run fails. You can chain steps with `CompletableFuture`, a ticket that carries its own instructions, and ask three suppliers at once without one bad answer spoiling the rest. Then you'll split one big sum among workers who steal from each other. Finally, you'll run it all on a busy night, with named threads, failures you can see, numbers to watch and a calm close.

You need the first track, Threads and the bugs they cause: what a thread is, race conditions, `synchronized` and interruption. The memory model track helps, but isn't required. Each lesson sets up its example in plain words before it puts any weight on it. Besides the kitchen, you'll meet a shop's checkout that asks the bank to charge a card, and a rate service that turns euros into dollars. Later come three flour suppliers and a year of card fees to add up. Install JDK 25. The labs compile for JDK 21, so they also run on 21 or later. A few things changed in JDK 25, such as the pool `CompletableFuture` uses on a small machine, and `ForkJoinPool` learning to schedule tasks. Where that happens, the lesson says so and keeps the code out of the labs.

Every lesson has a lab in `labs/executors`, in the package `workbench.executors.lNN`. The labs run from a tiny pool you build yourself in lesson 1 to a pool ready for production in lesson 9. The labs are in Java, and every code sample and Try-it program also comes in Kotlin. The tests never depend on lucky timing. They hold tasks in place with latches and barriers, count how many tasks run at the same moment, and model a scheduler's timetable in make-believe milliseconds. Their waits have generous time limits, so a wrong answer fails within seconds instead of hanging the build. From `labs/`, run `./gradlew :executors:test --tests 'workbench.executors.lNN.*'` until it passes. `./gradlew :executors:solutionTest` runs the same tests against the reference answers, and `./gradlew :executors:demo -Pmain=<class>` runs a demo (add `Kt` to the class name for the Kotlin version)."""

J_FLAG = """public void run() {
    try {
        rail.put(ticket);                     // waits while the rail is full
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();   // put the note back
    }                                         // and stop
}"""
K_FLAG = """override fun run() {
    try {
        rail.put(ticket)                      // waits while the rail is full
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()    // put the note back
    }                                         // and stop
}"""

J_SAFE = """scheduler.scheduleWithFixedDelay(() -> {
    try {
        refreshRate();
    } catch (RuntimeException e) {
        log.warn("rate refresh failed, keeping the last rate", e);   // report it, keep the schedule
    }
}, 0, 5, TimeUnit.SECONDS);"""
K_SAFE = """scheduler.scheduleWithFixedDelay({
    try {
        refreshRate()
    } catch (e: RuntimeException) {
        log.warn("rate refresh failed, keeping the last rate", e)    // report it, keep the schedule
    }
}, 0, 5, TimeUnit.SECONDS)"""

J_COMBINE = """// both calls start now and run side by side, on the io pool
CompletableFuture<BigDecimal> price = CompletableFuture.supplyAsync(() -> prices.priceEur(cart), io);
CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(() -> fx.rate("EUR", "USD"), io);
CompletableFuture<BigDecimal> usd = price.thenCombine(rate, BigDecimal::multiply);   // about 300 ms, not 600"""
K_COMBINE = """// both calls start now and run side by side, on the io pool
val price = CompletableFuture.supplyAsync({ prices.priceEur(cart) }, io)
val rate = CompletableFuture.supplyAsync({ fx.rate("EUR", "USD") }, io)
val usd = price.thenCombine(rate) { p, r -> p * r }                                    // about 300 ms, not 600"""

J_FORK = """protected Long compute() {
    if (to - from <= THRESHOLD) return sumByLoop();   // 1. small enough: just loop
    int mid = (from + to) >>> 1;
    SumTask left = new SumTask(a, from, mid), right = new SumTask(a, mid, to);
    left.fork();                                      // 2. another worker may take the left half
    long r = right.compute();                         // 3. this thread does the right half
    return left.join() + r;                           // 4. then collects the left half
}"""
K_FORK = """override fun compute(): Long {
    if (to - from <= THRESHOLD) return sumByLoop()    // 1. small enough: just loop
    val mid = (from + to) ushr 1
    val left = SumTask(a, from, mid)
    val right = SumTask(a, mid, to)
    left.fork()                                       // 2. another worker may take the left half
    val r = right.compute()                           // 3. this thread does the right half
    return left.join() + r                            // 4. then collects the left half
}"""

CHEAT = """## The track in one kitchen

Each lesson tied its tool to a scene in the same restaurant. The scene is the quickest way back to the rule.

| Lesson | Picture it | The rule |
|---|---|---|
| 1. Why pools | a fixed team of cooks takes tickets from one rail | Create threads once and reuse them. `shutdown()` doesn't wait. |
| 2. Inside ThreadPoolExecutor | the thrifty manager calls temporary cooks only when the rail is full | The pool queues first and grows second. Give the queue a limit. |
| 3. Sizing a pool | cooks who chop all day, cooks who wait for the oven, a kitchen with two ovens | One thread per core for computing, more for waiting. The smallest limit wins. |
| 4. Futures and cancellation | the takeaway ticket, and the manager's note on a cook's station | A time limit ends your wait, not the work. Cancelling only asks. |
| 5. Scheduled executors | two cleaners: one goes by the clock, one rests after each round | Fixed rate catches up, fixed delay doesn't. Catch inside the task. |
| 6. Composing CompletableFuture | the ticket for table 4 that carries its own instructions | Start independent calls first, then combine. Wait once, at the edge. |
| 7. Errors, timeouts, fan-out | the burned steak's note rides to the pass; the kitchen timer; three flour suppliers | Recover close to the failure. A timeout frees the caller, not the thread. |
| 8. ForkJoinPool | cooks steal from the bottom of a busy cook's stack | Fork one half, compute the other, then join. Never block in the common pool. |
| 9. Pools in production | a stuck Saturday night: name tags, the pinned note, closing the kitchen in order | Name threads, report every failure, carry the context, close in order. |

## Opening and closing a pool

| Call | What it does |
|---|---|
| `execute(r)` | runs `r`; if it throws, the worker dies and its `UncaughtExceptionHandler` prints the stack trace |
| `submit(c)` | returns a `Future`; if the task throws, the exception waits inside it and nothing prints |
| `shutdown()` | the gentle close: rejects new tasks, lets the rest finish, returns at once |
| `shutdownNow()` | the hard close: returns the tasks that never started and interrupts the running ones |
| `awaitTermination(t, unit)` | waits for the end or the timeout, and returns `true` or `false` to say which |
| `close()` (JDK 19+) | `shutdown()`, then waits with no time limit; works with try-with-resources and Kotlin's `use` |

Pool threads are not daemon threads, so a pool you never close keeps the JVM running.

## Inside ThreadPoolExecutor

Every `execute` walks four rules in order. Fewer threads than `corePoolSize`: start one. Otherwise: queue the task. Queue full: start a thread, up to `maximumPoolSize`. Still no room: call the rejection handler.

| Queue | Effect | Picture it |
|---|---|---|
| `new LinkedBlockingQueue<>()` (fixed pool) | never full, so the maximum never comes into play and overload hides as memory and waiting | a rail with no end |
| `SynchronousQueue` (cached pool) | holds nothing, so every burst becomes new threads | a plate passed straight into a free cook's hands |
| `new ArrayBlockingQueue<>(n)` | bounded: a full queue grows the pool, then rejects, so overload pushes back | a rail with room for `n` tickets |

The rejection handler decides who pays. `AbortPolicy` (the default) throws at the caller, and `CallerRunsPolicy` makes the submitting thread run the task, which slows it down. The two discard policies drop work silently. `keepAliveTime` sends idle threads above core home, and `allowCoreThreadTimeOut(true)` sends core threads home too.

## Sizing a pool

| Work | Threads | Picture it |
|---|---|---|
| all computing | about `availableProcessors()` | cooks who chop: one per board |
| mostly waiting | cores x target CPU use x (1 + wait / compute), both measured | cooks who wait for the oven |
| any traffic | Little's law: requests inside = arrival rate x time inside; a pool finishes at most threads / latency per second | the cinema ticket window |
| any path | the smallest limit further along is the ceiling, such as 20 database connections | two ovens cap the kitchen |
| several slow services | a bulkhead: a separate pool or `Semaphore` for each | a slow pizza oven mustn't hold every cook |

## Futures and cancellation

`get()` throws `ExecutionException` (the task's exception is its cause), `CancellationException` or `InterruptedException`. `get(t, unit)` adds `TimeoutException` and ends only your wait. `cancel(true)` on a `submit` future interrupts the worker, and the task stops only if it waits in a method that listens (`sleep`, `take`, `get`) or checks `isInterrupted()`. The future says cancelled at once, either way. Throwing `InterruptedException` clears the flag, so rethrow it or restore it:

""" + pair(J_FLAG, K_FLAG) + """

JDK 19 added `state()`, which reads a future without waiting; check it before `resultNow()` or `exceptionNow()`. `invokeAll` waits for every task, and `invokeAny` returns the first success and cancels the rest.

## Scheduled executors

| Method | Next run starts | Picture it |
|---|---|---|
| `schedule(task, d, unit)` | once, after `d` | drop a reservation in 15 minutes |
| `scheduleAtFixedRate` | at fixed times (initial delay + n x period); late runs start back to back to catch up | the cleaner who goes by the clock |
| `scheduleWithFixedDelay` | `delay` after the previous run ends | the cleaner who rests after each round |

Runs of one task never overlap. One uncaught exception skips every later run, and nothing is logged, so catch inside the task:

""" + pair(J_SAFE, K_SAFE) + """

On a scheduler with one thread, a slow task delays all the others. Skip `java.util.Timer`: one exception stops every task on it. JDK 25: `ForkJoinPool`, the common pool included, implements `ScheduledExecutorService` and adds `submitWithTimeout`.

## CompletableFuture

| You have | Method |
|---|---|
| `T -> U`, plain code | `thenApply` |
| `T -> CompletableFuture<U>`, another async call | `thenCompose`, which flattens it |
| a second future, and `(T, U) -> V` | `thenCombine` |
| `T -> void`, a side effect | `thenAccept` |

Work starts when you call `supplyAsync`, so start the independent calls first, then combine:

""" + pair(J_COMBINE, K_COMBINE) + """

- No pool means `ForkJoinPool.commonPool()`, shared by the whole JVM. Up to JDK 24, a common pool with fewer than 2 threads meant a new thread per task; JDK 25 always uses the common pool. Pass a pool for anything that waits.
- A plain step runs on the thread that completed the stage before it, or on the caller if that stage was already done. `thenApplyAsync(fn, pool)` moves a slow step.
- `join()` throws the unchecked `CompletionException` and has no time limit. Wait once, at the edge, with `get(t, unit)`, and never wait inside a stage.

## Errors, timeouts and fan-out

| Handler | Runs on | Changes the outcome? |
|---|---|---|
| `exceptionally(ex -> value)` | failure | yes: a value instead |
| `handle((value, ex) -> result)` | both | yes: any result |
| `whenComplete((value, ex) -> ...)` | both | no: it only looks |
| `exceptionallyCompose(ex -> future)` (JDK 12) | failure | yes: another future |

- A failure skips every stage until a handler. Recover as close to the failure as you can.
- An exception thrown inside a stage arrives in a `CompletionException` envelope; `completeExceptionally` and `orTimeout` store it bare. Unwrap with `getCause()` before you test the type.
- `orTimeout` and `completeOnTimeout` (JDK 9) free the caller while the cook stays on hold, and `cancel(true)` on a `CompletableFuture` interrupts nothing. Give each call its own timeout in the client too.
- `allOf` waits for all and fails if any failed; `anyOf` takes the first to finish, failures included. For a fan-out, give each call its own deadline and turn its failure into "no answer" with `handle`, then `allOf`.

## ForkJoinPool and parallel streams

""" + pair(J_FORK, K_FORK) + """

- Fork, compute, join, in that order. `fork(); join(); compute()` gives the right total, one leaf at a time.
- Stop splitting at roughly 100 to 10,000 basic steps per leaf, then measure.
- Each worker works from the top of its own deque, and idle workers steal the oldest, biggest task from the bottom of another's.
- Parallel streams use the common pool (`availableProcessors() - 1` workers plus the caller), shared with every `CompletableFuture` step that names no pool. Never write to shared state in them, and never block in them.

## Pools in production

| Question | Answer | Picture it |
|---|---|---|
| Which pool is stuck? | name threads: `Thread.ofPlatform().name("grill-", 0).factory()` (JDK 21+) | name tags |
| Did a task fail? | wrap `execute` once: catch what `execute` tasks throw, read `exceptionNow()` for `submit` tasks, report with the request id | the grill going out is loud; a negative price is silent |
| Which request? | capture a `ThreadLocal` such as the request id at submission, install it on the worker, restore the old value in `finally` | the note pinned to the wrong jacket |
| Keeping up? | queue size, active against max, rejections, time in queue | the board by the pass |
| Frozen, CPU idle? | a task waits for a task in its own bounded pool: compose, inline, or use a second pool | cooks waiting for tickets behind them |
| How to stop? | stop intake, then the pool that feeds the others, then the rest, all within one deadline | close the kitchen in order |

The limit of the whole track: every pool here holds one platform thread, one thread of the operating system, for each task that waits. The virtual threads track starts from that wall."""

RECAP = [
 "A pool is a few threads made once and a queue in front of them, like cooks and their rail. `execute` lets a failure reach the thread's handler, and `submit` keeps it inside the `Future`.",
 "`shutdown()` locks the door and returns at once, so wait with `awaitTermination` or `close()`. `shutdownNow()` hands back the tasks that never started and interrupts the rest.",
 "`ThreadPoolExecutor` starts core threads, then queues, then grows toward the maximum only when the queue is full, then rejects. With an unbounded queue the maximum never does anything, so give the queue a limit and choose who pays.",
 "Size from measurements: about one thread per core for computation, cores x CPU use x (1 + wait / compute) for waiting, and Little's law for traffic. The smallest limit on the path is the real ceiling, and a bulkhead keeps one slow service from taking every thread.",
 "A time limit on `get` ends your wait, not the work. `cancel(true)` and `shutdownNow()` only interrupt, so tasks must listen, and code that catches `InterruptedException` rethrows it or restores the flag.",
 "Fixed rate catches up after a slow run, fixed delay moves the later runs, and runs of one task never overlap. One uncaught exception ends a schedule without a word, so catch inside the task.",
 "`CompletableFuture` is a ticket that carries its next step. Start independent calls before you combine them, pass a pool for anything that waits, and wait once, at the edge, with a time limit.",
 "A failure skips every stage until a handler, often in a `CompletionException` envelope. Timeouts and `cancel` free the caller but not the thread, so give each call its own timeout and its own fallback before `allOf`.",
 "`ForkJoinPool` is for computation: fork one half, compute the other, then join, while idle workers steal the biggest task left. Parallel streams share its common pool with the whole JVM, so never write shared state or block in them.",
 "In production, name the threads and report every failure with its request id, from one wrapper that also carries the context. Watch the queue and the rejections, never let a task wait on its own pool, and shut down in order. The limit: each waiting task still holds a costly platform thread."
]

QUIZ = [
 {"q": "On JDK 21, a method runs `try (ExecutorService pool = Executors.newFixedThreadPool(4)) { pool.submit(this::printSalesReport); }`. What happens at the closing brace?",
  "options": [
   "Nothing: the pool keeps running until the JVM exits",
   "`close()` calls `shutdown()` and waits for the report to finish",
   "`close()` calls `shutdownNow()` and interrupts the report",
   "It doesn't compile, because an `ExecutorService` can't be closed"
  ],
  "answer": 1,
  "why": "Since JDK 19, `ExecutorService` is `AutoCloseable`, so try-with-resources (Kotlin's `use`) calls `close()`. It locks the door with `shutdown()`, then waits with no time limit for every task to finish. It calls `shutdownNow()` only if the waiting thread itself is interrupted.",
  "from": "exec-01"},
 {"q": "`new ThreadPoolExecutor(4, 32, 60, SECONDS, new LinkedBlockingQueue<>())` gets a burst of 1,000 slow tasks at once. How many threads does it run?",
  "options": [
   "32, the maximum",
   "4, and 996 tasks wait in the queue",
   "1,000, one per task",
   "4, and 996 tasks are rejected"
  ],
  "answer": 1,
  "why": "The thrifty manager calls extra threads only when the queue refuses a task, and a `LinkedBlockingQueue` with no capacity never refuses. So the pool stays at its 4 core threads, the maximum of 32 never comes into play, and nothing is rejected until memory runs out.",
  "from": "exec-02"},
 {"q": "A program on 8 cores handles requests that each compute for 20 ms and then wait 180 ms for the database. You want the cores about 80% busy, and the database's connection pool has 40 connections. How many threads should the request pool have?",
  "options": [
   "8, one per core",
   "64, from 8 x 0.8 x (1 + 180/20)",
   "About 40: the formula says 64, but only 40 requests can use the database at once",
   "200, to be safe in a rush"
  ],
  "answer": 2,
  "why": "The formula gives 64 threads to keep the cores 80% busy. But every request needs a connection, and only 40 exist, so threads 41 to 64 would just stand in line for one. As in the kitchen with two ovens, the smallest limit on the path is the real ceiling.",
  "from": "exec-03"},
 {"q": "A task adds up 10 million sales in a loop. It never waits and never checks the interrupt flag. You call `future.cancel(true)` while it runs. What happens?",
  "options": [
   "The thread is stopped at once",
   "`cancel` returns `false`, because the task is already running",
   "`cancel` returns `true` and the future says cancelled, but the loop runs to the end",
   "The task gets an `InterruptedException` on the next pass of the loop"
  ],
  "answer": 2,
  "why": "`cancel(true)` only sets the interrupt flag, the note on the cook's station. A task that never waits in a method that listens and never checks `isInterrupted()` doesn't notice, and chops on. The future is marked cancelled at once either way, so the result is thrown away even though the work finishes.",
  "from": "exec-04"},
 {"q": "A shop refreshes its exchange rate with `scheduleWithFixedDelay(this::refreshRate, 0, 30, SECONDS)`. At 18:12 the rate service doesn't answer, and `refreshRate` throws. What does the shop show at 21:00?",
  "options": [
   "Dollar prices from the last rate fetched before 18:12, and no log line about the failure",
   "A fresh rate, because the scheduler tried again 30 seconds later",
   "A stack trace in the log every 30 seconds since 18:12",
   "No prices at all, because every task on that scheduler stopped, as with `java.util.Timer`"
  ],
  "answer": 0,
  "why": "An exception that escapes a repeating task skips every later run. It waits inside the `ScheduledFuture`, which nobody reads, and the scheduler's other tasks carry on, which is why nobody notices. Catch `RuntimeException` inside the task, and let a health page report whether the future is done.",
  "from": "exec-05"},
 {"q": "`price()` and `rate()` each wait 200 ms for another service. Which version takes about 200 ms in total?",
  "options": [
   "`supplyAsync(() -> price(), io).thenCombine(supplyAsync(() -> rate(), io), BigDecimal::multiply)`",
   "`supplyAsync(() -> price(), io).thenCompose(p -> supplyAsync(() -> rate(), io).thenApply(p::multiply))`",
   "`supplyAsync(() -> price().multiply(rate()), io)`",
   "`supplyAsync(() -> price(), io).thenApplyAsync(p -> p.multiply(rate()), io)`"
  ],
  "answer": 0,
  "why": "Work starts when you call `supplyAsync`. Only the first version starts both calls before it waits for either, like the steak and the sauce cooking at once. The others are asynchronous too, but each asks for the rate only after the price has arrived, so they take about 400 ms.",
  "from": "exec-06"},
 {"q": "A call asks a flour supplier for today's price, with `orTimeout(300, MILLISECONDS)` on its future. The supplier hangs for 30 seconds. What happens to the thread on the `io` pool that makes the call?",
  "options": [
   "It is interrupted at 300 ms and goes back to the pool",
   "It stays busy for the full 30 seconds; only the future completed at 300 ms",
   "The pool replaces it with a new thread",
   "It is cancelled before the call starts"
  ],
  "answer": 1,
  "why": "`orTimeout` is the manager's kitchen timer. It completes the future with a `TimeoutException` and never touches the cook on the phone. Under load, those abandoned calls fill the pool, so give the call its own timeout in the client, no longer than the future's deadline.",
  "from": "exec-07"},
 {"q": "A shop's program checks stock with `products.parallelStream().map(p -> stock.level(p)).toList()`, and each call to the stock service waits 50 ms. Soon, `supplyAsync` tasks with no executor, in an unrelated part of the program, start to wait for seconds. Why?",
  "options": [
   "Parallel streams run on virtual threads, which get stuck on the call",
   "`toList()` locks the list until the other tasks finish",
   "The common pool rejects new tasks while a stream is running",
   "The stock calls hold the common pool's workers, and `supplyAsync` with no executor needs the same pool"
  ],
  "answer": 3,
  "why": "Parallel streams and `CompletableFuture` steps with no executor share `ForkJoinPool.commonPool()`, which has one worker fewer than the cores. The waiting calls hold those workers like cooks on the phone, so everyone else's tasks queue behind them. Move the stock calls to a pool built for waiting.",
  "from": "exec-08"},
 {"q": "A request thread puts the request id `req-42` in a `ThreadLocal` and submits a task to a pool. A wrapper copies the id onto the worker before the task runs, and puts the worker's old value back in `finally`. Which problem does that `finally` prevent?",
  "options": [
   "The submitting thread losing its own request id",
   "The task's exceptions being swallowed",
   "A deadlock between the request thread and the worker",
   "A later task on the same worker logging with `req-42`"
  ],
  "answer": 3,
  "why": "Pool threads are reused. Without the restore, the worker keeps `req-42`, like a note left pinned to a cook's jacket, and the next task on that thread logs under the wrong id. The worker never touches the submitting thread's own value, so that one can't go wrong.",
  "from": "exec-09"},
 {"q": "Pick the tool for each job on JDK 25. (1) Total the year's sales, 20 million amounts already in memory. (2) Make 2,000 calls at once to a slow web service that accepts at most 50 at a time. (3) Send the bank a heartbeat every 30 seconds.",
  "options": [
   "(1) virtual threads; (2) a parallel stream; (3) a loop with `Thread.sleep(30_000)` on the common pool",
   "All three on one `newFixedThreadPool(200)`",
   "(1) a parallel stream or a `ForkJoinPool`; (2) a pool built for waiting, or virtual threads, behind a `Semaphore` of 50; (3) a `ScheduledExecutorService` at a fixed rate",
   "(1) a single-thread executor; (2) `supplyAsync` with no executor; (3) `java.util.Timer`"
  ],
  "answer": 2,
  "why": "Arithmetic on data in memory splits well across the cores. Thousands of waiting calls want threads that are cheap to keep waiting, capped at what the service accepts, which is a bulkhead. A heartbeat follows the clock, which is what fixed rate is for. Sleeping in the common pool, `supplyAsync` with no executor for waiting calls, and `Timer` are each a bug from this track."}
]

T = {"id": "exec", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/exec.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
