import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l01.demo"


def kdemo(name, alt=True):
    path = f"{LAB}/demo/kotlin/workbench/functional/l01/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(name + "Java")
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l01/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def box(x, y, w, label, cls="box", h=38, tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + h // 2 + 5}" text-anchor="middle">{label}</text>')


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Functional core, imperative shell. The shell reads the date, the cupboard and the amount the recipe needs, '
    'passes them as plain values to the pure core, gramsToBuy and shoppingLine, and then performs the effects: write the shopping line and return the grams.">'
    '<rect class="box-dim" x="10" y="10" width="660" height="280" rx="8"/>'
    '<text class="t-s t-m" x="340" y="34" text-anchor="middle">imperative shell: the cook. Reads the inputs, does the errands, almost no branches</text>'
    '<text class="t-s t-m" x="115" y="66" text-anchor="middle">read the inputs</text>'
    + box(30, 78, 170, "LocalDate.now(clock)")
    + box(30, 138, 170, "Cupboard.flour")
    + box(30, 198, 170, "neededGrams (recipe)")
    + '<rect class="box-a" x="250" y="88" width="190" height="122" rx="8"/>'
    '<text class="t" x="345" y="116" text-anchor="middle">functional core</text>'
    '<text class="t-s t-code" x="345" y="146" text-anchor="middle">gramsToBuy(...)</text>'
    '<text class="t-s t-code" x="345" y="170" text-anchor="middle">shoppingLine(...)</text>'
    '<text class="t-s t-m" x="345" y="194" text-anchor="middle">the card: values in, values out</text>'
    '<text class="t-s t-m" x="570" y="66" text-anchor="middle">do the effects</text>'
    + box(490, 98, 160, "ShoppingList.add", "box-b")
    + box(490, 158, 160, "return grams", "box-b")
    + '<line class="ln-a" x1="200" y1="97" x2="246" y2="126" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="157" x2="246" y2="150" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="217" x2="246" y2="176" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="440" y1="130" x2="486" y2="117" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="440" y1="168" x2="486" y2="177" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="345" y="236" text-anchor="middle">many unit tests with plain values</text>'
    '<text class="t-s t-m" x="340" y="272" text-anchor="middle">a couple of tests with Clock.fixed cover the shell</text>'
    '</svg>'
)

OPENING = """Picture a recipe card for pancakes: 200 g of flour, two eggs, 300 ml of milk, makes eight. Follow it with the same ingredients and you get the same eight pancakes. The kitchen ends up the way you found it, apart from the pancakes and a pan to wash.

Now picture a cook with the same card who glances at the clock and makes half a batch because it's late. They weigh the flour on a scale someone left set to ounces, and eat a spoonful of batter on the way. Same card, same ingredients, different pancakes.

Code is full of that second cook, and it's an easy trap: each glance costs one line and looks harmless. The generics track ended by asking how a function can have more inputs than parameters. The cook just answered: the clock and the scale were inputs, and nobody passed them in.

In this lesson, we'll catch a shopping helper reading what it was never given, and define a pure function. Then we'll swap calls for their values, let `if`, `when` and `try` produce values, and push the effects to the edge. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_NAIVE = """static int flourToBuy(int neededGrams) {
    Bag bag = Cupboard.flour;                      // a global: whoever cooked last may have changed it
    LocalDate today = LocalDate.now();             // the calendar
    int usable = today.isAfter(bag.bestBefore()) ? 0 : bag.leftGrams();
    int missing = Math.max(neededGrams - usable, 0);
    int toBuy = (missing + bag.sizeGrams() - 1) / bag.sizeGrams() * bag.sizeGrams();   // whole bags only
    ShoppingList.lines.add(today + ": buy " + toBuy + " g flour");
    return toBuy;
}"""
K_NAIVE = """fun flourToBuy(neededGrams: Int): Int {
    val bag = Cupboard.flour                       // a global: whoever cooked last may have changed it
    val today = LocalDate.now()                    // the calendar
    val usable = if (today.isAfter(bag.bestBefore)) 0 else bag.leftGrams
    val missing = maxOf(neededGrams - usable, 0)
    val toBuy = (missing + bag.sizeGrams - 1) / bag.sizeGrams * bag.sizeGrams   // whole bags only
    ShoppingList.lines.add("$today: buy $toBuy g flour")
    return toBuy
}"""

S0 = """Here's a small piece of a recipe app. Before you cook, it looks in the cupboard and tells you how much flour to buy. A `Bag` holds three facts: the size the shop sells (1 kg), how much is left at home, and the best-before date printed on it. The shop only sells whole bags, so the helper rounds up, and then it writes a line on the shopping list:

""" + pair(J_NAIVE, K_NAIVE) + """

Read it top to bottom. First it takes the bag from `Cupboard`, a global object that any part of the program can change. Then it asks the calendar for today's date, and a bag past its best-before date counts as empty. The missing grams round up to whole bags. The one tricky line, `(missing + size - 1) / size * size`, is integer division that rounds up instead of down. Finally it writes the line and returns the grams.

The signature says it takes the grams you need and returns the grams to buy. That isn't the whole truth. It also takes today's date and whatever bag is in the cupboard at that moment, and it writes to the shopping list. Those two inputs and that one output are hidden. You can't see them where the function is called, and a test can't pass them in.

So every test of it is fragile. Say the bag holds 700 g and is good until 31 March. `assertEquals(1000, flourToBuy(1500))` passes all through March. On the first of April it fails with 2000, and nobody touched the code. The test didn't break. Its flour went off.

Order matters too. Another test puts a fresh bag into `Cupboard.flour` and forgets to take it out. Now your test fails only when JUnit, the tool that runs the tests, happens to run that one first. And every call writes a real line on the shopping list, so a test that wants to check the line has to go and read the global list.

