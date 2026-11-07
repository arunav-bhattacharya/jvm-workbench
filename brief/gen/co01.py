import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l01"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
J = "java/workbench/coroutines/l01"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l01.{cls}{extra}"

FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="State machine for chargeCard: three states joined by resume arrows. '
    'A suspending call returns COROUTINE_SUSPENDED and frees the thread. A continuation object keeps the label and the locals.">'
    '<text class="t-s t-m" x="227" y="34" text-anchor="middle">resume</text>'
    '<text class="t-s t-m" x="452" y="34" text-anchor="middle">resume</text>'
    '<rect class="box-a" x="20" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="115" y="70" text-anchor="middle">label 0</text>'
    '<text class="t-s t-code" x="115" y="92" text-anchor="middle">tokenize(pan)</text>'
    '<rect class="box-a" x="245" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="340" y="70" text-anchor="middle">label 1</text>'
    '<text class="t-s t-code" x="340" y="92" text-anchor="middle">authorize(token)</text>'
    '<rect class="box-ok" x="470" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="565" y="70" text-anchor="middle">label 2</text>'
    '<text class="t-s t-code" x="565" y="92" text-anchor="middle">return result</text>'
    '<line class="ln-a" x1="210" y1="76" x2="243" y2="76" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="435" y1="76" x2="468" y2="76" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="115" y1="108" x2="115" y2="156" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="340" y1="108" x2="340" y2="156" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="20" y="158" width="415" height="50" rx="8"/>'
    '<text class="t-s t-code" x="227" y="180" text-anchor="middle">return COROUTINE_SUSPENDED</text>'
    '<text class="t-s t-m" x="227" y="198" text-anchor="middle">the thread goes back to run other coroutines</text>'
    '<text class="t-s t-m" x="560" y="176" text-anchor="middle">later: resumeWith(value)</text>'
    '<text class="t-s t-m" x="560" y="194" text-anchor="middle">jumps to the saved label</text>'
    '<rect class="box" x="20" y="230" width="640" height="52" rx="8"/>'
    '<text class="t-s t-m" x="340" y="250" text-anchor="middle">one object per call, on the heap</text>'
    '<text class="t-s t-code" x="340" y="270" text-anchor="middle">StateMachineKt$chargeCard$1 { label, L$0, L$1, result }</text>'
    '</svg>'
)

