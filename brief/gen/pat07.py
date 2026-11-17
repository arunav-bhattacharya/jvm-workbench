import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l07"
K = "kotlin/workbench/patterns/l07"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l07.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="The same three-step recipe, start timer, the step that changes, record, filled two ways: by a subclass overriding doCall, or by a lambda the caller passes to a function">
<text class="t-s t-m" x="340" y="26" text-anchor="middle">Template Method: a subclass fills the blank</text>
<rect class="box" x="40" y="40" width="150" height="48" rx="8"/>
<text class="t" x="115" y="69" text-anchor="middle">start timer</text>
<rect class="box-b" x="265" y="40" width="150" height="48" rx="8"/>
<text class="t t-code" x="340" y="69" text-anchor="middle">doCall()</text>
<rect class="box" x="490" y="40" width="150" height="48" rx="8"/>
<text class="t" x="565" y="69" text-anchor="middle">record</text>
<line class="ln" x1="190" y1="64" x2="261" y2="64" marker-end="url(#arr)"/>
<line class="ln" x1="415" y1="64" x2="486" y2="64" marker-end="url(#arr)"/>
<text class="t-s t-b" x="340" y="108" text-anchor="middle">overridden in a subclass</text>
<text class="t-s t-m" x="340" y="150" text-anchor="middle">Execute around: the caller passes the blank in</text>
<rect class="box" x="40" y="164" width="150" height="48" rx="8"/>
<text class="t" x="115" y="193" text-anchor="middle">start timer</text>
<rect class="box-b" x="265" y="164" width="150" height="48" rx="8"/>
<text class="t t-code" x="340" y="193" text-anchor="middle">body.get()</text>
<rect class="box" x="490" y="164" width="150" height="48" rx="8"/>
<text class="t" x="565" y="193" text-anchor="middle">record</text>
<line class="ln-a" x1="190" y1="188" x2="261" y2="188" marker-end="url(#arr)"/>
<line class="ln-a" x1="415" y1="188" x2="486" y2="188" marker-end="url(#arr)"/>
<text class="t-s t-b" x="340" y="232" text-anchor="middle">a lambda from the call site</text>
</svg>""".replace("\n", "")

OPENING = """Every parcel leaves the corner shop the same way: weigh it, choose a courier, book it, print the label. Only the choosing changes. Most days the shopkeeper picks the cheapest courier, for an urgent order the fastest, and in heavy rain the van. Down the road, the bakery's bread recipe card has fixed steps (mix, knead, shape, bake, cool) and one blank, the shape, which changes with every loaf.

Code has both shapes: a routine with one decision plugged in, and a recipe with one step left open. The easy traps are an `if`/`else` chain that grows a branch for every new way to deliver, and a base class that asks for its blank before anyone has filled it in.

In the last lesson, we arranged objects into trees and bridges. In this lesson, we'll pass one decision in as a lambda (Strategy), refactor an `if`/`else` pricer without changing a cent, leave a blank for a subclass (Template Method), and then fill it with a function instead. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_CMP = """record Quote(String courier, long priceCents, long minutes) {}

Comparator<Quote> cheapest = Comparator.comparingLong(Quote::priceCents);
Comparator<Quote> cheapestThenFastest = cheapest.thenComparingLong(Quote::minutes);

quotes.sort(cheapestThenFastest);           // sort is the context; the comparator is the strategy"""
K_CMP = """data class Quote(val courier: String, val priceCents: Long, val minutes: Long)

val cheapest = compareBy<Quote> { it.priceCents }
val cheapestThenFastest = cheapest.thenBy { it.minutes }

val ordered = quotes.sortedWith(cheapestThenFastest)   // sortedWith is the context; the comparator is the strategy"""

S0 = """Back to the shop counter. The routine for sending a parcel stays the same, and one decision inside it is swapped: which courier to use. The rule for that decision can change from order to order without touching the rest of the routine.

Java's `sort` works the same way. It owns the routine for putting a list in order and leaves one decision to you, passed in as an object: which of two items goes first. That object is a **comparator**, and it's the Strategy pattern in one line. A **strategy** is one interchangeable algorithm, passed in by the caller and used by the code that needs the decision. That code is called the **context**.

In *Design Patterns*, the 1994 book that named these patterns, a strategy meant an interface and a class for every algorithm. Since Java 8, a lambda or a method reference is the class. Here the shop ranks courier quotes, each with a price and a delivery time:

""" + pair(J_CMP, K_CMP) + """

`Comparator.comparing` "accepts a function that extracts a Comparable sort key" and returns a comparator. `thenComparing` chains a second comparator behind it, used only when the first one ties. Nobody writes a class called `PriceThenTimeComparator` any more. Kotlin's `compareBy` and `thenBy` do the same with function types, and any `(Parcel) -> Long` already is a pricing strategy, with no interface to declare.

`StrategyDemo`, in the Try it, ranks three quotes three ways. They come from Pedal Post, Big Blue Vans and Kestrel, a new courier in town:

```text
cheapest: [Big Blue Vans, Pedal Post, Kestrel]
fastest: [Kestrel, Pedal Post, Big Blue Vans]
cheapest, then fastest: [Big Blue Vans, Kestrel, Pedal Post]
```

Look at the first line. Pedal Post and Kestrel both cost 4.50, and they stay in the order they came in, because the JDK's sort is **stable**: it never swaps two items that compare equal. The third strategy breaks that tie by time, so Kestrel's 20 minutes beat Pedal Post's 30.

The JDK hands you strategies in more places than sorting. A `ThreadPoolExecutor`, the JDK's pool of worker threads, takes a `RejectedExecutionHandler` that decides what happens when its queue is full. `Collectors.groupingBy` takes the function that decides which group each element joins. Each time, the library owns the loop and asks you for one decision.

A named type still helps in two cases. When the strategy has more than one method, such as a courier client with `book` and `track`, you have an interface with implementations, which is ordinary polymorphism: one interface, several classes, one of them chosen while the program runs. And a one-line `@FunctionalInterface interface PriceStrategy { long priceCents(Parcel p); }` says more than a bare `ToLongFunction<Parcel>`, and reads better in stack traces, the list of calls an exception prints.

The counter picture breaks on memory. The shopkeeper remembers that yesterday's van was late. A strategy shouldn't remember anything. A lambda that captures and changes a field is a strategy with hidden memory, a shopkeeper still holding a grudge, and two threads sorting with it at once will corrupt each other's results.

**A strategy is one decision, passed in. Keep it pure: input in, answer out.**

A comparator is a strategy for a context someone else wrote. Next, a context of our own that grew the old way."""

