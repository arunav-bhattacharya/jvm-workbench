import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l05"
K = "kotlin/workbench/nio/l05"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 680 290" role="img" aria-label="Two Vert.x event-loop threads, the clerks, each holding the contexts of desks: '
    'two weighing-desk instances and an HTTP server. The event bus above connects the contexts like mail tubes, and the worker pool '
    'below, the back office, runs executeBlocking calls and worker verticles">'
    '<rect class="box-b" x="20" y="16" width="640" height="36" rx="8"/>'
    '<text class="t-s" x="340" y="39" text-anchor="middle">event bus: tubes with string addresses such as desk.weigh, in memory, best effort</text>'
    '<rect class="box" x="20" y="74" width="300" height="122" rx="8"/>'
    '<text class="t-s t-code" x="170" y="94" text-anchor="middle">vert.x-eventloop-thread-0</text>'
    '<rect class="box-a" x="34" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="99" y="134" text-anchor="middle">weighing desk #2</text>'
    '<text class="t-s t-m" x="99" y="154" text-anchor="middle">context</text>'
    '<rect class="box-a" x="176" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="241" y="134" text-anchor="middle">HTTP server</text>'
    '<text class="t-s t-m" x="241" y="154" text-anchor="middle">context</text>'
    '<rect class="box" x="360" y="74" width="300" height="122" rx="8"/>'
    '<text class="t-s t-code" x="510" y="94" text-anchor="middle">vert.x-eventloop-thread-1</text>'
    '<rect class="box-a" x="374" y="108" width="130" height="64" rx="8"/>'
    '<text class="t-s" x="439" y="134" text-anchor="middle">weighing desk #1</text>'
    '<text class="t-s t-m" x="439" y="154" text-anchor="middle">context</text>'
    '<text class="t-s t-m" x="582" y="134" text-anchor="middle">one task</text>'
    '<text class="t-s t-m" x="582" y="152" text-anchor="middle">at a time</text>'
    '<line class="ln-d" x1="60" y1="108" x2="60" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="400" y1="108" x2="400" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="241" y1="172" x2="241" y2="226" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="250" y="212">executeBlocking</text>'
    '<rect class="box-ok" x="20" y="230" width="640" height="44" rx="8"/>'
    '<text class="t-s" x="340" y="257" text-anchor="middle">worker pool, the back office: 20 threads by default, for executeBlocking and WORKER verticles</text>'
    '</svg>'
)

price_java = """public class PriceDesk extends VerticleBase {
    @Override
    public Future<?> start() {
        return vertx.eventBus().<String>consumer("desk.price", msg ->
                vertx.executeBlocking(() -> PriceBook.postageCents(msg.body()), false)
                        .onSuccess(msg::reply)                        // back on this desk's context
                        .onFailure(e -> msg.fail(500, e.getMessage()))
        ).completion();
    }
}

vertx.deployVerticle(PriceDesk::new, new DeploymentOptions().setInstances(2));"""
price_kotlin = """class PriceDesk : VerticleBase() {
    override fun start(): Future<*> =
        vertx.eventBus().consumer<String>("desk.price") { msg ->
            val lookup = Callable<Long> { PriceBook.postageCents(msg.body()) }
            vertx.executeBlocking(lookup, false)
                .onSuccess { cents: Long -> msg.reply(cents) }        // back on this desk's context
                .onFailure { e -> msg.fail(500, e.message) }
        }.completion()
}

vertx.deployVerticle(::PriceDesk, DeploymentOptions().setInstances(2))"""

