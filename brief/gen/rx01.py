import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l01"
PK = "kotlin/workbench/reactive/l01"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l01."

S1 = """There are two ways to move data from a producer to a consumer.

In **pull**, the consumer asks for the next item when it is ready: `Iterator.next()`, `ResultSet.next()`, `KafkaConsumer.poll()`. The consumer sets the pace. The cost is a waiting thread: while the next item isn't there yet, the consumer's thread sits and does nothing.

In **push**, the producer calls the consumer when an item exists: a listener, a callback, `CompletableFuture.thenAccept`. Nobody waits. The cost is that the producer sets the pace, and the consumer has no way to say "slow down".

Push breaks when the producer is faster than the consumer. Here is a shape that shows up in payment services:

```java
// the listener returns at once, so the poll loop keeps fetching
void onMessage(PaymentEvent e) {
    ledgerWriter.execute(() -> ledger.write(e));   // a fixed pool: its queue has no limit
}
```

```kotlin
// the listener returns at once, so the poll loop keeps fetching
fun onMessage(e: PaymentEvent) {
    ledgerWriter.execute { ledger.write(e) }       // a fixed pool: its queue has no limit
}
```

Kafka itself is pull, and this code turns it into push. The listener returns in microseconds, so `poll()` keeps fetching, and the executor's `LinkedBlockingQueue` grows. With 10,000 events a second coming in and 2,000 going out, the heap gains 8,000 objects every second. Nothing fails at first. Then the garbage collector runs all the time, latency climbs, and the pod is killed for running out of memory.

**Backpressure** is the fix: the consumer tells the producer how much it can take, and the producer never sends more. Reactive Streams makes this part of the protocol. The subscriber calls `request(n)`, and the publisher may then push at most `n` items. If items are ready, they arrive at once, as with pull. If they aren't, the publisher pushes them when they appear, as with push. The Reactor docs call this a push-pull hybrid.

When the consumer can't keep up, a system has four honest options: slow the producer down, buffer up to a limit, drop items, or fail. An unbounded queue is a fifth option that only looks like a choice. Reactive Streams makes you pick one of the four on purpose. Lesson 7 of this track, "Backpressure in practice", shows how to pick in Reactor."""

S2 = """Reactive Streams is a small spec: four interfaces, seven methods, and a list of numbered rules. Here is all of the API:

```java
public interface Publisher<T>    { void subscribe(Subscriber<? super T> s); }
public interface Subscriber<T>   { void onSubscribe(Subscription s);
                                   void onNext(T item);
                                   void onError(Throwable t);
                                   void onComplete(); }
public interface Subscription    { void request(long n); void cancel(); }
public interface Processor<T, R> extends Subscriber<T>, Publisher<R> { }
```

```kotlin
// the same four interfaces, written as Kotlin declarations
interface Publisher<T>    { fun subscribe(s: Subscriber<in T>) }
interface Subscriber<T>   { fun onSubscribe(s: Subscription)
                            fun onNext(item: T)
                            fun onError(t: Throwable)
                            fun onComplete() }
interface Subscription    { fun request(n: Long); fun cancel() }
interface Processor<T, R> : Subscriber<T>, Publisher<R>
```

Every method returns `void` (`Unit` in Kotlin), so every call is a one-way message. Java's `Subscriber<? super T>` is Kotlin's `Subscriber<in T>`: a publisher of payments also accepts a subscriber of any supertype, such as a `Subscriber<Object>` that logs everything. A subscriber sees signals in one fixed order, which the spec writes as `onSubscribe onNext* (onError | onComplete)?`. That means one `onSubscribe`, then any number of `onNext`, then at most one terminal signal. After `onError` or `onComplete`, nothing else arrives.

You will rarely write these by hand. Reactor, RxJava, Mutiny (the library behind Quarkus' reactive APIs) and the reactive database drivers all implement them, and the rules are why one library can subscribe to another. The rules you will actually meet:

- **1.1** A publisher never sends more `onNext` signals than were requested in total.
- **1.3** Signals to one subscriber are serial: never two at the same time. So a subscriber needs no locks for its own fields.
- **1.9** `onSubscribe` comes before any other signal.
- **2.13** Subscriber methods must return normally. The only exception allowed is a `NullPointerException` for a `null` argument. A subscriber that wants to stop must call `cancel()`, not throw.
- **2.8** A subscriber must accept `onNext` calls that arrive after it cancelled. Items already requested may still be on their way.
- **3.9** `request(n)` with `n <= 0` must produce `onError(IllegalArgumentException)`.
- **3.17** Demand of `Long.MAX_VALUE` may be treated as "unbounded". That is a subscriber saying it wants no backpressure at all.

Rule 3.9 is a good place to see that the spec and a library can differ. The JDK's publisher follows it. Reactor's operators only log a bad request at DEBUG level and send nothing, so a broken subscriber just waits forever. A stream that silently stalls is the symptom to remember."""

