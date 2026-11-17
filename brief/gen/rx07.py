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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """Back at the end of the bakery line, the packer has a small table where loaves wait to be boxed. It holds ten. As long as the oven waits for her slips, the table never overflows, because she writes "send me 10 more" only when there's room. But not everything in a bakery reads slips. The thermometer in the oven is a chatterbox: it reports the temperature every millisecond, whether anyone looks or not. Orders on the website arrive whenever customers click. When a source like that outruns the packer, the table fills, and someone has to decide what happens to the next loaf.

The trap is that Reactor's answer has a reassuring name, `onBackpressureBuffer`. With no size, it quietly builds the doorstep from Why reactive all over again.

In Schedulers, `publishOn` asked for 256 items at a time. In this lesson, we'll watch those slips travel up the chain and shrink a big one with `limitRate`. Then we'll choose what to lose when a source can't slow down, and stay within what the services we call allow. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_BASE = """orders.subscribe(new BaseSubscriber<Order>() {
    @Override protected void hookOnSubscribe(Subscription s) { request(2); }      // the first slip
    @Override protected void hookOnNext(Order o) { box(o); request(1); }           // one more per boxed order
});"""
K_BASE = """orders.subscribe(object : BaseSubscriber<Order>() {
    override fun hookOnSubscribe(s: Subscription) { request(2) }                  // the first slip
    override fun hookOnNext(o: Order) { box(o); request(1) }                       // one more per boxed order
})"""

S0 = """`request(n)` is the whole mechanism. A subscriber, the receiving end of a stream, tells its publisher, the source, "I can take n more". The publisher sends at most n, and the subscriber asks again when it's ready. On the bakery line, that's the packer's slip from Why reactive. This lesson is about who writes those slips in real code, and what happens when a source can't read them.

Most of the time it isn't you. `subscribe(consumer)`, `block()` and `blockLast()` request `Long.MAX_VALUE`, which the Reactive Streams spec, the contract from Why reactive, treats as **unbounded demand**: send everything, as fast as you like. Then each operator between you and the source may change the number on its way up. Put `doOnRequest`, an operator that prints each request passing through it, just above the source, and you see what the source receives. `DemandDemo`, in the Try it, does that for five operators:

| Between you and the source | The source sees |
|---|---|
| nothing (`blockLast()` alone) | `9223372036854775807` |
| `take(3)` | `3` |
| `limitRate(10)` | `10, 8, 8, 8, 8, 8` |
| `publishOn(single())` | `256, 192, 192, 192` |
| `flatMap(call, 4)` | `4, 1, 1, 1, 1` |
| `concatMap(call)` | `1, 1, 1, ...` |

The long number on the first line is `Long.MAX_VALUE`, a slip with no limit. Operators with a queue inside (`publishOn`, `limitRate` and the inner queues of `flatMap`) **prefetch**: they ask for a batch in advance and refill it when about 75% of it has gone out. A batch of 256 is followed by slips for 192, three quarters of it. That keeps the source busy without a queue that grows forever.

When you want to write the slips yourself, extend `BaseSubscriber`, Reactor's helper class for hand-written subscribers. Ask for a first batch in `hookOnSubscribe`, and for more as you finish items:

""" + pair(J_BASE, K_BASE) + """

The demo's first part runs a subscriber like this one and prints `request(2)`, then `got 1`, `request(1)`, `got 2`, and so on: one new slip for each finished item.

Now the part that matters. A source that honours `request(n)` simply produces less when nobody asks, like the oven that waits for the packer's slip. `Flux.range` does, and so does a database query that fetches rows as they are requested, or a client that fetches a web service's answers one page at a time. Backpressure then works from end to end, and you never have to think about it.

A source that can't slow down has to put the extra items somewhere. A timer can't wait, and neither can a live connection to the oven thermometer. The website's orders can't either, once you bridge them into Reactor with `Flux.create`. That operator turns a callback API, one that calls your code whenever something happens, into a `Flux`. The third section is about that choice.

**A source that reads the slips gives you backpressure for free. Prefer one when you can.**

First, though, a source that reads its slips a little too faithfully."""

# ---------------------------------------------------------------- section 1
J_LR = """Flux<OrderRow> report = orderBook.rows(day)
        .limitRate(100)                    // the cursor sees 100, then 75 at a time
        .concatMap(archive::store);"""
K_LR = """val report: Flux<OrderRow> = orderBook.rows(day)
    .limitRate(100)                        // the cursor sees 100, then 75 at a time
    .concatMap(archive::store)"""

S1 = """The bakery's nightly report reads the day's orders from the order book's database through a **cursor**, a reader that fetches rows from the database as they are asked for. Ask it for 100 rows and it fetches 100. Hand it the `Long.MAX_VALUE` of a plain `subscribe` or `blockLast()`, and it tries to fetch the whole table at once.