# ---------------------------------------------------------------- opening
OPENING = """Picture our post office once more. The clerks from Netty still sit behind the wall, each with a row of boxes, but the manager has added desks: a weighing desk, a price desk, a lost-property desk. Each desk has its own drawers, and the same clerk always serves it, one job at a time. Desks pass notes to each other through labeled mail tubes. Slow jobs go to the back office.

That post office is Vert.x, a toolkit for network programs that runs on Netty's event loops. Here is its surprise. A desk sends four slow jobs to a back office with twenty idle workers, and the answers still come back one at a time.

The trap is easy to fall into, because the obvious fix, sending slow jobs to the back office, looks finished: the warnings stop and the tests pass. Netty in practice: codecs, flow control and leaks finished our tour of Netty. In this lesson, we'll see which clerk serves each desk, send notes through the tubes, meet a floor manager, and find out why the back office works in single file. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with what's underneath. Vert.x 5.2.3, the version this track uses, runs on Netty 4.2.20. When you call `Vertx.vertx()`, it starts a group of Netty event loops, the clerks from lesson 3. An **event loop** is one thread, a single line of work inside your program, that watches many connections and runs their code one piece at a time. Vert.x starts two per core by default, 8 on a 4-core machine, named `vert.x-eventloop-thread-0` and up. A stack trace later in this lesson ends in `io.netty.channel.SingleThreadIoEventLoop.run`, the same loop class Netty uses.

So what does Vert.x add? Rules about who runs your code. The central one is the **context**: the home of a piece of code, which decides the thread that runs it. Most contexts are event-loop contexts, each tied to one event loop for life. In the post office, a context is the card on a desk that names its clerk.

When you register a handler, Vert.x remembers the current context, and every call of that handler runs there. A **handler**, in Vert.x, is any piece of your code that Vert.x calls when something happens: a request arrives, a timer fires, a note comes through a tube. The Vert.x docs make a promise about it. A handler is never executed concurrently, and, worker verticles aside, it always runs on the same event loop thread.

That promise is lesson 3's Netty rule, one channel and one loop, stretched over all your code: handlers for HTTP (the protocol of the web), timers and event-bus consumers alike. One clerk serves the desk, one job at a time, so nobody needs to lock the drawers. A field that only one context touches needs no `synchronized`.

The promise has a price you already know. While a handler runs, its clerk does nothing else, so every desk and every connection on that loop waits. We'll meet the floor manager who watches for that in the last section.

The second change is the API. A **future** is an object that will hold a result later; you attach code to it, and that code runs when the result arrives. Vert.x 4 offered two styles side by side: callbacks, where you pass a function into the call itself, and futures. Vert.x 5 kept only futures. Every asynchronous method returns an `io.vertx.core.Future`, and the callback versions are gone:

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

The Java error looks unrelated. The compiler, trying to help, found the one two-argument `listen` that's left, `listen(int, String)`, and complained that a `String` isn't a lambda. The same change replaced `executeBlocking(promise -> ...)` with a version that takes a `Callable` and returns a `Future`, which the last section puts to work.

**A context is the home of your code. Everything registered on it runs on its thread, one task at a time.**

A context needs something to belong to. In Vert.x, that something is usually a verticle."""

# ---------------------------------------------------------------- section 1
S1 = """A **verticle** is a class you deploy into Vert.x, and deploying it gives each instance its own context. It's a desk: a small, self-contained unit with its own drawers (its fields), its own handlers, and the card that names its clerk.

In Vert.x 5 you extend `VerticleBase` and return a `Future` from `start()`, so the deployment finishes only when your setup has. Here is a first weighing desk. It listens at the address `desk.weigh` and answers every parcel with a `JsonObject`, Vert.x's map of named values, that says it was accepted. This lesson's lab makes it stricter:

```java
public class WeighingDesk extends VerticleBase {
    @Override
    public Future<?> start() {
        return vertx.eventBus().<JsonObject>consumer("desk.weigh", msg ->
                msg.reply(new JsonObject().put("status", "ACCEPTED"))
        ).completion();                                  // done when the consumer is registered
    }
}

vertx.deployVerticle(WeighingDesk::new, new DeploymentOptions().setInstances(2));
```

```kotlin
class WeighingDesk : VerticleBase() {
    override fun start(): Future<*> =
        vertx.eventBus().consumer<JsonObject>("desk.weigh") { msg ->
            msg.reply(JsonObject().put("status", "ACCEPTED"))
        }.completion()                                   // done when the consumer is registered
}

vertx.deployVerticle(::WeighingDesk, DeploymentOptions().setInstances(2))
```

Read it from the bottom. We deploy two instances, so we pass a factory, a function that makes a new object each time, because each instance must be its own object. In 5.2.3 that factory is a `Supplier`, though the docs still say `Callable`. Each instance gets its own event-loop context, usually on different loops, which is how one verticle class uses several cores. Inside one instance, code never runs on two threads at once, so its fields need no locks.

Inside `start()`, the desk registers a **consumer**, a handler for notes that arrive at one address. Then it returns `completion()`, a future that completes once the consumer is registered, and Vert.x waits for it before it calls the deployment done.

Not every desk wants an event-loop clerk. The **threading model** in `DeploymentOptions` decides what kind of context a verticle gets. `ContextsDemo` deploys one verticle of each kind and prints where its `start()` runs:

```text
[EVENT_LOOP] start() on vert.x-eventloop-thread-0 eventLoopCtx=true workerCtx=false
[WORKER] start() on vert.x-worker-thread-0 eventLoopCtx=false workerCtx=true
[VIRTUAL_THREAD] start() on vert.x-virtual-thread-0 (virtual) eventLoopCtx=false workerCtx=false
```

`EVENT_LOOP`, the default, must never block. A `WORKER` verticle runs on the **worker pool**, a bounded pool of ordinary threads that are allowed to block, 20 of them by default. It still never runs on two threads at once, but one call can land on a different worker thread from the last. `VIRTUAL_THREAD` is new in Vert.x 5 and needs Java 21. The verticle runs on virtual threads, cheap threads that the JDK parks while they wait, and `future.await()` parks the virtual thread until the result arrives.

A virtual-thread verticle also runs one task at a time, with one catch from the docs. A field you read before an `await()` may have changed after it, because another task of the same verticle can run while you wait.

Here the desk picture breaks a little. A real desk keeps the same clerk all day. A worker desk can get a different clerk from the pool for each job, though never two at once, so it's single-threaded without being tied to one thread.

**Each verticle instance is one desk with one context. For more cores, deploy more instances.**

Desks need a way to talk without opening each other's drawers. That's the event bus."""

