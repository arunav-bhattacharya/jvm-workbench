import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l04.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l04/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l04/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="t-s t-code" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


FIG = (
    '<svg viewBox="0 0 690 270" role="img" aria-label="CardPayment is a subtype of Payment. Because Source is declared out, Source of CardPayment is a subtype of Source of Payment: the arrow keeps its direction. '
    'On the right, a producer: values of T only come out of it, through next.">'
    '<text class="t-s t-m" x="110" y="18" text-anchor="middle">element types</text>'
    '<text class="t-s t-m" x="330" y="18" text-anchor="middle">Source&lt;out T&gt;</text>'
    '<text class="t-s t-m" x="570" y="18" text-anchor="middle">a producer</text>'
    + box(30, 32, 160, "Payment")
    + box(30, 190, 160, "CardPayment", "box-a")
    + '<line class="ln-a" x1="110" y1="190" x2="110" y2="72" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="118" y="136">is a</text>'
    + box(235, 32, 190, "Source&lt;Payment&gt;")
    + box(235, 190, 190, "Source&lt;CardPayment&gt;", "box-a")
    + '<line class="ln-a" x1="330" y1="190" x2="330" y2="72" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="338" y="128">same direction</text>'
    '<text class="t-s t-a" x="338" y="144">(covariant)</text>'
    '<rect class="box-b" x="470" y="100" width="120" height="44" rx="8"/>'
    '<text class="t t-code" x="530" y="127" text-anchor="middle">Source&lt;T&gt;</text>'
    '<line class="ln-a" x1="590" y1="122" x2="680" y2="122" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="635" y="112" text-anchor="middle">next(): T</text>'
    '<line class="ln-bad" x1="430" y1="200" x2="490" y2="150"/>'
    '<text class="t-s t-bad" x="560" y="190" text-anchor="middle">no member takes a T in</text>'
    '<text class="t-s t-m" x="345" y="258" text-anchor="middle">Every CardPayment that comes out is a Payment, so the substitution can never lie.</text>'
    '</svg>'
)

S1 = """A **producer** is a type whose values of `T` only ever come out of it. A feed of payments, a page of search results, an iterator, a `Supplier`. You call it, and it hands you a `T`. Nothing about it takes a `T` in.

Run the substitution test from lesson 3 of this track on a producer. Suppose some code expects a source of `Payment`, and you hand it a source of `CardPayment`. Every call it can make returns a `CardPayment`, and every `CardPayment` is a `Payment`. Nothing can go wrong. So it is safe to treat a `Source<CardPayment>` as a `Source<Payment>`.

The compiler can't see that by itself. Generic types are invariant unless you say otherwise. In Kotlin you say otherwise on the declaration, once, with **`out`**. Java has no such keyword, so it says it at every use with `? extends`:

```java
interface Source<T> {
    T next();                                       // null when empty
}

static long totalCents(Source<? extends Payment> source) { ... }

Source<Card> cards = listSource(List.of(card1, card2));
totalCents(cards);                                  // fine: the parameter says ? extends
Source<Payment> plain = cards;                      // error: Source<Card> cannot be converted to Source<Payment>
```

```kotlin
interface Source<out T> {
    fun next(): T?                                  // null when empty
}

fun totalCents(source: Source<Payment>): Long { ... }

val cards: Source<CardPayment> = ListSource(listOf(card1, card2))
totalCents(cards)                                   // fine: Source is declared out
val plain: Source<Payment> = cards                  // also fine
```

Remove the `out` and Kotlin behaves like Java's plain `Source<T>`:

```text
error: argument type mismatch: actual type is 'Source<CardPayment>', but 'Source<Payment>' was expected.
```

This property is called **covariance**: the subtype arrow between the element types carries over, in the same direction, to the generic type. `CardPayment` is a subtype of `Payment`, so `Source<CardPayment>` is a subtype of `Source<Payment>`. The figure shows the two arrows side by side.

Where you put `out` matters. Kotlin's `out` on the declaration is called **declaration-site variance**. You think about it once, when you write `Source`, and every user gets the flexible behaviour for free. Java's `? extends` is **use-site variance**: every method that takes a source must remember to write it, and the ones that forget are stricter than they need to be. Lesson 6 of this track shows that Kotlin has the use-site form too, for types that can't be `out` everywhere."""

