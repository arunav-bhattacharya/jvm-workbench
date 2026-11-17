import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l02.demo"


def kdemo(name, alt=True):
    path = f"{LAB}/demo/kotlin/workbench/functional/l02/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(name + "Java")
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l02/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="A captured var moves into a Ref box on the heap, like a note pinned to a recipe card. makeCounter and the lambda both point at the box. '
    'Two threads calling the lambda both read, add and write the same plain field, so updates are lost.">'
    '<text class="t-s t-m" x="115" y="26" text-anchor="middle">the function that made it</text>'
    '<text class="t-s t-m" x="345" y="26" text-anchor="middle">on the heap: the pinned note</text>'
    '<text class="t-s t-m" x="570" y="26" text-anchor="middle">the closure: the card</text>'
    '<rect class="box" x="20" y="40" width="190" height="70" rx="8"/>'
    '<text class="t t-code" x="115" y="68" text-anchor="middle">makeCounter()</text>'
    '<text class="t-s t-code" x="115" y="92" text-anchor="middle">var count</text>'
    '<rect class="box-a" x="260" y="40" width="170" height="70" rx="8"/>'
    '<text class="t t-code" x="345" y="68" text-anchor="middle">Ref$IntRef</text>'
    '<text class="t-s t-code" x="345" y="92" text-anchor="middle">int element = 3</text>'
    '<text class="t-s t-m" x="345" y="132" text-anchor="middle">a plain field: no volatile, no lock</text>'
    '<rect class="box" x="480" y="40" width="180" height="70" rx="8"/>'
    '<text class="t" x="570" y="68" text-anchor="middle">lambda object</text>'
    '<text class="t-s t-code" x="570" y="92" text-anchor="middle">{ ++ref.element }</text>'
    '<line class="ln-a" x1="210" y1="75" x2="256" y2="75" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="480" y1="75" x2="434" y2="75" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="470" y="180" width="90" height="38" rx="8"/>'
    '<text class="t-s" x="515" y="204" text-anchor="middle">thread A</text>'
    '<rect class="box-b" x="575" y="180" width="90" height="38" rx="8"/>'
    '<text class="t-s" x="620" y="204" text-anchor="middle">thread B</text>'
    '<line class="ln" x1="515" y1="180" x2="545" y2="114" marker-end="url(#arr)"/>'
    '<line class="ln" x1="620" y1="180" x2="595" y2="114" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="230" y="196" text-anchor="middle">both call it: read element, add 1, write element</text>'
    '<text class="t-s t-bad" x="230" y="216" text-anchor="middle">one plain field, so increments get lost</text>'
    '</svg>'
)

OPENING = """Picture a box of recipe cards in a kitchen drawer. You can take a card out, lend it to a friend, or lay three cards in a row for tonight's dinner. Or pin a note to one: "my oven runs hot, take five minutes off". A card is a thing you hold, not only something you do.

Code can hold its rules the same way. The last lesson, on pure functions, ended with every rule as a function we called by name. That works until each guest at your table needs different checks, and the method that checks dishes grows one `if` per guest.

The trap waits on the other side. A function value can carry a note from the place it was made. When that note is a variable that changes, everyone who holds the card shares it. Two threads (two paths of work running at once) writing on one note lose marks, and Kotlin compiles that without a word.

In this lesson, we'll turn checks into values, write them four ways, see what a lambda becomes on the JVM, and find the shared box inside a closure. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_IFS = """static String check(Dish d, Guest g) {
    if (d.minutes() > 60) return "too-slow";
    if (!AUTUMN.contains(d.main())) return "out-of-season";
    if (g.vegetarian() && d.diet().equals("meat")) return "has-meat";
    if (g.nutAllergy() && d.nuts()) return "has-nuts";
    // ...one more line for every guest with a need of their own
    return null;
}"""
K_IFS = """fun check(d: Dish, g: Guest): String? {
    if (d.minutes > 60) return "too-slow"
    if (d.main !in AUTUMN) return "out-of-season"
    if (g.vegetarian && d.diet == "meat") return "has-meat"
    if (g.nutAllergy && d.nuts) return "has-nuts"
    // ...one more line for every guest with a need of their own
    return null
}"""
J_VALUE = """// Java has no function types; it uses an interface with one method
Function<Dish, Problem> readyInAnHour =
        d -> d.minutes() > 60 ? new Problem("too-slow", d.name()) : null;
List<Function<Dish, Problem>> everyone = List.of(readyInAnHour, autumnOnly);
Problem p = readyInAnHour.apply(dish);"""
K_VALUE = """typealias Check = (Dish) -> Problem?

val readyInAnHour: Check = { d -> if (d.minutes > 60) Problem("too-slow", d.name) else null }
val everyone: List<Check> = listOf(readyInAnHour, autumnOnly)
val p = readyInAnHour(dish)"""

S0 = """Here's a dinner party in code. The host has a few dishes in mind and a few guests to please. A `Dish` knows its name, how many minutes it takes, its diet (vegan, vegetarian or meat), its main ingredient and whether it has nuts. Before cooking, one method checks a dish against a guest's needs:

""" + pair(J_IFS, K_IFS) + """

Every new need means editing this method, and every guest with a need of their own adds another flag. You can't test one check on its own, reorder them, or let a guest's settings pick which ones apply, because the checks aren't things you can hold. They're lines of code. And the guest list only ever grows.

So make each check a value, like a card in the drawer. In Kotlin a function has a type, written with an arrow: `(Dish) -> Problem?` means "a function that takes a `Dish` and returns a `Problem`, or null". `Problem` is a small data class that says which check said no, and about which dish. You can keep such a function in a `val` or a list, pass it as an argument, and return it from another function, just as you'd handle an `Int`. That's what people mean by **functions as values**.

