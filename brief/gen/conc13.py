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
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

# ---------------------------------------------------------------- code samples in the prose
J_NAIVE = """// Naive: two threads that may never meet
Counter c = new Counter();
Thread a = new Thread(() -> { for (int i = 0; i < 1_000; i++) c.hit(); });
Thread b = new Thread(() -> { for (int i = 0; i < 1_000; i++) c.hit(); });
a.start(); b.start();
a.join(); b.join();
assertThat(c.count).isEqualTo(2_000);"""
K_NAIVE = """// Naive: two threads that may never meet
val c = Counter()
val a = thread { repeat(1_000) { c.hit() } }
val b = thread { repeat(1_000) { c.hit() } }
a.join(); b.join()
assertThat(c.count).isEqualTo(2_000)"""

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

J_SLEEP_BAD = """// Naive: hopes 50 ms is enough on every machine, and is slow on all of them
worker.submit(refund);
Thread.sleep(50);
assertThat(ledger.status(refund.id())).isEqualTo(RECORDED);"""
K_SLEEP_BAD = """// Naive: hopes 50 ms is enough on every machine, and is slow on all of them
worker.submit(refund)
Thread.sleep(50)
assertThat(ledger.status(refund.id)).isEqualTo(RECORDED)"""
J_SLEEP_GOOD = """// Fixed: wait for the event itself, with a deadline far above any real duration
CountDownLatch recorded = new CountDownLatch(1);
ledger.onRecorded(id -> recorded.countDown());
worker.submit(refund);
assertThat(recorded.await(10, TimeUnit.SECONDS)).isTrue();
assertThat(ledger.status(refund.id())).isEqualTo(RECORDED);"""
K_SLEEP_GOOD = """// Fixed: wait for the event itself, with a deadline far above any real duration
val recorded = CountDownLatch(1)
ledger.onRecorded { recorded.countDown() }
worker.submit(refund)
assertThat(recorded.await(10, TimeUnit.SECONDS)).isTrue()
assertThat(ledger.status(refund.id)).isEqualTo(RECORDED)"""

J_FAKE = """class SlowBank implements Bank {
    final CountDownLatch inCall = new CountDownLatch(1);
    final CountDownLatch release = new CountDownLatch(1);

    @Override
    public Approval check(Payment p) throws InterruptedException {
        inCall.countDown();          // 1. tell the test: a thread is inside the call
        release.await();             // 2. hold it here until the test says go
        return Approval.YES;
    }
}"""
K_FAKE = """class SlowBank : Bank {
    val inCall = CountDownLatch(1)
    val release = CountDownLatch(1)

    override fun check(p: Payment): Approval {
        inCall.countDown()           // 1. tell the test: a thread is inside the call
        release.await()              // 2. hold it here until the test says go
        return Approval.YES
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

JCS_OUT = """  RESULT      SAMPLES     FREQ       EXPECT  DESCRIPTION
    1, 1  707,991,481   36.34%  Interesting  both read 0: one increment lost
    1, 2  675,088,320   34.65%   Acceptable  actor1 went first
    2, 1  565,287,693   29.01%   Acceptable  actor2 went first"""

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
| `RUNNABLE` | Running, ready to run, or waiting inside the operating system for input, such as data from the network |
| `BLOCKED (on object monitor)` | Waiting to enter a `synchronized` block that another thread holds |
| `WAITING (parking)` | Parked by `java.util.concurrent`: a lock, latch, queue or semaphore; the `parking to wait for` line names it |
| `WAITING (on object monitor)` | Inside `Object.wait()` |
| `TIMED_WAITING` | The same, with a timeout, or in `sleep` |"""

DUMP = """"till-0" #23 [14677] prio=5 os_prio=0 cpu=0.24ms elapsed=2.54s ...
   java.lang.Thread.State: TIMED_WAITING (sleeping)
	at java.lang.Thread.sleep(java.base@25.0.5.0.3/Thread.java:540)
	at Stuck.slowCall(Stuck.java:17)
	...
   Locked ownable synchronizers:
	- <0x000000073781f198> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)

"till-1" #24 [14678] prio=5 os_prio=0 cpu=0.59ms elapsed=2.34s ...
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@25.0.5.0.3/Native Method)
	- parking to wait for  <0x000000073781f198> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
	...
	at java.util.concurrent.locks.ReentrantLock.lock(java.base@25.0.5.0.3/ReentrantLock.java:323)
	at Stuck.lambda$main$1(Stuck.java:12)"""

