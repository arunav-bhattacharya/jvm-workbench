import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/flows/src"
P = "kotlin/workbench/flows/l05"
J = "java/workbench/flows/l05"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}"
jdemo = lambda name: f"{lab}/demo/{J}/{name}"
run = lambda cls, extra="": f"./gradlew :flows:demo -Pmain=workbench.flows.l05.{cls}{extra}"
API = "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/"
RAW = "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt"), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}}


# ---- the figure: the D1 timeline (virtual ms), one row per operator ----
X = lambda t: 165 + t * 0.54          # 0 ms -> 165, 800 ms -> 597
rows = [
    ("flatMapConcat", 70, [0, 300, 600], [(50, "1a"), (200, "1b"), (350, "2a"), (500, "2b"), (650, "3a"), (800, "3b")], [], 800),
    ("flatMapMerge", 160, [0, 100, 200], [(50, "1a"), (150, "2a"), (200, "1b"), (250, "3a"), (300, "2b"), (400, "3b")], [], 400),
    ("flatMapLatest", 250, [0, 100, 200], [(50, "1a"), (150, "2a"), (250, "3a"), (400, "3b")], [(100, "cut 1"), (200, "cut 2")], 400),
]
body = ""
for name, y, outers, inners, cuts, end in rows:
    body += f'<text class="t t-code" x="20" y="{y + 5}">{name}</text>'
    body += f'<line class="ln" x1="{X(0)}" y1="{y}" x2="{X(end) + 6:.0f}" y2="{y}"/>'
    body += f'<text class="t-s t-m" x="{X(end) + 12:.0f}" y="{y + 4}">done {end}</text>'
    for i, t in enumerate(outers):
        body += f'<circle class="box-a" cx="{X(t):.0f}" cy="{y - 18}" r="10"/>'
        body += f'<text class="t-s" x="{X(t):.0f}" y="{y - 14}" text-anchor="middle">{i + 1}</text>'
        body += f'<line class="ln-d" x1="{X(t):.0f}" y1="{y - 8}" x2="{X(t):.0f}" y2="{y}"/>'
    for t, label in inners:
        body += f'<rect class="box-b" x="{X(t) - 13:.0f}" y="{y + 6}" width="26" height="18" rx="4"/>'
        body += f'<text class="t-s" x="{X(t):.0f}" y="{y + 19}" text-anchor="middle">{label}</text>'
    for t, label in cuts:
        body += f'<text class="t-s t-bad" x="{X(t):.0f}" y="{y + 40}" text-anchor="middle">{label}</text>'
body += f'<line class="ln-d" x1="{X(0)}" y1="38" x2="{X(300):.0f}" y2="38"/>'
body += f'<text class="t-s t-m" x="{X(150):.0f}" y="32" text-anchor="middle">outer paused inside emit</text>'
axis = f'<line class="ln" x1="{X(0)}" y1="300" x2="{X(800) + 10:.0f}" y2="300" marker-end="url(#arr)"/>'
for t in (0, 200, 400, 600, 800):
    axis += f'<line class="ln" x1="{X(t):.0f}" y1="296" x2="{X(t):.0f}" y2="304"/>'
    axis += f'<text class="t-s t-m" x="{X(t):.0f}" y="320" text-anchor="middle">{t} ms</text>'
FIG = ('<svg viewBox="0 0 680 335" role="img" aria-label="Virtual-time timeline of three flattening operators. The outer flow tries to emit '
       '1, 2 and 3 a hundred milliseconds apart, and each inner emits part a after 50 ms and part b 150 ms later. flatMapConcat: '
       'the outer is paused inside emit, so 2 comes at 300 and 3 at 600, and it ends at 800. flatMapMerge: outers at 0, 100 and 200, '
       'inner values interleave by completion time, done at 400. flatMapLatest: each new outer value cuts the previous inner, so 1b and '
       '2b never arrive, done at 400.">' + body + axis + '</svg>')

