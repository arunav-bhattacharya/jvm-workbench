import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l07"
K = "kotlin/workbench/patterns/l07"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l07.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="The same three-step skeleton, start timer, the varying step, record, filled two ways: by a subclass overriding doCall, or by a lambda the caller passes to a function">
<text class="t-s t-m" x="340" y="26" text-anchor="middle">Template Method: a subclass fills the hole</text>
<rect class="box" x="40" y="40" width="150" height="48" rx="8"/>
<text class="t" x="115" y="69" text-anchor="middle">start timer</text>
<rect class="box-b" x="265" y="40" width="150" height="48" rx="8"/>
<text class="t t-code" x="340" y="69" text-anchor="middle">doCall()</text>
<rect class="box" x="490" y="40" width="150" height="48" rx="8"/>
<text class="t" x="565" y="69" text-anchor="middle">record</text>
<line class="ln" x1="190" y1="64" x2="261" y2="64" marker-end="url(#arr)"/>
<line class="ln" x1="415" y1="64" x2="486" y2="64" marker-end="url(#arr)"/>
<text class="t-s t-b" x="340" y="108" text-anchor="middle">overridden in a subclass</text>
<text class="t-s t-m" x="340" y="150" text-anchor="middle">Execute around: the caller passes the hole</text>
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

S1 = """`quotes.sort(Comparator.comparingLong(Quote::feeMinor))` is the Strategy pattern in one line. `sort` owns the algorithm for putting things in order. The comparator is the one decision it leaves to you, passed in as an object. GoF Strategy is exactly that: a family of interchangeable algorithms behind one interface, picked by the client.

In 1994 that meant an interface and a class per algorithm. Since Java 8, a lambda or a method reference is the class:

```java
record Quote(String psp, long feeMinor, long p95Millis) {}

Comparator<Quote> cheapest = Comparator.comparingLong(Quote::feeMinor);
Comparator<Quote> cheapestThenFastest = cheapest.thenComparingLong(Quote::p95Millis);

quotes.sort(cheapestThenFastest);          // sort is the context; the comparator is the strategy
```

```kotlin
data class Quote(val psp: String, val feeMinor: Long, val p95Millis: Long)

val cheapest = compareBy<Quote> { it.feeMinor }
val cheapestThenFastest = cheapest.thenBy { it.p95Millis }

val ordered = quotes.sortedWith(cheapestThenFastest)   // sortedWith is the context; the comparator is the strategy
```

`Comparator.comparing` "accepts a function that extracts a Comparable sort key" and returns a comparator, and `thenComparing` chains a second one behind it. Nobody writes a class called `FeeThenLatencyComparator` any more. Kotlin's `compareBy` and `thenBy` do the same with function types, and any `(Payment) -> Long` already is a fee strategy, with no interface to declare.

The JDK hands you strategies in more places than sorting. `ThreadPoolExecutor` takes a `RejectedExecutionHandler` that decides what happens when its queue is full (`AbortPolicy`, `CallerRunsPolicy` and two more), and `Collectors.groupingBy` takes the function that decides which group each element joins. Each time, the library owns the loop and asks you for one decision.

A named type still helps in two cases. When the strategy has more than one method, such as a PSP client with `authorize` and `refund`, you have an interface with implementations, which is ordinary polymorphism. And a one-line `@FunctionalInterface interface FeeStrategy { long fee(Payment p); }` documents intent better than a bare `ToLongFunction<Payment>`, and reads better in stack traces.

Watch for state. A lambda that captures and changes a field is a strategy with hidden memory, and two threads sorting with it at once will corrupt each other's results. Keep strategies pure: input in, answer out."""

