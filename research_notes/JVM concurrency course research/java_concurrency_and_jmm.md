# Core Java Concurrency and the Java Memory Model: state as of October 2026 (JDK 21 to JDK 27)

> **How this file was researched (read first).** The session's network policy blocked `docs.oracle.com`, `shipilev.net` and most other hosts; `github.com` was reachable. So the primary sources here are:
> 1. **OpenJDK source at each GA tag** (`jdk-21-ga` ... `jdk-27-ga`) and **OpenJDK commit history**, fetched with git from github.com/openjdk/jdk. Javadoc quotes below are taken from the source at the tag named.
> 2. **The jcstress repository** (README fetched; samples read with git).
> 3. **Demos run locally on OpenJDK 21.0.12.1** (the only JDK installed in the sandbox). These are labelled "[Local run, JDK 21]".
> 4. A few web-search results (labelled "search result, page not opened").
>
> **JLS chapter 17 could not be fetched.** The JLS wording below comes from training knowledge of the text. Its substance has been unchanged since JSR-133 (Java 5). Every such quote is marked **[JLS, not fetched]**. Writers must check those quotes against https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html before publishing. The j.u.c package Javadoc (verified, quoted below) restates the derived happens-before rules and can be cited safely instead.
>
> Release facts. JDK 21 is the previous LTS. JDK 25 is the current LTS (`jdk-25-ga`). JDK 26 is tagged `jdk-26-ga`. JDK 27 has shipped: the `jdk-27-ga` tag exists in github.com/openjdk/jdk, verified with git ls-remote on 2026-10-30.

---

## Q1. What exactly do the JLS chapter 17 happens-before rules say, and which ones does a working engineer need? (Precise wording and canonical examples)

### Takeaway
A write is guaranteed visible to a read in another thread only when the write happens-before the read. Working engineers need six edges: program order, monitor unlock→lock, volatile write→read, Thread.start, Thread termination→join/isAlive, and interrupt. Add transitivity, and the j.u.c "release→acquire" extensions (concurrent collections, executors, futures, latches, barriers). Data-race-free programs get sequential consistency (the DRF-SC guarantee). Anything racy can show reordering, staleness that never ends, and, for 64-bit non-volatile values, tearing.

### Cited Findings

**A. Verified restatement (j.u.c package Javadoc, JDK 25 GA; cite this when possible).** Quoted from `java/util/concurrent/package-info.java`, section "Memory Consistency Properties" — [package-info.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java):
- "Chapter 17 of The Java Language Specification defines the happens-before relation on memory operations such as reads and writes of shared variables. The results of a write by one thread are guaranteed to be visible to a read by another thread only if the write operation happens-before the read operation. The synchronized and volatile constructs, as well as the Thread.start() and Thread.join() methods, can form happens-before relationships. In particular:"
  - "Each action in a thread happens-before every action in that thread that comes later in the program's order."
  - "An unlock (synchronized block or method exit) of a monitor happens-before every subsequent lock (synchronized block or method entry) of that same monitor. And because the happens-before relation is transitive, all actions of a thread prior to unlocking happen-before all actions subsequent to any thread locking that monitor."
  - "A write to a volatile field happens-before every subsequent read of that same field. Writes and reads of volatile fields have similar memory consistency effects as entering and exiting monitors, but do not entail mutual exclusion locking."
  - "A call to start on a thread happens-before any action in the started thread."
  - "All actions in a thread happen-before any other thread successfully returns from a join on that thread."
- j.u.c extensions (same source, verbatim): "Actions in a thread prior to placing an object into any concurrent collection happen-before actions subsequent to the access or removal of that element from the collection in another thread." / "Actions in a thread prior to the submission of a Runnable to an Executor happen-before its execution begins. Similarly for Callables submitted to an ExecutorService." / "Actions taken by the asynchronous computation represented by a Future happen-before actions subsequent to the retrieval of the result via Future.get() in another thread." / "Actions prior to "releasing" synchronizer methods such as Lock.unlock, Semaphore.release, and CountDownLatch.countDown happen-before actions subsequent to a successful "acquiring" method such as Lock.lock, Semaphore.acquire, Condition.await, and CountDownLatch.await on the same synchronizer object in another thread." / Exchanger: "actions prior to the exchange() in each thread happen-before those subsequent to the corresponding exchange() in another thread." / "Actions prior to calling CyclicBarrier.await and Phaser.awaitAdvance (as well as its variants) happen-before actions performed by the barrier action, and actions performed by the barrier action happen-before actions subsequent to a successful return from the corresponding await in other threads." — [package-info.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java)

**B. JLS §17.4.4 synchronizes-with (wording from training knowledge; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)).**
- "An unlock action on monitor m synchronizes-with all subsequent lock actions on m (where "subsequent" is defined according to the synchronization order)."
- "A write to a volatile variable v (§8.3.1.4) synchronizes-with all subsequent reads of v by any thread (where "subsequent" is defined according to the synchronization order)."
- "An action that starts a thread synchronizes-with the first action in the thread it starts."
- "The write of the default value (zero, false, or null) to each variable synchronizes-with the first action in every thread." (Followed by the note that conceptually every object is created at the start of the program with its default values.)
- "The final action in a thread T1 synchronizes-with any action in another thread T2 that detects that T1 has terminated." (T2 may do this with `T1.isAlive()` or `T1.join()`.)
- "If thread T1 interrupts thread T2, the interrupt by T1 synchronizes-with any point where any other thread (including T2) determines that T2 has been interrupted (by having an InterruptedException thrown or by invoking Thread.interrupted or Thread.isInterrupted)."
- "The source of a synchronizes-with edge is called a release, and the destination is called an acquire."

**C. JLS §17.4.5 happens-before order (training knowledge; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)).**
- "Two actions can be ordered by a happens-before relationship. If one action happens-before another, then the first is visible to and ordered before the second."
- "If we have two actions x and y, we write hb(x, y) to indicate that x happens-before y."
  - "If x and y are actions of the same thread and x comes before y in program order, then hb(x, y)."
  - "There is a happens-before edge from the end of a constructor of an object to the start of a finalizer (§12.6) for that object."
  - "If an action x synchronizes-with a following action y, then we also have hb(x, y)."
  - "If hb(x, y) and hb(y, z), then hb(x, z)."
- "The wait methods of class Object (§17.2.1) have lock and unlock actions associated with them; their happens-before relationships are defined by these associated actions."
- "It should be noted that the presence of a happens-before relationship between two actions does not necessarily imply that they have to take place in that order in an implementation. If the reordering produces results consistent with a legal execution, it is not illegal."
- Derived list ("It follows from the above definitions that:"): unlock on a monitor happens-before every subsequent lock on that monitor; a write to a volatile field happens-before every subsequent read of that field; `start()` happens-before any actions in the started thread; all actions in a thread happen-before any other thread successfully returns from `join()` on that thread; "The default initialization of any object happens-before any other actions (other than default-writes) of a program."
- Data race and DRF: "When a program contains two conflicting accesses (§17.4.1) that are not ordered by a happens-before relationship, it is said to contain a data race." §17.4.1: two accesses to the same variable "are said to be conflicting if at least one of the accesses is a write." "A program is correctly synchronized if and only if all sequentially consistent executions are free of data races." "If a program is correctly synchronized, then all executions of the program will appear to be sequentially consistent (§17.4.3)."

**D. Canonical examples.**
- *Stop-flag loop that never ends.* JLS §17.3 example (training; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)): `while (!this.done) Thread.sleep(1000);` with non-volatile `done`. "the compiler is free to read the field this.done just once, and reuse the cached value in each execution of the loop. This would mean that the loop would never terminate, even if another thread changed the value of this.done." Also: "neither Thread.sleep nor Thread.yield have any synchronization semantics."
  - **Reproduced:** a `static boolean stop; while (!stop) { i++; }` worker was still alive 4 s after main set `stop = true` (JIT enabled). With `-Xint` (interpreter only) the same program terminated: "worker saw stop, i=144715786". So the hang is a compiler effect (the read is hoisted out of the loop), not a cache-coherence effect — [Local run, JDK 21.0.12.1, this session; source in Teaching notes].
  - jcstress `BasicJMM_04_Progress`: `PlainSpin` (plain `boolean ready; while (!ready);`) declares outcome STALE = `ACCEPTABLE_INTERESTING` ("Test is stuck"). `VolatileSpin` records "TERMINATED 17,882 100.0%" and STALE 0, with the comment "Making the field "volatile" is the surefire way to achieve progress guarantees. All volatile writes are eventually visible, so the loop eventually terminates." `OpaqueSpin` declares STALE = `FORBIDDEN`, so opaque mode already guarantees progress — [jcstress BasicJMM_04_Progress](https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_04_Progress.java)