`limitRate(n)` sits between a subscriber that asks for a lot and a source that should only be asked for a little. It requests n, then tops up by 75% of n each time 75% of the last batch has been delivered. `Flux.range(1, 40).limitRate(10)` sends `10, 8, 8, 8, 8, 8` upstream, toward the source, as the first section showed. Unlike `take`, it never cuts the stream short: every item still arrives, in batches. The figure below draws it.

In the bakery, `limitRate` is a packer who has been told to ask for ten at a time, however big an order the shop sends her. With `limitRate(100)` in front, the report still gets every row, but the cursor never has more than about one batch of 100 in flight:

""" + pair(J_LR, K_LR) + """

`limitRate(highTide, lowTide)` sets both numbers. `limitRate(10, 0)` asks for exactly 10, and waits until all 10 have arrived before it asks again (`10, 10, 10, 10, 10`). That suits a web service that answers in fixed pages. Its Javadoc says `limitRate(n)` is equivalent to `publishOn(Schedulers.immediate(), n)`: the same prefetch-and-refill queue, without the thread switch.

Know what it doesn't do. `limitRate` shapes demand. It doesn't make a slow consumer faster, and it can't help with a source that ignores demand. And despite its name, it isn't a rate limit in the "so many per second" sense, because it counts items, not time. The last section shows how to protect a service you call, and why that isn't a per-second limit either.

**limitRate splits one big slip into small ones. Every item still arrives.**

Quick check: predict the first three requests that `Flux.range(1, 100)` sees under `.limitRate(20).blockLast()`, and what changes with `limitRate(20, 0)`. (20, then 15 and 15, because it tops up by 75% of 20. With a low tide of 0, it asks for 20 each time, and only after the whole batch has arrived.)

A cursor waits patiently for its next slip. The next source doesn't wait for anyone."""

# ---------------------------------------------------------------- section 2
S2 = """`Flux.interval(Duration.ofMillis(1))` emits a number every millisecond, whatever you request, and Reactor calls each of those numbers a tick. In our bakery it stands in for the oven thermometer: one reading every millisecond. Put a screen behind it that asks for one reading at a time and takes 10 ms to draw each, and the second reading fails the stream. `OverflowDemo`, in the Try it, printed:

```text
1. no strategy               thermometer at reading   0, screen got [0]
                              then the error: Could not emit tick 1 due to lack of requests (interval doesn't support small downstream requests that replenish slower than the ticks)
```

Any source that can't be paused behaves like this, or worse, quietly piles items up: a live connection to another program, a sink that your own code pushes into (lesson 8 of this track), a callback API.

On the bakery line, the thermometer is a belt that won't stop, and it ends at the packer's small table. When the table is full, someone has to decide what happens to the next item. The `onBackpressure` operators make that choice explicit. Each one asks the source for everything, so the source never overflows, and then decides what to do with the items nobody further down the chain has asked for:

| Operator | Items nobody asked for | Use it for |
|---|---|---|
| `onBackpressureBuffer(n)` | keeps up to n (a small pile), then cancels the source and fails | bursts you must not lose |
| `onBackpressureBuffer()` | keeps all of them (a pile with no limit) | almost nothing: it grows until memory runs out |
| `onBackpressureDrop(onDropped)` | drops them into a bin, calling `onDropped` | samples, counts, best-effort events |
| `onBackpressureLatest()` | keeps only the newest, in one slot | readings, positions, statuses: newer replaces older |
| `onBackpressureError()` | fails at once, stopping the line | cases where falling behind is a bug |

The same thermometer and the same 10 ms screen, for 20 readings each:

```text
2. onBackpressureDrop        thermometer at reading 221, screen got [0, 11, 22, 34, 46, 57, 67, 79, 90, 101, 112, 123, 134, 145, 156, 167, 178, 189, 200, 211]
                              (202 readings dropped)
3. onBackpressureLatest      thermometer at reading 202, screen got [0, 10, 20, 30, 40, 50, 60, 70, 81, 91, 101, 111, 121, 131, 141, 151, 162, 172, 182, 192]
4. onBackpressureBuffer(10)  thermometer at reading  12, screen got [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                              then the error: The receiver is overrun by more signals than expected (bounded queue...)
5. onBackpressureBuffer()    thermometer at reading 216, screen got [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
```

Drop showed readings about 11 apart and threw away 202. Latest also showed roughly every tenth reading, always the newest one at the moment the screen asked. The bounded buffer delivered readings 0 to 11 in order, then failed with an overflow error once the pile was gone. The unbounded buffer delivered 0 to 19 in order, which looks perfect, and that's the problem. The thermometer had reached reading 216, so nearly 200 readings were waiting in memory, and that number only grows. It's the doorstep from Why reactive, with more loaves every second.

So the names mislead a little. **None of these operators slows the source down.** They are **loss policies**: they decide what to keep and what to give up. Here the bakery picture breaks. A full table in a real bakery is easy to see. `onBackpressureBuffer()` with no size is a table nobody can see, and it grows until the heap, the memory where Java keeps its objects, runs out. Real backpressure needs a source that honours `request(n)`, so when you have a choice of source, pick one that does.

When you bridge a callback API yourself, make the same choice at the bridge: `Flux.create(sink -> ..., FluxSink.OverflowStrategy.LATEST)`. The default strategy of `Flux.create` is `BUFFER`, the one with no limit.

Every policy so far protects your own program from a fast source. The services you call need the same protection from you."""

