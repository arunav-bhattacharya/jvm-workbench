import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l02"
K = "kotlin/workbench/quotes/l02"
read = lambda p: (ROOT / p).read_text()


def pair_kj(kotlin, java):
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def fill(text, **parts):
    """Put code pairs into prose written with @@NAME@@ placeholders (no brace escaping needed)."""
    for k, v in parts.items():
        text = text.replace(f"@@{k}@@", v)
    assert "@@" not in text, text[text.index("@@") - 40:text.index("@@") + 40]
    return text


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
    '<svg viewBox="0 0 680 262" role="img" aria-label="Timeline of one price request: Northline answers at 120 ms, '
    'Fjord at 200 ms, Eastgate would answer at 300 ms but is cancelled at the 250 ms deadline, so the request answers '
    'at 250 ms with the lowest price that arrived.">'
    '<line class="ln" x1="110" y1="47" x2="630" y2="47" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="652" y="51" text-anchor="middle">ms</text>'
    + ticks +
    '<text class="t" x="56" y="89" text-anchor="middle">northline</text>'
    f'<rect class="box-ok" x="{x(0)}" y="68" width="{x(120) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(120)) // 2}" y="89" text-anchor="middle">12.45</text>'
    '<text class="t" x="56" y="139" text-anchor="middle">fjord</text>'
    f'<rect class="box-ok" x="{x(0)}" y="118" width="{x(200) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(200)) // 2}" y="139" text-anchor="middle">12.43, the best in time</text>'
    '<text class="t" x="56" y="189" text-anchor="middle">eastgate</text>'
    f'<rect class="box-bad" x="{x(0)}" y="168" width="{x(250) - x(0)}" height="32" rx="8"/>'
    f'<text class="t-s" x="{(x(0) + x(250)) // 2}" y="189" text-anchor="middle">cancelled at the deadline</text>'
    f'<rect class="box-dim" x="{x(250)}" y="168" width="{x(300) - x(250)}" height="32" rx="8"/>'
    f'<text class="t-s t-m" x="{(x(300) + 640) // 2}" y="189" text-anchor="middle">would be 300</text>'
    f'<line class="ln-bad" x1="{x(250)}" y1="58" x2="{x(250)}" y2="214"/>'
    f'<text class="t-s t-bad" x="{x(250)}" y="230" text-anchor="middle">deadline: 250 ms</text>'
    '<text class="t-s t-a" x="340" y="252" text-anchor="middle">the request answers at 250 ms with fjord 12.43</text>'
    '</svg>'
)

K_FAN = """suspend fun allPrices(destination: String): List<Quote> = coroutineScope {
    couriers.map { c -> async { c.quote(destination) } }   // 1. text all three
        .awaitAll()                                       // 2. then read the replies: the slowest decides
}"""
J_FAN = """// Java equivalent with Reactor: Mono.zip subscribes to all three sources at once
Mono<List<Quote>> allPrices(String destination) {
    return Mono.zip(northline.quote(destination), eastgate.quote(destination), fjord.quote(destination))
            .map(t -> List.of(t.getT1(), t.getT2(), t.getT3()));
}"""
K_DEADLINE = """couriers.map { c ->
    async { withTimeoutOrNull(deadline) { c.quote(destination) } }   // null if c misses the deadline
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
        currentCoroutineContext().ensureActive()   // 1. were WE cancelled? then this rethrows
        null                                        // 2. no: only the courier's call ended that way
    } catch (e: Exception) {
        null                                        // 3. the courier failed: no answer from it
    }"""
J_AWAIT = """// Java equivalent with Reactor: each source handles its own error, so the zip never sees one
Mono<Optional<Quote>> alone(Mono<Quote> call) {
    return call.map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))   // a failure stays with its courier
            .defaultIfEmpty(Optional.empty());                 // and so does an empty answer
}"""
K_TAIL = """val best = answers.minByOrNull { it.price }
if (best != null) {
    cache.remember(best)                       // only live answers refresh the cache
    return best
}
return cache.lastGood(destination)?.asStale()  // an old price, marked, beats no price
    ?: throw NoQuoteException(destination)     // the handler writes "7 ERR no quote for LISBON\""""
J_TAIL = """// Java equivalent with Reactor: an empty Optional switches to the cache
.flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(destination)))
.doOnNext(q -> { if (!q.stale()) cache.remember(q); })   // only live answers refresh the cache"""
K_SERVICE = """class QuoteService(context: CoroutineContext, private val best: BestQuote) : QuoteSource, AutoCloseable {
    private val scope = CoroutineScope(context + SupervisorJob())   // 1. owned; failures stay per request

    override fun quote(destination: String): CompletableFuture<Quote> =
        scope.future { best.quote(destination) }                     // 2. returns at once; cancel() reaches it

    override fun close() = scope.cancel()                            // 3. closing the service cancels the rest
}"""
J_SERVICE = """// Java equivalent with Reactor: toFuture() subscribes, and cancelling the future cancels the subscription
final class ReactorQuoteSource implements QuoteSource {
    @Override
    public CompletableFuture<Quote> quote(String destination) {
        return best(destination).toFuture();                         // returns at once; cancel() reaches the zip
    }
}"""

