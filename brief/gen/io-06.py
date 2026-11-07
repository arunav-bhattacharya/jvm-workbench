import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l06"
K = "kotlin/workbench/nio/l06"
read = lambda p: (ROOT / p).read_text()

rows = [
    ("@RunOnVirtualThread?", "new virtual thread", "box-ok"),
    ("explicit @Blocking or @NonBlocking?", "worker / IO thread", "box"),
    ("@Transactional? (3.40 docs)", "worker thread", "box-a"),
    ("returns Uni, Multi, CompletionStage, Publisher, suspend?", "IO thread", "box-b"),
    ("anything else: a plain return value", "worker thread", "box-a"),
]
parts = []
for i, (q, outcome, cls) in enumerate(rows):
    y = 64 + i * 48
    parts.append(f'<rect class="box" x="20" y="{y}" width="410" height="34" rx="8"/>')
    parts.append(f'<text class="t-s" x="225" y="{y + 22}" text-anchor="middle">{q}</text>')
    parts.append(f'<line class="ln" x1="430" y1="{y + 17}" x2="466" y2="{y + 17}" marker-end="url(#arr)"/>')
    if i < 4:
        parts.append(f'<text class="t-s t-m" x="448" y="{y + 11}" text-anchor="middle">yes</text>')
    parts.append(f'<rect class="{cls}" x="470" y="{y}" width="190" height="34" rx="8"/>')
    parts.append(f'<text class="t-s" x="565" y="{y + 22}" text-anchor="middle">{outcome}</text>')
    if i < 4:
        parts.append(f'<line class="ln-d" x1="50" y1="{y + 34}" x2="50" y2="{y + 44}" marker-end="url(#arr)"/>')
        parts.append(f'<text class="t-s t-m" x="70" y="{y + 44}">no</text>')
FIG = (
    '<svg viewBox="0 0 680 310" role="img" aria-label="How Quarkus REST 3.40 picks the thread for an endpoint: '
    'the request arrives on an IO thread, then RunOnVirtualThread, explicit Blocking or NonBlocking, Transactional '
    'and finally the return type decide between a virtual thread, a worker thread and the IO thread">'
    '<rect class="box-b" x="20" y="10" width="640" height="34" rx="8"/>'
    '<text class="t-s" x="340" y="32" text-anchor="middle">every request arrives on an IO thread (a Vert.x event loop), then, first match wins:</text>'
    + "".join(parts) + '</svg>'
)

rules_kotlin = """object DispatchRules {
    private val nonBlockingReturns = setOf(
        ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND)

    fun target(e: Endpoint): Target = when {
        Marker.RUN_ON_VIRTUAL_THREAD in e.markers -> Target.VIRTUAL_THREAD
        Marker.BLOCKING in e.markers -> Target.WORKER
        Marker.NON_BLOCKING in e.markers -> Target.IO_THREAD
        Marker.TRANSACTIONAL in e.markers -> Target.WORKER
        e.returns in nonBlockingReturns -> Target.IO_THREAD
        else -> Target.WORKER
    }
}"""
rules_java = """final class DispatchRules {
    private static final Set<ReturnKind> NON_BLOCKING_RETURNS = EnumSet.of(
            ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND);

    static Target target(Endpoint e) {
        Set<Marker> m = e.markers();
        if (m.contains(Marker.RUN_ON_VIRTUAL_THREAD)) return Target.VIRTUAL_THREAD;
        if (m.contains(Marker.BLOCKING)) return Target.WORKER;
        if (m.contains(Marker.NON_BLOCKING)) return Target.IO_THREAD;
        if (m.contains(Marker.TRANSACTIONAL)) return Target.WORKER;
        return NON_BLOCKING_RETURNS.contains(e.returns()) ? Target.IO_THREAD : Target.WORKER;
    }
}"""

