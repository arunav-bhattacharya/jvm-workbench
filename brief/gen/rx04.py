import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l04"
PK = "kotlin/workbench/reactive/l04"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l04."


def code(name, title=None):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


S1 = """`Flux.zip(a, b)` waits until every source has emitted one item, combines those items, and repeats. It pairs by position: first with first, second with second. It completes as soon as any source completes, so the extra items of a longer source are dropped. `Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b"))` gives `[[1,a], [2,b]]`, and the 3 is never used.

In service code you'll use `Mono.zip` far more often, for fan-out: run several independent calls at once and combine the results.

```java
Mono<Quote> quote = Mono.zip(fx.rate("EURUSD"), fees.forMerchant(m), limits.forCustomer(c))
        .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));
```

```kotlin
val quote: Mono<Quote> = Mono.zip(fx.rate("EURUSD"), fees.forMerchant(m), limits.forCustomer(c))
    .map { t -> Quote(t.t1, t.t2, t.t3) }
```

`Mono.zip` subscribes to all of its sources immediately. If the FX rate takes 100 ms, the fee schedule 300 ms and the limit 200 ms, the quote is ready after 300 ms, not 600. There are typed overloads for up to eight sources (`Tuple2` to `Tuple8`).

If any source fails, the zip fails and cancels the others. That is usually what you want. The surprise is the other terminal signal. The `Mono.zip` Javadoc says it plainly: an "empty completion of any source will cause other sources to be cancelled and the resulting Mono to immediately ... complete". **No error, no value.** A customer with no limit configured makes the whole quote complete empty. A controller turns that into an empty 200 response, `block()` returns `null`, and the logs show nothing at all.

Decide what "empty" means for each source and say it in code. Either it is an error:

```java
limits.forCustomer(c)
        .switchIfEmpty(Mono.error(() -> new IllegalStateException("missing limit")))
```

```kotlin
limits.forCustomer(c)
    .switchIfEmpty(Mono.error { IllegalStateException("missing limit") })
```

or it has a sensible default, such as `fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO)`. A `Mono<Void>` is always empty, so it can never take part in a zip; the last section shows the tool for that."""

S2 = """`Flux.merge(a, b)` subscribes to every source at once and passes items on as they arrive, from whichever source has one. The output order is arrival order. It completes when all sources have completed, and by default the first error from any source ends it and cancels the rest.

`Flux.concat(a, b)` subscribes to `b` only after `a` has completed. The output is all of `a`, then all of `b`. That makes it the right tool when the second source must not start early: settled entries before pending ones, cached rows before fresh ones, the first page before the rest.

```java
Flux<String> feed = Flux.merge(cardEvents, bankEvents);          // both at once, as they arrive
Flux<String> statement = Flux.concat(settled, pending);          // pending only after settled completes
```

```kotlin
val feed: Flux<String> = Flux.merge(cardEvents, bankEvents)          // both at once, as they arrive
val statement: Flux<String> = Flux.concat(settled, pending)          // pending only after settled completes
```

The trap with `concat` is a first source that never completes. A live Kafka stream of card events never sends `onComplete`, so `Flux.concat(cardEvents, bankEvents)` never subscribes to the bank events at all. If the inputs are endless, you want `merge`.

`Flux.mergeSequential(a, b)` sits in between. It subscribes to all sources at once, like `merge`, but emits them source by source, like `concat`, buffering what arrives early. It is the combining twin of `flatMapSequential` from lesson 3 of this track.

Here are the three on the same inputs: card events at 30, 60 and 90 ms, bank events at 40, 80 and 120 ms.

| Operator | Output | Done at |
|---|---|---|
| `merge` | card-0, bank-0, card-1, bank-1, card-2, bank-2 | 120 ms |
| `concat` | card-0, card-1, card-2, bank-0, bank-1, bank-2 | 210 ms (bank starts at 90) |
| `mergeSequential` | card-0, card-1, card-2, bank-0, bank-1, bank-2 | 120 ms |

`concat` is late because the bank source starts its own 40 ms clock only when it is subscribed, at 90 ms. `mergeSequential` received bank-0 and bank-1 early, held them while the card events went out, and released both the moment the card source completed."""

