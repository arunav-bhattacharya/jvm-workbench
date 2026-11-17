import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l04"
PK = "kotlin/workbench/reactive/l04"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l04."


def code(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """Picture the packing table at the end of the bakery, where two belts arrive. One brings loaves from the oven. The other brings jars of jam from the jam kitchen. The packer can work in four ways. She can box whatever arrives first, from either belt. She can finish all the loaves before she looks at the jam. She can make gift boxes, one loaf and one jar in each. Or she can keep the price board on the wall up to date, whenever either price changes.

Reactor has an operator for each of those four, and they differ in two things: when each belt is switched on, and when something comes out. The trap is the gift box. When one belt arrives empty, Reactor's gift-box packer ships no box and says nothing at all.

Transforming streams worked on one belt at a time. In this lesson, we'll join several: `zip` for gift boxes, `merge` and `concat` for mixing and taking turns, and `combineLatest` for the price board. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_ZIP = """Mono<Quote> quote = Mono.zip(prices.forCake(cake), delivery.feeTo(address), tax.rateFor(address))
        .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));"""
K_ZIP = """val quote: Mono<Quote> = Mono.zip(prices.forCake(cake), delivery.feeTo(address), tax.rateFor(address))
    .map { t -> Quote(t.t1, t.t2, t.t3) }"""
J_EMPTY = """Mono<BigDecimal> safeDiscount = discount.defaultIfEmpty(BigDecimal.ZERO);   // empty means "no discount"
Mono<BigDecimal> safePrice = price.switchIfEmpty(
        Mono.error(() -> new IllegalStateException("missing price")));      // empty is an error"""
K_EMPTY = """val safeDiscount = discount.defaultIfEmpty(BigDecimal.ZERO)                  // empty means "no discount"
val safePrice = price.switchIfEmpty(
    Mono.error { IllegalStateException("missing price") })                   // empty is an error"""

S0 = """Every combining operator answers two questions: when does it subscribe to each source, and when does something come out? Here are the four from the opening in those terms. `zip` subscribes to all its sources at once and emits only when it has one item from each. `merge` subscribes to all at once and emits each item as it arrives. `concat` subscribes to the next source only after the previous one has completed. `combineLatest` subscribes to all at once and emits whenever any source changes. We'll take them in that order, starting with the gift boxes.

`Flux.zip(a, b)` waits until every source has emitted one item, combines those items, and repeats. It pairs by position, first with first and second with second, like one loaf and one jar in each gift box. It completes as soon as any source completes, so the extra items of a longer source are left over. `Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b"))` gives `[[1,a], [2,b]]`, and the 3 is never used.

In everyday code you'll use `Mono.zip` far more often, for **fan-out**: starting several independent calls at once and combining their results. The bakery's order page needs three lookups for a cake quote, each from a different part of the program:

""" + pair(J_ZIP, K_ZIP) + """

`Mono.zip` subscribes to all of its sources at once. If the price takes 100 ms, the delivery fee 300 ms and the tax rate 200 ms, the quote is ready after 300 ms, not 600. The result is a **tuple**, a small object that holds one value per source, read with `getT1()`, `getT2()` and so on. There are typed versions for up to eight sources.

If any source fails, the zip fails and cancels the others. That's usually what you want. The surprise is the other ending. The `Mono.zip` Javadoc, Reactor's reference page for the method, says it plainly: an "empty completion of any source will cause other sources to be cancelled and the resulting Mono to immediately ... complete". **No error, no value.**

`ZipDemo`, in the Try it, zips a price, a delivery fee and a discount, for a customer who has no discount. So the discount `Mono` completes empty:

```text
  price lookup cancelled
Mono.zip result: null
```

The price lookup was cancelled, and `doOnSuccess` received `null`, which here means "completed empty". No quote, no error, no complaint. One belt arrived empty, so the quiet packer shipped no box. A web page would show an empty answer, `block()` would return `null`, and the logs would show nothing at all.

This is where the gift-box picture breaks. A real packer with no jam would say "we're out of jam". `Mono.zip` just completes. So decide what "empty" means for each source, and say it in code. Either it has a sensible default, as a missing discount means no discount, or it's a real error, as a cake must have a price:

""" + pair(J_EMPTY, K_EMPTY) + """

The demo runs both, on the discount:

```text
with defaultIfEmpty: [24.00,3.50,0.00]
  price lookup cancelled
with switchIfEmpty: missing discount
```

**Mono.zip turns one empty source into an empty result. Say what empty means on every source.**

One more consequence: a `Mono<Void>` is always empty, so it can never take part in a zip. The last section shows the tool for that.

`zip` waits for one item from each belt. The next two operators either don't wait at all, or wait for a whole belt."""

