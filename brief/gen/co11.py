import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l11"
J = "java/workbench/coroutines/l11"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l11.{cls}{extra}"


def demo(kt, java, extra_kt="", extra_java=""):
    """A Kotlin demo and its runnable Java twin, read from disk so the lesson never drifts."""
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt", extra_kt),
            "file": f"{lab}/demo/{P}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{lab}/demo/{J}/{java}"), "run": run(j, extra_java),
                    "file": f"{lab}/demo/{J}/{java}"}}


def pair(kotlin, java):
    """A Kotlin fence and its Java twin, side by side, as the validator expects."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Kotlin coroutines in the middle, with bridges to three neighbours. '
    'CompletableFuture: await() suspends on a future, future { } returns one to Java. Reactor: mono { } and asFlux() go out, '
    'awaitSingle() and asFlow() come in. Virtual threads: asCoroutineDispatcher() runs coroutines on them, runBlocking blocks one on purpose.">'
    '<rect class="box" x="15" y="24" width="190" height="44" rx="8"/>'
    '<text class="t" x="110" y="51" text-anchor="middle">CompletableFuture</text>'
    '<text class="t-s t-code" x="232" y="38">future.await()</text>'
    '<text class="t-s t-m" x="350" y="38">suspends on a future</text>'
    '<text class="t-s t-code" x="232" y="58">scope.future { }</text>'
    '<text class="t-s t-m" x="350" y="58">returns one to Java</text>'
    '<line class="ln" x1="205" y1="60" x2="262" y2="114"/>'
    '<rect class="box-a" x="250" y="114" width="180" height="60" rx="8"/>'
    '<text class="t" x="340" y="139" text-anchor="middle">coroutines</text>'
    '<text class="t-s t-code" x="340" y="160" text-anchor="middle">suspend fun, Flow</text>'
    '<line class="ln" x1="430" y1="144" x2="488" y2="144"/>'
    '<rect class="box-ok" x="490" y="114" width="175" height="60" rx="8"/>'
    '<text class="t" x="577" y="139" text-anchor="middle">Reactor</text>'
    '<text class="t-s t-code" x="577" y="160" text-anchor="middle">Mono, Flux</text>'
    '<text class="t-s t-code" x="480" y="76">mono { }, asFlux()</text>'
    '<text class="t-s t-m" x="480" y="94">out to Reactor</text>'
    '<text class="t-s t-code" x="480" y="198">awaitSingle(), asFlow()</text>'
    '<text class="t-s t-m" x="480" y="216">in from Reactor</text>'
    '<line class="ln" x1="205" y1="232" x2="262" y2="174"/>'
    '<rect class="box-b" x="15" y="222" width="190" height="44" rx="8"/>'
    '<text class="t" x="110" y="249" text-anchor="middle">virtual threads</text>'
    '<text class="t-s t-code" x="232" y="236">asCoroutineDispatcher()</text>'
    '<text class="t-s t-m" x="410" y="236">run coroutines on them</text>'
    '<text class="t-s t-code" x="232" y="256">runBlocking { }</text>'
    '<text class="t-s t-m" x="350" y="256">block one on purpose</text>'
    '<text class="t-s t-m" x="340" y="290" text-anchor="middle">future { }, await(), mono { } and asFlow() carry cancellation across the bridge</text>'
    '</svg>'
)

TABLE = (
    "| | Virtual threads (JDK 21+) | Kotlin coroutines | Reactor |\n"
    "|---|---|---|---|\n"
    "| Picture it | a cheap helper standing at every pot | one cook, bookmarks and a tree of dishes | a line of stations |\n"
    "| Your code looks like | plain blocking Java or Kotlin | sequential `suspend` functions | chains of operators |\n"
    "| Blocking libraries (database drivers, older SDKs) | the natural fit | `withContext(Dispatchers.IO)` or a virtual-thread dispatcher | wrap them, move them to `boundedElastic` |\n"
    "| Several calls with one deadline | `StructuredTaskScope`, preview in JDK 25 | `coroutineScope`, `async`, `withTimeout` | `Mono.zip`, `timeout` |\n"
    "| Cancellation | interrupts, if the code checks them | flows down the job tree to every child | a cancel signal up the chain |\n"
    "| Streams with backpressure | none built in | `Flow` | `Flux` |\n"
    "| Debugging | ordinary stacks and thread dumps | debug mode and coroutine dumps | operator traces, harder to read |\n"
    "| Java callers | native | through `future { }` or `mono { }` | native |\n"
)

# ---------------------------------------------------------------- opening
OPENING = """Next door lives a neighbour who cooks the old way. Ask her for a pie, and she hands you a ticket: "Come back with this, and the pie will be ready." Our kitchen runs on bookmarks and timers, hers on tickets, and each works fine on its own. The trouble is at the fence. If our cook stands at the neighbour's door holding the ticket, every pot in our kitchen waits with her. And if the guests call dinner off, nobody tells the neighbour, and she bakes a pie that nobody will eat.

In code, the neighbour is Java. A `CompletableFuture` is her ticket, and she may also cook with Reactor or with virtual threads. Shared state and testing coroutines stayed inside Kotlin, but real programs mix both. The easy trap is to cross the fence with whatever works in a demo, a blocking `get()` or a `runBlocking`, and lose the cancel on the way.

In this lesson, we'll cross the fence both ways with futures, then with Reactor, give Java code a door it can use, and weigh the three ways of cooking against each other. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_AWAIT = """// Naive: an IO thread stands at the door for the whole wait, and a cancel never reaches the future
withContext(Dispatchers.IO) { bakery.loavesLeft("rye").get() }

