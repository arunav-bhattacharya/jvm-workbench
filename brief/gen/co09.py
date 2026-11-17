import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l09"
J = "java/workbench/coroutines/l09"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l09.{cls}{extra}"


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


helpers = ""
for i, y in enumerate([28, 76, 124, 172]):
    helpers += (f'<line class="ln" x1="270" y1="132" x2="318" y2="{y + 18}" marker-end="url(#arr)"/>'
                f'<rect class="box-a" x="320" y="{y}" width="110" height="36" rx="8"/>'
                f'<text class="t" x="375" y="{y + 23}" text-anchor="middle">helper {i + 1}</text>'
                f'<line class="ln" x1="430" y1="{y + 18}" x2="468" y2="132" marker-end="url(#arr)"/>')

FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="A fan-out and fan-in pipeline: produce sends twelve dishes into a rendezvous channel, the hatch. '
    'Four helper coroutines receive from it, and each dish goes to exactly one helper. Every helper sends what it cooked into a second channel, done, '
    'which the caller reads in one loop. At most four dishes cook at once.">'
    '<rect class="box" x="15" y="110" width="130" height="44" rx="8"/>'
    '<text class="t t-code" x="80" y="137" text-anchor="middle">produce { }</text>'
    '<text class="t-s t-m" x="80" y="174" text-anchor="middle">sends 12 dishes</text>'
    '<line class="ln" x1="145" y1="132" x2="168" y2="132" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="170" y="110" width="100" height="44" rx="8"/>'
    '<text class="t" x="220" y="130" text-anchor="middle">hatch</text>'
    '<text class="t-s" x="220" y="147" text-anchor="middle">rendezvous</text>'
    + helpers +
    '<rect class="box-b" x="470" y="110" width="100" height="44" rx="8"/>'
    '<text class="t" x="520" y="130" text-anchor="middle">done</text>'
    '<text class="t-s" x="520" y="147" text-anchor="middle">fan-in</text>'
    '<line class="ln" x1="570" y1="132" x2="598" y2="132" marker-end="url(#arr)"/>'
    '<rect class="box" x="600" y="110" width="70" height="44" rx="8"/>'
    '<text class="t" x="635" y="137" text-anchor="middle">caller</text>'
    '<text class="t-s t-a" x="375" y="228" text-anchor="middle">at most 4 dishes cooking at once</text>'
    '<text class="t-s t-m" x="340" y="254" text-anchor="middle">each dish is received by exactly one helper; done is closed after joinAll</text>'
    '</svg>'
)

CAP_TABLE = (
    "| Capacity | `send` suspends when | Picture it | Like |\n"
    "|---|---|---|---|\n"
    "| `Channel.RENDEZVOUS` (0, the default) | no receiver is waiting | no shelf: hand to hand | `SynchronousQueue` |\n"
    "| `Channel(n)` | n elements are already waiting | a shelf with n spots | `ArrayBlockingQueue(n)` |\n"
    "| `Channel.BUFFERED` | 64 are waiting (a JVM property changes the default) | a long shelf | `ArrayBlockingQueue(64)` |\n"
    "| `Channel.UNLIMITED` | never: memory is the limit | a shelf with no end | `LinkedBlockingQueue` |\n"
    "| `Channel.CONFLATED` | never: a new element replaces the waiting one | one spot, and the new plate takes it | no JDK equivalent |\n"
)

BP_TABLE = (
    "| Pipeline | The screen shows | Expected | Measured here |\n"
    "|---|---|---|---|\n"
    "| plain | 1, 2, 3 | 1,200 ms: (100 + 300) x 3 | 1,246 ms |\n"
    "| `buffer()` | 1, 2, 3 | 1,000 ms: the probe runs ahead | 1,061 ms |\n"
    "| `conflate()` | 1, 3 | 700 ms: a busy screen skips to the latest | 720 ms |\n"
    "| `collectLatest { }` | starts 1, 2 and 3, finishes only 3 | 600 ms: a new reading cancels the old work | 619 ms |\n"
)

# ---------------------------------------------------------------- opening
OPENING = """Between the kitchen and the dining room of an old house there's a hatch, a small window in the wall with a shelf. The cook puts a plate on the shelf, and on the other side a helper picks it up and carries it to the table. The shelf holds two plates. When it's full, the cook waits. When it's empty, the helper waits. And a plate, unlike a ring of the bell, can be eaten only once.

StateFlow, SharedFlow and hot streams ended at this hatch. Its board and bell sent every value to everyone. A **queue** between coroutines, a line of items taken out in the order they went in, hands each item to exactly one taker, and that's how work gets shared out. The easy trap is the last plate. The helper can't see the cook take off her apron, and unless she tells him, he waits at the hatch all night.

In this lesson, we'll build the hatch and size its shelf, put a team of helpers behind it, take whichever answer comes first, and find the hatches hidden inside flows. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_HATCH = """val hatch = Channel<String>(capacity = 2)
launch {
    for (dish in dinner) hatch.send(dish)   // suspends while the shelf is full
    hatch.close()                           // the last plate: the receiving loop will end
}
for (dish in hatch) serve(dish)              // receives until the hatch is closed and empty"""
J_HATCH = """// Java equivalent: a bounded BlockingQueue, with an end marker because a queue can't be closed
BlockingQueue<String> hatch = new ArrayBlockingQueue<>(2);
Thread.ofVirtual().start(() -> {
    for (String dish : dinner) putQuietly(hatch, dish);   // blocks while the queue is full
    putQuietly(hatch, LAST);
});
for (String dish = hatch.take(); !dish.equals(LAST); dish = hatch.take()) serve(dish);"""

