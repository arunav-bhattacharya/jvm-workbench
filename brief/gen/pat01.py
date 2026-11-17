import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l01"
K = "kotlin/workbench/patterns/l01"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l01.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def pair_kj(kotlin, java):
    """A Kotlin fence first, then its Java twin (the site still shows Java first)."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 270" role="img" aria-label="Three columns: patterns the language absorbed, patterns libraries absorbed, and patterns you still design by hand">
<rect class="box-a" x="10" y="20" width="210" height="236" rx="8"/>
<rect class="box-b" x="235" y="20" width="210" height="236" rx="8"/>
<rect class="box" x="460" y="20" width="210" height="236" rx="8"/>
<text class="t t-a" x="115" y="48" text-anchor="middle">the language</text>
<text class="t t-b" x="340" y="48" text-anchor="middle">a library</text>
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
<text class="t-s" x="340" y="90" text-anchor="middle">Observer: Flow, Reactor</text>
<text class="t-s" x="340" y="116" text-anchor="middle">Proxy: JDK dynamic proxies</text>
<text class="t-s" x="340" y="142" text-anchor="middle">Decorator: java.io streams</text>
<text class="t-s" x="340" y="168" text-anchor="middle">Chain: request filters</text>
<text class="t-s" x="565" y="90" text-anchor="middle">Adapter</text>
<text class="t-s" x="565" y="116" text-anchor="middle">Facade</text>
<text class="t-s" x="565" y="142" text-anchor="middle">Bridge</text>
<text class="t-s" x="565" y="168" text-anchor="middle">Composite</text>
<text class="t-s" x="565" y="194" text-anchor="middle">Mediator</text>
<text class="t-s" x="565" y="220" text-anchor="middle">Flyweight</text>
</svg>""".replace("\n", "")

OPENING = """Picture a small town. It has one town hall, where people go to register a new address. Nobody builds a second one, and everybody knows where it is. That works, until a clerk pins a note to the board for one visitor, and the next visitor reads it as their own.

Programs have town halls too: one price list, or one set of settings that every part of the program reads. An object that exists exactly once and is shared by everyone is called a Singleton, one of 23 patterns in a famous book from 1994. Making only one sounds easy. It stops being easy when two threads ask for it at the same moment, and the more code shares it, the harder that code is to test.

The functional programming track ended with immutable data and pure functions at the core of a program. A singleton is often the opposite: shared, and changeable. In this lesson, we'll see what a design pattern is, build one shared price list safely in Java and Kotlin, and find out why the best singleton is often one you don't write. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """A **design pattern** is a named solution to a design problem that keeps coming back. Think of the town again. Every town needs a way to show strangers where things are, and most towns solve it the same way: a map by the station. Nobody invented that map for your town. The idea was already there, with a name, and your town filled in its own streets.

Software has the same kind of ideas. In 1994, four authors, often called the Gang of Four (GoF), wrote down 23 of them in a book called *Design Patterns*. Each one has a name, the problem it solves, the shape of the solution and what it costs. The names are the part that lasts. When a teammate says "put an adapter around the old warehouse program", five words carry a whole design. So a pattern is a word in a shared vocabulary. It isn't a class you copy and paste.

The book was written for C++ and Smalltalk. Java at the time had no lambdas (small functions you can pass around as values), no records (classes that only carry data) and no sealed types. A sealed type lists all of its subtypes in one place, so the compiler knows every case. Many of the 23 patterns were workarounds for exactly those missing features.

In Java 21 and later, and in Kotlin 2, the 23 sort into three groups, as the figure shows.

- The language absorbed some of them. A strategy, an algorithm you plug into other code, used to be an interface and three classes. Now it's a lambda. State and Visitor become a sealed type plus a `switch` or `when` that the compiler checks covers every case. Builder mostly becomes Kotlin's named and default arguments, and Singleton becomes an `enum` or a Kotlin `object`.
- Libraries absorbed others. Observer, which tells interested code when something changes, is Kotlin's `Flow` or the Reactor library, both from earlier tracks. Proxy, a stand-in that controls access to another object, is something the JDK (the kit of tools and libraries that comes with Java) can generate for you while the program runs.
- You still design the rest by hand. Adapter, Facade, Composite, Bridge, Mediator and Flyweight are about how you cut up your own program, and no language feature does that for you.

The intent of an absorbed pattern survives. Strategy still means "swap the algorithm without touching the caller". What changed is the price. When a strategy costs one lambda instead of four classes, you use it ten times as often and stop calling it a pattern.

Brian Goetz, Java's language architect, gave the strongest version of this in a 2018 design note on pattern matching. With powerful enough pattern matching, he wrote, "the Visitor pattern is almost completely unnecessary". The same note says this doesn't make inheritance, and methods that subclasses override, wrong. That's the position of this track too. **Learn the intent, then reach for the cheapest feature that delivers it.**

