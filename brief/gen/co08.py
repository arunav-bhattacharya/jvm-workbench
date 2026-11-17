import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l08"
J = "java/workbench/coroutines/l08"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l08.{cls}{extra}"


def demo(kt, java, extra_kt="", extra_java=""):
    """A Kotlin demo and its runnable Java twin, read from disk so the lesson never drifts."""
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt", extra_kt),
            "file": f"{lab}/demo/{P}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{lab}/demo/{J}/{java}"), "run": run(j, extra_java),
                    "file": f"{lab}/demo/{J}/{java}"}}


def pair(kotlin, java):
    """A Kotlin fence and its Java twin, side by side, as the validator expects."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


slots = ""
for i, (x, v) in enumerate(zip([185, 243, 301, 359, 417], ["v4", "v5", "v6", "v7", "v8"])):
    cls = "box-a" if i < 3 else "box-b"
    slots += f'<rect class="{cls}" x="{x}" y="96" width="52" height="40" rx="8"/><text class="t t-code" x="{x + 26}" y="121" text-anchor="middle">{v}</text>'

FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Inside a MutableSharedFlow with replay 2 and extraBufferCapacity 3: five slots hold v4 to v8. '
    'The three oldest are kept for a slow subscriber that is still at v4. The two newest are the replay cache that a late subscriber gets first. '
    'When all slots are full, SUSPEND makes tryEmit return false and DROP_OLDEST drops v4. StateFlow is replay 1 with DROP_OLDEST and equal values skipped.">'
    '<text class="t-s t-code" x="15" y="24">MutableSharedFlow(replay = 2, extraBufferCapacity = 3)</text>'
    '<rect class="box" x="15" y="96" width="120" height="40" rx="8"/>'
    '<text class="t t-code" x="75" y="121" text-anchor="middle">tryEmit(v9)</text>'
    '<line class="ln" x1="135" y1="116" x2="168" y2="116" marker-end="url(#arr)"/>'
    '<rect class="box" x="170" y="70" width="315" height="100" rx="8"/>'
    '<text class="t-s t-m" x="185" y="88">oldest</text>'
    '<text class="t-s t-m" x="469" y="88" text-anchor="end">newest</text>'
    + slots +
    '<text class="t-s t-a" x="269" y="192" text-anchor="middle">held for slow subscribers</text>'
    '<text class="t-s t-b" x="414" y="192" text-anchor="middle">replay cache</text>'
    '<text class="t-s t-m" x="414" y="208" text-anchor="middle">late subscribers start here</text>'
    '<rect class="box" x="520" y="52" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="595" y="74" text-anchor="middle">late: starts at v7</text>'
    '<rect class="box-ok" x="520" y="99" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="595" y="121" text-anchor="middle">fast: up to date</text>'
    '<rect class="box-bad" x="520" y="146" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="595" y="168" text-anchor="middle">slow: still at v4</text>'
    '<text class="t-s" x="340" y="238" text-anchor="middle">all slots full: SUSPEND makes tryEmit return false; DROP_OLDEST drops v4</text>'
    '<text class="t-s t-m" x="340" y="258" text-anchor="middle">StateFlow is replay = 1, DROP_OLDEST, and skips values equal to the current one</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """In the hall of a busy house hangs a board that shows today's menu. Whoever walks past glances at it and sees what's for dinner now. Nobody reads yesterday's menu off it, and if the cook changes her mind three times before lunch, the board just shows the last choice. In the kitchen there's also a bell. When dinner is ready, the cook rings it, and everyone in the house who is listening hears it at that moment. Whoever comes home later hears nothing.

The flows of Flow basics were neither. A cold flow is a recipe card: it does nothing until someone cooks from it. Some values live on their own, whether anyone looks or not, such as the status of a dish or an announcement for the whole house. The easy traps are to use the board for announcements, and to ring a bell that nobody can hear while they're busy.

In this lesson, we'll build the board and the bell, see what each one loses, let many screens share one cold flow, and keep the writable version private. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_BOARD = """val board = MutableStateFlow(Menu(soup = "tomato"))
board.value = Menu(soup = "onion")     // set from any thread
println(board.value)                    // Menu(soup=onion)
board.collect { show(it) }              // current value first, then each change; never returns"""
J_BOARD = """// Java equivalent: a Reactor sink that replays its latest value, with repeats filtered out
Sinks.Many<Menu> board = Sinks.many().replay().latestOrDefault(new Menu("tomato"));
board.tryEmitNext(new Menu("onion"));
board.asFlux().distinctUntilChanged().subscribe(this::show);"""

