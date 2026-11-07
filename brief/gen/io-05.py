import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l05"
K = "kotlin/workbench/nio/l05"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 680 290" role="img" aria-label="Two Vert.x event-loop threads, each holding the contexts of verticle instances. '
    'The event bus above connects the contexts, and a worker pool below runs executeBlocking calls and worker verticles">'
    '<rect class="box-b" x="20" y="16" width="640" height="36" rx="8"/>'
    '<text class="t-s" x="340" y="39" text-anchor="middle">event bus: string addresses such as payments.authorize, in memory, best effort</text>'
    '<rect class="box" x="20" y="74" width="300" height="122" rx="8"/>'
    '<text class="t-s t-code" x="170" y="94" text-anchor="middle">vert.x-eventloop-thread-0</text>'
    '<rect class="box-a" x="34" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="99" y="134" text-anchor="middle">Authorize #2</text>'
    '<text class="t-s t-m" x="99" y="154" text-anchor="middle">context</text>'
    '<rect class="box-a" x="176" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="241" y="134" text-anchor="middle">HTTP server</text>'
    '<text class="t-s t-m" x="241" y="154" text-anchor="middle">context</text>'
    '<rect class="box" x="360" y="74" width="300" height="122" rx="8"/>'
    '<text class="t-s t-code" x="510" y="94" text-anchor="middle">vert.x-eventloop-thread-1</text>'
    '<rect class="box-a" x="374" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="439" y="134" text-anchor="middle">Authorize #1</text>'
    '<text class="t-s t-m" x="439" y="154" text-anchor="middle">context</text>'
    '<text class="t-s t-m" x="582" y="134" text-anchor="middle">one task</text>'
    '<text class="t-s t-m" x="582" y="152" text-anchor="middle">at a time</text>'
    '<line class="ln-d" x1="60" y1="108" x2="60" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="400" y1="108" x2="400" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="241" y1="172" x2="241" y2="226" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="250" y="212">executeBlocking</text>'
    '<rect class="box-ok" x="20" y="230" width="640" height="44" rx="8"/>'
    '<text class="t-s" x="340" y="257" text-anchor="middle">worker pool, 20 threads by default: executeBlocking and WORKER verticles</text>'
    '</svg>'
)

balance_java = """public class BalanceVerticle extends VerticleBase {
    @Override
    public Future<?> start() {
        return vertx.eventBus().<String>consumer("ledger.balance", msg ->
                vertx.executeBlocking(() -> LedgerDao.balanceCents(msg.body()), false)
                        .onSuccess(msg::reply)                        // back on this verticle's context
                        .onFailure(e -> msg.fail(500, e.getMessage()))
        ).completion();
    }
}

vertx.deployVerticle(BalanceVerticle::new, new DeploymentOptions().setInstances(2));"""
balance_kotlin = """class BalanceVerticle : VerticleBase() {
    override fun start(): Future<*> =
        vertx.eventBus().consumer<String>("ledger.balance") { msg ->
            val query = Callable<Long> { LedgerDao.balanceCents(msg.body()) }
            vertx.executeBlocking(query, false)
                .onSuccess { cents: Long -> msg.reply(cents) }        // back on this verticle's context
                .onFailure { e -> msg.fail(500, e.message) }
        }.completion()
}

vertx.deployVerticle(::BalanceVerticle, DeploymentOptions().setInstances(2))"""

