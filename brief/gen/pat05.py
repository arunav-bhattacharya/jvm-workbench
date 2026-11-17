import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l05"
K = "kotlin/workbench/patterns/l05"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l05.{cls}"


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


FIG = """<svg viewBox="0 0 680 262" role="img" aria-label="A caller's call goes through the proxy into pickBoth on the real stockroom; the inner call this.pick() goes straight to pick and never passes the proxy">
<rect class="box" x="16" y="100" width="110" height="48" rx="8"/>
<text class="t" x="71" y="121" text-anchor="middle">caller</text>
<text class="t-s t-m" x="71" y="139" text-anchor="middle">the shop's code</text>
<rect class="box-a" x="170" y="78" width="180" height="92" rx="8"/>
<text class="t" x="260" y="104" text-anchor="middle">proxy</text>
<text class="t-s" x="260" y="126" text-anchor="middle">time, retry, check</text>
<text class="t-s" x="260" y="146" text-anchor="middle">then forward the call</text>
<rect class="box-dim" x="400" y="16" width="270" height="214" rx="8"/>
<text class="t-s t-m" x="535" y="36" text-anchor="middle">the real stockroom (target)</text>
<rect class="box" x="440" y="56" width="190" height="44" rx="8"/>
<text class="t t-code" x="535" y="83" text-anchor="middle">pickBoth(a, b)</text>
<rect class="box" x="440" y="164" width="190" height="52" rx="8"/>
<text class="t-s t-m" x="535" y="184" text-anchor="middle">called twice</text>
<text class="t t-code" x="535" y="205" text-anchor="middle">pick(item)</text>
<line class="ln-a" x1="126" y1="124" x2="166" y2="124" marker-end="url(#arr)"/>
<line class="ln-a" x1="350" y1="110" x2="436" y2="82" marker-end="url(#arr)"/>
<line class="ln-bad" x1="535" y1="100" x2="535" y2="160" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="598" y="135" text-anchor="middle">this.pick()</text>
<text class="t-s t-bad" x="340" y="252" text-anchor="middle">the inner calls never pass the proxy: nobody times them</text>
</svg>""".replace("\n", "")

OPENING = """A customer at the corner shop buys a teapot as a present. The shopkeeper puts it in its box, wraps the box in gift paper and ties a ribbon around it. Then Pedal Post's rider weighs it, scans the label and rides off, quite unmoved by the bow. A wrapped parcel is still a parcel. The teapot didn't change, and the courier handles it exactly as before.

In the back office, the shop's manager is too busy to answer the phone, so a receptionist answers for her. Callers dial the same number as always. The receptionist checks who's calling, takes messages and puts the right calls through.

Code wraps objects in both ways. The easy trap is to think a wrapper is invisible. It isn't: the order of the layers can change a price, and some calls never pass the receptionist at all.

The last lesson ended on a wrapper that keeps the interface exactly as it is. In this lesson, we'll build two: a decorator, which adds one thing and passes the call on, and a proxy, which stands in front of an object and decides how to call it. Kotlin's `by` will write the passing-on for us. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_FEE = """@FunctionalInterface
interface DeliveryFee {
    long cents(Delivery d);

    static DeliveryFee perKm(long centsPerKm) { return d -> d.km() * centsPerKm; }
    default DeliveryFee plusFixed(long fixed) { return d -> cents(d) + fixed; }
    default DeliveryFee heavySurcharge(int overGrams, long extra) {
        return d -> cents(d) + (d.grams() > overGrams ? extra : 0);
    }
    default DeliveryFee cappedAt(long max) { return d -> Math.min(cents(d), max); }
}

DeliveryFee standard = DeliveryFee.perKm(50).plusFixed(200).heavySurcharge(5_000, 300).cappedAt(800);"""
K_FEE = """fun interface DeliveryFee {
    fun cents(d: Delivery): Long
}

fun perKm(centsPerKm: Long) = DeliveryFee { d -> d.km * centsPerKm }
fun DeliveryFee.plusFixed(fixed: Long) = DeliveryFee { d -> cents(d) + fixed }
fun DeliveryFee.heavySurcharge(overGrams: Int, extra: Long) =
    DeliveryFee { d -> cents(d) + if (d.grams > overGrams) extra else 0L }
fun DeliveryFee.cappedAt(max: Long) = DeliveryFee { d -> minOf(cents(d), max) }

val standard = perKm(50).plusFixed(200).heavySurcharge(5_000, 300).cappedAt(800)"""

S0 = """The corner shop charges for every parcel it sends. The rules are simple: 0.50 for each kilometer, 2.00 to start, 3.00 more for a parcel over 5 kg, and never more than 8.00 in all. The rules also change often, so we'd like each one to be a piece we can add, remove or move.

Here's a way to do that. Give each rule its own small object that wraps the rule before it. Each wrapper is still a delivery fee, with the same one method, so whoever asks for the price can't tell how many layers there are. A **decorator** is exactly that: an object with the same interface as the object it wraps, which does one extra thing and passes the call on. It's the gift wrap. The parcel inside doesn't change, the paper adds one thing, and the courier still handles one parcel.

