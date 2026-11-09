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


def step(x, y, w, label, cls="box-a"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="40" rx="8"/>'
            f'<text class="t-s" x="{x + w // 2}" y="{y + 25}" text-anchor="middle">{label}</text>')


def val(x, y, label, cls="t-s t-code"):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="middle">{label}</text>'


def arrow(x1, x2, y):
    return f'<line class="ln-a" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'


FIG = (
    '<svg viewBox="0 0 720 240" role="img" aria-label="Three small fee functions composed into one. A fee of 1200 becomes 1225 after the scheme fee, 1102 after the discount and 1000 after the cap. '
    'Composed in the other order, with the cap first, the same fee becomes 922.">'
    '<rect class="box-dim" x="72" y="40" width="586" height="70" rx="8"/>'
    '<text class="t-s t-code" x="365" y="30" text-anchor="middle">price = addSchemeFee andThen loyaltyDiscount andThen capAtTenEuros</text>'
    + val(35, 80, "1200") + arrow(58, 78, 75)
    + step(80, 55, 140, "+25 scheme fee") + arrow(220, 240, 75)
    + val(265, 80, "1225") + arrow(288, 308, 75)
    + step(310, 55, 140, "10% loyalty off") + arrow(450, 470, 75)
    + val(495, 80, "1102") + arrow(518, 538, 75)
    + step(540, 55, 110, "cap at 1000") + arrow(650, 668, 75)
    + val(690, 80, "1000", "t-s t-code t-ok")
    + '<text class="t-s t-m" x="365" y="150" text-anchor="middle">capFirst = capAtTenEuros andThen addSchemeFee andThen loyaltyDiscount</text>'
    + val(35, 195, "1200") + arrow(58, 78, 190)
    + step(80, 170, 140, "cap at 1000", "box") + arrow(220, 240, 190)
    + val(265, 195, "1000") + arrow(288, 308, 190)
    + step(310, 170, 140, "+25 scheme fee", "box") + arrow(450, 470, 190)
    + val(495, 195, "1025") + arrow(518, 538, 190)
    + step(540, 170, 110, "10% off", "box") + arrow(650, 668, 190)
    + val(690, 195, "922", "t-s t-code t-bad")
    + '</svg>'
)

S1 = """Look at three places in a payment service that call something flaky:

```java
// authorize
for (int attempt = 1; ; attempt++) {
    try { auth = issuer.authorize(payment); break; }
    catch (IssuerTimeoutException e) { if (attempt == 3) throw e; }
}
// post to the ledger: the same loop around ledger.post(entry)
// fetch the FX rate: the same loop around fx.rate("EURUSD")
```

```kotlin
// authorize
var attempt = 1
while (true) {
    try { auth = issuer.authorize(payment); break }
    catch (e: IssuerTimeoutException) { if (attempt++ == 3) throw e }
}
// post to the ledger: the same loop around ledger.post(entry)
// fetch the FX rate: the same loop around fx.rate("EURUSD")
```

The three loops are identical except for one call. An ordinary helper method can't pull that call out, because a method's parameters are values, and the call has to happen inside the loop, up to three times. What you need to pass in is the work itself.

A **higher-order function** is a function that takes a function as a parameter, returns one, or both. Here is retry written as one:

```java
static <T> T retry(int times, Supplier<T> block) {
    RuntimeException last = null;
    for (int attempt = 1; attempt <= times; attempt++) {
        try { return block.get(); }
        catch (RuntimeException e) { last = e; }
    }
    throw new IllegalStateException("gave up after " + times + " attempts", last);
}

String auth = retry(3, () -> issuer.authorize(payment));
```

```kotlin
fun <T> retry(times: Int, block: () -> T): T {
    var last: Exception? = null
    repeat(times) {
        try { return block() } catch (e: Exception) { last = e }
    }
    throw IllegalStateException("gave up after $times attempts", last)
}

val auth = retry(3) { issuer.authorize(payment) }
```

The loop is written once. The part that varies, the call, arrives as `block`, and `retry` decides when and how often to run it. That is the whole idea of this lesson: keep the shape of a computation (retry it, time it, cache it) apart from the work inside it. (The `return` inside `repeat` leaves `retry` itself. That only works because `repeat` is `inline`, which the last section explains.)

Kotlin makes the call site read like a language feature. When the last parameter is a function, you can write the lambda after the parentheses, a **trailing lambda**, and if it's the only argument you drop the parentheses too: `retry(3) { ... }`, `timed("auth") { ... }`. That's why `repeat`, `synchronized`, `use` and `buildList` look built in. They are ordinary library functions.

Java needs an interface for the parameter, and checked exceptions get in the way. `Supplier.get()` can't throw an `IOException`, so retrying I/O needs a `Callable<T>` and a `throws Exception` on `retry`. Kotlin has no checked exceptions, so `() -> T` fits every call."""