""" + pair(J_VALUE, K_VALUE) + """

The `{ d -> ... }` part is a **lambda**: a function written right where you need it, with no name, its parameters before the arrow and its body after.

Now the code that checks a dish doesn't know any check. It runs a list: `checks.firstNotNullOfOrNull { check -> check(dish) }`, which calls each check in turn and stops at the first one that returns a problem. Sam is vegetarian, so Sam's list is `everyone + meatFree`. The demo runs four dishes past both lists:

```text
pumpkin soup: everyone=ok, Sam=ok
slow roast: everyone=too-slow, Sam=too-slow
leek and bacon tart: everyone=ok, Sam=has-meat
strawberry cake: everyone=out-of-season, Sam=out-of-season
```

The tart is fine for everyone except Sam, and adding Sam's check changed no other line. The strawberry cake fails because this kitchen cooks in autumn, and the strawberries are five months late.

The two languages spell all this differently. Java has no function types, so it uses a **functional interface**, an interface with one abstract method: `Function<T, R>`, `Predicate<T>`, `Supplier<T>`, or one of your own. You call it by its method name, `apply` or `test`.

Kotlin has real function types, and you call a value of one like a function: `readyInAnHour(dish)`. On the JVM, Kotlin's `(Dish) -> Problem?` is the interface `kotlin.jvm.functions.Function1<Dish, Problem>`, and the call goes to its `invoke` method. The `typealias` only gives the type a short name. It creates nothing new.

**A check you can hold can be tested, reordered and chosen per guest. Make it a value.**

The card in the drawer holds up well so far: store it, lend it, line it up. The picture breaks in one place, and we'll reach it in the last section. First, a lambda is only one of the ways to make a card."""

# ---------------------------------------------------------------- section 1
J_FOUR = """Predicate<Integer> lambda = minutes -> minutes > 60;
Predicate<Integer> anon = new Predicate<>() {                 // anonymous class
    public boolean test(Integer minutes) { return minutes > 60; }
};
Predicate<Integer> ref = Timing::isTooSlow;                    // method reference
Predicate<Integer> obj = new TooSlow(60);                      // class implementing Predicate"""
K_FOUR = """val lambda: (Int) -> Boolean = { minutes -> minutes > 60 }
val anon: (Int) -> Boolean = fun(minutes: Int): Boolean { return minutes > 60 }
val ref: (Int) -> Boolean = ::isTooSlow                        // function reference
val obj: (Int) -> Boolean = TooSlow(60)                        // class TooSlow : (Int) -> Boolean"""

S1 = """A lambda is the most common way to write a function value, but it's one of four. All four below have the same type, and all four ask the same question: does this dish take more than an hour?

""" + pair(J_FOUR, K_FOUR) + """

A lambda with one parameter can leave it unnamed and use `it`: `{ it > 60 }`. Its value is its last expression. That's also why a bare `return` inside a lambda doesn't compile (`'return' is prohibited here.`): `return` belongs to the enclosing `fun`, not to the lambda.

If you want early exits, write an **anonymous function**, the `fun(minutes: Int)` form above, where `return` means what it means everywhere else. Or use a labelled return, `return@label`, which leaves only the lambda. The demo's anonymous function uses its early exit to flag negative times, because a dish that takes minus five minutes is a typo, not a miracle.

A **function reference** turns a named function into a value. `::isTooSlow` points at a top-level function. `Dish::isVegan` is unbound: its type takes the receiver as the first parameter, `(Dish) -> Boolean`. `oven::adjust` is bound to one `oven` object, so its type has only the remaining parameters. `::Problem` points at the constructor.

Two more shapes show up in Kotlin APIs. A function type can be nullable: `((Problem) -> Unit)?` is an optional callback, a function the caller may pass to hear about a problem, or leave out. Mind the parentheses. Without them, `(Problem) -> Unit?` is a function that returns `Unit?`. You call a nullable one with `onProblem?.invoke(p)`.

And a function type can have a **receiver**, a value the lambda sees as `this`. In `Int.() -> Boolean`, the body sees the `Int` as `this`, so `{ this % 15 == 0 }` asks "is this a whole quarter of an hour?". Receivers are how `apply` and `buildList` work. Lesson 6 of this track covers the scope functions, and the Advanced Kotlin track has a lesson on type-safe DSLs. Java has neither: a `Consumer<Problem>` parameter may simply be null by convention, and there is no receiver.

Four spellings, one type. They don't cost the same, though, and the next question is what each one becomes when it runs."""

# ---------------------------------------------------------------- section 2
J_SHAPES = """nonCapturing() == nonCapturing();       // true on HotSpot: one shared instance
capturing(5) == capturing(5);           // false: a new object per evaluation"""
K_SHAPES = """nonCapturing() === nonCapturing()       // true: one shared instance
capturing(5) === capturing(5)           // false: a new object per evaluation
capturing(5) == capturing(5)            // false: lambdas have no equals"""