L = {
 "id": "io-06",
 "title": "Quarkus on Vert.x: IO threads, workers and virtual threads",
 "minutes": 36,
 "goal": "By the end you can predict which thread runs a Quarkus REST endpoint from its signature and annotations, explain what happens when an IO thread blocks, and choose between a worker thread, the IO thread and @RunOnVirtualThread for a payment endpoint.",
 "warmup": {
  "q": "A Quarkus 3.40 endpoint returns `Uni<Payment>` and builds it with `Uni.createFrom().item(repository.findById(id))`, where `findById` is a JDBC call. Which thread runs that JDBC call?",
  "options": [
   "A worker thread, because Quarkus sees the JDBC call",
   "A Vert.x event loop (IO thread), because the method returns `Uni`",
   "A virtual thread, because Quarkus 3.40 runs everything on virtual threads",
   "The Mutiny scheduler, because `Uni` is lazy"
  ],
  "answer": 1,
  "why": "Quarkus REST picks the thread from the signature: `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` mean \"non-blocking\", so the method runs on the IO thread. `findById` is evaluated while the method builds the `Uni`, so the JDBC call blocks an event loop. Quarkus can't see inside your method; add `@Blocking` or return a plain value."
 },
 "sections": [
  {
   "h": "In Quarkus REST, the return type picks the thread",
   "body": """Every HTTP request to a Quarkus service is read on a Vert.x event loop, which Quarkus calls an IO thread. The Quarkus reactive architecture guide describes what happens next: the extension that dispatches the request decides whether to call your code right there on the IO thread, which avoids a thread switch, or on a worker thread, a thread from a normal bounded pool. For Quarkus REST (formerly RESTEasy Reactive) the decision comes from your method's signature. Everything in this lesson is pinned to Quarkus 3.40.

A method that returns `Uni`, `Multi`, `CompletionStage` or a Reactive Streams `Publisher`, or a Kotlin `suspend` function, counts as non-blocking and runs on the IO thread. Anything else, such as a method that returns a `Balance` directly, runs on a worker thread.

```java
@Path("/balances")
public class BalanceResource {
    @Inject LedgerRepository ledger;              // JDBC, blocking
    @Inject ReactiveLedger reactiveLedger;        // reactive SQL client, returns Uni

    @GET @Path("/{account}")
    public Balance balance(@PathParam("account") String account) {   // plain value: worker thread
        return ledger.find(account);
    }

    @GET @Path("/{account}/live")
    public Uni<Balance> live(@PathParam("account") String account) { // Uni: IO thread
        return reactiveLedger.find(account);
    }
}
```

```kotlin
@Path("/balances")
class BalanceResource(
    private val ledger: LedgerRepository,          // JDBC, blocking
    private val reactiveLedger: ReactiveLedger,    // reactive SQL client, returns Uni
) {
    @GET @Path("/{account}")
    fun balance(@PathParam("account") account: String): Balance =      // plain value: worker thread
        ledger.find(account)

    @GET @Path("/{account}/live")
    suspend fun live(@PathParam("account") account: String): Balance = // suspend: IO thread
        reactiveLedger.find(account).awaitSuspending()
}
```

Read the rule as a promise you make. A `Uni` return type tells Quarkus \"this method won't block\", so Quarkus skips the hop to a worker and saves its cost. Break the promise with a JDBC call inside and you are back in lesson 5: every other connection on that event loop waits.

The worker pool is a bounded pool like the ones in the executors track. Quarkus runs blocking endpoints on its own executor, whose size `quarkus.thread-pool.max-threads` defaults to the larger of 8 × CPUs and 200 in 3.40: 200 threads on a 4-core machine.""",
   "figure": {"svg": FIG, "caption": "Quarkus REST 3.40's dispatch decision, as this lesson's lab models it. The first rule that matches picks the thread."},
   "try": {
    "title": "Predict the thread",
    "minutes": 3,
    "steps": [
     "Without running anything, write down the thread for each Quarkus 3.40 endpoint: (a) `public List<Payment> recent()`, (b) `public Uni<Payment> byId(...)`, (c) `public CompletionStage<Receipt> refund(...)`, (d) Kotlin `suspend fun capture(id: String): Receipt`, (e) `public Multi<Payment> stream()`.",
     "Open the lab test `DispatcherTest` and find the test that encodes the same rules. Check your answers against it."
    ],
    "expect": "(a) runs on a worker thread; (b), (c), (d) and (e) run on the IO thread. The one people get wrong is (d): a Kotlin `suspend` function is treated as non-blocking, so a blocking JDBC call inside it blocks an event loop, exactly like one inside a `Uni` method."
   },
   "refs": [
    {"title": "Quarkus REST guide at 3.40.1: execution model, blocking, non-blocking", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "@Blocking, @NonBlocking, and the @Transactional disagreement",
   "body": """When the signature guesses wrong, you annotate. `@Blocking` (from `io.smallrye.common.annotation`) sends a method to a worker even if it returns `Uni`. `@NonBlocking` keeps a method on the IO thread even if it returns a plain value. Both work on a method, on a class, or on your `jakarta.ws.rs.core.Application` subclass to change the default for the whole application. Filters follow their endpoint: under `@Blocking` they run on the worker, otherwise on the IO thread.

```java
@Blocking                                          // returns Uni, but the body blocks: use a worker
@GET @Path("/{account}/legacy")
public Uni<Balance> legacy(@PathParam("account") String account) {
    return Uni.createFrom().item(ledger.find(account));   // the JDBC call runs right here
}
```

```kotlin
@Blocking                                          // returns Uni, but the body blocks: use a worker
@GET @Path("/{account}/legacy")
fun legacy(@PathParam("account") account: String): Uni<Balance> =
    Uni.createFrom().item(ledger.find(account))    // the JDBC call runs right here
```

`@Transactional` is where the Quarkus documentation disagrees with itself. The Quarkus REST guide tagged 3.40.1 says a method or class annotated with `jakarta.transaction.Transactional` \"will also be treated as a blocking method\", because JTA is a blocking technology, and that an explicit `@Blocking` or `@NonBlocking` overrides this. The same guide on Quarkus's main branch says the opposite: since 3.35, `@Transactional` no longer makes a method blocking, the return type decides, and a `Uni` method that uses JTA needs an explicit `@Blocking`. The research for this track could not find the code that settles which is right for 3.40.

So don't depend on either reading. Put `@Blocking` on every endpoint that uses JTA and doesn't return a plain value. It costs nothing when the rule already applies and saves you when it doesn't. When it doesn't, the failure is loud. Before it starts a transaction, Narayana's interceptor in 3.40.1 checks whether blocking is allowed and, on an IO thread, throws `BlockingOperationNotAllowedException`: \"@Transactional cannot start a JTA transaction within a reactive pipeline. If the annotated method is intended to be blocking, ensure it is executed on a worker thread, for example by annotating it with @Blocking. ...\"""",
   "try": {
    "title": "Read the rules both ways",
    "minutes": 3,
    "steps": [
     "Take `@Transactional public Uni<Void> post(Payment p)`. Where does it run under the 3.40.1 docs? Under the main-branch docs? What happens to the JTA interceptor in each case?",
     "Now `@Transactional @NonBlocking public Uni<Void> post(Payment p)`. Where does it run, and what happens?",
     "Check the first answer against the lab test that mentions `@Transactional`."
    ],
    "expect": "Under the 3.40.1 docs the first method runs on a worker and the transaction starts normally. Under the main-branch rule it runs on the IO thread, and the interceptor throws `BlockingOperationNotAllowedException` before your code runs. The second method runs on the IO thread under both readings, because an explicit annotation wins, so it always throws. In every case `@Blocking` would have given the same, working result, which is why it belongs on the method."
   }
  },
  {
   "h": "What happens when you block an IO thread in Quarkus",
   "body": """Quarkus configures its Vert.x instance differently from plain Vert.x, and the differences change what your logs show.

| Setting | Plain Vert.x 5 | Quarkus 3.40 |
|---|---|---|
| event loops | 2 × CPUs | CPUs, at least 2, at most one per 10 MB of max heap |
| warn about a blocked loop after | 2 s | 2 s (`quarkus.vertx.max-event-loop-execute-time`) |
| include the stack trace after | 5 s | 2 s (`quarkus.vertx.warning-exception-time`) |
| threads for blocking work | worker pool: 20 | executor: `quarkus.thread-pool.max-threads`, max(8 × CPUs, 200) |

A comment in Quarkus's source explains the event-loop default: twice the number of cores used to be the recommendation, but matching cores 1:1 seemed more reasonable and saves memory. On a 4-core laptop that means 4 event loops instead of 8, so one blocked loop stalls a quarter of your connections.

The stack-trace setting is the friendly difference. This section's demo builds a plain Vert.x instance with Quarkus's settings and blocks an event loop for 3 seconds. The first warning already carries the stack:

```text
plain Vert.x default event loops: 8, Quarkus 3.40 default: max(2, min(3420 MB / 10, 4 cpus)) = 4
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 2770 ms, time limit is 2000 ms
io.vertx.core.VertxException: Thread blocked
	at java.base/java.lang.Thread.sleep(Thread.java:509)
	at workbench.nio.l06.QuarkusLikeLoopDemo.lambda$main$0(QuarkusLikeLoopDemo.java:30)
```

In a real Quarkus service the line goes through Quarkus's own logging, so the prefix differs, but the message and the stack are Vert.x's. The first frame below `Thread.sleep` is your endpoint.

Some Quarkus APIs don't wait for the checker. They test where they run and fail at once with `BlockingOperationNotAllowedException`, which extends `IllegalStateException`: the JTA interceptor from the previous section, and reading a request body as a blocking stream, which fails with \"Attempting a blocking read on io thread\". Go one level down and the test is simple. Quarkus asks its IO-thread detectors whether the current thread is an IO thread, and the Vert.x detector in 3.40.1 returns `Context.isOnEventLoopThread()`, the same call this lesson's lab uses. A fast exception in a test is a better way to find a blocking call than a slow event loop in production.""",
   "try": {
    "title": "Block an IO thread with Quarkus settings",
    "minutes": 3,
    "steps": [
     "Open `QuarkusLikeLoopDemo.java` (or the Kotlin twin). Predict the event-loop count it computes for your machine.",
     "Predict whether the first blocked-thread warning comes with a stack trace. Run it.",
     "Run it again with `-Pargs=1500`. How many warnings now, and why?"
    ],
    "code": {"lang": "java", "title": "QuarkusLikeLoopDemo.java", "src": read(f"{lab}/demo/{P}/QuarkusLikeLoopDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.QuarkusLikeLoopDemo",
             "file": f"{lab}/demo/{P}/QuarkusLikeLoopDemo.java",
             "alt": {"lang": "kotlin", "title": "QuarkusLikeLoopDemo.kt", "src": read(f"{lab}/demo/{K}/QuarkusLikeLoopDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.QuarkusLikeLoopDemoKt",
                     "file": f"{lab}/demo/{K}/QuarkusLikeLoopDemo.kt"}},
    "expect": "With a few gigabytes of max heap the memory cap doesn't bite, so the count equals your CPUs (4 here, against Vert.x's 8). The first warning, between 2 and 3 seconds in, already includes `VertxException: Thread blocked` and the stack, because the warning-exception time is 2 s. With a 1,500 ms block there is no warning at all: the checker only reports a task that has run longer than 2 seconds, so short blocks stay invisible in the logs."
   }
  },
  {
   "h": "@RunOnVirtualThread: blocking code without the worker-pool cap",
   "body": """`@RunOnVirtualThread` tells Quarkus to run the method on a new virtual thread, instead of the IO thread or a worker. The code stays blocking-style, but waiting no longer holds a pooled thread: a JDBC call, or `uni.await().atMost(...)` on a Mutiny `Uni`, parks the virtual thread, and the JDK wakes it when the result is ready. This section's demo shows what the worker pool's cap costs. 200 requests arrive on one IO context, and each makes a 100 ms blocking call:

```text
worker pool (20 threads)   200 calls x 100 ms -> 1,037 ms on 20 distinct threads
virtual thread per call    200 calls x 100 ms ->   113 ms on 200 distinct threads
```

The Quarkus virtual threads guide compares the three models in one table, and its cons are the part to remember:

| Model | Runs on | Main cost |
|---|---|---|
| plain return value | worker thread | the pool caps concurrency |
| `Uni` and friends | IO thread | more complex code |
| `@RunOnVirtualThread` | a new virtual thread | pinning, monopolization, inefficient object pooling |

Pinning means a virtual thread that can't unmount, so it holds its carrier thread while it waits. On Java 21 to 23 that happens when it blocks inside `synchronized`. JDK 24 removed that case (JEP 491), but native code can still pin, and the guide notes that `pgjdbc` drivers before 42.6.0 pin often on 21 to 23. Monopolization means CPU-heavy work that never blocks, so it keeps its carrier: virtual threads are for IO-bound work only. And libraries such as Jackson and Netty pool objects per thread, assuming a few long-lived threads; a new virtual thread per request defeats those pools.

Two more things stay true. Virtual threads don't limit concurrency: 200 virtual threads sharing a 20-connection JDBC pool still queue at the pool, so put a semaphore or the pool's own limit in front of anything fragile. And the request still arrives on an IO thread. `@RunOnVirtualThread` works by moving your code off it.""",
   "try": {
    "title": "Pool cap versus virtual threads",
    "minutes": 3,
    "steps": [
     "Open `VirtualVsWorkerDemo.java` (or the Kotlin twin). Predict both times before running.",
     "Run it.",
     "Give the worker pool 40 threads: change `Vertx.vertx()` to `Vertx.vertx(new VertxOptions().setWorkerPoolSize(40))`. Predict the new worker time, then run."
    ],
    "code": {"lang": "java", "title": "VirtualVsWorkerDemo.java", "src": read(f"{lab}/demo/{P}/VirtualVsWorkerDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.VirtualVsWorkerDemo",
             "file": f"{lab}/demo/{P}/VirtualVsWorkerDemo.java",
             "alt": {"lang": "kotlin", "title": "VirtualVsWorkerDemo.kt", "src": read(f"{lab}/demo/{K}/VirtualVsWorkerDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.VirtualVsWorkerDemoKt",
                     "file": f"{lab}/demo/{K}/VirtualVsWorkerDemo.kt"}},
    "expect": "About 1,000 ms on 20 worker threads (200 calls / 20 threads × 100 ms) and about 110 to 130 ms on 200 virtual threads. With 40 workers it drops to about 500 to 600 ms (534 and 598 ms in my runs): Little's law again, throughput = threads / time per call. The virtual version has no such cap, which is its strength and also why you add your own limit in front of a fragile downstream."
   },
   "refs": [
    {"title": "Quarkus virtual threads guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A Quarkus endpoint's return type is a label on a kitchen order. Orders marked \"quick\" (`Uni`, `suspend`) are handled by the waiter at the pass, the IO thread, who never leaves the floor for long. Orders without the label go to the back kitchen, the worker pool, which has a fixed number of cooks. `@RunOnVirtualThread` hires a temporary cook for each order, who sits down while the oven works and costs almost nothing while waiting. The analogy breaks at the label: a real waiter would notice a forty-minute stew. Quarkus trusts the label completely, so a slow dish marked \"quick\" blocks the waiter and every table behind them.",
 "in_your_world": "A payments service on Quarkus with Oracle, JDBC and JTA is a blocking service, and that is fine: give its endpoints plain return types, put `@Blocking` on anything `@Transactional` that returns `Uni` or is `suspend`, and size the worker pool and the datasource pool together. Reach for `Uni` only where the whole call chain is reactive, such as a reactive SQL client or the Vert.x web client calling a card issuer. Kotlin teams need one extra rule: `suspend` does not mean \"off the event loop\". A `suspend fun` that calls a JDBC repository blocks an IO thread. When latency jumps while CPU is idle, search the logs for `has been blocked for`.",
 "mistake": "The common mistake is converting a JDBC endpoint to return `Uni` \"to make it reactive\": `return Uni.createFrom().item(repository.findById(id));`. Quarkus sees `Uni`, runs the method on the IO thread, and `findById` blocks the event loop while the `Uni` is built. Nothing becomes reactive. The service just loses the worker thread that used to protect the event loop. Either keep the plain return type, add `@Blocking`, or switch the data access to a reactive client so the method really doesn't block.",
 "compare": {
  "title": "The lab's dispatch rules in Kotlin and Java",
  "java": {"title": "DispatchRules.java", "src": rules_java},
  "kotlin": {"title": "DispatchRules.kt", "src": rules_kotlin},
  "note": "Both encode the same first-match-wins rules; Kotlin's `when` without a subject reads like the figure, Java uses early returns. The language difference that matters is in Quarkus itself: Java has no `suspend`, so a Java endpoint is non-blocking only through its return type, while a Kotlin `suspend fun` with a plain return type is non-blocking too and runs on the IO thread. One Kotlin trap from this lesson's lab: Vert.x 5's `Future` has a member `await()`, and in Kotlin a member always wins over an extension with the same name, so a test helper `fun <T> Future<T>.await()` is silently ignored. The lab's test calls its helper `awaitResult()` for that reason."
 },
 "worked": {
  "title": "Pick the thread for four payment endpoints",
  "steps": [
   {"say": "A payment lookup reads Oracle through JDBC. Plain return type, so it runs on a worker. Nothing to add.",
    "code": "@GET @Path(\"/payments/{id}\")\npublic Payment byId(@PathParam(\"id\") String id) {   // worker thread\n    return payments.findById(id);                     // JDBC\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@GET @Path(\"/payments/{id}\")\nfun byId(@PathParam(\"id\") id: String): Payment =   // worker thread\n    payments.findById(id)                          // JDBC"},
   {"say": "A capture endpoint uses JTA and returns `Uni` because a client library wants one. Under the 3.40.1 docs `@Transactional` alone would send it to a worker; under the main-branch docs it would run on the IO thread and the interceptor would throw. Add `@Blocking` and both readings agree.",
    "code": "@Blocking\n@Transactional\n@POST @Path(\"/payments/{id}/capture\")\npublic Uni<Receipt> capture(@PathParam(\"id\") String id) {\n    return Uni.createFrom().item(ledger.capture(id));    // JDBC inside a JTA transaction\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@Blocking\n@Transactional\n@POST @Path(\"/payments/{id}/capture\")\nfun capture(@PathParam(\"id\") id: String): Uni<Receipt> =\n    Uni.createFrom().item(ledger.capture(id))        // JDBC inside a JTA transaction"},
   {"say": "A live feed of payment events comes from a reactive client and never blocks. `Multi` keeps it on the IO thread with no thread switch, which is the case the reactive model is built for.",
    "code": "@GET @Path(\"/payments/events\")\npublic Multi<PaymentEvent> events() {                 // IO thread\n    return eventStream.subscribe();                  // non-blocking source\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@GET @Path(\"/payments/events\")\nfun events(): Multi<PaymentEvent> =                  // IO thread\n    eventStream.subscribe()                          // non-blocking source"},
   {"say": "A settlement report calls a slow SOAP service (2 s) that accepts at most 50 concurrent calls, and finance runs it in bursts of hundreds. The worker pool would cap throughput, so use a virtual thread per request, and put the downstream's limit back with a semaphore.",
    "code": "private final Semaphore soapSlots = new Semaphore(50);\n\n@RunOnVirtualThread\n@GET @Path(\"/reports/settlement/{day}\")\npublic Report settlement(@PathParam(\"day\") String day) throws InterruptedException {\n    soapSlots.acquire();                             // 1. respect the downstream's limit\n    try {\n        return soapClient.settlementFor(day);        // 2. blocks: parks the virtual thread\n    } finally {\n        soapSlots.release();\n    }\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "private val soapSlots = Semaphore(50)\n\n@RunOnVirtualThread\n@GET @Path(\"/reports/settlement/{day}\")\nfun settlement(@PathParam(\"day\") day: String): Report {\n    soapSlots.acquire()                              // 1. respect the downstream's limit\n    try {\n        return soapClient.settlementFor(day)         // 2. blocks: parks the virtual thread\n    } finally {\n        soapSlots.release()\n    }\n}"}
  ]
 },
 "lab": {
  "title": "Simulate Quarkus's dispatch on plain Vert.x",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/Dispatcher.kt", f"{lab}/main/{K}/Endpoint.kt"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l06.*'",
  "steps": [
   "Run the tests. All seven fail with `NotImplementedError`. Read `Endpoint.kt` for the types.",
   "Write `DispatchRules.target` with a `when` that applies the four rules in its KDoc, first match wins. The four rule tests should pass.",
   "Write `BlockingGuard.check`: throw `BlockingNotAllowedException(\"Attempting $what on an IO thread\")` when `Context.isOnEventLoopThread()` is true.",
   "Write `Dispatcher.invoke`: receive the request with `server.runOnContext { ... }`, then run the body there (IO thread), through `vertx.executeBlocking(callable, false)` (worker) or on a new virtual thread, and complete a `Promise` with the result or the failure.",
   "Run the tests until all seven pass. Then change `false` to the default and see which test fails, and why."
  ],
  "hints": [
   "`Marker.BLOCKING in endpoint.markers` reads naturally in Kotlin.",
   "`val p = Promise.promise<T>()`, then `p.complete(value)` or `p.fail(e)`, and return `p.future()`. For the worker branch, `vertx.executeBlocking(task, false).onComplete(p)` passes the result straight on.",
   "Give the `Callable` an explicit type (`val task: Callable<T> = Callable { body() }`); Kotlin can fail to infer Vert.x types whose `@Nullable` annotation lives in vertx-codegen.",
   "Every request goes through the one `server` context, so an ordered `executeBlocking` would make the four 300 ms calls queue: that is what the overlap test catches."
  ],
  "done_when": "All seven tests in `DispatcherTest` pass."
 },
 "drill": {
  "title": "Write the dispatch rules from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write a function that takes an endpoint's return kind and its annotations and returns IO_THREAD, WORKER or VIRTUAL_THREAD, using Quarkus 3.40's documented rules. Which rule would you add `@Blocking` for, to stay safe on any 3.x version?",
  "answer": {"lang": "kotlin", "src": rules_kotlin + "\n// add @Blocking to @Transactional endpoints that return Uni (or are suspend):\n// the 3.40.1 and main-branch docs disagree about the TRANSACTIONAL rule.",
             "alt": {"lang": "java", "src": rules_java + "\n// add @Blocking to @Transactional endpoints that return Uni:\n// the 3.40.1 and main-branch docs disagree about the TRANSACTIONAL rule."}}
 },
 "recap": [
  "Every Quarkus request arrives on an IO thread. Quarkus REST then picks the thread from the signature: `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` stay on the IO thread; plain return values go to a worker.",
  "`@Blocking` and `@NonBlocking` override the signature on a method, a class or the `Application`.",
  "The 3.40.1 docs say `@Transactional` makes a method blocking; the main-branch docs say it no longer does. Put `@Blocking` on JTA endpoints that return `Uni` either way.",
  "Quarkus 3.40 runs one event loop per CPU (at least 2), warns after 2 s and prints the stack at 2 s. Guarded APIs throw `BlockingOperationNotAllowedException` on an IO thread.",
  "`@RunOnVirtualThread` runs blocking code on a new virtual thread: no pool cap, but watch for pinning, CPU-heavy work and per-thread pools, and add your own limit toward fragile downstreams."
 ],
 "quiz": [
  {"q": "In Quarkus 3.40 with no annotations, which endpoint runs on the IO thread?",
   "options": ["`public Payment get(@PathParam(\"id\") String id)`", "`public List<Payment> recent()`", "`public Uni<Payment> get(@PathParam(\"id\") String id)`", "`public Response refund(...)`"],
   "answer": 2,
   "why": "Only the `Uni` return type marks the method as non-blocking. The other three return plain values, so Quarkus runs them on a worker thread."},
  {"q": "A Kotlin endpoint `suspend fun capture(id: String): Receipt = repository.capture(id)` calls a blocking JDBC repository. What happens under load?",
   "options": ["Nothing: suspend functions never block a thread", "It runs on the IO thread, so each JDBC call blocks an event loop; make it a plain function or call a non-blocking client", "Quarkus notices the JDBC call and moves it to a worker", "It runs on a new virtual thread"],
   "answer": 1,
   "why": "Quarkus treats `suspend` like `Uni`: non-blocking, so it runs on the IO thread. `suspend` only frees the thread when the code inside actually suspends; a JDBC call blocks it. Quarkus can't see inside the method."},
  {"q": "A Quarkus log shows `Thread vert.x-eventloop-thread-2 has been blocked for 2105 ms, time limit is 2000 ms` followed at once by a stack trace. Plain Vert.x would print the stack only after 5 s. Why here?",
   "options": ["Quarkus sets the warning-exception time to 2 s", "Quarkus lowers the blocked limit to 1 s", "Vert.x 5 changed its default to 2 s", "The stack means Quarkus killed the thread"],
   "answer": 0,
   "why": "Quarkus's `quarkus.vertx.warning-exception-time` defaults to 2 s, the same as the blocked limit, so the first warning already carries the stack trace. Neither Vert.x nor Quarkus kills or interrupts the thread."},
  {"q": "From lesson 5: a Vert.x consumer calls `vertx.executeBlocking(callable)` without the second argument for every message. Six messages arrive at once, each needing 300 ms of blocking work. Roughly how long until all six are answered?",
   "options": ["About 300 ms", "About 1,800 ms", "About 600 ms", "Never: it deadlocks"],
   "answer": 1,
   "why": "The default `executeBlocking` is ordered per context, and all six messages come from the consumer's one context, so they run one after another on the worker pool: 6 × 300 ms. Passing `false` lets them overlap.",
   "from": "io-05"},
  {"q": "A report endpoint calls a blocking SOAP service that takes 2 s and allows 50 concurrent calls. Finance sends bursts of 500 requests. Which fits best?",
   "options": ["Return `Uni` and call the SOAP client inside it", "Plain return type, with the worker pool raised to 500", "`@NonBlocking`, so it doesn't use a worker", "`@RunOnVirtualThread`, with a semaphore of 50 around the SOAP call"],
   "answer": 3,
   "why": "The call blocks, so it must stay off the IO thread, which rules out `Uni` and `@NonBlocking`. Virtual threads make 500 waiting requests cheap, and the semaphore keeps the SOAP service at its limit of 50. A 500-thread worker pool would work, but costs 500 platform threads and still sends 500 concurrent calls downstream."}
 ],
 "flashcards": [
  {"front": "Which Quarkus REST return types run on the IO thread by default?", "back": "`Uni`, `Multi`, `CompletionStage`, `Publisher`, and Kotlin `suspend` functions. Everything else runs on a worker thread."},
  {"front": "Where can you put `@Blocking` / `@NonBlocking` in Quarkus REST?", "back": "On a method, a class, or a `jakarta.ws.rs.core.Application` subclass (which sets the app-wide default)."},
  {"front": "Does `@Transactional` make a Quarkus REST method blocking?", "back": "The 3.40.1 docs say yes, the main-branch docs say no (since 3.35). Add an explicit `@Blocking` to JTA endpoints that return `Uni`."},
  {"front": "Default number of Vert.x event loops in Quarkus 3.40?", "back": "One per CPU, at least 2, and at most one per 10 MB of max heap: `max(2, min(maxHeapMB / 10, cpus))`."},
  {"front": "Why does a Quarkus blocked-thread warning come with a stack trace at 2 s?", "back": "Quarkus sets `quarkus.vertx.warning-exception-time` to 2 s; plain Vert.x uses 5 s."},
  {"front": "What exception do guarded Quarkus APIs throw on an IO thread?", "back": "`BlockingOperationNotAllowedException` (an `IllegalStateException`), e.g. from the JTA interceptor or a blocking body read."},
  {"front": "Three costs of `@RunOnVirtualThread` named by the Quarkus guide?", "back": "Pinning (e.g. `synchronized` on Java 21 to 23, native code), monopolization by CPU-heavy work, and inefficient per-thread object pools."}
 ],
 "terms": [
  {"term": "IO thread", "plain": "Quarkus's name for a Vert.x event-loop thread; it reads requests and writes responses."},
  {"term": "Worker thread", "plain": "A thread from Quarkus's bounded pool that may block, used for plain return types and `@Blocking`."},
  {"term": "@Blocking / @NonBlocking", "plain": "Annotations that override the thread Quarkus would pick from the method's signature."},
  {"term": "@RunOnVirtualThread", "plain": "Runs the endpoint on a new virtual thread instead of the IO thread or a worker."},
  {"term": "BlockingOperationNotAllowedException", "plain": "Thrown by guarded Quarkus APIs when blocking code runs on an IO thread."},
  {"term": "Pinning", "plain": "A virtual thread that can't unmount while it waits, so it holds its carrier thread."},
  {"term": "Monopolization", "plain": "CPU-heavy work on a virtual thread that never blocks, so it keeps its carrier."}
 ],
 "explain_back": {
  "prompt": "A teammate changed a JDBC endpoint to return `Uni` \"to make it reactive\" and latency got worse under load. Explain what Quarkus 3.40 does with that endpoint and what they should do instead.",
  "answer": "Quarkus REST decides the thread from the signature. A `Uni` return type means the method promises not to block, so Quarkus runs it on the IO thread, a Vert.x event loop, without switching to a worker. Wrapping a JDBC call in `Uni.createFrom().item(...)` evaluates the call while the method runs, so the JDBC call blocks the event loop and every other connection on it waits. Before the change, the plain return type put the call on a worker thread, which protected the event loop. They should either go back to a plain return type, or add `@Blocking` if they must return `Uni`, or switch to a reactive database client so the method really doesn't block. If the reason for the change was the worker pool's limit, `@RunOnVirtualThread` with a limit on database concurrency is another option."
 },
 "deeper": {
  "minutes": 10,
  "body": """A few details from the Quarkus 3.40 sources and docs help when you debug thread choices.

Filters follow their endpoint. A `@ServerRequestFilter` runs on the worker for a `@Blocking` endpoint and on the IO thread otherwise, so a filter that does a blocking lookup (say, an API-key check against a database) blocks the event loop for every non-blocking endpoint. `@ServerRequestFilter(nonBlocking = true)` forces a filter onto the IO thread, which is only safe if it really never blocks.

To check which thread runs your code, log `Thread.currentThread().getName()` or assert `io.vertx.core.Context.isOnEventLoopThread()` in a `@QuarkusTest`. Event-loop threads are named `vert.x-eventloop-thread-N`, and Quarkus's worker threads usually have `executor-thread` in their names.

The Vert.x knobs live under `quarkus.vertx.*`: `event-loops-pool-size`, `max-event-loop-execute-time`, `warning-exception-time` and `max-worker-execute-time` (60 s). The old `quarkus.vertx.worker-pool-size` is deprecated in favor of `quarkus.thread-pool.max-threads`. Raising the event-loop count rarely helps a service that blocks: it only spreads the damage over more loops. Removing the blocking call is the fix.

Finally, a version note on the `@Transactional` disagreement: the 3.40.1-tagged guide and the main-branch guide were both read for this track, and the code that applies the rule was not found. If you need certainty for your exact Quarkus version, write a `@QuarkusTest` that calls a `@Transactional` endpoint returning `Uni` and asserts which thread it ran on."""
 },
 "sources": [
  {"title": "Quarkus REST guide at 3.40.1: execution model", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc"},
  {"title": "Quarkus virtual threads guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc"},
  {"title": "Quarkus reactive architecture guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc"},
  {"title": "VertxCoreRecorder at 3.40.1: default event loops and IO-thread detector", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/extensions/vertx/runtime/src/main/java/io/quarkus/vertx/core/runtime/VertxCoreRecorder.java"},
  {"title": "TransactionalInterceptorBase at 3.40.1", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/extensions/narayana-jta/runtime/src/main/java/io/quarkus/narayana/jta/runtime/interceptor/TransactionalInterceptorBase.java"}
 ]
}

out = ROOT / "content/lessons/io-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
