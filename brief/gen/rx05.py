import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l05"
PK = "kotlin/workbench/reactive/l05"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l05."


def code(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


S1 = """`Flux.just(1, 2, 0, 4).map(i -> 8 / i)` emits 8 and 4, then fails on the zero. The 4 is never divided. That is the Reactive Streams rule from lesson 1 of this track: `onError` is a terminal signal, and nothing comes after it.

Reactor's error operators don't bend that rule. They can't resume the failed sequence. They catch the error signal on its way down and replace the rest of the stream with something else. The upstream is already finished.

```java
fees.onErrorReturn(-1)                                       // emit one fallback value, then complete
fees.onErrorResume(e -> cachedFees())                       // switch to a fallback publisher
fees.onErrorMap(ArithmeticException.class,
        e -> new IllegalStateException("bad fee table", e))  // translate it; still an error
```

```kotlin
fees.onErrorReturn(-1)                                       // emit one fallback value, then complete
fees.onErrorResume { cachedFees() }                         // switch to a fallback publisher
fees.onErrorMap(ArithmeticException::class.java) { e ->
    IllegalStateException("bad fee table", e) }              // translate it; still an error
```

On the `8 / i` stream, `onErrorReturn(-1)` gives `[8, 4, -1]`. The fallback takes the place of everything after the error, and the 4 is still lost.

Each of the three has overloads that take an exception class or a predicate. Use them. `onErrorResume(TimeoutException.class, e -> cachedRate())` recovers from the one failure you planned for and lets the others through. A fallback for every `Throwable` also hides the `NullPointerException` in your own mapper, and the dashboard shows cached data for a week before anyone notices.

Position matters. An error operator only sees errors from operators above it. Put `onErrorReturn(-1)` before the `map` and the division by zero sails past it.

`doOnError(e -> log.warn(...))` is the side-effect version: it logs and passes the error on unchanged.

One trap catches tests in particular. `Flux.error(e).subscribe(v -> {})` returns normally. With no error consumer, Reactor reports the error to its `onErrorDropped` hook, which logs `ErrorCallbackNotImplemented` at ERROR level, and your code never hears about it. Always pass an error consumer to `subscribe`, or test with `StepVerifier`, which fails on an error you didn't expect."""

S2 = """A Kafka consumer reads 10,000 settlement messages. Message 4,312 has a bad amount. You want to log it, park it on a dead-letter topic and carry on. `onErrorResume(e -> Mono.empty())` on the whole stream does stop the error, and it also stops the stream: on the demo input it gives `[8, 4]`. Everything after the bad item is gone, because the error ended the upstream before `onErrorResume` saw it.

To survive a bad item, give each item its own small publisher and handle the error there:

```java
amounts.concatMap(i -> Mono.fromCallable(() -> 8 / i)
        .doOnError(e -> log.warn("skipping {}", i, e))
        .onErrorResume(e -> Mono.empty()))            // only this item's Mono ends
```

```kotlin
amounts.concatMap { i ->
    Mono.fromCallable { 8 / i }
        .doOnError { e -> log.warn("skipping {}", i, e) }
        .onErrorResume { Mono.empty() }               // only this item's Mono ends
}
```

This gives `[8, 4, 2]`. The inner `Mono` for the zero failed and was replaced by an empty one. The outer stream never saw an error. Use `concatMap` to keep the order and handle one item at a time, or `flatMap` when items may run concurrently. For the Kafka case, replace `Mono.empty()` with `deadLetters.send(msg, e).then(Mono.empty())`.

Reactor also has `onErrorContinue((e, item) -> ...)`, which produces the same `[8, 4, 2]` here. Don't use it. Its own Javadoc calls it "a specialist operator that can make the behaviour of your reactive chain unclear". It doesn't catch anything itself. It puts a marker in the subscriber context, which flows up the chain, and operators above it that know the marker drop the failing item instead of failing.

That design has three consequences. It acts on operators above it, never below, so `Flux.just(1, 2, 0, 4).onErrorContinue(...).map(i -> 8 / i)` still fails. It only works with operators that support it. And it reaches into library code upstream that never expected an item to be skipped. Someone adds an operator above it six months later, and the error handling changes with no compile error. The inner-publisher version says what happens in the place where it happens."""

S3 = """`retry` doesn't rewind anything. When an error reaches it, it subscribes to its upstream again: a new subscription, so a cold publisher (lesson 2 of this track) does its work again from the start. The failed sequence stays failed.

`retry(2)` on a source that always fails makes **three** attempts, not two, and then passes on the original exception. It retries at once, with no pause. Against a card issuer that's already struggling, that is three calls inside a millisecond.

For remote calls, use `retryWhen` with a `Retry` spec:

```java
issuerCall.retryWhen(Retry.backoff(3, Duration.ofMillis(100))       // 3 retries, waits double from 100 ms
        .filter(e -> e instanceof IssuerUnavailableException))       // only errors worth retrying
```

```kotlin
issuerCall.retryWhen(Retry.backoff(3, Duration.ofMillis(100))       // 3 retries, waits double from 100 ms
    .filter { e -> e is IssuerUnavailableException })                // only errors worth retrying
```

Here is the arithmetic people get wrong. `Retry.backoff(3, 100ms)` means 3 retries, so **4 attempts**. With jitter off, a source that always fails is called at 0, 100, 300 and 700 ms, and at 700 ms the chain fails with a `RetryExhaustedException`. Its message is `Retries exhausted: 3/3`, its cause is the last real error, and `Exceptions.isRetryExhausted(e)` recognises it. An error that the `filter` rejects is not retried and comes through unchanged.

The defaults in Reactor 3.8: the wait doubles each time, the waits run on `Schedulers.parallel()`, and the jitter factor is 0.5. Jitter moves each wait by a random amount of up to half its length, never below the first wait. Keep it in production: a thousand clients that failed together shouldn't all come back in the same millisecond. Turn it off with `.jitter(0)` in tests that check times.

Now the trap. `retry` re-runs only what happens at subscription time. Many hand-written clients do the work when you call the method and wrap the answer: `return Mono.just(response)` or `Mono.error(e)`. Retrying that Mono re-subscribes to the same stored answer, four times, and never calls the issuer again. Wrap the call so it happens per subscription: `Mono.defer(() -> issuer.authorize(id))`. Reactor's `WebClient` is already lazy (each subscription sends a new request), but don't assume the same of every client."""

S4 = """A retry needs an error to react to. A card issuer that accepts the connection and then never answers sends no error at all. Your request waits, holding one of the 20 connections in the pool, until something gives up. With no timeout, nothing does.

`timeout(Duration.ofMillis(500))` signals a `TimeoutException` if no item arrives within 500 ms of subscribing (for a `Flux`, within 500 ms of the previous item), and it cancels the slow upstream. Its clock runs on `Schedulers.parallel()`, so it works under virtual time in tests.

Where you put it decides what it limits:

```java
Mono.defer(() -> issuer.authorize(id))
        .timeout(Duration.ofMillis(500))                 // each attempt gets 500 ms
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::worthRetrying))
        .timeout(Duration.ofSeconds(2));                 // the caller waits 2 s at most, in total
```

```kotlin
Mono.defer { issuer.authorize(id) }
    .timeout(Duration.ofMillis(500))                     // each attempt gets 500 ms
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::worthRetrying))
    .timeout(Duration.ofSeconds(2))                      // the caller waits 2 s at most, in total
```

Above `retryWhen`, the timeout applies to each attempt. Its `TimeoutException` is one more error that the retry handles, if the filter lets it through. Below `retryWhen`, the timeout is a budget for the whole operation, waits included. With only the budget, one hanging attempt uses all 2 seconds and is never retried. Most remote calls want both.

To swap in a fallback, use `timeout(Duration, fallbackMono)` or `onErrorResume(TimeoutException.class, e -> ...)`.

In payments, one fact matters more than the operators. A timeout tells you that you stopped waiting. It doesn't tell you the issuer said no. The authorization may have gone through on the other side while your client was giving up. So a retry must send the same idempotency key as the first attempt, so the issuer can recognise a repeat. And when the retries run out, the honest state is "unknown". Leave the payment pending and let reconciliation settle it, rather than marking it failed and letting the customer pay again."""

X0, PX = 70, 0.8
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 235" role="img" aria-label="Retry.backoff(3, 100 ms) without jitter on a call that always fails: '
       'attempts at 0, 100, 300 and 700 ms with waits of 100, 200 and 400 ms between them, then RetryExhaustedException at 700 ms, '
       'which onErrorResume turns into PENDING.">')
