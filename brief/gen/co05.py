import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l05"
J = "java/workbench/coroutines/l05"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l05.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


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
    '<text class="t-s" x="385" y="126" text-anchor="middle">keeps computing until the loop ends</text>'
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

L = {
 "id": "co-05",
 "title": "Cancellation and timeouts",
 "minutes": 35,
 "goal": "By the end you can make CPU loops and blocking calls respond to cancellation, keep CancellationException flowing instead of swallowing it, run suspending cleanup after a cancel, and choose between withTimeout and withTimeoutOrNull.",
 "warmup": {
  "q": "A coroutine on `Dispatchers.Default` runs `for (t in transactions) score(t)` over two million transactions, with no suspend calls inside the loop. Another coroutine calls `job.cancel()` halfway through. What happens?",
  "options": [
   "The loop stops at once, because `cancel()` stops the coroutine's thread",
   "The loop stops at the next iteration, because the compiler adds a check to every loop",
   "The loop runs to the end, and only then does the job finish as cancelled",
   "`cancel()` throws `IllegalStateException`, because the coroutine is busy"
  ],
  "answer": 2,
  "why": "Cancellation is cooperative. `cancel()` only marks the job as cancelling. The coroutine notices at its next suspension point or explicit check, and this loop has neither, so it finishes all two million transactions first. Java's `Future.cancel(true)` has the same limit: it sets a flag that someone has to read."
 },
 "sections": [
  {
   "h": "Cancellation is a request your code has to notice",
   "body": "`job.cancel()` doesn't stop a coroutine. It marks the job as cancelling, and that's all. The coroutine stops the next time it reaches a **suspension point** that checks: `delay`, `withContext`, `await`, `join`, a channel's `send` or `receive`, `yield`. That call throws `CancellationException`, the exception unwinds the stack, `finally` blocks run, and the job ends as cancelled. A coroutine that is already suspended notices at once: one waiting in `delay(10_000)` is resumed with the exception straight away.\n\nCode that never reaches such a point never notices. A CPU loop over two million card transactions runs to the end. So does a blocking call such as `Thread.sleep` or a JDBC query (section 4). This is **cooperative cancellation**. Java has the same model: `Future.cancel(true)` sets the interrupt flag, and a loop that never reads it keeps going.\n\nA CPU loop cooperates by checking now and then:\n\n```kotlin\nsuspend fun scan(rows: List<Txn>) = withContext(Dispatchers.Default) {\n    for ((i, row) in rows.withIndex()) {\n        if (i % 1_000 == 0) ensureActive()   // throws CancellationException once cancelled\n        score(row)\n    }\n}\n```\n\n```java\n// Java equivalent: read the interrupt flag yourself\nvoid scan(List<Txn> rows) {\n    for (int i = 0; i < rows.size(); i++) {\n        if (i % 1_000 == 0 && Thread.currentThread().isInterrupted()) throw new CancellationException();\n        score(rows.get(i));\n    }\n}\n```\n\nYou have three tools. `ensureActive()` throws if the job is cancelled. `isActive` returns a boolean, for loops that want to stop quietly: `while (isActive) { ... }`. `yield()` checks too, and also lets other coroutines waiting for the same dispatcher run, which matters when a long loop shares a small dispatcher. A check is just a read of the job's state, so it costs almost nothing, but once every few hundred rows is plenty.\n\nWatch which job you are checking. Inside `launch { }`, `isActive` and `ensureActive()` refer to that coroutine. A plain suspend function has no scope receiver, so write `currentCoroutineContext().ensureActive()`. In a lambda nested inside another scope, a bare `isActive` can quietly refer to the outer scope.\n\nFlow (lesson 7 of this track) has the same trap at a smaller scale. A `flow { }` builder checks on every `emit`, but `asFlow()` doesn't:\n\n```kotlin\n(1..5).asFlow().collect { if (it == 3) cancel(); println(it) }                // prints 1 to 5\n(1..5).asFlow().cancellable().collect { if (it == 3) cancel(); println(it) }  // prints 1 to 3\n```\n\n```java\n// Java equivalent: a stream never reads the interrupt flag on its own\nIntStream.rangeClosed(1, 5).forEach(i -> {\n    if (i == 3) Thread.currentThread().interrupt();   // ask to stop\n    System.out.println(i);                            // prints 1 to 5\n});\n```",
   "figure": {"svg": FIG, "caption": "The same cancel reaches three coroutines. Only the ones at a suspension point or a check stop, and their finally blocks run."},
   "try": {
    "title": "Cancel four CPU loops",
    "minutes": 4,
    "steps": [
     "Read `CancelABusyLoop.kt`. Each loop would take about 1.5 s; the demo cancels it after 100 ms. Predict how long each one takes to stop.",
     "Run it.",
     "In the `ensureActive()` loop, change `1_000` to `10_000_000` and run it again. Predict first.",
     "Run the Java twin, which uses `Future.cancel(true)` and the interrupt flag."
    ],
    "code": tryit("CancelABusyLoop.kt", "CancelABusyLoopJava.java"),
    "expect": "The loop with no check stops about 1,000 ms after `cancel()` (or more on a slow machine): it simply finished its work. The other three stop within a few milliseconds. With a check only every 10 million rows, that loop stops late, at its next check (10 million rows take a couple of hundred ms). The Java twin shows the same split: `cancel(true)` reports success at once, but the loop that never reads the flag keeps its thread busy until it ends."
   },
   "refs": [
    {"title": "Cancellation and timeouts (Kotlin docs)", "url": "https://kotlinlang.org/docs/cancellation-and-timeouts.html", "kind": "read"},
    {"title": "ensureActive (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html", "kind": "docs"}
   ]
  },
  {
   "h": "CancellationException carries the cancel, so never swallow it",
   "body": "Cancellation travels as an exception, `CancellationException` (on the JVM it is `java.util.concurrent.CancellationException`). That is the point of it: it unwinds the stack, runs every `finally` and closes every `use`. It is also the danger. Any `catch` that catches it stops it.\n\n```kotlin\nfor (id in batchIds) {\n    runCatching { settle(id) }                                   // also catches CancellationException\n        .onFailure { log.warn(\"batch $id failed\", it); failed += id }\n}\n```\n\n```java\n// Java equivalent: swallowing InterruptedException\nfor (String id : batchIds) {\n    try { settle(id); }\n    catch (InterruptedException e) { log.warn(\"batch {} failed\", id, e); failed.add(id); }  // the cancel request is gone\n}\n```\n\n`runCatching` catches every `Throwable`. So do `catch (e: Exception)` and `catch (e: Throwable)`, because `CancellationException` extends `IllegalStateException`. Here is what happens when the pod shuts down and cancels this run. The batch in progress is logged as failed. The loop moves to the next batch, which starts, hits its first suspension point, throws at once and is logged as failed too, and so on to the end of the list. Then the function returns normally, with a list of \"failed\" batches that never failed. In a `while (true)` polling loop it is worse: every `delay` throws at once, the exception is swallowed, and the loop spins at full CPU forever.\n\nThe fix is to let it through. With `runCatching`, rethrow it first: `.onFailure { if (it is CancellationException) throw it; ... }`. With `try`, put `catch (e: CancellationException) { throw e }` before the general clause. Better still, catch only what you expect, such as `IOException` or your client's error type, and let everything else propagate.\n\nThe Java rule is the same: catch `InterruptedException`, restore the flag with `Thread.currentThread().interrupt()`, and stop. But the failure looks different, and the Try it shows how. A swallowed interrupt clears the flag, so the next `sleep` sleeps normally and the loop just runs to the end at its usual pace. A swallowed cancellation clears nothing. The job stays cancelled, every later suspension point throws at once, and the loop races to the end in a few milliseconds.\n\nSo a coroutine that is cancelled cannot be talked out of it. Catching the exception only means the code after the catch runs inside a coroutine that is still cancelled.",
   "try": {
    "title": "Swallow a cancel and count the damage",
    "minutes": 4,
    "steps": [
     "Read `SwallowedCancellation.kt`. The poller is cancelled at 250 ms, after 3 attempts. Predict how many attempts run after the cancel, and how long `cancelAndJoin` takes.",
     "Run it.",
     "Run it with `-Pargs=fixed`, which rethrows `CancellationException`.",
     "Run the Java twin both ways and compare how long shutdown takes."
    ],
    "code": tryit("SwallowedCancellation.kt", "SwallowedCancellationJava.java", " -Pargs=fixed", " -Pargs=fixed"),
    "expect": "Swallowing: 17 attempts after the cancel, and `cancelAndJoin` returns within a few milliseconds, because every remaining `delay` threw at once. Fixed: 0 attempts after the cancel. The swallowing Java twin also runs 17 more attempts, but over about 1.7 s: catching the interrupt cleared the flag, so the later sleeps were normal sleeps. Restoring the flag and returning stops it at once."
   }
  },
  {
   "h": "A cancelled coroutine can't suspend, so cleanup needs NonCancellable",
   "body": "`finally` blocks run when a coroutine is cancelled, but they run inside a coroutine that is still cancelled. There, every suspension point throws `CancellationException` at once. Cleanup that suspends never gets past its first suspension:\n\n```kotlin\nval hold = issuer.placeHold(amount)\ntry {\n    awaitChallenge()             // cancelled here\n} finally {\n    issuer.releaseHold(hold)     // suspends, so it throws at once: the hold stays on the card\n}\n```\n\n```java\n// Java equivalent: once the flag is set again, blocking cleanup fails at once\nString hold = issuer.placeHold(amount);\ntry {\n    awaitChallenge();\n} catch (InterruptedException e) {\n    Thread.currentThread().interrupt();   // keep the cancel request, as you should\n} finally {\n    issuer.releaseHold(hold);             // blocks, sees the flag, throws InterruptedException\n}\n```\n\nThe fix is one wrapper: `finally { withContext(NonCancellable) { issuer.releaseHold(hold) } }`.\n\n`NonCancellable` is a job that is always active. Inside that block, suspension points don't throw, so the release runs to the end. The coroutine itself stays cancelled. When the block finishes, the `CancellationException` carries on up the stack as before.\n\nUse it in exactly this shape: `withContext(NonCancellable)`, in a `finally` (or a cleanup `catch`), around the cleanup call and nothing else. The docs warn against `launch(NonCancellable)` or `async(NonCancellable)`. Passing a job to a builder replaces the parent, so the new coroutine leaves the tree from lesson 3 of this track: nothing waits for it and nothing can cancel it. And keep the cleanup short. Nothing will cancel it for you, so give a slow network call its own `withTimeout` inside the block.\n\nCleanup that doesn't suspend needs nothing special. Closing a file, returning a JDBC connection to its pool, `mutex.unlock()` and `semaphore.release()` are ordinary calls and run fine in a cancelled coroutine.\n\nThe same rule explains a quieter loss. If a coroutine is cancelled while it waits for a call that returns a resource, such as a pooled session, it resumes with `CancellationException` even if the resource was already on its way. The resource is never handed to your code, so your code can't close it. Lesson 1 of this track showed the fix on the callback side: the `onCancellation` lambda of `resume` releases it.",
   "try": {
    "title": "Leave a hold on the card, then release it",
    "minutes": 3,
    "steps": [
     "Read `CleanupAfterCancel.kt`. The payment is cancelled while it waits for a 3-D Secure challenge. Predict whether `released hold-4250` prints.",
     "Run it.",
     "Run it with `-Pargs=fixed`, which wraps the release in `withContext(NonCancellable)`.",
     "Run the Java twin both ways."
    ],
    "code": tryit("CleanupAfterCancel.kt", "CleanupAfterCancelJava.java", " -Pargs=fixed", " -Pargs=fixed"),
    "expect": "Without the wrapper, `release failed at once: JobCancellationException` prints, and the hold is never released. With `-Pargs=fixed`, `released hold-4250` prints about 50 ms after the cancel, and the job still finishes as cancelled. The Java twin fails the same way with `InterruptedException`, and the fix there is to clear the flag around the cleanup and restore it afterwards."
   },
   "refs": [
    {"title": "NonCancellable (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-non-cancellable/", "kind": "docs"}
   ]
  },
  {
   "h": "Timeouts are cancellation with a clock",
   "body": "`withTimeout(d) { ... }` runs the block and cancels it when `d` runs out. The cancellation is the ordinary kind: the block stops at its next suspension point, and `withTimeout` throws `TimeoutCancellationException`. `withTimeoutOrNull(d) { ... }` does the same and returns `null` instead of throwing.\n\n```kotlin\nval decision = withTimeoutOrNull(800.milliseconds) { issuer.authorize(request) }\n    ?: Decision.TIMED_OUT          // decline, or route to the fallback acquirer\n```\n\n```java\n// Java equivalent: a fallback value when the future is late\nDecision decision = issuer.authorizeAsync(request)\n    .completeOnTimeout(Decision.TIMED_OUT, 800, TimeUnit.MILLISECONDS)\n    .join();\n```\n\nPrefer `withTimeoutOrNull` when a timeout is an outcome you expect. `TimeoutCancellationException` is a subclass of `CancellationException`, and that has a surprising effect. Inside `launch`, a timeout looks like an ordinary cancel, so the docs' own pitfall applies: a child that times out inside `coroutineScope` lets the scope finish normally, and nobody hears about it. If a timeout should fail the caller, turn it into a real error: `withTimeoutOrNull(d) { ... } ?: error(\"issuer timed out\")`.\n\nA timeout is still cooperative, so it can't stop a blocking call. A thread blocked in `Thread.sleep`, a socket read or a JDBC call is not at a suspension point. `withTimeout(300) { withContext(Dispatchers.IO) { client.lookup(bin) } }` waits for the whole call and only then throws, and the IO thread stays busy the whole time. If the blocking call is the entire block, with no suspension at all, the timeout is ignored and the late result comes back as if nothing had happened.\n\nFor blocking code that responds to interrupts, use `runInterruptible`:\n\n```kotlin\nwithTimeoutOrNull(300.milliseconds) {\n    runInterruptible(Dispatchers.IO) { binDirectory.lookup(bin) }   // interrupted on cancel\n}\n```\n\n```java\n// Java equivalent: give up after the timeout and interrupt the worker\nFuture<String> f = io.submit(() -> binDirectory.lookup(bin));\ntry { return f.get(300, TimeUnit.MILLISECONDS); }\ncatch (TimeoutException e) { f.cancel(true); return null; }   // interrupts the blocked thread\n```\n\n`runInterruptible` runs the block on the dispatcher you give it. When the coroutine is cancelled, it interrupts that thread, and it turns the resulting `InterruptedException` back into a `CancellationException`. It only helps if the blocking call responds to interrupts. `Thread.sleep`, `BlockingQueue.take` and `java.nio` interruptible channels do. A classic socket read on a platform thread doesn't, and JDBC drivers vary, so set the client's own timeout too.",
   "try": {
    "title": "Time out a slow issuer four ways",
    "minutes": 4,
    "steps": [
     "Read `TimeoutsAndBlocking.kt`. The issuer takes 1.5 s and every call gets 300 ms. Predict the outcome and the time for each line.",
     "Run it.",
     "Delete the `withContext(Dispatchers.IO)` wrapper in the third case, leaving `withTimeout(300) { Thread.sleep(1_500); \"approved\" }`. Predict, then run.",
     "Run the Java twin and compare `orTimeout` with `get` plus `cancel(true)`."
    ],
    "code": tryit("TimeoutsAndBlocking.kt", "TimeoutsAndBlockingJava.java"),
    "expect": "The two `delay` cases end at about 300 ms: one throws, one returns null. The `withContext(IO)` case throws too, but only after about 1,500 ms, when the sleep is over. `runInterruptible` returns null at about 300 ms. After your change, the bare sleep returns `approved` after 1,500 ms: the block never suspended, so the timeout was ignored. In the Java twin, `orTimeout` gives the caller its exception on time while the abandoned call finishes at 1,500 ms anyway; `cancel(true)` interrupts it at about 300 ms."
   },
   "refs": [
    {"title": "withTimeout (API reference: the pitfalls section)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html", "kind": "docs"},
    {"title": "runInterruptible (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Cancelling a coroutine is like a manager putting a \"stop, we're closing\" note on each worker's desk. A worker who looks up between tasks (a suspension point) sees it, tidies up and goes home. A worker deep in a long calculation who never looks up keeps going until the calculation is done. A worker on hold with a supplier (a blocking call) can't see the desk at all until someone taps them on the shoulder, which is what `runInterruptible` does. `runCatching` is the worker who reads the note, throws it in the bin and starts the next task. `NonCancellable` is the exemption for tidying up: \"finish putting the cash in the safe, then go.\" The analogy breaks in one place: binning the note doesn't make it go away. Every desk the worker sits at afterwards has the same note on it.",
 "in_your_world": "Cancellation reaches your payment code more often than you think. A Kafka rebalance revokes a partition, and its worker's scope is cancelled. A Quarkus shutdown cancels long-lived scopes in `@PreDestroy`. Every `withTimeout` on an issuer call is a cancel waiting to happen. Three things keep that safe. Never wrap a suspend call in `runCatching` or `catch (e: Exception)` without rethrowing `CancellationException`, or a shutdown turns into a list of fake failures. Release card holds, distributed locks and idempotency claims in `finally` with `withContext(NonCancellable)`. And remember that an Oracle query running in `withContext(Dispatchers.IO)` ignores the timeout around it: use `runInterruptible` only if the driver responds to interrupts, and set `Statement.setQueryTimeout` either way. Temporal works on the same idea: an activity learns that it has been cancelled only when it heartbeats.",
 "mistake": "The most common mistake is swallowing `CancellationException` with a catch-all: `runCatching { }`, `catch (e: Exception)` or `catch (e: Throwable)` around a suspend call, usually written to \"log and keep going\" in a batch or polling loop. It looks like good defensive code, and it works perfectly until the first shutdown or timeout. Then the loop either reports every remaining item as failed or spins at full CPU, and a cancelled job seems to hang or to finish with nonsense. The fix: rethrow `CancellationException` before handling anything else (`if (e is CancellationException) throw e`), or catch only the exception types you expect from the call.",
 "compare": {
  "title": "Stopping a CPU loop: Future.cancel(true) vs Job.cancel()",
  "java": {"title": "ReconciliationJob.java", "src": "Future<Integer> f = pool.submit(() -> {\n    int matched = 0;\n    for (int i = 0; i < entries.size(); i++) {\n        if (i % 1_000 == 0 && Thread.currentThread().isInterrupted()) {\n            throw new CancellationException(\"reconciliation stopped at \" + i);   // 1. look at the flag\n        }\n        if (matches(entries.get(i))) matched++;\n    }\n    return matched;\n});\n\nf.cancel(true);   // 2. sets the worker's interrupt flag; the loop stops at its next check"},
  "kotlin": {"title": "ReconciliationJob.kt", "src": "val job = scope.async(Dispatchers.Default) {\n    var matched = 0\n    for ((i, entry) in entries.withIndex()) {\n        if (i % 1_000 == 0) ensureActive()   // 1. throws CancellationException once cancelled\n        if (matches(entry)) matched++\n    }\n    matched\n}\n\njob.cancel()   // 2. marks the job cancelled; the loop stops at its next check"},
  "note": "Both models are cooperative, and both loops need the same explicit check. The differences are in what carries the request. Java's interrupt is a flag on a thread. Catching `InterruptedException` clears it, so a swallowed interrupt is lost, and the request doesn't reach other threads the task started. A coroutine's cancellation is a state on its job. It stays set, it flows down to every child in the tree, and every suspension point checks it. The two also see different things: blocking JDK calls react to interrupts but not to job cancellation (bridge them with `runInterruptible`), while suspension points react to job cancellation and ignore the interrupt flag."
 },
 "worked": {
  "title": "Make a chargeback poller stop cleanly",
  "steps": [
   {"say": "A poller checks a chargeback's status every 5 s until the card scheme decides. It holds a lease (a row lock in Oracle) so only one pod polls each case. During a deploy, pods take 30 s to shut down, and leases stay locked until they expire. Find the three problems before reading on.",
    "code": "suspend fun pollChargeback(id: String): Status {\n    val lease = leases.acquire(id)\n    try {\n        while (true) {\n            try {\n                val s = scheme.status(id)\n                if (s.isFinal) return s\n                delay(5.seconds)\n            } catch (e: Exception) {\n                log.warn(\"poll failed for $id\", e)\n            }\n        }\n    } finally {\n        leases.release(lease)   // suspend: a network call to Oracle\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same bugs\nStatus pollChargeback(String id) {\n    Lease lease = leases.acquire(id);\n    try {\n        while (true) {\n            try {\n                Status s = scheme.status(id);\n                if (s.isFinal()) return s;\n                Thread.sleep(5_000);\n            } catch (Exception e) {              // also catches InterruptedException\n                log.warn(\"poll failed for {}\", id, e);\n            }\n        }\n    } finally {\n        leases.release(lease);                  // fails at once if the flag is set\n    }\n}", "alt_lang": "java"},
   {"say": "Problem 1: `catch (e: Exception)` swallows the `CancellationException` from `delay`, so a cancelled poller spins. Catch only the scheme client's error, and let cancellation through.",
    "code": "        while (true) {\n            try {\n                val s = scheme.status(id)\n                if (s.isFinal) return s\n            } catch (e: SchemeException) {     // 1. only what we expect from the call\n                log.warn(\"poll failed for $id\", e)\n            }\n            delay(5.seconds)                   //    outside the try: a cancel ends the loop\n        }", "lang": "kotlin",
    "alt_code": "        while (true) {\n            try {\n                Status s = scheme.status(id);\n                if (s.isFinal()) return s;\n            } catch (SchemeException e) {        // 1. only what we expect from the call\n                log.warn(\"poll failed for {}\", id, e);\n            }\n            Thread.sleep(5_000);                 //    InterruptedException now propagates\n        }", "alt_lang": "java"},
   {"say": "Problem 2: the lease release suspends in a cancelled coroutine, so it throws before it reaches Oracle. Wrap it in `NonCancellable`, with its own short timeout so a stuck database can't hold up shutdown.",
    "code": "    } finally {\n        // 2. cleanup that suspends must run non-cancellable, and bounded\n        withContext(NonCancellable) {\n            withTimeoutOrNull(2.seconds) { leases.release(lease) }\n        }\n    }", "lang": "kotlin",
    "alt_code": "    } finally {\n        // 2. clear the flag for the cleanup, then restore it\n        boolean interrupted = Thread.interrupted();\n        try { leases.release(lease); }\n        finally { if (interrupted) Thread.currentThread().interrupt(); }\n    }", "alt_lang": "java"},
   {"say": "Problem 3: nothing bounds the whole poll. Give the caller a deadline, and treat running out as an expected outcome rather than an exception.",
    "code": "// 3. the caller decides how long a poll may take\nval status: Status? = withTimeoutOrNull(10.minutes) { pollChargeback(id) }\nif (status == null) scheduleRetry(id)   // still undecided: try again from the outbox later", "lang": "kotlin",
    "alt_code": "// 3. the caller decides how long a poll may take\nFuture<Status> f = pool.submit(() -> pollChargeback(id));\ntry { handle(f.get(10, TimeUnit.MINUTES)); }\ncatch (TimeoutException e) { f.cancel(true); scheduleRetry(id); }", "alt_lang": "java"},
   {"say": "Self-check: the timeout in step 3 cancels `pollChargeback` while it is suspended in `delay`. Trace what happens. (The `delay` throws `TimeoutCancellationException`, it passes the narrow `catch`, the `finally` releases the lease under `NonCancellable`, and `withTimeoutOrNull` turns the exception into `null`.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix four cancellation bugs in a payments batch",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/FraudScan.kt", f"{lab}/main/{P}/SettlementRun.kt", f"{lab}/main/{P}/CardHold.kt", f"{lab}/main/{P}/BinLookup.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l05.*'",
  "steps": [
   "Run the tests. Four of eight fail, one per file. Each stub is the buggy code, and its KDoc says what is wrong.",
   "`FraudScan.kt`: make `countFlagged` check for cancellation at least once every 1,000 amounts.",
   "`SettlementRun.kt`: keep `runCatching`, but make a `CancellationException` end the run instead of being logged as a failed batch.",
   "`CardHold.kt`: make the release in `finally` run to the end even when the caller was cancelled.",
   "`BinLookup.kt`: return `null` on timeout instead of throwing, and make the timeout interrupt the blocked `lookup` call.",
   "Run the tests until all eight pass, then run them once more."
  ],
  "hints": [
   "`countFlagged` is a plain suspend function with no scope receiver, so call `currentCoroutineContext().ensureActive()`. Read the context once, before the loop.",
   "Import `CancellationException` from `kotlin.coroutines.cancellation` (or `kotlinx.coroutines`). Both name the same class.",
   "The release fix is one wrapper: `withContext(NonCancellable) { ... }`.",
   "`runInterruptible(Dispatchers.IO) { ... }` replaces `withContext(Dispatchers.IO) { ... }` for blocking code that should be interrupted on cancel."
  ],
  "done_when": "All eight tests in `CancellationTest` pass, twice in a row."
 },
 "drill": {
  "title": "A cancellable batch from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `suspend fun reprice(rows: List<Row>, lease: Lease)` that runs on `Dispatchers.Default`, checks for cancellation every 500 rows, calls `price(row)` (which can throw `PricingException`; log and skip the row), and always releases the lease with the suspending `lease.release()`, even after a cancel.",
  "answer": {"lang": "kotlin", "src": "suspend fun reprice(rows: List<Row>, lease: Lease) {\n    try {\n        withContext(Dispatchers.Default) {\n            for ((i, row) in rows.withIndex()) {\n                if (i % 500 == 0) ensureActive()            // cooperate with cancel\n                try {\n                    price(row)\n                } catch (e: PricingException) {             // only what we expect\n                    log.warn(\"skipping ${row.id}\", e)\n                }\n            }\n        }\n    } finally {\n        withContext(NonCancellable) { lease.release() }    // suspending cleanup\n    }\n}",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: read the interrupt flag, clear it around the cleanup\nvoid reprice(List<Row> rows, Lease lease) {\n    try {\n        for (int i = 0; i < rows.size(); i++) {\n            if (i % 500 == 0 && Thread.currentThread().isInterrupted()) return;   // cooperate with cancel\n            try {\n                price(rows.get(i));\n            } catch (PricingException e) {                                    // only what we expect\n                log.warn(\"skipping {}\", rows.get(i).id(), e);\n            }\n        }\n    } finally {\n        boolean interrupted = Thread.interrupted();\n        try { lease.release(); }                                              // blocking cleanup\n        finally { if (interrupted) Thread.currentThread().interrupt(); }\n    }\n}"}}
 },
 "recap": [
  "Cancellation is cooperative. `cancel()` marks the job, and the coroutine stops at its next suspension point or explicit check. CPU loops need `ensureActive()`, `isActive` or `yield()`.",
  "Cancellation travels as `CancellationException`. `runCatching`, `catch (e: Exception)` and `catch (e: Throwable)` all catch it, so rethrow it or catch narrower types.",
  "In a cancelled coroutine every suspension point throws at once. Run suspending cleanup in `finally` inside `withContext(NonCancellable)`, and never pass `NonCancellable` to `launch` or `async`.",
  "`withTimeout` throws `TimeoutCancellationException` (a `CancellationException`), and `withTimeoutOrNull` returns `null`. Inside `launch`, a timeout doesn't fail the parent unless you turn it into an error.",
  "Timeouts can't stop blocking calls. Wrap interruptible blocking code in `runInterruptible(Dispatchers.IO)`, and give clients such as JDBC their own timeouts.",
  "`flow { }` checks for cancellation on each `emit`; `asFlow()` doesn't, so add `.cancellable()`."
 ],
 "quiz": [
  {"q": "`val job = scope.launch(Dispatchers.Default) { while (true) { digest.update(nextBlock()) } }`, where `nextBlock()` is a plain function. You call `job.cancelAndJoin()`. What happens?",
   "options": ["It returns at once, because `cancel` stops the coroutine", "It returns after the current loop iteration", "It never returns: the loop has no suspension point and never checks", "The caller gets a `CancellationException` thrown from `cancelAndJoin`"],
   "answer": 2,
   "why": "Nothing in the loop looks at the job, so the cancel request is never noticed, and `cancelAndJoin` waits forever. Add `ensureActive()` or `yield()` to the loop, or loop on `while (isActive)`."},
  {"q": "A coroutine was cancelled while it waited in `delay`. Its `finally` block must call the suspending `lease.release()`. Which line does that correctly?",
   "options": ["`try { lease.release() } catch (e: CancellationException) { }`", "`withContext(NonCancellable) { lease.release() }`", "`launch(NonCancellable) { lease.release() }`", "`GlobalScope.launch { lease.release() }`"],
   "answer": 1,
   "why": "Inside `withContext(NonCancellable)` suspension points don't throw, so the release runs to the end, and the cancel carries on afterwards. Catching the exception just loses the release. `launch(NonCancellable)` and `GlobalScope` both start a coroutine outside the tree that nothing waits for, so shutdown can finish before the release does."},
  {"q": "What does this print?\n\n```kotlin\ncoroutineScope {\n    launch { withTimeout(100) { delay(1_000) } }\n}\nprintln(\"done\")\n```",
   "options": ["`done`, after about 100 ms", "Nothing: `coroutineScope` throws `TimeoutCancellationException`", "`done`, after about 1,000 ms", "Nothing: the program hangs"],
   "answer": 0,
   "why": "`TimeoutCancellationException` is a `CancellationException`, so the child counts as cancelled, not failed, and the scope completes normally. If a timeout must fail the caller, write `withTimeoutOrNull(100) { ... } ?: error(\"timed out\")`."},
  {"q": "`withTimeout(500) { withContext(Dispatchers.IO) { Thread.sleep(3_000) } }`. How long does the caller wait, and what does it get?",
   "options": ["About 500 ms, then `TimeoutCancellationException`", "About 500 ms, then `null`", "About 3 s, then `TimeoutCancellationException`", "About 3 s, then the block's result"],
   "answer": 2,
   "why": "The timer fires at 500 ms and cancels the coroutine, but `Thread.sleep` doesn't see it. When the sleep ends, `withContext` checks, finds the job cancelled, and the timeout surfaces as the exception. `runInterruptible(Dispatchers.IO)` would interrupt the sleep at 500 ms."},
  {"q": "From the executors track: a task is blocked in `Thread.sleep(5_000)` when someone calls `future.cancel(true)` on it. What happens to the task?",
   "options": ["Nothing until the sleep ends, then it carries on", "The thread is stopped and the task's `finally` blocks are skipped", "The future completes normally with `null`", "`sleep` throws `InterruptedException` at once, and the task can clean up and stop"],
   "answer": 3,
   "why": "`cancel(true)` interrupts the worker thread, and `sleep` responds to interrupts by throwing. What the task does next is up to its code: restore the flag and stop, or swallow it and carry on. That is the Java version of `runInterruptible`.",
   "from": "exec-04"}
 ],
 "flashcards": [
  {"front": "Does `job.cancel()` stop a CPU loop with no suspend calls?", "back": "No. Cancellation is cooperative: the loop must call `ensureActive()` or `yield()`, or check `isActive`."},
  {"front": "What does a suspension point such as `delay` do in a cancelled coroutine?", "back": "It throws `CancellationException` at once, without suspending."},
  {"front": "Why is `runCatching { suspendCall() }` risky inside a coroutine?", "back": "It catches every `Throwable`, `CancellationException` included, so the coroutine carries on after it was cancelled. Rethrow `CancellationException`."},
  {"front": "How do you call a suspending cleanup function in `finally` after a cancel?", "back": "`withContext(NonCancellable) { release() }`"},
  {"front": "On timeout, what do `withTimeout` and `withTimeoutOrNull` do?", "back": "`withTimeout` throws `TimeoutCancellationException`, a subclass of `CancellationException`. `withTimeoutOrNull` returns `null`."},
  {"front": "Can `withTimeout` stop a `Thread.sleep(10_000)` inside it?", "back": "No. Blocking calls ignore cancellation. Wrap them in `runInterruptible(Dispatchers.IO) { ... }` so the thread is interrupted."},
  {"front": "`(1..1_000).asFlow().collect { ... }`: does each element check for cancellation?", "back": "No. `asFlow()` doesn't check. Add `.cancellable()`. A `flow { }` builder checks on every `emit`."}
 ],
 "terms": [
  {"term": "Cooperative cancellation", "plain": "Cancelling only asks; the code stops when it next checks or reaches a suspension point."},
  {"term": "Suspension point", "plain": "A call to a suspend function such as `delay`, `await` or `withContext`. Library ones check for cancellation."},
  {"term": "CancellationException", "plain": "The exception that carries a cancel through the coroutine's code. Catching it without rethrowing breaks cancellation."},
  {"term": "NonCancellable", "plain": "A job that is always active. `withContext(NonCancellable)` lets cleanup suspend after a cancel."},
  {"term": "TimeoutCancellationException", "plain": "What `withTimeout` throws. It is a `CancellationException`, so a parent treats it as a cancel, not a failure."},
  {"term": "runInterruptible", "plain": "Runs blocking code on a dispatcher and interrupts its thread if the coroutine is cancelled."}
 ],
 "explain_back": {
  "prompt": "A teammate wrapped every call in a settlement loop in `runCatching` \"so one bad batch never stops the run\". After the last deploy, the shutdown logs listed forty failed batches that had never failed. Explain what happened and how you'd change the code.",
  "answer": "When the pod shut down, the settlement coroutine was cancelled. Cancellation reaches the code as a CancellationException thrown from the next suspension point, and runCatching catches every Throwable, so it caught that too and logged the batch in progress as failed. The coroutine was still cancelled, so the next batch threw at its first suspension point, got caught and logged the same way, and so on through all forty remaining batches. Then the function returned normally. I'd keep the per-batch error handling but rethrow CancellationException before logging anything, or catch only the exceptions the settle call is expected to throw. Then a cancel ends the run at the batch in progress, and any cleanup that suspends goes in a finally inside withContext(NonCancellable)."
 },
 "deeper": {
  "minutes": 10,
  "body": "A `CancellationException` doesn't always mean \"I was cancelled\". If you `await()` a `Deferred` that someone else cancelled, `await` throws `CancellationException` in your coroutine, even though your coroutine is fine. The kotlinx.coroutines 1.11 KDoc calls this out as a legacy behavior that can't be changed compatibly: your coroutine then ends as \"cancelled\", so its parent isn't told and the work silently stops. If you catch it, check `currentCoroutineContext().ensureActive()` in the `catch`. It throws only if *your* coroutine was cancelled, so after it you know the exception came from the thing you awaited, and you can turn it into a real error.\n\nThe library also gives a **prompt cancellation guarantee**. If a coroutine is cancelled while suspended, it resumes with `CancellationException` even when the value it was waiting for had already arrived. `withContext` checks for cancellation both on entry and when its block returns. So `val conn = withContext(io) { pool.borrow() }` can lose a connection: the block borrowed it, the caller was cancelled in the meantime, and the result is thrown away. Borrow and release inside the same block, or use the `onCancellation` callback of `CancellableContinuation.resume` when you write the bridge yourself (lesson 1 of this track).\n\nTimeouts have one more subtle rule. The KDoc says cancellation on timeout \"may happen at any time, even after the block finishes executing but before the caller gets resumed\". So never write `withTimeout { resource = open() }` and expect `resource` to be either unset or yours. Open the resource outside the timeout, or close it in the block's own `finally`.\n\nFinally, `runBlocking` bridges in the other direction. If the thread blocked in `runBlocking` is interrupted, the coroutine is cancelled and `runBlocking` throws `InterruptedException`. That is how a coroutine-based Kafka handler called from a plain consumer thread can still be stopped by `shutdownNow()`."
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
