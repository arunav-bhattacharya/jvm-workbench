import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/flows/src"
P = "kotlin/workbench/flows/l07"
J = "java/workbench/flows/l07"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :flows:demo -Pmain=workbench.flows.l07.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


# ---- the figure: WhileSubscribed(5_000) as a tap on a motion sensor ----
def x(ms):
    return round(100 + ms * 0.03625, 1)


def bar(cls, a, b, y, h=28):
    return f'<rect class="{cls}" x="{x(a)}" y="{y}" width="{round(x(b) - x(a), 1)}" height="{h}" rx="8"/>'


ticks = ""
for ms, label in [(0, "0"), (2500, "2.5 s"), (4000, "4 s"), (6000, "6 s"), (11000, "11 s"), (14000, "14 s")]:
    ticks += f'<line class="ln" x1="{x(ms)}" y1="224" x2="{x(ms)}" y2="232"/><text class="t-s t-m" x="{x(ms)}" y="248" text-anchor="middle">{label}</text>'

FIG = (
    '<svg viewBox="0 0 700 270" role="img" aria-label="Timeline of stateIn with WhileSubscribed 5000. Dashboard A is subscribed from 0 to 2.5 s, '
    'from 4 s to 6 s and again from 14 s. The upstream run 1 lasts from 0 to 11 s: the stop timer that started at 2.5 s was cancelled when A came back at 4 s, '
    'and the timer that started at 6 s ran for 5 s and stopped the upstream at 11 s. At 4 s A gets 104 from the same run. At 14 s A first gets the stale 111, '
    'then run 2 starts and sends 200.">'
    '<text class="t-s t-code" x="15" y="22">stateIn(scope, WhileSubscribed(5_000), initialValue = -1)</text>'
    '<text class="t-s t-m" x="15" y="76">dashboard A</text>'
    '<text class="t-s t-m" x="15" y="134">upstream run</text>'
    '<text class="t-s t-m" x="15" y="186">stop timer</text>'
    '<text class="t-s" x="281" y="48" text-anchor="middle">back at 4 s: gets 104</text>'
    '<text class="t-s" x="690" y="48" text-anchor="end">back at 14 s: stale 111, then 200</text>'
    + bar("box-b", 0, 2500, 58) + bar("box-b", 4000, 6000, 58) + bar("box-b", 14000, 15500, 58)
    + bar("box-a", 0, 11000, 116)
    + f'<text class="t-s" x="{x(5500)}" y="135" text-anchor="middle">run #1: 100, 101, 102 ... 111</text>'
    + bar("box-a", 14000, 15500, 116)
    + f'<text class="t-s" x="{x(14750)}" y="135" text-anchor="middle">#2</text>'
    + f'<line class="ln-d" x1="{x(2500)}" y1="182" x2="{x(4000)}" y2="182"/>'
    + f'<text class="t-s t-ok" x="{x(3250)}" y="202" text-anchor="middle">cancelled</text>'
    + f'<line class="ln-d" x1="{x(6000)}" y1="182" x2="{x(11000)}" y2="182" marker-end="url(#arr)"/>'
    + f'<text class="t-s t-bad" x="{x(8500)}" y="202" text-anchor="middle">5 s, then STOP</text>'
    + f'<line class="ln-bad" x1="{x(11000)}" y1="146" x2="{x(11000)}" y2="182"/>'
    + '<line class="ln" x1="100" y1="228" x2="685" y2="228" marker-end="url(#arr)"/>'
    + ticks
    + '<text class="t-s t-m" x="15" y="248">virtual time</text>'
    '</svg>'
)

S1 = """A teammate wired up this transition bus. The notifier sends receipts and is fast. The audit writer needs a full second per row, so they picked `DROP_LATEST`: when the audit writer falls behind, it should drop transitions while the notifier carries on.

```kotlin
val bus = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_LATEST)
backgroundScope.launch { bus.collect { notifier += it } }              // fast
backgroundScope.launch { bus.collect { audit += it; delay(1_000) } }   // 1 s per row
for (transition in 1..6) { bus.emit(transition); delay(10) }
```

```java
// Java equivalent: a Reactor multicast sink; the audit subscriber requests one item, then stalls
Sinks.Many<Integer> bus = Sinks.many().multicast().directAllOrNothing();
bus.asFlux().subscribe(notifier::add);          // fast: unbounded demand
bus.asFlux().subscribe(auditThatRequestsOne);   // slow: request(1), then nothing
for (int t = 1; t <= 6; t++) bus.tryEmitNext(t);
```

Predict what the notifier receives. Here is the output in virtual time, with the other two policies for comparison:

```text
DROP_LATEST   notifier got [1, 2, 3]            audit got [1, 2, 3]
SUSPEND       notifier got [1, 2, 3, 4, 5, 6]   audit got [1, 2, 3, 4, 5, 6]   emit(4), (5), (6) returned at t=1000, 2000, 3000
DROP_OLDEST   notifier got [1, 2, 3, 4, 5, 6]   audit got [1, 5, 6]
```

The notifier lost 4, 5 and 6, and it was never slow. To see why, picture a `MutableSharedFlow` as a radio station that records onto **one tape loop**. The emitter is the DJ, and every subscriber is a playback head on that same tape. There is no queue per subscriber. Old tape can only be cleared behind the slowest head, so the slowest subscriber decides when the tape is full, for everyone.

Walk through it. The audit writer takes 1 and starts its one-second write. Values 2 and 3 go onto the tape, which has room for exactly two (`extraBufferCapacity`). The notifier reads them at once, but that clears nothing, because the audit head still needs them. Value 4 finds the tape full, and the policy decides what happens:

- `SUSPEND`, the default: `emit(4)` waits until the audit writer takes 2, at t=1000. The notifier has nothing new to read, so it waits as well.
- `DROP_LATEST`: 4 is never recorded. Nobody hears it.
- `DROP_OLDEST`: 4 is recorded over 2, and the audit head is pushed past the part that was overwritten. Only the slow subscriber skips.

So the overflow policy is a choice about every subscriber at once. When no transition may be lost and the notifier must not wait, keep `SUSPEND` and give the slow subscriber a buffer of its own. `bus.buffer(64).collect { ... }` puts a channel between the tape and the slow work (lesson 4 of this track), so the audit head takes values off the tape at once. In the Try it, that version delivers all six to both, and every `emit` returns by t=50. The cushion has a size: once those 64 slots fill, the audit side stops taking from the tape, and everyone waits again."""

