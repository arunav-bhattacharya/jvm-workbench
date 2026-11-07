import json, pathlib, re
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l03"
K = "kotlin/workbench/quotes/l03"
read = lambda p: (ROOT / p).read_text()


def pair_kj(kotlin, java):
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def demo(name):
    """A Try-it code object for a Kotlin demo with its Java twin (NameJava.java)."""
    return {
        "lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
        "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l03.{name}Kt",
        "file": f"{lab}/demo/{K}/{name}.kt",
        "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{J}/{name}Java.java"),
                "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l03.{name}Java",
                "file": f"{lab}/demo/{J}/{name}Java.java"},
    }


# ---- the figure: every guard in the final program ----
provs = [  # y, class, name, rule
    (40, "box-a", "northbank", "bulkhead 10, retry, hedge at 80 ms"),
    (122, "box-ok", "eastgate", "bulkhead 40, retry"),
    (204, "box-b", "fjord", "bulkhead 5, firm quotes: called once"),
]
pp = []
for y, cls, name, rule in provs:
    pp.append(f'<rect class="{cls}" x="410" y="{y}" width="278" height="56" rx="8"/>')
    pp.append(f'<text class="t" x="549" y="{y + 23}" text-anchor="middle">{name}</text>')
    pp.append(f'<text class="t-s" x="549" y="{y + 43}" text-anchor="middle">{rule}</text>')
    pp.append(f'<line class="ln" x1="364" y1="150" x2="406" y2="{y + 28}" marker-end="url(#arr)"/>')
FIG = (
    '<svg viewBox="0 0 700 316" role="img" aria-label="The final quote service: a request passes admission, '
    'which sheds it with ERR busy when the service is full, then BestQuote with its 300 ms deadline fans out to three '
    'guarded providers: Northbank with a bulkhead of 10, retries and a hedge, Eastgate with a bulkhead of 40 and retries, '
    'and Fjord with a bulkhead of 5 and firm quotes that are called once. Shutdown stops accepting, stops admitting, '
    'drains, cancels the rest and closes.">'
    '<rect class="box" x="12" y="124" width="80" height="52" rx="8"/>'
    '<text class="t" x="52" y="155" text-anchor="middle">request</text>'
    '<line class="ln" x1="94" y1="150" x2="114" y2="150" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="116" y="124" width="110" height="52" rx="8"/>'
    '<text class="t" x="171" y="146" text-anchor="middle">admission</text>'
    '<text class="t-s t-m" x="171" y="165" text-anchor="middle">max in flight</text>'
    '<text class="t-s t-bad" x="171" y="196" text-anchor="middle">full: ERR busy</text>'
    '<line class="ln" x1="228" y1="150" x2="242" y2="150" marker-end="url(#arr)"/>'
    '<rect class="box" x="244" y="124" width="120" height="52" rx="8"/>'
    '<text class="t" x="304" y="146" text-anchor="middle">BestQuote</text>'
    '<text class="t-s t-m" x="304" y="165" text-anchor="middle">deadline 300 ms</text>'
    + "".join(pp) +
    '<rect class="box-dim" x="12" y="274" width="676" height="32" rx="8"/>'
    '<text class="t-s" x="350" y="295" text-anchor="middle">shutdown: stop accepting, stop admitting, drain in flight, cancel the rest, close</text>'
    '</svg>'
)

