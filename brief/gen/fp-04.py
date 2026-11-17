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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# fold as a picture: the jar's weight flows left to right, each cookie changes it (or not)
ACC = [("200", "box-b"), ("245", "box"), ("245", "box"), ("285", "box"), ("285", "box"), ("315", "box-ok")]
COOKIES = [("c1 GOLDEN", "+45", "box-a"), ("c2 RAW", "+0", "box-dim"), ("c3 GOLDEN", "+50 - 10", "box-a"),
           ("c4 BURNT", "+0", "box-dim"), ("c5 GOLDEN", "+30", "box-a")]
parts = []
for i, (label, cls) in enumerate(ACC):
    x = 20 + i * 115
    parts.append(f'<rect class="{cls}" x="{x}" y="150" width="90" height="38" rx="8"/>'
                 f'<text class="t-s t-code" x="{x + 45}" y="174" text-anchor="middle">{label}</text>')
    if i < len(ACC) - 1:
        parts.append(f'<line class="ln-a" x1="{x + 90}" y1="169" x2="{x + 113}" y2="169" marker-end="url(#arr)"/>')
for i, (name, delta, cls) in enumerate(COOKIES):
    cx = 122 + i * 115
    parts.append(f'<rect class="{cls}" x="{cx - 52}" y="44" width="104" height="52" rx="8"/>'
                 f'<text class="t-s" x="{cx}" y="65" text-anchor="middle">{name}</text>'
                 f'<text class="t-s t-code" x="{cx}" y="85" text-anchor="middle">{delta}</text>'
                 f'<line class="ln-d" x1="{cx}" y1="96" x2="{cx}" y2="162" marker-end="url(#arr)"/>')
FIG = (
    '<svg viewBox="0 0 700 230" role="img" aria-label="fold as a picture. The accumulator starts at the 200 g already in the cookie jar and moves left to right. '
    'Each cookie changes it: golden ones add their weight minus any bite, raw and burnt ones add nothing. It ends at 315 g.">'
    '<text class="t-s t-code" x="350" y="24" text-anchor="middle">cookies.fold(200) { jar, c -&gt; ... }</text>'
    + "".join(parts)
    + '<text class="t-s t-m" x="20" y="212">in the jar</text>'
    + '<text class="t-s t-m" x="680" y="212" text-anchor="end">result</text>'
    + '<text class="t-s t-m" x="350" y="212" text-anchor="middle">the accumulator carries the jar from one cookie to the next</text>'
    + '</svg>'
)

OPENING = """Picture a baking day. Two trays of cookies come out of the oven. Most are golden, one is burnt, one is still raw in the middle, and someone has already taken a bite of another. You want to know a few things: how much good cookie there is, by flavor, which ones to throw away, and which golden one is the biggest.

Nobody does that by saying "for each cookie, if it's golden, add it to this pile, and if it's burnt...". You take out the burnt ones, sort the rest by flavor, and weigh each pile. Each job is one step.

Code usually says "for each cookie" anyway. One loop builds four results at once, every line changes one of them, and it works fine until a day when nothing was baked. The last lesson, on higher-order functions, wrote functions that take functions. Kotlin's collection library is a set of them, ready-made.

In this lesson, we'll watch a report loop fail on an empty day, then rebuild it from `map`, `filter`, `fold` and their friends, with the trap each one hides. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_LOOP = """int golden = 0;
Map<String, Integer> net = new LinkedHashMap<>();
List<String> burnt = new ArrayList<>();
Cookie largest = cookies.get(0);
for (Cookie c : cookies) {
    switch (c.status()) {
        case GOLDEN -> {
            golden += c.grams();
            net.merge(c.flavor(), c.grams() - biteOf(c), Integer::sum);
            if (c.grams() > largest.grams()) largest = c;
        }
        case BURNT -> burnt.add(c.id());
        case RAW -> { }
    }
}"""
K_LOOP = """var golden = 0
val net = LinkedHashMap<String, Int>()
val burnt = ArrayList<String>()
var largest = cookies.first()
for (c in cookies) {
    when (c.status) {
        Status.GOLDEN -> {
            golden += c.grams
            net[c.flavor] = (net[c.flavor] ?: 0) + c.grams - (c.nibbledGrams ?: 0)
            if (c.grams > largest.grams) largest = c
        }
        Status.BURNT -> burnt.add(c.id)
        Status.RAW -> {}
    }
}"""
J_CHAIN = """List<Cookie> goldenCookies = cookies.stream().filter(c -> c.status() == GOLDEN).toList();
int golden = goldenCookies.stream().mapToInt(Cookie::grams).sum();
Map<String, Integer> net = goldenCookies.stream().collect(Collectors.groupingBy(
        Cookie::flavor, LinkedHashMap::new, Collectors.summingInt(c -> c.grams() - biteOf(c))));
List<String> burnt = cookies.stream().filter(c -> c.status() == BURNT).map(Cookie::id).toList();
Optional<Cookie> largest = goldenCookies.stream().max(Comparator.comparingInt(Cookie::grams));"""
K_CHAIN = """val goldenCookies = cookies.filter { it.status == Status.GOLDEN }
val golden = goldenCookies.sumOf { it.grams }
val net = goldenCookies.groupBy { it.flavor }
    .mapValues { (_, cs) -> cs.sumOf { it.grams - (it.nibbledGrams ?: 0) } }
