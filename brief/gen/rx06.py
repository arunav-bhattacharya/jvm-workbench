import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l06"
PK = "kotlin/workbench/reactive/l06"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l06."


def code(name, args=""):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name + args, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt" + args, "file": f"{lab}/demo/{PK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """Picture the bakery on a busy morning. A few workers keep the belts moving, and none of them ever stands still. Then someone puts a telephone at the slicing station, and the old stock room has to be called about every loaf. The stock room is in no hurry. While the worker at the slicer waits with the phone at her ear, every loaf on her belt waits too.

A Reactor program has the same workers, called threads, and the same phone, called a blocking call. The surprise is how few workers Reactor keeps: its main team has one per processor core. The easy trap is one line in the wrong place, which leaves a single worker making every call in turn.

In Errors, retries and timeouts, the pauses of a retry ran on a thread named `parallel-1`. In this lesson, we'll find out who those workers are and move work between them with `publishOn` and `subscribeOn`. Then we'll hand the slow calls to workers who are allowed to wait, and see why `block()` is refused on some threads. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """So far the belt has had stations but no workers. In a program, the workers are **threads**: paths of work that each run one piece of code at a time. An `ExecutorService`, the JDK object from the executors track, keeps its own team of threads. A Reactor chain doesn't. Unless you say otherwise, the source runs on the thread that called `subscribe()`. Each operator, each station on the belt, runs on the thread that delivered the signal to it, the item, error or completion that just arrived.

On the bakery line, the worker who puts a loaf on the belt carries it through every station to the end. `ThreadTourDemo`, in the Try it, shows it with `Flux.range(1, 2).map(...).subscribe(...)` called from `main`:

```text
1. no scheduler anywhere
  source emits 1             on main
  subscriber gets 10         on main
  source emits 2             on main
  subscriber gets 20         on main
```

Every step ran on `main`, item by item, and `subscribe` returned only when the range was done.

Other threads appear when something asynchronous, something that finishes later on its own schedule, sits in the chain. A timer fires on one of Reactor's own threads, and `Mono.delay`, `interval`, `delayElements`, `timeout` and the pauses of `Retry.backoff` are all timers. The operators after the timer carry on there. A non-blocking client, one that hands its request to the operating system and moves on (Why reactive), delivers its answer on its own threads too. The demo's other two parts show the timers:

```text
2. after a timer (Mono.delay)
  timer fires                on parallel-1
  map after the timer        on parallel-1
3. flatMap over three timers
  downstream gets 1          on parallel-2
  downstream gets 2          on parallel-3
  downstream gets 3          on parallel-4
```

The `map` after the timer ran on the timer's thread. In the `flatMap` over three timers, the items arrived on three different threads, but still one at a time. Rule 1.3 from Why reactive holds: signals to one subscriber never overlap, even when the thread changes.

When you want to choose the worker, you pass a **scheduler**, Reactor's source of threads. It is close to an `ExecutorService`, and it is also a clock, which is how a test can fake time. Reactor 3.8 has four shared ones, like four teams in the bakery:

| Scheduler | Threads | Use it for |
|---|---|---|
| `Schedulers.immediate()` | the current thread | a placeholder that changes nothing |
| `Schedulers.single()` | one shared thread | cheap work that must stay in order |
| `Schedulers.parallel()` | one per CPU core | CPU work and timers; never block here |
| `Schedulers.boundedElastic()` | up to 10 x cores, then a queue of 100,000 tasks | blocking calls |

A **CPU core** is the part of the processor that runs one thread at a time. So on a 4-core machine, `parallel` is a team of four quick hands who must never stand still. `boundedElastic` is a back room of up to forty workers who are allowed to wait on the phone.

The threads of `parallel` and `single` are marked as non-blocking, and Reactor refuses `block()` on them, as the last section shows. `boundedElastic` creates threads when it needs them, up to its cap, reuses them, and lets a worker go after 60 seconds with nothing to do. Past the cap, tasks wait in its queue. Past the queue, it throws `RejectedExecutionException`.

You can build your own with `Schedulers.newParallel`, `newBoundedElastic` or `fromExecutorService`, and you then have to `dispose()` them. The reference guide still mentions `Schedulers.elastic()`, which no longer exists in 3.8: use `boundedElastic()`.

**A Reactor chain runs on whatever thread delivered the last signal, unless you say otherwise.**

So far a timer chose the thread for us. Next, we'll choose it ourselves."""

# ---------------------------------------------------------------- section 1
J_PS = """Flux.range(1, 1)
        .doOnNext(i -> where("source"))                 // boundedElastic-1
        .publishOn(Schedulers.single())
        .doOnNext(i -> where("after publishOn"))        // single-1
        .subscribeOn(Schedulers.boundedElastic())       // written last, still moves the source
        .blockLast();"""
K_PS = """Flux.range(1, 1)
    .doOnNext { where("source") }                       // boundedElastic-1
    .publishOn(Schedulers.single())
    .doOnNext { where("after publishOn") }              // single-1
    .subscribeOn(Schedulers.boundedElastic())           // written last, still moves the source
    .blockLast()"""

S1 = """Two operators move work to another team, and they move different things.

`publishOn(scheduler)` sits on the belt itself, in the path of the data. Items arrive from above on whatever thread, and `publishOn` puts them in a queue (it asks for 256 at a time by default). Then one worker of the scheduler carries them on to the operators below. Everything after it, up to the next `publishOn`, runs on that worker. Everything before it is unaffected.

On the bakery line, `publishOn` is a hand-over point. Up to here, the oven's worker carries each loaf; from here on, a worker from another team does. Use it to get work off a thread that must stay free, or onto `parallel` for a step that keeps the processor busy.

`subscribeOn(scheduler)` sits on the path of the subscription instead. When you call `subscribe()`, Reactor passes the subscription up the chain from your end to the source, as Mono and Flux showed. `subscribeOn` makes that trip, and the `request(n)` calls after it, continue on the scheduler's thread. So the source starts producing there, and a source that does its work as it is subscribed, such as `fromCallable` or `range`, runs there.

In the bakery, `subscribeOn` is the line on the signed order form that says which team starts the oven, and it doesn't matter where on the form you write it:

""" + pair(J_PS, K_PS) + """

`PublishSubscribeDemo`, in the Try it, runs that chain:

```text
2. subscribeOn(boundedElastic) written last
  source                 on boundedElastic-1
  after publishOn        on single-1
```

The source ran on `boundedElastic-1`, although `subscribeOn` was written last. After the hand-over point, the item moved to `single-1`. The figure below draws both paths.

With two `subscribeOn` calls, **the one nearest the source wins**. The other one only adds a thread hop on the way up. Here the order-form picture breaks: a real form with two lines that disagree would go back to the customer, while Reactor quietly obeys the line nearest the oven. The reference guide recommends writing `subscribeOn` right after the source, where a reader looks for it.

Two limits. If the source is asynchronous itself, such as `Mono.delay` or a non-blocking client, `subscribeOn` moves only the subscribe call, and the items still arrive on the source's own threads. And after a `publishOn` below the source, the data path belongs to the `publishOn` scheduler, as the second line of the output shows.

**publishOn moves the operators after it. subscribeOn moves the source, wherever you write it.**

Now we can decide where a slow call should run. First, let's look at what makes a call slow in the wrong way."""

# ---------------------------------------------------------------- section 2
J_WRAP = """Mono<Integer> loavesLeft(String shop) {
    return Mono.fromCallable(() -> stock.loavesLeft(shop))     // lazy: runs per subscription
            .subscribeOn(Schedulers.boundedElastic());        // on a thread that may block
}"""
K_WRAP = """fun loavesLeft(shop: String): Mono<Int> =
    Mono.fromCallable { stock.loavesLeft(shop) }              // lazy: runs per subscription
        .subscribeOn(Schedulers.boundedElastic())             // on a thread that may block"""
J_OUTER = """// Naive: looks concurrent, isn't
Flux.fromIterable(shops)
        .flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s)))
        .subscribeOn(Schedulers.boundedElastic());      // one thread makes every call, in turn"""
K_OUTER = """// Naive: looks concurrent, isn't
Flux.fromIterable(shops)
    .flatMap { s -> Mono.fromCallable { stock.loavesLeft(s) } }
    .subscribeOn(Schedulers.boundedElastic())           // one thread makes every call, in turn"""

S2 = """The bakery keeps its stock in an old database, a program that stores data on disk and answers questions about it. The bakery's program reaches it through a blocking driver, a library that holds the calling thread until the database answers, like a worker waiting on the phone. `stock.loavesLeft("shop-7")` takes about 100 ms, and for all of that time its thread does nothing else. That's a **blocking call**. Reading a file with `Files.readAllLines` is one too, and so is any older client library that waits for its answers.

Run one on `parallel`, and you take one of its few workers off the belts. Four slow calls on a 4-core machine stop every timer and every other chain that shares that team. Reactor's FAQ gives the standard wrapper:

""" + pair(J_WRAP, K_WRAP) + """

`fromCallable` makes the call lazy and turns a thrown exception into `onError` (Mono and Flux). `subscribeOn` puts the call on a thread that is allowed to block. As the FAQ says, `subscribeOn` doesn't subscribe to anything. It only says where the work runs once somebody subscribes.

For many calls, the `subscribeOn` must sit on each inner `Mono`. This version looks concurrent:

""" + pair(J_OUTER, K_OUTER) + """

`flatMap` subscribes to each inner on the thread it is running on, and a `fromCallable` runs right there, as it is subscribed. So the calls take turns on one thread. `BlockingCallDemo`, in the Try it, makes eight calls of 100 ms three ways:

```text
1. fromCallable, no scheduler      8 calls in 893 ms on 1 thread(s), e.g. main (virtual=false)
2. subscribeOn on the outer Flux   8 calls in 813 ms on 1 thread(s), e.g. boundedElastic-1 (virtual=false)
3. subscribeOn on each call        8 calls in 116 ms on 8 thread(s), e.g. boundedElastic-4 (virtual=false)
```

The second line is the trap: eight calls, one worker, and a queue at the phone. With `subscribeOn` inside the `flatMap`, the same eight calls took 116 ms on eight threads, about seven times faster on this busy machine. Then cap them with `flatMap`'s concurrency argument from Transforming streams, so that a stock database that allows 20 connections isn't asked for 40 at once.

**A blocking call needs fromCallable and subscribeOn(boundedElastic) on its own Mono.**

Since Reactor 3.6, `boundedElastic` can use virtual threads, the light threads from Part 1 that let go of their carrier thread while they wait. On JDK 21 or later, start the JVM with `-Dreactor.schedulers.defaultBoundedElasticOnVirtualThreads=true`, and the shared `boundedElastic()` runs every task on a new virtual thread, named `loomBoundedElastic-N`. The caps stay the same, and the Javadoc suggests raising `reactor.schedulers.defaultBoundedElasticSize` when you turn it on. The property is read once, when Reactor's `Schedulers` class loads, so put it on the command line. The virtual threads track applies here too: on JDK 21 to 23, a driver that blocks inside `synchronized` pins its carrier.

Wrapping a call moves it off the wrong thread. The last trap is code that tries to wait in the middle of a chain."""

# ---------------------------------------------------------------- section 3
J_BLOCK = """loaves.map(n -> worth(n, prices.pricePerLoaf().block()))           // Naive: throws on a parallel thread
loaves.flatMap(n -> prices.pricePerLoaf().map(p -> worth(n, p)))    // composes instead"""
K_BLOCK = """loaves.map { n -> worth(n, prices.pricePerLoaf().block()!!) }      // Naive: throws on a parallel thread
loaves.flatMap { n -> prices.pricePerLoaf().map { p -> worth(n, p) } }   // composes instead"""

S3 = """`block()` subscribes and makes the calling thread wait until the `Mono` finishes, as Mono and Flux showed. On a `parallel` or `single` thread, that's a bug, and Reactor checks for it: `block()`, `blockFirst()`, `blockLast()`, `toIterable()` and `toStream()` all throw `IllegalStateException` there.

The bug shows up in code like the first line below, once the item comes from a timer, a timeout or a non-blocking client. The bakery wants to know what the loaves in a shop are worth, at the current price per loaf from its price list, a non-blocking client:

""" + pair(J_BLOCK, K_BLOCK) + """

`BlockInParallelDemo`, in the Try it, runs both lines, with the count of loaves arriving from a timer:

```text
1. block() inside map:  block()/blockFirst()/blockLast() are blocking, which is not supported in thread parallel-1
2. flatMap instead:     250.00
```

The `flatMap` version doesn't wait at all. It hands the price lookup to the chain and carries on when the price arrives: 100 loaves at 2.50 each.

The check is a safety net with holes in it. `Mono.just(x).block()` takes a shortcut for a value that is already there, and doesn't check the thread at all. So a unit test whose stubs return `Mono.just` passes, and the bug waits patiently for the real server. The check also only knows threads that carry Reactor's `NonBlocking` marker, a small interface that its own threads implement. A thread that some other library created isn't marked, so `block()` there works, and holds that thread until the answer comes.

To find the blocking calls that the check misses, the Reactor team has a separate tool, BlockHound (not in the labs). It's a Java agent, a library loaded when the JVM starts that changes classes as they load. It throws when a non-blocking thread calls something like `Thread.sleep` or a blocking read from the network.

So where is `block()` fine? In `main`, in a test (though `StepVerifier` is better), and at the edge where reactive code meets code that waits anyway, on a thread that is yours to block. On `boundedElastic` it's allowed, and it costs you one of a limited set of threads. Inside a chain, there is always an operator that composes instead: `flatMap`, `zipWith` or `then`.

**Inside a chain, compose with flatMap. Keep block() for the edges.**

That leaves one question for the place where most reactive code runs: a web server."""

ASIDE = {
    "title": "Where do a web server's threads fit in?",
    "body": "If you write web services, the server hands each request to your code on one of its own threads. A reactive server, such as the one under Spring WebFlux, uses a few event-loop threads, each serving many visitors without ever waiting (Why reactive). Those threads are marked non-blocking, so a `block()` there throws the same error, naming a thread such as `reactor-http-nio-2`. A blocking database call in a `map` throws nothing at all. It just stops every visitor that thread serves until the database answers, so wrap it exactly as the section on blocking calls shows.",
}

# ---------------------------------------------------------------- figure: who runs each part of a chain
BX = [15, 126, 237, 348, 459, 570]
BW = 95
names = [("Flux.range", None), ("map", None), ("publishOn", "single()"), ("filter", None),
         ("subscribeOn", "boundedElastic()"), ("subscriber", None)]
SVG = ('<svg viewBox="0 0 680 196" role="img" aria-label="A chain range, map, publishOn(single), filter, subscribeOn(boundedElastic), subscriber. '
       'The subscribe call travels up from the subscriber on main and switches to boundedElastic at subscribeOn. '
       'Data flows down on boundedElastic until publishOn, then on single.">')
c = [x0 + BW / 2 for x0 in BX]
SVG += f'<text class="t-s t-m" x="{(c[4] + c[5]) / 2:.0f}" y="22" text-anchor="middle">on main</text>'
SVG += f'<line class="ln-d" x1="{c[5]:.0f}" y1="32" x2="{c[4] + 4:.0f}" y2="32" marker-end="url(#arr)"/>'
SVG += f'<text class="t-s t-b" x="{(c[0] + c[4]) / 2:.0f}" y="22" text-anchor="middle">subscribe() and request(n) continue on boundedElastic-1</text>'
SVG += f'<line class="ln-d" x1="{c[4]:.0f}" y1="32" x2="{c[0] + 4:.0f}" y2="32" marker-end="url(#arr)"/>'
for i, (x0, (n, sub)) in enumerate(zip(BX, names)):
    cls = "box-a" if n == "publishOn" else ("box-b" if n == "subscribeOn" else "box")
    SVG += f'<rect class="{cls}" x="{x0}" y="46" width="{BW}" height="38" rx="8"/>'
    SVG += f'<text class="t-s" x="{x0 + BW / 2:.0f}" y="69" text-anchor="middle">{n}</text>'
    if sub:
        tcls = "t-a" if n == "publishOn" else "t-b"
        SVG += f'<text class="t-s {tcls}" x="{x0 + BW / 2:.0f}" y="102" text-anchor="middle">{sub}</text>'
    if i < 5:
        SVG += f'<line class="ln" x1="{x0 + BW + 1}" y1="65" x2="{BX[i + 1] - 2}" y2="65" marker-end="url(#arr)"/>'
mid = c[2]
SVG += f'<rect class="box-b" x="15" y="116" width="{mid - 15:.0f}" height="28" rx="8"/>'
SVG += f'<text class="t-s" x="{(15 + mid) / 2:.0f}" y="135" text-anchor="middle">items on boundedElastic-1</text>'
SVG += f'<rect class="box-a" x="{mid:.0f}" y="116" width="{BX[5] + BW - mid:.0f}" height="28" rx="8"/>'
SVG += f'<text class="t-s" x="{(mid + BX[5] + BW) / 2:.0f}" y="135" text-anchor="middle">items on single-1</text>'
SVG += '<text class="t-s t-m" x="340" y="172" text-anchor="middle">items flow left to right; the subscription travels right to left, and subscribeOn switches its thread</text>'
SVG += '</svg>'

# ---------------------------------------------------------------- closing
CLOSING = """We started with a phone at the slicing station and a worker who couldn't put it down. Reactor's workers are threads, and by default the one that delivers a signal works every station after it. `publishOn` hands the belt to another team, `subscribeOn` says who starts the oven, and slow calls go to `boundedElastic`, one wrapped call per inner `Mono`.

Now search your own code for `.block()` inside a `map` or `flatMap`, and for a `subscribeOn` written after a `flatMap` of `fromCallable` calls.

Next, we'll come back to the packer's slip. `publishOn` quietly asked for 256 items at a time. Who writes the slips in real code, and what do we do with a source that can't read them?"""

# ---------------------------------------------------------------- compare, worked, drill
CJ = '''// Reactor: say where each part of the chain runs
Mono<Report> stockReport(String shop) {
    return Mono.fromCallable(() -> stock.linesFor(shop))      // blocking database call...
            .subscribeOn(Schedulers.boundedElastic())          // ...so the source runs here
            .publishOn(Schedulers.parallel())                  // what follows runs here
            .map(lines -> report.render(lines));               // CPU-heavy page layout
}'''
CK = '''// Kotlin coroutines: switch the dispatcher around each block of work
suspend fun stockReport(shop: String): Report {
    val lines = withContext(Dispatchers.IO) { stock.linesFor(shop) }   // blocking database call
    return withContext(Dispatchers.Default) { report.render(lines) }   // CPU-heavy page layout
}'''

W0 = '''Mono<OrderView> view(Mono<OrderRequest> request) {
    return request
            .map(req -> orders.find(req.orderId()))     // blocking database call, about 30 ms
            .map(OrderView::from);
}'''
W0K = '''fun view(request: Mono<OrderRequest>): Mono<OrderView> =
    request
        .map { req -> orders.find(req.orderId) }       // blocking database call, about 30 ms
        .map(OrderView::from)'''
W2 = '''Mono<OrderView> view(Mono<OrderRequest> request) {
    return request
            .flatMap(req -> Mono.fromCallable(() -> orders.find(req.orderId()))   // 1. wrap the blocking call
                    .subscribeOn(Schedulers.boundedElastic()))                    // 2. run it off the server's thread
            .map(OrderView::from);                                                // 3. continues on boundedElastic
}'''
W2K = '''fun view(request: Mono<OrderRequest>): Mono<OrderView> =
    request
        .flatMap { req ->
            Mono.fromCallable { orders.find(req.orderId) }         // 1. wrap the blocking call
                .subscribeOn(Schedulers.boundedElastic())          // 2. run it off the server's thread
        }
        .map(OrderView::from)                                      // 3. continues on boundedElastic'''
W3 = '''@Test
void lookupRunsOnBoundedElastic() {
    AtomicReference<String> thread = new AtomicReference<>();
    orders.onFind(() -> thread.set(Thread.currentThread().getName()));
    Mono<OrderRequest> request = Mono.delay(Duration.ofMillis(5))         // 4. arrive on a non-blocking thread,
            .thenReturn(new OrderRequest("order-42"));                    //    as the real server does

    StepVerifier.create(page.view(request)).expectNextCount(1).verifyComplete();
    assertThat(thread.get()).startsWith("boundedElastic-");
}'''
W3K = '''@Test
fun `lookup runs on boundedElastic`() {
    val thread = AtomicReference<String>()
    orders.onFind { thread.set(Thread.currentThread().name) }
    val request = Mono.delay(Duration.ofMillis(5))                          // 4. arrive on a non-blocking thread,
        .thenReturn(OrderRequest("order-42"))                               //    as the real server does

    StepVerifier.create(page.view(request)).expectNextCount(1).verifyComplete()
    assertThat(thread.get()).startsWith("boundedElastic-")
}'''

DJ = '''Mono<Recipe> recipe(String id) {
    return Mono.fromCallable(() -> archive.fetchRecipe(id))    // lazy, exceptions become onError
            .subscribeOn(Schedulers.boundedElastic());         // a thread that may block
}

Flux<Recipe> recipes(List<String> ids) {
    return Flux.fromIterable(ids)
            .flatMap(this::recipe, 8);                         // each inner has its own subscribeOn
}'''
DK = '''fun recipe(id: String): Mono<Recipe> =
    Mono.fromCallable { archive.fetchRecipe(id) }              // lazy, exceptions become onError
        .subscribeOn(Schedulers.boundedElastic())              // a thread that may block

fun recipes(ids: List<String>): Flux<Recipe> =
    Flux.fromIterable(ids)
        .flatMap({ recipe(it) }, 8)                            // each inner has its own subscribeOn'''

L = {
 "id": "rx-06",
 "title": "Schedulers: publishOn, subscribeOn and blocking calls",
 "minutes": 35,
 "goal": "By the end you can predict which thread runs each step of a Reactor chain, move work with publishOn and subscribeOn on purpose, wrap blocking calls so they really run concurrently on boundedElastic, and replace block() inside a chain with composition.",
 "opening": OPENING,
 "warmup": {
  "q": "The bakery's program asks its old stock book how many loaves each of 10 shops has left. Each call blocks its thread for 100 ms. The code is `Flux.fromIterable(shops).flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s))).subscribeOn(Schedulers.boundedElastic())`. About how long does it take?",
  "options": [
   "About 100 ms: `flatMap` runs them concurrently on boundedElastic threads",
   "About 1 second: all ten run in turn on one boundedElastic thread",
   "About 250 ms: boundedElastic has one thread per core",
   "It fails, because `fromCallable` cannot block"
  ],
  "answer": 1,
  "why": "`subscribeOn` on the outer Flux moves the subscription to one boundedElastic thread. `flatMap` subscribes to each inner `fromCallable` on that same thread, and a `fromCallable` runs its call as it is subscribed, so the calls take turns. To get concurrency, put `subscribeOn` on each inner Mono. `flatMap` only subscribes to many inners at once; the threads have to come from the inners. The section on blocking calls measures all three versions."
 },
 "sections": [
  {
   "h": "Who works each station: the thread that delivered the last signal",
   "body": S0,
   "try": {
    "title": "A tour of the threads",
    "minutes": 3,
    "steps": [
     "`ThreadTourDemo` prints the thread of each step in three chains: no scheduler at all, a chain after `Mono.delay`, and a `flatMap` over three timers. Predict each thread name before you run it.",
     "Run it.",
     "In part 3, add `.publishOn(Schedulers.single())` right before the `doOnNext` (and import `reactor.core.scheduler.Schedulers`). Predict the threads, then run it again."
    ],
    "code": code("ThreadTourDemo"),
    "expect": "Part 1 runs entirely on `main`, and the source and the subscriber take turns item by item. Part 2 runs on `parallel-1`, the timer's thread, including the `map` after it. Part 3 delivers the three items on three different parallel threads (for example `parallel-2`, `parallel-3`, `parallel-4`). After your change, all three arrive on `single-1`: a hand-over point moved them to one worker."
   },
   "refs": [
    {"title": "Reactor reference: Threading and Schedulers (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/schedulers.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "publishOn moves what comes after it; subscribeOn moves the source",
   "body": S1,
   "figure": {"svg": SVG, "caption": "publishOn splits the data path: before it, items run where the source runs; after it, on single. subscribeOn changes the thread of the subscription on its way up, so the source runs on boundedElastic even though subscribeOn is written near the end."},
   "try": {
    "title": "publishOn, subscribeOn, and two of them",
    "minutes": 4,
    "steps": [
     "`PublishSubscribeDemo` runs three chains: `publishOn` in the middle, `subscribeOn` written after a `publishOn`, and two `subscribeOn` calls in a row. Predict the thread of every printed line.",
     "Run it.",
     "In part 3, swap the two `subscribeOn` lines so that `boundedElastic` is nearest the source. Predict, then run it again."
    ],
    "code": code("PublishSubscribeDemo"),
    "expect": "Part 1: the source on `main`, after `publishOn` on `single-1`. Part 2: the source on `boundedElastic-1` although `subscribeOn` is written last, and after `publishOn` still `single-1`. Part 3: everything on `single-1`, because the `subscribeOn` nearest the source wins. After the swap, everything runs on a `boundedElastic` thread."
   }
  },
  {
   "h": "A slow phone call at one station: wrap blocking calls for boundedElastic",
   "body": S2,
   "try": {
    "title": "Eight blocking calls, three ways",
    "minutes": 5,
    "steps": [
     "`BlockingCallDemo` makes eight stock-book calls that each block for 100 ms: with no scheduler, with `subscribeOn` on the outer Flux, and with `subscribeOn` on each inner call. Predict the time and the number of threads for each.",
     "Run it.",
     "Run it again with `-Pargs=virtual` added to the command. The demo then sets `reactor.schedulers.defaultBoundedElasticOnVirtualThreads` before Reactor loads its schedulers. Look at the thread names and the `virtual` flag."
    ],
    "code": code("BlockingCallDemo"),
    "expect": "No scheduler: about 800 ms on `main` (869 to 893 ms in runs here). `subscribeOn` outside: about 800 ms on one thread, `boundedElastic-1`. `subscribeOn` on each call: a little over 100 ms on 8 threads (115 to 125 ms here). With `-Pargs=virtual`, the thread names become `loomBoundedElastic-N` and `virtual=true`, with the same timings: virtual threads change the cost of each thread, not the shape of the chain."
   },
   "refs": [
    {"title": "Reactor FAQ: How do I wrap a synchronous, blocking call? (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/faq.adoc", "kind": "docs"},
    {"title": "What's new in reactor-core 3.6.0 (Spring blog): virtual-thread boundedElastic", "url": "https://spring.io/blog/2023/10/31/what-new-is-coming-in-reactor-core-3-6-0", "kind": "read"}
   ]
  },
  {
   "h": "Keep block() at the edges of reactive code",
   "body": S3,
   "aside": ASIDE,
   "try": {
    "title": "When block() is refused",
    "minutes": 4,
    "steps": [
     "`BlockInParallelDemo` works out what 100 loaves are worth at the price per loaf, four ways: `block()` inside `map`, `flatMap`, `block()` on a `Mono.just`, and `block()` after `publishOn(boundedElastic())`. The count arrives from `Mono.delay`, so on a parallel thread. Predict which lines fail.",
     "Run it.",
     "Change `loaves` to `Mono.just(100)` and run it again. Predict line 1 first."
    ],
    "code": code("BlockInParallelDemo"),
    "expect": "Line 1 prints the `block()/blockFirst()/blockLast() are blocking, which is not supported in thread parallel-1` message. Lines 2, 3 and 4 print `250.00`: `flatMap` composes, `Mono.just` takes its shortcut, and `boundedElastic` threads are allowed to block. With `Mono.just(100)` as the count, line 1 also prints `250.00`, because `map` now runs on `main`. Same code, different thread, different result: that's why tests with `Mono.just` stubs miss this bug."
   },
   "refs": [
    {"title": "BlockHound README", "url": "https://github.com/reactor/BlockHound/blob/master/README.md", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Choosing threads in Reactor and in coroutines",
  "java": {"title": "StockReport.java (Reactor)", "src": CJ},
  "kotlin": {"title": "StockReport.kt (coroutines)", "src": CK},
  "note": "Reactor attaches threads to positions in a chain: `subscribeOn` picks where the source runs and `publishOn` picks where the rest runs. Coroutines attach them to blocks of code: `withContext(Dispatchers.IO)` runs the block on the IO dispatcher, the coroutines' version of a scheduler, and comes back afterwards, so you read the thread switches from top to bottom. The pools line up: `Dispatchers.Default` has one thread per core like `parallel`, and `Dispatchers.IO` is for blocking calls like `boundedElastic`. Kotlin `Flow` has one more twist: `flowOn(Dispatchers.IO)` changes where everything *above* it runs, which is closer to `subscribeOn` than to `publishOn`. `kotlinx-coroutines-reactor` bridges the two worlds with `Scheduler.asCoroutineDispatcher()`."
 },
 "worked": {
  "title": "Get a blocking lookup off the server's thread",
  "steps": [
   {"say": "The bakery's website has a page that shows the status of a cake order. The web server hands each request to this method as a `Mono`, and the method looks the order up in the old order database through `orders`, a repository (a class that wraps the database calls) that blocks. When the shop is busy, every page on the website slows down, not just this one. Find the cause before you read on.",
    "code": W0, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "The request arrives on one of the server's few event-loop threads, the threads that serve many visitors without waiting, and `map` runs on whatever thread delivered the item. So the 30 ms database call runs on the event loop. While it waits for the database, every other visitor that loop serves waits too. Nothing throws, because a database call isn't a `block()`, and a unit test with `Mono.just(request)` runs it on the test thread, where it looks fine.", "code": "", "lang": ""},
   {"say": "Turn the lookup into its own inner Mono, wrapped and moved off the server's thread. The `map` after it now runs on the boundedElastic thread that finished the lookup, which is fine for a cheap conversion. A heavy step would get a `publishOn(Schedulers.parallel())` first.",
    "code": W2, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Pin it with a test. The trick is to make the request arrive on a non-blocking thread, as it does in production, and to record the thread the repository sees.",
    "code": W3, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A reactive front for the old stock book",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/ShopStock.java", f"{lab}/main/{P}/StockBook.java", f"{lab}/main/{P}/PriceList.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l06.*'",
  "steps": [
   "Run the tests once. All five fail. `StockBook` is the blocking stock book, `PriceList` is the non-blocking price list, and `ShopStock` puts a reactive front on both. Read the failure of the `stockValue` test: it's the `block()` message from the last section.",
   "Write `loavesLeft(shop)`: wrap `stock.loavesLeft(shop)` so that it runs only when subscribed, on `Schedulers.boundedElastic()`.",
   "Write `loavesLeftIn(shops)`: the counts for all the shops in the input order, with at most 4 stock-book calls at a time. Reuse `loavesLeft`.",
   "Fix `stockValue` without `block()`. Then run the tests until all five pass, and run them once more: the concurrency test must pass every time."
  ],
  "hints": [
   "If the boundedElastic test reports the thread `Test worker`, the call ran on the thread that subscribed: `subscribeOn` is missing.",
   "If `loavesLeftIn` peaks at 1 call in flight, your `subscribeOn` sits on the outer Flux, or `loavesLeft` lacks it. Each inner Mono needs its own.",
   "If it peaks at 20, you used `flatMap` or `flatMapSequential` without the concurrency argument (the default is 256).",
   "If the order test fails, use `flatMapSequential(this::loavesLeft, 4)` from Transforming streams: it runs inners concurrently and emits in source order."
  ],
  "done_when": "All five tests in `ShopStockTest` pass, twice in a row."
 },
 "drill": {
  "title": "Wrap a blocking client from memory",
  "minutes": 4,
  "prompt": "Close this page. `archive.fetchRecipe(id)` is a blocking call to the bakery's old recipe archive. Write `Mono<Recipe> recipe(String id)` that never blocks the subscriber's thread, and `Flux<Recipe> recipes(List<String> ids)` that runs at most 8 calls at once, in any order. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "Without a scheduler, a chain runs on the thread that subscribed; after a timer or a non-blocking client, it runs on whatever thread delivered the item.",
  "`publishOn` moves the operators after it to one worker of a scheduler. `subscribeOn` moves the subscription, and so the source, wherever you write it; with several, the one nearest the source wins.",
  "Wrap blocking calls as `Mono.fromCallable(...).subscribeOn(Schedulers.boundedElastic())`, with `subscribeOn` on each inner Mono, and cap the fan-out with `flatMap`'s concurrency.",
  "On JDK 21 or later, `-Dreactor.schedulers.defaultBoundedElasticOnVirtualThreads=true` (Reactor 3.6+) runs boundedElastic tasks on virtual threads.",
  "`block()` throws on `parallel` and `single` threads and belongs only at the edges. Inside a chain, compose with `flatMap`.",
  "The limit: Reactor only catches `block()` itself, and only on threads it marked. A blocking call on the wrong thread throws nothing, and `Mono.just` stubs hide even `block()`, so tests must deliver items on a non-blocking thread."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "Where do A and B run?\n\n```java\nFlux.range(1, 3)\n        .map(i -> i * 2)                    // A\n        .publishOn(Schedulers.parallel())\n        .map(i -> i + 1)                    // B\n        .subscribeOn(Schedulers.single())\n        .blockLast();\n```\n\n```kotlin\nFlux.range(1, 3)\n    .map { i -> i * 2 }                     // A\n    .publishOn(Schedulers.parallel())\n    .map { i -> i + 1 }                     // B\n    .subscribeOn(Schedulers.single())\n    .blockLast()\n```",
   "options": ["A on `single-1`, B on a parallel thread", "A on `main`, B on a parallel thread", "Both on `single-1`", "A on a parallel thread, B on `single-1`"],
   "answer": 0,
   "why": "`subscribeOn` moves the subscription, so `range` and the `map` right after it run on `single-1`, even though `subscribeOn` is written last. `publishOn` then moves everything below it to a parallel worker. The second option ignores `subscribeOn`; the last one mixes up which operator affects which direction."},
  {"q": "`Mono.fromCallable(stock::load).subscribeOn(Schedulers.parallel()).subscribeOn(Schedulers.boundedElastic())`. Where does `stock.load` run, and is that a problem?",
   "options": [
    "On boundedElastic, the last `subscribeOn`; fine",
    "On a parallel thread, the `subscribeOn` nearest the source; a problem if `load` blocks",
    "On both, one after the other",
    "On the calling thread, because two `subscribeOn` calls cancel out"
   ],
   "answer": 1,
   "why": "Only the `subscribeOn` nearest the source decides where the subscription reaches the source. The outer one adds a hop on the way up and nothing else. So a blocking `load` would run on one of the few parallel threads, the team you must never block."},
  {"q": "A page handler calls `prices.current().block()` inside a `map`. Its unit tests, which stub `prices.current()` with `Mono.just(...)`, pass. On the real server, where the item comes from a non-blocking client, it throws `IllegalStateException`. Why the difference?",
   "options": [
    "The server runs a newer Reactor that bans `block()` everywhere",
    "On the server the `map` runs on a non-blocking thread, which Reactor checks; `Mono.just(...).block()` takes a shortcut and is never checked",
    "`Mono.just` is cold and the client is hot",
    "The unit tests forgot to call `verify()`"
   ],
   "answer": 1,
   "why": "In the tests everything runs on the test thread, and `block()` on a `Mono.just` returns the stored value without any check. On the server the item arrives on a thread marked non-blocking, so the real `block()` call is refused. Replace the `block()` with `flatMap`, and make test stubs emit on a non-blocking thread (for example with `Mono.delay`)."},
  {"q": "You need the loaves left in 200 shops from the blocking stock book, and the stock database allows 20 connections. Which line fits?",
   "options": [
    "`Flux.fromIterable(shops).flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s))).subscribeOn(boundedElastic())`",
    "`Flux.fromIterable(shops).flatMap(s -> Mono.fromCallable(() -> stock.loavesLeft(s)).subscribeOn(boundedElastic()), 20)`",
    "`Flux.fromIterable(shops).publishOn(boundedElastic()).map(stock::loavesLeft)`",
    "`Flux.fromIterable(shops).flatMap(s -> Mono.just(stock.loavesLeft(s)), 20)`"
   ],
   "answer": 1,
   "why": "Each inner call carries its own `subscribeOn`, so up to 20 run at once on boundedElastic threads, matching the database. The first option runs all 200 in turn on one thread. The third also runs them one by one, on one publishOn worker. The last calls the stock book while building each inner, on the caller's thread, so it blocks there."},
  {"q": "From \"Pinning, ThreadLocals and other traps\": you turn on the virtual-thread boundedElastic on JDK 21, and your database driver blocks on network reads inside `synchronized` methods. What happens during those reads?",
   "options": [
    "Nothing special: virtual threads always unmount when they block",
    "Each blocked virtual thread pins its carrier thread until the read returns, so carriers can run out",
    "Reactor detects it and moves the call to a platform thread",
    "The read throws `IllegalStateException` because boundedElastic is non-blocking"
   ],
   "answer": 1,
   "why": "On JDK 21 to 23, a virtual thread that blocks while holding a monitor can't unmount, so it holds its carrier (JDK 24 removed that limit, JEP 491). Reactor doesn't step in. boundedElastic threads, virtual or not, are allowed to block, so there is no `IllegalStateException` either.",
   "from": "vt-04"}
 ],
 "flashcards": [
  {"front": "With no scheduler anywhere, which thread runs a Reactor chain?", "back": "The thread that called `subscribe()`. After a timer or a non-blocking client, the thread that delivered the item."},
  {"front": "What does `publishOn(s)` change?", "back": "The thread of every operator after it (until the next `publishOn`), using one worker of `s`."},
  {"front": "What does `subscribeOn(s)` change?", "back": "The thread of the subscription and the request calls on their way up, so the source runs on `s`, wherever `subscribeOn` is written."},
  {"front": "Two `subscribeOn` calls in one chain: which one decides where the source runs?", "back": "The one nearest the source. The other only adds a thread hop."},
  {"front": "How do you wrap a blocking call in Reactor?", "back": "`Mono.fromCallable(() -> blockingCall()).subscribeOn(Schedulers.boundedElastic())`"},
  {"front": "`flatMap(x -> Mono.fromCallable(...))` followed by `.subscribeOn(boundedElastic())`: do the calls run concurrently?", "back": "No. They run in turn on one boundedElastic thread. Put `subscribeOn` on each inner Mono."},
  {"front": "`Mono.delay(d).map(x -> other.block())`: what happens?", "back": "`IllegalStateException`: `block()` is not supported on the parallel thread where the timer fired. Use `flatMap`."}
 ],
 "terms": [
  {"term": "Scheduler", "plain": "Reactor's source of threads, like an ExecutorService that is also a clock."},
  {"term": "publishOn", "plain": "Moves the operators after it onto a scheduler's thread."},
  {"term": "subscribeOn", "plain": "Moves the subscription, and so the source, onto a scheduler's thread."},
  {"term": "boundedElastic", "plain": "The shared scheduler for blocking calls: up to 10 threads per core, then a bounded queue."},
  {"term": "parallel scheduler", "plain": "The shared scheduler with one thread per core, for CPU work and timers. Never block on it."},
  {"term": "Blocking call", "plain": "A call that holds its thread until an answer comes, such as a database query through a blocking driver."},
  {"term": "Non-blocking thread", "plain": "A thread marked with Reactor's `NonBlocking` interface; `block()` throws on it."},
  {"term": "BlockHound", "plain": "A Java agent from the Reactor team that detects blocking calls on non-blocking threads."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"What's the difference between publishOn and subscribeOn, and which one do I use to call our old stock database from a reactive chain?\" Explain it in your own words.",
  "answer": "Both move work to a scheduler's thread, but in different directions. `publishOn` sits in the stream of items: everything after it runs on the new thread, and everything before it is unchanged. `subscribeOn` changes the thread on which the subscription travels up to the source, so the source itself runs there, no matter where in the chain you write it; if there are several, the one nearest the source wins. For a blocking database call you want the call itself to run on a thread that may block, so you wrap it as `Mono.fromCallable(() -> stock.loavesLeft(shop))` and add `subscribeOn(Schedulers.boundedElastic())` to that Mono. If you make many calls in a `flatMap`, each inner Mono needs its own `subscribeOn`, and you cap the concurrency at the number of connections the database allows."
 },
 "deeper": {
  "minutes": 8,
  "body": "**ParallelFlux.** For CPU-heavy work on many items, `flux.parallel(4).runOn(Schedulers.parallel()).map(this::render).sequential()` splits the stream into 4 rails, runs each rail on its own parallel worker, and merges them back. Without `runOn`, the rails exist but share one thread. `sequential()` merges the rails as items finish, so the original order is lost.\n\n**Tuning the shared schedulers.** System properties set the sizes before the `Schedulers` class loads: `reactor.schedulers.defaultPoolSize` for `parallel`, `reactor.schedulers.defaultBoundedElasticSize` (threads) and `reactor.schedulers.defaultBoundedElasticQueueSize` (queued tasks) for `boundedElastic`. Prefer a dedicated `Schedulers.newBoundedElastic(20, 1_000, \"stock\")` per slow dependency. It works like the bulkhead from the executors track, a wall between pools: one slow dependency can only use up its own threads. Dispose it on shutdown.\n\n**publishOn prefetch.** `publishOn` requests 256 items up front and then tops up, so it also changes the demand the source sees. `publishOn(scheduler, 32)` lowers that. The next lesson looks at demand in detail.\n\n**Coroutines on a Reactor scheduler.** `kotlinx-coroutines-reactor` has `Schedulers.boundedElastic().asCoroutineDispatcher()`, so coroutine code can share the same threads as the Reactor parts of a program."
 },
 "sources": [
  {"title": "Reactor reference: Threading and Schedulers (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/coreFeatures/schedulers.adoc"},
  {"title": "Schedulers source and Javadoc, including the virtual-thread boundedElastic (3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/scheduler/Schedulers.java"},
  {"title": "Reactor FAQ: wrapping blocking calls (source, 3.8.x)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/faq.adoc"},
  {"title": "What's new in reactor-core 3.6.0 (Spring blog, Oleh Dokuka)", "url": "https://spring.io/blog/2023/10/31/what-new-is-coming-in-reactor-core-3-6-0"}
 ]
}
out = ROOT / "content/lessons/rx-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