The usual fixes add machinery. You pass in a `Clock` and use `Clock.fixed(...)` in tests, a clock that always says the same time. You reset `Cupboard` in a `@BeforeEach` method, which JUnit runs before every test. You clear the list after every test. All of that works. All of it exists only because the function reaches outside its own parameters.

There's a simpler fix. Make every input a parameter, and make the return value the only output. That kind of function has a name, and the rest of this lesson shows why it pays off so much."""

# ---------------------------------------------------------------- section 1
J_PURE = """static int gramsToBuy(int neededGrams, Bag bag, LocalDate today) {
    int usable = today.isAfter(bag.bestBefore()) ? 0 : bag.leftGrams();
    int missing = Math.max(neededGrams - usable, 0);
    int bags = (missing + bag.sizeGrams() - 1) / bag.sizeGrams();
    return bags * bag.sizeGrams();
}"""
K_PURE = """fun gramsToBuy(neededGrams: Int, bag: Bag, today: LocalDate): Int {
    val usable = if (today.isAfter(bag.bestBefore)) 0 else bag.leftGrams
    val missing = maxOf(neededGrams - usable, 0)
    val bags = (missing + bag.sizeGrams - 1) / bag.sizeGrams
    return bags * bag.sizeGrams
}"""

S1 = """A **pure function** follows two rules. Its result depends only on its arguments, so two calls with the same values give the same answer. And calling it changes nothing outside it. Break either rule and the function is impure.

That's the recipe card from the opening. The same ingredients give the same pancakes, and following the card leaves the kitchen as you found it. The second cook broke both rules: they used things that weren't on the card, and they changed the kitchen on the way.

Anything a call does besides hand back its value is a **side effect**: writing a file, sending a message, printing, changing a field or the contents of a parameter. Eating the batter was a side effect, and so is writing the shopping list.

The first rule has a half that people forget. Reading something that can change also breaks purity: `LocalDate.now()`, `Random.nextInt()`, a mutable global like `Cupboard`, or a cache (a store of saved answers) that some other code fills. These are **hidden inputs**. The answer depends on them, so the same arguments can give different answers. The clock and the scale left on ounces were the cook's hidden inputs.

Here is the shopping rule with every input moved into the parameter list:

""" + pair(J_PURE, K_PURE) + """

Two things changed. The bag and the date arrive as arguments, so nothing is read from outside. And nothing is written: the grams come back as the return value, and that's all. `Bag` is a record in Java and a data class with `val`s in Kotlin, so it's a plain value that can't change under you. Now the test:

""" + pair("assertEquals(2000, gramsToBuy(1500, bag, LocalDate.of(2026, 4, 1)));",
           "assertEquals(2000, gramsToBuy(1500, bag, LocalDate.of(2026, 4, 1)))") + """

No fake clock, no reset, no clean-up. You can test 31 March and 1 April in two lines, run the tests in any order, and run them on eight threads at once. (A thread is one path of work running through a program, and several can run at the same moment.) Nothing is shared, so nothing can race, which means no two threads can change the same data at once and get a wrong answer.

**A function that reads only its arguments is tested with plain values. Pass everything in.**

The recipe card picture breaks in one place, and it's worth knowing where. A real recipe never gives exactly the same pancakes twice, because eggs and pans differ. A pure function gives exactly the same value every time, to the last digit. That's stronger than any kitchen.

Purity is a property of what a function does, not of the language. Kotlin has no `pure` keyword, and neither compiler checks it. The clues are in the signature: plain value parameters, a real return type instead of `Unit` or `void`, and no clock, file or logger among the things it uses.

So the rule is easy to test now. Pure functions also let you do things with the code itself that the first version would not survive."""

# ---------------------------------------------------------------- section 2
J_SWAP = """int total = batterGrams(8) + batterGrams(8);
int b = batterGrams(8);
int same = b + b;                          // always equal to total"""
K_SWAP = """val total = batterGrams(8) + batterGrams(8)
val b = batterGrams(8)
val same = b + b                           // always equal to total"""
J_EGG = """String e = fridge.takeEgg();
List<String> eggs = List.of(e, e);                                   // one egg
List<String> inlined = List.of(fridge.takeEgg(), fridge.takeEgg());  // two eggs"""
K_EGG = """val e = fridge.takeEgg()
val eggs = listOf(e, e)                                              // one egg
val inlined = listOf(fridge.takeEgg(), fridge.takeEgg())             // two eggs"""

S2 = """Pure functions have a property with a long name and a simple meaning. **Referential transparency** means you can replace a call with the value it returns, and the program does exactly the same thing.

In the kitchen, it's a bowl of batter. If you've already made batter from the card, you can use that bowl instead of making it again, and nobody can tell. Here's the same move in code. `batterGrams(pancakes)` says how much batter a batch needs, 55 g a pancake:

""" + pair(J_SWAP, K_SWAP) + """

You make this kind of change every day without thinking about it: extract a variable, inline a variable, move a call out of a loop. It's only safe when the call is pure. Try the same move on a call with a side effect. `fridge.takeEgg()` takes one egg out of the fridge and returns its label:

""" + pair(J_EGG, K_EGG) + """

The demo below runs both halves and counts the eggs that leave the fridge:

```text
batterGrams(8) + batterGrams(8) = 880
val b = batterGrams(8); b + b   = 880
val e = takeEgg(); listOf(e, e)  -> [egg_1, egg_1], eggs taken: 1
listOf(takeEgg(), takeEgg())     -> [egg_1, egg_2], eggs taken: 2
```

The batter came to 880 g both ways. Inlining the egg variable, though, took a second egg out of the fridge. Nothing in the syntax warned you. Both versions look like the same expression, and only what you know about `takeEgg` tells them apart.

That's what purity buys you in practice: the call site tells you everything. You can reorder pure calls, because no call depends on another one's effects. You can cache the result, because the same arguments always give the same answer (lesson 3 of this track builds `memoize` on exactly this). You can retry after a failure, because a second call can't do anything twice. You can run it on many threads at once, because it touches nothing shared.

With an impure function, each of those moves first needs you to read its body, and often the bodies of everything it calls.

**A pure call can be swapped for its value. An impure call can't. Know which one you hold before you refactor.**

Pure code works with values rather than changing variables, and Kotlin has a feature that pushes you that way."""

