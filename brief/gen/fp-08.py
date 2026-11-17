import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :functional:demo -Pmain="
PKG = "workbench.functional.l08.demo"


def kdemo(name):
    path = f"{LAB}/demo/kotlin/workbench/functional/l08/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path,
            "alt": jdemo(name + "Java")}


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/functional/l08/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 280" role="img" aria-label="Functional core, imperative shell. The shell, on the outside, reads the clock, the shopping list and the shops, '
    'passes plain values into the pure core in the middle, gets a shopping plan back, then sends the orders and saves the budget book. The core has no arrows to the outside world.">'
    '<rect class="box-dim" x="20" y="20" width="640" height="240" rx="8"/>'
    '<text class="t-s t-m" x="340" y="44" text-anchor="middle">imperative shell: the cook does the errands (I/O, few branches, one wiring test)</text>'
    '<rect class="box" x="40" y="80" width="140" height="40" rx="8"/><text class="t-s" x="110" y="105" text-anchor="middle">clock: today</text>'
    '<rect class="box" x="40" y="140" width="140" height="40" rx="8"/><text class="t-s" x="110" y="165" text-anchor="middle">shopping list</text>'
    '<rect class="box" x="40" y="200" width="140" height="40" rx="8"/><text class="t-s" x="110" y="225" text-anchor="middle">shops</text>'
    '<rect class="box-a" x="250" y="100" width="180" height="110" rx="8"/>'
    '<text class="t" x="340" y="135" text-anchor="middle">functional core</text>'
    '<text class="t-s t-code" x="340" y="160" text-anchor="middle">planShopping(...)</text>'
    '<text class="t-s" x="340" y="185" text-anchor="middle">the card decides</text>'
    '<line class="ln-a" x1="180" y1="100" x2="248" y2="130" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="180" y1="160" x2="248" y2="158" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="180" y1="220" x2="248" y2="186" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="470" y="100" width="170" height="40" rx="8"/><text class="t-s t-code" x="555" y="125" text-anchor="middle">ShoppingPlan</text>'
    '<line class="ln-a" x1="430" y1="140" x2="468" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box" x="470" y="160" width="170" height="36" rx="8"/><text class="t-s" x="555" y="183" text-anchor="middle">send each order</text>'
    '<rect class="box" x="470" y="208" width="170" height="36" rx="8"/><text class="t-s" x="555" y="231" text-anchor="middle">save the budget once</text>'
    '<line class="ln" x1="555" y1="140" x2="555" y2="158" marker-end="url(#arr)"/>'
    '<line class="ln" x1="555" y1="196" x2="555" y2="206" marker-end="url(#arr)"/>'
    '</svg>'
)

OPENING = """Picture a printed recipe book. Nobody edits the page for lemon cake. When the publisher improves the recipe, a new edition comes out, and the copy on your shelf still says what it always said. Now picture the recipe card on the fridge door that the whole household scribbles on. You can never be sure which version you cooked last time.

Data in a program can be either one. A value that never changes can be shared, kept and compared without a second thought. The trap is that Kotlin code can look printed when it isn't: a `val` and a read-only `List` feel frozen, while a list someone else still holds changes underneath.

All track long, the recipe card decided and the cook did the errands, and the last lesson made failures into values too.

In this last lesson, we'll see what `val`, `List` and `copy()` really promise, make new editions cheaply, recurse without running out of stack, and split a whole shopping job into a pure core and a thin shell. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_MENU = """record Menu(String id, List<String> dishes) {}

Menu menu = new Menu("week-7", editing);   // editing is the screen's ArrayList
saved.add(menu);
editing.clear();                           // menu.dishes() is now empty too"""
K_MENU = """data class Menu(val id: String, val dishes: List<String>)

val menu = Menu("week-7", editing)        // editing is the screen's MutableList
saved.add(menu)
editing.clear()                           // menu.dishes is now empty too"""
J_SCALE = """BigDecimal price = new BigDecimal(text).setScale(2, RoundingMode.UNNECESSARY);   // same fix"""
K_SCALE = """val price = BigDecimal(text).setScale(2, RoundingMode.UNNECESSARY)   // one scale for every price"""