// Fixed: suspends until the future completes; cancelling this coroutine cancels the future
bakery.loavesLeft("rye").await()"""
J_AWAIT = """// Java equivalent: block a thread on the future, or chain on it
int loaves = bakery.loavesLeft("rye").join();                                       // blocks the caller
CompletableFuture<String> note = bakery.loavesLeft("rye").thenApply(n -> n + " left");   // or composes"""

K_DOOR = """class KitchenDoor(private val cook: suspend (Order) -> Outcome) : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun cookAsync(order: Order): CompletableFuture<Outcome> = scope.future { cook(order) }

    override fun close() = scope.cancel()
}"""
J_DOOR = """// Java equivalent: the Java caller's side, which is plain CompletableFuture code
CompletableFuture<String> reply = door.cookAsync(new Order("soup", 4))
    .orTimeout(800, TimeUnit.MILLISECONDS)
    .thenApply(outcome -> "soup: " + outcome);"""

S0 = """Most Java code that waits for something speaks `CompletableFuture`. A **future** is an object that stands for a result that isn't ready yet: the neighbour's ticket. kotlinx.coroutines crosses the fence in both directions with nothing extra on the classpath, since the old `kotlinx-coroutines-jdk8` artifact was merged into the core library in 1.7.

Start with the way in. The bakery has a Java library whose `loavesLeft(bread)` returns a future at once, and the future completes later with the number of loaves left. Here is the naive bridge, which the lab's starting code uses, and the fixed one:

""" + pair(K_AWAIT, J_AWAIT) + """

The naive version "doesn't block the caller", and that's why it ships. But `get()` blocks an IO thread for the whole wait, the cook standing at the neighbour's door. Worse, if the calling coroutine is cancelled, the future never hears about it.

`await()` suspends instead, so no thread waits. It rethrows the future's exception unwrapped, so you catch the `IOException` itself rather than an `ExecutionException`, and it has a fast path for a future that is already done. It also carries the cancel across: if the awaiting coroutine is cancelled, `await()` calls `future.cancel(false)`. That is usually right, because nobody wants the answer any more. When the future is shared, or must finish anyway (a pie already in the oven), use `future.asDeferred().await()`, which waits without cancelling it.

Now the way out. Our kitchen can hand the neighbour a ticket too:

""" + pair(K_DOOR, J_DOOR) + """

`future { }` is a builder like `async`: it starts a coroutine in the scope and hands its result back as a `CompletableFuture`. The link runs both ways. The KDoc says the coroutine is cancelled when the future "is cancelled or otherwise completed", so a Java caller's `cancel(true)`, or an `orTimeout` that fires, cancels the Kotlin coroutine. Give the door a scope it owns, as in Structured concurrency, so that closing the door cancels everything still cooking. `GlobalScope.future` also compiles, and it leaks in exactly the way that lesson described.

Predict three lines before you run `FutureBridge`, in the Try it below:

```text
1. await() on a Java future, then cancel the coroutine:
  future cancelled: true
2. asDeferred().await(), then cancel the coroutine:
  future cancelled: false  (it still completes: apple pie ready)
3. future { } for a Java caller, who cancels it:
  [kotlin] cooking leek was cancelled
  future cancelled: true
```

The cancel crossed the fence both ways. In case 1, cancelling the coroutine cancelled the neighbour's future. In case 3, the Java caller cancelled the future, and the Kotlin coroutine heard it at its next suspension point. Here the picture breaks a little. Cancelling a plain Java future only marks it as cancelled. Whether the work behind it stops depends on the code that made it, just as a real neighbour may or may not read your note. A future from `future { }` always stops its coroutine.

**Cross the fence with `await()` and `future { }`. `get()` and `runBlocking` hold a thread and drop the cancel.**

The neighbour across the road cooks another way again, with Reactor."""

# ---------------------------------------------------------------- section 1
K_REACT = """fun recipeMono(book: RecipeBook, dish: String): Mono<Recipe> = mono { book.recipe(dish) }   // suspend code as a Mono
suspend fun recipeNow(dish: String): Recipe = recipeFromReactor(dish).awaitSingle()      // a Mono in suspend code
fun plates(): Flow<String> = plateFlux().asFlow()                                         // a Flux as a Flow
fun temperatureFlux(): Flux<Int> = temperatures().asFlux()                                // a Flow as a Flux"""
J_REACT = """// Java equivalent: the Reactor side just sees ordinary Mono and Flux values
Mono<Recipe> soup = RecipeMonoKt.recipeMono(book, "soup");             // built by mono { } in Kotlin
Mono<String> both = Mono.zip(soup, RecipeMonoKt.recipeMono(book, "bread")).map(t -> t.getT1() + " | " + t.getT2());
Flux<Integer> temps = ReactorBridgeKt.temperatureFlux();                // a Kotlin Flow through asFlux()"""

