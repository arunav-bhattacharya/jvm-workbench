import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l03.demo"


def kdemo(name, alt=True):
    path = f"{LAB}/demo/kotlin/workbench/functional/l03/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(name + "Java")
    else:
        d["solo"] = True
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l03/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def step(x, y, w, label, cls="box-a"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="40" rx="8"/>'
            f'<text class="t-s" x="{x + w // 2}" y="{y + 25}" text-anchor="middle">{label}</text>')


def val(x, y, label, cls="t-s t-code"):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="middle">{label}</text>'


def arrow(x1, x2, y):
    return f'<line class="ln-a" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'


FIG = (
    '<svg viewBox="0 0 720 250" role="img" aria-label="Three small steps composed into one. A recipe asks for 200 g of sugar: scaled for six guests it becomes 300, ten percent less makes 270, '
    'and the cap of 250 g left in the bag gives 250. Composed in the other order, with the cap first, the same 200 g becomes 270 g, more sugar than the bag holds.">'
    '<rect class="box-dim" x="72" y="40" width="586" height="70" rx="8"/>'
    '<text class="t-s t-code" x="365" y="30" text-anchor="middle">sugar = forSixGuests andThen tenPercentLess andThen atMostTheBag</text>'
    + val(35, 80, "200") + arrow(58, 78, 75)
    + step(80, 55, 140, "x 6/4, six guests") + arrow(220, 240, 75)
    + val(265, 80, "300") + arrow(288, 308, 75)
    + step(310, 55, 140, "10 % less") + arrow(450, 470, 75)
    + val(495, 80, "270") + arrow(518, 538, 75)
    + step(540, 55, 110, "at most 250") + arrow(650, 668, 75)
    + val(690, 80, "250", "t-s t-code t-ok")
    + '<text class="t-s t-m" x="365" y="150" text-anchor="middle">capFirst = atMostTheBag andThen forSixGuests andThen tenPercentLess</text>'
    + val(35, 195, "200") + arrow(58, 78, 190)
    + step(80, 170, 140, "at most 250", "box") + arrow(220, 240, 190)
    + val(265, 195, "200") + arrow(288, 308, 190)
    + step(310, 170, 140, "x 6/4, six guests", "box") + arrow(450, 470, 190)
    + val(495, 195, "300") + arrow(518, 538, 190)
    + step(540, 170, 110, "10 % less", "box") + arrow(650, 668, 190)
    + val(690, 195, "270", "t-s t-code t-bad")
    + '<text class="t-s t-bad" x="560" y="236" text-anchor="middle">270 g: more sugar than the bag holds</text>'
    + '</svg>'
)

OPENING = """Picture a friend who is good in the kitchen. You hand them any recipe card, and they hand back a new card: "the same, but for six people", or "the same, but vegan", or "the same, and if it burns, try again". They don't need to know what the recipe makes. They change the card, not the dinner.

Code needs friends like that. Function types, lambdas and closures turned checks into values you can hold. The next step is a function whose arguments, or whose result, are such values. That sounds abstract until you notice the same loop copied around three calls, with one line changed each time.

The easy trap is to trust every such friend equally. One that "remembers last time's answer" is only right for recipes whose answer never changes, and it can't taste the difference.

In this lesson, we'll write retry and timed, return a function that is set up once, clip small functions together where order matters, build a memo that remembers, and see why `inline` makes Kotlin's own versions free. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_LOOPS = """// fetch a recipe page from the website
for (int attempt = 1; ; attempt++) {
    try { page = site.fetch("pancakes"); break; }
    catch (SiteTimeoutException e) { if (attempt == 3) throw e; }
}
// the same loop around shop.prices(basket)
// the same loop around weather.today()"""
K_LOOPS = """// fetch a recipe page from the website
var attempt = 1
while (true) {
    try { page = site.fetch("pancakes"); break }
    catch (e: SiteTimeoutException) { if (attempt++ == 3) throw e }
}
// the same loop around shop.prices(basket)
// the same loop around weather.today()"""
J_RETRY = """static <T> T retry(int times, Supplier<T> block) {
    RuntimeException last = null;
    for (int attempt = 1; attempt <= times; attempt++) {
        try { return block.get(); }
        catch (RuntimeException e) { last = e; }
    }
    throw new IllegalStateException("gave up after " + times + " attempts", last);
}

String page = retry(3, () -> site.fetch("pancakes"));"""
K_RETRY = """fun <T> retry(times: Int, block: () -> T): T {
    var last: Exception? = null
    repeat(times) {
        try { return block() } catch (e: Exception) { last = e }
    }
    throw IllegalStateException("gave up after $times attempts", last)
}

val page = retry(3) { site.fetch("pancakes") }"""

