import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l05"
J = "java/workbench/coroutines/l05"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l05.{cls}{extra}"


def demo(kt, java, extra_kt="", extra_java=""):
    """A Kotlin demo and its runnable Java twin, read from disk so the lesson never drifts."""
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt", extra_kt),
            "file": f"{lab}/demo/{P}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{lab}/demo/{J}/{java}"), "run": run(j, extra_java),
                    "file": f"{lab}/demo/{J}/{java}"}}


def pair(kotlin, java):
    """A Kotlin fence and its Java twin, side by side, as the validator expects."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="Three coroutines are cancelled at the same moment. One suspended in delay '
    'throws CancellationException at once and runs its finally block. A CPU loop with no checks keeps computing to the end. '
    'A CPU loop that calls ensureActive throws at its next check and runs its finally block.">'
    '<text class="t-s t-m" x="160" y="24">time</text>'
    '<line class="ln-d" x1="196" y1="20" x2="660" y2="20" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="300" y1="34" x2="300" y2="222"/>'
    '<text class="t-s t-a" x="300" y="242" text-anchor="middle">job.cancel()</text>'
    '<text class="t-s" x="78" y="66" text-anchor="middle">suspended in delay</text>'
    '<rect class="box" x="160" y="44" width="135" height="36" rx="8"/>'
    '<text class="t-s t-code" x="227" y="66" text-anchor="middle">delay(10_000)</text>'
    '<rect class="box-bad" x="306" y="44" width="170" height="36" rx="8"/>'
    '<text class="t-s" x="391" y="66" text-anchor="middle">CancellationException</text>'
    '<rect class="box-ok" x="482" y="44" width="110" height="36" rx="8"/>'
    '<text class="t-s" x="537" y="66" text-anchor="middle">finally runs</text>'
    '<text class="t-s" x="78" y="126" text-anchor="middle">CPU loop, no checks</text>'
    '<rect class="box-a" x="160" y="104" width="450" height="36" rx="8"/>'
    '<text class="t-s" x="385" y="126" text-anchor="middle">keeps sorting until the sack is empty</text>'
    '<text class="t-s t-bad" x="645" y="126" text-anchor="middle">late</text>'
    '<text class="t-s" x="78" y="186" text-anchor="middle">with ensureActive()</text>'
    '<rect class="box-a" x="160" y="164" width="150" height="36" rx="8"/>'
    '<text class="t-s" x="235" y="186" text-anchor="middle">to the next check</text>'
    '<rect class="box-bad" x="316" y="164" width="170" height="36" rx="8"/>'
    '<text class="t-s" x="401" y="186" text-anchor="middle">CancellationException</text>'
    '<rect class="box-ok" x="492" y="164" width="110" height="36" rx="8"/>'
    '<text class="t-s" x="547" y="186" text-anchor="middle">finally runs</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Halfway through the afternoon, the phone rings. The guests can't come: dinner is off. The cook turns the oven down, puts a lid on the soup and takes the sauce off the heat. She hears the news between two steps of a recipe, when she glances at her phone.

Her helper in the corner is picking small stones out of a big sack of lentils. He never looks up between lentils, so he hears nothing, and he sorts the whole sack.

Coroutines are called off the same way. It's natural to think `cancel()` stops the code, but it only asks, and the code has to look up. Structured concurrency sent a cancel down the tree, and Dispatchers and the coroutine context ended with a question: what does a coroutine do when it's cancelled in the middle of a long loop, or inside a blocking call?

In this lesson, we'll watch a cancel reach a coroutine between steps and miss a busy loop, stop a `catch` from eating it, return a borrowed pan after it, and put a timer on the whole thing. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_NAIVE = """// Naive: never looks up from the sack
suspend fun countStones(lentils: LongArray, isStone: (Long) -> Boolean): Int {
    var stones = 0
    for (lentil in lentils) if (isStone(lentil)) stones++
    return stones
}"""
J_NAIVE = """// Java equivalent: a loop that never reads the interrupt flag
int countStones(long[] lentils, LongPredicate isStone) {
    int stones = 0;
    for (long lentil : lentils) if (isStone.test(lentil)) stones++;
    return stones;
}"""
K_FIXED = """// Fixed: looks up every 1,000 lentils
suspend fun countStones(lentils: LongArray, isStone: (Long) -> Boolean): Int {
    val context = currentCoroutineContext()
    var stones = 0
    for ((i, lentil) in lentils.withIndex()) {
        if (i % 1_000 == 0) context.ensureActive()   // throws CancellationException once cancelled
        if (isStone(lentil)) stones++
    }
    return stones
}"""
J_FIXED = """// Java equivalent: read the interrupt flag yourself
int countStones(long[] lentils, LongPredicate isStone) {
    int stones = 0;
    for (int i = 0; i < lentils.length; i++) {
        if (i % 1_000 == 0 && Thread.currentThread().isInterrupted()) throw new CancellationException();
        if (isStone.test(lentils[i])) stones++;
    }
    return stones;
}"""

S0 = """Start with what `cancel()` really does. A **coroutine** is a piece of work that can pause and resume without holding its **thread**, the worker that runs the code. Every coroutine has a **job**, the handle to its life that you can wait for or cancel; Structured concurrency drew the tree of them. `job.cancel()` marks that job as cancelling, and that's all it does. It doesn't stop a thread, and it doesn't reach into the middle of your code.

The coroutine finds out at its next **suspension point**, a call to a suspend function where it may pause, such as `delay`, `await`, `join` or `withContext`. Those library calls look at the job first. When they find it cancelled, they throw `CancellationException`, the exception that carries a cancel through the code. It unwinds the stack, every `finally` block runs on the way out, and the job ends as cancelled. A coroutine that is already paused hears it at once: one waiting in `delay(10_000)` is woken with the exception straight away.

