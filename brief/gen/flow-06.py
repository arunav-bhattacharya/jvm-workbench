import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/flows/src"
P = "kotlin/workbench/flows/l06"
J = "java/workbench/flows/l06"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :flows:demo -Pmain=workbench.flows.l06.{cls}{extra}"
API = "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt"), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 680 318" role="img" aria-label="catch drawn as a net between the upstream and the downstream. '
    'An IOException and a TimeoutCancellationException thrown by the upstream fall into the net and are caught. '
    'The cancellation of the collecting job passes through the net to the caller. A failure in the collector starts '
    'below the net and goes straight to the caller.">'
    '<text class="t-s t-m" x="340" y="22" text-anchor="middle">what reaches the catch action, and what passes it</text>'
    '<rect class="box-a" x="20" y="40" width="290" height="76" rx="8"/>'
    '<text class="t" x="165" y="68" text-anchor="middle">upstream</text>'
    '<text class="t-s t-code" x="165" y="94" text-anchor="middle">provider call, map { }, withTimeout</text>'
    '<line class="ln-d" x1="20" y1="150" x2="660" y2="150"/>'
    '<text class="t t-code" x="165" y="142" text-anchor="middle">catch { }</text>'
    '<rect class="box-b" x="20" y="178" width="290" height="60" rx="8"/>'
    '<text class="t" x="165" y="202" text-anchor="middle">downstream</text>'
    '<text class="t-s t-code" x="165" y="224" text-anchor="middle">collect { ledger.post(it) }</text>'
    '<rect class="box" x="20" y="266" width="640" height="36" rx="8"/>'
    '<text class="t" x="340" y="289" text-anchor="middle">the caller of collect()</text>'
    '<text class="t-s" x="375" y="56" text-anchor="middle">IOException</text>'
    '<line class="ln-a" x1="375" y1="64" x2="375" y2="144" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="375" y="170" text-anchor="middle">caught</text>'
    '<text class="t-s" x="460" y="56" text-anchor="middle">withTimeout</text>'
    '<line class="ln-a" x1="460" y1="64" x2="460" y2="144" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="460" y="170" text-anchor="middle">caught</text>'
    '<text class="t-s" x="545" y="56" text-anchor="middle">job.cancel()</text>'
    '<line class="ln-bad" x1="545" y1="64" x2="545" y2="262" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="552" y="172">passes</text>'
    '<text class="t-s" x="630" y="196" text-anchor="middle">ledger fails</text>'
    '<line class="ln-bad" x1="630" y1="204" x2="630" y2="262" marker-end="url(#arr)"/>'
    '</svg>'
)

S1 = """An FX rate flow calls a slow provider inside `withTimeout(50)`, and a `catch` below it emits a fallback rate. The provider takes 100 ms. Most people expect the timeout to fly past the `catch`, because "catch doesn't handle cancellation" and a timeout is a `CancellationException`. Run it, then run a second version where the caller's own job is cancelled instead:

```kotlin
flow { emit(cachedRate); emit(withTimeout(50) { provider.call() }) }   // the call takes 100 ms
    .catch { e -> emit(fallbackRate) }
    .collect { show(it) }                 // case 2: the request scope calls job.cancel() meanwhile
```

```java
// Closest Java equivalent: onErrorResume handles what comes from above it; dispose() is a cancel signal
Flux.concat(Flux.just(cachedRate), provider.call().timeout(Duration.ofMillis(50)))
    .onErrorResume(e -> Mono.just(fallbackRate))
    .subscribe(this::show);               // case 2: the subscription is disposed meanwhile
```

Here is what the Try it prints for five ways the request can end:

| How it ends | The `catch` action runs | The caller sees |
|---|---|---|
| the provider throws `IOException` | yes | nothing |
| the provider throws `CancellationException` | yes | nothing |
| `withTimeout` fires inside the provider call | yes, with `TimeoutCancellationException` | nothing |
| the collector's ledger write fails | no | `IllegalStateException: ledger write failed` |
| the caller's job is cancelled | no | `JobCancellationException` |

You know from lesson 2 of this track that an exception thrown by the collector comes back out of `emit`, up into the upstream's code, and that emitting again after that breaks exception transparency. So when the upstream's `collect` throws, `catch` has to work out who threw. Build it by hand and the rule falls out:

```kotlin
fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T> = flow {
    var fromDownstream: Throwable? = null
    try {
        collect { value -> try { emit(value) } catch (e: Throwable) { fromDownstream = e; throw e } }
    } catch (e: Throwable) {
        if (e === fromDownstream) throw e                                              // below the net
        if (e is CancellationException && !currentCoroutineContext().isActive) throw e // our job is cancelled
        action(e)                                                                      // an upstream failure
    }
}
```

```java
// Closest Java equivalent: the same bookkeeping around a push-style source and a Consumer
static <T> void myCatch(Consumer<Consumer<T>> upstream, Consumer<T> downstream, Function<Throwable, T> action) {
    RuntimeException[] fromDownstream = {null};
    try {
        upstream.accept(v -> { try { downstream.accept(v); } catch (RuntimeException e) { fromDownstream[0] = e; throw e; } });
    } catch (RuntimeException e) {
        if (e == fromDownstream[0]) throw e;                                   // below the net
        if (Thread.currentThread().isInterrupted()) throw e;                   // our own task was cancelled
        downstream.accept(action.apply(e));                                    // an upstream failure
    }
}
```

The library's `catch` does the same bookkeeping. It wraps the downstream `emit`, remembers what came out of it, and rethrows that. It also rethrows when the exception is the cancellation cause of the collecting job. Everything else goes to your action. Picture a **net under the upstream half of the pipe**. Anything that falls from above lands in it, including a `CancellationException` the upstream throws while the job is still active. The job's own cancellation passes through, and whatever the collector drops falls below the net, straight to the caller.

So `catch` ignores the cancellation of the collector, not every `CancellationException`. For a provider call that is usually what you want: a timeout becomes a fallback. If not, rethrow `CancellationException` in the action. And the net only covers what is above it. Move the ledger write into `onEach` above the `catch` and call `collect()` with no lambda, or `launchIn(scope)`. A caught error still ends the upstream: `flowOf(1, 2, 3).map { fails on 2 }.catch { emit(-1) }` gives 1 and -1, and 3 is never produced.

Check yourself: `catch` sits above `map`, and `map` throws. Who handles it?"""

