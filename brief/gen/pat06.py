import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l06"
K = "kotlin/workbench/patterns/l06"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l06.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 640 282" role="img" aria-label="The breakfast box as a tree: a Box at the root holds bread at 2.50, jam at 3.00 and a smaller Box holding tea at 4.50; the root adds up what its contents return, 10.00">
<rect class="box-a" x="210" y="16" width="220" height="50" rx="8"/>
<text class="t t-code" x="320" y="38" text-anchor="middle">Box</text>
<text class="t-s t-a" x="320" y="56" text-anchor="middle">2.50 + 3.00 + 4.50 = 10.00</text>
<rect class="box" x="40" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="110" y="144" text-anchor="middle">Item bread</text>
<text class="t-s t-m" x="110" y="162" text-anchor="middle">2.50</text>
<rect class="box" x="250" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="320" y="144" text-anchor="middle">Item jam</text>
<text class="t-s t-m" x="320" y="162" text-anchor="middle">3.00</text>
<rect class="box-b" x="460" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="530" y="144" text-anchor="middle">Box</text>
<text class="t-s" x="530" y="162" text-anchor="middle">4.50</text>
<rect class="box" x="460" y="220" width="140" height="50" rx="8"/>
<text class="t t-code" x="530" y="242" text-anchor="middle">Item tea</text>
<text class="t-s t-m" x="530" y="260" text-anchor="middle">4.50</text>
<line class="ln" x1="290" y1="66" x2="120" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="320" y1="66" x2="320" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="350" y1="66" x2="520" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="530" y1="172" x2="530" y2="217" marker-end="url(#arr)"/>
<text class="t-s t-m" x="220" y="232" text-anchor="middle">price() asks every node</text>
<text class="t-s t-m" x="220" y="250" text-anchor="middle">the same question: item or box</text>
</svg>""".replace("\n", "")

OPENING = """The corner shop's Saturday breakfast box holds a loaf, a jar of jam and a smaller box of tea. Ask what it costs and you get one price, because each box adds up what it holds. Across the street, the sign shop paints SALE banners with one stencil for every letter A. And in the shop's back room, one TV remote works with any brand of TV.

The shop's program meets all three shapes. Boxes hold items and other boxes. Notices such as "your order is on its way" go out by text message or by email. And thousands of order lines name the same few hundred products. The easy traps are an `if` for every kind of box, a class for every notice on every channel, and a fresh copy of the same product on every line.

In the last lesson, one object wrapped another. In this lesson, we'll build trees where a group answers like a single item (Composite), split two things that vary on their own (Bridge), and share one object among many users (Flyweight). Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_TREE = """sealed interface Goods permits Item, Box {}
record Item(String name, long cents) implements Goods {}
record Box(List<Goods> contents) implements Goods {
    Box { contents = List.copyOf(contents); }          // immutable: copy what the caller passed
}

static long price(Goods g) {
    return switch (g) {                                 // no default
        case Item i -> i.cents();
        case Box b -> b.contents().stream().mapToLong(x -> price(x)).sum();
    };
}

Goods breakfast = new Box(List.of(new Item("bread", 250), new Item("jam", 300),
        new Box(List.of(new Item("tea", 450)))));"""
K_TREE = """sealed interface Goods {
    data class Item(val name: String, val cents: Long) : Goods
    class Box(contents: List<Goods>) : Goods {
        val contents: List<Goods> = contents.toList()    // immutable: copy what the caller passed
    }
}

fun price(g: Goods): Long = when (g) {                  // no else
    is Goods.Item -> g.cents
    is Goods.Box -> g.contents.sumOf { price(it) }
}

val breakfast = Goods.Box(listOf(Goods.Item("bread", 250), Goods.Item("jam", 300),
    Goods.Box(listOf(Goods.Item("tea", 450)))))"""

S0 = """Here's the Saturday breakfast box from the order template in *Builder and Prototype*: a loaf of bread, a jar of jam, and a small box of tea packed inside the big box. Ask the big box what it costs, and it asks each thing it holds. The bread says 2.50 and the jam says 3.00. The small box asks its own tea, which says 4.50. The big box adds them up: 10.00.

That's **Composite**: single items and groups of items share one interface, and a group answers by asking what it holds. The code that prices a box never checks whether it holds one jar or a crate of boxes. In tree words, an item with nothing inside is a **leaf**, and a box is a node with children.

*Design Patterns*, the 1994 book that named these patterns, builds Composite from an abstract `Component` class with `add` and `remove` methods that leaves must implement somehow. Since Java 21, and in Kotlin from the start, a sealed type and one exhaustive switch, a switch that must cover every case, replace it. A **sealed** type lists all its subtypes up front, so the compiler knows every case:

""" + pair(J_TREE, K_TREE) + """

