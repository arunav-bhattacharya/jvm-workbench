import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l07"
J = "java/workbench/coroutines/l07"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l07.{cls}{extra}"


def tryit(kt, java, extra_kt="", extra_java=""):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt", extra_kt), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j, extra_java), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 680 240" role="img" aria-label="A flow pipeline from left to right: flow builder, map, onCompletion, catch, collect. '
    'Errors from the builder, map and onCompletion are upstream of catch, so catch can handle them. Errors thrown in collect are downstream '
    'and pass through to the caller. onCompletion sees every ending.">'
    '<text class="t-s t-m" x="15" y="30">values flow this way</text>'
    '<line class="ln-d" x1="150" y1="26" x2="665" y2="26" marker-end="url(#arr)"/>'
    '<rect class="box" x="15" y="70" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="70" y="95" text-anchor="middle">flow { }</text>'
    '<line class="ln" x1="125" y1="90" x2="143" y2="90" marker-end="url(#arr)"/>'
    '<rect class="box" x="145" y="70" width="100" height="40" rx="8"/>'
    '<text class="t t-code" x="195" y="95" text-anchor="middle">map</text>'
    '<line class="ln" x1="245" y1="90" x2="263" y2="90" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="265" y="70" width="130" height="40" rx="8"/>'
    '<text class="t t-code" x="330" y="95" text-anchor="middle">onCompletion</text>'
    '<line class="ln" x1="395" y1="90" x2="413" y2="90" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="415" y="70" width="100" height="40" rx="8"/>'
    '<text class="t t-code" x="465" y="95" text-anchor="middle">catch</text>'
    '<line class="ln" x1="515" y1="90" x2="533" y2="90" marker-end="url(#arr)"/>'
    '<rect class="box" x="535" y="70" width="130" height="40" rx="8"/>'
    '<text class="t t-code" x="600" y="95" text-anchor="middle">collect { }</text>'
    '<line class="ln-a" x1="15" y1="134" x2="395" y2="134"/>'
    '<text class="t-s t-a" x="205" y="154" text-anchor="middle">upstream errors: catch can emit a fallback</text>'
    '<line class="ln-bad" x1="535" y1="134" x2="665" y2="134"/>'
    '<text class="t-s t-bad" x="600" y="154" text-anchor="middle">collector errors</text>'
    '<text class="t-s t-bad" x="600" y="170" text-anchor="middle">pass through catch</text>'
    '<text class="t-s t-b" x="330" y="200" text-anchor="middle">onCompletion sees every ending:</text>'
    '<text class="t-s t-m" x="330" y="218" text-anchor="middle">null, an error from either side, or a cancel</text>'
    '</svg>'
)

