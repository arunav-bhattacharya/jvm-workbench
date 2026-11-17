import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l10"
J = "java/workbench/coroutines/l10"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l10.{cls}{extra}"


def demo(kt, java, extra_kt="", extra_java=""):
    """A Kotlin demo and its runnable Java twin, read from disk so the lesson never drifts."""
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt", extra_kt),
            "file": f"{lab}/demo/{P}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{lab}/demo/{J}/{java}"), "run": run(j, extra_java),
                    "file": f"{lab}/demo/{J}/{java}"}}


def solo(kt):
    """A Kotlin demo with no Java twin: the test library has no Java counterpart worth showing."""
    k = kt.replace(".kt", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt"),
            "file": f"{lab}/demo/{P}/{kt}", "solo": True}


def pair(kotlin, java):
    """A Kotlin fence and its Java twin, side by side, as the validator expects."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def helper(name):
    return {"name": name, "steps": [
        {"op": "read", "var": "flour", "reg": "before", "code": "val before = grams[\"flour\"] ?: 0L"},
        {"op": "note", "code": "val more = units.toGrams(1, \"scoop\")   // suspends: the thread is free"},
        {"op": "add", "reg": "before", "n": 100, "code": "val after = before + more   // 100 g"},
        {"op": "write", "var": "flour", "reg": "before", "code": "grams[\"flour\"] = after"},
    ]}


SIM = {
 "title": "Two helpers on limitedParallelism(1)",
 "intro": "Both helpers run on a one-thread view, so only one runs at a time. But each one gives the thread away when it suspends in units.toGrams. You are the scheduler: click a helper to run its next line. Can you end with flour = 100 after two additions of 100 g?",
 "vars": {"flour": 0},
 "threads": [helper("helper A"), helper("helper B")],
 "goal": {"var": "flour", "eq": 100, "say": "Lost addition. Both helpers read 0 before either wrote. One coroutine at a time between suspensions is not one addition at a time."},
}

# ---------------------------------------------------------------- opening
OPENING = """Before a big dinner, a shopping list hangs on the fridge, and every helper who spots something missing writes it down. Two helpers notice the flour at the same moment. Each reads "flour: 200 g", goes to look up how much a scoop weighs, comes back and writes "flour: 300 g". Two scoops were needed, the list asks for one, and the cake will notice.

The house tries a rule: only one person may hold the pen at a time. It sounds like the fix, and that's the trap. A helper puts the pen down while she looks up the scoop, and the next helper picks it up.

Channels, select and pipelines passed plates from one coroutine to another, so no two of them ever held the same plate. A shopping list is shared. In this lesson, we'll watch coroutines lose additions the way threads do, see why one at a time between steps isn't one at a time, guard the list with a `Mutex`, and then hold a rehearsal dinner on a fake clock, so tests of slow code finish in milliseconds. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_LOCK = """private val mutex = Mutex()

suspend fun add(item: String, grams: Long) = mutex.withLock {
    list[item] = (list[item] ?: 0L) + grams
}"""
J_LOCK = """// Java equivalent: a ReentrantLock around the same read-modify-write
private final ReentrantLock lock = new ReentrantLock();

void add(String item, long grams) {
    lock.lock();
    try { list.put(item, list.getOrDefault(item, 0L) + grams); }
    finally { lock.unlock(); }
}"""

S0 = """Start with something smaller than a shopping list: a pot of peas. `SharedCounter`, in the Try it below, starts 100 helpers. Each one is a **coroutine**, a piece of work that can pause without holding a thread, and each counts 10,000 peas into the same pot. They run on `Dispatchers.Default`, the **dispatcher** (the part that picks a thread for each coroutine) with one thread per core. So the helpers really do run at the same moment, on different threads. Here is the pot counted five ways:

```text
plain var                      982,455 of 1,000,000 in   78 ms
@Volatile var                  913,871 of 1,000,000 in   61 ms
AtomicLong                   1,000,000 of 1,000,000 in   43 ms
Mutex.withLock               1,000,000 of 1,000,000 in  891 ms
withContext(limited(1))      1,000,000 of 1,000,000 in 1095 ms
```

Some 17,000 peas went into the pot uncounted. `count++` is three steps, read, add and write, and two coroutines on two threads can both read 41 and both write 42: the race from Race conditions in the first track. **Shared mutable state**, a variable that more than one coroutine changes, needs the same care with coroutines as with threads. `@Volatile` didn't help, and the coroutines guide says so in as many words: "volatiles are of no help". A volatile write is visible to every thread, but read, add and write are still three steps.

Pick the tool by the shape of the update.

- One value, changed in one step: an **atomic**, a variable whose read-modify-write can't be split by another thread. `AtomicLong.incrementAndGet()`, `AtomicReference.updateAndGet` and `MutableStateFlow.update { }` from lesson 8 of this track never suspend and never block. Kotlin 2.1.20 also added common atomics such as `AtomicInt` in `kotlin.concurrent.atomics`, still experimental; on the JVM the `java.util.concurrent.atomic` classes do the same job.
- Several steps that must happen together, such as reading the list and writing a new total: a `Mutex`.
- State that one coroutine owns: **confinement**. Keep the list inside one coroutine and send it requests through a channel, the hatch from the last lesson. Nothing else can touch it, so nothing needs a lock.

`Mutex` is the coroutine lock, the pen on a string by the fridge:

""" + pair(K_LOCK, J_LOCK) + """

`withLock` takes the lock, runs the block in a `try`, and releases the lock in `finally`, the same idiom as Java's. The difference is what waiting costs. `Mutex.lock()` suspends the coroutine, so a helper waiting for the pen holds no thread. The KDoc, the documentation in the library's source, gives the Mutex the memory rules of a `synchronized` block, and makes it fair: waiters get the lock in the order they asked.

Two warnings come with it. A `Mutex` is **not reentrant**: a coroutine that holds it and calls `withLock` again suspends forever, waiting for itself. Its KDoc gives it just two states, locked and unlocked, and it keeps no record of who holds it, unless you pass an `owner` token for debugging. (A `ReentrantLock` records the thread that holds it, which wouldn't work here, because a coroutine may resume on another thread.) So take the lock once, at the top. And the numbers above show the second warning: a lock or a dispatcher switch around every tiny increment costs about 20 times more than an atomic. Lock around a meaningful piece of work, or use an atomic for a single number.

**One number: an atomic. Several steps that belong together: a Mutex.**

The last line of the table looks like a third, cheaper lock. It counted every pea. It fails on the shopping list, and the reason is the heart of this lesson."""

