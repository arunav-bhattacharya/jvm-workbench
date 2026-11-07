import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l11"
K = "kotlin/workbench/patterns/l11"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l11.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 660 240" role="img" aria-label="Circuit breaker states: Closed goes to Open after N failures in a row; Open goes to HalfOpen when openFor has passed; HalfOpen goes back to Open if the probe fails and to Closed if it succeeds">
<rect class="box-ok" x="30" y="84" width="140" height="56" rx="8"/>
<text class="t" x="100" y="108" text-anchor="middle">Closed</text>
<text class="t-s" x="100" y="127" text-anchor="middle">calls pass</text>
<rect class="box-bad" x="260" y="84" width="140" height="56" rx="8"/>
<text class="t" x="330" y="108" text-anchor="middle">Open</text>
<text class="t-s" x="330" y="127" text-anchor="middle">reject at once</text>
<rect class="box-b" x="490" y="84" width="140" height="56" rx="8"/>
<text class="t" x="560" y="108" text-anchor="middle">HalfOpen</text>
<text class="t-s" x="560" y="127" text-anchor="middle">one probe</text>
<line class="ln-bad" x1="170" y1="102" x2="256" y2="102" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="214" y="72" text-anchor="middle">N failures in a row</text>
<line class="ln" x1="400" y1="102" x2="486" y2="102" marker-end="url(#arr)"/>
<text class="t-s t-m" x="444" y="72" text-anchor="middle">openFor passed</text>
<line class="ln-bad" x1="490" y1="124" x2="404" y2="124" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="446" y="160" text-anchor="middle">probe fails</text>
<line class="ln-a" x1="560" y1="140" x2="560" y2="200"/>
<line class="ln-a" x1="560" y1="200" x2="70" y2="200"/>
<line class="ln-a" x1="70" y1="200" x2="70" y2="144" marker-end="url(#arr)"/>
<text class="t-s t-ok" x="330" y="222" text-anchor="middle">probe succeeds</text>
</svg>""".replace("\n", "")

S1 = """The safest way to share work between threads is to share a queue and nothing else. In **producer-consumer**, producers put work into a `BlockingQueue`, consumers take it out, and the queue does all the locking and waiting:

```java
BlockingQueue<Msg> queue = new ArrayBlockingQueue<>(16);           // bounded: a full queue makes the producer wait
for (int c = 0; c < 4; c++) {
    pool.submit(() -> {
        while (true) {
            if (queue.take() instanceof Stop) return null;          // poison pill: this consumer is done
            processed.incrementAndGet();
        }
    });
}
for (int i = 0; i < 1_000; i++) queue.put(new Job(i));
for (int c = 0; c < 4; c++) queue.put(new Stop());                  // one pill PER consumer
```

```kotlin
val channel = Channel<Int>(capacity = 16)                          // bounded: send suspends when full
val workers = List(4) {
    launch(Dispatchers.Default) {
        for (job in channel) processed.incrementAndGet()            // ends when the channel is closed and drained
    }
}
repeat(1_000) { channel.send(it) }
channel.close()                                                     // one call stops every worker
```

Three rules from *Classic problems: producer-consumer, philosophers, readers-writers* still hold. Bound the queue: a full `ArrayBlockingQueue(16)` makes a fast producer wait, which is backpressure, while an unbounded queue hides overload until the heap runs out. Send one poison pill per consumer, because each pill stops exactly one. And don't swallow `InterruptedException`: it is how a pool tells its workers to stop. Kotlin's channel removes the pill: `close()` ends every `for (job in channel)` loop once the buffer is empty. Use a `for` loop in each worker, not `consumeEach`, which cancels the channel when its own loop ends.

A **worker pool** is the same picture with the queue inside an `ExecutorService`. A fixed pool of platform threads still suits CPU-bound work. For blocking I/O, Java 21 brought back **thread-per-message**: `Executors.newVirtualThreadPerTaskExecutor()` starts a virtual thread for every task, and Kotlin launches a coroutine per message. Both make it trivial to send ten thousand concurrent requests to a PSP that accepts fifty, so thread-per-message always comes with a limit. That limit is the bulkhead, two sections down."""

S2 = """Most of the remaining concurrency patterns answer one question: who owns this state, and what happens to callers who arrive at the wrong moment? You've met them all in earlier tracks:

| Pattern | Problem | Java 21+ | Kotlin | Taught in |
|---|---|---|---|---|
| Immutable object | share state with no locks | records with `List.copyOf` | `data class` with `val`s and copied lists | *Don't share: immutability, confinement, ThreadLocal* |
| Active object | one owner for mutable state | a single-thread executor as a mailbox; methods return `CompletableFuture` | a coroutine that owns the state and reads commands from a `Channel` | *Observer and Command* (the command worker) |
| Guarded suspension | wait until a condition holds | `wait()` in a `while` loop, or better `CompletableFuture`, `CountDownLatch`, `Condition` | `CompletableDeferred.await()`, which suspends | *wait, notify and guarded blocks* |
| Balking | don't start if it's already running | `AtomicBoolean.compareAndSet(false, true)` | the same, or `Mutex.tryLock()` | *Atomics and compare-and-set* |
| Read-write lock | many readers, rare writers | `ReentrantReadWriteLock` (no read-to-write upgrade), or an `AtomicReference` to an immutable snapshot | the same | *Explicit locks: ReentrantLock, Condition, ReadWriteLock* |
| Future / promise | a result that arrives later | `CompletableFuture` with your own executor | `async` and `await` inside `coroutineScope` | *CompletableFuture: composing async steps* |

**Balking** is the one people get wrong most often. A settlement job that runs on a schedule, on retries and from an operator's button must never run twice at once. If it is already running, the right answer is to return at once, not to wait:

```java
final class SettlementJob {
    private final AtomicBoolean running = new AtomicBoolean();

    boolean runIfIdle(Runnable settle) {
        if (!running.compareAndSet(false, true)) return false;      // balk: a run is in progress
        try {
            settle.run();
            return true;
        } finally {
            running.set(false);
        }
    }
}
```

```kotlin
class SettlementJob {
    private val mutex = Mutex()

    suspend fun runIfIdle(settle: suspend () -> Unit): Boolean {
        if (!mutex.tryLock()) return false                          // balk: a run is in progress
        try {
            settle()
            return true
        } finally {
            mutex.unlock()
        }
    }
}
```

The plain-`boolean` version, `if (running) return; running = true;`, is check-then-act and lets two runs overlap. And an `AtomicBoolean` protects one JVM only. With three pods, each pod has its own flag, so a run that must be unique across the fleet needs a database lock or a lease."""

S3 = """Virtual threads make threads cheap. They don't make your dependencies cheap. The card issuer accepts 50 concurrent requests, the Oracle pool has 20 connections, and the fraud service slows to a crawl above 100. A **bulkhead** caps how many calls run against one dependency at once, so a slow dependency can use up its own share and nothing else. The name comes from ships: watertight walls keep one leak from flooding the hull.

```java
final class Bulkhead {
    private final Semaphore permits;
    Bulkhead(int maxConcurrent) { permits = new Semaphore(maxConcurrent); }

    <T> T call(Supplier<T> op) {
        if (!permits.tryAcquire()) throw new BulkheadFull();     // fail fast: don't queue behind slow calls
        try {
            return op.get();
        } finally {
            permits.release();                                    // always, or the limit shrinks for good
        }
    }
}
```

```kotlin
class Bulkhead(maxConcurrent: Int) {
    private val permits = Semaphore(maxConcurrent)                // kotlinx.coroutines.sync.Semaphore

    suspend fun <T> call(op: suspend () -> T): T {
        if (!permits.tryAcquire()) throw BulkheadFull()           // fail fast: don't queue behind slow calls
        try {
            return op()
        } finally {
            permits.release()                                     // always, or the limit shrinks for good
        }
    }
}
```

`tryAcquire()` makes the bulkhead fail fast: a call over the limit gets an error at once instead of waiting behind the slow ones. Resilience4j's semaphore bulkhead does the same by default (`maxConcurrentCalls = 25`, `maxWaitDuration = 0`). `acquire()` would wait, which turns the bulkhead into a limiter. That's fine for a batch job, and risky on a request path, where waiting requests pile up until the caller times out.

Size each bulkhead to its dependency, not to your threads. A bulkhead of 30 in front of a 20-connection pool still queues ten callers inside the pool. With virtual threads, a semaphore is the natural limiter (*Using virtual threads: one per task, limits with semaphores*); a separate thread pool per dependency brings back the pools that virtual threads let you drop. Spring Framework 7 ships the same idea as `@ConcurrencyLimit`, applied through a proxy, so the self-invocation rule from *Decorator and Proxy* applies to it."""

S4 = """A bulkhead limits how much a failing dependency can hurt you. A **circuit breaker** stops calling it for a while. After a run of failures the breaker opens, and calls fail at once without a network trip. That gives the issuer room to recover and gives your callers a quick answer instead of a two-second timeout. After a cool-down the breaker goes half-open and lets one probe through: success closes it, failure opens it again.

The breaker is this track's capstone, because it is three earlier patterns in one class. Its states are sealed records with a transition, as in *State and Chain of Responsibility*. Its `call(op)` wraps any operation behind the same shape, as a decorator does. And its state lives in an `AtomicReference` that changes by compare-and-set, so a thousand request threads can share it without a lock:

```java
sealed interface State permits Closed, Open, HalfOpen {}
record Closed(int consecutiveFailures) implements State {}
record Open(Instant until) implements State {}
record HalfOpen() implements State {}

private final AtomicReference<State> state = new AtomicReference<>(new Closed(0));

// after a failed call: one pure transition, applied atomically
state.updateAndGet(cur -> switch (cur) {
    case HalfOpen h -> new Open(clock.instant().plus(openFor));                            // the probe failed
    case Closed(var n) when n + 1 >= threshold -> new Open(clock.instant().plus(openFor)); // trip
    case Closed(var n) -> new Closed(n + 1);
    case Open o -> o;                                                                      // already open
});
```

```kotlin
sealed interface State {
    data class Closed(val consecutiveFailures: Int) : State
    data class Open(val until: Instant) : State
    data object HalfOpen : State
}

private val state = AtomicReference<State>(State.Closed(0))

// after a failed call: one pure transition, applied atomically
state.updateAndGet { cur ->
    when (cur) {
        State.HalfOpen -> State.Open(clock.instant() + openFor)                                     // the probe failed
        is State.Closed if cur.consecutiveFailures + 1 >= threshold -> State.Open(clock.instant() + openFor)   // trip
        is State.Closed -> State.Closed(cur.consecutiveFailures + 1)
        is State.Open -> cur                                                                        // already open
    }
}
```

Two choices make it testable and correct. Time comes from an injected `Clock`, so a test moves time forward 31 seconds at once instead of sleeping. And the move from open to half-open is a `compareAndSet`: when the cool-down ends and many threads arrive together, exactly one wins the right to probe, and the rest are still rejected.

