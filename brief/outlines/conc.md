# Track: conc, "Threads and the bugs they cause" (lab: labs/concurrency, package workbench.concurrency.lNN)

Research notes: java_concurrency_and_jmm.md (its demo outcomes were measured on JDK 21; reuse them).
conc-03 already exists (it is the golden lesson). Do NOT rewrite it. Write the other 12 lessons and
the track file, and keep them consistent with conc-03: it promises that lesson 4 covers synchronized
and lesson 8 shows how atomics work. Labs in Java; add a Kotlin `compare` where Kotlin differs
(@Synchronized, synchronized(lock) {}, @Volatile, thread {} builder, no checked InterruptedException).
Use the interleaving `sim` in lessons where stepping threads by hand teaches (conc-04 locks, conc-06 deadlock).
Machines running the tests are loaded (several builds at once), so never assert tight timings.

Lessons:
- conc-01 Threads from zero: process vs thread, cores, concurrency vs parallelism, what a thread
  costs, Thread and Runnable, start vs run, main thread ending vs other threads, Kotlin `thread {}`.
  Lab: start N workers that each process a slice of a list and combine results after join.
- conc-02 A thread's life: the six states (measured in notes), join, sleep, interrupt and the
  interruption protocol (flag cleared on InterruptedException, restore it), daemon threads,
  Thread.stop removed in JDK 26 (notes). Figure: the state diagram. Lab: an interruptible worker.
- conc-04 synchronized and intrinsic locks: monitors, mutual exclusion plus visibility, reentrancy,
  what to lock on (private final lock object; never boxed Integer or String literals), keep critical
  sections short, never call alien code while holding a lock, Kotlin @Synchronized. sim with lock/unlock.
- conc-05 wait, notify and guarded blocks: the condition-wait idiom in a while loop, spurious wakeups,
  notify vs notifyAll, a bounded buffer by hand. Lab: bounded buffer with wait/notifyAll.
- conc-06 Deadlock, livelock and starvation: the four conditions (one card each), lock ordering,
  tryLock with timeout, diagnosing with jcmd Thread.print / jstack ("Found one Java-level deadlock",
  measured in notes), JSON thread dumps. sim showing AB/BA deadlock. Lab: fix a transfer deadlock by ordering locks.
- conc-07 Explicit locks: ReentrantLock (tryLock, lockInterruptibly, fairness), Condition (two
  conditions for a bounded buffer), ReadWriteLock and why upgrade deadlocks, StampedLock optimistic
  reads in brief. Lab: rewrite the bounded buffer with Lock + two Conditions; a read-mostly cache.
- conc-08 Atomics and compare-and-set: AtomicInteger, the CAS retry loop, updateAndGet, LongAdder vs
  AtomicLong under contention, AtomicReference, ABA in brief. Lab: a lock-free max tracker and a
  CAS-based stack (Treiber).
- conc-09 Concurrent collections: ConcurrentHashMap (compute/merge/computeIfAbsent semantics, the
  recursive-update IllegalStateException from notes, no null keys/values, weakly consistent iteration),
  CopyOnWriteArrayList, the BlockingQueue family, ConcurrentModificationException vs concurrency.
- conc-10 Synchronizers: CountDownLatch, CyclicBarrier, Semaphore (connection limit), Phaser in brief,
  Exchanger in one line. Lab: rate-limit concurrent calls with a Semaphore; a barrier-based simulation step.
- conc-11 Don't share: immutability (records, final fields, defensive copies), thread confinement,
  stack confinement, ThreadLocal (and its leak in pools), ownership hand-off through queues.
- conc-12 Classic problems: producer-consumer with BlockingQueue and poison pills, dining philosophers
  (deadlock and fixes), readers-writers. Lab: implement two of the three with tests.
- conc-13 Testing and debugging concurrent code: stress tests with a start latch, repeating tests,
  timeouts, jcstress (0.16, Maven archetype per notes; outcomes and how to read results),
  thread dumps, JFR events. Lab: write a stress test that catches a provided racy class, then fix it.
