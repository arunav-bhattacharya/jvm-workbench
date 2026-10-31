# Track: co, "Kotlin coroutines" (lab: labs/coroutines, package workbench.coroutines.lNN)

Research notes: kotlin_coroutines.md. Labs in Kotlin with kotlinx-coroutines-test (`runTest`,
virtual time). Dependencies available: kotlinx-coroutines-core, -reactor, -test 1.11.0, reactor-core,
reactor-test. Keep real-time delays in tests tiny or use virtual time. Use `compare` blocks where a
Java counterpart exists (CompletableFuture, virtual threads, Reactor).

Lessons:
- co-01 Suspend functions from zero: what suspend means, thread vs coroutine, `delay` vs `Thread.sleep`,
  the compiler's continuation-passing state machine (show the `Continuation` parameter with javap),
  wrapping a callback API with `suspendCancellableCoroutine`. Lab: wrap a callback-based
  card-issuer client into a suspend function, with cancellation.
- co-02 Builders: launch, async/await, runBlocking (only at edges: main and tests), coroutineScope,
  Job and Deferred, concurrent decomposition. Lab: fetch three quotes concurrently; total time is the
  slowest, not the sum (assert with virtual time).
- co-03 Structured concurrency: the job tree, a parent waits for children, failure cancels siblings
  and parent, GlobalScope and leaked work, a class that owns a scope and closes it. Figure: the tree.
- co-04 Dispatchers and the coroutine context: Default, IO (64 and its elasticity), Main, Unconfined,
  limitedParallelism (views over IO add to the 64), withContext, Executor.asCoroutineDispatcher
  (including a virtual-thread executor), context elements and `+`, CoroutineName.
- co-05 Cancellation and timeouts: cooperative cancellation, isActive/ensureActive/yield, never swallow
  CancellationException (runCatching trap), NonCancellable in finally, withTimeout vs
  withTimeoutOrNull, blocking calls need runInterruptible, asFlow builders don't check cancellation.
- co-06 Exceptions: launch vs async propagation (a failed async cancels its parent without await),
  CoroutineExceptionHandler only on roots, SupervisorJob vs supervisorScope, the
  `launch(SupervisorJob())` trap. Lab: notification fan-out where one failing channel does not cancel the others.
- co-07 Flow basics: cold streams, builders, intermediate vs terminal operators, flowOn,
  exception transparency and `catch`, onCompletion, `.cancellable()`. Compare with Reactor Flux briefly.
- co-08 StateFlow, SharedFlow and hot streams: conflation and equality in StateFlow, replay,
  extraBufferCapacity, onBufferOverflow, stateIn/shareIn with SharingStarted, the
  private-mutable/public-read-only pattern (explicit backing fields are stable in Kotlin 2.4, per notes).
- co-09 Channels, select and pipelines: capacities, produce, fan-out/fan-in, select,
  channelFlow/callbackFlow, Flow buffer/conflate/collectLatest as backpressure.
- co-10 Shared state and testing: Mutex (not reentrant), atomics, `limitedParallelism(1)` is not a
  mutex across suspension points, runTest, StandardTestDispatcher vs UnconfinedTestDispatcher,
  advanceUntilIdle, backgroundScope, virtual time; test a retry-with-backoff.
- co-11 Coroutines meet Java: `future {}`, `await()` on CompletableFuture, Reactor interop
  (mono {}, awaitSingle, asFlow, asFlux), calling suspend code from Java, and a decision guide:
  virtual threads vs coroutines vs Reactor, with a table, for a team like the learner's.