ASIDE = {
    "title": "How do I choose a policy for my own data?",
    "body": "Ask what one missed item costs. A temperature or a stock level is a value where newer replaces older, so keep the latest. A sample, such as one visitor count out of hundreds, can be dropped, as long as you count the drops. An order must never vanish silently: give it a bounded buffer that fails loudly, plus a way to resume, such as asking the website to send again everything after the last saved order number. Put the decision in code where a reviewer can see it, because it's a business decision as much as a technical one.",
}

# ---------------------------------------------------------------- section 3
J_CAP = """Flux<Booking> vans = deliveries.flatMap(courier::book, 20);     // never more than 20 open requests"""
K_CAP = """val vans: Flux<Booking> = deliveries.flatMap(courier::book, 20) // never more than 20 open requests"""

S3 = """Demand also flows from your program toward the services it calls. Each inner publisher in a `flatMap` is an open request to somebody: the courier's booking service, the stock database, the mill. And `flatMap`'s default concurrency, from Transforming streams, is 256.

Picture the bakery booking a courier van for each of the day's 200 cake deliveries. The courier's booking service allows 20 open requests per customer and answers in 50 ms. `CourierLimitDemo`, in the Try it, books all 200 two ways. It skips a refused booking with `onErrorResume`, so that one refusal doesn't end the batch (Errors, retries and timeouts):

```text
1. flatMap(call)        20 booked, 180 refused, in 165 ms
2. flatMap(call, 20)   200 booked,   0 refused, in 520 ms
```

The default opened all 200 requests at once. 20 were booked, and 180 came back with a polite "too many open requests". With a cap of 20, all 200 were booked in about 500 ms, ten rounds of 50 ms:

""" + pair(J_CAP, K_CAP) + """

The cap didn't slow down anything the courier would have accepted. It stopped 180 requests that were never going to work.

The source is backpressured too. `flatMap` requests 20 deliveries, subscribes to 20 calls, and requests one more delivery each time a call finishes. That's the `4, 1, 1, 1, 1` pattern from the first section, with 20 instead of 4, so the deliveries are never read faster than the courier answers. On the bakery line, it's the icing machine from Transforming streams, given 20 nozzles, and a packer who sends a cake only when a nozzle is free.

Pick the number from the smallest limit on the path: the courier's open-request limit, the number of connections a database allows, a service's quota. That's the downstream ceiling from the executors track. **Little's law**, from the same track, connects the numbers: the calls in flight equal the calls per second times the time each call takes. So 20 open requests of 50 ms each make at most 20 / 0.05 s = 400 calls per second.

A limit of so many calls *per second* is a different thing, because `flatMap` caps how many calls are open, not how many start each second. If the courier also had a per-second quota, you would add a rate limiter, a tool that spaces calls out in time, on top.

`concatMap` is the extreme case, a concurrency of 1. Use `flatMapSequential(call, 20)` from Transforming streams when you need the results in input order.

**flatMap's concurrency is how many calls you have open. Set it from the smallest limit on the path.**

That cap is the last piece of backpressure in practice: slips that travel up, a loss policy where they can't be read, and a cap on what we ask of others."""

# ---------------------------------------------------------------- figure: limitRate reshapes demand
SVG = ('<svg viewBox="0 0 680 200" role="img" aria-label="Demand flows right to left: the subscriber requests an unbounded amount from limitRate(10), '
       'and limitRate requests 10, then 8 at a time, from the cursor. Items flow left to right: all 40 rows reach the subscriber.">')
boxes = [(20, "cursor", "the source"), (280, "limitRate(10)", "a queue of 10"), (540, "subscriber", "blockLast()")]
for x0, name, sub in boxes:
    cls = "box-a" if name.startswith("limitRate") else "box"
    SVG += f'<rect class="{cls}" x="{x0}" y="50" width="120" height="64" rx="8"/>'
    SVG += f'<text class="t t-code" x="{x0 + 60}" y="80" text-anchor="middle">{name}</text>'
    SVG += f'<text class="t-s t-m" x="{x0 + 60}" y="100" text-anchor="middle">{sub}</text>'
