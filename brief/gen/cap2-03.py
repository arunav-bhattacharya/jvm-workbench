import json, pathlib, re
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/quotes/src"
J = "java/workbench/quotes/l03"
K = "kotlin/workbench/quotes/l03"
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
        "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l03.{name}Kt",
        "file": f"{lab}/demo/{K}/{name}.kt",
        "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{J}/{name}Java.java"),
                "run": f"./gradlew :quotes:demo -Pmain=workbench.quotes.l03.{name}Java",
                "file": f"{lab}/demo/{J}/{name}Java.java"},
    }


# ---- the figure: every guard in the final program ----
provs = [  # y, class, name, rule
    (40, "box-a", "northline", "bulkhead 10, retry, hedge at 80 ms"),
    (122, "box-ok", "eastgate", "bulkhead 40, retry"),
    (204, "box-b", "fjord", "bulkhead 5, bookings: called once"),
]
pp = []
for y, cls, name, rule in provs:
    pp.append(f'<rect class="{cls}" x="410" y="{y}" width="278" height="56" rx="8"/>')
    pp.append(f'<text class="t" x="549" y="{y + 23}" text-anchor="middle">{name}</text>')
    pp.append(f'<text class="t-s" x="549" y="{y + 43}" text-anchor="middle">{rule}</text>')
    pp.append(f'<line class="ln" x1="364" y1="150" x2="406" y2="{y + 28}" marker-end="url(#arr)"/>')
FIG = (
    '<svg viewBox="0 0 700 316" role="img" aria-label="The finished quote service: a request passes admission, '
    'which turns it away with ERR busy when the service is full, then BestQuote with its 300 ms deadline fans out to three '
    'guarded couriers: Northline with a bulkhead of 10, retries and a hedge, Eastgate with a bulkhead of 40 and retries, '
    'and Fjord with a bulkhead of 5, whose prices are bookings and are asked once. Shutdown stops accepting, stops admitting, '
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

    private suspend fun once(destination: String): Quote =
        permits.withPermit { delegate.quote(destination) }         // suspends while all permits are out
}"""
J_BULK = """// Java equivalent on virtual threads: java.util.concurrent.Semaphore, acquire before the try
private Quote once(String destination) throws IOException, InterruptedException {
    permits.acquire();                                             // blocks a cheap virtual thread
    try {
        return delegate.quote(destination);
    } finally {
        permits.release();
    }
}"""
K_GATE = """override suspend fun quote(destination: String): Quote {
    val once: suspend () -> Quote = { permits.withPermit { delegate.quote(destination) } }   // 1. a permit per call
    if (!delegate.idempotent) return once()                         // 2. a booking: exactly one call
    val attempt: suspend () -> Quote = if (hedgeAfter == null) once else ({ hedged(hedgeAfter, once) })
    return retrying(backoff, random, attempt)                       // 3. the rest may be asked again
}"""
J_GATE = """// Java equivalent with Reactor: the same decision before any retry operator is added
Mono<Quote> quote(String destination) {
    Mono<Quote> once = Mono.defer(() -> delegate.quote(destination));
    if (!delegate.idempotent()) return once;                       // a booking: exactly one call
    return once.retryWhen(Retry.backoff(2, Duration.ofMillis(50)).jitter(0.5)
            .filter(e -> e instanceof IOException));
}"""
K_JITTER = """val factor = 1 + backoff.jitter * (random.nextDouble() * 2 - 1)   // 0.5 .. 1.5 for jitter 0.5
delay(backoff.nominal(n) * factor)                                  // cancellable: the deadline still rules"""
J_JITTER = """// Java equivalent on a virtual thread: the same factor, and a sleep that an interrupt ends
double factor = 1 + jitter * (ThreadLocalRandom.current().nextDouble() * 2 - 1);
Thread.sleep((long) (nominal(n).toMillis() * factor));"""
K_HEDGE = """suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T = coroutineScope {
    val first = async { call() }                               // 1. the first call
    val early = withTimeoutOrNull(after) { first.await() }     // 2. stops the waiting, not the call
    if (early != null) return@coroutineScope early
    val second = async { call() }                              // 3. the hedge
    val winner = select { first.onAwait { it }; second.onAwait { it } }
    coroutineContext.cancelChildren()                          // 4. stop the loser
    winner
}"""
J_HEDGE = """// Java equivalent with Reactor: the delayed hedge is cancelled before it starts if the first call wins
Mono<Quote> hedged(Duration after, Mono<Quote> call) {
    return Mono.firstWithValue(call, Mono.delay(after).then(call));
}"""
K_ADMIT = """override fun quote(destination: String): CompletableFuture<Quote> {
    if (!accepting) return CompletableFuture.failedFuture(ShuttingDownException())
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(BusyException())   // never waits
    val reply = scope.future { best.quote(destination) }
    reply.whenComplete { _, _ -> admission.release() }         // however the request ends
    return reply
}"""
J_ADMIT = """// Java equivalent: the same door with a java.util.concurrent.Semaphore
public CompletableFuture<Quote> quote(String destination) {
    if (!accepting) return CompletableFuture.failedFuture(new ShuttingDownException());
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(new BusyException());
    CompletableFuture<Quote> reply = best(destination).toFuture();
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

OPENING = """Picture the post office on the last day before the holidays. The queue runs out of the door, and everyone wants a price at once. The three couriers behind the counter have limits of their own. Northline's contract allows ten questions at a time, and one of its answers in twenty is very slow. Eastgate sometimes says "try again later". And Fjord holds a seat on a van every time it's asked.