S0 = """Look at three places in a recipe app that call something flaky. A **flaky** call is one that fails now and then for reasons outside your code, like a website that is slow to answer and times out:

""" + pair(J_LOOPS, K_LOOPS) + """

The three loops are identical except for one call. An ordinary helper method can't pull that call out, because a method's parameters are values, and the call has to happen inside the loop, up to three times. What you need to pass in is the work itself.

A **higher-order function** is a function that takes a function as a parameter, returns one, or both. It's the friend from the opening: hand it a card, and it does something with the card. Here is retry written as one:

""" + pair(J_RETRY, K_RETRY) + """

The loop is written once. The part that varies, the call, arrives as `block`, and `retry` decides when and how often to run it. That's the whole idea of this lesson: keep the shape of a computation (retry it, time it, remember it) apart from the work inside it. (The `return` inside `repeat` leaves `retry` itself. That only works because `repeat` is `inline`, which the last section explains.)

The demo's fake website times out twice, then answers. It also wraps the call in `timed`, a second higher-order function that runs any block and reports how long it took:

```text
  attempt 1 failed: site timeout on call 1
  attempt 2 failed: site timeout on call 2
  fetch with retry took 41.14 ms
result: page:pancakes after 3 calls
```

Three calls, one page, and neither function knows what a recipe is. (The 41 ms is from a busy machine, and most of it is the JVM running brand-new code for the first time.)

Kotlin makes the call site read like a language feature. When the last parameter is a function, you can write the lambda after the parentheses. That's a **trailing lambda**, and if it's the only argument, you drop the parentheses too: `retry(3) { ... }`, `timed("fetch") { ... }`. That's why `repeat`, `synchronized`, `use` and `buildList` look built in. They're ordinary library functions.

Java needs an interface for the parameter, and checked exceptions get in the way. Those are exceptions the compiler makes you catch or declare, like `IOException`. `Supplier.get()` can't throw one, so retrying file or network code needs a `Callable<T>` and a `throws Exception` on `retry`. Kotlin has no checked exceptions, so `() -> T` fits every call.

**When code differs by one call, pass the call in. Write the loop once.**

That's functions in. The friend can also hand back a new card."""

# ---------------------------------------------------------------- section 1
J_GRAMSFOR = """static Function<Integer, Integer> gramsFor(String ingredient) {
    int perLitre = WEIGHT_PER_LITRE.get(ingredient);       // looked up once
    return ml -> ml * perLitre / 1_000;
}

Function<Integer, Integer> honey = gramsFor("honey");
honey.apply(250);                                          // 355"""
K_GRAMSFOR = """fun gramsFor(ingredient: String): (Int) -> Int {
    val perLitre = WEIGHT_PER_LITRE.getValue(ingredient)    // looked up once
    return { ml -> ml * perLitre / 1_000 }
}

val honey = gramsFor("honey")
honey(250)                                                 // 355"""
J_CURRY = """Function<String, Function<Integer, Integer>> curriedGrams = ingredient -> ml -> grams(ingredient, ml);
curriedGrams.apply("flour").apply(500);                    // 265"""
K_CURRY = """val curriedGrams: (String) -> (Int) -> Int = { ingredient -> { ml -> grams(ingredient, ml) } }
curriedGrams("flour")(500)                                 // 265"""

S1 = """Higher-order works in the other direction too. A function can build another function and hand it back.

Here's a kitchen problem that needs it. Some recipes measure in millilitres, with a jug, but your scale wants grams. A litre of honey weighs roughly 1,420 g, and a litre of loosely spooned flour roughly 530 g. So the grams depend on two things: which ingredient, and how many millilitres. A plain function `grams(ingredient, ml)` takes both at once. This one takes the ingredient and returns a function that waits for the millilitres:

""" + pair(J_GRAMSFOR, K_GRAMSFOR) + """

Fixing some of a function's arguments and getting back a function of the rest is called **partial application**. In the kitchen, it's a card with one blank already filled in: "honey", so only the amount is left to write.

It pays off when the first argument is known early and the second arrives many times. Baking a honey cake, you know the ingredient once and measure many times. `gramsFor` looks the weight up once, and the closure it returns (lesson 2 of this track) keeps only the number it needs.

It also moves failure to the right moment. An unknown ingredient fails when you build the function, not halfway through the cake. Ask for `gramsFor("sand")` and you hear about it at once, before a single gram is weighed.

**Currying** takes the same idea all the way: every function takes exactly one argument and returns a function for the next. A curried converter has the type `(String) -> (Int) -> Int`. The arrows group to the right, so read it as `(String) -> ((Int) -> Int)`.

""" + pair(J_CURRY, K_CURRY) + """

Some languages, Haskell for one, curry every function. In Kotlin, don't. The signatures get hard to read and the IDE hints get noisy. And Kotlin already covers what currying is for: a lambda that fixes one argument (`{ ml: Int -> grams("milk", ml) }`), default and named arguments, and bound references like `oven::adjust` from the last lesson.

**Return a function when you mean "set up now, run many times". That's the case that earns its keep.**

One card at a time is useful. Clipping several cards together is where real recipes come from."""

# ---------------------------------------------------------------- section 2
J_COMPOSE = """Function<Integer, Integer> sugar = FOR_SIX_GUESTS.andThen(TEN_PERCENT_LESS).andThen(AT_MOST_THE_BAG);
sugar.apply(200);                                          // 250"""
K_COMPOSE = """infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

val sugar = forSixGuests andThen tenPercentLess andThen atMostTheBag
sugar(200)                                                 // 250"""
J_FOLDFN = """Function<Integer, Integer> fromList = steps.stream()
        .reduce(Function.identity(), (acc, step) -> acc.andThen(step));"""
K_FOLDFN = """val fromList = steps.fold({ x: Int -> x }) { acc, step -> acc andThen step }"""

