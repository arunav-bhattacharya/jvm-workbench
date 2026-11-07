import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l09"
J = "java/workbench/coroutines/l09"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l09.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


workers = ""
for i, y in enumerate([28, 76, 124, 172]):
    workers += (f'<line class="ln" x1="270" y1="132" x2="318" y2="{y + 18}" marker-end="url(#arr)"/>'
                f'<rect class="box-a" x="320" y="{y}" width="110" height="36" rx="8"/>'
                f'<text class="t" x="375" y="{y + 23}" text-anchor="middle">worker {i + 1}</text>'
                f'<line class="ln" x1="430" y1="{y + 18}" x2="468" y2="132" marker-end="url(#arr)"/>')

FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="A fan-out and fan-in pipeline: produce sends batch ids into a rendezvous channel. '
    'Four worker coroutines receive from it, each id going to exactly one worker. Every worker sends its receipt into a receipts channel, '
    'which one caller loop reads. At most four settle calls run at once.">'
    '<rect class="box" x="15" y="110" width="130" height="44" rx="8"/>'
    '<text class="t t-code" x="80" y="137" text-anchor="middle">produce { }</text>'
    '<text class="t-s t-m" x="80" y="174" text-anchor="middle">sends 12 ids</text>'
    '<line class="ln" x1="145" y1="132" x2="168" y2="132" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="170" y="110" width="100" height="44" rx="8"/>'
    '<text class="t" x="220" y="130" text-anchor="middle">ids</text>'
    '<text class="t-s" x="220" y="147" text-anchor="middle">rendezvous</text>'
    + workers +
    '<rect class="box-b" x="470" y="110" width="100" height="44" rx="8"/>'
    '<text class="t" x="520" y="130" text-anchor="middle">receipts</text>'
    '<text class="t-s" x="520" y="147" text-anchor="middle">fan-in</text>'
    '<line class="ln" x1="570" y1="132" x2="598" y2="132" marker-end="url(#arr)"/>'
    '<rect class="box" x="600" y="110" width="70" height="44" rx="8"/>'
    '<text class="t" x="635" y="137" text-anchor="middle">caller</text>'
    '<text class="t-s t-a" x="375" y="228" text-anchor="middle">at most 4 settle calls at once</text>'
    '<text class="t-s t-m" x="340" y="254" text-anchor="middle">each id is received by exactly one worker; receipts is closed after joinAll</text>'
    '</svg>'
)

CAP_TABLE = (
    "| Capacity | `send` suspends when | Like |\n"
    "|---|---|---|\n"
    "| `Channel.RENDEZVOUS` (0, the default) | no receiver is waiting | `SynchronousQueue` |\n"
    "| `Channel(n)` | n elements are already waiting | `ArrayBlockingQueue(n)` |\n"
    "| `Channel.BUFFERED` | 64 are waiting (a JVM property changes the default) | `ArrayBlockingQueue(64)` |\n"
    "| `Channel.UNLIMITED` | never: memory is the limit | `LinkedBlockingQueue` |\n"
    "| `Channel.CONFLATED` | never: a new element replaces the waiting one | no JDK equivalent |\n"
)

BP_TABLE = (
    "| Pipeline | The collector sees | Time |\n"
    "|---|---|---|\n"
    "| plain | 1, 2, 3 | about 1,200 ms: (100 + 300) x 3 |\n"
    "| `buffer()` | 1, 2, 3 | about 1,000 ms: the producer runs ahead |\n"
    "| `conflate()` | 1, 3 | about 700 ms: a busy collector skips to the latest |\n"
    "| `collectLatest { }` | starts 1, 2 and 3, finishes only 3 | about 600 ms: a new value cancels the old work |\n"
)