S2 = """Higher-order works in the other direction too. A function can build another function and hand it back.

```java
static Function<Long, Long> feeFor(String country) {
    long bps = RATES_BPS.get(country);                   // looked up once
    return amountCents -> amountCents * bps / 10_000;
}

Function<Long, Long> dutch = feeFor("NL");
dutch.apply(100_000L);                                   // 1400
```

```kotlin
fun feeFor(country: String): (Long) -> Long {
    val bps = RATES_BPS.getValue(country)                // looked up once
    return { amountCents -> amountCents * bps / 10_000 }
}

val dutch = feeFor("NL")
dutch(100_000)                                           // 1400
```

`fee(country, amount)` needs two arguments. `feeFor(country)` takes the first one now and gives back a function that waits for the second. Fixing some of a function's arguments and getting back a function of the rest is called **partial application**.

It pays off when the first argument is known early and the second arrives many times. A settlement job knows each merchant's country at startup and then computes thousands of fees. `feeFor` looks the rate up once, and the closure it returns (lesson 2) keeps only the number it needs. It also moves failure to the right moment. An unknown country fails when you build the function, at startup, not on the first payment at 3 a.m.

**Currying** takes the same idea all the way: every function takes exactly one argument and returns a function for the next. A curried fee has the type `(String) -> (Long) -> Long`. The arrows group to the right, so read it as `(String) -> ((Long) -> Long)`.

```java
Function<String, Function<Long, Long>> curriedFee = country -> amount -> fee(country, amount);
curriedFee.apply("DE").apply(100_000L);                  // 1500
```

```kotlin
val curriedFee: (String) -> (Long) -> Long = { country -> { amount -> fee(country, amount) } }
curriedFee("DE")(100_000)                                // 1500
```

Haskell curries every function. In Kotlin, don't. The signatures get hard to read, the IDE hints get noisy, and Kotlin already covers what currying is for: a lambda that fixes one argument (`{ a: Long -> fee("US", a) }`), default and named arguments, and bound references like `merchant::fee`. Write a function that returns a function when you mean "configure now, run many times", like `feeFor`. That's the case that earns its keep."""

S3 = """Fee adjustments come in small pieces: add a 25-cent scheme fee, take 10 % off for loyal merchants, cap at 10 euros. Each piece is a `(Long) -> Long`. A merchant's price is some of those pieces run one after another, and each merchant has a different set.

Running one function on the result of another is called **composition**. Java's `Function` interface has it built in, as two default methods, `andThen` and `compose`:

```java
Function<Long, Long> price = addSchemeFee.andThen(loyaltyDiscount).andThen(capAtTenEuros);
price.apply(1_200L);                                      // 1000
```

```kotlin
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

val price = addSchemeFee andThen loyaltyDiscount andThen capAtTenEuros
price(1_200)                                              // 1000
```

Kotlin's standard library has no `andThen` or `compose` for function types. Without the one-line extension above, `addSchemeFee andThen loyaltyDiscount` fails with `unresolved reference 'andThen' on receiver of type '(Long) -> Long'.` Arrow, the best-known functional library for Kotlin, ships `andThen`, `compose` and `curried` in a separate `arrow-functions` module. This track's lab doesn't depend on it. One line is all you need, and writing it shows there is no magic: `this` is the first function, `this(a)` calls it, and `next` gets the result. `infix` lets you write it without dots and parentheses, so the steps read left to right in the order they run. `compose` is the same with the arguments swapped, `(g compose f)(x) == g(f(x))`, as mathematicians write it. Pick one and stay with it. `andThen` matches the way people read.

Two things about composition matter in practice. The order is part of the result: capping before the scheme fee gives 922 cents, capping after it gives 1,000. And a list of steps folds into one function, starting from the function that returns its input unchanged:

```java
Function<Long, Long> merchantPrice = steps.stream()
        .reduce(Function.identity(), (acc, step) -> acc.andThen(step));
```

```kotlin
val merchantPrice = steps.fold({ x: Long -> x }) { acc, step -> acc andThen step }
```

That's how configuration becomes code. Read a merchant's adjustments at startup, turn each row into a function, fold them into one `(Long) -> Long`, and call it for every payment. Every piece stays small, pure and testable on its own. (Lesson 4 covers `fold` properly.)"""

