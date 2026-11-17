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
    'An IOException and a TimeoutCancellationException thrown by the upstream, the bakery call, fall into the net and are caught. '
    'The cancellation of the collecting job passes through the net to the caller. A failure in the collector, the diner dropping a plate, starts '
    'below the net and goes straight to the caller.">'
    '<text class="t-s t-m" x="340" y="22" text-anchor="middle">what reaches the catch action, and what passes it</text>'
    '<rect class="box-a" x="20" y="40" width="290" height="76" rx="8"/>'
    '<text class="t" x="165" y="68" text-anchor="middle">upstream</text>'
    '<text class="t-s t-code" x="165" y="94" text-anchor="middle">bakery call, map { }, withTimeout</text>'
    '<line class="ln-d" x1="20" y1="150" x2="660" y2="150"/>'
    '<text class="t t-code" x="165" y="142" text-anchor="middle">catch { }</text>'
    '<rect class="box-b" x="20" y="178" width="290" height="60" rx="8"/>'
    '<text class="t" x="165" y="202" text-anchor="middle">downstream</text>'
    '<text class="t-s t-code" x="165" y="224" text-anchor="middle">collect { diner.eat(it) }</text>'
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
    '<text class="t-s" x="630" y="196" text-anchor="middle">diner drops it</text>'
    '<line class="ln-bad" x1="630" y1="204" x2="630" y2="262" marker-end="url(#arr)"/>'
    '</svg>'
)

OPENING = """Bread for dinner comes from the bakery round the corner, ordered by phone. It's a lovely bakery with a terrible phone. Sometimes the call drops halfway, and sometimes nobody picks up at all. So the cook has a routine. She rings again after a short pause, a longer pause each time, and if the corner bakery still can't help, she rings the backup bakery across town. Meanwhile plates can drop anywhere: in the kitchen, or at the table.

Kotlin flows have an operator for each part of that routine: `catch` for a dropped plate, `retry` for ringing again, `timeout` for giving up at a time limit, and `onCompletion` for the note about how it all ended. The easy trap is to believe that `catch` never sees a timeout, because a timeout is a kind of cancellation. It does see it, and that turns out to be useful.

In Flattening and combining, one failing inner flow took all the others down. In this lesson, we'll find which failures a `catch` hears, what a retry cooks again, what the note at the end says, and where a time limit goes. Before we start, make a guess, and keep it in mind."""

S1 = r"""Here is the bread course as a flow. The cook first sends out yesterday's loaf, then fetches a fresh one from the bakery inside `withTimeout(50)`, which cancels the call if it takes longer than 50 ms. A `catch` below sends out crackers if anything goes wrong. The bakery takes 100 ms today.

Most people expect the timeout to fly straight past the `catch`. The reasoning sounds solid: a timeout is a **CancellationException**, the exception coroutines use to say "stop, you've been called off", and `catch` doesn't handle cancellation. Run it, and then run a second version where the caller's own **job**, the handle that can cancel the collecting coroutine, is cancelled instead:

```kotlin
flow { emit(oldLoaf); emit(withTimeout(50) { bakery.fresh() }) }   // the call takes 100 ms
    .catch { e -> emit(crackers) }
    .collect { diner.eat(it) }            // case 2: the caller calls job.cancel() meanwhile
```

```java
// Closest Java equivalent: onErrorResume handles what comes from above it; dispose() is a cancel signal
Flux.concat(Flux.just(oldLoaf), bakery.fresh().timeout(Duration.ofMillis(50)))
    .onErrorResume(e -> Mono.just(crackers))
    .subscribe(diner::eat);               // case 2: the subscription is disposed meanwhile
```

Here is what the Try it prints for five ways the bread course can end:

| How it ends | The `catch` action runs | The caller sees |
|---|---|---|
| the bakery call throws `IOException` | yes | nothing |
| the bakery call throws `CancellationException` | yes | nothing |
| `withTimeout` fires inside the bakery call | yes, with `TimeoutCancellationException` | nothing |
| the diner drops a plate | no | `IllegalStateException: the diner dropped the plate` |
| the caller's job is cancelled | no | `JobCancellationException` |

The timeout was caught, and the cancelled job was not. To see why, remember lesson 2 of this track. An exception thrown by the collector, the diner, comes back out of `emit` and up into the cook's code, and the inspector refuses any `emit` after that. That rule is called **exception transparency**: an exception from downstream belongs to downstream. So when the upstream's `collect` throws, `catch` has to work out who threw. Build it by hand and the rule falls out:

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

Read it top to bottom. First it wraps the downstream `emit` and remembers anything that comes out of it. Then, when the whole `collect` fails, it asks two questions. Did this come from downstream? Rethrow it. Is it the cancellation of our own job? Rethrow that too. Everything else goes to your action.

The library's `catch` keeps the same books. Picture a net strung under the **upstream**, everything above `catch` in the chain, while the **downstream** is everything below it, the collector included. Anything that falls from above lands in the net, even a `CancellationException` that the upstream throws while the job is still running. The job's own cancellation passes through on purpose. And a plate the diner drops falls below the net, straight to the caller.

So `catch` ignores the cancellation of its collector, not every `CancellationException`. For a bakery call, that's usually what you want: a timeout becomes crackers. If it isn't, rethrow `CancellationException` in the action yourself.

The net is generous, but it only covers what hangs above it. To put the serving under its protection, move it into `onEach` above the `catch` and call `collect()` with no lambda, or `launchIn(scope)`, which collects in a new coroutine of that scope. And a caught error still ends the upstream: `flowOf(1, 2, 3).map { fails on 2 }.catch { emit(-1) }` gives 1 and -1, and 3 is never made.

**catch hears only what falls from above it. Put the work it should cover above it.**

Check yourself: `catch` sits above `map`, and `map` throws. Who handles it? The net can send out crackers. Sometimes you'd rather ring the bakery again."""

