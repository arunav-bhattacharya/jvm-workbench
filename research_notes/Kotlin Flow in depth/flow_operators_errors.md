# Kotlin Flow in depth, lessons 5 and 6: flattening and combining; errors, completion, retries, timeouts and cancellation (kotlinx.coroutines 1.11.0, Kotlin 2.4.21)

Scope: lesson 5 (`flatMapConcat`, `flatMapMerge`, `flatMapLatest`, `flattenConcat`/`flattenMerge`, `merge`, `zip`, `combine`, `transformLatest`/`mapLatest`) and lesson 6 (exception transparency, `catch`, `onCompletion`, `retry`/`retryWhen`, `onEach` + `launchIn`, downstream exceptions, `CancellationException`, `timeout()`, `withTimeout`, `debounce`, `sample`, `onEmpty`, `first`/`single`/`firstOrNull`, `take` and `AbortFlowException`, a flaky-provider pattern) of the new track "Kotlin Flow in depth". The learner is a senior backend engineer (Kotlin and Java, payments, Kafka, Quarkus) who has done the coroutines track (co-07 Flow basics, co-08 StateFlow/SharedFlow, co-09 channels) and the Reactor track (rx-03 flatMap/concatMap/switchMap, rx-04 zip/merge/combineLatest, rx-05 errors/retries/timeouts). These notes go one level down: what the library actually builds, so the learner can predict variants.

