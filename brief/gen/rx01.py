import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l01"
PK = "kotlin/workbench/reactive/l01"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l01."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """There are two ways to get your bread. You can walk to the bakery whenever you want a loaf, but if the shelf is empty, you stand at the counter and wait. Or the bakery can leave a loaf at your door every morning. Nobody waits, but the bakery decides how much comes. Go away for two weeks and you come home to fourteen loaves on the step, the oldest turning green.

Programs move data the same two ways, with the same flaw in the second. A fast sender keeps sending, a slow receiver falls behind, and the extra items pile up in memory. It's an easy trap: every test with ten items passes.

Serve it with virtual threads ended Part 1 with a ledger that said "busy" once its queue was full, and a question: what if the receiver could tell the sender how much it can take, before it fills up? In this lesson, we'll watch a fast oven drown a slow packer and give the packer a way to say "send me 10 more". Then we'll read the contract behind that note and weigh its costs. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_PUSH = """// Naive: the oven never waits, so the packer's queue grows without limit
ExecutorService packer = Executors.newSingleThreadExecutor();
for (int i = 0; i < LOAVES; i++) {
    packer.execute(() -> packLoaf());   // returns at once; the loaf waits in the queue
}"""
K_PUSH = """// Naive: the oven never waits, so the packer's queue grows without limit
val packer = Executors.newSingleThreadExecutor()
repeat(LOAVES) {
    packer.execute { packLoaf() }       // returns at once; the loaf waits in the queue
}"""

S0 = """Every stream of data has two ends. A **producer** is the code that makes items, and a **consumer** is the code that uses them. Between the two, something has to decide when the next item moves.

In **pull**, the consumer asks for the next item when it's ready, like walking to the bakery. `Iterator.next()` works that way, and so does `BufferedReader.readLine()`. The consumer sets the pace. The cost is waiting: if the next item isn't there yet, the consumer's thread, one path of work in a program, sits and does nothing.

In **push**, the producer hands over each item the moment it exists, like the morning delivery. The consumer gives the producer a **callback**, a method to call when something arrives, and goes about its day. `CompletableFuture.thenAccept` works that way. Nobody waits. The cost is that the producer sets the pace, and the consumer has no way to say "slow down".

Let's set up the example this track uses from here on. Picture a bakery line. At one end, an oven bakes loaves. A belt carries them, one behind another. At the other end, a packer puts each loaf in a box. The oven is the producer, the packer is the consumer, and the belt is the stream between them. Our oven is fast. It can bake loaves far faster than anyone can box them.

Here is plain push in code. The oven hands each loaf to the packer's executor, the JDK object from the executors track that runs tasks on its own thread. Tasks it can't run yet wait in its queue:

""" + pair(J_PUSH, K_PUSH) + """

`execute` puts the task in the queue and returns at once, so the oven never waits. `DrowningDemo`, in the Try it below, bakes 100,000 loaves this way, with 10 microseconds of packing per loaf. I expected the oven to finish long before the packer. On this 4-core machine, while other programs were busy, one run printed:

```text
plain push:  oven done in    65 ms, packer boxed   3,193, 96,807 loaves waiting in memory
```

The oven finished in 65 ms and went home happy. The packer had boxed 3,193 loaves, and 96,807 waited in the queue.

Each waiting loaf is an object on the **heap**, the memory where Java keeps its objects. Here they fit, because the demo stops at 100,000. A real oven doesn't stop. With 10,000 loaves a second coming in and 2,000 going out, the heap gains 8,000 objects every second. Nothing fails at first. Then the garbage collector, the part of the JVM that frees memory nobody uses, runs more and more often, everything slows down, and the program dies with `OutOfMemoryError`.

The cure is the note on the doorstep. **Backpressure** means the consumer tells the producer how much it can take, and the producer never sends more. On the bakery line, the packer sends a slip back up the belt: "send me 10 more". The oven puts 10 loaves on the belt, then waits for the next slip.

The second half of `DrowningDemo` does exactly that, with the JDK's `SubmissionPublisher`, a ready-made producer we'll meet properly in the third section. This time the packer asks for one loaf at a time. The same run went on:

```text
with demand: oven done in 1,521 ms, packer boxed  99,898, never more than 257 waiting
```

Never more than 257 loaves waited, about the 256 that the publisher's buffer holds. The last 102 were still on the belt when the oven finished, and the packer boxed them a moment later. The oven took 1,521 ms instead of 65, because it now works at the packer's pace. That isn't a loss. The packing took that long in both halves; the first half just hid the work in memory.

Notice the shape of the slip. If loaves are already waiting, they go to the packer at once, as with pull. If none are ready, the oven sends each one as soon as it's baked, as with push. The documentation of Reactor, the library this track uses from the next lesson on, calls this a push-pull hybrid.

When a consumer can't keep up, a program has four honest choices: slow the producer down, buffer up to a limit, drop items, or fail. A queue with no limit is a fifth choice that only looks like one, because it postpones the failure instead of choosing.

**A queue with no limit only hides a slow consumer. Give the slowness somewhere to go.**

The belt picture breaks in one place, and the place matters. A real belt keeps rolling whether the packer is ready or not, which is the plain push we just watched fail. On a reactive belt, nothing moves without a slip. So the slip is the whole idea, and it comes with a short contract that says exactly how it works."""