S2 = """Adjustments to a recipe come in small pieces. Scale it from four people to six. Use 10 % less sugar, as plenty of cooks do. Never use more than the 250 g left in the bag. Each piece is an `(Int) -> Int` on grams. The amount you actually weigh out is some of those pieces run one after another, and every cook has a different set.

Running one function on the result of another is called **composition**. Java's `Function` interface has it built in, as two default methods, `andThen` and `compose`:

""" + pair(J_COMPOSE, K_COMPOSE) + """

Kotlin's standard library has no `andThen` or `compose` for function types. Without the one-line extension above, `forSixGuests andThen tenPercentLess` fails with `unresolved reference 'andThen' on receiver of type '(Int) -> Int'.` Arrow, the best-known functional library for Kotlin, ships `andThen`, `compose` and `curried` in a separate `arrow-functions` module. This track's lab doesn't depend on it.

One line is all you need, and writing it shows there's no magic: `this` is the first function, `this(a)` calls it, and `next` gets the result. `infix` lets you write it without dots and parentheses, so the steps read left to right in the order they run. `compose` is the same with the arguments swapped, `(g compose f)(x) == g(f(x))`, as mathematicians write it. Pick one and stay with it. `andThen` matches the way people read.

Two things about composition matter in practice. The first is that the order is part of the result. The demo runs the same three steps both ways:

```text
recipe says 100 g -> 135 g   (cap first: 135 g)
recipe says 200 g -> 250 g   (cap first: 270 g)
```

For 100 g the cap never bites, so the order doesn't show. For 200 g, scaling gives 300 g, 10 % less gives 270 g, and the cap brings it down to the 250 g you have. Cap first, and you check the bag before you've scaled: the recipe then asks for 270 g of sugar you don't own. It's the same with mixing, baking and icing. Ice before you bake and you still get something, just not a cake.

The second is that a list of steps folds into one function, starting from the function that returns its input unchanged:

""" + pair(J_FOLDFN, K_FOLDFN) + """

That's how saved settings become code. Read a cook's adjustments when the app starts, turn each one into a function, fold them into one `(Int) -> Int`, and call it for every ingredient. Every piece stays small, pure and testable on its own. (Lesson 4 of this track covers `fold` properly.)

**The order of the steps is part of the function. Test them in the order you'll run them.**

Composition builds new functions out of old ones. The next higher-order function improves a function without changing a single one of its answers."""

# ---------------------------------------------------------------- section 3
J_MEMO = """static <A, R> Function<A, R> memoize(Function<A, R> f) {
    Map<A, R> cache = new ConcurrentHashMap<>();
    return a -> cache.computeIfAbsent(a, f);
}

Function<String, Integer> kcal = memoize(Foods::kcalPer100g);"""
K_MEMO = """fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {
    val cache = ConcurrentHashMap<A, R>()
    return { a -> cache.computeIfAbsent(a) { f(it) } }
}

val kcal = memoize(::kcalPer100g)"""

S3 = """A higher-order function can also take a function and return an improved version of it. `memoize` returns a function that gives the same answers as the original but works each one out only once. Picture the friend writing the answer on the back of the card the first time, and reading it off after that.

""" + pair(J_MEMO, K_MEMO) + """

Everything from the last lesson is in those few lines. `memoize` takes a function and returns one. The returned lambda is a closure over `cache`, so each memoized function gets its own map that nobody else can reach.

It's safe on many threads because the captured state is a `ConcurrentHashMap`, a map built to be shared by threads, held in a `val` rather than a `var`. `computeIfAbsent` runs `f` at most once per key, even when two threads ask for the same key at the same moment, as the concurrent collections lesson showed. The `A : Any, R : Any` bounds are there because `ConcurrentHashMap` can't store null.

The demo's food table is slow on purpose, 50 ms a lookup, like a long table searched from the top every time. Five calls for oats and honey:

```text
[389, 304, 389, 389, 304]
lookups: 2 for 5 calls, 129 ms
```

Two lookups instead of five, and the same answers.

Memoizing is only correct for pure functions. Referential transparency, from lesson 1, says a pure call can be replaced by its value, and a cache does exactly that replacement for you. Memoize something impure and you get stale answers. The demo also memoizes `eggsIn("fridge")`, which reads how many eggs are left:

```text
eggs in the fridge now:        6
eggs after someone's omelette: 6   (really: 2)
```

The memo says six. The fridge holds two, and the memo will keep saying six until the program restarts. Here the friend picture breaks: a real cook can open the fridge and look, but a memo has no way to tell that its answer went stale.

Calories per 100 g of oats from a fixed table is a good fit. How many eggs are left, today's price of butter, or anything you read from a file or a database is not.

**Memoize only pure functions. A saved answer is right only if the function would have given it again.**

Two practical limits. The cache never forgets, so only memoize over a small, known set of keys (ingredients, units, recipe names), never over something that keeps growing, like timestamps. When you need expiry or a size limit, use a real cache library such as Caffeine, which is the same idea plus eviction, throwing old entries out. And the function you pass to `computeIfAbsent` must not change the same map, so this `memoize` can't wrap a recursive function that calls its own memoized version.

Each of these higher-order functions takes a lambda, and a lambda is an object. So what do all those objects cost?"""

# ---------------------------------------------------------------- section 4
J_INLINE = """// Java has no inline functions. The method reference is a lambda object
// (shared, since it captures nothing), and only the JIT may inline it at runtime.
long total = grams.stream().mapToLong(Long::longValue).sum();"""
K_INLINE = """inline fun <T> measuredInline(block: () -> T): T {
    val start = System.nanoTime()
    val result = block()
    lastNanos = System.nanoTime() - start
    return result
}

var total = 0L
measuredInline { grams.forEach { total += it } }   // becomes a plain loop; total stays a local"""

