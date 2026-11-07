import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l03"
PK = "kotlin/workbench/reactive/l03"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l03."

S1 = """`map` and `filter` are the operators you already know from `java.util.stream`, with one difference: they run when items arrive, not when you call them.

`map(f)` is one item in, one item out, synchronously, on whatever thread delivered the item. Use it for pure, fast transformations: parse a message, convert cents to a `Money`, compute a fee. `filter(p)` keeps the items that match. It also takes care of demand for you: a dropped item doesn't use up the downstream's request, so the source is asked for more. In the Try it below, `take(2)` asks for 2 items, yet the source runs through 1 to 6 to find two that pass the filter.

The most common `map` bug looks like this:

```java
Flux<Mono<String>> statuses = paymentIds.map(id -> issuer.fetchStatus(id));   // returns Mono<String>
```

```kotlin
val statuses: Flux<Mono<String>> = paymentIds.map { id -> issuer.fetchStatus(id) }   // returns Mono<String>
```

The function returns a `Mono`, so `map` gives you a `Flux<Mono<String>>`: a stream of recipes. Nothing subscribes to the inner `Mono`s, so not one issuer call is made. The compiler is happy, the tests that only count items are happy, and the statuses are never fetched. When your function returns a publisher, you need one of the flattening operators below. The type checker is your friend here: if you see `Flux<Mono<T>>`, you used `map` where you needed `flatMap`.

Two smaller rules. In Reactor 3.8 a `map` function may not return `null`; in Java the stream fails with `NullPointerException: The mapper [...] returned a null value.`, and in Kotlin the null-returning lambda doesn't compile, thanks to Reactor's JSpecify annotations. Filter first, or use `handle`, which works like a `map` that may emit zero or one item for each input, so it can skip the inputs that have no value. And `map` must stay fast and non-blocking, because it runs inline on the delivering thread. A JDBC call inside `map` blocks that thread for every item. Lesson 6 of this track shows where blocking calls belong."""

S2 = """`flatMap(f)` takes a function that returns a publisher, the **inner**, and does three things with it:

1. For each source item it calls `f` and subscribes to the inner right away, without waiting for earlier inners to finish.
2. It keeps up to `concurrency` inners subscribed at once. The default is 256.
3. It merges all their items into one output, in the order they arrive.

So the output order follows completion time, not input order. Its Javadoc says flatMap "does not necessarily preserve original ordering", and with real network calls it almost never does.

Two facts about flatMap surprise people. First, **flatMap does not create threads**. If the inner is synchronous, such as `Mono.fromCallable` with no scheduler, the inners run one after another on the calling thread. The concurrency comes from inners that are themselves asynchronous: a non-blocking HTTP call, a `Mono.delay`, or a blocking call moved to another scheduler with `subscribeOn` (lesson 6 of this track). flatMap only subscribes to several of them before the first one finishes.

Second, **concurrency is also demand**. `flatMap(f, 4)` asks the source for 4 items, then for 1 more each time an inner completes. That makes the concurrency argument a cap on in-flight calls:

```java
Flux<Score> scores = paymentIds.flatMap(id -> fraud.score(id), 4);   // at most 4 calls at once
```

```kotlin
// the lambda stays inside the parentheses when another argument follows it
val scores: Flux<Score> = paymentIds.flatMap({ id -> fraud.score(id) }, 4)   // at most 4 calls at once
```

Set it whenever the inner touches something shared. The default of 256 means up to 256 simultaneous calls to the fraud service, or 256 queries waiting on a connection pool of 20. Pick the number from the downstream's limit, not from a feeling.

Each inner also gets a prefetch of 32: if an inner is a `Flux`, flatMap requests 32 items from it at a time. That rarely matters for `Mono` inners.

One more behaviour to know now: if any inner fails, flatMap cancels the others and the whole stream fails. Lesson 5 of this track shows how to contain an error inside one inner."""

