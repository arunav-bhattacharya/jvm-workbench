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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """Picture the bakery's oven breaking down at ten in the morning, halfway through a tray of rye. The packer has boxed four loaves. Then nothing more comes down the belt, only a note: the oven has stopped. She can't make a broken oven finish the tray. She can fill the box with yesterday's bread, switch to the backup oven, or ask for the whole tray to be baked again once the repairman has had a minute.

Reactor, the library this track uses, gives your code the same choices, and no others, because an error ends a stream for good. The easy traps are to think that an error operator patches the hole so the stream carries on, and to think that `retry(3)` means three tries. (It means four.)

Combining streams ended with every combinator giving up at the first error. In this lesson, we'll watch an error end a stream and skip one bad item without stopping the rest. Then we'll retry a flaky call to the flour mill with growing pauses, and put a timer on a call that never answers. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_RAW = """Flux<Integer> perBox = Flux.just(1, 2, 0, 4).map(i -> 8 / i);       // 8 loaves into i boxes
perBox.subscribe(v -> System.out.println("raw: " + v),
        e -> System.out.println("raw: error " + e));"""
K_RAW = """val perBox: Flux<Int> = Flux.just(1, 2, 0, 4).map { i -> 8 / i }     // 8 loaves into i boxes
perBox.subscribe({ v -> println("raw: $v") },
    { e -> println("raw: error $e") })"""
J_OPS = """perBox.onErrorReturn(-1)                                       // one loaf from yesterday, then close the box
perBox.onErrorResume(e -> backupOven())                        // switch to the backup oven's belt
perBox.onErrorMap(ArithmeticException.class,
        e -> new IllegalStateException("bad box count", e))    // a clearer note; still an error"""
K_OPS = """perBox.onErrorReturn(-1)                                       // one loaf from yesterday, then close the box
perBox.onErrorResume { backupOven() }                          // switch to the backup oven's belt
perBox.onErrorMap(ArithmeticException::class.java) { e ->
    IllegalStateException("bad box count", e) }                // a clearer note; still an error"""

S0 = """Start with the smallest stream that breaks. The bakery's program shares a tray of 8 loaves equally among some boxes, and the box counts arrive on a stream, one after another: 1, 2, 0 and 4. Zero boxes is a mistake in the data, and `8 / 0` throws.

""" + pair(J_RAW, K_RAW) + """

The `Flux` is the **publisher**, the source of the stream: Reactor's type for zero or more items. The two lambdas make up its **subscriber**, the receiver, one for items and one for errors. `ErrorsDemo`, in the Try it, printed:

```text
raw: 8
raw: 4
raw: error java.lang.ArithmeticException: / by zero
```

The 4 was never divided. That's the rule from Why reactive: `onError` is a **terminal signal**, a signal after which nothing else arrives. On the bakery line, it's the oven breaking down halfway through a tray. The belt stops, a note comes down instead of a loaf, and that tray is over.

The packer can't make a broken oven finish the tray. She can only decide what goes in the box instead, and Reactor's error **operators**, the methods that add a station to the belt, make the same three choices:

""" + pair(J_OPS, K_OPS) + """

`onErrorReturn` emits one fallback value and completes. `onErrorResume` switches to a fallback publisher. `onErrorMap` turns one error into a more useful one, and the stream still fails. The demo runs all three:

```text
onErrorReturn: [8, 4, -1]
onErrorResume: [8, 4, 100, 200]
onErrorMap: java.lang.IllegalStateException: bad box count caused by java.lang.ArithmeticException: / by zero
```

No line has a result for the 4. Each operator caught the error signal on its way down and replaced the rest of the stream with something else. The source above it had already finished.

Each of the three has versions that take an exception class or a test, called a predicate. Use them. `onErrorResume(TimeoutException.class, e -> yesterdaysPrice())` recovers from the one failure you planned for and lets the others through. A fallback for every `Throwable` also hides the `NullPointerException` in your own code, and the shop shows yesterday's prices for a week before anyone notices.

Position matters as well. An error operator only sees errors from the operators above it, the ones nearer the source. Put `onErrorReturn(-1)` before the `map`, and the division by zero sails past it. `doOnError(e -> log.warn(...))` is the side-effect version: it logs the error and passes it on unchanged.

**An error ends the stream. Error operators replace what's left; they never resume it.**

One trap catches tests in particular. `Flux.error(e).subscribe(v -> {})` returns normally. With no error handler, Reactor only logs `ErrorCallbackNotImplemented`, as Mono and Flux showed, and your code never hears about it. Always pass an error handler to `subscribe`, or test with `StepVerifier`, a test tool from Reactor that subscribes and checks every signal (lesson 8 of this track).

So one bad box count cost us the 4. In a stream of 10,000 order lines, the same mistake would cost us thousands."""

# ---------------------------------------------------------------- section 1
J_ITEM = """boxCounts.concatMap(i -> Mono.fromCallable(() -> 8 / i)
        .doOnError(e -> log.warn("skipping {}", i, e))
        .onErrorResume(e -> Mono.empty()))            // only this item's Mono ends"""
K_ITEM = """boxCounts.concatMap { i ->
    Mono.fromCallable { 8 / i }
        .doOnError { e -> log.warn("skipping {}", i, e) }
        .onErrorResume { Mono.empty() }               // only this item's Mono ends
}"""

