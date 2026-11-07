import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l10"
K = "kotlin/workbench/concurrency/l10"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l10.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_LATCH = """CountDownLatch warmedUp = new CountDownLatch(3);

// each warm-up thread, when it is done (in a finally):
warmedUp.countDown();

// the thread that opens the service for traffic:
if (!warmedUp.await(30, TimeUnit.SECONDS)) {
    throw new IllegalStateException("caches not warm after 30 s");
}"""
K_LATCH = """val warmedUp = CountDownLatch(3)

// each warm-up thread, when it is done (in a finally):
warmedUp.countDown()

// the thread that opens the service for traffic:
if (!warmedUp.await(30, TimeUnit.SECONDS)) {
    throw IllegalStateException("caches not warm after 30 s")
}"""

J_BARRIER = """CyclicBarrier endOfDay = new CyclicBarrier(4, () -> recordExposure(sum(shares)));   // the barrier action

// each of the 4 workers, for every simulated day:
shares[me] = simulate(me, day);
endOfDay.await();          // the 4th to arrive runs the action, then all 4 go on"""
K_BARRIER = """val endOfDay = CyclicBarrier(4) { recordExposure(shares.sum()) }   // the barrier action

// each of the 4 workers, for every simulated day:
shares[me] = simulate(me, day)
endOfDay.await()          // the 4th to arrive runs the action, then all 4 go on"""

J_SEM = """private final Semaphore issuerPermits = new Semaphore(20);

Authorization authorize(Request r) throws InterruptedException {
    issuerPermits.acquire();             // before the try, like lock()
    try {
        return issuer.authorize(r);      // at most 20 threads in here
    } finally {
        issuerPermits.release();
    }
}"""
K_SEM = """private val issuerPermits = Semaphore(20)

fun authorize(r: Request): Authorization {
    issuerPermits.acquire()              // before the try, like lock()
    try {
        return issuer.authorize(r)       // at most 20 threads in here
    } finally {
        issuerPermits.release()
    }
}"""

J_PHASER = """Phaser phaser = new Phaser(1);          // the coordinator is a party
phaser.register();                      // each worker joins when it starts
phaser.arriveAndAwaitAdvance();         // wait for everyone still registered
phaser.arriveAndDeregister();           // leave; later phases wait for one party fewer"""
K_PHASER = """val phaser = Phaser(1)          // the coordinator is a party
phaser.register()               // each worker joins when it starts
phaser.arriveAndAwaitAdvance()  // wait for everyone still registered
phaser.arriveAndDeregister()    // leave; later phases wait for one party fewer"""

J_W1 = """CountDownLatch done = new CountDownLatch(4);
List<Mismatch> found = new CopyOnWriteArrayList<>();
for (Partition p : partitions) {
    new Thread(() -> {
        found.addAll(reconcile(p));
        done.countDown();
    }).start();
}
done.await();
report(found);"""
K_W1 = """val done = CountDownLatch(4)
val found = CopyOnWriteArrayList<Mismatch>()
for (p in partitions) {
    thread {
        found.addAll(reconcile(p))
        done.countDown()
    }
}
done.await()
report(found)"""
J_W2 = """CountDownLatch done = new CountDownLatch(partitions.size());
List<Mismatch> found = new CopyOnWriteArrayList<>();
List<Throwable> failures = new CopyOnWriteArrayList<>();
for (Partition p : partitions) {
    new Thread(() -> {
        try {
            found.addAll(reconcile(p));          // 1. do the work
        } catch (Throwable e) {
            failures.add(e);                      // 2. remember the failure instead of losing it
        } finally {
            done.countDown();                     // 3. always count down
        }
    }, "recon-" + p.id()).start();
}
if (!done.await(10, TimeUnit.MINUTES)) {          // 4. never wait forever
    throw new IllegalStateException("reconciliation still running after 10 min");
}
if (!failures.isEmpty()) throw new IllegalStateException("partitions failed: " + failures);
report(found);                                    // 5. countDown happens-before await returns: all results visible"""
K_W2 = """val done = CountDownLatch(partitions.size)
val found = CopyOnWriteArrayList<Mismatch>()
val failures = CopyOnWriteArrayList<Throwable>()
for (p in partitions) {
    thread(name = "recon-${p.id}") {
        try {
            found.addAll(reconcile(p))          // 1. do the work
        } catch (e: Throwable) {
            failures.add(e)                      // 2. remember the failure instead of losing it
        } finally {
            done.countDown()                     // 3. always count down
        }
    }
}
if (!done.await(10, TimeUnit.MINUTES)) {         // 4. never wait forever
    throw IllegalStateException("reconciliation still running after 10 min")
}
if (failures.isNotEmpty()) throw IllegalStateException("partitions failed: $failures")
report(found)                                    // 5. countDown happens-before await returns: all results visible"""