`price(breakfast)` is 1,000 cents, as in the figure. `price` calls itself for each thing a box holds, which is called recursion, and the recursion follows the tree: a `Box` adds up whatever its contents return, and the contents don't care who asked. A box of two breakfast boxes costs 2,000, with no new code.

The sealed type buys two things. The switch has no `default`, so adding a third kind of node, say a `Deal`, makes javac report "the switch expression does not cover all possible input values" (kotlinc says "'when' expression must be exhaustive") at every place that prices or prints goods. And a second operation over the same tree, such as `describe` for the receipt, is just another function. The node classes don't change.

The box picture breaks in one place. A cardboard box can't change once it's taped shut, but a Java list can. Build a box from a list that someone else still holds, and the box changes when they edit the list. `CompositeDemo`, in the Try it, does exactly that once you delete the copy:

```text
box: (bread 2.50 + jam 3.00 + (tea 4.50))
after editing the source list: (bread 2.50 + jam 3.00 + (tea 4.50 + champagne 30.00))
```

A breakfast box already promised to a customer quietly gained a bottle of champagne, and its price went up by 30.00. `List.copyOf` in the compact constructor, the short record constructor that can adjust values before they are stored, stops that. Kotlin's `List` is only a read-only view, so the Kotlin box copies with `toList()`. An immutable tree can't grow a loop either, and threads can share it safely, which the last section relies on.

**Build the tree from copies. Then it can't change behind your back.**

One tree, several operations. Next, two things in the program that change on their own."""

# ---------------------------------------------------------------- section 1
J_BRIDGE = """interface Channel { void deliver(String to, String body); }          // implementor: how it travels

sealed interface Notice permits OnItsWay, SoldOut {                   // abstraction: what to say
    void send(String to);
}
record OnItsWay(Channel channel, String orderNo) implements Notice {
    public void send(String to) { channel.deliver(to, "order " + orderNo + " is on its way"); }
}
record SoldOut(Channel channel, String item, int days) implements Notice {
    public void send(String to) { channel.deliver(to, item + " is sold out, back in " + days + " days"); }
}

new OnItsWay(sms, "7781").send("Ana");
new OnItsWay(email, "7781").send("Ana");    // same notice, other channel: no new class"""
K_BRIDGE = """fun interface Channel { fun deliver(to: String, body: String) }       // implementor: how it travels

sealed interface Notice { fun send(to: String) }                      // abstraction: what to say
data class OnItsWay(val channel: Channel, val orderNo: String) : Notice {
    override fun send(to: String) = channel.deliver(to, "order $orderNo is on its way")
}
data class SoldOut(val channel: Channel, val item: String, val days: Int) : Notice {
    override fun send(to: String) = channel.deliver(to, "$item is sold out, back in $days days")
}

OnItsWay(sms, "7781").send("Ana")
OnItsWay(email, "7781").send("Ana")         // same notice, other channel: no new class"""

S1 = """The shop sends customers short notices: "order 7781 is on its way", "rye bread is sold out, back in 2 days". Each can go by SMS, a text message to a phone, or by email. Model that with inheritance (`OnItsWaySms`, `OnItsWayEmail`, `SoldOutSms`, `SoldOutEmail`) and you write four classes. A third channel costs two more, a third notice costs three more, and each one is a near copy of its neighbors.

Now think of a TV remote and the TV. The remote's buttons say what you want: louder, next channel. The TV decides how to do it. One remote works with any brand of TV that understands its signal, so nobody builds a separate remote for every model.

**Bridge** splits code the same way, into two sides that vary on their own. The **abstraction** says what you want: the notice and its words. The **implementor** says how it gets done: the channel that carries the words. Each notice holds a channel and calls it:

""" + pair(J_BRIDGE, K_BRIDGE) + """

Two notices and two channels are now four small pieces, and a new channel is one more. Every notice works with it, because notices only know `Channel`. Tests pass a recording lambda as the channel and check the words, with no phone in sight. In Kotlin, the implementor side often shrinks to a function: with `fun interface Channel`, the lambda `Channel { to, body -> println("$to: $body") }` is a whole channel.

The picture breaks in one place. A universal remote learns each brand's signals, so it bends to fit the TV. In a bridge, every channel is written to fit our `Channel` interface. When a channel wraps someone else's code, such as a text-message service with its own method names, that wrapper is an adapter, as in *Adapter and Facade*.

That's also how to tell Bridge from Adapter. Both put an interface between two pieces of code. You design a bridge up front, because you know two things will vary. You write an adapter afterwards, because a class you can't change has the wrong shape. They often meet: each channel is usually an adapter around someone's service.

**Two things that vary on their own get two sides and one interface between them.**

Skip the bridge when only one side varies. If every notice goes by email, a notice with a `MailServer` field is plain composition, and calling it a pattern adds nothing.

Composite and Bridge arrange objects. The next pattern asks how many of them we need at all."""

