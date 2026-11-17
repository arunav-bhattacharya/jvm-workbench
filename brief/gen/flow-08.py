import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/flows/src"
P = "kotlin/workbench/flows/l08"
J = "java/workbench/flows/l08"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :flows:demo -Pmain=workbench.flows.l08.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


turbine_kt = f"{lab}/test/{P}/TurbineTourTest.kt"
stepv_java = f"{lab}/test/{J}/StepVerifierTourTest.java"

# ---- the figure: where runCurrent, advanceTimeBy and advanceUntilIdle stop ----
def x(ms):
    return round(130 + ms * 1.6, 1)


ticks = ""
for ms in (0, 100, 200, 300):
    ticks += f'<line class="ln" x1="{x(ms)}" y1="146" x2="{x(ms)}" y2="154"/><text class="t-s t-m" x="{x(ms)}" y="168" text-anchor="middle">{ms}</text>'

FIG = (
    '<svg viewBox="0 0 700 262" role="img" aria-label="Timeline of the test scheduler in runTest. The test body has tasks due at 100 and 200 ms, '
    'and backgroundScope has a poll due at 300 ms. advanceTimeBy(100) moves the clock to 100 but runs only the tasks due before 100. '
    'runCurrent then runs the task due at 100. advanceUntilIdle runs on to 200 and stops there, because only background work is left, '
    'so the poll at 300 never runs.">'
    '<text class="t-s t-m" x="15" y="22">virtual time inside runTest (ms)</text>'
    '<text class="t-s t-m" x="15" y="72">test body</text>'
    '<text class="t-s t-m" x="15" y="122">background</text>'
    f'<rect class="box-a" x="{x(100) - 45}" y="52" width="90" height="28" rx="8"/>'
    f'<text class="t-s t-code" x="{x(100)}" y="71" text-anchor="middle">delay(100)</text>'
    f'<rect class="box-a" x="{x(200) - 45}" y="52" width="90" height="28" rx="8"/>'
    f'<text class="t-s t-code" x="{x(200)}" y="71" text-anchor="middle">delay(200)</text>'
    f'<rect class="box-dim" x="{x(300) - 50}" y="102" width="100" height="28" rx="8"/>'
    f'<text class="t-s t-code" x="{x(300)}" y="121" text-anchor="middle">poll at 300</text>'
    '<line class="ln" x1="130" y1="150" x2="670" y2="150" marker-end="url(#arr)"/>'
    + ticks +
    f'<line class="ln-d" x1="{x(100)}" y1="44" x2="{x(100)}" y2="210"/>'
    f'<rect class="box-b" x="{x(0)}" y="180" width="{x(100) - x(0)}" height="24" rx="8"/>'
    f'<text class="t-s t-code" x="{x(50)}" y="196" text-anchor="middle">advanceTimeBy(100)</text>'
    f'<rect class="box-b" x="{x(100)}" y="180" width="{x(200) - x(100)}" height="24" rx="8"/>'
    f'<text class="t-s t-code" x="{x(150)}" y="196" text-anchor="middle">advanceUntilIdle()</text>'
    f'<text class="t-s" x="{x(50)}" y="224" text-anchor="middle">clock at 100, task not run</text>'
    f'<text class="t-s t-ok" x="{x(100)}" y="246" text-anchor="middle">runCurrent() runs the task at 100</text>'
    f'<text class="t-s" x="{x(200)}" y="224" text-anchor="middle">stops at 200</text>'
    f'<text class="t-s t-bad" x="{x(300)}" y="224" text-anchor="middle">poll at 300 never runs</text>'
    '</svg>'
)

OPENING = """The old wireless oven probe from the coroutines track is still in the kitchen drawer. You push it into the roast, and it calls you. Its library has a **listener**: you register a function, and the probe calls it on its own thread with every new reading, until you unregister it. Next door, the neighbour's kitchen runs on Reactor, a line of stations where each one asks the one before it for a number of items at a time. And before a big dinner, the house holds a rehearsal on a fake clock.

A flow fits none of these. It waits to be collected, it hands values over by suspending, and its delays take real time. The easy trap is to wrap the probe in a few lines that work in a demo, and then lose readings, or leave the listener behind, in the first busy hour.

Hot flows in depth shared values inside one program. In this lesson, we'll bridge the probe with `callbackFlow`, survive the burst it sends on connect, cross into Reactor and back, and rehearse it all on virtual time. Before we start, make a guess, and keep it in mind."""

S1 = r"""Here is a first bridge from the probe's listener to a flow. The caller starts collecting, gives way once with `yield()` (a suspension point that lets other coroutines run), and then the probe fires a reading:

```kotlin
fun DemoProbe.events(): Flow<ProbeEvent> = callbackFlow {
    val registration = register(object : ProbeEventListener {
        override fun onEvent(event: ProbeEvent) { trySend(event) }   // on the probe's thread
        override fun onError(error: Throwable) { close(error) }
        override fun onClosed() { close() }
    })
    awaitClose { registration.unregister() }
}

launch { probe.events().collect { println("got $it") } }
yield()
probe.fire(ProbeEvent(0, 61))   // fired with listeners=0
```

```java
// Java equivalent: Flux.create runs its lambda inside subscribe(), so the listener is there at once
Flux<ProbeEvent> events = Flux.create(sink -> {
    ProbeRegistration registration = probe.register(new ProbeEventListener() {
        public void onEvent(ProbeEvent e) { sink.next(e); }
        public void onError(Throwable t) { sink.error(t); }
        public void onClosed() { sink.complete(); }
    });
    sink.onDispose(registration::unregister);
});
events.subscribe(e -> System.out.println("got " + e));
probe.fire(new ProbeEvent(0, 61));   // got ProbeEvent(seq=0, celsius=61)
```

**callbackFlow** is a flow builder for listener APIs. Its block registers a listener that drops each value into a channel, a queue between coroutines, and the collector takes the values out on the other side. The Kotlin reading is lost. `collect` on a `callbackFlow` starts a producer coroutine, and your block, with its `register` call, runs inside that coroutine only when it is first scheduled. `launch` and one `yield()` got the collector going, but not its producer. Reactor's `Flux.create` runs its lambda inside `subscribe()`, on the calling thread, so the Java version has no gap. In Kotlin, collecting does not mean registered. A test must wait for the registration, and real code must not count on it.

Picture the bridge as the hatch with a shelf from Context and threads, fitted to the probe. The probe's thread puts each reading on the shelf with `trySend`, which never waits. `send` would wait for room, so it is a suspend function, and calling it from a plain listener method doesn't compile: "suspension functions can only be called within coroutine body". `awaitClose { }` is you standing at the hatch until you're told to leave, and then taking the hatch down. It suspends until the channel closes and runs its block in a `finally`, so the listener goes away whatever ended the flow: `take(2)`, a cancelled collector, `close(error)` from `onError` (the collector's `collect` throws that error), or `close()` from `onClosed` (the flow completes normally).

Forget `awaitClose`, and the library sounds an alarm as soon as the block returns with the channel still open. It is quite insistent:

```text
java.lang.IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.
Otherwise, a callback/listener may leak in case of external cancellation.
See callbackFlow API documentation for the details.
```

Reactor has no such check. A `Flux.create` without `onDispose` still has its listener registered after `take(1)` has finished, and nothing tells you. For your own coroutines feeding one flow, such as two thermometers that you `launch` yourself, use `channelFlow` from lesson 3 of this track: the same machinery without the check, and it completes when the block and all its children are done. For a callback that fires only once, use `suspendCancellableCoroutine`.

**Collecting is not registering. End every callbackFlow with awaitClose.**

Check yourself: the collector is cancelled while it waits for a reading. Which line of the bridge runs, and on which ending of the flow would it not run? The listener is now in place and goes away cleanly. The probe's first act on connect is to send everything it stored."""

