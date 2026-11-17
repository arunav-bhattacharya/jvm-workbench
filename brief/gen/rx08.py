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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """The bakery has started a little radio show. Every morning at seven, the head baker reads out the day's bread over the shop's radio, live. If you switch on at five past, you missed the rye. The bakery also keeps a recording of each show, and anyone who presses play hears it from the first word. The live show is shared and goes on whether anyone listens. The recording starts again for each listener.

Reactor's publishers come in the same two kinds, hot and cold, and the trap is not knowing which one you hold. Six screens open six connections to the oven where one would do. A screen that switches on late shows nothing until the next reading. And a test that should check all of it can pass without running a line.

Backpressure in practice ended with two screens and one thermometer. In this lesson, we'll share one source among many subscribers, push values in from ordinary code with Sinks, and test it all on a fake clock. Then we'll track down a failing operator, and end by asking when Reactor is worth it. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """A **cold** publisher, a source of items such as a `Flux`, does its work again for every subscriber, as Mono and Flux showed. It's the recording: each listener who presses play gets the show from the first word, and the bakery plays one copy per listener. That's right for one call per request. It's wrong for the oven thermometer when six screens watch it: six connections to the oven, six copies of the same readings.

A **hot** publisher is the live show. It produces whether or not anyone listens, and subscribers share what it produces from the moment they join.

Reactor turns cold into hot with a few operators. They differ in two decisions: when to connect to the source, and what a subscriber who tunes in late hears.

| Operator | Connects | A late subscriber gets | Disconnects |
|---|---|---|---|
| `share()`, which is `publish().refCount()` | at the first subscriber | only new items | when the last one leaves |
| `replay(n).refCount()` | at the first subscriber | the last n items, then new ones | when the last one leaves |
| `publish().autoConnect(n)` | when n have subscribed | only new items | never |
| `cache()` | at the first subscriber | every item, from the start | never |

In radio terms, `share()` is the live show. `replay(1)` is a show that repeats its last announcement for anyone who tunes in. `cache()` is a recorder that keeps the whole broadcast and plays it to every newcomer from the start, while the tapes pile up. `refCount` switches the transmitter off when the last listener leaves, and `autoConnect(n)` waits for n listeners, then never switches off.

`HotColdDemo`, in the Try it, runs the thermometer as a cold feed: a reading every 100 ms, five readings, `200` to `204`. Screen A subscribes at once and screen B 250 ms later. The figure below draws three of the runs:

```text
1. cold                      connections=2
     A=[200, 201, 202, 203, 204]
     B=[200, 201, 202, 203, 204]
2. share()                   connections=1
     A=[200, 201, 202, 203, 204]
     B=[202, 203, 204]
3. replay(1).refCount()      connections=1
     A=[200, 201, 202, 203, 204]
     B=[201, 202, 203, 204]
4. cache()                   connections=1
     A=[200, 201, 202, 203, 204]
     B=[200, 201, 202, 203, 204]
```

Cold, B opened a second connection and started from the first reading. With `share()`, there was one connection, and B heard only the readings from 300 ms on. With `replay(1).refCount()`, B got the 200 ms reading the moment it subscribed, then the live ones. With `cache()`, B got all of them, the two it missed included. The cache keeps every item for as long as the `Flux` lives, and for a feed that never ends, that's a memory leak. Prefer `replay(n)` or `cache(n)` there. `Mono.cache(ttl)` is the right tool for a value that should be loaded again now and then, such as the price list.

Here the radio picture breaks. A radio station keeps broadcasting to an empty room. With `refCount`, the show stops when the last listener leaves, and the next listener starts it again.

Two details matter in production. `publish` follows the slowest subscriber: it asks the source only for what every subscriber can take, so one slow screen slows them all (pair it with a loss policy from Backpressure in practice). And `refCount(1, Duration.ofSeconds(5))` adds a grace period. When the last subscriber leaves, it waits 5 seconds before it disconnects, so a screen that restarts doesn't make you reconnect to the oven.

**Cold plays from the start for each subscriber. Hot is shared, and the operator decides what a latecomer gets.**

All of these share a source that already exists. Sometimes the values come from code that isn't a publisher at all."""

# ---------------------------------------------------------------- section 1
J_SINK = """Sinks.Many<OrderEvent> bell = Sinks.many().multicast().directBestEffort();
Flux<OrderEvent> live = bell.asFlux();                     // what the kitchen screens subscribe to
Sinks.EmitResult result = bell.tryEmitNext(event);         // what a till calls"""
K_SINK = """val bell: Sinks.Many<OrderEvent> = Sinks.many().multicast().directBestEffort()
val live: Flux<OrderEvent> = bell.asFlux()                 // what the kitchen screens subscribe to
val result: Sinks.EmitResult = bell.tryEmitNext(event)     // what a till calls"""

