# Track: exec, "Thread pools and executors" (lab: labs/executors, package workbench.executors.lNN)

Research notes: executors_and_virtual_threads.md (executor parts), and java_concurrency_and_jmm.md
if it exists by the time you start. Labs in Java (release 21). Add a Kotlin `compare` where it teaches
something (Kotlin calling the same executor APIs, or coroutine equivalents briefly).

Lessons:
- exec-01 Why pools: thread creation cost, Executor vs ExecutorService, execute vs submit (submit hides
  exceptions inside the Future), shutdown/shutdownNow/awaitTermination, ExecutorService is
  AutoCloseable since JDK 19 (close() waits). Lab: a tiny fixed pool built from N workers and a
  BlockingQueue, with correct shutdown, so the learner sees what a pool really is.
- exec-02 Inside ThreadPoolExecutor: core then queue then max then reject; why an unbounded queue
  makes maximumPoolSize useless; the four rejection policies; keepAlive; allowCoreThreadTimeOut;
  prestartAllCoreThreads. Figure: the decision flow. Lab: configure a pool to meet a spec and
  predict which tasks get rejected; write a custom RejectedExecutionHandler.
- exec-03 Sizing a pool: CPU-bound vs IO-bound, N*(1+W/C), Little's law L = lambda * W with a worked
  payments example, downstream limits (a 20-connection DB pool caps you), bulkheads.
- exec-04 Callable, Future, cancellation and interruption: get with timeout, cancel(true) interrupts,
  the interruption protocol (restore the flag), Future.state()/resultNow()/exceptionNow() (JDK 19),
  invokeAll/invokeAny.
- exec-05 Scheduled executors: schedule, fixed rate vs fixed delay, an exception silently stops future
  runs, runs never overlap, catching inside the task; mention the JDK 25 ForkJoinPool change from notes.
- exec-06 CompletableFuture composing: supplyAsync and its default executor (and the JDK 25 change in
  notes), thenApply/thenCompose/thenCombine/thenAccept, async variants, join vs get. Lab: a checkout
  that fetches price and FX rate in parallel, combines them, then charges.
- exec-07 CompletableFuture errors, timeouts and fan-out: exceptionally/handle/whenComplete,
  exceptionallyCompose, CompletionException wrapping, orTimeout/completeOnTimeout, allOf/anyOf,
  cancel does not interrupt the running task. Lab: a quote aggregator with per-provider timeouts and fallbacks.
- exec-08 ForkJoinPool, work stealing and parallel streams: RecursiveTask, fork/compute/join order,
  common pool parallelism, parallel stream pitfalls (blocking IO in the common pool, shared mutable
  state, small inputs), ManagedBlocker in brief. Figure: work-stealing deques.
- exec-09 Pools in production: naming threads (Thread.ofPlatform().name("x-", 0).factory()),
  UncaughtExceptionHandler vs submit swallowing, propagating context (MDC/ThreadLocal) by wrapping
  tasks, metrics to watch (queue size, active count, rejections), graceful shutdown order,
  pool-induced deadlock (tasks waiting on tasks in the same bounded pool). Lab: an executor decorator
  that names threads, carries context and logs failures; fix a pool-induced deadlock.
