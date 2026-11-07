import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l01"
K = "kotlin/workbench/patterns/l01"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l01.{cls}"

FIG = """<svg viewBox="0 0 680 270" role="img" aria-label="Three columns: patterns the language absorbed, patterns frameworks absorbed, and patterns you still design by hand">
<rect class="box-a" x="10" y="20" width="210" height="236" rx="8"/>
<rect class="box-b" x="235" y="20" width="210" height="236" rx="8"/>
<rect class="box" x="460" y="20" width="210" height="236" rx="8"/>
<text class="t t-a" x="115" y="48" text-anchor="middle">the language</text>
<text class="t t-b" x="340" y="48" text-anchor="middle">a framework</text>
<text class="t" x="565" y="48" text-anchor="middle">you, by hand</text>
<line class="ln-d" x1="25" y1="62" x2="205" y2="62"/>
<line class="ln-d" x1="250" y1="62" x2="430" y2="62"/>
<line class="ln-d" x1="475" y1="62" x2="655" y2="62"/>
<text class="t-s" x="115" y="90" text-anchor="middle">Strategy: a lambda</text>
<text class="t-s" x="115" y="116" text-anchor="middle">Command: a lambda or record</text>
<text class="t-s" x="115" y="142" text-anchor="middle">Template Method: a function</text>
<text class="t-s" x="115" y="168" text-anchor="middle">State, Visitor: sealed types</text>
<text class="t-s" x="115" y="194" text-anchor="middle">Builder: named arguments</text>
<text class="t-s" x="115" y="220" text-anchor="middle">Singleton: enum, object</text>
<text class="t-s" x="115" y="246" text-anchor="middle">Decorator: Kotlin by</text>
<text class="t-s" x="340" y="90" text-anchor="middle">Proxy: Spring, Quarkus</text>
<text class="t-s" x="340" y="116" text-anchor="middle">Chain: servlet filters</text>
<text class="t-s" x="340" y="142" text-anchor="middle">Chain: HTTP interceptors</text>
<text class="t-s" x="340" y="168" text-anchor="middle">Observer: Flow, Reactor</text>
<text class="t-s" x="340" y="194" text-anchor="middle">Decorator: Resilience4j</text>
<text class="t-s" x="565" y="90" text-anchor="middle">Adapter</text>
<text class="t-s" x="565" y="116" text-anchor="middle">Facade</text>
<text class="t-s" x="565" y="142" text-anchor="middle">Bridge</text>
<text class="t-s" x="565" y="168" text-anchor="middle">Composite</text>
<text class="t-s" x="565" y="194" text-anchor="middle">Mediator</text>
<text class="t-s" x="565" y="220" text-anchor="middle">Flyweight</text>
</svg>""".replace("\n", "")

S1 = """A design pattern is a name for a design that keeps showing up: the problem, the shape of the solution, and what it costs you. It is a word in a shared vocabulary. It is not a class template to paste.

The 1994 "Gang of Four" book listed 23 patterns, written for C++ and Smalltalk. Java at the time had no lambdas, no records and no sealed types, and many of those patterns were workarounds for exactly that. The names are still worth knowing. In a code review, "put a decorator around the issuer client" is a whole design in a few words. And you need the names to recognise a pattern when a language feature or a framework hands it to you under another name.

In Java 21+ and Kotlin 2.x, the 23 sort into three groups. This track follows them.

- The language absorbed them. Strategy, Command and Template Method become function values. State and Visitor become a sealed type plus an exhaustive `switch` or `when`. A sealed type lists all its subtypes in one place, so the compiler knows every case, and an exhaustive switch is one the compiler has checked covers them all. Builder mostly becomes Kotlin's named and default arguments. Singleton becomes an `enum` or a Kotlin `object`. Decorator becomes Kotlin's `by` delegation, where the compiler writes the forwarding methods for you.
- A framework absorbed them. Proxy lives inside Spring and Quarkus. Chain of Responsibility is a servlet filter chain or an HTTP client interceptor. Observer is Kotlin `Flow`, Reactor and `java.util.concurrent.Flow`.
- You still design them by hand. Adapter, Facade, Bridge, Composite, Mediator and Flyweight are about how you cut up your own domain, and no feature does that for you.

The intent of an absorbed pattern survives. Strategy still means "swap the algorithm without touching the caller". What changed is the price. A strategy used to be an interface and three classes. Now it is a lambda in a map, so you use it ten times more often and stop calling it a pattern.

Brian Goetz, Java's language architect, gave the strongest version of this in a 2018 design note on pattern matching: with powerful enough pattern matching, "the Visitor pattern is almost completely unnecessary". The same note says this does not make inheritance and virtual methods wrong. That is the position of this track too. Learn the intent, then reach for the cheapest feature that delivers it, and know when the feature is not enough."""

