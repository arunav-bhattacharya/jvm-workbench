# Track: cap1, "Capstone: a payment ledger under load" (lab: labs/ledger, package workbench.ledger.lNN)

Part 1, Concurrency on the JVM (conc, jmm, exec, vt). Draws on every track in the part.
Dependencies: none beyond the shared JUnit/AssertJ setup.

The program: an in-memory ledger of accounts that applies transfers from many threads, never loses
money, never deadlocks, publishes balances safely, and serves thousands of concurrent requests.

- cap1-01 Design the ledger and make it correct: invariants first (total money is constant, no
  negative balance), per-account locks with a global lock order, an immutable Transfer record, a
  stress harness (start-line latch) that proves the invariant across 8 threads x 100k transfers.
- cap1-02 Run it on a pool you can reason about: a bounded ThreadPoolExecutor with a named factory,
  a rejection policy chosen on purpose, pool sizing from Little's law, graceful shutdown that drains,
  and a balance snapshot published safely (happens-before named for each field). Tests: no lost
  transfers on shutdown, rejection counted, snapshot never torn.
- cap1-03 Serve it with virtual threads: one virtual thread per request, a semaphore bulkhead for the
  slow fraud check, deadlines with a fallback, no pinning (ReentrantLock, not synchronized around IO),
  and a fail-fast fan-out with an executor (structured concurrency is preview on 21: show it in a
  deeper note only). Tests: max in-flight never exceeds the bulkhead, the deadline fires, the
  invariant still holds at 10k concurrent requests. Ends with the design review.

Diagnostics thread (required): cap1-02 has a Try-it that hangs the pool on purpose (a task waiting on
a task in the same bounded pool) and has the learner find it with `jcmd <pid> Thread.print`: read the
thread names, states, the "waiting on" / "locked" lines and the stack frames. cap1-03 has a Try-it that
takes a JSON dump with `jcmd <pid> Thread.dump_to_file -format=json` while 10k virtual threads are
parked, and reads it (where the virtual threads appear, how to group them by stack). Show the real
output from your runs, trimmed.