S4 = """A higher-order function can also take a function and return an improved version of it. `memoize` returns a function that gives the same answers as the original but computes each one only once.

```java
static <A, R> Function<A, R> memoize(Function<A, R> f) {
    Map<A, R> cache = new ConcurrentHashMap<>();
    return a -> cache.computeIfAbsent(a, f);
}

Function<String, String> country = memoize(Bins::issuerCountry);
```

```kotlin
fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {
    val cache = ConcurrentHashMap<A, R>()
    return { a -> cache.computeIfAbsent(a) { f(it) } }
}

val country = memoize(::issuerCountry)
```

Everything from the last lesson is in those four lines. `memoize` takes a function and returns one. The returned lambda is a closure over `cache`, so each memoized function gets its own map that nobody else can reach. It's safe on many threads because the captured state is a `ConcurrentHashMap` held in a `val`, not a `var`. `computeIfAbsent` runs `f` at most once per key, even when two threads ask for the same key at the same moment, as the concurrent collections lesson showed. The `A : Any, R : Any` bounds are there because `ConcurrentHashMap` can't store null.

Memoizing is only correct for pure functions. Referential transparency, from lesson 1, says a pure call can be replaced by its value, and a cache does exactly that replacement for you. Memoize something impure and you get stale answers. In the demo, a memoized FX rate keeps returning 1.08 after the market moves to 1.11, and it will keep doing so until the process restarts. Mapping a card BIN to its issuer country from a fixed table is a good fit. Today's exchange rate, an account balance or anything you read from a database is not.

Two practical limits. The cache never forgets, so only memoize over a small, known set of keys (countries, currencies, BIN prefixes), never over payment ids. When you need expiry or a size limit, use a real cache library such as Caffeine, which is the same idea plus eviction. And the function you pass to `computeIfAbsent` must not change the same map, so this `memoize` can't wrap a recursive function that calls its own memoized version."""

S5 = """Every lambda you pass to `retry` or `memoize` is an object (lesson 2), and a `var` it changes becomes a `Ref` box. So you might expect `payments.filter { ... }.map { ... }` to create two lambda objects on every call. It creates none, because `filter`, `map`, `forEach`, `fold`, `sumOf` and almost every other collection function on `Iterable` are declared **`inline`**.

When you call an inline function, the compiler doesn't emit a call. It copies the function's body into the call site, and the lambda's body with it. The lambda never exists as an object.

```java
// Java has no inline functions. The method reference is a lambda object
// (shared, since it captures nothing), and only the JIT may inline it at runtime.
long total = payments.stream().mapToLong(Payment::amountCents).sum();
```

```kotlin
inline fun <T> measuredInline(block: () -> T): T {
    val start = System.nanoTime()
    val result = block()
    lastNanos = System.nanoTime() - start
    return result
}

var total = 0L
measuredInline { amounts.forEach { total += it } }   // becomes a plain loop; total stays a local
```

The demo compiles two versions of the same code. With a non-inline `measured`, the bytecode has `new Ref$LongRef` for `total`, an `invokedynamic` for the lambda and a call through `Function0.invoke`. With `measuredInline` it has none of them: the `System.nanoTime()` calls, the iterator loop and an `ladd` on a local variable are pasted straight into `totalInlined`. That is also why `return` inside `repeat` worked in `retry`. After inlining, the lambda body is part of `retry`, so `return` leaves `retry`. This is called a **non-local return**, and it's only allowed when the lambda is inlined.

So mark your own small higher-order functions `inline` when they take a lambda and call it straight away, as `measuredInline` and `retry` do. Don't mark everything `inline`. The body is copied into every call site, so a big inline function bloats the code. And a lambda you keep for later, like the `f` that `memoize` stores in its closure, can't be inlined: the compiler needs a real object to keep. The Advanced Kotlin track, later in this part of the course, has a whole lesson on `inline`, `noinline`, `crossinline` and non-local returns."""

