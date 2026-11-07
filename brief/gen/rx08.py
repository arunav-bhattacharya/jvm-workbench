import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l08"
PK = "kotlin/workbench/reactive/l08"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l08."


def code(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


S1 = """A cold publisher does its work again for every subscriber (lesson 2 of this track). That is right for an HTTP call per request. It is wrong for a WebSocket of FX rates that six dashboards open: six connections to the provider, six copies of the same ticks. A hot publisher produces whether or not anyone listens, and subscribers share what it produces from the moment they join.

Reactor turns cold into hot with a few operators. They differ in two decisions: when to connect to the source, and what a subscriber that joins late receives.

| Operator | Connects | A late subscriber gets | Disconnects |
|---|---|---|---|
| `share()`, which is `publish().refCount()` | at the first subscriber | only new items | when the last one leaves |
| `replay(n).refCount()` | at the first subscriber | the last n items, then new ones | when the last one leaves |
| `publish().autoConnect(n)` | when n have subscribed | only new items | never |
| `cache()` | at the first subscriber | every item, from the start | never |

In the demo a feed emits a rate every 100 ms and dashboard B joins at 250 ms. Cold, B opens a second connection and starts from the first rate. With `share()`, B gets only the rates from 300 ms on. With `replay(1).refCount()`, B immediately gets the 200 ms rate, then the live ones. With `cache()`, B gets all of them, including the two it missed, and the cache keeps every item for as long as the Flux lives. For a long-running feed that is a memory leak, so prefer `replay(n)` or `cache(n)`. `Mono.cache(ttl)` is the right tool for a value that should be reloaded now and then, such as a fee schedule.

Two details matter in production. `publish` follows the slowest subscriber: it requests from the source only what every subscriber can take, so one slow dashboard slows them all (combine it with a policy from lesson 7 of this track). And `refCount(1, Duration.ofSeconds(5))` adds a grace period: when the last subscriber leaves, it waits 5 seconds before disconnecting, so a dashboard that refreshes the page doesn't make you reconnect to the provider."""

S2 = """Sometimes the values come from ordinary code: a Kafka listener callback, a webhook handler, a scheduled job. `Sinks` is Reactor's safe way to push them into a `Flux`. (Processors used to do this; Reactor has phased them out in favour of Sinks.)

```java
Sinks.Many<PaymentEvent> sink = Sinks.many().multicast().directBestEffort();
Flux<PaymentEvent> live = sink.asFlux();                    // what subscribers see
Sinks.EmitResult result = sink.tryEmitNext(event);          // what the listener calls
```

```kotlin
val sink: Sinks.Many<PaymentEvent> = Sinks.many().multicast().directBestEffort()
val live: Flux<PaymentEvent> = sink.asFlux()                // what subscribers see
val result: Sinks.EmitResult = sink.tryEmitNext(event)      // what the listener calls
```

`Sinks.many().multicast()` sends each item to the subscribers present at that moment, in three flavours. `onBackpressureBuffer()` buffers for slow subscribers and keeps items pushed before the first subscriber arrives for it. By default it also shuts down for good when its last subscriber leaves: a subscriber that comes later just receives `onComplete`. `directBestEffort()` keeps no buffer: a subscriber that isn't asking misses the item, and the sink keeps working with zero subscribers. `directAllOrNothing()` drops the item for everyone if one subscriber isn't ready. Then `many().replay()` keeps history for late subscribers (`all()`, `limit(n)`, `limit(Duration)`, `latest()`), `many().unicast()` allows exactly one subscriber, and `Sinks.one()` and `Sinks.empty()` carry a single value or a bare completion.

The trap is threads. `tryEmitNext` never blocks and never retries. If two threads call it at the same moment, one of them gets `EmitResult.FAIL_NON_SERIALIZED` and its item is not emitted. Ignore the result and items vanish. In my runs of the demo, 8 threads emitting 10,000 items each delivered only a few thousand of the 80,000.

Either check every result, or call `emitNext(item, handler)` with a handler that retries. `Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1))` spins until the sink is free, for up to a second. Its Javadoc asks you not to keep and reuse it, so create one per call. Wrapping the emit in a lock works too."""

S3 = """A reactive test has to subscribe, check each signal in order, and fail when anything else happens. `StepVerifier` from reactor-test does that:

```java
StepVerifier.create(checkout.quote("m-1", "c-1"))
        .expectNext(expectedQuote)
        .expectComplete()
        .verify(Duration.ofSeconds(1));
```

```kotlin
StepVerifier.create(checkout.quote("m-1", "c-1"))
    .expectNext(expectedQuote)
    .expectComplete()
    .verify(Duration.ofSeconds(1))
```

Four rules, each learned from a test that lied:

1. Nothing runs until `verify()` (or a shortcut such as `verifyComplete()` or `verifyError()`). A test that ends at `expectComplete()` never subscribes, and passes whatever the code does.
2. `verify()` has no timeout by default, so a hung publisher hangs the build. Pass a `Duration`, or set `StepVerifier.setDefaultTimeout(...)` once.
3. `StepVerifier.withVirtualTime(() -> ...)` replaces Reactor's schedulers with a virtual clock, so a one-day delay is verified in milliseconds. Build the publisher **inside** the supplier: a `Mono.delay` built earlier has already picked the real clock, and the test times out.
4. `expectNoEvent(d)` checks that nothing happens during d of virtual time. The subscription counts as an event, so put `expectSubscription()` first.

For a source you drive by hand there is `TestPublisher`: call `next(...)`, `complete()` or `error(...)` from the test, then check `wasCancelled()` or `assertMinRequested(n)`. `TestPublisher.create()` respects demand like a real source and fails if pushed without it; `createNoncompliant(...)` breaks the spec on purpose (lesson 1 of this track). `PublisherProbe` answers a different question: was this branch subscribed at all? Use it to prove that a `switchIfEmpty` fallback ran, or didn't. All the virtual-time tests in this track's labs, from the backoff in lesson 5 to the bank calls in lesson 7, are built from these pieces."""

S4 = """A stack trace from a reactive chain shows where the error was raised and how the subscription got there. It almost never shows where you wrote the operator that failed. In the demo, `Flux.just(120, 80).single()` inside a `feeRow()` method fails with `IndexOutOfBoundsException: Source emitted more than one item`. The top frame is Reactor's `MonoSingle`, and no frame of the trace is in `feeRow()`.

`checkpoint("fee-row")` marks a point in the chain. When an error passes through it, Reactor attaches a suppressed exception that reads `Error has been observed at the following site(s):` followed by `*__checkpoint` and `fee-row`. It is cheap, so put one at the edges of your own pipelines, named after what they do. `checkpoint("fee-row", true)` also records a stack trace when the chain is assembled, which points at the line in your code, at the cost of capturing that trace every time the chain is built.

`Hooks.onOperatorDebug()` does that for every operator in the application. The reference guide calls it a last resort because of the cost. For production there is the reactor-tools agent (`ReactorDebugAgent.init()` as the first line of `main`), which adds the same information by instrumenting your classes when they load. It is a separate dependency and not in the labs.

```java
Mono<Integer> fee = feeRow(merchant).checkpoint("fee-row");   // name the place, cheaply
Flux<Integer> rows = Flux.range(1, 5).log("rows").take(2);    // print every signal at this point
```

```kotlin
val fee: Mono<Int> = feeRow(merchant).checkpoint("fee-row")   // name the place, cheaply
val rows: Flux<Int> = Flux.range(1, 5).log("rows").take(2)    // print every signal at this point
```

`log("rows")` prints every signal that passes that point: `onSubscribe`, `request(2)`, `onNext(1)`, `onNext(2)`, `cancel()`. It is the quickest way to see this track's ideas in a real chain: the demand from lesson 7, the cancellation that `take` sends upstream, the thread each signal arrives on. It logs through SLF4J when that is on the classpath."""

S5 = """Reactor is not the default answer for new JVM code in 2026, and the Spring team says so itself. The Spring Framework reference still reads: "If you have a Spring MVC application that works fine, there is no need to change. Imperative programming is the easiest way to write, understand, and debug code." It warns about "the steep learning curve", tells you to "start small and measure the benefits", and adds: "We expect that, for a wide range of applications, the shift is unnecessary." Lesson 1 of this track quoted the same docs on speed: reactive doesn't make applications faster; it lets them scale with fewer threads when calls have latency.

Virtual threads (final in JDK 21) took away most of the thread-count argument. Mark Paluch of the Spring team wrote in 2022, while they were still a preview: "The reasons to use asynchronous programming models go away in many cases if we start with the assumption that our code runs on Virtual Threads." The same post keeps a place for reactive: ReactiveX-style APIs "remain a powerful way to compose concurrent logic and a natural way for dealing with streams", and they are "the right approach for concurrent scenarios in which declarative concurrency (such as scatter-gather) matters."

So here is the position I'd take for your services:

- For request and response over JDBC, JPA or other blocking clients, use virtual threads and plain imperative code. Don't rewrite a working Quarkus REST or Spring MVC service in Reactor.
- For streams (server-sent events, WebSockets, Kafka pipelines, anything where demand, cancellation and a loss policy matter), Reactor earns its complexity.
- For many calls composed with timeouts, retries and fan-out, Reactor's operators are hard to beat. Coroutines, or structured concurrency once it is final, are the imperative alternatives.
- In a stack that is already reactive end to end (WebClient, R2DBC, Reactor Netty), stay reactive and keep the few blocking calls on `boundedElastic`.
- In Kotlin, coroutines give sequential-looking code over the same runtime. `kotlinx-coroutines-reactor` bridges both ways (`awaitSingle()`, `mono { }`, `Flow.asFlux()`), and Spring maps `Mono` to `suspend` and `Flux` to `Flow`. The coroutines track builds on that."""

X0, PX = 150, 0.8
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 290" role="img" aria-label="A feed emits rates 0 to 4 at 100 to 500 ms. Subscriber A gets all five. '
       'Subscriber B joins at 250 ms: with share() it gets 2, 3, 4; with replay(1) it gets 1 at once, then 2, 3, 4; with cache() it gets 0 and 1 at once, then 2, 3, 4.">')