# ---------------------------------------------------------------- section 1
J_MC = """Flux<String> screen = Flux.merge(counterOrders, webOrders);    // both at once, as they arrive
Flux<String> daySheet = Flux.concat(collected, waiting);       // waiting only after collected completes"""
K_MC = """val screen: Flux<String> = Flux.merge(counterOrders, webOrders)    // both at once, as they arrive
val daySheet: Flux<String> = Flux.concat(collected, waiting)       // waiting only after collected completes"""

S1 = """`Flux.merge(a, b)` subscribes to every source at once and passes items on as they arrive, from whichever source has one. On the bakery line, it's two belts feeding one: loaves join in the order they arrive. It completes when all sources have completed, and by default the first error from any source ends it and cancels the rest.

`Flux.concat(a, b)` subscribes to `b` only after `a` has completed. The output is all of `a`, then all of `b`: the first belt runs until its end-of-day bell rings, and only then is the second switched on. That makes `concat` the right tool when the second source must not start early: orders already collected before the slow search for those still waiting, saved results before fresh ones, the first page before the rest.

The bakery's kitchen has a screen that shows new orders from two places, the shop counter and the website. At closing time it prints a day sheet. Here are both:

""" + pair(J_MC, K_MC) + """

The trap with `concat` is a first source that never completes. A live stream of counter orders never sends `onComplete`, so `Flux.concat(counterOrders, webOrders)` never subscribes to the web orders at all. They wait for a bell that never rings. If the inputs are endless, you want `merge`.

`Flux.mergeSequential(a, b)` sits in between. It subscribes to all its sources at once, like `merge`, but emits them source by source, like `concat`, and buffers what arrives early. It's the combining twin of `flatMapSequential` from the last lesson.

`MergeConcatDemo`, in the Try it, makes counter orders every 30 ms and web orders every 40 ms, three of each, and prints when each source is subscribed. One run on this busy machine:

```text
merge:
  [  8 ms] counter subscribed
  [ 11 ms] web subscribed
  [counter-0, web-0, counter-1, web-1, counter-2, web-2], done at about 130 ms
concat:
  [  0 ms] counter subscribed
  [ 92 ms] web subscribed
  [counter-0, counter-1, counter-2, web-0, web-1, web-2], done at about 210 ms
mergeSequential:
  [  3 ms] counter subscribed
  [  3 ms] web subscribed
  [counter-0, counter-1, counter-2, web-0, web-1, web-2], done at about 120 ms
```

`merge` subscribed to both at once and mixed them by time. `concat` subscribed to the web orders only at 92 ms, when the counter source completed. It finished late, because the web source starts its own 40 ms clock only when it is subscribed. `mergeSequential` gave concat's order at merge's speed. It received web-0 and web-1 early, held them while the counter orders went out, and released both the moment the counter source completed. The figure below draws all three on one clock.

**concat waits for each source to complete. Behind an endless source, the next one never starts.**

`merge` and `concat` pass items through unchanged. Sometimes you want a new value, made from the latest item on each belt."""

X0, PX = 150, 2.0
def x(ms): return X0 + ms * PX
SVG = ('<svg viewBox="0 0 680 300" role="img" aria-label="Marble diagram. Counter orders at 30, 60, 90 ms and web orders at 40, 80, 120 ms. '
       'merge mixes them by time; concat emits the counter orders, then starts the web source at 90 ms; mergeSequential emits the counter orders, then the buffered web orders.">')
for ms in range(0, 250, 50):
    SVG += f'<line class="ln-d" x1="{x(ms)}" y1="38" x2="{x(ms)}" y2="285"/>'
    SVG += f'<text class="t-s t-m" x="{x(ms)}" y="28" text-anchor="middle">{ms}</text>'