In the kitchen, a suspension point is the moment between two steps, when the cook glances at her phone. That's when the news reaches her.

Code that never reaches such a point never hears. Here's the helper with the lentils, a loop that is pure CPU work, which means calculation with no waiting in it:

""" + pair(K_NAIVE, J_NAIVE) + """

Nothing in the loop is a suspension point, so a cancel waits until the loop ends. This is **cooperative cancellation**: cancelling asks, and the code stops when it next checks. Java works the same way. `Future.cancel(true)` sets the thread's interrupt flag, a per-thread true-or-false value that asks it to stop (A thread's life, in the first track). A loop that never reads the flag keeps going.

`CancelABusyLoop`, in the Try it below, runs four loops over 60 million lentils on `Dispatchers.Default`, the pool for CPU work. It has one thread per core, the part of the processor that runs one thread at a time. Each loop is cancelled 100 ms after it starts. Predict how long each takes to stop. On this busy machine it printed:

```text
no check                     stopped  2851 ms after cancel()
while (isActive)             stopped     4 ms after cancel()
ensureActive() every 1,000   stopped    10 ms after cancel()
yield() every 1,000          stopped     1 ms after cancel()
```

The loop with no check didn't stop when it was asked. It stopped when the sack was empty, almost three seconds later. (An idle machine sorts the whole sack in about 1.5 s.) The other three looked up now and then, and stopped within a few milliseconds.

Those three are the tools a CPU loop has. `ensureActive()` throws `CancellationException` if the job is cancelled. `isActive` returns a boolean, for a loop that wants to stop quietly: `while (isActive) { ... }`. `yield()` checks too, and also lets other coroutines waiting for the same thread run first. That matters when a long loop shares a small **dispatcher**, the part of the library that hands coroutines to threads. A check only reads the job's state, so it costs almost nothing, but once every thousand lentils is plenty:

""" + pair(K_FIXED, J_FIXED) + """

Watch which job you are checking. Inside `launch { }`, `isActive` and `ensureActive()` belong to the coroutine you launched. A plain suspend function like `countStones` has no scope to call them on, so it reads its own context with `currentCoroutineContext()`. A bare `isActive` in a lambda nested inside another scope can quietly read the outer scope's job.

**A cancel only asks. Code that never suspends or checks never hears it.**