# ---------------------------------------------------------------- section 1
J_API = """public interface Publisher<T>    { void subscribe(Subscriber<? super T> s); }
public interface Subscriber<T>   { void onSubscribe(Subscription s);
                                   void onNext(T item);
                                   void onError(Throwable t);
                                   void onComplete(); }
public interface Subscription    { void request(long n); void cancel(); }
public interface Processor<T, R> extends Subscriber<T>, Publisher<R> { }"""
K_API = """// the same four interfaces, written as Kotlin declarations
interface Publisher<T>    { fun subscribe(s: Subscriber<in T>) }
interface Subscriber<T>   { fun onSubscribe(s: Subscription)
                            fun onNext(item: T)
                            fun onError(t: Throwable)
                            fun onComplete() }
interface Subscription    { fun request(n: Long); fun cancel() }
interface Processor<T, R> : Subscriber<T>, Publisher<R>"""

S1 = """A slip only works if both ends read it the same way. One library's oven must be able to serve another library's packer. **Reactive Streams** is that agreement: a short **specification**, a written contract that libraries promise to follow, with four interfaces, seven methods and a list of numbered rules. Here is the whole API:

""" + pair(J_API, K_API) + """

Each interface has a place on the bakery line. A **publisher** is the oven, the source of items. A **subscriber** is the packer, which receives them. A **subscription** is the pad of slips between one oven and one packer: it carries `request(n)`, "send me n more", and `cancel()`, "stop sending". A `Processor` is a station in the middle of the belt, a subscriber to what comes before it and a publisher to what comes after.

Every method returns `void` (`Unit` in Kotlin), so every call is a one-way message, called a **signal**: the caller never waits for an answer. Java's `Subscriber<? super T>` is Kotlin's `Subscriber<in T>`. Both say that a publisher of rye loaves also accepts a subscriber of any kind of bread, or even a `Subscriber<Object>` that logs everything.

The figure below draws one conversation. The packer calls `subscribe` on the oven. The oven answers with `onSubscribe` and hands over the pad of slips. Nothing else happens until the packer writes a slip, say `request(2)`. Then the oven may call `onNext` twice, once per loaf, and no more. When the oven is out of loaves for good, it calls `onComplete`, the bell at the end of the day. If it breaks down, it calls `onError` instead.

The spec writes that order as `onSubscribe onNext* (onError | onComplete)?`. Read it as one `onSubscribe`, then any number of `onNext`, then at most one of the two endings. `onError` and `onComplete` are **terminal signals**: after one of them, the stream is over and nothing else arrives.

Here are the rules you'll actually meet, each in plain words:

- **1.1** A publisher never sends more `onNext` signals than were requested in total.
- **1.3** Signals to one subscriber never overlap; they come one at a time. So a subscriber needs no locks, the guards from Part 1 that let one thread in at a time, for its own fields.
- **1.9** `onSubscribe` comes before any other signal.
- **2.13** Subscriber methods must return normally. The only exception allowed is a `NullPointerException` for a `null` argument. A subscriber that wants to stop must call `cancel()`, not throw. An exception from `onNext` lands inside the publisher's delivery code, which can't hand it back. So the spec has the publisher treat the subscription as cancelled and report the problem some other way, such as a log line.
- **2.8** A subscriber must accept `onNext` calls that arrive after it cancelled, because loaves it already asked for may still be on the belt.
- **3.9** `request(n)` with `n <= 0` must produce `onError(IllegalArgumentException)`.
- **3.17** Demand of `Long.MAX_VALUE` may be treated as unbounded: a packer saying it wants no backpressure at all.

You will rarely write these interfaces by hand. Reactor, RxJava and some database drivers implement them, and the rules are why one library can subscribe to another.

**Demand is the only permission to send. No slip, no loaf.**

Rule 3.9 is a good place to see that a spec and a library can differ. `RequestZeroDemo`, in the Try it below, has a subscriber named `Rude` that asks for zero items. It subscribes once to the JDK's publisher and once to `Flux.range(1, 3)` from Reactor:

```text
JDK SubmissionPublisher: onError java.lang.IllegalArgumentException: non-positive subscription request
Reactor Flux.range: no signal at all, the stream just stalls
```

The JDK complains at once, as the rule says. Reactor only logs the bad request at DEBUG level, which nobody sees by default, and sends nothing. Its stream simply waits. A stream that stalls in silence is a symptom to remember: somewhere, a slip was never written.

Here the bakery picture breaks again. A real packer who stopped sending slips would be missed by lunchtime. In code, unmet demand never times out by itself.

The contract so far is only interfaces. The JDK carries its own copy of them, and one real publisher you can run today."""

SVG = ('<svg viewBox="0 0 640 380" role="img" aria-label="Sequence of signals: the subscriber subscribes, receives onSubscribe, '
       'requests 2, gets two loaves with onNext, requests 2 more, gets one loaf and then onComplete">'
       '<rect class="box-b" x="60" y="14" width="180" height="40" rx="8"/><text class="t" x="150" y="39" text-anchor="middle">Publisher: the oven</text>'
       '<rect class="box-a" x="400" y="14" width="180" height="40" rx="8"/><text class="t" x="490" y="39" text-anchor="middle">Subscriber: the packer</text>'
       '<line class="ln-d" x1="150" y1="54" x2="150" y2="366"/><line class="ln-d" x1="490" y1="54" x2="490" y2="366"/>'
       '<text class="t-s t-m" x="600" y="74" text-anchor="middle">owed</text>')
