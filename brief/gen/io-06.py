import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/nio/src"
P = "java/workbench/nio/l06"
K = "kotlin/workbench/nio/l06"
read = lambda p: (ROOT / p).read_text()

rows = [
    ("@RunOnVirtualThread?", "new virtual thread", "box-ok"),
    ("explicit @Blocking or @NonBlocking?", "worker / IO thread", "box"),
    ("@Transactional? (3.40 docs)", "worker thread", "box-a"),
    ("returns Uni, Multi, CompletionStage, Publisher, suspend?", "IO thread", "box-b"),
    ("anything else: a plain return value", "worker thread", "box-a"),
]
parts = []
for i, (q, outcome, cls) in enumerate(rows):
    y = 64 + i * 48
    parts.append(f'<rect class="box" x="20" y="{y}" width="410" height="34" rx="8"/>')
    parts.append(f'<text class="t-s" x="225" y="{y + 22}" text-anchor="middle">{q}</text>')
    parts.append(f'<line class="ln" x1="430" y1="{y + 17}" x2="466" y2="{y + 17}" marker-end="url(#arr)"/>')
    if i < 4:
        parts.append(f'<text class="t-s t-m" x="448" y="{y + 11}" text-anchor="middle">yes</text>')
    parts.append(f'<rect class="{cls}" x="470" y="{y}" width="190" height="34" rx="8"/>')
    parts.append(f'<text class="t-s" x="565" y="{y + 22}" text-anchor="middle">{outcome}</text>')
    if i < 4:
        parts.append(f'<line class="ln-d" x1="50" y1="{y + 34}" x2="50" y2="{y + 44}" marker-end="url(#arr)"/>')
        parts.append(f'<text class="t-s t-m" x="70" y="{y + 44}">no</text>')
FIG = (
    '<svg viewBox="0 0 680 310" role="img" aria-label="How Quarkus REST 3.40 picks the thread for an endpoint, like a rule book reading the label on a job ticket: '
    'the request arrives on an IO thread, then RunOnVirtualThread, explicit Blocking or NonBlocking, Transactional '
    'and finally the return type decide between a virtual thread, a worker thread and the IO thread">'
    '<rect class="box-b" x="20" y="10" width="640" height="34" rx="8"/>'
    '<text class="t-s" x="340" y="32" text-anchor="middle">every request arrives on an IO thread (a Vert.x event loop), then, first match wins:</text>'
    + "".join(parts) + '</svg>'
)

rules_kotlin = """object DispatchRules {
    private val nonBlockingReturns = setOf(
        ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND)

    fun target(e: Endpoint): Target = when {
        Marker.RUN_ON_VIRTUAL_THREAD in e.markers -> Target.VIRTUAL_THREAD
        Marker.BLOCKING in e.markers -> Target.WORKER
        Marker.NON_BLOCKING in e.markers -> Target.IO_THREAD
        Marker.TRANSACTIONAL in e.markers -> Target.WORKER
        e.returns in nonBlockingReturns -> Target.IO_THREAD
        else -> Target.WORKER
    }
}"""
rules_java = """final class DispatchRules {
    private static final Set<ReturnKind> NON_BLOCKING_RETURNS = EnumSet.of(
            ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND);

    static Target target(Endpoint e) {
        Set<Marker> m = e.markers();
        if (m.contains(Marker.RUN_ON_VIRTUAL_THREAD)) return Target.VIRTUAL_THREAD;
        if (m.contains(Marker.BLOCKING)) return Target.WORKER;
        if (m.contains(Marker.NON_BLOCKING)) return Target.IO_THREAD;
        if (m.contains(Marker.TRANSACTIONAL)) return Target.WORKER;
        return NON_BLOCKING_RETURNS.contains(e.returns()) ? Target.IO_THREAD : Target.WORKER;
    }
}"""

