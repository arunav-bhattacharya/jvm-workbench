import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l07"
K = "kotlin/workbench/nio/l07"
read = lambda p: (ROOT / p).read_text()

def box(x, y, w, h, cls, lines, first_cls="t-s"):
    out = [f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>']
    for i, line in enumerate(lines):
        c = first_cls if i == 0 else "t-s t-m"
        out.append(f'<text class="{c}" x="{x + w // 2}" y="{y + 20 + i * 17}" text-anchor="middle">{line}</text>')
    return "".join(out)

FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Jetty 12: an acceptor hands sockets to managed selectors. '
    'The adaptive execution strategy then runs non-blocking tasks on the selector thread, runs blocking tasks on the '
    'selector thread while a reserved thread takes over selecting, or dispatches them to the pool or to a virtual thread. '
    'One QueuedThreadPool provides all these threads">'
    + box(20, 16, 150, 44, "box", ["acceptor", "1 thread"])
    + '<line class="ln" x1="170" y1="38" x2="206" y2="38" marker-end="url(#arr)"/>'
    + box(210, 16, 230, 44, "box", ["ManagedSelector x 2", "1 thread each, epoll"])
    + '<line class="ln" x1="440" y1="38" x2="476" y2="38" marker-end="url(#arr)"/>'
    + box(480, 16, 180, 44, "box-b", ["AdaptiveExecution", "Strategy"])
    + '<line class="ln-a" x1="570" y1="60" x2="120" y2="106" marker-end="url(#arr)"/>'
    + '<line class="ln-a" x1="570" y1="60" x2="340" y2="106" marker-end="url(#arr)"/>'
    + '<line class="ln-a" x1="570" y1="60" x2="560" y2="106" marker-end="url(#arr)"/>'
    + box(20, 110, 200, 92, "box-ok", ["PC: Produce-Consume", "NON_BLOCKING task:", "runs on the selector", "thread itself"])
    + box(240, 110, 200, 92, "box-a", ["EPC: Execute-Produce-Consume", "BLOCKING, reserved thread", "free: selector thread runs", "it, reserved one selects"])
    + box(460, 110, 200, 92, "box", ["PEC: Produce-Execute-Consume", "BLOCKING, none reserved:", "dispatched to the pool", "or to a virtual thread"])
    + box(20, 232, 640, 56, "box-dim", ["QueuedThreadPool: min 8, max 200, unbounded queue",
                                        "it leases threads to the acceptor, the selectors and the reserved threads"])
    + '</svg>'
)

echo_java = """public class EchoHandler extends Handler.Abstract.NonBlocking {
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        Content.Source.asStringAsync(request, UTF_8).whenComplete((body, failure) -> {
            if (failure != null) {
                Response.writeError(request, response, callback, failure);
                return;
            }
            Content.Sink.write(response, true, "echo: " + body, callback);   // completes the callback
        });
        return true;   // "I took this request"; the response finishes later
    }
}"""
echo_kotlin = """class EchoHandler : Handler.Abstract.NonBlocking() {
    override fun handle(request: Request, response: Response, callback: Callback): Boolean {
        Content.Source.asStringAsync(request, UTF_8).whenComplete { body, failure ->
            if (failure != null) {
                Response.writeError(request, response, callback, failure)
            } else {
                Content.Sink.write(response, true, "echo: $body", callback)  // completes the callback
            }
        }
        return true   // "I took this request"; the response finishes later
    }
}"""