J_DRILL = """static boolean awaitAll(List<Runnable> tasks, Duration deadline) throws InterruptedException {
    CountDownLatch done = new CountDownLatch(tasks.size());
    for (Runnable task : tasks) {
        new Thread(() -> {
            try {
                task.run();
            } finally {
                done.countDown();          // even when the task throws
            }
        }).start();
    }
    return done.await(deadline.toMillis(), TimeUnit.MILLISECONDS);
}"""
K_DRILL = """fun awaitAll(tasks: List<() -> Unit>, deadline: Duration): Boolean {
    val done = CountDownLatch(tasks.size)
    for (task in tasks) {
        thread {
            try {
                task()
            } finally {
                done.countDown()          // even when the task throws
            }
        }
    }
    return done.await(deadline.toMillis(), TimeUnit.MILLISECONDS)
}"""

def bar(x1, x2, y, cls="box"):
    return f'<rect class="{cls}" x="{x1}" y="{y - 8}" width="{x2 - x1}" height="16" rx="6"/>'
def wait(x1, x2, y):
    return f'<line class="ln-d" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'

ROWS = [60, 105, 150]
FIG = (
    '<svg viewBox="0 0 680 240" role="img" aria-label="Three workers run day 1 and day 2. Each waits at the barrier until the last one arrives; the barrier action runs once per day, then all three continue">'
    + "".join(f'<text class="t" x="20" y="{y + 5}">W{i}</text>' for i, y in enumerate(ROWS))
    + '<line class="ln-a" x1="270" y1="40" x2="270" y2="170"/><text class="t-s t-a" x="270" y="30" text-anchor="middle">barrier: day 1</text>'
    + '<line class="ln-a" x1="520" y1="40" x2="520" y2="170"/><text class="t-s t-a" x="520" y="30" text-anchor="middle">barrier: day 2</text>'
    + bar(70, 150, ROWS[0]) + wait(150, 268, ROWS[0])
    + bar(70, 210, ROWS[1]) + wait(210, 268, ROWS[1])
    + bar(70, 266, ROWS[2], "box-a")
    + bar(290, 350, ROWS[0]) + wait(350, 518, ROWS[0])
    + bar(290, 516, ROWS[1], "box-a")
    + bar(290, 440, ROWS[2]) + wait(440, 518, ROWS[2])
    + '<rect class="box-ok" x="215" y="186" width="110" height="30" rx="8"/><text class="t-s" x="270" y="206" text-anchor="middle">action: total</text>'
    + '<rect class="box-ok" x="465" y="186" width="110" height="30" rx="8"/><text class="t-s" x="520" y="206" text-anchor="middle">action: total</text>'
    + '<text class="t-s t-m" x="600" y="65">bar: work</text><text class="t-s t-m" x="600" y="110">dashes: wait</text><text class="t-s t-a" x="600" y="155">last to arrive</text>'
    + '</svg>'
)