S2 = r"""The probe keeps its readings while nobody listens, and on connect it replays them in one burst, from its own thread, one callback after another. Fire 200 readings into a default `callbackFlow` while its collector waits in `receive()`, and 135 `trySend` calls fail. The other 65 got through: 64 onto the shelf (`Channel.BUFFERED`), and one handed straight to the receiver that was already waiting, before the shelf was touched. So a shelf of 64 takes 65 when someone is waiting at the hatch. Better to know that before a test counts it for you.

`trySend` returns a `ChannelResult` that says whether it worked. Ignore it, and the 135 failures are silent losses. After the channel is closed it fails too, with `isClosed=true`. The fix is a policy you choose on purpose. A `buffer(...)` or `conflate()` right after `callbackFlow { }` fuses into its one channel (the shelves snapping together from Buffering), so it changes that channel instead of adding a second one:

| After `callbackFlow { }` | `trySend` failures | The collector got |
|---|---|---|
| nothing (64, `SUSPEND`) | 135 | 65 accepted |
| `.buffer(Channel.UNLIMITED)` | 0 | all 200 |
| `.conflate()` | 0 | `[0, 199]`: the first went to the waiting receiver, the last stayed in the one spot |
| `.buffer(10, DROP_OLDEST)` | 0 | `[0, 190, 191, ..., 199]` |

```kotlin
fun FakeProbe.readings(): Flow<ProbeReading> = callbackFlow { /* register, trySend, awaitClose */ }
    .buffer(500)   // fused: the bridge's own channel now holds the 500 stored readings
```

```java
// Java equivalent: Flux.create buffers without limit by default (OverflowStrategy.BUFFER);
// onBackpressureBuffer(500) caps it and fails with an overflow error past 500
Flux<ProbeReading> readings = Flux.create(sink -> { /* register, sink.next, onDispose */ })
    .onBackpressureBuffer(500);
```

`trySendBlocking(e)` looks like the safe version. It is `trySend` with a fallback of `runBlocking { send(e) }`, so when the shelf is full it blocks the probe's own thread until there is room. With the probe's thread pushing 200 readings and a collector that takes 2 ms each, `trySend` let the thread finish in about 1 ms and lost 135, while `trySendBlocking` lost none and held the probe's thread for about 340 ms. (That run uses the real clock, so your numbers will differ.) Use it only when the library runs your callback on a worker thread of its own, and making that thread wait is how you slow it down. Pick `UNLIMITED` only when the producer is known to stop. For a feed where only the latest value matters, `conflate()` drops readings in a way you can explain.

**A failed trySend is a lost reading. Size the shelf for the burst, or choose what to drop.**

Check yourself: what does the collector get from the same burst after `.buffer(10, DROP_LATEST)`? The probe now feeds a flow without losing anything. The neighbour wants the readings too, and her kitchen speaks Reactor."""

S3 = r"""Reactor follows **Reactive Streams**, a small standard set of Java interfaces for streams, and it makes the subscriber say how much it can take, with `request(n)`. That number is called **demand**. A Flow has no such call: it suspends. The bridges in the kotlinx-coroutines-reactive and kotlinx-coroutines-reactor modules translate one into the other.

`Publisher.asFlow()` works like a diner with an order pad, sitting at the end of the neighbour's line of stations. It orders 64, eats them, and orders 64 more after every 64 it has passed on. (A `Flux` is a `Publisher`, so `flux.asFlow()` is this same function.) The items wait in a channel of that size, and `buffer` sets the size of the order:

| Flow side | Requests sent to a 300-item `Flux` |
|---|---|
| `asFlow()` | 64 after 0, 64, 128, 192 and 256 |
| `asFlow().buffer(10)` | 10 every 10 |
| `asFlow().buffer(0)` | 1 every 1 |
| `asFlow().conflate()` or `.buffer(UNLIMITED)` | `Long.MAX_VALUE`, once |
| `asFlow().take(3)` | 64, then cancel: the 61 extra already in the channel are thrown away |

That is a refill in batches. Reactor's own operators top up earlier: `publishOn` asked a Flow-backed Flux for 256 and then 192 at a time, and `limitRate(10)` for 10 and then 8.

`Flow.asFlux()` and `asPublisher()` go the other way. Nothing runs until the first `request(n)`. Then each `emit` calls `onNext` right there, inside `emit`, and counts the demand down. When it reaches 0, the flow suspends inside that `emit`, and a later `request` resumes it. After `request(2)` the subscriber had `[1, 2]`, and `emit` had returned only for 1: the flow was parked inside `emit(2)`. Cancelling the subscription cancels the flow's coroutine, so a `callbackFlow` underneath runs its `awaitClose`.

Two details bite in real programs. The bridge runs the flow on `Dispatchers.Unconfined` unless you pass a dispatcher, so the flow and every Reactor operator after it run on whichever thread resumed it: the subscriber's thread at first, `kotlinx.coroutines.DefaultExecutor` after a `delay`, and the probe's own thread under a probe bridge. Pass `asFlux(dispatcher)`, or add `publishOn` before anything slow downstream. And Reactor's `Context`, a small map of values that travels with a subscription, crosses in both directions. Through `asFlux()`, a table number written with `contextWrite` was visible inside the flow as a `ReactorContext` element. The other way, a `ReactorContext` in the coroutine reaches a publisher collected with `asFlow()` only when kotlinx-coroutines-reactor is on the classpath, because that module supplies the piece that injects it, found with `ServiceLoader`.

Java can't call `Flow.collect`, which it sees as `Object collect(FlowCollector, Continuation)`. Give Java a face built in Kotlin:

```kotlin
class ProbeApi(private val probe: FakeProbe) {
    fun readings(): Flow<ProbeReading> = probe.readings()          // for Kotlin callers
    fun readingsFlux(): Flux<ProbeReading> = readings().asFlux()   // for Java and Reactor callers
}
```

```java
// Java caller: only Reactor types, no Flow and no Continuation
List<ProbeReading> firstTwo = new ProbeApi(probe).readingsFlux().take(2).collectList().block();
```

For a single result, a `CompletableFuture` built with `scope.future { }` is the better face, as lesson 11 of the coroutines track showed.

**Give Java a Flux or a future, never a Flow.**

Check yourself: how many requests does `asFlow().buffer(10)` send to a 300-item `Flux`, and why one more than 30? Every bridge in this lesson has a timing story, and testing timing on a real clock is slow and flaky. So the house rehearses."""