S2 = """`emit` is two steps in the source: `if (tryEmit(value)) return`, and only then suspend. So one rule answers both questions, when `emit` waits and when `tryEmit` returns `false`.

1. With no subscribers, every call succeeds. The value goes into the replay cache if `replay > 0`, and nowhere otherwise. `extraBufferCapacity` plays no part: with `replay = 2, extraBufferCapacity = 10`, five emits to nobody leave `replayCache = [4, 5]`.
2. With subscribers, the tape holds `replay + extraBufferCapacity` values, and it is full when the slowest subscriber has that many values it has not taken yet. Then `SUSPEND` makes `tryEmit` return `false` and `emit` wait, while the two drop policies return `true` and drop.

"Taken" has an exact meaning. A subscriber takes a value when it reads it off the tape, before your `collect` lambda runs. A value that a busy subscriber is still working on no longer counts. That is why the audit writer in the first section held only 2 and 3 against the tape, and not 1.

Now the default, `MutableSharedFlow()`, with no replay and no extra buffer. There is no tape at all, so a value can only pass like a **relay baton**. The runner (`emit`) holds it out and lets go once every receiver has a hand on it. `tryEmit` throws the baton without waiting, and it falls. So `tryEmit` returns `false` whenever there is a subscriber, even an idle one, as lesson 8 of the coroutines track said. And `emit` returns the moment the subscriber takes the value, before the subscriber has done anything with it: with 100 ms of work per value, `emit(1)`, `emit(2)` and `emit(3)` return at t=0, 100 and 200.

Here is the rule at work. One subscriber has subscribed and waits, then `tryEmit(1)` to `tryEmit(6)` run back to back (T is `true`, f is `false`):

| Flow | `tryEmit(1..6)` | The subscriber gets |
|---|---|---|
| `MutableSharedFlow()`, no subscriber | T T T T T T | (nobody there) |
| `MutableSharedFlow()` | f f f f f f | nothing |
| `extraBufferCapacity = 2` | T T f f f f | 1, 2 |
| `replay = 2` | T T f f f f | 1, 2 |
| `replay = 1, extraBufferCapacity = 2` | T T T f f f | 1, 2, 3 |
| `extraBufferCapacity = 2, DROP_OLDEST` | T T T T T T | 5, 6 |
| `extraBufferCapacity = 2, DROP_LATEST` | T T T T T T | 1, 2 |

Two rows deserve a second look. While someone is subscribed, `replay = 2` behaves exactly like `extraBufferCapacity = 2`: both are slots on the one tape. And three idle subscribers give the same row as one, because they share the tape.

The tape also explains a subscriber that arrives late. It is like walking into a cinema mid-film: you get the recap (the replay cache), then the live film. You never see the scenes the slow viewer in row 3 is still catching up on. With `replay = 1, extraBufferCapacity = 10`, a subscriber stuck on value 1 while 1 to 5 are emitted works through all five, and a second subscriber that joins after 5 gets only `[5]`."""

S3 = """A `StateFlow` has no tape. It is a notice board with one slot. Two rules follow, and both compare with `equals`.

Pinning an equal sheet does nothing. The setter checks the new value against the current one and returns early when they are equal: no collector wakes up, and the old object stays on the board. After `board.value = Quote("EURUSD", BigDecimal("1.0850"))` on a board that holds an equal quote, `board.value === first` is still `true`. Equality is whatever your type says, so `BigDecimal("1.08500")` counts as a new rate, because `BigDecimal.equals` compares the scale too.

Each reader remembers the last sheet they read. A collector that wakes up reads the slot, and it emits only if the value differs from the one it emitted last. A busy collector skips everything in between, including a value that went away and came back:

```kotlin
val status = MutableStateFlow("AUTHORIZED")
launch { status.collect { log += it; delay(100) } }   // 100 ms of work per value
delay(10); status.value = "CAPTURED"
delay(10); status.value = "AUTHORIZED"
// log is [AUTHORIZED]: the board changed twice, and the busy reader saw nothing new
```

```java
// Java equivalent: Reactor conflates and skips repeats only when you add both operators
Sinks.Many<String> status = Sinks.many().replay().latestOrDefault("AUTHORIZED");
status.asFlux().onBackpressureLatest().distinctUntilChanged().subscribe(busyReader);
status.tryEmitNext("CAPTURED");
status.tryEmitNext("AUTHORIZED");
// busyReader got [AUTHORIZED]; without the two operators it gets all three
```

An audit trail built on a StateFlow loses exactly these transitions. Use it for state, and a SharedFlow for events.

Writes go through compare-and-set. `update { it + 1 }` is a loop: read the value, compute the next one, call `compareAndSet(prev, next)`, and go round again if another writer got in first. With 8 coroutines on `Dispatchers.Default` each adding 1 a hundred thousand times, the value ends at exactly 800,000, and in one run the lambda ran 1,405,098 times. So a side effect inside `update { }`, such as a log line, a metric or a call, runs more than once. Compute inside the lambda and act after it. `compareAndSet` compares with `equals` as well, which gives one odd case: `compareAndSet(11, 11)` on a board that holds 11 returns `true`, changes nothing and wakes nobody. Java's `AtomicReference.compareAndSet` compares references instead, so a fresh `BigDecimal("10")` fails against the stored one.

One counter does not conflate: `subscriptionCount`. It works like a turnstile that prints every click on a paper strip. A subscriber that walks in and straight out still leaves +1 and -1 on the strip. An observer saw `[0, 1, 0]` for such a visitor, where a plain StateFlow set to 1 and back to 0 showed only `[0]`. Sharing is built on this count."""

