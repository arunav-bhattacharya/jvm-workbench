import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can read and write Project Reactor code with a clear picture of what runs when, on which thread, and how fast. You can explain the Reactive Streams contract and its demand signal, build lazy `Mono` and `Flux` chains, and pick the right operators to transform and combine streams. You can make a call to another computer survive failures with timeouts, filtered backoff and fallbacks, move blocking calls off the wrong threads, choose what to lose when a source can't slow down, share one source between many subscribers, and test all of it in milliseconds with `StepVerifier` and virtual time. The last lesson says plainly when you shouldn't use Reactor at all. One picture runs through all eight lessons: a bakery line, where an oven puts loaves on a belt and a packer at the end sends slips back saying how many more she can take. The bakery's own program, with its cake orders, its flour mill and its oven thermometer, is the running example in the code.

You need the first track (threads, races, `synchronized`), the executors track (pools, `CompletableFuture`, Little's law) and the virtual threads track, because this one keeps comparing against them. Install JDK 25. The labs use Reactor 3.8.8 and reactor-test 3.8.8 and compile with release 21, so they run on JDK 21 or later.

The labs live in `labs/reactive`, one package per lesson (`workbench.reactive.l01` to `l08`). They are in Java, and every code sample and Try-it demo also comes in Kotlin, with Kotlin `Flow` and coroutine counterparts where they exist. Timing tests use virtual time, latches and counters of calls in flight rather than sleeps. Run `./gradlew :reactive:test --tests 'workbench.reactive.lNN.*'` from `labs/` until it passes, use `solutionTest` to check the reference answers, and run the demos with `./gradlew :reactive:demo -Pmain=...`."""

CHEAT = """## The contract

| Signal | Direction | Rule | Picture it |
|---|---|---|---|
| `onSubscribe(s)` | publisher to subscriber | always first, exactly once | the oven hands the packer a pad of slips |
| `request(n)` | subscriber to publisher | demand; the publisher never sends more than requested | the packer's slip: "send me n more" |
| `onNext(item)` | publisher to subscriber | zero or more, never `null`, one at a time | a loaf on the belt |
| `onError(e)` or `onComplete()` | publisher to subscriber | at most one, and nothing after it | the oven breaks down, or the end-of-day bell |
| `cancel()` | subscriber to publisher | the only way a subscriber stops the stream | "stop sending" |

`java.util.concurrent.Flow` is the same four interfaces in the JDK. `Flux` is 0 to N items (a tray of loaves), `Mono` is 0 or 1 (one cake).

## Nothing happens until you subscribe

Picture it: building a chain fills in an order form, and `subscribe` signs it. Every signature on a cold publisher bakes a fresh cake.

| You write | The work runs |
|---|---|
| `Mono.just(call())` | once, at assembly, before anyone subscribes |
| `Mono.fromCallable(() -> call())` | once per subscription |
| `Mono.defer(() -> client.call())` | once per subscription; `client.call()` returns a publisher |

A cold publisher does its work again for each subscriber. `retry` subscribes again, so it needs a lazy source.

## Picking an operator

| You want | Use | Picture it |
|---|---|---|
| a quick synchronous change per item | `map`, `filter` | the slicer, the inspector |
| async calls, any order, capped | `flatMap(call, n)` (default n is 256) | the icing room |
| async calls, one at a time, in order | `concatMap(call)` | one decorator |
| async calls, concurrent, in input order | `flatMapSequential(call, n)` | the clerk at the exit |
| only the latest request matters | `switchMap(call)` | the customer who changes their mind |
| one result from several independent calls | `Mono.zip(a, b, c)`, with `switchIfEmpty` or `defaultIfEmpty` on each | the gift box |
| two live streams mixed / one after the other | `Flux.merge` / `Flux.concat` | two belts into one / one belt, then the next |
| a value recomputed when any input changes | `Flux.combineLatest` | the price board |

Source `3, 1, 2`, item i takes i x 100 ms: `flatMap` gives `1, 2, 3` at 300 ms, `concatMap` gives `3, 1, 2` at 600 ms, `flatMapSequential` gives `3, 1, 2` at 300 ms.

## Errors, retries, timeouts

Picture it: an error is the oven breaking down. Error operators only decide what goes in the box instead, `retry` bakes the whole order again, and `timeout` is the kitchen timer on the wait.

```java
Mono.defer(() -> mill.order(id))                          // a fresh call per attempt
        .timeout(Duration.ofMillis(500))                  // per attempt
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))   // 4 attempts: 0, 100, 300, 700 ms
                .filter(e -> e instanceof MillBusyException || e instanceof TimeoutException))
        .onErrorResume(Exceptions::isRetryExhausted, e -> Mono.just("PENDING:" + id));
```

```kotlin
Mono.defer { mill.order(id) }                             // a fresh call per attempt
    .timeout(Duration.ofMillis(500))                      // per attempt
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100))   // 4 attempts: 0, 100, 300, 700 ms
        .filter { e -> e is MillBusyException || e is TimeoutException })
    .onErrorResume(Exceptions::isRetryExhausted) { Mono.just("PENDING:$id") }
```

Errors are terminal. `retry(n)` makes n + 1 immediate attempts and rethrows the original error; `Retry.backoff` ends with `RetryExhaustedException` (jitter 0.5 by default). Skip a bad item inside a per-item `Mono`, not with `onErrorContinue`. A timeout means you stopped waiting, not that the other side said no: send the same order number on every attempt.

## Threads

| Scheduler | Threads | For | Picture it |
|---|---|---|---|
| none | the thread that subscribed, or the one that delivered the item | most operators | the worker who brought the loaf carries it on |
| `Schedulers.parallel()` | one per core | CPU work and timers; never block | a few quick hands who never stand still |
| `Schedulers.single()` | one | cheap work that must stay in order | one worker |
| `Schedulers.boundedElastic()` | up to 10 x cores, then a queue of 100,000 | blocking calls | the back room, allowed to wait on the phone |

`publishOn` moves the operators after it: a hand-over point on the belt. `subscribeOn` moves the source, wherever it is written, like the line on the order form that says who starts the oven; the one nearest the source wins. Wrap blocking calls as `Mono.fromCallable(...).subscribeOn(boundedElastic())`, with `subscribeOn` on each inner Mono. `block()` throws on `parallel` and `single` threads. `-Dreactor.schedulers.defaultBoundedElasticOnVirtualThreads=true` (Reactor 3.6+, JDK 21+) runs boundedElastic on virtual threads.

## Backpressure

| Between you and the source | The source sees |
|---|---|
| `subscribe(consumer)` or `block()` alone | `Long.MAX_VALUE` |
| `take(3)` | `3` |
| `limitRate(10)` | `10, 8, 8, ...` |
| `flatMap(call, 4)` | `4, 1, 1, ...` |

For a source that can't slow down, choose what to lose at the packer's small table:

| Operator | Picture it |
|---|---|
| `onBackpressureBuffer(n)` | a small pile, and an alarm when it overflows |
| `onBackpressureDrop(onDropped)` | extra loaves go in a bin |
| `onBackpressureLatest()` | one slot, and the newest replaces the old |
| `onBackpressureError()` | stop the line |

All of them ask the source for everything; none slows it down. Never use `onBackpressureBuffer()` without a size: it's the doorstep of fourteen loaves. `Flux.create` buffers without limit by default. Cap the calls you make with `flatMap(call, n)`, set from the smallest limit on the path.

## Sharing and Sinks

| Operator | A late subscriber gets | Disconnects | Picture it |
|---|---|---|---|
| `share()` = `publish().refCount()` | only new items | when the last one leaves | a live radio show |
| `replay(n).refCount()` | the last n, then new ones | when the last one leaves | a show that repeats its last announcement |
| `publish().autoConnect(n)` | only new items | never | waits for n listeners, never switches off |
| `cache()` | everything | never | a recorder that keeps the whole show |
| `Mono.cache(ttl)` | the value until it expires | not applicable | the price list, loaded again every ttl |

A sink is a bell anyone can ring. `Sinks.many().multicast().directBestEffort()` gives a live bell that survives having no listeners; `onBackpressureBuffer()` buffers but shuts down when its last subscriber leaves. From several threads, use `emitNext(item, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)))`; a bare `tryEmitNext` can return `FAIL_NON_SERIALIZED` and lose the item.

## Testing and debugging

Picture it: `StepVerifier` is a quality inspector with a script, and a clock she can wind forward.

```java
StepVerifier.withVirtualTime(() -> poller.awaitDone("cake-7"))   // build it inside the supplier
        .expectSubscription()                                      // before expectNoEvent
        .expectNoEvent(Duration.ofSeconds(90))
        .expectNext(DONE)
        .expectComplete()
        .verify(Duration.ofSeconds(1));                            // nothing runs without verify()
```

```kotlin
StepVerifier.withVirtualTime { poller.awaitDone("cake-7") }       // build it inside the supplier
    .expectSubscription()                                          // before expectNoEvent
    .expectNoEvent(Duration.ofSeconds(90))
    .expectNext(DONE)
    .expectComplete()
    .verify(Duration.ofSeconds(1))                                 // nothing runs without verify()
```

`TestPublisher` drives a source by hand; `PublisherProbe` proves a branch ran. `checkpoint("name")` labels errors cheaply, `log()` prints every signal, `Hooks.onOperatorDebug()` is a costly last resort.

## When to use it

One request and one reply over databases and services whose clients block: virtual threads and plain code. Streams, demand, cancellation, loss policies, and many calls composed with timeouts and retries: Reactor. Kotlin: coroutines and `Flow`, bridged by `kotlinx-coroutines-reactor`."""

RECAP = [
 "Reactive Streams is a contract of four interfaces: the subscriber asks for `n` items, the publisher never sends more, and `onError` or `onComplete` ends the stream for good. On the bakery line, that's the packer's slip.",
 "Assembly fills in an order form; subscription runs it, once per subscriber for a cold publisher. `Mono.just(call())` runs the call at assembly; `fromCallable` and `defer` run it per subscription.",
 "`flatMap` runs inners concurrently in completion order (256 at a time by default), `concatMap` one at a time in order, `flatMapSequential` concurrently in order, and `switchMap` keeps only the latest.",
 "`Mono.zip` completes empty, silently, when one source is empty. Say what empty means on each source.",
 "For calls to another computer: a lazy source, a per-attempt `timeout`, `retryWhen(Retry.backoff(...).filter(...))` (3 retries means 4 attempts), and a fallback for exhausted retries that admits \"we don't know yet\".",
 "Code runs on the thread that delivered the signal. `publishOn` moves what follows, `subscribeOn` moves the source; blocking calls go on `boundedElastic`, with `subscribeOn` on each inner.",
 "`limitRate` reshapes demand. For sources that can't slow down, pick a loss policy; `onBackpressureBuffer()` with no size only hides the backlog. Cap `flatMap` at the smallest limit of the services you call.",
 "`share`, `replay(n).refCount()` and `cache` differ in what late subscribers get and when they disconnect. Sinks need a retrying emit when several threads push.",
 "Test with `StepVerifier` and virtual time: always `verify()` with a time limit, and build the publisher inside the supplier.",
 "Use Reactor for streams and composed concurrency; for one request and one reply over blocking clients, virtual threads and plain code are simpler."
]

QUIZ = [
 {"q": "A `Flow.Subscriber` calls `request(2)` in `onSubscribe` and never requests again. Its publisher has 100 items ready. What does the subscriber receive?",
  "options": ["All 100 items, because the publisher pushes what it has", "2 items, then nothing until it requests more", "2 items, then `onComplete`", "2 items, then `onError`, because the rest were not requested"],
  "answer": 1,
  "why": "Rule 1.1: a publisher sends no more `onNext` signals than were requested. A publisher that still has items to deliver doesn't complete; it waits for more demand. A stream with unmet demand simply stalls, which is what to look for when a chain hangs."},
 {"q": "`Mono<Cake> c = Mono.just(bakeCake(order));` is built, but nothing ever subscribes to `c`. How many cakes are baked?",
  "options": ["None: nothing happens until you subscribe", "One", "One per subscriber, so none", "It depends on the scheduler"],
  "answer": 1,
  "why": "`Mono.just` takes a value, so Java evaluates `bakeCake(order)` before `just` is even called: the cake is baked at assembly. \"Nothing happens until you subscribe\" is true of the work inside operators and `fromCallable`, not of arguments you compute yourself."},
 {"q": "Source `3, 1, 2`; each item i is turned into a call that takes i x 100 ms. What does `concatMap` emit, and when is it done?",
  "options": ["`1, 2, 3`, done at 300 ms", "`3, 1, 2`, done at 300 ms", "`3, 1, 2`, done at 600 ms", "`1, 2, 3`, done at 600 ms"],
  "answer": 2,
  "why": "`concatMap` runs one call at a time in source order, so it takes 300 + 100 + 200 = 600 ms. `flatMap` would give `1, 2, 3` at 300 ms (completion order), and `flatMapSequential` `3, 1, 2` at 300 ms (concurrent, but put back in order)."},
 {"q": "The cake search box on the bakery's website sends a lookup on every keystroke. Results of an older query must never overwrite newer ones. Which operator fits?",
  "options": ["`flatMap`", "`concatMap`", "`switchMap`", "`flatMapSequential`"],
  "answer": 2,
  "why": "`switchMap` cancels the previous lookup as soon as a new keystroke arrives, so only the latest query can produce results. `flatMap` lets a slow old query land after a newer one; `concatMap` and `flatMapSequential` would wait for every old query, in order."},
 {"q": "`Mono.zip(price, deliveryFee, discount)`: `discount` completes empty because this customer has no discount. What does the zip do?",
  "options": ["Fails with `NoSuchElementException`", "Emits a tuple with `null` for the discount", "Waits for a discount that never comes", "Completes empty, with no error, and cancels the other calls"],
  "answer": 3,
  "why": "An empty source gives the zip nothing to combine, so it completes empty at once and cancels the rest. Nothing is logged. Put `switchIfEmpty(Mono.error(...))` or `defaultIfEmpty(...)` on each source that can be empty."},
 {"q": "`Mono.defer(() -> mill.order(id)).retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0))` against a mill whose ordering service always fails. What happens?",
  "options": ["3 calls, then the mill's exception", "4 calls at 0, 100, 300 and 700 ms, then `RetryExhaustedException` with the mill's exception as its cause", "4 calls 100 ms apart, then the mill's exception", "An endless loop of calls"],
  "answer": 1,
  "why": "The 3 counts retries, so there are 4 attempts, with waits of 100, 200 and 400 ms. When the retries run out, `Retry.backoff` signals `RetryExhaustedException` (\"Retries exhausted: 3/3\"). Plain `retry(3)` would also make 4 attempts, with no waits, and rethrow the original error."},
 {"q": "`Flux.fromIterable(shops).flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s))).subscribeOn(Schedulers.boundedElastic())` asks a blocking stock book about 50 shops, 20 ms each. About how long does it take?",
  "options": ["About 20 ms: flatMap runs them all at once", "About 1 second: all 50 run in turn on one thread", "About 250 ms: one thread per core", "It fails: blocking is not allowed on boundedElastic"],
  "answer": 1,
  "why": "`subscribeOn` on the outer Flux puts the whole subscription on one boundedElastic thread, and each `fromCallable` runs its call when `flatMap` subscribes to it, on that same thread. Put `subscribeOn(boundedElastic())` on each inner Mono, and cap the fan-out with `flatMap`'s concurrency."},
 {"q": "Orders arrive from the website over a live connection that can't slow down. No order may be lost silently, and bursts of a few hundred are normal. Which line fits?",
  "options": ["`orders.onBackpressureBuffer()`", "`orders.onBackpressureLatest()`", "`orders.onBackpressureBuffer(1_000, o -> log.error(\"overflow at {}\", o.id()))`", "`orders.limitRate(100)`"],
  "answer": 2,
  "why": "A bounded buffer absorbs the bursts, and if the consumer falls further behind, it cancels the source, logs the overflowing order and fails, so the gap is visible. The unbounded buffer hides the backlog until memory runs out, `onBackpressureLatest` drops orders silently, and `limitRate` changes requests that this source ignores."},
 {"q": "Twelve screens share one connection to the oven thermometer. A screen that switches on late must show the current temperature at once, and the connection must close when nobody watches. Which operator fits?",
  "options": ["`readings.replay(1).refCount()`", "`readings.share()`", "`readings.cache()`", "`readings.publish().autoConnect(1)`"],
  "answer": 0,
  "why": "`replay(1)` hands a late subscriber the latest reading, and `refCount()` cancels the source when the last subscriber leaves. `share()` makes a late screen wait for the next reading; `cache()` and `autoConnect` never disconnect, and `cache()` keeps every reading forever."},
 {"q": "A test builds `Mono<Status> poll = poller.awaitDone(\"cake-7\");` in `@BeforeEach`, then runs `StepVerifier.withVirtualTime(() -> poll).thenAwait(Duration.ofMinutes(5))...verify(Duration.ofSeconds(1))`. It fails with \"VerifySubscriber timed out\". Why?",
  "options": ["Virtual time doesn't work with `Mono`", "`thenAwait` must be replaced with `Thread.sleep`", "`verify` needs a longer timeout, such as 5 minutes", "The Mono was built before virtual time was installed, so its timers use the real clock"],
  "answer": 3,
  "why": "Operators such as `interval`, `delay` and `timeout` pick their scheduler when the chain is built. Built in `@BeforeEach`, the poller's timers run on the real `parallel` scheduler, and winding the virtual clock forward does nothing. Call `poller.awaitDone(\"cake-7\")` inside the supplier. A 5-minute real timeout would just make the test slow."}
]

T = {"id": "rx", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/rx.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