In Java, a functional interface with default methods turns each rule into a one-line decorator. In Kotlin, the rules are extension functions on a `fun interface`. Either way, each call returns a new fee and leaves the one it wraps alone:

""" + pair(J_FEE, K_FEE) + """

Read the chain from the inside out. `perKm(50)` is the parcel. Each method around it adds one layer, a lambda that first asks the fee it wraps, `cents(d)`, and then applies one rule. The tricky part is that bare `cents(d)`. Inside a default method it means `this.cents(d)`, the fee being decorated, and the lambda captures it.

Now predict three prices. A 2 kg parcel going 4 km costs 2.00 plus 4 times 0.50, so 4.00. A 12 kg parcel going 4 km pays the surcharge: 7.00. And a 12 kg parcel going 20 km would cost 15.00, so the cap brings it down to 8.00. The lab's tests check all three.

Then move `cappedAt(800)` one place to the left, before the surcharge. Both chains compile, and both read sensibly. For the heavy parcel going 20 km, they disagree:

```text
...heavySurcharge(5_000, 300).cappedAt(800)   ->   800 cents
...cappedAt(800).heavySurcharge(5_000, 300)   -> 1,100 cents
```

In the second chain, the cap brings 12.00 down to 8.00, and then the surcharge lands on top. The gift-wrap picture predicts this: a ribbon tied under the paper is hidden, and the outer layer has the last word. The picture breaks in one place, though. Paper can only add. A decorator can also take away, as the cap does, or decide not to call the object inside at all.

**The order of the layers is part of the behavior. Pin it in a test.**

The JDK has stacked decorators for decades. `new DataOutputStream(new BufferedOutputStream(new GZIPOutputStream(out)))` is three wrappers around one stream, a destination for bytes such as a file. Each wrapper is an `OutputStream` too, and each adds one thing: typed writes, buffering, compression. The `FilterInputStream` Javadoc says such a stream "wraps some other input stream, which it uses as its basic source of data, possibly transforming the data along the way".

Behavior stacks the same way as arithmetic. The Try it puts a logging decorator and a retrying decorator around a busy courier line, in both orders. Before you run it, guess whether the order matters there too."""

# ---------------------------------------------------------------- section 1
K_BY = """class CountingMap<K, V>(private val inner: MutableMap<K, V> = HashMap()) : MutableMap<K, V> by inner {
    var puts = 0
    override fun put(key: K, value: V): V? { puts++; return inner.put(key, value) }
}"""
J_BY = """// Java has no `by`. The short way is inheritance, and HashMap's insides decide what you count.
class CountingMap<K, V> extends HashMap<K, V> {
    int puts;
    @Override public V put(K key, V value) { puts++; return super.put(key, value); }
}"""
J_VIEW = """List<String> view = Collections.unmodifiableList(shopping);
shopping.add("jam");           // the view shows it too
view.add("tea");               // UnsupportedOperationException"""
K_VIEW = """val view: List<String> = shopping          // the same object, with a read-only type
shopping += "jam"                           // the view shows it too
(view as MutableList).add("tea")            // works: nothing guards it"""

S1 = """A delivery fee has one method, so a lambda can decorate it. Most interfaces have more. A hand-written decorator for `Map` in Java must pass on every method (`get`, `put`, `remove`, `size`, `entrySet` and a dozen more) just to change one. That passing-on is called **forwarding**, and it's most of the code.

Kotlin's **class delegation** writes the forwarding for you. Say we want a map that counts how often something is put into it:

""" + pair_kj(K_BY, J_BY) + """

Read `: MutableMap<K, V> by inner` as "for every method of `MutableMap` I don't write myself, call the same method on `inner`". The object `by` forwards to is called the **delegate**. The Kotlin docs call delegation "a good alternative to implementation inheritance", where inheritance means taking a parent class's code with `extends`.

Now predict. We call `put("tea", 1)` and then `putAll` with two more entries. What is `puts`? The `CountingMapDemo` in the Try it prints:

```text
CountingMap: puts=1, size=3
```

One, while the map holds three. The compiler forwarded `putAll` to `inner.putAll`, and `inner` is a plain `HashMap` that has never heard of our `put`. The docs say so: overridden members "do not get called from the members of the delegate object". The delegate never calls you back. To count every insertion, override `putAll` too, and `putIfAbsent`, `compute` and `merge`.

That surprise is also the benefit. With inheritance, the count depends on how the parent class is written today. `HashMap.putAll` happens not to call `put`, so the Java version also prints 1. But `HashSet.addAll` does call `add`, so a set that counts in both methods counts each item twice, and the Java twin prints `added=6` for three items. *Effective Java*, the well-known book of Java advice, builds its item 18, "Favor composition over inheritance", on that very bug. With `by`, the delegate never calls back into your code, so a JDK update can't change your numbers.

**The delegate never calls your overrides. Override every method that should behave differently.**

The JDK has a read-only decorator you meet often: `Collections.unmodifiableList`. It forwards reads and throws on writes. It's a **view**, which means it reads through to the list it wraps, so later changes to that list show up in it. For a frozen copy, use `List.copyOf`. Kotlin's `List` is weaker still: a read-only type on the same object, with no wrapper at all:

""" + pair(J_VIEW, K_VIEW) + """

A decorator works when we know the interface and want one extra behavior. Sometimes we want the same extra behavior, such as timing, on every method of every interface, without writing a class for each one."""