S0 = """Here's the app's weekly menu. The planner screen builds a `Menu` from the list of dishes the cook is editing, saves it, and then clears the list for next week:

""" + pair(J_MENU, K_MENU) + """

Everything in `Menu` looks printed: a data class, `val` properties, a read-only `List`. But `val` only means the property can't point at a different list. `List` only means you can't call `add` *through that reference*. Neither one freezes the object behind them, and here both sides hold the same `ArrayList`. A read-only `List` is a shop window: you can't touch the cakes, but the baker behind the glass can.

The Kotlin docs put it plainly: a read-only interface "prevents accidental modification through that interface. By contrast, an immutable collection doesn't allow you to change its elements after creation." And the read-only part is checked only at compile time. On the JVM, `listOf("soup", "pie")` is a `java.util.Arrays$ArrayList`; cast it to `MutableList` and `set(0, "stew")` works, while `add` throws `UnsupportedOperationException`.

Data classes add two traps of their own. `copy()` is shallow: in the docs' words, "it doesn't copy components recursively". A **shallow copy** is a new object whose properties point at the same objects as the original's. `card.copy(recipe = "waffles")` makes a new card but staples the same page of notes to both, so a note added through the copy shows up on the original too.

And `equals` compares every property with its own `equals`. For `BigDecimal`, Java's exact decimal number, that includes the **scale**, the count of digits after the point. `Price("butter", BigDecimal("2.50")) == Price("butter", BigDecimal("2.5"))` is `false`, although `compareTo` says the amounts are equal. Read `2.5` from one shop's website, compute `2.50` yourself, and your "same price as last week?" check says no:

""" + pair(J_SCALE, K_SCALE) + """

`UNNECESSARY` throws if rounding would be needed, so a third decimal fails loudly instead of being rounded away. Storing prices as a whole number of cents avoids the question entirely.

So an **immutable** value, one nobody can change after it's built, needs three layers. Its properties are `val`. Their types are immutable all the way down: `String`, `BigDecimal`, `LocalDate`, other immutable data classes, immutable collections. And nothing mutable leaks in or out, which at a boundary means a copy: `toList()` for a snapshot, or `toImmutableList()` from the next section when you want the type to promise it.

**val and List stop you from changing a value, not everyone else. Copy at the boundary.**

Copying at every change is the price of a printed page. The next section makes that price small."""

# ---------------------------------------------------------------- section 1
J_PERS = """// Java equivalent: no persistent collections in the JDK, so copy the whole list per version
List<String> v1 = List.of("preheat the oven");
List<String> v2 = Stream.concat(v1.stream(), Stream.of("cream butter and sugar")).toList();
List<String> tmp = new ArrayList<>(v2);
tmp.addAll(List.of("beat in the eggs", "fold in the flour"));
List<String> v3 = List.copyOf(tmp);"""
K_PERS = """val v1 = persistentListOf("preheat the oven")
val v2 = v1.adding("cream butter and sugar")             // a new list; v1 is untouched
val v3 = v2.addingAll(listOf("beat in the eggs", "fold in the flour"))
val v4 = v3.mutate { it.removeAt(0); it += "bake for 25 minutes" }   // several changes in one go"""

S1 = """Immutable values pay you back in three ways. You can share them between threads (paths of work that run at the same time) with no lock, because nobody can write ("Don't share: immutability, confinement, ThreadLocal" in the first track). You can keep the old version, the way an old edition stays on the shelf. And a test can hold the "before" and "after" side by side. The price is that every change makes a new value. Copying a whole list to add one step is what Java does in the Try it, and it costs time and memory in proportion to the list's size, on every change.

**Persistent collections** avoid most of that copy. A new version shares most of its insides with the old one, the way a new edition of a cookbook reuses most of its pages and reprints only the ones that changed. Adding a step builds a few new pieces of the list's inner tree and reuses the rest. The library is `kotlinx-collections-immutable`, version 0.5.2 in the lab. Its README still says "the library is experimental and the API is subject to change", so treat it as a dependency that hasn't reached 1.0. `ImmutableList` promises that nobody can change the list; `PersistentList` adds the operations that return a new version:

""" + pair(J_PERS, K_PERS) + """

The picture breaks in one place. A publisher prints a whole new book, while a persistent list really does share its pages between versions, in memory. That sharing is safe only because no version can ever change.

Notice the names. Until 0.5.0 these methods were called `add`, `remove`, `put` and `set`, like the changing methods on `MutableList`. That invited a quiet bug: `budget.entries.add(entry)` as a statement builds a new list and throws it away, and the budget never changes. Version 0.5.0 renamed the copy-returning methods to `adding`, `removing`, `putting`, `replacingAt` and `removingAt`. It follows a naming proposal (KEEP-0459, still a draft) where a verb like `add` changes the object and a participle like `adding` returns a copy, as `sorted()` does next to `sort()`. The old names still compile, with a warning: `'fun add(element: String): PersistentList<String>' is deprecated. Use adding() instead.`

**A persistent collection makes a new version and leaves the old one alone. Keep the result, or the change is lost.**

In the lab, the household budget book is a data class around a `PersistentList<Entry>`, and posting returns a new budget with `copy(entries = entries.addingAll(...))`. The budget you posted to is still there, unchanged, for the test to compare against.

Immutable data changes how functional code loops, too. Instead of a `var` that changes, a function often calls itself."""

# ---------------------------------------------------------------- section 2
J_SUM = """// Java has no tailrec: write the loop the Kotlin compiler would write
static long sumTo(long n) {
    long acc = 0;
    while (n > 0) { acc += n; n--; }
    return acc;
}"""
K_SUM = """tailrec fun sumTo(n: Long, acc: Long = 0): Long = if (n == 0L) acc else sumTo(n - 1, acc + n)
// sumTo(1_000_000) == 500000500000, no stack growth"""

