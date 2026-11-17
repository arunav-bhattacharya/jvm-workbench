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


# ---- the figure: WhileSubscribed(5_000) as a cook who stops 5 s after the last diner leaves ----
def x(ms):
    return round(100 + ms * 0.03625, 1)


def bar(cls, a, b, y, h=28):
    return f'<rect class="{cls}" x="{x(a)}" y="{y}" width="{round(x(b) - x(a), 1)}" height="{h}" rx="8"/>'


ticks = ""
for ms, label in [(0, "0"), (2500, "2.5 s"), (4000, "4 s"), (6000, "6 s"), (11000, "11 s"), (14000, "14 s")]:
    ticks += f'<line class="ln" x1="{x(ms)}" y1="224" x2="{x(ms)}" y2="232"/><text class="t-s t-m" x="{x(ms)}" y="248" text-anchor="middle">{label}</text>'

FIG = (
    '<svg viewBox="0 0 700 270" role="img" aria-label="Timeline of stateIn with WhileSubscribed 5000. Screen A is subscribed from 0 to 2.5 s, '
    'from 4 s to 6 s and again from 14 s. The upstream run 1 lasts from 0 to 11 s: the stop timer that started at 2.5 s was cancelled when A came back at 4 s, '
    'and the timer that started at 6 s ran for 5 s and stopped the upstream at 11 s. At 4 s A gets 104 from the same run. At 14 s A first gets the stale 111, '
    'then run 2 starts and sends 200.">'
    '<text class="t-s t-code" x="15" y="22">stateIn(scope, WhileSubscribed(5_000), initialValue = -1)</text>'
    '<text class="t-s t-m" x="15" y="76">screen A</text>'
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

OPENING = """The busy house from the coroutines track has two ways to tell people things. In the hall hangs the menu board, which always shows the latest choice. In the kitchen hangs the house bell, which the cook rings for each announcement: soup's ready, the bread is here, clear the table. Tonight the bell has a small slate beside it, and the cook chalks each announcement on it, so that a listener who was busy can catch up. Two people listen: the waiter, who is quick, and the diary keeper, who copies every announcement into the kitchen diary by hand.

The diary keeper falls behind, and the waiter starts missing announcements, though he was never slow at all. The easy trap is to picture a slate for each listener.

In Errors, completion, retries and timeouts, every collector cooked its own recipe. Hot flows share. In this lesson, we'll find who decides when the slate is full, write the exact rule for `emit` and `tryEmit`, read the menu board closely, and share one cooking session among many diners. Before we start, make a guess, and keep it in mind."""

S1 = r"""A cold flow is a recipe card: every collector, the code that calls `collect` to receive its values, cooks it again from the top. A **hot flow** runs whether or not anyone collects it, and shares each value with whoever is listening at that moment. A `MutableSharedFlow` is a hot flow that you send values into by hand with `emit`, and it is the house bell. Each collector of a hot flow is a subscriber.

A helper wired up the bell like this, with one coroutine (a light piece of work that can pause without holding a thread) per listener. The waiter is quick. The diary keeper needs a full second per line, so the helper picked `DROP_LATEST`: when the diary keeper falls behind, the bell should drop announcements while the waiter carries on.

```kotlin
val bell = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_LATEST)
backgroundScope.launch { bell.collect { waiter += it } }                // quick
backgroundScope.launch { bell.collect { diary += it; delay(1_000) } }   // 1 s per line
for (announcement in 1..6) { bell.emit(announcement); delay(10) }
```

```java
// Java equivalent: a Reactor multicast sink; the diary subscriber requests one item, then stalls
Sinks.Many<Integer> bell = Sinks.many().multicast().directAllOrNothing();
bell.asFlux().subscribe(waiter::add);          // quick: unbounded demand
bell.asFlux().subscribe(diaryThatRequestsOne); // slow: request(1), then nothing
for (int a = 1; a <= 6; a++) bell.tryEmitNext(a);
```

`extraBufferCapacity = 2` gives the slate room for two announcements, and `onBufferOverflow` says what to do when it is full. Predict what the waiter receives. Here is the output in virtual time, the fake clock of `runTest` that skips over waits, with the other two choices for comparison:

```text
DROP_LATEST   waiter got [1, 2, 3]            diary got [1, 2, 3]
SUSPEND       waiter got [1, 2, 3, 4, 5, 6]   diary got [1, 2, 3, 4, 5, 6]   emit(4), (5), (6) returned at t=1000, 2000, 3000
DROP_OLDEST   waiter got [1, 2, 3, 4, 5, 6]   diary got [1, 5, 6]
```

The waiter lost 4, 5 and 6, and he was never slow. To see why, look at the slate. There is **one slate** beside the bell, and every subscriber reads it at their own pace, keeping their place with a finger. A line can be wiped only when every listener has read it. So the slowest listener decides when the slate is full, for everyone. There is no slate per listener.

Walk through it. The diary keeper takes 1 and starts a line that takes a second. Announcements 2 and 3 go onto the slate, which has room for exactly two. The waiter reads them at once, but that wipes nothing, because the diary keeper still needs them. Announcement 4 finds the slate full, and the overflow policy, what a full buffer does with a new value, decides what happens:

- `SUSPEND`, the default: `emit(4)` waits until the diary keeper takes 2, at t=1000. The waiter has nothing new to read, so he waits as well.
- `DROP_LATEST`: 4 is never chalked up. Nobody hears it, the waiter included.
- `DROP_OLDEST`: 4 is chalked over 2, and the diary keeper's finger is pushed past the wiped line. Only the slow listener skips.

That makes the overflow policy a choice about every subscriber at once. When no announcement may be lost and the waiter must not wait, keep `SUSPEND` and give the slow listener a shelf of its own. `bell.buffer(64).collect { ... }` puts a channel, a queue between coroutines, between the slate and the slow work (the shelf from Buffering), so the diary keeper copies each line off the slate at once. In the Try it, that version delivers all six to both, and every `emit` returns by t=50. The shelf has a size: once its 64 spots fill, the diary keeper stops taking from the slate, and everyone waits again.

**A SharedFlow has one buffer for all its subscribers. Give a slow subscriber a buffer of its own.**

The picture breaks at the cook's hand. A real cook would just ring louder and carry on. With `SUSPEND`, she stands with the chalk raised until the slowest listener has read a line. The exact rule behind all this is short enough to fit in two lines, and it also says when `tryEmit` answers no."""

S2 = r"""`emit` is two steps in the source: `if (tryEmit(value)) return`, and only then suspend. `tryEmit` is the version that never waits: it returns `true` if it handled the value, and `false` if it would have had to wait. So one rule answers both questions, when `emit` waits and when `tryEmit` says no.

1. With no subscribers, every call succeeds. The value goes into the **replay cache** if `replay > 0`, the last few values kept for subscribers who arrive later, and nowhere otherwise. `extraBufferCapacity` plays no part: with `replay = 2, extraBufferCapacity = 10`, five emits to nobody leave `replayCache = [4, 5]`.
2. With subscribers, the slate holds `replay + extraBufferCapacity` values, and it is full when the slowest subscriber has that many values it has not taken yet. Then `SUSPEND` makes `tryEmit` return `false` and `emit` wait, while the two drop policies return `true` and drop.

"Taken" has an exact meaning. A subscriber takes a value when it reads it off the slate, before your `collect` lambda runs. A value that a busy subscriber is still working on no longer counts. That is why the diary keeper held only 2 and 3 against the slate in the first section, and not 1.

Now the default, `MutableSharedFlow()`, with no replay and no extra buffer. There is no slate at all, so a value can only pass hand to hand. That is a **rendezvous**, the hand-over from Buffering where both hands must meet: `emit` holds the note out until every listener has a hand on it. `tryEmit` can't wait, so it lets go of the note, and the note falls. It therefore returns `false` whenever there is a subscriber, even an idle one, as lesson 8 of the coroutines track said. And `emit` returns the moment the subscriber takes the value, before the subscriber has done anything with it: with 100 ms of work per value, `emit(1)`, `emit(2)` and `emit(3)` return at t=0, 100 and 200.

Here is the rule at work. One subscriber has subscribed and waits, and then `tryEmit(1)` to `tryEmit(6)` run back to back (T is `true`, f is `false`):

| Flow | `tryEmit(1..6)` | The subscriber gets |
|---|---|---|
| `MutableSharedFlow()`, no subscriber | T T T T T T | (nobody there) |
| `MutableSharedFlow()` | f f f f f f | nothing |
| `extraBufferCapacity = 2` | T T f f f f | 1, 2 |
| `replay = 2` | T T f f f f | 1, 2 |
| `replay = 1, extraBufferCapacity = 2` | T T T f f f | 1, 2, 3 |
| `extraBufferCapacity = 2, DROP_OLDEST` | T T T T T T | 5, 6 |
| `extraBufferCapacity = 2, DROP_LATEST` | T T T T T T | 1, 2 |

Two rows deserve a second look. While someone is subscribed, `replay = 2` behaves exactly like `extraBufferCapacity = 2`: both are lines on the one slate. And three idle subscribers give the same row as one, because they share the slate.

The slate also explains a subscriber who arrives late. Someone who walks into the kitchen late reads the lines kept for latecomers, the replay cache, and then hears new announcements. They never see the lines that the slow diary keeper is still working through. With `replay = 1, extraBufferCapacity = 10`, a subscriber stuck on value 1 while 1 to 5 are emitted works through all five, and a second subscriber who joins after 5 gets only `[5]`.

**Count what the slowest subscriber hasn't taken. That number decides every emit.**

Check yourself: with `extraBufferCapacity = 3`, `SUSPEND` and one waiting subscriber, which call is the first `tryEmit` to return `false`? The bell keeps every line until the slowest reader is done. The menu board keeps one."""

S3 = r"""A **StateFlow** is a hot flow that always holds exactly one current value, `.value`. Setting it replaces the old value, and collectors get the new one. It is the menu board in the hall: one slot. Two rules follow, and both compare with `equals`, the type's own idea of "the same".

Pinning up an equal card does nothing. The setter checks the new value against the current one and returns early when they are equal: no collector wakes up, and the old object stays on the board. After `board.value = MenuItem("soup of the day", BigDecimal("4.50"))` on a board that holds an equal item, `board.value === first` is still `true`. Equality is whatever your type says, so `BigDecimal("4.500")` counts as a new price, because `BigDecimal.equals` compares the number of decimal places too.

Each reader remembers the last card they read. A collector that wakes up reads the slot, and it emits only if the value differs from the one it emitted last. A busy collector skips everything in between, even a value that went away and came back:

```kotlin
val soup = MutableStateFlow("tomato")
launch { soup.collect { log += it; delay(100) } }   // 100 ms of work per value
delay(10); soup.value = "leek"
delay(10); soup.value = "tomato"
// log is [tomato]: the board changed twice, and the busy reader saw nothing new
```

```java
// Java equivalent: Reactor skips repeats and in-between values only when you add both operators
Sinks.Many<String> soup = Sinks.many().replay().latestOrDefault("tomato");
soup.asFlux().onBackpressureLatest().distinctUntilChanged().subscribe(busyReader);
soup.tryEmitNext("leek");
soup.tryEmitNext("tomato");
// busyReader got [tomato]; without the two operators it gets all three
```

The busy reader looked up, saw tomato, and concluded that nothing had happened. As far as the board knows, nothing had. A diary built on a StateFlow loses exactly these changes. Use a StateFlow for state, and a SharedFlow for events.

Writes go through **compare-and-set**, an update that succeeds only if nobody changed the value since you read it. `update { it + 1 }` is a loop: read the value, compute the next one, call `compareAndSet(prev, next)`, and go round again if another writer got in first. With 8 coroutines on `Dispatchers.Default`, which runs them on real threads, one per core, each adding 1 a hundred thousand times, the value ends at exactly 800,000, and the lambda ran more than that: 807,072 times in one run here, 1,405,098 in another. Any side effect inside `update { }`, such as a log line or a call, can run more than once. Compute inside the lambda and act after it.

`compareAndSet` compares with `equals` as well, which gives one odd case: `compareAndSet(11, 11)` on a board that holds 11 returns `true`, changes nothing and wakes nobody. Java's `AtomicReference.compareAndSet` compares references instead, so a fresh `BigDecimal("10")` fails against the stored one.

One counter does not skip anything: `subscriptionCount`, the number of current subscribers, as a StateFlow of its own. It works like a tally sheet by the hall door that marks every person coming and going. A subscriber that walks in and straight out still leaves +1 and -1 on the sheet. An observer saw `[0, 1, 0]` for such a visitor, where a plain StateFlow set to 1 and back to 0 showed only `[0]`. Sharing is built on this count.

**A StateFlow keeps state, not history. When every change counts, use a SharedFlow.**

Check yourself: a busy collector last saw tomato, and the soup goes leek, then pea. What does it see when it's free? Both kinds of hot flow so far were filled by hand. Most hot flows in real programs are a cold flow, shared."""

S4 = r"""`stateIn` and `shareIn` read like conversions, but each one launches a coroutine. `shareIn(scope, started, replay)` creates a `MutableSharedFlow` with that `replay`, an extra buffer that brings it up to at least 64 slots, and `SUSPEND`. Then it launches one coroutine in `scope`, the owner that cancels all its coroutines when it is cancelled, and that coroutine collects the upstream, the cold flow above it, into the shared flow. `stateIn` does the same with a `MutableStateFlow(initialValue)`.

Picture one cook and many diners. The **sharing coroutine** is the cook: she cooks the recipe once and serves every diner at the table. `started`, a `SharingStarted` value, decides when she works. `Eagerly` starts her at opening time, diners or not. `Lazily` lets the first diner get her started, and she never stops. `WhileSubscribed(5_000)` keeps her cooking while anyone is at the table and stops her 5 s after the last diner leaves, in case someone just stepped out.

Inside, `WhileSubscribed` watches `subscriptionCount`. When the count drops to 0, it waits for the **stop timeout** and then sends STOP, which cancels the upstream collection. A subscriber who comes back first cancels that pending wait, so the cook never stopped. The figure shows an exact virtual-time run for the oven thermometer, which sends `run * 100 + i` every second (made-up readings that show which run sent them). Screen A switches off at 2.5 s and is back at 4 s: it gets 104, from the same run. A goes off again at 6 s, and STOP comes at 11 s. When A comes back at 14 s, it gets the stale 111 first, and then 200 from run #2.

Three facts in that run catch people out:

- The upstream restarts from the top, because it is a cold flow collected again. Run #2 counts from 200, and a running total built with `runningFold` would start over.
- The returning subscriber sees the stale value first. `replayExpirationMillis = 0` resets the StateFlow to its initial value when the cook stops, so the returning A gets -1 instead of 111.
- With `WhileSubscribed()`, whose stop timeout is 0, every flicker of a screen is a STOP and a new START.

```kotlin
val live: StateFlow<Reading?> = thermometer.stateIn(
    houseScope, SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0), initialValue = null)
```

```java
// Java equivalent: connect with the first subscriber, disconnect 5 s after the last.
// After a disconnect Reactor reconnects with an empty replay cache, so no stale reading is shown.
Flux<Reading> live = thermometer.replay(1).refCount(1, Duration.ofSeconds(5));
```

Reading `.value` is not a subscription. It is glancing at the hall board from the doorway, and it doesn't call the cook. A hall board built with `Lazily` or `WhileSubscribed` and read only through `.value` never starts: in the Try it, three glances at 3.5 s read `[null, null, null]`, and the thermometer was read 0 times. With `Eagerly` they read `[180, 180, 180]` after 4 readings.

**Pick `started` by who reads. Code that only reads `.value` needs `Eagerly`.**

Two more ways the sharing goes wrong. If the upstream throws, the sharing coroutine dies, and the exception goes to the scope's handler. The subscribers are not told. They sit at the table and wait for ever, so put `retry` or `retryWhen` above `shareIn`, as in the last lesson. And `shareIn` inside a function that each request calls starts a new cook per call: 50 calls that each read one value left 50 sharing coroutines and 500 upstream reads after 10 s. Fifty cooks, each one cooking for a diner who left after the first bite. Build the shared flow once, in a field, in a scope that you cancel when the program stops.

Check yourself: a screen goes off at 10 s and comes back at 13 s under `WhileSubscribed(5_000)`. Does the thermometer restart? Everything here happens inside one Kotlin program, where every value arrives through `emit`. The outside world calls you back instead."""

CLOSING = """We started with a bell, a slate, a quick waiter and a slow diary keeper. A SharedFlow has one slate for every subscriber, so the slowest one sets the pace or the losses, and the default flow has no slate at all. A StateFlow is the menu board: one slot, compared with `equals`. `shareIn` and `stateIn` give a shared cooking session one cook, started and stopped by `SharingStarted`.

Now search your own code for `stateIn(` and check who reads the result. If nothing collects it, `WhileSubscribed` never starts.

Next, we'll connect flows to the world outside. How do you turn an old probe that calls you back into a flow, without losing readings or leaving its listener behind?"""

L = {
 "id": "flow-07",
 "title": "Hot flows in depth: SharedFlow, StateFlow and sharing",
 "minutes": 40,
 "goal": "By the end you can predict when a SharedFlow's emit waits, when tryEmit fails and which subscribers lose values under each overflow policy, say what a busy StateFlow collector will see, and pick a SharingStarted strategy from its exact start, stop and restart timeline.",
 "opening": OPENING,
 "warmup": {
  "q": "The house bell is `MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = DROP_LATEST)`. A quick waiter and a diary keeper who needs 1 s per line both subscribe. Six announcements are emitted 10 ms apart. What does the quick waiter receive?",
  "options": ["All six: `DROP_LATEST` only drops values for the slow subscriber", "1, 2 and 3: announcements 4, 5 and 6 are dropped for everyone", "1 and 2: the buffer holds two values", "4, 5 and 6: the newest values win"],
  "answer": 1,
  "why": "Every subscriber reads from one shared buffer. The diary keeper took 1 and is busy, so 2 and 3 fill the two slots it still needs. When 4 arrives the buffer is full, and `DROP_LATEST` throws 4 away before anyone can read it, the waiter included. The same happens to 5 and 6."
 },
 "sections": [
  {
   "h": "One slow subscriber decides what the quick one gets",
   "body": S1,
   "try": {
    "title": "Six announcements, two listeners, four setups",
    "minutes": 4,
    "steps": [
     "Read `FastAndSlow.kt`. For each of the four setups, predict what the waiter and the diary keeper receive, and when each `emit` returns.",
     "Run it.",
     "Change `extraBufferCapacity = 2` to `3` and run again. Predict first: what does the waiter get under `DROP_LATEST`, and which `emit` is the first to wait under `SUSPEND`?"
    ],
    "code": tryit("FastAndSlow.kt", "FastAndSlowJava.java"),
    "expect": "`DROP_LATEST`: both get `[1, 2, 3]`, and every `emit` returns at once. `SUSPEND`: both get all six, but `emit(4)`, `emit(5)` and `emit(6)` return at t=1000, 2000 and 3000, so the quick waiter waits for the diary keeper. `DROP_OLDEST`: the waiter gets all six and the diary keeper `[1, 5, 6]`. With `bell.buffer(64)` on the diary side, both get all six and every `emit` returns by t=50. With a buffer of 3, `DROP_LATEST` gives both `[1, 2, 3, 4]`, and under `SUSPEND` the first to wait is `emit(5)`, which returns at t=1000. The Java twin shows the same choices with Reactor sinks: `directAllOrNothing()` refuses 2 to 6 for both subscribers (`FAIL_OVERFLOW`), a one-slot `onBackpressureBuffer` holds the waiter at `[1]` while the diary keeper is stuck, `directBestEffort()` drops only for the stalled subscriber (a setting Kotlin's SharedFlow doesn't have), and `onBackpressureBuffer(64)` on the diary side frees the waiter."
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
   "h": "StateFlow is the menu board in the hall: one slot, compared with equals",
   "body": S3,
   "try": {
    "title": "Read the menu board",
    "minutes": 4,
    "steps": [
     "Read `NoticeBoard.kt`. Predict each part: which prices the collector sees, what the busy collector logs, the three `compareAndSet` results, the final value in part D, and the two lists in part E.",
     "Run it. Part D runs on real threads, so its lambda count changes from run to run.",
     "Run the Java twin, then explain part C: why does Java's `compareAndSet` fail where Kotlin's would succeed?"
    ],
    "code": tryit("NoticeBoard.kt", "NoticeBoardJava.java"),
    "expect": "A: the board still holds the first object after the equal set, and the collector sees `[4.50, 4.500]`. B: only `[t=0 tomato]`. C: `true`, `false`, `true`, with the value still 11. D: exactly 800000, with the lambda run more than 800,000 times (807,072 in one run here). E: `[0, 1, 0]` against `[0]`. In the Java twin, `BigDecimal.equals` says 4.50 and 4.500 differ while `compareTo` says they are equal. The plain replay sink delivers all three soups, and the one with `onBackpressureLatest().distinctUntilChanged()` delivers only `[tomato]`. `AtomicReference.compareAndSet` fails because it compares references, and the expected `BigDecimal` is a different object. `updateAndGet` runs its lambda again on a conflict in the same way. `currentSubscriberCount()` is a plain number, 0 before and after the visitor, with no record of the visit."
   },
   "refs": [
    {"title": "MutableStateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-state-flow/", "kind": "docs"},
    {"title": "update (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html", "kind": "docs"}
   ]
  },
  {
   "h": "One cook for many diners: shareIn, stateIn and when the cook starts and stops",
   "body": S4,
   "figure": {"svg": FIG, "caption": "WhileSubscribed(5_000): a return within 5 s cancels the stop timer, so run #1 keeps going; after a real stop, the next subscriber gets the stale value and then a new run from the top."},
   "try": {
    "title": "Watch the cook start, stop and start again",
    "minutes": 5,
    "steps": [
     "Read `SharingTimeline.kt`. Before running it, write down when `upstream START` and `STOP` print, and what A gets each time it comes back.",
     "Run it. Then run it with `-Pargs=expire` and with `-Pargs=stop0`, predicting each first.",
     "Run the Java twin, the same script ten times faster on Reactor's `replay(1).refCount`. Compare the lines after A's second return."
    ],
    "code": tryit("SharingTimeline.kt", "SharingTimelineJava.java"),
    "expect": "The default run: START #1 at 0, A gets 104 at 4000 with no restart, STOP #1 at 11000, and at 14000 A gets 111, then START #2 and 200, for 2 starts in all. In the `.value` part, `WhileSubscribed` and `Lazily` read `[null, null, null]` with 0 readings taken, and `Eagerly` reads `[180, 180, 180]` after 4. With `expire`, A gets -1 instead of 111 at 14000. With `stop0`, STOP #1 comes at 2500 and START #2 at 4000, where A gets the stale 102 and then 200; STOP #2 at 6000 and START #3 at 14000 make three starts. The Java twin keeps run #1 through the first return (A gets 104), stops about 500 ms after A leaves the second time, and on the late return prints START #2 and then 200 with no stale value, because Reactor's `replay(1)` begins a fresh cache for the new connection. Its times vary by a few ms."
   },
   "refs": [
    {"title": "shareIn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/share-in.html", "kind": "docs"},
    {"title": "SharingStarted (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "One oven thermometer, shared for the hall board and for the kitchen screens",
  "java": {"title": "OvenBoard.java (Reactor)", "src": "final class OvenBoard implements AutoCloseable {\n    private final AtomicReference<Reading> latest = new AtomicReference<>();\n    private final Disposable boardConnection;\n    final Flux<Reading> live;\n\n    OvenBoard(Flux<Reading> thermometer) {\n        // for the hall board: connect now, retry after a second, keep the latest in a field\n        this.boardConnection = thermometer\n            .retryWhen(Retry.fixedDelay(Long.MAX_VALUE, Duration.ofSeconds(1))\n                .filter(e -> e instanceof IOException))\n            .subscribe(latest::set);\n        // for the screens: connect with the first, disconnect 5 s after the last\n        this.live = thermometer.replay(1).refCount(1, Duration.ofSeconds(5));\n    }\n\n    Reading current() { return latest.get(); }\n\n    @Override public void close() { boardConnection.dispose(); }\n}"},
  "kotlin": {"title": "OvenBoard.kt (StateFlow)", "src": "class OvenBoard(thermometer: Flow<Reading>, scope: CoroutineScope) {\n    // for the hall board: .value is not a subscription, so start now\n    val board: StateFlow<Reading?> = thermometer\n        .retry { e -> (e is IOException).also { if (it) delay(1_000) } }\n        .stateIn(scope, SharingStarted.Eagerly, null)\n\n    // for the screens: survive a 5 s flicker, then stop and forget the old reading\n    val live: StateFlow<Reading?> = thermometer\n        .stateIn(scope, SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0), null)\n\n    fun current(): Reading? = board.value\n}\n// cancelling `scope` stops both"},
  "note": "The Kotlin side needs no `AtomicReference`, because a StateFlow is both the holder and the stream: `.value` reads it at once, and collectors get the same value with equality checks built in. Lifetime differs too. Both Kotlin flows live in `scope`, so cancelling that one scope stops both upstream collections; in Reactor the board lives as long as its `Disposable`, and the screen connection as long as it has subscribers. The two sides also forget differently. After a disconnect, `replay(1).refCount` reconnects with an empty cache, and Kotlin needs `replayExpirationMillis = 0` for the same effect. Errors are where they differ most. In Reactor an error in the thermometer reaches every subscriber as `onError`. In Kotlin it ends the sharing coroutine, goes to the scope, and leaves the subscribers waiting, which is why the `retry` sits above `stateIn`. Both versions open two connections to the thermometer, one per view."
 },
 "worked": {
  "title": "Share one order rail between the grill and the dessert station",
  "steps": [
   {"say": "Orders arrive on a rail and are read off it one by one. Two stations need every order, the grill and the dessert station. Reading the rail twice would take every ticket twice, so the reading is shared with `shareIn` and `replay = 0`. The grill starts work at 250 ms and the dessert station at 500 ms. Predict what each has received by 800 ms.",
    "code": "var next = 0\nval orders = flow { while (true) { delay(100); emit(\"order-${next++}\") } }   // stands in for reading the rail\nval shared = orders.shareIn(houseScope, SharingStarted.Eagerly)               // replay = 0\n// the grill subscribes at t=250, desserts at t=500",
    "lang": "kotlin",
    "alt_code": "// Java equivalent: one connection, multicast to whoever is subscribed when an order arrives\nFlux<String> orders = Flux.interval(Duration.ofMillis(100)).map(i -> \"order-\" + i);\nFlux<String> shared = orders.publish().autoConnect(0);   // connect now, like Eagerly\n// the grill subscribes at t=250, desserts at t=500",
    "alt_lang": "java"},
   {"say": "The virtual-time run. With `Eagerly`, `order-0` and `order-1` were read before anyone listened, and the dessert station also missed everything up to `order-4`. `WhileSubscribed()` helps the first station and not the second. With `replay = 0`, the slate keeps nothing for a late subscriber.",
    "code": "Eagerly:            grill=[order-2, order-3, order-4, order-5, order-6]  desserts=[order-5, order-6]\nWhileSubscribed():  grill=[order-0, order-1, order-2, order-3, order-4]  desserts=[order-2, order-3, order-4]",
    "lang": "text"},
   {"say": "Start reading only when both stations are there. `SharingStarted` is a `fun interface` that turns the subscriber count into START and STOP commands, so the gate is one line. In the same run, both stations now get `[order-0, order-1]` by 800 ms.",
    "code": "// 1. a strategy built on subscriptionCount\nval bothStations = SharingStarted { count ->\n    count.map { if (it >= 2) SharingCommand.START else SharingCommand.STOP }\n}\n// 2. the same shareIn, gated\nval shared = orders.shareIn(houseScope, bothStations)",
    "lang": "kotlin",
    "alt_code": "// 1. and 2.: connect once two subscribers are there (Reactor's version never disconnects)\nFlux<String> shared = orders.publish().autoConnect(2);",
    "alt_lang": "java"},
   {"say": "Self-check: the dessert station needs 50 ms per order and the grill needs 5 ms. With `shareIn`'s default `SUSPEND`, which one sets the pace of reading the rail, and is that what you want here? (The dessert station. The slate is full once the slowest station has 64 orders it hasn't taken, and then `emit`, the reading, waits. For orders that must all be cooked, that is exactly the waiting you want. A drop policy would lose orders with no error.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Predict the slate, then share the oven thermometer two ways",
  "minutes": 15,
  "files": [
   f"{lab}/main/{P}/SharedFlowRule.kt",
   f"{lab}/main/{P}/OvenBoard.kt",
   f"{lab}/main/{P}/Reading.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l07.*'",
  "steps": [
   "Run the tests. 24 of 25 fail: every `SharedFlowRuleTest` case and five of the six `OvenBoardTest` cases.",
   "In `SharedFlowRule.kt`, write `predictTryEmits` from the rule in the second section, without creating a flow. For each row, the test runs a real `MutableSharedFlow` and compares. Then write `predictReceived`.",
   "In `OvenBoard.kt`, fix `hallBoard`. People only read `.value`, so pick the `SharingStarted` that doesn't wait for a subscriber, and add a retry above `stateIn` that waits 1,000 ms after an `IOException`.",
   "Fix `screenFeed`: survive a flicker within 5 s, stop 5 s after the last screen goes off, and reset to `null` when it stops.",
   "Run the tests until all 25 pass. Then read how `OvenBoardTest` counts feed starts and stops in virtual time, and why it never calls `advanceUntilIdle()`."
  ],
  "hints": [
   "The rule has three cases: no subscribers, a drop policy, and `SUSPEND`. In the last one the answer depends only on the number of the call and `replay + extraBufferCapacity`.",
   "`predictReceived`: `SUSPEND` and `DROP_LATEST` keep the first values that fit, and `DROP_OLDEST` keeps the last ones.",
   "`retry { e -> ... }` takes a suspending predicate, so it can `delay(1_000)` before it returns `true`. It must sit before `stateIn`: once the sharing coroutine has died, nothing restarts it.",
   "If the late-screen test sees the old reading first, you need the second parameter of `WhileSubscribed`."
  ],
  "done_when": "All 25 tests in `SharedFlowRuleTest` and `OvenBoardTest` pass."
 },
 "drill": {
  "title": "A kitchen bell, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `class KitchenBell` with `fun ring(a: Announcement): Boolean`, called from a callback that can't suspend (an old timer's callback, say), and `val announcements: SharedFlow<Announcement>`. A burst of up to 64 announcements must not be refused, no announcement may be dropped by a policy, and a slow diary keeper must not hold back a quick waiter. Write the diary keeper's collection too, and say in a comment when `ring` returns `false`.",
  "answer": {"lang": "kotlin", "src": "class KitchenBell {\n    private val bell = MutableSharedFlow<Announcement>(extraBufferCapacity = 64)   // SUSPEND, the default\n    val announcements: SharedFlow<Announcement> = bell.asSharedFlow()\n\n    // false only when some subscriber already has 64 announcements it hasn't taken;\n    // the caller must not treat the announcement as delivered then. With no subscriber\n    // it is always true, and the announcement goes nowhere.\n    fun ring(a: Announcement): Boolean = bell.tryEmit(a)\n}\n\n// the diary keeper copies values off the shared buffer at once, into a channel of its own\nsuspend fun keepDiary(bell: KitchenBell, diary: Diary) =\n    bell.announcements.buffer(1_000).collect { diary.write(it) }",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a buffered multicast sink, and a buffer of its own on the diary side\nclass KitchenBell {\n    private final Sinks.Many<Announcement> bell = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    Flux<Announcement> announcements() { return bell.asFlux(); }\n\n    // false when the buffer is full (FAIL_OVERFLOW); synchronized because a Reactor sink\n    // refuses concurrent emits with FAIL_NON_SERIALIZED\n    synchronized boolean ring(Announcement a) { return bell.tryEmitNext(a).isSuccess(); }\n}\n\nDisposable keepDiary(KitchenBell bell, Diary diary) {\n    return bell.announcements()\n        .onBackpressureBuffer(1_000)\n        .publishOn(Schedulers.boundedElastic())\n        .subscribe(diary::write);\n}"}}
 },
 "recap": [
  "A `MutableSharedFlow` is one buffer of `replay + extraBufferCapacity` slots shared by every subscriber. It is full when the slowest subscriber has that many values it hasn't taken, and a subscriber takes a value before its `collect` lambda runs.",
  "When it is full, `SUSPEND` makes `emit` wait and `tryEmit` return `false`, `DROP_LATEST` drops the new value for everyone, and `DROP_OLDEST` makes only the slow subscriber skip. With no subscribers nothing ever waits. The default `MutableSharedFlow()` is a rendezvous: `tryEmit` fails whenever anyone is subscribed.",
  "A StateFlow compares with `equals` when you set it and again in each collector. A busy collector sees only the latest value, so A, B, A while it is busy shows nothing. `update { }` may run its lambda many times.",
  "`shareIn` and `stateIn` launch one coroutine in your scope. `WhileSubscribed(5_000)` survives a return within 5 s; after a stop the upstream restarts from the top, behind the stale value unless `replayExpirationMillis = 0`.",
  "Reading `.value` is not a subscription, an upstream failure leaves subscribers waiting, and `shareIn` per call leaks a coroutine per call. Use `Eagerly` for values that are only read, `retry` above the share, and one shared flow per program.",
  "The limit: every value here arrives through `emit` inside Kotlin. A library that calls you back on its own thread needs a bridge, which is the next lesson."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "Three subscribers have subscribed to `MutableSharedFlow<Int>(replay = 1, extraBufferCapacity = 2)` and are waiting. Code calls `tryEmit(1)` to `tryEmit(5)` back to back, so no subscriber runs in between. What do the five calls return?",
   "options": ["true, true, true, false, false", "true five times: replay keeps values, so the flow never refuses one", "true, true, false, false, false: only `extraBufferCapacity` counts", "true five times: each subscriber has its own three slots, nine in all"],
   "answer": 0,
   "why": "The buffer has `replay + extraBufferCapacity` = 3 slots, and all three subscribers share them. None of them can take a value between the calls, so the fourth call finds the slowest subscriber with 3 untaken values, and `SUSPEND` refuses it. While anyone is subscribed, replay slots are ordinary buffer slots, and there is no queue per subscriber."},
  {"q": "A dish's `StateFlow<Status>` goes READY, then SENT_BACK, then READY again within 5 ms, while its only collector is inside a 50 ms write to the kitchen diary that started after it got READY. What does the collector get when the write finishes?",
   "options": ["SENT_BACK, then READY", "READY a second time", "Nothing new: the current value equals the last one it got", "SENT_BACK only"],
   "answer": 2,
   "why": "A waking collector reads the one slot and emits only if the value differs from the one it emitted last. The slot holds READY, equal to what it last saw, so nothing is emitted. If every change matters, the stream should be a SharedFlow with a buffer."},
  {"q": "The kitchen screens share the oven thermometer. A screen that flickers off and on must not reconnect to the thermometer, and a screen switched on after the feed has stopped must never show an old reading. Which `started` fits `stateIn(scope, started, null)`?",
   "options": ["`SharingStarted.Eagerly`", "`SharingStarted.Lazily`", "`SharingStarted.WhileSubscribed(5_000)`", "`SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0)`"],
   "answer": 3,
   "why": "The 5 s stop timeout covers the flicker: a subscriber that comes back cancels the pending stop. The second parameter resets the StateFlow to `null` when the feed stops, so a later screen sees `null`, then a fresh reading. Plain `WhileSubscribed(5_000)` shows the stale reading first, and `Eagerly` and `Lazily` never stop at all."},
  {"q": "`readings.shareIn(houseScope, SharingStarted.Eagerly, replay = 1)` has two subscribers. The upstream sends two readings, then throws `IOException(\"thermometer lost\")`. What happens next?",
   "options": ["Both subscribers' `collect` calls throw the `IOException`", "The sharing coroutine fails, the scope's handler gets the exception, and the subscribers keep waiting with no error", "`shareIn` restarts the upstream on its own", "Both subscribers' `collect` calls return normally"],
   "answer": 1,
   "why": "The upstream runs in the sharing coroutine, not in the subscribers. Its exception ends that coroutine and goes to the scope, and the subscribers are never told: in the measured run the subscriber had `[1, 2]` and was still waiting a second later. Put `retry` or `retryWhen` above `shareIn`."},
  {"q": "From lesson 4 of this track: `plates.buffer(10).collect { ... }`, and the collector is stuck on its first plate. How many of the producer's `emit` calls have returned?",
   "options": ["10", "11", "1", "64"],
   "answer": 1,
   "why": "Ten plates wait in the buffer and one is in the collector's hands, so 11 calls returned and the 12th is suspended. `shareIn` follows the same arithmetic: with its default 64-slot buffer, the upstream ran 65 emits ahead of a stuck subscriber.",
   "from": "flow-04"}
 ],
 "flashcards": [
  {"front": "Default `MutableSharedFlow()` with one idle subscriber: what does `tryEmit` return?", "back": "`false`. There is no buffer, so a value can only pass from a suspended `emit` to a subscriber taking it (a rendezvous). With no subscriber at all it returns `true` and the value goes nowhere."},
  {"front": "When is a MutableSharedFlow's buffer full?", "back": "When the slowest subscriber has `replay + extraBufferCapacity` values it hasn't taken yet. With no subscribers it is never full."},
  {"front": "One subscriber stalls under `DROP_LATEST`. Does the quick subscriber lose values too?", "back": "Yes. The dropped value was never stored, so nobody gets it. Only `DROP_OLDEST` limits the skipping to the slow subscriber."},
  {"front": "What does a subscriber that joins a SharedFlow late receive?", "back": "The replay cache, then live values. Never the backlog that slower subscribers are still working through."},
  {"front": "A StateFlow goes A, then B, then A while its collector is busy. What does the collector see when it is free?", "back": "Nothing new. It reads the current value (A), which equals the last one it emitted, so it emits nothing."},
  {"front": "Does reading `stateFlow.value` start a `Lazily` or `WhileSubscribed` upstream?", "back": "No. `.value` is not a subscription. A value that is only read through `.value` needs `Eagerly` (or the suspend `stateIn(scope)`)."},
  {"front": "`WhileSubscribed(5_000)`: the last subscriber leaves and a new one arrives 2 s later. Does the upstream restart?", "back": "No: the pending stop is cancelled and the same run continues. After more than 5 s it restarts from the top, and the newcomer first sees the stale value unless `replayExpirationMillis = 0`."}
 ],
 "terms": [
  {"term": "Hot flow", "plain": "A flow that runs whether or not anyone collects it, and shares what it produces with whoever is subscribed. SharedFlow and StateFlow are hot."},
  {"term": "Shared buffer", "plain": "The one slate of `replay + extraBufferCapacity` slots that every subscriber of a MutableSharedFlow reads from, each at its own place. There is no queue per subscriber."},
  {"term": "Rendezvous", "plain": "A hand-over with no buffer: the value passes only while the sender waits and the receiver takes it. The default `MutableSharedFlow()` works this way."},
  {"term": "Taking a value", "plain": "The moment a subscriber reads a value off the shared buffer, before its `collect` lambda runs. Only values not yet taken count against the buffer."},
  {"term": "Equality conflation", "plain": "StateFlow ignores a set that equals the current value, and a waking collector skips a value equal to the last one it emitted."},
  {"term": "Sharing coroutine", "plain": "The one coroutine that `shareIn` or `stateIn` launches in your scope to collect the upstream: the cook who serves every diner. It lives as long as the scope, whatever the subscribers do."},
  {"term": "Stop timeout", "plain": "How long `WhileSubscribed` waits after the last subscriber leaves before it cancels the upstream. A subscriber who returns sooner cancels the stop."}
 ],
 "explain_back": {
  "prompt": "A friend asks two things: why did the quick waiter lose announcements under `DROP_LATEST` when only the diary keeper was slow, and why does `tryEmit` on a default `MutableSharedFlow()` fail while the subscriber is idle? Answer both with the slate picture, in a few sentences.",
  "answer": "A MutableSharedFlow keeps one slate of replay + extraBufferCapacity values, and every subscriber reads it at their own place. A line can be wiped only once the slowest subscriber has taken it, so the slowest subscriber decides when the slate is full, for everyone. Under DROP_LATEST a value that finds the slate full is never written down, so the quick waiter never sees it either. The default flow has no slate at all. A value can only pass from an emit that is suspended and waiting to a subscriber that takes it, hand to hand. tryEmit can't wait, so with any subscriber present it returns false, idle or not. With no subscriber it returns true, and the value goes nowhere."
 },
 "deeper": {
  "minutes": 10,
  "body": "The internals, for a curious day. The field names here are private and may change in any release, so don't build on them.\n\nEvery collector of a shared flow gets a slot object from an array that starts at size 2 and doubles when full: 2 for one or two subscribers, 4 for three or four, 8 for five. A SharedFlow slot holds the index of the next value its collector will read, plus that collector's suspended continuation. The slate is a ring buffer, also allocated lazily and doubled when needed, and it holds the buffered values followed by the suspended `emit` calls as placeholder objects. Its start, `head`, is the smaller of the slowest collector's index and the start of the replay cache. When the slowest collector moves on, `head` moves, the old cells are cleared, and waiting emitters are resumed as their values move onto the slate. Every change happens under one lock, and the coroutines to resume are collected and resumed after the lock is released. The KDoc puts the cost of an emit at O(N) in the number of subscribers.\n\nA StateFlow slot is one atomic field: free, waiting, pending, or a suspended continuation. An update marks every slot pending and copies nothing, which is why the KDoc calls StateFlow allocation-free. Updates that race each other use a sequence number that is odd while an update is being delivered. A second writer that arrives in the middle only bumps it, and the first writer loops round to deliver the newest value.\n\nTwo APIs in this area are experimental in 1.11.0 and need `@OptIn(ExperimentalCoroutinesApi::class)`. `resetReplayCache()` empties the replay cache for new subscribers, while existing ones keep what they had; on a `MutableStateFlow` it throws `UnsupportedOperationException: MutableStateFlow.resetReplayCache is not supported`. `SharedFlow.asFlow()`, new in 1.11.0, hides the hot type from callers.\n\nThe suspend overload `stateIn(scope)` has no `started`. It launches the upstream in `scope`, suspends until the first value, and returns a StateFlow holding it: in one run, a settings flow whose first value took 300 ms made `stateIn` return at t=300. That fits a setting loaded once at start-up. An empty upstream throws `NoSuchElementException: Flow is empty`. An upstream that fails before its first value rethrows to the caller and also cancels the scope you passed, so choose that scope knowing it goes down with a failed load."
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
