import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l13"
K = "kotlin/workbench/concurrency/l13"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l13.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_STRESS = """record Round(RefundLedger ledger, AtomicLong approved) {}

int failed = Stress.failingRounds(20, 8, 2_000,
        () -> new Round(new RefundLedger(Map.of("pay-1", 10_000L)), new AtomicLong()),   // fresh state per round
        r -> { if (r.ledger().refund("pay-1", 1)) r.approved().incrementAndGet(); },      // every thread, over and over
        r -> r.approved().get() == 10_000 && r.ledger().refunded("pay-1") == 10_000);     // must hold at the end
assertThat(failed).isZero();"""
K_STRESS = """class Round(val ledger: RefundLedger, val approved: AtomicLong)

val failed = Stress.failingRounds(20, 8, 2_000,
    { Round(RefundLedger(mapOf("pay-1" to 10_000L)), AtomicLong()) },              // fresh state per round
    { r -> if (r.ledger.refund("pay-1", 1)) r.approved.incrementAndGet() },        // every thread, over and over
    { r -> r.approved.get() == 10_000L && r.ledger.refunded("pay-1") == 10_000L }) // must hold at the end
assertThat(failed).isZero()"""

J_SLEEP = """// flaky: hopes 50 ms is enough on every machine, and is slow on all of them
worker.submit(payment);
Thread.sleep(50);
assertThat(store.status(payment.id())).isEqualTo(SETTLED);

// solid: wait for the event itself, with a deadline far above any real duration
CountDownLatch settled = new CountDownLatch(1);
store.onSettled(id -> settled.countDown());
worker.submit(payment);
assertThat(settled.await(10, TimeUnit.SECONDS)).isTrue();
assertThat(store.status(payment.id())).isEqualTo(SETTLED);"""
K_SLEEP = """// flaky: hopes 50 ms is enough on every machine, and is slow on all of them
worker.submit(payment)
Thread.sleep(50)
assertThat(store.status(payment.id)).isEqualTo(SETTLED)

// solid: wait for the event itself, with a deadline far above any real duration
val settled = CountDownLatch(1)
store.onSettled { settled.countDown() }
worker.submit(payment)
assertThat(settled.await(10, TimeUnit.SECONDS)).isTrue()
assertThat(store.status(payment.id)).isEqualTo(SETTLED)"""

J_FAKE = """class BlockingIssuer implements Issuer {
    final CountDownLatch inCall = new CountDownLatch(1);
    final CountDownLatch release = new CountDownLatch(1);

    @Override
    public Result authorize(Request r) throws InterruptedException {
        inCall.countDown();          // 1. tell the test: a thread is inside the call
        release.await();             // 2. hold it here until the test says go
        return Result.APPROVED;
    }
}"""
K_FAKE = """class BlockingIssuer : Issuer {
    val inCall = CountDownLatch(1)
    val release = CountDownLatch(1)

    override fun authorize(r: Request): Result {
        inCall.countDown()           // 1. tell the test: a thread is inside the call
        release.await()              // 2. hold it here until the test says go
        return Result.APPROVED
    }
}"""

JCSTRESS = """import org.openjdk.jcstress.annotations.*;
import org.openjdk.jcstress.infra.results.II_Result;
import static org.openjdk.jcstress.annotations.Expect.*;

@JCStressTest
@Outcome(id = "1, 2", expect = ACCEPTABLE, desc = "actor1 went first")
@Outcome(id = "2, 1", expect = ACCEPTABLE, desc = "actor2 went first")
@Outcome(id = "1, 1", expect = ACCEPTABLE_INTERESTING, desc = "both read 0: one increment lost")
@State
public class RefundCounterRace {
    int refunds;                                  // shared state, fresh for every sample

    @Actor
    public void actor1(II_Result r) { r.r1 = ++refunds; }

    @Actor
    public void actor2(II_Result r) { r.r2 = ++refunds; }
}"""

BASH_JC = """mvn archetype:generate -DinteractiveMode=false -DarchetypeGroupId=org.openjdk.jcstress \\
    -DarchetypeArtifactId=jcstress-java-test-archetype -DgroupId=org.sample -DartifactId=test -Dversion=1.0
cd test
# put RefundCounterRace.java next to the generated sample test, then:
mvn clean verify
java -jar target/jcstress.jar -t RefundCounterRace"""

BASH_DIAG = """jcmd <pid> Thread.print -l                          # states, stacks, owned j.u.c locks, deadlocks
jcmd <pid> Thread.dump_to_file -format=json t.json  # JSON; per-thread state and lock fields need JDK 25+
jcmd <pid> JFR.start duration=60s filename=locks.jfr
jfr summary locks.jfr                               # how many events of each type
jfr print --events jdk.JavaMonitorEnter locks.jfr   # who waited for which monitor, how long, after whom"""

