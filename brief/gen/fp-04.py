import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l04.demo"


def kdemo(name, alt=True):
    path = f"{LAB}/demo/kotlin/workbench/functional/l04/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(name + "Java")
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l04/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


# fold as a picture: the accumulator flows left to right, each payment changes it (or not)
ACC = [("10,000", "box-b"), ("11,500", "box"), ("11,500", "box"), ("13,000", "box"), ("13,000", "box"), ("13,700", "box-ok")]
PAY = [("pay_1 SETTLED", "+1,500", "box-a"), ("pay_2 PENDING", "+0", "box-dim"), ("pay_3 SETTLED", "+2,000 - 500", "box-a"),
       ("pay_4 FAILED", "+0", "box-dim"), ("pay_5 SETTLED", "+700", "box-a")]
parts = []
for i, (label, cls) in enumerate(ACC):
    x = 20 + i * 115
    parts.append(f'<rect class="{cls}" x="{x}" y="150" width="90" height="38" rx="8"/>'
                 f'<text class="t-s t-code" x="{x + 45}" y="174" text-anchor="middle">{label}</text>')
    if i < len(ACC) - 1:
        parts.append(f'<line class="ln-a" x1="{x + 90}" y1="169" x2="{x + 113}" y2="169" marker-end="url(#arr)"/>')
for i, (name, delta, cls) in enumerate(PAY):
    cx = 122 + i * 115
    parts.append(f'<rect class="{cls}" x="{cx - 52}" y="44" width="104" height="52" rx="8"/>'
                 f'<text class="t-s" x="{cx}" y="65" text-anchor="middle">{name}</text>'
                 f'<text class="t-s t-code" x="{cx}" y="85" text-anchor="middle">{delta}</text>'
                 f'<line class="ln-d" x1="{cx}" y1="96" x2="{cx}" y2="162" marker-end="url(#arr)"/>')
FIG = (
    '<svg viewBox="0 0 700 230" role="img" aria-label="fold as a picture. The accumulator starts at the opening balance of 10,000 and moves left to right. '
    'Each payment changes it: settled ones add their amount minus refunds, pending and failed ones add nothing. It ends at 13,700.">'
    '<text class="t-s t-code" x="350" y="24" text-anchor="middle">payments.fold(10_000L) { balance, p -&gt; ... }</text>'
    + "".join(parts)
    + '<text class="t-s t-m" x="20" y="212">opening</text>'
    + '<text class="t-s t-m" x="680" y="212" text-anchor="end">result</text>'
    + '<text class="t-s t-m" x="350" y="212" text-anchor="middle">the accumulator carries the state from one element to the next</text>'
    + '</svg>'
)

S1 = """Here is the end-of-day settlement report the way most of us first write it: one pass over the payments, four results.

```java
long settled = 0;
Map<String, Long> net = new LinkedHashMap<>();
List<String> failed = new ArrayList<>();
Payment largest = payments.get(0);
for (Payment p : payments) {
    switch (p.status()) {
        case SETTLED -> {
            settled += p.amountCents();
            net.merge(p.merchant(), p.amountCents() - refundOf(p), Long::sum);
            if (p.amountCents() > largest.amountCents()) largest = p;
        }
        case FAILED -> failed.add(p.id());
        case PENDING -> { }
    }
}
```

```kotlin
var settled = 0L
val net = LinkedHashMap<String, Long>()
val failed = ArrayList<String>()
var largest = payments.first()
for (p in payments) {
    when (p.status) {
        Status.SETTLED -> {
            settled += p.amountCents
            net[p.merchant] = (net[p.merchant] ?: 0L) + p.amountCents - (p.refundCents ?: 0L)
            if (p.amountCents > largest.amountCents) largest = p
        }
        Status.FAILED -> failed.add(p.id)
        Status.PENDING -> {}
    }
}
```

It works on a normal day. It's also hard to read, for a reason you can name: four results are being built at the same time, interleaved, and every line changes one of them. To check how `largest` is computed, you have to read the whole loop, because any line might touch it.

And it has two bugs that a normal day never shows. On a day with no payments, `payments.first()` throws `NoSuchElementException: List is empty.` (Java's `get(0)` throws an `IndexOutOfBoundsException`). And when the first payment of the day is a pending one for 99,000 cents, `largest` starts there, no settled payment beats it, and the report names a payment that never settled.

Here is the same report written with collection operations:

```java
List<Payment> settledPayments = payments.stream().filter(p -> p.status() == SETTLED).toList();
long settled = settledPayments.stream().mapToLong(Payment::amountCents).sum();
Map<String, Long> net = settledPayments.stream().collect(Collectors.groupingBy(
        Payment::merchant, LinkedHashMap::new, Collectors.summingLong(p -> p.amountCents() - refundOf(p))));
List<String> failed = payments.stream().filter(p -> p.status() == FAILED).map(Payment::id).toList();
Optional<Payment> largest = settledPayments.stream().max(Comparator.comparingLong(Payment::amountCents));
```

```kotlin
val settledPayments = payments.filter { it.status == Status.SETTLED }
val settled = settledPayments.sumOf { it.amountCents }
val net = settledPayments.groupBy { it.merchant }
    .mapValues { (_, ps) -> ps.sumOf { it.amountCents - (it.refundCents ?: 0L) } }
val failed = payments.filter { it.status == Status.FAILED }.map { it.id }
val largest = settledPayments.maxByOrNull { it.amountCents }
```

Each result is one `val`, computed from the list, and each line says what it computes rather than how to walk the list. Both bugs are gone without anyone hunting for them: `maxByOrNull` only ever sees settled payments and returns null for an empty list, and nothing assumes there is a first element. The rest of this lesson takes those operations one at a time, with the traps that come with them."""

