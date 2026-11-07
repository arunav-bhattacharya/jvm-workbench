import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")


def pair(first_lang, first, second_lang, second):
    return f"```{first_lang}\n{first}\n```\n\n```{second_lang}\n{second}\n```"


INTRO = """By the end of this track you have built one program: a TCP quote service on Netty 4.2. It fans every request out to three FX providers with Kotlin coroutines, answers within 300 ms with the best price (or the last good one, marked stale), cancels the provider calls when a client hangs up, and holds up under load with a bulkhead per provider, jittered retries for idempotent calls only, a hedge for the slow provider, load shedding at the door and an ordered shutdown. Its tests prove each of those properties by counting, never by timing: calls, permits, cancellations and virtual milliseconds.

The track draws on all of Part 2. The server shell comes from "Servers and event loops: NIO, Netty, Vert.x and Jetty" (the event loop, the pipeline, codecs and writability). The fan-out comes from "Kotlin coroutines" (builders, the job tree, cancellation and timeouts, supervisors, `select`, virtual-time tests and the bridge to Java futures). "Reactive programming" supplies backpressure, `Mono.zip` and retries, and Reactor is the Java side of most comparisons. From Part 1 it uses Little's law, semaphores and the migration checklist of the virtual threads track. The last lesson ends with a design review: event loop or virtual threads for this service, and when you would switch.

The lab is `labs/quotes`, one package per lesson (`workbench.quotes.l01` to `l03`). Each lesson's starting code contains the previous lesson's solution, so you can start any sitting fresh. Lesson 1's lab is Java; lessons 2 and 3 are Kotlin, with lesson 1's Java server carried along. From `labs/`, run `./gradlew :quotes:test --tests 'workbench.quotes.lNN.*'` until it passes; `./gradlew :quotes:solutionTest` runs the same tests against the reference answers. Servers bind `127.0.0.1` on a free port, coroutine tests run on virtual time, and the Try-it demos run with `./gradlew :quotes:demo -Pmain=...`, in Kotlin and in Java."""

K_FAN = """suspend fun quote(symbol: String): Quote {
    val answers = supervisorScope {                                  // a failed call fails alone
        providers.map { p -> async { withTimeoutOrNull(deadline) { p.quote(symbol) } } }
            .map { d ->
                try { d.await() }
                catch (e: CancellationException) { currentCoroutineContext().ensureActive(); null }
                catch (e: Exception) { null }
            }
    }.filterNotNull()
    val best = answers.minByOrNull { it.price } ?: return cache.lastGood(symbol)?.asStale()
        ?: throw NoQuoteException(symbol)
    return best.also { cache.remember(it) }
}"""
J_FAN = """// Reactor: every outcome becomes a value at its source, then Mono.zip
Mono<Optional<Quote>> inTime(Mono<Quote> call) {
    return call.timeout(DEADLINE).map(Optional::of)
            .onErrorResume(e -> Mono.just(Optional.empty()))
            .defaultIfEmpty(Optional.empty());               // or an empty source empties the zip
}"""
J_LOOP = """// the handler never waits: hand the future back, finish on this channel's loop
CompletableFuture<Quote> quote = source.quote(r.symbol());
inFlight.add(quote);
updateReading(ctx);                                      // autoRead = writable && inFlight < 16
quote.whenCompleteAsync((q, e) -> {
    inFlight.remove(quote);
    if (ctx.channel().isActive()) ctx.writeAndFlush(e == null ? ok(r.id(), q) : error(r.id(), e));
    updateReading(ctx);
}, ctx.executor());"""
K_LOOP = """// the handler never waits: hand the future back, finish on this channel's loop
val quote = source.quote(r.symbol)
inFlight += quote
updateReading(ctx)                                       // isAutoRead = isWritable && inFlight.size < 16
quote.whenCompleteAsync({ q, e ->
    inFlight -= quote
    if (ctx.channel().isActive) ctx.writeAndFlush(if (e == null) ok(r.id, q) else error(r.id, e))
    updateReading(ctx)
}, ctx.executor())"""
K_GUARD = """override suspend fun quote(symbol: String): Quote {
    val once: suspend () -> Quote = { permits.withPermit { delegate.quote(symbol) } }   // every call
    if (!delegate.idempotent) return once()                                            // firm: once
    val attempt: suspend () -> Quote = if (hedgeAfter == null) once else ({ hedged(hedgeAfter, once) })
    return retrying(backoff, random, attempt)                                          // jittered
}"""
J_GUARD = """// Java on virtual threads: the same rules with blocking calls
Quote quote(String symbol) throws IOException, InterruptedException {
    if (!delegate.idempotent()) return once(symbol);       // firm: once
    for (int n = 1; ; n++) {
        try { return once(symbol); }                       // once() = acquire, call, release
        catch (IOException e) {
            if (n > backoff.retries()) throw e;
            Thread.sleep(jittered(backoff.nominal(n)));
        }
    }
}"""

