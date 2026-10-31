import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l03"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
J = "java/workbench/coroutines/l03"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l03.{cls}{extra}"

FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="A coroutine tree: a request coroutine, a coroutineScope under it, and three children: account, ledger and risk. '
    'Ledger throws; the scope cancels account and risk, then rethrows to the request. Cancellation goes down the tree, failure goes up.">'
    '<rect class="box" x="240" y="16" width="200" height="40" rx="8"/>'
    '<text class="t" x="340" y="41" text-anchor="middle">request</text>'
    '<line class="ln" x1="340" y1="56" x2="340" y2="94"/>'
    '<rect class="box-a" x="240" y="96" width="200" height="40" rx="8"/>'
    '<text class="t t-code" x="340" y="121" text-anchor="middle">coroutineScope</text>'
    '<line class="ln" x1="340" y1="136" x2="130" y2="184"/>'
    '<line class="ln" x1="340" y1="136" x2="340" y2="184"/>'
    '<line class="ln" x1="340" y1="136" x2="550" y2="184"/>'
    '<rect class="box-dim" x="60" y="186" width="140" height="40" rx="8"/>'
    '<text class="t" x="130" y="211" text-anchor="middle">account</text>'
    '<text class="t-s t-m" x="130" y="244" text-anchor="middle">cancelled</text>'
    '<rect class="box-bad" x="270" y="186" width="140" height="40" rx="8"/>'
    '<text class="t" x="340" y="211" text-anchor="middle">ledger</text>'
    '<text class="t-s t-bad" x="340" y="244" text-anchor="middle">throws IOException</text>'
    '<rect class="box-dim" x="480" y="186" width="140" height="40" rx="8"/>'
    '<text class="t" x="550" y="211" text-anchor="middle">risk</text>'
    '<text class="t-s t-m" x="550" y="244" text-anchor="middle">cancelled</text>'
    '<text class="t-s t-a" x="30" y="84" text-anchor="middle">cancel</text>'
    '<text class="t-s t-a" x="30" y="100" text-anchor="middle">goes</text>'
    '<text class="t-s t-a" x="30" y="116" text-anchor="middle">down</text>'
    '<line class="ln-a" x1="30" y1="126" x2="30" y2="226" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="652" y1="226" x2="652" y2="40" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="652" y="244" text-anchor="middle">failure</text>'
    '<text class="t-s t-bad" x="652" y="260" text-anchor="middle">goes up</text>'
    '<text class="t-s t-m" x="340" y="284" text-anchor="middle">the scope cancels the siblings, waits for them, then rethrows to its caller</text>'
    '</svg>'
)

