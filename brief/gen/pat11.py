import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l11"
K = "kotlin/workbench/patterns/l11"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l11.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 660 240" role="img" aria-label="Circuit breaker states: Closed goes to Open after N failures in a row; Open goes to HalfOpen when the cool-down is over; HalfOpen goes back to Open if the probe fails and to Closed if it succeeds">
<rect class="box-ok" x="30" y="84" width="140" height="56" rx="8"/>
<text class="t" x="100" y="108" text-anchor="middle">Closed</text>
<text class="t-s" x="100" y="127" text-anchor="middle">calls pass</text>
<rect class="box-bad" x="260" y="84" width="140" height="56" rx="8"/>
<text class="t" x="330" y="108" text-anchor="middle">Open</text>
<text class="t-s" x="330" y="127" text-anchor="middle">turn away at once</text>
<rect class="box-b" x="490" y="84" width="140" height="56" rx="8"/>
<text class="t" x="560" y="108" text-anchor="middle">HalfOpen</text>
<text class="t-s" x="560" y="127" text-anchor="middle">one probe</text>
<line class="ln-bad" x1="170" y1="102" x2="256" y2="102" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="214" y="72" text-anchor="middle">N failures in a row</text>
<line class="ln" x1="400" y1="102" x2="486" y2="102" marker-end="url(#arr)"/>
<text class="t-s t-m" x="444" y="72" text-anchor="middle">cool-down over</text>
<line class="ln-bad" x1="490" y1="124" x2="404" y2="124" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="446" y="160" text-anchor="middle">probe fails</text>
<line class="ln-a" x1="560" y1="140" x2="560" y2="200"/>
<line class="ln-a" x1="560" y1="200" x2="70" y2="200"/>
<line class="ln-a" x1="70" y1="200" x2="70" y2="144" marker-end="url(#arr)"/>
<text class="t-s t-ok" x="330" y="222" text-anchor="middle">probe succeeds</text>
</svg>""".replace("\n", "")

OPENING = """Saturday morning is the corner shop's busiest hour. Orders arrive faster than anyone can pack them, so the counter clips each slip onto a rail, and four packers take them off. At closing time, each packer must be told to go home. At ten o'clock, the Big Blue Vans booking line goes quiet, and every call hangs for two seconds, then fails. Pedal Post's line takes only twenty calls at once.

Every pattern so far was about one object. On a busy morning, many threads (paths of work that run side by side) use those objects at once. The concurrency track met this scene in a kitchen: the rail of tickets, the team of cooks, the price board nobody writes on, the ticket that says what to do next. The trap is to think cheap threads make everything cheap. The van company's line doesn't get any wider.

The last lesson ended here. In this lesson, we'll name the concurrency patterns behind it, then build two from this track's patterns: a bulkhead, which caps the calls to one service, and a circuit breaker, which stops calling one that keeps failing. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_RAIL = """BlockingQueue<Card> rail = new ArrayBlockingQueue<>(16);       // bounded: a full rail makes the counter wait
for (int p = 0; p < 4; p++) {
    team.submit(() -> {
        while (true) {
            if (rail.take() instanceof Closed) return null;      // the poison pill: this packer goes home
            packed.incrementAndGet();
        }
    });
}
for (int i = 0; i < 1_000; i++) rail.put(new Slip(i));
for (int p = 0; p < 4; p++) rail.put(new Closed());             // one card PER packer"""
K_RAIL = """val rail = Channel<Int>(capacity = 16)                         // bounded: send waits when the rail is full
val packers = List(4) {
    launch(Dispatchers.Default) {
        for (slip in rail) packed.incrementAndGet()            // ends when the rail is closed and empty
    }
}
repeat(1_000) { rail.send(it) }
rail.close()                                                   // one call sends every packer home"""

S0 = """The safest way to share work between threads is to share a queue and nothing else. A **queue** is a line of items that leave in the order they joined. In **producer-consumer**, producers put work into a queue, consumers take it out, and the queue does all the locking and waiting. At the shop, the counter is the producer, the packers are the consumers, and the rail of order slips is the queue: the kitchen rail from *wait, notify and guarded blocks*, moved to the back room.

""" + pair(J_RAIL, K_RAIL) + """

`ProducerConsumerDemo`, in the Try it, clips 1,000 slips onto a rail that holds 16, with four packers taking them off:

```text
packed 1000 of 1000, all packers finished: true
```

Three rules from *Classic problems: producer-consumer, philosophers, readers-writers* still hold. Bound the queue: a full `ArrayBlockingQueue(16)` makes a fast counter wait, which is called **backpressure**, while an unbounded queue hides a pile-up until memory runs out. Send one **poison pill**, a special item that tells one consumer to stop, for each consumer, because each `take()` removes exactly one. And don't swallow `InterruptedException`: it's how a pool tells its threads to stop. Kotlin's channel needs no pill: `close()` ends every `for (slip in rail)` loop once the rail is empty. Use a `for` loop in each packer, not `consumeEach`, which cancels the whole channel when its own loop ends.

The rail picture holds until closing time. A packer can see the lights go off; a thread waiting in `take()` sees nothing until an item arrives, so you must send it one. Forget a card, and three packers wait by the empty rail all night.

A **worker pool**, or thread pool, is the same picture with the rail inside an `ExecutorService`: the team of cooks from *Why pools: Executor, ExecutorService and shutdown*, hired once. A fixed pool of ordinary threads still suits work that keeps the processor busy. For work that mostly waits, Java 21 brought back **thread-per-message**: `Executors.newVirtualThreadPerTaskExecutor()` starts a cheap virtual thread for every task, and in Kotlin you launch a coroutine per message. Both make it easy to send ten thousand bookings at once to a courier who takes twenty.

**Share a bounded queue and nothing else. Close it, or send one pill per consumer.**

So thread-per-message always comes with a limit, and that limit is the bulkhead, two sections down. First, the patterns that keep state apart."""