L = {
 "id": "co-09",
 "title": "Channels, select and pipelines",
 "minutes": 35,
 "goal": "By the end you can pick a channel capacity, build a fan-out and fan-in worker pipeline with produce, race calls with select, bridge a listener API with callbackFlow, and choose between buffer, conflate and collectLatest.",
 "warmup": {
  "q": "Three worker coroutines each run `for (id in ids) settle(id)` over the same `Channel<String>`, and a producer sends 9 ids into it, then closes it. How many times is each id settled?",
  "options": [
   "Three times: every worker gets every id",
   "Exactly once: each element goes to one receiver",
   "Once, but all 9 go to whichever worker started first",
   "It can't work: only one coroutine may receive from a channel"
  ],
  "answer": 1,
  "why": "A channel is a queue: each element is received by exactly one receiver. Several receivers on one channel is fan-out, and the channel serves waiting receivers fairly, so the ids spread across the three workers. Delivering every value to every subscriber is what a SharedFlow does."
 },
 "sections": [
  {
   "h": "A channel is a queue between coroutines, and its capacity sets the pace",
   "body": "A `Channel<T>` is the coroutine version of a `BlockingQueue`. `send` puts an element in and `receive` takes one out, but where a blocking queue blocks a thread, a channel suspends a coroutine. Each element is received by exactly one receiver, which is the difference from a SharedFlow (lesson 8 of this track), where every subscriber gets every value.\n\n```kotlin\nval ids = Channel<String>(capacity = 64)\nlaunch {\n    for (id in batchIds) ids.send(id)   // suspends while the buffer is full\n    ids.close()                         // no more elements: the receiving loop will end\n}\nfor (id in ids) settle(id)              // receives until the channel is closed and empty\n```\n\n```java\n// Java equivalent: a bounded BlockingQueue, with an end marker because a queue can't be closed\nBlockingQueue<String> ids = new ArrayBlockingQueue<>(64);\nThread.ofVirtual().start(() -> {\n    for (String id : batchIds) putQuietly(ids, id);   // blocks while the queue is full\n    putQuietly(ids, END);\n});\nfor (String id = ids.take(); !id.equals(END); id = ids.take()) settle(id);\n```\n\nThe capacity decides how far a sender can run ahead of the receiver:\n\n" + CAP_TABLE + "\nRendezvous is the default for a good reason: it gives you backpressure for free, because a fast producer simply waits for the consumer. Add a buffer to absorb bursts. Be suspicious of `UNLIMITED`, which turns a slow consumer into an `OutOfMemoryError` some hours later.\n\nClose a channel when you are done sending. `for (x in channel)` ends only when the channel is closed and empty, so a receiver on a channel nobody closes waits forever. The `produce { }` builder takes care of it. It starts a coroutine that sends into a new channel, closes the channel when the block ends or fails, and returns it as a `ReceiveChannel`. It is still marked `@ExperimentalCoroutinesApi`, so it needs an opt-in.\n\nA channel is hot. Elements sit in it whether or not anyone receives, and a coroutine suspended in `send` never finishes until someone does. For a stream with a single consumer, a cold `Flow` is usually the better tool. Channels are for coroutines that hand work to each other.",
   "try": {
    "title": "Five sends, four capacities",
    "minutes": 4,
    "steps": [
     "Read `ChannelCapacities.kt`. The producer sends five ids as fast as it can, and the consumer needs 100 ms per id. Predict when each `send` returns, and what is received, for each capacity.",
     "Run it.",
     "Delete the `channel.close()` line and run it again. Predict first: what happens?",
     "Put the line back and run the Java twin, which uses three `BlockingQueue`s."
    ],
    "code": tryit("ChannelCapacities.kt", "ChannelCapacitiesJava.java"),
    "expect": "Rendezvous: each `send` returns about 100 ms after the previous one, in step with the consumer. Capacity 2: the first three return at once (two buffered, one handed straight to the waiting receiver), then one every 100 ms. Unlimited: all five at once. Conflated: all five at once, but only `[1, 5]` is received, because each new id replaced the waiting one. Without `close()` the program never ends: the `for` loop waits for an id that will never come (stop it with Ctrl+C). The Java twin's three queues match the first three rows."
   },
   "refs": [
    {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html", "kind": "read"}
   ]
  },
  {
   "h": "Fan out to a fixed set of workers, fan in to one channel",
   "body": "Fan-out means several coroutines receive from the same channel. Each element goes to exactly one of them, and channels are fair: receivers waiting in line are served in the order they asked. So one channel plus N worker coroutines is a worker pool with a concurrency limit of N, and no thread pool is involved.\n\n```kotlin\nsuspend fun settleAll(ids: List<String>, workers: Int): Map<String, String> = coroutineScope {\n    val queue = produce { ids.forEach { send(it) } }                // fan-out source\n    val receipts = Channel<Pair<String, String>>()                 // fan-in\n    val pool = List(workers) { launch { for (id in queue) receipts.send(id to settle(id)) } }\n    launch { pool.joinAll(); receipts.close() }                    // close once every worker is done\n    val result = mutableMapOf<String, String>()\n    for ((id, receipt) in receipts) result[id] = receipt\n    result\n}\n```\n\n```java\n// Java equivalent: a fixed pool takes tasks from its queue, a CompletionService collects results\nMap<String, String> settleAll(List<String> ids, int workers) throws Exception {\n    try (ExecutorService pool = Executors.newFixedThreadPool(workers)) {\n        CompletionService<Map.Entry<String, String>> receipts = new ExecutorCompletionService<>(pool);\n        for (String id : ids) receipts.submit(() -> Map.entry(id, settle(id)));\n        Map<String, String> result = new HashMap<>();\n        for (int i = 0; i < ids.size(); i++) { var e = receipts.take().get(); result.put(e.getKey(), e.getValue()); }\n        return result;\n    }\n}\n```\n\nFan-in is the reverse: many senders, one channel, one receiver. The hard part is knowing when to close the fan-in channel. Close it too early and a worker's `send` throws `ClosedSendChannelException`. Never close it and the receiving loop waits forever. A separate coroutine that does `joinAll()` and then `close()` is the usual answer.\n\nEverything sits inside `coroutineScope`, so the pipeline is structured (lesson 3 of this track). If one `settle` throws, the scope cancels the producer, the other workers and the closer, and rethrows. No coroutine is left waiting on a channel.\n\nWhy not `ids.map { async { settle(it) } }.awaitAll()`? Because that starts all 10,000 calls at once, and the acquirer will not thank you. The worker pool caps them at N. A `Semaphore` would cap them too (lesson 10 of this track), but a pool of workers also gives each worker a natural home for its own state, such as one connection per worker. And it composes into multi-stage pipelines, with a channel between each stage: parse, then enrich, then post, each stage with as many workers as it needs.",
   "figure": {"svg": FIG, "caption": "One channel feeds four workers, so at most four calls run at once; a second channel brings their results back to one place."},
   "try": {
    "title": "Spread 20 refunds over a pool",
    "minutes": 3,
    "steps": [
     "Read `FanOutFanIn.kt`. Twenty refunds take 50 to 150 ms each. Predict the total time with 4 workers, and how the refunds spread across them.",
     "Run it, then run it with `-Pargs=1` and `-Pargs=10`.",
     "Run the Java twin, a fixed pool with an `ExecutorCompletionService`."
    ],
    "code": tryit("FanOutFanIn.kt", "FanOutFanInJava.java", " -Pargs=1"),
    "expect": "With 4 workers each one handles about 5 refunds, and the run takes roughly 20 x 100 ms / 4, about 500 to 700 ms. With 1 worker it takes about 2 s. With 10 workers it takes a few hundred ms, and each worker handles about 2. The Java twin spreads the work across its four pool threads the same way."
   }
  },
  {
   "h": "Use select to wait for whichever happens first",
   "body": "`select { }` suspends until the first of several clauses can complete, runs that clause, and drops the rest. The clauses are things you can wait on: `deferred.onAwait`, `channel.onReceive`, `channel.onSend(value)` and `onTimeout(ms)`.\n\nThe classic payments use is hedging: ask two acquirers for a quote and take whichever answers first.\n\n```kotlin\nval quote = coroutineScope {\n    val north = async { northAcquirer.quote(req) }\n    val east = async { eastAcquirer.quote(req) }\n    val first = select {\n        north.onAwait { it }\n        east.onAwait { it }\n        onTimeout(500) { defaultQuote }      // needs @OptIn(ExperimentalCoroutinesApi::class)\n    }\n    north.cancel(); east.cancel()            // stop the losers\n    first\n}\n```\n\n```java\n// Java equivalent: anyOf completes with the first future, completeOnTimeout adds a fallback\nObject first = CompletableFuture.anyOf(north, east)\n    .completeOnTimeout(defaultQuote, 500, TimeUnit.MILLISECONDS)\n    .join();\nnorth.cancel(true); east.cancel(true);       // marks the futures; the HTTP calls may run on\nQuote quote = (Quote) first;\n```\n\nThree details matter. `select` is biased: if several clauses are ready at the same moment, the first one listed wins, so list the source you prefer first. Stopping the losers is your job, just as with `anyOf`, but with coroutines the cancel actually reaches the losing calls at their next suspension point instead of only marking a future as cancelled. And the API status is mixed: in 1.11 the `select` builder compiles without an opt-in, while the guide still calls select expressions experimental and `onTimeout` needs `@OptIn(ExperimentalCoroutinesApi::class)`.\n\nWithout the timeout clause, this is also what the lab's `fastestQuote` does, generalized to a list: `select { calls.forEach { c -> c.onAwait { it } } }`.\n\n`select` over the `onReceive` clauses of several channels can merge streams by hand. For most merging, Flow operators such as `merge` and `combine` are simpler and harder to get wrong. Keep `select` for \"the first of these, then stop\", and for the rare loop that must react to whichever of several channels has something.",
   "try": {
    "title": "Hedge a quote across two acquirers",
    "minutes": 3,
    "steps": [
     "Read `SelectFirst.kt`. North answers in 300 ms, east in 120 ms, and the budget is 500 ms. Predict the answer and the time.",
     "Run it.",
     "Run it with `-Pargs=100`, a 100 ms budget. Predict first.",
     "Run the Java twin both ways."
    ],
    "code": tryit("SelectFirst.kt", "SelectFirstJava.java", " -Pargs=100", " -Pargs=100"),
    "expect": "With 500 ms the answer is `east: 2.10%` after about 120 ms (a little more on a cold JVM), and north is cancelled. With 100 ms the timeout clause wins: `no quote within 100 ms` after about 100 ms. The Java twin gives the same answers with `anyOf` and `completeOnTimeout`."
   },
   "refs": [
    {"title": "Select expression (Kotlin docs)", "url": "https://kotlinlang.org/docs/select-expression.html", "kind": "read"}
   ]
  },
  {
   "h": "Channels inside flows: callbackFlow, channelFlow and the backpressure operators",
   "body": "A flow is sequential, so `emit` may only be called from the flow's own coroutine (lesson 7 of this track). When values come from somewhere else, such as a listener API or several coroutines at once, `callbackFlow` and `channelFlow` put a channel inside the flow. Producers `send` or `trySend` into it, and the collector receives from it.\n\n`callbackFlow` is the bridge for listener APIs that call you many times:\n\n```kotlin\nfun PaymentEventBus.events(): Flow<PaymentEvent> = callbackFlow {\n    val registration = register { event -> trySend(event) }   // called on the bus's thread\n    awaitClose { registration.unregister() }                   // runs when the collector stops\n}\n```\n\n```java\n// Java equivalent: Flux.create with a sink, and onDispose for the cleanup\nFlux<PaymentEvent> events(PaymentEventBus bus) {\n    return Flux.create(sink -> {\n        Registration registration = bus.register(sink::next);\n        sink.onDispose(registration::unregister);\n    });\n}\n```\n\n`awaitClose` is not optional. It suspends until the collector goes away, then runs the cleanup. Without it the block returns right after registering, and `callbackFlow` throws `IllegalStateException` to stop you leaking the listener. From the callback, use `trySend`: it never blocks the caller's thread, and it fails if the buffer (64 by default) is full. For a callback that fires once, `suspendCancellableCoroutine` from lesson 1 of this track is the right tool. `channelFlow` is the same idea for your own coroutines: `launch` several producers inside it, and each one can `send` safely.\n\nThe other place channels hide is the **backpressure operators**. Take the guide's numbers: a producer that needs 100 ms per item, a collector that needs 300 ms, three items.\n\n" + BP_TABLE + "\n`buffer` keeps everything and lets the producer run ahead into a channel. `conflate` keeps only the latest value, which suits prices and never suits payments. `collectLatest` cancels and restarts the collector's block for each new value, which suits \"recompute the quote whenever the input changes\". It is wrong for anything with side effects you can't take back, because the cancelled run may have done half its work.\n\nAll three trade memory, completeness and freshness against each other, and the plain flow is the safe default. Reactor's `onBackpressureBuffer`, `onBackpressureLatest` and `switchMap` (lesson 7 of the reactive track) make the same three trades.",
   "try": {
    "title": "Time four backpressure choices",
    "minutes": 4,
    "steps": [
     "Read `FlowBackpressure.kt`. Predict what each of the four lines prints, and roughly how long it takes.",
     "Run it.",
     "In the `conflate()` line, change the collector's `delay(300)` to `delay(50)`. Predict first: does it still skip a value?",
     "Run the Java twin with the Reactor counterparts."
    ],
    "code": tryit("FlowBackpressure.kt", "FlowBackpressureJava.java"),
    "expect": "Plain: `1 2 3` in about 1,200 ms. `buffer()`: `1 2 3` in about 1,000 ms. `conflate()`: `1 3` in about 700 ms. `collectLatest`: `start 1, start 2, start 3, done 3` in about 600 ms. With a 50 ms collector, `conflate()` prints `1 2 3`: it only skips values that arrive while the collector is busy, and now it never is. The Java twin prints the same values in about the same times with `concatMap`, `onBackpressureBuffer`, `onBackpressureLatest` and `switchMap`."
   },
   "refs": [
    {"title": "callbackFlow (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html", "kind": "docs"},
    {"title": "conflate (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/conflate.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A channel is the hatch between a restaurant's kitchen and its dining room. With a rendezvous hatch there is no shelf: the cook holds the plate until a waiter takes it. A buffered hatch has a shelf with a fixed number of spots, and the cook waits only when the shelf is full. Fan-out is several waiters taking plates from the same hatch, each plate going to exactly one of them. Fan-in is several cooks passing plates through one hatch to one waiter. `select` is ringing two suppliers and going with whoever picks up first, then hanging up on the other. The analogy breaks at closing time: in a real kitchen the staff see the lights go off. A channel's receivers only learn that nothing more is coming when someone calls `close()`, and if nobody does, they wait at the hatch forever.",
 "in_your_world": "A worker pool over a channel is a good fit for settlement and refund batches: size the pool to what the acquirer allows (say, 8 concurrent calls), and the channel keeps everything else waiting without holding a thread. Rendezvous or small buffers keep memory flat when the acquirer slows down. `select` with `onAwait` and `onTimeout` is the shape of a hedged authorization or a fallback acquirer: take the first answer within 800 ms, otherwise route elsewhere, and cancel what you no longer need. `callbackFlow` is how a legacy listener API, such as a fraud engine's event callbacks or a JMS listener, becomes a Flow with clean unregistering. For a Kafka consumer, keep offset commits in order: a fan-out pool processes records out of order, so commit only what every worker has finished, or keep one worker per partition.",
 "mistake": "The most common mistake is a channel that nobody closes, or a `callbackFlow` without `awaitClose`. In the first case the receiving `for` loop never ends, so the `coroutineScope` around it never returns, and the request hangs with no error and no CPU use. In the second, `callbackFlow` throws `IllegalStateException` the first time it is collected, and the fix people reach for, an `awaitCancellation()` or a `delay(Long.MAX_VALUE)`, keeps the flow open but never unregisters the listener. Use `produce { }`, which closes its channel when the block ends; close fan-in channels after `joinAll()`; and end every `callbackFlow` with `awaitClose { unregister() }`.",
 "compare": {
  "title": "A capped worker pool: ExecutorService vs channel and coroutines",
  "java": {"title": "RefundRunner.java", "src": "List<String> refundAll(List<String> ids) throws Exception {\n    try (ExecutorService pool = Executors.newFixedThreadPool(8)) {     // 1. 8 threads = at most 8 calls\n        CompletionService<String> done = new ExecutorCompletionService<>(pool);\n        for (String id : ids) done.submit(() -> issuer.refund(id));     // 2. every task queued up front\n        List<String> receipts = new ArrayList<>();\n        for (int i = 0; i < ids.size(); i++) receipts.add(done.take().get());   // 3. fan-in, in finish order\n        return receipts;\n    }   // a failure surfaces at get(); the other tasks keep running until close() waits for them\n}"},
  "kotlin": {"title": "RefundRunner.kt", "src": "suspend fun refundAll(ids: List<String>): List<String> = coroutineScope {\n    val queue = produce { ids.forEach { send(it) } }                  // 2. ids handed out one at a time\n    val receipts = Channel<String>()\n    val pool = List(8) { launch { for (id in queue) receipts.send(issuer.refund(id)) } }   // 1. 8 workers\n    launch { pool.joinAll(); receipts.close() }\n    val result = mutableListOf<String>()\n    for (r in receipts) result += r                                    // 3. fan-in, in finish order\n    result\n}   // a failure cancels the producer and every worker, then rethrows"},
  "note": "Both cap the issuer at 8 concurrent refunds and collect results in the order they finish. The Java version spends 8 threads, which sit blocked while the issuer thinks, and it queues every task up front. The Kotlin version spends 8 coroutines, which suspend while waiting, and the rendezvous channel hands out ids only as workers free up, so a list of a million ids never sits in a task queue. The bigger difference is failure. In Java one failed refund shows up at `get()`, and the other tasks keep running until `close()` waits for them. In Kotlin the whole pipeline is one `coroutineScope`, so the first failure cancels the producer and every worker before the exception reaches the caller."
 },
 "worked": {
  "title": "A three-stage settlement pipeline",
  "steps": [
   {"say": "An acquirer's settlement file has 200,000 lines. Each line must be parsed, enriched with a BIN lookup (a blocking legacy client, 20 ms per call), and posted to the ledger in batches of 500. Doing it in one loop takes over an hour, almost all of it in BIN lookups.",
    "code": "suspend fun importFile(reader: LineReader) {\n    val batch = mutableListOf<Posting>()\n    while (true) {\n        val line = reader.readLine() ?: break\n        val rec = parse(line)\n        val bin = withContext(Dispatchers.IO) { binClient.lookup(rec.cardBin) }   // 20 ms, one at a time\n        batch += Posting(rec, bin)\n        if (batch.size == 500) { ledger.post(batch.toList()); batch.clear() }\n    }\n    if (batch.isNotEmpty()) ledger.post(batch)\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same single loop\nvoid importFile(LineReader reader) {\n    List<Posting> batch = new ArrayList<>();\n    for (String line = reader.readLine(); line != null; line = reader.readLine()) {\n        Record rec = parse(line);\n        BinInfo bin = binClient.lookup(rec.cardBin());     // 20 ms, one at a time\n        batch.add(new Posting(rec, bin));\n        if (batch.size() == 500) { ledger.post(List.copyOf(batch)); batch.clear(); }\n    }\n    if (!batch.isEmpty()) ledger.post(batch);\n}", "alt_lang": "java"},
   {"say": "Stage 1 reads and parses on IO, into a small buffer. `produce` closes the channel when the file ends.",
    "code": "@OptIn(ExperimentalCoroutinesApi::class)\nsuspend fun importFile(reader: LineReader) = coroutineScope {\n    // 1. parse: one reader, a little ahead of the enrichers\n    val records = produce(Dispatchers.IO, capacity = 100) {\n        while (true) send(parse(reader.readLine() ?: break))\n    }", "lang": "kotlin",
    "alt_code": "void importFile(LineReader reader) throws Exception {\n    // 1. parse: one reader thread, a little ahead of the enrichers\n    BlockingQueue<Record> records = new ArrayBlockingQueue<>(100);\n    Thread parser = Thread.ofPlatform().start(() -> {\n        for (String line = reader.readLine(); line != null; line = reader.readLine()) putQuietly(records, parse(line));\n        putQuietly(records, Record.END);\n    });", "alt_lang": "java"},
   {"say": "Stage 2 fans out to 16 enrichers, the BIN service's limit. They fan in to one channel, closed when all 16 are done.",
    "code": "    // 2. enrich: 16 workers on IO, because the BIN client blocks\n    val postings = Channel<Posting>(capacity = 1_000)\n    val enrichers = List(16) {\n        launch(Dispatchers.IO) { for (rec in records) postings.send(Posting(rec, binClient.lookup(rec.cardBin))) }\n    }\n    launch { enrichers.joinAll(); postings.close() }", "lang": "kotlin",
    "alt_code": "    // 2. enrich: 16 threads, because the BIN client blocks\n    BlockingQueue<Posting> postings = new ArrayBlockingQueue<>(1_000);\n    ExecutorService enrichers = Executors.newFixedThreadPool(16);\n    for (int i = 0; i < 16; i++) enrichers.submit(() -> {\n        for (Record rec = records.take(); rec != Record.END; rec = records.take())\n            postings.put(new Posting(rec, binClient.lookup(rec.cardBin())));\n        records.put(Record.END);   // pass the end marker on to the next enricher\n        return null;\n    });", "alt_lang": "java"},
   {"say": "Stage 3 is a single writer, so ledger batches stay simple. When `postings` is closed and drained, the loop ends, and `coroutineScope` returns once every stage has finished. If any stage throws, the scope cancels the others.",
    "code": "    // 3. post: one writer, batches of 500\n    val batch = mutableListOf<Posting>()\n    for (p in postings) {\n        batch += p\n        if (batch.size == 500) { ledger.post(batch.toList()); batch.clear() }\n    }\n    if (batch.isNotEmpty()) ledger.post(batch)\n}", "lang": "kotlin",
    "alt_code": "    // 3. post: one writer, batches of 500 (the end of stage 2 needs its own marker or a latch)\n    enrichers.shutdown();\n    List<Posting> batch = new ArrayList<>();\n    while (!(enrichers.isTerminated() && postings.isEmpty())) {\n        Posting p = postings.poll(100, TimeUnit.MILLISECONDS);\n        if (p == null) continue;\n        batch.add(p);\n        if (batch.size() == 500) { ledger.post(List.copyOf(batch)); batch.clear(); }\n    }\n    if (!batch.isEmpty()) ledger.post(batch);\n    parser.join();\n}", "alt_lang": "java"},
   {"say": "Self-check: the ledger slows to a crawl. Trace what happens to memory and to the BIN service. (The writer falls behind, `postings` fills up to 1,000, the enrichers suspend in `send`, `records` fills up to 100, and the parser suspends too. Memory stays flat, and the BIN service sees fewer calls. Backpressure flows all the way back to the file read.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A worker pool, an event bridge and a hedged quote",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/PipelineModel.kt", f"{lab}/main/{P}/ParallelSettlement.kt", f"{lab}/main/{P}/EventBusFlow.kt", f"{lab}/main/{P}/FastestQuote.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l09.*'",
  "steps": [
   "Run the tests. Five of seven fail. `PipelineModel.kt` has the bus, its `Registration` and `Quote`.",
   "In `ParallelSettlement.kt`, build the pool inside `coroutineScope`: `produce` the ids, start `workers` coroutines that loop over the ids channel and send `id to settle(id)` into a receipts channel, close receipts after `joinAll()`, and read it into a map.",
   "In `EventBusFlow.kt`, keep the `Registration` that `register` returns, and end the block with `awaitClose { registration.unregister() }`.",
   "In `FastestQuote.kt`, start every call with `async`, `select` on their `onAwait` clauses, cancel all the calls, and return the winner.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "`produce` needs `@OptIn(ExperimentalCoroutinesApi::class)` on the function. It closes its channel when its block ends.",
   "Close the receipts channel from its own coroutine: `launch { pool.joinAll(); receipts.close() }`. If you close it after the receiving loop, the loop never ends.",
   "`awaitClose` comes from `kotlinx.coroutines.channels`. It suspends until the collector stops, so it must be the last line of the `callbackFlow` block.",
   "`select { calls.forEach { c -> c.onAwait { it } } }` is a whole `select`: the lambda registers one clause per call. Cancelling a call that already finished does nothing, so you can cancel them all."
  ],
  "done_when": "All seven tests in `ChannelsTest` pass."
 },
 "drill": {
  "title": "A capped worker pool from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `suspend fun refundAll(ids: List<String>)` that calls the suspend function `refund(id)` for every id, with at most 3 calls running at once, using a channel and 3 worker coroutines. It returns when every refund is done, and a failure in any refund cancels the rest.",
  "answer": {"lang": "kotlin", "src": "@OptIn(ExperimentalCoroutinesApi::class)\nsuspend fun refundAll(ids: List<String>) = coroutineScope {\n    val queue = produce { for (id in ids) send(id) }   // closed when the block ends\n    repeat(3) {\n        launch { for (id in queue) refund(id) }        // each id goes to one worker\n    }\n}   // coroutineScope waits for the producer and all three workers",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a pool of 3 threads, and invokeAll to wait for every task\nvoid refundAll(List<String> ids) throws Exception {\n    try (ExecutorService pool = Executors.newFixedThreadPool(3)) {\n        List<Callable<Void>> tasks = ids.stream()\n            .<Callable<Void>>map(id -> () -> { refund(id); return null; })\n            .toList();\n        for (Future<Void> f : pool.invokeAll(tasks)) f.get();   // rethrows the first failure\n    }   // unlike coroutineScope, the other refunds are not cancelled on a failure\n}"}}
 },
 "recap": [
  "A `Channel` hands each element to exactly one receiver. `send` and `receive` suspend instead of blocking.",
  "Capacity sets the pace: rendezvous (the default) hands over directly, `Channel(n)` buffers n, `UNLIMITED` never suspends (and can run out of memory), `CONFLATED` keeps only the newest.",
  "Close a channel when sending is done, or `for (x in channel)` never ends. `produce { }` closes its channel for you.",
  "Fan-out (several workers on one channel) caps concurrency at the number of workers. Fan-in channels close after `joinAll()`. Inside `coroutineScope`, one failure cancels the whole pipeline.",
  "`select` takes whichever clause completes first (`onAwait`, `onReceive`, `onTimeout`). It is biased to the first clause, and stopping the losers is your job.",
  "`callbackFlow` bridges listener APIs and must end with `awaitClose { unregister() }`. `buffer`, `conflate` and `collectLatest` trade completeness for speed or freshness."
 ],
 "quiz": [
  {"q": "`val ch = Channel<String>()`. A coroutine runs `ch.send(\"batch-1\"); println(\"sent\")`, and nothing ever receives from `ch`. What happens?",
   "options": ["`sent` prints at once, because `send` puts the element in a buffer", "`send` suspends forever, so `sent` never prints", "`send` throws `IllegalStateException` because nobody is receiving", "The element is dropped and `sent` prints"],
   "answer": 1,
   "why": "The default capacity is rendezvous: `send` waits until a receiver takes the element. With no receiver it waits forever, and the coroutine never finishes. A buffered channel would accept it at once."},
  {"q": "Four workers each run `for (id in ids) settle(id)` on the same channel. The producer sends 40 ids and closes it. Which statement is true?",
   "options": ["Each id is settled exactly once, and at most 4 settle calls run at the same time", "Each id is settled four times, once per worker", "All 40 go to the first worker, because it started first", "The workers deadlock, because they compete for the same channel"],
   "answer": 0,
   "why": "A channel is a queue: each element goes to one receiver, and fair receiving spreads the ids across the waiting workers. Four workers means at most four calls in flight. That is fan-out."},
  {"q": "What happens when this flow is collected?\n\n```kotlin\ncallbackFlow {\n    bus.register { trySend(it) }\n}\n```",
   "options": ["Events flow normally until the collector cancels", "Nothing is ever emitted, but the collector waits forever", "`callbackFlow` throws `IllegalStateException`, because the block returned without `awaitClose`", "The listener is unregistered automatically when the block returns"],
   "answer": 2,
   "why": "`callbackFlow` requires the block to suspend in `awaitClose { }` until the collector stops. If the block returns while the channel is still open, it throws `IllegalStateException`, and the listener it registered is never unregistered."},
  {"q": "A pricing service recomputes a merchant's FX quote every time the amount in the checkout changes. A recompute takes 300 ms, and amounts change every 100 ms while the customer types. Only the latest quote matters, and a stale computation should stop. Which operator fits?",
   "options": ["`buffer()`", "`conflate()`", "`Channel.UNLIMITED` between input and pricing", "`collectLatest { }`"],
   "answer": 3,
   "why": "`collectLatest` cancels the computation in progress when a new amount arrives, so only the latest is computed to the end. `conflate` skips values that arrive while busy but still finishes every computation it starts. `buffer` and an unlimited channel compute every stale amount."},
  {"q": "From the reactive track: which Kotlin Flow operator behaves most like Reactor's `onBackpressureLatest()`?",
   "options": ["`buffer()`", "`conflate()`", "`collectLatest { }`", "`flowOn(Dispatchers.IO)`"],
   "answer": 1,
   "why": "Both keep only the newest value while the consumer is busy and hand it over when the consumer is ready. `collectLatest` is closer to `switchMap`, because it cancels the work in progress. `buffer` is `onBackpressureBuffer`.",
   "from": "rx-07"}
 ],
 "flashcards": [
  {"front": "What is the default capacity of `Channel<T>()`, and what does it mean for `send`?", "back": "`RENDEZVOUS` (0): `send` suspends until a receiver takes the element."},
  {"front": "What does a `Channel.CONFLATED` channel do with a new element when one is already waiting?", "back": "It replaces the waiting one. `send` never suspends, and a slow receiver gets only the newest."},
  {"front": "Several coroutines receive from one channel. How many of them get each element?", "back": "Exactly one. That is fan-out, and it caps concurrency at the number of receivers."},
  {"front": "When does `for (x in channel)` stop?", "back": "When the channel has been closed and every element in it has been received."},
  {"front": "Why must a `callbackFlow` block end with `awaitClose { ... }`?", "back": "It keeps the flow open until the collector stops, then runs the cleanup. Without it, `callbackFlow` throws `IllegalStateException` and the listener leaks."},
  {"front": "Two `select` clauses are ready at the same moment. Which one wins?", "back": "The one listed first: `select` is biased toward the first clause."},
  {"front": "`conflate()` vs `collectLatest { }` for a slow collector?", "back": "`conflate` skips values that arrived while busy but finishes each one it starts. `collectLatest` cancels the block in progress when a new value arrives."}
 ],
 "terms": [
  {"term": "Channel", "plain": "A queue between coroutines: each element is received once, and send and receive suspend instead of blocking."},
  {"term": "Rendezvous", "plain": "A channel with no buffer: the sender waits until a receiver takes the element."},
  {"term": "Fan-out", "plain": "Several receivers on one channel, so each element is handled by exactly one of them."},
  {"term": "Fan-in", "plain": "Several senders into one channel, read by one receiver."},
  {"term": "produce", "plain": "A builder that starts a coroutine sending into a new channel and closes it when the block ends."},
  {"term": "select", "plain": "Waits for whichever of several clauses can complete first, and runs only that one."},
  {"term": "callbackFlow", "plain": "A flow builder with a channel inside, for turning listener callbacks into a Flow."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to settle 50,000 batches with `batchIds.map { async { settle(it) } }.awaitAll()`, and the acquirer allows 8 concurrent calls. Explain the problem and how a channel-based worker pool fixes it.",
  "answer": "That code starts 50,000 coroutines at once, so the acquirer sees 50,000 concurrent calls, far more than its limit of 8. We'd get rate-limited or time out, and we'd hold 50,000 pending requests in memory. With a channel, one producer sends the ids into a rendezvous channel and 8 worker coroutines loop over it. Each id goes to exactly one worker, so at most 8 settle calls are in flight, and the producer just waits until a worker is free, which keeps memory flat. The workers send their receipts into a second channel that one loop reads, and a separate coroutine closes it after all the workers finish so that loop can end. Because it all runs inside coroutineScope, one failed settle cancels the producer and the other workers and the exception reaches the caller."
 },
 "deeper": {
  "minutes": 10,
  "body": "`actor { }`, which older tutorials use to protect shared state with a channel of messages, is marked `@ObsoleteCoroutinesApi`: the KDoc says it will become obsolete when \"complex actors\" arrive. A plain coroutine looping over a channel you create does the same job without the warning. `BroadcastChannel` was deprecated in 1.7, and its deprecation level was raised in 1.9. Use `SharedFlow` (lesson 8 of this track) for one-to-many.\n\nThe `BUFFERED` default of 64 comes from the JVM system property `kotlinx.coroutines.channels.defaultBuffer`. It is also the buffer `flowOn`, `buffer()`, `channelFlow` and `callbackFlow` use unless you pass a size. When you size a pipeline for memory, count those hidden buffers too.\n\nChannels also have `trySend` and `tryReceive`, which never suspend and return a `ChannelResult`. They are for code at the edge that can't suspend, like a listener callback, and `trySendBlocking` is the blocking variant for a plain thread that may wait. Since kotlinx.coroutines 1.11, `ReceiveChannel.consumeTo(collection)` drains a channel into a collection.\n\nThe prime-sieve pipeline in the official channels guide is a fun read: each prime gets its own filtering coroutine, chained by channels, so the pipeline grows as it runs. It is a good picture of how cheap coroutines and channels are, and a poor model for production code, where a fixed number of stages with a known number of workers is far easier to monitor and to cancel."
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