for ms in range(0, 700, 100):
    SVG += f'<text class="t-s t-m" x="{x(ms):.0f}" y="22" text-anchor="middle">{ms}</text>'
    SVG += f'<line class="ln-d" x1="{x(ms):.0f}" y1="30" x2="{x(ms):.0f}" y2="36"/>'
SVG += '<text class="t-s t-m" x="660" y="22" text-anchor="middle">ms</text>'
live = [(100, "0"), (200, "1"), (300, "2"), (400, "3"), (500, "4")]
lanes = [
    ("source", 56, live, []),
    ("A, from 0 ms", 104, live, []),
    ("B, share()", 160, live[2:], []),
    ("B, replay(1)", 208, live[2:], [(250, "1")]),
    ("B, cache()", 256, live[2:], [(238, "0"), (262, "1")]),
]
SVG += '<line class="ln-d" x1="16" y1="128" x2="660" y2="128"/>'
SVG += f'<line class="ln-bad" x1="{x(250):.0f}" y1="134" x2="{x(250):.0f}" y2="278"/>'
SVG += f'<text class="t-s t-bad" x="{x(250) + 8:.0f}" y="146">B subscribes at 250 ms</text>'
for name, y, items, replayed in lanes:
    SVG += f'<text class="t-s" x="16" y="{y + 4}">{name}</text>'
    SVG += f'<line class="ln" x1="{X0}" y1="{y}" x2="645" y2="{y}" marker-end="url(#arr)"/>'
    for ms, label in replayed:
        SVG += f'<circle class="box-b" cx="{x(ms):.0f}" cy="{y}" r="10"/><text class="t-s" x="{x(ms):.0f}" y="{y + 4}" text-anchor="middle">{label}</text>'
    for ms, label in items:
        SVG += f'<circle class="box-a" cx="{x(ms):.0f}" cy="{y}" r="10"/><text class="t-s" x="{x(ms):.0f}" y="{y + 4}" text-anchor="middle">{label}</text>'