S2 = """The acquirer's settlement feed resets after payment-2 on the first attempt, and the import wraps it in `retry(3)`. What does the ledger receive?

```kotlin
val received = feed.retry(3).toList()
// [payment-1, payment-2, payment-1, payment-2, payment-3]
```

```java
// Closest Java equivalent: retry re-subscribes, so a cold Flux replays from the top too
List<String> received = Flux.defer(acquirer::feed).retry(3).collectList().block();
// [payment-1, payment-2, payment-1, payment-2, payment-3]
```

Two payments posted twice. `retryWhen` is a loop around the same bookkeeping as `catch`. When the upstream fails with an exception that came from above the net, it calls your predicate with the cause and an attempt number. If the predicate says yes, it collects the upstream again, and a cold flow is a recipe: collecting it again runs it again from the top. Values that were already emitted are emitted again. Picture rewinding a tape: everything already played plays again.

The counting follows from the loop. `retry(n)` is `retryWhen { cause, attempt -> attempt < n && predicate(cause) }`, so `retry(2)` on a flow that always fails collects it 3 times, and then the third exception comes out. `retry(0)` fails when you build the flow with `Expected positive amount of retries, but had 0`. The default is `Long.MAX_VALUE`, which retries forever. `attempt` is 0 on the first failure, and with `retry(n, predicate)` the predicate is no longer called once the attempts run out.

A backoff is a `delay` inside the predicate:

```kotlin
feed.retryWhen { cause, attempt ->
    val retry = cause is IOException && attempt < 3
    if (retry) delay(100L shl attempt.toInt())        // 100, 200, 400 ms
    retry
}
```

```java
// Closest Java equivalent: Reactor's backoff spec (jitter off, so the times are exact)
feed.retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0)
        .filter(e -> e instanceof IOException));
```

Against a call that always fails, both collect at 0, 100, 300 and 700 ms. Then they differ. Flow gives up by letting the original `IOException` out. Reactor wraps it in a `RetryExhaustedException` (`Retries exhausted: 3/3`, the real error as its cause), and in production it adds jitter (0.5 by default, from lesson 5 of the reactive track). Flow has no jitter, no cap and no exhaustion type. You write those yourself, which is what the lab does.

Like `catch`, a retry never fires for an exception the collector threw or for the caller's own cancellation. It does fire for a `TimeoutCancellationException` from a `timeout()` above it, and the last section builds on that.

The replay is the part that hurts in payments. Every consumer after a retry must be idempotent. De-duplicate by payment id (one set per collection), or make the source resumable from a cursor or a Kafka offset, so a retry starts where the last attempt stopped.

Check yourself: `retry(3)` on a stream that fails after its second element on every attempt. How many times does the collector see element 1?"""

S3 = """A metrics hook counts each FX lookup as a success or a failure. Lookups go through `first()`. In the dashboard, every lookup is a failure:

```kotlin
rates(pair)
    .onCompletion { cause -> if (cause == null) metrics.ok() else metrics.failed(cause) }
    .first()
```

```java
// Closest Java equivalent: doFinally reports a signal type instead of a cause
rates(pair)
    .doFinally(signal -> { if (signal == SignalType.ON_COMPLETE) metrics.ok(); else metrics.failed(signal); })
    .next()
    .block();
```

`onCompletion` is a `try`/`finally` around the upstream, placed exactly where you wrote it. It runs once, and its `cause` says what passed through that position on the way out:

| How the flow ended | `cause` |
|---|---|
| completed normally | `null` |
| the upstream threw | `IOException: provider reset` |
| the collector threw | `IllegalStateException: ledger write failed` |
| a `map` below threw, and a `catch` below that swallowed it | `IllegalStateException: map failed` |
| above `take(1)` or `first()` | `AbortFlowException: Flow was aborted, no more elements needed` |
| below `take(1)` | `null` |
| the collecting job was cancelled | `JobCancellationException: StandaloneCoroutine was cancelled` |

`first()` stops the upstream the way lesson 2 of this track described: it throws `AbortFlowException`, a `CancellationException`, out of the upstream's `emit`. Everything above it sees that exception go by, so the hook counts a stopped flow as a failed one. Below `take(1)` the flow just ended, so the cause is `null`. Picture a bell at the end of the line that rings once with a tag. The tag "aborted, no more needed" is only visible to stations above the `take`. The fix is to classify in order: `null` is success, a `CancellationException` is cancelled or stopped early, anything else is a failure.

`onCompletion` can emit, but only on success: `flowOf("a", "b").onCompletion { if (it == null) emit("Done") }` gives a, b, Done. After a failure, `emit` throws the original cause again. Use `catch` to emit a replacement.

The terminal operators fail in specific ways, and they stop the upstream at different points. `first()` on an empty flow throws `NoSuchElementException: Expected at least one element`. `single()` throws `NoSuchElementException: Flow is empty`, or `IllegalArgumentException: Flow has more than one element`. On a three-element flow, `first()` pulls 1 element and `single()` pulls 2 before it fails. Reactor's `single()` says `Source was a (constant) empty` and throws `IndexOutOfBoundsException: Source emitted more than one item` instead.

Check yourself: `onCompletion` sits below `take(1)`, and the collector throws on the first element. What is `cause`?"""