# ---------------------------------------------------------------- section 1
J_BALK = """final class StockCount {
    private final AtomicBoolean running = new AtomicBoolean();

    boolean runIfIdle(Runnable count) {
        if (!running.compareAndSet(false, true)) return false;      // balk: a count is already running
        try {
            count.run();
            return true;
        } finally {
            running.set(false);
        }
    }
}"""
K_BALK = """class StockCount {
    private val mutex = Mutex()                                     // kotlinx.coroutines.sync.Mutex

    suspend fun runIfIdle(count: suspend () -> Unit): Boolean {
        if (!mutex.tryLock()) return false                          // balk: a count is already running
        try {
            count()
            return true
        } finally {
            mutex.unlock()
        }
    }
}"""

S1 = """Most of the other concurrency patterns answer one question: who owns this state, and what happens to a thread that arrives at the wrong moment? You've met them all in earlier tracks. Each row names a pattern, what it solves, and where you saw it:

| Pattern | What it solves | Java 21+ | Kotlin | Taught in |
|---|---|---|---|---|
| Immutable object | share state with no locks, like the price board nobody writes on | records with `List.copyOf` | `data class` with `val`s and copied lists | *Don't share: immutability, confinement, ThreadLocal* |
| Active object | one owner for changeable state, like the stock worker that alone touches the shelves | a single-thread executor as a mailbox; methods return `CompletableFuture` | a coroutine that owns the state and reads commands from a `Channel` | *Observer and Command* |
| Guarded suspension | wait until a condition holds, like a cook waiting for the next ticket | `wait()` in a `while` loop, or better `CompletableFuture`, `CountDownLatch`, `Condition` | `CompletableDeferred.await()`, which suspends | *wait, notify and guarded blocks* |
| Balking | don't start a job that's already running | `AtomicBoolean.compareAndSet(false, true)` | the same, or `Mutex.tryLock()` | *Atomics and compare-and-set* |
| Read-write lock | many readers, rare writers | `ReentrantReadWriteLock` (no read-to-write upgrade), or an `AtomicReference` to an immutable snapshot | the same | *Explicit locks: ReentrantLock, Condition, ReadWriteLock* |
| Future | a result that arrives later, like the ticket that says what to do when the steak is ready | `CompletableFuture` with your own executor | `async` and `await` inside `coroutineScope` | *CompletableFuture: composing async steps* |

**Balking** means returning at once, instead of waiting, when the object isn't ready for the job, and it's the one people get wrong most often. The shop's stock count walks every shelf and counts what's left. It runs at closing time, again after a failure, and whenever the manager presses a button, and it must never run twice at once. If a count is already running, the right answer is to return at once:

""" + pair(J_BALK, K_BALK) + """

The Kotlin version uses a coroutine `Mutex`, whose `tryLock()` gives up at once instead of waiting; the Kotlin twin of the demo keeps the `AtomicBoolean`, exactly as Java does. `StockCountDemo`, in the Try it, fires eight triggers at the same moment:

```text
ran 1, balked 7, most counts at once: 1
```

The plain-`boolean` version, `if (running) return; running = true;`, is check-then-act, the race from *Race conditions: why count++ lies*: two threads can both see `false` before either one sets `true`, and two counts walk the same shelves at once. And an `AtomicBoolean` protects one program only. If the shop runs its program on two computers, each has its own flag, so a count that must be unique everywhere needs a shared lock, such as a row locked in the shop's database.

**Balk with one atomic step, `compareAndSet`, never with a check and then a set.**

Balking protects a job from itself. Next, we'll protect the services the shop calls from the shop."""

# ---------------------------------------------------------------- section 2
J_BULK = """final class Bulkhead {
    private final Semaphore permits;
    Bulkhead(int maxConcurrent) { permits = new Semaphore(maxConcurrent); }

    <T> T call(Supplier<T> op) {
        if (!permits.tryAcquire()) throw new BulkheadFull("all lines busy");   // busy tone: fail fast
        try {
            return op.get();
        } finally {
            permits.release();                                  // always, or the shop loses a line for good
        }
    }
}"""
K_BULK = """class Bulkhead(maxConcurrent: Int) {
    private val permits = Semaphore(maxConcurrent)              // kotlinx.coroutines.sync.Semaphore

    suspend fun <T> call(op: suspend () -> T): T {
        if (!permits.tryAcquire()) throw BulkheadFull("all lines busy")        // busy tone: fail fast
        try {
            return op()
        } finally {
            permits.release()                                   // always, or the shop loses a line for good
        }
    }
}"""