K_BULK = """class GuardedProvider(private val delegate: Provider, maxConcurrent: Int /* ... */) : Provider {
    private val permits = Semaphore(maxConcurrent)                 // kotlinx.coroutines.sync

    private suspend fun once(symbol: String): Quote =
        permits.withPermit { delegate.quote(symbol) }              // suspends while all permits are out
}"""
J_BULK = """// Java equivalent on virtual threads: java.util.concurrent.Semaphore, acquire before the try
private Quote once(String symbol) throws IOException, InterruptedException {
    permits.acquire();                                             // blocks a cheap virtual thread
    try {
        return delegate.quote(symbol);
    } finally {
        permits.release();
    }
}"""
K_GATE = """override suspend fun quote(symbol: String): Quote {
    val once: suspend () -> Quote = { permits.withPermit { delegate.quote(symbol) } }
    if (!delegate.idempotent) return once()                         // a firm quote: exactly one call
    val attempt: suspend () -> Quote = if (hedgeAfter == null) once else ({ hedged(hedgeAfter, once) })
    return retrying(backoff, random, attempt)
}"""
J_GATE = """// Java equivalent with Reactor: the same decision before any retry operator is added
Mono<Quote> quote(String symbol) {
    Mono<Quote> once = Mono.defer(() -> delegate.quote(symbol));
    if (!delegate.idempotent()) return once;                       // a firm quote: exactly one call
    return once.retryWhen(Retry.backoff(2, Duration.ofMillis(50)).jitter(0.5)
            .filter(e -> e instanceof IOException));
}"""
K_JITTER = """val factor = 1 + backoff.jitter * (random.nextDouble() * 2 - 1)   // 0.5 .. 1.5 for jitter 0.5
delay(backoff.nominal(n) * factor)                                  // cancellable: the deadline still rules"""
J_JITTER = """// Java equivalent on a virtual thread: the same factor, and a sleep that an interrupt ends
double factor = 1 + jitter * (ThreadLocalRandom.current().nextDouble() * 2 - 1);
Thread.sleep((long) (nominal(n).toMillis() * factor));"""
K_HEDGE = """suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T = coroutineScope {
    val first = async { call() }
    val early = withTimeoutOrNull(after) { first.await() }    // stops the waiting, not the call
    if (early != null) return@coroutineScope early
    val second = async { call() }                              // the hedge
    val winner = select { first.onAwait { it }; second.onAwait { it } }
    coroutineContext.cancelChildren()                          // stop the loser
    winner
}"""
J_HEDGE = """// Java equivalent with Reactor: the delayed hedge is cancelled before it starts if the first call wins
Mono<Quote> hedged(Duration after, Mono<Quote> call) {
    return Mono.firstWithValue(call, Mono.delay(after).then(call));
}"""
K_ADMIT = """override fun quote(symbol: String): CompletableFuture<Quote> {
    if (!accepting) return CompletableFuture.failedFuture(ShuttingDownException())
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(BusyException())   // never waits
    val reply = scope.future { best.quote(symbol) }
    reply.whenComplete { _, _ -> admission.release() }         // however the request ends
    return reply
}"""
J_ADMIT = """// Java equivalent: the same door with a java.util.concurrent.Semaphore
public CompletableFuture<Quote> quote(String symbol) {
    if (!accepting) return CompletableFuture.failedFuture(new ShuttingDownException());
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(new BusyException());
    CompletableFuture<Quote> reply = best(symbol).toFuture();
    reply.whenComplete((q, e) -> admission.release());
    return reply;
}"""
K_SHUT = """suspend fun shutdown(grace: Duration): Int {
    accepting = false                                            // 2. stop admitting
    val job = scope.coroutineContext.job
    withTimeoutOrNull(grace) { job.children.toList().joinAll() }   // 3. drain, up to grace
    val left = job.children.count()
    job.cancelAndJoin()                                          // 4. cancel the rest, wait for them
    return left
}

// QuoteApp: 1. server.stopAccepting(), then the above, then 5. server.close()"""
J_SHUT = """// Java equivalent for an executor-based service: the same order, from "Pools in production"
void shutdown(Duration grace) throws InterruptedException {
    server.stopAccepting();                                      // 1. no new connections
    accepting = false;                                           // 2. stop admitting
    pool.shutdown();
    if (!pool.awaitTermination(grace.toMillis(), MILLISECONDS)) {   // 3. drain, up to grace
        pool.shutdownNow();                                      // 4. interrupt the rest
        pool.awaitTermination(5, SECONDS);
    }
    server.close();                                              // 5. close connections, stop the loops
}"""

S1 = f"""Lesson 2's fan-out sends every request to every provider at once. With a thousand requests in flight, Northbank sees a thousand concurrent calls, and its contract allows 10. Past that it answers 429, or slows down for everyone. The fix is a **bulkhead**: a limit on the calls in flight to one provider, so that one provider's limit doesn't become everybody's outage. In coroutines it is a `Semaphore` from `kotlinx.coroutines.sync`, the same tool "Using virtual threads: one per task, limits with semaphores" used from the JDK:

{pair_kj(K_BULK, J_BULK)}

`withPermit` suspends while no permit is free. It holds no thread, and the wait is cancellable, so lesson 2's deadline still applies: a call that waits too long for a permit is cancelled with the rest and counts as no answer.

How many permits? Little's law ("Sizing a pool: CPU-bound, IO-bound and Little's law") says calls in flight equal arrival rate times time per call. If Northbank allows 10 calls at once and answers in 50 ms, it serves at most 200 calls a second. More permits add no capacity; they move the queue to Northbank's side, where you can't see it. Take the number from the provider's contract, and give each provider its own: Eastgate may allow 40, as the figure shows.

Two placement rules matter. The permit goes around each single call, not around a whole retry loop: a call that waits out its backoff shouldn't hold a permit, and a hedge is a second call that needs one of its own. And the bulkhead lives in the provider's wrapper, not around the fan-out. A limit on requests can't protect a provider, because each request makes three calls."""

S2 = f"""A transient failure, such as a 503 or a reset connection, often succeeds on a second try. But a retry is a second request, and the provider can't tell it from a new one. Northbank and Eastgate stream indicative prices, so asking twice changes nothing. Fjord's quotes are firm: each call reserves liquidity for two seconds and counts against our daily quota, and a retried firm quote reserves twice. So the decision belongs to the provider, as `Provider.idempotent`, false unless the provider says otherwise:

{pair_kj(K_GATE, J_GATE)}

`retrying` is the backoff loop from "Shared state and testing coroutines" with one change, jitter. When Northbank blips, every request in flight fails in the same millisecond. Without jitter they all come back one backoff later, in the same millisecond again, and hit a provider that is still recovering. Multiplying each wait by a random factor between 0.5 and 1.5 spreads them out, which is what Reactor's `Retry.backoff` does by default ("Errors, retries and timeouts"):

{pair_kj(K_JITTER, J_JITTER)}

This section's demo has 1,000 clients that failed together and retry after a nominal 100 ms. Without jitter, all 1,000 retries land in one millisecond. With a jitter of 0.5 they spread over 50 to 150 ms, and no millisecond gets more than 18.

Three more rules keep retries honest. Retry only errors that a later attempt might fix: here an `IOException`, never an unknown symbol. Keep every wait cancellable, so the deadline cuts off retries that can't finish in time; a retry after the deadline is work nobody will read. And count the calls: two retries means up to three calls per request, and Little's law applies to those as well."""