S4 = r"""`runTest` is the rehearsal dinner from lesson 10 of the coroutines track. It replaces the clock with a scheduler that jumps from one due task to the next, so a `delay` takes no real time: that fake clock is **virtual time**. Three calls move it along, and each one stops in a different place:

- `runCurrent()` runs everything that is due now.
- `advanceTimeBy(n)` runs ahead up to, but not including, `now + n`. With tasks due at 100 and 200, `advanceTimeBy(100)` leaves the clock at 100 with `fired=[]`. Only `runCurrent()` then runs the task at 100.
- `advanceUntilIdle()` runs ahead until only background work is left. With nothing but a poller in `backgroundScope`, it leaves `t=0 polls=0`, while `advanceTimeBy(5000)` plus `runCurrent()` gives `t=5000 polls=5`.

`backgroundScope` is a scope inside `runTest` for coroutines that never end on their own; they are cancelled when the test body ends. A test that collects a hot flow there should drive the clock with `advanceTimeBy(...)` and `runCurrent()`, as this track's labs do. Reactor's virtual clock puts the edge elsewhere:

```kotlin
@Test
fun `the task due at 100 needs runCurrent`() = runTest {
    val fired = mutableListOf<Long>()
    launch { delay(100); fired += currentTime }
    advanceTimeBy(100)
    assertThat(fired).isEmpty()               // runs only what is due BEFORE now + 100
    runCurrent()
    assertThat(fired).containsExactly(100L)   // runs what is due now
}
```

```java
// Java equivalent: Reactor's VirtualTimeScheduler includes the end point
@Test
void taskDueAt100RunsWithAdvanceTimeBy() {
    VirtualTimeScheduler clock = VirtualTimeScheduler.create();
    List<Long> fired = new ArrayList<>();
    clock.schedule(() -> fired.add(100L), 100, TimeUnit.MILLISECONDS);
    clock.advanceTimeBy(Duration.ofMillis(100));
    assertThat(fired).containsExactly(100L);  // already ran, no extra step
}
```

The test dispatcher decides what a StateFlow collector sees. A dish tracker's `cookAndServe()` sets COOKING and then SERVED, with no suspension between them. A collector on the default `StandardTestDispatcher` runs only when the test lets the clock move, so it saw `[ORDERED, SERVED]`. One launched with `UnconfinedTestDispatcher(testScheduler)`, which runs a coroutine at once, inside the call that wakes it, saw all three. That dispatcher is experimental. A real collector on `Dispatchers.Default` can see either. So the Unconfined test shows the most a collector can see, and the Standard one shows the menu board skipping a value. Assert on the final state and on the changes that matter. If every change matters, the type shouldn't be a StateFlow.

Two failures come with exact messages. `async { status.take(3).toList() }` waits for a third value that the board skipped, and with `runTest(timeout = 500.milliseconds)` it ends in `UncompletedCoroutinesError: After waiting for 500ms, the test body did not run to completion`. (The default timeout is 60 s, and the 20 s JUnit timeout in these labs fires first.) A hot flow collected in the test scope itself, or `stateIn(this, WhileSubscribed(), 0)`, fails with `there were active child jobs`, followed by the advice to use `TestScope.backgroundScope`.

**advanceTimeBy(n) stops just before n. Follow it with runCurrent().**

Check yourself: change `advanceTimeBy(100)` to `advanceTimeBy(101)` in the first part of the Try it. What does its first line print? Driving the clock by hand is precise and a little tedious. A library can read the flow for you, and its one blind spot is worth knowing."""

S5 = r"""**Turbine** 1.2.1 (`app.cash.turbine`, a test dependency of this lab module) is a test library that turns a flow into a list of events you read one by one:

```kotlin
probe.readings().test {          // collects before the block runs: the listener is registered
    probe.fire(first)
    assertThat(awaitItem()).isEqualTo(first)
    probe.fail(IOException("probe connection lost"))
    assertThat(awaitError()).hasMessage("probe connection lost")
}
```

```java
// Java equivalent: StepVerifier subscribes, then runs each step in order
StepVerifier.create(api.readingsFlux())
    .then(() -> probe.fire(first))
    .expectNext(first)
    .then(() -> probe.fail(new IOException("probe connection lost")))
    .expectErrorMessage("probe connection lost")
    .verify(Duration.ofSeconds(5));
```

Picture the rehearsal's note-taker. `test { }` runs the flow up to its first suspension before your block starts, so a SharedFlow is subscribed and a `callbackFlow` listener is registered by then, which removes the race from the first section. Every event goes into her notebook, an unlimited channel, in order. You read it with `awaitItem()`, `awaitComplete()` and `awaitError()`, which hands you the error as an event instead of throwing it. An event you never read fails the test with `Unconsumed events found`, unless you end with `cancelAndIgnoreRemainingEvents()`. If no new event arrives within 3 s of real time, the test fails with `No value produced in 3s`. The flow's own `delay` calls stay virtual inside `runTest`; only Turbine's wait is real. To follow two flows at once, call `testIn(backgroundScope)` inside `turbineScope { }`. Outside it, `testIn` compiles and then fails at run time with `Turbine can only collect flows within a TurbineContext`.

The note-taker hears everything, and that is her blind spot. Turbine collects on `UnconfinedTestDispatcher`, so it takes each value the instant it is sent. It saw COOKING, which the Standard collector of the last section never got. It also took all 500 readings of a burst through a 64-spot `callbackFlow`, where a Standard collector got 65. She never misses a word, which makes her a poor witness to what a slower listener would miss.

So use Turbine to check what a flow emits and in what order. Don't use it to test skipped values, buffer sizes or a slow collector. For those, collect with a Standard collector in `backgroundScope` and drive the clock yourself, as the lab's burst test does. And on a SharedFlow with no replay, a value emitted before `test { }` starts is gone, so the test fails with `No value produced`.

**Turbine shows what a flow says, not what a slow listener hears. Test buffers with a Standard collector.**

Check yourself: which test in the lab would still pass with a 64-spot buffer if you rewrote it with Turbine, and why? Every bridge in this lesson sits on top of something that waits: a probe's thread, a Reactor line, a clock. Underneath them all is the place where waiting really happens."""