OPENING = """Remember the home cook from the Kotlin coroutines track. When she needed tomatoes, she texted three shops at once and waited only as long as the slowest reply. Now she does it for the post office counter. A customer asks what it costs to send a parcel to Lisbon. She texts three couriers, sets the kitchen timer, and passes on the cheapest reply that came in before it rang.

The plan is simple, and a bad day breaks it in three places. One courier answers with an error, and a careless kitchen throws away the other two replies. One is still typing when the timer rings. And the customer may walk away before anyone answers, leaving three couriers working for nobody.

A Netty server that never blocks its loop left the counter with a promise: `quote` hands back a ticket at once. In this lesson, we'll keep that promise with coroutines: ask all three couriers together under one deadline, let one fail alone, serve the last good price when nobody answers, and stop the calls when the customer hangs up. Before we start, make a guess, and keep it in mind."""

S1 = fill("""Lesson 1 left the server with a `QuoteSource` that must return a future at once. This lesson writes that source, in Kotlin. For each request it asks Northline, Eastgate and Fjord for a price, keeps the lowest, and answers by a deadline, whatever the couriers do.

The tool is the coroutine. A **coroutine** is a piece of work that can pause without holding its thread, like a dish the cook leaves to simmer while she starts the next one (Suspend functions from zero). A suspend function is a function that can pause that way. In the lab, each courier is a `Provider`: a name, and a suspend function `quote(destination)` that returns that courier's price, or throws.

The shape comes from Builders: launch, async, runBlocking, coroutineScope, where the cook texted three shops first and read the replies after. `async` starts a coroutine that will bring back a result, and hands you a `Deferred`, the coroutine's own ticket for that result. `awaitAll` waits until every ticket has its answer. Say the couriers need 120, 300 and 200 ms. Asked one after another, they take 620 ms. Asked together, they take 300 ms, the time of the slowest:

@@FAN@@

`coroutineScope` gives the three calls a parent that waits for all of them, so none of them can outlive the function. The Java twin uses Reactor from the Reactive track: `Mono.zip` subscribes to all three sources at once and waits for a value from each, like packing a gift box that closes only when every slot is full.

The deadline is the next decision. A price that arrives after two seconds is no use to a customer standing at the counter. So each call gets the kitchen timer:

@@DEADLINE@@

`withTimeoutOrNull` is a cancel with a timer, as Cancellation and timeouts called it. At the deadline it cancels the late call, which stops at its next suspension point, the next place where it pauses, and returns `null` for it. A **deadline** is the moment by which the request must answer, whatever its couriers are doing.

You may wonder why each call gets its own timer, and not one `withTimeout` around the whole fan-out. Both bound the request. Around the whole fan-out, the timer cancels everything and throws away the answers that did arrive. In the figure, Northline answered at 120 ms and Fjord at 200 ms, and with one timer for everything we would still have nothing to say. With a timer per call, only the late courier drops out. Because all the calls start together, a deadline per call is also a deadline for the request.

That's a good day. On a bad day, a courier doesn't just run late. It fails.""", FAN=pair_kj(K_FAN, J_FAN), DEADLINE=pair_kj(K_DEADLINE, J_DEADLINE))