S2 = """Every payments codebase has a method like `LegacyRouter.fee`: an `if`/`else if` chain on the payment method, with special cases added over the years. Before you touch it, pin what it does. Write a test that runs the old code and the new code over a grid of inputs (every method, amounts including 0 and 1, several countries) and asserts that they agree. Michael Feathers calls this a characterization test. It records today's behavior, bugs included, so the refactor can't change it by accident.

Choose the grid for its edges, not its size. Include amount 0, amount 1 (where integer division rounds a percentage down to nothing), the home country and a foreign one, and every enum constant. Those are the places where a refactored rule most often drifts by a cent.

Then pick one of two shapes:

```java
// open set: one lambda per method, in a map that config or plug-ins could fill
static final Map<Method, FeeStrategy> STRATEGIES = new EnumMap<>(Map.of(
        Method.CARD,   p -> 30 + p.amountMinor() * 290 / 10_000,
        Method.SEPA,   p -> 25,
        Method.WALLET, p -> p.amountMinor() * 150 / 10_000));

// closed set: one switch, checked by the compiler
static long fee(Payment p) {
    return switch (p.method()) {
        case CARD -> 30 + p.amountMinor() * 290 / 10_000;
        case SEPA -> 25;
        case WALLET -> p.amountMinor() * 150 / 10_000;
    };
}
```

```kotlin
// open set: one lambda per method, in a map that config or plug-ins could fill
val strategies: Map<Method, (Payment) -> Long> = mapOf(
    Method.CARD to { p -> 30 + p.amountMinor * 290 / 10_000 },
    Method.SEPA to { _ -> 25L },
    Method.WALLET to { p -> p.amountMinor * 150 / 10_000 },
)

// closed set: one when, checked by the compiler
fun fee(p: Payment): Long = when (p.method) {
    Method.CARD -> 30 + p.amountMinor * 290 / 10_000
    Method.SEPA -> 25
    Method.WALLET -> p.amountMinor * 150 / 10_000
}
```

A map of strategies suits an **open** set: methods loaded from config, PSP plug-ins, rules a merchant can switch on. A `switch` or `when` with no default suits a **closed** set you own, like your `Method` enum.

You see the difference the day someone adds `CRYPTO` to the enum. The switch stops compiling: "the switch expression does not cover all possible input values", or in Kotlin, "'when' expression must be exhaustive". The map compiles, ships, and throws on the first crypto payment: a `NullPointerException` from `EnumMap.get` in Java, or `NoSuchElementException: Key CRYPTO is missing in the map` from Kotlin's `getValue`. If you do choose a map for a closed set, add a startup check that every constant has an entry, so the failure moves from the first customer to the deploy.

Neither shape needs a class per payment method. The lambdas are the strategies."""

S3 = """Every call to a PSP needs the same wrapping: start a timer, make the call, note the outcome, record it. Template Method puts that skeleton in a base class as a `final` method and leaves holes, called hooks, for subclasses to fill:

```java
abstract class OutboundCall<T> {
    public final T execute() {                         // the skeleton: subclasses can't change it
        long start = System.nanoTime();
        try {
            return doCall();                           // hook 1: the varying step
        } finally {
            metrics.record(name(), System.nanoTime() - start);
        }
    }
    protected abstract String name();                  // hook 2
    protected abstract T doCall();
}

final class CaptureCall extends OutboundCall<String> {
    protected String name() { return "psp.capture"; }
    protected String doCall() { return psp.capture(authId); }
}
```

```kotlin
abstract class OutboundCall<T> {
    fun execute(): T {                                 // final by default in Kotlin: subclasses can't change it
        val start = System.nanoTime()
        try {
            return doCall()                            // hook 1: the varying step
        } finally {
            metrics.record(name(), System.nanoTime() - start)
        }
    }
    protected abstract fun name(): String              // hook 2
    protected abstract fun doCall(): T
}

class CaptureCall(private val authId: String) : OutboundCall<String>() {
    override fun name() = "psp.capture"
    override fun doCall() = psp.capture(authId)
}
```

The base class owns the order, and because `execute` is final, no subclass can skip the timer. The JDK uses the shape: to build an unmodifiable list, you extend `AbstractList` and write only `get` and `size`; the rest of `List` is a skeleton built on those two hooks.

Inheritance is the cost. A subclass depends on every detail of its parent, and a parent that changes when it calls its hooks can break subclasses it has never seen. That is the fragile base class problem. The sharpest edge is a base-class constructor that calls a hook. A subclass assigns its own fields only after the base constructor returns, so the hook runs on a half-built object. In Java, the field reads as `null`. In Kotlin, the same code reads `null` from `private val psp: String`, a property the type system promises is never null, and kotlinc compiles it without a warning.

Never call an overridable method from a constructor. Compute such values lazily, or pass them up to the base constructor as arguments."""

