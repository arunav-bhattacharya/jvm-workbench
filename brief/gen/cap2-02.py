import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l02"
K = "kotlin/workbench/quotes/l02"
read = lambda p: (ROOT / p).read_text()


def pair_kj(kotlin, java):
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def demo(name):
    """A Try-it code object for a Kotlin demo with its Java twin (NameJava.java)."""
    return {
        "lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
        "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l02.{name}Kt",
        "file": f"{lab}/demo/{K}/{name}.kt",
        "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{J}/{name}Java.java"),
                "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l02.{name}Java",
                "file": f"{lab}/demo/{J}/{name}Java.java"},
    }


# ---- the figure: three calls, one deadline ----
X0, PX = 110, 1.2          # x of 0 ms, pixels per ms
x = lambda ms: int(X0 + ms * PX)
ticks = "".join(
    f'<line class="ln" x1="{x(t)}" y1="44" x2="{x(t)}" y2="50"/><text class="t-s t-m" x="{x(t)}" y="36" text-anchor="middle">{t}</text>'
    for t in (0, 100, 200, 300, 400))
FIG = (
    '<svg viewBox="0 0 680 262" role="img" aria-label="Timeline of one quote request: Northbank answers at 120 ms, '
    'Fjord at 200 ms, Eastgate would answer at 300 ms but is cancelled at the 250 ms deadline, so the request answers '
    'at 250 ms with the best price that arrived.">'
    '<line class="ln" x1="110" y1="47" x2="630" y2="47" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="652" y="51" text-anchor="middle">ms</text>'
    + ticks +
    '<text class="t" x="56" y="89" text-anchor="middle">northbank</text>'
    f'<rect class="box-ok" x="{x(0)}" y="68" width="{x(120) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(120)) // 2}" y="89" text-anchor="middle">1.0845</text>'
    '<text class="t" x="56" y="139" text-anchor="middle">fjord</text>'
    f'<rect class="box-ok" x="{x(0)}" y="118" width="{x(200) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(200)) // 2}" y="139" text-anchor="middle">1.0843, the best in time</text>'
    '<text class="t" x="56" y="189" text-anchor="middle">eastgate</text>'
    f'<rect class="box-bad" x="{x(0)}" y="168" width="{x(250) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(250)) // 2}" y="189" text-anchor="middle">cancelled at the deadline</text>'
    f'<rect class="box-dim" x="{x(250)}" y="168" width="{x(300) - x(250)}" height="32" rx="8"/>'
    f'<text class="t-s t-m" x="{(x(300) + 640) // 2}" y="189" text-anchor="middle">would be 300</text>'
    f'<line class="ln-bad" x1="{x(250)}" y1="58" x2="{x(250)}" y2="214"/>'
    f'<text class="t-s t-bad" x="{x(250)}" y="230" text-anchor="middle">deadline: 250 ms</text>'
    '<text class="t-s t-a" x="340" y="252" text-anchor="middle">the request answers at 250 ms with fjord 1.0843</text>'
    '</svg>'
)

K_FAN = """suspend fun allPrices(symbol: String): List<Quote> = coroutineScope {
    providers.map { p -> async { p.quote(symbol) } }   // 1. start all three
        .awaitAll()                                     // 2. then wait: as long as the slowest
}"""
J_FAN = """// Java equivalent with Reactor: Mono.zip subscribes to all three sources at once
Mono<List<Quote>> allPrices(String symbol) {
    return Mono.zip(northbank.quote(symbol), eastgate.quote(symbol), fjord.quote(symbol))
            .map(t -> List.of(t.getT1(), t.getT2(), t.getT3()));
}"""
K_DEADLINE = """providers.map { p ->
    async { withTimeoutOrNull(deadline) { p.quote(symbol) } }   // null if p misses the deadline
}"""
J_DEADLINE = """// Java equivalent with Reactor: a timeout on each source, turned into "no answer"
Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE)
            .map(Optional::of)
            .onErrorResume(TimeoutException.class, e -> Mono.just(Optional.empty()));
}"""
K_AWAIT = """private suspend fun Deferred<Quote?>.awaitOrNull(): Quote? =
    try {
        await()
    } catch (e: CancellationException) {
        currentCoroutineContext().ensureActive()   // we were cancelled ourselves: this rethrows
        null                                        // only the provider's call ended that way
    } catch (e: Exception) {
        null                                        // the provider failed: no answer from it
    }"""
J_AWAIT = """// Java equivalent with Reactor: each source handles its own error, so the zip never sees one
Mono<Optional<Quote>> alone(Mono<Quote> call) {
    return call.map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))   // a failure stays with its provider
            .defaultIfEmpty(Optional.empty());                 // and so does an empty answer
}"""
K_TAIL = """val best = answers.minByOrNull { it.price }
if (best != null) {
    cache.remember(best)                       // only live answers refresh the cache
    return best
}
return cache.lastGood(symbol)?.asStale()       // stale beats nothing
    ?: throw NoQuoteException(symbol)          // the handler writes "7 ERR no quote for EURUSD\""""
