import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l07.demo"


def kdemo(name):
    path = f"{LAB}/demo/kotlin/workbench/functional/l07/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path,
            "alt": jdemo(name + "Java")}


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l07/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 640 260" role="img" aria-label="A kitchen line drawn as two tracks. A batter moves along the success track through three steps: check, mix, bake. '
    'From each step a branch drops to the failure track with a note. Once on the failure track, the note travels to the end and no later step runs.">'
    '<text class="t-s t-ok" x="20" y="84">success</text><text class="t-s t-bad" x="20" y="194">failure</text>'
    '<line class="ln-a" x1="80" y1="80" x2="600" y2="80" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="80" y1="190" x2="600" y2="190" marker-end="url(#arr)"/>'
    '<rect class="box" x="115" y="60" width="110" height="40" rx="8"/><text class="t t-code" x="170" y="85" text-anchor="middle">check</text>'
    '<rect class="box" x="275" y="60" width="110" height="40" rx="8"/><text class="t t-code" x="330" y="85" text-anchor="middle">mix</text>'
    '<rect class="box" x="435" y="60" width="110" height="40" rx="8"/><text class="t t-code" x="490" y="85" text-anchor="middle">bake</text>'
    '<line class="ln-bad" x1="200" y1="100" x2="250" y2="186" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="360" y1="100" x2="410" y2="186" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="520" y1="100" x2="570" y2="186" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="250" y="146" text-anchor="middle">Invalid</text>'
    '<text class="t-s t-bad" x="412" y="146" text-anchor="middle">BowlTooSmall</text>'
    '<text class="t-s t-bad" x="574" y="146" text-anchor="middle">Burnt</text>'
    '<text class="t-s t-ok" x="560" y="56" text-anchor="middle">Ok(loaf)</text>'
    '<text class="t-s t-bad" x="520" y="214" text-anchor="middle">Err(the first note)</text>'
    '<text class="t-s t-m" x="320" y="248" text-anchor="middle">andThen runs a step only on the success track; map changes the value there</text>'
    '</svg>'
)

OPENING = """Picture a recipe step that goes wrong. The custard splits. A calm cook hands back a note: "the custard split, let's serve the cake with cream instead", and dinner goes on. An upset cook throws the pan across the room, and someone further away has to catch it, or the whole dinner stops.

Code does both. An exception is the thrown pan: an object a function throws to say something failed, which flies up through every caller until some code catches it. A returned value is the note: the caller holds it and must read it. The easy trap is to throw the pan for failures that happen every week, like a jar that's out of flour, because nothing in a Kotlin signature says what might fly out.

The last lesson used null for "nothing here". Null can't say why.

In this lesson, we'll put expected failures into the return type with a sealed result, write a small result type of our own, see what `kotlin.Result` is for and what it swallows, and use Arrow's `Either` to stop at the first error or collect every one. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_THROWS = """int takeFlour(int grams) throws NotEnoughFlourException, PastBestBeforeException;"""
K_THROWS = """fun takeFlour(grams: Int): Int   // throws NotEnoughFlourException, PastBestBeforeException"""
J_SEALED = """sealed interface TakeResult {}
record Taken(int leftGrams) implements TakeResult {}
record Refused(JarFailure reason) implements TakeResult {}
TakeResult takeFlour(int grams, int leftGrams, LocalDate bestBefore, LocalDate today);"""
K_SEALED = """sealed interface TakeResult {
    data class Taken(val leftGrams: Int) : TakeResult
    data class Refused(val reason: JarFailure) : TakeResult
}
fun takeFlour(grams: Int, leftGrams: Int, bestBefore: LocalDate, today: LocalDate): TakeResult"""

S0 = """Here's the recipe app's helper that takes flour from the jar, in both languages:

""" + pair(J_THROWS, K_THROWS) + """

Java has **checked exceptions**: exceptions a method must list in its signature, so the compiler makes every caller deal with them. Kotlin has none. In the words of its docs, "Kotlin treats all exceptions as unchecked by default." So the Kotlin signature says only `Int`, and nothing tells the caller that the jar runs short every few weeks. A new screen forgets the `try`. The exception flies up past every caller, and the cook sees "Something went wrong" because the flour ran out.

The real problem is that two kinds of failure share one mechanism. An empty jar, an old bag or an amount of -5 is **expected**: it happens in normal use, and the caller must decide what to do. A null pointer, a broken rule inside our own code or a full disk is a bug or a broken machine, and no caller can do anything useful about it on the spot. The Kotlin team draws the same line. The design notes for `kotlin.Result` say: "Use nullable types or domain-specific classes to represent failures that need specific handling." The newer rich-errors proposal, KEEP-0441, says exceptions "should be used for unrecoverable cases."

So put the expected failures in the return type, as values:

""" + pair(J_SEALED, K_SEALED) + """

The jar's contents and today's date are parameters now, as the first lesson of this track taught: a pure function takes its inputs as arguments. And `sealed` means the compiler knows every subtype, so a `when` over them needs no `else`.

That pays off when someone adds a case. Add `JarMissing` to `JarFailure`, and every `when` that doesn't handle it stops compiling: `'when' expression must be exhaustive. Add the 'JarMissing' branch or an 'else' branch.` Java 21's sealed interfaces and pattern `switch` give the same check: `the switch expression does not cover all possible input values`. That error is the whole point.

**A sealed result lists every expected failure, and the compiler checks each `when`. Never add `else` to a `when` over a sealed type.**

Exceptions keep their job for bugs. `require`, `check` and `error()` still belong wherever one of your own rules breaks.

A sealed type for one step works well. Chain three of them, and every step needs a `when` to look at the step before."""

