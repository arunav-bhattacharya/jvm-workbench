import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
K = "kotlin/workbench/functional/l05"
J = "java/workbench/functional/l05"
read = lambda p: (ROOT / p).read_text()
run = lambda cls: f"./gradlew :functional:demo -Pmain=workbench.functional.l05.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{LAB}/demo/{K}/{kt}"), "run": run(k + "Kt"), "file": f"{LAB}/demo/{K}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{LAB}/demo/{J}/{java}"), "run": run(j), "file": f"{LAB}/demo/{J}/{java}"}}


def cell(x, y, cls, label):
    return (f'<rect class="{cls}" x="{x - 28}" y="{y - 14}" width="56" height="28" rx="8"/>'
            + (f'<text class="t-s" x="{x}" y="{y + 5}" text-anchor="middle">{label}</text>' if label else ""))


ROWS = [80, 120, 160, 200, 240]
fig = ['<svg viewBox="0 0 680 300" role="img" aria-label="Two grids of five payments by two steps, filter and map. '
       'Numbers show the order the lambdas run. On a List, filter runs on all five payments first, then map on payments 1, 3 and 5. '
       'On a Sequence, filter 1 and map 1 run first, then filter 2, filter 3 and map 3, and payments 4 and 5 are never read.">',
       '<text class="t" x="170" y="24" text-anchor="middle">List: one step at a time</text>',
       '<text class="t" x="510" y="24" text-anchor="middle">Sequence: one payment at a time</text>',
       '<line class="ln-d" x1="340" y1="40" x2="340" y2="270"/>']
for x, label in ((160, "filter"), (250, "map"), (500, "filter"), (590, "map")):
    fig.append(f'<text class="t-s t-code" x="{x}" y="54" text-anchor="middle">{label}</text>')
for i, y in enumerate(ROWS):
    fig.append(f'<text class="t-s" x="80" y="{y + 5}" text-anchor="middle">pay {i + 1}</text>')
    fig.append(f'<text class="t-s" x="420" y="{y + 5}" text-anchor="middle">pay {i + 1}</text>')
# List: filter 1..5, then map on 1, 3, 5
for i, y in enumerate(ROWS):
    fig.append(cell(160, y, "box-a", str(i + 1)))
for i, y in enumerate(ROWS):
    order = {0: "6", 2: "7", 4: "8"}.get(i)
    fig.append(cell(250, y, "box-b" if order else "box-dim", order))
# Sequence: f1=1, m1=2, f2=3, f3=4, m3=5; rows 4 and 5 never read
seq = {(0, "f"): "1", (0, "m"): "2", (1, "f"): "3", (2, "f"): "4", (2, "m"): "5"}
for i, y in enumerate(ROWS):
    f, m = seq.get((i, "f")), seq.get((i, "m"))
    fig.append(cell(500, y, "box-a" if f else "box-dim", f))
    fig.append(cell(590, y, "box-b" if m else "box-dim", m))
fig.append('<text class="t-s t-m" x="648" y="205" text-anchor="middle">not read</text>')
fig.append('<text class="t-s t-m" x="648" y="245" text-anchor="middle">not read</text>')
fig.append('<text class="t-s" x="170" y="286" text-anchor="middle">8 calls, a new list after each step</text>')
fig.append('<text class="t-s" x="510" y="286" text-anchor="middle">5 calls, stops when take(2) is full</text>')
fig.append('</svg>')
FIG = "".join(fig)