SVG += '<line class="ln-d" x1="50" y1="40" x2="655" y2="40" marker-end="url(#arr)"/>'
for ms in (0, 100, 300, 700):
    SVG += f'<text class="t-s t-m" x="{x(ms):.0f}" y="28" text-anchor="middle">{ms} ms</text>'
    SVG += f'<line class="ln-d" x1="{x(ms):.0f}" y1="44" x2="{x(ms):.0f}" y2="62"/>'
att = [0, 100, 300, 700]
for i, ms in enumerate(att):
    SVG += f'<circle class="box-bad" cx="{x(ms):.0f}" cy="90" r="14"/><text class="t" x="{x(ms):.0f}" y="95" text-anchor="middle">{i + 1}</text>'
for a, b in zip(att, att[1:]):
    SVG += f'<line class="ln-a" x1="{x(a) + 16:.0f}" y1="90" x2="{x(b) - 18:.0f}" y2="90" marker-end="url(#arr)"/>'
    SVG += f'<text class="t-s t-a" x="{(x(a) + x(b)) / 2:.0f}" y="78" text-anchor="middle">+{b - a} ms</text>'
SVG += '<text class="t-s t-code" x="70" y="150">Retry.backoff(3, 100 ms).jitter(0)</text>'
SVG += '<text class="t-s" x="70" y="176">3 retries, so 4 attempts</text>'
SVG += '<text class="t-s t-m" x="70" y="202">every attempt here fails at once</text>'
SVG += f'<line class="ln" x1="{x(700):.0f}" y1="106" x2="{x(700):.0f}" y2="138" marker-end="url(#arr)"/>'
SVG += '<rect class="box-bad" x="460" y="140" width="210" height="32" rx="8"/>'
SVG += '<text class="t-s t-code" x="565" y="161" text-anchor="middle">Retries exhausted: 3/3</text>'
SVG += '<line class="ln" x1="565" y1="172" x2="565" y2="192" marker-end="url(#arr)"/>'
SVG += '<rect class="box-ok" x="460" y="194" width="210" height="32" rx="8"/>'
SVG += '<text class="t-s t-code" x="565" y="215" text-anchor="middle">onErrorResume: PENDING</text>'
SVG += '</svg>'

