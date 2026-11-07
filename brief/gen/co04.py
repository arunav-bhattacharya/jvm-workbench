import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l04"
J = "java/workbench/coroutines/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l04.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="One shared pool of worker threads. Default takes one thread per core for CPU work. '
    'IO allows 64 blocking tasks. Two views over IO, issuer with 20 and reports with 100, add their own budgets on top, so up to 184 blocking tasks can run at peak.">'
    '<rect class="box" x="15" y="16" width="670" height="46" rx="8"/>'
    '<text class="t" x="350" y="37" text-anchor="middle">one shared pool of worker threads</text>'
    '<text class="t-s t-m" x="350" y="54" text-anchor="middle">threads are created as the budgets below need them</text>'
    '<line class="ln" x1="95" y1="62" x2="95" y2="120"/>'
    '<line class="ln" x1="265" y1="62" x2="265" y2="120"/>'
    '<line class="ln-d" x1="435" y1="62" x2="435" y2="120"/>'
    '<line class="ln-d" x1="605" y1="62" x2="605" y2="120"/>'
    '<rect class="box-a" x="15" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="95" y="145" text-anchor="middle">Default</text>'
    '<text class="t-s" x="95" y="165" text-anchor="middle">CPU work</text>'
    '<text class="t-s" x="95" y="181" text-anchor="middle">one per core (min 2)</text>'
    '<rect class="box-b" x="185" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="265" y="145" text-anchor="middle">IO</text>'
    '<text class="t-s" x="265" y="165" text-anchor="middle">blocking calls</text>'
    '<text class="t-s" x="265" y="181" text-anchor="middle">up to 64 at once</text>'
    '<rect class="box-ok" x="355" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="435" y="145" text-anchor="middle">"issuer"</text>'
    '<text class="t-s t-code" x="435" y="165" text-anchor="middle">IO.limited(20)</text>'
    '<text class="t-s" x="435" y="181" text-anchor="middle">adds up to 20</text>'
    '<rect class="box-ok" x="525" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="605" y="145" text-anchor="middle">"reports"</text>'
    '<text class="t-s t-code" x="605" y="165" text-anchor="middle">IO.limited(100)</text>'
    '<text class="t-s" x="605" y="181" text-anchor="middle">adds up to 100</text>'
    '<text class="t-s t-a" x="95" y="214" text-anchor="middle">never blocked by IO</text>'
    '<text class="t-s t-ok" x="520" y="214" text-anchor="middle">views over IO are elastic: they add to the 64</text>'
    '<rect class="box-dim" x="185" y="232" width="500" height="44" rx="8"/>'
    '<text class="t" x="435" y="259" text-anchor="middle">peak blocking tasks: 64 + 20 + 100 = 184</text>'
    '<text class="t-s t-m" x="95" y="250" text-anchor="middle">a view over Default</text>'
    '<text class="t-s t-m" x="95" y="266" text-anchor="middle">stays within its cores</text>'
    '</svg>'
)