S1 = """Ten merchants are waiting for their fees. The fee service allows 4 concurrent calls, and a lookup takes 100 ms. This code is supposed to fan out 4 at a time. The trace shows one call at a time, 1,000 ms in all:

```kotlin
merchants.flatMapMerge(concurrency = 4) { merchant ->
    val fee = feeService.lookup(merchant)        // a suspend call, 100 ms
    flowOf(fee)
}
```

```java
// Closest Java equivalent: Reactor's flatMap with a blocking call in the mapper
merchants.flatMap(merchant -> {
    Fee fee = feeService.lookupBlocking(merchant);   // 100 ms on the calling thread
    return Mono.just(fee);
}, 4);
```

To see why, build the operator yourself. It takes three parts: a coroutine that reads the outer flow, a semaphore with one permit per lane, and one coroutine per inner flow, all sending into one channel:

```kotlin
fun <T, R> Flow<T>.mergeLanes(lanes: Int, transform: suspend (T) -> Flow<R>): Flow<R> = channelFlow {
    val permits = Semaphore(lanes)
    collect { value ->
        val inner = transform(value)          // runs here, one value at a time
        permits.acquire()                     // wait for a free lane
        launch { try { inner.collect { send(it) } } finally { permits.release() } }
    }
}
```

```java
// Closest Java equivalent: one loop builds each task, a semaphore caps the lanes, one virtual thread per lane
static void mergeLanes(List<String> merchants, int lanes, BlockingQueue<Fee> out) throws InterruptedException {
    Semaphore permits = new Semaphore(lanes);
    for (String m : merchants) {
        Callable<Fee> inner = () -> feeService.lookupBlocking(m);   // built here, one merchant at a time
        permits.acquire();                                         // wait for a free lane
        Thread.ofVirtual().start(() -> {
            try { out.put(inner.call()); } catch (Exception e) { /* omitted */ } finally { permits.release(); }
        });
    }
}
```

Now read the bug again. `transform` runs inside the one coroutine that reads the outer flow, before it even asks for a permit. Whatever you do in the lambda happens one merchant at a time. Only the flow it returns gets a lane of its own. So the slow call has to live inside that flow: `flatMapMerge(4) { m -> flow { emit(feeService.lookup(m)) } }`. With five merchants of 300, 100, 200, 50 and 150 ms and two lanes, that version finishes at 450 ms with 2 in flight. The lambda version takes 800 ms, the same as a plain `map { lookup(it) }`.

The library's `flatMapMerge` is `map(transform).flattenMerge(concurrency)`, and `flattenMerge` is the same shape as `mergeLanes`: a producer coroutine, a `Semaphore(concurrency)`, a `launch` per inner flow, and one output channel of 64 slots. Its KDoc says it "calls transform sequentially". Results come out in completion order: m2, m1, m3, m4, m5. Picture a toll plaza with N booths feeding one merge lane. One dispatcher at the entrance waves cars in, one at a time. If he inspects every car himself, the booths sit empty.

Without a `concurrency` argument you get `DEFAULT_CONCURRENCY`, which is 16, read once from the property `kotlinx.coroutines.flow.defaultConcurrency`. Reactor's `flatMap` defaults to 256. In 1.11.0 `flatMapMerge` is `@ExperimentalCoroutinesApi` and `DEFAULT_CONCURRENCY` is `@FlowPreview`. Without an opt-in you get a compiler warning, not an error. Set the cap from the provider's contract, never from the default.

Check yourself: in the fixed version with two lanes, at what time does the lambda run for m3?"""

S2 = """A merchant search box gets three picks, 100 ms apart. For each pick, a details flow sends part a after 50 ms and part b 150 ms later. With `flatMapConcat`, at what time does the outer flow emit pick 2?

```kotlin
picks().flatMapConcat { n -> details(n) }     // also try flatMapMerge and flatMapLatest
```

```java
// Closest Java equivalent: concatMap (and flatMap, switchMap) on the same Flux timeline
picks().concatMap(n -> details(n));
```

Most people say 100. It is 300, and the whole run takes 800 ms. `flatMapConcat` is `map(transform).flattenConcat()`, and `flattenConcat` is one line: `collect { value -> emitAll(value) }`. No coroutine, no channel. The inner flow runs inside the outer's `emit`, so the outer's code is paused until the inner has finished, and its `delay(100)` only starts after that. Picture a single-lane bridge where the depot worker drives each truck across himself. No new truck gets loaded while one is on the bridge. Put `buffer()` in front, and the outer runs in its own coroutine and loads trucks into a parking lot. The run drops to 600 ms.

Reactor's `concatMap` on the same timeline also finishes at 600 ms. It asks for one item at a time too, but the timers in its source kept running while no request was outstanding. A `flow { }` body can't do that: it is suspended in `emit`. If you want Reactor's timeline in Flow, add the `buffer()`.

`flatMapMerge` gives each pick its own lane. The outer emits at 0, 100 and 200, the inner values interleave by completion time (1-b at 200 comes after 2-a at 150), and the run ends at 400.

`flatMapLatest` is a railway switch that drops the old lane. It is `transformLatest { emitAll(transform(it)) }`, the operator from lesson 4 of this track. Each new pick cancels the inner in flight with `ChildCancelledException` ("Child of the scoped flow was cancelled"), joins it, and starts the next. So 1-b and 2-b never arrive, and the run ends at 400. Reactor's `switchMap` gives the identical timeline. This is the shape for search-as-you-type: a new keystroke makes the old search worthless. Keep the cancelled inner's cleanup short, because the next one waits for it.

The figure shows all three, drawn from the virtual-time output of the Try it.

Check yourself: the outer is `for (n in 1..3) { emit(n); delay(100) }` and each inner is one value after 200 ms. How long does `flatMapConcat` take?"""

S3 = """Checkout prices arrive in USD every 100 ms, starting at 100 ms. The USD to EUR rate arrives at 250 ms (0.92) and at 550 ms (0.95). You want each price in EUR. A teammate writes `prices.zip(rates)`:

```kotlin
prices.zip(rates) { cents, rate -> EurPrice(cents, rate) }       // a zipper
combine(prices, rates) { cents, rate -> EurPrice(cents, rate) }  // a board of latest values
merge(cardEvents, bankEvents)                                     // on-ramps onto one road
```

```java
// Closest Java equivalent: the same three Reactor operators
Flux.zip(prices, rates, EurPrice::new);
Flux.combineLatest(prices, rates, EurPrice::new);
Flux.merge(cardEvents, bankEvents);
```

`zip` gives two results: 1000 at 0.92 at 250 ms, and 1010 at 0.95 at 550 ms. Then it ends. It is a zipper: each price tooth must meet a rate tooth, by index, and it stops at the end of the shorter side. The price flow's `onCompletion` reports `AbortFlowException: Flow was aborted, no more elements needed`. Something else happened too: the second price was emitted at 350 ms, not 200. `zip` collects the receiver (`prices`) in the caller's coroutine with no buffer at all, and only the other flow gets a producer coroutine with a rendezvous channel. So each price `emit` waits until a rate is there to pair with. The slower side sets the pace. Reactor's `zip` produced the same two pairs, but its price feed kept ticking every 100 ms, because Reactor prefetches. Flow has only the two-flow `zip`.

Pairing the n-th price with the n-th rate is the wrong question for money. You want the latest rate. That is `combine`, which keeps a board with one slot per flow. It starts one coroutine per source. Nothing comes out until every slot has a value, and after that every update produces one output. The first result is 1010 at 0.92, at 250 ms: price 1000 was overwritten on the board before any rate existed. Then 1020, 1030 and 1040 at 0.92, then 1040 at 0.95 the moment the new rate lands at 550, then 1050 at 0.95. A source that never emits means no output at all, and `combine` completes when the other sources complete.

`merge` is on-ramps joining one road. Card events every 100 ms and bank events every 70 ms come out in arrival order: bank-0 at 70, card-0 at 100, bank-1 at 140, and so on. The merged flow ends when the last source ends, and one source that fails cancels the others.

Check yourself: what does `combine` emit if the rate flow sends 0.92 at 0 ms, before the first price?"""