S1 = """Picture a nightly job that reads the day's 10,000 order lines. Line 4,312 says a customer wants zero boxes. You want to log that line, put it on a pile for a person to check, and carry on with the other 5,688.

The first idea is `onErrorResume(e -> Mono.empty())` on the whole stream. `Mono.empty()` is a publisher that completes at once with no item. It does stop the error, and it also stops the job. `SkipBadItemsDemo` tries that idea on our four box counts:

```text
onErrorResume on the stream: [8, 4]
```

Everything after the bad item is gone, because the error ended the source before `onErrorResume` saw it. The fix is to give each item its own small publisher, so that an error ends only that one:

""" + pair(J_ITEM, K_ITEM) + """

`concatMap`, from Transforming streams, runs one inner publisher at a time, in order. Each inner here is a `Mono`, Reactor's type for one item or none, built with `fromCallable`, which turns a thrown exception into an error signal. The `Mono` for the zero fails, and `onErrorResume` replaces it with an empty one. The outer stream never sees an error:

```text
  skipping 0: / by zero
onErrorResume per item:      [8, 4, 2]
```

On the bakery line, that's the inspector lifting one bad loaf off the belt while the oven keeps baking. Use `concatMap` to keep the order, or `flatMap` when items may be handled at the same time. For the nightly job, replace `Mono.empty()` with `toCheck.add(line, e).then(Mono.empty())`, which puts the line on the pile first.

Reactor also has `onErrorContinue((e, item) -> ...)`, and on this input it prints the same `[8, 4, 2]`. Don't use it. Its own Javadoc calls it "a specialist operator that can make the behaviour of your reactive chain unclear". It doesn't catch anything itself. It leaves a marker that travels up the chain, and the operators above it that know the marker drop the failing item instead of failing.

That design has three consequences. It acts on operators above it, never below, so `Flux.just(1, 2, 0, 4).onErrorContinue(...).map(i -> 8 / i)` still fails. It only works with operators that support it. And it reaches into library code above it that never expected an item to be skipped. Someone adds an operator above it six months later, and the error handling changes with no compile error. The per-item version says what happens in the place where it happens.

**To skip a bad item, handle the error inside that item's own publisher.**

Skipping suits a bad line of data, which will be just as bad tomorrow. A mill that is busy right now is a different case: in a moment, the same request may work."""

# ---------------------------------------------------------------- section 2
J_BACKOFF = """Mono.defer(() -> mill.order(orderId))
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))     // 3 retries, waits double from 100 ms
                .filter(e -> e instanceof MillBusyException))    // only errors worth another try"""
K_BACKOFF = """Mono.defer { mill.order(orderId) }
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100))         // 3 retries, waits double from 100 ms
        .filter { e -> e is MillBusyException })                 // only errors worth another try"""

S2 = """Here is the running example for the rest of this lesson. Every morning, the bakery's program orders flour from the mill. The mill's ordering service is a **web service**, a program on another computer that answers over the network, and it has three moods. Usually it says `CONFIRMED`. Sometimes it's busy and fails with `MillBusyException`, and a minute later the same order goes through. Now and then it refuses with `OrderRefusedException`, because there's no rye flour this week, and asking again won't change that.

The busy case calls for another try. `retry` doesn't rewind anything, though. When an error reaches it, it subscribes to its source again. That's a new subscription, so a **cold** publisher, one that does its work again for every subscriber (Mono and Flux), starts over from the beginning. The failed run stays failed. On the bakery line, `retry` asks for the whole order to be baked again, from the first loaf.

Here the picture breaks in a way worth knowing. A repaired oven carries on where it stopped, but a retried `Flux` starts again from its first item, so the packer may box rye-1 twice. For a `Mono` with one answer, starting over is exactly what we want.

`retry(2)` on a source that always fails makes **three** attempts, not two, and then passes on the original exception. It retries at once, with no pause. `RetryDemo`, in the Try it, shows it:

```text
2. retry(2) on a source that always fails
  [  5 ms] attempt 1
  [  6 ms] attempt 2
  [  6 ms] attempt 3
  -> java.lang.IllegalStateException: mill down
```

Three calls in about one millisecond. A mill that is already struggling won't feel helped.

For a call to another computer, use `retryWhen` with a `Retry` spec, a small object that describes the policy:

""" + pair(J_BACKOFF, K_BACKOFF) + """

**Exponential backoff** means waiting longer before each retry, usually twice as long each time. Here is the arithmetic people get wrong. `Retry.backoff(3, 100ms)` means 3 retries, so **4 attempts**. With the random part switched off, a source that always fails is called at 0, 100, 300 and 700 ms, as the figure shows. At 700 ms the chain fails with `RetryExhaustedException`. Its message is `Retries exhausted: 3/3`, its cause is the last real error, and `Exceptions.isRetryExhausted(e)` recognises it. An error that the `filter` rejects, such as a refusal, isn't retried at all and reaches the subscriber unchanged.

The demo's third part runs the same policy with a first wait of 50 ms. On this busy machine it printed:

```text
3. backoff exhausted
  [  0 ms] attempt 1
  [ 53 ms] attempt 2
  [155 ms] attempt 3
  [356 ms] attempt 4
  -> reactor.core.Exceptions$RetryExhaustedException: Retries exhausted: 3/3
     cause: java.lang.IllegalStateException: mill down
```

Those are waits of 50, 100 and 200 ms, plus a few milliseconds of a loaded machine.

The defaults in Reactor 3.8: the wait doubles each time, the waits run on `Schedulers.parallel()`, a small set of Reactor's own threads (lesson 6 of this track), and the jitter factor is 0.5. **Jitter** moves each wait by a random amount of up to half its length, but never below the first wait. Keep it in production. A thousand bakeries that failed together shouldn't all call the mill again in the same millisecond. Turn it off with `.jitter(0)` in tests that check times.

Now the trap, and it's the one from Mono and Flux. `retry` runs again only what happens at subscription time. Many hand-written clients do the work when you call the method, and wrap the answer they already have: `return Mono.just(answer)` or `Mono.error(e)`. Retrying that `Mono` subscribes four times to the same stored answer and never calls the mill again. The demo's last part does exactly that:

```text
4. retry(3) on a Mono built from one eager call
  [  0 ms] attempt 1
  -> java.lang.IllegalStateException: mill busy after 4 subscriptions
```

Four subscriptions, one call. Wrap the call so that it happens per subscription: `Mono.defer(() -> mill.order(orderId))`. The reactive `WebClient` of Spring, the toolkit that Reactor comes from, is lazy already: each subscription sends a new request. Don't assume that of every client.

**A retry subscribes again. Make the source lazy, and choose which errors deserve another try.**

Every retry so far had an error to react to. The hardest failure sends none."""