S2 = """A `Source<out T>` can't also have a `fun push(item: T)`, and the substitution test shows why. `out` lets you pass `cards`, a `Source<CardPayment>`, where a `Source<Payment>` is expected. Through that view, `push(BankTransfer(...))` type-checks, because a bank transfer is a `Payment`. Now a source that hands out card payments holds a bank transfer, and the next `next()` gives it to code that reads it as a `CardPayment`: a `ClassCastException`, far from the `push`. The compiler can't allow both the upcast and the parameter. With `out`, it keeps the upcast and rejects the parameter.

`out` is a promise: "values of `T` only come out of this type". The compiler holds you to it by checking where `T` appears in each public member. Every place has a **position**:

- A return type is an **out-position**. The value flows out to the caller.
- A parameter type is an **in-position**. The value flows in from the caller.
- A `var` property is both at once, because it has a getter and a setter. That is an **invariant position**.

In a class declared `out T`, `T` may appear only in out-positions. Try to break it, and the error names the position:

```java
// Java has no `out` on the declaration, so it checks the same rule where you USE the type:
interface Producer<T> {
    T produce();
    void consume(T item);
}

Producer<? extends Object> view = strings;
Object out = view.produce();     // fine: T comes out
view.consume("USD");             // error: String cannot be converted to CAP#1
```

```kotlin
interface Producer<out T> {
    fun produce(): T             // fine
    val latest: T                // fine: a val only has a getter
    fun consume(item: T)         // error: ... declared as 'out' but occurs in 'in' position
    var current: T               // error: ... declared as 'out' but occurs in 'invariant' position
}
```

The full Kotlin message reads `type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of interface Producer<out T>)'.` Java's `CAP#1` is javac's name for "the unknown subtype behind `? extends`". Java can't promise any `String` fits it, so it refuses the call.

Three special cases come up all the time in Kotlin.

**Constructor parameters are fine**, as long as they are plain parameters or `val` properties. `class Holder<out T>(val item: T, plain: T)` compiles. Building the object puts a `T` in, but only once, when the real type is still known. A `var` constructor property is a `var`, so `class Mutable<out T>(var item: T)` fails with the invariant-position error.

**Private members are exempt.** `private var hidden: T` and `private fun replace(t: T)` are allowed, because no outside code can call them with the wrong type. `protected` and `internal` members are checked like public ones.

**`private set` is not enough.** `var lastServed: T? = null; private set` still fails, with `occurs in 'invariant' position`. The property is still a `var`. The fix is to split it: a `private var` for the class and a public `val` that reads it. The lab makes you do exactly that."""

S3 = """You have used a covariant type every day: Kotlin's read-only `List`. Its declaration is `public interface List<out E> : Collection<E>`. That `out` is why a `List<CardPayment>` goes into any function that takes a `List<Payment>`, with no ceremony.

```java
static long sumCents(List<? extends Payment> payments) {    // the wildcard is the flexible part
    long sum = 0;
    for (Payment p : payments) sum += p.getCents();
    return sum;
}

static long sumCentsInvariant(List<Payment> payments) { ... }

List<CardPayment> cards = new ArrayList<>(List.of(card1, card2));
sumCents(cards);              // fine
sumCentsInvariant(cards);     // error: List<CardPayment> cannot be converted to List<Payment>
```

```kotlin
fun sumCents(payments: List<Payment>): Long = payments.sumOf { it.cents }

fun sumCentsMutable(payments: MutableList<Payment>): Long = payments.sumOf { it.cents }

val cards: MutableList<CardPayment> = mutableListOf(card1, card2)
sumCents(cards)               // fine: List is out
sumCentsMutable(cards)        // error: actual type is 'MutableList<CardPayment>', but 'MutableList<Payment>' was expected
```

The two snippets line up exactly. Java's `List<? extends Payment>` and Kotlin's `List<Payment>` are the same contract: "a list I will only read from, of `Payment` or any subtype". Java's plain `List<Payment>` and Kotlin's `MutableList<Payment>` are the strict, invariant version.

Kotlin keeps this promise when Java code calls it. When a parameter's type is declared `out`, Kotlin writes a `? extends` into the Java signature. `javap`, the JDK tool that prints what a class file contains, shows it (package names shortened):

```text
public static final long sumCents(java.util.List<? extends Payment>);
public static final long sumCentsMutable(java.util.List<Payment>);
```

So Java callers can pass a `List<CardPayment>` to `sumCents` too. Kotlin skips the wildcard in two places: in return types, so Java callers don't have to handle wildcards, and when the type argument is a final class like `String`, where `? extends String` would mean nothing. The lab's tests use this rule to check your `out`: they read the Java signature of your function and look for `? extends`."""