# ---------------------------------------------------------------- section 1
K_VIEW = """withContext(oneAtATime) {
    val before = grams[item] ?: 0L
    val more = units.toGrams(amount, unit)     // suspends: another helper runs here
    grams[item] = before + more                // writes over the other helper's addition
}"""
J_VIEW = """// Java equivalent: one thread, but an async step in the middle
CompletableFuture.supplyAsync(() -> grams.getOrDefault(item, 0L), oneThread)
    .thenCombine(units.toGramsAsync(amount, unit), Long::sum)          // another helper runs meanwhile
    .thenAcceptAsync(after -> grams.put(item, after), oneThread);      // writes over the other addition"""

S1 = """A **view** such as `Dispatchers.Default.limitedParallelism(1)` is a slice of a dispatcher that runs at most one of its coroutines at a time. That's the house rule about the pen, and it looks like a lock. The KDoc has a heading of its own to say it isn't one: "limitedParallelism(1) is not a mutex!"

The view promises that code **between suspension points** runs one coroutine at a time. A suspension point is a call where a coroutine may pause, such as `delay` or a call to another suspend function. Between two of them, each coroutine sees what the one before it wrote, so `count++` on the view is safe, which is why it counted every pea. But the moment a coroutine suspends, the view's thread is free, and the next coroutine runs. That's the helper putting the pen down to look up the scoop. Any update that suspends in the middle is open:

""" + pair(K_VIEW, J_VIEW) + """

That is the lab's `ShoppingList.add`, as the starting code writes it. A **critical section** is code that must run with nothing else touching the same state in the middle of it, and this one has a middle. Play it out in the simulator: two helpers, one thread, and a suspension in the middle of each. (The simulator lets you switch after any line. On the real view a switch can happen only at the suspending line, and that's enough to lose an addition.)

`NotAMutex`, in the Try it below, runs three helpers on a one-thread view, then the same three under a `Mutex`:

```text
limitedParallelism(1):
  helper 0: read the list
  helper 1: read the list
  helper 2: read the list
  helper 0: write the list
  helper 1: write the list
  helper 2: write the list
Mutex.withLock:
  helper 0: read the list
  helper 0: write the list
  helper 2: read the list
  helper 2: write the list
  helper 1: read the list
  helper 1: write the list
```

On the view, all three read before anyone wrote, so two of the three additions are lost. Under the Mutex, each helper reads and writes before the next one starts. The holder still suspends in the middle, but it keeps the pen while it does.

There are two fixes. Move the suspension out of the critical part: convert first, then read and write with nothing that suspends between them. Or hold a `Mutex` across the whole update, which keeps the others out even while the holder is suspended. The first is faster, because the lookups overlap; it's the lab's solution. Use the second when the suspending call really must sit inside, for example a check whose answer must not go stale before you write.

The rule is the one you learned for threads, with one word added for coroutines.

**A critical section is safe only if nothing can run in the middle of it. In a coroutine, every suspension point is a middle, including the ones hidden inside functions you call.**

The list is safe now. Proving it in a test is another matter: every lookup takes 50 ms, and a test of a retry with long waits takes longer still. We need a faster clock."""

# ---------------------------------------------------------------- section 2
K_TEST = """@Test
fun `waits 100 then 200 ms between attempts`() = runTest {
    val attempts = mutableListOf<Long>()
    retryWithBackoff(times = 3, initialDelay = 100.milliseconds, maxDelay = 1.seconds) {
        attempts += currentTime                           // virtual milliseconds
        if (attempts.size < 3) throw IOException("the line is busy") else "loaf ordered"
    }
    assertThat(attempts).containsExactly(0L, 100L, 300L)  // in a few real milliseconds
}"""
J_TEST = """// Java equivalent: Reactor's StepVerifier with virtual time (reactor-test)
@Test
void waitsBetweenAttempts() {
    StepVerifier.withVirtualTime(() -> bakery.order("rye")
            .retryWhen(Retry.backoff(2, Duration.ofMillis(100)).jitter(0)))
        .expectSubscription()
        .thenAwait(Duration.ofMillis(300))
        .expectNext("loaf ordered")
        .verifyComplete();
}"""