S4 = """`stateIn` and `shareIn` read like conversions, and each one launches a coroutine. `shareIn(scope, started, replay)` creates a `MutableSharedFlow` with that `replay`, an extra buffer that brings it up to at least 64 slots, and `SUSPEND`. Then it launches one coroutine in `scope` that collects the upstream into it. `stateIn` does the same with a `MutableStateFlow(initialValue)`. Picture a building with one water pump (that coroutine) and a tap for every subscriber. `started` decides when the pump runs. `Eagerly` runs it from opening time, whether anyone is there. `Lazily` lets the first visitor switch it on, and nobody ever switches it off. `WhileSubscribed(5_000)` is a tap on a motion sensor that shuts the water off 5 s after the last person leaves.

Inside, `WhileSubscribed` watches `subscriptionCount`. When the count drops to 0, it waits `stopTimeout` and then sends STOP, which cancels the upstream collection. A subscriber who comes back first cancels that pending wait, so the pump never stopped. The figure shows an exact virtual-time run for an FX poller that emits `run * 100 + i` every second. Dashboard A leaves at 2.5 s and is back at 4 s: it gets 104, from the same run. A leaves again at 6 s, and STOP comes at 11 s. When A returns at 14 s, it gets the stale 111 first, and then 200 from run #2.

Three facts in that run catch people:

- The upstream restarts from the top, because it is a cold flow collected again. Run #2 counts from 200, and a `runningFold` would start over.
- The returning subscriber sees the stale value first. `replayExpirationMillis = 0` resets the StateFlow to its initial value when the pump stops, so the late A gets -1 instead of 111.
- With `WhileSubscribed()`, whose stop timeout is 0, every page reload is a STOP and a new START.

```kotlin
val live: StateFlow<Rate?> = feed.stateIn(
    appScope, SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0), initialValue = null)
```

```java
// Java equivalent: connect with the first subscriber, disconnect 5 s after the last.
// After a disconnect Reactor reconnects with an empty replay cache, so no stale rate is shown.
Flux<Rate> live = feed.replay(1).refCount(1, Duration.ofSeconds(5));
```

Reading `.value` is not a subscription. It is looking at the tap from the doorway, and it doesn't trip the sensor. A request cache built with `Lazily` or `WhileSubscribed` and read only through `.value` never starts: in the Try it, three requests at 3.5 s read `[null, null, null]`, and the feed was fetched 0 times. With `Eagerly` they read the latest rate after 4 fetches.

Two more ways the pump goes wrong. If the upstream throws, the sharing coroutine dies and the exception goes to the scope's handler. Subscribers are not told. They stand at their taps and wait for ever, so put `retry` or `retryWhen` above `shareIn`. And `shareIn` inside a function that each request calls installs a new pump per call: 50 requests that each read one value left 50 sharing coroutines and 500 upstream polls after 10 s. Build the shared flow once, in a field, in a scope that you cancel when the service stops."""