To keep that promise honest, every pattern in this track gets two things: an everyday picture from one small town, and a job in one small program. The program is the order system of the town's corner shop. The shop sells groceries and household things, takes orders by phone and online, and delivers them around town by bike or by van. Its first job is small. Every part of the program needs to know what things cost, so the shop needs one price list that everybody shares."""

# ---------------------------------------------------------------- section 1
J_RACY = """// Naive: this will not work when threads race
static PriceList instance;
static PriceList getInstance() {
    if (instance == null) instance = new PriceList();   // two threads can both see null
    return instance;
}"""
K_RACY = """// Naive: this will not work when threads race
private var instance: PriceList? = null
fun priceList(): PriceList {
    if (instance == null) instance = PriceList()        // the same race in Kotlin
    return instance!!
}"""
J_SAFE = """enum OrderNumbers {                     // 1. enum: the JVM makes exactly one INSTANCE
    INSTANCE;
    private final AtomicLong last = new AtomicLong();
    long next() { return last.incrementAndGet(); }
}

final class PriceList {                 // 2. holder: lazy, no lock on the fast path
    private PriceList() { }
    private static final class Holder { static final PriceList INSTANCE = new PriceList(); }
    static PriceList getInstance() { return Holder.INSTANCE; }
}"""
K_SAFE = """enum class OrderNumbers {               // 1. enum works the same in Kotlin
    INSTANCE;
    private val last = AtomicLong()
    fun next() = last.incrementAndGet()
}

class PriceList private constructor() { // 2. holder: a private object nested in the companion
    companion object {
        private object Holder { val INSTANCE = PriceList() }
        fun getInstance(): PriceList = Holder.INSTANCE
    }
}"""
J_DCL = """private volatile Map<String, Long> prices;
Map<String, Long> prices() {
    Map<String, Long> p = prices;         // one volatile read on the fast path
    if (p == null) {
        synchronized (lock) {
            p = prices;                   // check again: another thread may have won
            if (p == null) prices = p = load();
        }
    }
    return p;
}"""
K_DCL = """@Volatile private var prices: Map<String, Long>? = null
fun prices(): Map<String, Long> {
    prices?.let { return it }             // one volatile read on the fast path
    synchronized(lock) {
        prices?.let { return it }         // check again: another thread may have won
        return load().also { prices = it }
    }
}"""

S1 = """A **singleton** is a class with exactly one instance and one place to get it. The JDK has its own: the `Runtime` Javadoc, Java's official documentation, says every Java application has a single instance of `Runtime`, and an application can't create its own. In the town, it's the town hall. In the shop's program, it's the price list: every part of the program asks it what a loaf of bread costs, and there should be only one.

Making one is easy. Making one lazily, that is, only when somebody first asks, is where people slip. Loading the price list means reading the supplier's price file, which is slow, so we'd like to wait until we need it. Here's the version most of us write first:

""" + pair(J_RACY, K_RACY) + """

A thread is a path of work that runs alongside others in the same program. The shop's program has several, one for each customer order it's handling, so several can ask for the price list at once. Let's trace the smallest case. Thread A reads `instance` and sees `null`. Before A has finished building, thread B reads `instance` and sees `null` too. Both build a price list. A third thread that arrives a moment later gets one of the two, and nobody can say which.

That's the check-then-act race from *Race conditions: why count++ lies*. The check and the act are two separate steps, and another thread can slip in between them. Here the town picture breaks for the first time. Two builders who turned up at the empty plot for the town hall would see each other and agree. Threads can't see each other at all. Each one sees only the field.

`LazyRaceDemo`, in the Try it, lets eight threads ask at the same moment, with a constructor that takes 20 ms, like a slow file read. It printed:

```text
racy check-then-act: constructor ran 8 time(s), callers saw 8 instance(s)
holder idiom       : constructor ran 1 time(s), callers saw 1 instance(s)
```

Eight threads asked for the one price list and got eight. So much for one. The second line is a fix, and there are three good ones. Here are the first two, in the order I reach for them:

""" + pair(J_SAFE, K_SAFE) + """

The first is an `enum` with one constant. Effective Java (item 3), the best-known book of Java advice, calls it the preferred approach. The JVM, the program that runs your Java and Kotlin code, creates the constant once. Neither serialization (turning an object into bytes and back) nor reflection (code that inspects and calls classes while the program runs) can make a second. Use it when the object is cheap, or needed at startup anyway, like the counter that hands out order numbers.

The second is the **holder idiom**, for an expensive object you want lazily. The JVM initializes a class, which means running the setup code of its static fields, the first time anyone uses it, and it does that exactly once. So `Holder` is set up on the first call to `getInstance()`, not before. The JVM is a strict doorkeeper here: the first thread in runs the setup, and every other thread waits politely at the door until it's done. After that, every call is a plain read of a static field.

The third is **double-checked locking**, from *Lazy init done right: double-checked locking and holders* in the memory model track. The holder only works for static fields. When the lazy value is an instance field, one per object, you check it once without a lock. Only if it's still `null` do you take a lock and check again:

""" + pair(J_DCL, K_DCL) + """

`synchronized (lock)` lets only one thread at a time into the block. `volatile` (`@Volatile` in Kotlin) makes a write to the field visible to every thread that reads the field afterwards. Leave `volatile` out, and another thread can see a non-null reference to a map whose contents it can't see yet. That's the bug the lab asks you to fix.

**A plain null check can't promise one instance. Let the JVM or a lock promise it.**

Java gives us three tools, then, and each needs a little care. Kotlin moves two of them into the language."""