S2 = """Tests of code with timers are slow in real time, and they wobble. Take **retry with backoff**: try again after a wait, and wait longer each time. Waits of 100, 200 and 400 ms cost 700 ms per test. On a busy build machine 700 becomes 1,500, and a timing check becomes a coin toss.

A theatre solves the same problem with a rehearsal. Nobody waits three hours for the roast: the stage manager says "the roast is done" and the next scene starts. `runTest`, from the kotlinx-coroutines-test library, is that rehearsal. Every `delay` in the test's coroutines is skipped. Instead, a **virtual clock**, a pretend clock that jumps forward instead of ticking, moves on to the next delay that is due, in the order the delays would have finished.

""" + pair(K_TEST, J_TEST) + """

`retryWithBackoff` is the function you write in this lesson's lab. The test reads `currentTime`, the virtual clock, at every attempt, and checks exact numbers instead of a window of real time.

Predict the log of a whole rehearsal dinner. `VirtualTime`, in the Try it below, calls `runTest` from a plain `main`. One coroutine simmers the soup for 1,000 ms, seasons it for 200 and bakes bread for 2,000. Another cooks the roast for 3,000 and rests it for 500:

```text
virtual  1000 ms (real  246 ms)  soup simmered
virtual  1200 ms (real  265 ms)  soup seasoned
virtual  3000 ms (real  266 ms)  roast cooked
virtual  3200 ms (real  266 ms)  bread baked
virtual  3500 ms (real  268 ms)  roast rested
virtual  3500 ms (real  269 ms)  await returned
whole runTest took 274 ms of real time
withContext(Default) { delay(1_000) }: virtual 0 ms, real 1005 ms
```

Three and a half seconds of dinner took about 20 real milliseconds once the library had loaded, in the right order. `runTest` runs the body in a `TestScope`, a scope made for tests, on a single-threaded **test dispatcher**, a dispatcher tied to the virtual clock. You can also drive the clock by hand: `advanceTimeBy(ms)` runs everything due before that point, `runCurrent()` runs what is due now, and `advanceUntilIdle()` runs everything queued. At the end, `runTest` waits for every child coroutine, so a test can't pass with work still pending.

Now the last line, where the picture breaks. In a rehearsal, the stage manager can skip only the scenes he runs. `runTest` can skip only delays on its own dispatcher. Code that moves to `Dispatchers.IO` or `Dispatchers.Default` waits in real time, and the virtual clock never sees it: one real second, and `currentTime` stayed at 0. That's why Dispatchers and the coroutine context injected the dispatchers: tests pass `StandardTestDispatcher(testScheduler)`, and the program passes the real ones.

Two more rules keep the clock honest. `withTimeout` inside `runTest` uses virtual time too. Mix it with real work on another dispatcher, and the scheduler, finding nothing of its own to do, can jump the clock forward and fire the timeout while the real work is still running. The tests in Cancellation and timeouts use `runBlocking` for their blocking call for exactly that reason. And the timeout of `runTest` itself is real, wall-clock time: 60 seconds by default since kotlinx.coroutines 1.8 (it was 10 s in 1.7). Change it with `runTest(timeout = 10.seconds)` or the `kotlinx.coroutines.test.default_timeout` system property. In 1.11 the old `dispatchTimeoutMs` overloads are errors.

**Only delays on the test dispatcher are virtual. Inject your dispatchers.**

The rehearsal has one more question to settle: when a test starts a new coroutine, when does it actually run?"""

# ---------------------------------------------------------------- section 3
K_UNCONF = """backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
    tracker.transitions.collect { seen += it }    // subscribed before the next line runs
}
tracker.moveTo(DishStatus.COOKING)"""
J_UNCONF = """// Java equivalent: StepVerifier subscribes first, then runs the action that emits
StepVerifier.create(tracker.transitions())
    .then(() -> tracker.moveTo(DishStatus.COOKING))
    .expectNextMatches(t -> t.to() == DishStatus.COOKING)
    .thenCancel()
    .verify();"""

S3 = """`runTest` uses a `StandardTestDispatcher` by default. With it, `launch` only queues the new coroutine, and nothing runs until the test body suspends or moves the clock. Tests stay predictable, because you decide when each child runs. Real dispatchers don't run a new coroutine on the spot either, so this is also the more honest default.

`UnconfinedTestDispatcher(testScheduler)` enters a new coroutine at once and runs it up to its first suspension. That's handy for a collector that must be listening before the next line emits. Take the `DishTracker` from lesson 8 of this track, whose `transitions` is a SharedFlow with no replay:

""" + pair(K_UNCONF, J_UNCONF) + """

If you mix dispatchers, give them all the same `testScheduler`. Two schedulers mean two clocks, and one of them will not move.

`TestDispatchers`, in the Try it below, shows both dispatchers and a third tool:

```text
StandardTestDispatcher:  [after launch, child ran]
UnconfinedTestDispatcher: [child ran, after launch]
polls after advanceTimeBy(5_500): 5
polls after advanceUntilIdle(): 5 (background work doesn't keep it busy)
```

The third tool is `backgroundScope`, for coroutines that never finish on their own: a loop that reads the oven probe every second, a collector of a StateFlow, the sharing scope of a `stateIn`. `runTest` waits for every child before it returns, so an endless child in the test body would keep it waiting until the 60-second timeout. Coroutines in `backgroundScope` are cancelled when the test body ends instead. Two details matter. `advanceUntilIdle()` stops once only background work is left, otherwise a poller would keep it busy forever, so drive background work with `advanceTimeBy`. And a failure in `backgroundScope` doesn't stop the test at once, but it's reported when the test ends, so the test still fails.

This lesson's lab is written the way these rules suggest. The retry tests read `currentTime` to check each wait exactly, and the shopping-list tests count how many lookups overlap instead of timing them. On the starting code, one of those tests reports 0 virtual milliseconds: the lookups ran on a real `Default` thread, outside the virtual clock.

For flows there is also Turbine (`app.cash.turbine`, not on this lab's classpath), a small test library that adds `flow.test { awaitItem() }`. Its waits use a 3-second wall-clock timeout, not the virtual clock.

**Put endless coroutines in `backgroundScope`, and drive them with `advanceTimeBy`.**

A rehearsal proves the order of the scenes and the timing logic. It says nothing about how long the real bakery takes to answer, and that's the limit to keep in mind."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a shopping list on the fridge, two helpers who each wrote their own total, and a rule about the pen that didn't help. Coroutines on Default race like threads. An atomic fixes one number, a Mutex holds a whole update, and a one-thread view lets go at every suspension. Then `runTest` rehearsed the dinner on a fake clock.

Now search your own code for `limitedParallelism(1)` used to guard a variable, and look for a suspend call inside each guarded block. Each one is a pen put down mid-sentence.

Next, we'll visit a neighbour who cooks the Java way. How does coroutine code work with futures, Reactor and virtual threads?"""