S3 = """Java 9 copied the four interfaces into the JDK as nested types of `java.util.concurrent.Flow`: `Flow.Publisher`, `Flow.Subscriber`, `Flow.Subscription` and `Flow.Processor`. Same methods, same rules, different package. Reactor works with `org.reactivestreams.Publisher`, so you bridge with `JdkFlowAdapter` (in reactor-core) or `FlowAdapters` (in the reactive-streams jar).

The JDK ships one real implementation, `SubmissionPublisher`. You hand it items from ordinary code, and it delivers them to each subscriber asynchronously:

```java
try (var publisher = new SubmissionPublisher<PaymentEvent>()) {
    publisher.subscribe(new BatchingSubscriber<>(32, ledger::write));
    for (PaymentEvent e : events) {
        publisher.submit(e);       // blocks while this subscriber is 256 items behind
    }
}   // close(): subscribers get onComplete after their buffered items
```

```kotlin
SubmissionPublisher<PaymentEvent>().use { publisher ->
    publisher.subscribe(BatchingSubscriber(32, ledger::write))
    for (e in events) {
        publisher.submit(e)        // blocks while this subscriber is 256 items behind
    }
}   // close(): subscribers get onComplete after their buffered items
```

The parts that matter:

- Each subscriber gets its own buffer. Its maximum size defaults to `Flow.defaultBufferSize()`, which is 256.
- Delivery runs on an `Executor`. On JDK 21 the default is `ForkJoinPool.commonPool()`. Pass your own executor for anything slow.
- `submit(item)` **blocks the producer's thread** when a subscriber's buffer is full. This is where backpressure turns into something an ordinary thread can feel. In the first Try it, `submit` is what slowed the producer down to the ledger writer's pace.
- `offer(item, onDrop)` never blocks. When a buffer is full it calls your drop handler, and returns a negative number for each drop. There is also an `offer` with a timeout.
- If a subscriber method throws, the publisher cancels that subscription.
- `close()` completes every subscriber. `closeExceptionally(t)` sends them `onError(t)`.

Blocking in `submit` is fine on a dedicated producer thread or a virtual thread. It is a bad idea on an event-loop thread, where it stalls everything else on that loop.

`SubmissionPublisher` is a good teaching tool and a decent in-process fan-out, but it has no operators. You can't `map`, retry or time out a `Flow.Publisher` without writing the code yourself. That is the job Reactor does, starting with lesson 2 of this track."""

S4 = """Here is what blocking IO costs. A thread sends a request to the card issuer and waits 120 ms for the answer. During those 120 ms it holds about a megabyte of stack and does no work. A pool of 200 such threads can have 200 calls in flight. By Little's law that caps you at 200 / 0.12 s, about 1,670 calls a second, however idle the CPUs are.

Non-blocking IO removes the wait. An event-loop thread (Netty, or the JDK's NIO selectors) hands the request to the operating system and moves on to other work. When the response bytes arrive, the loop runs a callback to continue. A handful of threads can keep thousands of calls in flight. Reactive libraries are the programming model for that callback world: a `Mono` is the one reply you are waiting for, a `Flux` is a stream of them, and demand travels with the data.

It has real costs. The Spring Framework docs say it plainly: "Reactive and non-blocking generally do not make applications run faster." The gain is "the ability to scale with a small, fixed number of threads and less memory", and you only see it when calls have latency. You also pay with stack traces that show operator internals instead of your code, a learning curve the whole team has to climb, and one strict rule: nothing on an event loop may block. A single JDBC call on an event-loop thread stalls every request that loop serves.

Virtual threads (JDK 21, JEP 444) changed the trade. A blocked virtual thread unmounts from its carrier, so blocking code no longer burns a platform thread per call. For request and response over JDBC, a plain blocking style on virtual threads is now the simpler default. Reactive still earns its place where the problem is a stream: backpressure, cancellation that travels upstream, rate-limited fan-out, retries and timeouts as composable operators. Lesson 8 of this track comes back to this choice with the Spring team's own words."""