L = {
 "id": "flow-07",
 "title": "Hot flows in depth: SharedFlow, StateFlow and sharing",
 "minutes": 40,
 "goal": "By the end you can predict when a SharedFlow's emit waits, when tryEmit fails and which subscribers lose values under each overflow policy, say what a busy StateFlow collector will see, and pick a SharingStarted strategy from its exact start, stop and restart timeline.",
 "warmup": {
  "q": "A transition bus is `MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = DROP_LATEST)`. A fast notifier and an audit writer that needs 1 s per row both subscribe. Six transitions are emitted 10 ms apart. What does the fast notifier receive?",
  "options": ["All six: `DROP_LATEST` only drops values for the slow subscriber", "1, 2 and 3: values 4, 5 and 6 are dropped for everyone", "1 and 2: the buffer holds two values", "4, 5 and 6: the newest values win"],
  "answer": 1,
  "why": "Every subscriber reads from one shared buffer. The audit writer took 1 and is busy, so 2 and 3 fill the two slots it still needs. When 4 arrives the buffer is full, and `DROP_LATEST` throws 4 away before anyone can read it, notifier included. The same happens to 5 and 6."
 },
 "sections": [
  {
   "h": "One slow subscriber decides what the fast one gets",
   "body": S1,
   "try": {
    "title": "Six transitions, two subscribers, four setups",
    "minutes": 4,
    "steps": [
     "Read `FastAndSlow.kt`. For each of the four setups, predict what the notifier and the audit writer receive, and when each `emit` returns.",
     "Run it.",
     "Change `extraBufferCapacity = 2` to `3` and run again. Predict first: what does the notifier get under `DROP_LATEST`, and which `emit` is the first to wait under `SUSPEND`?"
    ],
    "code": tryit("FastAndSlow.kt", "FastAndSlowJava.java"),
    "expect": "`DROP_LATEST`: both get `[1, 2, 3]`, and every `emit` returns at once. `SUSPEND`: both get all six, but `emit(4)`, `emit(5)` and `emit(6)` return at t=1000, 2000 and 3000, so the fast notifier waits for the audit writer. `DROP_OLDEST`: the notifier gets all six and the audit writer `[1, 5, 6]`. With `bus.buffer(64)` on the audit side, both get all six and every `emit` returns by t=50. With a buffer of 3, `DROP_LATEST` gives both `[1, 2, 3, 4]`, and under `SUSPEND` the first to wait is `emit(5)`, which returns at t=1000. The Java twin shows the same choices with Reactor sinks: `directAllOrNothing()` refuses 2 to 6 for both subscribers (`FAIL_OVERFLOW`), a one-slot `onBackpressureBuffer` holds the notifier at `[1]` while the audit writer is stuck, `directBestEffort()` drops only for the stalled subscriber (a setting Kotlin's SharedFlow doesn't have), and `onBackpressureBuffer(64)` on the audit side frees the notifier."
   },
   "refs": [
    {"title": "MutableSharedFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "The exact rule: count what the slowest subscriber hasn't taken",
   "body": S2,
   "try": {
    "title": "Fill in the tryEmit table",
    "minutes": 5,
    "steps": [
     "Cover the table above. Read `OneTape.kt` and write down the six results and the received values for each line before you run it.",
     "Run it. In the `emit` timeline, compare when each `emit` returns with when the subscriber takes the value.",
     "Run the Java twin. Predict first: a Reactor subscriber that has called `request(1)` is idle too. Does the first `tryEmitNext` succeed?"
    ],
    "code": tryit("OneTape.kt", "OneTapeJava.java"),
    "expect": "The lines match the table, and three subscribers give the same line as one. Each `emit` returns at the same virtual time as `subscriber took`, so it waits for the take, not for the 100 ms of work. The late subscriber gets `[5]` while the first one works through `[1, 2, 3, 4, 5]`. In the Java twin the first `tryEmitNext` to an idle subscriber returns `OK` and the rest `FAIL_OVERFLOW`: a Reactor subscriber announces its demand with `request(1)` before anything is emitted, so the sink can hand one item straight over. With no subscriber Reactor answers `FAIL_ZERO_SUBSCRIBER`, where Kotlin answers `true` and the value goes nowhere. A `replay().limit(2)` sink accepts all six, and the stalled subscriber still gets all six once it asks: the limit only decides what a late subscriber gets, and the late subscriber to `limit(1)` gets `[5]`, as in Kotlin."
   },
   "refs": [
    {"title": "MutableSharedFlow.tryEmit (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/try-emit.html", "kind": "docs"},
    {"title": "SharedFlow.kt at the 1.11.0 tag (the rule is in tryEmitLocked)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/SharedFlow.kt", "kind": "read"}
   ]
  },
  {
   "h": "StateFlow is a notice board with one slot",
   "body": S3,
   "try": {
    "title": "Read the notice board",
    "minutes": 4,
    "steps": [
     "Read `NoticeBoard.kt`. Predict each part: which quotes the collector sees, what the busy collector logs, the three `compareAndSet` results, the final value in part D, and the two lists in part E.",
     "Run it. Part D runs on real threads, so its lambda count changes from run to run.",
     "Run the Java twin, then explain part C: why does Java's `compareAndSet` fail where Kotlin's would succeed?"
    ],
    "code": tryit("NoticeBoard.kt", "NoticeBoardJava.java"),
    "expect": "A: the board still holds the first object after the equal set, and the collector sees `[1.0850, 1.08500]`. B: only `[t=0 AUTHORIZED]`. C: `true`, `false`, `true`, with the value still 11. D: exactly 800000, with the lambda run far more than 800,000 times (1,405,098 in one run here). E: `[0, 1, 0]` against `[0]`. In the Java twin, `BigDecimal.equals` says 1.0850 and 1.08500 differ while `compareTo` says they are equal. The plain replay sink delivers all three statuses, and the one with `onBackpressureLatest().distinctUntilChanged()` delivers only `[AUTHORIZED]`. `AtomicReference.compareAndSet` fails because it compares references, and the expected `BigDecimal` is a different object. `updateAndGet` re-runs its lambda the same way. `currentSubscriberCount()` is a plain number, 0 before and after the visitor, with no record of the visit."
   },
   "refs": [
    {"title": "MutableStateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-state-flow/", "kind": "docs"},
    {"title": "update (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html", "kind": "docs"}
   ]
  },
  {
   "h": "Sharing is one pump and many taps",
   "body": S4,
   "figure": {"svg": FIG, "caption": "WhileSubscribed(5_000): a return within 5 s cancels the stop timer, so run #1 keeps going; after a real stop, the next subscriber gets the stale value and then a new run from the top."},
   "try": {
    "title": "Watch the pump start, stop and restart",
    "minutes": 5,
    "steps": [
     "Read `SharingTimeline.kt`. Before running it, write down when `upstream START` and `STOP` print, and what A gets each time it comes back.",
     "Run it. Then run it with `-Pargs=expire` and with `-Pargs=stop0`, predicting each first.",
     "Run the Java twin, the same script ten times faster on Reactor's `replay(1).refCount`. Compare the lines after A's second return."
    ],
    "code": tryit("SharingTimeline.kt", "SharingTimelineJava.java"),
    "expect": "The default run: START #1 at 0, A gets 104 at 4000 with no restart, STOP #1 at 11000, and at 14000 A gets 111, then START #2 and 200, for 2 starts in all. In the `.value` part, `WhileSubscribed` and `Lazily` read `[null, null, null]` with 0 fetches, and `Eagerly` reads `[1.0854, 1.0854, 1.0854]` after 4 fetches. With `expire`, A gets -1 instead of 111 at 14000. With `stop0`, STOP #1 comes at 2500 and START #2 at 4000, where A gets the stale 102 and then 200; STOP #2 at 6000 and START #3 at 14000 make three starts. The Java twin keeps run #1 through the first return (A gets 104), stops about 500 ms after A leaves the second time, and on the late return prints START #2 and then 200 with no stale value, because Reactor's `replay(1)` begins a fresh cache for the new connection. Its times vary by a few ms."
   },
   "refs": [
    {"title": "shareIn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/share-in.html", "kind": "docs"},
    {"title": "SharingStarted (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A cold flow is a recording: everyone who presses play hears it from the start, on their own player. A hot flow is a radio station: one broadcast, and you hear whatever is on air when you tune in. A `SharedFlow` station records onto one tape loop that every listener's playback head reads, so the slowest listener decides when the tape is full. A `StateFlow` is a notice board with one sheet, and readers only look up when they have a moment. `stateIn` and `shareIn` are the building's water pump: `Eagerly` runs it from opening time, `Lazily` is switched on by the first visitor and never off, and `WhileSubscribed` is a motion sensor with a delay. The analogy breaks at the tape. A real radio station never waits for its slowest listener, and a SharedFlow with `SUSPEND` does exactly that.",
 "in_your_world": "In a payment service the hot shapes map onto different jobs. The FX rates that request handlers read through `.value` are a cache: `stateIn(appScope, Eagerly, null)` with a retry above it, as in the lab, because a cache that waits for a subscriber never fills. The live rates pushed to ops dashboards over server-sent events are a tap: `WhileSubscribed(5_000, replayExpirationMillis = 0)`, so a page reload keeps the provider connection and a dashboard opened at night never shows an old rate. Payment transitions that a notifier and an audit writer both consume are events: a `MutableSharedFlow` with a buffer, `SUSPEND`, a checked `tryEmit` from the Kafka listener thread, and a buffer of its own in front of the slow audit writer. And when a fraud handler and a ledger handler share one poll loop, the tape keeps nothing for a handler that subscribes late (with `replay = 0`): the records polled before it arrived are gone for it, unless the sharing waits for both, as in the worked example.",
 "mistake": "The most common mistake is a request cache copied from dashboard code: `rates.stateIn(appScope, SharingStarted.WhileSubscribed(5_000), null)`, read in every handler with `.value`. Nothing ever collects it, and reading `.value` is not a subscription, so the feed never starts and every handler gets `null`. `Lazily` has the same trap. It passes a unit test that collects the flow to check it, which is the one thing the production code never does. Pick the strategy by who reads. Code that only reads `.value` needs `Eagerly`, or the suspend `stateIn(scope)` at start-up. Code that collects can use `WhileSubscribed`. Then put `retry` above `stateIn`, or the first feed error stops the cache for good while it keeps serving its last rate.",
 "compare": {
  "title": "One FX feed, shared for request handlers and for dashboards",
  "java": {"title": "FxRates.java (Reactor)", "src": "final class FxRates implements AutoCloseable {\n    private final AtomicReference<Rate> latest = new AtomicReference<>();\n    private final Disposable cacheConnection;\n    final Flux<Rate> live;\n\n    FxRates(Flux<Rate> feed) {\n        // for request handlers: connect now, retry after a second, keep the latest in a field\n        this.cacheConnection = feed\n            .retryWhen(Retry.fixedDelay(Long.MAX_VALUE, Duration.ofSeconds(1))\n                .filter(e -> e instanceof IOException))\n            .subscribe(latest::set);\n        // for dashboards: connect with the first, disconnect 5 s after the last\n        this.live = feed.replay(1).refCount(1, Duration.ofSeconds(5));\n    }\n\n    Rate current() { return latest.get(); }\n\n    @Override public void close() { cacheConnection.dispose(); }\n}"},
  "kotlin": {"title": "FxRates.kt (StateFlow)", "src": "class FxRates(feed: Flow<Rate>, scope: CoroutineScope) {\n    // for request handlers: .value is not a subscription, so start now\n    val cache: StateFlow<Rate?> = feed\n        .retry { e -> (e is IOException).also { if (it) delay(1_000) } }\n        .stateIn(scope, SharingStarted.Eagerly, null)\n\n    // for dashboards: survive a 5 s reload, then stop and forget the old rate\n    val live: StateFlow<Rate?> = feed\n        .stateIn(scope, SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0), null)\n\n    fun current(): Rate? = cache.value\n}\n// cancelling `scope` stops both"},
  "note": "The Kotlin side needs no `AtomicReference`, because a StateFlow is both the holder and the stream: `.value` reads it synchronously, and collectors get the same value with equality conflation built in. Lifetime differs too. Both Kotlin flows live in `scope`, so cancelling that one scope stops both upstream collections; in Reactor the cache lives as long as its `Disposable`, and the dashboard connection as long as it has subscribers. The two sides also forget differently. After a disconnect, `replay(1).refCount` reconnects with an empty cache, and Kotlin needs `replayExpirationMillis = 0` for the same effect. Errors are where they differ most. In Reactor an error in the feed reaches every subscriber as `onError`. In Kotlin it ends the sharing coroutine, goes to the scope, and leaves the subscribers waiting, which is why the `retry` sits above `stateIn`. Both versions open two connections to the provider, one per view."
 },
 "worked": {
  "title": "Share one poll loop between a fraud handler and a ledger handler",
  "steps": [
   {"say": "A service polls a Kafka-style source and hands every record to two handlers, fraud checks and ledger posting. Polling twice would read every record twice, so the poll loop is shared with `shareIn` and `replay = 0`. As their beans start, the fraud handler subscribes at 250 ms and the ledger handler at 500 ms. Predict what each has received by 800 ms.",
    "code": "var offset = 0\nval records = flow { while (true) { delay(100); emit(\"rec-${offset++}\") } }   // stands in for poll()\nval shared = records.shareIn(appScope, SharingStarted.Eagerly)                 // replay = 0\n// fraud subscribes at t=250, ledger at t=500",
    "lang": "kotlin",
    "alt_code": "// Java equivalent: one connection, multicast to whoever is subscribed when a record arrives\nFlux<String> records = Flux.interval(Duration.ofMillis(100)).map(i -> \"rec-\" + i);\nFlux<String> shared = records.publish().autoConnect(0);   // connect now, like Eagerly\n// fraud subscribes at t=250, ledger at t=500",
    "alt_lang": "java"},
   {"say": "The virtual-time run. With `Eagerly`, `rec-0` and `rec-1` were polled before anyone listened, and the ledger handler also missed everything up to `rec-4`. `WhileSubscribed()` helps the first handler and not the second. With `replay = 0` the tape keeps nothing for a late subscriber.",
    "code": "Eagerly:            fraud=[rec-2, rec-3, rec-4, rec-5, rec-6]  ledger=[rec-5, rec-6]\nWhileSubscribed():  fraud=[rec-0, rec-1, rec-2, rec-3, rec-4]  ledger=[rec-2, rec-3, rec-4]",
    "lang": "text"},
   {"say": "Start the poll only when both handlers are there. `SharingStarted` is a `fun interface` that turns the subscriber count into START and STOP commands, so the gate is one line. In the same run, both handlers now get `[rec-0, rec-1]` by 800 ms.",
    "code": "// 1. a strategy built on subscriptionCount\nval bothHandlers = SharingStarted { count ->\n    count.map { if (it >= 2) SharingCommand.START else SharingCommand.STOP }\n}\n// 2. the same shareIn, gated\nval shared = records.shareIn(appScope, bothHandlers)",
    "lang": "kotlin",
    "alt_code": "// 1. and 2.: connect once two subscribers are there (Reactor's version never disconnects)\nFlux<String> shared = records.publish().autoConnect(2);",
    "alt_lang": "java"},
   {"say": "Self-check: the ledger handler needs 50 ms per record and fraud needs 5 ms. With `shareIn`'s default `SUSPEND`, which one sets the pace of the poll loop, and is that what you want here? (The ledger handler. The tape is full once the slowest handler has 64 records it hasn't taken, and then `emit`, the poll loop, waits. For records that must all be processed, that is the backpressure you want. A drop policy would lose records with no error.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Predict the tape, then share an FX feed two ways",
  "minutes": 15,
  "files": [
   f"{lab}/main/{P}/SharedFlowRule.kt",
   f"{lab}/main/{P}/FxRates.kt",
   f"{lab}/main/{P}/Rate.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l07.*'",
  "steps": [
   "Run the tests. 24 of 25 fail: every `SharedFlowRuleTest` case and five of the six `FxRatesTest` cases.",
   "In `SharedFlowRule.kt`, write `predictTryEmits` from the rule in the second section, without creating a flow. For each row, the test runs a real `MutableSharedFlow` and compares. Then write `predictReceived`.",
   "In `FxRates.kt`, fix `requestCache`. Handlers only read `.value`, so pick the `SharingStarted` that doesn't wait for a subscriber, and add a retry above `stateIn` that waits 1,000 ms after an `IOException`.",
   "Fix `dashboardFeed`: survive a reload within 5 s, stop 5 s after the last dashboard leaves, and reset to `null` when it stops.",
   "Run the tests until all 25 pass. Then read how `FxRatesTest` counts feed starts and stops in virtual time, and why it never calls `advanceUntilIdle()`."
  ],
  "hints": [
   "The rule has three cases: no subscribers, a drop policy, and `SUSPEND`. In the last one the answer depends only on the index of the call and `replay + extraBufferCapacity`.",
   "`predictReceived`: `SUSPEND` and `DROP_LATEST` keep the first values that fit, and `DROP_OLDEST` keeps the last ones.",
   "`retry { e -> ... }` takes a suspending predicate, so it can `delay(1_000)` before it returns `true`. It must sit before `stateIn`: once the sharing coroutine has died, nothing restarts it.",
   "If the late-dashboard test sees the old rate first, you need the second parameter of `WhileSubscribed`."
  ],
  "done_when": "All 25 tests in `SharedFlowRuleTest` and `FxRatesTest` pass."
 },
 "drill": {
  "title": "A transition bus, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `class TransitionBus` with `fun publish(t: Transition): Boolean`, called from a non-suspending Kafka listener callback, and `val events: SharedFlow<Transition>`. A burst of up to 64 transitions must not be refused, no transition may be dropped by a policy, and a slow audit subscriber must not hold back a fast notifier. Write the audit subscriber's collection too, and say in a comment when `publish` returns `false`.",
  "answer": {"lang": "kotlin", "src": "class TransitionBus {\n    private val bus = MutableSharedFlow<Transition>(extraBufferCapacity = 64)   // SUSPEND, the default\n    val events: SharedFlow<Transition> = bus.asSharedFlow()\n\n    // false only when some subscriber already has 64 transitions it hasn't taken;\n    // the listener must not acknowledge the record then. With no subscriber it is\n    // always true, and the transition goes nowhere.\n    fun publish(t: Transition): Boolean = bus.tryEmit(t)\n}\n\n// the audit writer takes values off the shared buffer at once, into a channel of its own\nsuspend fun auditAll(bus: TransitionBus, repo: AuditRepository) =\n    bus.events.buffer(1_000).collect { repo.write(it) }",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a buffered multicast sink, and a buffer of its own on the audit side\nclass TransitionBus {\n    private final Sinks.Many<Transition> bus = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    Flux<Transition> events() { return bus.asFlux(); }\n\n    // false when the buffer is full (FAIL_OVERFLOW); synchronized because a Reactor sink\n    // refuses concurrent emits with FAIL_NON_SERIALIZED\n    synchronized boolean publish(Transition t) { return bus.tryEmitNext(t).isSuccess(); }\n}\n\nDisposable auditAll(TransitionBus bus, AuditRepository repo) {\n    return bus.events()\n        .onBackpressureBuffer(1_000)\n        .publishOn(Schedulers.boundedElastic())\n        .subscribe(repo::write);\n}"}}
 },
 "recap": [
  "A `MutableSharedFlow` is one buffer of `replay + extraBufferCapacity` slots shared by every subscriber. It is full when the slowest subscriber has that many values it hasn't taken, and a subscriber takes a value before its `collect` lambda runs.",
  "When it is full, `SUSPEND` makes `emit` wait and `tryEmit` return `false`, `DROP_LATEST` drops the new value for everyone, and `DROP_OLDEST` makes only the slow subscriber skip. With no subscribers nothing ever waits.",
  "The default `MutableSharedFlow()` has no buffer: a value passes like a relay baton, so `tryEmit` fails whenever anyone is subscribed, and `emit` returns once every subscriber has taken the value. A late subscriber gets the replay cache, then live values.",
  "A StateFlow compares with `equals` when you set it and again in each collector. A busy collector sees only the latest value, so A, B, A while it is busy shows nothing. `update { }` may run its lambda many times.",
  "`shareIn` and `stateIn` launch one coroutine in your scope. `WhileSubscribed(5_000)` survives a return within 5 s; after a stop the upstream restarts from the top, behind the stale value unless `replayExpirationMillis = 0`.",
  "Reading `.value` is not a subscription, an upstream failure leaves subscribers waiting, and `shareIn` per call leaks a coroutine per call. Use `Eagerly` for caches, `retry` above the share, and one shared flow per service."
 ],
 "quiz": [
  {"q": "Three subscribers have subscribed to `MutableSharedFlow<Int>(replay = 1, extraBufferCapacity = 2)` and are waiting. Code calls `tryEmit(1)` to `tryEmit(5)` back to back, so no subscriber runs in between. What do the five calls return?",
   "options": ["true, true, true, false, false", "true five times: replay keeps values, so the flow never refuses one", "true, true, false, false, false: only `extraBufferCapacity` counts", "true five times: each subscriber has its own three slots, nine in all"],
   "answer": 0,
   "why": "The buffer has `replay + extraBufferCapacity` = 3 slots, and all three subscribers share them. None of them can take a value between the calls, so the fourth call finds the slowest subscriber with 3 untaken values, and `SUSPEND` refuses it. While anyone is subscribed, replay slots are ordinary buffer slots, and there is no queue per subscriber."},
  {"q": "A payment's `StateFlow<Status>` goes CAPTURED, then REFUND_PENDING, then CAPTURED again within 5 ms, while its only collector is inside a 50 ms database write that started after it got CAPTURED. What does the collector get when the write finishes?",
   "options": ["REFUND_PENDING, then CAPTURED", "CAPTURED a second time", "Nothing new: the current value equals the last one it got", "REFUND_PENDING only"],
   "answer": 2,
   "why": "A waking collector reads the one slot and emits only if the value differs from the one it emitted last. The slot holds CAPTURED, equal to what it last saw, so nothing is emitted. If every transition matters, the stream should be a SharedFlow with a buffer."},
  {"q": "An SSE endpoint shares an FX feed with ops dashboards. A page reload must not reconnect to the provider, and a dashboard opened after the feed has stopped must never show the old rate. Which `started` fits `stateIn(scope, started, null)`?",
   "options": ["`SharingStarted.Eagerly`", "`SharingStarted.Lazily`", "`SharingStarted.WhileSubscribed(5_000)`", "`SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0)`"],
   "answer": 3,
   "why": "The 5 s stop timeout covers the reload: a subscriber that comes back cancels the pending stop. The second parameter resets the StateFlow to `null` when the feed stops, so a later dashboard sees `null`, then a fresh rate. Plain `WhileSubscribed(5_000)` shows the stale rate first, and `Eagerly` and `Lazily` never stop at all."},
  {"q": "`prices.shareIn(appScope, SharingStarted.Eagerly, replay = 1)` has two subscribers. The upstream sends two prices, then throws `IOException(\"feed reset\")`. What happens next?",
   "options": ["Both subscribers' `collect` calls throw the `IOException`", "The sharing coroutine fails, the scope's handler gets the exception, and the subscribers keep waiting with no error", "`shareIn` restarts the upstream on its own", "Both subscribers' `collect` calls return normally"],
   "answer": 1,
   "why": "The upstream runs in the sharing coroutine, not in the subscribers. Its exception ends that coroutine and goes to the scope, and the subscribers are never told: in the measured run the subscriber had `[1, 2]` and was still waiting a second later. Put `retry` or `retryWhen` above `shareIn`."},
  {"q": "From lesson 4 of this track: `postings.buffer(10).collect { ... }`, and the collector is stuck on its first posting. How many of the producer's `emit` calls have returned?",
   "options": ["10", "11", "1", "64"],
   "answer": 1,
   "why": "Ten postings wait in the buffer and one is in the collector's hands, so 11 calls returned and the 12th is suspended. `shareIn` follows the same arithmetic: with its default 64-slot buffer, the upstream ran 65 emits ahead of a stuck subscriber.",
   "from": "flow-04"}
 ],
 "flashcards": [
  {"front": "Default `MutableSharedFlow()` with one idle subscriber: what does `tryEmit` return?", "back": "`false`. There is no buffer, so a value can only pass from a suspended `emit` to a subscriber taking it (a rendezvous). With no subscriber at all it returns `true` and the value goes nowhere."},
  {"front": "When is a MutableSharedFlow's buffer full?", "back": "When the slowest subscriber has `replay + extraBufferCapacity` values it hasn't taken yet. With no subscribers it is never full."},
  {"front": "One subscriber stalls under `DROP_LATEST`. Does the fast subscriber lose values too?", "back": "Yes. The dropped value was never stored, so nobody gets it. Only `DROP_OLDEST` limits the skipping to the slow subscriber."},
  {"front": "What does a subscriber that joins a SharedFlow late receive?", "back": "The replay cache, then live values. Never the backlog that slower subscribers are still working through."},
  {"front": "A StateFlow goes A, then B, then A while its collector is busy. What does the collector see when it is free?", "back": "Nothing new. It reads the current value (A), which equals the last one it emitted, so it emits nothing."},
  {"front": "Does reading `stateFlow.value` start a `Lazily` or `WhileSubscribed` upstream?", "back": "No. `.value` is not a subscription. A cache that is only read through `.value` needs `Eagerly` (or the suspend `stateIn(scope)`)."},
  {"front": "`WhileSubscribed(5_000)`: the last subscriber leaves and a new one arrives 2 s later. Does the upstream restart?", "back": "No: the pending stop is cancelled and the same run continues. After more than 5 s it restarts from the top, and the newcomer first sees the stale value unless `replayExpirationMillis = 0`."}
 ],
 "terms": [
  {"term": "Hot flow", "plain": "A flow that runs whether or not anyone collects it, and shares what it produces with whoever is subscribed. SharedFlow and StateFlow are hot."},
  {"term": "Shared buffer", "plain": "The one array of `replay + extraBufferCapacity` slots that every subscriber of a MutableSharedFlow reads from, each at its own position. There is no queue per subscriber."},
  {"term": "Rendezvous", "plain": "A hand-over with no buffer: the value passes only while the sender waits and the receiver takes it. The default `MutableSharedFlow()` works this way."},
  {"term": "Taking a value", "plain": "The moment a subscriber reads a value off the shared buffer, before its `collect` lambda runs. Only values not yet taken count against the buffer."},
  {"term": "Equality conflation", "plain": "StateFlow ignores a set that equals the current value, and a waking collector skips a value equal to the last one it emitted."},
  {"term": "Sharing coroutine", "plain": "The one coroutine that `shareIn` or `stateIn` launches in your scope to collect the upstream. It lives as long as the scope, whatever the subscribers do."},
  {"term": "Stop timeout", "plain": "How long `WhileSubscribed` waits after the last subscriber leaves before it cancels the upstream. A subscriber who returns sooner cancels the stop."}
 ],
 "explain_back": {
  "prompt": "A teammate asks two things: why did the fast notifier lose transitions under `DROP_LATEST` when only the audit writer was slow, and why does `tryEmit` on a default `MutableSharedFlow()` fail while the subscriber is idle? Answer both with the tape model, in a few sentences.",
  "answer": "A MutableSharedFlow keeps one buffer of replay + extraBufferCapacity values, and every subscriber reads it at its own position. A value can only be cleared once the slowest subscriber has taken it, so the slowest subscriber decides when the buffer is full, for everyone. Under DROP_LATEST a value that finds the buffer full is never stored, so the fast notifier never sees it either. The default flow has no buffer at all. A value can only pass from an emit that is suspended and waiting to a subscriber that takes it, like a relay baton. tryEmit can't wait, so with any subscriber present it returns false, idle or not. With no subscriber it returns true, and the value goes nowhere."
 },
 "deeper": {
  "minutes": 10,
  "body": "The internals, for a curious day. The field names here are private and may change in any release, so don't build on them.\n\nEvery collector of a shared flow gets a slot object from an array that starts at size 2 and doubles when full: 2 for one or two subscribers, 4 for three or four, 8 for five. A SharedFlow slot holds the index of the next value its collector will read, plus that collector's suspended continuation. The tape is a ring buffer, also allocated lazily and doubled when needed, and it holds the buffered values followed by the suspended `emit` calls as placeholder objects. Its start, `head`, is the smaller of the slowest collector's index and the start of the replay cache. When the slowest collector moves on, `head` moves, the old cells are cleared, and waiting emitters are resumed as their values move onto the tape. Every change happens under one lock, and the coroutines to resume are collected and resumed after the lock is released. The KDoc puts the cost of an emit at O(N) in the number of subscribers.\n\nA StateFlow slot is one atomic field: free, waiting, pending, or a suspended continuation. An update marks every slot pending and copies nothing, which is why the KDoc calls StateFlow allocation-free. Concurrent updates use a sequence number that is odd while an update is being delivered. A second writer that arrives in the middle only bumps it, and the first writer loops round to deliver the newest value.\n\nTwo APIs in this area are experimental in 1.11.0 and need `@OptIn(ExperimentalCoroutinesApi::class)`. `resetReplayCache()` empties the replay cache for new subscribers, while existing ones keep what they had; on a `MutableStateFlow` it throws `UnsupportedOperationException: MutableStateFlow.resetReplayCache is not supported`. `SharedFlow.asFlow()`, new in 1.11.0, hides the hot type from callers.\n\nThe suspend overload `stateIn(scope)` has no `started`. It launches the upstream in `scope`, suspends until the first value, and returns a StateFlow holding it: in one run, a config flow whose first value took 300 ms made `stateIn` return at t=300. That fits a config value loaded at start-up. An empty upstream throws `NoSuchElementException: Flow is empty`. An upstream that fails before its first value rethrows to the caller and also cancels the scope you passed, so choose that scope knowing it goes down with a failed load."
 },
 "sources": [
  {"title": "MutableSharedFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow.html"},
  {"title": "StateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/"},
  {"title": "SharingStarted.WhileSubscribed (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/-companion/-while-subscribed.html"},
  {"title": "SharedFlow.kt at the 1.11.0 tag", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/SharedFlow.kt"},
  {"title": "Asynchronous Flow (Kotlin docs), including hot flows", "url": "https://kotlinlang.org/docs/coroutines-flow.html"}
 ]
}

out = ROOT / "content/lessons/flow-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