L = {
 "id": "co-10",
 "title": "Shared state and testing coroutines",
 "minutes": 35,
 "goal": "By the end you can protect shared state across coroutines with atomics or a Mutex, explain why limitedParallelism(1) is not a lock, and test timing-heavy code such as retry with backoff on virtual time with runTest, test dispatchers and backgroundScope.",
 "opening": OPENING,
 "warmup": {
  "q": "100 helper coroutines run on a `Dispatchers.Default.limitedParallelism(1)` view. Each does `val before = grams[\"flour\"] ?: 0; val more = units.toGrams(1, \"scoop\"); grams[\"flour\"] = before + more`, where `toGrams` is a suspend call to the recipe app that returns 100. What does the list say for flour at the end?",
  "options": [
   "Exactly 10,000 g, because only one helper runs at a time on the view",
   "Usually far less than 10,000 g, because the helpers interleave at toGrams",
   "Exactly 10,000 g, but only if toGrams doesn't suspend for long",
   "The code fails, because a one-thread view rejects concurrent coroutines"
  ],
  "answer": 1,
  "why": "A one-thread view runs one coroutine at a time only between suspension points. When a helper suspends in `toGrams`, the thread is free, and the next helper reads the same old amount. When they resume, each writes its own `before + more` over the others. The KDoc's own heading for this is \"limitedParallelism(1) is not a mutex!\"."
 },
 "sections": [
  {
   "h": "Helpers who share one list race like threads, and the same tools fix them",
   "body": S0,
   "try": {
    "title": "Count a million peas five ways",
    "minutes": 4,
    "steps": [
     "Read `SharedCounter.kt`. 100 coroutines on Default each count 10,000 peas. Predict which counters reach 1,000,000, and which is slowest.",
     "Run it twice.",
     "Run the Java twin, which uses 8 threads and a `ReentrantLock`."
    ],
    "code": demo("SharedCounter.kt", "SharedCounterJava.java"),
    "expect": "The plain and `@Volatile` counters come out short, by a different amount each run. `AtomicLong`, `Mutex.withLock` and the one-thread view all reach exactly 1,000,000. `AtomicLong` is fastest by far; the `Mutex` and the `withContext` switch for every increment take around a second, because each increment pays for a lock or a dispatch. The Java twin shows the same split, with `ReentrantLock` much cheaper than a Mutex here, because these threads never suspend."
   },
   "refs": [
    {"title": "Shared mutable state and concurrency (Kotlin docs)", "url": "https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html", "kind": "read"},
    {"title": "Mutex (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/", "kind": "docs"}
   ]
  },
  {
   "h": "A one-thread view is not a lock: the pen goes down at every suspension",
   "body": S1,
   "sim": SIM,
   "try": {
    "title": "Interleave three helpers, then lock them",
    "minutes": 3,
    "steps": [
     "Read `NotAMutex.kt`. Predict the order of the `read` and `write` lines for the one-thread view, then for the `Mutex`.",
     "Run it.",
     "Look at the last part: why does the nested `withLock` time out instead of returning `inner`?",
     "Run the Java twin, where a single-thread executor interleaves the same way and `ReentrantLock` happily locks twice."
    ],
    "code": demo("NotAMutex.kt", "NotAMutexJava.java"),
    "expect": "On the one-thread view, all three `read the list` lines print before any `write the list`: each helper suspended in the middle and let the next one in. With the `Mutex`, each helper reads and writes before the next one starts (the order of the helpers may vary). The nested `withLock` times out after 500 ms, because a Mutex is not reentrant: the inner lock waits for the outer one, which waits for the inner one. The Java twin interleaves the same way on one thread, and its `ReentrantLock` reports a hold count of 2."
   },
   "refs": [
    {"title": "limitedParallelism (API reference: \"not a mutex\")", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html", "kind": "docs"}
   ]
  },
  {
   "h": "A rehearsal dinner on a fake clock: runTest skips the delays",
   "body": S2,
   "try": {
    "title": "Rehearse three and a half seconds of dinner in a blink",
    "minutes": 3,
    "steps": [
     "Read `VirtualTime.kt`. It calls `runTest` from a plain `main`. Predict the virtual time of each log line, and how much real time the first `runTest` takes.",
     "Run it.",
     "Look at the last line: why did the clock stay at 0 while a real second went by?"
    ],
    "code": solo("VirtualTime.kt"),
    "expect": "The lines print at virtual 1,000, 1,200, 3,000, 3,200 and 3,500 ms, in that order, and `await returned` at 3,500. The real time stays well under a second, and most of it is the test library starting up. The last `runTest` reports virtual 0 ms and about 1,000 real ms: `withContext(Dispatchers.Default)` left the test scheduler, so its `delay` was a real one."
   },
   "refs": [
    {"title": "runTest (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html", "kind": "docs"}
   ]
  },
  {
   "h": "Standard or Unconfined, and backgroundScope for work that never ends",
   "body": S3,
   "try": {
    "title": "Watch the two test dispatchers and a background poller",
    "minutes": 3,
    "steps": [
     "Read `TestDispatchers.kt`. Predict the order in each of the two lists, and the poll count after each line.",
     "Run it.",
     "Move the poller from `backgroundScope.launch` to a plain `launch`, and add `runTest(timeout = 3.seconds)` (import `kotlin.time.Duration.Companion.seconds`). Predict, then run."
    ],
    "code": solo("TestDispatchers.kt"),
    "expect": "`StandardTestDispatcher: [after launch, child ran]` and `UnconfinedTestDispatcher: [child ran, after launch]`. The poller has run 5 times after `advanceTimeBy(5_500)`, and still 5 after `advanceUntilIdle()`, which ignores background work. After your change, `advanceUntilIdle()` treats the poller as ordinary work and runs it again and again, millions of virtual seconds' worth, until the 3-second wall-clock timeout stops everything with `UncompletedCoroutinesError` (an `AssertionError`): the test body did not run to completion."
   }
  }
 ],
 "compare": {
  "title": "A dinner budget: ReentrantLock vs Mutex",
  "java": {"title": "DinnerBudget.java", "src": "class DinnerBudget {\n    private final long limitCents;\n    private long spentCents = 0;\n    private final ReentrantLock lock = new ReentrantLock();\n\n    DinnerBudget(long limitCents) { this.limitCents = limitCents; }\n\n    boolean buy(String item) {\n        long price = shop.priceOf(item);                  // 1. the slow call, outside the lock (blocks a thread)\n        lock.lock();                                      // 2. blocks the thread while waiting\n        try {\n            if (spentCents + price > limitCents) return false;\n            spentCents += price;                          // 3. check and spend together\n            return true;\n        } finally {\n            lock.unlock();\n        }\n    }\n}"},
  "kotlin": {"title": "DinnerBudget.kt", "src": "class DinnerBudget(private val limitCents: Long) {\n    private var spentCents = 0L\n    private val mutex = Mutex()\n\n    suspend fun buy(item: String): Boolean {\n        val price = shop.priceOf(item)                    // 1. the slow call, outside the lock (suspends)\n        return mutex.withLock {                           // 2. suspends while waiting, holds no thread\n            if (spentCents + price > limitCents) return@withLock false\n            spentCents += price                           // 3. check and spend together\n            true\n        }\n    }\n}"},
  "note": "The shape is the same: ask the shop for the price first, then check and spend under one lock. Two things differ. Waiting for a `ReentrantLock` blocks a thread, while waiting for a `Mutex` suspends a coroutine, so a rush of 5,000 purchases doesn't need 5,000 threads. And the Java lock is reentrant while the Mutex isn't, so a helper function that takes the Mutex again from inside `withLock` hangs instead of nesting. The Kotlin version has one extra trap that Java can't have. If someone later moves `shop.priceOf` inside `withLock`, it still works, but it holds the lock across a call to the shop. If they replace the Mutex with a one-thread view, it stops being correct at all."
 },
 "worked": {
  "title": "Test a retry policy without waiting for it",
  "steps": [
   {"say": "Helpers order bread through `BakeryOrders.orderWithRetry`, which tries again when the bakery's line is busy (an `IOException`): up to 5 attempts, with waits that start at 200 ms, double each time and never exceed 2 s. The existing test uses real time. It takes 1.4 seconds, and on a busy machine it fails now and then.",
    "code": "@Test\nfun `retries while the line is busy`() = runBlocking {\n    var calls = 0\n    val started = System.currentTimeMillis()\n    val result = orders.orderWithRetry(\"rye\") { calls++; if (calls < 4) throw IOException(\"busy\") else \"ticket 42\" }\n    assertThat(result).isEqualTo(\"ticket 42\")\n    assertThat(System.currentTimeMillis() - started).isBetween(1_350L, 1_600L)   // 200 + 400 + 800 = 1,400\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the shaky test: real sleeps, a timing window\n@Test\nvoid retriesWhileTheLineIsBusy() {\n    AtomicInteger calls = new AtomicInteger();\n    long started = System.currentTimeMillis();\n    String result = orders.orderWithRetry(\"rye\", () -> { if (calls.incrementAndGet() < 4) throw new UncheckedIOException(new IOException(\"busy\")); return \"ticket 42\"; });\n    assertThat(result).isEqualTo(\"ticket 42\");\n    assertThat(System.currentTimeMillis() - started).isBetween(1_350L, 1_600L);\n}", "alt_lang": "java"},
   {"say": "Move to `runTest`. The waits are `delay` calls on the test dispatcher, so they become virtual, and the test can check each attempt's exact virtual time instead of a window.",
    "code": "@Test\nfun `waits 200, 400, then 800 ms between attempts`() = runTest {\n    val at = mutableListOf<Long>()\n    val result = orders.orderWithRetry(\"rye\") {\n        at += currentTime                                   // 1. record virtual ms per attempt\n        if (at.size < 4) throw IOException(\"busy\") else \"ticket 42\"\n    }\n    assertThat(result).isEqualTo(\"ticket 42\")\n    assertThat(at).containsExactly(0L, 200L, 600L, 1_400L)   // 2. exact, and instant\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: Reactor's virtual time, if the orders are built on Reactor\n@Test\nvoid waitsBetweenAttempts() {\n    StepVerifier.withVirtualTime(() -> orders.orderWithRetry(\"rye\"))\n        .expectSubscription()\n        .thenAwait(Duration.ofMillis(1_400))             // 1. move the virtual clock\n        .expectNext(\"ticket 42\")                         // 2. exact, and instant\n        .verifyComplete();\n}", "alt_lang": "java"},
   {"say": "The test went back to real time when someone added `withContext(Dispatchers.IO)` around the phone call inside `BakeryOrders`: its `delay` calls now ran on IO. Inject the dispatcher, and give the test the one tied to the test scheduler.",
    "code": "class BakeryOrders(private val io: CoroutineDispatcher = Dispatchers.IO) {\n    suspend fun <T> orderWithRetry(bread: String, call: suspend () -> T): T =\n        withContext(io) { retryWithBackoff(times = 5, initialDelay = 200.milliseconds, maxDelay = 2.seconds) { call() } }\n}\n\n// 3. in the test\nval orders = BakeryOrders(io = StandardTestDispatcher(testScheduler))", "lang": "kotlin",
    "alt_code": "// Java equivalent: inject the Scheduler, and give the test a virtual one\nclass BakeryOrders {\n    private final Scheduler io;\n    BakeryOrders(Scheduler io) { this.io = io; }\n\n    <T> Mono<T> orderWithRetry(String bread, Mono<T> call) {\n        return call.subscribeOn(io)\n            .retryWhen(Retry.backoff(4, Duration.ofMillis(200)).maxBackoff(Duration.ofSeconds(2)).jitter(0).scheduler(io));\n    }\n}\n\n// 3. in the test\nVirtualTimeScheduler vts = VirtualTimeScheduler.getOrSet();\nBakeryOrders orders = new BakeryOrders(vts);", "alt_lang": "java"},
   {"say": "Add the case people forget: a cancel during a wait must stop the retries. Virtual time lets you stop exactly between two attempts.",
    "code": "@Test\nfun `a cancel during the backoff stops the retries`() = runTest {\n    var calls = 0\n    val job = launch { orders.orderWithRetry(\"rye\") { calls++; throw IOException(\"busy\") } }\n    advanceTimeBy(300)                 // 4. attempts at 0 and 200 ms; now waiting until 600 ms\n    job.cancel()\n    advanceUntilIdle()\n    assertThat(calls).isEqualTo(2)\n}", "lang": "kotlin",
    "alt_code": "@Test\nvoid cancelDuringBackoffStopsRetries() {\n    AtomicInteger calls = new AtomicInteger();\n    StepVerifier.withVirtualTime(() -> orders.orderWithRetry(\"rye\",\n            Mono.<String>fromCallable(() -> { calls.incrementAndGet(); throw new IOException(\"busy\"); })))\n        .expectSubscription()\n        .thenAwait(Duration.ofMillis(300))   // 4. attempts at 0 and 200 ms\n        .thenCancel()\n        .verify();\n    assertThat(calls.get()).isEqualTo(2);\n}", "alt_lang": "java"},
   {"say": "Self-check: suppose the helper wrapped both the attempt and the `delay` in one `runCatching` and retried on any failure. What would the cancel test report? (`calls` would be 5, not 2. After the cancel, each `delay` throws at once, `runCatching` swallows it as a failed attempt, and the loop races through the remaining attempts. The test catches it because it counts calls instead of timing them. Cancellation and timeouts showed the same trap.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix a shared shopping list, then write retry with backoff",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/ShoppingList.kt", f"{lab}/main/{P}/Retry.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l10.*'",
  "steps": [
   "Meet the code. `ShoppingList` keeps the grams needed per item, and many helpers call `add` at once; each addition converts its amount to grams with a suspending `UnitConverter`. `retryWithBackoff` in `Retry.kt` is a `TODO()`. Run the tests: all seven fail. Read `SharedStateAndTestingTest.kt` first. It is the spec, and every test runs on virtual time.",
   "In `ShoppingList.add`, call `units.toGrams` first, outside any lock. Then do the read and the write inside `mutex.withLock { }`. Replace the one-thread view with the `Mutex` in `total` too.",
   "Write `retryWithBackoff`. Loop over attempts 1 to `times - 1`: return the block's result on success; on an exception, rethrow `CancellationException`, rethrow when `retryOn` is false, otherwise `delay` and grow the wait. Then make the last attempt outside the loop, so its exception reaches the caller.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "On the starting code, `100 helpers adding at once all land` reports a few hundred grams instead of 10,000 (200 in one run here): nearly every helper read the list before any wrote. The second test reports 0 virtual ms, because the starting code's lookups ran on a real `Default` thread, outside the test clock.",
   "`Duration` times a `Double` is a `Duration`: `wait = (wait * factor).coerceAtMost(maxDelay)`.",
   "Catch `CancellationException` before `Exception`, and rethrow it. `kotlin.coroutines.cancellation.CancellationException` is the class to import.",
   "The cancel test cancels the job during a `delay`. A `delay` that is not inside your `try` simply throws, and the loop ends without another attempt."
  ],
  "done_when": "All seven tests in `SharedStateAndTestingTest` pass."
 },
 "drill": {
  "title": "A safe counter map and a virtual-time test, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `class PlateCounts` with `suspend fun serve(dish: String)` that calls a suspending `kitchen.plateUp(dish)` first, then adds one to that dish's count, safe for many coroutines on `Dispatchers.Default`. Then write a `runTest` test that checks `pollEvery(1.seconds) { polls++ }` has polled 3 times after 3.5 virtual seconds, using `backgroundScope` for the endless poller.",
  "answer": {"lang": "kotlin", "src": "class PlateCounts(private val kitchen: Kitchen) {\n    private val counts = HashMap<String, Int>()\n    private val mutex = Mutex()\n\n    suspend fun serve(dish: String) {\n        kitchen.plateUp(dish)                      // suspends: keep it outside the lock\n        mutex.withLock { counts[dish] = (counts[dish] ?: 0) + 1 }\n    }\n}\n\n@Test\nfun `polls once a second`() = runTest {\n    var polls = 0\n    backgroundScope.launch { pollEvery(1.seconds) { polls++ } }   // never ends on its own\n    advanceTimeBy(3_500)\n    assertThat(polls).isEqualTo(3)\n}",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a lock-free counter map, and Reactor virtual time for the poller\nclass PlateCounts {\n    private final ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();\n\n    void serve(String dish) {\n        kitchen.plateUp(dish);                     // blocking: outside any lock\n        counts.merge(dish, 1, Integer::sum);       // one atomic step\n    }\n}\n\n@Test\nvoid pollsOnceASecond() {\n    StepVerifier.withVirtualTime(() -> Flux.interval(Duration.ofSeconds(1)).map(tick -> poll()))\n        .expectSubscription()\n        .thenAwait(Duration.ofMillis(3_500))\n        .expectNextCount(3)\n        .thenCancel()\n        .verify();\n}"}}
 },
 "recap": [
  "Coroutines on `Dispatchers.Default` race like threads. `@Volatile` doesn't make `count++` safe; an atomic does, for a single value.",
  "A `Mutex` guards a sequence of steps. `withLock` suspends instead of blocking, and the Mutex is fair and not reentrant: locking it again from inside hangs.",
  "`limitedParallelism(1)` runs one coroutine at a time only between suspension points, so a read, a suspending call and a write on it can lose updates. Move the suspension out, or hold a Mutex.",
  "`runTest` skips `delay` with a virtual clock (`currentTime`, `advanceTimeBy`, `runCurrent`, `advanceUntilIdle`). Delays on real dispatchers stay real, so inject dispatchers.",
  "`StandardTestDispatcher` (the default) queues new coroutines, `UnconfinedTestDispatcher` starts them at once, and endless coroutines belong in `backgroundScope`.",
  "The limit: virtual time proves the order and the timing logic, not real speed. It can't tell you how long the real bakery takes, or how a Mutex behaves with thousands of waiters."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A dinner budget runs `mutex.withLock { if (spent + price <= limit) { spend(price) } }`, and `spend` itself calls `mutex.withLock { spent += price }`. What happens on the first purchase?",
   "options": ["It works: a coroutine may take a lock it already holds", "It throws `IllegalStateException`: the mutex is already locked", "It hangs: the inner `withLock` waits for the outer one, which never finishes", "The inner `withLock` is skipped, so `spent` never changes"],
   "answer": 2,
   "why": "`Mutex` is not reentrant. The inner `withLock` suspends until the lock is free, but the lock is held by the same code that is waiting for it, so it never is. Take the lock once at the top, and have `spend` assume it is held."},
  {"q": "Which tool fits a per-dish count of plates served, updated by many coroutines on Default, where each update is just \"add one\"?",
   "options": ["A `ConcurrentHashMap<String, AtomicLong>` and `incrementAndGet()`", "A `Dispatchers.Default.limitedParallelism(1)` view around the whole kitchen", "A `Mutex` held across each dish's cooking", "`@Volatile` on the map field"],
   "answer": 0,
   "why": "Each update is one step on one value, so an atomic is the cheapest correct tool: it never suspends or blocks. A Mutex held across the cooking makes every dish wait for every other, and `@Volatile` on the field only covers the reference to the map, not the increments."},
  {"q": "Inside `runTest`, the code under test calls `withContext(Dispatchers.IO) { delay(2_000) }`. What does the test see?",
   "options": ["`currentTime` jumps by 2,000 and the test finishes at once", "The test fails at once, because `Dispatchers.IO` is forbidden in `runTest`", "`currentTime` jumps by 2,000, but only after `advanceUntilIdle()`", "The test waits about 2 real seconds, and `currentTime` doesn't move"],
   "answer": 3,
   "why": "Only delays on the test dispatcher are virtual. `withContext(Dispatchers.IO)` leaves the test scheduler, so that `delay` is a real one that the virtual clock never sees. Inject the dispatcher, so the test can pass `StandardTestDispatcher(testScheduler)`."},
  {"q": "A test starts `launch { while (true) { delay(1_000); poll() } }` in the `runTest` body, checks the poll count after `advanceTimeBy(3_500)`, and ends. What happens?",
   "options": ["The test passes; the loop is cancelled when the body ends", "The test hangs until the `runTest` timeout, because `runTest` waits for every child", "The loop never runs, because `launch` only queues it", "`advanceTimeBy` throws, because the loop never ends"],
   "answer": 1,
   "why": "`runTest` waits for every child of the test scope before it returns, and this one never ends, so the test fails after the wall-clock timeout (60 s by default). Start endless work in `backgroundScope`, which `runTest` cancels when the body ends."},
  {"q": "From lesson 5 of this track: a retry helper wraps each attempt in `runCatching { block() }` and retries on any failure. The caller is cancelled while an attempt is suspended in a call to the bakery. What happens?",
   "options": ["The `CancellationException` counts as a failed attempt, and the helper goes on to the next one", "The retries stop at once, because `runCatching` never catches `CancellationException`", "The coroutine is killed and no `finally` blocks run", "The helper waits for the call to finish, then stops"],
   "answer": 0,
   "why": "`runCatching` catches every `Throwable`, including `CancellationException`, so the cancel is handled as a failed attempt. If the backoff `delay` sits outside the `runCatching`, it throws at once and ends the loop more or less by luck; if it sits inside, the loop races through every remaining attempt. Rethrow `CancellationException` before treating anything as worth retrying.",
   "from": "co-05"}
 ],
 "flashcards": [
  {"front": "Does `@Volatile` make `count++` safe across coroutines on `Dispatchers.Default`?", "back": "No. It makes each read and write visible, but `count++` is still read, add, write. Use an atomic or a `Mutex`."},
  {"front": "What does `Mutex.withLock` do while another coroutine holds the lock?", "back": "It suspends the caller (no thread is blocked) until the lock is free, and the Mutex hands out the lock in the order coroutines asked."},
  {"front": "A coroutine holding a `Mutex` calls `withLock` on it again. What happens?", "back": "It suspends forever: `Mutex` is not reentrant."},
  {"front": "Why is `limitedParallelism(1)` not a mutex?", "back": "It runs one coroutine at a time only between suspension points. When one suspends, another runs, so an update with a suspension in the middle can interleave."},
  {"front": "What happens to `delay(1_000)` inside `runTest`?", "back": "It is skipped: the virtual clock (`currentTime`) jumps forward by 1,000 ms, keeping the order of events."},
  {"front": "`StandardTestDispatcher` vs `UnconfinedTestDispatcher` for `launch`?", "back": "Standard queues the new coroutine until the test yields or moves the clock. Unconfined starts it at once and runs it to its first suspension."},
  {"front": "Where do never-ending coroutines go in a `runTest` test?", "back": "`backgroundScope`: they are cancelled when the test body ends, and `advanceUntilIdle()` doesn't wait for them."}
 ],
 "terms": [
  {"term": "Shared mutable state", "plain": "A variable that more than one coroutine or thread changes."},
  {"term": "Atomic", "plain": "A variable whose read-modify-write happens as one step that no other thread can split."},
  {"term": "Mutex", "plain": "A coroutine lock: waiting suspends instead of blocking. Fair, and not reentrant."},
  {"term": "Critical section", "plain": "Code that must run with nothing else touching the same state in the middle of it."},
  {"term": "Confinement", "plain": "Keeping changeable state reachable from only one coroutine or thread, so it needs no lock."},
  {"term": "Virtual time", "plain": "The test scheduler's pretend clock. Delays move it forward at once instead of waiting."},
  {"term": "StandardTestDispatcher", "plain": "A test dispatcher that queues work until the test lets the scheduler run."},
  {"term": "backgroundScope", "plain": "A scope inside runTest for endless work; it is cancelled when the test body ends."}
 ],
 "explain_back": {
  "prompt": "A friend replaced a `Mutex` with `Dispatchers.Default.limitedParallelism(1)` in the dinner budget, \"because it's simpler, and only one coroutine runs at a time anyway\". Each purchase asks the shop for the price between reading and writing the amount spent. Explain what can go wrong, and how you'd test it without real time.",
  "answer": "The one-thread view only promises one coroutine at a time between suspension points. Asking the shop suspends, so while one purchase waits for the price, the thread runs the next purchase, which reads the same amount spent. Both then pass the limit check and both spend, so the dinner can go over budget. A Mutex held across the whole purchase keeps the second one out, even while the first is suspended. Better still, ask the shop first, then do the check and the spend together under the lock, with nothing suspending in between. To test it, I'd use runTest with a fake shop that just calls delay(50), start a hundred purchases, and check the total spent and how many price lookups overlapped. On virtual time that gives the same answer every run and takes milliseconds, as long as the class takes its dispatcher as a parameter instead of hard-coding Dispatchers.Default."
 },
 "deeper": {
  "minutes": 10,
  "body": "`Semaphore(permits)` in `kotlinx.coroutines.sync` is the counting version of a Mutex: `withPermit { }` lets at most n coroutines in at once, like the three sinks of the last lesson's drill. It is the coroutine counterpart of the `Semaphore` from Using virtual threads, in the virtual threads track, and like the Mutex it suspends rather than blocks. Since 1.9 you can no longer cast a `Mutex` to a `Semaphore`; they are separate types.\n\n`Mutex` has an optional owner: `lock(owner)` and `withLock(owner)` record who holds it, and `holdsLock(owner)` checks it. Passing an owner turns a reentrant call into an immediate `IllegalStateException` instead of a silent hang, which is a cheap safety net in code where a helper function might be called with the lock already held.\n\nThe test library has more knobs than this lesson uses. Several `StandardTestDispatcher(testScheduler, name = ...)` instances can share one scheduler, so code that takes two dispatchers (one for blocking calls, one for CPU work) can get two named test dispatchers with one clock. `Dispatchers.setMain(...)` and `resetMain()` swap the Main dispatcher for code written for a user interface. And `runTest` reports uncaught exceptions from coroutines it doesn't own at the end of the test, which is why a forgotten `GlobalScope.launch` that throws can fail an unrelated test.\n\nFinally, virtual time is not a load test. It proves that the order and the timing logic are right. It says nothing about how long the real recipe app takes, how a real Mutex behaves with 5,000 waiters, or whether the shop keeps up. Keep a few real-time tests, with generous margins, for that."
 },
 "sources": [
  {"title": "Shared mutable state and concurrency (Kotlin docs)", "url": "https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html"},
  {"title": "Mutex (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/"},
  {"title": "kotlinx-coroutines-test (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/"},
  {"title": "runTest (kotlinx-coroutines-test API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html"}
 ]
}
out = ROOT / "content/lessons/co-10.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