# ---------------------------------------------------------------- section 2
J_BOX = """Integer a = 127, b = 127;
Integer c = 128, d = 128;
System.out.println(a == b);       // true
System.out.println(c == d);       // false"""
K_BOX = """val a: Any = 127; val b: Any = 127    // typed Any, so Kotlin boxes them as Java does
val c: Any = 128; val d: Any = 128
println(a === b)                      // true: === asks "the same object?"
println(c === d)                      // false"""
J_BUG = """Long onShelf = stockGrams.get("coffee");    // 2,500, boxed when it went into the map
Long ordered = orderGrams.get("coffee");    // 2,500, boxed separately
if (onShelf == ordered) { ... }             // false: two different Long objects
if (onShelf.equals(ordered)) { ... }        // true"""
K_BUG = """val onShelf: Long? = stockGrams["coffee"]   // 2,500
val ordered: Long? = orderGrams["coffee"]   // 2,500
if (onShelf == ordered) { /* ... */ }       // true: == calls equals()
if (onShelf === ordered) { /* ... */ }      // false, and the compiler warns"""

S2 = """The sign shop across the street paints SALE banners. The painter has one stencil for the letter A and uses it every time an A appears; BANANA takes the same stencil three times. The stencil holds the shape. Where each letter goes, and in what color, belongs to each use.

A **flyweight** is that stencil in code: one small object that never changes, shared by many users instead of copied for each. Java has several built in, and one of them surprises everyone once:

""" + pair(J_BOX, K_BOX) + """

`==` on objects asks "the same object?", not "the same value?". **Autoboxing**, Java's automatic wrapping of an `int` in an `Integer` object, calls `Integer.valueOf`, which "will always cache values in the range -128 to 127, inclusive". So 127 comes from a shared drawer of ready-made objects, and 128 is a new object every time. That drawer is a flyweight.

The JDK has more. The JVM interns string literals, which means it keeps one `String` object per literal, and `s.intern()` returns the pooled copy of any string. `Currency` "is designed so that there's never more than one Currency instance for any given currency", which is why you call `Currency.getInstance("EUR")` instead of `new`. Enums are flyweights by definition, and so are Kotlin's `object` and `data object`.

The drawer also explains an old Java bug:

""" + pair(J_BUG, K_BUG) + """

Test data such as 100 g sits inside the drawer, so the check passes. Real stock like 2,500 g doesn't, so it fails. The drawer stops at 127, which is about where test data stops and real stock begins. Kotlin's `==` calls `equals`, so you meet this bug only with `===`, and on `Long?` kotlinc warns: "Identity equality for arguments of types 'Long?' and 'Long?' is prohibited."

You build your own flyweight with a **canonicalizing factory**: a private constructor, and an `of` method that returns the one pooled instance for a key. Keep the pool in a `ConcurrentHashMap` and use `computeIfAbsent`, which checks and inserts in one atomic step, a step no other thread can cut into. Eight threads asking for a new product code at the same moment still get one instance. A `get` followed by a `put` on a miss is check-then-act: another thread can slip in between the check and the act, so under load it builds duplicates.

The stencil picture breaks on sharing. Only one painter at a time can hold a stencil. A flyweight can be used by many threads at the same instant, because nothing in it ever changes. That's the first rule: flyweights must be immutable, because every holder sees every change. The second is that the pool must be bounded. Pool the shop's catalog, a few hundred known codes, and never every customer name typed into an order form.

**Share only what never changes, and only from a set you know.**

We now have shared boxes and shared products. Let's see what may live inside a shared object, and what must stay outside it."""

# ---------------------------------------------------------------- section 3
S3 = """Composite and Flyweight work well together. The shop sells the Saturday breakfast box hundreds of times. It doesn't need hundreds of box trees: it builds the tree once and lets every order point at it, as every A on a banner uses the same stencil.

*Design Patterns* names the split that makes this work. **Intrinsic state** lives inside the shared object and is the same for every user: what the box holds and what each item costs. **Extrinsic state** belongs to one use, so the order keeps it or the caller passes it in: who ordered the box, where it goes, how many boxes. A breakfast box with a `customer` field could not be shared, by two orders or by two threads.

Sharing across threads costs nothing here, because the trees never change. Records have final fields, `List.copyOf` returns a list nobody can modify, and an object that never changes can be read by 200 threads at once with no lock, once it has been **published safely**: stored where other threads are guaranteed to see it fully built, such as a `static final` field, or set before the threads start. *Don't share: immutability, confinement, ThreadLocal* in the concurrency track showed why that holds.

The same thinking fits the small values that appear on every order line: delivery methods, units, product codes. If the set is closed and known when you compile, an `enum` (Java) or `enum class` (Kotlin) is the flyweight, with no pool to write. Reach for a pooled factory only when the set is open but bounded, such as product codes loaded from the catalog.

**Keep the shared object's state the same for everyone. Each use brings its own details.**

In the lab you build both halves. `Goods` is a five-node composite: items, goods sold by weight, boxes, a percentage off and a deal with a maximum price, priced and described by two functions. `Product` is a catalog flyweight that stays correct when eight threads ask for the same code at once.

Check yourself. The shop wants each breakfast box to show who ordered it, and a teammate adds `var orderedBy` to the shared box tree. What goes wrong, and where should the name live? (Every order of the breakfast box points at that one tree, so every order shows whoever ordered last, and two threads writing the name at once can mix them up. The name is extrinsic state: keep it on the order, outside the tree.)"""