# ---------------------------------------------------------------- section 2
J_PROXY = """@SuppressWarnings("unchecked")
static <T> T retrying(Class<T> iface, T target, int maxAttempts) {
    InvocationHandler handler = (proxy, method, args) -> {
        Throwable last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return method.invoke(target, args);
            } catch (InvocationTargetException e) {
                last = e.getCause();             // unwrap: the target's own exception
            }
        }
        throw last;
    };
    return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler);
}"""
K_PROXY = """inline fun <reified T : Any> retrying(target: T, maxAttempts: Int): T =
    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { _, method, args ->
        var last: Throwable? = null
        repeat(maxAttempts) {
            try {
                return@newProxyInstance method.invoke(target, *(args ?: emptyArray()))
            } catch (e: InvocationTargetException) {
                last = e.cause                    // unwrap: the target's own exception
            }
        }
        throw last!!
    } as T"""

S2 = """Back to the receptionist. Callers dial the manager's number, but the receptionist answers. She may put the call through, take a message, or try again later when the line is busy. A **proxy** is that receptionist in code: a stand-in with the same interface as the real object, which controls whether and how each call reaches it.

A decorator is written for one interface. A **dynamic proxy** is written once and works for any interface. `java.lang.reflect.Proxy` creates a class while the program runs, one that implements the interfaces you name and sends every call to a single **invocation handler**, one method that receives each call as data. Here is a proxy that retries any method of any interface:

""" + pair(J_PROXY, K_PROXY) + """

The handler gets the proxy, the `Method` being called, and its arguments. First it asks the real object, the **target**, with `method.invoke(target, args)`. If that throws, it remembers the exception and tries again, and after the last attempt it throws what it remembered. A retry, a timer or a check of who's calling is written once and covers every method of every interface you wrap.

The tricky line is the `catch`. `method.invoke` is an eager gift wrapper: whatever the target throws, it wraps in an `InvocationTargetException`. Unwrap it with `getCause()` and rethrow that. If you rethrow the wrapper instead, the proxy is throwing a checked exception that `book` never declared, and Java wraps it once more. `RetryingProxyDemo`, in the Try it, does exactly that when you remove the unwrap:

```text
Exception in thread "main" java.lang.reflect.UndeclaredThrowableException
Caused by: java.lang.reflect.InvocationTargetException
Caused by: java.lang.IllegalStateException: line busy
```

That's three layers of paper around one small `line busy`. Worse, no `catch (IllegalStateException e)` in the caller will match it.

**A handler must unwrap what `method.invoke` throws. Rethrow `getCause()`.**

JDK proxies have one more limit: they implement interfaces only, and can't extend a class. Tools that must proxy a class generate a subclass instead, and a subclass can't override `final` methods. The Kotlin version is shorter for one reason: `reified T` lets the function read `T::class.java` itself, so callers write `retrying(busy, 3)` and pass no `Class` object.

Before you wrap the shop's order line in this proxy, notice that it retries everything. A check of an order's status is safe to repeat. Placing an order isn't: if the first attempt timed out after the warehouse had already taken it, the second attempt orders the bread again. The worked example fixes that.

There's also a quieter gap, and the demo's third line shows it: `calls the proxy saw: [pickBoth]`. Two more calls happened that the proxy never saw."""

# ---------------------------------------------------------------- section 3
J_SELF = """class RealStockroom implements Stockroom {
    public void pick(String item) { /* walk to the shelf */ }

    public void pickBoth(String first, String second) {
        pick(first);                 // really this.pick(first): the real object, not the proxy
        pick(second);
    }
}"""
K_SELF = """class RealStockroom : Stockroom {
    override fun pick(item: String) { /* walk to the shelf */ }

    override fun pickBoth(first: String, second: String) {
        pick(first)                  // really this.pick(first): the real object, not the proxy
        pick(second)
    }
}"""

S3 = """Here is the stockroom from the demo. A tracing proxy, one that writes down the name of every call it handles, stands in front of it:

""" + pair(J_SELF, K_SELF) + """

The shop's code calls `pickBoth("tea", "jam")` on the proxy. The proxy writes down `pickBoth` and forwards the call to the real stockroom. Inside, `pick(first)` is a plain call on `this`, and `this` is the real stockroom, not the proxy. So the trace reads `[pickBoth]`, and the two walks to the shelf go unrecorded. A call that an object makes on itself is called **self-invocation**, and it never passes the proxy. The figure shows the two paths.

The receptionist picture holds here. She hears every call that comes in through the switchboard. When the manager walks to the next office herself, nobody at the front desk hears a thing.

The lab's timing proxy has the same gap, and a test pins it. `bookTwice` on the courier calls its own `book` twice, the timing sink records one line, `CourierBooking.bookTwice 7ms`, and the real courier counts two bookings. That isn't a bug in the proxy. A proxy is a separate object, and it can only handle calls that are made on it.

There are two ways to get the inner calls handled. Let the caller make them through the proxy, so `pick` is called twice from outside. Or move `pick` to its own object, behind its own proxy, and let `pickBoth` call that object. Either way, each call you care about crosses a proxy.

The picture breaks on judgment. A receptionist notices when the same caller has rung three times in a minute. A proxy sees only a method's name and its arguments, so it retries placing an order as happily as a status check, unless the method carries a mark that tells it otherwise.

**A proxy sees only the calls made on it. Calls through `this` go straight past.**

Decorator and Proxy have the same shape: an object with the same interface, holding the real one. What tells them apart is intent. A decorator adds behavior the caller asked for, such as a surcharge or compression. A proxy controls access to the real object: when, whether and how it gets called, as with retries, timing or a check of who's calling. `Collections.unmodifiableList` sits on the line, which is a good sign that the names are for talking about designs, not for sorting classes into boxes.

Check yourself. The timing proxy wraps the courier, and the shop's code calls `bookTwice` three times. How many lines does the timing sink record, and how many bookings does the real courier make? (Three lines, all named `bookTwice`, and six bookings. Each outside call passes the proxy once; each inner `book` goes straight to the real courier.)"""

