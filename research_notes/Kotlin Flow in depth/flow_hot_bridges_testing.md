# Hot flows in depth, bridges to other APIs, and testing flows (Kotlin 2.4.21, kotlinx.coroutines 1.11.0, Reactor 3.8.8, JDK 21)

Scope: lessons 7 and 8 of the "Kotlin Flow in depth" track. Lesson 7 covers hot flows (`MutableSharedFlow`, `StateFlow`, `stateIn`/`shareIn`, `SharingStarted`) down to what the library does inside. Lesson 8 covers bridges (`callbackFlow`, `channelFlow`, Reactive Streams, Reactor, `java.util.concurrent.Flow`, Java callers) and testing flows (`runTest`, virtual time, dispatchers, Turbine). The learner is a senior payments backend engineer who already did the coroutines track: co-07 (cold flows), co-08 ("StateFlow, SharedFlow and hot streams"), co-09 (channels, `callbackFlow`, `channelFlow`), co-10 (shared state, `runTest`, `backgroundScope`, `StandardTestDispatcher` vs `UnconfinedTestDispatcher`) and co-11 (futures, Reactor, `asFlow`/`asFlux`). These notes do not repeat that material. They give the exact rules and numbers so a learner can predict variants.

**How the claims were checked.** Every claim tagged **[Local]** was run in this session. I compiled with the Kotlin compiler `kotlin-compiler-embeddable-2.4.21` from the Gradle cache, run as `org.jetbrains.kotlin.cli.jvm.K2JVMCompiler` with `-jvm-target 21`, on OpenJDK 21.0.12.1. The classpath held kotlin-stdlib 2.4.21, kotlinx-coroutines-core-jvm / -test-jvm / -reactive / -reactor 1.11.0, reactor-core 3.8.8 and reactive-streams 1.0.4, all from the Gradle cache. I downloaded two more jars from Maven Central into the scratch folder: kotlinx-coroutines-jdk9 1.11.0 and turbine-jvm 1.2.1. Timelines use `runTest` virtual time unless marked **REAL time**, so their numbers are exact and repeat on every run. I re-ran every demo once more before writing, and all virtual-time outputs matched. Real-time numbers (races, millisecond timings) differ between runs, and the notes say so where they appear. **[Source]** means I read the file at the `1.11.0` tag on raw.githubusercontent.com (the tag exists; the paths are listed under Verified URLs). **[Docs]** means an official page I fetched in this session. **[Unverified]** means I did not check it here. The full programs and outputs are in "Demo ideas with expected outcomes".

---

## Summary

- **`MutableSharedFlow` has one buffer shared by all subscribers, of size `replay + extraBufferCapacity`.** With no subscribers, `emit` never suspends and `tryEmit` always returns `true`. Only the last `replay` values are kept; `extraBufferCapacity` is ignored. With subscribers and `SUSPEND`, `emit` suspends (and `tryEmit` returns `false`) exactly when the slowest subscriber has `replay + extraBufferCapacity` values it has not yet taken. [Source + Local]
- **Default `MutableSharedFlow()` (0, 0, SUSPEND) is a rendezvous.** `tryEmit` returns `false` whenever there is any subscriber, even one that is idle and waiting. `emit` returns only once every subscriber has taken the value. [Source + Local] This corrects co-08, which says `tryEmit` fails "whenever a subscriber is busy".
- **One slow subscriber affects everyone.** Under `SUSPEND` it slows the emitter, and with it every fast subscriber. Under `DROP_LATEST` the fast subscriber loses the dropped values too. Under `DROP_OLDEST` only the slow subscriber skips values. [Local]
- **A late subscriber gets the replay cache and then live values only.** It never gets older buffered values that slower subscribers are still working through. [Source + Local]
- **`StateFlow` compares values with `equals`, both when a value is set and in every collector.** Setting an equal value does nothing, and the old reference stays in place. A busy collector wakes up to the latest value only, so A→B→A while it is busy shows nothing new. `value = value + 1` from 8 coroutines lost more than half the updates. `update { }` lost none, but its lambda ran 1.39 million times for 800,000 updates. [Source + Local]
- **`subscriptionCount` is deliberately not conflated.** An observer sees `[0, 1, 0]` for a subscriber that came and went before the observer ran. A plain `StateFlow` doing the same 0→1→0 shows `[0]`. [Source + Local]
- **`WhileSubscribed(stopTimeoutMillis, replayExpirationMillis)`:** if the last subscriber leaves and a new one arrives within `stopTimeoutMillis`, the upstream is not restarted. After the timeout the upstream is cancelled. The next subscriber restarts it from the top, and first sees the stale cached value (for `stateIn`), or `initialValue` if `replayExpirationMillis` has passed. [Source + Local, exact virtual timelines below]
- **Reading `stateFlow.value` is not a subscription.** A `Lazily` or `WhileSubscribed` cache that request handlers only read through `.value` never starts its upstream and returns `initialValue` forever. Use `Eagerly`, or the suspend `stateIn(scope)`. [Local]
- **`shareIn`/`stateIn` buffer 64 values by default** (`max(replay, 64) - replay` extra). The upstream ran 65 `emit`s ahead of a stuck subscriber; with `buffer(0)` it ran 1 ahead. An upstream exception kills the sharing coroutine and goes to the scope's handler, while subscribers wait forever without an error. Calling `shareIn` per request leaks one sharing coroutine per call: 50 requests left 50 upstreams polling. [Source + Local]
- **`callbackFlow` without `awaitClose` throws** `IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.` (three lines, exact text below). [Source + Local] Registration happens when collection starts, so events fired before the producer coroutine runs are lost. [Local]
- **The `callbackFlow` channel holds 64 elements by default, plus one handed straight to a receiver that is already waiting.** 200 synchronous `trySend`s gave 135 failures. `conflate()` delivered `[0, 199]`. `trySendBlocking` delivered all 200, but blocked the SDK's thread for about 300 ms (REAL time). [Local]
- **`Publisher.asFlow()` requests 64 and then 64 more after every 64 collected.** `buffer(n)` changes that to `request(n)`, `buffer(0)` to `request(1)`, and `buffer(UNLIMITED)` or `conflate()` to `request(Long.MAX_VALUE)`. `Flow.asFlux()`/`asPublisher()` call `onNext` from inside `emit` and suspend the flow when the outstanding demand reaches 0. [Source + Local]
- **Reactor `Context` reaches the coroutine as `ReactorContext`, in both directions.** It needs `kotlinx-coroutines-reactor` on the classpath, because `ReactorContextInjector` is found by `ServiceLoader`. [Source + Local]
- **`kotlinx-coroutines-jdk9` exists at 1.11.0** (`org.jetbrains.kotlinx:kotlinx-coroutines-jdk9:1.11.0`, an 8.7 KB jar). It is a thin wrapper over the reactive module and reactive-streams' `FlowAdapters`. `FlowAdapters` plus `kotlinx-coroutines-reactive` does the same job without the extra artifact. [Source + Local]
- **Testing:** `advanceUntilIdle()` ignores background-only work. `advanceTimeBy(100)` does not run a task due at exactly +100 (`runCurrent()` does). A `StateFlow` collected on `StandardTestDispatcher` misses values that are set back to back. A `take(3)` on such a flow hangs until runTest's timeout. Exact error messages are below. [Source + Local]
- **Turbine:** the latest release is **1.2.1** (2025-06-11), artifact `app.cash.turbine:turbine:1.2.1`. It resolves from Maven Central in a tiny Gradle build, and Gradle upgrades its kotlinx.coroutines 1.10.2 dependencies to 1.11.0. 13 scenarios on 1.11.0 behaved as its README and source describe; the failure messages are recorded below. **Recommended as the one new test dependency** for the flows lab, with the caveats in "Notes for the lesson writer". [Local + Docs]

---

## What the learner already has (co-07 to co-11), and what lessons 7 and 8 add

| Already taught | Where | What these notes add |
|---|---|---|
| StateFlow conflates and skips equal values; SharedFlow `replay`/`extraBufferCapacity`/`onBufferOverflow`; `tryEmit` can fail | co-08 | The exact suspension rule, a table of `tryEmit` results per configuration, one buffer shared by all subscribers, the rendezvous case, late subscribers, identity on an equal set, `update` lambda re-runs |
| `stateIn`/`shareIn`, the three `SharingStarted` values, `replayExpirationMillis`, `subscriptionCount` not conflated | co-08 (section 3 and "deeper") | Exact virtual timelines for leave and rejoin within and after the timeout; `.value` not subscribing; the default 64 buffer; failure behaviour; leaks; internals (slots, ring buffer, command flow) |
| `callbackFlow` + `awaitClose` + `trySend`, buffer 64 | co-09 section 4 | The exact error text; the registration race; 64 + 1; `conflate`/`DROP_OLDEST` results; `trySendBlocking`; a compile error for `send` |
| `mono {}`, `awaitSingle`, `Publisher.asFlow()`, `Flow.asFlux()`, `ReactorContext` exists | co-11 section 2 | Exact `request(n)` numbers; how `emit` maps to `onNext` and suspension; threads (`Unconfined`, `DefaultExecutor`); context both ways; the JDK `Flow` bridge; Java faces |
| `runTest`, virtual time, `backgroundScope`, Standard vs Unconfined, "Turbine exists, 3 s wall-clock timeout" | co-10 sections 3-4 | The `advanceTimeBy` boundary; `advanceUntilIdle` vs background work; StateFlow conflation in tests; exact `UncompletedCoroutinesError` messages; Turbine API, version, behaviour, recommendation |

---

## Part A. Lesson 7: hot flows in depth

### A1. `MutableSharedFlow(replay, extraBufferCapacity, onBufferOverflow)`: when `emit` suspends and `tryEmit` fails

**Signature (1.11.0)** [Source: `kotlinx-coroutines-core/common/src/flow/SharedFlow.kt`]
```kotlin
public fun <T> MutableSharedFlow(
    replay: Int = 0,
    extraBufferCapacity: Int = 0,
    onBufferOverflow: BufferOverflow = BufferOverflow.SUSPEND
): MutableSharedFlow<T>
```
- The constructor checks `replay >= 0` and `extraBufferCapacity >= 0`. A drop policy needs some buffer: `MutableSharedFlow<Int>(onBufferOverflow = DROP_OLDEST)` throws `IllegalArgumentException: replay or extraBufferCapacity must be positive with non-default onBufferOverflow strategy DROP_OLDEST`. [Source + Local]
- The internal buffer capacity is `replay + extraBufferCapacity`, coerced to `Int.MAX_VALUE` on overflow. It is **one buffer for all subscribers**; there is no queue per subscriber. [Source]
- `emit(v)` is literally `if (tryEmit(v)) return; emitSuspend(v)`. `tryEmit` is the fast path, and `emit` suspends only when `tryEmit` would fail. [Source]

**The rule, from `tryEmitLocked`** [Source]
1. **No subscribers:** the call always succeeds. The value goes into the replay cache if `replay > 0` (displacing the oldest) and is otherwise dropped. `extraBufferCapacity` and the overflow policy play no part. KDoc: "In the absence of subscribers emitter never suspends despite `BufferOverflow.SUSPEND` option". [Source + Local: `replay=2, extraBufferCapacity=10`, 5 emits with no subscriber, gave `replayCache=[4, 5]`]
2. **With subscribers:** the buffer is "full" when `bufferSize >= bufferCapacity && minCollectorIndex <= replayIndex`, that is, when **the slowest subscriber has `replay + extraBufferCapacity` values it has not taken yet**. What happens then depends on the policy:
   - `SUSPEND`: `tryEmit` returns `false`, and `emit` queues an `Emitter` object in the same array and suspends.
   - `DROP_LATEST`: returns `true` and simply drops the new value, **for every subscriber**.
   - `DROP_OLDEST`: enqueues the value and drops the oldest one. Subscribers still pointing at the dropped index are moved forward, so they skip it.
3. A subscriber "takes" a value when it reads it, before it runs the `collect` lambda (`slot.index = index + 1` happens in `tryTakeValue`). A value that a busy subscriber is still processing no longer counts against the buffer. [Source]

**Measured** [Local, demo D1; one subscriber subscribed and waiting, then `tryEmit(1..6)` called back to back on `StandardTestDispatcher`, so the subscriber cannot take anything between calls]

| Configuration | `tryEmit(1..6)` results | What the subscriber then received |
|---|---|---|
| `MutableSharedFlow()`, **no** subscribers | true ×6 | (nobody) |
| `MutableSharedFlow()`, 1 idle subscriber | **false ×6** | nothing |
| `extraBufferCapacity = 2` | true, true, false ×4 | 1, 2 |
| `replay = 2` | true, true, false ×4 | 1, 2 |
| `replay = 1, extraBufferCapacity = 2` | true ×3, false ×3 | 1, 2, 3 |
| `extra = 2, DROP_OLDEST` | true ×6 | **5, 6** |
| `extra = 2, DROP_LATEST` | true ×6 | **1, 2** |

On a multi-threaded dispatcher a real subscriber can take values between `tryEmit` calls, so the counts can be higher there. The rule stays the same. [Unverified for real threads: inferred from the source rule]

**The `emit` timeline** [Local, D1, virtual ms; one subscriber that takes 100 ms per item]
- Default `MutableSharedFlow()`: `sub got 1` then `emit(1) returned` at t=0; `emit(2)` returns at t=100, `emit(3)` at 200, and so on. Each `emit` waits until the subscriber has **taken** the value (picked it up), not until it has finished processing it.
- `extraBufferCapacity = 2`: `emit(1)` and `emit(2)` return at t=0. The subscriber takes 1, so `emit(3)` also returns at t=0. Then `emit(4)` returns at t=100 and `emit(5)` at t=200.

**One slow subscriber, one fast one** [Local, D1b `H6FastSlow`; `extraBufferCapacity = 2`, emit 1..6 ten ms apart, slow subscriber takes 1000 ms per item]
```
SUSPEND:     fast=[1, 2, 3, 4, 5, 6] slow=[1, 2, 3, 4, 5, 6] emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=1000, 5@t=2000, 6@t=3000]
DROP_OLDEST: fast=[1, 2, 3, 4, 5, 6] slow=[1, 5, 6]          emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=30, 5@t=40, 6@t=50]
DROP_LATEST: fast=[1, 2, 3]          slow=[1, 2, 3]          emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=30, 5@t=40, 6@t=50]
```
So the overflow policy is a decision about **everybody**, not only the slow subscriber. For an event bus where one consumer can stall (an audit writer behind a slow database), `DROP_LATEST` silently costs the fast consumers events too. [Local]

**Thread safety and cost.** "All methods of shared flow are thread-safe … Shared flow implementation uses a lock to ensure thread-safety, but suspending collector and emitter coroutines are resumed outside of this lock … emitting has `O(N)` cost, where `N` is the number of subscribers." [Source: SharedFlow.kt KDoc]

### A2. What a subscriber that arrives late sees

- It starts at `replayIndex` (`updateNewCollectorIndexLocked` returns `replayIndex`), so it gets the replay cache first and then live values. [Source]
- `replay = 0`: anything emitted before it subscribed is gone. Demo: five emits with no subscriber, then subscribe, then `emit(6)` gives `[6]`. [Local, D2]
- **It does not get the buffered backlog of slower subscribers.** Demo with `replay = 1, extra = 10`: S1 is stuck on item 1 while 1..5 are emitted. S2 joins and gets only `5`, while S1 still works through 2, 3, 4, 5. [Local, D2]
- `resetReplayCache()` empties the replay cache for **new** subscribers; existing subscribers keep their buffered values. It is `@ExperimentalCoroutinesApi`. On `MutableStateFlow` it throws `UnsupportedOperationException: MutableStateFlow.resetReplayCache is not supported`. [Source + Local]
- `SharedFlow.collect` returns `Nothing` and never completes. Only truncating operators (`take`, `takeWhile`, `first`) make collection finish. The KDoc guarantees "by the time the first suspension happens, `collect` has already subscribed". [Source]

### A3. `StateFlow`: equality conflation, slow collectors, races, `compareAndSet`

**What it is, exactly.** The KDoc says: "MutableStateFlow(initialValue) is a shared flow with the following parameters: `MutableSharedFlow(replay = 1, onBufferOverflow = BufferOverflow.DROP_OLDEST)` … `shared.tryEmit(initialValue)` … `val state = shared.distinctUntilChanged()`". The implementation, though, is a separate class, `StateFlowImpl`, with one atomic state and no buffer. [Source: StateFlow.kt]

**Conflation happens in two places** [Source: StateFlow.kt]
1. **On set:** `updateState` does `if (oldState == newState) return true // Don't do anything if value is not changing`. Nobody wakes up, **and the old reference is kept**. Demo: `s.value = second` where `second == first` but `second !== first` leaves `s.value === first`, so `true`. [Local, D16]
2. **In each collector:** the collect loop re-reads `_state.value` when it wakes up and emits only `if (oldState == null || oldState != newState)`. A busy collector never sees the intermediate values, and it never sees a value that came back to what it last saw. [Source + Local]

**Measured** [Local, D3, virtual ms]
- Equal value: the initial `Rate(EURUSD, 1.0850)`, then an equal `Rate(EURUSD, 1.0850)` (skipped), then `Rate(EURUSD, 1.08500)` (BigDecimal scale differs, so `equals` is false and it **is** emitted), then `1.0851`. The collector saw 3 values.
- Slow collector (100 ms per item) with updates every 25 ms, 1..10: it saw `[t=0:0, t=100:3, t=200:7, t=300:10]`.
- A→B→A while busy: `AUTHORIZED` → `CAPTURED` → `AUTHORIZED` within 20 ms while the collector is in a 100 ms step: it saw only `[t=0:AUTHORIZED]`. The same three sets with an Unconfined collector that never suspends: `[AUTHORIZED, CAPTURED, AUTHORIZED]`.
- In-place mutation: holding a `MutableList` in a `StateFlow`, then `list += "p2"; state.value = list`, emits nothing (it is equal to itself). `state.value = list + "p3"` emits. The collector saw `[[p1], [p1, p2, p3]]`. [Local, D16]
- `emit`/`tryEmit` on a `MutableStateFlow` just set `value`: they never suspend, and `tryEmit` always returns `true`, even with a collector stuck for 1,000,000 ms. [Source + Local]

**Races** [Local, D3/D16, REAL threads, 4 CPUs, 8 coroutines × 100,000 increments on `Dispatchers.Default`]
- `racy.value = racy.value + 1`: 356,783 / 338,953 / 343,110 in one session, and 397,154 / 376,352 / 349,669 on the re-run, against an expected 800,000. The read and the write are each atomic; the pair is not.
- `safe.update { it + 1 }`: 800,000 every time.
- `update` is a CAS loop: `while (true) { val prev = value; val next = function(prev); if (compareAndSet(prev, next)) return }`. "[function] may be evaluated multiple times". Measured: **1,390,485 lambda calls for 800,000 successful updates**, so side effects inside `update {}` (logging, metrics, I/O) run more than once. [Source + Local]
- `compareAndSet(expect, update)` compares with `equals`: `cas(10→11)` gives true, `cas(10→12)` with a stale expect gives false, and `cas(11→11)` gives true but changes nothing and emits nothing. The KDoc says: "If both expect and update are equal to the current value, this function returns true, but it does not actually change the reference". `getAndUpdate`/`updateAndGet` return the old or new value. [Source + Local]

**Update cost.** "updating a value has O(N) cost, where N is the number of active subscribers". Concurrent updates are fired by "a sort of simple flat combining": a sequence number that is odd while an update is in progress. A second writer that arrives mid-update just bumps the sequence, and the first writer loops to deliver the newest value. [Source]

### A4. `subscriptionCount`

- It is a `StateFlow<Int>` on `MutableSharedFlow` (and therefore on `MutableStateFlow`). It is **not conflated**: internally it is `SubscriptionCountStateFlow : SharedFlowImpl<Int>(1, Int.MAX_VALUE, BufferOverflow.DROP_OLDEST)`. The KDoc explains why: "if a single subscriber appeared and immediately left, those collecting subscriptionCount could fail to notice it". [Source: AbstractSharedFlow.kt, SharedFlow.kt]
- It is created lazily on first access. Subscribers that come and go before anyone has read `subscriptionCount` are never recorded. [Source + Local: my first demo got `[0]` for exactly this reason. After reading it first and letting the observer subscribe, it got `[0, 1, 0]`]
- Measured: the observer subscribed and waiting, then a subscriber joined and left before the observer ran again: `[0, 1, 0]`. A plain `MutableStateFlow` doing 0→1→0 under the same conditions: `[0]`. [Local, D4]
- `WhileSubscribed` and `Lazily` are built on exactly this count (see A5). [Source]

### A5. `shareIn`, `stateIn` and `SharingStarted`

**Signatures (1.11.0)** [Source: `flow/operators/Share.kt`, `flow/SharingStarted.kt`]
```kotlin
public fun <T> Flow<T>.shareIn(scope: CoroutineScope, started: SharingStarted, replay: Int = 0): SharedFlow<T>
public fun <T> Flow<T>.stateIn(scope: CoroutineScope, started: SharingStarted, initialValue: T): StateFlow<T>
public suspend fun <T> Flow<T>.stateIn(scope: CoroutineScope): StateFlow<T>
public fun interface SharingStarted {
    public companion object {
        public val Eagerly: SharingStarted
        public val Lazily: SharingStarted
        public fun WhileSubscribed(stopTimeoutMillis: Long = 0, replayExpirationMillis: Long = Long.MAX_VALUE): SharingStarted
    }
    public fun command(subscriptionCount: StateFlow<Int>): Flow<SharingCommand>
}
public fun SharingStarted.Companion.WhileSubscribed(stopTimeout: Duration = Duration.ZERO, replayExpiration: Duration = Duration.INFINITE): SharingStarted
public enum class SharingCommand { START, STOP, STOP_AND_RESET_REPLAY_CACHE }
```

