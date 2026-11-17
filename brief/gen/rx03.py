import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/reactive/src"
P = "java/workbench/reactive/l03"
PK = "kotlin/workbench/reactive/l03"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :reactive:demo -Pmain=workbench.reactive.l03."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{PK}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{PK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- opening
OPENING = """Back on the bakery line, the belt now has stations along it. A slicer takes each loaf, slices it and puts it back on the belt. A wrapper wraps it. Each station does one quick job per loaf, and the loaves come out in the order they went in.

Cakes are different, because icing takes a while. So the bakery sends its cakes to an icing room, where four decorators work at once. Send in cakes 1, 2 and 3, and they may come back as 2, 3 and 1, in whatever order the decorators finish them.

The trap is that the code for the icing room looks almost exactly like the code for the slicer, and the wrong one compiles. In Mono and Flux, a chain was an order form that ran nothing until someone subscribed. In this lesson, we'll add stations to that form: `map` and `filter` for quick jobs, then `flatMap`, `concatMap`, `flatMapSequential` and `switchMap` for jobs that take time. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_MF = """Flux.range(1, 10)
        .doOnRequest(n -> System.out.println("  oven asked for " + n))
        .filter(loaf -> loaf % 3 == 0)               // only every third loaf has seeds
        .map(loaf -> "sliced loaf-" + loaf)
        .take(2)                                     // we only want two
        .subscribe(s -> System.out.println("got " + s));"""
K_MF = """Flux.range(1, 10)
    .doOnRequest { n -> println("  oven asked for $n") }
    .filter { loaf -> loaf % 3 == 0 }                // only every third loaf has seeds
    .map { loaf -> "sliced loaf-$loaf" }
    .take(2)                                         // we only want two
    .subscribe { s -> println("got $s") }"""
J_BUG = """Flux<Mono<String>> iced = cakes.map(cake -> icing.ice(cake));   // Naive: a belt of unsigned forms"""
K_BUG = """val iced: Flux<Mono<String>> = cakes.map { cake -> icing.ice(cake) }   // Naive: a belt of unsigned forms"""

S0 = """`map` and `filter` are the operators you may know from Java's streams in `java.util.stream`, with one difference: here they run when items arrive, not when you call them.

`map(f)` is the slicer: one item in, one item out, right away, on whatever thread delivered the item. Use it for quick, pure work, which only computes a new value from the item, such as turning a loaf number into a label, or cents into euros. `filter(p)` is the inspector who lifts burnt loaves off the belt: it keeps only the items that pass a test.

`filter` also keeps the slips honest. A loaf it removes doesn't count against the packer's slip, so `filter` asks the source for another one. `MapFilterDemo`, in the Try it, keeps every third loaf, slices it, and takes two:

""" + pair(J_MF, K_MF) + """

`doOnRequest` is an operator that prints each request passing up through it, so we can watch the slip reach the oven:

```text
  oven asked for 2
got sliced loaf-3
got sliced loaf-6
```

`take(2)` wrote one slip for 2, and the oven saw exactly that slip. Yet the oven sent loaves 1 to 6, because `filter` asked for a replacement each time it threw a loaf away.

Now the most common `map` bug. Say the bakery has a slow icing machine, and `icing.ice(cake)` returns a `Mono<String>` that completes when the cake is iced:

""" + pair(J_BUG, K_BUG) + """

The function returns a `Mono`, so `map` gives you a `Flux<Mono<String>>`: a belt that carries order forms instead of cakes. Remember the last lesson: a `Mono` that nobody subscribes to does nothing. So not one cake is iced. The compiler is happy, a test that only counts items is happy, and the icing machine never switches on.

When your function returns a publisher, you need one of the flattening operators in the next sections. The type is your friend here. If you see `Flux<Mono<T>>`, you used `map` where you needed `flatMap`.

Two smaller rules. In Reactor 3.8, a `map` function may not return `null`. In Java the stream fails with `NullPointerException: The mapper [...] returned a null value.`, and in Kotlin the lambda doesn't even compile, thanks to Reactor's JSpecify annotations. Filter first, or use `handle`, which works like a `map` that may emit zero or one item for each input.

And `map` must stay quick and must not block, because it runs on the thread that delivered the item. A slow database call inside `map` holds that thread for every single item. Lesson 6 of this track shows where blocking calls belong.

**`map` is for quick work that returns a value. If your function returns a `Mono`, `map` is the wrong station.**

So what is the right station, when every cake needs a trip to the icing machine?"""