JFR_SUM = """JavaMonitorEnter on java.lang.Object                                       3 events,   1975 ms waiting
ThreadPark on java.util.concurrent.locks.ReentrantLock$NonfairSync       326 events,   1728 ms waiting"""
JFR_EVT = """jdk.JavaMonitorEnter {
  startTime = 17:45:51.586 (2026-11-16)
  duration = 986 ms
  monitorClass = java.lang.Object (classLoader = bootstrap)
  previousOwner = "ledger-2" (javaThreadId = 28)
  address = 0x7FB344000F20
  eventThread = "ledger-4" (javaThreadId = 30)
  ...
}"""

J_W1 = """// Naive: tests the scheduler, not the cache
@Test
void loadsOnce() throws Exception {
    AtomicInteger loads = new AtomicInteger();
    PriceCache cache = new PriceCache(item -> { loads.incrementAndGet(); return 250L; });
    for (int i = 0; i < 8; i++) new Thread(() -> cache.priceOf("bread")).start();
    Thread.sleep(100);                                   // "they should be done by now"
    assertThat(loads.get()).isEqualTo(1);
}"""
K_W1 = """// Naive: tests the scheduler, not the cache
@Test
fun `loads once`() {
    val loads = AtomicInteger()
    val cache = PriceCache { loads.incrementAndGet(); 250L }
    repeat(8) { thread { cache.priceOf("bread") } }
    Thread.sleep(100)                                    // "they should be done by now"
    assertThat(loads.get()).isEqualTo(1)
}"""
J_W2 = """@Test
@Timeout(10)
void loadsOnceWhileOthersWait() throws Exception {
    AtomicInteger loads = new AtomicInteger();
    CountDownLatch inLoader = new CountDownLatch(1), release = new CountDownLatch(1);
    PriceCache cache = new PriceCache(item -> {
        loads.incrementAndGet();
        inLoader.countDown();                              // 1. a caller is inside the loader
        try { release.await(); }                           //    and stays there until we say go
        catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return 250L;
    });
    List<Thread> callers = new ArrayList<>();
    for (int i = 0; i < 8; i++) {
        Thread t = new Thread(() -> cache.priceOf("bread"));
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
    val cache = PriceCache {
        loads.incrementAndGet()
        inLoader.countDown()                               // 1. a caller is inside the loader
        release.await()                                    //    and stays there until we say go
        250L
    }
    val callers = List(8) { thread { cache.priceOf("bread") } }
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

OPENING = """Picture the refund desk at a shop. A customer who brings something back gets a refund, money paid back, and one sale can be refunded in several parts. The rule: the refunds for one sale must never add up to more than the sale. The shop's program handles refunds on several threads at once. (A thread is one path of work running beside others in one program.) So the team wrote a test: two threads ask for refunds at once, and the total must stay within the sale. It has passed every day for a year.

Then, on the first busy day of a sale, a coat that sold for 100.00 is refunded 160.00. The customer is delighted. The shop is not.

The test wasn't lying. Its two threads never met: on a quiet machine, the first finished before the second started. This lesson turns the track's "run it a few times" into a skill. We'll make test threads collide, swap sleeps for latches, let jcstress search the timings for us, and read what a stuck or slow JVM, the program that runs your Java code, can tell us. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's start with the smallest form of the problem. In Race conditions, a counter's `count++` lost updates when two threads ran it at once, because `count++` is three steps: read, add, write. Here's the kind of test most people write for it:

""" + pair(J_NAIVE, K_NAIVE) + """

The Try it runs this test twenty times against that racy counter. Then it runs a stress test, which we'll build in a moment, twenty times against the same counter:

```text
naive test  (2 threads x 1,000, no start line): failed 1 of 20 runs
stress test (8 threads x 100,000, start latch): failed 20 of 20 runs
```

Same code, same bug. The naive test caught it once in twenty runs, and in another run here, not at all. Race conditions put it this way: a race is shy around small numbers. A thousand increments take a few microseconds, about as long as starting a thread, so the first thread is often done before the second begins. On a quiet machine, the scheduler, the part of the system that decides which thread runs when, is kind to small tests. It runs them one after the other, and the bug never gets its chance.

A test that doesn't force overlap is really a single-threaded test. Five habits turn it into a **stress test**, a test that runs code on many threads at once, many times, to make races show up:

1. Hold every thread at a start line and release them together, with the start latch from Synchronizers (a `CountDownLatch` of 1 that opens for everyone at once).
2. Use more threads than cores, the parts of the processor that each run one thread at a time, so the scheduler has to switch between them.
3. Give each thread many operations, so the threads overlap for a long time.
4. Run many rounds, with fresh state each time. One round is one sample of all the possible timings.
5. When all the threads are done, check an **invariant**, a fact that must hold whatever the timing: totals that must add up, an amount that must never be passed. Never assert on how long something took.