# ---------------------------------------------------------------- section 2
K_OBJ = """object OrderNumbers {
    private val last = AtomicLong()
    fun next() = last.incrementAndGet()
}"""
J_OBJ = """// what the Kotlin compiler writes for that object, give or take
public final class OrderNumbers {
    public static final OrderNumbers INSTANCE = new OrderNumbers();
    private final AtomicLong last = new AtomicLong();
    private OrderNumbers() { }
    public long next() { return last.incrementAndGet(); }
}"""

S2 = """Kotlin builds the singleton into the language. An `object` declaration defines a class and its one instance in a single step:

""" + pair_kj(K_OBJ, J_OBJ) + """

The Kotlin docs say the initialization of an object declaration is thread-safe and done on first access. The Java twin shows why. The compiler writes a class with a static `INSTANCE` field, set when the class is initialized, so the doorkeeper from the holder idiom does the same job here. From Java, you call it as `OrderNumbers.INSTANCE.next()`.

Two details trip people up. A `companion object`, the object inside a class that holds what Java would make `static`, is initialized when its outer class is loaded, like a Java static initializer. And companion members aren't really static. They're members of the companion object, so Java callers write `PriceList.Companion.getInstance()` unless you mark the function `@JvmStatic`.

For a lazy value inside a class, Kotlin has `by lazy`. You hand it a function, and it runs the function on the first read and keeps the result. It has three modes, and they behave very differently when threads race:

| Mode | What it does | Use it for |
|---|---|---|
| `SYNCHRONIZED` (default) | takes a lock; the function runs once | anything with side effects |
| `PUBLICATION` | no lock; racing threads may each run the function, and the first stored value wins | cheap, pure computations |
| `NONE` | no lock and no promise across threads | values only one thread ever touches |

`LazyModes`, in the Try it, sends eight threads at the first two modes at once:

```text
SYNCHRONIZED initializer ran 1 time(s), callers saw 1 instance(s)
PUBLICATION  initializer ran 8 time(s), callers saw 1 instance(s)
```

That second line answers the warm-up. Every caller saw the same map, so the program looks fine. But the function ran eight times. A side effect is anything a function does besides returning its value, such as opening a file or a network connection. If the function opens a connection to the warehouse, eight first reads open eight connections. Seven results are thrown away, and nobody closes their connections.

The default `lazy` is double-checked locking, written once and correctly in the standard library. It does one more thing: if the function throws, the next read runs it again. **In Kotlin, never write double-checked locking by hand. Write `by lazy`.**

So both languages can make one of something safely. The harder question is whether you should."""

# ---------------------------------------------------------------- section 3
J_HIDDEN = """class OrderPricer {
    long totalCents(Map<String, Integer> basket) {        // product code -> how many
        long total = 0;
        for (var line : basket.entrySet())
            total += PriceList.getInstance().priceOf(line.getKey()) * line.getValue();   // hidden, global
        return total;
    }
}"""
K_HIDDEN = """class OrderPricer {
    fun totalCents(basket: Map<String, Int>): Long =      // product code -> how many
        basket.entries.sumOf { (code, count) ->
            PriceList.priceOf(code) * count               // PriceList is an object: hidden, global
        }
}"""
J_INJECT = """interface Prices { long priceOf(String code); }

class OrderPricer {
    private final Prices prices;
    OrderPricer(Prices prices) { this.prices = prices; }

    long totalCents(Map<String, Integer> basket) {
        long total = 0;
        for (var line : basket.entrySet()) total += prices.priceOf(line.getKey()) * line.getValue();
        return total;
    }
}
// in a test: new OrderPricer(code -> 450)"""
K_INJECT = """fun interface Prices { fun priceOf(code: String): Long }

class OrderPricer(private val prices: Prices) {
    fun totalCents(basket: Map<String, Int>): Long =
        basket.entries.sumOf { (code, count) -> prices.priceOf(code) * count }
}
// in a test: OrderPricer { 450 }"""