CLOSING = """We started with an old probe that calls you, a neighbour who speaks Reactor, and a rehearsal on a fake clock. `callbackFlow` fits a hatch to the probe: `trySend` fills a shelf sized for the burst, and `awaitClose` takes the listener down. `asFlow` and `asFlux` turn `request(n)` into suspension and back, and `runTest` and Turbine rehearse it all.

Now search your own code for `callbackFlow`, and check two lines in each: the `awaitClose`, and what happens to a failed `trySend`.

That ends the Flow track. Next, we'll go underneath, to the sockets where all this waiting happens. Why does a server with one thread per client run out of threads long before it runs out of work?"""

L = {
 "id": "flow-08",
 "title": "Bridges and tests: callbackFlow, Reactor and runTest",
 "minutes": 40,
 "goal": "By the end you can wrap a listener API in callbackFlow without leaking the listener or losing values, predict how Reactor demand and Flow suspension map onto each other, give Java callers a Flux, and test flows on virtual time knowing what runCurrent, advanceTimeBy, advanceUntilIdle and Turbine show and hide.",
 "opening": OPENING,
 "warmup": {
  "q": "A test runs `backgroundScope.launch { probe.readings().collect { got += it } }`, where `readings()` is a correct `callbackFlow` that registers a listener, and on the very next line calls `probe.fire(reading)`. Then it calls `runCurrent()`. What is in `got`?",
  "options": ["`[reading]`: `launch` started the collection", "Nothing: the listener wasn't registered when the reading fired", "`[reading]` twice, once per dispatch", "It throws `IllegalStateException`"],
  "answer": 1,
  "why": "On the default `StandardTestDispatcher`, `launch` only queues the collector. The `callbackFlow` block that calls `register` runs in a producer coroutine when the scheduler next runs, which is at `runCurrent()`, after the fire. The reading found no listener and went nowhere. Real code has the same gap."
 },
 "sections": [
  {
   "h": "A callbackFlow is a hatch between the probe and your flow",
   "body": S1,
   "try": {
    "title": "Bridge the probe five ways",
    "minutes": 5,
    "steps": [
     "Read `ProbeBridge.kt`. For parts 0 to 5, predict each `[probe]` line and what the collector gets.",
     "Run it, then run the Java twin, which bridges the same probe with `Flux.create`.",
     "In part 0, replace the first `yield()` with `probe0.awaitRegistered()` and run again. Predict first."
    ],
    "code": tryit("ProbeBridge.kt", "ProbeBridgeJava.java"),
    "expect": "Part 0 prints `fired with listeners=0`, and `registered` only after it, so the collector gets nothing. Part 1 throws the `IllegalStateException` above, right after `registered`. Parts 2 to 4 each print `unregistered`: after `take(2)` with the first two readings, before the collector catches `IOException: probe connection lost`, and when the flow completes with the last reading. Part 5 shows `trySend` on a closed channel: `isSuccess=false isClosed=true`. With `awaitRegistered()`, part 0 prints `registered`, then `fired with listeners=1` and `got ProbeEvent(seq=0, celsius=61)`. The Java twin registers inside `subscribe()`, so its part 0 gets the reading at once, and its part 1 still has `listeners=1` after `take(1)`, with no error at all."
   },
   "refs": [
    {"title": "callbackFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html", "kind": "docs"},
    {"title": "awaitClose (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/await-close.html", "kind": "docs"}
   ]
  },
  {
   "h": "A burst of 200 on connect: 64 spots and one waiting hand",
   "body": S2,
   "try": {
    "title": "Count what a burst leaves behind",
    "minutes": 4,
    "steps": [
     "Read `ProbeBurst.kt`. For each of the four buffers in part 1, predict the `trySend` failures and what the collector gets.",
     "Run it. Part 2 runs on real threads, so its numbers change from run to run.",
     "Run the Java twin. Which Reactor overflow strategy behaves like `conflate()`, and what does Reactor do by default?"
    ],
    "code": tryit("ProbeBurst.kt", "ProbeBurstJava.java"),
    "expect": "Part 1 matches the table: 135 failures with 64 collected before `take(64)` cancels, then 0 failures and 200, then `[0, 199]`, then `[0, 190, ..., 199]`. In part 2, `trySend` lets the probe's thread finish almost at once with about 135 failures, and the collector receives about 65. `trySendBlocking` holds the probe's thread for about 300 ms or more and loses nothing. In the Java twin, `BUFFER`, the default, keeps all 200 because it has no limit; `LATEST` gives `[0, 199]`, the same as `conflate()`; `DROP` keeps only `[0]`; and `ERROR` delivers reading 0 and then fails with `OverflowException`."
   },
   "refs": [
    {"title": "trySendBlocking (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/try-send-blocking.html", "kind": "docs"}
   ]
  },
  {
   "h": "Across the Reactor bridge, demand becomes suspension",
   "body": S3,
   "try": {
    "title": "Watch request(n) cross the bridge",
    "minutes": 5,
    "steps": [
     "Read `ReactorDemand.kt`. Predict the request lines in part 1 and the two lines of part 2.",
     "Run it. Then run the Java twin, which consumes the same Kotlin flows through `PlateFaces` and sees only Reactor types.",
     "In part 3, change `asFlux()` to `asFlux(Dispatchers.IO)` (import `kotlinx.coroutines.Dispatchers`) and predict the thread names."
    ],
    "code": tryit("ReactorDemand.kt", "ReactorDemandJava.java"),
    "expect": "Part 1 matches the table, and `buffer(10)` sends 31 requests, the last one after the Flux has already finished. Part 2: after `request(2)` the subscriber has `[1, 2]` while `emit` has returned only for `[1]`; after `request(3)` it is `[1, 2, 3, 4, 5]` and `[1, 2, 3, 4]`. Part 3: `main` before the delay and `kotlinx.coroutines.DefaultExecutor` after it, for the flow and for `onNext` alike. With `Dispatchers.IO` both lines name a `DefaultDispatcher-worker` thread. Part 4: `table-7` with `contextWrite` and `no ReactorContext` without it. The Java twin shows Reactor's own demand on a Flow-backed Flux: `blockLast()` asks for `MAX`, `limitRate(10)` for 10 and then 8 at a time, `publishOn` and `flatMap` for 256 and then 192. It prints the same two lines for `request(2)` and `request(3)`."
   },
   "refs": [
    {"title": "Publisher.asFlow (kotlinx-coroutines-reactive API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactive/kotlinx.coroutines.reactive/as-flow.html", "kind": "docs"},
    {"title": "Flow.asFlux (kotlinx-coroutines-reactor API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/kotlinx.coroutines.reactor/as-flux.html", "kind": "docs"}
   ]
  },
  {
   "h": "The test clock has edges: where runCurrent, advanceTimeBy and advanceUntilIdle stop",
   "body": S4,
   "figure": {"svg": FIG, "caption": "advanceTimeBy(n) runs what is due before now + n, runCurrent() runs what is due now, and advanceUntilIdle() stops once only backgroundScope work is left."},
   "try": {
    "title": "Find the edges of the test clock",
    "minutes": 4,
    "steps": [
     "Read `TestClock.kt`. Predict every line before you run it, the two error messages included.",
     "Run it. Parts 4 and 5 each wait 500 ms of real time for the `runTest` timeout.",
     "In part 1, change `advanceTimeBy(100)` to `advanceTimeBy(101)`. What does the first line print now?"
    ],
    "code": {"lang": "kotlin", "title": "TestClock.kt", "src": read(demo("TestClock.kt")), "run": run("TestClockKt"), "file": demo("TestClock.kt"), "solo": True},
    "expect": "Part 1: `t=100 fired=[]`, then `fired=[100]` after `runCurrent()`, then `t=200 fired=[100, 200]`. Part 2: `t=0 polls=0`, then `t=5000 polls=5`. Part 3: `[ORDERED, SERVED]` for the Standard collector and `[ORDERED, COOKING, SERVED]` for the Unconfined one. Part 4: `UncompletedCoroutinesError: After waiting for 500ms, the test body did not run to completion`. Part 5 prints `saw 3, test body done` and then fails with `there were active child jobs`, because the `WhileSubscribed` sharing coroutine never ends. With `advanceTimeBy(101)` the clock stops at 101 and the task at 100 has already run, so the first line reads `t=101 fired=[100]`. (Reactor's virtual clock has no Java twin here: it lives in reactor-test, which only the tests can use.)"
   },
   "refs": [
    {"title": "TestCoroutineScheduler.advanceTimeBy (kotlinx-coroutines-test API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-coroutine-scheduler/advance-time-by.html", "kind": "docs"},
    {"title": "UnconfinedTestDispatcher (kotlinx-coroutines-test API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-unconfined-test-dispatcher.html", "kind": "docs"}
   ]
  },
  {
   "h": "Turbine writes down every value, and that is its blind spot",
   "body": S5,
   "try": {
    "title": "A tour of Turbine",
    "minutes": 5,
    "steps": [
     "Read `TurbineTourTest.kt`. For each of the eight tests, predict the commented line before you run anything.",
     "Run the class with the command below. All eight pass; test 6 waits half a second of real time.",
     "In test 4, delete the line that awaits `SERVED` and run again. Predict the failure message first."
    ],
    "code": {"lang": "kotlin", "title": "TurbineTourTest.kt", "src": read(turbine_kt),
             "run": "./gradlew :flows:test --tests 'workbench.flows.l08.TurbineTourTest'", "file": turbine_kt,
             "alt": {"lang": "java", "title": "StepVerifierTourTest.java", "src": read(stepv_java),
                     "run": "./gradlew :flows:test --tests 'workbench.flows.l08.StepVerifierTourTest'", "file": stepv_java}},
    "expect": "All eight pass. Turbine reads items and completion in order, reports an unread event as `Unconsumed events found`, and hands the error over as an event. It sees all three StateFlow values where the Standard collector sees `[ORDERED, SERVED]`, and takes all 500 burst readings where the Standard collector gets 65. It misses the value emitted before `test { }`, with `No value produced in 500ms`, and a virtual 10 s delay passes inside a 200 ms timeout. With the `SERVED` line gone, test 4 fails with `Unconsumed events found`, listing `Item(SERVED)`. The Java twin passes six StepVerifier tests: an unexpected signal fails with `actual: onNext(two)`, a Kotlin StateFlow through `asFlux()` delivers all three values as Turbine does, a hot item emitted before anyone subscribed is lost and `verify` times out, and `thenAwait` of 10 s runs the task due at exactly +10 s."
   },
   "refs": [
    {"title": "Turbine README", "url": "https://raw.githubusercontent.com/cashapp/turbine/trunk/README.md", "kind": "read"},
    {"title": "Testing Kotlin flows (Android developers): the StateFlow conflation warning", "url": "https://developer.android.com/kotlin/flow/test", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A probe bridge: Flux.create next to callbackFlow",
  "java": {"title": "ProbeReadings.java (Reactor)", "src": "static Flux<ProbeReading> readings(FakeProbe probe) {\n    return Flux.<ProbeReading>create(sink -> {\n        Registration registration = probe.register(new ProbeListener() {\n            @Override public void onReading(ProbeReading r) { sink.next(r); }  // runs the subscriber inline\n            @Override public void onError(Throwable t) { sink.error(t); }\n            @Override public void onClosed() { sink.complete(); }\n        });\n        sink.onDispose(registration::unregister);   // optional: nothing complains if it is missing\n    })\n    .onBackpressureBuffer(500);                    // the default buffer has no limit\n}"},
  "kotlin": {"title": "ProbeReadings.kt (callbackFlow)", "src": "fun FakeProbe.readings(): Flow<ProbeReading> = callbackFlow {\n    val registration = register(object : ProbeListener {\n        override fun onReading(reading: ProbeReading) { trySend(reading) }   // never blocks the probe's thread\n        override fun onError(error: Throwable) { close(error) }\n        override fun onClosed() { close() }\n    })\n    awaitClose { registration.unregister() }   // required: collecting throws without it\n}.buffer(500)                                  // fused into the bridge's channel; the default is 64"},
  "note": "The shapes match line for line, and four things differ. Registration time: `Flux.create` registers inside `subscribe()`, while `callbackFlow` registers when its producer coroutine first runs, so a reading fired right after `collect` starts can be lost. Cleanup: `callbackFlow` throws when its block returns without `awaitClose`, and Reactor lets a missing `onDispose` leak the listener with no message. Buffering: Kotlin's channel holds 64 (65 with a waiting receiver) and makes you look at `trySend`'s result; Reactor buffers without limit unless you add a policy. Threads: `sink.next` calls the subscriber's `onNext` on the probe's thread, while the Kotlin collector runs on its own dispatcher and the probe's thread only drops the reading into the channel. That holds until you turn the flow into a Flux with plain `asFlux()`, whose `Unconfined` default puts the subscriber back on the probe's thread."
 },
 "worked": {
  "title": "Hand the probe to Java, and test it from both sides",
  "steps": [
   {"say": "Start from the Kotlin bridge, the lab's solution. It registers per collector, never blocks the probe's thread, closes the channel on `onError` and `onClosed`, and has room for the 500 stored readings.",
    "code": "fun FakeProbe.readings(): Flow<ProbeReading> = callbackFlow {\n    val registration = register(object : ProbeListener {\n        override fun onReading(reading: ProbeReading) { trySend(reading) }   // 1. hand over, never block\n        override fun onError(error: Throwable) { close(error) }              // 2. fail the flow\n        override fun onClosed() { close() }                                  // 3. complete it\n    })\n    awaitClose { registration.unregister() }                                 // 4. clean up on any ending\n}.buffer(500)",
    "lang": "kotlin",
    "alt_code": "// Java equivalent of the same four steps\nstatic Flux<ProbeReading> readings(FakeProbe probe) {\n    return Flux.<ProbeReading>create(sink -> {\n        Registration registration = probe.register(new ProbeListener() {\n            @Override public void onReading(ProbeReading r) { sink.next(r); }  // 1.\n            @Override public void onError(Throwable t) { sink.error(t); }      // 2.\n            @Override public void onClosed() { sink.complete(); }               // 3.\n        });\n        sink.onDispose(registration::unregister);                               // 4.\n    }).onBackpressureBuffer(500);\n}",
    "alt_lang": "java"},
   {"say": "Give Java a face. `asFlux()` starts the flow at the first `request(n)`, so registration happens then and not at `subscribe()`. A cancelled subscription cancels the flow, so `awaitClose` unregisters.",
    "code": "class ProbeApi(private val probe: FakeProbe) {\n    fun readings(): Flow<ProbeReading> = probe.readings()\n    fun readingsFlux(): Flux<ProbeReading> = probe.readings().asFlux()   // Unconfined: pass a dispatcher if operators after it are slow\n}",
    "lang": "kotlin",
    "alt_code": "// what the Java caller writes: Reactor types only\nList<ProbeReading> firstTwo = new ProbeApi(probe).readingsFlux().take(2).collectList().block();",
    "alt_lang": "java"},
   {"say": "Test the content with Turbine and the buffer with a Standard collector. Turbine registers before its block runs and reads events in order. The burst test needs a collector that can't run during the burst, so it uses the default dispatcher and `runCurrent()`.",
    "code": "@Test\nfun `a probe error fails the flow`() = runTest {\n    probe.readings().test {\n        probe.fire(first)\n        assertThat(awaitItem()).isEqualTo(first)\n        probe.fail(IOException(\"probe connection lost\"))\n        assertThat(awaitError()).hasMessage(\"probe connection lost\")\n    }\n}\n\n@Test\nfun `a 500-reading burst arrives in full`() = runTest {\n    val got = mutableListOf<ProbeReading>()\n    backgroundScope.launch { probe.readings().collect { got += it } }\n    runCurrent()       // registered and waiting\n    probe.burst(500)   // 500 synchronous callbacks\n    runCurrent()\n    assertThat(got).hasSize(500)\n}",
    "lang": "kotlin",
    "alt_code": "// the Java side, with StepVerifier: no demand at first, so nothing is registered yet\nStepVerifier.create(api.readingsFlux(), 0)\n    .then(() -> assertThat(probe.getListenerCount()).isZero())\n    .thenRequest(1)\n    .then(() -> probe.fire(first))\n    .expectNext(first)\n    .thenCancel()\n    .verify(Duration.ofSeconds(5));\nassertThat(probe.getListenerCount()).isZero();   // cancel reached awaitClose",
    "alt_lang": "java"},
   {"say": "Self-check: why does the burst test avoid Turbine, which would make it shorter? (Turbine collects on `UnconfinedTestDispatcher`, so every `trySend` wakes it at once and the reading leaves the channel immediately. The buffer never fills, and a 64-spot version would pass with all 500 readings. In the tour test, a Standard collector got 65.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Bridge the probe's listener, hand it to Java, test it both ways",
  "minutes": 15,
  "files": [
   f"{lab}/main/{P}/ProbeReadings.kt",
   f"{lab}/main/{P}/ProbeApi.kt",
   f"{lab}/main/{P}/Probe.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l08.*'",
  "steps": [
   "Run the tests. The five `ProbeReadingsTest` cases and the three in `ProbeFluxTest` (a Java test) fail. `TurbineTourTest` and `StepVerifierTourTest` already pass: they are this lesson's Try it. Read one failure: it is the `awaitClose` message from the first section.",
   "In `ProbeReadings.kt`, keep the `Registration` that `register` returns, close the channel from `onError` and `onClosed`, and end the block with `awaitClose`. Run `ProbeReadingsTest`. One test still fails, with a number you have seen in this lesson.",
   "Size the bridge's channel for the 500 stored readings that the KDoc promises, without blocking the probe's thread.",
   "In `ProbeApi.kt`, write `readingsFlux()`. Run `ProbeFluxTest`, which sees only Reactor types.",
   "Run all the l08 tests. Then read `ProbeReadingsTest` and say, for each test, why it uses Turbine, an Unconfined collector or a Standard one."
  ],
  "hints": [
   "`close(error)` and `close()` belong to the `ProducerScope` the block runs in, so you can call them from inside the listener object.",
   "`Expected size: 500 but was: 65` is the default 64 spots plus the one reading handed to the waiting collector. A `buffer(...)` right after `callbackFlow { }` is fused into its channel. `Channel.UNLIMITED` passes too; a number states how much memory you allow.",
   "Don't reach for `trySendBlocking`. In the burst test the probe's thread is the test's only thread, the one the collector needs in order to run.",
   "`asFlux()` is in `kotlinx.coroutines.reactor`. It starts the flow at the first `request(n)` and cancels it when the subscription is cancelled, which is what the Java tests check."
  ],
  "done_when": "All tests in `workbench.flows.l08` pass: `ProbeReadingsTest`, `ProbeFluxTest` and the two tours."
 },
 "drill": {
  "title": "A listener bridge, from memory",
  "minutes": 5,
  "prompt": "Close this page. A made-up kitchen scale library has `fun subscribe(onWeight: (Weight) -> Unit, onFailure: (Throwable) -> Unit): Cancellable`. Write `fun KitchenScale.weights(): Flow<Weight>` that never blocks the scale's thread, fails the flow on `onFailure`, holds a burst of 1,000 weights, and cancels the subscription whatever ends the collection. Then say in a comment what happens if you leave out the cleanup line.",
  "answer": {"lang": "kotlin", "src": "fun KitchenScale.weights(): Flow<Weight> = callbackFlow {\n    val subscription = subscribe(\n        onWeight = { weight -> trySend(weight) },      // never blocks the scale's thread\n        onFailure = { error -> close(error) },         // collect throws this error\n    )\n    awaitClose { subscription.cancel() }               // on take(n), cancellation, close and error\n}.buffer(1_000)                                        // fused into the callbackFlow's channel\n\n// Without awaitClose the block returns with the channel open, and collecting throws\n// IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used\n// in the end of callbackFlow block.",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent, for a library whose Java API is subscribe(Consumer<Weight>, Consumer<Throwable>)\nFlux<Weight> weights(KitchenScale scale) {\n    return Flux.<Weight>create(sink -> {\n        Cancellable subscription = scale.subscribe(sink::next, sink::error);\n        sink.onDispose(subscription::cancel);   // leave it out and the subscription leaks, silently\n    }).onBackpressureBuffer(1_000);              // caps the default unlimited buffer\n}"}}
 },
 "recap": [
  "`callbackFlow` registers when its producer coroutine first runs, after `collect` starts, so a value fired in between is lost. Tests wait for the registration; Turbine's `test { }` does it for you. Reactor's `Flux.create` registers inside `subscribe()`.",
  "`awaitClose { unregister() }` runs on `take(n)`, cancellation, `close(error)` and `close()`. Without it, collecting throws the exact `IllegalStateException` shown in the lesson. Use `channelFlow` for your own coroutines and `suspendCancellableCoroutine` for a callback that fires once.",
  "The bridge holds 64 by default plus one handed to a waiting receiver, so 65 of a 200-reading burst got in. Check `trySend`'s result, and choose a fused `buffer(n)`, `conflate()` or `UNLIMITED` (for a producer known to stop) on purpose. `trySendBlocking` blocks the library's thread.",
  "`Publisher.asFlow()` requests 64, then 64 more after each 64; `buffer(n)` makes it `request(n)`. `asFlux()` starts at the first request, calls `onNext` inside `emit` and suspends there when demand runs out, on `Unconfined` unless you pass a dispatcher. Give Java a `Flux` or a `CompletableFuture`, never a `Flow`.",
  "`advanceTimeBy(n)` runs what is due before `now + n`, `runCurrent()` what is due now, and `advanceUntilIdle()` stops when only `backgroundScope` work is left. Turbine reads a flow in order with a 3 s real-time timeout, but it collects on `UnconfinedTestDispatcher`, so test skipped values and buffer sizes with a Standard collector.",
  "The limit: these bridges and tests live inside one program, on top of threads and sockets that do the real waiting. How that waiting scales is the next track's subject."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A `callbackFlow` with the default buffer is followed by `.conflate()`. Its collector is suspended, waiting for the first value, when the probe fires readings 0 to 199 one after another on its own thread. What does the collector get?",
   "options": ["`[0, 199]`: the first went straight to the waiting collector, the last stayed in the one spot", "`[199]`: conflate keeps only the latest", "`[0]`: the rest were dropped", "All 200, delivered more slowly"],
   "answer": 0,
   "why": "`conflate()` is fused into the callbackFlow's channel and turns it into one spot that a new value overwrites. Reading 0 was handed directly to the receiver that was already waiting, so it never touched the spot; the spot then ended up holding 199. Lesson 4's `conflate()` works the same way."},
  {"q": "A test runs `backgroundScope.launch { probe.readings().collect { got += it } }`, then `probe.fire(r)` on the next line, then `runCurrent()`. `readings()` is a correct `callbackFlow` with `awaitClose`. What are `got` and the listener count afterwards?",
   "options": ["`[r]` and 1", "`[]` and 1: the listener registered after the fire", "`[]` and 0", "`[r, r]` and 1"],
   "answer": 1,
   "why": "The default `StandardTestDispatcher` only queues the collector. Its producer coroutine, which calls `register`, runs at `runCurrent()`, after the fire, so the reading found no listener; from then on one listener is registered. Call `runCurrent()` before firing, or use Turbine's `test { }`."},
  {"q": "Reactor code subscribes to `plates.asFlux()`, where `plates = flow { for (i in 1..10) { emit(i); log += i } }`, with a subscriber that calls `request(2)` and nothing more. What has the subscriber received, and what is in `log`?",
   "options": ["`[1, 2]` and `[1, 2]`", "`[1..10]` in both: `asFlux` runs 64 ahead", "Nothing yet: the flow waits for `request(64)`", "`[1, 2]` and `[1]`: the flow is suspended inside `emit(2)`"],
   "answer": 3,
   "why": "`asFlux()` calls `onNext` inside `emit` and then counts the demand down. After the second `onNext` the demand is 0, so the flow suspends inside `emit(2)` before `log += 2` runs. A later `request(n)` resumes it. The 64 is the other direction: `Publisher.asFlow()` requests 64 at a time."},
  {"q": "`cookAndServe()` sets a StateFlow to COOKING and then SERVED with no suspension between. Which test setup can show that a collector misses COOKING?",
   "options": ["Turbine's `status.test { }`", "`backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { status.toList(seen) }`", "`backgroundScope.launch { status.toList(seen) }` on the default dispatcher, with `runCurrent()` before and after", "`async { status.take(3).toList() }`"],
   "answer": 2,
   "why": "Only a Standard collector waits for its turn, so it wakes to SERVED and records `[ORDERED, SERVED]`. Turbine and the Unconfined collector run inside each set and see all three. `take(3)` waits for a third value that never comes and fails with `UncompletedCoroutinesError`."},
  {"q": "From lesson 7 of this track: people glance at `board.value`, where `board = readings.stateIn(houseScope, SharingStarted.WhileSubscribed(5_000), null)`, and nobody ever collects it. What do they read?",
   "options": ["The latest reading", "`null` for ever: reading `.value` is not a subscription, so the feed never starts", "The first reading, and never an update", "An `IllegalStateException`, because nobody subscribed"],
   "answer": 1,
   "why": "`WhileSubscribed` starts the upstream from `subscriptionCount`, and `.value` doesn't count as a subscriber. Nothing ever starts the feed. A value that is only read through `.value` needs `Eagerly` or the suspend `stateIn(scope)`.",
   "from": "flow-07"}
 ],
 "flashcards": [
  {"front": "When does a `callbackFlow` register its listener?", "back": "When its producer coroutine first runs, after collection starts. A value fired before that is lost. Reactor's `Flux.create` registers inside `subscribe()`."},
  {"front": "What happens when a `callbackFlow` block returns without `awaitClose`?", "back": "Collecting throws `IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.`"},
  {"front": "A collector waits on a default `callbackFlow`, and the probe fires 200 readings one after another. How many `trySend` calls succeed?", "back": "65: 64 buffered, plus 1 handed straight to the waiting receiver. The other 135 fail, and are lost unless you check the result."},
  {"front": "How does `Publisher.asFlow()` request from the publisher?", "back": "`request(64)`, then 64 more after every 64 collected. `buffer(n)` makes it `request(n)`; `conflate()` and `UNLIMITED` request `Long.MAX_VALUE`."},
  {"front": "With `asFlux()`, where does the flow suspend when the subscriber's demand runs out?", "back": "Inside `emit`, right after the `onNext` that used the last of the demand. A later `request(n)` resumes it."},
  {"front": "Tasks are due at +100 and +200 ms. What does `advanceTimeBy(100)` run?", "back": "Nothing: it runs tasks due before now + 100 and leaves the clock at 100. `runCurrent()` then runs the task at 100."},
  {"front": "Why can't a Turbine test show a StateFlow skipping a value, or a buffer that is too small?", "back": "Turbine collects on `UnconfinedTestDispatcher` and takes every value the instant it is sent, so it sees all values and the buffer never fills."}
 ],
 "terms": [
  {"term": "callbackFlow", "plain": "A flow builder for listener APIs. Its block registers a listener that sends into a channel, and `awaitClose` removes the listener when the flow ends."},
  {"term": "awaitClose", "plain": "Suspends the `callbackFlow` block until its channel is closed, then runs your cleanup, whatever ended the flow."},
  {"term": "Demand", "plain": "In Reactive Streams, the number of items a subscriber has asked for with `request(n)` and not yet received."},
  {"term": "Fusion", "plain": "A `buffer`, `conflate` or `flowOn` placed right after a channel-based flow changes that flow's own channel instead of adding a second one."},
  {"term": "Virtual time", "plain": "The test scheduler's clock in `runTest`. It jumps to the next due task, so a `delay` takes no real time."},
  {"term": "backgroundScope", "plain": "A scope inside `runTest` for coroutines that never end. They are cancelled when the test body ends, and `advanceUntilIdle()` doesn't wait for them."},
  {"term": "Turbine", "plain": "A test library (`app.cash.turbine`) that collects a flow into a queue you read with `awaitItem`, `awaitComplete` and `awaitError`."}
 ],
 "explain_back": {
  "prompt": "Explain to a friend why `probe.fire(r)` right after `backgroundScope.launch { probe.readings().collect { ... } }` loses the reading in a test, why rewriting the test with Turbine fixes that, and why Turbine would then hide a buffer that is too small.",
  "answer": "On the default StandardTestDispatcher, launch only queues the collector. The callbackFlow's producer coroutine, which calls register, runs the next time the scheduler runs, so the fire happens with no listener and the reading goes nowhere. Turbine's test { } runs the flow up to its first suspension before the block starts, so by then the listener is registered. But Turbine collects on UnconfinedTestDispatcher. Each trySend wakes it at once and the reading leaves the channel right away, so the channel never fills, and a 64-spot buffer passes a 500-reading burst. To test the buffer, collect with a Standard collector that can't run during the burst: launch it, call runCurrent() so it registers, fire the burst, call runCurrent() again and count."
 },
 "deeper": {
  "minutes": 10,
  "body": "The JDK has its own Reactive Streams interfaces, `java.util.concurrent.Flow`, with `Publisher`, `Subscriber` and `Subscription`. kotlinx.coroutines bridges them in a separate artifact, `org.jetbrains.kotlinx:kotlinx-coroutines-jdk9:1.11.0`. It is a thin wrapper over the reactive module: `asFlow()`, `asPublisher()` and `collect` for the JDK types, with the same demand mapping (a JDK publisher over 150 items saw `request(64)` three times). You don't need the extra artifact. reactive-streams 1.0.4, already on this lab's classpath through kotlinx-coroutines-reactive, has `org.reactivestreams.FlowAdapters`, and `FlowAdapters.toPublisher(jdkPublisher).asFlow()` does the same job.\n\nThe JDK `HttpClient` shows why that matters. `client.sendAsync(request, BodyHandlers.ofPublisher())` is two bridges in one call. The `CompletableFuture` completes once, when the headers arrive, so it belongs to `await()`. The body is a JDK `Flow.Publisher<List<ByteBuffer>>` that delivers chunks as they come off the socket, so it belongs to `asFlow()`. In one run against a local server that wrote five lines 50 ms apart, the chunks arrived about 50 ms apart too. Wrapping the future in `callbackFlow` would be the wrong tool: a single result is a `suspendCancellableCoroutine` or `await()` job.\n\nA few facts about the Reactor modules themselves. The README of kotlinx-coroutines-reactive calls `asPublisher` TCK-compliant, meaning it passes the official Reactive Streams compatibility tests. The subscription it creates has no parent job, so its lifetime belongs to the subscription and not to any scope. Element types must be non-null (`T : Any`), because Reactive Streams forbids `null` items. And the 1.11.0 reactor module declares reactor-core 3.4.1 in its pom; this course pins 3.8.8, and Gradle picks the higher version."
 },
 "sources": [
  {"title": "callbackFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html"},
  {"title": "kotlinx-coroutines-reactor (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/"},
  {"title": "kotlinx-coroutines-test README at the 1.11.0 tag", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/README.md"},
  {"title": "Turbine README", "url": "https://raw.githubusercontent.com/cashapp/turbine/trunk/README.md"},
  {"title": "Testing Kotlin flows (Android developers)", "url": "https://developer.android.com/kotlin/flow/test"}
 ]
}

out = ROOT / "content/lessons/flow-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
