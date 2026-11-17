import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l05.demo"


def kdemo(name):
    path = f"{LAB}/demo/kotlin/workbench/functional/l05/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path,
            "alt": jdemo(name + "Java")}


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l05/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# The figure: the same filter, map and take(2) over five cookies, numbered in the order the lambdas run.
def cell(x, y, cls, label):
    return (f'<rect class="{cls}" x="{x - 28}" y="{y - 14}" width="56" height="28" rx="8"/>'
            + (f'<text class="t-s" x="{x}" y="{y + 5}" text-anchor="middle">{label}</text>' if label else ""))


ROWS = [80, 120, 160, 200, 240]
NAMES = ["c1 golden", "c2 raw", "c3 golden", "c4 burnt", "c5 golden"]
fig = ['<svg viewBox="0 0 680 300" role="img" aria-label="Two grids of five cookies by two steps, filter and map. '
       'Numbers show the order the lambdas run. On a List, filter runs on all five cookies first, then map on cookies 1, 3 and 5. '
       'On a Sequence, filter 1 and map 1 run first, then filter 2, filter 3 and map 3, and cookies 4 and 5 are never looked at.">',
       '<text class="t" x="170" y="24" text-anchor="middle">List: the whole tray per step</text>',
       '<text class="t" x="510" y="24" text-anchor="middle">Sequence: one cookie at a time</text>',
       '<line class="ln-d" x1="340" y1="40" x2="340" y2="270"/>']
for x, label in ((175, "filter"), (255, "map"), (515, "filter"), (595, "map")):
    fig.append(f'<text class="t-s t-code" x="{x}" y="54" text-anchor="middle">{label}</text>')
for i, y in enumerate(ROWS):
    fig.append(f'<text class="t-s" x="80" y="{y + 5}" text-anchor="middle">{NAMES[i]}</text>')
    fig.append(f'<text class="t-s" x="420" y="{y + 5}" text-anchor="middle">{NAMES[i]}</text>')
for i, y in enumerate(ROWS):                       # List: filter 1..5, then map on 1, 3, 5
    fig.append(cell(175, y, "box-a", str(i + 1)))
for i, y in enumerate(ROWS):
    order = {0: "6", 2: "7", 4: "8"}.get(i)
    fig.append(cell(255, y, "box-b" if order else "box-dim", order))
seq = {(0, "f"): "1", (0, "m"): "2", (1, "f"): "3", (2, "f"): "4", (2, "m"): "5"}   # Sequence
for i, y in enumerate(ROWS):
    f, m = seq.get((i, "f")), seq.get((i, "m"))
    fig.append(cell(515, y, "box-a" if f else "box-dim", f))
    fig.append(cell(595, y, "box-b" if m else "box-dim", m))
fig.append('<text class="t-s t-m" x="652" y="205" text-anchor="middle">untouched</text>')
fig.append('<text class="t-s t-m" x="652" y="245" text-anchor="middle">untouched</text>')
fig.append('<text class="t-s" x="170" y="286" text-anchor="middle">8 calls, a new list after each step</text>')
fig.append('<text class="t-s" x="510" y="286" text-anchor="middle">5 calls, stops when take(2) is full</text>')
fig.append('</svg>')
FIG = "".join(fig)

OPENING = """Picture an evening with a thick recipe book. You read the first recipe and ask one question: can I make this with what's in the fridge? No, so you turn the page. At the first yes, you close the book and start cooking. Nobody copies out all five hundred ingredient lists first, then checks every copy, then picks the first match.

Yet that's how the cookie trays in "Collections without loops: map, filter, fold and friends" worked. Each step finished the whole tray before the next step started. For two trays, nobody notices. For the recipe app's book of a million recipes, where each check is a slow call over the network, it means reading every page to find a recipe on page 518.

The trap is easy to miss, because the chain reads well and gives the right answer. Only the bill is wrong.

In this lesson, we'll count the work a list chain does, send one item at a time down the whole line with a sequence, make items on demand, and see where Java streams fit. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_SEARCH = """Recipe firstMatch(List<Recipe> book, ToIntFunction<Recipe> matchScore) {
    List<Scored> scored = book.stream()
            .map(r -> new Scored(r, matchScore.applyAsInt(r)))   // about 2 ms per recipe
            .toList();
    List<Recipe> good = scored.stream().filter(s -> s.score() >= 90).map(Scored::recipe).toList();
    return good.isEmpty() ? null : good.get(0);
}"""
K_SEARCH = """fun firstMatch(book: List<Recipe>, matchScore: (Recipe) -> Int): Recipe? =
    book.map { it to matchScore(it) }              // about 2 ms per recipe
        .filter { (_, score) -> score >= 90 }
        .map { (recipe, _) -> recipe }
        .firstOrNull()"""

S0 = """The recipe app keeps a big recipe book: a million recipes that its users have shared. Each evening it suggests one. To pick it, the app asks a matching service, a program on another computer that rates from 0 to 100 how well a recipe fits what's in your fridge. Each question takes about 2 ms, and the app pays for every one. Here's the search, written the way the last lesson taught us:

""" + pair(J_SEARCH, K_SEARCH) + """

`it to matchScore(it)` builds a pair: the recipe and its score, side by side. The chain reads well and gives the right answer. But say the first good match is recipe number 518. The chain still asks about all million recipes: 1,000,000 times 2 ms is 2,000 seconds, about 33 minutes of waiting for an answer that was ready after one second.

The cause is the tray from the last lesson. `map` and `filter` on a Kotlin `List` are **eager**: each one does its whole job at once. It loops over its whole input, writes every result into a brand-new list, and only then does the next step start. So the first `map` scores all million recipes and builds a list of a million pairs. `filter` builds a second list. Only then does `firstOrNull` look at element 0.

Java's collections have no eager chain, so the Java version above collects into a list after every step to do the same thing. Kotlin's `List` operations do exactly that for you.

The lambdas aren't the cost. As "Higher-order functions: functions in, functions out" showed, these functions are `inline`: the compiler pastes the loop and your lambda into the caller, so no lambda objects exist while the program runs. The cost is the lists. Every step allocates a new `ArrayList`, and a list of numbers holds each number as a separate boxed object. In a JMH run made for this course (JMH is a tool for timing small pieces of JVM code), a two-step `filter { }.map { }.sum()` over a million items allocated 26.5 MB per call.

For a short chain over a few hundred items, none of this matters, and the eager chain is the easiest to debug: you can stop after any step and look at a real list. It starts to matter when the input is big, a step is slow, or you only need the first few results.

**A list chain runs every step on every item. Ask how many items you really need.**

Let's watch the order of the work on one small tray first, then fix the search."""

# ---------------------------------------------------------------- section 1
J_WRAP = """Iterator<R> mapped = new Iterator<>() {
    public boolean hasNext() { return source.hasNext(); }
    public R next() { return transformer.apply(source.next()); }
};"""
K_WRAP = """override fun next(): R = transformer(iterator.next())
override fun hasNext(): Boolean = iterator.hasNext()"""

S1 = """Put `asSequence()` in front of the same chain and the order of the work changes. A **sequence** is a lazy chain of steps. **Lazy** means it does no work until a result is wanted, and then only as much as that result needs.

Picture a kitchen line with two helpers: one checks each cookie's color, the next one weighs it. With a list, the checker goes through the whole tray before the weigher starts. With a sequence, the first cookie walks down the whole line, checked and then weighed, before the second cookie leaves the tray. When the lunchbox is full, the line stops, and the cookies still on the tray are never touched. The figure shows both orders for the lunchbox you just packed.

The work starts at a **terminal operation**, a step such as `toList()`, `first()`, `sum()` or `count()` that asks for items. Steps like `map` and `filter` are **intermediate operations**: on a sequence they only add a step to the plan. That's why the lunchbox program printed `built TakeSequence, nothing has run yet` before any cookie was checked. The sequence is in no hurry at all. It has written down the plan and will wait as long as you like for someone to ask.

Now the search. `book.asSequence().map { ... }.filter { ... }.map { ... }.firstOrNull()` asks the matching service 518 times and stops. This is **short-circuiting**: stopping as soon as the answer is known. `first`, `firstOrNull`, `any`, `find` and `take(n)` can do it, and in a lazy chain they stop every step above them too. For a single test you don't even need a sequence. `book.firstOrNull { matchScore(it) >= 90 }` is one inlined loop, and it also stops at 518.

How does it work underneath? Each intermediate operation on a sequence is an ordinary function, not `inline`, that wraps the sequence before it. `map` returns a `TransformingSequence` that holds your lambda, `filter` a `FilteringSequence`, `take` a `TakeSequence`. When the terminal operation asks the last wrapper for an item, that wrapper asks the one before it, and so on back to the list. Here is the heart of `TransformingSequence` in the Kotlin 2.4.21 standard library, next to the same idea written by hand in Java:

""" + pair(J_WRAP, K_WRAP) + """

So a sequence trades the lists in between for one small wrapper object per step. The price is that the lambdas become real objects again, of the `Function1` interface (created through `invokedynamic`, as "Function types, lambdas and closures" showed), and a number that passes through `map` is boxed on its way.

One kind of step breaks the line. `sorted()` and `sortedBy { }` can't hand out the smallest item until they've seen every item, so the first request makes them pull the whole input into a list and sort it. The kitchen picture breaks here too: no cook can say which cookie is the lightest by looking at one cookie. In the Try it, a `sortedBy` before `firstOrNull { }` pulls all 1,000,000 recipes, though the service still runs only 518 times. If you only need the smallest item, `minByOrNull { }` reads the input once and sorts nothing.

**A sequence moves one item through every step and stops when the answer is known. Put the step that can stop at the end.**

So far every item came from a list we already had. A sequence doesn't need one."""