# ---------------------------------------------------------------- section 1
J_FM4 = """Flux<String> iced = cakes.flatMap(cake -> icing.ice(cake), 4);   // at most 4 cakes at the machine"""
K_FM4 = """// the lambda stays inside the parentheses when another argument follows it
val iced: Flux<String> = cakes.flatMap({ cake -> icing.ice(cake) }, 4)   // at most 4 cakes at the machine"""

S1 = """`flatMap(f)` takes a function that returns a publisher, called the **inner** publisher, and does three things with it:

1. For each source item, it calls `f` and subscribes to the inner right away, without waiting for earlier inners to finish.
2. It keeps up to `concurrency` inners subscribed at once. The default is 256.
3. It merges all their items into one output, in the order they arrive.

In the bakery, `flatMap` is the hatch to the icing room. Each cake goes through the hatch as soon as it arrives, several decorators work at once, and iced cakes come back out in whatever order they're finished. That last point is the one to remember: the output order follows finishing time, not input order. Reactor's Javadoc, the reference pages built from its source code, says flatMap "does not necessarily preserve original ordering", and with real calls of different speeds, it almost never does.

Two facts about `flatMap` surprise people. First, **flatMap does not create threads**. This is where the icing-room picture breaks: flatMap hires no decorators. If the inner is synchronous, such as a `Mono.fromCallable` with nothing to move it elsewhere, the inners run one after another on the calling thread. `FlatMapThreadsDemo`, in the Try it, shows both cases:

```text
1. synchronous inners:
  iced cake 1 on main
  iced cake 2 on main
  iced cake 3 on main
2. asynchronous inners (Mono.delay runs on Reactor's parallel scheduler):
  iced cake 3 on parallel-3
  iced cake 2 on parallel-2
  iced cake 1 on parallel-1
```

In part 1, everything ran on `main`, in order. In part 2, each inner was a `Mono.delay`, which waits on a timer and then finishes on one of Reactor's own threads. Cake 3 had the shortest wait, so it came out first. The concurrency came from the inners themselves: a timer, a non-blocking network call, or a blocking call moved to another thread with `subscribeOn` (lesson 6 of this track). flatMap only subscribes to several of them before the first one finishes.

Second, **concurrency is also demand**. `flatMap(f, 4)` writes a first slip for 4 items, then a slip for 1 more each time an inner completes. That makes the concurrency argument a cap on calls in flight:

""" + pair(J_FM4, K_FM4) + """

Part 3 of the demo prints the slips each operator sends to the source:

```text
  flatMap(f)    requests: 256
  flatMap(f, 2) requests: 2 1 1 1 1
  concatMap(f)  requests: 1 1 1 1 1 1
```

Set the concurrency whenever the inner touches something shared. flatMap is generous by default: unless told otherwise, it sends 256 cakes to an icing machine with four nozzles, or 256 queries to a database that allows 20 connections. Pick the number from what the other side allows, not from a feeling.

**flatMap's default is 256 calls at once. Set the concurrency to what the other side can take.**

Each inner also gets a prefetch of 32: if an inner is a `Flux`, flatMap asks it for 32 items at a time. That rarely matters for `Mono` inners. One more behavior to know now: if any inner fails, flatMap cancels the others and the whole stream fails. Lesson 5 of this track shows how to keep an error inside one inner.

So flatMap is fast, and it has no sense of order. Sometimes order is the whole point."""