S0 = """A `StateFlow<T>` is a flow that always has a value. You read it with `.value` at any moment, like glancing at the board. When you collect it, you get the current value first, then each new one. It is **hot**: it exists and holds its value whether or not anyone collects it, unlike the cold flows of Flow basics. That makes it the natural type for **state**, a value where only the latest one matters: the status of a dish, the oven's temperature, today's menu.

""" + pair(K_BOARD, J_BOARD) + """

Two rules make a StateFlow cheap, and both surprise people. Updates are **conflated**: a slow collector doesn't get a queue of the values it missed, it gets the latest one when it's ready. And a StateFlow compares with `equals`. Setting a value equal to the current one does nothing, and no collector wakes up. With a data class, a new object with the same fields counts as equal.

Predict the output before you read on. `StateFlowConflation`, in the Try it below, has a board in the hall that takes 100 ms to chalk up each menu. The cook changes the soup three times while the first one is being chalked up, then sets the last one again:

```text
the board in the hall shows tomato soup
the board in the hall shows onion soup
setting an equal menu again (a new object, same fields)
value is onion; the collector is still waiting, because a StateFlow never completes
```

Leek and pea never reached the board, and the second onion didn't either. Nobody chalks up "still onion".

Both rules follow from what StateFlow is underneath. Its KDoc, the documentation written in the library's source, describes `MutableStateFlow(initial)` as a shared flow (the next section's type) with `replay = 1` and `DROP_OLDEST`. That shared flow starts out holding the initial value, and a `distinctUntilChanged()` step drops repeats on the way out.

So a StateFlow is for state. It's the wrong type for **events**, values where every single one matters, such as each step a dish goes through for the kitchen log, or "dinner's ready". Conflation would drop some of them without a trace.

One more thing to expect: `collect` on a StateFlow never returns. The KDoc says it plainly, "state flow never completes". Collect it in a coroutine you will cancel, or wait for one particular value with `first`: `status.first { it == DishStatus.SERVED }`.

**A StateFlow keeps only the latest value. Use it for state, never for events.**

The board shows what's true now. For what just happened, the house needs a bell."""

# ---------------------------------------------------------------- section 1
K_BELL = """val bell = MutableSharedFlow<String>(
    replay = 0,                                 // late listeners get no history
    extraBufferCapacity = 64,                   // room for rings a busy listener hasn't heard yet
    onBufferOverflow = BufferOverflow.SUSPEND,  // when full: emit waits, tryEmit returns false
)"""
J_BELL = """// Java equivalent: a multicast Reactor sink with a buffer for slow subscribers
Sinks.Many<String> bell = Sinks.many().multicast().onBackpressureBuffer(64, false);
Sinks.EmitResult result = bell.tryEmitNext("dinner's ready");   // FAIL_OVERFLOW when full"""

S1 = """A `MutableSharedFlow<T>` is the house bell. It sends every value to every current **subscriber**, each coroutine collecting it at that moment. (A coroutine is a piece of work that can pause without holding a thread.) It has no current value of its own. Three parameters decide what it keeps:

""" + pair(K_BELL, J_BELL) + """

`replay` is how many recent values a new subscriber gets first. `extraBufferCapacity` is room beyond that for values that slow subscribers haven't taken yet. `onBufferOverflow` decides what happens when all of it is full. `SUSPEND`, the default, makes `emit` wait for the slowest subscriber. `DROP_OLDEST` throws away the oldest buffered value, and `DROP_LATEST` throws away the new one. The two drop policies need some replay or buffer to work with.

`emit` is a suspend function. `tryEmit` is its twin for code that can't suspend, such as a callback from an older library, and it's the impatient one: it never waits for anybody. If the value doesn't fit, it returns `false` and walks off.

Here's the trap, and it's easy to fall into because the defaults look harmless. With the default parameters there is no buffer at all. So **`tryEmit` fails whenever the flow has a subscriber, even an idle one** waiting for a value, and the value is lost unless you check the result. With no buffer, only the suspending `emit` can hand a value over, and it waits until every subscriber has taken it. With no subscriber at all, `tryEmit` returns `true`, and the value goes nowhere. The lab's starting code has exactly this bug.

`SharedFlowEvents`, in the Try it below, rings the bell five times with `tryEmit` while its one listener needs 50 ms to write each ring in the log. Predict each line:

```text
default (no replay, no buffer)           tryEmit: [false, false, false, false, false]  received: []
extraBufferCapacity = 2                  tryEmit: [true, true, false, false, false]  received: [e1, e2]
extraBufferCapacity = 2, DROP_OLDEST     tryEmit: [true, true, true, true, true]  received: [e4, e5]
extraBufferCapacity = 64                 tryEmit: [true, true, true, true, true]  received: [e1, e2, e3, e4, e5]
a late subscriber to replay = 2 first gets: [e4, e5]
```

The default bell rang five times and reached nobody. A buffer of 2 took two rings and refused the rest. `DROP_OLDEST` said `true` five times and quietly threw three rings away. Only the buffer of 64 delivered everything.

Here the bell picture breaks. A real bell rings for whoever is in the house, and a listener in the shower simply misses it. A SharedFlow with a buffer keeps each ring for a busy listener until they're ready, and when the buffer is full, `SUSPEND` makes the ringer wait. In an empty house, though, the two agree: a value emitted while nobody subscribes is gone, apart from the replay cache. If events must survive having no listener, you want something else: a `Channel` with one consumer (lesson 9 of this track), or a file or a database.

Side by side: a StateFlow has a value, replays exactly one, conflates and skips duplicates. A SharedFlow has no value, replays what you configure, and with a buffer and `SUSPEND` it delivers every event to every subscriber. Both are safe to emit into from many threads, the workers that run code, at once. Reactor's sinks, its objects for pushing values into a `Flux`, aren't by default: concurrent `tryEmitNext` calls can fail with `FAIL_NON_SERIALIZED`.

**A default `MutableSharedFlow()` has no buffer. Give it one, and check what `tryEmit` returns.**

The board and the bell are hot from the start. Often, though, the values come from a cold flow, and you want many screens to share one run of it."""