The easy trap is to let every customer in and hope. Each request then waits its full deadline for a courier that was never going to answer, and the service looks slow when the truth is that it's full.

Fan out with coroutines, inside a deadline asked the three couriers at once, under one deadline. In this lesson, we'll give each courier its own limit, repeat only the questions that are safe to repeat, send a second question when one is slow, turn customers away at the door with a clear word, and close at night without losing a coroutine. Then we'll ask whether one virtual thread per customer would have been simpler. Before we start, make a guess, and keep it in mind."""

S1 = fill("""Lesson 2's fan-out sends every request to every courier at once. With a thousand requests in flight, Northline sees a thousand calls at once, and its contract allows 10. Past that, it answers 429, the web's code for "too many requests", or it slows down for everyone.

The fix is a **bulkhead**, named after the walls inside a ship's hull that keep one flooded section from sinking the whole ship. Here, it's a limit on the calls in flight to one courier, so that one courier's limit can't become everybody's outage. Using virtual threads: one per task, limits with semaphores pictured it as twenty tokens by the grill: a pan goes on only with a token in hand, and a cook without one waits. A **semaphore** is that box of tokens, and each token is a **permit**.

In the lab, the guards for one courier live in `GuardedProvider`, a wrapper that applies them and then passes each call on to the real courier. Its bulkhead is a `Semaphore` from `kotlinx.coroutines.sync`:

@@BULK@@

`withPermit` takes a permit, runs the call and gives the permit back, however the call ends. While no permit is free, it suspends. It holds no thread, and the wait is cancellable, so lesson 2's deadline still applies: a call that waits too long for a permit is cancelled with the rest and counts as no answer. The Java twin does the same with the JDK's `Semaphore` on a virtual thread, where waiting is cheap too.

How many permits? Sizing a pool: CPU-bound, IO-bound and Little's law gave the rule: the calls in flight equal the arrival rate times the time per call. If Northline allows 10 calls at once and answers in 50 ms, it serves at most 10 / 0.05 = 200 calls a second. More permits add no speed. They only move the queue to Northline's side, where you can't see it. So take the number from each courier's contract, and give each courier its own: Eastgate allows 40 and Fjord 5, as the figure shows.

This section's demo sends 40 requests at once to a courier that answers in 50 ms. With no limit, the courier sees all 40 at once, and every answer arrives after 50 ms. With a limit of 4, it never sees more than 4, and the 40 answers take 10 rounds of 50 ms, 500 ms in all. The limit didn't make anything faster. It made the courier's load a number we chose.

Two placement rules matter. The permit goes around each single call, not around a whole retry loop: a call that waits out its pause before a retry shouldn't hold a permit meanwhile, and a hedge, the second call of section 3, needs a permit of its own. And the bulkhead lives in the courier's wrapper, not around the fan-out. A limit on requests can't protect a courier, because each request makes three calls.

**A courier's limit is a number in its contract. Write it into a semaphore, around every single call.**

Now each courier sees no more than its share. Some of those calls still fail, and the question is whether to ask again.""", BULK=pair_kj(K_BULK, J_BULK))

S2 = fill("""A **transient failure**, one that goes away by itself, often succeeds on a second try: a 503, the web's code for "busy, try again later", or a connection that broke halfway. But a **retry**, asking again after a failure, is a second request, and the courier can't tell it from a new one.

That matters more for some couriers than others. Northline and Eastgate only look up a price, so asking twice changes nothing. Fjord's price is a booking: each call holds a place on one of its vans for two minutes and counts against our daily allowance of calls. Ask Fjord twice, and it holds two places. A call is **idempotent** when repeating it does no harm, like reading a price. So the decision belongs to the courier, as `Provider.idempotent`, which is false unless the courier says otherwise:

@@GATE@@

Let's read it in order. Every single call holds a permit (1). A courier that isn't idempotent gets exactly one call (2). The rest go through `retrying`, with a hedge around each attempt when one is set (3).

`retrying` is the retry loop with growing waits from Shared state and testing coroutines, a **backoff**, with one change: jitter. When Northline has a bad moment, every request in flight fails in the same millisecond. Without jitter, they all come back one backoff later, punctual to the millisecond, and hit a courier that is still getting back on its feet. **Jitter** multiplies each wait by a random factor, here between 0.5 and 1.5, which spreads the retries out. Reactor's `Retry.backoff` does the same by default, as Errors, retries and timeouts showed:

@@JITTER@@

It's the broken oven from that lesson, with a crowd of packers. If every packer asks for the tray to be baked again at the same second, the oven that has just been repaired breaks again.

This section's demo has 1,000 customers that failed together and retry after a nominal 100 ms. Without jitter, all 1,000 retries land in one millisecond. With a jitter of 0.5, they spread over 50 to 150 ms, and no millisecond gets more than 18.