- *Reordering example.* JLS Example 17.4-1, "Surprising results caused by statement reordering" (training; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)). Initially `A == B == 0`. Thread 1: `r2 = A; B = 1;` Thread 2: `r1 = B; A = 2;`. The result `r2 == 2 && r1 == 1` "may appear" impossible, but a compiler may reorder Thread 1 to `B = 1; r2 = A;`, which produces it.
  - jcstress `BasicJMM_06_Causality`: for two plain variables the JMM allows the reader to see `y` but not `x`. The sample's recorded run shows outcome "1, 0" ("Seeing $y, but not $x!") at 5,559,858 samples (0.09%) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- *DCL broken without volatile.* jcstress `Singleton_07_BrokenNonVolatileDCL` uses `private T instance; // specifically non-volatile`, and the comment says: "A very common antipattern is omitting `volatile` from the instance field... this breaks safe publication guarantees, as the read of instance on fast path has no memory ordering at all." Fixed variants exist as samples `Singleton_05_DCL`, `Singleton_06_AcquireReleaseDCL`, `Singleton_08_FinalWrapper` and `Singleton_09_Holder` — [Singleton_07 source](https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/primitives/singletons/Singleton_07_BrokenNonVolatileDCL.java)

**E. Final fields (JLS §17.5; training; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)).**
- "A thread that can only see a reference to an object after that object has been completely initialized is guaranteed to see the correctly initialized values for that object's final fields."
- Usage model: "Set the final fields for an object in that object's constructor; and do not write a reference to the object being constructed in a place where another thread can see it before the object's constructor is finished."
- Example 17.5-1 `FinalFieldExample`: `final int x; int y; static FinalFieldExample f;` The constructor sets `x = 3; y = 4;`. The reader does `if (f != null) { int i = f.x; /* guaranteed to see 3 */ int j = f.y; /* could see 0 */ }`.
- jcstress has `BasicJMM_08_Finals` and `AdvancedJMM_13_VolatileVsFinal` samples (file names verified) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- **JDK 26 change relevant to §17.5.3 (reflective final-field mutation):** JEP 500 "Prepare to Make Final Mean Final" is implemented in JDK 26 (commit subject "8353835: Implement JEP 500: Prepare to Make Final Mean Final", in `jdk-25-ga..jdk-26-ga`) — [OpenJDK git history](https://github.com/openjdk/jdk). By default JDK 26 warns when deep reflection mutates a final field, and a future release is planned to throw. Opt-in flag per the JEP: `--enable-final-field-mutation=ALL-UNNAMED` — [JEP 500 (search result, page not opened)](https://openjdk.org/jeps/500). JDK 27 adds "8372696: Allow boot classes to explicitly opt-in for final field trusting" — [OpenJDK git history](https://github.com/openjdk/jdk). JDK 25 removed j.u.c's own use: "8355369: Remove setAccessible usage for setting final fields in java.util.concurrent" — [OpenJDK git history](https://github.com/openjdk/jdk)

**F. long/double tearing (JLS §17.7; training; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)).** "a single write to a non-volatile long or double value is treated as two separate writes: one to each 32-bit half." "Writes and reads of volatile long and double values are always atomic." "Writes to and reads of references are always atomic."
- jcstress `BasicJMM_02_AccessAtomicity` shows tearing on x86_32: outcomes `-4294967296` (0.08%) and `4294967295` (<0.01%), labelled "violating access atomicity, but allowed". The comment notes some 32-bit VMs (for example ARMv7) use wider instructions and stay atomic — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- The VarHandle Javadoc gives the same rule for plain mode: "Plain read (get) and write (set) accesses are guaranteed to be bitwise atomic only for references and for primitive values of at most 32 bits" — [VarHandle.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/VarHandle.java). JDK 25 and 26 include "8315131: Clarify VarHandle set/get access on 32-bit platforms" — [OpenJDK git history](https://github.com/openjdk/jdk)

**G. wait/notify and spurious wakeups.**
- `Object.wait` Javadoc (JDK 25), verbatim: "A thread can wake up without being notified, interrupted, or timing out, a so-called spurious wakeup. While this will rarely occur in practice, applications must guard against it by testing for the condition that should have caused the thread to be awakened, and continuing to wait if the condition is not satisfied." It then points to "section 14.2, "Condition Queues," in Brian Goetz and others' Java Concurrency in Practice" — [Object.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java)
- `Condition` Javadoc: "When waiting upon a Condition, a "spurious wakeup" is permitted to occur", and each `await` variant lists "A "spurious wakeup" occurs" as a wake reason — [Condition.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/Condition.java)
- JLS §17.2.1 (training; [JLS, not fetched](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)): implementations "are permitted, although not encouraged, to perform "spurious wake-ups"", and this "necessitates the Java coding practice of using wait only within loops that terminate only when some logical condition that the thread is waiting for holds." §17.1: the language "does not prevent, nor require detection of, deadlock conditions."
- JVM bug fixed in JDK 26: "8369944: Notification can be lost due to interrupt in Object.wait" — [OpenJDK git history](https://github.com/openjdk/jdk) (commit subject only; details not read).

**H. VarHandle access modes (JDK 9+; Javadoc text from JDK 25 GA).** Verbatim: "Access modes control atomicity and consistency properties. Plain read (get) and write (set) accesses are guaranteed to be bitwise atomic only for references and for primitive values of at most 32 bits, and impose no observable ordering constraints with respect to threads other than the executing thread. Opaque operations are bitwise atomic and coherently ordered with respect to accesses to the same variable. In addition to obeying Opaque properties, Acquire mode reads and their subsequent accesses are ordered after matching Release mode writes and their previous accesses. In addition to obeying Acquire and Release properties, all Volatile operations are totally ordered with respect to each other." — [VarHandle.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/VarHandle.java)
- Read modes are `get`, `getVolatile`, `getAcquire` and `getOpaque`, with matching `set*` modes. The Javadoc maps them to C/C++11: volatile is "compatible with memory_order_seq_cst", acquire with "memory_order_acquire", and release with "memory_order_release". The fences `fullFence`, `acquireFence` and `releaseFence` are documented as `atomic_thread_fence(memory_order_seq_cst / _acquire / _release)` — [VarHandle.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/VarHandle.java)
- jcstress shows the boundaries: `AdvancedJMM_09/10/11/12_Wrong{Release,ListRelease,Acquire,AcquireRelease}Order`, `AdvancedJMM_14_SynchronizedAreNotFences`, `AdvancedJMM_15_VolatilesAreNotFences`, `AdvancedJMM_02_MultiCopyAtomic`, and `RMW_05..08_{Acquire,Release}On{Success,Failure}` (file names verified) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

### Inferences
- Rules to teach first: (1) program order, (2) unlock→lock on the *same* monitor, (3) volatile write→read of the *same* variable, (4) start, (5) join/isAlive, (6) interrupt. Then transitivity, then the j.u.c extensions. The finalizer edge and the default-value write are trivia for this course.
- The "same monitor / same variable" condition is the most-tested idea. A volatile write to `a` followed by a volatile read of `b` gives no edge. `synchronized (new Object())` is a no-op for visibility between threads.
- Teach DRF-SC as the contract: "if you have no data races (every conflicting pair is ordered by hb), you can reason as if execution were interleaved; otherwise all bets are off, except final fields and access atomicity."
- For the VarHandle modes, a reasonable classroom ladder is: plain (no inter-thread guarantees, possible tearing for long/double) < opaque (atomic, coherent per variable, eventual progress, no ordering of other variables) < acquire/release (one-way message passing of everything before the release) < volatile (also a single total order, which forbids the store-buffering/Dekker outcome).

### Gaps
- **JLS text not verified in this session** (docs.oracle.com blocked). All "[JLS, not fetched]" quotes need a check against the SE 25 JLS. Section numbers (17.2.1, 17.3, 17.4.1, 17.4.3, 17.4.4, 17.4.5, 17.5, 17.5.3, 17.7) and example numbers (17.4-1, 17.5-1) are from memory.
- Shipilëv's "Java Memory Model Pragmatics", "Close Encounters of The Java Memory Model Kind" and "Safe Publication and Safe Initialization in Java", and Doug Lea's "Using JDK 9 Memory Order Modes", could not be fetched (shipilev.net blocked; gee.cs.oswego.edu not attempted after two hosts failed). Their contents are not summarized here as verified facts.

---

## Q2. What changed in these areas from JDK 21 to JDK 27?

### Takeaway
The core JMM and the j.u.c APIs did not change. The changes are removals of unsafe Thread APIs, better observability, virtual-thread and monitor internals, preview APIs, and final fields:
- **Removals:** `countStackFrames` (22), `suspend`/`resume` plus `ThreadGroup.stop` (23), and `Thread.stop` (26).
- **Observability:** richer JSON thread dumps (25–27), new jcmd `Thread.vthread_*` commands (24), new JFR monitor events (25).
- **Virtual threads and monitors:** `synchronized` no longer pins virtual threads (24). LockingMode was deprecated (24) and its code removed (26). The ObjectMonitorTable is on by default and compact object headers are the default (27).
- **APIs:** ScopedValue is final (25). StructuredTaskScope is still preview (7th preview in 27).
- **Final fields:** reflective mutation of final fields now warns (26).

### Cited Findings

**Thread / ThreadGroup API (diffs of public signatures in `Thread.java`/`ThreadGroup.java` between GA tags)** — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java), [OpenJDK git history](https://github.com/openjdk/jdk)
| JDK | Change | Evidence |
|---|---|---|
| 21 (baseline) | Present: `ofPlatform()`, `ofVirtual()`, `isVirtual()`, `threadId()`, `sleep(Duration)`, `join(Duration)`, `onSpinWait()`; `stop()`, `suspend()`, `resume()`, `countStackFrames()` still declared | `javap java.lang.Thread` [Local run, JDK 21] |
| 22 | `Thread.countStackFrames()` removed | commit "8309196: Remove Thread.countStackFrames"; signature diff 21→22 |
| 23 | `Thread.suspend()/resume()` and `ThreadGroup.suspend()/resume()/stop()` removed | "8320532: Remove Thread/ThreadGroup suspend/resume", "8320786: Remove ThreadGroup.stop"; signature diffs 22→23 |
| 26 | `Thread.stop()` removed | "8368226: Remove Thread.stop"; `void stop()` present in 25 source, absent in 26/27 |
| 27 | Still deprecated, not removed: `checkAccess()` `@Deprecated(since="17", forRemoval=true)` (now an empty body `{ }`); `getId()` `@Deprecated(since="19")` (use `threadId()`) | Thread.java @ jdk-27-ga |
- Thread.stop history (search result, page not opened): deprecated in 1.2, deprecated for removal in 18, re-specified in JDK 20 to throw `UnsupportedOperationException` unconditionally, removed in 26. Code compiled against older releases that calls it gets `NoSuchMethodError` on JDK 26+ — [JDK-8368370 release note (search result)](https://bugs.openjdk.org/browse/JDK-8368370)
- Security Manager permanently disabled in JDK 24 (commit "8338411: Implement JEP 486: Permanently Disable the Security Manager") — [OpenJDK git history](https://github.com/openjdk/jdk). This is why `checkAccess()` is now a no-op.
- Thread Javadoc gained a "Thread Interruption" section (`id="thread-interruption"`) in JDK 26. It is present in the 26 and 27 sources, absent in 25. It says: "Code that catches InterruptedException should rethrow the exception, or restore the current thread's interrupted status, with Thread.currentThread().interrupt(), before continuing normally or handling it by throwing another type of exception." It also says code that wraps the exception as a cause or suppressed exception "should also restore the interrupted status before throwing the exception." — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)
- `Thread.interrupt()` Javadoc (JDK 27) has an implNote: "In the JDK Reference Implementation, interruption of a thread that is not alive still records that the interrupt request was made and will report it via interrupted() and isInterrupted()." — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)
- JDK 22: "8309545: Thread.interrupted from virtual thread needlessly resets interrupt status" — [OpenJDK git history](https://github.com/openjdk/jdk)

**Thread dumps: jcmd and JSON format**
- JDK 21 baseline (verified by running it): `jcmd <pid> help Thread.dump_to_file` prints "Dump threads, with stack traces, to a file in plain text or JSON format." with options `-overwrite` (BOOLEAN, false) and `-format` ("plain" or "json", default plain), plus a required `<filepath>`. `Thread.print` has `-l` "print java.util.concurrent locks" and `-e` "print extended thread information". In JDK 21 each JSON thread entry holds **only `tid`, `name` and `stack`**, grouped in `threadContainers` with `processId`, `time` and `runtimeVersion` — [Local run, JDK 21.0.12.1]
- JDK 24: new commands **`Thread.vthread_scheduler`** ("Print the virtual thread scheduler, and the delayed task schedulers that support virtual threads doing timed operations.") and **`Thread.vthread_pollers`** ("Print the I/O pollers that support virtual threads doing blocking network I/O operations.") — commit "8337199"; present in diagnosticCommand.hpp from 24 through 27 — [diagnosticCommand.hpp @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp). Also in 24: jcmd accepts `%p` in output filenames, replaced by the PID ("8334492"); the HotSpot thread dump (`Thread.print`/jstack) now includes **mounted** virtual threads ("8330846: Add stacks of mounted virtual threads to the HotSpot thread dump"). The JDK 27 `Thread.print` description reads: "Print all platform threads, and mounted virtual threads, with stack traces. The Thread.dump_to_file command will print all threads to a file." — [diagnosticCommand.hpp @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp), [OpenJDK git history](https://github.com/openjdk/jdk)
- JDK 25: "8356870: HotSpotDiagnosticMXBean.dumpThreads and jcmd Thread.dump_to_file updates" and "8357650: ThreadSnapshot to take snapshot of thread for thread dumps". The JDK 25 JSON schema (`threadDump.schema.json`) and `ThreadDumper` add, per thread, **`state`, `parkBlocker`, `blockedOn`, `waitingOn`, `monitorsOwned` (with `depth` and `locks`), `owner`, `carrier` and `virtual`**, plus `threadCount` per container — [threadDump.schema.json @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.schema.json), [ThreadDumper.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/ThreadDumper.java). Also "8356222: Thread.print command reports waiting on the Class initialization monitor for both carrier and virtual threads" — [OpenJDK git history](https://github.com/openjdk/jdk)
- JDK 26: "8365057: Add support for java.util.concurrent lock information to Thread.dump_to_file" and "8364106: Include java.runtime.version in thread dump output" — [OpenJDK git history](https://github.com/openjdk/jdk)
- JDK 27: the JSON writer adds a **`formatVersion`** key ([ThreadDumper.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/jdk/internal/vm/ThreadDumper.java)), and "8381002: Thread dump should convert longs to json numbers if possible" ([OpenJDK git history](https://github.com/openjdk/jdk)). The separate `threadDump.schema.json` file is gone from the 27 tree; the format is documented in `doc-files/threadDump.html` instead — [threadDump.html @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.html). Also "8357439: Add bash autocompletion for jcmd" — [OpenJDK git history](https://github.com/openjdk/jdk)
- `HotSpotDiagnosticMXBean.dumpThreads(String outputFile, ThreadDumpFormat format)` is the programmatic equivalent. In JDK 25 its Javadoc points to `threadDump.schema.json` for the JSON format and warns that the output may "include output for some or all virtual threads" — [HotSpotDiagnosticMXBean.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/HotSpotDiagnosticMXBean.java)

**JFR events (from `src/hotspot/share/jfr/metadata/metadata.xml` at each tag)** — [metadata.xml @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml), [metadata.xml @ jdk-21-ga](https://github.com/openjdk/jdk/blob/jdk-21-ga/src/hotspot/share/jfr/metadata/metadata.xml)
- Native thread and lock events in JDK 21: `JavaMonitorEnter`, `JavaMonitorWait`, `JavaMonitorInflate`, `ThreadPark`, `ThreadStart`, `ThreadEnd`, `ThreadDump`, `ThreadCPULoad`, `JavaThreadStatistics`, `ThreadContextSwitchRate`, `ThreadAllocationStatistics`, and the Safepoint* events.
- **JDK 25 adds `JavaMonitorDeflate`, `JavaMonitorStatistics`** ("8351142: Add JFR monitor deflation and statistics events") **and `JavaMonitorNotify`** ("8351187: Add JFR monitor notification event"). It also makes "JavaMonitorInflate event ... default to no threshold and be disabled" (8351146). None of these is in the 24 metadata. JDK 25 also adds `CPUTimeSample`/`CPUTimeSamplesLost` (JEP 509 JFR CPU-Time Profiling), `MethodTiming`/`MethodTrace` (JEP 520) and `SafepointLatency` (with JEP 518 cooperative sampling) — [OpenJDK git history](https://github.com/openjdk/jdk)
- `VirtualThreadPinned` is in the VM metadata from JDK 24 on, with fields `blockingOperation`, `pinnedReason` and `carrierThread` — [metadata.xml @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml). JDK 25 fix: "8346120: VirtualThreadPinned event recorded for Object.wait may have wrong duration or may record second event" — [OpenJDK git history](https://github.com/openjdk/jdk)
- Event fields useful for lessons (JDK 27): `JavaMonitorEnter` ("Java Monitor Blocked") has `monitorClass`, `previousOwner`, `address`. `JavaMonitorWait` has `monitorClass`, `notifier`, `timeout`, `timedOut` — [metadata.xml @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml)
- **No JFR event in metadata.xml is named "Deadlock"** (searched across 21–27). Deadlock detection is done with thread dumps (`Thread.print` / jstack) or `ThreadMXBean` — [metadata.xml @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml)

**Virtual threads, monitors and locking internals** — [OpenJDK git history](https://github.com/openjdk/jdk)
- JDK 24: "8338383: Implement JEP 491: Synchronize Virtual Threads without Pinning". JDK 24 also adds "8338890: Add monitoring/management interface for the virtual thread scheduler".
- LockingMode: the default became LM_LIGHTWEIGHT in JDK 23 ("8319251: [REDO] Change LockingMode default from LM_LEGACY to LM_LIGHTWEIGHT"). It was deprecated in JDK 24 ("8334299: Deprecate LockingMode option, along with LM_LEGACY and LM_MONITOR"), and its code was removed in JDK 26 ("8365190: Remove LockingMode related code from share").
- Object monitor table: "8315884: New Object to ObjectMonitor mapping" (JDK 24) and "8379782: Implement Object Monitor Table enabled by default" (JDK 27).
- Compact object headers: JEP 450 experimental (24), JEP 519 (25), "8360700: Implement JEP 534: Compact Object Headers by Default" (27).

**Preview / final APIs** — [OpenJDK git history](https://github.com/openjdk/jdk), [StructuredTaskScope.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java), [ScopedValue.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/ScopedValue.java)
- Scoped Values: 2nd preview in 22 (8321223), 3rd preview in 23 (8331189), **final in JDK 25** ("8355022: Implement JEP 506: Scoped Values"; no `@PreviewFeature` in the 25 `ScopedValue.java`).
- Structured Concurrency: 3rd preview in 23 (8332064); JEP 505 5th preview in 25 (8342486); JEP 525 6th preview in 26 (8367857); **JEP 533 7th preview in 27** (8380109). The 27 source is `public sealed interface StructuredTaskScope<T, R, R_X extends Throwable>` with a static `open()` factory. Also in 27: "8373427: StructuredTaskScope::join not clear if called with interrupted status set".
- Stable Values / Lazy Constants (lazy-init alternative to DCL): JEP 502 preview in 25 (8351565), JEP 526 "Lazy Constants (Second Preview)" in 26 (8366178), JEP 531 3rd preview in 27 (8376811).

**j.u.c library changes (commit subjects)** — [OpenJDK git history](https://github.com/openjdk/jdk)
- 23: "8278255: Add more warning text in ReentrantLock and ReentrantReadWriteLock"; "8322149: ConcurrentHashMap smarter presizing for copy constructor and putAll".
- 24: "8336384: AbstractQueuedSynchronizer.acquire should cancel acquire when failing due to a LinkageError or other errors"; "8332842: Optimize empty CopyOnWriteArrayList allocations".
- 26: "8359919: Minor java.util.concurrent doc improvements" (bundled with "8187775: AtomicReferenceFieldUpdater does not support static fields"); "8365058: Enhance CopyOnWriteArraySet".
- 27: "8378354: Faulty assertion in checkInvariants method of ConcurrentHashMap".

### Inferences
- For the course, nothing about happens-before, `volatile`, `synchronized` semantics, CHM, atomics or the synchronizers changed between 21 and 27. Lessons written against JDK 25 stay valid on 26 and 27.
- Lessons that mention `Thread.stop`, `suspend`, `resume` or `countStackFrames` should present them as removed (version-tagged), not deprecated. Interruption is the only cooperative cancellation mechanism.
- The thread-dump lesson should show both formats: `jcmd <pid> Thread.print -l` (human-readable, deadlock detection) and `jcmd <pid> Thread.dump_to_file -format=json <file>` (machine-readable). Tell learners that JSON fields such as `state`, `blockedOn` and `owner` need JDK 25+, and that the JSON on JDK 21 has stacks only.
- JDK 24's JEP 491 changes the old advice "replace synchronized with ReentrantLock for virtual threads". On JDK 24+ that advice is mostly obsolete. The `pinnedReason` field in `jdk.VirtualThreadPinned` exists because pinning still happens in some cases.

### Gaps
- Exact JDK 27 GA date: secondary sources conflict, September 15, 2026 per [InfoQ (search result)](https://infoq.com/news/2026/08/java-27-so-far) and September 14 per lavx.hu (search result). The `jdk-27-ga` tag is verified.
- JDK 21's own virtual-thread facts (JEP 444, `jdk.tracePinnedThreads`, the JDK 21 Java-level `jdk.VirtualThreadPinned` event) were not re-verified; the commit history fetched starts after the JDK 21 GA tag.
- JEP 500 command-line flags (`--enable-final-field-mutation`, `--illegal-final-field-mutation=...`) come from search snippets that disagree with each other. Verify against `java --help-extra` on JDK 26.
- Default JFR thresholds (for example, JavaMonitorEnter's 20 ms) were not verified; they live in `default.jfc`/`profile.jfc`, which were not fetched.

---

## Q3. What are the most common misconceptions and real production bugs, per topic?

### Takeaway
The recurring failure modes are:
- treating visibility as atomicity (`volatile` with `count++`);
- treating thread-safe collections as making compound operations atomic (CHM check-then-act);
- locking on shared or interned objects (boxed `Integer`, `String` literals);
- calling foreign ("alien") code while holding a lock;
- swallowing interrupts;
- missing `volatile` in DCL;
- misusing `wait`/`notify` (no loop, or `notify` where `notifyAll` is needed).

The JDK's own commit log has real instances of several of these, which make good case studies.

### Cited Findings

**Races and atomicity**
- *"volatile makes count++ atomic"*: false. 4 threads × 1,000,000 `v++` on a `static volatile int` ended at **3,681,731** (expected 4,000,000). Plain `int` ended at 3,997,394; `AtomicInteger.incrementAndGet` and `LongAdder.increment` gave exactly 4,000,000. Numbers vary per run — [Local run, JDK 21]
- jcstress `RaceCondition_01_RMW`: `private volatile int v = 200;` with two read-modify-write actors. The recorded outcomes include "actors conflicted, actor2 won the race" at 5.70% and "actor1 won the race" at 5.52%. The fixed version shows those outcomes at 0 (Forbidden). `RaceCondition_02_CheckThenReact` covers check-then-act — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- jcstress `API_01_Simple`: two actors do `r.r1 = ++v` and `r.r2 = ++v` on plain `int v`. Outcome "1, 1" is `ACCEPTABLE_INTERESTING` ("Both actors came up with the same value: atomicity failure.") — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

**synchronized / monitors**
- *Synchronizing on a boxed Integer is fine*: false. `javac` on JDK 21 prints `warning: [synchronization] attempt to synchronize on an instance of a value-based class` for `static final Integer LOCK = 42; synchronized (LOCK) {...}`. The runtime diagnostic `-XX:DiagnoseSyncOnValueBasedClasses` is a diagnostic flag and needs `-XX:+UnlockDiagnosticVMOptions` first — [Local run, JDK 21]
- Reentrancy limit: "This lock supports a maximum of 2147483647 recursive locks by the same thread" (ReentrantLock) — [ReentrantLock.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java)
- *Holding a lock while calling alien methods* (real JDK bug, JDK 25): "8349206: j.u.l.Handler classes create deadlock risk via synchronized publish() method". JDK 23: "8238169: BasicDirectoryModel getDirectories and DoChangeContents.run can deadlock" — [OpenJDK git history](https://github.com/openjdk/jdk) (commit subjects only).

**Interruption**
- After `InterruptedException` is thrown, the flag is cleared. A waiter interrupted inside `wait()` printed `isInterrupted now=false` — [Local run, JDK 21]. The Javadoc says: "Methods that throw InterruptedException do so after first clearing the interrupted status." — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)
- Real "swallowed interrupt" bugs fixed in the JDK itself: "8339403: sun.security.ssl.StatusResponseManager.get swallows interrupt status" (24); "8339850: Restore the interrupt status in FileSystemPreferences.lockFile()" (24); "8320328: Restore interrupted flag in ImageIcon.loadImage" (23); "8323782: Race: Thread::interrupt vs. AbstractInterruptibleChannel.begin" (23); "8347274: Gatherers.mapConcurrent exhibits undesired behavior under variable delays, interruption, and finishing" (25) — [OpenJDK git history](https://github.com/openjdk/jdk)
- `interrupt()` semantics (JDK 27 Javadoc): if blocked in `wait`/`join`/`sleep`, "its interrupted status will be cleared and it will receive an InterruptedException". If blocked on an `InterruptibleChannel`, "the channel will be closed, the thread's interrupted status will be set, and the thread will receive a ClosedByInterruptException". In a `Selector`, it returns immediately with the status set. Otherwise the status is just set. — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)

**Thread states (JDK 27 Javadoc, verbatim fragments)** — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)
- NEW: "has not yet started". RUNNABLE: "executing in the Java virtual machine but it may be waiting for other resources from the operating system such as processor." BLOCKED: "waiting for a monitor lock to enter a synchronized block/method or reenter a synchronized block/method after calling Object.wait." WAITING: `Object.wait` with no timeout, `Thread.join` with no timeout, `LockSupport.park`. TIMED_WAITING: `Thread.sleep`, `Object.wait(long)`, `Thread.join(long)`, `LockSupport.parkNanos`, `LockSupport.parkUntil`. TERMINATED: "has completed execution."
- Observed with a probe program: NEW before start; WAITING inside `wait()`; TIMED_WAITING inside `sleep`; BLOCKED trying to enter a held monitor; RUNNABLE in a busy loop; TERMINATED after join — [Local run, JDK 21]
- Misconception: a thread blocked on a `ReentrantLock` shows as BLOCKED. Per the list above it is WAITING or TIMED_WAITING, because `ReentrantLock` parks through `LockSupport.park`. BLOCKED is only for monitors — [Thread.java @ jdk-27-ga](https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java)

**Deadlock diagnosis**
- `jcmd <pid> Thread.print` on a classic AB/BA deadlock prints `Found one Java-level deadlock:` and, per thread, `waiting to lock monitor 0x... (object 0x..., a java.lang.Object), which is held by "t2"`. The stacks show `- waiting to lock <0x...>` / `- locked <0x...>`, ending with `Found 1 deadlock.` — [Local run, JDK 21]
- `Thread.print -l` adds j.u.c ownable synchronizers ("print java.util.concurrent locks") — [Local run, JDK 21]. JDK 26 adds j.u.c lock info to `Thread.dump_to_file` (8365057) — [OpenJDK git history](https://github.com/openjdk/jdk)

**ReentrantLock / Condition / ReadWriteLock / StampedLock**
- ReentrantLock Javadoc (JDK 25): "It is recommended practice to always immediately follow a call to lock with a try block", with the snippet comment `lock.unlock(); // unlock() as the first statement in the finally block`. On fairness: "fairness of locks does not guarantee fairness of thread scheduling", and untimed `tryLock` does not "honor the fairness setting" — [ReentrantLock.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java)
- StampedLock (JDK 25): StampedLocks "are not reentrant, so locked bodies should not call other unknown methods that may try to re-acquire locks". `tryOptimisticRead` plus `validate`: actions "are guaranteed to happen-before those following a tryOptimisticRead only if a later validate returns true; otherwise there is no guarantee". `tryConvertToWriteLock` attempts to "upgrade" a mode — [StampedLock.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java)

**Atomics / LongAdder**
- LongAdder: "This class is usually preferable to AtomicLong when" multiple threads update a common sum. Under high contention, its throughput "is significantly higher, at the expense of higher space consumption". `sum()` "returns an accurate result" only without concurrent updates: "concurrent updates that occur while the sum is being calculated might not be incorporated" (second half of that quote from training; first half verified in source) — [LongAdder.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/LongAdder.java)
- CAS samples in jcstress: `RMW_01..12` (contended success, failure witness, acquire/release on success or failure), `Singleton_03_InefficientCAS`, `Mutex_03_SpinLock` — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

**ConcurrentHashMap (compute/merge semantics and pitfalls)** — [ConcurrentHashMap.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java)
- `computeIfAbsent` Javadoc (verbatim): "The entire method invocation is performed atomically. The supplied function is invoked exactly once per invocation of this method if the key is absent, else not at all. Some attempted update operations on this map by other threads may be blocked while computation is in progress, so the computation should be short and simple. The mapping function must not modify this map during computation." "@throws IllegalStateException if the computation detectably attempts a recursive update to this map that would otherwise never complete." If the function throws, "the mapping is left unestablished". `compute`/`computeIfPresent`/`merge` likewise say "The entire method invocation is performed atomically" and "should be short and simple".
- Recursive memoization (`fib` via `computeIfAbsent`) fails at once: CHM throws **`java.lang.IllegalStateException: Recursive update`** and HashMap throws **`java.util.ConcurrentModificationException`** — [Local run, JDK 21]. The CHM source throws `new IllegalStateException("Recursive update")` in several places — [ConcurrentHashMap.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java)
- Class Javadoc begins "Bear in mind that the results of aggregate status methods including" `size`, `isEmpty` and `containsValue`. The rest of that sentence, from training, warns these are only useful when the map is not being updated concurrently, and otherwise suit monitoring and estimation, not program control. Bulk iterators are "weakly consistent" — [ConcurrentHashMap.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java)
- jcstress `Library_01_CHM` (Multimap): `get` then `put` of a new list "Contains a nasty race on putting the list into the map". It is fixed with `putIfAbsent` (use the returned existing list) or `computeIfAbsent` — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

**CopyOnWriteArrayList** — [CopyOnWriteArrayList.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CopyOnWriteArrayList.java)
- Every mutation works "by making a fresh copy of the underlying array". "This is ordinarily too costly, but may be more efficient than alternatives when traversal operations vastly outnumber mutations". The "snapshot" iterator never throws CME, and its element-changing methods throw `UnsupportedOperationException`.

**ThreadLocal / ScopedValue**
- ThreadLocal's canonical example uses `private static final ThreadLocal<Integer> threadId` with `initialValue()`. `ThreadLocal.withInitial(Supplier)` is the factory alternative. The JDK 25 source has a `TRACE_VTHREAD_LOCALS` diagnostic for thread-locals set in virtual threads — [ThreadLocal.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/ThreadLocal.java)
- `ScopedValue` is final as of JDK 25 (JEP 506) and is the immutable, bounded-lifetime alternative — [OpenJDK git history](https://github.com/openjdk/jdk)

**Safe publication / DCL / immutability**
- Broken DCL: `Singleton_07_BrokenNonVolatileDCL` (quoted in Q1). Data-race publication of `new Object()`: jcstress `BasicJMM_01_DataRaces` declares `null` and `class java.lang.Object` acceptable and anything else FORBIDDEN — [BasicJMM_01_DataRaces](https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_01_DataRaces.java)
- Lazy-init idioms with jcstress samples: `Lazy_01_BrokenFactory`, `Lazy_02_BrokenNulls`, `Lazy_03_Basic`, `Lazy_04_BrokenOneShot`, `Lazy_05_WrapperOneShot`, `Lazy_06_FencedOneShot`; singletons `Singleton_01..10` (including `Singleton_10_ThreadLocalWitness`) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

### Inferences
- High-value "myth vs fact" pairs for lessons. Each one is backed by a runnable demo above:
  - `volatile` ≠ atomic RMW.
  - `sleep`/`yield` do not synchronize.
  - The interrupt flag is cleared on InterruptedException.
  - `ReentrantLock` waiters show WAITING, not BLOCKED.
  - CHM `size()` is an estimate under concurrent updates.
  - CHM compound operations need `compute*`/`merge`/`putIfAbsent`.
  - Recursive `computeIfAbsent` fails fast (CHM: ISE; HashMap: CME).
  - StampedLock is not reentrant.
  - `LongAdder.sum()` is not a snapshot.
- The JDK's own "Restore interrupted flag" and "swallows interrupt status" fixes are good proof for learners that this mistake happens even to JDK engineers.
- Synchronizing on `String` literals is dangerous because literals are interned and shared across unrelated code. The interning rule (JLS §3.10.5) was not re-verified here. The javac `[synchronization]` lint covers value-based classes such as `Integer`, not `String`.

### Gaps
- The CHM computeIfAbsent livelock/hang in JDK 8 (JDK-8062841, fixed by throwing ISE in JDK 9) and HashMap's infinite-loop corruption under concurrent resize in old JDKs are well-known production stories. They were not re-verified this session.
- `notify` vs `notifyAll` guidance (missed signals, "single notification" conditions per JCiP §14.2.4) is from training, not verified this session. The Object.wait Javadoc confirms JCiP §14.2 "Condition Queues" as the reference.
- **Standard facts not re-verified this session (check Javadoc before citing):**
  - BlockingQueue method table: throws (`add`/`remove`/`element`), special value (`offer`/`poll`/`peek`), blocks (`put`/`take`), times out (`offer(e,t,u)`/`poll(t,u)`). Null elements are rejected.
  - `LinkedBlockingQueue` defaults to capacity `Integer.MAX_VALUE`. `SynchronousQueue` has no capacity. `ArrayBlockingQueue` is bounded and has an optional fairness setting.
  - `CountDownLatch` is one-shot. `CyclicBarrier` is reusable, with `BrokenBarrierException`. `Semaphore` permits are not owned by a thread (a release without an acquire adds a permit). `Phaser` supports dynamic party registration.
  - `ReentrantReadWriteLock` does not allow upgrading a read lock to a write lock (the attempt deadlocks); downgrading is allowed.
  - `AtomicStampedReference`/`AtomicMarkableReference` are the ABA mitigations.

---

## Q4. What is the current state of jcstress (latest version, how to run it with Maven/Gradle, sample tests)?

### Takeaway
jcstress is still the standard OpenJDK harness. The latest **tagged release is 0.16 (tagged 2023-02-27)**. Master is `0.17-SNAPSHOT`, and its latest commit, from 2025-06-19, fixes `AdvancedJMM_15_VolatilesAreNotFences`. Use the Maven archetype; the official README documents no Gradle path. Samples are grouped into API, JMM (basic/advanced) and concurrency/primitives, and each sample file contains recorded result tables that make ready-made lesson material.

### Cited Findings
- What it is: "an experimental harness and test suite for researching the correctness of concurrency support in the JVM, class libraries, and hardware" — [jcstress README](https://github.com/openjdk/jcstress)
- Versions: git tags run up to `0.16` (0.15 tagged 2021-12-02, 0.16 tagged 2023-02-27). Master `pom.xml` is `0.17-SNAPSHOT`, and the last master commit is dated 2025-06-19 ("7904043: jcstress: AdvancedJMM_15_VolatilesAreNotFences.Fences is failing after CODETOOLS-7904033") — [jcstress repo (git)](https://github.com/openjdk/jcstress)
- JDK requirements (README): JDK 11+ to build, JDK 17+ to compile all tests, and most tests run on JDK 8+. The archetype sets `javac.target` 1.8 — [jcstress README](https://github.com/openjdk/jcstress)
- Bootstrapping a project (README, verbatim):
  ```
  mvn archetype:generate -DinteractiveMode=false -DarchetypeGroupId=org.openjdk.jcstress -DarchetypeArtifactId=jcstress-java-test-archetype -DgroupId=org.sample -DartifactId=test -Dversion=1.0
  cd test
  mvn clean verify
  java -jar target/jcstress.jar
  ```
  Libraries are on Maven Central. The README also mentions a prebuilt `jcstress.jar` at builds.shipilev.net (`java -jar jcstress.jar`, `-h` for options) — [jcstress README](https://github.com/openjdk/jcstress)
- Running the repo's own suites (README): `mvn clean verify` then `java -jar tests-all/target/jcstress.jar`. Quick mode: `java -jar tests-all/target/jcstress.jar -m quick` ("many CIs use `-m quick`"). Custom subset: `mvn clean verify -pl tests-custom -am`. Samples: `mvn clean verify -pl jcstress-samples -am` then `java -jar jcstress-samples/target/jcstress.jar -t <test-name>` — [jcstress README](https://github.com/openjdk/jcstress)
- Annotations and outcome model (from `API_01_Simple`): `@JCStressTest`, `@State`, `@Actor`, result holders such as `II_Result` (fields `r1`, `r2`), `@Outcome(id = "1, 2", expect = ACCEPTABLE, desc = ...)`, and `ACCEPTABLE_INTERESTING` / `FORBIDDEN`. `BasicJMM_04_Progress` uses `@Signal` (the termination mode); there are samples `API_02_Arbiters`, `API_03_Termination`, `API_04_Nesting`, `API_05_SharedMetadata` and `API_06_Descriptions` — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- Full sample inventory (file names, master):
  - **API_01–06**
  - **BasicJMM_01** DataRaces, 02 AccessAtomicity, 03 WordTearing, 04 Progress, 05 Coherence, 06 Causality, 07 Consensus, 08 Finals, 09 BenignRaces, 10 OOTA
  - **AdvancedJMM_01** SynchronizedBarriers, 02 MultiCopyAtomic, 03 NonMCA_Coherence, 04 LosingUpdates, 05 MisplacedVolatile, 06 SemiSynchronized, 07 SemiVolatile, 08 ArrayVolatility, 09–12 Wrong{Release,ListRelease,Acquire,AcquireRelease}Order, 13 VolatileVsFinal, 14 SynchronizedAreNotFences, 15 VolatilesAreNotFences
  - **Classic_01** DiningPhilosophers, 02 ProducerConsumerProblem
  - **Mutex_01** Peterson, 02 Dekker, 03 SpinLock, 04 Synchronized, 05 ReentrantLock, 06 Semaphore
  - **RaceCondition_01** RMW, 02 CheckThenReact
  - **Library_01_CHM**
  - **RMW_01–12**
  - **Lazy_01–06**
  - **Singleton_01–10**

  [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)

### Inferences
- With no release since 0.16 in Feb 2023, a course should pin `jcstress-core` 0.16 from Maven Central or build master. The samples on master (which writers will browse on GitHub) may differ slightly from the 0.16 jar. Writers should note which they used.
- Outcomes are hardware-dependent: x86 (TSO) rarely shows store-buffer and publication anomalies, while ARM/AArch64 and POWER show more. Lessons should present "INTERESTING" outcomes as *allowed*, not *guaranteed* to appear on a learner's laptop. This is supported by the samples' own per-platform tables (e.g. BasicJMM_02 x86_32 vs ARMv7).

### Gaps
- **Gradle:** the README documents no Gradle support. A community Gradle plugin exists according to training knowledge, but it was not verified (plugins.gradle.org not reachable). For Gradle users, writers should either verify a plugin or show running the archetype-built jar.
- The latest jcstress version on Maven Central could not be checked directly (repository browsing not attempted). The tag list suggests 0.16.
- The exact package paths of some samples (e.g. `API_01_Simple`, `RaceCondition_01_RMW`, `Library_01_CHM`) were not recorded. Link to the samples tree root.

---

## Q5. What are the best exercises and demos for teaching these topics?

### Takeaway
The strongest demos are small, deterministic-enough programs whose "wrong" outcome learners can actually see on a laptop:
- stop-flag hang under the JIT (gone under `-Xint`);
- `volatile` counter losing updates;
- thread-state probe;
- AB/BA deadlock read through `jcmd Thread.print`;
- recursive `computeIfAbsent` failure;
- `synchronized` on `Integer` lint;
- JSON thread dump comparison (JDK 21 vs 25+).

jcstress samples cover the anomalies that need a stress harness or weak hardware (reordering, tearing, DCL, causality), and each sample carries its own expected-results table.

### Cited Findings
- All seven local demos above ran on JDK 21.0.12.1 with the outcomes stated in Q1–Q3 — [Local run, JDK 21]
- jcstress samples with recorded result tables in their source: `BasicJMM_02_AccessAtomicity` (tearing table for x86_32), `BasicJMM_04_Progress` (VolatileSpin 100% TERMINATED), `BasicJMM_06_Causality` ("1, 0" at 0.09%), `RaceCondition_01_RMW` (about 11% conflicting outcomes with volatile; 0% after the fix) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- Classic problems as jcstress tests: `Classic_01_DiningPhilosophers`, `Classic_02_ProducerConsumerProblem`, and mutual-exclusion algorithms `Mutex_01_PetersonAlgorithm` / `Mutex_02_DekkerAlgorithm` (which fail without sequentially consistent accesses) — [jcstress samples tree](https://github.com/openjdk/jcstress/tree/master/jcstress-samples)
- JCiP §14.2 "Condition Queues" is the reference that `Object.wait`'s Javadoc itself cites — [Object.java @ jdk-25-ga](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java)

### Inferences
- See "Teaching notes" below for the concrete exercise list with expected outcomes.

### Gaps
- Shipilëv's JMM Pragmatics talk/article and JCiP listing numbers were not verified (sites blocked or not online). Writers can recommend them as further reading, but should not quote them from these notes.

---

## Teaching notes

### Misconceptions to address explicitly (with the fact that refutes each)
1. **"volatile makes `count++` atomic."** It only gives visibility and ordering. Demo: lost updates (3,681,731 / 4,000,000 in one run). Fix: `AtomicInteger`/`LongAdder`/lock.
2. **"Thread.sleep() or a println in the loop makes the flag visible."** `sleep`/`yield` have no synchronization semantics (JLS §17.3). A `println` that "fixes" it does so by accident, because `PrintStream` locks internally. Demo: the stop-flag hang.
3. **"If I see the reference, I see the object's fields."** Only `final` fields are guaranteed (JLS §17.5). Non-final fields of a racily published object may appear as defaults.
4. **"DCL is fine without volatile on x86, so it's fine."** Correctness is defined by the JMM, not your CPU. Demo: jcstress `Singleton_07`.
5. **"happens-before means 'executes earlier'."** It is a visibility and ordering guarantee between specific actions; the JLS explicitly allows reordering consistent with legal executions.
6. **"ConcurrentHashMap makes my code thread-safe."** Only single operations are atomic. `if (!map.containsKey(k)) map.put(k, v)` is a check-then-act race. Use `putIfAbsent`/`computeIfAbsent`/`merge`. `size()` is an estimate under concurrent updates.
7. **"computeIfAbsent can call back into the same map."** The Javadoc forbids it. CHM throws `IllegalStateException: Recursive update`; HashMap throws `ConcurrentModificationException`.
8. **"Any object is a fine lock."** Not boxed values (`Integer` caches -128..127 and is shared; javac warns `[synchronization]`), not `String` literals (interned), not `this` of a public class whose clients might also lock it, and not a field you later reassign.
9. **"notify() is an optimization over notifyAll()."** It is only safe when every waiter waits for the same condition and any one can proceed. Otherwise a signal can be lost.
10. **"if (cond) wait();"** Always `while (!cond) wait();`. Spurious wakeups are permitted, and the condition may change between notify and re-acquiring the monitor.
11. **"Catching InterruptedException and logging is handling it."** The flag is cleared when the exception is thrown. Restore it with `Thread.currentThread().interrupt()` or rethrow (JDK 26+ Thread Javadoc says this explicitly).
12. **"Thread.stop() is a last resort."** It was removed in JDK 26 (it threw UOE since JDK 20). Cancellation is cooperative.
13. **"A thread stuck on ReentrantLock.lock() is BLOCKED."** It is WAITING (parked). BLOCKED is only for monitors.
14. **"Fair locks give fair scheduling."** The Javadoc says not, and `tryLock()` barges.
15. **"StampedLock is a faster ReentrantReadWriteLock."** It is not reentrant, has no Conditions, and optimistic reads need `validate()` plus side-effect-free reading code.
16. **"LongAdder.sum() is exact."** It is not a snapshot under concurrent updates. Use it for statistics, not for control decisions.
17. **"CopyOnWriteArrayList is the concurrent ArrayList."** Each write copies the whole array; it is only good when reads vastly outnumber writes.
18. **"Virtual threads + synchronized = pinning."** That was true on JDK 21–23. JEP 491 (JDK 24) removed most pinning for `synchronized`.

### Analogies that work
- **Happens-before = a signed hand-off receipt.** Writes made before a *release* (unlock, volatile write, `countDown`, queue `put`) are "in the envelope". A thread sees them only if it *acquires* the same envelope (lock of the same monitor, volatile read of the same field, `await`, `take`). Different envelopes mean no guarantee.
- **Monitor = a single-occupancy room.** The entry queue is the corridor (BLOCKED). `wait()` hands back the key and moves you to the lounge (WAITING). `notify()` sends one person from the lounge back to the corridor, where they must re-acquire the key, so they must re-check the condition.
- **Plain vs opaque vs acquire/release vs volatile = notes vs bulletin board.** Plain writes are private scribbles the compiler may batch or skip. Opaque writes are pinned to the board eventually and in per-note order. Release/acquire pins a note plus everything written before it. Volatile adds one global order of all volatile notes.
- **CAS = Git push with a "remote must still be at commit X" check.** ABA: the remote went X→Y→X, so the push succeeds though history changed. The fix is a version stamp (`AtomicStampedReference`).
- **LongAdder = tally counters at several doors**, summed at closing time. Fast to increment, and approximate while doors are still open.
- **CopyOnWriteArrayList = printing a new edition for every correction.** Readers keep their edition (snapshot iterators).
- **CountDownLatch = rocket launch countdown** (one-shot). **CyclicBarrier = a tour group regrouping at each landmark** (reusable). **Semaphore = a parking lot with N spaces.** **Phaser = a relay race where runners can join or leave between legs.**
- **ThreadLocal in a pool = a locker that the next tenant inherits** unless you `remove()` it. This causes leaks and data bleeding across requests.
- **Deadlock = two cars at a one-lane bridge**, each waiting for the other to back up. Livelock is both repeatedly backing up and re-entering. Starvation is the car that never gets a turn.

### Demo programs (verified on JDK 21.0.12.1 in this session; expected outcomes)
1. **Stop-flag hang**
   ```java
   public class StopFlag { static boolean stop;
     public static void main(String[] a) throws Exception {
       Thread t = new Thread(() -> { long i = 0; while (!stop) { i++; } System.out.println("worker saw stop, i=" + i); });
       t.start(); Thread.sleep(1000); stop = true; System.out.println("main set stop=true");
       t.join(4000); System.out.println("worker alive after 4s join? " + t.isAlive()); System.exit(0); } }
   ```
   Expected: `worker alive after 4s join? true` with the JIT on. With `java -Xint StopFlag.java` it terminates (`worker saw stop, ...`, alive false). The `volatile boolean stop` version should terminate; this is guaranteed by the JMM and shown by jcstress VolatileSpin, but it was not run locally.
2. **Lost update:** 4 threads × 1M `v++` on `volatile int`, a plain `int`, `AtomicInteger` and `LongAdder`. Expected: volatile and plain come out below 4,000,000 (one run: volatile 3,681,731, plain 3,997,394); the atomic counter and LongAdder are exact. Point out that plain *can* appear "less wrong" than volatile. That is because of JIT and cache behaviour and proves nothing.
3. **Thread-state probe:** prints NEW, WAITING (in `wait()`), TIMED_WAITING (in `sleep`), BLOCKED (entering a held monitor), RUNNABLE (busy loop), TERMINATED. After interrupting the waiter, `isInterrupted()` inside the catch is **false**.
4. **AB/BA deadlock and diagnosis:** two threads lock A then B, and B then A, with a 300 ms sleep in between. `jcmd <pid> Thread.print` shows `Found one Java-level deadlock:` … `Found 1 deadlock.` (`jstack <pid>` gives the same dump; not run separately). Extension: fix it with global lock ordering, or `tryLock(timeout)` with back-off (and then discuss livelock).
5. **Recursive computeIfAbsent:** memoized `fib(30)` via `map.computeIfAbsent(n, k -> fib(k-1) + fib(k-2))`. Expected: CHM throws `IllegalStateException: Recursive update`; HashMap throws `ConcurrentModificationException`. Fix: compute outside the map, or iterate bottom-up.
6. **Lock on a boxed value:** `static final Integer LOCK = 42; synchronized (LOCK) {}`. Expected javac warning: `[synchronization] attempt to synchronize on an instance of a value-based class`. Runtime check: `-XX:+UnlockDiagnosticVMOptions -XX:DiagnoseSyncOnValueBasedClasses=2` (logs) or `=1` (fatal error). The values 1/2 come from training; the need for the unlock flag was verified.
7. **JSON thread dump across versions:** `jcmd <pid> Thread.dump_to_file -format=json /tmp/td.json`. Expected: on JDK 21 each thread has only `tid`, `name`, `stack`. On JDK 25+ there are also `state`, `blockedOn`/`waitingOn`/`parkBlocker`, `owner`, `monitorsOwned` and `virtual`. JDK 26+ adds j.u.c lock info; JDK 27 adds `formatVersion`. The file must not exist unless you pass `-overwrite`.

### Exercise ideas with expected outcomes
- **E1 (race spotting):** give a `Counter` with `synchronized increment()` but an unsynchronized `get()`. Q: is `get()` safe? Expected: no. Without the same monitor (or volatile) there is no happens-before edge, so a reader may see stale values.
- **E2 (check-then-act):** "register user if absent" with `HashMap` → `ConcurrentHashMap` → `putIfAbsent`/`computeIfAbsent`. Expected: only the last version is atomic. A jcstress version of this is `RaceCondition_02_CheckThenReact` / `Library_01_CHM`.
- **E3 (bounded buffer):** implement it with `wait`/`notifyAll`, then with `ReentrantLock` and two `Condition`s (`notFull`, `notEmpty`), then replace it with `ArrayBlockingQueue`. Expected: the `if`→`while` bug shows up with several producers and consumers. Single `notify()` with two condition kinds can stall all threads.
- **E4 (interruption hygiene):** fix a worker that does `catch (InterruptedException e) { log(e); }` inside a `while (true)` loop. Expected: after the fix, `executor.shutdownNow()` actually stops it.
- **E5 (DCL):** write a lazy singleton four ways: synchronized method, DCL with volatile, holder class idiom, enum. Explain why DCL without volatile is broken (see `Singleton_07`). Expected: everything except the non-volatile DCL is correct; the holder relies on class-initialization locking.
- **E6 (immutability):** turn a mutable `Point` into a final class with `private final` fields, defensive copies for mutable components, and no `this` escape in the constructor. Expected: it can be shared through a data race and still be seen correctly (final-field semantics).
- **E7 (atomics/ABA):** implement a Treiber stack with `AtomicReference.compareAndSet`, discuss ABA in a node-recycling variant, and fix it with `AtomicStampedReference`. Expected: in Java, GC makes ABA rare for plain object nodes, but it is real for recycled nodes or indices.
- **E8 (synchronizers):** a parallel test harness that starts N threads together (`CountDownLatch start = new CountDownLatch(1)`) and waits for all (`CountDownLatch done = new CountDownLatch(N)`). Then do iterative phases with `CyclicBarrier` and a barrier action, and dynamic participants with `Phaser`. Expected: all threads start within a short window, and the barrier action runs once per generation.
- **E9 (ThreadLocal leak):** a fixed pool of 2 threads, where a request handler sets a ThreadLocal "current user" without `remove()`. Expected: a later request on the same thread sees the previous user. Fix with `try/finally remove()`, or with `ScopedValue` on JDK 25+.
- **E10 (jcstress):** run `API_01_Simple` and `RaceCondition_01_RMW`. Expected: "1, 1" / the conflict outcomes appear (labelled Interesting). Then make the field an `AtomicInteger` and see them disappear. Run `BasicJMM_06_Causality` and `Singleton_07` on x86 and, if available, on ARM (for example Apple Silicon or Graviton), and compare. Expected: weak-memory outcomes are more frequent on ARM; they may never appear on x86.
- **E11 (JFR):** record `jcmd <pid> JFR.start duration=30s filename=c.jfr` while a contended `synchronized` hot spot runs, then `jfr print --events jdk.JavaMonitorEnter c.jfr`. Expected: events with `monitorClass` and `previousOwner`. On JDK 25+ also look at `jdk.JavaMonitorStatistics`. The `JFR.start` parameters and the `jfr` CLI syntax are from training; verify them on the target JDK.

---

## Verified URLs

Only URLs whose content was actually retrieved in this session are listed. "git" means the content was retrieved with git from that repository (clone, fetch or ls-remote). The blob URLs below are the browser addresses for the exact tag and path whose content was read through git.

**Fetched over HTTP (WebFetch)**
- https://github.com/openjdk/jcstress — jcstress README: purpose, build and run commands, Maven archetype command, JDK requirements, sample groups.

**Retrieved via git from github.com**
- https://github.com/openjdk/jdk — tags `jdk-21-ga` … `jdk-27-ga` (confirms JDK 27 GA is tagged), and commit history from 2023-03 to `jdk-27-ga`, used for every "commit NNNNNNN" attribution (the release is the GA-tag range the commit falls in).
- https://github.com/openjdk/jdk25u, https://github.com/openjdk/jdk26u, https://github.com/openjdk/jdk27u — update repos (tags only: `jdk-25+36`, `jdk-26+35`, `jdk-27+35`).
- https://github.com/openjdk/jcstress — tags 0.11–0.16 with dates for 0.15/0.16, master `pom.xml` (0.17-SNAPSHOT), last master commit, archetype, and the full sample sources.
- Specific files read at tags (content verified via git):
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java — j.u.c Memory Consistency Properties (happens-before list).
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java — Thread.State docs, interrupt() docs, Thread Interruption section, deprecated methods (also read at the 21–26 GA tags for API diffs).
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/ThreadGroup.java — ThreadGroup API (also read at the 21–26 tags).
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java — wait() spurious-wakeup text, JCiP §14.2 reference.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java — computeIfAbsent/compute/merge contracts, "Recursive update".
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/VarHandle.java — access modes, C++11 mappings, fences.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java — non-reentrancy, optimistic-read HB rule.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java — try/finally idiom, fairness caveats, recursion limit.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/Condition.java — spurious wakeups.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/LongAdder.java — LongAdder vs AtomicLong, sum() caveat.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CopyOnWriteArrayList.java — copy-on-write cost, snapshot iterators.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/ThreadLocal.java — ThreadLocal example and initialValue/withInitial.
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/ScopedValue.java — final (no preview annotation) in 25.
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java — still preview in 27; sealed interface with `open()`.
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp — jcmd Thread.* commands and descriptions (also at the 21/24/25/26 tags).
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml — JFR event definitions (also at the 21/24/25/26 tags).
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/ThreadDumper.java — JSON thread-dump keys (also at 21 and 27).
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.schema.json — JSON schema (25/26).
  - https://github.com/openjdk/jdk/blob/jdk-27-ga/src/jdk.management/share/classes/com/sun/management/doc-files/threadDump.html — 27 format documentation (file existence and partial content).
  - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/HotSpotDiagnosticMXBean.java — dumpThreads(…, ThreadDumpFormat).
  - https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_04_Progress.java — spin-loop progress test.
  - https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_01_DataRaces.java — data-race publication test.
  - https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/primitives/singletons/Singleton_07_BrokenNonVolatileDCL.java — broken DCL.
  - https://github.com/openjdk/jcstress/tree/master/jcstress-samples — samples root (all other samples cited by name).

**Not reachable or not opened (do not cite from these notes without checking):** docs.oracle.com (JLS, API docs) and shipilev.net were blocked by network policy. openjdk.org JEP pages, bugs.openjdk.org and the InfoQ articles appeared only as search results and were not opened.