The lab packs these habits into a small harness, a reusable piece of test code, called `Stress`. You give it a setup that builds fresh state, an actor that every thread runs over and over, and an invariant to check after `join()`. The figure shows one round. Here's the refund desk from the opening, under stress:

""" + pair(J_STRESS, K_STRESS) + """

Eight threads each try 2,000 one-cent refunds against a sale of 10,000 cents, so a correct ledger, the record that tracks the refunds, approves exactly 10,000. The racy ledger in the lab, which checks the total and then writes it in two separate steps, approves all 16,000. That's the coat refunded 160.00 on a 100.00 sale.

Two more rules keep these tests from hurting you. Put a timeout on every one, with `@Timeout` or `assertTimeoutPreemptively` from JUnit, the test library the labs use. Then a deadlock fails the test in seconds instead of hanging the whole test run for an hour. And remember what a pass means: this run found no failure. A stress test can prove that a race exists. It can never prove that none does, which is why the design rules from earlier lessons matter more than any test.

**A passing race test means "not found this time", never "can't happen".**

A stress test makes threads meet. The next trouble is a test that waits for its threads and guesses how long."""

# ---------------------------------------------------------------- section 1
S1 = """Work that happens in the background, such as recording a refund after the customer has left the desk, is hard to test. The test has to wait until the work is done, and the quickest way to wait is a nap:

""" + pair(J_SLEEP_BAD, K_SLEEP_BAD) + """

`Thread.sleep` in a test is a guess about how long something takes. On your laptop the guess is generous, so the test is slow. On a busy build server, a shared machine that runs everyone's tests, the guess is too short, and the test fails for no reason. A test like that, which passes or fails with no change to the code, is called **flaky**, and a flaky test teaches the whole team to ignore red builds.

The Try it shows how quickly a guess goes wrong. Eight threads keep every core busy, like a build server on a busy afternoon. A background worker records a refund in about 2 ms. One test sleeps 3 ms and then checks; the other waits on a latch for up to 5 seconds. Each runs 100 times:

```text
sleep(3) then assert:  failed 45 of 100
latch.await(5 s):      failed 0 of 100
```

A nap 50% longer than the work failed almost half the time. Another run here failed 14 of 100; on a busy machine, a guess is a coin toss. The fix is to wait for the event itself, and to keep the timeout only as a deadline far above any real duration:

""" + pair(J_SLEEP_GOOD, K_SLEEP_GOOD) + """

The latch version is as fast as the code when the code is fast, and patient when the machine is slow. When it does fail, it fails with a clear message, "not recorded within 10 s", instead of a wrong status.

The same tools can hold a thread at a known point, which makes many concurrency tests deterministic: they give the same result on every run. Give the code under test a fake dependency that blocks on a latch, for example a fake bank service:

""" + pair(J_FAKE, K_FAKE) + """

Now the test can wait on `inCall` and know for certain that one thread is inside the call. Plug this fake behind the `IssuerGate` from Synchronizers, the semaphore that guards the bank's card service, set to one permit. A second caller with a 100 ms limit must then time out. Finally the test opens `release` and checks that the permit came back. No sleeps, and no luck.

When there's no hook to wait on, poll: check the condition, sleep a few milliseconds, and check again, until an overall deadline passes. Checking `Thread.getState()` until the threads you expect are `BLOCKED` or `WAITING` is a common way to know they have queued up, and the worked example uses it.

**A sleep in a test is a guess. Wait for the event, and keep the timeout as a deadline.**

Latches and stress tests find the races you can provoke on purpose. Some bugs need millions of tries, and a tool built for exactly that."""

# ---------------------------------------------------------------- section 2
S2 = """Some bugs need millions of attempts to show up at all, and some need a particular kind of processor. ARM processors, such as the ones in Apple Silicon laptops and many cloud servers, may let one core see another core's writes in a different order from how they were made. Intel and AMD processors allow less of that. **jcstress** is a harness for exactly these bugs, from OpenJDK, the open-source project that builds Java itself. It runs tiny tests millions of times, with careful control over how the threads start and where the state lives, and it counts every outcome it sees. Its latest tagged release is 0.16, from February 2023, and the master branch is 0.17-SNAPSHOT.

A jcstress test is a class with shared `@State`, two or more `@Actor` methods that run at the same time, and a result object, here `II_Result`, which holds two `int` fields. `@Outcome` annotations list the results you expect and label each one. Here's the race from the first section, as two refund desks bumping one counter:

```java solo
""" + JCSTRESS + """
```

jcstress is a Java-only tool. An annotation processor, a plug-in that runs inside the compiler, turns these classes into test code at build time, so there's no Kotlin twin here.

The labels are the part to learn:

- `ACCEPTABLE` is a correct result.
- `ACCEPTABLE_INTERESTING` is allowed but worth seeing, usually the race the test is about. Here, `1, 1` means both actors read 0, so one increment was lost.
- `FORBIDDEN` must never happen. If jcstress sees it even once, the test fails.

Write down your guess: how often will `1, 1` happen? Here's a real run, on a 4-core x86 Linux machine with JDK 21. It took under two minutes:

```text
""" + JCS_OUT + """
```

Almost two billion samples, and the increment was lost in more than a third of them. That's the same bug the naive test caught once in twenty runs. jcstress doesn't hope the threads meet; it arranges for them to meet, two billion times. With an `AtomicInteger` instead of the plain `int`, a rerun on the same machine never saw `1, 1` at all, and jcstress listed no interesting results. Had we marked `1, 1` as `FORBIDDEN` in the racy version, the test would have failed.

Results depend on the hardware. x86 processors, the Intel and AMD kind, keep their writes in order, so some surprises that ARM machines show regularly, such as one thread seeing another's writes out of order, may never appear on an Intel laptop. Interesting means allowed, not guaranteed to appear. The README documents a Maven project template and no official Gradle setup, so try it in a separate Maven project. (Maven is a Java build tool, like the Gradle that runs this course's labs.) The jcstress samples on GitHub are a course in themselves. Each one has the outcomes it expects written in its source.

Tests find bugs before a program ships. When a running program misbehaves anyway, you need the JVM to tell you what its threads are doing."""

# ---------------------------------------------------------------- section 3
S3 = """Once a program runs for real, you debug it with what the JVM can tell you about itself. Two tools cover most cases, and both come with the JDK, the kit you install to build and run Java.

A **thread dump** answers "where is every thread right now, and what is it waiting for?". It's a printout of every thread's name, state and stack, the chain of method calls the thread is in the middle of. `jcmd <pid> Thread.print -l` prints one: `jcmd` is the JDK's tool for sending commands to a running JVM, and the PID is the number the operating system gives each running program. The `-l` adds the `java.util.concurrent` locks each thread owns, and the dump ends with a deadlock report if there's a cycle (Deadlock, livelock and starvation). The state line is the first thing to read:

""" + STATES + """

Here's a trimmed dump of a small program in which `till-0` takes a `ReentrantLock` and then makes a slow call while holding it, and three other tills wait for the lock. It was taken on JDK 25:

```text
""" + DUMP + """
```

Read it from the waiting side. `till-1` is parked, waiting for the lock at `...f198`. The same address appears under `till-0`'s "Locked ownable synchronizers", so `till-0` holds it, and its stack says why it's slow: it's asleep in `slowCall`, still holding the lock. That's the rule from synchronized and intrinsic locks, keep slow calls out of the lock, broken in a real program.

One dump is a photo. Take three, a few seconds apart: a thread that shows the same frame every time is stuck, and one whose stack changes is busy. In this program's third dump, four seconds later, `till-1` still showed `cpu=0.59ms`, while `elapsed` had grown from 2.34 s to 6.58 s. That's a thread that exists, waits and does nothing. For tools of your own, `Thread.dump_to_file -format=json` writes the same dump as JSON, with state and lock fields from JDK 25.

**Java Flight Recorder** (JFR) answers a different question: "what were the threads waiting for over the last minute, and for how long?". It's an event recorder built into the JVM, cheap enough to leave on in production. `jdk.JavaMonitorEnter` records each wait to enter a `synchronized` block that lasts longer than a threshold, with the lock's class, the duration and the previous owner. `jdk.JavaMonitorWait` covers `Object.wait()`, and `jdk.ThreadPark` covers `ReentrantLock` and the other `java.util.concurrent` waits.

```bash
""" + BASH_DIAG + """
```

The Try it records one second of six threads fighting, three over a `synchronized` block and three over a `ReentrantLock`, each holding its lock for 3 ms at a time. I expected hundreds of short waits for both. The `ReentrantLock` gave exactly that. The monitor, in most runs here on JDK 21 and JDK 25, gave something else. Here's one run on JDK 25:

```text
""" + JFR_SUM + """
```

Three waits for the monitor, adding up to almost two seconds. `jfr print` on the same recording shows one of the two long ones:

```text
""" + JFR_EVT + """
```

`ledger-4` waited 986 ms to get in, and the thread that held the monitor just before it was `ledger-2`. In other words, `ledger-2` released the monitor and took it straight back, over and over, while the other two threads waited for nearly the whole second. `synchronized` makes no promise of fairness, and here one thread kept the lock for almost a second: the starvation from Deadlock, livelock and starvation, now with numbers. (One busy run here split the waiting into 94 shorter events instead, so take a few recordings before you decide.) A single thread dump would have shown two `BLOCKED` threads and nothing more. The recording showed who waited, how long, and for whom.