S2 = r"""The grocer's van is back with the delivery note from Context and threads: flour, eggs and butter, read line by line. On the first attempt the reader loses its connection after line 2, with an `IOException`, Java's usual exception for a failed read or write. The pantry import wraps the note in `retry(3)`. What does the pantry receive?

```kotlin
val received = note.retry(3).toList()
// [flour, eggs, flour, eggs, butter]
```

```java
// Closest Java equivalent: retry re-subscribes, so a cold Flux replays from the top too
List<String> received = Flux.defer(grocer::note).retry(3).collectList().block();
// [flour, eggs, flour, eggs, butter]
```

Two lines went into the pantry twice. The flour doesn't mind, but the pantry book now lists it twice. `retryWhen`, the operator under `retry`, is a loop around the same books that `catch` keeps. When the upstream fails with an exception from above the net, it calls your **predicate**, a function that answers yes or no, with the cause and an attempt number. If the answer is yes, it collects the upstream again. A cold flow is a recipe card, and collecting it again cooks it again from the top. Values that were already emitted are emitted again.

The counting follows from the loop. `retry(n)` is `retryWhen { cause, attempt -> attempt < n && predicate(cause) }`, so `retry(2)` on a note that always fails collects it 3 times, and then the third exception comes out. `retry(0)` fails when you build the flow, with `Expected positive amount of retries, but had 0`. The default is `Long.MAX_VALUE`, which retries for ever. `attempt` is 0 on the first failure, and with `retry(n, predicate)` the predicate is no longer called once the attempts run out.

The cook's longer pause each time is a **backoff**, and in code it is a `delay` inside the predicate:

```kotlin
bakery.order("sourdough").retryWhen { cause, attempt ->
    val retry = cause is IOException && attempt < 3
    if (retry) delay(100L shl attempt.toInt())        // 100, 200, 400 ms
    retry
}
```

```java
// Closest Java equivalent: Reactor's backoff spec (jitter off, so the times are exact)
bakery.order("sourdough").retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0)
        .filter(e -> e instanceof IOException));
```

Against a bakery that never answers, both ring at 0, 100, 300 and 700 ms. Then they differ. Flow gives up by letting the original `IOException` out. Reactor wraps it in a `RetryExhaustedException` (`Retries exhausted: 3/3`, with the real error as its cause), and outside tests it adds **jitter**, a random spread on each wait so that many callers don't ring at the same moment (0.5 by default, from lesson 5 of the reactive track). Flow has no jitter, no cap and no exhaustion type. You write those yourself, which is what the lab does.

Like `catch`, a retry never fires for an exception the collector threw, or for the caller's own cancellation. It does fire for a `TimeoutCancellationException` from a `timeout()` above it, and the last section builds on that.

The replay is the part that hurts whenever each value changes something, such as a line in the pantry book. Every consumer after a retry must be **idempotent**: seeing the same item twice must leave the same result as seeing it once. Skip lines whose id you have seen (one set per collection), or make the source start where it stopped, from a bookmark that a retry can pass back.

**A retry cooks the recipe again from the top. Make whatever comes after it safe to see an item twice.**

Check yourself: `retry(3)` on a note that fails after its second line on every attempt. How many times does the collector see line 1? A retry hides failures well. A tally of how each order ended should hide nothing, and it's easy to get wrong."""

