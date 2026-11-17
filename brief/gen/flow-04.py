import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/flows/src"
P = "kotlin/workbench/flows/l04"
J = "java/workbench/flows/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :flows:demo -Pmain=workbench.flows.l04.{cls}{extra}"
API = "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/"


def tryit(kt, java=None, extra_kt=""):
    k = kt.replace(".kt", "")
    code = {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt)}
    if java:
        j = java.replace(".java", "")
        code["alt"] = {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}
    else:
        code["solo"] = True
    return code


spots = ""
for i in range(10):
    x = 166 + i * 36
    spots += (f'<rect class="box" x="{x}" y="56" width="32" height="38" rx="6"/>'
              f'<text class="t-s" x="{x + 16}" y="80" text-anchor="middle">{i + 2}</text>')

FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="buffer(10) drawn as a shelf in the hatch. The cook, a second coroutine on the left, '
    'sends dumplings onto a shelf with ten spots, holding dumplings 2 to 11. The diner on the right holds dumpling 1, still inside emit. '
    'So 11 emits have returned. Below, three small panels: a plain flow has no shelf and 0 emits ahead, buffer(0) is a hand-over with 1 emit ahead, '
    'and conflate() is a shelf with one spot where the newest value replaces the waiting one.">'
    '<text class="t-s t-m" x="346" y="34" text-anchor="middle">buffer(10): a shelf with 10 spots in the hatch</text>'
    '<rect class="box-a" x="20" y="50" width="120" height="50" rx="8"/>'
    '<text class="t" x="80" y="72" text-anchor="middle">cook</text>'
    '<text class="t-s" x="80" y="90" text-anchor="middle">coroutine 2</text>'
    '<line class="ln" x1="140" y1="75" x2="158" y2="75" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="160" y="48" width="364" height="54" rx="8"/>'
    + spots +
    '<line class="ln" x1="524" y1="75" x2="544" y2="75" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="546" y="50" width="114" height="50" rx="8"/>'
    '<text class="t" x="603" y="72" text-anchor="middle">diner</text>'
    '<text class="t-s" x="603" y="90" text-anchor="middle">holds dumpling 1</text>'
    '<text class="t-s t-m" x="342" y="124" text-anchor="middle">send() returns while a spot is free</text>'
    '<text class="t-s t-m" x="603" y="124" text-anchor="middle">emit(1) still running</text>'
    '<text class="t t-a" x="340" y="156" text-anchor="middle">emits returned = 10 on the shelf + 1 in hand = 11</text>'
    '<rect class="box" x="20" y="186" width="200" height="90" rx="8"/>'
    '<text class="t t-code" x="120" y="210" text-anchor="middle">flow { }</text>'
    '<text class="t-s" x="120" y="234" text-anchor="middle">emit runs the diner\'s code</text>'
    '<text class="t-s t-a" x="120" y="258" text-anchor="middle">0 emits ahead</text>'
    '<rect class="box" x="240" y="186" width="200" height="90" rx="8"/>'
    '<text class="t t-code" x="340" y="210" text-anchor="middle">buffer(0)</text>'
    '<text class="t-s" x="340" y="234" text-anchor="middle">coroutine 2, a hand-over</text>'
    '<text class="t-s t-a" x="340" y="258" text-anchor="middle">1 emit ahead</text>'
    '<rect class="box" x="460" y="186" width="200" height="90" rx="8"/>'
    '<text class="t t-code" x="560" y="210" text-anchor="middle">conflate()</text>'
    '<text class="t-s" x="560" y="234" text-anchor="middle">one spot, newest replaces</text>'
    '<text class="t-s t-bad" x="560" y="258" text-anchor="middle">never waits, drops</text>'
    '</svg>'
)

OPENING = """A big family lunch, and the cook is making dumplings, two hundred of them, cooked one at a time. A diner at the table eats them as they come. Then the diner's phone rings, with dumpling 1 still on the plate. In a plain flow, the cook stands at the table holding dumpling 2 until the call ends. Put a shelf in the hatch, and she can keep cooking while the diner talks.

How far does she get? It depends on the shelf, and the answer is always one more than people expect. And when the shelf is full, someone has to decide: the cook waits, or a dumpling goes in the bin. The easy trap is a line that reads like "keep the newest 64" and really keeps one.

In Context and threads, `flowOn` built a wall with a hatch to move work to another thread. `buffer` builds the same hatch only to change its shelf. In this lesson, we'll count how far the cook gets, choose what a full shelf throws away, watch shelves snap together, and time what `collectLatest` waits for. Before we start, make a guess, and keep it in mind."""