S2 = fill("""The first draft of `BestQuote`, the starting code of this lesson's lab, uses `coroutineScope` and `withTimeout`. Both are wrong for a price, for reasons earlier lessons gave.

`coroutineScope` treats its children as one unit of work. Structured concurrency: scopes, jobs and the tree put it as a kitchen rule: a course goes out only when all of its dishes are ready. So when Northline throws `IOException` at 50 ms, the scope cancels Eastgate and Fjord and rethrows, as Exceptions: launch vs async, SupervisorJob, handlers showed with the burnt gravy. That's right when a page needs all three answers. A price needs any one of them.

`supervisorScope` is the bake sale from that lesson, where one burnt tray doesn't spoil the others. Each child fails alone. A failed `async` keeps its exception in its `Deferred`, and `await` hands it to you, where you turn it into "no answer".

`withTimeout` has a subtler problem. It signals a late call with `TimeoutCancellationException`, and that is a kind of `CancellationException`, the exception that carries a cancel. Cancellation and timeouts gave the rule: never swallow a `CancellationException`, or you throw away the message that dinner is off. So you rethrow it, and now one courier's timeout looks like a cancel of the whole request, and ends it.

`withTimeoutOrNull` turns our own deadline into a plain `null`. But a courier can still throw a cancellation from deep inside its own code. Fjord's own client has a short fuse: it gives up after 100 ms, and it says so with a `TimeoutCancellationException` of its own. So we have to be precise, and rethrow only when *our* coroutine was cancelled. `ensureActive()` asks exactly that question:

@@AWAIT@@

Let's read the catch in order. If the request itself was cancelled, because the client hung up, `ensureActive()` throws, and the cancel carries on up (1). If it returns, the cancellation belonged to the courier's call, and that courier simply has no answer (2). Any other exception is a courier that failed, and it counts as no answer too (3).

This section's demo runs the same three calls in three scopes. Northline fails at 50 ms, Fjord's client gives up at 100 ms, and Eastgate answers at 300 ms. On virtual time, a fake clock that skips the waiting, it printed:

| Scope | Outcome |
|---|---|
| `coroutineScope`, `awaitAll` | fails at 50 ms: `IOException: northline 503` |
| `supervisorScope`, rethrow every cancel | fails at 100 ms: `TimeoutCancellationException` |
| `supervisorScope`, rethrow only our cancel | answers `eastgate 12.41` at 300 ms |

The first scope lost two good couriers to one bad one. The second lost Eastgate's price to Fjord's short fuse. Only the third answered.

**A caught cancellation may belong to someone else. Ask whose it is before you rethrow it.**

Reactor has no such trap, because there a cancel is not an error signal: you isolate each source with `onErrorResume` before `Mono.zip`. The compare block puts the two whole fan-outs side by side.

One courier can now fail alone, and a late one drops out. But what if all three do?""", AWAIT=pair_kj(K_AWAIT, J_AWAIT))

S3 = fill("""Sometimes no courier answers by the deadline. The network between us and them is down, or every courier is swamped on the busiest morning of the year. The service then has three choices. It can wait longer, fail the request, or serve the last price it saw.

Waiting longer breaks the deadline, which is the one promise the service makes. Failing is honest, and no help to a customer who only wants a rough idea of the cost. So `BestQuote` keeps a **cache**, a store of recent answers kept close at hand: here, the last live price for each destination. When nobody answers, it serves that price marked as **stale**, old and labelled so, as `7 STALE LISBON 12.41 eastgate`. The customer sees the word and decides whether a slightly old price is good enough:

@@TAIL@@

Two rules keep the cache honest. Only live answers go into it. If a stale answer could refresh the cache, one old price could be served forever, each serving making it look new. And with nothing cached, the request fails with `NoQuoteException`, which lesson 1's handler turns into `7 ERR no quote for LISBON`. A shrug, but at least a quick one. A production cache would also have an age limit, so that a price from a minute ago is served and one from last week is not.

Check yourself: after an outage, the couriers recover. On the next request Eastgate answers 12.39 and Fjord 12.42. What does the customer get, and what does the cache hold for Lisbon afterwards? (`OK LISBON 12.39 eastgate`, and the cache now holds that live price in place of the old one.)

The fan-out is complete. It still has to meet lesson 1's Java handler, and the handler holds the one thing we haven't used yet: a cancel.""", TAIL=pair_kj(K_TAIL, J_TAIL))

S4 = fill("""Lesson 1's handler calls `quote` on the event loop, and it cancels the future when the client hangs up. `QuoteService` connects that future to a coroutine:

@@SERVICE@@

The service owns a scope, the object that starts coroutines and keeps track of them (1). `scope.future { }` starts a coroutine in that scope and returns a `CompletableFuture` at once (2), so the event loop never waits. Coroutines meet Java pictured this bridge as the neighbour's ticket, and here the ticket is tied to the coroutine in both directions. When the coroutine finishes, the future completes. When someone cancels the future, the coroutine is cancelled. Closing the service cancels whatever is left (3).

The second direction is what ties a request to its connection. The client hangs up, `channelInactive` cancels the future, and the `future` coroutine is cancelled. The cancel then travels down the **job tree**, the parent and child links between running coroutines, to the `supervisorScope` and its three courier calls. The guests have called dinner off, and this time the news reaches every pot on the stove.

Why not give each connection its own scope and cancel it in `channelInactive`? That works too, and it's the shape to pick when the handler itself is written in Kotlin. Here, the Java handler from lesson 1 already keeps every pending future and cancels them on close, so a scope per connection would track the same requests twice. With `future { }`, the Java side holds the ticket, the Kotlin side holds the tree, and neither needs to know how the other works.

Two choices in the scope matter. The scope uses a `SupervisorJob`, a parent that lets each child fail alone. With a plain `Job`, one request that fails with `NoQuoteException` would cancel its parent, and with it every other request in flight. Every later `future` would then come back cancelled at once. And the scope takes its dispatcher, the part of a coroutine's context that decides which threads run it, as a parameter. Production passes `Dispatchers.Default`. The tests pass a `StandardTestDispatcher`, the rehearsal dinner on a fake clock from Shared state and testing coroutines, so every `delay` and every deadline runs on virtual time, and a test of a 300 ms deadline takes a few milliseconds.

This section's demo starts one request behind `scope.future { }`, with three courier calls of 300, 400 and 500 ms, and cancels the future after 120 ms, as `channelInactive` would. All three calls print `cancelled` within a few milliseconds of the hang-up, and the scope is left with 0 coroutines. The Java twin builds the same request from three `supplyAsync` calls and cancels it the same way. It prints `calls cancelled: 0 of 3`, and the three couriers answer later with nobody listening. Cancelling a plain `CompletableFuture` voided the ticket and stopped nothing.

**A cancel that can't reach the work only hides it. Tie the ticket to the coroutine with `future { }`.**

The service now answers within its deadline and cleans up after a customer who leaves. It still trusts the couriers with as many calls as it likes, and a crowd will test that.""", SERVICE=pair_kj(K_SERVICE, J_SERVICE))