S2 = """Functional code often recurses where Java code loops: a function calls itself on a smaller problem. On the JVM that has a hard limit. Every call takes a **stack frame**, a slot that holds the call's local variables until it returns, on the thread's stack: the memory that holds the calls in progress. The stack has room for only so many. The JVM never removes a frame early, even for the last call in a method. Sum the numbers 1 to 1,000,000 by recursion and you get a `StackOverflowError`, in both languages. In Java it overflows even when the recursive call is the last thing the method does.

Kotlin's `tailrec` moves the fix into the compiler. "When a function is marked with the `tailrec` modifier and meets the required formal conditions, the compiler optimizes out the recursion, leaving behind a fast and efficient loop based version instead." A **tail call** is a call that is the very last thing a function does. The trick is an **accumulator**, an extra parameter that carries the result so far. The work still pending becomes an argument, so the recursive call can come last:

""" + pair(J_SUM, K_SUM) + """

`javap -c`, the JDK tool that prints a class's bytecode, shows what the compiler did. `sumTo` stores the new values into its own parameter slots and ends with `goto 0`, a jump back to its first instruction. There's no `invokestatic sumTo` left. The conditions are strict. The function must call itself as its very last operation, not inside `try`, `catch` or `finally`, and it can't be `open`. Get it wrong and the compiler takes your word for it, mutters a warning and compiles ordinary recursion anyway: `A function is marked as tail-recursive but no tail calls are found.` and `Recursive call is not a tail call.` The code still overflows, so read the warnings.

Here's recursion that fits `tailrec` naturally. A sourdough starter is fed from a spoonful of another starter, which came from another, and friends pass them on for years. Walking back to the very first one makes one call per generation, always as the last thing the function does, so the demo walks 100,000 generations without growing the stack.

Some recursion has no tail form. Counting the parts of a recipe made of parts, each made of more parts, makes several recursive calls per part. `DeepRecursiveFunction` from the standard library runs such a function with its "stack" on the heap, the big memory area where objects live, using coroutine machinery. In the Try it, it counts a recipe nested 100,001 levels deep, where the same code as a plain function overflows.

Most of the time you need neither. Adding up a basket or a budget is a `fold` or a `sumOf` (the collections lesson), which says what it means in one line and compiles to the same kind of loop. Recursion that walks a list with `first()` and `drop(1)` is worse than either, because `drop(1)` copies the rest of the list at every step.

**Reach for fold or sumOf first. Keep tailrec for problems that are recursive by nature, and read its warnings.**

We now have every piece of the track: pure functions, function values, collections, errors as values and data that can't change. The last section puts them into one shape."""

# ---------------------------------------------------------------- section 3
J_SIG = """static ShoppingPlan planShopping(List<Item> items, Map<String, Shop> shops, LocalDate today)"""
K_SIG = """fun planShopping(items: List<Item>, shops: Map<String, Shop>, today: LocalDate): ShoppingPlan"""
J_RUN = """ShoppingPlan run() {
    LocalDate today = LocalDate.now(clock);                                        // 1. read
    ShoppingPlan plan = planShopping(store.shoppingList(), store.shops(), today);  // 2. decide
    plan.orders().forEach(shopApi::send);                                          // 3. act
    store.saveBudget(posting(store.loadBudget(), plan.orders(), "shopping-" + today));
    return plan;
}"""
K_RUN = """fun run(): ShoppingPlan {
    val today = LocalDate.now(clock)                                         // 1. read
    val plan = planShopping(store.shoppingList(), store.shops(), today)      // 2. decide
    plan.orders.forEach(shopApi::send)                                       // 3. act
    store.saveBudget(store.loadBudget().posting(plan.orders, "shopping-$today"))
    return plan
}"""

S3 = """Here's the track's last step: put the pieces into one shape. The lab's `LegacyShoppingJob` runs every morning in the recipe app. In one loop it reads the clock and loads the shopping list. It skips crossed-off items, holds back items it's too early to order, adds up a total per shop and works out each shop's member discount. Then it sends the orders, writes each one into the household budget book and saves the book, with `println` in between. It works. But to test one discount rule you need a fake store, a fake shop, a fixed clock, and checks on what the fakes recorded.

The fix is the shape from the first lesson of this track: the recipe card decides and the cook does the errands. Its usual name is **functional core, imperative shell**. The **functional core** is a pure function. It takes plain values, today's date included, and returns a value that describes what should happen:

""" + pair(J_SIG, K_SIG) + """

Everything from this track fits in there. `filterNot`, `partition`, `groupBy` and `sumOf` from the collections lesson do the work. Data classes of `val`s, with prices as `BigDecimal` at scale 2, carry it. Expected outcomes, like an item from a shop the app doesn't know, come back as values in the plan instead of exceptions or log lines, as the errors lesson taught.

The **imperative shell** is the thin outer part, the only code that touches the world, and it has almost no branches:

""" + pair(J_RUN, K_RUN) + """

The tests change shape with the code. The core gets many small tests that build a list, call a function and compare the result with `equals`: no fakes, no clock, milliseconds each. Because the date is a parameter, "an item needed in ten days is still waiting" and "the same item is ordered three days later" are two lines. The shell gets one test with fakes that checks the wiring.

The shell isn't pure and doesn't try to be. The program still does all its errands. What moved is the decisions: each one now lives where you can test it with a value, like a recipe card you can read without lighting the oven.

**Decide in the core, with every input passed in. Let the shell read, call the core and act, and nothing more.**"""