STATES = """| What the dump says | What the thread is doing |
|---|---|
| `RUNNABLE` | Running, ready to run, or blocked inside native I/O such as a socket read |
| `BLOCKED (on object monitor)` | Waiting to enter a `synchronized` block that another thread holds |
| `WAITING (parking)` | Parked by `java.util.concurrent`: a lock, latch, queue or semaphore; the `parking to wait for` line names it |
| `WAITING (on object monitor)` | Inside `Object.wait()` |
| `TIMED_WAITING` | The same, with a timeout, or in `sleep` |"""

J_W1 = """@Test
void loadsOnce() throws Exception {
    AtomicInteger loads = new AtomicInteger();
    BinCache cache = new BinCache(bin -> { loads.incrementAndGet(); return "Northwind Bank"; });
    for (int i = 0; i < 8; i++) new Thread(() -> cache.issuerFor("411111")).start();
    Thread.sleep(100);                                   // "they should be done by now"
    assertThat(loads.get()).isEqualTo(1);
}"""
K_W1 = """@Test
fun `loads once`() {
    val loads = AtomicInteger()
    val cache = BinCache { loads.incrementAndGet(); "Northwind Bank" }
    repeat(8) { thread { cache.issuerFor("411111") } }
    Thread.sleep(100)                                    // "they should be done by now"
    assertThat(loads.get()).isEqualTo(1)
}"""
J_W2 = """@Test
@Timeout(10)
void loadsOnceWhileOthersWait() throws Exception {
    AtomicInteger loads = new AtomicInteger();
    CountDownLatch inLoader = new CountDownLatch(1), release = new CountDownLatch(1);
    BinCache cache = new BinCache(bin -> {
        loads.incrementAndGet();
        inLoader.countDown();                              // 1. a caller is inside the loader
        try { release.await(); }                           //    and stays there until we say go
        catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return "Northwind Bank";
    });
    List<Thread> callers = new ArrayList<>();
    for (int i = 0; i < 8; i++) {
        Thread t = new Thread(() -> cache.issuerFor("411111"));
        t.start();
        callers.add(t);
    }
    assertThat(inLoader.await(5, TimeUnit.SECONDS)).isTrue();
    awaitParked(callers, 8);                               // 2. all 8 are now waiting, inside or outside
    release.countDown();                                   // 3. let the load finish
    for (Thread t : callers) t.join();
    assertThat(loads.get()).isEqualTo(1);                  // 4. one load served all eight
}

static void awaitParked(List<Thread> threads, int n) throws InterruptedException {
    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
    while (threads.stream().filter(t -> t.getState() == Thread.State.BLOCKED
            || t.getState() == Thread.State.WAITING).count() < n) {
        if (System.nanoTime() > deadline) throw new AssertionError("callers never queued up");
        Thread.sleep(5);                                   // polling with a deadline: never a bare guess
    }
}"""
K_W2 = """@Test
@Timeout(10)
fun `loads once while others wait`() {
    val loads = AtomicInteger()
    val inLoader = CountDownLatch(1)
    val release = CountDownLatch(1)
    val cache = BinCache {
        loads.incrementAndGet()
        inLoader.countDown()                               // 1. a caller is inside the loader
        release.await()                                    //    and stays there until we say go
        "Northwind Bank"
    }
    val callers = List(8) { thread { cache.issuerFor("411111") } }
    assertThat(inLoader.await(5, TimeUnit.SECONDS)).isTrue()
    awaitParked(callers, 8)                                // 2. all 8 are now waiting, inside or outside
    release.countDown()                                    // 3. let the load finish
    callers.forEach { it.join() }
    assertThat(loads.get()).isEqualTo(1)                   // 4. one load served all eight
}

fun awaitParked(threads: List<Thread>, n: Int) {
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
    while (threads.count { it.state == Thread.State.BLOCKED || it.state == Thread.State.WAITING } < n) {
        check(System.nanoTime() < deadline) { "callers never queued up" }
        Thread.sleep(5)                                    // polling with a deadline: never a bare guess
    }
}"""

J_DRILL = """@Test
@Timeout(10)
void countsEveryIncrement() throws Exception {
    Counter counter = new Counter();
    CountDownLatch go = new CountDownLatch(1);
    List<Thread> threads = new ArrayList<>();
    for (int t = 0; t < 8; t++) {
        Thread th = new Thread(() -> {
            try { go.await(); } catch (InterruptedException e) { return; }
            for (int i = 0; i < 50_000; i++) counter.increment();
        });
        th.start();
        threads.add(th);
    }
    go.countDown();
    for (Thread th : threads) th.join();
    assertThat(counter.total()).isEqualTo(8 * 50_000);
}"""
K_DRILL = """@Test
@Timeout(10)
fun `counts every increment from 8 threads`() {
    val counter = Counter()
    val go = CountDownLatch(1)
    val threads = List(8) { thread { go.await(); repeat(50_000) { counter.increment() } } }
    go.countDown()
    threads.forEach { it.join() }
    assertThat(counter.total()).isEqualTo(8 * 50_000)
}"""