S3 = r"""The kitchen keeps a tally of bread orders: a tick for each one that went well, a cross for each one that failed. The orders go through `first()`, which takes the first value and stops. At the end of the evening, every order has a cross:

```kotlin
loaves(kind)
    .onCompletion { cause -> if (cause == null) tally.ok() else tally.failed(cause) }
    .first()
```

```java
// Closest Java equivalent: doFinally reports a signal type instead of a cause
loaves(kind)
    .doFinally(signal -> { if (signal == SignalType.ON_COMPLETE) tally.ok(); else tally.failed(signal); })
    .next()
    .block();
```

`onCompletion` is a `try`/`finally` around the upstream, placed exactly where you wrote it. It runs once, when the flow ends, and leaves a note: its `cause` says what passed through that spot on the way out.

| How the flow ended | `cause` |
|---|---|
| it completed normally | `null` |
| the upstream threw | `IOException: line dropped` |
| the collector threw | `IllegalStateException: the diner dropped the plate` |
| a `map` below threw, and a `catch` below that swallowed it | `IllegalStateException: map failed` |
| above `take(1)` or `first()` | `AbortFlowException: Flow was aborted, no more elements needed` |
| below `take(1)` | `null` |
| the collecting job was cancelled | `JobCancellationException: StandaloneCoroutine was cancelled` |

`first()` stops the upstream the way lesson 2 of this track described. It throws `AbortFlowException`, the signed "no more, thanks" note, out of the upstream's `emit`. That exception is a `CancellationException`, and every operator above `first()` sees it go by, so the tally counts a stopped order as a failed one. Below `take(1)` the flow simply ended, so the cause there is `null`.

So read the note in order. `null` means it went well. A `CancellationException` means it was called off or stopped early, which is not a failure. Anything else is a failure. In code, that is one more branch before the cross: `cause is CancellationException -> tally.stopped()`.

`onCompletion` can emit, but only on success: `flowOf("a", "b").onCompletion { if (it == null) emit("done") }` gives a, b, done. After a failure, `emit` there throws the original cause again. Use `catch` to send out a replacement.

The terminal operators, the calls such as `first()` and `single()` that run a flow and return a result, fail in their own words, and they stop the upstream at different points. `first()` on an empty flow throws `NoSuchElementException: Expected at least one element`. `single()` throws `NoSuchElementException: Flow is empty`, or `IllegalArgumentException: Flow has more than one element`. On a three-element flow, `first()` pulls 1 element and `single()` pulls 2 before it fails. Reactor's `single()` says `Source was a (constant) empty`, and throws `IndexOutOfBoundsException: Source emitted more than one item` instead.

Check yourself: `onCompletion` sits below `take(1)`, and the collector throws on the first element. What is `cause`? Every failure so far arrived quickly. The worst bakery is the one that never answers."""

S4 = r"""The corner bakery has stopped answering: each call now rings for 1,000 ms. The chain gives every call 300 ms, retries with backoff and then rings the backup bakery. When does the backup answer?

```kotlin
bakery.order("sourdough")
    .timeout(300.milliseconds)            // per try; @FlowPreview
    .retryWithBackoff()                   // 3 retries: 100, 200, 400 ms
    .catch { e -> if (!isTransient(e)) throw e; emitAll(backup.order("sourdough")) }
```

```java
// Closest Java equivalent: the Reactor chain from lesson 5 of the reactive track
bakery.order("sourdough")
    .timeout(Duration.ofMillis(300))
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0).filter(this::isTransient))
    .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e), e -> backup.order("sourdough"));
```

Here `isTransient` is the lab's question "is this failure worth another try?": yes for a dropped line and for a timeout, no for anything else. The calls start at 0, 400, 900 and 1,600 ms, and each one is cut at +300. At 1,900 ms the corner bakery gives up with `Timed out waiting for 300ms`, and the backup answers at 1,930. Reactor's chain prints the same times on a real clock.

`timeout(d)` arrived in kotlinx.coroutines 1.7.0 and is still `@FlowPreview` in 1.11.0. It takes a `Duration` only. It runs the upstream in a producer coroutine and arms a timer only while it waits for the next upstream value. Time the downstream spends on a value doesn't count, but the wait for the first value does. Picture the kitchen's egg timer, wound each time the cook starts waiting for the bakery and paused while the diner eats. When it rings, it throws `TimeoutCancellationException`, and that is a `CancellationException`.

That one fact explains the rest of the chain. The timeout comes from above `retryWhen` while the job is still running, so `retryWhen` can retry it, but only if `isTransient` lists `TimeoutCancellationException`, because a timeout is not an `IOException`. Position sets the meaning. Above `retryWhen`, the timer limits each try. Below it, the timer limits the whole sequence, waits included: a budget. Add `.timeout(1.seconds)` after the retries, and the same bakery gets calls at 0, 400 and 900, the budget rings at 1,000, and the backup answers at 1,030.

The `catch` at the end filters on `isTransient`, so moon bread, which nobody bakes, reaches the caller as an `IllegalArgumentException` at 20 ms, with no retry and no call to the backup. When the backup fails too, the caller sees the backup's error. The corner bakery's error is not attached.

**Above the retry, a timeout limits one try. Below it, a timeout limits them all.**

The cancellation nature bites when the flow runs in the background. A timeout that nobody catches inside `launch` or `launchIn` just ends that coroutine as cancelled. The scope's **CoroutineExceptionHandler**, its last-resort handler for failures that nobody caught, never runs, and the parent scope keeps going, because handlers ignore `CancellationException`. Your bread refresher stops, and nobody hears the egg timer. Translate the timeout at the edge: `.catch { e -> if (e is TimeoutCancellationException) throw BakeryTimeout(e) else throw e }`, and the handler gets `BakeryTimeout` with the timeout as its cause. Reactor's `timeout` signals `java.util.concurrent.TimeoutException`, an ordinary error, so the trap doesn't exist there.

Two notes for tests. Under `runTest`, `withTimeout` words its message differently ("Timed out after 50ms of _virtual_ (kotlinx.coroutines.test) time..."), so assert on the exception's type, never its text. And `TimeoutCancellationException` has no public constructor, so produce one with a real `timeout()` under virtual time, as the lab does.

Check yourself: where does `.timeout(1.seconds)` go to limit each try instead of the whole sequence? Everything in this lesson acts on one collector and its own cold flow. When many diners share one cooking session, a failure behaves very differently."""