S1 = """Sometimes the values come from ordinary code: a callback from a library, a handler for a web request, a job that runs every minute. In the bakery, each till in the shop rings a bell when an order is placed, and every screen in the kitchen hears it. Any till can ring it, and anyone in the kitchen at that moment hears the ring. Someone who walks in later didn't hear the earlier rings.

A **sink** is Reactor's safe way to ring that bell from code. It takes values from ordinary method calls and hands them to subscribers as a `Flux` or a `Mono`. (Processors used to do this job, and Reactor has phased them out in favour of `Sinks`.)

""" + pair(J_SINK, K_SINK) + """

`Sinks.many().multicast()` sends each item to the subscribers present at that moment, and it comes in three flavours. `onBackpressureBuffer()` buffers for slow subscribers, and keeps the items pushed before the first subscriber arrives, for that subscriber. By default it also shuts down for good when its last subscriber leaves, so a subscriber that comes later receives only `onComplete`. `directBestEffort()` keeps no buffer: a subscriber that isn't asking misses the item, and the sink keeps working with no subscribers at all. `directAllOrNothing()` drops the item for everyone if one subscriber isn't ready.

`SinksDemo`, in the Try it, shows the first two flavours after everyone has left:

```text
2. onBackpressureBuffer() after everyone left, a new subscriber [completed]
2. directBestEffort()     after everyone left, a new subscriber [got 42]
```

There are other kinds too. `many().replay()` keeps history for late subscribers (`all()`, `limit(n)`, `limit(Duration)` or `latest()`), `many().unicast()` allows exactly one subscriber, and `Sinks.one()` and `Sinks.empty()` carry a single value or a bare completion.

The trap is threads. `tryEmitNext` never blocks and never retries. If two threads call it at the same moment, one of them gets `EmitResult.FAIL_NON_SERIALIZED`, and its item isn't emitted. That's rule 1.3 from Why reactive at work: a subscriber must never get two signals at once. The sink notices the overlap, and instead of breaking the rule, it fails the second call. Here the bell picture breaks: two hands on a real bell rope still make a ring, while the sink refuses one of them.

Ignore the result, and items vanish. The demo's race lets 8 threads emit 10,000 items each:

```text
5. tryEmitNext from 8 threads    received 11,679 of 80,000 (68,321 emits failed)
6. emitNext + busyLooping        received 80,000 of 80,000 (0 emits failed)
```

In that run, 68,321 items reached the sink at the same moment as another one. The sink said no to each of them, politely, with a return value nobody read. The number changes from run to run (15,391 arrived in the Kotlin run). Either check every result, or call `emitNext(item, handler)` with a handler that retries. `Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1))` spins until the sink is free, for up to a second, which is how the second line got all 80,000. Its Javadoc asks you not to keep and reuse one, so create one per call. Wrapping the emit in a lock works too.

**A sink refuses an overlapping emit. From several threads, retry it or serialize it.**

We now have hot sources, shared sources and sinks, and each one has timing in it. Testing timing with a real clock is slow and flaky, so Reactor gives us a fake one."""

# ---------------------------------------------------------------- section 2
J_SV = """StepVerifier.create(orderPage.quote("chocolate", "home"))
        .expectNext(expectedQuote)
        .expectComplete()
        .verify(Duration.ofSeconds(1));"""
K_SV = """StepVerifier.create(orderPage.quote("chocolate", "home"))
    .expectNext(expectedQuote)
    .expectComplete()
    .verify(Duration.ofSeconds(1))"""

S2 = """A reactive test has to subscribe, check each signal in order, and fail when anything else happens. `StepVerifier`, from the reactor-test library, does exactly that. It's a quality inspector at the end of the belt with a script in her hand: first a loaf named `rye-1`, then the end-of-day bell, and nothing else.

""" + pair(J_SV, K_SV) + """

Four rules, each learned from a test that lied:

1. Nothing runs until `verify()`, or a shortcut such as `verifyComplete()` or `verifyError()`. A test that ends at `expectComplete()` never subscribes, and passes whatever the code does. It's the most optimistic test you will ever write.
2. `verify()` has no time limit by default, so a publisher that hangs also hangs the build. Pass a `Duration`, or set `StepVerifier.setDefaultTimeout(...)` once.
3. `StepVerifier.withVirtualTime(() -> ...)` swaps Reactor's schedulers for a **virtual clock**, a fake clock that the test winds forward, so a one-day delay is checked in milliseconds. Build the publisher **inside** the supplier lambda. A `Mono.delay` built earlier has already picked the real clock, and the test times out.
4. `expectNoEvent(d)` checks that nothing happens during d of virtual time. The subscription counts as an event, so put `expectSubscription()` first.

`StepVerifierDemo`, in the Try it, breaks the rules on purpose:

```text
1. no verify():     subscriptions=0, wrong expectation unnoticed
2. virtual time:    one day took 52 ms of real time
3. expectNoEvent first: expectation failed (expected no event: onSubscribe(reactor.core.publisher.MonoDelay$MonoDelayRunnable@2db7a79b))
4. built outside the supplier: VerifySubscriber timed out on reactor.core.publisher.MonoIgnoreThen$ThenIgnoreMain@47db50c5
```

The first test expected `burnt` from a `Mono` that says `baked`, and never noticed, because it never subscribed. The second checked a whole day of waiting in 52 ms. The third and fourth broke rules 4 and 3, and failed as they should. Here the inspector picture breaks in our favour: a real inspector can't wind the clock forward by a day.

For a source you drive by hand, there's `TestPublisher`. Call `next(...)`, `complete()` or `error(...)` from the test, then check `wasCancelled()` or `assertMinRequested(n)`. `TestPublisher.create()` respects demand like a real source and fails if you push without it; `createNoncompliant(...)` breaks the spec on purpose (Why reactive). `PublisherProbe` answers a different question: was this branch subscribed at all? Use it to prove that a `switchIfEmpty` fallback ran, or didn't. All the virtual-time tests in this track's labs, from the mill's backoff to the courier's limit, are built from these pieces.

**End every StepVerifier with verify and a time limit, and build timed publishers inside withVirtualTime.**

A good test tells you that something failed. When a chain fails in a running program, the next question is where."""