# ---------------------------------------------------------------- opening
OPENING = """Picture a company that runs post offices. Every branch puts last lesson's clerks at the counter, and the company gives each branch a rule book for jobs. The rule book reads only the label on each job ticket. A job marked "quick" stays with the counter clerk. An unmarked job goes to the back office, which has a fixed number of workers. A job stamped "helper" gets a temporary helper, hired for that one job, who costs almost nothing while the job waits.

That company is Quarkus, a Java framework for web services that runs its counter on Vert.x. The surprise is how literally it reads the labels. It never looks at the job itself.

So the trap is a relabeled ticket. Mark a slow database job "quick", perhaps in the hope of speeding it up, and the counter clerk takes it while the whole queue waits. In Vert.x: event loops, verticles and the golden rule, we sent slow jobs to the back office by hand. In this lesson, we'll read Quarkus's labels, change them, block a counter clerk with Quarkus's settings, and hire temporary helpers. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Quarkus is a framework for **web services**: programs that answer requests sent over HTTP, the protocol behind web pages. Its HTTP layer is a Vert.x server, so every request is first read on a Vert.x event loop, which Quarkus calls an **IO thread**. That's the counter clerk. Everything in this lesson is pinned to Quarkus 3.40.

Quarkus REST, its library for writing web endpoints (formerly called RESTEasy Reactive), then decides who runs your code. An **endpoint** is a Java method that answers one kind of request, such as `GET /prices/P-17`. Annotations, the labels that start with `@`, tell Quarkus which requests it answers. The Quarkus reactive architecture guide describes the choice that follows. Quarkus calls your code right there on the IO thread, which saves a thread switch, or on a **worker thread**. A worker thread comes from a bounded pool, and it is allowed to block.

The decision comes from the method's signature: the label on the ticket. A method that returns `Uni`, `Multi`, `CompletionStage` or `Publisher`, or a Kotlin `suspend` function, counts as non-blocking and runs on the IO thread. All of these say "the answer comes later". `Uni`, from the Mutiny library that Quarkus uses, holds one result, and `Multi` holds a stream of them. `CompletionStage` is the JDK's own future, `Publisher` is the Reactive Streams standard's type for a stream of results, and a `suspend` function can pause without holding its thread. Anything else, such as a method that returns a `Price` directly, runs on a worker thread.

Here is the price desk as a Quarkus service, with one endpoint of each kind:

```java
@Path("/prices")
public class PriceResource {
    @Inject PriceBook priceBook;              // a database, called the blocking way
    @Inject LivePrices livePrices;            // a non-blocking client that returns Uni

    @GET @Path("/{parcel}")
    public Price price(@PathParam("parcel") String parcel) {        // plain value: worker thread
        return priceBook.find(parcel);
    }

    @GET @Path("/{parcel}/live")
    public Uni<Price> live(@PathParam("parcel") String parcel) {    // Uni: IO thread
        return livePrices.find(parcel);
    }
}
```

```kotlin
@Path("/prices")
class PriceResource(
    private val priceBook: PriceBook,         // a database, called the blocking way
    private val livePrices: LivePrices,       // a non-blocking client that returns Uni
) {
    @GET @Path("/{parcel}")
    fun price(@PathParam("parcel") parcel: String): Price =         // plain value: worker thread
        priceBook.find(parcel)

    @GET @Path("/{parcel}/live")
    suspend fun live(@PathParam("parcel") parcel: String): Price =  // suspend: IO thread
        livePrices.find(parcel).awaitSuspending()
}
```

`@Inject` asks Quarkus to hand the class the objects it needs; in Kotlin, the constructor does the same job. The first endpoint returns a plain `Price`, so Quarkus sends it to the back office. The second promises a result later, so it stays at the counter.

Read the rule as a promise you make. A `Uni` return type tells Quarkus "this method won't block", so Quarkus skips the hop to a worker and saves its cost. Quarkus believes that promise completely, and never looks inside the method. Break it with a database call inside, and you're back in lesson 5, with every other connection on that event loop waiting.

Here the ticket picture breaks. A real clerk would notice a forty-minute job marked "quick". Quarkus never will.

The back office is a bounded pool, like the ones in the executors track. Its size, `quarkus.thread-pool.max-threads`, defaults to the larger of 8 × CPUs and 200 in 3.40: 200 threads on a 4-core machine.

**The return type is a promise about blocking, and Quarkus believes it. Return `Uni` only from code that never waits.**

When the signature tells the wrong story, you can change the label."""

# ---------------------------------------------------------------- section 1
S1 = """Changing the label takes one annotation. `@Blocking` (from `io.smallrye.common.annotation`) sends a method to a worker even if it returns `Uni`. `@NonBlocking` keeps a method on the IO thread even if it returns a plain value. Both work on a method, on a class, or on your `jakarta.ws.rs.core.Application` subclass, the class that stands for the whole service, which sets the default for all of it. Filters, small pieces of code that run before or after every endpoint, follow their endpoint: under `@Blocking` they run on the worker, otherwise on the IO thread.

```java
@Blocking                                          // returns Uni, but the body blocks: use a worker
@GET @Path("/{parcel}/archive")
public Uni<Price> archived(@PathParam("parcel") String parcel) {
    return Uni.createFrom().item(priceBook.find(parcel));   // the database call runs right here
}
```

```kotlin
@Blocking                                          // returns Uni, but the body blocks: use a worker
@GET @Path("/{parcel}/archive")
fun archived(@PathParam("parcel") parcel: String): Uni<Price> =
    Uni.createFrom().item(priceBook.find(parcel))  // the database call runs right here
```

Look at the line inside. `Uni.createFrom().item(...)` wraps a value that already exists, so `priceBook.find(parcel)` runs while the method builds the `Uni`, on whatever thread runs the method. Without `@Blocking`, that's the counter clerk.

Transactions are where the rule book argues with itself. A **transaction** groups several database changes so that they all happen or none do. JTA, the Jakarta Transactions API, is Java's standard way to run one, and you ask for it with `@Transactional`. JTA blocks the thread that uses it.

The Quarkus REST guide as released with 3.40.1 says a method or class annotated with `jakarta.transaction.Transactional` \"will also be treated as a blocking method\", and that an explicit `@Blocking` or `@NonBlocking` overrides this. The same guide on Quarkus's main branch, its newest code, says the opposite. Since 3.35, it says, `@Transactional` no longer makes a method blocking, the return type decides, and a `Uni` method that uses JTA needs an explicit `@Blocking`. The research for this track couldn't find the code that settles which is right for 3.40.

So don't depend on either reading. Put `@Blocking` on every endpoint that uses JTA and doesn't return a plain value. It costs nothing when the rule already applies and saves you when it doesn't.

When it doesn't, at least the failure is loud. Quarkus's JTA support comes from a library called Narayana, and its interceptor, the code that runs around a `@Transactional` method, checks whether blocking is allowed before it starts a transaction. In 3.40.1, on an IO thread, it throws `BlockingOperationNotAllowedException`: \"@Transactional cannot start a JTA transaction within a reactive pipeline. If the annotated method is intended to be blocking, ensure it is executed on a worker thread, for example by annotating it with @Blocking. ...\"

**When the signature tells the wrong story, change the label. On a `@Transactional` endpoint that returns `Uni`, write `@Blocking`.**

That exception is one way Quarkus catches a blocked counter clerk. Lesson 5's floor manager is the other, and Quarkus gives him new instructions."""