In production, use a library. Resilience4j 2.4.0 adds sliding windows, failure-rate and slow-call thresholds, metrics and events. Learn its defaults before you trust a test: `minimumNumberOfCalls` is 100, so a breaker that fails five calls in a unit test never opens, and `waitDurationInOpenState` is 60 seconds. And decide what counts as a failure. A declined card means the issuer is working fine, so it must not trip the breaker."""

L = {
 "id": "pat-11",
 "title": "Concurrency patterns that tie it all together",
 "minutes": 39,
 "goal": "By the end you can name the concurrency patterns behind your services (producer-consumer, worker pool, thread-per-message, active object, guarded suspension, balking, read-write lock, future), and build and test a circuit breaker and a fail-fast bulkhead that combine State, Decorator and compare-and-set.",
 "warmup": {
  "q": "A service on virtual threads handles each incoming payment in its own virtual thread and calls a card issuer that allows 50 concurrent requests. A traffic spike brings 5,000 payments at once. What protects the issuer?",
  "options": ["Nothing is needed: virtual threads are cheap, so 5,000 calls are fine", "The JVM limits virtual threads to the number of CPU cores", "A semaphore bulkhead of 50 around the issuer call", "A larger heap"],
  "answer": 2,
  "why": "Virtual threads remove the cost of threads, not the limits of what they call. Thousands of them will happily send thousands of concurrent requests. The JVM runs them on a few carrier threads, but a blocked virtual thread unmounts, so all 5,000 can be waiting on the issuer at once. A bulkhead (a semaphore with `tryAcquire`) caps the in-flight calls at what the issuer allows."
 },
 "sections": [
  {
   "h": "Hand-offs: producer-consumer, worker pools, thread-per-message",
   "body": S1,
   "try": {
    "title": "Forget a poison pill",
    "minutes": 4,
    "steps": [
     "Run `ProducerConsumerDemo` (Java or Kotlin) with the command below.",
     "Java: replace the pill loop with a single `queue.put(new Stop());`. Kotlin: delete `channel.close()`. Predict both numbers in the output line, then run.",
     "Put it back."
    ],
    "code": code("java", "ProducerConsumerDemo.java", "ProducerConsumerDemo", "kotlin", "ProducerConsumerDemo.kt", "ProducerConsumerDemoKt"),
    "expect": "`processed 1000 of 1000, all consumers finished: true`. With one pill, all 1,000 jobs are still processed, but after the two-second wait the line reads `all consumers finished: false`, and the demo reports that consumers were still waiting in `take()`. Three of the four never got a pill. In Kotlin without `close()`, the workers wait forever for the next element: `all workers finished: false`. In a service, that is a shutdown that hangs."
   },
   "refs": [
    {"title": "BlockingQueue.java at jdk-25-ga (the producer-consumer example)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java", "kind": "read"},
    {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html", "kind": "docs"}
   ]
  },
  {
   "h": "Who owns the state: the patterns you already know",
   "body": S2,
   "try": {
    "title": "Turn the balk into check-then-act",
    "minutes": 4,
    "steps": [
     "Run `SettlementJobDemo` in either language: eight triggers fire at the same moment. Read the line.",
     "Replace the `compareAndSet` line with three lines: `if (running.get()) return false;`, then `for (int i = 0; i < 1_000; i++) Thread.onSpinWait();` (Kotlin: `repeat(1_000) { Thread.onSpinWait() }`), then `running.set(true);`.",
     "Run it four or five times and watch `most runs at once`. Then restore the `compareAndSet`."
    ],
    "code": code("java", "SettlementJobDemo.java", "SettlementJobDemo", "kotlin", "SettlementJobDemo.kt", "SettlementJobDemoKt"),
    "expect": "With `compareAndSet`, `most runs at once` is always 1, and usually `ran 1, balked 7`. With check-then-act, several triggers pass the check before any of them sets the flag, so most runs print 2 or 3 for `most runs at once`: two settlement runs over the same batch at the same time. It is the race from the concurrency track, inside a pattern."
   },
   "refs": [
    {"title": "ReentrantReadWriteLock.java at jdk-25-ga (no read-to-write upgrade)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java", "kind": "read"}
   ]
  },
  {
   "h": "Bulkhead: cap the calls to each dependency",
   "body": S3,
   "try": {
    "title": "Wait for a permit, or fail fast",
    "minutes": 4,
    "steps": [
     "Run `BulkheadDemo` (Java or Kotlin). It sends 200 calls that each take 20 ms through a 20-permit semaphore, first with `acquire()` (wait), then with `tryAcquire()` (fail fast). Predict both lines first.",
     "Change the semaphore from 20 permits to 200 and run again. Predict `most in flight` before you look.",
     "Put it back to 20."
    ],
    "code": code("java", "BulkheadDemo.java", "BulkheadDemo", "kotlin", "BulkheadDemo.kt", "BulkheadDemoKt"),
    "expect": "Waiting: `done 200, rejected 0, most in flight 20`, in a bit over 200 ms (ten waves of 20). Fail fast: about `done 20, rejected 180`, in about 20 ms. The exact split can vary slightly between runs. With 200 permits, `most in flight` jumps to 200 in both modes: nothing protects the PSP. Your times will differ a little from these."
   },
   "refs": [
    {"title": "Resilience4j BulkheadConfig.java (defaults)", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/BulkheadConfig.java", "kind": "read"}
   ]
  },
  {
   "h": "Circuit breaker: State, Decorator and compare-and-set in one class",
   "body": S4,
   "figure": {"svg": FIG, "caption": "The breaker's three states. Only one probe runs in half-open; its result decides whether the breaker closes or opens again."},
   "refs": [
    {"title": "Resilience4j CircuitBreakerConfig.java (defaults)", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java", "kind": "read"}
   ]
  }
 ],
 "analogy": "Picture a restaurant kitchen. The order rail is producer-consumer: waiters clip tickets on, cooks take them off, and a full rail tells the waiters to slow down. Each station has four burners, so a run on soup can't take the grill's burners: a bulkhead. When the fryer catches fire, someone hangs a sign saying \"no fried food for ten minutes\", and orders that need it are refused at the door instead of waiting forever: the breaker opening. When the dishwasher is already running, nobody starts a second one: balking. The analogy breaks on knowing why. A kitchen can see the fire. A breaker only counts failures, so you must tell it which errors mean \"the dependency is sick\" and which, like a declined card, mean the dependency is working perfectly.",
 "in_your_world": "Your Kafka consumers are producer-consumer at the scale of a cluster: partitions are the queues, and a consumer per partition is the confinement that keeps per-account ordering safe. Your Quarkus services already speak these patterns through SmallRye Fault Tolerance's `@CircuitBreaker`, `@Bulkhead`, `@Retry` and `@Timeout`, which are interceptor-based, so they need calls that go through the proxy. Temporal brings its own retry policy for activities: don't add a second retry around the PSP call inside the activity, or one failure becomes nine calls. And breakers are per instance: with six pods, each pod has its own breaker and its own view of the issuer, so the fleet keeps probing a dead issuer six times as often as one pod would.",
 "mistake": "The most common mistake is retrying at every layer. The mobile app retries three times, the API gateway retries three times, the payment service's client retries three times, and Temporal retries the activity. One user tap becomes dozens of calls to an issuer that is already struggling, and the retries keep it down. It happens because each team adds a retry to make their own layer reliable, and nobody sees the product. Retry in one place, close to the call, only for idempotent operations or with an idempotency key, with backoff and jitter. Never retry a `CallNotPermitted` or a full bulkhead: those mean \"stop\", not \"try again\".",
 "compare": {
  "title": "Guarded suspension: waiting for a 3-D Secure callback",
  "java": {"title": "ChallengeResults.java", "src": """// the request thread waits until the issuer's webhook arrives, or gives up after a timeout
final class ChallengeResults {
    private final ConcurrentHashMap<String, CompletableFuture<String>> pending = new ConcurrentHashMap<>();

    String awaitResult(String paymentId, Duration timeout)
            throws InterruptedException, ExecutionException, TimeoutException {
        CompletableFuture<String> slot = pending.computeIfAbsent(paymentId, id -> new CompletableFuture<>());
        try {
            return slot.get(timeout.toMillis(), TimeUnit.MILLISECONDS);   // blocks this thread until completed
        } finally {
            pending.remove(paymentId);
        }
    }