S2 = """A function value is an object, so something has to create it. What that costs depends on how you wrote it, and Kotlin and Java don't agree on every case.

Since **Kotlin 2.0, lambdas compile to `invokedynamic`** by default, the mechanism Java has used for lambdas since Java 8. `invokedynamic` is a bytecode instruction (one step of the JVM's own machine language) that asks a helper method, the first time it runs, how to do its job.

The compiler moves the lambda body into a private static method, such as `nonCapturing$lambda$0`. Where the lambda is created, it emits an `invokedynamic` whose helper is `LambdaMetafactory.metafactory`. The first time that instruction runs, the JVM spins up a hidden class that implements `Function1` and calls the private method. No `.class` file for the lambda shows up in your build output. (Kotlin 1.x generated one class per lambda, and the compiler flag `-Xlambdas=class` still brings that back.)

How many objects you get depends on what the lambda **captures**, that is, which variables from outside its body it uses. The demo's `capturing(extra)` returns `{ it + extra }`, a card with a note pinned to it, while `nonCapturing()` returns `{ it + 10 }`, which needs nothing from outside:

""" + pair(J_SHAPES, K_SHAPES) + """

A **non-capturing** lambda uses nothing from outside its body, so one instance serves every call. A **capturing** lambda holds the values it uses (`extra` here), so each evaluation allocates a new object with those values inside. On JDK 21, the demo printed this for Kotlin (the number after `0x` changes from run to run):

```text
non-capturing lambda: same object every time?  true
capturing lambda: same object every time?      false
capturing lambdas equal with == ?              false
unbound reference ::addRest: same object?      true
bound reference oven::adjust: same object?     false

lambda class:    workbench.functional.l02.demo.LambdaShapesKt$$Lambda/0x00000007c0001800  (hidden: true)
reference class: workbench.functional.l02.demo.LambdaShapesKt$topLevelRef$1  (hidden: false, extends FunctionReferenceImpl)
```

The shared instance for a non-capturing lambda is what HotSpot does today, not a promise. Don't write code that depends on it.

The last line is where Kotlin differs from Java. In Kotlin 2.4.21, function references such as `::addRest` and `oven::adjust` still compile to real classes, `LambdaShapesKt$topLevelRef$1` and `LambdaShapesKt$boundRef$1`, which extend `kotlin.jvm.internal.FunctionReferenceImpl`. An unbound reference is a singleton held in a static `INSTANCE` field. A bound one is a new object each time, holding its receiver. Java method references go through `invokedynamic` like lambdas do, and leave no class file behind.

One more cost hides in the types. `(Long) -> Long` is `Function1<Long, Long>`, which is generic, so a call through it **boxes** the `long`: it wraps the number in a `java.lang.Long` object and unwraps it again. Java avoids that with primitive interfaces like `LongUnaryOperator`. Kotlin has no primitive function interfaces. It avoids the box another way, with `inline` functions, which the next lesson covers.

None of this is a reason to avoid lambdas. A capturing lambda costs one small object per evaluation, which the JVM allocates cheaply. It starts to matter in two places: a capturing lambda created inside a hot loop, and code that compares function values with `==`, which never works for lambdas.

Objects are cheap. The surprise is what happens to a captured variable that changes."""

# ---------------------------------------------------------------- section 3
J_COUNTER = """static IntSupplier makeCounter() {
    int[] count = {0};                  // Java makes you build the box yourself
    return () -> ++count[0];
}"""
K_COUNTER = """fun makeCounter(): () -> Int {
    var count = 0
    return { ++count }                  // the lambda keeps count alive
}"""

S3 = """A lambda can use variables from the function that created it, and it keeps them after that function has returned. Code plus the variables it captured is called a **closure**. It's the recipe card with a note pinned to it: "my oven runs hot, take five minutes off". The note was written where the card was made, and it goes wherever the card goes.

""" + pair(J_COUNTER, K_COUNTER) + """

Call `makeCounter()` twice and you get two counters, each with its own `count`. Each one returns 1, 2, 3 and so on.

Look at what the Java version needed. Java refuses to capture a local variable that changes: `local variables referenced from a lambda expression must be final or effectively final`. The reason is mechanical. A local variable lives in the method's **stack frame**, the memory one method call uses for its locals, and that frame is gone once `makeCounter` returns.

The lambda outlives the frame, so all it can take is a copy of the value, and copying a variable that keeps changing would be confusing. Java programmers work around it with a one-element array or an `AtomicInteger`. Either one is an object on the **heap**, the memory where objects live for as long as something points at them, and both sides can share it.

Kotlin builds that object for you, silently. When a lambda captures a `var`, the compiler moves the variable into a small heap object, a `kotlin.jvm.internal.Ref$IntRef` (or `LongRef`, `ObjectRef` and so on). Both the function and the lambda use its field. The field is a plain `public int element`, with no `volatile` and no lock. Java refuses the capture; the Kotlin compiler shrugs and builds the box.

Here the recipe card picture breaks, and it breaks in a way that matters. Lend a paper card and your friend gets their own copy of the note. Hand out a closure and everyone holds the same box.

That's fine on one thread. It's a bug as soon as two threads share the closure. A **thread** is one path of work through a program, and several can run at the same moment. `++count` becomes "read `element`, add one, write `element`", the same read-modify-write as `count++` in the race conditions lesson. When two threads read the same old value, one of the two additions is lost. Nothing in the Kotlin source looks shared. The sharing comes from the box the compiler made.

The `CapturedRace` demo shares one captured `var total` between four tasks on a thread pool (a fixed group of threads that take tasks from a queue). Each task adds 1 a quarter of a million times, and the whole thing runs ten times. One try on this busy 4-core machine began like this:

```text
run  1: expected 1,000,000, got   250,956 (lost 749,044)
run  2: expected 1,000,000, got 1,000,000 (lost 0)
run  3: expected 1,000,000, got 1,000,000 (lost 0)
```

Runs 4 to 10 were correct too. A second try lost 202,126 in run 1, and a third lost nothing in all ten. The Java twin, with its hand-made array box, lost exactly 500,000 in one run.

Most losses land in the first run, while the JVM is still interpreting the loop. Then the JIT compiler, the part of the JVM that turns busy code into machine code, compiles it. From then on each task keeps the count in a register, a slot inside the processor, and writes it back once at the end. Then a loss wipes out whole tasks, which is why 500,000 is such a round number. The memory model track explains why the JIT may do that to a plain field. A race that shows up once in ten runs is still a race, and the worst kind, because it passes most tests.

**A captured var is one box that everyone holding the closure shares. Never change it from two threads.**

There are two fixes. Share a thread-safe object instead of a `var`: capture `val total = AtomicLong()` and call `total.incrementAndGet()`. Or, better, don't share at all. Let each task count its own work and combine the results at the end with a sum or a `fold`. The second fix is the functional one, and it keeps working when the tasks move to other machines.

That second fix needs functions that take other functions and combine their results. Writing our own is where the next lesson starts."""