CJ = '''// Reactor: the policy is a chain of operators on a lazy Mono
Mono<String> authorize(String paymentId) {
    return Mono.defer(() -> issuer.authorize(paymentId))         // a fresh call per attempt
            .timeout(Duration.ofMillis(500))                       // per attempt
            .retryWhen(Retry.backoff(3, Duration.ofMillis(100))    // waits of 100, 200, 400 ms
                    .filter(e -> e instanceof IssuerUnavailableException
                            || e instanceof TimeoutException))
            .onErrorResume(Exceptions::isRetryExhausted,
                    e -> Mono.just("PENDING:" + paymentId));
}'''
CK = '''// Kotlin coroutines: the same policy as a plain loop in a suspend function
suspend fun authorize(paymentId: String): String {
    var wait = 100.milliseconds
    repeat(4) { attempt ->                                       // 1 call + 3 retries
        try {
            return withTimeout(500.milliseconds) { issuer.authorize(paymentId) }   // per attempt
        } catch (e: IssuerUnavailableException) {
            // worth another try
        } catch (e: TimeoutCancellationException) {
            // so is a hang; a decline is not caught, so it reaches the caller
        }
        if (attempt < 3) { delay(wait); wait *= 2 }              // 100, 200, 400 ms
    }
    return "PENDING:$paymentId"
}'''

W0 = '''Mono<Void> post(LedgerEntry entry) {
    return ledger.post(entry, UUID.randomUUID().toString()).retry();
}'''
W0K = '''fun post(entry: LedgerEntry): Mono<Void> =
    ledger.post(entry, UUID.randomUUID().toString()).retry()'''
W2 = '''Mono<Void> post(LedgerEntry entry) {
    String key = entry.idempotencyKey();                              // 1. the entry's own key, never a new one
    return Mono.defer(() -> ledger.post(entry, key))                 // 2. a fresh call per attempt
            .timeout(Duration.ofSeconds(1))                           // 3. no attempt waits forever
            .retryWhen(Retry.backoff(3, Duration.ofMillis(200))       // 4. 3 retries, jitter left on
                    .filter(LedgerErrors::isTransient))               //    a 400 or 409 is final
            .onErrorResume(Exceptions::isRetryExhausted,              // 5. out of retries: park it
                    e -> deadLetters.send(entry, e.getCause()));
}'''
W2K = '''fun post(entry: LedgerEntry): Mono<Void> {
    val key = entry.idempotencyKey                                    // 1. the entry's own key, never a new one
    return Mono.defer { ledger.post(entry, key) }                     // 2. a fresh call per attempt
        .timeout(Duration.ofSeconds(1))                               // 3. no attempt waits forever
        .retryWhen(Retry.backoff(3, Duration.ofMillis(200))           // 4. 3 retries, jitter left on
            .filter(LedgerErrors::isTransient))                       //    a 400 or 409 is final
        .onErrorResume(Exceptions::isRetryExhausted) { e ->           // 5. out of retries: park it
            deadLetters.send(entry, e.cause!!) }
}'''
W3 = '''StepVerifier.withVirtualTime(() -> poster.post(entry))     // build it inside the supplier
        .expectSubscription()
        .thenAwait(Duration.ofSeconds(10))                     // more than any jittered wait
        .verifyComplete();                                     // parked, not failed

assertThat(ledger.keysSeen()).hasSize(4).containsOnly(entry.idempotencyKey());
assertThat(deadLetters.sent()).containsExactly(entry);'''
W3K = '''StepVerifier.withVirtualTime { poster.post(entry) }        // build it inside the supplier
    .expectSubscription()
    .thenAwait(Duration.ofSeconds(10))                         // more than any jittered wait
    .verifyComplete()                                          // parked, not failed

assertThat(ledger.keysSeen()).hasSize(4).containsOnly(entry.idempotencyKey)
assertThat(deadLetters.sent()).containsExactly(entry)'''

