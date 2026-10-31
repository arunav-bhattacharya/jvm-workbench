# Track: jmm, "The Java Memory Model" (lab: labs/jmm, package workbench.jmm.lNN)

Research notes: java_concurrency_and_jmm.md. The JLS was NOT fetchable; the j.u.c package Javadoc
restates the happens-before rules and was verified, so cite that for the rules and treat JLS quotes
carefully (paraphrase, don't quote). Labs in Java; Kotlin `compare` for @Volatile, `lazy` modes,
`by lazy` vs holder idiom. JMM bugs are hard to reproduce in tests: design labs around code that is
deterministic once correct (e.g. a stop flag that must be seen, which hangs forever without volatile;
use @Timeout so the stub fails instead of hanging the build), and around API usage (VarHandle modes).
Never assert timings.

Lessons:
- jmm-01 Why your loop never stops: CPU caches and store buffers in plain words, compiler and JIT
  reordering and hoisting, the non-volatile stop flag that hangs (measured in notes: hangs with JIT,
  stops under -Xint). Figure: cores with caches. Lab: fix a stop flag and a "ready" publication bug.
- jmm-02 Happens-before: program order, monitor unlock/lock, volatile write/read, thread start, join,
  plus j.u.c guarantees (executor submit, concurrent collections, latches). Data race defined.
  Figure: happens-before edges between two threads. Lab: annotate and fix three snippets so each
  read is guaranteed to see the write.
- jmm-03 volatile: visibility and ordering, not atomicity (4 threads x 1M on volatile int lost updates,
  measured), when volatile is enough (single writer flags, status fields), volatile long/double
  tearing rule. Lab: decide volatile vs atomic vs lock for four fields in a payment session object.
- jmm-04 Safe publication, final fields and escaping this: the safe publication idioms, final field
  freeze semantics, `this` escaping from a constructor (registering a listener, starting a thread),
  immutable objects are thread-safe with no publication care. Lab: fix an escaping constructor and
  an unsafe publication.
- jmm-05 Lazy init done right: broken double-checked locking, DCL with volatile, the holder class
  idiom, enum singleton, Kotlin `by lazy` and its three LazyThreadSafetyMode values.
  Lab: implement three correct lazy initializers and count initializations under contention.
- jmm-06 VarHandles and memory ordering modes: plain, opaque, acquire/release, volatile, with
  getAcquire/setRelease and compareAndSet; when you need them (almost never in app code); jcstress as
  the only honest test. Lab: a single-producer single-consumer slot or a lazily-set flag with
  VarHandle acquire/release.