S4 = """The modern answer keeps the skeleton and drops the subclass. Write the skeleton as a function and take the varying step as a lambda:

```java
static <T> T timed(String name, Metrics metrics, Supplier<T> body) {
    long start = System.nanoTime();                    // setup
    try {
        return body.get();                             // the caller's code
    } finally {
        metrics.record(name, System.nanoTime() - start);   // teardown, always
    }
}

String captured = timed("psp.capture", metrics, () -> psp.capture(authId));
```

```kotlin
inline fun <T> timed(name: String, metrics: Metrics, body: () -> T): T {
    val start = System.nanoTime()                      // setup
    try {
        return body()                                  // the caller's code, inlined: no lambda object
    } finally {
        metrics.record(name, System.nanoTime() - start)    // teardown, always
    }
}

val captured = timed("psp.capture", metrics) { psp.capture(authId) }
```

This is **execute around**: the function runs the setup and the teardown, and calls your code in the middle. You use it every day. `try`-with-resources is execute around built into Java. Kotlin's standard library is full of it: `use {}` closes a resource, `synchronized(lock) {}` takes and releases a monitor, and `measureTimeMillis {}` times a block.

Kotlin makes the function version cheaper than Java's. The compiler copies the body of an `inline` function, lambda included, into each call site, so no lambda object is created, and a `return` inside the block returns from the enclosing function. Java's `Supplier` has a different limit: it can't throw checked exceptions, so wrapping an SDK call that throws `IOException` needs your own functional interface with a `throws` clause. Kotlin has no checked exceptions, so `timed { sdk.call() }` just works.

Prefer the function. It composes (`timed("psp.capture") { retrying(3) { psp.capture(id) } }`), it needs no class per call site, and it can't hit the constructor trap, because there is no constructor. Keep Template Method for skeletons with many hooks, such as `AbstractList`, and make the template method `final`."""