S2 = """Each collection operation does one job and returns a new collection, so you read a chain top to bottom, one job per line.

- `map` transforms every element: `payments.map { it.amountCents }` gives one amount per payment, in the same order.
- `filter` keeps the elements that pass a test: `payments.filter { it.status == SETTLED }`.
- `mapNotNull` transforms and drops the nulls in one step. `payments.mapNotNull { it.refundCents }` gives just the refunds, `[500]` on the sample day. It replaces `map { ... }.filterNotNull()` and builds one list instead of two.
- `flatMap` turns each element into a list and joins the lists: `batches.flatMap { it.payments }` turns a day of acquirer files into one list of payments.

Then come the operations that boil a list down to one answer: `sumOf`, `count { }`, `any { }`, `all { }`, `none { }`, `first { }` and `maxByOrNull { }`. The ones that take a predicate stop at the first element that decides the answer, so `any` stops at its first match.

Java has the same operations on streams. Side by side:

```java
List<Long> refunds = payments.stream()
        .map(Payment::refundCents)
        .filter(Objects::nonNull)
        .toList();                                          // [500]
List<String> ids = batches.stream()
        .flatMap(b -> b.payments().stream())
        .map(Payment::id)
        .toList();
boolean anyLarge = payments.stream().anyMatch(p -> p.amountCents() > 10_000);
```

```kotlin
val refunds = payments.mapNotNull { it.refundCents }        // [500]
val ids = batches.flatMap { it.payments }.map { it.id }
val anyLarge = payments.any { it.amountCents > 10_000 }
```

The difference that matters isn't the syntax. A Java stream is lazy: nothing runs until the terminal operation, and then each element travels through the whole pipeline. Kotlin's operations on a `List` are **eager**. `filter` runs over the whole list and returns a new `ArrayList`, then `map` runs over that one and returns another. Every step allocates a full intermediate list. As the last lesson showed, the lambdas cost nothing, because these functions are `inline`. The lists are the cost. For a settlement day of a few thousand payments that's nothing. For a million rows and five steps it starts to matter, and the next lesson's sequences are the fix.

One rule keeps a chain honest: no side effects inside it. A `map` that also writes to the database, or a `filter` that bumps a counter, brings back exactly the hidden state you just removed. Effects go at the end, in a `forEach`, or better, in the shell from lesson 1."""

S3 = """Every loop that builds one result has the same two parts: a starting value, and a step that combines the result so far with the next element. `fold` is that loop with both parts passed in.

```java
long balance = payments.stream().reduce(10_000L,
        (acc, p) -> p.status() == SETTLED ? acc + p.amountCents() - refundOf(p) : acc,
        Long::sum);                     // the third argument only matters for parallel streams
```

```kotlin
val balance = payments.fold(10_000L) { acc, p ->
    when (p.status) {
        Status.SETTLED -> acc + p.amountCents - (p.refundCents ?: 0L)
        Status.PENDING, Status.FAILED -> acc
    }
}
```

The value carried from one step to the next is the **accumulator**, `acc` here. The stdlib's `fold` is the loop you'd write by hand: `var accumulator = initial; for (element in this) accumulator = operation(accumulator, element); return accumulator`. It's `inline`, so your lambda is pasted into that loop. The `var` still exists, but it lives inside `fold` where nothing else can touch it, and your own code has only `val`s.

`sumOf`, `count`, `maxByOrNull` and `joinToString` are all special cases of `fold`, already written and named. Prefer them when they fit, because `sumOf { it.amountCents }` says more than `fold(0L) { acc, p -> acc + p.amountCents }`. Reach for `fold` when the step needs a `when`, as the balance does, or when the accumulator is something richer than a number.

`reduce` looks like `fold` without the starting value. It uses the first element as the start instead, and that is the trap: an empty list has no first element. Here is what Kotlin 2.4.21 does with an empty list:

```text
fold(0L) { a, b -> a + b }        0
sum()                             0
reduceOrNull { a, b -> a + b }    null
reduce { a, b -> a + b }          throws UnsupportedOperationException: Empty collection can't be reduced.
first()                           throws NoSuchElementException: List is empty.
maxOf { it }                      throws NoSuchElementException
firstOrNull(), maxOrNull()        null
```

Java chose differently. `Stream.reduce` without an identity value returns an `Optional`, empty for an empty stream, so the type makes you handle the case. Kotlin gives you two names instead, a throwing one and an `OrNull` one. The rule for payment code: use `fold`, `sumOf` or an `OrNull` function whenever the input can be empty, and a quiet day always can be. Keep `reduce` and `first()` for the places where an empty list is a bug you want to hear about loudly."""