Three more rules keep retries honest. Retry only errors that a later attempt might fix: here an `IOException`, never an unknown destination. Keep every wait cancellable, so the deadline cuts off retries that can't finish in time; a retry after the deadline is work nobody will read. And count the calls. Two retries means up to three calls per request, and Little's law counts every one of them.

**A retry is a second request. Send it only when repeating is harmless, and never all at the same moment.**

Retries help when a call fails. Some calls don't fail at all. They're just slow.""", GATE=pair_kj(K_GATE, J_GATE), JITTER=pair_kj(K_JITTER, J_JITTER))

S3 = fill("""Northline answers in 40 ms most of the time, but one call in twenty takes 600 ms. Nothing failed, so a retry doesn't help. Northline is simply lost in thought now and then.

To talk about slow calls, we need one more word. A **percentile** says how slow the slow ones are: p50 is the time half the calls beat, and p99 is the time 99 calls in 100 beat. The slowest few calls are the **tail**, and **tail latency** is what the unluckiest customers see. Northline's p50 is 40 ms. Its p99 is 600 ms.

A **hedge** cuts the tail. If the first call hasn't answered by the time 95 calls in 100 would have (its p95), send one more identical call and take whichever answers first. It's the cook texting a second branch of the same shop when the first hasn't replied by the time shops usually do:

@@HEDGE@@

Let's read it in order. We start the first call (1). `withTimeoutOrNull(after) { first.await() }` stops waiting at the hedge time (2), and it doesn't cancel `first`, which is a child of the `coroutineScope`, not of the timeout. If nothing came back, we start the hedge (3). `select` takes whichever deferred completes first, the way Channels, select and pipelines took whichever answer came first. Then `cancelChildren()` stops the loser (4). Forget that line, and `coroutineScope` waits for the slow call anyway, which undoes the hedge.

This section's demo asks Northline for 200 prices, one after another, first without a hedge and then with a hedge after 80 ms. On virtual time it printed:

```text
no hedge        p50  40 ms   p99 600 ms   max 600 ms   calls to Northline: 200
hedge at 80 ms  p50  40 ms   p99 120 ms   max 120 ms   calls to Northline: 210
```

The p99 fell from 600 ms to 120 ms: 80 ms of waiting, plus 40 ms for the hedge. It cost 10 extra calls, 5% more, because only the slow 5% got a hedge.

That cost decides where hedges go. Hedge only an idempotent courier, because a hedge is a duplicate request: a hedged Fjord would book two vans. Hedge only the courier whose tail hurts, here Northline, at a time taken from its measured latency. And make the hedge take its own permit from the bulkhead. When Northline is saturated, a hedge would only add to the queue that made it slow, so under full load the hedge waits for a permit, and the first call usually wins. The lab has a test for exactly that: with one permit, the hedge never runs alongside the first call.

**A hedge is a duplicate request. Spend it on the slow tail, and only where a duplicate is harmless.**

Bulkheads, retries and hedges look after the couriers and the customer's wait. Nothing yet protects the service itself from more customers than it can answer.""", HEDGE=pair_kj(K_HEDGE, J_HEDGE))

S4 = fill("""Northline takes 10 calls at a time, at 50 ms each, so within a 300 ms deadline it can answer about 60 requests. A burst of 500 then leaves hundreds waiting for a permit, until they fail at the deadline anyway. This section's demo measured it: 50 live answers, 450 misses, and 135,000 ms of waiting, summed over the requests that missed, that produced nothing.

Customers don't read slips. Like the oven thermometer in Backpressure in practice, they arrive whenever they like, so someone has to choose what to lose. Buffering: buffer, conflate, collectLatest and fusion asked the same question at the shelf in the hatch: when the shelf is full, either the cook waits or a dumpling goes in the bin. Waiting is the queue we just measured. The bin is closer to the answer, with one change: the customer hears about it. **Load shedding** turns away work the service can't finish in time, at once and with a clear word. `QuoteService` admits at most `maxInFlight` requests, and the next one gets a failed future straight away, which lesson 1's handler writes as `7 ERR busy`:

@@ADMIT@@

With 50 admitted, the same burst got the same 50 live answers, and the other 450 customers heard `busy` within a millisecond, early enough to try another post office. `tryAcquire` takes a permit if one is free and never waits, so the event loop that calls `quote` never waits either. The permit comes back in `whenComplete`, however the request ends, including a cancel after a hang-up. Here the picture breaks in our favour: a dumpling in the bin is gone for good, while a customer who hears "busy" can ask again elsewhere.

**A request that can't make its deadline fails either way. Fail it at the door, in a millisecond.**

Shutdown uses the same pieces. Pools in production: names, errors, context, shutdown closed the kitchen at night in a fixed order, and the post office closes the same way. Lock the front door, stop taking new questions, let the customers at the counter finish, send the rest away, then turn off the lights:

@@SHUT@@

That order has a name, a **graceful shutdown**: no new work, a **grace period** for the work in flight to finish, then cancel the rest and release everything. First, the server stops accepting connections (1). Then the service stops admitting requests, which now get `ERR shutting down` (2). The requests in flight get the grace period (3). What is left is cancelled, and `cancelAndJoin()` waits until those coroutines have finished their cleanup, so that no coroutine outlives the service (4). Finally, the server closes the connections and stops its loops (5). Lesson 1's `ChannelGroup` pays off here: each connection is closed on its own loop, behind the reply that the drain just let through.

That's the whole service. Before we call it done, a reviewer has a fair question.""", ADMIT=pair_kj(K_ADMIT, J_ADMIT), SHUT=pair_kj(K_SHUT, J_SHUT))

