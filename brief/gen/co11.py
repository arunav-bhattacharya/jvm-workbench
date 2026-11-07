import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l11"
J = "java/workbench/coroutines/l11"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l11.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Kotlin coroutines in the middle, with bridges to three neighbours. '
    'CompletableFuture: await() suspends on a future, future { } returns one to Java. Reactor: mono { } and asFlux() go out, '
    'awaitSingle() and asFlow() come in. Virtual threads: asCoroutineDispatcher() runs coroutines on them, runBlocking blocks one on purpose.">'
    '<rect class="box" x="15" y="24" width="190" height="44" rx="8"/>'
    '<text class="t" x="110" y="51" text-anchor="middle">CompletableFuture</text>'
    '<text class="t-s t-code" x="232" y="38">future.await()</text>'
    '<text class="t-s t-m" x="350" y="38">suspends on a future</text>'
    '<text class="t-s t-code" x="232" y="58">scope.future { }</text>'
    '<text class="t-s t-m" x="350" y="58">returns one to Java</text>'
    '<line class="ln" x1="205" y1="60" x2="262" y2="114"/>'
    '<rect class="box-a" x="250" y="114" width="180" height="60" rx="8"/>'
    '<text class="t" x="340" y="139" text-anchor="middle">coroutines</text>'
    '<text class="t-s t-code" x="340" y="160" text-anchor="middle">suspend fun, Flow</text>'
    '<line class="ln" x1="430" y1="144" x2="488" y2="144"/>'
    '<rect class="box-ok" x="490" y="114" width="175" height="60" rx="8"/>'
    '<text class="t" x="577" y="139" text-anchor="middle">Reactor</text>'
    '<text class="t-s t-code" x="577" y="160" text-anchor="middle">Mono, Flux</text>'
    '<text class="t-s t-code" x="480" y="76">mono { }, asFlux()</text>'
    '<text class="t-s t-m" x="480" y="94">out to Reactor</text>'
    '<text class="t-s t-code" x="480" y="198">awaitSingle(), asFlow()</text>'
    '<text class="t-s t-m" x="480" y="216">in from Reactor</text>'
    '<line class="ln" x1="205" y1="232" x2="262" y2="174"/>'
    '<rect class="box-b" x="15" y="222" width="190" height="44" rx="8"/>'
    '<text class="t" x="110" y="249" text-anchor="middle">virtual threads</text>'
    '<text class="t-s t-code" x="232" y="236">asCoroutineDispatcher()</text>'
    '<text class="t-s t-m" x="410" y="236">run coroutines on them</text>'
    '<text class="t-s t-code" x="232" y="256">runBlocking { }</text>'
    '<text class="t-s t-m" x="350" y="256">block one on purpose</text>'
    '<text class="t-s t-m" x="340" y="290" text-anchor="middle">future { }, await(), mono { } and asFlow() carry cancellation across the bridge</text>'
    '</svg>'
)

TABLE = (
    "| | Virtual threads (JDK 21+) | Kotlin coroutines | Reactor |\n"
    "|---|---|---|---|\n"
    "| Your code looks like | plain blocking Java or Kotlin | sequential `suspend` functions | chains of operators |\n"
    "| Blocking libraries (JDBC, old SDKs) | the natural fit | `withContext(Dispatchers.IO)` or a VT dispatcher | wrap them, move them to `boundedElastic` |\n"
    "| Fan-out with one deadline | `StructuredTaskScope`, preview in JDK 25 | `coroutineScope`, `async`, `withTimeout` | `Mono.zip`, `timeout` |\n"
    "| Cancellation | interrupts, if the code checks them | flows down the job tree to every child | a cancel signal up the chain |\n"
    "| Streams with backpressure | none built in | `Flow` | `Flux` |\n"
    "| Debugging | ordinary stacks and thread dumps | debug mode and coroutine dumps | operator traces, harder to read |\n"
    "| Java callers | native | through `future { }` or `mono { }` | native |\n"
)