L = {
    "id": "fp-03",
    "title": "Higher-order functions: functions in, functions out",
    "minutes": 35,
    "goal": "By the end you can write your own higher-order functions (retry, timed, memoize), return functions to configure behaviour once, compose small functions into a pipeline, and say when inline makes a lambda free.",
    "warmup": {
        "q": "In Kotlin, `payments.filter { it.settled }.map { it.amountCents }` runs on a `List`. How many lambda objects does one call create?",
        "options": [
            "Two, one per lambda",
            "One, shared by both steps",
            "None: `filter` and `map` are inline, so the lambda bodies are copied into plain loops",
            "Two per element"
        ],
        "answer": 2,
        "why": "`filter` and `map` on `Iterable` are `inline` functions. The compiler pastes their loops, and the bodies of your lambdas, into the calling method, so no lambda object is ever created. The call still builds two new `ArrayList`s, one per step: that is the real cost of a chain, and the next lessons deal with it. Lesson 2's answer, one object per capturing lambda, applies to functions that are not inline."
    },
    "sections": [
        {
            "h": "Pass the part that changes in as a function",
            "body": S1,
            "try": {
                "title": "One retry loop for every flaky call",
                "minutes": 4,
                "steps": [
                    "Run `Retry` (or `RetryJava`). Predict first: how many calls reach the issuer in each half?",
                    "Wrap the second `retry` in `timed(\"gave up\") { ... }` as well. Predict whether its timing line prints, even though the block throws.",
                    "Change the first `retry(3)` to `retry(1)` and run again."
                ],
                "code": kdemo("Retry"),
                "expect": "The first half takes three calls: two timeouts, then `auth_pay_42`. The second gives up after three: `gave up after 3 attempts (last cause: issuer timeout on call 3)`. `timed` prints its line even when the block throws, because the print is in a `finally`. With `retry(1)`, the program stops with `IllegalStateException: gave up after 1 attempts`. `retry` never changed in any of these runs; only the function you handed it did."
            }
        },
        {
            "h": "Return a function: build the fee rule once",
            "body": S2,
            "try": {
                "title": "When does a bad country fail?",
                "minutes": 4,
                "steps": [
                    "Run `FeeFor` (or `FeeForJava`) and check one number: 140 basis points of 100,000 cents is 1,400.",
                    "Add `val broken = feeFor(\"XX\")` as the first line of `main`, without calling `broken`. Predict whether the program fails, and where.",
                    "Move the lookup into the returned lambda: `return { amountCents -> amountCents * RATES_BPS.getValue(country) / 10_000 }` (Java: `RATES_BPS.get(country)` inside the lambda). Run again. Now when does it fail?"
                ],
                "code": kdemo("FeeFor"),
                "expect": "With the lookup outside the lambda, `feeFor(\"XX\")` fails right away: Kotlin throws `NoSuchElementException: Key XX is missing in the map.`, and Java throws a `NullPointerException` when it unboxes the missing rate. With the lookup inside the lambda, `feeFor(\"XX\")` succeeds and returns a function that fails on its first call, which could be hours later in production. Same code, different moment of failure. You want the first one."
            }
        },
        {
            "h": "Compose small functions into a pipeline",
            "body": S3,
            "figure": {"svg": FIG, "caption": "Composition turns three small functions into one. The order is part of the function: capping first gives 922, capping last gives 1,000."},
            "try": {
                "title": "Compose, reorder, extend",
                "minutes": 4,
                "steps": [
                    "Run `Compose` (or `ComposeJava`). Predict both prices for 500 and for 1,200 before you look.",
                    "Delete the `andThen` extension at the top of `Compose.kt` and run again. Read the error, then put the line back.",
                    "Add a fourth step, `val roundToTen: (Long) -> Long = { it / 10 * 10 }`, at the end of `steps`, and print `fromList(900)`. Predict it first."
                ],
                "code": kdemo("Compose"),
                "expect": "500 gives 472 both ways, because the cap never bites. 1,200 gives 1,000 with the cap last and 922 with the cap first. Without the extension, Kotlin reports `unresolved reference 'andThen' on receiver of type '(Long) -> Long'.` The Java version has nothing to delete: `andThen` is a default method on `Function`. With `roundToTen`, `fromList(900)` goes 925, then 832, then 832 again (under the cap), then 830."
            },
            "refs": [
                {"title": "Function: andThen, compose, identity (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/function/Function.html", "kind": "docs"}
            ]
        },
        {
            "h": "memoize: a function that remembers its answers",
            "body": S4,
            "try": {
                "title": "A cache that helps, and one that lies",
                "minutes": 4,
                "steps": [
                    "Run `Memoize` (or `MemoizeJava`). Predict the number of lookups for the five BINs, and roughly how long they take (each real lookup sleeps 50 ms).",
                    "Replace `memoize(::issuerCountry)` with plain `::issuerCountry` and run again.",
                    "Explain the last line of the output to yourself before you read the expected result. Why is the memoized rate wrong?"
                ],
                "code": kdemo("Memoize"),
                "expect": "Memoized: 2 lookups for 5 calls, a little over 100 ms. Without `memoize`: 5 lookups, about 250 ms, and the same answers. The FX line prints 1.08 after the rate moved to 1.11. `fxRate` reads a mutable global, so it is impure, and the cache froze its first answer. A cache is only invisible when the function it wraps is pure."
            },
            "refs": [
                {"title": "ConcurrentHashMap.computeIfAbsent (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html", "kind": "docs"}
            ]
        },
        {
            "h": "inline: why map and filter cost no lambdas",
            "body": S5,
            "try": {
                "title": "Find the missing lambda in the bytecode",
                "minutes": 4,
                "steps": [
                    "Run `InlineCost`. Both totals print 13400. (Java has no `inline` functions, so this demo has no Java twin.)",
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
    "analogy": "A higher-order function is a standard procedure with a blank in it. \"Call the system; if it times out, try again, up to three times\" works for the issuer, the ledger and the FX service, and you fill in which call. Partial application is a pre-filled form: the country is already written in, so the clerk only adds the amount. Composition is an assembly line where each station does one small job and passes the part on, and moving a station changes the product. The analogy breaks at memoize: a paper procedure doesn't remember what happened last time, and that memory is exactly why memoize only suits answers that never change.",
    "in_your_world": "Your Quarkus services already wrap calls in retry and timing logic, mostly through annotations: MicroProfile Fault Tolerance's `@Retry` and `@Timeout`, Micrometer's `@Timed`. Those are higher-order functions in disguise: the framework takes your method and returns a wrapped one. A hand-written `retry(3) { issuer.authorize(p) }` fits where annotations can't reach, such as one call inside a Kafka consumer loop. Partial application fits per-merchant configuration: when a merchant's config loads, build its `(Long) -> Long` fee function once and keep it in a map. In Temporal, leave activity retries to the activity's `RetryOptions` rather than a loop of your own, so the server tracks attempts and backoff for you.",
    "mistake": "The most common mistake is memoizing a function that isn't pure. It's tempting to wrap an exchange-rate lookup, a merchant-config read or an account lookup in `memoize` to save a database call, and in a test it looks perfect. In production the cache keeps its first answer forever: the rate moves, the config changes, and the memoized function never notices. A quieter version is memoizing over keys that never repeat, such as payment ids, which turns the cache into a memory leak. Memoize only pure functions over a small, known set of keys. For data that changes, use a real cache with expiry (Caffeine, or your framework's cache) and decide how stale an answer you can accept.",
    "compare": {
        "title": "Functions in, functions out, functions combined",
        "java": {
            "title": "Fees.java",
            "src": "import java.util.Map;\nimport java.util.concurrent.ConcurrentHashMap;\nimport java.util.function.Function;\nimport java.util.function.Supplier;\n\nfinal class Fees {\n    // functions in\n    static <T> T retry(int times, Supplier<T> block) {\n        RuntimeException last = null;\n        for (int i = 0; i < times; i++) {\n            try { return block.get(); } catch (RuntimeException e) { last = e; }\n        }\n        throw new IllegalStateException(\"gave up after \" + times + \" attempts\", last);\n    }\n\n    // functions out: partial application\n    static Function<Long, Long> feeFor(long bps) {\n        return amountCents -> amountCents * bps / 10_000;\n    }\n\n    // composition is built into Function\n    static Function<Long, Long> price(long bps) {\n        return feeFor(bps).andThen(fee -> fee + 25).andThen(fee -> Math.min(fee, 1_000));\n    }\n\n    static <A, R> Function<A, R> memoize(Function<A, R> f) {\n        Map<A, R> cache = new ConcurrentHashMap<>();\n        return a -> cache.computeIfAbsent(a, f);\n    }\n}"
        },
        "kotlin": {
            "title": "Fees.kt",
            "src": "import java.util.concurrent.ConcurrentHashMap\n\n// functions in; inline, so the lambda is pasted into the caller\ninline fun <T> retry(times: Int, block: () -> T): T {\n    var last: Exception? = null\n    repeat(times) {\n        try { return block() } catch (e: Exception) { last = e }\n    }\n    throw IllegalStateException(\"gave up after $times attempts\", last)\n}\n\n// functions out: partial application\nfun feeFor(bps: Long): (Long) -> Long = { amountCents -> amountCents * bps / 10_000 }\n\n// composition is not in the stdlib: one line of your own\ninfix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }\n\nfun price(bps: Long): (Long) -> Long =\n    feeFor(bps) andThen { fee -> fee + 25 } andThen { fee -> minOf(fee, 1_000) }\n\nfun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {\n    val cache = ConcurrentHashMap<A, R>()\n    return { a -> cache.computeIfAbsent(a) { f(it) } }\n}"
        },
        "note": "Both languages make the same three moves: functions in, functions out, functions combined. The differences are in the plumbing. Java's `Function` comes with `andThen` and `compose`, and Kotlin's function types don't, so you write the extension yourself or use Arrow's `arrow-functions` module. Java needs a different interface per shape (`Supplier`, `Function`, `Callable` once checked exceptions appear), while Kotlin uses `() -> T` and `(A) -> R` everywhere. And Kotlin can declare a higher-order function `inline`, so the lambda passed to `retry` is pasted into the caller and never allocated. Java leaves that to the JIT, which may or may not inline at runtime."
    },
    "worked": {
        "title": "Turn a merchant's fee configuration into one function",
        "steps": [
            {
                "say": "A merchant's fee configuration is a list of rows loaded at startup: a kind of adjustment and a number. We want one `(Long) -> Long` per merchant, built once, called for every payment.",
                "code": "data class AdjustmentRow(val kind: String, val value: Long)\n\nval acmeRows = listOf(\n    AdjustmentRow(\"discount\", 10),     // 10 % off\n    AdjustmentRow(\"floor\", 50),        // at least 50 cents\n    AdjustmentRow(\"cap\", 1_000),       // at most 10 euros\n)",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "record AdjustmentRow(String kind, long value) {}\n\nList<AdjustmentRow> acmeRows = List.of(\n        new AdjustmentRow(\"discount\", 10),   // 10 % off\n        new AdjustmentRow(\"floor\", 50),      // at least 50 cents\n        new AdjustmentRow(\"cap\", 1_000));    // at most 10 euros"
            },
            {
                "say": "1. Turn each row into a function with a `when` expression. Each branch returns a function, and nothing is computed yet. An unknown kind is a configuration bug, so it throws here.",
                "code": "fun toAdjust(row: AdjustmentRow): (Long) -> Long = when (row.kind) {\n    \"flat\" -> { fee -> fee + row.value }\n    \"discount\" -> { fee -> fee * (100 - row.value) / 100 }\n    \"floor\" -> { fee -> maxOf(fee, row.value) }\n    \"cap\" -> { fee -> minOf(fee, row.value) }\n    else -> throw IllegalArgumentException(\"unknown adjustment ${row.kind}\")\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static Function<Long, Long> toAdjust(AdjustmentRow row) {\n    return switch (row.kind()) {\n        case \"flat\" -> fee -> fee + row.value();\n        case \"discount\" -> fee -> fee * (100 - row.value()) / 100;\n        case \"floor\" -> fee -> Math.max(fee, row.value());\n        case \"cap\" -> fee -> Math.min(fee, row.value());\n        default -> throw new IllegalArgumentException(\"unknown adjustment \" + row.kind());\n    };\n}"
            },
            {
                "say": "2. Fold the adjustments onto the country's base fee. Self-check: when does a row with an unknown kind fail, at startup or on the first payment? (At startup: `toAdjust` runs inside `map`, while the function is being built.)",
                "code": "fun merchantFee(country: String, rows: List<AdjustmentRow>): (Long) -> Long =\n    rows.map(::toAdjust)                                   // 1. rows to functions\n        .fold(feeFor(country)) { acc, f -> acc andThen f } // 2. one function, base fee first",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static Function<Long, Long> merchantFee(String country, List<AdjustmentRow> rows) {\n    return rows.stream()\n            .map(Fees::toAdjust)                               // 1. rows to functions\n            .reduce(feeFor(country), Function::andThen);       // 2. one function, base fee first\n}"
            },
            {
                "say": "3. Build once per merchant, call per payment. Each payment now costs four small calls and no lookups, and every adjustment can be tested on its own with plain numbers.",
                "code": "val acmeFee = merchantFee(\"NL\", acmeRows)\n\nacmeFee(100_000)    // 1,400 -> 1,260 -> 1,260 -> 1,000\nacmeFee(2_000)      // 28 -> 25 -> 50 -> 50",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "Function<Long, Long> acmeFee = merchantFee(\"NL\", acmeRows);\n\nacmeFee.apply(100_000L);   // 1,400 -> 1,260 -> 1,260 -> 1,000\nacmeFee.apply(2_000L);     // 28 -> 25 -> 50 -> 50"
            }
        ]
    },
    "lab": {
        "title": "Compose a fee pipeline, and memoize a slow lookup",
        "minutes": 13,
        "files": [
            "labs/functional/src/main/kotlin/workbench/functional/l03/Pipeline.kt",
            "labs/functional/src/main/kotlin/workbench/functional/l03/Memo.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l03.*'",
        "steps": [
            "Run the tests. All ten fail with `NotImplementedError`. Read the four finished building blocks at the top of `Pipeline.kt`: each one is a function that returns a function.",
            "Write `andThen` and `compose`. Each body is one lambda.",
            "Write `pipeline` with `fold`, starting from `{ x: T -> x }`. An empty list must give back that identity function.",
            "Write `feeFor`. Do the rate lookup outside the lambda you return, and throw `IllegalArgumentException(\"no rate for $country\")` for an unknown country.",
            "Write `merchantFee` from `feeFor`, `andThen` and `pipeline`. Then write `curried`.",
            "Write `memoize` in `Memo.kt`. Run the tests until all ten pass."
        ],
        "hints": [
            "`andThen` is `{ a -> next(this(a)) }`. Inside an extension on a function type, `this` is the function, and `this(a)` calls it.",
            "`requireNotNull(BASIS_POINTS[country]) { \"no rate for $country\" }` returns the rate, or throws `IllegalArgumentException` with that message.",
            "`ConcurrentHashMap.computeIfAbsent(key) { f(it) }` calls `f` only when the key is missing. A `HashMap` with `getOrPut` also passes these tests, but it isn't safe once several threads share the memoized function."
        ],
        "done_when": "All ten tests in `HigherOrderTest` pass."
    },
    "drill": {
        "title": "Write retry and andThen from memory",
        "minutes": 5,
        "prompt": "Close this page. Write an `inline` function `retry(times, block)` that calls `block` until it returns, at most `times` times, and then throws `IllegalStateException` with the last failure as its cause. Write `andThen` for function types. Use both: retry a call that returns a fee in cents, then run the fee through `{ it + 25 } andThen { minOf(it, 1_000) }`. Then write the Java version of both functions.",
        "answer": {
            "lang": "kotlin",
            "src": "inline fun <T> retry(times: Int, block: () -> T): T {\n    var last: Exception? = null\n    repeat(times) {\n        try { return block() } catch (e: Exception) { last = e }   // non-local return: repeat is inline\n    }\n    throw IllegalStateException(\"gave up after $times attempts\", last)\n}\n\ninfix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }\n\nval adjust: (Long) -> Long = { fee: Long -> fee + 25 } andThen { fee -> minOf(fee, 1_000) }\nval fee = adjust(retry(3) { pricing.baseFee(payment) })",
            "alt": {
                "lang": "java",
                "src": "static <T> T retry(int times, Supplier<T> block) {\n    RuntimeException last = null;\n    for (int i = 0; i < times; i++) {\n        try { return block.get(); } catch (RuntimeException e) { last = e; }\n    }\n    throw new IllegalStateException(\"gave up after \" + times + \" attempts\", last);\n}\n\n// andThen is already a default method on java.util.function.Function\nFunction<Long, Long> addScheme = fee -> fee + 25;\nFunction<Long, Long> adjust = addScheme.andThen(fee -> Math.min(fee, 1_000));\nlong fee = adjust.apply(retry(3, () -> pricing.baseFee(payment)));"
            }
        }
    },
    "recap": [
        "A higher-order function takes a function, returns one, or both. It keeps the shape of a computation (retry, time, cache) apart from the work inside it.",
        "Trailing lambdas make higher-order calls read like built-ins: `retry(3) { issuer.authorize(p) }`.",
        "Returning a function gives you partial application: `feeFor(country)` looks up the rate once and returns a `(Long) -> Long`. Prefer that, or a plain lambda, to curried signatures.",
        "Kotlin's stdlib has no `andThen` or `compose` for function types; write the one-line infix extension (Java's `Function` has both). Order matters, and a list of steps folds into one function.",
        "Memoize only pure functions, over a small set of keys. A memoized impure function returns stale answers until restart.",
        "`inline` pastes a function and its lambda into the call site: no lambda object, no `Ref` box, and `return` leaves the enclosing function. That's why `map` and `filter` on lists create no lambdas."
    ],
    "quiz": [
        {
            "q": "`val a = capAt(1_000) andThen addFlat(25)` and `val b = addFlat(25) andThen capAt(1_000)`. What are `a(990)` and `b(990)`?",
            "options": [
                "1015 and 1000",
                "1000 and 1015",
                "1015 and 1015",
                "1000 and 1000"
            ],
            "answer": 0,
            "why": "`andThen` runs the left function first. `a` caps 990 (no change) and then adds 25, giving 1015. `b` adds 25 (1015) and then caps at 1000. Composition is not commutative: the order of the steps is part of the function."
        },
        {
            "q": "`fun feeFor(country: String): (Long) -> Long { val bps = rates.getValue(country); return { it * bps / 10_000 } }`. A config typo passes `\"NLD\"`. When does it fail?",
            "options": [
                "On the first payment that uses the fee function",
                "When `feeFor(\"NLD\")` is called, before any fee is computed",
                "Never: the fee comes out as 0",
                "At compile time"
            ],
            "answer": 1,
            "why": "The lookup sits outside the returned lambda, so it runs when the function is built, and `getValue` throws `NoSuchElementException: Key NLD is missing in the map.` Building fee functions at startup turns config typos into startup failures. If the lookup were inside the lambda, the first payment would fail instead."
        },
        {
            "q": "Which of these functions is safe to memoize?",
            "options": [
                "`fun balance(accountId: String): Long`, which reads the ledger",
                "`fun fxRate(pair: String): BigDecimal`, which calls a rates API",
                "`fun schemeFor(bin: String): CardScheme`, which maps a BIN prefix to Visa or Mastercard from a fixed table",
                "`fun nextInvoiceNumber(merchant: String): Long`"
            ],
            "answer": 2,
            "why": "Only `schemeFor` is pure: the same BIN always gives the same scheme, so a cached answer is always right. The balance and the FX rate change over time, so a memoized version would freeze them. `nextInvoiceNumber` is supposed to return a new value on every call, so memoizing it would hand out the same number forever."
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
            "q": "From the concurrent collections lesson: two threads call a memoized function with the same new key at the same moment. The cache is a `ConcurrentHashMap` and uses `computeIfAbsent(key) { f(it) }`. How many times does `f` run for that key?",
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
        {"front": "What is partial application?", "back": "Fixing some of a function's arguments now and getting back a function of the rest. `feeFor(\"NL\")` returns a `(Long) -> Long`."},
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
        {"term": "Memoization", "plain": "Remembering a pure function's results so each one is computed only once."},
        {"term": "Inline function", "plain": "A function whose body, and the bodies of the lambdas passed to it, the compiler copies into each call site."}
    ],
    "explain_back": {
        "prompt": "A teammate asks why `payments.filter { it.settled }.map { it.amountCents }` creates no lambda objects, while their own `fun <T> timed(block: () -> T): T` does. Explain it in your own words, and say what you'd change in `timed`.",
        "answer": "A lambda is normally an object: a function value that something has to create, and if it changes a captured `var`, that `var` moves into a `Ref` box. `filter` and `map` on lists are declared `inline`, so the compiler never calls them. It copies their loops into my method and pastes my lambda bodies into those loops, and no lambda object ever exists. `timed` isn't inline, so its `block` has to be a real object passed to a real call. Since `timed` only calls `block` once, right away, I'd mark it `inline`. Then the timing code and the block are pasted into each caller, with no allocation and no `Ref` box. I wouldn't do that for a function that stores its lambda, like `memoize`, because a stored lambda has to be an object."
    },
    "deeper": {
        "minutes": 10,
        "body": "Kotlin gives you partial application in a few forms besides returning a lambda. A bound reference fixes the receiver, which is often all you need:\n\n```kotlin\nclass Merchant(private val bps: Long) {\n    fun fee(amountCents: Long): Long = amountCents * bps / 10_000\n}\n\nval acme = Merchant(bps = 140)\nval acmeFee: (Long) -> Long = acme::fee          // a bound reference: the receiver is fixed\nlistOf(10_000L, 50_000L).map(acmeFee)            // [140, 700]\n```\n\n```java\nfinal class Merchant {\n    private final long bps;\n    Merchant(long bps) { this.bps = bps; }\n    long fee(long amountCents) { return amountCents * bps / 10_000; }\n}\n\nMerchant acme = new Merchant(140);\nFunction<Long, Long> acmeFee = acme::fee;          // a bound method reference\nList.of(10_000L, 50_000L).stream().map(acmeFee).toList();   // [140, 700]\n```\n\nThis is the strategy pattern with the ceremony removed: an object with one behaviour, passed around as a function. Remember lesson 2's detail, though: in Kotlin 2.4.21 a bound reference compiles to a small class and allocates one object each time the expression runs.\n\nArrow 2.3.0 puts its function utilities in the `io.arrow-kt:arrow-functions` artifact, separate from `arrow-core`. Its jar contains `andThen` and `compose`, `curried` and `uncurried` with overloads up to 22 parameters, `partially1` and its siblings, and `memoize`. If your codebase already uses Arrow, use those rather than your own. If it doesn't, the one-line versions in this lesson are not a reason to add a dependency.\n\nOne more look at `inline` and `return`. Inside an inline higher-order function's lambda, a bare `return` leaves the enclosing function, and `return@forEach` (or any label) leaves only the lambda, acting like `continue`. Java developers moving to Kotlin trip on this in `forEach`, because a `return` in a Java `Stream.forEach` lambda only ends that one call. The Advanced Kotlin track's inline lesson goes through `noinline` and `crossinline`, the two modifiers that control which lambdas get pasted and where `return` may go."
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