S5 = """Here is the finished design next to the question every reviewer asks about it: wouldn't one virtual thread per connection, with plain blocking calls to the couriers, be simpler? A **virtual thread** is a thread the JDK makes so cheap that a program can run thousands of them, and **blocking** means a call that holds its thread until the answer comes.

Blocking IO, threads and the C10K problem offered the post office two ways out of the crowd: fewer clerks, or cheaper clerks. This service took the first way: a few clerks, each watching a row of boxes, who never wait. Virtual threads take the second: a clerk for every customer, so cheap that most of them can stand and wait. Here are the two side by side:

| Concern | This service | One virtual thread per connection |
|---|---|---|
| idle connections | a few loop threads hold thousands | one parked virtual thread each, a few KB |
| waiting for couriers | suspended coroutines | blocked virtual threads |
| deadline and cancel | structured: the cancel reaches every courier call | interrupts, which some blocking clients ignore |
| limits per courier | a `Semaphore` per courier | a `Semaphore` per courier |
| framing and backpressure | Netty's decoders and auto-read | your own read loop; TCP does the pacing |
| code shape | futures at the Java edge, coroutines inside | plain blocking Java |

Virtual threads make the right-hand column cheap (The thread-per-request wall), and for many services they are the better choice. Switch when the couriers only ship blocking clients, such as JDBC, Java's standard way to talk to a database. This design would then need a pool of blocking threads behind the coroutines, and you'd pay for two models. Switch, too, when the team writes Java and connections number in the thousands. Stay on the event loop when the service already lives on Netty or a framework built on it, such as Vert.x or Quarkus; when connections number in the hundreds of thousands; when you need the control over the protocol that auto-read and decoders give you; or when the courier clients are non-blocking and a cancel must reach them.

Either way, the limits stay. Bulkheads, deadlines, admission and an ordered shutdown appear in both columns. Moving to virtual threads removes the pool, and with it the one limit nobody wrote down, as Moving a blocking service to virtual threads found. The question that picks the model is where the waiting happens, as Zero-copy, epoll, io_uring, and choosing a server model put it. Here it happens in three courier calls per request, under a deadline, and both models can wait well.

**Pick the model by where the waiting happens. Keep the limits whichever you pick.**"""

ASIDE = {
    "title": "Where do these guards live in a real service?",
    "body": "Often in a library rather than in hand-written code. Resilience4j, for example, is a Java library with a bulkhead, a retry with backoff, a time limit and a circuit breaker, a switch that stops calling a courier that keeps failing. Whichever you use, let one layer own the retries. Two retries in the courier's own client, two in a library and two in your code turn one call into 3 x 3 x 3 = 27 calls during an outage. And when a platform stops your program, tell it to send no more customers before the drain starts, so the shutdown order holds."
}

# ---- compare: the guards with coroutines and on virtual threads ----
sol = read(f"{lab}/solution/{K}/Resilience.kt")
K_RETRY_SRC = sol[sol.index("suspend fun <T> retrying"):sol.index("/**", sol.index("suspend fun <T> retrying"))].rstrip()
K_GUARD_SRC = sol[sol.index("class GuardedProvider("):].rstrip()
COMPARE_K = K_RETRY_SRC + "\n\n" + K_GUARD_SRC + "\n"
COMPARE_J = """// Java on virtual threads: the same guards around a blocking courier client
final class GuardedProvider {
    private final BlockingProvider delegate;
    private final Semaphore permits;
    private final Backoff backoff;

    GuardedProvider(BlockingProvider delegate, int maxConcurrent, Backoff backoff) {
        this.delegate = delegate;
        this.permits = new Semaphore(maxConcurrent);
        this.backoff = backoff;
    }

    Quote quote(String destination) throws IOException, InterruptedException {
        if (!delegate.idempotent()) return once(destination);        // 2. never repeat a booking
        for (int n = 1; ; n++) {
            try {
                return once(destination);
            } catch (IOException e) {
                if (n > backoff.retries()) throw e;                   // out of retries
                double factor = 1 + backoff.jitter() * (ThreadLocalRandom.current().nextDouble() * 2 - 1);
                Thread.sleep((long) (backoff.nominal(n).toMillis() * factor));   // an interrupt ends it
            }
        }
    }

    private Quote once(String destination) throws IOException, InterruptedException {
        permits.acquire();                                           // 1. every call holds a permit
        try {
            return delegate.quote(destination);
        } finally {
            permits.release();
        }
    }
}"""