# ---------------------------------------------------------------- section 2
J_GEN = """List<Integer> servings = Stream.iterate(1, n -> n <= 16, n -> n * 2).toList();   // [1, 2, 4, 8, 16]"""
K_GEN = """val servings = generateSequence(1) { (it * 2).takeIf { next -> next <= 16 } }
servings.toList()   // [1, 2, 4, 8, 16]"""
J_PAGES = """Stream<SearchResult> results = Stream.iterate(1, page -> page <= 3, page -> page + 1)
        .flatMap(page -> fetchPage(page).stream());          // fetchPage is a web request
results.filter(r -> r.minutes() < 30).findFirst();           // also skips page 3 on JDK 21"""
K_PAGES = """val results = sequence {
    for (page in 1..3) yieldAll(fetchPage(page))   // fetchPage is a web request
}
results.first { it.minutes < 30 }                 // fetches page 1 and page 2, never page 3"""

S2 = """A sequence can make its items as it goes. Two builders produce an item only when someone asks for the next one.

`generateSequence(seed) { next }` starts from the seed and works out each item from the one before. It ends when the lambda returns `null`. The app's serving buttons, for 1, 2, 4, 8 and 16 servings, are one line:

""" + pair(J_GEN, K_GEN) + """

`takeIf` returns the value when the test passes and `null` when it doesn't (lesson 6 covers it). Without the `takeIf`, the sequence never ends. That's fine as long as something downstream stops it, such as `take(5)` or `first { }`.

`sequence { }` is for items that take real code to make, like a recipe website that shows its search results one page at a time. Inside the block, `yield(x)` hands out one item and `yieldAll(list)` hands out many:

""" + pair(J_PAGES, K_PAGES) + """

You may wonder how a `for` loop can stop halfway and wait. The block is a suspend lambda: its type is `suspend SequenceScope<T>.() -> Unit`. A suspend function is one that can pause in the middle and carry on later, and the coroutines track covers them. The compiler turns the block into a small state machine, code that remembers which step it reached. Each `yield` saves where the block is and hands control back to whoever asked for an item. When they ask for the next one, the block carries on right after that `yield`. No second thread is involved: it all runs on the caller's thread, one step at a time. When nobody asks again, the block never carries on, so page 3 is never requested.

The block is restricted. Only `yield` and `yieldAll` may pause it. Call `delay` inside `sequence { }` and Kotlin 2.4.21 refuses: `Restricted suspending functions can invoke member or extension suspending functions only on their restricted coroutine scope.` For pages you must wait for without blocking a thread, use a `Flow` (the coroutines track).

The lab's version has one more rule: it doesn't know how many pages exist, and an empty page means the end. In Kotlin that's a `while (true)` loop with a `break`. In Java it's `Stream.iterate(0, p -> p + 1).map(site::page).takeWhile(p -> !p.isEmpty()).flatMap(List::stream)`.

We now have three lazy pipelines: a list turned into a sequence, a generated one and a paging one. Java has a lazy pipeline of its own, and the two part ways at the edges."""

ASIDE = {
    "title": "Can a sequence outlive the file it reads?",
    "body": "Yes, and that's a trap. `File(\"recipes.txt\").bufferedReader().use { it.lineSequence() }` looks as if it reads the file inside `use { }`. It doesn't. It returns a lazy plan for the reading, and `use` closes the file on its way out. The first terminal operation, somewhere else, reads from a closed file and fails with `java.io.IOException: Stream closed`. Either finish the work inside the block, with `toList()` if the lines fit in memory, or pass the work in, as `File(\"recipes.txt\").useLines { lines -> ... }` does: it reads while the file is open and closes it afterwards. Java's `Files.lines` has the same shape, and whoever uses its stream must close it."
}

# ---------------------------------------------------------------- section 3
S3 = """A Java **stream** is Java's lazy pipeline: you make one from a collection with `.stream()`, add steps, and finish with a terminal operation. It runs in the same order as a sequence, one item at a time down the whole line, and the Java twins in this lesson print the same order and the same counts. The differences are practical.

A sequence is a recipe, not a tray of cookies. Each terminal operation follows the recipe again from the top, side effects included: call `sum()` and then `count()` on the same sequence and every `map` lambda runs twice. A few sequences refuse a second run. `iterator().asSequence()` and `generateSequence { }` without a seed throw `IllegalStateException: This sequence can be consumed only once.` A stream is always single-use, like a disposable piping bag: squeeze it once and it's spent. A second terminal operation throws `IllegalStateException: stream has already been operated upon or closed`.

Streams can do things sequences can't. `parallelStream()` splits the work over several threads (paths of work that run at the same time), taken from a shared pool called the common ForkJoinPool. Sequences have no parallel mode at all. `IntStream`, `LongStream` and `mapToLong` keep numbers unboxed, and Kotlin has no `LongSequence`. On JDK 24 and later, gatherers add windows and running totals to streams (Go deeper has them).

Here are the numbers from the JMH run behind this course. The machine was a 4-core virtual machine shared with other work, so treat the times as rough, order-of-magnitude figures. The bytes allocated per call barely move between runs, so you can trust those. Each variant took a list of 1,000,000 items, kept the ones that passed a test (about 60% of them) and summed one `Long` from each:

| Variant | Time per call | Allocated per call |
|---|---|---|
| `for` loop | 5.2 ms | about 0 |
| `filter { }.map { }.sum()` on a List | 148 ms | 26,507,194 B |
| `sumOf { if (passes) n else 0L }` | 2.6 ms | about 0 |
| `asSequence().filter { }.map { }.sum()` | 9.0 ms | 189 B |
| `stream().filter().mapToLong().sum()` | 8.9 ms | 428 B |
| `stream().filter().map().reduce(0L, ...)` | 14 ms | 28,782,178 B |

The fastest line is neither a list chain nor a sequence. It's one fused `sumOf`, which is the hand-written loop. The sequence allocated almost nothing only because the JIT (the compiler inside the JVM that speeds up hot code while it runs) removed the boxes in this tiny benchmark. Don't count on that in a big program, where one call site sees many different lambdas. When the terminal operation could stop early (the first match was at index 101), the gap was huge: 141 ns for the sequence, 4.4 ms for the list chain.

So here's the rule I use. Use list operations by default. Switch to `asSequence()` when the end of the chain can stop early, or when a long chain runs over a big input. Use `sequence { }` or `generateSequence` for items made on demand, such as pages. Use a stream when you need `parallel()`, a primitive stream or a gatherer, or when a Java library hands you one.

**Laziness saves work only when something stops early. When nothing does, one fused pass beats both.**

That fused pass is `sumOf`, `count { }` or `firstOrNull { }`, and it's usually the shortest line too."""