J_TAIL = """// Java equivalent with Reactor: an empty Optional switches to the cache
.flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(symbol)))
.doOnNext(q -> { if (!q.stale()) cache.remember(q); })   // only live answers refresh the cache"""
K_SERVICE = """class QuoteService(context: CoroutineContext, private val best: BestQuote) : QuoteSource, AutoCloseable {
    private val scope = CoroutineScope(context + SupervisorJob())   // owned; failures stay per request

    override fun quote(symbol: String): CompletableFuture<Quote> =
        scope.future { best.quote(symbol) }                          // returns at once; cancel() reaches it

    override fun close() = scope.cancel()
}"""
J_SERVICE = """// Java equivalent with Reactor: toFuture() subscribes, and cancelling the future cancels the subscription
final class ReactorQuoteSource implements QuoteSource {
    @Override
    public CompletableFuture<Quote> quote(String symbol) {
        return best(symbol).toFuture();                              // returns at once; cancel() reaches the zip
    }
}"""

S1 = f"""Lesson 1 left the server with a `QuoteSource` that must return a future at once. This lesson writes the source. For each request it asks Northbank, Eastgate and Fjord for a price, keeps the lowest, and answers within a deadline whatever the providers do. Lowest is what a customer buying the currency wants; a real dealing desk compares bid and ask, but the fan-out is the same either way.

The shape is the concurrent decomposition from "Builders: launch, async, runBlocking, coroutineScope": start all three calls, then wait for them. With latencies of 120, 300 and 200 ms, one call after another takes 620 ms. Started together they take 300 ms, the time of the slowest:

{pair_kj(K_FAN, J_FAN)}

The deadline is the next decision. A price that arrives after 2 seconds is useless to a checkout page with a 300 ms budget. Give each call the deadline, start them together, and the whole request ends by the deadline:

{pair_kj(K_DEADLINE, J_DEADLINE)}

`withTimeoutOrNull` is cancellation with a clock ("Cancellation and timeouts"). At the deadline it cancels the late call, which stops at its next suspension point, and returns `null` for it.

Why one deadline per call, and not one `withTimeout` around the whole fan-out? Both bound the request. Around the whole fan-out, the timeout cancels everything and throws away the answers that did arrive: Northbank answered at 120 ms and Fjord at 200 ms, and you would still have nothing to send. Per call, only the late provider drops out, as the figure shows. Because all the calls start together, a per-call deadline is also a deadline for the request."""

S2 = f"""The first draft of `BestQuote`, the starting code of this lesson's lab, uses `coroutineScope` and `withTimeout`. Both are wrong for a quote, for reasons from earlier lessons.

`coroutineScope` treats its children as one unit of work. When Northbank throws `IOException` at 50 ms, the scope cancels Eastgate and Fjord and rethrows ("Exceptions: launch vs async, SupervisorJob, handlers"). That is right for a payment details page that needs all three answers. A quote needs any one of them. `supervisorScope` lets each child fail alone: a failed `async` keeps its exception in its `Deferred`, and `await` hands it to you, where you turn it into "no answer".

`withTimeout` signals a late call with `TimeoutCancellationException`, and that is a `CancellationException`. The usual rule, rethrow `CancellationException` so a cancel is never swallowed, now bites: one provider's timeout looks like a cancel of the whole request, and ends it. `withTimeoutOrNull` turns your own deadline into a plain `null`. But a provider can still throw `TimeoutCancellationException` from deep inside its own HTTP client, and this section's demo has one that does. So be precise and rethrow only when *your* coroutine was cancelled. `ensureActive()` makes exactly that check:

{pair_kj(K_AWAIT, J_AWAIT)}

If the request itself was cancelled (the client hung up), `ensureActive()` throws and the cancel carries on up. If it returns, the cancellation belonged to the provider's call, and that provider simply has no answer. The demo runs the same three calls in three scopes:

| Scope | Outcome |
|---|---|
| `coroutineScope`, `awaitAll` | fails at 50 ms: `IOException: northbank 503` |
| `supervisorScope`, rethrow every cancel | fails at 100 ms: `TimeoutCancellationException` |
| `supervisorScope`, rethrow only our cancel | `eastgate 1.0841` at 300 ms |

Reactor has no such trap, because cancellation there is not an error signal: you isolate each source with `onErrorResume` before `Mono.zip`. The compare block below puts the two whole fan-outs side by side."""