S1 = r"""Here is that lunch as code. The cook is a plain `flow { }` that counts how many of its `emit` calls have returned. The diner holds dumpling 1 until the call ends. Put a buffer between them and look at the counter while the diner is on the phone:

```kotlin
var returned = 0
val cook = flow { for (dumpling in 1..200) { emit(dumpling); returned = dumpling } }
launch { cook.buffer(10).collect { d -> diner.eat(d) } }   // the phone rings at dumpling 1
delay(100)
println(returned)   // and with no buffer? buffer(0)? buffer()?
```

```java
// Closest Java equivalent: a bounded queue between a cook thread and a diner thread
BlockingQueue<Integer> shelf = new ArrayBlockingQueue<>(10);
Thread.ofPlatform().start(() -> { for (int d = 1; d <= 200; d++) { putQuietly(shelf, d); returned.set(d); } });
Thread.ofPlatform().start(() -> { while (true) diner.eat(takeQuietly(shelf)); });   // stuck on dumpling 1
```

Write your four guesses down. The answers are 0 with no buffer, 1 for `buffer(0)`, 11 for `buffer(10)` and 65 for `buffer()`. They come out the same on every run.

The 0 is lesson 1 of this track: without a buffer, `emit` calls the diner's code, so it can't return while the diner is stuck. The other three numbers need a mechanism. The `buffer` KDoc, its documentation in the library's source, sketches it in a few lines, and it is worth writing out once:

```kotlin
fun <T> Flow<T>.handMadeBuffer(n: Int): Flow<T> = flow {
    coroutineScope {
        val channel = produce(capacity = n) { collect { send(it) } }   // coroutine 2 runs the upstream
        channel.consumeEach { emit(it) }                               // our coroutine hands each value on
    }
}
```

```java
// Closest Java equivalent: a second thread runs the upstream and puts into a queue with n slots
static <T> void handMadeBuffer(List<T> upstream, int n, Consumer<T> downstream) throws InterruptedException {
    BlockingQueue<T> shelf = n == 0 ? new SynchronousQueue<>() : new ArrayBlockingQueue<>(n);
    Thread producer = Thread.ofVirtual().start(() -> upstream.forEach(v -> putQuietly(shelf, v)));
    for (int i = 0; i < upstream.size(); i++) downstream.accept(shelf.take());
    producer.join();
}
```

Read it as two rooms with a hatch between them and a **shelf with n spots** in the hatch. `buffer(n)` moves everything above it into a second coroutine. In there, the cook's `emit` has become a `send` into a **channel**, a queue between coroutines, and `send` returns as soon as a spot is free. Our own coroutine takes values off the shelf and calls the real `emit`, which runs the diner. So while the diner holds dumpling 1, dumplings 2 to 11 sit on the shelf. Eleven emits have returned: ten for the dumplings on the shelf, and one for dumpling 1, which left the shelf when the diner picked it up.

If this looks like the wall with a hatch from lesson 3 of this track, it is the same machine. `flowOn` builds it to change the thread, and `buffer` builds it to change the size of the shelf.

`buffer(0)` has no spots. It's a hand-over where both hands must meet, which channels call a **rendezvous**. There is still a second coroutine, so exactly one emit returns. That one value of slack is why `buffer(0)` turns the 1,200 ms of lesson 1's dinner (a 100 ms cook, a 300 ms diner, three dishes) into 1,000 ms, the same as `buffer()`.

`buffer()` with no argument means `Channel.BUFFERED`, which is -2 in the code and 64 spots on the JVM. Hence 65. The system property `kotlinx.coroutines.channels.defaultBuffer` changes that default for every channel in the program. It is `@DelicateCoroutinesApi`, and its KDoc calls it a "last-ditch effort" for urgent fixes. Write the size at the call site instead.

**Behind `buffer(n)` the producer gets n + 1 ahead: n on the shelf, one in the collector's hands.**

Check yourself before the Try it: what does the probe print for `buffer(1)`? So far a full shelf made the cook wait. That is only one of the three things it can do."""

S2 = r"""Everything so far used the default **overflow policy**, which is what a full buffer does with a new value. The default, `BufferOverflow.SUSPEND`, makes `send` wait, so the cook waits. Nothing is lost, and the cook is never more than n + 1 ahead. The other two policies never wait. When the shelf is full they throw a value away.

Dumplings are the wrong food to throw away, so take something where only the newest value matters. The oven from StateFlow, SharedFlow and hot streams has a thermometer, and a little screen on the oven door shows its readings. Say the screen is stuck drawing reading 1 while 200 readings arrive. Which ones does it show once it's free?

| Operator | The screen shows | What the full shelf did |
|---|---|---|
| `buffer(10)` | all 200 | made the thermometer wait |
| `buffer(10, DROP_OLDEST)` | 1, then 191 to 200 | threw the oldest waiting reading in the bin |
| `buffer(10, DROP_LATEST)` | 1 to 11 | threw each new reading in the bin |
| `conflate()` | 1 and 200 | one spot: each new reading replaces the one on it |

Reading 1 is in every row because the screen had it in hand before the flood started.

`conflate()` is `buffer(CONFLATED)`, and **conflation** means keeping only the newest waiting value. The library turns `CONFLATED` into capacity 0 with `DROP_OLDEST`. A drop policy can't work with zero spots, so the channel gets exactly one. It's the ruthless shelf: each new value pushes the waiting one into the bin, and it never makes anybody wait.

That rule sets a trap. A helper wants "the newest 64 if the table falls behind" and writes `buffer(onBufferOverflow = DROP_OLDEST)`. The capacity defaults to `BUFFERED`, and the `Channel` KDoc says what that means with a drop policy: "If a different BufferOverflow is specified, `Channel(BUFFERED)` creates a channel with a buffer of size 1". So the line is `conflate()` under another name, and the probe receives `[1, 200]`. If you mean 64, write `buffer(64, DROP_OLDEST)`.

Conflation only loses values that arrive while the collector is busy. A screen that draws in 50 ms, behind a thermometer that reads every 100 ms, shows every reading.

So pick the policy by what a lost value costs. A stale temperature is worth nothing once a newer one exists, so the screen may conflate. A dropped plate of dumplings is a guest with no lunch, so plates for the table get `SUSPEND`, always.

**Before you pick a drop policy, ask what one lost value costs. If the answer is too much, keep `SUSPEND`.**

Reactor makes the same trades under other names, and you used them in Backpressure in practice, in the reactive track:

```kotlin
readings.conflate()
readings.buffer(10, BufferOverflow.DROP_OLDEST)
plates.buffer(10)                                     // full: the cook suspends
```

```java
// Closest Java equivalent: Reactor's onBackpressure operators
readings.onBackpressureLatest();
readings.onBackpressureBuffer(10, r -> {}, BufferOverflowStrategy.DROP_OLDEST);
plates.onBackpressureBuffer(10);                      // full: the stream fails
```

In the probe the first two match their Flow twins exactly: `[1, 200]` and `[1, 191..200]`. The third doesn't. Reactor's bounded buffer with no strategy cancels the source and fails with `OverflowException: The receiver is overrun by more signals than expected (bounded queue...)`. Flow's bounded buffer has no failure mode. It makes the producer wait.

Check yourself: what does `buffer(0, DROP_LATEST)` deliver in the same probe? So far each chain had one buffer. Put two side by side, and they don't stay two."""