ASIDE = {
    "title": "Why not just call block() in a test?",
    "body": "For a single value, `block()` works, and it's fine for a quick check. But it can't check the order of the signals, it can't prove that nothing arrived for 90 seconds, and it can't fake time, so a one-hour delay takes an hour. It also waits forever on a publisher that never finishes, unless you pass it a timeout. `StepVerifier` does all of that, and when it fails, its message says which step went wrong.",
}

# ---------------------------------------------------------------- section 3
J_DBG = """Mono<Integer> price = priceRow(cake).checkpoint("price-row");   // name the place, cheaply
Flux<Integer> rows = Flux.range(1, 5).log("rows").take(2);      // print every signal at this point"""
K_DBG = """val price: Mono<Int> = priceRow(cake).checkpoint("price-row")   // name the place, cheaply
val rows: Flux<Int> = Flux.range(1, 5).log("rows").take(2)      // print every signal at this point"""

S3 = """A stack trace from a reactive chain shows where the error was raised and how the subscription got there. It almost never shows where you wrote the operator that failed. In `DebugDemo`, a method called `priceRow(cake)` builds `Flux.just(2400, 2600).single()`: the cake has two price rows, and the code expects one. `single()` fails:

```text
1. no help
   java.lang.IndexOutOfBoundsException: Source emitted more than one item
   top frame: reactor.core.publisher.MonoSingle$SingleSubscriber.onNext(MonoSingle.java:135)
   any frame in priceRow(), where single() was written? false
```

The top frame is Reactor's `MonoSingle`, and no frame of the trace is in `priceRow()`. Mono and Flux explains why. `priceRow()` only filled in the order form and returned. By the time `single()` sees the second row, the data is flowing, and the frame of `priceRow()` is long gone.

`checkpoint("price-row")` marks a place in the chain. When an error passes through it, Reactor attaches a suppressed exception, an extra exception carried inside the first one, that names the place:

```text
2. checkpoint("price-row")
   ...
   Error has been observed at the following site(s):
   *__checkpoint -> price-row
```

It's cheap, so put one at the edges of your own chains, named after what they do. `checkpoint("price-row", true)` also records a stack trace when the chain is built, which points at the line in your code. The cost is capturing that trace every time the chain is built. The demo's third run shows it pointing at the line in `main` where the checkpoint was written.

`Hooks.onOperatorDebug()` does the same for every operator in the program, and the reference guide calls it a last resort because of the cost. For a program that runs for real, there's the reactor-tools agent (`ReactorDebugAgent.init()` as the first line of `main`), which adds the same information by changing your classes as they load. It's a separate dependency, and not in the labs.

""" + pair(J_DBG, K_DBG) + """

`log("rows")` prints every signal that passes that point:

```text
[ INFO] (main) | onSubscribe([Synchronous Fuseable] FluxRange.RangeSubscription)
[ INFO] (main) | request(2)
[ INFO] (main) | onNext(1)
[ INFO] (main) | onNext(2)
[ INFO] (main) | cancel()
```

It's the quickest way to see this track's ideas in a real chain: the slip that `take(2)` wrote, the cancel it sent up once it had enough, and the thread each signal arrived on. It logs through SLF4J, a common Java logging front end, when that is on the classpath.

**When a chain fails far from where it was built, name the place with checkpoint.**

That completes the toolkit. The last question is when to reach for it at all."""

# ---------------------------------------------------------------- section 4
S4 = """Reactor isn't the default answer for new JVM code, and the Spring team, the home of Reactor, says so itself. The Spring Framework reference compares Spring MVC, its classic style in which each request holds a thread, with the reactive Spring WebFlux. It reads: "If you have a Spring MVC application that works fine, there is no need to change. Imperative programming is the easiest way to write, understand, and debug code." Imperative code is ordinary step-by-step code, one line after another. The reference warns about "the steep learning curve", tells you to "start small and measure the benefits", and adds: "We expect that, for a wide range of applications, the shift is unnecessary." Why reactive quoted the same docs on speed: reactive code doesn't make programs faster; it lets them scale with fewer threads when calls have to wait.

Virtual threads (final in JDK 21) took away most of the thread-count argument. Mark Paluch of the Spring team wrote in 2022, while they were still a preview: "The reasons to use asynchronous programming models go away in many cases if we start with the assumption that our code runs on Virtual Threads." The same post keeps a place for reactive. ReactiveX-style APIs "remain a powerful way to compose concurrent logic and a natural way for dealing with streams". They are also "the right approach for concurrent scenarios in which declarative concurrency (such as scatter-gather) matters." ReactiveX is the family of libraries that Reactor's style comes from, and scatter-gather means sending many calls out at once and collecting the answers.

So here is the position I'd take for your own programs:

- For one request and one reply, over databases and services whose clients block, use virtual threads and plain code. Don't rewrite a working service in Reactor.
- For streams, such as live updates to browsers, a feed that never ends, or anything where demand, cancellation and a loss policy matter, Reactor earns its complexity.
- For many calls composed with timeouts, retries and fan-out, Reactor's operators are hard to beat. Coroutines, and structured concurrency once it is final (it is a preview in JDK 25), are the alternatives that read from top to bottom.
- In a program that is already reactive from end to end, stay reactive, and keep the few blocking calls on `boundedElastic`.
- In Kotlin, coroutines give code that reads from top to bottom over the same idea. `kotlinx-coroutines-reactor` bridges both ways (`awaitSingle()`, `mono { }`, `Flow.asFlux()`), and Spring maps `Mono` to `suspend` and `Flux` to `Flow`.

Quick check: the bakery's website has two pages. One reads an order from the database and shows it. The other shows the oven's live temperature to browsers that read at different speeds. Which one needs `request(n)`, and why? (The second. The first waits for one reply, which a virtual thread does cheaply. The second has a fast producer and slow consumers, and only demand or a loss policy stops readings piling up in memory for the slow ones.)

That last bullet is where the next track begins."""