ASIDE = {
 "title": "Why does a framework annotation sometimes do nothing?",
 "body": "If you write web services, your framework probably hands out proxies like ours. In Spring, a popular Java framework, an annotation such as `@Transactional` (run this method inside a database transaction, a group of changes that all succeed or all fail together) is carried out by a proxy that stands in front of your class. So a call from one of its methods to another, through `this`, skips the proxy, exactly like `pickBoth` calling `pick`; the Spring docs say self-invocation \"will bypass the advice\". Their preferred fix is to move the inner method to another class, so the call crosses a proxy. Quarkus, another framework, does intercept such calls, as a feature its docs mark non-standard, so the same code can behave differently in the two. And because Kotlin classes are final unless marked `open`, Kotlin Spring projects add the `kotlin-spring` compiler plugin, which opens Spring-annotated classes so the framework's subclass proxies can override them."
}

L = {
 "id": "pat-05",
 "title": "Decorator and Proxy",
 "minutes": 37,
 "goal": "By the end you can stack decorators and predict what their order does, use Kotlin `by` without falling into its forwarding trap, write a dynamic proxy that unwraps exceptions, and explain why a proxy never sees the calls an object makes on itself.",
 "opening": OPENING,
 "warmup": {
  "q": "A proxy times every call made to the shop's `Stockroom`. Through the proxy, you call `pickBoth(\"tea\", \"jam\")`. Inside the real stockroom, `pickBoth` calls its own `pick` method twice. How many calls does the proxy time?",
  "options": ["Three: `pickBoth` and both `pick` calls", "One: only `pickBoth`", "Two: only the two `pick` calls", "None: a proxy only times calls that return a value"],
  "answer": 1,
  "why": "The proxy is a separate object, and it only handles calls made on it. The shop's code calls `pickBoth` on the proxy, so that call is timed. Inside, `pick(first)` means `this.pick(first)`, and `this` is the real stockroom, so both inner calls go straight past the proxy. The last section of this lesson shows the two paths, and the Try it in the third section prints the trace `[pickBoth]`."
 },
 "sections": [
  {
   "h": "Decorators: wrap a delivery price and keep its shape",
   "body": S0,
   "try": {
    "title": "Stack two decorators in both orders",
    "minutes": 4,
    "steps": [
     "Open `DecoratorStack.java` (or `DecoratorStack.kt`). Big Blue Vans' booking line is busy twice, then it books, as booking lines tend to be. `Logging` writes down each call it sees; `Retrying` tries up to three times.",
     "Before you run it, write down how many log lines each of the two stacks writes.",
     "Run it with the command below. Then decide: if the log fed a chart of how many bookings the shop makes, which order would you want?"
    ],
    "code": code("java", "DecoratorStack.java", "DecoratorStack", "kotlin", "DecoratorStack.kt", "DecoratorStackKt"),
    "expect": "`Retrying(Logging(line)): BB-1250, log lines: 3` and `Logging(Retrying(line)): BB-1250, log lines: 1`. The inner decorator sees every attempt; the outer one sees one booking. For a chart of bookings, put the logging outside: one line per booking. To see how often the line is busy, put it inside, where both busy signals show up."
   },
   "refs": [
    {"title": "FilterInputStream (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/FilterInputStream.html", "kind": "docs"}
   ]
  },
  {
   "h": "Kotlin's by writes the forwarding, and never calls you back",
   "body": S1,
   "try": {
    "title": "Count what the delegate does behind your back",
    "minutes": 4,
    "steps": [
     "Read `CountingMapDemo.kt`. Predict `puts` after one `put` and a `putAll` of two entries, and `added` after an `addAll` of three items.",
     "Run it with the command below.",
     "Now run the Java twin, `CountingMapDemoJava`, which uses `extends HashMap` and `extends HashSet` with the same overrides. Predict first: will the Java numbers match?"
    ],
    "code": code("kotlin", "CountingMapDemo.kt", "CountingMapDemoKt", "java", "CountingMapDemoJava.java", "CountingMapDemoJava"),
    "expect": "Kotlin prints `CountingMap: puts=1, size=3` and `CountingSet: added=3, size=3`: the delegate never calls your overrides, so you count exactly what you wrote. Java prints `puts=1, size=3` but `added=6, size=3`, because `HashSet.addAll` calls `add` for each item and the override counts them a second time. With inheritance, your count depends on the parent's insides."
   },
   "refs": [
    {"title": "Delegation (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegation.html", "kind": "docs"},
    {"title": "Collections.unmodifiableList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)", "kind": "docs"}
   ]
  },
  {
   "h": "Proxies: one stand-in for every method of an interface",
   "body": S2,
   "try": {
    "title": "Break the retry proxy two ways",
    "minutes": 5,
    "steps": [
     "Run `RetryingProxyDemo` (Java or Kotlin) and read the three lines.",
     "In `main`, change `retrying(CourierLine.class, busy, 3)` to 2 attempts (`retrying(busy, 2)` in Kotlin). Predict what the caller sees, then run.",
     "Keep 2 attempts. In `retrying`, replace `last = e.getCause()` with `last = e` (in Kotlin, `last = e.cause` becomes `last = e`). Predict the exception, then run. Undo both changes."
    ],
    "code": code("java", "RetryingProxyDemo.java", "RetryingProxyDemo", "kotlin", "RetryingProxyDemo.kt", "RetryingProxyDemoKt"),
    "expect": "The first run prints `book -> BB-1250 after 3 target calls`, `proxy class: true` and `calls the proxy saw: [pickBoth]`. With 2 attempts the program stops with `IllegalStateException: line busy`, the target's own exception. Without the unwrap it stops with `java.lang.reflect.UndeclaredThrowableException`, caused by an `InvocationTargetException`, caused by the `IllegalStateException`: a checked wrapper escaped a method that doesn't declare it."
   },
   "refs": [
    {"title": "java.lang.reflect.Proxy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/Proxy.html", "kind": "docs"}
   ]
  },
  {
   "h": "The calls a proxy never sees",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Calls from outside go through the proxy. A call through this inside the real object goes straight to the target, so the proxy never handles it."},
   "aside": ASIDE,
   "refs": [
    {"title": "Spring Framework: proxying mechanisms (docs source)", "url": "https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc", "kind": "read"},
    {"title": "All-open compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/all-open-plugin.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A timing decorator for a three-method courier desk",
  "java": {"title": "TimedCourierDesk.java", "src": """interface CourierDesk {
    String book(String address, int grams);
    String track(String ref);
    void cancel(String ref);
}

// one method changes; the other two are forwarded by hand
final class TimedCourierDesk implements CourierDesk {
    private final CourierDesk inner;
    private final Map<String, Long> nanos;

    TimedCourierDesk(CourierDesk inner, Map<String, Long> nanos) {
        this.inner = inner;
        this.nanos = nanos;
    }

    @Override public String book(String address, int grams) {
        long start = System.nanoTime();
        try {
            return inner.book(address, grams);
        } finally {
            nanos.merge("book", System.nanoTime() - start, Long::sum);
        }
    }

    @Override public String track(String ref) { return inner.track(ref); }
    @Override public void cancel(String ref) { inner.cancel(ref); }
}"""},
  "kotlin": {"title": "TimedCourierDesk.kt", "src": """interface CourierDesk {
    fun book(address: String, grams: Int): String
    fun track(ref: String): String
    fun cancel(ref: String)
}

// `by inner` generates track and cancel; you write only what changes
class TimedCourierDesk(
    private val inner: CourierDesk,
    private val nanos: MutableMap<String, Long>,
) : CourierDesk by inner {
    override fun book(address: String, grams: Int): String {
        val start = System.nanoTime()
        try {
            return inner.book(address, grams)
        } finally {
            nanos.merge("book", System.nanoTime() - start) { a, b -> a + b }
        }
    }
}"""},
  "note": "The behavior is the same: time `book`, pass `track` and `cancel` straight on. What differs is who writes the passing-on. Java makes you type `track` and `cancel`, and Kotlin's `by inner` generates them. That matters again when the interface grows. Add `void reschedule(String ref)` to `CourierDesk` and the Java decorator stops compiling until someone decides what it should do with the new method. The Kotlin one forwards it without a word, untimed. Neither is wrong, but know which one you have. And remember that `by` never calls you back: if the real desk's `track` calls its own `book`, that inner booking isn't timed. Kotlin makes the hand-written forwarding class unnecessary; it doesn't make Decorator unnecessary."
 },
 "worked": {
  "title": "Make a retry proxy safe for orders",
  "steps": [
   {"say": "A teammate wrapped the shop's order line in the retrying proxy from this lesson, with three attempts. The warehouse sometimes takes 2 seconds to answer, and the shop's code gives up after 1.5 seconds. Before reading on, say what the customer gets on a slow afternoon.",
    "code": """interface OrderLine {
    String place(String item, int grams);
    String status(String orderNo);
}

OrderLine line = retrying(OrderLine.class, new WarehouseOrderLine(), 3);
line.place("rye bread", 800);   // attempt 1 gives up after 1.5 s, but the warehouse finishes it""", "lang": "java",
    "alt_code": """interface OrderLine {
    fun place(item: String, grams: Int): String
    fun status(orderNo: String): String
}

val line = retrying<OrderLine>(WarehouseOrderLine(), 3)
line.place("rye bread", 800)    // attempt 1 gives up after 1.5 s, but the warehouse finishes it""", "alt_lang": "kotlin"},
   {"say": "Attempt one gave up on our side, but the warehouse took the order anyway. Attempts two and three are new orders, so the customer gets two or three loaves. A retry is safe only for a call you can repeat without changing the result: the usual word for that is idempotent. Make that visible in the interface by marking the methods that are safe to repeat.",
    "code": """@Retention(RetentionPolicy.RUNTIME)       // 1. keep the mark while the program runs, so the handler can read it
@Target(ElementType.METHOD)
@interface SafeToRepeat {}

interface OrderLine {
    String place(String item, int grams);     // not marked: one attempt only
    @SafeToRepeat String status(String orderNo);   // a read: safe to repeat
}""", "lang": "java",
    "alt_code": """@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)   // 1. keep the mark while the program runs, so the handler can read it
annotation class SafeToRepeat

interface OrderLine {
    fun place(item: String, grams: Int): String        // not marked: one attempt only
    @SafeToRepeat fun status(orderNo: String): String   // a read: safe to repeat
}""", "alt_lang": "kotlin"},
   {"say": "The handler reads the mark before its loop, and unmarked methods get exactly one attempt. Why does `method.isAnnotationPresent` work here, even though the mark sits on the interface and not on `WarehouseOrderLine`? Because the `Method` the proxy receives is the interface's method.",
    "code": """InvocationHandler handler = (proxy, method, args) -> {
    int attempts = method.isAnnotationPresent(SafeToRepeat.class) ? maxAttempts : 1;   // 2. ask the method
    Throwable last = null;
    for (int i = 1; i <= attempts; i++) {
        try {
            return method.invoke(target, args);
        } catch (InvocationTargetException e) {
            last = e.getCause();                                                         // 3. unwrap
        }
    }
    throw last;
};""", "lang": "java",
    "alt_code": """val handler = InvocationHandler { _, method, args ->
    val attempts = if (method.isAnnotationPresent(SafeToRepeat::class.java)) maxAttempts else 1   // 2. ask the method
    var last: Throwable? = null
    repeat(attempts) {
        try {
            return@InvocationHandler method.invoke(target, *(args ?: emptyArray()))
        } catch (e: InvocationTargetException) {
            last = e.cause                                                                       // 3. unwrap
        }
    }
    throw last!!
}""", "alt_lang": "kotlin"},
   {"say": "Now make placing an order safe to repeat. The caller picks an order number once and sends it with every attempt. The warehouse keeps its first answer for each number and hands it back for a repeat, instead of taking a second order. The number must come from the caller: one made up inside the retry loop would be new on each attempt and protect nothing.",
    "code": """interface OrderLine {
    @SafeToRepeat String place(String orderNo, String item, int grams);   // 4. the warehouse remembers order numbers
    @SafeToRepeat String status(String orderNo);
}

line.place("7781", "rye bread", 800);   // 5. the same number on every attempt""", "lang": "java",
    "alt_code": """interface OrderLine {
    @SafeToRepeat fun place(orderNo: String, item: String, grams: Int): String   // 4. the warehouse remembers order numbers
    @SafeToRepeat fun status(orderNo: String): String
}

line.place("7781", "rye bread", 800)    // 5. the same number on every attempt""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A delivery fee decorator chain and a timing proxy",
  "minutes": 13,
  "files": [f"{lab}/main/{J}/DeliveryFee.java", f"{lab}/main/{J}/TimingProxy.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l05.*'",
  "steps": [
   "Run the tests once. All twelve fail with `UnsupportedOperationException`.",
   "In `DeliveryFee`, write `perKm` as a lambda: `d -> d.km() * centsPerKm`. Then write each default method so it returns a new lambda that calls `cents(d)` (the fee being decorated) and adds one rule.",
   "In `TimingProxy.wrap`, build an `InvocationHandler` and pass it to `Proxy.newProxyInstance`. Forward methods declared by `Object` without timing them. For the rest, read the clock, call `method.invoke(target, args)`, read the clock again and report `Interface.method`.",
   "Catch `InvocationTargetException`, report the call as failed, and rethrow `e.getCause()`.",
   "Run the tests until all twelve pass. Then read the self-invocation test and explain to yourself why only `bookTwice` is reported."
  ],
  "hints": [
   "Inside a default method, a bare `cents(d)` means `this.cents(d)`, where `this` is the fee you are decorating. The lambda you return captures it.",
   "\"Over 5 kg\" means strictly more: a parcel of exactly 5,000 g pays no surcharge, and a test checks it.",
   "`method.getDeclaringClass() == Object.class` is true for `toString`, `equals` and `hashCode` on a JDK proxy. Report with `iface.getSimpleName() + \".\" + method.getName()`. `throw e.getCause();` compiles because `InvocationHandler.invoke` is declared `throws Throwable`."
  ],
  "done_when": "All twelve tests in `DecoratorProxyTest` pass."
 },
 "drill": {
  "title": "A logging proxy from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `static <T> T logging(Class<T> iface, T target, List<String> log)` (in Kotlin, `inline fun <reified T : Any> logging(target: T, log: MutableList<String>): T`). It returns a JDK dynamic proxy that adds each method name to `log`, forwards the call, and lets the target's own exception reach the caller unwrapped. Then compare. Did you remember the unwrap?",
  "answer": {"lang": "java", "src": """@SuppressWarnings("unchecked")
static <T> T logging(Class<T> iface, T target, List<String> log) {
    InvocationHandler handler = (proxy, method, args) -> {
        log.add(method.getName());
        try {
            return method.invoke(target, args);
        } catch (InvocationTargetException e) {
            throw e.getCause();                    // the target's own exception, unwrapped
        }
    };
    return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler);
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """inline fun <reified T : Any> logging(target: T, log: MutableList<String>): T =
    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { _, method, args ->
        log += method.name
        try {
            method.invoke(target, *(args ?: emptyArray()))
        } catch (e: InvocationTargetException) {
            throw e.cause!!                        // the target's own exception, unwrapped
        }
    } as T"""}}
 },
 "recap": [
  "A decorator has the same interface as the object it wraps, adds one behavior and passes the call on. `java.io` streams and `Collections.unmodifiableList` are decorators.",
  "The order of the layers changes results: capping before the heavy-parcel surcharge turns an 8.00 delivery into 11.00, and retrying outside logging logs every attempt.",
  "Kotlin `by` generates the forwarding methods, but the delegate never calls your overrides: `putAll` skips your `put`.",
  "A dynamic proxy (`java.lang.reflect.Proxy`) sends every call on an interface to one handler. Unwrap `InvocationTargetException`, or callers get `UndeclaredThrowableException`.",
  "The limit: a proxy sees only the calls made on it, so an object's calls on `this` skip it, and it knows only a method's name and arguments. It can't tell a status check from an order that must happen once unless you mark the method."
 ],
 "closing": "We started at the counter, with a teapot in gift paper and a receptionist in the back office. In code, the paper became decorators around a delivery fee, where moving one layer changed the price, and Kotlin's `by` wrote the passing-on for us. The receptionist became a proxy that answers for every method, and misses every call an object makes on itself.\n\nNow look in your own code for a class that implements an interface and passes most calls to a field of the same type. That's a decorator. Check what order it's stacked in, and whether a test pins that order.\n\nNext, we'll stop wrapping one object and start building trees of them. How can a box full of smaller boxes answer \"what do you cost?\" as if it were one parcel?",
 "quiz": [
  {"q": "`DeliveryFee.perKm(50).plusFixed(200).cappedAt(800).heavySurcharge(5_000, 300)` prices a 12 kg parcel going 20 km. What does it return, in cents?",
   "options": ["800", "1,100", "1,500", "1,200"],
   "answer": 1,
   "why": "Work from the inside out: 20 km at 50 is 1,000, plus 200 to start is 1,200, capped at 800, and then the surcharge adds 300 after the cap. Total 1,100. The tempting 800 is what you get with the cap as the outermost layer."},
  {"q": "`class LoggedOrderBook(private val inner: OrderBook) : OrderBook by inner` overrides only `write(order)` to log a line. The real order book's `writeAll(orders)` calls its own `write` for each order. You call `logged.writeAll(listOf(a, b, c))`. How many lines are logged?",
   "options": ["3", "1", "0", "It depends on the JVM"],
   "answer": 2,
   "why": "`writeAll` is forwarded to `inner.writeAll`, and `inner` calls its own `write`, never the override in `LoggedOrderBook`. The delegate never calls you back. To log bulk writes, override `writeAll` too."},
  {"q": "An `InvocationHandler` does `return method.invoke(target, args);` with no try/catch. The target throws `IllegalArgumentException`. What does the caller of the proxy catch?",
   "options": ["`IllegalArgumentException`", "`InvocationTargetException`", "Nothing: the proxy swallows it", "`UndeclaredThrowableException`"],
   "answer": 3,
   "why": "`method.invoke` wraps the target's exception in `InvocationTargetException`, a checked exception. The interface method doesn't declare it, so the proxy wraps it again in `UndeclaredThrowableException`. Catch the `InvocationTargetException` in the handler and rethrow `getCause()`."},
  {"q": "You need to record how long every method takes on six different interfaces (about forty methods in all), with one rule for all of them. Which tool fits best?",
   "options": ["A dynamic proxy, or your framework's interceptor", "A hand-written decorator class per interface", "Kotlin `by` with one override per method", "An adapter per interface"],
   "answer": 0,
   "why": "One rule applied to every method of many interfaces is what a proxy is for: one handler, written once. Hand-written decorators and `by` overrides mean forty copies of the same timing code, and an adapter changes the interface, which you don't want here."},
  {"q": "From *Adapter and Facade*: which of these wrappers is an adapter rather than a decorator?",
   "options": ["`TimedWarehouse implements Warehouse`, wrapping a `Warehouse`", "`BufferedInputStream`, wrapping an `InputStream`", "`WarehouseAdapter implements Warehouse`, wrapping an `OldWarehouseSystem`", "`Collections.unmodifiableList(list)`"],
   "answer": 2,
   "why": "An adapter gives the wrapped object a different interface: the shop's `Warehouse` port instead of the old program's item numbers and two-digit codes. The other three keep the interface of the object they wrap and add or restrict behavior, which is what a decorator does.",
   "from": "pat-04"}
 ],
 "flashcards": [
  {"front": "What makes a wrapper a decorator?", "back": "It has the same interface as the object it wraps, adds one behavior, and passes the call on. Callers can't tell it's there."},
  {"front": "Retry decorator outside a logging decorator, and the line is busy twice before it books: how many log lines?", "back": "Three. The inner decorator sees every attempt; the outer one sees one booking."},
  {"front": "`CountingMap : MutableMap by inner` overrides `put`. After `put` once and `putAll` of two entries, what is `puts`?", "back": "1. `putAll` is forwarded to `inner`, which never calls your override."},
  {"front": "What does `Collections.unmodifiableList(list)` give you?", "back": "A read-through view: writes throw, but later changes to `list` show up. Use `List.copyOf` for a frozen copy."},
  {"front": "In an `InvocationHandler`, why rethrow `e.getCause()` from `InvocationTargetException`?", "back": "`method.invoke` wraps the target's exception. If the wrapper escapes, callers get `UndeclaredThrowableException` instead of the real error."},
  {"front": "A proxied object calls its own method through `this`. Does the proxy handle that call?", "back": "No. Self-invocation goes straight to the real object; a proxy only sees calls made on it."},
  {"front": "Decorator and Proxy have the same shape. What tells them apart?", "back": "Intent. A decorator adds behavior the caller wants; a proxy controls whether, when and how the real object is called."}
 ],
 "terms": [
  {"term": "Decorator", "plain": "A wrapper with the same interface as the object inside it, adding one behavior."},
  {"term": "Proxy", "plain": "A stand-in with the same interface that controls whether and how the real object is called: retrying, timing, checking."},
  {"term": "Dynamic proxy", "plain": "A class made while the program runs by `java.lang.reflect.Proxy`, which implements interfaces and routes every call to one handler."},
  {"term": "InvocationHandler", "plain": "The one method, `invoke(proxy, method, args)`, that a dynamic proxy calls for every interface method."},
  {"term": "Class delegation (`by`)", "plain": "Kotlin syntax that generates the forwarding methods of an interface, sending each call to a delegate object."},
  {"term": "Self-invocation", "plain": "An object calling its own method through `this`, which skips any proxy in front of it."},
  {"term": "View", "plain": "A wrapper that reads through to the collection it wraps, so later changes to that collection show up in it."}
 ],
 "explain_back": {
  "prompt": "A teammate wraps the stockroom in a timing proxy and says: \"`pickBoth` shows up in the timings, but the two `pick` calls inside it never do. The proxy is broken.\" Explain what is happening, and give two ways to get the inner calls timed.",
  "answer": "The proxy isn't broken. It's a separate object that stands in front of the real stockroom, and it can only handle calls made on it. The shop's code calls `pickBoth` on the proxy, so that call is timed and forwarded. Inside the real stockroom, `pick(first)` is `this.pick(first)`, and `this` is the real object, so the two inner calls never pass the proxy. To time them, either make them through the proxy, so the caller calls `pick` twice itself, or move `pick` to its own object behind its own proxy and let `pickBoth` call that object. Frameworks that put proxies in front of our classes behave the same way, which is why an annotation on a method called through `this` can silently do nothing."
 },
 "deeper": {
  "minutes": 10,
  "body": """JDK proxy classes are final, extend `java.lang.reflect.Proxy`, and can be detected with `Proxy.isProxyClass`. Their names aren't specified, but names starting with `$Proxy` are reserved for them, which is why stack traces show `$Proxy0.book`, as the demo's did. A proxy also sends `equals`, `hashCode` and `toString` to the handler, so a proxy and its target are different objects to a `HashSet` unless the handler forwards those methods. The lab's timing proxy forwards them on purpose.

Resilience4j, a widely used Java library for calls that may fail, is a decorator library by design. Its README says it provides "higher-order functions (decorators)" for any functional interface, lambda or method reference, and that you can stack more than one. You wrap a `Supplier` in a retry, wrap the result in a circuit breaker (a switch that stops calling a service that keeps failing), and so on. The order question from this lesson comes back: a retry outside the breaker retries calls the breaker refused, and a retry inside it counts every attempt as a call. Lesson 11 of this track, *Concurrency patterns that tie it all together*, builds a breaker by hand.

The GoF book lists several kinds of proxy by job. A virtual proxy creates the expensive real object only on the first call, like the lazy price list in lesson 1 of this track. A remote proxy makes an object in another program look local. A protection proxy checks who is calling. All three have the same structure as a decorator, which is why intent, not shape, is how people tell them apart."""
 },
 "sources": [
  {"title": "Delegation (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegation.html"},
  {"title": "java.lang.reflect.Proxy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/reflect/Proxy.html"},
  {"title": "Spring Framework: proxying mechanisms (docs source)", "url": "https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc"},
  {"title": "Quarkus CDI reference (docs source)", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc"},
  {"title": "Resilience4j README", "url": "https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc"}
 ]
}

out = ROOT / "content/lessons/pat-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