L = {
 "id": "pat-07",
 "title": "Strategy and Template Method",
 "minutes": 37,
 "goal": "By the end you can pass algorithms as lambdas and comparators, refactor an if/else router into a strategy map or an exhaustive switch behind a characterization test, and replace a Template Method base class with an execute-around function.",
 "warmup": {
  "q": "Fees are priced two ways: through an `EnumMap<Method, FeeStrategy>`, and through a `switch` expression over `Method` with no `default`. A teammate adds `CRYPTO` to the `Method` enum and builds. What happens?",
  "options": ["Both versions fail to compile", "The switch fails to compile; the map compiles and throws on the first crypto payment", "The map fails to compile; the switch throws at runtime", "Both compile, and crypto payments are charged 0"],
  "answer": 1,
  "why": "A switch expression over an enum with no `default` must cover every constant, so javac reports \"the switch expression does not cover all possible input values\" right where the rule is missing. The map has no idea which keys should exist: `EnumMap.get(CRYPTO)` returns null, and calling `.fee` on it throws in production. That difference decides which shape fits which job."
 },
 "sections": [
  {
   "h": "A strategy is a function you pass in",
   "body": S1,
   "try": {
    "title": "Rank PSPs three ways",
    "minutes": 4,
    "steps": [
     "Read `StrategyDemo.java` (or `StrategyDemo.kt`) and predict the three lines. Equal fees keep their original order, because the JDK's sort is stable.",
     "Run it with the command below.",
     "Add a fourth quote at the end of the list, `new Quote(\"Bluefin\", 25, 150)` (`PspQuote(\"Bluefin\", 25, 150)` in Kotlin). Predict all three lines again, then run."
    ],
    "code": code("java", "StrategyDemo.java", "StrategyDemo", "kotlin", "StrategyDemo.kt", "StrategyDemoKt"),
    "expect": "`cheapest: [Adyx, Northpay, Kestrel]`, `fastest: [Kestrel, Northpay, Adyx]`, `cheapest, then fastest: [Adyx, Kestrel, Northpay]`. With Bluefin: `[Adyx, Bluefin, Northpay, Kestrel]`, `[Kestrel, Bluefin, Northpay, Adyx]` and `[Bluefin, Adyx, Kestrel, Northpay]`. Three algorithms, zero classes: each strategy is one expression."
   },
   "refs": [
    {"title": "Comparator (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Comparator.html", "kind": "docs"}
   ]
  },
  {
   "h": "Refactor the if/else router, after pinning what it does",
   "body": S2,
   "try": {
    "title": "Add a payment method and see who notices",
    "minutes": 5,
    "steps": [
     "Run `RouterDemo` in either language: the map and the switch agree on all three methods.",
     "Add `CRYPTO` to the enum (`PayMethod`). Predict which part fails, and when, then run.",
     "Add the missing branch, `case CRYPTO -> 0;` in Java or `PayMethod.CRYPTO -> 0` in Kotlin. Predict, then run again. Remove `CRYPTO` when you're done."
    ],
    "code": code("java", "RouterDemo.java", "RouterDemo", "kotlin", "RouterDemo.kt", "RouterDemoKt"),
    "expect": "With `CRYPTO` added, the build fails: javac says `the switch expression does not cover all possible input values`, kotlinc says `'when' expression must be exhaustive. Add the 'CRYPTO' branch or an 'else' branch.` After you add the branch, three lines print and then `CRYPTO  switch=0` dies: Java throws `NullPointerException` because `Map.get` returned null, Kotlin throws `NoSuchElementException: Key CRYPTO is missing in the map.` The compiler found one gap; only a runtime crash found the other."
   },
   "refs": [
    {"title": "Conditions and loops: when (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Template Method: a skeleton with holes for subclasses",
   "body": S3,
   "try": {
    "title": "Watch a hook run too early",
    "minutes": 4,
    "steps": [
     "Read `TemplateHookDemo.java` (or `.kt`). The base constructor builds `label` by calling `name()`. Predict the label the template version prints.",
     "Run it with the command below and compare the two versions.",
     "Fix the template without changing `ChargeCall`: delete the `label` field and build the label inside `execute()` instead. Run again."
    ],
    "code": code("java", "TemplateHookDemo.java", "TemplateHookDemo", "kotlin", "TemplateHookDemo.kt", "TemplateHookDemoKt"),
    "expect": "The template prints `start outbound charge via null`: `name()` ran inside the base constructor, before `ChargeCall` had assigned `psp`. Kotlin prints the same `null` from a property declared as non-null `String`, with no compiler warning. The function version prints `charge via northpay`. After the fix, the template prints it too, because `name()` now runs only when the object is complete."
   },
   "refs": [
    {"title": "AbstractList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/AbstractList.html", "kind": "docs"}
   ]
  },
  {
   "h": "Execute around: pass the hole in as a function",
   "body": S4,
   "figure": {"svg": FIG, "caption": "The same skeleton both ways. Template Method fills the hole with a subclass; execute around takes it as a lambda from the call site."},
   "refs": [
    {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Strategy is the route setting on a satnav: fastest, shortest, avoid tolls. The satnav still plans the trip; you swap the one rule it uses to rank roads. Template Method is a printed form with blanks: the form fixes the order of the questions, and each department fills in its own answers. Execute around is a waffle iron: it heats up, times the bake and switches off, and you pour in whatever batter you like. The analogy breaks at the waffle iron's plug. A real appliance can't forget to switch off, but a hand-written execute-around function can, which is why the teardown belongs in a `finally` block.",
 "in_your_world": "Kafka already runs on strategies: the producer's `partitioner.class` names a `Partitioner` implementation, and the client calls it for every record. In your own services, the PSP router is the strategy you own: choose PSPs with a comparator over quotes, and price with a map or a switch depending on whether the set is yours. Temporal's `RetryOptions` is a back-off strategy passed as data. Execute around is the shape for everything that wraps a call in your Quarkus services: timing a PSP call, putting a payment id in the logging MDC for a block, running a block in a transaction. Write those as small higher-order functions, `inline` in Kotlin, instead of a base class every client must extend.",
 "mistake": "The most common mistake is adding `default -> 0` (or `else -> 0`) to a switch over your own enum \"to be safe\". It feels defensive, and it silences the one check that mattered: when `CRYPTO` arrives, the compiler no longer lists the switches that need a rule, and crypto payments are priced at zero until finance notices. The map version has the same hole in a different place, a null lookup on the first crypto payment. For a closed set you own, leave the default out and let the build fail. Keep a `default` for open sets you don't control, such as config strings or vendor codes, and make it throw.",
 "compare": {
  "title": "An execute-around timer for SDK calls",
  "java": {"title": "Psp.java", "src": """// Supplier can't throw checked exceptions, so a wrapper for SDK calls needs its own interface
@FunctionalInterface
interface IoCall<T> {
    T call() throws IOException;
}

final class Psp {
    static <T> T timed(String name, Map<String, Long> metrics, IoCall<T> body) throws IOException {
        long start = System.nanoTime();
        try {
            return body.call();
        } finally {
            metrics.merge(name, System.nanoTime() - start, Long::sum);
        }
    }

    static String captureOrNull(Map<String, Long> metrics, PspSdk sdk, String authId) throws IOException {
        String ref = timed("psp.capture", metrics, () -> sdk.capture(authId));
        return ref.isEmpty() ? null : ref;          // a lambda can't return from captureOrNull itself
    }
}"""},
  "kotlin": {"title": "Psp.kt", "src": """// inline: the block is pasted into the caller, so no lambda object and no checked-exception plumbing
inline fun <T> timed(name: String, metrics: MutableMap<String, Long>, body: () -> T): T {
    val start = System.nanoTime()
    try {
        return body()
    } finally {
        metrics.merge(name, System.nanoTime() - start) { a, b -> a + b }
    }
}

fun captureOrNull(metrics: MutableMap<String, Long>, sdk: PspSdk, authId: String): String? {
    val ref = timed("psp.capture", metrics) {
        sdk.capture(authId).ifEmpty { return null }   // non-local return: leaves captureOrNull, the finally still records
    }
    return ref
}"""},
  "note": "The skeleton is identical: read the clock, run the caller's block, record in `finally`. Three things differ. Java's standard functional interfaces can't throw checked exceptions, so an SDK that throws `IOException` forces you to declare `IoCall` with a `throws` clause; Kotlin has no checked exceptions. Kotlin's `inline` copies `timed` and the block into each call site, so there is no lambda object, and `return null` inside the block returns from `captureOrNull` itself while the `finally` still runs. And an inline block may call suspend functions when the caller is a suspend function, which a Java lambda can't do. Neither language needs Template Method for this; the function is the whole pattern."
 },
 "worked": {
  "title": "Turn a back-off if/else into strategies, without changing behavior",
  "steps": [
   {"say": "A retry helper reads the back-off policy name from config and decides the delay on every attempt. Spot two problems before reading on.",
    "code": """// config: psp.backoff=exponential  (or "fixed", "none")
Duration delayBeforeRetry(String policy, int attempt) {
    if (policy.equals("fixed")) {
        return Duration.ofMillis(200);
    } else if (policy.equals("exponential")) {
        long ms = 100L << (attempt - 1);                 // 100, 200, 400, ...
        return Duration.ofMillis(Math.min(ms, 5_000));
    } else if (policy.equals("none")) {
        return Duration.ZERO;
    }
    return Duration.ofMillis(200);                       // a typo in config silently means "fixed"
}""", "lang": "java",
    "alt_code": """// config: psp.backoff=exponential  (or "fixed", "none")
fun delayBeforeRetry(policy: String, attempt: Int): Duration =
    if (policy == "fixed") {
        Duration.ofMillis(200)
    } else if (policy == "exponential") {
        val ms = 100L shl (attempt - 1)                  // 100, 200, 400, ...
        Duration.ofMillis(minOf(ms, 5_000))
    } else if (policy == "none") {
        Duration.ZERO
    } else {
        Duration.ofMillis(200)                           // a typo in config silently means "fixed"
    }""", "alt_lang": "kotlin"},
   {"say": "The policy is chosen again on every attempt, and a typo like `exponentail` quietly becomes \"fixed\". Fix neither yet. First pin today's behavior with a characterization test, so the refactor can't change a delay by accident.",
    "code": """@ParameterizedTest
@CsvSource({"fixed,1,200", "fixed,4,200", "exponential,1,100", "exponential,3,400", "exponential,9,5000", "none,2,0"})
void pinned(String policy, int attempt, long expectedMs) {
    assertThat(delayBeforeRetry(policy, attempt)).isEqualTo(Duration.ofMillis(expectedMs));
}""", "lang": "java",
    "alt_code": """@ParameterizedTest
@CsvSource("fixed,1,200", "fixed,4,200", "exponential,1,100", "exponential,3,400", "exponential,9,5000", "none,2,0")
fun pinned(policy: String, attempt: Int, expectedMs: Long) {
    assertThat(delayBeforeRetry(policy, attempt)).isEqualTo(Duration.ofMillis(expectedMs))
}""", "alt_lang": "kotlin"},
   {"say": "Now give the decision a type with one method, and a factory for each policy. Each factory returns a lambda: a complete strategy.",
    "code": """@FunctionalInterface
interface Backoff {
    Duration delay(int attempt);                                        // 1. one decision, one method

    static Backoff fixed(Duration d) { return attempt -> d; }
    static Backoff exponential(Duration base, Duration max) {
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
        fun exponential(base: Duration, max: Duration) = Backoff { attempt ->
            minOf(base.multipliedBy(1L shl (attempt - 1)), max)
        }
        val NONE = Backoff { Duration.ZERO }
    }
}""", "alt_lang": "kotlin"},
   {"say": "Choose the strategy once, at startup. Here a `default` is right, because config strings are an open set you don't control, and it throws, so a typo fails the deploy. Point the pinned test at `fromConfig(policy).delay(attempt)`: it still passes.",
    "code": """static Backoff fromConfig(String name) {                                 // 2. choose once, at startup
    return switch (name) {
        case "fixed" -> Backoff.fixed(Duration.ofMillis(200));
        case "exponential" -> Backoff.exponential(Duration.ofMillis(100), Duration.ofSeconds(5));
        case "none" -> Backoff.NONE;
        default -> throw new IllegalArgumentException("unknown psp.backoff: " + name);   // 3. a typo fails the deploy
    };
}

Backoff backoff = fromConfig(config.backoff());                          // 4. the retry loop calls backoff.delay(n)""", "lang": "java",
    "alt_code": """fun fromConfig(name: String): Backoff = when (name) {                    // 2. choose once, at startup
    "fixed" -> Backoff.fixed(Duration.ofMillis(200))
    "exponential" -> Backoff.exponential(Duration.ofMillis(100), Duration.ofSeconds(5))
    "none" -> Backoff.NONE
    else -> throw IllegalArgumentException("unknown psp.backoff: $name") // 3. a typo fails the deploy
}

val backoff = fromConfig(config.backoff)                                 // 4. the retry loop calls backoff.delay(n)""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Refactor the fee router twice, and replace a template with a function",
  "minutes": 13,
  "files": [f"{lab}/main/{J}/Fees.java", f"{lab}/main/{J}/Outbound.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l07.*'",
  "steps": [
   "Read `Method`, `Payment` and `LegacyRouter`. They are given, and `LegacyRouter.fee` is the specification. Run the tests: all eight fail.",
   "Write `Fees.strategies()`: a `new EnumMap<>(Method.class)` with one lambda per method. Copy the rules from `LegacyRouter`, including the cross-border card surcharge. Then write `feeByMap` as one line.",
   "Write `feeBySwitch` as a switch expression over `p.method()` with no `default`.",
   "Write `cheapestThenFastest` from `Comparator.comparingLong` and its `then...` methods.",
   "Write `Outbound.timed`: one clock read before, the body in a `try`, the outcome noted in a `catch` that rethrows, one record added in `finally`. Compare it with the given `OutboundCall`.",
   "Run the tests until all eight pass. Then add `CRYPTO` to `Method` and build: which of your two refactors complains? Remove it again."
  ],
  "hints": [
   "Inside the card lambda, `(p.country().equals(\"DE\") ? 0 : p.amountMinor() * 100 / 10_000)` is the surcharge. Keep the integer division exactly as the legacy code has it, or the parity test finds the difference.",
   "`Comparator.comparingLong(Quote::feeMinor).thenComparingLong(Quote::p95Millis).thenComparing(Quote::psp)` sorts by fee, then latency, then name.",
   "Declare `String outcome = \"ok\";` before the `try`, set it to `e.getClass().getSimpleName()` in `catch (RuntimeException e)`, rethrow with `throw e;`, and add the `CallRecord` in `finally`, so success and failure each log exactly once."
  ],
  "done_when": "All eight tests in `StrategyTemplateTest` pass."
 },
 "drill": {
  "title": "A retry wrapper from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `retrying(attempts, body)` as an execute-around function: it runs `body` up to `attempts` times, returns the first success, and rethrows the last failure. In Kotlin make it `inline`. Then say which PSP call you would never pass to it without an idempotency key.",
  "answer": {"lang": "java", "src": """static <T> T retrying(int attempts, Supplier<T> body) {
    RuntimeException last = null;
    for (int i = 1; i <= attempts; i++) {
        try {
            return body.get();                 // the caller's step, run again on failure
        } catch (RuntimeException e) {
            last = e;
        }
    }
    throw last;                                 // never pass a charge without an idempotency key
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
    throw last!!                                // never pass a charge without an idempotency key
}"""}}
 },
 "recap": [
  "Strategy is an algorithm the client picks and passes in. In modern Java and Kotlin, a lambda, method reference or function type is the strategy; `Comparator.comparing` is the JDK's own example.",
  "Before refactoring an if/else chain, pin its behavior with a characterization test over a grid of inputs.",
  "Use a map of strategies for open sets (config, plug-ins) and a `switch` or `when` with no default for closed sets you own. A missing map entry fails at runtime; a missing case fails to compile.",
  "Template Method is a final skeleton in a base class with hooks for subclasses. Never call a hook from a constructor: the subclass's fields are still unset, even Kotlin non-null `val`s.",
  "Execute around replaces most Template Methods: the skeleton is a function and the varying step is a lambda, as in try-with-resources, `use`, `synchronized` and `measureTimeMillis`.",
  "Kotlin `inline` makes execute around free of lambda objects and allows non-local `return`; Java's `Supplier` can't throw checked exceptions."
 ],
 "quiz": [
  {"q": "A team prices with `Map<Method, FeeStrategy>` built from config, and also has a `switch` over `Method` with no default in the invoicing code. Someone adds `CRYPTO` to `Method`. Which statement is true?",
   "options": ["The map fails to compile; the switch throws at runtime", "The switch fails to compile; the map compiles and fails on the first crypto payment", "Both fail to compile", "Both compile, and crypto payments cost 0"],
   "answer": 1,
   "why": "Only the switch tells the compiler which constants must be handled, so only the switch breaks the build. The map has no idea `CRYPTO` should be a key, so `get` returns null in production. With a map over a closed set, add a startup check that every constant has an entry."},
  {"q": "Quotes: Atlas (fee 30, p95 200 ms), Bluefin (fee 25, p95 900 ms), Cobalt (fee 30, p95 120 ms). In what order does `Comparator.comparingLong(Quote::feeMinor).thenComparingLong(Quote::p95Millis)` sort them?",
   "options": ["Bluefin, Cobalt, Atlas", "Bluefin, Atlas, Cobalt", "Cobalt, Atlas, Bluefin", "Atlas, Cobalt, Bluefin"],
   "answer": 0,
   "why": "The first comparator puts the 25 fee first: Bluefin. Atlas and Cobalt tie on fee, so the second comparator breaks the tie by latency: Cobalt (120 ms) before Atlas (200 ms). The tempting \"Bluefin, Atlas, Cobalt\" ignores the tie-breaker and keeps the original order."},
  {"q": "A base class sets `label = \"outbound \" + name();` in its constructor. The subclass `ChargeCall(String psp)` assigns `this.psp = psp` and implements `name()` as `\"charge via \" + psp`. What is the label of `new ChargeCall(\"northpay\")`?",
   "options": ["It throws `NullPointerException`", "`outbound charge via northpay`", "`outbound charge via null`", "It doesn't compile"],
   "answer": 2,
   "why": "The base constructor runs first and calls the overridden `name()` before `ChargeCall` has assigned `psp`, so `psp` is still null, and string concatenation turns null into \"null\". Nothing throws, which makes the bug easy to miss. Kotlin behaves the same even for a non-null `val psp: String`."},
  {"q": "At 30 call sites, code calls different PSP endpoints, and every call must be timed and logged in the same way. Which shape fits best?",
   "options": ["An abstract base class with a final `execute()` and one subclass per call site", "A `Map<String, Runnable>` holding all 30 calls", "A singleton that every call registers with", "A higher-order function, `timed(\"psp.capture\") { ... }`, `inline` in Kotlin, wrapped around each call"],
   "answer": 3,
   "why": "The skeleton is fixed and the middle varies per call site, which is execute around: one function, and each call site passes its own block. Thirty subclasses is Template Method's ceremony with its inheritance problems, and a map or a singleton doesn't wrap anything."},
  {"q": "From *Decorator and Proxy*: each method's base rule is a `FeeCalculator` stored in a `Map<Method, FeeCalculator>`. Ops now wants every fee capped at 5.00. Where does the cap go with the least code?",
   "options": ["Edit every lambda in the map to call `Math.min(..., 500)`", "Decorate each calculator once when you build the map: `calculators.replaceAll((m, c) -> c.cappedAt(500))`", "Add a `default -> 500` branch to the switch", "Make each strategy extend a `CappedCalculator` base class"],
   "answer": 1,
   "why": "Strategies and decorators combine: the map picks the rule, and wrapping each rule in `cappedAt(500)` adds the cap once, in one place. Editing every lambda copies the rule into each strategy, a `default` branch changes nothing for known methods, and a base class brings back the inheritance this lesson moves away from.",
   "from": "pat-05"}
 ],
 "flashcards": [
  {"front": "In modern Java or Kotlin, what is a strategy usually written as?", "back": "A lambda or method reference for a functional interface (`Comparator`, `FeeStrategy`), or a Kotlin function type such as `(Payment) -> Long`."},
  {"front": "You add a constant to an enum. What happens to a `switch` over it with no default, and to an `EnumMap` of strategies?", "back": "The switch fails to compile. The map compiles, and `get` returns null for the new key at runtime."},
  {"front": "Map of strategies or exhaustive switch: which for a closed set you own?", "back": "The switch (or `when`) with no default, so a new case is a compile error. Use the map for open sets: config, plug-ins."},
  {"front": "What is a characterization test?", "back": "A test that records what existing code does today, bugs included, so a refactor can prove it changed nothing."},
  {"front": "What is Template Method?", "back": "A final skeleton method in a base class that calls hook methods subclasses override."},
  {"front": "A base-class constructor calls an overridden method that reads a subclass field. What does it see?", "back": "The field's default: null or 0, because the subclass constructor hasn't run yet. In Kotlin even a non-null `val` reads as null."},
  {"front": "What is execute around?", "back": "A function that does the setup and teardown and takes the varying step as a lambda: try-with-resources, `use {}`, `synchronized(lock) {}`."}
 ],
 "terms": [
  {"term": "Strategy", "plain": "One interchangeable algorithm, passed in by the caller and used by the code that needs a decision."},
  {"term": "Characterization test", "plain": "A test that pins down what legacy code does now, so a refactor can't change it unnoticed."},
  {"term": "Template Method", "plain": "A base-class method that fixes the steps and lets subclasses fill in some of them."},
  {"term": "Hook", "plain": "An overridable method a template calls at a fixed point in its skeleton."},
  {"term": "Fragile base class", "plain": "When a change inside a parent class breaks subclasses that relied on how it worked."},
  {"term": "Execute around", "plain": "A function that wraps the caller's code with setup and teardown, taking that code as a lambda."},
  {"term": "Inline function", "plain": "A Kotlin function whose body, with its lambda arguments, is copied into each call site."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"Should our fee rules live in a `Map<Method, FeeStrategy>` or in a `switch` over `Method`?\" Explain how you decide, and what each version does on the day someone adds a new payment method.",
  "answer": "It depends on who owns the set of keys. If the set is closed and ours, like the `Method` enum, I use a switch (or `when`) with no default. When someone adds `CRYPTO`, the build fails at every switch that needs a rule, so nobody can ship without deciding the crypto fee. If the set is open, because rules come from config or plug-ins or merchants switch them on, a map of strategies fits, since the code can't know the keys at compile time. The map's weakness is that a missing entry only shows up at runtime: `EnumMap.get` returns null and the first crypto payment fails. If we use a map for an enum anyway, we add a startup check that every constant has an entry, so the deploy fails instead of a customer's payment. Either way, I'd pin the current behavior with a parity test against the old code before changing anything."
 },
 "deeper": {
  "minutes": 10,
  "body": """Strategy and State have the same structure: an object holds an interface and delegates to it. The difference is who chooses. The client picks a strategy and it stays put. A state object, or a transition function, picks the next state itself as events arrive. Lesson 9 of this track, *State and Chain of Responsibility*, builds the payment lifecycle that way.

Java can do execute around without lambdas. Make the setup a constructor and the teardown `close()`, and try-with-resources does the rest: `try (var t = metrics.timer(\"psp.capture\")) { return psp.capture(id); }`. This form lets checked exceptions pass through untouched and needs no functional interface, which is why many tracing and metrics libraries offer a closeable span or timer. The cost is that the caller must remember the `try`.

Kotlin's `inline` has limits worth knowing. An inlined lambda can't be stored or passed to a non-inline function, because it doesn't exist as an object. Mark such a parameter `noinline`. If the lambda runs in another context (a different thread, a callback), mark it `crossinline`, which forbids non-local returns inside it. And large inline functions grow every call site, so keep them small: the skeleton inline, the heavy lifting in a normal function it calls.

Spring's `JdbcTemplate` and `TransactionTemplate` carry the pattern's name, but they take your code as a callback, which is the execute-around shape from this lesson. The name stuck from an era when callbacks needed anonymous inner classes."""
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
