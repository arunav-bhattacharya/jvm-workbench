# Java Executors, Thread Pools, Virtual Threads, Structured Concurrency and Scoped Values (state as of 30 October 2026)

**Read this first: how these notes were verified.**
- This session's network policy blocked page fetches from **openjdk.org** and **docs.oracle.com** (DNS failure: "host outside the session's allowed network domains"). Per the tool guidance, no other sites were fetched after that. **No web page was fetched in full.** The "Verified URLs" section at the end is therefore empty, and it says so.
- What *was* possible: about 20 web searches. The search tool returns summaries of specific result pages, often with short quotes. Facts taken from those summaries are cited inline with the result URL and tagged **[S]** (search-summary verified; the page itself was not opened).
- Long-standing API facts (ThreadPoolExecutor rules, CompletableFuture methods, etc.) that searches did not cover come from the researcher's training knowledge (cutoff mid-2026). They sit under "Background facts (training knowledge)" sub-headings, are tagged **[TK]**, and need a check against the Javadoc before they are published. They are stable, well-known facts, but this session did not re-check them.
- JDK timeline used throughout: JDK 21 LTS (Sep 2023), JDK 24 (Mar 2025), JDK 25 LTS (Sep 2025), JDK 26 (Mar 2026), **JDK 27 GA 15 Sep 2026 (non-LTS)**, JDK 28 due March 2027.
- Fix for the writer: allow openjdk.org and docs.oracle.com in the session's network settings (environment settings, then Network access, then Allowed domains), then re-verify the [TK] items and the [S] items marked "conflict".

---

## Q0. Classic executor framework: what lesson writers need (lifecycle, ThreadPoolExecutor, sizing, Future, scheduling, CompletableFuture, ForkJoinPool, production)

### Takeaway
The executor framework (JDK 5+) has not changed in shape. The things that changed recently and are easy to get wrong are: `ExecutorService` is `AutoCloseable` (JDK 19); `Future.state()/resultNow()/exceptionNow()` (JDK 19); in **JDK 25** `ForkJoinPool` implements `ScheduledExecutorService` and gains `submitWithTimeout`; also in **JDK 25**, `CompletableFuture` async methods without an executor *always* use the common pool (the thread-per-task fallback on 1–2-CPU machines is gone); in **JDK 27**, `ThreadPoolExecutor.finalize()` is removed.