# ---------------------------------------------------------------- section 2
S2 = """The **event bus** is how verticles talk without sharing objects. There's one per `Vertx` instance, and an **address** is just a string, such as `desk.weigh`. In the post office, it's the system of mail tubes between desks, each tube labeled with a name. You can send a note in three ways:

- `send(address, msg)`: to one consumer at that address, chosen in turn (round-robin).
- `request(address, msg)`: to one consumer, and you get a `Future` of its reply.
- `publish(address, msg)`: to every consumer at that address.

`EventBusDemo` deploys two instances of a greeter desk and sends it four requests. Then it tries three addresses: one with nobody behind it, one that fails on purpose, and one that never answers:

```text
request greet #0 -> hello dev0 from instance#1 on vert.x-eventloop-thread-1
request greet #1 -> hello dev1 from instance#2 on vert.x-eventloop-thread-0
request greet #2 -> hello dev2 from instance#1 on vert.x-eventloop-thread-1
request nobody -> NO_HANDLERS code=-1 message=No handlers for address nobody
request fail -> RECIPIENT_FAILURE code=42 message=boom from instance#1
request silent (timeout 300 ms) -> TIMEOUT after 308 ms
```

The two instances took turns, each on its own loop: the round-robin at work. After them come the three ways a request can fail, each delivered as a `ReplyException` with a `failureType()`. `NO_HANDLERS` means nobody listens at the address, a tube that leads to an empty room. `RECIPIENT_FAILURE` means the consumer called `msg.fail(code, text)`, and you get its code and text. `TIMEOUT` means no reply came in time.

The silent consumer deserves a second look. It took the note and never wrote back, and the requester only found out because it had set a timeout of 300 ms. The default is 30 seconds, a long time to stand at a tube. Set one on every request with `new DeliveryOptions().setSendTimeout(...)`.

The reply comes back on the requester's context, not the consumer's. A worker verticle that sends a request handles the reply on a worker thread, and a virtual-thread verticle resumes on its virtual thread. So the promise of one desk and one clerk holds at both ends of a tube.

Two properties keep the event bus from being a message store. First, delivery is best effort: there's no saved copy and no retry, and the docs tell you to write consumers that can safely see the same message twice. Second, inside one JVM a message can be handed over by reference. A **codec** is the code that turns a message into bytes and back. With a custom local codec whose `transform` returns its argument, the consumer receives the very object you sent.

Here the tube picture breaks. A real tube carries the sheet away, while this one can leave the same sheet in both hands. Never change a message after you send it. Built-in codecs cover strings, numbers, `Buffer`, `JsonObject` and `JsonArray`; other types need a codec you register.

**The event bus carries quick notes between desks. Set a timeout on every request, and treat delivery as best effort.**

Notes, timers and requests all run on the clerks. So what happens when one of those jobs doesn't come back?"""