L = {
 "id": "co-11",
 "title": "Coroutines meet Java: futures, Reactor, virtual threads",
 "minutes": 35,
 "goal": "By the end you can bridge suspend code to CompletableFuture and Reactor in both directions without losing cancellation, give Java callers a usable face for a Kotlin service, and choose between virtual threads, coroutines and Reactor for a given service.",
 "warmup": {
  "q": "A Kotlin class exposes `fun authorizeAsync(req): CompletableFuture<Decision> = scope.future { authorize(req) }` to Java. A Java caller adds `.orTimeout(800, MILLISECONDS)`, and the timeout fires. What happens to the Kotlin coroutine?",
  "options": [
   "Nothing: a Java timeout can't reach a Kotlin coroutine",
   "It is cancelled, because the future it belongs to completed",
   "It keeps running, and its result is ignored when it arrives",
   "The JVM interrupts the thread the coroutine runs on"
  ],
  "answer": 1,
  "why": "The future returned by `future { }` is tied to its coroutine: the KDoc says the coroutine is cancelled when the future \"is cancelled or otherwise completed\". `orTimeout` completes that same future exceptionally, so the coroutine is cancelled at its next suspension point. Nothing is interrupted, and nothing keeps running."
 },
 "sections": [
  {
   "h": "Bridge CompletableFuture both ways with future { } and await()",
   "body": "Most of your Java code speaks `CompletableFuture`, and kotlinx.coroutines bridges it in both directions with nothing extra on the classpath. The old `kotlinx-coroutines-jdk8` artifact was merged into the core library in 1.7.\n\nFrom a future to a suspend call, use `await()`:\n\n```kotlin\nsuspend fun fraudScore(req: AuthRequest): Int =\n    legacyFraudClient.score(req).await()   // suspends until the future completes; no thread waits\n```\n\n```java\n// Java equivalent: block a thread on the future, or chain on it\nint score = legacyFraudClient.score(req).join();                                  // blocks the caller\nCompletableFuture<Decision> d = legacyFraudClient.score(req).thenApply(this::decide);   // or composes\n```\n\n`await()` suspends without holding a thread. It rethrows the future's exception unwrapped, so you catch the `IOException` itself rather than an `ExecutionException`, and it has a fast path for a future that is already done. It also carries cancellation: if the awaiting coroutine is cancelled, it calls `future.cancel(false)`. That is usually right, because nobody wants the answer any more. When the future is shared, or must finish anyway (a capture that has already gone to the issuer), use `future.asDeferred().await()`, which waits without cancelling it.\n\nFrom a suspend call to a future, use `future { }`:\n\n```kotlin\nclass AuthorizationFacade(private val service: AuthorizationService) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)\n\n    fun authorizeAsync(req: AuthRequest): CompletableFuture<Decision> = scope.future { service.authorize(req) }\n\n    override fun close() = scope.cancel()\n}\n```\n\n```java\n// Java equivalent: the Java caller's side, which is plain CompletableFuture code\nCompletableFuture<String> reply = facade.authorizeAsync(req)\n    .orTimeout(800, TimeUnit.MILLISECONDS)\n    .thenApply(decision -> \"pay-1: \" + decision);\n```\n\n`future { }` is a builder like `async`: it starts a coroutine in the scope and hands its result back as a `CompletableFuture`. The link runs both ways. A Java caller's `cancel(true)`, or an `orTimeout` that fires, completes the future, and that cancels the Kotlin coroutine. Give the facade a scope it owns, as in lesson 3 of this track, so closing the facade cancels everything still in flight. `GlobalScope.future` also compiles, and it leaks in exactly the way lesson 3 described.",
   "figure": {"svg": FIG, "caption": "Each neighbour of the coroutine world has a bridge in and a bridge out, and the async bridges carry cancellation both ways."},
   "try": {
    "title": "Cancel across the bridge",
    "minutes": 4,
    "steps": [
     "Read `FutureBridge.kt`. Predict the three `future cancelled` lines.",
     "Run it.",
     "Run the Java twin. It is plain Java calling the Kotlin `FraudFacade` from the same file, so watch for the `[kotlin]` lines.",
     "In the Java twin, change `orTimeout(50, ...)` to `orTimeout(500, ...)` and run it again. Predict first."
    ],
    "code": tryit("FutureBridge.kt", "FutureBridgeJava.java"),
    "expect": "Case 1 prints `future cancelled: true`: cancelling the coroutine cancelled the Java future it was awaiting. Case 2 prints `false` and the future still completes, because `asDeferred().await()` only waits. Case 3 prints `[kotlin] scoring pay-123 was cancelled`, then `true`. In the Java twin, the combined score is 77, and both the `orTimeout` and the `cancel(true)` produce a `[kotlin] ... was cancelled` line. With a 500 ms timeout the 200 ms score finishes first, so there is no timeout and no cancel line for it."
   },
   "refs": [
    {"title": "future (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html", "kind": "docs"},
    {"title": "await on CompletionStage (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/await.html", "kind": "docs"}
   ]
  },
  {
   "h": "Bridge Reactor with mono { }, awaitSingle and asFlow",
   "body": "Reactor speaks `Mono` and `Flux`, and the `kotlinx-coroutines-reactor` module (on this lab's classpath) bridges them.\n\n```kotlin\nfun quote(req: AuthRequest): Mono<Quote> = mono { quoteSource.quote(req) }      // suspend code as a Mono\nsuspend fun quoteNow(req: AuthRequest): Quote = webClientQuote(req).awaitSingle() // a Mono in suspend code\nfun settlements(): Flow<Batch> = settlementFlux().asFlow()                       // a Flux as a Flow\nfun ticks(): Flux<Double> = fxTicks.asFlux()                                     // a Flow as a Flux\n```\n\n```java\n// Java equivalent: the Reactor side just sees ordinary Mono and Flux values\nMono<Quote> north = quotes.quote(req);                       // built by mono { } in Kotlin\nMono<String> both = Mono.zip(north, quotes.quote(otherReq)).map(t -> t.getT1() + \" | \" + t.getT2());\nFlux<Double> ticks = fx.ticks();                              // a Kotlin Flow through asFlux()\n```\n\n`mono { }` gives a **cold** Mono: the coroutine starts on subscription, once per subscriber, which is the contract every Reactor user expects (lesson 2 of the reactive track). A `null` result completes the Mono empty, and disposing the subscription cancels the coroutine. Its context may not contain a `Job` (\"Mono context cannot contain job in it\"), because the subscription owns the coroutine's life, not a scope. `flux { }` does the same for a stream, with `send` inside.\n\nIn the other direction, `awaitSingle()` waits for exactly one value and throws `NoSuchElementException` for an empty Mono; `awaitSingleOrNull()` returns `null` instead. `Publisher.asFlow()` collects a Flux as a Flow: the Flow's suspension turns into Reactive Streams `request(n)` demand, and cancelling the collector cancels the subscription. `Flow.asFlux()` goes back, and the module's README describes the result as TCK-compliant: it passes the Reactive Streams test kit (TCK), which checks a publisher against the spec's numbered rules.\n\nTwo things need care. Threads first: unless you pass a dispatcher, `mono { }` starts its coroutine on `Dispatchers.Default`, while the Reactor operators around it run wherever their schedulers put them. Then context: Reactor's `Context`, which WebFlux uses for things like trace ids, is visible inside the coroutine as a `ReactorContext` element. MDC thread locals are not, for the reason lesson 4 of this track gave.\n\nQuarkus users will meet Mutiny rather than Reactor. The shapes are the same (`Uni` is a Mono, `Multi` is a Flux), and Mutiny ships its own Kotlin coroutine bridges.",
   "try": {
    "title": "Hand a coroutine to Reactor and back",
    "minutes": 4,
    "steps": [
     "Read `ReactorBridge.kt`. Predict how many `[kotlin] asking north` lines print in part 1.",
     "Run it.",
     "Run the Java twin, which uses the same Kotlin `quoteFor` and `tickFlux` functions from plain Reactor code.",
     "In the Kotlin file, change `awaitSingle()` in part 2 to `awaitSingleOrNull()` and print the result. Predict first."
    ],
    "code": tryit("ReactorBridge.kt", "ReactorBridgeJava.java"),
    "expect": "`[kotlin] asking north` prints twice in part 1, once per `awaitSingle()`, and not when the Mono is built: `mono { }` is cold. Part 2 throws `NoSuchElementException` for the empty Mono, and after your change it prints `null`. Part 3 prints three batches and `[reactor] subscription cancelled`, because `take(3)` stopped the Flow. The Java twin shows the same cold Mono from the Reactor side, plus `defaultIfEmpty` and `Mono.zip` over two Kotlin quotes."
   },
   "refs": [
    {"title": "kotlinx-coroutines-reactor (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/", "kind": "docs"}
   ]
  },
  {
   "h": "Give Java callers a face they can use",
   "body": "Java can see a suspend function, but it can't call it nicely. The compiler adds a `Continuation` parameter and changes the return type to `Object` (lesson 1 of this track showed the bytecode), so from Java the signature looks like this:\n\n```kotlin\nsuspend fun authorize(req: AuthRequest): Decision\n```\n\n```java\n// what Java sees for the same function: a Continuation parameter and an Object result\npublic Object authorize(AuthRequest req, Continuation<? super Decision> $completion)\n```\n\nYou could implement `Continuation` by hand, but you would be rebuilding a coroutine builder, badly. Give Java callers one of three faces instead.\n\n- A `CompletableFuture` method built with `future { }`, as in this lesson's lab. It is the default for Java code that composes asynchronously, such as a Quarkus REST resource that returns a `CompletionStage`.\n- A `Mono` built with `mono { }`, for code that already lives in Reactor.\n- A blocking method that wraps `runBlocking { }`, for Java callers that block anyway: a Temporal activity, a JUnit test, a Kafka listener thread, or any code running on a virtual thread. Blocking a virtual thread is cheap, so `runBlocking` on one is a fair bridge. It is still wrong inside suspend code or on an event-loop thread (lesson 2 of this track).\n\nWhichever you choose, name the faces so the difference shows: `authorize` for Kotlin, `authorizeAsync` or `authorizeBlocking` for Java. Keep the suspend function as the one real implementation and make the others thin wrappers, so the rules for retries and timeouts live in one place. `@JvmOverloads`, `@JvmStatic` and `@JvmName` take care of the rest of the Java-facing surface: default arguments, companion functions and clashing names.\n\nA blocking face needs a timeout of its own. `runBlocking { withTimeout(2.seconds) { authorize(req) } }` gives the Java caller an upper bound, and an interrupt of the calling thread cancels the coroutine and makes `runBlocking` throw `InterruptedException`. That is the bridge from Java's cancellation model to Kotlin's.\n\nThe lab's Java test, `JavaCallerTest.java`, shows what a Java caller ends up writing against a `future { }` face: `orTimeout`, `thenApply` and `get`, with no Kotlin types in sight beyond the data classes.\n\nQuick check: two Java callers block on the issuer through different faces, and each caller's thread is interrupted while the call is in flight. Caller A uses `authorizeBlocking`, the `runBlocking` face. Caller B calls `authorizeAsync(req).get()`. Whose issuer call is cancelled? (Only A's. The interrupt reaches `runBlocking`, which cancels its coroutine. B's interrupt only makes `get()` throw `InterruptedException`. The future is still not complete, so the coroutine behind it keeps running until someone cancels the future or closes the facade.)"
  },
  {
   "h": "Virtual threads, coroutines or Reactor: choosing for a payments team",
   "body": "All three solve the problem the virtual threads track opened with: a request spends most of its time waiting, and a platform thread per waiting request is too expensive. They solve it at different layers. Virtual threads make blocking cheap, so ordinary blocking code scales. Coroutines make waiting explicit with `suspend`, and add structured concurrency, cancellation and Flow. Reactor turns a request into a pipeline of operators with backpressure. The Try it below runs the same three calls each way, and each takes as long as the slowest call.\n\n" + TABLE + "\nHere is what I would do in a team that writes Quarkus services in Kotlin and Java, talks to Oracle over JDBC, consumes Kafka and runs Temporal workflows.\n\n- Start with virtual threads for request handling that is mostly blocking calls. Quarkus has `@RunOnVirtualThread`, JDBC and the Temporal SDK are blocking APIs anyway, and since JDK 24 (JEP 491) `synchronized` no longer pins a virtual thread in most cases, so JDK 25 is a good base. Cap each downstream with a semaphore or a sized pool (lesson 3 of the virtual threads track).\n- Use coroutines in Kotlin code that needs what virtual threads don't give you: fan-out with one deadline, cancellation that reaches every child, Flow pipelines, StateFlow-style shared state. Blocking calls inside still go through `withContext(Dispatchers.IO)` or a virtual-thread dispatcher.\n- Keep Reactor (or Mutiny) where a reactive stack already exists, or where you stream with backpressure end to end. Don't start a new, blocking-heavy service on it.\n\nMixing them is normal, and cheap with the bridges from this lesson. What to avoid is several models in one call path for no reason: a coroutine that calls `runBlocking`, which calls a `Mono`, which blocks on JDBC. Pick one model per component, and convert at its edges.",
   "try": {
    "title": "One request, three ways",
    "minutes": 4,
    "steps": [
     "Read `ThreeWays.kt` and its Java twin. Each runs the same three calls (100, 300 and 200 ms) at once. Predict every time.",
     "Run both.",
     "In `ThreeWays.kt`, wrap the body of `detailsWithCoroutines` in `withTimeout(250) { ... }` and run it again. What happens to the calls still in flight?"
    ],
    "code": tryit("ThreeWays.kt", "ThreeWaysJava.java"),
    "expect": "Every version takes about 300 ms: the coroutines, the blocking code on a virtual-thread dispatcher, the blocking code on `Dispatchers.IO`, the plain virtual threads and the Reactor `Mono.zip`. With `withTimeout(250)`, the program fails with `TimeoutCancellationException` at about 250 ms, and the ledger and risk calls still in flight are cancelled with it. Doing that in the Java virtual-thread version would take extra code to cancel the futures yourself."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444", "kind": "read"},
    {"title": "Reactor bridges: kotlinx-coroutines-reactor README", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/master/reactive/kotlinx-coroutines-reactor/README.md", "kind": "read"}
   ]
  }
 ],
 "analogy": "Think of three ways to run a busy restaurant. Virtual threads hire a cheap waiter for every table, and each one simply stands there while the kitchen cooks, which is fine because standing costs almost nothing. Coroutines have a few waiters who leave a numbered ticket at each table and come back when the order is ready; they also know which tickets belong to which party, so when a party leaves they tear up all its tickets at once. Reactor runs the room as a conveyor: orders move through fixed stations, and the conveyor only moves as fast as the last station can take plates. The bridges are the pass between the kitchen and the floor, where a ticket can become a plate and back. The analogy breaks on cost: in a real restaurant the conveyor is the expensive option to install, while in code the expensive part of Reactor is the reading, debugging and changing of the pipeline afterwards.",
 "in_your_world": "In a mixed Kotlin and Java Quarkus codebase, the Kotlin services keep their logic in `suspend fun`s, and each one gets a thin Java face: a `CompletionStage` method built with `future { }` for Java resources and the Kafka listener code, and a blocking `runBlocking` method with its own timeout for Temporal activities, which are blocking by design. Java fraud and limits clients that return `CompletableFuture` are consumed with `await()`, so cancelling a payment request also cancels the score request. Where a downstream library is reactive, `awaitSingle()` and `asFlow()` bring it in, and `mono { }` serves a reactive caller. Blocking-heavy Java services, such as a ledger service that is mostly JDBC, move to virtual threads with `@RunOnVirtualThread` on JDK 25, with a semaphore in front of Oracle's connection pool.",
 "mistake": "The most common mistake is bridging with blocking calls: `runBlocking { }` inside `CompletableFuture.supplyAsync` to give Java a future, or `future.get()` (even inside `withContext(Dispatchers.IO)`) to use a Java future from a coroutine. Both work in a demo, so they ship. Under load, each in-flight call pins a pool thread, and cancellation stops at the bridge: a Java caller's `cancel(true)` doesn't reach the coroutine, and a cancelled coroutine leaves the Java future running. The fix is the purpose-built bridges, which suspend instead of block and carry cancellation both ways: `scope.future { }` with a scope you own, `future.await()`, `mono { }` and `awaitSingle()`.",
 "compare": {
  "title": "One fan-out with a deadline: virtual threads vs coroutines",
  "java": {"title": "PaymentDetails.java", "src": "PaymentDetails details(String id) throws Exception {\n    try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {\n        Future<Account> account = vt.submit(() -> accounts.load(id));        // 1. three blocking calls,\n        Future<List<Entry>> ledger = vt.submit(() -> ledgerClient.recent(id)); //    one virtual thread each\n        Future<Risk> risk = vt.submit(() -> riskClient.flags(id));\n        long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(800);\n        try {\n            return new PaymentDetails(                                       // 2. one shared deadline\n                account.get(remaining(deadline), TimeUnit.NANOSECONDS),\n                ledger.get(remaining(deadline), TimeUnit.NANOSECONDS),\n                risk.get(remaining(deadline), TimeUnit.NANOSECONDS));\n        } catch (TimeoutException | ExecutionException e) {\n            account.cancel(true); ledger.cancel(true); risk.cancel(true);   // 3. cancel by hand\n            throw e;\n        }\n    }   // close() waits for every task\n}"},
  "kotlin": {"title": "PaymentDetails.kt", "src": "suspend fun details(id: String): PaymentDetails = withTimeout(800) {   // 2. one shared deadline\n    coroutineScope {\n        val account = async { accounts.load(id) }                     // 1. three suspending calls,\n        val ledger = async { ledgerClient.recent(id) }                //    one coroutine each\n        val risk = async { riskClient.flags(id) }\n        PaymentDetails(account.await(), ledger.await(), risk.await())\n    }   // 3. a timeout or a failure cancels the other two automatically\n}"},
  "note": "Both take as long as the slowest call, and both are cheap: a virtual thread or a coroutine per call. The difference is how much of the structure you write yourself. In Java with virtual threads, the clients can stay blocking, which is the big win, but the shared deadline, the cancel-the-siblings-on-failure step and the cleanup are your code. JDK 25's `StructuredTaskScope` covers that, but it is still a preview API. In Kotlin, the deadline is `withTimeout`, the siblings are cancelled by `coroutineScope`, and the clients must suspend (or be wrapped in `withContext(Dispatchers.IO)` or a virtual-thread dispatcher). Pick the model that matches your clients: blocking clients favour virtual threads, suspending clients and complex fan-out favour coroutines."
 },
 "worked": {
  "title": "Give a Java Temporal activity the Kotlin authorization service",
  "steps": [
   {"say": "The authorization service is Kotlin, and its core is a suspend function with retries and timeouts. A Temporal activity written in Java must call it, and Temporal activities are blocking code. The activity can't call the suspend function directly.",
    "code": "class AuthorizationService(private val issuer: IssuerClient) {\n    suspend fun authorize(req: AuthRequest): Decision =\n        retryWithBackoff(times = 3, initialDelay = 200.milliseconds, maxDelay = 2.seconds) {\n            issuer.authorize(req)\n        }\n}", "lang": "kotlin",
    "alt_code": "// what the Java activity sees: a Continuation parameter it can't sensibly supply\npublic final class AuthorizationService {\n    public final Object authorize(AuthRequest req, Continuation<? super Decision> $completion) { /* ... */ }\n}", "alt_lang": "java"},
   {"say": "Add Java faces in a small Kotlin facade with its own scope. One returns a future, for Java code that composes; one blocks with its own timeout, for callers that block anyway.",
    "code": "class AuthorizationJavaApi(private val service: AuthorizationService) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)\n\n    // 1. for Java code that composes futures\n    fun authorizeAsync(req: AuthRequest): CompletableFuture<Decision> = scope.future { service.authorize(req) }\n\n    // 2. for callers that block anyway, with its own upper bound\n    fun authorizeBlocking(req: AuthRequest): Decision = runBlocking { withTimeout(10.seconds) { service.authorize(req) } }\n\n    override fun close() = scope.cancel()\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same facade, if the service were a Java class returning futures\nfinal class AuthorizationJavaApi implements AutoCloseable {\n    private final AuthorizationService service;\n    AuthorizationJavaApi(AuthorizationService service) { this.service = service; }\n\n    // 1. for Java code that composes futures\n    CompletableFuture<Decision> authorizeAsync(AuthRequest req) { return service.authorizeAsync(req); }\n\n    // 2. for callers that block anyway, with its own upper bound\n    Decision authorizeBlocking(AuthRequest req) throws Exception {\n        return service.authorizeAsync(req).get(10, TimeUnit.SECONDS);\n    }\n\n    @Override public void close() { }\n}", "alt_lang": "java"},
   {"say": "The activity uses the future face, so it can cancel the Kotlin work when Temporal cancels the activity. Temporal reports a cancel through the heartbeat, which throws.",
    "code": "// the activity is Java; this is the Kotlin side it relies on: cancel(true) reaches the coroutine\nval f = api.authorizeAsync(req)\nf.cancel(true)   // 3. cancels the coroutine inside AuthorizationService, retries included", "lang": "kotlin",
    "alt_code": "public Decision authorize(AuthRequest req) {\n    CompletableFuture<Decision> f = api.authorizeAsync(req);\n    try {\n        while (true) {\n            try { return f.get(1, TimeUnit.SECONDS); }\n            catch (TimeoutException stillWaiting) { Activity.getExecutionContext().heartbeat(null); }   // 3. throws if cancelled\n        }\n    } catch (ActivityCompletionException cancelled) {\n        f.cancel(true);    // stops the Kotlin coroutine and its retries\n        throw cancelled;\n    } catch (InterruptedException | ExecutionException e) {\n        throw Activity.wrap(e);\n    }\n}", "alt_lang": "java"},
   {"say": "A Reactor-based caller elsewhere gets its own face from the same function, and the retry rules still live in one place.",
    "code": "// 4. a cold Mono for reactive callers\nfun authorizeMono(req: AuthRequest): Mono<Decision> = mono { service.authorize(req) }", "lang": "kotlin",
    "alt_code": "// 4. the reactive caller's side\nMono<Decision> decision = api.authorizeMono(req)\n    .timeout(Duration.ofSeconds(10))\n    .onErrorReturn(Decision.DECLINED);", "alt_lang": "java"},
   {"say": "Self-check: why not implement `authorizeAsync` as `CompletableFuture.supplyAsync { runBlocking { service.authorize(req) } }`? (It blocks a common-pool thread for every call, the future has no link to the coroutine so `cancel(true)` stops nothing, and the work belongs to no scope, so `close()` can't stop it. That is the bug in this lesson's lab.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Three bridges between Kotlin and Java",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/InteropModel.kt", f"{lab}/main/{P}/AuthorizationFacade.kt", f"{lab}/main/{P}/FraudScore.kt", f"{lab}/main/{P}/ReactiveQuotes.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l11.*'",
  "steps": [
   "Run the tests. Five of ten fail. One test, `JavaCallerTest.java`, is written in Java, to show what a Java caller of the facade writes.",
   "In `AuthorizationFacade.kt`, give the class a `CoroutineScope(SupervisorJob() + dispatcher)`, return `scope.future { authorize(req) }` from `authorizeAsync`, and cancel the scope in `close`.",
   "In `FraudScore.kt`, replace the blocking `get()` with `score(req).await()` (import `kotlinx.coroutines.future.await`).",
   "In `ReactiveQuotes.kt`, return `mono { source.quote(req) }` (import `kotlinx.coroutines.reactor.mono`).",
   "Run the tests until all ten pass."
  ],
  "hints": [
   "`future` is an extension on `CoroutineScope` in `kotlinx.coroutines.future`. It is in the core library; no extra artifact is needed.",
   "A coroutine cancelled through `close()` completes its future with a `CancellationException`, which is what a Java caller sees from `get()`.",
   "`mono { }` returns `Mono<T>` from a block that returns `T?`: a `null` completes the Mono empty, so the \"nobody quotes\" test needs no special case.",
   "The stubs' tests wait at most a few seconds each, so a stub never hangs the build. On the solution they finish in milliseconds."
  ],
  "done_when": "All ten tests in `JavaInteropTest` and `JavaCallerTest` pass."
 },
 "drill": {
  "title": "Three bridges from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `class LimitsJavaApi(private val limits: LimitsService)` where `LimitsService` has `suspend fun dailyLimit(merchantId: String): Long`. Give it `fun dailyLimitAsync(merchantId: String): CompletableFuture<Long>` for Java and `fun dailyLimitMono(merchantId: String): Mono<Long>` for Reactor, both cancellable, and a `close()`. Then write `suspend fun MerchantClient.loadAwait(id: String): Merchant` for a Java client whose `load(id)` returns `CompletableFuture<Merchant>`.",
  "answer": {"lang": "kotlin", "src": "class LimitsJavaApi(private val limits: LimitsService) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)\n\n    fun dailyLimitAsync(merchantId: String): CompletableFuture<Long> =\n        scope.future { limits.dailyLimit(merchantId) }\n\n    fun dailyLimitMono(merchantId: String): Mono<Long> =\n        mono { limits.dailyLimit(merchantId) }\n\n    override fun close() = scope.cancel()\n}\n\nsuspend fun MerchantClient.loadAwait(id: String): Merchant = load(id).await()",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: the Java and Reactor callers of those faces\nclass LimitsCaller {\n    private final LimitsJavaApi api;\n    LimitsCaller(LimitsJavaApi api) { this.api = api; }\n\n    long dailyLimitBlocking(String merchantId) throws Exception {\n        return api.dailyLimitAsync(merchantId).get(2, TimeUnit.SECONDS);   // blocks this thread: fine on a virtual thread\n    }\n\n    Mono<String> describe(String merchantId) {\n        return api.dailyLimitMono(merchantId).map(cents -> merchantId + \": \" + cents);   // cold, cancellable\n    }\n}"}}
 },
 "recap": [
  "`future.await()` suspends on a `CompletableFuture`, unwraps its exception, and cancels the future if the coroutine is cancelled; `asDeferred().await()` waits without cancelling it.",
  "`scope.future { }` gives Java a `CompletableFuture` for suspend code. Cancelling or completing the future cancels the coroutine, and closing the scope cancels everything in flight.",
  "`mono { }` is a cold Mono (once per subscriber, empty on `null`, cancelled on dispose). `awaitSingle()`, `asFlow()` and `asFlux()` cover the other directions.",
  "Java can't call a suspend function sensibly. Give it a future face, a Mono face, or a blocking `runBlocking` face with its own timeout for callers that block anyway.",
  "Virtual threads make blocking code cheap, coroutines add structure, cancellation and Flow, and Reactor gives operator pipelines with backpressure.",
  "Pick one model per component and convert at its edges with the purpose-built bridges, never with `runBlocking` or `get()` in the middle of a call path."
 ],
 "quiz": [
  {"q": "A Java caller holds `f = facade.authorizeAsync(req)`, where `authorizeAsync` is `scope.future { authorize(req) }`, and calls `f.cancel(true)`. What happens to the Kotlin side?",
   "options": ["Nothing: `cancel(true)` only interrupts Java threads", "The coroutine is cancelled at its next suspension point", "The coroutine finishes, and its result is thrown away", "The whole scope is cancelled, with every other authorization"],
   "answer": 1,
   "why": "The future from `future { }` is tied to its coroutine, and cancelling or completing the future cancels it. Only that coroutine is affected: the scope and its other children carry on, especially with a `SupervisorJob`."},
  {"q": "A coroutine does `val s = fraudClient.score(req).await()` and is cancelled while it waits. What happens to the Java future?",
   "options": ["It is cancelled with `cancel(false)`, because nobody wants the answer any more", "It keeps running, and its result is discarded", "It is completed with `null`", "`await()` blocks until the future finishes, then throws"],
   "answer": 0,
   "why": "`await()` cancels the future when the awaiting coroutine is cancelled. If the future must finish anyway (it is shared, or the work is already committed), use `future.asDeferred().await()`, which waits without cancelling."},
  {"q": "`val q: Mono<Quote> = mono { quoteSource.quote(req) }` is built, and then two different callers subscribe to `q`. How many times does `quoteSource.quote` run?",
   "options": ["Once, when `mono { }` is called", "Once, at the first subscription; the second subscriber gets the cached value", "Twice: the Mono is cold, so each subscription runs the coroutine", "Never, unless `block()` is called"],
   "answer": 2,
   "why": "`mono { }` starts the coroutine on subscription, once per subscriber, like any cold Mono. Use `.cache()` on the Mono if you really want one call shared."},
  {"q": "A Java service handles 2,000 concurrent requests. Each one makes three blocking JDBC queries and one blocking HTTP call, and the team writes Java. Which model fits best?",
   "options": ["Rewrite it with Reactor, to avoid blocking", "Rewrite it in Kotlin with coroutines", "A platform thread pool of 2,000 threads", "Virtual threads, with a semaphore in front of the connection pool"],
   "answer": 3,
   "why": "The code is blocking and Java, which is exactly what virtual threads make cheap: one per request, with no rewrite. A semaphore keeps the database pool from being overrun. Reactor and coroutines would mean rewriting every client for little gain, and 2,000 platform threads cost a lot of memory."},
  {"q": "From the virtual threads track: on JDK 21, a virtual thread blocks on a socket read while inside a `synchronized` block. What happens to its carrier thread?",
   "options": ["It is released, as with any blocking call", "It is pinned: it stays blocked with the virtual thread until the read returns", "The JVM throws `IllegalStateException`", "The virtual thread is moved to a new carrier"],
   "answer": 1,
   "why": "On JDK 21 to 23, blocking while holding a monitor pins the virtual thread to its carrier, so the carrier blocks too. JEP 491 in JDK 24 removed most of that pinning, which is one reason to run virtual-thread services on JDK 25.",
   "from": "vt-04"}
 ],
 "flashcards": [
  {"front": "How do you wait for a `CompletableFuture` inside a coroutine without blocking?", "back": "`future.await()` from `kotlinx.coroutines.future`. It suspends, unwraps the exception, and cancels the future if the coroutine is cancelled."},
  {"front": "How do you await a `CompletableFuture` without cancelling it when the coroutine is cancelled?", "back": "`future.asDeferred().await()`."},
  {"front": "How do you return suspend code to Java as a `CompletableFuture`?", "back": "`scope.future { suspendCall() }`, with a scope the class owns. Cancelling or completing the future cancels the coroutine."},
  {"front": "When does the coroutine inside `mono { }` run?", "back": "On each subscription. The Mono is cold, a `null` result completes it empty, and disposing the subscription cancels the coroutine."},
  {"front": "What does `awaitSingle()` do on an empty Mono?", "back": "It throws `NoSuchElementException`. `awaitSingleOrNull()` returns `null` instead."},
  {"front": "What does Java see for `suspend fun authorize(req: AuthRequest): Decision`?", "back": "`Object authorize(AuthRequest req, Continuation<? super Decision> completion)`: give Java a future, Mono or blocking face instead."},
  {"front": "Virtual threads or coroutines for a blocking JDBC-heavy Java service?", "back": "Virtual threads: they make the existing blocking code cheap without a rewrite. Coroutines pay off for structured fan-out, cancellation and Flow in Kotlin."}
 ],
 "terms": [
  {"term": "future { }", "plain": "A coroutine builder that returns the coroutine's result as a CompletableFuture."},
  {"term": "await()", "plain": "Suspends until a CompletableFuture completes, without blocking a thread."},
  {"term": "mono { }", "plain": "Turns suspend code into a cold Reactor Mono that runs once per subscription."},
  {"term": "awaitSingle()", "plain": "Suspends until a Mono emits its one value; throws if it completes empty."},
  {"term": "asFlow / asFlux", "plain": "Convert a Reactive Streams Publisher to a Flow, and a Flow to a Flux."},
  {"term": "Java face", "plain": "A thin wrapper that exposes a suspend function to Java as a future, a Mono or a blocking call."}
 ],
 "explain_back": {
  "prompt": "Your team lead asks: \"We have Kotlin and Java services on Quarkus, Oracle over JDBC, Kafka and Temporal. Should new code use virtual threads, coroutines or Reactor?\" Give your answer and the reasons.",
  "answer": "For most request handling I'd use virtual threads: our clients are blocking (JDBC, the Temporal SDK, several vendor SDKs), Quarkus can run endpoints on virtual threads, and on JDK 25 the old synchronized pinning problem is mostly gone. We keep plain blocking code and cap each downstream with a semaphore. In Kotlin code where we need more than cheap blocking, like a fan-out with one deadline, cancellation that reaches every child, or Flow pipelines and shared state, I'd use coroutines, and push blocking calls inside them onto Dispatchers.IO or a virtual-thread dispatcher. Reactor or Mutiny stays where it already is or where we genuinely stream with backpressure; I wouldn't start a new blocking-heavy service on it. Where the models meet, we convert at the edge with future {}, await(), mono {} and awaitSingle(), which keep cancellation working, and we never stack runBlocking and blocking get() calls in one call path."
 },
 "deeper": {
  "minutes": 10,
  "body": "kotlinx.coroutines 1.11 has no built-in virtual-thread dispatcher. `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()` is the supported route, and it gives every dispatch a fresh virtual thread. That makes it a good home for blocking calls inside coroutines, with two cautions. A coroutine blocked inside it still ignores cancellation unless the call is wrapped in `runInterruptible`, which interrupts the virtual thread. And the coroutine scheduler's habit of keeping a coroutine on one worker is lost, so code that relies on thread-local caches gets a new thread every time it resumes.\n\n`CompletionStage.await()` works for any `CompletionStage`, not just `CompletableFuture`, and `Deferred.asCompletableFuture()` goes the other way for a coroutine you already started with `async`. On the Reactor side, `Deferred.asMono()` and `Job.asMono()` give hot Monos for work that is already running, and `Scheduler.asCoroutineDispatcher()` lets coroutines run on a Reactor scheduler, which keeps thread usage in one place in a WebFlux service.\n\nThe structured-concurrency story differs most across the three. Coroutines enforce it by default. Virtual threads get it through `StructuredTaskScope`, a preview API in JDK 25 (JEP 505) whose shape changed between previews. Reactor has no tree of tasks at all, only operator chains that cancel upstream. When you bridge, the tree ends at the bridge: a `future { }` coroutine belongs to the facade's scope, not to the Java caller, which is exactly why the facade must own and close that scope."
 },
 "sources": [
  {"title": "future (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html"},
  {"title": "kotlinx-coroutines-reactor (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"}
 ]
}
out = ROOT / "content/lessons/co-11.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