CHEAT = f"""## The design checklist

### The shell (lesson 1)

| Guard | Why | How |
|---|---|---|
| a frame limit | a client that never sends a newline can't make the decoder buffer forever | `LineBasedFrameDecoder(64)`; a longer line gets `ERR line too long`, then a close |
| a request id | replies leave when quotes arrive, so they overtake each other | `7 EURUSD` gets `7 OK EURUSD 1.0842 northbank` |
| never block the loop | one wait stalls every channel on that loop | `QuoteSource.quote` returns a future; no `join()`, `get()` or `runBlocking` in a handler |
| finish on the loop | handler state stays on one thread, so no locks | `whenCompleteAsync(callback, ctx.executor())` |
| backpressure | writes never block; unread replies and pending futures pile up in your memory | auto-read only while writable and fewer than 16 requests wait, plus `FlowControlHandler` |
| close on purpose | a close right after `flush()` can drop bytes; nobody reads a hung-up client's answers | close from the write's future; cancel in-flight futures in `channelInactive` |
| ordered server close | no new work while you stop | stop accepting, close the `ChannelGroup`, then `shutdownGracefully` |

{pair("java", J_LOOP, "kotlin", K_LOOP)}

### The fan-out (lesson 2)

| Decision | Choice | What breaks otherwise |
|---|---|---|
| scope | `supervisorScope` | `coroutineScope` cancels the other providers at the first failure |
| deadline | `withTimeoutOrNull(deadline)` around each call | one timeout around the fan-out throws away answers that arrived |
| failures | await each call in a try; failed or late is `null` | one bad provider fails every quote |
| cancels | rethrow only after `currentCoroutineContext().ensureActive()` says it was yours | a provider's own timeout ends the request |
| nobody answered | the last live quote, marked `STALE`, else `NoQuoteException` | a stale answer refreshing the cache serves an old price forever |
| the Java edge | `scope.future {{ }}` in a scope with `SupervisorJob()` | `supplyAsync` futures don't stop the work; a plain `Job` lets one failure cancel every request |

{pair("kotlin", K_FAN, "java", J_FAN)}

### Under load (lesson 3)

| Guard | Rule |
|---|---|
| bulkhead | a `Semaphore` per provider, sized from its contract; a permit around every single call, hedges included |
| retry | idempotent providers only, `IOException` only, waits jittered by 0.5 to 1.5, inside the deadline |
| hedge | idempotent and slow-tailed providers only, after about p95, with its own permit; cancel the loser |
| admission | `tryAcquire()` at the door; full means `ERR busy` at once, never a queue |
| shutdown | stop accepting, stop admitting, drain within a grace period, `cancelAndJoin()` the rest, close connections and loops |

{pair("kotlin", K_GUARD, "java", J_GUARD)}

## Numbers from this track's demos

| What | Measured |
|---|---|
| 10 clients, one loop, 100 ms provider | `join()`: 1,072 ms, one quote at a time; future handed back: 106 ms, ten at once |
| 20,000 pipelined requests, client not reading | no policy 2,487,339 bytes queued; auto-read rule 694,144; plus `FlowControlHandler` 67,596 |
| fan-out of 120, 300 and 200 ms | 620 ms in turn, 300 ms with `async`, 250 ms with a 250 ms deadline |
| 1,000 clients retrying together | no jitter: all in one millisecond; jitter 0.5: at most 18 per millisecond |
| hedge after 80 ms, slow call every 20th | p99 600 ms down to 120 ms, 210 calls instead of 200 |
| 500 requests, 10 permits x 50 ms, 300 ms deadline | queued: 50 live, 450 slow failures; admit 50: 50 live, 450 `ERR busy` at once |

## Little's law for every limit

In flight = arrival rate x time. A provider that allows 10 calls at once and answers in 50 ms serves at most 200 calls a second; inside a 300 ms deadline that is about 60 requests. Bulkhead permits come from the contract, admission comes from what the providers can answer before the deadline, and every retry and hedge counts as a call.

## Event loop or virtual threads

| Pick | When |
|---|---|
| event loop + coroutines (this design) | the service lives on Netty, Vert.x or Quarkus; connections in the hundreds of thousands; you need auto-read, codecs and flow control; provider clients are non-blocking and a cancel must reach them |
| one virtual thread per connection | provider SDKs only block (JDBC, old SOAP clients); connections in the thousands; the team prefers plain Java |
| either way | bulkheads, deadlines, admission and an ordered shutdown stay. Virtual threads remove the pool and with it the one limit nobody wrote down |

## Test recipes

- Count, don't time: hold quotes open with a controllable fake, then count calls, probe tasks, permits and cancellations. A 5-second wait only bounds how long a failure takes.
- Coroutines on virtual time: `runTest`, and pass `StandardTestDispatcher(testScheduler)` to the class that owns a scope. `currentTime` is exact; a `delay` on `Dispatchers.Default` is real.
- Pipelines without sockets: `EmbeddedChannel(handlers)`, `writeInbound`, then `runPendingTasks()` before `readOutbound()` when replies are written from tasks.
- Real servers: bind `127.0.0.1` on port 0, read with a socket timeout, assert with latches, and always close the server in `finally`."""