rows = [
    (92, "subscribe(subscriber)", "left", "ln", ""),
    (130, "onSubscribe(subscription)", "right", "ln", "0"),
    (168, "request(2): the slip", "left", "ln-a", "2"),
    (206, "onNext(loaf-1)", "right", "ln", "1"),
    (244, "onNext(loaf-2)", "right", "ln", "0"),
    (282, "request(2)", "left", "ln-a", "2"),
    (320, "onNext(loaf-3)", "right", "ln", "1"),
    (358, "onComplete(): end of the day", "right", "ln", ""),
]
for y, label, d, cls, owed in rows:
    x1, x2 = (490, 156) if d == "left" else (150, 484)
    tcls = "t-s t-code t-a" if cls == "ln-a" else "t-s t-code"
    SVG += f'<line class="{cls}" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'
    SVG += f'<text class="{tcls}" x="320" y="{y - 7}" text-anchor="middle">{label}</text>'
    if owed:
        SVG += f'<text class="t-s t-a" x="600" y="{y + 4}" text-anchor="middle">{owed}</text>'
SVG += '</svg>'

# ---------------------------------------------------------------- section 2
J_SP = """try (var oven = new SubmissionPublisher<Loaf>()) {
    oven.subscribe(new BatchingSubscriber<>(32, packer::box));   // asks for 32 at a time
    for (Loaf loaf : todaysLoaves) {
        oven.submit(loaf);       // waits while this packer is 256 loaves behind
    }
}   // close(): each subscriber gets onComplete after the loaves already on its belt"""
K_SP = """SubmissionPublisher<Loaf>().use { oven ->
    oven.subscribe(BatchingSubscriber(32, packer::box))         // asks for 32 at a time
    for (loaf in todaysLoaves) {
        oven.submit(loaf)        // waits while this packer is 256 loaves behind
    }
}   // close(): each subscriber gets onComplete after the loaves already on its belt"""

S2 = """Java 9 copied the four interfaces into the JDK, as nested types of `java.util.concurrent.Flow`: `Flow.Publisher`, `Flow.Subscriber`, `Flow.Subscription` and `Flow.Processor`. Same methods, same rules, different package. Reactor works with the `org.reactivestreams` copies, so you bridge between the two with `JdkFlowAdapter` (in reactor-core) or `FlowAdapters` (in the reactive-streams jar). `RequestZeroDemo` used the first one.

The JDK ships one real publisher, `SubmissionPublisher`. You hand it items from ordinary code, and it delivers them to each subscriber on another thread. Here it is with the lab's `BatchingSubscriber`, a packer that asks for loaves 32 at a time:

""" + pair(J_SP, K_SP) + """

The parts that matter, mapped onto the belt:

- Each subscriber gets its own **buffer**, its own stretch of belt where loaves wait to be delivered. It holds up to `Flow.defaultBufferSize()` items, which is 256.
- Delivery runs on an `Executor`. By default that is `ForkJoinPool.commonPool()`, a pool of threads the whole JDK shares. Pass your own executor for anything slow.
- `submit(item)` **blocks the producer's thread** while a subscriber's buffer is full: the baker stands at a full belt and waits. This is where backpressure becomes something an ordinary thread can feel. In the first Try it, `submit` is what slowed the oven to the packer's pace.
- `offer(item, onDrop)` never blocks. When a buffer is full, it calls your drop handler and returns a negative number. There is also an `offer` with a timeout.
- If a subscriber method throws, the publisher cancels that subscription.
- `close()` completes every subscriber, and `closeExceptionally(t)` sends them `onError(t)`.

`SaturationDemo`, in the Try it, builds a publisher with a belt of just 2 slots and a packer that never writes a slip. Then it offers 10 loaves:

```text
offer(1) -> 1
offer(2) -> 2
offer(3) -> -1
...
offer(10) -> -1
dropped 8 of 10, lag 2
```

The first two offers fill the belt, and `offer` returns the lag, the number of items waiting. The other eight are dropped, because the belt is full and nobody asked for anything. Not one loaf reached the packer. No slip, no loaf, even with loaves sitting right there.

Blocking in `submit` is fine on a thread of its own, or on a virtual thread from Part 1. It's a bad idea on an **event loop**, a single thread that serves many connections by never waiting, which the next section explains. There, one blocked `submit` stalls everything else the loop serves.

`SubmissionPublisher` is a good teaching tool, and a decent way to hand items to several subscribers inside one program. But it has no **operators**, the methods that add a station to the belt, such as one that slices every loaf. You can't transform, retry or time out a `Flow.Publisher` without writing that code yourself. Reactor does that job, from the next lesson on.

Before we take on a whole library, though, a fair question: why not just block and wait?"""