# ---------------------------------------------------------------- section 1
J_OUT = """sealed interface Outcome<E, A> {
    default <B> Outcome<E, B> andThen(Function<? super A, Outcome<E, B>> f) {
        return switch (this) {
            case Ok<E, A> ok -> f.apply(ok.value());
            case Err<E, A> err -> new Err<>(err.error());
        };
    }
}
record Ok<E, A>(A value) implements Outcome<E, A> {}
record Err<E, A>(E error) implements Outcome<E, A> {}"""
K_OUT = """sealed interface Outcome<out E, out A> {
    data class Ok<A>(val value: A) : Outcome<Nothing, A>
    data class Err<E>(val error: E) : Outcome<E, Nothing>
}

inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }"""

S1 = """One generic type can cover every step. It holds either a success with a value or a failure with an error:

""" + pair(J_OUT, K_OUT) + """

`andThen` runs the next step only if this one succeeded. An `Err` skips every later step and comes out at the end unchanged. Its sibling `map`, in the Try it, does the same for a plain function that can't fail, such as `uppercase()`. Making a loaf becomes one line: `checkBatter(b).andThen(::mix).andThen(::bake).map { it.uppercase() }`.

Picture the kitchen line from the sequences lesson, with a side door. A good batter walks down the line, step by step. When a step fails, the batter leaves through the side door with a note pinned to it, and the note walks straight to the end of the line, past every step still waiting. Programmers draw the same idea as a railway with two tracks, success on top and failure below, which is why the style is called **railway-oriented programming**. The figure shows it.

Look at the variance. `Outcome<out E, out A>` is covariant in both parameters: an `Outcome` of a subtype counts as an `Outcome` of its supertype ("Covariance with out: producers" in the generics track). And `Err` is an `Outcome<E, Nothing>`. `Nothing` is the type with no values at all, and it's a subtype of every type. So an `Err<BakeErr>` already *is* an `Outcome<BakeErr, String>`, an `Outcome<BakeErr, Loaf>`, an `Outcome<BakeErr, X>` for any `X`. That's why `is Outcome.Err -> this` compiles without building a new object. Java has no declaration-site variance (variance written once, on the type itself) and no `Nothing`, so the Java version builds a new `Err` at every step.

The kitchen picture breaks at one point. A cook who gets a note can still decide to carry on with a second-best dish; this line never does. Once a value is an `Err`, nothing after it runs, unless you write a step that looks for errors on purpose. Arrow, later in this lesson, calls that step `recover`.

That's all an **Either** is at heart: a value that holds one of two things, an error or a result. Libraries add more helpers, and a block syntax that makes chains read like straight-line code. Before we get there, the standard library ships one result type of its own, and it was built for a different job."""

# ---------------------------------------------------------------- section 2
J_IMPORT = """Recipe recipe;
try { recipe = importer.parse(file); }      // a Java library that throws
catch (Exception e) { recipe = Recipe.EMPTY; }"""
K_IMPORT = """val recipe = runCatching { importer.parse(file) }   // a Java library that throws
    .getOrElse { Recipe.EMPTY }"""
J_RETHROW = """// Java equivalent: never swallow the interrupt that carries a stop request
try { return shop.ask(item); }
catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new CancellationException(); }"""
K_RETHROW = """runCatching { shop.ask(item) }                               // a suspend call that waits for the shop
    .onFailure { if (it is CancellationException) throw it }   // a cancel keeps travelling"""

S2 = """The standard library has one result type, `kotlin.Result<T>`, and `runCatching { }` makes one: it runs the block and catches whatever the block throws. `Result` isn't an `Either`. It has a single type parameter, and the failure is always a `Throwable`, the parent class of every exception and error on the JVM. Its design notes are blunt: "The `Result` class is not designed to represent domain-specific error conditions." It was built mainly for the coroutine machinery: `Continuation.resumeWith` takes a `Result`.

Use it at the edge, around code that throws when you'd rather have a value. Here the app reads a recipe file that a user imported, and falls back to an empty recipe when the file is broken:

""" + pair(J_IMPORT, K_IMPORT) + """

Two traps come with it. The first is that `runCatching` catches every `Throwable`. It catches everything you throw at it, including the message that tells it to stop. That covers `OutOfMemoryError` and `StackOverflowError`, and inside a coroutine it covers `CancellationException`, the exception that carries a cancel.

A **coroutine** is a light task that can pause while it waits, without holding on to a thread, and you cancel one to say "stop, nobody wants the answer any more" ("Cancellation and timeouts" in the coroutines track). The Try it cancels a coroutine while it waits for the shop inside `runCatching`. The cancel turns into a failed `Result`. The coroutine runs on until its next suspension point, the next place where it could pause, and the line that places the order runs. An issue asking kotlinx.coroutines for a `runCatching` that rethrows `CancellationException` (#1814) has been open since February 2020. Until something ships, rethrow it yourself, as the lab asks:

""" + pair(J_RETHROW, K_RETHROW) + """

The second trap is that `map` doesn't catch. `runCatching { "12".toInt() }.map { error("boom") }` throws `IllegalStateException: boom` straight out of `map`. Only `mapCatching` turns it into `Failure(java.lang.IllegalStateException: boom)`. The library pairs `recover` and `recoverCatching` the same way. If a chain should be safe from end to end, every step that can throw needs the `Catching` variant.

So `Result` answers one question: did this throwing call work? It can't say which kitchen failure happened. `fun order(item: Ingredient): Result<Delivery>` tells the caller less than the sealed type from the first section.

**Keep runCatching at the edge, around code that throws. Let CancellationException through.**

For our own failures we want the railway back, with a nicer shape. That's Arrow's `Either`, and it brings a second mode the railway never had."""