S3 = f"""Sometimes all three providers miss the deadline: a network partition, or the minutes after a market opens. The service then has three options. It can wait longer, fail the request, or serve the last price it saw. Waiting longer breaks the deadline, which is the one promise the service makes. Failing is honest, and useless to a checkout page that only needs an indicative price. So `BestQuote` keeps the last live quote per symbol and serves it marked stale, `7 STALE EURUSD 1.0841 eastgate`, and the client decides whether stale is good enough.

{pair_kj(K_TAIL, J_TAIL)}

Two rules keep the cache honest. Only live answers go into it: if a stale answer could refresh the cache, one old price could be served forever. And with nothing cached, the request fails with `NoQuoteException`, which lesson 1's handler turns into `7 ERR no quote for EURUSD`. A production cache would also have an age limit, so that a price from three seconds ago is served and one from last night is not.

Check yourself: after an outage the providers recover, and on the next request Eastgate answers 1.0839 and Fjord 1.0842. What does the client get, and what does the cache hold for EURUSD afterwards? (`OK EURUSD 1.0839 eastgate`, and the cache now holds that live quote in place of the old one.)"""

S4 = f"""Lesson 1's handler calls `quote` on the event loop, and it cancels the future when the client hangs up. `QuoteService` connects that future to a coroutine:

{pair_kj(K_SERVICE, J_SERVICE)}

`scope.future {{ }}` starts a coroutine in the service's scope and returns a `CompletableFuture` at once, so the event loop never waits. The link works in both directions ("Coroutines meet Java: futures, Reactor, virtual threads"): when the coroutine finishes, the future completes, and when someone cancels the future, the coroutine is cancelled. The second direction is what binds a request to its connection. The client hangs up, `channelInactive` cancels the future, the `future` coroutine is cancelled, and the cancel travels down the job tree to the `supervisorScope` and its three provider calls ("Structured concurrency: scopes, jobs and the tree"). Each request is a small tree whose root is that coroutine, and the channel's lifetime bounds it.

Why not give each channel its own `CoroutineScope` and cancel it in `channelInactive`? That works too, and it is the shape to pick when the handler itself is written in Kotlin. Here the Java handler from lesson 1 already keeps every pending future and cancels them on close, so a scope per channel would track the same requests twice. With `future {{ }}`, the Java side holds the handle, the Kotlin side holds the tree, and neither needs to know how the other works.

Two choices in the scope matter. The scope uses `SupervisorJob`. With a plain `Job`, one request that fails with `NoQuoteException` would cancel its parent, and with it every other request in flight; every later `future` would then come back cancelled at once. And the dispatcher is passed in. Production uses `Dispatchers.Default`. The tests pass a `StandardTestDispatcher`, so every `delay` and every deadline runs on virtual time, and a test that checks a 300 ms deadline takes a few milliseconds.

The Java twin of this section's demo shows what you'd lose with a plain `CompletableFuture` built from three `supplyAsync` calls: cancelling the outer future cancels 0 of the 3 calls, and all three answer later with nobody listening."""

# ---- worked example: test the deadline on virtual time ----
W1K = """class FakeProvider(
    override val name: String,
    private val price: String,
    private val latency: Duration,
    private val cancelled: MutableList<String>,
) : Provider {
    override suspend fun quote(symbol: String): Quote {
        try {
            delay(latency)                     // 1. virtual time under runTest
        } catch (e: CancellationException) {
            cancelled += name                  // 2. record who was cancelled
            throw e
        }
        return Quote.live(symbol, price, name)
    }
}"""
W1J = """// Java equivalent with Reactor: Mono.delay runs on Schedulers.parallel(), which virtual time replaces
Mono<Quote> fake(String name, String price, Duration latency, List<String> cancelled) {
    return Mono.delay(latency)                                        // 1. virtual time under StepVerifier
            .map(x -> Quote.live("EURUSD", price, name))
            .doOnCancel(() -> cancelled.add(name));                   // 2. record who was cancelled
}"""
W2K = """@Test
fun `a provider slower than the deadline is cancelled at the deadline`() = runTest {
    val best = BestQuote(listOf(northbank(120), eastgate(1_000), fjord(200)), deadline = 300.milliseconds)
    val quote = best.quote("EURUSD")
    assertThat(quote.provider).isEqualTo("fjord")
    assertThat(currentTime).isEqualTo(300)            // 3. exact, and the test takes milliseconds
    assertThat(cancelled).containsExactly("eastgate")
}"""
W2J = """// Java equivalent with Reactor: StepVerifier on virtual time
StepVerifier.withVirtualTime(() -> best("EURUSD"))           // build the Mono inside the supplier
        .expectSubscription()
        .expectNoEvent(Duration.ofMillis(299))
        .thenAwait(Duration.ofMillis(1))                      // 3. exactly at the deadline
        .expectNextMatches(q -> q.provider().equals("fjord"))
        .verifyComplete();
assertThat(cancelled).containsExactly("eastgate");"""
W3K = """@Test
fun `cancelling the future cancels all three provider calls`() = runTest {
    val service = QuoteService(StandardTestDispatcher(testScheduler), slowBest)   // 4. inject the test clock
    val future = service.quote("EURUSD")
    runCurrent()                                     // the three calls have started
    future.cancel(true)                              // what channelInactive does
    runCurrent()
    assertThat(cancelled).containsExactlyInAnyOrder("northbank", "eastgate", "fjord")
    assertThat(service.inFlight).isEqualTo(0)
}"""
W3J = """// Java equivalent with Reactor: cancelling toFuture() cancels the subscription at once
CompletableFuture<Quote> future = source.quote("EURUSD");
future.cancel(true);                                 // what channelInactive does
assertThat(cancelled).containsExactlyInAnyOrder("northbank", "eastgate", "fjord");"""