S3 = f"""Northbank answers in 40 ms most of the time, but one call in twenty takes 600 ms: a garbage-collection pause, or a slow replica. A retry doesn't help, because nothing failed; the call is just slow. A **hedge** does. If the first call hasn't answered by the time 95% of calls have, send one more identical call and take whichever answers first:

{pair_kj(K_HEDGE, J_HEDGE)}

`withTimeoutOrNull(after) {{ first.await() }}` stops waiting at the hedge time. It doesn't cancel `first`, which is a child of the `coroutineScope`, not of the timeout. Then `select` takes whichever deferred completes first ("Channels, select and pipelines"), and `cancelChildren()` stops the loser. Forget that line and `coroutineScope` waits for the slow call anyway, which undoes the hedge. In this section's demo, 200 Northbank quotes went from a p99 of 600 ms to a p99 of 120 ms, for 210 calls instead of 200. Hedging at the 95th percentile costs about 5% more calls.

That cost decides where hedges go. Hedge only an idempotent provider, because a hedge is a duplicate request. Hedge only the provider whose tail hurts, here Northbank, at a time taken from its measured latency. And make the hedge take its own permit from the bulkhead. When Northbank is saturated, a hedge would only add to the queue that made it slow, so under full load the hedge waits for a permit, and the first call usually wins. The lab has a test for exactly that: with one permit, the hedge never runs alongside the first call."""

S4 = f"""Bulkheads protect the providers. Nothing yet protects the service from more requests than it can answer within its deadline. Northbank takes 10 calls at a time at 50 ms each, so within 300 ms it can answer about 60 requests, and a burst of 500 leaves hundreds waiting for a permit until they fail at the deadline anyway. This section's demo measured it: 50 live answers, 450 misses, and 135,000 ms of waiting (summed over the requests that missed) that produced nothing.

**Load shedding** turns those slow failures into fast ones. `QuoteService` admits at most `maxInFlight` requests, and the next one gets a failed future at once, which lesson 1's handler writes as `7 ERR busy`:

{pair_kj(K_ADMIT, J_ADMIT)}

With 50 admitted, the same burst got the same 50 live answers, and the other 450 clients heard `busy` within a millisecond, early enough to try another instance. `tryAcquire` never waits, so the event loop that calls `quote` never waits either. The permit comes back in `whenComplete`, however the request ends, including a cancel after a hang-up.

Shutdown uses the same pieces, in the order "Pools in production: names, errors, context, shutdown" gave for thread pools:

{pair_kj(K_SHUT, J_SHUT)}

Stop accepting connections. Stop admitting requests (`ERR shutting down`). Give the requests in flight a grace period to finish. Cancel what is left and wait for it with `cancelAndJoin()`, so that no coroutine outlives the service. Then close the connections and the loops. Lesson 1's `ChannelGroup` matters here: each connection is closed on its own loop, behind the reply that the drain just let through."""

S5 = """Here is the finished design next to the question every reviewer asks about it: wouldn't one virtual thread per connection, with plain blocking calls, be simpler?

| Concern | This service | One virtual thread per connection |
|---|---|---|
| idle connections | a few loop threads hold thousands | one parked virtual thread each, a few KB |
| waiting for providers | suspended coroutines | blocked virtual threads |
| deadline and cancel | structured: the cancel reaches every provider call | interrupts, which some blocking clients ignore |
| per-provider limits | a `Semaphore` per provider | a `Semaphore` per provider |
| framing and backpressure | Netty codecs, auto-read | your own read loop; TCP does the pacing |
| code shape | futures at the Java edge, coroutines inside | plain blocking Java |

Virtual threads ("The thread-per-request wall") make the right column cheap, and for many services they are the better choice. Switch when the providers only ship blocking SDKs, such as JDBC or an old SOAP client: this design would then need a blocking pool behind the coroutines, and you'd pay for two models. Switch when the team writes Java and connections number in the thousands. Stay on the event loop when the service already lives on Netty (Vert.x, Quarkus), when connections number in the hundreds of thousands, when you need the protocol control that auto-read and codecs give you, or when the provider clients are non-blocking and a cancel must reach them.

Either way, the limits stay. Bulkheads, deadlines, admission and an ordered shutdown appear in both columns, because moving to virtual threads removes the pool, and with it the only limit nobody wrote down ("Moving a blocking service to virtual threads"). The question that picks the model is where the waiting happens ("Zero-copy, epoll, io_uring, and choosing a server model"). Here it happens in three provider calls per request, under a deadline, and both models can wait well."""

# ---- compare: the guards with coroutines and on virtual threads ----
sol = read(f"{lab}/solution/{K}/Resilience.kt")
K_RETRY_SRC = sol[sol.index("suspend fun <T> retrying"):sol.index("/**", sol.index("suspend fun <T> retrying"))].rstrip()
K_GUARD_SRC = sol[sol.index("class GuardedProvider("):].rstrip()
COMPARE_K = K_RETRY_SRC + "\n\n" + K_GUARD_SRC + "\n"
COMPARE_J = """// Java on virtual threads: the same guards around a blocking provider client
final class GuardedProvider {
    private final BlockingProvider delegate;
    private final Semaphore permits;
    private final Backoff backoff;

    GuardedProvider(BlockingProvider delegate, int maxConcurrent, Backoff backoff) {
        this.delegate = delegate;
        this.permits = new Semaphore(maxConcurrent);
        this.backoff = backoff;
    }

    Quote quote(String symbol) throws IOException, InterruptedException {
        if (!delegate.idempotent()) return once(symbol);             // 2. never repeat a firm quote
        for (int n = 1; ; n++) {
            try {
                return once(symbol);
            } catch (IOException e) {
                if (n > backoff.retries()) throw e;                   // out of retries
                double factor = 1 + backoff.jitter() * (ThreadLocalRandom.current().nextDouble() * 2 - 1);
                Thread.sleep((long) (backoff.nominal(n).toMillis() * factor));   // an interrupt ends it
            }
        }
    }

    private Quote once(String symbol) throws IOException, InterruptedException {
        permits.acquire();                                           // 1. every call holds a permit
        try {
            return delegate.quote(symbol);
        } finally {
            permits.release();
        }
    }
}"""