S2 = """A singleton is a class with exactly one instance and one place to get it. The JDK has its own: the `Runtime` Javadoc says every Java application has a single instance of `Runtime`, and an application cannot create its own.

The "one" is easy. The hard part is "one, created lazily, by many threads at once". The naive version is the check-then-act race from *Race conditions: why count++ lies*:

```java
static FxRates instance;
static FxRates getInstance() {
    if (instance == null) instance = new FxRates();   // two threads can both see null
    return instance;
}
```

```kotlin
private var instance: FxRates? = null
fun fxRates(): FxRates {
    if (instance == null) instance = FxRates()        // the same race in Kotlin
    return instance!!
}
```

If loading `FxRates` takes 20 ms and eight request threads arrive together, all eight see `null` and you build eight. Here are the correct versions, in the order I reach for them.

```java
enum IdGenerator {                      // 1. enum: the JVM makes exactly one INSTANCE
    INSTANCE;
    private final AtomicLong next = new AtomicLong();
    long nextId() { return next.incrementAndGet(); }
}

final class FxRates {                   // 2. holder: lazy, no lock on the fast path
    private FxRates() { }
    private static final class Holder { static final FxRates INSTANCE = new FxRates(); }
    static FxRates getInstance() { return Holder.INSTANCE; }
}
```

```kotlin
enum class IdGenerator {                // 1. enum works the same in Kotlin
    INSTANCE;
    private val next = AtomicLong()
    fun nextId() = next.incrementAndGet()
}

class FxRates private constructor() {   // 2. holder: a private object nested in the companion
    companion object {
        private object Holder { val INSTANCE = FxRates() }
        fun getInstance(): FxRates = Holder.INSTANCE
    }
}
```

The enum is what Effective Java (item 3) calls the preferred approach. Serialization and reflection can't make a second instance, and you write no locking code. Use it when the object is cheap or needed at startup anyway.

The holder idiom is for an expensive object you want lazily. The JVM initializes the nested `Holder` class the first time anyone reads `Holder.INSTANCE`. Class initialization runs once, under a lock the JVM owns, so every later call is a plain static read.

The third tool is **double-checked locking** (DCL), from *Lazy init done right: double-checked locking and holders* in the memory model track. The holder only works for static fields. When the lazy value lives in an instance field, such as one cache per merchant or a registry your DI container creates, DCL is the answer:

```java
private volatile Map<String, String> table;
Map<String, String> table() {
    Map<String, String> t = table;       // one volatile read on the fast path
    if (t == null) {
        synchronized (lock) {
            t = table;                   // re-check: another thread may have won
            if (t == null) table = t = load();
        }
    }
    return t;
}
```

```kotlin
@Volatile private var table: Map<String, String>? = null
fun table(): Map<String, String> {
    table?.let { return it }             // one volatile read on the fast path
    synchronized(lock) {
        table?.let { return it }         // re-check: another thread may have won
        return load().also { table = it }
    }
}
```

Leave out `volatile` (`@Volatile` in Kotlin) and another thread can see a non-null reference to a map whose contents it can't see yet. That is the lab for this lesson."""

S3 = """Kotlin builds the singleton into the language. An `object` declaration defines a class and its one instance in a single step:

```kotlin
object IdGenerator {
    private val next = AtomicLong()
    fun nextId() = next.incrementAndGet()
}
```

```java
// what the Kotlin compiler writes for that object, give or take
public final class IdGenerator {
    public static final IdGenerator INSTANCE = new IdGenerator();
    private final AtomicLong next = new AtomicLong();
    private IdGenerator() { }
    public long nextId() { return next.incrementAndGet(); }
}
```

The Kotlin docs say the initialization of an object declaration is thread-safe and done on first access. Under the hood the compiler writes a class with a static `INSTANCE` field, set in its static initializer, as the Java twin shows. That is the same JVM mechanism as the holder idiom.

Two details trip people up. A `companion object` is initialized when its outer class is loaded, like a Java static initializer. And companion members are not static. They are instance members of the companion object, so Java callers write `Money.Companion.of(100)` unless you mark the function `@JvmStatic`.

For a lazy value inside a class, use `by lazy`. It has three modes, and they behave very differently:

| Mode | What it does | Use it for |
|---|---|---|
| `SYNCHRONIZED` (default) | takes a lock; the initializer runs once | anything with side effects |
| `PUBLICATION` | no lock; racing threads may each run the initializer, the first stored value wins | cheap, pure computations |
| `NONE` | no lock and no guarantee across threads | values one thread owns |

`PUBLICATION` is the trap. If the initializer opens a connection pool or starts a Kafka consumer, eight concurrent first reads can open eight pools. Seven are thrown away, and nobody closes them.

The default `lazy` is DCL written once, correctly, in the standard library. It also retries: if the initializer throws, the next access runs it again. In Kotlin, never write DCL by hand."""