# ---------------------------------------------------------------- section 3
S3 = """Vert.x calls it the **golden rule**: don't block the event loop. Lesson 3 put it as the clerk who never stops to make a phone call. The Vert.x docs list what counts as a phone call: `Thread.sleep()`, waiting on a lock or a `synchronized` block, a long database operation, a complex calculation, spinning in a loop. They also give a budget. With one event loop and 10,000 HTTP requests a second, each request can take at most 0.1 ms.

Vert.x checks the rule for you, with a floor manager. A separate thread, `vertx-blocked-thread-checker`, walks past every event loop once a second. Each loop notes when its current task began, and the checker compares that with the clock. If a task has run for more than 2 seconds, it writes a warning in the log. Past 5 seconds, it adds the blocked thread's **stack trace**, the list of method calls the thread is inside. `BlockedThreadDemo` makes a clerk sleep for 6 seconds on an event loop:

```text
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 2773 ms, time limit is 2000 ms
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 3772 ms, time limit is 2000 ms
...
io.vertx.core.VertxException: Thread blocked
	at java.base/java.lang.Thread.sleep(Thread.java:509)
	at workbench.nio.l05.BlockedThreadDemo.lambda$main$0(BlockedThreadDemo.java:13)
	...
	at io.netty.channel.SingleThreadIoEventLoop.run(SingleThreadIoEventLoop.java:228)
```

The first warning came at 2.8 seconds, not 2.0, because the manager only walks past once a second. Search your logs for `has been blocked for`; the logger's name is `io.vertx.core.impl.BlockedThreadChecker`. And notice what the manager never does: interrupt. He writes it down and walks on, and the clerk stays on the phone.

The manager has one blind spot. He measures one task at a time, so ten 300 ms calls in a row hold a loop for 3 seconds and never produce a warning. Short blocking calls are the kind that never reach the logs.

For blocking work there's `executeBlocking`, the back office. It runs a `Callable`, a task that returns a value, on the worker pool, and completes a `Future` back on your context, so your own clerk writes the reply. `ExecuteBlockingDemo` tries it on an HTTP server with one event loop. Four requests arrive at once, and each needs a 500 ms lookup. The demo runs it three ways: blocking right on the loop, then `executeBlocking` with its default, then `executeBlocking(callable, false)`. One run on a busy 4-core machine printed:

```text
block-on-event-loop        4 requests x 500 ms -> 2201 ms, ran on [vert.x-eventloop-thread-0]
executeBlocking-ordered    4 requests x 500 ms -> 2012 ms, ran on [vert.x-worker-thread-0]
executeBlocking-unordered  4 requests x 500 ms ->  511 ms, ran on [vert.x-worker-thread-0, ..., vert.x-worker-thread-3]
```

The first line is the failure we expected: four lookups in a row on the clerk's own time. The second line is the surprise from the opening. The loop was free, so the floor manager had nothing to report, and yet the four lookups still ran one after another, all on `vert.x-worker-thread-0`. Twenty workers sat in the back office, and one of them did all the work.

The cause is one word in the docs: `executeBlocking` is **ordered** by default. Calls from the same context go into one queue and run in turn. Every request to one HTTP server shares that server's context, so every request joined the same queue. Pass `false` when the calls don't depend on each other, and they overlap: 511 ms, on four different workers.

**Moving a call to the back office frees the clerk. Pass `false`, or the calls still wait in single file.**

One last look at the back office itself. Its 20 threads are a bounded pool, like the ones in the executors track, so behind it you have a thread-per-request design again. That's fine, as long as you size it like one, with Little's law from lesson 1."""

ASIDE = {
 "title": "Why would anyone want single file?",
 "body": "Because order sometimes matters. Picture a desk that sends two jobs about the same parcel: first \"mark it weighed\", then \"mark it shipped\". If the back office ran both at once, the second could finish first and leave the record wrong. Ordered by default keeps the calls from one context in the order they were made, which is the safe choice when nobody has said otherwise. For independent lookups, like the price desk's, that safety only costs time, and `false` gives the time back."
}

# ---------------------------------------------------------------- closing
CLOSING = """We started with a post office of desks, each served by one clerk, with mail tubes between them and a back office for slow jobs. Vert.x names them: contexts on Netty's event loops, verticles, the event bus and `executeBlocking`. The floor manager reports long calls, and `false` keeps the back office from working in single file.

Now search your own Vert.x code for `executeBlocking(` with a single argument, and ask whether those calls really need to wait for each other.

Next, we'll meet Quarkus, a framework that runs on these same clerks. How does it decide, for each job, between the counter clerk, the back office and a cheap temporary helper?"""