ASIDE = {
    "title": "Is serving an old price honest?",
    "body": "It is when it says so. The reply carries the word `STALE`, so the customer, or the program they use, knows the price may have moved and can decide. For a rough idea of the cost, a recent price is fine; for a booking, the courier will confirm the real price anyway. What would not be honest is serving the old price as `OK`. That's why the label lives in the `Quote` itself, as its `stale` field, and the protocol turns it into a different word on the wire."
}

# ---- worked example: test the deadline on virtual time ----
W1K = """class FakeProvider(
    override val name: String,
    private val price: String,
    private val latency: Duration,
    private val cancelled: MutableList<String>,
) : Provider {
    override suspend fun quote(destination: String): Quote {
        try {
            delay(latency)                     // 1. virtual time under runTest
        } catch (e: CancellationException) {
            cancelled += name                  // 2. record who was cancelled
            throw e
        }
        return Quote.live(destination, price, name)
    }
}"""
W1J = """// Java equivalent with Reactor: Mono.delay runs on Schedulers.parallel(), which virtual time replaces
Mono<Quote> fake(String name, String price, Duration latency, List<String> cancelled) {
    return Mono.delay(latency)                                        // 1. virtual time under StepVerifier
            .map(x -> Quote.live("LISBON", price, name))
            .doOnCancel(() -> cancelled.add(name));                   // 2. record who was cancelled
}"""
W2K = """@Test
fun `a provider slower than the deadline is cancelled at the deadline`() = runTest {
    val best = BestQuote(listOf(northline(120), eastgate(1_000), fjord(200)), deadline = 300.milliseconds)
    val quote = best.quote("LISBON")
    assertThat(quote.provider).isEqualTo("fjord")
    assertThat(currentTime).isEqualTo(300)            // 3. exact, and the test takes milliseconds
    assertThat(cancelled).containsExactly("eastgate")
}"""
W2J = """// Java equivalent with Reactor: StepVerifier on virtual time
StepVerifier.withVirtualTime(() -> best("LISBON"))           // build the Mono inside the supplier
        .expectSubscription()
        .expectNoEvent(Duration.ofMillis(299))
        .thenAwait(Duration.ofMillis(1))                      // 3. exactly at the deadline
        .expectNextMatches(q -> q.provider().equals("fjord"))
        .verifyComplete();
assertThat(cancelled).containsExactly("eastgate");"""
W3K = """@Test
fun `cancelling the future cancels all three provider calls`() = runTest {
    val service = QuoteService(StandardTestDispatcher(testScheduler), slowBest)   // 4. inject the test clock
    val future = service.quote("LISBON")
    runCurrent()                                     // the three calls have started
    future.cancel(true)                              // what channelInactive does
    runCurrent()
    assertThat(cancelled).containsExactlyInAnyOrder("northline", "eastgate", "fjord")
    assertThat(service.inFlight).isEqualTo(0)
}"""
W3J = """// Java equivalent with Reactor: cancelling toFuture() cancels the subscription at once
CompletableFuture<Quote> future = source.quote("LISBON");
future.cancel(true);                                 // what channelInactive does
assertThat(cancelled).containsExactlyInAnyOrder("northline", "eastgate", "fjord");"""

COMPARE_J = """// Reactor: errors, timeouts and empties become values at each source, then Mono.zip
Mono<Quote> best(String destination) {
    return Mono.zip(inTime(northline.quote(destination)), inTime(eastgate.quote(destination)), inTime(fjord.quote(destination)))
            .map(t -> Stream.of(t.getT1(), t.getT2(), t.getT3())
                    .flatMap(Optional::stream)
                    .min(Comparator.comparing(Quote::price)))
            .flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(destination)))
            .doOnNext(q -> { if (!q.stale()) cache.remember(q); });
}

Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE)
            .map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))   // a failure or a timeout: no answer
            .defaultIfEmpty(Optional.empty());                 // an empty source would empty the zip
}

Mono<Quote> fromCache(String destination) {
    Quote last = cache.lastGood(destination);
    return last != null ? Mono.just(last.asStale()) : Mono.error(new NoQuoteException(destination));
}"""
COMPARE_K = read(f"{lab}/solution/{K}/BestQuote.kt").split("class BestQuote(", 1)[1]
COMPARE_K = "class BestQuote(" + COMPARE_K.rstrip() + "\n"