So a loop can be taught to look up. The next trap is a loop that looks up, hears the news, and throws it away."""

# ---------------------------------------------------------------- section 1
K_SWALLOW = """// Naive: runCatching also catches the cancel
for (order in orders) {
    runCatching { confirm(order) }
        .onFailure { e -> println("call for $order failed, skipping: $e"); failed += order }
}"""
J_SWALLOW = """// Java equivalent: catching InterruptedException and carrying on
for (String order : orders) {
    try { confirm(order); }
    catch (InterruptedException e) { System.out.println("call for " + order + " failed"); failed.add(order); }
}"""

S1 = """Cancellation travels as an exception, and that is both its strength and its weak spot. The strength: `CancellationException` unwinds the stack, runs every `finally`, and closes every `use` block (Kotlin's way to close a resource) on the way out. The weak spot: a `catch` that catches it stops it right there.

Picture the evening before the big dinner. The cook phones each supplier in turn to confirm tomorrow's delivery. One busy line shouldn't stop the round, so every call is wrapped in `runCatching`, the standard function that runs a block and catches whatever it throws:

""" + pair(K_SWALLOW, J_SWALLOW) + """

`runCatching` catches every `Throwable`. So do `catch (e: Exception)` and `catch (e: Throwable)`, because on the JVM `CancellationException` is `java.util.concurrent.CancellationException`, a subclass of `IllegalStateException`.

Now the dinner is called off during the third call. Predict what the log shows. `SwallowedCancellation`, in the Try it below, phones the butcher every 100 ms, 20 times, and is cancelled at 250 ms:

```text
runCatching, swallowing:
  calls before cancel: 3, after cancel: 17, cancelAndJoin took 8 ms
```

Seventeen more calls in 8 milliseconds, which is quick work even for a butcher. The coroutine was still cancelled, so every `delay` threw at once, `runCatching` caught it, and the loop went round again. Each "failed call" in the log was the cancel in disguise. A `while (true)` loop written this way is worse: it spins at full speed, forever.

That's the part that surprises people. Catching the exception doesn't undo the cancel. The job stays cancelled, so the code after the `catch` runs in a coroutine whose next suspension point throws again.

The Java twin fails differently, and the difference teaches something. Catching `InterruptedException` clears the thread's interrupt flag, so the next `sleep` sleeps normally. The swallowing Java loop made the same 17 calls at the usual pace, and shutdown took 1,719 ms. A swallowed interrupt is lost. A swallowed cancellation is still there, and every later suspension point throws it again.

The fix is to let it through. With `runCatching`, rethrow it first: `.onFailure { if (it is CancellationException) throw it; ... }`. With `try`, put `catch (e: CancellationException) { throw e }` before the general clause. Better still, catch only the exceptions you expect, such as `IOException`, and let everything else go up. With the rethrow in place, the same run printed `after cancel: 0`.

**A cancel is an exception on its way out. Never catch it without rethrowing it.**

So the cancel must be free to unwind the stack, `finally` blocks and all. But what can a `finally` block still do inside a coroutine that has been cancelled?"""

ASIDE = {
    "title": "Is cancelling a coroutine the same as interrupting its thread?",
    "body": "No, though the two ideas are cousins. A cancel marks the coroutine's job and leaves the thread alone, so `Thread.sleep` and other blocking JDK calls don't notice it. An interrupt marks a thread, and suspension points such as `delay` ignore it. The job's state also lasts: it reaches every child in the tree, and no `catch` can clear it, while catching `InterruptedException` clears the flag. The last section of this lesson shows `runInterruptible`, which turns a cancel into an interrupt for the blocking code that needs one.",
}

# ---------------------------------------------------------------- section 2
K_KEEP = """// Naive: after a cancel, the pan stays in our kitchen
val ticket = desk.lend("jam-pan")
try {
    waitForTheJamToSet()        // cancelled here
} finally {
    desk.giveBack(ticket)       // suspends, so it throws at once
}"""
J_KEEP = """// Java equivalent: once the flag is set again, blocking cleanup fails at once
String ticket = desk.lend("jam-pan");
try {
    waitForTheJamToSet();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();   // keep the cancel request, as you should
} finally {
    desk.giveBack(ticket);                // blocks, sees the flag, throws InterruptedException
}"""

S2 = """Picture the cook making jam in a big pan borrowed from the community kitchen down the road. The jam takes a while to set, and the pan must go back afterwards, whatever happens. Giving it back means phoning the lending desk, so `giveBack` is a suspend function. The natural shape is `try` and `finally`:

""" + pair(K_KEEP, J_KEEP) + """

The `finally` block runs, as promised. But it runs inside a coroutine that is still cancelled, and there every suspension point throws `CancellationException` at once. `giveBack` never gets past its first one. `CleanupAfterCancel`, in the Try it below, calls the jam off at 100 ms:

```text
  borrowed the jam pan on ticket-7
cancel, plain suspend call in finally:
  giving back failed at once: JobCancellationException
  jam job finished, cancelled = true
```

`JobCancellationException` is the library's own subclass of `CancellationException`. The jam is off, and the pan is still in our kitchen. The community kitchen would like a word.

The fix is one wrapper: `finally { withContext(NonCancellable) { desk.giveBack(ticket) } }`. `NonCancellable` is a job that is always active. Inside that block, suspension points don't throw, so the call runs to the end. The coroutine itself stays cancelled: when the block finishes, the `CancellationException` carries on up the stack as before. Run with `-Pargs=fixed`, the demo printed `gave back the pan on ticket-7` about 50 ms after the cancel, and the job still finished as cancelled.

Use it in exactly this shape: `withContext(NonCancellable)`, inside a `finally`, around the cleanup call and nothing else. The docs warn against `launch(NonCancellable)` or `async(NonCancellable)`. A job passed to a builder replaces the parent, so the new coroutine leaves the tree: nothing waits for it, and nothing can cancel it. Lesson 6 of this track shows the same trap with another job. Keep the cleanup short, too. Nothing will cancel it for you, so a slow call inside it needs its own timeout, which the next section builds.

Cleanup that doesn't suspend needs nothing special. Closing a file is an ordinary call, not a suspending one, and it runs fine in a cancelled coroutine.

**A cancelled coroutine can't suspend. Wrap suspending cleanup in `withContext(NonCancellable)`.**

So far the guests have phoned to call things off. Often nobody phones. You decide in advance how long you're willing to wait."""

# ---------------------------------------------------------------- section 3
K_ORNULL = """val answer = withTimeoutOrNull(300.milliseconds) { bakery.ask("sourdough") }
    ?: "no answer: bake our own\""""
J_ORNULL = """// Java equivalent: a fallback value when the future is late
String answer = bakery.askAsync("sourdough")
    .completeOnTimeout("no answer: bake our own", 300, TimeUnit.MILLISECONDS)
    .join();"""
K_INTERRUPT = """withTimeoutOrNull(300.milliseconds) {
    runInterruptible(Dispatchers.IO) { hotline.ask("sourdough") }   // interrupted on cancel
}"""
J_INTERRUPT = """// Java equivalent: give up after the timeout and interrupt the worker
Future<String> f = io.submit(() -> hotline.ask("sourdough"));
try { return f.get(300, TimeUnit.MILLISECONDS); }
catch (TimeoutException e) { f.cancel(true); return null; }   // interrupts the blocked thread"""

S3 = """Before a big dinner, the cook also sets a kitchen timer on the bread order: if the bakery hasn't answered in a few minutes, she bakes her own. `withTimeout(d) { ... }` is that timer. It runs the block, and when `d` runs out, it cancels the block. The cancel is the ordinary kind from the first section: the block stops at its next suspension point, and `withTimeout` throws `TimeoutCancellationException`. `withTimeoutOrNull(d) { ... }` does the same, but returns `null` instead of throwing:

""" + pair(K_ORNULL, J_ORNULL) + """

Prefer `withTimeoutOrNull` when a timeout is an outcome you expect, as it is here. `TimeoutCancellationException` is a subclass of `CancellationException`, and that has a surprising effect. Inside `launch`, a timeout looks like an ordinary cancel, so a child that times out inside `coroutineScope` lets the scope finish normally, and nobody hears about it. If a timeout should fail the caller, turn it into a real error: `withTimeoutOrNull(d) { ... } ?: error("the bakery never answered")`.

A timer is still a cancel, and a cancel still only asks. So what happens when the block is stuck in a blocking call, one that holds its thread until it returns? The bakery from lesson 4 of this track still has an old order line, `BakeryHotline`, whose `ask` blocks the thread until somebody picks up. Let's wait 300 ms, and let the bakery take 1.5 s. `TimeoutsAndBlocking`, in the Try it below, tries four shapes, with `Thread.sleep` standing in for the call:

```text
withTimeout { delay }                              threw TimeoutCancellationException   after   307 ms
withTimeoutOrNull { delay }                        returned null                        after   304 ms
withTimeout { withContext(IO) { sleep } }          threw TimeoutCancellationException   after  1519 ms
withTimeoutOrNull { runInterruptible { sleep } }   returned null                        after   301 ms
```

The two `delay` lines stopped on time. The third line is the trap. The timer fired at 300 ms, but a thread blocked in `Thread.sleep` isn't at a suspension point. The thread stayed on the old phone line, listening to it ring, long after the timer had given up. Only when the call ended at 1.5 s did `withContext` notice the cancel and throw. The `Dispatchers.IO` thread, from the pool for blocking calls, was stuck the whole time. When the blocking call is the whole block, with no suspension at all, the timeout is ignored entirely, and the late answer comes back as if nothing had happened.

The fourth line is the fix. `runInterruptible(dispatcher) { ... }` runs blocking code on that dispatcher, and when the coroutine is cancelled, it interrupts the thread. It turns the resulting `InterruptedException` back into a `CancellationException`, so the caller sees an ordinary cancel:

""" + pair(K_INTERRUPT, J_INTERRUPT) + """

Here the kitchen picture breaks. A cook can put the phone down whenever she likes. `runInterruptible` can only interrupt, and that helps only if the blocking call listens for interrupts. `Thread.sleep` and `BlockingQueue.take` do. A read from an old-style `java.net.Socket` network connection doesn't, and database drivers vary, so give such a client its own timeout as well.

**A timeout is a cancel with a timer. A blocking call hears it only through `runInterruptible`.**

That covers the places a cancel can get lost. A cancel, though, is the polite way for a coroutine to end. The next lesson takes the rude one: a coroutine that fails."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a dinner called off halfway, a cook who heard the news between steps, and a helper who sorted the whole sack. Coroutines hear a cancel only at suspension points and checks, carry it as `CancellationException`, and need `NonCancellable` to clean up after it. A timeout is the same cancel with a timer.

Now search your own code for `runCatching` and `catch (e: Exception)` around suspend calls. Each one that doesn't rethrow `CancellationException` turns the next cancel into a list of fake failures.

Next, we'll burn a dish instead of calling it off. When a coroutine fails, who hears about it, and how do you stop one burnt tray from spoiling the rest?"""

L = {
 "id": "co-05",
 "title": "Cancellation and timeouts",
 "minutes": 35,
 "goal": "By the end you can make CPU loops and blocking calls respond to cancellation, keep CancellationException flowing instead of swallowing it, run suspending cleanup after a cancel, and choose between withTimeout and withTimeoutOrNull.",
 "opening": OPENING,
 "warmup": {
  "q": "A coroutine on `Dispatchers.Default` runs `for (lentil in sack) if (isStone(lentil)) stones++` over two million lentils, with no suspend calls inside the loop. Another coroutine calls `job.cancel()` halfway through. What happens?",
  "options": [
   "The loop stops at once, because `cancel()` stops the coroutine's thread",
   "The loop stops at the next lentil, because the compiler adds a check to every loop",
   "The loop runs to the end, and only then does the job finish as cancelled",
   "`cancel()` throws `IllegalStateException`, because the coroutine is busy"
  ],
  "answer": 2,
  "why": "Cancellation is cooperative. `cancel()` only marks the job as cancelling. The coroutine notices at its next suspension point or explicit check, and this loop has neither, so it sorts all two million lentils first, like the helper who never looks up. Java's `Future.cancel(true)` has the same limit: it sets a flag that somebody has to read."
 },
 "sections": [
  {
   "h": "A cancel is a request, heard only at suspension points and checks",
   "body": S0,
   "figure": {"svg": FIG, "caption": "The same cancel reaches three coroutines. Only the ones at a suspension point or a check stop, and their finally blocks run."},
   "try": {
    "title": "Cancel four sorting loops",
    "minutes": 4,
    "steps": [
     "Read `CancelABusyLoop.kt`. Each loop would sort its sack in about 1.5 s on an idle machine; the demo cancels it after 100 ms. Predict how long each one takes to stop.",
     "Run it.",
     "In the `ensureActive()` loop, change `1_000` to `10_000_000` and run it again. Predict first.",
     "Run the Java twin, which uses `Future.cancel(true)` and the interrupt flag."
    ],
    "code": demo("CancelABusyLoop.kt", "CancelABusyLoopJava.java"),
    "expect": "The loop with no check stops only when its sack is empty: about 1,400 ms after `cancel()` on an idle machine, and 2,851 ms here on a busy one. The other three stop within a few milliseconds (4, 10 and 1 ms here). With a check only every 10 million lentils, that loop stops late, at its next check, a few hundred milliseconds on. The Java twin shows the same split (1,425 and 0 ms here): `cancel(true)` reports success at once, but the loop that never reads the flag keeps its thread busy until it ends."
   },
   "refs": [
    {"title": "Cancellation and timeouts (Kotlin docs)", "url": "https://kotlinlang.org/docs/cancellation-and-timeouts.html", "kind": "read"},
    {"title": "ensureActive (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html", "kind": "docs"}
   ]
  },
  {
   "h": "Never swallow the CancellationException that carries the cancel",
   "body": S1,
   "aside": ASIDE,
   "try": {
    "title": "Swallow a cancel and count the damage",
    "minutes": 4,
    "steps": [
     "Read `SwallowedCancellation.kt`. The round of calls is cancelled at 250 ms, after 3 calls. Predict how many calls happen after the cancel, and how long `cancelAndJoin` takes.",
     "Run it.",
     "Run it with `-Pargs=fixed`, which rethrows `CancellationException`.",
     "Run the Java twin both ways and compare how long shutdown takes."
    ],
    "code": demo("SwallowedCancellation.kt", "SwallowedCancellationJava.java", " -Pargs=fixed", " -Pargs=fixed"),
    "expect": "Swallowing: 3 calls before the cancel and 17 after, and `cancelAndJoin` returns within a few milliseconds (8 ms here), because every remaining `delay` threw at once. Fixed: 0 calls after the cancel. The swallowing Java twin also makes 17 more calls, but over about 1.7 s (1,719 ms here): catching the interrupt cleared the flag, so the later sleeps were normal sleeps. Restoring the flag and returning stops it at once (1 ms here)."
   }
  },
  {
   "h": "Cleanup after a cancel: give the pan back inside NonCancellable",
   "body": S2,
   "try": {
    "title": "Keep the pan, then give it back",
    "minutes": 3,
    "steps": [
     "Read `CleanupAfterCancel.kt`. The jam is called off while it sets. Predict whether `gave back the pan` prints.",
     "Run it.",
     "Run it with `-Pargs=fixed`, which wraps `giveBack` in `withContext(NonCancellable)`.",
     "Run the Java twin both ways."
    ],
    "code": demo("CleanupAfterCancel.kt", "CleanupAfterCancelJava.java", " -Pargs=fixed", " -Pargs=fixed"),
    "expect": "Without the wrapper, `giving back failed at once: JobCancellationException` prints, and the pan is never returned. With `-Pargs=fixed`, `gave back the pan on ticket-7` prints about 50 ms after the cancel, and the job still finishes as cancelled. The Java twin fails the same way with `InterruptedException`, and its fix is to clear the flag around the cleanup and restore it afterwards."
   },
   "refs": [
    {"title": "NonCancellable (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/", "kind": "docs"}
   ]
  },
  {
   "h": "A timeout is a cancel with a timer, and blocking calls don't hear it",
   "body": S3,
   "try": {
    "title": "Time out the bakery four ways",
    "minutes": 4,
    "steps": [
     "Read `TimeoutsAndBlocking.kt`. The bakery takes 1.5 s to answer and every call waits 300 ms. Predict the outcome and the time for each line.",
     "Run it.",
     "Delete the `withContext(Dispatchers.IO)` wrapper in the third case, leaving `withTimeout(300) { Thread.sleep(1_500); \"bread ready\" }`. Predict, then run.",
     "Run the Java twin and compare `orTimeout` with `get` plus `cancel(true)`."
    ],
    "code": demo("TimeoutsAndBlocking.kt", "TimeoutsAndBlockingJava.java"),
    "expect": "The two `delay` cases end at about 300 ms (307 and 304 ms here): one throws, one returns null. The `withContext(IO)` case throws too, but only after about 1,500 ms (1,519 ms here), when the sleep is over. `runInterruptible` returns null at about 300 ms. After your change, the bare sleep returns `bread ready` after 1,500 ms: the block never suspended, so the timeout was ignored. In the Java twin, `orTimeout` gives the caller its exception on time (320 ms here) while the abandoned call finishes at 1,519 ms anyway, and `cancel(true)` interrupts the call at about 300 ms."
   },
   "refs": [
    {"title": "withTimeout (API reference: the pitfalls section)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html", "kind": "docs"},
    {"title": "runInterruptible (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "Stopping a CPU loop: Future.cancel(true) vs Job.cancel()",
  "java": {"title": "LentilSort.java", "src": "Future<Integer> f = pool.submit(() -> {\n    int stones = 0;\n    for (int i = 0; i < lentils.length; i++) {\n        if (i % 1_000 == 0 && Thread.currentThread().isInterrupted()) {\n            throw new CancellationException(\"sorting stopped at \" + i);   // 1. look at the flag\n        }\n        if (isStone(lentils[i])) stones++;\n    }\n    return stones;\n});\n\nf.cancel(true);   // 2. sets the worker's interrupt flag; the loop stops at its next check"},
  "kotlin": {"title": "LentilSort.kt", "src": "val job = scope.async(Dispatchers.Default) {\n    var stones = 0\n    for ((i, lentil) in lentils.withIndex()) {\n        if (i % 1_000 == 0) ensureActive()   // 1. throws CancellationException once cancelled\n        if (isStone(lentil)) stones++\n    }\n    stones\n}\n\njob.cancel()   // 2. marks the job cancelled; the loop stops at its next check"},
  "note": "Both models are cooperative, and both loops need the same explicit check, once every thousand lentils. The difference is what carries the request. Java's interrupt is a flag on one thread. It doesn't reach other threads the task started, and catching `InterruptedException` clears it, so a careless `catch` loses it for good. A coroutine's cancel is a state on its job. It reaches every child in the tree, it stays set whatever you catch, and every suspension point in the library checks it for you, so most coroutine code needs no explicit check at all. Only CPU loops like this one, and blocking calls (which need `runInterruptible`), have to be taught to look up."
 },
 "worked": {
  "title": "Make an oven watcher stop cleanly",
  "steps": [
   {"say": "The community kitchen has shared ovens. This function books one, then checks every 5 seconds whether the bread is done. When the cook calls the evening off, the function seems to hang, and the oven stays booked, so nobody else can use it. Find the three problems before you read on.",
    "code": "suspend fun waitForBread(loaf: String): Bread {\n    val booking = ovens.book(loaf)\n    try {\n        while (true) {\n            try {\n                val bread = ovens.check(loaf)\n                if (bread.isDone) return bread\n                delay(5.seconds)\n            } catch (e: Exception) {\n                log.warn(\"oven check failed for $loaf\", e)\n            }\n        }\n    } finally {\n        ovens.release(booking)   // suspend: a phone call to the community kitchen\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same bugs\nBread waitForBread(String loaf) {\n    Booking booking = ovens.book(loaf);\n    try {\n        while (true) {\n            try {\n                Bread bread = ovens.check(loaf);\n                if (bread.isDone()) return bread;\n                Thread.sleep(5_000);\n            } catch (Exception e) {              // also catches InterruptedException\n                log.warn(\"oven check failed for {}\", loaf, e);\n            }\n        }\n    } finally {\n        ovens.release(booking);                 // fails at once if the flag is set\n    }\n}", "alt_lang": "java"},
   {"say": "Problem 1: `catch (e: Exception)` swallows the `CancellationException` from `delay`, so a cancelled watcher spins. Catch only the oven's own error, and let the cancel through.",
    "code": "        while (true) {\n            try {\n                val bread = ovens.check(loaf)\n                if (bread.isDone) return bread\n            } catch (e: OvenException) {        // 1. only what we expect from the call\n                log.warn(\"oven check failed for $loaf\", e)\n            }\n            delay(5.seconds)                    //    outside the try: a cancel ends the loop\n        }", "lang": "kotlin",
    "alt_code": "        while (true) {\n            try {\n                Bread bread = ovens.check(loaf);\n                if (bread.isDone()) return bread;\n            } catch (OvenException e) {           // 1. only what we expect from the call\n                log.warn(\"oven check failed for {}\", loaf, e);\n            }\n            Thread.sleep(5_000);                  //    InterruptedException now propagates\n        }", "alt_lang": "java"},
   {"say": "Problem 2: the release suspends in a cancelled coroutine, so it throws before the phone even rings. Wrap it in `NonCancellable`, with its own short timeout, so a phone nobody answers can't hold up the evening.",
    "code": "    } finally {\n        // 2. cleanup that suspends must run non-cancellable, and bounded\n        withContext(NonCancellable) {\n            withTimeoutOrNull(2.seconds) { ovens.release(booking) }\n        }\n    }", "lang": "kotlin",
    "alt_code": "    } finally {\n        // 2. clear the flag for the cleanup, then restore it\n        boolean interrupted = Thread.interrupted();\n        try { ovens.release(booking); }\n        finally { if (interrupted) Thread.currentThread().interrupt(); }\n    }", "alt_lang": "java"},
   {"say": "Problem 3: nothing bounds the whole wait. Give the caller a deadline, and treat running out as an expected outcome rather than an exception.",
    "code": "// 3. the caller decides how long the bread may take\nval bread: Bread? = withTimeoutOrNull(10.minutes) { waitForBread(\"rye\") }\nif (bread == null) bakeFlatbread()   // plan B", "lang": "kotlin",
    "alt_code": "// 3. the caller decides how long the bread may take\nFuture<Bread> f = pool.submit(() -> waitForBread(\"rye\"));\ntry { serve(f.get(10, TimeUnit.MINUTES)); }\ncatch (TimeoutException e) { f.cancel(true); bakeFlatbread(); }", "alt_lang": "java"},
   {"say": "Self-check: the timeout in step 3 cancels `waitForBread` while it is suspended in `delay`. Trace what happens. (The `delay` throws `TimeoutCancellationException`, which passes the narrow `catch`. The `finally` releases the oven under `NonCancellable`, and `withTimeoutOrNull` turns the exception into `null`.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix four cancellation bugs in the kitchen",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/SortLentils.kt", f"{lab}/main/{P}/SupplierCalls.kt", f"{lab}/main/{P}/BorrowedPot.kt", f"{lab}/main/{P}/BakeryHotline.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l05.*'",
  "steps": [
   "Meet the code. Each file holds one small kitchen job, and each stub is the buggy code, with a KDoc that says what's wrong. `countStones` picks through a sack of lentils, `confirmEach` phones each supplier in turn, `withBorrowed` borrows a pan from the lending desk and must always give it back, and `askBakery` asks the bakery's old blocking phone line. Run the tests: four of eight fail, one per file.",
   "`SortLentils.kt`: make `countStones` check for cancellation at least once every 1,000 lentils.",
   "`SupplierCalls.kt`: keep `runCatching`, but make a `CancellationException` end the round instead of being logged as a failed call.",
   "`BorrowedPot.kt`: make the `giveBack` call in `finally` run to the end even when the caller was cancelled.",
   "`BakeryHotline.kt`: return `null` on timeout instead of throwing, and make the timeout interrupt the blocked `ask` call.",
   "Run the tests until all eight pass, then run them once more."
  ],
  "hints": [
   "`countStones` is a plain suspend function with no scope, so call `currentCoroutineContext().ensureActive()`. Read the context once, before the loop.",
   "Import `CancellationException` from `kotlin.coroutines.cancellation` (or `kotlinx.coroutines`). Both name the same class.",
   "The `giveBack` fix is one wrapper: `withContext(NonCancellable) { ... }`.",
   "`runInterruptible(Dispatchers.IO) { ... }` replaces `withContext(Dispatchers.IO) { ... }` for blocking code that should be interrupted on cancel."
  ],
  "done_when": "All eight tests in `CancellationTest` pass, twice in a row."
 },
 "drill": {
  "title": "A cancellable job from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `suspend fun labelJars(jars: List<Jar>, loan: Loan)` that runs on `Dispatchers.Default`, checks for cancellation every 500 jars, and calls `label(jar)`, which can throw `LabelException` (log it and skip that jar). It must always return the borrowed label printer with the suspending `loan.giveBack()`, even after a cancel.",
  "answer": {"lang": "kotlin", "src": "suspend fun labelJars(jars: List<Jar>, loan: Loan) {\n    try {\n        withContext(Dispatchers.Default) {\n            for ((i, jar) in jars.withIndex()) {\n                if (i % 500 == 0) ensureActive()            // cooperate with a cancel\n                try {\n                    label(jar)\n                } catch (e: LabelException) {               // only what we expect\n                    log.warn(\"skipping ${jar.id}\", e)\n                }\n            }\n        }\n    } finally {\n        withContext(NonCancellable) { loan.giveBack() }    // suspending cleanup\n    }\n}",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: read the interrupt flag, clear it around the cleanup\nvoid labelJars(List<Jar> jars, Loan loan) {\n    try {\n        for (int i = 0; i < jars.size(); i++) {\n            if (i % 500 == 0 && Thread.currentThread().isInterrupted()) return;   // cooperate with a cancel\n            try {\n                label(jars.get(i));\n            } catch (LabelException e) {                                      // only what we expect\n                log.warn(\"skipping {}\", jars.get(i).id(), e);\n            }\n        }\n    } finally {\n        boolean interrupted = Thread.interrupted();\n        try { loan.giveBack(); }                                              // blocking cleanup\n        finally { if (interrupted) Thread.currentThread().interrupt(); }\n    }\n}"}}
 },
 "recap": [
  "Cancellation is cooperative. `cancel()` marks the job, and the coroutine stops at its next suspension point or explicit check. CPU loops need `ensureActive()`, `isActive` or `yield()`.",
  "Cancellation travels as `CancellationException`. `runCatching`, `catch (e: Exception)` and `catch (e: Throwable)` all catch it, so rethrow it or catch narrower types. Catching it never undoes the cancel.",
  "In a cancelled coroutine every suspension point throws at once. Run suspending cleanup in `finally` inside `withContext(NonCancellable)`, and never pass `NonCancellable` to `launch` or `async`.",
  "`withTimeout` throws `TimeoutCancellationException` (a `CancellationException`), and `withTimeoutOrNull` returns `null`. Inside `launch`, a timeout doesn't fail the parent unless you turn it into an error.",
  "The limit: a cancel only asks. Blocking code hears it only through `runInterruptible`, and only if the call responds to interrupts; for the rest, give the client its own timeout."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "`val job = scope.launch(Dispatchers.Default) { while (true) { weigh(nextJar()) } }`, where `weigh` and `nextJar` are plain functions. You call `job.cancelAndJoin()`. What happens?",
   "options": ["It returns at once, because `cancel` stops the coroutine", "It returns after the current loop iteration", "It never returns: the loop has no suspension point and never checks", "The caller gets a `CancellationException` thrown from `cancelAndJoin`"],
   "answer": 2,
   "why": "Nothing in the loop looks at the job, so the cancel is never noticed, and `cancelAndJoin` waits forever. Add `ensureActive()` or `yield()` to the loop, or loop on `while (isActive)`. The tempting \"after the current iteration\" would need a check at the top of each iteration, and there is none."},
  {"q": "A coroutine was cancelled while it waited in `delay`. Its `finally` block must call the suspending `desk.giveBack(ticket)`. Which line does that correctly?",
   "options": ["`try { desk.giveBack(ticket) } catch (e: CancellationException) { }`", "`withContext(NonCancellable) { desk.giveBack(ticket) }`", "`launch(NonCancellable) { desk.giveBack(ticket) }`", "`GlobalScope.launch { desk.giveBack(ticket) }`"],
   "answer": 1,
   "why": "Inside `withContext(NonCancellable)` suspension points don't throw, so `giveBack` runs to the end, and the cancel carries on afterwards. Catching the exception just loses the call. `launch(NonCancellable)` and `GlobalScope` both start a coroutine outside the tree that nothing waits for, so the program can finish before the pan goes back."},
  {"q": "What does this print?\n\n```kotlin\ncoroutineScope {\n    launch { withTimeout(100) { delay(1_000) } }\n}\nprintln(\"done\")\n```",
   "options": ["`done`, after about 100 ms", "Nothing: `coroutineScope` throws `TimeoutCancellationException`", "`done`, after about 1,000 ms", "Nothing: the program hangs"],
   "answer": 0,
   "why": "`TimeoutCancellationException` is a `CancellationException`, so the child counts as cancelled, not failed, and the scope completes normally. If a timeout must fail the caller, write `withTimeoutOrNull(100) { ... } ?: error(\"timed out\")`."},
  {"q": "`withTimeout(500) { withContext(Dispatchers.IO) { Thread.sleep(3_000) } }`. How long does the caller wait, and what does it get?",
   "options": ["About 500 ms, then `TimeoutCancellationException`", "About 500 ms, then `null`", "About 3 s, then `TimeoutCancellationException`", "About 3 s, then the block's result"],
   "answer": 2,
   "why": "The timer fires at 500 ms and cancels the coroutine, but `Thread.sleep` doesn't see it. When the sleep ends, `withContext` checks, finds the job cancelled, and the timeout comes out as the exception. `runInterruptible(Dispatchers.IO)` would interrupt the sleep at 500 ms."},
  {"q": "From the executors track: a task is blocked in `Thread.sleep(5_000)` when someone calls `future.cancel(true)` on it. What happens to the task?",
   "options": ["Nothing until the sleep ends, then it carries on", "The thread is stopped and the task's `finally` blocks are skipped", "The future completes normally with `null`", "`sleep` throws `InterruptedException` at once, and the task can clean up and stop"],
   "answer": 3,
   "why": "`cancel(true)` interrupts the worker thread, and `sleep` responds to interrupts by throwing. What the task does next is up to its code: restore the flag and stop, or swallow it and carry on. That is the Java version of `runInterruptible`.",
   "from": "exec-04"}
 ],
 "flashcards": [
  {"front": "Does `job.cancel()` stop a CPU loop with no suspend calls?", "back": "No. Cancellation is cooperative: the loop must call `ensureActive()` or `yield()`, or check `isActive`."},
  {"front": "What does a suspension point such as `delay` do in a cancelled coroutine?", "back": "It throws `CancellationException` at once, without suspending."},
  {"front": "Why is `runCatching { suspendCall() }` risky inside a coroutine?", "back": "It catches every `Throwable`, `CancellationException` included, so the loop carries on in a coroutine that is still cancelled. Rethrow `CancellationException`."},
  {"front": "How do you call a suspending cleanup function in `finally` after a cancel?", "back": "`withContext(NonCancellable) { giveBack() }`"},
  {"front": "On timeout, what do `withTimeout` and `withTimeoutOrNull` do?", "back": "`withTimeout` throws `TimeoutCancellationException`, a subclass of `CancellationException`. `withTimeoutOrNull` returns `null`."},
  {"front": "Can `withTimeout` stop a `Thread.sleep(10_000)` inside it?", "back": "No. Blocking calls ignore cancellation. Wrap them in `runInterruptible(Dispatchers.IO) { ... }` so the thread is interrupted."},
  {"front": "How does a plain suspend function, with no scope, check for cancellation?", "back": "`currentCoroutineContext().ensureActive()`."}
 ],
 "terms": [
  {"term": "Job", "plain": "The handle to a coroutine's life: you can wait for it or cancel it."},
  {"term": "Cooperative cancellation", "plain": "Cancelling only asks; the code stops when it next checks or reaches a suspension point."},
  {"term": "Suspension point", "plain": "A call to a suspend function such as `delay`, `await` or `withContext`. Library ones check for cancellation."},
  {"term": "CancellationException", "plain": "The exception that carries a cancel through the coroutine's code. Catching it without rethrowing breaks cancellation."},
  {"term": "NonCancellable", "plain": "A job that is always active. `withContext(NonCancellable)` lets cleanup suspend after a cancel."},
  {"term": "TimeoutCancellationException", "plain": "What `withTimeout` throws. It is a `CancellationException`, so a parent treats it as a cancel, not a failure."},
  {"term": "runInterruptible", "plain": "Runs blocking code on a dispatcher and interrupts its thread if the coroutine is cancelled."}
 ],
 "explain_back": {
  "prompt": "A friend wrapped every call in the evening's supplier round in `runCatching`, \"so one busy line never stops the round\". When the dinner was called off, the log listed seventeen failed calls that had never failed. Explain what happened and how you'd change the code.",
  "answer": "Calling the dinner off cancelled the coroutine running the round. A cancel reaches the code as a CancellationException thrown from the next suspension point, and runCatching catches every Throwable, so it caught that too and logged the call in progress as failed. Catching it didn't undo the cancel: the coroutine was still cancelled, so the next call threw at its first suspension point, got caught and logged the same way, and so on through all seventeen remaining calls. Then the function returned normally. I'd keep the per-call error handling, but rethrow CancellationException before logging anything, or catch only the exceptions a phone call is expected to throw. Then a cancel ends the round at the call in progress, and any cleanup that suspends goes in a finally inside withContext(NonCancellable)."
 },
 "deeper": {
  "minutes": 10,
  "body": "A `CancellationException` doesn't always mean \"I was cancelled\". If you `await()` a `Deferred` that someone else cancelled, `await` throws `CancellationException` in your coroutine, even though your coroutine is fine. The kotlinx.coroutines 1.11 KDoc calls this a legacy behavior that can't be changed compatibly: your coroutine then ends as \"cancelled\", so its parent isn't told and the work quietly stops. If you catch it, call `currentCoroutineContext().ensureActive()` in the `catch`. It throws only if *your* coroutine was cancelled, so after it you know the exception came from the thing you awaited, and you can turn it into a real error.\n\nThe library also gives a **prompt cancellation guarantee**. If a coroutine is cancelled while suspended, it resumes with `CancellationException` even when the value it was waiting for had already arrived. `withContext` checks for cancellation both on entry and when its block returns. So `val pan = withContext(io) { desk.lendBlocking() }` can lose a pan: the block borrowed it, the caller was cancelled in the meantime, and the result is thrown away. Borrow and give back inside the same block, or use the cleanup function of `CancellableContinuation.resume` when you write the bridge yourself (lesson 1 of this track).\n\nTimeouts have one more subtle rule. The KDoc says cancellation on timeout \"may happen at any time, even after the block finishes executing but before the caller gets resumed\". So never write `withTimeout { pan = desk.lend() }` and expect `pan` to be either unset or yours. Borrow outside the timeout, or give it back in the block's own `finally`.\n\nFlows, which lesson 7 of this track introduces, have the same cooperative rule at a smaller scale. A `flow { }` builder checks for cancellation at every `emit`, but `list.asFlow()` and `(1..n).asFlow()` don't, so add `.cancellable()` to a long one that must stop on time.\n\nFinally, `runBlocking` bridges in the other direction. If the thread blocked in `runBlocking` is interrupted, the coroutine is cancelled, and `runBlocking` throws `InterruptedException`. That's how coroutine code called from a plain Java worker thread can still be stopped by an executor's `shutdownNow()`."
 },
 "sources": [
  {"title": "Cancellation and timeouts (Kotlin docs)", "url": "https://kotlinlang.org/docs/cancellation-and-timeouts.html"},
  {"title": "withTimeout (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html"},
  {"title": "runInterruptible (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html"},
  {"title": "NonCancellable (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/"}
 ]
}
out = ROOT / "content/lessons/co-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