W1K = """override fun quote(symbol: String): CompletableFuture<Quote> {
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(BusyException())   // 49 -> 50: admitted
    val reply = scope.future { best.quote(symbol) }    // 300 ms deadline per provider call
    reply.whenComplete { _, _ -> admission.release() }
    return reply
}"""
W1J = """// Java equivalent: the same admission check in front of a Reactor fan-out
if (!admission.tryAcquire()) return CompletableFuture.failedFuture(new BusyException());   // 49 -> 50: admitted
CompletableFuture<Quote> reply = best(symbol).toFuture();       // 300 ms deadline per provider call
reply.whenComplete((q, e) -> admission.release());
return reply;"""
W2 = """  0 ms  northbank  permit 1 of 10, call 1 starts
 80 ms  northbank  no answer yet: the hedge takes permit 2 of 10, call 2 starts
120 ms  northbank  call 2 answers 1.0845; call 1 is cancelled, both permits are back
  0 ms  fjord      permit 1 of 5, one firm call (never retried, never hedged)
200 ms  fjord      answers 1.0843"""
W3 = """  0 ms  eastgate   permit, call 1
 30 ms  eastgate   IOException: 503; permit back; wait 50 ms x 1.3 = 65 ms
 95 ms  eastgate   permit, call 2
145 ms  eastgate   answers 1.0841
200 ms  BestQuote  all three answered: eastgate 1.0841 wins; admission permit back (50 -> 49)"""

DRILL_K = """suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T = coroutineScope {
    val first = async { call() }
    val early = withTimeoutOrNull(after) { first.await() }   // stop waiting, not the call
    if (early != null) return@coroutineScope early
    val second = async { call() }
    val winner = select { first.onAwait { it }; second.onAwait { it } }
    coroutineContext.cancelChildren()                         // or coroutineScope waits for the loser
    winner
}"""
DRILL_J = """// Java equivalent with Reactor
<T> Mono<T> hedged(Duration after, Mono<T> call) {
    return Mono.firstWithValue(call, Mono.delay(after).then(call));   // the loser is cancelled
}"""