S4 = """Every lambda you pass to `retry` or `memoize` is an object (lesson 2), and a `var` it changes becomes a `Ref` box. So you might expect `recipes.filter { ... }.map { ... }` to create two lambda objects on every call. It creates none, because `filter`, `map`, `forEach`, `fold`, `sumOf` and almost every other collection function on `Iterable` are declared **`inline`**.

When you call an inline function, the compiler doesn't emit a call. It copies the function's body into the call site, and the lambda's body with it. The lambda never exists as an object.

""" + pair(J_INLINE, K_INLINE) + """

The `InlineCost` demo compiles two versions of the same code and adds up 500 g, 250 g and 1,000 g, the flour, sugar and milk for one cake. With a non-inline `measured`, the bytecode (the instructions the JVM actually runs) has `new Ref$LongRef`, a box for `total`. It also has an `invokedynamic`, the instruction that creates the lambda object, and a call through `Function0.invoke`.

With `measuredInline` it has none of them: the `System.nanoTime()` calls, the iterator loop and an `ladd` on a local variable are pasted straight into `totalInlined`. (`ladd` is the bytecode instruction that adds two `long` values.) The JIT compiler, the part of the JVM that turns busy code into machine code while the program runs, may inline Java's lambda later. Kotlin's `inline` does it before the program ever starts.

That's also why `return` inside `repeat` worked in `retry`. After inlining, the lambda body is part of `retry`, so `return` leaves `retry`. This is called a **non-local return**, and it's only allowed when the lambda is inlined.

**Inline a small higher-order function that calls its lambda right away. Leave the rest alone.**

So mark your own small higher-order functions `inline` when they take a lambda and call it straight away, as `measuredInline` and `retry` do. Don't mark everything `inline`. The body is copied into every call site, so a big inline function bloats the code. And a lambda you keep for later, like the `f` that `memoize` stores in its closure, can't be inlined: the compiler needs a real object to keep. The Advanced Kotlin track, later in this part of the course, has a whole lesson on `inline`, `noinline`, `crossinline` and non-local returns.

`inline` removes the lambda objects, not the work. Each `filter` or `map` on a list still builds a whole new list, and that's the cost the next lesson puts on the table."""