COMPARE_J = """// Reactor: errors, timeouts and empties become values at each source, then Mono.zip
Mono<Quote> best(String symbol) {
    return Mono.zip(inTime(northbank.quote(symbol)), inTime(eastgate.quote(symbol)), inTime(fjord.quote(symbol)))
            .map(t -> Stream.of(t.getT1(), t.getT2(), t.getT3())
                    .flatMap(Optional::stream)
                    .min(Comparator.comparing(Quote::price)))
            .flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(symbol)))
            .doOnNext(q -> { if (!q.stale()) cache.remember(q); });
}

Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE)
            .map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))   // a failure or a timeout: no answer
            .defaultIfEmpty(Optional.empty());                 // an empty source would empty the zip
}

Mono<Quote> fromCache(String symbol) {
    Quote last = cache.lastGood(symbol);
    return last != null ? Mono.just(last.asStale()) : Mono.error(new NoQuoteException(symbol));
}"""
COMPARE_K = read(f"{lab}/solution/{K}/BestQuote.kt").split("class BestQuote(", 1)[1]
COMPARE_K = "class BestQuote(" + COMPARE_K.rstrip() + "\n"

DRILL_K = """suspend fun quote(symbol: String): Quote {
    val answers = supervisorScope {
        providers
            .map { p -> async { withTimeoutOrNull(deadline) { p.quote(symbol) } } }
            .map { d ->
                try { d.await() }
                catch (e: CancellationException) { currentCoroutineContext().ensureActive(); null }
                catch (e: Exception) { null }
            }
    }.filterNotNull()
    val best = answers.minByOrNull { it.price }
    if (best != null) return best.also { cache.remember(it) }
    return cache.lastGood(symbol)?.asStale() ?: throw NoQuoteException(symbol)
}"""
DRILL_J = """// Java equivalent with Reactor
Mono<Quote> best(String symbol) {
    return Mono.zip(inTime(northbank.quote(symbol)), inTime(eastgate.quote(symbol)), inTime(fjord.quote(symbol)))
            .map(t -> Stream.of(t.getT1(), t.getT2(), t.getT3()).flatMap(Optional::stream)
                    .min(Comparator.comparing(Quote::price)))
            .flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(symbol)))
            .doOnNext(q -> { if (!q.stale()) cache.remember(q); });
}

Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE).map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))
            .defaultIfEmpty(Optional.empty());
}"""