SVG += '<text class="t-s t-m" x="650" y="28" text-anchor="middle">ms</text>'
lanes = [
    ("counter", 62, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a")]),
    ("web", 106, [(40, "w0", "b"), (80, "w1", "b"), (120, "w2", "b")]),
    ("merge", 168, [(30, "c0", "a"), (40, "w0", "b"), (60, "c1", "a"), (80, "w1", "b"), (90, "c2", "a"), (120, "w2", "b")]),
    ("concat", 216, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a"), (130, "w0", "b"), (170, "w1", "b"), (210, "w2", "b")]),
    ("mergeSequential", 264, [(30, "c0", "a"), (60, "c1", "a"), (90, "c2", "a"), (100, "w0", "b"), (110, "w1", "b"), (120, "w2", "b")]),
]
for name, y, marbles in lanes:
    SVG += f'<text class="t t-code" x="16" y="{y + 5}">{name}</text>'
    SVG += f'<line class="ln" x1="{X0}" y1="{y}" x2="640" y2="{y}" marker-end="url(#arr)"/>'
    for ms, label, c in marbles:
        SVG += f'<circle class="box-{c}" cx="{x(ms)}" cy="{y}" r="9.5"/><text class="t-s" x="{x(ms)}" y="{y + 4}" text-anchor="middle">{label}</text>'
SVG += '<line class="ln-d" x1="20" y1="136" x2="660" y2="136"/>'
SVG += '</svg>'

# ---------------------------------------------------------------- section 2
J_CL = """Flux<BigDecimal> shown = Flux.combineLatest(weightsInKg, pricesPerKg, BigDecimal::multiply);
Flux<Bill> bills = orders.withLatestFrom(pricesPerKg, Order::billAt);      // only orders trigger"""
K_CL = """val shown: Flux<BigDecimal> = Flux.combineLatest(weightsInKg, pricesPerKg) { w, p -> w.multiply(p) }
val bills: Flux<Bill> = orders.withLatestFrom(pricesPerKg) { o, p -> o.billAt(p) }   // only orders trigger"""

S2 = """`Flux.combineLatest(a, b, f)` waits until every source has emitted at least once. After that, each new item from any source is combined with the most recent item from each of the others. Its Javadoc warns that elements "can and will be passed to the combinator multiple times", because the latest value stays in use until it is replaced.

On the bakery wall, it's the price board. The board shows a cake's price, its weight times the price per kilogram. The customer can change the weight on the order page, the owner can change the price per kilogram, and the board shows a new total whenever either one changes:

""" + pair(J_CL, K_CL) + """

`CombineLatestDemo`, in the Try it, runs `zip` and `combineLatest` on the same timeline. The weight is 1.5 kg at 0 ms and 2.0 kg at 300 ms. The price per kilogram is 20.00 at 100 ms, 22.00 at 200 ms and 21.00 at 400 ms:

```text
zip:           [30.000, 44.000]
combineLatest: [30.000, 33.000, 44.000, 42.000]
```

`zip` paired by position, as gift boxes do: the first weight with the first price, and the second weight with the second price. So 2.0 kg was multiplied by 22.00, though the price had moved to 21.00 by the end, and the change at 200 ms never showed. `combineLatest` showed every state the inputs passed through: 1.5 x 20.00, then 1.5 x 22.00, then 2.0 x 22.00, then 2.0 x 21.00. That's what a price board should do. (The three decimal places come from `BigDecimal`, which keeps every digit when it multiplies a number with one decimal place by a number with two.)

Two details. `combineLatest` stays silent until every source has emitted once, so an input that might never emit needs a starting value, such as `pricesPerKg.startWith(listPrice)`. And when only one side should trigger output, use `withLatestFrom`, from the second line above. Each order is billed at the price that is current when the order arrives, and a price change on its own emits nothing.

**combineLatest shows every change. zip shows only matched pairs.**

We now have four combinators and a few look-alikes. The last section puts them side by side, and looks at what happens when one source fails."""

# ---------------------------------------------------------------- section 3
S3 = """Most combining questions come down to this table:

| You want | Use |
|---|---|
| One result from several independent lookups | `Mono.zip`, with `switchIfEmpty` or `defaultIfEmpty` on each source |
| Items from several streams, as they arrive | `Flux.merge` |
| One stream after another, the next one started late | `Flux.concat` |
| Several streams started together, output stream by stream | `Flux.mergeSequential` |
| Item-by-item pairs | `Flux.zip` |
| A value recomputed from the latest of every input | `Flux.combineLatest` |
| Each item of one stream, with the latest of another | `withLatestFrom` |
| Wait for several jobs that return `Mono<Void>` | `Mono.when` |
| The first of several sources to produce a value | `Mono.firstWithValue` |

`Mono.when(a, b)` exists because `Mono.zip` and `Mono<Void>` don't mix: a `Mono<Void>` always completes empty, so zipping it completes the whole zip empty. `Mono.when(orderBook.save(order), receipts.print(order)).then(Mono.just(ticket))` waits for both jobs to finish, then carries on with the ticket.

`Mono.firstWithValue(millA.flourPrice(), millB.flourPrice())` asks two flour mills for a price, takes the first answer that arrives, and cancels the slower call. Empty sources are skipped. This is called a hedged request. It trades extra work for the mills for a faster answer, so keep it for calls that are cheap for the other side.

Every combinator in the table gives up at the first error: the first failure cancels the other sources. Each has a `DelayError` version, such as `Mono.zipDelayError`, `Flux.mergeDelayError` and `Flux.concatDelayError`, that lets the other sources finish and reports the error at the end. Use those when partial work is still useful, such as a nightly job that should process every file before it reports the bad one. The `DelayError` versions treat empty differently too: `Mono.zipDelayError` waits for the other sources to finish before it completes empty, instead of cancelling them.

**The first error ends every combinator here. Use a DelayError version when the rest is still worth finishing.**

If a combinator surprises you, ask the two questions from the start of this lesson. When does it subscribe to each source? And what does it do when a source completes early or empty? Those two answers explain every row of the table.

Quick check: `Mono.zip(orderBook.save(order), prices.forCake(cake))`, where the save is a `Mono<Void>` that completes after 20 ms and the price takes 100 ms. What does the zip emit, when, and what happens to the price lookup? (It completes empty at about 20 ms, because the save completed with no value, and it cancels the price lookup that is still in flight. A run here printed `null` at 22 ms. `orderBook.save(order).then(prices.forCake(cake))` gives you the price after the save.)"""

# ---------------------------------------------------------------- closing
CLOSING = """We started at a packing table with two belts. `zip` makes gift boxes, and ships nothing when one belt is empty. `merge` boxes whatever comes first, `concat` finishes one belt before it switches on the next, and `combineLatest` keeps the price board current.

Now search your own code for `Mono.zip(` and check each source: what should happen if it completes empty?

Next, we'll look at errors, retries and timeouts. Every combinator here gave up at the first error, because `onError` is a terminal signal. When the icing machine fails once, how do we try again, and how long should we wait before giving up?"""

# ---------------------------------------------------------------- worked, drill, compare
W0J = """Mono<Quote> quote(String cake, String address) {
    return Mono.zip(prices.forCake(cake), delivery.feeTo(address), tax.rateFor(address))
            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));
}"""
W0K = """fun quote(cake: String, address: String): Mono<Quote> =
    Mono.zip(prices.forCake(cake), delivery.feeTo(address), tax.rateFor(address))
        .map { t -> Quote(t.t1, t.t2, t.t3) }"""
W2J = """Mono<Quote> quote(String cake, String address) {
    return Mono.zip(
                    prices.forCake(cake).switchIfEmpty(missing("price")),           // 1. empty becomes an error
                    delivery.feeTo(address).switchIfEmpty(missing("delivery fee")),
                    tax.rateFor(address).switchIfEmpty(missing("tax rate")))
            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));                 // 2. only reached with all three
}

private static <T> Mono<T> missing(String what) {
    return Mono.error(() -> new IllegalStateException("missing " + what));        // 3. built only when needed
}"""
W2K = """fun quote(cake: String, address: String): Mono<Quote> =
    Mono.zip(
        prices.forCake(cake).switchIfEmpty(missing("price")),           // 1. empty becomes an error
        delivery.feeTo(address).switchIfEmpty(missing("delivery fee")),
        tax.rateFor(address).switchIfEmpty(missing("tax rate")))
        .map { t -> Quote(t.t1, t.t2, t.t3) }                          // 2. only reached with all three

private fun <T : Any> missing(what: String): Mono<T> =
    Mono.error { IllegalStateException("missing $what") }              // 3. built only when needed"""
W3J = """StepVerifier.create(orderPage.quote("chocolate", "new-area-7"))
        .expectErrorMessage("missing tax rate")     // 4. the case that used to complete empty
        .verify(Duration.ofSeconds(1));"""
W3K = """StepVerifier.create(orderPage.quote("chocolate", "new-area-7"))
    .expectErrorMessage("missing tax rate")         // 4. the case that used to complete empty
    .verify(Duration.ofSeconds(1))"""
DJ = """Mono<Quote> quote(Mono<BigDecimal> price, Mono<BigDecimal> deliveryFee, Mono<BigDecimal> taxRate) {
    return Mono.zip(
                    price.switchIfEmpty(missing("price")),
                    deliveryFee.switchIfEmpty(missing("delivery fee")),
                    taxRate.switchIfEmpty(missing("tax rate")))
            .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));
}

static <T> Mono<T> missing(String what) {
    return Mono.error(() -> new IllegalStateException("missing " + what));
}"""
DK = """fun quote(price: Mono<BigDecimal>, deliveryFee: Mono<BigDecimal>, taxRate: Mono<BigDecimal>): Mono<Quote> =
    Mono.zip(
        price.switchIfEmpty(missing("price")),
        deliveryFee.switchIfEmpty(missing("delivery fee")),
        taxRate.switchIfEmpty(missing("tax rate")))
        .map { t -> Quote(t.t1, t.t2, t.t3) }

private fun <T : Any> missing(what: String): Mono<T> =
    Mono.error { IllegalStateException("missing $what") }"""
CJ = """// three lookups at once; ready when the slowest one is
Mono<Quote> quote = Mono.zip(
                prices.forCake(cake).switchIfEmpty(missing("price")),
                delivery.feeTo(address).switchIfEmpty(missing("delivery fee")),
                tax.rateFor(address).switchIfEmpty(missing("tax rate")))
        .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));

// three jobs that return Mono<Void>: zip would complete empty
Mono<String> done = Mono.when(orderBook.save(order), receipts.print(order), screen.show(order))
        .then(Mono.just(ticket));"""
CK = """// three lookups at once; ready when the slowest one is
val quote: Mono<Quote> = Mono.zip(
        prices.forCake(cake).switchIfEmpty(missing("price")),
        delivery.feeTo(address).switchIfEmpty(missing("delivery fee")),
        tax.rateFor(address).switchIfEmpty(missing("tax rate")))
    .map { t -> Quote(t.t1, t.t2, t.t3) }

// `when` is a Kotlin keyword, so the method name needs backticks
val done: Mono<String> = Mono.`when`(orderBook.save(order), receipts.print(order), screen.show(order))
    .then(Mono.just(ticket))"""

L = {
 "id": "rx-04",
 "title": "Combining streams: zip, merge, concat, combineLatest",
 "minutes": 35,
 "goal": "By the end you can fan out independent calls with `Mono.zip` without losing empty results, and choose between `merge`, `concat`, `zip` and `combineLatest` from when each source is subscribed and when output is produced.",
 "opening": OPENING,
 "warmup": {
  "q": "The bakery's order page builds a quote with `Mono.zip(price, deliveryFee, discount)`. The price and the delivery fee arrive, but this customer has no discount, so `discount` completes empty. What does the zip do?",
  "options": [
   "It fails with `NoSuchElementException`",
   "It emits a tuple with `null` in the third slot",
   "It completes empty, with no value and no error, and cancels the other calls",
   "It waits forever for the discount"
  ],
  "answer": 2,
  "why": "`Mono.zip` needs one value from every source. When one completes empty, there is nothing to put in that slot, so the zip completes empty right away and cancels the others. Reactive Streams forbids `null` items, so a tuple with a null slot can't happen. The quote quietly disappears, which is the trap this lesson fixes."
 },
 "sections": [
  {
   "h": "Four ways to join two belts, starting with zip, which pairs by position",
   "body": S0,
   "try": {
    "title": "Watch a quote disappear",
    "minutes": 4,
    "steps": [
     "`ZipDemo` zips two Fluxes of different lengths. Then it zips three Monos where the discount is empty, and does it again with `defaultIfEmpty` and with `switchIfEmpty` on the discount.",
     "Predict each line, including whether the slow price lookup finishes or is cancelled.",
     "Run it. Then change the empty discount to `Mono.just(\"2.00\")` and predict how long the first zip takes."
    ],
    "code": code("ZipDemo"),
    "expect": "`Flux.zip: [[1,a], [2,b]]`. The plain `Mono.zip` prints `price lookup cancelled` and `Mono.zip result: null`: `doOnSuccess` got no value, because the zip completed empty. `defaultIfEmpty` gives `[24.00,3.50,0.00]` after about 200 ms, the time of the slowest lookup. `switchIfEmpty` cancels the price lookup again and prints `with switchIfEmpty: missing discount`, so now the problem is visible. With a real discount, every zip gets all three values after about 200 ms. The last one then prints nothing, because it only prints when it catches an error."
   },
   "refs": [{"title": "Mono Javadoc source, reactor-core 3.8.x (zip, zipDelayError, when, firstWithValue)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Mono.java", "kind": "docs"}]
  },
  {
   "h": "Mix or take turns: merge and concat",
   "body": S1,
   "figure": {"svg": SVG, "caption": "The same two sources through three combinators. concat starts the web source late; mergeSequential starts it early, holds w0 and w1 back, and releases them when the counter source completes at 90 ms."},
   "try": {
    "title": "Three ways to join two order feeds",
    "minutes": 4,
    "steps": [
     "`MergeConcatDemo` makes counter orders every 30 ms and web orders every 40 ms, three of each, and prints when each source is subscribed.",
     "For each combinator, predict when the web source is subscribed, the output order and the total time.",
     "Run it. Then, in `main`, comment out the `merge` and `mergeSequential` runs, remove `.take(3)` from `counter()`, and predict what `concat` prints. Stop it with Ctrl+C, and put both back afterwards."
    ],
    "code": code("MergeConcatDemo"),
    "expect": "`merge` subscribes to both at once and mixes them: `counter-0, web-0, counter-1, web-1, counter-2, web-2`, done at about 120 to 140 ms. `concat` subscribes to the web source only at about 90 ms and finishes at about 210 ms. `mergeSequential` subscribes to both at once, emits the counter orders and then the web orders, and finishes at about 120 ms, like merge. Timings drift by a few milliseconds, more on a busy machine. With an endless counter source, `concat` prints `counter subscribed` and then nothing, forever: `web subscribed` never appears."
   }
  },
  {
   "h": "Recompute on every change: combineLatest",
   "body": S2,
   "try": {
    "title": "zip versus combineLatest",
    "minutes": 3,
    "steps": [
     "`CombineLatestDemo` multiplies a cake's weight by the price per kilogram, with `zip` and with `combineLatest`, on the timeline from the section.",
     "Write down both outputs before you run it.",
     "Run it. Then swap `combineLatest` for `weights().withLatestFrom(pricesPerKg(), ...)` (keep the multiply) and predict the output."
    ],
    "code": code("CombineLatestDemo"),
    "expect": "`zip: [30.000, 44.000]` and `combineLatest: [30.000, 33.000, 44.000, 42.000]`. With `withLatestFrom`, only the weights trigger output. The first weight arrives at 0 ms, before any price exists, so it is dropped. The second weight (300 ms) uses the latest price, 22.00, which gives `[44.000]`."
   }
  },
  {
   "h": "Choosing a combinator, and what errors do",
   "body": S3,
   "refs": [{"title": "Flux Javadoc source, reactor-core 3.8.x (merge, concat, mergeSequential, combineLatest, zip)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "Fan-out with Mono.zip and Mono.when in Java and Kotlin",
  "java": {"title": "OrderPage.java", "src": CJ},
  "kotlin": {"title": "OrderPage.kt", "src": CK},
  "note": "The Reactor calls are the same. In Kotlin, tuple getters read as properties (`t.t1`), and core Reactor has no destructuring for tuples. `when` is a keyword in Kotlin, so `Mono.when` has to be written with backticks. Kotlin's own fan-out looks different: inside `coroutineScope { }` you start each call with `async { }` and then `await()` them. The Reactor bridge `awaitSingleOrNull()` turns an empty `Mono` into `null`, which the compiler then makes you handle. That makes the empty case hard to forget, while `Mono.zip` lets you forget it. The coroutines track covers `async`."
 },
 "worked": {
  "title": "Make a cake quote fail loudly instead of disappearing",
  "steps": [
   {"say": "The order page fans out three lookups for a quote. It passed every test, and yet customers in a new delivery area see an empty order page.",
    "code": W0J, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "Nobody has set a tax rate for the new area yet, so `tax.rateFor(address)` completes empty. `Mono.zip` then completes empty and cancels the other two lookups. The `map` never runs, the page has nothing to show, and no error is logged. Decide for each source: here a missing price, delivery fee or tax rate is a real error. A source with a sensible default, such as a discount, would take `defaultIfEmpty` instead.", "code": "", "lang": ""},
   {"say": "Write those decisions on each source, before the zip.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "Pin the behavior with a test for the empty case, the one the original tests never had.",
    "code": W3J, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Four combinators for the bakery's order page",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/OrderPage.java", f"{lab}/main/{P}/Quote.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l04.*'",
  "steps": [
   "Read the Javadoc on the four methods in `OrderPage`. For each one, decide on the combinator before you write code: when must each source be subscribed, and when should output appear?",
   "`quote`: run the three lookups at once, build a `Quote`, and turn an empty lookup into `IllegalStateException(\"missing <name>\")`.",
   "`kitchenScreen`: counter and web orders, in the order they arrive.",
   "`daySheet`: collected orders, then waiting ones, without subscribing to the waiting source early. The test checks this with a `PublisherProbe`, a test helper that records whether anything subscribed to it.",
   "`cakePrice`: a new value whenever either the weight or the price per kilogram changes. Run the tests until all five pass."
  ],
  "hints": [
   "If the empty-quote test says `expected: onError(); actual: onComplete()`, you zipped the sources as they are. Add `switchIfEmpty(Mono.error(...))` to each one.",
   "`Mono.error(() -> new IllegalStateException(...))`, with a supplier, builds the exception only if the source really is empty.",
   "If `cakePrice` emits 30 and 44 but not 33, you used `zip`: it waits for a new item from both sides before it emits."
  ],
  "done_when": "All five tests in `OrderPageTest` pass."
 },
 "drill": {
  "title": "Write the safe fan-out from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Mono<Quote> quote(Mono<BigDecimal> price, Mono<BigDecimal> deliveryFee, Mono<BigDecimal> taxRate)` so that all three run at once, and any empty source fails with an `IllegalStateException(\"missing ...\")` that names it. Then compare.",
  "answer": {"lang": "java", "src": DJ, "alt": {"lang": "kotlin", "src": DK}}
 },
 "recap": [
  "`Mono.zip` subscribes to all its sources at once, so a fan-out takes as long as its slowest call.",
  "If any zipped source completes empty, the zip completes empty and cancels the others. Say what empty means with `switchIfEmpty` or `defaultIfEmpty`.",
  "`merge` subscribes to everything at once and emits in arrival order; `concat` subscribes to the next source only after the previous one completes.",
  "`concat` behind an endless source never reaches the second source. Use `merge` for live feeds.",
  "`combineLatest` emits again whenever any input changes, using the latest of the others. `zip` pairs strictly by position.",
  "The limit: every combinator gives up at the first error and cancels the rest. The `DelayError` versions let the others finish, but none of them can try again."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "`Mono.zip(price, deliveryFee)`: the price lookup fails after 50 ms, and the delivery fee would take 2 seconds. What happens?",
   "options": ["The zip waits 2 seconds, then fails", "The zip fails at about 50 ms and cancels the delivery-fee call", "The zip emits the delivery fee with a null price", "The zip calls the price lookup again"],
   "answer": 1,
   "why": "Combinators give up at the first error: it ends the zip and cancels the other sources. Waiting for the others is what `Mono.zipDelayError` does. Nothing is tried again unless you add `retry` (lesson 5 of this track)."},
  {"q": "The end-of-day sheet must show collected orders, then waiting ones. The search for waiting orders is slow and must not start until the collected list is complete. Which line fits?",
   "options": ["`Flux.merge(collected, waiting)`", "`Flux.mergeSequential(collected, waiting)`", "`Flux.concat(collected, waiting)`", "`Flux.zip(collected, waiting)`"],
   "answer": 2,
   "why": "`concat` subscribes to `waiting` only after `collected` completes. `mergeSequential` gives the same output order but subscribes to both at once, so the slow search starts early. `merge` mixes them, and `zip` pairs orders that have nothing to do with each other."},
  {"q": "Counter orders and web orders are two endless streams. The kitchen screen uses `Flux.concat(counterOrders, webOrders)`. What does it show?",
   "options": ["Only counter orders, forever", "Counter and web orders, mixed by arrival", "Nothing until both streams complete", "Web orders first, because there are fewer of them"],
   "answer": 0,
   "why": "`concat` waits for the first source to complete before it subscribes to the second, and an endless stream never completes. The web stream is never subscribed. `merge` is the combinator for live feeds."},
  {"q": "Weights: 1.5 kg at 0 ms, 2.0 kg at 300 ms. Prices per kilogram: 20.00 at 100 ms, 22.00 at 200 ms. What does `Flux.combineLatest(weights, prices, BigDecimal::multiply)` emit?",
   "options": ["`30, 44`", "`30, 33, 44`", "`30, 33`", "`40, 44`"],
   "answer": 1,
   "why": "Nothing until both have emitted (100 ms: 1.5 x 20.00 = 30). Then every change from either side emits again with the latest of the other: the price change at 200 ms gives 1.5 x 22.00 = 33, and the weight change at 300 ms gives 2.0 x 22.00 = 44. `zip` would give only `30, 44`."},
  {"q": "From \"CompletableFuture: errors, timeouts and fan-out\": you fan out three calls with `CompletableFuture.allOf(a, b, c)`, and `a` fails at once. When does the `allOf` future complete?",
   "options": ["At once, exceptionally, and it cancels `b` and `c`", "Normally, and you have to check each future yourself", "Never, because one future failed", "Exceptionally, but only after `b` and `c` have also completed"],
   "answer": 3,
   "why": "`allOf` completes when all of the given futures complete, and exceptionally if any of them did. It doesn't cancel the others. That's the opposite of `Mono.zip`, which fails at the first error and cancels the remaining sources.",
   "from": "exec-07"}
 ],
 "flashcards": [
  {"front": "What does `Mono.zip` do when one of its sources completes empty?", "back": "It completes empty right away (no value, no error) and cancels the other sources."},
  {"front": "How do you make an empty source fail inside a `Mono.zip`?", "back": "Put `.switchIfEmpty(Mono.error(...))` on that source before zipping it (or `defaultIfEmpty(x)` if there is a sensible default)."},
  {"front": "`merge` vs `concat`: when is the second source subscribed?", "back": "`merge`: at once, together with the first. `concat`: only after the first source completes."},
  {"front": "`Flux.concat(endless, other)`: what happens to `other`?", "back": "It is never subscribed, because `endless` never completes."},
  {"front": "When does `combineLatest` emit?", "back": "Once every source has emitted at least once, and then on every new item from any source, combined with the latest of the others."},
  {"front": "Why can't you `Mono.zip` a `Mono<Void>`?", "back": "It always completes empty, so the zip completes empty. Use `Mono.when(...)` to wait for jobs like that, then `.then(...)`."}
 ],
 "terms": [
  {"term": "Fan-out", "plain": "Starting several independent calls at once and combining their results."},
  {"term": "zip", "plain": "Combines one item from each source, position by position; completes when any source completes."},
  {"term": "merge", "plain": "Subscribes to all sources at once and emits their items in arrival order."},
  {"term": "concat", "plain": "Subscribes to each source only after the previous one has completed."},
  {"term": "combineLatest", "plain": "Emits a new combination whenever any source emits, using the latest item of each."},
  {"term": "DelayError version", "plain": "A version of a combinator that lets the other sources finish before it reports an error."}
 ],
 "explain_back": {
  "prompt": "A teammate's order page uses `Mono.zip` over three lookups, and it \"sometimes shows nothing, with no error\". Explain in your own words what is happening, and how you would fix it so it can't happen silently again.",
  "answer": "`Mono.zip` needs a value from every source. If any of them completes without a value, there is nothing to combine, so the zip completes empty at once and cancels the other lookups. No error is raised, so nothing is logged, and the page has nothing to show. It happens for whichever lookup can be empty, for example a delivery area with no tax rate set up. The fix is to decide what empty means for each lookup and write it down before zipping: `switchIfEmpty(Mono.error(...))` where empty is a real error, and `defaultIfEmpty(...)` where there is a sensible default. Then add a test with an empty stub for each lookup, so the case stays covered."
 },
 "deeper": {
  "minutes": 8,
  "body": "**Zip in a chain.** `mono.zipWith(other)` zips two Monos without the static call. `Mono.zipWhen(value -> otherCall(value))` runs the second call *after* the first and gives you both results. That's handy when the second lookup needs the first one's answer, such as fetching a customer and then that customer's discount. It is one after another on purpose, so it takes the sum of both times.\n\n**Numbering items.** `flux.index()` pairs each item with its position, which is often what people reach for `zip` with `Flux.range` to do.\n\n**Many Monos, number unknown.** For a list of calls, `Mono.zip(listOfMonos, array -> ...)` exists, but it hands you an `Object[]`. Usually `Flux.fromIterable(ids).flatMap(this::lookup, n).collectList()` is clearer: it caps how many calls run at once, which `Mono.zip` cannot, and it returns results in arrival order (use `flatMapSequential` to keep the input order).\n\n**Merge and backpressure.** `merge` asks each source for a small batch ahead (a prefetch) and requests more only as items move downstream, so a fast source can't flood a slow subscriber. Lesson 7 of this track looks at demand in detail.\n\n**`switchIfEmpty` is lazy, its argument isn't.** `switchIfEmpty(Mono.error(new IllegalStateException(...)))` builds the exception object on every call, even when the source has a value. That's cheap but wasteful, and the stack trace points at the place where the chain was built. The supplier form, `Mono.error(() -> new IllegalStateException(...))`, builds it only when it is needed."
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