# ---------------------------------------------------------------- section 2
S2 = """Quarkus configures its Vert.x differently from plain Vert.x, and the differences change what your logs show:

| Setting | Plain Vert.x 5 | Quarkus 3.40 |
|---|---|---|
| event loops | 2 × CPUs | CPUs, at least 2, at most one per 10 MB of max heap (the memory for objects) |
| warn about a blocked loop after | 2 s | 2 s (`quarkus.vertx.max-event-loop-execute-time`) |
| include the stack trace after | 5 s | 2 s (`quarkus.vertx.warning-exception-time`) |
| threads for blocking work | worker pool: 20 | `quarkus.thread-pool.max-threads`: max(8 × CPUs, 200) |

A comment in Quarkus's source explains the first row. Twice the number of cores used to be the recommendation, but matching cores one to one seemed more reasonable, and it saves memory. On a 4-core laptop that means 4 event loops instead of 8, so one blocked loop stalls a quarter of your connections instead of an eighth.

The third row is the friendly difference. `QuarkusLikeLoopDemo` builds a plain Vert.x instance with Quarkus's settings and blocks an event loop for 3 seconds. The first warning already carries the stack trace:

```text
plain Vert.x default event loops: 8, Quarkus 3.40 default: max(2, min(3420 MB / 10, 4 cpus)) = 4
[vertx-blocked-thread-checker] WARN io.vertx.core.impl.BlockedThreadChecker - Thread vert.x-eventloop-thread-0 has been blocked for 2681 ms, time limit is 2000 ms
io.vertx.core.VertxException: Thread blocked
	at java.base/java.lang.Thread.sleep(Thread.java:509)
	at workbench.nio.l06.QuarkusLikeLoopDemo.lambda$main$0(QuarkusLikeLoopDemo.java:30)
```

In the post office, Quarkus's floor manager writes down what the clerk is doing on his very first pass. In a real Quarkus service the line goes through Quarkus's own logging, so the prefix differs, but the message and the stack are Vert.x's. The first frame below `Thread.sleep` is your endpoint.

Some Quarkus APIs don't wait for the floor manager at all. They check where they run and fail at once with `BlockingOperationNotAllowedException`, which extends `IllegalStateException`. The JTA interceptor from the previous section is one. Reading a request body as a blocking stream on the IO thread is another, and it fails with \"Attempting a blocking read on io thread\".

Go one level down, and the check is simple. Quarkus asks its IO-thread detectors whether the current thread is an IO thread, and the Vert.x detector in 3.40.1 returns `Context.isOnEventLoopThread()`, the same call this lesson's lab uses. A fast exception in a test is a better way to find a blocking call than a slow event loop in production.

**Quarkus reports a blocked IO thread after 2 seconds, stack and all. Read the first frame of your own code below the block.**

Warnings and exceptions tell you a counter clerk blocked. The last label in the rule book avoids the back office's limit altogether."""