L = {
 "id": "co-01",
 "title": "Suspend functions from zero",
 "minutes": 35,
 "goal": "By the end you can say what `suspend` really does (and what it does not), read the state machine the compiler builds from a suspend function, and wrap a callback API in a cancellable suspend function.",
 "warmup": {
  "q": "What does adding `suspend` to a function do?",
  "options": [
   "It runs the function on a background thread",
   "It lets the function pause at suspending calls and continue later, without holding a thread while it waits",
   "It makes the function return a `CompletableFuture`",
   "It runs the function in parallel with its caller"
  ],
  "answer": 1,
  "why": "`suspend` only gives a function the ability to pause. It does not pick a thread, start anything in parallel or return a future. The thread is chosen by the coroutine's dispatcher, and a suspend function that never reaches a suspending call runs start to finish on its caller's thread."
 },
 "sections": [
  {
   "h": "A suspend function can pause without blocking its thread",
   "body": "Most payment code has the same shape: call the card issuer and wait 120 ms, call the ledger and wait 30 ms, return. Nearly all of the time is waiting. With one thread per request, each thread spends that time parked and still holds its stack. The Kotlin docs put the cost plainly: a thread usually needs a few megabytes of memory, and a JVM typically handles a few thousand of them at once.\n\nA **suspend function** is a function that can pause in the middle and continue later, without holding a thread while it is paused.\n\n```kotlin\nsuspend fun charge(req: ChargeRequest): Authorization {\n    val token = vault.tokenize(req.pan)          // may pause here\n    return issuer.authorize(token, req.amount)   // and here\n}\n```\n\n```java\n// Java equivalent: plain blocking calls on a virtual thread (JDK 21+); the JVM does the pausing\nAuthorization charge(ChargeRequest req) {\n    String token = vault.tokenize(req.pan());          // the virtual thread unmounts while it waits\n    return issuer.authorize(token, req.amount());      // and here\n}\n```\n\nWhen `charge` pauses inside `tokenize`, the thread leaves and runs other work. When the vault answers, `charge` continues on the next line, possibly on a different thread. The code still reads top to bottom, with normal `try`/`catch` and normal return values.\n\nA **coroutine** is one running instance of such code: a piece of work that can be paused and resumed. You start one with a builder like `runBlocking` or `launch` (lesson 2 of this track). Two rules follow.\n\nYou can call a suspend function only from another suspend function or from inside a coroutine. Plain code has nothing to resume, so the compiler refuses.\n\nWaiting must be done with a suspending call. `delay(200)` suspends: the coroutine is set aside and the thread is free. `Thread.sleep(200)` blocks: the thread stops, and every other coroutine that needs that thread waits too. The compiler accepts both, so nothing warns you.\n\nThe Try it runs five coroutines on a single thread, `main`. Each waits 200 ms. With `delay`, the five waits overlap. With `Thread.sleep`, the one thread can only sleep for one of them at a time.",
   "try": {
    "title": "Five waits on one thread",
    "minutes": 4,
    "steps": [
     "Read `SleepVsDelay.kt`. All five coroutines run on `main`. Predict the total time with `delay`.",
     "Run it with the command below.",
     "Run it again with `-Pargs=sleep` added. Predict first, then watch how the five lines appear."
    ],
    "code": {"lang": "kotlin", "title": "SleepVsDelay.kt", "src": read(demo("SleepVsDelay.kt")),
             "run": run("SleepVsDelayKt"), "file": demo("SleepVsDelay.kt"),
             "alt": {"lang": "java", "title": "SleepVsDelayJava.java", "src": read(jdemo("SleepVsDelayJava.java")),
                     "run": run("SleepVsDelayJava"), "file": jdemo("SleepVsDelayJava.java")}},
    "expect": "With `delay` the run takes a little over 200 ms (278 ms here): the waits overlap on one thread. With `Thread.sleep` it takes over a second (1,078 ms here), and the five lines appear 200 ms apart, because each sleep holds the only thread. Same code, one word changed. The Java twin gives the same two numbers (225 ms and 1,025 ms here): a timer callback on a single-thread executor is the closest Java match for `delay`."
   }
  },
  {
   "h": "A suspend function runs on whatever thread calls it",
   "body": "The most common wrong idea about coroutines is that `suspend` sends work to a background thread. It does not. The modifier adds the ability to pause and nothing else. Which thread runs the code is decided by the coroutine's **dispatcher**, a scheduler you will meet in lesson 4 of this track.\n\n```kotlin\nsuspend fun checksum(digits: String): Int {\n    var sum = 0\n    for (c in digits) sum = (sum * 31 + c.code) % 1_000_003\n    return sum   // no suspension point anywhere\n}\n```\n\n```java\n// Java equivalent: the same plain method; in Kotlin the suspend modifier changed nothing\nint checksum(String digits) {\n    int sum = 0;\n    for (char c : digits.toCharArray()) sum = (sum * 31 + c) % 1_000_003;\n    return sum;\n}\n```\n\nThis function never suspends, so it runs start to finish on the caller's thread, exactly like a normal function. IntelliJ flags the modifier as redundant. Put a two-second CPU loop in a suspend function, call it from a request coroutine, and that request's thread is busy for two seconds. Marking it `suspend` changed nothing.\n\nThe other half of the story: after a real suspension, the coroutine may continue on a different thread. A coroutine on `Dispatchers.Default` can start on worker-1, pause in `delay`, and resume on worker-3. Two things follow for your code.\n\nA `ThreadLocal` is not safe across a suspension point. The thread that resumes you may hold someone else's value. Logging MDC is a `ThreadLocal`, so this bites in real services. Lesson 4 of this track shows context elements, the coroutine way to carry such values.\n\nMemory visibility, on the other hand, is handled for you. Values a coroutine wrote before it suspended are visible after it resumes, even on another thread. You don't need `@Volatile` on locals that live across a `delay`. The reason is the hand-off. To resume you on another thread, the dispatcher submits your coroutine to its pool as a task, and the JDK's rule for executors applies: whatever a thread wrote before it submitted a task is visible to the thread that runs it (a happens-before edge, from the memory model track). That covers one coroutine's own state. Two coroutines that share a variable still need a lock or an atomic, which lesson 10 of this track covers.",
   "try": {
    "title": "Watch coroutines change threads",
    "minutes": 3,
    "steps": [
     "Read `WhichThread.kt`. Predict which thread computes the checksum.",
     "Run it. Look at the `payment N ran on` lines.",
     "Run it twice more. Do the thread sequences repeat?"
    ],
    "code": {"lang": "kotlin", "title": "WhichThread.kt", "src": read(demo("WhichThread.kt")),
             "run": run("WhichThreadKt"), "file": demo("WhichThread.kt"),
             "alt": {"lang": "java", "title": "WhichThreadJava.java", "src": read(jdemo("WhichThreadJava.java")),
                     "run": run("WhichThreadJava"), "file": jdemo("WhichThreadJava.java")}},
    "expect": "The checksum runs on `main`, the caller's thread. Each payment coroutine shows a sequence like `worker-1 -> worker-1 -> worker-4 -> worker-3`: after each `delay` any free Default worker may pick it up. The sequences change from run to run. The Java twin shows the same thing for virtual threads: after each `Thread.sleep` a virtual thread may continue on a different carrier."
   }
  },
  {
   "h": "The compiler turns a suspend function into a state machine",
   "body": "Coroutines need no special support from the JVM. They are a compiler feature plus a library. The Kotlin compiler rewrites every suspend function in **continuation-passing style**: it adds one hidden last parameter, a `Continuation`, and changes the return type to `Any?`. Here is what `javap`, the JDK tool that prints the contents of a compiled class, shows:\n\n```text\n// you write\nsuspend fun chargeCard(pan: String): String\n\n// javap shows\npublic static final java.lang.Object chargeCard(java.lang.String, kotlin.coroutines.Continuation<? super java.lang.String>);\n```\n\nA `Continuation` is a callback that also carries the coroutine's context: `interface Continuation<in T> { val context: CoroutineContext; fun resumeWith(result: Result<T>) }`. The `Object` return is either the real result or a marker, `COROUTINE_SUSPENDED`, which means \"I paused; I will call your continuation later\".\n\nThe body becomes a state machine. Each suspension point ends a state. The compiler generates one small class per suspend function (here `StateMachineKt$chargeCard$1`) with an `int label` for the next state and fields `L$0`, `L$1` for locals that must survive a pause. Here is `chargeCard` from the demo, step by step:\n\n1. Label 0: store `pan` in the object, set `label = 1`, call `tokenize(pan, this)`. If it returns `COROUTINE_SUSPENDED`, return that marker straight up the stack. The thread is now free.\n2. When the vault answers, someone calls `resumeWith(token)`. That calls `chargeCard` again with the same object. A `tableswitch` (the bytecode for a `switch` over a small range of `int` values) on `label` jumps to state 1, which picks up the token and calls `authorize`.\n3. Label 2: take the result and return it to whoever is waiting.\n\nIf `tokenize` does not suspend (a cache hit, say), it returns the token directly and the function carries on. Nothing is scheduled and no thread changes.\n\nThis explains both the cost and the rules. A suspended coroutine is one small object holding a label and a few fields, not a thread stack, so you can have hundreds of thousands. And plain code cannot call a suspend function, because it has no continuation to pass in.",
   "figure": {"svg": FIG, "caption": "Each suspension point ends a state. Suspending returns a marker and frees the thread; resuming calls the same function again, and the saved label says where to continue."},
   "try": {
    "title": "Read the state machine with javap",
    "minutes": 5,
    "steps": [
     "Run the demo once so Gradle compiles it: `" + run("StateMachineKt") + "`.",
     "From `labs/`, run the first `javap` command. Find the `Continuation` parameter and the `Object` return type on `chargeCard`.",
     "Run the second command. It prints the generated state class. Find `label` and the `L$` fields.",
     "Run the third command and find the `tableswitch`. Predict first: how many cases will it have?"
    ],
    "code": {"lang": "bash", "title": "terminal",
             "src": "javap -p coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt.class\n\njavap -p 'coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt$chargeCard$1.class'\n\njavap -c -p coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt.class | grep -A4 tableswitch",
             "run": ""},
    "expect": "`chargeCard(java.lang.String, kotlin.coroutines.Continuation<? super java.lang.String>)` returns `java.lang.Object`, and so do `tokenize` and `authorize`. The state class extends `kotlin.coroutines.jvm.internal.ContinuationImpl` and has `int label`, `L$0`, `L$1` and `result`. The first `tableswitch` says `0 to 2`: three states for two suspension points."
   },
   "refs": [
    {"title": "KEEP: Kotlin coroutines design (continuations and state machines)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md", "kind": "read"}
   ]
  },
  {
   "h": "Wrapping a callback API with suspendCancellableCoroutine",
   "body": "Most vendor SDKs in payments take a callback or return a future. `suspendCancellableCoroutine` turns a callback into a suspend function. It suspends the coroutine and hands you its continuation, and you resume it when the callback fires.\n\n```kotlin\nsuspend fun FraudSdk.scoreAwait(paymentId: String): Int =\n    suspendCancellableCoroutine { cont ->\n        val cancel = score(paymentId) { s -> cont.resume(s) }   // 1. start; resume on callback\n        cont.invokeOnCancellation { cancel() }                   // 2. we were cancelled: tell the SDK\n    }\n```\n\n```java\n// Java equivalent: complete a CompletableFuture from the callback, and pass cancellation back\nCompletableFuture<Integer> scoreAsync(Sdk sdk, String paymentId) {\n    CompletableFuture<Integer> result = new CompletableFuture<>();\n    Runnable cancel = sdk.score(paymentId, result::complete);          // 1. start; complete on callback\n    result.whenComplete((v, e) -> { if (e != null) cancel.run(); });   // 2. timed out or cancelled: tell the SDK\n    return result;\n}\n```\n\nThree rules make a wrapper like this correct.\n\nResume exactly once. Call `resume` with a value or `resumeWithException` with an error. A second resume on the same continuation throws `IllegalStateException`.\n\nUse the cancellable version. The standard library also has `suspendCoroutine`, and it works fine until someone cancels the caller. Then it can't react. The coroutine stays suspended until the SDK calls back, so a timeout fires late, and the SDK never hears that you gave up. In the Try it, a 100 ms timeout returns after a full second.\n\nExpect late replies. If the coroutine is cancelled first, a callback that arrives afterwards is ignored. kotlinx.coroutines calls this the **prompt cancellation guarantee**: a cancelled coroutine does not resume successfully, even if the value was already on its way. If that late value is a resource, such as a pooled session, pass a cleanup lambda: `cont.resume(session) { _, late, _ -> late.close() }`. The library calls it when the value can no longer be delivered.\n\nThis tool is for callbacks that fire once. For listeners that fire many times you want `callbackFlow` (lesson 9 of this track). For a `CompletableFuture` you don't write any of this: `future.await()` in kotlinx-coroutines-core already does it (lesson 11 of this track).",
   "try": {
    "title": "Make a timeout reach the SDK",
    "minutes": 5,
    "steps": [
     "Read `CallbackBridge.kt`. The SDK answers after one second. The caller allows 100 ms. Predict how long `withTimeout(100)` takes to return.",
     "Run it.",
     "Change `scoreAwait` to use `suspendCancellableCoroutine` (import `kotlinx.coroutines.suspendCancellableCoroutine`). Keep the function the SDK returns: `val cancel = score(paymentId) { s -> cont.resume(s) }`, then add `cont.invokeOnCancellation { cancel() }`.",
     "Run it again.",
     "In the Java twin, run it, then add `result.whenComplete((v, e) -> { if (e != null) cancel.run(); });` before `return result;` and run it again."
    ],
    "code": {"lang": "kotlin", "title": "CallbackBridge.kt", "src": read(demo("CallbackBridge.kt")),
             "run": run("CallbackBridgeKt"), "file": demo("CallbackBridge.kt"),
             "alt": {"lang": "java", "title": "CallbackBridgeJava.java", "src": read(jdemo("CallbackBridgeJava.java")),
                     "run": run("CallbackBridgeJava"), "file": jdemo("CallbackBridgeJava.java")}},
    "expect": "First run: `timed out` after about 1,000 ms (1,014 ms here). The timeout did fire at 100 ms, but `suspendCoroutine` could not wake up until the SDK answered, and the SDK was never told. After the change: `sdk: request for pay_981 cancelled`, then `timed out` after about 100 ms (116 ms here). The Java twin returns at about 100 ms even before your change, because `orTimeout` completes the future by itself, but the SDK only hears about it once you add the `whenComplete` hook."
   },
   "refs": [
    {"title": "suspendCancellableCoroutine (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A continuation is a bookmark with a sticky note. When a cook (a thread) reaches a step that needs the oven for 40 minutes, they don't stand at the oven. They put a bookmark in the recipe, write on the note which step comes next and which ingredients are already measured, and go cook something else. When the oven timer rings, any free cook can pick up the book, read the note, and carry on from that step. The recipe is the state machine, the step number is `label`, and the measured ingredients are the `L$` fields. The analogy breaks in one place: in a kitchen the free cook picks up the book on their own. In a coroutine, the dispatcher decides who picks it up, and the callback that rings the timer is the only thing that can wake it.",
 "in_your_world": "Your services talk to an issuer SDK, an HSM client, a fraud-scoring vendor and a tokenization vault. Several of them hand you a callback or a future. Wrap each one once, with `suspendCancellableCoroutine` or `future.await()`, and the rest of the code base gets plain sequential functions with normal `try`/`catch`. More important for payments: when the caller's timeout fires, the cancel reaches the vendor call, so you are not left with a charge in flight that nobody is waiting for. The same rule applies in a Kafka consumer or a Temporal activity written in Kotlin: a retry backoff written with `Thread.sleep` holds the thread and stalls every other coroutine scheduled on it. Use `delay`.",
 "mistake": "The common mistake is thinking `suspend` makes code non-blocking. People mark a function `suspend`, call JDBC or `Thread.sleep` inside it, and expect the thread to be free while it waits. It isn't. `suspend` only lets a function pause at suspending calls such as `delay`, `await` or a `suspendCancellableCoroutine` wrapper. A blocking call inside a suspend function still blocks the thread. Wait with `delay`, wrap callback APIs with `suspendCancellableCoroutine`, and move unavoidable blocking calls to `Dispatchers.IO` with `withContext` (lesson 4 of this track).",
 "compare": {
  "title": "Two calls in a row: CompletableFuture vs suspend",
  "java": {"title": "ChargeService.java", "src": "CompletableFuture<String> chargeCard(String pan) {\n    return vault.tokenize(pan)                          // CompletableFuture<String>\n        .thenCompose(token -> issuer.authorize(token))  // CompletableFuture<String>\n        .orTimeout(2, TimeUnit.SECONDS);\n}"},
  "kotlin": {"title": "ChargeService.kt", "src": "suspend fun chargeCard(pan: String): String = withTimeout(2.seconds) {\n    val token = vault.tokenize(pan)   // suspend fun\n    issuer.authorize(token)           // suspend fun\n}"},
  "note": "Both versions free the thread while they wait. The Java version expresses \"then\" with callbacks: each `thenCompose` registers a lambda, errors arrive wrapped in `CompletionException`, and `orTimeout` only completes the outer future exceptionally. The vault and issuer calls keep running, because cancelling a `CompletableFuture` never interrupts the work behind it. The Kotlin version reads like blocking code: locals, `try`/`catch` and loops all work, and the compiler builds the callbacks for you. When `withTimeout` fires, it cancels the coroutine, and cancellation reaches the two calls if they are written to cooperate, as in section 4. On JDK 21+ you can also write the Java version as plain blocking calls on a virtual thread. Lesson 11 of this track has a guide for choosing between the two."
 },
 "worked": {
  "title": "Wrap a pooled-session SDK without leaking sessions",
  "steps": [
   {"say": "An HSM vendor hands out sessions from a pool. `acquire` returns at once with a `Ticket` and calls you back later with a session or an error. Sessions must be closed. You want `suspend fun HsmPool.acquireAwait(): Session`.",
    "code": "class Session(val id: Int) : AutoCloseable { override fun close() { /* back to the pool */ } }\nfun interface Ticket { fun cancel() }\ninterface HsmPool {\n    fun acquire(onReady: (Session?, Throwable?) -> Unit): Ticket\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: the same SDK shape\nfinal class Session implements AutoCloseable {\n    @Override public void close() { /* back to the pool */ }\n}\ninterface Ticket { void cancel(); }\ninterface HsmPool {\n    Ticket acquire(BiConsumer<Session, Throwable> onReady);\n}", "alt_lang": "java"},
   {"say": "Start the request inside `suspendCancellableCoroutine` and resume exactly once from the callback: a value on success, an exception on error.",
    "code": "suspend fun HsmPool.acquireAwait(): Session = suspendCancellableCoroutine { cont ->\n    // 1. start the request; the pool calls back on its own thread\n    val ticket = acquire { session, error ->\n        // 2. resume exactly once, with a value or an error\n        if (error != null) cont.resumeWithException(error)\n        else cont.resume(session!!)\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: complete a CompletableFuture from the callback\nstatic CompletableFuture<Session> acquireAsync(HsmPool pool) {\n    CompletableFuture<Session> result = new CompletableFuture<>();\n    // 1. start the request; the pool calls back on its own thread\n    Ticket ticket = pool.acquire((session, error) -> {\n        // 2. complete exactly once, with a value or an error\n        if (error != null) result.completeExceptionally(error);\n        else result.complete(session);\n    });\n    return result;\n}", "alt_lang": "java"},
   {"say": "If the caller times out, stop waiting for a session. `invokeOnCancellation` runs when the coroutine is cancelled while suspended here.",
    "code": "    // 3. our caller gave up: cancel the ticket\n    cont.invokeOnCancellation { ticket.cancel() }", "lang": "kotlin",
    "alt_code": "    // 3. our caller gave up (cancelled the future): cancel the ticket\n    result.whenComplete((s, e) -> { if (result.isCancelled()) ticket.cancel(); });", "alt_lang": "java"},
   {"say": "One gap is left. The pool may hand out a session just after you were cancelled. The continuation ignores that late resume, and the session leaks. Use the `resume` overload that takes a cleanup lambda: the library calls it with the value it could not deliver.",
    "code": "        else cont.resume(session!!) { _, late, _ -> late.close() }   // 4. late session: close it", "lang": "kotlin",
    "alt_code": "        // 4. late session: complete() returns false when the future is already done, so close it\n        else if (!result.complete(session)) session.close();", "alt_lang": "java"},
   {"say": "Self-check: why is step 4 needed even though step 3 cancels the ticket? (Cancelling is a request. The pool may already be calling you back on another thread, so the session can still arrive after you were cancelled.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Wrap the issuer SDK, then fix a blocking backoff",
  "minutes": 12,
  "files": [
   f"{lab}/main/{P}/IssuerSdk.kt",
   f"{lab}/main/{P}/SuspendingIssuer.kt",
   f"{lab}/main/{P}/Backoff.kt"
  ],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l01.*'",
  "steps": [
   "Run the tests once. All five fail: four hit the `TODO` in `authorizeAwait`, and the backoff test shows the coroutines running one after another.",
   "Read `IssuerSdk.kt`. It is the vendor's callback API; do not change it.",
   "Write `authorizeAwait` in `SuspendingIssuer.kt` with `suspendCancellableCoroutine`. Start the request with an `AuthCallback` object whose two methods resume the continuation.",
   "Register `invokeOnCancellation` so that a cancelled caller calls `cancel()` on the `InFlight` handle.",
   "Fix `pauseBeforeRetry` in `Backoff.kt` so it waits without blocking the thread.",
   "Run the tests until all five pass."
  ],
  "hints": [
   "You need three imports: `kotlinx.coroutines.suspendCancellableCoroutine`, `kotlin.coroutines.resume` and `kotlin.coroutines.resumeWithException`.",
   "An anonymous object implements the callback: `object : AuthCallback { override fun onApproved(auth: Authorization) = cont.resume(auth); ... }`.",
   "If the cancellation test hangs for 10 seconds, you used `suspendCoroutine`. It cannot react to cancellation, so `cancelAndJoin` waits forever.",
   "The backoff test runs under `runTest`, which skips `delay` on virtual time. That is why it expects `currentTime` to be exactly 200."
  ],
  "done_when": "All five tests in `SuspendFunctionsTest` pass."
 },
 "drill": {
  "title": "Wrap a callback from memory",
  "minutes": 4,
  "prompt": "Close this page. A BIN lookup SDK has `fun lookup(bin: String, cb: (BinInfo?, Throwable?) -> Unit): Call`, and `Call` has a `cancel()` method. Write `suspend fun BinSdk.lookupAwait(bin: String): BinInfo` so that errors are thrown and a cancelled caller cancels the call. Then compare.",
  "answer": {"lang": "kotlin", "src": "suspend fun BinSdk.lookupAwait(bin: String): BinInfo =\n    suspendCancellableCoroutine { cont ->\n        val call = lookup(bin) { info, error ->\n            if (error != null) cont.resumeWithException(error)\n            else cont.resume(info!!)\n        }\n        cont.invokeOnCancellation { call.cancel() }\n    }",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a CompletableFuture that cancels the call when it is cancelled\nstatic CompletableFuture<BinInfo> lookupAsync(BinSdk sdk, String bin) {\n    CompletableFuture<BinInfo> result = new CompletableFuture<>();\n    Call call = sdk.lookup(bin, (info, error) -> {\n        if (error != null) result.completeExceptionally(error);\n        else result.complete(info);\n    });\n    result.whenComplete((v, e) -> { if (result.isCancelled()) call.cancel(); });\n    return result;\n}"}}
 },
 "recap": [
  "`suspend` lets a function pause at suspending calls without holding a thread. It does not choose a thread or run anything in the background.",
  "`delay` suspends and frees the thread; `Thread.sleep` blocks it, and every coroutine that needs that thread waits.",
  "The compiler adds a `Continuation` parameter, returns `Any?` (`COROUTINE_SUSPENDED` or the result), and turns the body into a state machine with a `label` and fields for live locals.",
  "A coroutine may resume on a different thread after a suspension, so `ThreadLocal` values don't follow it, but your own writes stay visible.",
  "Wrap single-shot callbacks with `suspendCancellableCoroutine`: resume exactly once, cancel the underlying call in `invokeOnCancellation`, and expect late replies."
 ],
 "quiz": [
  {"q": "This runs on one thread: `runBlocking { repeat(3) { launch { Thread.sleep(100) } } }`. About how long does it take?",
   "options": ["About 100 ms, because the three coroutines run concurrently", "About 300 ms, because each sleep blocks the only thread", "About 0 ms, because launch returns at once", "It does not compile: Thread.sleep is not allowed in a coroutine"],
   "answer": 1,
   "why": "`Thread.sleep` blocks the thread, and `runBlocking` gives all three coroutines one thread, so they sleep one after another. With `delay(100)` they would overlap and finish in about 100 ms. The compiler happily accepts `Thread.sleep` here, which is why the bug survives code review."},
  {"q": "`suspend fun parseStatement(json: String): Statement` is pure CPU work with no suspending calls. A request coroutine on thread `worker-2` calls it. Which thread runs the parsing?",
   "options": ["`worker-2`, the caller's thread", "A thread from `Dispatchers.IO`", "A new background thread for each call", "The thread is chosen at random by the JVM"],
   "answer": 0,
   "why": "A suspend function that never suspends is ordinary code on the caller's thread. `suspend` does not move work anywhere. To run CPU work elsewhere you'd switch dispatcher explicitly with `withContext(Dispatchers.Default)`, which lesson 4 of this track covers."},
  {"q": "How does `suspend fun balance(accountId: String): Long` look to a Java caller?",
   "options": ["`long balance(String accountId)`", "`CompletableFuture<Long> balance(String accountId)`", "`Object balance(String accountId, Continuation<? super Long> continuation)`", "`void balance(String accountId, Consumer<Long> callback)`"],
   "answer": 2,
   "why": "The compiler adds a `Continuation` as the last parameter and changes the return type to `Object`, which holds either the result (boxed) or `COROUTINE_SUSPENDED`. That is why Java code can't simply call suspend functions; lesson 11 of this track shows the bridges (`future {}`)."},
  {"q": "A callback SDK is wrapped with `suspendCoroutine` (not the cancellable version). The caller runs `withTimeout(200) { sdk.callAwait() }` and the SDK answers after 3 seconds. What happens?",
   "options": ["`TimeoutCancellationException` at 200 ms, and the SDK call is cancelled", "The call returns the SDK's value after 3 seconds; the timeout is ignored", "`IllegalStateException`, because the continuation was resumed twice", "The coroutine stays suspended until the SDK answers at 3 s, then throws `TimeoutCancellationException`; the SDK is never told"],
   "answer": 3,
   "why": "The timeout cancels the coroutine at 200 ms, but a non-cancellable continuation cannot wake up until it is resumed. When the SDK answers at 3 s, the coroutine finds itself cancelled and throws. `suspendCancellableCoroutine` would resume at 200 ms and run `invokeOnCancellation`, where you cancel the SDK call."},
  {"q": "From the virtual threads track: a virtual thread calls `Thread.sleep(200)`. What happens to its carrier thread?",
   "options": ["The carrier is blocked for the full 200 ms", "The virtual thread unmounts, and the carrier is free to run other virtual threads", "The JVM creates a new carrier to replace it", "`sleep` throws, because virtual threads cannot sleep"],
   "answer": 1,
   "why": "When a virtual thread blocks in `sleep`, the JVM saves its stack and unmounts it, so the carrier runs other virtual threads. It is the same idea as a coroutine suspending, done by the JVM for any blocking call instead of by the Kotlin compiler for `suspend` calls.",
   "from": "vt-02"}
 ],
 "flashcards": [
  {"front": "Does `suspend` run a function on a background thread?", "back": "No. It only lets the function pause without blocking. The dispatcher decides the thread, and a suspend function that never suspends runs on its caller's thread."},
  {"front": "Inside a coroutine, what is the difference between `delay(200)` and `Thread.sleep(200)`?", "back": "`delay` suspends the coroutine and frees the thread for others. `Thread.sleep` blocks the thread, so every coroutine waiting for that thread waits too."},
  {"front": "What does the compiler add to a suspend function's signature?", "back": "A `Continuation<T>` as the last parameter. The return type becomes `Any?` (`Object` in Java)."},
  {"front": "What does a compiled suspend function return when it pauses?", "back": "The marker `COROUTINE_SUSPENDED`. The real result arrives later through `continuation.resumeWith(...)`."},
  {"front": "Where does a suspended coroutine keep its local variables?", "back": "In fields (`L$0`, `L$1`, ...) of a small state-machine object on the heap, next to an `int label` that says which state runs next."},
  {"front": "Why wrap a callback with `suspendCancellableCoroutine` and not `suspendCoroutine`?", "back": "Only the cancellable one reacts to cancellation: it resumes the caller at once with `CancellationException` and runs `invokeOnCancellation`, where you cancel the underlying call."},
  {"front": "A callback fires after its coroutine was cancelled. What happens to `cont.resume(value)`?", "back": "It is ignored (prompt cancellation guarantee). If the value is a resource, pass a cleanup lambda: `cont.resume(value) { _, v, _ -> v.close() }`."}
 ],
 "terms": [
  {"term": "Coroutine", "plain": "One running piece of work that can pause and resume later, without holding a thread while paused."},
  {"term": "Suspend function", "plain": "A function marked `suspend`. It may pause at suspending calls and can only be called from a coroutine or another suspend function."},
  {"term": "Suspension point", "plain": "A call to a suspend function, where the caller may pause. It does not always pause, for example on a cache hit."},
  {"term": "Continuation", "plain": "The object that knows how to resume a paused coroutine: its context plus `resumeWith(result)`."},
  {"term": "COROUTINE_SUSPENDED", "plain": "The marker a compiled suspend function returns to say it paused and will resume through the continuation."},
  {"term": "Continuation-passing style", "plain": "Compiling a function so it receives \"what to do next\" as an extra parameter, instead of returning to a waiting caller."},
  {"term": "Dispatcher", "plain": "The scheduler that decides which thread runs a coroutine, and which thread it resumes on."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"I marked our ledger lookup `suspend`, so it no longer blocks the request thread.\" The lookup uses plain JDBC inside. Explain what `suspend` actually changed, and what you'd do instead.",
  "answer": "`suspend` only gives the function the ability to pause at suspending calls, and the compiler adds a continuation parameter so it can be resumed later. It does not move the code to another thread. A JDBC call is blocking, not suspending, so the function never pauses: it holds the request thread for the whole query, exactly as before. To keep the request thread free, the blocking call has to run somewhere else, for example `withContext(Dispatchers.IO) { jdbc... }`, or the driver has to offer a suspending or async API that we wrap with `suspendCancellableCoroutine` or `await()`."
 },
 "deeper": {
  "minutes": 10,
  "body": "Kotlin coroutines and Java virtual threads both rest on continuations, but they put them in different places.\n\nKotlin's continuations are **stackless**. The compiler rewrites each suspend function into a state machine, and a suspended coroutine is a chain of those small state objects, one per suspend function still in progress. That is why `suspend` is part of the function type: every function between the coroutine and the suspending call must be compiled this way, or there is nowhere to save its state. People call this function coloring. It is also why coroutines work on any JVM version, on Android, and on Kotlin/JS and Native, where there is no Loom.\n\nVirtual threads use **stackful** continuations inside the JVM. When a virtual thread blocks, the JVM copies its stack frames to the heap and unmounts it from the carrier. Any blocking call, in any library, can pause it, with no change to the code and no coloring. The price is that the JVM decides when to pause, and code that holds a monitor or calls native code could pin the carrier on older JDKs (JDK 24 removed most pinning on `synchronized`, JEP 491).\n\nThe KEEP also explains a detail you saw in javap: the state object is created once per call and reused across every suspension point in that call, so a function that suspends three times allocates one object, not three. And a suspend function whose suspending calls are all in tail position needs no state machine at all; it passes its continuation straight through.\n\nRead the \"Implementation details\" part of the KEEP (linked in sources) if you want the pseudo-Java the compiler generates, including how the generated `invokeSuspend` method re-enters the function."
 },
 "sources": [
  {"title": "Coroutines basics (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-basics.html"},
  {"title": "KEEP: Kotlin coroutines design document (Breslav, Elizarov)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md"},
  {"title": "suspendCancellableCoroutine (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html"},
  {"title": "Intro to coroutines and channels (Kotlin hands-on tutorial)", "url": "https://kotlinlang.org/docs/coroutines-and-channels.html"}
 ]
}
out = ROOT / "content/lessons/co-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