L = {
    "id": "fp-05",
    "title": "Sequences: lazy pipelines, and where Java Streams fit",
    "minutes": 36,
    "goal": "By the end you can predict the order in which a List chain and a Sequence chain run their lambdas, choose between a List chain, a Sequence and a Java Stream for a pipeline, and build a lazy paging source with `sequence { }`.",
    "opening": OPENING,
    "warmup": {
        "q": "A tray holds five cookies, `c1` to `c5`; `c1`, `c3` and `c5` are golden. This runs: `tray.asSequence().filter { println(\"filter ${it.id}\"); it.bake == GOLDEN }.map { println(\"map ${it.id}\"); it.grams }.take(2).toList()`. What prints?",
        "options": [
            "`filter c1` to `filter c5`, then `map c1`, `map c3`, `map c5`",
            "`filter c1`, `map c1`, `filter c2`, `filter c3`, `map c3`",
            "`filter c1`, `filter c2`, `filter c3`, then `map c1`, `map c3`",
            "Nothing: a sequence only runs when you print it"
        ],
        "answer": 1,
        "why": "A sequence sends one cookie through the whole chain before it looks at the next. `c1` passes the filter and goes straight on to `map`. `c2` fails the filter. `c3` passes and is mapped, and now `take(2)` has its two results, so nothing asks for `c4` and `c5`. The first option is what the same chain prints on a List. `toList()` is what starts the work."
    },
    "sections": [
        {
            "h": "A list chain finishes the whole tray before the next step starts",
            "body": S0,
            "try": {
                "title": "Watch the order of the lambdas",
                "minutes": 4,
                "steps": [
                    "Open `OrderDemo.kt` (or `OrderDemoJava.java`). The same `filter`, `map` and `take(2)` pick two golden cookies for a lunchbox, once from a List and once from a Sequence. Write down the print order you expect for each.",
                    "Run it with the command below.",
                    "In the List chain, move `.take(2)` up to right after `tray`. Predict how many `filter` lines print and what goes in the lunchbox, then run it."
                ],
                "code": kdemo("OrderDemo"),
                "expect": "The List chain prints `filter c1` to `filter c5`, then `map c1`, `map c3`, `map c5`: each step finishes the whole tray before the next starts. The Sequence chain first prints `built TakeSequence, nothing has run yet`, then `filter c1, map c1, filter c2, filter c3, map c3`. Cookies `c4` and `c5` are never looked at. Both lunchboxes hold `[45, 50]`. With `take(2)` first, the List chain filters only `c1` and `c2`, and the lunchbox holds `[45]`. That's a different question (which of the first two cookies are golden), so moving a step changes the answer in both models. Laziness only changes how much work runs."
            }
        },
        {
            "h": "A sequence sends one item at a time down the whole line",
            "body": S1,
            "figure": {"svg": FIG, "caption": "The same filter, map and take(2). The List runs each step over the whole tray; the Sequence moves each cookie through both steps and stops after two results."},
            "try": {
                "title": "Count the work on a million recipes",
                "minutes": 4,
                "steps": [
                    "Read `ScanCount.kt`. Every line looks for the same recipe, number 518 of a million. For each line, predict how many times `match` runs and how many recipes the `onEach` counter pulls.",
                    "Run it.",
                    "In the Sequence chain line, add `.toList()` just before `.firstOrNull()`. Predict the counts, then run it again.",
                    "Run the Java twin and compare `findFirst` on one stream with collecting first."
                ],
                "code": kdemo("ScanCount"),
                "expect": "The List chain scores all 1,000,000. The Sequence chain and `firstOrNull { }` score 518 and stop. The `sortedBy` line also scores only 518, but its counter shows it pulled all 1,000,000 recipes into a list to sort them first. With `.toList()` added, the Sequence scores 1,000,000 again: `toList()` is a terminal operation that wants every item. Java prints the same numbers, because a stream is lazy in the same way and a collected list is not."
            },
            "refs": [{"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html", "kind": "docs"}]
        },
        {
            "h": "Making items on demand: generateSequence and sequence { yield }",
            "body": S2,
            "aside": ASIDE,
            "try": {
                "title": "Fetch only the pages you read",
                "minutes": 3,
                "steps": [
                    "Read `Paging.kt`. Each page holds three recipes, and later pages hold quicker ones. Predict which pages are fetched before the first recipe under 30 minutes prints.",
                    "Run it.",
                    "Change `first` to `firstOrNull` and `< 30` to `< 1`. Predict which pages are fetched and what prints, then run it."
                ],
                "code": kdemo("Paging"),
                "expect": "`fetching page 1`, `fetching page 2`, then `SearchResult(title=R2-1, minutes=25)`. Page 3 is never fetched, because `first` stopped asking. Nobody has a recipe that takes under a minute, so with `< 1` all three pages are fetched and it prints `null`: laziness can only save work when something stops early. The serving buttons are `[1, 2, 4, 8, 16]` in both languages."
            },
            "refs": [{"title": "SequenceBuilder.kt, Kotlin 2.4.21 stdlib source", "url": "https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/collections/SequenceBuilder.kt", "kind": "read"}]
        },
        {
            "h": "Sequence or Stream, and when you need neither",
            "body": S3,
            "try": {
                "title": "Read a sequence twice, and a stream twice",
                "minutes": 3,
                "steps": [
                    "Read `Reuse.kt`. Predict how many `weigh` lines print, and what the second read of `once` does.",
                    "Run it, then run `ReuseJava`.",
                    "In `Reuse.kt`, delete `.asSequence()` from `weights`. Predict how many `weigh` lines print now."
                ],
                "code": kdemo("Reuse"),
                "expect": "Six `weigh` lines: three for `sum()` and three more for `count()`, because each terminal operation follows the recipe again. The sum is 950 and the count 3. The iterator-backed sequence fails on its second read with `IllegalStateException: This sequence can be consumed only once.` Java's stream fails on the second terminal operation with `IllegalStateException: stream has already been operated upon or closed`. Without `asSequence()`, `weights` is a List built once, so `weigh` prints three lines in total."
            },
            "refs": [{"title": "java.util.stream package summary (Java SE 21 API)", "url": "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html", "kind": "docs"}]
        }
    ],
    "compare": {
        "title": "The first matches for a vegetarian guest: Sequence vs Stream",
        "java": {"title": "RecipeSearch.java", "src": "List<Long> firstMatchesFor(List<Recipe> book, ToIntFunction<Recipe> matchScore, int n) {\n    return book.stream()\n            .filter(Recipe::vegetarian)                       // the quick look first\n            .filter(r -> matchScore.applyAsInt(r) >= 90)\n            .map(Recipe::id)                                  // boxed Long, as in Kotlin\n            .limit(n)                                         // stops early, like take(n)\n            .toList();                                        // unmodifiable on JDK 16+\n}"},
        "kotlin": {"title": "RecipeSearch.kt", "src": "fun firstMatchesFor(book: List<Recipe>, matchScore: (Recipe) -> Int, n: Int): List<Long> =\n    book.asSequence()\n        .filter { it.vegetarian }              // the quick look first\n        .filter { matchScore(it) >= 90 }\n        .map { it.id }                         // boxed Long at the Function1 boundary\n        .take(n)                               // stops early, like limit(n)\n        .toList()"},
        "note": "Both pipelines are lazy and run in the same order, one recipe at a time, so both ask the matching service exactly as often. The real differences are at the edges. The stream can be used once; the sequence can be read again and will run the whole chain again. The stream could go `parallel()`; the sequence can't. Kotlin's terminal operations mirror the List API (`firstOrNull` returns `null`, and `groupBy` and `sumOf` are there), while the stream returns `Optional` from `findFirst` and needs `Collectors` for grouping. And on the Kotlin side you can drop `asSequence()` and get an eager List chain with the same code, which is often the better choice for small inputs."
    },
    "worked": {
        "title": "Decide whether a nutrition check should be lazy",
        "steps": [
            {"say": "The app checks the 2 million ingredient lines in its recipe book against a nutrition table, and shows the first 20 lines whose ingredient the table doesn't know, so someone can add them. Here's the first version. Before reading on, find the step that makes laziness pay off.", "code": "fun firstUnknown(lines: List<Line>, kcalPer100g: Map<String, Int>): List<Check> =\n    lines.map { line -> Check(line.recipeId, line.ingredient, kcalPer100g[line.ingredient]) }\n        .filter { it.kcal == null }\n        .take(20)", "lang": "kotlin", "alt_lang": "java", "alt_code": "List<Check> firstUnknown(List<Line> lines, Map<String, Integer> kcalPer100g) {\n    List<Check> all = lines.stream()\n            .map(l -> new Check(l.recipeId(), l.ingredient(), kcalPer100g.get(l.ingredient())))\n            .toList();                                   // 2 million objects\n    return all.stream().filter(c -> c.kcal() == null).limit(20).toList();\n}"},
            {"say": "`take(20)` can stop early, so this chain should be lazy. 1. Ask the question: does the last step stop before the end? Here, yes. 2. Put `asSequence()` at the front. Now the chain builds 20 checks plus the known lines it read on the way, and no 2-million-item lists.", "code": "fun firstUnknown(lines: List<Line>, kcalPer100g: Map<String, Int>): List<Check> =\n    lines.asSequence()                                   // 2. lazy from here on\n        .map { line -> Check(line.recipeId, line.ingredient, kcalPer100g[line.ingredient]) }\n        .filter { it.kcal == null }\n        .take(20)                                        // 1. stops early\n        .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "List<Check> firstUnknown(List<Line> lines, Map<String, Integer> kcalPer100g) {\n    return lines.stream()                                // 2. one lazy pipeline\n            .map(l -> new Check(l.recipeId(), l.ingredient(), kcalPer100g.get(l.ingredient())))\n            .filter(c -> c.kcal() == null)\n            .limit(20)                                   // 1. stops early\n            .toList();\n}"},
            {"say": "3. Move the cheap test before the work. Building a `Check` for every line is wasted effort; test first and build the object only for real unknowns.", "code": "lines.asSequence()\n    .filter { it.ingredient !in kcalPer100g }            // 3. cheap test, no object built\n    .map { Check(it.recipeId, it.ingredient, null) }\n    .take(20)\n    .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "lines.stream()\n        .filter(l -> !kcalPer100g.containsKey(l.ingredient()))   // 3. cheap test\n        .map(l -> new Check(l.recipeId(), l.ingredient(), null))\n        .limit(20)\n        .toList();"},
            {"say": "4. Look for a barrier. Now someone asks for the 20 *heaviest* unknown lines, so the biggest gaps come first. That needs `sortedByDescending { }` before `take(20)`, and the sort must read all 2 million lines first, so the sequence saves nothing over a List here. Keep whichever reads better, and know that the cost is the full pass plus the sort.", "code": "lines.asSequence()\n    .filter { it.ingredient !in kcalPer100g }\n    .sortedByDescending { it.grams }                     // 4. reads everything\n    .take(20)\n    .map { Check(it.recipeId, it.ingredient, null) }\n    .toList()", "lang": "kotlin", "alt_lang": "java", "alt_code": "lines.stream()\n        .filter(l -> !kcalPer100g.containsKey(l.ingredient()))\n        .sorted(Comparator.comparingInt(Line::grams).reversed())   // 4. reads everything\n        .limit(20)\n        .map(l -> new Check(l.recipeId(), l.ingredient(), null))\n        .toList();"}
        ]
    },
    "lab": {
        "title": "Score only what you must, and fetch pages lazily",
        "minutes": 12,
        "files": [f"{LAB}/main/kotlin/workbench/functional/l05/RecipeSearch.kt", f"{LAB}/main/kotlin/workbench/functional/l05/ResultPages.kt"],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l05.*'",
        "steps": [
            "Run the tests. Seven of nine fail. `firstMatch` already returns the right recipe, but the test shows it asks the matching service 200,000 times.",
            "Fix `firstMatch` so it scores only up to the first match. Keep the signature.",
            "Write `firstMatchesFor`: tonight's guest is vegetarian, so other recipes must never reach the service, and nothing may be scored after the nth match.",
            "In `ResultPages.kt`, write `allResults` with `sequence { }`: ask for page 0, then 1, then 2, and stop at the first empty page.",
            "Run the tests until all nine pass. Then read the last test and say what it shows about reading a sequence twice."
        ],
        "hints": [
            "For `firstMatch`, `book.asSequence()` in front of the existing chain is enough. So is `book.firstOrNull { matchScore(it) >= 90 }`, one inlined loop.",
            "In `firstMatchesFor`, the order of the two `filter` calls decides which recipes reach the service. `take(n)` goes after both, before `toList()`.",
            "Inside `sequence { }` a `while (true)` loop is fine: `break` on an empty page, otherwise `yieldAll(page)`. The loop pauses at every `yieldAll` until someone wants more."
        ],
        "done_when": "All nine tests in `LazyPipelinesTest` pass."
    },
    "drill": {
        "title": "A paging source from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `fun <T> paged(fetch: (Int) -> List<T>): Sequence<T>` that asks for page 1, then 2, then 3, and so on, and stops at the first empty page without asking for the next one. Then write the Java version that returns a `Stream<T>`. Check: does yours fetch anything before a terminal operation runs?",
        "answer": {
            "lang": "kotlin",
            "src": "fun <T> paged(fetch: (Int) -> List<T>): Sequence<T> = sequence {\n    var page = 1\n    while (true) {\n        val items = fetch(page++)      // runs only when someone asks for more\n        if (items.isEmpty()) break     // an empty page ends it\n        yieldAll(items)                // pauses here between items\n    }\n}",
            "alt": {"lang": "java", "src": "static <T> Stream<T> paged(IntFunction<List<T>> fetch) {\n    return Stream.iterate(1, page -> page + 1)       // 1, 2, 3, ... lazily\n            .map(fetch::apply)                       // one fetch per page, on demand\n            .takeWhile(items -> !items.isEmpty())    // stops at the first empty page\n            .flatMap(List::stream);\n}"}
        }
    },
    "recap": [
        "List operations are eager: each step loops over everything and builds a new list. They're inlined, so the cost is the lists and the boxed numbers, not lambda objects.",
        "A sequence is lazy: nothing runs until a terminal operation asks, and then each item goes through every step before the next one is read.",
        "Laziness pays when the end of the chain stops early (`first`, `any`, `take`). `generateSequence` and `sequence { yield }` make items on demand, on the caller's thread.",
        "A sequence follows its recipe again on every terminal operation (a few are once-only); a Java stream is always single-use but can go parallel and stay unboxed.",
        "Default to List operations. Use a sequence for early exits, long chains on big inputs and paging. One fused `sumOf` or `firstOrNull { }` beats both.",
        "The limit: laziness can't help a step that needs everything. `sorted` reads the whole input first, and a chain with no early stop does all the work anyway."
    ],
    "closing": "We started with a recipe book and a cook who stops at the first recipe that fits. A list chain read every page anyway, because each step finished the whole tray first. A sequence sends one item down the whole line and stops when the answer is known, and a Java stream does the same, once.\n\nSearch your code for a list chain that ends in `first`, `firstOrNull`, `any` or `take`, and count what runs before it.\n\nNext, we'll look at five tiny functions that run a block with one value in hand: `let`, `run`, `with`, `apply` and `also`. Which ones hand back the value, and which hand back the block's answer?",
    "quiz": [
        {"q": "`score` is a slow call. Which line calls it only until the first recipe that scores 90 or more?", "options": ["`book.map { score(it) }.first { it >= 90 }`", "`book.asSequence().map { score(it) }.toList().first { it >= 90 }`", "`book.asSequence().map { score(it) }.first { it >= 90 }`", "`book.asSequence().map { score(it) }.sorted().first { it >= 90 }`"], "answer": 2, "why": "Only the third line is lazy all the way to a terminal step that stops early. The first is eager and scores everything before `first` looks. In the second, `toList()` is a terminal operation that pulls every item. In the fourth, `sorted()` must read every score before it can hand out the smallest."},
        {"q": "`val weights = basket.asSequence().map { log(it.name); it.grams }` runs over a basket of 5 items, then the code calls `weights.sum()` and `weights.max()`. How many times does `log` run?", "options": ["5", "10", "0, because sequences are lazy", "5, then `max()` throws IllegalStateException"], "answer": 1, "why": "A sequence is a recipe, and each terminal operation follows it again: five calls for `sum()`, five more for `max()`. Only a few sequences are once-only (for example `iterator().asSequence()`). If you need the values twice, call `toList()` once and reuse the list."},
        {"q": "The app's server adds up the grams of 40 million logged bakes on a 16-core machine, and should use all the cores. What fits best?", "options": ["`grams.asSequence().sum()`", "`sequence { yieldAll(grams) }.sum()`", "A List chain with `sumOf`", "`grams.parallelStream().mapToLong { it }.sum()`"], "answer": 3, "why": "Only Java streams have a parallel mode, and `mapToLong` keeps the numbers unboxed. Kotlin sequences run on one thread and have no parallel API. `sumOf` is the fastest single-threaded option, but it still uses one core."},
        {"q": "From the collections lesson: today's shopping basket can be empty. What does `basket.asSequence().map { it.grams }.reduce { a, b -> a + b }` do on an empty basket?", "options": ["Throws `UnsupportedOperationException: Empty sequence can't be reduced.`", "Returns 0", "Returns null", "Returns an empty sequence"], "answer": 0, "why": "`reduce` has no starting value, so with no items it has nothing to return, and it throws. That holds for sequences as it does for lists. Use `fold(0) { a, b -> a + b }` or `sum()`, which return 0, or `reduceOrNull`.", "from": "fp-04"},
        {"q": "`sequence { for (p in 1..10) yieldAll(site.page(p)) }.take(5).toList()`. Every page holds 3 recipes. How many pages are fetched?", "options": ["1", "2", "10", "0, until the result is printed"], "answer": 1, "why": "Page 1 gives three recipes and page 2 gives the fourth and fifth. `take(5)` is then full and stops asking, so the block never carries on to fetch page 3. `toList()` is the terminal operation, so the fetching happens right there, not when you print."}
    ],
    "flashcards": [
        {"front": "What does `list.filter { }.map { }` allocate?", "back": "A new `ArrayList` per step, plus a box for every number in a `List<Long>`. The lambdas are inlined, so no function objects."},
        {"front": "When does a sequence chain run its lambdas?", "back": "Only when a terminal operation (`toList`, `first`, `sum`, `count`, ...) asks for items. `map` and `filter` on a sequence only add a step to the plan."},
        {"front": "In what order does `asSequence().filter { }.map { }` run?", "back": "Item by item: filter 1, map 1, filter 2, ... Each item goes through every step before the next one is read."},
        {"front": "Why does `sortedBy { }` in a sequence read everything?", "back": "It can't hand out the smallest item until it has seen all of them, so the first request pulls the whole input into a list and sorts it."},
        {"front": "What happens when you read a sequence twice?", "back": "The whole chain runs again, side effects included. `iterator().asSequence()` and seedless `generateSequence { }` throw `IllegalStateException` instead."},
        {"front": "What happens when you use a Java stream twice?", "back": "`IllegalStateException: stream has already been operated upon or closed`. Streams are single-use."},
        {"front": "How does `sequence { }` pause between items?", "back": "The block is a suspend lambda. Each `yield` pauses it until someone asks for the next item. No second thread is involved."}
    ],
    "terms": [
        {"term": "Eager", "plain": "Does all the work for a step right away and stores the result, before the next step starts."},
        {"term": "Lazy", "plain": "Does no work until a result is asked for, and then only as much as needed."},
        {"term": "Sequence", "plain": "Kotlin's lazy chain of steps: each item goes through every step, and nothing runs until a terminal operation asks."},
        {"term": "Intermediate operation", "plain": "A step such as `map` or `filter` that returns another sequence or stream and runs nothing by itself."},
        {"term": "Terminal operation", "plain": "A step such as `toList`, `first` or `sum` that asks for items and so makes the chain run."},
        {"term": "Short-circuiting", "plain": "Stopping as soon as the answer is known, as `first`, `any` and `take` do."},
        {"term": "Stateful operation", "plain": "A step like `sorted` that must remember many items, often all of them, before it can hand out one."}
    ],
    "explain_back": {
        "prompt": "A teammate added `.asSequence()` in front of every collection chain in the recipe app \"because sequences are faster\". Explain in your own words what a sequence changes, and when it is worth it.",
        "answer": "A sequence changes the order of the work. A List chain runs each step over the whole collection and builds a new list before the next step starts. A sequence runs nothing until a terminal operation asks for items, then moves each item through every step before reading the next. That saves the lists in between, and when the last step can stop early, like `first` or `take`, it skips the rest of the input entirely. It isn't free: each step becomes a wrapper object with a lambda, numbers get boxed on the way through, and a chain read twice does all its work twice. For a full pass over a few hundred items, the eager chain is just as fast and easier to debug, and a single `sumOf` or `count { }` beats both. I'd keep `asSequence()` where a chain stops early or runs several steps over large inputs, and take it out elsewhere."
    },
    "deeper": {
        "minutes": 10,
        "body": """Three details matter once you write sequences in hot code, the code that runs most often.

**Boxing.** A sequence of `Long` is a sequence of `java.lang.Long` objects, because each step calls a `Function1` whose `invoke` takes and returns `Object`. In bytecode, the lambda of `map { it.grams.toLong() }` is a `Function1` whose `invokedynamic` signature returns `Ljava/lang/Long;`. Java's `mapToLong` takes a `ToLongFunction` that returns a primitive `long`. In the JMH run above, the sequence still allocated only 189 bytes per call, because the JIT's escape analysis saw that the boxes never left the method and removed them. That worked because the benchmark had one call site and one lambda type. In a big program the same `FilteringSequence` code runs with dozens of different lambdas, the call site becomes megamorphic (it sees too many types for the JIT to inline them), and the boxes come back.

**IntelliJ's hint.** The Kotlin plugin has an inspection that suggests turning a call chain on a collection into a sequence. It is on by default as a weak warning and fires for chains of five or more calls. Treat it as a prompt to ask this lesson's question (does the end of the chain stop early, and is the input big?), not as a rule.

**Gatherers.** Since JDK 24, streams have `Stream.gather`, with built-ins in `java.util.stream.Gatherers`: `windowFixed`, `windowSliding`, `fold`, `scan` and `mapConcurrent`. Kotlin has had the equivalents on both `List` and `Sequence` for years: `chunked`, `windowed`, `fold` and `runningFold` (also called `scan`). So a seven-day average of grams baked is `days.windowed(7) { it.average() }` in Kotlin, a hand-written loop in Java on JDK 21, and `stream.gather(Gatherers.windowSliding(7))` on JDK 24 and later. The labs compile with release 21, so they use none of this."""
    },
    "sources": [
        {"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html"},
        {"title": "Collections in Java and Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html"},
        {"title": "java.util.stream package summary (Java SE 21 API)", "url": "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html"},
        {"title": "_Sequences.kt, Kotlin 2.4.21 stdlib source", "url": "https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt"}
    ]
}

out = ROOT / "content/lessons/fp-05.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