# ---------------------------------------------------------------- section 3
J_STMT = """Difficulty level;
if (stars == 1) level = Difficulty.EASY;
else if (stars == 2) level = Difficulty.MEDIUM;
else level = Difficulty.HARD;"""
K_STMT = """var level: Difficulty
if (stars == 1) level = Difficulty.EASY
else if (stars == 2) level = Difficulty.MEDIUM
else level = Difficulty.HARD"""
J_EXPR = """Difficulty level = switch (stars) {          // switch expression, JDK 14
    case 1 -> Difficulty.EASY;
    case 2 -> Difficulty.MEDIUM;
    default -> Difficulty.HARD;
};"""
K_EXPR = """val level = when (stars) {
    1 -> Difficulty.EASY
    2 -> Difficulty.MEDIUM
    else -> Difficulty.HARD
}"""

S3 = """Pure code computes values instead of changing variables. Kotlin helps more than Java here, because `if`, `when` and `try` are **expressions**: code that produces a value you can assign or return. In Java, `if` and `try` are **statements**: they do something, and produce nothing.

Our recipe book marks each recipe with one, two or three stars for how hard it is. Here's the habit both languages allow, a variable declared first and assigned in branches:

""" + pair(J_STMT, K_STMT) + """

And this is the expression form:

""" + pair(J_EXPR, K_EXPR) + """

The expression version is a `val`, so nothing can reassign it later. It also can't be left without a value. Delete the `else` branch and Kotlin refuses to compile it: `'when' expression must be exhaustive. Add an 'else' branch.`

When the subject is an enum or a sealed type (a type whose subtypes are all listed in one place), you can name every case and leave out `else`. Then adding a new case to the type breaks every `when` that doesn't handle it yet, which is exactly the reminder you want.

`try` works the same way in Kotlin. Its value is the last expression of the `try` block, or of the `catch` block that ran. Here it reads a weight that someone typed into the app:

""" + pair("""int grams;
try { grams = Integer.parseInt(raw); } catch (NumberFormatException e) { grams = -1; }""",
           """val grams = try { raw.toInt() } catch (e: NumberFormatException) { -1 }""") + """

Java has no `try` expression, so you assign in each block or return from each block. The demo feeds it `"25O"`, typed with a letter O where the zero should be, and gets -1. (Returning -1 for bad input only keeps the example short. Lesson 7 of this track shows better ways to return a failure.)

You can't write a whole program as expressions, and you shouldn't try. Inside the rules, though, expressions push you toward pure code: each line computes one value from the values before it. The rest, reading the cupboard and writing the list, still has to live somewhere. That's the last step."""

# ---------------------------------------------------------------- section 4
J_SHELL = """static int flourToBuy(int neededGrams, Clock clock) {
    Bag bag = Cupboard.flour;                              // 1. gather the inputs
    LocalDate today = LocalDate.now(clock);
    int grams = gramsToBuy(neededGrams, bag, today);       // 2. decide, purely
    ShoppingList.lines.add(shoppingLine("flour", grams, today));   // 3. do the effect
    return grams;
}"""
K_SHELL = """fun flourToBuy(neededGrams: Int, clock: Clock): Int {
    val bag = Cupboard.flour                               // 1. gather the inputs
    val today = LocalDate.now(clock)
    val grams = gramsToBuy(neededGrams, bag, today)        // 2. decide, purely
    ShoppingList.lines.add(shoppingLine("flour", grams, today))    // 3. do the effect
    return grams
}"""

S4 = """A real app can't be pure. It has to read the calendar, look in the cupboard and write the shopping list. Pure functions don't remove those effects. They let you push them to the edges.

Think of the kitchen again. The recipe card decides: how much flour, how long in the pan. The cook does the errands: opens the cupboard, reads the date on the bag, writes the list. Keep the card free of errands, and keep the cook free of decisions.

The shape has a name, **functional core, imperative shell**, usually credited to Gary Bernhardt's Destroy All Software screencasts. The core holds the decisions and is pure. The shell does the input and output, and stays so thin that it has almost no decisions left in it. (Imperative code works by doing things in order: read this, then write that.)

For the shopping helper, the shell is three steps:

""" + pair(J_SHELL, K_SHELL) + """

Look at `shoppingLine`. Deciding what to write is a decision, so it moves into the core as a pure function that returns a `String`. Writing the line is an effect, so it stays in the shell.

The payoff shows in where the tests go. The core has all the branches: the best-before date, the never-below-zero rule, the rounding, and every rule you add later. It gets many fast unit tests with plain values. The shell has no branches, so two tests with `Clock.fixed` cover it. You still need a fixed clock, but in two tests instead of twenty.

**Decide in the core, act in the shell. Keep the shell too thin to hide a bug.**

This is the target shape for the whole track. Function values, higher-order functions, collection pipelines and errors as values are all tools for making the core bigger and the shell smaller. The last lesson of the track puts a whole program into this shape.

The shape has a limit, and it's best said plainly. A pure core can't do anything on its own: no file, no screen, no network. The shell still reads and writes, it's still the part that's hard to test, and no compiler checks that the core stayed pure. Purity makes a rule easy to test. It doesn't make the rule right.

So far, every rule was a function we called by name. Rules can also be things you hold, store and hand to other code, and that's where the track goes next."""