DJ = '''Mono<Account> fetch(String id) {
    return Mono.defer(() -> client.fetch(id))                   // fresh call per attempt
            .timeout(Duration.ofSeconds(1))                       // per attempt
            .retryWhen(Retry.backoff(5, Duration.ofMillis(50))
                    .filter(e -> e instanceof IOException || e instanceof TimeoutException)
                    .onRetryExhaustedThrow((spec, signal) -> signal.failure()));   // the real error
}'''
DK = '''fun fetch(id: String): Mono<Account> =
    Mono.defer { client.fetch(id) }                             // fresh call per attempt
        .timeout(Duration.ofSeconds(1))                           // per attempt
        .retryWhen(Retry.backoff(5, Duration.ofMillis(50))
            .filter { e -> e is IOException || e is TimeoutException }
            .onRetryExhaustedThrow { _, signal -> signal.failure() })   // the real error'''

L = {
 "id": "rx-05",
 "title": "Errors, retries and timeouts",
 "minutes": 35,
 "goal": "By the end you can recover from errors without pretending a stream continues, skip bad items safely, and wrap a flaky remote call in a per-attempt timeout, a filtered exponential backoff and a fallback, then prove the timing with virtual time.",
 "warmup": {
  "q": "A call to the card issuer always fails. You wrap it as `Mono.defer(() -> issuer.authorize(id)).retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0))`. How many times is the issuer called, and what reaches the subscriber?",
  "options": [
   "3 calls, then the issuer's own exception",
   "4 calls, then a `RetryExhaustedException` with the issuer's exception as its cause",
   "3 calls, then a `RetryExhaustedException`",
   "4 calls, then the issuer's own exception"
  ],
  "answer": 1,
  "why": "The 3 in `Retry.backoff(3, ...)` counts retries, so there are 4 attempts: at 0, 100, 300 and 700 ms. When the retries run out, the spec fails with `RetryExhaustedException` (\"Retries exhausted: 3/3\") and attaches the last real error as the cause. Plain `retry(3)` also makes 4 attempts but passes on the original exception, which is where the other options come from."
 },
 "sections": [
  {
   "h": "An error ends the stream for good",
   "body": S1,
   "try": {
    "title": "Four ways to handle a division by zero",
    "minutes": 4,
    "steps": [
     "`ErrorsDemo` divides 8 by each of `1, 2, 0, 4` and handles the failure four ways: not at all, `onErrorReturn`, `onErrorResume` and `onErrorMap`. Write down what each line prints.",
     "Run it and compare. Does any version ever print a result for the 4?",
     "Add one more line: `Flux.just(1, 2, 0, 4).onErrorReturn(-1).map(i -> 8 / i)` (the operator before `map`), collected and blocked like the others. Predict first, then run it."
    ],
    "code": code("ErrorsDemo"),
    "expect": "The raw subscriber prints 8 and 4, then the `ArithmeticException`. `onErrorReturn` gives `[8, 4, -1]`, `onErrorResume` gives `[8, 4, 100, 200]`, and `onErrorMap` reports an `IllegalStateException` caused by the `ArithmeticException`. No line ever shows a result for 4: the error ended the source. Your extra line throws `ArithmeticException` from `block()`, because `onErrorReturn` only sees errors from operators above it."
   },
   "refs": [
    {"title": "Reactor reference: Handling errors (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/error-handling.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Skip a bad item inside the item, not on the stream",
   "body": S2,
   "try": {
    "title": "Skip the zero three ways",
    "minutes": 4,
    "steps": [
     "`SkipBadItemsDemo` runs the same four amounts through `onErrorResume` on the whole stream, `onErrorResume` inside a per-item `Mono`, and `onErrorContinue`. Predict the three lists.",
     "Run it.",
     "Now move the `onErrorContinue` line above the `map` (so it reads `amounts.onErrorContinue(...).map(i -> 8 / i)`). Predict what happens, then run it."
    ],
    "code": code("SkipBadItemsDemo"),
    "expect": "The whole-stream version prints `[8, 4]`: the 4 is lost. The per-item version prints `[8, 4, 2]` and logs the skipped zero. `onErrorContinue` also prints `[8, 4, 2]` in its original place. Moved above the `map`, it does nothing and `block()` throws `ArithmeticException`, because it only affects operators upstream of it."
   },
   "refs": [
    {"title": "Flux Javadoc source: onErrorContinue (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}
   ]
  },
  {
   "h": "Retrying means subscribing again",
   "body": S3,
   "figure": {"svg": SVG, "caption": "Retry.backoff(3, 100 ms) with jitter off, against a call that always fails: four attempts, waits that double, and an exhausted error at 700 ms that a fallback can catch."},
   "try": {
    "title": "Count the attempts",
    "minutes": 5,
    "steps": [
     "`RetryDemo` has four parts: a backoff that succeeds on the third call, `retry(2)` on a call that always fails, a backoff that runs out, and `retry(3)` on a Mono built from one eager call. For each part, write down the number of attempts, the times, and the final result.",
     "Run it and compare your numbers.",
     "In part 3, delete `.jitter(0)` and run the demo twice. Watch the times of attempts 2 to 4."
    ],
    "code": code("RetryDemo"),
    "expect": "Part 1 calls at about 0, 50 and 150 ms and prints `APPROVED`. Part 2 makes 3 attempts in the same millisecond and rethrows `issuer down`. Part 3 calls at about 0, 50, 150 and 350 ms, then throws `RetryExhaustedException: Retries exhausted: 3/3` with `issuer down` as the cause. Part 4 calls the issuer once and fails with `issuer busy` after 4 subscriptions: retry re-subscribed to the same stored error. Without jitter the waits are exactly 50, 100 and 200 ms; with the default jitter they change from run to run."
   },
   "refs": [
    {"title": "Retry and RetryBackoffSpec source (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java", "kind": "docs"}
   ]
  },
  {
   "h": "A timeout turns silence into an error you can handle",
   "body": S4,
   "try": {
    "title": "Per attempt or in total",
    "minutes": 4,
    "steps": [
     "`TimeoutDemo` has a rate call that takes 300 ms. It applies a 100 ms timeout, then the same with a fallback, then a 100 ms per-attempt timeout with retries inside a 400 ms total budget. Predict each line, and how many attempts fit in the budget.",
     "Run it.",
     "In the last chain, delete the per-attempt `.timeout(Duration.ofMillis(100))` and keep the 400 ms budget. Predict the result and the number of attempts, then run it."
    ],
    "code": code("TimeoutDemo"),
    "expect": "The plain timeout prints `TimeoutException: Did not observe any item or terminal signal within 100ms` and the slow call is cancelled. The fallback version prints `cached rate 1.07`. The budget run makes 3 attempts (at about 0, 150 and 350 ms) and gives up near 400 ms. Without the per-attempt timeout there is no error to retry, the single 300 ms call fits inside the 400 ms budget, and you get `live rate 1.08` after 1 attempt."
   }
  }
 ],
 "analogy": "Retry with backoff is how you call a busy support line. You don't press redial fifty times a second: you wait a minute, then two, then four, and after a few tries you stop and send an email instead (the fallback). A timeout is hanging up on a line that rings forever. The analogy breaks in two places. The phone tells you \"busy\" and \"no\" apart for you, but in code you have to classify errors yourself, or you will redial a definite no. And when you hang up on a slow line, the other side never acted. A card issuer may have approved the payment just as your timeout fired.",
 "in_your_world": "Your issuer client, your ledger client and your Kafka producer all need the same three decisions: which errors are worth another try, how long one attempt may take, and what happens when the tries run out. In a payment flow the last answer is rarely \"fail\": it is \"pending, reconcile later\", with the same idempotency key on every attempt so the issuer can spot repeats. Watch for stacked retries. A Temporal activity already has a retry policy (initial interval, backoff coefficient, maximum attempts, non-retryable error types), and Quarkus apps often add SmallRye Fault Tolerance `@Retry` on top. Put `Retry.backoff(3, ...)` inside an activity that Temporal retries 5 times and one bad minute at the issuer turns into 20 calls per payment. Pick one layer to own retries.",
 "mistake": "The most common mistake is a retry that doesn't choose. `.retry()` with no argument retries forever, at once, on every error. `.retry(3)` is better, but it still resends a declined card three times and retries the `NullPointerException` in your own mapper. People write it because the first failure they saw was a timeout, and a retry made it go away. The fix is `retryWhen(Retry.backoff(n, firstWait).filter(...))`, where the filter names the errors that a later attempt can fix (timeouts, 503s, connection resets) and everything else fails at once. Then check that the source is lazy, with `Mono.defer` if you are not sure, or the retries will never reach the server.",
 "compare": {
  "title": "One retry policy as a Reactor chain and as a suspend function",
  "java": {"title": "ResilientAuthorizer.java (Reactor)", "src": CJ},
  "kotlin": {"title": "ResilientAuthorizer.kt (coroutines)", "src": CK},
  "note": "Both versions make up to 4 attempts, give each 500 ms, wait 100, 200 and 400 ms between them, let a decline through and return `PENDING` at the end. In Reactor the policy is data: operators you can reorder, and a `Retry` spec you can pass around and reuse, and the result is still a lazy `Mono` that does nothing until subscribed. In the coroutine version the policy is ordinary control flow: a loop, `try`/`catch`, `delay` and `withTimeout`. That is easier to read and to step through in a debugger, but you write the loop yourself, and you must not swallow `CancellationException` by catching `Exception` too broadly (`withTimeout` throws `TimeoutCancellationException`, which is one). Kotlin `Flow` has `retry` and `retryWhen` operators too, and the coroutines track covers them."
 },
 "worked": {
  "title": "Make a ledger write safe to retry",
  "steps": [
   {"say": "A Kafka consumer posts each entry to the ledger service. Someone added `retry()` after a deploy caused a few 503s. Read it and list what can go wrong before reading on.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Four problems. `retry()` with no limit retries forever and at once, so one bad entry stalls the whole partition. It retries a 400 (a bad entry) as eagerly as a 503. Nothing limits how long one attempt may hang. And the idempotency key is a fresh UUID per call of `post`. The retries of this one Mono reuse it, but when Kafka redelivers the message after a rebalance, `post` runs again with a new key, and the ledger has no way to see that it already booked the entry. The key has to come from the entry itself.", "code": "", "lang": ""},
   {"say": "Rebuild it in the order the lesson used: a lazy call, a per-attempt timeout, a filtered backoff, and a fallback for when the retries run out. `LedgerErrors.isTransient` returns true for timeouts, 503s and connection resets.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Test the slow path with virtual time. The jitter is still on, so don't assert exact times: advance the clock further than any possible wait, then check the counts. Four attempts, one key, one dead letter.",
    "code": W3, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A card-issuer call with timeout, backoff and a fallback",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/ResilientAuthorizer.java", f"{lab}/main/{P}/CardIssuer.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l05.*'",
  "steps": [
   "Run the tests once. All five fail. Read the Javadoc on `ResilientAuthorizer`: it lists five rules, and each test checks one of them.",
   "Look at `ScriptedIssuer` in `ResilientAuthorizerTest`. It chooses its answer when `authorize()` is called, not when the Mono is subscribed. Decide what that means for your retry before writing code.",
   "Write `authorize` as one chain: a lazy issuer call, a 500 ms timeout per attempt, `retryWhen` with `Retry.backoff(3, Duration.ofMillis(100))` and no jitter, a filter that lets declines through, and a fallback to `\"PENDING:\" + paymentId` only when the retries are used up.",
   "Run the tests until all five pass. Then read the virtual-time steps in each test: `expectNoEvent(Duration.ofMillis(699))` followed by `thenAwait(Duration.ofMillis(1))` pins the result to exactly 700 ms."
  ],
  "hints": [
   "If \"succeeds on the third attempt\" fails and the issuer was called once, you called `issuer.authorize(paymentId)` directly. Retry then re-subscribes to the same failed Mono. Wrap it in `Mono.defer`.",
   "If the hanging-attempt test ends in a `TimeoutException`, either your timeout sits below `retryWhen` (so it limits the whole call) or your filter does not accept `java.util.concurrent.TimeoutException`.",
   "If the decline test receives `PENDING:p-3`, your fallback catches every error. Use the predicate overload: `onErrorResume(Exceptions::isRetryExhausted, e -> ...)`.",
   "`Retry.backoff(3, ...)` gives 3 retries, so 4 attempts. `jitter(0)` makes the waits exactly 100, 200 and 400 ms."
  ],
  "done_when": "All five tests in `ResilientAuthorizerTest` pass."
 },
 "drill": {
  "title": "Write a retrying fetch from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Mono<Account> fetch(String id)` around `client.fetch(id)` (which returns a `Mono` but may do its work when called). Each attempt gets 1 second. Retry `IOException`s and timeouts up to 5 times, starting with a 50 ms wait. When the retries run out, the caller should get the last real error, not a `RetryExhaustedException`. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "Errors are terminal. `onErrorReturn`, `onErrorResume` and `onErrorMap` replace or translate what is left; they never resume the failed source.",
  "To skip a bad item, handle the error inside a per-item `Mono` in `concatMap` or `flatMap`. `onErrorContinue` acts upstream, depends on operator support, and its own Javadoc discourages it.",
  "`retry` re-subscribes. Make the source lazy (`Mono.defer`) or the retry re-reads a stored answer and never calls the server again.",
  "`retry(n)` makes n + 1 immediate attempts and passes on the original error. `Retry.backoff(3, 100ms)` makes 4 attempts with waits of 100, 200 and 400 ms, then fails with `RetryExhaustedException`.",
  "Filter what you retry, keep jitter in production, and turn it off with `jitter(0)` in tests that check times.",
  "`timeout` above `retryWhen` limits each attempt; below it, the whole operation. A timeout means you stopped waiting, not that the other side said no."
 ],
 "quiz": [
  {"q": "What does `Flux.just(5, 10, 0, 20).map(i -> 100 / i).onErrorReturn(-1).collectList().block()` return?",
   "options": ["`[20, 10, -1, 5]`", "`[20, 10, -1]`", "`[20, 10, 5]`", "It throws `ArithmeticException`"],
   "answer": 1,
   "why": "The division by zero ends the source, so 20 is never divided. `onErrorReturn` replaces the rest of the stream with one value and completes. The first option assumes the stream continues after the fallback, and the third is what per-item handling would give."},
  {"q": "An exchange-rate call sometimes hangs. Which chain retries a hanging attempt? (`ofMillis` and `ofSeconds` are `Duration` factories.)",
   "options": [
    "`Mono.defer(this::rate).retryWhen(Retry.backoff(3, ofMillis(100))).timeout(ofSeconds(2))`",
    "`Mono.defer(this::rate).timeout(ofMillis(500)).retryWhen(Retry.backoff(3, ofMillis(100)))`",
    "`Mono.defer(this::rate).retryWhen(Retry.backoff(3, ofMillis(100)))`",
    "`Mono.defer(this::rate).retry(3)`"
   ],
   "answer": 1,
   "why": "Only a timeout above `retryWhen` turns each hanging attempt into an error that the retry can see. In the first option the timeout is a total budget: the first attempt hangs for 2 seconds and is never retried. The last two have no timeout, so a hang produces no error at all and nothing is retried."},
  {"q": "A Kafka consumer must log and skip messages whose amount fails to parse, and keep consuming. Which is the right shape?",
   "options": [
    "`messages.map(this::parse).onErrorResume(e -> Mono.empty())`",
    "`messages.map(this::parse).onErrorContinue((e, m) -> log(m))`",
    "`messages.concatMap(m -> Mono.fromCallable(() -> parse(m)).onErrorResume(e -> logAndSkip(m, e)))`",
    "`messages.map(this::parse).retry()`"
   ],
   "answer": 2,
   "why": "Handling the error inside each message's own `Mono` ends only that inner Mono, so the outer stream keeps going. The first option ends the whole stream at the first bad message. `onErrorContinue` happens to work here, but it acts on operators upstream of it and can leak into library code; its Javadoc recommends the inner-publisher shape. `retry()` re-subscribes to the consumer forever and hits the same bad message again."},
  {"q": "`issuer.authorize(id)` always fails with `IssuerUnavailableException`. What does `Mono.defer(() -> issuer.authorize(id)).retry(2).block()` do?",
   "options": [
    "Calls the issuer 2 times, then throws `RetryExhaustedException`",
    "Calls the issuer 3 times, 100 ms apart, then throws `IssuerUnavailableException`",
    "Calls the issuer 3 times with no pause, then throws `IssuerUnavailableException`",
    "Calls the issuer once, because `retry` re-uses the first result"
   ],
   "answer": 2,
   "why": "`retry(n)` means n retries, so 3 attempts, all back to back, and it rethrows the original error. Pauses and `RetryExhaustedException` come from `retryWhen(Retry.backoff(...))`. Because of `Mono.defer`, each attempt really calls the issuer; without it, a client that does the work on call would be called once."},
  {"q": "From \"Mono and Flux: nothing happens until you subscribe\": a teammate writes `Mono.just(issuerClient.authorizeBlocking(id)).retry(3)`. The call fails on the first try. How many times does the issuer receive a request?",
   "options": ["Once, and the exception is thrown before `retry` exists", "Four times", "Three times", "Zero times, because nothing is subscribed"],
   "answer": 0,
   "why": "`Mono.just` takes a value, so Java evaluates `authorizeBlocking(id)` first, at assembly time. It throws right there, out of the line that builds the pipeline, and `retry(3)` is never even created. Even if it had returned a value, `Mono.just` would replay that same value to every subscriber. Use `Mono.fromCallable` or `Mono.defer` so each subscription makes the call.",
   "from": "rx-02"}
 ],
 "flashcards": [
  {"front": "`Flux.just(1, 2, 0, 4).map(i -> 8 / i).onErrorReturn(-1)`: what is emitted?", "back": "`8, 4, -1`, then complete. The error ended the source, so 4 is never processed."},
  {"front": "How do you skip one bad item in a Flux without ending the stream?", "back": "Process each item in its own `Mono` inside `concatMap`/`flatMap`, and put `onErrorResume` on that inner Mono."},
  {"front": "Why is `onErrorContinue` discouraged?", "back": "It acts on operators upstream of it (not downstream), only works with operators that support it, and can leak into library code. Its own Javadoc says so."},
  {"front": "`retry(2)` on a source that always fails: how many attempts, and which error?", "back": "3 attempts with no pause, then the original error."},
  {"front": "`Retry.backoff(3, 100ms).jitter(0)` on a source that always fails: attempts, timing, error?", "back": "4 attempts at 0, 100, 300 and 700 ms, then `RetryExhaustedException` (\"Retries exhausted: 3/3\") with the last error as its cause."},
  {"front": "Why can `retry` fail to call the server again?", "back": "It re-subscribes. If the Mono was built from a call made at assembly (`Mono.just(call())` or a client that calls eagerly), it replays the stored answer. Wrap it in `Mono.defer`."},
  {"front": "`timeout` above vs below `retryWhen`?", "back": "Above: each attempt gets the time, and a timeout is retried. Below: one budget for the whole operation, waits included."}
 ],
 "terms": [
  {"term": "Fallback", "plain": "What a stream switches to when an error arrives: a value, another publisher, or a different error."},
  {"term": "Retry", "plain": "Subscribing to the source again after an error, so a cold source does its work again."},
  {"term": "Exponential backoff", "plain": "Waiting longer before each retry, usually doubling: 100 ms, 200 ms, 400 ms."},
  {"term": "Jitter", "plain": "A random change to each backoff wait, so many clients that failed together don't retry at the same instant."},
  {"term": "RetryExhaustedException", "plain": "The error `Retry.backoff` and `Retry.max` signal when the retries run out; the cause is the last real error."},
  {"term": "Transient error", "plain": "A failure that a later attempt may not repeat: a timeout, a 503, a connection reset."},
  {"term": "Idempotency key", "plain": "A unique id sent with a request, so the server can tell a retry from a new request and do the work once."}
 ],
 "explain_back": {
  "prompt": "A teammate added `.retry(3)` to the issuer call and says \"now it retries three times, so a blip can't fail a payment\". Explain in your own words what that line really does, and what you would write instead.",
  "answer": "`retry(3)` re-subscribes up to three times, so there are four attempts, one right after the other with no pause, and then the original error comes out. It retries every error, including a decline that will never change and bugs in our own code. If the client did its call when the method was invoked, the retries just re-read the stored failure and the issuer is called once. I would make the call lazy with `Mono.defer`, give each attempt a timeout, use `retryWhen(Retry.backoff(3, Duration.ofMillis(100)))` with a filter for timeouts and unavailable errors, keep the jitter on, and decide what happens when the retries run out: for a payment, mark it pending and reconcile, with the same idempotency key on every attempt."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Transient errors.** `Retry.max(2).transientErrors(true)` (also on `backoff`) counts retries in a row and resets the count after a successful `onNext`. That suits long-lived streams, such as a Kafka consumer, that fail now and then: each burst of failures gets its own budget instead of using up a lifetime total. The reference guide's example fails twice, emits, fails twice more and then succeeds: `Retry.max(2).transientErrors(true)` gets through, and plain `Retry.max(2)` runs out in the second burst.\n\n**Other specs.** `Retry.fixedDelay(5, Duration.ofSeconds(1))` waits the same time between retries. `Retry.indefinitely()` never gives up, so pair it with a filter. Every spec has `doBeforeRetry(signal -> ...)` for logging the attempt number and `onRetryExhaustedThrow(...)` to choose the final error.\n\n**The companion.** `retryWhen` takes a function from a `Flux<RetrySignal>` (one signal per error) to a companion publisher. Each item the companion emits triggers one retry; if it completes, the sequence completes without error; if it errors, that error goes downstream. `Retry.backoff` is a ready-made companion built on `Mono.delay`, which is why its waits run on `Schedulers.parallel()` and why virtual time controls them.\n\n**Repeat is the other loop.** `repeat` re-subscribes after a *successful* completion, for polling. Reactor 3.8 added `RepeatSpec` for `repeatWhen`, the counterpart of `Retry` for repeats.\n\n**Fatal errors.** Reactor throws some errors straight up the stack instead of turning them into `onError`, such as `OutOfMemoryError` and `StackOverflowError` (see `Exceptions.throwIfFatal`). No error operator will catch those, and you shouldn't want one to."
 },
 "sources": [
  {"title": "Reactor reference: Handling errors (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/error-handling.adoc"},
  {"title": "Retry source and Javadoc (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/util/retry/Retry.java"},
  {"title": "RetryBackoffSpec source: backoff formula, jitter and exhaustion message (3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java"},
  {"title": "Flux Javadoc source: timeout, onErrorContinue, retryWhen (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java"}
 ]
}
out = ROOT / "content/lessons/rx-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