    // the webhook thread completes the guard; a callback that comes first is kept for the waiter
    void onCallback(String paymentId, String result) {
        pending.computeIfAbsent(paymentId, id -> new CompletableFuture<>()).complete(result);
    }
}"""},
  "kotlin": {"title": "ChallengeResults.kt", "src": """// the request coroutine waits until the issuer's webhook arrives, or gives up after a timeout
class ChallengeResults {
    private val pending = ConcurrentHashMap<String, CompletableDeferred<String>>()

    suspend fun awaitResult(paymentId: String, timeout: Duration): String {
        val slot = pending.computeIfAbsent(paymentId) { CompletableDeferred() }
        try {
            return withTimeout(timeout) { slot.await() }                  // suspends: no thread is held while waiting
        } finally {
            pending.remove(paymentId)
        }
    }

    // the webhook handler completes the guard; a callback that comes first is kept for the waiter
    fun onCallback(paymentId: String, result: String) {
        pending.computeIfAbsent(paymentId) { CompletableDeferred() }.complete(result)
    }
}"""},
  "note": "Both replace the hand-written `wait()` in a `while` loop with a one-shot promise, which can't miss a signal or wake up spuriously: `complete` happens once, and `get` or `await` returns as soon as it has. The difference is what waiting costs. `CompletableFuture.get` blocks a thread; on a virtual thread that is cheap, but it is still a thread per waiting payment. `CompletableDeferred.await` suspends the coroutine and holds no thread at all, and `withTimeout` cancels the wait cleanly. Java needs three checked exceptions in the signature; Kotlin needs none, and the timeout arrives as a `TimeoutCancellationException`. One gap is shared: a callback that arrives after the waiter gave up leaves an entry in the map, so a real version also expires old entries."
 },
 "worked": {
  "title": "Put retry, breaker and bulkhead in the right order",
  "steps": [
   {"say": "Three pieces from this lesson wrap one PSP charge. The order of the wrappers decides what happens on a bad day. Before reading on: with retry outermost, what does each retry attempt do while the breaker is open?",
    "code": """Supplier<String> charge = () -> psp.charge("order-7781:charge", "tok_42", 1_250);   // idempotency key