S4 = """Most singletons in a backend service should not be hand-rolled at all. Here is why, in one test you can't write:

```java
class PaymentPricer {
    long priceMinor(Payment p) {
        double rate = FxRates.getInstance().rate(p.currency(), "EUR");   // hidden, global
        return Math.round(p.amountMinor() * rate);
    }
}
```

```kotlin
class PaymentPricer {
    fun priceMinor(p: Payment): Long {
        val rate = FxRates.rate(p.currency, "EUR")          // FxRates is an object: hidden, global
        return (p.amountMinor * rate).roundToLong()
    }
}
```

To test `priceMinor` with a fixed rate of 1.10 you need to control `FxRates`, and you can't. The instance is global, built once per JVM, and loads real rates. A test that changes its state leaks into the next test, so the suite passes or fails depending on order. Nothing in the constructor of `PaymentPricer` even tells a reader that it calls an FX service.

Pass the dependency in, typed as an interface:

```java
interface FxRates { double rate(String from, String to); }

class PaymentPricer {
    private final FxRates rates;
    PaymentPricer(FxRates rates) { this.rates = rates; }
    long priceMinor(Payment p) { return Math.round(p.amountMinor() * rates.rate(p.currency(), "EUR")); }
}
// in a test: new PaymentPricer((from, to) -> 1.10)
```

```kotlin
fun interface FxRates { fun rate(from: String, to: String): Double }

class PaymentPricer(private val rates: FxRates) {
    fun priceMinor(p: Payment): Long = (p.amountMinor * rates.rate(p.currency, "EUR")).roundToLong()
}
// in a test: PaymentPricer { _, _ -> 1.10 }
```

Production still wants exactly one `FxRates`. Let the container make it. In Quarkus, an `@ApplicationScoped` bean is created once per application, on first use. In Spring, singleton is the default scope. You get one instance, lazy creation and shutdown hooks, and the class stays a plain class that a test can construct with `new`.

A hand-written singleton still fits in a few places: stateless objects such as a comparator or a `data object` state in a sealed hierarchy, library code that can't assume a container, and state the JVM itself owns, like `Runtime`. Anything with I/O or configuration gets injected.

The lab's `CardNetworkRegistry` follows that rule. It is not a static singleton. Its loader comes in through the constructor, so the tests can pass a slow fake loader and count its calls. A container would make one per application, and DCL inside keeps the lazy load safe when eight threads ask at once.

Check yourself. Suppose the Kotlin `object FxRates` had a test hook, `FxRates.override(1.10)`, and one test called it and never reset it. A test in another class runs later in the same JVM and prices a payment. Which rate does it get, and why? (1.10. The `object` is one static `INSTANCE` for the whole JVM, as the previous section showed, so its state outlives the test that set it. An injected fake goes away with its test.)"""