SVG += '</svg>'

CJ = '''// Reactor: a hub that listener threads push into, and a shared rate feed
private final Sinks.Many<PaymentEvent> events = Sinks.many().multicast().directBestEffort();

void publish(PaymentEvent e) {
    events.emitNext(e, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)));
}

Flux<PaymentEvent> live() { return events.asFlux(); }

Flux<Rate> rates = provider.rates()
        .replay(1)                                    // late subscribers get the latest rate
        .refCount(1, Duration.ofSeconds(5));          // disconnect 5 s after the last one leaves'''
CK = '''// Kotlin coroutines: SharedFlow for events, StateFlow for "the latest value"
private val events = MutableSharedFlow<PaymentEvent>(extraBufferCapacity = 1_000)

fun publish(e: PaymentEvent) {
    check(events.tryEmit(e)) { "subscribers are too slow" }   // thread-safe; suspend emit() waits instead
}

val live: SharedFlow<PaymentEvent> = events.asSharedFlow()

val rates: StateFlow<Rate?> = provider.rates()
    .stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)   // latest rate, stop 5 s after the last leaves'''

W0 = '''Mono<Status> awaitFinal(String paymentId) {
    return Flux.interval(Duration.ofSeconds(30))              // poll every 30 s
            .concatMap(tick -> api.status(paymentId))         // one call at a time
            .filter(Status::isFinal)
            .next()                                           // first final status, then stop polling
            .timeout(Duration.ofMinutes(5));
}'''
W0K = '''fun awaitFinal(paymentId: String): Mono<Status> =
    Flux.interval(Duration.ofSeconds(30))                     // poll every 30 s
        .concatMap { api.status(paymentId) }                  // one call at a time
        .filter(Status::isFinal)
        .next()                                               // first final status, then stop polling
        .timeout(Duration.ofMinutes(5))'''
W1 = '''FakeStatusApi api = new FakeStatusApi(PENDING, PENDING, SETTLED);

StepVerifier.withVirtualTime(() -> new StatusPoller(api).awaitFinal("p-1"))   // 1. build it inside the supplier
        .expectSubscription()                                                  // 2. before any expectNoEvent
        .expectNoEvent(Duration.ofSeconds(90))                                 // 3. silent until the third poll
        .expectNext(SETTLED)
        .verifyComplete();

assertThat(api.calls()).isEqualTo(3);'''
W1K = '''val api = FakeStatusApi(PENDING, PENDING, SETTLED)

StepVerifier.withVirtualTime { StatusPoller(api).awaitFinal("p-1") }       // 1. build it inside the supplier
    .expectSubscription()                                                  // 2. before any expectNoEvent
    .expectNoEvent(Duration.ofSeconds(90))                                 // 3. silent until the third poll
    .expectNext(SETTLED)
    .verifyComplete()

assertThat(api.calls()).isEqualTo(3)'''
W2 = '''FakeStatusApi stuck = new FakeStatusApi(PENDING);          // pending forever

StepVerifier.withVirtualTime(() -> new StatusPoller(stuck).awaitFinal("p-2"))
        .expectSubscription()
        .thenAwait(Duration.ofMinutes(5))                    // 4. jump to the deadline
        .expectError(TimeoutException.class)
        .verify(Duration.ofSeconds(1));                      // 5. a real-time safety net'''