W1K = """override fun quote(destination: String): CompletableFuture<Quote> {
    if (!admission.tryAcquire()) return CompletableFuture.failedFuture(BusyException())   // 49 -> 50: admitted
    val reply = scope.future { best.quote(destination) }    // 300 ms deadline per courier call
    reply.whenComplete { _, _ -> admission.release() }
    return reply
}"""
W1J = """// Java equivalent: the same admission check in front of a Reactor fan-out
if (!admission.tryAcquire()) return CompletableFuture.failedFuture(new BusyException());   // 49 -> 50: admitted
CompletableFuture<Quote> reply = best(destination).toFuture();       // 300 ms deadline per courier call
reply.whenComplete((q, e) -> admission.release());
return reply;"""
W2 = """  0 ms  northline  permit 1 of 10, call 1 starts
 80 ms  northline  no answer yet: the hedge takes permit 2 of 10, call 2 starts
120 ms  northline  call 2 answers 12.45; call 1 is cancelled, both permits are back
  0 ms  fjord      permit 1 of 5, one call (a booking: never retried, never hedged)
200 ms  fjord      answers 12.43"""
W3 = """  0 ms  eastgate   permit, call 1
 30 ms  eastgate   IOException: 503; permit back; wait 50 ms x 1.3 = 65 ms
 95 ms  eastgate   permit, call 2
145 ms  eastgate   answers 12.41
200 ms  BestQuote  all three answered: eastgate 12.41 wins; admission permit back (50 -> 49)"""

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

CLOSING = """We started at the post office on its busiest day, with a crowd at the door and three couriers with limits of their own. Now each courier gets its share of calls, only harmless questions are asked twice, a slow answer gets one second chance, and a customer we can't serve in time hears "busy" at once.

That's Part 2 in one program: the bakery's slip became auto-read, the home cook texted the couriers under a kitchen timer, the shelf decided what to lose, and the clerk never picked up the phone.

Now search your own code for a retry around a call that books or charges something.

Next, we'll start Part 3 with Generics from zero, in a fruit shop's storeroom. Our service kept promises about time. Can a label on a box make the compiler keep promises about types?"""