SVG = ('<svg viewBox="0 0 640 380" role="img" aria-label="Sequence of signals: the subscriber subscribes, receives onSubscribe, '
       'requests 2, gets two onNext signals, requests 2 more, gets one onNext and then onComplete">'
       '<rect class="box-b" x="60" y="14" width="180" height="40" rx="8"/><text class="t" x="150" y="39" text-anchor="middle">Publisher</text>'
       '<rect class="box-a" x="400" y="14" width="180" height="40" rx="8"/><text class="t" x="490" y="39" text-anchor="middle">Subscriber</text>'
       '<line class="ln-d" x1="150" y1="54" x2="150" y2="366"/><line class="ln-d" x1="490" y1="54" x2="490" y2="366"/>'
       '<text class="t-s t-m" x="590" y="74" text-anchor="middle">owed</text>')
rows = [
    (92, "subscribe(subscriber)", "left", "ln", ""),
    (130, "onSubscribe(subscription)", "right", "ln", "0"),
    (168, "request(2)", "left", "ln-a", "2"),
    (206, "onNext(auth-1)", "right", "ln", "1"),
    (244, "onNext(auth-2)", "right", "ln", "0"),
    (282, "request(2)", "left", "ln-a", "2"),
    (320, "onNext(auth-3)", "right", "ln", "1"),
    (358, "onComplete()", "right", "ln", ""),
]
for y, label, d, cls, owed in rows:
    x1, x2 = (490, 156) if d == "left" else (150, 484)
    tcls = "t-s t-code t-a" if cls == "ln-a" else "t-s t-code"
    SVG += f'<line class="{cls}" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'
    SVG += f'<text class="{tcls}" x="320" y="{y - 7}" text-anchor="middle">{label}</text>'
    if owed:
        SVG += f'<text class="t-s t-a" x="590" y="{y + 4}" text-anchor="middle">{owed}</text>'
SVG += '</svg>'

W0K = """class ExportSubscriber : Flow.Subscriber<Row> {
    private lateinit var s: Flow.Subscription

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(Long.MAX_VALUE)
    }
    override fun onNext(row: Row) {
        if (row.amount == null) throw IllegalStateException("bad row ${row.id}")
        file.append(row.toCsv())
    }
    override fun onError(t: Throwable) = s.request(1)   // "try again"
    override fun onComplete() = file.close()
}"""
W2K = """class ExportSubscriber : Flow.Subscriber<Row> {
    private lateinit var s: Flow.Subscription
    private var stopped = false
    @Volatile var failure: Throwable? = null

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)                               // 1. bounded demand
    }
    override fun onNext(row: Row) {
        if (stopped) return                        // 2. rule 2.8: late items may still come
        if (row.amount == null) {
            stopped = true
            failure = IllegalStateException("bad row ${row.id}")
            s.cancel()                             // 3. stop by cancelling, never by throwing
            return
        }
        file.append(row.toCsv())
        s.request(1)                               // 4. ask for the next one when done
    }
    override fun onError(t: Throwable) { failure = t; file.close() }   // 5. terminal: just clean up
    override fun onComplete() = file.close()
}"""
DK = """class StopAtError : Flow.Subscriber<String> {
    private lateinit var s: Flow.Subscription
    private var stopped = false

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)
    }
    override fun onNext(item: String) {
        if (stopped) return                        // rule 2.8
        if (item.startsWith("ERR")) {
            stopped = true
            s.cancel()                             // rule 2.13: cancel, don't throw
            return
        }
        println(item)
        s.request(1)
    }
    override fun onError(t: Throwable) = t.printStackTrace()
    override fun onComplete() = println("done")
}"""
CK = """publisher.subscribe(object : Flow.Subscriber<Payment> {
    private lateinit var s: Flow.Subscription

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)                     // ask for the first item
    }
    override fun onNext(p: Payment) {    // non-null type: Kotlin itself throws NPE on null
        ledger.write(p)                  // slow work
        s.request(1)                     // only now ask for the next
    }
    override fun onError(t: Throwable) = log.error("feed failed", t)
    override fun onComplete() = log.info("feed done")
})"""