S3 = """When order matters, you have two choices with very different costs.

`concatMap(f)` subscribes to one inner at a time. It asks the source for one item, waits for that item's inner to complete, then asks for the next. Output order is input order, and the total time is the sum of all the inner times. In Reactor 3.8 it does no prefetching on the source at all.

`flatMapSequential(f)` subscribes to inners eagerly, like flatMap (concurrency 256, prefetch 32), but it holds back results from later inners until all earlier inners have finished. Output order is input order, and the total time is about the time of the slowest inner. The cost is memory, since results that finish early wait in a buffer, and **head-of-line blocking**: one slow first call holds back everything behind it.

Here are the three on the same input, measured with virtual time (a test clock that skips the waits, lesson 8 of this track). The source emits 3, 1, 2 at once, and item `i` takes `i x 100 ms`:

| Operator | Output | Done at |
|---|---|---|
| `flatMap` | `[1, 2, 3]` | 300 ms |
| `concatMap` | `[3, 1, 2]` | 600 ms |
| `flatMapSequential` | `[3, 1, 2]` | 300 ms |

Ordered output is not the only reason to pick `concatMap`. Pick it when each step must *start* after the previous one has finished. Ledger postings for one account are the classic case: posting 2 may only go out after posting 1 is acknowledged, because the ledger checks the balance, and after a failed posting nothing else may be sent. `flatMapSequential` gives you the right order in the output while sending all four postings at once, which is exactly what the ledger must not see.

A short guide:

| You need | Use |
|---|---|
| Independent calls, any order | `flatMap(f, n)` |
| Output in input order, calls may overlap | `flatMapSequential(f, n)` |
| One at a time, each after the previous | `concatMap(f)` |
| Only the latest item matters | `switchMap(f)` |"""

S4 = """`switchMap(f)` is for streams where a new item makes the old work pointless. Each time the source emits, switchMap cancels the inner for the previous item and subscribes to a new one.

The checkout page is the payments example. The user picks EUR, then GBP 50 ms later. The quote for EUR is still in flight. With `flatMap`, both quotes eventually arrive, and if the EUR quote is slower, it arrives last and overwrites the GBP one on screen. That is a race with a real cost: the customer sees a price for the wrong currency. With `switchMap`, the EUR quote is cancelled the moment GBP is picked, and its result can never reach you.

```java
Flux<Quote> quotes = currencyPicks.switchMap(ccy -> fx.quote(ccy));
```

```kotlin
val quotes: Flux<Quote> = currencyPicks.switchMap { ccy -> fx.quote(ccy) }
```

Cancellation travels upstream through the inner, so a reactive HTTP client can abort the request it was making, and a `Flux.interval` inside stops ticking. Whether the far side stops its work depends on that service; cancelling only promises that you stop listening.

Some details. switchMap requests an unbounded amount from its source, so it applies no backpressure upstream: every pick is seen, and older ones are simply dropped by cancelling. The stream completes when the source has completed and the last inner has completed. Search-as-you-type, "recompute when the config changes" and "show the latest balance" all have this shape.

Kotlin Flow has the same operator under a different name: `flatMapLatest`, and `mapLatest` when the block returns a single value. The comparison below says how the other three map onto Flow."""

# marble diagram: source 3,1,2 at t=0; item i takes i*100 ms
X0, PX = 170, 0.7
def x(ms): return X0 + ms * PX
rows = [
    ("flatMap", 112, [(100, "1"), (200, "2"), (300, "3")], "300 ms"),
    ("concatMap", 172, [(300, "3"), (400, "1"), (600, "2")], "600 ms"),
    ("flatMapSequential", 232, [(300, "3"), (300, "1"), (300, "2")], "300 ms"),
]
SVG = ('<svg viewBox="0 0 700 280" role="img" aria-label="Marble diagram. Source emits 3, 1, 2 at time zero. flatMap emits 1, 2, 3 at 100, 200 and 300 ms. '
       'concatMap emits 3, 1, 2 at 300, 400 and 600 ms. flatMapSequential emits 3, 1, 2 together at 300 ms.">')
for ms in range(0, 700, 100):
    SVG += f'<line class="ln-d" x1="{x(ms)}" y1="40" x2="{x(ms)}" y2="250"/>'
    SVG += f'<text class="t-s t-m" x="{x(ms)}" y="30" text-anchor="middle">{ms}</text>'
SVG += '<text class="t-s t-m" x="668" y="30" text-anchor="middle">ms</text>'
SVG += f'<text class="t t-code" x="20" y="61">source</text><line class="ln" x1="{X0}" y1="56" x2="634" y2="56" marker-end="url(#arr)"/>'
SVG += '<text class="t-s t-m" x="330" y="82" text-anchor="middle">all three at 0 ms</text>'
for k, v in enumerate("312"):
    cx = X0 + 4 + k * 26
    SVG += f'<circle class="box-b" cx="{cx}" cy="56" r="11"/><text class="t-s" x="{cx}" y="60" text-anchor="middle">{v}</text>'
