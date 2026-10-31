# Track: vt, "Virtual threads" (lab: labs/vthreads, package workbench.vthreads.lNN)

Research notes: executors_and_virtual_threads.md (virtual thread parts). Key facts from it: JEP 444
final in JDK 21; JEP 491 in JDK 24 removed pinning on synchronized in most cases; what still pins;
-Djdk.tracePinnedThreads was removed in JDK 24, use JFR jdk.VirtualThreadPinned; structured
concurrency is still preview in JDK 25 (JEP 505), 26 (JEP 525) and 27 (JEP 533) and is final in
JDK 28; scoped values are final in JDK 25 (JEP 506). Labs compile with release 21 and must pass on
JDK 21 and 25, so labs use only final JDK 21 APIs (no ScopedValue, no StructuredTaskScope).
Preview-API demos go in labs/vthreads/preview/*.java as single-file programs run with
`java --enable-preview --source 25 <file>` (outside Gradle; say in the lesson they need JDK 25 and
that the API shape changes slightly in 27 and is final in 28). You cannot run those here (JDK 21 only),
so keep them short and check them against the JDK 25 API in the notes. Say so in your report.
Keep demos safe on a laptop: no more than about 100,000 virtual threads, 5,000 platform threads.

Lessons:
- vt-01 The thread-per-request wall: what a platform thread costs, the async/reactive workaround and
  its price, Little's law with a payments example. Lab: a blocking handler run on a fixed pool vs one
  virtual thread per task; a test shows the virtual version finishes 2,000 sleeping tasks far faster.
- vt-02 How virtual threads work: continuations, carrier threads, the ForkJoinPool scheduler,
  mount/unmount at blocking points, stacks on the heap. Figure: carriers and mounted threads.
  Demo: print Thread.currentThread() before and after a sleep to see carriers.
- vt-03 Using virtual threads: Thread.ofVirtual(), startVirtualThread, newVirtualThreadPerTaskExecutor
  in try-with-resources, one thread per task, never pool them, limit access to scarce resources with a
  Semaphore. Lab: fan out 5,000 blocking calls while never exceeding 20 in flight (tests assert the max).
- vt-04 Pinning, ThreadLocals and other traps: synchronized before and after JDK 24, what still pins,
  JFR detection, ThreadLocal caches multiplied by a million threads, CPU-bound work gains nothing.
  Lab: replace synchronized-around-IO with ReentrantLock in a cache; replace a ThreadLocal cache.
- vt-05 Structured concurrency and scoped values: the problem (leaked threads, lost cancellation,
  ThreadLocal inheritance), StructuredTaskScope in its JDK 25 preview shape with Joiner, the changes
  in 27 and finalization in 28, ScopedValue (final in 25) vs ThreadLocal. Lab (Java 21 APIs): build a
  mini "fork, fail fast, cancel siblings" helper on an ExecutorService so the learner understands
  what the scope does for them. Preview demos in labs/vthreads/preview/.
- vt-06 Moving a blocking service to virtual threads: a migration checklist (replace pools, keep
  semaphores for downstream limits, ThreadLocal caches, synchronized + IO on JDK < 24, connection pool
  sizing), Quarkus @RunOnVirtualThread and Spring's switch in brief, how to measure. Lab: migrate a
  small QuoteService from a fixed pool to virtual threads with a semaphore-guarded fake DB pool.