L = {
 "id": "rx-01",
 "title": "Why reactive: push, pull and backpressure",
 "minutes": 35,
 "goal": "By the end you can explain how Reactive Streams demand (`request(n)`) stops a fast producer from drowning a slow consumer, name the rules a subscriber must follow, and write a `Flow.Subscriber` that asks for items in batches.",
 "warmup": {
  "q": "A Kafka listener receives 10,000 payment events a second and hands each one to a fixed thread pool that writes 2,000 a second to the ledger. What happens over the next few minutes?",
  "options": [
   "The listener slows down to 2,000 a second on its own",
   "The pool rejects the extra events with RejectedExecutionException",
   "Events pile up in the pool's queue, about 8,000 more each second, until the heap runs out",
   "Kafka stops delivering because the consumer group sees a slow member"
  ],
  "answer": 2,
  "why": "`Executors.newFixedThreadPool` uses an unbounded `LinkedBlockingQueue`, so it never rejects and never pushes back. The listener returns at once, `poll()` keeps fetching, and nothing tells the producer to slow down. Kafka would slow down if the listener itself blocked, but handing off to an unbounded queue hides the slowness until memory runs out."
 },
 "sections": [
  {
   "h": "Pull, push, and the consumer that drowns",
   "body": S1,
   "try": {
    "title": "Drown a ledger writer, then rescue it",
    "minutes": 4,
    "steps": [
     "Read `DrowningDemo` below. It sends 100,000 events to a writer that needs 10 microseconds per event, first with plain push and then through a `SubmissionPublisher` with `request(1)`.",
     "Predict for each version: how long will the producer take, and how many events will be waiting in memory when it finishes?",
     "Run it (Java or Kotlin, they print the same). Then change `writeToLedger` to wait 20,000 nanoseconds and run again. Which number changes in each line?"
    ],
    "code": {"lang": "java", "title": "DrowningDemo.java", "src": read(f"{lab}/demo/{P}/DrowningDemo.java"),
             "run": DEMO + "DrowningDemo", "file": f"{lab}/demo/{P}/DrowningDemo.java",
             "alt": {"lang": "kotlin", "title": "DrowningDemo.kt", "src": read(f"{lab}/demo/{PK}/DrowningDemo.kt"),
                     "run": DEMO + "DrowningDemoKt", "file": f"{lab}/demo/{PK}/DrowningDemo.kt"}},
    "expect": "With plain push the producer finishes in tens of milliseconds and almost everything is still queued (one run here: 40 ms, 1,347 written, 98,653 waiting). With demand the producer takes as long as the writer needs (1,805 ms here) and never more than about 256 events wait, which is the publisher's buffer. With a 20 microsecond write, the plain version leaves even more events queued, and the demand version simply takes about twice as long. Its memory stays flat."
   }
  },
  {
   "h": "Reactive Streams: the contract in seven methods",
   "body": S2,
   "figure": {"svg": SVG, "caption": "Demand goes up as request(n), data comes down as onNext. The publisher never sends more than it is owed."},
   "try": {
    "title": "Break rule 3.9 on purpose",
    "minutes": 3,
    "steps": [
     "`RequestZeroDemo` has a subscriber that calls `request(0)` in `onSubscribe`. It subscribes to a JDK `SubmissionPublisher` and to a Reactor `Flux.range(1, 3)`.",
     "Predict what each publisher sends back. Then run it.",
     "Change `request(0)` to `request(2)`. Predict again: does each stream complete?"
    ],
    "code": {"lang": "java", "title": "RequestZeroDemo.java", "src": read(f"{lab}/demo/{P}/RequestZeroDemo.java"),
             "run": DEMO + "RequestZeroDemo", "file": f"{lab}/demo/{P}/RequestZeroDemo.java",
             "alt": {"lang": "kotlin", "title": "RequestZeroDemo.kt", "src": read(f"{lab}/demo/{PK}/RequestZeroDemo.kt"),
                     "run": DEMO + "RequestZeroDemoKt", "file": f"{lab}/demo/{PK}/RequestZeroDemo.kt"}},
    "expect": "The JDK publisher follows rule 3.9 and prints `onError java.lang.IllegalArgumentException: non-positive subscription request`. Reactor prints nothing at all: the stream just stalls. With `request(2)`, the JDK publisher sends its one item and then `onComplete`, because it was closed. Reactor sends 1 and 2 and then stops without completing, because nobody asked for 3. Unmet demand never times out by itself."
   },
   "refs": [{"title": "Reactive Streams for the JVM: specification and rules", "url": "https://github.com/reactive-streams/reactive-streams-jvm/blob/master/README.md", "kind": "docs"}]
  },
  {
   "h": "java.util.concurrent.Flow and SubmissionPublisher",
   "body": S3,
   "try": {
    "title": "Fill a two-slot buffer",
    "minutes": 4,
    "steps": [
     "`SaturationDemo` builds a `SubmissionPublisher` with a buffer of 2 and a subscriber that never calls `request`. It then offers 10 items.",
     "Predict what each `offer` returns and how many items are dropped. Run it.",
     "Now replace the `offer(...)` call with `publisher.submit(i)` and keep the assignment to `lag`. Predict, then run it. Stop it with Ctrl+C."
    ],
    "code": {"lang": "java", "title": "SaturationDemo.java", "src": read(f"{lab}/demo/{P}/SaturationDemo.java"),
             "run": DEMO + "SaturationDemo", "file": f"{lab}/demo/{P}/SaturationDemo.java",
             "alt": {"lang": "kotlin", "title": "SaturationDemo.kt", "src": read(f"{lab}/demo/{PK}/SaturationDemo.kt"),
                     "run": DEMO + "SaturationDemoKt", "file": f"{lab}/demo/{PK}/SaturationDemo.kt"}},
    "expect": "The first two offers return a lag of 1 and 2. Offers 3 to 10 each return -1, the drop handler runs eight times, and the last line is `dropped 8 of 10, lag 2`. Nothing is delivered, because nothing was requested. With `submit` the program hangs on item 3: the buffer is full, the subscriber never asks for more, and `submit` waits for space. That hang is backpressure reaching your thread."
   },
   "refs": [
    {"title": "Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html", "kind": "docs"},
    {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html", "kind": "docs"}
   ]
  },
  {
   "h": "What non-blocking buys you, and what it costs",
   "body": S4,
   "refs": [{"title": "Spring Framework reference: WebFlux overview (applicability and performance)", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html", "kind": "read"}]
  }
 ],
 "analogy": "Think of a kitchen and a waiter. With plain push the kitchen sends out every plate the moment it is cooked, and the waiter stacks them on a side table that keeps getting longer. With pull the waiter walks to the pass and stands there until a plate is ready. Reactive Streams is the waiter saying \"I can carry three\": the kitchen sends up to three plates, at once if they are ready or as soon as they are, and never a fourth until the waiter asks again. The analogy breaks at the end of the shift: a real kitchen notices when the waiter quits, but a publisher only stops when the subscriber calls `cancel()`.",
 "in_your_world": "Your Kafka consumers already pull, which is why a slow listener slows `poll()` and eventually triggers a rebalance. The danger is the moment you hand records to something that doesn't push back: an unbounded executor queue, a `CompletableFuture.runAsync` per record, or a reactive pipeline that calls `request(Long.MAX_VALUE)`. The same applies to a Temporal activity that streams settlement rows into an in-memory list, or a Quarkus endpoint that relays an issuer's event stream to clients. Ask one question of each: when the next stage is slow, what makes the stage before it wait?",
 "mistake": "The most common mistake is asking for everything. `subscription.request(Long.MAX_VALUE)` in `onSubscribe`, or a Reactor `subscribe(item -> ...)` with no demand control, tells the publisher \"no backpressure, please\". People do it because it is the shortest code that works in a test with ten items. In production the slow stage then buffers without limit or drops data. Request a bounded batch and ask for more as you finish, as in the lab.",
 "compare": {
  "title": "A one-at-a-time Flow.Subscriber in Java and Kotlin",
  "java": {"title": "OneAtATime.java", "src": "publisher.subscribe(new Flow.Subscriber<Payment>() {\n    private Flow.Subscription s;\n\n    public void onSubscribe(Flow.Subscription s) {\n        this.s = s;\n        s.request(1);                    // ask for the first item\n    }\n    public void onNext(Payment p) {\n        ledger.write(p);                 // slow work\n        s.request(1);                    // only now ask for the next\n    }\n    public void onError(Throwable t) { log.error(\"feed failed\", t); }\n    public void onComplete() { log.info(\"feed done\"); }\n});"},
  "kotlin": {"title": "OneAtATime.kt", "src": CK},
  "note": "The protocol code is the same in both languages; three Kotlin details change how it feels. `lateinit var s` replaces the nullable field you would otherwise check. `object : Flow.Subscriber<Payment>` is Kotlin's anonymous class. And because `onNext(p: Payment)` declares a non-null parameter, the Kotlin compiler adds a null check to it: a publisher that sends `null` gets a `NullPointerException`, which is exactly what rule 2.13 asks for, with no code from you. Don't confuse `java.util.concurrent.Flow` with `kotlinx.coroutines.flow.Flow`. The Kotlin one is a coroutine stream with no `request(n)` at all: `emit` suspends until the collector has finished with the item, so a producer can never run ahead. The Spring docs call Kotlin Flow push-based and Reactor's `Flux` a push-pull hybrid. The coroutines track covers Flow, and `kotlinx-coroutines-reactive` converts between the two with `asFlow()` and `asPublisher()`."
 },
 "worked": {
  "title": "Find the rule violations in a hand-written subscriber",
  "steps": [
   {"say": "A teammate wrote this subscriber for a statement export. It reads rows from a reactive database driver and writes them to a file. Read it and look for broken rules before reading on.",
    "code": "class ExportSubscriber implements Flow.Subscriber<Row> {\n    private Flow.Subscription s;\n\n    public void onSubscribe(Flow.Subscription s) {\n        this.s = s;\n        s.request(Long.MAX_VALUE);\n    }\n    public void onNext(Row row) {\n        if (row.amount() == null) throw new IllegalStateException(\"bad row \" + row.id());\n        file.append(row.toCsv());\n    }\n    public void onError(Throwable t) { s.request(1); }   // \"try again\"\n    public void onComplete() { file.close(); }\n}", "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Three problems. `request(Long.MAX_VALUE)` turns backpressure off (rule 3.17), so a slow disk makes the driver buffer rows. Throwing from `onNext` breaks rule 2.13: the publisher may cancel, log, or do something you didn't expect. And calling `request` from `onError` breaks rule 2.3: after a terminal signal the subscription is dead.", "code": "", "lang": ""},
   {"say": "Fix them one by one. Ask for one item at a time. Turn a bad row into a cancel plus a recorded error. Treat `onError` as the end.",
    "code": "class ExportSubscriber implements Flow.Subscriber<Row> {\n    private Flow.Subscription s;\n    private boolean stopped;\n    volatile Throwable failure;\n\n    public void onSubscribe(Flow.Subscription s) {\n        this.s = s;\n        s.request(1);                          // 1. bounded demand\n    }\n    public void onNext(Row row) {\n        if (stopped) return;                   // 2. rule 2.8: late items may still come\n        if (row.amount() == null) {\n            stopped = true;\n            failure = new IllegalStateException(\"bad row \" + row.id());\n            s.cancel();                        // 3. stop by cancelling, never by throwing\n            return;\n        }\n        file.append(row.toCsv());\n        s.request(1);                          // 4. ask for the next one when done\n    }\n    public void onError(Throwable t) { failure = t; file.close(); }   // 5. terminal: just clean up\n    public void onComplete() { file.close(); }\n}", "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "This is correct but chatty: one `request(1)` call per row. Each call crosses into the publisher, and some publishers do real work per request. The lab asks for the same correctness with demand in batches, which is what Reactor's own operators do internally.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A Flow.Subscriber that asks in batches",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/BatchingSubscriber.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l01.*'",
  "steps": [
   "Run the tests once. All five fail with `TODO` errors, and the two `SubmissionPublisher` tests also time out after 3 seconds.",
   "Write `onSubscribe`: keep the subscription and call `request(batchSize)`. If a subscription is already stored, cancel the new one and return.",
   "Write `onNext`: reject `null`, pass the item to the handler, count it, and call `request(batchSize)` again only when a whole batch has been handled.",
   "Make a throwing handler safe: catch it, cancel the subscription, record the error, count down `done`, and ignore any later `onNext`.",
   "Write `onError` and `onComplete` so `await` returns. Run the tests until all five pass."
  ],
  "hints": [
   "You need two more fields: an `int` counting items in the current batch, and a `boolean` that says you have cancelled. Signals are serial (rule 1.3), so plain fields are safe here.",
   "The request test expects exactly `[4, 4, 4]` for 10 items in batches of 4. If you see eleven requests, you are asking after every item. If you see `[4]`, you never reset the counter.",
   "`Objects.requireNonNull(item)` is all rule 2.13 asks for on `null`."
  ],
  "done_when": "All five tests in `BatchingSubscriberTest` pass."
 },
 "drill": {
  "title": "Write a one-at-a-time subscriber from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a `Flow.Subscriber<String>` that requests one item at a time, prints each item, and cancels the subscription (without throwing) at the first item that starts with `\"ERR\"`. Then compare with the answer. Did you guard against items that arrive after the cancel?",
  "answer": {"lang": "java", "src": "class StopAtError implements Flow.Subscriber<String> {\n    private Flow.Subscription s;\n    private boolean stopped;\n\n    public void onSubscribe(Flow.Subscription s) {\n        this.s = s;\n        s.request(1);\n    }\n    public void onNext(String item) {\n        if (stopped) return;                 // rule 2.8\n        if (item.startsWith(\"ERR\")) {\n            stopped = true;\n            s.cancel();                      // rule 2.13: cancel, don't throw\n            return;\n        }\n        System.out.println(item);\n        s.request(1);\n    }\n    public void onError(Throwable t) { t.printStackTrace(); }\n    public void onComplete() { System.out.println(\"done\"); }\n}", "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "Pull lets the consumer set the pace but parks a thread while it waits. Push never waits but lets a fast producer drown a slow consumer.",
  "Backpressure means the consumer says how much it can take (`request(n)`) and the producer never sends more (rule 1.1).",
  "Signals arrive as `onSubscribe onNext* (onError | onComplete)?`, one at a time. Subscribers stop by calling `cancel()`, never by throwing.",
  "`java.util.concurrent.Flow` is the same contract in the JDK. `SubmissionPublisher.submit` blocks the producer when a subscriber's 256-item buffer is full; `offer` drops instead.",
  "Reactor ignores `request(0)` silently, while the JDK reports it as `onError`. A stream with unmet demand just stalls.",
  "Non-blocking IO scales with few threads when calls have latency. It does not make code faster, and virtual threads now cover plain request and response well."
 ],
 "quiz": [
  {"q": "A subscriber calls `request(3)` in `onSubscribe` and never calls `request` again. The publisher has 10 items ready. What does the subscriber receive?",
   "options": ["All 10 items, because the publisher has them ready", "3 items, then `onComplete`", "3 items, and then nothing until it requests more", "1 item, because each `onNext` needs its own request"],
   "answer": 2,
   "why": "Rule 1.1 caps `onNext` signals at the total requested. The publisher has more to send, so it may not complete either. It waits for more demand. Having items ready doesn't let a publisher exceed demand."},
  {"q": "Inside `onNext`, your handler fails to parse a row. What should the subscriber do?",
   "options": ["Throw the exception so the publisher can call `onError`", "Call `subscription.cancel()`, record the error, and return normally", "Call `request(0)` to signal a problem", "Ignore it and call `request(1)` to get the next row"],
   "answer": 1,
   "why": "Rule 2.13 says subscriber methods must return normally. Cancelling is the only legal way for a subscriber to stop the stream. Throwing leaves the reaction up to the publisher (`SubmissionPublisher` cancels; other publishers may just log), and `request(0)` is itself a rule violation."},
  {"q": "A producer thread calls `SubmissionPublisher.submit(event)` in a loop. One subscriber is slow and its buffer of 256 is full. What happens?",
   "options": ["`submit` blocks until that subscriber has room", "`submit` drops the event and returns -1", "`submit` throws `IllegalStateException`", "The event goes to the other subscribers only"],
   "answer": 0,
   "why": "`submit` blocks while any subscriber's buffer is full, which slows the producer to the slowest subscriber's pace. `offer` is the method that drops instead (and returns a negative number). Pick `offer` with a drop handler if the producer must never wait."},
  {"q": "Which of these is the strongest reason to choose a non-blocking, reactive design for a service?",
   "options": ["Each request will finish faster", "It is easier to debug than blocking code", "It can keep thousands of slow calls in flight with a few threads and little memory", "It removes the need for timeouts"],
   "answer": 2,
   "why": "The Spring docs say reactive code generally doesn't run faster. The gain is scale with a small, fixed number of threads, and it only shows when calls have real latency. Debugging is harder, not easier, and slow calls still need timeouts."},
  {"q": "From \"How virtual threads work: carriers and continuations\": a virtual thread calls a blocking card-issuer API over a socket and waits 120 ms. What does its carrier thread do during the wait?",
   "options": ["It blocks for 120 ms, like a platform thread", "The JVM creates a new carrier thread for the other virtual threads", "It unmounts the waiting virtual thread and runs other virtual threads", "The call throws, because virtual threads cannot block"],
   "answer": 2,
   "why": "Blocking socket IO parks the virtual thread and frees the carrier to run other virtual threads. That is why blocking code on virtual threads scales without a reactive rewrite. The carrier pool doesn't grow to compensate for normal IO waits.",
   "from": "vt-02"}
 ],
 "flashcards": [
  {"front": "What does `request(n)` promise the subscriber?", "back": "That the publisher will send at most `n` more `onNext` signals (rule 1.1). It may send fewer and then complete or fail."},
  {"front": "In what order can a Reactive Streams subscriber see signals?", "back": "`onSubscribe onNext* (onError | onComplete)?`: one `onSubscribe`, any number of `onNext`, then at most one terminal signal."},
  {"front": "How does a subscriber stop a stream when its handler fails?", "back": "It calls `subscription.cancel()` and returns normally. Throwing from `onNext` breaks rule 2.13."},
  {"front": "What does `SubmissionPublisher.submit` do when a subscriber's buffer is full?", "back": "It blocks the calling thread until there is room. `offer` drops instead and calls your drop handler."},
  {"front": "What happens if you call `request(0)` on a Reactor `Flux.range` subscription?", "back": "Nothing at all. Reactor only logs it at DEBUG and the stream stalls. Spec rule 3.9 (and the JDK's `SubmissionPublisher`) say it must signal `onError(IllegalArgumentException)`."},
  {"front": "What does `request(Long.MAX_VALUE)` mean?", "back": "Unbounded demand: \"send everything, no backpressure\" (rule 3.17)."},
  {"front": "Is `kotlinx.coroutines.flow.Flow` the same as `java.util.concurrent.Flow`?", "back": "No. The JDK one is the Reactive Streams protocol with `request(n)`. Kotlin's is a coroutine stream whose backpressure is suspension of `emit`."}
 ],
 "terms": [
  {"term": "Backpressure", "plain": "A way for a slow consumer to tell a fast producer how much it can take, so the producer never sends more."},
  {"term": "Demand", "plain": "The number of items a subscriber has asked for with `request(n)` and not yet received."},
  {"term": "Publisher", "plain": "The source of a stream. It sends items to a subscriber, never more than the subscriber asked for."},
  {"term": "Subscriber", "plain": "The receiver of a stream. It gets `onSubscribe`, then `onNext` items, then `onError` or `onComplete`."},
  {"term": "Subscription", "plain": "The link between one publisher and one subscriber. It carries `request(n)` and `cancel()` upstream."},
  {"term": "Terminal signal", "plain": "`onError` or `onComplete`. After one of them the stream is over and nothing else arrives."},
  {"term": "Non-blocking IO", "plain": "IO where the thread hands the request to the OS and moves on, and a callback runs when the answer arrives."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why the payments team bothers with `request(n)` when \"a queue in between does the same job\". Explain in your own words what demand gives you that an unbounded queue doesn't, and when a queue is fine.",
  "answer": "An unbounded queue lets the producer run as fast as it likes. When the consumer falls behind, the queue grows until the heap runs out, and nobody upstream finds out until the pod dies. With `request(n)` the consumer says how many items it can take, and the publisher may not send more. The slowness travels back to the producer: it blocks, buffers up to a limit, drops on purpose, or fails, and you choose which. A queue is fine when it is bounded and you have decided what happens when it is full (block the producer or reject), because then it is backpressure too. Kafka's poll loop is the same idea: the consumer pulls only what it can handle."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three details that will help later.\n\n**Why `request` takes a `long`.** Demand adds up. A subscriber may call `request(5)` and then `request(10)` before any item arrives, and the publisher then owes 15. Rule 3.17 says a subscription must support demand up to `Long.MAX_VALUE`, and that total demand at or above 2^63 - 1 may be treated as unbounded. Reactor's `subscribe(Consumer)` uses exactly that: it requests `Long.MAX_VALUE`. Operators like `limitRate` and `flatMap` then turn that unbounded demand into bounded requests upstream, which is lesson 7 of this track.\n\n**Rule 3.3 and reentrancy.** `request` may be called from inside `onNext` (rule 3.2), and a synchronous publisher may respond by calling `onNext` again from inside that `request` (rule 3.10). Done naively, a stream of a million items becomes a stack a million frames deep. Rule 3.3 makes publishers bound that recursion, usually with a small trampoline loop. This is one reason writing a correct publisher is much harder than writing a subscriber, and why you should use a library's.\n\n**The TCK.** The Reactive Streams project ships a Technology Compatibility Kit: a set of tests that check a publisher or subscriber against the numbered rules. Library authors run it. Reactor's `TestPublisher` (lesson 8 of this track) borrows the idea for application tests: you can create a deliberately non-compliant publisher, for example one that ignores demand, and check that your code survives it.\n\n**`Processor`.** A processor is both a subscriber and a publisher, so it can sit in the middle of a chain. Reactor used to expose processors directly. It has phased them out in favour of `Sinks`, which you'll meet in lesson 8 of this track."
 },
 "sources": [
  {"title": "Reactive Streams for the JVM: specification (README with all rules)", "url": "https://github.com/reactive-streams/reactive-streams-jvm/blob/master/README.md"},
  {"title": "java.util.concurrent.Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html"},
  {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html"},
  {"title": "Reactor reference guide: Introduction to reactive programming (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc"},
  {"title": "Spring Framework reference: WebFlux overview", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html"}
 ]
}
out = ROOT / "content/lessons/rx-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