S3 = """`Flux.combineLatest(a, b, f)` waits until every source has emitted at least once. After that, each new item from any source is combined with the most recent item from each of the others. Its Javadoc warns that elements "can and will be passed to the combinator multiple times", because the latest value stays in use until it is replaced.

That is the shape of a derived value that must track several inputs. A customer's spending limit is stored in EUR, the checkout shows USD, and the EUR/USD rate moves:

```java
Flux<BigDecimal> usdLimit = Flux.combineLatest(limitsInEur, eurUsdRates, BigDecimal::multiply);
Flux<Payment> inUsd = payments.withLatestFrom(eurUsdRates, Payment::convertedAt);   // only payments trigger
```

```kotlin
val usdLimit: Flux<BigDecimal> = Flux.combineLatest(limitsInEur, eurUsdRates) { limit, rate -> limit.multiply(rate) }
val inUsd: Flux<Payment> = payments.withLatestFrom(eurUsdRates) { p, rate -> p.convertedAt(rate) }   // only payments trigger
```

Compare it with `zip` on the same timeline. The limit is 1000 at 0 ms and 2000 at 300 ms. The rate is 1.10 at 100 ms, 1.20 at 200 ms and 1.15 at 400 ms.

| Operator | Output |
|---|---|
| `zip` | 1100, 2400 |
| `combineLatest` | 1100, 1200, 2400, 2300 |

`zip` pairs the second limit with the second rate, so 2000 is multiplied by 1.20 even though 1.15 is the current rate by the end, and the rate change at 200 ms is never shown. `combineLatest` shows every state the inputs pass through.

Two details. `combineLatest` stays silent until every source has emitted once, so an input that might never emit needs a starting value (`rates.startWith(defaultRate)`). And when only one side should trigger output, use `withLatestFrom` from the second line above: each payment is converted with the rate that is current when the payment arrives, and a rate change on its own emits nothing."""

S4 = """Most combining questions come down to this table:

| You want | Use |
|---|---|
| One result from several independent calls | `Mono.zip`, with `switchIfEmpty` or `defaultIfEmpty` on each source |
| Items from several streams, as they arrive | `Flux.merge` |
| One stream after another, the next one started late | `Flux.concat` |
| Several streams started together, output stream by stream | `Flux.mergeSequential` |
| Item-by-item pairs | `Flux.zip` |
| A value recomputed from the latest of every input | `Flux.combineLatest` |
| Each item of one stream, enriched with the latest of another | `withLatestFrom` |
| Wait for several side effects that return `Mono<Void>` | `Mono.when` |
| The first of several sources to produce a value | `Mono.firstWithValue` |

`Mono.when(a, b)` exists because `Mono.zip` and `Mono<Void>` don't mix: a `Mono<Void>` always completes empty, so zipping it completes the whole zip empty. `Mono.when(ledger.write(a), audit.write(b)).then(Mono.just(receipt))` waits for both writes and then carries on.

`Mono.firstWithValue(providerA.rate(ccy), providerB.rate(ccy))` subscribes to both FX providers and takes the first rate that arrives, cancelling the slower call. Empty sources are skipped. That is the hedged-request pattern: it trades extra load for lower tail latency, so keep it for calls that are cheap for the other side.

Every combinator in the table fails fast: the first error cancels the other sources. Each has a `DelayError` variant (`Mono.zipDelayError`, `Flux.mergeDelayError`, `Flux.concatDelayError`) that lets the other sources finish and reports the error at the end. Use those when partial work is still useful, such as a batch job that should process every file before reporting the bad one. The `DelayError` versions treat empty differently too: `Mono.zipDelayError` waits for the other sources to finish before it completes empty, instead of cancelling them.

If a combinator surprises you, check two things: when does it subscribe to each source (all at once, or one after another), and what does it do when one source completes early or empty. Those two answers explain every row of the table.

Quick check: `Mono.zip(ledger.write(entry), fx.rate("EURUSD"))`, where the write is a `Mono<Void>` that completes after 20 ms and the rate takes 100 ms. What does the zip emit, when, and what happens to the rate call? (It completes empty at about 20 ms, because the write completed with no value, and it cancels the rate call that is still in flight. `ledger.write(entry).then(fx.rate("EURUSD"))` gives you the rate after the write.)"""