ASIDE = {
    "title": "What if something else already retries?",
    "body": "Some programs run their work inside a tool that retries failed jobs by itself, such as a job scheduler or a framework with a retry setting. If that layer tries a job 5 times, and the job's own chain makes 4 attempts, one bad minute at the mill turns into 20 calls for a single order. Pick one layer to own the retries, and let the others fail fast. Look for retry settings in configuration files as well as in code, because that is where the second layer usually hides.",
}

# ---------------------------------------------------------------- section 3
J_PLACE = """Mono.defer(() -> mill.order(orderId))
        .timeout(Duration.ofMillis(500))                 // each attempt gets 500 ms
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::worthRetrying))
        .timeout(Duration.ofSeconds(2));                 // the caller waits 2 s at most, in total"""
K_PLACE = """Mono.defer { mill.order(orderId) }
    .timeout(Duration.ofMillis(500))                     // each attempt gets 500 ms
    .retryWhen(Retry.backoff(3, Duration.ofMillis(100)).filter(this::worthRetrying))
    .timeout(Duration.ofSeconds(2))                      // the caller waits 2 s at most, in total"""

S3 = """Sometimes the mill accepts the connection and then never answers. No item, no error, nothing. That's the most polite failure there is, with no complaint at all, and your code waits along with it. A retry needs an error to react to, so without a timer, nothing ever gives up.

`timeout(Duration.ofMillis(500))` is the kitchen timer. If no item arrives within 500 ms of subscribing, it signals a `TimeoutException` and cancels the slow call above it. (For a `Flux`, the 500 ms count from the previous item.) Its clock runs on `Schedulers.parallel()` too, which is how a test can fake it. `TimeoutDemo`, in the Try it, asks for the flour price from a service that takes 300 ms, with a 100 ms timer:

```text
  slow call cancelled
timeout: java.util.concurrent.TimeoutException: Did not observe any item or terminal signal within 100ms in 'peek' (and no fallback has been configured)
```

To swap in a fallback instead, use `timeout(Duration, fallbackMono)` or `onErrorResume(TimeoutException.class, e -> ...)`. The demo's second run falls back to `yesterday's price 0.90`.

Where you put the timer decides what it limits:

""" + pair(J_PLACE, K_PLACE) + """

Above `retryWhen`, nearer the source, the timeout applies to each attempt. Its `TimeoutException` is one more error that the retry handles, if the filter lets it through. Below `retryWhen`, the timeout is a budget for the whole operation, waits included. With only the budget, one hanging attempt uses up all 2 seconds and is never retried. Most calls to another computer want both. The demo's last run gives each attempt 100 ms inside a 400 ms budget, and the 300 ms call never fits:

```text
budget: gave up after 3 attempts and 423 ms: TimeoutException
```

Now the fact that matters more than any operator. A timeout tells you that you stopped waiting. It doesn't tell you that the mill said no. The order may have reached the mill just as your timer rang. The picture breaks here too: when a kitchen timer rings, you can open the oven and look, while `timeout` can't see the far side at all.

That has two consequences for the retry. Every attempt must send the same order number, so the mill can see that the second message is a repeat and deliver one load of flour, not two. And when the retries run out, the honest answer is "we don't know yet". Mark the order pending and check with the mill later. Marking it failed invites someone to order again, and the bakery pays for two loads of flour.

**A timeout means you stopped waiting, not that the other side said no.**

That's the whole policy: a lazy call, a timer per attempt, a filtered backoff, and an honest fallback. The lab asks you to build it, and to prove its timing without waiting a single real millisecond."""

# ---------------------------------------------------------------- figure
X0, PX = 70, 0.8
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 235" role="img" aria-label="Retry.backoff(3, 100 ms) without jitter on a call to the mill that always fails: '
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
SVG += '<text class="t-s t-m" x="70" y="202">every call to the mill fails here</text>'
SVG += f'<line class="ln" x1="{x(700):.0f}" y1="106" x2="{x(700):.0f}" y2="138" marker-end="url(#arr)"/>'
SVG += '<rect class="box-bad" x="460" y="140" width="210" height="32" rx="8"/>'
SVG += '<text class="t-s t-code" x="565" y="161" text-anchor="middle">Retries exhausted: 3/3</text>'
SVG += '<line class="ln" x1="565" y1="172" x2="565" y2="192" marker-end="url(#arr)"/>'
SVG += '<rect class="box-ok" x="460" y="194" width="210" height="32" rx="8"/>'
SVG += '<text class="t-s t-code" x="565" y="215" text-anchor="middle">onErrorResume: PENDING</text>'
SVG += '</svg>'