ASIDE = {
    "title": "Is this Flow the same as Kotlin's Flow?",
    "body": "No, and the shared name causes real confusion. `java.util.concurrent.Flow` is the Reactive Streams protocol, with `request(n)`. `kotlinx.coroutines.flow.Flow` is a coroutine stream with no `request` at all: its `emit` suspends, that is, pauses without holding a thread, until the collector has finished with the item, so a producer can never run ahead. Both protect a slow consumer, by different means. The `kotlinx-coroutines-reactive` library converts between them with `asFlow()` and `asPublisher()`, and the coroutines track covers Kotlin's `Flow`.",
}

# ---------------------------------------------------------------- section 3
S3 = """Here is what blocking costs. Say the bakery's program asks a supplier's web service how much flour is left, and the answer takes 120 ms to come back. The thread that makes the call blocks: for 120 ms it holds about a megabyte of memory for its stack, and does no work.

So the number of threads caps the number of calls. **Little's law** says that the calls in flight equal the calls per second times the time each call takes. Turn it around: 200 threads, each holding a call for 0.12 s, finish at most 200 / 0.12 s, about 1,670 calls a second, however idle the processors are.

**Non-blocking I/O** removes the wait. The thread hands the request to the operating system and moves on to other work. When the answer arrives, the operating system tells the program, and a callback carries on where the request left off. An event loop works this way: one thread, many calls in flight, and never a wait. A handful of threads can keep thousands of calls going.

Reactive libraries are the way to write code for that world of callbacks without drowning in them. In Reactor, a `Mono` is the one answer you're waiting for, a `Flux` is a stream of answers, and demand, the slip, travels with the data.

The style has real costs, and its own makers say so. The Spring Framework is a widely used toolkit for building Java web services, and the home of Reactor. Its documentation puts it plainly: "Reactive and non-blocking generally do not make applications run faster." The gain is "the ability to scale with a small, fixed number of threads and less memory", and you only see it when calls take time.

You also pay in other ways. Stack traces show library internals instead of your code. Everyone on the team has to learn a new way of thinking. And one rule is strict: nothing on an event loop may block. A single blocking database call on an event-loop thread stalls every request that loop serves.

Virtual threads (final in JDK 21) changed the trade. Part 1 showed that a blocked virtual thread lets go of its carrier, the platform thread that runs it. So blocking code no longer ties up a thread of the operating system per call. For a plain request and response, blocking code on virtual threads is now the simpler default.

Reactive code still earns its place where the problem really is a stream. Think of backpressure, cancellation that travels back to the source, a cap on how many calls run at once, and retries and timeouts you add like stations on a belt. Lesson 8 of this track comes back to this choice.

Quick check: the bakery's program makes 3,000 supplier calls a second, and each takes 120 ms. How many calls are in flight at any moment, and how many threads does each model need? (Little's law gives 3,000 x 0.12 s = 360 calls in flight. Blocking needs 360 threads, one parked per call. An event loop needs a handful, because no thread waits for an answer.)"""

# ---------------------------------------------------------------- closing
CLOSING = """We started with fourteen loaves on a doorstep. A program has the same problem when a fast producer pushes into a queue with no limit, and the same cure: a note that says how much to send. In Reactive Streams that note is `request(n)`, and a publisher may never send more than it was asked for.

Now look in your own code for `newFixedThreadPool`, `newSingleThreadExecutor` or a `LinkedBlockingQueue` made without a size. Ask what happens when the code that empties it falls behind the code that fills it.

Next, we'll meet Reactor's `Mono` and `Flux`. Our oven started baking the moment it existed. Why does a Reactor publisher do nothing at all until someone subscribes?"""

