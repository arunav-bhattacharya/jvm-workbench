import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l08"
J = "java/workbench/coroutines/l08"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l08.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


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

L = {
 "id": "co-08",
 "title": "StateFlow, SharedFlow and hot streams",
 "minutes": 35,
 "goal": "By the end you can choose between StateFlow and SharedFlow, configure replay, buffer and overflow so events aren't lost, share one upstream with stateIn and SharingStarted, and expose state read-only with an explicit backing field.",
 "warmup": {
  "q": "A `MutableStateFlow<Int>(0)` has one collector that takes 100 ms per value. Code sets `value = 1`, `2` and `3` within a millisecond, and later sets `3` again. Which values does the collector see?",
  "options": [
   "0, 1, 2, 3, 3",
   "0, 1, 2, 3",
   "0 and 3",
   "Only 3, because the collector started late"
  ],
  "answer": 2,
  "why": "A StateFlow holds one current value. A busy collector doesn't get a queue of what it missed; it gets the latest value when it is ready, so 1 and 2 are skipped. Setting a value equal to the current one does nothing at all, so the second 3 never arrives."
 },
 "sections": [
  {
   "h": "StateFlow is one current value, and it skips what you missed",
   "body": "A `StateFlow<T>` always has a value. You can read it with `.value` at any moment, and when you collect it you get the current value first, then each new one. It is **hot**: it exists and holds its value whether or not anyone collects, unlike the cold flows of lesson 7 of this track. That makes it the natural type for state such as a payment's status, a circuit breaker's state or the latest FX rate.\n\n```kotlin\nval status = MutableStateFlow(PaymentStatus.PENDING)\nstatus.value = PaymentStatus.AUTHORIZED     // set from any thread\nprintln(status.value)                       // AUTHORIZED\nstatus.collect { render(it) }               // current value first, then each change; never returns\n```\n\n```java\n// Java equivalent: a Reactor sink that replays its latest value, with repeats filtered out\nSinks.Many<PaymentStatus> status = Sinks.many().replay().latestOrDefault(PaymentStatus.PENDING);\nstatus.tryEmitNext(PaymentStatus.AUTHORIZED);\nstatus.asFlux().distinctUntilChanged().subscribe(this::render);\n```\n\nTwo rules make StateFlow cheap, and both surprise people. Updates are **conflated**: a slow collector doesn't get a queue of the values it missed, it gets the latest one when it is ready. Set 1, 2 and 3 in quick succession while a collector is busy and it sees 3 next, never 1 or 2. And it compares with `equals`. Setting a value equal to the current one does nothing, and no collector wakes up. With a data class, a new object with the same fields counts as equal.\n\nBoth rules follow from what StateFlow is. Its KDoc describes `MutableStateFlow(initial)` as a shared flow with `replay = 1` and `DROP_OLDEST`, seeded with the initial value and followed by `distinctUntilChanged()`.\n\nSo StateFlow is for state, where only the latest value matters. It is the wrong type for events, where every one matters: payment transitions for the audit log, \"send this receipt\" commands, ledger postings. Conflation would drop some of them without a trace. Events need `SharedFlow`, which is the next section.\n\nOne more thing to expect: `collect` on a StateFlow never returns. The KDoc says it plainly, \"state flow never completes\". Collect it in a coroutine you will cancel, or wait for one particular value with `first`: `status.first { it == PaymentStatus.CAPTURED }`.",
   "try": {
    "title": "Watch a dashboard skip FX ticks",
    "minutes": 3,
    "steps": [
     "Read `StateFlowConflation.kt`. Three ticks arrive while the dashboard is busy, then an equal rate is set again. Predict every `dashboard shows` line.",
     "Run it.",
     "Change `Rate` from a `data class` to a plain `class` and run it again. Predict first: what changes, and why?",
     "Run the Java twin, which needs three Reactor operators to get the same behavior."
    ],
    "code": tryit("StateFlowConflation.kt", "StateFlowConflationJava.java"),
    "expect": "The dashboard shows 1.0809, then 1.0813: the two ticks in between are skipped. Setting the equal rate again prints nothing. With a plain class, equality falls back to identity, so the \"equal\" rate is a new value and the dashboard shows 1.0813 a second time. The Java twin prints the same two lines, using `replay().latestOrDefault`, `distinctUntilChanged` and `onBackpressureLatest`."
   },
   "refs": [
    {"title": "StateFlow (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/", "kind": "docs"}
   ]
  },
  {
   "h": "SharedFlow is for events, and its buffer decides what gets lost",
   "body": "A `MutableSharedFlow<T>` broadcasts every value to every current subscriber. It has no current value. Three parameters decide what it keeps:\n\n```kotlin\nval transitions = MutableSharedFlow<Transition>(\n    replay = 0,                                 // late subscribers get no history\n    extraBufferCapacity = 64,                   // room for values a slow subscriber hasn't read yet\n    onBufferOverflow = BufferOverflow.SUSPEND,  // when full: emit waits, tryEmit returns false\n)\n```\n\n```java\n// Java equivalent: a multicast Reactor sink with a buffer for slow subscribers\nSinks.Many<Transition> transitions = Sinks.many().multicast().onBackpressureBuffer(64, false);\nSinks.EmitResult result = transitions.tryEmitNext(t);   // FAIL_OVERFLOW when full\n```\n\n`replay` is how many recent values a new subscriber gets first. `extraBufferCapacity` is room beyond that for values that slow subscribers haven't taken yet. `onBufferOverflow` decides what happens when all of it is full. `SUSPEND`, the default, makes `emit` wait for the slowest subscriber. `DROP_OLDEST` throws away the oldest buffered value, and `DROP_LATEST` throws away the new one. The two drop policies need some replay or buffer to work with.\n\n`emit` is a suspend function. `tryEmit` is its non-suspending twin for code that can't suspend, such as a Kafka listener callback, and it returns `false` when the value doesn't fit. Here is the trap. With the default parameters there is no buffer at all, so **`tryEmit` fails whenever a subscriber is busy**, and the value is lost unless you check the result. The lab's stub has exactly this bug. Give the flow a buffer, and check what `tryEmit` returns.\n\nA SharedFlow never completes either, and a value emitted while nobody subscribes goes nowhere, apart from the replay cache. If events must survive having no listener, you want something else: a `Channel` with one consumer (lesson 9 of this track), or a durable topic.\n\nPut side by side: StateFlow has a value, replays exactly one, conflates and skips duplicates. SharedFlow has no value, replays what you configure, and with a buffer and `SUSPEND` it delivers every event to every subscriber. Both are safe to emit into from many threads at once. Reactor's sinks are not by default: concurrent `tryEmitNext` calls can fail with `FAIL_NON_SERIALIZED`.",
   "figure": {"svg": FIG, "caption": "A SharedFlow keeps replay plus extraBufferCapacity values. The newest are the replay cache; the older ones wait for slow subscribers."},
   "try": {
    "title": "Find out which events get through",
    "minutes": 4,
    "steps": [
     "Read `SharedFlowEvents.kt`. Each case calls `tryEmit` five times while the only subscriber needs 50 ms per event. Predict the five results and what is received, for each of the four configurations.",
     "Run it.",
     "Change the last case to `MutableSharedFlow(replay = 1, extraBufferCapacity = 64)`. Does anything in that line change?",
     "Run the Java twin."
    ],
    "code": tryit("SharedFlowEvents.kt", "SharedFlowEventsJava.java"),
    "expect": "Default: `[false, false, false, false, false]` and nothing received: no room at all while the subscriber is busy. Buffer of 2: two `true`, then `false`, and `[e1, e2]` received. Buffer of 2 with `DROP_OLDEST`: every `tryEmit` returns `true`, but only `[e4, e5]` arrive, because the older ones were dropped. Buffer of 64: everything gets through. The late subscriber to `replay = 2` gets `[e4, e5]`. Adding `replay = 1` changes nothing in that line: the subscriber was there from the start. The Java twin reports `FAIL_OVERFLOW` instead of `false`, and only after 9 events, because Reactor rounds small buffers up."
   },
   "refs": [
    {"title": "MutableSharedFlow (API reference: replay, buffer, overflow)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Turn one cold flow into a shared hot one with stateIn and shareIn",
   "body": "A cold flow runs once per collector. If three ops dashboards each collect a flow that polls the acquirer's settlement API, the API is polled three times. `stateIn` and `shareIn` run the upstream once, in a scope you give them, and share its values:\n\n```kotlin\nval capturedTotal: StateFlow<Long> = captures            // a cold flow fed from Kafka\n    .runningFold(0L) { total, cents -> total + cents }\n    .stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = 0L)\n```\n\n```java\n// Java equivalent: one shared upstream that starts with the first subscriber\n// and stops 5 seconds after the last one leaves\nFlux<Long> capturedTotal = captures\n    .scan(0L, Long::sum)\n    .replay(1)\n    .refCount(1, Duration.ofSeconds(5));\n```\n\n`stateIn` gives a `StateFlow`, so it needs an initial value. `shareIn(scope, started, replay)` gives a `SharedFlow`. The `started` argument decides when the shared upstream runs:\n\n- `SharingStarted.Eagerly` starts at once, before any subscriber, and runs until the scope is cancelled.\n- `SharingStarted.Lazily` starts with the first subscriber and then never stops.\n- `SharingStarted.WhileSubscribed(stopTimeoutMillis)` starts with the first subscriber and stops once the last one has been gone for `stopTimeoutMillis`. The default is 0. A few seconds is common, so a page reload or a quick reconnect doesn't restart the upstream.\n\nThe scope owns the shared collection, so make it a long-lived scope you control, like the owned scopes of lesson 3 of this track. A request's scope would end the sharing when the request ends, and `GlobalScope` would never end it. In tests, `backgroundScope` plays that part.\n\nThere is also a suspend overload, `stateIn(scope)` without `started`, which waits for the first value and keeps the upstream running for the life of the scope.\n\nSharing doesn't make the upstream any less cold. When `WhileSubscribed` stops it and a new subscriber arrives later, the upstream runs again from the top: the poll loop restarts, and a `runningFold` starts again from its initial value. That is usually what you want for a live feed. For a total that must survive restarts, keep it somewhere durable and use the flow only to show it.",
   "try": {
    "title": "Start and stop a shared poller",
    "minutes": 4,
    "steps": [
     "Read `StateInDemo.kt`. It shares an FX poller with `WhileSubscribed(300)`. Predict when `polling started` and `polling stopped` print.",
     "Run it.",
     "Run it with `-Pargs=eagerly`, then with `-Pargs=lazily`. Predict each first.",
     "Run the Java twin, which uses `replay(1).refCount(1, 300 ms)`."
    ],
    "code": tryit("StateInDemo.kt", "StateInDemoJava.java", " -Pargs=eagerly"),
    "expect": "With `WhileSubscribed(300)`, polling starts only when the dashboards subscribe, at about 200 ms, once for both. It stops about 300 ms after they leave. With `eagerly`, polling starts at once, before anyone subscribes, and stops only when the scope is cancelled at the end. With `lazily`, it starts with the first dashboard and never stops on its own. The Java twin starts and stops at the same moments as the `WhileSubscribed` run."
   },
   "refs": [
    {"title": "stateIn (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/state-in.html", "kind": "docs"},
    {"title": "SharingStarted (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/", "kind": "docs"}
   ]
  },
  {
   "h": "Keep the mutable flow private and update it in one step",
   "body": "A class that owns some state should let callers read it and nobody else write it. Before Kotlin 2.4 that took two properties:\n\n```kotlin\nclass PaymentTracker {\n    private val _status = MutableStateFlow(PaymentStatus.PENDING)\n    val status: StateFlow<PaymentStatus> = _status.asStateFlow()\n\n    fun authorize() { _status.value = PaymentStatus.AUTHORIZED }\n}\n```\n\n```java\n// Java equivalent: a private sink and a public read-only view\nclass PaymentTracker {\n    private final Sinks.Many<PaymentStatus> status = Sinks.many().replay().latestOrDefault(PaymentStatus.PENDING);\n\n    public Flux<PaymentStatus> status() { return status.asFlux(); }\n\n    void authorize() { status.tryEmitNext(PaymentStatus.AUTHORIZED); }\n}\n```\n\nKotlin 2.4.0 made **explicit backing fields** stable. They arrived as experimental in 2.3.0, whose release notes used exactly this case as their example. One property declares its public type and, separately, its field:\n\n```kotlin solo\nclass PaymentTracker {\n    val status: StateFlow<PaymentStatus>\n        field = MutableStateFlow(PaymentStatus.PENDING)\n\n    fun authorize() { status.value = PaymentStatus.AUTHORIZED }   // smart-cast inside the class\n}\n```\n\nOutside the class, `status` is a `StateFlow` with no setter. Inside it, the compiler knows the field is a `MutableStateFlow` and smart-casts. One small difference remains. `asStateFlow()` returns a wrapper, so a caller can't cast it back to `MutableStateFlow`. An explicit backing field hides the type only at compile time. Both are fine in application code. In a library other teams build on, the wrapper is the stricter choice.\n\nThen write every change as one atomic step. `count.value = count.value + 1` is a read-modify-write (lesson 3 of the threads track), and two threads running it together lose updates. `count.update { it + 1 }` retries with compare-and-set until it wins. `status.compareAndSet(expected, new)` moves only if the value is still `expected` and returns whether it did. That is how the lab's tracker makes sure two Kafka listener threads can't both capture the same payment: the loser's `compareAndSet` fails, it reads the new status, and the move is no longer allowed.\n\nThe same habit applies to SharedFlow events. Emit from the method that changes the state, after the change has succeeded, so the event stream never describes a move that didn't happen.",
   "try": {
    "title": "Lose cents with value = value + 1",
    "minutes": 3,
    "steps": [
     "Read `StateUpdates.kt`. Eight coroutines on Default each add a cent 100,000 times. Predict both totals.",
     "Run it twice.",
     "Run the Java twin, which does the same with an `AtomicReference`."
    ],
    "code": tryit("StateUpdates.kt", "StateUpdatesJava.java"),
    "expect": "`value = value + 1` comes out far short of 800,000, and the number changes from run to run (one run here gave 259,299). `update { it + 1 }` gives exactly 800,000 every time. The Java twin loses updates with `set(get() + 1)` and gets 800,000 with `updateAndGet`, because they are the same race and the same fix."
   },
   "refs": [
    {"title": "What's new in Kotlin 2.4.0 (explicit backing fields)", "url": "https://kotlinlang.org/docs/whatsnew24.html", "kind": "read"}
   ]
  }
 ],
 "analogy": "A StateFlow is the departures board at a station. It always shows something, it shows only the latest state of each train, and if you look away while a platform changes twice, you see only the final platform. Nobody announces \"still on time\" again. A SharedFlow is the station's public address system. Every announcement goes to everyone standing there, people who arrive late hear nothing that was said before they came (unless the station repeats the last few, which is `replay`), and if the announcer talks faster than the slowest listener can follow, someone has to wait or a message gets cut. `stateIn` is putting one person in charge of phoning the control room and updating the board for everyone, instead of every passenger phoning in. The analogy breaks at the empty station: a real announcer stops talking when nobody is there, but a SharedFlow's emitter keeps going, and the announcements simply vanish.",
 "in_your_world": "In a payment service, StateFlow fits anything a page or a health check reads as \"the current value\": a payment's status for the status endpoint, the circuit breaker in front of the card issuer, the latest FX rates. SharedFlow fits in-process events, such as status transitions that an audit writer and a notifier both consume. Remember it is in memory only: an audit trail that must survive a pod restart still belongs in Kafka or an outbox table, with the SharedFlow as a fast in-process fan-out at most. Kafka listener threads can't suspend, so they publish with `tryEmit`, which means the flow needs a buffer and the result must be checked or turned into a metric. For a live ops dashboard or a server-sent-events endpoint in Quarkus, `stateIn(appScope, WhileSubscribed(5_000), initial)` gives every open connection the same feed from one upstream, and stops polling when nobody is watching.",
 "mistake": "The most common mistake is using a StateFlow (or `MutableSharedFlow()` with default parameters) as an event bus. With StateFlow, two transitions in quick succession arrive as one, and repeating an event that equals the current value delivers nothing, so an audit log quietly misses entries. With a default SharedFlow, `tryEmit` from a non-suspending callback returns `false` whenever a subscriber is busy, and the event vanishes. Both look fine in a unit test with one fast collector. Decide what the stream carries. State, where only the latest matters, goes in a StateFlow. Events, where every one matters, go in a SharedFlow with `extraBufferCapacity` sized for bursts, `SUSPEND` overflow, and a checked `tryEmit` (or `emit` from a coroutine).",
 "compare": {
  "title": "A payment tracker: Reactor sinks vs StateFlow and SharedFlow",
  "java": {"title": "PaymentTracker.java", "src": "class PaymentTracker {\n    private final AtomicReference<PaymentStatus> current = new AtomicReference<>(PaymentStatus.PENDING);\n    private final Sinks.Many<PaymentStatus> status = Sinks.many().replay().latestOrDefault(PaymentStatus.PENDING);\n    private final Sinks.Many<Transition> transitions = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    public PaymentStatus currentStatus() { return current.get(); }               // 1. a synchronous read\n    public Flux<PaymentStatus> status() { return status.asFlux().distinctUntilChanged(); }\n    public Flux<Transition> transitions() { return transitions.asFlux(); }\n\n    boolean moveTo(PaymentStatus next) {\n        PaymentStatus from = current.get();\n        if (!from.canMoveTo(next) || !current.compareAndSet(from, next)) return false;   // 2. atomic move\n        // 3. sinks reject concurrent emits (FAIL_NON_SERIALIZED), so serialize them\n        synchronized (this) {\n            status.tryEmitNext(next);\n            transitions.tryEmitNext(new Transition(id, from, next));\n        }\n        return true;\n    }\n}"},
  "kotlin": {"title": "PaymentTracker.kt", "src": "class PaymentTracker(private val id: String) {\n    val status: StateFlow<PaymentStatus>                      // 1. .value is a synchronous read\n        field = MutableStateFlow(PaymentStatus.PENDING)\n    val transitions: SharedFlow<Transition>\n        field = MutableSharedFlow(extraBufferCapacity = 64)\n\n    fun moveTo(next: PaymentStatus): Boolean {\n        while (true) {\n            val from = status.value\n            if (!from.canMoveTo(next)) return false\n            if (status.compareAndSet(from, next)) {           // 2. atomic move\n                check(transitions.tryEmit(Transition(id, from, next)))   // 3. safe from any thread\n                return true\n            }\n        }\n    }\n}"},
  "note": "The Kotlin version needs fewer moving parts because StateFlow is both the holder and the stream: `.value` reads it synchronously, `compareAndSet` changes it atomically, and collectors see changes with conflation and de-duplication built in. Reactor has no single type for that, so the Java version keeps an `AtomicReference` for the value and a replaying sink for the stream, and must keep them consistent. The other real difference is concurrency. `MutableStateFlow` and `MutableSharedFlow` are documented as safe for concurrent emitters. Reactor's default sinks detect concurrent `tryEmitNext` calls and fail them with `FAIL_NON_SERIALIZED`, so the Java tracker serializes its emits."
 },
 "worked": {
  "title": "Share one FX feed across every dashboard",
  "steps": [
   {"say": "An ops dashboard shows live FX rates over server-sent events. Each open connection collects `rates()`, a cold flow that polls the provider every second. With 40 open tabs the provider sees 40 polls a second and starts rate-limiting the payment service too.",
    "code": "fun rates(): Flow<FxRates> = flow {\n    while (true) {\n        emit(provider.latest())   // one HTTP call per collector per second\n        delay(1.seconds)\n    }\n}\n\n// in the SSE resource, once per connection\nrates().collect { send(it) }", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same design: a cold Flux subscribed once per connection\nFlux<FxRates> rates() {\n    return Flux.interval(Duration.ZERO, Duration.ofSeconds(1))\n        .concatMap(tick -> provider.latest());   // one HTTP call per subscriber per second\n}\n\n// in the SSE resource, once per connection\nreturn rates();", "alt_lang": "java"},
   {"say": "Decide the type first. A dashboard wants the latest rates, and a tab that missed a tick doesn't need it replayed, so this is state: a `StateFlow`.",
    "code": "", "lang": ""},
   {"say": "Share the upstream in a scope that lives as long as the service, and stop it when nobody watches. Five seconds of grace covers a tab reload.",
    "code": "@ApplicationScoped\nclass FxFeed(provider: FxProvider) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)    // 1. the owner of the sharing\n\n    val rates: StateFlow<FxRates?> = flow {\n        while (true) { emit(provider.latest()); delay(1.seconds) }\n    }.stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue = null)   // 2. one poll for all\n\n    override fun close() = scope.cancel()                                   // 3. ends with the bean\n}", "lang": "kotlin",
    "alt_code": "@ApplicationScoped\nclass FxFeed {\n    // 1. and 2.: one shared poll, started by the first subscriber, stopped 5 s after the last\n    final Flux<FxRates> rates;\n\n    FxFeed(FxProvider provider) {\n        this.rates = Flux.interval(Duration.ZERO, Duration.ofSeconds(1))\n            .concatMap(tick -> provider.latest())\n            .replay(1)\n            .refCount(1, Duration.ofSeconds(5));\n    }\n}", "alt_lang": "java"},
   {"say": "Each connection now collects the shared StateFlow. A slow client gets the newest rates rather than a backlog, and a tick with unchanged rates (an equal data class) isn't sent at all.",
    "code": "// in the SSE resource, once per connection: no extra poll\nfxFeed.rates.filterNotNull().collect { send(it) }", "lang": "kotlin",
    "alt_code": "// in the SSE resource, once per connection: no extra poll\nreturn fxFeed.rates.distinctUntilChanged().onBackpressureLatest();", "alt_lang": "java"},
   {"say": "Self-check: why not `SharingStarted.Eagerly`? (It would poll the provider every second from startup, even at night with no dashboards open, and never stop until shutdown. `WhileSubscribed` polls only while someone is watching.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A payment tracker and a live total",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/PaymentStatus.kt", f"{lab}/main/{P}/PaymentTracker.kt", f"{lab}/main/{P}/LiveTotals.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l08.*'",
  "steps": [
   "Run the tests. Five of seven fail. `PaymentStatus.kt` has the allowed moves; `PaymentTracker.kt` already uses explicit backing fields, so `status` is read-only outside the class.",
   "Give `transitions` a buffer: `MutableSharedFlow(replay = 0, extraBufferCapacity = 64)`. The two transition tests should pass.",
   "Make `moveTo` atomic: in a loop, read `status.value`, check `canMoveTo`, call `beforeMove`, then `status.compareAndSet(from, next)`. If the CAS fails, go round again. Emit the transition only after a successful CAS.",
   "In `LiveTotals.kt`, replace `SharingStarted.Eagerly` with `SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000)`.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "Inside the class, `status` smart-casts to `MutableStateFlow`, so `status.compareAndSet(from, next)` and `transitions.tryEmit(...)` compile without a cast.",
   "Check what `tryEmit` returns. With a buffer of 64 it should always be `true` here; `check(...)` turns a surprise `false` into a loud failure instead of a lost event.",
   "The race test holds both threads in `beforeMove` until both have read `AUTHORIZED`. With `compareAndSet`, the second one's CAS fails, it reads `CAPTURED`, and `canMoveTo` says no.",
   "The `stateIn` tests run on virtual time, so `WhileSubscribed(5_000)` takes no real time at all."
  ],
  "done_when": "All seven tests in `HotFlowsTest` pass."
 },
 "drill": {
  "title": "A circuit breaker's state, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `class IssuerBreaker` with a read-only `state: StateFlow<BreakerState>` (CLOSED at first) backed by a mutable one, `fun trip(): Boolean` that moves CLOSED to OPEN atomically and returns whether this call did it, and `events: SharedFlow<String>` that a non-suspending caller can publish to with `tryEmit` even while a subscriber is busy.",
  "answer": {"lang": "kotlin", "src": "class IssuerBreaker {\n    val state: StateFlow<BreakerState>\n        field = MutableStateFlow(BreakerState.CLOSED)\n\n    val events: SharedFlow<String>\n        field = MutableSharedFlow(extraBufferCapacity = 64)\n\n    fun trip(): Boolean {\n        if (!state.compareAndSet(BreakerState.CLOSED, BreakerState.OPEN)) return false\n        check(events.tryEmit(\"breaker opened\"))\n        return true\n    }\n}",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: an atomic holder for the state, a buffered multicast sink for events\nclass IssuerBreaker {\n    private final AtomicReference<BreakerState> state = new AtomicReference<>(BreakerState.CLOSED);\n    private final Sinks.Many<String> events = Sinks.many().multicast().onBackpressureBuffer(64, false);\n\n    BreakerState state() { return state.get(); }\n    Flux<String> events() { return events.asFlux(); }\n\n    synchronized boolean trip() {   // synchronized: Reactor sinks reject concurrent emits\n        if (!state.compareAndSet(BreakerState.CLOSED, BreakerState.OPEN)) return false;\n        events.tryEmitNext(\"breaker opened\").orThrow();\n        return true;\n    }\n}"}}
 },
 "recap": [
  "A `StateFlow` is hot and always has a value. It conflates (slow collectors get only the latest) and skips values equal to the current one, so it is for state, not events.",
  "A `SharedFlow` broadcasts every value to every subscriber. `replay` is history for late subscribers, `extraBufferCapacity` is room for slow ones, and `onBufferOverflow` says what happens when both are full.",
  "With default parameters a `MutableSharedFlow` has no buffer, so `tryEmit` fails while a subscriber is busy. Give it a buffer and check the result.",
  "`stateIn` and `shareIn` run a cold upstream once in a scope you own and share it. `WhileSubscribed(stopTimeoutMillis)` starts with the first subscriber and stops after the last one has left.",
  "Expose state read-only with an explicit backing field (`val s: StateFlow<T>` with `field = MutableStateFlow(...)`, stable since Kotlin 2.4) or `asStateFlow()`.",
  "Change shared state in one atomic step: `update { }` or `compareAndSet`, never `value = value + 1`."
 ],
 "quiz": [
  {"q": "What does the collector print?\n\n```kotlin\nval s = MutableStateFlow(0)\nlaunch { s.collect { println(it); delay(100) } }\ndelay(10)\ns.value = 1; s.value = 2; s.value = 3\ndelay(200)\ns.value = 3\n```",
   "options": ["0, 1, 2, 3, 3", "0, 1, 2, 3", "0, 3", "3"],
   "answer": 2,
   "why": "The collector prints 0 and is busy for 100 ms while 1, 2 and 3 are set. StateFlow conflates, so when it is ready it gets only the latest, 3. Setting 3 again is equal to the current value, so nothing is emitted."},
  {"q": "An audit writer collects `val events = MutableSharedFlow<Transition>()` and takes 50 ms per write. A Kafka listener thread calls `events.tryEmit(t)` while the writer is busy. What happens?",
   "options": ["`tryEmit` blocks the listener thread until the writer is ready", "`tryEmit` returns `false` and the transition is lost unless you check", "The transition is queued without limit", "`tryEmit` throws `IllegalStateException`"],
   "answer": 1,
   "why": "With default parameters there is no buffer, so a non-suspending emit has nowhere to put the value while a subscriber is busy. `tryEmit` never blocks or throws; it returns `false`. Use `extraBufferCapacity` and check the result."},
  {"q": "Every chargeback event must reach both the email sender and the audit writer, which run all the time, and a burst of 50 events must not drop any. Which type fits?",
   "options": ["`MutableStateFlow<Chargeback?>(null)`", "`MutableSharedFlow<Chargeback>(extraBufferCapacity = 64)` with the default `SUSPEND`", "A cold `flow { }` that each consumer collects", "`MutableSharedFlow<Chargeback>(replay = 1, onBufferOverflow = DROP_OLDEST)`"],
   "answer": 1,
   "why": "Events go to several subscribers, and none may be lost, so a SharedFlow with room for bursts and `SUSPEND` fits. A StateFlow conflates events away, a cold flow would run once per consumer instead of broadcasting, and `DROP_OLDEST` discards events when a subscriber falls behind."},
  {"q": "A live settlement dashboard shares a polling flow with `stateIn`. A page reload must not restart the polling, and nothing should poll when no dashboard is open. Which `started` value fits?",
   "options": ["`SharingStarted.Eagerly`", "`SharingStarted.Lazily`", "`SharingStarted.WhileSubscribed()`", "`SharingStarted.WhileSubscribed(5_000)`"],
   "answer": 3,
   "why": "`WhileSubscribed(5_000)` starts with the first subscriber and stops 5 s after the last leaves, so a reload within that window keeps it running. The default `WhileSubscribed()` stops at once, `Lazily` never stops, and `Eagerly` polls even before anyone opens a dashboard."},
  {"q": "From lesson 7 of this track: three dashboards each collect the same `val rates = flow { while (true) { emit(poll()); delay(1_000) } }`. How many times does `poll()` run per second?",
   "options": ["Three times: a cold flow runs once per collector", "Once: the flow is shared because it is the same object", "Once, but only for the first dashboard; the others get nothing", "It depends on the dispatcher"],
   "answer": 0,
   "why": "A cold flow's body runs separately for every collector, even if they all hold the same `Flow` object. Sharing one upstream takes `stateIn` or `shareIn`.",
   "from": "co-07"}
 ],
 "flashcards": [
  {"front": "A StateFlow collector is busy while three new values are set. What does it see next?", "back": "Only the latest one. StateFlow conflates: values a slow collector missed are skipped."},
  {"front": "What happens when you set a `MutableStateFlow` to a value equal to its current one?", "back": "Nothing. It compares with `equals`, and an equal value emits nothing."},
  {"front": "`MutableSharedFlow()` with default parameters: what does `tryEmit` return while a subscriber is busy?", "back": "`false`. There is no buffer, so the value is dropped. Add `extraBufferCapacity` and check the result."},
  {"front": "`replay` vs `extraBufferCapacity` in a MutableSharedFlow?", "back": "`replay`: how many recent values a new subscriber gets first. `extraBufferCapacity`: extra room for values slow subscribers haven't taken yet."},
  {"front": "What does `SharingStarted.WhileSubscribed(5_000)` do?", "back": "Starts the shared upstream with the first subscriber and stops it 5 s after the last subscriber leaves."},
  {"front": "How do you expose a StateFlow read-only with one property in Kotlin 2.4?", "back": "An explicit backing field: `val status: StateFlow<S>` followed by `field = MutableStateFlow(initial)`."},
  {"front": "How do you add 1 to a `MutableStateFlow<Int>` safely from many threads?", "back": "`flow.update { it + 1 }`, which retries with compare-and-set. `value = value + 1` loses updates."}
 ],
 "terms": [
  {"term": "Hot flow", "plain": "A flow that exists and produces values whether or not anyone collects it."},
  {"term": "StateFlow", "plain": "A hot flow with one current value; it conflates and skips equal values."},
  {"term": "SharedFlow", "plain": "A hot flow that broadcasts every value to every current subscriber."},
  {"term": "Conflation", "plain": "Keeping only the latest value for a slow consumer and dropping the ones in between."},
  {"term": "Replay cache", "plain": "The last few values a SharedFlow keeps and gives to each new subscriber first."},
  {"term": "SharingStarted", "plain": "The rule that tells stateIn or shareIn when to start and stop the shared upstream."},
  {"term": "Explicit backing field", "plain": "A Kotlin property whose field has a different, more specific type than the property itself."}
 ],
 "explain_back": {
  "prompt": "A teammate stores payment transitions in a `MutableStateFlow<Transition?>` so the audit writer can collect them, and the audit log is missing entries under load. Explain why, and what you would use instead.",
  "answer": "A StateFlow holds one current value, so it's built to drop history. When the audit writer is busy writing one transition and two more happen, it only gets the latest one when it's ready, and the middle one is gone. It also skips a value equal to the current one, so a repeated transition never arrives. That's right for state like \"the current status\", but transitions are events and every one matters. I'd use a MutableSharedFlow with no replay and an extraBufferCapacity big enough for bursts, keep the default SUSPEND overflow, and check what tryEmit returns from the Kafka threads so a full buffer shows up as an error instead of a lost entry. And because it's all in memory, anything that must survive a restart should also go to the outbox table or a Kafka topic."
 },
 "deeper": {
  "minutes": 10,
  "body": "`MutableSharedFlow` has a `subscriptionCount: StateFlow<Int>`. It is deliberately not conflated, so you can react to the first subscriber arriving or the last one leaving, for example to open and close a connection to a market-data feed. `SharingStarted` is an interface, and `WhileSubscribed` is written on top of exactly that count. A custom strategy can start sharing only during business hours, or only after a warm-up.\n\n`WhileSubscribed` has a second parameter, `replayExpirationMillis`, which defaults to `Long.MAX_VALUE`. It decides how long the last value stays in the replay cache after the upstream stops. Set it to 0 if a stale value is worse than none, for instance a rate that must never be shown once its feed is down.\n\n`stateIn` and `shareIn` keep a coroutine running in the scope you give them, so the scope's lifetime is the sharing's lifetime. If the upstream throws, that coroutine fails, the error goes up into the scope, and the StateFlow simply stops updating. Put a `catch` or `retryWhen` on the upstream, above `stateIn`, and decide what the subscribers should see while it recovers.\n\nkotlinx.coroutines 1.11 added two small helpers. `SharedFlow.asFlow()` returns a view that hides the hot-flow type, so callers can't rely on it being shared. And there is now an `onSubscription` overload on StateFlow that keeps the `StateFlow` type. Kotlin 2.1.20 also added common atomics such as `AtomicInt` in `kotlin.concurrent.atomics`, marked experimental. For plain counters shared between coroutines they are an alternative to a StateFlow you never collect, which lesson 10 of this track compares with `Mutex`."
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