ASIDE4 = {
    "title": "Isn't passing in a Clock enough?",
    "body": "It's a good first step, and it's where most people stop. A `ShoppingHelper(clock, cupboard, list)` class with a `flourFor(grams)` method can be tested, but it isn't pure. Each call still reads a clock and a cupboard and writes a list, so every test needs fakes, and two calls with the same grams can still disagree. Passing the dependencies in moves the hidden inputs into the constructor; it doesn't remove them. Go one step further: let the helper gather the inputs and pass them as values to `gramsToBuy(neededGrams, bag, today)`, and keep the fakes for the two or three tests of the helper itself.",
}

L = {
    "id": "fp-01",
    "title": "Pure functions: the idea everything else builds on",
    "minutes": 35,
    "goal": "By the end you can tell a pure function from an impure one, name its hidden inputs and side effects, and pull the pure rule out of code that reads the calendar and a global so it can be tested with plain values.",
    "opening": OPENING,
    "warmup": {
        "q": "`flourToBuy(1500)` reads a global `Cupboard.flour` and `LocalDate.now()`. A test calls it and expects `1000`. It passes on your laptop all through March. What can make the same test fail with no code change?",
        "options": [
            "Nothing: same argument, same answer",
            "Only a JDK upgrade that changes how integers divide",
            "The date the build runs, and the order the tests run in",
            "Only running the test class twice in a row"
        ],
        "answer": 2,
        "why": "The function has two inputs that are not in its parameter list: the calendar and the global cupboard. The test controls only the argument. On the first of April the bag in the cupboard is past its best-before date, so it stops counting and the answer doubles. After a test that put a new bag in the cupboard and never took it out, the answer changes again. A function whose every input is a parameter can't fail this way, and the first section takes both cases slowly."
    },
    "sections": [
        {
            "h": "A shopping helper with three inputs, and only one is a parameter",
            "body": S0,
            "try": {
                "title": "Two tests, one cupboard",
                "minutes": 3,
                "steps": [
                    "Open `OrderDependentTests.kt` (or its Java twin, `OrderDependentTestsJava.java`). It runs two little tests that share one global, `Cupboard.flourLeft`. Both pass in the order they are written. Predict what happens if you swap the order.",
                    "Run it with the command below. Then run it again with `-Pargs=reverse` added.",
                    "Find the line that makes `halfBagTest` fail. Notice that it isn't in `halfBagTest`."
                ],
                "code": kdemo("OrderDependentTests"),
                "expect": "In the written order both tests print `pass`. Reversed, `newBag` still passes, but `halfBag` prints `FAIL (expected 800, got 0)`. The cause is in the other test, which set `Cupboard.flourLeft` to 1,700 g and never put it back. `flourMissing` can't protect itself, because what's in the cupboard is not one of its inputs."
            }
        },
        {
            "h": "What makes a function pure: it depends only on its arguments and changes nothing",
            "body": S1,
            "try": {
                "title": "Pure or not?",
                "minutes": 3,
                "steps": [
                    "For each function, decide pure or impure. For the impure ones, name the hidden input or the side effect. Write your answers down before you read the expected result.",
                    "1: `fun gramsFor(cups: Int) = cups * FLOUR_GRAMS_PER_CUP`, where `FLOUR_GRAMS_PER_CUP` is a `const val`.",
                    "2: `fun isFresh(bag: Bag) = !LocalDate.now().isAfter(bag.bestBefore)`.",
                    "3: `fun totalGrams(items: MutableList<Item>): Int { items.sortBy { it.name }; return items.sumOf { it.grams } }`.",
                    "4: `fun newJarLabel() = UUID.randomUUID().toString()`.",
                    "5: `fun shortName(recipe: String) = recipe.take(12)`.",
                    "6: `fun portion(grams: Int): Int { stats.portions++; return grams / 4 }`, where `stats` is a shared object."
                ],
                "expect": "Pure: 1 (a `const val` can never change) and 5. Impure: 2 reads the calendar, a hidden input. 3 sorts the caller's list in place, a side effect the caller can see, even though the total is right. 4 reads a random source, so two calls never agree. 6 returns the right portion but bumps a shared counter on every call, a side effect. If you hesitated on 3, that's the one that bites in practice: the caller's list comes back reordered."
            }
        },
        {
            "h": "Swapping a call for its value: referential transparency",
            "body": S2,
            "try": {
                "title": "One egg or two",
                "minutes": 4,
                "steps": [
                    "Run `ReplaceTheCall` (or `ReplaceTheCallJava`). Before you read the output, predict how many eggs leave the fridge in each half.",
                    "Add `println(\"weighing batter\")` as the first line of `batterGrams` (in Java, `System.out.println(...)`). Predict how many times it prints, then run again.",
                    "Is `batterGrams` still pure? Decide before you read the expected result."
                ],
                "code": kdemo("ReplaceTheCall"),
                "expect": "The pure half prints 880 twice. The egg half takes one egg for `listOf(e, e)`, which holds the same label twice, and two eggs for the inlined version, `[egg_1, egg_2]`. After you add the print, `weighing batter` appears three times: once for `val b`, twice for `batterGrams(8) + batterGrams(8)`. Printing is a side effect, so `batterGrams` is no longer strictly pure: inlining `b` would now change the output. A debug print is harmless, but it is the same mechanism as the second egg."
            }
        },
        {
            "h": "Computing values instead of changing variables: if, when and try as expressions",
            "body": S3,
            "try": {
                "title": "Let the compiler catch the missing branch",
                "minutes": 4,
                "steps": [
                    "Run `Expressions` (or `ExpressionsJava`). Check that the statement and expression versions agree for one, two and three stars.",
                    "In `difficultyOf`, delete the `else ->` line (in Java, the `default ->` line). Run the demo again and read the compiler error.",
                    "Put the line back. In `difficultyStatement`, delete the last `else level = ...` line and run once more. Predict first: will the statement version compile?"
                ],
                "code": kdemo("Expressions"),
                "expect": "Step 2 fails to compile in both languages. Kotlin: `'when' expression must be exhaustive. Add an 'else' branch.` javac: `the switch expression does not cover all possible input values`. Step 3 fails too: Kotlin says `variable 'level' must be initialized.`, javac says `variable level might not have been initialized`. Both compilers track the missing value either way. The expression form reports it where you made the mistake, and leaves you a `val` that nobody can reassign afterwards."
            },
            "refs": [
                {"title": "Conditions and loops: if and when expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html", "kind": "docs"},
                {"title": "Exceptions: try is an expression (Kotlin docs)", "url": "https://kotlinlang.org/docs/exceptions.html", "kind": "docs"},
                {"title": "JEP 361: Switch Expressions", "url": "https://openjdk.org/jeps/361", "kind": "read"}
            ]
        },
        {
            "h": "Keeping the effects at the edge: functional core, imperative shell",
            "body": S4,
            "aside": ASIDE4,
            "figure": {"svg": FIG, "caption": "The shell, like the cook, gathers the inputs, hands them to the pure core as values, and performs whatever the core decided."}
        }
    ],
    "compare": {
        "title": "The same core and shell in Java and Kotlin",
        "java": {
            "title": "Shopping.java",
            "src": "record Bag(int sizeGrams, int leftGrams, LocalDate bestBefore) {}\n\nfinal class Shopping {\n    // core: static, every input is a parameter, the result is the only output\n    static int gramsToBuy(int neededGrams, Bag bag, LocalDate today) {\n        int usable = today.isAfter(bag.bestBefore()) ? 0 : bag.leftGrams();\n        int missing = Math.max(neededGrams - usable, 0);\n        int bags = (missing + bag.sizeGrams() - 1) / bag.sizeGrams();\n        return bags * bag.sizeGrams();\n    }\n\n    static String shoppingLine(String ingredient, int grams, LocalDate today) {\n        return today + \": buy \" + grams + \" g \" + ingredient;\n    }\n\n    // shell: gather, decide, act\n    static int flourToBuy(int neededGrams, Clock clock, List<String> list) {\n        Bag bag = Cupboard.flour;\n        LocalDate today = LocalDate.now(clock);\n        int grams = gramsToBuy(neededGrams, bag, today);\n        list.add(shoppingLine(\"flour\", grams, today));\n        return grams;\n    }\n}"
        },
        "kotlin": {
            "title": "Shopping.kt",
            "src": "data class Bag(val sizeGrams: Int, val leftGrams: Int, val bestBefore: LocalDate)\n\n// core: a top-level function, every input is a parameter, the result is the only output\nfun gramsToBuy(neededGrams: Int, bag: Bag, today: LocalDate): Int {\n    val usable = if (today.isAfter(bag.bestBefore)) 0 else bag.leftGrams\n    val missing = maxOf(neededGrams - usable, 0)\n    val bags = (missing + bag.sizeGrams - 1) / bag.sizeGrams\n    return bags * bag.sizeGrams\n}\n\nfun shoppingLine(ingredient: String, grams: Int, today: LocalDate) = \"$today: buy $grams g $ingredient\"\n\n// shell: gather, decide, act\nfun flourToBuy(neededGrams: Int, clock: Clock, list: MutableList<String>): Int {\n    val bag = Cupboard.flour\n    val today = LocalDate.now(clock)\n    val grams = gramsToBuy(neededGrams, bag, today)\n    list.add(shoppingLine(\"flour\", grams, today))\n    return grams\n}"
        },
        "note": "The idea is the same in both languages, and so is the risk: neither compiler checks purity, so a Java method or a Kotlin function can call `LocalDate.now()` and nothing complains. Kotlin makes pure code a little easier to write. `val` and data classes make values the default, top-level functions need no holder class, and `if`, `when` and `try` produce values, so you rarely need a temporary `var`. Java gets close with records (JDK 16), switch expressions (JDK 14) and the `?:` ternary operator, which covers the simple `if` but not a block with several lines, and `try` stays a statement."
    },
    "worked": {
        "title": "Pull a pure decision out of a 'cook it tonight' button",
        "steps": [
            {
                "say": "The recipe app has a 'cook it tonight' button. Its handler loads the recipe, checks two rules and starts cooking: it sets a timer and marks the ingredients as used. Before reading on, list every hidden input and every side effect in it.",
                "code": "fun cookTonight(recipeName: String) {\n    val recipe = book.load(recipeName)\n    val now = LocalTime.now()\n    if (now.plusMinutes(recipe.minutes.toLong()).isAfter(DINNER_TIME)) { log.warn(\"$recipeName: not enough time\"); return }\n    if (!cupboard.hasAll(recipe.ingredients)) { log.warn(\"$recipeName: something is missing\"); return }\n    timer.start(recipe.minutes)\n    cupboard.use(recipe.ingredients)\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "void cookTonight(String recipeName) {\n    Recipe recipe = book.load(recipeName);\n    LocalTime now = LocalTime.now();\n    if (now.plusMinutes(recipe.minutes()).isAfter(DINNER_TIME)) { log.warn(recipeName + \": not enough time\"); return; }\n    if (!cupboard.hasAll(recipe.ingredients())) { log.warn(recipeName + \": something is missing\"); return; }\n    timer.start(recipe.minutes());\n    cupboard.use(recipe.ingredients());\n}"
            },
            {
                "say": "Hidden inputs: `book.load`, `LocalTime.now()` and `cupboard.hasAll`, which reads what's in the cupboard right now. Side effects: two `log.warn` calls, `timer.start` and `cupboard.use`. The decision is tangled with all of them. 1. Give the decision a type, so the core can return it as a value instead of acting on it.",
                "code": "sealed interface Plan {\n    data class Cook(val recipe: String, val minutes: Int, val ingredients: Set<String>) : Plan\n    data class Skip(val recipe: String, val reason: String) : Plan\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "sealed interface Plan {\n    record Cook(String recipe, int minutes, Set<String> ingredients) implements Plan {}\n    record Skip(String recipe, String reason) implements Plan {}\n}"
            },
            {
                "say": "2. Write the core. The recipe, the time and the cupboard's contents come in as values, and the decision goes out as a value. Self-check: how many tests does it need, and which fakes? (Three, one per branch, and no fakes at all.)",
                "code": "fun decide(recipe: Recipe, now: LocalTime, inCupboard: Set<String>): Plan = when {\n    now.plusMinutes(recipe.minutes.toLong()).isAfter(DINNER_TIME) ->\n        Plan.Skip(recipe.name, \"not enough time\")\n    !inCupboard.containsAll(recipe.ingredients) ->\n        Plan.Skip(recipe.name, \"something is missing\")\n    else -> Plan.Cook(recipe.name, recipe.minutes, recipe.ingredients)\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "static Plan decide(Recipe recipe, LocalTime now, Set<String> inCupboard) {\n    if (now.plusMinutes(recipe.minutes()).isAfter(DINNER_TIME))\n        return new Plan.Skip(recipe.name(), \"not enough time\");\n    if (!inCupboard.containsAll(recipe.ingredients()))\n        return new Plan.Skip(recipe.name(), \"something is missing\");\n    return new Plan.Cook(recipe.name(), recipe.minutes(), recipe.ingredients());\n}"
            },
            {
                "say": "3. The shell gathers, calls the core and carries out the decision. Its `when` has no rules of its own, only one branch per kind of decision, and because `Plan` is sealed the compiler checks that every kind is handled.",
                "code": "fun cookTonight(recipeName: String) {\n    val recipe = book.load(recipeName)                                         // 1. gather\n    when (val plan = decide(recipe, LocalTime.now(clock), cupboard.contents())) {  // 2. decide\n        is Plan.Cook -> {                                                       // 3. act\n            timer.start(plan.minutes)\n            cupboard.use(plan.ingredients)\n        }\n        is Plan.Skip -> log.warn(\"${plan.recipe}: ${plan.reason}\")\n    }\n}",
                "lang": "kotlin",
                "alt_lang": "java",
                "alt_code": "void cookTonight(String recipeName) {\n    Recipe recipe = book.load(recipeName);                                         // 1. gather\n    switch (decide(recipe, LocalTime.now(clock), cupboard.contents())) {           // 2. decide\n        case Plan.Cook c -> {                                                      // 3. act\n            timer.start(c.minutes());\n            cupboard.use(c.ingredients());\n        }\n        case Plan.Skip s -> log.warn(s.recipe() + \": \" + s.reason());\n    }\n}"
            }
        ]
    },
    "lab": {
        "title": "Pull the pure shopping rule out of flourToBuy",
        "minutes": 12,
        "files": ["labs/functional/src/main/kotlin/workbench/functional/l01/Shopping.kt"],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l01.*'",
        "steps": [
            "Open `Shopping.kt`. `Bag` is one bag in the cupboard: the size the shop sells, what's left and its best-before date. `Cupboard` is the global the old helper reads, and `ShoppingList` is the global it writes.",
            "Run the tests. Six fail with `NotImplementedError`. Three already pass: they pin the behaviour of the old `flourToBuy`, which you are about to refactor, and they must stay green.",
            "Write `gramsToBuy` from the rules in its KDoc, the doc comment above it. Use only its three arguments: no `Cupboard`, no clock, no `ShoppingList`. Try to write it with `val`s and one `if` expression.",
            "Write `shoppingLine`. Match the format exactly: `2026-03-02: buy 1000 g flour`.",
            "Rewrite the body of `flourToBuy` as a three-step shell: read `Cupboard.flour` and the date from `clock`, call `gramsToBuy`, add `shoppingLine(...)` to `ShoppingList.lines`, return the grams.",
            "Run the tests until all nine pass. Then open `PureShoppingTest.kt` and notice which tests need the `@BeforeEach` reset and `Clock.fixed`. None of the core tests do."
        ],
        "hints": [
            "`today.isAfter(bag.bestBefore)` is only true from the day after the date, so the bag still counts on the date itself. `!today.isBefore(bag.bestBefore)` would throw it out a day early, and one test checks the date itself.",
            "`maxOf(neededGrams - usable, 0)` stops a full cupboard from asking you to buy a negative amount.",
            "`(missing + size - 1) / size` rounds up in integer arithmetic. `missing / size + 1` looks similar but buys one bag too many when exactly one bag is missing, and the 1,700 g test checks that."
        ],
        "done_when": "All nine tests in `PureShoppingTest` pass, and `flourToBuy` has no arithmetic left in it."
    },
    "drill": {
        "title": "Write a core and its shell from memory",
        "minutes": 5,
        "prompt": "Close this page. Write a pure function `useSoon(jar, today)`: true when the jar is open and its best-before date is at most two days after `today` (or already past). Then write a shell `checkFridge(jarId)` that loads the jar, gets today's date from an injected `Clock`, and adds a note to the fridge door when the jar should be used soon. Finally, write one test of the core. Which of the three pieces needs a fake?",
        "answer": {
            "lang": "kotlin",
            "src": "data class Jar(val id: String, val bestBefore: LocalDate, val open: Boolean)\n\n// core: pure\nfun useSoon(jar: Jar, today: LocalDate): Boolean =\n    jar.open && !jar.bestBefore.isAfter(today.plusDays(2))\n\n// shell: gather, decide, act\nclass FridgeCheck(private val jars: JarRepo, private val door: Notes, private val clock: Clock) {\n    fun checkFridge(jarId: String) {\n        val jar = jars.load(jarId)\n        if (useSoon(jar, LocalDate.now(clock))) door.add(\"use ${jar.id} soon\")\n    }\n}\n\n// a core test: no clock, no repository, no reset\n// assertTrue(useSoon(Jar(\"jam\", LocalDate.of(2026, 3, 4), open = true), LocalDate.of(2026, 3, 2)))\n// Only tests of FridgeCheck need fakes and Clock.fixed.",
            "alt": {
                "lang": "java",
                "src": "record Jar(String id, LocalDate bestBefore, boolean open) {}\n\n// core: pure\nstatic boolean useSoon(Jar jar, LocalDate today) {\n    return jar.open() && !jar.bestBefore().isAfter(today.plusDays(2));\n}\n\n// shell: gather, decide, act\nclass FridgeCheck {\n    private final JarRepo jars;\n    private final Notes door;\n    private final Clock clock;\n    FridgeCheck(JarRepo jars, Notes door, Clock clock) { this.jars = jars; this.door = door; this.clock = clock; }\n\n    void checkFridge(String jarId) {\n        Jar jar = jars.load(jarId);\n        if (useSoon(jar, LocalDate.now(clock))) door.add(\"use \" + jar.id() + \" soon\");\n    }\n}\n\n// a core test: no clock, no repository, no reset\n// assertTrue(useSoon(new Jar(\"jam\", LocalDate.of(2026, 3, 4), true), LocalDate.of(2026, 3, 2)));"
            }
        }
    },
    "recap": [
        "A pure function's result depends only on its arguments, and calling it changes nothing outside it, like a recipe card that gives the same pancakes and leaves the kitchen as it was.",
        "Hidden inputs (the clock, `Random`, a mutable global) break purity just as side effects (writing, printing, changing shared state) do.",
        "Referential transparency: a pure call can be replaced by its value. Only then are extract, inline, cache, retry and parallel calls safe without reading the body.",
        "In Kotlin, `if`, `when` and `try` are expressions. Compute a `val` from them instead of assigning a `var` in branches.",
        "Functional core, imperative shell: decisions in pure functions with many plain-value tests, effects in a thin shell with a few.",
        "The limit: no compiler checks purity, and a pure core does nothing on its own. The shell still reads and writes, and it stays the part that's harder to test."
    ],
    "closing": "We started with two cooks and one recipe card. The shopping helper was the second cook: it read the calendar and the cupboard and wrote the list, so its test passed in March and failed in April. Moving every input into the parameter list gave us `gramsToBuy`, which can be swapped for its value and tested in one line, inside a thin shell that does the errands.\n\nLook in your code for `now()`, `Random` or a global object inside a function that makes a decision. Each one is a hidden input waiting for the wrong day.\n\nNext, we'll hold a function as a value. How do you keep a rule in a list and hand it on?",
    "quiz": [
        {
            "q": "Which of these functions is pure?",
            "options": [
                "`fun grams(cups: Int) = cups * densityCache.current()`, where a background thread refreshes `densityCache`",
                "`fun grams(cups: Int, gramsPerCup: Int) = cups * gramsPerCup`",
                "`fun grams(cups: Int): Int { log.debug(\"grams for $cups\"); return cups * 120 }`",
                "`fun portion(grams: Int) = if (LocalTime.now().hour >= 18) grams * 2 else grams`"
            ],
            "answer": 1,
            "why": "Only the second depends on nothing but its arguments and changes nothing. The first reads a hidden input that another thread changes. The third returns the right number but writes a log line on every call, which is a side effect. The fourth reads the clock, so the same grams give two different portions in one day."
        },
        {
            "q": "`val label = UUID.randomUUID().toString(); val labels = listOf(label, label)`. A teammate inlines the variable: `listOf(UUID.randomUUID().toString(), UUID.randomUUID().toString())`. What changed?",
            "options": [
                "Nothing: inlining a `val` never changes behaviour",
                "Nothing, because `UUID` objects are immutable",
                "The list used to hold one label twice; now it holds two different labels",
                "It no longer compiles, because `randomUUID` can't be called twice in one expression"
            ],
            "answer": 2,
            "why": "`randomUUID` reads a random source, so it isn't referentially transparent: the call and its value are not interchangeable. Inlining is only safe for pure calls. The tempting answer is the first one, which is true only when the call is pure. Immutability of the result doesn't help; the call itself gives a different value each time."
        },
        {
            "q": "What does `g` hold? `val g = try { \"25O\".toInt() } catch (e: NumberFormatException) { -1 } finally { println(\"done\") }` (the string has a letter O at the end)",
            "options": [
                "`-1`, and it prints `done`",
                "`Unit`, because `finally` runs last",
                "It doesn't compile: `try` is a statement",
                "`25`, because `toInt` stops at the first bad character"
            ],
            "answer": 0,
            "why": "In Kotlin, `try` is an expression. Its value is the last expression of the `try` block, or of the `catch` block that ran, here `-1`. `finally` always runs, but it doesn't change the value. `toInt` doesn't stop early: any bad character makes it throw. In Java the same code would need a variable assigned in each block, because Java's `try` is a statement."
        },
        {
            "q": "A meal-planning app has 14 rules and talks to three outside systems: a recipe website, an online shop and a calendar. With functional core, imperative shell, where do most of the unit tests go?",
            "options": [
                "In the shell, with a fake for each outside system",
                "Split evenly between the shell and the core",
                "Neither: only end-to-end tests catch real bugs",
                "In the pure core, called with plain values and no fakes"
            ],
            "answer": 3,
            "why": "The core holds all 14 rules, so it holds almost all the branches, and pure functions are tested with plain values in a line each. The shell gathers inputs and carries out decisions with almost no branches, so a couple of tests with fakes cover it. Testing the rules through the shell is what makes test suites full of fakes."
        },
        {
            "q": "From Race conditions: why count++ lies: eight threads call `gramsToBuy(needed, bag, today)` at the same time, each with its own arguments. `Bag` is a data class with only `val`s of immutable types. What do you need to make the calls thread-safe?",
            "options": [
                "A `synchronized` block around each call",
                "Nothing: the function reads only its arguments and writes nothing shared",
                "An `AtomicReference` to hold the result",
                "A `ThreadLocal` copy of the bag for each thread"
            ],
            "answer": 1,
            "why": "A race needs shared state that at least one thread writes: read-modify-write or check-then-act on something both threads can see. A pure function writes nothing outside itself, and the immutable `Bag` can't change under a reader, so there is nothing to race on. A lock would only make the threads wait in line for no reason.",
            "from": "conc-03"
        }
    ],
    "flashcards": [
        {"front": "What two rules make a function pure?", "back": "Its result depends only on its arguments, and calling it changes nothing outside it: no writing, no printing, no changes to shared state."},
        {"front": "Why does calling `LocalDate.now()` make a function impure?", "back": "The calendar is a hidden input. The same arguments can give a different answer on a different day."},
        {"front": "What is referential transparency?", "back": "You can replace a call with the value it returns without changing what the program does. Only pure calls have it."},
        {"front": "`val e = takeEgg(); listOf(e, e)` vs `listOf(takeEgg(), takeEgg())`: how many eggs does each take?", "back": "One, then two. Inlining a variable is only safe when the call is pure."},
        {"front": "What does Kotlin 2.4 say about `val d = when (stars) { 1 -> EASY; 2 -> MEDIUM }` with an `Int` subject?", "back": "It won't compile: `'when' expression must be exhaustive. Add an 'else' branch.`"},
        {"front": "What is the value of a Kotlin `try { ... } catch (...) { ... }` expression?", "back": "The last expression of the `try` block, or of the `catch` block that ran. `finally` runs but doesn't change the value."},
        {"front": "In functional core, imperative shell, what belongs in the shell?", "back": "Reading inputs (clock, files, globals) and performing effects (writes, calls, logs), with as few decisions as possible."}
    ],
    "terms": [
        {"term": "Pure function", "plain": "A function whose result depends only on its arguments, and whose call changes nothing outside it."},
        {"term": "Side effect", "plain": "Anything a call does besides return its value: writing, sending, printing, changing shared state."},
        {"term": "Hidden input", "plain": "Something a function reads that isn't a parameter: the clock, a random source, a mutable global."},
        {"term": "Referential transparency", "plain": "A call can be replaced by its value without changing the program."},
        {"term": "Expression", "plain": "Code that produces a value. In Kotlin, `if`, `when` and `try` are expressions."},
        {"term": "Functional core, imperative shell", "plain": "A design where pure functions make the decisions and a thin outer layer does the reading and writing."}
    ],
    "explain_back": {
        "prompt": "A teammate says: \"`flourToBuy` is already testable, we pass in a `Clock`.\" In your own words, explain why pulling out `gramsToBuy(neededGrams, bag, today)` is still worth doing.",
        "answer": "Passing in a `Clock` makes the date controllable, but `flourToBuy` still has other hidden inputs and effects. It reads the global cupboard, so every test has to reset it or depend on test order, and it writes to the shopping list, so tests have to clear or read that list. Each test of a rule also needs a fixed clock built just right. If I pull the rule into `gramsToBuy(neededGrams, bag, today)`, every input is a parameter and the grams are the only output. I can test each rule in one line with plain values, in any order, on any number of threads. The old function becomes a three-step shell (read, decide, write), and two tests with `Clock.fixed` are enough for it."
    },
    "deeper": {
        "minutes": 10,
        "body": "Purity has fuzzy edges, and it helps to know where they are.\n\nCreating an object changes the heap, the memory where objects live, but nobody calls a function impure because it creates a `String`. What counts is whether a caller can observe the change. The same goes for a cache inside a function: `memoize` in lesson 3 stores results in a map, yet from the outside the function still returns the same answer for the same arguments, so callers can treat it as pure.\n\nThrowing is the contested case. `require(neededGrams >= 0)` makes a function partial: it has no answer for some inputs. Many people still call it pure, because the same bad input always throws the same way. What hurts is using exceptions for expected outcomes, like a recipe that can't be cooked tonight, because the signature no longer tells you what can come back. Lesson 7 of this track returns those outcomes as values.\n\nKotlin can't check purity, but it can catch the most common bug with pure functions: calling one and dropping the result. Compile with `-Xreturn-value-checker=full` and Kotlin 2.4.21 warns on a call like `plusExtra(grams, 50)` on a line of its own:\n\n```kotlin\nfun plusExtra(grams: Int, extra: Int): Int = grams + extra\n\nfun total(grams: Int): Int {\n    plusExtra(grams, 50)          // warning: unused return value of 'plusExtra'.\n    return grams\n}\n```\n\n```java\nstatic int plusExtra(int grams, int extra) { return grams + extra; }\n\nstatic int total(int grams) {\n    plusExtra(grams, 50);         // javac says nothing\n    return grams;\n}\n```\n\nIn a quick test the warning covered Kotlin functions, including stdlib ones like `map`, but not Java methods: a dropped call to `BigDecimal.add` got no warning. That one stays a code-review catch."
    },
    "sources": [
        {"title": "Conditions and loops (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html"},
        {"title": "Exceptions (Kotlin docs)", "url": "https://kotlinlang.org/docs/exceptions.html"},
        {"title": "Functions: single-expression functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html"},
        {"title": "JEP 361: Switch Expressions", "url": "https://openjdk.org/jeps/361"}
    ]
}

out = ROOT / "content/lessons/fp-01.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