DRILL_K = """suspend fun quote(destination: String): Quote {
    val answers = supervisorScope {
        providers
            .map { p -> async { withTimeoutOrNull(deadline) { p.quote(destination) } } }
            .map { d ->
                try { d.await() }
                catch (e: CancellationException) { currentCoroutineContext().ensureActive(); null }
                catch (e: Exception) { null }
            }
    }.filterNotNull()
    val best = answers.minByOrNull { it.price }
    if (best != null) return best.also { cache.remember(it) }
    return cache.lastGood(destination)?.asStale() ?: throw NoQuoteException(destination)
}"""
DRILL_J = """// Java equivalent with Reactor
Mono<Quote> best(String destination) {
    return Mono.zip(inTime(northline.quote(destination)), inTime(eastgate.quote(destination)), inTime(fjord.quote(destination)))
            .map(t -> Stream.of(t.getT1(), t.getT2(), t.getT3()).flatMap(Optional::stream)
                    .min(Comparator.comparing(Quote::price)))
            .flatMap(best -> best.map(Mono::just).orElseGet(() -> fromCache(destination)))
            .doOnNext(q -> { if (!q.stale()) cache.remember(q); });
}

Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE).map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))
            .defaultIfEmpty(Optional.empty());
}"""

CLOSING = """We started with a cook texting three couriers, the kitchen timer running, and a customer who might walk away. Now every request asks all three at once under one deadline. A courier that fails or runs late drops out alone, an old price goes out only with its label, and a hang-up reaches every pot on the stove.

Now look in your own code for `coroutineScope` around calls where any one answer would do, and for `catch (e: CancellationException) { throw e }` around an `await`.

Next, we'll put the service under load. What happens when a thousand customers ask at once, and Northline's contract allows only ten calls at a time?"""

