# Track: flow, "Kotlin Flow in depth" (lab: labs/flows, package workbench.flows.lNN)

Research notes: "research_notes/Kotlin Flow in depth/" (flow_internals_buffering.md for lessons 1 to 4,
flow_operators_errors.md for lessons 5 and 6, flow_hot_bridges_testing.md for lessons 7 and 8). They are your
source of truth: exact 1.11.0 signatures and stability annotations, exact exception messages, misconceptions,
demo programs with observed output, lab ideas checked under virtual time, and "picture" ideas. Anything they mark
[Unverified] must not be stated as fact. Read the "Notes for the lesson writer" section of each file you use.

Who this track is for: the same senior engineer, who has just finished the Kotlin coroutines track. That track
already has a short Flow introduction: co-07 (cold flows, operators, flowOn vs withContext, catch/onCompletion),
co-08 (StateFlow, SharedFlow, stateIn/shareIn) and co-09 (channels, callbackFlow/channelFlow, a
buffer/conflate/collectLatest table). Skim those three lessons first. Do not re-teach their surface: use what they
taught as the "you already know" hook, then go one level down to the mechanism, so the reader can predict variants
nobody showed them. Refer to them as "lesson 7 of the coroutines track", and so on.

First principles, intuition first. Every lesson opens with a small payments program whose behaviour surprises
(a print order, a timing, a lost value, an exception), lets the reader predict it, then builds the mechanism that
explains it, usually by writing a small version by hand before showing what the library does. Name a concept only
after the reader has felt why it exists. Use the notes' "picture" ideas in prose and figures so the reader leaves
with a model they could redraw. Follow brief/BRIEF.md (especially "Novice on the topic, taught from first
principles" and "Voice: blog mode, human, simple") and the human-writing skill it links: blog mode, very simple
English, short sentences, no em or en dashes, no banned words, take positions.

Both languages: labs are Kotlin. Every code sample in the prose still comes as a Kotlin and Java pair. Flow has no
Java twin, so the Java side is the closest Java equivalent, with a first-line comment that says so: a hand-written
push "flow" with a Consumer (lesson 1), Reactor Flux operators (lessons 4 to 6 and 8: concatMap, flatMap, switchMap,
zip, combineLatest, onBackpressureBuffer/Latest, retryWhen, timeout), a BlockingQueue between two threads (the
channel behind flowOn and buffer), or Java calling the Kotlin API through Flux/Publisher (lesson 8). Where nothing
fits, use a `solo` fence (at most 3 per lesson, as the validator allows).

Versions: Kotlin 2.4.21, kotlinx.coroutines 1.11.0 (core, test, reactive, reactor), Reactor 3.8.8, JUnit 6.1.3,
AssertJ 3.27.7. Dependencies already in labs/flows/build.gradle.kts: kotlinx-coroutines-core, -reactive, -reactor,
reactor-core, and for tests kotlinx-coroutines-test, reactor-test and Turbine 1.2.1. Don't add others. Package per lesson:
workbench.flows.l01 .. l08. Tests must use virtual time (runTest, advanceTimeBy, currentTime) for anything about
timing, and inject dispatchers instead of using Dispatchers.IO/Default inside runTest (the notes show
flowOn(Dispatchers.Default) inside runTest runs on the real clock). Opt-ins (@OptIn(ExperimentalCoroutinesApi::class),
@FlowPreview) exactly as the notes list them for 1.11.0; say in the prose when an API is experimental or preview.

Lessons:
- flow-01 A flow from scratch: two interfaces and a function call. Open with a settlement-file reader and a ledger
  writer: predict the print order of "read", "posted" lines. Build ToyFlow/ToyCollector and a 3-line builder by
  hand (notes D1): building runs nothing, collecting twice runs the body twice, and each emit returns only after
  the collector's code finished. Print the stack from inside collect (D2): the collector runs inside emit. Derive
  the three properties from that call shape: cold, sequential, backpressure for free (100 ms producer, 300 ms
  collector: emit 2 happens at t=500). Then the real interfaces (Flow is not a fun interface, FlowCollector is),
  and operators on the toy: map and filter are collectors wrapped in collectors. Lab (notes E1): the toy flow with
  map, filter and take; tests for laziness, re-running, the exact event order, and take stopping the producer with
  its finally run. Java twin for the toy: the same push shape with Consumer, which blocks a thread where Kotlin
  suspends; mention java.util.concurrent.Flow (Reactive Streams) only to say it pulls with request(n) instead.
- flow-02 Inside flow { }: the three checks, and how operators are built. What flow { } adds over the toy:
  SafeFlow, AbstractFlow and SafeCollector, and the three checks on every emit: ensureActive, same context
  ("Flow invariant is violated", exact text), exception transparency (exact text; the original exception survives
  only as message text). Why the library's own map/filter/take/flowOf/asFlow use unsafeFlow, and what that means:
  flowOf and asFlow are not cancellable between items; cancellable() fixes it (the notes' six-flow table).
  How take and first stop the producer: AbortFlowException with an owner marker, so the producer's finally runs.
  The payments trap: a try/catch around emit that "logs and continues". Lab (notes E2 and E3): a small
  SafeCollector-lite that enforces context and transparency on the toy flow, plus a predict-then-assert test of
  which flows stop when the collector cancels.
- flow-03 Context and threads: flowOn, the invariant, and channelFlow. Why emit inside withContext is forbidden:
  the collector's code runs inside emit, so it would run on the wrong thread. What flowOn really builds: a second
  coroutine and a channel (ChannelFlow; the stack after flowOn shows emitAllImpl draining it), which side it
  changes (upstream only), several flowOn calls (rooms and walls), adjacent ones fuse, flowOn(CoroutineName) makes
  no channel. channelFlow for emitting from several coroutines (and the exact error when you try that with
  flow { }), produceIn. Testing: inject the dispatcher. Lab (notes E8 and E9): move only the blocking reader of a
  settlement file behind flowOn(ioDispatcher), asserting which side ran where; then fan in two acquirer feeds with
  channelFlow and show the flow { } version fails with the exact message.
- flow-04 Buffering: buffer, conflate, collectLatest and fusion. The 100/300 ms model in virtual time
  (1200/1000/700/600), then the mechanism: a belt with n slots, so n + 1 emits return while the collector holds
  item 1; buffer() is 64 (Channel.BUFFERED and its system property); overflow policies and the verified surprises
  (DROP_OLDEST with no capacity keeps 1; buffer(10).conflate() acts like conflate()); fusion shown with toString()
  as a peek under the hood, asserted by behaviour; collectLatest waits for the cancelled block's cleanup; a
  CPU-only collector that cancels keeps draining the buffer, and cancellable() after the buffer fixes it. Payments
  framing: FX repricing can conflate or use mapLatest; ledger postings must never drop. Reactor table (notes D14):
  conflate = onBackpressureLatest, buffer(n, DROP_OLDEST) = onBackpressureBuffer(n, ..., DROP_OLDEST), and
  onBackpressureBuffer(n) with no policy errors. Lab (notes E5 and E6): the "ahead" helper and three FX repricing
  strategies asserted in virtual time.
- flow-05 Flattening and combining: flatMap, zip and combine. Use flow_operators_errors.md. flatMapConcat,
  flatMapMerge (concurrency, DEFAULT_CONCURRENCY and its property, ordering) and flatMapLatest, with timelines from
  the notes' virtual-time demos; zip (pairs by index, ends with the shorter) vs combine (latest of each, when it
  first emits, what it drops for a slow collector); merge. Stability annotations as the notes give them. Reactor
  twins (concatMap, flatMap, switchMap, zip, combineLatest, merge) and where semantics differ. Payments examples:
  fan out to fee lookups with bounded concurrency, merchant search-as-you-type, an FX rate stream combined with a
  price stream. Lab from the notes' exercise ideas, in virtual time.
- flow-06 Errors, completion, retries and timeouts. Use flow_operators_errors.md. Exception transparency as the
  rule behind catch (only upstream), where to put catch, what a downstream exception in collect does, onCompletion
  and its cause (success, failure, cancellation), retry and retryWhen with attempt and exponential backoff,
  timeout (stability and exception as the notes give them), first/single/firstOrNull and their messages, catch and
  CancellationException, onEach + launchIn. The flaky provider pattern: retry with backoff, then fall back, verified.
  Reactor twins (onErrorResume, retryWhen(Retry.backoff), timeout). Lab: a flaky acquirer feed with retries,
  backoff and a fallback, asserted in virtual time, including the cancellation case.
- flow-07 Hot flows in depth: SharedFlow, StateFlow and sharing. Use flow_hot_bridges_testing.md.
  MutableSharedFlow(replay, extraBufferCapacity, onBufferOverflow): exactly when emit suspends and tryEmit returns
  false, what a late subscriber sees; StateFlow's equality conflation, a slow collector skipping values,
  update { } vs value = value + 1 under contention, compareAndSet; subscriptionCount; stateIn and shareIn with
  Eagerly, Lazily and WhileSubscribed(stopTimeoutMillis, replayExpirationMillis), including whether the upstream
  restarts when the last subscriber leaves and returns inside or after the timeout; scope leaks. Server examples:
  an FX rate shared by many requests, a config value. Reactor twins (Sinks, share(), replay(1).refCount()).
  Lab: an FX rate cache built with shareIn/stateIn, with tests on upstream start counts in virtual time.
- flow-08 Bridges and tests: callbackFlow, Reactor and runTest. Use flow_hot_bridges_testing.md. callbackFlow
  with awaitClose (the exact error without it), trySend vs send and the buffer for a fast callback, wrapping a
  made-up payment-gateway listener; Flow and Reactor: Publisher.asFlow, Flow.asPublisher, asFlux, Flux.asFlow, how
  request(n) maps to suspension, the default buffer, context; how Java code consumes a Kotlin Flow (as a Flux or
  Publisher). Testing flows: runTest and virtual time, backgroundScope, StandardTestDispatcher vs
  UnconfinedTestDispatcher, collecting a StateFlow without missing values, toList with take, the backgroundScope
  traps the notes found (advanceUntilIdle skips it; advanceTimeBy(100) doesn't run a task due at exactly +100).
  Turbine 1.2.1 is a test dependency of labs/flows (testImplementation only): teach test { awaitItem() ... } and
  turbineScope, and say when not to use it (it collects eagerly, so it sees every StateFlow value and hides
  conflation). Lab: wrap a listener API in callbackFlow (unregister on cancel, no lost
  events with a buffer), expose it to Java as a Flux, and test both with runTest and StepVerifier.

Track file content/tracks/flow.json: intro (what the reader can do at the end; it assumes the coroutines track),
a cheatsheet (the two interfaces and the three checks, an operator picker for buffering, flattening and combining,
hot flow and SharingStarted settings, a Flow-to-Reactor table, testing recipes), recap, and a 10-question quiz
mixing all eight lessons.