No JFR event reports deadlocks; for those, use a dump or `ThreadMXBean`, the JDK's window onto the JVM's threads. And if your program runs in a container, a packaged and walled-off environment that many servers use, the JVM is often process 1, so `jcmd 1 Thread.print` inside the container is the quickest start."""

L = {
 "id": "conc-13",
 "title": "Testing and debugging concurrent code",
 "minutes": 40,
 "goal": "By the end you can write a stress test that reliably catches a race, replace sleeps in tests with latches, read what jcstress reports, and find a stuck or slow thread with thread dumps and JFR.",
 "opening": OPENING,
 "warmup": {
  "q": "A test starts 2 threads that each call a counter's unsafe `hit()` method 1,000 times, then checks the total. It passes 20 runs out of 20. What's the most likely reason?",
  "options": ["The counter is thread-safe after all", "The first thread usually finishes before the second one starts, so they never overlap", "The JIT compiler fixed the race", "JUnit runs threads one at a time"],
  "answer": 1,
  "why": "1,000 increments take microseconds, about as long as starting a thread. The first thread is often done before the second begins, so there's no overlap to go wrong, and the test proves nothing. Make the threads start together with a latch, use more of them, and run far more operations, as the first section shows."
 },
 "sections": [
  {
   "h": "Making test threads collide: the stress test",
   "body": S0,
   "figure": {"svg": FIG, "caption": "One round of a stress test: fresh state, all actors released together, join, check the invariant. Repeat for many rounds."},
   "try": {
    "title": "The same bug, tested two ways",
    "minutes": 3,
    "steps": [
     "Read `NaiveVsStress`. It tests the racy counter from Race conditions twenty times the usual way (2 threads, 1,000 hits, no start line), then twenty times as a stress test (8 threads, 100,000 hits, a start latch).",
     "Predict how many runs of each fail.",
     "Run it two or three times."
    ],
    "code": code("NaiveVsStress"),
    "expect": "The naive test fails rarely, 0 or 1 of 20 in runs here, and a different number each time. The stress test fails 20 of 20. Same code, same bug. Only the second test is worth keeping."
   }
  },
  {
   "h": "Replacing sleeps with latches, and guesses with deadlines",
   "body": S1,
   "try": {
    "title": "Make a test flaky on purpose",
    "minutes": 3,
    "steps": [
     "Read `SleepVsLatch`. Eight threads keep every core busy, like a busy build server. A background worker records a refund in about 2 ms.",
     "One test sleeps 3 ms and then checks; the other waits on a latch for up to 5 seconds. Each runs 100 times. Predict the failure counts.",
     "Run it. Then change the sleep to 10 ms and run it again."
    ],
    "code": code("SleepVsLatch"),
    "expect": "The sleep version failed 14 and 45 times out of 100 in two runs here. The latch version failed 0 times. A 10 ms sleep fails less often, but it can still fail, and it makes every run slower."
   }
  },
  {
   "h": "Letting jcstress search the timings for you",
   "body": S2,
   "try": {
    "title": "Run a jcstress test (optional, needs Maven and a network)",
    "minutes": 6,
    "steps": [
     "In a scratch folder outside the labs, make a jcstress project with the template command below, from the jcstress README. Maven downloads what it needs the first time.",
     "Add `RefundCounterRace` from this section to the generated sources, build, and run only that test with `-t`. A run takes a minute or two and keeps every core busy.",
     "Find the line for outcome `1, 1`. Then change `int refunds` to an `AtomicInteger` and both actors to `incrementAndGet()`, rebuild and run again."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": BASH_JC, "run": ""},
    "expect": "The first run reports `1, 2` and `2, 1` as acceptable and `1, 1` as interesting, seen in a large share of the samples (about 36% across all configurations on the 4-core machine here; your share will differ). With `AtomicInteger`, `1, 1` is never seen, and the run lists no interesting tests. If you mark `1, 1` as `FORBIDDEN` in the racy version, the test fails."
   },
   "refs": [
    {"title": "jcstress (README: archetype, running, modes)", "url": "https://github.com/openjdk/jcstress", "kind": "docs"},
    {"title": "jcstress samples", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples", "kind": "read"}
   ]
  },
  {
   "h": "When it hangs, take dumps; when it's slow, record JFR",
   "body": S3,
   "try": {
    "title": "Record contention with JFR",
    "minutes": 4,
    "steps": [
     "Read `JfrContention`. It starts a JFR recording from inside the program, runs six threads for one second (three fight over a `synchronized` block, three over a `ReentrantLock`), then reads the recording back.",
     "Predict the number of events and the total waiting time for each kind of lock. Then run it.",
     "Run `jfr summary` and then `jfr print --events jdk.JavaMonitorEnter` on the file the demo printed. Find `duration` and `previousOwner`."
    ],
    "code": code("JfrContention"),
    "expect": "`ThreadPark on java.util.concurrent.locks.ReentrantLock$NonfairSync` with about 320 events and about 1.7 seconds of waiting in total. `JavaMonitorEnter on java.lang.Object` with only a handful of events (2 to 8 in most runs here), adding up to almost two seconds: one thread kept taking the monitor back while two others waited. A busy machine can split the waiting into many shorter events. `jfr print` shows each event's `duration`, `monitorClass`, `previousOwner` and the waiting thread's stack."
   }
  }
 ],
 "compare": {
  "title": "The same stress test in Java and Kotlin",
  "java": {"title": "Java (JUnit 6)", "src": J_CMP},
  "kotlin": {"title": "Kotlin (JUnit 6)", "src": K_CMP},
  "note": "JUnit, AssertJ and the latches work the same from both languages, and the Java version is already short for what it does. Kotlin trims the ceremony: `thread { }` starts a thread in one line, `List(8) { ... }` collects them, and with no checked exceptions there's no `try` and `catch` around `go.await()`. Two details differ. Backtick test names read like specs. And AssertJ needs `10_000L` in Kotlin: `assertThat(aLong).isEqualTo(10_000)` would pass an `Int`, which picks the `Object` overload and fails, because a `Long` 10,000 isn't equal to an `Integer` 10,000. For coroutine code, Kotlin has a tool Java lacks: kotlinx-coroutines-test runs suspending code on virtual time, so tests of delays and timeouts run instantly and give the same result every run. The coroutines track covers it."
 },
 "worked": {
  "title": "Turn a flaky \"loads once\" test into a deterministic one",
  "steps": [
   {"say": "A cache keeps each answer from a slow web service, so the service is asked only once, like the caches in Concurrent collections. This test is meant to prove that `PriceCache` loads the price of bread once when eight callers ask together. Read it and decide what it actually tests.",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "It tests the scheduler. The loader is so fast that the threads rarely overlap, so a racy cache that checks with `get` and then stores with `put` passes too. And on a slow machine the threads might not have run at all within 100 ms, so `loads` is 0 and a correct cache fails. The fix is to control the timing: hold the first load inside the loader until every caller is known to be waiting, then let it go.", "code": "", "lang": ""},
   {"say": "Here's the deterministic version, with a label on each step. The loader blocks on a latch, and the test polls the thread states, with a deadline, until all eight callers are waiting.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why this version fails on the racy cache every time. Answer: with get-then-put, every caller misses and enters the loader, so all eight end up waiting on `release` inside it, and step 2 is satisfied. When the test opens the latch, all eight loads finish, and `loads` is 8. With `computeIfAbsent`, one caller is inside the loader and the other seven are `BLOCKED` on the part of the map that holds that key, so `loads` is 1. The result no longer depends on luck, only on the code.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A stress harness that catches races, and a refund race to fix",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Stress.java", f"{lab}/main/{P}/RefundLedger.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l13.*'",
  "steps": [
   "Meet the two classes. `Stress` is the harness from the first section, and you'll write it. `RefundLedger` is the refund desk: `refund(paymentId, cents)` pays back part of a payment if the total stays within what was actually paid (the code calls that the captured amount), and returns whether it did.",
   "Run the tests. Six of the seven fail. The five `Stress` tests hit `UnsupportedOperationException`, and the ledger's load test approves 16,000 one-cent refunds against 10,000 cents paid.",
   "Write `Stress.failingRounds`. For each round: call `setup`, create a `ready` latch and a `go` latch, and start `threads` threads that count down `ready`, wait on `go`, then run the actor `perThread` times. Wait on `ready`, count down `go`, join every thread, then test the invariant and count the failures.",
   "Run the tests again. The `Stress` tests should pass, including the two that point your harness at racy code (a `volatile` counter and a check-then-act ledger) and expect it to find failures.",
   "Fix `RefundLedger.refund`: do the check and the update inside one `refunded.compute(...)` call, and call `writeAuditLine()` after it, only when the refund was approved.",
   "Run the tests until all seven pass, then twice more."
  ],
  "hints": [
   "The start line is the `Hammer` from Race conditions. Make the actor threads daemons, so a stuck actor can't keep the JVM alive.",
   "The `join()` does two jobs: it waits, and it makes everything the actors wrote visible to the thread that checks the invariant.",
   "Inside `compute`, return `already` unchanged (it may be `null`) to reject a refund. Record the decision in a local `boolean[1]` or an `AtomicBoolean`, because a lambda can't assign a local variable."
  ],
  "done_when": "All seven tests in `ConcurrencyTestingTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A stress test from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a JUnit test that checks a `Counter` (with `increment()` and `total()`) loses nothing when 8 threads each call `increment()` 50,000 times. Then check: do the threads start together, does a deadlock fail the test, and is your assertion an invariant rather than a timing?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "A stress test forces overlap: a start latch, more threads than cores, many operations, many rounds with fresh state, and an invariant checked after `join()`.",
  "Every concurrency test gets a timeout. A pass means \"not found this time\", never \"can't happen\".",
  "Replace `Thread.sleep` in tests with latches or polling with a deadline. A fake that blocks on a latch holds a thread at a known point.",
  "jcstress runs tiny tests millions of times and labels each outcome `ACCEPTABLE`, `ACCEPTABLE_INTERESTING` or `FORBIDDEN`; a forbidden outcome seen even once fails the test.",
  "Thread dumps show where every thread is and what it waits for; take several, seconds apart. JFR's `JavaMonitorEnter` and `ThreadPark` events show who waited, for how long, and after whom.",
  "The limit: tests and tools find the bugs that happen. Only the design rules of this track keep them from being possible."
 ],
 "closing": "We started with a refund test that passed for a year while a coat went out at 160.00, because its threads never met. A start latch, more threads and many rounds made them collide every time. A latch replaced the sleep, jcstress counted two billion meetings, and a dump and a recording showed what the stuck and slow threads were doing.\n\nNow search your own tests for `Thread.sleep(`. Each one is a guess about timing. Replace it with a latch, or with polling that has a deadline.\n\nThat ends this track. Next, we'll look beneath the threads at memory itself, starting with a loop that never stops: how can one thread miss a write that another thread made long ago?",
 "quiz": [
  {"q": "Which change makes a test most likely to catch a lost update in a counter?",
   "options": ["Add `Thread.sleep(10)` before the assertion", "Release 8 or more threads together with a start latch, give each many operations, and repeat the round many times", "Run the test with `-Xint`, so the JIT compiler is off", "Run the test first in the suite"],
   "answer": 1, "why": "Lost updates need threads running the same code at the same moment, over and over. The latch lines them up, many operations keep them overlapping, and many rounds take many samples. A sleep before the assertion changes nothing about the overlap."},
  {"q": "A test does `worker.submit(r); Thread.sleep(50); assertTrue(ledger.isRecorded(r));` and fails about once in 50 runs on the build server. What's the best fix?",
   "options": ["Increase the sleep to 500 ms", "Mark the test to retry twice on failure", "Wait for the recorded event with a latch (or poll with a deadline) and a generous timeout, then assert", "Turn it off on the build server"],
   "answer": 2, "why": "The test guesses how long recording takes. Waiting for the event makes it as fast as the code, and patient on a slow machine, and a timeout far above any real duration only trips when something is really wrong. A longer sleep is slower and still a guess; a retry hides real races too."},
  {"q": "A jcstress run shows outcome `1, 1` marked `ACCEPTABLE_INTERESTING` and seen in 4% of samples. What does that mean?",
   "options": ["The test failed", "The outcome is allowed by the test's annotations but marks the interesting case, here the lost update, and it really happened in 4% of samples", "jcstress couldn't decide", "The outcome only appears on ARM"],
   "answer": 1, "why": "Interesting outcomes are allowed results that the test's author wants highlighted, usually the race being shown. Only a `FORBIDDEN` outcome that was seen fails a test. The share depends on the hardware and the load, so another machine may show a different number, or none."},
  {"q": "From Explicit locks: three thread dumps, 5 seconds apart, each show 30 threads `WAITING (parking)` with `parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`. What do you look at next?",
   "options": ["Which thread owns that lock: run `Thread.print -l`, find the address under \"Locked ownable synchronizers\", then read that thread's stack", "The garbage collector's log", "Restart the program and see whether it happens again", "Nothing: `WAITING` threads are idle and harmless"],
   "answer": 0, "why": "Threads waiting for an explicit lock are parked, so they show as `WAITING`, not `BLOCKED`, and three identical dumps say they're stuck, not busy. The owner explains why: it may be in a slow call while it holds the lock, or it may have left without calling `unlock()`. `-l` lists the `java.util.concurrent` locks each thread owns.",
   "from": "conc-07"},
  {"q": "The shop's program is slow when it's busy, but nothing deadlocks. Which tool shows which monitors threads waited on, for how long, and which thread held each one before them?",
   "options": ["A single `jcmd Thread.print`", "`ThreadMXBean.findDeadlockedThreads()`", "The garbage collector's log", "A JFR recording with `jdk.JavaMonitorEnter` events (and `jdk.ThreadPark` for `java.util.concurrent` locks)"],
   "answer": 3, "why": "`JavaMonitorEnter` records each wait above a threshold, with the monitor's class, the duration and `previousOwner`, over the whole recording. A single dump is one instant. The deadlock check only finds cycles, and the garbage collector's log is about memory."}
 ],
 "flashcards": [
  {"front": "Why hold the threads of a stress test behind a start latch?", "back": "So they all begin at the same moment and overlap. Without it, early threads can finish before late ones start, and the race never happens."},
  {"front": "Why does every concurrency test need `@Timeout` or `assertTimeoutPreemptively`?", "back": "So a deadlock or a lost wake-up fails the test in seconds instead of hanging the build."},
  {"front": "What's wrong with `Thread.sleep(50)` before an assertion in a test?", "back": "It guesses at timing: flaky on busy machines, slow on quiet ones. Wait for the event with a latch, or poll with a deadline."},
  {"front": "jcstress: what does `ACCEPTABLE_INTERESTING` mean?", "back": "The outcome is allowed, but the author flags it as worth seeing, usually the race the test shows."},
  {"front": "jcstress: what happens if a `FORBIDDEN` outcome is seen even once?", "back": "The test fails."},
  {"front": "How do you tell a stuck thread from a busy one with thread dumps?", "back": "Take several dumps a few seconds apart. A thread in the same frame every time is stuck; one whose stack changes is busy."},
  {"front": "Which JFR events show threads waiting for locks?", "back": "`jdk.JavaMonitorEnter` for `synchronized` (with the monitor's class, the duration and the previous owner), `jdk.JavaMonitorWait` for `Object.wait()`, and `jdk.ThreadPark` for `java.util.concurrent` locks."}
 ],
 "terms": [
  {"term": "Stress test", "plain": "A test that runs code on many threads at once, many times, to make races show up."},
  {"term": "Invariant", "plain": "A fact that must hold whatever the timing, such as \"refunds never add up to more than the sale\"."},
  {"term": "Flaky test", "plain": "A test that passes or fails without any change to the code, often because it guesses at timing."},
  {"term": "jcstress", "plain": "The OpenJDK harness that runs tiny concurrent tests millions of times and counts each outcome."},
  {"term": "Outcome", "plain": "One possible result of a jcstress test, labelled acceptable, interesting or forbidden."},
  {"term": "Thread dump", "plain": "A printout of every thread's state and stack, from `jcmd <pid> Thread.print`."},
  {"term": "JFR", "plain": "Java Flight Recorder: a low-cost event recorder built into the JVM, read with the `jfr` tool."}
 ],
 "explain_back": {
  "prompt": "A friend says: \"Our concurrency test has been green for months, so the class is thread-safe.\" Explain what a green stress test does and doesn't tell you, and what you'd check about the test itself.",
  "answer": "A green run means the test didn't happen to hit a bad timing, not that no bad timing exists. Races depend on timing, hardware and load, so a test can stay green for months and the race can still fire on a busy day. I'd check that the test really makes threads collide. It needs a start latch, more threads than cores, enough operations per thread, many rounds with fresh state, and an assertion on an invariant rather than on timing. I'd check that it has a timeout, so a deadlock would fail it. And I'd still review the class against the rules of this track: what state is shared, which lock or atomic protects each compound action, and whether anything calls out while holding a lock. Tests find races; design prevents them."
 },
 "deeper": {
  "minutes": 10,
  "body": "jcstress has more than actors and outcomes. An `@Arbiter` method runs after all actors have finished and can record the final state into the result, which suits tests like \"after two increments, is the counter 2?\". Termination tests, marked `@JCStressTest(Mode.Termination)` with a `@Signal` method, check whether a thread ever notices a signal; the sample `BasicJMM_04_Progress` uses this to show whether a spin loop ever sees a field change. The runner has modes too: the README mentions `-m quick`, which many build servers use to keep runs short.\n\nFor Kotlin code, JetBrains' Lincheck library tests concurrent data structures by running operations from several threads, including in a model-checking mode that explores the possible timings one by one. Then it checks that the results match some one-at-a-time order of the same operations. It's worth a look before you write a lock-free structure.\n\nJFR is not only a file format. `jdk.jfr.consumer.RecordingStream`, added in JDK 14 (JEP 349), streams events to your code while the program runs. A service can subscribe to `jdk.JavaMonitorEnter` and report a number when waits on one class go over a budget.\n\nFinally, the JDK's own tools can be scripted. `jcmd <pid> help` lists every diagnostic command a JVM supports, and the list changes between versions: JDK 24 added `Thread.vthread_scheduler` and `Thread.vthread_pollers` for virtual threads, and from JDK 24 `Thread.print` also includes virtual threads that are mounted on a carrier. The virtual threads track uses those."
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