# ---------------------------------------------------------------- closing
CLOSING = """We started with an oven that broke down halfway through a tray. A Reactor stream behaves the same way: an error ends it, and error operators only decide what goes in the box instead. `retry` bakes the whole order again, so it needs a lazy source, growing pauses and a filter. A timer turns silence into an error, but never tells you the mill said no.

Now search your own code for `retry(` with no filter, and for a `Mono.just(` just above a retry.

Next, we'll look at threads. The pauses and the timer in this lesson ran on threads named `parallel`. Who decides which thread works each station, and what happens when one station makes a slow phone call?"""

# ---------------------------------------------------------------- compare, worked, drill
CJ = '''// Reactor: the policy is a chain of operators on a lazy Mono
Mono<String> place(String orderId) {
    return Mono.defer(() -> mill.order(orderId))                  // a fresh call per attempt
            .timeout(Duration.ofMillis(500))                       // per attempt
            .retryWhen(Retry.backoff(3, Duration.ofMillis(100))    // waits of 100, 200, 400 ms
                    .filter(e -> e instanceof MillBusyException
                            || e instanceof TimeoutException))
            .onErrorResume(Exceptions::isRetryExhausted,
                    e -> Mono.just("PENDING:" + orderId));
}'''
CK = '''// Kotlin coroutines: the same policy as a plain loop in a suspend function
suspend fun place(orderId: String): String {
    var wait = 100.milliseconds
    repeat(4) { attempt ->                                       // 1 call + 3 retries
        try {
            return withTimeout(500.milliseconds) { mill.order(orderId) }   // per attempt
        } catch (e: MillBusyException) {
            // worth another try
        } catch (e: TimeoutCancellationException) {
            // so is a hang; a refusal is not caught, so it reaches the caller
        }
        if (attempt < 3) { delay(wait); wait *= 2 }              // 100, 200, 400 ms
    }
    return "PENDING:$orderId"
}'''

W0 = '''Mono<Void> book(Delivery delivery) {
    return courier.book(delivery, UUID.randomUUID().toString()).retry();
}'''
W0K = '''fun book(delivery: Delivery): Mono<Void> =
    courier.book(delivery, UUID.randomUUID().toString()).retry()'''
W2 = '''Mono<Void> book(Delivery delivery) {
    String number = delivery.bookingNumber();                         // 1. the delivery's own number, never a new one
    return Mono.defer(() -> courier.book(delivery, number))           // 2. a fresh call per attempt
            .timeout(Duration.ofSeconds(1))                            // 3. no attempt waits forever
            .retryWhen(Retry.backoff(3, Duration.ofMillis(200))        // 4. 3 retries, jitter left on
                    .filter(CourierErrors::isTemporary))               //    a refusal is final
            .onErrorResume(Exceptions::isRetryExhausted,               // 5. out of retries: a person checks it
                    e -> toCheck.add(delivery, e.getCause()));
}'''
W2K = '''fun book(delivery: Delivery): Mono<Void> {
    val number = delivery.bookingNumber                               // 1. the delivery's own number, never a new one
    return Mono.defer { courier.book(delivery, number) }              // 2. a fresh call per attempt
        .timeout(Duration.ofSeconds(1))                                // 3. no attempt waits forever
        .retryWhen(Retry.backoff(3, Duration.ofMillis(200))            // 4. 3 retries, jitter left on
            .filter(CourierErrors::isTemporary))                       //    a refusal is final
        .onErrorResume(Exceptions::isRetryExhausted) { e ->            // 5. out of retries: a person checks it
            toCheck.add(delivery, e.cause!!) }
}'''
W3 = '''StepVerifier.withVirtualTime(() -> vans.book(delivery))      // build it inside the supplier
        .expectSubscription()
        .thenAwait(Duration.ofSeconds(10))                     // more than any jittered wait
        .verifyComplete();                                     // put aside for a person, not failed

assertThat(courier.numbersSeen()).hasSize(4).containsOnly(delivery.bookingNumber());
assertThat(toCheck.added()).containsExactly(delivery);'''
W3K = '''StepVerifier.withVirtualTime { vans.book(delivery) }        // build it inside the supplier
    .expectSubscription()
    .thenAwait(Duration.ofSeconds(10))                         // more than any jittered wait
    .verifyComplete()                                          // put aside for a person, not failed

assertThat(courier.numbersSeen()).hasSize(4).containsOnly(delivery.bookingNumber)
assertThat(toCheck.added()).containsExactly(delivery)'''