S4 = """Put a slow collector behind `combine`. A price feed ticks every 10 ms, ten times, and is combined with one merchant config value. The dashboard that collects the result needs 100 ms per update. What does it see?

```kotlin
combine(ticks, flowOf("cfg")) { i, cfg -> "$i/$cfg" }
    .collect { render(it); delay(100) }        // the dashboard is slow
```

```java
// Closest Java equivalent: combineLatest in front of a subscriber that takes one at a time
Flux.combineLatest(ticks, Flux.just("cfg"), (i, cfg) -> i + "/" + cfg)
    .concatMap(v -> render(v).delayElement(Duration.ofMillis(100)), 1);
```

Flow delivers 1, 3, 5, 7, 9 and 10, at 10, 110, 210, 310, 410 and 510 ms. Reactor's `combineLatest` delivers all ten, at about 110, 210 and so on up to 1,010 ms. And there is a second effect in Flow: the feed itself slowed down. It needed about 330 ms to emit its ten values, not 100.

The mechanism is the board's mailbox. Each source coroutine sends an update into a channel whose capacity equals the number of flows, here 2, and then calls `yield()`. The collecting loop takes updates in batches: it reads until it sees a second update from a source it already updated in this batch, overwriting that source's slot each time, and then calls your transform once for the batch. While the dashboard is busy, updates pile up. 2 is overwritten by 3 before anyone takes a photo of the board. Once the mailbox is full, the feed's next `send` suspends: value 4 waits in `send` from 40 ms. So `combine` backpressures its sources and skips values, both at once. Picture a scoreboard and a slow photographer. Updates that land between two photos blur into the last one, and the mailbox in front of the board holds only as many notes as there are slots, so fast sources queue at the mailbox. Reactor's photographer keeps every board state in a queue and develops them all.

It is not plain conflation either. Pure latest-only would give 1 and then 10. If you care, say which one you want:

| After `combine(...)` | The dashboard sees |
|---|---|
| nothing | 1, 3, 5, 7, 9, 10 and the feed slows |
| `.conflate()` | 1 at 10 ms, then 10 at 110 ms |
| `.buffer(Channel.UNLIMITED)` | all ten, the last at 1,010 ms |

For FX on a dashboard, skipping is fine. For anything you must audit, every combination counts, and an unbounded buffer is a memory bill you must size yourself.

One more thing not to rely on. Two flows with no delays, `combine(flowOf("a0", "a1", "a2"), flowOf("b0", "b1", "b2"))`, give `a0b0, a1b1, a2b2` in Flow and `a2b0, a2b1, a2b2` in Reactor. With synchronous sources, the combinations you get depend on scheduling.

Check yourself: with the dashboard at 100 ms per update, would `buffer(10)` instead of `UNLIMITED` keep all ten?"""