L = {
 "id": "co-07",
 "title": "Flow basics: cold streams and operators",
 "minutes": 35,
 "goal": "By the end you can build a cold Flow with flow { }, tell intermediate operators from terminal ones, move blocking upstream work with flowOn, and handle errors with catch and onCompletion without breaking exception transparency.",
 "warmup": {
  "q": "`fun entries(): Flow<LedgerEntry> = flow { println(\"fetching\"); emit(api.firstPage()) }`. You call `val f = entries()` and then `f.collect { }` twice. How many times does `fetching` print?",
  "options": [
   "Once, when `entries()` is called",
   "Once, at the first `collect`; the second one reuses the values",
   "Twice: the body runs again for every collector",
   "Never: `println` inside a flow builder is ignored"
  ],
  "answer": 2,
  "why": "A `flow { }` is cold. Calling `entries()` only builds a description of the work, and the body runs from the top each time someone collects it. Nothing is cached between collectors, which is also why a retry can simply collect again."
 },
 "sections": [
  {
   "h": "A flow is a recipe that runs once per collector",
   "body": "A `Flow<T>` is a stream of values that you receive one at a time through a suspend call. The usual way to make one is the `flow { }` builder, where you call `emit` once per value:\n\n```kotlin\nfun ledgerEntries(api: LedgerApi, accountId: String): Flow<LedgerEntry> = flow {\n    var cursor: String? = null\n    do {\n        val page = api.page(accountId, cursor)   // a suspend call to the ledger service\n        page.entries.forEach { emit(it) }\n        cursor = page.nextCursor\n    } while (cursor != null)\n}\n```\n\n```java\n// Java equivalent: a cold Flux that asks for the next page once the previous one is in\nFlux<LedgerEntry> ledgerEntries(LedgerApi api, String accountId) {\n    return api.page(accountId, null)                                      // Mono<LedgerPage>\n        .expand(p -> p.nextCursor() == null ? Mono.empty() : api.page(accountId, p.nextCursor()))\n        .flatMapIterable(LedgerPage::entries);\n}\n```\n\nCalling `ledgerEntries(...)` runs nothing. It returns a description of the work, like a recipe. The body runs when someone calls a terminal operator such as `collect`, and it runs again from the top for every collector. That is a **cold** flow. A Reactor `Flux` is cold in the same way (lesson 2 of the reactive track): nothing happens until you subscribe.\n\nTwo properties follow from the design. A flow is sequential: `emit` is a suspend call that returns only when the collector has finished with the value, so the producer never runs ahead of the consumer. That is Flow's backpressure, and there is no `request(n)` in sight. And a collector that stops early stops the producer. `take(3)` cancels the flow after the third value, so the `flow { }` body never asks for a page it doesn't need.\n\nThe other builders are shortcuts. `flowOf(a, b, c)` emits fixed values, and `list.asFlow()` or `(1..n).asFlow()` turn collections and ranges into flows. Remember from lesson 5 of this track that `asFlow()` doesn't check for cancellation between items, so add `.cancellable()` when a long one has to stop on time. `channelFlow` and `callbackFlow` are for producers that aren't plain sequential code, and lesson 9 of this track covers them.\n\nA flow returned from a function is almost always cold. The exceptions are the hot flows, `StateFlow` and `SharedFlow`, which keep running whether or not anyone collects. They are lesson 8 of this track.",
   "try": {
    "title": "Collect a cold flow three times",
    "minutes": 3,
    "steps": [
     "Read `ColdFlow.kt`. Predict every `fetching page` line, including the ones for `take(3)`.",
     "Run it.",
     "Change `take(3)` to `take(2)` and run it again. Predict first: how many pages now?",
     "Run the Java twin, a Flux built the same way."
    ],
    "code": tryit("ColdFlow.kt", "ColdFlowJava.java"),
    "expect": "Building prints nothing. Each full collection fetches pages 0, 1 and 2 again. `take(3)` fetches pages 0 and 1, because the third entry is on page 1, and the flow is cancelled before page 2. With `take(2)` only page 0 is fetched. The Java twin prints the same lines, because a Flux is cold too."
   },
   "refs": [
    {"title": "Asynchronous Flow (Kotlin docs)", "url": "https://kotlinlang.org/docs/flow.html", "kind": "read"}
   ]
  },
  {
   "h": "Intermediate operators build the pipeline, terminal operators run it",
   "body": "Operators come in two kinds. **Intermediate** operators such as `map`, `filter`, `onEach`, `take` and `transform` take a flow and return a new flow. They are plain functions, they return at once, and they run nothing. **Terminal** operators such as `collect`, `toList`, `first`, `single`, `fold` and `count` are suspend functions. They start the flow, consume it, and return when it ends.\n\n```kotlin\nval receipts: Flow<String> = ledgerEntries(api, \"acc-1\")    // nothing runs yet\n    .filter { it.amountCents > 0 }\n    .map { \"EUR %.2f\".format(it.amountCents / 100.0) }\nval firstTen = receipts.take(10).toList()                   // now it runs\n```\n\n```java\n// Java equivalent: Reactor operators also only build; block() (or subscribe) runs them\nFlux<String> receipts = ledgerEntries(api, \"acc-1\")\n    .filter(e -> e.amountCents() > 0)\n    .map(e -> String.format(\"EUR %.2f\", e.amountCents() / 100.0));\nList<String> firstTen = receipts.take(10).collectList().block();\n```\n\nBy default all of it runs in one coroutine, one value at a time. The first entry travels through `filter`, through `map` and into the collector before the flow body produces the second. There are no queues between the stages and no extra threads. The few operators that add concurrency on purpose, such as `buffer`, `flowOn` and `flatMapMerge`, say so in their docs.\n\nA reusable operator is just an extension function, and it reads like a built-in:\n\n```kotlin\nfun Flow<LedgerEntry>.settledOnly(): Flow<LedgerEntry> = filter { it.status == Status.SETTLED }\n\nval settled = ledgerEntries(api, \"acc-1\").settledOnly()\n```\n\n```java\n// Java equivalent: a function from Flux to Flux, applied with transform\nstatic Flux<LedgerEntry> settledOnly(Flux<LedgerEntry> entries) {\n    return entries.filter(e -> e.status() == Status.SETTLED);\n}\n\nFlux<LedgerEntry> settled = ledgerEntries(api, \"acc-1\").transform(Ledger::settledOnly);\n```\n\n`transform { value -> ... }` is the general form: it can emit zero, one or many values for each input.\n\nWatch for a terminal operator hiding in a function that ought to return a flow. `suspend fun receipts(): List<String> = pipeline.toList()` runs the whole export at the call and holds every line in memory. `fun receipts(): Flow<String>` leaves the caller free to stream, take the first ten, or stop on an error.",
   "try": {
    "title": "Watch one value at a time",
    "minutes": 3,
    "steps": [
     "Read `OperatorOrder.kt`. Predict the order of the `emit`, `filter`, `map` and `collect` lines.",
     "Run it.",
     "Add `.take(1)` just before `.collect`. Predict how many `emit` lines print now.",
     "Run the Java twin."
    ],
    "code": tryit("OperatorOrder.kt", "OperatorOrderJava.java"),
    "expect": "The `pipeline built` line comes first. Then each amount goes all the way through before the next one is emitted: `emit 4250`, `filter passed`, `map`, `collect`, then `emit -990`, which stops at the filter, then the third amount. With `take(1)` only one `emit` prints: once the collector has its value, the flow is cancelled. The synchronous Flux in the Java twin prints the same order."
   },
   "refs": [
    {"title": "Flow (API reference: operators, context, exceptions)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/", "kind": "docs"}
   ]
  },
  {
   "h": "Move the upstream with flowOn, not with withContext around emit",
   "body": "A flow runs in the context of the coroutine that collects it. The docs call this **context preservation**, and it means the code that collects never has to wonder which thread its lambda runs on. It also rules out the obvious way to move a blocking source, such as the acquirer's settlement file read through a legacy blocking reader, to IO:\n\n```kotlin\n// wrong: emit from another context throws IllegalStateException (\"Flow invariant is violated\")\nflow { withContext(Dispatchers.IO) { emit(parse(reader.readLine()!!)) } }\n\n// right: flowOn changes the context of everything above it\nflow {\n    while (true) emit(parse(reader.readLine() ?: break))\n}.flowOn(Dispatchers.IO)\n```\n\n```java\n// Java equivalent: Reactor has no such rule; subscribeOn moves the source to another scheduler\nFlux.<SettlementRecord>generate(sink -> {\n        String line = reader.readLine();\n        if (line == null) sink.complete(); else sink.next(parse(line));\n    })\n    .subscribeOn(Schedulers.boundedElastic());\n```\n\n`emit` must run in the collector's context, and the builder checks every call. The reason is in the first section: `emit` calls the collector's code directly, so an `emit` inside `withContext(Dispatchers.IO)` would run the collector's lambda on an IO thread that the collector never asked for. `flowOn(ctx)` is the tool. It changes the context of the flow **above** it, the upstream, and leaves everything below it, the collector included, where it was. You can use it more than once, and each one covers the operators up to the previous `flowOn`.\n\nTo do that, `flowOn` has to run the upstream in a separate coroutine, so when the dispatcher changes it puts a channel between the two halves. The KDoc says it buffers \"similarly to buffer operator\", with the default buffer size. The upstream can therefore run ahead of the collector by up to 64 values instead of exactly one. For a file read that is usually what you want.\n\nReactor's nearest tools are `subscribeOn`, which moves the source, and `publishOn`, which moves what follows it (lesson 6 of the reactive track). The difference that matters is the subscriber. With Reactor, unless you add a `publishOn`, your subscriber runs on the scheduler's thread too. With `flowOn`, the collector always stays in its own context.\n\nSo don't reach for `flowOn` to move the collector. If the collecting side blocks (it writes each line to a file, say), wrap the terminal call instead: `withContext(Dispatchers.IO) { flow.collect { writer.write(it) } }`.",
   "try": {
    "title": "Print which thread runs each stage",
    "minutes": 4,
    "steps": [
     "Read `FlowOnDemo.kt`. Predict the thread for `read`, `parse`, `format` and `save`.",
     "Run it.",
     "Move `.flowOn(Dispatchers.IO)` to just after the second `map`, before `collect`. Predict, then run.",
     "Run it with `-Pargs=wrong` to see the invariant check, then run the Java twin."
    ],
    "code": tryit("FlowOnDemo.kt", "FlowOnDemoJava.java", " -Pargs=wrong"),
    "expect": "`read` and `parse` run on a `DefaultDispatcher-worker` thread, while `format` and `save` run on `main`. After the move, `format` joins them on the worker, but `save` stays on `main`: no `flowOn` can move the collector. With `-Pargs=wrong` you get `IllegalStateException: Flow invariant is violated`. The Java twin needs `subscribeOn` for the source and `publishOn` to move the later steps to `single-1`."
   },
   "refs": [
    {"title": "flowOn (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html", "kind": "docs"}
   ]
  },
  {
   "h": "Handle upstream errors with catch, and every ending with onCompletion",
   "body": "Flows promise **exception transparency**. An exception thrown downstream, by an operator below or by the collector, belongs to the downstream, and a flow must not catch it and carry on emitting. The error-handling operators are built around that rule.\n\n`catch { e -> ... }` handles exceptions from the flow above it. It can log, emit a fallback, or rethrow. Exceptions thrown below it, including inside `collect { }`, pass straight through to whoever called `collect`.\n\n```kotlin\nsettlementRecords(file)                                         // may throw IOException\n    .map<SettlementRecord, ImportEvent> { ImportEvent.Imported(it.paymentId) }\n    .onCompletion { cause -> metrics.importEnded(cause) }      // sees every way the flow ends\n    .catch { e -> emit(ImportEvent.Aborted(e.message ?: \"error\")) }   // upstream failures only\n    .collect { ledger.save(it) }                                // a failure here reaches the caller\n```\n\n```java\n// Java equivalent: onErrorResume only handles errors from above it; doFinally runs on every exit\nsettlementRecords(file)\n    .<ImportEvent>map(r -> new Imported(r.paymentId()))\n    .doFinally(signal -> metrics.importEnded(signal))\n    .onErrorResume(e -> Flux.just(new Aborted(e.getMessage())))\n    .doOnNext(ledger::save)\n    .blockLast();\n```\n\n`onCompletion { cause -> }` is the flow's `finally`. It runs once, however the flow ends. `cause` is `null` after a normal end, the exception after a failure upstream or downstream, and a `CancellationException` when the collector stopped early, as `take` and `first` do. Unlike `catch`, it handles nothing: the exception carries on after it. Put it above `catch` to see the original error, or below to see only what got past.\n\nThe classic way to break the rule is a `try`/`catch` around `emit` inside a builder. `emit` runs the downstream code, so that `catch` also catches the collector's exceptions. If it then emits again, the flow throws `IllegalStateException` (\"Flow exception transparency is violated\"). That is one of the bugs in this lesson's lab. Use `catch` instead, which knows where it sits.\n\nOne more benefit of cold flows shows up here. `retry(3)` and `retryWhen { cause, attempt -> ... }` recover by collecting the upstream again, and that works only because the recipe can be run again from the top.\n\nFlow's error model is close to Reactor's. In both, a step that can fail goes above the error operator if you want it handled (`onEach` above `catch`, `doOnNext` above `onErrorResume`), and anything below it is the subscriber's problem. One difference makes Flow simpler: a failure in the collector is an ordinary exception thrown out of `collect`, so a plain `try` around the terminal call catches it.",
   "figure": {"svg": FIG, "caption": "catch covers the flow above it, never the collector. onCompletion sees every way the flow can end."},
   "try": {
    "title": "Fail upstream, then fail in the collector",
    "minutes": 4,
    "steps": [
     "Read `CatchDemo.kt`. By default the file read fails after two lines. Predict every line of output, including what `onCompletion` prints.",
     "Run it.",
     "Run it with `-Pargs=collector`, where saving `pay-2` throws instead. Predict first: does `catch` print anything?",
     "Run the Java twin both ways."
    ],
    "code": tryit("CatchDemo.kt", "CatchDemoJava.java", " -Pargs=collector", " -Pargs=collector"),
    "expect": "Upstream failure: `pay-1` and `pay-2` are collected, `onCompletion` prints the `IOException`, `catch` prints it and emits `ABORTED`, which is collected, and `collect` returns normally. Collector failure: `onCompletion` prints the `IllegalStateException`, `catch` prints nothing, and the caller gets `ledger db down`. The Java twin matches: `onErrorResume` only handles the upstream error, and `doFinally` reports `onError` or `cancel`."
   },
   "refs": [
    {"title": "catch (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/catch.html", "kind": "docs"},
    {"title": "onCompletion (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/on-completion.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A cold flow is a recipe card, not a pot of soup. Writing the card (calling `flow { }` and chaining `map` and `filter`) cooks nothing. Each diner who orders (each `collect`) gets the recipe cooked from scratch, one plate at a time, and the cook doesn't start the next plate until the diner has taken the last one. A diner who says \"that's enough\" (`take`) stops the cooking. `flowOn` moves the cooking to another kitchen while the diner stays at the same table. `catch` is the cook's rule for kitchen accidents, such as serving a fallback dish when the oven breaks, and it has nothing to say about a diner who drops their plate. The analogy breaks on cost: a real kitchen would never cook the same meal twice for two diners, and a flow does exactly that unless you share it, which is lesson 8 of this track.",
 "in_your_world": "Flows fit the streaming jobs in a payments platform. A statement export can stream ledger pages straight to the file instead of loading two million rows into a list. A settlement-file import can read the acquirer's file with a blocking reader under `flowOn(Dispatchers.IO)`, map each line to a ledger posting, report progress in `onCompletion`, and turn a truncated file into one `Aborted` event with `catch`. Two habits keep them honest. Put work that can fail and must be covered by `catch` (such as saving each record) in `onEach` above the `catch`, then call `collect()` with no lambda. And keep blocking JDBC or file reads above a `flowOn`, never inside `withContext` around `emit`. For a JDBC cursor, opening and closing the connection inside the `flow { }` body means each collector gets its own connection, and `onCompletion` or `finally` releases it however the flow ends.",
 "mistake": "The most common mistake is treating `.catch { }` at the end of a chain as a try/catch around the whole pipeline, including the `collect { }` lambda. It isn't: `catch` handles only the flow above it, so an exception thrown while saving a record in `collect` sails past it and fails the caller. People expect otherwise because every other error handler they know wraps everything inside it. The fix is to move the work that can fail upstream of `catch`, the pattern the Kotlin docs show: `records.onEach { ledger.save(it) }.catch { e -> log.warn(\"import failed\", e) }.collect()`. If the caller should see the failure instead, drop the `catch` and let it propagate.",
 "compare": {
  "title": "A settlement import: Flux vs Flow",
  "java": {"title": "SettlementImport.java", "src": "Flux<ImportEvent> importFile(LineReader reader) {\n    return Flux.<SettlementRecord>generate(sink -> {             // 1. a cold source, pulled on demand\n            String line = reader.readLine();\n            if (line == null) sink.complete(); else sink.next(parse(line));\n        })\n        .subscribeOn(Schedulers.boundedElastic())                // 2. the blocking read runs elsewhere\n        .<ImportEvent>map(r -> new Imported(r.paymentId()))\n        .doFinally(signal -> metrics.importEnded(signal))        // 3. every ending\n        .onErrorResume(e -> Flux.just(new Aborted(e.getMessage())));   // 4. upstream errors only\n}"},
  "kotlin": {"title": "SettlementImport.kt", "src": "fun importFile(reader: LineReader): Flow<ImportEvent> =\n    flow {                                                     // 1. a cold source, plain sequential code\n        while (true) emit(parse(reader.readLine() ?: break))\n    }\n        .flowOn(Dispatchers.IO)                                // 2. the blocking read runs elsewhere\n        .map<SettlementRecord, ImportEvent> { ImportEvent.Imported(it.paymentId) }\n        .onCompletion { cause -> metrics.importEnded(cause) }  // 3. every ending\n        .catch { e -> emit(ImportEvent.Aborted(e.message ?: \"error\")) }   // 4. upstream errors only"},
  "note": "The shapes line up step for step, and both are cold. The source is where they differ most. Reactor needs a generator callback with an explicit sink, because a Flux source must answer `request(n)` from subscribers. A Flow source is an ordinary loop: `emit` suspends until the collector is ready, so backpressure comes from suspension. Threads differ too. `subscribeOn` moves the whole chain until a `publishOn` moves it again, so Reactor subscribers often end up on a scheduler thread. `flowOn` moves only the upstream, and the collector stays in its own coroutine context. The error operators are nearly identical: `catch` and `onErrorResume` both handle only what is above them, and `onCompletion` and `doFinally` both run on every ending."
 },
 "worked": {
  "title": "Stream a statement export instead of loading it",
  "steps": [
   {"say": "A statement export loads every ledger entry for the month into a list, formats it, and writes the file. For a merchant with two million entries the pod runs out of heap, and nothing is written until all the pages are in.",
    "code": "suspend fun exportStatement(accountId: String, out: Path) {\n    val all = mutableListOf<LedgerEntry>()\n    var cursor: String? = null\n    do {\n        val page = api.page(accountId, cursor)\n        all += page.entries                        // every entry held in memory\n        cursor = page.nextCursor\n    } while (cursor != null)\n    withContext(Dispatchers.IO) {\n        Files.write(out, all.filter { it.amountCents != 0L }.map(::format))\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the same design: collect everything, then write\nvoid exportStatement(String accountId, Path out) throws IOException {\n    List<LedgerEntry> all = new ArrayList<>();\n    String cursor = null;\n    do {\n        LedgerPage page = api.page(accountId, cursor);\n        all.addAll(page.entries());                // every entry held in memory\n        cursor = page.nextCursor();\n    } while (cursor != null);\n    Files.write(out, all.stream().filter(e -> e.amountCents() != 0).map(Export::format).toList());\n}", "alt_lang": "java"},
   {"say": "Make the source a cold flow. Only one page is in memory at a time, and the next page is fetched only when the writer has caught up.",
    "code": "// 1. the source: pages on demand\nfun ledgerEntries(accountId: String): Flow<LedgerEntry> = flow {\n    var cursor: String? = null\n    do {\n        val page = api.page(accountId, cursor)\n        page.entries.forEach { emit(it) }\n        cursor = page.nextCursor\n    } while (cursor != null)\n}", "lang": "kotlin",
    "alt_code": "// 1. the source: pages on demand\nFlux<LedgerEntry> ledgerEntries(String accountId) {\n    return api.page(accountId, null)\n        .expand(p -> p.nextCursor() == null ? Mono.empty() : api.page(accountId, p.nextCursor()))\n        .flatMapIterable(LedgerPage::entries);\n}", "alt_lang": "java"},
   {"say": "Build the pipeline with intermediate operators, and write in the collector. The file write blocks, and it is on the collecting side, so it moves with `withContext` around the terminal call. `flowOn` wouldn't help: it never moves the collector.",
    "code": "suspend fun exportStatement(accountId: String, out: Path) =\n    withContext(Dispatchers.IO) {                    // 3. the collector's blocking writes run on IO\n        Files.newBufferedWriter(out).use { writer ->\n            ledgerEntries(accountId)\n                .filter { it.amountCents != 0L }     // 2. build: nothing runs yet\n                .map(::format)\n                .collect { line -> writer.write(line); writer.newLine() }   // runs it, one line at a time\n        }\n    }", "lang": "kotlin",
    "alt_code": "void exportStatement(String accountId, Path out) throws IOException {\n    try (BufferedWriter writer = Files.newBufferedWriter(out)) {\n        ledgerEntries(accountId)\n            .filter(e -> e.amountCents() != 0)           // 2. build: nothing runs yet\n            .map(Export::format)\n            .publishOn(Schedulers.boundedElastic())      // 3. the blocking writes run elsewhere\n            .doOnNext(line -> write(writer, line))\n            .blockLast();                                //    runs it\n    }\n}", "alt_lang": "java"},
   {"say": "A half-written statement must not look finished. Delete it when the flow ends with an error. `onCompletion` sees the cause, and the exception still reaches the caller afterwards, which is what an export job should do.",
    "code": "            ledgerEntries(accountId)\n                .filter { it.amountCents != 0L }\n                .map(::format)\n                .onCompletion { cause -> if (cause != null) Files.deleteIfExists(out) }   // 4. no partial files\n                .collect { line -> writer.write(line); writer.newLine() }", "lang": "kotlin",
    "alt_code": "        ledgerEntries(accountId)\n            .filter(e -> e.amountCents() != 0)\n            .map(Export::format)\n            .publishOn(Schedulers.boundedElastic())\n            .doOnNext(line -> write(writer, line))\n            .doOnError(e -> deleteQuietly(out))            // 4. no partial files\n            .blockLast();", "alt_lang": "java"},
   {"say": "Self-check: a caller runs `exportStatement(...)` inside `withTimeout(30.seconds)` and the timeout fires halfway. Is the partial file deleted? (Yes. The timeout cancels the coroutine, so the flow ends with a `CancellationException`, `cause` is not null, and `onCompletion` deletes the file. It runs inside the pipeline, before `use` has closed the writer. Linux doesn't mind, but Windows refuses to delete an open file, so a `finally` around `use` is the more portable place for the delete.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A ledger flow, a settlement reader and an importer",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/LedgerModel.kt", f"{lab}/main/{P}/LedgerFlows.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l07.*'",
  "steps": [
   "Run the tests. Seven of eight fail. `LedgerModel.kt` holds the API, the reader and the event types.",
   "Write `ledgerEntries` with `flow { }`: ask for pages starting with cursor `null`, emit every entry, and stop when `nextCursor` is `null`. The three ledger tests check that it is lazy, cold and stops early.",
   "Fix `settlementRecords`: delete the `withContext` and add `.flowOn(io)` after the builder.",
   "Rewrite `importReport` as a chain: `map` each record to `Imported`, then `onCompletion { onDone(it) }`, then `catch` that emits `Aborted(message)`.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "For `ledgerEntries`, a `do { ... } while (cursor != null)` loop inside `flow { }` is all you need. `emit` suspends until the collector is done, so `take(3)` cancels the loop before the next `api.page` call.",
   "`map` needs to know it produces the sealed type, not `Imported`, or `catch` can't emit `Aborted` into it. Write `.map<SettlementRecord, ImportEvent> { ... }`.",
   "Put `onCompletion` above `catch`: there it sees the upstream exception itself. Below `catch` it would see `null`, because `catch` turned the failure into a normal end.",
   "No `try` anywhere in `importReport`. A `try` around `emit` also catches the collector's exceptions, and that breaks exception transparency."
  ],
  "done_when": "All eight tests in `FlowBasicsTest` pass."
 },
 "drill": {
  "title": "A blocking file as a flow, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `fun chargebacks(reader: LineReader): Flow<Chargeback>` that reads lines with the blocking `reader.readLine()` (null at the end) on `Dispatchers.IO`, parses each with `parseChargeback(line)`, skips lines whose amount is 0, and emits `Chargeback.INVALID_FILE` once if reading or parsing fails.",
  "answer": {"lang": "kotlin", "src": "fun chargebacks(reader: LineReader): Flow<Chargeback> =\n    flow {\n        while (true) {\n            val line = reader.readLine() ?: break\n            emit(parseChargeback(line))\n        }\n    }\n        .flowOn(Dispatchers.IO)                        // the blocking reads, and nothing below\n        .filter { it.amountCents != 0L }\n        .catch { emit(Chargeback.INVALID_FILE) }      // upstream failures only",
            "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent with Reactor\nFlux<Chargeback> chargebacks(LineReader reader) {\n    return Flux.<Chargeback>generate(sink -> {\n            String line = reader.readLine();\n            if (line == null) sink.complete(); else sink.next(parseChargeback(line));\n        })\n        .subscribeOn(Schedulers.boundedElastic())     // the blocking reads\n        .filter(c -> c.amountCents() != 0)\n        .onErrorResume(e -> Flux.just(Chargeback.INVALID_FILE));   // upstream failures only\n}"}}
 },
 "recap": [
  "A `Flow` is cold: building it runs nothing, and the `flow { }` body runs from the top for every collector.",
  "Flows are sequential. `emit` suspends until the collector is done with the value, which gives backpressure for free, and `take` stops the producer early.",
  "Intermediate operators (`map`, `filter`, `onEach`, `take`) build a new flow; terminal operators (`collect`, `toList`, `first`) are suspend functions that run it.",
  "A flow runs in its collector's context. Move the upstream with `flowOn(dispatcher)`; `emit` inside `withContext` throws \"Flow invariant is violated\".",
  "`catch` handles only exceptions from above it, and the collector's exceptions pass through. Never wrap `emit` in a `try`.",
  "`onCompletion { cause -> }` runs on every ending: `null` for normal, the error for a failure, a `CancellationException` for an early stop."
 ],
 "quiz": [
  {"q": "What does this print?\n\n```kotlin\nval f = flow { println(\"start\"); emit(1); emit(2) }\nprintln(\"built\")\nf.collect { println(it) }\nf.take(1).collect { println(it) }\n```",
   "options": ["`built`, `start`, `1`, `2`, `start`, `1`", "`start`, `built`, `1`, `2`, `1`", "`built`, `start`, `1`, `2`, `1`", "`start`, `1`, `2`, `built`, `start`, `1`"],
   "answer": 0,
   "why": "Building the flow runs nothing, so `built` comes first. Each `collect` runs the body from the top, so `start` prints twice. `take(1)` cancels the flow after the first value, so the second run never emits 2."},
  {"q": "`records.map { parse(it) }.catch { emit(FALLBACK) }.collect { ledger.save(it) }`, and `ledger.save` throws `SQLException` on the third record. What happens?",
   "options": ["`catch` emits `FALLBACK` and the import carries on", "The `SQLException` reaches the caller of `collect`, and `catch` never sees it", "The flow retries the third record", "The exception is swallowed and `collect` returns normally"],
   "answer": 1,
   "why": "`catch` only handles exceptions from the flow above it. `save` runs in the collector, below `catch`, so its exception passes through to the caller. Move the save into `onEach` above `catch` if the fallback should cover it."},
  {"q": "In `runBlocking` on the main thread: `flow { A }.map { B }.flowOn(Dispatchers.IO).filter { C }.collect { D }`. Where do A, B, C and D run?",
   "options": ["All four on IO", "A on IO; B, C and D on main", "A and B on IO; C and D on main", "A, B and C on IO; D on main"],
   "answer": 2,
   "why": "`flowOn` changes the context of everything above it, the builder and the first `map`. Operators below it and the collector stay in the collector's context, which here is `main`."},
  {"q": "You collect `flow { withContext(Dispatchers.IO) { emit(loadRates()) } }`. What happens?",
   "options": ["It works, and the collector runs on IO too", "It deadlocks, because `emit` waits for the IO thread", "It works, and the collector stays on its own thread", "It throws `IllegalStateException`: the flow invariant is violated"],
   "answer": 3,
   "why": "A flow must emit in its collector's context, and the builder checks every `emit`. Move the work with `flow { emit(loadRates()) }.flowOn(Dispatchers.IO)` instead."},
  {"q": "From the reactive track: `Flux<String> f = Flux.just(\"pay-1\").map(id -> { log(id); return id; });` runs, and nobody ever subscribes to `f`. What is logged?",
   "options": ["`pay-1`, once, when `map` is called", "Nothing", "`pay-1`, once per operator in the chain", "An error, because a Flux must be subscribed"],
   "answer": 1,
   "why": "A Flux is cold, like a Flow: assembling operators runs nothing, and the work starts only on subscribe. A Kotlin flow built the same way logs nothing until a terminal operator collects it.",
   "from": "rx-02"}
 ],
 "flashcards": [
  {"front": "When does the body of a `flow { }` run?", "back": "Each time a terminal operator collects it, from the top. Building the flow runs nothing."},
  {"front": "Intermediate vs terminal flow operator: what's the difference?", "back": "Intermediate ones (`map`, `filter`, `take`) return a new flow and run nothing. Terminal ones (`collect`, `toList`, `first`) are suspend functions that run the flow."},
  {"front": "How does a flow get backpressure without `request(n)`?", "back": "`emit` suspends until the collector has finished with the value, so the producer can't run ahead."},
  {"front": "What does `.flowOn(Dispatchers.IO)` move?", "back": "Everything above it in the chain. Operators below it and the collector stay in the collector's context."},
  {"front": "What happens if you call `emit` inside `withContext(Dispatchers.IO)` in a `flow { }`?", "back": "The flow throws `IllegalStateException`: \"Flow invariant is violated\". Use `flowOn` instead."},
  {"front": "Does `.catch { }` handle an exception thrown inside `collect { }`?", "back": "No. It only handles exceptions from upstream; the collector's exceptions pass through to the caller."},
  {"front": "What `cause` does `onCompletion` get when the collector uses `take(1)`?", "back": "A `CancellationException`: the flow was stopped early. It gets `null` only after a normal end."}
 ],
 "terms": [
  {"term": "Cold flow", "plain": "A flow whose code runs only when collected, from the start, once per collector."},
  {"term": "Flow builder", "plain": "A function that creates a flow, such as `flow { }`, `flowOf` or `asFlow`."},
  {"term": "Intermediate operator", "plain": "An operator that returns a new flow without running anything, such as `map` or `filter`."},
  {"term": "Terminal operator", "plain": "A suspend function that runs the flow and consumes its values, such as `collect` or `toList`."},
  {"term": "Context preservation", "plain": "A flow runs in the collector's context; only `flowOn` changes the context of the part above it."},
  {"term": "Exception transparency", "plain": "A flow never catches and hides exceptions thrown by the code downstream of it."},
  {"term": "Upstream", "plain": "The part of a flow chain above a given operator, closer to the source."}
 ],
 "explain_back": {
  "prompt": "A teammate's import pipeline ends in `.catch { log.warn(\"import failed\", it) }.collect { repo.save(it) }`. When the database went down, the import failed with an exception instead of logging it, and they think `catch` is broken. Explain what is going on and how to change the code.",
  "answer": "catch only handles exceptions from the part of the chain above it. The save runs in the collect lambda, which is below catch, so when the database failed, the exception went straight to whoever called collect. That's deliberate: flows promise exception transparency, meaning a flow never hides the downstream code's failures. If we want the database failure to be logged the same way, the save has to move above the catch, into onEach, and then we call collect with no lambda: records.onEach { repo.save(it) }.catch { log.warn(\"import failed\", it) }.collect(). If the job should fail on a database outage instead, which is probably better for an import, we leave catch for upstream file errors only and let the save failure propagate."
 },
 "deeper": {
  "minutes": 10,
  "body": "Why does a flow check `emit` so strictly? Because operators rely on it. Every operator in the chain runs in one coroutine and assumes that nothing else calls its downstream at the same time. If `emit` could be called from another coroutine or thread, `map` and `filter` would need locks. The checks for context and for exception transparency are what let ordinary sequential code be a correct stream operator.\n\nWhen you need to emit from several coroutines, use `channelFlow { }`. Its `send` is safe from any coroutine started inside the builder, because a channel sits between the producers and the collector. `callbackFlow { }` is the same thing for callback APIs, and it requires `awaitClose { unregister() }` at the end, or it throws when the block returns. Lesson 9 of this track uses both.\n\nThe Flow interface itself is \"not stable for inheritance\", in the words of its KDoc: write flows with the builders, or extend `AbstractFlow` if you really need a class. That matters if you are tempted to implement `Flow` on a repository class.\n\nTwo older guide examples are worth knowing, because the current Kotlin docs dropped them. A busy flow built with `asFlow()` doesn't check for cancellation between items, which lesson 5 of this track showed. And `buffer()`, `conflate()` and `collectLatest` change the sequential model on purpose. With a producer that takes 100 ms per item and a collector that takes 300 ms, three items take about (100 + 300) x 3 = 1,200 ms plain, about 100 + 300 x 3 = 1,000 ms with `buffer()`, and about 700 to 800 ms with `conflate()`, which skips the middle item. Lesson 9 of this track runs those numbers."
 },
 "sources": [
  {"title": "Asynchronous Flow (Kotlin docs)", "url": "https://kotlinlang.org/docs/flow.html"},
  {"title": "Flow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/"},
  {"title": "flowOn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html"},
  {"title": "catch (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/catch.html"}
 ]
}
out = ROOT / "content/lessons/co-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