# ---------------------------------------------------------------- section 1
J_TWO = """static long bike(Parcel p) {                  // two divisions, rounded separately, as the legacy code does
    return 200 + p.grams() * 30 / 1_000 + (p.district().equals("Old Town") ? 0 : p.grams() * 10 / 1_000);
}

// open set: one lambda per method, in a map that settings or plug-ins could fill
static final Map<DeliveryMethod, PriceStrategy> STRATEGIES = new EnumMap<>(Map.of(
        BIKE,   p -> bike(p),
        VAN,    p -> 450,
        PICKUP, p -> 0));

// closed set: one switch, checked by the compiler
static long priceCents(Parcel p) {
    return switch (p.method()) {
        case BIKE -> bike(p);
        case VAN -> 450;
        case PICKUP -> 0;
    };
}"""
K_TWO = """fun bike(p: Parcel): Long =                   // two divisions, rounded separately, as the legacy code does
    200L + p.grams * 30 / 1_000 + if (p.district == "Old Town") 0 else p.grams * 10 / 1_000

// open set: one function per method, in a map that settings or plug-ins could fill
val strategies: Map<DeliveryMethod, (Parcel) -> Long> = mapOf(
    BIKE to ::bike,
    VAN to { _ -> 450L },
    PICKUP to { _ -> 0L },
)

// closed set: one when, checked by the compiler
fun priceCents(p: Parcel): Long = when (p.method) {
    BIKE -> bike(p)
    VAN -> 450
    PICKUP -> 0
}"""

S1 = """The shop's delivery pricer grew the way most do: one `if`/`else if` chain on the delivery method, with a special case added every year. `LegacyPricer`, in the lab, is that method. A bike costs 2.00 plus 0.30 per kg, and 0.10 more per kg outside the Old Town, where the hills are. A van costs 4.50, whatever the weight. Picking the parcel up at the counter is free.

Before you touch a method like that, pin what it does. Write a test that runs the old code and the new code over a grid of inputs and asserts that they agree. Michael Feathers, in his book *Working Effectively with Legacy Code*, calls this a **characterization test**. It records today's behavior, bugs included, so the refactor can't change it by accident.

Choose the grid for its edges, not its size: weight 0, weight 1, the Old Town and two districts outside it, and every enum constant. Integer division rounds down, and that's where a tidied-up rule drifts by a cent. The legacy code rounds the per-kg price and the hill surcharge separately, so 999 g outside the Old Town costs 2.38. A refactor that "simplifies" the two into `grams * 40 / 1_000` charges 2.39, and the grid catches it.

Then pick one of two shapes:

""" + pair(J_TWO, K_TWO) + """

A map of strategies suits an **open** set: methods read from settings, plug-ins, rules a customer can switch on. A `switch` or `when` with no default suits a **closed** set you own, like the `DeliveryMethod` enum.

You see the difference on the day the town's first delivery drone arrives, and someone adds `DRONE` to the enum. The switch stops compiling, right where the rule is missing. javac says "the switch expression does not cover all possible input values", and kotlinc says "'when' expression must be exhaustive. Add the 'DRONE' branch or an 'else' branch." The map compiles, ships, and fails on the first drone parcel: a `NullPointerException` in Java, because `Map.get` returned null, and `NoSuchElementException: Key DRONE is missing in the map.` from Kotlin's `getValue`. The Try it shows all four messages.

If you do choose a map for a closed set, add a check at startup that every constant has an entry. The failure then moves from the first drone parcel to the moment the program starts.

**For a closed set you own, let the compiler check every case. Use a map when the set is open.**

Neither shape needs a class per delivery method: the lambdas are the strategies. A strategy swaps a whole decision. Sometimes the routine is what stays fixed, and one step inside it changes."""