S2 = """Virtual threads make threads cheap. They don't make the services the shop calls any bigger. A **service** here is another program the shop's program calls over the network, such as a courier's booking line or the shop's database. Pedal Post's booking line takes 20 calls at once, the database accepts 20 connections, and Big Blue Vans slows to a crawl above 50. A **bulkhead** caps how many calls run against one service at once, so a slow service can use up its own share and nothing else. The name comes from ships, where watertight walls keep one leak from flooding the whole hull.

The shop's picture is a switchboard. Pedal Post has 20 phone lines. When all 20 are busy, a caller hears the busy tone at once and can try something else, instead of waiting on hold with the music. In code, the lines are the permits of a **semaphore**, a counter of permits that threads take and give back:

""" + pair(J_BULK, K_BULK) + """

`BulkheadDemo`, in the Try it, sends 200 bookings that each take 20 ms through 20 lines, first waiting on hold (`acquire()`), then with the busy tone (`tryAcquire()`). One run, on a busy machine, printed:

```text
wait       done 200, rejected   0, most at once 20, about 288 ms
fail fast  done  20, rejected 180, most at once 20, about 26 ms
```

Correctness first: neither mode ever had more than 20 calls on the line. Then time. Waiting served all 200 in about ten rounds of 20, close to 300 ms. Failing fast answered every caller within about 26 ms, and 180 of them heard the busy tone. Your numbers will differ a little; the shape won't.

`tryAcquire()` makes the bulkhead **fail fast**: a call over the limit gets an error at once instead of waiting behind the slow ones. `acquire()` waits, which turns the bulkhead into a limiter. That's fine for a job that runs at night, and risky for a customer at the counter, where waiting calls pile up until someone gives up.

Size each bulkhead to its service, not to your threads. A bulkhead of 30 in front of a database with 20 connections still makes ten callers wait inside. With virtual threads, a semaphore is the natural limit, as in *Using virtual threads: one per task, limits with semaphores*, where the grill had room for 20 pans.

The switchboard picture breaks when the call ends. A phone line frees itself when the caller hangs up. A permit comes back only if your code gives it back, which is why `release()` sits in `finally`: miss it once on an exception, and the shop has 19 lines for good.

**Give each service its own bulkhead, sized to what that service can take, and release in `finally`.**

A bulkhead limits how much a slow service can hurt the shop. A service that's down needs something stronger."""

# ---------------------------------------------------------------- section 3
J_BREAKER = """sealed interface State permits Closed, Open, HalfOpen {}
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
});"""
K_BREAKER = """sealed interface State {
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
}"""

S3 = """At ten o'clock, the Big Blue Vans booking service goes quiet. Every call hangs for two seconds and then fails, and the customers at the counter wait each time. The shop's back room has a fuse box with a circuit breaker: when something goes wrong in the wiring, it trips and cuts the power, so the fault can't do more damage. The software **circuit breaker** borrows the name. After a run of failures it **opens**, and calls fail at once without even trying the van company. After a cool-down, it goes **half-open** and lets one test call through, called a **probe**. Success **closes** it again; failure opens it for another cool-down.

The breaker is this track's capstone, because it is three earlier patterns in one class. Its states are sealed records with a transition, as in *State and Chain of Responsibility*. Its `call(op)` wraps any operation and keeps its shape, as a decorator does in *Decorator and Proxy*. And its state lives in an `AtomicReference` that changes by **compare-and-set**, read as "update it only if nobody beat me to it", so a thousand threads can share it without a lock:

""" + pair(J_BREAKER, K_BREAKER) + """

Two choices make it testable and correct. Time comes from an injected `Clock`, so a test moves time forward 31 seconds at once instead of sleeping. And the move from open to half-open is a `compareAndSet`: when the cool-down ends and many threads arrive together, exactly one wins the right to probe, and the rest are still turned away. The figure shows the three states and the moves between them.

The fuse box picture breaks in two places. A real breaker stays off until a person resets it; the software one tries again by itself after the cool-down. And a real breaker reacts to the current in the wire, while the software one only counts failures, so you must tell it which errors mean "the service is sick". A courier who answers "no vans free in your area" is working perfectly, and must not trip the breaker.

**Count only the failures that mean the service is sick, and let one probe, chosen by compare-and-set, decide when it has recovered.**

Check yourself. The breaker opened at 10:00:00 with a 30-second cool-down. A test moves the fake clock to 10:00:31, and eight threads call at the same moment. How many calls reach the van company, and what picks them? (One. Each thread tries the `compareAndSet` from `Open` to `HalfOpen`; exactly one succeeds and runs the probe. The other seven find the state already changed and are turned away.)"""