L = {
 "id": "co-03",
 "title": "Structured concurrency: scopes, jobs and the tree",
 "minutes": 35,
 "goal": "By the end you can draw the job tree for a piece of coroutine code, predict what a failure or a cancel does to it, spot leaked work, and give a class that starts background work a scope it owns and closes.",
 "warmup": {
  "q": "A request coroutine calls `GlobalScope.launch { refund(id) }` and then the client disconnects, so the request coroutine is cancelled. What happens to the refund?",
  "options": [
   "It is cancelled too, because it was started from the request",
   "It keeps running: it belongs to GlobalScope, not to the request",
   "It is paused until the request is retried",
   "The JVM throws IllegalStateException when the request is cancelled"
  ],
  "answer": 1,
  "why": "Cancellation travels down a tree of parent and child jobs. `GlobalScope` has no job, so a coroutine launched there has no parent. The request being cancelled does not reach it, nobody waits for it, and nobody hears about its failure."
 },
 "sections": [
  {
   "h": "Every coroutine has a parent, and a parent waits for its children",
   "body": "Every coroutine you start with `launch` or `async` gets a `Job`, and that job becomes a **child** of the job in the scope you called it on. Children can have children. The result is a tree, and the tree is the whole idea behind **structured concurrency**: concurrent work has the same nested shape as the code that started it.\n\n```kotlin\nrunBlocking(CoroutineName(\"request\")) {          // root\n    launch(CoroutineName(\"details\")) {             // child of request\n        coroutineScope {                           // a node of its own\n            async(CoroutineName(\"account\")) { /* ... */ }\n            async(CoroutineName(\"ledger\")) { /* ... */ }\n            launch(CoroutineName(\"risk\")) { /* ... */ }\n        }\n    }\n}\n```\n\n```java\n// Java equivalent: nested StructuredTaskScope (preview in JDK 25, JEP 505; needs --enable-preview)\ntry (var details = StructuredTaskScope.open()) {      // a node, like coroutineScope\n    details.fork(() -> accounts.load(id));\n    details.fork(() -> ledger.recent(id, 20));\n    details.fork(() -> risk.flags(id));\n    details.join();                                     // waits for all three subtasks\n}\n```\n\nA **scope** is just a coroutine context that holds a job. `launch` reads the job from the scope's context and attaches the new coroutine to it. `coroutineScope` adds a node of its own between its caller and the children started inside it.\n\nThe first rule of the tree: **a parent cannot complete until all of its children have completed.** When the body of a coroutine finishes, its job enters a waiting state (\"completing\") until every child is done. That is why `coroutineScope` returns only after the slowest child, and why `runBlocking` doesn't return while anything below it is still running. Completed children leave the tree, so `job.children` lists only the work that is still going.\n\nThe kotlinx.coroutines 1.11 docs spell out four rules for how lifecycles interact. The parent waits for its children. Cancelling the parent cancels the children. A child that fails with an exception cancels its parent (unless the parent is a supervisor, lesson 6 of this track). And a child that ends with `CancellationException` counts as cancelled, so the parent is not told. The next section is about the middle two.",
   "try": {
    "title": "Print the tree",
    "minutes": 4,
    "steps": [
     "Read `JobTree.kt`. Before running it, sketch the tree you expect to see at 100 ms, with names.",
     "Run it and compare with your sketch.",
     "Why does `details` appear twice? (Hint: what does `coroutineScope` inherit from its parent?)"
    ],
    "code": {"lang": "kotlin", "title": "JobTree.kt", "src": read(demo("JobTree.kt")),
             "run": run("JobTreeKt"), "file": demo("JobTree.kt"), "solo": True},
    "expect": "`request` has one child, `details`. Under it sits a second node also called `details`: that is the `coroutineScope`, which inherits its parent's context, name included. It has three children: `account`, `ledger` and `risk`. After `join`, the request has 0 children, because finished children leave the tree."
   },
   "refs": [
    {"title": "coroutineScope (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/coroutine-scope.html", "kind": "docs"}
   ]
  },
  {
   "h": "Failure goes up, cancellation goes down",
   "body": "Take the payment details endpoint from lesson 2 of this track: account, ledger and risk calls as three children of one `coroutineScope`. The ledger call throws `IOException` at 100 ms. Here is what the tree does, in order:\n\n1. The ledger child fails. It reports the exception to its parent, the scope.\n2. The scope's job is cancelled with that exception. A cancelled job cancels all of its children, so the account and risk calls are cancelled. Their `finally` blocks run.\n3. The scope waits until those children have actually stopped.\n4. `coroutineScope` rethrows the `IOException` to its caller, which can catch it like any exception.\n\nSo a single failure takes down the whole subtree it belongs to, and then surfaces as one exception at the place that started the work. The total time is the time to the failure, about 100 ms, not the time of the slowest call. Nothing is left running in the background holding a connection.\n\nCancellation only travels **down**. If the caller cancels the request (the client hung up, or a timeout fired), every coroutine below it is cancelled. A child that is cancelled does not cancel its parent. A child whose block ends by throwing `CancellationException` is treated the same way: it is \"cancelled\", not \"failed\", and the parent carries on.\n\nThis is the default because it is almost always what a request needs. If one of three calls needed to build the response has failed, there is no response, so the other two calls are wasted work. When you do want siblings to survive each other's failures (sending a notification to email, SMS and push), you ask for it explicitly with a supervisor. That is lesson 6 of this track.\n\nOne caution from the docs: cancellation reaches a coroutine only at a suspension point. A child stuck in a CPU loop or a blocking call finishes that first. Lesson 5 of this track shows how to cooperate.",
   "figure": {"svg": FIG, "caption": "One child fails. The scope cancels its siblings, waits for them to stop, and rethrows the failure to its caller."},
   "try": {
    "title": "Watch one failure take down a scope",
    "minutes": 4,
    "steps": [
     "Read `FailureSpreads.kt`. Predict which lines print, and at roughly what times.",
     "Run it.",
     "Run it with `-Pargs=ok`, so the ledger does not fail. Predict when `coroutineScope` returns.",
     "Run the Java twin, then run it with `-Pargs=cancel`. Compare what happens to the risk task."
    ],
    "code": {"lang": "kotlin", "title": "FailureSpreads.kt", "src": read(demo("FailureSpreads.kt")),
             "run": run("FailureSpreadsKt"), "file": demo("FailureSpreads.kt"),
             "alt": {"lang": "java", "title": "FailureSpreadsJava.java", "src": read(jdemo("FailureSpreadsJava.java")),
                     "run": run("FailureSpreadsJava"), "file": jdemo("FailureSpreadsJava.java")}},
    "expect": "The scope body finishes first, at a few ms. At about 100 ms the ledger throws, and within a few ms the risk child's `finally` runs and the caller catches `ledger unavailable`. `risk: done` never prints. (The first `delay` can read 150 ms or so on a cold JVM.) With `-Pargs=ok`, `coroutineScope` returns at about 1,000 ms, after the slowest child. The Java twin is the honest contrast: an executor has no tree, so after the ledger fails the risk task runs to `risk: done` at about 1,000 ms, and `close()` waits for it. With `-Pargs=cancel` you cancel the sibling by hand and its `finally` runs at about 100 ms (the last two lines can come in either order). `coroutineScope` does that step for you."
   }
  },
  {
   "h": "GlobalScope cuts work loose from the tree",
   "body": "`GlobalScope` is a scope with no job. A coroutine launched in it has no parent, so none of the rules above apply. Nothing waits for it, nothing cancels it, and its exception goes to the thread's uncaught exception handler, which usually means a log line nobody reads.\n\n```kotlin\nsuspend fun startRefund(id: String) {\n    GlobalScope.launch { refundSteps(id) }   // returns at once; the refund is an orphan\n}\n```\n\n```java\n// Java equivalent: a task on a shared, app-wide pool; nothing ties it to the request\nvoid startRefund(String id) {\n    SHARED_POOL.submit(() -> refundSteps(id));   // returns at once; the refund is an orphan\n}\n```\n\nThe caller of `startRefund` thinks the refund is part of its request. It is not. When the client gives up and the request coroutine is cancelled, the refund keeps going. In a test, it keeps running after the test has finished and may fail the next one. At shutdown, it can still be writing when the connection pool closes. This is a **leaked coroutine**: work that outlives everything that knows about it.\n\nkotlinx.coroutines marks `GlobalScope` as `@DelicateCoroutinesApi`, so you have to opt in, and its docs call using it an antipattern. They also warn about the obvious workaround: `CoroutineScope(Dispatchers.IO).launch { }` inside a function creates a brand-new root scope on every call and has every one of the same problems. The opt-in warning just doesn't fire.\n\nThe fix depends on what you meant. If the caller should wait for the refund, call it directly, or use `coroutineScope { launch { } }` when it runs alongside other work. If the refund really should outlive the request, then something with a longer life has to own it: a component with its own scope, which the next section builds. In payments it often means something else again: write the refund to an outbox table or a Temporal workflow, so it survives a restart. An in-memory coroutine doesn't.\n\nThere is one legitimate use: a coroutine that lives exactly as long as the whole application, such as a metrics reporter started in `main`.",
   "try": {
    "title": "Cancel a request and watch the refund carry on",
    "minutes": 4,
    "steps": [
     "Read `LeakedWork.kt`. The request is cancelled at 250 ms. Predict how many refund steps print after that.",
     "Run it.",
     "Run it with `-Pargs=fixed`, which uses the `coroutineScope` version. Predict first.",
     "Run the Java twin both ways. It interrupts a request thread instead of cancelling a coroutine."
    ],
    "code": {"lang": "kotlin", "title": "LeakedWork.kt", "src": read(demo("LeakedWork.kt")),
             "run": run("LeakedWorkKt"), "file": demo("LeakedWork.kt"),
             "alt": {"lang": "java", "title": "LeakedWorkJava.java", "src": read(jdemo("LeakedWorkJava.java")),
                     "run": run("LeakedWorkJava"), "file": jdemo("LeakedWorkJava.java")}},
    "expect": "With `GlobalScope`, steps 2 to 5 keep printing after `request cancelled`: the refund never heard about it. With `-Pargs=fixed`, the refund is a child of the request, so nothing prints after `request cancelled` except `main done`. The Java twin leaks the same way: interrupting the request thread does not reach a task on a shared pool. Its `fixed` version runs the refund on the request's own thread, so the interrupt stops it."
   },
   "refs": [
    {"title": "GlobalScope (API reference: why it is delicate)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-global-scope/", "kind": "docs"}
   ]
  },
  {
   "h": "A class that starts background work owns a scope and closes it",
   "body": "Some work really does outlive a single call: a settler that works through card batches for one Kafka partition, an FX rate refresher, a cache warmer. The structured way to write it is a class that **owns** a scope, launches into it, and cancels it when its own life ends.\n\n```kotlin\nclass BatchSettler(context: CoroutineContext, private val settle: suspend (String) -> Unit) {\n    private val scope = CoroutineScope(context + Job())      // 1. the class's own root\n\n    fun submit(batchId: String): Job =\n        scope.launch { settle(batchId) }                      // 2. every batch is a child\n\n    suspend fun shutdown() =\n        scope.coroutineContext.job.cancelAndJoin()            // 3. cancel them all, wait\n}\n```\n\n```java\n// Java equivalent: the class owns an executor and shuts it down\nclass BatchSettler implements AutoCloseable {\n    private final ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();   // 1. the class's own pool\n    private final Consumer<String> settle;\n\n    BatchSettler(Consumer<String> settle) { this.settle = settle; }\n\n    Future<?> submit(String batchId) {\n        return pool.submit(() -> settle.accept(batchId));                               // 2. every batch runs in it\n    }\n\n    @Override public void close() throws InterruptedException {\n        pool.shutdownNow();                                                             // 3. interrupt them all\n        pool.awaitTermination(30, TimeUnit.SECONDS);                                   //    and wait\n    }\n}\n```\n\nThe scope's job is the parent of every batch. One call to `cancel` reaches all of them, and `job.children` tells you what is still running. The tree still exists. Its root is now the object, not a request.\n\nA few rules keep this honest.\n\nTie the scope to a real lifecycle. Cancel it in `@PreDestroy` in a Quarkus bean, in `onPartitionsRevoked` for a Kafka partition worker, or in `@AfterEach` in a test. An owned scope that nobody cancels is just `GlobalScope` with extra steps.\n\nCreate it once, as a field. A scope created inside a method is the orphan from the previous section.\n\nPass the dispatcher (or the whole context) in. Production can use `Dispatchers.IO`, and tests can pass a test dispatcher and run on virtual time. The lab does exactly this.\n\nChoose `cancel` or `cancelAndJoin` on purpose. `scope.cancel()` is not a suspend function and returns at once, while children are still running their `finally` blocks. `cancelAndJoin()` waits until they have stopped, which is what you want before closing a connection pool.\n\n`CoroutineScope(...)` adds a `Job()` for you if the context has none, but write it out so readers see it. With a plain `Job`, one failed batch cancels the whole settler. Lesson 6 of this track swaps it for a `SupervisorJob`, so batches can fail on their own."
  }
 ],
 "analogy": "A family on a day out. The parent won't leave the park until every child is back at the car. If one child gets hurt, the parent calls everyone back and the trip ends, and the parent then tells whoever is waiting at home what happened. If a child simply decides they've had enough and sits in the car, nobody panics. `GlobalScope` is a child who wandered off with no parent at all: nobody will look for them at closing time. An owned scope is a school trip: the school, not any one parent, brings everyone home at the end of the day. The analogy breaks on timing. Real children come back when they hear the call. A coroutine only hears it at its next suspension point, so a child busy in a CPU loop keeps going until it pauses.",
 "in_your_world": "Two places in a payments service need this most. First, request fan-out: a payment details or checkout endpoint that calls three services should do so inside `coroutineScope`, so a failure or a client disconnect cancels the other calls and releases their Oracle connections. Second, partition-scoped background work in a Kafka consumer. Give each assigned partition a worker with its own scope, launch the per-partition jobs into it, and call `shutdown()` (cancel and join) in `onPartitionsRevoked`, before the offsets are committed and the partition moves to another pod. If those jobs ran in `GlobalScope`, two pods could settle the same batch during a rebalance. Anything that must survive a pod restart belongs in an outbox table or a Temporal workflow, not in a coroutine.",
 "mistake": "The most common mistake is reaching for `GlobalScope.launch` (or `CoroutineScope(Dispatchers.IO).launch` inside a function) to \"run this in the background\" from a request. It compiles and seems to work, so it ships. The cost shows up later: work keeps running after the client has gone, tests interfere with each other, failures only appear as stray log lines, and shutdown races with in-flight writes. Decide who owns the work. If the caller should wait, use `coroutineScope`. If the work should outlive the call, give a long-lived component a scope it owns and cancels at the end of its life. If it must survive a restart, use durable storage, not a coroutine.",
 "compare": {
  "title": "Fan-out that cannot leak: StructuredTaskScope vs coroutineScope",
  "java": {"title": "PaymentDetails.java (preview in JDK 25, JEP 505: compile and run with --enable-preview)", "src": "Details details(PaymentId id) throws InterruptedException {\n    try (var scope = StructuredTaskScope.open()) {          // default: fail on the first failure\n        Subtask<Account> account = scope.fork(() -> accounts.load(id));\n        Subtask<List<Entry>> entries = scope.fork(() -> ledger.recent(id, 20));\n        scope.join();         // waits; throws StructuredTaskScope.FailedException if a subtask failed\n        return new Details(account.get(), entries.get());\n    }                         // close() cancels unfinished subtasks and waits for them\n}"},
  "kotlin": {"title": "PaymentDetails.kt", "src": "suspend fun details(id: PaymentId): Details = coroutineScope {\n    val account = async { accounts.load(id) }\n    val entries = async { ledger.recent(id, 20) }\n    Details(account.await(), entries.await())\n}   // returns only when both children are done; a failure cancels the other"},
  "note": "The idea is the same in both: subtasks cannot outlive the block that started them, the first failure cancels the siblings, and the caller gets one exception. In Java each subtask is a virtual thread running blocking code, and cancellation means interruption. In Kotlin each child is a coroutine, and cancellation reaches it at its next suspension point. The bigger practical difference is maturity. In JDK 25, `StructuredTaskScope` is a preview API that needs `--enable-preview`, and its shape has changed between previews (the JDK 21 to 24 previews used a different, subclass-based API). In Kotlin, every `launch` and `async` already joins the tree, including calls deep inside other suspend functions, and you get the guarantee without asking for it."
 },
 "worked": {
  "title": "Give an FX rate refresher a scope it owns",
  "steps": [
   {"say": "A Quarkus bean refreshes FX rates every 30 seconds. It was written with `GlobalScope`. After shutdown it keeps calling the rate provider against a closed connection pool, and in tests one instance's loop keeps running into the next test.",
    "code": "class FxRateRefresher(private val rates: RateSource) {\n    @OptIn(DelicateCoroutinesApi::class)\n    fun start() {\n        GlobalScope.launch {\n            while (true) { rates.refresh(); delay(30.seconds) }\n        }\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the bug: a static scheduler that nobody shuts down\nclass FxRateRefresher {\n    private static final ScheduledExecutorService SHARED = Executors.newScheduledThreadPool(1);\n    private final RateSource rates;\n\n    void start() {\n        SHARED.scheduleWithFixedDelay(rates::refresh, 0, 30, TimeUnit.SECONDS);\n    }\n}", "alt_lang": "java"},
   {"say": "Give the class its own scope, created once, with the dispatcher passed in so tests can use a test dispatcher. A `CoroutineName` makes it easy to spot in thread dumps and debug output.",
    "code": "class FxRateRefresher(\n    private val rates: RateSource,\n    dispatcher: CoroutineDispatcher = Dispatchers.IO,\n) : AutoCloseable {\n    // 1. one scope per instance; its Job is the parent of everything we start\n    private val scope = CoroutineScope(dispatcher + Job() + CoroutineName(\"fx-refresher\"))", "lang": "kotlin",
    "alt_code": "// Java equivalent: one scheduler per instance, with a named thread\nclass FxRateRefresher implements AutoCloseable {\n    private final RateSource rates;\n    // 1. the instance owns its scheduler\n    private final ScheduledExecutorService scheduler =\n        Executors.newSingleThreadScheduledExecutor(Thread.ofPlatform().name(\"fx-refresher\").factory());", "alt_lang": "java"},
   {"say": "Launch into that scope. Catch failures of a single refresh inside the loop, so one bad response does not end the loop and, with a plain `Job`, cancel the whole scope. Rethrow `CancellationException` (lesson 5 of this track explains why).",
    "code": "    // 2. the loop is a child of the scope\n    fun start(): Job = scope.launch {\n        while (true) {\n            try { rates.refresh() }\n            catch (e: CancellationException) { throw e }\n            catch (e: Exception) { log.warn(\"rate refresh failed\", e) }\n            delay(30.seconds)\n        }\n    }", "lang": "kotlin",
    "alt_code": "    // 2. the refresh belongs to this instance's scheduler\n    ScheduledFuture<?> start() {\n        return scheduler.scheduleWithFixedDelay(() -> {\n            try { rates.refresh(); }\n            catch (Exception e) { log.warn(\"rate refresh failed\", e); }   // an escaping exception stops the schedule\n        }, 0, 30, TimeUnit.SECONDS);\n    }", "alt_lang": "java"},
   {"say": "Close the scope when the owner's life ends: `@PreDestroy` in the bean, `@AfterEach` in a test. `cancel()` returns at once; use `cancelAndJoin()` from suspend code when you must wait for the loop to stop.",
    "code": "    // 3. tie the scope to a real lifecycle\n    override fun close() = scope.cancel()\n}\n\n@ApplicationScoped\nclass RatesLifecycle(private val refresher: FxRateRefresher) {\n    @PreDestroy fun stop() = refresher.close()\n}", "lang": "kotlin",
    "alt_code": "    // 3. tie the scheduler to a real lifecycle\n    @Override public void close() { scheduler.shutdownNow(); }\n}\n\n@ApplicationScoped\nclass RatesLifecycle {\n    @Inject FxRateRefresher refresher;\n    @PreDestroy void stop() { refresher.close(); }\n}", "alt_lang": "java"},
   {"say": "Self-check: a colleague suggests `fun start() = CoroutineScope(Dispatchers.IO).launch { ... }` to avoid the opt-in warning. Why is that no better? (Each call makes a new root scope that nothing holds on to. Nobody can cancel it, so it leaks exactly like `GlobalScope`.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Stop leaking settlement work",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/SettleAll.kt", f"{lab}/main/{P}/BatchSettler.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l03.*'",
  "steps": [
   "Run the tests. Five of seven fail. Read the messages: `settleAll` returns before anything is settled, and `shutdown` stops nothing.",
   "Fix `settleAll`: replace `GlobalScope` with `coroutineScope` so every batch is a child of the call. The three `settleAll` tests should now pass.",
   "In `BatchSettler`, add a private scope built from `context + Job()`, and make `submit` launch into it.",
   "Write `inFlight` from the scope's job: `scope.coroutineContext.job.children.count()`.",
   "Write `shutdown` so it cancels the scope's job and waits for the children to stop. Make `submit` throw `IllegalStateException` once the scope is no longer active.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "`coroutineScope { for (id in batchIds) launch { settle(id) } }` is the whole fix for `settleAll`.",
   "`check(scope.isActive) { \"settler is shut down\" }` throws `IllegalStateException` with that message. `isActive` on a scope comes from `kotlinx.coroutines.isActive`.",
   "`job` is an extension property on `CoroutineContext` (import `kotlinx.coroutines.job`). `cancelAndJoin()` is an extension on `Job`.",
   "The tests pass `StandardTestDispatcher(testScheduler)` as the context, so your scope runs on virtual time and `shutdown` returns at virtual time 0."
  ],
  "done_when": "All seven tests in `StructuredConcurrencyTest` pass."
 },
 "drill": {
  "title": "An owned scope from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a class `AuditWriter(dispatcher: CoroutineDispatcher)` with `fun write(entry: String): Job` that writes in the background, and `suspend fun close()` that cancels every pending write and waits until they have stopped. Use a suspend function `persist(entry)` that you can assume exists.",
  "answer": {"lang": "kotlin", "src": "class AuditWriter(dispatcher: CoroutineDispatcher) {\n    private val scope = CoroutineScope(dispatcher + Job())\n\n    fun write(entry: String): Job =\n        scope.launch { persist(entry) }\n\n    suspend fun close() {\n        scope.coroutineContext.job.cancelAndJoin()\n    }\n}",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: the writer owns an executor and shuts it down\nclass AuditWriter implements AutoCloseable {\n    private final ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();\n\n    Future<?> write(String entry) {\n        return pool.submit(() -> persist(entry));\n    }\n\n    @Override public void close() throws InterruptedException {\n        pool.shutdownNow();                          // interrupt pending writes\n        pool.awaitTermination(30, TimeUnit.SECONDS); // wait until they have stopped\n    }\n}"}}
 },
 "recap": [
  "Every `launch` and `async` makes a child of the scope's job, so concurrent work forms a tree that mirrors the code.",
  "A parent completes only after all of its children complete; `coroutineScope` returns after its slowest child.",
  "A child failure cancels the parent and all siblings, then surfaces as one exception at the scope. Cancellation only travels down, and a `CancellationException` from a child does not alarm the parent.",
  "`GlobalScope` (or a new `CoroutineScope(...)` inside a function) creates orphans: nothing waits for them, cancels them or sees their failures.",
  "Work that outlives a call belongs to a class that owns a scope, launches into it, and cancels it at the end of its lifecycle."
 ],
 "quiz": [
  {"q": "What happens here?\n\n```kotlin\ncoroutineScope {\n    launch { delay(100); throw IOException(\"down\") }\n    launch { delay(1_000); println(\"done\") }\n}\n```",
   "options": ["`done` prints at 1 s, then the scope throws `IOException`", "The `IOException` is printed by the uncaught handler and the scope returns normally", "At about 100 ms the second child is cancelled, `done` never prints, and the scope throws `IOException`", "The scope returns normally at 1 s, because `launch` swallows exceptions"],
   "answer": 2,
   "why": "The failed child cancels the scope's job, which cancels its sibling. The scope waits for the sibling to stop, then rethrows the original exception to its caller. Nothing waits for the full second."},
  {"q": "A child coroutine ends by throwing `CancellationException`. What happens to its parent and its siblings?",
   "options": ["Nothing: the child counts as cancelled, and the parent is not notified", "The parent is cancelled, and so are the siblings", "The parent rethrows the `CancellationException` to its caller", "The siblings are cancelled, but the parent keeps running"],
   "answer": 0,
   "why": "A `CancellationException` means \"I was cancelled\", not \"I failed\". The child cancels its own children, but the parent keeps going. Only other exceptions travel up. Lesson 5 of this track shows why that makes swallowing it dangerous."},
  {"q": "A request handler calls `GlobalScope.launch { reconcile(batch) }` and returns. A minute later the service shuts down while the reconciliation is still running. What stops the reconciliation?",
   "options": ["The request's scope, which cancels it when the response is sent", "Quarkus, which cancels all coroutines on shutdown", "`runBlocking` at the top of the call stack", "Nothing in coroutines: it runs until it finishes or the JVM exits"],
   "answer": 3,
   "why": "A `GlobalScope` coroutine has no parent, so no lifecycle reaches it. It stops when it finishes, or when the JVM dies, possibly halfway through. If it must be stopped cleanly, it needs an owner with a scope that is cancelled on shutdown."},
  {"q": "A Kafka partition worker starts a background flush loop when its partition is assigned. Where should the loop's coroutine live?",
   "options": ["In `GlobalScope`, because it outlives any single record", "In a scope owned by the partition worker, cancelled and joined in `onPartitionsRevoked`", "In `runBlocking` on the consumer's poll thread", "In a new `CoroutineScope(Dispatchers.IO)` created inside the assignment callback"],
   "answer": 1,
   "why": "The loop lives exactly as long as the partition assignment, so the worker for that partition should own the scope and cancel it when the partition is revoked. A new scope created in the callback has no owner and leaks like `GlobalScope`. `runBlocking` would block the poll thread."},
  {"q": "From lesson 2 of this track: what does this return, and when?\n\n```kotlin\ncoroutineScope {\n    launch { delay(200) }\n    42\n}\n```",
   "options": ["42, at once, because `launch` returns immediately", "42, after about 200 ms, when the child finishes", "Unit, because the last expression is `launch`", "It never returns, because nobody joins the child"],
   "answer": 1,
   "why": "The block's value is 42, but `coroutineScope` returns only after every child has completed. You don't need `join`: waiting for children is the scope's job.",
   "from": "co-02"}
 ],
 "flashcards": [
  {"front": "When does a parent coroutine complete?", "back": "Only after its own block and all of its children have completed."},
  {"front": "In a regular `coroutineScope`, one child throws `IOException`. What happens?", "back": "The scope is cancelled, which cancels the other children. The scope waits for them to stop, then rethrows the `IOException` to its caller."},
  {"front": "A child ends with `CancellationException`. Is its parent cancelled?", "back": "No. It counts as cancelled, not failed, so the parent is not notified."},
  {"front": "Which direction does cancellation travel in the job tree?", "back": "Down only. Cancelling a parent cancels all of its children; cancelling a child leaves the parent alone."},
  {"front": "Why is `GlobalScope.launch` in a request handler a leak?", "back": "The coroutine has no parent: nothing waits for it, nothing cancels it when the request ends, and its failure goes to the uncaught exception handler."},
  {"front": "How should a class that starts background coroutines be structured?", "back": "Own one `CoroutineScope(context + Job())` as a field, launch into it, and cancel it (or `cancelAndJoin`) when the owner's lifecycle ends."}
 ],
 "terms": [
  {"term": "Structured concurrency", "plain": "Concurrent work forms a tree that matches the code: children can't outlive their parent, and failures and cancels follow the tree."},
  {"term": "Parent job", "plain": "The job a new coroutine attaches to. It waits for its children and cancels them when it is cancelled."},
  {"term": "Child coroutine", "plain": "A coroutine started in a scope. Its failure cancels its parent unless the parent is a supervisor."},
  {"term": "Scope", "plain": "A coroutine context that holds a job. New coroutines started in it become that job's children."},
  {"term": "GlobalScope", "plain": "A scope with no job. Coroutines started there have no parent and are not structured."},
  {"term": "Leaked coroutine", "plain": "A coroutine that keeps running after everything that cared about it has gone."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to start a refund with `GlobalScope.launch` from a request handler, \"so the response is fast\". Explain what they lose, and what you would do instead.",
  "answer": "A coroutine in GlobalScope has no parent, so it is outside the job tree. Nothing waits for it, nothing cancels it when the request is cancelled or the service shuts down, and if it fails, the exception goes to the uncaught handler instead of to anyone who can react. If the response really shouldn't wait for the refund, the refund needs a real owner: a component with its own scope that we cancel and join on shutdown. And because a refund must not be lost on a crash or a restart, the safest choice is to record it durably first (an outbox row or a Temporal workflow) and let a background worker with an owned scope process it."
 },
 "deeper": {
  "minutes": 10,
  "body": "An owned scope does not have to be a separate root. `Job(parent)` creates a job that is a child of another one, so `CoroutineScope(dispatcher + Job(appJob))` gives you a component scope that is cancelled when the application job is cancelled. With a plain `Job`, the link also works upwards: a failure in the component cancels `appJob` too. That is usually not what you want for a long-lived component, which is one reason lesson 6 of this track reaches for `SupervisorJob(parent)`.\n\nThe tree is also how kotlinx.coroutines reports problems. When several children fail, the first exception wins, and the others are attached to it as suppressed exceptions. When you print a stack trace from a failed scope, look at the suppressed list before you conclude that only one thing went wrong.\n\nThe kotlinx-coroutines-debug module can dump the live coroutines of a running JVM with their states and creation stacks (`DebugProbes.dumpCoroutines()`). It is not on this lab's classpath, but it is the tool to reach for when you suspect a leak in a real service. Without it, the cheap trick from the Try it, walking `job.children` from a known root, already tells you how much work a component still has in flight. Exposing `inFlight` per partition worker on a health or metrics endpoint is a cheap way to spot a stuck consumer."
 },
 "sources": [
  {"title": "Coroutines basics: structured concurrency (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-basics.html"},
  {"title": "CoroutineScope (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-scope/"},
  {"title": "GlobalScope (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-global-scope/"},
  {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html"}
 ]
}
out = ROOT / "content/lessons/co-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