SVG += '<text class="t-s t-m" x="340" y="24" text-anchor="middle">demand travels up, right to left</text>'
SVG += '<line class="ln-a" x1="538" y1="62" x2="404" y2="62" marker-end="url(#arr)"/>'
SVG += '<text class="t-s t-a" x="470" y="44" text-anchor="middle">request(unbounded)</text>'
SVG += '<line class="ln-a" x1="278" y1="62" x2="144" y2="62" marker-end="url(#arr)"/>'
SVG += '<text class="t-s t-a" x="210" y="44" text-anchor="middle">request 10, then 8, 8, 8</text>'
SVG += '<line class="ln" x1="142" y1="102" x2="276" y2="102" marker-end="url(#arr)"/>'
SVG += '<text class="t-s" x="210" y="132" text-anchor="middle">rows, as requested</text>'
SVG += '<line class="ln" x1="402" y1="102" x2="536" y2="102" marker-end="url(#arr)"/>'
SVG += '<text class="t-s" x="470" y="132" text-anchor="middle">all 40 rows</text>'
SVG += '<text class="t-s t-m" x="340" y="160" text-anchor="middle">items travel down, left to right</text>'
SVG += '<text class="t-s t-m" x="340" y="186" text-anchor="middle">after 8 of a batch are delivered, limitRate asks for 8 more</text>'
SVG += '</svg>'

# ---------------------------------------------------------------- closing
CLOSING = """We started with the packer's small table and a thermometer that never stops talking. A source that reads the slips gives you backpressure for free, and `limitRate` keeps the slips small. For a source that can't wait, the `onBackpressure` operators only decide what to lose, and `flatMap`'s number decides how hard you lean on the services you call.

Now search your own code for `onBackpressureBuffer()` with empty parentheses, and for `flatMap(` with no second argument.

Next, we'll share one belt among several screens. The thermometer feeds a screen in the shop and another in the kitchen. Must each screen open its own connection to the oven, and what does a screen that switches on late get to see?"""

# ---------------------------------------------------------------- compare, worked, drill
CJ = '''// Reactor: say what happens when the consumer can't keep up
Flux<Reading> screen = readings.onBackpressureLatest();           // keep only the newest
Flux<WebOrder> kept = webOrders.onBackpressureBuffer(1_000);      // hold 1,000, then fail loudly
Flux<Booking> vans = deliveries.flatMap(courier::book, 20);       // at most 20 calls in flight'''
CK = '''// Kotlin Flow: a slow collector suspends the emitter, unless a buffer sits between them
val screen: Flow<Reading> = readings.conflate()                    // keep only the newest
val kept: Flow<WebOrder> = webOrders.buffer(1_000)                 // hold 1,000, then the emitter suspends

@OptIn(ExperimentalCoroutinesApi::class)
val vans: Flow<Booking> =
    deliveries.flatMapMerge(concurrency = 20) { d -> flow { emit(courier.book(d)) } }   // at most 20 at once'''

W0 = '''Flux<WebOrder> orders = Flux.create(sink -> website.onOrder(sink::next));   // push-only listener API

orders.flatMap(addresses::check)                    // about 30 ms per call
      .subscribe(checked::save);'''
W0K = '''val orders: Flux<WebOrder> = Flux.create { sink -> website.onOrder(sink::next) }   // push-only listener API

orders.flatMap(addresses::check)                    // about 30 ms per call
    .subscribe(checked::save)'''
W2 = '''Flux.create((FluxSink<WebOrder> sink) -> website.onOrder(sink::next))
        .onBackpressureBuffer(10_000,                                 // 1. a bounded backlog...
                o -> log.error("backlog full at order {}", o.id()))   //    ...that says when it overflows
        .flatMap(addresses::check, 50)                                // 2. the address service's limit, not 256
        .subscribe(checked::save,
                e -> website.resendFrom(lastSavedOrder()));           // 3. on overflow, resend from the last saved order'''
W2K = '''Flux.create { sink: FluxSink<WebOrder> -> website.onOrder(sink::next) }
    .onBackpressureBuffer(10_000) { o ->                              // 1. a bounded backlog...
        log.error("backlog full at order {}", o.id) }                 //    ...that says when it overflows
    .flatMap(addresses::check, 50)                                    // 2. the address service's limit, not 256
    .subscribe(checked::save) { website.resendFrom(lastSavedOrder()) }   // 3. on overflow, resend from the last saved order'''

DJ = '''Flux<Check> checked = webOrders                      // a live connection: it can't slow down
        .onBackpressureBuffer(5_000,
                o -> log.error("overflow at {}", o.id()))   // hold bursts, fail loudly beyond them
        .flatMap(addresses::check, 50);                   // at most 50 calls in flight'''