L = {
    "id": "fp-03",
    "title": "Higher-order functions: functions in, functions out",
    "minutes": 35,
    "goal": "By the end you can write your own higher-order functions (retry, timed, memoize), return functions to set up behaviour once, compose small functions into a pipeline, and say when inline makes a lambda free.",
    "opening": OPENING,
    "warmup": {
        "q": "In Kotlin, `recipes.filter { it.vegan }.map { it.name }` runs on a `List`. How many lambda objects does one call create?",
        "options": [
            "Two, one per lambda",
            "One, shared by both steps",
            "None: `filter` and `map` are inline, so the lambda bodies are copied into plain loops",
            "Two per element"
        ],
        "answer": 2,
        "why": "`filter` and `map` on `Iterable` are `inline` functions. The compiler pastes their loops, and the bodies of your lambdas, into the calling method, so no lambda object is ever created. The call still builds two new `ArrayList`s, one per step: that is the real cost of a chain, and the next lessons deal with it. Lesson 2's answer, one object per capturing lambda, applies to functions that are not inline. The last section shows the bytecode."
    },
    "sections": [
        {
            "h": "Passing in the part that changes: retry and timed take a function",
            "body": S0,
            "try": {
                "title": "One retry loop for every flaky call",
                "minutes": 4,
                "steps": [
                    "Run `Retry` (or `RetryJava`). Predict first: how many calls reach the website in each half?",
                    "Wrap the second `retry` in `timed(\"gave up\") { ... }` as well. Predict whether its timing line prints, even though the block throws.",
                    "Change the first `retry(3)` to `retry(1)` and run again."
                ],
                "code": kdemo("Retry"),
                "expect": "The first half takes three calls: two timeouts, then `page:pancakes`. The second gives up after three: `gave up after 3 attempts (last cause: site timeout on call 3)`. `timed` prints its line even when the block throws, because the print is in a `finally`. With `retry(1)`, the program stops with `IllegalStateException: gave up after 1 attempts`, a message that never expected to be used with one attempt. `retry` never changed in any of these runs; only the function you handed it did."
            }
        },
        {
            "h": "Handing back a function: set up the converter once",
            "body": S1,
            "try": {
                "title": "When does a bad ingredient fail?",
                "minutes": 4,
                "steps": [
                    "Run `GramsFor` (or `GramsForJava`) and check one number: 250 ml of honey at 1,420 g a litre is 355 g.",
                    "Add `val broken = gramsFor(\"sand\")` as the first line of `main`, without calling `broken`. Predict whether the program fails, and where.",
                    "Move the lookup into the returned lambda: `return { ml -> ml * WEIGHT_PER_LITRE.getValue(ingredient) / 1_000 }` (Java: `WEIGHT_PER_LITRE.get(ingredient)` inside the lambda). Run again. Now when does it fail?"
                ],
                "code": kdemo("GramsFor"),
                "expect": "With the lookup outside the lambda, `gramsFor(\"sand\")` fails right away: Kotlin throws `NoSuchElementException: Key sand is missing in the map.`, and Java throws a `NullPointerException` when it unboxes the missing weight. With the lookup inside the lambda, `gramsFor(\"sand\")` succeeds and returns a function that fails on its first call, which could be much later. Same code, different moment of failure. You want the first one."
            }
        },
        {
            "h": "Clipping small functions together: composition, where order matters",
            "body": S2,
            "figure": {"svg": FIG, "caption": "Composition turns three small steps into one. The order is part of the function: capping last gives the 250 g in the bag, capping first asks for 270 g."},
            "try": {
                "title": "Compose, reorder, extend",
                "minutes": 4,
                "steps": [
                    "Run `Compose` (or `ComposeJava`). Predict both amounts for 100 g and for 200 g before you look.",
                    "Delete the `andThen` extension at the top of `Compose.kt` and run again. Read the error, then put the line back.",
                    "Add a fourth step, `val roundToTen: (Int) -> Int = { it / 10 * 10 }`, at the end of `steps`, and print `fromList(130)`. Predict it first."
                ],
                "code": kdemo("Compose"),
                "expect": "100 g gives 135 g both ways, because the cap never bites. 200 g gives 250 g with the cap last and 270 g with the cap first. Without the extension, Kotlin reports `unresolved reference 'andThen' on receiver of type '(Int) -> Int'.` The Java version has nothing to delete: `andThen` is a default method on `Function`. With `roundToTen`, `fromList(130)` goes 195, then 175, then 175 again (under the cap), then 170."
            },
            "refs": [
                {"title": "Function: andThen, compose, identity (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/function/Function.html", "kind": "docs"}
            ]
        },
        {
            "h": "memoize: a function that remembers its answers, and when that lies",
            "body": S3,
            "try": {
                "title": "A memo that helps, and one that lies",
                "minutes": 4,
                "steps": [
                    "Run `Memoize` (or `MemoizeJava`). Predict the number of lookups for the five foods, and roughly how long they take (each real lookup sleeps 50 ms).",
                    "Replace `memoize(::kcalPer100g)` with plain `::kcalPer100g` and run again.",
                    "Explain the last line of the output to yourself before you read the expected result. Why is the memoized egg count wrong?"
                ],
                "code": kdemo("Memoize"),
                "expect": "Memoized: 2 lookups for 5 calls, a little over 100 ms. Without `memoize`: 5 lookups, about 250 ms, and the same answers. The egg line prints 6 after the fridge dropped to 2. `eggsIn` reads a mutable global, so it is impure, and the memo froze its first answer. A cache is only invisible when the function it wraps is pure."
            },
            "refs": [
                {"title": "ConcurrentHashMap.computeIfAbsent (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html", "kind": "docs"}
            ]
        },
        {
            "h": "inline: why map and filter create no lambdas",
            "body": S4,
            "try": {
                "title": "Find the missing lambda in the bytecode",
                "minutes": 4,
                "steps": [
                    "Run `InlineCost`. Both totals print 1750. (Java has no `inline` functions, so this demo has no Java twin.)",
                    "From `labs/`, run `javap -c -p functional/build/classes/kotlin/demo/workbench/functional/l03/demo/InlineCostKt.class`. Compare `totalWithLambda` with `totalInlined`: look for `Ref$LongRef`, `invokedynamic` and `System.nanoTime`.",
                    "Predict what changes in `totalInlined` if you delete the word `inline` from `measuredInline`. Then try it."
                ],
                "code": kdemo("InlineCost", alt=False),
                "expect": "`totalWithLambda` has `new kotlin/jvm/internal/Ref$LongRef`, an `invokedynamic` that makes a `Function0`, and a call to `measured`. `totalInlined` has none of them: it calls `System.nanoTime` itself and adds into a local with `ladd`. Without `inline`, `totalInlined` looks like `totalWithLambda`: a `Ref$LongRef`, an `invokedynamic` and a call to `measuredInline`. `measuredInline` also exists as an ordinary method in the class, for callers such as Java code that can't inline it."
            },
            "refs": [
                {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "Functions in, functions out, functions combined",
        "java": {
            "title": "Kitchen.java",
            "src": "import java.util.Map;\nimport java.util.concurrent.ConcurrentHashMap;\nimport java.util.function.Function;\nimport java.util.function.Supplier;\n\nfinal class Kitchen {\n    // functions in\n    static <T> T retry(int times, Supplier<T> block) {\n        RuntimeException last = null;\n        for (int i = 0; i < times; i++) {\n            try { return block.get(); } catch (RuntimeException e) { last = e; }\n        }\n        throw new IllegalStateException(\"gave up after \" + times + \" attempts\", last);\n    }\n\n    // functions out: partial application\n    static Function<Integer, Integer> gramsFor(int perLitre) {\n        return ml -> ml * perLitre / 1_000;\n    }\n\n    // composition is built into Function\n    static Function<Integer, Integer> sugarToWeigh(int perLitre) {\n        return gramsFor(perLitre).andThen(g -> g * 90 / 100).andThen(g -> Math.min(g, 250));\n    }\n\n    static <A, R> Function<A, R> memoize(Function<A, R> f) {\n        Map<A, R> cache = new ConcurrentHashMap<>();\n        return a -> cache.computeIfAbsent(a, f);\n    }\n}"
        },
        "kotlin": {
            "title": "Kitchen.kt",
            "src": "import java.util.concurrent.ConcurrentHashMap\n\n// functions in; inline, so the lambda is pasted into the caller\ninline fun <T> retry(times: Int, block: () -> T): T {\n    var last: Exception? = null\n    repeat(times) {\n        try { return block() } catch (e: Exception) { last = e }\n    }\n    throw IllegalStateException(\"gave up after $times attempts\", last)\n}\n\n// functions out: partial application\nfun gramsFor(perLitre: Int): (Int) -> Int = { ml -> ml * perLitre / 1_000 }\n\n// composition is not in the stdlib: one line of your own\ninfix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }\n\nfun sugarToWeigh(perLitre: Int): (Int) -> Int =\n    gramsFor(perLitre) andThen { g -> g * 90 / 100 } andThen { g -> minOf(g, 250) }\n\nfun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {\n    val cache = ConcurrentHashMap<A, R>()\n    return { a -> cache.computeIfAbsent(a) { f(it) } }\n}"
        },
        "note": "Both languages make the same three moves: functions in, functions out, functions combined. The differences are in the plumbing. Java's `Function` comes with `andThen` and `compose`, and Kotlin's function types don't, so you write the extension yourself or use Arrow's `arrow-functions` module. Java needs a different interface per shape (`Supplier`, `Function`, `Callable` once checked exceptions appear), while Kotlin uses `() -> T` and `(A) -> R` everywhere. And Kotlin can declare a higher-order function `inline`, so the lambda passed to `retry` is pasted into the caller and never allocated. Java leaves that to the JIT, which may or may not inline at runtime."
    },
    "worked": {
        "title": "Turn a cook's saved adjustments into one function",
        "steps": [
            {
                "say": "A cook's adjustments are saved as rows: a kind of adjustment and a number. We want one `(Int) -> Int` per ingredient, built once when the app starts and called for every measurement. The base step is the jug-to-scale converter, `gramsFor(ingredient)`, from the second section.",
                "code": "data class AdjustmentRow(val kind: String, val value: Int)\n\nval myRows = listOf(\n    AdjustmentRow(\"less\", 10),       // 10 % less\n    AdjustmentRow(\"atLeast\", 50),    // at least 50 g\n    AdjustmentRow(\"atMost\", 300),    // at most 300 g\n)",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "record AdjustmentRow(String kind, int value) {}\n\nList<AdjustmentRow> myRows = List.of(\n        new AdjustmentRow(\"less\", 10),       // 10 % less\n        new AdjustmentRow(\"atLeast\", 50),    // at least 50 g\n        new AdjustmentRow(\"atMost\", 300));   // at most 300 g"
            },
            {
                "say": "1. Turn each row into a function with a `when` expression. Each branch returns a function, and nothing is computed yet. An unknown kind is a bug in the saved settings, so it throws here.",
                "code": "fun toAdjust(row: AdjustmentRow): (Int) -> Int = when (row.kind) {\n    \"add\" -> { g -> g + row.value }\n    \"less\" -> { g -> g * (100 - row.value) / 100 }\n    \"atLeast\" -> { g -> maxOf(g, row.value) }\n    \"atMost\" -> { g -> minOf(g, row.value) }\n    else -> throw IllegalArgumentException(\"unknown adjustment ${row.kind}\")\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static Function<Integer, Integer> toAdjust(AdjustmentRow row) {\n    return switch (row.kind()) {\n        case \"add\" -> g -> g + row.value();\n        case \"less\" -> g -> g * (100 - row.value()) / 100;\n        case \"atLeast\" -> g -> Math.max(g, row.value());\n        case \"atMost\" -> g -> Math.min(g, row.value());\n        default -> throw new IllegalArgumentException(\"unknown adjustment \" + row.kind());\n    };\n}"
            },
            {
                "say": "2. Fold the adjustments onto the ingredient's converter. Self-check: when does a row with an unknown kind fail, at startup or at the first measurement? (At startup: `toAdjust` runs inside `map`, while the function is being built.)",
                "code": "fun measure(ingredient: String, rows: List<AdjustmentRow>): (Int) -> Int =\n    rows.map(::toAdjust)                                      // 1. rows to functions\n        .fold(gramsFor(ingredient)) { acc, f -> acc andThen f } // 2. one function, converter first",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static Function<Integer, Integer> measure(String ingredient, List<AdjustmentRow> rows) {\n    return rows.stream()\n            .map(Kitchen::toAdjust)                               // 1. rows to functions\n            .reduce(gramsFor(ingredient), Function::andThen);     // 2. one function, converter first\n}"
            },
            {
                "say": "3. Build once per ingredient, call per measurement. Each measurement now costs four small calls and no lookups, and every adjustment can be tested on its own with plain numbers.",
                "code": "val sugar = measure(\"sugar\", myRows)\n\nsugar(500)    // 425 -> 382 -> 382 -> 300\nsugar(50)     // 42 -> 37 -> 50 -> 50",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Function<Integer, Integer> sugar = measure(\"sugar\", myRows);\n\nsugar.apply(500);   // 425 -> 382 -> 382 -> 300\nsugar.apply(50);    // 42 -> 37 -> 50 -> 50"
            }
        ]
    },
    "lab": {
        "title": "Compose a measuring pipeline, and memoize a slow lookup",
        "minutes": 13,
        "files": [
            "labs/functional/src/main/kotlin/workbench/functional/l03/Pipeline.kt",
            "labs/functional/src/main/kotlin/workbench/functional/l03/Memo.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l03.*'",
        "steps": [
            "Run the tests. All ten fail with `NotImplementedError`. Read the four finished building blocks at the top of `Pipeline.kt` (`add`, `percentLess`, `atMost`, `atLeast`): each one is a function that returns a function.",
            "Write `andThen` and `compose`. Each body is one lambda.",
            "Write `pipeline` with `fold`, starting from `{ x: T -> x }`. An empty list must give back that identity function.",
            "Write `gramsFor`. Do the lookup outside the lambda you return, and throw `IllegalArgumentException(\"unknown ingredient $ingredient\")` for an ingredient that isn't in `GRAMS_PER_LITRE`.",
            "Write `weighOut` from `gramsFor`, `andThen` and `pipeline`. Then write `curried`.",
            "Write `memoize` in `Memo.kt`. Run the tests until all ten pass."
        ],
        "hints": [
            "`andThen` is `{ a -> next(this(a)) }`. Inside an extension on a function type, `this` is the function, and `this(a)` calls it.",
            "`requireNotNull(GRAMS_PER_LITRE[ingredient]) { \"unknown ingredient $ingredient\" }` returns the weight, or throws `IllegalArgumentException` with that message.",
            "`ConcurrentHashMap.computeIfAbsent(key) { f(it) }` calls `f` only when the key is missing. A `HashMap` with `getOrPut` also passes these tests, but it isn't safe once several threads share the memoized function."
        ],
        "done_when": "All ten tests in `HigherOrderTest` pass."
    },
    "drill": {
        "title": "Write retry and andThen from memory",
        "minutes": 5,
        "prompt": "Close this page. Write an `inline` function `retry(times, block)` that calls `block` until it returns, at most `times` times, and then throws `IllegalStateException` with the last failure as its cause. Write `andThen` for function types. Use both: retry a call that fetches a recipe's sugar in grams from a website, then run the grams through `{ it * 90 / 100 } andThen { minOf(it, 250) }`. Then write the Java version of both functions.",
        "answer": {
            "lang": "kotlin",
            "src": "inline fun <T> retry(times: Int, block: () -> T): T {\n    var last: Exception? = null\n    repeat(times) {\n        try { return block() } catch (e: Exception) { last = e }   // non-local return: repeat is inline\n    }\n    throw IllegalStateException(\"gave up after $times attempts\", last)\n}\n\ninfix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }\n\nval adjust: (Int) -> Int = { g: Int -> g * 90 / 100 } andThen { g -> minOf(g, 250) }\nval sugar = adjust(retry(3) { site.sugarGrams(\"pancakes\") })",
            "alt": {
                "lang": "java",
                "src": "static <T> T retry(int times, Supplier<T> block) {\n    RuntimeException last = null;\n    for (int i = 0; i < times; i++) {\n        try { return block.get(); } catch (RuntimeException e) { last = e; }\n    }\n    throw new IllegalStateException(\"gave up after \" + times + \" attempts\", last);\n}\n\n// andThen is already a default method on java.util.function.Function\nFunction<Integer, Integer> lessSugar = g -> g * 90 / 100;\nFunction<Integer, Integer> adjust = lessSugar.andThen(g -> Math.min(g, 250));\nint sugar = adjust.apply(retry(3, () -> site.sugarGrams(\"pancakes\")));"
            }
        }
    },
    "recap": [
        "A higher-order function takes a function, returns one, or both. It keeps the shape of a computation (retry, time, remember) apart from the work inside it.",
        "Trailing lambdas make higher-order calls read like built-ins: `retry(3) { site.fetch(\"pancakes\") }`.",
        "Returning a function gives you partial application: `gramsFor(ingredient)` looks the weight up once and returns an `(Int) -> Int`. Prefer that, or a plain lambda, to curried signatures.",
        "Kotlin's stdlib has no `andThen` or `compose` for function types; write the one-line infix extension (Java's `Function` has both). Order matters, and a list of steps folds into one function.",
        "Memoize only pure functions, over a small set of keys. A memoized impure function returns stale answers until restart, and it can't tell.",
        "`inline` pastes a function and its lambda into the call site: no lambda object, no `Ref` box, and `return` leaves the enclosing function. Its limit: each `map` or `filter` on a list still builds a whole new list."
    ],
    "closing": "We started with a friend who takes any recipe card and hands back a new one. `retry` and `timed` took the work as a function, `gramsFor` handed back a converter set up once, `andThen` clipped small steps together in an order that matters, and `memoize` remembered answers, honestly only for pure functions.\n\nSearch your code for two loops that differ by one call, and for a `fun` that takes a lambda and calls it right away without `inline`. The first wants a higher-order function; the second wants one word.\n\nNext, we'll put these functions to work on whole collections. What does a loop that builds four results at once look like without the loop?",
    "quiz": [
        {
            "q": "`val a = atMost(250) andThen add(25)` and `val b = add(25) andThen atMost(250)`. What are `a(240)` and `b(240)`?",
            "options": [
                "265 and 250",
                "250 and 265",
                "265 and 265",
                "250 and 250"
            ],
            "answer": 0,
            "why": "`andThen` runs the left function first. `a` caps 240 (no change) and then adds 25, giving 265. `b` adds 25 (265) and then caps at 250. Composition is not commutative: the order of the steps is part of the function."
        },
        {
            "q": "`fun gramsFor(ingredient: String): (Int) -> Int { val perLitre = weights.getValue(ingredient); return { it * perLitre / 1000 } }`. A recipe typo passes `\"hony\"`. When does it fail?",
            "options": [
                "At the first measurement that uses the function",
                "When `gramsFor(\"hony\")` is called, before anything is weighed",
                "Never: the weight comes out as 0",
                "At compile time"
            ],
            "answer": 1,
            "why": "The lookup sits outside the returned lambda, so it runs when the function is built, and `getValue` throws `NoSuchElementException: Key hony is missing in the map.` Building converters when the app starts turns typos into startup failures. If the lookup were inside the lambda, the first measurement would fail instead."
        },
        {
            "q": "Which of these functions is safe to memoize?",
            "options": [
                "`fun eggsLeft(fridge: String): Int`, which counts what's in the fridge now",
                "`fun butterPrice(shop: String): Int`, which asks the shop's website",
                "`fun gramsPerCup(ingredient: String): Int`, which reads a fixed table printed in the recipe book",
                "`fun nextJarNumber(shelf: String): Int`"
            ],
            "answer": 2,
            "why": "Only `gramsPerCup` is pure: the same ingredient always gives the same weight, so a saved answer is always right. The eggs and the price change over time, so a memoized version would freeze them. `nextJarNumber` is supposed to return a new value on every call, so memoizing it would hand out the same number forever."
        },
        {
            "q": "`fun <T> timed(block: () -> T): T` is not `inline`. You call it as `var n = 0; timed { n++ }`. What does the compiler create at that call site?",
            "options": [
                "Nothing extra: Kotlin inlines small lambdas on its own",
                "A new `.class` file for the lambda",
                "A compile error: a lambda can't change a captured `var`",
                "A lambda object through `invokedynamic`, and a `Ref$IntRef` box for `n`"
            ],
            "answer": 3,
            "why": "Without `inline`, the lambda is a real object, created with `invokedynamic` (no class file in Kotlin 2.x), and the captured `var n` moves into a `Ref$IntRef`. Kotlin never inlines a function you didn't mark `inline`. Mark `timed` inline and both disappear: the body and the lambda are pasted into the caller, and `n` stays a local."
        },
        {
            "q": "From Concurrent collections: two threads call a memoized function with the same new key at the same moment. The cache is a `ConcurrentHashMap` and uses `computeIfAbsent(key) { f(it) }`. How many times does `f` run for that key?",
            "options": [
                "Exactly once: the second thread waits and gets the first one's result",
                "Twice, once per thread",
                "Once or twice, depending on timing",
                "Zero: the second thread throws"
            ],
            "answer": 0,
            "why": "`ConcurrentHashMap.computeIfAbsent` is atomic per key: it runs the mapping function at most once, and a second caller for the same key waits for that result. A `HashMap` with `getOrPut`, or `get` followed by `put`, is check-then-act and can run `f` twice.",
            "from": "conc-09"
        }
    ],
    "flashcards": [
        {"front": "What makes a function higher-order?", "back": "It takes a function as a parameter, returns a function, or both."},
        {"front": "What is partial application?", "back": "Fixing some of a function's arguments now and getting back a function of the rest. `gramsFor(\"honey\")` returns an `(Int) -> Int`."},
        {"front": "Does Kotlin's stdlib have `andThen` for function types?", "back": "No: `f andThen g` gives `unresolved reference 'andThen'`. Write `infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }`."},
        {"front": "What do you start a `fold` from to compose a list of `(T) -> T` steps?", "back": "The identity function, `{ x: T -> x }`. An empty pipeline is exactly that function."},
        {"front": "When is it safe to memoize a function?", "back": "When it's pure: the same argument always gives the same answer. Otherwise the cache keeps a stale answer."},
        {"front": "What does `inline` do to `measuredInline { total += x }`?", "back": "The compiler copies the function's body and the lambda's body into the caller. No lambda object is created, and `total` stays a local instead of a `Ref` box."},
        {"front": "Why can `return` inside `repeat { }` leave the enclosing function?", "back": "`repeat` is inline, so the lambda's body becomes part of the enclosing function. That non-local return is only allowed for inlined lambdas."}
    ],
    "terms": [
        {"term": "Higher-order function", "plain": "A function that takes a function as a parameter, returns one, or both."},
        {"term": "Trailing lambda", "plain": "A lambda written after the parentheses when it is the last argument: `retry(3) { ... }`."},
        {"term": "Partial application", "plain": "Fixing some arguments now and getting back a function of the rest."},
        {"term": "Currying", "plain": "Turning `(A, B) -> C` into `(A) -> (B) -> C`: one argument at a time."},
        {"term": "Composition", "plain": "Running one function on another's result: `f andThen g` is `{ x -> g(f(x)) }`."},
        {"term": "Memoization", "plain": "Remembering a pure function's results so each one is worked out only once."},
        {"term": "Inline function", "plain": "A function whose body, and the bodies of the lambdas passed to it, the compiler copies into each call site."}
    ],
    "explain_back": {
        "prompt": "A teammate asks why `recipes.filter { it.vegan }.map { it.name }` creates no lambda objects, while their own `fun <T> timed(block: () -> T): T` does. Explain it in your own words, and say what you'd change in `timed`.",
        "answer": "A lambda is normally an object: a function value that something has to create, and if it changes a captured `var`, that `var` moves into a `Ref` box. `filter` and `map` on lists are declared `inline`, so the compiler never calls them. It copies their loops into my method and pastes my lambda bodies into those loops, and no lambda object ever exists. `timed` isn't inline, so its `block` has to be a real object passed to a real call. Since `timed` only calls `block` once, right away, I'd mark it `inline`. Then the timing code and the block are pasted into each caller, with no allocation and no `Ref` box. I wouldn't do that for a function that stores its lambda, like `memoize`, because a stored lambda has to be an object."
    },
    "deeper": {
        "minutes": 10,
        "body": "Kotlin gives you partial application in a few forms besides returning a lambda. A bound reference fixes the receiver, which is often all you need:\n\n```kotlin\nclass Oven(private val extraMinutes: Int) {\n    fun adjust(minutes: Int): Int = minutes + extraMinutes\n}\n\nval myOven = Oven(extraMinutes = 5)               // this oven runs a little cold\nval bake: (Int) -> Int = myOven::adjust           // a bound reference: the receiver is fixed\nlistOf(20, 35).map(bake)                          // [25, 40]\n```\n\n```java\nfinal class Oven {\n    private final int extraMinutes;\n    Oven(int extraMinutes) { this.extraMinutes = extraMinutes; }\n    int adjust(int minutes) { return minutes + extraMinutes; }\n}\n\nOven myOven = new Oven(5);\nFunction<Integer, Integer> bake = myOven::adjust;    // a bound method reference\nList.of(20, 35).stream().map(bake).toList();          // [25, 40]\n```\n\nThis is the strategy pattern with the ceremony removed: an object with one behaviour, passed around as a function. Remember lesson 2's detail, though: in Kotlin 2.4.21 a bound reference compiles to a small class and allocates one object each time the expression runs.\n\nArrow 2.3.0 puts its function utilities in the `io.arrow-kt:arrow-functions` artifact, separate from `arrow-core`. Its jar contains `andThen` and `compose`, `curried` and `uncurried` with overloads up to 22 parameters, `partially1` and its siblings, and `memoize`. If your codebase already uses Arrow, use those rather than your own. If it doesn't, the one-line versions in this lesson are not a reason to add a dependency.\n\nOne more look at `inline` and `return`. Inside an inline higher-order function's lambda, a bare `return` leaves the enclosing function, and `return@forEach` (or any label) leaves only the lambda, acting like `continue`. Java developers moving to Kotlin trip on this in `forEach`, because a `return` in a Java `Stream.forEach` lambda only ends that one call. The Advanced Kotlin track's inline lesson goes through `noinline` and `crossinline`, the two modifiers that control which lambdas get pasted and where `return` may go."
    },
    "sources": [
        {"title": "Higher-order functions and lambdas (Kotlin docs)", "url": "https://kotlinlang.org/docs/lambdas.html"},
        {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
        {"title": "Function (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/function/Function.html"},
        {"title": "ConcurrentHashMap (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html"}
    ]
}

out = ROOT / "content/lessons/fp-03.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