### Cited Findings
- **[JDK 19+] `ExecutorService.close()`** exists because ExecutorService now implements `AutoCloseable`, "enables ExecutorServices to be used in try-with-resources", and is default-implemented "using nearly the same code as was already illustrated in existing javadoc examples"; the code carries `@since 19`. [S] — [JDK-8285450](https://bugs.openjdk.org/browse/JDK-8285450)
- **[JDK 19+] `Future.State`, `state()`, `resultNow()`, `exceptionNow()`** were added "to simplify some uses of Futures expected to be common in loom". `resultNow()` throws `IllegalStateException` if the task has not completed or did not complete with a result. `state()` has a default implementation built on `isDone()`, `isCancelled()` and `get()`. [S] — [JDK-8285450](https://bugs.openjdk.org/browse/JDK-8285450)
- Design intent of `resultNow`: "obtain the result in the common case, in which you already know that it's there", while `Future.state` "never fails". [S] — [loom-dev, Nov 2021](https://mail.openjdk.org/pipermail/loom-dev/2021-November/003218.html)
- **[JDK 5+] Periodic task exception pitfall:** "If any execution of the task encounters an exception, subsequent executions are suppressed. Otherwise, the task will only terminate via cancellation or termination of the executor." [S] — [ScheduledExecutorService Javadoc mirror (Java 6)](https://www.iitk.ac.in/esc101/share/documentation/docs/api/java/util/concurrent/ScheduledExecutorService.html). Calling `get()` on the returned future then throws `ExecutionException` holding the exception as its cause, and `isDone()` returns true. [S] — [Android ScheduledExecutorService reference](https://developer.android.com/reference/java/util/concurrent/ScheduledExecutorService?authuser=1). The same rule appears in the JDK 26-era API build at [cr.openjdk.org ScheduledExecutorService](https://cr.openjdk.org/~alanb/sc-jdk26/api/java.base/java/util/concurrent/ScheduledExecutorService.html) [S, surfaced in search; content not quoted].
- **[JDK 25+] `ForkJoinPool implements ScheduledExecutorService`.** The JDK 25 class docs show `ForkJoinPool extends AbstractExecutorService implements ScheduledExecutorService`. It adds `submitWithTimeout(Callable, long, TimeUnit, Consumer)`, which returns a `ForkJoinTask<V>` and cancels the task (or runs another action) if the timeout expires first. [S] — [JDK-8362881](https://bugs.openjdk.org/browse/JDK-8362881), [JDK-8350493](https://bugs.openjdk.org/browse/JDK-8350493), [ForkJoinPool JDK 25 docs mirror](https://docs.w3cub.com/openjdk~25/java.base/java/util/concurrent/forkjoinpool.html)
- The delayed-task scheduler is attached lazily to any ForkJoinPool, including the common pool. `submitWithTimeout` is not on the `ScheduledExecutorService` interface because it relies on `ForkJoinTask` methods. Origin: JDK-8319447 "Improve performance of delayed task handling". [S] — [core-libs-dev review thread, Mar 2025](https://mail.openjdk.org/pipermail/core-libs-dev/2025-March/141639.html)
- **[JDK 25+] CompletableFuture default executor change.** JDK-8319447 "updated CompletableFuture and SubmissionPublisher to use the ForkJoinPool commonPool in all cases". [S] — [JDK-8362882 thread](https://mail.openjdk.org/pipermail/core-libs-dev/2025-July/149334.html). Alan Bateman: "this changed in JDK 25 so that the async methods without an explicit Executor will submit to the common pool". [S] — [net-dev, Oct 2025](https://mail.openjdk.org/pipermail/net-dev/2025-October/028226.html). **Before JDK 25:** `useCommonPool = (ForkJoinPool.getCommonPoolParallelism() > 1)`, otherwise a thread-per-task executor. In practice that meant machines with 1–2 cores (common-pool parallelism = CPUs − 1). [S] — same sources
- A regression caused by JDK-8319447 was filed and resolved; details not found. [S] — [JDK-8360593](https://bugs.openjdk.org/browse/JDK-8360593)
- **[JDK 27] `ThreadPoolExecutor.finalize()` removed** (listed among JDK 27 removals). [S] — [JDK 27 release notes](https://www.oracle.com/java/technologies/javase/27-relnote-issues.html)
- **Goetz pool-sizing formula** (*Java Concurrency in Practice* §8.2): `N_threads = N_cpu × U_cpu × (1 + W/C)`. N_cpu = `Runtime.getRuntime().availableProcessors()`, U_cpu = target utilization (0–1), W/C = wait-to-compute ratio. For CPU-bound work (W = 0), N ≈ N_cpu. Sources stress load-testing over trusting the formula. [S] — [Zalando Engineering, "How to set an ideal thread pool size"](https://engineering.zalando.com/posts/2019/04/how-to-set-an-ideal-thread-pool-size.html) (secondary source; the book itself is not online)

### Background facts (training knowledge) [TK], applies JDK 5+ unless tagged
**ExecutorService lifecycle**
- States: running, then shutdown, then terminated. `shutdown()` stops new submissions (they are rejected) and lets queued and running tasks finish. It **does not wait**. `shutdownNow()` interrupts running tasks (TPE interrupts workers), drains the queue and **returns `List<Runnable>` of never-started tasks**. `awaitTermination(t, unit)` blocks until terminated or timed out and returns a boolean. `isShutdown()` / `isTerminated()`.
- [JDK 19+] `close()` default semantics: if not terminated, it calls `shutdown()`, then loops on `awaitTermination(1, DAYS)` until terminated. If interrupted while waiting, it calls `shutdownNow()` once, keeps waiting, then re-asserts the interrupt status. **Consequence:** `close()` can block forever on a task that ignores interrupts. `close()` on `ForkJoinPool.commonPool()` has no effect.
- Canonical graceful-shutdown idiom (from the ExecutorService Javadoc):
```java
void shutdownAndAwaitTermination(ExecutorService pool) {
    pool.shutdown();                                   // no new tasks
    try {
        if (!pool.awaitTermination(60, TimeUnit.SECONDS)) {
            pool.shutdownNow();                        // interrupt stragglers
            if (!pool.awaitTermination(60, TimeUnit.SECONDS))
                System.err.println("Pool did not terminate");
        }
    } catch (InterruptedException ie) {
        pool.shutdownNow();
        Thread.currentThread().interrupt();            // preserve interrupt status
    }
}
```
- [JDK 19+] try-with-resources form:
```java
try (ExecutorService pool = Executors.newFixedThreadPool(4)) {
    Future<Integer> f = pool.submit(() -> 6 * 7);
    System.out.println(f.get());
}   // close() = shutdown + wait for all tasks
```

**ThreadPoolExecutor internals**
- Constructor: `(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue[, threadFactory][, handler])`.
- The submission algorithm from the Javadoc, which is the core lesson:
  1. Fewer than `corePoolSize` threads running: **start a new thread**, even if others are idle.
  2. Otherwise: **try to queue** the task.
  3. Queue refuses (full): start a new thread **if below `maximumPoolSize`**.
  4. Otherwise: **reject** (call the `RejectedExecutionHandler`).
  So **the pool grows past core only when the queue is full**. With an unbounded `LinkedBlockingQueue`, `maximumPoolSize` never matters. (Design rationale: prefer queuing to keep thread count bounded; extra threads are a burst valve, not the main capacity.)
- Queue choice: `SynchronousQueue` (direct handoff, no capacity; used by `newCachedThreadPool`); `LinkedBlockingQueue` unbounded (used by `newFixedThreadPool` and `newSingleThreadExecutor`; risk of unbounded memory growth and latency); `ArrayBlockingQueue(n)` bounded (gives back-pressure via rejection); `PriorityBlockingQueue`.
- Factory configurations: `newFixedThreadPool(n)` = `TPE(n, n, 0, ms, new LinkedBlockingQueue<>())`. `newCachedThreadPool()` = `TPE(0, Integer.MAX_VALUE, 60, s, new SynchronousQueue<>())` (unbounded threads under load). Default thread names are `pool-N-thread-M`.
- `keepAliveTime` applies to threads above core. `allowCoreThreadTimeOut(true)` applies it to core threads too. `prestartAllCoreThreads()` / `prestartCoreThread()` start core threads early.
- Rejection policies (`ThreadPoolExecutor.*Policy`): **`AbortPolicy` (default; throws `RejectedExecutionException`)**, `CallerRunsPolicy` (the submitting thread runs the task, a simple form of back-pressure), `DiscardPolicy` (silently drops), `DiscardOldestPolicy` (drops the oldest queued task and retries). Tasks submitted after `shutdown()` are also rejected.
- Hooks: `beforeExecute(Thread, Runnable)`, `afterExecute(Runnable, Throwable)`, `terminated()`. These are useful for metrics and MDC.
- Monitoring getters: `getPoolSize()`, `getActiveCount()`, `getLargestPoolSize()`, `getQueue().size()`, `getCompletedTaskCount()`, `getTaskCount()` (the counts are approximate).

**Little's law (pool sizing and why Loom exists)**
- L = λ × W: the average number of requests in the system equals throughput times average latency. JEP 444 uses it to argue that thread-per-request throughput is capped by the number of threads. Example: 2,000 req/s × 0.5 s = 1,000 concurrent requests, so 1,000 threads. [TK; JEP 444 has a section on this, not quoted here]

**Future / Callable / cancellation / interruption**
- `Callable<V>.call() throws Exception` vs `Runnable.run()`. `submit()` wraps the task in a `FutureTask`. `get()` throws `ExecutionException` (cause = the task's exception), `InterruptedException`, or `CancellationException`. `get(timeout)` can also throw `TimeoutException`.
- `cancel(true)` on a `FutureTask` **interrupts** the running thread. Cancellation is cooperative: the task must check `Thread.interrupted()` or call an interruptible blocking method. `cancel(false)` only prevents a task that has not started.
- **`CompletableFuture.cancel(mayInterruptIfRunning)`: the flag has no effect.** CF does not use interrupts. It completes the future with `CancellationException`.
- Interruption etiquette: catching `InterruptedException` clears the flag. Either propagate it or call `Thread.currentThread().interrupt()`.
- [JDK 19+] `Future.State` values: `RUNNING, SUCCESS, FAILED, CANCELLED`. `exceptionNow()` throws `IllegalStateException` if the task did not fail (including when it was cancelled).
```java
switch (f.state()) {                       // JDK 21+ pattern switch on enum is fine
    case SUCCESS   -> use(f.resultNow());
    case FAILED    -> log(f.exceptionNow());
    case CANCELLED -> log("cancelled");
    case RUNNING   -> log("still running");
}
```

**ScheduledExecutorService**
- `scheduleAtFixedRate(task, initialDelay, period, unit)`: start times follow `initialDelay + n*period`. If one run takes longer than the period, later runs **start late but never overlap**.
- `scheduleWithFixedDelay(task, initialDelay, delay, unit)`: the delay is measured from the **end** of one run to the start of the next, so there is no catch-up burst.
- The exception rule (cited above) applies to both. Fix: wrap the body in `try { … } catch (Throwable t) { log }`, or watch the returned future.
- `ScheduledThreadPoolExecutor` is fixed-size (corePoolSize) with an unbounded delay queue, so `maximumPoolSize` has no effect. `setRemoveOnCancelPolicy(true)` stops cancelled tasks from piling up in the queue.

**CompletableFuture** (JDK 8 base; additions tagged)
- Creation: `supplyAsync`, `runAsync`, `completedFuture`, `new CompletableFuture<>()` + `complete`/`completeExceptionally`. [JDK 9] `failedFuture`, `completedStage`, `failedStage`, `completeAsync`, `copy`, `minimalCompletionStage`, `newIncompleteFuture`, `defaultExecutor`.
- Composition: `thenApply` (map), `thenCompose` (flatMap), `thenCombine` (zip two), `thenAccept`/`thenRun`, `applyToEither`/`acceptEither`, `allOf(...)` (→ `CompletableFuture<Void>`; collect results yourself via `join()`), `anyOf(...)` (→ `CompletableFuture<Object>`; the first to complete wins, **including exceptional completion**).
- Async variants: `xxxAsync(fn)` runs on the **default async executor = `ForkJoinPool.commonPool()`** (from JDK 25 in all cases; earlier, a thread per task when common-pool parallelism < 2). `xxxAsync(fn, executor)` runs on a pool you choose. A non-async `thenApply` runs on whichever thread completes the previous stage, or on the caller if it is already complete.
- Exceptions: dependents see a `CompletionException` wrapping the cause. `join()` throws unchecked `CompletionException`; `get()` throws checked `ExecutionException`. Handlers: `exceptionally` (JDK 8), `handle(BiFunction)`, `whenComplete` (observes, does not recover). [JDK 12] `exceptionallyAsync`, `exceptionallyCompose`, `exceptionallyComposeAsync` (recover with another CF).
- [JDK 9] `orTimeout(t, unit)` completes exceptionally with `TimeoutException`. `completeOnTimeout(value, t, unit)` completes with a default value. **Neither stops or interrupts the underlying work.** `CompletableFuture.delayedExecutor(delay, unit[, executor])` returns an Executor that submits after a delay.
- [JDK 19+] CF overrides `state()`, `resultNow()`, `exceptionNow()`.
```java
ExecutorService io = Executors.newVirtualThreadPerTaskExecutor();      // JDK 21+
CompletableFuture<Quote> best =
    CompletableFuture.supplyAsync(() -> priceFromA(), io)
        .thenCombine(CompletableFuture.supplyAsync(() -> priceFromB(), io), Quote::cheaper)
        .orTimeout(2, TimeUnit.SECONDS)                                   // JDK 9
        .exceptionallyCompose(ex -> CompletableFuture.supplyAsync(() -> cachedQuote(), io)); // JDK 12
```

**ForkJoinPool and work stealing** (JDK 7; common pool JDK 8)
- Each worker owns a deque. It pushes and pops its own tasks LIFO (cache-friendly). Idle workers **steal** FIFO from the other end of a busy worker's deque. `RecursiveTask`/`RecursiveAction` use `fork()`/`join()`. A joining worker helps run other tasks instead of sitting blocked.
- `ForkJoinPool.commonPool()`: parallelism defaults to `availableProcessors() − 1`. Configure it with `-Djava.util.concurrent.ForkJoinPool.common.parallelism`, `.threadFactory`, `.exceptionHandler`, `.maximumSpares`. Thread names look like `ForkJoinPool.commonPool-worker-N`.
- **Parallel streams run on the common pool** (the calling thread also takes part). One blocking I/O call in a parallel stream or in a default-executor `CompletableFuture` can starve every other user of the common pool in the JVM. `ForkJoinPool.ManagedBlocker` lets FJP add a compensating thread. Running a parallel stream inside `customPool.submit(...)` uses that pool, but this is implementation behavior, not a spec guarantee.

**Pools in production**
- Name threads: [JDK 21+] `Thread.ofPlatform().name("orders-", 0).factory()`. Before 21: a custom `ThreadFactory` or Guava `ThreadFactoryBuilder`.
- `UncaughtExceptionHandler` fires only for tasks sent with `execute()`. **With `submit()`, the exception is captured in the Future and is silent unless someone calls `get()`.** This is the classic "my task died silently" bug. Override `afterExecute` or always inspect futures.
- Context/MDC: MDC is ThreadLocal-based. Wrap tasks to capture `MDC.getCopyOfContextMap()` at submit time and restore and clear it in the worker. The same applies to security and tracing contexts. Virtual threads do not change this: a new virtual thread normally starts with an empty MDC unless you propagate it. (The exact behavior depends on whether the logging backend's MDC adapter uses inheritable thread-locals.)
- Metrics: queue depth, active count, pool size vs max, rejected count (wrap the handler), task latency (queue wait + run time via before/afterExecute). Micrometer's `ExecutorServiceMetrics` wraps executors.
- Graceful shutdown: register shutdown in the app lifecycle (Spring `ThreadPoolTaskExecutor.setWaitForTasksToCompleteOnShutdown` / `setAwaitTerminationSeconds`). Use the shutdown, awaitTermination, shutdownNow idiom above.

### Inferences
- Since JDK 25, the old "CompletableFuture on a 2-core container spawns a thread per task" surprise no longer happens, but courses targeting JDK 21 must still mention it.
- Since JDK 25, `CompletableFuture.delayedExecutor`/`orTimeout` timing probably relies on the ForkJoinPool delayed-task machinery from JDK-8319447 rather than the older dedicated delay-scheduler thread. This is inferred from the change title and the "CF uses the common pool in all cases" note, not confirmed.

### Gaps
- No ThreadPoolExecutor, ExecutorService, CompletableFuture or ForkJoinPool Javadoc page could be fetched (docs.oracle.com blocked). All [TK] items above need a check against the JDK 25 Javadoc.
- Whether JDK 26 or JDK 27 changed any executor API beyond `ThreadPoolExecutor.finalize()` removal: none found in searches.
- A public `ForkJoinPool.asyncCommonPool()` method is mentioned in a [JavaSpecialists issue title](https://javaspecialists.eu/archive/Issue332-ForkJoinPool.asyncCommonPool.html) and in the JDK-8362882 thread title. Unclear whether it is public API and in which JDK (possibly JDK 26). Not verified.

---

## Q1. What is the exact, current status and API of each Loom feature per JDK version (21, 24, 25, 26, 27)? Minimal correct code for the current API

### Takeaway
Virtual threads are final in JDK 21 (JEP 444). JDK 24 (JEP 491) removed `synchronized` pinning. JDK 25 is the first LTS with that fix. Scoped values are **final in JDK 25 (JEP 506)**. Structured concurrency is **still preview in JDK 26 (JEP 525, 6th preview) and JDK 27 (JEP 533, 7th preview)**. It has been **integrated as final in JDK 28 (JEP 543, GA March 2027) with no API changes from JDK 27**. As of October 2026 no released JDK has a final `StructuredTaskScope`.

### Cited Findings
**Structured concurrency: JEP history**
- Incubator: JEP 428 (JDK 19), JEP 437 (JDK 20). It then went through seven previews ending with JEP 533 in JDK 27. [S] — [InfoQ, JEP 543 targeted to JDK 28 (Oct 2026)](https://www.infoq.com/news/2026/10/jep-543-jdk-28/)
- Preview JEPs named in search results: [JEP 453 (Preview)](https://openjdk.org/jeps/453), [JEP 462 (Second Preview)](https://openjdk.org/jeps/462), [JEP 499 (Fourth Preview)](https://openjdk.org/jeps/499), [JEP 505 (Fifth Preview)](https://openjdk.org/jeps/505), [JEP 525 (Sixth Preview)](https://openjdk.org/jeps/525), [JEP 533 (Seventh Preview)](https://openjdk.org/jeps/533). [S, titles only]
- **JEP 525** (JDK 26) is "completed for JDK 26, re-previewing the API after JEP 505 in JDK 25 … to allow further time for feedback." [S] — [JEP 525](https://openjdk.org/jeps/525)
- JEP 525 changes [S] — [JDK-8367858](https://bugs.openjdk.org/browse/JDK-8367858), [InfoQ timeout-joiner refinements (Jan 2026)](https://www.infoq.com/news/2026/01/timeout-joiner-refinements), [JavaPro JEP 525 deep dive](https://javapro.io/2026/06/09/structured-concurrency-in-java-26-jep-525-deep-dive/), [HappyCoders Java 26 features](https://www.happycoders.eu/java/java-26-features/):
  - `join()` now calls the joiner's **`onTimeout()`** if a configured timeout expires. `onTimeout` either throws `TimeoutException` or does nothing, so a custom joiner can return partial or fallback results. **Conflict:** a second search said it "found no confirmed public `onTimeout` method", only a patch. JDK-8367858 and the InfoQ article both describe it, so treat it as likely but unconfirmed against the Javadoc.
  - `Joiner.allSuccessfulOrThrow()` now returns **`List<T>`** of results instead of a `Stream<Subtask<T>>`.
  - `anySuccessfulResultOrThrow()` was **renamed `anySuccessfulOrThrow()`**.
  - `onFork`/`onComplete` take `Subtask<T>` rather than `Subtask<? extends T>`. `Joiner` is no longer a `@FunctionalInterface`.
  - `allUntil(Predicate)` return shape changed (the ticket is inconsistent: "list of subtasks" vs "stream of all forked subtasks").
- **JEP 533** (JDK 27, 7th preview, "minor changes"):
  - `join()` on `StructuredTaskScope` and `Joiner` gained a third type parameter for the exception thrown. **Built-in joiners now throw the standard `java.util.concurrent.ExecutionException`** (same as `Future.get()`) instead of the preview-only `StructuredTaskScope.FailedException`. [S] — [InfoQ, JEP 533 (May 2026)](https://www.infoq.com/news/2026/05/jep-533-jdk-27/), [danvega/structured-concurrency](https://github.com/danvega/structured-concurrency), [HappyCoders STS Java 27](https://www.happycoders.eu/java/structured-concurrency-structuredtaskscope/)
  - New static `open(UnaryOperator<Configuration>)` overload uses the default joiner with custom config (name, timeout). [S] — [InfoQ](https://www.infoq.com/news/2026/05/jep-533-jdk-27/)
  - `Joiner.awaitAll()` removed. The old `StructuredTaskScope.TimeoutException` is gone. [S] — [danvega/structured-concurrency](https://github.com/danvega/structured-concurrency) (single secondary source)
  - JEP 533 itself "doesn't commit to a finalization timeline". [S] — [InfoQ](https://www.infoq.com/news/2026/05/jep-533-jdk-27/)
  - Code that caught `FailedException` must change to catch `ExecutionException` when moving to JDK 27. [S] — [inside.java, JEP 533 targeted](https://inside.java/2026/05/11/jep533-target-jdk27/) / InfoQ
- **JEP 543** (JDK 28): integrated, **final, "no API changes from JDK 27's seventh preview"**. Migration is "a build change, not a code change": drop `--enable-preview`. JDK 28 GA is scheduled for March 2027. Earlier it was moved to Targeted per the 12 Oct 2026 roundup. [S] — [InfoQ JEP 543](https://www.infoq.com/news/2026/10/jep-543-jdk-28/), [InfoQ Java news roundup Oct 12 2026](https://www.infoq.com/news/2026/10/java-news-roundup-oct12-2026/)
- JDK 27 joiner semantics: with no joiner (or `awaitAllSuccessfulOrThrow()`), a subtask failure cancels the scope and `join()` throws it wrapped in `ExecutionException`. `anySuccessfulOrThrow()` returns the first successful result and cancels the rest. `allSuccessfulOrThrow()` returns the `List` of results, so `scope.join().map(Subtask::get).toList()` becomes `scope.join()`. [S] — [HappyCoders STS Java 27](https://www.happycoders.eu/java/structured-concurrency-structuredtaskscope/), [Oracle JDK 27 Structured Concurrency guide (search snippet)](https://docs.oracle.com/en/java/javase/27/core/structured-concurrency.html). JDK 28 EA docs: "the standard joiners produce a result or throw ExecutionException". [S] — [JDK 28 EA Joiner Javadoc](https://download.java.net/java/early_access/jdk28/docs/api/java.base/java/util/concurrent/StructuredTaskScope.Joiner.html)
- **Conflict:** which joiner the no-arg `open()` uses. One source says `Joiner.awaitAllSuccessfulOrThrow()`, another says `allSuccessfulOrThrow()`. [S] — same HappyCoders and Oracle-guide search summary. (In JDK 25/JEP 505 it was `awaitAllSuccessfulOrThrow()` with `join()` returning `null` [TK].)
- `onFork()` is called when forking a subtask, `onComplete()` when a subtask completes (JDK 25 description). [S] — [JDK 25 Joiner Javadoc mirror](https://javadoc.scijava.org/Java25/java.base/java/util/concurrent/StructuredTaskScope.Joiner.html)
- JEP 505 (JDK 25) was the redesign: static `open()` factories plus `Joiner`, replacing subclassing. [S, title/coverage] — [InfoQ JEP 505](https://www.infoq.com/news/2025/05/jep-505-concurrency-preview-5)

**Scoped values**
- **JEP 506 Scoped Values: Closed / Delivered in JDK 25 (final).** The single change from the last preview: **`ScopedValue.orElse` no longer accepts `null`**. Earlier rounds ran from JEP 429 (JDK 20, incubator) to JEP 487 (JDK 24, fourth preview). [S] — [JEP 506](https://openjdk.org/jeps/506), [heise.de Java 25 summary](https://heise.de/-10530625)
- Scoped values let a method share immutable data with its callees and with child threads. Child tasks inherit scoped values. [S] — [inside.java JDK 25 performance improvements](https://inside.java/2025/10/20/jdk-25-performance-improvements/)

**Virtual threads and pinning by version**
- **JDK 24:** JEP 491 changes HotSpot object monitors "so that virtual threads can acquire, hold, and release monitors, independently of their carriers". [S] — [JEP 491](https://openjdk.org/jeps/491). **JDK 25** is the first LTS containing it. [S] — [Java Code Geeks, "Virtual Threads Two Years In" (May 2026)](https://www.javacodegeeks.com/2026/05/virtual-threads-two-years-in-production-war-stories-the-pinning-edge-cases-and-what-jdk-25-fixed.html)
- **JDK 26:** JDK-8369238: a virtual thread waiting for another thread to finish a class initializer **now unmounts**. Before this it pinned its carrier, including when trying to initialize a class another thread was initializing. Also in JDK 26: `Thread.stop` removed (JDK-8368226; not VT-specific). [S] — [Oracle JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26-relnote-issues.html)
- **JDK 27:** the 9 JEPs are JEP 523 (G1 default everywhere), 527 (post-quantum hybrid key exchange, TLS 1.3), 534 (compact object headers by default), 536 (JFR in-process data redaction) as final; 531 (Lazy Constants), 532 (primitive types in patterns), **533 (Structured Concurrency, 7th preview)**, 538 (PEM encodings, 3rd preview) as preview; 537 (Vector API, 12th incubator). GA 15 Sep 2026, non-LTS, superseded by JDK 28 in March 2027. [S] — [inside.java "The Arrival of Java 27"](https://inside.java/2026/09/15/jdk-27-available/), [Oracle blog](https://blogs.oracle.com/java/the-arrival-of-java-27), [HowToDoInJava Java 27 features](https://howtodoinjava.com/java/java-27-features/). **No JDK 27 release note changing the virtual-thread scheduler was found.** [S] — [JDK 27 release notes](https://www.oracle.com/java/technologies/javase/27-relnote-issues.html)
- The virtual-thread scheduler's default worker pool is a ForkJoinPool. Parallelism is set with `jdk.virtualThreadScheduler.parallelism`. JEP 491 notes a default limit of 256 scheduler platform threads. [S] — [JEP 444](https://openjdk.org/jeps/444), [JEP 491](https://openjdk.org/jeps/491) (via search summary)

### Background facts (training knowledge) [TK]
**Version matrix**

| Feature | JDK 19 | JDK 20 | JDK 21 (LTS) | JDK 22 | JDK 23 | JDK 24 | JDK 25 (LTS) | JDK 26 | JDK 27 | JDK 28 (Mar 2027) |
|---|---|---|---|---|---|---|---|---|---|---|
| Virtual threads | JEP 425 preview | JEP 436 2nd preview | **JEP 444 final** | final | final | + JEP 491 (no `synchronized` pinning) | final | + class-init wait unmounts [S] | final | final |
| Structured concurrency | JEP 428 incubator | JEP 437 incubator | JEP 453 preview | JEP 462 | JEP 480 | JEP 499 | **JEP 505 (new `open()`/`Joiner` API)** | JEP 525 [S] | JEP 533 [S] | **JEP 543 final** [S] |
| Scoped values | — | JEP 429 incubator | JEP 446 preview | JEP 464 | JEP 481 | JEP 487 | **JEP 506 final** [S] | final | final | final |

(Row cells marked [S] are search-verified. Others are [TK]: the JEP numbers 425/436/446/464/480/481/487 and their JDK assignments come from training knowledge.)

**Virtual-thread API (JDK 21+, final)**
```java
Thread t1 = Thread.ofVirtual().name("worker-", 0).start(() -> work());   // builder
Thread t2 = Thread.startVirtualThread(() -> work());                      // shortcut
Thread t3 = Thread.ofVirtual().unstarted(() -> work());  t3.start();
ThreadFactory vtf = Thread.ofVirtual().name("vt-", 0).factory();         // for frameworks
boolean v = Thread.currentThread().isVirtual();

try (ExecutorService exec = Executors.newVirtualThreadPerTaskExecutor()) {  // one new VT per task, unbounded
    Future<String> f = exec.submit(() -> fetch("https://example.com"));
    System.out.println(f.get());
}   // close() waits for all tasks
```
- Virtual threads are always daemon threads with fixed `NORM_PRIORITY`. `setDaemon(false)` is not allowed. `Thread.getAllStackTraces()` returns platform threads only. `Executors.newThreadPerTaskExecutor(ThreadFactory)` (JDK 21) is the general form.
- The JEP 444 change from preview: virtual threads **always** support thread-locals. The preview-era `Thread.Builder.allowSetThreadLocals(false)` was dropped.
- How they work: a virtual thread is a `java.lang.Thread` whose stack frames live on the heap (as "stack chunk" objects) and are backed by an internal continuation (`jdk.internal.vm.Continuation`). The scheduler, a **work-stealing `ForkJoinPool` in FIFO mode**, mounts it on a **carrier** platform thread. When the code blocks in a JDK blocking operation (socket I/O, `LockSupport.park`, `Thread.sleep`, `BlockingQueue.take`, and `synchronized`/`Object.wait` from JDK 24), the continuation yields: frames are saved, the VT is **unmounted**, and the carrier is free. When unblocked, the VT is resubmitted and may resume on a different carrier.
- Scheduler tuning properties (JDK 21+): `jdk.virtualThreadScheduler.parallelism` (default = `availableProcessors()`), `jdk.virtualThreadScheduler.maxPoolSize` (default max(parallelism, 256)), `jdk.virtualThreadScheduler.minRunnable`. Some blocking operations (e.g. most file I/O) **capture** the carrier rather than unmount, and the scheduler compensates by temporarily adding carriers up to `maxPoolSize`.
- Analogy from JEP 444: the OS maps a large virtual address space onto limited RAM; the JDK maps many virtual threads onto few OS threads.

**Structured concurrency, JDK 25 API (JEP 505, `--enable-preview`)**
```java
// javac --release 25 --enable-preview App.java && java --enable-preview App
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Subtask;

Response handle() throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {             // default joiner: fail on first failure
        Subtask<String>  user  = scope.fork(() -> findUser());
        Subtask<Integer> order = scope.fork(() -> fetchOrder());
        scope.join();             // JDK 25: throws StructuredTaskScope.FailedException (unchecked) on failure
        return new Response(user.get(), order.get());
    }                             // close(): cancels unfinished subtasks, waits for them
}
```
- JDK 25 timeout: `StructuredTaskScope.open(Joiner.allSuccessfulOrThrow(), cf -> cf.withTimeout(Duration.ofSeconds(2)))`, which throws `StructuredTaskScope.TimeoutException`. Config methods: `withName`, `withThreadFactory`, `withTimeout`. Subtasks run in **virtual threads by default**.
- `Subtask<T>`: `state()` returns `Subtask.State {UNAVAILABLE, SUCCESS, FAILED}`, plus `get()` and `exception()`. `get()` before `join()` throws `IllegalStateException`. `fork`/`join` must be called by the scope's owner thread. Scopes must nest strictly, otherwise `StructureViolationException`.
- JDK 21–24 (JEP 453–499) used the old subclass API, `new StructuredTaskScope.ShutdownOnFailure()` + `scope.join().throwIfFailed()`. **This does not compile on JDK 25+.** Course material must not mix the two.

**Structured concurrency, JDK 27 API (JEP 533, `--enable-preview`), per the [S] findings above**
```java
// JDK 27, preview. Per InfoQ/HappyCoders: standard joiners throw ExecutionException.
Response handle() throws InterruptedException, ExecutionException {
    try (var scope = StructuredTaskScope.open()) {
        Subtask<String>  user  = scope.fork(() -> findUser());
        Subtask<Integer> order = scope.fork(() -> fetchOrder());
        scope.join();
        return new Response(user.get(), order.get());
    }
}

// Collect all results (JDK 26+: List<T>, not Stream<Subtask<T>>)
List<String> fetchAll(List<URI> uris) throws InterruptedException, ExecutionException {
    try (var scope = StructuredTaskScope.open(StructuredTaskScope.Joiner.<String>allSuccessfulOrThrow())) {
        for (URI u : uris) scope.fork(() -> get(u));
        return scope.join();
    }
}

// First success wins, the rest are cancelled (JDK 26+ name)
String fastestMirror() throws InterruptedException, ExecutionException {
    try (var scope = StructuredTaskScope.open(StructuredTaskScope.Joiner.<String>anySuccessfulOrThrow())) {
        scope.fork(() -> query("mirror-a"));
        scope.fork(() -> query("mirror-b"));
        return scope.join();
    }
}

// JDK 27: default joiner + config via the new UnaryOperator<Configuration> overload
try (var scope = StructuredTaskScope.open(cf -> cf.withTimeout(Duration.ofSeconds(2)))) { … }
```
(The exact generic signature and the timeout exception type in JDK 27 are unconfirmed; see Gaps.)

**Scoped values, JDK 25+ final**
```java
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

void serve(Request req) {
    ScopedValue.where(REQUEST_ID, req.id())
               .run(() -> handle(req));                 // binding visible only inside run()
}
String compute() throws Exception {
    return ScopedValue.where(REQUEST_ID, "batch-7")
                      .call(() -> doWork());            // call() takes ScopedValue.CallableOp, may throw
}
void handle(Request req) {
    String id = REQUEST_ID.get();                       // NoSuchElementException if unbound
    boolean bound = REQUEST_ID.isBound();
    String orDefault = REQUEST_ID.orElse("none");       // JDK 25: orElse(null) is not allowed [S]
}
```
- Bindings are immutable. To "change" a value, rebind in a nested `where(...).run(...)`. Multiple bindings: `ScopedValue.where(A, a).where(B, b).run(...)`. Inheritance happens **only** into `StructuredTaskScope` forks, so on JDK 25–27 that requires `--enable-preview` for STS. Plain `Thread`s and executors do not inherit. The early static helpers were removed during the previews: `getWhere` in JDK 23 (JEP 481, when `call` switched to `CallableOp`), then `runWhere`/`callWhere` in JDK 24 (JEP 487), leaving only the fluent `where(...).run/call` form. (From memory; check before teaching the history.)

### Inferences
- "Current API" for a course launched in Q4 2026: teach virtual threads and scoped values as final (JDK 25 LTS). Teach structured concurrency with the **JDK 27 shape** (catch `ExecutionException`), because JEP 543 says JDK 28 final = JDK 27 API. Warn that JDK 25 LTS users see `FailedException` and need `--enable-preview`.
- Students on the JDK 25 LTS who copy JDK 27 snippets will hit `Joiner.allSuccessfulOrThrow()` returning `Stream<Subtask<T>>` (JDK 25) vs `List<T>` (JDK 26+), plus the `FailedException`/`ExecutionException` difference. Pin each lesson to one JDK version.

### Gaps
- None of the JEP pages (444, 491, 505, 506, 525, 533, 543) or Javadoc could be opened. Exact JDK 27 signatures (`StructuredTaskScope<T, R, R_X>`?), the JDK 27 timeout exception type, the default joiner of no-arg `open()`, and the `allUntil` return type are **unconfirmed**.
- Whether `Joiner.onTimeout()` is public in JDK 26/27: conflicting search summaries.
- The JDK 19–24 JEP numbers for VT/SV previews (425, 436, 446, 464, 480, 481, 487) are [TK], not search-verified.

---

## Q2. Which things still pin a virtual thread after JEP 491, and how do you detect pinning today?

### Takeaway
From JDK 24, `synchronized` and `Object.wait()` no longer pin. A virtual thread is **still pinned** when a native frame (JNI or FFM downcall that calls back into blocking Java) or a VM frame is on its stack, notably **blocking inside a class initializer**. JDK 26 removed the "waiting for another thread's class init" case. Detect pinning with the **JFR `jdk.VirtualThreadPinned` event** (default 20 ms threshold; lower it to catch short pins). **`-Djdk.tracePinnedThreads` was removed in JDK 24.** File I/O "captures" the carrier, which the scheduler compensates for. That is not monitor pinning, but it has a similar effect.

### Cited Findings
- JEP 491 (JDK 24) still-pinned cases: "When blocking inside a class initializer. This is also a case where the virtual thread pins the carrier due to a native frame on the stack", and "when waiting for a class to be initialized by another thread". Also: "if a virtual thread calls native code, either through a native method or the Foreign Function & Memory API, and that native code calls back to Java code that performs a blocking operation or blocks on a monitor, then the virtual thread will be pinned." [S] — [JEP 491](https://openjdk.org/jeps/491)
- JDK 26 (JDK-8369238): waiting for another thread's class initializer now unmounts. [S] — [Oracle JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26-relnote-issues.html)
- JDK 24 JFR change: the pinned event "will now be recorded when a virtual thread parks, blocks on monitor enter, or waits in Object.wait while pinned due to a native or VM frame. This includes blocking during class loading while executing a class initializer." [S] — [JDK-8338813, Implement JEP 491](https://bugs.java.com/bugdatabase/view_bug?bug_id=8338813)
- JEP 491 describes `jdk.tracePinnedThreads` as "introduced by JEP 444" and as printing a stack trace "whenever a virtual thread blocks inside a synchronized method". [S] — [JEP 491](https://openjdk.org/jeps/491)
- **Removal:** "The `jdk.tracePinnedThreads` system property is no longer supported by Virtual Threads implementation in mainline. That system property was dropped as part of https://github.com/openjdk/jdk/pull/21565 in JDK 24." [S] — [serviceability-dev, May 2025](https://mail.openjdk.org/pipermail/serviceability-dev/2025-May/064051.html). A follow-up test cleanup is at [JDK-8357673](https://bugs.openjdk.org/browse/JDK-8357673). A field guide gives the same advice: removed in JDK 24, works on 21–23, use JFR on 24+. [S] — [foojay virtual-thread pinning field guide](https://foojay.io/today/virtual-thread-pinning-field-guide/)
- Residual pinning "around native frames, class loading, and local file I/O on Linux" keeps the JFR `jdk.VirtualThreadPinned` event on the rollout checklist. The default threshold is 20 ms in JDK 25. [S] — [InfoQ, "Virtual Threads after JDK 24"](https://www.infoq.com/articles/virtual-threads-after-jdk24/)
- Caution from a single test: a native-call pin was not flagged at the default setting and appeared only with the event explicitly enabled at a 10 ms threshold. Treat this as a caution, not settled fact. [S] — [devdojo, "What Still Pins Virtual Threads After JDK 24"](https://devdojo.academy/en/blog/virtual-thread-pinning-jdk-24-what-still-pins/)
- Thread dumps: `jcmd <PID> Thread.dump_to_file -format=json thread_dump.json` writes a JSON dump with the thread container hierarchy. `Thread.print` (and jstack) lacks detail on virtual threads. Before JDK 25, `Thread.dump_to_file` lacked lock and monitor information. [S] — [Keycloak thread-dump guide](https://www.keycloak.org/observability/thread-dumps). JDK-8356872 adds thread state and lock info to text and JSON dumps (with a JSON schema file). [S] — [JDK-8356872](https://bugs.openjdk.org/browse/JDK-8356872). JDK-8365057 adds the owner of a `java.util.concurrent` lock (the `parkBlocker` owner, when it is an `AbstractOwnableSynchronizer`). [S] — [jmx-dev RFR, Sep 2025](https://mail.openjdk.org/pipermail/jmx-dev/2025-September/003658.html)
- A field article says jstack misses virtual threads in production services. [S, title only] — [foojay "What jstack Misses When Your Java Service Uses Virtual Threads"](https://foojay.io/today/what-jstack-misses-when-your-java-service-uses-virtual-threads/)

### Background facts (training knowledge) [TK]
- JFR virtual-thread events (JDK 21+): `jdk.VirtualThreadStart` / `jdk.VirtualThreadEnd` (off by default), **`jdk.VirtualThreadPinned` (on by default, threshold 20 ms)**, `jdk.VirtualThreadSubmitFailed` (on).
- Commands:
```
java -XX:StartFlightRecording=filename=rec.jfr,settings=profile,jdk.VirtualThreadPinned#threshold=1ms App
jfr print --events jdk.VirtualThreadPinned rec.jfr
jcmd <pid> JFR.start name=pin settings=profile
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json
```
(The `event#setting=value` override syntax on `-XX:StartFlightRecording` exists since JDK 17.) `HotSpotDiagnosticMXBean.dumpThreads(file, ThreadDumpFormat.JSON)` is the programmatic form (JDK 21).
- What is *not* pinning but still matters: file I/O and some DNS lookups block the carrier ("capture"), and the scheduler compensates by temporarily growing beyond parallelism. Long CPU-bound loops are not pinning, but they monopolize a carrier because there is no time-slice preemption of virtual threads.
- On JDK 21–23, `synchronized` + blocking (I/O, `sleep`, `Object.wait`) pins. The JDK 21-era advice "replace `synchronized` with `ReentrantLock` around blocking code" is **no longer needed on JDK 24+**, but it is still correct for JDK 21 deployments.

### Inferences
- On JDK 25 LTS, the remaining practical pinning sources are (a) native libraries that call back into Java and block, (b) slow or blocking `static {}` initializers, (c) carrier capture by file I/O. Lessons should show (b), because it is easy to reproduce in pure Java.
- Monitoring advice: keep `jdk.VirtualThreadPinned` in continuous JFR recordings. Consider lowering the threshold in staging.

### Gaps
- The exact field list of the JDK 24+ `jdk.VirtualThreadPinned` event (one blog claims it carries the pin reason and carrier identity; unverified).
- Which JDK release first shipped JDK-8356872 and JDK-8365057 (the Keycloak note suggests JDK 25 for lock info; JDK-8365057 is likely JDK 26). Not confirmed.
- Whether JEP 491's still-pinned list includes other VM-frame cases (e.g. symbolic-reference resolution during class loading) beyond those quoted. Could not open the JEP.

---

## Q3. What are real-world lessons from teams migrating to virtual threads?

### Takeaway
The canonical incident is Netflix's July 2024 "Java 21 Virtual Threads – Dude, Where's My Lock?". Their Spring Boot 3/Tomcat services hung because every carrier was pinned by VTs blocked inside `synchronized`, while the next lock holder was a VT that could not get a carrier. JDK 24/25 fixes this class of bug. The lessons that still apply on JDK 25+ are about **resources, not threads**: connection pools and downstream limits become the real concurrency cap, ThreadLocal caches stop caching, and observability tools need updating.

### Cited Findings
- **Netflix (blog post dated around 29 July 2024):** after enabling virtual threads for request handling on Java 21 + Spring Boot 3 + embedded Tomcat, services showed intermittent timeouts and full unresponsiveness. Threads were pinned to carriers while waiting on a lock inside a `synchronized` block. Thread analysis showed that no thread appeared to own the lock. A heap dump (Eclipse MAT) confirmed no owner while waiters could not proceed. The lock object was found via the stack of the non-virtual AsyncReporter thread. Mechanism: "None of the pinned VTs can ever acquire the lock — because they're pinned, and the carrier threads they need to run on are held by themselves." [S] — [sysdesign-wiki summary of the Netflix post](https://sysdesign-wiki.pages.dev/sources/2024-07-29-netflix-java-21-virtual-threads-dude-wheres-my-lock/), [InfoQ coverage (Aug 2024)](https://www.infoq.com/news/2024/08/netflix-performance-case-study). The search tool rated InfoQ the more dependable secondary account. Java Code Geeks' retelling is garbled.
- JEP 491 (JDK 24) removed the monitor pinning that caused Java 21 production stalls. [S] — [InfoQ, "Virtual Threads after JDK 24"](https://www.infoq.com/articles/virtual-threads-after-jdk24/); see also [Java Virtual Threads: The Pinning Problem, the Deadlock, and the Fix in Java 24 (blog, Apr 2026)](https://shbhmrzd.github.io/java/concurrency/virtual-threads/2026/04/25/java-virtual-threads-pinning-and-the-deadlock-problem.html) [S, title]
- "Connection pools, rate limits, file descriptors, and downstream services become the real concurrency boundaries once virtual threads remove the servlet-thread ceiling." [S] — [InfoQ](https://www.infoq.com/articles/virtual-threads-after-jdk24/). Example: 10,000 concurrent requests competing for a pool of 10 DB connections. Monitor pool wait time, queue depth and real concurrency, not thread counts. [S] — [Spring Boot virtual threads guide (blog)](https://blogs.pavanrangani.com/spring-boot-virtual-threads-production/)
- ThreadLocal caches: each request gets a fresh VT, so a `ThreadLocal.withInitial(() -> new SimpleDateFormat(...))` "cache" is rebuilt per request. One benchmark reported a **2,216× increase** in initializations, showing up as GC pressure rather than errors. [S, secondary, single source] — [daily.dev summary of "Virtual Threads after JDK 24"](https://daily.dev/posts/virtual-threads-after-jdk-24-what-changed-for-production-java-1iad53gy7). JEP 444 says not to use thread-locals to pool costly resources. [S] — [JEP 444](https://openjdk.org/jeps/444)
- Suggested fixes: semaphores around shared resources, a concurrent cache (e.g. Caffeine) instead of per-thread caches, auditing ThreadLocal use (with `remove()` in `finally`), and moving request context to scoped values (JDK 25). [S] — [InfoQ](https://www.infoq.com/articles/virtual-threads-after-jdk24/), [Java Code Geeks, ThreadLocal vs Scoped Values (Mar 2026)](https://www.javacodegeeks.com/2026/03/threadlocal-vs-scoped-valuesthe-virtual-thread-migrationno-one-warned-you-about.html)
- Apple's ServiceTalk docs recommend **JDK 25 as the first release suitable for large-scale production use** of virtual threads. [S] — [ServiceTalk virtual threads](https://apple.github.io/servicetalk/servicetalk/SNAPSHOT/virtual-threads.html)
- Pooling VTs: a Quarkus article (Sep 2026) measured that pooling saved a small amount of allocation but cost substantial memory. The advice against pooling stands. (The original explanation rested on a buggy benchmark and was revised.) [S] — [Quarkus, "To Cache or Not to Cache Virtual Threads"](https://quarkus.io/blog/to-cache-or-not-to-cache-virtual-threads/)
- Contrary data point: a loom-dev thread (May 2024) found a Semaphore strategy used more CPU than a fixed pool of VTs on many-core machines. Replies attributed this to heavy semaphore contention when creating very many threads. [S] — [loom-dev, "Performance of pooling virtual threads vs. semaphores"](https://mail.openjdk.org/pipermail/loom-dev/2024-May/006603.html)
- Claim (unverified): HikariCP's `ConcurrentBag` uses ThreadLocal connection affinity, which loses its benefit under VTs. [S, flagged by the search tool as unverified] — see Gaps.
- Other practitioner write-ups surfaced (titles only): [Cashfree, "7 Key Lessons from Using Java 21 Virtual Threads in Production"](https://www.cashfree.com/blog/java-21-virtual-threads-lessons-production/), [Java Code Geeks, "Stop Using Virtual Threads for Everything"](https://www.javacodegeeks.com/2026/07/stop-using-virtual-threads-for-everything-performance-lessons-learned.html), [Java Code Geeks, "Virtual Threads One Year in Production"](https://www.javacodegeeks.com/2026/04/virtual-threads-one-year-in-production-what-teams-got-wrong-and-what-actually-improved.html). Content not reviewed.

### Inferences
- Migration checklist for JDK 25: (1) upgrade from 21 to 25 before enabling VTs widely (JEP 491); (2) size and **bound** every downstream resource (Semaphore or pool) and alert on pool wait time; (3) grep for `ThreadLocal`/`withInitial` caches and replace them with shared caches or scoped values; (4) keep JFR `VirtualThreadPinned` on; (5) learn `jcmd Thread.dump_to_file -format=json`, because jstack will not show VTs; (6) check native libraries that call back into Java.

### Gaps
- The original Netflix Tech Blog URL did not appear in search results. It is cited via a summary site and InfoQ. Specific library frames in the Netflix incident (Brave/Zipkin reporter, lock type, carrier count) are not verified here beyond "AsyncReporter".
- HikariCP ThreadLocal claim: not checked against HikariCP source.
- No primary (vendor-published) benchmark numbers were verified.

---

## Q4. What are the most common misconceptions?

### Takeaway
Virtual threads raise **throughput for workloads with many concurrent, mostly-blocking tasks**. They do not make code faster, do not help CPU-bound work, should never be pooled, and parallel streams do not use them. Several "facts" from 2023 tutorials are now stale: `synchronized` pins, `-Djdk.tracePinnedThreads`, scoped values in preview, the `ShutdownOnFailure` API.

### Cited Findings
- **"Pool them":** wrong. A thread pool shares expensive resources; virtual threads are cheap enough that pooling is never needed, and pooling to limit concurrency is discouraged. Use a Semaphore. [S] — [JEP 444](https://openjdk.org/jeps/444), [Java Almanac virtual threads](https://javaalmanac.io/features/virtual-threads/), [HappyCoders virtual threads](https://www.happycoders.eu/java/virtual-threads/)
- **"ThreadLocal is fine as a cache":** use thread-locals "only after careful consideration", not to pool costly resources. [S] — [JEP 444](https://openjdk.org/jeps/444)
- **"synchronized always pins":** stale since JDK 24. [S] — [JEP 491](https://openjdk.org/jeps/491)
- **"Use -Djdk.tracePinnedThreads":** removed in JDK 24. [S] — [serviceability-dev](https://mail.openjdk.org/pipermail/serviceability-dev/2025-May/064051.html)
- **"Structured concurrency is final in Java 25":** wrong. Preview in 25, 26, 27; final only in JDK 28 (Mar 2027). [S] — [InfoQ JEP 543](https://www.infoq.com/news/2026/10/jep-543-jdk-28/)
- **"Scoped values are preview":** final since JDK 25. [S] — [JEP 506](https://openjdk.org/jeps/506)
- **"Raising the thread count removes the bottleneck":** the cap moves to connection pools and downstream limits. [S] — [InfoQ](https://www.infoq.com/articles/virtual-threads-after-jdk24/)

### Background facts (training knowledge) [TK]
- JEP 444: "Virtual threads are not faster threads — they do not run code any faster than platform threads. They exist to provide scale (higher throughput), not speed (lower latency)." It also says they help when the number of concurrent tasks is high (more than a few thousand) and the workload is not CPU-bound. (Quote from memory; check the wording before quoting in a lesson.)
- **"CPU-bound work benefits":** no. With N carriers, at most N VTs compute at once, the same as a fixed pool of N. There is no preemptive time-slicing between VTs.
- **"Parallel streams / CompletableFuture use virtual threads":** no. Both use `ForkJoinPool.commonPool()` platform workers. A parallel stream started *from* a VT still runs on the common pool.
- **"newVirtualThreadPerTaskExecutor limits concurrency":** no. It creates a new unbounded VT per task.
- **"Virtual threads replace reactive/CompletableFuture entirely":** opinion territory. They remove the *need* for async APIs for scalability, but CF remains useful for composition. Structured concurrency is the blocking-style alternative.
- **"Thread.sleep in a VT wastes an OS thread":** no. It unmounts.
- **"A ThreadLocal set in the parent shows up in a VT started from an executor":** no. Only `InheritableThreadLocal`s are copied at thread creation, and builders can disable that.

### Inferences
- Present each misconception with a two-minute demo that disproves it (see Teaching notes).

### Gaps
- The exact JEP 444 "not faster threads" wording could not be re-quoted from the page.

---

## Q5. What are good hands-on demos and exercises?

### Takeaway
The best demos make Little's law visible: (1) a JEP 444-style "N sleeping tasks" run on VTs vs a fixed pool; (2) a ThreadPoolExecutor queue-vs-max puzzle; (3) a pinning demo that behaves differently on JDK 21 and JDK 25 (`synchronized`) and still pins on 25 (class initializer); (4) silent failure of scheduled tasks and of `submit()`. Expected outcomes below are **derived from the stated rules and Little's law, not measured in this session**.

### Cited Findings
- JEP 444's flagship example uses `Executors.newVirtualThreadPerTaskExecutor()` to run 10,000 tasks that each sleep 1 second, inside try-with-resources. [TK for the exact code; the JEP is the source] — [JEP 444](https://openjdk.org/jeps/444) (not opened)
- The pinning demo idea (sleep inside `synchronized` exhausts carriers on older JDKs) appears in the Java Almanac. [S] — [Java Almanac virtual threads](https://javaalmanac.io/features/virtual-threads/)
- A worked example repository for the current STS API exists: [danvega/structured-concurrency](https://github.com/danvega/structured-concurrency). [S]

### Inferences
- See Teaching notes for full demo specs and expected outcomes.

### Gaps
- No measured numbers (wall time, heap) for the million-thread demo were found in verified sources. Writers should run it on the course's reference machine and publish their own numbers.

---

## Teaching notes

### Misconceptions to address explicitly (with the one-line fix)
1. "Virtual threads are faster." They give scale, not speed. Same CPU per request; more requests in flight.
2. "CPU-bound code gets faster." No. Carriers = cores. Use a fixed pool or ForkJoinPool sized to cores, or parallel streams.
3. "Pool your virtual threads." Never. Create one per task and limit the *resource* with a Semaphore.
4. "Parallel streams / `supplyAsync()` use virtual threads." No, they use the common ForkJoinPool. Pass a VT executor explicitly to CF if you want one.
5. "`synchronized` pins." True on JDK 21–23 only. From JDK 24, no.
6. "`-Djdk.tracePinnedThreads=full` shows pinning." Removed in JDK 24. Use JFR `jdk.VirtualThreadPinned`.
7. "`maximumPoolSize` = how many threads I'll get." Only when the queue is full. With an unbounded queue you never exceed core.
8. "`shutdown()` waits for tasks." No, `awaitTermination` or `close()` waits.
9. "Exceptions in pool tasks are logged." Not with `submit()`. They are hidden in the Future.
10. "A failing periodic task logs and retries." No. It silently stops forever.
11. "`orTimeout()` cancels the work." No. It only completes the future; the work keeps running.
12. "`cancel(true)` kills the thread." It only interrupts; the code must cooperate. On CompletableFuture it does not even interrupt.
13. "Structured concurrency and scoped values are both preview / both final." SV is final in 25. STS is preview until JDK 28.

### Analogies
- **ThreadPoolExecutor as a restaurant:** core threads are permanent waiters. The work queue is the waiting area. Max threads are temp staff, called in **only when the waiting area is full**. The rejection policy is the bouncer (`CallerRunsPolicy` = the manager takes the order himself, which slows down the front door: back-pressure).
- **Virtual threads as virtual memory** (JEP 444's own analogy): many virtual threads mapped onto few OS threads, the way many virtual pages map onto limited RAM.
- **Carriers as desks, virtual threads as workers with briefcases:** when a worker waits for a phone call (I/O), he packs his papers (stack frames to the heap) and leaves the desk. Any free desk can be used when he returns. **Pinning** is a worker who is handcuffed to the desk while waiting: a native frame, or `synchronized` before JDK 24.
- **Little's law as a supermarket:** customers in the store = arrival rate × time spent. To serve more customers per hour when each one shops for 30 minutes, you need more people inside, not faster cashiers.
- **Structured concurrency as a function call for concurrency:** subtasks cannot outlive the block that started them, the same way local variables cannot outlive their scope.
- **Scoped value vs ThreadLocal:** a ThreadLocal is a whiteboard anyone can scribble on, and it is never wiped. A scoped value is a sealed envelope handed down a call chain that is shredded when the call returns.

### Demo ideas (with expected outcomes)
1. **One million sleeping virtual threads** (JDK 21+)
```java
public static void main(String[] args) {
    long t0 = System.nanoTime();
    try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
        for (int i = 0; i < 1_000_000; i++)
            exec.submit(() -> { Thread.sleep(Duration.ofSeconds(1)); return null; });
    }
    System.out.printf("done in %d ms%n", (System.nanoTime() - t0) / 1_000_000);
}
```
Expected: finishes in a few seconds (1 s of sleep plus creation and scheduling overhead). Only about `availableProcessors()` carrier threads exist (check with `jcmd <pid> Thread.print`, or count `ForkJoinPool-1-worker-*`). Contrast: the same loop with `Executors.newCachedThreadPool()` at 1M tasks will typically fail with `OutOfMemoryError: unable to create native thread` or thrash the machine. **Run the platform version only at 10k–20k, or in a container with limits.** Exact timings and heap use must be measured on the course machine.

2. **200-thread pool vs virtual threads on a blocking workload**: 10,000 tasks, each `Thread.sleep(100 ms)` (stand-in for an HTTP or DB call).
- `Executors.newFixedThreadPool(200)`: Little's law caps throughput at 200 / 0.1 s = 2,000 tasks/s, so about **5 s** total (10,000 / 2,000).
- `newVirtualThreadPerTaskExecutor()`: about **0.1–0.5 s** (all tasks sleep concurrently).
- Follow-up: replace sleep with CPU work (e.g. a 100 ms hash loop). Both finish in about `10,000 × 0.1 s / cores`. VTs give **no win**, which disproves misconception 2.
- Follow-up 2: add `Semaphore(20)` around the "DB call" in the VT version. Total time is about 10,000 × 0.1 / 20 = **50 s**. The resource limit, not the thread count, decides throughput.

3. **ThreadPoolExecutor queue puzzle** (JDK 5+): `new ThreadPoolExecutor(2, 4, 60, SECONDS, new ArrayBlockingQueue<>(2))`. Submit 7 tasks that each block for 5 s.
Expected: tasks 1–2 start core threads, 3–4 queue, 5–6 start extra threads (pool size 4), and **task 7 is rejected with `RejectedExecutionException`** (AbortPolicy). `getPoolSize()==4`, `getQueue().size()==2`. Then swap in `new LinkedBlockingQueue<>()`: pool size stays at **2** forever, all 7 are accepted, and total time is about 4 × 5 s = 20 s. Then try `CallerRunsPolicy`: task 7 runs on `main`, blocking the submit loop for 5 s.

4. **Pinning across JDK versions**: run with `-Djdk.virtualThreadScheduler.parallelism=1` and JFR on.
```java
static final Object LOCK = new Object();
// start 5 VTs, each: synchronized (LOCK) { Thread.sleep(1000); }   plus one VT that prints "tick" every 100 ms
```
Expected on **JDK 21**: the ticker freezes while a VT sleeps inside `synchronized`, and JFR shows `jdk.VirtualThreadPinned` events (about 1 s each). Expected on **JDK 24/25+**: the ticker keeps ticking and there are no pinned events. Total time is about 5 s in both cases, because the lock still serializes the sleepers.
Then show **what still pins on JDK 25**: a class whose `static {}` block sleeps 1 s, first touched by a VT. JFR records a pinned event (class-initializer case), and the ticker stalls. On JDK 26+, *other* VTs waiting for that class init unmount (JDK-8369238), but the initializing VT itself still pins.

5. **Silent death of scheduled tasks** (JDK 5+): `scheduleAtFixedRate` a task that throws on its 3rd run. Expected: runs 1–2 print, then nothing more, with no log output. `future.get()` throws `ExecutionException` and `isDone()` is true. Fix: wrap the body in try/catch.

6. **`execute()` vs `submit()` exceptions**: install a `ThreadFactory` with an `UncaughtExceptionHandler`. `execute(() -> { throw new RuntimeException(); })` triggers the handler and the worker thread is replaced. `submit(...)` prints nothing until `get()`.

7. **CompletableFuture threads**: print `Thread.currentThread()` inside `supplyAsync` with and without an executor. You get `ForkJoinPool.commonPool-worker-N` vs your pool's names. On JDK 21 inside a 1–2 CPU container (`docker run --cpus=2`), the no-executor version shows a new `Thread-N` per task. On JDK 25+ it shows common-pool workers (JDK-8319447 change).

8. **Thread dump of 10k virtual threads**: start 10k VTs blocked on a `CountDownLatch`. `jstack <pid>` shows none of them. `jcmd <pid> Thread.dump_to_file -format=json vt.json` lists them grouped under their thread container (the executor). On JDK 25+, compare the lock information (JDK-8356872).

9. **Structured concurrency failure propagation** (JDK 25/27 with `--enable-preview`): fork task A (sleeps 5 s) and task B (throws after 100 ms). Expected: `join()` throws after about 100 ms (JDK 25 `FailedException`, JDK 27 `ExecutionException`), and A is interrupted or cancelled, which you can print in a `finally`. Compare with an `ExecutorService` + two `Future`s, where A keeps running for 5 s (a thread leak).

10. **Scoped value vs ThreadLocal leak**: set a ThreadLocal in a pooled platform thread and forget `remove()`. The next task sees the stale value. The same pattern with `ScopedValue.where(...).run(...)` makes the value unbound after `run()` returns, so `isBound()==false`.

### Exercise ideas (with expected outcomes)
- **E1 Pool sizing:** an 8-core service, each request spends 20 ms CPU and 180 ms waiting on a DB, target CPU 80%. Goetz: 8 × 0.8 × (1 + 180/20) = **64 threads**. Little's law check: at 64 threads and 200 ms per request, max throughput is about 320 req/s.
- **E2 Little's law:** an API must handle 5,000 req/s with 400 ms average latency. Concurrency = **2,000 requests in flight**. Discuss why a 200-thread Tomcat pool caps out at 500 req/s, and what changes with VTs (the DB pool size becomes the cap).
- **E3 Predict the pool size:** give 4 TPE configurations (Synchronous, bounded, unbounded, core=0) and a burst of N tasks. Students predict pool size, queue size, and rejections, then run to check. (Note: `core=0` + `LinkedBlockingQueue` still starts 1 thread when the pool is empty.)
- **E4 Fix the leak:** a periodic health check stops after a transient exception. The student must find the cause (suppressed executions) and fix it.
- **E5 Migrate a fan-out:** rewrite a `CompletableFuture.allOf` fan-out of 3 remote calls as a `StructuredTaskScope` (JDK 27 preview) with a 2 s timeout. Expected: the same result, plus automatic cancellation of siblings on failure.
- **E6 Bound a resource:** 10,000 VT tasks call a fake DB that throws if more than 50 calls are concurrent. The student adds `Semaphore(50)`. Expected: zero errors, total time about tasks × latency / 50.
- **E7 Replace a ThreadLocal cache:** a `ThreadLocal<SimpleDateFormat>` under VTs, counting initializations. Expected: about one initialization per task. Fix with `DateTimeFormatter` (immutable, shared) and measure again: 0 per task.
- **E8 Graceful shutdown:** implement shutdown, awaitTermination(5 s), shutdownNow, and report the never-started tasks returned by `shutdownNow()`. Test with a task that ignores interrupts: `awaitTermination` times out and the code must log it.

### Version-pinning advice for lesson writers
- State the JDK at the top of every lesson. Recommended baseline: **JDK 25 LTS** for virtual threads, scoped values and executors. **JDK 27** (preview, `--enable-preview`) for structured concurrency, noting that JDK 28 (March 2027) makes it final unchanged.
- Never show `StructuredTaskScope.ShutdownOnFailure` (JDK 21–24 API) except as history.
- Never recommend `-Djdk.tracePinnedThreads` for JDK 24+.

---

## Verified URLs

**No URL was fetched successfully in this session.** Page fetches to **openjdk.org** (JEP 491, JEP 525, JDK 26 and 27 project pages) and **docs.oracle.com** (virtual threads guide) failed with a DNS/network-policy error ("host outside the session's allowed network domains"). After the second failure, no other sites were attempted, per the tool's guidance.

Every URL cited inline above was **surfaced by the web-search tool**, which returned a summary (often with short quotes) of that page's content. Those citations are marked [S]. They are search-summary evidence, not verified page reads, so this section lists none of them. To produce a verified URL list, allow openjdk.org and docs.oracle.com (and ideally inside.java, infoq.com, netflixtechblog.com) in the environment's network settings, then re-run the fetches. Highest priority to re-verify: [JEP 491](https://openjdk.org/jeps/491), [JEP 533](https://openjdk.org/jeps/533), the JDK 27 `StructuredTaskScope` Javadoc, [JEP 506](https://openjdk.org/jeps/506), the [Oracle JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26-relnote-issues.html), and the Netflix Tech Blog post.