S3 = """Back to the town hall for a moment. Everybody depends on it, which is handy, and also the trouble. A note pinned to its board for one visitor is read by the next. And when new staff need to practice, there's no pretend town hall to practice in. Programs have both problems. Here's the shop's code that adds up a basket, fetching the price list the singleton way:

""" + pair(J_HIDDEN, K_HIDDEN) + """

To test `totalCents` with bread at 450 cents, you need to control the price list, and you can't. The instance is global, built once per JVM, and it reads the real price file. A test that changes its state leaks into the next test, so the suite passes or fails depending on the order the tests run in. That's the note on the town hall's board. And nothing in `OrderPricer`'s constructor even tells a reader that it needs a price list.

The fix is to pass the dependency in, typed as an interface. This is called **dependency injection**: an object receives what it needs through its constructor, instead of reaching out for it.

""" + pair(J_INJECT, K_INJECT) + """

Now the test has its pretend town hall: one lambda that says every product costs 450 cents. The real program still wants exactly one price list. So make one where the program is put together, in `main` for example, and pass the same object to everyone who needs it. You get one instance, and nobody calls `getInstance()`.

**One instance is a decision for the code that wires the program together. Pass it in.**

A hand-written singleton still fits in a few places. Stateless objects, such as a comparator that decides which of two values comes first, are safe to share, because there's nothing to pin on their board. So are values with no data at all, such as a Kotlin `data object` in a sealed hierarchy (lesson 9 of this track). So is state the JVM itself owns, like `Runtime`. Anything that reads files, talks over the network or holds settings gets passed in.

The lab's `PriceList` follows that rule. It isn't a static singleton: its loader comes in through the constructor, so the tests can pass a slow pretend loader and count how often it runs. The program makes one `PriceList`, and double-checked locking inside keeps the lazy load safe when eight threads ask at once.

Check yourself. Suppose the Kotlin `object PriceList` had a test helper, `PriceList.override("BREAD", 1)`, and one test called it and never reset it. A test in another class runs later in the same JVM and prices a loaf. What does it get, and why? (1 cent. The `object` is one static `INSTANCE` for the whole JVM, so its state outlives the test that set it. A fake that was passed in goes away with its test.)"""

ASIDE3 = {
    "title": "Don't frameworks make singletons for me?",
    "body": "If you write web services, often yes. Frameworks such as Spring and Quarkus create your objects for you and pass them in through constructors; the part that does this is called a dependency injection container. Each object it manages has a scope, and the usual one is a single instance for the whole application. So you get the singleton's one-ness without its `getInstance()`, and your class stays a plain class that a test can build with `new`. This section is what such a container does for you, written by hand."
}

