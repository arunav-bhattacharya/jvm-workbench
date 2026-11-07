import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

CHEATSHEET = """## Lifecycle

| Call | What it does |
|---|---|
| `execute(r)` | runs `r`; an exception kills the worker and reaches its `UncaughtExceptionHandler` |
| `submit(c)` | returns a `Future`; an exception is stored in it and nothing is printed |
| `shutdown()` | rejects new tasks, lets queued and running ones finish, returns at once |
| `shutdownNow()` | also interrupts running tasks and returns the ones that never started |
| `awaitTermination(t, unit)` | waits until terminated or the timeout passes; returns a boolean |
| `close()` (JDK 19+) | `shutdown()`, then waits with no timeout; works with try-with-resources |

## ThreadPoolExecutor: where a task goes

1. Fewer than `corePoolSize` threads: start a new thread.
2. Otherwise: offer it to the queue.
3. Queue full: start a thread if below `maximumPoolSize`.
4. Otherwise: reject.

| Queue | Effect |
|---|---|
| `LinkedBlockingQueue()` (fixed pool) | unbounded: max is dead code, overload hides as memory and latency |
| `SynchronousQueue` (cached pool) | no queue: every burst becomes threads, up to max |
| `ArrayBlockingQueue(n)` | bounded: a full queue grows the pool, then rejects. Pushes back. |

Rejection: `AbortPolicy` throws (default), `CallerRunsPolicy` makes the submitter run it (back-pressure), `DiscardPolicy` and `DiscardOldestPolicy` lose work silently. `keepAliveTime` retires threads above core; `allowCoreThreadTimeOut(true)` retires core threads too.

## Sizing

| Work | Threads |
|---|---|
| CPU-bound | about `availableProcessors()` |
| Waits on I/O | cores x target utilization x (1 + wait / compute) |
| Any | Little's law: in flight = arrival rate x time in system |

The smallest limit downstream (a 20-connection DB pool, an issuer's rate limit) is the real ceiling. Give each dependency its own pool or semaphore: a bulkhead.

## Futures, cancellation and interruption

- `get()` throws `ExecutionException` (cause inside), `CancellationException` or `InterruptedException`; `get(t, unit)` adds `TimeoutException` and ends only your wait.
- `cancel(true)` on a `FutureTask` interrupts the worker. The task stops only if it blocks interruptibly or checks the flag.
- Catching `InterruptedException` clears the flag: rethrow it, or call `Thread.currentThread().interrupt()`.
- JDK 19: `state()`, `resultNow()`, `exceptionNow()`. `invokeAll` waits for all; `invokeAny` returns the first success and cancels the rest.

## Scheduling

| Method | Next run starts |
|---|---|
| `schedule(task, d, unit)` | once, after `d` |
| `scheduleAtFixedRate` | at `initialDelay + n x period`; late runs catch up back to back |
| `scheduleWithFixedDelay` | `delay` after the previous run ends |

Runs of one task never overlap. One uncaught exception suppresses every later run, silently: catch `RuntimeException` inside the task. JDK 25: `ForkJoinPool` implements `ScheduledExecutorService` and adds `submitWithTimeout`.

## CompletableFuture

| You have | Method |
|---|---|
| `T -> U` | `thenApply` |
| `T -> CompletableFuture<U>` | `thenCompose` |
| two futures, `(T, U) -> V` | `thenCombine` |
| failure -> value / future | `exceptionally` / `exceptionallyCompose` (JDK 12) |
| both outcomes -> new result | `handle` |
| both outcomes, observe only | `whenComplete` |
| a deadline | `orTimeout` (fails) / `completeOnTimeout` (default value), JDK 9 |
| many futures | `allOf` (waits for all, fails if any failed) / `anyOf` (first to complete, even a failure) |

- No executor means `ForkJoinPool.commonPool()`. Up to JDK 24, a common pool with parallelism below 2 meant a new thread per task; JDK 25 always uses the common pool. Pass an executor for anything that blocks.
- A plain stage runs on the thread that completes the previous stage, or on the caller if it's already done. `xxxAsync(fn, executor)` moves it.
- Start independent calls before combining them, or they run one after the other.
- Exceptions thrown in a stage arrive wrapped in `CompletionException`; `completeExceptionally` and `orTimeout` store them raw. Unwrap before testing the type.
- `orTimeout` and `cancel(true)` don't stop the task. Give the client its own timeout.
- Block once, at the edge, with a timeout. Never `join()` an unfinished future inside a stage.

## ForkJoinPool and parallel streams

- `compute()`: below the threshold, loop; else split, `left.fork()`, `right.compute()`, then `left.join()`.
- Each worker owns a deque (push and pop at the top); idle workers steal the oldest task from the bottom.
- Common pool: `availableProcessors() - 1` workers plus the caller, shared by parallel streams and default async tasks.
- In parallel streams: no shared mutable state, `toList()` keeps order, small or cheap inputs are faster sequential.
- Never block in the common pool. Put I/O on an executor built for waiting; `ManagedBlocker` is a patch.

## Production checklist

- Name threads: `Thread.ofPlatform().name("ledger-", 0).factory()` (JDK 21+).
- Report failures from both `execute` and `submit` in one wrapper, with the request id; don't rethrow.
- Carry `ThreadLocal` context (MDC, tracing): capture at submission, install in the worker, restore in `finally`.
- Watch queue size, active count against max, rejections (count them in the handler) and time in queue.
- No task may block on another task in the same bounded pool: compose, inline, or use a separate pool per stage.
- Shut down in order: stop intake, then pools upstream first, all within one deadline inside the grace period; log what `shutdownNow()` returns.
"""