J_CMP = """@RepeatedTest(5)                                   // a race test is a sample: take several
@Timeout(10)                                       // a deadlock fails the test instead of hanging the build
void noRefundIsLost() throws Exception {
    RefundLedger ledger = new RefundLedger(Map.of("pay-1", 10_000L));
    AtomicLong approved = new AtomicLong();
    CountDownLatch go = new CountDownLatch(1);
    List<Thread> threads = new ArrayList<>();
    for (int t = 0; t < 8; t++) {                  // more threads than cores
        Thread th = new Thread(() -> {
            try { go.await(); } catch (InterruptedException e) { return; }
            for (int i = 0; i < 2_000; i++) if (ledger.refund("pay-1", 1)) approved.incrementAndGet();
        });
        th.start();
        threads.add(th);
    }
    go.countDown();                                // the starting gun
    for (Thread th : threads) th.join();
    assertThat(approved.get()).isEqualTo(10_000);  // an invariant, not a timing
    assertThat(ledger.refunded("pay-1")).isEqualTo(10_000);
}"""
K_CMP = """@RepeatedTest(5)                                   // a race test is a sample: take several
@Timeout(10)                                       // a deadlock fails the test instead of hanging the build
fun `no refund is lost`() {
    val ledger = RefundLedger(mapOf("pay-1" to 10_000L))
    val approved = AtomicLong()
    val go = CountDownLatch(1)
    val threads = List(8) {                        // more threads than cores
        thread {
            go.await()
            repeat(2_000) { if (ledger.refund("pay-1", 1)) approved.incrementAndGet() }
        }
    }
    go.countDown()                                 // the starting gun
    threads.forEach { it.join() }
    assertThat(approved.get()).isEqualTo(10_000L)  // an invariant, not a timing
    assertThat(ledger.refunded("pay-1")).isEqualTo(10_000L)
}"""

FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="One stress round: a fresh state, eight actor threads released together by a start latch, join all, check the invariant, then repeat for the next round">'
    '<rect class="box" x="20" y="80" width="130" height="50" rx="8"/>'
    '<text class="t" x="85" y="102" text-anchor="middle">setup()</text><text class="t-s t-m" x="85" y="120" text-anchor="middle">fresh state</text>'
    '<line class="ln" x1="150" y1="105" x2="186" y2="105" marker-end="url(#arr)"/>'
    '<rect class="box" x="190" y="30" width="200" height="150" rx="8"/>'
    '<line class="ln-a" x1="210" y1="44" x2="210" y2="166"/>'
    '<text class="t-s t-a" x="300" y="48" text-anchor="middle">start latch: go!</text>'
    + "".join(f'<rect class="box-a" x="220" y="{y}" width="150" height="20" rx="6"/><text class="t-s" x="295" y="{y + 15}" text-anchor="middle">actor x {n}</text>' for y, n in ((60, "2,000"), (88, "2,000"), (116, "2,000")))
    + '<text class="t-s t-m" x="295" y="162" text-anchor="middle">8 threads at once</text>'
    '<line class="ln" x1="390" y1="105" x2="426" y2="105" marker-end="url(#arr)"/>'
    '<rect class="box" x="430" y="80" width="100" height="50" rx="8"/>'
    '<text class="t" x="480" y="110" text-anchor="middle">join all</text>'
    '<line class="ln" x1="530" y1="105" x2="556" y2="105" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="560" y="80" width="105" height="50" rx="8"/>'
    '<text class="t" x="612" y="102" text-anchor="middle">invariant</text><text class="t-s" x="612" y="120" text-anchor="middle">holds?</text>'
    '<path class="ln-d" d="M612 132 V200 H85 V134" fill="none" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="348" y="220" text-anchor="middle">repeat for many rounds; count the rounds that failed</text>'
    '</svg>'
)