ASIDE = {
 "title": "Should I build my own breaker?",
 "body": "Only to learn how one works, as the lab does. In a real program, use a library. Resilience4j, a fault-tolerance library for Java (2.4.0 when this course was written), gives you breakers with sliding windows, failure-rate and slow-call thresholds, metrics and events, plus bulkheads and retries. Learn its defaults before you trust a test: `minimumNumberOfCalls` is 100, so a breaker that fails five calls in a unit test never opens, and `waitDurationInOpenState` is 60 seconds. Its semaphore bulkhead fails fast by default, like ours: `maxConcurrentCalls` is 25 and `maxWaitDuration` is 0."
}

L = {
 "id": "pat-11",
 "title": "Concurrency patterns that tie it all together",
 "minutes": 39,
 "goal": "By the end you can name the concurrency patterns behind a busy program (producer-consumer, worker pool, thread-per-message, active object, guarded suspension, balking, read-write lock, future), and build and test a circuit breaker and a fail-fast bulkhead that combine State, Decorator and compare-and-set.",
 "opening": OPENING,
 "warmup": {
  "q": "The shop's program handles each booking on its own virtual thread and calls Pedal Post's booking service, which takes 20 calls at once. A Saturday rush brings 5,000 bookings at once. What protects Pedal Post?",
  "options": ["Nothing is needed: virtual threads are cheap, so 5,000 calls are fine", "The JVM limits virtual threads to the number of processor cores", "A semaphore bulkhead of 20 around the booking call", "A larger heap"],
  "answer": 2,
  "why": "Virtual threads remove the cost of threads, not the limits of what they call. The JVM runs them on a few carrier threads, but a virtual thread that waits steps off its carrier, so all 5,000 can be waiting on Pedal Post at once. A bulkhead, a semaphore with `tryAcquire`, caps the calls on the line at what the courier allows."
 },
 "sections": [
  {
   "h": "The packing rail: producer-consumer and a team of packers",
   "body": S0,
   "try": {
    "title": "Forget a closed card",
    "minutes": 4,
    "steps": [
     "Run `ProducerConsumerDemo` (Java or Kotlin) with the command below.",
     "Java: replace the card loop with a single `rail.put(new Closed());`. Kotlin: delete `rail.close()`. Predict both parts of the output line, then run.",
     "Put it back."
    ],
    "code": code("java", "ProducerConsumerDemo.java", "ProducerConsumerDemo", "kotlin", "ProducerConsumerDemo.kt", "ProducerConsumerDemoKt"),
    "expect": "`packed 1000 of 1000, all packers finished: true`. With one card, all 1,000 slips are still packed, but after the two-second wait the line reads `all packers finished: false`, and the demo reports that packers were still waiting at the rail: three of the four never got a card. In Kotlin without `close()`, the packers wait for a slip that never comes, and you get `all packers finished: false` too. In a real program, that is a shutdown that hangs."
   },
   "refs": [
    {"title": "BlockingQueue.java at jdk-25-ga (the producer-consumer example)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java", "kind": "read"},
    {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html", "kind": "docs"}
   ]
  },
  {
   "h": "Who owns the state: the patterns you already know, and balking",
   "body": S1,
   "try": {
    "title": "Turn the balk into check-then-act",
    "minutes": 4,
    "steps": [
     "Run `StockCountDemo` in either language: eight triggers fire at the same moment. Read the line.",
     "Replace the `compareAndSet` line with three lines: `if (running.get()) return false;`, then `for (int i = 0; i < 1_000; i++) Thread.onSpinWait();` (Kotlin: `repeat(1_000) { Thread.onSpinWait() }`), then `running.set(true);`.",
     "Run it four or five times and watch `most counts at once`. Then put the `compareAndSet` back."
    ],
    "code": code("java", "StockCountDemo.java", "StockCountDemo", "kotlin", "StockCountDemo.kt", "StockCountDemoKt"),
    "expect": "With `compareAndSet`, `most counts at once` is always 1, and usually `ran 1, balked 7`. With check-then-act, several triggers pass the check before any of them sets the flag, so most runs print 2 or 3 for `most counts at once`: two stock counts walking the same shelves at the same time. It is the race from the concurrency track, inside a pattern."
   },
   "refs": [
    {"title": "ReentrantReadWriteLock.java at jdk-25-ga (no read-to-write upgrade)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java", "kind": "read"}
   ]
  },
  {
   "h": "Bulkhead: a fixed number of phone lines for each service",
   "body": S2,
   "try": {
    "title": "Wait on hold, or hear the busy tone",
    "minutes": 4,
    "steps": [
     "Run `BulkheadDemo` (Java or Kotlin). It sends 200 bookings that each take 20 ms through a 20-permit semaphore, first with `acquire()` (wait), then with `tryAcquire()` (fail fast). Predict both lines first.",
     "Change the semaphore from 20 permits to 200 and run again. Predict `most at once` before you look.",
     "Put it back to 20."
    ],
    "code": code("java", "BulkheadDemo.java", "BulkheadDemo", "kotlin", "BulkheadDemo.kt", "BulkheadDemoKt"),
    "expect": "Waiting: `done 200, rejected 0, most at once 20`, in a bit over 200 ms (ten rounds of 20). Fail fast: about `done 20, rejected 180`, in 20 to 30 ms. The exact split can vary slightly between runs. With 200 permits, `most at once` jumps to 200 in both modes: nothing protects the courier. Your times will differ a little from these."
   },
   "refs": [
    {"title": "Resilience4j BulkheadConfig.java (defaults)", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/BulkheadConfig.java", "kind": "read"}
   ]
  },
  {
   "h": "Circuit breaker: State, Decorator and compare-and-set in one class",
   "body": S3,
   "figure": {"svg": FIG, "caption": "The breaker's three states. Only one probe runs in half-open; its result decides whether the breaker closes or opens again."},
   "aside": ASIDE,
   "refs": [
    {"title": "Resilience4j CircuitBreakerConfig.java (defaults)", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Guarded suspension: waiting for the courier to confirm a pickup",
  "java": {"title": "PickupConfirmations.java", "src": """// the counter's thread waits until the courier confirms the pickup, or gives up after a timeout
final class PickupConfirmations {
    private final ConcurrentHashMap<String, CompletableFuture<String>> pending = new ConcurrentHashMap<>();

    String awaitConfirmation(String orderNo, Duration timeout)
            throws InterruptedException, ExecutionException, TimeoutException {
        CompletableFuture<String> slot = pending.computeIfAbsent(orderNo, no -> new CompletableFuture<>());
        try {
            return slot.get(timeout.toMillis(), TimeUnit.MILLISECONDS);   // blocks this thread until completed
        } finally {
            pending.remove(orderNo);
        }
    }

    // the courier's message arrives on another thread; one that comes first is kept for the waiter
    void onConfirmation(String orderNo, String pickupRef) {
        pending.computeIfAbsent(orderNo, no -> new CompletableFuture<>()).complete(pickupRef);
    }
}"""},
  "kotlin": {"title": "PickupConfirmations.kt", "src": """// the counter's coroutine waits until the courier confirms the pickup, or gives up after a timeout
class PickupConfirmations {
    private val pending = ConcurrentHashMap<String, CompletableDeferred<String>>()

    suspend fun awaitConfirmation(orderNo: String, timeout: Duration): String {
        val slot = pending.computeIfAbsent(orderNo) { CompletableDeferred() }
        try {
            return withTimeout(timeout) { slot.await() }                  // suspends: no thread is held while waiting
        } finally {
            pending.remove(orderNo)
        }
    }

    // the courier's message arrives elsewhere; one that comes first is kept for the waiter
    fun onConfirmation(orderNo: String, pickupRef: String) {
        pending.computeIfAbsent(orderNo) { CompletableDeferred() }.complete(pickupRef)
    }
}"""},
  "note": "Both replace the hand-written `wait()` in a `while` loop with a one-shot promise, which can't miss a signal or wake up by accident: `complete` happens once, and `get` or `await` returns as soon as it has. The difference is what waiting costs. `CompletableFuture.get` blocks a thread; on a virtual thread that is cheap, but it is still a thread per waiting order. `CompletableDeferred.await` suspends the coroutine and holds no thread at all, and `withTimeout` cancels the wait cleanly. Java needs three checked exceptions in the signature; Kotlin needs none, and the timeout arrives as a `TimeoutCancellationException`. One gap is shared: a confirmation that arrives after the waiter gave up leaves an entry in the map, so a real version also clears out old entries."
 },
 "worked": {
  "title": "Put retry, breaker and bulkhead in the right order",
  "steps": [
   {"say": "Three pieces from this lesson wrap one van booking. The order of the wrappers decides what happens on a bad morning. Before reading on: with the retry on the outside, what does each attempt do while the breaker is open?",
    "code": """Supplier<String> book = () -> vans.book("order-7781", 2);   // safe to repeat: the van company skips a second booking for 7781

Supplier<String> limited = () -> bulkhead.call(book);        // innermost: caps the calls on the line
Supplier<String> guarded = () -> breaker.call(limited);      // then: stop calling a service that keeps failing
String ref = retrying(3, guarded);                           // outermost: try again after a passing failure""", "lang": "java",
    "alt_code": """val book = Supplier { vans.book("order-7781", 2) }           // safe to repeat: the van company skips a second booking for 7781

val limited = Supplier { bulkhead.call(book) }               // innermost: caps the calls on the line
val guarded = Supplier { breaker.call(limited) }             // then: stop calling a service that keeps failing
val ref = retrying(3) { guarded.get() }                      // outermost: try again after a passing failure""", "alt_lang": "kotlin"},
   {"say": "Each attempt hits the open breaker and gets `CallNotPermitted` in microseconds, which costs the van company nothing. But a rejection isn't a passing failure, and retrying it is noise. Teach the retry to let the fail-fast signals through untouched.",
    "code": """static <T> T retrying(int attempts, Supplier<T> body) {
    RuntimeException last = null;
    for (int i = 1; i <= attempts; i++) {
        try {
            return body.get();
        } catch (CircuitBreaker.CallNotPermitted | Bulkhead.BulkheadFull e) {
            throw e;                                          // 1. fail-fast signals: never retry them
        } catch (RuntimeException e) {
            last = e;                                         // 2. a timeout or a dropped line: worth another try
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
            last = e                                          // 2. a timeout or a dropped line: worth another try
        }
    }
    throw last!!
}""", "alt_lang": "kotlin"},
   {"say": "Why is the bulkhead inside the breaker? An open breaker turns calls away before they reach the bulkhead, so a dead service never holds a line. Why is the retry outside? Each attempt is a separate breaker call, so three failed attempts count as three failures, and a van company that is really down trips the breaker within one or two bookings. A retry inside the breaker would hide those failures from it.",
    "code": """what each layer sees for one booking while the van company is down:

retry      attempt 1          attempt 2          attempt 3
breaker    Closed(0) -> (1)   Closed(1) -> (2)   Closed(2) -> Open    (three failures trip it)
bulkhead   line, given back   line, given back   line, given back

next booking: retry -> breaker turns it away at once (CallNotPermitted) -> no call, no line used""", "lang": "text"},
   {"say": "Pin it in a test, with a fake van service that always fails and the lab's classes. The second booking must never reach the van company.",
    "code": """AtomicInteger vanCalls = new AtomicInteger();
Supplier<String> failing = () -> { vanCalls.incrementAndGet(); throw new IllegalStateException("vans booking line down"); };
CircuitBreaker breaker = new CircuitBreaker(3, Duration.ofSeconds(30), clock);
Bulkhead bulkhead = new Bulkhead(20);
Supplier<String> pipeline = () -> breaker.call(() -> bulkhead.call(failing));

assertThatThrownBy(() -> retrying(3, pipeline)).hasMessage("vans booking line down");   // 3. first booking: 3 attempts
assertThat(breaker.state()).isInstanceOf(CircuitBreaker.Open.class);
assertThatThrownBy(() -> retrying(3, pipeline)).isInstanceOf(CircuitBreaker.CallNotPermitted.class);
assertThat(vanCalls.get()).isEqualTo(3);                                                 // 4. the second never left""", "lang": "java",
    "alt_code": """val vanCalls = AtomicInteger()
val failing = Supplier<String> { vanCalls.incrementAndGet(); throw IllegalStateException("vans booking line down") }
val breaker = CircuitBreaker(3, Duration.ofSeconds(30), clock)
val bulkhead = Bulkhead(20)
val pipeline = { breaker.call { bulkhead.call(failing) } }

assertThatThrownBy { retrying(3, pipeline) }.hasMessage("vans booking line down")       // 3. first booking: 3 attempts
assertThat(breaker.state()).isInstanceOf(CircuitBreaker.Open::class.java)
assertThatThrownBy { retrying(3, pipeline) }.isInstanceOf(CircuitBreaker.CallNotPermitted::class.java)
assertThat(vanCalls.get()).isEqualTo(3)                                                  // 4. the second never left""", "alt_lang": "kotlin"}
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
   "Write the second half: run `op`. On success, move to `Closed(0)` unless another thread has opened the breaker in the meantime. On a `RuntimeException`, apply the failure transition with `updateAndGet` and rethrow the same exception.",
   "Write `Bulkhead.call`: `tryAcquire`, run, `release` in `finally`.",
   "Run the tests until all ten pass, then run them twice more. Code that many threads share has to pass every time."
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
  "prompt": "Close this page. Write a `Bulkhead` that lets at most `n` calls run at once and turns the rest away immediately with an exception. Then answer two questions: what goes wrong if you `release()` outside a `finally`, and what changes if you use `acquire()` instead of `tryAcquire()`?",
  "answer": {"lang": "java", "src": """final class Bulkhead {
    static final class BulkheadFull extends RuntimeException {}

    private final Semaphore permits;

    Bulkhead(int n) { permits = new Semaphore(n); }

    <T> T call(Supplier<T> op) {
        if (!permits.tryAcquire()) throw new BulkheadFull();   // fail fast; acquire() would wait on hold
        try {
            return op.get();
        } finally {
            permits.release();       // outside finally, every exception loses a permit until none are left
        }
    }
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """class Bulkhead(n: Int) {
    class BulkheadFull : RuntimeException()

    private val permits = Semaphore(n)                          // kotlinx.coroutines.sync.Semaphore

    suspend fun <T> call(op: suspend () -> T): T {
        if (!permits.tryAcquire()) throw BulkheadFull()         // fail fast; acquire() would suspend on hold
        try {
            return op()
        } finally {
            permits.release()        // outside finally, every exception loses a permit until none are left
        }
    }
}"""}}
 },
 "recap": [
  "Producer-consumer: share a bounded queue and nothing else. One poison pill per consumer in Java; `close()` the channel in Kotlin, with a `for` loop, not `consumeEach`, in each worker.",
  "Thread-per-message is back with virtual threads and coroutines, but cheap threads make it easy to flood a service, so it always comes with a limit.",
  "Balking returns at once when a job is already running. Use `compareAndSet` (or `Mutex.tryLock`), never a check-then-act on a plain boolean.",
  "A bulkhead is a semaphore per service with `tryAcquire`: it fails fast, releases in `finally`, and is sized to the service, not to your threads.",
  "A circuit breaker is State plus Decorator plus compare-and-set: sealed states in an `AtomicReference`, a `call(op)` wrapper, an injected `Clock`, and one half-open probe chosen by `compareAndSet`. Retry in one layer only, outside the breaker, and never on a rejection.",
  "The limit: each of these lives in one program's memory. Two copies of the program have two flags, two bulkheads and two breakers, so a limit for the whole shop needs something they share, such as a lock in the database."
 ],
 "closing": "We started on a busy Saturday: a rail of slips, four packers, twenty phone lines and a van company that went quiet. The rail became a bounded queue with a card for each packer, the phone lines a semaphore, and the fuse box a breaker built from State, Decorator and an atomic reference.\n\nThat ends the track. Look in your own code for a call to another service with no limit around it and no timeout. That call is a van company waiting to go quiet.\n\nNext, we'll look closely at the records we've used all through this track. A record looks like a short way to write a class. What exactly does it promise?",
 "quiz": [
  {"q": "A Java program has four packer threads reading a `BlockingQueue`. After the last slip, the counter puts a single `Closed` card on the rail, then calls `close()` on the executor. What happens?",
   "options": ["All four packers stop, because they all see the card", "One packer stops and the other three keep packing new slips", "One packer stops, three wait in `take()` forever, and `close()` never returns", "The queue throws because a card was taken twice"],
   "answer": 2,
   "why": "`take()` removes the card, so exactly one packer sees it. The other three wait for the next item, which never comes, and `ExecutorService.close()` waits for them. Put one card per packer, or in Kotlin close the channel, which ends every `for` loop."},
  {"q": "The shop's program runs on virtual threads and calls a courier whose booking line takes 50 calls at once. Which limit fits best?",
   "options": ["A semaphore of 50 around the courier call, with `tryAcquire` so extra calls fail fast", "A fixed pool of 50 ordinary threads for the whole program", "No limit: virtual threads are cheap", "A new `CompletableFuture` per call"],
   "answer": 0,
   "why": "The limit belongs to the service, not to the program's threads, and with virtual threads a semaphore is the natural way to say it. A fixed pool of 50 throttles everything the program does, not just the bookings. \"Virtual threads are cheap\" is exactly how you send 5,000 calls to a courier who takes 50."},
  {"q": "In a unit test, a Resilience4j 2.4.0 circuit breaker built with the default settings fails five calls in a row, yet it stays `CLOSED`. Why?",
   "options": ["Resilience4j only counts checked exceptions as failures", "The default `minimumNumberOfCalls` is 100, so the failure rate isn't worked out yet", "Breakers only open after `waitDurationInOpenState` has passed", "The test needs a real clock"],
   "answer": 1,
   "why": "With the defaults, the breaker needs at least 100 recorded calls before it works out a failure rate, so five failures change nothing. Set `minimumNumberOfCalls` and `slidingWindowSize` to small numbers in tests. All exceptions count as failures by default, and `waitDurationInOpenState` controls how long the breaker stays open, not when it opens."},
  {"q": "The shop's stock count runs at closing time and can also be started by the manager. If a count is already running, a second trigger should simply return. Which pattern is this?",
   "options": ["Guarded suspension", "Read-write lock", "Producer-consumer", "Balking"],
   "answer": 3,
   "why": "Balking means: if the object isn't ready for the job, return at once instead of waiting. Guarded suspension is the opposite, waiting until the condition holds, which here would line up a second count behind the first. Build it with `compareAndSet` on an `AtomicBoolean`, and with a shared lock, such as one in the database, if it must be unique across copies of the program."},
  {"q": "From *Atomics and compare-and-set*: when the cool-down ends, many threads find the breaker `Open` with an expired `until` at the same moment. Why must the move to `HalfOpen` be a `compareAndSet` rather than a plain `set`?",
   "options": ["`set` is slower than `compareAndSet`", "So exactly one thread wins the right to probe; with `set`, every thread that saw the expired state would call the service", "`AtomicReference` doesn't allow `set` on records", "`compareAndSet` makes the call to the service atomic"],
   "answer": 1,
   "why": "Each thread read the same `Open` state. `compareAndSet(open, halfOpen)` succeeds for the first thread only, because after that the state is no longer the `Open` object the others read, so their compare-and-set fails and they're turned away. A plain `set` lets all of them through to a service that may still be down. Compare-and-set makes the state change atomic, not the call itself.",
   "from": "conc-08"}
 ],
 "flashcards": [
  {"front": "Why bound a producer-consumer queue?", "back": "A full bounded queue makes producers wait, which is backpressure. An unbounded one hides a pile-up until memory runs out."},
  {"front": "N consumers stop on poison pills. How many pills?", "back": "N, one per consumer: each `take()` removes one pill. In Kotlin, `close()` the channel instead."},
  {"front": "Balking or guarded suspension: which returns at once?", "back": "Balking returns immediately if the object is busy. Guarded suspension waits until the condition holds."},
  {"front": "Bulkhead: `tryAcquire` or `acquire`?", "back": "`tryAcquire`, so a call over the limit fails fast. `acquire` waits in line, which makes it a limiter. Release in `finally` either way."},
  {"front": "Circuit breaker: what happens in each state?", "back": "Closed: calls pass and failures are counted. Open: calls are turned away at once. HalfOpen: one probe runs; success closes, failure opens again."},
  {"front": "Resilience4j 2.4.0 default `minimumNumberOfCalls`?", "back": "100. A default breaker in a unit test that fails a handful of calls never opens."},
  {"front": "Which exceptions should a retry wrapper never retry?", "back": "Fail-fast signals, such as `CallNotPermitted` and a full bulkhead, and any call that isn't safe to run twice."}
 ],
 "terms": [
  {"term": "Producer-consumer", "plain": "Producers put work on a shared queue and consumers take it off; the queue does the locking and waiting."},
  {"term": "Poison pill", "plain": "A special item on a queue that tells one consumer to stop."},
  {"term": "Active object", "plain": "An object whose method calls become messages, run one at a time by its own thread or coroutine."},
  {"term": "Balking", "plain": "Returning at once, instead of waiting, when the object isn't ready, such as \"already running\"."},
  {"term": "Guarded suspension", "plain": "Waiting until a condition holds, then going on: `wait` in a loop, or a future."},
  {"term": "Bulkhead", "plain": "A cap on the calls running against one service at once, so one slow service can't use up everything."},
  {"term": "Circuit breaker", "plain": "A wrapper that stops calling a failing service for a while, then probes to see if it has recovered."},
  {"term": "Half-open", "plain": "The breaker's state after the cool-down, where one probe call decides whether it closes or opens again."}
 ],
 "explain_back": {
  "prompt": "Explain how the lab's circuit breaker combines State, Decorator and compare-and-set, and why the move from open to half-open has to be a `compareAndSet`.",
  "answer": "The breaker's state is a small sealed type, `Closed(failures)`, `Open(until)` and `HalfOpen`, and each outcome moves it with a pure transition, like the order's life in *State and Chain of Responsibility*. That's State. Its `call(op)` takes any operation and returns that operation's result through the same shape, adding behavior around it, which is what a decorator does. The current state lives in an `AtomicReference`, so hundreds of threads can share one breaker without a lock, and every change is a `compareAndSet` or an `updateAndGet`. The open-to-half-open move matters most. When the cool-down ends, many threads may read the same expired `Open` state at once. `compareAndSet(thatOpen, new HalfOpen())` succeeds for exactly one of them, which becomes the probe; the others see their compare-and-set fail and are turned away. With a plain `set`, every one of them would call a service that may still be down. The injected `Clock` is what lets the tests check all this without sleeping."
 },
 "deeper": {
  "minutes": 12,
  "body": """Resilience4j's breaker defaults, read from its source and printed by version 2.4.0: `failureRateThreshold` 50%, `slowCallRateThreshold` 100%, `slowCallDurationThreshold` 60 s, `waitDurationInOpenState` 60 s, `permittedNumberOfCallsInHalfOpenState` 10, `minimumNumberOfCalls` 100, and a count-based sliding window of 100 calls. Every exception counts as a failure unless you configure `recordExceptions` or `ignoreExceptions`. The project's README says Resilience4j 3 will require Java 21 and adds virtual-thread schedulers; it wasn't on Maven Central when this course was written, so the labs build the breaker by hand.

Spring Framework 7, a widely used framework for Java web services, added `@Retryable` and `@ConcurrencyLimit` to its core, switched on with `@EnableResilientMethods`. `@Retryable` defaults to `maxRetries = 3` after the first failure, so four attempts in total, with a one-second delay. Both work through proxies, so the self-call rule from *Decorator and Proxy* applies: a method that calls another method on `this` skips them.

Structured concurrency is the future pattern with a lifetime. `StructuredTaskScope` starts subtasks, waits for them, and cancels the rest when one fails, so no subtask outlives the method that started it. It is still a preview API in JDK 25, 26 and 27 (run with `--enable-preview`), which is why it stays out of the labs. Kotlin's `coroutineScope` has worked this way from the start: an `async` that fails cancels its siblings, and the scope waits for every child.

The patterns in this lesson have cousins that span several programs. A lock held in a shared database is balking across copies of a program. A queue server, a separate program that holds messages until other programs take them, is producer-consumer between programs. The questions stay the same: who owns the state, what waits, and what fails fast."""
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