L = {
 "id": "pat-06",
 "title": "Composite, Bridge and Flyweight",
 "minutes": 36,
 "goal": "By the end you can model a box of goods as an immutable sealed tree priced by one exhaustive switch, split two independent dimensions with a bridge, and share immutable values through a thread-safe flyweight factory without falling for boxed `==`.",
 "opening": OPENING,
 "warmup": {
  "q": "In Java, `Integer a = 127, b = 127;` and `Integer c = 128, d = 128;`. What do `a == b` and `c == d` print with default JVM settings?",
  "options": ["true and true", "true and false", "false and false", "It doesn't compile: `==` can't compare Integer objects"],
  "answer": 1,
  "why": "Autoboxing calls `Integer.valueOf`, which always returns a cached, shared object for -128 to 127. So `a` and `b` are the same object. 128 is outside the cache, so `c` and `d` are two different objects with equal values, and `==` on objects compares which object, not which value. That shared cache is a flyweight, and it's the reason boxed `==` bugs pass tests that use small numbers."
 },
 "sections": [
  {
   "h": "Composite: a box of boxes priced like one item",
   "body": S0,
   "figure": {"svg": FIG, "caption": "The big box adds up what its contents return. The small box answers the same question, so one recursive function prices any box."},
   "try": {
    "title": "Price a box, then let someone edit its list",
    "minutes": 4,
    "steps": [
     "Open `CompositeDemo.java` (or `CompositeDemo.kt`). Before you run it, work out both prices in your head.",
     "Run it with the command below and check your numbers. Note the last line.",
     "Remove the copy: in Java delete the compact constructor `Box { contents = List.copyOf(contents); }`; in Kotlin change `= contents.toList()` to `= contents`. Predict the last line, then run."
    ],
    "code": code("java", "CompositeDemo.java", "CompositeDemo", "kotlin", "CompositeDemo.kt", "CompositeDemoKt"),
    "expect": "`box: (bread 2.50 + jam 3.00 + (tea 4.50))`, `price: 1000 cents`, `a box of two breakfast boxes: 2000 cents`, and the last line unchanged. Without the copy, the last line becomes `(bread 2.50 + jam 3.00 + (tea 4.50 + champagne 30.00))`: a box already in use changed because someone edited the list they built it from."
   },
   "refs": [
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Bridge: notices and channels that vary on their own",
   "body": S1,
   "try": {
    "title": "Add a channel without touching a notice",
    "minutes": 4,
    "steps": [
     "Run `BridgeDemo` in either language and count the lines: 2 notices times 2 channels.",
     "Add a postcard channel. Java: `record Postcard() implements Channel { public String deliver(String to, String body) { return \"CARD  to \" + to + \": \" + body; } }`, then add `new Postcard()` to the list. Kotlin: `private val postcard = NoticeChannel { to, body -> \"CARD  to $to: $body\" }`, then add `postcard` to the list.",
     "Predict how many lines print and how many notice types you had to edit. Run it."
    ],
    "code": code("java", "BridgeDemo.java", "BridgeDemo", "kotlin", "BridgeDemo.kt", "BridgeDemoKt"),
    "expect": "Four lines before, starting `SMS   to Ana: order 7781 is on its way with Pedal Post`. Six after, the last two starting `CARD  to Ana` and `CARD  to Ben`. You edited zero notice types. In Kotlin the new channel was one lambda; in Java it was one small record."
   },
   "refs": [
    {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html", "kind": "docs"}
   ]
  },
  {
   "h": "Flyweight: share one unchanging object instead of building new ones",
   "body": S2,
   "try": {
    "title": "Find out which objects are shared",
    "minutes": 4,
    "steps": [
     "Read `FlyweightDemo.java` (or `FlyweightDemo.kt`) and predict all five lines before you run it.",
     "Run it with the command below.",
     "Break the pool: make `Product.of` return `new Product(code)` (Kotlin: make `CatalogProduct.of` return `CatalogProduct(code)`). Predict the last line, then run."
    ],
    "code": code("java", "FlyweightDemo.java", "FlyweightDemo", "kotlin", "FlyweightDemo.kt", "FlyweightDemoKt"),
    "expect": "127 is shared (`true`), 128 is not (`false`, though `equals` is `true`), a code read as `\"T-1001\"` is a different object until you call `intern()`, `Currency` hands out one EUR, and the pool gives one product with `instances built: 1`. Without the pool, the last line reads `false   instances built: 2`."
   },
   "refs": [
    {"title": "Integer.valueOf(int) (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Integer.html#valueOf(int)", "kind": "docs"},
    {"title": "Currency (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Currency.html", "kind": "docs"}
   ]
  },
  {
   "h": "Share the box, keep each order's details outside it",
   "body": S3
  }
 ],
 "compare": {
  "title": "A flyweight that callers can't go around",
  "java": {"title": "Product.java", "src": """// Not a record: a record's canonical constructor can't be private,
// so `new Product(...)` would always go around the pool.
public final class Product {
    private static final Map<String, Product> POOL = new ConcurrentHashMap<>();

    private final String code;          // the catalog code, such as "T-1001"
    private final String name;

    private Product(String code, String name) {
        this.code = code;
        this.name = name;
    }

    public static Product of(String code, Function<String, String> nameLookup) {
        return POOL.computeIfAbsent(code, c -> new Product(c, nameLookup.apply(c)));   // built once per code
    }

    public String code() { return code; }
    public String name() { return name; }
}"""},
  "kotlin": {"title": "Product.kt", "src": """// A plain class: a private constructor holds, and there is no generated copy() to go around it.
class Product private constructor(val code: String, val name: String) {
    companion object {
        private val pool = ConcurrentHashMap<String, Product>()

        fun of(code: String, nameLookup: (String) -> String): Product =
            pool.computeIfAbsent(code) { Product(it, nameLookup(it)) }   // built once per code
    }
}"""},
  "note": "Both use `computeIfAbsent`, so the lookup runs at most once per code even when many threads ask at once. The real difference is what each language lets you hide. A Java record would be the natural value type, but javac rejects a private canonical constructor (\"attempting to assign stronger access privileges; was public\"), so anyone could call `new` and skip the pool: use a final class. In Kotlin, a `data class` with a private constructor still exposes a public `copy()` in 2.4 unless you add `@ConsistentCopyVisibility`, as *Builder and Prototype* showed, so a plain class is the safe choice there too. Kotlin also makes the flyweight's identity matter less: `==` calls `equals`, so the pool is about memory and one place to check codes, not about making comparisons work. For a closed set, skip the pool and use an enum in either language."
 },
 "worked": {
  "title": "Turn a notice class explosion into a bridge",
  "steps": [
   {"say": "The shop's notice code grew by inheritance. Count the classes, then count what a voice-message channel would cost.",
    "code": """abstract class Notice { abstract void send(); }

class OnItsWaySms extends Notice   { void send() { texts.send(phone, "order " + orderNo + " is on its way"); } }
class OnItsWayEmail extends Notice { void send() { mail.send(address, "Your order", "order " + orderNo + " is on its way"); } }
class SoldOutSms extends Notice    { void send() { /* the SMS code again */ } }
class SoldOutEmail extends Notice  { void send() { /* the email code again */ } }
// voice messages: OnItsWayVoice, SoldOutVoice, and one more per future notice""", "lang": "java",
    "alt_code": """abstract class Notice { abstract fun send() }

class OnItsWaySms : Notice()   { override fun send() = texts.send(phone, "order $orderNo is on its way") }
class OnItsWayEmail : Notice() { override fun send() = mail.send(address, "Your order", "order $orderNo is on its way") }
class SoldOutSms : Notice()    { override fun send() { /* the SMS code again */ } }
class SoldOutEmail : Notice()  { override fun send() { /* the email code again */ } }
// voice messages: OnItsWayVoice, SoldOutVoice, and one more per future notice""", "alt_lang": "kotlin"},
   {"say": "Four classes for two notices and two channels, and voice messages add two more. Name the two dimensions: the notice decides the words, the channel decides how they travel. Pull the travel out behind one interface, the implementor.",
    "code": """interface Channel { void deliver(String to, String body); }               // 1. the implementor side

record SmsChannel(TextService texts) implements Channel {                   // 2. one class per channel,
    public void deliver(String to, String body) { texts.send(to, body); }   //    usually an adapter
}
record EmailChannel(MailServer mail) implements Channel {
    public void deliver(String to, String body) { mail.send(to, "Your order", body); }
}""", "lang": "java",
    "alt_code": """fun interface Channel { fun deliver(to: String, body: String) }          // 1. the implementor side

class SmsChannel(private val texts: TextService) : Channel {                // 2. one class per channel,
    override fun deliver(to: String, body: String) = texts.send(to, body)   //    usually an adapter
}
class EmailChannel(private val mail: MailServer) : Channel {
    override fun deliver(to: String, body: String) = mail.send(to, "Your order", body)
}""", "alt_lang": "kotlin"},
   {"say": "Each notice now holds a channel and builds only its words. Ask yourself: which notice would change if the text-message service changed its method names? None. Only `SmsChannel` would.",
    "code": """sealed interface Notice permits OnItsWay, SoldOut { void send(String to); }   // 3. the abstraction side

record OnItsWay(Channel channel, String orderNo) implements Notice {
    public void send(String to) { channel.deliver(to, "order " + orderNo + " is on its way"); }
}
record SoldOut(Channel channel, String item, int days) implements Notice {
    public void send(String to) { channel.deliver(to, item + " is sold out, back in " + days + " days"); }
}""", "lang": "java",
    "alt_code": """sealed interface Notice { fun send(to: String) }                              // 3. the abstraction side

data class OnItsWay(val channel: Channel, val orderNo: String) : Notice {
    override fun send(to: String) = channel.deliver(to, "order $orderNo is on its way")
}
data class SoldOut(val channel: Channel, val item: String, val days: Int) : Notice {
    override fun send(to: String) = channel.deliver(to, "$item is sold out, back in $days days")
}""", "alt_lang": "kotlin"},
   {"say": "Test each side alone. A recording lambda is a complete channel, so notice tests need no phone and no mail server. Voice messages are now one class, and no notice changes.",
    "code": """List<String> sent = new ArrayList<>();
Channel recording = (to, body) -> sent.add(to + ": " + body);              // 4. a fake channel in one line

new OnItsWay(recording, "7781").send("Ana");
assertThat(sent).containsExactly("Ana: order 7781 is on its way");""", "lang": "java",
    "alt_code": """val sent = mutableListOf<String>()
val recording = Channel { to, body -> sent += "$to: $body" }                // 4. a fake channel in one line

OnItsWay(recording, "7781").send("Ana")
assertThat(sent).containsExactly("Ana: order 7781 is on its way")""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A priced box of goods and a catalog flyweight",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/Goods.kt", f"{lab}/main/{K}/Product.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l06.*'",
  "steps": [
   "Read the five node types in `Goods.kt`; they are given. Run the tests: all eight fail.",
   "Write `price` as one `when (this)` with five branches and no `else`. Leaves compute (`ByWeight` is `grams * centsPerKg / 1_000`); `Box` adds up its contents; `PercentOff` is `inside.price() * (100 - percent) / 100`; `Deal` is `minOf(inside.price(), maxCents)`.",
   "Write `describe` the same way, following the formats in its KDoc.",
   "In `Product`, add a private pool to the companion object and write `of`: reject unknown codes first, then return the pooled instance.",
   "Run the tests until all eight pass. Then add `data class Free(val name: String) : Goods` to the sealed interface, read the two compiler errors, and delete it again."
  ],
  "hints": [
   "`contents.sumOf { it.price() }` returns a `Long` when the lambda does, and an empty list sums to 0.",
   "`joinToString(\" + \", \"(\", \")\") { it.describe() }` takes a separator, a prefix and a postfix, and gives `()` for an empty list. `\"%d.%02d\".format(cents / 100, cents % 100)` turns 5 into `0.05`.",
   "`requireNotNull(CATALOG[code]) { \"unknown product: $code\" }` throws `IllegalArgumentException`. Then `pool.computeIfAbsent(code) { Product(it, name) }`: a `get` then `put` would let two threads both build one."
  ],
  "done_when": "All eight tests in `CompositeFlyweightTest` pass."
 },
 "drill": {
  "title": "The box composite from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a sealed `Goods` with an `Item` and an immutable `Box`, and a `price` function that prices any tree with one exhaustive switch (or `when`) and no default. Then price a box holding bread at 2.50 and a smaller box with jam at 3.00, in your head. You should get 550 cents.",
  "answer": {"lang": "java", "src": """sealed interface Goods permits Item, Box {}
record Item(String name, long cents) implements Goods {}
record Box(List<Goods> contents) implements Goods {
    Box { contents = List.copyOf(contents); }        // immutable: copy what the caller passed
}

static long price(Goods g) {
    return switch (g) {                               // no default: a new node type breaks the build
        case Item i -> i.cents();
        case Box b -> b.contents().stream().mapToLong(x -> price(x)).sum();
    };
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """sealed interface Goods {
    data class Item(val name: String, val cents: Long) : Goods
    class Box(contents: List<Goods>) : Goods {
        val contents: List<Goods> = contents.toList()   // immutable: copy what the caller passed
    }
}

fun price(g: Goods): Long = when (g) {                 // no else: a new node type breaks the build
    is Goods.Item -> g.cents
    is Goods.Box -> g.contents.sumOf { price(it) }
}"""}}
 },
 "recap": [
  "Composite: single items and groups share one interface, and a group answers by asking what it holds. A sealed type plus an exhaustive `switch` or `when` replaces the `Component` class from *Design Patterns*.",
  "Leave out `default` and `else`, and a new node type becomes a compile error at every operation that handles the tree.",
  "Keep trees immutable with `List.copyOf` in a compact constructor (Java) or `toList()` (Kotlin), so one box can be shared by many orders and threads.",
  "Bridge splits two things that vary on their own, such as the notice and its channel, so they cost N + M classes instead of N x M. You design it up front; an adapter is written afterwards.",
  "Flyweight shares unchanging instances: the `Integer` cache for -128 to 127, interned strings, `Currency`, enums. Build your own with a private constructor and `computeIfAbsent`, and never compare boxed numbers with `==` in Java.",
  "The limit: all three rely on shared pieces that never change. One mutable field in a shared box or flyweight turns every user into a writer, and a pool fed by outside input grows without end."
 ],
 "closing": "We started with a box of boxes, a sign painter's stencil and a remote that works with any TV. In the shop's code, the box became a sealed tree priced by one switch, the remote became notices that hold a channel, and the stencil became one shared `Product` per catalog code.\n\nNow look in your own code for `==` between two `Integer` or `Long` values in Java. Each one works until the numbers pass 127.\n\nNext, we'll look at choices. When the shop must pick a courier, or a recipe has one step that changes, how do we swap that one decision without touching the rest?",
 "quiz": [
  {"q": "In Java, two weights are read from two maps: `Long onShelf = stockGrams.get(\"coffee\"); Long ordered = orderGrams.get(\"coffee\");`. Each holds 2,500, boxed separately. What does `onShelf == ordered` return on a standard JVM?",
   "options": ["true, because the values are equal", "false, because they are two different `Long` objects", "It doesn't compile", "It throws `NullPointerException`"],
   "answer": 1,
   "why": "`==` on objects compares which object, not which value. `Long.valueOf` shares instances only for -128 to 127, so two separately boxed 2,500s are different objects. With a test value of 100 the cache makes it pass, which is how this bug reaches real stock. Use `equals`, or primitive `long`."},
  {"q": "What does `Box(Item(\"card\", 100), Deal(PercentOff(Item(\"cake\", 1_200), 25), 850)).price()` return, in cents?",
   "options": ["1,300", "1,000", "950", "850"],
   "answer": 2,
   "why": "25% off 1,200 is 900. The deal caps that at 850, and the box adds the card's 100: 950. The tempting 1,000 takes the percentage off and forgets the deal's maximum."},
  {"q": "You're designing the shop's notices: four kinds today, three channels (SMS, email, postcard), and both lists will grow. Which structure fits?",
   "options": ["Notices that hold a `Channel` interface, with one class or lambda per channel", "Twelve classes, one per notice and channel pair", "An adapter per notice kind", "A singleton per channel that every notice extends"],
   "answer": 0,
   "why": "Two things that vary on their own are the case for Bridge: 4 + 3 pieces, and a new channel works with every notice. Twelve classes become fifteen with the next notice. An adapter fixes one mismatched interface, and extending a singleton puts the channel back into the class hierarchy."},
  {"q": "To save memory, the shop's program puts every customer name typed into an order form into a static `ConcurrentHashMap` pool and reuses the pooled string. What goes wrong over time?",
   "options": ["Two threads can get different instances for the same name", "Nothing: `ConcurrentHashMap` is thread-safe", "The pool grows with every new name and never shrinks: a slow memory leak", "Pooled strings can't be compared with `equals` any more"],
   "answer": 2,
   "why": "A flyweight pool must be bounded. Names typed by customers are an open set, so the map keeps every name ever seen for as long as the program runs. Pool a known set, such as the catalog's product codes, or use a cache that forgets old entries. Thread safety isn't the issue here; `computeIfAbsent` handles that."},
  {"q": "From *Don't share: immutability, confinement, ThreadLocal*: the breakfast box tree is built once at startup from records whose lists go through `List.copyOf`, kept in a `static final` field, and read by 200 threads. What do the reads need?",
   "options": ["A `synchronized` block around each `price` call", "The read side of a `ReadWriteLock`", "`volatile` on every record field", "Nothing: the tree is immutable and safely published"],
   "answer": 3,
   "why": "Record fields are final, `List.copyOf` returns a list nobody can modify, and a `static final` field is published safely when the class is set up. Nothing ever writes after that, so there is nothing to race on, and locks would only make threads wait.",
   "from": "conc-11"}
 ],
 "flashcards": [
  {"front": "What does Composite let you do?", "back": "Treat a single item and a group of items through one interface. A group answers by asking what it holds, so callers never check which one they have."},
  {"front": "Why leave `default` out of the switch that walks a sealed composite?", "back": "So adding a node type is a compile error at every operation that handles the tree, instead of a silent fallback."},
  {"front": "What problem does Bridge solve?", "back": "Two things that vary on their own (notice and channel) without N x M classes: the abstraction holds an implementor and calls it."},
  {"front": "Bridge or Adapter: which one is designed up front?", "back": "Bridge. An adapter is written afterwards, to make a class you can't change fit your interface."},
  {"front": "Java: `Integer a = 128, b = 128;` What is `a == b`?", "back": "false with default settings. `Integer.valueOf` caches only -128 to 127; 128 gives two different objects."},
  {"front": "Why must a flyweight be immutable?", "back": "Every holder shares the same instance, so a change made by one would show up for all of them, on every thread."},
  {"front": "Why does a flyweight factory use `computeIfAbsent` instead of `get` then `put`?", "back": "`computeIfAbsent` checks and inserts in one atomic step, so callers at the same moment get one instance. `get` then `put` is check-then-act and can build duplicates."}
 ],
 "terms": [
  {"term": "Composite", "plain": "A tree where groups and single items share one interface, so you handle both the same way."},
  {"term": "Leaf", "plain": "A node in a composite with nothing inside it, such as `Item(\"jam\", 300)`."},
  {"term": "Bridge", "plain": "Splitting two things that vary on their own, so one side holds the other through an interface."},
  {"term": "Implementor", "plain": "In a bridge, the side that does the low-level work, such as a `Channel` that carries messages."},
  {"term": "Flyweight", "plain": "A small object that never changes, shared by many users instead of copied for each."},
  {"term": "Intrinsic and extrinsic state", "plain": "Intrinsic state lives in the shared object; extrinsic state belongs to each use and stays outside it."},
  {"term": "Canonicalizing factory", "plain": "A factory that returns the one pooled instance for a key, such as `Currency.getInstance(\"EUR\")`."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why the customer's name and address live on the order, not inside the shared breakfast box, and why that lets hundreds of orders and many threads share one box object safely.",
  "answer": "The box tree holds only what is the same for every order: the items and their prices. That is its intrinsic state. Who ordered it and where it goes change with every order, so they are extrinsic state, and the order keeps them. Because the box never stores anything about one order, one box object can serve every order of the breakfast box. It is also immutable: record fields are final and the contents are copied with `List.copyOf`. Once it's published safely, for example in a `static final` field built at startup, any number of threads can read it at the same time with no locks, because nothing ever writes to it. If the box kept \"the current customer\" in a field, two orders would overwrite each other's name, and we'd need one box per order or a lock on every read."
 },
 "deeper": {
  "minutes": 10,
  "body": """*Design Patterns* spends pages on Composite's "transparency versus safety" choice: should `add` and `remove` live on the shared `Component` type, so leaves must throw, or only on groups, so callers must cast? A sealed type with immutable records ends the debate. There are no methods for managing children at all: you build a new tree. Pattern matching gives each operation exact access to each node type, with no casts.

Recursion over a tree is fine for a box a few levels deep. A tree built from outside input, such as a gift-box design a customer uploads, could be thousands of levels deep and throw `StackOverflowError`. Check the depth when you build the tree, or walk it with your own stack. Composite also pairs with Visitor; lesson 10 of this track, *Visitor, Iterator, Mediator and Memento*, shows why sealed types and pattern matching usually replace it.

The `Integer` cache bounds are part of the contract: `valueOf` "will always cache values in the range -128 to 127, inclusive, and may cache other values outside of this range". The upper bound can be raised with the `java.lang.Integer.IntegerCache.high` system property. That can make a boxed `==` bug disappear on one JVM and show up on another, which is one more reason never to rely on it.

String interning has a cousin in the garbage collector, the part of the JVM that frees memory nobody uses. G1's `-XX:+UseStringDeduplication` lets the collector make equal `String` objects share one array of characters underneath, with no code change. It saves memory for programs that hold many equal strings, such as product codes and unit names, but doesn't make `==` work, because the `String` objects themselves stay distinct."""
 },
 "sources": [
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "Integer.java at jdk-25-ga (valueOf and IntegerCache)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java"},
  {"title": "Currency.java at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Currency.java"},
  {"title": "JLS 5.1.7: Boxing conversion", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-5.html#jls-5.1.7"},
  {"title": "JLS 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10"}
 ]
}

out = ROOT / "content/lessons/pat-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