L = {
 "id": "conc-10",
 "title": "Synchronizers: latch, barrier, semaphore, phaser",
 "minutes": 36,
 "goal": "By the end you can pick the right synchronizer for a coordination problem (wait for events, meet at a line, limit concurrency, phases that change size) and use each without the classic bugs.",
 "warmup": {
  "q": "A `Semaphore` starts with 5 permits. One thread calls `release()` without ever calling `acquire()`. What does `availablePermits()` return?",
  "options": ["5: the stray release is ignored", "6", "It throws `IllegalMonitorStateException`", "4"],
  "answer": 1,
  "why": "Permits belong to nobody. A semaphore is a counter, and `release()` adds one whoever calls it. That's handy (one thread can acquire, another release), and it's also how a bug quietly raises your connection limit from 5 to 6, then 7. A lock would throw here; a semaphore can't."
 },
 "sections": [
  {
   "h": "CountDownLatch waits for N events, once",
   "body": "A `CountDownLatch` starts at a count. Any thread can call `countDown()`. Threads that call `await()` wait until the count reaches zero, then all of them go on. You used two of them in lesson 3 of this track to make threads collide.\n\n" + pair(J_LATCH, K_LATCH) + "\n\nThe latch waits for events, not for particular threads. One thread may count down three times, or three threads once each. It doesn't care.\n\nIt is also **one-shot**. Once the count reaches zero, it stays there. Every later `await()` returns at once, and extra `countDown()` calls do nothing. There is no reset. If you need the same gate every round, you want a barrier, the next section.\n\nTwo habits keep latches from hanging services. Call `countDown()` in a `finally`, so a task that throws still counts. Otherwise the count never reaches zero and the waiter waits forever, `WAITING` in `CountDownLatch.await` in every thread dump. And prefer `await(timeout, unit)`, which returns `false` if time ran out, so the caller can fail with a clear message instead of hanging.\n\nA latch also carries visibility: everything a thread did before `countDown()` happens-before `await()` returns in the waiting thread. That is why the caller can read the warm-up results without another lock.",
   "try": {
    "title": "Open for traffic when the caches are warm",
    "minutes": 3,
    "steps": [
     "Read `LatchDemo`. Three threads load three caches (200, 400 and 300 ms) and count down. `main` waits at most 2 seconds.",
     "Predict when `ready` is printed, and what an extra `countDown()` does after that.",
     "Run it, then run it again with `-Pargs=stuck`, where one load takes a minute."
    ],
    "code": code("LatchDemo"),
    "expect": "The caches load at about 200, 300 and 400 ms, and `ready=true, count=0` follows right after the slowest one. The extra `countDown()` leaves the count at 0, and `await` returns at once. With `stuck`, `main` prints `ready=false, count=1` after 2 seconds instead of hanging forever."
   }
  },
  {
   "h": "CyclicBarrier makes N threads meet, then all go on together",
   "body": "A `CyclicBarrier` waits for threads, not events. You give it a number of parties. Each thread calls `await()` when it reaches the meeting point and waits there until the last party arrives. Then all of them are released together, and the barrier resets itself for the next round. That is the cyclic part.\n\n" + pair(J_BARRIER, K_BARRIER) + "\n\nThe optional **barrier action** runs once per round, on the last thread to arrive, before anyone is released. It's the place to combine results: each worker writes its own slot of `shares` before `await()`, and those writes are visible to the action and to every thread after the barrier. The figure shows two rounds.\n\nA barrier can break. If a waiting thread is interrupted, or its `await(timeout)` times out, or the barrier action throws, the barrier is broken: the thread that timed out gets `TimeoutException`, and every other waiter, now and later, gets `BrokenBarrierException` until someone calls `reset()`. That is deliberate. A round with a missing party can't complete, and failing all of them is better than leaving the rest waiting forever.\n\nBut look at what doesn't break it: a thread that throws before it ever calls `await()`. The barrier can't know it's gone. The others wait, with plain `await()`, forever. So use the timed `await` in anything that runs in production.\n\nLatch or barrier? A latch is a gate opened by events (\"three caches loaded\"). A barrier is a meeting point for a fixed group of threads (\"all four workers finished day 3\").",
   "figure": {"svg": FIG, "caption": "Each worker waits at the barrier until the last one arrives. The barrier action runs once per round, then all three start the next day together."},
   "try": {
    "title": "Three rounds, then a missing worker",
    "minutes": 3,
    "steps": [
     "Read `BarrierDemo`. Three workers simulate three days; the barrier action prints the day's exposure and the name of the thread that ran it.",
     "On day 4, worker 2 never arrives and the other two wait at most 300 ms. Predict what each of them prints.",
     "Run it twice."
    ],
    "code": code("BarrierDemo"),
    "expect": "Three lines `day closed by worker-2`, with exposures 6,000, 12,000 and 18,000: worker 2 is the slowest, so it is always the last to arrive and runs the action. On day 4, one worker gets `TimeoutException` and breaks the barrier, and the other gets `BrokenBarrierException`. Which one gets which can change between runs. `broken: true` at the end."
   }
  },
  {
   "h": "Semaphore limits how many threads do something at once",
   "body": "A `Semaphore` holds a number of permits. `acquire()` takes one, waiting while none are left. `release()` gives one back. With 20 permits, at most 20 threads can be between the two calls.\n\n" + pair(J_SEM, K_SEM) + "\n\nThis is how you protect something that tolerates N users but not N + 1: a card-issuer API that throttles above 20 concurrent calls per client, a pool of 20 database connections, a CPU-heavy PDF renderer. `tryAcquire(timeout, unit)` waits a bounded time and returns `false` if no permit came free, so a request can fail fast instead of piling up.\n\nThe idiom is the one from explicit locks: `acquire()` before the `try`, `release()` in `finally`. It matters even more here, because of the property from the warm-up: **permits have no owner**. A lock knows who holds it and throws if a stranger releases it. A semaphore is just a counter. Both of these bugs silently raise your limit:\n\n- calling `acquire()` inside the `try`, so an interrupted wait still runs the `release()` in `finally`;\n- ignoring the result of `tryAcquire`, then running the task and releasing anyway.\n\nThe lab's `IssuerGate` has both. Every extra release is a permanent extra permit, and a limit of 20 drifts to 30 over a day of interrupts and timeouts. No exception, no log line.\n\nTwo more points. A `Semaphore` limits one JVM: six pods with 20 permits each send up to 120 calls to the issuer, so divide the issuer's limit by your pod count. And `new Semaphore(20, true)` makes it fair, which stops a fast thread from grabbing permits ahead of threads that have waited longer.",
   "try": {
    "title": "Five permits, twenty calls",
    "minutes": 3,
    "steps": [
     "Read `SemaphoreDemo`. Twenty threads each make a 100 ms issuer call through a `Semaphore(5)`, and the demo tracks the peak number in flight.",
     "Predict the peak and the total time.",
     "Run it. Then move `issuer.acquire()` to inside the `try` in the Java version: does anything change in this run? Why might it in production?"
    ],
    "code": code("SemaphoreDemo"),
    "expect": "Peak in flight 5, total about 400 ms: four waves of five calls. The stray `release()` turns 5 permits into 6. Moving `acquire()` inside the `try` changes nothing here, because nobody interrupts the waiters. In production an interrupt during the wait (a cancelled request, a shutdown) would release a permit that was never taken."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  },
  {
   "h": "Phaser and Exchanger, briefly",
   "body": "A `Phaser` is a barrier whose group can change size. Parties `register()` to join and `arriveAndDeregister()` to leave, and each phase waits only for the parties registered at that moment. Phases are numbered from 0, and you can override `onAdvance(phase, parties)` to run code between phases and to end the phaser by returning `true`.\n\n" + pair(J_PHASER, K_PHASER) + "\n\nUse it when the number of workers isn't known up front or changes between phases: a settlement run where some workers only fetch and then leave, or a job that registers one party per file it discovers. If the group is fixed, a `CyclicBarrier` is simpler and says what it means. A phaser can also replace a `CountDownLatch` that you'd like to reuse.\n\nAn `Exchanger` is the smallest synchronizer: two threads meet and swap one object each, for example a full buffer for an empty one. You will rarely need it.\n\nAll of these synchronizers, like `ReentrantLock`, are built on `AbstractQueuedSynchronizer`, so a thread waiting in any of them is parked and shows as `WAITING` or `TIMED_WAITING` in a thread dump, with the synchronizer's class in its stack. And none of them has an owner the deadlock detector can see, so a cycle of threads waiting on semaphores or latches is never reported as a deadlock.",
   "try": {
    "title": "A worker leaves halfway",
    "minutes": 3,
    "steps": [
     "Read `PhaserDemo`. Three workers run three phases (fetch, net, post). Worker 2 leaves after the first phase. `onAdvance` prints each phase and the parties left.",
     "Predict the party count printed for each phase.",
     "Run it."
    ],
    "code": code("PhaserDemo"),
    "expect": "`phase 0 (fetch) done, 3 parties`, then `phase 1 (net) done, 2 parties` and `phase 2 (post) done, 2 parties`, then `terminated: true`. `main` registered itself first so no phase could finish before every worker had joined, then left. Worker 2's `arriveAndDeregister` counts as its arrival for phase 1 and shrinks every later phase."
   }
  }
 ],
 "analogy": "A `CountDownLatch` is a rocket countdown: when it reaches zero the launch happens, and you can't count down again. A `CyclicBarrier` is a tour group regrouping at every landmark: the bus leaves only when everyone is back, and the guide (the barrier action) does a head count each time. A `Semaphore` is a car park with 20 spaces and a sign showing how many are free; nobody checks which car leaves, so a car that never parked can still \"leave\" and the sign shows 21. A `Phaser` is a relay race where runners can join or drop out between legs. The analogy breaks at the tour bus: a guide would go looking for a missing tourist. A barrier just waits, forever, unless you gave `await` a timeout.",
 "in_your_world": "In a Quarkus service, a latch shows up at startup (open for traffic after the BIN ranges and FX rates load) and in almost every concurrency test you write. A semaphore shows up in front of anything with a concurrency limit: a card-issuer API that throttles at 20 calls per client, a PDF generator, a Temporal activity that calls a partner with a strict rate limit. Remember the multiplication: the limit is per JVM, so 6 pods with 20 permits each is 120 calls at the partner. Barriers and phasers are rarer in request-handling code and common in batch jobs: an end-of-day exposure simulation or a reconciliation that runs in phases across worker threads.",
 "mistake": "The most common real mistake is releasing a permit you never acquired. It happens in two ways: `acquire()` placed inside the `try`, so an interrupted wait still reaches the `release()` in `finally`, and `tryAcquire(timeout)` whose `false` result is ignored. Both look fine in review and in tests, because tests rarely interrupt waiters or exhaust permits. In production, each cancelled request or timeout adds one permit for good, and the limit that protected the issuer API slowly stops limiting. The fix is the lock idiom: `acquire()` on the line before `try`, and `if (!tryAcquire(...))` that returns or throws before the `try` is entered.",
 "compare": {
  "title": "A permit helper in Java and Kotlin",
  "java": {"title": "Java", "src": """static <T> T withPermit(Semaphore s, Callable<T> task) throws Exception {
    s.acquire();                  // before the try, like lock()
    try {
        return task.call();
    } finally {
        s.release();              // exactly the permit we took
    }
}

Authorization a = withPermit(issuerPermits, () -> issuer.authorize(request));"""},
  "kotlin": {"title": "Kotlin", "src": """inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()                     // before the try, like lock()
    try {
        return block()
    } finally {
        release()                 // exactly the permit we took
    }
}

val a = issuerPermits.withPermit { issuer.authorize(request) }"""},
  "note": "Both languages use the same `java.util.concurrent` classes, and both block a thread while it waits. Kotlin's difference is that an `inline` extension function makes the safe idiom read like a language feature: the lambda is inlined, so there's no allocation, `return` inside it works as usual, and nobody on the team writes the `try`/`finally` by hand again. The Kotlin standard library doesn't ship `withPermit` for `java.util.concurrent.Semaphore`; you write it once, as above. kotlinx.coroutines has its own `Semaphore` with a built-in `withPermit` that suspends the coroutine instead of blocking a thread. The coroutines track covers it."
 },
 "worked": {
  "title": "A parallel reconciliation that can't hang",
  "steps": [
   {"say": "End-of-day reconciliation compares 4 ledger partitions against the bank statement. Each takes a few seconds, so it runs on 4 threads and waits for all of them with a latch. Read this first version. What happens if `reconcile` throws for one partition?",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "The failing thread dies before `countDown()`. The count stays at 1, and `await()` waits forever. The job doesn't fail; it just never ends. A dump shows `main` `WAITING` in `CountDownLatch.await` and no worker threads at all, because they all finished or died. The fix has three parts: count down in `finally`, record the failure so it isn't lost, and never wait without a deadline.", "code": "", "lang": ""},
   {"say": "Here is the version that always ends, with subgoal labels.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself: why can `main` read `found` after `await` returns without any lock? Answer: everything a worker did before `countDown()` happens-before `await()` returns in the thread that waited. `found` is still a `CopyOnWriteArrayList`, because the four workers add to it at the same time. In a real service you'd submit the four tasks to an `ExecutorService` and use `invokeAll`, which the executors track covers. A latch is one of the pieces such tools are built from.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix a permit leak, then run a simulation in rounds",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/IssuerGate.java", f"{lab}/main/{P}/RoundRunner.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l10.*'",
  "steps": [
   "Run the tests. Four of six fail: the timed call runs its task with no permit, an interrupted waiter adds a permit, and both `RoundRunner` tests hit `UnsupportedOperationException`.",
   "Fix `IssuerGate.call(task)`: move `acquire()` to the line before the `try`.",
   "Fix `IssuerGate.call(task, maxWait)`: if `tryAcquire` returns `false`, throw `TimeoutException` before the `try`, so the task doesn't run and nothing is released.",
   "Write `RoundRunner.run`. Keep a `long[] shares`, one slot per worker. Build a `CyclicBarrier(workers, action)` whose action sums `shares` and calls `onRoundTotal`. Start one thread per worker that loops over the rounds: `shares[me] = step.applyAsLong(me, r)`, then `await()`. Join every thread before returning.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "Why can the barrier action read `shares` without a lock? Each worker writes only its own slot, before `await()`, and everything before `await()` happens-before the action runs.",
   "`await()` throws `InterruptedException` and `BrokenBarrierException`. In the worker, restore the interrupt flag for the first, and stop the loop for both.",
   "The second `RoundRunner` test calls your step from 4 threads and checks that round `r` never starts before `r` totals have been passed on. The barrier action runs before anyone is released, so this holds by construction."
  ],
  "done_when": "All six tests in `SynchronizersTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Wait for N tasks, with a deadline",
  "minutes": 4,
  "prompt": "Close this page. Write `awaitAll(tasks, deadline)`: run each task on its own thread and return `true` if all of them finished within the deadline, `false` otherwise. A task that throws must not make it hang. Check: where is your `countDown()`?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "`CountDownLatch`: wait until N events have happened. One-shot; count down in `finally`; await with a timeout.",
  "`CyclicBarrier`: N threads meet, the barrier action runs once on the last arrival, then all continue. It resets itself each round and breaks on timeout or interrupt.",
  "A thread that never reaches `await()` leaves the others waiting forever unless they use the timed `await`.",
  "`Semaphore`: at most N threads at once. Permits have no owner, so release only what you acquired: `acquire()` before `try`, check `tryAcquire`'s result.",
  "`Phaser`: a reusable barrier whose parties can register and leave between phases. `Exchanger` swaps one object between two threads.",
  "Releasing a latch, barrier or semaphore happens-before the waiting threads continue, so results written before it are visible after it."
 ],
 "quiz": [
  {"q": "A service must not accept traffic until four independent caches have loaded, each on its own thread. Which tool fits best?",
   "options": ["`CountDownLatch(4)`, counted down by each loader, awaited by the startup code", "`CyclicBarrier(4)`", "`Semaphore(4)`", "`Exchanger`"],
   "answer": 0, "why": "You are waiting for four events, once. That is a latch. A barrier would make the four loader threads wait for each other, which they don't need to, and it is built for repeated rounds. A semaphore limits concurrency; it doesn't wait for completion."},
  {"q": "`try { sem.acquire(); callIssuer(); } finally { sem.release(); }` with `new Semaphore(10)`. A thread is interrupted while it waits in `acquire()`. What happens?",
   "options": ["Nothing: `acquire()` gives up cleanly", "The thread gets the permit anyway", "`acquire()` throws, the `finally` releases a permit that was never taken, and the semaphore now allows 11", "The semaphore throws `IllegalMonitorStateException` in `release()`"],
   "answer": 2, "why": "`acquire()` throws `InterruptedException`, which still runs the `finally`. Permits have no owner, so `release()` simply adds one. Move `acquire()` above the `try`."},
  {"q": "Three workers use a `CyclicBarrier(3)` with plain `await()`. One worker throws an exception before it reaches `await()` in round 5. What do the other two do?",
   "options": ["They get `BrokenBarrierException` at once", "The barrier notices the dead thread and lets them through", "They get `TimeoutException` after a default timeout", "They wait forever"],
   "answer": 3, "why": "The barrier only breaks when a waiting thread is interrupted or times out, or the action fails. A thread that never arrives is invisible to it, and plain `await()` has no timeout. Use `await(timeout, unit)` so the round fails instead of hanging."},
  {"q": "From deadlock, livelock and starvation: 20 request threads each take 1 permit from a `Semaphore(20)` that guards DB connections, then call a helper that takes another permit from the same semaphore. Under full load everything stops. What will `jcmd Thread.print` say?",
   "options": ["`Found one Java-level deadlock` naming the semaphore", "No deadlock report: semaphore permits have no owner, so the detector can't see the cycle; you see 20 threads `WAITING` in `Semaphore.acquire`", "It reports a livelock", "The threads show as `BLOCKED`"],
   "answer": 1, "why": "This is hold-and-wait: every thread holds one permit and waits for a second. It is a real deadlock, but the JVM's detector only follows owned locks (monitors and `ReentrantLock`-style synchronizers). Parked threads show as `WAITING`, not `BLOCKED`. Acquire both permits at once with `acquire(2)`, or don't take a second one while holding the first.",
   "from": "conc-06"},
  {"q": "A batch job processes files in rounds and the number of worker threads changes between rounds as files are discovered. Which tool fits?",
   "options": ["One `CountDownLatch` per round, created up front", "A `CyclicBarrier` with the maximum number of workers", "A `Phaser`, with workers registering when they start and deregistering when they finish", "A `Semaphore`"],
   "answer": 2, "why": "A phaser's group can grow and shrink between phases, and each phase waits only for the parties registered then. A barrier's party count is fixed, so missing workers would hang it. Latches are one-shot and need their count known in advance."}
 ],
 "flashcards": [
  {"front": "A `CountDownLatch` has reached zero. What do later `await()` and `countDown()` calls do?", "back": "`await()` returns at once. `countDown()` does nothing. A latch can't be reset."},
  {"front": "When does a `CyclicBarrier`'s barrier action run, and on which thread?", "back": "Once per round, on the last thread to arrive, before any waiting thread is released."},
  {"front": "What breaks a `CyclicBarrier`?", "back": "A waiting thread being interrupted or timing out, the barrier action throwing, or `reset()`. Then every waiter gets `BrokenBarrierException`."},
  {"front": "What does `release()` do on a `Semaphore` when the caller never acquired a permit?", "back": "It adds a permit anyway. Permits have no owner, so stray releases silently raise the limit."},
  {"front": "Where do `acquire()` and `release()` go relative to `try`/`finally`?", "back": "`acquire()` on the line before `try`; `release()` in `finally`. With `tryAcquire`, check its result before entering the `try`."},
  {"front": "Latch or barrier: \"start serving after 3 caches load\" vs \"4 workers finish day N before any starts day N+1\"?", "back": "The first is a latch (waiting for events, once). The second is a barrier (a fixed group meeting every round)."},
  {"front": "What can a `Phaser` do that a `CyclicBarrier` can't?", "back": "Change its number of parties between phases: `register()` to join, `arriveAndDeregister()` to leave."}
 ],
 "terms": [
  {"term": "Synchronizer", "plain": "An object that makes threads wait for each other or for events, such as a latch, barrier or semaphore."},
  {"term": "CountDownLatch", "plain": "A one-shot gate that opens when a count reaches zero."},
  {"term": "CyclicBarrier", "plain": "A meeting point for a fixed number of threads that resets itself after each round."},
  {"term": "Barrier action", "plain": "Code a `CyclicBarrier` runs once per round, before releasing the threads."},
  {"term": "Semaphore", "plain": "A counter of permits that limits how many threads can do something at once."},
  {"term": "Permit", "plain": "One unit of a semaphore's count. It belongs to nobody."},
  {"term": "Phaser", "plain": "A reusable barrier whose set of parties can change between phases."}
 ],
 "explain_back": {
  "prompt": "Explain the difference between a `CountDownLatch`, a `CyclicBarrier` and a `Semaphore` to a teammate, with one payments example of each.",
  "answer": "A latch waits for a number of events and then opens for good: startup code waits until the BIN ranges, FX rates and merchant config have loaded, then starts taking traffic. A barrier is a meeting point for a fixed group of threads, every round: four workers simulating exposure each finish day 3, the last one totals the day, and then all four start day 4. A semaphore limits how many threads do something at the same time: at most 20 threads may be inside a call to the card issuer. The traps differ too. A latch hangs if a task forgets to count down. A barrier hangs if a thread never arrives and nobody used a timeout. A semaphore quietly raises its limit if code releases a permit it never took."
 },
 "deeper": {
  "minutes": 10,
  "body": "Every synchronizer in this lesson, like `ReentrantLock`, is a thin layer over `AbstractQueuedSynchronizer`: an `int` of state and a queue of parked threads. For a latch the state is the count, and `await` parks until it is zero. For a semaphore it is the permits left. That shared core is why they all show up the same way in a thread dump: `WAITING (parking)`, with a line like `parking to wait for <0x...> (a java.util.concurrent.Semaphore$NonfairSync)`.\n\nA few API corners are worth knowing. `Semaphore.acquire(n)` takes several permits in one step, which avoids the hold-one-wait-for-another deadlock from the quiz. `drainPermits()` takes all that are left, which is handy when you want to stop new work during a shutdown. `acquireUninterruptibly()` ignores interrupts, which you almost never want. `CyclicBarrier.await()` returns the arrival index (parties minus one for the first to arrive, zero for the last), so you can pick one thread to do extra work without a barrier action.\n\n`Phaser` supports tiering: you can build a tree of phasers so thousands of parties don't all contend on one. Its Javadoc caps a single phaser at 65,535 registered parties.\n\nOn virtual threads (JDK 21), blocking in any of these is cheap: the virtual thread parks and its carrier thread runs something else. A `Semaphore` is in fact the standard way to limit concurrency once you start a virtual thread per task, because there is no pool size to do it for you. The virtual threads track comes back to that. In Kotlin coroutines, the equivalents suspend instead of blocking: `kotlinx.coroutines.sync.Semaphore`, `Job.join()` or `awaitAll()` for latches, and channels for most of the rest."
 },
 "sources": [
  {"title": "CountDownLatch (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html"},
  {"title": "CyclicBarrier (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CyclicBarrier.html"},
  {"title": "Phaser (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Phaser.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 5.5 (synchronizers)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-10.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