S0 = """A `Channel<T>` connects **coroutines**, pieces of work that can pause without holding a thread, the worker that runs the code. One coroutine calls `send` to put an element in, and another calls `receive` to take one out. Each element is received exactly once, by one receiver. That's the difference from the SharedFlow of the last lesson, where every subscriber heard every ring.

""" + pair(K_HATCH, J_HATCH) + """

Read the Kotlin aloud: the cook puts each dish through the hatch, then says "that's the last one", and the helper serves plates until the hatch is closed and empty. The Java version is the `BlockingQueue` from the first track, with one difference that matters. Where a queue blocks a thread, a channel suspends a coroutine, so a helper waiting at an empty hatch holds no thread at all.

The **capacity** is the size of the shelf: how many elements can wait in the channel before `send` has to suspend. The default, a **rendezvous** channel, has no shelf at all. The cook holds the plate until a helper's hands take it.

""" + CAP_TABLE + """
Predict the four lines before you read them. `ChannelCapacities`, in the Try it below, has a cook who puts five plates through the hatch as fast as she can, and a helper who needs 100 ms per plate:

```text
RENDEZVOUS   send() returned at [38, 142, 247, 348, 448] ms received [1, 2, 3, 4, 5]
capacity 2   send() returned at [0, 0, 0, 101, 201] ms     received [1, 2, 3, 4, 5]
UNLIMITED    send() returned at [0, 0, 0, 0, 0] ms         received [1, 2, 3, 4, 5]
CONFLATED    send() returned at [3, 3, 3, 3, 3] ms         received [1, 5]
```

With no shelf, the cook moved in step with the helper, one plate every 100 ms (the first 38 ms is the program warming up). With a shelf for two, three sends returned at once: two plates on the shelf, and one straight into the helper's hands. Then the cook waited. `UNLIMITED` never waited. `CONFLATED` never waited either, and only plates 1 and 5 were received, because each new plate replaced the one on the shelf.

That waiting has a name. **Backpressure** is a slow receiver slowing down a fast sender, so work doesn't pile up between them. A rendezvous channel gives it for free, which is why it's the default. Add a small shelf to absorb bursts. Be suspicious of `UNLIMITED`, which turns a slow helper into an `OutOfMemoryError` some hours later.

Now the last plate. `for (dish in hatch)` ends only when the channel is closed and empty. Delete `hatch.close()` in the Try it, and the program never ends. The helper waits at the hatch, loyal to a fault, for a plate that will never come. Here the picture breaks: a real helper would see the cook take off her apron. A coroutine can't tell "later" from "never" until someone calls `close()`.

The `produce { }` builder does it for you. It starts a coroutine that sends into a new channel, closes the channel when the block ends or fails, and returns its receiving half, a `ReceiveChannel`. It is still marked `@ExperimentalCoroutinesApi` in kotlinx.coroutines 1.11, so it needs an opt-in.

**A receiver stops only when the channel is closed. Close it, or let `produce` close it.**

A channel is hot, like the board and the bell: plates sit on the shelf whether or not anyone takes them, and a coroutine suspended in `send` waits until someone does. For a stream with one consumer, a cold `Flow` is usually simpler. Channels earn their place when coroutines hand work to each other, and the first job worth handing out is more dishes than one helper can carry."""

# ---------------------------------------------------------------- section 1
K_TEAM = """suspend fun cookAll(dishes: List<String>, helpers: Int, cook: suspend (String) -> String): Map<String, String> =
    coroutineScope {
        val hatch = produce { dishes.forEach { send(it) } }        // fan-out source
        val done = Channel<Pair<String, String>>()                 // fan-in
        val team = List(helpers) { launch { for (dish in hatch) done.send(dish to cook(dish)) } }
        launch { team.joinAll(); done.close() }                    // close once every helper is done
        val result = mutableMapOf<String, String>()
        for ((dish, plate) in done) result[dish] = plate
        result
    }"""
J_TEAM = """// Java equivalent: a fixed pool takes tasks from its queue, a CompletionService collects results
Map<String, String> cookAll(List<String> dishes, int helpers) throws Exception {
    try (ExecutorService pool = Executors.newFixedThreadPool(helpers)) {
        CompletionService<Map.Entry<String, String>> done = new ExecutorCompletionService<>(pool);
        for (String dish : dishes) done.submit(() -> Map.entry(dish, cook(dish)));
        Map<String, String> result = new HashMap<>();
        for (int i = 0; i < dishes.size(); i++) { var e = done.take().get(); result.put(e.getKey(), e.getValue()); }
        return result;
    }
}"""