# ---------------------------------------------------------------- section 2
J_TPL = """abstract class OutboundCall<T> {
    public final T execute() {                         // the recipe: subclasses can't change it
        long start = System.nanoTime();
        try {
            return doCall();                           // hook 1: the step that changes
        } finally {
            timings.record(name(), System.nanoTime() - start);
        }
    }
    protected abstract String name();                  // hook 2
    protected abstract T doCall();
}

final class BookingCall extends OutboundCall<String> {
    protected String name() { return "courier.book"; }
    protected String doCall() { return courier.book(address, grams); }
}"""
K_TPL = """abstract class OutboundCall<T> {
    fun execute(): T {                                 // final by default in Kotlin: subclasses can't change it
        val start = System.nanoTime()
        try {
            return doCall()                            // hook 1: the step that changes
        } finally {
            timings.record(name(), System.nanoTime() - start)
        }
    }
    protected abstract fun name(): String              // hook 2
    protected abstract fun doCall(): T
}

class BookingCall(private val address: String, private val grams: Int) : OutboundCall<String>() {
    override fun name() = "courier.book"
    override fun doCall() = courier.book(address, grams)
}"""

S2 = """Back to the bakery's recipe card: mix, knead, shape, bake, cool. Only the shaping changes from loaf to loaf, and the card leaves a blank for it. Nobody rewrites the card for a new loaf. They fill in the blank.

Every call the shop's program makes to a courier company needs the same steps around it: start a timer, make the call, write down how long it took. **Template Method** puts those steps in a base class as one `final` method, which subclasses can't override, called the template, and leaves blanks called **hooks** for subclasses to fill. The base class is abstract, which means it has methods left for its subclasses to write:

""" + pair(J_TPL, K_TPL) + """

The base class owns the order of the steps, and because `execute` is final, no subclass can skip the timer. The JDK uses this shape too. To build a read-only list, you extend `AbstractList` and write only `get` and `size`; the rest of `List` is a recipe built on those two hooks.

Inheritance is the cost. A subclass depends on every detail of its parent, and a parent that changes when it calls its hooks can break subclasses it has never seen. That is the **fragile base class** problem.

The sharpest edge is a base-class constructor that calls a hook. Java and Kotlin run the base constructor first, and a subclass assigns its own fields only after that returns. So the hook runs on a half-built object. `TemplateHookDemo`, in the Try it, builds a log label in the base constructor by calling `name()`, and `BookingCall` builds its name from its `courier` field:

```text
  start outbound booking via null
```

The courier field hadn't been assigned yet, so the label names a courier nobody in town has heard of: `null`. In Java, a field that hasn't been assigned reads as `null`. In Kotlin, the same code reads `null` from `private val courier: String`, a property the type system promises is never null, and kotlinc compiles it without a warning.

JDK 25 gives Java one way out. With flexible constructor bodies (JEP 513), a constructor may assign its own fields before it calls `super()`, so `this.courier = courier; super();` makes the label read `booking via Pedal Post`. The labs compile for Java 21, where javac answers "flexible constructors is not supported in -source 21", and Kotlin has no such option.

That's where the recipe picture breaks. A baker can't be asked for the shape before anyone has said which loaf it is. A base-class constructor can ask, and it gets back whatever an empty field holds.

**Never call an overridable method from a constructor.** Compute such values when they're first needed, or pass them up to the base constructor as arguments.

Template Method gives the recipe to a base class and the blank to a subclass. What if we could fill the blank without writing a subclass at all?"""

# ---------------------------------------------------------------- section 3
J_EA = """static <T> T timed(String name, Timings timings, Supplier<T> body) {
    long start = System.nanoTime();                    // before
    try {
        return body.get();                             // the caller's step
    } finally {
        timings.record(name, System.nanoTime() - start);   // after, always
    }
}

String ref = timed("courier.book", timings, () -> courier.book(address, grams));"""
K_EA = """inline fun <T> timed(name: String, timings: Timings, body: () -> T): T {
    val start = System.nanoTime()                      // before
    try {
        return body()                                  // the caller's step, inlined: no lambda object
    } finally {
        timings.record(name, System.nanoTime() - start)    // after, always
    }
}

val ref = timed("courier.book", timings) { courier.book(address, grams) }"""

S3 = """The modern answer keeps the recipe and drops the subclass. Write the recipe as a function, and take the step that changes as a lambda. The blank on the card becomes a parameter: you hand over the shaping together with the card.

""" + pair(J_EA, K_EA) + """

This shape is called **execute around**: a function runs the steps before and after, and calls your code in the middle. You already use it every day. `try`-with-resources is execute around built into Java: the language opens the resource, runs your block, and closes the resource whatever happens. Kotlin's standard library is full of it. `use {}` closes a resource, `synchronized(lock) {}` takes and releases a lock, and `measureTimeMillis {}` times a block.

Kotlin makes the function version cheaper than Java's. The compiler copies the body of an **inline** function, lambda included, into each place that calls it. So no lambda object is created, and a `return` inside the block returns from the function that called `timed`. Java's `Supplier` has a different limit: its `get` method can't throw checked exceptions, the ones the Java compiler makes you catch or declare, so wrapping a courier library that throws `IOException` needs your own functional interface with a `throws` clause. Kotlin has no checked exceptions, so `timed("courier.book", timings) { client.book(address) }` just works. The compare block below shows both.

Prefer the function. It composes: `timed("courier.book", timings) { retrying(3) { courier.book(address, grams) } }` times the whole booking, retries included. It needs no class per call site. And it can't hit the constructor trap, because there is no constructor. Keep Template Method for recipes with many hooks, such as `AbstractList`, and make the template method `final`.

**When only one step changes, pass that step in as a function.**

The figure puts the two shapes side by side. They run the same steps in the same order; only the way the blank gets filled is different.

Check yourself. `courier.book(address, grams)` throws inside `timed`. Does the call still show up in the timings, and does the caller see the exception? (Yes to both. The `finally` block records the time, and then the exception carries on to the caller as if `timed` weren't there.)"""