# ---------------------------------------------------------------- section 2
S2 = """When order matters, you have two choices with very different costs.

`concatMap(f)` is a single decorator who finishes one cake before taking the next. It asks the source for one item, waits for that item's inner to complete, then asks for the next. Output order is input order, and the total time is the sum of all the inner times. In Reactor 3.8, it doesn't fetch ahead from the source at all, which is why the last demo showed its slips of 1.

`flatMapSequential(f)` is the icing room with a clerk at the exit. It subscribes to inners eagerly, like flatMap (concurrency 256, prefetch 32), but the clerk holds back results from later inners until all earlier inners have finished. Output order is input order, and the total time is about the time of the slowest inner.

That speed has two costs. One is memory, since cakes that finish early wait in a buffer. The other is **head-of-line blocking**: one slow cake at the front holds back every cake behind it, even the finished ones.

`OrderingDemo`, in the Try it, runs all three operators on the same input. The source emits 3, 1, 2 at once, and item `i` takes `i x 100 ms`. The figure below draws the result:

```text
flatMap           -> [1, 2, 3] in about 300 ms
concatMap         -> [3, 1, 2] in about 600 ms
flatMapSequential -> [3, 1, 2] in about 300 ms
```

`flatMap` let the fastest item out first. `concatMap` kept the order and added up the times: 300, then 100, then 200. `flatMapSequential` kept the order at flatMap's speed, because items 1 and 2 finished early and waited for 3.

Ordered output isn't the only reason to pick `concatMap`. Pick it when each step must *start* after the previous one has finished. A tall layer cake is the bakery's case. The second layer may only go on after the first has set, because it sits on top, and after a layer collapses, no more layers go on. `flatMapSequential` would report the layers in the right order while placing all four at the same moment, which is exactly what the cake can't take.

Here is a short guide:

| You need | Use |
|---|---|
| Independent calls, any order | `flatMap(f, n)` |
| Output in input order, calls may overlap | `flatMapSequential(f, n)` |
| One at a time, each after the previous | `concatMap(f)` |
| Only the latest item matters | `switchMap(f)` |

**flatMapSequential orders the results, not the work. When each step must wait for the last, use concatMap.**

The last row of the table solves a different problem: work that a newer item makes pointless."""

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
SVG += '<text class="t-s t-m" x="420" y="272" text-anchor="middle">flatMapSequential: 1 and 2 finished early and waited for 3</text>'
SVG += '</svg>'

# ---------------------------------------------------------------- section 3
J_SW = """Flux<String> prices = sizePicks.switchMap(size -> priceService.priceOf(size));"""
K_SW = """val prices: Flux<String> = sizePicks.switchMap { size -> priceService.priceOf(size) }"""

S3 = """`switchMap(f)` is for streams where a new item makes the old work pointless. Each time the source emits, switchMap cancels the inner for the previous item and subscribes to a new one.

Picture a customer on the bakery's website, choosing a cake size from a list. Each pick asks a price service for the price. The customer picks small, then medium 50 ms later, while the price for small is still on its way. With `flatMap`, both prices eventually arrive. If the small one is slower, it arrives last and replaces the medium one on screen, and the customer sees the price of a cake they no longer want. With `switchMap`, the request for the small price is cancelled the moment medium is picked, and its result can never reach the page:

""" + pair(J_SW, K_SW) + """

On the bakery line, it's the customer who keeps changing their mind, and a decorator who bins the half-iced cake each time. `SwitchMapDemo`, in the Try it, does the same with a search box. The customer types `cr`, then `cro` 100 ms later, and each prefix starts a lookup that sends a suggestion every 60 ms:

```text
show cr-match0
  cancelled lookup for cr
show cro-match0
show cro-match1
show cro-match2
all shown: [cr-match0, cro-match0, cro-match1, cro-match2]
```

The `cr` lookup showed one suggestion and was cancelled when `cro` arrived. No stale `cr` suggestion appeared after that.

Cancellation travels upstream through the inner, so a reactive web client can abort the request it was making, and a `Flux.interval` inside stops ticking. Here the bakery picture breaks once more. A decorator who stops icing really stops. A service on another computer may finish its work anyway; cancelling only promises that you stop listening.

A few details. switchMap requests an unbounded amount from its source, so it applies no backpressure upstream: every pick is seen, and older ones are dropped by cancelling. The stream completes when the source has completed and the last inner has completed. Search as you type, "recompute when the settings change" and "show the latest stock level" all have this shape.

**When a newer item makes the older work pointless, switchMap cancels it for you.**

Kotlin's own `Flow` has the same operator under another name: `flatMapLatest`, or `mapLatest` when the block returns a single value. The comparison below shows how the other three operators map onto Flow."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a slicer and an icing room, and they turned out to need different stations. `map` is the slicer: one quick job per item. `flatMap` sends items to the icing room and takes them back in any order. `concatMap` uses one decorator at a time, `flatMapSequential` puts a clerk at the exit, and `switchMap` drops the cake nobody wants any more.

Now search your own code for `flatMap(` with no second argument, and ask how many calls the other side can really take at once.

Next, we'll bring several belts together. When one cake order needs a price, a delivery fee and a tax rate from three places, how do we combine three streams into one?"""