Supplier<String> limited = () -> bulkhead.call(charge);       // innermost: caps the calls in flight to the PSP
Supplier<String> guarded = () -> breaker.call(limited);       // then: stop calling a PSP that keeps failing
String ref = retrying(3, guarded);                            // outermost: try again on transient failures""", "lang": "java",
    "alt_code": """val charge = Supplier { psp.charge("order-7781:charge", "tok_42", 1_250) }   // idempotency key

val limited = Supplier { bulkhead.call(charge) }              // innermost: caps the calls in flight to the PSP
val guarded = Supplier { breaker.call(limited) }              // then: stop calling a PSP that keeps failing
val ref = retrying(3) { guarded.get() }                       // outermost: try again on transient failures""", "alt_lang": "kotlin"},
   {"say": "Each attempt hits the open breaker and gets `CallNotPermitted` in microseconds, which costs the PSP nothing. But a rejection isn't a transient failure, and retrying it is noise. Teach the retry to let fail-fast signals through untouched.",
    "code": """static <T> T retrying(int attempts, Supplier<T> body) {
    RuntimeException last = null;
    for (int i = 1; i <= attempts; i++) {
        try {
            return body.get();
        } catch (CircuitBreaker.CallNotPermitted | Bulkhead.BulkheadFull e) {
            throw e;                                          // 1. fail-fast signals: never retry them
        } catch (RuntimeException e) {
            last = e;                                         // 2. a timeout or a 503: worth another attempt
        }
    }
    throw last;
}""", "lang": "java",
    "alt_code": """inline fun <T> retrying(attempts: Int, body: () -> T): T {
    var last: RuntimeException? = null
    repeat(attempts) {
        try {
            return body()
        } catch (e: CircuitBreaker.CallNotPermitted) {
            throw e                                           // 1. fail-fast signals: never retry them
        } catch (e: Bulkhead.BulkheadFull) {
            throw e
        } catch (e: RuntimeException) {
            last = e                                          // 2. a timeout or a 503: worth another attempt
        }
    }
    throw last!!
}""", "alt_lang": "kotlin"},
   {"say": "Why is the bulkhead inside the breaker? An open breaker rejects before the bulkhead is reached, so a dead PSP never holds permits. Why is the retry outside? Each attempt is a separate breaker call, so three failed attempts count as three failures, and a PSP that is really down trips the breaker within one or two payments. Retrying inside the breaker would hide those failures from it.",
    "code": """what each layer sees for one payment while the PSP returns 503:

retry      attempt 1          attempt 2          attempt 3
breaker    Closed(0) -> (1)   Closed(1) -> (2)   Closed(2) -> Open    (three failures trip it)
bulkhead   permit, released   permit, released   permit, released

next payment: retry -> breaker rejects at once (CallNotPermitted) -> no PSP call, no permit""", "lang": "text"},
   {"say": "Pin it in a test with a fake PSP that always fails and the lab's classes. The second payment must never reach the PSP.",
    "code": """AtomicInteger pspCalls = new AtomicInteger();
Supplier<String> failing = () -> { pspCalls.incrementAndGet(); throw new IllegalStateException("PSP 503"); };
CircuitBreaker breaker = new CircuitBreaker(3, Duration.ofSeconds(30), clock);
Bulkhead bulkhead = new Bulkhead(20);
Supplier<String> pipeline = () -> breaker.call(() -> bulkhead.call(failing));

assertThatThrownBy(() -> retrying(3, pipeline)).hasMessage("PSP 503");                 // 4. first payment: 3 attempts
assertThat(breaker.state()).isInstanceOf(CircuitBreaker.Open.class);
assertThatThrownBy(() -> retrying(3, pipeline)).isInstanceOf(CircuitBreaker.CallNotPermitted.class);
assertThat(pspCalls.get()).isEqualTo(3);                                                // 5. the second never left""", "lang": "java",
    "alt_code": """val pspCalls = AtomicInteger()
val failing = Supplier<String> { pspCalls.incrementAndGet(); throw IllegalStateException("PSP 503") }
val breaker = CircuitBreaker(3, Duration.ofSeconds(30), clock)
val bulkhead = Bulkhead(20)
val pipeline = { breaker.call { bulkhead.call(failing) } }

assertThatThrownBy { retrying(3, pipeline) }.hasMessage("PSP 503")                      // 4. first payment: 3 attempts
assertThat(breaker.state()).isInstanceOf(CircuitBreaker.Open::class.java)
assertThatThrownBy { retrying(3, pipeline) }.isInstanceOf(CircuitBreaker.CallNotPermitted::class.java)
assertThat(pspCalls.get()).isEqualTo(3)                                                 // 5. the second never left""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A circuit breaker with a fake clock, and a semaphore bulkhead",
  "minutes": 15,
  "files": [f"{lab}/main/{J}/CircuitBreaker.java", f"{lab}/main/{J}/Bulkhead.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l11.*'",
  "steps": [
   "Read the state table in the Javadoc of `CircuitBreaker`; the states, the constructor and `state()` are given. Run the tests: all ten fail.",
   "Write the first half of `call`: read the state. If it is `Open` and the clock is still before `until`, throw `CallNotPermitted`. If the cool-down is over, `compareAndSet` it to `HalfOpen`, and throw if you lose. If it is already `HalfOpen`, throw.",
   "Write the second half: run `op`. On success, move to `Closed(0)` unless another thread has opened the breaker meanwhile. On a `RuntimeException`, apply the failure transition with `updateAndGet` and rethrow the same exception.",
   "Write `Bulkhead.call`: `tryAcquire`, run, `release` in `finally`.",
   "Run the tests until all ten pass, then run them twice more. Concurrency code has to pass every time."
  ],
  "hints": [
   "`if (s instanceof Open(var until))` gives you `until` in one step. `state.compareAndSet(s, new HalfOpen())` succeeds only if nobody changed the state since you read `s`, so exactly one thread becomes the probe.",
   "On success, `state.updateAndGet(cur -> cur instanceof Open ? cur : new Closed(0))` closes both a half-open breaker and a closed one with failures, without undoing an open set by another thread.",
   "The failure transition is the four-case `switch` from the lesson: `HalfOpen` and the tripping `Closed` both become `new Open(clock.instant().plus(openFor))`."
  ],
  "done_when": "All ten tests in `ResilienceTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A fail-fast bulkhead from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a `Bulkhead` that lets at most `n` calls run at once and rejects the rest immediately with an exception. Then answer two questions: what goes wrong if you `release()` outside a `finally`, and what changes if you use `acquire()` instead of `tryAcquire()`?",
  "answer": {"lang": "java", "src": """final class Bulkhead {
    static final class BulkheadFull extends RuntimeException {}

    private final Semaphore permits;

    Bulkhead(int n) { permits = new Semaphore(n); }

    <T> T call(Supplier<T> op) {
        if (!permits.tryAcquire()) throw new BulkheadFull();   // fail fast; acquire() would wait in line
        try {
            return op.get();
        } finally {
            permits.release();       // outside finally, every exception leaks a permit until none are left
        }
    }
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """class Bulkhead(n: Int) {
    class BulkheadFull : RuntimeException()

    private val permits = Semaphore(n)                          // kotlinx.coroutines.sync.Semaphore

    suspend fun <T> call(op: suspend () -> T): T {
        if (!permits.tryAcquire()) throw BulkheadFull()         // fail fast; acquire() would suspend in line
        try {
            return op()
        } finally {
            permits.release()        // outside finally, every exception leaks a permit until none are left
        }
    }
}"""}}
 },
 "recap": [
  "Producer-consumer: share a bounded queue and nothing else. One poison pill per consumer in Java; `close()` the channel in Kotlin, and use `for`, not `consumeEach`, in each worker.",
  "Thread-per-message is back with virtual threads and coroutines, but cheap threads make it easy to flood a dependency, so it always comes with a limit.",
  "Balking returns at once when the object is busy. Use `compareAndSet` (or `Mutex.tryLock`), never a check-then-act on a plain boolean, and remember it only covers one JVM.",
  "A bulkhead is a semaphore per dependency with `tryAcquire`: it fails fast, releases in `finally`, and is sized to the dependency, not to your threads.",
  "A circuit breaker is State plus Decorator plus compare-and-set: sealed states in an `AtomicReference`, a `call(op)` wrapper, an injected `Clock`, and one half-open probe chosen by `compareAndSet`.",
  "Retry in one layer only, around idempotent calls, outside the breaker, and never on `CallNotPermitted` or a full bulkhead."
 ],
 "quiz": [
  {"q": "A Java pipeline has four consumer threads reading a `BlockingQueue`. After the last job, the producer puts a single `Stop` pill, then calls `close()` on the executor. What happens?",
   "options": ["All four consumers stop, because they all see the pill", "One consumer stops and the other three keep processing new jobs", "One consumer stops, three block in `take()` forever, and `close()` never returns", "The queue throws because a pill was taken twice"],
   "answer": 2,
   "why": "`take()` removes the pill, so exactly one consumer sees it. The other three wait for the next item, which never comes, and `ExecutorService.close()` waits for them. Put one pill per consumer, or in Kotlin close the channel, which ends every `for` loop."},
  {"q": "A Quarkus service on virtual threads calls an issuer that allows 50 concurrent requests. Which limit fits best?",
   "options": ["A semaphore of 50 around the issuer call, with `tryAcquire` so extra calls fail fast", "A fixed pool of 50 platform threads for the whole service", "No limit: virtual threads are cheap", "A new `CompletableFuture` per call"],
   "answer": 0,
   "why": "The limit belongs to the dependency, not to the service's threads, and with virtual threads a semaphore is the natural way to express it. A fixed pool of 50 throttles everything the service does, not just the issuer calls. \"Virtual threads are cheap\" is exactly how you send 5,000 requests to an issuer that takes 50."},
  {"q": "In a unit test, a Resilience4j 2.4.0 circuit breaker built with the default config fails five calls in a row, yet it stays `CLOSED`. Why?",
   "options": ["Resilience4j only counts checked exceptions as failures", "The default `minimumNumberOfCalls` is 100, so the failure rate isn't calculated yet", "Breakers only open after `waitDurationInOpenState` has passed", "The test needs a real clock"],
   "answer": 1,
   "why": "With the defaults, the breaker needs at least 100 recorded calls before it computes a failure rate, so five failures change nothing. Set `minimumNumberOfCalls` and `slidingWindowSize` to small numbers in tests. All exceptions are recorded by default, and `waitDurationInOpenState` controls how long it stays open, not when it opens."},
  {"q": "A scheduled reconciliation job can also be started by an operator. If a run is already in progress, a second trigger should simply return. Which pattern is this?",
   "options": ["Guarded suspension", "Read-write lock", "Producer-consumer", "Balking"],
   "answer": 3,
   "why": "Balking means: if the object isn't in the right state, return at once instead of waiting. Guarded suspension is the opposite, waiting until the condition holds, which here would queue a second run behind the first. Implement it with `compareAndSet` on an `AtomicBoolean`, and with a database lock or lease if it must be unique across pods."},
  {"q": "From *Atomics and compare-and-set*: when the cool-down ends, many request threads find the breaker `Open` with an expired `until` at the same moment. Why must the move to `HalfOpen` be a `compareAndSet` rather than a plain `set`?",
   "options": ["`set` is slower than `compareAndSet`", "So exactly one thread wins the right to probe; with `set`, every thread that saw the expired state would probe the PSP", "`AtomicReference` doesn't allow `set` on records", "`compareAndSet` makes the PSP call atomic"],
   "answer": 1,
   "why": "Each thread read the same `Open` state. `compareAndSet(open, halfOpen)` succeeds for the first thread only, because after that the state is no longer the `Open` object the others read, so their CAS fails and they're rejected. A plain `set` lets all of them through to a PSP that may still be down. CAS makes the state change atomic, not the call itself.",
   "from": "conc-08"}
 ],
 "flashcards": [
  {"front": "Why bound a producer-consumer queue?", "back": "A full bounded queue makes producers wait, which is backpressure. An unbounded one hides overload until memory runs out."},
  {"front": "N consumers stop on poison pills. How many pills?", "back": "N, one per consumer: each `take()` removes one pill. In Kotlin, `close()` the channel instead."},
  {"front": "Balking or guarded suspension: which returns at once?", "back": "Balking returns immediately if the object is busy. Guarded suspension waits until the condition holds."},
  {"front": "Bulkhead: `tryAcquire` or `acquire`?", "back": "`tryAcquire`, so a call over the limit fails fast. `acquire` waits in line, which makes it a limiter. Release in `finally` either way."},
  {"front": "Circuit breaker: what happens in each state?", "back": "Closed: calls pass and failures are counted. Open: calls are rejected at once. HalfOpen: one probe runs; success closes, failure reopens."},
  {"front": "Resilience4j 2.4.0 default `minimumNumberOfCalls`?", "back": "100. A default breaker in a unit test that fails a handful of calls never opens."},
  {"front": "Which exceptions should a retry wrapper never retry?", "back": "Fail-fast signals such as `CallNotPermitted` and a full bulkhead, and anything non-idempotent sent without an idempotency key."}
 ],
 "terms": [
  {"term": "Producer-consumer", "plain": "Producers put work on a shared queue and consumers take it off; the queue does the locking and waiting."},
  {"term": "Poison pill", "plain": "A special message that tells one consumer to stop."},
  {"term": "Active object", "plain": "An object whose method calls become messages run one at a time by its own thread, returning futures."},
  {"term": "Balking", "plain": "Returning at once instead of waiting when the object isn't in the right state, such as \"already running\"."},
  {"term": "Guarded suspension", "plain": "Waiting until a condition holds, then going on; `wait` in a loop, or a future."},
  {"term": "Bulkhead", "plain": "A per-dependency cap on concurrent calls, so one slow dependency can't use up everything."},
  {"term": "Circuit breaker", "plain": "A wrapper that stops calling a failing dependency for a while, then probes to see if it recovered."},
  {"term": "Half-open", "plain": "The breaker state after the cool-down, where one probe call decides whether to close or reopen."}
 ],
 "explain_back": {
  "prompt": "Explain how the lab's circuit breaker combines State, Decorator and compare-and-set, and why the move from open to half-open has to be a `compareAndSet`.",
  "answer": "The breaker's state is a small sealed type, `Closed(failures)`, `Open(until)` and `HalfOpen`, and each outcome moves it with a pure transition, like the payment state machine. That's State. Its `call(op)` takes any operation and returns that operation's result through the same shape, adding behavior around it, which is what a decorator does. The current state lives in an `AtomicReference` so that hundreds of request threads can share one breaker without a lock, and every change is a compare-and-set or `updateAndGet`. The open-to-half-open move matters most. When the cool-down ends, many threads may read the same expired `Open` state at once. `compareAndSet(thatOpen, new HalfOpen())` succeeds for exactly one of them, which becomes the probe; the others see their CAS fail and are rejected. With a plain `set`, every one of them would probe a PSP that may still be down. The injected `Clock` is what lets the tests check all this without sleeping."
 },
 "deeper": {
  "minutes": 12,
  "body": """Resilience4j's breaker defaults, read from its source and printed by version 2.4.0: `failureRateThreshold` 50%, `slowCallRateThreshold` 100%, `slowCallDurationThreshold` 60 s, `waitDurationInOpenState` 60 s, `permittedNumberOfCallsInHalfOpenState` 10, `minimumNumberOfCalls` 100, and a count-based sliding window of 100 calls. Every exception counts as a failure unless you configure `recordExceptions` or `ignoreExceptions`. The project's README says Resilience4j 3 will require Java 21 and adds virtual-thread schedulers; it wasn't on Maven Central when this course was written, so the labs build the breaker by hand.

Spring Framework 7 added `@Retryable` and `@ConcurrencyLimit` to the core framework, switched on with `@EnableResilientMethods`. `@Retryable` defaults to `maxRetries = 3` after the first failure, so four attempts in total, with a one-second delay. Both work through proxies, so the self-invocation rule applies.

Structured concurrency is the future-and-promise pattern with a lifetime. `StructuredTaskScope` forks subtasks, joins them, and cancels the rest when one fails, so no subtask outlives the method that started it. It is still a preview API in JDK 25, 26 and 27 (run with `--enable-preview`), which is why it stays out of the labs. Kotlin's `coroutineScope` has worked this way since the start: an `async` that fails cancels its siblings, and the scope waits for every child.

The patterns in this lesson have distributed cousins. A database row lock or a lease is balking across pods. Kafka partitions are producer-consumer with ordering per key. A Temporal workflow is an active object with durable state: one logical thread per workflow, commands in, results out. The questions you ask stay the same: who owns the state, what waits, and what fails fast."""
 },
 "sources": [
  {"title": "BlockingQueue.java at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java"},
  {"title": "Executors.java at jdk-25-ga (newVirtualThreadPerTaskExecutor)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Executors.java"},
  {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html"},
  {"title": "Resilience4j README", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc"},
  {"title": "Resilience4j CircuitBreakerConfig.java (defaults)", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java"}
 ]
}

out = ROOT / "content/lessons/pat-11.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
