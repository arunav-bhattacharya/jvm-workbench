import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l07"
PK = "kotlin/workbench/reactive/l07"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l07."


def code(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


S1 = """`request(n)` is the whole mechanism. A subscriber tells its publisher "I can take n more", the publisher sends at most n, and the subscriber asks again when it is ready. Lesson 1 of this track showed the contract. This lesson is about who sends those numbers in real code, and what happens when a source can't obey them.

Most of the time it isn't you. `subscribe(consumer)`, `block()` and `blockLast()` request `Long.MAX_VALUE`, which the spec treats as unbounded: send everything, as fast as you like. Then each operator between you and the source may change the number on its way up. Put `doOnRequest` right above an operator and you see what it sends:

| Between you and the source | The source sees |
|---|---|
| nothing (`blockLast()` alone) | `9223372036854775807` |
| `take(3)` | `3` |
| `limitRate(10)` | `10, 8, 8, 8, 8, 8` |
| `publishOn(single())` | `256, 192, 192, 192` |
| `flatMap(call, 4)` | `4, 1, 1, 1, 1` |
| `concatMap(call)` | `1, 1, 1, ...` |

Operators with a queue inside (`publishOn`, `limitRate`, the inner queues of `flatMap`) prefetch a batch and refill it when about 75% of it has gone out. That keeps the source busy without unbounded buffering.

When you need to control demand yourself, extend `BaseSubscriber`. Request a first batch in `hookOnSubscribe`, and more as you finish items:

```java
payments.subscribe(new BaseSubscriber<Payment>() {
    @Override protected void hookOnSubscribe(Subscription s) { request(2); }
    @Override protected void hookOnNext(Payment p) { post(p); request(1); }
});
```

```kotlin
payments.subscribe(object : BaseSubscriber<Payment>() {
    override fun hookOnSubscribe(s: Subscription) { request(2) }
    override fun hookOnNext(p: Payment) { post(p); request(1) }
})
```

Now the part that matters. A source that honours `request(n)` simply produces less when nobody asks: `Flux.range`, a database cursor, a paged API client, a Kafka adapter that polls only on demand. Backpressure then works from end to end, and you never have to think about it. A source that can't slow down (a ticker, a WebSocket, a callback API bridged with `Flux.create`) has to put the extra items somewhere. The third section is about that choice."""

S2 = """`limitRate(n)` sits between a subscriber that asks for a lot and a source that should only be asked for a little. It requests n, then tops up by 75% of n each time 75% of the last batch has been delivered. `Flux.range(1, 40).limitRate(10)` sends `10, 8, 8, 8, 8, 8` upstream. Unlike `take`, it never cuts the stream short: every item still arrives, in batches.

Use it when the size of the request changes what the source does. A database cursor or a paging client that fetches "as many rows as were requested" will try to fetch the whole table for `request(Long.MAX_VALUE)`. With `limitRate(100)` in front, the export still streams every row, but never has more than one batch of about 100 in flight:

```java
Flux<LedgerRow> export = cursor.rows(day)
        .limitRate(100)                    // the cursor sees 100, then 75 at a time
        .concatMap(uploader::send);
```

```kotlin
val export: Flux<LedgerRow> = cursor.rows(day)
    .limitRate(100)                        // the cursor sees 100, then 75 at a time
    .concatMap(uploader::send)
```

`limitRate(highTide, lowTide)` sets both numbers. `limitRate(10, 0)` asks for exactly 10 and waits until all 10 have arrived before asking again (`10, 10, 10, 10, 10`), which suits an API that works in fixed pages. Its Javadoc says `limitRate(n)` is equivalent to `publishOn(Schedulers.immediate(), n)`: the same prefetch-and-refill queue, without the thread switch.

Know what it doesn't do. `limitRate` shapes demand; it doesn't make a slow consumer faster, and it can't help with a source that ignores demand. It also isn't a rate limit in the \"per second\" sense, despite the name. For that, the last section has a better tool."""

S3 = """`Flux.interval(Duration.ofMillis(1))` ticks once a millisecond, whatever you request. Put a screen behind it that takes 10 ms per tick and asks for one at a time, and the second tick fails the stream: `OverflowException: Could not emit tick 1 due to lack of requests`. Any source that can't be paused behaves like this, or worse, quietly piles items up: a WebSocket of FX prices, a multicast sink, a callback API.

The `onBackpressure` operators make the choice explicit. Each one requests unbounded from the source, so the source never overflows, and then decides what to do with the items nobody downstream asked for:

| Operator | Items with no demand | Use it for |
|---|---|---|
| `onBackpressureBuffer(n)` | keeps up to n, then cancels the source and fails | bursts you must not lose |
| `onBackpressureBuffer()` | keeps all of them | almost nothing: the backlog grows until the heap runs out |
| `onBackpressureDrop(onDropped)` | drops them, calling `onDropped` | samples, metrics, best-effort events |
| `onBackpressureLatest()` | keeps only the newest | prices, positions, statuses: newer replaces older |
| `onBackpressureError()` | fails at once | cases where falling behind is a bug |

Same ticker, same 10 ms screen, 20 frames. Drop showed ticks about 11 apart and threw away about 200. Latest also showed roughly every tenth tick, always the newest one at the moment the screen asked. `onBackpressureBuffer(10)` delivered ticks 0 to 11 in order, then failed with an overflow error once the buffer was drained. The unbounded buffer delivered 0 to 19 in order, which looks perfect, while the ticker had reached 204: more than 180 ticks were waiting in memory, and that number only grows.

So the name misleads a little. **None of these operators slows the source down.** They are loss policies: they decide what to keep and what to give up. Real backpressure needs a source that honours `request(n)`. When you have a choice of client or API, pick one that does.

When you bridge a callback API yourself, make the same choice at the bridge: `Flux.create(sink -> ..., FluxSink.OverflowStrategy.LATEST)`. The default strategy of `Flux.create` is `BUFFER`, the unbounded one."""

S4 = """Demand also flows from your service toward the services it calls. Each inner publisher in a `flatMap` is an open request to somebody: the bank's settlement API, Oracle, the fraud service. And `flatMap`'s default concurrency is 256.

In the demo, the bank allows 20 open requests per client and answers in 50 ms. `payments.flatMap(this::settle)` over 200 payments opens all 200 at once: 20 settle and 180 come back as `429 Too Many Requests`. `payments.flatMap(this::settle, 20)` keeps 20 open at a time, and all 200 settle in about 500 ms: ten rounds of 50 ms. The cap didn't slow down anything the bank would have accepted. It stopped 180 requests that were never going to work.

```java
Flux<Receipt> receipts = payments.flatMap(bank::settle, 20);     // never more than 20 open requests
```

```kotlin
val receipts: Flux<Receipt> = payments.flatMap(bank::settle, 20) // never more than 20 open requests
```

The source is backpressured too. `flatMap` requests 20 payments, subscribes to 20 calls, and requests one more payment each time a call finishes (the `4, 1, 1, 1, 1` pattern from the first section). So a Kafka adapter that polls on demand is never read faster than the bank answers.

Pick the number from the smallest limit on the path, the downstream ceiling from the executors track: the bank's open-request limit, the connection pool, the fraud API's quota. Little's law connects them: 20 open requests of 50 ms each is at most 400 calls per second. A limit of so many calls *per second* is a different thing, because `flatMap` caps how many are open, not how many start per second. If the bank also had a per-second quota, you would add a rate limiter as well.

`concatMap` is the extreme case, concurrency 1. Use `flatMapSequential(call, 20)` from lesson 3 of this track when you need the results in input order."""

# figure: limitRate reshapes demand
SVG = ('<svg viewBox="0 0 680 200" role="img" aria-label="Demand flows right to left: the subscriber requests an unbounded amount from limitRate(10), '
       'and limitRate requests 10, then 8 at a time, from the cursor. Items flow left to right: all 40 rows reach the subscriber.">')
boxes = [(20, "cursor", "the source"), (280, "limitRate(10)", "a queue of 10"), (540, "subscriber", "blockLast()")]
for x0, name, sub in boxes:
    cls = "box-a" if name.startswith("limitRate") else "box"
    SVG += f'<rect class="{cls}" x="{x0}" y="50" width="120" height="64" rx="8"/>'
    SVG += f'<text class="t t-code" x="{x0 + 60}" y="80" text-anchor="middle">{name}</text>'
    SVG += f'<text class="t-s t-m" x="{x0 + 60}" y="100" text-anchor="middle">{sub}</text>'
# demand lane (right to left)
SVG += '<text class="t-s t-m" x="340" y="24" text-anchor="middle">demand travels up, right to left</text>'
SVG += '<line class="ln-a" x1="538" y1="62" x2="404" y2="62" marker-end="url(#arr)"/>'
SVG += '<text class="t-s t-a" x="470" y="44" text-anchor="middle">request(unbounded)</text>'
SVG += '<line class="ln-a" x1="278" y1="62" x2="144" y2="62" marker-end="url(#arr)"/>'
SVG += '<text class="t-s t-a" x="210" y="44" text-anchor="middle">request 10, then 8, 8, 8</text>'
# items lane (left to right)
SVG += '<line class="ln" x1="142" y1="102" x2="276" y2="102" marker-end="url(#arr)"/>'
SVG += '<text class="t-s" x="210" y="132" text-anchor="middle">rows, as requested</text>'
SVG += '<line class="ln" x1="402" y1="102" x2="536" y2="102" marker-end="url(#arr)"/>'
SVG += '<text class="t-s" x="470" y="132" text-anchor="middle">all 40 rows</text>'
SVG += '<text class="t-s t-m" x="340" y="160" text-anchor="middle">items travel down, left to right</text>'
SVG += '<text class="t-s t-m" x="340" y="186" text-anchor="middle">after 8 of a batch are delivered, limitRate asks for 8 more</text>'
SVG += '</svg>'

CJ = '''// Reactor: say what happens when the consumer can't keep up
Flux<Tick> screen = ticks.onBackpressureLatest();                 // keep only the newest
Flux<AuditEvent> audit = events.onBackpressureBuffer(1_000);      // hold 1,000, then fail loudly
Flux<Receipt> receipts = payments.flatMap(bank::settle, 20);      // at most 20 calls in flight'''
CK = '''// Kotlin Flow: a slow collector suspends the emitter, unless a buffer sits between them
val screen: Flow<Tick> = ticks.conflate()                          // keep only the newest
val audit: Flow<AuditEvent> = events.buffer(1_000)                 // hold 1,000, then the emitter suspends

@OptIn(ExperimentalCoroutinesApi::class)
val receipts: Flow<Receipt> =
    payments.flatMapMerge(concurrency = 20) { p -> flow { emit(bank.settle(p)) } }   // at most 20 at once'''

W0 = '''Flux<PaymentEvent> events = Flux.create(sink -> gateway.onEvent(sink::next));   // push-only listener API

events.flatMap(fraud::score)                       // about 30 ms per call
      .subscribe(scores::save);'''
W0K = '''val events: Flux<PaymentEvent> = Flux.create { sink -> gateway.onEvent(sink::next) }   // push-only listener API

events.flatMap(fraud::score)                       // about 30 ms per call
    .subscribe(scores::save)'''
W2 = '''Flux.create((FluxSink<PaymentEvent> sink) -> gateway.onEvent(sink::next))
        .onBackpressureBuffer(10_000,                                // 1. a bounded backlog...
                e -> log.error("backlog full at event {}", e.id()))  //    ...that says when it overflows
        .flatMap(fraud::score, 50)                                   // 2. the fraud API's limit, not 256
        .subscribe(scores::save,
                e -> gateway.resumeFrom(lastSavedId()));             // 3. on overflow, replay from the last saved event'''
W2K = '''Flux.create { sink: FluxSink<PaymentEvent> -> gateway.onEvent(sink::next) }
    .onBackpressureBuffer(10_000) { e ->                             // 1. a bounded backlog...
        log.error("backlog full at event {}", e.id) }                //    ...that says when it overflows
    .flatMap(fraud::score, 50)                                       // 2. the fraud API's limit, not 256
    .subscribe(scores::save) { gateway.resumeFrom(lastSavedId()) }   // 3. on overflow, replay from the last saved event'''

DJ = '''Flux<Score> scored = authorizations                 // a WebSocket feed: it can't slow down
        .onBackpressureBuffer(5_000,
                a -> log.error("overflow at {}", a.id()))   // hold bursts, fail loudly beyond them
        .flatMap(fraud::score, 50);                       // at most 50 calls in flight'''
DK = '''val scored: Flux<Score> = authorizations              // a WebSocket feed: it can't slow down
    .onBackpressureBuffer(5_000) { a ->
        log.error("overflow at {}", a.id) }                // hold bursts, fail loudly beyond them
    .flatMap(fraud::score, 50)                            // at most 50 calls in flight'''

L = {
 "id": "rx-07",
 "title": "Backpressure in practice",
 "minutes": 35,
 "goal": "By the end you can read the demand an operator sends upstream, cap it with limitRate, pick an explicit loss policy (buffer, drop, latest or error) for a source that can't slow down, and use flatMap's concurrency to protect the services you call.",
 "warmup": {
  "q": "A ticker emits once per millisecond. Your consumer needs 10 ms per item. You add `.onBackpressureBuffer()` before it, and the `OverflowException` you had before goes away. What has really happened?",
  "options": [
   "Reactor slowed the ticker down to match the consumer",
   "The extra ticks now wait in an unbounded queue that keeps growing",
   "The extra ticks are dropped, and only the ones the consumer asked for are kept",
   "The consumer now runs on more threads, so it keeps up"
  ],
  "answer": 1,
  "why": "`onBackpressureBuffer()` requests unbounded from the ticker and stores every tick the consumer hasn't asked for yet. Nothing slows the ticker down, and nothing is dropped, so the queue grows by about 90 items per 100 ms for as long as the stream runs. The error went away; the problem became a memory leak. Dropping is what `onBackpressureDrop` does."
 },
 "sections": [
  {
   "h": "Demand is a number that travels up the chain",
   "body": S1,
   "try": {
    "title": "Watch the requests",
    "minutes": 4,
    "steps": [
     "`DemandDemo` first runs a `BaseSubscriber` that asks for 2, then 1 more after each item. Then it puts `doOnRequest` above five different operators and prints what the source received.",
     "Before running, write down your guess for each of the five lines.",
     "Run it. Then change `limitRate(10)` to `limitRate(10, 0)` and predict the new line."
    ],
    "code": code("DemandDemo"),
    "expect": "The `BaseSubscriber` prints `request(2)`, then alternates `got n` and `request(1)`. The source sees `9223372036854775807` for `blockLast()` alone, `[3]` for `take(3)`, `[10, 8, 8, 8, 8, 8]` for `limitRate(10)`, `[256, 192, 192, 192]` for `publishOn`, and `[4, 1, 1, 1, 1]` for `flatMap(call, 4)`. With `limitRate(10, 0)` it sees `[10, 10, 10, 10, 10]`: a new batch only after the last one fully arrived."
   },
   "refs": [
    {"title": "Reactor reference: Introduction to reactive programming, on backpressure (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Use limitRate to turn one big request into small ones",
   "body": S2,
   "figure": {"svg": SVG, "caption": "limitRate sits between an unbounded request and a source that should be asked for little: the source sees 10, then 8 at a time, and every row still arrives."}
  },
  {
   "h": "When the source can't slow down, choose what to lose",
   "body": S3,
   "try": {
    "title": "One ticker, five policies",
    "minutes": 5,
    "steps": [
     "`OverflowDemo` runs a 1 ms ticker into a screen that asks for one tick at a time and takes 10 ms to draw each. It tries no strategy, then drop, latest, a buffer of 10 and an unbounded buffer, for 20 frames each.",
     "Predict, for each run, which ticks the screen gets and whether it ends with an error.",
     "Run it. For the last run, compare \"ticker reached\" with the number of ticks the screen got. Where are the others?"
    ],
    "code": code("OverflowDemo"),
    "expect": "No strategy: the screen gets tick 0, then `Could not emit tick 1 due to lack of requests`. Drop: about every eleventh tick, with roughly 200 dropped. Latest: about every tenth tick, each the newest at that moment. Buffer of 10: ticks 0 to 11 in order, then `The receiver is overrun by more signals than expected`. Unbounded buffer: ticks 0 to 19 in order with no error, while the ticker reached about 200. The other 180 or so are sitting in the buffer, and in a long-running service that backlog never stops growing."
   },
   "refs": [
    {"title": "Flux Javadoc source: limitRate and the onBackpressure operators (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}
   ]
  },
  {
   "h": "flatMap's concurrency protects the services you call",
   "body": S4,
   "try": {
    "title": "Respect the bank's limit",
    "minutes": 4,
    "steps": [
     "`RateLimitDemo` settles 200 payments against a fake bank that allows 20 open requests and refuses the 21st with a 429. Each refused call is skipped with `onErrorResume`, so the batch keeps going.",
     "Predict both lines: how many settle, how many are refused, and roughly how long each run takes.",
     "Run it. Then change the 20 in the second run to 25 and predict again."
    ],
    "code": code("RateLimitDemo"),
    "expect": "With the default concurrency of 256, all 200 calls open at once: 20 settle and 180 are refused, in well under a second. With a cap of 20, all 200 settle and none are refused, in about 500 ms (ten rounds of 50 ms). With 25, about 5 calls per round are refused, so you lose settlements while gaining nothing: the cap has to match the smallest limit on the path."
   }
  }
 ],
 "analogy": "Think of a coffee bar. Real backpressure is the barista taking the next order only when a hand is free: the queue simply waits at the door, which is a source that honours `request(n)`. `limitRate` is taking orders ten at a time instead of all at once. A source that can't slow down is a conveyor belt of cups that won't stop, and someone has to decide: stack them on a shelf of ten and call the manager when it's full (a bounded buffer that fails), let them fall off (drop), or keep only the last cup (latest). `flatMap(call, 20)` is a machine with 20 heads: never more than 20 brews at once. The analogy breaks at the shelf. A real shelf that overflows is easy to see. In Reactor, `onBackpressureBuffer()` with no size is a shelf you can't see, and it grows until the JVM runs out of heap.",
 "in_your_world": "In payments the loss policy is a business decision, so make it in code where a reviewer can see it. An FX rate feed to a pricing screen wants `onBackpressureLatest`. Card authorizations and audit events must never be dropped silently, so they get a bounded buffer that fails loudly, plus a way to resume (Kafka offsets, the gateway's last acknowledged id). Metrics samples can be dropped. Calls out of your service are the other half: the issuer, the bank's settlement API and your Oracle pool each have a limit, and `flatMap`'s concurrency should match the smallest of them. Quarkus's Mutiny has the same choices under `onOverflow()`, and the same reasoning applies.",
 "mistake": "The most common mistake is fixing an `OverflowException` with `onBackpressureBuffer()` and no size. The error goes away, the tests pass, and in production the buffer quietly holds everything the consumer hasn't caught up with, until a busy morning turns it into an `OutOfMemoryError` far from the cause. People reach for it because the name sounds like the fix. Decide instead what may be lost: give the buffer a size and a callback (`onBackpressureBuffer(10_000, e -> log.error(...))`) for data you must keep, `onBackpressureLatest` for values where newer replaces older, `onBackpressureDrop` for samples, and prefer a source that honours demand when you have the choice.",
 "compare": {
  "title": "Loss policies and concurrency caps in Reactor and Kotlin Flow",
  "java": {"title": "Feeds.java (Reactor)", "src": CJ},
  "kotlin": {"title": "Feeds.kt (Kotlin Flow)", "src": CK},
  "note": "Reactor's backpressure is a number sent upstream with `request(n)`. Kotlin Flow's is suspension: `emit()` simply doesn't return until the collector is ready, so a cold flow can't overflow and has no demand numbers to reshape. The policies only matter when something puts a buffer between producer and collector: `buffer`, `flowOn`, or a hot `callbackFlow` or `SharedFlow`. `conflate()` keeps the newest, like `onBackpressureLatest`. `buffer(1_000)` suspends the emitter when full instead of failing, and `buffer(n, BufferOverflow.DROP_LATEST)` or `DROP_OLDEST` drops. A callback API can't suspend, so inside `callbackFlow` you call `trySend` and must handle its failure: that is the place where Flow makes you choose. `flatMapMerge(concurrency = 20)` is the twin of `flatMap(call, 20)`, and in kotlinx.coroutines 1.11 it still needs an opt-in."
 },
 "worked": {
  "title": "Stop a fraud-scoring stream from eating the heap",
  "steps": [
   {"say": "A service receives payment events from a gateway's listener API and scores each one with the fraud service. During the morning peak, heap use climbs for an hour and the pod is killed. The fraud team also reports bursts of 250 concurrent calls from this one client. Find both causes.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Two defaults. `Flux.create` with no strategy uses `BUFFER`, which is unbounded: whatever the listener pushes while nobody is asking waits in memory. And `flatMap` without a number runs up to 256 scoring calls at once. The fraud API allows 50 per client, so most of the extra calls fail, and an error is terminal (lesson 5 of this track), so the stream can die as well as leak.", "code": "", "lang": ""},
   {"say": "Make each decision visible. Events must not be lost, but the gateway can replay from an event id, so a bounded buffer that fails is safe. The concurrency comes from the fraud API's limit.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Now check the size with numbers, not hope. 50 calls in flight at 30 ms each finish at most about 1,666 scores per second (Little's law: 50 / 0.03 s). The morning peak sends 2,000 events per second, so the backlog grows by about 334 per second, and 10,000 slots last about 30 seconds. A burst of a few seconds fits. A peak that lasts an hour doesn't fit any buffer: it needs a faster consumer, more instances, or a source that can be told to wait. A buffer only absorbs bursts; it never fixes a consumer that is slower on average.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Four feeds, four backpressure decisions",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/FeedPolicies.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l07.*'",
  "steps": [
   "Run the tests once. All five fail. The tests use `TestPublisher.create()` as a hot source: it fails with `Can't deliver value due to lack of requests` when pushed without demand, just like `Flux.interval`.",
   "For each method in `FeedPolicies`, answer two questions before writing code: does the source honour `request(n)`, and may anything be lost?",
   "Write each method. Each one is a single operator.",
   "Run the tests until all five pass. Then read `settleKeepsTwentyInFlight`: it counts calls in flight under virtual time, so the count is exact."
  ],
  "hints": [
   "If `ledgerExport`'s first request is `9223372036854775807`, nothing between the test and the cursor changed the demand. `take(100)` would cap the request too, but it stops after 100 rows.",
   "If `latestTicks` receives `1.0811`, you buffered. If it waits and receives `1.0815`, you dropped.",
   "If `auditEvents` holds 1,000 events but never fails, your buffer has no size. `onBackpressureError()` fails the first audit test instead, because it can't hold anything.",
   "If `settle` reports 100 calls in flight, you used `flatMap` without its concurrency argument. If it reports 1, you used `concatMap`."
  ],
  "done_when": "All five tests in `FeedPoliciesTest` pass."
 },
 "drill": {
  "title": "Score a feed that can't wait",
  "minutes": 4,
  "prompt": "Close this page. `authorizations` is a `Flux<Authorization>` from a WebSocket that cannot slow down. Each one must be scored with `fraud.score(a)` (returns a `Mono<Score>`), the fraud API allows 50 calls at once, bursts of up to 5,000 must be absorbed, and nothing may be lost silently: log the authorization that overflows. Write the chain, then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`subscribe(consumer)` and `block()` request `Long.MAX_VALUE`. Operators reshape that demand on its way up: `take(3)` asks for 3, `flatMap(call, 4)` for 4 and then 1 at a time.",
  "`limitRate(n)` turns a big request into batches of n, topped up by 75%: `10, 8, 8, ...`. Every item still arrives.",
  "A source that honours `request(n)` gives you backpressure for free. For one that can't slow down, you must pick a loss policy.",
  "`onBackpressureBuffer(n)`, `Drop`, `Latest` and `Error` all request unbounded upstream. They decide what to keep, not how fast the source goes.",
  "`onBackpressureBuffer()` with no size hides a backlog until the heap runs out. Give buffers a size and a way to report overflow.",
  "`flatMap`'s concurrency (256 by default) is how many calls you have open at once. Set it from the smallest downstream limit."
 ],
 "quiz": [
  {"q": "A nightly export does `cursor.rows().limitRate(100).concatMap(upload)`. What requests does the cursor receive?",
   "options": ["One request for `Long.MAX_VALUE`", "100, then 75 at a time", "100, then nothing: `limitRate` stops after 100 rows", "1 at a time, because of `concatMap`"],
   "answer": 1,
   "why": "`limitRate(100)` requests 100 and tops up by 75 each time 75 have been delivered, however much the downstream asks for. Unlike `take(100)`, it never ends the stream early. `concatMap` asks `limitRate` for one item at a time, but `limitRate` decides what reaches the cursor."},
  {"q": "A pricing screen shows the live EUR/USD rate from a feed that ticks 200 times a second. The screen redraws 10 times a second. Which policy fits?",
   "options": ["`onBackpressureBuffer()`", "`onBackpressureBuffer(1_000)`", "`onBackpressureDrop()`", "`onBackpressureLatest()`"],
   "answer": 3,
   "why": "A rate is a value where newer replaces older: when the screen asks, it wants the newest tick. `onBackpressureDrop` would show whichever tick arrives after the screen asks, which is fresh too, but it may wait for the next tick and it throws away the newest one on hand. Both buffers would show stale rates, in order, getting further behind."},
  {"q": "Audit events arrive from a source that can't slow down. None may be lost silently, and bursts of a few hundred are normal. Which line fits best?",
   "options": [
    "`events.onBackpressureBuffer()`",
    "`events.onBackpressureBuffer(1_000, e -> log.error(\"audit overflow at {}\", e.id()))`",
    "`events.onBackpressureLatest()`",
    "`events.limitRate(100)`"
   ],
   "answer": 1,
   "why": "A bounded buffer absorbs the normal bursts, and if the subscriber falls further behind, it cancels the source, logs the overflowing event and ends with an overflow error, so the gap is visible. The unbounded buffer never reports anything until memory runs out. `onBackpressureLatest` loses events silently. `limitRate` changes requests, which a source that ignores demand doesn't read."},
  {"q": "`Flux.fromIterable(payments).flatMap(bank::settle)` runs 300 settlements. The bank allows 20 open requests per client and answers the rest with 429. What happens, and what is the fix?",
   "options": [
    "All 300 settle, just more slowly; no fix needed",
    "`flatMap` opens up to 256 calls at once, most get a 429, and the first error can end the stream; use `flatMap(bank::settle, 20)`",
    "`flatMap` opens one call at a time; use `flatMap(bank::settle, 20)` to speed it up",
    "Add `limitRate(20)` before `flatMap`"
   ],
   "answer": 1,
   "why": "The default concurrency is 256, so far more than 20 requests are open at once, and an unhandled 429 is a terminal error. Capping `flatMap` at 20 matches the bank. `limitRate(20)` only changes how many payments are requested from the list at a time; `flatMap` would still subscribe to as many calls as it has payments, up to 256."},
  {"q": "From \"Sizing a pool: CPU-bound, IO-bound and Little's law\": `flatMap(bank::settle, 20)` and each call takes 50 ms. What is the most this can settle per second?",
   "options": ["20", "50", "400", "1,000"],
   "answer": 2,
   "why": "Little's law: in flight = rate x time, so rate = 20 / 0.05 s = 400 per second. To go faster you need more open requests (if the bank allows them) or faster calls. A per-second quota from the bank is a separate limit that a concurrency cap doesn't enforce.",
   "from": "exec-03"}
 ],
 "flashcards": [
  {"front": "What does `subscribe(consumer)` request from the source?", "back": "`Long.MAX_VALUE`: unbounded demand, unless an operator in between reshapes it."},
  {"front": "`Flux.range(1, 40).limitRate(10)`: what does the range see?", "back": "`request(10)`, then `request(8)` five times: it tops up by 75% of the batch."},
  {"front": "`limitRate(100)` vs `take(100)`?", "back": "`limitRate` caps each request and still delivers every item. `take` caps the request and ends the stream after 100."},
  {"front": "Does `onBackpressureDrop` (or `Buffer`, `Latest`) slow the source down?", "back": "No. They all request unbounded upstream and decide what to do with items nobody asked for."},
  {"front": "A slow subscriber finally requests 1. What does it get from `onBackpressureLatest` vs `onBackpressureDrop`?", "back": "Latest: the newest item that arrived while it wasn't asking. Drop: nothing until the next item arrives after the request."},
  {"front": "What happens when `onBackpressureBuffer(1000)` overflows?", "back": "It cancels the source, and after the subscriber drains the 1,000 held items, it ends with an overflow error."},
  {"front": "What is `Flux.create`'s default overflow strategy?", "back": "`BUFFER`: unbounded. Pass a `FluxSink.OverflowStrategy` (DROP, LATEST, ERROR) to choose."}
 ],
 "terms": [
  {"term": "Demand", "plain": "How many more items a subscriber has asked for with `request(n)` and not yet received."},
  {"term": "Unbounded demand", "plain": "A request of `Long.MAX_VALUE`: send everything, as fast as you can."},
  {"term": "limitRate", "plain": "An operator that splits downstream demand into batches of n requested from upstream."},
  {"term": "Loss policy", "plain": "Buffer, drop, keep the latest, or fail: what to do with items a source pushes without demand."},
  {"term": "OverflowException", "plain": "Reactor's error for more items than were requested, from a source or a full bounded buffer."},
  {"term": "Concurrency cap", "plain": "The most inner publishers `flatMap` subscribes at once; 256 by default."}
 ],
 "explain_back": {
  "prompt": "A teammate got `OverflowException: Could not emit tick ... due to lack of requests` and wants to add `onBackpressureBuffer()` because \"that's what backpressure is for\". Explain what backpressure really is in Reactor, why their fix is risky, and what you would ask before choosing a fix.",
  "answer": "Backpressure is the subscriber telling the source how many items it can take, with `request(n)`, and the source sending no more than that. A source like `Flux.interval` can't wait, so when the consumer falls behind, it fails instead of slowing down. `onBackpressureBuffer()` with no size doesn't slow anything either: it asks the source for everything and keeps every item the consumer hasn't asked for in an unbounded queue. The error disappears, and the backlog grows until memory runs out. Before choosing, I'd ask two things: can we use a source that honours demand instead, and if not, what may we lose? If old values are useless, keep the latest. If samples are fine to skip, drop them and count the drops. If nothing may be lost, use a bounded buffer that fails loudly and a way to resume, and check with Little's law that the consumer is fast enough on average, because a buffer only absorbs bursts."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Sources that pull.** `Flux.generate` calls your generator once per requested item, so it is backpressured by construction: good for paging through an API or reading a file line by line. `Flux.create` gives you a `FluxSink` for push APIs, and `sink.onRequest(n -> ...)` lets you pull n items from an API that supports it, which turns a push bridge into a real backpressured source.\n\n**More buffer options.** `onBackpressureBuffer(maxSize, onOverflow, BufferOverflowStrategy.DROP_OLDEST)` keeps the buffer bounded but evicts old items instead of failing (`DROP_LATEST` and `ERROR` are the other strategies). `onBackpressureBuffer(Duration ttl, int maxSize, onEvicted)` also evicts items older than the ttl, for data that goes stale.\n\n**Prefetch everywhere.** Many operators take a prefetch argument: `flatMap(fn, concurrency, prefetch)` sets how many items each inner is asked for (32 by default), `concatMap(fn, prefetch)` and `publishOn(scheduler, prefetch)` likewise. Smaller numbers mean less memory and more request round trips.\n\n**Demand across the network.** Reactive Streams demand stops at the process boundary. RSocket carries `request(n)` across the wire. HTTP has no `request(n)` of its own: a server streaming to a slow client relies on TCP flow control, and it is the server library's job to turn a full socket into lower demand on your `Flux`.\n\n**Deprecated name.** `limitRequest(n)` is deprecated in favour of `take(n)`, which in 3.8 caps the upstream request at n by default."
 },
 "sources": [
  {"title": "Flux Javadoc source: limitRate, onBackpressureBuffer/Drop/Latest/Error, flatMap (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java"},
  {"title": "Reactor reference: Introduction to reactive programming, backpressure and push-pull (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc"},
  {"title": "Reactive Streams specification for the JVM (rules 1.1, 2.1, 3.17)", "url": "https://github.com/reactive-streams/reactive-streams-jvm/blob/master/README.md"},
  {"title": "Kotlin docs: Asynchronous Flow, buffering and conflation", "url": "https://kotlinlang.org/docs/flow.html"}
 ]
}
out = ROOT / "content/lessons/rx-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