DJ = '''Mono<Recipe> recipe(String name) {
    return Mono.defer(() -> recipes.fetch(name))                  // fresh call per attempt
            .timeout(Duration.ofSeconds(1))                         // per attempt
            .retryWhen(Retry.backoff(5, Duration.ofMillis(50))
                    .filter(e -> e instanceof IOException || e instanceof TimeoutException)
                    .onRetryExhaustedThrow((spec, signal) -> signal.failure()));   // the real error
}'''
DK = '''fun recipe(name: String): Mono<Recipe> =
    Mono.defer { recipes.fetch(name) }                            // fresh call per attempt
        .timeout(Duration.ofSeconds(1))                             // per attempt
        .retryWhen(Retry.backoff(5, Duration.ofMillis(50))
            .filter { e -> e is IOException || e is TimeoutException }
            .onRetryExhaustedThrow { _, signal -> signal.failure() })   // the real error'''

L = {
 "id": "rx-05",
 "title": "Errors, retries and timeouts",
 "minutes": 35,
 "goal": "By the end you can recover from errors without pretending a stream continues, skip bad items safely, and wrap a flaky call to another computer in a per-attempt timeout, a filtered exponential backoff and a fallback, then prove the timing with virtual time.",
 "opening": OPENING,
 "warmup": {
  "q": "The bakery's program orders flour from a mill whose ordering service always fails. You wrap the call as `Mono.defer(() -> mill.order(id)).retryWhen(Retry.backoff(3, Duration.ofMillis(100)).jitter(0))`. How many times is the mill called, and what reaches the subscriber?",
  "options": [
   "3 calls, then the mill's own exception",
   "4 calls, then a `RetryExhaustedException` with the mill's exception as its cause",
   "3 calls, then a `RetryExhaustedException`",
   "4 calls, then the mill's own exception"
  ],
  "answer": 1,
  "why": "The 3 in `Retry.backoff(3, ...)` counts retries, so there are 4 attempts: at 0, 100, 300 and 700 ms. When the retries run out, the spec fails with `RetryExhaustedException` (\"Retries exhausted: 3/3\") and attaches the last real error as its cause. Plain `retry(3)` also makes 4 attempts but passes on the original exception, which is where the tempting wrong options come from. The section on retrying counts the attempts one by one."
 },
 "sections": [
  {
   "h": "An error ends the stream, and error operators can only replace the rest",
   "body": S0,
   "try": {
    "title": "Four ways to handle zero boxes",
    "minutes": 4,
    "steps": [
     "`ErrorsDemo` shares 8 loaves among `1, 2, 0, 4` boxes and handles the failure four ways: not at all, `onErrorReturn`, `onErrorResume` and `onErrorMap`. Write down what each line will print.",
     "Run it and compare. Does any version ever print a result for the 4?",
     "Add one more line: `Flux.just(1, 2, 0, 4).onErrorReturn(-1).map(i -> 8 / i)` (the error operator before `map`), collected and blocked like the others. Predict first, then run it."
    ],
    "code": code("ErrorsDemo"),
    "expect": "The raw subscriber prints 8 and 4, then the `ArithmeticException`. `onErrorReturn` gives `[8, 4, -1]`, `onErrorResume` gives `[8, 4, 100, 200]`, and `onErrorMap` reports an `IllegalStateException: bad box count` caused by the `ArithmeticException`. No line ever shows a result for 4: the error ended the source. Your extra line throws `ArithmeticException` from `block()`, because `onErrorReturn` only sees errors from operators above it, and the `map` is below."
   },
   "refs": [
    {"title": "Reactor reference: Handling errors (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/error-handling.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Skip a bad item inside its own Mono, not on the whole stream",
   "body": S1,
   "try": {
    "title": "Skip the zero three ways",
    "minutes": 4,
    "steps": [
     "`SkipBadItemsDemo` runs the same four box counts through `onErrorResume` on the whole stream, `onErrorResume` inside a per-item `Mono`, and `onErrorContinue`. Predict the three lists.",
     "Run it.",
     "Now move the `onErrorContinue` line above the `map`, so it reads `boxCounts.onErrorContinue(...).map(i -> 8 / i)`. Predict what happens, then run it."
    ],
    "code": code("SkipBadItemsDemo"),
    "expect": "The whole-stream version prints `[8, 4]`: the 4 is lost. The per-item version prints `[8, 4, 2]` and logs the skipped zero. `onErrorContinue` also prints `[8, 4, 2]` in its original place. Moved above the `map`, it does nothing and `block()` throws `ArithmeticException`, because it only affects operators above it."
   },
   "refs": [
    {"title": "Flux Javadoc source: onErrorContinue (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}
   ]
  },
  {
   "h": "Retrying means subscribing again, so the call has to be lazy",
   "body": S2,
   "figure": {"svg": SVG, "caption": "Retry.backoff(3, 100 ms) with jitter off, against a mill that always fails: four attempts, waits that double, and an exhausted error at 700 ms that a fallback can catch."},
   "aside": ASIDE,
   "try": {
    "title": "Count the attempts",
    "minutes": 5,
    "steps": [
     "`RetryDemo` has four parts: a backoff that succeeds on the third call, `retry(2)` on a call that always fails, a backoff that runs out, and `retry(3)` on a Mono built from one eager call. For each part, write down the number of attempts, the times, and the final result.",
     "Run it and compare your numbers.",
     "In part 3, delete `.jitter(0)` and run the demo twice. Watch the times of attempts 2 to 4."
    ],
    "code": code("RetryDemo"),
    "expect": "Part 1 calls at about 0, 50 and 150 ms and prints `CONFIRMED` (a busy machine adds a little: one run here printed 0, 88 and 194 ms). Part 2 makes 3 attempts in the same millisecond or two and rethrows `mill down`. Part 3 calls at about 0, 50, 150 and 350 ms, then throws `RetryExhaustedException: Retries exhausted: 3/3` with `mill down` as the cause. Part 4 calls the mill once and fails with `mill busy` after 4 subscriptions: retry subscribed again to the same stored error. Without jitter the waits are 50, 100 and 200 ms; with the default jitter they change from run to run."
   },
   "refs": [
    {"title": "Retry and RetryBackoffSpec source (reactor-core 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java", "kind": "docs"}
   ]
  },
  {
   "h": "A timer on the wait turns silence into an error you can handle",
   "body": S3,
   "try": {
    "title": "Per attempt or in total",
    "minutes": 4,
    "steps": [
     "`TimeoutDemo` asks for the flour price from a service that takes 300 ms. It applies a 100 ms timeout, then the same with a fallback, then a 100 ms per-attempt timeout with retries inside a 400 ms budget. Predict each line, and how many attempts fit in the budget.",
     "Run it.",
     "In the last chain, delete the per-attempt `.timeout(Duration.ofMillis(100))` and keep the 400 ms budget. Predict the result and the number of attempts, then run it."
    ],
    "code": code("TimeoutDemo"),
    "expect": "The plain timeout prints `TimeoutException: Did not observe any item or terminal signal within 100ms` and the slow call is cancelled. The fallback version prints `yesterday's price 0.90`. The budget run makes 3 attempts (at about 0, 150 and 350 ms) and gives up a little after 400 ms (423 ms in one run here). Without the per-attempt timeout there is no error to retry, the single 300 ms call fits inside the 400 ms budget, and you get `fresh flour price 0.92` after 1 attempt."
   }
  }
 ],
 "compare": {
  "title": "One retry policy as a Reactor chain and as a suspend function",
  "java": {"title": "FlourOrders.java (Reactor)", "src": CJ},
  "kotlin": {"title": "FlourOrders.kt (coroutines)", "src": CK},
  "note": "Both versions make up to 4 attempts, give each one 500 ms, wait 100, 200 and 400 ms between them, let a refusal through and return `PENDING` at the end. (In the Kotlin version, `mill.order` is a suspend function, a function that can pause without holding its thread, and it returns the confirmation itself.) In Reactor the policy is data: operators you can reorder, and a `Retry` spec you can pass around and reuse, and the result is still a lazy `Mono` that does nothing until it is subscribed. In the coroutine version the policy is ordinary control flow: a loop, `try` and `catch`, `delay` and `withTimeout`. That is easier to read and to step through in a debugger, but you write the loop yourself, and you must not swallow `CancellationException` by catching `Exception` too broadly (`withTimeout` throws `TimeoutCancellationException`, which is one). Kotlin `Flow` has `retry` and `retryWhen` operators too, and the coroutines track covers them."
 },
 "worked": {
  "title": "Make a courier booking safe to retry",
  "steps": [
   {"say": "Every evening a job books a courier van for each cake delivery. The courier's booking service is a web service, and the second argument is a booking number that the courier uses to spot repeats. Someone added `retry()` after a bad week of timeouts. Read it and list what can go wrong before you read on.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Four problems. `retry()` with no number retries forever and at once, so one bad delivery stalls the whole job. It retries a refusal, such as an address the courier doesn't serve, as eagerly as a busy answer. Nothing limits how long one attempt may hang. And the booking number is a fresh random one each time `book` runs. The retries of this one Mono reuse it, but when the job crashes and runs again, `book` runs again with a new number, and the courier can't tell that the van is already booked. The number has to come from the delivery itself.", "code": "", "lang": ""},
   {"say": "Rebuild it in the order the lesson used: a lazy call, a per-attempt timeout, a filtered backoff, and a fallback for when the retries run out. `CourierErrors.isTemporary` returns true for timeouts, busy answers and dropped connections, and `toCheck` is a list a person goes through in the morning.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Test the slow path with virtual time, the fake clock from `StepVerifier`. The jitter is still on, so don't assert exact times: move the clock further than any possible wait, then check the counts. Four attempts, one booking number, one delivery put aside.",
    "code": W3, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A flour order with a timer, growing pauses and a fallback",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/FlourOrders.java", f"{lab}/main/{P}/Mill.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l05.*'",
  "steps": [
   "Run the tests once. All five fail. Read the Javadoc on `FlourOrders`, the class that places the bakery's flour orders with the mill: it lists five rules, and each test checks one of them.",
   "Look at `ScriptedMill` in `FlourOrdersTest`, a fake mill that answers from a script. It chooses its answer when `order()` is called, not when the Mono is subscribed. Decide what that means for your retry before you write any code.",
   "Write `place` as one chain: a lazy call to the mill, a 500 ms timeout per attempt, `retryWhen` with `Retry.backoff(3, Duration.ofMillis(100))` and no jitter, a filter that lets refusals through, and a fallback to `\"PENDING:\" + orderId` only when the retries are used up.",
   "Run the tests until all five pass. Then read the virtual-time steps in each test: `expectNoEvent(Duration.ofMillis(699))` followed by `thenAwait(Duration.ofMillis(1))` pins the result to exactly 700 ms."
  ],
  "hints": [
   "If \"succeeds on the third attempt\" fails and the mill was called once, you called `mill.order(orderId)` directly. Retry then subscribes again to the same failed Mono. Wrap the call in `Mono.defer`.",
   "If the hanging-attempt test ends in a `TimeoutException`, either your timeout sits below `retryWhen` (so it limits the whole call) or your filter doesn't accept `java.util.concurrent.TimeoutException`.",
   "If the refusal test receives `PENDING:flour-3`, your fallback catches every error. Use the predicate version: `onErrorResume(Exceptions::isRetryExhausted, e -> ...)`.",
   "`Retry.backoff(3, ...)` gives 3 retries, so 4 attempts. `jitter(0)` makes the waits exactly 100, 200 and 400 ms."
  ],
  "done_when": "All five tests in `FlourOrdersTest` pass."
 },
 "drill": {
  "title": "Write a retrying fetch from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Mono<Recipe> recipe(String name)` around `recipes.fetch(name)`, which returns a `Mono` but may do its work when it is called. Each attempt gets 1 second. Retry `IOException`s and timeouts up to 5 times, starting with a 50 ms wait. When the retries run out, the caller should get the last real error, not a `RetryExhaustedException`. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "Errors are terminal. `onErrorReturn`, `onErrorResume` and `onErrorMap` replace or translate what is left of the stream; they never resume the failed source.",
  "To skip a bad item, handle the error inside a per-item `Mono` in `concatMap` or `flatMap`. `onErrorContinue` acts upstream, depends on operator support, and its own Javadoc discourages it.",
  "`retry` subscribes again. Make the source lazy (`Mono.defer`), or the retry re-reads a stored answer and never calls the other side again.",
  "`retry(n)` makes n + 1 immediate attempts and passes on the original error. `Retry.backoff(3, 100ms)` makes 4 attempts with waits of 100, 200 and 400 ms, then fails with `RetryExhaustedException`. Filter what you retry, and keep jitter outside tests.",
  "`timeout` above `retryWhen` limits each attempt; below it, the whole operation.",
  "The limit: a timeout only means you stopped waiting. The other side may have done the work, so send the same order number on every attempt and treat \"out of retries\" as \"unknown\", not \"failed\"."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A tray of 100 rolls is shared among boxes, and the box counts arrive as `Flux.just(5, 10, 0, 20)`. What does `.map(i -> 100 / i).onErrorReturn(-1).collectList().block()` return?",
   "options": ["`[20, 10, -1, 5]`", "`[20, 10, -1]`", "`[20, 10, 5]`", "It throws `ArithmeticException`"],
   "answer": 1,
   "why": "The division by zero ends the source, so the 20 boxes are never handled. `onErrorReturn` replaces the rest of the stream with one value and completes. The first option assumes the stream carries on after the fallback, and the third is what per-item handling would give."},
  {"q": "The call for today's flour price sometimes hangs. Which chain retries a hanging attempt? (`ofMillis` and `ofSeconds` are `Duration` factories.)",
   "options": [
    "`Mono.defer(this::price).retryWhen(Retry.backoff(3, ofMillis(100))).timeout(ofSeconds(2))`",
    "`Mono.defer(this::price).timeout(ofMillis(500)).retryWhen(Retry.backoff(3, ofMillis(100)))`",
    "`Mono.defer(this::price).retryWhen(Retry.backoff(3, ofMillis(100)))`",
    "`Mono.defer(this::price).retry(3)`"
   ],
   "answer": 1,
   "why": "Only a timeout above `retryWhen` turns each hanging attempt into an error that the retry can see. In the first option the timeout is a total budget: the first attempt hangs for 2 seconds and is never retried. The last two have no timeout, so a hang produces no error at all and nothing is retried."},
  {"q": "A nightly job must log and skip order lines whose quantity fails to parse, and keep going. Which is the right shape?",
   "options": [
    "`lines.map(this::parse).onErrorResume(e -> Mono.empty())`",
    "`lines.map(this::parse).onErrorContinue((e, l) -> log(l))`",
    "`lines.concatMap(l -> Mono.fromCallable(() -> parse(l)).onErrorResume(e -> logAndSkip(l, e)))`",
    "`lines.map(this::parse).retry()`"
   ],
   "answer": 2,
   "why": "Handling the error inside each line's own `Mono` ends only that inner Mono, so the outer stream keeps going. The first option ends the whole stream at the first bad line. `onErrorContinue` happens to work here, but it acts on operators above it and can leak into library code; its Javadoc recommends the inner-publisher shape. `retry()` subscribes to the lines again forever and hits the same bad line every time."},
  {"q": "`mill.order(id)` always fails with `MillBusyException`. What does `Mono.defer(() -> mill.order(id)).retry(2).block()` do?",
   "options": [
    "Calls the mill 2 times, then throws `RetryExhaustedException`",
    "Calls the mill 3 times, 100 ms apart, then throws `MillBusyException`",
    "Calls the mill 3 times with no pause, then throws `MillBusyException`",
    "Calls the mill once, because `retry` re-uses the first result"
   ],
   "answer": 2,
   "why": "`retry(n)` means n retries, so 3 attempts, all back to back, and it rethrows the original error. Pauses and `RetryExhaustedException` come from `retryWhen(Retry.backoff(...))`. Because of `Mono.defer`, each attempt really calls the mill; without it, a client that does its work when called would be called once."},
  {"q": "From \"Mono and Flux: nothing happens until you subscribe\": a teammate writes `Mono.just(mill.orderBlocking(id)).retry(3)`. The call fails on the first try. How many requests reach the mill?",
   "options": ["One, and the exception is thrown before `retry` even exists", "Four", "Three", "None, because nothing is subscribed"],
   "answer": 0,
   "why": "`Mono.just` takes a value, so Java evaluates `orderBlocking(id)` first, at assembly time. It throws right there, out of the line that builds the chain, and `retry(3)` is never even created. Even if it had returned a value, `Mono.just` would replay that same value to every subscriber. Use `Mono.fromCallable` or `Mono.defer` so that each subscription makes the call.",
   "from": "rx-02"}
 ],
 "flashcards": [
  {"front": "`Flux.just(1, 2, 0, 4).map(i -> 8 / i).onErrorReturn(-1)`: what is emitted?", "back": "`8, 4, -1`, then complete. The error ended the source, so the 4 is never handled."},
  {"front": "How do you skip one bad item in a Flux without ending the stream?", "back": "Handle each item in its own `Mono` inside `concatMap` or `flatMap`, and put `onErrorResume` on that inner Mono."},
  {"front": "Why is `onErrorContinue` discouraged?", "back": "It acts on operators above it (not below), only works with operators that support it, and can leak into library code. Its own Javadoc says so."},
  {"front": "`retry(2)` on a source that always fails: how many attempts, and which error?", "back": "3 attempts with no pause, then the original error."},
  {"front": "`Retry.backoff(3, 100ms).jitter(0)` on a source that always fails: attempts, timing, error?", "back": "4 attempts at 0, 100, 300 and 700 ms, then `RetryExhaustedException` (\"Retries exhausted: 3/3\") with the last error as its cause."},
  {"front": "Why can `retry` fail to call the other side again?", "back": "It subscribes again. If the Mono was built from a call made at assembly (`Mono.just(call())`, or a client that calls eagerly), it replays the stored answer. Wrap the call in `Mono.defer`."},
  {"front": "`timeout` above vs below `retryWhen`?", "back": "Above: each attempt gets the time, and a timeout is retried. Below: one budget for the whole operation, waits included."}
 ],
 "terms": [
  {"term": "Terminal signal", "plain": "`onError` or `onComplete`: after one of them the stream is over and nothing else arrives."},
  {"term": "Fallback", "plain": "What a stream switches to when an error arrives: a value, another publisher, or a different error."},
  {"term": "Retry", "plain": "Subscribing to the source again after an error, so a cold source does its work again from the start."},
  {"term": "Exponential backoff", "plain": "Waiting longer before each retry, usually twice as long: 100 ms, 200 ms, 400 ms."},
  {"term": "Jitter", "plain": "A random change to each backoff wait, so many clients that failed together don't retry at the same instant."},
  {"term": "RetryExhaustedException", "plain": "The error `Retry.backoff` and `Retry.max` signal when the retries run out; its cause is the last real error."},
  {"term": "Temporary error", "plain": "A failure that a later attempt may not repeat: a timeout, a busy answer, a dropped connection."}
 ],
 "explain_back": {
  "prompt": "A teammate added `.retry(3)` to the call that orders flour from the mill and says \"now it retries three times, so a busy mill can't stop the order\". Explain in your own words what that line really does, and what you would write instead.",
  "answer": "`retry(3)` subscribes again up to three times, so there are four attempts, one right after the other with no pause, and then the original error comes out. It retries every error, including a refusal that will never change and bugs in our own code. If the client made its call when the method was invoked, the retries just re-read the stored failure and the mill is called once. I would make the call lazy with `Mono.defer`, give each attempt a timeout, use `retryWhen(Retry.backoff(3, Duration.ofMillis(100)))` with a filter for timeouts and busy errors, keep the jitter on, and decide what happens when the retries run out: for an order, mark it pending and check with the mill later, with the same order number on every attempt so the mill can spot a repeat."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Temporary errors in a long stream.** `Retry.max(2).transientErrors(true)` (also on `backoff`) counts retries in a row and resets the count after a successful `onNext`. That suits long-lived streams, such as a feed of web orders, that fail now and then: each burst of failures gets its own budget instead of using up a lifetime total. The reference guide's example fails twice, emits, fails twice more and then succeeds. `Retry.max(2).transientErrors(true)` gets through, and plain `Retry.max(2)` runs out in the second burst.\n\n**Other specs.** `Retry.fixedDelay(5, Duration.ofSeconds(1))` waits the same time between retries. `Retry.indefinitely()` never gives up, so pair it with a filter. Every spec has `doBeforeRetry(signal -> ...)` for logging the attempt number, and `onRetryExhaustedThrow(...)` to choose the final error.\n\n**The companion.** `retryWhen` takes a function from a `Flux<RetrySignal>` (one signal per error) to a companion publisher. Each item the companion emits triggers one retry; if it completes, the sequence completes without error; if it errors, that error goes downstream. `Retry.backoff` is a ready-made companion built on `Mono.delay`, which is why its waits run on `Schedulers.parallel()` and why virtual time controls them.\n\n**Repeat is the other loop.** `repeat` subscribes again after a *successful* completion, which suits polling. Reactor 3.8 added `RepeatSpec` for `repeatWhen`, the counterpart of `Retry` for repeats.\n\n**Fatal errors.** Reactor throws some errors straight up the stack instead of turning them into `onError`, such as `OutOfMemoryError` and `StackOverflowError` (see `Exceptions.throwIfFatal`). No error operator will catch those, and you shouldn't want one to."
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
