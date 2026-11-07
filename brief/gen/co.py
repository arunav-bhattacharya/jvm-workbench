import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = (
    "By the end of this track you can write Kotlin coroutine code that a payments service can trust. You can say what `suspend` does and doesn't do, split a request into concurrent calls that take as long as the slowest one, and keep every coroutine inside a scope that waits for it, cancels it and hears about its failures. You can put blocking and CPU work on the right dispatcher, make loops and blocking calls respond to cancellation, and let independent work fail alone with a supervisor. You can build cold flows, share hot ones with StateFlow and SharedFlow, connect workers with channels, protect shared state with a Mutex, and test all of it on virtual time. And you can bridge coroutines to CompletableFuture, Reactor and virtual threads, and choose between the three for a given service.\n\n"
    "You need everyday Kotlin, and the earlier tracks help: threads, races and locks from the first track, executors and `CompletableFuture` from the executors track, virtual threads, and Reactor's cold and hot publishers. Install JDK 25. The coroutine library is kotlinx.coroutines 1.11.0 with Kotlin 2.4.21, and the lessons say which version a fact comes from, because several rules changed recently: passing a `Job` to a builder is deprecated since 1.11, and explicit backing fields became stable in Kotlin 2.4.\n\n"
    "The labs live in `labs/coroutines`, one package per lesson (`workbench.coroutines.l01` to `l11`), all in Kotlin, with one Java test in lesson 11 that calls the Kotlin code from Java. Most stubs are buggy code with a KDoc that says what is wrong; a few are `TODO()`s. Run `./gradlew :coroutines:test --tests 'workbench.coroutines.lNN.*'` from `labs/` until it passes, and `solutionTest` to check the reference answers. Nearly every test runs on virtual time with `runTest`, so a test of a 30-second backoff finishes in milliseconds. The Try-it demos run with `./gradlew :coroutines:demo -Pmain=...`, and almost every Kotlin demo has a Java twin showing the closest Java equivalent."
)