S1 = """Reactor, the subject of the reactive track, is a Java library for streams of values. A `Mono` is a recipe for at most one value, a `Flux` is a recipe for many, and nothing runs until someone subscribes. The `kotlinx-coroutines-reactor` module, on this lab's classpath, bridges both:

""" + pair(K_REACT, J_REACT) + """

`mono { }` gives a **cold** Mono: the coroutine starts on subscription, once per subscriber, which is the contract every Reactor user expects (Mono and Flux: nothing happens until you subscribe). It's the recipe card of Flow basics again: each subscriber cooks from it afresh. A `null` result completes the Mono empty, and disposing the subscription cancels the coroutine. Its context may not contain a `Job` ("Mono context cannot contain job in it"), because the subscription owns the coroutine's life, not a scope. `flux { }` does the same for a stream of values, with `send` inside.

In the other direction, `awaitSingle()` waits for exactly one value, and throws `NoSuchElementException` for an empty Mono; `awaitSingleOrNull()` returns `null` instead. `Publisher.asFlow()` collects a Flux as a Flow. The Flow's suspension becomes `request(n)`, the Reactive Streams call by which a subscriber asks for n more values, and cancelling the collector cancels the subscription. `Flow.asFlux()` goes back. The module's README calls the result TCK-compliant: it passes the Reactive Streams test kit (TCK), which checks a publisher against the numbered rules of the specification.

`ReactorBridge`, in the Try it below, looks up a recipe twice through one Mono, then asks for a dish the book doesn't have:

```text
1. mono { } is cold:
  built the Mono; nothing looked up yet
  [kotlin] looking up soup
  awaitSingle() -> soup: 40 minutes
  [kotlin] looking up soup
  awaitSingle() again -> soup: 40 minutes
2. an empty Mono:
  [kotlin] looking up dragon stew
  awaitSingle() threw NoSuchElementException
```

Building the Mono looked up nothing. Each `awaitSingle()` subscribed, and each subscription ran the coroutine again. The recipe book, sensibly, has nothing for dragon stew, so that Mono completed empty, and `awaitSingle()` threw. If one lookup must be shared, `.cache()` on the Mono does it.

Two things need care. Threads first: unless you pass a dispatcher, `mono { }` starts its coroutine on `Dispatchers.Default`, while the Reactor operators around it run wherever their schedulers put them. Then context: Reactor's own `Context`, which a Reactor-based web framework uses for values such as a request id, is visible inside the coroutine as a `ReactorContext` element. Thread-local values are not, for the reason Dispatchers and the coroutine context gave: a coroutine may resume on another thread.

**`mono { }` runs its coroutine once per subscriber, and disposing the subscription cancels it.**

Futures and Monos are shapes Java code already knows. Plain Java can call our suspend functions too, if we give it a door."""

# ---------------------------------------------------------------- section 2
K_SIG = """suspend fun cook(order: Order): Outcome"""
J_SIG = """// what Java sees for the same function: a Continuation parameter and an Object result
public Object cook(Order order, Continuation<? super Outcome> $completion)"""

S2 = """Java can see a suspend function, but it can't call it in any useful way. The compiler adds a `Continuation` parameter, the bookmark of Suspend functions from zero, and changes the return type to `Object`. So from Java the signature looks like this:

""" + pair(K_SIG, J_SIG) + """

You could write a `Continuation` by hand, but you'd be rebuilding a coroutine builder, badly. Give Java callers one of three doors instead.

- A `CompletableFuture` door, built with `future { }`, like the lab's `KitchenDoor`. It's the default for Java code that composes its work as futures.
- A `Mono` door, built with `mono { }`, for code that already lives in Reactor.
- A blocking door that wraps `runBlocking { }`, for Java callers that block anyway: a command-line tool, a JUnit test, or any code running on a virtual thread. Blocking a virtual thread is cheap, so `runBlocking` on one is a fair bridge. It's still wrong inside suspend code, as Builders showed.

Whichever you choose, name the doors so the difference shows: `cook` for Kotlin, `cookAsync` or `cookBlocking` for Java. Keep the suspend function as the one real implementation, and make the others thin wrappers, so the rules for retries and timeouts live in one place. `@JvmOverloads`, `@JvmStatic` and `@JvmName` take care of the rest of what Java sees: default arguments, functions in a companion object, and names that would clash.

A blocking door needs a timeout of its own. `runBlocking { withTimeout(2.seconds) { cook(order) } }` gives the Java caller an upper bound. And an **interrupt** of the calling thread, Java's request to stop from the first track, cancels the coroutine and makes `runBlocking` throw `InterruptedException`. That's the bridge from Java's way of cancelling to Kotlin's.

The lab's Java test, `JavaCallerTest.java`, shows what a Java caller ends up writing against a `future { }` door: `orTimeout`, `thenApply` and `get`, with no Kotlin types in sight beyond the data classes.

Quick check: two Java callers wait for the kitchen through different doors, and each caller's thread is interrupted while the dish is cooking. Caller A uses `cookBlocking`, the `runBlocking` door. Caller B calls `cookAsync(order).get()`. Whose cooking is cancelled? (Only A's. The interrupt reaches `runBlocking`, which cancels its coroutine. B's interrupt only makes `get()` throw `InterruptedException`. The future isn't complete, so the coroutine behind it keeps cooking until someone cancels the future or closes the door.)

**Keep one suspend function as the real code, and give Java thin doors: a future, a Mono, or a blocking call with its own timeout.**

Three neighbours, three ways of cooking. Which one should a new program start with?"""