# ---------------------------------------------------------------- worked example and drill twins
W0J = """class ReportSubscriber implements Flow.Subscriber<Order> {
    private Flow.Subscription s;

    public void onSubscribe(Flow.Subscription s) {
        this.s = s;
        s.request(Long.MAX_VALUE);
    }
    public void onNext(Order order) {
        if (order.total() == null) throw new IllegalStateException("bad order " + order.id());
        file.append(order.toLine());
    }
    public void onError(Throwable t) { s.request(1); }   // "try again"
    public void onComplete() { file.close(); }
}"""
W0K = """class ReportSubscriber : Flow.Subscriber<Order> {
    private lateinit var s: Flow.Subscription

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(Long.MAX_VALUE)
    }
    override fun onNext(order: Order) {
        if (order.total == null) throw IllegalStateException("bad order ${order.id}")
        file.append(order.toLine())
    }
    override fun onError(t: Throwable) = s.request(1)   // "try again"
    override fun onComplete() = file.close()
}"""
W2J = """class ReportSubscriber implements Flow.Subscriber<Order> {
    private Flow.Subscription s;
    private boolean stopped;
    volatile Throwable failure;

    public void onSubscribe(Flow.Subscription s) {
        this.s = s;
        s.request(1);                          // 1. bounded demand
    }
    public void onNext(Order order) {
        if (stopped) return;                   // 2. rule 2.8: late items may still come
        if (order.total() == null) {
            stopped = true;
            failure = new IllegalStateException("bad order " + order.id());
            s.cancel();                        // 3. stop by cancelling, never by throwing
            return;
        }
        file.append(order.toLine());
        s.request(1);                          // 4. ask for the next one when done
    }
    public void onError(Throwable t) { failure = t; file.close(); }   // 5. terminal: just clean up
    public void onComplete() { file.close(); }
}"""
W2K = """class ReportSubscriber : Flow.Subscriber<Order> {
    private lateinit var s: Flow.Subscription
    private var stopped = false
    @Volatile var failure: Throwable? = null

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)                               // 1. bounded demand
    }
    override fun onNext(order: Order) {
        if (stopped) return                        // 2. rule 2.8: late items may still come
        if (order.total == null) {
            stopped = true
            failure = IllegalStateException("bad order ${order.id}")
            s.cancel()                             // 3. stop by cancelling, never by throwing
            return
        }
        file.append(order.toLine())
        s.request(1)                               // 4. ask for the next one when done
    }
    override fun onError(t: Throwable) { failure = t; file.close() }   // 5. terminal: just clean up
    override fun onComplete() = file.close()
}"""
DJ = """class StopAtBurnt implements Flow.Subscriber<String> {
    private Flow.Subscription s;
    private boolean stopped;

    public void onSubscribe(Flow.Subscription s) {
        this.s = s;
        s.request(1);
    }
    public void onNext(String loaf) {
        if (stopped) return;                 // rule 2.8
        if (loaf.startsWith("burnt")) {
            stopped = true;
            s.cancel();                      // rule 2.13: cancel, don't throw
            return;
        }
        System.out.println("boxed " + loaf);
        s.request(1);
    }
    public void onError(Throwable t) { t.printStackTrace(); }
    public void onComplete() { System.out.println("done"); }
}"""
DK = """class StopAtBurnt : Flow.Subscriber<String> {
    private lateinit var s: Flow.Subscription
    private var stopped = false

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)
    }
    override fun onNext(loaf: String) {
        if (stopped) return                        // rule 2.8
        if (loaf.startsWith("burnt")) {
            stopped = true
            s.cancel()                             // rule 2.13: cancel, don't throw
            return
        }
        println("boxed $loaf")
        s.request(1)
    }
    override fun onError(t: Throwable) = t.printStackTrace()
    override fun onComplete() = println("done")
}"""
CJ = """oven.subscribe(new Flow.Subscriber<Loaf>() {
    private Flow.Subscription s;

    public void onSubscribe(Flow.Subscription s) {
        this.s = s;
        s.request(1);                    // the first slip: one loaf
    }
    public void onNext(Loaf loaf) {
        packer.box(loaf);                // slow work
        s.request(1);                    // only now ask for the next
    }
    public void onError(Throwable t) { log.error("the oven stopped", t); }
    public void onComplete() { log.info("all loaves boxed"); }
});"""
CK = """oven.subscribe(object : Flow.Subscriber<Loaf> {
    private lateinit var s: Flow.Subscription

    override fun onSubscribe(s: Flow.Subscription) {
        this.s = s
        s.request(1)                     // the first slip: one loaf
    }
    override fun onNext(loaf: Loaf) {    // non-null type: Kotlin itself throws NPE on null
        packer.box(loaf)                 // slow work
        s.request(1)                     // only now ask for the next
    }
    override fun onError(t: Throwable) = log.error("the oven stopped", t)
    override fun onComplete() = log.info("all loaves boxed")
})"""