# ---------------------------------------------------------------- compare, worked
CJ = """// any order, at most 4 cakes at the icing machine
Flux<String> iced = cakes.flatMap(cake -> icing.ice(cake), 4);

// one at a time, each after the previous one completes
Flux<String> stacked = layers.concatMap(layer -> stacker.place(layer));

// overlapping calls, output in input order
Flux<String> report = ingredients.flatMapSequential(item -> supplier.stockOf(item), 4);

// latest wins: a new pick cancels the previous price
Flux<String> prices = sizePicks.switchMap(size -> priceService.priceOf(size));"""
CK = """// any order, at most 4 cakes at the icing machine
val iced = cakes.flatMap({ cake -> icing.ice(cake) }, 4)

// one at a time, each after the previous one completes
val stacked = layers.concatMap { layer -> stacker.place(layer) }

// overlapping calls, output in input order
val report = ingredients.flatMapSequential({ item -> supplier.stockOf(item) }, 4)

// latest wins: a new pick cancels the previous price
val prices = sizePicks.switchMap { size -> priceService.priceOf(size) }"""
W0J = """Flux<StockRow> nightlyCheck(Flux<String> ingredients) {
    return ingredients
            .flatMap(item -> supplier.stockOf(item))   // Mono<Stock>, about 120 ms each
            .map(StockRow::from);
}"""
W0K = """fun nightlyCheck(ingredients: Flux<String>): Flux<StockRow> =
    ingredients
        .flatMap { item -> supplier.stockOf(item) }     // Mono<Stock>, about 120 ms each
        .map { StockRow.from(it) }"""
W2J = """return ingredients
        .flatMap(item -> supplier.stockOf(item), 10)   // 1. never more than 10 in flight
        .map(StockRow::from);"""
W2K = """ingredients
    .flatMap({ item -> supplier.stockOf(item) }, 10)    // 1. never more than 10 in flight
    .map { StockRow.from(it) }"""
W3J = """return ingredients
        .flatMapSequential(item -> supplier.stockOf(item), 10)   // 2. same cap, list order
        .map(StockRow::from);"""
W3K = """ingredients
    .flatMapSequential({ item -> supplier.stockOf(item) }, 10)    // 2. same cap, list order
    .map { StockRow.from(it) }"""