# ---------------------------------------------------------------- section 3
S3 = """All three solve the problem the virtual threads track opened with. A program that answers many requests at once spends most of its time waiting, for a database or for another web service, and an operating-system thread per waiting request is too expensive. They solve it at different layers. **Virtual threads**, final since JDK 21, are threads so cheap that a waiting one costs almost nothing: a helper at every pot, who simply stands there. Coroutines make waiting explicit with `suspend`, and add a tree of dishes with cancellation and Flow. Reactor turns a request into a line of stations, with backpressure.

`ThreeWays`, in the Try it below, cooks the same dinner each way: soup in 100 ms, the roast in 300 and the salad in 200, all started at once. Predict the times:

```text
coroutines:                       [soup, roast, salad]
  took 304 ms on main
blocking code on virtual threads: [soup, roast, salad]
  took 332 ms
blocking code on Dispatchers.IO: [soup, roast, salad]
  took 318 ms
```

Each one takes as long as the slowest dish, and the Java twin's virtual threads and Reactor `Mono.zip` did the same (309 and 301 ms). Speed doesn't decide between them. The shape of your code does:

""" + TABLE + """
Here is what I would do in a program that answers many requests and talks to a database through a blocking driver.

- Start with virtual threads for request handling that is mostly blocking calls. Database drivers and many older libraries block anyway, and since JDK 24 (JEP 491) `synchronized` no longer pins a virtual thread to its carrier in most cases, so JDK 25 is a good base. Cap each slow neighbour with a semaphore, as Using virtual threads showed.
- Use coroutines in Kotlin code that needs what virtual threads don't give you: several calls with one deadline, a cancel that reaches every child, Flow pipelines, StateFlow-style shared state. Blocking calls inside still go through `withContext(Dispatchers.IO)` or a virtual-thread dispatcher.
- Keep Reactor where a reactive stack already exists, or where you stream with backpressure from end to end. Don't start a new program full of blocking calls on it.

Mixing them is normal, and cheap with the bridges from this lesson. What to avoid is several models in one call path for no reason: a coroutine that calls `runBlocking`, which subscribes to a `Mono`, which blocks on a database. That's three kitchens to boil one egg, and a cancel has to cross every fence on the way.

**Pick one model for each part of the program, and convert only at its edges.**

Whichever you pick, the bridges in this lesson keep a cancel from getting lost at the fence."""

ASIDE = {
 "title": "What if my framework has already chosen?",
 "body": "If you write web services, your framework probably has a switch for each model. Spring WebFlux runs on Reactor, and it also accepts Kotlin `suspend` functions as request handlers, converting at the edge for you. Quarkus can run a request handler on a virtual thread with its `@RunOnVirtualThread` annotation, and its reactive library, Mutiny, has `Uni` and `Multi` types that play the parts of `Mono` and `Flux`, with Kotlin coroutine bridges of its own. The rule of this section still holds: let the framework choose the model at the edge, and stay with it inside each part of your program."
}

# ---------------------------------------------------------------- closing
CLOSING = """We started at the fence between two kitchens, with the neighbour's ticket and a cook who mustn't stand at her door. `await()` waits for a Java future without holding a thread and passes the cancel across. `future { }` and `mono { }` hand Java and Reactor tickets tied to the coroutine, and each of the three ways of cooking suits a different kitchen.

Now search your own code for `.get()` or `.join()` on a future inside a coroutine, and for `runBlocking` inside `supplyAsync`. Each one is a cook standing at the neighbour's door.

That ends this track. Next, in Kotlin Flow in depth, we'll take the recipe card apart. What is a Flow made of, underneath `map` and `collect`?"""