L = {
 "id": "cap2-02",
 "title": "Fan out with coroutines, inside a deadline",
 "minutes": 38,
 "goal": "By the end you can fan one price request out to three couriers with `async` inside `supervisorScope`, give every call the same deadline with `withTimeoutOrNull`, fall back to the last good price marked stale, and tie each request's coroutine to its connection with `scope.future { }`, so that a client who hangs up cancels the courier calls.",
 "opening": OPENING,
 "warmup": {
  "q": "Inside `coroutineScope { }`, three `async` calls ask three couriers for a price. One courier throws `IOException` after 50 ms; the other two would answer at 120 and 300 ms. What does the request get?",
  "options": [
   "The lower of the two prices that came back, after 300 ms",
   "The `IOException` after about 50 ms, and the other two calls are cancelled",
   "The `IOException` after 300 ms, once the other two calls have finished",
   "Two prices and a `null` for the courier that failed"
  ],
  "answer": 1,
  "why": "A failed child cancels its parent at once, and a plain scope then cancels the other children and rethrows. So the request fails at 50 ms with the `IOException`, and the two calls that would have answered are cancelled. That's right when you need every answer, and wrong when any one will do. The fix for a price is `supervisorScope`, this lesson's first change."
 },
 "sections": [
  {
   "h": "One request, three couriers, one deadline",
   "body": S1,
   "figure": {"svg": FIG, "caption": "All three calls start together, and each gets the same deadline. The late call is cancelled at 250 ms, and the answers that arrived still count."},
   "try": {
    "title": "Three ways to ask three couriers",
    "minutes": 4,
    "steps": [
     "Open `FanOutDemo.kt`. It runs on virtual time with `runTest`, so the clock is exact. The Java twin, `FanOutDemoJava.java`, does the same with Reactor in real time.",
     "Predict the three times and the three answer lists: one after another, all at once, and all at once with a 250 ms deadline.",
     "Run it. Then set `deadline` to 100 and predict the last line again."
    ],
    "code": demo("FanOutDemo"),
    "expect": "620 ms in turn, 300 ms all at once, 250 ms with the deadline, where Eastgate (300 ms) comes back as `null` and the other two still count. With a 100 ms deadline, the last line takes 100 ms and all three answers are `null`: nobody was fast enough, which is the case section 3 handles. The Java twin prints similar times in real time (780, 307 and 267 ms in one run on a busy machine), with `Optional.empty` where Kotlin prints `null`."
   },
   "refs": [
    {"title": "withTimeoutOrNull (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-timeout-or-null.html", "kind": "docs"}
   ]
  },
  {
   "h": "Let one courier fail alone, and tell your cancel from theirs",
   "body": S2,
   "try": {
    "title": "One failure, one timeout, three scopes",
    "minutes": 4,
    "steps": [
     "Open `FailAloneDemo.kt`. Northline fails at 50 ms, Fjord's own client gives up at 100 ms, and Eastgate answers at 300 ms.",
     "Predict the outcome and the virtual time of each of the three attempts.",
     "Run it. Then, in `callAll()`, move `async { fjord() }` to the end of the list and predict the second line again."
    ],
    "code": demo("FailAloneDemo"),
    "expect": "`coroutineScope` fails at 50 ms with the `IOException`. The naive supervisor fails at 100 ms with `TimeoutCancellationException`: it rethrew Fjord's timeout as if it were its own cancel. The careful one answers `[null, null, eastgate 12.41]` at 300 ms. With Fjord last, the naive version waits for Eastgate first, then rethrows Fjord's exception: it fails at 300 ms instead of 100, and still throws Eastgate's price away. The Java twin shows the Reactor side: the raw `Mono.zip` fails on Northline's error, and with `onErrorResume` on each call it answers with Eastgate at about 300 ms."
   },
   "refs": [
    {"title": "Coroutine exceptions handling (Kotlin docs)", "url": "https://kotlinlang.org/docs/exception-handling.html", "kind": "read"},
    {"title": "ensureActive (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html", "kind": "docs"}
   ]
  },
  {
   "h": "When nobody answers, serve the last good price and say it is stale",
   "body": S3,
   "aside": ASIDE
  },
  {
   "h": "Tie each request to its connection with scope.future",
   "body": S4,
   "try": {
    "title": "Hang up on a request",
    "minutes": 3,
    "steps": [
     "Open `HangUpDemo.kt`. A request coroutine started with `scope.future { }` waits for three courier calls of 300, 400 and 500 ms. After 120 ms, the demo cancels the future, as `channelInactive` would.",
     "Predict which calls print `answered` and which print `cancelled`, and how many coroutines are left in the scope.",
     "Run it, then run the Java twin, which builds the request from three `supplyAsync` calls."
    ],
    "code": demo("HangUpDemo"),
    "expect": "All three calls print `cancelled` within a few milliseconds of the hang-up, and the scope has 0 coroutines left: the cancel went from the future to the coroutine and down to its children. The Java twin reports `calls cancelled: 0 of 3`, and the three couriers answer about 300, 400 and 500 ms after the start, with nobody listening. `CompletableFuture.cancel` completed the outer future and stopped nothing."
   },
   "refs": [
    {"title": "future (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The fan-out with Reactor's Mono.zip and with coroutines",
  "java": {"title": "BestQuoteReactor.java", "src": COMPARE_J},
  "kotlin": {"title": "BestQuote.kt", "src": COMPARE_K},
  "note": "Both start the three calls together, give each its own deadline, turn a failure into \"no answer\", keep the lowest price and fall back to the cache. In Reactor, every outcome becomes a value at the source. A timeout is an error signal you resume from, and an empty source is a third outcome you must name with `defaultIfEmpty`, or `Mono.zip` completes empty (Combining streams: zip, merge, concat, combineLatest). Nothing runs until something subscribes, and cancelling the subscription cancels the three calls. In Kotlin, the same policy is ordinary control flow: a scope, `try` and `catch`, `minByOrNull`. The scope guarantees that when `quote` returns, every call is either done or cancelled. The price of that directness is the `CancellationException` rule, which only coroutines have: a timeout is a cancel, so you must tell your own cancel from a courier's."
 },
 "worked": {
  "title": "Test the deadline and the hang-up on virtual time",
  "steps": [
   {"say": "Make the couriers controllable on the test clock. `delay` inside `runTest` uses virtual time, so a fake that delays 1,000 ms costs nothing, and recording cancellations in the `catch` tells the test exactly who was stopped.",
    "code": W1K, "lang": "kotlin", "alt_code": W1J, "alt_lang": "java"},
   {"say": "Test the deadline. `currentTime` is the virtual clock, so the assertion can be exact: 300, not \"under 400\". A version on the real clock would take 300 ms per test and could fail on a busy build machine.",
    "code": W2K, "lang": "kotlin", "alt_code": W2J, "alt_lang": "java"},
   {"say": "Test the hang-up through `QuoteService`. Pass `StandardTestDispatcher(testScheduler)` as its context, and the service's own scope runs on the test clock too. `runCurrent()` runs what is due now, without moving the clock.",
    "code": W3K, "lang": "kotlin", "alt_code": W3J, "alt_lang": "java"},
   {"say": "Know where virtual time stops. A `delay` inside `withContext(Dispatchers.Default)` escapes the test scheduler and takes real time (Shared state and testing coroutines), which is why the service takes its dispatcher as a parameter. The two end-to-end tests in this lab use `Dispatchers.Default` and a real Netty server, so they assert only with latches: 6 courier calls started, 6 cancelled after the hang-up. Self-check: what would `currentTime` read in a test that built `QuoteService(Dispatchers.Default, ...)` inside `runTest`? (0: the coroutines ran on real threads, and the virtual clock never moved.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fan out to three couriers, and cancel on hang-up",
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
   "Run the tests. Ten of eleven fail. The Java files in `l02` are lesson 1's solution, carried over; the tests' couriers are in `src/test/.../l02/FakeProvider.kt`.",
   "Fix `BestQuote` along points 1 to 3 of its KDoc: `supervisorScope`, `withTimeoutOrNull` inside each `async`, and an await that turns failures into `null` and rethrows only your own cancel.",
   "Add point 4: remember the best live price, else serve `cache.lastGood(destination)?.asStale()`, else throw `NoQuoteException(destination)`. The six `BestQuote` tests should pass.",
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
  "prompt": "Close the lab. Write `BestQuote.quote(destination)` from memory: all couriers at once, the same deadline for each, a failed or late courier counts as no answer, your own cancel still propagates, the lowest price wins, and with no answer you serve the cached price as stale or throw `NoQuoteException`. Which line would break the request when a courier's own client times out?",
  "answer": {"lang": "kotlin", "src": DRILL_K, "alt": {"lang": "java", "src": DRILL_J}}
 },
 "recap": [
  "Fan out with `async` inside a scope: three couriers at 120, 300 and 200 ms answer in 300 ms instead of 620.",
  "Give each call the deadline with `withTimeoutOrNull`. A late courier drops out as `null` and the others still count; one timeout around the whole fan-out throws away answers that already arrived.",
  "`supervisorScope` lets each courier fail alone, and a courier's own timeout is a `CancellationException` too. In the catch, `currentCoroutineContext().ensureActive()` rethrows only if your coroutine was cancelled.",
  "With no answer, serve the last live price marked `STALE`, or fail with `NoQuoteException`. Only live answers refresh the cache.",
  "`scope.future { }` gives the Java handler a future at once, and cancelling it cancels the request's coroutine and its courier calls. The scope uses `SupervisorJob`, so one failed request can't cancel the others.",
  "Where today's service stops: every request still goes to every courier at once, with no limit. A thousand requests mean a thousand calls to each courier."
 ],
 "closing": CLOSING,
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
   "q": "Each courier call is `async { withTimeout(300) { c.quote(d) } }` inside `supervisorScope`, and the code that awaits it does `catch (e: CancellationException) { throw e }`. One courier takes a second. What does the request get?",
   "options": [
    "The best of the other two prices, with `null` for the slow courier",
    "It waits a full second for the slow courier",
    "An `IOException` from the slow courier",
    "It ends with `TimeoutCancellationException`, as if the whole request had been cancelled"
   ],
   "answer": 3,
   "why": "`withTimeout` signals a late call with `TimeoutCancellationException`, a subclass of `CancellationException`. The catch rethrows it, so one courier's timeout ends the request. Use `withTimeoutOrNull` for your own deadline, and call `currentCoroutineContext().ensureActive()` before deciding a cancel was yours.",
   "from": "co-05"
  },
  {
   "q": "In the Reactor version, one courier's `Mono` completes empty: no value and no error. What does `Mono.zip` of the three do if that source has no `defaultIfEmpty`?",
   "options": [
    "It emits a tuple with an empty slot",
    "It fails with `NoSuchElementException`",
    "It completes empty at once and cancels the other two calls",
    "It waits for the other two and emits their pair"
   ],
   "answer": 2,
   "why": "`Mono.zip` needs one value from every source. When one completes empty there is nothing to combine, so the zip completes empty, with no error, and cancels the rest. The request would get no price and no error. Mapping each source to `Optional` with `defaultIfEmpty(Optional.empty())` names the empty case.",
   "from": "rx-04"
  },
  {
   "q": "`QuoteService.quote` returned `scope.future { best.quote(destination) }` to the handler, and the client hangs up, so `channelInactive` calls `cancel(true)` on it. What happens to the three courier calls?",
   "options": [
    "They are cancelled at their next suspension point: cancelling the future cancels the coroutine, and the cancel goes down the job tree",
    "Nothing: `CompletableFuture.cancel` never reaches the work behind a future",
    "Their threads are interrupted",
    "They finish, and their results go into the cache"
   ],
   "answer": 0,
   "why": "The `future` builder links both ways: the coroutine completes the future, and cancelling the future cancels the coroutine. From there, cancellation travels down to the `supervisorScope` and its `async` children. A future made with `supplyAsync` is the case where the second option holds.",
   "from": "co-11"
  },
  {
   "q": "Someone builds `QuoteService`'s scope from `context + Job()` instead of `SupervisorJob()`. One request fails with `NoQuoteException` while 40 others are in flight. What happens?",
   "options": [
    "Only that request's future fails",
    "The other 40 are cancelled, the scope is cancelled, and every later request's future comes back cancelled at once",
    "The other 40 finish, but new requests fail",
    "Only requests for the same destination are cancelled"
   ],
   "answer": 1,
   "why": "A failed child cancels a plain `Job` parent, and the cancelled parent cancels all its other children. A cancelled scope can't run new coroutines either: each new `future` completes with `JobCancellationException` at once. With `SupervisorJob`, each request's failure stays in its own future.",
   "from": "co-03"
  }
 ],
 "flashcards": [
  {"front": "Best-of fan-out: `coroutineScope` or `supervisorScope`?", "back": "`supervisorScope`. Any one answer will do, so a failed call must not cancel the others."},
  {"front": "Why `withTimeoutOrNull` inside each `async`, not one `withTimeout` around the whole fan-out?", "back": "Per call, only the late courier drops out. Around everything, the timeout cancels all calls and throws away answers that already arrived."},
  {"front": "Why is `catch (e: CancellationException) { throw e }` wrong around a courier's `await` in this fan-out?", "back": "A courier's own client timeout throws a `CancellationException` too, so rethrowing it ends the whole request."},
  {"front": "What does `currentCoroutineContext().ensureActive()` tell you inside a catch?", "back": "It throws only if your own coroutine was cancelled. If it returns, the cancellation came from the call you awaited."},
  {"front": "What does `cancel(true)` on a future from `scope.future { }` do?", "back": "It cancels the coroutine, and through the job tree, every child the coroutine started."},
  {"front": "Why does `QuoteService` build its scope with `SupervisorJob()`?", "back": "With a plain `Job`, one failed request cancels the scope and every other request, and later futures come back cancelled at once."},
  {"front": "May a stale price refresh the cache?", "back": "No. Only live answers go in; otherwise one old price could be served forever."}
 ],
 "terms": [
  {"term": "Coroutine", "plain": "A piece of work that can pause without holding its thread, and carry on later where it stopped."},
  {"term": "Fan-out", "plain": "Starting several independent calls at once and combining what comes back."},
  {"term": "Deadline", "plain": "The time by which a request must answer, whatever the calls behind it do."},
  {"term": "Supervisor scope", "plain": "A scope whose children fail alone; cancelling the scope still cancels them all."},
  {"term": "Stale price", "plain": "The last live price for a destination, served and labelled as old when no courier answers in time."},
  {"term": "future builder", "plain": "`scope.future { }`: starts a coroutine and returns a `CompletableFuture` linked to it both ways."},
  {"term": "Job tree", "plain": "The parent and child links between running coroutines; cancellation travels down it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why `BestQuote` needs `supervisorScope`, `withTimeoutOrNull` on every call and that odd `ensureActive()` in a catch, and what actually stops the courier calls when a client hangs up. Explain it in your own words.",
  "answer": "A price needs any one courier's answer, not all three, so one courier failing must not cancel the others. In a plain coroutineScope, a failed child cancels its siblings at once, so we use supervisorScope, where each async keeps its failure for await and we turn it into no answer. Each call gets the deadline with withTimeoutOrNull: a late courier becomes null and the others still count, and since all calls start together, the request ends by the deadline. withTimeout would be worse, because its TimeoutCancellationException is a CancellationException, and a courier's own client can throw one too. If we rethrew every CancellationException, one courier's timeout would end the request. So in the catch we call ensureActive: it throws only if our own coroutine was cancelled, and otherwise that courier just has no answer. With no answers, we serve the last live price marked stale, or fail with NoQuoteException. On hang-up, lesson 1's handler cancels the future in channelInactive; scope.future links that future to the request's coroutine, so the coroutine is cancelled and the cancel goes down the job tree to the three courier calls. The service's scope uses SupervisorJob, so one failed request can't cancel the rest."
 },
 "deeper": {
  "minutes": 8,
  "body": "Four refinements a production fan-out often adds.\n\nPass the deadline on. The service knows that a request has, say, 180 ms left; the courier doesn't. Many systems that call each other over a network send the time left along with each call, so that the far side can give up too, instead of finishing work nobody will read. With coroutines you compute it from a start time and pass it down; `withTimeoutOrNull` then wraps the time that is left, not a fixed number.\n\nAnswer early when the answer can't get much better. If any price within 10 cents of the lowest seen in the last minute is good enough, the request can return as soon as one such price arrives, and cancel the rest. That is `select` over the `onAwait` clauses (Channels, select and pipelines), with the losers cancelled by hand.\n\nPut an age on the cache. Store the time with each price, and refuse to serve one older than a few minutes. Then a long outage ends in a clear error, not in a price from last week.\n\nMind the `await` rule. The kotlinx.coroutines KDoc notes that `await()` on a `Deferred` that someone else cancelled throws `CancellationException` in *your* coroutine, even though your coroutine is fine. This lesson's `ensureActive()` check is the documented way to tell the two apart, and it is worth using anywhere you await work you didn't start.\n\nLesson 3 of this track adds what the fan-out still lacks: a limit on how many calls each courier sees at once, retries for the calls that are safe to repeat, a second call for the slowest courier, and turning work away when the whole service is full."
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