S3 = r"""`buffer(10).buffer(20)` doesn't build two shelves. It builds one shelf with 30 spots, and the probe counts 31 emits. Every operator that is built on a channel (`buffer`, `conflate`, `flowOn`, `channelFlow`, `produceIn`) first looks at the flow it was called on. If that is also a channel flow, it adds no coroutine. It merges its settings into the one that is already there. The library calls this **fusion**. Picture short shelves snapped together into one long shelf with a single label on it.

The merge rules are short:

- Two explicit sizes add up: 10 + 20 is 30.
- `buffer()` without a size gives way to an explicit one, so `buffer(10).buffer()` has 10 spots and `buffer().buffer()` still has 64.
- A policy other than `SUSPEND` replaces everything before it. `buffer(10).conflate()` is plain `conflate()`, and the 10 is thrown away. `conflate().buffer(10)` is a 10-spot shelf that drops the oldest.
- `flowOn` shares the channel too. `buffer(5).flowOn(Dispatchers.IO)` and `flowOn(Dispatchers.IO).buffer(5)` are both one channel, filled on IO, with 5 spots.

You can watch it happen, because these channel flows print their settings in `toString()`:

```text
buffer(10).buffer(20)    ChannelFlowOperatorImpl[capacity=30]
buffer(10).conflate()    ChannelFlowOperatorImpl[capacity=0, onBufferOverflow=DROP_OLDEST]
conflate().buffer(10)    ChannelFlowOperatorImpl[capacity=10, onBufferOverflow=DROP_OLDEST]
buffer(5).flowOn(IO)     ChannelFlowOperatorImpl[context=Dispatchers.IO, capacity=5]
```

Treat that string as a peek under the hood. It is a debug aid, not an API, and any release may change it. When it matters, test the behaviour instead: count the emits that return while the collector is stuck, as the lab does.

Here the shelf picture breaks. Two real shelves in a row hold the plates of both, and nothing on the second shelf can empty the first. Fused buffers are one shelf with one label, and a drop policy written at the end rewrites the label for everything before it.

One line in the docs reads the other way. The `conflate` KDoc says that if a buffer size was given before it, "the buffer size is unchanged". In 1.11.0, `buffer(10).conflate()` delivers `[1, 200]` in the probe, exactly like `conflate()`, and its `toString()` shows capacity 0. The `buffer` KDoc matches the code: a `buffer` call with a non-`SUSPEND` policy "overrides all immediately preceding buffering operators". I read the `conflate` sentence as ambiguous rather than wrong, and I don't rely on it. When I want ten spots that drop the oldest, I write it in one call: `buffer(10, DROP_OLDEST)`.

Check yourself: what single channel does `buffer(10).buffer(5, DROP_LATEST)` become? Every buffer so far threw away values that were still waiting. The Latest operators go one step further: they stop work that has already started."""

S4 = r"""Back to the screen on the oven door. It moves to `collectLatest`, so a new reading cancels the drawing in progress. A cancelled drawing must wipe its half-drawn number first, which takes 50 ms that can't be cancelled. (`NonCancellable`, from Cancellation and timeouts, is the context that lets such cleanup run after a cancel.) Readings arrive every 100 ms and a drawing takes 300 ms. When does the thermometer emit reading 3?

```kotlin
readings.collectLatest { reading ->
    try {
        draw(reading)                                              // 300 ms
    } catch (e: CancellationException) {
        withContext(NonCancellable) { wipeHalfDrawn(reading) }     // 50 ms
        throw e
    }
}
```

```java
// Closest Java equivalent: switchMap cancels the inner; a cancel is a signal, so the wipe can only be fired off
readings.switchMap(reading -> draw(reading)
        .doOnCancel(() -> wipeHalfDrawnAsync(reading).subscribe()));
```

Most people say 300. The virtual clock says 350, and the run ends at 700 instead of 600 (lines merged for space):

```text
t=100 emit 1, start 1
t=200 emit 2, cancelled 1 (ChildCancelledException)
t=250 cleanup of 1 finished, start 2
t=350 emit 3, cancelled 2
t=400 cleanup of 2 finished, start 3
t=700 done 3
```

`collectLatest` is `mapLatest(action).buffer(0).collect()`, and `mapLatest` is a thin wrapper over `transformLatest`. Its core is a short loop. A producer coroutine collects the upstream, and for each new value it cancels the previous block, joins it (waits for it to finish), and only then launches the new one:

```kotlin solo
flow.collect { value ->
    previous?.apply { cancel(ChildCancelledException()); join() }    // wait until the old block has finished
    previous = launch(start = CoroutineStart.UNDISPATCHED) { collector.transform(value) }
}
```

The `join()` is the surprise. Reading 1's wipe must finish before reading 2's drawing starts. And this loop body runs inside the upstream's `collect`, so the `join()` also sits inside the thermometer's `emit`. The thermometer can't start its next `delay(100)` until the old block has cleaned up. Picture the screen wiping its half-drawn number before it starts the new one, while the thermometer waits at the hatch with the next reading. Reactor's `switchMap` gives emits at 100, 200 and 300 and ends at 600, because a Reactor cancel is a method call that returns at once, with no suspending cleanup to wait for.

Two rules follow. Keep the cancelled path short. And use the Latest family only for work you can throw away. Drawing a number on a screen changes nothing else, so a cancelled drawing costs nothing. Writing each reading into the cooking log is a side effect, a change that stays after the block ends: a cancelled block may have written half a line, and a skipped reading is never written. That pipeline gets `buffer()`.

**Use the Latest operators only for work you can throw away, and keep their cleanup short.**

Cancelling yourself behind a shelf has its own surprise. A collector that never suspends calls `cancel()` on its own job at value 3. Behind `buffer()` it still receives 66 values in all, and behind `buffer(10)` it receives 12. The values already on the shelf keep coming, because receiving from a channel that has elements doesn't suspend, and `emitAll` checks for cancellation once, before its loop. A collector that waits on a file or calls `delay` sees the cancel at its next suspension, so this bites only collectors that do nothing but compute. Add `.cancellable()` after the buffer. It checks before every emit, and the count drops to 3.

Every flow in this lesson made one value at a time and handed it on. A value can also start a whole flow of its own, and that is where flows begin to branch."""