# ---------------------------------------------------------------- section 2
K_SHARE = """val temperature: StateFlow<Int> = thermometerReadings     // a cold flow
    .stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = 0)"""
J_SHARE = """// Java equivalent: one shared upstream that starts with the first subscriber
// and stops 5 seconds after the last one leaves
Flux<Integer> temperature = thermometerReadings
    .replay(1)
    .refCount(1, Duration.ofSeconds(5));"""

S2 = """A cold flow runs once per collector, as Flow basics showed. Picture a cold flow that reads the oven thermometer every 100 ms, and three screens around the house that show the temperature. Each screen collects the flow, so the thermometer is read three times as often as it needs to be.

`stateIn` and `shareIn` run the **upstream**, the cold flow they read from, just once. They run it in a scope you give them, the owner of coroutines from Structured concurrency, and share its values with every collector:

""" + pair(K_SHARE, J_SHARE) + """

`stateIn` gives a `StateFlow`, so it needs an initial value. `shareIn(scope, started, replay)` gives a `SharedFlow`. The `started` argument decides when the shared upstream runs:

- `SharingStarted.Eagerly` starts at once, before any subscriber, and runs until the scope is cancelled.
- `SharingStarted.Lazily` starts with the first subscriber and then never stops.
- `SharingStarted.WhileSubscribed(stopTimeoutMillis)` starts with the first subscriber and stops once the last one has been gone for `stopTimeoutMillis`. The default is 0. A few seconds is common, so a screen that restarts doesn't restart the upstream.

`StateInDemo`, in the Try it below, shares the thermometer with `WhileSubscribed(300)`. Two screens subscribe at 200 ms and leave 250 ms later. Predict when reading starts and stops:

```text
   79 ms  stateIn returned; waiting 200 ms before the first screen
  327 ms  two screens subscribed
  344 ms  thermometer: reading started
  581 ms  both screens left; temperature.value = 182
  884 ms  thermometer: reading stopped
 1081 ms  done
```

Reading started once, for both screens, and stopped about 300 ms after they left. Run with `-Pargs=eagerly`, the same demo started reading at 62 ms, before anyone was watching.

The scope owns the shared collection, so make it a long-lived scope you control, like the `Oven`'s scope in Structured concurrency. A scope that belongs to one short call would end the sharing when the call ends, and `GlobalScope` would never end it. In tests, the test library's `backgroundScope` plays that part.

Sharing doesn't make the upstream any less cold. When `WhileSubscribed` stops it and a new subscriber arrives later, the upstream runs again from the top. The readings restart, and a running total built with `runningFold`, the operator that keeps a running total, starts again from its initial value. For a live display that's what you want. For a total that must survive restarts, keep it somewhere durable and use the flow only to show it.

**`stateIn` and `shareIn` run one cold flow for many collectors. Give them a scope you own.**

Now we can build a class that owns some state and shares it. One question is left: who is allowed to change it?"""

# ---------------------------------------------------------------- section 3
K_TWO = """class DishTracker {
    private val _status = MutableStateFlow(DishStatus.WAITING)
    val status: StateFlow<DishStatus> = _status.asStateFlow()

    fun startCooking() { _status.value = DishStatus.COOKING }
}"""
J_TWO = """// Java equivalent: a private sink and a public read-only view
class DishTracker {
    private final Sinks.Many<DishStatus> status = Sinks.many().replay().latestOrDefault(DishStatus.WAITING);

    public Flux<DishStatus> status() { return status.asFlux(); }

    void startCooking() { status.tryEmitNext(DishStatus.COOKING); }
}"""
K_FIELD = """class DishTracker {
    val status: StateFlow<DishStatus>
        field = MutableStateFlow(DishStatus.WAITING)

    fun startCooking() { status.value = DishStatus.COOKING }   // smart-cast inside the class
}"""