L = {
 "id": "co-11",
 "title": "Coroutines meet Java: futures, Reactor, virtual threads",
 "minutes": 35,
 "goal": "By the end you can bridge suspend code to CompletableFuture and Reactor in both directions without losing cancellation, give Java callers a usable door into Kotlin code, and choose between virtual threads, coroutines and Reactor for a new program.",
 "opening": OPENING,
 "warmup": {
  "q": "A Kotlin class gives Java a door: `fun cookAsync(order: Order): CompletableFuture<Outcome> = scope.future { cook(order) }`. A Java caller adds `.orTimeout(800, MILLISECONDS)`, and the timeout fires. What happens to the Kotlin coroutine?",
  "options": [
   "Nothing: a Java timeout can't reach a Kotlin coroutine",
   "It is cancelled, because the future it belongs to completed",
   "It keeps running, and its result is ignored when it arrives",
   "The JVM interrupts the thread the coroutine runs on"
  ],
  "answer": 1,
  "why": "The future returned by `future { }` is tied to its coroutine: the KDoc says the coroutine is cancelled when the future \"is cancelled or otherwise completed\". `orTimeout` completes that same future exceptionally, so the coroutine is cancelled at its next suspension point. Nothing is interrupted, and nothing keeps running."
 },
 "sections": [
  {
   "h": "Cross the fence with futures: await() in, future { } out",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Each neighbour of the coroutine kitchen has a bridge in and a bridge out, and the bridges that suspend carry cancellation both ways."},
   "try": {
    "title": "Cancel across the fence",
    "minutes": 4,
    "steps": [
     "Read `FutureBridge.kt`. Predict the three `future cancelled` lines.",
     "Run it.",
     "Run the Java twin. It is plain Java calling the Kotlin `SoupKitchen` from the same file, so watch for the `[kotlin]` lines.",
     "In the Java twin, change `orTimeout(50, ...)` to `orTimeout(500, ...)` and run it again. Predict first."
    ],
    "code": demo("FutureBridge.kt", "FutureBridgeJava.java"),
    "expect": "Case 1 prints `future cancelled: true`: cancelling the coroutine cancelled the Java future it was awaiting. Case 2 prints `false`, and the future still completes, because `asDeferred().await()` only waits. Case 3 prints `[kotlin] cooking leek was cancelled`, then `true`. In the Java twin, the two soups make 70 bowls between them, and both the `orTimeout` and the `cancel(true)` produce a `[kotlin] ... was cancelled` line. With a 500 ms timeout the 200 ms soup finishes first, so there is no timeout and no cancel line for it."
   },
   "refs": [
    {"title": "future (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html", "kind": "docs"},
    {"title": "await on CompletionStage (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/await.html", "kind": "docs"}
   ]
  },
  {
   "h": "Cross into Reactor: mono { } out, awaitSingle() and asFlow() in",
   "body": S1,
   "try": {
    "title": "Hand a coroutine to Reactor and back",
    "minutes": 4,
    "steps": [
     "Read `ReactorBridge.kt`. Predict how many `[kotlin] looking up soup` lines print in part 1.",
     "Run it.",
     "Run the Java twin, which uses the same Kotlin `recipeFor` and `temperatureFlux` functions from plain Reactor code.",
     "In the Kotlin file, change `awaitSingle()` in part 2 to `awaitSingleOrNull()` and print the result. Predict first."
    ],
    "code": demo("ReactorBridge.kt", "ReactorBridgeJava.java"),
    "expect": "`[kotlin] looking up soup` prints twice in part 1, once per `awaitSingle()`, and not when the Mono is built: `mono { }` is cold. Part 2 throws `NoSuchElementException` for the empty Mono, and after your change it prints `null`. Part 3 prints three plates and `[reactor] subscription cancelled`, because `take(3)` stopped the Flow. Part 4 prints five temperatures from 180 C to 200 C. The Java twin shows the same cold Mono from the Reactor side, plus `defaultIfEmpty` and `Mono.zip` over two Kotlin lookups."
   },
   "refs": [
    {"title": "kotlinx-coroutines-reactor (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/", "kind": "docs"}
   ]
  },
  {
   "h": "Give Java callers a door they can use",
   "body": S2
  },
  {
   "h": "Virtual threads, coroutines or Reactor: choosing for a new program",
   "body": S3,
   "aside": ASIDE,
   "try": {
    "title": "One dinner, three ways",
    "minutes": 4,
    "steps": [
     "Read `ThreeWays.kt` and its Java twin. Each cooks the same three dishes (100, 300 and 200 ms) at once. Predict every time.",
     "Run both.",
     "In `ThreeWays.kt`, wrap the body of `dinnerWithCoroutines` in `withTimeout(250) { ... }` and run it again. What happens to the dishes still cooking?"
    ],
    "code": demo("ThreeWays.kt", "ThreeWaysJava.java"),
    "expect": "Every version takes about 300 ms: the coroutines, the blocking code on a virtual-thread dispatcher, the blocking code on `Dispatchers.IO`, the plain virtual threads and the Reactor `Mono.zip`. With `withTimeout(250)`, the program fails with `TimeoutCancellationException` at about 250 ms, and the roast and the salad, still cooking, are cancelled with it. Doing that in the Java virtual-thread version would take extra code to cancel the futures yourself."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444", "kind": "read"},
    {"title": "Reactor bridges: kotlinx-coroutines-reactor README", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/master/reactive/kotlinx-coroutines-reactor/README.md", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Three dishes for one table, with one deadline: virtual threads vs coroutines",
  "java": {"title": "Dinner.java", "src": "Dinner dinner(String table) throws Exception {\n    try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {\n        Future<Soup> soup = vt.submit(() -> soupPot.serve(table));      // 1. three blocking calls,\n        Future<Roast> roast = vt.submit(() -> oven.carve(table));       //    one virtual thread each\n        Future<Salad> salad = vt.submit(() -> salads.toss(table));\n        long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(800);\n        try {\n            return new Dinner(                                           // 2. one shared deadline\n                soup.get(remaining(deadline), TimeUnit.NANOSECONDS),\n                roast.get(remaining(deadline), TimeUnit.NANOSECONDS),\n                salad.get(remaining(deadline), TimeUnit.NANOSECONDS));\n        } catch (TimeoutException | ExecutionException e) {\n            soup.cancel(true); roast.cancel(true); salad.cancel(true);  // 3. cancel by hand\n            throw e;\n        }\n    }   // close() waits for every task\n}"},
  "kotlin": {"title": "Dinner.kt", "src": "suspend fun dinner(table: String): Dinner = withTimeout(800) {   // 2. one shared deadline\n    coroutineScope {\n        val soup = async { soupPot.serve(table) }                // 1. three suspending calls,\n        val roast = async { oven.carve(table) }                  //    one coroutine each\n        val salad = async { salads.toss(table) }\n        Dinner(soup.await(), roast.await(), salad.await())\n    }   // 3. a timeout or a failure cancels the other two automatically\n}"},
  "note": "Both take as long as the slowest dish, and both are cheap: a virtual thread or a coroutine per call. The difference is how much of the structure you write yourself. In Java with virtual threads, the calls can stay blocking, which is the big win, but the shared deadline, the step that cancels the other dishes on a failure, and the cleanup are your code. JDK 25's `StructuredTaskScope` covers that, but it is still a preview API (JEP 505). In Kotlin, the deadline is `withTimeout`, the other dishes are cancelled by `coroutineScope`, and the calls must suspend, or be wrapped in `withContext(Dispatchers.IO)` or a virtual-thread dispatcher. Pick the model that matches the code you call: blocking libraries favour virtual threads, suspending ones and complex fan-out favour coroutines."
 },
 "worked": {
  "title": "Give the neighbour's Java program a door into the Kotlin kitchen",
  "steps": [
   {"say": "The kitchen's real work is a Kotlin suspend function with retries: `KitchenService.cook(order)`. The neighbour's Java program must call it from two places: a screen that works with futures and has a Cancel button, and a command-line tool that just waits for the answer. Neither can call the suspend function directly.",
    "code": "class KitchenService(private val stove: Stove) {\n    suspend fun cook(order: Order): Outcome =\n        retryWithBackoff(times = 3, initialDelay = 200.milliseconds, maxDelay = 2.seconds) {\n            stove.cook(order)\n        }\n}", "lang": "kotlin",
    "alt_code": "// what the Java program sees: a Continuation parameter it can't sensibly supply\npublic final class KitchenService {\n    public final Object cook(Order order, Continuation<? super Outcome> $completion) { /* ... */ }\n}", "alt_lang": "java"},
   {"say": "Add Java doors in a small Kotlin class with its own scope. One returns a future, for Java code that composes; one blocks with its own timeout, for callers that block anyway.",
    "code": "class KitchenJavaApi(private val service: KitchenService) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)\n\n    // 1. for Java code that composes futures\n    fun cookAsync(order: Order): CompletableFuture<Outcome> = scope.future { service.cook(order) }\n\n    // 2. for callers that block anyway, with its own upper bound\n    fun cookBlocking(order: Order): Outcome = runBlocking { withTimeout(10.seconds) { service.cook(order) } }\n\n    override fun close() = scope.cancel()\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same doors, if the service were a Java class returning futures\nfinal class KitchenJavaApi implements AutoCloseable {\n    private final KitchenService service;\n    KitchenJavaApi(KitchenService service) { this.service = service; }\n\n    // 1. for Java code that composes futures\n    CompletableFuture<Outcome> cookAsync(Order order) { return service.cookAsync(order); }\n\n    // 2. for callers that block anyway, with its own upper bound\n    Outcome cookBlocking(Order order) throws Exception {\n        return service.cookAsync(order).get(10, TimeUnit.SECONDS);\n    }\n\n    @Override public void close() { }\n}", "alt_lang": "java"},
   {"say": "The screen uses the future door, so its Cancel button can stop the Kotlin work: `cancel(true)` on the future cancels the coroutine, retries and all.",
    "code": "// the screen is Java; this is the Kotlin side it relies on: cancel(true) reaches the coroutine\nval pending = api.cookAsync(order)\npending.cancel(true)   // 3. cancels the coroutine inside KitchenService, retries included", "lang": "kotlin",
    "alt_code": "// 3. the Java screen: show the outcome, or stop the kitchen when Cancel is pressed\nCompletableFuture<Outcome> pending = api.cookAsync(order);\ncancelButton.onClick(() -> pending.cancel(true));       // stops the Kotlin coroutine and its retries\npending.thenAccept(outcome -> screen.show(order.dish() + \": \" + outcome));", "alt_lang": "java"},
   {"say": "A caller written with Reactor gets its own door from the same function, and the retry rules still live in one place.",
    "code": "// 4. a cold Mono for Reactor callers\nfun cookMono(order: Order): Mono<Outcome> = mono { service.cook(order) }", "lang": "kotlin",
    "alt_code": "// 4. the Reactor caller's side\nMono<Outcome> outcome = api.cookMono(order)\n    .timeout(Duration.ofSeconds(10))\n    .onErrorReturn(Outcome.REFUSED);", "alt_lang": "java"},
   {"say": "Self-check: why not write `cookAsync` as `CompletableFuture.supplyAsync { runBlocking { service.cook(order) } }`? (It blocks a pool thread for every order, the future has no link to the coroutine so `cancel(true)` stops nothing, and the work belongs to no scope, so `close()` can't stop it either. That is the bug in this lesson's lab.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Three bridges between Kotlin and Java",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/InteropModel.kt", f"{lab}/main/{P}/KitchenDoor.kt", f"{lab}/main/{P}/LoavesLeft.kt", f"{lab}/main/{P}/RecipeMono.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l11.*'",
  "steps": [
   "Meet the code. `InteropModel.kt` has an `Order`, the bakery's Java library (`JavaBakery`, which returns futures) and a Kotlin `RecipeBook`. `KitchenDoor` lets Java code call a Kotlin `cook` function, `loavesLeftAwait` lets Kotlin code wait for the bakery, and `recipeMono` hands a recipe to Reactor code. All three cross the fence with blocking calls. Run the tests: five of ten fail. One test, `JavaCallerTest.java`, is written in Java, to show what a Java caller of the door writes.",
   "In `KitchenDoor.kt`, give the class a `CoroutineScope(SupervisorJob() + dispatcher)`, return `scope.future { cook(order) }` from `cookAsync`, and cancel the scope in `close`.",
   "In `LoavesLeft.kt`, replace the blocking `get()` with `loavesLeft(bread).await()` (import `kotlinx.coroutines.future.await`).",
   "In `RecipeMono.kt`, return `mono { book.recipe(dish) }` (import `kotlinx.coroutines.reactor.mono`).",
   "Run the tests until all ten pass."
  ],
  "hints": [
   "`future` is an extension on `CoroutineScope` in `kotlinx.coroutines.future`. It is in the core library; no extra artifact is needed.",
   "A coroutine cancelled through `close()` completes its future with a `CancellationException`, which is what a Java caller sees from `get()`.",
   "`mono { }` returns `Mono<T>` from a block that returns `T?`: a `null` completes the Mono empty, so the \"no recipe\" test needs no special case.",
   "The tests on the starting code wait at most a few seconds each, so a stub never hangs the build. On the solution they finish in milliseconds."
  ],
  "done_when": "All ten tests in `JavaInteropTest` and `JavaCallerTest` pass."
 },
 "drill": {
  "title": "Three bridges from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `class PantryDoor(private val pantry: Pantry)` where `Pantry` has `suspend fun stock(item: String): Int`. Give it `fun stockAsync(item: String): CompletableFuture<Int>` for Java and `fun stockMono(item: String): Mono<Int>` for Reactor, both cancellable, and a `close()`. Then write `suspend fun JavaButcher.cutAwait(order: String): Cut` for a Java library whose `cut(order)` returns `CompletableFuture<Cut>`.",
  "answer": {"lang": "kotlin", "src": "class PantryDoor(private val pantry: Pantry) : AutoCloseable {\n    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)\n\n    fun stockAsync(item: String): CompletableFuture<Int> =\n        scope.future { pantry.stock(item) }\n\n    fun stockMono(item: String): Mono<Int> =\n        mono { pantry.stock(item) }\n\n    override fun close() = scope.cancel()\n}\n\nsuspend fun JavaButcher.cutAwait(order: String): Cut = cut(order).await()",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: the Java and Reactor callers of those doors\nclass PantryCaller {\n    private final PantryDoor door;\n    PantryCaller(PantryDoor door) { this.door = door; }\n\n    int stockBlocking(String item) throws Exception {\n        return door.stockAsync(item).get(2, TimeUnit.SECONDS);   // blocks this thread: fine on a virtual thread\n    }\n\n    Mono<String> describe(String item) {\n        return door.stockMono(item).map(n -> item + \": \" + n + \" left\");   // cold, cancellable\n    }\n}"}}
 },
 "recap": [
  "`future.await()` suspends on a `CompletableFuture`, unwraps its exception, and cancels the future if the coroutine is cancelled; `asDeferred().await()` waits without cancelling it.",
  "`scope.future { }` gives Java a `CompletableFuture` for suspend code. Cancelling or completing the future cancels the coroutine, and closing the scope cancels everything still running.",
  "`mono { }` is a cold Mono: one coroutine per subscriber, empty on `null`, cancelled on dispose. `awaitSingle()`, `asFlow()` and `asFlux()` cover the other directions.",
  "Java can't call a suspend function in any useful way. Give it a future door, a Mono door, or a blocking `runBlocking` door with its own timeout, all wrapping one suspend function.",
  "Virtual threads make blocking code cheap, coroutines add structure, cancellation and Flow, and Reactor gives operator pipelines with backpressure. Pick one model per part of the program, and convert at its edges.",
  "The limit: a bridge carries a cancel only as far as the other side listens. A cancelled Java future may still finish its work, and a blocking call inside a coroutine ignores a cancel unless it can be interrupted."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A Java caller holds `f = door.cookAsync(order)`, where `cookAsync` is `scope.future { cook(order) }`, and calls `f.cancel(true)`. What happens on the Kotlin side?",
   "options": ["Nothing: `cancel(true)` only interrupts Java threads", "The coroutine is cancelled at its next suspension point", "The coroutine finishes, and its result is thrown away", "The whole scope is cancelled, with every other order"],
   "answer": 1,
   "why": "The future from `future { }` is tied to its coroutine, and cancelling or completing the future cancels it. Only that coroutine is affected: the scope and its other children carry on, all the more with a `SupervisorJob`."},
  {"q": "A coroutine does `val n = bakery.loavesLeft(\"rye\").await()` and is cancelled while it waits. What happens to the Java future?",
   "options": ["It is cancelled with `cancel(false)`, because nobody wants the answer any more", "It keeps running, and its result is thrown away", "It is completed with `null`", "`await()` blocks until the future finishes, then throws"],
   "answer": 0,
   "why": "`await()` cancels the future when the awaiting coroutine is cancelled. If the future must finish anyway (it is shared, or the work is already under way), use `future.asDeferred().await()`, which waits without cancelling."},
  {"q": "`val r: Mono<Recipe> = mono { book.recipe(\"soup\") }` is built, and then two different callers subscribe to `r`. How many times does `book.recipe` run?",
   "options": ["Once, when `mono { }` is called", "Once, at the first subscription; the second subscriber gets the cached value", "Twice: the Mono is cold, so each subscription runs the coroutine", "Never, unless `block()` is called"],
   "answer": 2,
   "why": "`mono { }` starts the coroutine on subscription, once per subscriber, like any cold Mono. Use `.cache()` on the Mono if one lookup really should be shared."},
  {"q": "A Java program answers 2,000 requests at once. Each request makes three database queries through a blocking driver and one call to a slow web service, and the team writes Java. Which model fits best?",
   "options": ["Rewrite it with Reactor, to avoid blocking", "Rewrite it in Kotlin with coroutines", "A pool of 2,000 platform threads", "Virtual threads, with a semaphore in front of the database"],
   "answer": 3,
   "why": "The code is blocking and in Java, which is exactly what virtual threads make cheap: one per request, with no rewrite. A semaphore keeps the database's connections from being overrun. Reactor and coroutines would mean rewriting every call for little gain, and 2,000 platform threads cost a lot of memory."},
  {"q": "From the virtual threads track: on JDK 21, a virtual thread blocks on a socket read while inside a `synchronized` block. What happens to its carrier thread?",
   "options": ["It is released, as with any blocking call", "It is pinned: it stays blocked with the virtual thread until the read returns", "The JVM throws `IllegalStateException`", "The virtual thread is moved to a new carrier"],
   "answer": 1,
   "why": "On JDK 21 to 23, blocking while holding a monitor pins the virtual thread to its carrier, so the carrier blocks too. JEP 491 in JDK 24 removed most of that pinning, which is one reason to run virtual-thread programs on JDK 25.",
   "from": "vt-04"}
 ],
 "flashcards": [
  {"front": "How do you wait for a `CompletableFuture` inside a coroutine without blocking?", "back": "`future.await()` from `kotlinx.coroutines.future`. It suspends, unwraps the exception, and cancels the future if the coroutine is cancelled."},
  {"front": "How do you await a `CompletableFuture` without cancelling it when the coroutine is cancelled?", "back": "`future.asDeferred().await()`."},
  {"front": "How do you hand suspend code to Java as a `CompletableFuture`?", "back": "`scope.future { suspendCall() }`, with a scope the class owns. Cancelling or completing the future cancels the coroutine."},
  {"front": "When does the coroutine inside `mono { }` run?", "back": "On each subscription. The Mono is cold, a `null` result completes it empty, and disposing the subscription cancels the coroutine."},
  {"front": "What does `awaitSingle()` do on an empty Mono?", "back": "It throws `NoSuchElementException`. `awaitSingleOrNull()` returns `null` instead."},
  {"front": "What does Java see for `suspend fun cook(order: Order): Outcome`?", "back": "`Object cook(Order order, Continuation<? super Outcome> completion)`: give Java a future, Mono or blocking door instead."},
  {"front": "Virtual threads or coroutines for a Java program full of blocking database calls?", "back": "Virtual threads: they make the existing blocking code cheap without a rewrite. Coroutines pay off for structured fan-out, cancellation and Flow in Kotlin."}
 ],
 "terms": [
  {"term": "CompletableFuture", "plain": "A Java object for a result that isn't ready yet; it can be completed, chained and cancelled. The neighbour's ticket."},
  {"term": "future { }", "plain": "A coroutine builder that returns the coroutine's result as a CompletableFuture tied to it."},
  {"term": "await()", "plain": "Suspends until a CompletableFuture completes, without blocking a thread."},
  {"term": "mono { }", "plain": "Turns suspend code into a cold Reactor Mono that runs once per subscription."},
  {"term": "awaitSingle()", "plain": "Suspends until a Mono emits its one value; throws if it completes empty."},
  {"term": "asFlow / asFlux", "plain": "Convert a Reactive Streams publisher to a Flow, and a Flow to a Flux."},
  {"term": "Java door", "plain": "A thin wrapper that lets Java call a suspend function, as a future, a Mono or a blocking call."}
 ],
 "explain_back": {
  "prompt": "A friend is starting a new Java program that answers many requests at once. Each request makes three database queries through a blocking driver and calls one slow web service. Should it use virtual threads, coroutines or Reactor? Give your answer and the reasons.",
  "answer": "I'd use virtual threads. The calls are blocking anyway and the code is Java, so one cheap virtual thread per request lets the team write plain blocking code with no rewrite, and on JDK 25 the old pinning problem with synchronized is mostly gone. I'd put a semaphore in front of the database and the slow web service, so the program can't overrun them. If parts of the program were in Kotlin and needed more than cheap blocking, such as several calls with one deadline, a cancel that reaches every child, or Flow pipelines, I'd use coroutines there, with the blocking calls on Dispatchers.IO or a virtual-thread dispatcher. Reactor would make sense only if a reactive stack already existed or we really streamed with backpressure end to end. Where models meet, I'd convert at the edge with future {}, await(), mono {} and awaitSingle(), which keep cancellation working, and never stack runBlocking and blocking get() calls in one call path."
 },
 "deeper": {
  "minutes": 10,
  "body": "kotlinx.coroutines 1.11 has no built-in virtual-thread dispatcher. `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()` is the supported route, and it gives every dispatch a fresh virtual thread. That makes it a good home for blocking calls inside coroutines, with two cautions. A coroutine blocked inside it still ignores cancellation unless the call is wrapped in `runInterruptible`, which interrupts the virtual thread. And the coroutine scheduler's habit of keeping a coroutine on one worker is lost, so code that relies on per-thread caches gets a new thread every time it resumes.\n\n`CompletionStage.await()` works for any `CompletionStage`, not just `CompletableFuture`, and `Deferred.asCompletableFuture()` goes the other way for a coroutine you already started with `async`. On the Reactor side, `Deferred.asMono()` and `Job.asMono()` give hot Monos for work that is already running, and `Scheduler.asCoroutineDispatcher()` lets coroutines run on a Reactor scheduler, which keeps all the threads of a Reactor-based program in one place.\n\nThe structured-concurrency story differs most across the three. Coroutines enforce it by default. Virtual threads get it through `StructuredTaskScope`, a preview API in JDK 25 (JEP 505) whose shape changed between previews. Reactor has no tree of tasks at all, only operator chains that cancel upstream. When you bridge, the tree ends at the bridge: a `future { }` coroutine belongs to the door's scope, not to the Java caller, which is exactly why the door must own and close that scope.\n\nBridges and tests, the last lesson of the Kotlin Flow in depth track, comes back to `callbackFlow` and the Reactor bridges for whole streams."
 },
 "sources": [
  {"title": "future (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/future.html"},
  {"title": "kotlinx-coroutines-reactor (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-reactor/"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"}
 ]
}
out = ROOT / "content/lessons/co-11.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