# ---------------------------------------------------------------- section 3
S3 = """The back office has a fixed number of workers. `@RunOnVirtualThread` is the third label in the rule book: it tells Quarkus to run the method on a new virtual thread, instead of the IO thread or a worker. A **virtual thread** is a thread the JDK manages itself. It runs on a **carrier**, an ordinary operating system thread, and while it waits it hands the carrier back, so a waiting virtual thread costs a few kilobytes of memory. In the post office, it's the temporary helper, hired for one job, who sits down while the job waits.

The code stays blocking style. A database call, or `uni.await().atMost(...)` on a Mutiny `Uni`, parks the virtual thread, and the JDK wakes it when the result is ready. `VirtualVsWorkerDemo` shows what the back office's size costs. 200 requests arrive on one IO context, and each makes a 100 ms blocking call:

```text
worker pool (20 threads)   200 calls x 100 ms -> 1,037 ms on 20 distinct threads
virtual thread per call    200 calls x 100 ms ->   113 ms on 200 distinct threads
```

Twenty workers needed ten rounds of 100 ms: Little's law from lesson 1, 20 threads / 0.1 s = 200 calls a second. Two hundred helpers needed one. The Quarkus virtual threads guide compares the three models in one table, and its costs column is the part to remember:

| Model | Runs on | Main cost |
|---|---|---|
| plain return value | worker thread | the pool caps concurrency |
| `Uni` and friends | IO thread | more complex code |
| `@RunOnVirtualThread` | a new virtual thread | pinning, monopolization, inefficient object pooling |

**Pinning** means a virtual thread that can't hand its carrier back while it waits. On Java 21 to 23 that happens when it blocks inside `synchronized`. JDK 24 removed that case (JEP 491), but native code, code written in C and called from Java, can still pin, and the guide notes that the PostgreSQL driver `pgjdbc` before 42.6.0 pins often on 21 to 23. **Monopolization** means CPU-heavy work that never blocks, so it never hands the carrier back: virtual threads are for work that waits, not work that computes. And libraries such as Jackson (which reads and writes JSON) and Netty keep pools of objects per thread, assuming a few long-lived threads. A new virtual thread per request defeats those pools.

Two more things stay true. Helpers don't limit anything. 200 virtual threads sharing a 20-connection database pool still queue at the pool, so put a semaphore (a counter of permits that makes extra callers wait) or the pool's own limit in front of anything fragile. And the request still arrives on an IO thread. `@RunOnVirtualThread` works by moving your code off it.

**A virtual thread per request removes the back office's cap, and with it the back office's protection. Put the limit back in front of the database.**"""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a company rule book that reads only the label on each job ticket. Quarkus works the same way: the return type and three annotations pick the counter clerk, the back office or a temporary helper, and Quarkus never looks inside the method.

Now search your own endpoints for a `Uni` return or a `suspend fun` that calls a blocking repository, client or library. Each one is a slow job wearing a "quick" label.

Next, we'll meet Jetty 12, a server with its own doormen, light-watchers and pool of clerks. How does it decide, task by task, who serves each customer?"""