W2K = '''val stuck = FakeStatusApi(PENDING)                          // pending forever

StepVerifier.withVirtualTime { StatusPoller(stuck).awaitFinal("p-2") }
    .expectSubscription()
    .thenAwait(Duration.ofMinutes(5))                        // 4. jump to the deadline
    .expectError(TimeoutException::class.java)
    .verify(Duration.ofSeconds(1))                           // 5. a real-time safety net'''

DJ = '''StepVerifier.withVirtualTime(() -> Mono.delay(Duration.ofHours(1)).thenReturn("expired"))
        .expectSubscription()
        .expectNoEvent(Duration.ofHours(1))
        .expectNext("expired")
        .expectComplete()
        .verify(Duration.ofSeconds(1));'''
DK = '''StepVerifier.withVirtualTime { Mono.delay(Duration.ofHours(1)).thenReturn("expired") }
    .expectSubscription()
    .expectNoEvent(Duration.ofHours(1))
    .expectNext("expired")
    .expectComplete()
    .verify(Duration.ofSeconds(1))'''

L = {
 "id": "rx-08",
 "title": "Hot and cold publishers, Sinks, and StepVerifier",
 "minutes": 40,
 "goal": "By the end you can share one source between many subscribers with the right late-subscriber behaviour, push values in from many threads with Sinks without losing any, test timing with StepVerifier and virtual time, find a failing operator with checkpoint and log, and say when Reactor is still the right tool.",
 "warmup": {
  "q": "An FX feed emits a rate every 100 ms. Dashboard A subscribes at 0 ms, dashboard B at 250 ms, both to `feed.share()`. What does B receive first?",
  "options": [
   "The first rate, because `share()` replays from the start",
   "The rate emitted at 200 ms, because `share()` keeps the latest",
   "The rate emitted at 300 ms",
   "Nothing: `share()` allows one subscriber"
  ],
  "answer": 2,
  "why": "`share()` is `publish().refCount()`: one upstream subscription, multicast to whoever is subscribed when an item arrives. B joined at 250 ms, so its first item is the one at 300 ms. Replaying the latest is `replay(1).refCount()`, and replaying everything is `cache()`."
 },
 "sections": [
  {
   "h": "Cold sources run per subscriber; hot ones are shared",
   "body": S1,
   "figure": {"svg": SVG, "caption": "One feed, three ways to share it with a subscriber that joins at 250 ms. Blue items arrive live; yellow ones are replayed at the moment B subscribes."},
   "try": {
    "title": "Five ways to share one feed",
    "minutes": 4,
    "steps": [
     "`HotColdDemo` runs a cold feed (a rate every 100 ms, five rates) with dashboard A subscribing at once and B 250 ms later. It tries cold, `share()`, `replay(1).refCount()`, `cache()` and `publish().autoConnect(2)`.",
     "For each run, predict the number of connections and what B receives.",
     "Run it. Then explain the `autoConnect(2)` line: why does A get all five rates, starting late?"
    ],
    "code": code("HotColdDemo"),
    "expect": "Cold: 2 connections, and both get all five rates. `share()`: 1 connection, B gets `1.082` to `1.084`. `replay(1).refCount()`: B also gets `1.081` the moment it subscribes. `cache()`: B gets all five. `autoConnect(2)`: 1 connection that opens only when B subscribes at 250 ms, so both get all five, and A waited 250 ms for its first rate."
   },
   "refs": [
    {"title": "Reactor reference: Hot versus cold (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/reactor-hotCold.adoc", "kind": "docs"},
    {"title": "Reactor reference: Broadcasting to multiple subscribers with ConnectableFlux (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/advanced-broadcast-multiple-subscribers-connectableflux.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Sinks push values in from ordinary code",
   "body": S2,
   "try": {
    "title": "Who gets what from a sink",
    "minutes": 4,
    "steps": [
     "`SinksDemo` pushes values into a multicast sink before and between two subscribers, checks two multicast flavours after every subscriber has left, fills a `replay().limit(2)` sink, tries two subscribers on a unicast sink, and finally lets 8 threads emit 10,000 items each, first with `tryEmitNext`, then with `emitNext` and `busyLooping`.",
     "Predict each line before you run it. For the race, guess how many of the 80,000 items arrive.",
     "Run it twice and compare the race numbers."
    ],
    "code": code("SinksDemo"),
    "expect": "Multicast: `early=[10, 1, 2, 3]` (the 10 waited in the warm-up buffer) and `late=[3]`. After everyone left, the `onBackpressureBuffer()` sink only completes the new subscriber, while `directBestEffort()` delivers `got 42`. Replay with limit 2: `[2, 3]`. Unicast: the second subscriber fails with `Sinks.many().unicast() sinks only allow a single Subscriber`. The `tryEmitNext` race delivers only a few thousand of 80,000, with a different number each run; `emitNext` with `busyLooping` delivers all 80,000."
   },
   "refs": [
    {"title": "Reactor reference: Sinks (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/processors.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "StepVerifier checks the signals, and virtual time fakes the clock",
   "body": S3,
   "try": {
    "title": "Break four StepVerifier rules",
    "minutes": 4,
    "steps": [
     "`StepVerifierDemo` runs five small tests: one without `verify()`, a one-day delay under virtual time, `expectNoEvent` as the first step, a delay built outside the virtual-time supplier, and a `TestPublisher` driven by hand. (It runs from `src/demo`, so the lab's build adds reactor-test to the demo classpath.)",
     "Predict which ones pass, which fail, and with what message.",
     "Run it. In part 1, add `.verify()` to the end of the line and run again."
    ],
    "code": code("StepVerifierDemo"),
    "expect": "Part 1 reports `subscriptions=0`: without `verify()` nothing ran, and the wrong expectation (`refunded`) went unnoticed. After you add `.verify()`, it throws an `AssertionError` saying it expected `refunded` and got `charged`. Part 2 verifies a full day in a few dozen milliseconds. Part 3 fails with `expected no event: onSubscribe(...)`. Part 4 fails with `VerifySubscriber timed out`, because the delay holds the real clock. Part 5 passes."
   },
   "refs": [
    {"title": "Reactor reference: Testing (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/testing.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Debugging: name the place with checkpoint, watch the signals with log",
   "body": S4,
   "try": {
    "title": "Find the operator that failed",
    "minutes": 3,
    "steps": [
     "`DebugDemo` runs a chain whose `single()` sees two fee rows, three times: plain, with `checkpoint(\"fee-row\")`, and with `checkpoint(\"fee-row\", true)`. Then it puts `log(\"rows\")` between a range and `take(2)`.",
     "Run it. For each of the first three, find the information that tells you where the failing operator was written.",
     "Predict the `log` output first: which `request` and which last signal will it show?"
    ],
    "code": code("DebugDemo"),
    "expect": "All three report `IndexOutOfBoundsException: Source emitted more than one item` with `MonoSingle` as the top frame, and no frame in `feeRow()`. The plain run gives no clue where it came from. The checkpoint run names `fee-row`. The run with `true` adds an assembly trace pointing at the `main` line where the checkpoint was written. The log shows `onSubscribe`, `request(2)`, `onNext(1)`, `onNext(2)` and `cancel()`: `take(2)` capped the demand and then cancelled the range."
   },
   "refs": [
    {"title": "Reactor reference: Debugging Reactor (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/debugging.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "When reactive is still worth it",
   "body": S5,
   "refs": [
    {"title": "Embracing Virtual Threads (Spring blog, Mark Paluch, 2022)", "url": "https://spring.io/blog/2022/10/11/embracing-virtual-threads", "kind": "read"},
    {"title": "Spring Framework reference: Spring WebFlux overview, applicability and performance", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Cold is video on demand: everyone who presses play gets the film from the start, and the studio streams one copy per viewer. `share()` is live TV: one broadcast, and if you switch on late, you missed the start. `replay(1)` is live TV that shows you the last scene when you switch on. `cache()` is a recorder that keeps the whole broadcast forever, so every newcomer can watch from the beginning, and the recordings pile up. A sink is the studio's microphone, which only one presenter may speak into at a time. The analogy breaks at the end of the evening: a TV station keeps broadcasting to an empty room, while `refCount` switches the transmitter off when the last viewer leaves.",
 "in_your_world": "Picture a payment operations service. A Kafka consumer pushes authorization events into a sink, and dashboards follow them over server-sent events: that is a multicast `directBestEffort` sink with a thread-safe emit, because Kafka listener threads run concurrently and dashboards come and go. The FX rates come from one provider connection that a dozen screens share with `replay(1).refCount(1, grace)`. The fee schedule is read from Oracle at most once every five minutes with `Mono.cache(ttl)`. Every one of those has timing in it, so each gets a virtual-time test that runs in milliseconds in CI. And when a new service is plain request and response over Oracle, you build it on virtual threads instead.",
 "mistake": "The most common mistake is calling `tryEmitNext` on a sink from several threads and ignoring the result. It looks safe because the sink is \"thread-safe\", and it is, in the sense that it detects the concurrent call and refuses it with `FAIL_NON_SERIALIZED` instead of corrupting itself. The refused item is simply gone. In tests with one thread, everything arrives; in production, with four Kafka listener threads, events go missing with no log line. Use `emitNext(item, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)))`, or serialize the calls yourself, and write a test that emits from several threads at once.",
 "compare": {
  "title": "A hot event hub and a shared feed in Reactor and Kotlin",
  "java": {"title": "PaymentEvents.java (Reactor)", "src": CJ},
  "kotlin": {"title": "PaymentEvents.kt (coroutines)", "src": CK},
  "note": "The shapes match: a multicast sink is close to a `MutableSharedFlow`, and `replay(1).refCount(1, grace)` is close to `stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)`. The differences are in concurrency and lifetime. A `MutableSharedFlow` accepts emissions from any number of threads at once; its `tryEmit` fails only when the buffer is full, and `emit` suspends instead. A Reactor sink refuses concurrent emissions unless you retry or serialize. And `stateIn` and `shareIn` need a `CoroutineScope`: the shared upstream lives in that scope and is cancelled with it, which is structured concurrency. Reactor's sharing lives as long as subscribers keep it alive. `StateFlow` also always has a current value and skips values equal to the last one, which `replay(1)` does not. The coroutines track covers `SharedFlow` and `StateFlow` in detail."
 },
 "worked": {
  "title": "Test a payment-status poller in milliseconds",
  "steps": [
   {"say": "After a payment is sent to the bank, a poller asks for its status every 30 seconds until it is final, and gives up after 5 minutes. A real-time test would take 90 seconds for the happy path and 5 minutes for the timeout. Here is the code under test.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "The happy path: the fake API answers PENDING twice, then SETTLED. Under virtual time the polls happen at 30, 60 and 90 seconds of fake time. `expectNoEvent(90 s)` proves nothing came out earlier, and the settled status arrives exactly at 90 s.",
    "code": W1, "lang": "java", "alt_code": W1K, "alt_lang": "kotlin"},
   {"say": "The timeout path: the payment never settles. Jump the clock to the deadline and expect the `TimeoutException`. Keep a real-time limit on `verify` as well, so a mistake makes the test fail in one second instead of hanging.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Both tests run in a few milliseconds. If one of them hangs instead, look at where the poller is built: `Flux.interval` and `timeout` pick their scheduler when the chain is assembled, so a poller created before `withVirtualTime` runs on the real clock. The same goes for a `Mono` built once in a `@BeforeEach` and kept in a field.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A payment-event hub and two shared feeds",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/PaymentEventHub.java", f"{lab}/main/{P}/RateFeeds.java", f"{lab}/main/{P}/PaymentEvent.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l08.*'",
  "steps": [
   "Run the tests once. All six fail.",
   "`PaymentEventHub`: choose the sink from the Javadoc of `live()` (only events after you subscribed, nothing kept while nobody listens, survives every subscriber leaving). Then make `publish` safe for 8 threads at once, and return a read-only view from `live()`.",
   "`RateFeeds.shareWithLatest`: one upstream connection, the latest rate for late subscribers, and a disconnect when the last subscriber leaves.",
   "`RateFeeds.cacheFor`: load at most once per ttl. Read how the test controls the clock with `VirtualTimeScheduler.getOrSet()` and `advanceTimeBy`.",
   "Run the tests until all six pass, then once more: the 8-thread test must pass every time."
  ],
  "hints": [
   "If the hot test finds event 0 in the early subscriber's list, your sink kept events published before anyone subscribed: `multicast().onBackpressureBuffer()` does that. The same sink fails the \"every subscriber has left\" test with a completion.",
   "If the 8-thread test receives fewer than 16,000 events, you ignored the result of `tryEmitNext`. If it reports crashed threads, you used `EmitFailureHandler.FAIL_FAST`, which throws on `FAIL_NON_SERIALIZED`.",
   "`share()` fails the late-subscriber test (no latest value); `cache()` and `replay(1).autoConnect()` fail the disconnect test (they never cancel upstream).",
   "`Mono.cache()` with no argument never reloads. There is an overload that takes a `Duration`."
  ],
  "done_when": "All six tests in `HotPublishersTest` pass, twice in a row."
 },
 "drill": {
  "title": "A one-hour test that runs in milliseconds",
  "minutes": 3,
  "prompt": "Close this page. Write a `StepVerifier` test for `Mono.delay(Duration.ofHours(1)).thenReturn(\"expired\")` that proves nothing is emitted before the hour is up, then `expired` and completion, runs in milliseconds, and can't hang the build. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`share()` (`publish().refCount()`) gives late subscribers only new items; `replay(n).refCount()` replays the last n; `cache()` replays everything forever. `refCount` disconnects when the last subscriber leaves, `autoConnect` never does.",
  "Sinks push values from ordinary code. `tryEmitNext` refuses concurrent calls with `FAIL_NON_SERIALIZED`: check the result, or use `emitNext` with `busyLooping`.",
  "A `multicast().onBackpressureBuffer()` sink shuts down when its last subscriber leaves; `directBestEffort()` keeps no buffer and survives an empty room.",
  "StepVerifier runs nothing until `verify()`. Give it a timeout, build the publisher inside the `withVirtualTime` supplier, and call `expectSubscription()` before `expectNoEvent`.",
  "`checkpoint(\"name\")` tags errors with a place in your chain cheaply; `log()` prints every signal at one point.",
  "Reactive earns its complexity for streams, backpressure and composed concurrency. For request and response over blocking libraries, the Spring team itself says imperative code on virtual threads is enough."
 ],
 "quiz": [
  {"q": "Two Kafka listener threads call `sink.tryEmitNext(event)` on the same `Sinks.many().multicast()` sink at the same moment, and ignore the return value. What can happen?",
   "options": [
    "Both events are emitted, in some order",
    "One call returns `FAIL_NON_SERIALIZED` and its event is never emitted",
    "The sink buffers the second event and emits it later",
    "The sink throws `ConcurrentModificationException`"
   ],
   "answer": 1,
   "why": "Reactor sinks detect concurrent emission and refuse it instead of blocking or queueing, so one of the two calls gets `FAIL_NON_SERIALIZED`. Ignoring the result loses that event silently. Use `emitNext(event, EmitFailureHandler.busyLooping(...))`, which retries, or serialize the calls."},
  {"q": "A test reads `StepVerifier.create(service.refund(\"p-1\")).expectNext(\"REFUNDED\").expectComplete();` and passes. The refund code is in fact broken. Why does the test pass?",
   "options": [
    "`expectComplete()` ignores the value",
    "Nothing subscribes until `verify()` is called, so no expectation is ever checked",
    "StepVerifier only fails on errors, not on wrong values",
    "The refund runs on another thread, so its result arrives after the test ends"
   ],
   "answer": 1,
   "why": "`expectComplete()` only adds a step to the script. `verify()`, or a shortcut like `verifyComplete()`, is what subscribes and runs it. Add `.verify(Duration.ofSeconds(1))` and the test checks the value and fails if it hangs."},
  {"q": "Dashboards share one FX provider connection. A dashboard that opens late must show the current rate at once, and the connection must close when nobody watches. Which operator fits?",
   "options": ["`rates.share()`", "`rates.cache()`", "`rates.replay(1).refCount()`", "`rates.publish().autoConnect(1)`"],
   "answer": 2,
   "why": "`replay(1)` gives a late subscriber the latest rate, and `refCount()` connects on the first subscriber and cancels upstream when the last one leaves. `share()` gives late subscribers nothing until the next tick. `cache()` and `autoConnect` never disconnect, and `cache()` also keeps every rate forever."},
  {"q": "A team runs a Spring MVC service on JDBC that meets its latency targets. Someone proposes rewriting it with WebFlux \"to make it faster\". What do Spring's own docs say?",
   "options": [
    "Rewrite it: reactive code is faster for every workload",
    "If an MVC application works fine there is no need to change; reactive doesn't generally make applications faster",
    "Rewrite only the JDBC calls with Reactor and keep the controllers",
    "Switch to WebFlux but keep JDBC on the event loop"
   ],
   "answer": 1,
   "why": "The Spring reference says a working MVC application has no need to change, that blocking persistence APIs like JDBC point to MVC, and that reactive and non-blocking generally don't make applications run faster. With virtual threads, the thread-count argument for this kind of service is mostly gone too. The last option is the worst of both: JDBC on an event loop blocks every request it serves."},
  {"q": "From \"Errors, retries and timeouts\": a retry uses `Retry.backoff(3, Duration.ofMillis(200))` with the default jitter. How should its virtual-time test check the slow path?",
   "options": [
    "`expectNoEvent` for exactly 1,400 ms, then expect the fallback",
    "Advance the clock well past the longest possible total wait, then check the result and the number of attempts",
    "Use real time with `Thread.sleep(2_000)` so the jitter is realistic",
    "It can't be tested while jitter is on"
   ],
   "answer": 1,
   "why": "With jitter each wait moves by up to half its length, so exact times are not fixed. Advancing well past the maximum (the worked example used 10 seconds) and then asserting the outcome and the count is stable. Exact-time assertions need `jitter(0)`. Real sleeps make the test slow and still flaky.",
   "from": "rx-05"}
 ],
 "flashcards": [
  {"front": "What is `share()` the same as, and what does a late subscriber get?", "back": "`publish().refCount()`. A late subscriber gets only items emitted after it subscribed."},
  {"front": "Late subscriber on `replay(1).refCount()`: what does it get?", "back": "The most recent item at once, then the live ones. The upstream is cancelled when the last subscriber leaves."},
  {"front": "Two threads call `tryEmitNext` on one sink at the same moment. What can happen?", "back": "One gets `EmitResult.FAIL_NON_SERIALIZED` and its item is not emitted. Check the result or use `emitNext(item, busyLooping(...))`."},
  {"front": "What happens to `Sinks.many().multicast().onBackpressureBuffer()` when its last subscriber leaves?", "back": "By default it shuts down: a later subscriber just receives `onComplete`. `directBestEffort()` keeps working."},
  {"front": "A `StepVerifier` chain without `verify()`: what runs?", "back": "Nothing. `verify()` (or `verifyComplete()` etc.) is what subscribes and checks the steps."},
  {"front": "Why must the publisher be built inside the `withVirtualTime` supplier?", "back": "Operators like `delay`, `interval` and `timeout` pick their scheduler at assembly. Built earlier, they use the real clock and the test hangs."},
  {"front": "What does `checkpoint(\"fee-row\")` add to an error?", "back": "A suppressed exception saying the error was observed at the checkpoint named `fee-row`. Cheap; `checkpoint(name, true)` also captures the assembly stack trace."}
 ],
 "terms": [
  {"term": "Hot publisher", "plain": "A publisher that produces whether or not anyone subscribes; subscribers see what is produced while they listen."},
  {"term": "ConnectableFlux", "plain": "What `publish()` and `replay()` return: a shared Flux that subscribes to its source when it is connected."},
  {"term": "refCount", "plain": "Connect on the first subscriber, disconnect when the last one leaves (optionally after a grace period)."},
  {"term": "Sink", "plain": "Reactor's thread-aware way to push values from ordinary code into a Flux or Mono."},
  {"term": "StepVerifier", "plain": "reactor-test's tool that subscribes to a publisher and checks its signals step by step."},
  {"term": "Virtual time", "plain": "A fake clock that replaces Reactor's schedulers in a test, so delays pass instantly."},
  {"term": "checkpoint", "plain": "An operator that labels a place in a chain so errors passing through it say where they came from."}
 ],
 "explain_back": {
  "prompt": "A teammate is building a dashboard backend: a Kafka consumer receives payment events and a dozen browsers should see them live, plus the current FX rate. Explain which Reactor pieces you would use, what can silently go wrong with each, and how you would test it.",
  "answer": "For the events I'd use a multicast sink, `directBestEffort()`, because each browser only needs events from the moment it connects, nothing should pile up while nobody watches, and the hub must keep working after every browser disconnects (the buffered flavour shuts down when its last subscriber leaves). The Kafka listener threads would publish with `emitNext` and a `busyLooping` handler, because `tryEmitNext` refuses concurrent calls and the refused event just disappears. For the FX rate I'd wrap the provider feed in `replay(1).refCount(1, grace)`: one connection, new browsers get the current rate at once, and the connection closes a few seconds after the last browser leaves. `share()` would leave new browsers blank until the next tick, and `cache()` would never disconnect and would keep every rate. To test it I'd use `TestPublisher` for the provider, a multi-threaded test for the hub with a start latch, and `StepVerifier.withVirtualTime` for anything with time in it, always with `verify(Duration)` so a bug fails fast instead of hanging."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Connecting by hand.** `publish()` and `replay()` return a `ConnectableFlux`. Besides `refCount` and `autoConnect`, you can call `connect()` yourself once every subscriber is in place, and dispose the returned `Disposable` to disconnect. That suits a startup sequence that wires several consumers before any data should flow.\n\n**Context instead of ThreadLocal.** Because a chain hops threads, a `ThreadLocal` such as an MDC trace id doesn't follow it. Reactor's `Context` does: write it at the bottom with `contextWrite(Context.of(\"traceId\", id))` and read it upstream with `Mono.deferContextual(ctx -> ...)`. It travels from the subscriber toward the source, so a `contextWrite` above the reader is invisible to it. With the Micrometer context-propagation library on the classpath, `Hooks.enableAutomaticContextPropagation()` (Reactor 3.5.3+) restores ThreadLocals such as the MDC around each operator; it isn't in the labs.\n\n**BlockHound in tests.** Calling `BlockHound.install()` at the start of a test run makes any blocking call on a non-blocking thread throw `BlockingOperationError`, which catches the JDBC call on an event loop from the schedulers lesson before production does. On JDK 13+ it needs `-XX:+AllowRedefinitionToAddDeleteMethods`.\n\n**Backpressure in tests.** `StepVerifier.create(flux, 0)` starts with no demand, and `thenRequest(n)` adds it step by step. That is how the lab of lesson 7 of this track checked which tick a slow subscriber receives."
 },
 "sources": [
  {"title": "Reactor reference: Hot versus cold (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/reactor-hotCold.adoc"},
  {"title": "Reactor reference: Sinks (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/processors.adoc"},
  {"title": "Reactor reference: Testing (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/testing.adoc"},
  {"title": "Reactor reference: Debugging Reactor (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/debugging.adoc"},
  {"title": "Embracing Virtual Threads (Spring blog, Mark Paluch, 2022)", "url": "https://spring.io/blog/2022/10/11/embracing-virtual-threads"}
 ]
}
out = ROOT / "content/lessons/rx-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