L = {
    "id": "fp-02",
    "title": "Function types, lambdas and closures",
    "minutes": 35,
    "goal": "By the end you can store, pass and return functions as values, read any Kotlin function type, predict what a lambda or reference compiles to, and explain why a captured var shared between threads loses updates.",
    "opening": OPENING,
    "warmup": {
        "q": "`fun makeCounter(): () -> Int { var count = 0; return { ++count } }`. Four threads share one counter and call it 250,000 times each. What does the next call return?",
        "options": [
            "Always 1,000,001",
            "It doesn't compile: Kotlin, like Java, won't let a lambda change a captured local",
            "Often less than 1,000,001, and a different number from run to run",
            "Always 250,001, because each thread gets its own copy of count"
        ],
        "answer": 2,
        "why": "Kotlin does let a lambda change a captured `var`. It moves `count` into a heap object, a `Ref$IntRef` with one plain `int` field, that all four threads share. `++count` is a read, an add and a write on that field, so increments get lost when two threads read the same old value. Java would refuse to compile the same code; Kotlin compiles it, and it races. The last section shows the box and the lost counts."
    },
    "sections": [
        {
            "h": "Making a check a value you can hold: function types",
            "body": S0,
            "try": {
                "title": "Add a check without touching the others",
                "minutes": 4,
                "steps": [
                    "Run `ChecksAsValues` (or `ChecksAsValuesJava`). Predict first: which dish gets a different answer for Sam?",
                    "Alex can't eat nuts. Add a check, `val noNuts: Check = { d -> if (d.nuts) Problem(\"has-nuts\", d.name) else null }`, and a list, `val forAlex = listOf(noNuts) + everyone`. Print the answer for the strawberry cake under `forAlex`. (Java: a `NO_NUTS` field, and `Stream.concat(Stream.of(NO_NUTS), EVERYONE.stream()).toList()` for the list.)",
                    "Note what you didn't touch: `firstProblem` and every other check."
                ],
                "code": kdemo("ChecksAsValues"),
                "expect": "The leek and bacon tart passes for everyone and gets `has-meat` for Sam. Under `forAlex`, the strawberry cake gets `has-nuts` instead of `out-of-season`: the order of the list is the order of the checks, and the first problem wins. `firstProblem` didn't change, because it never knew any check."
            },
            "refs": [
                {"title": "Higher-order functions and lambdas: function types (Kotlin docs)", "url": "https://kotlinlang.org/docs/lambdas.html", "kind": "docs"},
                {"title": "java.util.function package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/function/package-summary.html", "kind": "docs"}
            ]
        },
        {
            "h": "Four ways to write a function value: lambdas, references and the rest",
            "body": S1,
            "try": {
                "title": "Four ways, one type",
                "minutes": 4,
                "steps": [
                    "Open `FourWays.kt` (or `FourWaysJava.java`). Predict the four booleans it prints for 45, 90 and -5 minutes.",
                    "Run it.",
                    "In `tooSlowLambda`, add the same early exit the anonymous function has: `if (minutes < 0) return true` on its own line before `minutes > 60`. Run it and read the error. Then fix it with a label: write `slow@{ minutes -> ... }` and `return@slow true`."
                ],
                "code": kdemo("FourWays"),
                "expect": "45 prints four `false`, 90 four `true`. For -5 only the anonymous function says `true`, because it is the only one with the early `return`. The bare `return` in the lambda fails with `'return' is prohibited here.`; the labelled `return@slow true` returns from the lambda and compiles. The Java version has no `isQuarterHour` line, because Java has no receiver types."
            }
        },
        {
            "h": "What a lambda turns into on the JVM, and what it costs",
            "body": S2,
            "try": {
                "title": "Count the objects and the class files",
                "minutes": 5,
                "steps": [
                    "Run `LambdaShapes` (or `LambdaShapesJava`). Before you look, predict the five `true` or `false` answers.",
                    "From `labs/`, list the compiled demo classes: `ls functional/build/classes/kotlin/demo/workbench/functional/l02/demo/`. Look for a class per lambda and a class per reference.",
                    "Run `javap -c -p functional/build/classes/kotlin/demo/workbench/functional/l02/demo/LambdaShapesKt.class` and find the first instruction of `nonCapturing` and of `topLevelRef`."
                ],
                "code": kdemo("LambdaShapes"),
                "expect": "`true, false, false, true, false` in both languages. The Kotlin lambda's class is a hidden class named like `LambdaShapesKt$$Lambda/0x...`, while the reference's class is an ordinary class, `LambdaShapesKt$topLevelRef$1`, that extends `FunctionReferenceImpl`. The directory has `LambdaShapesKt$topLevelRef$1.class` and `LambdaShapesKt$boundRef$1.class`, and no file for any lambda. In the Java version, the lambda and the method reference are both hidden classes. `javap` shows `invokedynamic ... invoke:()Lkotlin/jvm/functions/Function1;` in `nonCapturing` and `getstatic ... LambdaShapesKt$topLevelRef$1.INSTANCE` in `topLevelRef`."
            },
            "refs": [
                {"title": "What's new in Kotlin 2.0.0: lambdas via invokedynamic", "url": "https://kotlinlang.org/docs/whatsnew20.html", "kind": "docs"}
            ]
        },
        {
            "h": "A closure keeps its variables, and a captured var becomes one shared box",
            "body": S3,
            "figure": {"svg": FIG, "caption": "A captured var moves into a Ref box on the heap, a note pinned to the card. The function, the lambda and every thread that calls the lambda share its plain field."},
            "try": {
                "title": "Lose updates, then fix it two ways",
                "minutes": 5,
                "steps": [
                    "Run `CapturedRace` (or `CapturedRaceJava`). Four pool threads each add 1 to a captured `total` 250,000 times, ten runs in a row. If all ten runs print 1,000,000, run it once more: the losses come and go.",
                    "Fix it by sharing a thread-safe object: make it `val total = AtomicLong()` (Java: `AtomicLong total = new AtomicLong()`), call `total.incrementAndGet()` in the loop, and print `total.get()`. Run it.",
                    "Undo that, and fix it by not sharing: make each task return its own count, `pool.submit(Callable { go.await(); var mine = 0L; repeat(250_000) { mine += 1 }; mine })`, then add up `tasks.sumOf { it.get() }`. (Java: return `mine` from the lambda and add up the `Future<Long>` results.) Run it."
                ],
                "code": kdemo("CapturedRace"),
                "expect": "The broken version loses updates in some runs, by different amounts each time, most often in run 1. Here one try lost 749,044 in run 1 and nothing after, and another lost nothing in all ten runs. Both fixes print exactly 1,000,000 in every run, every try. The don't-share version has no contention at all: `mine` is only ever touched by one thread, so the compiler keeps it a plain local (`repeat` is inline, so no lambda captures it)."
            },
            "refs": [
                {"title": "Ref.java: the boxes for captured vars (Kotlin stdlib source)", "url": "https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/runtime/kotlin/jvm/internal/Ref.java", "kind": "read"}
            ]
        }
    ],
    "compare": {
        "title": "Checks and closures with functional interfaces and with function types",
        "java": {
            "title": "Checks.java",
            "src": "import java.util.List;\nimport java.util.function.Function;\nimport java.util.function.IntSupplier;\n\nrecord Dish(String name, int minutes, String diet) {}\nrecord Problem(String check, String dish) {}\n\nfinal class Checks {\n    // a function value is an instance of a functional interface\n    static Function<Dish, Problem> readyWithin(int maxMinutes) {\n        return d -> d.minutes() > maxMinutes ? new Problem(\"too-slow\", d.name()) : null;   // captures maxMinutes\n    }\n\n    static Problem firstProblem(Dish d, List<Function<Dish, Problem>> checks) {\n        return checks.stream()\n                .map(check -> check.apply(d))        // called by its method name\n                .filter(p -> p != null)\n                .findFirst()\n                .orElse(null);\n    }\n\n    // a captured local that changes is a compile error; the array is the box, built by hand\n    static IntSupplier makeCounter() {\n        int[] count = {0};\n        return () -> ++count[0];\n    }\n}"
        },
        "kotlin": {
            "title": "Checks.kt",
            "src": "data class Dish(val name: String, val minutes: Int, val diet: String)\ndata class Problem(val check: String, val dish: String)\n\ntypealias Check = (Dish) -> Problem?             // a real function type: Function1 on the JVM\n\nfun readyWithin(maxMinutes: Int): Check = { d ->  // captures maxMinutes\n    if (d.minutes > maxMinutes) Problem(\"too-slow\", d.name) else null\n}\n\nfun firstProblem(d: Dish, checks: List<Check>): Problem? =\n    checks.firstNotNullOfOrNull { check -> check(d) }   // called like a function\n\n// capturing a var is allowed; the compiler builds the Ref box for you\nfun makeCounter(): () -> Int {\n    var count = 0\n    return { ++count }\n}"
        },
        "note": "Kotlin has function types; Java has functional interfaces. That changes three things you notice every day. Kotlin calls a function value with `f(x)`, where Java needs the interface's method name (`apply`, `test`, `getAsInt`), and Kotlin has one family of types, `(A) -> B`, where Java has dozens of interfaces, primitive ones included. Kotlin's types can say \"may be null\" (`Problem?`, `((Problem) -> Unit)?`), so a check that returns null shows it in its type. And Kotlin lets a lambda capture a `var` by moving it into a `Ref` box, where Java insists on effectively final locals and makes you write the box. Under the hood both compile lambdas with `invokedynamic`; only Kotlin's function references still compile to classes."
    },
    "worked": {
        "title": "Find the hidden shared box in a recipe import",
        "steps": [
            {
                "say": "A recipe app imports a big file of recipes. It splits the list into chunks of 500 with `chunked(500)`, saves each chunk on a thread pool, and counts how many recipes it saved. Under load the count comes out a little low, and only sometimes. Find the shared state before reading on.",
                "code": "fun importAll(recipes: List<Recipe>, pool: ExecutorService): Int {\n    var saved = 0\n    val futures = recipes.chunked(500).map { chunk ->\n        pool.submit {\n            chunk.forEach { r -> if (book.save(r)) saved += 1 }\n        }\n    }\n    futures.forEach { it.get() }\n    return saved\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "// The Java version doesn't compile as written:\nstatic int importAll(List<Recipe> recipes, ExecutorService pool) throws Exception {\n    int saved = 0;\n    List<Future<?>> futures = new ArrayList<>();\n    for (List<Recipe> chunk : chunks(recipes, 500)) {\n        futures.add(pool.submit(() -> {\n            for (Recipe r : chunk) if (book.save(r)) saved += 1;\n            // error: local variables referenced from a lambda expression must be final or effectively final\n        }));\n    }\n    for (Future<?> f : futures) f.get();\n    return saved;\n}"
            },
            {
                "say": "1. Find the box. `saved` is a `var` captured by the lambda passed to `submit`, which runs on pool threads. The compiler turned it into one `Ref$IntRef`, and every chunk task does read, add, write on its plain `element` field. (`forEach` is inline, so its lambda doesn't count; the `submit` lambda is the one that captures.) Java refused the same code, and the usual Java workaround is the same box written by hand.",
                "code": "// roughly what the compiler made of it\nval saved = Ref.IntRef()                        // one box on the heap\npool.submit { ...; saved.element += 1 }         // every task, on every thread",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "int[] saved = {0};                              // the box Java makes you write\npool.submit(() -> { ...; saved[0] += 1; });     // the same race"
            },
            {
                "say": "2. Don't share. Make each task count its own saves in a local, return that count, and add the counts up on the calling thread. Each task's lambda now captures only its `chunk`, which nobody changes. Self-check: why is the `var mine` inside the task safe? (It's a local of that one task, used on one thread, and no other lambda captures it, so it never becomes a box.)",
                "code": "fun importAll(recipes: List<Recipe>, pool: ExecutorService): Int {\n    val futures = recipes.chunked(500).map { chunk ->\n        pool.submit(Callable {                            // 1. each task returns a value\n            var mine = 0                                  //    a local: only this task touches it\n            for (r in chunk) if (book.save(r)) mine++\n            mine\n        })\n    }\n    return futures.sumOf { it.get() }                     // 2. combine on one thread\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static int importAll(List<Recipe> recipes, ExecutorService pool) throws Exception {\n    List<Future<Integer>> futures = new ArrayList<>();\n    for (List<Recipe> chunk : chunks(recipes, 500)) {\n        futures.add(pool.submit(() -> {                       // 1. each task returns a value\n            int mine = 0;                                     //    a local: only this task touches it\n            for (Recipe r : chunk) if (book.save(r)) mine++;\n            return mine;\n        }));\n    }\n    int total = 0;\n    for (Future<Integer> f : futures) total += f.get();     // 2. combine on one thread\n    return total;\n}"
            },
            {
                "say": "3. If you do need a live shared number, say a progress bar while the import runs, share a thread-safe object through a `val`, never a `var`. `LongAdder` spreads the work over several cells and is cheaper than `AtomicLong` when many threads add at once.",
                "code": "val savedSoFar = LongAdder()                   // a val: the reference never changes\npool.submit { chunk.forEach { r -> if (book.save(r)) savedSoFar.increment() } }",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "LongAdder savedSoFar = new LongAdder();        // effectively final, so Java is happy too\npool.submit(() -> { for (Recipe r : chunk) if (book.save(r)) savedSoFar.increment(); });"
            }
        ]
    },
    "lab": {
        "title": "Checks as values, and a counter that survives eight threads",
        "minutes": 13,
        "files": [
            "labs/functional/src/main/kotlin/workbench/functional/l02/Checks.kt",
            "labs/functional/src/main/kotlin/workbench/functional/l02/Counters.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l02.*'",
        "steps": [
            "Open `Checks.kt`. A `Dish` has a name, the minutes it takes, a diet and a main ingredient, and a `Check` is a `(Dish) -> Problem?`. Run the tests. All ten fail: nine with `NotImplementedError`, and the shared-counter test with a short count, something like `but was: 1580389L` where 1,600,001 was expected.",
            "Write `readyWithin` (return a lambda that captures `maxMinutes`), `meatFree` (a lambda in a `val`) and `inSeason`. Then replace the body of `seasonCheck` with the reference `::inSeason`.",
            "Write `firstProblem` and `allProblems`. `firstProblem` must stop at the first problem: one test counts calls to a later check that phones a guest.",
            "Write `suits`. The callback is optional, so call it with `?.invoke`.",
            "In `Counters.kt`, write `makeCounter`. Then fix `makeSharedCounter` so the 8-thread test passes. Keep the return type `() -> Long`.",
            "Run the tests until all ten pass, then run them twice more. A race fix has to pass every time."
        ],
        "hints": [
            "`checks.firstNotNullOfOrNull { check -> check(dish) }` returns the first non-null result and stops there. `mapNotNull` keeps every non-null result.",
            "If `meatFree` gives you a type error, name the lambda's parameter and make both branches of the `if` produce a `Problem?`: `{ d -> if (d.diet in MEAT_FREE_DIETS) null else Problem(...) }`.",
            "A `val` that holds an `AtomicLong` is safe to capture: the reference never changes, and `incrementAndGet()` is one atomic step that returns the new value."
        ],
        "done_when": "All ten tests in `FunctionValuesTest` pass, three runs in a row."
    },
    "drill": {
        "title": "Write two closures from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `scaleFor(guests, serves)`, which returns a function from grams to grams: a recipe that serves `serves` people, scaled for `guests`, so `grams * guests / serves`. Then write `makeCounter()`, and add a one-line comment saying what the compiler does with its captured `var`. Write both in Kotlin and in Java, and note the one line Java refuses to compile.",
        "answer": {
            "lang": "kotlin",
            "src": "fun scaleFor(guests: Int, serves: Int): (Int) -> Int =\n    { grams -> grams * guests / serves }    // captures guests and serves\n\nfun makeCounter(): () -> Int {\n    var count = 0          // captured var: moved into a Ref.IntRef box with a plain int field\n    return { ++count }\n}\n\n// val forSix = scaleFor(6, 4)\n// forSix(200) == 300, forSix(250) == 375\n// val c = makeCounter(); c(); c() == 2",
            "alt": {
                "lang": "java",
                "src": "static IntUnaryOperator scaleFor(int guests, int serves) {\n    return grams -> grams * guests / serves;\n}\n\nstatic IntSupplier makeCounter() {\n    // int count = 0; return () -> ++count;   <- won't compile:\n    // local variables referenced from a lambda expression must be final or effectively final\n    int[] count = {0};     // the box, written by hand\n    return () -> ++count[0];\n}"
            }
        }
    },
    "recap": [
        "A function type such as `(Dish) -> Problem?` is a type like any other: store its values, put them in lists, pass them and return them. On the JVM it is `Function1`.",
        "Java uses functional interfaces (`Function`, `Predicate`, your own) and calls them by method name. Kotlin calls a function value like a function.",
        "Lambdas, anonymous functions, references and classes that implement a function type all make function values. A bare `return` is prohibited in a lambda that isn't inlined.",
        "Kotlin 2.x compiles lambdas with `invokedynamic`: no class file, one shared instance when nothing is captured, a new object per evaluation when something is. Function references still compile to classes.",
        "A closure keeps the variables it captured. A captured `var` lives in one `Ref` box with a plain field, and everyone holding the closure shares it.",
        "The limit: a closure is only as safe to share as what it captured. Return a value from each task and combine the values, or capture a `val` that holds an atomic."
    ],
    "closing": "We started with a drawer of recipe cards and a dinner party whose checks were stuck inside one method. Each check became a value you can store and line up per guest, and a closure kept its note from where it was made. Then the picture broke: a closure's note isn't copied, it's one shared box.\n\nSearch your Kotlin code for a `var` declared just before a lambda that runs somewhere else, inside `submit { }`, `thread { }` or a callback. Each one is a note several threads may write on.\n\nNext, we'll write functions that take functions and hand them back. How do you write a retry loop once, for every call that might fail?",
    "quiz": [
        {
            "q": "`fun withExtra(extra: Long): (Long) -> Long = { it + extra }`. What do `println(withExtra(5) === withExtra(5))` and `println(withExtra(5)(30) == withExtra(5)(30))` print?",
            "options": [
                "`true` and `true`",
                "`false` and `true`",
                "`false` and `false`",
                "`true` and `false`"
            ],
            "answer": 1,
            "why": "The lambda captures `extra`, so every evaluation creates a new object, and `===` compares objects. Calling both gives `35`, and two `Long` values compare equal with `==`. A lambda that captured nothing would print `true` for the first line, because one shared instance serves every call."
        },
        {
            "q": "Which parameter declaration means \"an optional callback that receives a Problem\"?",
            "options": [
                "`onProblem: (Problem) -> Unit?`",
                "`onProblem: (Problem?) -> Unit`",
                "`onProblem: Problem.() -> Unit`",
                "`onProblem: ((Problem) -> Unit)?`"
            ],
            "answer": 3,
            "why": "The parentheses make the whole function type nullable, so the caller may pass nothing and you call it with `onProblem?.invoke(p)`. Without them, `(Problem) -> Unit?` is a required function that returns `Unit?`. The second takes a nullable argument, and the third is a function with a receiver."
        },
        {
            "q": "In Kotlin 2.4.21, which of these leaves a `.class` file of its own in your build output?",
            "options": [
                "`::isTooSlow`, a reference to a top-level function",
                "`{ d: Dish -> d.minutes > 0 }`",
                "`{ it + extra }`, which captures `extra`",
                "`Runnable { println(\"done\") }`"
            ],
            "answer": 0,
            "why": "Function references still compile to a class extending `FunctionReferenceImpl`; an unbound one is a singleton. Lambdas, capturing or not, and SAM conversions like `Runnable { }` compile to `invokedynamic`, and the JVM creates a hidden class at runtime, with no file on disk. Capturing changes how many objects you get, not whether a class file exists."
        },
        {
            "q": "A pool of four threads imports recipes. Each task's lambda does `saved++` on a captured `var saved = 0`. What happens to `saved`?",
            "options": [
                "It's exact, because Kotlin makes captured vars thread-safe",
                "It doesn't compile, just like in Java",
                "It can end up lower than the number of recipes saved, because all four threads share one plain field in a `Ref` box",
                "Each thread gets its own copy, so it counts only one thread's recipes"
            ],
            "answer": 2,
            "why": "Kotlin allows the capture and moves the variable into one `Ref$IntRef` on the heap. All four threads run read, add, write on its non-volatile `element` field, so increments get lost. Java would reject the code; Kotlin compiles it. Return a count from each task and add them up, or use a `LongAdder`."
        },
        {
            "q": "From Contravariance with in: consumers: `Function1` is declared `Function1<in P1, out R>`. Can you put `val logAll: (Any) -> Problem? = { null }` into a `List<Check>`, where `Check = (Dish) -> Problem?`?",
            "options": [
                "Yes: a function that accepts any object can certainly accept a Dish",
                "No: `Any` is not `Dish`, so the types don't match",
                "Only after an unchecked cast",
                "Only if `Problem` is declared `out`"
            ],
            "answer": 0,
            "why": "The parameter type of a function is an in-position, and `Function1` is contravariant in it: `(Any) -> R` is a subtype of `(Dish) -> R` because every `Dish` is an `Any`. The return type is covariant. The tempting \"no\" applies the subtype arrow the wrong way round, which is exactly what `in` fixes.",
            "from": "gen-05"
        }
    ],
    "flashcards": [
        {"front": "What JVM interface does Kotlin's `(Dish) -> Problem?` compile to?", "back": "`kotlin.jvm.functions.Function1<Dish, Problem>`. Calling the value calls its `invoke` method."},
        {"front": "How do you declare an optional callback that takes a Problem?", "back": "`onProblem: ((Problem) -> Unit)? = null`, with the parentheses, and call it with `onProblem?.invoke(p)`."},
        {"front": "In Kotlin 2.x, is `nonCapturing() === nonCapturing()` true for a lambda that captures nothing?", "back": "Yes, on HotSpot today. The `invokedynamic` call site hands out one shared instance. A capturing lambda is a new object each time."},
        {"front": "Does `::addRest` compile to `invokedynamic` in Kotlin 2.4.21?", "back": "No. Function references still compile to a class that extends `FunctionReferenceImpl`; an unbound one is a singleton `INSTANCE`."},
        {"front": "What does a `var` captured by a lambda become?", "back": "A `kotlin.jvm.internal.Ref` box (`IntRef`, `LongRef`, `ObjectRef`) with a plain, non-volatile `element` field."},
        {"front": "Why won't `{ minutes -> if (minutes < 0) return true; minutes > 60 }` compile?", "back": "A bare `return` returns from the enclosing `fun`, which is only allowed when the lambda is inlined: `'return' is prohibited here.` Use `return@label` or an anonymous function."},
        {"front": "What does javac say when a lambda changes a captured local?", "back": "`local variables referenced from a lambda expression must be final or effectively final`."}
    ],
    "terms": [
        {"term": "Function type", "plain": "A type for functions, like `(Dish) -> Problem?`. Its values can be stored, passed and returned."},
        {"term": "Lambda", "plain": "A function value written inline, with no name: `{ d -> d.minutes > 60 }`."},
        {"term": "Function reference", "plain": "A named function used as a value: `::isTooSlow`, `Dish::isVegan`, `oven::adjust`."},
        {"term": "Functional interface", "plain": "Java's stand-in for a function type: an interface with one abstract method, like `Function<T, R>`."},
        {"term": "Closure", "plain": "A function value together with the variables it captured from the place it was created."},
        {"term": "Capturing lambda", "plain": "A lambda that uses values from outside its body, so each evaluation creates a new object that holds them."},
        {"term": "Ref box", "plain": "The small heap object (`Ref$IntRef` and friends) that the Kotlin compiler puts a captured `var` into."}
    ],
    "explain_back": {
        "prompt": "A teammate's Kotlin counter, a `var n = 0` captured by a lambda that four threads call, loses counts. They say: \"There's no shared field anywhere in my code.\" Explain what the compiler did and what you would change.",
        "answer": "A local variable normally lives in the stack frame of the function that declares it, and the lambda outlives that frame. So when a lambda captures a `var`, Kotlin moves the variable into a small object on the heap, a `Ref$IntRef`, and both the function and the lambda use its `element` field. That field is the shared field: all four threads reach it through the same lambda. It's a plain field, so `n++` is a read, an add and a write that two threads can interleave, and increments get lost. Java would have refused to compile the capture. I'd stop sharing: have each thread or task count its own work and add the counts up at the end. If a live shared count is needed, I'd capture a `val` holding a `LongAdder` or `AtomicLong` instead of a `var`."
    },
    "deeper": {
        "minutes": 10,
        "body": "`javap -v` shows how `invokedynamic` is wired. Each lambda site has an entry in the class's `BootstrapMethods` table pointing at `LambdaMetafactory.metafactory`, with three arguments: the erased method type of `invoke`, `(Ljava/lang/Object;)Ljava/lang/Object;`, a handle to the private static method holding the body, and the instantiated type, `(Ljava/lang/Long;)Ljava/lang/Long;` for a `(Long) -> Long`. The erased signature is why a call through `Function1` boxes: `invoke` takes and returns `Object`.\n\nKotlin 2.0's switch to `invokedynamic` changed three visible things, according to its release notes. These lambdas aren't serializable, the experimental `reflect()` API doesn't support them, and `toString()` prints the hidden class name, something like `LambdaShapesKt$$Lambda/0x...@1b6d3586`, instead of a readable description of the function type. A test or log that matched on the old text breaks after the upgrade. Annotate a single lambda with `@JvmSerializableLambda`, or compile the module with `-Xlambdas=class`, to get the old class-per-lambda behaviour.\n\nSAM conversions went to `invokedynamic` earlier, in Kotlin 1.5. A SAM conversion turns a lambda into an instance of an interface with a Single Abstract Method: a Kotlin lambda passed where Java expects a `Runnable` or `Comparator`, or a lambda for your own `fun interface`:\n\n```kotlin\nfun interface Rest { fun minutesFor(grams: Int): Int }\n\nval flat = Rest { 10 }                       // a SAM conversion: invokedynamic, no class file\nval task = Runnable { println(\"timer done\") } // the same for a Java interface\n```\n\n```java\n@FunctionalInterface\ninterface Rest { int minutesFor(int grams); }\n\nRest flat = grams -> 10;                      // Java lambdas have always worked this way\nRunnable task = () -> System.out.println(\"timer done\");\n```\n\nA `fun interface` is worth using when a function type needs a name in a public API, or when Java callers will implement it, since Java code can't write a lambda for `Function1` as naturally as for an interface named after its job."
    },
    "sources": [
        {"title": "Higher-order functions and lambdas (Kotlin docs)", "url": "https://kotlinlang.org/docs/lambdas.html"},
        {"title": "What's new in Kotlin 2.0.0: generation of lambda functions using invokedynamic", "url": "https://kotlinlang.org/docs/whatsnew20.html"},
        {"title": "Ref.java (Kotlin stdlib source)", "url": "https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/runtime/kotlin/jvm/internal/Ref.java"},
        {"title": "Lambda Expressions (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html"}
    ]
}

out = ROOT / "content/lessons/fp-02.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