L = {
 "id": "io-07",
 "title": "Jetty 12: acceptors, selectors and thread pools",
 "minutes": 38,
 "goal": "By the end you can describe how a Jetty 12 server turns a socket into a handler call, write blocking and non-blocking core handlers, predict which thread the adaptive execution strategy uses for each, and move blocking handlers onto virtual threads.",
 "warmup": {
  "q": "A Jetty 12 server uses its default thread pool. A handler that extends `Handler.Abstract` (so it declares itself blocking) calls a 300 ms JDBC query. Which thread usually runs it?",
  "options": [
   "A worker thread taken from the pool's queue, like Tomcat does for every request",
   "The selector thread that read the request, while a spare reserved thread takes over the selecting",
   "A virtual thread, because Jetty 12 enables them by default",
   "The acceptor thread that accepted the connection"
  ],
  "answer": 1,
  "why": "Jetty's adaptive execution strategy prefers to run a task on the thread that produced it, while its data is still in that CPU's cache. For a blocking task it does that only when a reserved thread is free to take over selecting, the Execute-Produce-Consume mode. The demo in this lesson shows `epcRunTask` in the handler's stack. Virtual threads are off unless you configure them."
 },
 "sections": [
  {
   "h": "A Jetty server is connectors, handlers and one thread pool",
   "body": """Jetty's documentation describes a `Server` as the component that links a collection of `Connector`s and a collection of `Handler`s, with threads from one `ThreadPool` doing all the work. Every thread you'll see in this lesson comes from that one pool.

The connector you'll use is the `ServerConnector`. It has two kinds of threads. Acceptors (one by default) call `accept()` and hand each new socket on. A `SelectorManager` owns several `ManagedSelector`s, and each `ManagedSelector` is one thread running a `java.nio` `Selector`: the select loop from lesson 2, so `epoll` on Linux. By default there are `max(1, min(cpus / 2, maxThreads / 16))` selectors, and the docs give a rule of thumb that one selector manages 1,000 to 5,000 sockets. Inside, each socket becomes an `EndPoint` that moves bytes and a `Connection` that parses a protocol (HTTP/1.1, HTTP/2, WebSocket).

```java
Server server = new Server(new QueuedThreadPool());   // one pool for everything
ServerConnector connector = new ServerConnector(server);
connector.setHost("127.0.0.1");
connector.setPort(8080);
server.addConnector(connector);
server.setHandler(new LedgerHandler(300));
server.start();
```

```kotlin
val server = Server(QueuedThreadPool())                // one pool for everything
val connector = ServerConnector(server).apply { host = "127.0.0.1"; port = 8080 }
server.addConnector(connector)
server.handler = LedgerHandler(300)
server.start()
```

The default pool is a `QueuedThreadPool` with at least 8 and at most 200 threads. The connector leases some of them for good: this section's demo, on 4 CPUs, shows 1 acceptor, 2 selectors and 3 leased threads. The pool must have room for those plus at least one thread for requests, and the docs suggest sizing `maxThreads` as the leased threads plus the threads you want for handlers.

Two pool rules surprise people. The pool's queue must be unbounded. Jetty sometimes needs to run its own tasks to make progress (HTTP/2, for example, must write in order to read), and the docs warn that a rejected task can make the server grind to a halt. Limit load with a QoS handler instead. And a platform thread costs about 1 MiB of native memory, so 200 threads is a real number.""",
   "try": {
    "title": "Count what a default server starts",
    "minutes": 3,
    "steps": [
     "Open `JettyThreadsDemo.java` (or `JettyThreadsDemo.kt`). From the formula above, predict the selector count on your machine with the default pool of 200.",
     "Run it and compare. Then predict the selectors for `new QueuedThreadPool(12)` on 4 CPUs.",
     "Ignore the last two lines for now; the third section explains them."
    ],
    "code": {"lang": "java", "title": "JettyThreadsDemo.java", "src": read(f"{lab}/demo/{P}/JettyThreadsDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.JettyThreadsDemo",
             "file": f"{lab}/demo/{P}/JettyThreadsDemo.java",
             "alt": {"lang": "kotlin", "title": "JettyThreadsDemo.kt", "src": read(f"{lab}/demo/{K}/JettyThreadsDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.JettyThreadsDemoKt",
                     "file": f"{lab}/demo/{K}/JettyThreadsDemo.kt"}},
    "expect": "On 4 CPUs: `acceptors=1 selectors=2` and `QueuedThreadPool min=8 max=200 started=8 leased=3` (one acceptor, two selectors). With a 12-thread pool the formula gives `max(1, min(2, 12 / 16 = 0))` = 1 selector. Jetty also logs a few INFO lines when servers start and stop."
   },
   "refs": [
    {"title": "Jetty 12.1 programming guide: HTTP server (connectors, acceptors, selectors)", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "The core Handler API is asynchronous",
   "body": """Jetty 12 rewrote the API at its center. In Jetty 11 a handler had a blocking signature built on Servlet types. In Jetty 12 it is `boolean handle(Request request, Response response, Callback callback)`, and the migration guide spells out the new contract: return `true` to say you handled the request, and then complete the `Callback`, by succeeding or failing it, possibly long after `handle` has returned. Return `false` and Jetty moves on; with no other handler, the client gets a 404.

A blocking handler is the simple case: do the work, write the response with `Content.Sink.write(response, true, text, callback)`, which completes the callback once the bytes are written, and return `true`. A non-blocking handler reads the body without waiting for it:

```java
public class EchoHandler extends Handler.Abstract.NonBlocking {
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        Content.Source.asStringAsync(request, UTF_8).whenComplete((body, failure) -> {
            if (failure != null) {
                Response.writeError(request, response, callback, failure);
                return;
            }
            Content.Sink.write(response, true, "echo: " + body, callback);   // completes the callback
        });
        return true;   // "I took this request"; the response finishes later
    }
}
```

```kotlin
class EchoHandler : Handler.Abstract.NonBlocking() {
    override fun handle(request: Request, response: Response, callback: Callback): Boolean {
        Content.Source.asStringAsync(request, UTF_8).whenComplete { body, failure ->
            if (failure != null) {
                Response.writeError(request, response, callback, failure)
            } else {
                Content.Sink.write(response, true, "echo: $body", callback)  // completes the callback
            }
        }
        return true   // "I took this request"; the response finishes later
    }
}
```

The request body is a `Content.Source`: you read it in `Content.Chunk`s, which are slices of Jetty's network buffers, passed up without copying. The rule echoes Netty's reference counting from lesson 4: every chunk you `read()` must be released, except failure chunks, and a source must be read to the end or failed, or Jetty can leak its buffers. Helpers such as `asStringAsync` do the reading and releasing for you.

The superclass is a declaration. `Handler.Abstract` says \"I may block\" (`InvocationType.BLOCKING`). `Handler.Abstract.NonBlocking` says \"I never block\", and Jetty uses that promise to pick a thread, as the next section shows.

The Servlet API still exists, as a layer on top of this core. Jetty 12 ships it in separate environments named after Jakarta EE versions: `ee8`, `ee9`, `ee10`, and since 12.1 `ee11`, which brings Servlet 6.1. The docs list the core API's strengths as simple, minimal and asynchronous, with low overhead because you only configure what you use.""",
   "try": {
    "title": "Break the handler contract",
    "minutes": 3,
    "steps": [
     "In `JettyThreadsDemo`, change the `Blocking` handler's body to just `return false;` (delete the `Content.Sink.write` line). Predict what the first GET prints.",
     "Put it back. Now think it through without running it: what does a client see if a handler returns `true` and never completes the callback?"
    ],
    "expect": "With `return false` the request finds no handler and Jetty answers with a 404 page, which the demo prints as the body. A handler that returns `true` and never completes the callback leaves the request open: the client waits until its own timeout or Jetty's idle timeout ends the connection. Returning `true` is a promise to finish the response exactly once."
   },
   "refs": [
    {"title": "Jetty 11 to 12 migration guide (Handler API)", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/11-to-12.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "One strategy, three modes: who runs your handler",
   "body": """When a selector finds a readable socket, it produces a task: \"run this connection's `onFillable`\", which parses the request and calls your handler. Jetty's `AdaptiveExecutionStrategy` then decides which thread consumes that task, and it has three main modes, named in the Jetty docs:

- Produce-Consume (PC): the selector thread runs the task itself. No hand-off and warm CPU caches, but every other socket on that selector waits. The docs say this mode is equivalent to the event loop of Node.js or Netty.
- Produce-Execute-Consume (PEC): the task goes to the thread pool. No head-of-line blocking, but a hand-off, a queue and cold caches on another core.
- Execute-Produce-Consume (EPC): the selector thread runs the task, and a reserved thread, one the pool keeps idle and ready, takes over the selecting. Warm caches and no stall.

The choice follows the task's invocation type. A `NON_BLOCKING` task runs in PC mode. A `BLOCKING` task runs in EPC mode when a reserved thread is available, and in PEC mode when none is. Jetty's source notes that this strategy used to be called \"Eat What You Kill\": the hunter eats what it caught. This section's demo reads the mode from each handler's own stack:

```text
default pool, BLOCKING       -> qtp1636182655-25 :: AdaptiveExecutionStrategy.epcRunTask
default pool, NON_BLOCKING   -> qtp2144284609-37 :: AdaptiveExecutionStrategy.pcRunTask
reservedThreads=0, BLOCKING  -> qtp826865256-50 :: no strategy frame: dispatched to the pool
virtual threads, BLOCKING    -> jetty-vt-1 :: VirtualThread.run
```

Now you can see why the handler's declaration matters. `NonBlocking` is a promise that lets Jetty run your code on the selector thread, exactly like a Netty event loop. Break the promise with a JDBC call and every connection on that selector stalls; the docs call it a risk of server lock-up. Containers combine their children's types, so one blocking handler anywhere in a handler tree makes the whole tree blocking. That's safe, but it costs the PC fast path.

Compare that with the other servers you know. Netty-based servers, including Vert.x and Quarkus, run every handler in PC mode on the event loop, and offloading is your job. Tomcat's NIO connector watches sockets with a poller and processes requests on its executor threads (200 by default). Jetty sits in between: it chooses per task, from what your handler declares.""",
   "figure": {"svg": FIG, "caption": "A selector produces a task per ready connection; the adaptive strategy runs it in place, runs it in place while a reserved thread selects, or hands it off."},
   "try": {
    "title": "Read the mode from the stack",
    "minutes": 4,
    "steps": [
     "Open `StrategyDemo.java` (or `StrategyDemo.kt`). For each of the four setups, predict the mode: PC, EPC, PEC, or a virtual thread.",
     "Run it with the command below.",
     "Explain the third line: why does `setReservedThreads(0)` change the mode for a blocking handler?"
    ],
    "code": {"lang": "java", "title": "StrategyDemo.java", "src": read(f"{lab}/demo/{P}/StrategyDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.StrategyDemo",
             "file": f"{lab}/demo/{P}/StrategyDemo.java",
             "alt": {"lang": "kotlin", "title": "StrategyDemo.kt", "src": read(f"{lab}/demo/{K}/StrategyDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.StrategyDemoKt",
                     "file": f"{lab}/demo/{K}/StrategyDemo.kt"}},
    "expect": "Blocking on the default pool: `epcRunTask`. Non-blocking: `pcRunTask`, on the selector's own thread. With no reserved threads, a blocking task can't use EPC, because nobody could take over selecting, so it is dispatched to the pool and the handler's stack has no strategy frame at all (PEC). With virtual threads, the PEC path hands the task to a virtual thread, `jetty-vt-1`."
   },
   "refs": [
    {"title": "Jetty 12.1 programming guide: threading architecture", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Virtual threads in Jetty 12",
   "body": """Jetty 12 offers virtual threads in two ways, and they behave very differently.

The first keeps the `QueuedThreadPool` and gives it a virtual threads executor:

```java
QueuedThreadPool pool = new QueuedThreadPool(12);
pool.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("ledger-vt-"));
```

```kotlin
val pool = QueuedThreadPool(12)
pool.virtualThreadsExecutor = VirtualThreads.getNamedVirtualThreadsExecutor("ledger-vt-")
```

When the strategy picks PEC for a blocking task, it sends the task to a virtual thread instead of a pool thread. Turning this on sets the reserved threads to zero by default, so blocking tasks always take that path. Acceptors, selectors and non-blocking tasks stay on platform threads. The demo in the first section showed it: the blocking handler ran on `jetty-vt-0` and the non-blocking one on a `qtp` thread.

The second is `VirtualThreadPool`, which replaces the pool. Despite its name, it doesn't pool virtual threads. It starts a new virtual thread for each task and limits how many tasks run at once with a semaphore, 200 permits by default. With it there are no `qtp` threads at all: the acceptor and the selectors run on it too.

This section's demo sends 40 concurrent requests to a handler that blocks for 300 ms:

```text
QueuedThreadPool(max=12)               40 x 300 ms -> 1,681 ms, at most 10 in the handler at once
QueuedThreadPool(max=12) + virtual     40 x 300 ms ->   326 ms, at most 40 in the handler at once
VirtualThreadPool(maxThreads=8)        40 x 300 ms -> 2,122 ms, at most 7 in the handler at once
```

Twelve platform threads minus the leased ones left about ten for requests. The virtual executor let all 40 wait at once. The `VirtualThreadPool` with 8 permits was slowest, because its permits cap concurrency below even the platform pool, and only 7 ever reached the handler at once, so at least one permit was held by something else at the time.

One version note from the Jetty docs. Jetty dedicates a thread to each `Selector`, and up to Java 23, calling `Selector.select()` from a virtual thread pins its carrier; from Java 24 it doesn't. On 21 to 23, then, a server running everything on virtual threads loses one carrier per selector. That is one more reason to prefer the first option: `QueuedThreadPool` plus the virtual threads executor keeps selectors on platform threads and runs only your blocking handlers virtually. And as in every lesson of this track, virtual threads don't protect your downstream: 40 handlers at once means 40 JDBC calls at once.""",
   "try": {
    "title": "Three pools, one load",
    "minutes": 4,
    "steps": [
     "Open `JettyLoadDemo.java` (or `JettyLoadDemo.kt`). Predict the time and the concurrency for each pool. Use Little's law: 40 requests, 300 ms each, and the number of threads that can run handlers.",
     "Run it.",
     "Change `new VirtualThreadPool(8)` to `new VirtualThreadPool(64)` and predict again before running."
    ],
    "code": {"lang": "java", "title": "JettyLoadDemo.java", "src": read(f"{lab}/demo/{P}/JettyLoadDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.JettyLoadDemo",
             "file": f"{lab}/demo/{P}/JettyLoadDemo.java",
             "alt": {"lang": "kotlin", "title": "JettyLoadDemo.kt", "src": read(f"{lab}/demo/{K}/JettyLoadDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l07.JettyLoadDemoKt",
                     "file": f"{lab}/demo/{K}/JettyLoadDemo.kt"}},
    "expect": "About 1.7 s with at most 9 or 10 at once on the 12-thread pool (four rounds of about ten requests), about 330 ms with all 40 at once with the virtual executor, and about 2.1 s with at most 7 at once on `VirtualThreadPool(8)` (this track's research measured 2.6 to 2.8 s, 0.53 s and 3.0 s for 500 ms requests). With 64 permits, the virtual pool lets all 40 requests run at once and finishes in about the same time as the virtual executor."
   }
  }
 ],
 "analogy": "Jetty's adaptive strategy is a chef who also receives the deliveries. When a delivery arrives, the quickest thing is to cook it at once, while the ingredients are still warm, which is Produce-Consume. If the dish takes long (a blocking task), the chef first waves over a standby cook to take over receiving deliveries, then cooks: Execute-Produce-Consume. With no standby cook free, the order goes onto the kitchen's ticket rail for whoever is free next: Produce-Execute-Consume. The analogy breaks where Jetty trusts the order slip: a dish marked \"quick\" (`NonBlocking`) is always cooked at the door, even if it turns out to take an hour, and then nobody receives deliveries.",
 "in_your_world": "You may run Jetty without choosing it: as the embedded server in a service, inside a test harness such as WireMock, or behind a framework. For a payments team the useful knobs are few. Declare honestly whether your handlers block. Size the `QueuedThreadPool` as leased threads plus request threads, and never give it a bounded queue. Use a QoS handler to shed load, not the pool. On JDK 21 or newer, turn on the virtual threads executor for a blocking service, and keep a real limit (the JDBC pool, a semaphore) in front of the database and the card issuer, because Jetty will now happily run 2,000 handlers at once.",
 "mistake": "The most damaging mistake is extending `Handler.Abstract.NonBlocking` because it sounds faster, then calling JDBC, a synchronous HTTP client or anything else that waits. The superclass is a promise: Jetty runs the handler on the selector thread in Produce-Consume mode, so every other connection on that selector waits behind your query, which is the event-loop failure from lessons 3 and 5. Extend `Handler.Abstract` for anything that might block. A close second is giving the `QueuedThreadPool` a bounded queue to protect the server: the docs say the queue must be unbounded, because Jetty's own progress depends on tasks that must not be rejected.",
 "compare": {
  "title": "An asynchronous echo handler in Java and Kotlin",
  "java": {"title": "EchoHandler.java", "src": echo_java},
  "kotlin": {"title": "EchoHandler.kt", "src": echo_kotlin},
  "note": "The two are the same handler at runtime. The Kotlin version shows two small differences. The `BiConsumer` passed to `whenComplete` becomes a two-parameter lambda, and `if`/`else` replaces the early `return`, because a bare `return` inside a Kotlin lambda would return from `handle` itself and doesn't compile here (you'd need `return@whenComplete`). Kotlin also lets you write Jetty's setters as properties (`server.handler = ...`, `pool.virtualThreadsExecutor = ...`). The threading is identical: the lambda runs on whichever thread completes the body future, which can be a different thread from the one that called `handle`."
 },
 "worked": {
  "title": "Move a blocking ledger service onto virtual threads",
  "steps": [
   {"say": "A Jetty service serves balances with a 300 ms JDBC query per request on a pool of 50. Under a burst of 400 requests the tail latency explodes. Little's law: about 45 threads can run handlers, so 400 requests need 400 / 45 × 0.3 s, about 2.7 s, to drain, while the CPU is nearly idle.",
    "code": "QueuedThreadPool pool = new QueuedThreadPool(50);       // about 45 left after leasing\nServer server = new Server(pool);\nserver.setHandler(new LedgerHandler(300));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "val pool = QueuedThreadPool(50)                         // about 45 left after leasing\nval server = Server(pool)\nserver.handler = LedgerHandler(300)"},
   {"say": "Keep the handler and give blocking tasks virtual threads. The pool keeps its platform threads for acceptors and selectors; every blocking handler gets a virtual thread, so the burst no longer queues for threads.",
    "code": "QueuedThreadPool pool = new QueuedThreadPool(50);\npool.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor(\"ledger-vt-\"));",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "val pool = QueuedThreadPool(50)\npool.virtualThreadsExecutor = VirtualThreads.getNamedVirtualThreadsExecutor(\"ledger-vt-\")"},
   {"say": "Now the queue has moved to the database. 400 handlers all ask the connection pool, which has 20 connections. That is the right place for the wait, but give it a timeout, so a slow database turns into fast errors instead of 400 stuck requests.",
    "code": "HikariConfig config = new HikariConfig();\nconfig.setMaximumPoolSize(20);              // the real concurrency limit\nconfig.setConnectionTimeout(500);           // ms to wait for a connection, then fail",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "val config = HikariConfig().apply {\n    maximumPoolSize = 20                    // the real concurrency limit\n    connectionTimeout = 500                 // ms to wait for a connection, then fail\n}"},
   {"say": "Check the health endpoint is still cheap. It extends `Handler.Abstract.NonBlocking`, so it keeps running on platform threads in Produce-Consume mode, which the lab's last test asserts. If someone later adds a database ping to it, change its superclass in the same commit.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build Jetty core handlers and move blocking ones to virtual threads",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/PaymentServer.java", f"{lab}/main/{P}/LedgerHandler.java", f"{lab}/main/{P}/StatusHandler.java", f"{lab}/main/{P}/EchoHandler.java"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l07.*'",
  "steps": [
   "Run the tests. All five fail.",
   "Fix `StatusHandler`'s superclass so it declares itself non-blocking. Write `LedgerHandler.serve`: sleep `delayMs`, write the body from its Javadoc with `Content.Sink.write`, return `true`. The invocation-type test should pass.",
   "Write `PaymentServer.start`: `new Server(pool)`, a `ServerConnector` on host 127.0.0.1 and port 0, `setHandler`, `start()`. The platform-pool test should pass: read its assertion on `maxConcurrent()`.",
   "Write `EchoHandler.handle` with `Content.Source.asStringAsync` and return `true` right away.",
   "Write `PaymentServer.virtualQueuedThreadPool`. Run all five tests. The last one shows that `StatusHandler` stays on platform threads even with virtual threads enabled."
  ],
  "hints": [
   "`Thread.currentThread().isVirtual()` gives the `virtual=` part of the ledger body.",
   "If the echo test hangs and then fails, check that every path through the `whenComplete` lambda completes the callback, either with `Content.Sink.write(..., callback)` or with `Response.writeError(...)`.",
   "With `QueuedThreadPool(12)` the connector leases one acceptor and one selector thread, and one more is kept as a reserved thread, so fewer than 12 handlers ever run at once.",
   "If the last test fails with `virtual=true`, `StatusHandler` still extends `Handler.Abstract`, so Jetty treats it as blocking and sends it to a virtual thread."
  ],
  "done_when": "All five tests in `JettyTest` pass."
 },
 "drill": {
  "title": "Write an asynchronous Jetty handler from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write a Jetty 12 core handler that reads the whole request body without blocking and answers `echo: <body>`. Which superclass, what does `handle` return, and who completes the callback?",
  "answer": {"lang": "java", "src": echo_java + "\n// Superclass: Handler.Abstract.NonBlocking (it never blocks).\n// handle returns true at once; Content.Sink.write or Response.writeError completes the callback later.",
             "alt": {"lang": "kotlin", "src": echo_kotlin + "\n// Superclass: Handler.Abstract.NonBlocking (it never blocks).\n// handle returns true at once; Content.Sink.write or Response.writeError completes the callback later."}}
 },
 "recap": [
  "A Jetty `Server` links connectors and handlers to one `ThreadPool`. A `ServerConnector` runs acceptors (1 by default) and `ManagedSelector`s, one thread each, `max(1, min(cpus / 2, maxThreads / 16))` by default.",
  "`QueuedThreadPool` defaults to 8 to 200 threads; connectors lease some for good, and its queue must stay unbounded. Shed load with a QoS handler.",
  "The core API is `boolean handle(Request, Response, Callback)`: return `true` and complete the callback exactly once, maybe later. Read bodies as `Content.Source` chunks and release them, or use helpers like `asStringAsync`.",
  "`AdaptiveExecutionStrategy` runs `NON_BLOCKING` tasks on the selector thread (PC), `BLOCKING` ones on the selector thread with a reserved thread taking over (EPC), or hands them off (PEC).",
  "`setVirtualThreadsExecutor` sends only blocking tasks to virtual threads; `VirtualThreadPool` runs everything virtually and caps tasks with a semaphore. Before Java 24, selectors on virtual threads pin carriers.",
  "Netty-based servers always run handlers on the event loop; Tomcat runs requests on executor threads; Jetty chooses per task from what the handler declares."
 ],
 "quiz": [
  {"q": "A Jetty 12 handler extends `Handler.Abstract.NonBlocking` and calls a 200 ms REST client synchronously. What happens under load?",
   "options": ["Nothing special: Jetty moves it to a worker because the call blocks", "It runs on a selector thread in Produce-Consume mode, so other connections on that selector wait behind each call", "Jetty throws an exception because non-blocking handlers can't block", "It runs on a virtual thread, so blocking is free"],
   "answer": 1,
   "why": "`NonBlocking` is a declaration Jetty trusts. It runs the task on the selector thread with no hand-off, like a Netty event loop. Jetty can't see that the call blocks, and virtual threads only get blocking tasks."},
  {"q": "A team gives Jetty's `QueuedThreadPool` a bounded queue of 1,000 tasks so it rejects work under overload. What do the Jetty docs say?",
   "options": ["Good practice: a bounded queue protects the heap", "Fine, as long as the bound is above maxThreads", "The queue must be unbounded: Jetty needs its own tasks to run to make progress, and rejecting one can stall the server; use a QoS handler instead", "Only HTTP/1.1 connectors support bounded queues"],
   "answer": 2,
   "why": "Jetty submits internal tasks to the same pool, for example HTTP/2 must be able to write in order to read. A rejected internal task can stall connections. Limit concurrency with a QoS handler, which works at the request level."},
  {"q": "On a 4-CPU machine, `new Server(new QueuedThreadPool(64))` with one default `ServerConnector`. How many selector threads?",
   "options": ["1", "2", "4", "8"],
   "answer": 1,
   "why": "`max(1, min(cpus / 2, maxThreads / 16))` = `max(1, min(2, 4))` = 2. Selector count follows CPUs and pool size, not connections."},
  {"q": "From lesson 2: a Jetty `ManagedSelector` wraps a `java.nio.channels.Selector`. Why does it run on its own dedicated thread?",
   "options": ["A selector's selected-key set isn't safe for concurrent use, so one thread owns each selector and its loop", "`Selector.select()` must run on the main thread", "Selectors are faster on platform threads", "The JDK allows only one selector per thread"],
   "answer": 0,
   "why": "The `Selector` Javadoc says the selector is thread-safe but its key sets are not. One owner thread per selector is the pattern every framework uses: Netty's event loop, Vert.x's event loop, Jetty's `ManagedSelector`.",
   "from": "io-02"},
  {"q": "You enable `QueuedThreadPool.setVirtualThreadsExecutor(...)` on JDK 21. Which of these runs on a virtual thread?",
   "options": ["The acceptor", "The `ManagedSelector` loops", "A `Handler.Abstract.NonBlocking` health check", "A `Handler.Abstract` handler that calls JDBC"],
   "answer": 3,
   "why": "Only tasks the strategy runs in PEC mode, which are blocking tasks, go to the virtual threads executor. Acceptors, selectors and non-blocking handlers stay on platform threads, which also avoids selectors pinning carriers before Java 24."}
 ],
 "flashcards": [
  {"front": "What does a Jetty 12 `ServerConnector` run on threads?", "back": "Acceptors (1 by default) that accept sockets, and `ManagedSelector`s, one thread each, running a `java.nio` select loop."},
  {"front": "Default number of selectors in a Jetty 12 `ServerConnector`?", "back": "`max(1, min(cpus / 2, maxThreads / 16))`: 2 on 4 CPUs with the default 200-thread pool."},
  {"front": "The Jetty 12 core handler contract?", "back": "`boolean handle(Request, Response, Callback)`: return `true` if you handle it, then complete the callback exactly once, possibly after `handle` returns. `false` means \"not mine\"."},
  {"front": "PC, EPC, PEC in one line each?", "back": "PC: the selector thread runs the task. EPC: the selector thread runs it while a reserved thread takes over selecting. PEC: the task is handed to the pool (or a virtual thread)."},
  {"front": "When does Jetty run a task in Produce-Consume mode?", "back": "When the task is `NON_BLOCKING`, for example a handler that extends `Handler.Abstract.NonBlocking`."},
  {"front": "`QueuedThreadPool.setVirtualThreadsExecutor` vs `VirtualThreadPool`?", "back": "The first sends only blocking tasks to virtual threads and keeps selectors on platform threads. The second runs everything on new virtual threads with a semaphore cap (200 by default)."},
  {"front": "Why must Jetty's thread pool queue be unbounded?", "back": "Jetty submits its own tasks to the pool to make progress (HTTP/2 must write to read); rejecting one can stall the server. Use a QoS handler to limit load."}
 ],
 "terms": [
  {"term": "Connector", "plain": "The Jetty component that accepts connections and turns bytes into protocol messages."},
  {"term": "Acceptor", "plain": "A thread that calls `accept()` and hands each new socket to a selector."},
  {"term": "ManagedSelector", "plain": "Jetty's wrapper around one `java.nio` `Selector`, run by one thread."},
  {"term": "Invocation type", "plain": "A task's or handler's declaration: `BLOCKING`, `NON_BLOCKING` or `EITHER`."},
  {"term": "Reserved thread", "plain": "An idle pool thread kept ready so a selector thread can hand off selecting and run a task itself."},
  {"term": "AdaptiveExecutionStrategy", "plain": "Jetty's per-task choice between running a task in place and handing it off (formerly Eat What You Kill)."},
  {"term": "Callback", "plain": "The object a Jetty handler completes, by success or failure, when its response is done."}
 ],
 "explain_back": {
  "prompt": "A colleague says \"Jetty is just a thread-per-request server like Tomcat\". Explain what Jetty 12 actually does between reading a socket and calling a handler, and why a handler's superclass matters.",
  "answer": "A Jetty connector has an acceptor thread that accepts sockets and selector threads, each running a java.nio select loop. When a selector sees a readable connection, it produces a task that parses the request and calls the handler, and the adaptive execution strategy decides who runs that task. If the handler declares itself non-blocking (`Handler.Abstract.NonBlocking`), the selector thread runs it directly, like an event loop, with no hand-off. If it declares itself blocking (`Handler.Abstract`), the selector thread still runs it when a reserved thread is free to take over selecting, which keeps caches warm; otherwise the task goes to the thread pool, or to a virtual thread if that executor is configured. So Jetty is neither purely thread-per-request nor purely an event loop: it chooses per task, based on the declaration. That's why the superclass matters. A handler that claims to be non-blocking and then calls JDBC stalls every connection on its selector, while an honest blocking declaration costs at most a thread hand-off."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three details from the Jetty 12.1 sources and docs round out the picture.

There is a fourth mode. `AdaptiveExecutionStrategy`'s Javadoc names Produce-Invoke-Consume for tasks whose invocation type is `EITHER`: they are run with `Invocable.invokeNonBlocking`, meaning the task is asked to proceed in a non-blocking way if it can. The selection order is PC for a non-blocking task, EPC if a reserved thread is available, PIC for `EITHER`, and PEC otherwise. Strategies also nest: the selector's strategy produces connection tasks, and an HTTP/2 connection runs its own strategy over its streams.

Jetty also has the reverse problem of a declared handler. `Request.demand(Runnable)`, which asks Jetty to call you back when more body content is available, treats a plain lambda as blocking. If your callback really is non-blocking, pass an `Invocable.Task` that declares so, or Jetty may hand it off to another thread for nothing.

On sizing: each connector leases a thread per acceptor and per selector, and `ReservedThreadExecutor` leases its reserved threads, by default `max(1, ceilToNextPowerOfTwo(min(cpus, maxThreads / 8)))`, or 0 once a virtual threads executor is set. The docs suggest `maxThreads` = leased threads + threads you want for handlers, and remind you that idle threads shrink back according to `idleTimeout`. Raising `maxThreads` to thousands is the old fix for blocking handlers; on JDK 21 or newer, the virtual threads executor is the cheaper one.

HTTP/3 shows how far the connector abstraction stretches: Jetty implements HTTP/3 in Java but uses the native Quiche library for QUIC, through JNA, with a connector that has zero acceptors and a single selector over a `DatagramChannel`."""
 },
 "sources": [
  {"title": "Jetty 12.1 programming guide: threading architecture", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/threads.adoc"},
  {"title": "Jetty 12.1 programming guide: I/O architecture (EndPoint, Connection, Content.Source)", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/arch/io.adoc"},
  {"title": "Jetty 12.1 programming guide: HTTP server", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/server/http.adoc"},
  {"title": "Jetty 11 to 12 migration guide", "url": "https://github.com/jetty/jetty.project/blob/jetty-12.1.14/documentation/jetty/modules/programming-guide/pages/migration/11-to-12.adoc"},
  {"title": "Tomcat 11 HTTP connector configuration (docs source)", "url": "https://raw.githubusercontent.com/apache/tomcat/11.0.x/webapps/docs/config/http.xml"}
 ]
}

out = ROOT / "content/lessons/io-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