S1 = """One helper at the hatch carries one plate at a time. Twenty dishes of about 100 ms each take two seconds. The fix in a real kitchen is plain: put more helpers at the same hatch.

That's **fan-out**: several coroutines receive from the same channel. Each element still goes to exactly one of them, and channels are fair: receivers waiting in line are served in the order they asked. So one channel plus N helper coroutines is a team that cooks at most N dishes at once, with no thread pool involved. **Fan-in** is the reverse: many senders into one channel, read by one receiver, like every helper bringing finished plates to one table.

Here is the lab's `cookAll`, which cooks a list of dishes with a fixed number of helpers and returns what each dish became:

""" + pair(K_TEAM, J_TEAM) + """

Walk through it in order. `produce` puts the dishes through a rendezvous hatch, one at a time. `List(helpers) { launch { ... } }` starts the team. Each helper loops over the hatch, cooks what it gets and sends the result into `done`. A separate coroutine waits for the whole team with `joinAll()`, then closes `done`. Finally, the caller's loop reads `done` into a map.

The tricky line is the closer. Close `done` too early, and a helper's `send` throws `ClosedSendChannelException`. Never close it, and the caller's loop waits all night, like the helper in the last section. A coroutine of its own that calls `joinAll()` and then `close()` is the usual answer.

`FanOutFanIn`, in the Try it below, runs the same shape with 20 dishes of 50 to 150 ms each:

```text
4 helpers: {helper 0=5, helper 1=4, helper 2=6, helper 3=5}
20 dishes took 614 ms
```

Twenty dishes of about 100 ms on four helpers should take about 500 ms, and 614 is close on a busy machine. With `-Pargs=1` the same run took 2,181 ms, and with `-Pargs=10` it took 324 ms, two dishes per helper.

Everything sits inside `coroutineScope`, so the pipeline belongs to its caller's job tree, as in Structured concurrency. If one `cook` throws, the scope cancels the producer, the other helpers and the closer, then rethrows. No coroutine is left waiting at a hatch.

Why not `dishes.map { async { cook(it) } }.awaitAll()`? Because that starts every call at once. Order 5,000 loaves that way, and the bakery gets 5,000 phone calls in the same second, and it will not thank you. The team caps them at N. It also gives each helper a natural home for its own things, such as one pan per helper, and it grows into a **pipeline**: stations in a row with a channel between each pair, such as shape, then bake, then pack, each with as many helpers as it needs. The worked example below builds one.

**A fixed team on one channel caps the work at the team's size. Size the team to what the slow part can take.**

A team takes whatever comes through the hatch next. Sometimes, though, you are waiting for two different things, and you want whichever comes first."""

# ---------------------------------------------------------------- section 2
K_SELECT = """val answer = coroutineScope {
    val corner = async { cornerBakery.ask() }
    val market = async { marketBakery.ask() }
    val first = select {
        corner.onAwait { it }
        market.onAwait { it }
        onTimeout(500) { "we bake our own" }   // needs @OptIn(ExperimentalCoroutinesApi::class)
    }
    corner.cancel(); market.cancel()          // hang up on the others
    first
}"""
J_SELECT = """// Java equivalent: anyOf completes with the first future, completeOnTimeout adds a fallback
Object first = CompletableFuture.anyOf(corner, market)
    .completeOnTimeout("we bake our own", 500, TimeUnit.MILLISECONDS)
    .join();
corner.cancel(true); market.cancel(true);     // only marks the futures; the calls may run on"""

S2 = """Picture the cook phoning two bakeries to ask who still has bread tonight. The corner bakery takes 300 ms to answer, and the market bakery 120 ms. She'll take the first answer and hang up on the other. If neither answers within 500 ms, she'll bake her own.

`select { }` is that pair of phone calls. It suspends until the first of several **clauses**, the things it waits on, can complete. Then it runs that clause and drops the rest. The clauses you'll use are `deferred.onAwait` (an `async` result is ready), `channel.onReceive` (a plate is at the hatch), `channel.onSend(value)` (there's room on the shelf) and `onTimeout(ms)`, the kitchen timer.

""" + pair(K_SELECT, J_SELECT) + """

Expect the market's answer after about 120 ms. `SelectFirst`, in the Try it below, printed this:

```text
after 213 ms: market bakery: plenty of sourdough
```

The extra 90 ms is a cold program on a busy machine: the clock starts before the coroutine machinery has loaded. With `-Pargs=100`, a budget of 100 ms, the timer won: `nobody answered within 100 ms: we bake our own bread`.

Three details matter. First, `select` is **biased**: if several clauses are ready at the same moment, the first one listed wins, so list the one you prefer first. Second, hanging up is your job, just as with `anyOf`. The difference is what the hang-up reaches. A coroutine's cancel arrives at the losing call's next suspension point, as Cancellation and timeouts showed. `future.cancel(true)` only marks a Java future as cancelled, and the work behind it may run on. Third, the status is mixed. In 1.11 the `select` builder compiles without an opt-in, the guide still calls select expressions experimental, and `onTimeout` needs `@OptIn(ExperimentalCoroutinesApi::class)`.

Without the timer, this is the lab's `firstOffer`, written for a list of shops: `select { calls.forEach { c -> c.onAwait { it } } }`. The lambda registers one clause per call.

`select` over the `onReceive` clauses of several channels can merge streams by hand, like a helper at two hatches, one for soup and one for bread, who takes whichever plate shows up first. For most merging, though, Flow operators such as `merge` and `combine` are simpler and harder to get wrong. Keep `select` for "the first of these, then stop", and for the rare loop that must react to whichever of several channels has something.

**`select` takes the first clause that's ready, and prefers the first one listed. Cancel the losers yourself.**

Every channel so far was one we made on purpose. The last two hide inside flows, and one of them rescues an old gadget."""

# ---------------------------------------------------------------- section 3
K_PROBE = """fun OvenProbe.readings(): Flow<Reading> = callbackFlow {
    val registration = register { reading -> trySend(reading) }   // called on the probe's thread
    awaitClose { registration.unregister() }                      // runs when the collector stops
}"""
J_PROBE = """// Java equivalent: Flux.create with a sink, and onDispose for the cleanup
Flux<Reading> readings(OvenProbe probe) {
    return Flux.create(sink -> {
        Registration registration = probe.register(sink::next);
        sink.onDispose(registration::unregister);
    });
}"""