L = {
 "id": "cap2-03",
 "title": "Hold up under load",
 "minutes": 40,
 "goal": "By the end you can give each courier a bulkhead sized with Little's law, retry only idempotent calls with backoff and jitter, hedge the slow tail of one courier, turn work away at the door with a clear error, shut the service down in order without leaving a coroutine behind, and defend the whole design against one virtual thread per connection.",
 "opening": OPENING,
 "warmup": {
  "q": "The quote service answers within 300 ms. Northline takes 10 calls at a time and needs 50 ms per call. A burst of 500 requests arrives at once, and the service lets them all queue. About how many get a live Northline price?",
  "options": [
   "All 500, each a little later than usual",
   "About 50 to 60: ten at a time, and six rounds of 50 ms fit in 300 ms",
   "About 10: only the first round",
   "None: the burst knocks Northline over"
  ],
  "answer": 1,
  "why": "Little's law: 10 calls at once at 50 ms each is at most 200 calls a second, so 300 ms holds about 60. This lesson's demo got 50, because the sixth round ends exactly at the deadline. The other 450 wait for a permit until their deadline and then fail. Queueing them didn't get them a price; it made them slow failures. Section 4 turns them into fast ones."
 },
 "sections": [
  {
   "h": "A bulkhead for each courier, sized by Little's law",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The finished service: admission at the door, one deadline for the fan-out, and a different set of guards for each courier."},
   "try": {
    "title": "Forty requests, one courier, two limits",
    "minutes": 3,
    "steps": [
     "Open `BulkheadDemo.kt` (virtual time) or `BulkheadDemoJava.java` (virtual threads, real time). Forty requests call a courier that answers in 50 ms.",
     "Predict the most calls in flight at once, and the time until all forty are answered, with no limit and with a limit of 4.",
     "Run it. Then change the limit to 8 and predict again from Little's law."
    ],
    "code": demo("BulkheadDemo"),
    "expect": "No limit: 40 calls at once, all answered after 50 ms. Limit 4: 4 at once, and 40 / 4 = 10 rounds of 50 ms, 500 ms. With a limit of 8, it is 5 rounds, 250 ms. The Java twin prints the same peaks in real time, with a few extra milliseconds of scheduling (81 and 511 ms in one run on a busy machine). The limit didn't make anything faster; it made the courier's load a number you chose."
   },
   "refs": [
    {"title": "Semaphore (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-semaphore/", "kind": "docs"}
   ]
  },
  {
   "h": "Retry only what is safe to repeat, and spread the retries out",
   "body": S2,
   "try": {
    "title": "A thousand retries in one millisecond",
    "minutes": 3,
    "steps": [
     "Open `RetryJitterDemo.kt` (or the Java twin, which computes the same waits without sleeping). A thousand customers failed together at 0 ms and retry after a nominal 100 ms.",
     "Predict how the retries spread over 25 ms buckets with no jitter and with a jitter of 0.5, and the most retries in any single millisecond.",
     "Run it. Then set the jitter to 0.1 and predict the busiest millisecond."
    ],
    "code": demo("RetryJitterDemo"),
    "expect": "No jitter: all 1,000 retries in the 100 to 124 ms bucket, and all of them in the same millisecond. Jitter 0.5: about 250 in each bucket from 50 to 149 ms (a few land at exactly 150 after rounding up), and the busiest millisecond has 18 (17 in the Java twin, whose random numbers differ). With 0.1, the retries squeeze into 90 to 110 ms, and the busiest millisecond gets about three times as many: less jitter, less spread."
   },
   "refs": [
    {"title": "Retry and RetryBackoffSpec source (reactor-core 3.8.x)", "url": "https://raw.githubusercontent.com/reactor/reactor-core/3.8.x/reactor-core/src/main/java/reactor/util/retry/RetryBackoffSpec.java", "kind": "docs"}
   ]
  },
  {
   "h": "Hedge the slow tail of one courier",
   "body": S3,
   "try": {
    "title": "Cut Northline's tail",
    "minutes": 4,
    "steps": [
     "Open `HedgeDemo.kt`. Northline answers in 40 ms, except every 20th call, which takes 600 ms. The demo asks for 200 prices without a hedge, then with a hedge after 80 ms.",
     "Predict p50, p99, the slowest request and the number of calls for both runs.",
     "Run it. Then set the hedge to 30 ms, below Northline's normal time, and predict the number of calls."
    ],
    "code": demo("HedgeDemo"),
    "expect": "No hedge: p50 40 ms, p99 and max 600 ms, 200 calls. Hedge at 80 ms: p50 still 40, p99 and max 120 ms (80 ms of waiting plus a 40 ms hedge), 210 calls. With the hedge at 30 ms, every request is hedged: 400 calls, twice the load, for a p99 that the 80 ms hedge already got down to 120. A hedge time below the normal time duplicates every request. The Java twin uses Reactor's `Mono.firstWithValue` and prints about the same numbers in real time, give or take the scheduling delays of a busy machine."
   },
   "refs": [
    {"title": "select (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.selects/select.html", "kind": "docs"}
   ]
  },
  {
   "h": "Turn work away at the door, then close in order",
   "body": S4,
   "try": {
    "title": "Queue the burst, or turn it away",
    "minutes": 4,
    "steps": [
     "Open `ShedDemo.kt`. A burst of 500 requests meets a courier that takes 10 calls at a time, 50 ms each, under a 300 ms deadline.",
     "Predict the live answers, the misses, the requests turned away as busy, and the time spent waiting for nothing, for both runs.",
     "Run it. Then admit 100 instead of 50 and predict the misses again."
    ],
    "code": demo("ShedDemo"),
    "expect": "Queue them all: 50 live answers, 450 misses, and 135,000 ms spent waiting by requests that got nothing. Admit 50: the same 50 live answers, 0 misses, 450 turned away at once, and no wasted waiting. Admitting 100 gives the same 50 live answers, 50 misses and 15,000 ms of wasted waiting: past what the courier can serve in 300 ms, a bigger door only buys slow failures. The Java twin does the same with virtual threads in real time, so its waiting total drifts a little (139,688 ms in one run here)."
   },
   "refs": [
    {"title": "cancelAndJoin (kotlinx.coroutines API, from the Job documentation)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/cancel-and-join.html", "kind": "docs"}
   ]
  },
  {
   "h": "Design review: would one virtual thread per connection be simpler?",
   "body": S5,
   "aside": ASIDE
  }
 ],
 "compare": {
  "title": "The guards around a courier with coroutines and on virtual threads",
  "java": {"title": "GuardedProvider.java (virtual threads)", "src": COMPARE_J},
  "kotlin": {"title": "Resilience.kt", "src": COMPARE_K},
  "note": "The rules are the same in both: a permit around every single call, one call for a courier that isn't idempotent, and retries with jitter for `IOException` only. What differs is what waiting and stopping cost. In Kotlin, `withPermit` and `delay` suspend, so a thousand requests waiting for a permit or a backoff hold no threads, and a cancel (the deadline or a hang-up) reaches them at once through the job tree. On virtual threads, `acquire` and `Thread.sleep` block, which is cheap too, and a cancel is an interrupt: it reaches the sleep and the semaphore, but it reaches the courier call only if its client responds to interrupts. The Java version leaves the hedge out. On threads, a hedge takes an `ExecutorCompletionService`, or JDK 25's `StructuredTaskScope`, still a preview API there (Structured concurrency and scoped values), and the loser is stopped by an interrupt, which again works only if its client listens. Java code that can block on a virtual thread is shorter to read. Kotlin code gets the hedge and the deadline from the library."
 },
 "worked": {
  "title": "Trace one request through every guard on a bad afternoon",
  "steps": [
   {"say": "The scene: 49 requests are in flight (the limit is 50), Northline's next call is one of its slow ones, and Eastgate answers 503 now and then. A request for Lisbon arrives. It takes the last admission permit, so the next request will hear `ERR busy`.",
    "code": W1K, "lang": "kotlin", "alt_code": W1J, "alt_lang": "java"},
   {"say": "`BestQuote` starts the three courier calls at 0 ms, each under the 300 ms deadline. Northline's first call is slow, so at 80 ms the hedge starts, with a second permit. Fjord's price is a booking, so it gets exactly one call and no hedge.",
    "code": W2, "lang": "text"},
   {"say": "Eastgate fails at 30 ms with an `IOException`. Its permit goes back during the pause, and the jittered wait (65 ms here) puts the retry at 95 ms. By 200 ms every courier has answered, so `BestQuote` doesn't need the deadline at all this time.",
    "code": W3, "lang": "text"},
   {"say": "Self-check: run the same afternoon, but the customer hangs up at 100 ms. Which calls are running at that moment, what stops them, and when does the admission count drop back to 49? (Four calls are running: Northline's slow first call and its hedge, Eastgate's retry and Fjord's one call. Lesson 1's `channelInactive` cancels the future, `scope.future` cancels the request coroutine, and the cancel reaches all four, the hedge included. The future completes at once, so `whenComplete` gives the admission permit back at 100 ms.)",
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
   "Write `GuardedProvider.quote` (points 1 to 3 of its KDoc): a `Semaphore` field, a permit around every single call, one call for a courier that isn't idempotent, `retrying` for the rest, and `hedged` around each attempt when `hedgeAfter` is set.",
   "Add the jitter to `retrying`: one line that computes the factor, and the `delay` that uses it.",
   "Write `hedged` as its KDoc describes. The bulkhead, retry and hedge tests should pass now.",
   "In `QuoteService`, add the admission `Semaphore` and the `accepting` flag to `quote`, then write `shutdown`. Run the tests until all 13 pass, including the two over TCP, then run them twice more."
  ],
  "hints": [
   "If the bulkhead test sees more than 4 calls at once, the permit isn't around every call. If `the limit counts hedges too` sees 2, the hedge runs outside the permit: wrap the permit inside the function you pass to `hedged`.",
   "`select { first.onAwait { it }; second.onAwait { it } }` is in `kotlinx.coroutines.selects`. Without `coroutineContext.cancelChildren()` after it, `coroutineScope` waits for the slow call, and the hedge test reads 1,000 ms instead of 130.",
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
  "Give each courier its own bulkhead, a `Semaphore` sized from its contract by Little's law, with a permit around every single call, hedges included.",
  "Retry only idempotent calls, only errors a later attempt can fix, with jitter and inside the deadline. A price that is really a booking, like Fjord's, is asked for once.",
  "Hedge the courier whose tail hurts, after about its p95, and cancel the loser. In the demo, p99 fell from 600 to 120 ms for 5% more calls.",
  "Turn work away at the door with `tryAcquire`: a request that can't make the deadline gets `ERR busy` in a millisecond instead of failing after 300 ms in a queue. Then shut down in order: stop accepting, stop admitting, drain, `cancelAndJoin` the rest, close.",
  "Event loop or virtual threads, the limits stay. Switch to virtual threads when the courier clients only block or the team writes plain Java; keep the event loop for huge numbers of connections, control over the protocol and non-blocking clients.",
  "Where this design stops: fixed limits are right only for the load they were measured under, and retries make a courier that is down worse. Circuit breakers, retry budgets and adaptive limits come next (Go deeper)."
 ],
 "closing": CLOSING,
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
   "q": "With `Backoff(retries = 2, first = 50 ms, jitter = 0.5)`, or Reactor's `Retry.backoff(2, Duration.ofMillis(50))`, a call fails every time with `IOException`. How many calls does the courier see?",
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
   "q": "A courier's contract allows 10 calls at once, and it answers in 50 ms. How many calls per second can it serve, and how many permits should its bulkhead have?",
   "options": [
    "200 per second, and 10 permits",
    "500 per second, and 50 permits",
    "10 per second, and 10 permits",
    "200 per second, and 200 permits"
   ],
   "answer": 0,
   "why": "Little's law: in flight = rate x time, so 10 = rate x 0.05 s gives 200 calls a second. The bulkhead holds the contract's 10. More permits don't add capacity; they move the queue to the courier's side, where it slows everyone and you can't see it.",
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
   "why": "`cancel()` only asks for cancellation and returns while children may still be running their `finally` blocks; `cancelAndJoin()` waits until they have stopped. The grace period lets well-behaved requests finish, and `accepting = false` stops new ones from arriving, but neither stops what is already running.",
   "from": "co-03"
  },
  {
   "q": "The couriers only ship blocking Java clients, the service holds about 2,000 connections, and the team writes Java. A reviewer suggests one virtual thread per connection. What is the strongest argument for switching?",
   "options": [
    "Virtual threads make each request faster",
    "Virtual threads remove the need for limits per courier",
    "Netty can't serve 2,000 connections",
    "With blocking clients, this design needs a pool of blocking threads behind the coroutines anyway, while virtual threads run the same calls in plain code, and 2,000 connections are easy for them"
   ],
   "answer": 3,
   "why": "The model should follow where the waiting happens. Blocking clients put the waiting on threads, so the event loop buys little here and costs a second model. Virtual threads give scale, not speed, and they remove the pool, so the bulkheads must be written down. Netty handles far more than 2,000 connections.",
   "from": "io-08"
  }
 ],
 "flashcards": [
  {"front": "Where does a bulkhead's permit go?", "back": "Around each single call to the courier: not around the retry loop (a pause before a retry shouldn't hold a permit), and a hedge takes a permit of its own."},
  {"front": "How do you size a courier's bulkhead?", "back": "From its contract's limit on calls at once. Little's law: permits / time per call = the most calls per second it can serve."},
  {"front": "Which calls may be retried or hedged?", "back": "Only idempotent ones, where a repeat does no harm. A price that is really a booking is asked for once."},
  {"front": "Why add jitter to retry waits?", "back": "Clients that failed together would retry in the same millisecond. A factor between 0.5 and 1.5 spread 1,000 retries so that no millisecond had more than 18."},
  {"front": "When does a hedge start, and what does it cost?", "back": "After about the courier's p95 time. It adds about 5% more calls; in the demo it cut p99 from 600 to 120 ms."},
  {"front": "Why turn work away with `tryAcquire` instead of queueing it?", "back": "A request that can't make the deadline fails anyway. Shedding makes it fail in a millisecond with `ERR busy`, and nothing waits on the event loop."},
  {"front": "The quote service's shutdown order?", "back": "Stop accepting, stop admitting, drain within the grace period, `cancelAndJoin` the rest, then close the connections and the loops."}
 ],
 "terms": [
  {"term": "Bulkhead", "plain": "A limit on the calls in flight to one dependency, so that its limit can't sink the rest of the service."},
  {"term": "Semaphore", "plain": "A box of permits: a call takes one before it starts and gives it back when it ends, and waits while the box is empty."},
  {"term": "Idempotent call", "plain": "A call you can repeat without changing the outcome, such as reading a price."},
  {"term": "Jitter", "plain": "A random change to each retry wait, so clients that failed together don't retry together."},
  {"term": "Hedged request", "plain": "A second, identical request sent when the first is slower than usual; the first answer wins and the other is cancelled."},
  {"term": "Tail latency", "plain": "The time of the slowest few percent of requests, such as p99: what the unluckiest customers see."},
  {"term": "Load shedding", "plain": "Turning work away at the door, at once and with a clear error, when the service can't finish it in time."},
  {"term": "Graceful shutdown", "plain": "Stopping in order: no new work, a grace period for the work in flight, then cancel the rest and release resources."}
 ],
 "explain_back": {
  "prompt": "Design review. A doubtful reviewer says: \"This is too much machinery: Netty, coroutines, futures, semaphores, hedges. One virtual thread per connection with blocking courier clients would be simpler, and Netty buffers everything anyway.\" Defend your design: say what each guard protects against, what you would keep if you did switch to virtual threads, and when you would switch.",
  "answer": "Each piece answers a failure we can name. The event loop never waits, and auto-read with a cap of 16 per connection keeps one greedy client from filling our memory, because Netty's buffers have no limit of their own. The fan-out asks three couriers under one deadline in a supervisor scope, so a failed or slow courier just drops out, and a stale price, clearly labelled, beats no answer. Cancelling the future on hang-up cancels every courier call through the job tree. Under load, each courier gets a bulkhead sized from its contract, so we never send Northline more than its 10 calls; only idempotent couriers are retried, with jitter so a recovering courier isn't hit by waves of retries, and Fjord, whose prices are bookings, is asked once. Northline's slow tail gets a hedge after its p95, which cut p99 from 600 to 120 ms for 5% more calls. Admission turns away what we can't answer in 300 ms with an immediate ERR busy instead of a slow failure, and shutdown stops intake, drains, cancels and joins the rest, and then closes, so nothing leaks. If we switched to virtual threads, I'd keep every limit: the bulkheads, the deadline, admission and the shutdown order, because virtual threads remove the pool and with it the only limit we never wrote down. I'd switch if the couriers only had blocking clients, because then this design needs a blocking pool anyway, or if the team prefers plain Java and connections stay in the thousands. I'd stay on Netty for huge numbers of connections, for the control over the protocol, or when the courier clients are non-blocking and cancellation has to reach them."
 },
 "deeper": {
  "minutes": 10,
  "body": "What a production version of this service would add, roughly in the order it would hurt to miss them.\n\nMeasurements. For each courier: how long calls take (the hedge time comes from the p95), permits in use, calls retried, hedges sent and won, errors by type. For the service: requests admitted, turned away and served stale, and the age of the stale prices. Without them, every number in this track (the 10 permits, the 80 ms hedge, the 50 in flight) is a guess.\n\nA circuit breaker. Retries help with short blips; they make a courier that is down worse. A circuit breaker counts recent failures and, past a threshold, stops calling the courier for a while, then lets a few trial calls through. It sits outside the retry loop, so an open breaker fails fast instead of retrying.\n\nA retry budget. Cap retries as a share of all calls, for example 10%. During a long outage the budget runs out, and the service stops multiplying its own load.\n\nAdaptive limits. Fixed permits are right only for the load they were measured under. Adaptive limits change the number of permits from the response times they observe, the way TCP finds out how much the network can carry: when calls slow down, the limit shrinks before the courier falls over.\n\nDeadlines and context passed along. Send the time left with each courier call, so that the courier can give up too, and carry each request's id across the edge between Netty and coroutines (`asContextElement` or `MDCContext`, as Dispatchers and the coroutine context showed), so that a slow price can be found in the logs.\n\nFair admission. One heavy client can still take most of the 50 places. A quota per client at the door, on top of the limit for the whole service, keeps a single caller from crowding out the rest.\n\nA plan for shutdown on a shared platform. Programs that run as many copies behind a load balancer, a router that spreads customers over the copies, should first tell it to send no more customers, then drain, and keep the grace period shorter than the time the platform waits before it stops the program by force."
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