L = {
 "id": "co-04",
 "title": "Dispatchers and the coroutine context",
 "minutes": 35,
 "goal": "By the end you can say which thread a coroutine runs on and why, move blocking and CPU work to the right dispatcher with withContext, give a slow resource its own budget with limitedParallelism, and read and extend a coroutine context with +.",
 "warmup": {
  "q": "A coroutine launched on `Dispatchers.Default` calls a blocking JDBC query that takes 300 ms. The pod has 4 cores. What does that call cost the rest of the service while it runs?",
  "options": [
   "Nothing: a coroutine suspends while the query runs, so the thread is free",
   "One of the 4 Default threads is stuck for 300 ms, so other CPU work queues behind it",
   "Nothing: kotlinx.coroutines moves blocking calls to Dispatchers.IO by itself",
   "The call fails, because blocking calls are not allowed in a coroutine"
  ],
  "answer": 1,
  "why": "A coroutine only frees its thread at a suspension point, and a JDBC call is not one: it blocks the thread. Default has one thread per core, so on 4 cores, four such calls stop all CPU work. Nothing detects or moves the call for you. You move it with `withContext(Dispatchers.IO)`."
 },
 "sections": [
  {
   "h": "A dispatcher picks the thread, and withContext switches it",
   "body": "`suspend` says nothing about threads (lesson 1 of this track). The **dispatcher** in a coroutine's context does: it decides which thread runs the coroutine each time it starts or resumes. kotlinx.coroutines ships four.\n\n- `Dispatchers.Default` is a pool with one thread per CPU core, and at least two. `launch` and `async` use it when the context names no dispatcher.\n- `Dispatchers.IO` is for calls that block a thread, such as JDBC or a blocking HTTP client. Up to 64 of them run at once.\n- `Dispatchers.Main` is the UI thread on Android, JavaFX or Swing, and needs a UI module on the classpath. A Quarkus service has none, and using it throws `IllegalStateException`.\n- `Dispatchers.Unconfined` has no thread of its own. The coroutine starts on the caller's thread and, after its first suspension, carries on on whatever thread resumed it. The docs say it should not be used in general code.\n\n`runBlocking` is the odd one out: it runs its coroutine on the thread that called it.\n\nTo run one piece of work somewhere else, use `withContext`:\n\n```kotlin\nsuspend fun statementPdf(accountId: String): ByteArray {\n    val rows = withContext(Dispatchers.IO) { store.loadRows(accountId) }   // blocking JDBC call\n    return withContext(Dispatchers.Default) { renderer.render(rows) }      // CPU-heavy layout\n}\n```\n\n```java\n// Java equivalent: CompletableFuture stages, each with its own executor\nCompletableFuture<byte[]> statementPdf(String accountId) {\n    return CompletableFuture.supplyAsync(() -> store.loadRows(accountId), ioPool)  // blocking JDBC call\n        .thenApplyAsync(renderer::render, cpuPool);                                // CPU-heavy layout\n}\n```\n\n`withContext` suspends the caller, runs the block on the other dispatcher, and then resumes the caller on its own dispatcher with the block's result. The code reads top to bottom. In the Java version every stage names its executor, and whatever you chain next runs where the last stage left off, not back where you started.\n\n`withContext` is also a scope, like `coroutineScope` in lesson 3 of this track. It waits for any children launched inside the block, and a failure inside it comes out as an exception in the caller.\n\nA switch is cheap but not free: the library queues a task on the other dispatcher, and the coroutine's state machine resumes there. Values you wrote before the switch are visible after it, even on another thread. The library provides that happens-before edge, so you don't need `@Volatile` for a coroutine's own locals.",
   "try": {
    "title": "Print where each step runs",
    "minutes": 4,
    "steps": [
     "Read `WhereDoesItRun.kt`. It turns on debug mode, which adds the coroutine's name and number to thread names. Predict the thread for each line.",
     "Run it. Look closely at the two Unconfined lines.",
     "Run it two or three times. Do Default and IO always print different workers?",
     "Run the Java twin and match each line to its Kotlin counterpart."
    ],
    "code": tryit("WhereDoesItRun.kt", "WhereDoesItRunJava.java"),
    "expect": "`runBlocking` prints `main @statement#1`. Default and IO print `DefaultDispatcher-worker-N` threads, and on some runs IO prints the same worker as Default: the two share one pool. Unconfined starts on `main` and, after `delay`, resumes on `kotlinx.coroutines.DefaultExecutor`, the thread that fired the timer. The single-thread executor prints `ledger-writer @ledger#1` (the new name replaced the old one) and the virtual-thread executor prints a `VirtualThread`. In the Java twin, the `thenAccept` stage runs on whichever thread completed the timer stage, which is Java's version of Unconfined."
   },
   "refs": [
    {"title": "Coroutine context and dispatchers (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html", "kind": "read"}
   ]
  },
  {
   "h": "Default is for CPU work, IO is for blocking calls",
   "body": "`Dispatchers.Default` has as many threads as the machine has cores. On a 4-core pod that is 4. Run a 200 ms blocking query there and you hold one of those 4 threads for 200 ms while it does nothing. Four requests doing that at once take every thread, and all the CPU work in the service waits in the queue: JSON parsing, signature checks, and the coroutines of every other request.\n\nA blocking call belongs on `Dispatchers.IO`. Its limit is 64 (or the number of cores, if that is larger), set by the system property `kotlinx.coroutines.io.parallelism`. IO threads spend most of their time asleep in the kernel, waiting for Oracle or the issuer to answer, so 64 of them on 4 cores is fine.\n\nIO and Default share one pool of worker threads. When code on Default calls `withContext(Dispatchers.IO)`, the docs say it \"typically does not lead to an actual switching to another thread\": the same worker keeps going, and the library counts it against IO's limit instead of Default's. What the split buys you is separate budgets. Blocking work can fill IO, and Default still has a thread for every core.\n\nThree rules follow.\n\nNever block on Default. Put `withContext(Dispatchers.IO)` around each blocking call at the lowest level, inside the repository or the client, so callers don't need to know the call blocks.\n\nPut long CPU work on Default: laying out a statement PDF, hashing a file of card numbers. A few microseconds of CPU work need no switch at all.\n\nDon't wrap calls that already suspend. A non-blocking HTTP client, a `delay` or a `Channel.receive` never holds a thread while waiting, so `withContext(Dispatchers.IO)` around them only adds a hop.\n\nThe Java world has the same split under other names. The common `ForkJoinPool` is sized for CPU work, and blocking in it starves `parallelStream()` and every `CompletableFuture.supplyAsync` without an executor. Lesson 3 of the executors track sized a pool for each kind of work. Here the library gives you the two pools ready-made, and your job is to put each call in the right one.",
   "try": {
    "title": "Starve Default with blocking calls",
    "minutes": 4,
    "steps": [
     "Read `BlockingOnDefault.kt`. It starts 32 blocking calls of 200 ms, then asks Default to run a task that takes a microsecond. Predict how long that tiny task waits to start on your machine.",
     "Run it.",
     "Run it with `-Pargs=io`, which puts the blocking calls on IO. Predict first.",
     "Run the Java twin both ways."
    ],
    "code": tryit("BlockingOnDefault.kt", "BlockingOnDefaultJava.java", " -Pargs=io", " -Pargs=io"),
    "expect": "On 4 cores, the 32 calls take about 1,600 ms on Default (8 rounds of 4) and the tiny task waits about 1,500 ms, because every Default thread is asleep in `Thread.sleep`. With `-Pargs=io` the calls take about 220 ms (all 32 at once) and the tiny task starts within a few milliseconds. Scale the numbers to your core count. The Java twin shows the same starvation with a `ForkJoinPool` sized like Default."
   }
  },
  {
   "h": "A limitedParallelism view gives each resource its own budget",
   "body": "IO's 64 is one budget for every blocking call in the JVM. That hurts when one resource is slow. Say the card issuer's client blocks, and its connection pool has 20 connections. When the issuer slows down, 64 coroutines can pile into issuer calls: 20 hold a connection, 44 hold an IO thread while they wait for one, and the ledger's JDBC calls, which need IO threads too, queue behind them.\n\n`limitedParallelism` makes a **view** of a dispatcher with its own limit:\n\n```kotlin\nval issuer = Dispatchers.IO.limitedParallelism(20, \"issuer\")     // at most 20 issuer calls at once\nval reports = Dispatchers.IO.limitedParallelism(100, \"reports\")  // a batch export with its own budget\n```\n\n```java\n// Java equivalent: a separate pool per resource (a bulkhead)\nExecutorService issuer = Executors.newFixedThreadPool(20, Thread.ofPlatform().name(\"issuer-\", 0).factory());\nExecutorService reports = Executors.newFixedThreadPool(100, Thread.ofPlatform().name(\"reports-\", 0).factory());\n```\n\nA view owns no threads and needs no closing. It is a gate in front of its parent: at most 20 coroutines from the issuer view run at the same moment, and the rest wait in the view's queue without holding a thread. The name is optional. It arrived in kotlinx.coroutines 1.9, when the API became stable, and it is what `toString()` returns, which helps in logs.\n\nViews over IO are **elastic**: they don't take a share of IO's 64, they add to it. The KDoc's own example has a view of 100 for MySQL and one of 60 for MongoDB, and says the system may then run up to 64 + 100 + 60 blocking tasks at peak. So the view isolates the issuer both ways. It can't take more than 20 threads, and a burst of other IO work can't starve it either.\n\nViews over Default are different. A view can never exceed its parent's parallelism, so `Dispatchers.Default.limitedParallelism(100)` still runs at most one task per core. And `limitedParallelism(1)` gives you a view that runs one task at a time, which is not the same as a lock. Lesson 10 of this track shows why.\n\nWhen you need a dispatcher that is not one of these, wrap an executor: `executor.asCoroutineDispatcher()`. That includes the virtual-thread executor from the virtual threads track, `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`. kotlinx.coroutines 1.11 has no built-in virtual-thread dispatcher, so this is the supported route. A wrapped executor is yours to close: the dispatcher is `AutoCloseable`, and `close()` shuts the executor down.",
   "figure": {"svg": FIG, "caption": "Default and IO share one pool of threads but keep separate budgets. Views over IO add their own budgets on top of IO's 64."},
   "try": {
    "title": "Three budgets for 400 blocking calls",
    "minutes": 4,
    "steps": [
     "Read `BlockingBudgets.kt`. It runs 400 blocking calls of 200 ms on plain IO, on a view of 400 over IO, and on a virtual-thread executor. Predict the time and the peak for each.",
     "Run it.",
     "Change the view to `Dispatchers.Default.limitedParallelism(400)` and run it again. Predict first.",
     "Run the Java twin."
    ],
    "code": tryit("BlockingBudgets.kt", "BlockingBudgetsJava.java"),
    "expect": "Plain IO peaks at 64 calls at once, so 400 calls take 7 rounds, about 1,400 ms. The view of 400 runs all 400 at once in about 300 ms: it adds to IO's 64 instead of sharing it. The virtual-thread executor also peaks at 400. The view over Default peaks at your core count (at least 2) and takes far longer (about 20 s on 4 cores), because a view can't exceed its parent. The Java twin shows the same pattern with a fixed pool of 64, a cached pool and a virtual thread per task."
   },
   "refs": [
    {"title": "limitedParallelism (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html", "kind": "docs"},
    {"title": "Dispatchers.IO (API reference: the 64 limit and elastic views)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html", "kind": "docs"}
   ]
  },
  {
   "h": "The context is a set of elements, and + merges them",
   "body": "A coroutine context is a small immutable set of elements, at most one per key. You've met most of them already: the `Job` (the node in the tree from lesson 3 of this track), the dispatcher, `CoroutineName`, and `CoroutineExceptionHandler` (lesson 6). `+` combines two contexts, and when both have an element with the same key, the right side wins.\n\n```kotlin solo\nval ctx = Dispatchers.IO + CoroutineName(\"capture\")\nval renamed = ctx + CoroutineName(\"refund\")\nrenamed[CoroutineName]             // CoroutineName(refund): the right side won\nrenamed[ContinuationInterceptor]   // Dispatchers.IO: untouched\n```\n\nA new coroutine's context is built in three steps: the scope's context, then the context you pass to the builder (which overrides it), then a fresh `Job` that is a child of the scope's job. So children inherit the dispatcher, the name and anything else you add, but every child gets its own job. `withContext(ctx)` builds the context of its block the same way.\n\nInside a suspend function, read an element with `currentCoroutineContext()[Key]`. The key is usually the element's companion object, which is why `ctx[CoroutineName]` reads so naturally. One change in kotlinx.coroutines 1.11: using `CoroutineDispatcher` as the key is deprecated, and later versions will reject it. Look the dispatcher up with `ContinuationInterceptor`.\n\nYou can define your own element by extending `AbstractCoroutineContextElement` and giving it a companion `Key`. The lab does that to carry a payment's trace id into every coroutine that works on the payment.\n\nWhat does not follow a coroutine is a plain `ThreadLocal`. A coroutine that resumes on another thread sees that thread's value, which is how request ids and MDC log fields go missing after a `withContext`. `asContextElement()` turns a `ThreadLocal` into an element. The library sets the value on whichever thread runs the coroutine and restores the old value when the coroutine leaves.\n\n```kotlin\nrequestId.set(\"req-42\")\nwithContext(Dispatchers.Default) { requestId.get() }                                // null: another thread\nwithContext(Dispatchers.Default + requestId.asContextElement()) { requestId.get() }  // req-42\n```\n\n```java\n// Java equivalent: copy the ThreadLocal into the task by hand\nString captured = REQUEST_ID.get();\npool.submit(() -> {\n    REQUEST_ID.set(captured);\n    try { work(); } finally { REQUEST_ID.remove(); }\n});\n```\n\nFor SLF4J's MDC there is a ready-made element, `MDCContext`, in the `kotlinx-coroutines-slf4j` module, which is not on this lab's classpath. And `CoroutineName` shows up in thread names when the JVM runs with `-Dkotlinx.coroutines.debug` (assertions with `-ea` turn it on too). That costs little, and it makes thread dumps readable.",
   "try": {
    "title": "Merge contexts and lose a ThreadLocal",
    "minutes": 3,
    "steps": [
     "Read `ContextElements.kt`. Predict the three lines about `requestId`.",
     "Run it.",
     "Add `+ CoroutineName(\"late\")` to the end of the `renamed` line and run again. Which name wins now?",
     "Run the Java twin, which copies the value by hand the way an MDC-propagating executor wrapper does."
    ],
    "code": tryit("ContextElements.kt", "ContextElementsJava.java"),
    "expect": "The name lookups print `CoroutineName(capture)`, then `CoroutineName(refund)`, and the dispatcher lookup prints `Dispatchers.IO`. The main thread sees `req-42`, the plain `ThreadLocal` on Default prints `null`, and the `asContextElement` version prints `req-42`. After your change the rightmost name, `late`, wins. The Java twin prints the same three `requestId` lines."
   },
   "refs": [
    {"title": "asContextElement (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/as-context-element.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A dispatcher is the dispatch desk at a delivery company. Default is a small team of in-house drivers, one per loading bay, who never sit idle. IO is a large pool of contract drivers who spend most of the day parked outside customers' buildings, waiting for someone to sign. A `limitedParallelism` view is a separate contract for one difficult customer: at most 20 drivers on that route, hired on top of the usual pool. The context is the delivery note stapled to each parcel: which desk, which customer, which tracking number, and every parcel split off from it gets a copy. The analogy breaks on idle drivers. A real driver waiting at a door can't be reassigned. A suspended coroutine gives its thread back at once, which is why only blocking calls need the IO desk at all.",
 "in_your_world": "In a Quarkus service, coroutines usually start on a worker or event-loop thread and then run wherever their dispatcher sends them. Give each blocking dependency a view sized to its real limit: `Dispatchers.IO.limitedParallelism(20, \"oracle\")` for an Agroal pool of 20 connections, and another for a blocking issuer SDK. Then a slow issuer can't take the threads the ledger queries need. Wrap the JDBC call itself in `withContext(oracle)` inside the repository, so a Kafka consumer coroutine on Default never blocks on Oracle. And if your logs rely on an MDC trace id, carry it in the context (`MDCContext` or `asContextElement`). Otherwise the half of a payment's log lines written after the first `withContext` will be missing it.",
 "mistake": "The most common mistake is a blocking call on Default: a JDBC query, a blocking HTTP client, a `Thread.sleep` in a retry loop, inside a `launch` that inherited Default. It works in tests with one request at a time and falls over under load, when a handful of slow queries occupy every core's thread. People make it because nothing in the type system marks a call as blocking, and the code looks like any other function call. Wrap every blocking call in `withContext(Dispatchers.IO)` (or a view sized to the resource) inside the function that makes it, so the caller can't get it wrong. The opposite mistake is cheaper but still common: wrapping already-suspending calls in `withContext(Dispatchers.IO)` \"to be safe\", which adds a hop and hides which calls really block.",
 "compare": {
  "title": "One request, two kinds of work: executors vs dispatchers",
  "java": {"title": "StatementService.java", "src": "class StatementService {\n    private final ExecutorService io;     // sized for blocking JDBC calls\n    private final ExecutorService cpu;    // sized to the cores\n\n    StatementService(ExecutorService io, ExecutorService cpu) { this.io = io; this.cpu = cpu; }\n\n    CompletableFuture<byte[]> statementPdf(String accountId) {\n        return CompletableFuture\n            .supplyAsync(() -> store.loadRows(accountId), io)   // 1. block on an IO thread\n            .thenApplyAsync(renderer::render, cpu);              // 2. render on a CPU thread\n        // the caller gets a future; whatever it chains next runs on a cpu thread\n    }\n}"},
  "kotlin": {"title": "StatementService.kt", "src": "class StatementService(\n    private val io: CoroutineDispatcher = Dispatchers.IO,\n    private val cpu: CoroutineDispatcher = Dispatchers.Default,\n) {\n    suspend fun statementPdf(accountId: String): ByteArray {\n        val rows = withContext(io) { store.loadRows(accountId) }   // 1. block on an IO thread\n        return withContext(cpu) { renderer.render(rows) }         // 2. render on a CPU thread\n    }   // the caller resumes on its own dispatcher with the bytes\n}"},
  "note": "Both versions keep the blocking call off the CPU threads, and both take the pools as constructor arguments so a test can pass its own. The difference is where the caller ends up. With `CompletableFuture`, the result is delivered on the thread of the last stage, and the caller either blocks on `join()` or keeps chaining callbacks that run who knows where. With `withContext`, the caller suspends, and when the block finishes it resumes on its own dispatcher, as if the call had been ordinary. You also own less: `Dispatchers.IO` and `Dispatchers.Default` are shared, process-wide pools that you never create or shut down, while the Java version needs two executors with a lifecycle."
 },
 "worked": {
  "title": "Give a blocking issuer client a budget of its own",
  "steps": [
   {"say": "A Kafka consumer captures card payments with a blocking issuer SDK. Each record is handled in `launch` on Default, on a 4-core pod. When the issuer slows to 2 s per call, consumer lag climbs and unrelated CPU work in the pod stalls.",
    "code": "class CaptureHandler(private val issuer: BlockingIssuerClient, private val scope: CoroutineScope) {\n    fun onRecord(record: CaptureRequest) {\n        scope.launch {                                  // scope uses Dispatchers.Default\n            val result = issuer.capture(record)         // blocks a Default thread for up to 2 s\n            ledger.record(result)\n        }\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the bug: blocking calls on the common pool, which is sized for CPU work\nclass CaptureHandler {\n    void onRecord(CaptureRequest record) {\n        CompletableFuture.supplyAsync(() -> issuer.capture(record))   // no executor: ForkJoinPool.commonPool()\n            .thenAccept(ledger::record);\n    }\n}", "alt_lang": "java"},
   {"say": "First, get the blocking call off Default. Put the switch inside a small suspend wrapper around the SDK, so no caller can forget it.",
    "code": "class SuspendingIssuer(private val sdk: BlockingIssuerClient) {\n    // 1. the only place that knows this SDK blocks\n    suspend fun capture(req: CaptureRequest): CaptureResult =\n        withContext(Dispatchers.IO) { sdk.capture(req) }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: the wrapper picks the executor, so callers can't forget\nclass AsyncIssuer {\n    private final ExecutorService io = Executors.newCachedThreadPool();\n    // 1. the only place that knows this SDK blocks\n    CompletableFuture<CaptureResult> capture(CaptureRequest req) {\n        return CompletableFuture.supplyAsync(() -> sdk.capture(req), io);\n    }\n}", "alt_lang": "java"},
   {"say": "IO allows 64 calls, but the SDK's pool has 20 connections. A slow issuer would let 64 coroutines take IO threads, and 44 of them would only be waiting for a connection, while ledger queries queue for IO threads. Give the issuer a view sized to its pool, and inject it so a test can pass a test dispatcher.",
    "code": "class SuspendingIssuer(\n    private val sdk: BlockingIssuerClient,\n    // 2. a budget sized to the SDK's 20 connections, on top of IO's 64\n    private val dispatcher: CoroutineDispatcher = Dispatchers.IO.limitedParallelism(20, \"issuer\"),\n) {\n    suspend fun capture(req: CaptureRequest): CaptureResult =\n        withContext(dispatcher) { sdk.capture(req) }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: a bulkhead pool of exactly 20 threads for the issuer\nclass AsyncIssuer implements AutoCloseable {\n    // 2. a budget sized to the SDK's 20 connections\n    private final ExecutorService issuerPool =\n        Executors.newFixedThreadPool(20, Thread.ofPlatform().name(\"issuer-\", 0).factory());\n\n    CompletableFuture<CaptureResult> capture(CaptureRequest req) {\n        return CompletableFuture.supplyAsync(() -> sdk.capture(req), issuerPool);\n    }\n\n    @Override public void close() { issuerPool.shutdown(); }\n}", "alt_lang": "java"},
   {"say": "The handler no longer cares where the issuer runs. Its own work (mapping, a suspending ledger call) can stay on Default.",
    "code": "fun onRecord(record: CaptureRequest) {\n    scope.launch {\n        val result = issuer.capture(record)   // 3. suspends; no Default thread is held\n        ledger.record(result)                 // back on Default\n    }\n}", "lang": "kotlin",
    "alt_code": "void onRecord(CaptureRequest record) {\n    issuer.capture(record)               // 3. runs on the issuer pool\n        .thenAccept(ledger::record);     //    and so does this stage, unless you pass an executor\n}", "alt_lang": "java"},
   {"say": "Self-check: why not `Executors.newFixedThreadPool(20).asCoroutineDispatcher()` instead of the view? (It works, but it is a pool you must close, with 20 threads that sit idle between bursts. The view has no lifecycle, borrows threads from the shared pool only while calls run, and still caps the issuer at 20.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Put each call on the right dispatcher",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/StatementService.kt", f"{lab}/main/{P}/IssuerDispatcher.kt", f"{lab}/main/{P}/TraceContext.kt",
            f"{lab}/main/{P}/StatementModel.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l04.*'",
  "steps": [
   "Run the tests. All eight fail. Read `StatementModel.kt` first: it has the blocking store, the CPU renderer and a `PaymentTrace` context element.",
   "In `StatementService.statementPdf`, run `loadRows` inside `withContext(io)` and `render` inside `withContext(cpu)`. The tests pass two single-thread dispatchers named `test-io` and `test-cpu`, so they can see where each call ran.",
   "Write `issuerDispatcher()`: a view over `Dispatchers.IO` that allows exactly 20 calls at once and is named `issuer`. Don't create a thread pool.",
   "Write `withPaymentTrace`: run the block in `withContext` with a `PaymentTrace(traceId)` and a `CoroutineName(\"payment-$traceId\")`, combined with `+`.",
   "Write `currentTraceId()`: read the `PaymentTrace` element from the current context by its key.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "`withContext(io) { store.loadRows(accountId) }` returns the rows. You don't need `async`, because the two steps depend on each other.",
   "`limitedParallelism` takes an optional second argument, the view's name. The name is what `toString()` returns.",
   "`withContext(context, block)` accepts the block parameter as it is. `PaymentTrace(id) + CoroutineName(\"payment-$id\")` is a `CoroutineContext`.",
   "`currentCoroutineContext()` (from `kotlinx.coroutines`) returns the context of the calling coroutine. The companion object `PaymentTrace` is the key, so `ctx[PaymentTrace]` gives you a `PaymentTrace?`."
  ],
  "done_when": "All eight tests in `DispatchersTest` pass."
 },
 "drill": {
  "title": "Two dispatchers and a budget, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `suspend fun riskReport(merchantId: String): Report` that loads transactions with a blocking `repo.load(merchantId)` and scores them with a CPU-heavy `scorer.score(rows)`, each on the right dispatcher. Then declare a dispatcher for a blocking sanctions-screening client that has a pool of 8 connections, without creating a thread pool.",
  "answer": {"lang": "kotlin", "src": "suspend fun riskReport(merchantId: String): Report {\n    val rows = withContext(Dispatchers.IO) { repo.load(merchantId) }    // blocking: IO\n    return withContext(Dispatchers.Default) { scorer.score(rows) }     // CPU: Default\n}\n\nval sanctions: CoroutineDispatcher = Dispatchers.IO.limitedParallelism(8, \"sanctions\")",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: one executor per kind of work, plus a bulkhead pool\nCompletableFuture<Report> riskReport(String merchantId) {\n    return CompletableFuture.supplyAsync(() -> repo.load(merchantId), ioPool)  // blocking: IO pool\n        .thenApplyAsync(scorer::score, cpuPool);                              // CPU: CPU pool\n}\n\nExecutorService sanctions = Executors.newFixedThreadPool(8, Thread.ofPlatform().name(\"sanctions-\", 0).factory());"}}
 },
 "recap": [
  "The dispatcher in a coroutine's context picks its thread. `launch` and `async` default to `Dispatchers.Default`, which has one thread per core (at least 2).",
  "Blocking calls go on `Dispatchers.IO` (64 at once by default), wrapped in `withContext` inside the function that blocks. CPU work goes on Default. Calls that already suspend need no switch.",
  "`withContext` runs a block on another dispatcher and resumes the caller on its own, with the result. IO and Default share threads, so the switch is cheap.",
  "`Dispatchers.IO.limitedParallelism(n, name)` is a budget for one resource. IO views add to the 64, while views over Default never exceed the core count.",
  "A context is a set of elements keyed by type. `+` merges them, with the right side winning, and children inherit everything except the `Job`.",
  "A plain `ThreadLocal` does not follow a coroutine across threads. Carry it with `asContextElement()` (or `MDCContext` for logging)."
 ],
 "quiz": [
  {"q": "A Quarkus endpoint handles 10 concurrent requests on a 4-core pod. Each one runs `launch { repo.findPayment(id) }` (a blocking 300 ms JDBC call) in a scope whose dispatcher is Default. At that moment a coroutine on Default needs 1 ms of CPU to check a signature. When does it run?",
   "options": ["At once, because Default and IO are separate thread pools", "Only once a Default thread finishes its blocking call, roughly 300 ms later", "At once, because kotlinx.coroutines moves blocking calls to IO for you", "Never: Default throws `IllegalStateException` when a thread blocks for too long"],
   "answer": 1,
   "why": "All 4 Default threads are blocked inside JDBC calls, so the signature check waits in the queue until one returns. Nothing moves a blocking call for you, and nothing throws. Wrapping the query in `withContext(Dispatchers.IO)` keeps Default free."},
  {"q": "A nightly export makes 300 blocking calls to a reporting database whose pool has 100 connections. It must not slow down the service's other blocking calls. Which dispatcher fits?",
   "options": ["`Dispatchers.IO`", "`Dispatchers.Default.limitedParallelism(100)`", "`Dispatchers.IO.limitedParallelism(100, \"reports\")`", "`Dispatchers.Unconfined`"],
   "answer": 2,
   "why": "A view over IO caps the export at 100, and because IO views are elastic it adds to IO's 64 instead of using them up. Plain IO would let the export take all 64 threads. A view over Default can't exceed the core count, and Default must never block anyway."},
  {"q": "What does this print?\n\n```kotlin\nval ctx = CoroutineName(\"a\") + Dispatchers.IO + CoroutineName(\"b\")\nprintln(ctx[CoroutineName]?.name)\n```",
   "options": ["`b`", "`a`", "`a, b`", "`null`, because the dispatcher replaced the name"],
   "answer": 0,
   "why": "A context holds at most one element per key, and `+` lets the right side win. `CoroutineName(\"b\")` replaces `a`. The dispatcher has a different key, so it sits beside the name without touching it."},
  {"q": "Inside `withContext(Dispatchers.IO + CoroutineName(\"capture\")) { ... }` you call `launch(CoroutineName(\"refund\")) { ... }`. What does the child coroutine's context contain?",
   "options": ["Default and `refund`, because `launch` uses Default unless told otherwise", "IO and `capture`, because the parent's context always wins", "IO and `refund`, and the same `Job` as the `withContext` block", "IO and `refund`, and a new `Job` that is a child of the block's job"],
   "answer": 3,
   "why": "A child starts from its scope's context (IO and `capture`), then the builder's argument overrides it (`refund`), then it gets a fresh `Job` that is a child of the scope's job. The \"Default unless told\" rule only applies when the context has no dispatcher at all."},
  {"q": "From the executors track: each issuer call holds one of the issuer SDK's 20 connections. You give issuer calls their own pool of 64 threads. How many issuer calls can really make progress at once?",
   "options": ["64", "20", "84", "One per core"],
   "answer": 1,
   "why": "The smallest limit on the path is the real ceiling. The other 44 threads sit waiting for a connection. That is why the issuer's dispatcher in this lesson is a view of exactly 20.",
   "from": "exec-03"}
 ],
 "flashcards": [
  {"front": "How many threads does `Dispatchers.Default` have?", "back": "One per CPU core, and at least two."},
  {"front": "What is `Dispatchers.IO`'s default limit?", "back": "64 parallel blocking tasks, or the core count if that is larger. The `kotlinx.coroutines.io.parallelism` property changes it."},
  {"front": "Does `Dispatchers.IO.limitedParallelism(100)` take 100 of IO's 64 threads?", "back": "No. Views over IO are elastic and add to IO's budget: IO and the view together can run 64 + 100 blocking tasks."},
  {"front": "What does `withContext(Dispatchers.IO) { load() }` do to the calling coroutine?", "back": "It suspends the caller, runs `load()` on IO, then resumes the caller on its own dispatcher with the result."},
  {"front": "`ctx` holds `CoroutineName(\"a\")`. What name does `ctx + CoroutineName(\"b\")` hold?", "back": "`b`. One element per key, and the right side of `+` wins."},
  {"front": "Why does a `ThreadLocal` read `null` after `withContext(Dispatchers.Default)`?", "back": "The block runs on another thread, which has its own value. Pass `threadLocal.asContextElement()` in the context to carry it along."},
  {"front": "In kotlinx.coroutines 1.11, which key looks up the dispatcher in a context?", "back": "`ContinuationInterceptor`. Using `CoroutineDispatcher` as the key is deprecated."}
 ],
 "terms": [
  {"term": "Dispatcher", "plain": "The context element that decides which thread runs a coroutine each time it starts or resumes."},
  {"term": "Dispatchers.Default", "plain": "The shared pool for CPU work: one thread per core, at least two."},
  {"term": "Dispatchers.IO", "plain": "The shared pool for blocking calls: up to 64 at once by default, using the same threads as Default."},
  {"term": "limitedParallelism view", "plain": "A dispatcher in front of another one that lets at most n of its tasks run at the same time. It owns no threads."},
  {"term": "withContext", "plain": "Runs a block with a changed context (often another dispatcher) and returns its result to the caller."},
  {"term": "Coroutine context", "plain": "The immutable set of elements a coroutine carries: job, dispatcher, name, exception handler, your own elements."},
  {"term": "Context element", "plain": "One entry in a context, found by its key, usually the class's companion object."}
 ],
 "explain_back": {
  "prompt": "A teammate's payment-status endpoint got slow under load, and so did unrelated endpoints. You find `repo.findStatus(id)`, a blocking JDBC call, inside a coroutine on Default. Explain what was happening and the two changes you would make.",
  "answer": "Default has one thread per core, so on our 4-core pods only 4 coroutines can run on it at once. The JDBC call doesn't suspend, it blocks, so each slow query held a Default thread for its whole duration. A few slow queries took every Default thread, and all the CPU work in the service, including other endpoints, waited in the queue. First, I'd wrap the call in `withContext` inside the repository, so it runs on IO and nobody calling `findStatus` has to remember. Second, I'd give the database its own budget, `Dispatchers.IO.limitedParallelism(20, \"oracle\")` to match our 20-connection pool, so a slow Oracle can't use up IO threads that other blocking calls need. That view adds to IO's 64 rather than taking from them, and it needs no closing."
 },
 "deeper": {
  "minutes": 10,
  "body": "Default and IO are two faces of one scheduler. On the JVM, kotlinx.coroutines runs a single pool of worker threads, and each task is marked as CPU work or blocking work. A worker running a blocking task doesn't count against Default's limit, so the scheduler can start another worker for CPU work. That is how a switch from Default to IO can stay on the same thread: the worker just changes which budget it is counted against. IO itself is a view of 64 over an unbounded blocking budget, which is why further views over IO can add to it.\n\nThe docs say `Dispatchers.IO.limitedParallelism(n)` can safely replace the older `newFixedThreadPoolContext(n)`. The old function creates n dedicated threads that you must close, and that idle between bursts. If you find it in a codebase, a view is almost always the better choice.\n\n`Dispatchers.Unconfined` has one legitimate niche: code that must react immediately on whatever thread delivered an event, such as some operator internals. To avoid stack overflows, nested unconfined coroutines form an event loop instead of calling each other recursively, which makes the order of execution surprising. Treat it as a library-writer's tool.\n\nA virtual-thread dispatcher (`Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`) is an interesting option for code that blocks a lot, because each task gets a cheap virtual thread instead of an IO worker. It is not a free win. A virtual thread pinned by `synchronized` on JDK 21 to 23 (JEP 491 removed most pinning in JDK 24) still holds a carrier. Every time the coroutine resumes, the executor starts a new virtual thread for it, so you lose the scheduler's habit of keeping a coroutine on the same worker. And cancelling a coroutine blocked inside it still needs `runInterruptible`, which lesson 5 of this track covers. Lesson 11 of this track compares the options for a whole service."
 },
 "sources": [
  {"title": "Coroutine context and dispatchers (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html"},
  {"title": "Dispatchers.IO (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html"},
  {"title": "CoroutineDispatcher.limitedParallelism (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html"},
  {"title": "withContext (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-context.html"}
 ]
}
out = ROOT / "content/lessons/co-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