L = {
 "id": "pat-01",
 "title": "Patterns in a modern language, and Singleton",
 "minutes": 35,
 "goal": "By the end you can say what a design pattern is and which ones modern Java and Kotlin absorbed, pick the right singleton form in each language, and prove a lazy instance is built once under contention.",
 "warmup": {
  "q": "A Kotlin service has `val rates by lazy(LazyThreadSafetyMode.PUBLICATION) { loadRates() }`. Eight request threads read `rates` for the first time at the same moment. How many times can `loadRates()` run?",
  "options": ["Exactly once, because `lazy` always takes a lock", "Up to eight times, but every thread ends up with the same value", "Up to eight times, and each thread may keep its own value", "Zero times until the main thread reads it first"],
  "answer": 1,
  "why": "`PUBLICATION` takes no lock. Every thread that finds the value missing runs the initializer, and the first result stored wins; the rest are thrown away. So `loadRates()` can run eight times while all callers see one value. The default mode, `SYNCHRONIZED`, is the one that runs it once. Threads keeping their own values is what `NONE` allows."
 },
 "sections": [
  {
   "h": "A pattern is a name for a design you keep meeting",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Most GoF patterns still have a job. What changed is who writes them: the language, a framework, or you."},
   "try": {
    "title": "Find five patterns in the JDK",
    "minutes": 4,
    "steps": [
     "Read `main` in `PatternsYouAlreadyUse` below (Java or Kotlin, they print the same). Write down what each of the six lines will print before you run anything.",
     "Run it from `labs/` with the command below.",
     "Name the pattern behind each line: singleton, flyweight, read-through view (proxy) or strategy. Which line surprised you?"
    ],
    "code": {"lang": "java", "title": "PatternsYouAlreadyUse.java", "src": read(f"{lab}/demo/{J}/PatternsYouAlreadyUse.java"),
             "run": demo("PatternsYouAlreadyUse"), "file": f"{lab}/demo/{J}/PatternsYouAlreadyUse.java",
             "alt": {"lang": "kotlin", "title": "PatternsYouAlreadyUse.kt", "src": read(f"{lab}/demo/{K}/PatternsYouAlreadyUse.kt"),
                     "run": demo("PatternsYouAlreadyUseKt"), "file": f"{lab}/demo/{K}/PatternsYouAlreadyUse.kt"}},
    "expect": "It prints `true`, `true`, `false`, `true`, `[p-1, p-2]` and `[p-3, p-9]`. Line 3 surprises most people: `Integer.valueOf` only caches -128 to 127, so two boxed 128s are different objects. Line 5 shows that `unmodifiableList` is a view that reads through to the list it wraps. It blocks writes through the view, and it is not a copy."
   },
   "refs": [
    {"title": "Pattern Matching for Java (Bierman and Goetz, design note)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md", "kind": "read"}
   ]
  },
  {
   "h": "Singleton in Java: enum, holder and double-checked locking",
   "body": S2,
   "try": {
    "title": "Build eight singletons by accident",
    "minutes": 4,
    "steps": [
     "Predict: when eight threads call the racy `getInstance` together, how many `FxRates` get built? And with the holder?",
     "Run `LazyRaceDemo` with the command below.",
     "Delete the `Thread.sleep(20)` line in the constructor (`FxRates` in Java, `SlowRates` in Kotlin) and run it three more times. Did the race go away?"
    ],
    "code": {"lang": "java", "title": "LazyRaceDemo.java", "src": read(f"{lab}/demo/{J}/LazyRaceDemo.java"),
             "run": demo("LazyRaceDemo"), "file": f"{lab}/demo/{J}/LazyRaceDemo.java",
             "alt": {"lang": "kotlin", "title": "LazyRaceDemo.kt", "src": read(f"{lab}/demo/{K}/LazyRaceDemo.kt"),
                     "run": demo("LazyRaceDemoKt"), "file": f"{lab}/demo/{K}/LazyRaceDemo.kt"}},
    "expect": "With the slow constructor, the racy version builds 8 instances and callers see 8 different objects. The holder (an `object` in the Kotlin twin) builds 1. Without the sleep, the racy count drops to 1, 3 or 4 and changes between runs. The race is still there; the window got smaller. A real config load is slow, which is why this shows up in production and not in your unit test."
   },
   "refs": [
    {"title": "Runtime (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Runtime.html", "kind": "docs"}
   ]
  },
  {
   "h": "Kotlin: object and lazy do the locking for you",
   "body": S3,
   "try": {
    "title": "Count the lazy initializer runs",
    "minutes": 4,
    "steps": [
     "Read `LazyModes.kt`. The Java twin writes each mode by hand, which shows what the modes really do. Predict both lines of output: how many initializer runs, and how many distinct instances, for each mode?",
     "Run it with the command below.",
     "Add `trial(LazyThreadSafetyMode.NONE)` at the end of `main` (in Java: `trial(\"NONE\", UnsafeLazy::new);`) and run it again. Predict first."
    ],
    "code": {"lang": "kotlin", "title": "LazyModes.kt", "src": read(f"{lab}/demo/{K}/LazyModes.kt"),
             "run": demo("LazyModesKt"), "file": f"{lab}/demo/{K}/LazyModes.kt",
             "alt": {"lang": "java", "title": "LazyModesJava.java", "src": read(f"{lab}/demo/{J}/LazyModesJava.java"),
                     "run": demo("LazyModesJava"), "file": f"{lab}/demo/{J}/LazyModesJava.java"}},
    "expect": "`SYNCHRONIZED` runs the initializer once and callers see 1 instance. `PUBLICATION` runs it 8 times, yet callers still see 1 instance, because only the first stored value is kept. `NONE` runs it 8 times and callers see 8 instances: each thread kept the map it built. No warning, no exception."
   },
   "refs": [
    {"title": "Object declarations and expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/object-declarations.html", "kind": "docs"},
    {"title": "LazyThreadSafetyMode (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/", "kind": "docs"}
   ]
  },
  {
   "h": "Inject the instance instead of fetching it",
   "body": S4,
   "refs": [
    {"title": "Contexts and dependency injection (Quarkus CDI reference)", "url": "https://quarkus.io/guides/cdi-reference", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A singleton is like the one cash vault in a bank branch. Everyone who needs cash goes to the same vault, and the manager makes sure nobody builds a second one. Lazy initialization is opening the vault only when the first customer asks. Double-checked locking is the manager glancing at the vault door from across the room, and only if it looks shut, walking over with the key and checking again, in case a colleague opened it in the meantime. The analogy breaks on testing: a bank can build a practice vault for training new staff, but a hard-coded `getInstance()` gives your tests no practice vault at all. That is why you inject it.",
 "in_your_world": "In a Quarkus payment service you rarely need `getInstance()`. The card-network config, the FX rate cache and the Kafka producer are `@ApplicationScoped` beans, so ArC makes one of each and injects them. Hand-written lazy state hides in smaller places: a per-merchant cache that loads fee schedules from Oracle on first use, a lazily built `ObjectMapper` in a shared library, a Temporal activity implementation that creates its issuer client the first time it runs. Each of those is a check-then-act waiting for two Kafka partitions to hit it in the same millisecond. Use the holder for statics, DCL or Kotlin `lazy` for instance fields, and keep the loader injectable so a test can count how many times it ran.",
 "mistake": "The common mistake is lazy initialization through a plain field: `if (cache == null) cache = load();`. It passes every single-threaded test, so it looks harmless. Under load, two threads see `null`, both run `load()`, and if `load()` opens connections or registers listeners, one copy leaks. People write it because the race never shows in tests and the fix looks like over-engineering. The fix is one of three idioms: the holder class for a static, double-checked locking with a `volatile` field for an instance field, or Kotlin `by lazy` in its default `SYNCHRONIZED` mode.",
 "compare": {
  "title": "One instance, and one lazy field, in Java and Kotlin",
  "java": {"title": "FeeSchedules.java", "src": """// singleton: the JVM's class-init lock does the work
enum IdGenerator {
    INSTANCE;
    private final AtomicLong next = new AtomicLong();
    long nextId() { return next.incrementAndGet(); }
}

// lazy instance field: double-checked locking
final class FeeSchedules {
    private final Supplier<Map<String, Long>> loader;
    private final Object lock = new Object();
    private volatile Map<String, Long> fees;

    FeeSchedules(Supplier<Map<String, Long>> loader) { this.loader = loader; }

    Map<String, Long> fees() {
        Map<String, Long> f = fees;
        if (f == null) {
            synchronized (lock) {
                f = fees;
                if (f == null) fees = f = Map.copyOf(loader.get());
            }
        }
        return f;
    }
}"""},
  "kotlin": {"title": "FeeSchedules.kt", "src": """// singleton: the language makes it
object IdGenerator {
    private val next = AtomicLong()
    fun nextId() = next.incrementAndGet()
}

// lazy instance field: the standard library does the locking
class FeeSchedules(loader: () -> Map<String, Long>) {
    val fees: Map<String, Long> by lazy { loader().toMap() }   // SYNCHRONIZED by default
}"""},
  "note": "A Kotlin `object` compiles to the same thing as a Java holder: a class with a static `INSTANCE` set in its static initializer, so the JVM's class-init lock guarantees one instance. `by lazy` replaces the whole DCL block (the `volatile` field, the lock object and the re-check), and it retries on the next access if the initializer throws. So Kotlin makes hand-written singletons and hand-written DCL unnecessary. It does not fix the design problem: a global `object` that does I/O is as hard to test as a Java static singleton, and the answer in both languages is to inject it."
 },
 "worked": {
  "title": "Turn a static singleton into an injected bean, then make its lazy load safe",
  "steps": [
   {"say": "A fee service reads merchant fee schedules through a global singleton. Before reading on, find what stops you from unit-testing `feeMinor`.",
    "code": """class FeeService {
    long feeMinor(String merchantId, long amountMinor) {
        long bps = FeeSchedules.getInstance().bpsFor(merchantId);   // global; loads from Oracle
        return amountMinor * bps / 10_000;
    }
}""", "lang": "java",
    "alt_code": """class FeeService {
    fun feeMinor(merchantId: String, amountMinor: Long): Long {
        val bps = FeeSchedules.bpsFor(merchantId)                   // an object: global; loads from Oracle
        return amountMinor * bps / 10_000
    }
}""", "alt_lang": "kotlin"},
   {"say": "The dependency is hidden and global. A test can't pass a fixed schedule, and anything the singleton caches leaks into the next test. Make the dependency visible: an interface, passed through the constructor. Now the test is one line.",
    "code": """interface FeeSchedules { long bpsFor(String merchantId); }

class FeeService {
    private final FeeSchedules schedules;                  // 1. the dependency is in the signature
    FeeService(FeeSchedules schedules) { this.schedules = schedules; }

    long feeMinor(String merchantId, long amountMinor) {
        return amountMinor * schedules.bpsFor(merchantId) / 10_000;
    }
}
// test: new FeeService(id -> 290).feeMinor("m-1", 10_000) == 290""", "lang": "java",
    "alt_code": """fun interface FeeSchedules { fun bpsFor(merchantId: String): Long }

class FeeService(private val schedules: FeeSchedules) {     // 1. the dependency is in the signature
    fun feeMinor(merchantId: String, amountMinor: Long): Long =
        amountMinor * schedules.bpsFor(merchantId) / 10_000
}
// test: FeeService { 290 }.feeMinor("m-1", 10_000) == 290L""", "alt_lang": "kotlin"},
   {"say": "Production still wants one schedule table, loaded on first use. The container makes one bean. Inside it the table is an instance field, so the holder idiom can't help: Java uses DCL. Why must the field be `volatile`? Answer before you read the comment on it. The Kotlin bean is four lines, because `by lazy` is the DCL block.",
    "code": """@ApplicationScoped
class OracleFeeSchedules implements FeeSchedules {
    private final Object lock = new Object();
    private volatile Map<String, Long> table;              // 2. volatile: readers see the whole map

    public long bpsFor(String merchantId) {
        Map<String, Long> t = table;                       // 3. fast path: one read, no lock
        if (t == null) {
            synchronized (lock) {
                t = table;                                 // 4. re-check under the lock
                if (t == null) table = t = loadFromOracle();
            }
        }
        return t.getOrDefault(merchantId, 290L);
    }

    private Map<String, Long> loadFromOracle() {
        return Map.of("m-1", 250L);                        // SELECT merchant_id, bps FROM fee_schedule
    }
}""", "lang": "java",
    "alt_code": """@ApplicationScoped
class OracleFeeSchedules(private val db: FeeDb) : FeeSchedules {
    // 2-4. by lazy (SYNCHRONIZED) is the volatile field, the lock and the re-check in one line
    private val table: Map<String, Long> by lazy { db.loadSchedules() }

    override fun bpsFor(merchantId: String) = table[merchantId] ?: 290L
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A lazy registry that loads once, and a harness that proves it",
  "minutes": 12,
  "files": [f"{lab}/main/{J}/CardNetworkRegistry.java", f"{lab}/main/{J}/Contention.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l01.*'",
  "steps": [
   "Run the tests. Seven of ten fail: the harness is a stub, and the registry runs its slow loader eight times when eight threads do the first lookup together.",
   "Write `Contention.distinctInstances`. Start the threads behind two latches (`ready` and `go`, as in *Race conditions: why count++ lies*), store each result in its own array slot, join every thread, then count the results in a set that compares with `==`.",
   "Fix `CardNetworkRegistry.table()` with double-checked locking: a `volatile` field, a private lock object, and a re-check inside `synchronized`. Keep the `Map.copyOf` around the loader's result.",
   "Run the tests until all ten pass, then twice more."
  ],
  "hints": [
   "`Collections.newSetFromMap(new IdentityHashMap<>())` is a `Set` that compares with `==`. A `HashSet` would count eight empty lists as one.",
   "Read the volatile field into a local once at the top and return the local. The fast path then costs one volatile read.",
   "If the loader throws inside the `synchronized` block, the field is still `null` and the next caller tries again. You get that for free as long as you assign the field only after `loader.get()` returns."
  ],
  "done_when": "All ten tests in `SingletonTest` pass, three runs in a row."
 },
 "drill": {
  "title": "The holder idiom and DCL from memory",
  "minutes": 5,
  "prompt": "Close this page. In the language you use most, write (a) a lazy singleton `FxRates` with the holder idiom, and (b) a lazy field `fees: Map<String, Long>` loaded by `loadFees()` with double-checked locking, by hand. Then compare with the answer, and read the other language's version too. Did you remember `volatile` (or `@Volatile`) and the second null check?",
  "answer": {"lang": "java", "src": """// (a) holder idiom: lazy, thread-safe, no lock on the fast path
final class FxRates {
    private FxRates() { }
    private static final class Holder { static final FxRates INSTANCE = new FxRates(); }
    static FxRates getInstance() { return Holder.INSTANCE; }
}

// (b) double-checked locking for an instance field
private final Object lock = new Object();
private volatile Map<String, Long> fees;

Map<String, Long> fees() {
    Map<String, Long> f = fees;          // one volatile read
    if (f == null) {
        synchronized (lock) {
            f = fees;                    // second check, under the lock
            if (f == null) fees = f = loadFees();
        }
    }
    return f;
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """// (a) Kotlin's holder: a private object nested in the companion (or just make FxRates an object)
class FxRates private constructor() {
    companion object {
        private object Holder { val INSTANCE = FxRates() }
        fun getInstance(): FxRates = Holder.INSTANCE
    }
}

// (b) double-checked locking by hand, for practice
private val lock = Any()
@Volatile private var fees: Map<String, Long>? = null

fun fees(): Map<String, Long> {
    fees?.let { return it }               // one volatile read
    synchronized(lock) {
        fees?.let { return it }           // second check, under the lock
        return loadFees().also { fees = it }
    }
}
// in real Kotlin code, all of (b) is: val fees: Map<String, Long> by lazy { loadFees() }"""}}
 },
 "recap": [
  "A design pattern is a name for a recurring design and its trade-offs. Use the names as vocabulary, not as class templates.",
  "Lambdas, sealed types, records and Kotlin delegation turned Strategy, Command, Template Method, State, Visitor, Builder and Decorator into a few lines. Proxy, Chain of Responsibility and Observer moved into frameworks.",
  "Java singletons: an `enum` when eager is fine, the holder idiom for a lazy static, double-checked locking with `volatile` for a lazy instance field.",
  "Kotlin `object` is a thread-safe singleton created on first access. `by lazy` defaults to `SYNCHRONIZED`; `PUBLICATION` may run the initializer once per racing thread.",
  "Prefer a container-managed instance (`@ApplicationScoped`, a Spring bean) injected through the constructor. A static `getInstance()` hides the dependency and leaks state between tests.",
  "Prove \"only one\" with contention: threads released together, a slow constructor, and a count by identity."
 ],
 "quiz": [
  {"q": "A Kotlin class has `val pool by lazy(LazyThreadSafetyMode.PUBLICATION) { HikariDataSource(config) }`. What can go wrong when traffic starts?",
   "options": ["Nothing, because the property is lazy", "Several threads can each open a pool; one is kept and the others are never closed", "Threads can see a half-built pool", "The first caller deadlocks"],
   "answer": 1,
   "why": "`PUBLICATION` lets every racing thread run the initializer and keeps the first stored result. A pool opens connections when it is built, so the discarded pools leak them. Drop the mode argument: the default `SYNCHRONIZED` runs the initializer once. A half-built value is not the risk here; the store itself is safe, only the side effects repeat."},
  {"q": "You need a stateless, process-wide ID formatter in Java, and it's fine to build it at startup. Which form is simplest and still correct?",
   "options": ["An `enum` with one constant, `INSTANCE`", "Double-checked locking on a `volatile` static field", "A static field set inside `getInstance()` behind `if (instance == null)`", "A `synchronized static getInstance()` method"],
   "answer": 0,
   "why": "An enum gives you exactly one instance, created when the class initializes, and serialization or reflection can't make another. DCL is for lazy instance fields and is overkill here. The plain `if` version races, and a `synchronized` getter is correct but takes a lock on every call for no benefit."},
  {"q": "Java code calls a Kotlin factory declared as `class Money { companion object { fun of(minor: Long) = Money() } }`. What does the Java caller write?",
   "options": ["`Money.of(100)`", "`Money.INSTANCE.of(100)`", "`Money.Companion.of(100)`", "`new Money().of(100)`"],
   "answer": 2,
   "why": "Companion members are instance members of the companion object, which Java sees as a static field called `Companion`. Mark `of` with `@JvmStatic` if you want `Money.of(100)` to work from Java. `INSTANCE` is the field for an `object` declaration, not for a companion."},
  {"q": "A test passes alone and fails in the full suite. The class under test reads `MetricsRegistry.INSTANCE.count(\"declines\")`. What is the likely cause and fix?",
   "options": ["JUnit runs tests in parallel, so add `synchronized`", "The enum gets created twice, so switch to the holder idiom", "The JIT caches the count, so make the field `volatile`", "The singleton keeps counts from earlier tests, so inject the registry and give each test its own"],
   "answer": 3,
   "why": "A global singleton lives as long as the JVM, so one test's counts leak into the next and the result depends on order. Passing the registry through the constructor lets each test build a fresh one. An enum is never created twice, and visibility is not the problem when the tests run on one thread."},
  {"q": "From *Lazy init done right* in the memory model track: in double-checked locking, what goes wrong if the `instance` field is not `volatile`?",
   "options": ["Two instances can be created", "The `synchronized` block can deadlock", "Another thread can see a non-null reference to an object whose fields it can't see yet", "Nothing on x86, so it is safe in practice"],
   "answer": 2,
   "why": "The re-check under the lock still prevents a second instance. The problem is the fast path, which reads the field without a lock. Without `volatile` there is no happens-before edge from the constructor's writes to that read, so a thread can see the reference before the fields. The JIT may reorder those writes on any CPU, x86 included, and the memory model allows it.",
   "from": "jmm-05"}
 ],
 "flashcards": [
  {"front": "What is a design pattern, in one sentence?", "back": "A name for a recurring design: the problem, the shape of the solution and its trade-offs. Vocabulary, not a class template."},
  {"front": "Which Java singleton form does Effective Java call the preferred approach?", "back": "A single-element `enum`: `enum IdGenerator { INSTANCE; ... }`. The JVM guarantees one instance, even across serialization and reflection."},
  {"front": "Why is the holder idiom lazy and thread-safe without a lock in your code?", "back": "The JVM initializes the nested `Holder` class on the first read of `Holder.INSTANCE`, exactly once, under its own class-initialization lock."},
  {"front": "When do you need double-checked locking instead of the holder idiom?", "back": "When the lazy value is an instance field (one per object, such as a per-merchant cache). The holder idiom only works for statics."},
  {"front": "`by lazy(LazyThreadSafetyMode.PUBLICATION) { init() }`: how many times can `init()` run?", "back": "Once per racing thread. The first stored value wins and every caller sees it, but the side effects repeat."},
  {"front": "Are Kotlin companion object members static on the JVM?", "back": "No. They are instance members of the companion (`Money.Companion.of()` from Java) unless you mark them `@JvmStatic`."},
  {"front": "Why does an injected bean usually beat `getInstance()`?", "back": "The dependency shows in the constructor, a test can pass a fake, and no global state leaks between tests. The container still makes only one."}
 ],
 "terms": [
  {"term": "Design pattern", "plain": "A named, reusable shape for solving a design problem that keeps coming back."},
  {"term": "Singleton", "plain": "A class with exactly one instance and one way to get it."},
  {"term": "Holder idiom", "plain": "A nested static class whose static field holds the instance. The JVM creates it once, on first access."},
  {"term": "Double-checked locking", "plain": "Read a volatile field without a lock, and only lock (and check again) when it is still null."},
  {"term": "Object declaration", "plain": "Kotlin's built-in singleton: a class and its one instance, created thread-safely on first access."},
  {"term": "Lazy thread-safety mode", "plain": "How `by lazy` handles racing first reads: SYNCHRONIZED runs once, PUBLICATION may run many times, NONE promises nothing."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add `public static FraudRules getInstance()` with a lazy `if (instance == null)` check to a Quarkus service. Explain what you'd suggest instead, and why.",
  "answer": "The plain null check is a check-then-act race: two request threads can both see null and both load the rules. Even a correct lazy singleton makes the dependency hidden and global, so tests can't pass their own rules, and state leaks from one test to the next. I'd make `FraudRules` an `@ApplicationScoped` bean and inject it through the constructor; the container builds one instance. If the rules should load lazily inside the bean, that's an instance field, so I'd use double-checked locking with a volatile field, or `by lazy` in Kotlin, and keep the loader injectable so a test can count how often it runs."
 },
 "deeper": {
  "minutes": 10,
  "body": """The JDK is getting its own lazy constant, slowly. JDK 25 shipped `StableValue` as a preview API (JEP 502). JDK 26 renamed it `LazyConstant` (JEP 526, second preview), and JDK 27 still has it in preview (JEP 531). `LazyConstant.of(() -> load())` promises that when several threads race, only one runs the computation. It can't hold `null`, and a failed computation is remembered: later calls throw without running it again. That is the opposite of Kotlin's `lazy`, which retries. Because it is a preview API that has already changed its name once, it stays out of this course's labs. If you want to try it, you need the matching JDK and `--enable-preview`.

Serialization can break a class-based singleton. Deserializing a `Serializable` singleton creates a new object unless the class defines `readResolve()` to return the existing instance. The JVM handles enums specially, which is one reason Effective Java prefers them.

Kotlin's `data object` gives a singleton a readable `toString()` and value-style `equals`. The Kotlin docs warn that serialization or reflection can still produce a second instance, so compare data objects with `==`, never with `===`. You'll use `data object` for states that carry no data, such as `Pending` in a payment state machine, in *State and Chain of Responsibility* (lesson 9 of this track)."""
 },
 "sources": [
  {"title": "Object declarations and expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/object-declarations.html"},
  {"title": "LazyThreadSafetyMode (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/"},
  {"title": "Pattern Matching for Java, Bierman and Goetz (Amber design note)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md"},
  {"title": "Effective Java 3e source, item 3: enum singleton", "url": "https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/enumtype/Elvis.java"}
 ]
}

out = ROOT / "content/lessons/pat-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