L = {
 "id": "cap2-02",
 "title": "Fan out with coroutines, inside a deadline",
 "minutes": 38,
 "goal": "By the end you can fan one quote request out to three providers with `async` inside `supervisorScope`, give every call the same deadline with `withTimeoutOrNull`, fall back to the last good quote marked stale, and bind each request's coroutine to its connection with `scope.future { }`, so that a client who hangs up cancels the provider calls.",
 "warmup": {
  "q": "Inside `coroutineScope { }`, three `async` calls ask three providers for a price. One provider throws `IOException` after 50 ms; the other two would answer at 120 and 300 ms. What does the quote request get?",
  "options": [
   "The better of the two prices that came back, after 300 ms",
   "The `IOException` after about 50 ms, and the other two calls are cancelled",
   "The `IOException` after 300 ms, once the other two calls have finished",
   "Two prices and a `null` for the provider that failed"
  ],
  "answer": 1,
  "why": "A failed child cancels its parent at once, and a plain scope then cancels the other children and rethrows. So the request fails at 50 ms with the `IOException`, and the two calls that would have answered are cancelled. That is right when you need every answer and wrong when any one will do. The fix for a quote is `supervisorScope`, this lesson's first change."
 },
 "sections": [
  {
   "h": "One request, three providers, one deadline",
   "body": S1,
   "figure": {"svg": FIG, "caption": "All three calls start together and each gets the same deadline. The late call is cancelled at 250 ms, and the answers that arrived still count."},
   "try": {
    "title": "Three ways to ask three providers",
    "minutes": 4,
    "steps": [
     "Open `FanOutDemo.kt`. It runs on virtual time with `runTest`, so the clock is exact. The Java twin, `FanOutDemoJava.java`, does the same with Reactor in real time.",
     "Predict the three times and the three answer lists: one after another, all at once, and all at once with a 250 ms deadline.",
     "Run it. Then set `deadline` to 100 and predict the last line again."
    ],
    "code": demo("FanOutDemo"),
    "expect": "620 ms in turn, 300 ms all at once, 250 ms with the deadline, where Eastgate (300 ms) comes back as `null` and the other two still count. With a 100 ms deadline the last line takes 100 ms and all three answers are `null`: nobody was fast enough, which is the case section 3 handles. The Java twin prints similar times in real time (more on a busy machine), with `Optional.empty` where Kotlin prints `null`."
   },
   "refs": [
    {"title": "withTimeoutOrNull (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout-or-null.html", "kind": "docs"}
   ]
  },
  {
   "h": "Let one provider fail alone, and tell your cancel from theirs",
   "body": S2,
   "try": {
    "title": "One failure, one timeout, three scopes",
    "minutes": 4,
    "steps": [
     "Open `FailAloneDemo.kt`. Northbank fails at 50 ms, Fjord's own client times out at 100 ms, and Eastgate answers at 300 ms.",
     "Predict the outcome and the virtual time of each of the three attempts.",
     "Run it. Then, in `callAll()`, move `async { fjord() }` to the end of the list and predict the second line again."
    ],
    "code": demo("FailAloneDemo"),
    "expect": "`coroutineScope` fails at 50 ms with the `IOException`. The naive supervisor fails at 100 ms with `TimeoutCancellationException`: it rethrew Fjord's timeout as if it were its own cancel. The careful one answers `[null, null, eastgate 1.0841]` at 300 ms. With Fjord last, the naive version waits for Eastgate first, then rethrows Fjord's exception: it fails at 300 ms instead of 100, and still throws away Eastgate's price. The Java twin shows the Reactor side: the raw `Mono.zip` fails on Northbank's error, and with `onErrorResume` on each call it answers with Eastgate at about 300 ms."
   },
   "refs": [
    {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html", "kind": "read"},
    {"title": "ensureActive (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html", "kind": "docs"}
   ]
  },
  {
   "h": "When nobody answers, serve the last good quote and say it is stale",
   "body": S3
  },
  {
   "h": "Bind each request to its connection with scope.future",
   "body": S4,
   "try": {
    "title": "Hang up on a request",
    "minutes": 3,
    "steps": [
     "Open `HangUpDemo.kt`. A request coroutine started with `scope.future { }` waits for three provider calls of 300, 400 and 500 ms. After 120 ms the demo cancels the future, as `channelInactive` would.",
     "Predict which calls print `answered` and which print `cancelled`, and how many coroutines are left in the scope.",
     "Run it, then run the Java twin, which builds the request from three `supplyAsync` calls."
    ],
    "code": demo("HangUpDemo"),
    "expect": "All three calls print `cancelled` a few milliseconds after the hang-up, and the scope has 0 coroutines left: the cancel went from the future to the coroutine and down to its children. The Java twin reports `calls cancelled: 0 of 3`, and the three providers answer at about 300, 400 and 500 ms with nobody listening. `CompletableFuture.cancel` completed the outer future and stopped nothing."
   },
   "refs": [
    {"title": "future (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A dealer on an FX desk needs a price for a customer. She calls three banks at once on three phones and starts a kitchen timer. If one bank's line drops, she keeps listening to the other two; that is `supervisorScope`, where `coroutineScope` would hang up all three phones. When the timer rings she hangs up on whoever is still talking and quotes the best price she has. If nobody answered, she reads yesterday's price off the board with an \"indicative\" sticker on it. And if the customer walks away from the desk, she hangs up all three phones at once, which is the cancel travelling down the job tree. The analogy breaks at hanging up: a dealer's phone goes dead the instant she puts it down. A coroutine stops only at its next suspension point, so a provider client stuck in blocking IO keeps going until its call returns (\"Cancellation and timeouts\").",
 "in_your_world": "A checkout service fans out all the time: FX rates from several liquidity providers, a fraud score, merchant fees, a BIN lookup. Decide per call which scope it needs. Where any answer will do, as with several FX providers or several fraud vendors, use `supervisorScope` and a deadline per call. Where the response needs every answer, as with an account, its limits and its risk flags, use `coroutineScope` so that one failure cancels the rest at once. A Quarkus REST endpoint written as a Kotlin `suspend fun` runs on the event loop (\"Quarkus on Vert.x: IO threads, workers and virtual threads\"), so the fan-out inside it must suspend, never block. And keep the stale-price rule in mind for anything that moves money: an indicative price may be stale, but a price you book a payment at must be live and confirmed.",
 "mistake": "The most common mistake is building a best-of fan-out with `coroutineScope` and `awaitAll()`, then trying to rescue it with `runCatching { deferred.await() }` when one bad provider starts failing every quote. It doesn't work: in a plain scope, a failed child cancels its parent and siblings the moment it fails, long before your `runCatching` runs (\"Exceptions: launch vs async, SupervisorJob, handlers\"). The second version of the same mistake catches correctly but rethrows every `CancellationException`, and one provider's internal timeout then ends the request. Use `supervisorScope`, give each call `withTimeoutOrNull`, and in the catch rethrow only after `currentCoroutineContext().ensureActive()` says the cancel was yours.",
 "compare": {
  "title": "The fan-out with Reactor's Mono.zip and with coroutines",
  "java": {"title": "BestQuoteReactor.java", "src": COMPARE_J},
  "kotlin": {"title": "BestQuote.kt", "src": COMPARE_K},
  "note": "Both start the three calls together, give each its own deadline, turn a failure into \"no answer\", keep the lowest price and fall back to the cache. In Reactor every outcome becomes a value at the source: a timeout is an error signal you resume from, and an empty source is a third outcome you must name with `defaultIfEmpty`, or `Mono.zip` completes empty (\"Combining streams: zip, merge, concat, combineLatest\"). Nothing runs until something subscribes, and cancelling the subscription cancels the three calls. In Kotlin the same policy is ordinary control flow: a scope, `try`/`catch`, `minByOrNull`. The scope guarantees that when `quote` returns, every call is either done or cancelled. The price of that directness is the `CancellationException` rule, which only coroutines have: a timeout is a cancel, so you must tell your own cancel from a provider's."
 },
 "worked": {
  "title": "Test the deadline and the hang-up on virtual time",
  "steps": [
   {"say": "Make the providers controllable on the test clock. `delay` inside `runTest` uses virtual time, so a fake that delays 1,000 ms costs nothing, and recording cancellations in the `catch` tells the test exactly who was stopped.",
    "code": W1K, "lang": "kotlin", "alt_code": W1J, "alt_lang": "java"},
   {"say": "Test the deadline. `currentTime` is the virtual clock, so the assertion can be exact: 300, not \"under 400\". A real-time version would take 300 ms per test and could fail on a busy build machine.",
    "code": W2K, "lang": "kotlin", "alt_code": W2J, "alt_lang": "java"},
   {"say": "Test the hang-up through `QuoteService`. Pass `StandardTestDispatcher(testScheduler)` as its context: the service's own scope then runs on the test clock too. `runCurrent()` runs what is due now, without moving the clock.",
    "code": W3K, "lang": "kotlin", "alt_code": W3J, "alt_lang": "java"},
   {"say": "Know where virtual time stops. A `delay` inside `withContext(Dispatchers.Default)` escapes the test scheduler and takes real time (\"Shared state and testing coroutines\"), which is why the service takes its dispatcher as a parameter. The two end-to-end tests in this lab use `Dispatchers.Default` and a real Netty server, so they assert only with latches: 6 provider calls started, 6 cancelled after the hang-up. Self-check: what would `currentTime` read in a test that built `QuoteService(Dispatchers.Default, ...)` inside `runTest`? (0: the coroutines ran on real threads, and the virtual clock never moved.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fan out to three providers, and cancel on hang-up",
  "minutes": 15,
  "files": [
   f"{lab}/main/{K}/BestQuote.kt",
   f"{lab}/main/{K}/QuoteService.kt",
   f"{lab}/main/{K}/Provider.kt",
   f"{lab}/main/{K}/QuoteCache.kt",
   f"{lab}/main/{J}/QuoteSource.java"
  ],
  "run": "./gradlew :quotes:test --tests 'workbench.quotes.l02.*'",
  "steps": [
   "Run the tests. Ten of eleven fail. The Java files in `l02` are lesson 1's solution, carried over; the tests' providers are in `src/test/.../l02/FakeProvider.kt`.",
   "Fix `BestQuote` along points 1 to 3 of its KDoc: `supervisorScope`, `withTimeoutOrNull` inside each `async`, and an await that turns failures into `null` and rethrows only your own cancel.",
   "Add point 4: remember the best live quote, else serve `cache.lastGood(symbol)?.asStale()`, else throw `NoQuoteException(symbol)`. The six `BestQuote` tests should pass.",
   "Write `QuoteService`: a private scope from `context + SupervisorJob()`, `quote` with `scope.future { }`, `inFlight` from the scope's job, and `close`.",
   "Run the tests until all eleven pass, including the two over TCP. Run them once more."
  ],
  "hints": [
   "If the deadline test fails with `TimeoutCancellationException: Timed out after 300ms of _virtual_ ... time`, you still use `withTimeout`, or you rethrow every `CancellationException`.",
   "`supervisorScope` returns what its block returns. Map the deferreds to `awaitOrNull()` inside the block, and `filterNotNull()` outside it.",
   "`scope.future { }` is in `kotlinx.coroutines.future`. It starts the coroutine on the scope's dispatcher and returns the future at once.",
   "`inFlight` is `scope.coroutineContext.job.children.count()`; `job` is an extension property from `kotlinx.coroutines`."
  ],
  "done_when": "All eleven tests in `FanOutTest` pass, twice in a row."
 },
 "drill": {
  "title": "Write the best-of fan-out from memory",
  "minutes": 5,
  "prompt": "Close the lab. Write `BestQuote.quote(symbol)` from memory: all providers at once, the same deadline for each, a failed or late provider counts as no answer, your own cancel still propagates, the lowest price wins, and with no answer you serve the cached quote as stale or throw `NoQuoteException`. Which line would break the request when a provider's own client times out?",
  "answer": {"lang": "kotlin", "src": DRILL_K, "alt": {"lang": "java", "src": DRILL_J}}
 },
 "recap": [
  "Fan out with `async` inside a scope: three providers at 120, 300 and 200 ms answer in 300 ms instead of 620.",
  "Give each call the deadline with `withTimeoutOrNull`. A late provider drops out as `null` and the others still count; one timeout around the whole fan-out throws away answers that already arrived.",
  "`supervisorScope` lets each provider fail alone. `coroutineScope` cancels the other calls at the first failure, which is right only when you need every answer.",
  "A provider's own timeout is a `CancellationException` too. In the catch, `currentCoroutineContext().ensureActive()` rethrows only if your coroutine was cancelled.",
  "With no answer, serve the last live quote marked `STALE`, or fail with `NoQuoteException`. Only live answers refresh the cache.",
  "`scope.future { }` gives the Java handler a future at once, and cancelling it cancels the request's coroutine and its provider calls. The scope uses `SupervisorJob`, so one failed request can't cancel the others."
 ],
 "quiz": [
  {
   "q": "Inside `supervisorScope`, an `async` child throws `IOException` at 50 ms, while its two siblings run until 300 ms. Nobody has called `await` yet. What happens at 50 ms?",
   "options": [
    "The scope is cancelled and rethrows the `IOException`",
    "Nothing visible: the exception waits in that child's `Deferred`, and the siblings keep running",
    "The uncaught exception handler prints it, and the siblings are cancelled",
    "The two siblings are cancelled, but the scope itself keeps running"
   ],
   "answer": 1,
   "why": "In a supervisor, a failed child doesn't cancel its siblings or the scope. A failed `async` keeps its exception for `await`, which rethrows it when you get there. A handler is never used for `async`. In a plain `coroutineScope`, the first option would be right.",
   "from": "co-06"
  },
  {
   "q": "Each provider call is `async { withTimeout(300) { p.quote(s) } }` inside `supervisorScope`, and the code that awaits it does `catch (e: CancellationException) { throw e }`. One provider takes a second. What does the request get?",
   "options": [
    "The best of the other two prices, with `null` for the slow provider",
    "It waits a full second for the slow provider",
    "An `IOException` from the slow provider",
    "It ends with `TimeoutCancellationException`, as if the whole request had been cancelled"
   ],
   "answer": 3,
   "why": "`withTimeout` signals a late call with `TimeoutCancellationException`, a subclass of `CancellationException`. The catch rethrows it, so one provider's timeout ends the request. Use `withTimeoutOrNull` for your own deadline, and call `currentCoroutineContext().ensureActive()` before deciding a cancel was yours.",
   "from": "co-05"
  },
  {
   "q": "In the Reactor version, one provider's `Mono` completes empty: no value and no error. What does `Mono.zip` of the three do if that source has no `defaultIfEmpty`?",
   "options": [
    "It emits a tuple with an empty slot",
    "It fails with `NoSuchElementException`",
    "It completes empty at once and cancels the other two calls",
    "It waits for the other two and emits their pair"
   ],
   "answer": 2,
   "why": "`Mono.zip` needs one value from every source. When one completes empty there is nothing to combine, so the zip completes empty, with no error, and cancels the rest. The request would get no quote and no error. Mapping each source to `Optional` with `defaultIfEmpty(Optional.empty())` names the empty case.",
   "from": "rx-04"
  },
  {
   "q": "`QuoteService.quote` returned `scope.future { best.quote(symbol) }` to the handler, and the client hangs up, so `channelInactive` calls `cancel(true)` on it. What happens to the three provider calls?",
   "options": [
    "They are cancelled at their next suspension point: cancelling the future cancels the coroutine, and the cancel goes down the job tree",
    "Nothing: `CompletableFuture.cancel` never reaches the work behind a future",
    "Their threads are interrupted",
    "They finish, and their results go into the cache"
   ],
   "answer": 0,
   "why": "The `future` builder links both ways: the coroutine completes the future, and cancelling the future cancels the coroutine. From there cancellation travels down to the `supervisorScope` and its `async` children. A future made with `supplyAsync` is the case where the second option holds.",
   "from": "co-11"
  },
  {
   "q": "Someone builds `QuoteService`'s scope from `context + Job()` instead of `SupervisorJob()`. One request fails with `NoQuoteException` while 40 others are in flight. What happens?",
   "options": [
    "Only that request's future fails",
    "The other 40 are cancelled, the scope is cancelled, and every later request's future comes back cancelled at once",
    "The other 40 finish, but new requests fail",
    "Only requests for the same symbol are cancelled"
   ],
   "answer": 1,
   "why": "A failed child cancels a plain `Job` parent, and the cancelled parent cancels all its other children. A cancelled scope can't run new coroutines either: each new `future` completes with `JobCancellationException` at once. With `SupervisorJob`, each request's failure stays in its own future.",
   "from": "co-03"
  }
 ],
 "flashcards": [
  {"front": "Best-of fan-out: `coroutineScope` or `supervisorScope`?", "back": "`supervisorScope`. Any one answer will do, so a failed call must not cancel the others."},
  {"front": "Why `withTimeoutOrNull` inside each `async`, not one `withTimeout` around the whole fan-out?", "back": "Per call, only the late provider drops out. Around everything, the timeout cancels all calls and throws away answers that already arrived."},
  {"front": "Why is `catch (e: CancellationException) { throw e }` wrong around a provider's `await` in this fan-out?", "back": "A provider's own client timeout throws a `CancellationException` too, so rethrowing it ends the whole request."},
  {"front": "What does `currentCoroutineContext().ensureActive()` tell you inside a catch?", "back": "It throws only if your own coroutine was cancelled. If it returns, the cancellation came from the call you awaited."},
  {"front": "What does `cancel(true)` on a future from `scope.future { }` do?", "back": "It cancels the coroutine, and through the job tree every child the coroutine started."},
  {"front": "Why does `QuoteService` build its scope with `SupervisorJob()`?", "back": "With a plain `Job`, one failed request cancels the scope and every other request, and later futures come back cancelled at once."},
  {"front": "May a stale quote refresh the cache?", "back": "No. Only live answers go in; otherwise one old price could be served forever."}
 ],
 "terms": [
  {"term": "Fan-out", "plain": "Starting several independent calls at once and combining what comes back."},
  {"term": "Deadline", "plain": "The time by which a request must answer, whatever its dependencies do."},
  {"term": "Supervisor scope", "plain": "A scope whose children fail alone; cancelling the scope still cancels them all."},
  {"term": "Stale quote", "plain": "The last live price for a symbol, served and labelled as old when no provider answers in time."},
  {"term": "future builder", "plain": "`scope.future { }`: starts a coroutine and returns a `CompletableFuture` linked to it both ways."},
  {"term": "Job tree", "plain": "The parent and child jobs of running coroutines; cancellation travels down it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why `BestQuote` needs `supervisorScope`, `withTimeoutOrNull` on every call and that odd `ensureActive()` in a catch, and what actually stops the provider calls when a client hangs up. Explain it in your own words.",
  "answer": "A quote needs any one price, not all three, so one provider failing must not cancel the others. In a plain coroutineScope a failed child cancels its siblings at once, so we use supervisorScope, where each async keeps its failure for await and we turn it into no answer. Each call gets the deadline with withTimeoutOrNull: a late provider becomes null and the others still count, and since all calls start together the request ends by the deadline. withTimeout would be worse because its TimeoutCancellationException is a CancellationException, and a provider's own client can throw one too. If we rethrew every CancellationException, one provider's timeout would end the request. So in the catch we call ensureActive: it throws only if our own coroutine was cancelled, and otherwise that provider just has no answer. With no answers we serve the last live quote marked stale, or fail with NoQuoteException. On hang-up, lesson 1's handler cancels the future in channelInactive; scope.future links that future to the request's coroutine, so the coroutine is cancelled and the cancel goes down the job tree to the three provider calls. The service's scope uses SupervisorJob so one failed request can't cancel the rest."
 },
 "deeper": {
  "minutes": 8,
  "body": "Four refinements a production fan-out often adds.\n\nPropagate the deadline. The service knows that a request has, say, 180 ms left; the provider doesn't. Many RPC systems carry the remaining time in a header, so that the provider can give up too instead of finishing work nobody will read. With coroutines you compute it from a start time and pass it down; `withTimeoutOrNull` then wraps the remaining budget, not a fixed number.\n\nAnswer early when the answer can't improve. If the request only needs a price within 0.5 pip of the best seen in the last second, it can return as soon as one such price arrives and cancel the rest. That is `select` over the `onAwait` clauses (\"Channels, select and pipelines\"), with the losers cancelled by hand.\n\nPut an age on the cache. Store the time with each quote and refuse to serve one older than a few seconds. Then a long outage ends in a clear error, not in a price from the morning.\n\nMind the `await` legacy rule. The kotlinx.coroutines KDoc notes that `await()` on a `Deferred` that someone else cancelled throws `CancellationException` in *your* coroutine, even though your coroutine is fine. This lesson's `ensureActive()` check is the documented way to tell the two apart, and it is worth using anywhere you await work you didn't start.\n\nLesson 3 of this track adds what the fan-out still lacks: a limit on how many calls each provider sees at once, retries for the calls that are safe to repeat, a hedge for the slowest provider, and load shedding when the whole service is full."
 },
 "sources": [
  {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html"},
  {"title": "supervisorScope (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/supervisor-scope.html"},
  {"title": "withTimeoutOrNull (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout-or-null.html"},
  {"title": "Future.kt: the future builder and CompletionStage.await (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/master/kotlinx-coroutines-core/jvm/src/future/Future.kt"},
  {"title": "Mono Javadoc source, reactor-core 3.8.x (zip, timeout, toFuture)", "url": "https://raw.githubusercontent.com/reactor/reactor-core/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Mono.java"}
 ]
}

out = ROOT / "content/lessons/cap2-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