**How the claims were checked.**
- **[Local]** means I compiled and ran it in this session. I used `kotlin-compiler-embeddable-2.4.21` from the Gradle cache (`org.jetbrains.kotlin.cli.jvm.K2JVMCompiler`, `-jvm-target 21`) on OpenJDK 21.0.12.1, with `kotlinx-coroutines-core-jvm-1.11.0` and `kotlinx-coroutines-test-jvm-1.11.0` on the classpath. The Reactor comparisons ran against `reactor-core-3.8.8` + `reactor-test-3.8.8` (`VirtualTimeScheduler`), also from the Gradle cache. Each program and its output is in "Demo ideas with expected outcomes". **All times are virtual time** (`runTest` + the `TestCoroutineScheduler` clock, or Reactor's `VirtualTimeScheduler`) unless a line says "real time". Virtual numbers are exact and repeat on every run.
- **[Source]** means I read it in the 1.11.0 source. The git tag is `1.11.0` (no `v`; `v1.11.0` returns 404). Files were fetched from `https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/...`. Paths below are relative to `kotlinx-coroutines-core/` unless they start with `kotlinx-coroutines-test/`.
- **[Docs]** means an official kotlinlang.org page, URL given and fetched in this session.
- **[Unverified]** means I did not check it. It is never stated as fact.

---

## Summary

1. **Stability in 1.11.0** [Source + Local compile]. `@ExperimentalCoroutinesApi`: `flatMapConcat`, `flatMapMerge`, `flatMapLatest`, `flattenConcat`, `flattenMerge`, `transformLatest`, `mapLatest` (and `chunked`). `@FlowPreview`: `DEFAULT_CONCURRENCY`, `DEFAULT_CONCURRENCY_PROPERTY_NAME`, `debounce`, `sample`, `timeout`. **Stable** (no annotation): `merge`, `zip`, `combine`, `combineTransform`, `catch`, `retry`, `retryWhen`, `onCompletion`, `onEmpty`, `onStart`, `onEach`, `launchIn`, `take`, `first`, `firstOrNull`, `single`, `singleOrNull`, `collectLatest`. Without an opt-in, the 2.4.21 compiler gives a **warning**, not an error ("this declaration needs opt-in"). The build fails only with warnings-as-errors.
2. **`flatMapConcat` creates no coroutine and no channel.** It is `map(transform).flattenConcat()`, and `flattenConcat` is `collect { emitAll(it) }`. The outer flow's code is paused inside `emit` while each inner flow runs. In the demo, an outer that "emits every 100 ms" emitted its second value at 300 ms, not 100 ms [Source + Local].
3. **`flatMapMerge(concurrency)` is a channel flow.** One producer coroutine collects the outer flow and calls `transform` **one value at a time**. A `Semaphore(concurrency)` caps the inner flows, each inner gets its own `launch`, and the results go through one `Channel.BUFFERED` (64) output channel. Output order is completion order [Source + Local]. If the slow call sits in the `transform` lambda instead of inside the returned flow, everything runs sequentially: 800 ms instead of 450 ms in the fee fan-out demo [Local].
4. **`DEFAULT_CONCURRENCY` is 16.** It is read once from the system property `kotlinx.coroutines.flow.defaultConcurrency`, which must be in 1..`Int.MAX_VALUE`. With `-D...=4`, at most 4 lookups were in flight. With `=0`, the first access threw `ExceptionInInitializerError` ← `IllegalStateException: System property 'kotlinx.coroutines.flow.defaultConcurrency' should be in range 1..2147483647, but is '0'` [Source + Local]. Reactor's `flatMap` default is 256 (observed 256 in flight) [Source + Local].
5. **`flatMapLatest`/`mapLatest` are thin wrappers over `transformLatest`.** For each new value, `transformLatest` cancels the previous block with `ChildCancelledException("Child of the scoped flow was cancelled")` and then **`join()`s it** before it launches the next one. A 50 ms `NonCancellable` cleanup in the old inner delayed the new inner's start by 50 ms [Source + Local].
6. **`zip` pairs by index and ends with the shorter flow.** The receiver flow is collected in the caller's coroutine with no buffer. Only `other` gets a `produce` coroutine (rendezvous channel). The longer side is cancelled: with `AbortFlowException` when `other` ends first, or `JobCancellationException` ("ProducerCoroutine was cancelled") when the receiver ends first [Source + Local].
7. **`combine` emits once every source has a value, and then on each update.** It starts one coroutine per source and uses a channel whose capacity equals the number of flows, with a `yield()` after each send. When the collector is slow, `combine` **both suspends the sources and drops intermediate values**: a source emitting 1..10 every 10 ms, with a collector that takes 100 ms per item, delivered `1, 3, 5, 7, 9, 10`. Reactor's `combineLatest` delivered all ten [Source + Local].
8. **Exception transparency.** After `emit` throws, the flow must not emit again. Breaking the rule throws `IllegalStateException: Flow exception transparency is violated: Previous 'emit' call has thrown exception …, but then emission attempt of value '…' has been detected. …` (exact text below) [Source + Local].
9. **`catch` only sees upstream exceptions.** It passes downstream exceptions through, and it also passes the cancellation of the collecting job. It **does** catch a `CancellationException` that the upstream throws while the job is still active, and that includes a `TimeoutCancellationException` from `timeout()` or from a `withTimeout` inside the upstream [Source + Local].
10. **`onCompletion`'s `cause`** is `null` on success. It is the exception on an upstream or a downstream failure. On cancel it is `JobCancellationException` ("StandaloneCoroutine was cancelled"), or the exception you passed to `cancel(...)`. Above `take`/`first` it is `AbortFlowException` ("Flow was aborted, no more elements needed"); below them it is `null` [Local].
11. **`retry(n)` means n retries (n + 1 collections).** `retryWhen`'s `attempt` starts at 0. A retry re-runs the upstream from the top, so values already emitted are **emitted again**. The streaming demo delivered `[payment-1, payment-2, payment-1, payment-2, payment-3]` [Source + Local].
12. **`timeout(d)` (`@FlowPreview` since 1.7.0)** throws `TimeoutCancellationException("Timed out waiting for 100ms")`. It times the gap between upstream values and does not count the time the downstream spends processing. It is a `CancellationException`, so if it escapes a `launch` the coroutine just ends as **cancelled**. No handler is called and the parent keeps running [Source + Local + Docs].
13. **Messages to quote.** `first()` on empty: `NoSuchElementException: Expected at least one element`. `single()`: `NoSuchElementException: Flow is empty` / `IllegalArgumentException: Flow has more than one element`. `withTimeout`: `Timed out waiting for 250 ms` in real time, but `Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time. …` under `runTest` [Local].
14. **Docs drift.** `https://kotlinlang.org/docs/flow.html` (cited by co-07 and rx-03) is now a redirect stub to `coroutines-flow.html`. That rewritten page (last modified 13 July 2026) still covers `catch`, `onEach`-before-`catch`, `retry`/`retryWhen` and `take`-style cancellation. It no longer has the flattening, `zip`/`combine`, `onCompletion` operator or `cancellable()` sections. Cite the API reference pages for those [Docs].

---

## Exact signatures and stability annotations (1.11.0)

All of these are in package `kotlinx.coroutines.flow`, in the multifile facade class `FlowKt` [Source]. The annotations were also confirmed by compiling a file with no `@OptIn` (output in Demo D0) [Local].

```kotlin
// operators/Merge.kt
@FlowPreview public const val DEFAULT_CONCURRENCY_PROPERTY_NAME: String = "kotlinx.coroutines.flow.defaultConcurrency"
@FlowPreview public val DEFAULT_CONCURRENCY: Int = systemProp(DEFAULT_CONCURRENCY_PROPERTY_NAME, 16, 1, Int.MAX_VALUE)

@ExperimentalCoroutinesApi
public fun <T, R> Flow<T>.flatMapConcat(transform: suspend (value: T) -> Flow<R>): Flow<R> = map(transform).flattenConcat()
@ExperimentalCoroutinesApi
public fun <T, R> Flow<T>.flatMapMerge(concurrency: Int = DEFAULT_CONCURRENCY, transform: suspend (value: T) -> Flow<R>): Flow<R> =
    map(transform).flattenMerge(concurrency)
@ExperimentalCoroutinesApi public fun <T> Flow<Flow<T>>.flattenConcat(): Flow<T>
@ExperimentalCoroutinesApi public fun <T> Flow<Flow<T>>.flattenMerge(concurrency: Int = DEFAULT_CONCURRENCY): Flow<T>
public fun <T> Iterable<Flow<T>>.merge(): Flow<T>                       // stable
public fun <T> merge(vararg flows: Flow<T>): Flow<T>                    // stable
@ExperimentalCoroutinesApi
public fun <T, R> Flow<T>.transformLatest(transform: suspend FlowCollector<R>.(value: T) -> Unit): Flow<R>
@ExperimentalCoroutinesApi
public inline fun <T, R> Flow<T>.flatMapLatest(crossinline transform: suspend (value: T) -> Flow<R>): Flow<R> =
    transformLatest { emitAll(transform(it)) }
@ExperimentalCoroutinesApi
public fun <T, R> Flow<T>.mapLatest(transform: suspend (value: T) -> R): Flow<R> = transformLatest { emit(transform(it)) }

// operators/Zip.kt (all stable)
@JvmName("flowCombine") public fun <T1, T2, R> Flow<T1>.combine(flow: Flow<T2>, transform: suspend (a: T1, b: T2) -> R): Flow<R>
public fun <T1, T2, R> combine(flow: Flow<T1>, flow2: Flow<T2>, transform: suspend (a: T1, b: T2) -> R): Flow<R>
// … typed overloads for 3, 4 and 5 flows, plus:
public inline fun <reified T, R> combine(vararg flows: Flow<T>, crossinline transform: suspend (Array<T>) -> R): Flow<R>
public inline fun <reified T, R> combine(flows: Iterable<Flow<T>>, crossinline transform: suspend (Array<T>) -> R): Flow<R>
public fun <T1, T2, R> Flow<T1>.combineTransform(flow: Flow<T2>, transform: suspend FlowCollector<R>.(a: T1, b: T2) -> Unit): Flow<R>
public fun <T1, T2, R> Flow<T1>.zip(other: Flow<T2>, transform: suspend (T1, T2) -> R): Flow<R>   // the only zip: two flows

// operators/Errors.kt (all stable)
public fun <T> Flow<T>.catch(action: suspend FlowCollector<T>.(cause: Throwable) -> Unit): Flow<T>
public fun <T> Flow<T>.retry(retries: Long = Long.MAX_VALUE, predicate: suspend (cause: Throwable) -> Boolean = { true }): Flow<T>
public fun <T> Flow<T>.retryWhen(predicate: suspend FlowCollector<T>.(cause: Throwable, attempt: Long) -> Boolean): Flow<T>

// operators/Emitters.kt (all stable)
public fun <T> Flow<T>.onCompletion(action: suspend FlowCollector<T>.(cause: Throwable?) -> Unit): Flow<T>
public fun <T> Flow<T>.onStart(action: suspend FlowCollector<T>.() -> Unit): Flow<T>
public fun <T> Flow<T>.onEmpty(action: suspend FlowCollector<T>.() -> Unit): Flow<T>
// operators/Transform.kt
public fun <T> Flow<T>.onEach(action: suspend (T) -> Unit): Flow<T>          // = transform { action(it); emit(it) }
// terminal/Collect.kt
public fun <T> Flow<T>.launchIn(scope: CoroutineScope): Job = scope.launch { collect() }
public suspend fun <T> Flow<T>.collectLatest(action: suspend (value: T) -> Unit)  // = mapLatest(action).buffer(0).collect()

// operators/Delay.kt
@FlowPreview public fun <T> Flow<T>.debounce(timeoutMillis: Long): Flow<T>
@FlowPreview @OverloadResolutionByLambdaReturnType public fun <T> Flow<T>.debounce(timeoutMillis: (T) -> Long): Flow<T>
@FlowPreview public fun <T> Flow<T>.debounce(timeout: Duration): Flow<T>
@FlowPreview @JvmName("debounceDuration") @OverloadResolutionByLambdaReturnType public fun <T> Flow<T>.debounce(timeout: (T) -> Duration): Flow<T>
@FlowPreview public fun <T> Flow<T>.sample(periodMillis: Long): Flow<T>
@FlowPreview public fun <T> Flow<T>.sample(period: Duration): Flow<T>
@FlowPreview public fun <T> Flow<T>.timeout(timeout: Duration): Flow<T>        // Duration only; no Long overload

// operators/Limit.kt and terminal/Reduce.kt (stable)
public fun <T> Flow<T>.take(count: Int): Flow<T>        // require(count > 0) { "Requested element count $count should be positive" }
public suspend fun <T> Flow<T>.first(): T
public suspend fun <T> Flow<T>.first(predicate: suspend (T) -> Boolean): T
public suspend fun <T> Flow<T>.firstOrNull(): T?
public suspend fun <T> Flow<T>.firstOrNull(predicate: suspend (T) -> Boolean): T?
public suspend fun <T> Flow<T>.single(): T
public suspend fun <T> Flow<T>.singleOrNull(): T?

// kotlinx.coroutines (Timeout.kt), stable
public suspend fun <T> withTimeout(timeMillis: Long, block: suspend CoroutineScope.() -> T): T
public suspend fun <T> withTimeout(timeout: Duration, block: suspend CoroutineScope.() -> T): T
public suspend fun <T> withTimeoutOrNull(timeMillis: Long, block: suspend CoroutineScope.() -> T): T?
public class TimeoutCancellationException internal constructor(message: String, /* @JvmField @Transient */ internal val coroutine: Job?) :
    CancellationException(message), CopyableThrowable<TimeoutCancellationException>     // constructor is internal
```

Notes on the annotations:
- The compiler wording differs for the two markers [Local]. `@ExperimentalCoroutinesApi` gives "this declaration needs opt-in. Its usage should be marked with '@kotlinx.coroutines.ExperimentalCoroutinesApi' or '@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)'". `@FlowPreview` gives "this declaration is in a preview state and can be changed in a backwards-incompatible manner with a best-effort migration. Its usage should be marked with '@kotlinx.coroutines.FlowPreview' …". Both are warnings.
- `TimeoutCancellationException` has only internal constructors, so application code cannot throw one itself. To simulate a timeout in a test, use a real `timeout()`/`withTimeout` under virtual time [Source: `common/src/Timeout.kt`].
- Test helpers [Local, compile warnings]: `TestScope.currentTime`, `testScheduler.currentTime`, `advanceTimeBy`, `runCurrent`, `advanceUntilIdle` and `UnconfinedTestDispatcher` need `@OptIn(ExperimentalCoroutinesApi::class)` in kotlinx-coroutines-test 1.11.0. `runTest`, `backgroundScope` and `StandardTestDispatcher` compiled with no warning.
- The 1.11.0 changelog lists **no behaviour changes** to any operator in this scope. Its Flow items are `SharedFlow.asFlow`, the `StateFlow.collectLatest` overload, the `StateFlow.onSubscription` overload, terminal operators that collect into a `Map`, and a `flowOn` fix for `ThreadContextElement` [Source: `CHANGES.md` at tag 1.11.0]. `Flow.timeout` was "Added … as `@FlowPreview` (#2624)" in **1.7.0**. In **1.8.1**, "`Flow.timeout` throws the exception with which the channel was closed (#4071)". `chunked` arrived in 1.9.0 [Source: `CHANGES.md`].

---

## Lesson 5: flattening and combining

### 5.1 How each operator is built (what you would see in a debugger)

| Operator | Implementation [Source] | Coroutines started per collection | Channel(s) | Observed [Local, Demo D3 with `-Dkotlinx.coroutines.debug`] |
|---|---|---|---|---|
| `flatMapConcat(f)` / `flattenConcat()` | `map(f).flattenConcat()`; `flattenConcat = unsafeFlow { collect { value -> emitAll(value) } }` (`flow/operators/Merge.kt`) | none | none | outer, inner and collector all ran in the test coroutine (`runner#4`) |
| `flatMapMerge(c, f)` / `flattenMerge(c)` | `map(f).flattenMerge(c)`. For `c == 1` that is `flattenConcat()`; otherwise `ChannelFlowMerge(flow, c)`: `produce` → `flow.collect { inner -> job?.ensureActive(); semaphore.acquire(); scope.launch { try { inner.collect(collector) } finally { semaphore.release() } } }` (`flow/internal/Merge.kt`) | 1 producer (collects the outer and runs `f`) plus 1 `launch` per inner flow, at most `c` alive | one output channel, `Channel.BUFFERED` (64), `BufferOverflow.SUSPEND` | outer in `coroutine#7 (ProducerCoroutine)`, inners in `#8`, `#9 (StandaloneCoroutine)`, collector in the caller (`ScopeCoroutine`) |
| `transformLatest(f)` | `ChannelFlowTransformLatest`: `coroutineScope { flow.collect { v -> previous?.apply { cancel(ChildCancelledException()); join() }; previous = launch(start = UNDISPATCHED) { collector.transform(v) } } }` | 1 producer plus 1 `launch` per upstream value (one alive at a time) | output `Channel.BUFFERED` | outer in `#12`, the blocks in `#13`, `#14` |
| `flatMapLatest(f)` | `transformLatest { emitAll(f(it)) }` (inline) | as above | as above | as above |
| `mapLatest(f)` | `transformLatest { emit(f(it)) }` | as above | as above | — |
| `collectLatest(a)` | `mapLatest(a).buffer(0).collect()` (`flow/terminal/Collect.kt`) | as above | rendezvous (buffer 0) | — |
| `merge(a, b, …)` | `ChannelLimitedFlowMerge`: `flows.forEach { scope.launch { it.collect(collector) } }` | 1 producer plus 1 `launch` per source flow | output `Channel.BUFFERED` | sources in `#18`, `#19`; collector in the caller |
| `a.zip(b)` | `zipImpl`: `coroutineScope { val second = produce { b.collect { send(it ?: NULL) } }; withContextUndispatched(ctx + collectJob) { a.collect { v -> … second.receiveCatching() … emit(transform(v, other)) } } }` (`flow/internal/Combine.kt`) | 1 (`produce` for `b`); `a` runs in the caller under a child `Job` (`collectJob`) | one **rendezvous** channel for `b` | `a` in the caller (context `JobImpl`), `b` in `#22 (ProducerCoroutine)` |
| `combine(a, b, …)` | `combineInternal` inside `flowScope`: one `launch` per source doing `resultChannel.send(Update(i, value)); yield()`, then a batching receive loop (`flow/internal/Combine.kt`) | 1 per source flow | `Channel<Update>(size)`: **capacity = number of flows** | sources in `#25`, `#26`; transform and collector in the caller (`FlowCoroutine`) |
| `buffer()` | `ChannelFlowOperatorImpl` with `produce` | 1 producer | `BUFFERED` | upstream in `#29 (ProducerCoroutine)` |
| `debounce(t)` | `scopedFlow { val values = produce { collect { send(it ?: NULL) } } … select { onTimeout; values.onReceiveCatching } }` (`flow/operators/Delay.kt`) | 1 producer | rendezvous | upstream in `#32 (ProducerCoroutine)` |
| `sample(p)` | `scopedFlow`, `produce(capacity = Channel.CONFLATED)` for values, plus `fixedPeriodTicker` (`produce(capacity = 0)`) | 2 (values and ticker) | conflated + rendezvous | — (source only) |
| `timeout(d)` | `scopedFlow { val values = buffer(Channel.RENDEZVOUS).produceIn(this); whileSelect { values.onReceiveCatching { … }; onTimeout(d) { throw TimeoutCancellationException("Timed out waiting for $d") } } }` | 1 producer | rendezvous | upstream in `#35 (ProducerCoroutine)` |

What follows from the table:
- `ChannelFlowMerge.toString()` prints `ChannelFlowMerge[concurrency=2, capacity=-2]`. `-2` is `Channel.BUFFERED`. With `.buffer(0)` after it, the operators fuse into one channel flow: `ChannelFlowMerge[concurrency=4, capacity=0]`. `flatMapMerge(1)` returns the plain `flattenConcat` flow, `kotlinx.coroutines.flow.FlowKt__MergeKt$flattenConcat$$inlined$unsafeFlow$1@…` [Local, Demo D2].
- `Channel.BUFFERED` means 64 when the overflow strategy is `SUSPEND`. You can change it JVM-wide with `kotlinx.coroutines.channels.defaultBuffer` (`@DelicateCoroutinesApi`, "highly discouraged … last-ditch effort") [Source: `common/src/channels/Channel.kt`].
- How far does `flatMapMerge` run ahead of a slow collector? The test had 500 one-item inners and a collector that suspended on its first item. **82 upstream items** had been pulled by then. My decomposition (inference, not measured): 64 buffer + about 16 suspended inners + about 2 in hand. With `.buffer(0)` it was **18**. With `flatMapConcat` it was **1** [Local, Demo D10]. Budget memory for this: up to 64 finished results plus `concurrency` inners can be in flight.
- `combine` and the `latest` operators run their sources in child coroutines of a scope (`flowScope`/`scopedFlow`). Its `FlowCoroutine.childCancelled` cancels the whole scope when **any** child is cancelled, unless the cause is a `ChildCancelledException`. So a source that ends with a bare `CancellationException` cancels the whole `combine` [Source: `flow/internal/FlowCoroutine.kt`]. I did not run that case [Unverified as behaviour].

### 5.2 `flatMapConcat` vs `flatMapMerge` vs `flatMapLatest`: one timeline

Setup (Demo D1): the outer emits 1, then `delay(100)`, emits 2, then `delay(100)`, emits 3. `inner(n)` waits 50 ms, emits `n-a`, waits 150 ms, emits `n-b`. Virtual ms [Local]:

| t (ms) | `flatMapConcat` | `flatMapMerge` (default 16) | `flatMapLatest` |
|---|---|---|---|
| 0 | outer 1 | outer 1 | outer 1 |
| 50 | 1-a | 1-a | 1-a |
| 100 | | outer 2 | outer 2; **inner 1 cancelled** (`ChildCancelledException: Child of the scoped flow was cancelled`) |
| 150 | | 2-a | 2-a |
| 200 | 1-b | outer 3; 1-b | outer 3; **inner 2 cancelled** |
| 250 | | 3-a | 3-a |
| 300 | **outer 2** (the outer was paused inside `emit`) | 2-b | |
| 350 | 2-a | | |
| 400 | | 3-b; done | 3-b; done |
| 500 | 2-b | | |
| 600 | outer 3 | | |
| 650 | 3-a | | |
| 800 | 3-b; done | | |

- `flatMapConcat` takes **800 ms**. The outer's own `delay(100)` only starts after `emit(1)` returns, and that happens only after inner 1 has finished. Add `.buffer()` before `flatMapConcat` and the outer runs ahead in its own coroutine: outer 2 at 100 ms, outer 3 at 200 ms, inners back to back, done at **600 ms** [Local, Demo D5].
- `flatMapMerge` interleaves by completion time. `1-b` (200) comes after `2-a` (150).
- `flatMapLatest`: `1-b` and `2-b` are never emitted. The cancelled inner's `onCompletion` sees `ChildCancelledException` with the message `Child of the scoped flow was cancelled` [Local + Source: `jvm/src/flow/internal/FlowExceptions.kt`].
- The same three shapes in Reactor 3.8.8 (`concatMap`/`flatMap`/`switchMap`, same delays, `VirtualTimeScheduler`). `flatMap` and `switchMap` gave the **identical** timeline. `concatMap` finished at **600 ms** (2-a at 250, 3-b at 600), not 800 [Local, Demo D11]. The reason is the source: Reactor's `concatMap(mapper)` is `FluxConcatMapNoPrefetch` and requests 1 at a time (`outer request(1)` logged at 0, 200 and 400 ms), but the `Mono.delay` timers in the source ran while no request was outstanding. A Flow `flow { }` body cannot do that: it is suspended in `emit`. To get the Reactor timeline in Flow, put `buffer()` in front [Source: `reactor-core` 3.8.8 `Flux.java` + Local].

### 5.3 `flatMapMerge` in detail: concurrency, ordering, and where the work must live

Fee fan-out (Demo D2). Five merchants with lookup latencies m1=300, m2=100, m3=200, m4=50, m5=150 ms; `flatMapMerge(concurrency = 2) { m -> flow { emit(feeLookup(m)) } }` [Local]:
```
    0 ms    transform called for m1
    0 ms    transform called for m2
    0 ms    transform called for m3        <- transform runs one value ahead of the permits
    0 ms      start lookup m1 (in flight: 1)
    0 ms      start lookup m2 (in flight: 2)
  100 ms  collector got m2:fee
  100 ms    transform called for m4
  100 ms      start lookup m3 (in flight: 2)
  300 ms  collector got m1:fee
  300 ms  collector got m3:fee
  300 ms    transform called for m5
  300 ms      start lookup m4 (in flight: 1)
  300 ms      start lookup m5 (in flight: 2)
  350 ms  collector got m4:fee
  450 ms  collector got m5:fee
  450 ms  done, max in flight = 2
```
- **Order is completion order** (m2, m1, m3, m4, m5), not input order [Local]. The docs say "Merges the given flows into a single flow without preserving an order of elements" (`merge`) [Docs: merge.html].
- **`transform` is called sequentially, in the producer coroutine, before the permit is taken.** The KDoc says so: "This operator calls `transform` *sequentially* and then merges the resulting flows with a `concurrency` limit" [Source + Docs: flat-map-merge.html]. In the source, `map(transform)` runs upstream of `semaphore.acquire()`. That is why `transform` for m3 ran at 0 ms while m3's lookup waited until 100 ms [Local].
- **The gotcha.** `flatMapMerge(2) { m -> val fee = feeLookup(m); flowOf(fee) }` runs every lookup **inside the transform**, one at a time: max in flight 1, **800 ms** total, the same as plain `map { feeLookup(it) }` [Local]. The suspend call has to be inside the returned flow (`flow { emit(feeLookup(m)) }`).
- The KDoc itself discourages these operators for everyday code: "we discourage its usage in a regular application-specific flows. Most likely, suspending operation in `map` operator will be sufficient and linear transformations are much easier to reason about." [Source + Docs: flat-map-merge.html, flat-map-concat.html].
- **Default concurrency.** 40 lookups of 100 ms with no `concurrency` argument: max in flight **16**, done at **300 ms** (3 waves). With `-Dkotlinx.coroutines.flow.defaultConcurrency=4`: max **4**, done at **1000 ms** [Local, Demo D2]. The property is read when the class `FlowKt__MergeKt` is initialised. The invalid-value case proves it: `java.lang.ExceptionInInitializerError at kotlinx.coroutines.flow.FlowKt.getDEFAULT_CONCURRENCY(Unknown Source)`, caused by `IllegalStateException: System property 'kotlinx.coroutines.flow.defaultConcurrency' should be in range 1..2147483647, but is '0'` [Local]. So a `System.setProperty` call after the first use does nothing (inference from the static initialiser; not run separately).
- `flatMapMerge(0) { … }` throws at build time: `IllegalArgumentException: Expected positive concurrency level, but had 0` [Local + Source].
- **One inner fails, all fail** (Demo X3). When m2's lookup threw `IOException` at 100 ms, m1 and m3 ended with `JobCancellationException`, and the caller saw `java.io.IOException: fee service 503 for m2` [Local]. To keep going when one lookup fails, put `catch` **inside** each inner: `flow { emit(lookup(m)) }.catch { emit(default(m)) }`. Output: `m2:DEFAULT` at 200 ms, `m3:fee` at 300, `m1:fee` at 400 [Local]. That is Flow's answer to Reactor's `onErrorContinue`.
- **Fusion.** "Applications of `flowOn`, `buffer`, and `produceIn` _after_ this operator are fused with its concurrent merging so that only one properly configured channel is used" [Source + Docs]. Shown by the `toString` above [Local].
- **No `flatMapSequential` in Flow** (concurrent calls, results in input order). The "Exercise ideas" section has an order-preserving `map { async { } }.buffer(n - 2)` pattern, verified for n = 2, 3, 4 and 8 [Local].

### 5.4 `flatMapLatest`, `transformLatest`, `mapLatest`, `collectLatest`

- The KDoc examples reproduce exactly [Local, Demo D5]. For `flow { emit("a"); delay(100); emit("b") }`: `transformLatest { v -> emit(v); delay(200); emit(v + "_last") }` gives `[a, b, b_last]`, the `flatMapLatest` version gives `[a, b, b_last]`, and `mapLatest { v -> println("Started computing $v"); delay(200); "Computed $v" }` prints both "Started computing" lines and gives `[Computed b]` [Docs: flat-map-latest.html, map-latest.html].
- **Cancel, then join, then start.** The previous block is cancelled with `ChildCancelledException` and then `join()`ed before the next block is launched [Source: `flow/internal/Merge.kt`]. Demo D5: inner A has a 50 ms `withContext(NonCancellable)` cleanup in `finally`. B arrives at 100 ms, but "inner A cleanup done" is logged at 150 ms and "inner B starts" also at 150 ms [Local]. So with `flatMapLatest` the old request's cleanup always finishes before the new one starts. The upstream is also held up during that `join()`. Lesson angle: keep cleanup in a cancelled inner short.
- The new block starts with `CoroutineStart.UNDISPATCHED` ("Do not pay for dispatch here") [Source].
- All three are "buffered by default and size of its output buffer can be changed by applying subsequent `buffer` operator" [Source + Docs].
- Search-as-you-type with `flatMapLatest` and no debounce (Demo T4). Each keystroke cancels the previous search (`search 'a' cancelled` at 80 ms, and so on), and only the searches that lasted their full 150 ms are shown: `acme` at 390 ms, `acme p` at 910 ms, `acme pay` at 1450 ms [Local].

### 5.5 `flattenConcat` / `flattenMerge`

- They work on a `Flow<Flow<T>>`, and `flatMap*` is `map(transform).flatten*()` [Source].
- Demo D5: `flowOf(x = (30 ms: x1, +30: x2), y = (10 ms: y1, +30: y2))`. `flattenConcat()` gives `[x1, x2, y1, y2]` in 100 ms. `flattenMerge()` gives `[y1, x1, y2, x2]` in 60 ms (the log line shows cumulative 160 ms) [Local].
- "With `concurrency == 1` this operator is identical to `flattenConcat`" [Source + Docs: flatten-merge.html]. It literally returns `flattenConcat()` [Source].

### 5.6 `merge`

- Stable. "All flows are merged concurrently, without limit on the number of simultaneously collected flows." Order is not preserved [Source + Docs: merge.html].
- Demo D5: card events every 100 ms and bank events every 70 ms, 3 each. Output `bank-0@70, card-0@100, bank-1@140, card-1@200, bank-2@210, card-2@300`; the merged flow completes at 300 ms, when the **last** source completes [Local].
- An error in one source cancels the others. Bank threw at 150 ms, card's `onCompletion` saw `JobCancellationException: Parent job is Cancelling`, and the caller got `IllegalStateException: bank feed down` [Local].

### 5.7 `zip`: pairs by index, paced by the slower, ends with the shorter

- KDoc: "The resulting flow completes as soon as one of the flows completes and cancel is called on the remaining flow." On buffering: "The upstream flow is collected sequentially in the same coroutine without any buffering, while the [other] flow is collected concurrently as if `buffer(0)` is used." [Source + Docs: zip.html].
- Docs example, run on its own (Demo C4): `flowOf(1,2,3).onEach{delay(10)}.zip(flowOf("a","b","c","d").onEach{delay(15)})` gives `1a@15, 2b@30, 3c@45` [Local].
- **FX × price with `zip`** (Demo D4). Prices are 1000, 1010, … every 100 ms; the FX rate is 0.92 at 250 ms and 0.95 at 550 ms. Output: `1000@0.92` at 250 and `1010@0.95` at 550, then done [Local]. Two points to teach:
  - The receiver (`prices`) is **slowed down**. Its second price is emitted at 350 ms, not 200, because `zip` collects the receiver in the caller with no buffer, so `emit` waits for the FX value [Local].
  - When FX (the `other`) completed at 550 ms, the price flow's `onCompletion` saw `kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed` [Local].
- When the receiver is the shorter one (Demo X4), the infinite `other` ended with `JobCancellationException: ProducerCoroutine was cancelled` [Local].
- `zip` pairs values by index, so with a price stream and a rate stream it pairs the n-th price with the n-th rate. For "price in EUR at the latest rate" that is the wrong tool. Use `combine`.
- Flow has only the **binary** `zip` (`Flow<T1>.zip(other)`). There is no `zip(a, b, c)` [Source: `flow/operators/Zip.kt`].

### 5.8 `combine`: latest of each

- KDoc: "combining the most recently emitted values by each flow." Docs example `flowOf(1, 2).onEach { delay(10) }` combined with `flowOf("a","b","c").onEach { delay(15) }` → "1a 2a 2b 2c" [Source + Docs: combine.html]. Reproduced as `1a@15, 2a@20, 2b@30, 2c@45` [Local, Demo D4].
- **When does it first emit?** Only when every source has emitted at least once. With prices every 100 ms and the first FX rate at 250 ms, the first output was `1010@0.92` at **250 ms**. Price 1000 (100 ms) was overwritten by 1010 (200 ms) and never combined. After that there is one output per update: `1020@0.92@300 … 1040@0.92@500, 1040@0.95@550, 1050@0.95@600` [Local].
- **A source that never emits:** `combine(prices(), emptyFlow())` emitted nothing and **completed** when prices completed (600 ms) [Local]. In the source, nothing is transformed until `remainingAbsentValues == 0`, and the loop ends when every source has closed [Source].
- **Slow collector** (Demo C1). Fast source 1..10 every 10 ms, `flowOf("cfg")`, collector `delay(100)` per item [Local]:
  ```
   10 ms    fast emits 1
   10 ms  -> 1/cfg (collector busy 100 ms)
   20 ms    fast emits 2
   30 ms    fast emits 3
   40 ms    fast emits 4        <- 4 is now suspended in send(): the channel (capacity 2) is full
  110 ms  -> 3/cfg              <- 2 and 3 were in one batch; 2 was overwritten
  120 ms    fast emits 5
  130 ms    fast emits 6
  210 ms  -> 5/cfg
  …
  410 ms  -> 9/cfg
  510 ms  -> 10/cfg
  610 ms  done
  ```
  So **yes, it drops intermediate values, and it also backpressures the sources**. The fast source took about 330 ms to emit 10 values instead of 100 ms. It is not pure conflation either: pure "latest only" would deliver 1 then 10. The mechanism is the batch-receive loop. It reads updates until it sees a second update from the same source in the same "epoch", overwriting that source's slot each time, and calls `transform` once per batch. The channel holds only `size` updates [Source: `flow/internal/Combine.kt`].
- With the same collector and no slowdown, all ten values come through (`1/cfg` … `10/cfg` at 10 … 100 ms) [Local].
- Make the choice explicit. `combine(...).conflate()` gives `1/cfg@10, 10/cfg@110`: only the newest survives. `combine(...).buffer(Channel.UNLIMITED)` keeps all 10 (the last at 1010 ms) [Local, Demo C2/C3].
- **Synchronous sources** (no delays): `combine(flowOf("a0","a1","a2"), flowOf("b0","b1","b2"))` gives `a0b0, a1b1, a2b2` [Local]. That is because of the `yield()` after each send ("Emulate fairness"). Reactor's `combineLatest` on two `Flux.just` gives `a2b0, a2b1, a2b2` [Local]. Teach the learner not to rely on either result: with synchronous sources, the combinations you get depend on scheduling.
- One source fails (Demo X5): the FX flow threw at 250 ms, the price flow ended with `JobCancellationException: Parent job is Cancelling`, and the caller saw `java.io.IOException: fx feed lost` [Local].

### 5.9 Reactor equivalents and where semantics differ

| Reactor 3.8.8 | Flow 1.11.0 | Same | Different (verified) |
|---|---|---|---|
| `concatMap(f)` | `flatMapConcat(f)`, or just `map { suspendCall(it) }` for 1:1 | output order, one inner at a time | Reactor's `concatMap(mapper)` is `FluxConcatMapNoPrefetch` and requests 1 at a time [Source: `Flux.java` + Local]. In Flow, the outer's **code** is paused inside `emit`, so a timed source runs slower (800 vs 600 ms in D1/D11). Add `buffer()` in front to decouple [Local] |
| `flatMap(f)` (concurrency `Queues.SMALL_BUFFER_SIZE` = 256, property `reactor.bufferSize.small`; prefetch `XS_BUFFER_SIZE` = 32) | `flatMapMerge(concurrency = 16)` (`DEFAULT_CONCURRENCY`, property `kotlinx.coroutines.flow.defaultConcurrency`) | interleaving by completion | default limit 256 vs 16 [Source: `Queues.java`, `Merge.kt` + Local: 256 and 16 in flight]. Flow's output is one 64-slot channel; the upstream runs in its own producer coroutine [Source] |
| `switchMap(f)` (`FluxSwitchMapNoPrefetch`) | `flatMapLatest(f)`, `mapLatest`, `transformLatest`, `collectLatest` | identical D1 timeline [Local] | Flow `join()`s the cancelled inner (including suspending cleanup) before starting the next [Source + Local]. Reactor sends a cancel signal and has no suspending cleanup to wait for [Unverified: Reactor-side timing not measured] |
| `flatMapSequential` | none built in; see the `mapConcurrentOrdered` exercise | — | [Local for the Flow pattern] |
| `Flux.merge(a, b)` | `merge(a, b)` (stable) | interleaves; completes when all complete; an error cancels the others [Local for Flow] | Reactor side not re-run here; rx-04 covers it |
| `Flux.zip`, `zipWith` | `a.zip(b) { … }` (binary only) | pairs by index, ends with the shorter, cancels the other [Docs + Local] | Flow's receiver side has no buffer, so it is paced by the slower side [Source + Local] |
| `Flux.combineLatest` | `combine`, `combineTransform` (2–5 typed, vararg, Iterable) | waits for every source; latest of each | **slow subscriber:** Reactor delivered all 10 combinations (110 … 1010 ms); Flow skipped 2, 4, 6, 8 [Local]. Synchronous sources: Reactor `a2b0, a2b1, a2b2`, Flow `a0b0, a1b1, a2b2` [Local] |
| `onErrorContinue` | no equivalent; `catch` inside each inner flow | — | [Local: X3] |

### 5.10 Payments examples verified in this session
- Fee lookups fanned out with a cap (D2), with per-merchant fallback (X3) [Local].
- Merchant search-as-you-type (T3, T4) [Local].
- FX rate × price stream with `combine` vs `zip` (D4) [Local].
- Card + bank event merge (D5) [Local].

---

## Lesson 6: errors, completion, retries, timeouts and cancellation

### 6.1 Exception transparency: what it is, and the exact message when violated

- The definition in the `Flow` KDoc: "When `emit` or `emitAll` throws, the Flow implementations must immediately stop emitting new values and finish with an exception. … If there is a need to emit values after the downstream failed, please use the `catch` operator." [Source: `flow/Flow.kt`, section "Exception transparency"].
- The rewritten docs page says: "When you catch an exception thrown by the collector inside a flow builder function, rethrow it. This preserves exception transparency and lets the caller of `collect()` handle the exception." [Docs: coroutines-flow.html].
- **How it is enforced** [Source: `jvm/src/flow/internal/SafeCollector.kt`]. The `SafeCollector` (used by `flow { }`, `transform`, `catch` actions and so on) records a `DownstreamExceptionContext` when the downstream `emit` throws. The next `emit` compares contexts, finds it, and calls `error(...)`.
- **The exact message** [Local, Demo E1: a `try { emit(1) } catch (e: Exception) { emit(-1) }` builder whose collector throws `IllegalStateException("ledger write failed")`]:
  ```
  java.lang.IllegalStateException: Flow exception transparency is violated:
      Previous 'emit' call has thrown exception java.lang.IllegalStateException: ledger write failed, but then emission attempt of value '-1' has been detected.
      Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
      For a more detailed explanation, please refer to Flow documentation.
  ```
  The builder's `catch` block did run first: it printed `builder caught: java.lang.IllegalStateException: ledger write failed`. The violation is the **second `emit`**, not the catching [Local].
- The same check fires on `take`'s abort. A builder that swallows `AbortFlowException` and emits again gets the same `IllegalStateException`, now naming `kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed` and value `'2'` [Local, Demo E4].
- The sibling invariant, **context preservation**, has its own messages [Source: `common/src/flow/internal/SafeCollector.common.kt`]. Emitting from another coroutine gives `"Flow invariant is violated:\n\t\tEmission from another coroutine is detected.\n\t\tChild of $emissionParentJob, expected child of $collectJob.\n\t\tFlowCollector is not thread-safe and concurrent emissions are prohibited.\n\t\tTo mitigate this restriction please use 'channelFlow' builder instead of 'flow'"`. Emitting from another context (`withContext`) gives `"Flow invariant is violated:\n\t\tFlow was collected in $collectContext,\n\t\tbut emission happened in $currentContext.\n\t\tPlease refer to 'flow' documentation or use 'flowOn' instead"`. co-07 covered the `flowOn` side, and I did not re-run these here.

### 6.2 `catch`: upstream only, where to place it, and `CancellationException`

- KDoc: "This operator is *transparent* to exceptions that occur in downstream flow and does not catch exceptions that are thrown to cancel the flow." It is "similar to wrapping the code of upstream flows with `try { ... } catch (e: Throwable) { action(e) }`" [Source: `flow/operators/Errors.kt`].
- The kotlinlang page for `catch` has newer KDoc text than the 1.11.0 tag ("If the upstream flow completes with an exception, this operator catches that exception and calls the specified action with it. … After the flow has completed with an exception, it cannot emit any more values …"). The header still says 1.11.0 [Docs: catch.html]. The rule is the same in both. The 1.11.0 changelog mentions "complete rewrites of … error handling-related KDoc (#4433, #4596)", so the doc site may have been regenerated from later KDoc [Source: `CHANGES.md`] [Unverified: which revision the site was built from].
- **How it decides** [Source: `catchImpl`, `Errors.kt`]. It wraps the downstream `emit` in a try/catch and remembers any exception thrown there (`fromDownstream`). When the upstream `collect` throws `e`:
  1. If `e` is the downstream exception, or `e` is the cancellation cause of the **current job** (the job is cancelled and `e` equals `job.getCancellationException()`), it rethrows.
  2. If there was no downstream exception, `e` goes to your action.
  3. If both failed, it rethrows: the upstream `e` wins and gets the downstream exception as suppressed. If `e` is a `CancellationException`, the downstream exception wins instead and gets `e` as suppressed.
- **Placement** [Local, Demos E2, X6]:
  - `flowOf(1,2,3).map { if (it == 2) throw IllegalArgumentException("bad amount $it") … }.catch { emit(-1) }` gives `1, -1`. The 3 is never produced, because a caught error still ends the upstream.
  - `catch` **before** `map` does not see a `map` failure: the caller gets `IOException: map failed`. `catch` **after** `map` gives `[1, -1]`.
  - A failure inside `collect { }` goes straight past `catch` to the caller (`caller saw java.lang.IllegalStateException: save failed for 2`).
  - The fix is to move the work into `onEach` above `catch` and call `collect()` with no lambda: `saving 1, saving 2, catch saw … save failed for 2` [Local]. The docs teach exactly this: "place that code in `.onEach()` before `.catch()`" [Docs: coroutines-flow.html].
- **`catch` and `CancellationException`** [Local, Demo E5]:
  - `flow { emit(1); throw CancellationException("upstream gave up") }.catch { emit(-1) }` gives **`[1, -1]`**. `catch` *does* handle a `CancellationException` the upstream throws while the collecting job is active. Note the class: `java.util.concurrent.CancellationException`, because `kotlinx.coroutines.CancellationException` is a typealias on the JVM.
  - `flow { emit(1); withTimeout(50) { delay(100) } }.catch { emit(-2) }` gives **`[1, -2]`**. `catch` sees the `TimeoutCancellationException` (here with the virtual-time message, see 6.8).
  - **Real cancellation passes through.** Cancelling the collecting job skipped the `catch` action, and `onCompletion` below it reported `JobCancellationException: StandaloneCoroutine was cancelled`.
  - Lesson phrasing: "`catch` ignores cancellation **of the collector's job**, not every `CancellationException`." So a broad `catch { emit(fallback) }` will also turn timeouts into fallbacks, which is usually what you want for a provider call. If you don't want that, rethrow `CancellationException` in the action.
- **`catch` vs. try/catch around `collect`.** Only the latter sees collector exceptions. co-07 already says this. The new detail here is the suppression rule (6.3).

### 6.3 What happens to a downstream exception inside `collect`

[Local, Demos E2, E3, E4, X1]
- It propagates out of `collect` to the caller unchanged: `caller saw java.lang.IllegalStateException: save failed for 2`.
- The upstream sees it **at its `emit` call**: `emit` rethrows the collector's exception into the builder. That is why a `try/catch` around `emit` can see it, and why it must rethrow (6.1). The upstream's `finally` runs.
- `catch` does not run its action. `onCompletion` does, with `cause` = that exception (`downstream failure: cause=java.lang.IllegalStateException: collector failed`).
- **Both fail** (Demo X1). The collector threw `IllegalStateException("collector failed")`, then the builder's `finally` threw `IOException("close() failed")`. The caller saw **`java.io.IOException: close() failed; suppressed=[java.lang.IllegalStateException: collector failed]`**, and the `catch` action did **not** run [Local]. The KDoc: "the downstream exception becomes superseded and suppressed by the upstream exception, being a semantic equivalent of throwing from `finally` block. However, this doesn't affect the operation of the exception-handling operators, which consider the downstream exception to be the root cause" [Source: `Flow.kt`].
- **A failed fallback does not keep the primary error.** `flow { throw IOException("primary down") }.catch { emitAll(flow { throw IOException("fallback down") }) }` → the caller saw `IOException: fallback down` with `suppressed=[]` and `cause=null` [Local, Demo X2]. If you want both in the logs, attach the primary error yourself (for example `addSuppressed`).

### 6.4 `onCompletion`: the `cause` parameter in every ending

[Local, Demos E3, W1, W2; Source: `Emitters.kt`]

| How the flow ended | `cause` observed |
|---|---|
| completed normally | `null` |
| upstream threw `IOException("provider reset")` | `java.io.IOException: provider reset` |
| the collector threw | `java.lang.IllegalStateException: collector failed` (it sees downstream failures too) |
| a later `map` threw and a `catch` further down swallowed it | `java.lang.IllegalStateException: map failed` (onCompletion sits above the failing operator, so it sees the failure even though the caller does not) |
| the collecting job was cancelled with `job.cancel()` | `kotlinx.coroutines.JobCancellationException: StandaloneCoroutine was cancelled` |
| `job.cancel("user closed the page")` | `java.util.concurrent.CancellationException: user closed the page` |
| placed **above** `take(1)` or `first()` | `kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed` |
| placed **below** `take(1)` | `null` (from the downstream's point of view the flow completed normally) |
| `withTimeout(250) { flow.onCompletion{}.collect() }` (real time) | `kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms` |
| above or below `.timeout(250.milliseconds)` | `kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250ms` (both sides) |

- So the answer to "CancellationException on cancel?" is yes. The class you see is the job's cancellation exception (`JobCancellationException` by default). Early termination by `take`/`first` also shows up as a `CancellationException` (`AbortFlowException`) to anything upstream. If your metrics hook treats every non-null cause as an "error", an `onCompletion` placed above `first()` will count every successful lookup as a failure. Check `cause is CancellationException` first.
- **Emitting from `onCompletion`.** On success it works: `flowOf("a","b").onCompletion { if (it == null) emit("Done") }` gives `a, b, Done`. After a failure, `emit` throws the original cause; the source uses a `ThrowingCollector(e)` [Local + Source]. KDoc: "In case of failure or cancellation, any attempt to emit additional elements throws the corresponding exception. Use `catch` if you need to suppress failure" [Source + Docs: on-completion.html].
- The KDoc says "Exception is empty if and only if the flow had fully completed successfully." [Source + Docs]. That is true from the operator's own position, as the `take` rows show.

### 6.5 `retry` and `retryWhen`

- Source [Errors.kt]: `retry(retries, predicate)` is `retryWhen { cause, attempt -> attempt < retries && predicate(cause) }`, with `require(retries > 0) { "Expected positive amount of retries, but had $retries" }`. `retryWhen` loops `catchImpl(this)`. When the predicate returns true it does `attempt++` and collects the upstream again; otherwise it rethrows the cause.
- **Counting** [Local, Demo E6]. `retry(2)` on a flow that always fails ran **3** attempts, and then the last `IOException("reset #3")` came out. `retry(0)` throws `IllegalArgumentException: Expected positive amount of retries, but had 0` when the flow is built. The default `retries` is `Long.MAX_VALUE` ("effectively means to retry forever") [Docs: retry.html]. Reactor's `retry(2)` also gave 3 subscriptions [Local], so the counts match between the two.
- **`attempt` starts at 0** on the first failure. The KDoc says "starting from zero on the initial call" [Docs: retry-when.html] [Local: `attempt=0` at the first call].
- **The predicate is not called once `retries` is reached** with `retry(n, predicate)`: "Note that `attempt` is checked first and predicate is not called when it reaches the given number of retries" [Source + Docs].
- **Exponential backoff** [Local, Demo E7]. `retryWhen { cause, attempt -> val retry = cause is IOException && attempt < 3; if (retry) delay(100L shl attempt.toInt()); retry }` made calls at **0, 100, 300, 700 ms**. At attempt 3 it gave up and rethrew `IOException: timeout from PSP (call 4)` to the `catch` below. A non-retryable `IllegalArgumentException("card declined")` was rethrown at once, after one predicate call with `attempt=0` [Local]. This matches Reactor's `Retry.backoff(3, 100ms)` attempt times from rx-05 (0, 100, 300, 700), except that Flow has **no jitter**, no built-in cap and no `RetryExhaustedException`. You write all of that yourself, and the original exception comes out [Source: no backoff helper exists in `Errors.kt`].
- **Retry replays emitted values** [Local, Demos E6, F]. `flow { emit("p1"); emit("p2"); throw … }.retry(2)` produced `[p1, p2, p1, p2, p1, p2, FALLBACK]`. A payment stream that failed after `payment-2` delivered `[payment-1, payment-2, payment-1, payment-2, payment-3]`. On a stream that has side effects, retry needs idempotent consumers, de-duplication, or a resumable source (a cursor or Kafka offset).
- `retry`/`retryWhen` don't retry downstream exceptions or the cancellation of the collector's job. They use the same `catchImpl` as `catch` [Source]. They **do** retry a `TimeoutCancellationException` from an upstream `timeout()`, which the flaky-provider pattern relies on (6.11, case B) [Local].
- The `retryWhen` predicate has a `FlowCollector` receiver, so it can `emit` (for example a "retrying…" status) before returning `true` [Source + Docs].
- The `catch` KDoc: to "retry an original flow use `retryWhen` operator that can retry the flow multiple times without introducing ever-growing stack of suspending calls" (in other words, don't call `emitAll(sameFlow)` from inside `catch` to retry) [Source].

### 6.6 `onEach` + `launchIn`

- `launchIn(scope)` is `scope.launch { collect() }` and returns the `Job` [Source: `terminal/Collect.kt`]. The docs' idiom is `flow.onEach { … }.onCompletion { … }.catch { … }.launchIn(scope)` [Docs: launch-in.html].
- Demo E8 [Local], in a `SupervisorJob()` + `CoroutineExceptionHandler` scope:
  - Without `catch`, an exception in `onEach` fails the launched job: "handler got java.lang.IllegalStateException: bad event 2", `j1.isCancelled == true`. The supervisor scope stays active. With a plain `Job()` the scope is cancelled too (see 6.8, the `IOException` row).
  - With `catch` **below** `onEach`: "catch below onEach saw … bad event 2", the job completes normally (`j2.isCancelled == false`), and value 3 is never processed. A caught error still ends the flow.
- Lesson point: in `launchIn` style, `catch` must come **after** `onEach`, because all the work is upstream of it. The `collect { }` lambda has gone away, so `catch` can see every error except cancellation.

### 6.7 `timeout()` (the Flow operator)

- `@FlowPreview`. The only overload takes `kotlin.time.Duration`. Added in 1.7.0 [Source + Docs: timeout.html + `CHANGES.md`].
- KDoc: "Returns a flow that will emit a `TimeoutCancellationException` if the upstream doesn't emit an item within the given time." "Note that delaying on the downstream doesn't trigger the timeout." "If non-positive, the flow is timed out immediately" [Source + Docs].
- **Messages** [Local, Demos E9, W2]: `Timed out waiting for 100ms` (from `"Timed out waiting for $timeout"` with `Duration.toString()`, so no space before "ms"), and `Timed out immediately` for a zero or negative timeout. Under `runTest` the message stays the same: it does **not** get the "virtual time" wording, because this operator builds its own message with `select { onTimeout }` [Source + Local].
- **What it times** [Source: `whileSelect`]. A fresh `onTimeout(d)` clause is armed only when the operator is waiting for the next upstream value. The downstream `emit` happens inside the select clause, so the time the downstream spends processing doesn't count. The docs example (emits at 0/100/200 ms, then a 1000 ms gap, with a 300 ms `onEach` downstream) reproduced `[1, 2, 3, -1]`. The `catch` ran at **1000 ms** of virtual time and the result was complete at 1300 ms [Local]. My reading of the code (inference, the intermediate steps were not logged): the third value went downstream at 600 ms, the downstream was busy until 900 ms, and only then was the 100 ms timer armed, so it fired at 1000.
- The first item counts too. `flow { delay(250); emit(1) }.timeout(200.ms)` gives `Timed out waiting for 200ms` [Local].
- **Boundary** [Local, virtual time only]. A gap of exactly 100 ms with `timeout(100.ms)` and a fast collector did **not** time out, while 101 ms did. Don't build a lesson on the exact-equality case, because it depends on how the scheduler orders events at the same instant.
- **Where it sits matters.** Put it above `retryWhen` and it is a per-attempt timeout that `retryWhen` can retry. Put it below and it is a deadline on the whole retry sequence (both in 6.11) [Local].

### 6.8 `withTimeout` around `collect`, and the "silent timeout" trap

- `withTimeout(250) { flow.collect() }` in real time (`runBlocking`) throws `kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms`. The `Duration` overload gives the same text. With `CoroutineName("settlement-import")` in the context: `Coroutine "settlement-import" timed out waiting for 50 ms` [Local + Source: `Timeout.kt`].
- **Under `runTest` the message changes**: `Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time. To use the real time, wrap 'withTimeout' in 'withContext(Dispatchers.Default.limitedParallelism(1))'` [Local + Source: `kotlinx-coroutines-test/common/src/TestDispatcher.kt`]. This appeared in 1.7.0: "The `withTimeout` exception messages indicate if the timeout used the virtual time (#3588)" [Source: `CHANGES.md`]. **Tests must not assert on the real-time message.**
- `withTimeoutOrNull(250) { flow { repeat(5) { delay(100); emit(it) } }.toList() }` returns `null`, and the values collected so far are lost to the caller. With `collect { partial += it }` you keep `[0, 1]` [Local].
- **A timeout that escapes `launch` is a cancellation, not a failure** [Local, Demo E11, real time, `CoroutineScope(Job() + handler)`]:
  - `launch { flow.timeout(50.ms).collect() }`: `job.isCancelled=true`, **the handler was not called**, and `scope.isActive=true`.
  - `launch { withTimeout(50) { delay(200) } }`: the same.
  - `launch { … throw IOException("real failure") }`: "handler got java.io.IOException: real failure", and `scope.isActive=false`.

  The docs back this up: "Coroutines internally use CancellationException for cancellation, these exceptions are ignored by all handlers" [Docs: exception-handling.html]. **Fix:** convert it to a domain exception, for example `.catch { e -> if (e is TimeoutCancellationException) throw ProviderTimeout(e) else throw e }`. The handler then gets `demo.ProviderTimeout: FX provider timed out; cause=…TimeoutCancellationException: Timed out waiting for 50ms`, and the scope is cancelled [Local, Demo X8]. Reactor's `timeout` signals `java.util.concurrent.TimeoutException` (`is CancellationException=false`) with "Did not observe any item or terminal signal within 100ms in 'source(FluxNever)' (and no fallback has been configured)" [Local], so in Reactor this trap does not exist.

### 6.9 `debounce`, `sample`

- Both are `@FlowPreview` [Source + Local].
- **`debounce`** [Source: `Delay.kt`]. A `produce` coroutine with a rendezvous channel, and a `select` that arms `onTimeout(t)` only while a value is pending. "The latest value is always emitted" means that on upstream completion the pending value is emitted **at once**.
  - The docs example (1, +90: 2, +90: 3, +1010: 4, +1010: 5 with `debounce(1000)`) gives `3@1180, 4@2190, 5@2200` → `[3, 4, 5]` [Local + Docs]. 5 came out at completion, with no wait.
  - `debounce(0)` returns the flow unchanged. A negative value gives `require(...) { "Debounce timeout should not be negative" }` [Source].
- **`sample`** [Source]. Values go through `produce(capacity = CONFLATED)` with a `fixedPeriodTicker` (the first tick after `period`).
  - The docs example (`repeat(10) { emit(it); delay(110) }.sample(200)`) gives `1@200, 3@400, 5@600, 7@800, 9@1000` [Local + Docs].
  - "the latest element is not emitted if it does not fit into the sampling window": `flow { emit("a"); delay(50); emit("b"); delay(10) }.sample(100)` gives `[]` [Local].
  - `sample(0)` gives `require(periodMillis > 0) { "Sample period should be positive" }` [Source].
- **Search-as-you-type** (Demo T3). `typing().debounce(300).map { it.trim() }.distinctUntilChanged().mapLatest { search(it) }` with keys at 0/80/160/240 ("acme"), 700/760 ("acme p") and 1300 ("acme pay") gives queries at 540 ("acme"), 1060 ("acme p") and 1300 ("acme pay", at once, because the upstream completed). Results came 150 ms after each query [Local]. In the lab, keep the key flow open (a `MutableSharedFlow`) so the last query is debounced too (verified in the LabCheck program: result at exactly 650 ms).

### 6.10 `onEmpty`, `first()`, `single()`, `firstOrNull()` and friends

- `onEmpty` is stable. Its action runs only when the upstream completed without emitting, and it can emit. `feeRules("m2").onEmpty { emit("default 3.5%") }` gives `[default 3.5%]`; for m1 the real rule passes through [Local + Source].
- Terminal operators [Local, Demo E12; Source: `terminal/Reduce.kt`]:

| Call | Result |
|---|---|
| `emptyFlow<Int>().first()` | `java.util.NoSuchElementException: Expected at least one element` |
| `flowOf(1,2).first { it > 5 }` | `java.util.NoSuchElementException: Expected at least one element matching the predicate` |
| `emptyFlow<Int>().firstOrNull()` | `null` |
| `emptyFlow<Int>().single()` | `java.util.NoSuchElementException: Flow is empty` |
| `flowOf(1,2).single()` | `java.lang.IllegalArgumentException: Flow has more than one element` (from `require`) |
| `flowOf(1,2).singleOrNull()` / `emptyFlow().singleOrNull()` | `null` / `null` |
| `emptyFlow<Int>().last()` | `java.util.NoSuchElementException: Expected at least one element` |
| `emptyFlow<Int>().reduce { a, b -> a + b }` | `java.util.NoSuchElementException: Empty flow can't be reduced` |
| `flowOf<Int?>(null).first()` | `null` (a real null element is fine; "empty" is tracked by an internal `NULL` marker) |

- **Early termination.** `first()`, `firstOrNull()`, `singleOrNull()`, `first { }` and `take` stop the upstream by throwing `AbortFlowException` through `collectWhile`. `first()` on a 3-element `flow { }` produced **1** element. `single()` uses plain `collect` plus `require`, so it stops at the **2nd** element (2 produced) with the `IllegalArgumentException` above [Local + Source].

### 6.11 `take` and `AbortFlowException`: is it visible?

- [Source: `Limit.kt`, `jvm/src/flow/internal/FlowExceptions.kt`] `take(n)` emits the n-th value and then throws `AbortFlowException(ownershipMarker)`. It catches the exception again only if the owner matches (`checkOwnership`). The class is `internal actual class AbortFlowException(owner: Any) : CancellationException("Flow was aborted, no more elements needed")`. It skips `fillInStackTrace` unless debug mode is on.
- **Yes, it is visible upstream** [Local, Demo E4]. A `try/catch(Throwable)` around `emit` in the builder printed `kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed; is CancellationException=true`, and the builder's `finally` ran. `onCompletion` above `take` shows it (6.4).
- **It is not visible downstream.** Below `take`, `onCompletion` sees `null`, and the collector just returns [Local].
- You cannot write `catch (e: AbortFlowException)`, because the class is internal. Treat it as a `CancellationException` and **rethrow** it. Swallowing it and emitting again violates exception transparency (6.1).
- `take(0)` → `IllegalArgumentException("Requested element count 0 should be positive")` [Source].
- The docs page describes this mechanism with a hand-written `myTake` that "throws a CancellationException to cancel the upstream flow". It says: "The collector can also cancel the upstream flow while the collecting coroutine stays active. To do this, throw a CancellationException from the collector." [Docs: coroutines-flow.html].
- Related cancellation checks [Local, Demo E14, real time; matches the old docs' "Flow cancellation checks"]. The collector calls `cancel()` on its own job when it sees 3:
  - `flow { for (i in 1..5) emit(i) }` delivered `[1, 2, 3]`. The builder runs `ensureActive` on each `emit` [Source: `Builders.kt` KDoc].
  - `(1..5).asFlow()` delivered `[1, 2, 3, 4, 5]`. It makes no cancellation check.
  - `(1..5).asFlow().cancellable()` delivered `[1, 2, 3]`.

### 6.12 Pattern: flaky provider → per-attempt timeout → retry with backoff → fallback

The full code is in Demo P1. The snippet here is condensed from it, with the logging removed. All cases ran under virtual time [Local]:
```kotlin
fun isTransient(e: Throwable) = e is IOException || e is TimeoutCancellationException

fun <T> Flow<T>.retryWithBackoff(maxRetries: Long = 3, first: Duration = 100.milliseconds, max: Duration = 1.seconds,
                                 retryOn: (Throwable) -> Boolean = ::isTransient): Flow<T> =
    retryWhen { cause, attempt ->
        if (attempt >= maxRetries || !retryOn(cause)) return@retryWhen false
        delay(minOf(first * (1L shl attempt.toInt()).toDouble(), max))   // 100, 200, 400 ms …
        true
    }

fun fxRate(pair: String, primary: FakeProvider, fallback: FakeProvider): Flow<Rate> =
    primary.rate(pair)
        .timeout(300.milliseconds)        // per attempt
        .retryWithBackoff()               // 3 retries
        .catch { e -> if (!isTransient(e)) throw e; emitAll(fallback.rate(pair)) }
```
Observed (virtual ms) [Local]:
- **A. Two `IOException`s, then success in 50 ms.** Calls at 0, 120 and 340 (each failing call takes 20 ms, then waits 100 and 200). Result from the primary at **390**. `primary=3, fallback=0`.
- **B. The primary is always too slow (1000 ms).** Calls at 0, 400, 900 and 1600, each cut off at +300 by `TimeoutCancellationException`; `retryWhen` retried them. At 1900: "primary gave up (TimeoutCancellationException: Timed out waiting for 300ms); using fallback". Fallback result at **1930**. `primary=4, fallback=1`.
- **C. Non-retryable** (`IllegalArgumentException("unsupported pair XXX/EUR")`). No retry, no fallback. The caller saw it at **20 ms**. `primary=1, fallback=0`.
- **D. Primary down and fallback down.** 4 primary calls (0, 120, 340, 760), then the fallback at 780. The caller saw `java.io.IOException: fallback down` at **800**. The primary's error is not attached (6.3).
- **E. Overall budget.** `….timeout(300.ms).retryWithBackoff().timeout(1.seconds).catch { emitAll(fallback) }` gave calls at 0, 400 and 900. At **1000** the outer timeout fired (`Timed out waiting for 1s`) and cancelled the third attempt. Fallback result at **1030**. `primary=3`.
- **F. Streaming source.** A replayed prefix produced duplicates (6.5).

Lesson points: the order of `timeout` → `retryWhen` → `timeout` → `catch` decides what each one sees. `retryOn` must list `TimeoutCancellationException`, because a timeout is not an `IOException`. The `catch` filter rethrows programming and business errors. And the fallback's failure is what the caller sees.

---

## Common misconceptions (with the correction)

1. **"`flatMapMerge` runs my lambda in parallel."** Not the lambda. `transform` runs sequentially in one producer coroutine; only the **returned flows** are collected concurrently. A suspend call placed before `flowOf(result)` makes the whole thing sequential: 800 ms vs 450 ms [Source + Local].
2. **"`flatMapConcat` is like Reactor's `concatMap` with prefetch."** In Flow, the outer's code is paused inside `emit` while each inner runs (800 ms in D1). Reactor 3.8.8's default `concatMap` is no-prefetch too, but its timer-based source kept running (600 ms). `buffer()` before `flatMapConcat` gives 600 ms [Source + Local].
3. **"`flatMapMerge` defaults to unlimited / to Reactor's 256."** It is 16 (`DEFAULT_CONCURRENCY`), set through `kotlinx.coroutines.flow.defaultConcurrency` and read once; 0 crashes class init [Source + Local].
4. **"`flatMapLatest` starts the new inner immediately."** It cancels the old one, **waits for it to finish** (`join`), then starts the new one [Source + Local: a 50 ms cleanup delayed B to 150 ms].
5. **"`zip` with an FX stream gives me the latest rate."** `zip` pairs by index and paces the faster side. Use `combine` for "latest of each" [Local].
6. **"`combine` emits once per upstream value."** Only while the collector keeps up. With a slow collector it skips intermediate values (1, 3, 5, 7, 9, 10) and also suspends the sources. Use `buffer()` to keep every combination, or `conflate()` to keep only the newest [Source + Local].
7. **"`combine` emits as soon as any source emits."** It waits until every source has a value. A source that never emits means no output at all [Local].
8. **"`catch` at the end protects the whole pipeline, including `collect { }`."** It sees only upstream exceptions. Move the work into `onEach` above it [Source + Docs + Local].
9. **"`catch` never sees `CancellationException`."** It skips the cancellation of the **collector's job**, but it does catch a `CancellationException` thrown by upstream code, including `TimeoutCancellationException` from `timeout()`/`withTimeout` [Source + Local].
10. **"`onCompletion(cause)` non-null means something went wrong."** It is also non-null on normal cancellation (`JobCancellationException`) and when a downstream `take`/`first` stops early (`AbortFlowException`) [Local].
11. **"`retry(3)` means 3 attempts."** It means 3 **retries**, so 4 collections. It also replays values that were already emitted [Source + Local].
12. **"A Flow `timeout` behaves like Reactor's `timeout` error."** It throws a `CancellationException` subclass. Uncaught inside `launch`, it cancels that coroutine silently: no handler call, and the parent keeps running [Local + Docs].
13. **"`timeout(100.ms)` limits how long my collector may take."** It times only the wait for the **next upstream value**. Time spent in the downstream doesn't count [Source + Docs + Local].
14. **"Tests can assert the `withTimeout` message."** Under `runTest` it reads "Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time…", not "Timed out waiting for 50 ms" [Local].
15. **"`take` just stops collecting; the upstream never notices."** The upstream's `emit` throws `AbortFlowException` (a `CancellationException`). A `try/catch(Throwable)` around `emit` sees it, and swallowing it and emitting again throws the exception-transparency `IllegalStateException` [Source + Local].
16. **"`single()` on a two-element flow throws `NoSuchElementException`."** It throws `IllegalArgumentException: Flow has more than one element`. `NoSuchElementException("Flow is empty")` is for the empty case [Local].
17. **"These operators are experimental, so the code won't compile without `@OptIn`."** It compiles with a warning. It only fails if warnings are errors. The opt-in is about API stability, not correctness [Local].
18. **"`asFlow()` stops when my coroutine is cancelled."** `(1..5).asFlow()` delivered all 5 values after the collector cancelled its own job at 3. Use `.cancellable()` or the `flow { }` builder [Local + Docs].

---

## Picture ideas (mental models for narrated animations)

- **`flatMapConcat`: a single-lane bridge with a gatekeeper who is also the truck driver.** The outer flow is the depot that loads trucks. In Flow the depot worker drives each truck across the bridge himself, so no new truck is loaded while one is on the bridge. Animate the depot freezing. Then add `buffer()`: a parking lot appears in front of the bridge, the depot keeps loading, and trucks queue.
- **`flatMapMerge`: a toll plaza with N booths feeding one merge lane.** The booths are semaphore permits (16 open by default). One dispatcher at the entrance (the producer coroutine, running `transform`) waves cars in one at a time. Cars leave by finish time, not arrival time. The merge lane has 64 parking slots (`Channel.BUFFERED`). The gotcha scene: the dispatcher inspects each car himself (work in `transform`), so 15 booths sit empty.
- **`flatMapLatest` / `mapLatest`: a railway switch with a brake.** A new value throws the switch. The old train gets an emergency brake (`ChildCancelledException`), and the junction stays closed until it has fully stopped and cleared (`join`). Only then does the new train enter. Show the 50 ms "cleanup" as the old train backing out.
- **`merge`: on-ramps joining a highway.** Cars enter in arrival order. The highway closes when the last on-ramp closes. A crash on one ramp closes the whole highway, and the other ramps' cars are turned back (`JobCancellationException`).
- **`zip`: a zipper.** Each left tooth must meet a right tooth. The left side (receiver) has no slack and waits at every tooth. The right side has a helper (its producer coroutine) who hands over one tooth at a time (rendezvous). The zipper stops at the end of the shorter side, and the rest of the longer side is cut off (`AbortFlowException`).
- **`combine`: a scoreboard and a slow photographer.** One slot per source. No photo until every slot shows a number. Each update rewrites its slot, and the photographer takes one photo per "batch". If the photographer is slow, several updates to the same slot between photos blur into the last one. The mailbox in front of the board holds only as many notes as there are slots, so fast sources wait at the mailbox. Contrast it with Reactor's photographer, who keeps a queue of every board state and develops them all.
- **`catch`: a safety net under the upstream half of the pipe.** Things that fall from above are caught. Things dropped below the net (the collector) fall to the caller. A falling "cancellation" sign marked with **this job's** name passes through the net; other cancellation signs land in it.
- **Exception transparency: a one-way valve.** Once the downstream has shouted "I broke" back up the pipe (an exception out of `emit`), the valve locks. Any further push from upstream sets off an alarm (`IllegalStateException`).
- **`onCompletion`: a bell at the end of the line that rings exactly once,** with a tag that says why: blank (success), the error, "cancelled", or "aborted, no more needed" (seen only by stations above a `take`).
- **`retry`: rewinding the tape.** Everything already played is played again (the duplicates), with pauses that double: 100, 200, 400. Then the side door: the fallback.
- **`timeout()`: a watchdog egg timer.** It is wound each time the operator starts waiting for the next item, and it pauses while the downstream is busy. When it rings, the alarm is a "cancellation" note, not an error note. Inside a `launch`, nobody hears it unless you translate it.
- **`debounce`: an elevator door** that closes only after nobody has stepped in for 300 ms. When the building closes (the flow completes), the last person is let out at once. **`sample`: a security camera** taking a still every period. Frames between stills are lost, and if nothing new happened there is no still.
- **`take` / `first`: hanging up the phone.** The caller hangs up after the n-th word. The speaker (upstream) hears a dial tone (`AbortFlowException`) on the next word and must stop talking, not keep shouting into the dead line.

---

## Demo ideas with expected outcomes

Every program below was compiled with Kotlin 2.4.21 (`K2JVMCompiler -jvm-target 21`) against kotlinx-coroutines-core-jvm 1.11.0 and kotlinx-coroutines-test-jvm 1.11.0 on OpenJDK 21.0.12.1. The outputs are pasted unedited. Times are **virtual** (from `TestCoroutineScheduler`) unless noted. In a Gradle demo module these need `org.jetbrains.kotlinx:kotlinx-coroutines-test:1.11.0` on the demo (not only test) classpath, because the demos use `runTest` as their `main` clock. A lesson can instead wrap the same flows in `runBlocking` and measure real time; the numbers then drift by a few ms.

Shared helper used by most demos (`T.kt`):
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*

/** Virtual time of the TestCoroutineScheduler that runs the current coroutine (runTest only). */
suspend fun now(): Long = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))
```

### D0. Stability: compile without `@OptIn`
Program: `src/stab/Stability.kt` below. Expected: warnings (no errors) for lines 8–14 and 25 (`ExperimentalCoroutinesApi`) and 19–21 and 23–24 (`FlowPreview`); nothing for `merge`, `zip`, `combine`, `retry`, `retryWhen`, `catch`, `onCompletion`, `onEmpty`, `first`, `single`, `firstOrNull`.
```kotlin
// Compiled WITHOUT any @OptIn so the compiler reports each operator that needs one.
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlin.time.Duration.Companion.milliseconds

suspend fun stability() {
    val f = flowOf(1, 2, 3)
    f.flatMapConcat { flowOf(it) }.collect()           // L8
    f.flatMapMerge(4) { flowOf(it) }.collect()         // L9
    f.flatMapLatest { flowOf(it) }.collect()           // L10
    f.map { flowOf(it) }.flattenConcat().collect()     // L11
    f.map { flowOf(it) }.flattenMerge().collect()      // L12
    f.transformLatest<Int, Int> { emit(it) }.collect() // L13
    f.mapLatest { it }.collect()                       // L14
    merge(f, f).collect()                              // L15
    f.zip(f) { a, b -> a + b }.collect()               // L16
    f.combine(f) { a, b -> a + b }.collect()           // L17
    combine(f, f, f) { a, b, c -> a + b + c }.collect()// L18
    f.debounce(10).collect()                           // L19
    f.sample(10).collect()                             // L20
    f.timeout(10.milliseconds).collect()               // L21
    f.retry(3).retryWhen { _, a -> a < 3 }.catch { }.onCompletion { }.onEmpty { }.collect() // L22
    println(DEFAULT_CONCURRENCY)                       // L23
    println(DEFAULT_CONCURRENCY_PROPERTY_NAME)         // L24
    f.chunked(2).collect()                             // L25
    f.first(); f.single(); f.firstOrNull()             // L26
}
```
Observed warnings (abridged to one line each; the full text repeats the opt-in sentence):
```
Stability.kt:8:7   flatMapConcat   needs opt-in … ExperimentalCoroutinesApi
Stability.kt:9:7   flatMapMerge    needs opt-in … ExperimentalCoroutinesApi
Stability.kt:10:7  flatMapLatest   needs opt-in … ExperimentalCoroutinesApi
Stability.kt:11:26 flattenConcat   needs opt-in … ExperimentalCoroutinesApi
Stability.kt:12:26 flattenMerge    needs opt-in … ExperimentalCoroutinesApi
Stability.kt:13:7  transformLatest needs opt-in … ExperimentalCoroutinesApi
Stability.kt:14:7  mapLatest       needs opt-in … ExperimentalCoroutinesApi
Stability.kt:19:7  debounce        is in a preview state … FlowPreview
Stability.kt:20:7  sample          is in a preview state … FlowPreview
Stability.kt:21:7  timeout         is in a preview state … FlowPreview
Stability.kt:23:13 DEFAULT_CONCURRENCY               is in a preview state … FlowPreview
Stability.kt:24:13 DEFAULT_CONCURRENCY_PROPERTY_NAME is in a preview state … FlowPreview
Stability.kt:25:7  chunked         needs opt-in … ExperimentalCoroutinesApi
```

### D1. The flatMap trio on one timeline (marble-diagram source)
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// Outer: 1 at t=0, 2 at t=100, 3 at t=200 (measured from when the outer is free to continue).
fun outer(): Flow<Int> = flow {
    for (n in 1..3) {
        if (n > 1) delay(100)
        log("outer emits $n")
        emit(n)
    }
}
// Inner for n: "n-a" 50 ms after start, "n-b" 150 ms after that.
fun inner(n: Int): Flow<String> = flow {
    delay(50); emit("$n-a")
    delay(150); emit("$n-b")
}.onCompletion { cause -> if (cause != null) log("inner $n cancelled: ${cause::class.simpleName}: ${cause.message}") }

fun main() {
    for ((name, op) in listOf<Pair<String, (Flow<Int>) -> Flow<String>>>(
        "flatMapConcat" to { f -> f.flatMapConcat { inner(it) } },
        "flatMapMerge" to { f -> f.flatMapMerge { inner(it) } },
        "flatMapLatest" to { f -> f.flatMapLatest { inner(it) } },
    )) runTest {
        println("== $name")
        op(outer()).collect { log("  collector got $it") }
        log("done")
    }
}
```
Output:
```
== flatMapConcat
    0 ms  outer emits 1
   50 ms    collector got 1-a
  200 ms    collector got 1-b
  300 ms  outer emits 2
  350 ms    collector got 2-a
  500 ms    collector got 2-b
  600 ms  outer emits 3
  650 ms    collector got 3-a
  800 ms    collector got 3-b
  800 ms  done
== flatMapMerge
    0 ms  outer emits 1
   50 ms    collector got 1-a
  100 ms  outer emits 2
  150 ms    collector got 2-a
  200 ms  outer emits 3
  200 ms    collector got 1-b
  250 ms    collector got 3-a
  300 ms    collector got 2-b
  400 ms    collector got 3-b
  400 ms  done
== flatMapLatest
    0 ms  outer emits 1
   50 ms    collector got 1-a
  100 ms  outer emits 2
  100 ms  inner 1 cancelled: ChildCancelledException: Child of the scoped flow was cancelled
  150 ms    collector got 2-a
  200 ms  outer emits 3
  200 ms  inner 2 cancelled: ChildCancelledException: Child of the scoped flow was cancelled
  250 ms    collector got 3-a
  400 ms    collector got 3-b
  400 ms  done
```

### D2. Fee fan-out: `concurrency`, ordering, the transform gotcha, `DEFAULT_CONCURRENCY`
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

val latencyMs = mapOf("m1" to 300L, "m2" to 100L, "m3" to 200L, "m4" to 50L, "m5" to 150L)
var inFlight = 0; var maxInFlight = 0

suspend fun feeLookup(merchant: String): String {
    inFlight++; maxInFlight = maxOf(maxInFlight, inFlight)
    log("    start lookup $merchant (in flight: $inFlight)")
    try { delay(latencyMs.getValue(merchant)); return "$merchant:fee" } finally { inFlight-- }
}

fun main() {
    println("DEFAULT_CONCURRENCY = $DEFAULT_CONCURRENCY (property $DEFAULT_CONCURRENCY_PROPERTY_NAME)")
    runTest {
        println("== flatMapMerge(concurrency = 2), the call is INSIDE the inner flow")
        val merchants = latencyMs.keys.asFlow()
        val f = merchants.flatMapMerge(concurrency = 2) { m ->
            log("  transform called for $m")
            flow { emit(feeLookup(m)) }
        }
        println("  flow object: $f")
        f.collect { log("collector got $it") }
        log("done, max in flight = $maxInFlight")
    }
    runTest {
        maxInFlight = 0
        println("== flatMapMerge(concurrency = 2), the call is in the transform lambda (gotcha)")
        latencyMs.keys.asFlow().flatMapMerge(concurrency = 2) { m -> val fee = feeLookup(m); flowOf(fee) }
            .collect { log("collector got $it") }
        log("done, max in flight = $maxInFlight")
    }
    runTest {
        maxInFlight = 0
        println("== default concurrency with 40 lookups of 100 ms each")
        (1..40).asFlow().flatMapMerge { n -> flow { inFlight++; maxInFlight = maxOf(maxInFlight, inFlight); delay(100); inFlight--; emit(n) } }
            .toList().also { log("done: ${it.size} results, max in flight = $maxInFlight") }
    }
    runTest {
        println("== map { suspend call } is sequential (the docs' recommendation when you need one result per item)")
        latencyMs.keys.asFlow().map { feeLookup(it) }.collect { log("collector got $it") }
        log("done")
    }
    println("flatMapMerge(1) object: " + flowOf(1).flatMapMerge(1) { flowOf(it) })
    println("flatMapMerge(4).buffer(0) object: " + flowOf(1).flatMapMerge(4) { flowOf(it) }.buffer(0))
    try { flowOf(1).flatMapMerge(0) { flowOf(it) } } catch (e: Exception) { println("flatMapMerge(0): $e") }
}
```
Output (default JVM):
```
DEFAULT_CONCURRENCY = 16 (property kotlinx.coroutines.flow.defaultConcurrency)
== flatMapMerge(concurrency = 2), the call is INSIDE the inner flow
  flow object: ChannelFlowMerge[concurrency=2, capacity=-2]
    0 ms    transform called for m1
    0 ms    transform called for m2
    0 ms    transform called for m3
    0 ms      start lookup m1 (in flight: 1)
    0 ms      start lookup m2 (in flight: 2)
  100 ms  collector got m2:fee
  100 ms    transform called for m4
  100 ms      start lookup m3 (in flight: 2)
  300 ms  collector got m1:fee
  300 ms  collector got m3:fee
  300 ms    transform called for m5
  300 ms      start lookup m4 (in flight: 1)
  300 ms      start lookup m5 (in flight: 2)
  350 ms  collector got m4:fee
  450 ms  collector got m5:fee
  450 ms  done, max in flight = 2
== flatMapMerge(concurrency = 2), the call is in the transform lambda (gotcha)
    0 ms      start lookup m1 (in flight: 1)
  300 ms      start lookup m2 (in flight: 1)
  300 ms  collector got m1:fee
  400 ms      start lookup m3 (in flight: 1)
  400 ms  collector got m2:fee
  600 ms      start lookup m4 (in flight: 1)
  600 ms  collector got m3:fee
  650 ms      start lookup m5 (in flight: 1)
  650 ms  collector got m4:fee
  800 ms  collector got m5:fee
  800 ms  done, max in flight = 1
== default concurrency with 40 lookups of 100 ms each
  300 ms  done: 40 results, max in flight = 16
== map { suspend call } is sequential (the docs' recommendation when you need one result per item)
    0 ms      start lookup m1 (in flight: 1)
  300 ms  collector got m1:fee
  300 ms      start lookup m2 (in flight: 1)
  400 ms  collector got m2:fee
  400 ms      start lookup m3 (in flight: 1)
  600 ms  collector got m3:fee
  600 ms      start lookup m4 (in flight: 1)
  650 ms  collector got m4:fee
  650 ms      start lookup m5 (in flight: 1)
  800 ms  collector got m5:fee
  800 ms  done
flatMapMerge(1) object: kotlinx.coroutines.flow.FlowKt__MergeKt$flattenConcat$$inlined$unsafeFlow$1@fad74ee
flatMapMerge(4).buffer(0) object: ChannelFlowMerge[concurrency=4, capacity=0]
flatMapMerge(0): java.lang.IllegalArgumentException: Expected positive concurrency level, but had 0
```
With `-Dkotlinx.coroutines.flow.defaultConcurrency=4`, the first line becomes `DEFAULT_CONCURRENCY = 4 …` and the 40-lookup run becomes `1000 ms  done: 40 results, max in flight = 4`. With `=0`:
```
Exception in thread "main" java.lang.ExceptionInInitializerError
	at kotlinx.coroutines.flow.FlowKt.getDEFAULT_CONCURRENCY(Unknown Source)
	at demo.FeeFanOutKt.main(FeeFanOut.kt:17)
	at demo.FeeFanOutKt.main(FeeFanOut.kt)
Caused by: java.lang.IllegalStateException: System property 'kotlinx.coroutines.flow.defaultConcurrency' should be in range 1..2147483647, but is '0'
	at kotlinx.coroutines.internal.SystemPropsKt__SystemProps_commonKt.systemProp(SystemProps.common.kt:50)
```

### D3. Which coroutine runs what (run with `-Dkotlinx.coroutines.debug`)
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// Run with -Dkotlinx.coroutines.debug so thread names carry "@coroutine#N".
suspend fun who(): String {
    val job = currentCoroutineContext()[Job]
    val co = Thread.currentThread().name.substringAfter("@", "?")
    return "$co (${job!!::class.simpleName})"
}
fun src(tag: String, n: Int = 2) = flow { repeat(n) { println("    upstream $tag emits $it in ${who()}"); emit("$tag$it") } }

fun main() {
    val cases = listOf<Pair<String, () -> Flow<String>>>(
        "plain map" to { src("a").map { it } },
        "flatMapConcat" to { src("o").flatMapConcat { o -> src("i[$o]", 1) } },
        "flatMapMerge" to { src("o").flatMapMerge { o -> src("i[$o]", 1) } },
        "flatMapLatest" to { src("o").flatMapLatest { o -> src("i[$o]", 1) } },
        "merge" to { merge(src("a"), src("b")) },
        "zip" to { src("a").zip(src("b")) { x, y -> x + y } },
        "combine" to { combine(src("a"), src("b")) { x, y -> x + y } },
        "buffer" to { src("a").buffer() },
        "debounce" to { src("a").debounce(10) },
        "timeout" to { src("a").timeout(kotlin.time.Duration.parse("1s")) },
    )
    for ((name, mk) in cases) runTest {
        println("== $name  (collector runs in ${who()})")
        mk().collect { println("    collector got $it in ${who()}") }
    }
}
```
Output:
```
== plain map  (collector runs in kotlinx.coroutines.test runner#2 (TestScopeImpl))
    upstream a emits 0 in kotlinx.coroutines.test runner#2 (TestScopeImpl)
    collector got a0 in kotlinx.coroutines.test runner#2 (TestScopeImpl)
    upstream a emits 1 in kotlinx.coroutines.test runner#2 (TestScopeImpl)
    collector got a1 in kotlinx.coroutines.test runner#2 (TestScopeImpl)
== flatMapConcat  (collector runs in kotlinx.coroutines.test runner#4 (TestScopeImpl))
    upstream o emits 0 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
    upstream i[o0] emits 0 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
    collector got i[o0]0 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
    upstream o emits 1 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
    upstream i[o1] emits 0 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
    collector got i[o1]0 in kotlinx.coroutines.test runner#4 (TestScopeImpl)
== flatMapMerge  (collector runs in kotlinx.coroutines.test runner#6 (TestScopeImpl))
    upstream o emits 0 in coroutine#7 (ProducerCoroutine)
    upstream o emits 1 in coroutine#7 (ProducerCoroutine)
    upstream i[o0] emits 0 in coroutine#8 (StandaloneCoroutine)
    upstream i[o1] emits 0 in coroutine#9 (StandaloneCoroutine)
    collector got i[o0]0 in kotlinx.coroutines.test runner#6 (ScopeCoroutine)
    collector got i[o1]0 in kotlinx.coroutines.test runner#6 (ScopeCoroutine)
== flatMapLatest  (collector runs in kotlinx.coroutines.test runner#11 (TestScopeImpl))
    upstream o emits 0 in coroutine#12 (ScopeCoroutine)
    upstream i[o0] emits 0 in coroutine#13 (StandaloneCoroutine)
    upstream o emits 1 in coroutine#12 (ScopeCoroutine)
    upstream i[o1] emits 0 in coroutine#14 (StandaloneCoroutine)
    collector got i[o0]0 in kotlinx.coroutines.test runner#11 (ScopeCoroutine)
    collector got i[o1]0 in kotlinx.coroutines.test runner#11 (ScopeCoroutine)
== merge  (collector runs in kotlinx.coroutines.test runner#16 (TestScopeImpl))
    upstream a emits 0 in coroutine#18 (StandaloneCoroutine)
    upstream a emits 1 in coroutine#18 (StandaloneCoroutine)
    upstream b emits 0 in coroutine#19 (StandaloneCoroutine)
    upstream b emits 1 in coroutine#19 (StandaloneCoroutine)
    collector got a0 in kotlinx.coroutines.test runner#16 (ScopeCoroutine)
    collector got a1 in kotlinx.coroutines.test runner#16 (ScopeCoroutine)
    collector got b0 in kotlinx.coroutines.test runner#16 (ScopeCoroutine)
    collector got b1 in kotlinx.coroutines.test runner#16 (ScopeCoroutine)
== zip  (collector runs in kotlinx.coroutines.test runner#21 (TestScopeImpl))
    upstream a emits 0 in kotlinx.coroutines.test runner#21 (JobImpl)
    upstream b emits 0 in coroutine#22 (ProducerCoroutine)
    upstream b emits 1 in coroutine#22 (ProducerCoroutine)
    collector got a0b0 in kotlinx.coroutines.test runner#21 (ScopeCoroutine)
    upstream a emits 1 in kotlinx.coroutines.test runner#21 (JobImpl)
    collector got a1b1 in kotlinx.coroutines.test runner#21 (ScopeCoroutine)
== combine  (collector runs in kotlinx.coroutines.test runner#24 (TestScopeImpl))
    upstream a emits 0 in coroutine#25 (StandaloneCoroutine)
    upstream b emits 0 in coroutine#26 (StandaloneCoroutine)
    collector got a0b0 in kotlinx.coroutines.test runner#24 (FlowCoroutine)
    upstream a emits 1 in coroutine#25 (StandaloneCoroutine)
    upstream b emits 1 in coroutine#26 (StandaloneCoroutine)
    collector got a1b1 in kotlinx.coroutines.test runner#24 (FlowCoroutine)
== buffer  (collector runs in kotlinx.coroutines.test runner#28 (TestScopeImpl))
    upstream a emits 0 in coroutine#29 (ProducerCoroutine)
    upstream a emits 1 in coroutine#29 (ProducerCoroutine)
    collector got a0 in kotlinx.coroutines.test runner#28 (ScopeCoroutine)
    collector got a1 in kotlinx.coroutines.test runner#28 (ScopeCoroutine)
== debounce  (collector runs in kotlinx.coroutines.test runner#31 (TestScopeImpl))
    upstream a emits 0 in coroutine#32 (ProducerCoroutine)
    upstream a emits 1 in coroutine#32 (ProducerCoroutine)
    collector got a1 in kotlinx.coroutines.test runner#31 (FlowCoroutine)
== timeout  (collector runs in kotlinx.coroutines.test runner#34 (TestScopeImpl))
    upstream a emits 0 in coroutine#35 (ProducerCoroutine)
    upstream a emits 1 in coroutine#35 (ProducerCoroutine)
    collector got a0 in kotlinx.coroutines.test runner#34 (FlowCoroutine)
    collector got a1 in kotlinx.coroutines.test runner#34 (FlowCoroutine)
```

### D4. FX × price: `combine` vs `zip`, slow collector, empty source, docs examples
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// Prices (USD cents) every 100 ms starting at t=100; FX rate USD->EUR at t=250 and t=550.
fun prices() = flow { for (p in listOf(1000, 1010, 1020, 1030, 1040, 1050)) { delay(100); log("price  $p"); emit(p) } }
fun fxRates() = flow { delay(250); log("fx     0.92"); emit(0.92); delay(300); log("fx     0.95"); emit(0.95) }

fun main() {
    runTest {
        println("== combine(prices, fx): fast collector")
        combine(prices(), fxRates()) { p, fx -> "$p@$fx" }.collect { log("  -> $it") }
        log("done")
    }
    runTest {
        println("== zip(prices, fx): pairs by index, paced by the slower, ends with the shorter")
        prices().onCompletion { log("prices completed, cause=$it") }
            .zip(fxRates().onCompletion { log("fx completed, cause=$it") }) { p, fx -> "$p@$fx" }
            .collect { log("  -> $it") }
        log("done")
    }
    runTest {
        println("== combine: fast source (1..10 every 10 ms) + one config value, collector takes 100 ms per item")
        val fast = flow { for (i in 1..10) { delay(10); emit(i) } }
        val cfg = flowOf("cfg")
        combine(fast, cfg) { i, c -> "$i/$c" }.collect { log("  -> $it (slow collector)"); delay(100) }
        log("done")
    }
    runTest {
        println("== combine: same, but fast collector")
        val fast = flow { for (i in 1..10) { delay(10); emit(i) } }
        combine(fast, flowOf("cfg")) { i, c -> "$i/$c" }.collect { log("  -> $it") }
    }
    runTest {
        println("== combine: two synchronous flows (no delays)")
        combine(flowOf("a0", "a1", "a2"), flowOf("b0", "b1", "b2")) { a, b -> a + b }.collect { log("  -> $it") }
    }
    runTest {
        println("== combine: one side never emits (empty) -> nothing, completes")
        combine(prices(), emptyFlow<Double>()) { p, fx -> "$p@$fx" }.collect { log("  -> $it") }
        log("done (no emissions)")
    }
    runTest {
        println("== docs example: flowOf(1,2).onEach{delay(10)} combine flowOf(a,b,c).onEach{delay(15)}")
        val flow = flowOf(1, 2).onEach { delay(10) }
        val flow2 = flowOf("a", "b", "c").onEach { delay(15) }
        flow.combine(flow2) { i, s -> i.toString() + s }.collect { log("  -> $it") }
        println("== docs example: zip of flowOf(1,2,3).onEach{delay(10)} and flowOf(a,b,c,d).onEach{delay(15)}")
        flowOf(1, 2, 3).onEach { delay(10) }.zip(flowOf("a", "b", "c", "d").onEach { delay(15) }) { i, s -> "$i$s" }.collect { log("  -> $it") }
    }
}
```
Output (note: the last block's `zip` times are cumulative after the `combine` example, so subtract 45 ms. C4 below runs it alone):
```
== combine(prices, fx): fast collector
  100 ms  price  1000
  200 ms  price  1010
  250 ms  fx     0.92
  250 ms    -> 1010@0.92
  300 ms  price  1020
  300 ms    -> 1020@0.92
  400 ms  price  1030
  400 ms    -> 1030@0.92
  500 ms  price  1040
  500 ms    -> 1040@0.92
  550 ms  fx     0.95
  550 ms    -> 1040@0.95
  600 ms  price  1050
  600 ms    -> 1050@0.95
  600 ms  done
== zip(prices, fx): pairs by index, paced by the slower, ends with the shorter
  100 ms  price  1000
  250 ms  fx     0.92
  250 ms    -> 1000@0.92
  350 ms  price  1010
  550 ms  fx     0.95
  550 ms  fx completed, cause=null
  550 ms    -> 1010@0.95
  550 ms  prices completed, cause=kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  550 ms  done
== combine: fast source (1..10 every 10 ms) + one config value, collector takes 100 ms per item
   10 ms    -> 1/cfg (slow collector)
  110 ms    -> 3/cfg (slow collector)
  210 ms    -> 5/cfg (slow collector)
  310 ms    -> 7/cfg (slow collector)
  410 ms    -> 9/cfg (slow collector)
  510 ms    -> 10/cfg (slow collector)
  610 ms  done
== combine: same, but fast collector
   10 ms    -> 1/cfg
   20 ms    -> 2/cfg
   30 ms    -> 3/cfg
   40 ms    -> 4/cfg
   50 ms    -> 5/cfg
   60 ms    -> 6/cfg
   70 ms    -> 7/cfg
   80 ms    -> 8/cfg
   90 ms    -> 9/cfg
  100 ms    -> 10/cfg
== combine: two synchronous flows (no delays)
    0 ms    -> a0b0
    0 ms    -> a1b1
    0 ms    -> a2b2
== combine: one side never emits (empty) -> nothing, completes
  100 ms  price  1000
  200 ms  price  1010
  300 ms  price  1020
  400 ms  price  1030
  500 ms  price  1040
  600 ms  price  1050
  600 ms  done (no emissions)
== docs example: flowOf(1,2).onEach{delay(10)} combine flowOf(a,b,c).onEach{delay(15)}
   15 ms    -> 1a
   20 ms    -> 2a
   30 ms    -> 2b
   45 ms    -> 2c
== docs example: zip of flowOf(1,2,3).onEach{delay(10)} and flowOf(a,b,c,d).onEach{delay(15)}
   60 ms    -> 1a
   75 ms    -> 2b
   90 ms    -> 3c
```

### C1–C4. `combine` with a slow collector: backpressure, `conflate`, `buffer`
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

fun main() {
    runTest {
        println("== C1 combine with a slow collector: when does the fast source get to emit?")
        val fast = flow { for (i in 1..10) { delay(10); log("  fast emits $i"); emit(i) } }
        combine(fast, flowOf("cfg")) { i, c -> "$i/$c" }.collect { log("-> $it (collector busy 100 ms)"); delay(100) }
        log("done")
    }
    runTest {
        println("== C2 the same slow collector after conflate(): only the newest combination survives")
        val fast = flow { for (i in 1..10) { delay(10); emit(i) } }
        combine(fast, flowOf("cfg")) { i, c -> "$i/$c" }.conflate().collect { log("-> $it"); delay(100) }
    }
    runTest {
        println("== C3 the same slow collector with buffer(UNLIMITED): every combination is kept")
        val fast = flow { for (i in 1..10) { delay(10); emit(i) } }
        val got = combine(fast, flowOf("cfg")) { i, c -> "$i/$c" }.buffer(kotlinx.coroutines.channels.Channel.UNLIMITED).onEach { delay(100) }.toList()
        log("got ${got.size}: $got")
    }
    runTest {
        println("== C4 docs zip example on its own")
        flowOf(1, 2, 3).onEach { delay(10) }.zip(flowOf("a", "b", "c", "d").onEach { delay(15) }) { i, s -> "$i$s" }.collect { log("-> $it") }
    }
}
```
Output:
```
== C1 combine with a slow collector: when does the fast source get to emit?
   10 ms    fast emits 1
   10 ms  -> 1/cfg (collector busy 100 ms)
   20 ms    fast emits 2
   30 ms    fast emits 3
   40 ms    fast emits 4
  110 ms  -> 3/cfg (collector busy 100 ms)
  120 ms    fast emits 5
  130 ms    fast emits 6
  210 ms  -> 5/cfg (collector busy 100 ms)
  220 ms    fast emits 7
  230 ms    fast emits 8
  310 ms  -> 7/cfg (collector busy 100 ms)
  320 ms    fast emits 9
  330 ms    fast emits 10
  410 ms  -> 9/cfg (collector busy 100 ms)
  510 ms  -> 10/cfg (collector busy 100 ms)
  610 ms  done
== C2 the same slow collector after conflate(): only the newest combination survives
   10 ms  -> 1/cfg
  110 ms  -> 10/cfg
== C3 the same slow collector with buffer(UNLIMITED): every combination is kept
 1010 ms  got 10: [1/cfg, 2/cfg, 3/cfg, 4/cfg, 5/cfg, 6/cfg, 7/cfg, 8/cfg, 9/cfg, 10/cfg]
== C4 docs zip example on its own
   15 ms  -> 1a
   30 ms  -> 2b
   45 ms  -> 3c
```

### D5. `buffer()` before `flatMapConcat`, `flatMapLatest` cleanup/join, docs examples, `merge`, `flatten*`
Uses `outer()`/`inner()` from D1.
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

fun main() {
    runTest {
        println("== buffer() before flatMapConcat: the outer runs ahead in its own coroutine")
        outer().buffer().flatMapConcat { inner(it) }.collect { log("  collector got $it") }
        log("done")
    }
    runTest {
        println("== flatMapLatest: previous inner's cleanup (50 ms, NonCancellable) finishes before the next inner starts")
        flow { emit("A"); delay(100); emit("B") }
            .flatMapLatest { q ->
                flow {
                    log("  inner $q starts")
                    try { delay(200); emit("$q-result") }
                    finally { withContext(NonCancellable) { delay(50); log("  inner $q cleanup done") } }
                }
            }.collect { log("  collector got $it") }
        log("done")
    }
    runTest {
        println("== docs examples: transformLatest / flatMapLatest / mapLatest on a(0) b(100)")
        val src = flow { emit("a"); delay(100); emit("b") }
        println("  transformLatest: " + src.transformLatest { v -> emit(v); delay(200); emit(v + "_last") }.toList())
        println("  flatMapLatest:   " + src.flatMapLatest { v -> flow { emit(v); delay(200); emit(v + "_last") } }.toList())
        println("  mapLatest:       " + src.mapLatest { v -> log("  Started computing $v"); delay(200); "Computed $v" }.toList())
    }
    runTest {
        println("== merge: card events every 100 ms (3), bank events every 70 ms (3)")
        val card = flow { repeat(3) { delay(100); emit("card-$it") } }.onCompletion { log("  card completed cause=$it") }
        val bank = flow { repeat(3) { delay(70); emit("bank-$it") } }.onCompletion { log("  bank completed cause=$it") }
        merge(card, bank).collect { log("  -> $it") }
        log("done")
    }
    runTest {
        println("== merge: bank fails at 150 ms; what happens to card?")
        val card = flow { repeat(3) { delay(100); emit("card-$it") } }
            .onCompletion { log("  card completed cause=${it?.let { c -> c::class.simpleName + ": " + c.message }}") }
        val bank = flow<String> { delay(150); throw IllegalStateException("bank feed down") }
        try { merge(card, bank).collect { log("  -> $it") } } catch (e: Exception) { log("collect threw $e") }
    }
    runTest {
        println("== flattenMerge / flattenConcat on Flow<Flow<T>>")
        val flows = flowOf(flow { delay(30); emit("x1"); delay(30); emit("x2") }, flow { delay(10); emit("y1"); delay(30); emit("y2") })
        println("  flattenConcat: " + flows.flattenConcat().toList() + " at " + now() + " ms")
        println("  flattenMerge:  " + flows.flattenMerge().toList() + " at " + now() + " ms (cumulative)")
    }
}
```
Output:
```
== buffer() before flatMapConcat: the outer runs ahead in its own coroutine
    0 ms  outer emits 1
   50 ms    collector got 1-a
  100 ms  outer emits 2
  200 ms    collector got 1-b
  200 ms  outer emits 3
  250 ms    collector got 2-a
  400 ms    collector got 2-b
  450 ms    collector got 3-a
  600 ms    collector got 3-b
  600 ms  done
== flatMapLatest: previous inner's cleanup (50 ms, NonCancellable) finishes before the next inner starts
    0 ms    inner A starts
  150 ms    inner A cleanup done
  150 ms    inner B starts
  350 ms    collector got B-result
  400 ms    inner B cleanup done
  400 ms  done
== docs examples: transformLatest / flatMapLatest / mapLatest on a(0) b(100)
  transformLatest: [a, b, b_last]
  flatMapLatest:   [a, b, b_last]
  600 ms    Started computing a
  700 ms    Started computing b
  mapLatest:       [Computed b]
== merge: card events every 100 ms (3), bank events every 70 ms (3)
   70 ms    -> bank-0
  100 ms    -> card-0
  140 ms    -> bank-1
  200 ms    -> card-1
  210 ms    bank completed cause=null
  210 ms    -> bank-2
  300 ms    card completed cause=null
  300 ms    -> card-2
  300 ms  done
== merge: bank fails at 150 ms; what happens to card?
  100 ms    -> card-0
  150 ms    card completed cause=JobCancellationException: Parent job is Cancelling
  150 ms  collect threw java.lang.IllegalStateException: bank feed down
== flattenMerge / flattenConcat on Flow<Flow<T>>
  flattenConcat: [x1, x2, y1, y2] at 100 ms
  flattenMerge:  [y1, x1, y2, x2] at 160 ms (cumulative)
```

### D10. How far does each operator run ahead of a slow collector?
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

fun main() {
    for ((name, op) in listOf<Pair<String, (Flow<Int>) -> Flow<Int>>>(
        "flatMapMerge (default buffer)" to { f -> f.flatMapMerge { n -> flow { emit(n) } } },
        "flatMapMerge + buffer(0)" to { f -> f.flatMapMerge { n -> flow { emit(n) } }.buffer(0) },
        "flatMapConcat (no channel)" to { f -> f.flatMapConcat { n -> flow { emit(n) } } },
    )) runTest {
        var produced = 0
        val src = (1..500).asFlow().onEach { produced++ }
        var first = true
        op(src).collect { if (first) { first = false; delay(1); println("$name: upstream items pulled before the collector finished its first item: $produced") } }
    }
}
```
Output:
```
flatMapMerge (default buffer): upstream items pulled before the collector finished its first item: 82
flatMapMerge + buffer(0): upstream items pulled before the collector finished its first item: 18
flatMapConcat (no channel): upstream items pulled before the collector finished its first item: 1
```

### D11. Reactor 3.8.8 comparison (VirtualTimeScheduler; classpath reactor-core 3.8.8, reactor-test 3.8.8, reactive-streams 1.0.4)
```kotlin
package rxdemo
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.test.scheduler.VirtualTimeScheduler
import java.time.Duration
import java.util.concurrent.TimeUnit

lateinit var vts: VirtualTimeScheduler
fun log(msg: String) = println("%5d ms  %s".format(vts.now(TimeUnit.MILLISECONDS), msg))
fun ms(n: Long) = Duration.ofMillis(n)

fun <T : Any> runVirtual(name: String, f: () -> Flux<T>) {
    vts = VirtualTimeScheduler.getOrSet(true)
    println("== $name")
    f().subscribe({ log("  -> $it") }, { log("  error $it") }, { log("done") })
    vts.advanceTimeBy(ms(10_000))
    VirtualTimeScheduler.reset()
}

fun outer(): Flux<Int> = Flux.concat(Mono.just(1), Mono.delay(ms(100)).thenReturn(2), Mono.delay(ms(100)).thenReturn(3))
    .doOnNext { log("outer emits $it") }
fun inner(n: Int): Flux<String> = Flux.concat(Mono.delay(ms(50)).thenReturn("$n-a"), Mono.delay(ms(150)).thenReturn("$n-b"))
    .doOnCancel { log("inner $n cancelled") }

var inFlight = 0; var maxInFlight = 0
fun main() {
    runVirtual("concatMap") { outer().doOnRequest { log("outer request($it)") }.concatMap { inner(it) } }
    runVirtual("flatMap") { outer().doOnRequest { log("outer request($it)") }.flatMap { inner(it) } }
    runVirtual("switchMap") { outer().switchMap { inner(it) } }
    runVirtual("flatMap default concurrency, 1000 inners of 100 ms") {
        Flux.range(1, 1000).flatMap { n ->
            Mono.delay(ms(100)).thenReturn(n)
                .doOnSubscribe { inFlight++; maxInFlight = maxOf(maxInFlight, inFlight) }
                .doOnTerminate { inFlight-- }
        }.count().flux().doOnNext { log("max in flight = $maxInFlight") }
    }
    runVirtual("combineLatest: interval(10ms).take(10) + just(cfg), consumer needs 100 ms per item") {
        Flux.combineLatest(Flux.interval(ms(10)).map { it + 1 }.take(10), Flux.just("cfg")) { i, c -> "$i/$c" }
            .concatMap({ v -> Mono.delay(ms(100)).thenReturn(v) }, 1)
    }
    runVirtual("combineLatest of two synchronous Flux.just") {
        Flux.combineLatest(Flux.just("a0", "a1", "a2"), Flux.just("b0", "b1", "b2")) { a, b -> a + b }
    }
}
```
Output:
```
== concatMap
    0 ms  outer request(1)
    0 ms  outer emits 1
   50 ms    -> 1-a
  200 ms    -> 1-b
  200 ms  outer request(1)
  200 ms  outer emits 2
  250 ms    -> 2-a
  400 ms    -> 2-b
  400 ms  outer request(1)
  400 ms  outer emits 3
  450 ms    -> 3-a
  600 ms    -> 3-b
  600 ms  done
== flatMap
    0 ms  outer request(256)
    0 ms  outer emits 1
   50 ms    -> 1-a
  100 ms  outer emits 2
  150 ms    -> 2-a
  200 ms    -> 1-b
  200 ms  outer request(1)
  200 ms  outer emits 3
  250 ms    -> 3-a
  300 ms    -> 2-b
  400 ms    -> 3-b
  400 ms  done
== switchMap
    0 ms  outer emits 1
   50 ms    -> 1-a
  100 ms  outer emits 2
  100 ms  inner 1 cancelled
  150 ms    -> 2-a
  200 ms  outer emits 3
  200 ms  inner 2 cancelled
  250 ms    -> 3-a
  400 ms    -> 3-b
  400 ms  done
== flatMap default concurrency, 1000 inners of 100 ms
  400 ms  max in flight = 256
  400 ms    -> 1000
  400 ms  done
== combineLatest: interval(10ms).take(10) + just(cfg), consumer needs 100 ms per item
  110 ms    -> 1/cfg
  210 ms    -> 2/cfg
  310 ms    -> 3/cfg
  410 ms    -> 4/cfg
  510 ms    -> 5/cfg
  610 ms    -> 6/cfg
  710 ms    -> 7/cfg
  810 ms    -> 8/cfg
  910 ms    -> 9/cfg
 1010 ms    -> 10/cfg
 1010 ms  done
== combineLatest of two synchronous Flux.just
    0 ms    -> a2b0
    0 ms    -> a2b1
    0 ms    -> a2b2
    0 ms  done
```
```kotlin
package rxdemo
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.test.scheduler.VirtualTimeScheduler
import java.time.Duration

fun main() {
    val v = VirtualTimeScheduler.getOrSet(true)
    Flux.never<Int>().timeout(Duration.ofMillis(100)).subscribe({}, { e -> println("Reactor timeout -> ${e::class.qualifiedName}: ${e.message}; is CancellationException=${e is java.util.concurrent.CancellationException}") })
    v.advanceTimeBy(Duration.ofMillis(200))
    var subs = 0
    Flux.defer { subs++; Flux.error<Int>(java.io.IOException("x")) }.retry(2).subscribe({}, { e -> println("Reactor retry(2) -> subscriptions=$subs, error=${e.message}") })
    VirtualTimeScheduler.reset()
}
```
Output:
```
Reactor timeout -> java.util.concurrent.TimeoutException: Did not observe any item or terminal signal within 100ms in 'source(FluxNever)' (and no fallback has been configured); is CancellationException=false
Reactor retry(2) -> subscriptions=3, error=x
```

### E1–E4. Exception transparency, `catch` placement, `onCompletion` causes, `take`
`desc()` is defined here and reused by later demos.
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

fun desc(t: Throwable?) = t?.let { "${it::class.qualifiedName}: ${it.message}" } ?: "null"

fun main() {
    runTest {
        println("== E1 exception transparency violated: try/catch around emit, then emit again")
        val bad = flow {
            try { emit(1) } catch (e: Exception) { println("  builder caught: ${desc(e)}"); emit(-1) }
        }
        try { bad.collect { v -> println("  collector got $v"); throw IllegalStateException("ledger write failed") } }
        catch (e: Exception) { println("  collect threw ${e::class.qualifiedName}:\n${e.message}") }
    }
    runTest {
        println("== E2 catch sees upstream only; collector exception passes through it")
        try {
            flowOf(1, 2, 3)
                .map { if (it == 2) throw IllegalArgumentException("bad amount $it") else it }
                .catch { e -> println("  catch saw ${desc(e)}"); emit(-1) }
                .collect { v -> println("  collector got $v") }
        } catch (e: Exception) { println("  caller saw ${desc(e)}") }
        try {
            flowOf(1, 2, 3)
                .catch { e -> println("  catch saw ${desc(e)} (never printed)") }
                .collect { v -> println("  collector got $v"); if (v == 2) throw IllegalStateException("save failed for $v") }
        } catch (e: Exception) { println("  caller saw ${desc(e)}") }
        println("  -- the fix: move the work into onEach above catch, then collect()")
        flowOf(1, 2, 3)
            .onEach { v -> println("  saving $v"); if (v == 2) throw IllegalStateException("save failed for $v") }
            .catch { e -> println("  catch saw ${desc(e)}") }
            .collect()
    }
    runTest {
        println("== E3 onCompletion cause in each ending")
        flowOf(1, 2).onCompletion { println("  success: cause=${desc(it)}") }.collect()
        try { flow<Int> { emit(1); throw java.io.IOException("provider reset") }.onCompletion { println("  upstream failure: cause=${desc(it)}") }.collect() } catch (e: Exception) {}
        try { flowOf(1, 2).onCompletion { println("  downstream failure: cause=${desc(it)}") }.collect { throw IllegalStateException("collector failed") } } catch (e: Exception) {}
        flowOf(1, 2, 3).onCompletion { println("  onCompletion ABOVE take(1): cause=${desc(it)}") }.take(1).onCompletion { println("  onCompletion BELOW take(1): cause=${desc(it)}") }.collect()
        flowOf(1, 2, 3).onCompletion { println("  above first(): cause=${desc(it)}") }.first()
        flowOf(1, 2).onCompletion { println("  caught later by catch: cause=${desc(it)}") }.map { throw IllegalStateException("map failed") }.catch { }.collect()
        val job = launch { flow { emit(1); awaitCancellation() }.onCompletion { println("  job cancelled: cause=${desc(it)}") }.collect() }
        delay(10); job.cancel()
        val job2 = launch { flow { emit(1); awaitCancellation() }.onCompletion { println("  job cancelled with reason: cause=${desc(it)}") }.collect() }
        delay(10); job2.cancel("user closed the page")
        println("  emit in onCompletion on success:")
        flowOf("a", "b").onCompletion { if (it == null) emit("Done") }.collect { println("    $it") }
        println("  emit in onCompletion after failure:")
        try { flow<String> { emit("a"); throw java.io.IOException("x") }.onCompletion { cause -> println("    cause=${desc(cause)}; trying emit"); emit("Done") }.collect { println("    $it") } }
        catch (e: Exception) { println("    caller saw ${desc(e)}") }
    }
    runTest {
        println("== E4 take(1): what does the upstream see?")
        flow {
            try { emit(1); emit(2) } catch (e: Throwable) { println("  upstream caught ${desc(e)}; is CancellationException=${e is CancellationException}"); throw e }
            finally { println("  upstream finally runs") }
        }.take(1).collect { println("  collector got $it") }
        println("  -- swallowing it and emitting again:")
        try {
            flow { try { emit(1) } catch (e: Throwable) { }; emit(2) }.take(1).collect { println("  collector got $it") }
        } catch (e: Exception) { println("  ${e::class.qualifiedName}: ${e.message}") }
    }
}
```
Output:
```
== E1 exception transparency violated: try/catch around emit, then emit again
  collector got 1
  builder caught: java.lang.IllegalStateException: ledger write failed
  collect threw java.lang.IllegalStateException:
Flow exception transparency is violated:
    Previous 'emit' call has thrown exception java.lang.IllegalStateException: ledger write failed, but then emission attempt of value '-1' has been detected.
    Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
    For a more detailed explanation, please refer to Flow documentation.
== E2 catch sees upstream only; collector exception passes through it
  collector got 1
  catch saw java.lang.IllegalArgumentException: bad amount 2
  collector got -1
  collector got 1
  collector got 2
  caller saw java.lang.IllegalStateException: save failed for 2
  -- the fix: move the work into onEach above catch, then collect()
  saving 1
  saving 2
  catch saw java.lang.IllegalStateException: save failed for 2
== E3 onCompletion cause in each ending
  success: cause=null
  upstream failure: cause=java.io.IOException: provider reset
  downstream failure: cause=java.lang.IllegalStateException: collector failed
  onCompletion ABOVE take(1): cause=kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  onCompletion BELOW take(1): cause=null
  above first(): cause=kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  caught later by catch: cause=java.lang.IllegalStateException: map failed
  job cancelled: cause=kotlinx.coroutines.JobCancellationException: StandaloneCoroutine was cancelled
  emit in onCompletion on success:
    a
    b
    Done
  emit in onCompletion after failure:
    a
    cause=java.io.IOException: x; trying emit
    caller saw java.io.IOException: x
  job cancelled with reason: cause=java.util.concurrent.CancellationException: user closed the page
== E4 take(1): what does the upstream see?
  collector got 1
  upstream caught kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed; is CancellationException=true
  upstream finally runs
  -- swallowing it and emitting again:
  collector got 1
  java.lang.IllegalStateException: Flow exception transparency is violated:
    Previous 'emit' call has thrown exception kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed, but then emission attempt of value '2' has been detected.
    Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
    For a more detailed explanation, please refer to Flow documentation.
```

### E5–E9. `catch` vs `CancellationException`, `retry` counting, backoff, `launchIn`, `timeout()`
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.io.IOException
import kotlin.time.Duration.Companion.milliseconds

fun main() {
    runTest {
        println("== E5 catch and CancellationException")
        val r1 = flow<Int> { emit(1); throw CancellationException("upstream gave up") }.catch { e -> println("  catch saw ${desc(e)}"); emit(-1) }.toList()
        println("  upstream-thrown CancellationException, job active -> catch handles it: $r1")
        val r2 = flow<Int> { emit(1); withTimeout(50) { delay(100) } }.catch { e -> println("  catch saw ${desc(e)}"); emit(-2) }.toList()
        println("  withTimeout inside upstream -> catch handles it: $r2")
        val job = launch {
            flow { emit(1); awaitCancellation() }
                .catch { e -> println("  catch saw ${desc(e)} (should NOT print)") }
                .onCompletion { println("  real cancellation passes catch; onCompletion cause=${desc(it)}") }
                .collect()
        }
        delay(10); job.cancel()
    }
    runTest {
        println("== E6 retry(2): attempts and what the collector sees")
        var calls = 0
        val r = flow { calls++; log("  attempt #$calls starts"); emit("p1"); emit("p2"); if (calls < 10) throw IOException("reset #$calls") }
            .retry(2)
            .catch { e -> log("  gave up: ${desc(e)}") ; emit("FALLBACK") }
            .toList()
        log("  collector saw $r (calls=$calls)")
        try { flowOf(1).retry(0).collect() } catch (e: Exception) { println("  retry(0): ${desc(e)}") }
    }
    runTest {
        println("== E7 retryWhen with exponential backoff (100, 200, 400 ms; max 3 retries; IOException only)")
        var n = 0
        val result = flow { n++; log("  call $n"); if (n <= 5) throw IOException("timeout from PSP (call $n)"); emit("ok") }
            .retryWhen { cause, attempt ->
                val retry = cause is IOException && attempt < 3
                val wait = 100L shl attempt.toInt()          // 100, 200, 400
                log("  retryWhen(cause=${cause.message}, attempt=$attempt) -> ${if (retry) "retry in $wait ms" else "give up"}")
                if (retry) delay(wait)
                retry
            }
            .catch { e -> log("  rethrown to catch: ${desc(e)}"); emit("fallback") }
            .single()
        log("  result=$result")
        println("  -- non-retryable error is rethrown at once:")
        try { flow<Int> { throw IllegalArgumentException("card declined") }.retryWhen { c, a -> log("  predicate called with attempt=$a"); c is IOException }.collect() }
        catch (e: Exception) { log("  caller saw ${desc(e)}") }
    }
    runTest {
        println("== E8 onEach + launchIn: where does an error go?")
        val handler = CoroutineExceptionHandler { _, e -> println("  handler got ${desc(e)}") }
        val scope = CoroutineScope(SupervisorJob() + handler + StandardTestDispatcher(testScheduler))
        val j1 = flowOf(1, 2, 3).onEach { if (it == 2) throw IllegalStateException("bad event $it") else println("  handled $it") }.launchIn(scope)
        val j2 = flowOf(1, 2, 3).onEach { if (it == 2) throw IllegalStateException("bad event $it") else println("  handled $it (with catch)") }
            .catch { e -> println("  catch below onEach saw ${desc(e)}") }.launchIn(scope)
        joinAll(j1, j2)
        println("  j1 cancelled=${j1.isCancelled}, j2 cancelled=${j2.isCancelled}, scope active=${scope.isActive}")
    }
    runTest {
        println("== E9 timeout() operator")
        val r = flow { emit(1); delay(100); emit(2); delay(100); emit(3); delay(1000); emit(4) }
            .timeout(100.milliseconds)
            .catch { e -> log("  caught ${desc(e)}"); if (e is TimeoutCancellationException) emit(-1) else throw e }
            .onEach { delay(300) }
            .toList()
        log("  docs example result: $r")
        try { flow { emit(1); delay(101); emit(2) }.timeout(100.milliseconds).collect { log("  got $it") } } catch (e: Exception) { log("  101 ms gap: ${desc(e)}") }
        try { flowOf(1).timeout(0.milliseconds).collect() } catch (e: Exception) { log("  zero: ${desc(e)}") }
        try { flow { delay(250); emit(1) }.timeout(java.time.Duration.ofMillis(200).toKotlinDurationCompat()).collect() } catch (e: Exception) { log("  first item late: ${desc(e)}") }
    }
}
fun java.time.Duration.toKotlinDurationCompat() = this.toMillis().milliseconds
```
Output (the E9 times are cumulative within one `runTest`):
```
== E5 catch and CancellationException
  catch saw java.util.concurrent.CancellationException: upstream gave up
  upstream-thrown CancellationException, job active -> catch handles it: [1, -1]
  catch saw kotlinx.coroutines.TimeoutCancellationException: Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time. To use the real time, wrap 'withTimeout' in 'withContext(Dispatchers.Default.limitedParallelism(1))'
  withTimeout inside upstream -> catch handles it: [1, -2]
  real cancellation passes catch; onCompletion cause=kotlinx.coroutines.JobCancellationException: StandaloneCoroutine was cancelled
== E6 retry(2): attempts and what the collector sees
    0 ms    attempt #1 starts
    0 ms    attempt #2 starts
    0 ms    attempt #3 starts
    0 ms    gave up: java.io.IOException: reset #3
    0 ms    collector saw [p1, p2, p1, p2, p1, p2, FALLBACK] (calls=3)
  retry(0): java.lang.IllegalArgumentException: Expected positive amount of retries, but had 0
== E7 retryWhen with exponential backoff (100, 200, 400 ms; max 3 retries; IOException only)
    0 ms    call 1
    0 ms    retryWhen(cause=timeout from PSP (call 1), attempt=0) -> retry in 100 ms
  100 ms    call 2
  100 ms    retryWhen(cause=timeout from PSP (call 2), attempt=1) -> retry in 200 ms
  300 ms    call 3
  300 ms    retryWhen(cause=timeout from PSP (call 3), attempt=2) -> retry in 400 ms
  700 ms    call 4
  700 ms    retryWhen(cause=timeout from PSP (call 4), attempt=3) -> give up
  700 ms    rethrown to catch: java.io.IOException: timeout from PSP (call 4)
  700 ms    result=fallback
  -- non-retryable error is rethrown at once:
  700 ms    predicate called with attempt=0
  700 ms    caller saw java.lang.IllegalArgumentException: card declined
== E8 onEach + launchIn: where does an error go?
  handled 1
  handler got java.lang.IllegalStateException: bad event 2
  handled 1 (with catch)
  catch below onEach saw java.lang.IllegalStateException: bad event 2
  j1 cancelled=true, j2 cancelled=false, scope active=true
== E9 timeout() operator
 1000 ms    caught kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 100ms
 1300 ms    docs example result: [1, 2, 3, -1]
 1300 ms    got 1
 1400 ms    101 ms gap: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 100ms
 1400 ms    zero: kotlinx.coroutines.TimeoutCancellationException: Timed out immediately
 1600 ms    first item late: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 200ms
```

### E10–E13. `withTimeout` (real time), the silent-timeout trap, terminal-operator messages, `onEmpty`
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import kotlin.time.Duration.Companion.milliseconds

suspend fun tryPrint(label: String, block: suspend () -> Any?) {
    try { println("  $label -> ${block()}") } catch (e: Throwable) { println("  $label -> throws ${desc(e)}") }
}

fun main() {
    println("== E10 withTimeout around collect (runBlocking, real time)")
    runBlocking {
        try { withTimeout(250) { flow { while (true) { delay(100); emit(1) } }.collect() } }
        catch (e: TimeoutCancellationException) { println("  ${desc(e)}") }
        try { withTimeout(250.milliseconds) { flow { while (true) { delay(100); emit(1) } }.collect() } }
        catch (e: TimeoutCancellationException) { println("  Duration overload: ${desc(e)}") }
        try { withContext(CoroutineName("settlement-import")) { withTimeout(50) { delay(100) } } }
        catch (e: TimeoutCancellationException) { println("  with CoroutineName: ${desc(e)}") }
        println("  withTimeoutOrNull: " + withTimeoutOrNull(250) { flow { repeat(5) { delay(100); emit(it) } }.toList() })
        val partial = mutableListOf<Int>()
        withTimeoutOrNull(250) { flow { repeat(5) { delay(100); emit(it) } }.collect { partial += it } }
        println("  values collected before the timeout: $partial")
    }
    println("== E11 a timeout that escapes a launch is a *cancellation*, not a failure")
    runBlocking {
        val handler = CoroutineExceptionHandler { _, e -> println("  handler got ${desc(e)}") }
        val scope = CoroutineScope(Job() + handler)
        val j = scope.launch { flow { delay(200); emit(1) }.timeout(50.milliseconds).collect { println("  got $it") } }
        j.join()
        println("  timeout(): job.isCancelled=${j.isCancelled}, scope.isActive=${scope.isActive} (no handler call above)")
        val j2 = scope.launch { withTimeout(50) { delay(200) } }
        j2.join()
        println("  withTimeout: job.isCancelled=${j2.isCancelled}, scope.isActive=${scope.isActive}")
        val j3 = scope.launch { flow<Int> { delay(10); throw java.io.IOException("real failure") }.collect() }
        j3.join()
        println("  IOException: job.isCancelled=${j3.isCancelled}, scope.isActive=${scope.isActive}")
    }
    runTest {
        println("== E12 terminal operators: results and exceptions")
        tryPrint("emptyFlow<Int>().first()") { emptyFlow<Int>().first() }
        tryPrint("flowOf(1,2).first { it > 5 }") { flowOf(1, 2).first { it > 5 } }
        tryPrint("emptyFlow<Int>().firstOrNull()") { emptyFlow<Int>().firstOrNull() }
        tryPrint("emptyFlow<Int>().single()") { emptyFlow<Int>().single() }
        tryPrint("flowOf(1,2).single()") { flowOf(1, 2).single() }
        tryPrint("flowOf(1,2).singleOrNull()") { flowOf(1, 2).singleOrNull() }
        tryPrint("emptyFlow<Int>().singleOrNull()") { emptyFlow<Int>().singleOrNull() }
        tryPrint("emptyFlow<Int>().last()") { emptyFlow<Int>().last() }
        tryPrint("emptyFlow<Int>().reduce { a, b -> a + b }") { emptyFlow<Int>().reduce { a, b -> a + b } }
        tryPrint("flowOf<Int?>(null).first()") { flowOf<Int?>(null).first() }
        tryPrint("flowOf<Int?>(null).firstOrNull()") { flowOf<Int?>(null).firstOrNull() }
        var produced = 0
        tryPrint("flow{1,2,3}.single() stops after the 2nd element") { flow { repeat(3) { produced++; emit(it) } }.single() }
        println("    elements produced: $produced")
        produced = 0
        tryPrint("flow{1,2,3}.first()") { flow { repeat(3) { produced++; emit(it) } }.first() }
        println("    elements produced: $produced")
    }
    runTest {
        println("== E13 onEmpty: default when a merchant has no fee schedule")
        fun feeRules(merchant: String): Flow<String> = if (merchant == "m1") flowOf("2.9% + 30c") else emptyFlow()
        for (m in listOf("m1", "m2")) println("  $m -> " + feeRules(m).onEmpty { emit("default 3.5%") }.toList())
    }
}
```
Output (E10 and E11 are real time):
```
== E10 withTimeout around collect (runBlocking, real time)
  kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms
  Duration overload: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms
  with CoroutineName: kotlinx.coroutines.TimeoutCancellationException: Coroutine "settlement-import" timed out waiting for 50 ms
  withTimeoutOrNull: null
  values collected before the timeout: [0, 1]
== E11 a timeout that escapes a launch is a *cancellation*, not a failure
  timeout(): job.isCancelled=true, scope.isActive=true (no handler call above)
  withTimeout: job.isCancelled=true, scope.isActive=true
  handler got java.io.IOException: real failure
  IOException: job.isCancelled=true, scope.isActive=false
== E12 terminal operators: results and exceptions
  emptyFlow<Int>().first() -> throws java.util.NoSuchElementException: Expected at least one element
  flowOf(1,2).first { it > 5 } -> throws java.util.NoSuchElementException: Expected at least one element matching the predicate
  emptyFlow<Int>().firstOrNull() -> null
  emptyFlow<Int>().single() -> throws java.util.NoSuchElementException: Flow is empty
  flowOf(1,2).single() -> throws java.lang.IllegalArgumentException: Flow has more than one element
  flowOf(1,2).singleOrNull() -> null
  emptyFlow<Int>().singleOrNull() -> null
  emptyFlow<Int>().last() -> throws java.util.NoSuchElementException: Expected at least one element
  emptyFlow<Int>().reduce { a, b -> a + b } -> throws java.util.NoSuchElementException: Empty flow can't be reduced
  flowOf<Int?>(null).first() -> null
  flowOf<Int?>(null).firstOrNull() -> null
  flow{1,2,3}.single() stops after the 2nd element -> throws java.lang.IllegalArgumentException: Flow has more than one element
    elements produced: 2
  flow{1,2,3}.first() -> 0
    elements produced: 1
== E13 onEmpty: default when a merchant has no fee schedule
  m1 -> [2.9% + 30c]
  m2 -> [default 3.5%]
```

### E14. Cancellation checks (real time)
```kotlin
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

fun main() = runBlocking {
    println("== E14 cancellation checks inside collect: flow{} vs asFlow() vs asFlow().cancellable()")
    for ((name, f) in listOf("flow { }" to flow { for (i in 1..5) emit(i) }, "asFlow()" to (1..5).asFlow(), "asFlow().cancellable()" to (1..5).asFlow().cancellable())) {
        val got = mutableListOf<Int>()
        val job = launch { f.collect { got += it; if (it == 3) cancel() } }
        job.join()
        println("  $name: collector received $got")
    }
}
```
Output:
```
== E14 cancellation checks inside collect: flow{} vs asFlow() vs asFlow().cancellable()
  flow { }: collector received [1, 2, 3]
  asFlow(): collector received [1, 2, 3, 4, 5]
  asFlow().cancellable(): collector received [1, 2, 3]
```

### T1–T6. `debounce`, `sample`, search-as-you-type, the timeout boundary
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import kotlin.time.Duration.Companion.milliseconds

// A user types a merchant name. Each pair is (time offset in ms from start, text in the box).
val keystrokes = listOf(0L to "a", 80L to "ac", 160L to "acm", 240L to "acme", 700L to "acme ", 760L to "acme p", 1300L to "acme pay")
fun typing(): Flow<String> = flow {
    var t = 0L
    for ((at, text) in keystrokes) { delay(at - t); t = at; log("key   '$text'"); emit(text) }
}
suspend fun searchMerchants(q: String): List<String> { delay(150); return listOf("${q.trim()}-merchant") }

fun main() {
    runTest {
        println("== T1 docs debounce example (1000 ms)")
        val r = flow { emit(1); delay(90); emit(2); delay(90); emit(3); delay(1010); emit(4); delay(1010); emit(5) }
            .debounce(1000).onEach { log("  -> $it") }.toList()
        log("  result $r")
    }
    runTest {
        println("== T2 docs sample example (200 ms)")
        val r = flow { repeat(10) { emit(it); delay(110) } }.sample(200).onEach { log("  -> $it") }.toList()
        log("  result $r")
    }
    runTest {
        println("== T3 search-as-you-type: debounce(300) + distinctUntilChanged + mapLatest(search 150 ms)")
        typing()
            .debounce(300)
            .map { it.trim() }
            .distinctUntilChanged()
            .onEach { log("  query '$it'") }
            .mapLatest { q -> searchMerchants(q) }
            .collect { log("  show $it") }
        log("done")
    }
    runTest {
        println("== T4 search-as-you-type without debounce: flatMapLatest cancels stale searches")
        typing()
            .flatMapLatest { q -> flow { emit(searchMerchants(q)) }.onCompletion { if (it != null) log("  search '$q' cancelled") } }
            .collect { log("  show $it") }
    }
    runTest {
        println("== T5 timeout boundary: gap exactly equal to the timeout, fast collector")
        try { flow { emit(1); delay(100); emit(2) }.timeout(100.milliseconds).collect { log("  got $it") }; log("  completed") }
        catch (e: Exception) { log("  ${desc(e)}") }
    }
    runTest {
        println("== T6 sample: last value at completion is dropped if it does not fit a window")
        val r = flow { emit("a"); delay(50); emit("b"); delay(10) }.sample(100).toList()
        log("  result $r (upstream completed at 60 ms, before the first 100 ms tick)")
    }
}
```
Output:
```
== T1 docs debounce example (1000 ms)
 1180 ms    -> 3
 2190 ms    -> 4
 2200 ms    -> 5
 2200 ms    result [3, 4, 5]
== T2 docs sample example (200 ms)
  200 ms    -> 1
  400 ms    -> 3
  600 ms    -> 5
  800 ms    -> 7
 1000 ms    -> 9
 1100 ms    result [1, 3, 5, 7, 9]
== T3 search-as-you-type: debounce(300) + distinctUntilChanged + mapLatest(search 150 ms)
    0 ms  key   'a'
   80 ms  key   'ac'
  160 ms  key   'acm'
  240 ms  key   'acme'
  540 ms    query 'acme'
  690 ms    show [acme-merchant]
  700 ms  key   'acme '
  760 ms  key   'acme p'
 1060 ms    query 'acme p'
 1210 ms    show [acme p-merchant]
 1300 ms  key   'acme pay'
 1300 ms    query 'acme pay'
 1450 ms    show [acme pay-merchant]
 1450 ms  done
== T4 search-as-you-type without debounce: flatMapLatest cancels stale searches
    0 ms  key   'a'
   80 ms  key   'ac'
   80 ms    search 'a' cancelled
  160 ms  key   'acm'
  160 ms    search 'ac' cancelled
  240 ms  key   'acme'
  240 ms    search 'acm' cancelled
  390 ms    show [acme-merchant]
  700 ms  key   'acme '
  760 ms  key   'acme p'
  760 ms    search 'acme ' cancelled
  910 ms    show [acme p-merchant]
 1300 ms  key   'acme pay'
 1450 ms    show [acme pay-merchant]
== T5 timeout boundary: gap exactly equal to the timeout, fast collector
    0 ms    got 1
  100 ms    got 2
  100 ms    completed
== T6 sample: last value at completion is dropped if it does not fit a window
   60 ms    result [] (upstream completed at 60 ms, before the first 100 ms tick)
```

### P1. Flaky provider: per-attempt timeout → retry with backoff → fallback
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.io.IOException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

data class Rate(val pair: String, val value: Double, val source: String)

/** A fake FX provider. `script` says what call n does: a latency in ms, or an exception to throw after 20 ms. */
class FakeProvider(private val name: String, private val script: (call: Int) -> Any) {
    var calls = 0
    fun rate(pair: String): Flow<Rate> = flow {
        val n = ++calls
        log("    $name call $n starts")
        when (val step = script(n)) {
            is Long -> { delay(step); emit(Rate(pair, 0.92, name)) }
            is Throwable -> { delay(20); log("    $name call $n throws ${step::class.simpleName}"); throw step }
            else -> error("bad script")
        }
    }
}

fun isTransient(e: Throwable) = e is IOException || e is TimeoutCancellationException

/** Retry transient failures with exponential backoff: first, first*2, first*4 ... capped at max. */
fun <T> Flow<T>.retryWithBackoff(
    maxRetries: Long = 3,
    first: Duration = 100.milliseconds,
    max: Duration = 1.seconds,
    retryOn: (Throwable) -> Boolean = ::isTransient,
): Flow<T> = retryWhen { cause, attempt ->
    if (attempt >= maxRetries || !retryOn(cause)) return@retryWhen false
    val wait = minOf(first * (1L shl attempt.toInt()).toDouble(), max)
    log("    retry #${attempt + 1} after ${cause::class.simpleName}, waiting $wait")
    delay(wait)
    true
}

fun fxRate(pair: String, primary: FakeProvider, fallback: FakeProvider): Flow<Rate> =
    primary.rate(pair)
        .timeout(300.milliseconds)                // per attempt: the provider must answer within 300 ms
        .retryWithBackoff()                       // 3 retries: wait 100, 200, 400 ms
        .catch { e ->                             // only reached once retries are exhausted or the error is not retryable
            if (!isTransient(e)) throw e
            log("    primary gave up (${e::class.simpleName}: ${e.message}); using fallback")
            emitAll(fallback.rate(pair))
        }

fun main() {
    val cases = listOf<Triple<String, (Int) -> Any, (Int) -> Any>>(
        Triple("A: two IOExceptions, then 50 ms success", { n -> if (n <= 2) IOException("connection reset") else 50L }, { 30L }),
        Triple("B: primary always too slow (1000 ms)", { 1000L }, { 30L }),
        Triple("C: non-retryable error (unsupported pair)", { IllegalArgumentException("unsupported pair XXX/EUR") }, { 30L }),
        Triple("D: primary down, fallback down too", { IOException("primary down") }, { IOException("fallback down") }),
    )
    for ((name, p, f) in cases) runTest {
        println("== $name")
        val primary = FakeProvider("primary", p); val fallback = FakeProvider("fallback", f)
        try { val r = fxRate("USD/EUR", primary, fallback).single(); log("  result $r") }
        catch (e: Exception) { log("  caller saw ${desc(e)}") }
        println("  calls: primary=${primary.calls}, fallback=${fallback.calls}")
    }
    runTest {
        println("== E: overall budget: per-attempt timeout(300) + retries, then timeout(1s) on the whole thing")
        val primary = FakeProvider("primary") { 1000L }; val fallback = FakeProvider("fallback") { 30L }
        val r = primary.rate("USD/EUR").timeout(300.milliseconds).retryWithBackoff().timeout(1.seconds)
            .catch { e -> log("    catch saw ${desc(e)}"); emitAll(fallback.rate("USD/EUR")) }
            .single()
        log("  result $r; calls: primary=${primary.calls}, fallback=${fallback.calls}")
    }
    runTest {
        println("== F: a streaming source that fails midway: retry replays what was already delivered")
        var attempt = 0
        val delivered = flow { attempt++; for (i in 1..3) { delay(10); if (attempt == 1 && i == 3) throw IOException("stream reset"); emit("payment-$i") } }
            .retryWithBackoff()
            .toList()
        log("  collector received $delivered")
    }
}
```
Output:
```
== A: two IOExceptions, then 50 ms success
    0 ms      primary call 1 starts
   20 ms      primary call 1 throws IOException
   20 ms      retry #1 after IOException, waiting 100ms
  120 ms      primary call 2 starts
  140 ms      primary call 2 throws IOException
  140 ms      retry #2 after IOException, waiting 200ms
  340 ms      primary call 3 starts
  390 ms    result Rate(pair=USD/EUR, value=0.92, source=primary)
  calls: primary=3, fallback=0
== B: primary always too slow (1000 ms)
    0 ms      primary call 1 starts
  300 ms      retry #1 after TimeoutCancellationException, waiting 100ms
  400 ms      primary call 2 starts
  700 ms      retry #2 after TimeoutCancellationException, waiting 200ms
  900 ms      primary call 3 starts
 1200 ms      retry #3 after TimeoutCancellationException, waiting 400ms
 1600 ms      primary call 4 starts
 1900 ms      primary gave up (TimeoutCancellationException: Timed out waiting for 300ms); using fallback
 1900 ms      fallback call 1 starts
 1930 ms    result Rate(pair=USD/EUR, value=0.92, source=fallback)
  calls: primary=4, fallback=1
== C: non-retryable error (unsupported pair)
    0 ms      primary call 1 starts
   20 ms      primary call 1 throws IllegalArgumentException
   20 ms    caller saw java.lang.IllegalArgumentException: unsupported pair XXX/EUR
  calls: primary=1, fallback=0
== D: primary down, fallback down too
    0 ms      primary call 1 starts
   20 ms      primary call 1 throws IOException
   20 ms      retry #1 after IOException, waiting 100ms
  120 ms      primary call 2 starts
  140 ms      primary call 2 throws IOException
  140 ms      retry #2 after IOException, waiting 200ms
  340 ms      primary call 3 starts
  360 ms      primary call 3 throws IOException
  360 ms      retry #3 after IOException, waiting 400ms
  760 ms      primary call 4 starts
  780 ms      primary call 4 throws IOException
  780 ms      primary gave up (IOException: primary down); using fallback
  780 ms      fallback call 1 starts
  800 ms      fallback call 1 throws IOException
  800 ms    caller saw java.io.IOException: fallback down
  calls: primary=4, fallback=1
== E: overall budget: per-attempt timeout(300) + retries, then timeout(1s) on the whole thing
    0 ms      primary call 1 starts
  300 ms      retry #1 after TimeoutCancellationException, waiting 100ms
  400 ms      primary call 2 starts
  700 ms      retry #2 after TimeoutCancellationException, waiting 200ms
  900 ms      primary call 3 starts
 1000 ms      catch saw kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 1s
 1000 ms      fallback call 1 starts
 1030 ms    result Rate(pair=USD/EUR, value=0.92, source=fallback); calls: primary=3, fallback=1
== F: a streaming source that fails midway: retry replays what was already delivered
   30 ms      retry #1 after IOException, waiting 100ms
  160 ms    collector received [payment-1, payment-2, payment-1, payment-2, payment-3]
```

### X1–X6. Suppression, fallback failure, `flatMapMerge` failure isolation, `zip`/`combine` failure, `catch` position
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import java.io.IOException

fun main() {
    runTest {
        println("== X1 downstream fails, then upstream's finally throws too: who wins?")
        try {
            flow { try { emit(1) } finally { throw IOException("close() failed") } }
                .catch { e -> println("  catch action saw ${desc(e)} (not expected)") }
                .collect { throw IllegalStateException("collector failed") }
        } catch (e: Exception) { println("  caller saw ${desc(e)}; suppressed=${e.suppressed.map { desc(it) }}") }
    }
    runTest {
        println("== X2 fallback failure: is the primary error kept?")
        try { flow<Int> { throw IOException("primary down") }.catch { emitAll(flow { throw IOException("fallback down") }) }.collect() }
        catch (e: Exception) { println("  caller saw ${desc(e)}; suppressed=${e.suppressed.map { desc(it) }}; cause=${desc(e.cause)}") }
    }
    runTest {
        println("== X3 flatMapMerge: one inner fails")
        val merchants = listOf("m1" to 300L, "m2" to 100L, "m3" to 200L)
        try {
            merchants.asFlow().flatMapMerge { (m, ms) ->
                flow { delay(ms); if (m == "m2") throw IOException("fee service 503 for $m"); emit("$m:fee") }
                    .onCompletion { c -> if (c != null) log("  inner $m ended: ${c::class.simpleName}") }
            }.collect { log("  -> $it") }
        } catch (e: Exception) { log("  caller saw ${desc(e)}") }
        println("  -- isolate failures by catching inside each inner flow:")
        merchants.asFlow().flatMapMerge { (m, ms) ->
            flow { delay(ms); if (m == "m2") throw IOException("fee service 503 for $m"); emit("$m:fee") }
                .catch { emit("$m:DEFAULT") }
        }.collect { log("  -> $it") }
    }
    runTest {
        println("== X4 zip when the receiver (left) is the shorter one")
        flowOf(1, 2).zip(flow { var i = 0; while (true) { delay(10); emit("r${i++}") } }.onCompletion { println("  right side ended: ${desc(it)}") }) { a, b -> "$a$b" }
            .collect { log("  -> $it") }
    }
    runTest {
        println("== X5 combine: one source fails")
        try {
            combine(flow { repeat(5) { delay(100); emit(it) } }.onCompletion { log("  prices ended: ${desc(it)}") },
                    flow<Double> { emit(0.92); delay(250); throw IOException("fx feed lost") }) { p, fx -> "$p@$fx" }
                .collect { log("  -> $it") }
        } catch (e: Exception) { log("  caller saw ${desc(e)}") }
    }
    runTest {
        println("== X6 catch position")
        val src = flow { emit(1); emit(2) }
        println("  catch BEFORE map: " + runCatching { src.catch { emit(-1) }.map { if (it == 2) throw IOException("map failed") else it }.toList() }.fold({ "$it" }, { "throws ${desc(it)}" }))
        println("  catch AFTER map:  " + runCatching { src.map { if (it == 2) throw IOException("map failed") else it }.catch { emit(-1) }.toList() }.fold({ "$it" }, { "throws ${desc(it)}" }))
    }
}
```
Output:
```
== X1 downstream fails, then upstream's finally throws too: who wins?
  caller saw java.io.IOException: close() failed; suppressed=[java.lang.IllegalStateException: collector failed]
== X2 fallback failure: is the primary error kept?
  caller saw java.io.IOException: fallback down; suppressed=[]; cause=null
== X3 flatMapMerge: one inner fails
  100 ms    inner m2 ended: IOException
  100 ms    inner m1 ended: JobCancellationException
  100 ms    inner m3 ended: JobCancellationException
  100 ms    caller saw java.io.IOException: fee service 503 for m2
  -- isolate failures by catching inside each inner flow:
  200 ms    -> m2:DEFAULT
  300 ms    -> m3:fee
  400 ms    -> m1:fee
== X4 zip when the receiver (left) is the shorter one
   10 ms    -> 1r0
   20 ms    -> 2r1
  right side ended: kotlinx.coroutines.JobCancellationException: ProducerCoroutine was cancelled
== X5 combine: one source fails
  100 ms    -> 0@0.92
  200 ms    -> 1@0.92
  250 ms    prices ended: kotlinx.coroutines.JobCancellationException: Parent job is Cancelling
  250 ms    caller saw java.io.IOException: fx feed lost
== X6 catch position
  catch BEFORE map: throws java.io.IOException: map failed
  catch AFTER map:  [1, -1]
```

### W1–W2. What `onCompletion` sees under `withTimeout` and `timeout()` (real time)
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlin.time.Duration.Companion.milliseconds

fun ticks() = flow { var i = 0; while (true) { delay(100); emit(i++) } }

fun main() = runBlocking {
    println("== W1 withTimeout(250) around collect: what does onCompletion see?")
    try { withTimeout(250) { ticks().onCompletion { println("  onCompletion cause=${desc(it)}") }.collect() } }
    catch (e: TimeoutCancellationException) { println("  caller: ${desc(e)}") }
    println("== W2 timeout(250ms) operator: upstream onCompletion (above) and downstream onCompletion (below)")
    try {
        flow { emit(0); delay(1000); emit(1) }.onCompletion { println("  above timeout: cause=${desc(it)}") }
            .timeout(250.milliseconds).onCompletion { println("  below timeout: cause=${desc(it)}") }.collect()
    } catch (e: TimeoutCancellationException) { println("  caller: ${desc(e)}") }
}
```
Output:
```
== W1 withTimeout(250) around collect: what does onCompletion see?
  onCompletion cause=kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms
  caller: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250 ms
== W2 timeout(250ms) operator: upstream onCompletion (above) and downstream onCompletion (below)
  above timeout: cause=kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250ms
  below timeout: cause=kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250ms
  caller: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 250ms
```

### X7–X8. Order-preserving concurrent map; turning a timeout into a real failure
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import kotlin.time.Duration.Companion.milliseconds

/** Order-preserving concurrent map: up to `concurrency` calls in flight, results in input order. */
fun <T, R> Flow<T>.mapConcurrentOrdered(concurrency: Int, f: suspend (T) -> R): Flow<R> = flow {
    coroutineScope {
        this@mapConcurrentOrdered
            .map { value -> async { f(value) } }
            .buffer(concurrency - 2)          // the buffer's channel + one Deferred being awaited + one being created
            .collect { emit(it.await()) }
    }
}

class ProviderTimeout(cause: Throwable) : Exception("FX provider timed out", cause)

fun main() {
    runTest {
        println("== X7 mapConcurrentOrdered(3) over latencies m1=300 m2=100 m3=200 m4=50 m5=150")
        var inFlight = 0; var max = 0
        val lat = listOf("m1" to 300L, "m2" to 100L, "m3" to 200L, "m4" to 50L, "m5" to 150L)
        lat.asFlow().mapConcurrentOrdered(3) { (m, ms) -> inFlight++; max = maxOf(max, inFlight); log("  start $m"); delay(ms); inFlight--; "$m:fee" }
            .collect { log("-> $it") }
        log("done, max in flight = $max")
    }
    runBlocking {
        println("== X8 turning a timeout into a real failure so the parent hears about it")
        val handler = CoroutineExceptionHandler { _, e -> println("  handler got ${desc(e)}; cause=${desc(e.cause)}") }
        val scope = CoroutineScope(Job() + handler)
        val j = scope.launch {
            flow { delay(200); emit(1) }.timeout(50.milliseconds)
                .catch { e -> if (e is TimeoutCancellationException) throw ProviderTimeout(e) else throw e }
                .collect()
        }
        j.join()
        println("  scope.isActive=${scope.isActive}")
    }
}
```
Output (X8 is real time):
```
== X7 mapConcurrentOrdered(3) over latencies m1=300 m2=100 m3=200 m4=50 m5=150
    0 ms    start m1
    0 ms    start m2
    0 ms    start m3
  300 ms  -> m1:fee
  300 ms  -> m2:fee
  300 ms  -> m3:fee
  300 ms    start m4
  300 ms    start m5
  350 ms  -> m4:fee
  450 ms  -> m5:fee
  450 ms  done, max in flight = 3
== X8 turning a timeout into a real failure so the parent hears about it
  handler got demo.ProviderTimeout: FX provider timed out; cause=kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 50ms
  scope.isActive=false
```
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

fun main() {
    for (c in listOf(2, 3, 4, 8)) runTest {
        var inFlight = 0; var max = 0
        val out = (1..20).asFlow().mapConcurrentOrdered(c) { n -> inFlight++; max = maxOf(max, inFlight); delay(100); inFlight--; n }.toList()
        println("concurrency=$c: in order=${out == (1..20).toList()}, max in flight=$max, total=${now()} ms")
    }
}
```
Output:
```
concurrency=2: in order=true, max in flight=2, total=1000 ms
concurrency=3: in order=true, max in flight=3, total=700 ms
concurrency=4: in order=true, max in flight=4, total=500 ms
concurrency=8: in order=true, max in flight=8, total=300 ms
```

### L1. A deterministic lab-test pattern (virtual time, exact timestamps)
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)
package demo
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*

// Pattern for deterministic lab tests: record (virtual time, value) pairs and compare to an exact list.
fun main() = runTest {
    val keys = MutableSharedFlow<String>()
    val seen = mutableListOf<Pair<Long, String>>()
    backgroundScope.launch {
        keys.debounce(300).mapLatest { q -> delay(150); "result($q)" }.collect { seen += currentTime to it }
    }
    runCurrent()                          // let the collector subscribe before emitting
    keys.emit("a"); advanceTimeBy(100); keys.emit("ac"); advanceTimeBy(100); keys.emit("acme")
    advanceTimeBy(449); runCurrent()
    check(seen.isEmpty()) { "too early: $seen" }
    println("at ${currentTime} ms: nothing yet")
    advanceTimeBy(1); runCurrent()
    println("at ${currentTime} ms: $seen")
    check(seen == listOf(650L to "result(acme)"))
    println("lab check passed")
}
```
Output:
```
at 649 ms: nothing yet
at 650 ms: [(650, result(acme))]
lab check passed
```
Note: `advanceTimeBy(n)` does **not** run tasks scheduled exactly at `currentTime + n`, so call `runCurrent()` after it [Source: `kotlinx-coroutines-test/common/src/TestScope.kt` KDoc + Local: nothing at 649, result at 650].

---

## Exercise ideas (testable, deterministic with virtual time)

Write all labs with `runTest`. Record `(currentTime, value)` pairs (or `testScheduler.currentTime` inside the flow), then assert on exact lists. Inject the dispatcher where production code creates its own scope: `StandardTestDispatcher(testScheduler)` is stable. `currentTime`, `advanceTimeBy` and `runCurrent` need `@OptIn(ExperimentalCoroutinesApi::class)`. The default `runTest` timeout is 60 s of real time [Source: `TestBuilders.kt` KDoc + `CHANGES.md` (#3800)].

1. **Fee fan-out under a contract.** Implement `fun fees(ids: Flow<MerchantId>): Flow<Fee>` so that 10 lookups of 100 ms with `concurrency = 4` finish at exactly **300 ms** of virtual time with max in-flight ≤ 4. Ship a buggy version that calls `lookup` in the transform lambda. Tests expect 300 ms and 4; the bug gives 1000 ms and 1 (basis: D2's 450 vs 800 ms).
2. **Ordered fan-out (no `flatMapSequential`).** Implement `mapConcurrentOrdered(n, f)`. Tests: input order preserved; max in flight == n; 20 × 100 ms → 1000/700/500/300 ms for n = 2/3/4/8 (D-X7, verified). Stretch: explain why m4 waits for m1 (head-of-line), and why `n = 1` must be rejected (`buffer(-1)` would be `CONFLATED`) [the last point is inference from `Channel.CONFLATED = -1`; not run].
3. **Fail one, keep the rest.** Five merchants, one throws `IOException`. Version A (`catch` after `flatMapMerge`): the test expects the caller to get the `IOException` at 100 ms and the others' `onCompletion` to report `JobCancellationException`. Version B (`catch` inside each inner): the test expects `[m2:DEFAULT@200, m3:fee@300, m1:fee@400]` (X3).
4. **Merchant search box.** `MutableSharedFlow<String>` keys → `debounce(300)` → `trim` → `distinctUntilChanged` → `mapLatest(search 150 ms)`. The test emits at 0/100/200 and asserts exactly one result at **650 ms** (the L1 pattern). Variant: typing "acme" then "acme " must not search twice (`distinctUntilChanged` after `trim`).
5. **FX × price.** Build `combine(prices, fx)`. Test 1: the first emission is at the FX arrival time and uses the latest price (D4: `1010@0.92` at 250). Test 2: with a 100 ms collector, assert the skipped values (`1,3,5,7,9,10`). Then make it lossless with `buffer()` (10 values) or newest-only with `conflate()` (`1, 10`) and assert again (C1–C3). Contrast with `zip` (D4: two pairs, and prices slowed).
6. **Exception transparency bug hunt.** Given a `flow { try { emit(x) } catch (e: Exception) { emit(errorEvent) } }`, the test expects `IllegalStateException` whose message starts with `Flow exception transparency is violated`. Fix it with `.catch { emit(errorEvent) }` and assert that the collector's failure now reaches the caller unchanged (E1, E2).
7. **Completion metrics.** Write `Flow<T>.recordOutcome(metrics)` using `onCompletion` that classifies success / failure / cancelled / aborted-by-downstream. Tests cover the 6.4 table rows: `null`, `IOException`, `JobCancellationException`, `AbortFlowException` above `first()`. A naive "non-null cause = error" version must fail the `first()` test.
8. **Backoff schedule.** Implement `retryWithBackoff(max = 3, first = 100.ms, cap = 1.s, retryOn)`. Tests: call times are **[0, 100, 300, 700]** for zero-latency failures (E7). A non-retryable exception gives exactly 1 call. `TimeoutCancellationException` from an upstream `timeout()` is retried (P1 case B: calls at 0, 400, 900, 1600; fallback at 1900).
9. **Flaky provider end to end.** Cases A–E of P1 as five tests with exact virtual timestamps (390, 1930, 20, 800, 1030 ms) and call counts.
10. **Retry is a replay.** A payment stream fails after 2 of 3 items. The test asserts the duplicate sequence `[p1, p2, p1, p2, p3]` (P1 case F), then the learner adds idempotency (de-dupe by payment id, or resume from a cursor), and the test asserts `[p1, p2, p3]`.
11. **The silent timeout.** A `launchIn(scope)` collector with `timeout(50.ms)` inside a `Job() + CoroutineExceptionHandler` scope. Test 1: the handler is **not** called and the scope stays active (E11). The fix translates it into `ProviderTimeout` in `catch`. Test 2: the handler gets `ProviderTimeout` with the `TimeoutCancellationException` as its cause (X8). Use `StandardTestDispatcher(testScheduler)` in the scope so it runs on virtual time (adapting X8, which used real time; the virtual-time version was not run).
12. **Terminal-operator contract.** A table-driven test of the 6.10 table (exception class + message). Then a quiz: "how many elements does the upstream produce before `single()` fails on a 3-element flow?" (2), and before `first()`? (1).

---

## Verified URLs

**Fetched in this session (HTTP 200; content read or checked):**
- https://kotlinlang.org/docs/coroutines-flow.html: the rewritten "Flows" page (last modified 13 July 2026). Exceptions in flows, `catch`, `onEach` before `catch`, `retry`/`retryWhen`, flow cancellation, `myTake` throwing `CancellationException`, "rethrow it. This preserves exception transparency"
- https://kotlinlang.org/docs/flow.html: **meta-refresh stub** to `coroutines-flow.html` (title "You will be redirected shortly"). co-07 and rx-03 cite this URL. It still "loads", but the target page has no flattening, `zip`/`combine`, `onCompletion`-operator or `cancellable()` material any more (searched: "flatMapConcat", "flatMapMerge", "Zip", "Combine", "cancellable" not found; `onCompletion` appears only as a parameter name in a custom example)
- https://kotlinlang.org/docs/exception-handling.html: "Coroutines internally use CancellationException for cancellation, these exceptions are ignored by all handlers"
- https://kotlinlang.org/docs/cancellation-and-timeouts.html: redirect stub → https://kotlinlang.org/docs/coroutines-cancellation.html (fetched: `withTimeoutOrNull` section, CancellationException rules)
- API reference (header shows 1.11.0), base https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/ : `flat-map-concat.html` (read), `flat-map-merge.html` (text read), `flat-map-latest.html` (read), `flatten-concat.html`, `flatten-merge.html` (read), `merge.html` (read), `zip.html` (read), `combine.html` (read), `combine-transform.html`, `transform-latest.html` (read), `map-latest.html` (read), `-d-e-f-a-u-l-t_-c-o-n-c-u-r-r-e-n-c-y.html` (read), `-d-e-f-a-u-l-t_-c-o-n-c-u-r-r-e-n-c-y_-p-r-o-p-e-r-t-y_-n-a-m-e.html`, `catch.html` (read; newer KDoc wording), `on-completion.html` (read), `retry.html` (read), `retry-when.html` (read), `on-each.html`, `launch-in.html` (read), `timeout.html` (read), `debounce.html` (read), `sample.html` (read), `on-empty.html`, `first.html`, `first-or-null.html`, `single.html` (read), `single-or-null.html`, `take.html`, `collect-latest.html`, `cancellable.html`, `buffer.html`. A bogus page under the same base returned 404, so these 200s are real.
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout.html (read), https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-timeout-cancellation-exception/ (read), https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-flow-preview/, https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-experimental-coroutines-api/
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html, https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/current-time.html
- Library source at tag 1.11.0 (all read), base https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/ : `common/src/flow/operators/Merge.kt`, `common/src/flow/internal/Merge.kt`, `common/src/flow/operators/Zip.kt`, `common/src/flow/internal/Combine.kt`, `common/src/flow/operators/Errors.kt`, `common/src/flow/operators/Emitters.kt`, `common/src/flow/operators/Delay.kt`, `common/src/flow/operators/Limit.kt`, `common/src/flow/operators/Transform.kt`, `common/src/flow/terminal/Reduce.kt`, `common/src/flow/terminal/Collect.kt`, `common/src/flow/internal/FlowExceptions.common.kt`, `jvm/src/flow/internal/FlowExceptions.kt`, `common/src/flow/internal/SafeCollector.common.kt`, `jvm/src/flow/internal/SafeCollector.kt`, `common/src/flow/Flow.kt`, `common/src/flow/Builders.kt`, `common/src/flow/internal/ChannelFlow.kt`, `common/src/flow/internal/FlowCoroutine.kt`, `common/src/Timeout.kt`, `common/src/channels/Channel.kt`
- https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-test/common/src/TestDispatcher.kt, `…/TestScope.kt`, `…/TestBuilders.kt`
- https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/CHANGES.md
- Reactor source at tag v3.8.8: https://raw.githubusercontent.com/reactor/reactor-core/v3.8.8/reactor-core/src/main/java/reactor/util/concurrent/Queues.java and https://raw.githubusercontent.com/reactor/reactor-core/v3.8.8/reactor-core/src/main/java/reactor/core/publisher/Flux.java

**Blocked in this session (HTTP 403 from the session proxy); same paths as the raw URLs above, so they should work for learners. Re-check before publishing:**
- https://github.com/Kotlin/kotlinx.coroutines/blob/1.11.0/kotlinx-coroutines-core/common/src/flow/operators/Merge.kt (and every other `github.com/.../blob/1.11.0/...` path listed above)
- https://github.com/Kotlin/kotlinx.coroutines/releases/tag/1.11.0
- https://github.com/reactor/reactor-core/blob/v3.8.8/reactor-core/src/main/java/reactor/core/publisher/Flux.java

**Local jars used (Gradle cache `~/.gradle/caches/modules-2/files-2.1/`):** `kotlin-compiler-embeddable-2.4.21`, `kotlin-stdlib-2.4.21`, `kotlinx-coroutines-core-jvm-1.11.0`, `kotlinx-coroutines-test-jvm-1.11.0`, `reactor-core-3.8.8`, `reactor-test-3.8.8`, `reactive-streams-1.0.4`.

---

## Notes for the lesson writer

- **Version anchors to state.** kotlinx.coroutines **1.11.0** (tag `1.11.0`) and Kotlin **2.4.21**. No operator in these two lessons changed in 1.11.0. `Flow.timeout` dates from 1.7.0 (`@FlowPreview`). The virtual-time `withTimeout` message dates from 1.7.0. The `runTest` default timeout has been 60 s since 1.8.0 (#3800) [Source: `CHANGES.md`].
- **Opt-ins for the lesson code.** Lesson 5 snippets need `@OptIn(ExperimentalCoroutinesApi::class)` for every `flatMap*`/`flatten*`/`*Latest`, and `@OptIn(FlowPreview::class)` for `DEFAULT_CONCURRENCY`. Lesson 6 snippets need `@OptIn(FlowPreview::class)` for `timeout`, `debounce` and `sample`. Lab tests also need `ExperimentalCoroutinesApi` for `currentTime`/`advanceTimeBy`/`runCurrent`. Say clearly that without them you get a **warning**, not a compile error.
- **Don't cite `https://kotlinlang.org/docs/flow.html` for flattening/zip/combine.** It is now a redirect to the rewritten `coroutines-flow.html`, which doesn't cover those operators. Use the API reference pages listed above. Existing lessons co-07 and rx-03 still link `flow.html`. That works as a link, but the content they describe has moved or been removed; this is outside my scope to change.
- **Claims in earlier lessons that I re-checked.** rx-03 says "`flatMapMerge(concurrency = 4)`, whose default is 16 rather than Reactor's 256" and that 1.11 "still need[s] `@OptIn(ExperimentalCoroutinesApi::class)`": both correct (warning-level). co-07 says a re-emit after catching throws "Flow exception transparency is violated": correct, full text in 6.1.
- **Marble diagrams.** D1 (flatMap trio), D4/C1 (combine/zip) and T1–T4 (debounce/sample/search) print one line per event with a virtual-ms timestamp. Lines that share a timestamp appear in the order the scheduler ran them, which is not always the "logical" order. Example: in the merge demo `bank completed` prints before `-> bank-2` at 210 ms, because the inner completes after its send into the channel. Draw marbles by timestamp, and treat same-time ordering as incidental.
- **Wording to get right.**
  - "`retry(3)` = 3 retries = 4 attempts."
  - "`catch` ignores the cancellation of the collector, not every `CancellationException`."
  - "`timeout()` throws a `TimeoutCancellationException`, which is a `CancellationException`."
  - "`combine` may skip intermediate values when the collector is slow." Don't say "always conflates": it backpressures *and* skips (C1).
  - "`zip` pairs by index; the receiver side is not buffered."
- **Payments framing that works.**
  - Fee lookups: `flatMapMerge` with a cap that matches the provider's contract, plus `catch` per inner for defaults.
  - Merchant search: `debounce` + `distinctUntilChanged` + `mapLatest`.
  - FX conversion: `combine(rates, prices)`, never `zip`.
  - Provider calls: per-attempt `timeout` → `retryWhen` backoff → `catch` + fallback, with an overall `timeout` as the budget.
  - Streaming retries need idempotency, because retry replays.
- **What I did not verify.**
  - Reactor-side cleanup timing for `switchMap`.
  - The `combine` behaviour when a source throws a bare `CancellationException` (from source only).
  - The exact revision of KDoc behind the kotlinlang API site, whose `catch` page wording is newer than the 1.11.0 tag.
  - Whether `System.setProperty("kotlinx.coroutines.flow.defaultConcurrency", …)` at runtime before first use takes effect (it should, as the property is read at class init, but I only tested `-D`).
  - JDK 25 runs (everything ran on JDK 21.0.12.1; nothing here should depend on the JDK).
  - Exercise 11's virtual-time variant (X8 was run in real time).
- **Demo hygiene.** The demos use `runTest` as the clock. In the course's Gradle demo source set that means adding `kotlinx-coroutines-test` to the demo classpath, or switching the demos to `runBlocking` and printing rounded real time like the rx demos do ("about 120 to 140 ms").