S4 = """The most common wrong idea about covariance is that `out` means read-only, or immutable. It doesn't. `out` only limits which **types** can flow in. State can still change. This compiles and empties the shelf:

```java
List<CardPayment> cards = new ArrayList<>(List.of(card1, card2));
List<? extends Payment> view = cards;      // "read-only" for the type only

Payment taken = view.remove(0);            // fine: remove hands a value out
view.clear();                              // fine: no T involved
view.add(card3);                           // error: CardPayment cannot be converted to CAP#1
```

```kotlin
class Shelf<out T>(private val items: MutableList<T>) {
    fun take(): T = items.removeAt(0)      // changes state, only hands T out
    fun clear() = items.clear()            // changes state, no T at all
}

val view: MutableList<out Payment> = mutableListOf(card1, card2)
view.removeAt(0)                           // fine
view.clear()                               // fine
view.add(card3)                            // error: contains out projection which prohibits the use of 'fun add(element: E)'
```

`Shelf` holds a private `MutableList<T>`, which is allowed because private members are exempt. `take()` removes an item and still only hands a `T` out. `clear()` mentions no `T` at all. Both are legal in an `out` class. The Kotlin docs say it plainly: the only thing variance guarantees is type safety, and immutability is a different story.

So when you need a class to be covariant but it also seems to need a method that takes a `T`, you have three honest options:

1. Move the method out of the class as an **extension function**. `fun <T> Feed<T>.nextOr(fallback: T): T` declares its own `T`, so the class's variance rules don't apply. The standard library does this: `plus(element: T)` and `getOrElse` on `List` are extensions.
2. Give the method its own type parameter, such as `fun <R> map(f: (T) -> R): Page<R>`. Here `T` sits inside the parameter of a function parameter, and two in-positions cancel out. Lesson 5 of this track shows why.
3. Split the type in two: a covariant read interface and an invariant read-write one, like `List` and `MutableList`.

There is also `@UnsafeVariance`, which switches the check off for one position. `List.contains(element: @UnsafeVariance E)` uses it, because `contains` only compares. It is a promise you make by hand, and lesson 10 of this track shows how to break it."""