RECAP = [
 "The program is a TCP quote service: a Netty shell, a coroutine fan-out to three providers under a 300 ms deadline, and the guards that keep it up under load.",
 "The event loop never waits. Handlers hand futures back and finish in `whenCompleteAsync(..., ctx.executor())`, and a test proves the loop is free by counting calls and probe tasks.",
 "Auto-read is the only tap: read while writable and under 16 in flight, with `FlowControlHandler` holding lines already decoded.",
 "A best-of fan-out uses `supervisorScope` and `withTimeoutOrNull` per call, and rethrows only its own cancel. With no answer it serves a stale quote or fails clearly.",
 "`scope.future { }` in a `SupervisorJob` scope gives Java a future whose cancel reaches every provider call, so a hang-up stops the work.",
 "Each provider gets a bulkhead sized by Little's law. Only idempotent calls are retried, with jitter, and only the slow, idempotent provider is hedged.",
 "Shed at the door with `tryAcquire` and a clear `ERR busy`, and shut down in order: stop accepting, stop admitting, drain, `cancelAndJoin`, close.",
 "Event loop or virtual threads, the limits stay. Pick the model by where the waiting happens and by what the provider clients can do."
]

QUIZ = [
 {
  "q": "Which line in a Netty handler blocks the event loop?",
  "options": [
   "`quote.whenCompleteAsync(callback, ctx.executor())`",
   "`ctx.writeAndFlush(reply)` called from a provider's thread",
   "`source.quote(symbol).join()`",
   "`ctx.channel().config().setAutoRead(false)`"
  ],
  "answer": 2,
  "why": "`join()` holds the loop thread until the quote arrives, so every channel on that loop waits. The callback runs later as a task, a write from another thread is queued onto the loop, and changing auto-read returns at once."
 },
 {
  "q": "The handler turns auto-read off after 16 requests, yet it still receives 2,000 more requests from the bytes of one socket read. What is missing?",
  "options": [
   "A bigger high water mark",
   "A `FlowControlHandler` between the decoders and the handler",
   "A call to `ctx.read()` in `channelRead0`",
   "`TCP_NODELAY` on the channel"
  ],
  "answer": 1,
  "why": "Auto-read stops the next socket read, not the lines the frame decoder already holds. `FlowControlHandler` keeps those decoded messages while auto-read is off and releases them as reading resumes. `ctx.read()` would do the opposite: ask for more."
 },
 {
  "q": "Why does this track's test for a free event loop count calls and probe tasks instead of asserting that a probe runs within 300 ms?",
  "options": [
   "On a busy build machine a healthy loop can miss a millisecond bar, while a blocked loop's counts are wrong at any speed",
   "Netty doesn't let you time tasks on an event loop",
   "Counting is faster to run",
   "Virtual time doesn't work for Netty, so nothing can be timed"
  ],
  "answer": 0,
  "why": "Timings depend on the machine's load; counts depend only on what the code did. A loop stuck in `join()` makes 1 call however fast the machine is, and the test's 5-second wait only bounds how long the failure takes to report."
 },
 {
  "q": "A quote needs any one of three providers' prices. Which scope runs the three calls?",
  "options": [
   "`coroutineScope`, so a failure cancels the rest",
   "`GlobalScope`, so the calls outlive a cancelled request",
   "`runBlocking`, so the event loop waits for the answers",
   "`supervisorScope`, so each call fails alone"
  ],
  "answer": 3,
  "why": "With `supervisorScope` a failed child keeps its exception for `await`, and the other calls carry on. `coroutineScope` is right when every answer is needed. `GlobalScope` leaks the calls, and `runBlocking` blocks the loop."
 },
 {
  "q": "Each call is `async { withTimeout(300) { p.quote(s) } }` in a supervisor fan-out, and the await rethrows every `CancellationException`. A provider is slow. What happens?",
  "options": [
   "The slow provider counts as no answer",
   "The request ends with `TimeoutCancellationException`, as if it had been cancelled",
   "The request waits for the slow provider",
   "The other providers are cancelled, but the request succeeds"
  ],
  "answer": 1,
  "why": "`withTimeout` signals with `TimeoutCancellationException`, a `CancellationException`, and the catch passes it up as if the whole request were cancelled. Use `withTimeoutOrNull`, and check `ensureActive()` before rethrowing a cancel."
 },
 {
  "q": "Lesson 1's Java handler cancels the future when the client hangs up. Which implementation of `QuoteSource.quote` turns that cancel into cancelled provider calls?",
  "options": [
   "`CompletableFuture.supplyAsync(() -> blockingBest(symbol), pool)`",
   "`CompletableFuture.completedFuture(runBlocking { best.quote(symbol) })`",
   "`scope.future { best.quote(symbol) }` in a scope the service owns",
   "`GlobalScope.async { best.quote(symbol) }.asCompletableFuture()` with no scope to close"
  ],
  "answer": 2,
  "why": "The `future` builder links both ways: cancelling the future cancels the coroutine, and the cancel travels down to the provider calls. `supplyAsync`'s cancel stops nothing, `runBlocking` blocks the event loop before returning, and `GlobalScope` work has no owner to close it at shutdown."
 },
 {
  "q": "Which provider may be hedged?",
  "options": [
   "Northbank: indicative prices, so a repeat is harmless, and a slow tail worth cutting",
   "Fjord: firm quotes that reserve liquidity, because it is the slowest",
   "Every provider, after the same 80 ms",
   "None: hedging always doubles the load"
  ],
  "answer": 0,
  "why": "A hedge is a duplicate request, so only an idempotent provider qualifies, and it pays off only where the tail hurts. Hedging after about p95 costs about 5% more calls, not double. A firm quote is never repeated."
 },
 {
  "q": "Where does a provider's bulkhead permit belong?",
  "options": [
   "Around the whole retry loop, so a request holds one permit for all its attempts",
   "Around each single call, so a backoff wait holds nothing and a hedge needs its own permit",
   "Around the whole fan-out, one permit per request",
   "Nowhere: the deadline already limits the calls"
  ],
  "answer": 1,
  "why": "The permit limits calls in flight to the provider, so it wraps exactly one call. Around the retry loop it would be held through backoff waits, around the fan-out it would count requests instead of calls, and a deadline limits time, not concurrency."
 },
 {
  "q": "A burst of 500 requests meets a provider that can answer about 60 within the deadline. What does admission with `tryAcquire` change?",
  "options": [
   "It gets live answers to all 500, just later",
   "It cuts the live answers to almost none",
   "It makes the provider faster",
   "The same number of live answers, but the rest hear `ERR busy` at once instead of failing after the deadline"
  ],
  "answer": 3,
  "why": "Requests beyond what the provider can serve in time fail either way. Shedding makes them fail in a millisecond, early enough to try another instance, and nothing waits in a queue or on the event loop. In the demo, 50 requests got live answers in both runs."
 },
 {
  "q": "When should this service stay on an event loop instead of moving to one virtual thread per connection?",
  "options": [
   "When the provider SDKs only block",
   "When the team prefers plain Java and connections number in the thousands",
   "When it already runs on Netty or Vert.x, connections number in the hundreds of thousands, or the provider clients are non-blocking and a cancel must reach them",
   "Always: event loops are faster per request"
  ],
  "answer": 2,
  "why": "The event loop pays off for huge connection counts, protocol control and async clients. Blocking SDKs and plain Java favour virtual threads. Neither model makes a single request faster, and both still need the bulkheads, deadlines and admission."
 }
]

T = {"id": "cap2", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/cap2.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