S4 = """Put it together for a provider that has stopped answering. Each call takes 1,000 ms. The chain gives every call 300 ms, retries with backoff and then falls back. When does the fallback answer?

```kotlin
primary.rate(pair)
    .timeout(300.milliseconds)            // per attempt; @FlowPreview
    .retryWithBackoff()                   // 3 retries: 100, 200, 400 ms
    .catch { e -> if (!isTransient(e)) throw e; emitAll(fallback.rate(pair)) }
```

```java
// Closest Java equivalent: the Reactor chain from lesson 5 of the reactive track
primary.rate(pair)
    .timeout(Duration.ofMillis(300))
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0).filter(this::isTransient))
    .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e), e -> fallback.rate(pair));
```

The calls start at 0, 400, 900 and 1,600 ms, and each one is cut at +300. At 1,900 ms the primary gives up with `Timed out waiting for 300ms`, and the fallback answers at 1,930. Reactor's chain prints the same times in real time.

`timeout(d)` arrived in 1.7.0 and is still `@FlowPreview` in 1.11.0. It takes a `Duration` only. It runs the upstream in a producer coroutine and arms a timer only while it waits for the next upstream value. Time the downstream spends on a value doesn't count, but the wait for the first value does. Picture a watchdog egg timer, wound each time the operator starts waiting, paused while the collector is busy. When it rings it throws `TimeoutCancellationException`, and that is a `CancellationException`.

That one fact explains the rest of the chain. The timeout comes from above `retryWhen` while the job is active, so `retryWhen` can retry it, but only if `isTransient` lists `TimeoutCancellationException`, because a timeout is not an `IOException`. Position sets the meaning: above `retryWhen` it limits each attempt, below it limits the whole sequence, waits included. Add `.timeout(1.seconds)` after the retries and the same provider gets calls at 0, 400 and 900, the budget fires at 1,000, and the fallback answers at 1,030. The `catch` at the end filters on `isTransient`, so a bad pair (`IllegalArgumentException`) reaches the caller at 20 ms with no retry and no fallback. And when the fallback fails too, the caller sees the fallback's error. The primary's error is not attached.

The cancellation nature bites when the flow runs in the background. Uncaught inside `launch` or `launchIn`, a timeout just ends that coroutine as cancelled. No `CoroutineExceptionHandler` runs, and the parent scope keeps going, because handlers ignore `CancellationException`. Your FX refresher stops and nobody hears it. Translate it at the edge: `.catch { e -> if (e is TimeoutCancellationException) throw ProviderTimeout(e) else throw e }`, and the handler gets `ProviderTimeout` with the timeout as its cause. Reactor's `timeout` signals `java.util.concurrent.TimeoutException`, which is an ordinary error, so the trap doesn't exist there.

Two notes for tests. Under `runTest`, `withTimeout` has a different message ("Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time..."), so assert on the exception type, never the text. And `TimeoutCancellationException` has no public constructor, so produce one with a real `timeout()` under virtual time, as the lab does.

Check yourself: where does `.timeout(1.seconds)` go to be a per-attempt limit instead of a budget?"""