val burnt = cookies.filter { it.status == Status.BURNT }.map { it.id }
val largest = goldenCookies.maxByOrNull { it.grams }"""

S0 = """Here is the end-of-day report the way most of us first write it. A `Cookie` has an id, a flavor, its weight in grams from the kitchen scale, a status (`GOLDEN`, `RAW` or `BURNT`) and `nibbledGrams`, which is null unless someone took a bite. One pass over the cookies builds four results:

""" + pair(J_LOOP, K_LOOP) + """

It works on a normal day. It's also hard to read, for a reason you can name: four results are being built at the same time, interleaved, and every line changes one of them. To check how `largest` is worked out, you have to read the whole loop, because any line might touch it.

And it has two bugs that a normal day never shows. On a day with no cookies, `cookies.first()` throws `NoSuchElementException: List is empty.` (Java's `get(0)` throws an `ArrayIndexOutOfBoundsException`). And say the first cookie of the day is a raw one of 99 g. `largest` starts there, no golden cookie beats it, and the report proudly names a cookie that is still dough.

Here is the same report written with collection operations. Each one is a function from the standard library that takes a lambda and does one job over the whole list:

""" + pair(J_CHAIN, K_CHAIN) + """

Each result is one `val`, computed from the list, and each line says what it computes rather than how to walk the list. The `ReportLoop` demo prints both versions:

```text
chain: golden=125 net={oat=85, chocolate=30} burnt=[c4] largest=c3
loop:  golden=125 net={oat=85, chocolate=30} burnt=[c4] largest=c3
```

Same answers on a normal day. Both bugs are gone without anyone hunting for them: `maxByOrNull` only ever sees golden cookies and returns null for an empty list, and nothing assumes there is a first element.

**Give each result its own chain. A loop that fills four piles at once makes every line a suspect.**

The rest of this lesson takes those operations one at a time, with the trap that comes with each."""

# ---------------------------------------------------------------- section 1
J_OPS = """List<Integer> bites = cookies.stream()
        .map(Cookie::nibbledGrams)
        .filter(Objects::nonNull)
        .toList();                                          // [10]
List<String> ids = trays.stream()
        .flatMap(t -> t.cookies().stream())
        .map(Cookie::id)
        .toList();
boolean anyBig = cookies.stream().anyMatch(c -> c.grams() > 75);"""
K_OPS = """val bites = cookies.mapNotNull { it.nibbledGrams }        // [10]
val ids = trays.flatMap { it.cookies }.map { it.id }
val anyBig = cookies.any { it.grams > 75 }"""

S1 = """Each collection operation does one job and returns a new collection, so you read a chain top to bottom, one job per line. In the kitchen: weigh every cookie, set aside the burnt ones, tip both trays onto one rack.

- `map` transforms every element: `cookies.map { it.grams }` gives one weight per cookie, in the same order.
- `filter` keeps the elements that pass a test: `cookies.filter { it.status == GOLDEN }`.
- `mapNotNull` transforms and drops the nulls in one step. `cookies.mapNotNull { it.nibbledGrams }` gives just the bites, `[10]` on the sample day. It replaces `map { ... }.filterNotNull()` and builds one list instead of two.
- `flatMap` turns each element into a list and joins the lists: `trays.flatMap { it.cookies }` turns a day of trays into one list of cookies.

Then come the operations that boil a list down to one answer: `sumOf`, `count { }`, `any { }`, `all { }`, `none { }`, `first { }` and `maxByOrNull { }`. Several of them take a **predicate**, a function that answers true or false. Those stop at the first element that decides the answer, so `any` stops at its first match.

Java has the same operations on streams. A **stream** is Java's pipeline object: you make one from a collection with `.stream()`, add steps, and finish with an operation such as `toList()` or `sum()`. Side by side:

""" + pair(J_OPS, K_OPS) + """

The difference that matters isn't the syntax. A Java stream is **lazy**: nothing runs until the last operation, and then each element travels through the whole pipeline. Kotlin's operations on a `List` are **eager**: `filter` runs over the whole list and returns a new `ArrayList`, then `map` runs over that one and returns another. Every step builds a full list in between.

As the last lesson showed, the lambdas cost nothing, because these functions are `inline`. The lists are the cost. For a day of a few hundred cookies that's nothing. For a million rows and five steps it starts to matter, and the next lesson's sequences are the fix.

This is also where the tray picture breaks. In a kitchen, cookies move along one at a time: you weigh one and pass it on. Kotlin's list operations finish the whole tray before the next step starts, onto a fresh tray each time.

One rule keeps a chain honest: no side effects inside it. A `map` that also writes to a file, or a `filter` that bumps a counter, brings back exactly the hidden state that lesson 1 removed. Effects go at the end, in a `forEach`, or better, in the shell from lesson 1.

**A chain computes and the shell acts. Keep side effects out of map and filter.**

Most of these operations are named versions of one general loop. The next section gives it its name."""

# ---------------------------------------------------------------- section 2
J_FOLD = """int jar = cookies.stream().reduce(200,
        (acc, c) -> c.status() == GOLDEN ? acc + c.grams() - biteOf(c) : acc,
        Integer::sum);                  // the third argument only matters for parallel streams"""
K_FOLD = """val jar = cookies.fold(200) { jar, c ->
    when (c.status) {
        Status.GOLDEN -> jar + c.grams - (c.nibbledGrams ?: 0)
        Status.RAW, Status.BURNT -> jar
    }
}"""

S2 = """Every loop that builds one result has the same two parts: a starting value, and a step that combines the result so far with the next element. `fold` is that loop with both parts passed in.

Our example is the cookie jar. It already holds 200 g. At the end of the day each golden cookie goes in, minus any bite, and the raw and burnt ones stay out:

""" + pair(J_FOLD, K_FOLD) + """

The value carried from one step to the next is the **accumulator**, `jar` here. Picture yourself at the jar with the kitchen scale. You carry one number, the jar's weight, past each cookie in turn, and each cookie either changes it or doesn't. The figure below walks it from 200 g to 315 g.

The standard library's `fold` is the loop you'd write by hand: `var accumulator = initial; for (element in this) accumulator = operation(accumulator, element); return accumulator`. It's `inline`, so your lambda is pasted into that loop. The `var` still exists, but it lives inside `fold` where nothing else can touch it, and your own code has only `val`s.

`sumOf`, `count`, `maxByOrNull` and `joinToString` are all special cases of `fold`, already written and named. Prefer them when they fit, because `sumOf { it.grams }` says more than `fold(0) { acc, c -> acc + c.grams }`. Reach for `fold` when the step needs a `when`, as the jar does, or when the accumulator is something richer than a number.

`reduce` looks like `fold` without the starting value. It uses the first element as the start instead, and that's the trap: an empty list has no first element. Here's what Kotlin 2.4.21 does with an empty list of weights, from the `EmptyTraps` demo:

```text
fold(0) { a, b -> a + b }        0
sum()                            0
reduceOrNull { a, b -> a + b }   null
reduce { a, b -> a + b }         throws java.lang.UnsupportedOperationException: Empty collection can't be reduced.
first()                          throws java.util.NoSuchElementException: List is empty.
firstOrNull()                    null
maxOf { it }                     throws java.util.NoSuchElementException
maxOrNull()                      null
```

Java chose differently. `Stream.reduce` without a starting value returns an `Optional`, a box that may be empty, so the type makes you handle the empty case. Kotlin gives you two names instead, a throwing one and an `OrNull` one.

**An empty list is a normal day. Use fold, sumOf or an OrNull function when the input can be empty.**

Keep `reduce` and `first()` for the places where an empty list is a bug you want to hear about loudly.

Folding gives one answer. Reports usually want an answer per flavor or per tray, and that means a map."""

# ---------------------------------------------------------------- section 3
J_GROUP = """Map<String, List<String>> byFlavor = cookies.stream().collect(
        Collectors.groupingBy(Cookie::flavor, Collectors.mapping(Cookie::id, Collectors.toList())));
// {oat=[c1, c3], ginger=[c4], chocolate=[c2, c5]}   a HashMap: no order promised"""
K_GROUP = """val byFlavor = cookies.groupBy({ it.flavor }, { it.id })
// {oat=[c1, c3], chocolate=[c2, c5], ginger=[c4]}   a LinkedHashMap: first-seen order"""
J_ASSOC = """Map<String, String> oneEach = cookies.stream()
        .collect(Collectors.toMap(Cookie::flavor, Cookie::id));
// throws IllegalStateException: Duplicate key oat (attempted merging values c1 and c3)"""
K_ASSOC = """val oneEach = cookies.associateBy({ it.flavor }, { it.id })
// {oat=c3, chocolate=c5, ginger=c4}   c1 and c2 are gone, without a word"""

S3 = """Reports are mostly maps: grams per flavor, cookies by id, counts per status. A **map** is a lookup table from keys to values. Three operations build one from a list, and each has a behaviour worth knowing before it surprises you.

`groupBy` puts every element into a list under its key, like sorting cookies into jars by flavor:

""" + pair(J_GROUP, K_GROUP) + """

Kotlin's `groupBy` returns a `LinkedHashMap`, a map that remembers the order its keys arrived in. Its documentation promises that keys keep the order in which they were first seen. Java's `groupingBy` promises nothing about the map it returns. On JDK 21 it was a plain `HashMap`, which keeps keys in an order of its own, and it put `ginger` before `chocolate`.

If a report must list flavors in the order they came out of the oven, Kotlin does that for you, and in Java you pass `LinkedHashMap::new`. When you only need a number per group, `groupingBy { it.flavor }.eachCount()` computes it in one pass. So does `groupingBy { it.flavor }.fold(0) { acc, c -> acc + c.grams }`, and neither builds a list for each group.

`associateBy` builds a map with one element per key. Here the two languages part ways:

""" + pair(J_ASSOC, K_ASSOC) + """

When two elements share a key, `associateBy` keeps the last one and says nothing. Java's `toMap` throws. For cookies keyed by an id that should be unique, Java's behaviour is the one you want.

Say someone writes the second tray down twice. The same cookies arrive twice, `associateBy` quietly keeps one copy of each, and nobody hears about the mistake. So check before you index. `cookies.groupingBy { it.id }.eachCount().filterValues { it > 1 }` lists every repeated id, and the lab's `indexById` refuses a day that has any.

**associateBy keeps the last value for a repeated key, without a word. Check for repeats first.**

`partition` splits a list in two by a predicate, and destructuring (unpacking a pair into two `val`s) makes it read well: `val (golden, rest) = cookies.partition { it.status == GOLDEN }`. Java's version is `Collectors.partitioningBy`, which returns a `Map<Boolean, List<Cookie>>`.

With these, the report from the first section is complete, and the lab builds it. Every one of these operations shares the limit from the second section, though: each step builds a whole new list or map before the next one starts."""

L = {
    "id": "fp-04",
    "title": "Collections without loops: map, filter, fold and friends",
    "minutes": 38,
    "goal": "By the end you can rewrite a loop that builds several results into a few collection operations, pick the right one for each job, use fold as the general loop, and avoid the empty-list and duplicate-key traps in both Kotlin and Java.",
    "opening": OPENING,
    "warmup": {
        "q": "On a day when nothing was baked, `cookies` is empty. What does `cookies.reduce { a, b -> if (a.grams >= b.grams) a else b }` do?",
        "options": [
            "Returns null",
            "Throws `UnsupportedOperationException: Empty collection can't be reduced.`",
            "Returns an empty `Optional`, like Java's `Stream.reduce`",
            "Doesn't compile, because `reduce` needs a starting value"
        ],
        "answer": 1,
        "why": "`reduce` starts from the first element, and an empty list has none, so Kotlin throws. Java's `Stream.reduce` without a starting value returns `Optional.empty`, which is why the third option is tempting. In Kotlin you choose explicitly: `reduceOrNull`, `maxByOrNull`, or `fold` with a starting value. The section on fold lines them all up."
    },
    "sections": [
        {
            "h": "A baking-day report written as one loop, and the two bugs it hides",
            "body": S0,
            "try": {
                "title": "Break the loop with an empty day",
                "minutes": 4,
                "steps": [
                    "Run `ReportLoop` (or `ReportLoopJava`). Check that the loop and the chain agree on the sample day.",
                    "Run it again with `-Pargs=empty` added. Predict first: which version survives a day with no cookies?",
                    "Put a raw cookie of 99 g at the front of the sample day, `Cookie(\"c0\", \"oat\", 99, Status.RAW)` in `sampleDay` in `SampleDay.kt` (Java: `new Cookie(\"c0\", \"oat\", 99, Status.RAW, null)` in `DAY`), and run once more. Compare the two `largest` values."
                ],
                "code": kdemo("ReportLoop"),
                "expect": "On the sample day both print `golden=125 net={oat=85, chocolate=30} burnt=[c4] largest=c3`. On the empty day the chain prints zeros, an empty map and `largest=null`, and the loop throws `java.util.NoSuchElementException: List is empty.` (Java: `ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0`). With the big raw cookie first, the loop reports that raw cookie as the largest; the chain still says `c3`."
            }
        },
        {
            "h": "One job per step: map, filter, mapNotNull and flatMap",
            "body": S1,
            "try": {
                "title": "Predict each line",
                "minutes": 4,
                "steps": [
                    "Open `Operations.kt` (or `OperationsJava.java`) and the sample day in `SampleDay.kt`. Predict every line of output, then run it.",
                    "Replace `mapNotNull { it.nibbledGrams }` with `map { it.nibbledGrams }` and run. What changed? Then add `.sum()` after it and read the compiler's answer.",
                    "Look at the last line. What class does each step return?"
                ],
                "code": kdemo("Operations"),
                "expect": "`map` gives all five weights, `[45, 90, 50, 80, 30]`, `filter` gives `[c1, c3, c5]`, `mapNotNull` gives `[10]`, `flatMap` gives the five ids in tray order, `sumOf` 295, `count` 3, `any / all` `true / true`, and `partition` `[c1, c3, c5] / [c2, c4]`. Plain `map` gives `[null, null, 10, null, null]`, a `List<Int?>`, and `.sum()` on it fails with `none of the following candidates is applicable`, because `sum` only exists for lists of non-null numbers. Kotlin's `map` returns a fresh `java.util.ArrayList`; Java's `toList()` returns an unmodifiable `ImmutableCollections$ListN`."
            },
            "refs": [
                {"title": "Collection transformations: map, flatMap, associate (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-transformations.html", "kind": "docs"},
                {"title": "Collections in Java and Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html", "kind": "docs"}
            ]
        },
        {
            "h": "The loop you were writing is a fold",
            "body": S2,
            "figure": {"svg": FIG, "caption": "fold carries one value, the accumulator, past every cookie. Each cookie makes the next value from the last, like a jar weighed after each one goes in."},
            "try": {
                "title": "Empty-list traps, both languages",
                "minutes": 3,
                "steps": [
                    "Run `EmptyTraps` (or `EmptyTrapsJava`). Before you look, mark each line: a value, or an exception?",
                    "Change `none` to `listOf(45, 50)` (Java: `List.of(45, 50)`) and predict each line again before running.",
                    "In your own code, search for `.first()` and `.reduce {`. For each hit, ask whether that list can be empty on a quiet day."
                ],
                "code": kdemo("EmptyTraps"),
                "expect": "On the empty list, `fold` and `sum` give 0; `reduceOrNull`, `firstOrNull` and `maxOrNull` give null; `reduce`, `first()` and `maxOf` throw, with the messages in the table above. The Java version prints 0 for both sums and `Optional.empty` for `reduce` without a starting value, for `findFirst()` and for `max`. It throws `NoSuchElementException: No value present` from `orElseThrow()` and `ArrayIndexOutOfBoundsException` from `get(0)`. With two weights every line returns a value: 95 for the folds, sums and reduces, 45 for `first()`, 50 for the max."
            },
            "refs": [
                {"title": "Aggregate operations: fold, reduce and the OrNull variants (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-aggregate.html", "kind": "docs"}
            ]
        },
        {
            "h": "From a list to a map: groupBy, associateBy and partition",
            "body": S3,
            "try": {
                "title": "Find the line that loses data",
                "minutes": 4,
                "steps": [
                    "Run `DuplicateKeys` (or `DuplicateKeysJava`). Compare the key order of Kotlin's `groupBy` with Java's `groupingBy`.",
                    "Find the line that loses data without telling you. Which cookies are missing from it?",
                    "In the Java version, give `toMap` a third argument, `(a, b) -> b`, and run. In the Kotlin version, add a line that prints the repeated flavors: `groupingBy { it.flavor }.eachCount().filterValues { it > 1 }.keys`."
                ],
                "code": kdemo("DuplicateKeys"),
                "expect": "Kotlin prints `oat, chocolate, ginger` in first-seen order, from a `java.util.LinkedHashMap`. Java's `groupingBy` prints `oat, ginger, chocolate`, from a `java.util.HashMap`. `associateBy` keeps `c3`, `c5` and `c4`: `c1` and `c2` vanished silently. Java's plain `toMap` throws `IllegalStateException: Duplicate key oat (attempted merging values c1 and c3)`; with `(a, b) -> b` it keeps the last value and behaves exactly like `associateBy`. The repeated flavors are `[oat, chocolate]`."
            },
            "refs": [
                {"title": "Grouping (Kotlin docs)", "url": "https://kotlinlang.org/docs/collection-grouping.html", "kind": "docs"},
                {"title": "Collectors: toMap and groupingBy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Collectors.html", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "The baking-day report with streams and with Kotlin collection functions",
        "java": {
            "title": "Report.java",
            "src": "static BakeReport report(List<Tray> trays) {\n    List<Cookie> cookies = trays.stream().flatMap(t -> t.cookies().stream()).toList();\n    Map<String, Cookie> byId = cookies.stream()\n            .collect(Collectors.toMap(Cookie::id, c -> c));               // throws on a repeated id\n\n    List<Cookie> golden = cookies.stream().filter(c -> c.status() == GOLDEN).toList();\n    return new BakeReport(\n            cookies.size(),\n            golden.stream().mapToInt(Cookie::grams).sum(),\n            cookies.stream().map(Cookie::nibbledGrams).filter(Objects::nonNull)\n                    .mapToInt(Integer::intValue).sum(),\n            golden.stream().collect(Collectors.groupingBy(Cookie::flavor,\n                    LinkedHashMap::new,                                     // or no order is promised\n                    Collectors.summingInt(c -> c.grams() - biteOf(c)))),\n            cookies.stream().filter(c -> c.status() == BURNT).map(Cookie::id).toList(),\n            golden.stream().max(Comparator.comparingInt(Cookie::grams)));   // Optional<Cookie>\n}"
        },
        "kotlin": {
            "title": "Report.kt",
            "src": "fun report(trays: List<Tray>): BakeReport {\n    val cookies = trays.flatMap { it.cookies }\n    val repeated = cookies.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys\n    require(repeated.isEmpty()) { \"duplicate cookie ids: ${repeated.joinToString()}\" }   // associateBy would not\n\n    val golden = cookies.filter { it.status == GOLDEN }\n    return BakeReport(\n        cookieCount = cookies.size,\n        goldenGrams = golden.sumOf { it.grams },\n        nibbledGrams = cookies.mapNotNull { it.nibbledGrams }.sum(),\n        netByFlavor = golden.groupBy { it.flavor }                         // first-seen order\n            .mapValues { (_, cs) -> cs.sumOf { it.grams - (it.nibbledGrams ?: 0) } },\n        burntIds = cookies.filter { it.status == BURNT }.map { it.id },\n        largestGolden = golden.maxByOrNull { it.grams },                   // Cookie?, null when none\n    )\n}"
        },
        "note": "The vocabulary is nearly the same, and the defaults are not. Java streams are lazy and single-use and finish with a collector; Kotlin's list functions are eager, return ordinary lists and maps, and can be called again on the same list. Java says \"maybe nothing\" with `Optional`, Kotlin with a nullable type and the `OrNull` functions. Java's `groupingBy` promises no key order unless you pass a map factory, while Kotlin's `groupBy` keeps first-seen order. And the duplicate-key defaults are opposite: Java's `toMap` throws, Kotlin's `associateBy` keeps the last value, so in Kotlin the duplicate check is your job."
    },
    "worked": {
        "title": "Rewrite a nested-loop match of reviews to recipes",
        "steps": [
            {
                "say": "A recipe site matches each review to the recipe it belongs to, by `recipeId`. Here is a direct translation of two nested loops into a chain. Before reading on, estimate how many comparisons it makes for 10,000 recipes and 2,000 reviews.",
                "code": "val matched = recipes.flatMap { r ->\n    reviews.filter { it.recipeId == r.id }.map { rv -> r to rv }\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "List<Map.Entry<Recipe, Review>> matched = recipes.stream()\n        .flatMap(r -> reviews.stream()\n                .filter(rv -> rv.recipeId().equals(r.id()))\n                .map(rv -> Map.entry(r, rv)))\n        .toList();"
            },
            {
                "say": "1. Count the work. The inner `filter` runs over every review for every recipe: 10,000 x 2,000 = 20 million comparisons, plus one small list per recipe. A chain is no faster than the loop it replaced; it only reads better. 2. Index once instead: build a map from id to recipe, then look each review up. (`?.let` runs its lambda only when the lookup found something; lesson 6 covers it.)",
                "code": "val recipesById = recipes.associateBy { it.id }          // 1. one pass: 10,000 entries\nval matched = reviews.mapNotNull { rv ->                    // 2. one pass: 2,000 lookups\n    recipesById[rv.recipeId]?.let { r -> r to rv }\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Map<String, Recipe> recipesById = recipes.stream()\n        .collect(Collectors.toMap(Recipe::id, r -> r));          // 1. one pass; throws on a repeated id\nList<Map.Entry<Recipe, Review>> matched = reviews.stream()    // 2. one lookup per review\n        .filter(rv -> recipesById.containsKey(rv.recipeId()))\n        .map(rv -> Map.entry(recipesById.get(rv.recipeId()), rv))\n        .toList();"
            },
            {
                "say": "3. Decide what duplicates and orphans mean. `associateBy` keeps the last recipe for a repeated id, so check for repeats first, as the lab does. And `mapNotNull` silently drops reviews whose recipe isn't in the list, say because it was deleted. Self-check: is dropping them right? (Usually not. An orphan review is worth reporting, so split them out with `partition` and keep both lists.)",
                "code": "val (known, orphans) = reviews.partition { it.recipeId in recipesById }\nval matched = known.map { rv -> recipesById.getValue(rv.recipeId) to rv }\n// orphans goes into the report instead of disappearing",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Map<Boolean, List<Review>> split = reviews.stream()\n        .collect(Collectors.partitioningBy(rv -> recipesById.containsKey(rv.recipeId())));\nList<Review> orphans = split.get(false);       // goes into the report instead of disappearing\nList<Map.Entry<Recipe, Review>> matched = split.get(true).stream()\n        .map(rv -> Map.entry(recipesById.get(rv.recipeId()), rv))\n        .toList();"
            }
        ]
    },
    "lab": {
        "title": "Rewrite the baking-day report without loops",
        "minutes": 15,
        "files": [
            "labs/functional/src/main/kotlin/workbench/functional/l04/Report.kt",
            "labs/functional/src/main/kotlin/workbench/functional/l04/Cookies.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l04.*'",
        "steps": [
            "Run the tests. All twelve fail with `NotImplementedError`. Open `Cookies.kt` and read `bakeReportLoop`, the version you are replacing. Don't edit it. A `Tray` is one tray out of the oven, and a baking day is a list of trays.",
            "In `Report.kt`, write `allCookies`, `goldenGrams`, `nibbledGrams` and `burntIds`. Each is one chain, and each TODO names the operations.",
            "Write `netByFlavor` with `groupBy` and `mapValues`, and `largestGolden` with `maxByOrNull`. Read the test names first: key order and the null case both count.",
            "Write `jarGrams` with `fold` and a `when` expression inside the lambda.",
            "Write `indexById`: find repeated ids with `groupingBy { it.id }.eachCount()`, throw with `require` if there are any, then `associateBy`.",
            "Write `bakeReport` from the functions above, calling `indexById` first. Run the tests until all twelve pass. Then look at the empty-day and largest-golden tests and work out how `bakeReportLoop` would fail each one."
        ],
        "hints": [
            "`mapValues { (_, cs) -> cs.sumOf { ... } }` destructures each map entry; `_` skips the key you don't need.",
            "`require(condition) { message }` throws `IllegalArgumentException(message)` when the condition is false. `joinToString()` joins with \", \" by default.",
            "`nibbledGrams ?: 0` turns a missing bite into zero, so the subtraction works for every golden cookie."
        ],
        "done_when": "All twelve tests in `BakeReportTest` pass, and `Report.kt` has no `for` and no `var`."
    },
    "drill": {
        "title": "Write the report chain from memory",
        "minutes": 5,
        "prompt": "Close this page. Given `cookies: List<Cookie>` with `id`, `flavor`, `grams` and `status`, write from memory: the golden total; the golden total per flavor in first-seen order; the number of burnt cookies; the heaviest golden cookie, or nothing; and a map from id to cookie that refuses repeated ids. Then write the same five results with Java streams. Which Java line needs an extra argument to keep the flavor order?",
        "answer": {
            "lang": "kotlin",
            "src": "val golden = cookies.filter { it.status == Status.GOLDEN }\nval total = golden.sumOf { it.grams }\nval perFlavor = golden.groupBy { it.flavor }.mapValues { (_, cs) -> cs.sumOf { it.grams } }\nval burntCount = cookies.count { it.status == Status.BURNT }\nval heaviest = golden.maxByOrNull { it.grams }            // null when nothing came out golden\n\nval repeated = cookies.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys\nrequire(repeated.isEmpty()) { \"duplicate cookie ids: ${repeated.joinToString()}\" }\nval byId = cookies.associateBy { it.id }",
            "alt": {
                "lang": "java",
                "src": "List<Cookie> golden = cookies.stream().filter(c -> c.status() == Status.GOLDEN).toList();\nint total = golden.stream().mapToInt(Cookie::grams).sum();\nMap<String, Integer> perFlavor = golden.stream().collect(Collectors.groupingBy(\n        Cookie::flavor, LinkedHashMap::new,                         // the extra argument: keeps the order\n        Collectors.summingInt(Cookie::grams)));\nlong burntCount = cookies.stream().filter(c -> c.status() == Status.BURNT).count();\nOptional<Cookie> heaviest = golden.stream().max(Comparator.comparingInt(Cookie::grams));\nMap<String, Cookie> byId = cookies.stream()\n        .collect(Collectors.toMap(Cookie::id, c -> c));               // throws on a repeated id"
            }
        }
    },
    "recap": [
        "`map`, `filter`, `mapNotNull` and `flatMap` each do one job and return a new list. Read a chain top to bottom, one job per line.",
        "`fold(initial) { acc, x -> ... }` is the general loop with its `var` hidden inside. `sumOf`, `count` and `maxByOrNull` are named special cases; prefer them when they fit.",
        "On an empty list, `reduce` throws `UnsupportedOperationException: Empty collection can't be reduced.` and `first()` throws `NoSuchElementException: List is empty.` Use `fold`, `sumOf` or the `OrNull` functions when input can be empty.",
        "`groupBy` keeps first-seen key order in a `LinkedHashMap`. Java's `groupingBy` promises no order unless you pass `LinkedHashMap::new`.",
        "`associateBy` silently keeps the last element for a repeated key, where Java's `toMap` throws. When keys should be unique, check for repeats first.",
        "The limit: Kotlin's operations on a `List` are eager. Each step builds a whole new `ArrayList`; the lambdas are free because the functions are `inline`, but the lists in between are not."
    ],
    "closing": "We started with two trays of cookies and a loop that built four results at once, then threw on a day when nothing was baked. Each result became one chain: `filter` and `sumOf` for the golden grams, `groupBy` for flavors in first-seen order, `maxByOrNull` for a largest that can be nothing, and `fold` for the jar, the loop with its `var` tucked inside.\n\nSearch your code for `.first()`, `.reduce {` and `associateBy`. Ask of each one: what happens on an empty day, or when a tray is written down twice?\n\nNext, we'll stop a chain from building a new list at every step. What changes when one cookie at a time travels the whole pipeline?",
    "quiz": [
        {
            "q": "On a day with no cookies, what does `cookies.filter { it.status == GOLDEN }.sumOf { it.grams }` return?",
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
            "q": "`listOf(c1, c3).associateBy { it.flavor }`, where both cookies (ids `c1` and `c3`) are oat. What do you get?",
            "options": [
                "`IllegalStateException: Duplicate key oat`",
                "A map with only `oat -> c3`, and no warning",
                "`oat -> [c1, c3]`",
                "A map with only `oat -> c1`"
            ],
            "answer": 1,
            "why": "`associateBy` keeps the last element for a repeated key and says nothing. The exception is what Java's `Collectors.toMap` does, which is why the first option is tempting. If you want every cookie per key, use `groupBy`; if a repeat is a bug, check with `groupingBy { }.eachCount()` first."
        },
        {
            "q": "Which operation gives you \"the bites that were taken, for the cookies that have one\" as a `List<Int>`?",
            "options": [
                "`map { it.nibbledGrams }`",
                "`filter { it.nibbledGrams != null }`",
                "`mapNotNull { it.nibbledGrams }`",
                "`flatMap { it.nibbledGrams }`"
            ],
            "answer": 2,
            "why": "`mapNotNull` transforms each cookie and drops the null results in one step. `map` gives a `List<Int?>` with nulls in it, `filter` gives cookies rather than bites, and `flatMap` needs a lambda that returns a collection, so it doesn't compile here."
        },
        {
            "q": "Cookies come out in the flavors ginger, oat, ginger, chocolate, in that order. In what order does `groupBy { it.flavor }` return the keys?",
            "options": [
                "Alphabetical: chocolate, ginger, oat",
                "Hash order, as Java's `groupingBy` gives",
                "Last-seen order: oat, ginger, chocolate",
                "First-seen order: ginger, oat, chocolate"
            ],
            "answer": 3,
            "why": "Kotlin's `groupBy` builds a `LinkedHashMap` and documents that keys keep the order in which they were first produced. Java's `groupingBy` promises no particular map, and on JDK 21 it gave a `HashMap` in hash order. Nothing in either sorts the keys."
        },
        {
            "q": "From Higher-order functions: functions in, functions out: `cookies.filter { it.grams > minGrams }` on a `List` creates no lambda object, even though the lambda captures `minGrams`. Why?",
            "options": [
                "`filter` is `inline`, so the lambda's body is pasted into the loop inside the calling function",
                "Kotlin caches capturing lambdas, one per call site",
                "The JIT removes the object at runtime",
                "Capturing a `val` never needs an object"
            ],
            "answer": 0,
            "why": "An inline function's lambda never becomes an object: the compiler copies `filter`'s loop and the lambda's body into your method, and `minGrams` is just a local it reads. Without `inline` a capturing lambda is a new object per evaluation (lesson 2), whether it captures a `val` or a `var`. Caching only applies to lambdas that capture nothing.",
            "from": "fp-03"
        }
    ],
    "flashcards": [
        {"front": "What does `reduce` do on an empty list?", "back": "It throws `UnsupportedOperationException: Empty collection can't be reduced.` Use `fold` with a starting value, or `reduceOrNull`."},
        {"front": "What does `emptyList<Int>().first()` throw?", "back": "`NoSuchElementException: List is empty.` `firstOrNull()` returns null instead."},
        {"front": "`associateBy` meets a repeated key. What happens?", "back": "The last element wins, silently. Java's `Collectors.toMap` throws `IllegalStateException: Duplicate key ...` instead."},
        {"front": "In what key order does Kotlin's `groupBy` return its map?", "back": "First-seen order: it returns a `LinkedHashMap`. Java's `groupingBy` promises no order (it was a `HashMap` on JDK 21)."},
        {"front": "What does `mapNotNull { it.nibbledGrams }` replace?", "back": "`map { it.nibbledGrams }.filterNotNull()`, building one list instead of two."},
        {"front": "How do you find repeated ids before indexing a list?", "back": "`cookies.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys`"},
        {"front": "Is `cookies.filter { }.map { }` on a `List` lazy?", "back": "No. Each step runs over the whole list and returns a new `ArrayList`. Sequences, in the next lesson, are lazy."}
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
        "prompt": "A teammate who likes loops asks why the chain version of the baking-day report fixed two bugs nobody was hunting for, and what the chain costs that the loop doesn't. Explain it in your own words.",
        "answer": "The loop built four results at once with mutable variables, so each one depended on details spread over the whole loop. `largest` started from `cookies.first()`, which crashes on an empty day and, on a normal day, starts from whatever cookie came first, even a raw one. In the chain, each result is computed on its own from the list. `largest` is `maxByOrNull` over the golden cookies only, so it can't pick a raw one and returns null when there are none, and no line assumes there is a first element. The cost is allocation: Kotlin's list operations are eager, so each `filter` or `map` builds a whole new list, where the loop made one pass and built nothing extra. The lambdas themselves are free because the functions are inline. For a few hundred cookies that cost doesn't matter; for millions of rows I'd fuse steps or use a sequence."
    },
    "deeper": {
        "minutes": 10,
        "body": "A few more operations earn a place in collection code.\n\n`runningFold` (also called `scan`) is `fold` that keeps every value along the way, which is exactly a running total. Over the weights `[45, 90, 50, 80, 30]`, `runningFold(0) { acc, x -> acc + x }` gives `[0, 45, 135, 185, 265, 295]`: one more element than the input, because it includes the starting value. `runningReduce` leaves the starting value out.\n\n```kotlin\nval totals = grams.runningFold(0) { acc, x -> acc + x }   // [0, 45, 135, 185, 265, 295]\nval firstOver200 = totals.indexOfFirst { it > 200 }        // 4: the tray passes 200 g after the fourth cookie\n```\n\n```java\n// JDK 21 streams have no running fold; a loop is the plain answer.\nList<Integer> totals = new ArrayList<>(List.of(0));\nfor (int x : grams) totals.add(totals.get(totals.size() - 1) + x);\n// JDK 24 added java.util.stream.Gatherers, with scan(...) and windowFixed(...) as intermediate operations.\n```\n\n`chunked(12)` splits cookies into boxes of twelve, and the last box may hold fewer: `listOf(1, 2, 3, 4, 5).chunked(2)` is `[[1, 2], [3, 4], [5]]`. `windowed(7)` gives sliding windows, for a seven-day average of how much you baked. `zip` pairs two lists element by element and quietly stops at the shorter one, so zipping 10 planned bakes with 9 actual ones loses the 10th without a word: compare the sizes first.\n\nOne caution from the other direction. Kotlin's `forEach` is inline, so a `return` inside its lambda returns from the enclosing function and skips every remaining element. Java developers expect `continue`-like behaviour from `Stream.forEach`. Use `return@forEach` to skip one element, or better, express the skip with `filter`."
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
