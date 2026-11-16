# Kotlin Flow in depth, lessons 1 to 4: what the library really does (kotlinx.coroutines 1.11.0, Kotlin 2.4.21)

Scope: the first four lessons of the "Kotlin Flow in depth" track. (1) A flow from scratch: the two interfaces, a toy flow, cold, sequential, the call stack. (2) What `flow { }` adds: `SafeFlow`, `AbstractFlow`, `SafeCollector`, the three runtime checks, how the library writes `map`/`filter`/`take`/`first`, and which builders are cancellable. (3) Context: why `withContext` around `emit` is forbidden, what `flowOn` builds, `channelFlow`, `produceIn`. (4) Buffering: timing, `buffer`, `conflate`, `collectLatest`/`mapLatest`, operator fusion, and a verified mapping to Reactor's backpressure operators.

The learner already did co-07 (cold flows, operators, `flowOn` vs `withContext`, `catch`/`onCompletion`), co-08 (StateFlow/SharedFlow) and co-09 (channels, `callbackFlow`, a buffer/conflate/collectLatest table). These notes go one level down and avoid re-teaching those surfaces.

**Summary.** A `Flow` is one suspend method, `collect(collector)`, and a `FlowCollector` is one suspend method, `emit(value)`. In 1.11.0 `FlowCollector` is a `fun interface` and `Flow` is **not**. Collecting a flow is a plain nested function call: the collector's lambda runs *inside* `emit`, on the same thread and stack (printed below), which is why emission is sequential and why backpressure needs no protocol. `flow { }` is `SafeFlow`, an `AbstractFlow` that wraps your collector in a `SafeCollector`, which on every `emit` checks cancellation (`ensureActive`), context identity ("Flow invariant is violated"), and exception transparency. The library's own `map`, `filter`, `onEach`, `take`, `flowOf` and `asFlow` use the unchecked `unsafeFlow`, so `flowOf`/`asFlow` are **not cancellable** between items. `flowOn`, `buffer`, `conflate`, `channelFlow`, `produceIn` and `*Latest` are all `ChannelFlow` subclasses: when they need a channel, they start a second coroutine with `produce` and the collector drains the channel. Adjacent ones fuse into one channel, and `toString()` shows the fused result, which makes fusion easy to demo. Several surprises were verified locally: `buffer(onBufferOverflow = DROP_OLDEST)` keeps **one** element, not 64. `buffer(10).conflate()` is plain `conflate()`. A collector that cancels itself without suspending keeps draining values that are already buffered. `collectLatest` waits for the cancelled block's cleanup, and the producer waits with it. `flowOn(Dispatchers.Default)` inside `runTest` runs in real time.

**How claims were checked.** **[Local]** means I compiled and ran the program in this session. I used `kotlin-compiler-embeddable-2.4.21` from the Gradle cache (`org.jetbrains.kotlin.cli.jvm.K2JVMCompiler`, `-jvm-target 21`) against `kotlinx-coroutines-core-jvm-1.11.0`, `kotlinx-coroutines-test-jvm-1.11.0`, and for the Reactor comparison `reactor-core-3.8.8` + `reactive-streams-1.0.4` (all from `~/.gradle/caches/modules-2/files-2.1/`). Everything ran on OpenJDK 21.0.12. The probe, lab checks and stack demo were re-run on OpenJDK 25.0.5 with identical output. The programs and outputs are below. **[Source]** means I read the file at git tag `1.11.0` (the tag exists under that exact name) via `https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/<path>`. **[Docs]** means an official page that I fetched and read in this session. **[Unverified]** is marked where it applies. All timing numbers come from this 4-core machine, which was busy with other jobs (load average 1.5 to 3.6 during the runs). Each timing demo ran 3 times and the range is reported. Virtual-time numbers come from `kotlinx-coroutines-test` and are exact.

---

## 1. A flow from scratch: two interfaces, cold, sequential, and the call stack

### Takeaway
A flow is an object with one suspend function, `collect(collector)`. A collector is an object with one suspend function, `emit(value)`. `collect` calls your block, the block calls `emit`, and `emit` *is* the collector's code. Nothing is queued, and no thread or coroutine is created. Three properties follow from that call shape. A flow is cold (the block runs once per `collect` call). It is sequential (the next `emit` cannot start until the collector's code for the previous value has returned). And backpressure is free (a slow collector simply makes `emit` take longer).