L = {
 "id": "rx-01",
 "title": "Why reactive: push, pull and backpressure",
 "minutes": 35,
 "goal": "By the end you can explain how Reactive Streams demand (`request(n)`) stops a fast producer from drowning a slow consumer, name the rules a subscriber must follow, and write a `Flow.Subscriber` that asks for items in batches.",
 "opening": OPENING,
 "warmup": {
  "q": "A bakery's program has a fast oven and a slow packer. The oven bakes 10,000 loaves a second and hands each one to the packer's thread pool (a few threads that take tasks from a queue), which boxes 2,000 a second. The pool's queue has no size limit. What happens over the next few minutes?",
  "options": [
   "The oven slows down to 2,000 loaves a second on its own",
   "The pool refuses the extra loaves with `RejectedExecutionException`",
   "Loaves pile up in the pool's queue, about 8,000 more each second, until memory runs out",
   "The packer's thread speeds up to keep pace"
  ],
  "answer": 2,
  "why": "A queue with no limit never says no and never pushes back. `Executors.newFixedThreadPool` and `newSingleThreadExecutor` both use one. The oven's call to `execute` returns at once, so nothing tells the oven to slow down, and the queue grows by the difference, 8,000 loaves a second, until the program runs out of memory. A pool refuses work only when its queue is full, and this queue never is."
 },
 "sections": [
  {
   "h": "Pull, push, and a fast oven that drowns a slow packer",
   "body": S0,
   "try": {
    "title": "Drown a packer, then rescue it",
    "minutes": 4,
    "steps": [
     "Read `DrowningDemo` below. It sends 100,000 loaves to a packer that needs 10 microseconds per loaf, first with plain push, then through a `SubmissionPublisher` whose subscriber asks for one loaf at a time.",
     "Predict for each half: how long will the oven take, and how many loaves will be waiting when it finishes?",
     "Run it (the Java and Kotlin versions print the same lines). Then change `packLoaf` to wait 20,000 nanoseconds instead of 10,000, and run it again. Which number changes in each line?"
    ],
    "code": demo("DrowningDemo"),
    "expect": "With plain push the oven finishes in tens of milliseconds and almost every loaf is still queued (runs here: 32 to 73 ms, with 96,807 to 99,180 loaves waiting). With demand the oven takes as long as the packer needs (1,272 to 1,521 ms here), and never more than about 256 loaves wait, the size of the publisher's buffer. With 20 microseconds of packing, the plain version leaves even more loaves queued, and the demand version simply takes about twice as long. Its memory stays flat."
   }
  },
  {
   "h": "Reactive Streams: four interfaces, seven methods and a slip called request(n)",
   "body": S1,
   "figure": {"svg": SVG, "caption": "Demand goes up as request(n), the packer's slip, and loaves come down as onNext. The publisher never sends more than it is owed."},
   "try": {
    "title": "Break rule 3.9 on purpose",
    "minutes": 3,
    "steps": [
     "`RequestZeroDemo` has a subscriber that calls `request(0)` in `onSubscribe`. It subscribes to a JDK `SubmissionPublisher` and to a Reactor `Flux.range(1, 3)`.",
     "Predict what each publisher sends back. Then run it.",
     "Change `request(0)` to `request(2)`. Predict again: does each stream complete?"
    ],
    "code": demo("RequestZeroDemo"),
    "expect": "The JDK publisher follows rule 3.9 and prints `onError java.lang.IllegalArgumentException: non-positive subscription request`. Reactor prints nothing at all: the stream just stalls. With `request(2)`, the JDK publisher sends its one item and then `onComplete`, because it was closed. Reactor sends 1 and 2 and then stops without completing, because nobody asked for 3. Unmet demand never times out by itself."
   },
   "refs": [{"title": "Reactive Streams for the JVM: specification and rules", "url": "https://github.com/reactive-streams/reactive-streams-jvm/blob/master/README.md", "kind": "docs"}]
  },
  {
   "h": "Flow and SubmissionPublisher: the same contract inside the JDK",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "Fill a two-slot belt",
    "minutes": 4,
    "steps": [
     "`SaturationDemo` builds a `SubmissionPublisher` with a buffer of 2 and a subscriber that never calls `request`. Then it offers 10 items.",
     "Predict what each `offer` returns and how many items are dropped. Run it.",
     "Now replace the `offer(...)` call with `publisher.submit(i)`, and keep the assignment to `lag`. Predict, then run it. Stop it with Ctrl+C."
    ],
    "code": demo("SaturationDemo"),
    "expect": "The first two offers return a lag of 1 and 2. Offers 3 to 10 each return -1, the drop handler runs eight times, and the last line is `dropped 8 of 10, lag 2`. Nothing is delivered, because nothing was requested. With `submit` the program hangs on item 3: the buffer is full, the subscriber never asks for more, and `submit` waits for space. That hang is backpressure reaching your thread."
   },
   "refs": [
    {"title": "Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html", "kind": "docs"},
    {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html", "kind": "docs"}
   ]
  },
  {
   "h": "What non-blocking buys you, and what it costs",
   "body": S3,
   "refs": [{"title": "Spring Framework reference: WebFlux overview (applicability and performance)", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html", "kind": "read"}]
  }
 ],
 "compare": {
  "title": "A one-at-a-time Flow.Subscriber in Java and Kotlin",
  "java": {"title": "OneAtATime.java", "src": CJ},
  "kotlin": {"title": "OneAtATime.kt", "src": CK},
  "note": "The protocol code is the same in both languages, and three Kotlin details change how it feels. `lateinit var s` replaces the nullable field you would otherwise check. `object : Flow.Subscriber<Loaf>` is Kotlin's anonymous class. And because `onNext(loaf: Loaf)` declares a non-null parameter, the Kotlin compiler adds a null check to it: a publisher that sends `null` gets a `NullPointerException`, which is exactly what rule 2.13 asks for, with no code from you. In Java, `Objects.requireNonNull(loaf)` does the same job by hand. Neither language protects you from the bigger mistake, asking for `Long.MAX_VALUE` in `onSubscribe`, which switches backpressure off."
 },
 "worked": {
  "title": "Find the broken rules in a hand-written subscriber",
  "steps": [
   {"say": "A teammate wrote this subscriber. It receives the day's cake orders from the order book and writes one line per order to a report file. Read it and look for broken rules before you read on.",
    "code": W0J, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Three problems. `request(Long.MAX_VALUE)` turns backpressure off (rule 3.17), so a slow disk makes the publisher pile orders up in memory. Throwing from `onNext` breaks rule 2.13: the publisher may cancel, log, or do something you didn't expect. And calling `request` from `onError` breaks rule 2.3: after a terminal signal the subscription is dead, and talking to it does nothing useful.", "code": "", "lang": ""},
   {"say": "Fix them one at a time. Ask for one order at a time. Turn a bad order into a cancel plus a recorded error. Treat `onError` as the end.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "This version is correct but chatty: one `request(1)` per order. Each call crosses into the publisher, and some publishers do real work per request. The lab asks for the same correctness with demand in batches, which is what Reactor's own operators do inside.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A Flow.Subscriber that asks in batches",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/BatchingSubscriber.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l01.*'",
  "steps": [
   "Run the tests once. All five fail. Two show the `TODO` message. The three that use a real `SubmissionPublisher` wait 3 seconds and fail on `[stream finished]`, because the `TODO` exception is thrown on the publisher's thread and never reaches the test.",
   "Write `onSubscribe`: keep the subscription and call `request(batchSize)`. If a subscription is already stored, cancel the new one and return.",
   "Write `onNext`: reject `null`, pass the item to the handler, count it, and call `request(batchSize)` again only when a whole batch has been handled.",
   "Make a throwing handler safe: catch the exception, cancel the subscription, record the error, count down `done`, and ignore any later `onNext`.",
   "Write `onError` and `onComplete` so that `await` returns. Run the tests until all five pass."
  ],
  "hints": [
   "You need two more fields: an `int` counting the items handled in the current batch, and a `boolean` that says you have cancelled. Signals never overlap (rule 1.3), so plain fields are safe here.",
   "The request test expects exactly `[4, 4, 4]` for 10 items in batches of 4. If you see eleven requests, you are asking after every item. If you see `[4]`, you never reset the counter.",
   "`Objects.requireNonNull(item)` is all rule 2.13 asks for on `null`."
  ],
  "done_when": "All five tests in `BatchingSubscriberTest` pass."
 },
 "drill": {
  "title": "Write a one-at-a-time subscriber from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a `Flow.Subscriber<String>` that requests one loaf at a time, prints each one, and cancels the subscription (without throwing) at the first loaf whose name starts with `\"burnt\"`. Then compare with the answer. Did you guard against loaves that arrive after the cancel?",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "Pull lets the consumer set the pace but parks a thread while it waits. Push never waits, but a fast producer can drown a slow consumer in a queue with no limit.",
  "Backpressure means the consumer says how much it can take (`request(n)`), and the producer never sends more (rule 1.1).",
  "Signals arrive as `onSubscribe onNext* (onError | onComplete)?`, one at a time. A subscriber stops by calling `cancel()`, never by throwing.",
  "`java.util.concurrent.Flow` is the same contract in the JDK. `SubmissionPublisher.submit` blocks when a subscriber's 256-item buffer is full; `offer` drops instead.",
  "Reactor ignores `request(0)` silently, while the JDK reports it as `onError`. A stream with unmet demand just stalls.",
  "The limits: `SubmissionPublisher` has no operators, and non-blocking code is not faster. It scales with few threads only when calls wait, and virtual threads now cover plain request and response well."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A subscriber calls `request(3)` in `onSubscribe` and never calls `request` again. The publisher has 10 items ready. What does the subscriber receive?",
   "options": ["All 10 items, because the publisher has them ready", "3 items, then `onComplete`", "3 items, and then nothing until it requests more", "1 item, because each `onNext` needs its own request"],
   "answer": 2,
   "why": "Rule 1.1 caps `onNext` signals at the total requested. The publisher still has items to send, so it may not complete either: it waits for more demand. Having items ready never lets a publisher send more than it was asked for."},
  {"q": "Inside `onNext`, your handler fails on a bad order. What should the subscriber do?",
   "options": ["Throw the exception so the publisher can call `onError`", "Call `subscription.cancel()`, record the error, and return normally", "Call `request(0)` to signal a problem", "Ignore it and call `request(1)` to get the next order"],
   "answer": 1,
   "why": "Rule 2.13 says subscriber methods must return normally, and cancelling is the legal way for a subscriber to stop the stream. Throwing leaves the reaction up to the publisher (`SubmissionPublisher` cancels; others may only log it), and `request(0)` breaks rule 3.9 itself."},
  {"q": "An oven thread calls `SubmissionPublisher.submit(loaf)` in a loop. One subscriber is slow, and its buffer of 256 is full. What happens?",
   "options": ["`submit` blocks until that subscriber has room", "`submit` drops the loaf and returns -1", "`submit` throws `IllegalStateException`", "The loaf goes to the other subscribers only"],
   "answer": 0,
   "why": "`submit` blocks while any subscriber's buffer is full, which slows the producer to the slowest subscriber's pace. `offer` is the method that drops instead and returns a negative number. Pick `offer` with a drop handler if the producer must never wait."},
  {"q": "Which of these is the strongest reason to choose a non-blocking, reactive design for a program?",
   "options": ["Each request will finish faster", "It is easier to debug than blocking code", "It removes the need for timeouts", "It can keep thousands of slow calls in flight with a few threads and little memory"],
   "answer": 3,
   "why": "The Spring docs say reactive code generally doesn't run faster. The gain is scale with a small, fixed number of threads, and it shows only when calls really wait. Debugging is harder, not easier, and slow calls still need timeouts."},
  {"q": "From \"How virtual threads work: carriers and continuations\": a virtual thread calls a slow web service over a socket and waits 120 ms for the answer. What does its carrier thread do during the wait?",
   "options": ["It blocks for 120 ms, like a platform thread", "The JVM creates a new carrier thread for the other virtual threads", "It unmounts the waiting virtual thread and runs other virtual threads", "The call throws, because virtual threads cannot block"],
   "answer": 2,
   "why": "A blocking socket read parks the virtual thread and frees the carrier to run other virtual threads. That's why blocking code on virtual threads scales without a reactive rewrite. The scheduler doesn't add carriers for ordinary network waits.",
   "from": "vt-02"}
 ],
 "flashcards": [
  {"front": "What does `request(n)` promise the subscriber?", "back": "That the publisher will send at most `n` more `onNext` signals (rule 1.1). It may send fewer and then complete or fail."},
  {"front": "In what order can a Reactive Streams subscriber see signals?", "back": "`onSubscribe onNext* (onError | onComplete)?`: one `onSubscribe`, any number of `onNext`, then at most one terminal signal."},
  {"front": "How does a subscriber stop a stream when its handler fails?", "back": "It calls `subscription.cancel()` and returns normally. Throwing from `onNext` breaks rule 2.13."},
  {"front": "What does `SubmissionPublisher.submit` do when a subscriber's buffer is full?", "back": "It blocks the calling thread until there is room. `offer` drops instead and calls your drop handler."},
  {"front": "What happens if you call `request(0)` on a Reactor `Flux.range` subscription?", "back": "Nothing visible. Reactor only logs it at DEBUG and the stream stalls. Rule 3.9 (and the JDK's `SubmissionPublisher`) say it must signal `onError(IllegalArgumentException)`."},
  {"front": "What does `request(Long.MAX_VALUE)` mean?", "back": "Unbounded demand: \"send everything, no backpressure\" (rule 3.17)."},
  {"front": "Is `kotlinx.coroutines.flow.Flow` the same as `java.util.concurrent.Flow`?", "back": "No. The JDK one is the Reactive Streams protocol with `request(n)`. Kotlin's is a coroutine stream whose backpressure is the suspension of `emit`."}
 ],
 "terms": [
  {"term": "Backpressure", "plain": "A way for a slow consumer to tell a fast producer how much it can take, so the producer never sends more."},
  {"term": "Demand", "plain": "The number of items a subscriber has asked for with `request(n)` and not yet received."},
  {"term": "Publisher", "plain": "The source of a stream. It sends items to a subscriber, never more than the subscriber asked for."},
  {"term": "Subscriber", "plain": "The receiver of a stream. It gets `onSubscribe`, then `onNext` items, then `onError` or `onComplete`."},
  {"term": "Subscription", "plain": "The link between one publisher and one subscriber. It carries `request(n)` and `cancel()` back to the publisher."},
  {"term": "Terminal signal", "plain": "`onError` or `onComplete`. After one of them the stream is over and nothing else arrives."},
  {"term": "Non-blocking I/O", "plain": "Input and output where the thread hands the request to the operating system and moves on, and a callback runs when the answer arrives."}
 ],
 "explain_back": {
  "prompt": "A friend asks why the bakery's program bothers with `request(n)` when \"a queue in between does the same job\". Explain in your own words what demand gives you that a queue with no limit doesn't, and when a queue is fine.",
  "answer": "A queue with no limit lets the producer run as fast as it likes. When the consumer falls behind, the queue grows until memory runs out, and nothing upstream finds out until the program dies. With `request(n)` the consumer says how many items it can take, and the publisher may not send more. The slowness travels back to the producer, which then waits, buffers up to a limit, drops items on purpose, or fails, and you choose which. A queue is fine when it has a size and you have decided what happens when it's full, block the producer or refuse the item, because then it is backpressure too."
 },
 "deeper": {
  "minutes": 10,
  "body": "Four details that will help later.\n\n**Why `request` takes a `long`.** Demand adds up. A subscriber may call `request(5)` and then `request(10)` before any item arrives, and the publisher then owes 15. Rule 3.17 says a subscription must support demand up to `Long.MAX_VALUE`, and that a total at or above 2^63 - 1 may be treated as unbounded. Reactor's `subscribe(Consumer)` uses exactly that: it requests `Long.MAX_VALUE`. Operators like `limitRate` and `flatMap` then turn that unbounded demand into bounded requests upstream, which is lesson 7 of this track.\n\n**Rule 3.3 and reentrancy.** `request` may be called from inside `onNext` (rule 3.2), and a publisher that has items ready may answer by calling `onNext` again from inside that `request` (rule 3.10). Done naively, a stream of a million items becomes a stack a million calls deep. Rule 3.3 makes publishers bound that recursion, usually with a small loop that hands out items one by one. This is one reason a correct publisher is much harder to write than a subscriber, and why you should use a library's.\n\n**The TCK.** The Reactive Streams project ships a Technology Compatibility Kit: a set of tests that check a publisher or subscriber against the numbered rules. Library authors run it. Reactor's `TestPublisher` (lesson 8 of this track) borrows the idea for your own tests: you can create a publisher that breaks the rules on purpose, for example one that ignores demand, and check that your code survives it.\n\n**`Processor`.** A processor is both a subscriber and a publisher, so it can sit in the middle of a chain like a station on the belt. Reactor used to expose processors directly. It has phased them out in favour of `Sinks`, which you'll meet in lesson 8 of this track."
 },
 "sources": [
  {"title": "Reactive Streams for the JVM: specification (README with all rules)", "url": "https://github.com/reactive-streams/reactive-streams-jvm/blob/master/README.md"},
  {"title": "java.util.concurrent.Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html"},
  {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html"},
  {"title": "Reactor reference guide: Introduction to reactive programming (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/reactiveProgramming.adoc"},
  {"title": "Spring Framework reference: WebFlux overview", "url": "https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html"}
 ]
}
out = ROOT / "content/lessons/rx-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