CHEAT = """## Builders and scopes

| You want | Use |
|---|---|
| Fire and forget inside a scope | `launch { }` returns a `Job` |
| A result later | `async { }` returns a `Deferred`; `await()` it |
| Several children, wait for all, fail together | `coroutineScope { }` |
| Children that fail alone | `supervisorScope { }` |
| Run a block on another dispatcher and come back | `withContext(dispatcher) { }` |
| Block a thread until done: `main`, tests, a blocking edge | `runBlocking { }`, never inside suspend code |
| Background work owned by a class | `CoroutineScope(SupervisorJob() + dispatcher + handler)`, cancelled when the owner closes |
| Wrap a one-shot callback | `suspendCancellableCoroutine { }` with `invokeOnCancellation { }` |

The tree: a parent completes only after its children; cancellation flows down; a failure (anything but `CancellationException`) cancels the parent and siblings, unless the parent is a supervisor. `GlobalScope` and `CoroutineScope(...)` created inside a function make orphans.

## Dispatchers

| Dispatcher | For | Size |
|---|---|---|
| `Dispatchers.Default` | CPU work; the default for `launch` and `async` | one thread per core, at least 2 |
| `Dispatchers.IO` | blocking calls (JDBC, blocking SDKs) | 64 at once (or cores, if more) |
| `Dispatchers.IO.limitedParallelism(n, "name")` | one blocking resource with its own budget | n, added on top of IO's 64 |
| `Dispatchers.Default.limitedParallelism(n)` | a CPU budget | at most the core count |
| `executor.asCoroutineDispatcher()` | an existing pool or virtual threads; close it | whatever the executor allows |
| `Dispatchers.Unconfined`, `Dispatchers.Main` | library code; UI threads | not for server code |

Context: `+` merges elements, the right side wins; children inherit everything but the `Job`. Look the dispatcher up with `ContinuationInterceptor` (1.11). A `ThreadLocal` needs `asContextElement()`.

## Cancellation

| Situation | Do |
|---|---|
| A CPU loop | `ensureActive()`, `yield()` or `while (isActive)` every few hundred items |
| Catching around suspend calls | rethrow `CancellationException`; `runCatching` and `catch (e: Exception)` catch it |
| Suspending cleanup in `finally` | `withContext(NonCancellable) { release() }` |
| A deadline that is an expected outcome | `withTimeoutOrNull(d) { } ?: fallback` |
| A deadline that must fail the caller | `withTimeoutOrNull(d) { } ?: error("timed out")`; `withTimeout` inside `launch` fails quietly |
| A blocking call that should stop on cancel | `runInterruptible(Dispatchers.IO) { }`, plus the client's own timeout |
| `asFlow()` over a long collection | add `.cancellable()` |

## Exceptions

| Builder | Failure goes to |
|---|---|
| `launch` child | its parent at once |
| `async` child | its parent at once, whether or not anyone awaits |
| root `launch` (in a scope you created, or a supervisor's child) | the `CoroutineExceptionHandler` in its context, else the uncaught handler |
| root `async` | kept in the `Deferred`; `await()` rethrows it |

Handlers only work on roots. Put `SupervisorJob()` in a scope's constructor or use `supervisorScope`; `launch(SupervisorJob())` detaches the child from the tree. The first exception wins, the rest are suppressed.

## Flow

| Rule | Detail |
|---|---|
| Cold | the `flow { }` body runs once per collector, only when collected |
| Sequential | `emit` suspends until the collector is done; `take(n)` stops the producer |
| Operators | intermediate (`map`, `filter`, `onEach`, `take`) build; terminal (`collect`, `toList`, `first`) run |
| Context | `flowOn(d)` moves everything above it; `emit` inside `withContext` throws |
| Errors | `catch` sees only upstream; the collector's exceptions pass through; never `try` around `emit` |
| Endings | `onCompletion { cause -> }`: `null`, the error, or a `CancellationException` for an early stop |
| Backpressure | plain waits; `buffer()` runs ahead; `conflate()` keeps the latest; `collectLatest` cancels stale work |

## Hot streams and channels

| Type | Behavior |
|---|---|
| `StateFlow` | one current value; conflates; skips equal values; never completes |
| `SharedFlow` | broadcasts to every subscriber; `replay`, `extraBufferCapacity`, `onBufferOverflow`; default has no buffer, so `tryEmit` fails while a subscriber is busy |
| `stateIn` / `shareIn` | one shared upstream; `SharingStarted.WhileSubscribed(5_000)` starts with the first subscriber, stops 5 s after the last |
| Read-only state | `val s: StateFlow<T>` with `field = MutableStateFlow(x)` (Kotlin 2.4), or `asStateFlow()`; update with `update { }` or `compareAndSet` |
| `Channel` | a queue: each element to one receiver; rendezvous by default; close it, or `for` never ends |
| Fan-out / fan-in | N workers on one channel cap concurrency at N; close the results channel after `joinAll()` |
| `select` | first clause to complete wins (`onAwait`, `onReceive`, `onTimeout`); biased to the first |
| `callbackFlow` | `trySend` from the callback, end with `awaitClose { unregister() }` |

## Shared state and testing

| Need | Use |
|---|---|
| One counter or value | `AtomicLong`, `AtomicReference`, `MutableStateFlow.update` |
| A compound update | `Mutex.withLock { }`: suspends, fair, not reentrant; keep suspension outside it if you can |
| `limitedParallelism(1)` | serializes code only between suspension points: not a mutex |
| Fast, exact timing tests | `runTest`; `currentTime`, `advanceTimeBy`, `runCurrent`, `advanceUntilIdle` |
| Delays in the code under test | inject the dispatcher; `Dispatchers.IO` and `Default` stay real time |
| A child that must start at once | `UnconfinedTestDispatcher(testScheduler)` |
| Endless work in a test | `backgroundScope`; `advanceUntilIdle` ignores it |

## Bridges and choosing

| From | To | Use |
|---|---|---|
| `CompletableFuture` | suspend | `future.await()` (cancels the future); `asDeferred().await()` (doesn't) |
| suspend | `CompletableFuture` | `scope.future { }` with an owned scope |
| suspend | `Mono` / `Flux` | `mono { }` (cold), `flux { }`, `flow.asFlux()` |
| `Mono` / `Flux` | suspend / Flow | `awaitSingle()`, `awaitSingleOrNull()`, `publisher.asFlow()` |
| blocking Java caller | suspend | `runBlocking { withTimeout(d) { } }`, fine on a virtual thread |

Virtual threads for blocking Java code at scale; coroutines for Kotlin code that needs structured fan-out, cancellation and Flow; Reactor where a reactive stack already exists. One model per component, converted at its edges."""