for name, y, marbles, done in rows:
    SVG += f'<text class="t t-code" x="20" y="{y + 5}">{name}</text>'
    SVG += f'<line class="ln" x1="{X0}" y1="{y}" x2="634" y2="{y}" marker-end="url(#arr)"/>'
    seen = {}
    for ms, v in marbles:
        off = seen.get(ms, 0); seen[ms] = off + 1
        cx = x(ms) + off * 26
        SVG += f'<circle class="box-a" cx="{cx}" cy="{y}" r="11"/><text class="t-s" x="{cx}" y="{y + 4}" text-anchor="middle">{v}</text>'
    SVG += f'<text class="t-s t-ok" x="668" y="{y + 4}" text-anchor="middle">{done}</text>'
SVG += '<text class="t-s t-m" x="420" y="272" text-anchor="middle">flatMapSequential: 1 and 2 finished early and waited in a buffer for 3</text>'
SVG += '</svg>'

W0K = """fun report(paymentIds: Flux<String>): Flux<SettlementRow> =
    paymentIds
        .flatMap { id -> issuer.settlementStatus(id) }   // Mono<Status>, about 120 ms
        .map { SettlementRow.from(it) }"""
W2K = """paymentIds
    .flatMap({ id -> issuer.settlementStatus(id) }, 10)   // 1. never more than 10 in flight
    .map { SettlementRow.from(it) }"""
W3K = """paymentIds
    .flatMapSequential({ id -> issuer.settlementStatus(id) }, 10)   // 2. same cap, input order
    .map { SettlementRow.from(it) }"""
CK = """// any order, at most 4 fraud calls in flight
val scores = paymentIds.flatMap({ id -> fraud.score(id) }, 4)

// one at a time, each after the previous one completes
val acks = postings.concatMap { p -> ledger.post(p) }

// overlapping calls, output in input order
val rows = ids.flatMapSequential({ id -> settlement.row(id) }, 4)

// latest wins: a new pick cancels the previous quote
val quotes = picks.switchMap { ccy -> fx.quote(ccy) }"""