# ---------------------------------------------------------------- section 3
J_ORDER = """// Java equivalent: the hand-written Outcome from earlier, chained with andThen
Outcome<KitchenError, Delivery> order(Ingredient ingredient, Shop shop) {
    return shop.reserve(ingredient).andThen(basketId -> {
        int minutes = shop.deliveryMinutes(basketId);
        if (minutes >= LATEST_MINUTES) return new Err<>(new TooLate(minutes));
        return shop.book(basketId).map(slotId -> new Delivery(basketId, slotId));
    });
}"""
K_ORDER = """fun order(ingredient: Ingredient, shop: Shop): Either<KitchenError, Delivery> = either {
    val basketId = shop.reserve(ingredient).bind()          // a Left ends the block here
    val minutes = shop.deliveryMinutes(basketId)
    ensure(minutes < LATEST_MINUTES) { KitchenError.TooLate(minutes) }
    val slotId = shop.book(basketId).bind()
    Delivery(basketId, slotId)
}"""
J_ACC = """// Java equivalent: run every check and collect the errors by hand
Validated<Amount> accumulate(int a, String u) {
    List<FormError> errors = new ArrayList<>();
    if (a <= 0) errors.add(new InvalidAmount(a));
    if (!UNITS.contains(u)) errors.add(new UnsupportedUnit(u));
    return errors.isEmpty() ? new Valid<>(new Amount(a, u)) : new Invalid<>(List.copyOf(errors));
}"""
K_ACC = """fun accumulate(a: Int, u: String): Either<NonEmptyList<FormError>, Amount> = either {
    zipOrAccumulate({ validAmount(a) }, { validUnit(u) }) { amount, unit -> Amount(amount, unit) }
}
// accumulate(-5, "oz") is Either.Left([InvalidAmount(amount=-5), UnsupportedUnit(unit=oz)])"""

S3 = """Arrow is a functional programming library for Kotlin, and the lab uses `arrow-core` 2.3.0. Its `Either<E, A>` is the `Outcome` from earlier, `Left(error)` or `Right(value)`, plus an `either { }` block that replaces chains of `andThen`. Here's the lab's grocery order: reserve the ingredient at the shop, check that the delivery arrives in time, then book it:

""" + pair(J_ORDER, K_ORDER) + """

Inside `either { }`, `.bind()` unwraps a `Right`. On a `Left` it stops the block, and that `Left` becomes the result. `ensure(condition) { error }` stops the block when the condition is false. The code reads top to bottom like the happy path, and it is **fail-fast**: the first failure wins, and nothing after it runs.

Fail-fast is right for a line of steps where each needs the one before. It's wrong for a form. A cook who types an amount of -5 with the unit `oz` (the scale was left on ounces again) should hear about both at once, not one per try. `zipOrAccumulate` runs independent checks, collects every failure into a `NonEmptyList`, a list that always holds at least one item, and calls its last lambda only if all of them passed:

""" + pair(J_ACC, K_ACC) + """

`validAmount` and `validUnit` are functions with a `Raise<FormError>` receiver, so the `ensure` inside them can stop whichever block called them. The same input through a plain `either { Amount(validAmount(-5), validUnit("oz")) }` gives only `Either.Left(InvalidAmount(amount=-5))`.

**Stop at the first error when each step needs the one before. Collect every error when the checks don't depend on each other.**

For code that throws, `Either.catch { }` is the safer cousin of `runCatching`. It turns an ordinary exception into a `Left`, but it rethrows `CancellationException` and fatal errors such as `OutOfMemoryError`.

You may have read that Kotlin is getting error unions, `fun load(): Recipe | NotFound`. That's a real proposal (KEEP-0441, with the detailed design in KEEP-0462), but it isn't in Kotlin 2.4.21: the compiler rejects `error class NotFound` with `Syntax error: Expecting a top level declaration.` Today the picker is short. Use a nullable type when absence needs no reason. Use a sealed type for a few outcomes of one function. Use `Either` when many steps chain or errors must be collected. Keep `Result` for code that throws, and exceptions for bugs."""