X0, PX = 150, 2.0
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 300" role="img" aria-label="Marble diagram. Card events at 30, 60, 90 ms and bank events at 40, 80, 120 ms. '
       'merge interleaves them by time; concat emits the cards, then starts bank at 90 ms; mergeSequential emits cards, then the buffered bank events.">')
for ms in range(0, 250, 50):
    SVG += f'<line class="ln-d" x1="{x(ms)}" y1="38" x2="{x(ms)}" y2="285"/>'
    SVG += f'<text class="t-s t-m" x="{x(ms)}" y="28" text-anchor="middle">{ms}</text>'
SVG += '<text class="t-s t-m" x="650" y="28" text-anchor="middle">ms</text>'
lanes = [
    ("card", 62, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a")]),
    ("bank", 106, [(40, "b0", "b"), (80, "b1", "b"), (120, "b2", "b")]),
    ("merge", 168, [(30, "c0", "a"), (40, "b0", "b"), (60, "c1", "a"), (80, "b1", "b"), (90, "c2", "a"), (120, "b2", "b")]),
    ("concat", 216, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a"), (130, "b0", "b"), (170, "b1", "b"), (210, "b2", "b")]),
    ("mergeSequential", 264, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a"), (100, "b0", "b"), (110, "b1", "b"), (120, "b2", "b")]),
]
for name, y, marbles in lanes:
    SVG += f'<text class="t t-code" x="16" y="{y + 5}">{name}</text>'
    SVG += f'<line class="ln" x1="{X0}" y1="{y}" x2="640" y2="{y}" marker-end="url(#arr)"/>'
    for ms, label, c in marbles:
        SVG += f'<circle class="box-{c}" cx="{x(ms)}" cy="{y}" r="9.5"/><text class="t-s" x="{x(ms)}" y="{y + 4}" text-anchor="middle">{label}</text>'
SVG += '<line class="ln-d" x1="20" y1="136" x2="660" y2="136"/>'
SVG += '</svg>'

W0K = '''fun quote(m: String, c: String): Mono<Quote> =
    Mono.zip(fx.rate("EURUSD"), fees.forMerchant(m), limits.forCustomer(c))
        .map { t -> Quote(t.t1, t.t2, t.t3) }'''
W2K = '''fun quote(m: String, c: String): Mono<Quote> =
    Mono.zip(
        fx.rate("EURUSD").switchIfEmpty(missing("fx rate")),     // 1. empty becomes an error
        fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),     // 2. or a sensible default
        limits.forCustomer(c).switchIfEmpty(missing("limit")))
        .map { t -> Quote(t.t1, t.t2, t.t3) }                    // 3. only reached with all three

private fun <T : Any> missing(what: String): Mono<T> =
    Mono.error { IllegalStateException("missing $what") }'''
W3K = '''StepVerifier.create(checkout.quote("m-1", "no-limit-customer"))
    .expectErrorMessage("missing limit")     // 4. the case that used to complete empty
    .verify(Duration.ofSeconds(1))'''
DK = '''fun quote(fxRate: Mono<BigDecimal>, fee: Mono<BigDecimal>, limit: Mono<BigDecimal>): Mono<Quote> =
    Mono.zip(
        fxRate.switchIfEmpty(missing("fx rate")),
        fee.switchIfEmpty(missing("fee")),
        limit.switchIfEmpty(missing("limit")))
        .map { t -> Quote(t.t1, t.t2, t.t3) }

private fun <T : Any> missing(what: String): Mono<T> =
    Mono.error { IllegalStateException("missing $what") }'''
CJ = '''// three calls at once; ready when the slowest one is
Mono<Quote> quote = Mono.zip(
                fx.rate("EURUSD").switchIfEmpty(missing("fx rate")),
                fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),
                limits.forCustomer(c).switchIfEmpty(missing("limit")))
        .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));

// three side effects that return Mono<Void>: zip would complete empty
Mono<Receipt> done = Mono.when(ledger.write(entry), audit.write(entry), kafka.send(event))
        .then(Mono.just(receipt));'''
CK = '''// three calls at once; ready when the slowest one is
val quote: Mono<Quote> = Mono.zip(
        fx.rate("EURUSD").switchIfEmpty(missing("fx rate")),
        fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),
        limits.forCustomer(c).switchIfEmpty(missing("limit")))
    .map { t -> Quote(t.t1, t.t2, t.t3) }

// `when` is a Kotlin keyword, so the method name needs backticks
val done: Mono<Receipt> = Mono.`when`(ledger.write(entry), audit.write(entry), kafka.send(event))
    .then(Mono.just(receipt))'''

L = {
 "id": "rx-04",
 "title": "Combining streams: zip, merge, concat, combineLatest",
 "minutes": 35,
 "goal": "By the end you can fan out independent calls with `Mono.zip` without losing empty results, and choose between `merge`, `concat`, `zip` and `combineLatest` from when each source is subscribed and when output is produced.",
 "warmup": {
  "q": "A checkout runs `Mono.zip(fxRate, fee, limit)`. The FX rate and the fee arrive, but this customer has no limit configured, so `limit` completes empty. What does the zip do?",
  "options": [
   "It fails with `NoSuchElementException`",
   "It emits a tuple with `null` in the third slot",
   "It completes empty, with no value and no error, and cancels the other calls",
   "It waits forever for the limit"
  ],
  "answer": 2,
  "why": "`Mono.zip` needs one value from every source. When one completes empty there is nothing to combine, so the zip completes empty right away and cancels the others. Reactive Streams forbids `null` items, so a tuple with a null slot can't happen. The silent empty result is the trap this lesson fixes."
 },
 "sections": [
  {
   "h": "Pairing by position: zip and Mono.zip",
   "body": S1,
   "try": {
    "title": "Watch a quote disappear",
    "minutes": 4,
    "steps": [
     "`ZipDemo` zips two Fluxes of different lengths, then zips three Monos where the limit is empty, then does it again with `switchIfEmpty` on the limit.",
     "Predict each line, including whether the slow FX call finishes or is cancelled.",
     "Run it. Then change the empty limit to `Mono.just(\"500\")` and predict how long the zip takes."
    ],
    "code": code("ZipDemo"),
    "expect": "`Flux.zip: [[1,a], [2,b]]`. The `Mono.zip` prints `fx rate call cancelled` and `Mono.zip result: null`: `doOnSuccess` received no value because the zip completed empty. The `switchIfEmpty` version cancels the FX call again and prints `with switchIfEmpty: missing limit`, so now the failure is visible. With a real limit the zip emits a tuple of all three after about 200 ms, the time of the slowest call."
   },
   "refs": [{"title": "Mono Javadoc source, reactor-core 3.8.x (zip, zipDelayError, when, firstWithValue)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Mono.java", "kind": "docs"}]
  },
  {
   "h": "Interleave or take turns: merge and concat",
   "body": S2,
   "figure": {"svg": SVG, "caption": "The same two sources through three combinators. concat starts the bank source late; mergeSequential starts it early, holds b0 and b1 back, and releases them when the card source completes at 90 ms."},
   "try": {
    "title": "Three ways to join two feeds",
    "minutes": 4,
    "steps": [
     "`MergeConcatDemo` builds card events every 30 ms and bank events every 40 ms, three of each, and prints when each source is subscribed.",
     "For each combinator, predict when the bank source is subscribed, the output order and the total time.",
     "Run it. Then remove `.take(3)` from `card()` and predict what `concat` does. (Put it back afterwards; that run never ends, so stop it with Ctrl+C.)"
    ],
    "code": code("MergeConcatDemo"),
    "expect": "`merge` subscribes to both at once and interleaves: `card-0, bank-0, card-1, bank-1, card-2, bank-2`, done at about 120 to 140 ms. `concat` subscribes to bank only at about 90 ms and finishes at about 210 ms. `mergeSequential` subscribes to both at once, emits cards then banks, and finishes at about 120 to 140 ms, like merge. Timings drift by a few milliseconds, more on a busy machine. With an endless card source, `concat` prints card events forever and never subscribes to bank."
   }
  },
  {
   "h": "Recompute on every change: combineLatest",
   "body": S3,
   "try": {
    "title": "zip versus combineLatest",
    "minutes": 3,
    "steps": [
     "`CombineLatestDemo` multiplies a EUR limit by a EUR/USD rate with `zip` and with `combineLatest`, on the timeline from the section.",
     "Write down both outputs before you run it.",
     "Run it. Then swap `combineLatest` for `limits().withLatestFrom(rates(), ...)` (keep the multiply) and predict the output."
    ],
    "code": code("CombineLatestDemo"),
    "expect": "`zip: [1100.00, 2400.00]` and `combineLatest: [1100.00, 1200.00, 2400.00, 2300.00]`. With `withLatestFrom`, only the limits trigger: the first limit arrives at 0 ms before any rate exists, so it is dropped, and the second limit (300 ms) uses the latest rate 1.20, giving `[2400.00]`."
   }
  },
  {
   "h": "Choosing a combinator, and what errors do",
   "body": S4,
   "refs": [{"title": "Flux Javadoc source, reactor-core 3.8.x (merge, concat, mergeSequential, combineLatest, zip)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}]
  }
 ],
 "analogy": "Think of four ways to serve a table. `merge` brings each dish out the moment it is ready, from any cook. `concat` serves all the starters before the kitchen even begins the mains. `zip` waits until it has one plate from each of three cooks and carries them out together, and if one cook has nothing to make, no tray goes out at all. `combineLatest` is the drinks board above the bar: whenever any price changes, the whole board is redrawn with the newest prices. The analogy breaks at empty: a real waiter would tell you the kitchen is out of something, but `Mono.zip` just quietly brings nothing.",
 "in_your_world": "A checkout or authorization service fans out constantly: FX rate, merchant fees, customer limits, a fraud score, all independent. `Mono.zip` keeps that fan-out at the speed of the slowest call, and the empty rule decides whether a misconfigured merchant becomes a clear error or a silent empty response. An operations dashboard that shows card events and bank callbacks in one feed is `merge`. A statement that lists settled entries before running the expensive pending query is `concat`. An exposure figure that must follow both the position and the FX rate is `combineLatest`.",
 "mistake": "The most common mistake is using `Mono.zip` without deciding what an empty source means. It works in every test that stubs all calls with values. In production one lookup returns nothing (a merchant without a fee schedule, a customer without a limit), and the whole result completes empty with no error and no log line. Put `switchIfEmpty(Mono.error(...))` or `defaultIfEmpty(...)` on each source that can be empty, and add a test for the empty case.",
 "compare": {
  "title": "Fan-out with Mono.zip and Mono.when in Java and Kotlin",
  "java": {"title": "Checkout.java", "src": CJ},
  "kotlin": {"title": "Checkout.kt", "src": CK},
  "note": "The Reactor calls are the same. In Kotlin, tuple getters read as properties (`t.t1`), and core Reactor has no destructuring for tuples. `when` is a keyword in Kotlin, so `Mono.when` has to be written with backticks. Kotlin's own fan-out looks different: inside `coroutineScope { }` you start each call with `async { }` and then `await()` them, and the Reactor bridge `awaitSingleOrNull()` turns an empty `Mono` into `null`, which the compiler then forces you to handle. That makes the empty case hard to forget, while `Mono.zip` lets you forget it. The coroutines track covers `async`."
 },
 "worked": {
  "title": "Make a checkout quote fail loudly instead of disappearing",
  "steps": [
   {"say": "The quote endpoint fans out three lookups. It passed every test, and support reports that some merchants see an empty checkout page.",
    "code": "Mono<Quote> quote(String m, String c) {\n    return Mono.zip(fx.rate(\"EURUSD\"), fees.forMerchant(m), limits.forCustomer(c))\n            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));\n}", "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "New merchants have no fee schedule yet, so `fees.forMerchant(m)` completes empty. `Mono.zip` then completes empty and cancels the other two calls. The `map` never runs, the controller has nothing to render, and no error is logged. Decide per source: a missing fee schedule means \"no fee\", a missing FX rate or limit is a real error.", "code": "", "lang": ""},
   {"say": "Encode those decisions on each source, before the zip.",
    "code": "Mono<Quote> quote(String m, String c) {\n    return Mono.zip(\n                    fx.rate(\"EURUSD\").switchIfEmpty(missing(\"fx rate\")),    // 1. empty becomes an error\n                    fees.forMerchant(m).defaultIfEmpty(BigDecimal.ZERO),    // 2. or a sensible default\n                    limits.forCustomer(c).switchIfEmpty(missing(\"limit\")))\n            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));        // 3. only reached with all three\n}\n\nprivate static <T> Mono<T> missing(String what) {\n    return Mono.error(() -> new IllegalStateException(\"missing \" + what));\n}", "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Pin the behaviour with a test for the empty case, the one the original tests never had.",
    "code": "StepVerifier.create(checkout.quote(\"m-1\", \"no-limit-customer\"))\n        .expectErrorMessage(\"missing limit\")     // 4. the case that used to complete empty\n        .verify(Duration.ofSeconds(1));", "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Four combinators for a checkout page",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Checkout.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l04.*'",
  "steps": [
   "Read the Javadoc on the four methods in `Checkout`. For each one, decide the combinator before writing code: when must each source be subscribed, and when should output appear?",
   "`quote`: run the three lookups at once, build a `Quote`, and turn an empty lookup into `IllegalStateException(\"missing <name>\")`.",
   "`activityFeed`: card and bank events in the order they happen.",
   "`statement`: settled entries, then pending ones, without subscribing to pending early. The test checks this with a `PublisherProbe`.",
   "`limitInUsd`: a new value whenever either the limit or the rate changes. Run the tests until all five pass."
  ],
  "hints": [
   "If the empty-quote test says `expected: onError(); actual: onComplete()`, you zipped the sources as they are. Add `switchIfEmpty(Mono.error(...))` to each one.",
   "`Mono.error(() -> new IllegalStateException(...))` with a supplier builds the exception lazily, only if the source really is empty.",
   "If `limitInUsd` emits `1100` and `2400` but not `1200`, you used `zip`: it waits for a new item from both sides before emitting."
  ],
  "done_when": "All five tests in `CheckoutTest` pass."
 },
 "drill": {
  "title": "Write the safe fan-out from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Mono<Quote> quote(Mono<BigDecimal> fxRate, Mono<BigDecimal> fee, Mono<BigDecimal> limit)` so that all three run at once, and any empty source fails with `IllegalStateException(\"missing ...\")` naming it. Then compare.",
  "answer": {"lang": "java", "src": "Mono<Quote> quote(Mono<BigDecimal> fxRate, Mono<BigDecimal> fee, Mono<BigDecimal> limit) {\n    return Mono.zip(\n                    fxRate.switchIfEmpty(missing(\"fx rate\")),\n                    fee.switchIfEmpty(missing(\"fee\")),\n                    limit.switchIfEmpty(missing(\"limit\")))\n            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));\n}\n\nstatic <T> Mono<T> missing(String what) {\n    return Mono.error(() -> new IllegalStateException(\"missing \" + what));\n}",
             "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`Mono.zip` subscribes to all sources at once, so a fan-out takes as long as its slowest call.",
  "If any zipped source completes empty, the zip completes empty and cancels the others. Say what empty means with `switchIfEmpty` or `defaultIfEmpty`.",
  "`merge` subscribes to everything at once and emits in arrival order; `concat` subscribes to the next source only after the previous one completes.",
  "`concat` behind an endless source never reaches the second source. Use `merge` for live feeds.",
  "`combineLatest` re-emits whenever any input changes, using the latest of the others. `zip` pairs strictly by position.",
  "Combinators fail fast on the first error. The `DelayError` variants let the other sources finish first."
 ],
 "quiz": [
  {"q": "`Mono.zip(fraudScore, fxRate)`: the fraud call fails after 50 ms; the FX call would take 2 seconds. What happens?",
   "options": ["The zip waits 2 seconds, then fails", "The zip fails at about 50 ms and cancels the FX call", "The zip emits the FX rate with a null fraud score", "The zip retries the fraud call"],
   "answer": 1,
   "why": "Combinators fail fast: the first error ends the zip and cancels the other sources. Waiting for the others is what `Mono.zipDelayError` does. Nothing is retried unless you add `retry` (lesson 5 of this track)."},
  {"q": "A statement must show settled entries, then pending ones. The pending query is expensive and must not start until the settled list is complete. Which line fits?",
   "options": ["`Flux.merge(settled, pending)`", "`Flux.mergeSequential(settled, pending)`", "`Flux.concat(settled, pending)`", "`Flux.zip(settled, pending)`"],
   "answer": 2,
   "why": "`concat` subscribes to `pending` only after `settled` completes. `mergeSequential` produces the same output order but subscribes to both at once, so the expensive query starts early. `merge` interleaves, and `zip` pairs entries that have nothing to do with each other."},
  {"q": "Card events and bank events are two endless Kafka streams. A dashboard uses `Flux.concat(cardEvents, bankEvents)`. What does it show?",
   "options": ["Card and bank events, interleaved", "Only card events, forever", "Nothing until both streams complete", "Bank events first, because they are smaller"],
   "answer": 1,
   "why": "`concat` waits for the first source to complete before subscribing to the second, and an endless stream never completes. The bank stream is never subscribed. `merge` is the combinator for live feeds."},
  {"q": "Limits: 1000 at 0 ms, 2000 at 300 ms. Rates: 1.10 at 100 ms, 1.20 at 200 ms. What does `Flux.combineLatest(limits, rates, BigDecimal::multiply)` emit?",
   "options": ["`1100, 2400`", "`1100, 1200, 2400`", "`1100, 1200`", "`2200, 2400`"],
   "answer": 1,
   "why": "Nothing until both have emitted (100 ms: 1000 x 1.10). Then every change from either side re-emits with the latest of the other: the rate change at 200 ms gives 1200, and the limit change at 300 ms gives 2000 x 1.20 = 2400. `zip` would give only `1100, 2400`."},
  {"q": "From \"CompletableFuture: errors, timeouts and fan-out\": you fan out three calls with `CompletableFuture.allOf(a, b, c)`, and `a` fails at once. When does the `allOf` future complete?",
   "options": ["At once, exceptionally, and it cancels `b` and `c`", "Exceptionally, but only after `b` and `c` have also completed", "Normally, and you have to check each future yourself", "Never, because one future failed"],
   "answer": 1,
   "why": "`allOf` completes when all of the given futures complete, and exceptionally if any of them did. It does not cancel the others. That is the opposite of `Mono.zip`, which fails at the first error and cancels the remaining sources.",
   "from": "exec-07"}
 ],
 "flashcards": [
  {"front": "What does `Mono.zip` do when one of its sources completes empty?", "back": "It completes empty right away (no value, no error) and cancels the other sources."},
  {"front": "How do you make an empty source fail inside a `Mono.zip`?", "back": "Put `.switchIfEmpty(Mono.error(...))` on that source before zipping it (or `defaultIfEmpty(x)` if there is a sensible default)."},
  {"front": "`merge` vs `concat`: when is the second source subscribed?", "back": "`merge`: immediately, together with the first. `concat`: only after the first source completes."},
  {"front": "`Flux.concat(endless, other)`: what happens to `other`?", "back": "It is never subscribed, because `endless` never completes."},
  {"front": "When does `combineLatest` emit?", "back": "Once every source has emitted at least once, and then on every new item from any source, combined with the latest of the others."},
  {"front": "Why can't you `Mono.zip` a `Mono<Void>`?", "back": "It always completes empty, so the zip completes empty. Use `Mono.when(...)` to wait for side effects, then `.then(...)`."}
 ],
 "terms": [
  {"term": "Fan-out", "plain": "Starting several independent calls at once and combining their results."},
  {"term": "zip", "plain": "Combines one item from each source, position by position; completes when any source completes."},
  {"term": "merge", "plain": "Subscribes to all sources at once and emits their items in arrival order."},
  {"term": "concat", "plain": "Subscribes to each source only after the previous one has completed."},
  {"term": "combineLatest", "plain": "Emits a new combination whenever any source emits, using the latest item of each."},
  {"term": "DelayError variant", "plain": "A version of a combinator that lets the other sources finish before reporting an error."}
 ],
 "explain_back": {
  "prompt": "A teammate's quote endpoint uses `Mono.zip` over three lookups and \"sometimes returns nothing, with no error\". Explain in your own words what is happening and how you would fix it so it can't happen silently again.",
  "answer": "`Mono.zip` needs a value from every source. If any of them completes without a value, there is nothing to combine, so the zip completes empty immediately and cancels the other lookups. No error is raised, so nothing is logged, and the endpoint has nothing to return. It happens for whichever lookup can legitimately be empty, for example a merchant without a fee schedule. The fix is to decide what empty means for each lookup and encode it before zipping: `switchIfEmpty(Mono.error(...))` where it is a real error, and `defaultIfEmpty(...)` where there is a sensible default. Then add a test with an empty stub for each lookup, so the case is covered."
 },
 "deeper": {
  "minutes": 8,
  "body": "**Zip in a chain.** `Mono.zipWith(other)` zips two Monos without the static call, and `Mono.zipWhen(value -> otherCall(value))` runs the second call *after* the first and gives you both results: handy when the second lookup needs the first one's answer, such as fetching a merchant and then that merchant's fee schedule. That is sequential on purpose, so it takes the sum of both times.\n\n**Zipping a Flux with an index.** `flux.index()` pairs each item with its position, which is often what people reach for `zip` with `Flux.range` to do.\n\n**Many Monos of unknown count.** For a list of calls, `Mono.zip(listOfMonos, array -> ...)` exists but hands you an `Object[]`. Usually `Flux.fromIterable(ids).flatMap(this::lookup, n).collectList()` is clearer: it caps concurrency, which `Mono.zip` cannot, and it returns results in arrival order (use `flatMapSequential` to keep the input order).\n\n**Merge and backpressure.** `merge` requests from all its sources at once, with a prefetch per source, and interleaves what comes back. merge asks each source for a small prefetch and requests more only as items move downstream, so a fast source can't flood a slow subscriber. Lesson 7 of this track looks at demand in detail.\n\n**`switchIfEmpty` is lazy, the argument isn't.** `switchIfEmpty(Mono.error(new IllegalStateException(...)))` builds the exception object on every call, even when the source has a value. That is cheap but wasteful, and the stack trace points at assembly. The supplier form `Mono.error(() -> new IllegalStateException(...))` builds it only when needed."
 },
 "sources": [
  {"title": "Mono Javadoc source, reactor-core 3.8.x", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Mono.java"},
  {"title": "Flux Javadoc source, reactor-core 3.8.x", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java"},
  {"title": "Reactor reference: Testing (StepVerifier, TestPublisher, PublisherProbe) (source)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/docs/modules/ROOT/pages/testing.adoc"},
  {"title": "CompletableFuture.allOf (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html"}
 ]
}
out = ROOT / "content/lessons/rx-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