S4 = """Reports are mostly maps: totals per merchant, payments by id, counts per status. Three operations build them, and each has a behaviour worth knowing before it surprises you.

`groupBy` puts every element into a list under its key:

```java
Map<String, List<String>> byMerchant = payments.stream().collect(
        Collectors.groupingBy(Payment::merchant, Collectors.mapping(Payment::id, Collectors.toList())));
// {globex=[pay_2, pay_5], acme=[pay_1, pay_3], initech=[pay_4]}   a HashMap: no order promised
```

```kotlin
val byMerchant = payments.groupBy({ it.merchant }, { it.id })
// {acme=[pay_1, pay_3], globex=[pay_2, pay_5], initech=[pay_4]}   a LinkedHashMap: first-seen order
```

Kotlin's `groupBy` returns a `LinkedHashMap`, and its documentation promises that keys keep the order in which they were first seen. Java's `groupingBy` promises nothing about the map it returns; on JDK 21 it was a `HashMap` that printed `globex` first. If a report must list merchants in the order they appeared, Kotlin does that for you, and in Java you pass `LinkedHashMap::new`. When you only need a number per group, `groupingBy { it.merchant }.eachCount()` or `.fold(0L) { acc, p -> acc + p.amountCents }` computes it in one pass without building a list for each group.

`associateBy` builds a map with one element per key. Here the two languages part ways:

```java
Map<String, String> byMerchantId = payments.stream()
        .collect(Collectors.toMap(Payment::merchant, Payment::id));
// throws IllegalStateException: Duplicate key acme (attempted merging values pay_1 and pay_3)
```

```kotlin
val byMerchantId = payments.associateBy({ it.merchant }, { it.id })
// {acme=pay_3, globex=pay_5, initech=pay_4}   pay_1 and pay_2 are gone, without a word
```

When two elements share a key, `associateBy` keeps the last one and says nothing. Java's `toMap` throws. For payments keyed by an id that should be unique, Java's behaviour is the one you want. A Kafka redelivery puts the same payment into two batches, `associateBy` quietly keeps one copy, and nobody hears about the duplicate. So check before you index. `payments.groupingBy { it.id }.eachCount().filterValues { it > 1 }` lists every repeated id, and the lab's `indexById` refuses a day that has any.

`partition` splits a list in two by a predicate, and destructuring makes it read well: `val (settled, open) = payments.partition { it.status == SETTLED }`. Java's version is `Collectors.partitioningBy`, which returns a `Map<Boolean, List<Payment>>`."""