L = {
 "id": "rx-03",
 "title": "Transforming streams: map, flatMap, concatMap",
 "minutes": 35,
 "goal": "By the end you can choose between `map`, `flatMap`, `concatMap`, `flatMapSequential` and `switchMap` from the requirements (order, one at a time, a concurrency limit, latest wins), and prove the choice with a virtual-time test.",
 "warmup": {
  "q": "A source emits 3, 1, 2 at the same moment. `flatMap` turns item `i` into a call that takes `i x 100 ms`. What comes out?",
  "options": [
   "`[3, 1, 2]`, finishing at 600 ms",
   "`[1, 2, 3]`, finishing at 300 ms",
   "`[3, 1, 2]`, finishing at 300 ms",
   "`[1, 2, 3]`, finishing at 600 ms"
  ],
  "answer": 1,
  "why": "flatMap subscribes to all three calls at once and emits each result as it finishes: 1 at 100 ms, 2 at 200 ms, 3 at 300 ms. Keeping the input order with the same speed is `flatMapSequential`; keeping order by running one at a time is `concatMap`, which takes 600 ms."
 },
 "sections": [
  {
   "h": "map and filter work one item at a time",
   "body": S1,
   "try": {
    "title": "Count the demand a filter sends",
    "minutes": 3,
    "steps": [
     "`MapFilterDemo` filters the numbers 1 to 10 down to multiples of 3, maps them to amounts, and takes 2. A `doOnRequest` prints what the source is asked for.",
     "Predict how many requests the source sees and which amounts print. In Java, predict what the second pipeline does with the `null`; in Kotlin, read the comment that says why that line can't be written.",
     "Run it. Then change `take(2)` to `take(4)` and run again."
    ],
    "code": {"lang": "java", "title": "MapFilterDemo.java", "src": read(f"{lab}/demo/{P}/MapFilterDemo.java"),
             "run": DEMO + "MapFilterDemo", "file": f"{lab}/demo/{P}/MapFilterDemo.java",
             "alt": {"lang": "kotlin", "title": "MapFilterDemo.kt", "src": read(f"{lab}/demo/{PK}/MapFilterDemo.kt"),
                     "run": DEMO + "MapFilterDemoKt", "file": f"{lab}/demo/{PK}/MapFilterDemo.kt"}},
    "expect": "The source is asked for 2 once, yet it emits 1 to 6, because `filter` tells it which items didn't count. You get `EUR 30` and `EUR 60`. The Java version's second pipeline prints `scheme VISA`, then `error: java.lang.NullPointerException: The mapper [...] returned a null value.`. The Kotlin version uses `handle`, so it prints only `scheme VISA`: the null case was caught by the compiler instead. With `take(4)` the source is asked for 4 and runs to 10, but only three multiples of 3 exist, so you get three amounts and the stream completes."
   }
  },
  {
   "h": "flatMap subscribes to many inners at once",
   "body": S2,
   "try": {
    "title": "Where does flatMap's concurrency come from?",
    "minutes": 4,
    "steps": [
     "`FlatMapThreadsDemo` runs flatMap with synchronous inners, then with `Mono.delay` inners, printing the thread for each result. Then it prints what flatMap and concatMap ask the source for.",
     "Predict the threads and the order in parts 1 and 2. Predict the request numbers in part 3.",
     "Run it. Then change part 3's concurrency from 2 to 3 and predict the new request line."
    ],
    "code": {"lang": "java", "title": "FlatMapThreadsDemo.java", "src": read(f"{lab}/demo/{P}/FlatMapThreadsDemo.java"),
             "run": DEMO + "FlatMapThreadsDemo", "file": f"{lab}/demo/{P}/FlatMapThreadsDemo.java",
             "alt": {"lang": "kotlin", "title": "FlatMapThreadsDemo.kt", "src": read(f"{lab}/demo/{PK}/FlatMapThreadsDemo.kt"),
                     "run": DEMO + "FlatMapThreadsDemoKt", "file": f"{lab}/demo/{PK}/FlatMapThreadsDemo.kt"}},
    "expect": "Part 1 runs on `main`, in order: flatMap made no threads. Part 2 prints score 3 first (100 ms), then 2, then 1, on `parallel-N` threads that belong to `Mono.delay`. Part 3 prints `256` for plain flatMap, `2 1 1 1 1` for concurrency 2, and `1 1 1 1 1 1` for concatMap. With concurrency 3 you get `3 1 1 1`: the first request is the cap, then one more per finished inner."
   },
   "refs": [{"title": "Flux Javadoc source, reactor-core 3.8.x (flatMap, concatMap, flatMapSequential, switchMap)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}]
  },
  {
   "h": "Putting the order back: concatMap and flatMapSequential",
   "body": S3,
   "figure": {"svg": SVG, "caption": "The same three calls through three operators. Only flatMapSequential is both ordered and fast, and it pays with a buffer."},
   "try": {
    "title": "Measure the three operators",
    "minutes": 3,
    "steps": [
     "`OrderingDemo` runs the source 3, 1, 2 through all three operators with real delays.",
     "Write down your prediction for each output and time, then run it.",
     "Change the source to `Flux.just(1, 2, 3)`. Which operator's output changes, and which timing changes?"
    ],
    "code": {"lang": "java", "title": "OrderingDemo.java", "src": read(f"{lab}/demo/{P}/OrderingDemo.java"),
             "run": DEMO + "OrderingDemo", "file": f"{lab}/demo/{P}/OrderingDemo.java",
             "alt": {"lang": "kotlin", "title": "OrderingDemo.kt", "src": read(f"{lab}/demo/{PK}/OrderingDemo.kt"),
                     "run": DEMO + "OrderingDemoKt", "file": f"{lab}/demo/{PK}/OrderingDemo.kt"}},
    "expect": "`flatMap -> [1, 2, 3]` in about 300 ms, `concatMap -> [3, 1, 2]` in about 600 ms, `flatMapSequential -> [3, 1, 2]` in about 300 ms, matching the table. With source 1, 2, 3 all three print `[1, 2, 3]`: the input order now matches the finishing order, so flatMap looks ordered. That is why order bugs hide in tests with uniform delays. concatMap still takes 600 ms, and the others still take 300 ms."
   }
  },
  {
   "h": "When only the latest matters: switchMap",
   "body": S4,
   "try": {
    "title": "Cancel a stale lookup",
    "minutes": 3,
    "steps": [
     "`SwitchMapDemo` simulates a user typing a card prefix: `41` at 100 ms, then `4111` at 200 ms. Each prefix starts a lookup that streams a suggestion every 60 ms, three in total.",
     "Predict which suggestions are shown, and when the first lookup is cancelled. Run it.",
     "Replace `switchMap` with `flatMap` and run it again."
    ],
    "code": {"lang": "java", "title": "SwitchMapDemo.java", "src": read(f"{lab}/demo/{P}/SwitchMapDemo.java"),
             "run": DEMO + "SwitchMapDemo", "file": f"{lab}/demo/{P}/SwitchMapDemo.java",
             "alt": {"lang": "kotlin", "title": "SwitchMapDemo.kt", "src": read(f"{lab}/demo/{PK}/SwitchMapDemo.kt"),
                     "run": DEMO + "SwitchMapDemoKt", "file": f"{lab}/demo/{PK}/SwitchMapDemo.kt"}},
    "expect": "You see `show 41-match0` (at 160 ms), then `cancelled lookup for 41` when `4111` arrives at 200 ms, then the three `4111` suggestions: `[41-match0, 4111-match0, 4111-match1, 4111-match2]`. With flatMap nothing is cancelled, and the two lookups interleave: `41-match1` and `41-match2` show up between the `4111` suggestions, which is the stale-result race switchMap prevents."
   },
   "refs": [{"title": "Kotlin docs: Asynchronous Flow (flattening flows)", "url": "https://kotlinlang.org/docs/flow.html", "kind": "docs"}]
  }
 ],
 "analogy": "Think of a kitchen pass during a rush. `flatMap` is several cooks working different orders at once; plates go out as they're ready, so table 7 may get food before table 3. `concatMap` is one cook doing one order start to finish before reading the next ticket. `flatMapSequential` is several cooks, but the waiter holds finished plates until every earlier table has been served. `switchMap` is a customer who keeps changing their order: the cook bins the half-made dish each time. The analogy breaks on cancellation: a cook can stop at once, but a cancelled reactive call only promises you stop listening. The remote service may still finish the work.",
 "in_your_world": "Most payment pipelines contain all four shapes. Fraud scoring and merchant enrichment are independent calls: `flatMap` with the concurrency set to what the downstream allows, not the default 256. Postings for one ledger account and state changes for one payment must happen in order and one at a time: `concatMap`, the same reason a Kafka topic keys messages by account so one partition sees them in order. A settlement report that must list rows in input order but can fetch them in parallel is `flatMapSequential`. The FX quote on a checkout page, or a card BIN lookup as the user types, is `switchMap`.",
 "mistake": "The most common mistake is reaching for plain `flatMap` for everything. It compiles, the tests pass with uniform fake delays, and in production two things go wrong. Order breaks: ledger postings or payment state changes arrive out of order as soon as latencies vary. And concurrency explodes: 256 simultaneous calls hit a service sized for 20. Decide on purpose: does order matter, must each call wait for the previous one, and what is the downstream's concurrency limit?",
 "compare": {
  "title": "The four flattening operators in Java and Kotlin",
  "java": {"title": "PaymentFlows.java", "src": "// any order, at most 4 fraud calls in flight\nFlux<String> scores = paymentIds.flatMap(id -> fraud.score(id), 4);\n\n// one at a time, each after the previous one completes\nFlux<String> acks = postings.concatMap(p -> ledger.post(p));\n\n// overlapping calls, output in input order\nFlux<String> rows = ids.flatMapSequential(id -> settlement.row(id), 4);\n\n// latest wins: a new pick cancels the previous quote\nFlux<String> quotes = picks.switchMap(ccy -> fx.quote(ccy));"},
  "kotlin": {"title": "PaymentFlows.kt", "src": CK},
  "note": "Same operators, two syntax details. In Kotlin a lambda can only trail outside the parentheses when it is the last argument, so `flatMap({ ... }, 4)` keeps it inside. And Kotlin lambdas adapt to Reactor's `Function<? super T, Publisher<? extends V>>` parameter without fuss, so the `switchMap` typing problem the lab hints at in Java doesn't arise. The bigger difference is with Kotlin's own streams. In Kotlin Flow the default is sequential: a suspending `map` waits for each call, so it behaves like `concatMap`, and you opt in to concurrency with `flatMapMerge(concurrency = 4)`, whose default is 16 rather than Reactor's 256. `flatMapLatest` and `mapLatest` are Flow's `switchMap`, and there is no `flatMapSequential`. In kotlinx.coroutines 1.11 those Flow operators still need `@OptIn(ExperimentalCoroutinesApi::class)`. `FlowOperators.kt` in the demo folder runs the same 3, 1, 2 example with Flow (`-Pmain=workbench.reactive.l03.FlowOperatorsKt`)."
 },
 "worked": {
  "title": "Fix a settlement job that floods the issuer",
  "steps": [
   {"say": "A nightly job fetches the settlement status of every payment from the card issuer. The issuer's contract allows 10 concurrent calls per merchant. Last night the job got hundreds of `429 Too Many Requests` responses. Read the pipeline.",
    "code": "Flux<SettlementRow> report(Flux<String> paymentIds) {\n    return paymentIds\n            .flatMap(id -> issuer.settlementStatus(id))   // Mono<Status>, about 120 ms\n            .map(SettlementRow::from);\n}", "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "flatMap with no concurrency argument subscribes to up to 256 inners at once, and its first request to the source is 256. With 50,000 payment ids, the job keeps about 256 calls in flight the whole time. The issuer allows 10.", "code": "", "lang": ""},
   {"say": "Cap the in-flight calls at the contract's limit. By Little's law, 10 calls in flight at 120 ms each gives at most 10 / 0.12 s, about 83 calls a second, so 50,000 payments take about 10 minutes. That's the honest throughput of this contract.",
    "code": "return paymentIds\n        .flatMap(id -> issuer.settlementStatus(id), 10)   // 1. never more than 10 in flight\n        .map(SettlementRow::from);", "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "The finance team then asks for the report in input order, so it diffs cleanly against yesterday's. Switching to `concatMap` would cut throughput to one call at a time, about 8 a second. `flatMapSequential` keeps the cap of 10 and restores the order, at the cost of buffering results that finish early.",
    "code": "return paymentIds\n        .flatMapSequential(id -> issuer.settlementStatus(id), 10)   // 2. same cap, input order\n        .map(SettlementRow::from);", "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Pick the right operator for three payment flows",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/PaymentFlows.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l03.*'",
  "steps": [
   "Read the Javadoc on each of the three methods in `PaymentFlows`. Each body is one line. Decide on the operator before you write anything.",
   "`fraudScores`: any order, at most 4 calls in flight, and all 4 slots used.",
   "`postAll`: each posting only after the previous one is acknowledged, results in posting order, and nothing sent after a failure.",
   "`latestQuotes`: only the most recent pick matters; a quote in flight must be cancelled when the user picks again.",
   "Run the tests. They use `StepVerifier.withVirtualTime`, so the 100 ms delays take no real time. Read `PaymentFlowsTest` to see how it measures calls in flight and cancellations."
  ],
  "hints": [
   "If a test says `Expecting AtomicInteger(12) to have value: 4`, you used flatMap without its concurrency argument.",
   "`flatMapSequential` gets the order right for `postAll` but sends all four postings at once; the in-flight check catches it.",
   "If `currencyPicks.switchMap(fxService)` doesn't compile, pass a lambda: `switchMap(ccy -> fxService.apply(ccy))`. `switchMap` declares its parameter as `Function<? super T, Publisher<? extends V>>`, and a `Function<String, Mono<String>>` variable is not that type, although a lambda or method reference can be."
  ],
  "done_when": "All four tests in `PaymentFlowsTest` pass."
 },
 "drill": {
  "title": "Predict the marbles",
  "minutes": 5,
  "prompt": "No code this time. A source emits A, B and C at the same moment. A's call takes 300 ms, B's 100 ms, C's 200 ms. On paper, write the output order and the time the stream completes for `flatMap`, `concatMap`, `flatMapSequential` and `switchMap`. Then check your answers.",
  "answer": {"lang": "text", "src": "flatMap            [B, C, A]   done at 300 ms   (B at 100, C at 200, A at 300)\nconcatMap          [A, B, C]   done at 600 ms   (A at 300, B at 400, C at 600)\nflatMapSequential  [A, B, C]   done at 300 ms   (all three released when A finishes)\nswitchMap          [C]         done at 200 ms   (B cancels A, C cancels B, only C finishes)"}
 },
 "recap": [
  "`map` is synchronous, one in and one out. If your function returns a `Mono`, `map` gives you `Flux<Mono<T>>` and no calls are made.",
  "`flatMap` subscribes to up to `concurrency` inners at once (default 256) and emits results in completion order. It creates no threads.",
  "The concurrency argument is also flatMap's demand: `flatMap(f, 4)` requests 4, then 1 per finished inner. Use it as a cap on in-flight calls.",
  "`concatMap` runs one inner at a time, in order; `flatMapSequential` runs them concurrently but buffers to emit in order.",
  "`switchMap` cancels the previous inner when a new item arrives. Use it when only the latest result matters."
 ],
 "quiz": [
  {"q": "You need to enrich 10,000 transactions with merchant data. The merchant service allows 20 concurrent calls, and the output order doesn't matter. Which line fits?",
   "options": ["`tx.map(t -> merchants.lookup(t))`", "`tx.concatMap(t -> merchants.lookup(t))`", "`tx.flatMap(t -> merchants.lookup(t), 20)`", "`tx.switchMap(t -> merchants.lookup(t))`"],
   "answer": 2,
   "why": "flatMap with concurrency 20 keeps exactly as many calls in flight as the service allows. `map` would produce a `Flux<Mono<...>>` and make no calls. `concatMap` is correct but makes one call at a time, and `switchMap` would cancel all but the last lookup."},
  {"q": "`issuer.fetchStatus(id)` returns `Mono<String>`. What happens when you subscribe to `ids.map(id -> issuer.fetchStatus(id))`?",
   "options": ["Each status is fetched, one at a time", "You receive one `Mono<String>` per id, and no issuer call is made unless something subscribes to those Monos", "It doesn't compile", "All statuses are fetched in parallel"],
   "answer": 1,
   "why": "`map` wraps each returned `Mono` as an item, giving `Flux<Mono<String>>`. A `Mono` is a recipe; nobody subscribes to these, so nothing runs. `flatMap` (or `concatMap`) is what subscribes to the inner publishers."},
  {"q": "Postings for one account must reach the ledger one at a time, each after the previous one is acknowledged. A teammate proposes `flatMapSequential` because \"it keeps the order\". What is wrong with that?",
   "options": ["Nothing, it is the right choice", "It sends all postings concurrently and only reorders the results", "It drops postings that finish out of order", "It cannot handle errors"],
   "answer": 1,
   "why": "flatMapSequential subscribes to inners eagerly, so the ledger sees all postings at once. Only the output is reordered. `concatMap` is the operator that waits for each inner to complete before subscribing to the next."},
  {"q": "A `switchMap` inner is still running when the source emits a new item. What happens to that inner?",
   "options": ["It is cancelled, and its results never reach the output", "It finishes, and its results are emitted after the new inner's", "It is paused until the new inner completes", "switchMap waits for it before starting the new inner"],
   "answer": 0,
   "why": "switchMap cancels the current inner and switches to a new one for each source item. That prevents a stale slow result from overwriting a newer one, which is what can happen with flatMap."},
  {"q": "From \"CompletableFuture: composing async steps\": which `CompletableFuture` method plays the same role as Reactor's `flatMap` for one async step?",
   "options": ["`thenApply`", "`thenAccept`", "`thenCombine`", "`thenCompose`"],
   "answer": 3,
   "why": "`thenCompose` takes a function that returns another `CompletableFuture` and flattens it, just as flatMap subscribes to the publisher your function returns. `thenApply` is like `map`: given a function that returns a future, it produces a `CompletableFuture<CompletableFuture<T>>`.",
   "from": "exec-06"}
 ],
 "flashcards": [
  {"front": "What is flatMap's default concurrency in Reactor?", "back": "256 inners at once (and a prefetch of 32 per inner). Its first request to the source is also 256."},
  {"front": "`flatMap(f, 4)`: what does it request from the source?", "back": "4 at first, then 1 more each time an inner completes. So at most 4 inners are in flight."},
  {"front": "Does flatMap run inners on several threads?", "back": "No. It only subscribes to several at once. Parallelism comes from inners that are themselves asynchronous (non-blocking IO, `Mono.delay`, `subscribeOn`)."},
  {"front": "Source 3, 1, 2; item i takes i x 100 ms. Output of `concatMap`, and when does it finish?", "back": "`[3, 1, 2]` at 600 ms: one at a time, in order."},
  {"front": "What does `flatMapSequential` trade for ordered output at flatMap speed?", "back": "Memory: results that finish early are buffered until all earlier inners are done (and a slow first item holds back the rest)."},
  {"front": "When does `switchMap` cancel an inner?", "back": "As soon as the source emits a new item. Only the latest item's inner is kept."},
  {"front": "Kotlin Flow equivalent of Reactor's `switchMap`?", "back": "`flatMapLatest`, or `mapLatest` when the block returns one value."}
 ],
 "terms": [
  {"term": "Inner publisher", "plain": "The `Mono` or `Flux` your function returns inside flatMap, concatMap or switchMap."},
  {"term": "Flattening", "plain": "Subscribing to inner publishers and merging their items into one output stream."},
  {"term": "Concurrency (flatMap)", "plain": "The maximum number of inners flatMap keeps subscribed at once, and its first request upstream."},
  {"term": "Prefetch", "plain": "How many items an operator requests ahead from a source so they are ready when needed."},
  {"term": "Head-of-line blocking", "plain": "One slow item at the front holds back items behind it that are already done."},
  {"term": "Virtual time", "plain": "A fake clock in tests (`StepVerifier.withVirtualTime`) that you move forward by hand, so delays take no real time."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate, in your own words, the difference between `flatMap`, `concatMap` and `flatMapSequential`, and give one payments example where each is the right choice.",
  "answer": "All three call a function that returns a publisher and subscribe to it. flatMap subscribes to many at once, up to its concurrency, and emits results as they finish, so it's fast and unordered; fraud scoring a batch of payments, with concurrency set to what the fraud service allows, is a good fit. concatMap subscribes to one at a time and only starts the next after the previous completes, so it's ordered and slow; ledger postings for one account need that, because each posting depends on the balance after the previous one. flatMapSequential subscribes to many at once like flatMap but buffers results so they come out in input order; a settlement report that must list payments in input order but can fetch their statuses in parallel fits it."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Ordering per key with concurrency across keys.** Postings must be ordered per account, but different accounts can be posted in parallel. The usual shape is `groupBy` plus `concatMap` inside a `flatMap`:\n\n```java\npostings.groupBy(Posting::accountId)\n        .flatMap(account -> account.concatMap(ledger::post), 512)\n```\n\n```kotlin\npostings.groupBy { it.accountId }\n    .flatMap({ account -> account.concatMap { ledger.post(it) } }, 512)\n```\n\nThere is a trap. Each group stays open until the source completes, and flatMap only drains as many groups as its concurrency allows. The `groupBy` Javadoc says the concurrency of the subscriber \"should be greater than or equal to the number of groups created\". In a measured run, `Flux.range(0, 1000).groupBy(i -> i % 300).flatMap(g -> g.reduce(0, Integer::sum), 10)` simply hung; with concurrency 300 it completed. If the number of accounts is unbounded, partition by `accountId.hashCode() % 32` instead and use concurrency 32, which is how a Kafka topic does it.\n\n**Delaying errors.** By default an error in any inner ends the whole stream. `flatMapDelayError(f, concurrency, prefetch)` and `concatMapDelayError(f)` let the other inners finish and report the error at the end. Use them for batch jobs where partial results are still useful, then decide what to do with the error.\n\n**`flatMapIterable`.** When your function returns a `List` (already in memory), `flatMapIterable(order -> order.lines())` flattens it without creating inner publishers.\n\n**`handle`.** `handle((item, sink) -> { if (ok(item)) sink.next(convert(item)); })` is a map and a filter in one step, and it lets you skip an item instead of returning `null`."
 },
 "sources": [
  {"title": "Flux Javadoc source, reactor-core 3.8.x", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java"},
  {"title": "Reactor 3 reference guide", "url": "https://projectreactor.io/docs/core/release/reference/index.html"},
  {"title": "Reactor reference: Testing with StepVerifier and virtual time (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/testing.adoc"},
  {"title": "Kotlin docs: Asynchronous Flow", "url": "https://kotlinlang.org/docs/flow.html"}
 ]
}
out = ROOT / "content/lessons/rx-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