DK = '''val checked: Flux<Check> = webOrders                   // a live connection: it can't slow down
    .onBackpressureBuffer(5_000) { o ->
        log.error("overflow at {}", o.id) }                // hold bursts, fail loudly beyond them
    .flatMap(addresses::check, 50)                        // at most 50 calls in flight'''

L = {
 "id": "rx-07",
 "title": "Backpressure in practice",
 "minutes": 35,
 "goal": "By the end you can read the demand an operator sends upstream, cap it with limitRate, pick an explicit loss policy (buffer, drop, latest or error) for a source that can't slow down, and use flatMap's concurrency to protect the services you call.",
 "opening": OPENING,
 "warmup": {
  "q": "The oven thermometer sends a reading every millisecond, and it can't slow down. The screen that shows it needs 10 ms per reading. You add `.onBackpressureBuffer()` before the screen, and the `OverflowException` you had before goes away. What has really happened?",
  "options": [
   "Reactor slowed the thermometer down to match the screen",
   "The extra readings now wait in a queue with no limit, and it keeps growing",
   "The extra readings are dropped, and only the ones the screen asked for are kept",
   "The screen now runs on more threads, so it keeps up"
  ],
  "answer": 1,
  "why": "`onBackpressureBuffer()` asks the thermometer for everything and stores every reading the screen hasn't asked for yet. Nothing slows the thermometer down, and nothing is dropped, so the queue grows by about 90 readings every 100 ms for as long as the stream runs. The error went away; the problem became a slow leak of memory. Dropping is what `onBackpressureDrop` does, and the section on sources that can't slow down compares all five choices."
 },
 "sections": [
  {
   "h": "Demand is a number that travels up the chain",
   "body": S0,
   "try": {
    "title": "Watch the requests",
    "minutes": 4,
    "steps": [
     "`DemandDemo` first runs a `BaseSubscriber` that asks for 2, then 1 more after each item. Then it puts `doOnRequest` above the source of five different chains and prints what the source received.",
     "Before you run it, write down your guess for each of the five lines.",
     "Run it. Then change `limitRate(10)` to `limitRate(10, 0)` and predict the new line."
    ],
    "code": code("DemandDemo"),
    "expect": "The `BaseSubscriber` prints `request(2)`, then alternates `got n` and `request(1)`. The source sees `9223372036854775807` for `blockLast()` alone, `[3]` for `take(3)`, `[10, 8, 8, 8, 8, 8]` for `limitRate(10)`, `[256, 192, 192, 192]` for `publishOn`, and `[4, 1, 1, 1, 1]` for `flatMap(call, 4)`. With `limitRate(10, 0)` it sees `[10, 10, 10, 10, 10]`: a new batch only after the last one has fully arrived."
   },
   "refs": [
    {"title": "Reactor reference: Introduction to reactive programming, on backpressure (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Use limitRate to turn one big request into small ones",
   "body": S1,
   "figure": {"svg": SVG, "caption": "limitRate sits between an unbounded request and a source that should be asked for little: the cursor sees 10, then 8 at a time, and every row still arrives."}
  },
  {
   "h": "When the source can't slow down, choose what to lose",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "One thermometer, five policies",
    "minutes": 5,
    "steps": [
     "`OverflowDemo` runs a 1 ms thermometer into a screen that asks for one reading at a time and takes 10 ms to draw each. It tries no strategy, then drop, latest, a buffer of 10 and an unbounded buffer, for 20 readings each.",
     "Predict, for each run, which readings the screen gets and whether it ends with an error.",
     "Run it. For the last run, compare \"thermometer at reading\" with the number of readings the screen got. Where are the others?"
    ],
    "code": code("OverflowDemo"),
    "expect": "No strategy: the screen gets reading 0, then `Could not emit tick 1 due to lack of requests`. Drop: about every eleventh reading, with roughly 200 dropped. Latest: about every tenth reading, each the newest at that moment. Buffer of 10: readings 0 to 10 or 11 in order, then `The receiver is overrun by more signals than expected`. Unbounded buffer: readings 0 to 19 in order with no error, while the thermometer reached about 200 or more. The other 180 or so are sitting in the buffer, and in a program that runs for days, that backlog never stops growing."
   },
   "refs": [
    {"title": "Flux Javadoc source: limitRate and the onBackpressure operators (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}
   ]
  },
  {
   "h": "flatMap's concurrency protects the services you call",
   "body": S3,
   "try": {
    "title": "Stay within the courier's limit",
    "minutes": 4,
    "steps": [
     "`CourierLimitDemo` books vans for 200 deliveries with a fake courier service that allows 20 open requests and refuses the 21st. Each refused call is skipped with `onErrorResume`, so the batch keeps going.",
     "Predict both lines: how many are booked, how many are refused, and roughly how long each run takes.",
     "Run it. Then change the 20 in the second run to 25 and predict again."
    ],
    "code": code("CourierLimitDemo"),
    "expect": "With the default concurrency of 256, all 200 calls open at once: 20 are booked and 180 refused, in well under a second (about 160 ms here). With a cap of 20, all 200 are booked and none refused, in about 500 ms (ten rounds of 50 ms). With 25, about 5 calls per round are refused, so you lose bookings and gain nothing: the cap has to match the smallest limit on the path."
   }
  }
 ],
 "compare": {
  "title": "Loss policies and concurrency caps in Reactor and Kotlin Flow",
  "java": {"title": "Belts.java (Reactor)", "src": CJ},
  "kotlin": {"title": "Belts.kt (Kotlin Flow)", "src": CK},
  "note": "Reactor's backpressure is a number sent upstream with `request(n)`. Kotlin Flow's is suspension: `emit()` simply doesn't return until the collector is ready, so a cold flow can't overflow and has no demand numbers to reshape. The policies only matter when something puts a buffer between producer and collector: `buffer`, `flowOn`, or a hot `callbackFlow` or `SharedFlow`. `conflate()` keeps the newest, like `onBackpressureLatest`. `buffer(1_000)` suspends the emitter when it is full instead of failing, and `buffer(n, BufferOverflow.DROP_LATEST)` or `DROP_OLDEST` drops. A callback API can't suspend, so inside `callbackFlow` you call `trySend` and must handle its failure: that's the place where Flow makes you choose. `flatMapMerge(concurrency = 20)` is the twin of `flatMap(call, 20)`, and in kotlinx.coroutines 1.11 it still needs an opt-in."
 },
 "worked": {
  "title": "Stop an address-checking stream from eating the memory",
  "steps": [
   {"say": "The bakery's website pushes each new order to a listener, a callback the program registers, and the program checks each delivery address with an address service, a web service that takes about 30 ms per call. During the morning rush, memory use climbs for an hour, until the program dies with `OutOfMemoryError`. The address service also reports bursts of 250 calls at once from this one program. Find both causes.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Two defaults. `Flux.create` with no strategy uses `BUFFER`, which has no limit: whatever the listener pushes while nobody is asking waits in memory. And `flatMap` without a number runs up to 256 address checks at once. The address service allows 50 per client, so most of the extra calls fail, and an error is terminal (Errors, retries and timeouts), so the stream can die as well as leak.", "code": "", "lang": ""},
   {"say": "Make each decision visible. Orders must not be lost, but the website can send orders again from a given order number, so a bounded buffer that fails is safe. The concurrency comes from the address service's limit.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Now check the size with numbers, not hope. 50 calls in flight at 30 ms each finish at most about 1,666 checks per second (Little's law: 50 / 0.03 s). The morning rush sends 2,000 orders per second, so the backlog grows by about 334 per second, and 10,000 slots last about 30 seconds. A burst of a few seconds fits. A rush that lasts an hour doesn't fit any buffer: it needs a faster consumer, more copies of the program, or a source that can be told to wait. A buffer only absorbs bursts; it never fixes a consumer that is slower on average.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Four belts, four backpressure decisions",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/BeltPolicies.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l07.*'",
  "steps": [
   "Run the tests once. All five fail. The tests use `TestPublisher.create()`, a test source you push items into by hand, as a source that can't slow down: it fails with `Can't deliver value due to lack of requests` when pushed without demand, just like `Flux.interval`.",
   "For each method in `BeltPolicies`, answer two questions before you write code: does the source honour `request(n)`, and may anything be lost?",
   "Write each method. Each one is a single operator.",
   "Run the tests until all five pass. Then read `bookCouriersKeepsTwentyInFlight`: it counts calls in flight under virtual time, so the count is exact."
  ],
  "hints": [
   "If `nightlyReport`'s first request is `9223372036854775807`, nothing between the test and the database changed the demand. `take(100)` would cap the request too, but it stops after 100 rows.",
   "If `latestTemperature` receives `201`, you buffered. If it waits and receives `205`, you dropped.",
   "If `webOrders` holds 1,000 orders but never fails, your buffer has no size. `onBackpressureError()` fails the first web-orders test instead, because it can't hold anything.",
   "If `bookCouriers` reports 100 calls in flight, you used `flatMap` without its concurrency argument. If it reports 1, you used `concatMap`."
  ],
  "done_when": "All five tests in `BeltPoliciesTest` pass."
 },
 "drill": {
  "title": "Check orders from a source that can't wait",
  "minutes": 4,
  "prompt": "Close this page. `webOrders` is a `Flux<WebOrder>` from a live connection that cannot slow down. Each order's address must be checked with `addresses.check(o)`, which returns a `Mono<Check>`. The address service allows 50 calls at once, bursts of up to 5,000 orders must be absorbed, and nothing may be lost silently: log the order that overflows. Write the chain, then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`subscribe(consumer)` and `block()` request `Long.MAX_VALUE`. Operators reshape that demand on its way up: `take(3)` asks for 3, `flatMap(call, 4)` for 4 and then 1 at a time.",
  "`limitRate(n)` turns a big request into batches of n, topped up by 75%: `10, 8, 8, ...`. Every item still arrives.",
  "A source that honours `request(n)` gives you backpressure for free. For one that can't slow down, you must pick a loss policy.",
  "`onBackpressureBuffer(n)`, `Drop`, `Latest` and `Error` all ask the source for everything. They decide what to keep, not how fast the source goes.",
  "`flatMap`'s concurrency (256 by default) is how many calls you have open at once. Set it from the smallest limit on the path.",
  "The limit: no operator makes a slow consumer faster. `onBackpressureBuffer()` with no size hides a backlog until memory runs out, and any buffer only absorbs bursts, never a consumer that is slower on average."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "The nightly report does `orderBook.rows(day).limitRate(100).concatMap(archive::store)`. What requests does the database cursor receive?",
   "options": ["One request for `Long.MAX_VALUE`", "100, then 75 at a time", "100, then nothing: `limitRate` stops after 100 rows", "1 at a time, because of `concatMap`"],
   "answer": 1,
   "why": "`limitRate(100)` requests 100 and tops up by 75 each time 75 have been delivered, however much the subscriber below it asks for. Unlike `take(100)`, it never ends the stream early. `concatMap` asks `limitRate` for one item at a time, but `limitRate` decides what reaches the cursor."},
  {"q": "A screen in the shop shows the oven temperature from a thermometer that sends 200 readings a second. The screen redraws 10 times a second. Which policy fits?",
   "options": ["`onBackpressureBuffer()`", "`onBackpressureBuffer(1_000)`", "`onBackpressureDrop()`", "`onBackpressureLatest()`"],
   "answer": 3,
   "why": "A temperature is a value where newer replaces older: when the screen asks, it wants the newest reading. `onBackpressureDrop` would show whichever reading arrives after the screen asks, which is fresh too, but it may wait for the next one and it throws away the newest one on hand. Both buffers would show old readings, in order, falling further behind."},
  {"q": "Orders arrive from the website, a source that can't slow down. None may be lost silently, and bursts of a few hundred are normal. Which line fits best?",
   "options": [
    "`orders.onBackpressureBuffer()`",
    "`orders.onBackpressureBuffer(1_000, o -> log.error(\"order overflow at {}\", o.id()))`",
    "`orders.onBackpressureLatest()`",
    "`orders.limitRate(100)`"
   ],
   "answer": 1,
   "why": "A bounded buffer absorbs the normal bursts. If the subscriber falls further behind, it cancels the source, logs the overflowing order and ends with an overflow error, so the gap is visible. The unbounded buffer reports nothing until memory runs out. `onBackpressureLatest` loses orders silently. `limitRate` changes requests, which a source that ignores demand doesn't read."},
  {"q": "`Flux.fromIterable(deliveries).flatMap(courier::book)` books 300 vans. The courier allows 20 open requests per customer and refuses the rest. What happens, and what is the fix?",
   "options": [
    "All 300 are booked, just more slowly; no fix needed",
    "`flatMap` opens up to 256 calls at once, most are refused, and the first unhandled refusal ends the stream; use `flatMap(courier::book, 20)`",
    "`flatMap` opens one call at a time; use `flatMap(courier::book, 20)` to speed it up",
    "Add `limitRate(20)` before `flatMap`"
   ],
   "answer": 1,
   "why": "The default concurrency is 256, so far more than 20 requests are open at once, and an unhandled refusal is a terminal error. Capping `flatMap` at 20 matches the courier. `limitRate(20)` only changes how many deliveries are requested from the list at a time; `flatMap` would still subscribe to as many calls as it has deliveries, up to 256."},
  {"q": "From \"Sizing a pool: CPU-bound, IO-bound and Little's law\": `flatMap(courier::book, 20)`, and each call takes 50 ms. What is the most this can book per second?",
   "options": ["20", "50", "400", "1,000"],
   "answer": 2,
   "why": "Little's law: in flight = rate x time, so rate = 20 / 0.05 s = 400 per second. To go faster you need more open requests (if the courier allows them) or faster calls. A per-second quota from the courier is a separate limit that a concurrency cap doesn't enforce.",
   "from": "exec-03"}
 ],
 "flashcards": [
  {"front": "What does `subscribe(consumer)` request from the source?", "back": "`Long.MAX_VALUE`: unbounded demand, unless an operator in between reshapes it."},
  {"front": "`Flux.range(1, 40).limitRate(10)`: what does the range see?", "back": "`request(10)`, then `request(8)` five times: it tops up by 75% of the batch."},
  {"front": "`limitRate(100)` vs `take(100)`?", "back": "`limitRate` caps each request and still delivers every item. `take` caps the request and ends the stream after 100."},
  {"front": "Does `onBackpressureDrop` (or `Buffer`, `Latest`) slow the source down?", "back": "No. They all ask the source for everything and decide what to do with items nobody asked for."},
  {"front": "A slow subscriber finally requests 1. What does it get from `onBackpressureLatest` vs `onBackpressureDrop`?", "back": "Latest: the newest item that arrived while it wasn't asking. Drop: nothing until the next item arrives after the request."},
  {"front": "What happens when `onBackpressureBuffer(1000)` overflows?", "back": "It cancels the source, and after the subscriber drains the 1,000 held items, it ends with an overflow error."},
  {"front": "What is `Flux.create`'s default overflow strategy?", "back": "`BUFFER`, with no limit. Pass a `FluxSink.OverflowStrategy` (DROP, LATEST, ERROR) to choose."}
 ],
 "terms": [
  {"term": "Demand", "plain": "How many more items a subscriber has asked for with `request(n)` and not yet received."},
  {"term": "Unbounded demand", "plain": "A request of `Long.MAX_VALUE`: send everything, as fast as you can."},
  {"term": "Prefetch", "plain": "Asking for a batch of items in advance and refilling it as items go out, as `publishOn` and `limitRate` do."},
  {"term": "limitRate", "plain": "An operator that splits a big demand from below into batches of n requested from above."},
  {"term": "Loss policy", "plain": "Buffer, drop, keep the latest, or fail: what to do with items a source pushes without demand."},
  {"term": "OverflowException", "plain": "Reactor's error for more items than were requested, from a source or from a full bounded buffer."},
  {"term": "Concurrency cap", "plain": "The most inner publishers `flatMap` subscribes to at once; 256 by default."}
 ],
 "explain_back": {
  "prompt": "A teammate got `OverflowException: Could not emit tick ... due to lack of requests` and wants to add `onBackpressureBuffer()` because \"that's what backpressure is for\". Explain what backpressure really is in Reactor, why their fix is risky, and what you would ask before choosing a fix.",
  "answer": "Backpressure is the subscriber telling the source how many items it can take, with `request(n)`, and the source sending no more than that. A source like `Flux.interval` can't wait, so when the consumer falls behind, it fails instead of slowing down. `onBackpressureBuffer()` with no size doesn't slow anything either: it asks the source for everything and keeps every item the consumer hasn't asked for in a queue with no limit. The error disappears, and the backlog grows until memory runs out. Before choosing, I'd ask two things: can we use a source that honours demand instead, and if not, what may we lose? If old values are useless, keep the latest. If samples are fine to skip, drop them and count the drops. If nothing may be lost, use a bounded buffer that fails loudly and a way to resume, and check with Little's law that the consumer is fast enough on average, because a buffer only absorbs bursts."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Sources that pull.** `Flux.generate` calls your generator once per requested item, so it is backpressured by construction: good for paging through a web service or reading a file line by line. `Flux.create` gives you a `FluxSink` for push APIs, and `sink.onRequest(n -> ...)` lets you pull n items from an API that supports it, which turns a push bridge into a real backpressured source.\n\n**More buffer options.** `onBackpressureBuffer(maxSize, onOverflow, BufferOverflowStrategy.DROP_OLDEST)` keeps the buffer bounded but evicts old items instead of failing (`DROP_LATEST` and `ERROR` are the other strategies). `onBackpressureBuffer(Duration ttl, int maxSize, onEvicted)` also evicts items older than the ttl, for data that goes stale.\n\n**Prefetch everywhere.** Many operators take a prefetch argument: `flatMap(fn, concurrency, prefetch)` sets how many items each inner is asked for (32 by default), and `concatMap(fn, prefetch)` and `publishOn(scheduler, prefetch)` likewise. Smaller numbers mean less memory and more request round trips.\n\n**Demand across the network.** Reactive Streams demand stops at the edge of the program. RSocket, a network protocol designed for reactive streams, carries `request(n)` across the wire. Plain web requests have no `request(n)` of their own: a server streaming to a slow client relies on the flow control of TCP, the protocol under most network connections, and it is the server library's job to turn a full connection into lower demand on your `Flux`.\n\n**Deprecated name.** `limitRequest(n)` is deprecated in favour of `take(n)`, which in 3.8 caps the upstream request at n by default."
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