L = {
 "id": "io-06",
 "title": "Quarkus on Vert.x: IO threads, workers and virtual threads",
 "minutes": 36,
 "goal": "By the end you can predict which thread runs a Quarkus REST endpoint from its signature and annotations, explain what happens when an IO thread blocks, and choose between a worker thread, the IO thread and @RunOnVirtualThread for an endpoint that waits on a database.",
 "opening": OPENING,
 "warmup": {
  "q": "A Quarkus 3.40 endpoint returns `Uni<Parcel>` and builds it with `Uni.createFrom().item(repository.findById(id))`, where `findById` calls a database the blocking way. Which thread runs that database call?",
  "options": [
   "A worker thread, because Quarkus sees the database call",
   "A Vert.x event loop (IO thread), because the method returns `Uni`",
   "A virtual thread, because Quarkus 3.40 runs everything on virtual threads",
   "The Mutiny scheduler, because `Uni` is lazy"
  ],
  "answer": 1,
  "why": "Quarkus REST picks the thread from the signature: `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` mean \"non-blocking\", so the method runs on the IO thread. `findById` runs while the method builds the `Uni`, so the database call blocks an event loop. Quarkus can't see inside your method; add `@Blocking` or return a plain value."
 },
 "sections": [
  {
   "h": "The label on the ticket: how Quarkus picks a thread from the return type",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Quarkus REST 3.40's dispatch decision, as this lesson's lab models it. The first rule that matches picks the thread."},
   "try": {
    "title": "Predict the thread",
    "minutes": 3,
    "steps": [
     "Without running anything, write down the thread for each Quarkus 3.40 endpoint: (a) `public List<Parcel> recent()`, (b) `public Uni<Parcel> byId(...)`, (c) `public CompletionStage<Label> printLabel(...)`, (d) Kotlin `suspend fun track(id: String): Status`, (e) `public Multi<Scan> scans()`.",
     "Open the lab test `DispatcherTest` and find the test that encodes the same rules. Check your answers against it."
    ],
    "expect": "(a) runs on a worker thread; (b), (c), (d) and (e) run on the IO thread. The one people get wrong is (d): Quarkus treats a Kotlin `suspend` function as non-blocking, so a blocking database call inside it blocks an event loop, exactly like one inside a `Uni` method."
   },
   "refs": [
    {"title": "Quarkus REST guide at 3.40.1: execution model, blocking, non-blocking", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "Changing the label: @Blocking, @NonBlocking, and the @Transactional disagreement",
   "body": S1,
   "try": {
    "title": "Read the rules both ways",
    "minutes": 3,
    "steps": [
     "Take `@Transactional public Uni<Void> record(Parcel p)`. Where does it run under the 3.40.1 docs? Under the main-branch docs? What does the JTA interceptor do in each case?",
     "Now take `@Transactional @NonBlocking public Uni<Void> record(Parcel p)`. Where does it run, and what happens?",
     "Check the first answer against the lab test that mentions `@Transactional`."
    ],
    "expect": "Under the 3.40.1 docs the first method runs on a worker, and the transaction starts normally. Under the main-branch rule it runs on the IO thread, and the interceptor throws `BlockingOperationNotAllowedException` before your code runs. The second method runs on the IO thread under both readings, because an explicit annotation wins, so it always throws. In every case `@Blocking` would have given the same working result, which is why it belongs on the method."
   }
  },
  {
   "h": "When a counter clerk blocks: Quarkus's settings and its fast failures",
   "body": S2,
   "try": {
    "title": "Block an IO thread with Quarkus settings",
    "minutes": 3,
    "steps": [
     "Open `QuarkusLikeLoopDemo.java` (or the Kotlin twin). Predict the event-loop count it computes for your machine.",
     "Predict whether the first blocked-thread warning comes with a stack trace. Run it.",
     "Run it again with `-Pargs=1500`. How many warnings now, and why?"
    ],
    "code": {"lang": "java", "title": "QuarkusLikeLoopDemo.java", "src": read(f"{lab}/demo/{P}/QuarkusLikeLoopDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.QuarkusLikeLoopDemo",
             "file": f"{lab}/demo/{P}/QuarkusLikeLoopDemo.java",
             "alt": {"lang": "kotlin", "title": "QuarkusLikeLoopDemo.kt", "src": read(f"{lab}/demo/{K}/QuarkusLikeLoopDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.QuarkusLikeLoopDemoKt",
                     "file": f"{lab}/demo/{K}/QuarkusLikeLoopDemo.kt"}},
    "expect": "With a few gigabytes of max heap the memory cap doesn't bite, so the count equals your CPUs (4 here, against Vert.x's 8). The first warning, between 2 and 3 seconds in, already includes `VertxException: Thread blocked` and the stack, because the warning-exception time is 2 s. With a 1,500 ms block there is no warning at all: the checker only reports a task that has run longer than 2 seconds, so short blocks stay out of the logs."
   }
  },
  {
   "h": "Temporary helpers: @RunOnVirtualThread without the worker-pool cap",
   "body": S3,
   "try": {
    "title": "Pool cap versus virtual threads",
    "minutes": 3,
    "steps": [
     "Open `VirtualVsWorkerDemo.java` (or the Kotlin twin). Predict both times before running.",
     "Run it.",
     "Give the worker pool 40 threads: change `Vertx.vertx()` to `Vertx.vertx(new VertxOptions().setWorkerPoolSize(40))`. Predict the new worker time, then run."
    ],
    "code": {"lang": "java", "title": "VirtualVsWorkerDemo.java", "src": read(f"{lab}/demo/{P}/VirtualVsWorkerDemo.java"),
             "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.VirtualVsWorkerDemo",
             "file": f"{lab}/demo/{P}/VirtualVsWorkerDemo.java",
             "alt": {"lang": "kotlin", "title": "VirtualVsWorkerDemo.kt", "src": read(f"{lab}/demo/{K}/VirtualVsWorkerDemo.kt"),
                     "run": "./gradlew :nio:demo -Pmain=workbench.nio.l06.VirtualVsWorkerDemoKt",
                     "file": f"{lab}/demo/{K}/VirtualVsWorkerDemo.kt"}},
    "expect": "About 1,000 ms on 20 worker threads (200 calls / 20 threads x 100 ms) and about 110 to 130 ms on 200 virtual threads; later runs for this lesson measured 1,059 and 132 ms. With 40 workers it drops to about 500 to 600 ms (534 and 598 ms in earlier runs): Little's law again, throughput = threads / time per call. The virtual version has no such cap, which is its strength, and also why you add your own limit in front of a fragile service."
   },
   "refs": [
    {"title": "Quarkus virtual threads guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The lab's dispatch rules in Kotlin and Java",
  "java": {"title": "DispatchRules.java", "src": rules_java},
  "kotlin": {"title": "DispatchRules.kt", "src": rules_kotlin},
  "note": "Both encode the same first-match-wins rules; Kotlin's `when` without a subject reads like the figure, and Java uses early returns. The language difference that matters is in Quarkus itself. Java has no `suspend`, so a Java endpoint is non-blocking only through its return type, while a Kotlin `suspend fun` with a plain return type is non-blocking too, and runs on the IO thread. One Kotlin trap from this lesson's lab: Vert.x 5's `Future` has a member `await()`, and in Kotlin a member always wins over an extension with the same name, so a test helper `fun <T> Future<T>.await()` is silently ignored. The lab's test calls its helper `awaitResult()` for that reason."
 },
 "worked": {
  "title": "Pick the thread for four post office endpoints",
  "steps": [
   {"say": "A tracking lookup reads the parcel from a database the blocking way. Plain return type, so it runs on a worker. Nothing to add.",
    "code": "@GET @Path(\"/parcels/{id}\")\npublic Parcel byId(@PathParam(\"id\") String id) {   // worker thread\n    return parcels.findById(id);                     // blocking database call\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@GET @Path(\"/parcels/{id}\")\nfun byId(@PathParam(\"id\") id: String): Parcel =    // worker thread\n    parcels.findById(id)                           // blocking database call"},
   {"say": "A label-printing endpoint records the label in a JTA transaction and returns `Uni` because a client library wants one. Under the 3.40.1 docs `@Transactional` alone would send it to a worker; under the main-branch docs it would run on the IO thread, and the interceptor would throw. Add `@Blocking`, and both readings agree.",
    "code": "@Blocking\n@Transactional\n@POST @Path(\"/parcels/{id}/label\")\npublic Uni<Label> printLabel(@PathParam(\"id\") String id) {\n    return Uni.createFrom().item(labels.print(id));    // database writes inside a JTA transaction\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@Blocking\n@Transactional\n@POST @Path(\"/parcels/{id}/label\")\nfun printLabel(@PathParam(\"id\") id: String): Uni<Label> =\n    Uni.createFrom().item(labels.print(id))        // database writes inside a JTA transaction"},
   {"say": "A live feed of parcel scans comes from a non-blocking client and never waits. `Multi` keeps it on the IO thread with no thread switch, which is the case the reactive model is built for.",
    "code": "@GET @Path(\"/scans\")\npublic Multi<Scan> scans() {                         // IO thread\n    return scanFeed.subscribe();                     // non-blocking source\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@GET @Path(\"/scans\")\nfun scans(): Multi<Scan> =                           // IO thread\n    scanFeed.subscribe()                             // non-blocking source"},
   {"say": "A customs report calls a slow outside web service (2 s) that accepts at most 50 calls at once, and the customs office sends bursts of hundreds of requests. The worker pool would cap the throughput, so give each request a virtual thread, and put the outside service's limit back with a semaphore.",
    "code": "private final Semaphore customsSlots = new Semaphore(50);\n\n@RunOnVirtualThread\n@GET @Path(\"/reports/customs/{day}\")\npublic Report customs(@PathParam(\"day\") String day) throws InterruptedException {\n    customsSlots.acquire();                          // 1. respect the outside service's limit\n    try {\n        return customsClient.reportFor(day);         // 2. blocks: parks the virtual thread\n    } finally {\n        customsSlots.release();\n    }\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "private val customsSlots = Semaphore(50)\n\n@RunOnVirtualThread\n@GET @Path(\"/reports/customs/{day}\")\nfun customs(@PathParam(\"day\") day: String): Report {\n    customsSlots.acquire()                           // 1. respect the outside service's limit\n    try {\n        return customsClient.reportFor(day)          // 2. blocks: parks the virtual thread\n    } finally {\n        customsSlots.release()\n    }\n}"}
  ]
 },
 "lab": {
  "title": "Simulate Quarkus's rule book on plain Vert.x",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/Dispatcher.kt", f"{lab}/main/{K}/Endpoint.kt"],
  "run": "./gradlew :nio:test --tests 'workbench.nio.l06.*'",
  "steps": [
   "Run the tests. All seven fail with `NotImplementedError`. Read `Endpoint.kt` for the types: an endpoint has a name, a return kind and a set of markers (the annotations).",
   "Write `DispatchRules.target` with a `when` that applies the four rules in its KDoc, first match wins. The four rule tests should pass.",
   "Write `BlockingGuard.check`: throw `BlockingNotAllowedException(\"Attempting $what on an IO thread\")` when `Context.isOnEventLoopThread()` is true.",
   "Write `Dispatcher.invoke`: receive the request with `server.runOnContext { ... }`, then run the body there (IO thread), through `vertx.executeBlocking(callable, false)` (worker) or on a new virtual thread, and complete a `Promise` with the result or the failure.",
   "Run the tests until all seven pass. Then change `false` to the default and see which test fails, and why."
  ],
  "hints": [
   "`Marker.BLOCKING in endpoint.markers` reads naturally in Kotlin.",
   "`val p = Promise.promise<T>()`, then `p.complete(value)` or `p.fail(e)`, and return `p.future()`. For the worker branch, `vertx.executeBlocking(task, false).onComplete(p)` passes the result straight on.",
   "Give the `Callable` an explicit type (`val task: Callable<T> = Callable { body() }`); Kotlin can fail to infer Vert.x types whose `@Nullable` annotation lives in vertx-codegen.",
   "Every request goes through the one `server` context, so an ordered `executeBlocking` would make the four 300 ms calls queue: that is what the overlap test catches."
  ],
  "done_when": "All seven tests in `DispatcherTest` pass."
 },
 "drill": {
  "title": "Write the rule book from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write a function that takes an endpoint's return kind and its annotations and returns IO_THREAD, WORKER or VIRTUAL_THREAD, using Quarkus 3.40's documented rules. For which rule would you add `@Blocking` anyway, to stay safe on any 3.x version?",
  "answer": {"lang": "kotlin", "src": rules_kotlin + "\n// add @Blocking to @Transactional endpoints that return Uni (or are suspend):\n// the 3.40.1 and main-branch docs disagree about the TRANSACTIONAL rule.",
             "alt": {"lang": "java", "src": rules_java + "\n// add @Blocking to @Transactional endpoints that return Uni:\n// the 3.40.1 and main-branch docs disagree about the TRANSACTIONAL rule."}}
 },
 "recap": [
  "Every Quarkus request arrives on an IO thread, a Vert.x event loop. Quarkus REST then reads the signature: `Uni`, `Multi`, `CompletionStage`, `Publisher` and Kotlin `suspend` stay on the IO thread, and plain return values go to a worker.",
  "`@Blocking` and `@NonBlocking` override the signature on a method, a class or the `Application`.",
  "The 3.40.1 docs say `@Transactional` makes a method blocking, and the main-branch docs say it no longer does. Put `@Blocking` on JTA endpoints that return `Uni` either way.",
  "Quarkus 3.40 runs one event loop per CPU (at least 2), warns after 2 s and prints the stack at 2 s. Guarded APIs throw `BlockingOperationNotAllowedException` on an IO thread.",
  "`@RunOnVirtualThread` runs blocking code on a new virtual thread with no pool cap; watch for pinning, CPU-heavy work and per-thread object pools.",
  "The limit: Quarkus trusts the label and never looks inside the method, and virtual threads limit nothing. Honest labels and a limit in front of the database stay your job."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "In Quarkus 3.40 with no annotations, which endpoint runs on the IO thread?",
   "options": ["`public Parcel get(@PathParam(\"id\") String id)`", "`public List<Parcel> recent()`", "`public Uni<Parcel> get(@PathParam(\"id\") String id)`", "`public Response cancel(...)`"],
   "answer": 2,
   "why": "Only the `Uni` return type marks the method as non-blocking. The other three return plain values, so Quarkus runs them on a worker thread."},
  {"q": "A Kotlin endpoint `suspend fun track(id: String): Status = repository.track(id)` calls a repository that uses the database the blocking way. What happens under load?",
   "options": ["Nothing: suspend functions never block a thread", "It runs on the IO thread, so each database call blocks an event loop; make it a plain function or call a non-blocking client", "Quarkus notices the database call and moves it to a worker", "It runs on a new virtual thread"],
   "answer": 1,
   "why": "Quarkus treats `suspend` like `Uni`: non-blocking, so it runs on the IO thread. `suspend` only frees the thread when the code inside actually suspends, and a blocking database call doesn't. Quarkus can't see inside the method."},
  {"q": "A Quarkus log shows `Thread vert.x-eventloop-thread-2 has been blocked for 2105 ms, time limit is 2000 ms` followed at once by a stack trace. Plain Vert.x would print the stack only after 5 s. Why here?",
   "options": ["Quarkus sets the warning-exception time to 2 s", "Quarkus lowers the blocked limit to 1 s", "Vert.x 5 changed its default to 2 s", "The stack means Quarkus killed the thread"],
   "answer": 0,
   "why": "Quarkus's `quarkus.vertx.warning-exception-time` defaults to 2 s, the same as the blocked limit, so the first warning already carries the stack trace. Neither Vert.x nor Quarkus kills or interrupts the thread."},
  {"q": "From lesson 5: a Vert.x consumer calls `vertx.executeBlocking(callable)` without the second argument for every message. Six messages arrive at once, each needing 300 ms of blocking work. Roughly how long until all six are answered?",
   "options": ["About 300 ms", "About 1,800 ms", "About 600 ms", "Never: it deadlocks"],
   "answer": 1,
   "why": "The default `executeBlocking` is ordered per context, and all six messages come from the consumer's one context, so they run one after another on the worker pool: 6 x 300 ms. Passing `false` lets them overlap.",
   "from": "io-05"},
  {"q": "A customs report endpoint calls a blocking outside service that takes 2 s and allows 50 calls at once. The customs office sends bursts of 500 requests. Which fits best?",
   "options": ["Return `Uni` and call the outside service inside it", "Plain return type, with the worker pool raised to 500", "`@NonBlocking`, so it doesn't use a worker", "`@RunOnVirtualThread`, with a semaphore of 50 around the outside call"],
   "answer": 3,
   "why": "The call blocks, so it must stay off the IO thread, which rules out `Uni` and `@NonBlocking`. Virtual threads make 500 waiting requests cheap, and the semaphore keeps the outside service at its limit of 50. A 500-thread worker pool would work, but it costs 500 platform threads and still sends 500 calls at once to a service that takes 50."}
 ],
 "flashcards": [
  {"front": "Which Quarkus REST return types run on the IO thread by default?", "back": "`Uni`, `Multi`, `CompletionStage`, `Publisher`, and Kotlin `suspend` functions. Everything else runs on a worker thread."},
  {"front": "Where can you put `@Blocking` / `@NonBlocking` in Quarkus REST?", "back": "On a method, a class, or a `jakarta.ws.rs.core.Application` subclass (which sets the default for the whole service)."},
  {"front": "Does `@Transactional` make a Quarkus REST method blocking?", "back": "The 3.40.1 docs say yes, the main-branch docs say no (since 3.35). Add an explicit `@Blocking` to JTA endpoints that return `Uni`."},
  {"front": "Default number of Vert.x event loops in Quarkus 3.40?", "back": "One per CPU, at least 2, and at most one per 10 MB of max heap: `max(2, min(maxHeapMB / 10, cpus))`."},
  {"front": "Why does a Quarkus blocked-thread warning come with a stack trace at 2 s?", "back": "Quarkus sets `quarkus.vertx.warning-exception-time` to 2 s; plain Vert.x uses 5 s."},
  {"front": "What exception do guarded Quarkus APIs throw on an IO thread?", "back": "`BlockingOperationNotAllowedException` (an `IllegalStateException`), for example from the JTA interceptor or a blocking body read."},
  {"front": "Three costs of `@RunOnVirtualThread` named by the Quarkus guide?", "back": "Pinning (for example `synchronized` on Java 21 to 23, native code), monopolization by CPU-heavy work, and inefficient per-thread object pools."}
 ],
 "terms": [
  {"term": "IO thread", "plain": "Quarkus's name for a Vert.x event-loop thread; it reads requests and writes responses."},
  {"term": "Worker thread", "plain": "A thread from Quarkus's bounded pool that may block, used for plain return types and `@Blocking`."},
  {"term": "Endpoint", "plain": "A method that answers one kind of web request, such as `GET /prices/P-17`."},
  {"term": "@Blocking / @NonBlocking", "plain": "Annotations that override the thread Quarkus would pick from the method's signature."},
  {"term": "@RunOnVirtualThread", "plain": "Runs the endpoint on a new virtual thread instead of the IO thread or a worker."},
  {"term": "BlockingOperationNotAllowedException", "plain": "Thrown by guarded Quarkus APIs when blocking code runs on an IO thread."},
  {"term": "Pinning", "plain": "A virtual thread that can't let go of its carrier thread while it waits."},
  {"term": "Monopolization", "plain": "CPU-heavy work on a virtual thread that never blocks, so it keeps its carrier."}
 ],
 "explain_back": {
  "prompt": "A teammate changed a database endpoint to return `Uni` \"to make it reactive\", and latency got worse under load. Explain what Quarkus 3.40 does with that endpoint and what they should do instead.",
  "answer": "Quarkus REST decides the thread from the signature, like a rule book that reads only the label on a job. A `Uni` return type means the method promises not to block, so Quarkus runs it on the IO thread, a Vert.x event loop, without switching to a worker. Wrapping a blocking database call in `Uni.createFrom().item(...)` runs the call while the method builds the `Uni`, so the call blocks the event loop and every other connection on it waits. Before the change, the plain return type put the call on a worker thread, which protected the event loop. They should go back to a plain return type, or add `@Blocking` if they must return `Uni`, or switch to a non-blocking database client so the method really doesn't block. If the reason for the change was the worker pool's limit, `@RunOnVirtualThread` with a limit on database calls is another option."
 },
 "deeper": {
  "minutes": 10,
  "body": """A few details from the Quarkus 3.40 sources and docs help when you debug thread choices.

Filters follow their endpoint. A `@ServerRequestFilter` runs on the worker for a `@Blocking` endpoint and on the IO thread otherwise, so a filter that does a blocking lookup (say, checking a key against a database) blocks the event loop for every non-blocking endpoint. `@ServerRequestFilter(nonBlocking = true)` forces a filter onto the IO thread, which is only safe if it really never blocks.

To check which thread runs your code, log `Thread.currentThread().getName()` or assert `io.vertx.core.Context.isOnEventLoopThread()` in a `@QuarkusTest`, Quarkus's annotation for tests that start the whole service. Event-loop threads are named `vert.x-eventloop-thread-N`, and Quarkus's worker threads usually have `executor-thread` in their names.

The Vert.x settings live under `quarkus.vertx.*`: `event-loops-pool-size`, `max-event-loop-execute-time`, `warning-exception-time` and `max-worker-execute-time` (60 s). The old `quarkus.vertx.worker-pool-size` is deprecated in favor of `quarkus.thread-pool.max-threads`. Raising the event-loop count rarely helps a service that blocks: it only spreads the damage over more loops. Removing the blocking call is the fix.

Finally, a version note on the `@Transactional` disagreement: the 3.40.1-tagged guide and the main-branch guide were both read for this track, and the code that applies the rule was not found. If you need certainty for your exact Quarkus version, write a `@QuarkusTest` that calls a `@Transactional` endpoint returning `Uni` and asserts which thread it ran on."""
 },
 "sources": [
  {"title": "Quarkus REST guide at 3.40.1: execution model", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/docs/src/main/asciidoc/rest.adoc"},
  {"title": "Quarkus virtual threads guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/virtual-threads.adoc"},
  {"title": "Quarkus reactive architecture guide", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/quarkus-reactive-architecture.adoc"},
  {"title": "VertxCoreRecorder at 3.40.1: default event loops and IO-thread detector", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/extensions/vertx/runtime/src/main/java/io/quarkus/vertx/core/runtime/VertxCoreRecorder.java"},
  {"title": "TransactionalInterceptorBase at 3.40.1", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/extensions/narayana-jta/runtime/src/main/java/io/quarkus/narayana/jta/runtime/interceptor/TransactionalInterceptorBase.java"}
 ]
}

out = ROOT / "content/lessons/io-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