L = {
 "id": "cap2-03",
 "title": "Hold up under load",
 "minutes": 40,
 "goal": "By the end you can give each provider a bulkhead sized with Little's law, retry only idempotent calls with backoff and jitter, hedge the slow tail of one provider, shed load at the door with a clear error, shut the service down in order without leaking a coroutine, and defend the whole design against one virtual thread per connection.",
 "warmup": {
  "q": "The quote service answers within 300 ms. Northbank takes 10 calls at a time and needs 50 ms per call. A burst of 500 requests arrives at once, and the service queues them all. About how many get a live Northbank price?",
  "options": [
   "All 500, each a little later than usual",
   "About 50 to 60: ten at a time, and six rounds of 50 ms fit in 300 ms",
   "About 10: only the first round",
   "None: the burst knocks Northbank over"
  ],
  "answer": 1,
  "why": "Little's law: 10 calls at once at 50 ms each is at most 200 calls a second, so 300 ms holds about 60. This lesson's demo got 50, because the sixth round ends exactly at the deadline. The other 450 wait for a permit until their deadline and then fail. Queueing them didn't get them a price; it made them slow failures. Section 4 turns them into fast ones."
 },
 "sections": [
  {
   "h": "A bulkhead for each provider, sized by Little's law",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The finished service: admission at the door, one deadline for the fan-out, and a different set of guards for each provider."},
   "try": {
    "title": "Forty requests, one provider, two limits",
    "minutes": 3,
    "steps": [
     "Open `BulkheadDemo.kt` (virtual time) or `BulkheadDemoJava.java` (virtual threads, real time). Forty requests call a provider that answers in 50 ms.",
     "Predict the most calls in flight at once, and the time until all forty are answered, with no limit and with a limit of 4.",
     "Run it. Then change the limit to 8 and predict again from Little's law."
    ],
    "code": demo("BulkheadDemo"),
    "expect": "No limit: 40 calls at once, all answered after 50 ms. Limit 4: 4 at once, and 40 / 4 = 10 rounds of 50 ms, 500 ms. With a limit of 8 it is 5 rounds, 250 ms. The Java twin prints the same peaks in real time, with a few extra milliseconds of scheduling. The limit didn't make anything faster; it made the provider's load a number you chose."
   },
   "refs": [
    {"title": "Semaphore (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-semaphore/", "kind": "docs"}
   ]
  },
  {
   "h": "Retry only what is safe to repeat, and spread the retries",
   "body": S2,
   "try": {
    "title": "A thousand retries in one millisecond",
    "minutes": 3,
    "steps": [
     "Open `RetryJitterDemo.kt` (or the Java twin, which computes the same waits without sleeping). A thousand clients failed together at 0 ms and retry after a nominal 100 ms.",
     "Predict how the retries spread over 25 ms buckets with no jitter and with a jitter of 0.5, and the most retries in any single millisecond.",
     "Run it. Then set the jitter to 0.1 and predict the busiest millisecond."
    ],
    "code": demo("RetryJitterDemo"),
    "expect": "No jitter: all 1,000 retries in the 100 to 124 ms bucket, and all of them in the same millisecond. Jitter 0.5: about 250 in each bucket from 50 to 149 ms (a few land at exactly 150 after rounding up), and the busiest millisecond has 18. With 0.1 the retries squeeze into 90 to 110 ms, and the busiest millisecond gets 58, three times as many: less jitter, less spread."
   },
   "refs": [
    {"title": "Retry and RetryBackoffSpec source (reactor-core 3.8.x)", "url": "https://raw.githubusercontent.com/reactor/reactor-core/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java", "kind": "docs"}
   ]
  },
  {
   "h": "Hedge the slow tail of one provider",
   "body": S3,
   "try": {
    "title": "Cut Northbank's tail",
    "minutes": 4,
    "steps": [
     "Open `HedgeDemo.kt`. Northbank answers in 40 ms, except every 20th call, which takes 600 ms. The demo asks for 200 quotes without a hedge, then with a hedge after 80 ms.",
     "Predict p50, p99, the slowest request and the number of calls for both runs.",
     "Run it. Then set the hedge to 30 ms, below Northbank's normal latency, and predict the number of calls."
    ],
    "code": demo("HedgeDemo"),
    "expect": "No hedge: p50 40 ms, p99 and max 600 ms, 200 calls. Hedge at 80 ms: p50 still 40, p99 and max 120 ms (80 ms of waiting plus a 40 ms hedge), 210 calls. With the hedge at 30 ms every request is hedged: 400 calls, twice the load, for a p99 that the 80 ms hedge already got down to 120. A hedge time below the normal latency duplicates every request. The Java twin uses Reactor's `Mono.firstWithValue` and prints about the same numbers in real time, give or take the scheduling delays of a busy machine."
   },
   "refs": [
    {"title": "select (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.selects/select.html", "kind": "docs"}
   ]
  },
  {
   "h": "Shed load at the door, then shut down in order",
   "body": S4,
   "try": {
    "title": "Queue the burst, or shed it",
    "minutes": 4,
    "steps": [
     "Open `ShedDemo.kt`. A burst of 500 requests meets a provider that takes 10 calls at a time, 50 ms each, under a 300 ms deadline.",
     "Predict the live answers, the misses, the requests shed as busy, and the time spent waiting for nothing, for both runs.",
     "Run it. Then admit 100 instead of 50 and predict the misses again."
    ],
    "code": demo("ShedDemo"),
    "expect": "Queue them all: 50 live answers, 450 misses, and 135,000 ms spent waiting by requests that got nothing. Admit 50: the same 50 live answers, 0 misses, 450 shed at once, and no wasted waiting. Admitting 100 gives the same 50 live answers, 50 misses and 15,000 ms of wasted waiting: past what the provider can serve in 300 ms, a bigger door only buys slow failures. The Java twin does the same with virtual threads in real time, so on a busy machine its numbers can drift by a few requests."
   },
   "refs": [
    {"title": "cancelAndJoin (kotlinx.coroutines API, from the Job documentation)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/cancel-and-join.html", "kind": "docs"}
   ]
  },
  {
   "h": "Design review: would one virtual thread per connection be simpler?",
   "body": S5
  }
 ],
 "analogy": "Picture the quote service as a restaurant on a Friday night with three suppliers. Each supplier has its own loading dock with a fixed number of bays: a truck that arrives when the bays are full waits outside (a bulkhead per provider). The host at the front door stops seating guests the kitchen can't serve before the theatre starts, and says so at once instead of letting them stand for an hour (shedding with `ERR busy`). A plate that comes out wrong is made again, but only when remaking is harmless; nobody runs the card twice (retry only idempotent calls). When one cook is slow, a second cook starts the same dish and the first plate out goes to the table (a hedge). At closing time the doors lock, the guests already eating finish, and the kitchen shuts after the last plate (an ordered shutdown). The analogy breaks at the hedge: a restaurant bins the second plate and eats the cost, while a provider counts both calls against your limit, which is why you hedge only the slow 5%.",
 "in_your_world": "The same guards sit in front of every payments dependency, with one difference that matters more than all the others: most payment calls are not idempotent. A card authorization, a capture or a refund must never be retried or hedged blindly, because the issuer can't tell a repeat from a new charge. Retry it only with the same idempotency key, and when the retries run out, mark it pending and reconcile, as \"Errors, retries and timeouts\" said. Reads are different: a balance, an FX rate or a BIN lookup can take a retry and a hedge. Give each issuer or acquirer its own bulkhead from its published limit, and pick one layer to own retries: a Temporal activity retry policy, SmallRye Fault Tolerance `@Retry` and a hand-written loop stacked on top of each other multiply the calls. During a Kubernetes rollout, the same shutdown order applies: fail the readiness check first so no new traffic arrives, drain within the termination grace period, then exit.",
 "mistake": "The most common load mistake is one retry policy for everything: every provider call, firm quotes and authorizations included, wrapped in the same `retry(3)` with no jitter. Under a short outage it sends synchronized waves of calls at a provider that is trying to recover, and for calls that aren't idempotent it does the work two or three times. The runner-up is an unbounded queue in front of a bounded resource: no admission limit, so a burst turns into hundreds of requests waiting for a permit until each one fails at its deadline, while the latency graph says the service is slow rather than full. Retry only idempotent calls, with jitter, inside the deadline, and shed at the door what you can't answer in time.",
 "compare": {
  "title": "The guards around a provider with coroutines and on virtual threads",
  "java": {"title": "GuardedProvider.java (virtual threads)", "src": COMPARE_J},
  "kotlin": {"title": "Resilience.kt", "src": COMPARE_K},
  "note": "The rules are the same in both: a permit around every single call, one call for a provider that isn't idempotent, and jittered retries for `IOException` only. What differs is what waiting and stopping cost. In Kotlin, `withPermit` and `delay` suspend, so a thousand requests waiting for a permit or a backoff hold no threads, and a cancel (the deadline or a hang-up) reaches them at once through the job tree. On virtual threads, `acquire` and `Thread.sleep` block, which is cheap too, and a cancel is an interrupt: it reaches the sleep and the semaphore, but only reaches the provider call if its client responds to interrupts. The Java version leaves the hedge out. On threads a hedge takes an `ExecutorCompletionService`, or JDK 25's `StructuredTaskScope`, still a preview API (\"Structured concurrency and scoped values\"), and the loser is stopped by an interrupt, which works only if its client responds to interrupts. Java code that can block on a virtual thread is shorter to read. Kotlin code gets the hedge and the deadline from the library."
 },
 "worked": {
  "title": "Trace one request through every guard on a bad afternoon",
  "steps": [
   {"say": "The scene: 49 requests are in flight (the limit is 50), Northbank's next call is one of its slow ones, and Eastgate is returning a 503 now and then. A request for EURUSD arrives. It takes the last admission permit, so the next request will hear `ERR busy`.",
    "code": W1K, "lang": "kotlin", "alt_code": W1J, "alt_lang": "java"},
   {"say": "`BestQuote` starts the three provider calls at 0 ms, each under the 300 ms deadline. Northbank's first call is slow, so at 80 ms the hedge starts with a second permit. Fjord's quote is firm, so it gets exactly one call and no hedge.",
    "code": W2, "lang": "text"},
   {"say": "Eastgate fails at 30 ms with an `IOException`. Its permit goes back during the backoff, and the jittered wait (65 ms here) puts the retry at 95 ms. By 200 ms every provider has answered, so `BestQuote` doesn't need the deadline at all this time.",
    "code": W3, "lang": "text"},
   {"say": "Self-check: run the same afternoon, but the client hangs up at 100 ms. Which calls are running at that moment, what stops them, and when does the admission count drop back to 49? (Four calls are running: Northbank's slow first call and its hedge, Eastgate's retry and Fjord's firm call. Lesson 1's `channelInactive` cancels the future, `scope.future` cancels the request coroutine, and the cancel reaches all four, the hedge included. The future completes at once, so `whenComplete` releases the admission permit at 100 ms.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Bulkheads, retries, a hedge, shedding and shutdown",
  "minutes": 18,
  "files": [
   f"{lab}/main/{K}/Resilience.kt",
   f"{lab}/main/{K}/QuoteService.kt",
   f"{lab}/main/{K}/QuoteApp.kt",
   f"{lab}/main/{K}/Provider.kt"
  ],
  "run": "./gradlew :quotes:test --tests 'workbench.quotes.l03.*'",
  "steps": [
   "Run the tests. All 13 fail. The `l03` package already holds lessons 1 and 2's solutions; `Provider` now has `idempotent`, and `QuoteApp.kt` wires the server, the service and the shutdown order.",
   "Write `GuardedProvider.quote` (points 1 to 3 of its KDoc): a `Semaphore` field, a permit around every single call, one call for a provider that isn't idempotent, `retrying` for the rest, and `hedged` around each attempt when `hedgeAfter` is set.",
   "Add the jitter to `retrying`: one line that computes the factor, and the `delay` that uses it.",
   "Write `hedged` as its KDoc describes. The bulkhead, retry and hedge tests should pass now.",
   "In `QuoteService`, add the admission `Semaphore` and the `accepting` flag to `quote`, then write `shutdown`. Run the tests until all 13 pass, including the two over TCP, then run them twice more."
  ],
  "hints": [
   "If the bulkhead test sees more than 4 calls at once, the permit isn't around every call. If `the limit counts hedges too` sees 2, the hedge runs outside the permit: wrap the permit inside the function you pass to `hedged`.",
   "`select { first.onAwait { it }; second.onAwait { it } }` is in `kotlinx.coroutines.selects`. Without `coroutineContext.cancelChildren()` after it, `coroutineScope` waits for the slow call and the hedge test reads 1,000 ms instead of 130.",
   "`Semaphore.tryAcquire()` never suspends, so `quote` can call it on the event loop. Release in `whenComplete` on the returned future, so a request that is cancelled gives its permit back too.",
   "In `shutdown`, join a snapshot of the children inside `withTimeoutOrNull(grace)`, count what is still running, then `cancelAndJoin()` the scope's job."
  ],
  "done_when": "All 13 tests in `UnderLoadTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the hedge from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write `suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T`: start the call, and if it hasn't answered after `after`, start one more, return the first answer and stop the other. Which line, if you leave it out, makes the hedge useless, and why?",
  "answer": {"lang": "kotlin", "src": DRILL_K, "alt": {"lang": "java", "src": DRILL_J}}
 },
 "recap": [
  "Give each provider its own bulkhead, a `Semaphore` sized from its contract by Little's law, with a permit around every single call, hedges included.",
  "Retry only idempotent calls, only errors a later attempt can fix, with jitter and inside the deadline. A firm quote, like an authorization, is called once.",
  "Hedge the provider whose tail hurts, after about its p95 latency, and cancel the loser. In the demo p99 fell from 600 to 120 ms for 5% more calls.",
  "Shed at the door with `tryAcquire`: a request that can't make the deadline gets `ERR busy` in a millisecond instead of failing after 300 ms in a queue.",
  "Shut down in order: stop accepting, stop admitting, drain within a grace period, `cancelAndJoin` the rest, then close connections and loops. No coroutine outlives the service.",
  "Event loop or virtual threads, the limits stay. Switch to virtual threads when the provider clients only block or the team writes plain Java; keep the event loop for huge connection counts, protocol control and non-blocking clients."
 ],
 "quiz": [
  {
   "q": "In `hedged`, the first call is still running at 80 ms, so a second starts, and `select` returns the second call's answer at 110 ms. The author forgot `cancelChildren()`. When does `hedged` return?",
   "options": [
    "At 110 ms: `select` cancels the clause that lost",
    "When the slow first call finishes, because `coroutineScope` waits for every child",
    "At 110 ms, and the slow call keeps running in the background",
    "Never: the two calls deadlock on the permit"
   ],
   "answer": 1,
   "why": "`select` only picks the first clause to complete; stopping the losers is your job. The first call is still a child of the `coroutineScope`, and a scope returns only after all its children are done, so `hedged` returns when the slow call ends, which undoes the hedge. Nothing runs in the background, because the scope is structured.",
   "from": "co-09"
  },
  {
   "q": "With `Backoff(retries = 2, first = 50 ms, jitter = 0.5)`, or Reactor's `Retry.backoff(2, Duration.ofMillis(50))`, a call fails every time with `IOException`. How many calls does the provider see?",
   "options": [
    "2",
    "It depends on the jitter",
    "3",
    "4"
   ],
   "answer": 2,
   "why": "Two retries after the first attempt: three calls, with waits of about 50 and 100 ms between them. Jitter moves when the retries happen, not how many there are. Count them when you size the bulkhead, because Little's law applies to every call.",
   "from": "rx-05"
  },
  {
   "q": "A provider's contract allows 10 calls at once, and it answers in 50 ms. How many calls per second can it serve, and how many permits should its bulkhead have?",
   "options": [
    "200 per second, and 10 permits",
    "500 per second, and 50 permits",
    "10 per second, and 10 permits",
    "200 per second, and 200 permits"
   ],
   "answer": 0,
   "why": "Little's law: in flight = rate x time, so 10 = rate x 0.05 s gives 200 calls a second. The bulkhead holds the contract's 10. More permits don't add capacity; they move the queue to the provider's side, where it slows everyone and you can't see it.",
   "from": "vt-03"
  },
  {
   "q": "After `shutdown`, the service must have no coroutines left. Which step guarantees it?",
   "options": [
    "`scope.cancel()`, which returns as soon as the cancel is sent",
    "`job.cancelAndJoin()`, which returns only after every child has finished",
    "`withTimeoutOrNull(grace)` around the drain",
    "Setting `accepting = false` before anything else"
   ],
   "answer": 1,
   "why": "`cancel()` only requests cancellation and returns while children may still be running their `finally` blocks; `cancelAndJoin()` waits until they have stopped. The grace period lets well-behaved requests finish, and `accepting = false` stops new ones from arriving, but neither stops what is already running.",
   "from": "co-03"
  },
  {
   "q": "The providers only ship blocking Java SDKs, the service holds about 2,000 connections, and the team writes Java. A reviewer suggests one virtual thread per connection. What is the strongest argument for switching?",
   "options": [
    "Virtual threads make each request faster",
    "Virtual threads remove the need for per-provider limits",
    "Netty can't serve 2,000 connections",
    "With blocking SDKs this design needs a blocking pool behind the coroutines anyway, while virtual threads run the same calls in plain code, and 2,000 connections are easy for them"
   ],
   "answer": 3,
   "why": "The model should follow where the waiting happens. Blocking SDKs put the waiting on threads, so the event loop buys little here and costs a second model. Virtual threads give scale, not speed, and they remove the pool, so the bulkheads must be written down explicitly. Netty handles far more than 2,000 connections.",
   "from": "io-08"
  }
 ],
 "flashcards": [
  {"front": "Where does a bulkhead's permit go?", "back": "Around each single call to the provider: not around the retry loop (a backoff wait shouldn't hold a permit), and a hedge takes a permit of its own."},
  {"front": "How do you size a provider's bulkhead?", "back": "From its contract's limit on concurrent calls. Little's law: permits / time per call = the most calls per second it can serve."},
  {"front": "Which calls may be retried or hedged?", "back": "Only idempotent ones, where a repeat does no harm. A firm quote that reserves liquidity, like a card authorization, is called once."},
  {"front": "Why add jitter to retry waits?", "back": "Clients that failed together would retry in the same millisecond. A factor between 0.5 and 1.5 spread 1,000 retries so that no millisecond had more than 18."},
  {"front": "When does a hedge start, and what does it cost?", "back": "After about the provider's p95 latency. It adds about 5% more calls; in the demo it cut p99 from 600 to 120 ms."},
  {"front": "Why shed with `tryAcquire` instead of queueing?", "back": "A request that can't make the deadline fails anyway. Shedding makes it fail in a millisecond with `ERR busy`, and nothing waits on the event loop."},
  {"front": "The quote service's shutdown order?", "back": "Stop accepting, stop admitting, drain within the grace period, `cancelAndJoin` the rest, then close the connections and the loops."}
 ],
 "terms": [
  {"term": "Bulkhead", "plain": "A limit on the calls in flight to one dependency, so that its limit can't sink the rest of the service."},
  {"term": "Idempotent call", "plain": "A call you can repeat without changing the outcome, such as reading a price."},
  {"term": "Jitter", "plain": "A random change to each retry wait, so clients that failed together don't retry together."},
  {"term": "Hedged request", "plain": "A second, identical request sent when the first is slower than usual; the first answer wins and the other is cancelled."},
  {"term": "Tail latency", "plain": "The slowest few percent of requests, such as p99: what the unluckiest users see."},
  {"term": "Load shedding", "plain": "Refusing work at the door, at once and with a clear error, when the service can't finish it in time."},
  {"term": "Graceful shutdown", "plain": "Stopping in order: no new work, let work in flight finish for a while, cancel the rest, then release resources."}
 ],
 "explain_back": {
  "prompt": "Design review. A sceptical reviewer says: \"This is too much machinery: Netty, coroutines, futures, semaphores, hedges. One virtual thread per connection with blocking provider clients would be simpler, and Netty buffers everything anyway.\" Defend your design: say what each guard protects against, what you would keep if you did switch to virtual threads, and when you would switch.",
  "answer": "Each piece answers a failure we can name. The event loop never waits, and auto-read with a cap of 16 per connection keeps one greedy client from filling our memory, because Netty's buffers have no limit of their own. The fan-out asks three providers under one deadline in a supervisor scope, so a failed or slow provider just drops out, and a stale cached price beats no answer. Cancelling the future on hang-up cancels every provider call through the job tree. Under load, each provider gets a bulkhead sized from its contract, so we never send Northbank more than its 10 calls; only idempotent providers are retried, with jitter so recoveries aren't hit by synchronized waves, and Fjord's firm quotes are called once. Northbank's slow tail gets a hedge after its p95, which cut p99 from 600 to 120 ms for 5% more calls. Admission sheds what we can't answer in 300 ms with an immediate ERR busy instead of a slow failure, and shutdown stops intake, drains, cancels and joins the rest, and then closes, so nothing leaks. If we switched to virtual threads I'd keep every limit: the bulkheads, the deadline, admission and the shutdown order, because virtual threads remove the pool and with it the only limit we never wrote down. I'd switch if the providers only had blocking SDKs, because then this design needs a blocking pool anyway, or if the team prefers plain Java and connections stay in the thousands. I'd stay on Netty for huge connection counts, for the protocol control, or when the provider clients are non-blocking and cancellation has to reach them."
 },
 "deeper": {
  "minutes": 10,
  "body": "What a production version of this service would add, roughly in the order it would hurt to miss them.\n\nMetrics. Per provider: latency histograms (the hedge time comes from the p95), permits in use, calls retried, hedges sent and won, errors by type. Per service: requests admitted, shed and served stale, and the age of stale quotes. Without them, every number in this track (the 10 permits, the 80 ms hedge, the 50 in flight) is a guess.\n\nA circuit breaker. Retries help with blips; they make a dead provider worse. A breaker counts recent failures and, past a threshold, stops calling the provider for a while, then lets a few trial calls through. It sits outside the retry loop, so an open breaker fails fast instead of retrying.\n\nA retry budget. Cap retries as a share of all calls, for example 10%. During a long outage the budget runs out and the service stops multiplying its own load.\n\nAdaptive limits. Fixed permits are right only for the load they were measured under. Adaptive concurrency limits change the permits from observed latency, the way TCP's congestion control finds a window: when latency rises, the limit shrinks before the provider falls over.\n\nDeadline propagation and context. Send the time left with each provider call so that the provider can give up too, and carry the trace and request ids across the Netty-to-coroutine edge (`asContextElement` or `MDCContext`, as \"Dispatchers and the coroutine context\" showed), so that a slow quote can be found in the logs.\n\nFair admission. One heavy client can still take most of the 50 slots. Per-client quotas at the door, on top of the global limit, keep a single caller from crowding out the rest.\n\nAn operations story for shutdown. Fail the readiness check before the drain starts, so that the load balancer stops sending, and keep the grace period shorter than the platform's termination grace, or the platform kills the process mid-drain."
 },
 "sources": [
  {"title": "Semaphore (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-semaphore/"},
  {"title": "Select expression (Kotlin docs)", "url": "https://kotlinlang.org/docs/select-expression.html"},
  {"title": "Cancellation and timeouts (Kotlin docs)", "url": "https://kotlinlang.org/docs/cancellation-and-timeouts.html"},
  {"title": "RetryBackoffSpec source: backoff formula and jitter (reactor-core 3.8.x)", "url": "https://raw.githubusercontent.com/reactor/reactor-core/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java"},
  {"title": "Netty 4.2 Migration Guide (Netty wiki)", "url": "https://raw.githubusercontent.com/wiki/netty/netty/Netty-4.2-Migration-Guide.md"}
 ]
}

out = ROOT / "content/lessons/cap2-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