RECAP = [
    "`suspend` lets a function pause without blocking its thread; the dispatcher, not `suspend`, decides which thread runs it. Wrap callbacks with `suspendCancellableCoroutine`.",
    "Every coroutine lives in a tree: parents wait for children, cancellation flows down, failures flow up. `coroutineScope` for work the caller waits for, an owned scope for work that outlives a call, never `GlobalScope`.",
    "Blocking calls go on `Dispatchers.IO` (or a `limitedParallelism` view sized to the resource), CPU work on `Default`, and `withContext` switches and comes back.",
    "Cancellation is cooperative and travels as `CancellationException`: check in CPU loops, rethrow it from every catch-all, clean up with `NonCancellable`, and use `runInterruptible` for blocking calls.",
    "A failed `launch` or `async` cancels its parent at once. Supervisors (`supervisorScope`, `SupervisorJob()` in a scope's constructor) let children fail alone; handlers only work on roots.",
    "Flows are cold and sequential: `flowOn` moves the upstream, `catch` handles only upstream errors, `onCompletion` sees every ending.",
    "StateFlow is state (conflated, deduplicated); SharedFlow is events (configure its buffer); `stateIn` with `WhileSubscribed` shares one upstream.",
    "Channels hand each element to one receiver: worker pools, pipelines and `callbackFlow` bridges, with `select` for whichever comes first.",
    "Protect compound updates with a `Mutex`, not a one-thread view, and test timing logic on virtual time with `runTest` and injected dispatchers.",
    "Bridge to Java with `future { }`, `await()`, `mono { }` and `awaitSingle()`, and choose virtual threads, coroutines or Reactor per component.",
]