L = {
 "id": "io-05",
 "title": "Vert.x: event loops, verticles and the golden rule",
 "minutes": 38,
 "goal": "By the end you can deploy verticles and say which thread runs each handler, use the event bus for request/reply and publish, read Vert.x's blocked-thread warning, and move blocking work off the event loop without serializing it by accident.",
 "warmup": {
  "q": "A Vert.x HTTP handler wraps its 500 ms JDBC call in `vertx.executeBlocking(() -> dao.query())`. Four requests arrive at the same moment on a server with one event loop. Roughly how long until all four are answered?",
  "options": [
   "About 500 ms: the four queries run in parallel on the worker pool",
   "About 2,000 ms: by default executeBlocking runs calls from the same context one after another",
   "About 500 ms, but only if the worker pool has at least 4 threads",
   "It never finishes: executeBlocking deadlocks on a single event loop"
  ],
  "answer": 1,
  "why": "`executeBlocking` is ordered by default, and all requests to one HTTP server share its context. The loop is free, but the four queries queue behind each other on the worker pool. This lesson's demo measured 2,012 ms ordered and 511 ms with `executeBlocking(callable, false)`. The default worker pool has 20 threads, so the pool size isn't the limit."
 },
 "sections": [
  {
   "h": "Vert.x puts a context on top of Netty's event loop",
   "body": """Vert.x 5.2.3 runs on Netty 4.2.20. A `Vertx` instance starts a group of Netty event loops, twice the number of cores by default (8 on a 4-core machine), named `vert.x-eventloop-thread-0` and up. Its HTTP server is a Netty pipeline like the one in lesson 3, and the stack trace later in this lesson ends in `io.netty.channel.SingleThreadIoEventLoop.run`, the same loop class.

What Vert.x adds is a set of rules over those loops. The central one is the **context**: the home of a piece of code, which decides the thread that runs it. Most contexts are event-loop contexts, each tied to one event loop for life. When you register a handler, Vert.x remembers the current context, and every call of that handler runs there. The Vert.x docs promise that a handler is never executed concurrently and, worker verticles aside, always runs on the same event loop thread. That is lesson 3's Netty rule, one channel, one loop, extended to all your code: HTTP handlers, timers and event-bus consumers.

The second change is the API. Vert.x 4 had two styles, callbacks and futures. Vert.x 5 kept only futures: every asynchronous method returns an `io.vertx.core.Future`, and the callback overloads are gone.

```java
// Vert.x 5: listen returns a Future
server.listen(8080).onSuccess(s -> System.out.println("listening on " + s.actualPort()));
// Vert.x 4 style no longer compiles:
// server.listen(8080, ar -> ...)  ->  error: incompatible types: String is not a functional interface
```

```kotlin
// Vert.x 5: listen returns a Future
server.listen(8080).onSuccess { s -> println("listening on ${s.actualPort()}") }
// Vert.x 4 style no longer compiles:
// server.listen(8080) { ar -> ... }   the only two-argument listen left is listen(int, String)
```

The Java error looks unrelated because the compiler matched the one remaining two-argument overload, `listen(int, String)`, and complains that a `String` isn't a lambda. The same migration replaced `executeBlocking(promise -> ...)` with a version that takes a `Callable` and returns a `Future`.""",
   "try": {
    "title": "Hit the Vert.x 5 API change",
    "minutes": 2,
    "steps": [
     "In `ContextsDemo.java`, add one line after `Vertx vertx = Vertx.vertx();`: `vertx.createHttpServer().listen(8080, ar -> {});`.",
     "Predict whether it compiles. Then run the demo with the command below.",
     "Remove the line again."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ContextsDemo", "run": ""},
    "expect": "Compilation fails with `error: incompatible types: String is not a functional interface`. The callback overload of `listen` no longer exists in Vert.x 5, so `javac` tries `listen(int, String)` and can't turn your lambda into a `String`."
   }
  },
  {
   "h": "Verticles: units you deploy, each with its own context",
   "body": """A verticle is a class you deploy into Vert.x, and deploying it gives each instance its own context. In Vert.x 5 you extend `VerticleBase` and return a `Future` from `start()`, so the deployment completes only when your setup has:

```java
public class AuthorizeVerticle extends VerticleBase {
    @Override
    public Future<?> start() {
        return vertx.eventBus().<JsonObject>consumer("payments.authorize", msg ->
                msg.reply(new JsonObject().put("status", "APPROVED"))
        ).completion();                                  // done when the consumer is registered
    }
}

vertx.deployVerticle(AuthorizeVerticle::new, new DeploymentOptions().setInstances(2));
```

```kotlin
class AuthorizeVerticle : VerticleBase() {
    override fun start(): Future<*> =
        vertx.eventBus().consumer<JsonObject>("payments.authorize") { msg ->
            msg.reply(JsonObject().put("status", "APPROVED"))
        }.completion()                                   // done when the consumer is registered
}

vertx.deployVerticle(::AuthorizeVerticle, DeploymentOptions().setInstances(2))
```

For two instances you pass a factory, because each instance must be its own object. In 5.2.3 that factory is a `Supplier`, though the docs still say `Callable`. Each instance gets its own event-loop context, usually on different loops, which is how one verticle class uses several cores. Inside one instance, code never runs on two threads at once, so its fields need no locks.

The threading model in `DeploymentOptions` decides what kind of context a verticle gets. This section's demo prints where each kind runs:

```text
[EVENT_LOOP] start() on vert.x-eventloop-thread-0 eventLoopCtx=true workerCtx=false
[WORKER] start() on vert.x-worker-thread-0 eventLoopCtx=false workerCtx=true
[VIRTUAL_THREAD] start() on vert.x-virtual-thread-0 (virtual) eventLoopCtx=false workerCtx=false
```

`EVENT_LOOP`, the default, must never block. A `WORKER` verticle runs on the worker pool (20 threads by default) and may block; it still never runs on two threads at once, though successive calls can land on different worker threads. `VIRTUAL_THREAD` is new in Vert.x 5 and needs Java 21: the verticle runs on virtual threads, and `future.await()` parks the virtual thread until the result arrives. It also runs one task at a time, with one catch from the docs: a field you read before an `await()` may have changed after it, because another task of the same verticle can run while you wait.""",
   "figure": {"svg": FIG, "caption": "Each verticle instance has a context on one event loop. Contexts talk over the event bus, and blocking work goes to the worker pool and comes back to the same context."},
   "try": {
    "title": "Where does each verticle run?",
    "minutes": 3,
    "steps": [
     "Open `ContextsDemo.java` (or `ContextsDemo.kt`). It deploys one verticle per threading model, then calls `executeBlocking` from an event-loop context.",
     "Predict the thread name in each line, and on which thread `onSuccess` runs after `executeBlocking`.",
     "Run it."
    ],
    "code": {"lang": "java", "title": "ContextsDemo.java", "src": read(f"{lab}/demo/{P}/ContextsDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ContextsDemo",
             "file": f"{lab}/demo/{P}/ContextsDemo.java",
             "alt": {"lang": "kotlin", "title": "ContextsDemo.kt", "src": read(f"{lab}/demo/{K}/ContextsDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ContextsDemoKt",
                     "file": f"{lab}/demo/{K}/ContextsDemo.kt"}},
    "expect": "The first line reports 8 event loops on 4 CPUs and a worker pool of 20. The three verticles start on `vert.x-eventloop-thread-0`, `vert.x-worker-thread-0` and a virtual thread `vert.x-virtual-thread-0`. The `executeBlocking` callable runs on a worker thread, and `onSuccess` runs back on an event-loop thread: the context that called it."
   }
  },
  {
   "h": "The event bus carries messages between contexts",
   "body": """The event bus is how verticles talk without sharing objects. There is one per `Vertx` instance, and an address is just a string such as `payments.authorize`. You can send in three ways:

- `send(address, msg)`: to one consumer at that address, chosen round-robin.
- `request(address, msg)`: to one consumer, and you get a `Future` of its reply.
- `publish(address, msg)`: to every consumer at that address.

This section's demo deploys two instances of a greeter and makes requests:

```text
request greet #0 -> hello dev0 from instance#1 on vert.x-eventloop-thread-1
request greet #1 -> hello dev1 from instance#2 on vert.x-eventloop-thread-0
request greet #2 -> hello dev2 from instance#1 on vert.x-eventloop-thread-1
request nobody -> NO_HANDLERS code=-1 message=No handlers for address nobody
request fail -> RECIPIENT_FAILURE code=42 message=boom from instance#2
request silent (timeout 300 ms) -> TIMEOUT after 311 ms
```

A request can fail in three ways, each delivered as a `ReplyException` with a `failureType()`. `NO_HANDLERS` means nobody listens at the address. `RECIPIENT_FAILURE` means the consumer called `msg.fail(code, text)`, and you get its code and text. `TIMEOUT` means no reply arrived in time. The default timeout is 30 seconds, far too long for a payment path, so set one per request with `new DeliveryOptions().setSendTimeout(...)`.

The reply comes back on the requester's context, not the consumer's. A worker verticle that sends a request handles the reply on a worker thread; a virtual-thread verticle resumes on its virtual thread.

Two properties keep the event bus from being a message broker. Delivery is best effort: there is no persistence and no retry, and the docs tell you to make handlers idempotent. And inside one JVM a message can be handed over by reference. With a custom local codec whose `transform` returns its argument, the consumer receives the very object you sent, so never change a message after you send it. Built-in codecs cover strings, numbers, `Buffer`, `JsonObject` and `JsonArray`; other types need a codec you register.""",
   "try": {
    "title": "Make every kind of reply happen",
    "minutes": 3,
    "steps": [
     "Open `EventBusDemo.java` (or `EventBusDemo.kt`). Predict which instance answers each of the four requests, and how many lines `publish` prints.",
     "Run it.",
     "Change the silent request's timeout from 300 to 1,000 ms and run again. What changes, and what doesn't?"
    ],
    "code": {"lang": "java", "title": "EventBusDemo.java", "src": read(f"{lab}/demo/{P}/EventBusDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.EventBusDemo",
             "file": f"{lab}/demo/{P}/EventBusDemo.java",
             "alt": {"lang": "kotlin", "title": "EventBusDemo.kt", "src": read(f"{lab}/demo/{K}/EventBusDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.EventBusDemoKt",
                     "file": f"{lab}/demo/{K}/EventBusDemo.kt"}},
    "expect": "The requests alternate between the two instances (1, 2, 1, 2 in my runs; the docs only promise a non-strict round-robin), each on its own event loop. `publish` prints two lines, one per instance, in either order. The failures come back as `NO_HANDLERS`, `RECIPIENT_FAILURE` with code 42, and `TIMEOUT` after about 300 ms. With 1,000 ms the timeout simply arrives later: the consumer still never replies."
   },
   "refs": [
    {"title": "Vert.x 5.2.3 event bus documentation (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/eventbus.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "The golden rule, and the catch in executeBlocking",
   "body": """Vert.x calls it the golden rule: don't block the event loop. Its docs list what counts: `Thread.sleep()`, waiting on a lock or a `synchronized` monitor, a long database operation, a complex calculation, spinning in a loop. They also give the budget: with one event loop and 10,000 HTTP requests a second, each request can take at most 0.1 ms.

Vert.x checks the rule for you. A separate thread, `vertx-blocked-thread-checker`, wakes up every second and looks at each event loop. If the task a loop is running started more than 2 seconds ago, it logs a warning, and past 5 seconds it adds the blocked thread's stack trace. It measures one task at a time: each loop records when its current task began, and the checker compares that with the clock. So ten 300 ms blocking calls in a row hold a loop for 3 seconds and never produce a warning. This section's demo sleeps 6 seconds on an event loop:

```text
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 2891 ms, time limit is 2000 ms
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 3891 ms, time limit is 2000 ms
...
io.vertx.core.VertxException: Thread blocked
	at java.base/java.lang.Thread.sleep(Thread.java:509)
	at workbench.nio.l05.BlockedThreadDemo.lambda$main$0(BlockedThreadDemo.java:13)
	...
	at io.netty.channel.SingleThreadIoEventLoop.run(SingleThreadIoEventLoop.java:228)
```

The first warning came at 2.9 s, not 2.0 s, because the checker only looks once a second. Search your logs for `has been blocked for`; the logger is `io.vertx.core.impl.BlockedThreadChecker`. The checker only reports. It never interrupts the blocked thread.

For blocking work there is `executeBlocking`: it runs a `Callable` on the worker pool and completes a `Future` back on your context. Its catch is that it is ordered by default, so calls from the same context run one after another. The demo sends 4 concurrent HTTP requests, each doing a 500 ms fake JDBC call, to a server with one event loop:

```text
block-on-event-loop        4 requests x 500 ms -> 2201 ms, ran on [vert.x-eventloop-thread-0]
executeBlocking-ordered    4 requests x 500 ms -> 2012 ms, ran on [vert.x-worker-thread-0]
executeBlocking-unordered  4 requests x 500 ms ->  511 ms, ran on [vert.x-worker-thread-0, ..., vert.x-worker-thread-3]
```

The ordered version freed the event loop for every other connection, but the four queries still ran single file, because every request to one server shares that server's context. Pass `false` when the calls are independent: `executeBlocking(callable, false)`. And remember what the worker pool is: 20 threads by default, a bounded pool like the ones in the executors track. Behind a 20-connection JDBC pool, that is a thread-per-request design again. That is fine, as long as you size it like one.""",
   "try": {
    "title": "Three ways to make a slow call",
    "minutes": 5,
    "steps": [
     "Open `ExecuteBlockingDemo.java` (or `ExecuteBlockingDemo.kt`). Predict the total time and the thread names for each of the three modes.",
     "Run it with the command below.",
     "Then run `./gradlew :nio:demo -Pmain=workbench.nio.l05.BlockedThreadDemo` and predict when the first warning appears and when the stack trace appears. Run it with `-Pargs=2500` too: how many warnings now?"
    ],
    "code": {"lang": "java", "title": "ExecuteBlockingDemo.java", "src": read(f"{lab}/demo/{P}/ExecuteBlockingDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ExecuteBlockingDemo",
             "file": f"{lab}/demo/{P}/ExecuteBlockingDemo.java",
             "alt": {"lang": "kotlin", "title": "ExecuteBlockingDemo.kt", "src": read(f"{lab}/demo/{K}/ExecuteBlockingDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ExecuteBlockingDemoKt",
                     "file": f"{lab}/demo/{K}/ExecuteBlockingDemo.kt"}},
    "expect": "About 2,000 ms on the event loop thread, about 2,000 ms on one worker thread with the ordered default, and about 500 ms across four worker threads with `false` (2,201, 2,012 and 511 ms in my run; this track's research run measured 2,814, 2,043 and 576). The blocked-thread demo warns between 2 and 3 seconds in, once a second after that, and adds the `VertxException: Thread blocked` stack trace after 5 seconds. A 2,500 ms sleep gives zero or one warning, depending on when the checker happens to look."
   },
   "refs": [
    {"title": "Vert.x 5.2.3 core documentation: The Golden Rule (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A Vert.x context is a desk with one chair. Everything registered at that desk (handlers, timers, event-bus consumers) is dealt with by whoever sits in the chair, one item at a time, so nobody at the desk needs to lock the drawers. An event-loop desk always has the same clerk; the event bus is the internal mail between desks; `executeBlocking` is sending a long errand to the back office and getting the result back on your desk. The analogy breaks for worker desks: different clerks can sit in a worker desk's chair on different days, though never two at once, which is why a worker verticle is still single-threaded but not tied to one thread.",
 "in_your_world": "Every Quarkus service you run is a Vert.x application underneath: the HTTP layer is a Vert.x server on Vert.x event loops, and Quarkus's `@ConsumeEvent` sits on the same event bus. The blocked-thread warning in this lesson is the one you will see in a Quarkus log when an endpoint blocks an IO thread, with Quarkus-specific limits that lesson 6 covers. If a team writes plain Vert.x for a payment router or a ledger projection, make them pass `false` to `executeBlocking` for independent queries, set a send timeout on every event-bus request, and keep handlers idempotent, because the event bus will not redeliver a lost message.",
 "mistake": "The common mistake is moving blocking code into `executeBlocking` and calling the job done. The event loop is free, so the warnings stop, but the default is ordered per context, and every request to one HTTP server or one consumer shares a context, so the calls still queue behind each other: 2,012 ms instead of 511 ms in this lesson's demo. Pass `false` for independent calls, or deploy a `WORKER` verticle with several instances. The second mistake is waiting for a result on the event loop, with `toCompletionStage().toCompletableFuture().get()`: if the result needs that same loop to complete, the thread waits for itself.",
 "compare": {
  "title": "A verticle that offloads a blocking query",
  "java": {"title": "BalanceVerticle.java", "src": balance_java},
  "kotlin": {"title": "BalanceVerticle.kt", "src": balance_kotlin},
  "note": "Same Vert.x API, same threads at runtime. Two Kotlin wrinkles came up while building this lesson's demos. `vertx.deployVerticle({ BalanceVerticle() }, options)` does not compile in Kotlin: `Deployable` is itself a single-method interface, so a bare lambda matches both overloads. Use a constructor reference (`::BalanceVerticle`) or `Supplier { BalanceVerticle() }`. And some Vert.x 5 signatures carry a `@Nullable` type annotation from `vertx-codegen`, which is not on the classpath, so Kotlin can fail with \"Type annotation class 'io.vertx.codegen.annotations.Nullable' of the inferred type is inaccessible\" when it infers a lambda's type. Giving the `Callable` and the lambda parameter explicit types, as above, avoids it. Java ignores the annotation."
 },
 "worked": {
  "title": "Unblock a ledger verticle, step by step",
  "steps": [
   {"say": "A balance consumer calls JDBC directly. It works in a demo with one request. Under load, every handler on the same event loop waits behind it, and the blocked-thread checker stays silent: it measures one task at a time, and each 300 ms query is under its 2-second limit. Short blocking calls are the kind that never show up in the logs.",
    "code": "vertx.eventBus().<String>consumer(\"ledger.balance\", msg -> {\n    try {\n        msg.reply(LedgerDao.balanceCents(msg.body()));   // 300 ms on the event loop\n    } catch (InterruptedException e) {\n        msg.fail(500, \"interrupted\");\n    }\n});",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.eventBus().consumer<String>(\"ledger.balance\") { msg ->\n    msg.reply(LedgerDao.balanceCents(msg.body()))       // 300 ms on the event loop\n}"},
   {"say": "First attempt: `executeBlocking` with the default. The loop is free now, but six concurrent requests still take about 6 × 300 ms, because they all come from this consumer's context and the default is ordered.",
    "code": "vertx.executeBlocking(() -> LedgerDao.balanceCents(msg.body()))   // ordered: one at a time\n        .onSuccess(msg::reply);",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.executeBlocking(Callable<Long> { LedgerDao.balanceCents(msg.body()) })   // ordered: one at a time\n    .onSuccess { cents: Long -> msg.reply(cents) }"},
   {"say": "Second attempt: unordered. The queries now overlap on the worker pool, and the replies still come back on the consumer's context. The lab's test checks both: total time under 1,000 ms for six queries, and an event-loop lag under 150 ms.",
    "code": "vertx.executeBlocking(() -> LedgerDao.balanceCents(msg.body()), false)   // independent calls\n        .onSuccess(msg::reply)\n        .onFailure(e -> msg.fail(500, e.getMessage()));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.executeBlocking(Callable<Long> { LedgerDao.balanceCents(msg.body()) }, false)   // independent calls\n    .onSuccess { cents: Long -> msg.reply(cents) }\n    .onFailure { e -> msg.fail(500, e.message) }"},
   {"say": "Another design gives you a visible concurrency limit: make the whole verticle a worker and deploy as many instances as you want parallel queries. Each instance handles one message at a time on the worker pool, so four instances means at most four queries in flight, which you can match to the JDBC pool.",
    "code": "vertx.deployVerticle(BlockingBalanceVerticle::new, new DeploymentOptions()\n        .setThreadingModel(ThreadingModel.WORKER)   // may block\n        .setInstances(4));                          // at most 4 queries at once",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.deployVerticle(::BlockingBalanceVerticle, DeploymentOptions()\n    .setThreadingModel(ThreadingModel.WORKER)       // may block\n    .setInstances(4))                               // at most 4 queries at once"}
  ]
 },
 "lab": {
  "title": "Request/reply on the event bus, then unblock a verticle",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/AuthorizeVerticle.java", f"{lab}/main/{P}/BalanceVerticle.java", f"{lab}/main/{P}/LedgerDao.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l05.*'",
  "steps": [
   "Run the tests. All five fail: `AuthorizeVerticle.start()` throws, so the deployment in `@BeforeEach` fails.",
   "Write `AuthorizeVerticle.start()`: register a `JsonObject` consumer on `ADDRESS`, approve amounts up to `LIMIT` with a reply `{status, card, thread}`, fail larger ones with `msg.fail(402, \"limit exceeded\")`, and return the consumer's `completion()`. Four tests should pass.",
   "Read `balanceQueriesDoNotBlockTheLoop`. It makes its own `Vertx` with one event loop, sends six requests, and measures both the event-loop lag and the total time.",
   "Fix `BalanceVerticle` with `executeBlocking`. Try the one-argument version first and read the failure, then pass `false`."
  ],
  "hints": [
   "`msg.body().getDouble(\"amount\")` reads the amount; `Thread.currentThread().getName()` gives the `thread` value.",
   "`msg.fail(402, \"limit exceeded\")` reaches the requester as a `ReplyException` with `failureType()` `RECIPIENT_FAILURE` and `failureCode()` 402.",
   "`.onSuccess(msg::reply)` works because `reply` takes any `Object`.",
   "If a test times out after 30 seconds instead of failing fast, an assertion probably ran outside `tc.verify(...)`. The test file writes `@io.vertx.junit5.Timeout` in full because JUnit's own `@Timeout` has the same simple name."
  ],
  "done_when": "All five tests in `VerticleTest` pass, and you have seen the ordered `executeBlocking` fail the total-time assertion."
 },
 "drill": {
  "title": "Write a verticle that offloads a blocking call",
  "minutes": 5,
  "prompt": "Close the lab. Write a `VerticleBase` that answers requests on `ledger.balance` by running the blocking `LedgerDao.balanceCents(account)` off the event loop, in parallel across requests, and fails the message with code 500 on error. Then write the line that deploys two instances.",
  "answer": {"lang": "java", "src": balance_java, "alt": {"lang": "kotlin", "src": balance_kotlin}}
 },
 "recap": [
  "Vert.x runs on Netty event loops (2 × cores by default). A context ties code to one thread, and a handler never runs concurrently with itself.",
  "Vert.x 5 is futures-only: async methods return `Future`, callback overloads are gone, and `executeBlocking` takes a `Callable`.",
  "Each verticle instance gets its own context: `EVENT_LOOP` (never block), `WORKER` (may block, still one task at a time) or `VIRTUAL_THREAD` (Java 21+, `await()` parks).",
  "The event bus offers `send`, `request` and `publish` on string addresses. Requests fail with `NO_HANDLERS`, `RECIPIENT_FAILURE` or `TIMEOUT`; the default timeout is 30 s, and delivery is best effort.",
  "The blocked-thread checker warns after 2 s (checked every second) and adds a stack trace after 5 s. It only reports.",
  "`executeBlocking` is ordered per context by default. Pass `false` for independent calls, or use worker verticles with several instances."
 ],
 "quiz": [
  {"q": "A verticle is deployed with `setInstances(4)` and default options. Its consumer increments a plain `int` field on every message. Is that safe?",
   "options": ["No: four threads can increment the same field at once", "Yes: each instance is its own object with its own context, and a context never runs two handlers at once", "Only if the field is `volatile`", "Only for `WORKER` verticles"],
   "answer": 1,
   "why": "The factory creates four separate objects, so there are four separate fields, and each is only touched from its own context, one task at a time. `volatile` doesn't make `++` atomic anyway, and worker verticles have the same one-at-a-time rule."},
  {"q": "An HTTP handler wraps every database call in `vertx.executeBlocking(() -> jdbc.query(...))`. Under load, latency climbs while the database is idle and CPU is low. What is the most likely cause?",
   "options": ["`executeBlocking` is ordered by default, so calls from the server's context run one after another", "The worker pool has only one thread", "The event loop is blocked", "JDBC doesn't work on worker threads"],
   "answer": 0,
   "why": "All requests to one server share its context, and the default `executeBlocking` serializes calls from a context. The default worker pool has 20 threads, and the event loop is free, which is why there are no blocked-thread warnings. Pass `false`."},
  {"q": "A log line says `Thread vert.x-eventloop-thread-3 has been blocked for 2412 ms, time limit is 2000 ms`. What does Vert.x do to that thread?",
   "options": ["Interrupts it", "Replaces the event loop with a new one", "Nothing: it only logs, and adds a stack trace once the block passes 5 seconds", "Moves its handlers to another event loop"],
   "answer": 2,
   "why": "The blocked-thread checker is an observer. It logs every second while the block lasts and includes the stack once it passes the warning-exception time (5 s by default). The handlers stay pinned to their loop, so everything on it keeps waiting."},
  {"q": "From lesson 3: Vert.x event loops are Netty event loops. Which Netty rule explains why a Vert.x handler doesn't need a lock for its own fields?",
   "options": ["A channel stays on one event-loop thread for life, and that thread runs its events one at a time", "Netty copies every message before delivering it", "Netty's event loops are virtual threads", "`ByteBuf` is reference-counted"],
   "answer": 0,
   "why": "Vert.x extends Netty's one-channel-one-loop rule to contexts: everything registered on a context runs on its thread, one task after another. Confinement to one thread is what removes the need for locks.",
   "from": "io-03"},
  {"q": "A ledger verticle must tell three other verticles (audit, metrics, notifications) about each posted entry and needs no answers. Which call fits?",
   "options": ["`eventBus().send(\"ledger.posted\", entry)`", "`eventBus().request(...)` once per listener", "`vertx.executeBlocking(...)` around each notification", "`eventBus().publish(\"ledger.posted\", entry)`"],
   "answer": 3,
   "why": "`publish` delivers to every consumer at the address. `send` would reach only one of them, chosen round-robin, and `request` waits for replies nobody needs. Remember that delivery is best effort: if a notification must not be lost, the event bus is the wrong tool."}
 ],
 "flashcards": [
  {"front": "How many event loops does a default `Vertx` instance create?", "back": "2 × available processors: 8 on a 4-core machine."},
  {"front": "What is a Vert.x context?", "back": "The home of a piece of code: it fixes which thread runs it. A handler registered on a context always runs there, never concurrently with itself."},
  {"front": "When does Vert.x log a blocked event loop, and when does it add a stack trace (defaults)?", "back": "A warning once a task has run more than 2 s (checked every 1 s); the stack trace after 5 s. It only logs."},
  {"front": "Why can `executeBlocking(callable)` still run your calls one at a time?", "back": "It is ordered per context by default. Calls from the same context queue behind each other. Use `executeBlocking(callable, false)` for independent calls."},
  {"front": "The three `failureType()` values of a failed event-bus request?", "back": "`NO_HANDLERS` (nobody listens), `RECIPIENT_FAILURE` (the consumer called `fail`), `TIMEOUT` (no reply in time; default 30 s)."},
  {"front": "`send` vs `request` vs `publish` on the event bus?", "back": "`send`: one consumer, round-robin. `request`: one consumer, and you get a `Future` of the reply. `publish`: every consumer at the address."},
  {"front": "How do you deploy 4 instances of a verticle in Vert.x 5?", "back": "`vertx.deployVerticle(MyVerticle::new, new DeploymentOptions().setInstances(4))`: a `Supplier`, so each instance is a new object."}
 ],
 "terms": [
  {"term": "Verticle", "plain": "A class you deploy into Vert.x; each deployed instance gets its own context."},
  {"term": "Context", "plain": "Where a piece of Vert.x code runs: one event loop, a worker, or a virtual thread, one task at a time."},
  {"term": "Threading model", "plain": "The kind of context a verticle gets: `EVENT_LOOP`, `WORKER` or `VIRTUAL_THREAD`."},
  {"term": "Event bus", "plain": "Vert.x's in-process messaging between verticles, addressed by strings, best effort."},
  {"term": "Worker pool", "plain": "The pool of threads (20 by default) that runs blocking work and worker verticles."},
  {"term": "executeBlocking", "plain": "Runs a `Callable` on the worker pool and completes a `Future` back on your context."},
  {"term": "Blocked-thread checker", "plain": "A Vert.x thread that warns when an event loop has been busy with one task for too long."}
 ],
 "explain_back": {
  "prompt": "A colleague wrapped four slow JDBC calls in `executeBlocking` and is surprised that a burst of four requests still takes four times as long as one. Explain what a Vert.x context is and why their change didn't help, and what to do instead.",
  "answer": "A context is where Vert.x runs a piece of code: a handler registered on a context always runs there, one task at a time. All requests to one HTTP server share that server's context. `executeBlocking` moves the callable to the worker pool, which frees the event loop, but by default it is ordered per context: Vert.x queues calls from the same context and runs them one after another. So the four queries still ran in sequence, just on a worker thread instead of the event loop. If the calls are independent, pass `false` as the second argument so they run in parallel on the worker pool, or deploy a worker verticle with several instances to get an explicit concurrency limit. Either way, size the parallelism to the JDBC connection pool behind it."
 },
 "deeper": {
  "minutes": 10,
  "body": """Testing Vert.x code has its own traps, and vertx-junit5 exists because of them. A Vert.x callback runs on an event loop, after your test method has returned. If an assertion fails there, JUnit never sees it. The extension fixes that with `VertxTestContext`: the test passes only when you call `completeNow()` (or flag all checkpoints), and fails when you call `failNow(...)` or when an assertion inside `tc.verify(() -> ...)` throws.

This track's research ran the same failing assertion both ways. Outside `verify`, the test ran into the timeout after about 2.6 seconds with \"The test execution timed out. Make sure your asynchronous code includes calls to either VertxTestContext#completeNow(), VertxTestContext#failNow() or Checkpoint#flag()\", and the real `AssertionFailedError` was only printed to the log. Inside `verify`, it failed in 0.059 seconds with the actual assertion message. So every assertion in a callback goes inside `verify`, or inside `tc.succeeding(...)` and `tc.failing(...)`, which wrap it for you.

Other details from the vertx-junit5 docs: the default timeout is 30 seconds, overridden per test with `@io.vertx.junit5.Timeout` (fully qualified, to avoid JUnit's `@Timeout`). A `Vertx` injected into a `@BeforeAll` method is shared by the class, one injected into `@BeforeEach` is shared by that test and its `@AfterEach`, and injected instances are closed for you. `tc.checkpoint(n)` gives a counter that must be flagged `n` times, handy for testing `publish` to several consumers. And in Vert.x 5, clients rely on `Cleaner`, so a client object that becomes unreachable can close its pool while a test still uses it. Keep clients in fields during tests."""
 },
 "sources": [
  {"title": "Vert.x 5.2.3 core documentation (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc"},
  {"title": "Vert.x 5.2.3 event bus documentation (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/eventbus.adoc"},
  {"title": "Vert.x 5.2.3 virtual threads documentation (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/virtualthreads.adoc"},
  {"title": "vertx-junit5 5.2.3 documentation (source)", "url": "https://raw.githubusercontent.com/vert-x3/vertx-junit5/5.2.3/src/main/asciidoc/index.adoc"},
  {"title": "Vert.x 5 migration guide (README)", "url": "https://raw.githubusercontent.com/vert-x3/vertx-5-migration-guide/main/README.md"}
 ]
}

out = ROOT / "content/lessons/io-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