S3 = """A flow is sequential: `emit` may be called only from the flow's own coroutine, as Flow basics showed. Some values come from somewhere else. Picture an older wireless oven probe, a thermometer you push into the roast. Its library has a **listener** API: you register a function, and the probe calls it on its own thread with every new reading, until you unregister it. Such a function is a **callback**, code you hand over for someone else to call later.

`callbackFlow` turns that into a Flow by putting a channel inside it. The callback calls `trySend` on the channel, and the collector receives from it:

""" + pair(K_PROBE, J_PROBE) + """

`awaitClose` is not optional. It suspends until the collector goes away, then runs the cleanup. Without it, the block returns right after registering, and `callbackFlow` throws `IllegalStateException` rather than leave the listener behind. That's the bug in the lab's starting code. From the callback, use `trySend`: it never blocks the probe's thread, and it fails if the channel's buffer (64 by default) is full. For a callback that fires once, `suspendCancellableCoroutine` from Suspend functions from zero is the right tool. And `channelFlow` is the same idea for your own coroutines: `launch` several producers inside it, and each one can `send` safely.

The other hidden channels sit inside three **backpressure operators**. Take the guide's numbers, told with our probe: a reading every 100 ms, a screen on the fridge that needs 300 ms to redraw, and three readings. `FlowBackpressure`, in the Try it below, measured them:

""" + BP_TABLE + """
`buffer` keeps every reading and lets the probe run ahead into a channel. `conflate` keeps only the latest, which suits a thermometer and never suits a list of orders. `collectLatest` cancels and restarts the collector's block for each new value, like a cook who starts the sauce again every time someone changes their order. That suits "work out the time left whenever the temperature changes". It's wrong for anything with side effects you can't take back, because the cancelled run may have done half its work.

All three trade memory, completeness and freshness against each other, and the plain flow is the safe default. Reactor makes the same three trades with `onBackpressureBuffer`, `onBackpressureLatest` and `switchMap`, as Backpressure in practice showed in the reactive track, and the Java twin measures them.

**Pick buffer, conflate or collectLatest by asking which values you can afford to lose.**

Every hatch in this lesson moved a plate from one coroutine to another, so no two coroutines ever held the same plate. A kitchen also has things that everyone writes on."""

# ---------------------------------------------------------------- closing
CLOSING = """We started at a hatch between the kitchen and the dining room, with a shelf for two plates. A channel is that hatch: each element goes to one receiver, the capacity sets the pace, and `close()` is the cook's word that the last plate is through. A team of helpers on one hatch caps the work, `select` takes whichever answer comes first, and `callbackFlow` hides a hatch inside a flow.

Now search your own code for `Channel(`. For each channel, find the line that closes it, and ask how full its shelf may get.

Next, we'll hang one shopping list on the fridge for every helper to write on. What happens when coroutines share a variable instead of passing plates?"""