L = {
 "id": "flow-06",
 "title": "Errors, completion, retries and timeouts",
 "minutes": 38,
 "goal": "By the end you can say which exceptions a catch handles and which pass it, predict what a retry replays, read onCompletion's cause, and build a provider call with a per-attempt timeout, backoff and a fallback that a cancelled caller still stops.",
 "warmup": {
  "q": "An FX flow emits a cached rate, then calls a provider inside `withTimeout(50)`. Below it sits `.catch { emit(fallbackRate) }`. The provider takes 100 ms. What does the collector get?",
  "options": [
   "The cached rate, then the timeout escapes, because catch never handles a CancellationException",
   "The cached rate, then the fallback rate",
   "Nothing at all: the timeout cancels the collector",
   "The cached rate, and then the flow completes normally with nothing else"
  ],
  "answer": 1,
  "why": "`withTimeout` throws `TimeoutCancellationException` inside the upstream while the collecting job is still active. To `catch` that is an upstream failure like any other, so the action runs and emits the fallback. What `catch` lets pass is the cancellation of the collecting job itself, and exceptions thrown below it."
 },
 "sections": [
  {
   "h": "A catch is a net under the upstream, and it checks who threw",
   "body": S1,
   "figure": {"svg": FIG, "caption": "catch handles what falls from above it, CancellationException included, except the cancellation of the collecting job. The collector's failures start below the net."},
   "try": {
    "title": "Five ways to end a rate request",
    "minutes": 4,
    "steps": [
     "Open `CatchNet.kt`. For each of the five cases, predict whether the net catches it and what the caller sees.",
     "Run it. Each case runs twice: once with the library's `catch`, once with `myCatch` from this section. Check that the two lines always agree.",
     "In `myCatch`, delete the line that rethrows `fromDownstream` and run again. Which case changes, and what does the caller see now?",
     "Run `CatchNetJava`, the `onErrorResume` twin. Find the case where moving the ledger write above the net changes the result."
    ],
    "code": tryit("CatchNet.kt", "CatchNetJava.java"),
    "expect": "The first three cases get `[0.92, -1.0]` and the caller sees nothing: the net caught an `IOException`, a `CancellationException` and a `TimeoutCancellationException` (\"Timed out waiting for 50 ms\"). The ledger failure and the job cancellation pass: the caller sees `IllegalStateException: ledger write failed` and `JobCancellationException`. `catch` and `myCatch` agree on every line. Without the `fromDownstream` check, the ledger case runs the action and emits again after the downstream failed, and the flow throws `IllegalStateException: Flow exception transparency is violated`. In Reactor, the ledger write fails the stream when it sits below `onErrorResume` and is handled when it sits above it."
   },
   "refs": [
    {"title": "catch (kotlinx.coroutines API)", "url": API + "catch.html", "kind": "docs"},
    {"title": "Flows: exceptions, catch and onEach (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-flow.html", "kind": "read"}
   ]
  },
  {
   "h": "A retry collects the upstream again, from the top",
   "body": S2,
   "try": {
    "title": "Rewind the tape",
    "minutes": 4,
    "steps": [
     "Open `RetryReplay.kt`. Predict what the ledger receives in the first block, and how many collections `retry(2)` makes in the second.",
     "Run it on virtual time. Check the backoff block's times against the section.",
     "Change the second block to `retry(2) { it is IllegalStateException }`. Predict the output, then run it.",
     "Run `RetryReplayJava`: the same replay in Reactor, and `Retry.backoff` in real time."
    ],
    "code": tryit("RetryReplay.kt", "RetryReplayJava.java"),
    "expect": "The ledger receives `[payment-1, payment-2, payment-1, payment-2, payment-3]`. `retry(2)` collects 3 times: `[p1, p2, p1, p2, p1, p2, FALLBACK]`, and `retry(0)` is rejected with \"Expected positive amount of retries, but had 0\". The backoff calls come at 0, 100, 300 and 700 ms, then the original `IOException` reaches the `catch`. With the predicate, an `IOException` is not retried, so you get `[p1, p2, FALLBACK]` after 1 collection. Reactor replays the same five payments, calls at about 0, 100, 300 and 700 ms, and ends with `RetryExhaustedException: Retries exhausted: 3/3`."
   },
   "refs": [
    {"title": "retryWhen (kotlinx.coroutines API)", "url": API + "retry-when.html", "kind": "docs"},
    {"title": "retry (kotlinx.coroutines API)", "url": API + "retry.html", "kind": "docs"}
   ]
  },
  {
   "h": "The onCompletion bell rings once, and its cause is not always a failure",
   "body": S3,
   "try": {
    "title": "Read the bell's tag",
    "minutes": 3,
    "steps": [
     "Open `CompletionCauses.kt`. Cover the output and write down the `cause` you expect on each line.",
     "Run it. Look at the two lines around `take(1)`, and at `above first()`.",
     "Run `CompletionCausesJava`. Which `doFinally` signal does Reactor give above `take(1)`?"
    ],
    "code": tryit("CompletionCauses.kt", "CompletionCausesJava.java"),
    "expect": "`null` for success and below `take(1)`. `IOException: provider reset` for the upstream failure, `IllegalStateException: ledger write failed` for the collector failure, `IllegalStateException: map failed` even though a `catch` below swallowed it. `AbortFlowException: Flow was aborted, no more elements needed` above `take(1)` and above `first()`, and `JobCancellationException: StandaloneCoroutine was cancelled` for `job.cancel()`. `single()` pulls 2 elements and `first()` pulls 1. Reactor reports `onComplete`, `onError`, `cancel` above `take(1)` and `onComplete` below it."
   },
   "refs": [
    {"title": "onCompletion (kotlinx.coroutines API)", "url": API + "on-completion.html", "kind": "docs"},
    {"title": "single (kotlinx.coroutines API)", "url": API + "single.html", "kind": "docs"}
   ]
  },
  {
   "h": "A timeout throws a cancellation, and its position sets its meaning",
   "body": S4,
   "try": {
    "title": "Time a flaky provider",
    "minutes": 5,
    "steps": [
     "Open `FlakyProvider.kt`. Before you run it, write down when each of cases A to E ends, and how many calls each provider gets.",
     "Run it on virtual time and compare. Case E is case B with an overall `timeout(1.seconds)` after the retries.",
     "Read the last block: the same timeout inside `launchIn`, first silent, then translated into `ProviderTimeout`.",
     "Run `FlakyProviderJava`, the Reactor version of case B, in real time."
    ],
    "code": tryit("FlakyProvider.kt", "FlakyProviderJava.java"),
    "expect": "A ends at 390 ms from the primary (3 calls). B: calls at 0, 400, 900 and 1,600, the primary gives up at 1,900 with \"Timed out waiting for 300ms\", and the fallback answers at 1,930. C: the caller sees `IllegalArgumentException` at 20 ms, with no retry. D: the caller sees `IOException: fallback down` at 800. E: the budget fires at 1,000 (\"Timed out waiting for 1s\") and the fallback answers at 1,030. In the `launchIn` block the silent version leaves the scope active and calls no handler; the loud version reaches the handler and the scope is no longer active. Reactor's case B starts calls at about 0, 400, 900 and 1,600 ms and answers from the fallback at about 1,950."
   },
   "refs": [
    {"title": "timeout (kotlinx.coroutines API)", "url": API + "timeout.html", "kind": "docs"},
    {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html", "kind": "read"}
   ]
  }
 ],
 "analogy": "A water pipe from a reservoir (the upstream) to a tap (the collector), with a net stretched across it. Debris that falls from the reservoir side lands in the net, and `catch` can replace it with clean water. A rock dropped at the tap end was never above the net, so it goes straight to whoever holds the tap. When the city shuts the main (your job is cancelled), the shut-off goes past the net on purpose. `retry` is draining the pipe and refilling it from the reservoir, so the water you already drank comes through again. `onCompletion` is a bell at one point on the pipe that rings once when the flow stops there, with a tag saying why. The analogy breaks at timeouts: in a real pipe an alarm is not the same as a shut-off, but in Flow a timeout is a kind of cancellation, which is why it slips silently out of a `launch` unless you translate it.",
 "in_your_world": "Your Quarkus service quotes card payments in the customer's currency, and the FX provider has a bad week. Wrap the call as in the last section: `timeout(300.milliseconds)` per attempt, `retryWithBackoff()` for `IOException` and `TimeoutCancellationException`, an overall budget that fits the checkout's own deadline, then a fallback to the second provider. The request's coroutine is cancelled when the client disconnects, and because `catch` and `retryWhen` skip the job's own cancellation, no retry or fallback call is wasted on a user who has left. The settlement import is the other side of the same coin. If it reads a Kafka topic or a paged acquirer API through a retried flow, a retry replays records you already posted. Make the ledger write idempotent on the payment id, or resume from the last committed offset, before you add the retry.",
 "mistake": "Putting `retry` on a stream that has side effects and assuming it continues where it failed. A retry collects the upstream again from the top, so every payment before the failure is delivered again: `[payment-1, payment-2, payment-1, payment-2, payment-3]`. People make this mistake because retries are usually shown on single calls, where replaying is exactly what you want. The fix is to make the consumer idempotent (de-duplicate by payment id, one set per collection, or let the database reject a second insert of the same key) or to make the source resumable, so the retry starts from a cursor or Kafka offset. A close second: `onCompletion { if (cause != null) metrics.failed() }` above `first()` or `take`, which counts every early stop as a failure because the cause there is an `AbortFlowException`.",
 "compare": {
  "title": "One flaky provider call, as a Reactor chain and as a Flow chain",
  "java": {
   "title": "Reactor",
   "src": "Mono<Rate> fxRate(String pair) {\n    return Mono.defer(() -> primary.rate(pair))\n        .timeout(Duration.ofMillis(300))                          // TimeoutException: an ordinary error\n        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))       // jitter 0.5 by default\n            .filter(e -> e instanceof IOException || e instanceof TimeoutException))\n        .timeout(Duration.ofSeconds(1))                           // overall budget\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || e instanceof TimeoutException,\n                       e -> fallback.rate(pair));                // exhausted: RetryExhaustedException\n}"
  },
  "kotlin": {
   "title": "Kotlin Flow",
   "src": "@OptIn(FlowPreview::class)\nfun fxRate(pair: String): Flow<Rate> =\n    primary.rate(pair)\n        .timeout(300.milliseconds)                // TimeoutCancellationException: a cancellation\n        .retryWhen { cause, attempt ->            // no jitter, no cap unless you write them\n            val retry = isTransient(cause) && attempt < 3\n            if (retry) delay(100L shl attempt.toInt())\n            retry\n        }\n        .timeout(1.seconds)                       // overall budget\n        .catch { e -> if (!isTransient(e)) throw e; emitAll(fallback.rate(pair)) }   // the original error"
  },
  "note": "The two chains have the same shape and, with jitter off, the same timeline. What differs is what the errors are. Reactor's `timeout` signals `TimeoutException`, an ordinary error, while Flow's throws `TimeoutCancellationException`, a `CancellationException`, so you must list it in `isTransient`, and a timeout that escapes a `launch` ends that coroutine silently. Reactor wraps exhausted retries in `RetryExhaustedException`, while `retryWhen` lets the original exception out. Reactor's backoff has jitter, a cap and an exhaustion error built in, and in Flow you write the policy yourself. One thing Flow gives you for free: `catch` and `retryWhen` never act on the collecting job's own cancellation, so a caller that goes away stops the whole chain without a retry or a fallback call."
 },
 "worked": {
  "title": "Wrap the FX provider call, one decision at a time",
  "steps": [
   {"say": "Give each attempt its own 300 ms and retry transient failures with backoff. The timeout sits above the retry, so `retryWhen` sees each timeout and can retry it. List the timeout in `isTransient`, because it is not an `IOException`.",
    "code": "fun isTransient(e: Throwable) = e is IOException || e is TimeoutCancellationException\n\n@OptIn(FlowPreview::class)\nval attempts = primary.rate(pair)\n    .timeout(300.milliseconds)      // 1. per attempt\n    .retryWithBackoff()             // 2. 100, 200, 400 ms; the original error after that",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Rate> attempts = Mono.defer(() -> primary.rate(pair))\n        .timeout(Duration.ofMillis(300))                                     // 1. per attempt\n        .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::isTransient));   // 2."},
   {"say": "Fall back only on transient failures. A bad currency pair is a bug or bad input, and the second provider will say the same, so let it reach the caller. With a provider that always hangs, the fallback answers at 1,930 ms; with a bad pair the caller sees the error at 20 ms.",
    "code": "val rate = attempts\n    .catch { e ->\n        if (!isTransient(e)) throw e            // 3. not ours to hide\n        emitAll(fallback.rate(pair))            // 4. the second provider\n    }",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Rate> rate = attempts\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e),   // 3.\n                       e -> fallback.rate(pair));                               // 4."},
   {"say": "The checkout itself has a deadline. Add a budget after the retries. Now the hanging provider gets calls at 0, 400 and 900, the budget fires at 1,000, and the fallback answers at 1,030.",
    "code": "@OptIn(FlowPreview::class)\nval rate = primary.rate(pair)\n    .timeout(300.milliseconds)\n    .retryWithBackoff()\n    .timeout(1.seconds)                         // 5. the whole sequence, waits included\n    .catch { e -> if (!isTransient(e)) throw e; emitAll(fallback.rate(pair)) }",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Rate> rate = attempts\n        .timeout(Duration.ofSeconds(1))         // 5. the whole sequence, waits included\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e), e -> fallback.rate(pair));"},
   {"say": "A background job refreshes the rate cache with `launchIn`. If both providers time out, the job would end as cancelled and no handler would hear it. Translate the timeout into a domain exception at the edge, so the handler logs it and alerts.",
    "code": "class ProviderTimeout(cause: Throwable) : Exception(\"FX provider timed out\", cause)\n\nrateUpdates\n    .onEach { cache.put(it) }\n    .catch { e -> if (e is TimeoutCancellationException) throw ProviderTimeout(e) else throw e }   // 6.\n    .launchIn(refresherScope)               // its CoroutineExceptionHandler now gets ProviderTimeout",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: not needed in Reactor, where TimeoutException is an ordinary error\nrateUpdates\n        .doOnNext(cache::put)\n        .subscribe(r -> { }, e -> alerts.providerFailed(e));   // 6. the error consumer sees the timeout"}
  ]
 },
 "lab": {
  "title": "A flaky FX provider: timeouts, backoff, a fallback, and a feed that replays",
  "minutes": 15,
  "files": [
   "labs/flows/src/main/kotlin/workbench/flows/l06/Retries.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l06/FxRates.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l06/Model.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l06.*'",
  "steps": [
   "Run the tests once. All 12 fail. Every timing in `ErrorsTest` is virtual, and each test name states the rule.",
   "In `Retries.kt`, write `isTransient`, then `retryWithBackoff` with `retryWhen`. The wait before retry k is `first * 2^k`, capped at `max`.",
   "In `FxRates.kt`, write `fxRate`: `timeout(300.milliseconds)`, then `retryWithBackoff()`, then a `catch` that rethrows non-transient errors and otherwise emits all of the fallback's flow. Predict the four provider tests' times before you run them.",
   "Read the cancellation test. Work out why your `fxRate` passes it without any extra code.",
   "Fix `uniquePayments` so a retry can't deliver a payment twice, and so a second collection still delivers everything."
  ],
  "hints": [
   "`retryWhen`'s lambda gets `(cause, attempt)`, and `attempt` starts at 0. Return `false` to let the original exception out, and `delay` before returning `true`.",
   "`Duration` times `Double` works: `first * (1L shl attempt.toInt()).toDouble()`, then `minOf(..., max)`.",
   "`timeout` is `@FlowPreview` in 1.11.0, so `fxRate` needs `@OptIn(FlowPreview::class)`. Without it you only get a warning.",
   "For `uniquePayments`, create the set of seen ids inside a `flow { }` builder, so each collection gets a fresh one. A set created outside it is shared by every collector."
  ],
  "done_when": "All 12 tests in `ErrorsTest` pass."
 },
 "drill": {
  "title": "Write catch from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T>` with `flow { }`. It must rethrow what the downstream threw, rethrow the cancellation of its own job, and hand everything else to `action`. Then say which of these reaches `action`: an upstream `withTimeout` firing, the collector throwing, `job.cancel()`.",
  "answer": {
   "lang": "kotlin",
   "src": "fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T> = flow {\n    var fromDownstream: Throwable? = null\n    try {\n        collect { value ->\n            try { emit(value) }\n            catch (e: Throwable) { fromDownstream = e; throw e }   // 1. remember what the collector threw\n        }\n    } catch (e: Throwable) {\n        if (e === fromDownstream) throw e                         // 2. below the net\n        if (e is CancellationException && !currentCoroutineContext().isActive) throw e   // 3. our job\n        action(e)                                                 // 4. from upstream\n    }\n}\n// Only the upstream withTimeout reaches action: it is a CancellationException, but our job is still active.",
   "alt": {
    "lang": "java",
    "src": "// Closest Java equivalent: a push-style source and a Consumer, with the same three checks\nstatic <T> void myCatch(Consumer<Consumer<T>> upstream, Consumer<T> downstream, Function<Throwable, T> action) {\n    RuntimeException[] fromDownstream = {null};\n    try {\n        upstream.accept(v -> {\n            try { downstream.accept(v); }\n            catch (RuntimeException e) { fromDownstream[0] = e; throw e; }   // 1. remember what the consumer threw\n        });\n    } catch (RuntimeException e) {\n        if (e == fromDownstream[0]) throw e;                                 // 2. below the net\n        if (Thread.currentThread().isInterrupted()) throw e;                 // 3. our own task was cancelled\n        downstream.accept(action.apply(e));                                  // 4. from upstream\n    }\n}"
   }
  }
 },
 "recap": [
  "A downstream exception comes out of `emit`. `catch` remembers it and rethrows it, and it rethrows its own job's cancellation. Everything else from upstream reaches the action, a `CancellationException` or `TimeoutCancellationException` included.",
  "Work in `collect { }` is below the net. Put it in `onEach` above `catch`, then call `collect()` or `launchIn`.",
  "`retry(n)` means n retries, n + 1 collections, and each one replays the upstream from the top. Consumers after a retry must be idempotent.",
  "`retryWhen`'s `attempt` starts at 0, a `delay` in it is the backoff, and the original exception comes out at the end. There is no jitter or exhaustion type unless you write it.",
  "`onCompletion`'s cause is `null` on success, the exception on failure, `JobCancellationException` on cancel, and `AbortFlowException` above `take` or `first`.",
  "`timeout()` throws `TimeoutCancellationException`, a cancellation. Above `retryWhen` it limits each attempt, below it is a budget, and uncaught in a `launch` it ends silently, so translate it."
 ],
 "quiz": [
  {"q": "Which failure does the `catch` action handle?\n\n```kotlin\nrates.map { parse(it) }\n    .catch { emit(fallbackRate) }\n    .collect { ledger.post(it) }\n```",
   "options": ["`ledger.post` throws `SQLException`", "`parse` throws `NumberFormatException`", "the request scope is cancelled while waiting for a rate", "all three"],
   "answer": 1,
   "why": "`parse` runs above the net, so its exception reaches the action. `ledger.post` runs in the collector, below the net, so its exception goes straight to the caller. The request's cancellation is the cancellation of the collecting job, which `catch` always lets pass."},
  {"q": "A stream fails after its second element on every attempt. It is collected through `retry(3)`. How many times does the collector receive element 1?",
   "options": ["Once: retry resumes after the failure", "3 times", "4 times", "It depends on the backoff"],
   "answer": 2,
   "why": "`retry(3)` means 3 retries, so 4 collections, and each collection runs the cold flow from the top. Elements 1 and 2 are delivered 4 times each, then the fourth failure comes out. A backoff changes when the retries happen, not how many."},
  {"q": "A metrics hook `onCompletion { cause -> if (cause == null) ok() else failed() }` sits right above `.first()`. Every successful lookup is counted as a failure. Why?",
   "options": ["`first()` stops the upstream by throwing `AbortFlowException`, a `CancellationException`, through it", "`first()` always fails with `NoSuchElementException` first and then retries", "`onCompletion` runs before the value is emitted, so `cause` isn't set yet", "`onCompletion` sees the collector's exception from `first()`'s internal collect"],
   "answer": 0,
   "why": "`first()` throws `AbortFlowException` (\"Flow was aborted, no more elements needed\") out of the upstream's `emit` once it has its value. Stations above it see that as the cause. Below `take(1)` or after the terminal call, the flow simply completed. Classify `cause is CancellationException` as cancelled or stopped early, not as a failure."},
  {"q": "Each provider call must be limited to 300 ms and retried with backoff, and the caller must get an answer or an error within 1 second overall. Which order?",
   "options": ["`.retryWithBackoff().timeout(300.milliseconds).timeout(1.seconds)`", "`.timeout(1.seconds).retryWithBackoff().timeout(300.milliseconds)`", "`.retryWithBackoff().timeout(300.milliseconds)`", "`.timeout(300.milliseconds).retryWithBackoff().timeout(1.seconds)`"],
   "answer": 3,
   "why": "A timeout above `retryWhen` covers one attempt and is retried, so 300 ms goes first. A timeout below the retries covers the whole sequence, waits included, so the 1 s budget goes after them. With the retries first, a 300 ms timeout would cut the whole sequence at 300 ms."},
  {"q": "From the reactive track: Reactor's `timeout` signals `TimeoutException`. In a Flow collected with `launchIn(scope)`, a `timeout(50.milliseconds)` fires and nothing catches it. What happens?",
   "options": ["The scope's `CoroutineExceptionHandler` logs a `TimeoutException`", "The launched job ends as cancelled, no handler runs, and the scope keeps running", "The whole scope is cancelled", "The flow retries once by default"],
   "answer": 1,
   "why": "Flow's `timeout` throws `TimeoutCancellationException`, a `CancellationException`, and handlers ignore cancellation. The job just ends cancelled, silently. Translate it in `catch` into a domain exception so the handler sees it. In Reactor this trap doesn't exist, because `TimeoutException` is an ordinary error.",
   "from": "rx-05"}
 ],
 "flashcards": [
  {"front": "Does `catch` handle a `CancellationException`?", "back": "Yes, if the upstream throws it while the collecting job is active (a `TimeoutCancellationException` too). It lets the cancellation of the collecting job pass."},
  {"front": "How does `catch` know an exception came from the collector?", "back": "It wraps the downstream `emit` and remembers what came out of it. That exception is rethrown, never handled."},
  {"front": "`retry(3)`: how many collections, and what does the collector see again?", "back": "Up to 4 collections. Each runs the upstream from the top, so values already emitted are emitted again."},
  {"front": "In `retryWhen { cause, attempt -> }`, what is `attempt` on the first failure?", "back": "0."},
  {"front": "`onCompletion` placed above `first()`: what is `cause` after a successful lookup?", "back": "`AbortFlowException: Flow was aborted, no more elements needed`, a `CancellationException`. Below `take(1)` it is `null`."},
  {"front": "What does `timeout(300.milliseconds)` throw, and what is its message?", "back": "`TimeoutCancellationException` (a `CancellationException`): \"Timed out waiting for 300ms\"."},
  {"front": "A `timeout()` escapes a `launchIn` job. What happens?", "back": "The job ends cancelled, no `CoroutineExceptionHandler` runs, and the parent scope keeps running. Translate it in `catch` if someone must hear it."}
 ],
 "terms": [
  {"term": "Exception transparency", "plain": "The rule that an exception from downstream belongs to the downstream: once `emit` has thrown, the flow must not emit again."},
  {"term": "Upstream and downstream", "plain": "Everything above an operator in the chain, and everything below it, including the collector."},
  {"term": "catch", "plain": "An operator that handles failures from above it, except the cancellation of the collecting job."},
  {"term": "retryWhen", "plain": "On an upstream failure, asks a predicate with the cause and attempt number, and collects the upstream again if it says yes."},
  {"term": "Idempotent consumer", "plain": "A consumer that gives the same result when it sees the same item twice, for example by keying writes on the payment id."},
  {"term": "TimeoutCancellationException", "plain": "What `timeout()` and `withTimeout` throw. It is a `CancellationException`, so handlers ignore it."},
  {"term": "AbortFlowException", "plain": "The internal `CancellationException` that `take` and `first` throw out of the upstream's `emit` to stop it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why `catch { emit(fallbackRate) }` turns a provider timeout into a fallback, but does nothing when the customer closes the page and the request is cancelled. They thought catch never sees CancellationException. Explain it with the net picture, and say what you'd add if the flow ran in a background `launchIn` job.",
  "answer": "`catch` is a net under the upstream. It wraps the downstream's `emit` and remembers anything the collector throws, which it rethrows, and it rethrows the cancellation of its own collecting job. Everything else that falls from above lands in the net. A `withTimeout` or `timeout()` inside the provider call throws `TimeoutCancellationException` while our job is still active, so to `catch` it's just an upstream failure and the action emits the fallback. When the customer closes the page, the request's job is cancelled. That cancellation is the job's own, so the net lets it pass and no fallback call is made, which is what we want. In a background `launchIn` job I'd add a translation: if both providers time out, the `TimeoutCancellationException` would escape the launch as a plain cancellation, no exception handler would run and the refresher would stop silently. So I'd convert it in a `catch` into a domain `ProviderTimeout` exception, which the scope's handler logs."
 },
 "deeper": {
  "minutes": 10,
  "body": "When both sides fail, the upstream wins. If the collector throws `IllegalStateException(\"collector failed\")` and the builder's `finally` then throws `IOException(\"close() failed\")`, the caller sees the `IOException`, with the collector's exception in `suppressed`, and a `catch` above does not run its action. The `Flow` KDoc calls this \"a semantic equivalent of throwing from finally block\", and notes that the exception-handling operators still treat the downstream exception as the root cause.\n\nA failed fallback forgets the primary. `flow { throw IOException(\"primary down\") }.catch { emitAll(flow { throw IOException(\"fallback down\") }) }` gives the caller `IOException: fallback down` with no cause and nothing suppressed. If you want both in the logs, attach the primary yourself with `addSuppressed` before you emit the fallback.\n\nDon't retry from inside `catch` with `emitAll(sameFlow)`. The `catch` KDoc points to `retryWhen`, which retries \"without introducing ever-growing stack of suspending calls\".\n\n`withTimeoutOrNull(250) { flow.toList() }` returns `null` and loses the values that arrived before the deadline. Collect into a list you own (`collect { partial += it }`) if you need them. Inside `runBlocking` with a `CoroutineName(\"settlement-import\")`, the `withTimeout` message names the coroutine: `Coroutine \"settlement-import\" timed out waiting for 50 ms`.\n\nThe exact boundary of `timeout(100.milliseconds)` depends on how the scheduler orders events at the same instant: under virtual time a 100 ms gap did not time out and a 101 ms gap did. Don't build logic on the equality case.\n\n`onEmpty { emit(default) }` is the counterpart for a flow that completes without a value: a merchant with no fee schedule gets the default fee, and a merchant with one gets theirs."
 },
 "sources": [
  {"title": "catch (kotlinx.coroutines API)", "url": API + "catch.html"},
  {"title": "retryWhen (kotlinx.coroutines API)", "url": API + "retry-when.html"},
  {"title": "onCompletion (kotlinx.coroutines API)", "url": API + "on-completion.html"},
  {"title": "timeout (kotlinx.coroutines API)", "url": API + "timeout.html"},
  {"title": "operators/Errors.kt at tag 1.11.0 (catch, retry and retryWhen)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/operators/Errors.kt"}
 ]
}
out = ROOT / "content/lessons/flow-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