### Facts
- **Exact shapes in 1.11.0.** `public interface Flow<out T> { public suspend fun collect(collector: FlowCollector<T>) }`. This is a plain interface, **not** `fun interface`. `public fun interface FlowCollector<in T> { public suspend fun emit(value: T) }`. [Source: `common/src/flow/Flow.kt`, `common/src/flow/FlowCollector.kt`] [Docs: the API page for FlowCollector shows `fun interface FlowCollector<in T>`, and the page for Flow shows `interface Flow<out T>`, both under version 1.11.0]
- Checked by reflection: `Flow::class.isFun == false`, `FlowCollector::class.isFun == true`. `val bad: Flow<Int> = Flow { c -> c.emit(1) }` does not compile: `error: interface 'interface Flow<out T> : Any' does not have constructors.` `FlowCollector<String> { v -> println(v) }` does compile (SAM conversion). [Local, Shapes.kt / FunIface.kt]
- `FlowCollector` KDoc: "Implementations of this interface are not thread-safe", and `emit` "is not thread-safe and should not be invoked concurrently." [Source: FlowCollector.kt]
- `Flow` KDoc: "**The `Flow` interface is not stable for inheritance in 3rd party libraries**, as new methods might be added to this interface in the future, but is stable for use. Use the `flow { ... }` builder function to create an implementation, or extend [AbstractFlow]." [Source: Flow.kt]
- `Flow` KDoc on sequential execution: "By default, flows are _sequential_ and all flow operations are executed sequentially in the same coroutine, with an exception for a few operations specifically designed to introduce concurrency into flow execution such as [buffer] and [flatMapMerge]." On cold flows: intermediate operators "do not execute any code in the flow and are not suspending functions themselves. They only set up a chain of operations for future execution and quickly return." [Source: Flow.kt]
- `flow { }` KDoc: "The flow being _cold_ means that the [block] is called every time a terminal operator is applied to the resulting flow." [Source: `common/src/flow/Builders.kt`]
- The current Kotlin guide says it directly in a code comment: "The emit() function calls the lambda passed to collect()". [Docs: https://kotlinlang.org/docs/coroutines-flow.html, section "Handle exceptions in flows"]
- **A toy flow with no library types behaves the same.** The program ToyFlow.kt (Demo D1) defines `fun interface ToyCollector<T>` + `interface ToyFlow<T>` + a 3-line builder. Building it prints nothing. Each `collect` reruns the body, and each `before emit(n)` is followed by `[collector] got n` and only then by `after emit(n)`. [Local]
- **Yes, the collector's code runs inside `emit`.** A stack printed from inside `collect { }` (Demo D2) shows the toy flow's chain `collect lambda <- toyFlow block <- ToyFlow.collect <- main`. For the real `flow { }.map { }` it shows, from the top: your lambda's `emit` <- map's inlined collector `emit` <- `SafeCollector.emit` <- the `flow { }` block (`invokeSuspend`) <- `SafeFlow.collectSafely` <- `AbstractFlow.collect` <- map's inlined `collect` <- `main`'s coroutine. All of it is on thread `main`. [Local, StackDemo.kt]
- After a `flowOn(Dispatchers.IO)`, the stack is different. The collector is called from `FlowKt__ChannelsKt.emitAllImpl` (the channel-draining loop), and the `flow { }` block is no longer on the stack, because it runs in another coroutine on an IO thread. [Local, StackFlowOn.kt]
- Free backpressure, measured. With a 100 ms producer and a 300 ms collector, `emit 2` happens at t=500 ms: 100 + 300 + 100. `emit(1)` did not return until the collector finished at t=400. [Local, Timing.kt "plain", virtual time: `t=100 emit 1, t=400 done 1, t=500 emit 2 …`] A probe that holds the first value shows **0** further emits returning while the collector is busy. [Local, Probe.kt]
- `flow.collect { … }` resolves to the **member** `Flow.collect(FlowCollector)`, with the lambda SAM-converted. The old inline extension `Flow<T>.collect(crossinline action)` is still in 1.11.0, but as `@Deprecated(level = DeprecationLevel.HIDDEN, message = "Backwards compatibility with JS and K/N")`. [Source: `common/src/flow/terminal/Collect.kt`] In the stack trace, the lambda appears as a generated class's `emit` method (`StackDemoKt$main$1$5.emit`). [Local]

### Gaps
- The version in which `FlowCollector` became a `fun interface` was not checked. Only the 1.11.0 state is verified.

---

## 2. What `flow { }` adds: SafeFlow, AbstractFlow, SafeCollector, and how operators are written

### Takeaway
`flow(block)` returns `SafeFlow(block)`, which is an `AbstractFlow`. `AbstractFlow.collect` is `final`: it wraps your collector in `SafeCollector(collector, coroutineContext)` and calls `collectSafely`. Each `SafeCollector.emit` (1) calls `ensureActive()` on the emitting context, (2) checks that context against the collector's context, but only when the context *object* changed since the last emit ("triggered once per flow on a happy path"), and (3) refuses to emit if the previous `emit` threw. The library's own operators skip all this with an internal `unsafeFlow` when they trust themselves, so they cost only a nested call.

### Facts: the classes
- `public fun <T> flow(block: suspend FlowCollector<T>.() -> Unit): Flow<T> = SafeFlow(block)`. `private class SafeFlow<T>(block) : AbstractFlow<T>() { override suspend fun collectSafely(collector) { collector.block() } }`. [Source: Builders.kt]
- `@ExperimentalCoroutinesApi public abstract class AbstractFlow<T> : Flow<T>, CancellableFlow<T>`. Its `final override suspend fun collect(collector)` does `val safeCollector = SafeCollector(collector, coroutineContext); try { collectSafely(safeCollector) } finally { safeCollector.releaseIntercepted() }`. The KDoc of `collectSafely` lists two constraints: don't change the context when emitting, and "serialize calls to emit as FlowCollector implementations are not thread-safe by default". [Source: Flow.kt] Extending `AbstractFlow` without opt-in gives the warning "this declaration needs opt-in. Its usage should be marked with '@kotlinx.coroutines.ExperimentalCoroutinesApi'…". [Local, Stability.kt]
- JVM `SafeCollector` extends `ContinuationImpl` "to pretend it *is* a state-machine of its own `emit` method", so that no state machine is allocated per element ("effectively garbage-free on its hot-path"). [Source: `jvm/src/flow/internal/SafeCollector.kt`]
- **The cancellation check:** `private fun emit(uCont, value)` starts with `val currentContext = uCont.context; currentContext.ensureActive()`. [Source: jvm SafeCollector.kt] The `flow { }` KDoc says: "Emissions from [flow] builder are [cancellable] by default — each call to emit also calls ensureActive." [Source: Builders.kt]
- **The context check** (`SafeCollector.checkContext`, common): it folds over the emission context. Every non-`Job` element must be **identical** (`!==` test) to the collector's element with the same key. The emission `Job` must reach the collector's `Job` through `ScopeCoroutine` parents only (`transitiveCoroutineParent`), so `coroutineScope { emit() }` is allowed but `launch { emit() }` is not. The element count must match. [Source: `common/src/flow/internal/SafeCollector.common.kt`]
- **The exception transparency check:** if the downstream `emit` throws, `SafeCollector` stores `DownstreamExceptionContext(e, …)` as the last emission context, so the next `emit` sees a context mismatch and throws. [Source: jvm SafeCollector.kt]

### Facts: exact messages in 1.11.0 (all [Local], Invariants.kt / TakeFirst.kt, collected inside `runBlocking(CoroutineName("collector"))`; object hashes vary per run)
- `flow { withContext(Dispatchers.IO) { emit(1) } }` →
  ```
  java.lang.IllegalStateException:
  Flow invariant is violated:
  		Flow was collected in [CoroutineName(collector), BlockingCoroutine{Active}@2f2575c4, BlockingEventLoop@bdffdb9],
  		but emission happened in [CoroutineName(collector), DispatchedCoroutine{Active}@65e9d512, Dispatchers.IO].
  		Please refer to 'flow' documentation or use 'flowOn' instead
  ```
- `withContext(CoroutineName("other")) { emit(1) }` fails with the same message, because it is not only about dispatchers: any different context element counts. `withContext(EmptyCoroutineContext) { emit(1) }` and `coroutineScope { emit(1) }` are **allowed**: both collect `1` and finish OK. [Local]
- `flow { coroutineScope { launch { emit(1) } } }` →
  ```
  java.lang.IllegalStateException:
  Flow invariant is violated:
  		Emission from another coroutine is detected.
  		Child of StandaloneCoroutine{Active}@67784306, expected child of BlockingCoroutine{Active}@2f2575c4.
  		FlowCollector is not thread-safe and concurrent emissions are prohibited.
  		To mitigate this restriction please use 'channelFlow' builder instead of 'flow'
  ```
- Emitting from a `catch` after a downstream failure →
  ```
  java.lang.IllegalStateException: Flow exception transparency is violated:
      Previous 'emit' call has thrown exception java.lang.IllegalArgumentException: bad amount 2, but then emission attempt of value '3' has been detected.
      Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
      For a more detailed explanation, please refer to Flow documentation.
  ```
  **The original exception is lost as an object.** On the thrown ISE, `cause == null` and `suppressed == []`. The original appears only as text inside the message. [Local]
- The same check fires when someone swallows `take`'s abort: `flow { try { emit(1) } catch (e: Throwable) {}; emit(2) }.take(1)` → "Previous 'emit' call has thrown exception kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed, but then emission attempt of value '2' has been detected." [Local]
- `flowOf(1).flowOn(Job())` throws **when the operator is built**, not on collect: `java.lang.IllegalArgumentException: Flow context cannot contain job in it. Had JobImpl{Active}@…`. [Local; Source: `checkFlowContext` in `operators/Context.kt`]

### Facts: how the library writes operators
- `@PublishedApi internal inline fun <T> unsafeFlow(crossinline block: suspend FlowCollector<T>.() -> Unit): Flow<T> = object : Flow<T> { override suspend fun collect(collector) { collector.block() } }`. KDoc: "An analogue of the [flow] builder that does not check the context of execution of the resulting flow. Used in our own operators where we trust the context of invocations." [Source: SafeCollector.common.kt]
- `Transform.kt` imports `unsafeFlow as flow` and `unsafeTransform as transform`. So `map` is `transform { value -> return@transform emit(transform(value)) }`, `filter` is `transform { value -> if (predicate(value)) return@transform emit(value) }`, and `onEach` is `transform { value -> action(value); return@transform emit(value) }`. All of these are the **unsafe** versions. `map` and `filter` are `inline` with `crossinline` lambdas. [Source: `operators/Transform.kt`]
- The public `transform` is the **safe** one: `public inline fun <T, R> Flow<T>.transform(crossinline transform: suspend FlowCollector<R>.(value: T) -> Unit): Flow<R> = flow { collect { value -> transform(value) } }`, with the comment "safe flow is used here, because collector is exposed to transform on each operation". `onStart`, `onCompletion` and `onEmpty` are `unsafeFlow` but run your action through a fresh `SafeCollector`. [Source: `operators/Emitters.kt`]
- Runtime classes confirm this. `flow{}` → `kotlinx.coroutines.flow.SafeFlow`. `flowOf(1,2)` → `kotlinx.coroutines.flow.FlowKt__BuildersKt$flowOf$$inlined$unsafeFlow$1`. `(1..3).asFlow()` → `…FlowKt__BuildersKt$asFlow$$inlined$unsafeFlow$9`. `.map {}` → a class in *your* file (`ShapesKt$main$1$invokeSuspend$$inlined$map$1`), because it is inlined. `.transform {}` → `SafeFlow`. `.take(1)` → `…FlowKt__LimitKt$take$$inlined$unsafeFlow$1`. `emptyFlow()` → `kotlinx.coroutines.flow.EmptyFlow`. [Local, Shapes.kt]
- **`take`:** `require(count > 0)`, then `unsafeFlow { val ownershipMarker = Any(); var consumed = 0; try { collect { value -> if (++consumed < count) return@collect emit(value) else return@collect emitAbort(value, ownershipMarker) } } catch (e: AbortFlowException) { e.checkOwnership(owner = ownershipMarker) } }`. `emitAbort` emits the value, then `throw AbortFlowException(ownershipMarker)`. `checkOwnership` rethrows if the owner is not `===` its own marker, so nested `take`s don't steal each other's aborts. [Source: `operators/Limit.kt`, `internal/FlowExceptions.common.kt`]
- `AbortFlowException` (JVM) `: CancellationException("Flow was aborted, no more elements needed")`, with `fillInStackTrace` disabled unless debug mode is on. [Source: `jvm/src/flow/internal/FlowExceptions.kt`]
- **What you see from the producer side** with `take(2)`: `emit 1, got 1, emit 2, got 2`, then the producer's `emit` throws `kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed`, the producer's `finally` runs, and an `onCompletion` placed above `take` gets `cause=…AbortFlowException…`. `emit 3` never happens. [Local, TakeFirst.kt]
- **`first()`** = `collectWhile { result = it; false }`, then `NoSuchElementException("Expected at least one element")` if nothing came. `collectWhile` uses an anonymous `FlowCollector` that throws `AbortFlowException(this)` when the predicate is false. It catches the exception, checks ownership, then calls `coroutineContext.ensureActive()`. `first(predicate)` is the same with the message "Expected at least one element matching the predicate". `single()` is a plain `collect` with `require(result === NULL) { "Flow has more than one element" }` and `NoSuchElementException("Flow is empty")`. [Source: `terminal/Reduce.kt`, `operators/Limit.kt`] Observed: `first()` aborts the producer right after `emit 1`, and `first { it > 2 }` aborts after `emit 3`. The producer's `finally` runs in both cases. [Local]
- Nested take: `(1..10).asFlow().take(5).onEach { print("[$it]") }.take(2).toList()` prints `[1][2]` and returns `[1, 2]`. [Local, Extra.kt]

### Facts: builders and cancellation
- `Builders.kt` has `import kotlinx.coroutines.flow.internal.unsafeFlow as flow`. Every `asFlow()` (Iterable, Iterator, Sequence, Array, IntArray, LongArray, IntRange, LongRange, `() -> T`, `suspend () -> T`) and both `flowOf` overloads are therefore written on `unsafeFlow`, with **no `ensureActive` per item**. [Source: Builders.kt; class names above, Local]
- `cancellable()`: "Returns a flow which checks cancellation status on each emission and throws the corresponding cancellation cause if flow collector was cancelled. Note that [flow] builder and all implementations of [SharedFlow] are [cancellable] by default. This operator provides a shortcut for `.onEach { currentCoroutineContext().ensureActive() }`." If the receiver is already a `CancellableFlow` (every `AbstractFlow`, so every `flow { }`), it returns `this`. Otherwise it wraps the flow in `CancellableFlowImpl`, which calls `ensureActive()` before each downstream `emit`. [Source: `operators/Context.kt`] `flow<Int>{}.cancellable() === it` is `true`. [Local]
- Measured with a collector that calls `cancel()` on its own coroutine at value 3 and never suspends (Demo D6): `flow { for (i in 1..5) emit(i) }` → `[1, 2, 3]`. `(1..5).asFlow()` → `[1, 2, 3, 4, 5]`. `flowOf(1,2,3,4,5)` → `[1, 2, 3, 4, 5]`. `(1..5).asFlow().cancellable()` → `[1, 2, 3]`. `asFlow().map { }` → `[1, 2, 3, 4, 5]` (map is unsafe). `asFlow().transform { emit(it) }` → `[1, 2, 3]` (transform is a SafeFlow). [Local, Cancel.kt]
- **Behind a buffer, the drain continues too.** With 1..100 and the same self-cancelling, non-suspending collector, `.buffer()` delivered **66** values and `.buffer(10)` delivered **12**, identical in 3 runs and again under `runTest`. `.flowOn(Dispatchers.Default)` delivered 36, 23 and 14 in three runs (it is a race). `.buffer().cancellable()` → 3. A receive from a channel that already has elements does not suspend, so nothing checks cancellation, and `emitAll` calls `ensureActive()` only once, before the loop. [Local, Cancel2.kt, LabChecks.kt; Source: `emitAllImpl` in `common/src/flow/Channels.kt`] In real code a collector that suspends (I/O, `delay`) sees the cancellation at its next suspension. This only bites CPU-only collectors.
- The current Kotlin Flow guide no longer has the old "Flow cancellation checks / Making busy flow cancellable" section. The repo's `docs/topics/flow.md` at tag 1.11.0, which is byte-identical to 1.10.2, still has it. [Docs: https://kotlinlang.org/docs/coroutines-flow.html headings; https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/docs/topics/flow.md, `#### Making busy flow cancellable`]

---

## 3. Context: why `withContext` around `emit` is forbidden, what `flowOn` builds, `channelFlow`, `produceIn`

### Takeaway
Because the collector runs *inside* `emit`, letting `emit` run under `withContext(IO)` would run the **collector's** code on an IO thread it never asked for, and two coroutines emitting at once would run the collector concurrently. A raw `Flow` implementation that skips `SafeCollector` shows exactly that. `flowOn(ctx)` fixes the problem with a second coroutine and a channel. It does this **only when the dispatcher changes**: a context change that keeps the dispatcher (a `CoroutineName`, say) runs inline with no channel. `flowOn` affects only the operators above it, up to the previous `flowOn`. Adjacent `flowOn`s fuse into one, and the one written first (nearest the source) wins for each context key.

### Facts
- **Why the rule exists, shown.** `object : Flow<String> { override suspend fun collect(c) { withContext(Dispatchers.IO) { c.emit("from raw Flow") } } }` compiles and runs with no error, and the collector prints `on DefaultDispatcher-worker-1`. The same code in `flow { }` throws "Flow invariant is violated". [Local, Shapes.kt]
- `Flow` KDoc, context preservation: "There is only one way to change the context of a flow: the [flowOn][Flow.flowOn] operator that changes the upstream context ("everything above the `flowOn` operator")." It also lists `launch(Dispatchers.IO)`, `GlobalScope.launch` and `withContext(CoroutineName("myFlow"))` as "prohibited" inside `flow { }`, while `coroutineScope { emit(2) }` is "OK -- still the same coroutine". [Source: Flow.kt]
- `flowOn` signature and body: `public fun <T> Flow<T>.flowOn(context: CoroutineContext): Flow<T> { checkFlowContext(context); return when { context == EmptyCoroutineContext -> this; this is FusibleFlow -> fuse(context = context); else -> ChannelFlowOperatorImpl(this, context = context) } }`. [Source: `operators/Context.kt`]
- **What `ChannelFlowOperatorImpl` does on collect** (`ChannelFlowOperator.collect`). The default capacity is the internal `Channel.OPTIONAL_CHANNEL` (-3). On that fast path it computes `newContext = collectContext.newCoroutineContext(context)`. If that equals the collector's context, it does a plain `flow.collect(collector)`. If the `ContinuationInterceptor` (the dispatcher) is the same, it runs the upstream via `withContextUndispatched` with no channel. Otherwise it takes the slow path: `ChannelFlow.collect` = `coroutineScope { collector.emitAll(produceImpl(this)) }`, where `produceImpl` = `scope.produce(context, produceCapacity, onBufferOverflow, start = CoroutineStart.ATOMIC, block = collectToFun)` and the upstream is collected into `SendingCollector(scope)` (whose `emit` is `channel.send(value)`). `produceCapacity` maps `OPTIONAL_CHANNEL` to `Channel.BUFFERED`. [Source: `internal/ChannelFlow.kt`, `internal/SendingCollector.kt`]
- So "flowOn builds a channel and a second coroutine" holds only when the dispatcher changes. Observed: `.flowOn(CoroutineName("renamed"))` interleaves `emit 1, collect 1, emit 2, collect 2…` on `main`. `.flowOn(io)` prints `emit 1, emit 2, emit 3` on `io-thread` before `collect 1` on `main` (the producer ran ahead into the channel). With a collector already on `Dispatchers.IO`, `flowOn(Dispatchers.IO)` stays sequential. With a collector on `Dispatchers.Default`, `flowOn(Dispatchers.IO)` creates a channel: they are different dispatcher objects even though they share threads. [Local, FlowOnThreads.kt, Extra.kt]
- `flowOn(CoroutineName("upstream"))`: inside the flow, `currentCoroutineContext()[CoroutineName]` is `CoroutineName(upstream)`, and in the collector it is `null`. [Local, ChannelFlowDemo.kt] The guide shows the same thing with `Dispatchers.IO + CoroutineName("upstream")`. [Docs: https://kotlinlang.org/docs/coroutines-flow.html, "Change the coroutine context of a cold flow with .flowOn()"]
- **Which side, with several `flowOn`s.** In `flow{emit}.map{map1}.flowOn(io).map{map2}.flowOn(cpu).collect{}`, `emit` and `map1` ran on `io-thread`, `map2` on `cpu-thread`, and `collect` on `main`. With `-Dkotlinx.coroutines.debug` the thread names show three coroutines (`io-thread @coroutine#3`, `cpu-thread @coroutine#2`, `main @coroutine#1`), so there are two channels and two extra coroutines. The interleaving of lines across threads varied between runs. [Local, FlowOnThreads.kt]
- **Adjacent `flowOn`s fuse.** KDoc: "Multiple `flowOn` operators fuse to a single `flowOn` with a combined context. The elements of the context of the first `flowOn` operator naturally take precedence". The code is `val newContext = context + this.context` ("previous upstream context (specified before) takes precedence"). [Source: Context.kt, ChannelFlow.kt] `flowOf(1,2,3).flowOn(Dispatchers.IO).flowOn(Dispatchers.Default).toString()` ends with `-> ChannelFlowOperatorImpl[context=Dispatchers.IO]`: one stage, IO wins. A `map` between them stops the fusion. [Local, Fusion.kt]
- `flowOn` KDoc on cancellation: "flows operating across different dispatchers might lose some in-flight elements when cancelled. In particular, this operator ensures that downstream flow does not resume on cancellation even if the element was already emitted by the upstream flow." [Source: Context.kt]
- To move the **collector**, wrap the terminal call. `withContext(io) { flow { … }.collect { … } }` printed both `emit` and `collect` on `io-thread`. [Local, FlowOnThreads.kt] (co-07 already teaches this. These notes confirm it.)
- **`channelFlow`** = `ChannelFlowBuilder(block)`, a `ChannelFlow` with `capacity = BUFFERED`, `SUSPEND`, whose `collectTo(scope)` just runs your block with the `ProducerScope` (a `CoroutineScope` + `SendChannel`). KDoc: "This builder ensures thread-safety and context preservation, thus the provided [ProducerScope] can be used concurrently from different contexts. The resulting flow completes as soon as the code in the [block] and all its children completes." [Source: Builders.kt] Observed: two `launch`es on `Dispatchers.IO` and `Dispatchers.Default` sent `A0, B0, A1, B1` from `DefaultDispatcher-worker-1`, and every `collect` line printed on `main`. The builder block returned first ("children still running"), and the flow completed only after both children finished. [Local, ChannelFlowDemo.kt, 3 runs, same order each time]
- `callbackFlow` is a `ChannelFlowBuilder` subclass that throws `IllegalStateException` ("'awaitClose { yourCallbackOrListener.cancel() }' should be used in the end of callbackFlow block. …") if the block returns while the channel is open. [Source: Builders.kt] (co-09 teaches this.)
- **`produceIn(scope)`** = `asChannelFlow().produceImpl(scope)`: a `produce` coroutine in *your* scope with the default `BUFFERED` capacity. KDoc: the transformation "is **stateful**, it launches a [produce] coroutine that collects the given flow". The `Flow` KDoc calls it "converting the flow into a hot channel". [Source: `common/src/flow/Channels.kt`, Flow.kt] Observed: `flow{…}.buffer(1).produceIn(this)` returned, and the upstream started at the caller's next suspension and emitted 1 (then suspended on the full 1-slot buffer) before anyone called `receive`. `ch.cancel()` stopped it. Without `cancel()` or full consumption, the enclosing scope waits for the producer. [Local, ChannelFlowDemo.kt; the last point follows from `produce` being a child coroutine, not separately run]
- Stability: `flowOn`, `channelFlow`, `callbackFlow` and `produceIn` compile with no opt-in warning in 1.11.0. `CoroutineScope.produce` itself is `@ExperimentalCoroutinesApi`. [Local, Stability.kt; Source: `channels/Produce.kt`]

---

## 4. Buffering: timing, buffer, conflate, collectLatest, fusion, Reactor

### Takeaway
Buffering operators move the upstream into a second coroutine and put a channel between the two halves. The channel's capacity and overflow policy decide how far the producer may run ahead and what is lost. All channel-based operators that sit next to each other fuse into **one** channel, and the fused configuration is visible in `toString()`. The `*Latest` operators are also channel flows, but they cancel the previous block and join it before starting the next one.

### Timing (producer 100 ms per item, collector 300 ms per item, 3 items)

| Pipeline | Virtual time (exact, `runTest`) | Real time, 3 runs [Local] | Values the collector finished |
|---|---|---|---|
| plain | 1200 ms | 1237 to 1254 ms | 1, 2, 3 |
| `buffer()` | 1000 ms | 1028 to 1045 ms | 1, 2, 3 |
| `buffer(0)` | 1000 ms | (virtual only) | 1, 2, 3 |
| `conflate()` | 700 ms | 705 to 706 ms | 1, 3 |
| `collectLatest { }` | 600 ms | 613 to 621 ms | 3 (started 1, 2, 3) |
| `mapLatest { delay(300) }` | 600 ms | 604 to 607 ms | 3 |
| `flowOn(CoroutineName(...))` | 1200 ms | (virtual only) | 1, 2, 3 (no channel) |
| `flowOn(StandardTestDispatcher(testScheduler))` | 1000 ms | (virtual only) | 1, 2, 3 |

Real-time numbers come from this 4-core machine, busy with other jobs. [Local, Timing.kt, TestTime.kt] The virtual traces: plain `emit 1@100, done 1@400, emit 2@500, done 2@800, emit 3@900, done 3@1200`. buffer `emits @100/200/300, done @400/700/1000`. conflate `emits @100/200/300, done 1@400, done 3@700`. collectLatest `emits @100/200/300, done 3@600`. The old guide quotes 1220, 1071, 758 and 741 ms for the same examples. [Docs: https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/docs/topics/flow.md] Our collectLatest measured ~615 ms, so 741 is just a slow run, and the model number is 600. `buffer(0)` equals `buffer()` here because with 3 items a 1-slot hand-off is already enough. A slow producer (300 ms) with a fast collector (100 ms) plus `buffer()` is also 1000 ms (300 × 3 + 100). Buffering hides whichever side is faster. [Local]

### Facts: buffer and conflate
- `public fun <T> Flow<T>.buffer(capacity: Int = BUFFERED, onBufferOverflow: BufferOverflow = BufferOverflow.SUSPEND): Flow<T>`. It `require`s `capacity >= 0 || capacity == BUFFERED || capacity == CONFLATED`, giving `"Buffer size should be non-negative, BUFFERED, or CONFLATED, but was -5"` for `buffer(-5)`. It also requires `capacity != CONFLATED || onBufferOverflow == SUSPEND`, giving `"CONFLATED capacity cannot be used with non-default onBufferOverflow"`. `CONFLATED` is desugared to `(0, DROP_OLDEST)`. Then `is FusibleFlow -> fuse(...)`, else `ChannelFlowOperatorImpl(this, capacity, onBufferOverflow)`. [Source: Context.kt; messages Local, Fusion.kt]
- `public fun <T> Flow<T>.conflate(): Flow<T> = buffer(CONFLATED)`. [Source]
- KDoc, conceptual implementation of `buffer`: `flow { coroutineScope { val channel = produce(capacity = capacity) { collect { send(it) } }; channel.consumeEach { emit(it) } } }`. [Source: Context.kt] This is a good "write it yourself" exercise.
- `Channel.BUFFERED = -2`. "For [BufferOverflow.SUSPEND] … the default capacity is 64, but on the JVM it can be overridden by setting the [DEFAULT_BUFFER_PROPERTY_NAME] system property." `@DelicateCoroutinesApi public const val DEFAULT_BUFFER_PROPERTY_NAME = "kotlinx.coroutines.channels.defaultBuffer"`. `CHANNEL_DEFAULT_CAPACITY = systemProp(DEFAULT_BUFFER_PROPERTY_NAME, 64, 1, UNLIMITED - 1)`. KDoc: "Usage of this property is highly discouraged and is intended to be used as a last-ditch effort as an immediate measure for hot fixes and duct-taping." [Source: `channels/Channel.kt`; Docs: API page for DEFAULT_BUFFER_PROPERTY_NAME loads] With `-Dkotlinx.coroutines.channels.defaultBuffer=8`, `buffer()` let 9 emits return instead of 65. [Local, Probe.kt] Reading the constant warns "this is a delicate API". [Local]
- **The trap with a drop policy and the default capacity.** `Channel(BUFFERED, onBufferOverflow != SUSPEND)` creates `ConflatedBufferedChannel(1, …)`. KDoc: "If a different [BufferOverflow] is specified, `Channel(BUFFERED)` creates a channel with a buffer of size 1". [Source: Channel.kt] So `buffer(onBufferOverflow = DROP_OLDEST)` is a 1-slot buffer that behaves exactly like `conflate()`: received `[1, 200]`. [Local, Probe.kt]
- `Channel(0, DROP_OLDEST/DROP_LATEST)` also becomes a 1-slot `ConflatedBufferedChannel`. The `buffer` KDoc: "To implement either of the custom strategies, a buffer of at least one element is used." [Source] Observed: `buffer(0, DROP_LATEST)` → `[1, 2]`, `buffer(0, DROP_OLDEST)` → `[1, 200]`. [Local]
- **`buffer(0)`** is a rendezvous channel, still with a separate producer coroutine. The producer can be exactly one element ahead (the one being handed over): 1 emit returned while the collector held its first value, versus 0 for the plain flow. [Local, Probe.kt]
- **Probe results** (Demo D11: a 200-item `flow {}`, the collector holds item 1 until the producer has gone as far as it can, then drains; single-threaded `runBlocking`; deterministic, identical md5 across runs and on JDK 25). "Emits returned while held" and what was finally received [Local]:

  | Operator | Emits returned while held | Received |
  |---|---|---|
  | plain | 0 | all 200 |
  | `flowOn(CoroutineName)` | 0 | all 200 |
  | `buffer(0)` | 1 | all 200 |
  | `buffer(1)` | 2 | all 200 |
  | `buffer(10)` | 11 | all 200 |
  | `buffer()` / `buffer().buffer()` | 65 | all 200 |
  | `buffer(10).buffer(20)` | 31 | all 200 |
  | `buffer(UNLIMITED)` | 200 | all 200 |
  | `conflate()` / `buffer(10).conflate()` / `buffer(onBufferOverflow = DROP_OLDEST)` / `buffer(0, DROP_OLDEST)` | 200 | `[1, 200]` |
  | `conflate().buffer(10)` / `buffer(10, DROP_OLDEST)` | 200 | `[1, 191..200]` (11) |
  | `buffer(10, DROP_LATEST)` | 200 | `[1..11]` |
  | `buffer(0, DROP_LATEST)` | 200 | `[1, 2]` |

  With `SUSPEND`, the producer gets `capacity + 1` emits ahead: `capacity` in the channel plus the one the collector holds.
- The `conflate` KDoc example holds: a flow of 1..30 every 100 ms, `.conflate().onEach { delay(1000) }.toList()` == `[1, 10, 20, 30]` under `runTest`. [Source: Context.kt; Local, LabChecks.kt] With a collector faster than the producer (50 ms vs 100 ms), `conflate()` delivers all of `[1, 2, 3]`: it only drops what arrives while the collector is busy. [Local, LatestJoin.kt]
- `StateFlow` already behaves as if `conflate` were applied, so "applying `conflate` to a `StateFlow` has no effect". `flowOn` on a `SharedFlow` "has not effect" (sic). [Source: Context.kt KDoc; not run]

### Facts: operator fusion (all Local via `toString()`, Fusion.kt and Extra.kt; Source: `ChannelFlow.fuse`)
- The `fuse` rules. The new context is `context + this.context`, so the earlier (upstream) setting wins. If the new `onBufferOverflow != SUSPEND`, it **replaces** the capacity and policy ("this additional buffer never suspends => overwrite preceding buffering configuration"). Otherwise capacities combine: `OPTIONAL_CHANNEL` and `BUFFERED` give way to an explicit size, two explicit sizes are **summed** (and clamped to `UNLIMITED` on int overflow), and the earlier overflow policy is kept. [Source: `internal/ChannelFlow.kt`]
- KDoc: "Adjacent applications of [channelFlow], [flowOn], [buffer], and [produceIn] are always fused so that only one properly configured channel is used for execution. Explicitly specified buffer capacity takes precedence over `buffer()` or `buffer(Channel.BUFFERED)` calls … Multiple requests with a specified buffer size produce a buffer with the sum of the requested buffer sizes." [Source: Context.kt]
- Observed `toString()` (upstream prefix trimmed):
  - `buffer()` → `ChannelFlowOperatorImpl[capacity=-2]`. `buffer(0)` → `[capacity=0]`.
  - `buffer().buffer()` → `[capacity=-2]` (one 64-slot channel, not two).
  - `buffer(10).buffer(20)` → `[capacity=30]`. `buffer(10).buffer()` → `[capacity=10]`. `buffer(0).buffer(0)` → `[capacity=0]`.
  - `conflate()` → `[capacity=0, onBufferOverflow=DROP_OLDEST]`.
  - `buffer(10).conflate()` → `[capacity=0, onBufferOverflow=DROP_OLDEST]`: the 10 is **discarded**.
  - `conflate().buffer(10)` → `[capacity=10, onBufferOverflow=DROP_OLDEST]`.
  - `buffer(10).buffer(5, DROP_LATEST)` → `[capacity=5, onBufferOverflow=DROP_LATEST]`.
  - `buffer(onBufferOverflow = DROP_OLDEST)` → `[capacity=-2, onBufferOverflow=DROP_OLDEST]` (and that is a 1-slot channel, see above).
  - `flowOn(IO).buffer(5)` and `buffer(5).flowOn(IO)` → both `[context=Dispatchers.IO, capacity=5]`.
  - `flowOn(IO).buffer(5).conflate()` → `[context=Dispatchers.IO, capacity=0, onBufferOverflow=DROP_OLDEST]`. `conflate().flowOn(IO).buffer(5)` → `[context=Dispatchers.IO, capacity=5, onBufferOverflow=DROP_OLDEST]`. Three operators, one channel.
  - `channelFlow{}` → `ChannelFlowBuilder[capacity=-2]`. `channelFlow{}.buffer(3)` → `ChannelFlowBuilder[capacity=3]` (the builder's own channel is resized, so no extra stage).
  - `mapLatest{}` → `ChannelFlowTransformLatest[capacity=-2]`. `mapLatest{}.buffer(0)` → `ChannelFlowTransformLatest[capacity=0]`.
  - `flatMapMerge{}` → `ChannelFlowMerge[concurrency=16, capacity=-2]` (`DEFAULT_CONCURRENCY` = 16, read through the `@FlowPreview` property `kotlinx.coroutines.flow.defaultConcurrency`).
- **A doc/code mismatch to flag.** The `conflate` KDoc says: "If there was no explicit buffer size specified, then the buffer size is `0`. Otherwise, the buffer size is unchanged." But `buffer(10).conflate()` fuses to capacity 0 and behaves like plain `conflate()` (received `[1, 200]`, not 11 values). The `buffer` KDoc is the accurate one: "A `buffer` call with a non-[SUSPEND] value of the [onBufferOverflow] parameter overrides all immediately preceding buffering operators". Only `conflate()` *followed by* `buffer(10)` gives a 10-slot drop-oldest buffer. [Source + Local]

### Facts: collectLatest, mapLatest, transformLatest
- `public suspend fun <T> Flow<T>.collectLatest(action: suspend (value: T) -> Unit) { mapLatest(action).buffer(0).collect() }`, with the note "buffer(0) is inserted here to fulfil user's expectations in sequential usages, e.g. `flowOf(1, 2, 3).collectLatest { delay(1); println(it) }` // Expect only 3 to be printed". [Source: `terminal/Collect.kt`] `collectLatest` is stable. [Local, Stability.kt]
- `@ExperimentalCoroutinesApi fun <T, R> Flow<T>.transformLatest(transform: suspend FlowCollector<R>.(value: T) -> Unit): Flow<R> = ChannelFlowTransformLatest(transform, this)`. `mapLatest` = `transformLatest { emit(transform(it)) }`. `flatMapLatest` = `transformLatest { emitAll(transform(it)) }`. All are `@ExperimentalCoroutinesApi`, and the KDoc says "This operator is [buffered][buffer] by default". [Source: `operators/Merge.kt`; Local: opt-in warnings]
- `ChannelFlowTransformLatest.flowCollect`: `coroutineScope { var previousFlow: Job? = null; flow.collect { value -> previousFlow?.apply { cancel(ChildCancelledException()); join() }; previousFlow = launch(start = CoroutineStart.UNDISPATCHED) { collector.transform(value) } } }`. [Source: `internal/Merge.kt`]
- **The cancel *and join* is observable** (Demo D13, virtual time). With a 50 ms `NonCancellable` cleanup in the cancelled block: `t=100 emit 1, start 1; t=200 emit 2, cancelled 1 (ChildCancelledException: Child of the scoped flow was cancelled); t=250 cleanup of 1 finished, start 2; t=350 emit 3` (not 300). **The producer is held up by the cleanup too**, because the cancel+join happens inside the upstream's `collect` lambda, and so inside the upstream's `emit`. The run ends at `t=700 done 3`. [Local, LatestJoin.kt]

### Facts: Reactor mapping (behavioral twin, [Local] with reactor-core 3.8.8; Reactor docs could not be fetched: projectreactor.io was blocked by this session's proxy)
ReactorProbe.kt is the Reactor version of the probe. `Flux.range(1, 200)` with a `BaseSubscriber` that requests 1, holds it, then requests `Long.MAX_VALUE`. Everything runs synchronously on main.

| Reactor | Source produced while held | Received | Matches Flow |
|---|---|---|---|
| no operator (`request(1)`) | 1 | all 200; upstream requests `[1, Long.MAX]` | plain flow (pull one at a time). Reactor counts the one in hand, the Flow probe counts emits that returned |
| `limitRate(10)` | 10 | all 200; upstream requests `[10, 8, 8, 8, …]` | ≈ `buffer(10)` (11 ahead). Not the same mechanism: it batches `request(n)`, with 75 % replenish |
| `onBackpressureBuffer()` | 200 | all 200 | `buffer(UNLIMITED)` |
| `onBackpressureBuffer(10)` | 12 | 11, then **ERROR** `OverflowException: The receiver is overrun by more signals than expected (bounded queue...)` | **no Flow equivalent**: Flow's bounded buffer suspends, it never errors |
| `onBackpressureBuffer(10, {}, DROP_OLDEST)` | 200 | `[1, 191..200]` | `buffer(10, DROP_OLDEST)`, identical |
| `onBackpressureBuffer(10, {}, DROP_LATEST)` | 200 | `[1..11]` | `buffer(10, DROP_LATEST)`, identical |
| `onBackpressureLatest()` | 200 | `[1, 200]` | `conflate()`, identical |
| `onBackpressureDrop()` | 200 | `[1]` | no exact twin: Flow's nearest, `buffer(0, DROP_LATEST)`, keeps one slot → `[1, 2]` |

Reactor's `switchMap` vs `flatMapLatest`/`mapLatest` was **not** run here [Unverified]. co-09 already pairs them.

### Facts: testing and virtual time
- `runTest { slow().flowOn(Dispatchers.Default).toList() }` with three `delay(1_000)`s took **3012 ms of wall time** and the virtual clock stayed at **0**. Without `flowOn`, or with `flowOn(StandardTestDispatcher(testScheduler))`, it was virtual 3000 ms in 4 to 123 ms of wall time. So inject the dispatcher you pass to `flowOn`. [Local, TestTime.kt]
- All lab expectations below were checked as PASS under `runTest` (LabChecks.kt): plain 1200, conflate `[1,3]` 700, mapLatest `[3]` 600, the KDoc `[1,10,20,30]` example, ahead counts 11/65/1, drop policies, the buffer(10) drain of 12, and `.cancellable()` stopping at 3. [Local]

---

## Exact API signatures and stability in 1.11.0

Annotation status is from the 1.11.0 source. "Stable" means no opt-in annotation, and the compile of Stability.kt confirmed it: experimental and preview APIs gave warnings, stable ones gave none. [Source + Local]

| Declaration (1.11.0) | Status |
|---|---|
| `public interface Flow<out T> { public suspend fun collect(collector: FlowCollector<T>) }` | stable for use, **not stable for inheritance** (KDoc) |
| `public fun interface FlowCollector<in T> { public suspend fun emit(value: T) }` | stable |
| `public abstract class AbstractFlow<T> : Flow<T>, CancellableFlow<T>`; `final override suspend fun collect(...)`; `abstract suspend fun collectSafely(collector: FlowCollector<T>)` | `@ExperimentalCoroutinesApi` |
| `public fun <T> flow(block: suspend FlowCollector<T>.() -> Unit): Flow<T>` | stable |
| `public fun <T> flowOf(vararg elements: T): Flow<T>`, `public fun <T> flowOf(value: T): Flow<T>`, `public fun <T> emptyFlow(): Flow<T>` | stable |
| `asFlow()` on `Iterable`, `Iterator`, `Sequence`, `Array`, `IntArray`, `LongArray`, `IntRange`, `LongRange`, `() -> T`, `suspend () -> T` | stable |
| `public fun <T> channelFlow(block: suspend ProducerScope<T>.() -> Unit): Flow<T>`, `public fun <T> callbackFlow(block: suspend ProducerScope<T>.() -> Unit): Flow<T>` | stable |
| `public fun <T> Flow<T>.buffer(capacity: Int = BUFFERED, onBufferOverflow: BufferOverflow = BufferOverflow.SUSPEND): Flow<T>` | stable (a 1-arg overload is `@Deprecated(HIDDEN)`) |
| `public fun <T> Flow<T>.conflate(): Flow<T>` | stable |
| `public fun <T> Flow<T>.flowOn(context: CoroutineContext): Flow<T>` | stable; `IllegalArgumentException` if `context` has a `Job` |
| `public fun <T> Flow<T>.cancellable(): Flow<T>` | stable |
| `public fun <T> Flow<T>.produceIn(scope: CoroutineScope): ReceiveChannel<T>` | stable (no annotation at 1.11.0) |
| `public inline fun <T, R> Flow<T>.map(crossinline transform: suspend (value: T) -> R): Flow<R>` | stable |
| `public inline fun <T> Flow<T>.filter(crossinline predicate: suspend (T) -> Boolean): Flow<T>` | stable |
| `public fun <T> Flow<T>.onEach(action: suspend (T) -> Unit): Flow<T>` | stable |
| `public inline fun <T, R> Flow<T>.transform(crossinline transform: suspend FlowCollector<R>.(value: T) -> Unit): Flow<R>` | stable |
| `public fun <T> Flow<T>.take(count: Int): Flow<T>` (`require(count > 0)`) | stable |
| `public suspend fun <T> Flow<T>.first(): T`, `first(predicate)`, `single()` | stable |
| `public suspend fun <T> Flow<T>.collectLatest(action: suspend (value: T) -> Unit)` | stable |
| `public suspend inline fun <T> SharedFlow<T>.collectLatest(noinline action: suspend (value: T) -> Unit): Nothing` | stable. CHANGES.md 1.11.0 calls it "a `StateFlow.collectLatest` overload returning `Nothing`", but the source declares it on `SharedFlow<T>`, so it covers StateFlow too |
| `transformLatest`, `mapLatest`, `flatMapLatest`, `flatMapMerge`, `flatMapConcat`, `flattenConcat`, `flattenMerge`, `chunked` | `@ExperimentalCoroutinesApi` |
| `DEFAULT_CONCURRENCY` (16), `DEFAULT_CONCURRENCY_PROPERTY_NAME = "kotlinx.coroutines.flow.defaultConcurrency"` | `@FlowPreview` |
| `Channel.BUFFERED = -2`, `RENDEZVOUS = 0`, `CONFLATED = -1`, `UNLIMITED = Int.MAX_VALUE`; internal `OPTIONAL_CHANNEL = -3` | stable (except the internal one) |
| `Channel.DEFAULT_BUFFER_PROPERTY_NAME = "kotlinx.coroutines.channels.defaultBuffer"` | `@DelicateCoroutinesApi` |
| `enum class BufferOverflow { SUSPEND, DROP_OLDEST, DROP_LATEST }` | stable |
| `CoroutineScope.produce(...)` | `@ExperimentalCoroutinesApi` |
| `FusibleFlow`, `ChannelFlow`, `SendingCollector` | `@InternalCoroutinesApi` (public but internal-use) |
| `unsafeFlow`, `unsafeTransform`, `SafeCollector`, `AbortFlowException`, `ChildCancelledException`, `ChannelFlowOperatorImpl`, `ChannelFlowTransformLatest`, `CancellableFlow` | `internal` (some `@PublishedApi`) |

---

## Common misconceptions (with the correction)

1. **"`Flow` is a `fun interface`, so `Flow { }` works."** Only `FlowCollector` is. `Flow { … }` fails with "interface … does not have constructors" [Local]. Use `flow { }`, or `AbstractFlow` (experimental) if you need a class [Source].
2. **"emit puts the value somewhere and the collector picks it up later."** Without a buffering operator, `emit` *calls* the collector. The collector's frames sit on top of `SafeCollector.emit` on the same thread [Local stack].
3. **"Backpressure needs a request(n) protocol."** In a plain flow, `emit` returns only when the collector returns (0 emits ahead), so it is free. Buffers make it bounded rather than zero [Local probe].
4. **"Every library operator goes through the safety checks."** `map`, `filter`, `onEach`, `take`, `flowOf` and `asFlow` use `unsafeFlow`. Only `flow { }`, `transform`, `transformWhile` and the actions of `onStart`/`onCompletion`/`onEmpty` use a `SafeCollector` [Source + Local class names].
5. **"`withContext` around `emit` is only a problem with dispatchers."** `withContext(CoroutineName("x")) { emit() }` fails too. `withContext(EmptyCoroutineContext)` and `coroutineScope` are fine [Local].
6. **"`flowOf`/`asFlow` stop when the collector is cancelled."** They don't check between items. Add `.cancellable()`, or rely on a suspending collector [Local].
7. **"After `cancel()`, nothing more reaches my collector."** Behind `buffer()`, a non-suspending collector drained 66 values after cancelling at 3, and 12 with `buffer(10)` [Local]. `.cancellable()` after the buffer fixes it.
8. **"The exception-transparency error tells me what went wrong."** Only as text. The original exception is neither the `cause` nor `suppressed` of the `IllegalStateException` [Local].
9. **"`take(n)` cancels the producer's coroutine."** It throws `AbortFlowException` (a `CancellationException`) *out of the producer's `emit`*. The producer's `finally` and an upstream `onCompletion` see it, and `take` catches only its own (ownership marker) [Source + Local]. Catching `Throwable` around `emit` breaks it ("exception transparency is violated") [Local].
10. **"`flowOn` always adds a thread hop and a buffer."** Only if the dispatcher changes. A `CoroutineName`-only `flowOn`, or `flowOn` to the dispatcher the collector already uses, runs inline [Source + Local].
11. **"With two `flowOn` calls, the last one wins."** Adjacent ones fuse, and the **first** (nearest the source) wins per context key. Non-adjacent ones each cover their own segment [Docs/Source + Local].
12. **"`buffer(onBufferOverflow = DROP_OLDEST)` keeps the latest 64."** It keeps **1**, because `Channel(BUFFERED, non-SUSPEND)` is a 1-slot channel [Source + Local]. Give an explicit capacity: `buffer(64, DROP_OLDEST)`.
13. **"`buffer(10).conflate()` is a 10-slot drop-oldest buffer."** It is plain `conflate()`. Use `buffer(10, DROP_OLDEST)` or `conflate().buffer(10)` [Local; the conflate KDoc wording is misleading].
14. **"Two `buffer()` calls give two buffers of 64."** They fuse into one of 64. `buffer(10).buffer(20)` is one of 30 [Local].
15. **"`buffer(0)` means no buffering, so it equals the plain flow."** It still creates a second coroutine and a rendezvous hand-off, so the producer runs one element ahead (1200 ms becomes 1000 ms in the timing demo) [Local].
16. **"`collectLatest` drops the old block instantly."** It cancels and **joins** it, so slow cleanup delays the next block *and* the producer [Source + Local].
17. **"`conflate()` always loses values."** Only values that arrive while the collector is busy. A fast collector gets everything [Local].
18. **"Flow's bounded buffer is like `onBackpressureBuffer(n)`."** Reactor's default errors with `OverflowException` when full. Flow's suspends the producer [Local].
19. **"Virtual time covers my `flowOn(Dispatchers.Default)` pipeline."** Not in `runTest`: it ran on the real clock (3 s) [Local]. Inject a test dispatcher.

---

## Demo ideas with expected outcomes

All demos are [Local] unless noted. Each is a single file with `import kotlinx.coroutines.*` and `import kotlinx.coroutines.flow.*` (plus `kotlinx.coroutines.test.*` where `runTest` is used). The outputs are copied from this session's runs. Hash codes (`@2f2575c4`) differ per run.

**D1. Toy flow from scratch (cold + sequential).** ToyFlow.kt:
```kotlin
fun interface ToyCollector<T> { suspend fun emit(value: T) }
interface ToyFlow<T> { suspend fun collect(collector: ToyCollector<T>) }

fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }

fun <T, R> ToyFlow<T>.map(f: suspend (T) -> R): ToyFlow<R> =
    toyFlow { this@map.collect { v -> emit(f(v)) } }

fun main() = runBlocking {
    val payments = toyFlow {
        println("  [producer] start")
        for (id in 1..3) {
            println("  [producer] before emit($id)")
            emit(id)
            println("  [producer] after emit($id)")
        }
        println("  [producer] done")
    }
    println("built the flow, nothing ran yet")
    println("--- first collect")
    payments.map { it * 100 }.collect { v -> println("  [collector] got $v") }
    println("--- second collect (cold: the body runs again)")
    payments.collect { v -> println("  [collector] got $v") }
}
```
Output (the first part; the second collect repeats the same pattern with values 1, 2, 3):
```
built the flow, nothing ran yet
--- first collect
  [producer] start
  [producer] before emit(1)
  [collector] got 100
  [producer] after emit(1)
  [producer] before emit(2)
  [collector] got 200
  [producer] after emit(2)
  [producer] before emit(3)
  [collector] got 300
  [producer] after emit(3)
  [producer] done
--- second collect (cold: the body runs again)
  [producer] start
  [producer] before emit(1)
  [collector] got 1
  ...
```

**D2. The call stack: the collector runs inside emit.** StackDemo.kt (it uses D1's `ToyCollector`/`ToyFlow`/`toyFlow`):
```kotlin
fun printStack(label: String) {
    println("$label, thread=${Thread.currentThread().name}")
    Thread.currentThread().stackTrace
        .drop(2)
        .takeWhile { !it.className.startsWith("kotlinx.coroutines.DispatchedTask") }
        .forEach { println("    at ${it.className}.${it.methodName}(${it.fileName}:${it.lineNumber})") }
}
fun main() = runBlocking {
    println("=== toy flow")
    toyFlow { emit("pay-1") }.collect { printStack("collector got $it") }
    println("=== kotlinx flow { } with map")
    flow { emit("pay-1") }.map { it.uppercase() }.collect { printStack("collector got $it") }
}
```
Output:
```
=== toy flow
collector got pay-1, thread=main
    at StackDemoKt$main$1$2.emit(StackDemo.kt:20)
    at StackDemoKt$main$1$2.emit(StackDemo.kt:20)
    at StackDemoKt$main$1$1.invokeSuspend(StackDemo.kt:20)
    at StackDemoKt$main$1$1.invoke(StackDemo.kt:-1)
    at StackDemoKt$main$1$1.invoke(StackDemo.kt:-1)
    at StackDemoKt$toyFlow$1.collect(StackDemo.kt:8)
    at StackDemoKt$main$1.invokeSuspend(StackDemo.kt:20)
    at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:34)
=== kotlinx flow { } with map
collector got PAY-1, thread=main
    at StackDemoKt$main$1$5.emit(StackDemo.kt:22)
    at StackDemoKt$main$1$5.emit(StackDemo.kt:22)
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1$2.emit(Emitters.kt:217)
    at kotlinx.coroutines.flow.internal.SafeCollectorKt$emitFun$1.invoke(SafeCollector.kt:11)
    at kotlinx.coroutines.flow.internal.SafeCollectorKt$emitFun$1.invoke(SafeCollector.kt:11)
    at kotlinx.coroutines.flow.internal.SafeCollector.emit(SafeCollector.kt:113)
    at kotlinx.coroutines.flow.internal.SafeCollector.emit(SafeCollector.kt:82)
    at StackDemoKt$main$1$3.invokeSuspend(StackDemo.kt:22)
    at StackDemoKt$main$1$3.invoke(StackDemo.kt:-1)
    at StackDemoKt$main$1$3.invoke(StackDemo.kt:-1)
    at kotlinx.coroutines.flow.SafeFlow.collectSafely(Builders.kt:57)
    at kotlinx.coroutines.flow.AbstractFlow.collect(Flow.kt:226)
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1.collect(SafeCollector.common.kt:112)
    at StackDemoKt$main$1.invokeSuspend(StackDemo.kt:22)
    at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:34)
```
How to read it, from the bottom: main → map's (inlined) collect → AbstractFlow.collect → SafeFlow.collectSafely → your `flow { }` block → SafeCollector.emit → map's collector → your lambda. Line numbers such as `Emitters.kt:217` belong to inlined code, so they can point past the end of the real file. Variant: add `.flowOn(Dispatchers.IO)` before `.collect` (StackFlowOn.kt). The stack becomes `your emit <- FlowKt__ChannelsKt.emitAllImpl(Channels.kt:33) <- … invokeSuspend <- BaseContinuationImpl.resumeWith`, and the flow block is gone from it.

**D3. Why the rule exists: a raw Flow vs `flow { }`.** Shapes.kt:
```kotlin
val raw: Flow<String> = object : Flow<String> {
    override suspend fun collect(collector: FlowCollector<String>) {
        withContext(Dispatchers.IO) { collector.emit("from raw Flow") }
    }
}
fun main() = runBlocking {
    val printer = FlowCollector<String> { v -> println("printer got '$v' on ${Thread.currentThread().name}") }
    flowOf("a").collect(printer)
    raw.collect(printer)
    try { flow { withContext(Dispatchers.IO) { emit("from flow { }") } }.collect(printer) }
    catch (e: IllegalStateException) { println("flow { } refused: ${e.message!!.lineSequence().first()}") }
}
```
Output: `printer got 'a' on main` / `printer got 'from raw Flow' on DefaultDispatcher-worker-1` / `flow { } refused: Flow invariant is violated:`. The same file printed the runtime class names listed in section 2.

**D4. The three invariant messages, verbatim.** Invariants.kt:
```kotlin
suspend fun attempt(name: String, f: Flow<Int>) {
    try { f.collect { println("  [$name] collected $it") }; println("[$name] OK") }
    catch (e: Throwable) { println("[$name] ${e::class.qualifiedName}:\n${e.message}\n") }
}
fun main() = runBlocking(CoroutineName("collector")) {
    attempt("withContext(IO)", flow { withContext(Dispatchers.IO) { emit(1) } })
    attempt("withContext(CoroutineName)", flow { withContext(CoroutineName("other")) { emit(1) } })
    attempt("withContext(Empty)", flow { withContext(EmptyCoroutineContext) { emit(1) } })
    attempt("coroutineScope", flow { coroutineScope { emit(1) } })
    attempt("launch", flow { coroutineScope { launch { emit(1) } } })
    attempt("channelFlow+launch(IO)", channelFlow { launch(Dispatchers.IO) { send(1) } })
    attempt("transparency", flow {
        emit(1)
        try { emit(2) } catch (e: Exception) { emit(3) }
    }.onEach { if (it == 2) throw IllegalArgumentException("bad amount 2") })
}
```
(`import kotlin.coroutines.EmptyCoroutineContext`.) Expected: the three messages quoted in section 2. `withContext(Empty)`, `coroutineScope` and `channelFlow+launch(IO)` each print `collected 1` and `OK`. For `transparency`, `collected 1` prints first. Adding `attempt("flowOn(Job())", flowOf(1).flowOn(Job()))` crashes `main` with `IllegalArgumentException: Flow context cannot contain job in it. Had JobImpl{Active}@…`, thrown at the `flowOn` call. This shows the check runs when the operator is built.

**D5. take/first from the producer's side.** TakeFirst.kt:
```kotlin
fun source(tag: String) = flow {
    try { for (i in 1..5) { println("  [$tag] emit $i"); emit(i) } }
    catch (e: Throwable) { println("  [$tag] emit threw ${e::class.qualifiedName}: ${e.message}"); throw e }
    finally { println("  [$tag] finally") }
}
fun main() = runBlocking {
    source("take").onCompletion { println("  [take] onCompletion cause=$it") }.take(2).collect { println("  got $it") }
    println("  first = " + source("first").first())
    println("  first = " + source("firstP").first { it > 2 })
}
```
Output:
```
  [take] emit 1
  got 1
  [take] emit 2
  got 2
  [take] emit threw kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  [take] finally
  [take] onCompletion cause=kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  [first] emit 1
  [first] emit threw kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  [first] finally
  first = 1
  [firstP] emit 1
  [firstP] emit 2
  [firstP] emit 3
  [firstP] emit threw kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  [firstP] finally
  first = 3
```
Follow-up: swallowing the abort, `flow { try { emit(1) } catch (e: Throwable) { println("swallowed") }; emit(2) }.take(1)`, prints `got 1`, `swallowed AbortFlowException`, then the "exception transparency is violated … AbortFlowException … value '2'" message.

**D6. Which builders are cancellable.** Cancel.kt:
```kotlin
suspend fun run(name: String, f: Flow<Int>) = coroutineScope {
    val seen = mutableListOf<Int>()
    val job = launch { f.collect { v -> seen += v; if (v == 3) cancel() } }
    job.join()
    println("%-28s collected %s".format(name, seen))
}
fun main() = runBlocking {
    run("flow { } loop", flow { for (i in 1..5) emit(i) })
    run("(1..5).asFlow()", (1..5).asFlow())
    run("flowOf(1,2,3,4,5)", flowOf(1, 2, 3, 4, 5))
    run("(1..5).asFlow().cancellable()", (1..5).asFlow().cancellable())
    run("asFlow().map { }", (1..5).asFlow().map { it })
    run("asFlow().transform { }", (1..5).asFlow().transform { emit(it) })
}
```
Output: `[1, 2, 3]`, `[1, 2, 3, 4, 5]`, `[1, 2, 3, 4, 5]`, `[1, 2, 3]`, `[1, 2, 3, 4, 5]`, `[1, 2, 3]`. Follow-up (Cancel2.kt): `flow { for (i in 1..100) emit(i) }` with the same collector collected 66 values behind `.buffer()`, 12 behind `.buffer(10)`, 3 behind `.buffer().cancellable()`, and 36/23/14 behind `.flowOn(Dispatchers.Default)` (a race; show it as "varies").

**D7. Thread names through two flowOn calls.** FlowOnThreads.kt:
```kotlin
fun named(name: String) = Executors.newSingleThreadExecutor { r -> Thread(r, name) }.asCoroutineDispatcher()
fun log(stage: String, v: Any?) = println("  %-8s %-3s thread=%s".format(stage, v, Thread.currentThread().name))
fun main() = runBlocking {
    val io = named("io-thread"); val cpu = named("cpu-thread")
    flow { for (i in 1..2) { log("emit", i); emit(i) } }
        .map { log("map1", it); it }
        .flowOn(io)
        .map { log("map2", it); it }
        .flowOn(cpu)
        .collect { log("collect", it) }
    io.close(); cpu.close()
}
```
(`import java.util.concurrent.Executors`.) Output: `emit`/`map1` on `io-thread`, `map2` on `cpu-thread`, `collect` on `main`. The interleaving between threads varies. Run it with `-Dkotlinx.coroutines.debug` to get `io-thread @coroutine#3`, `cpu-thread @coroutine#2`, `main @coroutine#1`. The same file also shows that `flowOn(CoroutineName("renamed"))` interleaves `emit 1, collect 1, emit 2, collect 2…`, while `flowOn(io)` prints all three `emit`s before the first `collect`, and that `withContext(io) { flow.collect {} }` puts both sides on `io-thread`.

**D8. channelFlow with two concurrent producers.** ChannelFlowDemo.kt:
```kotlin
var t0 = 0L
fun log(s: String) = println("  t=%3d %-36s thread=%s".format(System.currentTimeMillis() - t0, s, Thread.currentThread().name))
fun main() = runBlocking {
    t0 = System.currentTimeMillis()
    channelFlow {
        launch(Dispatchers.IO) { repeat(2) { delay(30); send("A$it"); log("sent A$it") } }
        launch(Dispatchers.Default) { repeat(2) { delay(45); send("B$it"); log("sent B$it") } }
        log("builder block returns (children still running)")
    }.collect { log("collect $it") }
    log("channelFlow completed after its children")
}
```
Output, run 2 of 3 (the order was the same in all three; the times shift by a few ms):
```
  t= 33 builder block returns (children still running) thread=main
  t= 70 sent A0                              thread=DefaultDispatcher-worker-1
  t= 70 collect A0                           thread=main
  t= 79 sent B0                              thread=DefaultDispatcher-worker-1
  t= 79 collect B0                           thread=main
  t=100 sent A1                              thread=DefaultDispatcher-worker-1
  t=100 collect A1                           thread=main
  t=125 sent B1                              thread=DefaultDispatcher-worker-1
  t=125 collect B1                           thread=main
  t=128 channelFlow completed after its children thread=main
```

**D9. produceIn is hot.** Same file:
```kotlin
coroutineScope {
    val ch = flow { log("upstream started"); for (i in 1..4) { emit(i); log("emitted $i") } }
        .buffer(1).produceIn(this)
    log("produceIn returned a ReceiveChannel")
    delay(100)
    log("receiving now: ${ch.receive()}")
    ch.cancel()
    log("cancelled the channel")
}
```
Output: `t=4 produceIn returned…`, `t=8 upstream started`, `t=11 emitted 1`, `t=105 receiving now: 1`, `t=106 cancelled the channel`. Only `emitted 1` appears: the 1-slot buffer is full, so `emit(2)` waits. Variant: remove `ch.cancel()` and the scope never finishes, because the producer waits on a full buffer forever (inferred from structured concurrency, not run).

**D10. Fusion, made visible with toString().** Fusion.kt:
```kotlin
fun show(label: String, f: Flow<*>) = println("%-40s %s".format(label, f.toString().replace(Regex("@[0-9a-f]+"), "")))
fun main() {
    val src = flowOf(1, 2, 3)
    show("buffer().buffer()", src.buffer().buffer())
    show("buffer(10).buffer(20)", src.buffer(10).buffer(20))
    show("buffer(10).conflate()", src.buffer(10).conflate())
    show("conflate().buffer(10)", src.conflate().buffer(10))
    show("buffer(onBufferOverflow = DROP_OLDEST)", src.buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST))
    show("flowOn(IO).flowOn(Default)", src.flowOn(Dispatchers.IO).flowOn(Dispatchers.Default))
    show("buffer(5).flowOn(IO)", src.buffer(5).flowOn(Dispatchers.IO))
    show("channelFlow{}.buffer(3)", channelFlow<Int> { }.buffer(3))
}
```
(`import kotlinx.coroutines.channels.BufferOverflow`.) Output (prefix `kotlinx.coroutines.flow.FlowKt__BuildersKt$flowOf$$inlined$unsafeFlow$1 -> ` dropped): `ChannelFlowOperatorImpl[capacity=-2]`, `[capacity=30]`, `[capacity=0, onBufferOverflow=DROP_OLDEST]`, `[capacity=10, onBufferOverflow=DROP_OLDEST]`, `[capacity=-2, onBufferOverflow=DROP_OLDEST]`, `[context=Dispatchers.IO]`, `[context=Dispatchers.IO, capacity=5]`, `block[…] -> ChannelFlowBuilder[capacity=3]`. Note that `toString()` of these classes is a debug aid, not API. Say so in the lesson.

**D11. How far can the producer run ahead? (the probe).** Probe.kt:
```kotlin
suspend fun probe(label: String, op: (Flow<Int>) -> Flow<Int>) = coroutineScope {
    var returned = 0
    val gate = CompletableDeferred<Unit>()
    val got = mutableListOf<Int>()
    val src = flow { for (i in 1..200) { emit(i); returned = i } }
    val job = launch { op(src).collect { got += it; if (got.size == 1) gate.await() } }
    delay(100)
    val ahead = returned
    gate.complete(Unit); job.join()
    val tail = if (got.size > 6) got.take(3) + listOf("...") + got.takeLast(2) else got
    println("%-38s emits returned while held: %3d; received %3d: %s".format(label, ahead, got.size, tail))
}
fun main() = runBlocking {
    probe("plain (no buffer)") { it }
    probe("buffer(0)") { it.buffer(0) }
    probe("buffer(10)") { it.buffer(10) }
    probe("buffer()") { it.buffer() }
    probe("conflate()") { it.conflate() }
    probe("buffer(10).conflate()") { it.buffer(10).conflate() }
    probe("buffer(onBufferOverflow = DROP_OLDEST)") { it.buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST) }
    probe("buffer(10, DROP_OLDEST)") { it.buffer(10, BufferOverflow.DROP_OLDEST) }
    probe("buffer(10, DROP_LATEST)") { it.buffer(10, BufferOverflow.DROP_LATEST) }
}
```
Output: see the probe table in section 4. Example lines:
```
plain (no buffer)                      emits returned while held:   0; received 200: [1, 2, 3, ..., 199, 200]
buffer(0)                              emits returned while held:   1; received 200: [1, 2, 3, ..., 199, 200]
buffer(10)                             emits returned while held:  11; received 200: [1, 2, 3, ..., 199, 200]
buffer()                               emits returned while held:  65; received 200: [1, 2, 3, ..., 199, 200]
conflate()                             emits returned while held: 200; received   2: [1, 200]
buffer(10).conflate()                  emits returned while held: 200; received   2: [1, 200]
buffer(onBufferOverflow = DROP_OLDEST) emits returned while held: 200; received   2: [1, 200]
buffer(10, DROP_OLDEST)                emits returned while held: 200; received  11: [1, 191, 192, ..., 199, 200]
buffer(10, DROP_LATEST)                emits returned while held: 200; received  11: [1, 2, 3, ..., 10, 11]
```
Run it again with `-Dkotlinx.coroutines.channels.defaultBuffer=8`: `buffer()` drops to 9.

**D12. The timing table (100/300 ms, 3 items).** Timing.kt runs the same scenarios in real or virtual time:
```kotlin
@file:OptIn(ExperimentalCoroutinesApi::class)
fun payments(clock: () -> Long, t0: Long) = flow {
    for (i in 1..3) { delay(100); println("    t=%4d emit %d".format(clock() - t0, i)); emit(i) }
}
suspend fun scenario(name: String, clock: () -> Long) {
    val t0 = clock(); val f = payments(clock, t0); val seen = mutableListOf<Int>()
    suspend fun consume(v: Int) { delay(300); seen += v; println("    t=%4d done %d".format(clock() - t0, v)) }
    when (name) {
        "plain" -> f.collect { consume(it) }
        "buffer()" -> f.buffer().collect { consume(it) }
        "conflate()" -> f.conflate().collect { consume(it) }
        "collectLatest" -> f.collectLatest { consume(it) }
        "mapLatest" -> f.mapLatest { delay(300); it }.collect { seen += it }
    }
    println("  => %-14s values=%s total=%d ms".format(name, seen, clock() - t0))
}
val names = listOf("plain", "buffer()", "conflate()", "collectLatest", "mapLatest")
fun main(args: Array<String>) {
    if (args.firstOrNull() == "virtual") runTest { for (n in names) scenario(n) { testScheduler.currentTime } }
    else runBlocking { for (n in names) scenario(n) { System.currentTimeMillis() } }
}
```
Virtual: 1200 / 1000 / 700 `[1, 3]` / 600 `[3]` / 600 `[3]`. Real, 3 runs: plain 1251, 1237, 1254. buffer 1045, 1028, 1030. conflate 706, 706, 705. collectLatest 613, 621, 614. mapLatest 604, 607, 605. (4-core machine, busy with other jobs.) For a video, run virtual first (it is exact), then real (it adds a few ms of scheduling).

**D13. collectLatest cancels *and waits*.** LatestJoin.kt:
```kotlin
fun main() = runTest {
    val t = { testScheduler.currentTime }
    flow { for (i in 1..3) { delay(100); println("t=${t()} emit $i"); emit(i) } }
        .collectLatest { v ->
            println("t=${t()} start $v")
            try { delay(300); println("t=${t()} done $v") }
            catch (e: CancellationException) {
                println("t=${t()} cancelled $v (${e::class.simpleName}: ${e.message})")
                withContext(NonCancellable) { delay(50) }
                println("t=${t()} cleanup of $v finished")
                throw e
            }
        }
}
```
Output:
```
t=100 emit 1
t=100 start 1
t=200 emit 2
t=200 cancelled 1 (ChildCancelledException: Child of the scoped flow was cancelled)
t=250 cleanup of 1 finished
t=250 start 2
t=350 emit 3
t=350 cancelled 2 (ChildCancelledException: Child of the scoped flow was cancelled)
t=400 cleanup of 2 finished
t=400 start 3
t=700 done 3
```
Ask the learner beforehand: "when is `emit 3`?" Most will say 300.

**D14. Reactor twin of the probe.** ReactorProbe.kt (Kotlin calling reactor-core 3.8.8):
```kotlin
import org.reactivestreams.Subscription
import reactor.core.publisher.*
fun probe(label: String, op: (Flux<Int>) -> Flux<Int>) {
    var produced = 0; val got = mutableListOf<Int>(); var error: Throwable? = null
    val src = Flux.range(1, 200).doOnNext { produced = it }
    val sub = object : BaseSubscriber<Int>() {
        override fun hookOnSubscribe(s: Subscription) = request(1)
        override fun hookOnNext(v: Int) { got += v }
        override fun hookOnError(t: Throwable) { error = t }
    }
    op(src).subscribe(sub)
    val ahead = produced
    sub.request(Long.MAX_VALUE)
    println("$label: produced while held=$ahead received=${got.size} first/last=${got.firstOrNull()}/${got.lastOrNull()} error=${error?.message}")
}
fun main() {
    probe("onBackpressureLatest()") { it.onBackpressureLatest() }
    probe("onBackpressureBuffer(10, {}, DROP_OLDEST)") { it.onBackpressureBuffer(10, {}, BufferOverflowStrategy.DROP_OLDEST) }
    probe("onBackpressureBuffer(10)") { it.onBackpressureBuffer(10) }
    probe("limitRate(10)") { it.limitRate(10) }
}
```
Output (this exact condensed program, ReactorCondensed.kt, was run):
```
onBackpressureLatest(): produced while held=200 received=2 first/last=1/200 error=null
onBackpressureBuffer(10, {}, DROP_OLDEST): produced while held=200 received=11 first/last=1/200 error=null
onBackpressureBuffer(10): produced while held=12 received=11 first/last=1/11 error=The receiver is overrun by more signals than expected (bounded queue...)
limitRate(10): produced while held=10 received=200 first/last=1/200 error=null
```
The longer ReactorProbe.kt also logs upstream requests with `doOnRequest`: `limitRate(10)` → `[10, 8, 8, 8, …]`, and every `onBackpressure*` → `[Long.MAX_VALUE]`.

**D15. flowOn on a real dispatcher defeats virtual time.** TestTime.kt:
```kotlin
fun slow() = flow { repeat(3) { delay(1_000); emit(it) } }
fun main() {
    var wall = System.nanoTime()
    runTest { slow().flowOn(Dispatchers.Default).toList()
        println("virtual=${currentTime} wall=${(System.nanoTime() - wall) / 1_000_000}") }
    wall = System.nanoTime()
    runTest { slow().flowOn(StandardTestDispatcher(testScheduler)).toList()
        println("virtual=${currentTime} wall=${(System.nanoTime() - wall) / 1_000_000}") }
}
```
Output: `virtual=0 wall=3012`, then `virtual=3000 wall=4`.

---

## Exercise ideas (labs with testable behavior; all expectations were checked with `runTest` in LabChecks.kt unless noted)

- **E1. Build the toy, then break it (lesson 1).** Write `ToyFlow`/`ToyCollector`/`toyFlow` plus `map`, `filter` and `take` on the toy. Tests: (a) building runs nothing (a side-effect counter stays 0); (b) collecting twice runs the body twice; (c) a recorded event list equals `[before 1, got 1, after 1, before 2, …]`; (d) toy `take(2)` stops the producer: throw a private exception from the collector with an owner marker and catch it in `take`. The test asserts the producer's `finally` ran and "emit 3" never happened. (The toy's behavior follows D1/D5. The toy `take` itself was not written in this session.)
- **E2. Write SafeCollector-lite (lesson 2).** Wrap a `ToyCollector` so the first `emit` records `currentCoroutineContext()`, and later emits throw `IllegalStateException("emission happened in another context")` if the context differs or a previous emit threw. Tests: `withContext(Dispatchers.IO) { emit() }` throws; `coroutineScope { emit() }` doesn't; emitting from a `catch` after the collector threw raises your error. Compare your messages with the real ones in section 2. (A design exercise; the expected behavior follows Invariants.kt.)
- **E3. Cancellable or not? (lesson 2).** Given six flows (`flow{}`, `asFlow()`, `flowOf`, `asFlow().cancellable()`, `asFlow().map{}`, `asFlow().transform{}`), predict which stop at 3 when the collector cancels itself, then assert. Expected: `[1,2,3]`, `[1..5]`, `[1..5]`, `[1,2,3]`, `[1..5]`, `[1,2,3]` (checked in `runBlocking`, Cancel.kt). Stretch: behind `buffer(10)` the count is 12, and `.cancellable()` after the buffer gives 3 (checked under `runTest`).
- **E4. Implement `buffer` yourself (lesson 4).** Use the KDoc's conceptual version (`flow { coroutineScope { val ch = produce(capacity = n) { collect { send(it) } }; ch.consumeEach { emit(it) } } }`). Assert in virtual time that your `myBuffer(64)` gives 1000 ms on the 100/300 × 3 model and your `myBuffer(0)` also gives 1000 ms, while plain gives 1200. Then assert that `myBuffer(10)` lets exactly 11 emits return while the collector holds item 1 (use the `ahead` helper below). (Library numbers verified. A hand-written version was not run.)
- **E5. Predict the fusion (lesson 4 quiz → test).** For `buffer(10).buffer(20)`, `buffer().buffer()`, `buffer(10).conflate()`, `conflate().buffer(10)`, `buffer(onBufferOverflow = DROP_OLDEST)` and `buffer(0, DROP_LATEST)`, predict the ahead count and the received list, then assert: 31/all, 65/all, `[1,200]`, `[1,191..200]`, `[1,200]`, `[1,2]`. The helper that works under `runTest`:
  ```kotlin
  suspend fun TestScope.ahead(op: (Flow<Int>) -> Flow<Int>): Pair<Int, List<Int>> {
      var returned = 0; val gate = CompletableDeferred<Unit>(); val got = mutableListOf<Int>()
      val job = launch { op(flow { for (i in 1..200) { emit(i); returned = i } }).collect { got += it; if (got.size == 1) gate.await() } }
      advanceUntilIdle(); val a = returned; gate.complete(Unit); job.join(); return a to got
  }
  ```
  Checked under `runTest` (LabChecks.kt, E5.kt): `buffer(10)` → 11, `buffer()` → 65, `buffer(0)` → 1, `buffer(10).buffer(20)` → 31 / all 200, `buffer().buffer()` → 65 / all 200, `buffer(10).conflate()` → `[1, 200]`, `conflate().buffer(10)` → 11 items `[1, 191..200]`, `buffer(onBufferOverflow = DROP_OLDEST)` → `[1, 200]`, `buffer(0, DROP_LATEST)` → `[1, 2]`, `buffer(3, DROP_OLDEST)` → `[1, 198, 199, 200]`, `buffer(3, DROP_LATEST)` → `[1, 2, 3, 4]`. Note that `advanceUntilIdle()` is `@ExperimentalCoroutinesApi` in kotlinx-coroutines-test 1.11.0 (the compiler warns), so the test file needs `@OptIn(ExperimentalCoroutinesApi::class)`.
- **E6. FX quote stream (lesson 4, payments flavor).** A rate feed emits every 100 ms and repricing takes 300 ms. Implement three strategies: keep every rate (`buffer`), latest rate only (`conflate`), and cancel stale repricing (`mapLatest`). Assert under virtual time: totals 1000/700/600 ms for 3 ticks and repriced values `[1,2,3]`/`[1,3]`/`[3]`. Then a fourth tick test: explain why `collectLatest` is wrong for "post a ledger entry per rate" (a half-done side effect). (Numbers verified for 3 ticks.)
- **E7. Slow cleanup in collectLatest (lesson 4).** A collectLatest block whose cancellation path does a 50 ms `NonCancellable` cleanup. Assert the producer's third emit happens at t=350, not 300, and the whole run ends at 700 (D13).
- **E8. Move only the blocking part (lesson 3).** A "settlement file reader" flow does blocking reads. Put `flowOn(ioDispatcher)` after the reader and assert (by recording `Thread.currentThread().name`, or a `CoroutineName`) that parsing runs on IO and the collector does not. In tests, pass `StandardTestDispatcher(testScheduler)` as `ioDispatcher` and assert virtual time advanced. Show that `Dispatchers.Default` there makes the test take real time (D15).
- **E9. Two producers, one sink (lesson 3).** Merge two acquirer feeds with `channelFlow { launch { a.collect { send(it) } }; launch { b.collect { send(it) } } }`. Assert every element arrives. Assert the flow completes only after both feeds complete (the builder block returns earlier). Then rewrite it with `flow { coroutineScope { launch { emit(…) } } }` and assert the "Emission from another coroutine is detected" message.
- **E10. Reactor parity table (lesson 4, optional Java/Kotlin lab).** Given D11 and D14, fill in the table that pairs each Flow operator with its Reactor equivalent and assert that the received lists match: `conflate()` ≡ `onBackpressureLatest()`, `buffer(10, DROP_OLDEST)` ≡ `onBackpressureBuffer(10, {}, DROP_OLDEST)`, `buffer(10, DROP_LATEST)` ≡ `onBackpressureBuffer(10, {}, DROP_LATEST)`, `buffer(UNLIMITED)` ≡ `onBackpressureBuffer()`. Plus one row that has no twin: `onBackpressureBuffer(10)` errors.

---

## Picture ideas (mental models for narrated animation)

- **Lesson 1: "One cook, one plate, walked to the table."** There is no conveyor. A single cook (the one coroutine) plates a dish (`emit`), walks it to the diner, and *stands there* while the diner eats (the collector's code). Only then does the cook walk back and plate the next one. Cold = a recipe card: nothing is cooked until a diner sits down, and each new diner gets a fresh cooking session. Stack view: draw it as nested boxes or Russian dolls. The diner's box sits *inside* the "emit" box, which sits inside the "flow block" box, inside "collect". A `map` adds a waiter doll between the cook and the diner, and the waiter also waits at the table. Backpressure is visible as the cook's idle time at the table.
- **Lesson 2: "The inspector at the serving hatch."** `flow { }` puts an inspector (SafeCollector) at the hatch. Every plate that passes gets three checks. Is the kitchen still open (`ensureActive`)? Is it the same kitchen and the same cook's badge as the first plate (context)? Did the diner throw the last plate back (exception transparency)? If so, the hatch is sealed and the error is read out. The library's own `map` and `filter` are trusted staff who walk past without an inspector (`unsafeFlow`). `take(n)` is a diner raising a red card with *their name* on it (the ownership marker). The card flies back up the line through each `emit`, only the diner who raised it catches it, and the cook's `finally` runs as the card passes.
- **Lesson 3: "A wall with a mailbox slot."** `flowOn(IO)` builds a wall across the kitchen. Behind the wall, a second cook (a second coroutine) on the IO shift cooks and drops plates into a mailbox (the channel, 64 slots). In front, the original diner takes them out. Two `flowOn`s = two walls and three rooms. Two adjacent `flowOn`s = one wall, labelled with the first sign that was hung. `flowOn(CoroutineName)` = repainting the sign on the same room: no wall, no mailbox. `channelFlow` = several cooks from different rooms dropping plates into one shared mailbox. Pushing a plate through the slot yourself (`withContext` around `emit`) sets off the alarm.
- **Lesson 4: "A conveyor belt with N slots."** `buffer(n)` = a belt with n slots between the two rooms. The producer stops when the belt is full (SUSPEND). The counter shows `n + 1` plates out of the kitchen: n on the belt and one in the diner's hands. `buffer(0)` = no belt, just a hatch where hands must meet (rendezvous). `conflate()` = a single plate stand where each new plate *replaces* the one standing there. `DROP_LATEST` = a full belt where the new plate falls into the bin. `DROP_OLDEST` = the oldest plate is pushed off the far end. Fusion = several short belt segments snapped into one belt with one label (the `toString()` sticker). `collectLatest` = a cashier tearing up a half-written receipt when a new order comes in. Show the cashier *finishing the shredding* before starting the new receipt, and the cook waiting at the hatch meanwhile. Reactor side by side: the same belt, but the Reactor diner sends tickets (`request(n)`) upstream, and `onBackpressureBuffer(10)` with no policy is a belt that *sounds an alarm and stops the line* when it overflows.

---

## Verified URLs

**Fetched and read in this session (HTTP 200, content checked):**
- https://kotlinlang.org/docs/flow.html: an HTML meta-refresh redirect to https://kotlinlang.org/docs/coroutines-flow.html. That page has these headings: Cold flows, Intermediate flow operators, Change the coroutine context of a cold flow with .flowOn(), Handle exceptions in flows, Flow cancellation, Emit values concurrently with channelFlow(), Hot flows… It has **no** conflate, collectLatest, cancellable or produceIn content, and it says the channelFlow buffer "can hold up to 64 values".
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/ (shows version selector 1.11.0; `interface Flow<out T>`)
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow-collector/ (`fun interface FlowCollector<in T>`)
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/buffer.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/conflate.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/collect-latest.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/produce-in.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/cancellable.html
- https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/docs/topics/flow.md: the old guide at tag 1.11.0, byte-identical to the 1.10.2 file. It has "Buffering" (1220/1071 ms), "Conflation" (758 ms), "Processing the latest value" (741 ms) and "Making busy flow cancellable".
- https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/CHANGES.md: the 1.11.0 entry (Kotlin 2.2.20; `flowOn` `ThreadContextElement` fix #4403; `SharedFlow.asFlow`; `StateFlow.collectLatest` returning `Nothing`).
- Source files at tag 1.11.0, each fetched as `https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/` + path:
  `common/src/flow/Flow.kt`, `common/src/flow/FlowCollector.kt`, `common/src/flow/Builders.kt`, `common/src/flow/Channels.kt`, `common/src/flow/internal/SafeCollector.common.kt`, `jvm/src/flow/internal/SafeCollector.kt`, `common/src/flow/internal/FlowExceptions.common.kt`, `jvm/src/flow/internal/FlowExceptions.kt`, `common/src/flow/internal/ChannelFlow.kt`, `common/src/flow/internal/FlowCoroutine.kt`, `common/src/flow/internal/Merge.kt`, `common/src/flow/internal/SendingCollector.kt`, `common/src/flow/internal/NopCollector.kt`, `common/src/flow/operators/Context.kt`, `common/src/flow/operators/Transform.kt`, `common/src/flow/operators/Limit.kt`, `common/src/flow/operators/Emitters.kt`, `common/src/flow/operators/Merge.kt`, `common/src/flow/operators/Distinct.kt`, `common/src/flow/terminal/Collect.kt`, `common/src/flow/terminal/Reduce.kt`, `common/src/channels/Channel.kt`, `common/src/channels/BufferOverflow.kt`, `common/src/channels/Produce.kt`.

**Loaded (HTTP 200) but only spot-checked for the title or signature:**
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-abstract-flow/
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-of.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/as-flow.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/map-latest.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/transform-latest.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/channel-flow.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/take.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/first.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/transform.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/on-each.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/catch.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-buffer-overflow/
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/-factory/-b-u-f-f-e-r-e-d.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/-factory/-d-e-f-a-u-l-t_-b-u-f-f-e-r_-p-r-o-p-e-r-t-y_-n-a-m-e.html
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html

**Blocked or failed (could not verify; re-check before citing):**
- https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Flux.html and https://projectreactor.io/docs/core/release/reference/: proxy refused (CONNECT 403). The Reactor facts here are behavioral only, from running reactor-core 3.8.8.
- https://github.com/Kotlin/kotlinx.coroutines/releases/tag/1.11.0: 403. The tag itself is confirmed by the raw.githubusercontent.com fetches.
- https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/docs/topics/coroutines-flow.md: 404. The rewritten guide is not in the 1.11.0 tag. The earlier notes cite it from `master`.

**Local verification setup (reproducible):** compiler classpath `kotlin-compiler-embeddable-2.4.21.jar:kotlin-stdlib-2.4.21.jar:kotlin-script-runtime-2.4.21.jar:kotlin-reflect-2.4.21.jar:kotlin-daemon-embeddable-2.4.21.jar:kotlinx-coroutines-core-jvm-1.8.0.jar:annotations-13.0.jar`. Command: `java -Xmx700m -cp <that> org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath kotlin-stdlib-2.4.21.jar:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlinx-coroutines-test-jvm-1.11.0.jar:reactor-core-3.8.8.jar:reactive-streams-1.0.4.jar -jvm-target 21 -d out X.kt`. Run with the same library jars plus `kotlin-reflect-2.4.21.jar` (needed only for `::class.isFun`). JDKs: OpenJDK 21.0.12 (default) and 25.0.5 (`/usr/lib/jvm/java-25-openjdk-amd64`) for the re-runs. All jars come from `~/.gradle/caches/modules-2/files-2.1/`.

---

## Notes for the lesson writer

- **Version anchors.** kotlinx.coroutines **1.11.0** (built with Kotlin 2.2.20 per CHANGES.md), run here with Kotlin **2.4.21**. The opt-in markers in these notes are the 1.11.0 state. Don't claim when something became stable unless you check older tags (not done here; for example, whether `produceIn` was ever `@FlowPreview` is [Unverified]).
- **Don't repeat co-07/co-09.** co-07 already says that "emit inside withContext throws 'Flow invariant is violated'" and that `asFlow()` is not cancellable. co-09 already has the 1200/1000/700/600 table. Lessons 1 to 4 of the new track should reuse those facts as the "you already know" hook and then show the *mechanism*: the stack (D2), the inspector (section 2), the second coroutine and channel (D7, debug coroutine numbers), and the fused `toString()` (D10).
- **The current kotlinlang.org guide does not cover buffering, conflation, collectLatest or busy-flow cancellation.** For an official citation, use the API pages (buffer, conflate, collect-latest, cancellable all load) or the 1.11.0-tagged `docs/topics/flow.md`. co-07's "deeper" text already says the guide dropped them, and that is confirmed.
- **Flag the conflate KDoc wording.** If you quote "Otherwise, the buffer size is unchanged", add the D10/D11 evidence that `buffer(10).conflate()` behaves like `conflate()`. That is safer than asserting the KDoc is a bug. It reads as an ambiguity, and the `buffer` KDoc ("overrides all immediately preceding buffering operators") matches the code.
- **`toString()` is a debug aid.** The `ChannelFlowOperatorImpl[capacity=30]` strings are not API and could change. Present them as "peek under the hood", and assert behavior (the ahead counts) in labs, not strings.
- **Use virtual time for anything you assert.** Real-time numbers here (plain 1237 to 1254, buffer 1028 to 1045, conflate 705 to 706, collectLatest 613 to 621, mapLatest 604 to 607 ms) come from a busy 4-core box. Present them as "about". The virtual numbers (1200/1000/700/600/600) are exact. Any `flowOn` in a test must use an injected test dispatcher, or the test runs on the real clock (D15).
- **The drain-after-cancel finding (66 / 12 values)** depends on a collector that never suspends. Frame it as "what a CPU-only collector sees" and pair it with the fix (`.cancellable()` after the buffer, or `ensureActive()`/`yield()` in the loop). Don't present it as a general leak. The numbers were deterministic only on a single-threaded dispatcher (`runBlocking`/`runTest`). With `flowOn(Dispatchers.Default)` they varied (14 to 36).
- **Payments framing that fits.** Lesson 1: a settlement-file reader that must not read ahead of the ledger writer (free backpressure). Lesson 2: why a `try/catch` around `emit` that "logs and continues" breaks the pipeline (the transparency message; the original exception survives only as text). Lesson 3: blocking acquirer SDK reads behind `flowOn(io)`, and fan-in from two acquirers with `channelFlow`. Lesson 4: FX rate repricing (`conflate`/`mapLatest` are fine) vs ledger postings (`buffer` only, never drop). The Reactor table (D14) maps it onto what they know from WebFlux/Reactor Kafka.
- **Things I did not verify:** Reactor `switchMap` vs `flatMapLatest` (not run), any Reactor docs text (the host was blocked), the exact history of when `FlowCollector` became a `fun interface`, the "scope never finishes without `ch.cancel()`" variant of D9 (inferred), and exercises E1, E2 and E4 as written (the designs were not run; their expected numbers come from the library runs).
- **Demo file names** (D1 to D15, plus Cancel2.kt, Extra.kt, StackFlowOn.kt, LabChecks.kt, E5.kt, ReactorCondensed.kt) refer to this session's scratch programs. Those files are not in the repo, so the listings above are the record. Most listings omit the `import kotlinx.coroutines.*` / `import kotlinx.coroutines.flow.*` lines, and the extra imports are named where needed.