S3 = """A class that owns some state should let callers read it, and nobody else write it. Picture a tracker for one dish: the board in the hall shows its status (waiting, cooking, served), and only the kitchen may move it on. Before Kotlin 2.4, that took two properties:

""" + pair(K_TWO, J_TWO) + """

A property's **backing field** is the hidden storage behind it. Kotlin 2.4.0 made **explicit backing fields** stable: a property can declare its field, with a more specific type than the property itself. They arrived as experimental in 2.3.0, whose release notes used exactly this case as their example:

```kotlin solo
""" + K_FIELD + """
```

Outside the class, `status` is a `StateFlow` with no setter. Inside it, the compiler knows the field is a `MutableStateFlow` and smart-casts, that is, treats it as the more specific type without a cast. One small difference remains. `asStateFlow()` returns a wrapper, so a caller can't cast it back to `MutableStateFlow`. An explicit backing field hides the type only at compile time. Both are fine in application code. In a library other people build on, the wrapper is the stricter choice.

Then write every change as one atomic step. `count.value = count.value + 1` is a read-modify-write, the race from Race conditions in the first track: two threads both read 41, both write 42, and one plate goes uncounted. `StateUpdates`, in the Try it below, lets 8 helpers each count 100,000 plates:

```text
value = value + 1                  expected 800000, got 457636
update { it + 1 }                  expected 800000, got 800000
```

Over 340,000 plates were served and never counted. `count.update { it + 1 }` retries with **compare-and-set**, an atomic "change it only if nobody beat me to it", until it wins. `status.compareAndSet(expected, new)` moves only if the value is still `expected`, and returns whether it did. That's how the lab's tracker makes sure two helpers can't both serve the same dish: the loser's `compareAndSet` fails, it reads the new status, and the move is no longer allowed.

The same habit applies to the bell. Ring it from the method that changes the state, after the change has succeeded, so the kitchen log never describes a move that didn't happen.

**Expose the read-only type, keep the writable one inside, and change it with `update` or `compareAndSet`.**"""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a board in the hall that always shows today's menu and a bell that everyone in the house hears when it rings. A StateFlow is the board: one current value, with missed and equal values skipped. A SharedFlow is the bell: every event to every listener, while its buffer has room. `stateIn` and `shareIn` let many screens share one cold flow.

Now search your own code for `MutableSharedFlow()` with no arguments, and for a `tryEmit` whose result nobody reads. Each is a bell that may ring unheard.

Next, we'll swap the bell for a hatch between two cooks. How does a queue between coroutines work, and how do you build a pipeline of workers with one?"""