**What the operator builds** [Source: Share.kt `launchSharing`]
- `shareIn` creates a `MutableSharedFlow(replay, extraBufferCapacity = max(replay, 64) - replay, SUSPEND)`. `stateIn` creates a `MutableStateFlow(initialValue)`. Both then launch **one** coroutine in `scope` that collects the upstream into it. They return a read-only wrapper that "keeps a strong reference to the job". (1.11.0 fixed "an R8 optimization leading to shareIn/stateIn coroutines getting garbage-collected", #4646.) [Source + CHANGES.md]
- `Eagerly` launches the sharing coroutine with `CoroutineStart.DEFAULT` (dispatched), so subscribers created right after `shareIn` in the same dispatcher get a chance to subscribe before the upstream starts. Every other strategy uses `CoroutineStart.UNDISPATCHED`, so it can observe those subscriptions immediately (the source comment uses `flow.shareIn(...); flow.take(1)` as its example). [Source]
- `Eagerly`: `upstream.collect(shared)` straight away. `Lazily`: `shared.subscriptionCount.first { it > 0 }`, then collect for ever. Anything else: `started.command(shared.subscriptionCount).distinctUntilChanged().collectLatest { START -> upstream.collect(shared); STOP -> {}; STOP_AND_RESET_REPLAY_CACHE -> resetReplayCache() or tryEmit(initialValue) }`. Because this is `collectLatest`, a `STOP` command cancels the running `upstream.collect`. [Source]
- `WhileSubscribed.command` is `subscriptionCount.transformLatest { count -> if (count > 0) emit(START) else { delay(stopTimeout); if (replayExpiration > 0) { emit(STOP); delay(replayExpiration) }; emit(STOP_AND_RESET_REPLAY_CACHE) } }.dropWhile { it != START }.distinctUntilChanged()`. A subscriber that comes back within the timeout cancels the pending `delay` (that is what `transformLatest` does) and emits `START` again, which `distinctUntilChanged` swallows. **So the upstream is not restarted.** [Source]

**Exact timelines** [Local, D4; the upstream emits `run*100 + i` every 1000 virtual ms and logs START/STOP; `stateIn(initialValue = -1)`. In the `WhileSubscribed` rows, subscriber A joins at 0, leaves at 2500, rejoins at 4000, leaves at 6000 and rejoins at 14000. The `Lazily` and `Eagerly` rows use their own short scripts (D4)]

| Strategy | Upstream START/STOP | What A sees when it rejoins |
|---|---|---|
| `WhileSubscribed(5000)` | START #1 at 0, **no stop during the 1.5 s gap**, STOP #1 at 11000 (6000 + 5000), START #2 at 14000 | at 4000: `104` (run 1 kept going; `value` was 103 while A was away). At 14000: the stale `111` first, then `200` from the new run |
| `WhileSubscribed(5000, replayExpirationMillis = 0)` | same as above | at 14000: `-1` (reset to `initialValue`), then `200` |
| `WhileSubscribed()` (stop 0) | STOP #1 at 2500, START #2 at 4000, STOP #2 at 6000, START #3 at 14000 | at 4000: stale `102`, then `200` |
| `Lazily` | START at the first subscriber (t=1000); never stops | after A leaves at 2500, `value` keeps changing (104 at 5500) |
| `Eagerly` (`shareIn`, replay 0) | START at 0, before any subscriber | A joins at 2500 and first gets `103` at 3000; everything before that was dropped |

- **The upstream always restarts from the top.** It is a cold flow collected again, so a `runningFold` or a counter starts over (run #2 emits `200`, `201`, and so on). [Local]
- For `shareIn`, `replayExpirationMillis = 0` empties the replay cache once sharing stops: `replayCache=[2]` while subscribed, `[]` after the last subscriber left. With the default (`Long.MAX_VALUE`) it stays `[2]`. [Local, D16]
- `WhileSubscribed` with negative values throws `IllegalArgumentException("stopTimeout(... ms) cannot be negative")`. `toString()` prints, for example, `SharingStarted.WhileSubscribed(stopTimeout=5000ms)`. `equals`/`hashCode` exist "to facilitate testing, not documented in public contract". [Source + Local for `toString`]
- Custom strategy, from the KDoc: `SharingStarted { count -> count.map { if (it >= threshold) START else STOP } }`. [Source + Local, D6 Kafka case]

**Completion and errors** [Source: Share.kt KDoc + Local]
- "Normal completion of the upstream flow has no effect on subscribers, and the sharing coroutine continues to run." For `Eagerly` and `Lazily` the sharing coroutine **ends** once a finite upstream completes. For `WhileSubscribed`, the command-flow collection keeps it alive until the scope is cancelled. This matters in tests: `flowOf(1,2,3).stateIn(this, Eagerly, 0)` inside `runTest` passed, and the same with `WhileSubscribed()` failed with `UncompletedCoroutinesError`. [Local, D14 #8]
- "Any exception in the upstream flow terminates the sharing coroutine without affecting any of the subscribers, and will be handled by the scope." Measured: the upstream emits 1 and 2, then throws `IOException("feed reset")`. The subscriber got `[1, 2]` and was **still waiting** at t=1000. The scope's `CoroutineExceptionHandler` saw `IOException: feed reset`. A `SupervisorJob` scope stayed active. [Local, D5] Put `retry`/`retryWhen`/`catch` **above** `shareIn`.
- **`.value` is not a subscription.** Each `stateIn` below was read three times through `.value` only, at t=3500:
  - `WhileSubscribed(5000)`: `[null, null, null]`, upstream fetches = 0.
  - `Lazily`: `[null, null, null]`, fetches = 0.
  - `Eagerly`: `[1.0854, 1.0854, 1.0854]`, fetches = 4. [Local, D6]

**Default buffering in `shareIn`** [Source + Local, D5]
- The source sets `defaultExtraCapacity = replay.coerceAtLeast(Channel.CHANNEL_DEFAULT_CAPACITY) - replay`, and `CHANNEL_DEFAULT_CAPACITY` is 64 (system property `kotlinx.coroutines.channels.defaultBuffer`). A `buffer(...)`/`conflate()` placed just before `shareIn` is fused into the shared flow instead of adding a channel: `buffer(b).shareIn(scope, started, r)` means `replay = r, extraBufferCapacity = b`.
- Measured with one stuck subscriber, counting how many upstream `emit()` calls returned:

| Configuration | `emit()` calls that returned |
|---|---|
| `shareIn(replay=0)` | **65** |
| `buffer(0).shareIn(replay=0)` | 1 |
| `buffer(10).shareIn(replay=0)` | 11 |
| `shareIn(replay=100)` | 101 |

### A6. The suspend overload `stateIn(scope)`

- It launches the upstream in `scope` with no `started` parameter. The upstream then runs until it completes or the scope is cancelled, much like `Eagerly`. The call **suspends until the first value**. It then returns a `StateFlow` that holds that value. [Source]
- Measured [Local, D5]:
  - An upstream whose first value arrives after 300 ms: `stateIn(scope)` returned at t=300 with `value=timeout=2s`, and at t=1800 the value was `timeout=3s`.
  - An empty flow throws `NoSuchElementException: Flow is empty`.
  - An upstream that fails before its first value: the caller gets the `IOException`, **and the scope is cancelled** (`scope still active? false`). The source does `result.completeExceptionally(e); throw e // But still cancel the scope`.
- Server use: load a config value at startup. Fail fast if it cannot load, then keep it fresh. Give it its own child scope (or a `SupervisorJob` child) if one failed config should not cancel the application scope. [Unverified, design advice following from the measured cancellation]

### A7. Scope leaks

- The sharing coroutine lives as long as its scope. With `Eagerly` and `Lazily` it never stops while the scope is alive. After A left at 2500, a `Lazily` upstream was still polling at 5500. [Local, D4]
- **`shareIn` per call** is the classic leak. `fun ratesForRequest() = upstream.shareIn(appScope, Lazily, 1)`, called by 50 "requests" that each read one value, left **50 sharing coroutines alive** and **500 upstream polls after 10 s** (50 × 10). After `appScope.cancel()`: 0 alive. [Local, D5] Create the shared flow once, in a field or a singleton, and never in a function that each request calls.
- `GlobalScope` or `CoroutineScope(Dispatchers.Default)` created ad hoc and never cancelled behave the same way: nothing ever stops the upstream. The fix is a scope with a lifecycle (Quarkus `@Shutdown`/`@PreDestroy`, Spring `DisposableBean`) that is cancelled on shutdown. [Unverified, framework hooks not checked in this session]
- A request-scoped `scope` is the opposite bug: the sharing stops when the first request ends. [Unverified, follows from "sharing lives in the scope", Source]

### A8. Internals at a high level (slots and the buffer array)

[Source: `flow/internal/AbstractSharedFlow.kt`, `flow/SharedFlow.kt`, `flow/StateFlow.kt`; Local reflection demo D6. Field names are implementation details and may change in any release.]
- **Slots.** Every collector gets a *slot* object from an array kept by `AbstractSharedFlow`. The array is allocated lazily with size 2 and doubles when full (`curSlots.copyOf(2 * curSlots.size)`). Freed slots are reused. Measured: slots array length 2 for 1-2 subscribers, 4 for 3-4, 8 for 5. The array starts as `null` and is not created until the first subscriber. [Source + Local]
  - A `SharedFlowSlot` holds `index` (the next value this collector will read, `-1` = free) and `cont` (its suspended continuation).
  - A `StateFlowSlot` holds one atomic state: `null` (free), `NONE`, `PENDING` (a new value is waiting), or a suspended continuation. A `StateFlow` update just runs `makePending()` on every slot. Nothing is copied, which is why the KDoc calls `StateFlow` "allocation-free". [Source]
- **The buffer array** (SharedFlow only) is a ring buffer, allocated lazily with size 2 and doubled when needed, always a power of two. Positions are absolute `Long` indexes mapped with `index.toInt() and (size - 1)`. It holds the buffered values *and* queued `Emitter` objects (suspended `emit` calls) one after another. [Source] Measured with `replay = 3, extra = 2` and no subscribers: buffer array length 2 after 1 emit and 4 after 10 emits, `replayCache=[8, 9, 10]`. [Local]
- The ASCII diagram from the source comment in `SharedFlowImpl` (abridged: a few annotation lines removed):
  ```
                    buffered values
               /-----------------------\
                            replayCache      queued emitters
                            /----------\/----------------------\
           +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
           |   | 1 | 2 | 3 | 4 | 5 | 6 | E | E | E | E | E | E |   |   |   |
           +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
                 ^           ^           ^                      ^
                head         |      head + bufferSize     head + totalSize
       index of the slowest  |    index of the fastest
        possible collector   |     possible collector
                       replayIndex == new collector's index
  ```
  `head = minOf(minCollectorIndex, replayIndex)`. When the slowest collector moves forward, `head` moves, the old cells are nulled, and queued emitters are resumed (their values move into the buffer). [Source]
- **Lock.** Every state change happens under `synchronized(this)`. Continuations to resume are collected into an array and resumed **after** the lock is released. [Source]

### A9. Server-side use cases

**A cached FX rate shared by many requests**
- Handlers read `rates.value` and never collect, so start it with `Eagerly` (or the suspend `stateIn`). `Lazily`/`WhileSubscribed` would never start (A5, [Local]).
- Use `stateIn(appScope, SharingStarted.Eagerly, initialValue = null)`, with `retryWhen` above it so that a feed failure does not kill the sharing coroutine for good (A5).
- Remember that `equals` decides whether an update counts. A `BigDecimal` with a different scale is a "new" rate; a rate object with the same fields is not (A3, [Local]).
- Every subscriber (for example an SSE endpoint pushing rates to dashboards) is a slot. `StateFlow` updates cost O(N subscribers) but allocate nothing (A8).

**A config value**
- `val config: StateFlow<Config> = configSource.stateIn(appScope)`, the suspend overload at startup. It fails startup on `NoSuchElementException`/`IOException` and cancels the scope (A6, [Local]).
- Change listeners collect `config` and so get only *distinct* values (A3).

**A Kafka consumer shared by several handlers** [Local, D6, virtual time; `records` is a `flow { while (true) { delay(100); emit("rec-${offset++}") } }` standing in for a poll loop; `shareIn(replay = 0)`; the fraud handler subscribes at 250 ms and the ledger handler at 500 ms]
```
Eagerly:                             fraud=[rec-2, rec-3, rec-4, rec-5, rec-6] ledger=[rec-5, rec-6]
WhileSubscribed():                   fraud=[rec-0, rec-1, rec-2, rec-3, rec-4] ledger=[rec-2, rec-3, rec-4]
custom: start when >= 2 subscribers: fraud=[rec-0, rec-1]                      ledger=[rec-0, rec-1]
```
- With `replay = 0`, records polled before a handler subscribes are **lost to that handler**. A custom `SharingStarted` that waits for N subscribers fixes the start-up race. [Local]
- `SUSPEND` (the default for `shareIn`) makes the poll loop wait for the slowest handler, which is the backpressure you want for Kafka. A drop policy would silently lose records. [Source + Local behaviour of A1]
- **Offsets** [Unverified, design inference, not run against Kafka]: `shareIn` separates polling from processing. Committing offsets after `poll()` therefore acknowledges records the handlers may not have processed yet (at-most-once on a crash). Commit only after every handler is done with a record, or give each handler its own consumer group. The Kafka `KafkaConsumer` is documented as not safe for multi-threaded access, so the poll loop must stay on one thread, for example `flowOn(singleThreadDispatcher)` [Unverified: Kafka Javadoc not fetched in this session].


---

## Part B. Lesson 8, first half: bridges

### B1. `callbackFlow` and `awaitClose`

**Signatures (1.11.0)** [Source: `flow/Builders.kt`, `channels/Produce.kt`]
```kotlin
public fun <T> callbackFlow(block: suspend ProducerScope<T>.() -> Unit): Flow<T>
public fun <T> channelFlow(block: suspend ProducerScope<T>.() -> Unit): Flow<T>
public suspend fun ProducerScope<*>.awaitClose(block: () -> Unit = {})
public interface ProducerScope<in E> : CoroutineScope, SendChannel<E> { public val channel: SendChannel<E> }
```
- Both builders are cold: the block runs once per collection, in a producer coroutine started when collection starts. They use a channel with `Channel.BUFFERED` (64) capacity and `SUSPEND`, and a following `buffer()`, `flowOn()` or `conflate()` is **fused** into that one channel. [Source] (`callbackFlow{}.buffer(UNLIMITED)` gave 0 `trySend` failures, so the fused channel really is unlimited [Local, D7].)
- **The exact error when `awaitClose` is missing** [Source: `CallbackFlowBuilder.collectTo`; Local, D7]. The check is `if (!scope.isClosedForSend) throw IllegalStateException(...)`, run once the block returns:
  ```
  java.lang.IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.
  Otherwise, a callback/listener may leak in case of external cancellation.
  See callbackFlow API documentation for the details.
  ```
  - It is thrown only if the block returns while the channel is still open. A block that closes the channel itself (`close()` before returning) does not throw. [Source]
  - It is thrown even if the block launched children that would send later: `callbackFlow { launch { send(...) } }` throws. The same shape with `channelFlow` completes normally, once its children are done, because `channelFlow` has no such check. Measured: `channelFlow { launch { send(quote("north", 300)) }; launch { send(quote("east", 100)) } }.toList()` gave `[east:100ms, north:300ms] at t=300`. [Source + Local, D9]
- `awaitClose` is `suspendCancellableCoroutine { invokeOnClose { cont.resume(Unit) } }` wrapped in `try { } finally { block() }`. The cleanup therefore runs whether the channel was closed by the SDK (`close()`, `close(cause)`) or by the collector going away (`take(n)`, cancellation). It must be called from the producer coroutine itself: `check(coroutineContext[Job] === this) { "awaitClose() can only be invoked from the producer context" }`. [Source]
- Measured with a made-up payment gateway SDK (`register(listener): Registration`, with `onEvent`/`onError`/`onClosed`) [Local, D7]:
  - `take(2)`: unregistered (`listeners=0`), and the collector got 2 events.
  - SDK `onError` → `close(IOException)`: the collector caught `IOException: gateway connection lost`, and unregister ran first.
  - SDK `onClosed` → `close()`: the flow completed normally with the events so far.
- **Registration race.** `launch { gw.events().collect { } }; yield(); gw.fire(e)` lost the event (`fired with listeners=0`). The producer coroutine that registers the listener had not run yet. Tests must wait for registration (Turbine's `test {}` does this: see C6), and production code must not assume that "collecting" means "registered". [Local, D7/D9]
- "The callback register/unregister methods provided by an external API must be thread-safe, because awaitClose block can be called at any time due to asynchronous nature of cancellation, even concurrently with the call of the callback." [Source: callbackFlow KDoc]
- For a callback that fires **once**, the KDoc says: "For single-shot callbacks use suspendCancellableCoroutine." [Source]

### B2. `trySend` vs `send` vs `trySendBlocking`, and the buffer for a fast callback

- `send` is `suspend`. Calling it from a plain listener lambda does not compile in 2.4.21: `error: suspension functions can only be called within coroutine body.` [Local, D7 compile check]
- `trySend(e): ChannelResult<Unit>` never blocks. It fails when the buffer is full, and after the channel is closed: `isSuccess=false isClosed=true result=Closed(kotlinx.coroutines.channels.ClosedSendChannelException: Channel was closed)`. The result **must be checked**; ignoring it is silent loss. [Local, D7]
- **The burst test** [Local, D7]: the SDK fires 200 events synchronously inside the `callbackFlow` block, before the collector runs. The collector was already suspended in `receive()`.

| Buffer | `trySend` failures | Collector got |
|---|---|---|
| default (64, SUSPEND) | **135 of 200** (65 accepted: 64 buffered + 1 handed straight to the waiting receiver) | 64 (then cancelled by `take(64)`) |
| `.buffer(Channel.UNLIMITED)` | 0 | 200 |
| `.conflate()` | 0 | **`[0, 199]`**: the first went straight to the waiting receiver, then the last one stayed in the single slot |
| `.buffer(10, DROP_OLDEST)` | 0 | `[0, 190, 191, …, 199]` |

- `trySendBlocking(e)` is `trySend` with a fallback of `runBlocking { send(e) }`: "this function should not be used from coroutine". It blocks the **calling (SDK) thread** until there is room, and it throws `InterruptedException` if that thread is interrupted. [Source: `kotlinx-coroutines-core/concurrent/src/channels/Channels.kt`]
- Measured with an SDK thread pushing 200 events and a collector taking 2 ms per event [Local, D8, REAL time, one run]:
  - `trySend`: the SDK thread was done in 5 ms with 134 failures; the collector received 66.
  - `trySendBlocking`: the SDK thread took 297-306 ms (two runs) with 0 failures; the collector received 200.
- How to choose:
  - Use `trySend` plus an explicit policy (`buffer(n, DROP_OLDEST)` for telemetry, `conflate()` for "latest status" feeds) on an SDK thread that must never block, such as a Netty event loop or a Kafka client callback thread [Unverified: specific SDK threading rules not checked].
  - Use `trySendBlocking` when the SDK runs your callback on its own worker thread and blocking it is how you push back (for example a JDBC-style poller).
  - Use `buffer(UNLIMITED)` only when the producer is bounded.
- The default capacity can be changed JVM-wide with `-Dkotlinx.coroutines.channels.defaultBuffer=N` (`Channel.DEFAULT_BUFFER_PROPERTY_NAME`). [Source: Channel.kt] Prefer an explicit `buffer(...)` at the call site.

### B3. `channelFlow`

- `channelFlow` is the same machinery without the `awaitClose` check. It is for *your own* concurrent producers: merging two acquirers' quote streams, fanning in from `launch` children. "The resulting flow completes as soon as the code in the block and all its children completes." [Source + Local, D9]
- `send` inside it suspends on a full buffer, which is real backpressure between coroutines. `ProducerScope` is safe to use from several coroutines at once ("This builder ensures thread-safety and context preservation"). [Source]

### B4. Bridging listener-style and JDK async APIs

**A payment-gateway listener** (made-up SDK): the code is in D7, and its behaviour under `take`, error and close is in B1.

**The JDK `HttpClient`** [Local, D12, a local `com.sun.net.httpserver.HttpServer` on 127.0.0.1 streaming 5 chunked lines 50 ms apart, REAL time]
- `client.sendAsync(req, BodyHandlers.ofPublisher())` returns `CompletableFuture<HttpResponse<Flow.Publisher<List<ByteBuffer>>>>`. That is two bridges in one call:
  - The future completes once, when the headers arrive. Use `kotlinx.coroutines.future.await()` (single-shot). It answered `status=200 after 174 ms (headers only)` on the first run and after 95 ms on the re-run.
  - The body is a `java.util.concurrent.Flow.Publisher` (multi-shot). Use `kotlinx.coroutines.jdk9.asFlow()`. The chunks arrived about 50 ms apart (198, 209, 260, 309, 360 ms on the first run; 110, 132, 182, 233, 283 ms on the re-run), so they were streamed, not buffered until the end. The body was `[batch-1, …, batch-5]`.
- Demand from the collector (64 at a time by default) becomes `Flow.Subscription.request(n)` on the HttpClient body publisher. That is how a slow collector slows the socket read [Source for the request mapping; Unverified: HttpClient's internal flow control was not measured].
- Wrapping `sendAsync`'s future in `callbackFlow` would be wrong: a single result belongs to `await()`/`suspendCancellableCoroutine`. [Source: callbackFlow KDoc says single-shot callbacks use `suspendCancellableCoroutine`]

### B5. Reactive Streams and Reactor interop (kotlinx-coroutines-reactive / -reactor 1.11.0)

**Signatures** [Source: `reactive/kotlinx-coroutines-reactive/src/ReactiveFlow.kt`, `reactive/kotlinx-coroutines-reactor/src/ReactorFlow.kt`, `ReactorContext.kt`; Local `javap`]
```kotlin
// kotlinx.coroutines.reactive
public fun <T : Any> Publisher<T>.asFlow(): Flow<T>
@JvmOverloads public fun <T : Any> Flow<T>.asPublisher(context: CoroutineContext = EmptyCoroutineContext): Publisher<T>
// kotlinx.coroutines.reactor
@JvmOverloads public fun <T : Any> Flow<T>.asFlux(context: CoroutineContext = EmptyCoroutineContext): Flux<T>
public class ReactorContext(public val context: Context) : AbstractCoroutineContextElement(ReactorContext)
public fun ContextView.asCoroutineContext(): ReactorContext
```
- **There is no `Flux.asFlow()` of its own.** A `Flux` is a `Publisher`, so `flux.asFlow()` is `kotlinx.coroutines.reactive.asFlow` (the import learners need). The extra `kotlinx.coroutines.reactor.FlowKt.asFlux(Flow)` in the jar is a synthetic, `@Deprecated` binary-compatibility bridge (`asFluxDeprecated`), not something to call. [Local: `javap -v` of both jars]
- Element types must be non-null (`T : Any`). Reactive Streams forbids `null` elements. [Source]
- The reactor module's 1.11.0 pom declares `reactor-core` **3.4.1** (compile), and `gradle.properties` at the tag has `reactor_version=3.4.1`. The labs pin 3.8.8, and Gradle picks the higher version. All Reactor demos here ran on 3.8.8. [Source + Local]

**`Publisher.asFlow()`: how the collector's demand becomes `request(n)`** [Source: `PublisherAsFlow.requestSize`, `collectImpl`; Local, D10, `Flux.range(1, 300)` with `doOnRequest` logging]
- In the source, `requestSize` is `Long.MAX_VALUE` for any non-SUSPEND overflow policy, 1 for `RENDEZVOUS`, `Long.MAX_VALUE` for `UNLIMITED`, 64 (`CHANNEL_DEFAULT_CAPACITY`) for `BUFFERED`, and otherwise the capacity. `onSubscribe` calls `request(requestSize)`, and the collect loop calls `request(requestSize)` again **after every `requestSize` elements emitted downstream** (`if (++consumed == requestSize) { consumed = 0; subscriber.makeRequest() }`). Elements wait in a channel of that capacity; `onNext` uses `trySend` and `require`s success.

| Flow side | Requests observed |
|---|---|
| `asFlow()` | `request(64)` after 0, 64, 128, 192, 256, then `complete` |
| `asFlow().buffer(10)` | `request(10)` every 10 |
| `asFlow().buffer(0)` | `request(1)` every 1 (RENDEZVOUS becomes a channel of 1) |
| `asFlow().buffer(UNLIMITED)` / `.conflate()` | `request(MAX)` once |
| `asFlow().take(3)` | `request(64)`, then `cancel after 64`: the synchronous `Flux.range` had already pushed 64 into the channel, and "all the in-flight elements are discarded" |

- **This is a batch refill, not Reactor's 75% replenish.** For comparison, Reactor's own operators on a Flow-backed Flux: `publishOn(single())` and `flatMap` requested `256, 192, 192, …`, and `limitRate(10)` requested `10, 8, 8, …`. A plain `blockLast()` requested `MAX`. [Local, D11]
- Same-context fast path: when the collector's context needs no change, the publisher is subscribed inline. With `flowOn`/a dispatcher change, it goes through an extra channel (`super.collect`). [Source]

**`Flow.asPublisher()` / `Flow.asFlux()`: how `request(n)` becomes suspension** [Source: `FlowSubscription`; Local, D10]
- Nothing runs until the first `request(n)`. Each `emit(v)` calls `subscriber.onNext(v)` **synchronously** and then decrements the outstanding demand. When it reaches 0, the flow suspends **inside that `emit`**, and a later `request(n)` resumes it.
- Measured: after `request(2)`, received `[1, 2]` and `emit()` had returned only for `[1]` (the flow was parked inside `emit(2)`). After `request(3)`: received `[1..5]`, and `emit` had returned for `[1, 2, 3, 4]`.
- `cancel()` cancels the flow's coroutine. Downstream `take(3)` gave `onCompletion cause=JobCancellationException` in the flow and `[0, 1, 2]` in Reactor. [Local]
- The README calls `asPublisher` "TCK-compliant". The class comment reads "Adapter that transforms Flow into TCK-complaint Publisher" (the typo is in the source). [Source]
- `FlowSubscription` is `AbstractCoroutine(context, initParentJob = false)`: it has **no parent job**. Its lifetime belongs to the subscription, not to a scope. [Source]

**Threads** [Source: default `Dispatchers.Unconfined + context`; Local, D10]
- `flow { emit(thread); delay(10); emit(thread) }.asFlux()`: before the delay the flow and `onNext` ran on `main`. **After the delay, both ran on `kotlinx.coroutines.DefaultExecutor`**, the thread that resumed the `delay`. Reactor operators downstream then run on that thread too. Pass a dispatcher to pin them: with `asFlux(Dispatchers.IO)`, both ran on `DefaultDispatcher-worker-3`. Never do blocking work downstream of an `Unconfined` bridge without `publishOn`.

**Context propagation** [Source: `ReactorContext.kt`, `ReactorContextInjector.kt`, `FlowAsFlux.subscribe`; Local, D10]
- Reactor → coroutine: `FlowAsFlux.subscribe` checks `subscriber.currentContext()`. If it is not empty, the flow runs with `flowOn(context.asCoroutineContext())`, so `currentCoroutineContext()[ReactorContext]` is visible inside the flow. Measured: `.contextWrite(Context.of("traceId", "t-123"))` gave `flow saw traceId=t-123`. Without `contextWrite`: `no ReactorContext`.
- Coroutine → Reactor: `Publisher.asFlow()` (and `awaitFirst` and friends) call `injectCoroutineContext`. That applies every `ContextInjector` found with `ServiceLoader`, and `ReactorContextInjector` (only in `kotlinx-coroutines-reactor`) does `publisher.contextWrite(reactorContext)` for a `Mono`/`Flux`. Measured: `Mono.deferContextual { ctx -> … }` collected with `asFlow()` saw `none` normally, and `t-456` inside `withContext(Context.of("traceId", "t-456").asCoroutineContext())`.
- With only `kotlinx-coroutines-reactive` on the classpath, the injector list is empty and nothing is propagated. [Source]
- MDC/ThreadLocal values are not part of this. That is a separate `ThreadContextElement` story, covered in co-04/co-11. [Unverified here]

**Errors** [Local, D10]: `Flux.error(IOException("acquirer down")).asFlow()` throws `IOException` in the collector. A flow that throws after `emit(1)` gives `onNext 1`, then `onError IOException: ledger write failed`.

### B6. The JDK `java.util.concurrent.Flow` bridge (`kotlinx-coroutines-jdk9`)

- **It exists at 1.11.0.** Maven Central's `maven-metadata.xml` shows `<latest>1.11.0</latest>`, with 1.11.0-rc01, -rc02 and 1.11.0 present. Coordinates: **`org.jetbrains.kotlinx:kotlinx-coroutines-jdk9:1.11.0`**. The jar is 8,727 bytes, with classes `ReactiveFlowKt`, `PublishKt` and `AwaitKt` in package `kotlinx.coroutines.jdk9`. Pom dependencies: `kotlinx-coroutines-core-jvm 1.11.0` (compile), `kotlin-stdlib 2.2.20` (compile), `kotlinx-coroutines-reactive 1.11.0` (**runtime**). [Local: downloaded and `javap`]
- API [Source: `reactive/kotlinx-coroutines-jdk9/src/ReactiveFlow.kt`; Local `javap`]:
  ```kotlin
  public fun <T : Any> JFlow.Publisher<T>.asFlow(): Flow<T> = FlowAdapters.toPublisher(this).asFlow()
  @JvmOverloads public fun <T : Any> Flow<T>.asPublisher(context: CoroutineContext = EmptyCoroutineContext): JFlow.Publisher<T>
  public suspend inline fun <T> JFlow.Publisher<T>.collect(action: (T) -> Unit): Unit
  ```
  Plus `publish {}` and the `await*` functions in `PublishKt`/`AwaitKt`. The README says: "Implemented as a collection of thin wrappers over kotlinx-coroutines-reactive".
- Same demand mapping: a JDK publisher over `Flux.range(1, 150)` saw `request(64), request(64), request(64)`. [Local, D12]
- **Without the extra artifact:** reactive-streams 1.0.4 (already on the classpath through `kotlinx-coroutines-reactive`) has `org.reactivestreams.FlowAdapters`. `FlowAdapters.toPublisher(jdkPublisher).asFlow()` received `[AUTHORIZED, CAPTURED]` from a `SubmissionPublisher`, and `FlowAdapters.toFlowPublisher(flow.asPublisher())` round-tripped `[a, b]`. [Local, D16] For the labs this avoids a second new dependency. The jdk9 module only saves typing.

### B7. How Java code consumes a Kotlin `Flow`

- What Java sees: `public abstract java.lang.Object collect(kotlinx.coroutines.flow.FlowCollector<? super T>, kotlin.coroutines.Continuation<? super kotlin.Unit>)`. That is a suspend function, so Java would have to implement `Continuation` by hand. Do not hand Java a `Flow`. [Local: `javap kotlinx.coroutines.flow.Flow`]
- Give Java one of three faces, built in Kotlin [Local, D13: `javac` compiled `JavaCaller.java` against the Kotlin classes, and it ran]:
  - `Flux<T>` via `asFlux()`, for Reactor/WebFlux code. Java ran `api.eventsFlux().take(2).collectList().block()`.
  - `java.util.concurrent.Flow.Publisher<T>` via jdk9 `asPublisher()` (or `FlowAdapters`), for plain-JDK code. Java implemented `Flow.Subscriber` with `request(Long.MAX_VALUE)` and got 3 `onNext` and `onComplete`.
  - `CompletableFuture<List<T>>` via `scope.future { flow.take(n).toList() }`, for a finite result. Java ran `.get()`.
- `javap` of the facade shows plain Java signatures: `Flux<PaymentEvent> eventsFlux()`, `java.util.concurrent.Flow$Publisher<PaymentEvent> eventsPublisher()`, `CompletableFuture<List<PaymentEvent>> firstEvents(int)`. [Local]
- From Java, the coroutine scope that `future {}` needs can be created with `CoroutineScopeKt.CoroutineScope(Dispatchers.getDefault())` and cancelled with `CoroutineScopeKt.cancel(scope, null)`. [Local, D13] Better: own it in Kotlin and expose `close()`.

---

## Part C. Lesson 8, second half: testing flows

### C1. `runTest` and virtual time

- Signature: `public fun runTest(context: CoroutineContext = EmptyCoroutineContext, timeout: Duration = DEFAULT_TIMEOUT.getOrThrow(), testBody: suspend TestScope.() -> Unit): TestResult`, with `DEFAULT_TIMEOUT` = 60 s, or the `kotlinx.coroutines.test.default_timeout` system property parsed with `Duration.parse` (`1m`, `30s`, `1500ms`). [Source: `kotlinx-coroutines-test/common/src/TestBuilders.kt`] The old `runTest(context, dispatchTimeoutMs: Long, …)` is `DeprecationLevel.ERROR` "since 1.11.0, warning since 1.7.0". [Source]
- Measured: `delay(10.minutes)` gave `currentTime=600000` in about 150 ms of REAL time, most of it JVM start-up. [Local, D14]
- The timeout is wall-clock time. On timeout the error is `kotlinx.coroutines.test.UncompletedCoroutinesError: After waiting for 500ms, the test body did not run to completion` (body still suspended), or `… there were active child jobs: [StandaloneCoroutine{Active}@…]. Use TestScope.backgroundScope to launch the coroutines that need to be cancelled when the test body finishes` (body done, children still running). [Local, D14 #6, #7, with `runTest(timeout = 500.milliseconds)`]
- `withTimeout`/`withTimeoutOrNull` inside `runTest` use virtual time: `withTimeoutOrNull(5_000) { delay(10_000) }` gave `null at t=5000`. [Local, D14 #10]
- In the labs, the root `labs/build.gradle.kts` sets the JUnit property `junit.jupiter.execution.timeout.default = 20 s`. A hanging `runTest` therefore fails through JUnit at 20 s, before runTest's 60 s. [Local: read that file]

### C2. `StandardTestDispatcher` vs `UnconfinedTestDispatcher`

- Signatures: `StandardTestDispatcher(scheduler: TestCoroutineScheduler? = null, name: String? = null): TestDispatcher` is stable. `UnconfinedTestDispatcher(scheduler: TestCoroutineScheduler? = null, name: String? = null): TestDispatcher` is **`@ExperimentalCoroutinesApi`**. [Source + Local opt-in check]
- Order measured: `[body after launch, unconfined child, body after unconfined launch, standard child]`. The Unconfined child ran inside `launch` up to its first suspension; the Standard child ran only at `runCurrent()`. [Local, D14 #2]
- The `UnconfinedTestDispatcher` docs: "launching child coroutines that are resumed immediately, without going through a dispatch; this can be helpful for testing Channel and StateFlow usages", with the `stateFlow.value = 1; = 2; = 3` example ("each assignment will immediately resume the collecting child coroutine, so no values will be skipped"). [Docs: kotlinx-coroutines-test API, `-unconfined-test-dispatcher.html`]

### C3. `runCurrent`, `advanceTimeBy`, `advanceUntilIdle`, `backgroundScope`

- **`advanceTimeBy(n)` runs the tasks scheduled for `now ..< now + n`** ("running the tasks scheduled for `timeSource.markNow()..<timeSource.markNow() + delayTime`"). A task due at exactly `now + n` does not run until `runCurrent()`. Measured with tasks at 100 and 200: after `advanceTimeBy(100)`, `t=100 fired=[]`; after `runCurrent()`, `fired=[100]`; after `advanceUntilIdle()`, `t=200 fired=[100, 200]`. [Source + Local, D14 #3]
- **`advanceUntilIdle()` stops once only `backgroundScope` work is left.** The source is `advanceUntilIdleOr { events.none(TestDispatchEvent::isForeground) }`. A ticker in `backgroundScope`: after `advanceUntilIdle()`, `t=0 ticks=0`; after `advanceTimeBy(5000); runCurrent()`, `t=5000 ticks=5`. [Source + Local, D14 #4] The same thing hit my own SharedFlow demo: background subscribers printed nothing after `advanceUntilIdle()` (D1 output: "background subscriber did not run").
- `backgroundScope` KDoc: "advanceUntilIdle … will stop advancing the virtual time once only the coroutines in this scope are left unprocessed. Failures in coroutines in this scope do not terminate the test. Instead, they are reported at the end of the test." [Source + Docs]
- Stability [Local, opt-in check]: the `TestScope` extensions `currentTime`, `advanceUntilIdle()`, `runCurrent()` and `advanceTimeBy()` need `@OptIn(ExperimentalCoroutinesApi::class)`, and so does `testScheduler.currentTime`. The scheduler methods `testScheduler.advanceUntilIdle()`, `testScheduler.runCurrent()` and `testScheduler.advanceTimeBy(Duration)` compile with **no** opt-in. `testScheduler.advanceTimeBy(Long)` is experimental [Source].

### C4. Collecting a `StateFlow` in a test without missing values (the conflation traps)

[Local, D14 #5; production code `fun authorizeAndCapture() { _status.value = "AUTHORIZED"; _status.value = "CAPTURED" }`]

| Collector | What it saw |
|---|---|
| `backgroundScope.launch { status.toList(seen) }` (Standard), two sets with no suspension in between | **`[PENDING, CAPTURED]`** (AUTHORIZED conflated away) |
| `backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { status.toList(seen) }` | `[PENDING, AUTHORIZED, CAPTURED]` |
| Standard collector, production code with `delay(100)` between the sets | `[PENDING, AUTHORIZED, CAPTURED]` |
| Turbine `status.test { awaitItem() ×3 }` | `PENDING, AUTHORIZED, CAPTURED` (Turbine collects on `UnconfinedTestDispatcher`) [Local, D15; Source: Turbine `flow.kt` line 198] |

- **Which is the truth?** A real production collector on `Dispatchers.Default` can see either result. The Unconfined test shows the most a collector can see, not what it will see. Assert on *final state* and *transitions that matter*. Do not assert that a StateFlow delivered every intermediate value; if every transition matters, the type should be a SharedFlow/Channel. The Android testing guide says the same: "this stream of values is conflated, which means that if values are set in a StateFlow rapidly, collectors of that StateFlow are not guaranteed to receive all intermediate values, only the most recent one". [Docs: developer.android.com/kotlin/flow/test]
- **`take(n)` hang**: `async { status.take(3).toList() }` followed by the two synchronous sets never gets its third value. The test fails with `UncompletedCoroutinesError: After waiting for 500ms, the test body did not run to completion`. [Local, D14 #6]

### C5. `toList` with `take`, and other patterns without Turbine

- SharedFlow with `replay = 0`: subscribe first (`async { events.take(2).toList() }`, then `runCurrent()`), then emit. That gave `[AUTHORIZED, CAPTURED]`. Without the `runCurrent()`, the emits happen before anyone subscribed and are lost. [Local, D14 #9; Source A2]
- Hot sources that never complete need `backgroundScope` (for collectors and for `stateIn`/`shareIn` scopes) or a truncating operator. `stateIn(this, WhileSubscribed())` inside `runTest` failed with the "active child jobs" message, and `stateIn(this, Eagerly)` over a finite flow passed (A5). [Local, D14 #8]
- `callbackFlow` under test: a Standard `backgroundScope.launch { bus.events().collect {} }` followed at once by `bus.fire(...)` lost the event (`got=[] listeners=1`). The listener registered only when the scheduler ran, after the fire. Turbine's `test {}` registered before its block started (`listeners at block start=1`) and unregistered after it (`listeners=0`). [Local, D9]

### C6. Turbine (`app.cash.turbine`)

**Version and artifact** [Local: Maven Central metadata, pom, Gradle module metadata, jar; Docs: README and CHANGELOG at tag `1.2.1`/`trunk` via raw.githubusercontent.com]
- The latest release is **1.2.1**: `maven-metadata.xml` shows `<latest>1.2.1</latest>`, `<lastUpdated>20250611194930</lastUpdated>`, and the CHANGELOG says "## [1.2.1] - 2025-06-11". The only newer thing is `1.3.0-SNAPSHOT`, in the snapshots repository, according to the README. Coordinates: `testImplementation("app.cash.turbine:turbine:1.2.1")`. Gradle module metadata redirects JVM builds to `app.cash.turbine:turbine-jvm:1.2.1`, an 86,713-byte jar compiled for Java 8 (class file major version 52).
- Dependencies (turbine-jvm 1.2.1 pom/module): `kotlinx-coroutines-core 1.10.2` (compile/API), `kotlin-stdlib 2.1.21`, `kotlinx-coroutines-test 1.10.2` (**runtime**).
- **It resolves from Maven Central here.** A tiny Groovy-DSL Gradle 9.8.2 build (`java-library`, `mavenCentral()`, GRADLE_USER_HOME in scratch) printed `app.cash.turbine:turbine:1.2.1 \--- app.cash.turbine:turbine-jvm:1.2.1`, with `kotlinx-coroutines-core:1.10.2 -> 1.11.0`, `kotlin-stdlib:2.1.21 -> 2.4.21` and `kotlinx-coroutines-test:1.10.2 -> 1.11.0`. The runtime classpath was `Turbine-jvm.jar, kotlinx-coroutines-core-jvm-1.11.0.jar, kotlinx-coroutines-test-jvm-1.11.0.jar, kotlin-stdlib-2.4.21.jar, annotations-23.0.0.jar`. **Adding it brings no new transitive artifacts and changes no pinned version.** [Local]
- The README states: "While Turbine's own API is stable, we are currently forced to depend on an unstable API from kotlinx.coroutines test artifact: UnconfinedTestDispatcher." [Docs]

**API (1.2.1)** [Source: Turbine `src/commonMain/kotlin/app/cash/turbine/{flow,ReceiveTurbine,Turbine,coroutines}.kt` at tag 1.2.1; Local `javap`]
```kotlin
public suspend fun <T> Flow<T>.test(timeout: Duration? = null, name: String? = null, validate: suspend TurbineTestContext<T>.() -> Unit)
public suspend fun turbineScope(timeout: Duration? = null, validate: suspend TurbineContext.() -> Unit)
public interface TurbineContext : CoroutineScope {
    public fun <R> Flow<R>.testIn(scope: CoroutineScope, timeout: Duration? = null, name: String? = null): ReceiveTurbine<R>
}
public interface ReceiveTurbine<T> {
    fun asChannel(): ReceiveChannel<T>
    suspend fun cancel(); suspend fun cancelAndIgnoreRemainingEvents(); suspend fun cancelAndConsumeRemainingEvents(): List<Event<T>>
    fun expectNoEvents(); fun expectMostRecentItem(): T
    suspend fun awaitEvent(): Event<T>; suspend fun awaitItem(): T; suspend fun skipItems(count: Int)
    suspend fun awaitComplete(); suspend fun awaitError(): Throwable
    fun ensureAllEventsConsumed()
}
public fun <T> Turbine(timeout: Duration? = null, name: String? = null): Turbine<T>  // standalone: add(), takeItem(), close(), …
```
- The default timeout is `private val DEFAULT_TIMEOUT: Duration = 3000.milliseconds` (coroutines.kt). `test` launches the collector on `UnconfinedTestDispatcher(testScheduler)` when a `TestCoroutineScheduler` is present, and on `Dispatchers.Unconfined` otherwise, into a `Channel(UNLIMITED)`. [Source]

**Behaviour on kotlinx.coroutines 1.11.0** [Local, D15; each case run inside `runTest`]

| Case | Result |
|---|---|
| `flowOf("one","two").test { awaitItem(); awaitItem(); awaitComplete() }` | PASS |
| same, consuming only "one" | FAIL `TurbineAssertionError: Unconsumed events found: - Item(two) - Complete` |
| `… awaitItem(); cancelAndIgnoreRemainingEvents()` | PASS |
| `flow { emit(1); throw IOException("issuer 503") }.test { awaitItem(); awaitError().message }` | PASS (the error arrives as an event, not as a thrown exception) |
| StateFlow, two synchronous sets inside `test {}` | PASS, saw all three values (Unconfined collector) |
| `MutableSharedFlow` emit inside `test {}` | PASS |
| `MutableSharedFlow` emit **before** `test {}` | FAIL `TurbineAssertionError: No value produced in 3s`, after 3006 ms of REAL time |
| virtual `delay(10.seconds)` in the flow, `test(timeout = 200.milliseconds)` | PASS (the flow's delay is virtual; only Turbine's own wait is wall-clock) |
| REAL `Thread.sleep(500)` on `Dispatchers.IO` in the flow, `test(timeout = 200.milliseconds)` | FAIL `No value produced in 200ms` |
| `expectNoEvents()`, `skipItems(2)`, `delay(250)`, `expectMostRecentItem()` on a 100 ms ticker | PASS (got 2, then most recent 4) |
| `turbineScope { flowA.testIn(backgroundScope, name = "rates"); flowB.testIn(backgroundScope) … }` | PASS |
| named turbine, `awaitComplete()` while an item is pending | FAIL `Expected complete for rates but found Item(1)` |
| standalone `Turbine<String>(name = "ledger")` fed by a fake | PASS |
| `testIn(backgroundScope)` **outside** `turbineScope` | compiles with no warning; at runtime `java.lang.AssertionError: Turbine can only collect flows within a TurbineContext. Wrap with turbineScope { .. }` |

- The README's example error text "No value produced in 1s" is stale. The default became 3 s in 0.12.2 (CHANGELOG), and 1.2.1 prints "in 3s". [Local + Docs]
- Turbine runs the flow under test "up to the first suspension point before proceeding", so subscribing a SharedFlow and registering a callbackFlow listener both happen before the validation block. [Docs: README "Order of Execution & Shared Flows"; Local, D9/D15]


---

## Exact signatures and stability annotations in 1.11.0

How these were checked: one file (`S1Stability.kt`, in the demo section) used every API below with no `@OptIn` and was compiled with 2.4.21. **Experimental** means the compiler printed `this declaration needs opt-in … @kotlinx.coroutines.ExperimentalCoroutinesApi`. **Stable** means no warning. Rows marked [Source] were read in the source but not compiled. [Local + Source]

| API | Signature (abridged) | Stability |
|---|---|---|
| `SharedFlow`, `MutableSharedFlow`, `StateFlow`, `MutableStateFlow` (interfaces) | `interface SharedFlow<out T> : Flow<T> { val replayCache: List<T>; suspend fun collect(collector: FlowCollector<T>): Nothing }` and so on | Stable to use. **Implementing them yourself needs opt-in:** `@SubclassOptInRequired(ExperimentalForInheritanceCoroutinesApi::class)`, "not stable for inheritance in 3rd party libraries" [Source] |
| `MutableSharedFlow(...)` | `fun <T> MutableSharedFlow(replay: Int = 0, extraBufferCapacity: Int = 0, onBufferOverflow: BufferOverflow = SUSPEND)` | Stable |
| `emit` / `tryEmit` / `subscriptionCount` | `suspend fun emit(value: T)`, `fun tryEmit(value: T): Boolean`, `val subscriptionCount: StateFlow<Int>` | Stable |
| `resetReplayCache()` | `@ExperimentalCoroutinesApi fun resetReplayCache()` | **Experimental**; throws `UnsupportedOperationException` on `MutableStateFlow` |
| `MutableStateFlow(value)`, `value`, `compareAndSet` | `fun <T> MutableStateFlow(value: T): MutableStateFlow<T>`, `fun compareAndSet(expect: T, update: T): Boolean` | Stable |
| `update` / `updateAndGet` / `getAndUpdate` | `inline fun <T> MutableStateFlow<T>.update(function: (T) -> T)` | Stable |
| `asSharedFlow()` / `asStateFlow()` | `fun <T> MutableSharedFlow<T>.asSharedFlow(): SharedFlow<T>` | Stable [Source] |
| `SharedFlow.asFlow()` (new in 1.11.0) | `@ExperimentalCoroutinesApi fun <T> SharedFlow<T>.asFlow(): Flow<T> = transform { emit(it) }` | **Experimental** |
| `onSubscription` (StateFlow overload new in 1.11.0) | `fun <T> StateFlow<T>.onSubscription(action: suspend FlowCollector<T>.() -> Unit): StateFlow<T>` | Stable |
| `shareIn` / `stateIn` / suspend `stateIn` | see A5 | Stable |
| `SharingStarted`, `Eagerly`, `Lazily`, `WhileSubscribed(Long, Long)`, `WhileSubscribed(Duration, Duration)`, `SharingCommand` | see A5 | Stable (the Duration overload: [Source]) |
| `callbackFlow`, `channelFlow`, `awaitClose`, `ProducerScope` | see B1 | Stable |
| `SendChannel.trySend` / `trySendBlocking` | `fun trySend(element: E): ChannelResult<Unit>`, `fun <E> SendChannel<E>.trySendBlocking(element: E): ChannelResult<Unit>` | Stable |
| `Publisher.asFlow()`, `Flow.asPublisher(context)` | see B5 | Stable; `FlowSubscription` is `@InternalCoroutinesApi` |
| `Flow.asFlux(context)`, `ReactorContext`, `ContextView.asCoroutineContext()` | see B5 | Stable |
| jdk9 `asFlow` / `asPublisher` / `collect` | see B6 | Stable [Source: no annotations] |
| `runTest(context, timeout, testBody)` | see C1 | Stable. `runTest(context, dispatchTimeoutMs: Long, …)` is `DeprecationLevel.ERROR` since 1.11.0 |
| `TestScope`, `backgroundScope`, `StandardTestDispatcher(...)` | see C2 | Stable |
| `UnconfinedTestDispatcher(...)` | see C2 | **Experimental** |
| `TestScope.currentTime`, `TestScope.advanceUntilIdle()`, `TestScope.runCurrent()`, `TestScope.advanceTimeBy(...)` | extension members on `TestScope` | **Experimental** |
| `testScheduler.advanceUntilIdle()`, `testScheduler.runCurrent()`, `testScheduler.advanceTimeBy(Duration)` | `TestCoroutineScheduler` members | Stable |
| `testScheduler.currentTime`, `testScheduler.advanceTimeBy(Long)` | `TestCoroutineScheduler` members | **Experimental** |
| Turbine 1.2.1 `test`, `turbineScope`, `testIn`, `Turbine()` | see C6 | Turbine's own API is stable, per its README; it depends on the experimental `UnconfinedTestDispatcher` [Docs] |

---

## Common misconceptions, with the correction

1. **"`tryEmit` on a default `MutableSharedFlow()` fails only when a subscriber is busy."** It fails whenever there is **any** subscriber, even an idle one waiting for a value. The default flow has no buffer, so delivery is a rendezvous that only the suspending `emit` can do. KDoc: "tryEmit call succeeds and returns true only if there are no subscribers (in which case the emitted value is immediately lost)". [Source + Local: false ×6 with one idle subscriber] Note that co-08 currently says "whenever a subscriber is busy".
2. **"`extraBufferCapacity` keeps values for subscribers that arrive later."** No. Only `replay` does. With no subscribers, the extra buffer is not used at all (`replay=2, extra=10` kept `[4, 5]`). [Source + Local]
3. **"Each subscriber has its own queue."** There is one ring buffer. One slow subscriber slows the emitter under `SUSPEND` (emit 4, 5, 6 returned at 1000, 2000, 3000 ms) and makes the **fast** subscriber lose values under `DROP_LATEST` (`fast=[1, 2, 3]`). [Source + Local]
4. **"A new subscriber gets everything still in the buffer."** It gets the replay cache only. S2 got `5` while S1 still had 2..5 to process. [Source + Local]
5. **"`emit` returns when subscribers have processed the value."** It returns as soon as the value is buffered, or, with no buffer, once every subscriber has *taken* it. Processing is not awaited. [Source + Local]
6. **"Every assignment to a StateFlow reaches every collector."** Equal values are dropped at the setter (the old reference is kept), and a busy collector sees only the latest value (A→B→A shows nothing). A list mutated in place and set again emits nothing. [Source + Local]
7. **"StateFlow is thread-safe, so `state.value = state.value + 1` is fine."** Each access is atomic; the read-modify-write is not. It kept about 340,000-400,000 of 800,000 updates. Use `update {}`, and keep side effects out of its lambda: it ran 1,390,485 times for 800,000 updates. [Source + Local, REAL threads]
8. **"`WhileSubscribed(5000)` restarts the upstream when a client reconnects."** Not if the client comes back within 5 s (the same run #1 kept going). After the window, the upstream starts again **from the top**, and the subscriber first sees the stale cached value, unless `replayExpirationMillis` reset it to `initialValue`. [Source + Local timeline]
9. **"Reading `.value` keeps a `WhileSubscribed`/`Lazily` StateFlow running."** `.value` is not a subscription. Such a cache never starts (`[null, null, null]`, 0 fetches). [Local]
10. **"`shareIn` is a cache I can build inside a function."** Every call launches a new sharing coroutine that lives as long as the scope: 50 calls left 50 upstreams and 500 polls. [Local]
11. **"If the upstream of `stateIn` fails, subscribers get the exception."** They do not. The sharing coroutine dies, the scope's handler gets the exception, and subscribers wait for ever. The suspend `stateIn(scope)` does rethrow to its caller, and it cancels the scope. [Source + Local]
12. **"`callbackFlow` doesn't need `awaitClose` if a child coroutine keeps sending."** It throws the same `IllegalStateException` once the block returns with the channel open. Use `channelFlow` for your own children, and `awaitClose` for listeners. [Source + Local]
13. **"Once `collect` is called, my listener is registered."** Registration happens when the producer coroutine runs. An event fired in between is lost (`listeners=0`). [Local]
14. **"Buffer 64 means at most 64 events."** With a receiver already waiting, the first element is handed over directly: 65 accepted, 135 rejected. `conflate()` delivered the first *and* the last (`[0, 199]`). [Local]
15. **"`trySendBlocking` is the safe version of `trySend`."** It blocks the SDK's thread (`runBlocking { send(e) }` inside) until there is room: about 300 ms for 200 events at 2 ms each. Never call it on an event-loop thread or from a coroutine. [Source + Local]
16. **"`Publisher.asFlow()` requests one element at a time" or "uses Reactor's 256 prefetch".** It requests 64, then 64 more after each 64 collected. `buffer(n)` maps straight to `request(n)`, and `conflate()`/`UNLIMITED` to `request(Long.MAX_VALUE)`. [Source + Local]
17. **"`asFlux()` runs my flow on a Reactor scheduler."** It runs on `Dispatchers.Unconfined`: on the subscribing thread, and after a `delay` on `kotlinx.coroutines.DefaultExecutor`, together with every Reactor operator downstream. Pass a dispatcher or use `publishOn`. [Source + Local]
18. **"Reactor `Context` propagates with kotlinx-coroutines-reactive alone."** The propagation code lives in kotlinx-coroutines-reactor (`ReactorContextInjector`, loaded with `ServiceLoader`). [Source]
19. **"The JDK `Flow` bridge was dropped" or "it is called kotlinx-coroutines-jdk-flow".** It is `org.jetbrains.kotlinx:kotlinx-coroutines-jdk9:1.11.0`, and it is optional: `org.reactivestreams.FlowAdapters` + kotlinx-coroutines-reactive do the same. [Local]
20. **"Java can just call `flow.collect`."** From Java it is `Object collect(FlowCollector, Continuation)`. Give Java a `Flux`, a JDK `Flow.Publisher` or a `CompletableFuture`. [Local]
21. **"`advanceUntilIdle()` runs everything" and "`advanceTimeBy(100)` runs what is due at 100".** It skips background-only work (`ticks=0`). `advanceTimeBy(100)` runs tasks due *before* +100, and `runCurrent()` runs the one due at exactly +100. [Source + Local]
22. **"My StateFlow test saw every value, so production will too."** `UnconfinedTestDispatcher` and Turbine show the most a collector can see. A Standard (or real) collector saw `[PENDING, CAPTURED]`. [Local + Docs]
23. **"Turbine's timeout is virtual time."** It is a 3 s wall-clock timeout. The flow's own `delay`s are still virtual inside `runTest`. [Source + Local]
24. **"`testIn` works anywhere."** It compiles anywhere, but at runtime it throws `AssertionError: Turbine can only collect flows within a TurbineContext. Wrap with turbineScope { .. }`. [Local]

---

## Picture ideas (physical mental models for narrated animations)

Each picture is chosen so the animation can show the *variant* that surprises people, not only the happy path.

- **SharedFlow = a radio station with a single shared tape loop.** The DJ (emitter) records each song onto one circular tape. Every listener has a playback head on that same tape.
  - `replay` = the last N songs the station replays to anyone who tunes in.
  - `extraBufferCapacity` = extra tape, so the slowest head can lag behind.
  - **SUSPEND:** when the tape is full up to the slowest head, the DJ stops and waits with the next song in hand. Show the fast listener's head waiting too.
  - **DROP_OLDEST:** the slowest head is pushed forward, skipping songs.
  - **DROP_LATEST:** the new song is never recorded, so *nobody* hears it.
  - No listeners: the station plays to an empty room and keeps only the replay songs.
- **Default `MutableSharedFlow()` = a relay baton handoff.** No tape at all. The runner (emitter) can only let go when a receiver's hand is on the baton (`tryEmit` = trying to throw it without waiting, so it falls). With three receivers, the runner waits until all three have grabbed it.
- **Late subscriber = walking into a cinema mid-film.** You see the recap (replay) and then the live film. You never see the scenes the slow viewer in row 3 is still rewinding through.
- **StateFlow = a notice board with one slot.** Writing the same notice again does nothing; the old sheet stays pinned, even if your sheet is a fresh copy. Each passer-by remembers the last notice they read. A busy passer-by who looks up after three changes sees only the current sheet, and if it reads the same as the last one they saw, they walk on. Show A→B→A: the board changed twice, and the busy viewer notices nothing.
- **`value = value + 1` race = two clerks reading the counter and writing back their own +1.** One update vanishes. **`update {}`** = a clerk who writes only if the board still shows what they read, and otherwise rereads and recomputes. Show the recompute count climbing (1.39 M attempts for 0.8 M updates).
- **`subscriptionCount` = a turnstile with a paper tally strip, not a digital display.** Someone who walks in and straight out still leaves "+1, -1" on the strip. A display (plain StateFlow) would show only "0".
- **`stateIn`/`shareIn` = a building with one water main and taps.**
  - `Eagerly` = the pump runs from opening time, whether anyone is there.
  - `Lazily` = the first person to arrive turns it on, and nobody ever turns it off.
  - `WhileSubscribed(5000)` = a motion-sensor tap that shuts 5 s after the last person leaves. Come back within 5 s and the water never stopped. Come back later and the pump restarts cold, from the beginning.
  - `replayExpirationMillis` = the glass of water left on the counter: drink the stale glass first, unless the cleaner threw it out (reset to `initialValue`).
  - Reading `.value` = looking at the counter from the doorway. It does not trip the sensor.
- **Scope leak = installing a new pump for every visitor and never switching any off.** Animate 50 pumps humming in an empty building at night.
- **Upstream failure in `shareIn` = the pump breaks, and the alarm rings in the manager's office (the scope's handler).** The people at the taps just stand there waiting for water.
- **Slots and the ring buffer = numbered seats around a circular conveyor belt.** Each seat has a marker showing which plate it takes next. The belt is lengthened by doubling (2, 4, 8). The slowest marker decides where the belt can be cleared (`head`). Waiting emitters stand on the belt as placeholder trays (`Emitter` objects).
- **`callbackFlow` = a mailbox bolted to the SDK's front door.**
  - `trySend` = dropping a letter through the slot. If the box is full, the letter bounces back, and you must look at it.
  - `trySendBlocking` = the courier stands at the door holding the letter until there is room, so the SDK's delivery van (its thread) is stuck.
  - `awaitClose` = you sit on the porch until told to leave, then unscrew the mailbox.
  - Forgetting `awaitClose` = walking away with the mailbox still bolted on, at which point the library sounds an alarm (`IllegalStateException`).
  - The registration race = the postman arriving before the mailbox is bolted on.
- **`channelFlow` = a kitchen with several cooks (children) feeding one serving hatch.** Service ends when the last cook finishes, and nobody needs to sit on a porch.
- **Reactive Streams demand = a restaurant order pad.**
  - `asFlux()`/`asPublisher()`: the waiter (Reactor) orders n plates. The cook (Flow) serves each one the moment it is cooked (`onNext` inside `emit`), and sits down mid-motion when the order is used up, holding the last plate's ladle (suspended inside `emit`).
  - `asFlow()`: the Kotlin diner orders 64 plates, eats 64, then orders 64 more. Reactor's own waiters (`publishOn`) order 256 and top up at 192.
- **Context propagation = a visitor badge (traceId) handed through a turnstile.** It passes either way, but only if the reactor-module turnstile (the `ServiceLoader` injector) is installed.
- **Unconfined `asFlux` threads = a relay where whoever wakes the runner carries on running.** After a `delay`, it is the alarm-clock thread (`DefaultExecutor`) that runs the rest of the race, Reactor operators included.
- **Virtual time = a film editor's timeline.** Empty stretches are cut. `runCurrent` = play this frame; `advanceTimeBy` = fast-forward up to, but not including, the frame at the mark; `advanceUntilIdle` = fast-forward until only the background music (`backgroundScope`) is left.
- **StandardTestDispatcher vs UnconfinedTestDispatcher = an in-tray vs an eager intern.** The Standard dispatcher puts new work in the in-tray, which nobody touches until you say "go". The Unconfined intern starts the moment you hand something over.
- **The conflation trap in tests = photographing the notice board only when you look up.** Two quick changes between photos leave one photo. The Unconfined collector (or Turbine) is a camera with a motion trigger.
- **Turbine = a court stenographer.** Every event goes into the transcript (an unlimited channel), in order. The judge (your test) must read every line, and an unread line fails the hearing. If no new line appears within 3 s on the wall clock, the stenographer objects.

---

## Demo ideas with expected outcomes

All programs below were compiled with Kotlin 2.4.21 (`-jvm-target 21`) and run on JDK 21.0.12.1 against kotlinx.coroutines 1.11.0 and Reactor 3.8.8. The output under each program is exactly what the run printed (copied from the saved output files). Virtual-time demos print the same numbers on every run. Lines marked REAL vary. Packages are scratch names (`h1`, `b2`, …); rename them to the lab convention (for example `workbench.flows.l07`) when pasting. `@OptIn(ExperimentalCoroutinesApi::class)` is needed for `currentTime`/`runCurrent`/`advance*` on `TestScope` and for `UnconfinedTestDispatcher`. D12 and D13 also need `kotlinx-coroutines-jdk9-1.11.0.jar` (or rewrite them with `FlowAdapters`, as in D16). D9 and D15 need `turbine-jvm-1.2.1.jar`.

How I compiled (reproducible): `java -cp <kotlin-compiler-embeddable-2.4.21 + kotlin-stdlib + kotlin-script-runtime + kotlin-reflect + kotlin-daemon-embeddable 2.4.21 + kotlinx-coroutines-core-jvm-1.8.0 + annotations-23.0.0> org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath <kotlin-stdlib-2.4.21:kotlinx-coroutines-core-jvm-1.11.0:kotlinx-coroutines-test-jvm-1.11.0:kotlinx-coroutines-reactive-1.11.0:kotlinx-coroutines-reactor-1.11.0:reactor-core-3.8.8:reactive-streams-1.0.4:annotations-23.0.0[:kotlinx-coroutines-jdk9-1.11.0][:turbine-jvm-1.2.1]> -jvm-target 21 -d out File.kt`, then `java -cp out:<same libs> <MainKt>`. All jars except the last two are in `~/.gradle/caches/modules-2/files-2.1/`.

### D1. When `tryEmit` fails and when `emit` suspends (lesson 7, A1)
What to point at: the "1 idle subscriber" row (false ×6); `replay=2` behaving like `extra=2` while subscribed; `DROP_OLDEST` delivering 5, 6 and `DROP_LATEST` delivering 1, 2; the rendezvous timeline (each `emit` returns at the moment the subscriber takes the value); and the trap printed by the harness itself, where `advanceUntilIdle()` did not run background subscribers.
```kotlin
package h1

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// When does MutableSharedFlow.tryEmit return false, and when does emit suspend?
// All times are VIRTUAL milliseconds (runTest).

@OptIn(ExperimentalCoroutinesApi::class)
fun scenario(name: String, flow: MutableSharedFlow<Int>, subscribers: Int, workMs: Long) = runTest {
    println("== $name, subscribers=$subscribers, each takes ${workMs}ms per item")
    repeat(subscribers) { s ->
        backgroundScope.launch {
            flow.collect { v -> println("  t=$currentTime sub$s got $v"); delay(workMs) }
        }
    }
    runCurrent() // let subscribers subscribe and suspend waiting for a value
    val results = (1..6).map { v -> v to flow.tryEmit(v) }
    println("  tryEmit 1..6 at t=$currentTime -> $results  (subscriptionCount=${flow.subscriptionCount.value})")
    advanceUntilIdle()
    println("  after advanceUntilIdle(): t=$currentTime (background subscriber did not run)")
    advanceTimeBy(1_000); runCurrent()
}

@OptIn(ExperimentalCoroutinesApi::class)
fun emitTimeline(name: String, flow: MutableSharedFlow<Int>, workMs: Long) = runTest {
    println("== emit timeline: $name, one subscriber taking ${workMs}ms per item")
    backgroundScope.launch { flow.collect { v -> println("  t=$currentTime   sub got $v"); delay(workMs) } }
    runCurrent()
    for (v in 1..5) {
        flow.emit(v)
        println("  t=$currentTime emit($v) returned")
    }
    advanceUntilIdle()
}

fun main() {
    scenario("MutableSharedFlow() defaults, NO subscribers", MutableSharedFlow(), 0, 100)
    scenario("MutableSharedFlow() defaults", MutableSharedFlow(), 1, 100)
    scenario("extraBufferCapacity=2", MutableSharedFlow(extraBufferCapacity = 2), 1, 100)
    scenario("replay=2", MutableSharedFlow(replay = 2), 1, 100)
    scenario("replay=1, extraBufferCapacity=2", MutableSharedFlow(replay = 1, extraBufferCapacity = 2), 1, 100)
    scenario("extra=2, DROP_OLDEST", MutableSharedFlow(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_OLDEST), 1, 100)
    scenario("extra=2, DROP_LATEST", MutableSharedFlow(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_LATEST), 1, 100)
    emitTimeline("MutableSharedFlow() defaults", MutableSharedFlow(), 100)
    emitTimeline("extraBufferCapacity=2", MutableSharedFlow(extraBufferCapacity = 2), 100)
    try { MutableSharedFlow<Int>(onBufferOverflow = BufferOverflow.DROP_OLDEST) } catch (e: IllegalArgumentException) { println("== DROP_OLDEST with no buffer: ${e::class.simpleName}: ${e.message}") }
}
```
Observed output:
```
== MutableSharedFlow() defaults, NO subscribers, subscribers=0, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, true), (4, true), (5, true), (6, true)]  (subscriptionCount=0)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
== MutableSharedFlow() defaults, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, false), (2, false), (3, false), (4, false), (5, false), (6, false)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
== extraBufferCapacity=2, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, false), (4, false), (5, false), (6, false)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
  t=0 sub0 got 1
  t=100 sub0 got 2
== replay=2, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, false), (4, false), (5, false), (6, false)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
  t=0 sub0 got 1
  t=100 sub0 got 2
== replay=1, extraBufferCapacity=2, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, true), (4, false), (5, false), (6, false)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
  t=0 sub0 got 1
  t=100 sub0 got 2
  t=200 sub0 got 3
== extra=2, DROP_OLDEST, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, true), (4, true), (5, true), (6, true)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
  t=0 sub0 got 5
  t=100 sub0 got 6
== extra=2, DROP_LATEST, subscribers=1, each takes 100ms per item
  tryEmit 1..6 at t=0 -> [(1, true), (2, true), (3, true), (4, true), (5, true), (6, true)]  (subscriptionCount=1)
  after advanceUntilIdle(): t=0 (background subscriber did not run)
  t=0 sub0 got 1
  t=100 sub0 got 2
== emit timeline: MutableSharedFlow() defaults, one subscriber taking 100ms per item
  t=0   sub got 1
  t=0 emit(1) returned
  t=100   sub got 2
  t=100 emit(2) returned
  t=200   sub got 3
  t=200 emit(3) returned
  t=300   sub got 4
  t=300 emit(4) returned
  t=400   sub got 5
  t=400 emit(5) returned
== emit timeline: extraBufferCapacity=2, one subscriber taking 100ms per item
  t=0 emit(1) returned
  t=0 emit(2) returned
  t=0   sub got 1
  t=0 emit(3) returned
  t=100   sub got 2
  t=100 emit(4) returned
  t=200   sub got 3
  t=200 emit(5) returned
== DROP_OLDEST with no buffer: IllegalArgumentException: replay or extraBufferCapacity must be positive with non-default onBufferOverflow strategy DROP_OLDEST
```

### D1b. One slow subscriber, one fast one, per overflow policy (lesson 7, A1)
```kotlin
package h6
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// One fast and one slow subscriber share ONE buffer. Virtual time.
@OptIn(ExperimentalCoroutinesApi::class)
fun run(policy: BufferOverflow) = runTest {
    val flow = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = policy)
    val fast = mutableListOf<Int>(); val slow = mutableListOf<Int>()
    backgroundScope.launch { flow.collect { fast += it } }
    backgroundScope.launch { flow.collect { slow += it; delay(1_000) } }
    runCurrent()
    val emitDone = mutableListOf<String>()
    for (v in 1..6) { flow.emit(v); emitDone += "$v@t=$currentTime"; delay(10) }
    advanceTimeBy(10_000); runCurrent()
    println("  $policy: fast=$fast slow=$slow emit returned: $emitDone")
}
fun main() { BufferOverflow.entries.forEach { run(it) } }
```
Observed output:
```
  SUSPEND: fast=[1, 2, 3, 4, 5, 6] slow=[1, 2, 3, 4, 5, 6] emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=1000, 5@t=2000, 6@t=3000]
  DROP_OLDEST: fast=[1, 2, 3, 4, 5, 6] slow=[1, 5, 6] emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=30, 5@t=40, 6@t=50]
  DROP_LATEST: fast=[1, 2, 3] slow=[1, 2, 3] emit returned: [1@t=0, 2@t=10, 3@t=20, 4@t=30, 5@t=40, 6@t=50]
```

### D2. What a late subscriber sees; `resetReplayCache` (lesson 7, A2)
```kotlin
package h2

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// What does a subscriber that arrives late see? (virtual time)
@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    runTest {
        println("== A: replay=2, extraBufferCapacity=10, emit 1..5 with NO subscribers")
        val a = MutableSharedFlow<Int>(replay = 2, extraBufferCapacity = 10)
        (1..5).forEach { a.emit(it) }
        println("  replayCache=${a.replayCache}")
        println("  late subscriber, first 2 items: ${a.take(2).toList()}")

        println("== B: replay=0: values emitted with no subscriber are gone")
        val b = MutableSharedFlow<Int>()
        (1..5).forEach { b.emit(it) }
        println("  replayCache=${b.replayCache}")
        val got = mutableListOf<Int>()
        val job = backgroundScope.launch { b.collect { got += it } }
        runCurrent(); b.emit(6); runCurrent()
        println("  late subscriber saw $got")
        job.cancel()

        println("== C: replay=1, extra=10, slow subscriber S1 is 4 items behind when S2 joins")
        val c = MutableSharedFlow<Int>(replay = 1, extraBufferCapacity = 10)
        backgroundScope.launch { c.collect { println("  t=$currentTime S1 got $it"); delay(100) } }
        runCurrent()
        (1..5).forEach { c.emit(it) }
        println("  t=$currentTime emitted 1..5, replayCache=${c.replayCache}")
        backgroundScope.launch { c.collect { println("  t=$currentTime S2 got $it") } }
        runCurrent()
        advanceTimeBy(1_000); runCurrent()

        println("== D: resetReplayCache() (experimental)")
        val d = MutableSharedFlow<Int>(replay = 3)
        (1..5).forEach { d.emit(it) }
        println("  before reset replayCache=${d.replayCache}")
        d.resetReplayCache()
        println("  after reset replayCache=${d.replayCache}")
        try { MutableStateFlow(0).resetReplayCache() } catch (e: UnsupportedOperationException) { println("  MutableStateFlow.resetReplayCache(): ${e::class.simpleName}: ${e.message}") }
    }
}
```
Observed output:
```
== A: replay=2, extraBufferCapacity=10, emit 1..5 with NO subscribers
  replayCache=[4, 5]
  late subscriber, first 2 items: [4, 5]
== B: replay=0: values emitted with no subscriber are gone
  replayCache=[]
  late subscriber saw [6]
== C: replay=1, extra=10, slow subscriber S1 is 4 items behind when S2 joins
  t=0 emitted 1..5, replayCache=[5]
  t=0 S1 got 1
  t=0 S2 got 5
  t=100 S1 got 2
  t=200 S1 got 3
  t=300 S1 got 4
  t=400 S1 got 5
== D: resetReplayCache() (experimental)
  before reset replayCache=[3, 4, 5]
  after reset replayCache=[]
  MutableStateFlow.resetReplayCache(): UnsupportedOperationException: MutableStateFlow.resetReplayCache is not supported
```

### D3. StateFlow conflation, `compareAndSet`, and the `value = value + 1` race (lesson 7, A3)
Part G runs on REAL threads, so its `racy` numbers change between runs. The `update` result is always 800000.
```kotlin
package h3

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.math.BigDecimal

data class Rate(val pair: String, val mid: BigDecimal)

@OptIn(ExperimentalCoroutinesApi::class)
fun conflation() = runTest {
    println("== A: setting an equal value emits nothing (data class equality)")
    val rate = MutableStateFlow(Rate("EURUSD", BigDecimal("1.0850")))
    val seen = mutableListOf<Rate>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { rate.collect { seen += it } }
    rate.value = Rate("EURUSD", BigDecimal("1.0850"))   // equal: no emission
    rate.value = Rate("EURUSD", BigDecimal("1.08500"))  // BigDecimal scale differs -> NOT equal -> emits
    rate.value = Rate("EURUSD", BigDecimal("1.0851"))
    println("  collector saw ${seen.size} values: $seen")

}
@OptIn(ExperimentalCoroutinesApi::class)
fun part_B() = runTest {
    println("== B: a slow collector skips values (virtual time)")
    val s = MutableStateFlow(0)
    val slow = mutableListOf<String>()
    backgroundScope.launch { s.collect { slow += "t=$currentTime:$it"; delay(100) } }
    runCurrent()
    for (v in 1..10) { delay(25); s.value = v }      // one update every 25 ms, 1..10
    advanceTimeBy(500); runCurrent()
    println("  slow collector saw $slow")

}
@OptIn(ExperimentalCoroutinesApi::class)
fun part_C() = runTest {
    println("== C: A -> B -> A while the collector is busy: it sees nothing new")
    val st = MutableStateFlow("AUTHORIZED")
    val log = mutableListOf<String>()
    backgroundScope.launch { st.collect { log += "t=$currentTime:$it"; delay(100) } }
    runCurrent()
    delay(10); st.value = "CAPTURED"; delay(10); st.value = "AUTHORIZED"
    advanceTimeBy(500); runCurrent()
    println("  collector saw $log")

}
@OptIn(ExperimentalCoroutinesApi::class)
fun part_D() = runTest {
    println("== D: same three updates with UnconfinedTestDispatcher and no delay in the collector")
    val st2 = MutableStateFlow("AUTHORIZED")
    val log2 = mutableListOf<String>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { st2.collect { log2 += it } }
    st2.value = "CAPTURED"; st2.value = "AUTHORIZED"
    println("  collector saw $log2")

}
@OptIn(ExperimentalCoroutinesApi::class)
fun part_E() = runTest {
    println("== E: StateFlow emit/tryEmit never suspend, never fail")
    val e = MutableStateFlow(0)
    backgroundScope.launch { e.collect { delay(1_000_000) } }
    runCurrent()
    println("  tryEmit results: ${(1..5).map { e.tryEmit(it) }}, value=${e.value}, t=$currentTime")
}

fun casDemo() {
    println("== F: compareAndSet semantics")
    val f = MutableStateFlow(10)
    println("  cas(10 -> 11) = ${f.compareAndSet(10, 11)}, value=${f.value}")
    println("  cas(10 -> 12) = ${f.compareAndSet(10, 12)}, value=${f.value}  (expect is stale)")
    println("  cas(11 -> 11) = ${f.compareAndSet(11, 11)}, value=${f.value}  (equal to equal: true, nothing emitted)")
    val prev = f.getAndUpdate { it * 2 }; val next = f.updateAndGet { it + 1 }
    println("  getAndUpdate{*2} returned $prev, updateAndGet{+1} returned $next")
}

fun race() {
    println("== G: value = value + 1 vs update { it + 1 } from 8 coroutines x 100_000 on Dispatchers.Default (REAL threads)")
    repeat(3) { run ->
        val racy = MutableStateFlow(0); val safe = MutableStateFlow(0)
        runBlocking(Dispatchers.Default) {
            repeat(8) { launch { repeat(100_000) { racy.value = racy.value + 1 } } }
            repeat(8) { launch { repeat(100_000) { safe.update { it + 1 } } } }
        }
        println("  run ${run + 1}: racy=${racy.value}  update=${safe.value}  (expected 800000)")
    }
}

fun main() { conflation(); part_B(); part_C(); part_D(); part_E(); casDemo(); race() }
```
Observed output:
```
== A: setting an equal value emits nothing (data class equality)
  collector saw 3 values: [Rate(pair=EURUSD, mid=1.0850), Rate(pair=EURUSD, mid=1.08500), Rate(pair=EURUSD, mid=1.0851)]
== B: a slow collector skips values (virtual time)
  slow collector saw [t=0:0, t=100:3, t=200:7, t=300:10]
== C: A -> B -> A while the collector is busy: it sees nothing new
  collector saw [t=0:AUTHORIZED]
== D: same three updates with UnconfinedTestDispatcher and no delay in the collector
  collector saw [AUTHORIZED, CAPTURED, AUTHORIZED]
== E: StateFlow emit/tryEmit never suspend, never fail
  tryEmit results: [true, true, true, true, true], value=5, t=0
== F: compareAndSet semantics
  cas(10 -> 11) = true, value=11
  cas(10 -> 12) = false, value=11  (expect is stale)
  cas(11 -> 11) = true, value=11  (equal to equal: true, nothing emitted)
  getAndUpdate{*2} returned 11, updateAndGet{+1} returned 23
== G: value = value + 1 vs update { it + 1 } from 8 coroutines x 100_000 on Dispatchers.Default (REAL threads)
  run 1: racy=397154  update=800000  (expected 800000)
  run 2: racy=376352  update=800000  (expected 800000)
  run 3: racy=349669  update=800000  (expected 800000)
```

### D4. `SharingStarted` timelines and `subscriptionCount` (lesson 7, A4/A5)
The headline demo for the "tap" animation. Pause on t=4000 (no restart within the window) and on t=11000 / t=14000 (stop, then a cold restart behind a stale value, or `-1` with `replayExpirationMillis = 0`).
```kotlin
package h4

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// An FX-rate poller: each run of the upstream is numbered; it emits run*100 + i every 1000 ms.
// All times are VIRTUAL milliseconds.
class Feed(private val scheduler: TestCoroutineScheduler) {
    var starts = 0
    val flow: Flow<Int> = flow {
        val n = ++starts
        println("  t=${scheduler.currentTime}: upstream START #$n")
        try {
            var i = 0
            while (true) { emit(n * 100 + i++); delay(1000) }
        } finally { println("  t=${scheduler.currentTime}: upstream STOP #$n") }
    }
}

fun TestScope.subscribe(name: String, f: Flow<Int>): Job =
    backgroundScope.launch { f.collect { println("  t=$currentTime: $name got $it") } }

@OptIn(ExperimentalCoroutinesApi::class)
fun eagerly() = runTest {
    println("== Eagerly (shareIn, replay=0): upstream starts before anyone subscribes")
    val feed = Feed(testScheduler)
    val shared = feed.flow.shareIn(backgroundScope, SharingStarted.Eagerly)
    delay(2500)
    val a = subscribe("A", shared)
    delay(2000); a.cancel(); println("  t=$currentTime: A leaves")
    delay(2000); println("  t=$currentTime: end, upstream starts=${feed.starts}")
}

@OptIn(ExperimentalCoroutinesApi::class)
fun lazily() = runTest {
    println("== Lazily (stateIn): starts with first subscriber, never stops")
    val feed = Feed(testScheduler)
    val state = feed.flow.stateIn(backgroundScope, SharingStarted.Lazily, initialValue = -1)
    delay(1000); println("  t=$currentTime: no subscriber yet, value=${state.value}")
    val a = subscribe("A", state)
    delay(1500); a.cancel(); println("  t=$currentTime: A leaves")
    delay(3000); println("  t=$currentTime: nobody subscribed, value=${state.value} (still polling)")
}

@OptIn(ExperimentalCoroutinesApi::class)
fun whileSubscribed(stop: Long, expire: Long) = runTest {
    println("== WhileSubscribed(stopTimeoutMillis=$stop, replayExpirationMillis=${if (expire == Long.MAX_VALUE) "MAX" else expire}) (stateIn, initial=-1)")
    val feed = Feed(testScheduler)
    val state = feed.flow.stateIn(backgroundScope, SharingStarted.WhileSubscribed(stop, expire), initialValue = -1)
    var a = subscribe("A", state)
    delay(2500); a.cancel(); println("  t=$currentTime: A leaves")
    delay(1500); println("  t=$currentTime: A comes back after 1500 ms, value=${state.value}")
    a = subscribe("A", state)
    delay(2000); a.cancel(); println("  t=$currentTime: A leaves")
    delay(8000); println("  t=$currentTime: A comes back after 8000 ms, value=${state.value}")
    a = subscribe("A", state)
    delay(1500); println("  t=$currentTime: end, upstream starts=${feed.starts}")
}

@OptIn(ExperimentalCoroutinesApi::class)
fun subscriptionCount() = runTest {
    println("== subscriptionCount is not conflated")
    val events = MutableSharedFlow<Int>()
    val counts = mutableListOf<Int>()
    backgroundScope.launch { events.subscriptionCount.collect { counts += it } }
    runCurrent() // the observer is now subscribed to subscriptionCount and waiting
    // join and leave before the observer coroutine gets a chance to run again
    val j = backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { events.collect { } }
    j.cancel()
    runCurrent()
    println("  observer saw $counts (a StateFlow<Int> holding the same numbers would have shown only [0])")
    val plain = MutableStateFlow(0); val seen = mutableListOf<Int>()
    backgroundScope.launch { plain.collect { seen += it } }
    runCurrent()
    plain.value = 1; plain.value = 0; runCurrent()
    println("  plain MutableStateFlow doing 0 -> 1 -> 0: observer saw $seen")
}

fun main() {
    eagerly(); lazily()
    whileSubscribed(5000, Long.MAX_VALUE)
    whileSubscribed(5000, 0)
    whileSubscribed(0, Long.MAX_VALUE)
    subscriptionCount()
}
```
Observed output:
```
== Eagerly (shareIn, replay=0): upstream starts before anyone subscribes
  t=0: upstream START #1
  t=3000: A got 103
  t=4000: A got 104
  t=4500: A leaves
  t=6500: end, upstream starts=1
  t=6500: upstream STOP #1
== Lazily (stateIn): starts with first subscriber, never stops
  t=1000: no subscriber yet, value=-1
  t=1000: A got -1
  t=1000: upstream START #1
  t=1000: A got 100
  t=2000: A got 101
  t=2500: A leaves
  t=5500: nobody subscribed, value=104 (still polling)
  t=5500: upstream STOP #1
== WhileSubscribed(stopTimeoutMillis=5000, replayExpirationMillis=MAX) (stateIn, initial=-1)
  t=0: A got -1
  t=0: upstream START #1
  t=0: A got 100
  t=1000: A got 101
  t=2000: A got 102
  t=2500: A leaves
  t=4000: A comes back after 1500 ms, value=103
  t=4000: A got 104
  t=5000: A got 105
  t=6000: A leaves
  t=11000: upstream STOP #1
  t=14000: A comes back after 8000 ms, value=111
  t=14000: A got 111
  t=14000: upstream START #2
  t=14000: A got 200
  t=15000: A got 201
  t=15500: end, upstream starts=2
  t=15500: upstream STOP #2
== WhileSubscribed(stopTimeoutMillis=5000, replayExpirationMillis=0) (stateIn, initial=-1)
  t=0: A got -1
  t=0: upstream START #1
  t=0: A got 100
  t=1000: A got 101
  t=2000: A got 102
  t=2500: A leaves
  t=4000: A comes back after 1500 ms, value=103
  t=4000: A got 104
  t=5000: A got 105
  t=6000: A leaves
  t=11000: upstream STOP #1
  t=14000: A comes back after 8000 ms, value=-1
  t=14000: A got -1
  t=14000: upstream START #2
  t=14000: A got 200
  t=15000: A got 201
  t=15500: end, upstream starts=2
  t=15500: upstream STOP #2
== WhileSubscribed(stopTimeoutMillis=0, replayExpirationMillis=MAX) (stateIn, initial=-1)
  t=0: A got -1
  t=0: upstream START #1
  t=0: A got 100
  t=1000: A got 101
  t=2000: A got 102
  t=2500: A leaves
  t=2500: upstream STOP #1
  t=4000: A comes back after 1500 ms, value=102
  t=4000: A got 102
  t=4000: upstream START #2
  t=4000: A got 200
  t=5000: A got 201
  t=6000: A leaves
  t=6000: upstream STOP #2
  t=14000: A comes back after 8000 ms, value=202
  t=14000: A got 202
  t=14000: upstream START #3
  t=14000: A got 300
  t=15000: A got 301
  t=15500: end, upstream starts=3
  t=15500: upstream STOP #3
== subscriptionCount is not conflated
  observer saw [0, 1, 0] (a StateFlow<Int> holding the same numbers would have shown only [0])
  plain MutableStateFlow doing 0 -> 1 -> 0: observer saw [0]
```

### D5. The suspend `stateIn`, upstream failure, the per-call leak, and the default 64 buffer (lesson 7, A5-A7)
```kotlin
package h5

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
fun suspendStateIn() = runTest {
    println("== suspend stateIn(scope): waits for the first value")
    val config = flow { delay(300); emit("timeout=2s"); delay(1000); emit("timeout=3s") }
    val t0 = currentTime
    val state = config.stateIn(backgroundScope)
    println("  returned at t=${currentTime - t0}, value=${state.value}")
    delay(1500); println("  t=$currentTime value=${state.value}")

    println("== suspend stateIn on an empty flow")
    try { emptyFlow<String>().stateIn(backgroundScope) } catch (e: NoSuchElementException) { println("  ${e::class.simpleName}: ${e.message}") }

    println("== suspend stateIn when the upstream fails before the first value")
    val scope = CoroutineScope(Job() + StandardTestDispatcher(testScheduler) + CoroutineExceptionHandler { _, _ -> })
    try { flow<String> { throw IOException("config server down") }.stateIn(scope) }
    catch (e: IOException) { println("  caller got ${e::class.simpleName}: ${e.message}; scope still active? ${scope.isActive}") }
}

@OptIn(ExperimentalCoroutinesApi::class)
fun upstreamFailure() = runTest {
    println("== shareIn: an upstream exception kills the sharing coroutine, not the subscribers")
    val handlerSaw = mutableListOf<String>()
    val appScope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler) +
        CoroutineExceptionHandler { _, e -> handlerSaw += "${e::class.simpleName}: ${e.message}" })
    val prices = flow { emit(1); delay(100); emit(2); delay(100); throw IOException("feed reset") }
        .shareIn(appScope, SharingStarted.Eagerly, replay = 1)
    val got = mutableListOf<Int>()
    val sub = backgroundScope.launch { prices.collect { got += it } }
    delay(1_000)
    println("  t=$currentTime subscriber got $got, still waiting? ${sub.isActive}; handler saw $handlerSaw; appScope active? ${appScope.isActive}")
    appScope.cancel()
}

@OptIn(ExperimentalCoroutinesApi::class)
fun perCallLeak() = runTest {
    println("== leak: calling shareIn per request in a long-lived scope")
    val appScope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
    var polls = 0
    val upstream = flow { while (true) { polls++; emit(polls); delay(1000) } }
    fun ratesForRequest(): SharedFlow<Int> = upstream.shareIn(appScope, SharingStarted.Lazily, 1) // BUG: new sharing per call
    repeat(50) { ratesForRequest().first() }  // 50 requests, each reads one value and leaves
    delay(10_000)
    println("  after 50 requests + 10s: sharing coroutines alive=${appScope.coroutineContext.job.children.count()}, upstream polls=$polls")
    appScope.cancel()
    println("  after appScope.cancel(): alive=${appScope.coroutineContext.job.children.count { it.isActive }}")
}

@OptIn(ExperimentalCoroutinesApi::class)
fun defaultBuffer() = runTest {
    println("== shareIn default buffer: how far can the upstream run ahead of one stuck subscriber?")
    var emitted = 0
    val upstream = flow { repeat(1000) { emit(it); emitted++ } }
    for (cfg in listOf("shareIn(replay=0)", "buffer(0).shareIn(replay=0)", "buffer(10).shareIn(replay=0)", "shareIn(replay=100)")) {
        emitted = 0
        val scope = CoroutineScope(Job() + StandardTestDispatcher(testScheduler))
        val shared = when (cfg) {
            "shareIn(replay=0)" -> upstream.shareIn(scope, SharingStarted.Lazily)
            "buffer(0).shareIn(replay=0)" -> upstream.buffer(0).shareIn(scope, SharingStarted.Lazily)
            "buffer(10).shareIn(replay=0)" -> upstream.buffer(10).shareIn(scope, SharingStarted.Lazily)
            else -> upstream.shareIn(scope, SharingStarted.Lazily, replay = 100)
        }
        backgroundScope.launch { shared.collect { delay(Long.MAX_VALUE) } } // takes one item, then is stuck forever
        advanceTimeBy(10); runCurrent()
        println("  $cfg: upstream emit() calls that returned = $emitted")
        scope.cancel()
    }
}

fun main() { suspendStateIn(); upstreamFailure(); perCallLeak(); defaultBuffer() }
```
Observed output:
```
== suspend stateIn(scope): waits for the first value
  returned at t=300, value=timeout=2s
  t=1800 value=timeout=3s
== suspend stateIn on an empty flow
  NoSuchElementException: Flow is empty
== suspend stateIn when the upstream fails before the first value
  caller got IOException: config server down; scope still active? false
== shareIn: an upstream exception kills the sharing coroutine, not the subscribers
  t=1000 subscriber got [1, 2], still waiting? true; handler saw [IOException: feed reset]; appScope active? true
== leak: calling shareIn per request in a long-lived scope
  after 50 requests + 10s: sharing coroutines alive=50, upstream polls=500
  after appScope.cancel(): alive=0
== shareIn default buffer: how far can the upstream run ahead of one stuck subscriber?
  shareIn(replay=0): upstream emit() calls that returned = 65
  buffer(0).shareIn(replay=0): upstream emit() calls that returned = 1
  buffer(10).shareIn(replay=0): upstream emit() calls that returned = 11
  shareIn(replay=100): upstream emit() calls that returned = 101
```

### D6. Server use cases: an FX cache read through `.value`, a shared Kafka-style poller, internals (lesson 7, A5/A8/A9)
The internals part uses reflection on private fields (`slots`, `buffer`), which may break in any release. Use it for the animation script, not as a lab.
```kotlin
package u1

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

@OptIn(ExperimentalCoroutinesApi::class)
fun fxCache() = runTest {
    println("== FX cache read with .value only (no collector) - virtual time")
    for (started in listOf(SharingStarted.WhileSubscribed(5_000), SharingStarted.Lazily, SharingStarted.Eagerly)) {
        var fetches = 0
        val rateFeed = flow { while (true) { fetches++; emit("1.08${50 + fetches}"); delay(1_000) } }
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
        val eurUsd: StateFlow<String?> = rateFeed.stateIn(scope, started, initialValue = null)
        delay(3_500)
        val reads = List(3) { eurUsd.value }   // three requests read the cache
        println("  $started: three requests read ${reads}, upstream fetches=$fetches, subscriptionCount-driven start? ${started != SharingStarted.Eagerly}")
        scope.cancel()
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
fun kafka() = runTest {
    println("== one Kafka-style poller shared by two handlers (replay=0) - virtual time")
    val strategies = listOf<Pair<String, SharingStarted>>(
        "Eagerly" to SharingStarted.Eagerly,
        "WhileSubscribed()" to SharingStarted.WhileSubscribed(),
        "custom: start when >= 2 subscribers" to SharingStarted { count -> count.map { if (it >= 2) SharingCommand.START else SharingCommand.STOP } },
    )
    for ((label, started) in strategies) {
        var offset = 0
        val records = flow { while (true) { delay(100); emit("rec-${offset++}") } }   // stands in for consumer.poll()
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
        val shared = records.shareIn(scope, started)
        val fraud = mutableListOf<String>(); val ledger = mutableListOf<String>()
        delay(250)
        val j1 = scope.launch { shared.collect { fraud += it } }
        delay(250)
        val j2 = scope.launch { shared.collect { ledger += it } }
        delay(300)
        println("  $label: fraud=${fraud} ledger=${ledger}")
        j1.cancel(); j2.cancel(); scope.cancel()
    }
}

// Peek at the internal arrays (implementation detail, names may change in any release)
fun internals() = runBlocking {
    println("== internals: slot array and buffer array sizes (reflection)")
    val flow = MutableSharedFlow<Int>(replay = 3, extraBufferCapacity = 2)
    fun field(name: String): Any? {
        var c: Class<*>? = flow.javaClass
        while (c != null) { c.declaredFields.firstOrNull { it.name == name }?.let { it.isAccessible = true; return it.get(flow) }; c = c.superclass }
        return "?"
    }
    fun slots() = (field("slots") as Array<*>?)?.size
    fun buffer() = (field("buffer") as Array<*>?)?.size
    println("  new flow: slots=${slots()} buffer=${buffer()}")
    flow.emit(1); println("  after 1 emit, no subscribers: buffer=${buffer()} replayCache=${flow.replayCache}")
    (2..10).forEach { flow.emit(it) }; println("  after 10 emits, no subscribers: buffer=${buffer()} replayCache=${flow.replayCache}")
    val jobs = mutableListOf<Job>()
    for (n in 1..5) {
        jobs += launch(start = CoroutineStart.UNDISPATCHED) { flow.collect { awaitCancellation() } }
        println("  subscribers=$n: slots array length=${slots()} subscriptionCount=${flow.subscriptionCount.value}")
    }
    jobs.forEach { it.cancel() }
}

fun main() { fxCache(); kafka(); internals() }
```
Observed output:
```
== FX cache read with .value only (no collector) - virtual time
  SharingStarted.WhileSubscribed(stopTimeout=5000ms): three requests read [null, null, null], upstream fetches=0, subscriptionCount-driven start? true
  SharingStarted.Lazily: three requests read [null, null, null], upstream fetches=0, subscriptionCount-driven start? true
  SharingStarted.Eagerly: three requests read [1.0854, 1.0854, 1.0854], upstream fetches=4, subscriptionCount-driven start? false
== one Kafka-style poller shared by two handlers (replay=0) - virtual time
  Eagerly: fraud=[rec-2, rec-3, rec-4, rec-5, rec-6] ledger=[rec-5, rec-6]
  WhileSubscribed(): fraud=[rec-0, rec-1, rec-2, rec-3, rec-4] ledger=[rec-2, rec-3, rec-4]
  custom: start when >= 2 subscribers: fraud=[rec-0, rec-1] ledger=[rec-0, rec-1]
== internals: slot array and buffer array sizes (reflection)
  new flow: slots=null buffer=null
  after 1 emit, no subscribers: buffer=2 replayCache=[1]
  after 10 emits, no subscribers: buffer=4 replayCache=[8, 9, 10]
  subscribers=1: slots array length=2 subscriptionCount=1
  subscribers=2: slots array length=2 subscriptionCount=2
  subscribers=3: slots array length=4 subscriptionCount=3
  subscribers=4: slots array length=4 subscriptionCount=4
  subscribers=5: slots array length=8 subscriptionCount=5
```

### D7. A payment-gateway listener bridged with `callbackFlow` (lesson 8, B1/B2)
```kotlin
package b1

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*
import kotlinx.coroutines.flow.*
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList

// A made-up payment-gateway SDK with a listener API.
data class GatewayEvent(val paymentId: String, val status: String)
interface GatewayListener {
    fun onEvent(event: GatewayEvent)
    fun onError(error: Throwable)
    fun onClosed()
}
class Registration(private val action: () -> Unit) { fun unregister() = action() }

class FakeGateway {
    val listeners = CopyOnWriteArrayList<GatewayListener>()
    fun register(l: GatewayListener): Registration { listeners += l; println("    [gateway] registered (listeners=${listeners.size})"); return Registration { listeners -= l; println("    [gateway] unregistered (listeners=${listeners.size})") } }
    fun fire(e: GatewayEvent) = listeners.forEach { it.onEvent(e) }
    fun fail(t: Throwable) = listeners.forEach { it.onError(t) }
    fun close() = listeners.forEach { it.onClosed() }
}

fun FakeGateway.events(): Flow<GatewayEvent> = callbackFlow {
    val reg = register(object : GatewayListener {
        override fun onEvent(event: GatewayEvent) { trySend(event) }      // non-suspending, never blocks the SDK thread
        override fun onError(error: Throwable) { close(error) }           // flow fails with this error
        override fun onClosed() { close() }                               // flow completes normally
    })
    awaitClose { reg.unregister() }                                       // runs on cancel, on close and on error
}

fun FakeGateway.eventsMissingAwaitClose(): Flow<GatewayEvent> = callbackFlow {
    register(object : GatewayListener {
        override fun onEvent(event: GatewayEvent) { trySend(event) }
        override fun onError(error: Throwable) { close(error) }
        override fun onClosed() { close() }
    })
    // forgot awaitClose
}

// fires n events synchronously from inside register(), before the collector can run
fun burst(n: Int): Flow<Int> = callbackFlow {
    var failed = 0
    repeat(n) { if (trySend(it).isFailure) failed++ }
    println("    trySend failures: $failed of $n")
    awaitClose { }
}

suspend fun FakeGateway.awaitRegistered() { while (listeners.isEmpty()) yield() }

fun main() = runBlocking {
    println("== 0. race: firing right after launch, before the producer registered")
    val gw0 = FakeGateway()
    val j0 = launch { gw0.events().collect { println("  got $it") } }
    yield()
    gw0.fire(GatewayEvent("p0", "AUTHORIZED"))
    println("  fired with listeners=${gw0.listeners.size} -> event lost")
    j0.cancelAndJoin()

    println("== 1. callbackFlow without awaitClose")
    try { FakeGateway().eventsMissingAwaitClose().collect { } }
    catch (e: IllegalStateException) { println("  ${e::class.qualifiedName}: ${e.message}") }

    println("== 2. take(2) cancels the collection: awaitClose unregisters")
    val gw = FakeGateway()
    val job = launch { println("  got " + gw.events().take(2).toList()) }
    gw.awaitRegistered()
    gw.fire(GatewayEvent("p1", "AUTHORIZED")); gw.fire(GatewayEvent("p1", "CAPTURED")); gw.fire(GatewayEvent("p1", "SETTLED"))
    job.join()

    println("== 3. the SDK reports an error: close(cause) fails the flow, awaitClose still runs")
    val gw3 = FakeGateway()
    val j3 = launch { try { gw3.events().collect { println("  got $it") } } catch (e: IOException) { println("  collector caught ${e::class.simpleName}: ${e.message}") } }
    gw3.awaitRegistered(); gw3.fire(GatewayEvent("p2", "AUTHORIZED")); yield(); gw3.fail(IOException("gateway connection lost")); j3.join()

    println("== 4. the SDK says it is done: close() completes the flow normally")
    val gw4 = FakeGateway()
    val j4 = launch { println("  completed with " + gw4.events().toList()) }
    gw4.awaitRegistered(); gw4.fire(GatewayEvent("p3", "REFUNDED")); gw4.close(); j4.join()

    println("== 5. a fast callback: 200 events fired before the collector runs")
    println("  default buffer (64, SUSPEND):"); println("    collector got ${burst(200).take(64).count()} (then cancelled)")
    println("  buffer(UNLIMITED):"); println("    collector got ${burst(200).buffer(Channel.UNLIMITED).take(200).count()}")
    println("  conflate():"); println("    collector got ${burst(200).conflate().take(2).toList()}")
    println("  buffer(10, DROP_OLDEST):"); println("    collector got ${burst(200).buffer(10, BufferOverflow.DROP_OLDEST).take(11).toList()}")

    println("== 6. trySend after the channel is closed")
    val ch = Channel<Int>(1); ch.close()
    val r = ch.trySend(1)
    println("  isSuccess=${r.isSuccess} isClosed=${r.isClosed} result=$r")
}
```
Observed output:
```
== 0. race: firing right after launch, before the producer registered
  fired with listeners=0 -> event lost
    [gateway] registered (listeners=1)
    [gateway] unregistered (listeners=0)
== 1. callbackFlow without awaitClose
    [gateway] registered (listeners=1)
  java.lang.IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.
Otherwise, a callback/listener may leak in case of external cancellation.
See callbackFlow API documentation for the details.
== 2. take(2) cancels the collection: awaitClose unregisters
    [gateway] registered (listeners=1)
    [gateway] unregistered (listeners=0)
  got [GatewayEvent(paymentId=p1, status=AUTHORIZED), GatewayEvent(paymentId=p1, status=CAPTURED)]
== 3. the SDK reports an error: close(cause) fails the flow, awaitClose still runs
    [gateway] registered (listeners=1)
  got GatewayEvent(paymentId=p2, status=AUTHORIZED)
    [gateway] unregistered (listeners=0)
  collector caught IOException: gateway connection lost
== 4. the SDK says it is done: close() completes the flow normally
    [gateway] registered (listeners=1)
    [gateway] unregistered (listeners=0)
  completed with [GatewayEvent(paymentId=p3, status=REFUNDED)]
== 5. a fast callback: 200 events fired before the collector runs
  default buffer (64, SUSPEND):
    trySend failures: 135 of 200
    collector got 64 (then cancelled)
  buffer(UNLIMITED):
    trySend failures: 0 of 200
    collector got 200
  conflate():
    trySend failures: 0 of 200
    collector got [0, 199]
  buffer(10, DROP_OLDEST):
    trySend failures: 0 of 200
    collector got [0, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199]
== 6. trySend after the channel is closed
  isSuccess=false isClosed=true result=Closed(kotlinx.coroutines.channels.ClosedSendChannelException: Channel was closed)
```

The compile error for calling `send` from a listener (file `B1Err.kt`):
```kotlin
package b1err
import kotlinx.coroutines.channels.*
import kotlinx.coroutines.flow.*
fun interface Listener { fun onEvent(e: String) }
fun register(l: Listener) {}
fun events(): Flow<String> = callbackFlow {
    register { e -> send(e) }   // send is suspend; the listener is not
    awaitClose { }
}
```
Observed output:
```
demos/B1Err.kt:7:21: error: suspension functions can only be called within coroutine body.
    register { e -> send(e) }   // send is suspend; the listener is not
                    ^^^^
```

### D8. `trySend` vs `trySendBlocking` from a real SDK thread (lesson 8, B2; REAL time, numbers vary)
```kotlin
package b5
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*
import kotlinx.coroutines.flow.*
import kotlin.concurrent.thread

// An SDK that pushes 200 events from its own thread as fast as it can.
fun sdkEvents(useBlocking: Boolean): Flow<Int> = callbackFlow {
    var failed = 0
    val sdk = thread(name = "sdk-io") {
        val t0 = System.nanoTime()
        repeat(200) { if (useBlocking) trySendBlocking(it) else if (trySend(it).isFailure) failed++ }
        println("    sdk thread done after ${(System.nanoTime() - t0) / 1_000_000} ms, trySend failures=$failed")
        channel.close()
    }
    awaitClose { sdk.join() }
}

fun main() = runBlocking {
    for (blocking in listOf(false, true)) {
        println("  ${if (blocking) "trySendBlocking" else "trySend"} into the default 64 buffer, collector takes 2 ms per event (REAL time):")
        val n = sdkEvents(blocking).onEach { delay(2) }.count()
        println("    collector received $n")
    }
}
```
Observed output:
```
  trySend into the default 64 buffer, collector takes 2 ms per event (REAL time):
    sdk thread done after 5 ms, trySend failures=134
    collector received 66
  trySendBlocking into the default 64 buffer, collector takes 2 ms per event (REAL time):
    sdk thread done after 297 ms, trySend failures=0
    collector received 200
```

### D9. `channelFlow` vs `callbackFlow`, and a callbackFlow under test: plain collector vs Turbine (lesson 8, B1/B3/C5)
```kotlin
package b7
import app.cash.turbine.test
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.util.concurrent.CopyOnWriteArrayList

suspend fun quote(acquirer: String, ms: Long): String { delay(ms); return "$acquirer:${ms}ms" }

class Bus { val ls = CopyOnWriteArrayList<(String) -> Unit>(); fun fire(e: String) = ls.forEach { it(e) } }
fun Bus.events() = callbackFlow { val l: (String) -> Unit = { trySend(it) }; ls += l; awaitClose { ls -= l } }

@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    runTest {
        println("== channelFlow: block launches children and returns; the flow completes when the children do")
        val quotes = channelFlow { launch { send(quote("north", 300)) }; launch { send(quote("east", 100)) } }
        println("  ${quotes.toList()} at t=$currentTime")
    }
    runTest {
        println("== callbackFlow with the same shape (no awaitClose)")
        try { callbackFlow { launch { send(quote("north", 300)) } }.toList() } catch (e: IllegalStateException) { println("  ${e::class.simpleName}: ${e.message?.lines()?.first()}") }
    }
    runTest {
        println("== testing a callbackFlow: plain collector vs Turbine")
        val bus = Bus(); val got = mutableListOf<String>()
        backgroundScope.launch { bus.events().collect { got += it } }
        bus.fire("AUTHORIZED"); runCurrent()
        println("  backgroundScope.launch (Standard) then fire: got=$got listeners=${bus.ls.size}")
        val bus2 = Bus()
        bus2.events().test { bus2.fire("AUTHORIZED"); println("  Turbine test{}: listeners at block start=${bus2.ls.size}, awaitItem=${awaitItem()}") }
        println("  after test{}: listeners=${bus2.ls.size}")
    }
}
```
Observed output:
```
== channelFlow: block launches children and returns; the flow completes when the children do
  [east:100ms, north:300ms] at t=300
== callbackFlow with the same shape (no awaitClose)
  IllegalStateException: 'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block.
== testing a callbackFlow: plain collector vs Turbine
  backgroundScope.launch (Standard) then fire: got=[] listeners=1
  Turbine test{}: listeners at block start=1, awaitItem=AUTHORIZED
  after test{}: listeners=0
```

### D10. Reactor interop: `request(n)` both ways, cancellation, threads, context, errors (lesson 8, B5)
```kotlin
package b2

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.reactive.asPublisher
import kotlinx.coroutines.reactor.ReactorContext
import kotlinx.coroutines.reactor.asCoroutineContext
import kotlinx.coroutines.reactor.asFlux
import org.reactivestreams.Subscription
import reactor.core.publisher.BaseSubscriber
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.util.context.Context
import java.io.IOException

fun requests(label: String, block: suspend (Flux<Int>) -> Unit) = runBlocking {
    val log = mutableListOf<String>()
    var delivered = 0
    val flux = Flux.range(1, 300)
        .doOnRequest { n -> log += "request(${if (n == Long.MAX_VALUE) "MAX" else n.toString()}) after $delivered" }
        .doOnNext { delivered++ }
        .doOnCancel { log += "cancel after $delivered" }
        .doOnComplete { log += "complete" }
    block(flux)
    println("  $label: $log")
}

fun main() {
    println("== 1. Flux -> Flow: how collector demand becomes request(n)")
    requests("asFlow()") { it.asFlow().collect { } }
    requests("asFlow().buffer(10)") { it.asFlow().buffer(10).collect { } }
    requests("asFlow().buffer(0)") { it.asFlow().buffer(0).take(3).collect { } }
    requests("asFlow().buffer(UNLIMITED)") { it.asFlow().buffer(Channel.UNLIMITED).collect { } }
    requests("asFlow().conflate()") { it.asFlow().conflate().collect { } }
    requests("asFlow().take(3)") { it.asFlow().take(3).collect { } }

    println("== 2. Flow -> Flux: the flow suspends until Reactor requests more")
    runBlocking {
        val emitted = mutableListOf<Int>()
        val flow = flow { for (i in 1..10) { emit(i); emitted += i } }
        val received = mutableListOf<Int>()
        lateinit var sub: Subscription
        flow.asFlux().subscribe(object : BaseSubscriber<Int>() {
            override fun hookOnSubscribe(s: Subscription) { sub = s; s.request(2) }
            override fun hookOnNext(v: Int) { received += v }
        })
        println("  after request(2): received=$received, emit() calls that returned=$emitted")
        sub.request(3)
        println("  after request(3): received=$received, emit() calls that returned=$emitted")
        sub.cancel()
    }

    println("== 3. Flow -> Flux: take(3) downstream cancels the flow")
    runBlocking {
        val r = flow { var i = 0; while (true) emit(i++) }
            .onCompletion { cause -> println("  flow onCompletion cause=${cause?.let { it::class.simpleName }}") }
            .asFlux().take(3).collectList().block()
        println("  Flux result $r")
    }

    println("== 4. Threads: asFlux() uses Dispatchers.Unconfined by default")
    val names = flow { emit("before delay: " + Thread.currentThread().name); delay(10); emit("after delay: " + Thread.currentThread().name) }
        .asFlux().map { "$it | onNext on " + Thread.currentThread().name }.collectList().block()
    names!!.forEach { println("  $it") }
    val names2 = flow { delay(10); emit(Thread.currentThread().name) }
        .asFlux(Dispatchers.IO).map { "flow ran on $it | onNext on " + Thread.currentThread().name }.blockFirst()
    println("  asFlux(Dispatchers.IO): $names2")

    println("== 5. Context: Reactor Context -> coroutine (asFlux + contextWrite)")
    val seen = flow { emit(currentCoroutineContext()[ReactorContext]?.context?.getOrDefault("traceId", "none") ?: "no ReactorContext") }
        .asFlux().contextWrite(Context.of("traceId", "t-123")).blockFirst()
    println("  flow saw traceId=$seen")
    val seenNone = flow { emit(currentCoroutineContext()[ReactorContext]?.toString() ?: "no ReactorContext") }.asFlux().blockFirst()
    println("  without contextWrite: $seenNone")

    println("== 6. Context: coroutine -> Reactor Context (asFlow inside withContext(ReactorContext))")
    runBlocking {
        val traced = Mono.deferContextual { ctx -> Mono.just(ctx.getOrDefault("traceId", "none")!!) }
        println("  no ReactorContext: ${traced.asFlow().first()}")
        withContext(Context.of("traceId", "t-456").asCoroutineContext()) { println("  inside withContext(Context.of(...).asCoroutineContext()): ${traced.asFlow().first()}") }
    }

    println("== 7. Errors cross both ways")
    runBlocking {
        try { Flux.error<Int>(IOException("acquirer down")).asFlow().collect { } } catch (e: IOException) { println("  Flux.error -> Flow throws ${e::class.simpleName}: ${e.message}") }
    }
    Flux.from(flow<Int> { emit(1); throw IOException("ledger write failed") }.asPublisher())
        .subscribe({ println("  onNext $it") }, { e -> println("  Flow throws -> onError ${e::class.simpleName}: ${e.message}") })
    Thread.sleep(100)
}
```
Observed output:
```
== 1. Flux -> Flow: how collector demand becomes request(n)
  asFlow(): [request(64) after 0, request(64) after 64, request(64) after 128, request(64) after 192, request(64) after 256, complete]
  asFlow().buffer(10): [request(10) after 0, request(10) after 10, request(10) after 20, request(10) after 30, request(10) after 40, request(10) after 50, request(10) after 60, request(10) after 70, request(10) after 80, request(10) after 90, request(10) after 100, request(10) after 110, request(10) after 120, request(10) after 130, request(10) after 140, request(10) after 150, request(10) after 160, request(10) after 170, request(10) after 180, request(10) after 190, request(10) after 200, request(10) after 210, request(10) after 220, request(10) after 230, request(10) after 240, request(10) after 250, request(10) after 260, request(10) after 270, request(10) after 280, request(10) after 290, complete, request(10) after 300]
  asFlow().buffer(0): [request(1) after 0, request(1) after 1, request(1) after 2, cancel after 3]
  asFlow().buffer(UNLIMITED): [request(MAX) after 0, complete]
  asFlow().conflate(): [request(MAX) after 0, complete]
  asFlow().take(3): [request(64) after 0, cancel after 64]
== 2. Flow -> Flux: the flow suspends until Reactor requests more
  after request(2): received=[1, 2], emit() calls that returned=[1]
  after request(3): received=[1, 2, 3, 4, 5], emit() calls that returned=[1, 2, 3, 4]
== 3. Flow -> Flux: take(3) downstream cancels the flow
  flow onCompletion cause=JobCancellationException
  Flux result [0, 1, 2]
== 4. Threads: asFlux() uses Dispatchers.Unconfined by default
  before delay: main | onNext on main
  after delay: kotlinx.coroutines.DefaultExecutor | onNext on kotlinx.coroutines.DefaultExecutor
  asFlux(Dispatchers.IO): flow ran on DefaultDispatcher-worker-1 | onNext on DefaultDispatcher-worker-1
== 5. Context: Reactor Context -> coroutine (asFlux + contextWrite)
  flow saw traceId=t-123
  without contextWrite: no ReactorContext
== 6. Context: coroutine -> Reactor Context (asFlow inside withContext(ReactorContext))
  no ReactorContext: none
  inside withContext(Context.of(...).asCoroutineContext()): t-456
== 7. Errors cross both ways
  Flux.error -> Flow throws IOException: acquirer down
  onNext 1
  Flow throws -> onError IOException: ledger write failed
```

### D11. How far Reactor operators make a Flow run ahead (lesson 8, B5)
```kotlin
package b6
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.reactor.asFlux
import reactor.core.publisher.Flux
import reactor.core.scheduler.Schedulers

fun probe(label: String, op: (Flux<Int>) -> Flux<Int>) {
    val reqs = mutableListOf<String>()
    val src = (1..600).asFlow().asFlux().doOnRequest { reqs += if (it == Long.MAX_VALUE) "MAX" else "$it" }
    op(src).blockLast()
    println("  $label: requests=${reqs.take(6)}${if (reqs.size > 6) " ... (${reqs.size} total)" else ""}")
}
fun main() {
    probe("asFlux().blockLast()") { it }
    probe("asFlux().limitRate(10)") { it.limitRate(10) }
    probe("asFlux().publishOn(single())") { it.publishOn(Schedulers.single()) }
    probe("asFlux().flatMap(Mono::just)") { f -> f.flatMap { reactor.core.publisher.Mono.just(it) } }
}
```
Observed output:
```
  asFlux().blockLast(): requests=[MAX]
  asFlux().limitRate(10): requests=[10, 8, 8, 8, 8, 8] ... (76 total)
  asFlux().publishOn(single()): requests=[256, 192, 192, 192]
  asFlux().flatMap(Mono::just): requests=[256, 192, 192, 192]
```

### D12. The JDK `Flow` bridge and the JDK `HttpClient` (lesson 8, B4/B6; part 3 is REAL time)
```kotlin
package b3

import com.sun.net.httpserver.HttpServer
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.future.await
import kotlinx.coroutines.jdk9.asFlow
import kotlinx.coroutines.jdk9.asPublisher
import org.reactivestreams.FlowAdapters
import reactor.core.publisher.Flux
import java.net.InetSocketAddress
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.ByteBuffer
import java.util.concurrent.Flow as JFlow

fun main() = runBlocking {
    println("== 1. JDK Flow.Publisher -> Flow: same request(n) mapping as the reactive module")
    val log = mutableListOf<String>()
    val jdkPublisher: JFlow.Publisher<Int> = FlowAdapters.toFlowPublisher(Flux.range(1, 150).doOnRequest { log += "request($it)" })
    println("  sum=${jdkPublisher.asFlow().fold(0) { a, b -> a + b }} requests=$log")

    println("== 2. Flow -> JDK Flow.Publisher, consumed by a plain Flow.Subscriber")
    val done = CompletableDeferred<Unit>()
    flowOf("AUTHORIZED", "CAPTURED", "SETTLED").asPublisher().subscribe(object : JFlow.Subscriber<String> {
        lateinit var s: JFlow.Subscription
        override fun onSubscribe(s: JFlow.Subscription) { this.s = s; s.request(1) }
        override fun onNext(item: String) { println("  onNext $item"); s.request(1) }
        override fun onError(t: Throwable) { println("  onError $t"); done.complete(Unit) }
        override fun onComplete() { println("  onComplete"); done.complete(Unit) }
    })
    done.await()

    println("== 3. JDK HttpClient: sendAsync(...).await() + BodyHandlers.ofPublisher() -> asFlow()")
    val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
    server.createContext("/settlements") { ex ->
        ex.sendResponseHeaders(200, 0) // 0 = chunked
        ex.responseBody.use { out -> for (i in 1..5) { out.write("batch-$i\n".toByteArray()); out.flush(); Thread.sleep(50) } }
    }
    server.start()
    val client = HttpClient.newHttpClient()
    val req = HttpRequest.newBuilder(URI("http://127.0.0.1:${server.address.port}/settlements")).build()
    val t0 = System.nanoTime()
    val response: HttpResponse<JFlow.Publisher<List<ByteBuffer>>> =
        client.sendAsync(req, HttpResponse.BodyHandlers.ofPublisher()).await()      // single-shot: CompletableFuture.await()
    println("  status=${response.statusCode()} after ${(System.nanoTime() - t0) / 1_000_000} ms (headers only)")
    val lines = response.body().asFlow()                                              // multi-shot: Flow.Publisher.asFlow()
        .map { buffers -> buffers.joinToString("") { Charsets.UTF_8.decode(it).toString() } }
        .onEach { print("  chunk at ${(System.nanoTime() - t0) / 1_000_000} ms: ${it.replace("\n", "\\n")}\n") }
        .toList()
    println("  body=${lines.joinToString("").trim().lines()}")
    server.stop(0)
    client.close()
}
```
Observed output:
```
== 1. JDK Flow.Publisher -> Flow: same request(n) mapping as the reactive module
  sum=11325 requests=[request(64), request(64), request(64)]
== 2. Flow -> JDK Flow.Publisher, consumed by a plain Flow.Subscriber
  onNext AUTHORIZED
  onNext CAPTURED
  onNext SETTLED
  onComplete
== 3. JDK HttpClient: sendAsync(...).await() + BodyHandlers.ofPublisher() -> asFlow()
  status=200 after 95 ms (headers only)
  chunk at 110 ms: batch-1\n
  chunk at 132 ms: batch-2\n
  chunk at 182 ms: batch-3\n
  chunk at 233 ms: batch-4\n
  chunk at 283 ms: batch-5\n
  body=[batch-1, batch-2, batch-3, batch-4, batch-5]
```

### D13. Java consuming a Kotlin Flow through three faces (lesson 8, B7)
Kotlin facade:
```kotlin
package b4

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.future.future
import kotlinx.coroutines.jdk9.asPublisher
import kotlinx.coroutines.reactor.asFlux
import reactor.core.publisher.Flux
import java.util.concurrent.CompletableFuture

data class PaymentEvent(val id: String, val status: String)

class PaymentEvents(private val scope: CoroutineScope) {
    // the one real implementation, for Kotlin callers
    fun events(): Flow<PaymentEvent> = flow {
        for (s in listOf("AUTHORIZED", "CAPTURED", "SETTLED")) { delay(10); emit(PaymentEvent("p-42", s)) }
    }
    // faces for Java callers
    fun eventsFlux(): Flux<PaymentEvent> = events().asFlux()
    fun eventsPublisher(): java.util.concurrent.Flow.Publisher<PaymentEvent> = events().asPublisher()
    fun firstEvents(n: Int): CompletableFuture<List<PaymentEvent>> = scope.future { events().take(n).toList() }
}
```
Java caller (`javac -d out/B4Facade -cp out/B4Facade:<libs> JavaCaller.java`):
```java
package b4;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Flow;
import kotlinx.coroutines.CoroutineScopeKt;
import kotlinx.coroutines.Dispatchers;

public class JavaCaller {
    public static void main(String[] args) throws Exception {
        var scope = CoroutineScopeKt.CoroutineScope(Dispatchers.getDefault());
        var api = new PaymentEvents(scope);

        List<PaymentEvent> viaFlux = api.eventsFlux().map(e -> e).take(2).collectList().block();
        System.out.println("Flux face:     " + viaFlux);

        System.out.println("Future face:   " + api.firstEvents(3).get());

        var latch = new CountDownLatch(1);
        api.eventsPublisher().subscribe(new Flow.Subscriber<PaymentEvent>() {
            Flow.Subscription s;
            public void onSubscribe(Flow.Subscription s) { this.s = s; s.request(Long.MAX_VALUE); }
            public void onNext(PaymentEvent e) { System.out.println("JDK Flow face: onNext " + e); }
            public void onError(Throwable t) { latch.countDown(); }
            public void onComplete() { System.out.println("JDK Flow face: onComplete"); latch.countDown(); }
        });
        latch.await();
        CoroutineScopeKt.cancel(scope, null);
    }
}
```
Observed output:
```
Flux face:     [PaymentEvent(id=p-42, status=AUTHORIZED), PaymentEvent(id=p-42, status=CAPTURED)]
Future face:   [PaymentEvent(id=p-42, status=AUTHORIZED), PaymentEvent(id=p-42, status=CAPTURED), PaymentEvent(id=p-42, status=SETTLED)]
JDK Flow face: onNext PaymentEvent(id=p-42, status=AUTHORIZED)
JDK Flow face: onNext PaymentEvent(id=p-42, status=CAPTURED)
JDK Flow face: onNext PaymentEvent(id=p-42, status=SETTLED)
JDK Flow face: onComplete
```

### D14. Testing: virtual time, dispatchers, `advance*`, StateFlow traps, the error messages (lesson 8, C1-C5)
```kotlin
package t1

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.minutes

class PaymentTracker {
    private val _status = MutableStateFlow("PENDING")
    val status: StateFlow<String> = _status.asStateFlow()
    fun authorizeAndCapture() { _status.value = "AUTHORIZED"; _status.value = "CAPTURED" }      // two sets, no suspension
    suspend fun authorizeThenCapture() { _status.value = "AUTHORIZED"; delay(100); _status.value = "CAPTURED" }
}

@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    val realStart = System.nanoTime()
    runTest {
        delay(10.minutes)
        println("== 1. virtual time: delay(10.minutes) -> currentTime=$currentTime, real ms=${(System.nanoTime() - realStart) / 1_000_000}")
    }

    runTest {
        println("== 2. launch order: StandardTestDispatcher (default) vs UnconfinedTestDispatcher")
        val order = mutableListOf<String>()
        launch { order += "standard child" }
        order += "body after launch"
        launch(UnconfinedTestDispatcher(testScheduler)) { order += "unconfined child" }
        order += "body after unconfined launch"
        runCurrent()
        println("  $order")
    }

    runTest {
        println("== 3. advanceTimeBy(n) runs tasks due BEFORE now+n; the task due exactly at now+n needs runCurrent()")
        val fired = mutableListOf<Long>()
        launch { delay(100); fired += currentTime }
        launch { delay(200); fired += currentTime }
        advanceTimeBy(100); println("  after advanceTimeBy(100): t=$currentTime fired=$fired")
        runCurrent();       println("  after runCurrent():       t=$currentTime fired=$fired")
        advanceUntilIdle(); println("  after advanceUntilIdle(): t=$currentTime fired=$fired")
    }

    runTest {
        println("== 4. advanceUntilIdle() does not drive backgroundScope; advanceTimeBy does")
        var ticks = 0
        backgroundScope.launch { while (true) { delay(1000); ticks++ } }
        advanceUntilIdle(); println("  after advanceUntilIdle(): t=$currentTime ticks=$ticks")
        advanceTimeBy(5000); runCurrent(); println("  after advanceTimeBy(5000)+runCurrent(): t=$currentTime ticks=$ticks")
    }

    println("== 5. collecting a StateFlow in a test: the conflation trap")
    runTest {
        val t = PaymentTracker(); val seen = mutableListOf<String>()
        backgroundScope.launch { t.status.toList(seen) }      // StandardTestDispatcher
        runCurrent()
        t.authorizeAndCapture(); runCurrent()
        println("  Standard collector, two sets without suspension:   $seen")
    }
    runTest {
        val t = PaymentTracker(); val seen = mutableListOf<String>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { t.status.toList(seen) }
        t.authorizeAndCapture()
        println("  Unconfined collector, two sets without suspension: $seen")
    }
    runTest {
        val t = PaymentTracker(); val seen = mutableListOf<String>()
        backgroundScope.launch { t.status.toList(seen) }
        runCurrent()
        t.authorizeThenCapture(); runCurrent()
        println("  Standard collector, sets separated by delay(100):  $seen")
    }

    println("== 6. take(n).toList() on a StateFlow that conflates: the test hangs until runTest's timeout")
    try {
        runTest(timeout = 500.milliseconds) {
            val t = PaymentTracker()
            val result = async { t.status.take(3).toList() }
            runCurrent()
            t.authorizeAndCapture()
            println("  got ${result.await()}")
        }
    } catch (e: Throwable) { println("  ${e::class.qualifiedName}: ${e.message?.lines()?.first()}") }

    println("== 7. collecting forever in the test scope instead of backgroundScope")
    try {
        runTest(timeout = 500.milliseconds) {
            val t = PaymentTracker()
            launch { t.status.collect { } }   // never completes
        }
    } catch (e: Throwable) { println("  ${e::class.qualifiedName}: ${e.message?.lines()?.first()}") }

    println("== 8. stateIn(this, ...) inside runTest, finite upstream flowOf(1, 2, 3)")
    for (started in listOf(SharingStarted.Eagerly, SharingStarted.WhileSubscribed())) {
        try {
            runTest(timeout = 500.milliseconds) {
                val s = flowOf(1, 2, 3).stateIn(this, started, 0)
                val first = s.first { it == 3 }
                println("  $started: saw $first, body done")
            }
            println("  $started: test passed")
        } catch (e: Throwable) { println("  $started: ${e::class.qualifiedName}: ${e.message?.lines()?.first()}") }
    }

    runTest {
        println("== 9. SharedFlow + take(n).toList(): subscribe first, then emit")
        val events = MutableSharedFlow<String>()
        val result = async { events.take(2).toList() }
        runCurrent()   // without this the emits below happen before anyone subscribed (replay=0) and are lost
        events.emit("AUTHORIZED"); events.emit("CAPTURED")
        println("  ${result.await()}")
    }

    runTest {
        println("== 10. withTimeout inside runTest is virtual too")
        val r = withTimeoutOrNull(5_000) { delay(10_000); "late" }
        println("  result=$r at t=$currentTime")
    }
}
```
Observed output:
```
== 1. virtual time: delay(10.minutes) -> currentTime=600000, real ms=162
== 2. launch order: StandardTestDispatcher (default) vs UnconfinedTestDispatcher
  [body after launch, unconfined child, body after unconfined launch, standard child]
== 3. advanceTimeBy(n) runs tasks due BEFORE now+n; the task due exactly at now+n needs runCurrent()
  after advanceTimeBy(100): t=100 fired=[]
  after runCurrent():       t=100 fired=[100]
  after advanceUntilIdle(): t=200 fired=[100, 200]
== 4. advanceUntilIdle() does not drive backgroundScope; advanceTimeBy does
  after advanceUntilIdle(): t=0 ticks=0
  after advanceTimeBy(5000)+runCurrent(): t=5000 ticks=5
== 5. collecting a StateFlow in a test: the conflation trap
  Standard collector, two sets without suspension:   [PENDING, CAPTURED]
  Unconfined collector, two sets without suspension: [PENDING, AUTHORIZED, CAPTURED]
  Standard collector, sets separated by delay(100):  [PENDING, AUTHORIZED, CAPTURED]
== 6. take(n).toList() on a StateFlow that conflates: the test hangs until runTest's timeout
  kotlinx.coroutines.test.UncompletedCoroutinesError: After waiting for 500ms, the test body did not run to completion
== 7. collecting forever in the test scope instead of backgroundScope
  kotlinx.coroutines.test.UncompletedCoroutinesError: After waiting for 500ms, there were active child jobs: [StandaloneCoroutine{Active}@17b8767a]. Use `TestScope.backgroundScope` to launch the coroutines that need to be cancelled when the test body finishes
== 8. stateIn(this, ...) inside runTest, finite upstream flowOf(1, 2, 3)
  SharingStarted.Eagerly: saw 3, body done
  SharingStarted.Eagerly: test passed
  SharingStarted.WhileSubscribed(): saw 3, body done
  SharingStarted.WhileSubscribed(): kotlinx.coroutines.test.UncompletedCoroutinesError: After waiting for 500ms, there were active child jobs: [StandaloneCoroutine{Active}@605bdb2a]. Use `TestScope.backgroundScope` to launch the coroutines that need to be cancelled when the test body finishes
== 9. SharedFlow + take(n).toList(): subscribe first, then emit
  [AUTHORIZED, CAPTURED]
== 10. withTimeout inside runTest is virtual too
  result=null at t=5000
```

### D15. Turbine 1.2.1 on kotlinx.coroutines 1.11.0 (lesson 8, C6)
"FAIL" lines are expected: they show the failure message a learner will meet. Case 7 takes 3 s of real time (the default timeout).
```kotlin
package t2

import app.cash.turbine.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.io.IOException
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

class PaymentTracker {
    private val _status = MutableStateFlow("PENDING")
    val status: StateFlow<String> = _status.asStateFlow()
    fun authorizeAndCapture() { _status.value = "AUTHORIZED"; _status.value = "CAPTURED" }
}

fun check(name: String, block: () -> Unit) {
    try { block(); println("  PASS $name") }
    catch (e: Throwable) { println("  FAIL $name -> ${e::class.qualifiedName}: ${e.message?.lines()?.take(3)?.joinToString(" | ")}") }
}

fun eq(expected: Any?, actual: Any?) { if (expected != actual) throw AssertionError("expected <$expected> but was <$actual>") }

@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    println("== Turbine 1.2.1 with kotlinx.coroutines 1.11.0 at runtime")
    check("cold flow: awaitItem x2 + awaitComplete") { runTest { flowOf("one", "two").test { eq("one", awaitItem()); eq("two", awaitItem()); awaitComplete() } } }
    check("unconsumed events fail the test") { runTest { flowOf("one", "two").test { eq("one", awaitItem()) } } }
    check("cancelAndIgnoreRemainingEvents") { runTest { flowOf("one", "two").test { eq("one", awaitItem()); cancelAndIgnoreRemainingEvents() } } }
    check("awaitError") { runTest { flow<Int> { emit(1); throw IOException("issuer 503") }.test { eq(1, awaitItem()); eq("issuer 503", awaitError().message) } } }
    check("StateFlow: two synchronous sets, are both seen?") {
        runTest {
            val t = PaymentTracker()
            t.status.test {
                eq("PENDING", awaitItem())
                t.authorizeAndCapture()
                eq("AUTHORIZED", awaitItem())
                eq("CAPTURED", awaitItem())
            }
        }
    }
    check("SharedFlow: emit inside test {} after subscription") {
        runTest {
            val events = MutableSharedFlow<String>()
            events.test { events.emit("AUTHORIZED"); eq("AUTHORIZED", awaitItem()) }
        }
    }
    val t0 = System.nanoTime()
    check("SharedFlow: emit BEFORE test {} is lost (default 3 s wall-clock timeout)") {
        runTest {
            val events = MutableSharedFlow<String>()
            events.emit("AUTHORIZED")
            events.test { eq("AUTHORIZED", awaitItem()) }
        }
    }
    println("    (that took ${(System.nanoTime() - t0) / 1_000_000} ms of real time)")
    check("a VIRTUAL delay(10s) in the flow does not trip a 200 ms Turbine timeout") {
        runTest { flow { delay(10.seconds); emit("late") }.test(timeout = 200.milliseconds) { eq("late", awaitItem()); awaitComplete() } }
    }
    check("a REAL 500 ms of blocking work trips a 200 ms Turbine timeout") {
        runTest { flow { withContext(Dispatchers.IO) { Thread.sleep(500) }; emit("late") }.test(timeout = 200.milliseconds) { eq("late", awaitItem()); awaitComplete() } }
    }
    check("expectNoEvents / skipItems / expectMostRecentItem") {
        runTest {
            val ticks = flow { var i = 0; while (true) { delay(100); emit(i++) } }
            ticks.test {
                expectNoEvents()              // nothing at t=0
                skipItems(2)                  // 0, 1
                eq(2, awaitItem())
                delay(250)                    // 3 and 4 arrive
                eq(4, expectMostRecentItem())
                cancelAndIgnoreRemainingEvents()
            }
        }
    }
    check("turbineScope + testIn for two flows") {
        runTest {
            turbineScope {
                val rates = flowOf(1.0850, 1.0851).testIn(backgroundScope, name = "rates")
                val alerts = flowOf("drift").testIn(backgroundScope, name = "alerts")
                eq(1.0850, rates.awaitItem()); eq("drift", alerts.awaitItem())
                eq(1.0851, rates.awaitItem()); rates.awaitComplete(); alerts.awaitComplete()
            }
        }
    }
    check("named turbine in an error") { runTest { turbineScope { val r = flowOf(1).testIn(backgroundScope, name = "rates"); r.awaitComplete() } } }
    check("standalone Turbine<T>() in a fake listener") {
        runTest {
            val ledgerWrites = Turbine<String>(name = "ledger")
            val writer: (String) -> Unit = { ledgerWrites.add(it) }   // what a fake repository would call
            launch { delay(50); writer("debit p-42 10.00") }
            eq("debit p-42 10.00", ledgerWrites.awaitItem())
            ledgerWrites.ensureAllEventsConsumed()
        }
    }
}
```
Observed output:
```
== Turbine 1.2.1 with kotlinx.coroutines 1.11.0 at runtime
  PASS cold flow: awaitItem x2 + awaitComplete
  FAIL unconsumed events fail the test -> app.cash.turbine.TurbineAssertionError: Unconsumed events found: |  - Item(two) |  - Complete
  PASS cancelAndIgnoreRemainingEvents
  PASS awaitError
  PASS StateFlow: two synchronous sets, are both seen?
  PASS SharedFlow: emit inside test {} after subscription
  FAIL SharedFlow: emit BEFORE test {} is lost (default 3 s wall-clock timeout) -> app.cash.turbine.TurbineAssertionError: No value produced in 3s
    (that took 3005 ms of real time)
  PASS a VIRTUAL delay(10s) in the flow does not trip a 200 ms Turbine timeout
  FAIL a REAL 500 ms of blocking work trips a 200 ms Turbine timeout -> app.cash.turbine.TurbineAssertionError: No value produced in 200ms
  PASS expectNoEvents / skipItems / expectMostRecentItem
  PASS turbineScope + testIn for two flows
  FAIL named turbine in an error -> app.cash.turbine.TurbineAssertionError: Expected complete for rates but found Item(1)
  PASS standalone Turbine<T>() in a fake listener
```

`testIn` outside `turbineScope` (file `T2Err.kt`) compiles and fails at runtime:
```kotlin
package t2err
import app.cash.turbine.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
fun x() = runTest { val t = flowOf(1).testIn(backgroundScope); t.awaitItem() }
fun main() { try { x() } catch (e: Throwable) { println("${e::class.qualifiedName}: ${e.message}") } }
```
Observed output:
```
java.lang.AssertionError: Turbine can only collect flows within a TurbineContext. Wrap with turbineScope { .. }
```

### D16. Extra checks: StateFlow identity, in-place mutation, `update` re-runs, `shareIn` replay reset, `FlowAdapters` without jdk9 (lessons 7/8)
Part 3 is REAL threads (the lambda-call count varies).
```kotlin
package x1
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.reactive.asPublisher
import kotlinx.coroutines.test.*
import org.reactivestreams.FlowAdapters
import java.util.concurrent.SubmissionPublisher
import java.util.concurrent.atomic.AtomicInteger

data class Rate(val pair: String, val mid: String)

@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    println("== 1. an equal value keeps the OLD reference")
    val first = Rate("EURUSD", "1.0850"); val second = Rate("EURUSD", "1.0850")
    val s = MutableStateFlow(first); s.value = second
    println("  value === first? ${s.value === first}; value === second? ${s.value === second}")

    println("== 2. mutating a list in place, then setting it again, emits nothing")
    runTest {
        val list = mutableListOf("p1"); val st = MutableStateFlow<List<String>>(list); val seen = mutableListOf<List<String>>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { st.collect { seen += it.toList() } }
        list += "p2"; st.value = list
        st.value = list + "p3"
        println("  collector saw $seen")
    }

    println("== 3. update {} may run its lambda more than once (8 coroutines x 100_000, REAL threads)")
    val calls = AtomicInteger(); val counter = MutableStateFlow(0)
    runBlocking(Dispatchers.Default) { repeat(8) { launch { repeat(100_000) { counter.update { calls.incrementAndGet(); it + 1 } } } } }
    println("  value=${counter.value} lambda calls=${calls.get()}")

    println("== 4. shareIn(replay=1, WhileSubscribed(0, 0)): replay cache is reset after stop")
    runTest {
        val shared = flow { var i = 0; while (true) { emit(i++); delay(100) } }.shareIn(backgroundScope, SharingStarted.WhileSubscribed(0, 0), replay = 1)
        val j = backgroundScope.launch { shared.collect { } }
        delay(250); println("  while subscribed: replayCache=${shared.replayCache}")
        j.cancel(); runCurrent(); println("  after last subscriber left: replayCache=${shared.replayCache}")
        val shared2 = flow { var i = 0; while (true) { emit(i++); delay(100) } }.shareIn(backgroundScope, SharingStarted.WhileSubscribed(0), replay = 1)
        val j2 = backgroundScope.launch { shared2.collect { } }
        delay(250); j2.cancel(); runCurrent(); println("  default replayExpiration: replayCache after stop=${shared2.replayCache}")
    }

    println("== 5. JDK Flow without the jdk9 module: reactive-streams FlowAdapters + kotlinx-coroutines-reactive")
    runBlocking {
        val pub = SubmissionPublisher<String>()
        val job = launch(Dispatchers.Default) { println("  received " + FlowAdapters.toPublisher(pub).asFlow().take(2).toList()) }
        while (pub.numberOfSubscribers == 0) delay(5)
        pub.submit("AUTHORIZED"); pub.submit("CAPTURED"); job.join(); pub.close()
        val jdk: java.util.concurrent.Flow.Publisher<String> = FlowAdapters.toFlowPublisher(flowOf("a", "b").asPublisher())
        println("  Flow -> JDK publisher via FlowAdapters: ${FlowAdapters.toPublisher(jdk).asFlow().toList()}")
    }
}
```
Observed output:
```
== 1. an equal value keeps the OLD reference
  value === first? true; value === second? false
== 2. mutating a list in place, then setting it again, emits nothing
  collector saw [[p1], [p1, p2, p3]]
== 3. update {} may run its lambda more than once (8 coroutines x 100_000, REAL threads)
  value=800000 lambda calls=1390485
== 4. shareIn(replay=1, WhileSubscribed(0, 0)): replay cache is reset after stop
  while subscribed: replayCache=[2]
  after last subscriber left: replayCache=[]
  default replayExpiration: replayCache after stop=[2]
== 5. JDK Flow without the jdk9 module: reactive-streams FlowAdapters + kotlinx-coroutines-reactive
  received [AUTHORIZED, CAPTURED]
  Flow -> JDK publisher via FlowAdapters: [a, b]
```

### Stability probe used for the signatures table
```kotlin
package s1
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.reactive.asPublisher
import kotlinx.coroutines.reactor.asFlux
import kotlinx.coroutines.reactor.ReactorContext
import reactor.core.publisher.Flux
import kotlin.time.Duration.Companion.seconds
fun probe(scope: CoroutineScope) = runTest {
    val msf = MutableSharedFlow<Int>(replay = 1, extraBufferCapacity = 1, onBufferOverflow = BufferOverflow.DROP_OLDEST)
    msf.resetReplayCache()                                            // L14
    msf.subscriptionCount                                             // L15
    msf.asFlow()                                                      // L16 SharedFlow.asFlow
    MutableStateFlow(0).onSubscription { }                            // L17
    flowOf(1).shareIn(scope, SharingStarted.WhileSubscribed(5_000, 0))// L18
    flowOf(1).stateIn(scope, SharingStarted.Lazily, 0)                // L19
    flowOf(1).stateIn(scope)                                          // L20
    callbackFlow<Int> { trySendBlocking(1); awaitClose { } }          // L21
    channelFlow<Int> { send(1) }                                      // L22
    Flux.just(1).asFlow(); flowOf(1).asPublisher(); flowOf(1).asFlux()// L23
    currentCoroutineContext()[ReactorContext]                         // L24
    backgroundScope.launch { }                                        // L25
    StandardTestDispatcher(testScheduler)                             // L26
    UnconfinedTestDispatcher(testScheduler)                           // L27
    currentTime                                                       // L28 TestScope.currentTime
    advanceUntilIdle(); runCurrent(); advanceTimeBy(1)                // L29 TestScope extensions
    testScheduler.advanceUntilIdle(); testScheduler.runCurrent()      // L30
    testScheduler.currentTime                                         // L31
    testScheduler.advanceTimeBy(1.seconds)                            // L32
    MutableStateFlow(0).update { it + 1 }                             // L33
    flowOf(1).conflate().buffer(2)                                    // L34
}
```
Compiler output: warnings `needs opt-in kotlinx.coroutines.ExperimentalCoroutinesApi` on lines 14 (`resetReplayCache`), 16 (`SharedFlow.asFlow`), 27 (`UnconfinedTestDispatcher`), 28 (`TestScope.currentTime`), 29 (×3: `TestScope.advanceUntilIdle`, `runCurrent`, `advanceTimeBy`) and 31 (`testScheduler.currentTime`), and no other warnings. [Local]

---

## Exercise ideas (labs with deterministic tests)

All tests run under `runTest` (virtual time), so they are exact and fast. Each one names the assertion that makes it deterministic.

- **E1. Fix the lossy transition bus (lesson 7).** The stub has `MutableSharedFlow<Transition>()` and `fun publish(t) = bus.tryEmit(t)` called from a non-suspending Kafka-listener callback.
  - Test: one subscriber on `UnconfinedTestDispatcher` blocks on a `CompletableDeferred` gate inside `collect`. Call `publish` 10 times and assert all 10 return `true`. Open the gate and assert the subscriber received `1..10` in order.
  - The stub fails at once (`false` ×10). The fix is `extraBufferCapacity = 64` (or more), with the policy stated.
  - Bonus test: an 11th publish beyond `replay + extra` returns `false`.
- **E2. Predict the table (lesson 7).** The learner writes `fun predictTryEmits(replay: Int, extra: Int, policy: BufferOverflow, subscribers: Int, n: Int): List<Boolean>` from the rule in A1. A parameterized test compares it with the real flow, using the D1 harness (subscribers subscribed with `runCurrent()`, then `n` back-to-back `tryEmit`s). Cases: every row of the A1 table plus `subscribers = 0`.
- **E3. The FX-rate cache (lesson 7).** Write `class RateCache(scope: CoroutineScope, feed: Flow<Rate>) { fun current(): Rate? }`. Tests:
  - (a) 100 concurrent `current()` calls at t=3500 trigger exactly one upstream start and return the latest rate. This forces `Eagerly`; a `WhileSubscribed` solution returns `null` (D6).
  - (b) When the feed throws `IOException` at t=2000, the cache keeps the last rate and retries after 1000 ms (a `retryWhen` above `stateIn`). Assert the start count is 2 at t=3000.
  - (c) An equal rate published again produces no change notification to a collector.
- **E4. Reconnecting dashboards (lesson 7).** `fun quotes(scope): StateFlow<Quote?>` with `WhileSubscribed(5_000)`. Tests script subscribe/leave/rejoin at fixed virtual times and assert the upstream start count:
  - 1 when the rejoin is at +1500 ms;
  - 2 when it is at +8000 ms, with the first value seen after the rejoin being the stale quote;
  - with `replayExpirationMillis = 0`, the first value after a late rejoin is `null`.
  (Numbers from D4.)
- **E5. Find the leak (lesson 7).** `PaymentStatusService.statusFor(id)` calls `shareIn` on every call. The test calls it 50 times, then asserts `scope.coroutineContext.job.children.count() == 1` and that the upstream poll counter is at most 11 after 10 s of virtual time. The stub gives 50 and 500 (D5).
- **E6. The gateway bridge (lesson 8).** Implement `FakeGateway.events()` with `callbackFlow`. Tests:
  - `take(2)` leaves `listeners.size == 0`;
  - `onError(IOException)` fails the flow with that exception and still unregisters;
  - `onClosed()` completes normally;
  - a 200-event synchronous burst with `buffer(UNLIMITED)` delivers 200 (and the default delivers exactly 65 accepted, if the lab wants learners to measure it);
  - a stub version without `awaitClose` makes the first test fail with the exact `IllegalStateException` text.
  Wait for registration in tests (`while (gw.listeners.isEmpty()) yield()`), or use Turbine.
- **E7. Demand you can see (lesson 8).**
  - (a) `fun Flux<Int>.collectInBatches(n: Int): Flow<Int> = asFlow().buffer(n)`. The test logs `doOnRequest` and asserts that the first request is `n` and the request count for 300 elements is `300 / n` (D10).
  - (b) `fun ledgerEntries(): Flux<Entry> = flow.asFlux()`. A `StepVerifier.create(flux, 0)` (reactor-test is already on the labs' test classpath) with `.thenRequest(2).expectNextCount(2)` also asserts, through a side-effect list, that the flow's `emit` returned only once (parked in the second `emit`).
- **E8. Trace ids across the bridge (lesson 8).** `fun traceIdSeen(): Flow<String>` reads `currentCoroutineContext()[ReactorContext]`. Tests: `asFlux().contextWrite(Context.of("traceId", "t-1"))` emits `"t-1"`, and without `contextWrite` it emits `"none"`. In the reverse direction, `Mono.deferContextual` collected through `asFlow()` inside `withContext(Context.of(...).asCoroutineContext())`.
- **E9. Test the tracker three ways (lesson 8).** Given `authorizeAndCapture()` (two synchronous sets), write:
  - (a) a Standard `backgroundScope` collector test that asserts `[PENDING, CAPTURED]` (documenting conflation);
  - (b) an `UnconfinedTestDispatcher` collector test that asserts all three;
  - (c) a Turbine test with `awaitItem()` ×3;
  - (d) a `take(3).toList()` test that is *expected* to time out. Use `runTest(timeout = 500.milliseconds)` and `assertThrows<UncompletedCoroutinesError>`.
- **E10. A face for Java (lesson 8).** A Kotlin `PaymentEvents` facade (D13) and a Java JUnit test that uses only `Flux`, `java.util.concurrent.Flow` and `CompletableFuture` types: `eventsFlux().take(2).collectList().block()`, and `firstEvents(3).get(1, SECONDS)`. Use `FlowAdapters` for the JDK face so that no jdk9 dependency is needed.
- **E11. A gate for the shared Kafka poller (lesson 7, stretch).** Write `fun SharingStarted.Companion.WhenAtLeast(n: Int)` (the KDoc example) and show with the D6 harness that both handlers receive `rec-0`, while with `WhileSubscribed()` the second handler misses `rec-0` and `rec-1`.

---

## Verified URLs

**Fetched in this session (content read):**
- kotlinx.coroutines source at the `1.11.0` tag (raw.githubusercontent.com, HTTP 200):
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/SharedFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/StateFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/operators/Share.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/SharingStarted.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/internal/AbstractSharedFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/internal/ChannelFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/Builders.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/channels/BufferOverflow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/channels/Produce.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/channels/Channel.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/concurrent/src/channels/Channels.kt (`trySendBlocking`; the `jvm/src/channels/Channels.kt` path is a 404)
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactive/src/ReactiveFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactive/src/ContextInjector.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactive/src/Publish.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactive/README.md
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactor/src/ReactorFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactor/src/ReactorContext.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactor/src/ReactorContextInjector.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-reactor/README.md
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-jdk9/src/ReactiveFlow.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/reactive/kotlinx-coroutines-jdk9/README.md
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/common/src/TestBuilders.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/common/src/TestScope.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/common/src/TestCoroutineDispatchers.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/common/src/TestCoroutineScheduler.kt
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/README.md
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/CHANGES.md (1.11.0 section)
  - https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/gradle.properties (`version=1.11.0-SNAPSHOT` in the tree, `kotlin_version=2.2.20`, `reactor_version=3.4.1`)
- Turbine (raw.githubusercontent.com, HTTP 200):
  - https://raw.githubusercontent.com/cashapp/turbine/trunk/README.md
  - https://raw.githubusercontent.com/cashapp/turbine/trunk/CHANGELOG.md
  - https://raw.githubusercontent.com/cashapp/turbine/1.2.1/src/commonMain/kotlin/app/cash/turbine/flow.kt (also `Turbine.kt`, `ReceiveTurbine.kt`, `coroutines.kt` in the same folder)
- Maven Central (HTTP 200; artifacts downloaded and inspected):
  - https://repo1.maven.org/maven2/app/cash/turbine/turbine/maven-metadata.xml (latest 1.2.1) and https://repo1.maven.org/maven2/app/cash/turbine/turbine/ (directory listing)
  - https://repo1.maven.org/maven2/app/cash/turbine/turbine-jvm/1.2.1/ (`turbine-jvm-1.2.1.jar`, `.pom`, `.module`)
  - https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-jdk9/maven-metadata.xml (latest 1.11.0) and https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-jdk9/1.11.0/ (jar, pom, module)
  - https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-reactive/maven-metadata.xml and https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-reactor/maven-metadata.xml (latest 1.11.0)
- kotlinlang.org (HTTP 200; the keyword I looked for was present unless noted):
  - https://kotlinlang.org/docs/coroutines-flow.html (the official Flow guide; it now has a hot-flows section on SharedFlow, StateFlow, `shareIn`/`stateIn` and "Cancel hot flows"). https://kotlinlang.org/docs/flow.html is a redirect page to it.
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow.html (constructor function; the interface page `-mutable-shared-flow/` also loads)
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-state-flow/
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/try-emit.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/subscription-count.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/share-in.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/state-in.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/-companion/-while-subscribed.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/update.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/channel-flow.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/await-close.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/try-send-blocking.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactive/ and https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactive/kotlinx.coroutines.reactive/as-flow.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactive/kotlinx.coroutines.reactive/as-publisher.html (loads; the word "TCK" is in the module README, not on this page)
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/ and https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/kotlinx.coroutines.reactor/as-flux.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/kotlinx.coroutines.reactor/-reactor-context/
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-jdk9/ and https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-jdk9/kotlinx.coroutines.jdk9/as-flow.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/ and https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-scope/background-scope.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-standard-test-dispatcher.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-unconfined-test-dispatcher.html (has the StateFlow example quoted in C2)
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-coroutine-scheduler/advance-time-by.html
  - https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-coroutine-scheduler/advance-until-idle.html
- https://developer.android.com/kotlin/flow/test ("Testing StateFlows": the conflation warning, `backgroundScope.launch(UnconfinedTestDispatcher(testScheduler))`, and Turbine)

**Blocked by this session's network (not verified here; re-check before citing):**
- https://github.com/cashapp/turbine and https://github.com/Kotlin/kotlinx.coroutines/blob/1.11.0/... (github.com web pages returned 403 through the proxy; the same files were read through raw.githubusercontent.com). api.github.com also refused ("GitHub access to this repository is not enabled for this session").
- https://central.sonatype.com/artifact/app.cash.turbine/turbine (CONNECT 403; repo1.maven.org was used instead)
- https://projectreactor.io/docs/core/release/reference/ (Reactor reference: not fetched; the Reactor demand numbers in D11 are Local only)
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Flow.html and https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpResponse.BodyHandlers.html (JDK Javadoc: not fetched; the HttpClient behaviour in D12 is Local only)
- https://www.reactive-streams.org/ (spec site: not fetched)

---

## Notes for the lesson writer

- **Correct co-08 in the new track rather than repeat it.** co-08 says `tryEmit` on default parameters "fails whenever a subscriber is busy". The source and the demo say it fails whenever there is any subscriber at all (D1, misconception 1). co-08's "deeper" box mentions `SharedFlow.asFlow()` (new in 1.11) without saying that it is `@ExperimentalCoroutinesApi`.
- **co-09's "the buffer (64 by default)"** is right, but a learner who measures it will count 65 accepted `trySend`s when the collector is already waiting (D7). Say so before they find it.
- **co-07 and co-08 cite `https://kotlinlang.org/docs/flow.html`.** That URL is now a redirect page to `https://kotlinlang.org/docs/coroutines-flow.html`, which has a proper hot-flows section. Cite the target.
- **Use virtual time for every timeline** in lessons and videos (D1, D4, D5, D6, D14). Every number there is exact and repeatable. The REAL-time numbers (D3 part G, D8, D12 part 3, D16 part 3) vary from run to run. Present them as "for example" and never as exact.
- **`advanceUntilIdle()` vs `backgroundScope`** caught me while writing the D1 harness. Expect learners to hit it in the first lab that collects a hot flow in `backgroundScope`. Teach `advanceTimeBy(...) + runCurrent()` (or Turbine) for background collectors.
- **Labs wiring** (read only, nothing changed):
  - `labs/flows/build.gradle.kts` already has core, reactive, reactor, reactor-core 3.8.8, coroutines-test (`testImplementation` and `demoImplementation`) and reactor-test.
  - It has neither Turbine nor the jdk9 module.
  - The root `labs/build.gradle.kts` sets `junit.jupiter.execution.timeout.default = 20 s`, so a hung `runTest` fails at 20 s through JUnit, not at 60 s.
  - For the JDK `Flow` demos, use `org.reactivestreams.FlowAdapters` (already on the classpath through kotlinx-coroutines-reactive) instead of adding `kotlinx-coroutines-jdk9` (D16). Mention the jdk9 artifact by name as the convenience option.
- **Turbine recommendation: add `testImplementation("app.cash.turbine:turbine:1.2.1")`** to `labs/flows` (someone who owns the labs build makes the change).
  - Why:
    - it is the current release;
    - it resolves from Maven Central;
    - Gradle aligns its coroutines 1.10.2 dependencies to the pinned 1.11.0, adding no new transitive jars;
    - every README behaviour reproduced on 1.11.0 (D15);
    - it removes the two traps that cost the most time in flow tests: the subscribe/register-before-emit race (D9) and hangs (3 s failures instead of a 20 s JUnit timeout).
  - Caveats to teach:
    - (1) It collects on `UnconfinedTestDispatcher`, so it shows *every* StateFlow value. In lesson 7's conflation labs, use plain Standard collectors so that learners actually see conflation (C4).
    - (2) Its timeout is wall-clock (3 s), separate from virtual time.
    - (3) `testIn` must sit inside `turbineScope { }` (runtime `AssertionError` otherwise).
    - (4) Its README admits a dependency on the experimental `UnconfinedTestDispatcher`, so a future kotlinx.coroutines release could change its behaviour. Re-run D15 when bumping coroutines.
    - (5) The README's sample message "No value produced in 1s" is stale; 1.2.1 prints "in 3s".
- **Stability call-outs for code in lessons:** `@OptIn(ExperimentalCoroutinesApi::class)` is needed for `resetReplayCache`, `SharedFlow.asFlow`, `UnconfinedTestDispatcher`, and the `TestScope` extensions `currentTime`/`runCurrent`/`advanceUntilIdle`/`advanceTimeBy`. If a lab wants to avoid opt-ins, `testScheduler.runCurrent()`, `testScheduler.advanceUntilIdle()` and `testScheduler.advanceTimeBy(Duration)` are stable (signatures table).
- **Unverified items, kept out of factual sentences:**
  - Kafka client threading and offset-commit advice (A9);
  - framework shutdown hooks (A7);
  - JDK HttpClient's internal flow control (B4);
  - Reactor's reference documentation (blocked);
  - MDC/ThreadLocal propagation in this context (B5).
  Re-check them before stating them as fact.
- **The internals (A8)** are a level-down explanation for videos. The field names (`slots`, `buffer`, `head`, `replayIndex`, `minCollectorIndex`) are private, and D6's reflection may break in any release. Do not build a lab on them.
- **Payments framing** that worked well in the demos:
  - the FX cache read through `.value` (the `Eagerly` vs `WhileSubscribed` trap);
  - a fraud and a ledger handler sharing one poller (late-subscriber loss, and the custom `SharingStarted` gate);
  - the gateway SDK (`take(2)` unregisters, `onError` fails the flow);
  - `PaymentTracker.authorizeAndCapture()` for the StateFlow test trap;
  - a `traceId` crossing the Reactor bridge.