L = {
    "id": "fp-08",
    "title": "Immutable data and a functional core",
    "minutes": 38,
    "goal": "By the end you can tell read-only from immutable, avoid the `copy()` and `BigDecimal` equality traps, choose between `tailrec`, `DeepRecursiveFunction` and `fold`, and split a job into a pure core that decides and a thin shell that does the I/O.",
    "opening": OPENING,
    "warmup": {
        "q": "`data class Menu(val id: String, val dishes: List<String>)`. You build `Menu(\"week-7\", dishes)` from a `MutableList` holding `soup`, and later the caller runs `dishes += \"pie\"`. What does `menu.dishes` show?",
        "options": [
            "`[soup]`, because `val` and `List` make it immutable",
            "`[soup, pie]`, because the menu holds the same list",
            "It throws `UnsupportedOperationException`",
            "It doesn't compile: a `MutableList` can't be passed as a `List`"
        ],
        "answer": 1,
        "why": "`val` only stops the property from pointing at another list, and `List` only stops writes made through that reference. The menu and the caller hold the same `ArrayList`, so the caller's change shows up in the menu. A `MutableList` is a `List`, so passing it compiles. Copy at the boundary (`dishes.toList()`) to take a snapshot."
    },
    "sections": [
        {
            "h": "Read-only is not immutable: what val and List really promise",
            "body": S0,
            "try": {
                "title": "Five ways a printed-looking value changes",
                "minutes": 4,
                "steps": [
                    "Read `ReadOnly.kt` and predict each of the five numbered lines before you run it.",
                    "Run it, then run `ReadOnlyJava.java`, where `List.copyOf` takes a real snapshot.",
                    "In `ReadOnly.kt`, change `Menu(\"week-7\", backing)` to `Menu(\"week-7\", backing.toList())`. Predict lines 1 and 2 now."
                ],
                "code": kdemo("ReadOnly"),
                "expect": "Line 1 shows `[soup, pie]`: the menu sees the caller's add. Line 2 shows `[soup, pie, cake]`: a cast gets past the read-only type. `listOf` is a `java.util.Arrays$ArrayList`, so `set` works and `add` throws. `copy()` shares the notes (`same list: true`), and `Price(2.50) == Price(2.5)` is `false` while `compareTo` says equal. Java's `Collections.unmodifiableList` is only a view too, but `List.copyOf` is a snapshot. With `toList()`, line 1 shows `[soup]`: the menu has its own snapshot. Line 2 now throws `UnsupportedOperationException`, but only by luck: for one element, `toList()` returns `java.util.Collections$SingletonList`. From two elements up it returns a plain `ArrayList`, and the cast-and-add would work. The read-only type is the only promise you get."
            },
            "refs": [{"title": "Collections overview: read-only and mutable (Kotlin docs)", "url": "https://kotlinlang.org/docs/collections-overview.html", "kind": "docs"}]
        },
        {
            "h": "Persistent collections: a new edition instead of crossing out",
            "body": S1,
            "try": {
                "title": "Four editions of one recipe",
                "minutes": 3,
                "steps": [
                    "Run `Persistent.kt`. Predict what `v1` and `v3` print at the end.",
                    "Uncomment `v1.add(\"lost\")` and run again. Read the build warning and the last line.",
                    "Run `PersistentJava.java` and count how many times it copies the whole list."
                ],
                "code": kdemo("Persistent"),
                "expect": "`v1` stays `[preheat the oven]` and `v3` stays four steps long, even after `v4` is built from it with `mutate`. `v1` is a `SmallPersistentVector`. With `v1.add(\"lost\")`, the build warns `'fun add(element: String): PersistentList<String>' is deprecated. Use adding() instead.` and the last line still shows `[preheat the oven]`: `add` returned a new list that nobody kept. The Java version copies the full list for every version it makes."
            },
            "refs": [{"title": "kotlinx.collections.immutable (GitHub)", "url": "https://github.com/Kotlin/kotlinx.collections.immutable", "kind": "read"}]
        },
        {
            "h": "Recursion: tailrec is a loop, everything else uses the stack",
            "body": S2,
            "try": {
                "title": "Watch tailrec become a goto",
                "minutes": 4,
                "steps": [
                    "Run `Recursion.kt`. Predict which lines print a number and which print `StackOverflowError`.",
                    "From `labs/`, run `javap -c -p -cp functional/build/classes/kotlin/demo workbench.functional.l08.demo.RecursionKt` and find `sumTo` and `sumNaive`. Which one calls itself?",
                    "Add `tailrec` in front of `fun sumNaive` and run again. Read the warnings in the build output.",
                    "Run `RecursionJava.java`. Does `sumTail`, with its call in tail position, survive?"
                ],
                "code": kdemo("Recursion"),
                "expect": "`sumTo` and `fold` both print `500000500000`; `sumNaive` overflows; `originOf` walks 100,000 starters back to `s1`; `countParts` returns `100001`. In `javap`, `sumTo` ends with `goto 0` and never calls itself, while `sumNaive` has `invokestatic sumNaive`. Marking `sumNaive` as `tailrec` gives `A function is marked as tail-recursive but no tail calls are found.` and `Recursive call is not a tail call.`, and it still overflows. In Java, `sumTail` overflows too: the JVM doesn't remove tail calls, so only a loop helps."
            },
            "refs": [{"title": "Functions: tail recursive functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html", "kind": "docs"}]
        },
        {
            "h": "A functional core decides, a thin shell does the errands",
            "body": S3,
            "figure": {"svg": FIG, "caption": "The shell reads the world, hands plain values to the pure core, and carries out the plan the core returns."},
            "try": {
                "title": "Run a core and its shell",
                "minutes": 3,
                "steps": [
                    "Read `CoreShell.kt`. `decideFridge` is the core and `FridgeJob` is the shell. Predict the two decisions and the one reminder.",
                    "Run it, then run `CoreShellJava.java`.",
                    "Change `now` to one day later, `2026-03-11T09:00:00Z`. Without running anything, which decision changes? Then run it to check."
                ],
                "code": kdemo("CoreShell"),
                "expect": "The core prints `ThrowOut(id=l1)` (4 days old) and `Keep(id=l2, goodFor=PT42H)` (30 hours old, 42 hours left). The shell sends one reminder: `reminder: throw out leftover l1`. One day later, `l2` is still kept with `PT18H` left, and `l1` goes as before. You could check that from the core alone, with no clock and no phone, which is the point."
            }
        }
    ],
    "compare": {
        "title": "Immutable values and a pure core: Java records vs Kotlin data classes",
        "java": {
            "title": "Shopping.java",
            "src": "record Order(String shopId, BigDecimal total, BigDecimal discount, BigDecimal toPay) {}\nrecord Budget(List<Entry> entries) {\n    Budget { entries = List.copyOf(entries); }               // snapshot: nobody can change it later\n    Budget posting(List<Entry> more) {                       // a new version, by copying everything\n        List<Entry> all = new ArrayList<>(entries);\n        all.addAll(more);\n        return new Budget(all);\n    }\n}\n\nstatic BigDecimal discount(BigDecimal total, BigDecimal rate) {   // pure: same inputs, same output\n    return total.multiply(rate).setScale(2, RoundingMode.HALF_EVEN);\n}"
        },
        "kotlin": {
            "title": "Shopping.kt",
            "src": "data class Order(val shopId: String, val total: BigDecimal, val discount: BigDecimal, val toPay: BigDecimal)\ndata class Budget(val entries: PersistentList<Entry>)    // the type promises it can't change\n\nfun Budget.posting(more: List<Entry>): Budget =\n    copy(entries = entries.addingAll(more))              // a new version that shares structure\n\nfun discount(total: BigDecimal, rate: BigDecimal): BigDecimal =   // pure: same inputs, same output\n    (total * rate).setScale(2, RoundingMode.HALF_EVEN)"
        },
        "note": "Both languages give you a value type whose `equals` compares contents, and in both `equals` uses `BigDecimal.equals`, so the scale counts. Kotlin's data class adds `copy()`, which Java records lack (you write \"wither\" methods by hand), and both are shallow. The real difference is in collections. Java's `List.copyOf` makes a snapshot that refuses changes at run time, but every new version copies the whole list. Kotlin's `List` is only a compile-time read-only view, so you need `toList()` for a snapshot, or kotlinx.collections.immutable for a real promise; its `PersistentList` makes new versions cheaply by sharing structure. The pure functions themselves look the same in both languages. Purity is a habit, not a keyword: neither compiler checks it."
    },
    "worked": {
        "title": "Pull the decisions out of a pantry check",
        "steps": [
            {"say": "Each night the app checks the opened jars in the pantry. A jar past its use-by date goes; a jar within two days of it goes on the shopping list, unless it's on there already; anything else waits. Before reading on, label every line as read, decide or act.", "code": "fun checkPantry() {\n    for (jar in pantry.openJars()) {                                         // read\n        val daysLeft = ChronoUnit.DAYS.between(LocalDate.now(), jar.useBy)   // read (the clock!)\n        if (daysLeft < 0) {                                                  // decide\n            pantry.remove(jar.id)                                            // act\n            phone.notify(\"throw out the ${jar.name}\")                        // act\n        } else if (daysLeft <= 2 && !jar.onShoppingList) {                   // decide\n            shoppingList.add(jar.name, \"use within $daysLeft days\")          // act\n        }\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "void checkPantry() {\n    for (Jar jar : pantry.openJars()) {                                          // read\n        long daysLeft = ChronoUnit.DAYS.between(LocalDate.now(), jar.useBy());   // read (the clock!)\n        if (daysLeft < 0) {                                                      // decide\n            pantry.remove(jar.id());                                             // act\n            phone.notify(\"throw out the \" + jar.name());                         // act\n        } else if (daysLeft <= 2 && !jar.onShoppingList()) {                     // decide\n            shoppingList.add(jar.name(), \"use within \" + daysLeft + \" days\");    // act\n        }\n    }\n}"},
            {"say": "1. Name the decisions as values. A sealed type makes the plan explicit and lets the shell's `when` be exhaustive.", "code": "sealed interface JarAction {\n    data class ThrowOut(val jarId: String, val name: String) : JarAction\n    data class Restock(val jarId: String, val name: String, val daysLeft: Long) : JarAction\n    data class Wait(val jarId: String) : JarAction\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "sealed interface JarAction {}\nrecord ThrowOut(String jarId, String name) implements JarAction {}\nrecord Restock(String jarId, String name, long daysLeft) implements JarAction {}\nrecord Wait(String jarId) implements JarAction {}"},
            {"say": "2. Write the core as a pure function. The clock becomes a parameter, `today`, and the result is a list of decisions. Every rule is now testable with one line: `decide(listOf(jar), LocalDate.of(2026, 3, 10))`.", "code": "fun decide(jars: List<Jar>, today: LocalDate): List<JarAction> = jars.map { jar ->\n    val daysLeft = ChronoUnit.DAYS.between(today, jar.useBy)\n    when {\n        daysLeft < 0 -> JarAction.ThrowOut(jar.id, jar.name)\n        daysLeft <= 2 && !jar.onShoppingList -> JarAction.Restock(jar.id, jar.name, daysLeft)\n        else -> JarAction.Wait(jar.id)\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "static List<JarAction> decide(List<Jar> jars, LocalDate today) {\n    return jars.stream().<JarAction>map(jar -> {\n        long daysLeft = ChronoUnit.DAYS.between(today, jar.useBy());\n        if (daysLeft < 0) return new ThrowOut(jar.id(), jar.name());\n        if (daysLeft <= 2 && !jar.onShoppingList()) return new Restock(jar.id(), jar.name(), daysLeft);\n        return new Wait(jar.id());\n    }).toList();\n}"},
            {"say": "3. The shell reads, calls the core and carries out each action with an exhaustive `when`. It has no rules left, so one test with fakes covers it. The many rule tests go against `decide` with plain values.", "code": "fun checkPantry() {\n    val actions = decide(pantry.openJars(), LocalDate.now(clock))   // read, then decide\n    for (action in actions) when (action) {                          // act\n        is JarAction.ThrowOut -> { pantry.remove(action.jarId); phone.notify(\"throw out the ${action.name}\") }\n        is JarAction.Restock -> shoppingList.add(action.name, \"use within ${action.daysLeft} days\")\n        is JarAction.Wait -> Unit\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "void checkPantry() {\n    List<JarAction> actions = decide(pantry.openJars(), LocalDate.now(clock));   // read, then decide\n    for (JarAction action : actions) {                                           // act\n        switch (action) {\n            case ThrowOut t -> { pantry.remove(t.jarId()); phone.notify(\"throw out the \" + t.name()); }\n            case Restock r -> shoppingList.add(r.name(), \"use within \" + r.daysLeft() + \" days\");\n            case Wait w -> { }\n        }\n    }\n}"}
        ]
    },
    "lab": {
        "title": "Split the shopping job into a pure core and a thin shell",
        "minutes": 15,
        "files": [
            f"{LAB}/main/kotlin/workbench/functional/l08/ShoppingCore.kt",
            f"{LAB}/main/kotlin/workbench/functional/l08/ShoppingJob.kt",
            f"{LAB}/main/kotlin/workbench/functional/l08/LegacyShoppingJob.kt",
            f"{LAB}/main/kotlin/workbench/functional/l08/Model.kt"
        ],
        "run": "./gradlew :functional:test --tests 'workbench.functional.l08.*'",
        "steps": [
            "Run the tests. All eight fail. Seven of them call `planShopping` or `posting` with plain values: no fakes and no clock.",
            "Read `LegacyShoppingJob.run` and label each line read, decide or act. `Model.kt` holds the types and needs no changes.",
            "Write `planShopping` in `ShoppingCore.kt` from the rules in its KDoc. `today` is a parameter; don't touch a clock.",
            "Write `Budget.posting` with `copy` and `addingAll`.",
            "Write `ShoppingJob.run` as a thin shell: read, call the core, send each order, post and save the budget once, return the plan.",
            "Run the tests until all eight pass. Then ask: which test would fail if `planShopping` called `LocalDate.now()` instead of using `today`?"
        ],
        "hints": [
            "`partition` splits a list in two in one pass. Use it twice: first known and unknown shops, then items due today and items still waiting.",
            "`sumOf { it.price }` has a `BigDecimal` overload. Round the discount with `setScale(2, RoundingMode.HALF_EVEN)`, or the test's `BigDecimal(\"3.64\")` won't equal your `3.63950`.",
            "`groupBy` keeps first-seen order. `toSortedMap()` sorts the groups by shop id.",
            "In the shell, `plan.orders.forEach(shopApi::send)` and `store.loadBudget().posting(plan.orders, \"shopping-$today\")` cover steps 3 and 4."
        ],
        "done_when": "All eight tests in `FunctionalCoreTest` pass."
    },
    "drill": {
        "title": "tailrec from memory",
        "minutes": 4,
        "prompt": "Close this page. Write `originOf(id, byId)`, which follows `parentId` links from a sourdough starter back to the very first one, as a `tailrec` function. Then write the Java loop. Last, predict: what happens if you add a `log.debug(...)` line after the recursive call?",
        "answer": {
            "lang": "kotlin",
            "src": "tailrec fun originOf(id: String, byId: Map<String, Starter>): String {\n    val parent = byId.getValue(id).parentId ?: return id   // no parent: this is the first starter\n    return originOf(parent, byId)                          // the last thing the function does\n}\n// A log line after the call makes it no longer a tail call: Kotlin warns\n// \"Recursive call is not a tail call.\" and compiles ordinary recursion, which can overflow.",
            "alt": {
                "lang": "java",
                "src": "static String originOf(String id, Map<String, Starter> byId) {\n    String current = id;\n    while (true) {\n        String parent = byId.get(current).parentId();\n        if (parent == null) return current;   // no parent: this is the first starter\n        current = parent;                     // what tailrec's goto does\n    }\n}"
            }
        }
    },
    "recap": [
        "`val` stops reassignment and `List` stops writes through that reference. Neither freezes the object: a read-only view changes when its backing list does.",
        "`copy()` is shallow, and data class `equals` uses `BigDecimal.equals`, which compares the scale. Bring prices to one scale when you read them.",
        "kotlinx.collections.immutable 0.5.2, still marked experimental, gives persistent collections: `adding`, `putting` and `removingAt` return new versions that share structure, and `mutate { }` batches changes.",
        "`tailrec` turns a self-call in tail position into a `goto`. Anywhere else it's only a warning, and the stack still overflows. `DeepRecursiveFunction` handles deep recursion with no tail form, and `fold` is usually simplest.",
        "A functional core decides from plain values, with the clock passed in; a thin shell reads, calls the core and does the I/O. Core tests need no fakes, and the shell needs one wiring test.",
        "The limit: neither compiler checks any of this. Kotlin has no keyword for pure or for deeply immutable, so both stay habits, and the shell stays thin only because you keep it thin."
    ],
    "closing": "We started with a printed recipe book and a fridge card everyone scribbles on. `val` and `List` turned out to be a shop window, `copy()` staples one page to two cards, and persistent collections print new editions that share pages. Then the track met in one job: a pure core that decides and a thin shell for the errands.\n\nLook in your code for a function that reads the clock or a store and also decides something. Pass those values in, and the decision becomes testable.\n\nThat ends this track. Next, we'll turn to design patterns, the named designs programmers reuse. Which of them does a modern language make simpler, starting with the one that allows a single instance?",
    "quiz": [
        {"q": "The planner screen builds `Menu(\"week-9\", editing)` from its `MutableList`, hands the menu to a background task on another thread that prints it, then calls `editing.clear()` for next week. What can the printout show?", "options": ["Always the dishes at the moment the menu was built", "An empty list, or next week's dishes, depending on timing", "`UnsupportedOperationException`, because `List` is read-only", "A compile error, because `dishes` is a `val`"], "answer": 1, "why": "The menu holds the screen's list, not a copy, so clearing and refilling it changes what the menu shows. On another thread it's also a data race. `Menu(\"week-9\", editing.toList())` takes a snapshot at the boundary; `toImmutableList()` puts the promise in the type."},
        {"q": "`data class Price(val item: String, val amount: BigDecimal)`. What is `setOf(Price(\"butter\", BigDecimal(\"2.5\")), Price(\"butter\", BigDecimal(\"2.50\"))).size`?", "options": ["1", "It depends on the JVM", "2", "It throws ArithmeticException"], "answer": 2, "why": "Data class `equals` compares each property with `equals`, and `BigDecimal.equals` treats `2.5` and `2.50` as different because their scales differ. `compareTo` would say they're equal. Bring every price to `setScale(2, ...)` when you read it, or store whole cents."},
        {"q": "`val steps = persistentListOf<String>()`, then `steps.adding(\"preheat\")` and `steps.adding(\"mix\")` as two statements. What is `steps.size`?", "options": ["0", "2", "1", "It doesn't compile, because `steps` is a `val`"], "answer": 0, "why": "`adding` returns a new list and leaves the receiver alone, and both results were thrown away. You need `val v2 = steps.adding(\"preheat\").adding(\"mix\")`. This is the exact bug the 0.5 rename from `add` to `adding` makes easier to spot."},
        {"q": "`tailrec fun depth(s: Starter?): Int = if (s == null) 0 else 1 + depth(s.parent)`, called on a chain of 1,000,000 starters. What happens?", "options": ["It compiles to a loop and returns 1,000,000", "It doesn't compile, because `tailrec` needs an accumulator", "It returns 0", "It compiles with warnings, stays ordinary recursion, and throws StackOverflowError"], "answer": 3, "why": "`1 + depth(...)` still has work to do after the call, so the call isn't in tail position. Kotlin only warns (`A function is marked as tail-recursive but no tail calls are found.`, `Recursive call is not a tail call.`) and compiles normal recursion. Make the pending work an argument: `tailrec fun depth(s: Starter?, acc: Int = 0): Int = if (s == null) acc else depth(s.parent, acc + 1)`."},
        {"q": "From the errors lesson: inside `planShopping`, an item names a shop that isn't in the map. What should the pure core do?", "options": ["`shops.getValue(id)`, and let `NoSuchElementException` stop the run", "`shops[id]!!`", "Return it as a value in the plan, such as an `unknownShops` list or a sealed error", "Log a warning and skip it"], "answer": 2, "why": "An unknown shop is an expected outcome that someone must handle, so it belongs in the result. Throwing would stop the whole morning's shopping for one bad line, `!!` gives a `NullPointerException` with no message, and logging is I/O, which doesn't belong in a pure core and leaves the caller unable to act on it.", "from": "fp-07"}
    ],
    "flashcards": [
        {"front": "Does `val dishes: List<String>` make the list immutable?", "back": "No. `val` stops reassigning the reference and `List` stops writes through it. The list can still change through another reference or a cast."},
        {"front": "Is a data class `copy()` deep or shallow?", "back": "Shallow. Properties are copied as references, so a nested `MutableList` is shared between the original and the copy."},
        {"front": "`Price(\"butter\", BigDecimal(\"2.50\")) == Price(\"butter\", BigDecimal(\"2.5\"))`?", "back": "`false`. Data class equals uses `BigDecimal.equals`, which compares the scale. `compareTo` returns 0."},
        {"front": "What did kotlinx.collections.immutable 0.5 rename, and why?", "back": "The copy-returning methods: `add` to `adding`, `put` to `putting`, `set` to `replacingAt` and so on, so a call whose result is dropped looks wrong. The old names are deprecated."},
        {"front": "What does `tailrec` compile to?", "back": "A loop: the self-call in tail position becomes stores into the parameter slots and a `goto` back to the start. No new stack frame."},
        {"front": "What if a `tailrec` function isn't really tail-recursive?", "back": "Only a warning, such as `Recursive call is not a tail call.` It compiles to ordinary recursion and can still overflow."},
        {"front": "Functional core vs imperative shell?", "back": "Core: pure decisions from plain values, with the clock passed in, and many fast tests. Shell: reads inputs, calls the core, does the I/O, with few branches and one wiring test."}
    ],
    "terms": [
        {"term": "Read-only", "plain": "You can't change it through this reference. Someone else may still change it."},
        {"term": "Immutable", "plain": "Nobody can change it after it is built, through any reference."},
        {"term": "Shallow copy", "plain": "A copy whose properties point at the same objects as the original's."},
        {"term": "Persistent collection", "plain": "An immutable collection whose \"change\" operations return a new version that shares most of its structure with the old one."},
        {"term": "Tail call", "plain": "A call that is the very last thing a function does, with no work left after it returns."},
        {"term": "Accumulator", "plain": "An extra parameter that carries the result so far, which turns pending work into an argument."},
        {"term": "Functional core", "plain": "The pure part of a program: it decides from plain values and returns a value."},
        {"term": "Imperative shell", "plain": "The thin outer part that reads inputs, calls the core and carries out the result."}
    ],
    "explain_back": {
        "prompt": "A new teammate asks why the shopping job was split into `planShopping` and `ShoppingJob`, when the old job \"worked fine\". Explain what changed and how it changes the tests.",
        "answer": "The old job worked, but its decisions were mixed with its I/O. It read the clock, loaded the list, applied the waiting and discount rules, sent the orders and saved the budget in one loop, so testing a single rule needed a fake store, a fake shop and a fixed clock, plus checks on what the fakes recorded. Now `planShopping` is a pure function: items, shops and today's date go in, and a plan comes out, with the same answer every time. All the rules live there, and each test builds a few values and compares the plan with `equals`, in milliseconds. A different day is just a different argument. `ShoppingJob` keeps only the I/O: read, call the core, send the orders, post and save the budget. It has almost no branches, so one test with fakes is enough to check the wiring. The data is immutable too, so the plan and the budget versions can't change behind our backs while we test or retry."
    },
    "deeper": {
        "minutes": 8,
        "body": "Immutability is also a concurrency tool, and the memory model track explains why. A `val` property compiles to a `final` field, and the Java memory model gives final fields a special promise: once the constructor has finished, any thread that sees the object sees those fields fully set, without a lock, as long as the constructor didn't let `this` escape (\"Safe publication, final fields and escaping this\"). So an object whose state is all `val`s of immutable types can be handed to another thread with no synchronization at all. A persistent collection extends that: one thread builds a new version with `adding` while other threads keep reading the old one, and neither can disturb the other. The catch is the same as in the first section. A `val` holding a `MutableList` gets the promise only for the reference, not for the list's contents.\n\nThe naming change in kotlinx.collections.immutable came with a compiler feature. The 0.5.0 line builds the library itself with Kotlin's Experimental return-value checker in its strictest mode, `-Xreturn-value-checker=full`. The checker arrived in Kotlin 2.3.0, is off by default, and warns when a call's result is ignored. Both changes go after the same bug: a new version computed and then dropped.\n\nOn recursion, `arrow-core` 2.3.0 also contains a `MemoizedDeepRecursiveFunction`, a variant of the standard library's `DeepRecursiveFunction` that remembers its answers. Reach for either only after a plain `fold` or a loop has been ruled out."
    },
    "sources": [
        {"title": "Collections overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/collections-overview.html"},
        {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html"},
        {"title": "Functions: tail recursive functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html"},
        {"title": "kotlinx.collections.immutable CHANGELOG", "url": "https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md"},
        {"title": "KEEP-0459: naming conventions for copy-returning operations", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0459-naming-conventions-for-copy-returning-operations.md"}
    ]
}

out = ROOT / "content/lessons/fp-08.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