L = {
 "id": "pat-01",
 "title": "Patterns in a modern language, and Singleton",
 "minutes": 35,
 "goal": "By the end you can say what a design pattern is and which ones modern Java and Kotlin absorbed, pick the right singleton form in each language, prove a lazy instance is built once under contention, and explain why passing an instance in usually beats fetching a global one.",
 "opening": OPENING,
 "warmup": {
  "q": "A Kotlin shop program has `val prices by lazy(LazyThreadSafetyMode.PUBLICATION) { loadPrices() }`. Eight threads read `prices` for the first time at the same moment. How many times can `loadPrices()` run?",
  "options": ["Exactly once, because `lazy` always takes a lock", "Up to eight times, but every thread ends up with the same value", "Up to eight times, and each thread may keep its own value", "Zero times until the main thread reads it first"],
  "answer": 1,
  "why": "`PUBLICATION` takes no lock. Every thread that finds the value missing runs the function, and the first result stored wins; the rest are thrown away. So `loadPrices()` can run eight times while every caller sees one value. The default mode, `SYNCHRONIZED`, is the one that runs it once, and threads keeping their own values is what `NONE` allows. The section on Kotlin's `object` and `lazy` runs all of this with real threads."
 },
 "sections": [
  {
   "h": "A pattern is a name for a problem you keep meeting",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Most of the 23 patterns still have a job. What changed is who writes them: the language, a library, or you."},
   "try": {
    "title": "Find five patterns in the JDK",
    "minutes": 4,
    "steps": [
     "Read `main` in `PatternsYouAlreadyUse` below (Java or Kotlin, they print the same). Write down what each of the six lines will print before you run anything.",
     "Run it from the `labs/` folder with the command below.",
     "Name the pattern behind each line: singleton, flyweight (one shared object for every equal value), a read-through view (a kind of proxy) or strategy. Which line surprised you?"
    ],
    "code": code("java", "PatternsYouAlreadyUse.java", "PatternsYouAlreadyUse", "kotlin", "PatternsYouAlreadyUse.kt", "PatternsYouAlreadyUseKt"),
    "expect": "It prints `true`, `true`, `false`, `true`, `[o-1, o-2]` and `[o-3, o-9]`. Line 3 surprises most people: `Integer.valueOf` only caches the numbers from -128 to 127, so two boxed 128s are two different objects. Line 5 shows that `unmodifiableList` is a view that reads through to the list it wraps: it blocks writes through the view, and it isn't a copy. Line 6 is a strategy in one line: the comparator decides the order, and `sort` does the rest."
   },
   "refs": [
    {"title": "Pattern Matching for Java (Bierman and Goetz, design note)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md", "kind": "read"}
   ]
  },
  {
   "h": "Building exactly one price list in Java: enum, holder and double-checked locking",
   "body": S1,
   "try": {
    "title": "Build eight singletons by accident",
    "minutes": 4,
    "steps": [
     "Predict: when eight threads call the racy getter together, how many price lists get built? And with the holder?",
     "Run `LazyRaceDemo` with the command below.",
     "Delete the `Thread.sleep(20)` line in the constructor (`PriceList` in Java, `SlowPriceList` in Kotlin) and run it three more times. Did the race go away?"
    ],
    "code": code("java", "LazyRaceDemo.java", "LazyRaceDemo", "kotlin", "LazyRaceDemo.kt", "LazyRaceDemoKt"),
    "expect": "With the slow constructor, the racy version builds 8 price lists and callers see 8 different objects. The holder (an `object` in the Kotlin twin) builds 1. Without the sleep, three runs in a row on a busy four-core machine printed `constructor ran 1 time(s)`. The race didn't go away. The gap between the check and the act shrank to a few microseconds, too small for eight threads to hit often. A real price file is slow, which is why this shows up when the shop is busy and not in your unit test."
   },
   "refs": [
    {"title": "Runtime (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Runtime.html", "kind": "docs"}
   ]
  },
  {
   "h": "Kotlin's object and lazy do the locking for you",
   "body": S2,
   "try": {
    "title": "Count the lazy function's runs",
    "minutes": 4,
    "steps": [
     "Read `LazyModes.kt`. The Java twin writes each mode by hand, which shows what the modes really do. Predict both lines of output: how many runs of the function, and how many distinct maps, for each mode?",
     "Run it with the command below.",
     "Add `trial(LazyThreadSafetyMode.NONE)` at the end of `main` (in Java: `trial(\"NONE\", UnsafeLazy::new);`) and run it again. Predict first."
    ],
    "code": code("kotlin", "LazyModes.kt", "LazyModesKt", "java", "LazyModesJava.java", "LazyModesJava"),
    "expect": "`SYNCHRONIZED` runs the function once, and callers see 1 instance. `PUBLICATION` runs it 8 times, yet callers still see 1 instance, because only the first stored value is kept. The new line reads `NONE         initializer ran 8 time(s), callers saw 8 instance(s)`: each thread kept the map it built. No warning, no exception."
   },
   "refs": [
    {"title": "Object declarations and expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/object-declarations.html", "kind": "docs"},
    {"title": "LazyThreadSafetyMode (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/", "kind": "docs"}
   ]
  },
  {
   "h": "Why one shared object causes trouble, and how passing it in helps",
   "body": S3,
   "aside": ASIDE3
  }
 ],
 "compare": {
  "title": "One instance, and one lazy field, in Java and Kotlin",
  "java": {"title": "Prices.java", "src": """// one instance: the JVM's class setup does the work
enum OrderNumbers {
    INSTANCE;
    private final AtomicLong last = new AtomicLong();
    long next() { return last.incrementAndGet(); }
}

// one lazy field per object: double-checked locking
final class Prices {
    private final Supplier<Map<String, Long>> loader;
    private final Object lock = new Object();
    private volatile Map<String, Long> table;

    Prices(Supplier<Map<String, Long>> loader) { this.loader = loader; }

    Map<String, Long> table() {
        Map<String, Long> t = table;
        if (t == null) {
            synchronized (lock) {
                t = table;
                if (t == null) table = t = Map.copyOf(loader.get());
            }
        }
        return t;
    }
}"""},
  "kotlin": {"title": "Prices.kt", "src": """// one instance: the language makes it
object OrderNumbers {
    private val last = AtomicLong()
    fun next() = last.incrementAndGet()
}

// one lazy field per object: the standard library does the locking
class Prices(loader: () -> Map<String, Long>) {
    val table: Map<String, Long> by lazy { loader().toMap() }   // SYNCHRONIZED by default
}"""},
  "note": "A Kotlin `object` compiles to the same thing as a Java holder: a class with a static `INSTANCE` field set while the class is initialized, so the JVM guarantees one instance. `by lazy` replaces the whole double-checked block (the `volatile` field, the lock object and the second check), and it runs the function again on the next read if the first run threw. So Kotlin makes hand-written singletons and hand-written double-checked locking unnecessary. It doesn't fix the design problem: a global `object` that reads files is as hard to test as a Java static singleton, and the answer in both languages is to pass the instance in."
 },
 "worked": {
  "title": "Turn a global singleton into a passed-in dependency, then make its lazy load safe",
  "steps": [
   {"say": "The shop charges for delivery by district, and the charge per parcel lives in a zones file read through a global singleton. Before reading on, find what stops you from unit-testing `chargeCents`.",
    "code": """class DeliveryCharge {
    long chargeCents(String district, int parcels) {
        long perParcel = Zones.getInstance().centsFor(district);   // global; reads the zones file
        return perParcel * parcels;
    }
}""", "lang": "java",
    "alt_code": """class DeliveryCharge {
    fun chargeCents(district: String, parcels: Int): Long {
        val perParcel = Zones.centsFor(district)                   // an object: global; reads the zones file
        return perParcel * parcels
    }
}""", "alt_lang": "kotlin"},
   {"say": "The dependency is hidden and global. A test can't pass its own charges, and anything the singleton keeps leaks into the next test. Make the dependency visible: an interface, passed through the constructor. Now the test is one line.",
    "code": """interface Zones { long centsFor(String district); }

class DeliveryCharge {
    private final Zones zones;                             // 1. the dependency is in the signature
    DeliveryCharge(Zones zones) { this.zones = zones; }

    long chargeCents(String district, int parcels) {
        return zones.centsFor(district) * parcels;
    }
}
// test: new DeliveryCharge(d -> 300).chargeCents("HARBOUR", 2) == 600""", "lang": "java",
    "alt_code": """fun interface Zones { fun centsFor(district: String): Long }

class DeliveryCharge(private val zones: Zones) {           // 1. the dependency is in the signature
    fun chargeCents(district: String, parcels: Int): Long =
        zones.centsFor(district) * parcels
}
// test: DeliveryCharge { 300 }.chargeCents("HARBOUR", 2) == 600L""", "alt_lang": "kotlin"},
   {"say": "The real program still wants one zones table, read on first use. `main` makes one `FileZones` and passes it to everyone. Inside it the table is an instance field, so the holder idiom can't help, and Java uses double-checked locking. Why must the field be `volatile`? Answer before you read the comment on it. The Kotlin class is four lines, because `by lazy` is the whole double-checked block.",
    "code": """final class FileZones implements Zones {
    private final Object lock = new Object();
    private volatile Map<String, Long> table;              // 2. volatile: readers see the whole map

    public long centsFor(String district) {
        Map<String, Long> t = table;                       // 3. fast path: one read, no lock
        if (t == null) {
            synchronized (lock) {
                t = table;                                 // 4. check again under the lock
                if (t == null) table = t = loadFromFile();
            }
        }
        return t.getOrDefault(district, 400L);
    }

    private Map<String, Long> loadFromFile() {
        return Map.of("HARBOUR", 300L, "OLD TOWN", 250L);  // the real one reads zones.txt
    }
}""", "lang": "java",
    "alt_code": """class FileZones(private val file: ZoneFile) : Zones {
    // 2-4. by lazy (SYNCHRONIZED) is the volatile field, the lock and the second check in one line
    private val table: Map<String, Long> by lazy { file.load() }

    override fun centsFor(district: String) = table[district] ?: 400L
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A lazy price list that loads once, and a harness that proves it",
  "minutes": 12,
  "files": [f"{lab}/main/{J}/PriceList.java", f"{lab}/main/{J}/Contention.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l01.*'",
  "steps": [
   "Open `PriceList`, the shop's price list from this lesson. Its loader is a `Supplier` that reads the prices, `priceOf` looks one up, and an unknown product, such as `CAVIAR` (the corner shop doesn't stock it), throws `IllegalArgumentException`.",
   "Run the tests. Seven of ten fail: the harness is a stub, and the price list runs its slow loader eight times when eight threads look up a price together.",
   "Write `Contention.distinctInstances`. Start the threads behind two latches, `ready` and `go`, as in *Race conditions: why count++ lies*. A latch (`CountDownLatch`) is a gate that opens when its count reaches zero. Store each result in its own array slot, join every thread, then count the results in a set that compares with `==`.",
   "Fix `PriceList.prices()` with double-checked locking: a `volatile` field, a private lock object, and a second check inside `synchronized`. Keep the `Map.copyOf` around the loader's result.",
   "Run the tests until all ten pass, then twice more."
  ],
  "hints": [
   "`Collections.newSetFromMap(new IdentityHashMap<>())` is a `Set` that compares with `==`. A `HashSet` would count eight empty lists as one.",
   "Read the volatile field into a local variable once at the top, and return the local. The fast path then costs one volatile read.",
   "If the loader throws inside the `synchronized` block, the field is still `null` and the next caller tries again. You get that for free, as long as you assign the field only after `loader.get()` returns."
  ],
  "done_when": "All ten tests in `SingletonTest` pass, three runs in a row."
 },
 "drill": {
  "title": "The holder idiom and double-checked locking from memory",
  "minutes": 5,
  "prompt": "Close this page. In the language you use most, write (a) a lazy singleton `PriceList` with the holder idiom, and (b) a lazy field `prices: Map<String, Long>` loaded by `loadPrices()` with double-checked locking, by hand. Then compare with the answer, and read the other language's version too. Did you remember `volatile` (or `@Volatile`) and the second null check?",
  "answer": {"lang": "java", "src": """// (a) holder idiom: lazy, thread-safe, no lock on the fast path
final class PriceList {
    private PriceList() { }
    private static final class Holder { static final PriceList INSTANCE = new PriceList(); }
    static PriceList getInstance() { return Holder.INSTANCE; }
}

// (b) double-checked locking for an instance field
private final Object lock = new Object();
private volatile Map<String, Long> prices;

Map<String, Long> prices() {
    Map<String, Long> p = prices;        // one volatile read
    if (p == null) {
        synchronized (lock) {
            p = prices;                  // second check, under the lock
            if (p == null) prices = p = loadPrices();
        }
    }
    return p;
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """// (a) Kotlin's holder: a private object nested in the companion (or just make PriceList an object)
class PriceList private constructor() {
    companion object {
        private object Holder { val INSTANCE = PriceList() }
        fun getInstance(): PriceList = Holder.INSTANCE
    }
}

// (b) double-checked locking by hand, for practice
private val lock = Any()
@Volatile private var prices: Map<String, Long>? = null

fun prices(): Map<String, Long> {
    prices?.let { return it }             // one volatile read
    synchronized(lock) {
        prices?.let { return it }         // second check, under the lock
        return loadPrices().also { prices = it }
    }
}
// in real Kotlin code, all of (b) is: val prices: Map<String, Long> by lazy { loadPrices() }"""}}
 },
 "recap": [
  "A design pattern is a name for a design problem that keeps coming back and the shape of its solution. Use the names as vocabulary, not as class templates.",
  "Lambdas, records, sealed types and Kotlin's `object`, `by lazy` and named arguments turned several patterns into a line or two. Adapter, Facade and a few others you still design by hand.",
  "Java singletons: an `enum` when making it at startup is fine, the holder idiom for a lazy static, and double-checked locking with `volatile` for a lazy instance field.",
  "A Kotlin `object` is a thread-safe singleton created on first access. `by lazy` defaults to `SYNCHRONIZED`; `PUBLICATION` may run the function once per racing thread.",
  "Prove \"only one\" under contention: threads released together, a slow constructor, and a count by identity.",
  "The limit: even a safe singleton is one global thing that hides a dependency and carries state from test to test. Make one instance where the program is put together, and pass it in."
 ],
 "closing": "We started with one town hall and the note on its board. In the shop, the town hall was the price list: eight threads built eight by accident, an enum, a holder or `by lazy` kept it to one, and the code was easiest to test when nobody fetched it with `getInstance()`.\n\nNow look in your own code for `getInstance()` or a Kotlin `object` that reads files or settings. Could a test hand that code a pretend one? If not, a dependency is waiting to be passed in.\n\nNext, we'll look at how objects get made. A constructor always makes one exact class, so what happens when the code that needs an object shouldn't choose its class?",
 "quiz": [
  {"q": "The shop's Kotlin code has `val warehouse by lazy(LazyThreadSafetyMode.PUBLICATION) { openConnection() }`, and `openConnection()` opens a network connection to the warehouse. What can go wrong when eight orders arrive at once?",
   "options": ["Nothing, because the property is lazy", "Several threads can each open a connection; one is kept and the others are never closed", "Threads can see a half-built connection", "The first caller deadlocks"],
   "answer": 1,
   "why": "`PUBLICATION` lets every racing thread run the function and keeps the first stored result. Opening a connection is a side effect, so the discarded results leave open connections behind. Drop the mode argument: the default `SYNCHRONIZED` runs the function once. A half-built value isn't the risk here, because the store itself is safe; only the side effects repeat."},
  {"q": "You need one counter that hands out order numbers for the whole Java program, and it's fine to create it at startup. Which form is simplest and still correct?",
   "options": ["An `enum` with one constant, `INSTANCE`", "Double-checked locking on a `volatile` static field", "A static field set inside `getInstance()` behind `if (instance == null)`", "A `synchronized static getInstance()` method"],
   "answer": 0,
   "why": "An enum gives you exactly one instance, created when the class is initialized, and serialization or reflection can't make another. Double-checked locking is for lazy instance fields and is more than this needs. The plain `if` version races, and a `synchronized` getter is correct but takes a lock on every call for nothing."},
  {"q": "Java code calls a Kotlin factory declared as `class Price { companion object { fun of(cents: Long) = Price() } }`. What does the Java caller write?",
   "options": ["`Price.of(100)`", "`Price.INSTANCE.of(100)`", "`Price.Companion.of(100)`", "`new Price().of(100)`"],
   "answer": 2,
   "why": "Companion members belong to the companion object, which Java sees as a static field called `Companion`. Mark `of` with `@JvmStatic` if you want `Price.of(100)` to work from Java. `INSTANCE` is the field for an `object` declaration, not for a companion."},
  {"q": "A test passes alone and fails in the full suite. The class under test reads `MessageCounter.INSTANCE.count(\"sent\")`. What is the likely cause and fix?",
   "options": ["JUnit runs tests in parallel, so add `synchronized`", "The enum gets created twice, so switch to the holder idiom", "The JIT caches the count, so make the field `volatile`", "The singleton keeps counts from earlier tests, so pass the counter in and give each test its own"],
   "answer": 3,
   "why": "A global singleton lives as long as the JVM, so one test's counts leak into the next, and the result depends on the order the tests run in. Passing the counter through the constructor lets each test make a fresh one. An enum is never created twice, and visibility isn't the problem when the tests run on one thread."},
  {"q": "From *Lazy init done right* in the memory model track: in double-checked locking, what goes wrong if the `instance` field is not `volatile`?",
   "options": ["Two instances can be created", "The `synchronized` block can deadlock", "Another thread can see a non-null reference to an object whose fields it can't see yet", "Nothing on x86, so it is safe in practice"],
   "answer": 2,
   "why": "The second check under the lock still prevents a second instance. The problem is the fast path, which reads the field without a lock. Without `volatile` there's no happens-before edge from the constructor's writes to that read, so a thread can see the reference before the fields. The JIT compiler may reorder those writes on any CPU, x86 included, and the memory model allows it.",
   "from": "jmm-05"}
 ],
 "flashcards": [
  {"front": "What is a design pattern, in one sentence?", "back": "A name for a design problem that keeps coming back, with the shape of its solution and its trade-offs. Vocabulary, not a class template."},
  {"front": "Which Java singleton form does Effective Java call the preferred approach?", "back": "A single-element `enum`: `enum OrderNumbers { INSTANCE; ... }`. The JVM guarantees one instance, even across serialization and reflection."},
  {"front": "Why is the holder idiom lazy and thread-safe without a lock in your code?", "back": "The JVM initializes the nested `Holder` class on the first read of `Holder.INSTANCE`, exactly once, under its own class-initialization lock."},
  {"front": "When do you need double-checked locking instead of the holder idiom?", "back": "When the lazy value is an instance field, one per object. The holder idiom only works for statics."},
  {"front": "`by lazy(LazyThreadSafetyMode.PUBLICATION) { init() }`: how many times can `init()` run?", "back": "Once per racing thread. The first stored value wins and every caller sees it, but the side effects repeat."},
  {"front": "Are Kotlin companion object members static on the JVM?", "back": "No. They belong to the companion object (`Price.Companion.of()` from Java) unless you mark them `@JvmStatic`."},
  {"front": "Why does passing an instance in usually beat `getInstance()`?", "back": "The dependency shows in the constructor, a test can pass a fake, and no global state leaks between tests. The program still makes only one."}
 ],
 "terms": [
  {"term": "Design pattern", "plain": "A named, reusable shape for solving a design problem that keeps coming back."},
  {"term": "Singleton", "plain": "A class with exactly one instance and one way to get it."},
  {"term": "Holder idiom", "plain": "A nested static class whose static field holds the instance. The JVM creates it once, on first use."},
  {"term": "Double-checked locking", "plain": "Read a volatile field without a lock, and only lock, and check again, when it is still null."},
  {"term": "Object declaration", "plain": "Kotlin's built-in singleton: a class and its one instance, created thread-safely on first access."},
  {"term": "Lazy thread-safety mode", "plain": "How `by lazy` handles racing first reads: SYNCHRONIZED runs once, PUBLICATION may run many times, NONE promises nothing."},
  {"term": "Dependency injection", "plain": "Giving an object what it needs through its constructor, instead of letting it fetch a global."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add `public static Settings getInstance()` with a plain `if (instance == null)` check to the shop's program. Explain what you'd suggest instead, and why.",
  "answer": "The plain null check is a check-then-act race: two threads can both see null and both load the settings. Even a correct lazy singleton hides the dependency and makes it global, so tests can't pass their own settings, and whatever one test changes leaks into the next. I'd make `Settings` a plain class, create one in `main` where the program is put together, and pass it through the constructors of the classes that need it. If the settings should load lazily inside that object, that's an instance field, so I'd use double-checked locking with a volatile field, or `by lazy` in Kotlin, and keep the loader passed in so a test can count how often it runs."
 },
 "deeper": {
  "minutes": 10,
  "body": """The JDK is getting its own lazy constant, slowly. JDK 25 shipped `StableValue` as a preview API (JEP 502), that is, a feature you can only try with `--enable-preview`. JDK 26 renamed it `LazyConstant` (JEP 526, second preview), and JDK 27 still has it in preview (JEP 531). `LazyConstant.of(() -> load())` promises that when several threads race, only one runs the computation. It can't hold `null`, and a failed computation is remembered: later calls throw without running it again. That's the opposite of Kotlin's `lazy`, which tries again. Because it's a preview API that has already changed its name once, it stays out of this course's labs.

Serialization can break a class-based singleton. Serialization turns an object into bytes and back, and turning the bytes back creates a new object, unless the class defines `readResolve()` to return the existing instance. The JVM handles enums specially, which is one reason Effective Java prefers them.

Kotlin's `data object` gives a singleton a readable `toString()` and value-style `equals`. The Kotlin docs warn that serialization or reflection can still produce a second instance, so compare data objects with `==`, never with `===`. You'll use `data object` for states that carry no data, such as `Delivered` in an order's life, in *State and Chain of Responsibility* (lesson 9 of this track)."""
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