L = {
 "id": "co-08",
 "title": "StateFlow, SharedFlow and hot streams",
 "minutes": 35,
 "goal": "By the end you can choose between StateFlow and SharedFlow, configure replay, buffer and overflow so events aren't lost, share one upstream with stateIn and SharingStarted, and expose state read-only with an explicit backing field.",
 "opening": OPENING,
 "warmup": {
  "q": "A `MutableStateFlow<Int>(0)` has one collector that takes 100 ms per value. Code sets `value = 1`, `2` and `3` within a millisecond, and later sets `3` again. Which values does the collector see?",
  "options": [
   "0, 1, 2, 3, 3",
   "0, 1, 2, 3",
   "0 and 3",
   "Only 3, because the collector started late"
  ],
  "answer": 2,
  "why": "A StateFlow holds one current value, like the board in the hall. A busy collector doesn't get a queue of what it missed; it gets the latest value when it's ready, so 1 and 2 are skipped. Setting a value equal to the current one does nothing at all, so the second 3 never arrives."
 },
 "sections": [
  {
   "h": "StateFlow is the board in the hall: one current value, and it skips what you missed",
   "body": S0,
   "try": {
    "title": "Watch the board skip two soups",
    "minutes": 3,
    "steps": [
     "Read `StateFlowConflation.kt`. Three menus are set while the board is busy, then an equal menu is set again. Predict every `the board in the hall shows` line.",
     "Run it.",
     "Change `Menu` from a `data class` to a plain `class` and run it again. Predict first: what changes, and why?",
     "Run the Java twin, which needs three Reactor operators for the same behavior."
    ],
    "code": demo("StateFlowConflation.kt", "StateFlowConflationJava.java"),
    "expect": "The board shows tomato soup, then onion soup: leek and pea are skipped. Setting the equal menu again prints nothing. With a plain class, equality falls back to identity, so the \"equal\" menu is a new value, and the board shows onion soup a second time. The Java twin prints the same two board lines, using `replay().latestOrDefault`, `distinctUntilChanged` and `onBackpressureLatest`."
   },
   "refs": [
    {"title": "StateFlow (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/", "kind": "docs"}
   ]
  },
  {
   "h": "SharedFlow is the house bell, and its buffer decides which rings are lost",
   "body": S1,
   "figure": {"svg": FIG, "caption": "A SharedFlow keeps replay plus extraBufferCapacity values. The newest are the replay cache; the older ones wait for slow subscribers."},
   "try": {
    "title": "Find out which rings get through",
    "minutes": 4,
    "steps": [
     "Read `SharedFlowEvents.kt`. Each case calls `tryEmit` five times while the only subscriber needs 50 ms per value. Predict the five results and what is received, for each of the four set-ups.",
     "Run it.",
     "Change the last case to `MutableSharedFlow(replay = 1, extraBufferCapacity = 64)`. Does anything in that line change?",
     "Run the Java twin."
    ],
    "code": demo("SharedFlowEvents.kt", "SharedFlowEventsJava.java"),
    "expect": "Default: `[false, false, false, false, false]` and nothing received: with no buffer, `tryEmit` can't hand anything over while there is a subscriber, busy or not. Buffer of 2: two `true`, then `false`, and `[e1, e2]` received. Buffer of 2 with `DROP_OLDEST`: every `tryEmit` returns `true`, but only `[e4, e5]` arrive, because the older ones were dropped. Buffer of 64: everything gets through. The late subscriber to `replay = 2` gets `[e4, e5]`. Adding `replay = 1` changes nothing in that line, because the subscriber was there from the start. The Java twin reports `FAIL_OVERFLOW` instead of `false`, and only after 9 values (it sends 20), because Reactor rounds small buffers up."
   },
   "refs": [
    {"title": "MutableSharedFlow (API reference: replay, buffer, overflow)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Share one cold flow among many screens with stateIn and shareIn",
   "body": S2,
   "try": {
    "title": "Start and stop a shared thermometer",
    "minutes": 4,
    "steps": [
     "Read `StateInDemo.kt`. It shares a thermometer flow with `WhileSubscribed(300)`. Predict when `reading started` and `reading stopped` print.",
     "Run it.",
     "Run it with `-Pargs=eagerly`, then with `-Pargs=lazily`. Predict each first.",
     "Run the Java twin, which uses `replay(1).refCount(1, 300 ms)`."
    ],
    "code": demo("StateInDemo.kt", "StateInDemoJava.java", " -Pargs=eagerly"),
    "expect": "With `WhileSubscribed(300)`, reading starts only when the screens subscribe, at about 200 ms, once for both, and stops about 300 ms after they leave. With `eagerly`, reading starts at once, before anyone subscribes, and stops only when the scope is cancelled at the end. With `lazily`, it starts with the first screen and never stops on its own (the line after `done` is the scope being cancelled). The Java twin starts and stops at the same moments as the `WhileSubscribed` run."
   },
   "refs": [
    {"title": "stateIn (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/state-in.html", "kind": "docs"},
    {"title": "SharingStarted (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/", "kind": "docs"}
   ]
  },
  {
   "h": "Keep the writable flow private, and change it in one step",
   "body": S3,
   "try": {
    "title": "Lose plates with value = value + 1",
    "minutes": 3,
    "steps": [
     "Read `StateUpdates.kt`. Eight coroutines on Default each add a plate 100,000 times. Predict both totals.",
     "Run it twice.",
     "Run the Java twin, which does the same with an `AtomicReference`."
    ],
    "code": demo("StateUpdates.kt", "StateUpdatesJava.java"),
    "expect": "`value = value + 1` comes out far short of 800,000, and the number changes from run to run (457,636 in one run here). `update { it + 1 }` gives exactly 800,000 every time. The Java twin loses updates with `set(get() + 1)` (303,507 here) and gets 800,000 with `updateAndGet`, because it's the same race and the same fix."
   },
   "refs": [
    {"title": "What's new in Kotlin 2.4.0 (explicit backing fields)", "url": "https://kotlinlang.org/docs/whatsnew24.html", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A dish tracker: Reactor sinks vs StateFlow and SharedFlow",
  "java": {"title": "DishTracker.java", "src": "class DishTracker {\n    private final AtomicReference<DishStatus> current = new AtomicReference<>(DishStatus.WAITING);\n    private final Sinks.Many<DishStatus> status = Sinks.many().replay().latestOrDefault(DishStatus.WAITING);\n    private final Sinks.Many<Transition> transitions = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    public DishStatus currentStatus() { return current.get(); }                   // 1. a synchronous read\n    public Flux<DishStatus> status() { return status.asFlux().distinctUntilChanged(); }\n    public Flux<Transition> transitions() { return transitions.asFlux(); }\n\n    boolean moveTo(DishStatus next) {\n        DishStatus from = current.get();\n        if (!from.canMoveTo(next) || !current.compareAndSet(from, next)) return false;   // 2. atomic move\n        // 3. sinks reject concurrent emits (FAIL_NON_SERIALIZED), so serialize them\n        synchronized (this) {\n            status.tryEmitNext(next);\n            transitions.tryEmitNext(new Transition(dish, from, next));\n        }\n        return true;\n    }\n}"},
  "kotlin": {"title": "DishTracker.kt", "src": "class DishTracker(private val dish: String) {\n    val status: StateFlow<DishStatus>                         // 1. .value is a synchronous read\n        field = MutableStateFlow(DishStatus.WAITING)\n    val transitions: SharedFlow<Transition>\n        field = MutableSharedFlow(extraBufferCapacity = 64)\n\n    fun moveTo(next: DishStatus): Boolean {\n        while (true) {\n            val from = status.value\n            if (!from.canMoveTo(next)) return false\n            if (status.compareAndSet(from, next)) {           // 2. atomic move\n                check(transitions.tryEmit(Transition(dish, from, next)))   // 3. safe from any thread\n                return true\n            }\n        }\n    }\n}"},
  "note": "The Kotlin version needs fewer moving parts, because a StateFlow is both the holder and the stream: `.value` reads it synchronously, `compareAndSet` changes it atomically, and collectors see changes with conflation and de-duplication built in. Reactor has no single type for that, so the Java version keeps an `AtomicReference` for the value and a replaying sink for the stream, and must keep the two in step. The other real difference is concurrency. `MutableStateFlow` and `MutableSharedFlow` are documented as safe for emitters on many threads. Reactor's default sinks detect concurrent `tryEmitNext` calls and fail them with `FAIL_NON_SERIALIZED`, so the Java tracker serializes its emits with a lock."
 },
 "worked": {
  "title": "Share one oven reading among every phone in the house",
  "steps": [
   {"say": "A family app shows the oven's temperature on every phone in the house. Each open phone collects `temperatures()`, a cold flow that asks the smart oven every second. With six phones open, the oven's small web server gets six questions a second and starts refusing some of them.",
    "code": "fun temperatures(): Flow<Int> = flow {\n    while (true) {\n        emit(oven.readCelsius())   // one call to the oven per collector per second\n        delay(1.seconds)\n    }\n}\n\n// on each phone's screen\ntemperatures().collect { show(it) }", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same design: a cold Flux subscribed once per phone\nFlux<Integer> temperatures() {\n    return Flux.interval(Duration.ZERO, Duration.ofSeconds(1))\n        .concatMap(tick -> oven.readCelsius());   // one call per subscriber per second\n}\n\n// on each phone's screen\ntemperatures().subscribe(this::show);", "alt_lang": "java"},
   {"say": "Decide the type first. A phone wants the latest temperature, and a phone that missed a reading doesn't need it replayed, so this is state: a `StateFlow`.",
    "code": "", "lang": ""},
   {"say": "Share the upstream in a scope that lives as long as the app, and stop it when nobody watches. Five seconds of grace covers a phone that locks its screen for a moment.",
    "code": "class OvenFeed(oven: SmartOven) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)     // 1. the owner of the sharing\n\n    val celsius: StateFlow<Int?> = flow {\n        while (true) { emit(oven.readCelsius()); delay(1.seconds) }\n    }.stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = null)   // 2. one call for all\n\n    override fun close() = scope.cancel()                                    // 3. ends with the app\n}", "lang": "kotlin",
    "alt_code": "class OvenFeed {\n    // 1. and 2.: one shared upstream, started by the first subscriber, stopped 5 s after the last\n    final Flux<Integer> celsius;\n\n    OvenFeed(SmartOven oven) {\n        this.celsius = Flux.interval(Duration.ZERO, Duration.ofSeconds(1))\n            .concatMap(tick -> oven.readCelsius())\n            .replay(1)\n            .refCount(1, Duration.ofSeconds(5));\n    }\n}", "alt_lang": "java"},
   {"say": "Each phone now collects the shared StateFlow. A slow phone gets the newest reading rather than a backlog, and a reading equal to the last one isn't sent again at all.",
    "code": "// on each phone's screen: no extra call to the oven\novenFeed.celsius.filterNotNull().collect { show(it) }", "lang": "kotlin",
    "alt_code": "// on each phone's screen: no extra call to the oven\novenFeed.celsius.distinctUntilChanged().onBackpressureLatest().subscribe(this::show);", "alt_lang": "java"},
   {"say": "Self-check: why not `SharingStarted.Eagerly`? (It would ask the oven every second from the moment the app starts, even at night with every phone asleep, and never stop until the app closes. `WhileSubscribed` asks only while someone is watching.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A dish tracker and a live plate count",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/DishStatus.kt", f"{lab}/main/{P}/DishTracker.kt", f"{lab}/main/{P}/LiveCount.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l08.*'",
  "steps": [
   "Meet the code. `DishStatus.kt` lists the statuses a dish moves through and the moves allowed between them. `DishTracker` tracks one dish: helpers call `moveTo` from their own threads, the board reads `status`, and the kitchen log collects `transitions`. It already uses explicit backing fields, so `status` is read-only outside the class. `liveServedCount` shares a running count of plates served. Run the tests: five of seven fail.",
   "Give `transitions` a buffer: `MutableSharedFlow(replay = 0, extraBufferCapacity = 64)`. The two transition tests should pass.",
   "Make `moveTo` atomic: in a loop, read `status.value`, check `canMoveTo`, call `beforeMove`, then `status.compareAndSet(from, next)`. If the compare-and-set fails, go round again. Emit the transition only after it succeeds.",
   "In `LiveCount.kt`, replace `SharingStarted.Eagerly` with `SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000)`.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "Inside the class, `status` smart-casts to `MutableStateFlow`, so `status.compareAndSet(from, next)` and `transitions.tryEmit(...)` compile without a cast.",
   "Check what `tryEmit` returns. With a buffer of 64 it should always be `true` here; `check(...)` turns a surprise `false` into a loud failure instead of a lost transition.",
   "The race test holds both helpers in `beforeMove` until both have read `COOKING`. With `compareAndSet`, the second one's move fails, it reads `SERVED`, and `canMoveTo` says no.",
   "The `stateIn` tests run on virtual time, the test library's pretend clock, so `WhileSubscribed(5_000)` takes no real time at all."
  ],
  "done_when": "All seven tests in `HotFlowsTest` pass."
 },
 "drill": {
  "title": "A smoke alarm's state, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `class SmokeAlarm` with a read-only `state: StateFlow<AlarmState>` (QUIET at first) backed by a writable one, `fun trip(): Boolean` that moves QUIET to RINGING atomically and returns whether this call did it, and `events: SharedFlow<String>` that code which can't suspend can publish to with `tryEmit`, even while a subscriber is busy.",
  "answer": {"lang": "kotlin", "src": "class SmokeAlarm {\n    val state: StateFlow<AlarmState>\n        field = MutableStateFlow(AlarmState.QUIET)\n\n    val events: SharedFlow<String>\n        field = MutableSharedFlow(extraBufferCapacity = 64)\n\n    fun trip(): Boolean {\n        if (!state.compareAndSet(AlarmState.QUIET, AlarmState.RINGING)) return false\n        check(events.tryEmit(\"alarm ringing\"))\n        return true\n    }\n}",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: an atomic holder for the state, a buffered multicast sink for events\nclass SmokeAlarm {\n    private final AtomicReference<AlarmState> state = new AtomicReference<>(AlarmState.QUIET);\n    private final Sinks.Many<String> events = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    AlarmState state() { return state.get(); }\n    Flux<String> events() { return events.asFlux(); }\n\n    synchronized boolean trip() {   // synchronized: Reactor sinks reject concurrent emits\n        if (!state.compareAndSet(AlarmState.QUIET, AlarmState.RINGING)) return false;\n        events.tryEmitNext(\"alarm ringing\").orThrow();\n        return true;\n    }\n}"}}
 },
 "recap": [
  "A `StateFlow` is hot and always has a value. It conflates (slow collectors get only the latest) and skips values equal to the current one, so it's for state, not events.",
  "A `SharedFlow` sends every value to every subscriber. `replay` is history for late subscribers, `extraBufferCapacity` is room for slow ones, and `onBufferOverflow` says what happens when both are full.",
  "With default parameters a `MutableSharedFlow` has no buffer, so `tryEmit` fails whenever the flow has a subscriber, even an idle one. Give it a buffer and check the result.",
  "`stateIn` and `shareIn` run a cold upstream once in a scope you own and share it. `WhileSubscribed(stopTimeoutMillis)` starts with the first subscriber and stops after the last one has left.",
  "Expose state read-only with an explicit backing field (stable since Kotlin 2.4) or `asStateFlow()`, and change it with `update { }` or `compareAndSet`, never `value = value + 1`.",
  "The limit: both hot flows live in memory. A value emitted while nobody subscribes is gone, apart from the replay cache, and nothing survives a restart."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "What does the collector print?\n\n```kotlin\nval s = MutableStateFlow(0)\nlaunch { s.collect { println(it); delay(100) } }\ndelay(10)\ns.value = 1; s.value = 2; s.value = 3\ndelay(200)\ns.value = 3\n```",
   "options": ["0, 1, 2, 3, 3", "0, 1, 2, 3", "0, 3", "3"],
   "answer": 2,
   "why": "The collector prints 0 and is busy for 100 ms while 1, 2 and 3 are set. A StateFlow conflates, so when it's ready it gets only the latest, 3. Setting 3 again is equal to the current value, so nothing is emitted."},
  {"q": "A kitchen log collects `val events = MutableSharedFlow<Transition>()` and takes 50 ms to write each line. A callback from an older library, which can't suspend, calls `events.tryEmit(t)` while the log is busy. What happens?",
   "options": ["`tryEmit` blocks the calling thread until the log is ready", "`tryEmit` returns `false`, and the transition is lost unless you check", "The transition is queued without limit", "`tryEmit` throws `IllegalStateException`"],
   "answer": 1,
   "why": "With default parameters there is no buffer, so a non-suspending emit has nowhere to put the value while there is any subscriber, busy or not. `tryEmit` never blocks or throws; it returns `false`. Use `extraBufferCapacity` and check the result."},
  {"q": "Every \"dish served\" event must reach both the kitchen log and the thank-you texter, which run all the time, and a burst of 50 events must not lose any. Which type fits?",
   "options": ["`MutableStateFlow<Served?>(null)`", "`MutableSharedFlow<Served>(extraBufferCapacity = 64)` with the default `SUSPEND`", "A cold `flow { }` that each consumer collects", "`MutableSharedFlow<Served>(replay = 1, onBufferOverflow = DROP_OLDEST)`"],
   "answer": 1,
   "why": "Events go to several subscribers, and none may be lost, so a SharedFlow with room for bursts and `SUSPEND` fits. A StateFlow conflates events away, a cold flow would run once per consumer instead of sending to both, and `DROP_OLDEST` throws events away when a subscriber falls behind."},
  {"q": "A screen shows the oven temperature from a flow shared with `stateIn`. A screen that restarts must not restart the readings, and nothing should read the oven when no screen is on. Which `started` value fits?",
   "options": ["`SharingStarted.Eagerly`", "`SharingStarted.Lazily`", "`SharingStarted.WhileSubscribed()`", "`SharingStarted.WhileSubscribed(5_000)`"],
   "answer": 3,
   "why": "`WhileSubscribed(5_000)` starts with the first subscriber and stops 5 s after the last one leaves, so a restart within that window keeps it running. The default `WhileSubscribed()` stops at once, `Lazily` never stops, and `Eagerly` reads the oven even before any screen is on."},
  {"q": "From lesson 7 of this track: three screens each collect the same `val readings = flow { while (true) { emit(readOven()); delay(1_000) } }`. How many times does `readOven()` run per second?",
   "options": ["Three times: a cold flow runs once per collector", "Once: the flow is shared because it is the same object", "Once, but only for the first screen; the others get nothing", "It depends on the dispatcher"],
   "answer": 0,
   "why": "A cold flow's body runs separately for every collector, even if they all hold the same `Flow` object. Sharing one upstream takes `stateIn` or `shareIn`.",
   "from": "co-07"}
 ],
 "flashcards": [
  {"front": "A StateFlow collector is busy while three new values are set. What does it see next?", "back": "Only the latest one. StateFlow conflates: values a slow collector missed are skipped."},
  {"front": "What happens when you set a `MutableStateFlow` to a value equal to its current one?", "back": "Nothing. It compares with `equals`, and an equal value emits nothing."},
  {"front": "`MutableSharedFlow()` with default parameters: what does `tryEmit` return when the flow has a subscriber?", "back": "`false`, even if the subscriber is idle. There is no buffer, so the value is dropped. Add `extraBufferCapacity` and check the result."},
  {"front": "`replay` vs `extraBufferCapacity` in a MutableSharedFlow?", "back": "`replay`: how many recent values a new subscriber gets first. `extraBufferCapacity`: extra room for values slow subscribers haven't taken yet."},
  {"front": "What does `SharingStarted.WhileSubscribed(5_000)` do?", "back": "Starts the shared upstream with the first subscriber and stops it 5 s after the last subscriber leaves."},
  {"front": "How do you expose a StateFlow read-only with one property in Kotlin 2.4?", "back": "An explicit backing field: `val status: StateFlow<S>` followed by `field = MutableStateFlow(initial)`."},
  {"front": "How do you add 1 to a `MutableStateFlow<Int>` safely from many threads?", "back": "`flow.update { it + 1 }`, which retries with compare-and-set. `value = value + 1` loses updates."}
 ],
 "terms": [
  {"term": "Hot flow", "plain": "A flow that exists and holds or sends values whether or not anyone collects it."},
  {"term": "StateFlow", "plain": "A hot flow with one current value; it conflates and skips equal values. The board in the hall."},
  {"term": "SharedFlow", "plain": "A hot flow that sends every value to every current subscriber. The house bell."},
  {"term": "Conflation", "plain": "Keeping only the latest value for a slow consumer and dropping the ones in between."},
  {"term": "Replay cache", "plain": "The last few values a SharedFlow keeps and gives to each new subscriber first."},
  {"term": "SharingStarted", "plain": "The rule that tells stateIn or shareIn when to start and stop the shared upstream."},
  {"term": "Explicit backing field", "plain": "A Kotlin property whose hidden field has a different, more specific type than the property itself."}
 ],
 "explain_back": {
  "prompt": "A friend stores each step a dish goes through in a `MutableStateFlow<Transition?>` so the kitchen log can collect them, and the log is missing entries on busy evenings. Explain why, and what you would use instead.",
  "answer": "A StateFlow holds one current value, so it's built to drop history. When the log is busy writing one transition and two more happen, it only gets the latest one when it's ready, and the middle one is gone. It also skips a value equal to the current one, so a repeated transition never arrives. That's right for state like \"the current status\", but transitions are events, and every one matters. I'd use a MutableSharedFlow with no replay and an extraBufferCapacity big enough for a busy evening, keep the default SUSPEND overflow, and check what tryEmit returns, so a full buffer shows up as an error instead of a missing line. And because it all lives in memory, anything that must survive a restart should also be written somewhere durable, such as a file or a database."
 },
 "deeper": {
  "minutes": 10,
  "body": "`MutableSharedFlow` has a `subscriptionCount: StateFlow<Int>`. It is deliberately not conflated, so you can react to the first subscriber arriving or the last one leaving, for example to open and close a connection to a slow device. `SharingStarted` is an interface, and `WhileSubscribed` is written on top of exactly that count. A custom strategy can start sharing only at certain hours, or only after a warm-up.\n\n`WhileSubscribed` has a second parameter, `replayExpirationMillis`, which defaults to `Long.MAX_VALUE`. It decides how long the last value stays in the replay cache after the upstream stops. Set it to 0 if a stale value is worse than none, for instance an oven temperature that must never be shown once the oven has been switched off.\n\n`stateIn` and `shareIn` keep a coroutine running in the scope you give them, so the scope's life is the sharing's life. If the upstream throws, that coroutine fails, the error goes up into the scope, and the StateFlow simply stops updating. Put a `catch` or `retryWhen` on the upstream, above `stateIn`, and decide what the subscribers should see while it recovers.\n\nkotlinx.coroutines 1.11 added two small helpers. `SharedFlow.asFlow()` returns a view that hides the hot-flow type, so callers can't rely on it being shared. And there is now an `onSubscription` overload on StateFlow that keeps the `StateFlow` type. Kotlin 2.1.20 also added common atomics such as `AtomicInt` in `kotlin.concurrent.atomics`, marked experimental. For plain counters shared between coroutines they are an alternative to a StateFlow that nobody collects, which lesson 10 of this track compares with `Mutex`.\n\nThis lesson is the first look at hot flows. Hot flows in depth, in the Kotlin Flow in depth track, opens up the SharedFlow buffer slot by slot, and shows how `stateIn` and `shareIn` decide when to start and stop."
 },
 "sources": [
  {"title": "StateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/"},
  {"title": "SharedFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/"},
  {"title": "stateIn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/state-in.html"},
  {"title": "What's new in Kotlin 2.4.0", "url": "https://kotlinlang.org/docs/whatsnew24.html"}
 ]
}
out = ROOT / "content/lessons/co-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