L = {
 "id": "rx-03",
 "title": "Transforming streams: map, flatMap, concatMap",
 "minutes": 35,
 "goal": "By the end you can choose between `map`, `flatMap`, `concatMap`, `flatMapSequential` and `switchMap` from what a pipeline needs (order, one at a time, a cap on calls in flight, latest wins), and prove the choice with a virtual-time test.",
 "opening": OPENING,
 "warmup": {
  "q": "Three cakes, numbered 3, 1 and 2, reach the icing station at the same moment. Cake `i` takes `i x 100 ms` to ice, and the station uses `flatMap`. What comes out, and when is the last cake done?",
  "options": [
   "`[3, 1, 2]`, finishing at 600 ms",
   "`[1, 2, 3]`, finishing at 300 ms",
   "`[3, 1, 2]`, finishing at 300 ms",
   "`[1, 2, 3]`, finishing at 600 ms"
  ],
  "answer": 1,
  "why": "flatMap subscribes to all three calls at once and emits each result as it finishes: 1 at 100 ms, 2 at 200 ms, 3 at 300 ms. Keeping the input order at the same speed is `flatMapSequential`; keeping the order by icing one cake at a time is `concatMap`, which takes 600 ms."
 },
 "sections": [
  {
   "h": "Stations that change one item at a time: map and filter",
   "body": S0,
   "try": {
    "title": "Count the slips a filter sends",
    "minutes": 3,
    "steps": [
     "`MapFilterDemo` keeps every third loaf from 1 to 10, slices it, and takes 2. A `doOnRequest` prints what the oven is asked for.",
     "Predict how many requests the oven sees and which loaves print. In Java, predict what the second pipeline does with the `null`; in Kotlin, read the comment that says why that line can't be written.",
     "Run it. Then change `take(2)` to `take(4)` and run it again."
    ],
    "code": demo("MapFilterDemo"),
    "expect": "The oven is asked for 2 once, yet it sends loaves 1 to 6, because `filter` asks for a replacement for each loaf it removes. You get `sliced loaf-3` and `sliced loaf-6`. The Java version's second pipeline prints `made dark bread`, then `error: java.lang.NullPointerException: The mapper [...] returned a null value.`. The Kotlin version uses `handle`, so it prints only `made dark bread`: the compiler caught the `null` case instead. With `take(4)` the oven is asked for 4 and runs to 10, but only three loaves pass the filter, so you get three and the stream completes."
   }
  },
  {
   "h": "flatMap sends many items out at once, and they come back in any order",
   "body": S1,
   "try": {
    "title": "Where does flatMap's concurrency come from?",
    "minutes": 4,
    "steps": [
     "`FlatMapThreadsDemo` runs flatMap with synchronous inners, then with `Mono.delay` inners, and prints the thread for each result. Then it prints the slips flatMap and concatMap send to the source.",
     "Predict the threads and the order in parts 1 and 2. Predict the request numbers in part 3.",
     "Run it. Then change part 3's concurrency from 2 to 3, and predict the new request line."
    ],
    "code": demo("FlatMapThreadsDemo"),
    "expect": "Part 1 runs on `main`, in order: flatMap made no threads. Part 2 prints cake 3 first (100 ms), then 2, then 1, on `parallel-N` threads that belong to `Mono.delay`. Part 3 prints `256` for plain flatMap, `2 1 1 1 1` for concurrency 2, and `1 1 1 1 1 1` for concatMap. With concurrency 3 you get `3 1 1 1`: the first request is the cap, then one more per finished inner."
   },
   "refs": [{"title": "Flux Javadoc source, reactor-core 3.8.x (flatMap, concatMap, flatMapSequential, switchMap)", "url": "https://github.com/reactor/reactor-core/blob/3.8.x/reactor-core/src/main/java/reactor/core/publisher/Flux.java", "kind": "docs"}]
  },
  {
   "h": "Putting the order back: concatMap and flatMapSequential",
   "body": S2,
   "figure": {"svg": SVG, "caption": "The same three calls through three operators. Only flatMapSequential is both ordered and fast, and it pays with a buffer."},
   "try": {
    "title": "Measure the three operators",
    "minutes": 3,
    "steps": [
     "`OrderingDemo` runs the source 3, 1, 2 through all three operators, with real delays.",
     "Write down your prediction for each output and time, then run it.",
     "Change the source to `Flux.just(1, 2, 3)`. Which operator's output changes, and which timing changes?"
    ],
    "code": demo("OrderingDemo"),
    "expect": "`flatMap -> [1, 2, 3]` in about 300 ms, `concatMap -> [3, 1, 2]` in about 600 ms, `flatMapSequential -> [3, 1, 2]` in about 300 ms, as in the figure. With source 1, 2, 3, all three print `[1, 2, 3]`: the input order now matches the finishing order, so flatMap looks ordered. That's why order bugs hide in tests where every fake call takes the same time. concatMap still takes 600 ms, and the other two still take 300 ms."
   }
  },
  {
   "h": "When only the latest matters: switchMap cancels the old work",
   "body": S3,
   "try": {
    "title": "Cancel a stale lookup",
    "minutes": 3,
    "steps": [
     "`SwitchMapDemo` plays a customer typing in the bakery's search box: `cr` at 100 ms, then `cro` at 200 ms. Each prefix starts a lookup that sends a suggestion every 60 ms, three in total.",
     "Predict which suggestions are shown, and when the first lookup is cancelled. Run it.",
     "Replace `switchMap` with `flatMap` and run it again."
    ],
    "code": demo("SwitchMapDemo"),
    "expect": "You see `show cr-match0` (at about 160 ms), then `cancelled lookup for cr` when `cro` arrives at 200 ms, then the three `cro` suggestions: `[cr-match0, cro-match0, cro-match1, cro-match2]`. With flatMap nothing is cancelled, and the two lookups interleave: `[cr-match0, cr-match1, cro-match0, cr-match2, cro-match1, cro-match2]`. A stale `cr` suggestion shows up after the customer has already typed `cro`, which is the race that switchMap prevents."
   },
   "refs": [{"title": "Kotlin docs: Asynchronous Flow (flattening flows)", "url": "https://kotlinlang.org/docs/flow.html", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "The four flattening operators in Java and Kotlin",
  "java": {"title": "BakeryStations.java", "src": CJ},
  "kotlin": {"title": "BakeryStations.kt", "src": CK},
  "note": "Same operators, two syntax details. In Kotlin a lambda can only trail outside the parentheses when it is the last argument, so `flatMap({ ... }, 4)` keeps it inside. And Kotlin lambdas adapt to Reactor's `Function<? super T, Publisher<? extends V>>` parameter without fuss, so the `switchMap` typing problem the lab hints at in Java doesn't arise. The bigger difference is with Kotlin's own streams. In Kotlin's `Flow` the default is one at a time: a `map` whose block suspends waits for each call, so it behaves like `concatMap`. You ask for concurrency with `flatMapMerge(concurrency = 4)`, whose default is 16 rather than Reactor's 256. `flatMapLatest` and `mapLatest` are Flow's `switchMap`, and there is no `flatMapSequential`. In kotlinx.coroutines 1.11 those Flow operators still need `@OptIn(ExperimentalCoroutinesApi::class)`. `FlowOperators.kt` in the demo folder runs the same 3, 1, 2 example with Flow (`-Pmain=workbench.reactive.l03.FlowOperatorsKt`)."
 },
 "worked": {
  "title": "Fix a nightly job that floods the supplier",
  "steps": [
   {"say": "Every night the bakery's program checks the stock of each of its 5,000 ingredients with the supplier's web service. The supplier allows 10 calls at once from each customer. Last night the job got hundreds of answers saying `429 Too Many Requests`, the web's way of saying \"slow down\". Read the pipeline.",
    "code": W0J, "lang": "java", "alt_code": W0K, "alt_lang": "kotlin"},
   {"say": "flatMap with no concurrency argument subscribes to up to 256 inners at once, and its first slip to the source asks for 256. With 5,000 ingredients, the job keeps about 256 calls in flight the whole time. The supplier allows 10.", "code": "", "lang": ""},
   {"say": "Cap the calls in flight at the supplier's limit. By Little's law, which says calls in flight equal calls per second times the time per call, 10 calls at 120 ms each finish at most 10 / 0.12 s, about 83 calls a second. So 5,000 ingredients take about a minute. That's the honest speed this supplier allows.",
    "code": W2J, "lang": "java", "alt_code": W2K, "alt_lang": "kotlin"},
   {"say": "The owner then asks for the report in the same order as the ingredient list, so it lines up with yesterday's. Switching to `concatMap` would cut the speed to one call at a time, about 8 a second, or ten minutes for the list. `flatMapSequential` keeps the cap of 10 and restores the order, at the cost of buffering results that finish early.",
    "code": W3J, "lang": "java", "alt_code": W3K, "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Pick the right operator for three bakery stations",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/CakeFlows.java"],
  "run": "./gradlew :reactive:test --tests 'workbench.reactive.l03.*'",
  "steps": [
   "Read the Javadoc on each of the three methods in `CakeFlows`. Each body is one line. Decide on the operator before you write anything.",
   "`iceAll`: any order, at most 4 cakes at the icing machine, and all 4 nozzles in use.",
   "`stackLayers`: each layer only after the one below it has set, results in stacking order, and nothing placed after a failure.",
   "`latestPrices`: only the most recent pick matters; a price still on its way must be cancelled when the customer picks again.",
   "Run the tests. They use `StepVerifier.withVirtualTime`, a test clock that skips the waits, so the 100 ms delays take no real time. Read `CakeFlowsTest` to see how it counts calls in flight and cancellations."
  ],
  "hints": [
   "If a test says `Expecting AtomicInteger(12) to have value: 4`, you used flatMap without its concurrency argument.",
   "`flatMapSequential` gets the order right for `stackLayers`, but places all four layers at once; the in-flight check catches it.",
   "If `sizePicks.switchMap(priceService)` doesn't compile, pass a lambda: `switchMap(size -> priceService.apply(size))`. `switchMap` declares its parameter as `Function<? super T, Publisher<? extends V>>`, and a `Function<String, Mono<String>>` variable is not that type, although a lambda or a method reference can be."
  ],
  "done_when": "All four tests in `CakeFlowsTest` pass."
 },
 "drill": {
  "title": "Predict the marbles",
  "minutes": 5,
  "prompt": "No code this time. Cakes A, B and C reach a station at the same moment. A takes 300 ms, B 100 ms and C 200 ms. On paper, write the output order and the time the stream completes for `flatMap`, `concatMap`, `flatMapSequential` and `switchMap`. Then check your answers.",
  "answer": {"lang": "text", "src": "flatMap            [B, C, A]   done at 300 ms   (B at 100, C at 200, A at 300)\nconcatMap          [A, B, C]   done at 600 ms   (A at 300, B at 400, C at 600)\nflatMapSequential  [A, B, C]   done at 300 ms   (all three released when A finishes)\nswitchMap          [C]         done at 200 ms   (B cancels A, C cancels B, only C finishes)"}
 },
 "recap": [
  "`map` is synchronous, one in and one out. If your function returns a `Mono`, `map` gives you `Flux<Mono<T>>` and no calls are made.",
  "`flatMap` subscribes to up to `concurrency` inners at once (default 256) and emits results in the order they finish. It creates no threads.",
  "The concurrency argument is also flatMap's demand: `flatMap(f, 4)` requests 4, then 1 per finished inner. Use it as a cap on calls in flight.",
  "`concatMap` runs one inner at a time, in order; `flatMapSequential` runs them at once but buffers results to emit them in order.",
  "`switchMap` cancels the previous inner when a new item arrives. Use it when only the latest result matters.",
  "The limits: cancelling only stops you listening, and the far side may finish its work anyway. And one failing inner ends the whole stream, until lesson 5 of this track."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "You need the delivery time for each of 10,000 orders. The delivery service allows 20 calls at once, and the output order doesn't matter. Which line fits?",
   "options": ["`orders.map(o -> delivery.timeFor(o))`", "`orders.concatMap(o -> delivery.timeFor(o))`", "`orders.flatMap(o -> delivery.timeFor(o), 20)`", "`orders.switchMap(o -> delivery.timeFor(o))`"],
   "answer": 2,
   "why": "flatMap with concurrency 20 keeps exactly as many calls in flight as the service allows. `map` would give a `Flux<Mono<...>>` and make no calls. `concatMap` is correct but makes one call at a time, and `switchMap` would cancel every lookup but the last."},
  {"q": "`orderBook.status(id)` returns `Mono<String>`. What happens when you subscribe to `ids.map(id -> orderBook.status(id))`?",
   "options": ["Each status is fetched, one at a time", "You receive one `Mono<String>` per id, and no call is made unless something subscribes to those Monos", "It doesn't compile", "All statuses are fetched at once"],
   "answer": 1,
   "why": "`map` passes each returned `Mono` along as an item, giving `Flux<Mono<String>>`. A `Mono` is an order form; nobody subscribes to these, so nothing runs. `flatMap` (or `concatMap`) is what subscribes to the inner publishers."},
  {"q": "The layers of a tall cake must be placed one at a time, each after the one below has set. A teammate proposes `flatMapSequential` because \"it keeps the order\". What is wrong with that?",
   "options": ["Nothing, it is the right choice", "It drops layers that finish out of order", "It places all the layers at once and only reorders the results", "It cannot handle errors"],
   "answer": 2,
   "why": "flatMapSequential subscribes to its inners eagerly, so every layer is placed at the same moment. Only the output is reordered. `concatMap` is the operator that waits for each inner to complete before subscribing to the next."},
  {"q": "A `switchMap` inner is still running when the source emits a new item. What happens to that inner?",
   "options": ["It is cancelled, and its results never reach the output", "It finishes, and its results are emitted after the new inner's", "It is paused until the new inner completes", "switchMap waits for it before starting the new inner"],
   "answer": 0,
   "why": "switchMap cancels the current inner and switches to a new one for each source item. That stops a slow, stale result from replacing a newer one, which is what can happen with flatMap."},
  {"q": "From \"CompletableFuture: composing async steps\": which `CompletableFuture` method plays the same role as Reactor's `flatMap` for one async step?",
   "options": ["`thenApply`", "`thenAccept`", "`thenCombine`", "`thenCompose`"],
   "answer": 3,
   "why": "`thenCompose` takes a function that returns another `CompletableFuture` and flattens it, just as flatMap subscribes to the publisher your function returns. `thenApply` is like `map`: given a function that returns a future, it produces a `CompletableFuture<CompletableFuture<T>>`.",
   "from": "exec-06"}
 ],
 "flashcards": [
  {"front": "What is flatMap's default concurrency in Reactor?", "back": "256 inners at once (and a prefetch of 32 per inner). Its first request to the source is also 256."},
  {"front": "`flatMap(f, 4)`: what does it request from the source?", "back": "4 at first, then 1 more each time an inner completes. So at most 4 inners are in flight."},
  {"front": "Does flatMap run inners on several threads?", "back": "No. It only subscribes to several at once. The parallel work comes from inners that are themselves asynchronous (non-blocking I/O, `Mono.delay`, `subscribeOn`)."},
  {"front": "Source 3, 1, 2; item i takes i x 100 ms. What does `concatMap` emit, and when does it finish?", "back": "`[3, 1, 2]` at 600 ms: one at a time, in order."},
  {"front": "What does `flatMapSequential` trade for ordered output at flatMap speed?", "back": "Memory: results that finish early wait in a buffer until all earlier inners are done (and a slow first item holds back the rest)."},
  {"front": "When does `switchMap` cancel an inner?", "back": "As soon as the source emits a new item. Only the latest item's inner is kept."},
  {"front": "What is the Kotlin Flow version of Reactor's `switchMap`?", "back": "`flatMapLatest`, or `mapLatest` when the block returns one value."}
 ],
 "terms": [
  {"term": "Inner publisher", "plain": "The `Mono` or `Flux` your function returns inside flatMap, concatMap or switchMap."},
  {"term": "Flattening", "plain": "Subscribing to inner publishers and merging their items into one output stream."},
  {"term": "Concurrency (flatMap)", "plain": "The most inners flatMap keeps subscribed at once, and its first request upstream."},
  {"term": "Prefetch", "plain": "How many items an operator requests ahead from a source, so they are ready when needed."},
  {"term": "Head-of-line blocking", "plain": "One slow item at the front holds back items behind it that are already done."},
  {"term": "Virtual time", "plain": "A fake clock in tests (`StepVerifier.withVirtualTime`) that you move forward by hand, so delays take no real time."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate, in your own words, the difference between `flatMap`, `concatMap` and `flatMapSequential`, and give one bakery example where each is the right choice.",
  "answer": "All three call a function that returns a publisher, and subscribe to it. flatMap subscribes to many at once, up to its concurrency, and emits results as they finish, so it's fast and unordered. Icing a batch of cakes on a machine with four nozzles fits it, with the concurrency set to 4. concatMap subscribes to one at a time and starts the next only after the previous completes, so it's ordered and slow. Stacking the layers of a cake needs that, because each layer sits on the one below. flatMapSequential subscribes to many at once like flatMap, but buffers results so they come out in input order. A stock report that must follow the ingredient list, but can ask the supplier about ten ingredients at once, fits it."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Order within a group, concurrency across groups.** The layers of each cake must be placed in order, but different cakes can be worked on at the same time. The usual shape is `groupBy` plus `concatMap` inside a `flatMap`:\n\n```java\nlayers.groupBy(Layer::cakeId)\n        .flatMap(cake -> cake.concatMap(stacker::place), 512)\n```\n\n```kotlin\nlayers.groupBy { it.cakeId }\n    .flatMap({ cake -> cake.concatMap { stacker.place(it) } }, 512)\n```\n\nThere is a trap. Each group stays open until the source completes, and flatMap only drains as many groups as its concurrency allows. The `groupBy` Javadoc says the concurrency of the subscriber \"should be greater than or equal to the number of groups created\". In a measured run, `Flux.range(0, 1000).groupBy(i -> i % 300).flatMap(g -> g.reduce(0, Integer::sum), 10)` simply hung; with concurrency 300 it completed. If the number of cakes has no upper limit, group by `cakeId.hashCode() % 32` instead and use concurrency 32, so there are never more than 32 groups.\n\n**Delaying errors.** By default an error in any inner ends the whole stream. `flatMapDelayError(f, concurrency, prefetch)` and `concatMapDelayError(f)` let the other inners finish and report the error at the end. Use them for batch jobs where partial results are still useful, then decide what to do with the error.\n\n**`flatMapIterable`.** When your function returns a `List` that is already in memory, `flatMapIterable(order -> order.items())` flattens it without creating inner publishers.\n\n**`handle`.** `handle((item, sink) -> { if (ok(item)) sink.next(convert(item)); })` is a map and a filter in one step, and it lets you skip an item instead of returning `null`."
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