L = {
 "id": "conc-13",
 "title": "Testing and debugging concurrent code",
 "minutes": 38,
 "goal": "By the end you can write a stress test that reliably catches a race, replace sleeps in tests with latches, read what jcstress reports, and find a stuck or slow thread with thread dumps and JFR.",
 "warmup": {
  "q": "A test starts 2 threads that each call a racy `hit()` 1,000 times, then checks the total. It passes 20 runs out of 20. What is the most likely reason?",
  "options": ["The counter is thread-safe after all", "The first thread usually finishes before the second one starts, so they never overlap", "The JIT fixed the race", "JUnit runs threads one at a time"],
  "answer": 1,
  "why": "1,000 increments take microseconds, about as long as starting a thread. The first thread is often done before the second begins, so there is no interleaving to go wrong. The test proves nothing. Make the threads start together with a latch, use more of them, and run far more iterations, as this lesson shows."
 },
 "sections": [
  {
   "h": "A concurrency test has to make threads collide",
   "body": "A race only shows up when threads overlap at the wrong moment. A test that doesn't force overlap is a single-threaded test with extra steps. Five habits turn it into a stress test:\n\n- Hold every thread at a start latch and release them together. Lesson 3 of this track built this.\n- Use more threads than cores, so the scheduler interleaves them.\n- Run many operations per thread, so the threads overlap for a long time.\n- Run many rounds with a fresh state each time. One round is one sample of the interleavings.\n- Check an invariant when all threads are done: totals that must add up, an amount that must never be exceeded. Never assert on timings.\n\nThe lab packs those habits into a small harness, shaped like jcstress: a setup that builds fresh state, an actor that every thread runs over and over, and an invariant checked after `join()`. The figure shows one round.\n\n" + pair(J_STRESS, K_STRESS) + "\n\nEight threads try 2,000 one-cent refunds each against 10,000 cents captured, so a correct ledger approves exactly 10,000. The racy ledger in the lab approves all 16,000.\n\nTwo more rules keep these tests from hurting you. Put a timeout on every one, with JUnit's `@Timeout` or `assertTimeoutPreemptively`, so a deadlock fails the test in seconds instead of hanging CI for an hour. And remember what a pass means: this run found no failure. A stress test can prove that a race exists. It can never prove that one doesn't, which is why the design rules from earlier lessons matter more than any test.",
   "figure": {"svg": FIG, "caption": "One round of a stress test: fresh state, all actors released together, join, check the invariant. Repeat for many rounds."},
   "try": {
    "title": "The same bug, tested two ways",
    "minutes": 3,
    "steps": [
     "Read `NaiveVsStress`. It tests the racy counter from lesson 3 twenty times the usual way (2 threads, 1,000 hits, no start line), then twenty times as a stress test (8 threads, 100,000 hits, start latch).",
     "Predict how many runs of each fail.",
     "Run it two or three times."
    ],
    "code": code("NaiveVsStress"),
    "expect": "The naive test fails rarely, 0 to 6 runs of 20 here, and a different number each time. The stress test fails 20 of 20. Same code, same bug. Only the second test is worth having in CI."
   }
  },
  {
   "h": "Replace sleeps with latches, and guesses with deadlines",
   "body": "`Thread.sleep` in a test is a guess about how long something takes. On your laptop the guess is generous and the test is slow. On a busy CI machine the guess is too short and the test fails for no reason. Both are bad, and the second teaches the team to ignore red builds.\n\nWait for the event itself, and use the timeout only as a deadline far above any real duration:\n\n" + pair(J_SLEEP, K_SLEEP) + "\n\nThe latch version is fast when things are fast and patient when the machine is slow. It also gives you a clear failure, \"not settled within 10 s\", instead of a wrong status.\n\nThe same tools let you hold a thread at a known point, which makes many concurrency tests deterministic. Give the code under test a fake dependency that blocks on a latch:\n\n" + pair(J_FAKE, K_FAKE) + "\n\nNow the test can wait on `inCall`, then check what other threads see while one is known to be inside the call. With the `IssuerGate` from lesson 10 set to one permit, a second caller with a 100 ms limit must time out. Then the test opens `release` and checks the clean-up. No sleeps, no luck.\n\nWhen there's no hook to wait on, poll for the condition with a short sleep and an overall deadline, rather than sleeping once and hoping. Checking `Thread.getState()` until the threads you expect are `BLOCKED` or `WAITING` is a common way to know they have queued up. The worked example uses it.",
   "try": {
    "title": "Make a test flaky on purpose",
    "minutes": 3,
    "steps": [
     "Read `SleepVsLatch`. Eight threads burn every core, like a busy CI box. A background worker settles a payment in about 2 ms.",
     "One test sleeps 3 ms and checks; the other waits on a latch for up to 5 seconds. Each runs 100 times. Predict the failure counts.",
     "Run it, then change the sleep to 10 ms and run it again."
    ],
    "code": code("SleepVsLatch"),
    "expect": "The sleep version failed in about a quarter of the runs here (24 and 32 of 100). The latch version failed 0 times. A 10 ms sleep fails less often, but it can still fail, and it makes every run slower."
   }
  },
  {
   "h": "Let jcstress search the interleavings for you",
   "body": "Some bugs need millions of attempts and a weak-memory CPU to show up at all. A weak-memory CPU, such as ARM, may let other cores see one core's writes in a different order than it made them. jcstress is the OpenJDK harness for exactly that. It runs tiny tests millions of times, with careful control over how threads start and where state lives, and counts every outcome it sees. The latest tagged release is 0.16, from February 2023; the master branch is 0.17-SNAPSHOT.\n\nA test is a class with shared `@State`, two or more `@Actor` methods that run at the same time, and a result object, here `II_Result` with two `int` fields. `@Outcome` annotations say which results are allowed:\n\n```java solo\n" + JCSTRESS + "\n```\n\nIt is a Java-only tool: tests are processed by an annotation processor at build time, so there is no Kotlin twin here.\n\nThe outcome labels are the part to learn:\n\n- `ACCEPTABLE` is a correct result.\n- `ACCEPTABLE_INTERESTING` is allowed but worth seeing, usually the race the test is about. Here, \"1, 1\" means both actors read 0: an increment was lost.\n- `FORBIDDEN` must never happen. If jcstress observes it even once, the test fails.\n\nFor each test jcstress reports every observed outcome with how many times it occurred and its label. Results depend on the hardware: x86 keeps stores in order, so some memory-model anomalies that ARM machines (Apple Silicon, AWS Graviton) show regularly may never appear on an Intel laptop. Interesting means allowed, not guaranteed to appear.\n\nThe README documents a Maven archetype and no official Gradle setup, so try it in a separate Maven project. The jcstress samples on GitHub are a course in themselves; each has the outcomes it expects in its source.",
   "try": {
    "title": "Run a jcstress test (optional, needs Maven and network)",
    "minutes": 6,
    "steps": [
     "In a scratch folder outside the labs, generate a jcstress project with the archetype command below (from the jcstress README).",
     "Add `RefundCounterRace` from this section to the generated sources, build, and run only that test with `-t`.",
     "Find the line for outcome `1, 1`. Then change `int refunds` to an `AtomicInteger` and both actors to `incrementAndGet()`, rebuild and run again."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": BASH_JC, "run": ""},
    "expect": "The first run reports `1, 2` and `2, 1` as acceptable and `1, 1` as interesting, observed some percentage of the time (the jcstress samples record a few percent for this kind of test; your count will differ). With `AtomicInteger`, `1, 1` is never observed. If you mark `1, 1` as `FORBIDDEN` in the racy version, the test fails."
   },
   "refs": [
    {"title": "jcstress (README: archetype, running, modes)", "url": "https://github.com/openjdk/jcstress", "kind": "docs"},
    {"title": "jcstress samples", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples", "kind": "read"}
   ]
  },
  {
   "h": "When it hangs, take dumps; when it's slow, record JFR",
   "body": "In production you debug with what the JVM can tell you about itself. Two tools cover most cases.\n\nA thread dump answers \"where is every thread right now, and what is it waiting for\". `jcmd <pid> Thread.print -l` prints each thread's state and stack, the `java.util.concurrent` locks it owns, and a deadlock report if there is a cycle (lesson 6 of this track). The state line is the first thing to read:\n\n" + STATES + "\n\nOne dump is a photo. Take three, a few seconds apart. A thread in the same frame each time is stuck; a thread that moves is busy. Thirty threads `WAITING (parking)` on the same lock in every dump send you looking for its owner, which `-l` names. For tooling, `Thread.dump_to_file -format=json` writes JSON; on JDK 21 it has only names and stacks per thread, and from JDK 25 it adds state and lock fields.\n\nJava Flight Recorder answers \"what were threads waiting on over the last minute, and for how long\". It is built into the JVM and cheap enough for production. `jdk.JavaMonitorEnter` records each wait to enter a `synchronized` block longer than a threshold, with the monitor's class, the duration and the previous owner. `jdk.JavaMonitorWait` covers `Object.wait()`, and `jdk.ThreadPark` covers `ReentrantLock` and the other `java.util.concurrent` waits. JDK 25 added `jdk.JavaMonitorStatistics` and `jdk.JavaMonitorNotify`.\n\n```bash\n" + BASH_DIAG + "\n```\n\nNo JFR event reports deadlocks; for those, use a dump or `ThreadMXBean`. In a container the JVM is often PID 1, so `jcmd 1 Thread.print` inside the pod is the quickest start.",
   "try": {
    "title": "Record contention with JFR",
    "minutes": 4,
    "steps": [
     "Read `JfrContention`. It starts a JFR recording from inside the program, runs six threads for one second (three fight over a monitor, three over a `ReentrantLock`), then reads the recording back.",
     "Run it. Which event type does each kind of lock produce?",
     "Run `jfr summary` and then `jfr print --events jdk.JavaMonitorEnter` on the file the demo printed. Find `previousOwner`."
    ],
    "code": code("JfrContention"),
    "expect": "Two lines: `JavaMonitorEnter on java.lang.Object` for the `synchronized` threads and `ThreadPark on java.util.concurrent.locks.ReentrantLock$NonfairSync` for the explicit lock, each with a hundred or more events and about a second of total waiting. `jfr print` shows each event's duration, `monitorClass`, `previousOwner` (the thread that held the monitor) and the waiting thread's stack."
   }
  }
 ],
 "analogy": "A stress test is a crash test: you don't learn anything by driving the car gently around the car park; you build a fresh car, drive it into the wall at speed, inspect it, and do it again many times. Replacing sleeps with latches is the difference between \"wait ten minutes, then check whether the pizza arrived\" and \"open the door when the bell rings\". jcstress is a test track that drives millions of cars in slightly different ways and records every kind of damage. A thread dump is a photo of the traffic; JFR is the traffic camera's recording. The analogy breaks at the crash test: a car that survived a thousand crashes really is strong. Code that passed a thousand stress rounds may still have a race the test never hit.",
 "in_your_world": "In a Quarkus service, keep stress tests in their own JUnit tag so the normal build stays fast, and run them on CI where machines are busy, since busy machines interleave more. Integration tests with Testcontainers, Kafka and Oracle check wiring, not thread safety; they run too few concurrent operations to find a race. When a pod stops answering, take three thread dumps before anyone restarts it: `kubectl exec <pod> -- jcmd 1 Thread.print -l` works when the JVM is PID 1. When latency creeps up without errors, start a JFR recording on the pod and look at `JavaMonitorEnter` and `ThreadPark`: a lock that every request waits on shows up as hundreds of events on the same class.",
 "mistake": "The most common mistake is fixing a flaky concurrency test by tuning it until it passes: a longer sleep, a retry annotation, a CI rule that reruns failures. Flakiness in a concurrency test is often the only symptom a real race ever shows before production. Every retry hides it a little better. The fix is to find out why the test is flaky. If the test guesses at timing, replace the sleep with a latch or a deadline-bounded wait. If the code is racy, the test just did its job, so fix the code and keep the test.",
 "compare": {
  "title": "The same stress test in Java and Kotlin",
  "java": {"title": "Java (JUnit 6)", "src": J_CMP},
  "kotlin": {"title": "Kotlin (JUnit 6)", "src": K_CMP},
  "note": "JUnit, AssertJ and the latches work the same from both languages. Kotlin removes ceremony: `thread { }` starts a thread in one line, `List(8) { ... }` collects them, and with no checked exceptions there is no `try`/`catch` around `go.await()`. Two details differ. Backtick test names read like specs. And AssertJ needs `10_000L` in Kotlin: `assertThat(aLong).isEqualTo(10_000)` would pass an `Int`, which picks the `Object` overload and fails because `Long` 10,000 isn't equal to `Integer` 10,000. For coroutine code, Kotlin has a tool Java lacks: kotlinx-coroutines-test runs suspending code on virtual time, so tests of delays and timeouts run instantly and deterministically. The coroutines track covers it."
 },
 "worked": {
  "title": "Turn a flaky \"loads once\" test into a deterministic one",
  "steps": [
   {"say": "This test is meant to prove that `BinCache` from lesson 9 loads a BIN once when eight callers ask together. Read it and decide what it actually tests.",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "It tests the scheduler. The loader is so fast that the threads rarely overlap, so the racy get-then-put cache passes too. And on a slow machine the threads might not have run at all within 100 ms, so `loads` is 0 and a correct cache fails. The fix is to control the timing: hold the first load inside the loader until every caller is known to be waiting, then let it go.", "code": "", "lang": ""},
   {"say": "Here is the deterministic version, with subgoal labels. The loader blocks on a latch, and the test polls thread states, with a deadline, until all eight callers are parked.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why this version fails on the racy cache every time. Answer: with get-then-put, every caller misses and enters the loader, so all eight end up waiting on `release` inside it, and step 2 is satisfied. When the test opens the latch, all eight loads finish and `loads` is 8. With `computeIfAbsent`, one caller is inside the loader and the other seven are `BLOCKED` on the map's bin, so `loads` is 1. The outcome no longer depends on luck, only on the code.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A stress harness that catches races, and a refund race to fix",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Stress.java", f"{lab}/main/{P}/RefundLedger.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l13.*'",
  "steps": [
   "Run the tests. Six of seven fail. The five `Stress` tests hit `UnsupportedOperationException`. The ledger load test approves 16,000 one-cent refunds against 10,000 captured.",
   "Write `Stress.failingRounds`. For each round: call `setup`, create `ready` and `go` latches, start `threads` threads that count down `ready`, wait on `go`, then run the actor `perThread` times. Wait on `ready`, count down `go`, join every thread, then test the invariant and count the failures.",
   "Run the tests again. The `Stress` tests should pass, including the two that point your harness at racy code (a `volatile` counter and a check-then-act ledger) and expect it to find failures.",
   "Fix `RefundLedger.refund`: do the check and the update inside one `refunded.compute(...)` call, and call `writeAuditLine()` after it, only when the refund was approved.",
   "Run the tests until all seven pass, then twice more."
  ],
  "hints": [
   "The start line is the `Hammer` from lesson 3 of this track. Make the actor threads daemons, so a stuck actor can't keep the JVM alive.",
   "The `join()` does two jobs: it waits, and it makes everything the actors wrote visible to the thread that checks the invariant.",
   "Inside `compute`, return `already` unchanged (it may be `null`) to reject a refund. Record the decision in a local `boolean[1]` or an `AtomicBoolean`, because a lambda can't assign a local variable."
  ],
  "done_when": "All seven tests in `ConcurrencyTestingTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A stress test from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a JUnit test that checks a `Counter` (with `increment()` and `total()`) loses nothing when 8 threads each call `increment()` 50,000 times. Check: do the threads start together, does a deadlock fail the test, and is your assertion an invariant rather than a timing?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "A stress test forces overlap: a start latch, more threads than cores, many operations, many rounds with fresh state, and an invariant checked after `join()`.",
  "Every concurrency test gets a timeout. A pass means \"not found this time\", never \"proven correct\".",
  "Replace `Thread.sleep` with latches, futures or deadline-bounded polling. A fake that blocks on a latch holds a thread at a known point.",
  "jcstress runs tiny tests millions of times and labels outcomes `ACCEPTABLE`, `ACCEPTABLE_INTERESTING` or `FORBIDDEN`; any forbidden outcome fails the test.",
  "Thread dumps show where threads are and what they wait for; take several, seconds apart. JFR's `JavaMonitorEnter` and `ThreadPark` show contention over time."
 ],
 "quiz": [
  {"q": "Which change makes a test most likely to catch a lost update in a counter?",
   "options": ["Add `Thread.sleep(10)` before the assertion", "Release 8+ threads together with a start latch, give each many iterations, and repeat the round many times", "Run the test with `-Xint`", "Run the test first in the suite"],
   "answer": 1, "why": "Lost updates need threads running the same code at the same moment, over and over. The latch lines them up, many iterations keep them overlapping, and many rounds take many samples. A sleep before the assertion changes nothing about overlap."},
  {"q": "A test does `worker.submit(p); Thread.sleep(50); assertTrue(store.isSettled(p));` and fails about once in 50 CI runs. What is the best fix?",
   "options": ["Increase the sleep to 500 ms", "Mark the test to retry twice on failure", "Wait for the settled event with a latch (or poll with a deadline) and a generous timeout, then assert", "Disable it on CI"],
   "answer": 2, "why": "The test guesses how long settling takes. Waiting for the event makes it as fast as the code and patient on a slow machine, and a timeout far above any real duration only trips when something is really wrong. A longer sleep is slower and still a guess; a retry hides real races too."},
  {"q": "A jcstress run shows outcome `1, 1` marked `ACCEPTABLE_INTERESTING` and observed in 4% of samples. What does that mean?",
   "options": ["The test failed", "The outcome is allowed by the test's annotations but marks the interesting case, here the lost update, and it really happened in 4% of samples", "jcstress could not decide", "The outcome only appears on ARM"],
   "answer": 1, "why": "Interesting outcomes are permitted results that the test author wants highlighted, typically the race being demonstrated. Only an observed `FORBIDDEN` outcome fails a test. The frequency depends on hardware and load, so another machine may show a different number, or none."},
  {"q": "From explicit locks: three thread dumps, 5 seconds apart, each show 30 threads `WAITING (parking)` with `parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`. What do you look at next?",
   "options": ["Which thread owns that lock: run `Thread.print -l` and find it under \"Locked ownable synchronizers\", then read its stack", "The GC log", "Restart the pod and see whether it happens again", "Nothing: `WAITING` threads are idle and harmless"],
   "answer": 0, "why": "Waiters on an explicit lock are parked, so they show as `WAITING`, not `BLOCKED`, and three identical dumps say they're stuck, not busy. The owner explains why: it may be in a slow call while holding the lock, or it may have left without `unlock()`. `-l` lists the `java.util.concurrent` locks each thread owns.",
   "from": "conc-07"},
  {"q": "Payments are slow under load but nothing deadlocks. Which tool shows which monitors threads waited on, for how long, and which thread held each one before them?",
   "options": ["A single `jcmd Thread.print`", "`ThreadMXBean.findDeadlockedThreads()`", "The GC log", "A JFR recording with `jdk.JavaMonitorEnter` events (and `jdk.ThreadPark` for `java.util.concurrent` locks)"],
   "answer": 3, "why": "`JavaMonitorEnter` records each wait above a threshold with the monitor class, the duration and `previousOwner`, over the whole recording. A single dump is one instant. The deadlock check only finds cycles, and the GC log is about memory."}
 ],
 "flashcards": [
  {"front": "Why hold the threads of a stress test behind a start latch?", "back": "So they all begin at the same moment and overlap. Without it, early threads can finish before late ones start, and the race never happens."},
  {"front": "Why does every concurrency test need `@Timeout` or `assertTimeoutPreemptively`?", "back": "So a deadlock or a lost wake-up fails the test in seconds instead of hanging the build."},
  {"front": "What is wrong with `Thread.sleep(50)` before an assertion in a test?", "back": "It guesses at timing: flaky on busy machines, slow on idle ones. Wait for the event with a latch or a deadline-bounded poll instead."},
  {"front": "jcstress: what does `ACCEPTABLE_INTERESTING` mean?", "back": "The outcome is allowed, but the author flags it as worth seeing, usually the race the test demonstrates."},
  {"front": "jcstress: what happens if a `FORBIDDEN` outcome is observed even once?", "back": "The test fails."},
  {"front": "How do you tell a stuck thread from a busy one with thread dumps?", "back": "Take several dumps a few seconds apart. A thread in the same frame every time is stuck; one whose stack changes is busy."},
  {"front": "Which JFR events show lock contention?", "back": "`jdk.JavaMonitorEnter` for `synchronized` (with monitor class, duration and previous owner), `jdk.JavaMonitorWait` for `Object.wait()`, `jdk.ThreadPark` for `java.util.concurrent` locks."}
 ],
 "terms": [
  {"term": "Stress test", "plain": "A test that runs code on many threads at once, many times, to make races show up."},
  {"term": "Invariant", "plain": "A fact that must hold whatever the interleaving, such as \"refunds never exceed captures\"."},
  {"term": "Flaky test", "plain": "A test that passes or fails without any code change, often because it guesses at timing."},
  {"term": "jcstress", "plain": "The OpenJDK harness that runs tiny concurrent tests millions of times and counts each outcome."},
  {"term": "Outcome", "plain": "One possible result of a jcstress test, labelled acceptable, interesting or forbidden."},
  {"term": "Thread dump", "plain": "A snapshot of every thread's state and stack, from `jcmd <pid> Thread.print`."},
  {"term": "JFR", "plain": "Java Flight Recorder: low-overhead event recording built into the JVM, read with the `jfr` tool."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our concurrency test has been green for months, so the class is thread-safe.\" Explain what a green stress test does and doesn't tell you, and what you'd check about the test itself.",
  "answer": "A green run means the test didn't happen to hit a bad interleaving, not that none exists. Races depend on timing, hardware and load, so a test can stay green for months and the race still fire in production. I'd check that the test actually makes threads collide: a start latch, more threads than cores, enough operations per thread, many rounds with fresh state, and an assertion on an invariant rather than timing. I'd check that it has a timeout so a deadlock would fail it. And I'd still review the class against the rules: what state is shared, which lock or atomic protects each compound action, and whether anything calls out while holding a lock. Tests find races; design prevents them."
 },
 "deeper": {
  "minutes": 10,
  "body": "jcstress has more than actors and outcomes. An `@Arbiter` method runs after all actors have finished and can record the final state into the result, which suits tests like \"after two increments, is the counter 2?\". Termination tests, marked `@JCStressTest(Mode.Termination)` with a `@Signal` method, check whether a thread ever notices a signal; the sample `BasicJMM_04_Progress` uses this to show whether a spin loop ever sees a field change. The runner has modes too: the README mentions `-m quick`, which many CI setups use to keep runs short.\n\nFor Kotlin code, JetBrains' Lincheck library tests concurrent data structures by running operations from several threads, including in a model-checking mode that explores interleavings systematically, and then checking that the results match some sequential order of the same operations. It is worth a look before you write a lock-free structure.\n\nJFR is not only a file format. `jdk.jfr.consumer.RecordingStream`, added in JDK 14 (JEP 349), streams events to your code while the program runs. A service can subscribe to `jdk.JavaMonitorEnter` and export a metric when waits on one class exceed a budget.\n\nFinally, the JDK's own tools can be scripted. `jcmd <pid> help` lists every diagnostic command a JVM supports, and the list changes between versions: JDK 24 added `Thread.vthread_scheduler` and `Thread.vthread_pollers` for virtual threads, and from JDK 24 `Thread.print` also includes virtual threads that are mounted on a carrier. The virtual threads track uses those."
 },
 "sources": [
  {"title": "jcstress README", "url": "https://github.com/openjdk/jcstress"},
  {"title": "jcstress samples", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples"},
  {"title": "JFR event definitions, metadata.xml at jdk-27-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml"},
  {"title": "jcmd diagnostic commands, diagnosticCommand.hpp at jdk-27-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 12 (testing concurrent programs)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-13.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