QUIZ = [
    {"q": "Five coroutines in one `runBlocking` each call `Thread.sleep(100)` and print a line. About how long does the program take?",
     "options": ["About 100 ms, because coroutines run concurrently", "About 500 ms, because `Thread.sleep` blocks the one thread they share", "About 100 ms on a 4-core machine, 125 ms on 2 cores", "It doesn't compile: `Thread.sleep` is not allowed in a coroutine"],
     "answer": 1,
     "why": "`runBlocking` runs its coroutines on the calling thread, and `Thread.sleep` blocks that thread, so the five sleeps happen one after another. `delay(100)` would suspend instead and the whole thing would take about 100 ms."},
    {"q": "What happens here?\n\n```kotlin\ncoroutineScope {\n    launch { delay(100); throw IOException(\"ledger down\") }\n    launch { delay(1_000); println(\"risk done\") }\n}\n```",
     "options": ["`risk done` prints at 1 s, then the scope throws", "The exception is logged and the scope returns normally at 1 s", "At about 100 ms the second child is cancelled, `risk done` never prints, and the scope throws `IOException`", "Nothing is thrown, because `launch` swallows exceptions"],
     "answer": 2,
     "why": "A failed child cancels its parent scope, which cancels the sibling and then rethrows the original exception once every child has stopped. Nothing waits for the full second."},
    {"q": "A Kotlin service calls a blocking JDBC repository from coroutines, and Oracle's pool has 20 connections. Where should the calls run?",
     "options": ["`withContext(Dispatchers.IO.limitedParallelism(20, \"oracle\"))` inside the repository", "On `Dispatchers.Default`, because it is the default", "`withContext(Dispatchers.Default.limitedParallelism(20))`", "`Dispatchers.Unconfined`, so they start immediately"],
     "answer": 0,
     "why": "Blocking calls belong on IO, and a view of 20 matches the pool and adds to IO's 64 instead of competing with other blocking work. Default has one thread per core and must never block; a view over Default can't exceed the core count anyway."},
    {"q": "A poller runs `while (true) { runCatching { checkStatus(); delay(5_000) } }`. During shutdown its scope is cancelled. What happens?",
     "options": ["The loop ends at the next `delay`", "The JVM interrupts the thread and the loop ends", "The loop ends after the current status check", "The loop spins at full CPU: every `delay` throws at once and `runCatching` swallows it"],
     "answer": 3,
     "why": "`runCatching` catches `CancellationException` like any other `Throwable`. The coroutine stays cancelled, so each `delay` throws immediately, gets swallowed, and the loop goes round again. Rethrow `CancellationException`, or keep the `delay` outside the catch."},
    {"q": "To stop one webhook failure from cancelling the ledger write in the same request, someone writes `launch(SupervisorJob()) { webhooks.post(e) }` inside `coroutineScope`. What did they get?",
     "options": ["A supervised child that the scope still waits for", "A child detached from the tree: the scope doesn't wait for it or cancel it, and its failure goes to a handler", "A compile error", "The same as `supervisorScope`"],
     "answer": 1,
     "why": "A `Job` in a builder's context replaces the parent, so the coroutine becomes a child of a fresh SupervisorJob outside the request's tree. kotlinx.coroutines 1.11 deprecates the pattern. Use `supervisorScope { }` or a supervisor scope owned by a long-lived component."},
    {"q": "`records.map { parse(it) }.catch { emit(FALLBACK) }.collect { repo.save(it) }`. `repo.save` throws `SQLException`. What does the caller of `collect` see?",
     "options": ["The `SQLException`", "Nothing: `catch` emits `FALLBACK` and the flow continues", "An `IllegalStateException` about exception transparency", "`FALLBACK` saved in place of the failed record"],
     "answer": 0,
     "why": "`catch` only handles exceptions from above it. The save runs in the collector, below `catch`, so its exception passes straight through. Move the save into `onEach` above `catch` if the fallback should cover it."},
    {"q": "Payment transitions must reach both an audit writer and a notifier, and none may be lost when a Kafka listener thread publishes a burst of them. Which holder fits?",
     "options": ["`MutableStateFlow<Transition?>(null)`", "A cold `flow { }` that each consumer collects", "`MutableSharedFlow<Transition>(extraBufferCapacity = 64)`, publishing with a checked `tryEmit`", "`MutableSharedFlow<Transition>()` with default parameters and `tryEmit`"],
     "answer": 2,
     "why": "Events for several subscribers call for a SharedFlow, and a non-suspending publisher needs a buffer so `tryEmit` can hand values to busy subscribers. A StateFlow conflates events away, and a default SharedFlow has no buffer, so `tryEmit` fails whenever a subscriber is busy."},
    {"q": "A pricing coroutine recomputes a quote each time the cart total changes. A recompute takes 300 ms, totals change every 100 ms while the customer types, and only the latest total matters. Which operator fits?",
     "options": ["`buffer()`", "`conflate()`", "`flowOn(Dispatchers.IO)`", "`collectLatest { }`"],
     "answer": 3,
     "why": "`collectLatest` cancels the computation in progress when a new total arrives, so stale work stops at once and only the latest is finished. `conflate` skips values but still finishes every computation it starts; `buffer` computes them all."},
    {"q": "Credits run on `Dispatchers.Default.limitedParallelism(1)` and each does `val b = balance; val c = fx.convert(amount); balance = b + c`, where `fx.convert` suspends. Which change makes it correct?",
     "options": ["Mark `balance` as `@Volatile`", "Convert first, then do the read and the write together with no suspension between them (or hold a `Mutex` across all of it)", "Use `Dispatchers.Default` without the view", "Add `yield()` before the write"],
     "answer": 1,
     "why": "A one-thread view serializes code only between suspension points, so credits interleave at `fx.convert` and overwrite each other. Removing the suspension from the critical part, or holding a Mutex across it, closes the gap. `@Volatile` and `yield()` don't."},
    {"q": "A Java caller holds `f = facade.authorizeAsync(req)`, built with `scope.future { authorize(req) }`, and its `orTimeout(800, MILLISECONDS)` fires. What happens to the Kotlin coroutine?",
     "options": ["It is cancelled, because its future completed", "It keeps running, and the result is discarded", "Its thread is interrupted", "The whole facade scope is cancelled"],
     "answer": 0,
     "why": "The coroutine started by `future { }` is cancelled when its future is cancelled or otherwise completed, and `orTimeout` completes that same future exceptionally. Only that coroutine stops; the scope and its other children carry on."},
]

T = {"id": "co", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/co.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