L = {
    "id": "fp-04",
    "title": "Collections without loops: map, filter, fold and friends",
    "minutes": 38,
    "goal": "By the end you can rewrite a loop that builds several results into a few collection operations, pick the right one for each job, use fold as the general loop, and avoid the empty-list and duplicate-key traps in both Kotlin and Java.",
    "warmup": {
        "q": "A quiet settlement day has no payments. What does `payments.reduce { a, b -> if (a.amountCents >= b.amountCents) a else b }` do?",
        "options": [
            "Returns null",
            "Throws `UnsupportedOperationException: Empty collection can't be reduced.`",
            "Returns an empty `Optional`, like Java's `Stream.reduce`",
            "Doesn't compile, because `reduce` needs a starting value"
        ],
        "answer": 1,
        "why": "`reduce` starts from the first element, and an empty list has none, so Kotlin throws. Java's `Stream.reduce` without an identity returns `Optional.empty`, which is why the third option is tempting. In Kotlin you choose explicitly: `reduceOrNull`, `maxByOrNull`, or `fold` with a starting value."
    },
    "sections": [
        {
            "h": "A settlement report written as one loop",
            "body": S1,
            "try": {
                "title": "Break the loop with a quiet day",
                "minutes": 4,
                "steps": [
                    "Run `ReportLoop` (or `ReportLoopJava`). Check that the loop and the chain agree on the sample day.",
                    "Run it again with `-Pargs=empty` added. Predict first: which version survives a day with no payments?",
                    "Put a pending payment for 99,000 cents at the front of the sample day (`sampleDay` in `SampleDay.kt`, or `DAY` in the Java file) and run once more. Compare the two `largest` values."
                ],
                "code": kdemo("ReportLoop"),
                "expect": "On the sample day both print `settled=4200 net={acme=3000, globex=700} failed=[pay_4] largest=pay_3`. On the empty day the chain prints zeros, an empty map and `largest=null`, and the loop throws `java.util.NoSuchElementException: List is empty.` (Java: `ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0`). With the big pending payment first, the loop reports that pending payment as the largest; the chain still says `pay_3`."
            }
        },
        {
            "h": "map, filter, mapNotNull, flatMap: one job per step",
            "body": S2,
            "try": {
                "title": "Predict each line",
                "minutes": 4,
                "steps": [
                    "Open `Operations.kt` (or `OperationsJava.java`) and the sample day in `SampleDay.kt`. Predict every line of output, then run it.",
                    "Replace `mapNotNull { it.refundCents }` with `map { it.refundCents }` and run. What changed? Then add `.sum()` after it and read the compiler's answer.",
                    "Look at the last line. What class does each step return?"
                ],
                "code": kdemo("Operations"),
                "expect": "`map` gives all five amounts, `filter` gives `[pay_1, pay_3, pay_5]`, `mapNotNull` gives `[500]`, `flatMap` gives the five ids in batch order, `sumOf` 26100, `count` 3, `any / all` `true / true`, and `partition` `[pay_1, pay_3, pay_5] / [pay_2, pay_4]`. Plain `map` gives `[null, null, 500, null, null]`, a `List<Long?>`, and `.sum()` on it fails with `none of the following candidates is applicable`, because `sum` only exists for lists of non-null numbers. Kotlin's `map` returns a fresh `java.util.ArrayList`; Java's `toList()` returns an unmodifiable `ImmutableCollections$ListN`."
            },
            "refs": [
                {"title": "Collection transformations: map, flatMap, associate (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-transformations.html", "kind": "docs"},
                {"title": "Collections in Java and Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html", "kind": "docs"}
            ]
        },
        {
            "h": "The loop you were writing is a fold",
            "body": S3,
            "figure": {"svg": FIG, "caption": "fold carries one value, the accumulator, through the list. Each element produces the next value from the last."},
            "try": {
                "title": "Empty-list traps, both languages",
                "minutes": 3,
                "steps": [
                    "Run `EmptyTraps` (or `EmptyTrapsJava`). Before you look, mark each line: a value, or an exception?",
                    "Change `none` to `listOf(1_500L, 2_000L)` and predict each line again before running.",
                    "In your own service, search for `.first()` and `.reduce {`. For each hit, ask whether that list can be empty on a quiet day."
                ],
                "code": kdemo("EmptyTraps"),
                "expect": "On the empty list, `fold` and `sum` give 0; `reduceOrNull`, `firstOrNull` and `maxOrNull` give null; `reduce`, `first()` and `maxOf` throw, with the messages in the table above. The Java version prints 0 for both sums, `Optional.empty` for `reduce` without an identity, for `findFirst()` and for `max`, and throws `NoSuchElementException: No value present` from `orElseThrow()`. With two amounts every line returns a value: 3500 for the folds, sums and reduces, 1500 for `first()`, 2000 for the max."
            },
            "refs": [
                {"title": "Aggregate operations: fold, reduce and the OrNull variants (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-aggregate.html", "kind": "docs"}
            ]
        },
        {
            "h": "From a list to a map: groupBy, associateBy, partition",
            "body": S4,
            "try": {
                "title": "Find the line that loses data",
                "minutes": 4,
                "steps": [
                    "Run `DuplicateKeys` (or `DuplicateKeysJava`). Compare the key order of Kotlin's `groupBy` with Java's `groupingBy`.",
                    "Find the line that loses data without telling you. Which payments are missing from it?",
                    "In the Java version, give `toMap` a third argument, `(a, b) -> b`, and run. In the Kotlin version, add a line that prints the repeated merchants: `groupingBy { it.merchant }.eachCount().filterValues { it > 1 }.keys`."
                ],
                "code": kdemo("DuplicateKeys"),
                "expect": "Kotlin prints `acme, globex, initech` in first-seen order, from a `java.util.LinkedHashMap`. Java's `groupingBy` prints `globex` first, from a `java.util.HashMap`. `associateBy` keeps `pay_3`, `pay_5` and `pay_4`: `pay_1` and `pay_2` vanished silently. Java's plain `toMap` throws `IllegalStateException: Duplicate key acme (attempted merging values pay_1 and pay_3)`; with `(a, b) -> b` it keeps the last value and behaves exactly like `associateBy`. The repeated merchants are `[acme, globex]`."
            },
            "refs": [
                {"title": "Grouping (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-grouping.html", "kind": "docs"},
                {"title": "Collectors: toMap and groupingBy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Collectors.html", "kind": "docs"}
            ]
        }
    ],
    "analogy": "Collection operations are the stations of a mail room's sorting line. One station throws away junk mail (`filter`), one stamps every envelope (`map`), one opens parcels and puts their contents on the belt (`flatMap`), and the last one counts what arrives (`sumOf`). Each station does one job and knows nothing about the others, so you can check one without reading the rest. The loop is one clerk doing everything at once with four piles on the desk. The analogy breaks on how the work moves: Kotlin's list operations don't pass envelopes along one at a time. Each station finishes the whole pile before the next one starts, which is what the next lesson's sequences change.",
    "in_your_world": "Settlement and reconciliation jobs are where this lesson pays off. Acquirer files arrive as batches (`flatMap`), you keep the settled rows (`filter`), total them per merchant (`groupBy` or `groupingBy().fold`) and index them by id for matching (`associateBy`). The duplicate trap is real there: Kafka delivers at least once, and acquirers resend a file after a timeout. Index by id or idempotency key with a duplicate check, as the lab does, or make duplicates a line in the report. Keep these chains in the pure core and let the shell load the lists. Then a reconciliation test is a list literal in and an expected map out.",
    "mistake": "The most common mistake is indexing payments with `associateBy { it.id }` (or Java's `toMap` with an `(a, b) -> b` merge function, its twin) and assuming duplicates can't happen. They can: a redelivered Kafka message, an acquirer file sent twice, a retried webhook. `associateBy` keeps the last copy, and the report quietly shows one payment where there were two. Use it only when a repeated key is impossible, or when last-wins is what you mean. Otherwise check first with `groupingBy { it.id }.eachCount().filterValues { it > 1 }`, or keep every element with `groupBy`.",
    "compare": {
        "title": "The settlement report with streams and with Kotlin collection functions",
        "java": {
            "title": "Report.java",
            "src": "static Report report(List<Batch> batches) {\n    List<Payment> payments = batches.stream().flatMap(b -> b.payments().stream()).toList();\n    Map<String, Payment> byId = payments.stream()\n            .collect(Collectors.toMap(Payment::id, p -> p));            // throws on a repeated id\n\n    List<Payment> settled = payments.stream().filter(p -> p.status() == SETTLED).toList();\n    return new Report(\n            payments.size(),\n            settled.stream().mapToLong(Payment::amountCents).sum(),\n            payments.stream().map(Payment::refundCents).filter(Objects::nonNull)\n                    .mapToLong(Long::longValue).sum(),\n            settled.stream().collect(Collectors.groupingBy(Payment::merchant,\n                    LinkedHashMap::new,                                   // or no order is promised\n                    Collectors.summingLong(p -> p.amountCents() - refundOf(p)))),\n            payments.stream().filter(p -> p.status() == FAILED).map(Payment::id).toList(),\n            settled.stream().max(Comparator.comparingLong(Payment::amountCents)));   // Optional<Payment>\n}"
        },
        "kotlin": {
            "title": "Report.kt",
            "src": "fun report(batches: List<Batch>): Report {\n    val payments = batches.flatMap { it.payments }\n    val repeated = payments.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys\n    require(repeated.isEmpty()) { \"duplicate payment ids: ${repeated.joinToString()}\" }   // associateBy would not\n\n    val settled = payments.filter { it.status == SETTLED }\n    return Report(\n        paymentCount = payments.size,\n        settledCents = settled.sumOf { it.amountCents },\n        refundedCents = payments.mapNotNull { it.refundCents }.sum(),\n        netByMerchant = settled.groupBy { it.merchant }                      // first-seen order\n            .mapValues { (_, ps) -> ps.sumOf { it.amountCents - (it.refundCents ?: 0L) } },\n        failedIds = payments.filter { it.status == FAILED }.map { it.id },\n        largestSettled = settled.maxByOrNull { it.amountCents },            // Payment?, null when none\n    )\n}"
        },
        "note": "The vocabulary is nearly the same, and the defaults are not. Java streams are lazy and single-use and finish with a collector; Kotlin's list functions are eager, return ordinary lists and maps, and can be called again on the same list. Java says \"maybe nothing\" with `Optional`, Kotlin with a nullable type and the `OrNull` functions. Java's `groupingBy` promises no key order unless you pass a map factory, while Kotlin's `groupBy` keeps first-seen order. And the duplicate-key defaults are opposite: Java's `toMap` throws, Kotlin's `associateBy` keeps the last value, so in Kotlin the duplicate check is your job."
    },
    "worked": {
        "title": "Rewrite a nested-loop refund match",
        "steps": [
            {
                "say": "Reconciliation matches each refund to the payment it belongs to. Here is a direct translation of two nested loops into a chain. Before reading on, estimate how many comparisons it makes for 10,000 payments and 2,000 refunds.",
                "code": "val matched = payments.flatMap { p ->\n    refunds.filter { it.paymentId == p.id }.map { r -> p to r }\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "List<Map.Entry<Payment, Refund>> matched = payments.stream()\n        .flatMap(p -> refunds.stream()\n                .filter(r -> r.paymentId().equals(p.id()))\n                .map(r -> Map.entry(p, r)))\n        .toList();"
            },
            {
                "say": "1. Count the work. The inner `filter` runs over every refund for every payment: 10,000 x 2,000 = 20 million comparisons, plus one small list per payment. A chain is no faster than the loop it replaced; it only reads better. 2. Index once instead: build a map from id to payment, then look each refund up. (`?.let` runs its lambda only when the lookup found something; lesson 6 covers it.)",
                "code": "val paymentsById = payments.associateBy { it.id }        // 1. one pass: 10,000 entries\nval matched = refunds.mapNotNull { r ->                   // 2. one pass: 2,000 lookups\n    paymentsById[r.paymentId]?.let { p -> p to r }\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Map<String, Payment> paymentsById = payments.stream()\n        .collect(Collectors.toMap(Payment::id, p -> p));       // 1. one pass; throws on a repeated id\nList<Map.Entry<Payment, Refund>> matched = refunds.stream() // 2. one lookup per refund\n        .filter(r -> paymentsById.containsKey(r.paymentId()))\n        .map(r -> Map.entry(paymentsById.get(r.paymentId()), r))\n        .toList();"
            },
            {
                "say": "3. Decide what duplicates and orphans mean. `associateBy` keeps the last payment for a repeated id, so check for repeats first, as the lab does. And `mapNotNull` silently drops refunds whose payment isn't in the day's file. Self-check: is dropping them right? (Usually not. An orphan refund is exactly what reconciliation should report, so split them out with `partition` and keep both lists.)",
                "code": "val (known, orphans) = refunds.partition { it.paymentId in paymentsById }\nval matched = known.map { r -> paymentsById.getValue(r.paymentId) to r }\n// orphans goes into the report instead of disappearing",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Map<Boolean, List<Refund>> split = refunds.stream()\n        .collect(Collectors.partitioningBy(r -> paymentsById.containsKey(r.paymentId())));\nList<Refund> orphans = split.get(false);       // goes into the report instead of disappearing\nList<Map.Entry<Payment, Refund>> matched = split.get(true).stream()\n        .map(r -> Map.entry(paymentsById.get(r.paymentId()), r))\n        .toList();"
            }
        ]
    },
    "lab": {
        "title": "Rewrite the settlement report without loops",
        "minutes": 15,
        "files": [
            "labs/functional/src/main/kotlin/workbench/functional/l04/Report.kt",
            "labs/functional/src/main/kotlin/workbench/functional/l04/Payments.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l04.*'",
        "steps": [
            "Run the tests. All twelve fail with `NotImplementedError`. Open `Payments.kt` and read `settlementReportLoop`, the version you are replacing. Don't edit it.",
            "In `Report.kt`, write `allPayments`, `settledCents`, `refundedCents` and `failedIds`. Each is one chain, and each TODO names the operations.",
            "Write `netByMerchant` with `groupBy` and `mapValues`, and `largestSettled` with `maxByOrNull`. Read the test names first: key order and the null case both count.",
            "Write `closingBalance` with `fold` and a `when` expression inside the lambda.",
            "Write `indexById`: find repeated ids with `groupingBy { it.id }.eachCount()`, throw with `require` if there are any, then `associateBy`.",
            "Write `settlementReport` from the functions above, calling `indexById` first. Run the tests until all twelve pass. Then look at the empty-day and largest-settled tests and work out how `settlementReportLoop` would fail each one."
        ],
        "hints": [
            "`mapValues { (_, ps) -> ps.sumOf { ... } }` destructures each map entry; `_` skips the key you don't need.",
            "`require(condition) { message }` throws `IllegalArgumentException(message)` when the condition is false. `joinToString()` joins with \", \" by default.",
            "`refundCents ?: 0L` turns a missing refund into zero. Write `0L`, not `0`, so the arithmetic stays `Long`."
        ],
        "done_when": "All twelve tests in `SettlementReportTest` pass, and `Report.kt` has no `for` and no `var`."
    },
    "drill": {
        "title": "Write the report chain from memory",
        "minutes": 5,
        "prompt": "Close this page. Given `payments: List<Payment>` with `id`, `merchant`, `amountCents` and `status`, write from memory: the settled total; the settled total per merchant in first-seen order; the number of failed payments; the largest settled payment, or nothing; and a map from id to payment that refuses repeated ids. Then write the same five results with Java streams. Which Java line needs an extra argument to keep the merchant order?",
        "answer": {
            "lang": "kotlin",
            "src": "val settled = payments.filter { it.status == Status.SETTLED }\nval total = settled.sumOf { it.amountCents }\nval perMerchant = settled.groupBy { it.merchant }.mapValues { (_, ps) -> ps.sumOf { it.amountCents } }\nval failedCount = payments.count { it.status == Status.FAILED }\nval largest = settled.maxByOrNull { it.amountCents }          // null when nothing settled\n\nval repeated = payments.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys\nrequire(repeated.isEmpty()) { \"duplicate payment ids: ${repeated.joinToString()}\" }\nval byId = payments.associateBy { it.id }",
            "alt": {
                "lang": "java",
                "src": "List<Payment> settled = payments.stream().filter(p -> p.status() == Status.SETTLED).toList();\nlong total = settled.stream().mapToLong(Payment::amountCents).sum();\nMap<String, Long> perMerchant = settled.stream().collect(Collectors.groupingBy(\n        Payment::merchant, LinkedHashMap::new,                       // the extra argument: keeps the order\n        Collectors.summingLong(Payment::amountCents)));\nlong failedCount = payments.stream().filter(p -> p.status() == Status.FAILED).count();\nOptional<Payment> largest = settled.stream().max(Comparator.comparingLong(Payment::amountCents));\nMap<String, Payment> byId = payments.stream()\n        .collect(Collectors.toMap(Payment::id, p -> p));             // throws on a repeated id"
            }
        }
    },
    "recap": [
        "`map`, `filter`, `mapNotNull` and `flatMap` each do one job and return a new list. Read a chain top to bottom, one job per line.",
        "Kotlin's operations on a `List` are eager: each step builds a whole new `ArrayList`. They are `inline`, so the lambdas cost nothing; the intermediate lists are the cost.",
        "`fold(initial) { acc, x -> ... }` is the general loop with its `var` hidden inside. `sumOf`, `count` and `maxByOrNull` are named special cases; prefer them when they fit.",
        "On an empty list, `reduce` throws `UnsupportedOperationException: Empty collection can't be reduced.` and `first()` throws `NoSuchElementException: List is empty.` Use `fold`, `sumOf` or the `OrNull` functions when input can be empty.",
        "`groupBy` keeps first-seen key order in a `LinkedHashMap`. Java's `groupingBy` promises no order unless you pass `LinkedHashMap::new`.",
        "`associateBy` silently keeps the last element for a repeated key, where Java's `toMap` throws. When keys should be unique, check for repeats first."
    ],
    "quiz": [
        {
            "q": "On a day with no payments, what does `payments.filter { it.status == SETTLED }.sumOf { it.amountCents }` return?",
            "options": [
                "0",
                "It throws `NoSuchElementException`",
                "null",
                "It throws `UnsupportedOperationException`"
            ],
            "answer": 0,
            "why": "`sumOf` is a fold that starts from zero, so an empty list sums to 0. `filter` on an empty list returns an empty list without complaint. The exceptions belong to `first()`, `maxOf` and `reduce`, which have no starting value to fall back on."
        },
        {
            "q": "`listOf(p1, p3).associateBy { it.merchant }`, where both payments (ids `pay_1` and `pay_3`) are for `acme`. What do you get?",
            "options": [
                "`IllegalStateException: Duplicate key acme`",
                "A map with only `acme -> pay_3`, and no warning",
                "`acme -> [pay_1, pay_3]`",
                "A map with only `acme -> pay_1`"
            ],
            "answer": 1,
            "why": "`associateBy` keeps the last element for a repeated key and says nothing. The exception is what Java's `Collectors.toMap` does, which is why the first option is tempting. If you want every payment per key, use `groupBy`; if a repeat is a bug, check with `groupingBy { }.eachCount()` first."
        },
        {
            "q": "Which operation gives you \"the refund amounts, for the payments that have one\" as a `List<Long>`?",
            "options": [
                "`map { it.refundCents }`",
                "`filter { it.refundCents != null }`",
                "`mapNotNull { it.refundCents }`",
                "`flatMap { it.refundCents }`"
            ],
            "answer": 2,
            "why": "`mapNotNull` transforms each payment and drops the null results in one step. `map` gives a `List<Long?>` with nulls in it, `filter` gives payments rather than amounts, and `flatMap` needs a lambda that returns a collection, so it doesn't compile here."
        },
        {
            "q": "Payments arrive from merchants globex, acme, globex, initech, in that order. In what order does `groupBy { it.merchant }` return the keys?",
            "options": [
                "Alphabetical: acme, globex, initech",
                "Hash order, as Java's `groupingBy` gives",
                "Last-seen order: acme, globex, initech",
                "First-seen order: globex, acme, initech"
            ],
            "answer": 3,
            "why": "Kotlin's `groupBy` builds a `LinkedHashMap` and documents that keys keep the order in which they were first produced. Java's `groupingBy` promises no particular map, and on JDK 21 it gave a `HashMap` in hash order. Nothing in either sorts the keys."
        },
        {
            "q": "From the last lesson: `payments.filter { it.amountCents > minCents }` on a `List` creates no lambda object, even though the lambda captures `minCents`. Why?",
            "options": [
                "`filter` is `inline`, so the lambda's body is pasted into the loop inside the calling function",
                "Kotlin caches capturing lambdas, one per call site",
                "The JIT removes the object at runtime",
                "Capturing a `val` never needs an object"
            ],
            "answer": 0,
            "why": "An inline function's lambda never becomes an object: the compiler copies `filter`'s loop and the lambda's body into your method, and `minCents` is just a local it reads. Without `inline` a capturing lambda is a new object per evaluation (lesson 2), whether it captures a `val` or a `var`. Caching only applies to lambdas that capture nothing.",
            "from": "fp-03"
        }
    ],
    "flashcards": [
        {"front": "What does `reduce` do on an empty list?", "back": "It throws `UnsupportedOperationException: Empty collection can't be reduced.` Use `fold` with a starting value, or `reduceOrNull`."},
        {"front": "What does `emptyList<Long>().first()` throw?", "back": "`NoSuchElementException: List is empty.` `firstOrNull()` returns null instead."},
        {"front": "`associateBy` meets a repeated key. What happens?", "back": "The last element wins, silently. Java's `Collectors.toMap` throws `IllegalStateException: Duplicate key ...` instead."},
        {"front": "In what key order does Kotlin's `groupBy` return its map?", "back": "First-seen order: it returns a `LinkedHashMap`. Java's `groupingBy` promises no order (it was a `HashMap` on JDK 21)."},
        {"front": "What does `mapNotNull { it.refundCents }` replace?", "back": "`map { it.refundCents }.filterNotNull()`, building one list instead of two."},
        {"front": "How do you find repeated ids before indexing a list?", "back": "`payments.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys`"},
        {"front": "Is `payments.filter { }.map { }` on a `List` lazy?", "back": "No. Each step runs over the whole list and returns a new `ArrayList`. Sequences, in the next lesson, are lazy."}
    ],
    "terms": [
        {"term": "map", "plain": "Transform every element: the same number of elements comes out, in the same order."},
        {"term": "filter", "plain": "Keep the elements that pass a test."},
        {"term": "flatMap", "plain": "Turn each element into a collection and join them all into one list."},
        {"term": "fold", "plain": "Combine all elements into one result, starting from a given value. The general loop."},
        {"term": "Accumulator", "plain": "The value `fold` carries from one element to the next, and finally returns."},
        {"term": "Eager operation", "plain": "One that runs over the whole collection at once and returns a new collection."},
        {"term": "associateBy", "plain": "Build a map with one element per key. For a repeated key, the last element wins."}
    ],
    "explain_back": {
        "prompt": "A teammate who likes loops asks why the chain version of the settlement report fixed two bugs nobody was hunting for, and what the chain costs that the loop doesn't. Explain it in your own words.",
        "answer": "The loop built four results at once with mutable variables, so each one depended on details spread over the whole loop. `largest` started from `payments.first()`, which crashes on an empty day and, on a normal day, starts from whatever payment came first, even a pending one. In the chain, each result is computed on its own from the list. `largest` is `maxByOrNull` over the settled payments only, so it can't pick an unsettled payment and returns null when there are none, and no line assumes there is a first element. The cost is allocation: Kotlin's list operations are eager, so each `filter` or `map` builds a whole new list, where the loop made one pass and built nothing extra. The lambdas themselves are free because the functions are inline. For a few thousand payments that cost doesn't matter; for millions I'd fuse steps or use a sequence."
    },
    "deeper": {
        "minutes": 10,
        "body": "A few more operations earn a place in payment code.\n\n`runningFold` (also called `scan`) is `fold` that keeps every intermediate value, which is exactly a running balance. Over the amounts `[1500, 9900, 2000, 12000, 700]`, `runningFold(0L) { acc, x -> acc + x }` gives `[0, 1500, 11400, 13400, 25400, 26100]`: one more element than the input, because it includes the starting value. `runningReduce` leaves the starting value out.\n\n```kotlin\nval balances = amounts.runningFold(0L) { acc, x -> acc + x }   // [0, 1500, 11400, 13400, 25400, 26100]\nval firstOverdraft = balances.indexOfFirst { it < 0 }          // -1 when the account never goes negative\n```\n\n```java\n// JDK 21 streams have no running fold; a loop is the plain answer.\nList<Long> balances = new ArrayList<>(List.of(0L));\nfor (long x : amounts) balances.add(balances.get(balances.size() - 1) + x);\n// JDK 24 added java.util.stream.Gatherers, with scan(...) and windowFixed(...) as intermediate operations.\n```\n\n`chunked(100)` splits payouts into batches for an API that accepts at most 100 per call, and the last chunk may be smaller: `listOf(1, 2, 3, 4, 5).chunked(2)` is `[[1, 2], [3, 4], [5]]`. `windowed(7)` gives sliding windows for a seven-day moving average. `zip` pairs two lists element by element and quietly stops at the shorter one, so zipping 10 expected settlements with 9 actual ones loses the 10th without a word: compare the sizes first.\n\nOne caution from the other direction. Kotlin's `forEach` is inline, so a `return` inside its lambda returns from the enclosing function and skips every remaining element. Java developers expect `continue`-like behaviour from `Stream.forEach`. Use `return@forEach` to skip one element, or better, express the skip with `filter`."
    },
    "sources": [
        {"title": "Collection transformations (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-transformations.html"},
        {"title": "Aggregate operations (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-aggregate.html"},
        {"title": "Grouping (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-grouping.html"},
        {"title": "Collections in Java and Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html"},
        {"title": "Collectors (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Collectors.html"}
    ]
}

out = ROOT / "content/lessons/fp-04.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