L = {
    "id": "fp-07",
    "title": "Errors as values: sealed results, Result and Either",
    "minutes": 38,
    "goal": "By the end you can choose between an exception, a sealed result, `kotlin.Result` and Arrow's `Either` for a failure, and write both a fail-fast pipeline of steps and a check that reports every error at once.",
    "opening": OPENING,
    "warmup": {
        "q": "`fun takeFlour(grams: Int): Int` throws `NotEnoughFlourException` when the jar runs short. A new screen in the recipe app calls it and catches nothing. What happens on a day the jar is short?",
        "options": [
            "The build fails until the caller handles the exception",
            "The exception flies up through every caller until something catches it, often a general handler that shows \"Something went wrong\"",
            "`takeFlour` returns null",
            "Kotlin wraps the exception in a `Result` for the caller"
        ],
        "answer": 1,
        "why": "Kotlin has no checked exceptions, so nothing in the signature or the build tells the caller that a short jar is possible. The exception travels up until something catches it, usually a general handler that shows an error screen. In Java, a checked `throws NotEnoughFlourException` would have forced a `catch`. This lesson puts that information back, in the return type."
    },
    "sections": [
        {
            "h": "Exceptions hide the failures your caller has to handle",
            "body": S0,
            "try": {
                "title": "Add a failure and let the compiler find the gaps",
                "minutes": 4,
                "steps": [
                    "Run `Exhaustive.kt`. Four attempts to take flour come out as four lines of advice.",
                    "Uncomment `JarMissing` in `JarFailure` and run it again. Read the error and note which `when` it points at.",
                    "Add a branch for it to `advice` (\"look in the other cupboard\" will do) and run again.",
                    "Do the same in `ExhaustiveJava.java`."
                ],
                "code": kdemo("Exhaustive"),
                "expect": "The first run prints `ok: 500 g left`, `check the amount: InvalidAmount(grams=-5)`, `open a new bag: PastBestBefore` and `buy more flour: NotEnough(shortByGrams=300)`. With the new case, Kotlin stops at `advice` with `'when' expression must be exhaustive. Add the 'JarMissing' branch or an 'else' branch.` The `when` in `main` still compiles, because it only looks at `TakeResult`. javac reports `the switch expression does not cover all possible input values` at the same spot. After you add the branch, both run again."
            },
            "refs": [{"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}]
        },
        {
            "h": "A result type you can write in ten lines",
            "body": S1,
            "figure": {"svg": FIG, "caption": "Each step either keeps the batter on the success track or switches it to the failure track, where its note rides to the end untouched."},
            "try": {
                "title": "Walk a batter down the line",
                "minutes": 3,
                "steps": [
                    "Read `Outcome.kt`. Each step prints its name when it runs. For each of the three batters, predict which names print and what comes out.",
                    "Run it, then run `OutcomeJava.java`.",
                    "In `Outcome.kt`, change `is Outcome.Err -> this` in `map` to `is Outcome.Err -> Outcome.Err(error)`. Does it still compile? Why was `this` allowed?"
                ],
                "code": kdemo("Outcome"),
                "expect": "`Batter(flourGrams=500)` runs all three steps and gives `Ok(value=LOAF FROM DOUGH)`. `Batter(flourGrams=-1)` prints only `check` and gives `Err(error=Invalid(why=flour<=0))`. `Batter(flourGrams=5000)` prints `check` and `mix` and gives `Err(error=BowlTooSmall)`: `bake` never runs. Java prints the same steps. Both versions of the `Err` branch compile; `this` works because an `Outcome<E, Nothing>` is already an `Outcome<E, B>` for every `B`, so there's no need to build a new object."
            }
        },
        {
            "h": "kotlin.Result wraps code that throws, and swallows cancellation",
            "body": S2,
            "try": {
                "title": "Cancel an order inside runCatching",
                "minutes": 4,
                "steps": [
                    "Read part 1 of `RunCatchingTrap.kt`. The coroutine is cancelled after 50 ms, while it waits for the shop inside `runCatching`. Predict: does `placing the order anyway` print, and what's in `orders`?",
                    "Run it and compare part 1 with part 2.",
                    "Read part 3 and predict which line throws.",
                    "Run `RunCatchingTrapJava.java`, which makes the same mistake with a thread and `catch (Exception e)`."
                ],
                "code": kdemo("RunCatchingTrap"),
                "expect": "Part 1 prints `runCatching returned: isFailure=true ex=JobCancellationException`, `isActive after swallow = false`, then `placing the order anyway`, and only the next `delay` throws. `orders` holds `placed the order`: work ran after the cancel. Part 2 rethrows, so the job ends `cancelled=true` with no orders. In part 3, `mapCatching` returns `Failure(java.lang.IllegalStateException: boom)` and `map` throws. Java's thread catches `InterruptedException`, carries on and places the order; restoring the interrupt flag and returning fixes it."
            },
            "refs": [{"title": "runCatching (Kotlin API reference)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html", "kind": "docs"}]
        },
        {
            "h": "Arrow's Either: stop at the first error, or collect every one",
            "body": S3,
            "try": {
                "title": "Fail fast, then collect everything",
                "minutes": 4,
                "steps": [
                    "Read `EitherDemo.kt`. Predict what `failFast(-5, \"oz\")` and `accumulate(-5, \"oz\")` print.",
                    "Run it.",
                    "Change `accumulate(-5, \"oz\")` to `accumulate(250, \"oz\")`. Predict the result, then run it.",
                    "Run `EitherDemoJava.java` and compare how much code the Java version needs per rule."
                ],
                "code": kdemo("EitherDemo"),
                "expect": "`fail fast:  Either.Left(InvalidAmount(amount=-5))`: the unit check never ran. `accumulate: Either.Left([InvalidAmount(amount=-5), UnsupportedUnit(unit=oz)])`. With a good amount, only `Either.Left([UnsupportedUnit(unit=oz)])` remains: still a list, now with one item. `Either.catch` turns `\"2OO\".toInt()`, typed with two letter Os, into `Either.Left(NumberFormatException)` and lets the `CancellationException` through. Java prints the same results with a hand-built list."
            },
            "refs": [{"title": "Working with typed errors, Arrow docs source", "url": "https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/working-with-typed-errors.md", "kind": "read"}]
        }
    ],
    "compare": {
        "title": "A fail-fast grocery order: Java sealed result vs Kotlin either { }",
        "java": {"title": "Order.java", "src": "sealed interface Outcome<E, A> { /* map and andThen as in section 2 */ }\nrecord Ok<E, A>(A value) implements Outcome<E, A> {}\nrecord Err<E, A>(E error) implements Outcome<E, A> {}\n\nOutcome<KitchenError, Delivery> order(Ingredient ingredient, Shop shop) {\n    return shop.reserve(ingredient).andThen(basketId -> {         // 1. reserve\n        int minutes = shop.deliveryMinutes(basketId);             // 2. check the time\n        if (minutes >= LATEST_MINUTES) return new Err<>(new TooLate(minutes));\n        return shop.book(basketId)                                // 3. book\n                .map(slotId -> new Delivery(basketId, slotId));\n    });\n}"},
        "kotlin": {"title": "Order.kt", "src": "fun order(ingredient: Ingredient, shop: Shop): Either<KitchenError, Delivery> = either {\n    val basketId = shop.reserve(ingredient).bind()                // 1. reserve\n    val minutes = shop.deliveryMinutes(basketId)                  // 2. check the time\n    ensure(minutes < LATEST_MINUTES) { KitchenError.TooLate(minutes) }\n    val slotId = shop.book(basketId).bind()                       // 3. book\n    Delivery(basketId, slotId)\n}"},
        "note": "Both are the same railway: the first `Err` or `Left` ends the pipeline and comes back unchanged, and the sealed error type keeps every `when` or `switch` over it exhaustive. The differences are in how it reads and what the library brings. Java nests a lambda per step, so a five-step pipeline drifts to the right, and every `Err` has to be rebuilt because Java has no `Nothing` and no declaration-site variance. Kotlin's `either { }` keeps the steps flat: `bind()` and `ensure` stop the block with the error, so the code reads like the happy path. Arrow also brings what the hand-written version lacks: `zipOrAccumulate` and `mapOrAccumulate` for collecting errors, `Either.catch` that lets cancellation through, and `mapLeft` and `recover` for translating errors between layers."
    },
    "worked": {
        "title": "Layer the \"order it\" button: check everything, then stop at the first failure",
        "steps": [
            {"say": "The cook types an ingredient line and taps \"order it\". 1. Check the line at the edge and collect every problem, so the cook fixes the whole line at once. The lab's `validate` returns `Either<NonEmptyList<KitchenError>, Ingredient>`.", "code": "val checked: Either<NonEmptyList<KitchenError>, Ingredient> = validate(form)\n// IngredientForm(\"fl0ur\", -5, \"oz\", \"\") gives Left([InvalidName(name=fl0ur), InvalidAmount(amount=-5), UnsupportedUnit(unit=oz)])", "lang": "kotlin", "alt_lang": "java", "alt_code": "Validated<Ingredient> checked = validate(form);   // every rule runs; the errors are collected\nif (checked instanceof Invalid<Ingredient> invalid) return showProblems(invalid.errors());"},
            {"say": "2. Run the shop steps fail-fast, and give the two kinds of error one type so the button can show either. `mapLeft` changes the error side and leaves a `Right` alone.", "code": "sealed interface ScreenError {\n    data class Invalid(val errors: NonEmptyList<KitchenError>) : ScreenError\n    data class Failed(val error: KitchenError) : ScreenError\n}\n\nfun orderIt(form: IngredientForm, shop: Shop): Either<ScreenError, Delivery> = either {\n    val ingredient = validate(form).mapLeft(ScreenError::Invalid).bind()   // every line error at once\n    order(ingredient, shop).mapLeft(ScreenError::Failed).bind()            // the first shop failure\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "sealed interface ScreenError {}\nrecord InvalidLine(List<KitchenError> errors) implements ScreenError {}\nrecord Failed(KitchenError error) implements ScreenError {}\n\nOutcome<ScreenError, Delivery> orderIt(IngredientForm form, Shop shop) {\n    return switch (validate(form)) {\n        case Invalid<Ingredient> invalid -> new Err<>(new InvalidLine(invalid.errors()));   // every line error\n        case Valid<Ingredient> valid -> switch (order(valid.value(), shop)) {              // the first shop failure\n            case Ok<KitchenError, Delivery> ok -> new Ok<>(ok.value());\n            case Err<KitchenError, Delivery> err -> new Err<>(new Failed(err.error()));\n        };\n    };\n}"},
            {"say": "3. At the outer edge, the shop's own client library throws when the network gives up. Turn the one failure that means something to the cook into a value, and let everything else fly. A `SocketTimeoutException` (the network call gave up waiting) becomes `ShopClosed`, which the screen can show; an `IllegalStateException` is a bug and must stay an exception.", "code": "fun ShopClient.reserveSafely(body: String): Either<KitchenError, String> =\n    Either.catch { post(body) }                     // rethrows CancellationException and fatal errors\n        .mapLeft { e -> if (e is SocketTimeoutException) KitchenError.ShopClosed else throw e }", "lang": "kotlin", "alt_lang": "java", "alt_code": "Outcome<KitchenError, String> reserveSafely(ShopClient client, String body) throws IOException {\n    try {\n        return new Ok<>(client.post(body));\n    } catch (SocketTimeoutException e) {\n        return new Err<>(new ShopClosed());            // the one failure that means something to the cook\n    }                                                  // other exceptions fly on: a bug stays a bug\n}"},
            {"say": "4. Turn errors into screen messages in exactly one place, with an exhaustive `when` and no `else`. When someone adds a `KitchenError` case next year, this function stops compiling until they decide what the cook should read.", "code": "fun message(error: ScreenError): String = when (error) {\n    is ScreenError.Invalid -> \"Please fix ${error.errors.size} things in this line\"\n    is ScreenError.Failed -> when (error.error) {\n        KitchenError.OutOfStock -> \"The shop is out of it\"\n        is KitchenError.TooLate -> \"It would arrive after your guests\"\n        KitchenError.ShopClosed -> \"The shop isn't answering, try later\"\n        is KitchenError.InvalidName, is KitchenError.InvalidAmount,\n        is KitchenError.UnsupportedUnit, is KitchenError.NoteTooLong -> \"Please check this line\"\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "String message(ScreenError error) {\n    return switch (error) {\n        case InvalidLine i -> \"Please fix \" + i.errors().size() + \" things in this line\";\n        case Failed f -> switch (f.error()) {\n            case OutOfStock o -> \"The shop is out of it\";\n            case TooLate t -> \"It would arrive after your guests\";\n            case ShopClosed c -> \"The shop isn't answering, try later\";\n            case InvalidName n -> \"Please check this line\";\n            case InvalidAmount a -> \"Please check this line\";\n            case UnsupportedUnit u -> \"Please check this line\";\n            case NoteTooLong l -> \"Please check this line\";\n        };\n    };\n}"}
        ]
    },
    "lab": {
        "title": "Check a line, order it, and keep cancellation working",
        "minutes": 15,
        "files": [
            f"{LAB}/main/kotlin/workbench/functional/l07/Validation.kt",
            f"{LAB}/main/kotlin/workbench/functional/l07/Pipeline.kt",
            f"{LAB}/main/kotlin/workbench/functional/l07/SafeCatching.kt",
            f"{LAB}/main/kotlin/workbench/functional/l07/Model.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l07.*'",
        "steps": [
            "Run the tests. Ten of twelve fail. The two that pass check `runCatchingCancellable` with a value and an ordinary exception, where plain `runCatching` already works. `Model.kt` holds the types and needs no changes.",
            "In `Validation.kt`, write `checkName` and `checkNote` in the style of the two rules above them.",
            "Write `validate` as `either { zipOrAccumulate(...) { ... } }`, with the four checks in the order the KDoc gives: name, amount, unit, note.",
            "In `Pipeline.kt`, write `order` as one `either { }` block: `bind()` each shop call that returns an `Either`, and `ensure` the delivery time.",
            "In `SafeCatching.kt`, make `runCatchingCancellable` rethrow `CancellationException`. The cancellation test runs on the virtual time of `kotlinx-coroutines-test`, a clock the test controls, so it finishes at once.",
            "Run the tests until all twelve pass."
        ],
        "hints": [
            "`zipOrAccumulate` takes up to nine lambdas and then a final lambda that receives their results. Inside each lambda you can call the `check...` functions directly, because the lambdas run in a `Raise` context.",
            "In `order`, read the minutes into a `val` first, then `ensure(minutes < LATEST_MINUTES) { KitchenError.TooLate(minutes) }`.",
            "Import `CancellationException` from `kotlin.coroutines.cancellation`. Catch it before the general `Throwable` clause and rethrow it, or use `runCatching { block() }.onFailure { if (it is CancellationException) throw it }`.",
            "If `either` or `zipOrAccumulate` won't resolve, add `import arrow.core.raise.either` and `import arrow.core.raise.zipOrAccumulate`."
        ],
        "done_when": "All twelve tests in `ErrorsAsValuesTest` pass."
    },
    "drill": {
        "title": "A railway from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `Outcome<E, A>` with its two cases, `map` and `andThen`, with the variance that lets an error pass through unchanged. Then chain `checkBatter`, `mix` and `bake` with it. Check: does your `Err` branch need to build a new object?",
        "answer": {
            "lang": "kotlin",
            "src": "sealed interface Outcome<out E, out A> {\n    data class Ok<A>(val value: A) : Outcome<Nothing, A>\n    data class Err<E>(val error: E) : Outcome<E, Nothing>\n}\n\ninline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =\n    when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }   // Err<E> is an Outcome<E, B>\n\ninline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =\n    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }\n\nfun makeLoaf(b: Batter) = checkBatter(b).andThen(::mix).andThen(::bake)",
            "alt": {
                "lang": "java",
                "src": "sealed interface Outcome<E, A> {\n    default <B> Outcome<E, B> map(Function<? super A, ? extends B> f) {\n        return switch (this) {\n            case Ok<E, A> ok -> new Ok<>(f.apply(ok.value()));\n            case Err<E, A> err -> new Err<>(err.error());          // Java must rebuild the Err\n        };\n    }\n    default <B> Outcome<E, B> andThen(Function<? super A, Outcome<E, B>> f) {\n        return switch (this) {\n            case Ok<E, A> ok -> f.apply(ok.value());\n            case Err<E, A> err -> new Err<>(err.error());\n        };\n    }\n}\nrecord Ok<E, A>(A value) implements Outcome<E, A> {}\nrecord Err<E, A>(E error) implements Outcome<E, A> {}\n\nOutcome<BakeErr, String> makeLoaf(Batter b) { return checkBatter(b).andThen(this::mix).andThen(this::bake); }"
            }
        }
    },
    "recap": [
        "Expected failures, such as an empty jar or a unit the app doesn't know, belong in the return type as values. Bugs and broken machines stay exceptions.",
        "A sealed result with an exhaustive `when` and no `else` makes the compiler list every case you forgot to handle.",
        "A two-case result with `map` and `andThen` is a railway: each step runs only on the success track. `out` variance and `Nothing` let an error pass through unchanged.",
        "`kotlin.Result` wraps code that throws. `runCatching` catches every `Throwable`, `CancellationException` included, and `map` doesn't catch: use `mapCatching`.",
        "Arrow's `either { }` with `bind` and `ensure` is fail-fast; `zipOrAccumulate` runs every check and collects the errors in a `NonEmptyList`.",
        "The limit: a returned error only helps if someone reads it. Kotlin 2.4.21 doesn't warn about an ignored return value by default, and error unions like `Recipe | NotFound` are still a proposal (KEEP-0441, KEEP-0462)."
    ],
    "closing": "We started with a custard that split and two cooks, one who hands back a note and one who throws the pan. Expected failures became notes: a sealed result the compiler checks, a railway where a note skips to the end of the line, and Arrow's `either { }`, which stops at the first error or, with `zipOrAccumulate`, collects them all. `runCatching` stayed at the edge, with cancellation let through.\n\nSearch your code for `catch (e: Exception)` and `runCatching`. Is each one catching a bug, an expected failure, or a cancel it should let go?\n\nNext, we'll finish the track with data that never changes. What do `val` and a read-only `List` really promise?",
    "quiz": [
        {"q": "Running out of flour must be handled by every caller of `takeFlour`. Which signature says so in a way the compiler can check?", "options": ["`fun takeFlour(grams: Int): Int`, with a KDoc saying it throws `NotEnoughFlourException`", "`fun takeFlour(grams: Int): Result<Int>`", "`fun takeFlour(grams: Int): Int?`", "`fun takeFlour(grams: Int): Either<JarFailure, Int>`, where `JarFailure` is sealed"], "answer": 3, "why": "Only the `Either` with a sealed error type names the possible failures, and a `when` over `JarFailure` is checked for every case. The exception is invisible to the compiler. `Result`'s failure is any `Throwable`, so it says nothing about flour. A nullable return drops the reason entirely."},
        {"q": "Inside `launch`, a coroutine runs `val r = runCatching { shop.ask(item) }` (a suspend call) and then `orders.add(entry)`, which doesn't suspend. The job is cancelled while `ask` waits. What happens?", "options": ["`add` never runs: cancellation stops the coroutine at once", "`r` is a failure holding a `CancellationException`, and `add` runs", "`runCatching` rethrows `CancellationException` by itself", "The cancel is ignored until `ask` returns its value"], "answer": 1, "why": "`runCatching` catches every `Throwable`, so the cancel becomes a failed `Result`. The coroutine is still cancelled, but code without a suspension point keeps running, so the order is added after the cancel. Rethrow `CancellationException`, or use `Either.catch`, which does it for you.", "from": "co-05"},
        {"q": "`runCatching { parse(text) }.map { toRecipe(it) }`. `parse` succeeds, but `toRecipe` throws `IllegalArgumentException` for a bad field. What does the expression do?", "options": ["Throws the `IllegalArgumentException` out of `map`", "Returns a `Failure` holding the `IllegalArgumentException`", "Returns the original `Success`", "Returns `Success(null)`"], "answer": 0, "why": "`map` changes a success but doesn't catch exceptions from its lambda. Only `mapCatching` captures them as a `Failure`. A chain that should be safe from end to end needs the `Catching` variant on every step that can throw."},
        {"q": "A form line has an amount of -5 and the unit `oz`. What does `either { Amount(validAmount(a), validUnit(u)) }` return?", "options": ["`Left` with both errors", "It throws on the first error", "`Left(InvalidAmount(...))` only", "`Left(UnsupportedUnit(...))` only"], "answer": 2, "why": "`either { }` is fail-fast. Arguments are evaluated left to right, `validAmount` raises first, the block stops, and `validUnit` never runs. To report both, use `zipOrAccumulate`, which runs every check and returns `Left` with a `NonEmptyList` of all the errors."},
        {"q": "From the scope functions lesson: `open?.let { menu.add(it) } ?: run { menu.add(suggest()) }` ran both branches when `add` returned null for a dish on the menu already. Now `add` returns `Either<MenuError, SlotId>`. Can both branches still run?", "options": ["Yes, whenever `add` returns a `Left`", "No: an `Either` is never null, so `run` runs only when `open` is null", "It no longer compiles", "Only when `add` throws"], "answer": 1, "why": "`?:` fires only on `null`. An `Either` is always a value, `Left` or `Right`, so the left side is null only when no dish is open. Errors as values removed the accidental overlap between \"no result\" and \"nothing there\". The dish on the menu already is now a `Left` the caller can see and handle.", "from": "fp-06"}
    ],
    "flashcards": [
        {"front": "Exception or value: the jar is out of flour?", "back": "A value. It's expected, and the caller must decide what to do. Keep exceptions for bugs and failures nobody can handle on the spot."},
        {"front": "What does a sealed type plus a `when` with no `else` buy you?", "back": "Adding a case breaks every `when` that doesn't handle it: `'when' expression must be exhaustive. Add the 'X' branch or an 'else' branch.`"},
        {"front": "What does `runCatching` catch?", "back": "Every `Throwable`: ordinary exceptions, `OutOfMemoryError`, `StackOverflowError`, and `CancellationException`, which breaks coroutine cancellation."},
        {"front": "`Result.map` vs `Result.mapCatching`?", "back": "`map` lets an exception from its lambda escape. `mapCatching` turns it into a `Failure`."},
        {"front": "Two `ensure` calls inside `either { }` would both fail. What comes back?", "back": "Only the first error: `either { }` is fail-fast. Use `zipOrAccumulate` to collect all of them."},
        {"front": "Does Arrow's `Either.catch` capture a `CancellationException`?", "back": "No. It rethrows `CancellationException` and fatal errors such as `OutOfMemoryError`, and captures ordinary exceptions as a `Left`."},
        {"front": "Does Kotlin 2.4.21 compile `fun load(): Recipe | NotFound`?", "back": "No. Rich errors are a proposal (KEEP-0441, KEEP-0462); 2.4.21 reports a syntax error."}
    ],
    "terms": [
        {"term": "Exception", "plain": "An object a function throws to say something failed. It travels up through the callers until some code catches it."},
        {"term": "Checked exception", "plain": "In Java, an exception a method must list in its signature, so the compiler makes callers handle it. Kotlin has none."},
        {"term": "Error as a value", "plain": "A failure returned in the result type, like any other value, instead of thrown."},
        {"term": "Exhaustive when", "plain": "A `when` over a sealed type that covers every subtype, so it needs no `else` and breaks when a subtype is added."},
        {"term": "Railway-oriented programming", "plain": "Chaining steps on a success track and a failure track: after the first failure, the later steps are skipped."},
        {"term": "Either", "plain": "Arrow's two-case type: `Left(error)` or `Right(value)`, with a typed error side."},
        {"term": "Fail fast", "plain": "Stop at the first error and return it; the remaining steps don't run."},
        {"term": "Error accumulation", "plain": "Run every independent check and return all the errors together, in Arrow as a `NonEmptyList`."}
    ],
    "explain_back": {
        "prompt": "A teammate proposes `fun order(item: Ingredient): Result<Delivery>` for the app's grocery feature, \"because Result is Kotlin's built-in way to return errors\". Explain why it's a poor fit, and what you'd use instead.",
        "answer": "`Result` has one type parameter, and its failure side is always a `Throwable`, so the signature says \"this can fail somehow\" and nothing about how. The caller can't tell an empty shelf from a late delivery from a shop that isn't answering without inspecting exception classes, and the compiler won't check that every case is handled. The Kotlin team's own design notes say `Result` isn't meant for domain errors. It also comes from `runCatching`, which catches `CancellationException` and fatal errors unless you're careful. I'd model the expected failures as a sealed `KitchenError` (`OutOfStock`, `TooLate`, `ShopClosed`, ...) and return `Either<KitchenError, Delivery>`, or a sealed result type if we don't want Arrow. Then a `when` over the error is exhaustive, adding a case breaks the build where it must be handled, and real bugs stay exceptions for the general handler."
    },
    "deeper": {
        "minutes": 10,
        "body": "Three parts of Arrow are worth knowing once `either { }` feels natural.\n\n**Raise without Either.** The lab's checks are functions with a `Raise<KitchenError>` receiver: they don't return an `Either`, they *raise* inside whatever block calls them. Kotlin 2.4.0 made context parameters Stable, and Arrow 2.3.0 ships matching versions of `ensure`, `raise` and `bind` in the `arrow.core.raise.context` package, so the same check can be written as `context(_: Raise<KitchenError>) fun checkUnit(unit: String): String`. With Kotlin 2.4.21 that compiles without any compiler flag. Arrow's own docs still show the extension-receiver style and describe context parameters as a future option, so expect both styles in code you read.\n\n**Collections and the experimental block.** `mapOrAccumulate` checks every element of a list and collects the failures: running it over the amounts `[10, -1, 20, -2]` gives `Either.Left([InvalidAmount(amount=-1), InvalidAmount(amount=-2)])`. There is also an `accumulate { ensureOrAccumulate(...) }` block that reads like a list of checks. In Arrow 2.3.0 it is still marked `@ExperimentalRaiseAccumulateApi`, so you opt in with `@OptIn(ExperimentalRaiseAccumulateApi::class)`; `zipOrAccumulate` is the stable choice.\n\n**Translating errors between layers.** `mapLeft` changes the error value and leaves a `Right` alone, as in the worked example. `recover` is more general: inside it you can run any computation that may itself raise, for example trying a second shop when the first returns `ShopClosed`. Use `mapLeft` to rename errors at a boundary, and `recover` to handle them."
    },
    "sources": [
        {"title": "KEEP: Result (Kotlin stdlib design notes)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md"},
        {"title": "KEEP-0441: Rich Errors, motivation and rationale", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md"},
        {"title": "Validation, Arrow docs source", "url": "https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/validation.md"},
        {"title": "kotlinx.coroutines issue 1814: a runCatching that rethrows CancellationException", "url": "https://github.com/Kotlin/kotlinx.coroutines/issues/1814"},
        {"title": "Exceptions (Kotlin docs)", "url": "https://kotlinlang.org/docs/exceptions.html"}
    ]
}

out = ROOT / "content/lessons/fp-07.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