L = {
 "id": "co-09",
 "title": "Channels, select and pipelines",
 "minutes": 35,
 "goal": "By the end you can pick a channel capacity, build a fan-out and fan-in team of workers with produce, race calls with select, turn a listener API into a flow with callbackFlow, and choose between buffer, conflate and collectLatest.",
 "opening": OPENING,
 "warmup": {
  "q": "Three helper coroutines each run `for (dish in hatch) serve(dish)` over the same `Channel<String>`. The cook sends 9 dishes into it, then closes it. How many times is each dish served?",
  "options": [
   "Three times: every helper gets every dish",
   "Exactly once: each element goes to one receiver",
   "Once, but all 9 go to whichever helper started first",
   "It can't work: only one coroutine may receive from a channel"
  ],
  "answer": 1,
  "why": "A channel is a queue: each element is received by exactly one receiver, like a plate taken off the hatch. Several receivers on one channel is fan-out, and the channel serves waiting receivers in turn, so the dishes spread across the three helpers. Sending every value to every subscriber is what a SharedFlow does, the bell from the last lesson."
 },
 "sections": [
  {
   "h": "A channel is the hatch between coroutines, and its shelf sets the pace",
   "body": S0,
   "try": {
    "title": "Five plates, four hatches",
    "minutes": 4,
    "steps": [
     "Read `ChannelCapacities.kt`. The cook sends five plates as fast as she can, and the helper needs 100 ms per plate. For each capacity, predict when each `send` returns, and what is received.",
     "Run it.",
     "Delete the `hatch.close()` line and run it again. Predict first: what happens?",
     "Put the line back, and run the Java twin, which uses three `BlockingQueue`s."
    ],
    "code": demo("ChannelCapacities.kt", "ChannelCapacitiesJava.java"),
    "expect": "Rendezvous: each `send` returns about 100 ms after the previous one, in step with the helper. Capacity 2: the first three return at once (two on the shelf, one handed straight to the waiting helper), then one every 100 ms. Unlimited: all five at once. Conflated: all five at once, but only `[1, 5]` is received, because each new plate replaced the waiting one. Without `close()`, the program never ends: the `for` loop waits for a plate that will never come (stop it with Ctrl+C). The Java twin's three queues match the first three lines."
   },
   "refs": [
    {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html", "kind": "read"}
   ]
  },
  {
   "h": "Fan out to a team of helpers, and fan in to one table",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One channel feeds four helpers, so at most four dishes cook at once; a second channel brings what they cooked back to one place."},
   "try": {
    "title": "Share 20 dishes among a team",
    "minutes": 3,
    "steps": [
     "Read `FanOutFanIn.kt`. Twenty dishes take 50 to 150 ms each. Predict the total time with 4 helpers, and how the dishes spread across them.",
     "Run it, then run it with `-Pargs=1` and `-Pargs=10`.",
     "Run the Java twin, a fixed pool with an `ExecutorCompletionService`."
    ],
    "code": demo("FanOutFanIn.kt", "FanOutFanInJava.java", " -Pargs=1"),
    "expect": "With 4 helpers each one serves about 5 dishes, and the run takes roughly 20 x 100 ms / 4, about 500 to 700 ms. With 1 helper it takes about 2 s. With 10 helpers it takes about 300 ms, and each helper serves about 2. The Java twin spreads the work across its four pool threads the same way."
   }
  },
  {
   "h": "Take whichever answer comes first with select",
   "body": S2,
   "try": {
    "title": "Phone two bakeries at once",
    "minutes": 3,
    "steps": [
     "Read `SelectFirst.kt`. The corner bakery answers in 300 ms, the market bakery in 120 ms, and the budget is 500 ms. Predict the answer and the time.",
     "Run it.",
     "Run it with `-Pargs=100`, a budget of 100 ms. Predict first.",
     "Run the Java twin both ways."
    ],
    "code": demo("SelectFirst.kt", "SelectFirstJava.java", " -Pargs=100", " -Pargs=100"),
    "expect": "With 500 ms the answer is `market bakery: plenty of sourdough` after about 120 ms (more on a cold, busy machine: 213 ms here), and the corner bakery is cancelled. With 100 ms the timer wins: `nobody answered within 100 ms: we bake our own bread`. The Java twin gives the same answers with `anyOf` and `completeOnTimeout`."
   },
   "refs": [
    {"title": "Select expression (Kotlin docs)", "url": "https://kotlinlang.org/docs/select-expression.html", "kind": "read"}
   ]
  },
  {
   "h": "Hatches inside flows: callbackFlow and the backpressure operators",
   "body": S3,
   "try": {
    "title": "Time four ways to keep up",
    "minutes": 4,
    "steps": [
     "Read `FlowBackpressure.kt`. Predict what each of the four lines prints, and roughly how long it takes.",
     "Run it.",
     "In the `conflate()` line, change the collector's `delay(300)` to `delay(50)`. Predict first: does it still skip a reading?",
     "Run the Java twin with the Reactor counterparts."
    ],
    "code": demo("FlowBackpressure.kt", "FlowBackpressureJava.java"),
    "expect": "Plain: `1 2 3` in about 1,200 ms. `buffer()`: `1 2 3` in about 1,000 ms. `conflate()`: `1 3` in about 700 ms. `collectLatest`: `start 1, start 2, start 3, done 3` in about 600 ms. With a 50 ms collector, `conflate()` prints `1 2 3`: it skips only values that arrive while the collector is busy, and now it never is. The Java twin prints the same readings in about the same times with `concatMap`, `onBackpressureBuffer`, `onBackpressureLatest` and `switchMap`."
   },
   "refs": [
    {"title": "callbackFlow (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html", "kind": "docs"},
    {"title": "conflate (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/conflate.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A capped team of helpers: ExecutorService vs a channel and coroutines",
  "java": {"title": "BreadRun.java", "src": "List<String> orderAll(List<String> loaves) throws Exception {\n    try (ExecutorService pool = Executors.newFixedThreadPool(8)) {          // 1. 8 threads = at most 8 calls\n        CompletionService<String> done = new ExecutorCompletionService<>(pool);\n        for (String loaf : loaves) done.submit(() -> bakery.order(loaf));     // 2. every task queued up front\n        List<String> tickets = new ArrayList<>();\n        for (int i = 0; i < loaves.size(); i++) tickets.add(done.take().get());   // 3. fan-in, in finish order\n        return tickets;\n    }   // a failure surfaces at get(); the other tasks keep running until close() waits for them\n}"},
  "kotlin": {"title": "BreadRun.kt", "src": "suspend fun orderAll(loaves: List<String>): List<String> = coroutineScope {\n    val hatch = produce { loaves.forEach { send(it) } }                 // 2. handed out one at a time\n    val tickets = Channel<String>()\n    val team = List(8) { launch { for (loaf in hatch) tickets.send(bakery.order(loaf)) } }   // 1. 8 helpers\n    launch { team.joinAll(); tickets.close() }\n    val result = mutableListOf<String>()\n    for (t in tickets) result += t                                      // 3. fan-in, in finish order\n    result\n}   // a failure cancels the producer and every helper, then rethrows"},
  "note": "Both keep the bakery's phone line at 8 calls at once and collect the tickets in the order the calls finish. The Java version spends 8 threads, which sit blocked while the bakery answers, and it queues every task up front. The Kotlin version spends 8 coroutines, which suspend while waiting, and the rendezvous channel hands out an order only when a helper is free, so a list of a million loaves never sits in a task queue. The bigger difference is failure. In Java, one failed order shows up at `get()`, and the other tasks keep running until `close()` waits for them. In Kotlin, the whole team is one `coroutineScope`, so the first failure cancels the producer and every helper before the exception reaches the caller."
 },
 "worked": {
  "title": "A three-station bake sale",
  "steps": [
   {"say": "The house is baking 600 cookies for a school bake sale. Each one is shaped from the dough (quick), baked (the slow part: 20 ms per cookie in our code, and the oven holds 12 at once), and packed into boxes of 12. In one loop, the oven bakes one cookie at a time: 600 x 20 ms is 12 seconds, with 11 spots in the oven empty the whole time.",
    "code": "suspend fun bakeSale(dough: Dough) {\n    val box = mutableListOf<Cookie>()\n    repeat(600) {\n        val ball = dough.shape()                  // quick\n        val cookie = oven.bake(ball)              // 20 ms, one cookie at a time\n        box += cookie\n        if (box.size == 12) { packer.pack(box.toList()); box.clear() }\n    }\n    if (box.isNotEmpty()) packer.pack(box)\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same single loop\nvoid bakeSale(Dough dough) {\n    List<Cookie> box = new ArrayList<>();\n    for (int i = 0; i < 600; i++) {\n        Ball ball = dough.shape();                // quick\n        Cookie cookie = oven.bake(ball);          // 20 ms, one cookie at a time\n        box.add(cookie);\n        if (box.size() == 12) { packer.pack(List.copyOf(box)); box.clear(); }\n    }\n    if (!box.isEmpty()) packer.pack(box);\n}", "alt_lang": "java"},
   {"say": "Station 1 shapes the dough into a small buffer, a little ahead of the oven. `produce` closes the channel when the dough runs out.",
    "code": "@OptIn(ExperimentalCoroutinesApi::class)\nsuspend fun bakeSale(dough: Dough) = coroutineScope {\n    // 1. shape: one helper, a little ahead of the oven\n    val balls = produce(capacity = 24) {\n        repeat(600) { send(dough.shape()) }\n    }", "lang": "kotlin",
    "alt_code": "void bakeSale(Dough dough) throws Exception {\n    // 1. shape: one thread, a little ahead of the oven\n    BlockingQueue<Ball> balls = new ArrayBlockingQueue<>(24);\n    Thread shaper = Thread.ofPlatform().start(() -> {\n        for (int i = 0; i < 600; i++) putQuietly(balls, dough.shape());\n        putQuietly(balls, Ball.LAST);\n    });", "alt_lang": "java"},
   {"say": "Station 2 fans out to 12 bakers, one per spot in the oven. They fan in to one channel, which a coroutine of its own closes when all 12 are done.",
    "code": "    // 2. bake: 12 helpers, because the oven holds 12 cookies at once\n    val cookies = Channel<Cookie>(capacity = 48)\n    val bakers = List(12) {\n        launch { for (ball in balls) cookies.send(oven.bake(ball)) }\n    }\n    launch { bakers.joinAll(); cookies.close() }", "lang": "kotlin",
    "alt_code": "    // 2. bake: 12 threads, because the oven holds 12 cookies at once\n    BlockingQueue<Cookie> cookies = new ArrayBlockingQueue<>(48);\n    ExecutorService bakers = Executors.newFixedThreadPool(12);\n    for (int i = 0; i < 12; i++) bakers.submit(() -> {\n        for (Ball ball = balls.take(); ball != Ball.LAST; ball = balls.take())\n            cookies.put(oven.bake(ball));\n        balls.put(Ball.LAST);   // pass the end marker on to the next baker\n        return null;\n    });", "alt_lang": "java"},
   {"say": "Station 3 is a single packer, so the boxes stay simple. When `cookies` is closed and empty, the loop ends, and `coroutineScope` returns once every station has finished. If any station throws, the scope cancels the others. The oven is now full: 600 x 20 ms / 12 is about one second instead of twelve.",
    "code": "    // 3. pack: one helper, boxes of 12\n    val box = mutableListOf<Cookie>()\n    for (c in cookies) {\n        box += c\n        if (box.size == 12) { packer.pack(box.toList()); box.clear() }\n    }\n    if (box.isNotEmpty()) packer.pack(box)\n}", "lang": "kotlin",
    "alt_code": "    // 3. pack: one thread, boxes of 12 (the end of station 2 needs its own marker or a latch)\n    bakers.shutdown();\n    List<Cookie> box = new ArrayList<>();\n    while (!(bakers.isTerminated() && cookies.isEmpty())) {\n        Cookie c = cookies.poll(100, TimeUnit.MILLISECONDS);\n        if (c == null) continue;\n        box.add(c);\n        if (box.size() == 12) { packer.pack(List.copyOf(box)); box.clear(); }\n    }\n    if (!box.isEmpty()) packer.pack(box);\n    shaper.join();\n}", "alt_lang": "java"},
   {"say": "Self-check: the packer runs out of boxes and slows to a crawl. Trace what happens to the counter and the oven. (The packer falls behind, `cookies` fills up to 48, the bakers suspend in `send`, `balls` fills up to 24, and the shaper suspends too. Dough never piles up on the counter, and the oven simply waits. Backpressure travels all the way back to the first station.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A team of helpers, an oven probe and the first shop to answer",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/PipelineModel.kt", f"{lab}/main/{P}/CookAll.kt", f"{lab}/main/{P}/ProbeFlow.kt", f"{lab}/main/{P}/FirstOffer.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l09.*'",
  "steps": [
   "Meet the code. `PipelineModel.kt` has the oven probe with its listener API, the `Registration` it hands back, and a shop's `Offer`. `cookAll` cooks a list of dishes, but one at a time; `readings()` should turn the probe into a Flow; `firstOffer` should phone every shop and keep the first answer. Run the tests: five of seven fail.",
   "In `CookAll.kt`, build the team inside `coroutineScope`: `produce` the dishes, start `helpers` coroutines that loop over that channel and send `dish to cook(dish)` into a second channel, close the second channel after `joinAll()`, and read it into a map.",
   "In `ProbeFlow.kt`, keep the `Registration` that `register` returns, and end the block with `awaitClose { registration.unregister() }`.",
   "In `FirstOffer.kt`, start every call with `async`, `select` on their `onAwait` clauses, cancel all the calls, and return the winner.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "`produce` needs `@OptIn(ExperimentalCoroutinesApi::class)` on the function. It closes its channel when its block ends.",
   "Close the second channel from a coroutine of its own: `launch { team.joinAll(); done.close() }`. If you close it after the receiving loop, the loop never ends.",
   "`awaitClose` comes from `kotlinx.coroutines.channels`. It suspends until the collector stops, so it must be the last line of the `callbackFlow` block.",
   "`select { calls.forEach { c -> c.onAwait { it } } }` is a whole `select`: the lambda registers one clause per call. Cancelling a call that already finished does nothing, so you can cancel them all."
  ],
  "done_when": "All seven tests in `ChannelsTest` pass."
 },
 "drill": {
  "title": "Three sinks, from memory",
  "minutes": 5,
  "prompt": "Close this page. The kitchen has three sinks. Write `suspend fun washAll(pans: List<String>)` that calls the suspend function `wash(pan)` for every pan, with at most 3 washes at once, using a channel and 3 helper coroutines. It returns when every pan is clean, and a failure in any wash cancels the rest.",
  "answer": {"lang": "kotlin", "src": "@OptIn(ExperimentalCoroutinesApi::class)\nsuspend fun washAll(pans: List<String>) = coroutineScope {\n    val pile = produce { for (pan in pans) send(pan) }   // closed when the block ends\n    repeat(3) {\n        launch { for (pan in pile) wash(pan) }           // each pan goes to one helper\n    }\n}   // coroutineScope waits for the producer and all three helpers",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a pool of 3 threads, and invokeAll to wait for every task\nvoid washAll(List<String> pans) throws Exception {\n    try (ExecutorService sinks = Executors.newFixedThreadPool(3)) {\n        List<Callable<Void>> tasks = pans.stream()\n            .<Callable<Void>>map(pan -> () -> { wash(pan); return null; })\n            .toList();\n        for (Future<Void> f : sinks.invokeAll(tasks)) f.get();   // rethrows the first failure\n    }   // unlike coroutineScope, the other washes are not cancelled on a failure\n}"}}
 },
 "recap": [
  "A `Channel` is a hatch between coroutines: each element goes to exactly one receiver, and `send` and `receive` suspend instead of blocking a thread.",
  "Capacity is the shelf: rendezvous (the default) hands over directly, `Channel(n)` holds n, `UNLIMITED` never makes the sender wait and can run out of memory, `CONFLATED` keeps only the newest. Close the channel when sending is done, or let `produce { }` close it.",
  "Fan-out, N coroutines on one channel, caps the work at N. Close a fan-in channel after `joinAll()`. Inside `coroutineScope`, one failure cancels the whole pipeline.",
  "`select` takes whichever clause completes first (`onAwait`, `onReceive`, `onTimeout`). It prefers the first clause listed, and cancelling the losers is your job.",
  "`callbackFlow` turns a listener into a Flow and must end with `awaitClose { unregister() }`. `buffer`, `conflate` and `collectLatest` trade completeness for speed or freshness.",
  "The limit: a channel hands each element from one coroutine to another. It does nothing for two coroutines that change the same variable."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "`val hatch = Channel<String>()`. A coroutine runs `hatch.send(\"soup\"); println(\"sent\")`, and nothing ever receives from `hatch`. What happens?",
   "options": ["`sent` prints at once, because `send` puts the element in a buffer", "`send` suspends forever, so `sent` never prints", "`send` throws `IllegalStateException` because nobody is receiving", "The element is dropped and `sent` prints"],
   "answer": 1,
   "why": "The default capacity is rendezvous, a hatch with no shelf: `send` waits until a receiver takes the element. With no receiver it waits forever, and the coroutine never finishes. A buffered channel would accept it at once."},
  {"q": "Four helpers each run `for (dish in hatch) cook(dish)` on the same channel. The cook sends 40 dishes and closes it. Which statement is true?",
   "options": ["Each dish is cooked exactly once, and at most 4 cook calls run at the same time", "Each dish is cooked four times, once per helper", "All 40 go to the first helper, because it started first", "The helpers deadlock, because they compete for the same channel"],
   "answer": 0,
   "why": "A channel is a queue: each element goes to one receiver, and fair receiving spreads the dishes across the waiting helpers. Four helpers means at most four dishes in progress. That is fan-out."},
  {"q": "What happens when this flow is collected?\n\n```kotlin\ncallbackFlow {\n    probe.register { trySend(it) }\n}\n```",
   "options": ["Readings flow normally until the collector cancels", "Nothing is ever emitted, but the collector waits forever", "`callbackFlow` throws `IllegalStateException`, because the block returned without `awaitClose`", "The listener is unregistered automatically when the block returns"],
   "answer": 2,
   "why": "`callbackFlow` requires the block to suspend in `awaitClose { }` until the collector stops. If the block returns while the channel is still open, it throws `IllegalStateException`, and the listener it registered is never unregistered."},
  {"q": "A screen on the fridge shows how many minutes the roast still needs. Working that out from a probe reading takes 300 ms, and readings arrive every 100 ms. Only the latest estimate matters, and a stale calculation should stop at once. Which operator fits?",
   "options": ["`buffer()`", "`conflate()`", "`Channel.UNLIMITED` between the probe and the screen", "`collectLatest { }`"],
   "answer": 3,
   "why": "`collectLatest` cancels the calculation in progress when a new reading arrives, so only the latest is worked out to the end. `conflate` skips readings that arrive while busy, but still finishes every calculation it starts. `buffer` and an unlimited channel work out every stale reading."},
  {"q": "From the reactive track: which Kotlin Flow operator behaves most like Reactor's `onBackpressureLatest()`?",
   "options": ["`buffer()`", "`conflate()`", "`collectLatest { }`", "`flowOn(Dispatchers.IO)`"],
   "answer": 1,
   "why": "Both keep only the newest value while the consumer is busy, and hand it over when the consumer is ready. `collectLatest` is closer to `switchMap`, because it cancels the work in progress. `buffer` is `onBackpressureBuffer`.",
   "from": "rx-07"}
 ],
 "flashcards": [
  {"front": "What is the default capacity of `Channel<T>()`, and what does it mean for `send`?", "back": "`RENDEZVOUS` (0): `send` suspends until a receiver takes the element."},
  {"front": "What does a `Channel.CONFLATED` channel do with a new element when one is already waiting?", "back": "It replaces the waiting one. `send` never suspends, and a slow receiver gets only the newest."},
  {"front": "Several coroutines receive from one channel. How many of them get each element?", "back": "Exactly one. That is fan-out, and it caps the work in progress at the number of receivers."},
  {"front": "When does `for (x in channel)` stop?", "back": "When the channel has been closed and every element in it has been received."},
  {"front": "Why must a `callbackFlow` block end with `awaitClose { ... }`?", "back": "It keeps the flow open until the collector stops, then runs the cleanup. Without it, `callbackFlow` throws `IllegalStateException` and the listener is left registered."},
  {"front": "Two `select` clauses are ready at the same moment. Which one wins?", "back": "The one listed first: `select` is biased toward the first clause."},
  {"front": "`conflate()` vs `collectLatest { }` for a slow collector?", "back": "`conflate` skips values that arrived while busy, but finishes each one it starts. `collectLatest` cancels the block in progress when a new value arrives."}
 ],
 "terms": [
  {"term": "Channel", "plain": "A queue between coroutines: each element is received once, and send and receive suspend instead of blocking. The hatch."},
  {"term": "Rendezvous", "plain": "A channel with no buffer: the sender waits until a receiver takes the element."},
  {"term": "Backpressure", "plain": "A slow receiver slowing down a fast sender, so work doesn't pile up between them."},
  {"term": "Fan-out", "plain": "Several receivers on one channel, so each element is handled by exactly one of them."},
  {"term": "Fan-in", "plain": "Several senders into one channel, read by one receiver."},
  {"term": "produce", "plain": "A builder that starts a coroutine sending into a new channel and closes the channel when the block ends."},
  {"term": "select", "plain": "Waits for whichever of several clauses can complete first, and runs only that one."},
  {"term": "callbackFlow", "plain": "A flow builder with a channel inside, for turning listener callbacks into a Flow."}
 ],
 "explain_back": {
  "prompt": "A friend wants to order 5,000 loaves for a festival with `loaves.map { async { bakery.order(it) } }.awaitAll()`, and the bakery's phone line takes 8 calls at once. Explain the problem, and how a channel and a team of helpers fix it.",
  "answer": "That code starts 5,000 coroutines at once, so the bakery gets 5,000 calls in the same moment, far more than its 8 lines. Most of them get a busy signal or time out, and we hold 5,000 calls in memory while we wait. With a channel, one producer sends the orders into a rendezvous channel, and 8 helper coroutines loop over it. Each order goes to exactly one helper, so at most 8 calls are in flight, and the producer just waits until a helper is free, which keeps memory flat. The helpers send their tickets into a second channel that one loop reads, and a separate coroutine closes that channel after all the helpers finish, so the loop can end. Because it all runs inside coroutineScope, one failed order cancels the producer and the other helpers, and the exception reaches the caller."
 },
 "deeper": {
  "minutes": 10,
  "body": "`actor { }`, which older tutorials use to guard shared state with a channel of messages, is marked `@ObsoleteCoroutinesApi`: its KDoc says it will become obsolete when \"complex actors\" arrive. A plain coroutine looping over a channel you create does the same job without the warning, and the next lesson calls that confinement. `BroadcastChannel` was deprecated in 1.7, and its deprecation level was raised in 1.9. Use a `SharedFlow` from the last lesson for one-to-many.\n\nThe `BUFFERED` default of 64 comes from the JVM system property `kotlinx.coroutines.channels.defaultBuffer`. It is also the buffer that `flowOn`, `buffer()`, `channelFlow` and `callbackFlow` use unless you pass a size. When you size a pipeline for memory, count those hidden shelves too.\n\nChannels also have `trySend` and `tryReceive`, which never suspend and return a `ChannelResult`. They are for code at the edge that can't suspend, like a listener callback, and `trySendBlocking` is the blocking variant for a plain thread that may wait. kotlinx.coroutines 1.11 added `ReceiveChannel.consumeTo(collection)`, which drains a channel into a collection.\n\nThe prime-sieve pipeline in the official channels guide is a fun read: each prime gets its own filtering coroutine, chained by channels, so the pipeline grows as it runs. It shows how cheap coroutines and channels are. It is a poor model for real programs, where a fixed number of stations with a known number of helpers is far easier to watch and to cancel.\n\nThis lesson is the first look at `callbackFlow` and the backpressure operators. Bridges and tests, in the Kotlin Flow in depth track, comes back to `callbackFlow`, and Buffering explains how `buffer`, `conflate` and `flowOn` merge their hidden channels into one."
 },
 "sources": [
  {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html"},
  {"title": "Select expression (Kotlin docs)", "url": "https://kotlinlang.org/docs/select-expression.html"},
  {"title": "Channel (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/"},
  {"title": "callbackFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html"}
 ]
}
out = ROOT / "content/lessons/co-09.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