# ---------------------------------------------------------------- figure: one feed, three ways to share it
X0, PX = 150, 0.8
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 290" role="img" aria-label="A thermometer feed emits readings 0 to 4 at 100 to 500 ms. Screen A gets all five. '
       'Screen B joins at 250 ms: with share() it gets 2, 3, 4; with replay(1) it gets 1 at once, then 2, 3, 4; with cache() it gets 0 and 1 at once, then 2, 3, 4.">')
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

# ---------------------------------------------------------------- closing: the end of the track
CLOSING = """We started with fourteen loaves on a doorstep, cured by a slip that said "send me 10 more". The bakery built a whole line on it: order forms, stations, joined belts, a broken oven, workers, a small table and a live show. Reactor frees threads while calls wait, at the price of code written as a chain of operators.

Now look in your code for `cache()` on a feed that never ends, and for a `StepVerifier` without `verify`.

Next, we'll start the Kotlin coroutines track with Suspend functions from zero. Coroutines free the thread just as Reactor does, but the code still reads from top to bottom, like a recipe. How can a function pause halfway without holding its thread?"""

# ---------------------------------------------------------------- compare, worked, drill
CJ = '''// Reactor: a bell that till threads ring, and a shared thermometer feed
private final Sinks.Many<OrderEvent> bell = Sinks.many().multicast().directBestEffort();

void ring(OrderEvent e) {
    bell.emitNext(e, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)));
}

Flux<OrderEvent> live() { return bell.asFlux(); }

Flux<Reading> temperature = oven.readings()
        .replay(1)                                    // late screens get the latest reading
        .refCount(1, Duration.ofSeconds(5));          // disconnect 5 s after the last one leaves'''
CK = '''// Kotlin coroutines: SharedFlow for events, StateFlow for "the latest value"
private val bell = MutableSharedFlow<OrderEvent>(extraBufferCapacity = 1_000)

fun ring(e: OrderEvent) {
    check(bell.tryEmit(e)) { "the screens are too slow" }   // thread-safe; suspend emit() waits instead
}

val live: SharedFlow<OrderEvent> = bell.asSharedFlow()

val temperature: StateFlow<Reading?> = oven.readings()
    .stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)   // latest reading, stop 5 s after the last leaves'''

W0 = '''Mono<Status> awaitDone(String cakeId) {
    return Flux.interval(Duration.ofSeconds(30))              // ask every 30 s
            .concatMap(tick -> oven.status(cakeId))           // one call at a time
            .filter(Status::isDone)
            .next()                                           // the first DONE, then stop asking
            .timeout(Duration.ofMinutes(5));
}'''
W0K = '''fun awaitDone(cakeId: String): Mono<Status> =
    Flux.interval(Duration.ofSeconds(30))                     // ask every 30 s
        .concatMap { oven.status(cakeId) }                    // one call at a time
        .filter(Status::isDone)
        .next()                                               // the first DONE, then stop asking
        .timeout(Duration.ofMinutes(5))'''
W1 = '''FakeOven oven = new FakeOven(BAKING, BAKING, DONE);

StepVerifier.withVirtualTime(() -> new CakePoller(oven).awaitDone("cake-7"))   // 1. build it inside the supplier
        .expectSubscription()                                                   // 2. before any expectNoEvent
        .expectNoEvent(Duration.ofSeconds(90))                                  // 3. silent until the third question
        .expectNext(DONE)
        .verifyComplete();

assertThat(oven.calls()).isEqualTo(3);'''
W1K = '''val oven = FakeOven(BAKING, BAKING, DONE)

StepVerifier.withVirtualTime { CakePoller(oven).awaitDone("cake-7") }       // 1. build it inside the supplier
    .expectSubscription()                                                   // 2. before any expectNoEvent
    .expectNoEvent(Duration.ofSeconds(90))                                  // 3. silent until the third question
    .expectNext(DONE)
    .verifyComplete()

assertThat(oven.calls()).isEqualTo(3)'''
W2 = '''FakeOven stuck = new FakeOven(BAKING);                     // baking forever

StepVerifier.withVirtualTime(() -> new CakePoller(stuck).awaitDone("cake-8"))
        .expectSubscription()
        .thenAwait(Duration.ofMinutes(5))                    // 4. jump to the deadline
        .expectError(TimeoutException.class)
        .verify(Duration.ofSeconds(1));                      // 5. a real-time safety net'''
W2K = '''val stuck = FakeOven(BAKING)                                // baking forever

StepVerifier.withVirtualTime { CakePoller(stuck).awaitDone("cake-8") }
    .expectSubscription()
    .thenAwait(Duration.ofMinutes(5))                        // 4. jump to the deadline
    .expectError(TimeoutException::class.java)
    .verify(Duration.ofSeconds(1))                           // 5. a real-time safety net'''