L = {
 "id": "io-05",
 "title": "Vert.x: event loops, verticles and the golden rule",
 "minutes": 38,
 "goal": "By the end you can deploy verticles and say which thread runs each handler, send notes between them on the event bus with request, reply and publish, read Vert.x's blocked-thread warning, and move blocking work off the event loop without putting it in single file by accident.",
 "opening": OPENING,
 "warmup": {
  "q": "A Vert.x HTTP handler wraps its 500 ms database call in `vertx.executeBlocking(() -> db.lookup())`. Four requests arrive at the same moment on a server with one event loop. Roughly how long until all four are answered?",
  "options": [
   "About 500 ms: the four lookups run in parallel on the worker pool",
   "About 2,000 ms: by default executeBlocking runs calls from the same context one after another",
   "About 500 ms, but only if the worker pool has at least 4 threads",
   "It never finishes: executeBlocking deadlocks on a single event loop"
  ],
  "answer": 1,
  "why": "`executeBlocking` is ordered by default, and all requests to one HTTP server share its context. The event loop is free, but the four lookups queue behind each other in the back office. This lesson's demo measured 2,012 ms ordered and 511 ms with `executeBlocking(callable, false)`. The default worker pool has 20 threads, so the pool size isn't the limit."
 },
 "sections": [
  {
   "h": "One desk, one clerk: a Vert.x context on Netty's event loop",
   "body": S0,
   "try": {
    "title": "Hit the Vert.x 5 API change",
    "minutes": 2,
    "steps": [
     "In `ContextsDemo.java`, add one line after `Vertx vertx = Vertx.vertx();`: `vertx.createHttpServer().listen(8080, ar -> {});`.",
     "Predict whether it compiles. Then run the demo with the command below.",
     "Remove the line again."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "./gradlew :nio:demo -Pmain=workbench.nio.l05.ContextsDemo", "run": ""},
    "expect": "Compilation fails with `error: incompatible types: String is not a functional interface`. The callback version of `listen` no longer exists in Vert.x 5, so `javac` tries `listen(int, String)` and can't turn your lambda into a `String`."
   }
  },
  {
   "h": "Desks you deploy: verticles and their threading models",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Each desk instance has a context on one event loop. Contexts pass notes over the event bus, and blocking work goes to the worker pool and comes back to the same context."},
   "try": {
    "title": "Where does each desk run?",
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
    "expect": "The first line reports 8 event loops on 4 CPUs and a worker pool of 20. The three verticles start on `vert.x-eventloop-thread-0`, `vert.x-worker-thread-0` and a virtual thread, `vert.x-virtual-thread-0`. The `executeBlocking` callable runs on a worker thread, and `onSuccess` runs back on an event-loop thread: the context that made the call."
   }
  },
  {
   "h": "Notes through the tubes: request, reply and publish on the event bus",
   "body": S2,
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
    "expect": "The requests alternate between the two instances (1, 2, 1, 2 in every run for this lesson; the docs only promise a loose round-robin), each on its own event loop. `publish` prints two lines, one per instance, in either order. The failures come back as `NO_HANDLERS`, `RECIPIENT_FAILURE` with code 42, and `TIMEOUT` after about 300 ms. With 1,000 ms the timeout simply arrives later: the consumer still never replies."
   },
   "refs": [
    {"title": "Vert.x 5.2.3 event bus documentation (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/eventbus.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "The golden rule, the floor manager, and a back office that works in single file",
   "body": S3,
   "aside": ASIDE,
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
    "expect": "About 2,000 ms on the event loop thread, about 2,000 ms on one worker thread with the ordered default, and about 500 ms across four worker threads with `false`. Runs for this lesson measured 2,201, 2,012 and 511 ms, and later 2,408, 2,047 and 570 ms on a busier machine. The blocked-thread demo warns between 2 and 3 seconds in, once a second after that, and adds the `VertxException: Thread blocked` stack trace after 5 seconds. A 2,500 ms sleep gives zero or one warning, depending on when the checker happens to look."
   },
   "refs": [
    {"title": "Vert.x 5.2.3 core documentation: The Golden Rule (source)", "url": "https://raw.githubusercontent.com/eclipse-vertx/vert.x/5.2.3/vertx-core/src/main/asciidoc/index.adoc", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A desk that sends a blocking lookup to the back office",
  "java": {"title": "PriceDesk.java", "src": price_java},
  "kotlin": {"title": "PriceDesk.kt", "src": price_kotlin},
  "note": "Same Vert.x API, same threads at run time. Two Kotlin wrinkles came up while building this lesson's demos. `vertx.deployVerticle({ PriceDesk() }, options)` does not compile in Kotlin: `Deployable` is itself a single-method interface, so a bare lambda matches both overloads. Use a constructor reference (`::PriceDesk`) or `Supplier { PriceDesk() }`. And some Vert.x 5 signatures carry a `@Nullable` type annotation from `vertx-codegen`, which is not on the classpath, so Kotlin can fail with \"Type annotation class 'io.vertx.codegen.annotations.Nullable' of the inferred type is inaccessible\" when it infers a lambda's type. Giving the `Callable` and the lambda parameter explicit types, as above, avoids it. Java ignores the annotation."
 },
 "worked": {
  "title": "Unblock the price desk, step by step",
  "steps": [
   {"say": "The price desk looks postage up in the price book, a database call that takes 300 ms, right on its clerk's time. It works in a demo with one request. Under load, every handler on the same event loop waits behind it, and the floor manager stays silent: he measures one task at a time, and each 300 ms lookup is under his 2-second limit.",
    "code": "vertx.eventBus().<String>consumer(\"desk.price\", msg -> {\n    try {\n        msg.reply(PriceBook.postageCents(msg.body()));   // 300 ms on the event loop\n    } catch (InterruptedException e) {\n        msg.fail(500, \"interrupted\");\n    }\n});",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.eventBus().consumer<String>(\"desk.price\") { msg ->\n    msg.reply(PriceBook.postageCents(msg.body()))       // 300 ms on the event loop\n}"},
   {"say": "First attempt: send the lookup to the back office with the default `executeBlocking`. The loop is free now, but six requests at once still take about 6 x 300 ms. They all come from this consumer's context, and the default is ordered.",
    "code": "vertx.executeBlocking(() -> PriceBook.postageCents(msg.body()))   // ordered: one at a time\n        .onSuccess(msg::reply);",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.executeBlocking(Callable<Long> { PriceBook.postageCents(msg.body()) })   // ordered: one at a time\n    .onSuccess { cents: Long -> msg.reply(cents) }"},
   {"say": "Second attempt: unordered. The lookups now overlap on the worker pool, and the replies still come back on the consumer's context. The lab's test checks both halves: under 1,000 ms in total for six lookups, and an event-loop lag under 150 ms.",
    "code": "vertx.executeBlocking(() -> PriceBook.postageCents(msg.body()), false)   // independent calls\n        .onSuccess(msg::reply)\n        .onFailure(e -> msg.fail(500, e.getMessage()));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.executeBlocking(Callable<Long> { PriceBook.postageCents(msg.body()) }, false)   // independent calls\n    .onSuccess { cents: Long -> msg.reply(cents) }\n    .onFailure { e -> msg.fail(500, e.message) }"},
   {"say": "Another design makes the limit visible: turn the whole desk into a worker verticle and deploy as many instances as you want lookups at once. Each instance takes one note at a time on the worker pool, so four instances means at most four lookups in flight, a number you can match to the database's connections.",
    "code": "vertx.deployVerticle(BlockingPriceDesk::new, new DeploymentOptions()\n        .setThreadingModel(ThreadingModel.WORKER)   // may block\n        .setInstances(4));                          // at most 4 lookups at once",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "vertx.deployVerticle(::BlockingPriceDesk, DeploymentOptions()\n    .setThreadingModel(ThreadingModel.WORKER)       // may block\n    .setInstances(4))                               // at most 4 lookups at once"}
  ]
 },
 "lab": {
  "title": "Weigh parcels over the event bus, then unblock the price desk",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/WeighingDesk.java", f"{lab}/main/{P}/PriceDesk.java", f"{lab}/main/{P}/PriceBook.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l05.*'",
  "steps": [
   "Run the tests. All five fail: `WeighingDesk.start()` throws, so the deployment in `@BeforeEach` fails.",
   "Write `WeighingDesk.start()`: register a `JsonObject` consumer on `ADDRESS`, accept parcels up to `LIMIT_KG` with a reply `{status, parcel, thread}`, fail heavier ones with `msg.fail(413, \"too heavy\")`, and return the consumer's `completion()`. Four tests should pass.",
   "Read `priceLookupsDoNotBlockTheLoop`. It makes its own `Vertx` with one event loop, sends six requests to the price desk, and measures both the event-loop lag and the total time.",
   "Fix `PriceDesk` with `executeBlocking`. Try the one-argument version first and read the failure, then pass `false`."
  ],
  "hints": [
   "`msg.body().getDouble(\"kg\")` reads the weight; `Thread.currentThread().getName()` gives the `thread` value.",
   "`msg.fail(413, \"too heavy\")` reaches the requester as a `ReplyException` with `failureType()` `RECIPIENT_FAILURE` and `failureCode()` 413.",
   "`.onSuccess(msg::reply)` works because `reply` takes any `Object`.",
   "If a test times out after 30 seconds instead of failing fast, an assertion probably ran outside `tc.verify(...)`. The test file writes `@io.vertx.junit5.Timeout` in full because JUnit's own `@Timeout` has the same simple name."
  ],
  "done_when": "All five tests in `VerticleTest` pass, and you have seen the ordered `executeBlocking` fail the total-time assertion."
 },
 "drill": {
  "title": "Write a desk that sends a blocking call to the back office",
  "minutes": 5,
  "prompt": "Close the lab. Write a `VerticleBase` that answers requests on `desk.price` by running the blocking `PriceBook.postageCents(parcel)` off the event loop, in parallel across requests, and fails the message with code 500 on error. Then write the line that deploys two instances.",
  "answer": {"lang": "java", "src": price_java, "alt": {"lang": "kotlin", "src": price_kotlin}}
 },
 "recap": [
  "Vert.x runs on Netty event loops, two per core by default. A context ties your code to one thread, so a handler never runs at the same time as itself.",
  "Vert.x 5 is futures only: asynchronous methods return `Future`, the callback versions are gone, and `executeBlocking` takes a `Callable`.",
  "Each verticle instance is a desk with its own context: `EVENT_LOOP` (never block), `WORKER` (may block, still one task at a time) or `VIRTUAL_THREAD` (Java 21 or newer, `await()` parks).",
  "The event bus offers `send`, `request` and `publish` on string addresses. A request fails with `NO_HANDLERS`, `RECIPIENT_FAILURE` or `TIMEOUT` (30 s by default), and delivery is best effort.",
  "`executeBlocking` is ordered per context by default. Pass `false` for independent calls, or deploy a worker verticle with several instances.",
  "The limit: the blocked-thread checker only reports, only after 2 s, and only one task at a time. Short blocking calls never reach the logs, so the golden rule stays yours to keep."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "The weighing desk is deployed with `setInstances(4)` and default options. Its consumer adds one to a plain `int` field on every message. Is that safe?",
   "options": ["No: four threads can update the same field at once", "Yes: each instance is its own object with its own context, and a context never runs two handlers at once", "Only if the field is `volatile`", "Only for `WORKER` verticles"],
   "answer": 1,
   "why": "The factory creates four separate objects, so there are four separate fields, and each is only touched from its own context, one task at a time. `volatile` wouldn't make `++` atomic anyway, and worker verticles follow the same one-at-a-time rule."},
  {"q": "An HTTP handler wraps every database call in `vertx.executeBlocking(() -> db.query(...))`. Under load, latency climbs while the database is idle and the CPU is low. What is the most likely cause?",
   "options": ["`executeBlocking` is ordered by default, so calls from the server's context run one after another", "The worker pool has only one thread", "The event loop is blocked", "Database calls don't work on worker threads"],
   "answer": 0,
   "why": "All requests to one server share its context, and the default `executeBlocking` runs calls from a context in single file. The default worker pool has 20 threads, and the event loop is free, which is why there are no blocked-thread warnings. Pass `false`."},
  {"q": "A log line says `Thread vert.x-eventloop-thread-3 has been blocked for 2412 ms, time limit is 2000 ms`. What does Vert.x do to that thread?",
   "options": ["Interrupts it", "Replaces the event loop with a new one", "Nothing: it only logs, and adds a stack trace once the block passes 5 seconds", "Moves its handlers to another event loop"],
   "answer": 2,
   "why": "The blocked-thread checker only watches. It logs every second while the block lasts and adds the stack once it passes the warning-exception time (5 s by default). The handlers stay on their loop, so everything on it keeps waiting."},
  {"q": "From lesson 3: Vert.x event loops are Netty event loops. Which Netty rule explains why a Vert.x handler doesn't need a lock for its own fields?",
   "options": ["A channel stays on one event-loop thread for life, and that thread runs its events one at a time", "Netty copies every message before delivering it", "Netty's event loops are virtual threads", "`ByteBuf` is reference-counted"],
   "answer": 0,
   "why": "Vert.x stretches Netty's one-channel-one-loop rule over contexts: everything registered on a context runs on its thread, one task after another. Keeping the data on one thread is what removes the need for locks.",
   "from": "io-03"},
  {"q": "The weighing desk must tell three other desks (tracking, statistics, text messages) about each parcel it accepts, and it needs no answers. Which call fits?",
   "options": ["`eventBus().send(\"parcel.accepted\", parcel)`", "`eventBus().request(...)` once per listener", "`vertx.executeBlocking(...)` around each notice", "`eventBus().publish(\"parcel.accepted\", parcel)`"],
   "answer": 3,
   "why": "`publish` delivers to every consumer at the address. `send` would reach only one of them, chosen in turn, and `request` waits for replies nobody needs. Remember that delivery is best effort: if a notice must never be lost, the event bus is the wrong tool."}
 ],
 "flashcards": [
  {"front": "How many event loops does a default `Vertx` instance create?", "back": "Two per available processor: 8 on a 4-core machine."},
  {"front": "What is a Vert.x context?", "back": "The home of a piece of code: it fixes which thread runs it. A handler registered on a context always runs there, never at the same time as itself."},
  {"front": "When does Vert.x log a blocked event loop, and when does it add a stack trace (defaults)?", "back": "A warning once a task has run more than 2 s (checked every 1 s); the stack trace after 5 s. It only logs."},
  {"front": "Why can `executeBlocking(callable)` still run your calls one at a time?", "back": "It is ordered per context by default, so calls from the same context queue behind each other. Use `executeBlocking(callable, false)` for independent calls."},
  {"front": "The three `failureType()` values of a failed event-bus request?", "back": "`NO_HANDLERS` (nobody listens), `RECIPIENT_FAILURE` (the consumer called `fail`), `TIMEOUT` (no reply in time; 30 s by default)."},
  {"front": "`send` vs `request` vs `publish` on the event bus?", "back": "`send`: one consumer, in turn. `request`: one consumer, and you get a `Future` of the reply. `publish`: every consumer at the address."},
  {"front": "How do you deploy 4 instances of a verticle in Vert.x 5?", "back": "`vertx.deployVerticle(MyVerticle::new, new DeploymentOptions().setInstances(4))`: a `Supplier`, so each instance is a new object."}
 ],
 "terms": [
  {"term": "Verticle", "plain": "A class you deploy into Vert.x; each deployed instance gets its own context."},
  {"term": "Context", "plain": "Where a piece of Vert.x code runs: one event loop, a worker, or a virtual thread, one task at a time."},
  {"term": "Future", "plain": "An object that will hold a result later; code attached to it runs when the result arrives."},
  {"term": "Threading model", "plain": "The kind of context a verticle gets: `EVENT_LOOP`, `WORKER` or `VIRTUAL_THREAD`."},
  {"term": "Event bus", "plain": "Vert.x's messaging inside one program, between verticles, addressed by strings, best effort."},
  {"term": "Worker pool", "plain": "The pool of threads (20 by default) that runs blocking work and worker verticles."},
  {"term": "executeBlocking", "plain": "Runs a `Callable` on the worker pool and completes a `Future` back on your context."},
  {"term": "Blocked-thread checker", "plain": "A Vert.x thread that logs a warning when an event loop has been busy with one task for too long."}
 ],
 "explain_back": {
  "prompt": "A colleague wrapped four slow database calls in `executeBlocking` and is surprised that a burst of four requests still takes four times as long as one. Explain what a Vert.x context is, why their change didn't help, and what to do instead.",
  "answer": "A context is where Vert.x runs a piece of code: a handler registered on a context always runs there, one task at a time, like a desk that always has the same clerk. All requests to one HTTP server share that server's context. `executeBlocking` moves the callable to the worker pool, the back office, which frees the event loop, but by default it is ordered per context: Vert.x queues calls from the same context and runs them one after another. So the four calls still ran in sequence, just on a worker thread instead of the event loop. If the calls are independent, pass `false` as the second argument so they run in parallel on the worker pool, or deploy a worker verticle with several instances to get a clear limit on how many run at once. Either way, size that parallelism to the database's connection pool behind it."
 },
 "deeper": {
  "minutes": 10,
  "body": """Testing Vert.x code has its own traps, and the vertx-junit5 library exists because of them. A Vert.x callback runs on an event loop, after your test method has returned. If an assertion fails there, JUnit never sees it. The extension fixes that with `VertxTestContext`: the test passes only when you call `completeNow()` (or flag all checkpoints), and fails when you call `failNow(...)` or when an assertion inside `tc.verify(() -> ...)` throws.

This track's research ran the same failing assertion both ways. Outside `verify`, the test ran into the timeout after about 2.6 seconds with \"The test execution timed out. Make sure your asynchronous code includes calls to either VertxTestContext#completeNow(), VertxTestContext#failNow() or Checkpoint#flag()\", and the real `AssertionFailedError` was only printed to the log. Inside `verify`, it failed in 0.059 seconds with the actual assertion message. So every assertion in a callback goes inside `verify`, or inside `tc.succeeding(...)` and `tc.failing(...)`, which wrap it for you.

Other details from the vertx-junit5 docs: the default timeout is 30 seconds, overridden per test with `@io.vertx.junit5.Timeout` (written in full, to avoid JUnit's `@Timeout`). A `Vertx` injected into a `@BeforeAll` method is shared by the class, one injected into `@BeforeEach` is shared by that test and its `@AfterEach`, and injected instances are closed for you. `tc.checkpoint(n)` gives a counter that must be flagged `n` times, handy for testing `publish` to several consumers. And in Vert.x 5, clients rely on `Cleaner`, the JDK's way to run cleanup when an object becomes unreachable, so a client object you stop referring to can close its pool while a test still uses it. Keep clients in fields during tests.

One trap belongs outside tests too: waiting for a result on the event loop itself, with `future.toCompletionStage().toCompletableFuture().get()`. If the result needs that same loop to complete, the clerk waits for himself, and the call never returns. The test helpers in this lesson's lab call `get` only from the test's own thread, never from inside a handler."""
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