L = {
 "id": "flow-05",
 "title": "Flattening and combining: flatMap, zip and combine",
 "minutes": 35,
 "goal": "By the end you can draw the timeline of flatMapConcat, flatMapMerge and flatMapLatest, put the slow call where flatMapMerge runs it concurrently, and choose between zip, combine and merge for prices and rates, including what combine drops for a slow collector.",
 "warmup": {
  "q": "`merchants.flatMapMerge(concurrency = 4) { m -> val fee = feeService.lookup(m); flowOf(fee) }` runs over 10 merchants. Each lookup suspends for 100 ms. How long does it take?",
  "options": [
   "100 ms: all ten at once",
   "300 ms: three waves of 4, 4 and 2",
   "1,000 ms: one lookup at a time",
   "It doesn't compile: the lambda must not suspend"
  ],
  "answer": 2,
  "why": "`flatMapMerge` calls the lambda sequentially, in the one coroutine that reads the outer flow, before it takes a lane. A lookup inside the lambda therefore runs one merchant at a time. Only the returned flows run concurrently, so `flow { emit(feeService.lookup(m)) }` would give the 300 ms you expected."
 },
 "sections": [
  {
   "h": "Your flatMapMerge lambda runs one value at a time",
   "body": S1,
   "try": {
    "title": "Watch the lanes fill",
    "minutes": 5,
    "steps": [
     "Open `FeeFanOut.kt`. It runs on virtual time. For the first scenario, predict when `lambda called for m3` prints and when `start lookup m3` prints.",
     "Run it. Compare the second scenario's total and `max in flight` with the first.",
     "The third scenario is `mergeLanes`, the hand-made version from this section. Check that its timeline is the same as the library's, line for line.",
     "Run the Reactor twin, `FeeFanOutJava`, in real time. Find the same gotcha there."
    ],
    "code": tryit("FeeFanOut.kt", "FeeFanOutJava.java"),
    "expect": "First scenario: the lambda runs for m1, m2 and m3 at 0 ms, but m3's lookup starts only at 100 ms, when m2 frees a lane. Results arrive m2, m1, m3, m4, m5 and the run ends at 450 ms with 2 in flight. The lambda version ends at 800 ms with 1 in flight. `mergeLanes` matches the first scenario exactly. Reactor gives about 450 ms with `Mono.delay` inside the returned `Mono`, and about 800 ms when the mapper blocks before returning `Mono.just`."
   },
   "refs": [
    {"title": "flatMapMerge (kotlinx.coroutines API)", "url": API + "flat-map-merge.html", "kind": "docs"},
    {"title": "DEFAULT_CONCURRENCY (kotlinx.coroutines API)", "url": API + "-d-e-f-a-u-l-t_-c-o-n-c-u-r-r-e-n-c-y.html", "kind": "docs"}
   ]
  },
  {
   "h": "The outer flow waits in flatMapConcat, and flatMapLatest drops the old lane",
   "body": S2,
   "figure": {"svg": FIG, "caption": "The same outer and inner flows under the three flattening operators, from the virtual-time run in the Try it."},
   "try": {
    "title": "Draw the three timelines",
    "minutes": 4,
    "steps": [
     "Before you run `FlatMapTrio.kt`, sketch the three rows of the figure on paper from the section alone, then cover the figure.",
     "Run it and check your sketch. Then read the fourth block, `buffer()` before `flatMapConcat`.",
     "Run the Reactor twin, `FlatMapTrioJava`. Which of its three timelines differs from Flow's?"
    ],
    "code": tryit("FlatMapTrio.kt", "FlatMapTrioJava.java"),
    "expect": "`flatMapConcat`: outer emits at 0, 300 and 600, done at 800. `flatMapMerge`: outer at 0, 100 and 200, done at 400. `flatMapLatest`: inners 1 and 2 cancelled at 100 and 200 with `ChildCancelledException`, 1-b and 2-b never arrive, done at 400. With `buffer()` in front, the outer emits at 0, 100 and 200 and `flatMapConcat` ends at 600. Reactor's `flatMap` and `switchMap` match Flow, and its `concatMap` ends at about 600 ms, like Flow with the buffer."
   },
   "refs": [
    {"title": "flatMapConcat (kotlinx.coroutines API)", "url": API + "flat-map-concat.html", "kind": "docs"},
    {"title": "flatMapLatest (kotlinx.coroutines API)", "url": API + "flat-map-latest.html", "kind": "docs"}
   ]
  },
  {
   "h": "A zipper for zip, a board of latest values for combine",
   "body": S3,
   "try": {
    "title": "Convert prices two ways",
    "minutes": 4,
    "steps": [
     "Open `FxBoard.kt`. Predict how many EUR prices `zip` produces, and at what time the second price is emitted.",
     "Run it. Then predict the first line `combine` prints, and when.",
     "Read the third block: a rate feed that never emits. Then run the Reactor twin, `FxBoardJava`, and compare when its price feed ticks under `zip`."
    ],
    "code": tryit("FxBoard.kt", "FxBoardJava.java"),
    "expect": "`zip`: `1000@0.92` at 250 and `1010@0.95` at 550, with the second price emitted at 350, and the price flow ending with `AbortFlowException`. `combine`: `1010@0.92` at 250 first, then one line per update, ending with `1050@0.95` at 600. With an empty rate feed, `combine` prints nothing and completes at 600. Reactor's `zip` gives the same two pairs, but its prices keep coming every 100 ms; its `combineLatest` matches Flow's `combine`."
   },
   "refs": [
    {"title": "zip (kotlinx.coroutines API)", "url": API + "zip.html", "kind": "docs"},
    {"title": "combine (kotlinx.coroutines API)", "url": API + "combine.html", "kind": "docs"},
    {"title": "merge (kotlinx.coroutines API)", "url": API + "merge.html", "kind": "docs"}
   ]
  },
  {
   "h": "A slow collector makes combine skip values and slow its sources",
   "body": S4,
   "try": {
    "title": "Photograph a busy board",
    "minutes": 4,
    "steps": [
     "Open `SlowBoard.kt`. Predict which values the slow dashboard sees in the first block, and when the feed emits 4.",
     "Run it. Then read the `conflate()` and `buffer(UNLIMITED)` blocks.",
     "Change `Channel.UNLIMITED` to `10` and run again, then to `3`. Predict each count first.",
     "Run `SlowBoardJava`, the `combineLatest` twin, in real time. Count its updates."
    ],
    "code": tryit("SlowBoard.kt", "SlowBoardJava.java"),
    "expect": "Flow's dashboard sees 1, 3, 5, 7, 9 and 10, at 10, 110, 210, 310, 410 and 510 ms. The feed emits 4 at 40 ms and then waits: 5 comes at 120 and 10 at 330. With `conflate()` it sees 1 at 10 and 10 at 110. With `buffer(UNLIMITED)` it gets all ten, done at 1,010 ms. `buffer(10)` also keeps all ten, since ten values fit in 10 slots plus one in hand, while `buffer(3)` delivers eight (1 to 5, 7, 9, 10): once its slots are full, `combine` has a slow collector again. Reactor's `combineLatest` delivers all ten, about 100 ms apart, the last at about 1,050 ms."
   },
   "refs": [
    {"title": "internal/Combine.kt at tag 1.11.0 (how combine and zip are built)", "url": RAW + "internal/Combine.kt", "kind": "read"}
   ]
  }
 ],
 "analogy": "Think of road traffic. `flatMapConcat` is a single-lane bridge where the depot worker drives every truck across himself, so the depot stops loading while a truck is on the bridge. `flatMapMerge` is a toll plaza: one dispatcher waves cars in one at a time, N booths work in parallel, and cars leave in the order they finish. `flatMapLatest` is a railway switch that sends the old train to a siding the moment a new one comes, and waits for the old one to stop. `zip` is a zipper, tooth for tooth. `combine` is a scoreboard with one slot per source. `merge` is on-ramps joining a highway. The picture breaks at speed: real traffic has no backpressure. On a Flow road, a slow collector at the end makes the cars upstream stop, and for `combine` it also blurs some cars into one.",
 "in_your_world": "Your payment service enriches each authorization with the merchant's fee schedule from a pricing service that allows 4 concurrent calls per client. `flatMapMerge(concurrency = 4) { m -> flow { emit(pricing.lookup(m)) }.catch { emit(defaultFee(m)) } }` respects that contract and keeps one 503 from cancelling the other lookups. The checkout page converts the basket into the customer's currency with `combine(basketTotals, fxRates)`, never `zip`, because the latest rate is what you quote. The merchant search box uses `flatMapLatest` so a stale query can't overwrite a fresh one. And the reconciliation job that merges card-network and bank events uses `merge`, knowing that one feed failing stops both.",
 "mistake": "Putting the slow suspend call in the `flatMapMerge` lambda and returning `flowOf(result)`. It looks concurrent and it compiles without a warning, but the lambda runs in the single coroutine that reads the outer flow, before a lane is taken, so the calls happen one at a time. People make the mistake because Reactor's `flatMap` reads the same way and the code looks like a map with a cap. In both libraries the fix is the same: the slow work goes inside the returned flow or publisher, `flow { emit(lookup(m)) }` in Kotlin, `Mono.fromCallable` or a non-blocking client call in Reactor. If you need one result per item and no concurrency, plain `map { lookup(it) }` is simpler, and the `flatMapMerge` KDoc itself recommends it.",
 "compare": {
  "title": "Flattening and combining in Kotlin Flow and in Reactor",
  "java": {
   "title": "Reactor",
   "src": "Flux<Fee> fees     = merchants.flatMap(m -> pricing.lookup(m), 4);      // default concurrency 256\nFlux<Fee> inOrder  = merchants.concatMap(m -> pricing.lookup(m));      // source keeps its own timers\nFlux<Fee> ordered  = merchants.flatMapSequential(m -> pricing.lookup(m), 4);\nFlux<Hit> hits     = queries.switchMap(q -> search.find(q));\nFlux<Eur> byIndex  = Flux.zip(prices, rates, Eur::of);                  // prefetches both sides\nFlux<Eur> latest   = Flux.combineLatest(prices, rates, Eur::of);       // keeps every combination\nFlux<Evt> events   = Flux.merge(cardEvents, bankEvents);"
  },
  "kotlin": {
   "title": "Kotlin Flow",
   "src": "@OptIn(ExperimentalCoroutinesApi::class)\nfun pipelines() {\n    val fees    = merchants.flatMapMerge(4) { m -> flow { emit(pricing.lookup(m)) } }   // default 16\n    val inOrder = merchants.flatMapConcat { m -> flow { emit(pricing.lookup(m)) } }  // outer paused in emit\n    // no flatMapSequential: see the worked example\n    val hits    = queries.flatMapLatest { q -> search.find(q) }                       // joins the old inner\n    val byIndex = prices.zip(rates) { p, r -> Eur.of(p, r) }                          // receiver unbuffered\n    val latest  = combine(prices, rates) { p, r -> Eur.of(p, r) }                     // may skip when slow\n    val events  = merge(cardEvents, bankEvents)\n}"
  },
  "note": "The operators line up one for one, and the virtual-time demos give the same timelines for `flatMap`/`flatMapMerge` and `switchMap`/`flatMapLatest`. The differences come from how each library moves values. In Flow, a value moves by a suspend call, so whatever is upstream of an `emit` waits for it: `flatMapConcat` pauses the outer's code (800 ms against Reactor's 600 on the same timeline), and `zip` slows its receiver to the other side's pace. Reactor moves values on demand and prefetches, so its sources keep their own timers. The defaults differ too: 16 lanes against 256. And with a slow subscriber, `combineLatest` queues every board state while `combine` skips some and makes its sources wait. Flow has no built-in `flatMapSequential`."
 },
 "worked": {
  "title": "Fan out fee lookups under a provider contract",
  "steps": [
   {"say": "The pricing service allows 4 concurrent calls. Put the call inside the returned flow, so each merchant gets a lane, and set the cap from the contract. 10 lookups of 100 ms finish at 300 ms.",
    "code": "@OptIn(ExperimentalCoroutinesApi::class)\nfun fees(merchants: Flow<String>): Flow<Fee> =\n    merchants.flatMapMerge(concurrency = 4) { m ->     // 1. the lambda only builds the inner flow\n        flow { emit(pricing.lookup(m)) }                // 2. the slow call runs in the lane\n    }",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: flatMap with a cap, the call inside the returned Mono\nFlux<Fee> fees(Flux<String> merchants) {\n    return merchants.flatMap(m -> pricing.lookup(m), 4);   // lookup returns a lazy Mono\n}"},
   {"say": "One merchant's lookup fails with a 503. Catch it inside that merchant's inner flow, so only that lane ends with a default. With m1 = 300, m2 = 100 (fails) and m3 = 200 ms, the output is m2's default at 100, m3 at 200 and m1 at 300.",
    "code": "merchants.flatMapMerge(concurrency = 4) { m ->\n    flow { emit(pricing.lookup(m)) }\n        .catch { e -> if (e is IOException) emit(defaultFee(m)) else throw e }   // 3. per lane\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: handle the error inside each inner Mono\nmerchants.flatMap(m -> pricing.lookup(m)\n        .onErrorResume(IOException.class, e -> Mono.just(defaultFee(m))), 4);"},
   {"say": "Compare a `catch` placed after `flatMapMerge`. The failing lane cancels its siblings first: m1 and m3 end with `JobCancellationException` and the caller sees `IOException: fee service 503 for m2` at 100 ms. A caught error still ends the upstream, so the `catch` can only add a fallback after everything else was lost.",
    "code": "merchants.flatMapMerge(concurrency = 4) { m -> flow { emit(pricing.lookup(m)) } }\n    .catch { e -> emit(defaultFee(\"all\")) }      // too late: the other lanes are already cancelled",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: onErrorResume after flatMap ends the whole stream\nmerchants.flatMap(m -> pricing.lookup(m), 4)\n        .onErrorResume(e -> Mono.just(defaultFee(\"all\")));"},
   {"say": "The ledger wants the fees back in input order. Flow has no `flatMapSequential`. Start each call with `async`, keep up to n of them in flight with a buffer, and await them in order. The `buffer(n - 2)` counts the buffer's slots plus one `Deferred` being awaited and one being created, so n must be at least 2. 20 calls of 100 ms take 1,000 / 700 / 500 / 300 ms for n = 2 / 3 / 4 / 8, all in order.",
    "code": "fun <T, R> Flow<T>.mapConcurrentOrdered(n: Int, f: suspend (T) -> R): Flow<R> = flow {\n    coroutineScope {\n        this@mapConcurrentOrdered\n            .map { value -> async { f(value) } }   // 4. start the call\n            .buffer(n - 2)                          // 5. at most n started and not yet emitted\n            .collect { emit(it.await()) }           // 6. emit in input order\n    }\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "// Closest Java equivalent: Reactor has it built in\nFlux<Fee> ordered = merchants.flatMapSequential(m -> pricing.lookup(m), 4);"}
  ]
 },
 "lab": {
  "title": "Fan out fee lookups and convert prices at the latest rate",
  "minutes": 12,
  "files": [
   "labs/flows/src/main/kotlin/workbench/flows/l05/FanOut.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l05/Prices.kt",
   "labs/flows/src/main/kotlin/workbench/flows/l05/Model.kt"
  ],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l05.*'",
  "steps": [
   "Run the tests once. All 7 fail. The `fees` tests print the evidence: 1,000 ms instead of 300, and 1 lookup in flight instead of 4.",
   "Fix `fees` in `FanOut.kt` without changing the cap. Ask yourself which coroutine runs the lambda.",
   "Write `feesOrDefault`: the same fan-out, but an `IOException` from one merchant's lookup becomes `default(merchant)` for that merchant only. Rethrow anything else.",
   "Write `eurPrices` in `Prices.kt`. Before you run it, use the test's two flows to predict the first EUR price and its time.",
   "Run the tests until all 7 pass."
  ],
  "hints": [
   "In `fees`, the lambda should return `flow { emit(service.lookup(merchant)) }` and do nothing else.",
   "In `feesOrDefault`, a `catch` after `flatMapMerge` is too late: by then the failing lane has cancelled the other lanes. Put it on the inner flow.",
   "`eurPrices` wants the latest of each, not pairs by index. The test that expects six results catches a `zip`.",
   "`flatMapMerge` needs `@OptIn(ExperimentalCoroutinesApi::class)` in 1.11.0. Without it you only get a warning."
  ],
  "done_when": "All 7 tests in `FlatteningTest` pass."
 },
 "drill": {
  "title": "Write a capped fan-out from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `fun <T, R> Flow<T>.mergeLanes(lanes: Int, transform: suspend (T) -> Flow<R>): Flow<R>` with `channelFlow`, a `Semaphore` and `launch`. Then answer: in your version, which line runs one value at a time, and why must the slow call not be in `transform`?",
  "answer": {
   "lang": "kotlin",
   "src": "fun <T, R> Flow<T>.mergeLanes(lanes: Int, transform: suspend (T) -> Flow<R>): Flow<R> = channelFlow {\n    val permits = Semaphore(lanes)\n    collect { value ->                          // 1. one coroutine reads the outer flow\n        val inner = transform(value)            // 2. ONE VALUE AT A TIME, before a permit\n        permits.acquire()                       // 3. wait for a free lane\n        launch {                                // 4. one coroutine per lane\n            try { inner.collect { send(it) } }  //    results go into one shared channel\n            finally { permits.release() }\n        }\n    }\n}\n// transform runs in the reading coroutine, so a slow call there blocks the next value from\n// being read at all. Only the flow it returns is collected inside a lane.",
   "alt": {
    "lang": "java",
    "src": "// Closest Java equivalent: a reading loop, a Semaphore, and a virtual thread per lane\nstatic <T, R> void mergeLanes(Iterable<T> outer, int lanes, Function<T, Callable<R>> transform,\n                              BlockingQueue<R> out) throws InterruptedException {\n    Semaphore permits = new Semaphore(lanes);\n    for (T value : outer) {                       // 1. one thread reads the outer source\n        Callable<R> inner = transform.apply(value); // 2. one value at a time, before a permit\n        permits.acquire();                        // 3. wait for a free lane\n        Thread.ofVirtual().start(() -> {          // 4. one thread per lane\n            try { out.put(inner.call()); }\n            catch (Exception e) { Thread.currentThread().interrupt(); }\n            finally { permits.release(); }\n        });\n    }\n}"
   }
  }
 },
 "recap": [
  "`flatMapMerge` calls your lambda sequentially, in one producer coroutine, before it takes a lane. Only the returned flows run concurrently, so the slow call belongs inside them.",
  "The cap defaults to 16 (`DEFAULT_CONCURRENCY`), against Reactor's 256. Set it from the provider's contract. Results come out in completion order.",
  "`flatMapConcat` runs each inner inside the outer's `emit`, so the outer's own code pauses. `buffer()` in front lets it run ahead, which is Reactor's `concatMap` timeline.",
  "`flatMapLatest` cancels the old inner, joins it and starts the new one. Use it for search-as-you-type, where stale results are worthless.",
  "`zip` pairs by index, slows the receiver to the other side's pace and ends with the shorter flow. `combine` keeps the latest of each and emits once every source has a value. FX conversion is `combine`.",
  "With a slow collector, `combine` skips intermediate values and suspends its sources. Add `conflate()` or `buffer()` to choose; Reactor's `combineLatest` keeps them all."
 ],
 "quiz": [
  {"q": "Which call runs with up to 4 in flight?\n\n```kotlin\nmerchants.flatMapMerge(4) { m ->\n    val rules = rulesCache.load(m)               // suspends 50 ms\n    flow { emit(pricing.lookup(m, rules)) }      // suspends 100 ms\n}\n```",
   "options": ["Both: flatMapMerge makes the whole lambda concurrent", "Only `pricing.lookup`; `rulesCache.load` runs one merchant at a time", "Only `rulesCache.load`; the inner flow is collected later, one at a time", "Neither, because `flow { }` inside a lambda is cold"],
   "answer": 1,
   "why": "The lambda runs in the one coroutine that reads the outer flow, sequentially and before a lane is taken. Only the returned flow gets a lane. So the 50 ms loads add up one after another, while the lookups overlap. Move the load into the inner flow if it should run concurrently too."},
  {"q": "The outer is `flow { for (n in 1..3) { emit(n); delay(100) } }` and each inner is one value after 200 ms. `flatMapConcat` takes 900 ms. How long with `.buffer()` before `flatMapConcat`?",
   "options": ["600 ms", "300 ms", "800 ms", "900 ms: buffer doesn't change a concat"],
   "answer": 0,
   "why": "Without the buffer, each inner runs inside the outer's `emit`, so the outer's `delay(100)` waits for it: 3 x (200 + 100). With the buffer, the outer runs ahead in its own coroutine and the three inners run back to back: 3 x 200 = 600 ms."},
  {"q": "A checkout shows each basket total converted at the latest USD to EUR rate. The rate changes every few minutes; totals change whenever the customer edits the basket. Which operator fits?",
   "options": ["`totals.zip(rates)`", "`merge(totals, rates)`", "`totals.flatMapLatest { rates }`", "`combine(totals, rates)`"],
   "answer": 3,
   "why": "`combine` keeps the latest value of each flow and emits on every update of either, once both have a value. `zip` would pair the n-th total with the n-th rate and stall the totals until a new rate arrives. `merge` doesn't combine values at all. The `flatMapLatest` version restarts the rate flow on every basket edit and emits rates, not converted totals."},
  {"q": "`combine(feed, flowOf(\"cfg\"))` feeds a dashboard that needs 100 ms per update. The feed emits 1 to 10, 10 ms apart. What happens?",
   "options": ["The dashboard sees all ten, 100 ms apart", "The dashboard sees only 1 and 10", "The dashboard sees 1, 3, 5, 7, 9, 10, and the feed itself slows down", "combine fails with an overflow error"],
   "answer": 2,
   "why": "`combine`'s mailbox holds one update per source. While the dashboard is busy, updates in the same batch overwrite each other, and once the mailbox is full the feed's `send` suspends. So it both skips and backpressures. All ten is Reactor's `combineLatest`, or Flow with `buffer(UNLIMITED)`. Only 1 and 10 is `conflate()`."},
  {"q": "From the reactive track: on the same timeline, Reactor's `concatMap` finished at 600 ms and Kotlin's `flatMapConcat` at 800 ms. Why?",
   "options": ["Reactor's concatMap prefetches 32 items", "Flow's outer code is suspended inside `emit` while each inner runs, so its own delays start late; Reactor's source timers kept running", "flatMapConcat runs the inners on Dispatchers.Default", "Flow's flatMapConcat runs two inners at once"],
   "answer": 1,
   "why": "`flatMapConcat` is `collect { emitAll(it) }`: no coroutine and no channel, so the outer's body waits in `emit`. Reactor 3.8's `concatMap` requests one at a time too (no prefetch), but its source's `Mono.delay` timers ran while no request was outstanding. `buffer()` before `flatMapConcat` gives Flow the same 600 ms.",
   "from": "rx-03"}
 ],
 "flashcards": [
  {"front": "In `flatMapMerge`, does the lambda run concurrently?", "back": "No. It runs sequentially in the one coroutine that reads the outer flow, before a lane is taken. Only the flows it returns run concurrently."},
  {"front": "Default concurrency of `flatMapMerge`, and of Reactor's `flatMap`?", "back": "16 (`DEFAULT_CONCURRENCY`, from the property `kotlinx.coroutines.flow.defaultConcurrency`). Reactor: 256."},
  {"front": "What happens to the outer flow while a `flatMapConcat` inner runs?", "back": "Its code is paused inside `emit`: there is no extra coroutine or channel. `buffer()` before `flatMapConcat` lets it run ahead."},
  {"front": "`flatMapLatest` gets a new value while an inner is running. What happens?", "back": "It cancels the inner with `ChildCancelledException`, joins it, then starts the inner for the new value."},
  {"front": "How does `zip` pair values, and when does it end?", "back": "By index. It ends when the shorter flow ends and cancels the other. The receiver side has no buffer, so it waits for the other side."},
  {"front": "When does `combine` emit its first value?", "back": "When every source has emitted at least once. After that, once per update of any source."},
  {"front": "`combine` with a slow collector: what happens to fast updates?", "back": "Some are skipped (overwritten on the board) and the sources are suspended, since the mailbox holds one update per source. Reactor's `combineLatest` delivers them all."}
 ],
 "terms": [
  {"term": "Flattening", "plain": "Turning a flow of flows (one inner flow per outer value) into one flow of values."},
  {"term": "Inner flow", "plain": "The flow your `flatMap*` lambda returns for one outer value."},
  {"term": "Lane", "plain": "One inner flow being collected in its own coroutine. `concurrency` is the number of lanes."},
  {"term": "Completion order", "plain": "Results leave in the order they finish, not the order their inputs arrived."},
  {"term": "zip", "plain": "Pairs the n-th value of one flow with the n-th value of another, and ends with the shorter."},
  {"term": "combine", "plain": "Keeps the latest value of each flow and emits a combination whenever any of them changes."},
  {"term": "merge", "plain": "Interleaves several flows in arrival order and ends when the last one ends."}
 ],
 "explain_back": {
  "prompt": "A teammate's fee fan-out uses `flatMapMerge(concurrency = 8)`, yet the trace shows one pricing call at a time. Explain why, how you'd fix it, and how you'd keep one failing merchant from cancelling the rest. Use the toll plaza picture.",
  "answer": "`flatMapMerge` has one dispatcher at the entrance: a single coroutine reads the merchants and calls the lambda for each, one at a time, before it waves the result into a booth. The booths are the 8 lanes, and only the flow the lambda returns is collected in a booth. The teammate does the pricing call in the lambda itself and returns `flowOf(fee)`, so the dispatcher inspects every car himself and the booths stay empty: one call at a time. The fix is to return `flow { emit(pricing.lookup(m)) }`, so the call runs inside the lane. To keep a 503 for one merchant from taking the others down, put `catch` on that inner flow and emit a default fee there. A `catch` after `flatMapMerge` comes too late, because the failing lane has already cancelled all the other lanes."
 },
 "deeper": {
  "minutes": 10,
  "body": "How far does `flatMapMerge` run ahead of a slow collector? With 500 one-value inners and a collector stuck on its first value, 82 outer values had been pulled. A plausible split (my inference, not measured) is 64 results in the output channel, about 16 inners suspended on a full channel, and a couple in hand. With `.buffer(0)` after it the count was 18, and with `flatMapConcat` it was 1. So budget memory for up to 64 finished results plus `concurrency` inners. A `buffer` or `flowOn` after `flatMapMerge` fuses into the same channel: `flatMapMerge(4) { }.buffer(0)` prints as `ChannelFlowMerge[concurrency=4, capacity=0]`.\n\nEdge cases: `flatMapMerge(1)` returns plain `flattenConcat()`. `flatMapMerge(0)` throws `IllegalArgumentException: Expected positive concurrency level, but had 0` when you build the flow. Setting `-Dkotlinx.coroutines.flow.defaultConcurrency=0` makes the first read of `DEFAULT_CONCURRENCY` throw `ExceptionInInitializerError`, caused by `IllegalStateException: System property 'kotlinx.coroutines.flow.defaultConcurrency' should be in range 1..2147483647, but is '0'`. With `=4`, 40 lookups of 100 ms took 1,000 ms instead of 300.\n\n`flattenConcat()` and `flattenMerge()` are the same operators for a `Flow<Flow<T>>` you already have; `flatMapX(f)` is literally `map(f).flattenX()`.\n\nThe `flatMapMerge` and `flatMapConcat` KDoc both say they are discouraged in regular application flows, because \"suspending operation in map operator will be sufficient and linear transformations are much easier to reason about\". Take that at face value: reach for `flatMapMerge` when you need bounded concurrency, and for `map { suspendCall(it) }` when you don't.\n\n`combineTransform` is `combine` with a `FlowCollector` receiver, so the transform can emit zero or several values per board update. Failure works the same way in `combine` and `merge`: one source that throws cancels the others (they end with `JobCancellationException: Parent job is Cancelling`) and the caller gets the original exception."
 },
 "sources": [
  {"title": "flatMapMerge (kotlinx.coroutines API)", "url": API + "flat-map-merge.html"},
  {"title": "flatMapConcat (kotlinx.coroutines API)", "url": API + "flat-map-concat.html"},
  {"title": "zip (kotlinx.coroutines API)", "url": API + "zip.html"},
  {"title": "combine (kotlinx.coroutines API)", "url": API + "combine.html"},
  {"title": "operators/Merge.kt at tag 1.11.0 (flatMapConcat, flatMapMerge, flatMapLatest)", "url": RAW + "operators/Merge.kt"}
 ]
}
out = ROOT / "content/lessons/flow-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