L = {
    "id": "gen-04",
    "title": "Covariance with out: producers",
    "minutes": 35,
    "goal": "By the end you can decide when a generic type is a producer, declare it `out` in Kotlin (or write `? extends` in Java), predict which members the compiler will reject, and fix them without breaking callers.",
    "warmup": {
        "q": "`interface Source<T> { fun next(): T }` and `fun total(s: Source<Payment>)`. You have a `Source<CardPayment>`. What do you need for `total(cards)` to compile?",
        "options": [
            "Nothing: CardPayment is a Payment, so it already compiles",
            "Declare `interface Source<out T>`, because Source only hands T out",
            "Declare `interface Source<in T>`",
            "Cast: `total(cards as Source<Payment>)` is the normal way"
        ],
        "answer": 1,
        "why": "Generic types are invariant unless you say otherwise, so the call does not compile yet. `Source` only produces `T`, so a source of card payments can safely act as a source of payments. `out` tells the compiler that. `in` is for the opposite case, consumers, which lesson 5 of this track covers."
    },
    "sections": [
        {
            "h": "A producer only hands values out",
            "body": S1,
            "figure": {"svg": FIG, "caption": "Covariance keeps the arrow: a Source of CardPayment is a Source of Payment, because a producer only hands values out."},
            "try": {
                "title": "Take out away and watch the call break",
                "minutes": 4,
                "steps": [
                    "Run `ProducerDemo` (or `ProducerDemoJava`) with the command below. Both print the same totals.",
                    "In `ProducerDemo.kt`, remove `out` from both `interface Source<out T>` and `class ListSource<out T>`. Predict which line fails, then run.",
                    "Put `out` back. In the Java twin, uncomment the wrong move. Why does Java need `? extends` on `totalCents` while Kotlin needs nothing there?"
                ],
                "code": kdemo("ProducerDemo", "ProducerDemoJava"),
                "expect": "Both versions print `card total: 1550` and `first of anything: EUR`. Without `out`, Kotlin fails on `totalCents(cards)` with `Argument type mismatch: actual type is 'Source<CardPayment>', but 'Source<Payment>' was expected.` The Java wrong move fails with `incompatible types: Source<Card> cannot be converted to Source<Payment>`. Java's `Source<T>` is invariant, so each method that wants flexibility writes `? extends`. Kotlin wrote `out` once on the interface."
            }
        },
        {
            "h": "Every member has a position: in, out or invariant",
            "body": S2,
            "try": {
                "title": "Find the positions the compiler rejects",
                "minutes": 5,
                "steps": [
                    "Open `PositionsDemo.kt`. For the four numbered lines, predict the position the error will name: in or invariant.",
                    "Uncomment each line on its own and run. Comment it out again before the next.",
                    "Run `PositionsDemoJava` and uncomment its `view.consume` line. Where does Java report the same rule?"
                ],
                "code": kdemo("PositionsDemo", "PositionsDemoJava"),
                "expect": "1 (`fun consume(item: T)`) and 3 (`protected fun keep`) fail with `occurs in 'in' position`. 2 (`var current`) and 4 (`class Mutable<out T>(var item: T)`) fail with `occurs in 'invariant' position`. The demo itself prints `Holder<String> used as Holder<Any>: EUR`. Java reports the rule at the call: `String cannot be converted to CAP#1`, because Java checks variance where you use a type, not where you declare it."
            }
        },
        {
            "h": "List<out E> is Kotlin's answer to ? extends",
            "body": S3,
            "try": {
                "title": "Call a Kotlin function from Java",
                "minutes": 4,
                "steps": [
                    "Run `ListOutDemo`, then `ListOutDemoJava`. The Java one calls the Kotlin function `sumCents` with a `List<CardPayment>`.",
                    "In each file, uncomment the wrong move(s) one at a time and run.",
                    "From `labs/`, run the `javap` command: `javap -p -cp generics/build/classes/kotlin/demo workbench.generics.l04.demo.ListOutDemoKt`. Which parameter got a wildcard?"
                ],
                "code": kdemo("ListOutDemo", "ListOutDemoJava"),
                "expect": "Both print `1550`, and Java prints `Kotlin's sumCents(cards) from Java = 1550`. The wrong moves fail with `actual type is 'MutableList<CardPayment>', but 'MutableList<Payment>' was expected` in Kotlin and `List<CardPayment> cannot be converted to List<Payment>` in Java, for both `sumCentsInvariant` and Kotlin's `sumCentsMutable`. `javap` shows `sumCents(java.util.List<? extends ...Payment>)` and `sumCentsMutable(java.util.List<...Payment>)`: Kotlin's `out` became Java's `? extends`."
            },
            "refs": [
                {"title": "Variant generics in Java signatures (Calling Kotlin from Java)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"}
            ]
        },
        {
            "h": "out does not mean immutable",
            "body": S4,
            "try": {
                "title": "Empty a covariant shelf",
                "minutes": 3,
                "steps": [
                    "Run `ImmutableMythDemo` (or `ImmutableMythDemoJava`). Before it runs, predict whether `take()` and `clear()` compile in a class declared `out T`.",
                    "Uncomment the `view.add` line and run. Read which rule stops it."
                ],
                "code": kdemo("ImmutableMythDemo", "ImmutableMythDemoJava"),
                "expect": "It prints `took pay_1, 1 left`, `after clear: 0 left` and, in Kotlin, `view after removeAt: 0 left`. Variance never stopped the state from changing. The `add` fails with `Receiver type 'MutableList<out Payment>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.` in Kotlin and `CardPayment cannot be converted to CAP#1` in Java: only the in-position is blocked."
            },
            "refs": [
                {"title": "Declaration-site variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html#declaration-site-variance", "kind": "docs"}
            ]
        }
    ],
    "analogy": "A covariant type is a vending machine. A machine that dispenses only cola can stand in for \"a drinks machine\": everyone who asks it for a drink gets a drink. What you must not do is let customers load their own cans into it. If the cola machine took returns, someone could load lemonade into it through the \"drinks machine\" label, and the next person who wanted cola would get lemonade. `out` is the rule that the machine has no loading slot for customers. The analogy breaks at one point: a real vending machine can still be emptied, restocked by staff or switched off. `out` says nothing about any of that. It only controls which type of can goes in through the public slot.",
    "in_your_world": "Most read-side types in a payment service are producers: a page of results from the ledger API, a `Feed` of settlement records, a query result, a read-only snapshot of balances. Declare them `out` (or keep them as Kotlin `List`s) and a `Page<CardPayment>` drops straight into reporting code that expects a `Page<Payment>`. In a Quarkus REST client written in Java you will see the same contract as `List<? extends PaymentDto>` in parameters. When you write a Kotlin library that Java services call, Kotlin adds those wildcards to parameters for you, so Java callers get the same flexibility.",
    "mistake": "The common mistake is to read `out` as \"immutable\" and then trust a covariant type to protect shared state. A `MutableList<out Payment>` still has `clear()` and `removeAt()`, and a `class Shelf<out T>` can wrap a private mutable list. People make this mistake because the C# and Kotlin keywords sound like access rules. They are type rules. The fix is to keep two questions apart: \"can a subtype stand in for the supertype here?\" (variance) and \"can anyone change this?\" (expose a read-only interface, or copy). The other mistake is the reverse: giving up on `out` because one method takes a `T`. Move that method to an extension function, or split the type into a read interface and a write interface.",
    "compare": {
        "title": "A producer, declared once in Kotlin, spelled at each use in Java",
        "java": {
            "title": "Feeds.java",
            "src": "import java.util.List;\n\ninterface Payment { long cents(); }\nrecord CardPayment(long cents) implements Payment {}\n\n// Java can't say \"T only comes out\" on the declaration\ninterface Source<T> {\n    T next();\n}\n\nclass Feeds {\n    // every method that should accept subtypes must remember ? extends\n    static long total(Source<? extends Payment> source, int n) {\n        long sum = 0;\n        for (int i = 0; i < n; i++) sum += source.next().cents();\n        return sum;\n    }\n\n    static long sum(List<? extends Payment> payments) {\n        return payments.stream().mapToLong(Payment::cents).sum();\n    }\n\n    // forget it once and the method is stricter than it needs to be\n    static long strict(Source<Payment> source) { return source.next().cents(); }\n}"
        },
        "kotlin": {
            "title": "Feeds.kt",
            "src": "interface Payment { val cents: Long }\ndata class CardPayment(override val cents: Long) : Payment\n\n// say it once, on the declaration\ninterface Source<out T> {\n    fun next(): T\n}\n\n// plain types in every signature: Source and List are both covariant\nfun total(source: Source<Payment>, n: Int): Long {\n    var sum = 0L\n    repeat(n) { sum += source.next().cents }\n    return sum\n}\n\nfun sum(payments: List<Payment>): Long = payments.sumOf { it.cents }\n\n// the compiler enforces the promise inside Source:\n// fun push(t: T) would fail with \"declared as 'out' but occurs in 'in' position\""
        },
        "note": "The safety rule is the same in both languages: through a covariant view you may take values out but not put them in. The difference is who carries the burden. In Java the type stays invariant and every method signature has to say `? extends`, so the flexibility depends on each author remembering. In Kotlin the author of `Source` says `out` once, the compiler checks every member of `Source` against it, and every signature that mentions `Source<Payment>` is automatically flexible. When Java calls that Kotlin code, Kotlin writes the `? extends` into the parameter types for it."
    },
    "worked": {
        "title": "Make a settlement Feed covariant without losing a feature",
        "steps": [
            {"say": "A settlement job reads payments from a `Feed`. Reporting code wants a `Feed<Payment>`, but the job has a `Feed<CardPayment>`. The feed only hands items out, so it should be covariant. Here it is before the change.", "code": "class Feed<T>(items: List<T>) {\n    private val queue = ArrayDeque(items)\n    var lastServed: T? = null\n        private set\n\n    fun next(): T { val item = queue.removeFirst(); lastServed = item; return item }\n    fun nextOr(fallback: T): T = if (queue.isEmpty()) fallback else next()\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Feed<T> {\n    private final ArrayDeque<T> queue;\n    private T lastServed;\n\n    Feed(List<T> items) { queue = new ArrayDeque<>(items); }\n\n    T next() { T item = queue.removeFirst(); lastServed = item; return item; }\n    T nextOr(T fallback) { return queue.isEmpty() ? fallback : next(); }\n    T lastServed() { return lastServed; }\n}"},
            {"say": "1. Add `out` and read the errors. The compiler names two members. `nextOr` takes a `T` (in-position). `lastServed` is a `var`, so its type is in an invariant position, even with a private setter. In Java there is nothing to add to the class; each caller writes `Feed<? extends Payment>` instead.", "code": "class Feed<out T>(items: List<T>) {\n    // error: ... declared as 'out' but occurs in 'invariant' position in type 'T?'\n    var lastServed: T? = null\n        private set\n    // error: ... declared as 'out' but occurs in 'in' position in type 'T'\n    fun nextOr(fallback: T): T = ...\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "// Java checks at the use site instead:\nstatic List<Payment> drainAll(Feed<? extends Payment> feed) { ... }\n\nFeed<? extends Payment> view = cardFeed;\nPayment p = view.next();                 // fine\nview.nextOr(new BankTransfer(...));      // error: cannot be converted to CAP#1"},
            {"say": "2. Fix the property by splitting it: a private `var` (exempt) and a public `val` (an out-position). Callers still read `lastServed`, and nobody outside could set it before either.", "code": "private var last: T? = null\nval lastServed: T? get() = last", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "private T last;\nT lastServed() { return last; }   // Java: a getter with no setter"},
            {"say": "3. Fix `nextOr` by moving it out of the class as an extension. The extension declares its own `T`, so the class's `out` doesn't constrain it. Self-check: why is this safe? (At the call `feed.nextOr(x)`, the compiler picks a `T` that fits both the feed and `x`. For a `Feed<CardPayment>` and a `BankTransfer` fallback, that `T` is `Payment`, and the result is typed `Payment`.)", "code": "fun <T> Feed<T>.nextOr(fallback: T): T = if (hasNext()) next() else fallback\n\nval cardFeed: Feed<CardPayment> = Feed(cards)\nval p: Payment = cardFeed.nextOr(BankTransfer(\"pay_9\", 0, \"DE89...\"))   // T = Payment", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "// Java: a static helper with its own <T> does the same job\nstatic <T> T nextOr(Feed<? extends T> feed, T fallback) {\n    return feed.hasNext() ? feed.next() : fallback;\n}\n\nPayment p = nextOr(cardFeed, new BankTransfer(\"pay_9\", 0, \"DE89...\"));"}
        ]
    },
    "lab": {
        "title": "Make Feed and Page covariant",
        "minutes": 13,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l04/Feed.kt",
            f"{LAB}/main/kotlin/workbench/generics/l04/Page.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l04.*'",
        "steps": [
            "Run the tests. Eight of nine fail. Read the two variance failures: `expected \"Feed<? extends Payment>\" but was \"Feed<Payment>\"`. The test reads the Java signature of `drainAll`, which only gets a wildcard when `Feed` is declared `out`.",
            "In `Feed.kt`, add `out` to `Feed`'s type parameter. Run the tests and read the compile error about `lastServed`.",
            "Fix `lastServed` without making it settable from outside: split it into a `private var` and a public `val` with a getter.",
            "Write `hasNext`, `next`, the `nextOr` extension, `drainAll` and `totalCents`.",
            "In `Page.kt`, add `out` to `Page`. Predict whether `map` still compiles before you run. Then write `map` and `firstOnPage`.",
            "Run the tests until all nine pass."
        ],
        "hints": [
            "`private var last: T? = null` plus `val lastServed: T? get() = last` keeps the read for callers and the write for the class.",
            "`ArrayDeque.removeFirst()` throws `NoSuchElementException` on an empty deque, which is what `next()` should do.",
            "`map` compiles under `out`: in `f: (T) -> R`, `T` is the parameter of a parameter, which counts as an out-position. `Page(items.map(f), nextCursor)` is the whole body."
        ],
        "done_when": "All nine tests in `CovarianceTest` pass."
    },
    "drill": {
        "title": "Write a producer from memory",
        "minutes": 4,
        "prompt": "Close this page. Write a covariant `Source` interface with one method `next()`, a `ListSource` class that implements it over a `List`, and a function `totalCents` that accepts a source of card payments as a source of payments. Write it in Kotlin with `out`, then in Java with `? extends`. Then add a `push(t: T)` member to the Kotlin interface and write down the error you expect.",
        "answer": {
            "lang": "kotlin",
            "src": "interface Source<out T> {\n    fun next(): T?\n}\n\nclass ListSource<out T>(items: List<T>) : Source<T> {\n    private val it = items.iterator()\n    override fun next(): T? = if (it.hasNext()) it.next() else null\n}\n\nfun totalCents(source: Source<Payment>): Long {\n    var sum = 0L\n    while (true) sum += (source.next() ?: break).cents\n    return sum\n}\n\n// fun push(t: T) inside Source:\n// error: type parameter 'T' is declared as 'out' but occurs in 'in' position",
            "alt": {"lang": "java", "title": "Source.java", "src": "interface Source<T> {\n    T next();   // null when empty\n}\n\nstatic <T> Source<T> listSource(List<T> items) {\n    Iterator<T> it = items.iterator();\n    return () -> it.hasNext() ? it.next() : null;\n}\n\n// the flexibility lives in the parameter, not in Source\nstatic long totalCents(Source<? extends Payment> source) {\n    long sum = 0;\n    for (Payment p = source.next(); p != null; p = source.next()) sum += p.cents();\n    return sum;\n}"}
        }
    },
    "recap": [
        "A producer only hands values of `T` out. A producer of a subtype can safely stand in for a producer of the supertype: that is covariance.",
        "Kotlin declares it once with `out T` (declaration-site). Java writes `? extends T` at every use (use-site).",
        "In an `out` class, `T` may appear in return types and `val`s, not in parameters or `var`s. Constructor `val`s and private members are fine; `private set` is not enough.",
        "Kotlin's read-only `List<out E>` is why `List<CardPayment>` fits a `List<Payment>` parameter. Java needs `List<? extends Payment>` for the same thing.",
        "Kotlin writes `? extends` into Java parameter signatures for `out` types, except for final type arguments and return types.",
        "`out` controls which types flow in, not whether state changes. A covariant type can still be cleared."
    ],
    "quiz": [
        {
            "q": "Which member compiles inside `class Feed<out T>`?",
            "options": [
                "`fun push(item: T)`",
                "`var current: T? = null` with `private set`",
                "`fun peek(): T?`",
                "`protected fun replay(item: T)`"
            ],
            "answer": 2,
            "why": "A return type is an out-position, so `peek(): T?` is fine. `push` takes a `T` (in-position), and so does the protected `replay`: only private members are exempt. A `var` is an invariant position even when its setter is private."
        },
        {
            "q": "Kotlin: `interface Source<out T> { fun next(): T }`, `interface Payment`, and `fun total(s: Source<Payment>)`. What does Java see as the parameter type of `total`?",
            "options": [
                "`Source<Payment>`",
                "`Source<? extends Payment>`",
                "`Source<? super Payment>`",
                "The raw type `Source`"
            ],
            "answer": 1,
            "why": "Kotlin turns a parameter of an `out`-declared type into `? extends`, so Java callers can pass a `Source<CardPayment>` as well. It would skip the wildcard if `Payment` were a final class, and it never adds one to a return type."
        },
        {
            "q": "`class Shelf<out T>(private val items: MutableList<T>) { fun clear() = items.clear() }`. Does it compile, and what does it say about `out`?",
            "options": [
                "No: an `out` class can't hold a `MutableList<T>`",
                "No: `clear()` changes state, and `out` means immutable",
                "Yes: private members are exempt, and `out` restricts types, not state changes",
                "Yes, but only with `@UnsafeVariance` on `items`"
            ],
            "answer": 2,
            "why": "The `MutableList<T>` is private, so the variance check skips it, and `clear()` does not mention `T` at all. `out` guarantees that no wrongly-typed value gets in through the public API. It says nothing about whether the object can change."
        },
        {
            "q": "Java: `static long sum(List<? extends Number> xs)` and `List<Integer> ints`. Which line compiles inside `sum`?",
            "options": [
                "`xs.add(5);`",
                "`Number first = xs.get(0);`",
                "`xs.add(null);` is the only thing that fails",
                "`Integer first = xs.get(0);`"
            ],
            "answer": 1,
            "why": "Through `? extends Number` you can read elements as `Number`. You can't add an `Integer`, because the list might really be a `List<Double>` (javac: `cannot be converted to CAP#1`). Reading as `Integer` fails for the same reason. `add(null)` actually compiles, since null fits any type."
        },
        {
            "q": "From \"Subtyping, and why List<String> is not List<Object>\": why does `val x: MutableList<Any> = mutableListOf<String>()` fail while `val y: List<Any> = mutableListOf<String>()` compiles?",
            "options": [
                "`MutableList` is a different class from `List` at run time",
                "Through `x` you could add an `Int` to a list of strings; `List` has no add, so `y` can only read",
                "Kotlin forbids `Any` as a type argument of mutable types",
                "`mutableListOf` returns a Java type that Kotlin can't widen"
            ],
            "answer": 1,
            "why": "That is the substitution test. A mutable view of the wider type could write a wrong value into the narrower list. A read-only view can't, which is exactly what `List<out E>` declares. At run time both are the same `java.util.List`.",
            "from": "gen-03"
        }
    ],
    "flashcards": [
        {"front": "What makes a generic type safe to declare `out T`?", "back": "It only hands values of `T` out (return types, `val`s). It never takes a `T` in through a public member."},
        {"front": "With `Source<out T>`, is `Source<CardPayment>` a subtype of `Source<Payment>`?", "back": "Yes. Covariance keeps the direction of the subtype arrow."},
        {"front": "Kotlin's `out T` on a declaration corresponds to what in Java?", "back": "`? extends T`, written at each use site, e.g. `List<? extends Payment>`."},
        {"front": "Why does `var x: T` fail in a class declared `out T`?", "back": "A `var` has a setter, so `T` is in an invariant position. Even `private set` doesn't help; split it into a private `var` and a public `val`."},
        {"front": "Are constructor parameters allowed in a class declared `out T`?", "back": "Plain parameters and `val` properties: yes. A `var` constructor property: no (invariant position)."},
        {"front": "Does `out` make a type immutable?", "back": "No. It only blocks `T` from flowing in. `MutableList<out T>` still has `clear()` and `removeAt()`."},
        {"front": "How do you keep a method like `getOrElse(default: T)` on a covariant type?", "back": "Make it an extension function with its own type parameter: `fun <T> Feed<T>.nextOr(fallback: T): T`."}
    ],
    "terms": [
        {"term": "Producer", "plain": "A type whose `T` values only come out: iterators, sources, pages, read-only lists."},
        {"term": "Covariant", "plain": "`C<Sub>` is a subtype of `C<Super>`: the arrow keeps its direction."},
        {"term": "out", "plain": "Kotlin's keyword on a type parameter: \"T only comes out of this type\"."},
        {"term": "Out-position", "plain": "A place where a value of `T` flows out: return types and `val` types."},
        {"term": "In-position", "plain": "A place where a value of `T` flows in: parameter types."},
        {"term": "Declaration-site variance", "plain": "Variance written once on the class (`interface Source<out T>`), as Kotlin does."},
        {"term": "Use-site variance", "plain": "Variance written where the type is used (`Source<? extends Payment>`), as Java does."}
    ],
    "explain_back": {
        "prompt": "In your own words, explain to a teammate why Kotlin lets a `Page<CardPayment>` be passed where a `Page<Payment>` is expected once `Page` is declared `out T`, and what the compiler gives up in return.",
        "answer": "`Page` only hands items out: you read `items` and `map` them, and nothing in its public API takes a `T` in. If I give you a page of card payments where you expected a page of payments, every item you read really is a payment, so nothing can go wrong. `out T` is my promise that this is true, and in return the compiler lets the subtype arrow carry over from `CardPayment` to `Page<CardPayment>`. To keep the promise honest, the compiler rejects any public member where `T` would flow in, like a parameter of type `T` or a `var`. In Java the same idea is written at each use as `Page<? extends Payment>`."
    },
    "deeper": {
        "minutes": 10,
        "body": "The rule \"parameters are in-positions\" has a twist when the parameter is itself a function. In `fun <R> map(f: (T) -> R)`, `T` is the input of `f`. The page calls `f` and passes it a `T`, so the value flows out of the page into the caller's lambda. Two in-positions cancel out. That is why `map` is legal in `Page<out T>`, while `fun replay(): (T) -> Unit` (a function returned to the caller, which the caller will feed a `T`) is not. Lesson 5 of this track turns this into a sign rule.\n\nKotlin is strict about inferred types too. In `class E<in T> { private fun produce(): T? = null; fun use() = produce() }`, the private `produce` is fine, but the public `use()` has the inferred return type `T?` and fails. Give public members of variant classes explicit types.\n\nPrivate members get one more rule, called private-to-this. Inside `class C<out T>(private var t: T)`, the method `fun copyFrom(o: C<@UnsafeVariance T>) { t = o.t }` fails with `cannot access 'var t: T': it is private/*private to this*/`. A private member is only exempt when you reach it through `this`, because another instance `o` might really be a `C<Subtype>` seen as a `C<T>`.\n\nFinally, Kotlin leaves the wildcard out of Java signatures when the type argument is final. `fun f(x: List<String>)` is `f(List<String>)` in Java, because nothing can extend `String`. Use `@JvmWildcard` to force one, or `@JvmSuppressWildcards` to drop them."
    },
    "sources": [
        {"title": "Generics: declaration-site variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Calling Kotlin from Java: variant generics (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
        {"title": "Wildcards (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/wildcards.html"}
    ]
}

out = ROOT / "content/lessons/gen-04.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