L = {
 "id": "fp-05",
 "title": "Sequences: lazy pipelines, and where Java Streams fit",
 "minutes": 35,
 "goal": "By the end you can predict the order in which a List chain and a Sequence chain run their lambdas, choose between a List chain, a Sequence and a Java Stream for a pipeline, and build a lazy paging source with `sequence { }`.",
 "warmup": {
  "q": "Payments 1, 3 and 5 of five are settled. This runs: `payments.asSequence().filter { println(\"filter ${it.id}\"); it.settled }.map { println(\"map ${it.id}\"); it.amountCents }.take(2).toList()`. What prints?",
  "options": [
   "`filter 1` to `filter 5`, then `map 1`, `map 3`, `map 5`",
   "`filter 1`, `map 1`, `filter 2`, `filter 3`, `map 3`",
   "`filter 1`, `filter 2`, `filter 3`, then `map 1`, `map 3`",
   "Nothing: a Sequence only runs when you print it"
  ],
  "answer": 1,
  "why": "A Sequence pulls one payment through the whole chain before it reads the next one. Payment 1 passes the filter and goes straight on to `map`. Payment 2 fails the filter. Payment 3 passes and is mapped, and now `take(2)` has its two results, so nothing pulls payments 4 and 5. The first option is what the same chain prints on a List. `toList()` is what starts the work."
 },
 "sections": [
  {
   "h": "A List chain builds a whole list at every step",
   "body": """Here is a scan from a fraud job. It asks a risk model to score each of the day's authorizations and returns the first one that looks bad.

```kotlin
fun firstSuspicious(feed: List<Auth>): Auth? =
    feed.map { it to riskModel.score(it) }        // a 2 ms call per authorization
        .filter { (_, score) -> score >= 90 }
        .map { (auth, _) -> auth }
        .firstOrNull()
```

```java
Auth firstSuspicious(List<Auth> feed) {
    List<Scored> scored = feed.stream().map(a -> new Scored(a, riskModel.score(a))).toList();   // 2 ms each
    List<Auth> flagged = scored.stream().filter(s -> s.score() >= 90).map(Scored::auth).toList();
    return flagged.isEmpty() ? null : flagged.get(0);
}
```

It reads well and gives the right answer. On a feed of a million authorizations where the first bad one is number 518, it also calls the model a million times. That is 33 minutes of model time to find something that was there after one second.

The cause is that `map` and `filter` on a Kotlin `List` are **eager**. Each one loops over its whole input, writes the results into a brand-new list, and only then does the next step start. So the first `map` scores all million and builds a list of a million pairs. `filter` builds a second list. `firstOrNull` finally looks at element 0. People call this horizontal: the work goes across every element for step 1, then across every element for step 2.

Java has no eager chain, so the Java version collects after every step to do the same thing. That is exactly what Kotlin's List operations do for you.

You saw in "Collections without loops: map, filter, fold and friends" that these functions are `inline`: the compiler pastes the loop and your lambda into the caller, so no lambda objects exist at run time. The cost is somewhere else. Every step allocates a new `ArrayList`, and a `List<Long>` holds boxed `Long` objects. In a JMH run made for this course, `filter { }.map { }.sum()` over a million payments allocated 26.5 MB per call.

For a short chain over a few hundred elements, none of this matters, and the eager version is the easiest to debug: you can stop after any step and look at a real list. It starts to matter when the input is big, the steps are expensive, or you only need the first few results.""",
   "try": {
    "title": "Watch the order of the lambdas",
    "minutes": 4,
    "steps": [
     "Open `OrderDemo.kt` (or `OrderDemoJava.java`). The same `filter`, `map` and `take(2)` run on a List and on a Sequence. Write down the print order you expect for each.",
     "Run it with the command below.",
     "In the List chain, move `.take(2)` up to right after `txns`. Predict how many `filter` lines print and what the result is, then run it."
    ],
    "code": tryit("OrderDemo.kt", "OrderDemoJava.java"),
    "expect": "The List chain prints `filter 1` to `filter 5`, then `map 1`, `map 3`, `map 5`: each step finishes before the next starts. The Sequence chain prints nothing until `toList()` (building it only made a `TakeSequence`), then `filter 1, map 1, filter 2, filter 3, map 3`. Payments 4 and 5 are never read. With `take(2)` first, the List chain filters only payments 1 and 2 and prints `[1500]`. That is a different question (which of the first two payments are settled), so moving a step changes the answer in both models. Laziness only changes how much work runs."
   }
  },
  {
   "h": "A Sequence pulls one element through the whole chain",
   "body": """Put `asSequence()` in front of the same chain and the order of work changes. A Sequence is **lazy**: building the chain does nothing. The work starts at a **terminal operation** such as `toList()`, `first()`, `sum()` or `count()`, and then each element goes through every step before the next element is read. That is vertical order, and the figure shows it for five payments.

On the million authorizations, `feed.asSequence().map { ... }.filter { ... }.map { ... }.firstOrNull()` scores 518 and stops. This is **short-circuiting**: `first`, `firstOrNull`, `any`, `find` and `take(n)` can stop as soon as they have an answer, and in a lazy chain they stop every step above them too. For a single condition you don't even need a Sequence. `feed.firstOrNull { risk(it) >= 90 }` is one inlined loop, and it also stops at 518.

Underneath, each intermediate operation on a Sequence is an ordinary function, not `inline`, that wraps the previous sequence. `map` returns a `TransformingSequence` holding your lambda, `filter` a `FilteringSequence`, `take` a `TakeSequence`. When the terminal operation asks the last wrapper for an element, that wrapper asks the one before it, and so on up to the list. Here is the heart of `TransformingSequence` in the Kotlin 2.4.21 stdlib, next to the same idea written by hand in Java:

```kotlin
override fun next(): R = transformer(iterator.next())
override fun hasNext(): Boolean = iterator.hasNext()
```

```java
Iterator<R> mapped = new Iterator<>() {
    public boolean hasNext() { return source.hasNext(); }
    public R next() { return transformer.apply(source.next()); }
};
```

So a Sequence trades the intermediate lists for one small wrapper per step. The lambdas become real `Function1` objects again (created through `invokedynamic`, as "Function types, lambdas and closures" showed), and a `Long` coming out of `map` is boxed on its way through `invoke`.

One kind of step breaks the vertical flow. `sorted()` and `sortedBy { }` must see every element before they can hand out the smallest, so the first request makes them copy the whole upstream into a list and sort it. In the Try it, a `sortedBy` before `firstOrNull { }` pulls all 1,000,000 authorizations, even though the model still runs only 518 times. If you only need the smallest element, `minByOrNull { }` reads the input once and sorts nothing.""",
   "figure": {"svg": FIG, "caption": "The same filter, map and take(2). The List runs each step over every payment; the Sequence moves each payment through both steps and stops after two results."},
   "try": {
    "title": "Count the work on a million authorizations",
    "minutes": 4,
    "steps": [
     "Read `ScanCount.kt`. Every line looks for the same authorization, number 518 of a million. For each line, predict how many times `risk` runs and how many authorizations the `onEach` counter pulls.",
     "Run it.",
     "In the Sequence chain line, add `.toList()` just before `.firstOrNull()`. Predict the counts, then run it again.",
     "Run the Java twin and compare `findFirst` on one Stream with collecting first."
    ],
    "code": tryit("ScanCount.kt", "ScanCountJava.java"),
    "expect": "The List chain scores all 1,000,000. The Sequence chain and `firstOrNull { }` score 518 and stop. The `sortedBy` line also scores only 518, but its counter shows it pulled all 1,000,000 into a list to sort them first. With `.toList()` added, the Sequence scores 1,000,000 again: `toList()` is a terminal operation that wants every element. Java prints the same numbers, because a Stream is lazy in the same way and a collected list is not."
   },
   "refs": [{"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html", "kind": "docs"}]
  },
  {
   "h": "Make your own: generateSequence and sequence { yield }",
   "body": """A Sequence doesn't need a collection behind it. Two builders produce elements only when someone asks.

`generateSequence(seed) { next }` computes each element from the one before and ends when the lambda returns `null`. Here is a retry schedule that doubles from 100 ms up to 1.6 s:

```kotlin
val backoff = generateSequence(100L) { (it * 2).takeIf { next -> next <= 1_600 } }
backoff.toList()   // [100, 200, 400, 800, 1600]
```

```java
List<Long> backoff = Stream.iterate(100L, d -> d <= 1_600, d -> d * 2).toList();   // [100, 200, 400, 800, 1600]
```

Without the `takeIf`, the sequence is infinite. That is fine as long as something downstream stops it, such as `take(5)` or `first { }`.

`sequence { }` is for when making the next element takes real code, like a paging API. Inside the block, `yield(x)` hands out one element and `yieldAll(list)` hands out many:

```kotlin
val settlements = sequence {
    for (page in 1..3) yieldAll(fetchPage(page))   // fetchPage is an HTTP call
}
settlements.first { it.amountCents > 6_500 }       // fetches page 1 and page 2, never page 3
```

```java
Stream<Settlement> settlements = Stream.iterate(1, page -> page <= 3, page -> page + 1)
        .flatMap(page -> fetchPage(page).stream());
settlements.filter(s -> s.amountCents() > 6_500).findFirst();   // also skips page 3 on JDK 21
```

How does a `for` loop stop halfway? The block is a suspend lambda (its type is `suspend SequenceScope<T>.() -> Unit`). The compiler turns it into a state machine, the same way it compiles the suspend functions in the coroutines track. Each `yield` saves where the block is and returns control to the consumer. When the consumer asks for the next element, the block resumes right after that `yield`. No thread is involved: it all runs on the caller's thread, one step at a time. When the consumer stops asking, the block never resumes, so page 3 is never requested.

The scope is restricted. Only `yield` and `yieldAll` may suspend in there. Call `delay` inside `sequence { }` and Kotlin 2.4.21 refuses: `Restricted suspending functions can invoke member or extension suspending functions only on their restricted coroutine scope.` For paging that has to wait without blocking, use a `Flow` (the coroutines track).

The lab's paging source has one more rule: it doesn't know how many pages exist, and an empty page means the end. In Kotlin that is a `while (true)` loop with a `break`. In Java it is `Stream.iterate(0, p -> p + 1).map(api::page).takeWhile(p -> !p.isEmpty()).flatMap(List::stream)`.""",
   "try": {
    "title": "Fetch only the pages you read",
    "minutes": 3,
    "steps": [
     "Read `Paging.kt`. Each page holds three settlements. Predict which pages are fetched before the first settlement over 65.00 prints.",
     "Run it.",
     "Change `first` to `firstOrNull` and the threshold to `1_000_000`. Predict which pages are fetched and what prints, then run it."
    ],
    "code": tryit("Paging.kt", "PagingJava.java"),
    "expect": "`fetching page 1`, `fetching page 2`, then `Settlement(ref=S2-1, amountCents=7000)`. Page 3 is never fetched, because `first` stopped asking. With no match, all three pages are fetched and it prints `null`: laziness can only save work when something stops early. The backoff line is `[100, 200, 400, 800, 1600]` in both languages."
   },
   "refs": [{"title": "SequenceBuilder.kt, Kotlin 2.4.21 stdlib source", "url": "https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/collections/SequenceBuilder.kt", "kind": "read"}]
  },
  {
   "h": "Sequence or Stream, and when you need neither",
   "body": """A Java Stream is lazy and vertical, just like a Sequence. The Java twins in this lesson print the same order and the same counts. The differences are practical.

A Sequence is a recipe. Each terminal operation runs the whole chain again, side effects included: call `sum()` and then `count()` on the same sequence and every `map` lambda runs twice. A few sequences refuse a second run. `iterator().asSequence()` and `generateSequence { }` without a seed throw `IllegalStateException: This sequence can be consumed only once.` A Stream is always single-use. The second terminal operation throws `IllegalStateException: stream has already been operated upon or closed`.

Streams can do things sequences can't. `parallelStream()` splits the work over the common ForkJoinPool, and sequences have no parallel mode at all. `LongStream` and `mapToLong` keep primitives unboxed, and Kotlin has no `LongSequence`. On JDK 24 and later, `Gatherers` add windowing and scans to streams.

Here are the numbers from the JMH run behind this course. The machine was a 4-vCPU VM shared with other work, so treat the times as rough. The bytes allocated per call barely move between runs, so you can trust those. It summed settled amounts over 1,000,000 payments:

| Variant | Time per call | Allocated per call |
|---|---|---|
| `for` loop | 5.2 ms | about 0 |
| `filter { }.map { }.sum()` on a List | 148 ms | 26,507,194 B |
| `sumOf { if (settled) amount else 0L }` | 2.6 ms | about 0 |
| `asSequence().filter { }.map { }.sum()` | 9.0 ms | 189 B |
| `stream().filter().mapToLong().sum()` | 8.9 ms | 428 B |
| `stream().filter().map().reduce(0L, ...)` | 14 ms | 28,782,178 B |

The fastest line is neither a List chain nor a Sequence: it is one fused `sumOf`, which is the hand-written loop. The Sequence allocated almost nothing only because the JIT removed the boxes in this tiny benchmark. Don't count on that in a large service where one call site sees many different lambdas. When the terminal operation could stop early (first match at index 101), the gap was huge: 141 ns for the Sequence, 4.4 ms for the List chain.

So here is the rule I use. Use List operations by default. Switch to `asSequence()` when the terminal operation can stop early, or when a long chain runs over a large input. Use `sequence { }` or `generateSequence` for data that is produced on demand, such as pages and retries. Use a Stream when you need `parallel()`, a primitive stream or a Gatherer, or when a Java API hands you one. And when one pass does the job, write one pass: `sumOf`, `count { }`, `firstOrNull { }`.""",
   "try": {
    "title": "Run a sequence twice, and a stream twice",
    "minutes": 3,
    "steps": [
     "Read `Reuse.kt`. Predict how many `map` lines print, and what the second read of `once` does.",
     "Run it, then run `ReuseJava`.",
     "In `Reuse.kt`, delete `.asSequence()` from `amounts`. Predict how many `map` lines print now."
    ],
    "code": tryit("Reuse.kt", "ReuseJava.java"),
    "expect": "Six `map` lines: three for `sum()` and three more for `count()`, because each terminal operation reruns the chain. The iterator-backed sequence fails on its second read with `IllegalStateException: This sequence can be consumed only once.` Java's stream fails on the second terminal operation with `IllegalStateException: stream has already been operated upon or closed`. Without `asSequence()`, `amounts` is a List built once, so `map` prints three lines in total."
   }
  }
 ],
 "analogy": "A List chain is a mailroom clerk who stamps every letter in the sack, then sorts every stamped letter, then delivers. A Sequence clerk takes one letter, stamps it, sorts it, delivers it, and only then reaches for the next one, so when you say \"I only need the first two delivered\" the rest of the sack stays untouched. The lazy clerk also does nothing at all until someone asks for a delivery. The analogy breaks in one place: a clerk who is told to sort the sack by postcode can't deliver anything until every letter is out of the sack. That is `sorted()` in a Sequence, and no amount of laziness avoids it.",
 "in_your_world": "Paging is where this pays off in a payments service. A Quarkus scheduled job that reconciles with an acquirer often reads a settlement API page by page: `sequence { }` with `yieldAll(page)` lets the rest of the job be plain `filter`, `map` and `first` while only the pages it reads are fetched. A Kafka consumer's poll loop is the opposite case: a batch of 500 records is already in memory, so a List chain is simpler and just as fast. Inside a Temporal activity, keep the laziness inside the activity. A Sequence is a recipe, not data: pass the materialized result (`toList()`) out of the activity, never the sequence.",
 "mistake": """The most common real mistake is returning a lazy sequence that reads from a resource you have already closed:

```kotlin
fun refunds(ds: DataSource): Sequence<Refund> = ds.connection.use { c ->
    val rs = c.prepareStatement("select id, amount from refund").executeQuery()
    generateSequence { if (rs.next()) Refund(rs.getLong(1), rs.getLong(2)) else null }
}   // use { } closes the connection here, before anyone reads the sequence
```

```java
Stream<Refund> refunds(DataSource ds) throws SQLException {
    try (Connection c = ds.getConnection()) {
        ResultSet rs = c.prepareStatement("select id, amount from refund").executeQuery();
        return Stream.generate(() -> next(rs)).takeWhile(Objects::nonNull);
    }   // closed here, before the caller's terminal operation runs
}
```

It compiles and looks tidy. The first read fails later, far from this code, because the connection is gone. People make it because the code *looks* like it fetches the rows inside `use`, but a lazy chain only describes the work. Either finish the work inside the block (`.toList()` before the closing brace, if the result fits in memory), or turn it around and take the consumer as a parameter: `fun forEachRefund(ds: DataSource, action: (Refund) -> Unit)`, so the reading happens while the connection is open.""",
 "compare": {
  "title": "The first suspicious foreign payments: Sequence vs Stream",
  "java": {"title": "FraudScan.java", "src": "List<Long> firstSuspiciousForeign(List<Payment> feed, ToIntFunction<Payment> riskScore, int n) {\n    return feed.stream()\n            .filter(p -> !p.country().equals(\"NL\"))      // cheap check first\n            .filter(p -> riskScore.applyAsInt(p) >= 90)\n            .map(Payment::id)                             // boxed Long, as in Kotlin\n            .limit(n)                                     // short-circuits like take(n)\n            .toList();                                    // unmodifiable on JDK 16+\n}"},
  "kotlin": {"title": "FraudScan.kt", "src": "fun firstSuspiciousForeign(feed: List<Payment>, riskScore: (Payment) -> Int, n: Int): List<Long> =\n    feed.asSequence()\n        .filter { it.country != \"NL\" }          // cheap check first\n        .filter { riskScore(it) >= 90 }\n        .map { it.id }                         // boxed Long at the Function1 boundary\n        .take(n)                               // short-circuits like limit(n)\n        .toList()"},
  "note": "Both pipelines are lazy and run in the same vertical order, so both call the model exactly as often. The real differences are around the edges. The Stream can only be consumed once; the Sequence can be iterated again and will rerun the whole chain. The Stream could go `parallel()`; the Sequence can't. Kotlin's terminal operations mirror the List API (`firstOrNull` returns `null`, `groupBy`, `sumOf`), while the Stream returns `Optional` from `findFirst` and needs `Collectors` for grouping. And on the Kotlin side you can drop `asSequence()` and get an eager List chain with the same code, which is often the better choice for small inputs."
 },
 "worked": {
  "title": "Decide whether a reconciliation report should be lazy",
  "steps": [
   {"say": "A nightly reconciliation compares 2 million ledger lines with the acquirer's file and alerts on the first 20 mismatches. Here is the first version. Before reading on, find the step that makes laziness pay off.", "code": "fun firstMismatches(ledger: List<LedgerLine>, acquirer: Map<String, Long>): List<Mismatch> =\n    ledger.map { line -> Mismatch(line.ref, line.amountCents, acquirer[line.ref]) }\n        .filter { it.acquirerCents != it.ledgerCents }\n        .take(20)", "lang": "kotlin", "alt_lang": "java", "alt_code": "List<Mismatch> firstMismatches(List<LedgerLine> ledger, Map<String, Long> acquirer) {\n    List<Mismatch> all = ledger.stream()\n            .map(line -> new Mismatch(line.ref(), line.amountCents(), acquirer.get(line.ref())))\n            .toList();                                   // 2 million objects\n    return all.stream().filter(m -> !Objects.equals(m.acquirerCents(), m.ledgerCents())).limit(20).toList();\n}"},
   {"say": "`take(20)` can stop early, so this chain should be lazy. 1. Ask the question: does the terminal step stop before the end? Here, yes. 2. Put `asSequence()` at the front. Now the chain builds 20 mismatches plus the matching lines it read on the way, and no 2-million-element lists.", "code": "fun firstMismatches(ledger: List<LedgerLine>, acquirer: Map<String, Long>): List<Mismatch> =\n    ledger.asSequence()                                  // 2. lazy from here on\n        .map { line -> Mismatch(line.ref, line.amountCents, acquirer[line.ref]) }\n        .filter { it.acquirerCents != it.ledgerCents }\n        .take(20)                                        // 1. stops early\n        .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "List<Mismatch> firstMismatches(List<LedgerLine> ledger, Map<String, Long> acquirer) {\n    return ledger.stream()                               // 2. one lazy pipeline\n            .map(line -> new Mismatch(line.ref(), line.amountCents(), acquirer.get(line.ref())))\n            .filter(m -> !Objects.equals(m.acquirerCents(), m.ledgerCents()))\n            .limit(20)                                   // 1. stops early\n            .toList();\n}"},
   {"say": "3. Move cheap checks before expensive ones. Building a `Mismatch` for every line is wasted work; compare first and build the object only for real mismatches.", "code": "ledger.asSequence()\n    .filter { acquirer[it.ref] != it.amountCents }        // 3. cheap test, no allocation\n    .map { Mismatch(it.ref, it.amountCents, acquirer[it.ref]) }\n    .take(20)\n    .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "ledger.stream()\n        .filter(l -> !Objects.equals(acquirer.get(l.ref()), l.amountCents()))   // 3. cheap test\n        .map(l -> new Mismatch(l.ref(), l.amountCents(), acquirer.get(l.ref())))\n        .limit(20)\n        .toList();"},
   {"say": "4. Look for a barrier. Product now asks for the 20 *largest* mismatches. That needs `sortedByDescending { }` before `take(20)`, and the sort must read all 2 million lines first, so the Sequence saves nothing over a List here. Keep whichever is easier to read, and know that the cost is the full pass plus the sort.", "code": "ledger.asSequence()\n    .filter { acquirer[it.ref] != it.amountCents }\n    .sortedByDescending { abs(it.amountCents - (acquirer[it.ref] ?: 0L)) }   // 4. reads everything\n    .take(20)\n    .map { Mismatch(it.ref, it.amountCents, acquirer[it.ref]) }\n    .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "ledger.stream()\n        .filter(l -> !Objects.equals(acquirer.get(l.ref()), l.amountCents()))\n        .sorted(Comparator.comparingLong((LedgerLine l) -> Math.abs(l.amountCents() - acquirer.getOrDefault(l.ref(), 0L))).reversed())\n        .limit(20)                                        // 4. sorted() already read everything\n        .map(l -> new Mismatch(l.ref(), l.amountCents(), acquirer.get(l.ref())))\n        .toList();"}
  ]
 },
 "lab": {
  "title": "Score only what you must, and page lazily",
  "minutes": 12,
  "files": [f"{LAB}/main/{K}/FraudScan.kt", f"{LAB}/main/{K}/SettlementPages.kt"],
  "run": "./gradlew :functional:test --tests 'workbench.functional.l05.*'",
  "steps": [
   "Run the tests. Seven of nine fail. `firstSuspicious` already returns the right payment, but the test shows it calls the model 200,000 times.",
   "Fix `firstSuspicious` so it scores only up to the first match. Keep the signature.",
   "Write `firstSuspiciousForeign`: domestic (`\"NL\"`) cards must never reach the model, and nothing may be scored after the nth match.",
   "Write `allSettlements` with `sequence { }`: ask for page 0, then 1, then 2, and stop at the first empty page.",
   "Run the tests until all nine pass. Then read the last test and say what it shows about iterating a sequence twice."
  ],
  "hints": [
   "For `firstSuspicious`, `feed.asSequence()` in front of the existing chain is enough. So is `feed.firstOrNull { riskScore(it) >= 90 }`, one inlined loop.",
   "In `firstSuspiciousForeign`, the order of the two `filter` calls decides which payments reach the model. `take(n)` goes after both, before `toList()`.",
   "Inside `sequence { }` a `while (true)` loop is fine: `break` on an empty page, otherwise `yieldAll(page)`. The loop pauses at every `yieldAll` until the consumer wants more."
  ],
  "done_when": "All nine tests in `LazyPipelinesTest` pass."
 },
 "drill": {
  "title": "A paging source from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `fun <T> paged(fetch: (Int) -> List<T>): Sequence<T>` that asks for page 1, then 2, then 3, and so on, and stops at the first empty page without asking for the next one. Then write the Java version that returns a `Stream<T>`. Check: does yours fetch anything before a terminal operation runs?",
  "answer": {
   "lang": "kotlin",
   "src": "fun <T> paged(fetch: (Int) -> List<T>): Sequence<T> = sequence {\n    var page = 1\n    while (true) {\n        val items = fetch(page++)      // runs only when the consumer asks for more\n        if (items.isEmpty()) break     // an empty page ends it\n        yieldAll(items)                // pauses here between elements\n    }\n}",
   "alt": {"lang": "java", "src": "static <T> Stream<T> paged(IntFunction<List<T>> fetch) {\n    return Stream.iterate(1, page -> page + 1)       // 1, 2, 3, ... lazily\n            .map(fetch::apply)                       // one fetch per page, on demand\n            .takeWhile(items -> !items.isEmpty())    // stops at the first empty page\n            .flatMap(List::stream);\n}"}
  }
 },
 "recap": [
  "List operations are eager: each step loops over everything and builds a new list. They are inlined, so the cost is the lists and the boxing, not lambda objects.",
  "A Sequence is lazy: nothing runs until a terminal operation, then each element passes through every step before the next is read.",
  "Laziness pays when the terminal step stops early (`first`, `any`, `take`). `sorted` reads the whole upstream first.",
  "`generateSequence` and `sequence { yield }` produce elements on demand; `yield` suspends the block on the caller's thread until the next request.",
  "A Sequence reruns its chain on every terminal operation (a few are once-only); a Java Stream is always single-use but can go parallel and stay unboxed.",
  "Default to List operations; use a Sequence for early exits, long chains on big inputs and paging; one fused `sumOf` or `firstOrNull { }` beats both."
 ],
 "quiz": [
  {"q": "`score` is an expensive call. Which line calls it only until the first payment that scores 90 or more?", "options": ["`feed.map { score(it) }.first { it >= 90 }`", "`feed.asSequence().map { score(it) }.toList().first { it >= 90 }`", "`feed.asSequence().map { score(it) }.first { it >= 90 }`", "`feed.asSequence().map { score(it) }.sorted().first { it >= 90 }`"], "answer": 2, "why": "Only the third line is lazy all the way to a terminal step that stops early. The first is eager and scores everything before `first` looks. In the second, `toList()` is a terminal operation that pulls every element. In the fourth, `sorted()` must read every score before it can hand out the smallest."},
  {"q": "`val amounts = payments.asSequence().map { audit.log(it.id); it.amountCents }` runs over 5 payments, then the code calls `amounts.sum()` and `amounts.max()`. How many audit lines are written?", "options": ["5", "10", "0, because sequences are lazy", "5, then `max()` throws IllegalStateException"], "answer": 1, "why": "A Sequence is a recipe, and each terminal operation runs it again: five lines for `sum()`, five more for `max()`. Only a few sequences are once-only (for example `iterator().asSequence()`). If you need the values twice, call `toList()` once and reuse the list."},
  {"q": "A nightly job sums 40 million settled amounts on a 16-core machine and should use the cores. What fits best?", "options": ["`amounts.asSequence().sum()`", "`sequence { yieldAll(amounts) }.sum()`", "A List chain with `sumOf`", "`amounts.parallelStream().mapToLong { it }.sum()`"], "answer": 3, "why": "Only Java Streams have a parallel mode, and `mapToLong` keeps the values unboxed. Kotlin sequences run on one thread and have no parallel API. `sumOf` is the fastest single-threaded option, but it still uses one core."},
  {"q": "From the collections lesson: today's refunds can be empty. What does `refunds.asSequence().map { it.amountCents }.reduce { a, b -> a + b }` do on an empty input?", "options": ["Throws `UnsupportedOperationException: Empty sequence can't be reduced.`", "Returns 0", "Returns null", "Returns an empty sequence"], "answer": 0, "why": "`reduce` has no starting value, so with no elements it has nothing to return, and it throws. That holds for sequences as it does for lists. Use `fold(0L) { a, b -> a + b }` or `sum()`, which return 0, or `reduceOrNull`.", "from": "fp-04"},
  {"q": "`sequence { for (p in 1..10) yieldAll(api.page(p)) }.take(5).toList()`. Every page holds 3 records. How many pages are fetched?", "options": ["1", "2", "10", "0, until the result is printed"], "answer": 1, "why": "Page 1 gives three records and page 2 gives the fourth and fifth. `take(5)` is then full and stops asking, so the block never resumes to fetch page 3. `toList()` is the terminal operation, so the fetching happens right there, not when you print."}
 ],
 "flashcards": [
  {"front": "What does `list.filter { }.map { }` allocate?", "back": "A new `ArrayList` per step, plus boxes for primitives in a `List<Long>`. The lambdas are inlined, so no function objects."},
  {"front": "When does a Sequence chain run its lambdas?", "back": "Only when a terminal operation (`toList`, `first`, `sum`, `count`, ...) asks for elements. `map` and `filter` on a Sequence only wrap it."},
  {"front": "In what order does `asSequence().filter { }.map { }` run?", "back": "Element by element: filter 1, map 1, filter 2, ... Each element goes through every step before the next one is read."},
  {"front": "Why does `sortedBy { }` in a Sequence read everything?", "back": "It can't hand out the smallest element until it has seen all of them, so the first request copies the whole upstream into a list and sorts it."},
  {"front": "What happens when you run a Sequence twice?", "back": "The whole chain runs again, side effects included. `iterator().asSequence()` and seedless `generateSequence { }` throw `IllegalStateException` instead."},
  {"front": "What happens when you use a Java Stream twice?", "back": "`IllegalStateException: stream has already been operated upon or closed`. Streams are single-use."},
  {"front": "How does `sequence { }` pause between elements?", "back": "The block is a suspend lambda. Each `yield` suspends it until the consumer asks for the next element. No thread is involved."}
 ],
 "terms": [
  {"term": "Eager", "plain": "Does all the work for a step right away and stores the result, before the next step starts."},
  {"term": "Lazy", "plain": "Does no work until a result is asked for, and then only as much as needed."},
  {"term": "Intermediate operation", "plain": "A step such as `map` or `filter` that returns another Sequence or Stream and runs nothing by itself."},
  {"term": "Terminal operation", "plain": "A step such as `toList`, `first` or `sum` that asks for elements and so makes the chain run."},
  {"term": "Short-circuiting", "plain": "Stopping as soon as the answer is known, as `first`, `any` and `take` do."},
  {"term": "Stateful operation", "plain": "A step like `sorted` that needs to remember many elements, often all of them, before it can produce output."},
  {"term": "Sequence builder", "plain": "`sequence { }`: a block that hands out elements with `yield` and pauses between them."}
 ],
 "explain_back": {
  "prompt": "A teammate added `.asSequence()` in front of every collection chain in the settlement service \"because sequences are faster\". Explain in your own words what a Sequence changes, and when it is worth it.",
  "answer": "A Sequence changes the order of work. A List chain runs each step over the whole collection and builds a new list before the next step starts. A Sequence runs nothing until a terminal operation asks for elements, then moves each element through every step before reading the next. That saves the intermediate lists, and when the last step can stop early, like `first` or `take`, it skips the rest of the input entirely. It isn't free: each step becomes a wrapper object with a lambda, values get boxed through `invoke`, and a chain run twice does all its work twice. For a full pass over a few hundred elements, the eager chain is just as fast and easier to debug, and a single `sumOf` or `count { }` beats both. I'd keep `asSequence()` where a chain stops early or runs several steps over large inputs, and remove it elsewhere."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three details that matter once you write sequences in hot code.

**Boxing.** A Sequence of `Long` is a sequence of `java.lang.Long` objects, because each step calls a `Function1` whose `invoke` takes and returns `Object`. In bytecode, the lambda of `map { it.amountCents }` is a `Function1` whose `invokedynamic` signature returns `Ljava/lang/Long;`. Java's `mapToLong` takes a `ToLongFunction` that returns a primitive `long`. In the JMH run above, the Sequence still allocated only 189 bytes per call, because C2's escape analysis saw that the boxes never escaped and removed them. That worked because the benchmark had one call site and one lambda type. In a real service the same `FilteringSequence` code runs with dozens of different lambdas, its call site becomes megamorphic, the JIT stops inlining, and the boxes come back.

**IntelliJ's hint.** The Kotlin plugin has an inspection that suggests converting a call chain on a collection into a sequence. It is on by default as a weak warning and fires for chains of five or more calls. Treat it as a prompt to ask the question from this lesson (does the end of the chain stop early, and is the input big?), not as a rule.

**Gatherers.** Since JDK 24, streams have `Stream.gather`, with built-ins in `java.util.stream.Gatherers`: `windowFixed`, `windowSliding`, `fold`, `scan` and `mapConcurrent`. Kotlin has had the equivalents on both `List` and `Sequence` for years: `chunked`, `windowed`, `fold` and `runningFold` (also called `scan`). So on JDK 21, a 7-day moving average of settlement volume is `days.windowed(7) { it.average() }` in Kotlin and a hand-written loop in Java; on JDK 24 and later Java can write `stream.gather(Gatherers.windowSliding(7))`. The labs compile with release 21, so they use none of this."""
 },
 "sources": [
  {"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html"},
  {"title": "Collections in Java and Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html"},
  {"title": "java.util.stream package summary (Java SE 21 API)", "url": "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html"},
  {"title": "_Sequences.kt, Kotlin 2.4.21 stdlib source", "url": "https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt"}
 ]
}

out = ROOT / "content/lessons/fp-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