L = {
 "id": "pat-07",
 "title": "Strategy and Template Method",
 "minutes": 37,
 "goal": "By the end you can pass algorithms as lambdas and comparators, refactor an if/else pricer into a strategy map or an exhaustive switch behind a characterization test, and replace a Template Method base class with an execute-around function.",
 "opening": OPENING,
 "warmup": {
  "q": "Delivery prices are worked out two ways: through an `EnumMap<DeliveryMethod, PriceStrategy>`, and through a `switch` expression over `DeliveryMethod` with no `default`. A teammate adds `DRONE` to the `DeliveryMethod` enum and builds. What happens?",
  "options": ["Both versions fail to compile", "The switch fails to compile; the map compiles and throws on the first drone parcel", "The map fails to compile; the switch throws at runtime", "Both compile, and drone parcels cost 0"],
  "answer": 1,
  "why": "A switch expression over an enum with no `default` must cover every constant, so javac reports \"the switch expression does not cover all possible input values\" right where the rule is missing. The map has no idea which keys should exist: `EnumMap.get(DRONE)` returns null, and calling `priceCents` on it throws when the program runs. That difference decides which shape fits which job, as the second section shows."
 },
 "sections": [
  {
   "h": "Strategy: the one decision you pass in",
   "body": S0,
   "try": {
    "title": "Rank couriers three ways",
    "minutes": 4,
    "steps": [
     "Read `StrategyDemo.java` (or `StrategyDemo.kt`) and predict the three lines. Remember that equal prices keep their original order, because the JDK's sort is stable.",
     "Run it with the command below.",
     "Add a fourth quote at the end of the list, `new Quote(\"Gull Express\", 350, 60)` (`CourierQuote(\"Gull Express\", 350, 60)` in Kotlin). Predict all three lines again, then run."
    ],
    "code": code("java", "StrategyDemo.java", "StrategyDemo", "kotlin", "StrategyDemo.kt", "StrategyDemoKt"),
    "expect": "`cheapest: [Big Blue Vans, Pedal Post, Kestrel]`, `fastest: [Kestrel, Pedal Post, Big Blue Vans]`, `cheapest, then fastest: [Big Blue Vans, Kestrel, Pedal Post]`. With Gull Express: `[Big Blue Vans, Gull Express, Pedal Post, Kestrel]`, `[Kestrel, Pedal Post, Gull Express, Big Blue Vans]` and `[Gull Express, Big Blue Vans, Kestrel, Pedal Post]`. Three algorithms, zero classes: each strategy is one expression."
   },
   "refs": [
    {"title": "Comparator (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Comparator.html", "kind": "docs"}
   ]
  },
  {
   "h": "Refactor the if/else pricer, after pinning what it does",
   "body": S1,
   "try": {
    "title": "Add a way to deliver and see who notices",
    "minutes": 5,
    "steps": [
     "Run `RouterDemo` in either language: the map and the switch agree on all three ways to deliver.",
     "Add `DRONE` to the `Way` enum. Predict which part fails, and when, then run.",
     "Add the missing branch, `case DRONE -> 990;` in Java or `Way.DRONE -> 990` in Kotlin. Predict, then run again. Remove `DRONE` when you're done."
    ],
    "code": code("java", "RouterDemo.java", "RouterDemo", "kotlin", "RouterDemo.kt", "RouterDemoKt"),
    "expect": "With `DRONE` added, the build fails: javac says `the switch expression does not cover all possible input values`, and kotlinc says `'when' expression must be exhaustive. Add the 'DRONE' branch or an 'else' branch.` After you add the branch, the three lines print, and then the drone line fails: Java throws `NullPointerException` because `Map.get` returned null, and Kotlin throws `NoSuchElementException: Key DRONE is missing in the map.` The compiler found one gap; only a crash found the other."
   },
   "refs": [
    {"title": "Conditions and loops: when (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Template Method: a recipe with a blank for subclasses",
   "body": S2,
   "try": {
    "title": "Watch a hook run too early",
    "minutes": 4,
    "steps": [
     "Read `TemplateHookDemo.java` (or `.kt`). The base constructor builds `label` by calling `name()`. Predict the label the template version prints.",
     "Run it with the command below and compare the two versions.",
     "Fix the template without changing `BookingCall`: delete the `label` field and build the label inside `execute()` instead. Run again."
    ],
    "code": code("java", "TemplateHookDemo.java", "TemplateHookDemo", "kotlin", "TemplateHookDemo.kt", "TemplateHookDemoKt"),
    "expect": "The template prints `start outbound booking via null`: `name()` ran inside the base constructor, before `BookingCall` had assigned `courier`. Kotlin prints the same `null` from a property declared as a non-null `String`, with no compiler warning. The function version prints `start outbound booking via Pedal Post`. After the fix, the template prints that too, because `name()` now runs only when the object is complete."
   },
   "refs": [
    {"title": "AbstractList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/AbstractList.html", "kind": "docs"}
   ]
  },
  {
   "h": "Execute around: pass the blank in as a function",
   "body": S3,
   "figure": {"svg": FIG, "caption": "The same recipe both ways. Template Method fills the blank with a subclass; execute around takes it as a lambda from the call site."},
   "refs": [
    {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "An execute-around timer for a courier library",
  "java": {"title": "Couriers.java", "src": """// Supplier can't throw checked exceptions, so a wrapper for library calls needs its own interface
@FunctionalInterface
interface IoCall<T> {
    T call() throws IOException;
}

final class Couriers {
    static <T> T timed(String name, Map<String, Long> timings, IoCall<T> body) throws IOException {
        long start = System.nanoTime();
        try {
            return body.call();
        } finally {
            timings.merge(name, System.nanoTime() - start, Long::sum);
        }
    }

    static String bookOrNull(Map<String, Long> timings, CourierLibrary lib, String address) throws IOException {
        String ref = timed("courier.book", timings, () -> lib.book(address));
        return ref.isEmpty() ? null : ref;          // a lambda can't return from bookOrNull itself
    }
}"""},
  "kotlin": {"title": "Couriers.kt", "src": """// inline: the block is pasted into the caller, so no lambda object and no checked-exception plumbing
inline fun <T> timed(name: String, timings: MutableMap<String, Long>, body: () -> T): T {
    val start = System.nanoTime()
    try {
        return body()
    } finally {
        timings.merge(name, System.nanoTime() - start) { a, b -> a + b }
    }
}

fun bookOrNull(timings: MutableMap<String, Long>, lib: CourierLibrary, address: String): String? {
    val ref = timed("courier.book", timings) {
        lib.book(address).ifEmpty { return null }   // non-local return: leaves bookOrNull, the finally still records
    }
    return ref
}"""},
  "note": "The recipe is identical: read the clock, run the caller's block, record in `finally`. Three things differ. Java's standard functional interfaces can't throw checked exceptions, so a library that throws `IOException` forces you to declare `IoCall` with a `throws` clause; Kotlin has no checked exceptions. Kotlin's `inline` copies `timed` and the block into each call site, so there is no lambda object, and `return null` inside the block returns from `bookOrNull` itself while the `finally` still runs. And an inline block may call suspend functions when the caller is a suspend function, which a Java lambda can't do. Neither language needs Template Method for this; the function is the whole pattern."
 },
 "worked": {
  "title": "Turn a back-off if/else into strategies, without changing behavior",
  "steps": [
   {"say": "When a courier's line is busy, the shop's retry helper waits a little before trying again; that wait is called the back-off. The helper reads the back-off rule's name from the settings file and decides the wait on every attempt. Spot two problems before reading on.",
    "code": """// settings: courier.backoff=doubling  (or "fixed", "none")
Duration waitBeforeRetry(String policy, int attempt) {
    if (policy.equals("fixed")) {
        return Duration.ofMillis(200);
    } else if (policy.equals("doubling")) {
        long ms = 100L << (attempt - 1);                 // 100, 200, 400, ...
        return Duration.ofMillis(Math.min(ms, 5_000));
    } else if (policy.equals("none")) {
        return Duration.ZERO;
    }
    return Duration.ofMillis(200);                       // a typo in the settings silently means "fixed"
}""", "lang": "java",
    "alt_code": """// settings: courier.backoff=doubling  (or "fixed", "none")
fun waitBeforeRetry(policy: String, attempt: Int): Duration =
    if (policy == "fixed") {
        Duration.ofMillis(200)
    } else if (policy == "doubling") {
        val ms = 100L shl (attempt - 1)                  // 100, 200, 400, ...
        Duration.ofMillis(minOf(ms, 5_000))
    } else if (policy == "none") {
        Duration.ZERO
    } else {
        Duration.ofMillis(200)                           // a typo in the settings silently means "fixed"
    }""", "alt_lang": "kotlin"},
   {"say": "The rule is chosen again on every attempt, and a typo like `doubeling` quietly becomes \"fixed\". Fix neither yet. First pin today's behavior with a characterization test, so the refactor can't change a wait by accident.",
    "code": """@ParameterizedTest
@CsvSource({"fixed,1,200", "fixed,4,200", "doubling,1,100", "doubling,3,400", "doubling,9,5000", "none,2,0"})
void pinned(String policy, int attempt, long expectedMs) {
    assertThat(waitBeforeRetry(policy, attempt)).isEqualTo(Duration.ofMillis(expectedMs));
}""", "lang": "java",
    "alt_code": """@ParameterizedTest
@CsvSource("fixed,1,200", "fixed,4,200", "doubling,1,100", "doubling,3,400", "doubling,9,5000", "none,2,0")
fun pinned(policy: String, attempt: Int, expectedMs: Long) {
    assertThat(waitBeforeRetry(policy, attempt)).isEqualTo(Duration.ofMillis(expectedMs))
}""", "alt_lang": "kotlin"},
   {"say": "Now give the decision a type with one method, and a factory for each rule. Each factory returns a lambda: a complete strategy.",
    "code": """@FunctionalInterface
interface Backoff {
    Duration delay(int attempt);                                        // 1. one decision, one method

    static Backoff fixed(Duration d) { return attempt -> d; }
    static Backoff doubling(Duration base, Duration max) {
        return attempt -> {
            Duration d = base.multipliedBy(1L << (attempt - 1));
            return d.compareTo(max) > 0 ? max : d;
        };
    }
    Backoff NONE = attempt -> Duration.ZERO;
}""", "lang": "java",
    "alt_code": """fun interface Backoff {
    fun delay(attempt: Int): Duration                                    // 1. one decision, one method

    companion object {
        fun fixed(d: Duration) = Backoff { d }
        fun doubling(base: Duration, max: Duration) = Backoff { attempt ->
            minOf(base.multipliedBy(1L shl (attempt - 1)), max)
        }
        val NONE = Backoff { Duration.ZERO }
    }
}""", "alt_lang": "kotlin"},
   {"say": "Choose the strategy once, at startup. Here a `default` is right, because names in a settings file are an open set you don't control, and it throws, so a typo stops the program the moment it starts. Point the pinned test at `fromSettings(policy).delay(attempt)`: it still passes.",
    "code": """static Backoff fromSettings(String name) {                              // 2. choose once, at startup
    return switch (name) {
        case "fixed" -> Backoff.fixed(Duration.ofMillis(200));
        case "doubling" -> Backoff.doubling(Duration.ofMillis(100), Duration.ofSeconds(5));
        case "none" -> Backoff.NONE;
        default -> throw new IllegalArgumentException("unknown courier.backoff: " + name);   // 3. a typo stops the start
    };
}

Backoff backoff = fromSettings(settings.backoff());                     // 4. the retry loop calls backoff.delay(n)""", "lang": "java",
    "alt_code": """fun fromSettings(name: String): Backoff = when (name) {                 // 2. choose once, at startup
    "fixed" -> Backoff.fixed(Duration.ofMillis(200))
    "doubling" -> Backoff.doubling(Duration.ofMillis(100), Duration.ofSeconds(5))
    "none" -> Backoff.NONE
    else -> throw IllegalArgumentException("unknown courier.backoff: $name") // 3. a typo stops the start
}

val backoff = fromSettings(settings.backoff)                             // 4. the retry loop calls backoff.delay(n)""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Refactor the delivery pricer twice, and replace a template with a function",
  "minutes": 13,
  "files": [f"{lab}/main/{J}/DeliveryPrices.java", f"{lab}/main/{J}/Outbound.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l07.*'",
  "steps": [
   "Read `DeliveryMethod`, `Parcel` and `LegacyPricer`. They are given, and `LegacyPricer.priceCents` is the specification. Run the tests: all eight fail.",
   "Write `DeliveryPrices.strategies()`: a `new EnumMap<>(DeliveryMethod.class)` with one lambda per method. Copy the rules from `LegacyPricer`, including the hill surcharge outside the Old Town. Then write `priceByMap` as one line.",
   "Write `priceBySwitch` as a switch expression over `p.method()` with no `default`.",
   "Write `cheapestThenFastest` from `Comparator.comparingLong` and its `then...` methods.",
   "Write `Outbound.timed`: one clock read before, the body in a `try`, the outcome noted in a `catch` that rethrows, one record added in `finally`. Compare it with the given `OutboundCall`.",
   "Run the tests until all eight pass. Then add `DRONE` to `DeliveryMethod` and build: which of your two refactors complains? Remove it again."
  ],
  "hints": [
   "For the bike, `200 + p.grams() * 30 / 1_000 + (p.district().equals(\"Old Town\") ? 0 : p.grams() * 10 / 1_000)`. Keep the two divisions separate, exactly as the legacy code has them, or the parity test finds the cent: 999 g outside the Old Town is 238, not 239.",
   "`Comparator.comparingLong(Quote::priceCents).thenComparingLong(Quote::minutes).thenComparing(Quote::courier)` sorts by price, then time, then name.",
   "Declare `String outcome = \"ok\";` before the `try`, set it to `e.getClass().getSimpleName()` in `catch (RuntimeException e)`, rethrow with `throw e;`, and add the `CallRecord` in `finally`, so success and failure each log exactly once."
  ],
  "done_when": "All eight tests in `StrategyTemplateTest` pass."
 },
 "drill": {
  "title": "A retry wrapper from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `retrying(attempts, body)` as an execute-around function: it runs `body` up to `attempts` times, returns the first success, and rethrows the last failure. In Kotlin make it `inline`. Then say which courier call you would never pass to it unless the courier remembers order numbers, as in *Decorator and Proxy*.",
  "answer": {"lang": "java", "src": """static <T> T retrying(int attempts, Supplier<T> body) {
    RuntimeException last = null;
    for (int i = 1; i <= attempts; i++) {
        try {
            return body.get();                 // the caller's step, run again on failure
        } catch (RuntimeException e) {
            last = e;
        }
    }
    throw last;                                 // never pass a booking that could happen twice
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """inline fun <T> retrying(attempts: Int, body: () -> T): T {
    var last: RuntimeException? = null
    repeat(attempts) {
        try {
            return body()                       // non-local return from retrying
        } catch (e: RuntimeException) {
            last = e
        }
    }
    throw last!!                                // never pass a booking that could happen twice
}"""}}
 },
 "recap": [
  "Strategy is an algorithm the caller picks and passes in. In modern Java and Kotlin, a lambda, a method reference or a function type is the strategy; `Comparator.comparing` is the JDK's own example.",
  "Before refactoring an `if`/`else` chain, pin its behavior with a characterization test over a grid of edge inputs, such as weight 0, weight 1 and 999 g.",
  "Use a map of strategies for open sets (settings, plug-ins) and a `switch` or `when` with no default for closed sets you own. A missing map entry fails when the program runs; a missing case fails to compile.",
  "Template Method is a final recipe in a base class with hooks for subclasses. Never call a hook from a constructor: the subclass's fields are still unset, even Kotlin non-null `val`s.",
  "Execute around replaces most Template Methods: the recipe is a function and the changing step is a lambda, as in try-with-resources, `use`, `synchronized` and `measureTimeMillis`. Kotlin `inline` makes it free of lambda objects.",
  "The limit: a passed-in function swaps one decision or one step, not the order of the steps. When what may happen next depends on what happened before, you need something that remembers, which is where lesson 9 of this track goes."
 ],
 "closing": "We started with a shopkeeper choosing a courier and a recipe card with one blank. The choice became a comparator or a lambda passed in, and the long `if`/`else` became a map or a switch, pinned by a test against the old code. The blank became a hook, and then simply a function's parameter.\n\nNow look in your own code for a base class whose constructor calls an abstract or open method. Each one hands its subclasses a half-built object.\n\nNext, we'll tell everyone who cares that something happened, and turn a request into a slip of paper. How does the shop ring a bell for everyone who signed up, without knowing who they are?",
 "quiz": [
  {"q": "A team prices with `Map<DeliveryMethod, PriceStrategy>` built from settings, and also has a `switch` over `DeliveryMethod` with no default in the receipt code. Someone adds `DRONE` to `DeliveryMethod`. Which statement is true?",
   "options": ["The map fails to compile; the switch throws at runtime", "The switch fails to compile; the map compiles and fails on the first drone parcel", "Both fail to compile", "Both compile, and drone parcels cost 0"],
   "answer": 1,
   "why": "Only the switch tells the compiler which constants must be handled, so only the switch breaks the build. The map has no idea `DRONE` should be a key, so `get` returns null when the program runs. With a map over a closed set, add a check at startup that every constant has an entry."},
  {"q": "Quotes: Hilltop Couriers (price 300, 40 minutes), Gull Express (price 250, 75 minutes), Riverside Bikes (price 300, 25 minutes), in that order. In what order does `Comparator.comparingLong(Quote::priceCents).thenComparingLong(Quote::minutes)` sort them?",
   "options": ["Gull Express, Riverside Bikes, Hilltop Couriers", "Gull Express, Hilltop Couriers, Riverside Bikes", "Riverside Bikes, Hilltop Couriers, Gull Express", "Hilltop Couriers, Riverside Bikes, Gull Express"],
   "answer": 0,
   "why": "The first comparator puts the 250 price first: Gull Express. Hilltop and Riverside tie on price, so the second comparator breaks the tie by time: Riverside's 25 minutes before Hilltop's 40. The tempting \"Gull Express, Hilltop Couriers, Riverside Bikes\" ignores the tie-breaker and keeps the original order."},
  {"q": "A base class sets `label = \"outbound \" + name();` in its constructor. The subclass `BookingCall(String courier)` assigns `this.courier = courier` and implements `name()` as `\"booking via \" + courier`. What is the label of `new BookingCall(\"Pedal Post\")`?",
   "options": ["It throws `NullPointerException`", "`outbound booking via Pedal Post`", "`outbound booking via null`", "It doesn't compile"],
   "answer": 2,
   "why": "The base constructor runs first and calls the overridden `name()` before `BookingCall` has assigned `courier`, so `courier` is still null, and string concatenation turns null into \"null\". Nothing throws, which makes the bug easy to miss. Kotlin behaves the same even for a non-null `val courier: String`."},
  {"q": "At 30 places, the shop's code calls different courier services, and every call must be timed and logged in the same way. Which shape fits best?",
   "options": ["An abstract base class with a final `execute()` and one subclass per call site", "A `Map<String, Runnable>` holding all 30 calls", "A singleton that every call registers with", "A higher-order function, `timed(\"courier.book\") { ... }`, `inline` in Kotlin, wrapped around each call"],
   "answer": 3,
   "why": "The steps around the call are fixed and the middle changes per call site, which is execute around: one function, and each call site passes its own block. Thirty subclasses is Template Method's ceremony with its inheritance problems, and a map or a singleton doesn't wrap anything."},
  {"q": "From *Decorator and Proxy*: each delivery method's base rule is a `DeliveryFee` stored in a `Map<DeliveryMethod, DeliveryFee>`. The shop now wants every delivery capped at 8.00. Where does the cap go with the least code?",
   "options": ["Edit every lambda in the map to call `Math.min(..., 800)`", "Decorate each fee once when you build the map: `fees.replaceAll((m, f) -> f.cappedAt(800))`", "Add a `default -> 800` branch to the switch", "Make each strategy extend a `CappedFee` base class"],
   "answer": 1,
   "why": "Strategies and decorators combine: the map picks the rule, and wrapping each rule in `cappedAt(800)` adds the cap once, in one place. Editing every lambda copies the rule into each strategy, a `default` branch changes nothing for known methods, and a base class brings back the inheritance this lesson moves away from.",
   "from": "pat-05"}
 ],
 "flashcards": [
  {"front": "In modern Java or Kotlin, what is a strategy usually written as?", "back": "A lambda or method reference for a functional interface (`Comparator`, `PriceStrategy`), or a Kotlin function type such as `(Parcel) -> Long`."},
  {"front": "You add a constant to an enum. What happens to a `switch` over it with no default, and to an `EnumMap` of strategies?", "back": "The switch fails to compile. The map compiles, and `get` returns null for the new key when the program runs."},
  {"front": "Map of strategies or exhaustive switch: which for a closed set you own?", "back": "The switch (or `when`) with no default, so a new case is a compile error. Use the map for open sets: settings, plug-ins."},
  {"front": "What is a characterization test?", "back": "A test that records what existing code does today, bugs included, so a refactor can prove it changed nothing."},
  {"front": "What is Template Method?", "back": "A final recipe method in a base class that calls hook methods subclasses override."},
  {"front": "A base-class constructor calls an overridden method that reads a subclass field. What does it see?", "back": "The field's default: null or 0, because the subclass constructor hasn't run yet. In Kotlin even a non-null `val` reads as null."},
  {"front": "What is execute around?", "back": "A function that runs the steps before and after, and takes the changing step as a lambda: try-with-resources, `use {}`, `synchronized(lock) {}`."}
 ],
 "terms": [
  {"term": "Strategy", "plain": "One interchangeable algorithm, passed in by the caller and used by the code that needs a decision."},
  {"term": "Characterization test", "plain": "A test that pins down what old code does now, so a refactor can't change it unnoticed."},
  {"term": "Template Method", "plain": "A base-class method that fixes the steps and lets subclasses fill in some of them."},
  {"term": "Hook", "plain": "An overridable method a template calls at a fixed point in its recipe."},
  {"term": "Fragile base class", "plain": "When a change inside a parent class breaks subclasses that relied on how it worked."},
  {"term": "Execute around", "plain": "A function that wraps the caller's code with steps before and after, taking that code as a lambda."},
  {"term": "Inline function", "plain": "A Kotlin function whose body, with its lambda arguments, is copied into each place that calls it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"Should our delivery prices live in a `Map<DeliveryMethod, PriceStrategy>` or in a `switch` over `DeliveryMethod`?\" Explain how you decide, and what each version does on the day someone adds a new way to deliver.",
  "answer": "It depends on who owns the set of keys. If the set is closed and ours, like the `DeliveryMethod` enum, I use a switch (or `when`) with no default. When someone adds `DRONE`, the build fails at every switch that needs a rule, so nobody can ship without deciding what a drone delivery costs. If the set is open, because rules come from settings or plug-ins or customers switch them on, a map of strategies fits, since the code can't know the keys when it's compiled. The map's weakness is that a missing entry only shows up when the program runs: `EnumMap.get` returns null and the first drone parcel fails. If we use a map for an enum anyway, we add a check at startup that every constant has an entry, so the program refuses to start instead of failing a customer's order. Either way, I'd pin the current prices with a characterization test against the old code before changing anything."
 },
 "deeper": {
  "minutes": 10,
  "body": """Strategy and State have the same structure: an object holds an interface and hands the decision to it. The difference is who chooses. The caller picks a strategy, and it stays put. A state object picks the next state itself as things happen to it. Lesson 9 of this track, *State and Chain of Responsibility*, builds that kind of object.

Java can do execute around without lambdas. Make the step before a constructor and the step after `close()`, and try-with-resources does the rest: `try (var t = timings.start(\"courier.book\")) { return courier.book(address, grams); }`. This form lets checked exceptions pass through untouched and needs no functional interface, which is why many timing and logging libraries offer a closeable timer. The cost is that the caller must remember the `try`.

Kotlin's `inline` has limits worth knowing. An inlined lambda can't be stored or passed to a function that isn't inline, because it doesn't exist as an object; mark such a parameter `noinline`. If the lambda runs somewhere else, such as on another thread or in a callback, mark it `crossinline`, which forbids a `return` from the outer function inside it. And large inline functions grow every place that calls them, so keep them small: the recipe inline, the heavy lifting in a normal function it calls.

Strategies hide in Kotlin's collection functions too. `sortedWith`, `maxByOrNull { it.priceCents }`, `groupBy { it.method }` and `partition { it.grams > 5_000 }` each own the loop and take one decision from you as a lambda."""
 },
 "sources": [
  {"title": "Comparator (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Comparator.html"},
  {"title": "Higher-order functions and lambdas (Kotlin docs)", "url": "https://kotlinlang.org/docs/lambdas.html"},
  {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
  {"title": "AbstractList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/AbstractList.html"},
  {"title": "JLS 15.28: switch expressions", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.28"}
 ]
}

out = ROOT / "content/lessons/pat-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