DJ = '''StepVerifier.withVirtualTime(() -> Mono.delay(Duration.ofHours(1)).thenReturn("cooled"))
        .expectSubscription()
        .expectNoEvent(Duration.ofHours(1))
        .expectNext("cooled")
        .expectComplete()
        .verify(Duration.ofSeconds(1));'''
DK = '''StepVerifier.withVirtualTime { Mono.delay(Duration.ofHours(1)).thenReturn("cooled") }
    .expectSubscription()
    .expectNoEvent(Duration.ofHours(1))
    .expectNext("cooled")
    .expectComplete()
    .verify(Duration.ofSeconds(1))'''

L = {
 "id": "rx-08",
 "title": "Hot and cold publishers, Sinks, and StepVerifier",
 "minutes": 40,
 "goal": "By the end you can share one source between many subscribers with the right late-subscriber behaviour, push values in from many threads with Sinks without losing any, test timing with StepVerifier and virtual time, find a failing operator with checkpoint and log, and say when Reactor is still the right tool.",
 "opening": OPENING,
 "warmup": {
  "q": "The oven thermometer sends a reading every 100 ms. Screen A subscribes at 0 ms and screen B at 250 ms, both to `thermometer.share()`. What does B receive first?",
  "options": [
   "The first reading, because `share()` replays from the start",
   "The reading sent at 200 ms, because `share()` keeps the latest",
   "The reading sent at 300 ms",
   "Nothing: `share()` allows one subscriber"
  ],
  "answer": 2,
  "why": "`share()` is `publish().refCount()`: one subscription to the source, shared with whoever is subscribed when an item arrives. B joined at 250 ms, so its first item is the one sent at 300 ms. Repeating the latest reading is `replay(1).refCount()`, and replaying everything is `cache()`. The first section runs all of them on the same thermometer."
 },
 "sections": [
  {
   "h": "Cold sources play from the start for each subscriber; hot ones are shared live",
   "body": S0,
   "figure": {"svg": SVG, "caption": "One feed, three ways to share it with a screen that joins at 250 ms. Items on the live lanes arrive as the source sends them; the extra items at 250 ms are replayed the moment B subscribes."},
   "try": {
    "title": "Five ways to share one thermometer",
    "minutes": 4,
    "steps": [
     "`HotColdDemo` runs a cold thermometer feed (a reading every 100 ms, five readings) with screen A subscribing at once and B 250 ms later. It tries cold, `share()`, `replay(1).refCount()`, `cache()` and `publish().autoConnect(2)`.",
     "For each run, predict the number of connections and what B receives.",
     "Run it. Then explain the `autoConnect(2)` line: why does A get all five readings, starting late?"
    ],
    "code": code("HotColdDemo"),
    "expect": "Cold: 2 connections, and both screens get all five readings. `share()`: 1 connection, B gets `202` to `204`. `replay(1).refCount()`: B also gets `201` the moment it subscribes. `cache()`: B gets all five. `autoConnect(2)`: 1 connection that opens only when B subscribes at 250 ms, so both get all five, and A waited 250 ms for its first reading."
   },
   "refs": [
    {"title": "Reactor reference: Hot versus cold (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/reactor-hotCold.adoc", "kind": "docs"},
    {"title": "Reactor reference: Broadcasting to multiple subscribers with ConnectableFlux (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/advancedFeatures/advanced-broadcast-multiple-subscribers-connectableflux.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Sinks push values in from ordinary code, one thread at a time",
   "body": S1,
   "try": {
    "title": "Who gets what from a sink",
    "minutes": 4,
    "steps": [
     "`SinksDemo` pushes values into a multicast sink before and between two subscribers, checks two multicast flavours after every subscriber has left, fills a `replay().limit(2)` sink, tries two subscribers on a unicast sink, and finally lets 8 threads emit 10,000 items each, first with `tryEmitNext`, then with `emitNext` and `busyLooping`.",
     "Predict each line before you run it. For the race, guess how many of the 80,000 items arrive.",
     "Run it twice and compare the race numbers."
    ],
    "code": code("SinksDemo"),
    "expect": "Multicast: `early=[10, 1, 2, 3]` (the 10 waited in the buffer for the first subscriber) and `late=[3]`. After everyone left, the `onBackpressureBuffer()` sink only completes the new subscriber, while `directBestEffort()` delivers `got 42`. Replay with limit 2: `[2, 3]`. Unicast: the second subscriber fails with `Sinks.many().unicast() sinks only allow a single Subscriber`. The `tryEmitNext` race delivers only a fraction of the 80,000 (11,679 and 15,391 in two runs here), with a different number each run; `emitNext` with `busyLooping` delivers all 80,000."
   },
   "refs": [
    {"title": "Reactor reference: Sinks (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/processors.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "StepVerifier checks every signal, and virtual time fakes the clock",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "Break four StepVerifier rules",
    "minutes": 4,
    "steps": [
     "`StepVerifierDemo` runs five small tests: one without `verify()`, a one-day delay under virtual time, `expectNoEvent` as the first step, a delay built outside the virtual-time supplier, and a `TestPublisher` driven by hand. (It runs from `src/demo`, so the lab's build adds reactor-test to the demo classpath.)",
     "Predict which ones pass, which fail, and with what message.",
     "Run it. In part 1, add `.verify()` to the end of the line and run it again."
    ],
    "code": code("StepVerifierDemo"),
    "expect": "Part 1 reports `subscriptions=0`: without `verify()` nothing ran, and the wrong expectation (`burnt`) went unnoticed. After you add `.verify()`, it throws an `AssertionError` saying it expected `burnt` and got `baked`. Part 2 checks a full day in a few dozen milliseconds. Part 3 fails with `expected no event: onSubscribe(...)`. Part 4 fails with `VerifySubscriber timed out`, because the delay holds the real clock. Part 5 passes."
   },
   "refs": [
    {"title": "Reactor reference: Testing (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/testing.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Find the failing operator with checkpoint, and watch the signals with log",
   "body": S3,
   "try": {
    "title": "Find the operator that failed",
    "minutes": 3,
    "steps": [
     "`DebugDemo` runs a chain whose `single()` sees two price rows, three times: plain, with `checkpoint(\"price-row\")`, and with `checkpoint(\"price-row\", true)`. Then it puts `log(\"rows\")` between a range and `take(2)`.",
     "Run it. For each of the first three runs, find the information that tells you where the failing operator was written.",
     "Predict the `log` output first: which `request` and which last signal will it show?"
    ],
    "code": code("DebugDemo"),
    "expect": "All three report `IndexOutOfBoundsException: Source emitted more than one item` with `MonoSingle` as the top frame, and no frame in `priceRow()`. The plain run gives no clue where it came from. The checkpoint run names `price-row`. The run with `true` adds an assembly trace pointing at the line in `main` where the checkpoint was written. The log shows `onSubscribe`, `request(2)`, `onNext(1)`, `onNext(2)` and `cancel()`: `take(2)` capped the demand and then cancelled the range."
   },
   "refs": [
    {"title": "Reactor reference: Debugging Reactor (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/debugging.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "When reactive is still worth it, and when plain code on virtual threads is enough",
   "body": S4,
   "refs": [
    {"title": "Embracing Virtual Threads (Spring blog, Mark Paluch, 2022)", "url": "https://spring.io/blog/2022/10/11/embracing-virtual-threads", "kind": "read"},
    {"title": "Spring Framework reference: Spring WebFlux overview, applicability and performance", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A bell for order events and a shared feed in Reactor and Kotlin",
  "java": {"title": "Kitchen.java (Reactor)", "src": CJ},
  "kotlin": {"title": "Kitchen.kt (coroutines)", "src": CK},
  "note": "The shapes match: a multicast sink is close to a `MutableSharedFlow`, and `replay(1).refCount(1, grace)` is close to `stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)`. The differences are in threads and lifetime. A `MutableSharedFlow` accepts emissions from any number of threads at once; its `tryEmit` fails only when the buffer is full, and `emit` suspends instead. A Reactor sink refuses overlapping emissions unless you retry or serialize them. And `stateIn` and `shareIn` need a `CoroutineScope`: the shared source lives in that scope and is cancelled with it, which is structured concurrency. Reactor's sharing lives as long as subscribers keep it alive. A `StateFlow` also always has a current value and skips values equal to the last one, which `replay(1)` does not. The coroutines track covers `SharedFlow` and `StateFlow` in detail."
 },
 "worked": {
  "title": "Test a cake-status poller in milliseconds",
  "steps": [
   {"say": "After a cake goes into the oven, a poller asks the oven's controller for its status every 30 seconds until it says `DONE`, and gives up after 5 minutes. A real-time test would take 90 seconds for the happy path and 5 minutes for the timeout. Here is the code under test.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "The happy path: the fake oven answers `BAKING` twice, then `DONE`. Under virtual time the questions come at 30, 60 and 90 seconds of fake time. `expectNoEvent(90 s)` proves nothing came out earlier, and `DONE` arrives exactly at 90 s.",
    "code": W1, "lang": "java", "alt_code": W1K, "alt_lang": "kotlin"},
   {"say": "The timeout path: the cake never finishes. Jump the clock to the deadline and expect the `TimeoutException`. Keep a real-time limit on `verify` as well, so a mistake makes the test fail in one second instead of hanging.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Both tests run in a fraction of a second. If one of them hangs instead, look at where the poller is built. `Flux.interval` and `timeout` pick their scheduler when the chain is built, so a poller created before `withVirtualTime` runs on the real clock. The same goes for a `Mono` built once in a `@BeforeEach` method and kept in a field.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "An order bell for the kitchen and two shared feeds",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/OrderBell.java", f"{lab}/main/{P}/SharedFeeds.java", f"{lab}/main/{P}/OrderEvent.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l08.*'",
  "steps": [
   "Run the tests once. All six fail. `OrderEvent` is one thing that happened to a cake order, `OrderBell` is the bell the tills ring, and `SharedFeeds` shares a thermometer feed and caches the price list.",
   "`OrderBell`: choose the sink from the Javadoc of `live()` (only events rung after you subscribed, nothing kept while nobody listens, and it survives every listener leaving). Then make `ring` safe for 8 threads at once, and return a read-only view from `live()`.",
   "`SharedFeeds.shareWithLatest`: one connection to the thermometer, the latest reading for late subscribers, and a disconnect when the last subscriber leaves.",
   "`SharedFeeds.cacheFor`: load at most once per ttl. Read how the test controls the clock with `VirtualTimeScheduler.getOrSet()` and `advanceTimeBy`.",
   "Run the tests until all six pass, then once more: the 8-thread test must pass every time."
  ],
  "hints": [
   "If the hot test finds event 0 in the early listener's list, your sink kept events rung before anyone subscribed: `multicast().onBackpressureBuffer()` does that. The same sink fails the \"every listener has left\" test with a completion.",
   "If the 8-thread test receives fewer than 16,000 events, you ignored the result of `tryEmitNext`. If it reports crashed threads, you used `EmitFailureHandler.FAIL_FAST`, which throws on `FAIL_NON_SERIALIZED`.",
   "`share()` fails the late-subscriber test (no latest value); `cache()` and `replay(1).autoConnect()` fail the disconnect test (they never cancel the source).",
   "`Mono.cache()` with no argument never loads again. There is a version that takes a `Duration`."
  ],
  "done_when": "All six tests in `HotPublishersTest` pass, twice in a row."
 },
 "drill": {
  "title": "A one-hour test that runs in milliseconds",
  "minutes": 3,
  "prompt": "Close this page. A cake must cool for an hour before it can be iced. Write a `StepVerifier` test for `Mono.delay(Duration.ofHours(1)).thenReturn(\"cooled\")` that proves nothing is emitted before the hour is up, then `cooled` and completion, runs in milliseconds, and can't hang the build. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`share()` (`publish().refCount()`) gives late subscribers only new items; `replay(n).refCount()` replays the last n; `cache()` replays everything, forever. `refCount` disconnects when the last subscriber leaves, `autoConnect` never does.",
  "Sinks push values from ordinary code. `tryEmitNext` refuses overlapping calls with `FAIL_NON_SERIALIZED`: check the result, or use `emitNext` with `busyLooping`. A `multicast().onBackpressureBuffer()` sink shuts down when its last subscriber leaves; `directBestEffort()` survives an empty room.",
  "StepVerifier runs nothing until `verify()`. Give it a time limit, build the publisher inside the `withVirtualTime` supplier, and call `expectSubscription()` before `expectNoEvent`.",
  "`checkpoint(\"name\")` tags errors with a place in your chain cheaply; `log()` prints every signal at one point.",
  "The limit of the whole toolkit: reactive code is harder to read, debug and teach, and it isn't faster. For one request and one reply over blocking clients, the Spring team itself says plain code, now on virtual threads, is enough."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "Two till threads call `bell.tryEmitNext(event)` on the same `Sinks.many().multicast()` sink at the same moment, and ignore the return value. What can happen?",
   "options": [
    "Both events are emitted, in some order",
    "One call returns `FAIL_NON_SERIALIZED` and its event is never emitted",
    "The sink buffers the second event and emits it later",
    "The sink throws `ConcurrentModificationException`"
   ],
   "answer": 1,
   "why": "Reactor sinks detect overlapping emissions and refuse them instead of blocking or queueing, so one of the two calls gets `FAIL_NON_SERIALIZED`. Ignoring the result loses that event silently. Use `emitNext(event, EmitFailureHandler.busyLooping(...))`, which retries, or serialize the calls."},
  {"q": "A test reads `StepVerifier.create(orders.cancel(\"order-42\")).expectNext(\"CANCELLED\").expectComplete();` and passes. The cancel code is in fact broken. Why does the test pass?",
   "options": [
    "`expectComplete()` ignores the value",
    "Nothing subscribes until `verify()` is called, so no expectation is ever checked",
    "StepVerifier only fails on errors, not on wrong values",
    "The cancel runs on another thread, so its result arrives after the test ends"
   ],
   "answer": 1,
   "why": "`expectComplete()` only adds a step to the script. `verify()`, or a shortcut like `verifyComplete()`, is what subscribes and runs it. Add `.verify(Duration.ofSeconds(1))`, and the test checks the value and fails if it hangs."},
  {"q": "Screens in the shop share one connection to the oven thermometer. A screen that switches on late must show the current temperature at once, and the connection must close when nobody watches. Which operator fits?",
   "options": ["`readings.share()`", "`readings.cache()`", "`readings.replay(1).refCount()`", "`readings.publish().autoConnect(1)`"],
   "answer": 2,
   "why": "`replay(1)` gives a late subscriber the latest reading, and `refCount()` connects on the first subscriber and cancels the source when the last one leaves. `share()` gives late subscribers nothing until the next reading. `cache()` and `autoConnect` never disconnect, and `cache()` also keeps every reading forever."},
  {"q": "A team runs a web service written with Spring MVC, the classic style in which each request holds a thread, on a blocking database driver. It meets its speed targets. Someone proposes a rewrite with Spring WebFlux \"to make it faster\". What do Spring's own docs say?",
   "options": [
    "Rewrite it: reactive code is faster for every workload",
    "If an MVC application works fine there is no need to change; reactive code doesn't generally make applications faster",
    "Rewrite only the database calls with Reactor and keep the rest",
    "Switch to WebFlux, but keep the blocking driver on the event loop"
   ],
   "answer": 1,
   "why": "The Spring reference says a working MVC application has no need to change, that blocking database APIs point to MVC, and that reactive and non-blocking code generally doesn't make applications run faster. With virtual threads, the thread-count argument for this kind of service is mostly gone too. The last option is the worst of both: a blocking driver on an event loop stalls every request that loop serves."},
  {"q": "From \"Errors, retries and timeouts\": a retry uses `Retry.backoff(3, Duration.ofMillis(200))` with the default jitter. How should its virtual-time test check the slow path?",
   "options": [
    "`expectNoEvent` for exactly 1,400 ms, then expect the fallback",
    "Advance the clock well past the longest possible total wait, then check the result and the number of attempts",
    "Use real time with `Thread.sleep(2_000)` so the jitter is realistic",
    "It can't be tested while jitter is on"
   ],
   "answer": 1,
   "why": "With jitter, each wait moves by up to half its length, so exact times are not fixed. Advancing well past the maximum (the courier example moved the clock 10 seconds) and then checking the outcome and the count is stable. Exact-time checks need `jitter(0)`. Real sleeps make the test slow and still flaky.",
   "from": "rx-05"}
 ],
 "flashcards": [
  {"front": "What is `share()` the same as, and what does a late subscriber get?", "back": "`publish().refCount()`. A late subscriber gets only the items emitted after it subscribed."},
  {"front": "Late subscriber on `replay(1).refCount()`: what does it get?", "back": "The most recent item at once, then the live ones. The source is cancelled when the last subscriber leaves."},
  {"front": "Two threads call `tryEmitNext` on one sink at the same moment. What can happen?", "back": "One gets `EmitResult.FAIL_NON_SERIALIZED` and its item is not emitted. Check the result or use `emitNext(item, busyLooping(...))`."},
  {"front": "What happens to `Sinks.many().multicast().onBackpressureBuffer()` when its last subscriber leaves?", "back": "By default it shuts down: a later subscriber just receives `onComplete`. `directBestEffort()` keeps working."},
  {"front": "A `StepVerifier` chain without `verify()`: what runs?", "back": "Nothing. `verify()` (or `verifyComplete()` and the other shortcuts) is what subscribes and checks the steps."},
  {"front": "Why must the publisher be built inside the `withVirtualTime` supplier?", "back": "Operators like `delay`, `interval` and `timeout` pick their scheduler when the chain is built. Built earlier, they use the real clock and the test hangs."},
  {"front": "What does `checkpoint(\"price-row\")` add to an error?", "back": "A suppressed exception saying the error was observed at the checkpoint named `price-row`. Cheap; `checkpoint(name, true)` also captures the stack trace of where the chain was built."}
 ],
 "terms": [
  {"term": "Cold publisher", "plain": "A publisher that does its work again, from the start, for every subscriber."},
  {"term": "Hot publisher", "plain": "A publisher that produces whether or not anyone subscribes; subscribers see what is produced while they listen."},
  {"term": "ConnectableFlux", "plain": "What `publish()` and `replay()` return: a shared Flux that subscribes to its source when it is connected."},
  {"term": "refCount", "plain": "Connect on the first subscriber, disconnect when the last one leaves (optionally after a grace period)."},
  {"term": "Sink", "plain": "Reactor's thread-aware way to push values from ordinary code into a Flux or Mono."},
  {"term": "StepVerifier", "plain": "reactor-test's tool that subscribes to a publisher and checks its signals step by step."},
  {"term": "Virtual time", "plain": "A fake clock that replaces Reactor's schedulers in a test, so delays pass instantly."},
  {"term": "checkpoint", "plain": "An operator that labels a place in a chain, so errors passing through it say where they came from."}
 ],
 "explain_back": {
  "prompt": "A teammate is building the kitchen screens: the shop's tills ring an order bell, a dozen screens should show the orders live, and every screen also shows the current oven temperature. Explain which Reactor pieces you would use, what can silently go wrong with each, and how you would test it.",
  "answer": "For the orders I'd use a multicast sink, `directBestEffort()`, because each screen only needs the orders from the moment it connects, nothing should pile up while nobody watches, and the bell must keep working after every screen switches off (the buffered flavour shuts down when its last subscriber leaves). The till threads would ring it with `emitNext` and a `busyLooping` handler, because `tryEmitNext` refuses overlapping calls, and the refused order just disappears. For the temperature I'd wrap the thermometer feed in `replay(1).refCount(1, grace)`: one connection, new screens get the current reading at once, and the connection closes a few seconds after the last screen leaves. `share()` would leave new screens blank until the next reading, and `cache()` would never disconnect and would keep every reading. To test it I'd use `TestPublisher` for the thermometer, a multi-threaded test for the bell with a start latch, and `StepVerifier.withVirtualTime` for anything with time in it, always with `verify(Duration)` so that a bug fails fast instead of hanging."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Connecting by hand.** `publish()` and `replay()` return a `ConnectableFlux`. Besides `refCount` and `autoConnect`, you can call `connect()` yourself once every subscriber is in place, and dispose the returned `Disposable` to disconnect. That suits a startup sequence that wires several consumers before any data should flow.\n\n**Context instead of ThreadLocal.** Because a chain hops threads, a `ThreadLocal`, such as the per-request id that a logging library keeps, doesn't follow it. Reactor's `Context` does: write it at the bottom with `contextWrite(Context.of(\"requestId\", id))` and read it upstream with `Mono.deferContextual(ctx -> ...)`. It travels from the subscriber toward the source, so a `contextWrite` above the reader is invisible to it. With the Micrometer context-propagation library on the classpath, `Hooks.enableAutomaticContextPropagation()` (Reactor 3.5.3+) restores ThreadLocals around each operator; it isn't in the labs.\n\n**BlockHound in tests.** Calling `BlockHound.install()` at the start of a test run makes any blocking call on a non-blocking thread throw `BlockingOperationError`. That catches a blocking database call on a server's event-loop thread, from the Schedulers lesson, before a real user does. On JDK 13+ it needs `-XX:+AllowRedefinitionToAddDeleteMethods`.\n\n**Backpressure in tests.** `StepVerifier.create(flux, 0)` starts with no demand, and `thenRequest(n)` adds it step by step. That's how the lab of Backpressure in practice checked which reading a slow screen receives."
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