CLOSING = """We started with a diner on the phone and a cook holding dumpling 2. `buffer(n)` gives her a shelf of n spots in the hatch, so she gets n + 1 ahead and then waits. A drop policy never waits; it bins plates. Shelves side by side fuse into one, and `collectLatest` cancels old work but waits for its cleanup.

Now find each `buffer` and `conflate` in your own code and ask what one lost value costs. If it's a missing plate, keep `SUSPEND`.

Next, we'll flatten and combine flows. When each value starts a flow of its own, which ones run at the same time, and how do you join two flows that tick at different speeds?"""

L = {
 "id": "flow-04",
 "title": "Buffering: buffer, conflate, collectLatest and fusion",
 "minutes": 35,
 "goal": "By the end you can predict how far a producer runs ahead behind any buffer or conflate chain, which values it loses and why, what collectLatest waits for, and pick the right one for values where only the newest matters and for values that must never be lost.",
 "opening": OPENING,
 "warmup": {
  "q": "A cook sends 200 dumplings into `.buffer(10)`. The diner's phone rang, and the diner is stuck on dumpling 1. How many of the cook's `emit` calls have returned?",
  "options": [
   "0: emit always waits for the collector",
   "10: one per spot on the shelf",
   "11",
   "200: the buffer lets the cook finish"
  ],
  "answer": 2,
  "why": "`buffer(10)` runs the cook in a second coroutine that sends into a channel with 10 slots. Dumplings 2 to 11 fill the shelf, and dumpling 1 left it when the diner took it. That is 10 + 1. Then the next `send` suspends. The answer 0 is right only without a buffer, where `emit` calls the diner's code directly."
 },
 "sections": [
  {
   "h": "buffer(n): a second coroutine and a shelf with n spots",
   "body": S1,
   "figure": {"svg": FIG, "caption": "With the default SUSPEND policy the producer gets n + 1 emits ahead: n on the shelf, one in the collector's hands."},
   "try": {
    "title": "Count the emits that return",
    "minutes": 4,
    "steps": [
     "Open `AheadProbe.kt`. Before you run it, write down a number for each of the seven lines, including `handMadeBuffer(10)`, the KDoc's sketch.",
     "Run it with the command below and compare.",
     "Run it again with `-Pargs=8` added. That sets `kotlinx.coroutines.channels.defaultBuffer` to 8 before any channel exists. Which line changes?",
     "Run the Java twin, `AheadProbeJava`. It puts a `SynchronousQueue` or an `ArrayBlockingQueue` between two threads. Predict its four numbers first."
    ],
    "code": tryit("AheadProbe.kt", "AheadProbeJava.java"),
    "expect": "Plain 0, `buffer(0)` 1, `buffer(1)` 2, `buffer(10)` 11, `handMadeBuffer(10)` 11, `buffer()` 65, `buffer(UNLIMITED)` 200, and all 200 dumplings are eaten in every line. With `-Pargs=8`, only `buffer()` changes, to 9. The Java twin prints 1, 2, 11 and 65: the same counting, with a blocked thread where Kotlin has a suspended coroutine."
   }
  },
  {
   "h": "When the shelf is full, the overflow policy decides which value is lost",
   "body": S2,
   "try": {
    "title": "Flood a stuck oven screen",
    "minutes": 4,
    "steps": [
     "Open `DropPolicies.kt`. For each of the six lines, predict which readings the screen shows after it gets unstuck.",
     "Run it. Look hardest at `buffer(onBufferOverflow = DROP_OLDEST)`.",
     "Run the Reactor twin, `DropPoliciesJava`. Find the one line where Reactor and Flow disagree, and the line Flow has no exact twin for."
    ],
    "code": tryit("DropPolicies.kt", "DropPoliciesJava.java"),
    "expect": "Flow: `buffer(10)` shows all 200, `DROP_OLDEST` `[1, 191..200]`, `DROP_LATEST` `[1..11]`, `conflate()` `[1, 200]`, `buffer(onBufferOverflow = DROP_OLDEST)` also `[1, 200]` (one spot), and `buffer(0, DROP_LATEST)` `[1, 2]`. Reactor matches the first three, `onBackpressureDrop()` gives just `[1]`, and `onBackpressureBuffer(10)` delivers 11 and then fails with \"The receiver is overrun by more signals than expected (bounded queue...)\"."
   }
  },
  {
   "h": "Buffers side by side fuse into one channel",
   "body": S3,
   "try": {
    "title": "Read the label on the shelf",
    "minutes": 3,
    "steps": [
     "Open `Fusion.kt`. For each chain, predict the capacity and policy the single channel ends up with, and the emits that return while the collector is stuck.",
     "Run it. The middle column is `toString()`, the right column is the behaviour.",
     "Add a line for `buffer(10).buffer(5, BufferOverflow.DROP_LATEST)` and check your answer to the section's question."
    ],
    "code": tryit("Fusion.kt"),
    "expect": "`buffer()` and `buffer().buffer()` both show `capacity=-2` and 65 ahead. `buffer(10).buffer(20)` shows `capacity=30` and 31 ahead. `buffer(10).conflate()` shows `capacity=0, onBufferOverflow=DROP_OLDEST` and receives 2. `conflate().buffer(10)` shows `capacity=10` with `DROP_OLDEST` and receives 11. `buffer(5).flowOn(IO)` is one channel on IO with 5 spots, 6 ahead. Your extra line shows `capacity=5, onBufferOverflow=DROP_LATEST`."
   }
  },
  {
   "h": "collectLatest: a new value cancels the old block, then waits for its cleanup",
   "body": S4,
   "try": {
    "title": "Time the wipe",
    "minutes": 4,
    "steps": [
     "Open `LatestJoin.kt`. It runs on virtual time. Predict the time of `emit 3` and of `done 3` before you run it.",
     "Run it. Then change the cleanup's `delay(50)` to `delay(150)` and predict again.",
     "Read the second half of the output: a collector that never suspends cancels itself at 3. Predict each count first.",
     "Run `LatestJoinJava`, the `switchMap` twin, in real time."
    ],
    "code": tryit("LatestJoin.kt", "LatestJoinJava.java"),
    "expect": "`emit 3` at 350 and `done 3` at 700. With a 150 ms cleanup, reading 2 starts at 350, the thermometer emits reading 3 at 450, and reading 3 is done at 900 ms. The collector that only computes gets 0 extra values from `flow { }`, 9 behind `buffer(10)`, 63 behind `buffer()`, and 0 once `.cancellable()` follows the buffer. The Reactor twin emits at about 100, 200 and 300 ms and finishes at about 600 ms: its cancel doesn't wait for anything."
   }
  }
 ],
 "compare": {
  "title": "The same loss policies in Kotlin Flow and in Reactor",
  "java": {"title": "Reactor", "src": """Flux<Plate> everyPlate = plates.limitRate(64);                       // demand in batches of 64; nothing is dropped
Flux<Reading> newestOnly = readings.onBackpressureLatest();           // one slot, the newest replaces it
Flux<Reading> lastTen = readings.onBackpressureBuffer(10, r -> {}, BufferOverflowStrategy.DROP_OLDEST);
Flux<Reading> firstTen = readings.onBackpressureBuffer(10, r -> {}, BufferOverflowStrategy.DROP_LATEST);
Flux<Reading> failFast = readings.onBackpressureBuffer(10);           // full: OverflowException
Flux<Shown> shown = readings.switchMap(screen::draw);                 // a new reading cancels the old drawing"""},
  "kotlin": {"title": "Kotlin Flow", "src": """val everyPlate = plates.buffer(64)                                    // full: the cook suspends
val newestOnly = readings.conflate()                                  // one slot, the newest replaces it
val lastTen = readings.buffer(10, BufferOverflow.DROP_OLDEST)
val firstTen = readings.buffer(10, BufferOverflow.DROP_LATEST)
// no failFast: a bounded Flow buffer never errors, it makes the producer wait
@OptIn(ExperimentalCoroutinesApi::class)
val shown = readings.mapLatest { screen.draw(it) }                   // cancels, joins, then starts the next"""},
  "note": "Both libraries offer the same drop policies, and the probe gives the same lists in both. The machinery underneath differs. Reactor's backpressure is a number sent upstream with `request(n)`, so `limitRate` reshapes demand and `onBackpressureBuffer(n)` has to decide what to do when a source ignores it: by default it fails. A cold Kotlin flow can't overflow, because `emit` doesn't return until the collector is ready. Loss is possible only where something puts a channel between two coroutines, and that is exactly what `buffer`, `conflate` and `flowOn` do. Two more differences show up in this lesson. Adjacent Flow buffers fuse into one channel with combined settings. And `mapLatest` joins the cancelled block before it starts the next one, while `switchMap` just sends the cancel."
 },
 "worked": {
  "title": "Pick the buffering for three kitchen pipelines",
  "steps": [
   {
    "say": "The oven-door screen shows the temperature. Readings come every 100 ms, a drawing takes 300 ms, and only the newest reading matters. A drawing that has started may finish. That is conflation.",
    "code": "val shown: Flow<Shown> = readings\n    .conflate()                       // 1. one spot: a busy screen skips to the newest reading\n    .map { screen.draw(it) }          // 2. runs below the spot, in the collector's coroutine",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: keep the newest reading, draw one at a time\nFlux<Shown> shown = readings\n        .onBackpressureLatest()           // 1. one spot: a busy screen skips to the newest reading\n        .concatMap(screen::draw, 1);      // 2. one drawing at a time, asking for one reading at a time"
   },
   {
    "say": "The kitchen scale has a display too, and someone is pouring flour. A stale drawing should stop at once, and drawing has no side effects. Cancel it. In virtual time this finishes only the newest of three weights, at 600 ms.",
    "code": "@OptIn(ExperimentalCoroutinesApi::class)   // mapLatest is experimental in 1.11.0\nval display: Flow<Shown> = weights\n    .mapLatest { grams -> scaleScreen.draw(grams) }   // a new weight cancels, joins, then starts again",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: switchMap cancels the inner drawing when a new weight arrives\nFlux<Shown> display = weights\n        .switchMap(scaleScreen::draw);"
   },
   {
    "say": "The plates for the table: nothing may be lost, and memory must stay bounded when the diner is on the phone. The default policy does both. The cook can get 65 plates ahead, then she waits.",
    "code": "cook.plates()\n    .buffer(64)                       // SUSPEND: a full shelf makes the cook wait\n    .collect { diner.eat(it) }        // nothing dropped, at most 64 waiting",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: a bounded queue between the cook thread and the diner\nBlockingQueue<Plate> shelf = new ArrayBlockingQueue<>(64);\nThread.ofVirtual().start(() -> cook.plates().forEach(p -> putQuietly(shelf, p)));   // blocks when full\nwhile (true) diner.eat(shelf.take());"
   },
   {
    "say": "Review the helper's version of the plates pipeline, which was meant to \"keep the newest 64\". It keeps one. During a long phone call it serves plate 1 and the last one cooked, and quietly bins the rest. Replace it with step 3.",
    "code": "cook.plates()\n    .buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST)   // BUFFERED + a drop policy = ONE spot\n    .collect { diner.eat(it) }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Closest Java equivalent of the bug: Reactor's latest-only buffer\ncook.platesFlux()\n        .onBackpressureLatest()                                // one spot, the newest replaces it\n        .concatMap(diner::eat, 1)\n        .blockLast();"
   }
  ]
 },
 "lab": {
  "title": "Build a shelf by hand, then buffer oven readings and plates",
  "minutes": 14,
  "files": [
   "labs/flows/src/main/kotlin/workbench/flows/l04/Shelf.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l04/Buffering.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l04/Model.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l04.*'",
  "steps": [
   "Run the tests once. All 11 fail. Read the test names in `BufferingTest`: they are the spec, and every timing is in virtual milliseconds.",
   "In `Shelf.kt`, write `shelf(capacity)` without calling `buffer()`: `flow { coroutineScope { ... } }` with a `Channel<T>(capacity)`, a `launch` that collects the upstream into it with `send` and closes it in a `finally`, and a `for` loop over the channel that calls `emit`.",
   "In `Buffering.kt`, write `everyReading`, `latestReading` and `cancelStale`. Each is one operator and at most one `map`. Predict each test's virtual time before you run it.",
   "Fix `towardsTable`. The tests say the cook may run exactly 64 plates ahead and must never lose one.",
   "Run the tests until all 11 pass, then run them once more."
  ],
  "hints": [
   "If `shelf(10)` reports 0 emits, the upstream still runs in the collector's coroutine. The `collect { spots.send(it) }` must be inside the `launch`.",
   "If a `shelf` test hangs and then times out, the `for` loop is waiting for more values. Close the channel when the upstream's `collect` returns, in a `finally`.",
   "`mapLatest` needs `@OptIn(ExperimentalCoroutinesApi::class)` in 1.11.0. Without it the compiler warns but still builds.",
   "For `towardsTable`, the default policy is the right one. You only need the right number of spots."
  ],
  "done_when": "All 11 tests in `BufferingTest` pass, twice in a row."
 },
 "drill": {
  "title": "Write buffer(n) from memory",
  "minutes": 5,
  "prompt": "Close this page and the lab. Write `fun <T> Flow<T>.myBuffer(n: Int): Flow<T>` with `flow { }`, `coroutineScope`, a `Channel` and `launch`. Then answer without running anything: behind `myBuffer(3)`, how many emits return while the collector is stuck on its first value? And behind `myBuffer(3).myBuffer(3)`, built from your function rather than the library's?",
  "answer": {
   "lang": "kotlin",
   "src": "fun <T> Flow<T>.myBuffer(n: Int): Flow<T> = flow {\n    coroutineScope {\n        val spots = Channel<T>(n)\n        launch {                                   // 1. a second coroutine runs the upstream\n            try { collect { spots.send(it) } }     //    send waits only when all n spots are full\n            finally { spots.close() }              // 2. lets the loop below end\n        }\n        for (value in spots) emit(value)           // 3. our coroutine hands each value on\n    }\n}\n// myBuffer(3): 3 on the shelf + 1 in hand = 4 emits return.\n// myBuffer(3).myBuffer(3): your function doesn't fuse, so it is two shelves and three coroutines.\n// The middle coroutine holds one value too: 3 + 1 + 3 + 1 = 8. The library's buffer(3).buffer(3)\n// fuses into one channel of 6 spots, so 7.",
   "alt": {
    "lang": "java",
    "src": "// Closest Java equivalent: a producer thread and a queue with n slots (n >= 1 here)\nstatic <T> void myBuffer(Iterable<T> upstream, int n, Consumer<T> downstream) throws InterruptedException {\n    BlockingQueue<Optional<T>> spots = new ArrayBlockingQueue<>(n);\n    Thread producer = Thread.ofVirtual().start(() -> {   // 1. a second thread runs the upstream\n        try {\n            for (T v : upstream) spots.put(Optional.of(v)); //    put blocks only when all n slots are full\n            spots.put(Optional.empty());                    // 2. the end marker lets the loop below end\n        } catch (InterruptedException e) { Thread.currentThread().interrupt(); }\n    });\n    for (Optional<T> v = spots.take(); v.isPresent(); v = spots.take()) downstream.accept(v.get());   // 3.\n    producer.join();\n}"
   }
  }
 },
 "recap": [
  "`buffer(n)` runs the upstream in a second coroutine that sends into a channel with n slots. With the default `SUSPEND`, the producer gets n + 1 emits ahead: n on the shelf and one in the collector's hands.",
  "`buffer(0)` still adds a coroutine, so it is 1 ahead. `buffer()` is `Channel.BUFFERED`, 64 slots on the JVM, so 65 ahead.",
  "`DROP_OLDEST`, `DROP_LATEST` and `conflate()` never wait; they drop. `buffer(onBufferOverflow = DROP_OLDEST)` has one slot. Values that must never be lost get `SUSPEND` only.",
  "Adjacent channel operators fuse into one channel: explicit sizes add, and a drop policy replaces what came before. `buffer(10).conflate()` is `conflate()`. `toString()` shows the result, but test the behaviour.",
  "`collectLatest` and `mapLatest` cancel the old block and join it, so a slow cleanup delays the next block and the producer. Use them only for work you can throw away.",
  "The limit: a buffer only reshapes one stream between one producer and one collector, and a collector that never suspends keeps receiving what's on the shelf after it cancels (add `.cancellable()`). Running several inner flows at once is flatMap's job, next lesson."
 ],
 "closing": CLOSING,
 "quiz": [
  {
   "q": "Behind `buffer(10).buffer(20)` with the default policy, the collector is stuck on its first value. How many of the producer's emits have returned?",
   "options": [
    "21: the second buffer wins",
    "32: two coroutines, each holding one",
    "31",
    "11: the first buffer is the one the producer sees"
   ],
   "answer": 2,
   "why": "Adjacent buffers fuse into one channel, and two explicit sizes add up to 30. One channel means one extra coroutine, so it is 30 on the shelf plus 1 in hand. 32 would be right for two separate shelves, which is what a hand-written buffer without fusion gives you."
  },
  {
   "q": "A helper puts `buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST)` between the cook and the table, \"to keep the newest 64\". The diner is on the phone while 200 plates are cooked. How many reach the table?",
   "options": [
    "All 200",
    "Plate 1 and the newest 64",
    "64",
    "2: plate 1 and plate 200"
   ],
   "answer": 3,
   "why": "The capacity defaults to `BUFFERED`, and a `BUFFERED` channel with a drop policy has one slot, so this is `conflate()`. The diner eats the plate in hand and the one standing on the shelf at the end. For plates, no drop policy is acceptable: use `buffer(64)` with the default `SUSPEND`."
  },
  {
   "q": "Readings every 100 ms go into `collectLatest`. A drawing takes 300 ms, and a cancelled one runs a 50 ms `withContext(NonCancellable)` cleanup. When does the thermometer emit reading 3?",
   "options": [
    "300 ms",
    "350 ms",
    "400 ms",
    "It never does: collectLatest stops the thermometer"
   ],
   "answer": 1,
   "why": "`transformLatest` cancels the old block and then joins it, inside the thermometer's `emit`. Reading 2 at 200 waits 50 ms for reading 1's cleanup, so the next `delay(100)` starts at 250 and reading 3 comes at 350. 300 is what you'd get with no cleanup, or with Reactor's `switchMap`, which doesn't wait."
  },
  {
   "q": "A collector that only computes (no I/O, no `delay`) reads from `flow { for (i in 1..100) emit(i) }.buffer()` and calls `cancel()` on its own job when it sees 3. It receives 66 values. What is the smallest fix?",
   "options": [
    "Add `.cancellable()` after `buffer()`",
    "Add `.cancellable()` before `buffer()`",
    "Replace `flow { }` with `(1..100).asFlow()`",
    "Replace `cancel()` with `return@collect`"
   ],
   "answer": 0,
   "why": "The values already on the shelf keep coming because receiving from a channel that has elements doesn't suspend, and nothing checks cancellation per value on the collector's side. `.cancellable()` after the buffer checks before each emit, and the count drops to 3. Before the buffer it guards the producer, which `flow { }` already does. `asFlow()` checks less, not more. And `return@collect` only ends this one call of the lambda, so all 100 values arrive."
  },
  {
   "q": "From the reactive track: Reactor's `onBackpressureBuffer(10)` with no strategy and Flow's `buffer(10)` both sit in front of a stuck subscriber while 200 items arrive. What happens in each?",
   "options": [
    "Both drop the newest items once 10 are waiting",
    "Both make the source wait",
    "Reactor delivers 11 and then fails with an OverflowException; Flow makes the producer suspend and later delivers all 200",
    "Reactor makes the source wait; Flow fails with an exception"
   ],
   "answer": 2,
   "why": "Reactor's bounded buffer with no strategy cancels the source and signals `OverflowException` (\"The receiver is overrun by more signals than expected\") when it overflows. A Flow buffer has no failure mode: with `SUSPEND`, a full channel makes `send` wait, so nothing is lost and nothing fails.",
   "from": "rx-07"
  }
 ],
 "flashcards": [
  {"front": "With the default policy, how many emits return behind `buffer(n)` while the collector is stuck on its first value?", "back": "n + 1: n wait on the shelf (the channel), one is in the collector's hands."},
  {"front": "What does `buffer(0)` still create, and how far ahead is the producer?", "back": "A second coroutine and a rendezvous hand-over. One emit returns: the value that was handed over."},
  {"front": "How many slots does `buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST)` have?", "back": "One. A `BUFFERED` channel with a drop policy is a one-slot channel, so it acts like `conflate()`. Write `buffer(64, DROP_OLDEST)` if you mean 64."},
  {"front": "What is `buffer(10).conflate()`? And `conflate().buffer(10)`?", "back": "Plain `conflate()`: a drop policy overrides the buffers before it. `conflate().buffer(10)` is one 10-slot channel that drops the oldest."},
  {"front": "What does `buffer(10).buffer(20)` build?", "back": "One fused channel with 30 slots, so the producer gets 31 ahead."},
  {"front": "In `collectLatest`, what happens to the old block when a new value arrives?", "back": "It is cancelled (`ChildCancelledException`) and joined. Its cleanup finishes before the new block starts, and the producer's `emit` waits for it too."},
  {"front": "Flow `buffer(10)` is full. Reactor `onBackpressureBuffer(10)` is full. What does each do?", "back": "Flow suspends the producer. Reactor cancels the source and fails with `OverflowException`."}
 ],
 "terms": [
  {"term": "buffer (Flow operator)", "plain": "Runs everything above it in a second coroutine and puts a channel between that coroutine and the collector. In the kitchen, a shelf in the hatch."},
  {"term": "Capacity", "plain": "How many values can wait in the channel. With SUSPEND, the producer can get capacity + 1 emits ahead."},
  {"term": "Overflow policy", "plain": "What a full buffer does with a new value: SUSPEND makes the sender wait, DROP_OLDEST discards the oldest waiting value, DROP_LATEST discards the new one."},
  {"term": "Conflation", "plain": "Keeping only the newest waiting value. `conflate()` is a one-slot buffer that drops the oldest."},
  {"term": "Rendezvous", "plain": "A channel with no slots. A send waits until a receiver takes the value."},
  {"term": "Fusion", "plain": "Adjacent channel-based operators merging into one channel with combined settings, instead of one coroutine each."},
  {"term": "ChildCancelledException", "plain": "The cancellation the Latest operators use to stop the previous block. Its message is \"Child of the scoped flow was cancelled\"."}
 ],
 "explain_back": {
  "prompt": "A friend asks why the plates for the table use `buffer(64)` while the oven screen uses `conflate()`, and why `buffer(onBufferOverflow = DROP_OLDEST)` isn't a good middle ground for both. Explain it with the shelf picture and the numbers from this lesson.",
  "answer": "A buffer runs the upstream in a second coroutine and puts a shelf between it and the collector. With `buffer(64)` and the default SUSPEND policy, the cook can get 65 plates ahead of a diner who is stuck, 64 on the shelf and one in the diner's hands, and then her `send` waits. Memory stays bounded and no plate is lost, which is what the table needs, because a dropped plate is a guest with no lunch. The oven screen is different: an old temperature is worthless once a new reading exists, so `conflate()` is fine. It is a shelf with one spot where a new reading replaces the one waiting, and a drawing that has started still finishes. `buffer(onBufferOverflow = DROP_OLDEST)` looks like \"keep the newest 64\", but with the default BUFFERED capacity a drop policy gives a one-slot channel. Under a long stall it serves plate 1 and the last one cooked, which is `conflate()` with a misleading name. It's wrong for the plates, and for the screen it just says `conflate()` in a confusing way."
 },
 "deeper": {
  "minutes": 10,
  "body": "The class behind `buffer`, `conflate` and `flowOn` is `ChannelFlowOperatorImpl`, an internal subclass of `ChannelFlow`. Its `fuse` method does the merging. The new context is `context + this.context`, so for each context key the setting nearest the source wins, which is why two adjacent `flowOn` calls keep the first one. If the new policy is not `SUSPEND`, it overwrites the capacity and policy (the source comment says \"this additional buffer never suspends => overwrite preceding buffering configuration\"). Otherwise the capacities combine: `BUFFERED` gives way to an explicit size, two explicit sizes add up, and a sum that overflows `Int` becomes `UNLIMITED`.\n\n`buffer` checks its arguments with `require`. `buffer(-5)` fails with \"Buffer size should be non-negative, BUFFERED, or CONFLATED, but was -5\", and `buffer(Channel.CONFLATED, BufferOverflow.DROP_LATEST)` fails with \"CONFLATED capacity cannot be used with non-default onBufferOverflow\".\n\nOther operators are channel flows too, and they fuse with a `buffer` placed right after them. `channelFlow { }` prints as `ChannelFlowBuilder[capacity=-2]`, and `channelFlow { }.buffer(3)` resizes the builder's own channel. `mapLatest { }` prints as `ChannelFlowTransformLatest[capacity=-2]`, which is why its KDoc says it is \"buffered by default\". `flatMapMerge { }` prints as `ChannelFlowMerge[concurrency=16, capacity=-2]`; the next lesson takes it apart.\n\n`StateFlow` already behaves as if `conflate()` were applied, and the KDoc says applying `conflate` to it has no effect. Lesson 7 of this track looks at why.\n\nReactor's `limitRate(10)` looks like `buffer(10)` in the probe: the source got 10 ahead, where Flow's count is 11 because the Flow probe counts emits that returned. The mechanism is different: `limitRate` batches the demand it sends upstream. It asks for 10, then for 8 more each time 75 % of a batch has been used."
 },
 "sources": [
  {"title": "buffer (kotlinx.coroutines API)", "url": API + "kotlinx.coroutines.flow/buffer.html"},
  {"title": "conflate (kotlinx.coroutines API)", "url": API + "kotlinx.coroutines.flow/conflate.html"},
  {"title": "collectLatest (kotlinx.coroutines API)", "url": API + "kotlinx.coroutines.flow/collect-latest.html"},
  {"title": "The kotlinx.coroutines Flow guide at tag 1.11.0 (Buffering, Conflation, Processing the latest value)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/docs/topics/flow.md"},
  {"title": "Flux.java in reactor-core 3.8 (onBackpressureBuffer, onBackpressureLatest)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java"}
 ]
}

out = ROOT / "content/lessons/flow-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