CLOSING = """We started with a bakery that drops calls. `catch` is a net that hears only what falls from above it, timeouts included, and lets the caller's own cancellation through. A retry cooks the recipe again from the top, `onCompletion` leaves one note that can say "no more, thanks", and a timeout's position decides whether it limits one try or all of them.

Now search your own code for `retry` on a flow whose values change something, such as rows written to a database. Ask what happens when the same item arrives twice.

Next, we'll share one cooking session among many diners. What does a hot flow do when one diner is slow, and when its cook fails?"""

L = {
 "id": "flow-06",
 "title": "Errors, completion, retries and timeouts",
 "minutes": 38,
 "goal": "By the end you can say which exceptions a catch handles and which pass it, predict what a retry replays, read onCompletion's cause, and build a slow call with a per-try timeout, backoff and a backup that a cancelled caller still stops.",
 "opening": OPENING,
 "warmup": {
  "q": "A flow emits yesterday's loaf, then calls the bakery inside `withTimeout(50)`. Below it sits `.catch { emit(crackers) }`. The bakery takes 100 ms. What does the collector get?",
  "options": [
   "Yesterday's loaf, then the timeout escapes, because catch never handles a CancellationException",
   "Yesterday's loaf, then crackers",
   "Nothing at all: the timeout cancels the collector",
   "Yesterday's loaf, and then the flow completes normally with nothing else"
  ],
  "answer": 1,
  "why": "`withTimeout` throws `TimeoutCancellationException` inside the upstream while the collecting job is still running. To `catch` that is an upstream failure like any other, so the action runs and emits the crackers. What `catch` lets pass is the cancellation of the collecting job itself, and exceptions thrown below it."
 },
 "sections": [
  {
   "h": "A catch is a net under the upstream, and it checks who threw",
   "body": S1,
   "figure": {"svg": FIG, "caption": "catch handles what falls from above it, CancellationException included, except the cancellation of the collecting job. The collector's failures start below the net."},
   "try": {
    "title": "Five ways to end the bread course",
    "minutes": 4,
    "steps": [
     "Open `CatchNet.kt`. For each of the five cases, predict whether the net catches it and what the caller sees.",
     "Run it. Each case runs twice: once with the library's `catch`, once with `myCatch` from this section. Check that the two lines always agree.",
     "In `myCatch`, delete the line that rethrows `fromDownstream` and run again. Which case changes, and what does the caller see now?",
     "Run `CatchNetJava`, the `onErrorResume` twin. Find the case where moving the serving above the net changes the result."
    ],
    "code": tryit("CatchNet.kt", "CatchNetJava.java"),
    "expect": "The first three cases get `[old loaf, crackers]` and the caller sees nothing: the net caught an `IOException`, a `CancellationException` and a `TimeoutCancellationException` (\"Timed out waiting for 50 ms\"). The dropped plate and the job cancellation pass: the caller sees `IllegalStateException: the diner dropped the plate` and `JobCancellationException`. `catch` and `myCatch` agree on every line. Without the `fromDownstream` check, the dropped-plate case runs the action and emits again after the downstream failed, and the flow throws `IllegalStateException: Flow exception transparency is violated`. In Reactor, the dropped plate fails the stream when the serving sits below `onErrorResume`, and is handled when it sits above it."
   },
   "refs": [
    {"title": "catch (kotlinx.coroutines API)", "url": API + "catch.html", "kind": "docs"},
    {"title": "Flows: exceptions, catch and onEach (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-flow.html", "kind": "read"}
   ]
  },
  {
   "h": "A retry cooks the recipe again, from the top",
   "body": S2,
   "try": {
    "title": "Read the note twice",
    "minutes": 4,
    "steps": [
     "Open `RetryReplay.kt`. Predict what the pantry receives in the first block, and how many collections `retry(2)` makes in the second.",
     "Run it on virtual time. Check the backoff block's times against the section.",
     "Change the second block to `retry(2) { it is IllegalStateException }`. Predict the output, then run it.",
     "Run `RetryReplayJava`: the same replay in Reactor, and `Retry.backoff` on a real clock."
    ],
    "code": tryit("RetryReplay.kt", "RetryReplayJava.java"),
    "expect": "The pantry receives `[flour, eggs, flour, eggs, butter]`. `retry(2)` collects 3 times: `[flour, eggs, flour, eggs, flour, eggs, PHONE THE GROCER]`, and `retry(0)` is refused with \"Expected positive amount of retries, but had 0\". The backoff calls come at 0, 100, 300 and 700 ms, then the original `IOException` reaches the `catch`. With the predicate, an `IOException` is not retried, so you get `[flour, eggs, PHONE THE GROCER]` after 1 collection. Reactor replays the same five lines, rings at about 0, 100, 300 and 700 ms, and ends with `RetryExhaustedException: Retries exhausted: 3/3`."
   },
   "refs": [
    {"title": "retryWhen (kotlinx.coroutines API)", "url": API + "retry-when.html", "kind": "docs"},
    {"title": "retry (kotlinx.coroutines API)", "url": API + "retry.html", "kind": "docs"}
   ]
  },
  {
   "h": "The onCompletion note is written once, and its cause is not always a failure",
   "body": S3,
   "try": {
    "title": "Read the note",
    "minutes": 3,
    "steps": [
     "Open `CompletionCauses.kt`. Cover the output and write down the `cause` you expect on each line.",
     "Run it. Look at the two lines around `take(1)`, and at `above first()`.",
     "Run `CompletionCausesJava`. Which `doFinally` signal does Reactor give above `take(1)`?"
    ],
    "code": tryit("CompletionCauses.kt", "CompletionCausesJava.java"),
    "expect": "`null` for success and below `take(1)`. `IOException: line dropped` for the upstream failure, `IllegalStateException: the diner dropped the plate` for the collector failure, and `IllegalStateException: map failed` even though a `catch` below swallowed it. `AbortFlowException: Flow was aborted, no more elements needed` above `take(1)` and above `first()`, and `JobCancellationException: StandaloneCoroutine was cancelled` for `job.cancel()`. `single()` pulls 2 elements and `first()` pulls 1. Reactor reports `onComplete`, `onError`, `cancel` above `take(1)` and `onComplete` below it."
   },
   "refs": [
    {"title": "onCompletion (kotlinx.coroutines API)", "url": API + "on-completion.html", "kind": "docs"},
    {"title": "single (kotlinx.coroutines API)", "url": API + "single.html", "kind": "docs"}
   ]
  },
  {
   "h": "A timeout throws a cancellation, and its position sets what it limits",
   "body": S4,
   "try": {
    "title": "Time a bakery that won't answer",
    "minutes": 5,
    "steps": [
     "Open `FlakyBakery.kt`. Before you run it, write down when each of cases A to E ends, and how many calls each bakery gets.",
     "Run it on virtual time and compare. Case E is case B with an overall `timeout(1.seconds)` after the retries.",
     "Read the last block: the same timeout inside `launchIn`, first silent, then translated into `BakeryTimeout`.",
     "Run `FlakyBakeryJava`, the Reactor version of case B, on a real clock."
    ],
    "code": tryit("FlakyBakery.kt", "FlakyBakeryJava.java"),
    "expect": "A ends at 390 ms with a loaf from the corner bakery (3 calls). B: calls at 0, 400, 900 and 1,600, the corner bakery gives up at 1,900 with \"Timed out waiting for 300ms\", and the backup answers at 1,930. C: the caller sees `IllegalArgumentException: nobody bakes moon bread` at 20 ms, with no retry. D: the caller sees `IOException: backup bakery closed` at 800. E: the budget rings at 1,000 (\"Timed out waiting for 1s\") and the backup answers at 1,030. In the `launchIn` block, the silent version leaves the scope active and calls no handler; the loud version reaches the handler, and the scope is no longer active. Reactor's case B starts calls at about 0, 400, 900 and 1,600 ms and answers from the backup at about 1,950."
   },
   "refs": [
    {"title": "timeout (kotlinx.coroutines API)", "url": API + "timeout.html", "kind": "docs"},
    {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "One slow bakery call, as a Reactor chain and as a Flow chain",
  "java": {
   "title": "Reactor",
   "src": "Mono<Loaf> freshLoaf(String kind) {\n    return Mono.defer(() -> bakery.order(kind))\n        .timeout(Duration.ofMillis(300))                          // TimeoutException: an ordinary error\n        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))       // jitter 0.5 by default\n            .filter(e -> e instanceof IOException || e instanceof TimeoutException))\n        .timeout(Duration.ofSeconds(1))                           // overall budget\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || e instanceof TimeoutException,\n                       e -> backup.order(kind));                 // exhausted: RetryExhaustedException\n}"
  },
  "kotlin": {
   "title": "Kotlin Flow",
   "src": "@OptIn(FlowPreview::class)\nfun freshLoaf(kind: String): Flow<Loaf> =\n    bakery.order(kind)\n        .timeout(300.milliseconds)                // TimeoutCancellationException: a cancellation\n        .retryWhen { cause, attempt ->            // no jitter, no cap unless you write them\n            val retry = isTransient(cause) && attempt < 3\n            if (retry) delay(100L shl attempt.toInt())\n            retry\n        }\n        .timeout(1.seconds)                       // overall budget\n        .catch { e -> if (!isTransient(e)) throw e; emitAll(backup.order(kind)) }   // the original error"
  },
  "note": "The two chains have the same shape and, with jitter off, the same timeline. What differs is what the errors are. Reactor's `timeout` signals `TimeoutException`, an ordinary error, while Flow's throws `TimeoutCancellationException`, a `CancellationException`, so you must list it in `isTransient`, and a timeout that escapes a `launch` ends that coroutine silently. Reactor wraps exhausted retries in `RetryExhaustedException`, while `retryWhen` lets the original exception out. Reactor's backoff has jitter, a cap and an exhaustion error built in, and in Flow you write the policy yourself. One thing Flow gives you for free: `catch` and `retryWhen` never act on the collecting job's own cancellation, so a caller that goes away stops the whole chain without a retry or a call to the backup."
 },
 "worked": {
  "title": "Order the bread, one decision at a time",
  "steps": [
   {"say": "Give each call its own 300 ms and retry the failures worth retrying, with backoff. The timeout sits above the retry, so `retryWhen` sees each timeout and can retry it. List the timeout in `isTransient`, because it is not an `IOException`.",
    "code": "fun isTransient(e: Throwable) = e is IOException || e is TimeoutCancellationException\n\n@OptIn(FlowPreview::class)\nval tries = bakery.order(kind)\n    .timeout(300.milliseconds)      // 1. per try\n    .retryWithBackoff()             // 2. 100, 200, 400 ms; the original error after that",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Loaf> tries = Mono.defer(() -> bakery.order(kind))\n        .timeout(Duration.ofMillis(300))                                     // 1. per try\n        .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::isTransient));   // 2."},
   {"say": "Ring the backup only for failures worth retrying. Moon bread, which nobody bakes, is a bug or bad input, and the backup will say the same, so let it reach the caller. With a bakery that never answers, the backup answers at 1,930 ms; with moon bread, the caller sees the error at 20 ms.",
    "code": "val loaf = tries\n    .catch { e ->\n        if (!isTransient(e)) throw e            // 3. not ours to hide\n        emitAll(backup.order(kind))             // 4. the backup bakery\n    }",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Loaf> loaf = tries\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e),   // 3.\n                       e -> backup.order(kind));                                // 4."},
   {"say": "Dinner itself has a deadline. Add a budget after the retries. Now the silent bakery gets calls at 0, 400 and 900, the budget rings at 1,000, and the backup answers at 1,030.",
    "code": "@OptIn(FlowPreview::class)\nval loaf = bakery.order(kind)\n    .timeout(300.milliseconds)\n    .retryWithBackoff()\n    .timeout(1.seconds)                         // 5. the whole sequence, waits included\n    .catch { e -> if (!isTransient(e)) throw e; emitAll(backup.order(kind)) }",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent\nMono<Loaf> loaf = tries\n        .timeout(Duration.ofSeconds(1))         // 5. the whole sequence, waits included\n        .onErrorResume(e -> Exceptions.isRetryExhausted(e) || isTransient(e), e -> backup.order(kind));"},
   {"say": "A background job keeps the bread board up to date with `launchIn`. If both bakeries time out, the job would end as cancelled and no handler would hear it. Translate the timeout into an exception of your own at the edge, so the handler logs it.",
    "code": "class BakeryTimeout(cause: Throwable) : Exception(\"the bakery timed out\", cause)\n\nbreadUpdates\n    .onEach { board.show(it) }\n    .catch { e -> if (e is TimeoutCancellationException) throw BakeryTimeout(e) else throw e }   // 6.\n    .launchIn(refresherScope)               // its CoroutineExceptionHandler now gets BakeryTimeout",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: not needed in Reactor, where TimeoutException is an ordinary error\nbreadUpdates\n        .doOnNext(board::show)\n        .subscribe(loaf -> { }, e -> alarms.bakeryFailed(e));   // 6. the error consumer sees the timeout"}
  ]
 },
 "lab": {
  "title": "A flaky bakery: timeouts, backoff, a backup, and a note that replays",
  "minutes": 15,
  "files": [
   "labs/flows/src/main/kotlin/workbench/flows/l06/Retries.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l06/Bread.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l06/Model.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l06.*'",
  "steps": [
   "Run the tests once. All 12 fail. Every timing in `ErrorsTest` is virtual, and each test name states the rule.",
   "In `Retries.kt`, write `isTransient`, then `retryWithBackoff` with `retryWhen`. The wait before retry k is `first * 2^k`, capped at `max`.",
   "In `Bread.kt`, write `freshLoaf`: `timeout(300.milliseconds)`, then `retryWithBackoff()`, then a `catch` that rethrows failures that aren't transient and otherwise emits all of the backup's flow. Predict the four bakery tests' times before you run them.",
   "Read the cancellation test. Work out why your `freshLoaf` passes it without any extra code.",
   "Fix `eachLineOnce` so a retry can't deliver a line twice, and so a second collection still delivers every line."
  ],
  "hints": [
   "`retryWhen`'s lambda gets `(cause, attempt)`, and `attempt` starts at 0. Return `false` to let the original exception out, and `delay` before returning `true`.",
   "`Duration` times `Double` works: `first * (1L shl attempt.toInt()).toDouble()`, then `minOf(..., max)`.",
   "`timeout` is `@FlowPreview` in 1.11.0, so `freshLoaf` needs `@OptIn(FlowPreview::class)`. Without it you only get a warning.",
   "For `eachLineOnce`, create the set of seen ids inside a `flow { }` builder, so each collection gets a fresh one. A set created outside it is shared by every collector."
  ],
  "done_when": "All 12 tests in `ErrorsTest` pass."
 },
 "drill": {
  "title": "Write catch from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T>` with `flow { }`. It must rethrow what the downstream threw, rethrow the cancellation of its own job, and hand everything else to `action`. Then say which of these reaches `action`: an upstream `withTimeout` firing, the collector throwing, `job.cancel()`.",
  "answer": {
   "lang": "kotlin",
   "src": "fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T> = flow {\n    var fromDownstream: Throwable? = null\n    try {\n        collect { value ->\n            try { emit(value) }\n            catch (e: Throwable) { fromDownstream = e; throw e }   // 1. remember what the collector threw\n        }\n    } catch (e: Throwable) {\n        if (e === fromDownstream) throw e                         // 2. below the net\n        if (e is CancellationException && !currentCoroutineContext().isActive) throw e   // 3. our job\n        action(e)                                                 // 4. from upstream\n    }\n}\n// Only the upstream withTimeout reaches action: it is a CancellationException, but our job is still running.",
   "alt": {
    "lang": "java",
    "src": "// Closest Java equivalent: a push-style source and a Consumer, with the same three checks\nstatic <T> void myCatch(Consumer<Consumer<T>> upstream, Consumer<T> downstream, Function<Throwable, T> action) {\n    RuntimeException[] fromDownstream = {null};\n    try {\n        upstream.accept(v -> {\n            try { downstream.accept(v); }\n            catch (RuntimeException e) { fromDownstream[0] = e; throw e; }   // 1. remember what the consumer threw\n        });\n    } catch (RuntimeException e) {\n        if (e == fromDownstream[0]) throw e;                                 // 2. below the net\n        if (Thread.currentThread().isInterrupted()) throw e;                 // 3. our own task was cancelled\n        downstream.accept(action.apply(e));                                  // 4. from upstream\n    }\n}"
   }
  }
 },
 "recap": [
  "A downstream exception comes out of `emit`. `catch` remembers it and rethrows it, and it rethrows its own job's cancellation. Everything else from upstream reaches the action, a `CancellationException` or `TimeoutCancellationException` included.",
  "Work in `collect { }` is below the net. Put it in `onEach` above `catch`, then call `collect()` or `launchIn`.",
  "`retry(n)` means n retries and n + 1 collections, and each one replays the upstream from the top. Whatever comes after a retry must be idempotent. `retryWhen`'s `attempt` starts at 0, a `delay` in it is the backoff, and the original exception comes out at the end.",
  "`onCompletion`'s cause is `null` on success, the exception on failure, `JobCancellationException` on cancel, and `AbortFlowException` above `take` or `first`. Read a `CancellationException` as stopped, not failed.",
  "`timeout()` throws `TimeoutCancellationException`, a cancellation. Above `retryWhen` it limits each try, below it is a budget, and uncaught in a `launch` it ends silently, so translate it.",
  "The limit: all of this acts on one collector and its own cold flow. When many collectors share one upstream, a failure in it never reaches them, which is the next lesson's surprise."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "Which failure does the `catch` action handle?\n\n```kotlin\nloaves.map { slice(it) }\n    .catch { emit(crackers) }\n    .collect { diner.eat(it) }\n```",
   "options": ["`diner.eat` throws `IllegalStateException`", "`slice` throws `IllegalArgumentException`", "the caller's scope is cancelled while it waits for a loaf", "all three"],
   "answer": 1,
   "why": "`slice` runs above the net, so its exception reaches the action. `diner.eat` runs in the collector, below the net, so its exception goes straight to the caller. The scope's cancellation is the cancellation of the collecting job, which `catch` always lets pass."},
  {"q": "A note fails after its second line on every attempt. It is collected through `retry(3)`. How many times does the collector receive line 1?",
   "options": ["Once: retry carries on after the failure", "3 times", "4 times", "It depends on the backoff"],
   "answer": 2,
   "why": "`retry(3)` means 3 retries, so 4 collections, and each collection runs the cold flow from the top. Lines 1 and 2 are delivered 4 times each, then the fourth failure comes out. A backoff changes when the retries happen, not how many."},
  {"q": "A tally hook `onCompletion { cause -> if (cause == null) ok() else failed() }` sits right above `.first()`. Every order that went well is counted as a failure. Why?",
   "options": ["`first()` stops the upstream by throwing `AbortFlowException`, a `CancellationException`, through it", "`first()` always fails with `NoSuchElementException` first and then retries", "`onCompletion` runs before the value is emitted, so `cause` isn't set yet", "`onCompletion` sees the collector's exception from `first()`'s own collect"],
   "answer": 0,
   "why": "`first()` throws `AbortFlowException` (\"Flow was aborted, no more elements needed\") out of the upstream's `emit` once it has its value. Operators above it see that as the cause. Below `take(1)` or after the terminal call, the flow simply completed. Count `cause is CancellationException` as stopped early, not as a failure."},
  {"q": "Each bakery call must be limited to 300 ms and retried with backoff, and the caller must get an answer or an error within 1 second overall. Which order?",
   "options": ["`.retryWithBackoff().timeout(300.milliseconds).timeout(1.seconds)`", "`.timeout(1.seconds).retryWithBackoff().timeout(300.milliseconds)`", "`.retryWithBackoff().timeout(300.milliseconds)`", "`.timeout(300.milliseconds).retryWithBackoff().timeout(1.seconds)`"],
   "answer": 3,
   "why": "A timeout above `retryWhen` covers one try and is retried, so 300 ms goes first. A timeout below the retries covers the whole sequence, waits included, so the 1 s budget goes after them. With the retries first, a 300 ms timeout would cut the whole sequence at 300 ms."},
  {"q": "From the reactive track: Reactor's `timeout` signals `TimeoutException`. In a Flow collected with `launchIn(scope)`, a `timeout(50.milliseconds)` fires and nothing catches it. What happens?",
   "options": ["The scope's `CoroutineExceptionHandler` logs a `TimeoutException`", "The launched job ends as cancelled, no handler runs, and the scope keeps running", "The whole scope is cancelled", "The flow retries once by default"],
   "answer": 1,
   "why": "Flow's `timeout` throws `TimeoutCancellationException`, a `CancellationException`, and handlers ignore cancellation. The job just ends cancelled, silently. Translate it in `catch` into an exception of your own so the handler sees it. In Reactor this trap doesn't exist, because `TimeoutException` is an ordinary error.",
   "from": "rx-05"}
 ],
 "flashcards": [
  {"front": "Does `catch` handle a `CancellationException`?", "back": "Yes, if the upstream throws it while the collecting job is running (a `TimeoutCancellationException` too). It lets the cancellation of the collecting job pass."},
  {"front": "How does `catch` know an exception came from the collector?", "back": "It wraps the downstream `emit` and remembers what came out of it. That exception is rethrown, never handled."},
  {"front": "`retry(3)`: how many collections, and what does the collector see again?", "back": "Up to 4 collections. Each runs the upstream from the top, so values already emitted are emitted again."},
  {"front": "In `retryWhen { cause, attempt -> }`, what is `attempt` on the first failure?", "back": "0."},
  {"front": "`onCompletion` placed above `first()`: what is `cause` after a lookup that went well?", "back": "`AbortFlowException: Flow was aborted, no more elements needed`, a `CancellationException`. Below `take(1)` it is `null`."},
  {"front": "What does `timeout(300.milliseconds)` throw, and what is its message?", "back": "`TimeoutCancellationException` (a `CancellationException`): \"Timed out waiting for 300ms\"."},
  {"front": "A `timeout()` escapes a `launchIn` job. What happens?", "back": "The job ends cancelled, no `CoroutineExceptionHandler` runs, and the parent scope keeps running. Translate it in `catch` if someone must hear it."}
 ],
 "terms": [
  {"term": "Exception transparency", "plain": "The rule that an exception from downstream belongs to the downstream: once `emit` has thrown, the flow must not emit again."},
  {"term": "Upstream and downstream", "plain": "Everything above an operator in the chain, and everything below it, the collector included."},
  {"term": "catch", "plain": "An operator that handles failures from above it, except the cancellation of the collecting job."},
  {"term": "retryWhen", "plain": "On an upstream failure, asks a predicate with the cause and attempt number, and collects the upstream again if it says yes."},
  {"term": "Idempotent consumer", "plain": "A consumer that gives the same result when it sees the same item twice, for example by skipping line ids it has already seen."},
  {"term": "TimeoutCancellationException", "plain": "What `timeout()` and `withTimeout` throw. It is a `CancellationException`, so handlers ignore it."},
  {"term": "AbortFlowException", "plain": "The internal `CancellationException` that `take` and `first` throw out of the upstream's `emit` to stop it: the signed \"no more, thanks\" note."}
 ],
 "explain_back": {
  "prompt": "A friend asks why `catch { emit(crackers) }` turns a bakery timeout into crackers, but does nothing when the diner leaves and the caller is cancelled. They thought catch never sees a CancellationException. Explain it with the net picture, and say what you'd add if the flow ran in a background `launchIn` job.",
  "answer": "`catch` is a net under the upstream. It wraps the downstream's `emit` and remembers anything the collector throws, which it rethrows, and it rethrows the cancellation of its own collecting job. Everything else that falls from above lands in the net. A `withTimeout` or `timeout()` inside the bakery call throws `TimeoutCancellationException` while our job is still running, so to `catch` it's just an upstream failure, and the action sends out crackers. When the diner leaves, the caller's job is cancelled. That cancellation is the job's own, so the net lets it pass and no crackers are sent, which is what we want. In a background `launchIn` job I'd add a translation. If both bakeries time out, the `TimeoutCancellationException` would escape the launch as a plain cancellation, no exception handler would run and the refresher would stop silently. So I'd convert it in a `catch` into a `BakeryTimeout` exception of my own, which the scope's handler logs."
 },
 "deeper": {
  "minutes": 10,
  "body": "When both sides fail, the upstream wins. If the collector throws `IllegalStateException(\"collector failed\")` and the builder's `finally` then throws `IOException(\"close() failed\")`, the caller sees the `IOException`, with the collector's exception in `suppressed`, and a `catch` above does not run its action. The `Flow` KDoc calls this \"a semantic equivalent of throwing from finally block\", and notes that the exception-handling operators still treat the downstream exception as the root cause.\n\nA failed backup forgets the first bakery. `flow { throw IOException(\"corner bakery closed\") }.catch { emitAll(flow { throw IOException(\"backup bakery closed\") }) }` gives the caller `IOException: backup bakery closed` with no cause and nothing suppressed. If you want both in the logs, attach the first one yourself with `addSuppressed` before you emit from the backup.\n\nDon't retry from inside `catch` with `emitAll(sameFlow)`. The `catch` KDoc points to `retryWhen`, which retries \"without introducing ever-growing stack of suspending calls\".\n\n`withTimeoutOrNull(250) { flow.toList() }` returns `null` and loses the values that arrived before the deadline. Collect into a list you own (`collect { partial += it }`) if you need them. Inside `runBlocking` with a `CoroutineName(\"bread-refresher\")`, the `withTimeout` message names the coroutine: `Coroutine \"bread-refresher\" timed out waiting for 50 ms`.\n\nThe exact boundary of `timeout(100.milliseconds)` depends on how the scheduler orders events at the same instant: under virtual time a 100 ms gap did not time out and a 101 ms gap did. Don't build logic on the equality case.\n\n`onEmpty { emit(default) }` is the counterpart for a flow that completes without a value: a dish with no sauce of its own gets the house sauce, and a dish with one gets its own."
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