T = {
 "id": "exec",
 "intro": "By the end of this track you can choose and configure a thread pool on purpose: predict where `ThreadPoolExecutor` puts each task, size a pool from measured wait and compute times with Little's law, and cap it at what the database or the issuer can take. You can cancel work that respects interruption, schedule periodic jobs that survive a failure, compose asynchronous calls with `CompletableFuture` (parallel lookups, per-call timeouts, fallbacks, fan-out), split CPU work with `ForkJoinPool` and parallel streams without starving the JVM, and run all of it in production with named threads, visible failures, carried request context, the right metrics and a clean shutdown.\n\nYou need the first track (threads, race conditions, `synchronized`, interruption), and the memory model track helps. Install JDK 25. The labs compile with release 21, so they run on JDK 21 or later; where JDK 25 changed something, such as the default executor of `CompletableFuture` or `ForkJoinPool` gaining scheduling, the lesson says so and keeps that code out of the labs.\n\nThe labs live in `labs/executors`, one package per lesson (`workbench.executors.l01` to `l09`). They are in Java, and every code sample and Try-it demo also comes in Kotlin. Concurrency tests never rely on tight timing: they use latches, barriers, max-concurrency counters, virtual time and generous timeouts, so a broken solution fails (or times out after a few seconds) instead of hanging the build. Run `./gradlew :executors:test --tests 'workbench.executors.lNN.*'` from `labs/` until it passes, `./gradlew :executors:solutionTest` to see the reference answers pass the same tests, and `./gradlew :executors:demo -Pmain=<class>` for the demos.",
 "cheatsheet": CHEATSHEET,
 "recap": [
  "A pool is a queue and a few reused threads. `shutdown()` only starts the stop; `awaitTermination` or `close()` waits. `submit` hides exceptions in the `Future`.",
  "`ThreadPoolExecutor` starts core threads, then queues, then grows to max only when the queue is full, then rejects. An unbounded queue makes max useless.",
  "Size CPU pools to the cores and I/O pools by cores x utilization x (1 + W/C), check with Little's law, and cap by the smallest downstream limit.",
  "`cancel(true)` and `shutdownNow()` only interrupt. Tasks must cooperate, and code that catches `InterruptedException` must rethrow it or restore the flag.",
  "Periodic tasks never overlap, fixed rate catches up while fixed delay doesn't, and one uncaught exception silently ends the schedule.",
  "`CompletableFuture`: start independent calls first, combine with `thenCombine`, flatten with `thenCompose`, and pass an executor for anything that blocks.",
  "Failures skip stages until a handler and often arrive wrapped in `CompletionException`. Timeouts and cancel end the wait, not the work. Give each fan-out call its own deadline and fallback.",
  "ForkJoin is for CPU work: fork one half, compute the other, then join. Parallel streams share the common pool with the whole JVM, so never block in them.",
  "In production: named threads, one wrapper that reports every failure with its request id and carries context, metrics on queue and rejections, no task waiting on its own pool, and an ordered shutdown."
 ],
 "quiz": [
  {
   "q": "On JDK 21, `try (ExecutorService pool = Executors.newFixedThreadPool(4)) { pool.submit(this::exportLedger); }`. What happens at the closing brace?",
   "options": [
    "Nothing: the pool keeps running until the JVM exits",
    "`close()` calls `shutdown()` and waits for the export to finish",
    "`close()` calls `shutdownNow()` and interrupts the export",
    "It doesn't compile, because ExecutorService isn't AutoCloseable"
   ],
   "answer": 1,
   "why": "Since JDK 19, `ExecutorService` is `AutoCloseable`. `close()` shuts the pool down and waits, with no timeout, for submitted tasks to finish. It only falls back to `shutdownNow()` if the waiting thread is interrupted.",
   "from": "exec-01"
  },
  {
   "q": "`new ThreadPoolExecutor(4, 32, 60, SECONDS, new LinkedBlockingQueue<>())` gets a burst of 1,000 slow tasks. How many threads does it run?",
   "options": [
    "32, the maximum",
    "4, and 996 tasks wait in the queue",
    "1,000, one per task",
    "4, and 996 tasks are rejected"
   ],
   "answer": 1,
   "why": "The pool grows past core only when the queue refuses a task, and an unbounded `LinkedBlockingQueue` never refuses. The maximum of 32 is never reached, and nothing is rejected until memory runs out.",
   "from": "exec-02"
  },
  {
   "q": "An 8-core service spends 20 ms of CPU and 180 ms waiting on the database per request, and you want about 80% CPU. The database pool has 40 connections. How many threads should the request pool have?",
   "options": [
    "8, one per core",
    "64, from 8 x 0.8 x (1 + 180/20)",
    "About 40: the formula says 64, but only 40 can talk to the database at once",
    "200, to be safe under bursts"
   ],
   "answer": 2,
   "why": "The formula gives 64 threads to keep the CPU at 80%, but every request needs a connection, and only 40 exist. Threads 41 to 64 would just wait for a connection. The smallest limit on the path is the real ceiling.",
   "from": "exec-03"
  },
  {
   "q": "A task loops over 10 million ledger rows and never blocks or checks the interrupt flag. You call `future.cancel(true)`. What happens?",
   "options": [
    "The thread is stopped at once",
    "`cancel` returns false because the task is running",
    "`cancel` returns true and the future reports cancelled, but the loop runs to the end",
    "The task gets an `InterruptedException` at the next loop iteration"
   ],
   "answer": 2,
   "why": "`cancel(true)` only sets the interrupt flag. A task that never blocks interruptibly and never checks `isInterrupted()` doesn't notice. The `Future` is marked cancelled either way, so its result is lost even though the work finishes.",
   "from": "exec-04"
  },
  {
   "q": "An FX refresher runs with `scheduleWithFixedDelay(this::refresh, 0, 30, SECONDS)`. At 03:12 the provider returns a 502 and `refresh` throws. What do you see at 09:00?",
   "options": [
    "The rate from 03:11, and no log line about the failure",
    "A fresh rate: the scheduler retried 30 seconds later",
    "A stack trace in the logs every 30 seconds since 03:12",
    "The scheduler shut down and the service failed its health check"
   ],
   "answer": 0,
   "why": "An exception that escapes a periodic task suppresses every later run, and it is stored in the `ScheduledFuture` that nobody reads. Catch `RuntimeException` inside the task and expose the age of the last success on a health endpoint.",
   "from": "exec-05"
  },
  {
   "q": "`price()` and `rate()` each block for 200 ms. Which version takes about 200 ms in total?",
   "options": [
    "`supplyAsync(() -> price(), io).thenCombine(supplyAsync(() -> rate(), io), BigDecimal::multiply)`",
    "`supplyAsync(() -> price(), io).thenCompose(p -> supplyAsync(() -> rate(), io).thenApply(p::multiply))`",
    "`supplyAsync(() -> price().multiply(rate()), io)`",
    "`supplyAsync(() -> price(), io).thenApplyAsync(p -> p.multiply(rate()), io)`"
   ],
   "answer": 0,
   "why": "Only the first starts both calls before waiting for either. The others are asynchronous too, but each calls `rate()` after `price()` has returned, so they take about 400 ms.",
   "from": "exec-06"
  },
  {
   "q": "A quote call has `orTimeout(300, MILLISECONDS)`, and the provider hangs for 30 seconds. What happens to the call's thread on the `io` pool?",
   "options": [
    "It is interrupted at 300 ms and returns to the pool",
    "It stays busy for the full 30 seconds; only the future completed at 300 ms",
    "The pool replaces it with a new thread",
    "It is cancelled before the call starts"
   ],
   "answer": 1,
   "why": "`orTimeout` completes the future with `TimeoutException` and never touches the task. Under load, abandoned calls fill the pool. Set a client-side timeout no longer than the future's deadline.",
   "from": "exec-07"
  },
  {
   "q": "A Quarkus service enriches payments with `payments.parallelStream().map(p -> enrich(p, binService.lookup(p.bin()))).toList()`, and each lookup takes 50 ms. Unrelated `CompletableFuture` timeouts start appearing elsewhere in the service. Why?",
   "options": [
    "Parallel streams use virtual threads, which pin on the lookup",
    "The stream's `toList()` locks the list while the futures run",
    "The common pool rejects tasks when the stream is busy",
    "The lookups block the common pool's workers, and executor-less `CompletableFuture` tasks need the same pool"
   ],
   "answer": 3,
   "why": "Parallel streams and default async `CompletableFuture` tasks share `ForkJoinPool.commonPool()`, which has cores minus one workers. Blocking lookups hold those workers, so everything else queues behind them. Move the lookups to an IO executor.",
   "from": "exec-08"
  },
  {
   "q": "A request thread sets the MDC `requestId` and submits a ledger write to a pool whose tasks, through a wrapper, run with the submitter's MDC. The wrapper restores the worker's MDC in `finally`. Which problem does that `finally` prevent?",
   "options": [
    "The submitting thread losing its own MDC",
    "A later task on the same worker logging with this request's id",
    "The task's exceptions being swallowed",
    "Deadlock between the request thread and the worker"
   ],
   "answer": 1,
   "why": "Pool threads are reused. Without the restore, the worker keeps `req-42` in its MDC, and the next task on that thread, possibly from another request or none at all, logs under the wrong id. The submitting thread's MDC is never touched by the worker.",
   "from": "exec-09"
  },
  {
   "q": "Pick the tool for each job on JDK 25: (1) total fees over 20 million rows in memory, (2) 2,000 concurrent calls to a card-issuer API, (3) a heartbeat to the issuer every 30 seconds.",
   "options": [
    "(1) a parallel stream or ForkJoinPool; (2) virtual threads or a bounded IO pool, capped by a semaphore at the issuer's limit; (3) a ScheduledExecutorService with fixed rate",
    "(1) virtual threads; (2) a parallel stream; (3) a loop with `Thread.sleep(30_000)` on the common pool",
    "All three on one `newFixedThreadPool(200)`",
    "(1) a single-thread executor; (2) `supplyAsync` without an executor; (3) `java.util.Timer`"
   ],
   "answer": 0,
   "why": "CPU work over in-memory data splits well across the cores. Thousands of blocking calls want cheap threads, limited by what the issuer accepts, not by a pool size. A heartbeat is a timetable, which is what fixed rate is for, on its own scheduler. Sleeping in the common pool, executor-less `supplyAsync` for I/O and `Timer` are each a bug from this track."
  }
 ]
}
out = ROOT / "content/tracks/exec.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
