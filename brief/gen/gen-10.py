import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l10.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l10/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l10/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


def arrow(x1, x2, y):
    return f'<line class="ln-a" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'


FIG = ('<svg viewBox="0 0 700 280" role="img" aria-label="Two builder chains. With a self type, GiftBoxBuilder().grams(1_200) returns B, which is GiftBoxBuilder, so ribbon can be called next. '
       'Without one, PlainGiftBoxBuilder().grams(1_200) returns PlainBuilder, and ribbon is an unresolved reference. '
       'The subclass declaration, class GiftBoxBuilder extends Builder of GiftBoxBuilder, writes the subclass\'s own name into the blank B.">'
       '<text class="t-s t-m" x="15" y="20">with a self type</text>'
       + box(15, 30, 190, "GiftBoxBuilder()") + arrow(207, 243, 49)
       + box(245, 30, 210, ".grams(1_200): B", "box-a") + arrow(457, 493, 49)
       + box(495, 30, 190, ".ribbon(\"red\")", "box-ok")
       + '<text class="t-s t-a" x="350" y="88" text-anchor="middle">B = GiftBoxBuilder</text>'
         '<text class="t-s t-m" x="15" y="126">without one</text>'
       + box(15, 136, 190, "PlainGiftBoxBuilder()") + arrow(207, 243, 155)
       + box(245, 136, 210, ".grams(1_200)", "box") + arrow(457, 493, 155)
       + box(495, 136, 190, ".ribbon(\"red\")", "box-bad")
       + '<text class="t-s t-m" x="350" y="194" text-anchor="middle">returns PlainBuilder</text>'
         '<text class="t-s t-bad" x="590" y="194" text-anchor="middle">Unresolved reference</text>'
       + '<rect class="box-dim" x="15" y="214" width="670" height="38" rx="8"/>'
         '<text class="t-s t-code" x="350" y="238" text-anchor="middle">class GiftBoxBuilder : Builder&lt;GiftBoxBuilder&gt;()    // the subclass writes its own name in B</text>'
         '</svg>')

OPENING = """Orders at the fruit shop come on printed forms. Every form starts with the same lines: the variety, the weight, a note. A gift-box form adds a line for the ribbon, and a delivery form adds a line for the address. A helper fills it in one line at a time.

Here is the odd part. The helper fills in the weight on a gift-box form, and what comes back is "an order form". The ribbon line is still printed on the paper, but nobody is allowed to look at it any more.

In code, the form is a builder, and the trap sits in its base class. A shared setter can only promise to return the base class, so a chain of calls loses the subclass halfway along.

KClass, Class and type tokens ended on that question. In this lesson, we'll give the base form a blank that each kind of form fills with its own name, take null out of a type with `T & Any`, see how `List<out E>` can take an `E` in `contains`, and finish with function types, `Nothing` and type aliases. Before we start, make a guess, and keep it in mind."""

S1 = """A **builder** is an object you fill in one setting at a time and then ask to build the finished thing. Each setter returns the builder, so the calls can follow each other on one line, a style called a fluent chain. Put the shared setters in a base class, add a subclass with a setter of its own, and the chain breaks as soon as a base setter runs:

```java
class PlainBuilder {
    protected int grams;
    PlainBuilder grams(int grams) { this.grams = grams; return this; }
}
class PlainGiftBoxBuilder extends PlainBuilder {
    PlainGiftBoxBuilder ribbon(String colour) { ... }
}

new PlainGiftBoxBuilder().grams(1_200).ribbon("red");   // error: cannot find symbol
```

```kotlin
open class PlainBuilder {
    protected var grams = 0
    fun grams(grams: Int): PlainBuilder { this.grams = grams; return this }
}
class PlainGiftBoxBuilder : PlainBuilder() {
    fun ribbon(colour: String): PlainGiftBoxBuilder { ... }
}

PlainGiftBoxBuilder().grams(1_200).ribbon("red")
// error: Unresolved reference 'ribbon' on receiver of type 'PlainBuilder'.
```

`grams` returns a `PlainBuilder`, because that's all the base class knows about itself. The object is still a `PlainGiftBoxBuilder`, and the demo prints that run-time class. But the static type, the one the compiler goes by, has lost it. The form has forgotten what kind of form it is.

The base class needs a way to say "I return whatever subclass I really am". The answer is a **self type**, a type parameter that stands for "my own subclass", written with a **recursive bound**, a bound that mentions the type parameter itself:

```java
abstract class Builder<B extends Builder<B>> {
    protected int grams;
    B grams(int grams) { this.grams = grams; return self(); }
    protected abstract B self();
}
final class GiftBoxBuilder extends Builder<GiftBoxBuilder> {
    GiftBoxBuilder ribbon(String colour) { ...; return this; }
    @Override protected GiftBoxBuilder self() { return this; }
}
```

```kotlin
abstract class Builder<B : Builder<B>> {
    protected var grams = 0
    fun grams(grams: Int): B { this.grams = grams; return self() }
    protected abstract fun self(): B
}
class GiftBoxBuilder : Builder<GiftBoxBuilder>() {
    fun ribbon(colour: String): GiftBoxBuilder { ...; return this }
    override fun self() = this
}
```

Read `B : Builder<B>` as "B is a builder whose own B is B". It's the blank at the top of the base form: "this is a ___ form". The only types that fit are subclasses that write their own name in it, as `GiftBoxBuilder : Builder<GiftBoxBuilder>()` does. Then substitute, as in lesson 1 of this track: for a `GiftBoxBuilder`, every `B` in the base class reads as `GiftBoxBuilder`. So `GiftBoxBuilder().grams(1_200)` has the static type `GiftBoxBuilder`, and `.ribbon("red")` is in reach again. You've met the shape before. Lesson 2's `T : Comparable<T>`, "a T that compares with its own kind", is a recursive bound, and so is Java's own `Enum<E extends Enum<E>>`.

Two details matter. The abstract `self()` keeps the code checked: each subclass returns `this`, and the compiler verifies that it is a `B`. The tempting shortcut, `return this as B` in the base class, is an unchecked cast, and erasure turns it into no check at all. And the bound can't force honesty. `class Liar : Builder<GiftBoxBuilder>()` compiles, because the blank only asks for the name of *some* builder. Here the form picture breaks just as the code does: anyone can write another form's name in the blank. With an abstract `self()`, the liar must hand back a `GiftBoxBuilder` it doesn't have, which is where you notice.

**A recursive bound lets a base class return its subclass. Fill the blank with the subclass's own name.**

In pure Kotlin code you often don't need a builder at all: a data class with default arguments and `copy` covers most cases. Reach for self types when Java callers need a builder, or when you extend a Java class that already uses one. Next, a smaller tool with a big promise: this box is never empty."""

S2 = """A plain `T` may stand for a nullable type, because its default bound is `Any?` (lesson 2). On a label, that's "Box of ___", where the caller may write "apples, or nothing". Sometimes you know that one particular value is not null, and you want its type to say so: whatever the label allows, this box holds a real fruit. Kotlin writes that as `T & Any`, a **definitely non-nullable type**: "`T`, with null taken out".

```java
// Java's types say nothing about null. The best you can do is a comment and a check at run time.
static <T> T firstNotNullValue(List<T> items) {
    for (T item : items) if (item != null) return item;
    throw new NoSuchElementException("no non-null element");
}

String first = firstNotNullValue(Arrays.asList(null, "Gala", "Fuji"));
```

```kotlin
fun <T> List<T>.firstNotNullValue(): T & Any {
    for (item in this) if (item != null) return item     // smart cast: item is T & Any here
    throw NoSuchElementException("no non-null element")
}

val first: String = listOf(null, "Gala", "Fuji").firstNotNullValue()   // T = String?, result String
```

With `T = String?`, `T & Any` is `String`. With `T = Apple`, it's just `Apple`. Inside the loop, the check `item != null` is what makes `item` fit: a smart cast, Kotlin's narrowing of a value's type after a check, turns `T` into `T & Any`. The compiler holds you to the promise. Return a plain `T`, and it says `Return type mismatch: expected 'T (of fun <T> forget) & Any', actual 'T (of fun <T> forget)'.`

The Kotlin docs name the main use: overriding Java methods whose generic parameters are annotated `@NotNull`, a marker that tells tools a value is never null. Kotlin reads `@NotNull T` in a Java interface as `T & Any`:

```java
public interface NotNullTransformer<T> {
    @NotNull T transform(@NotNull T value);
}
```

```kotlin
class UpperCaser<T : CharSequence?> : NotNullTransformer<T> {
    override fun transform(value: T & Any): T & Any = ...
}
```

Two rules come with it. The left side must be a type parameter with a nullable bound. With `T : Any` there is no null to take out, and the compiler says `Intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.` And the promise is Kotlin's alone: Java sees `<T> T firstNotNullValue(List<T>)`, with no trace of `& Any`.

The docs add that when you work only with Kotlin, you'll rarely need to write it, because inference handles it. Expect to type `T & Any` at the Java boundary and in small helpers like this one, which turns an optional field into a value the rest of the code can use without `!!`:

```java
// Java: the null check happens, but the type can't record it
static <T> T requireValue(T value, String name) {
    if (value == null) throw new IllegalArgumentException(name + " is required");
    return value;
}
```

```kotlin
fun <T> T.requireValue(name: String): T & Any = this ?: throw IllegalArgumentException("$name is required")

val ribbon: String = order.ribbon.requireValue("ribbon")   // order.ribbon is a String?
```

**`T & Any` is `T` with null taken out. Use it where a nullable `T` is known to hold a value.**

That was a type with one door closed. Next, a type with one door opened on purpose."""

S3 = """Here's a puzzle left over from lesson 4. `List` is declared `interface List<out E>`: it's the glass display case of lesson 3, where things come out and nothing goes in. An `out` type parameter can't appear as a parameter. Yet you call `list.contains(x)` every day, and hand it an `E`. The standard library's source (2.4.21) shows how:

```text
public operator fun contains(element: @UnsafeVariance E): Boolean
public fun indexOf(element: @UnsafeVariance E): Int
```

`@UnsafeVariance` "suppresses errors about variance conflict" for one use of the type. Think of it as a note the author tapes to the glass: "this opening is only for pointing". `contains` compares the element with what's inside and never keeps it. So a `List<Int>` seen as a `List<Number>` can't be damaged by it, and `contains(2.5)` just returns `false`. The clerk reads the note, nods, and stops checking that one spot.

Why take an `E` at all, when `Any?` would need no annotation? Because the `E` lets the compiler catch a question that makes no sense. Java chose `Object`, and pays for it:

```java
Set<Long> crateIds = Set.of(42L);
crateIds.contains(42);                        // false: 42 is boxed to an Integer, and Integer(42) != Long(42)
List.of(180, 150).contains("180");            // compiles, always false
```

```kotlin
val crateIds: Set<Long> = setOf(42L)
crateIds.contains(42)                         // true: the literal 42 is typed as a Long here
listOf(180, 150).contains("180")
// error: Type inference failed. The value of the type parameter 'T' must be mentioned in input types ...
```

That first Java line is a real kind of bug: an `int` id looked up in a set of `Long`s, false every time, with no warning.

The annotation is called unsafe for a reason. It switches the check off, and the compiler believes you. Here is a display case with a secret slot cut into the glass:

```java
// Java's way to break a ? extends view on purpose is an unchecked cast:
List<Apple> apples = new ArrayList<>(List.of(new Apple("Gala", 180)));
List<? extends Fruit> view = apples;
((List<Fruit>) view).add(new Lemon("Eureka", 120));
Apple last = apples.get(apples.size() - 1);     // ClassCastException
```

```kotlin
class DisplayCase<out T>(first: T) {
    private val items = mutableListOf(first)
    fun add(item: @UnsafeVariance T) { items.add(item) }   // keeps it: a broken promise
    fun last(): T = items.last()
}

val apples: DisplayCase<Apple> = DisplayCase(Apple("Gala", 180))
val anyFruit: DisplayCase<Fruit> = apples       // fine: DisplayCase is out T
anyFruit.add(Lemon("Eureka", 120))              // compiles
val last: Apple = apples.last()                 // ClassCastException
```

It's lesson 3's lemon in the crate of apples, back through a hole we cut ourselves. The demo prints `ClassCastException: class workbench.generics.l10.demo.Lemon cannot be cast to class workbench.generics.l10.demo.Apple`.

Use `@UnsafeVariance` only on parameters that are read and compared, such as those of `contains`, `indexOf` or an equality check, never on ones that are kept. To check that a use is honest, follow the parameter through the body. If it only reaches `==`, `equals` or `hashCode`, the promise holds. If it reaches a field, a collection or a callback that keeps it, remove the annotation and make the type invariant, or split it into a read view and a write view, as lesson 11 of this track does.

**`@UnsafeVariance` is a promise, not a check. Put it only on parameters that are compared, never kept.**

Three more tools sit at the edges of the type system, and one of them is a box that can never hold anything."""

S4 = """Function types carry variance on both ends. `(P) -> R` is `Function1<in P, out R>` (lesson 5): a function takes its parameter in and hands its result out. So a helper that joins two steps accepts a more general second step, and its result can be used as something more general:

```java
// Function<T, R> is invariant, so the JDK writes the variance into the signature:
// default <V> Function<T, V> andThen(Function<? super R, ? extends V> after)
Function<String, Long> toGrams = s -> new BigDecimal(s).movePointRight(3).longValueExact();   // kilograms to grams
Function<Object, String> describe = x -> "<" + x + ">";
Function<String, String> pipeline = toGrams.andThen(describe);      // <1250> for "1.25"
```

```kotlin
fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C = { a -> second(first(a)) }

val toGrams: (String) -> Long = { BigDecimal(it).movePointRight(3).longValueExact() }   // kilograms to grams
val describe: (Any) -> String = { "<$it>" }                  // takes Any, not just Long
val pipeline: (String) -> CharSequence = andThen(toGrams, describe)   // <1250> for "1.25"
```

`Nothing` is the **bottom type**: a subtype of every type, with no values at all. It's the one box that can never hold anything, so it fits every label. `throw` and `TODO()` have the type `Nothing`, which is why `val strict: Long = text.toLongOrNull() ?: fail("not a number")` type-checks when `fun fail(reason: String): Nothing`. It also explains `emptyList()`. One shared, empty `List<Nothing>` fits every `List<Apple>`, because `List` is `out E` and `Nothing` sits below `Apple`: an empty display case is a perfectly good apple display. Lesson 11 uses the same trick for `Either`. Java has no bottom type. `Collections.emptyList()` is a generic method whose `T` is inferred at each call, and a Kotlin `List<Nothing>` reaches Java as a raw `List`.

A **type alias** gives an existing type a shorter name, and it can be generic:

```java
// Java has no type aliases. The nearest thing, a functional interface, is a new, separate type.
@FunctionalInterface interface Listener<E> { void hear(E item); }
```

```kotlin
typealias Listener<E> = (E) -> Unit          // just a name: a Listener<E> IS an (E) -> Unit
typealias Index<K> = MutableMap<K, MutableList<K>>

val signWriter: Listener<Apple> = { println("sign for ${it.name}") }
val plain: (Apple) -> Unit = signWriter      // same type, no conversion
```

An alias is a nickname written on the label, not a new kind of box. So it has the variance of what it stands for: a `Listener<Fruit>` is a `Listener<Apple>`, exactly as with the function type. That's how lesson 5's delivery bell took a stock-keeper who counts every fruit. Aliases nested inside a class became Stable in Kotlin 2.3, with one limit: they can't mention the outer class's type parameters.

All the tools in this lesson share one limit, and it's worth saying plainly: each is a promise the compiler partly takes on trust. A recursive bound can't stop a liar, `T & Any` means nothing to Java, and `@UnsafeVariance` is believed without a second look. The lab puts the first and the last of them to work on the shop's order forms."""

CLOSING = """We started at the counter, where a gift-box form came back as "an order form". A recursive bound puts a blank at the top of the base form, and each subclass writes its own name there, so every shared setter hands back the right kind of form. `T & Any` says a box holds a real fruit, `@UnsafeVariance` lets the display case answer without opening, and `Nothing` fits every label.

Now search your code for `return this as` in a base class, or `@UnsafeVariance` on a parameter that gets stored. Each one is a promise nobody checks.

Next, we'll build four small designs that use the whole track. How do you store a listener for apples among listeners for any fruit?"""

L = {
    "id": "gen-10",
    "title": "Advanced generics: recursive bounds, T & Any, @UnsafeVariance",
    "minutes": 38,
    "goal": "By the end you can write a self-typed builder hierarchy with a recursive bound in Kotlin and Java, use `T & Any` for values known not to be null, explain why `List<out E>` may take an `E` in `contains` and when `@UnsafeVariance` is a lie, and use function-type variance, `Nothing` and generic type aliases on purpose.",
    "opening": OPENING,
    "warmup": {
        "q": "`open class Base { fun grams(g: Int): Base = this }` and `class GiftBox : Base() { fun ribbon(c: String): GiftBox = this }`. Which chain compiles?",
        "options": [
            "`GiftBox().grams(1_200).ribbon(\"red\")`",
            "`GiftBox().ribbon(\"red\").grams(1_200)`",
            "Both, because the object is a `GiftBox` either way",
            "Neither"
        ],
        "answer": 1,
        "why": "Each call returns its declared type. `ribbon` returns a `GiftBox`, so `grams` can follow. `grams` returns a `Base`, and `Base` has no `ribbon`, even though the object really is a `GiftBox`. The compiler goes by static types, which is the problem self types solve."
    },
    "sections": [
        {
            "h": "A form that names itself: a recursive bound keeps the builder chain typed",
            "body": S1,
            "figure": {"svg": FIG, "caption": "A recursive bound lets the base class return its own subclass, so a chain keeps the subclass's setters in reach. Each subclass writes its own name into the blank."},
            "try": {
                "title": "Break a builder chain, then fix it with B : Builder<B>",
                "minutes": 4,
                "steps": [
                    "Run `SelfTypeDemo` (or `SelfTypeDemoJava`). Compare the static type and the run-time class on the first line.",
                    "Uncomment wrong move 1. Predict, then run.",
                    "Uncomment wrong move 2, the `Liar` class. It compiles. Add `println(Liar().grams(5)::class.simpleName)` below it and predict what prints."
                ],
                "code": kdemo("SelfTypeDemo", "SelfTypeDemoJava"),
                "expect": "Both print `after grams(): static type PlainBuilder, run-time class PlainGiftBoxBuilder` and `gift box, 1200 g, red ribbon`. Wrong move 1 fails with `Unresolved reference 'ribbon' on receiver of type 'PlainBuilder'.` (Java: `cannot find symbol`). The `Liar` compiles because the bound only asks for some builder, and `Liar().grams(5)` prints `GiftBoxBuilder`: a fresh object, not the liar you filled in. Nothing forces a subclass to write its own name in the blank."
            },
            "refs": [
                {"title": "Generics: upper bounds (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "This box always holds a real fruit: T & Any takes null out of a type",
            "body": S2,
            "try": {
                "title": "Take null out of a type",
                "minutes": 4,
                "steps": [
                    "Run `NonNullDemo` (or `NonNullDemoJava`). Open `NotNullTransformer.java` next to it: a Java interface marked with `@NotNull`.",
                    "Uncomment wrong moves 1 and 2 in `NonNullDemo.kt` one at a time. Predict each error first.",
                    "Uncomment function 3 at the bottom. In the Java twin, uncomment the `oops` line and run: what does Java catch, and when?"
                ],
                "code": kdemo("NonNullDemo", "NonNullDemoJava"),
                "expect": "Both print `first = Gala, shown = no note` and `transformed = GALA`. Kotlin's wrong moves: (1) `Return type mismatch: expected 'T (of fun <T> forget) & Any', actual 'T (of fun <T> forget)'.`, (2) `Null cannot be a value of a non-null type 'String'.`, because for `T = String?`, `T & Any` is `String`. Function 3: `Intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.` The Java `oops` line compiles, and throws `NullPointerException` from `Objects.requireNonNull` when it runs."
            }
        },
        {
            "h": "A display case you can ask but not fill: @UnsafeVariance and List.contains",
            "body": S3,
            "try": {
                "title": "Use the annotation well, then badly",
                "minutes": 4,
                "steps": [
                    "Run `UnsafeVarianceDemo` and `UnsafeVarianceDemoJava`. Find the line that compiles in Java and is refused in Kotlin.",
                    "Uncomment wrong move 1 in the Kotlin file. Predict, then run.",
                    "Uncomment wrong move 2 (`DisplayCase2`) and read the error. That's the check `@UnsafeVariance` switched off in `DisplayCase`."
                ],
                "code": kdemo("UnsafeVarianceDemo", "UnsafeVarianceDemoJava"),
                "expect": "Both print `contains(150): true, contains(2.5): false` and `ClassCastException: class workbench.generics.l10.demo.Lemon cannot be cast to class workbench.generics.l10.demo.Apple`. Java also prints `contains(\"180\") compiles in Java: false`. In Kotlin, wrong move 1 fails with `Type inference failed. The value of the type parameter 'T' must be mentioned in input types ...`, and `DisplayCase2` fails with `Type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of class DisplayCase2<out T>)'.`"
            },
            "refs": [
                {"title": "UnsafeVariance (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/", "kind": "docs"}
            ]
        },
        {
            "h": "Three more tools at the edges: function types, Nothing and type aliases",
            "body": S4,
            "try": {
                "title": "Compose with variance, fail with Nothing",
                "minutes": 4,
                "steps": [
                    "Run `FunctionTypesDemo` (or `FunctionTypesDemoJava`, which also calls the JDK's own `andThen`).",
                    "Uncomment the wrong move and read which type the compiler found for the pipeline.",
                    "Change `fail`'s return type from `Nothing` to `Unit`. Which line breaks, and why?"
                ],
                "code": kdemo("FunctionTypesDemo", "FunctionTypesDemoJava"),
                "expect": "Kotlin prints `pipeline(\"1.25\") = <1250>`, `none = [], grams = 0, strict = 180` and `sign for Gala`. Java prints the pipeline line, `JDK andThen: <350>`, `none = [], strict = 180` and `sign for Gala`. The wrong move fails with `Initializer type mismatch: expected '(Any) -> String', actual '(String) -> String'.`: a function that needs a `String` input can't stand in for one that takes `Any`. With `Unit`, the `strict` line fails with `Initializer type mismatch: expected 'Long', actual 'Any'.`, because the elvis expression's type becomes the common supertype of `Long` and `Unit`. `Nothing` fits there because it is a subtype of `Long`."
            },
            "refs": [
                {"title": "Type aliases (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-aliases.html", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "A self-typed order builder in Java and Kotlin",
        "java": {
            "title": "OrderBuilder.java",
            "src": "abstract class OrderBuilder<B extends OrderBuilder<B>> {\n    protected int grams;\n    protected String variety;\n\n    B grams(int grams) { this.grams = grams; return self(); }\n    B variety(String name) { this.variety = name; return self(); }\n    protected abstract B self();\n}\n\nfinal class GiftBoxBuilder extends OrderBuilder<GiftBoxBuilder> {\n    private String ribbon;\n\n    GiftBoxBuilder ribbon(String colour) { this.ribbon = colour; return this; }\n    @Override protected GiftBoxBuilder self() { return this; }\n\n    GiftBox build() {\n        if (grams <= 0) throw new IllegalStateException(\"weight must be positive\");\n        return new GiftBox(grams, variety, \"\", ribbon);\n    }\n}\n\n// new GiftBoxBuilder().grams(1_200).variety(\"Gala\").ribbon(\"red\").build();"
        },
        "kotlin": {
            "title": "OrderBuilder.kt",
            "src": "abstract class OrderBuilder<B : OrderBuilder<B>> {\n    protected var grams: Int = 0\n    protected var variety: String? = null\n\n    fun grams(grams: Int): B { this.grams = grams; return self() }\n    fun variety(name: String): B { variety = name; return self() }\n    protected abstract fun self(): B\n}\n\nclass GiftBoxBuilder : OrderBuilder<GiftBoxBuilder>() {\n    private var ribbon: String? = null\n\n    fun ribbon(colour: String): GiftBoxBuilder { ribbon = colour; return this }\n    override fun self() = this\n\n    fun build(): GiftBox {\n        check(grams > 0) { \"weight must be positive\" }\n        return GiftBox(grams, variety!!, \"\", checkNotNull(ribbon))\n    }\n}\n\n// GiftBoxBuilder().grams(1_200).variety(\"Gala\").ribbon(\"red\").build()"
        },
        "note": "The recursive bound is the same idea in both languages: `B extends OrderBuilder<B>` and `B : OrderBuilder<B>`, with each subclass passing itself and an abstract `self()` in place of an unchecked cast. Kotlin adds checks Java can't express. `variety` and `ribbon` are `String?`, so `build()` must deal with a missing value, and `check` and `checkNotNull` throw `IllegalStateException` with your message. Java's `build()` happily passes a `null` ribbon along. The other three tools of this lesson have no Java twin: `T & Any` (Java types carry no nullability), `@UnsafeVariance` (Java has no declaration-site variance to suppress) and `Nothing` (Java has no bottom type). Java has no type aliases either. And in Kotlin you can often skip the builder entirely with a data class, default arguments and `copy`."
    },
    "worked": {
        "title": "Add a pickup order to the builder hierarchy",
        "steps": [
            {"say": "The lab's hierarchy has gift boxes and deliveries. The shop wants pickup orders too, collected at the counter at a set time. The quickest path is to copy `GiftBoxBuilder` and edit it, and that's how the classic bug gets in: the type argument still says `GiftBoxBuilder`.",
             "code": "class PickupBuilder : OrderBuilder<GiftBoxBuilder>() {   // copied, not changed\n    private var time: String? = null\n    fun pickupAt(time: String): PickupBuilder { this.time = time; return this }\n    override fun self(): GiftBoxBuilder = this\n}\n// error: Return type mismatch: expected 'GiftBoxBuilder', actual 'PickupBuilder'.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class PickupBuilder extends OrderBuilder<GiftBoxBuilder> {   // copied, not changed\n    private String time;\n    PickupBuilder pickupAt(String time) { this.time = time; return this; }\n    @Override protected GiftBoxBuilder self() { return this; }\n}\n// error: incompatible types: PickupBuilder cannot be converted to GiftBoxBuilder"},
            {"say": "1. The abstract `self()` caught it at compile time. With `return this as B` in the base class, the same slip would compile, and `PickupBuilder().grams(500)` would throw `ClassCastException: class PickupBuilder cannot be cast to class GiftBoxBuilder` at the call. Fix the declaration: the subclass writes its own name in the blank.",
             "code": "class PickupBuilder : OrderBuilder<PickupBuilder>() {\n    private var time: String? = null\n    fun pickupAt(time: String): PickupBuilder { this.time = time; return this }\n    override fun self() = this       // B is PickupBuilder: no cast",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class PickupBuilder extends OrderBuilder<PickupBuilder> {\n    private String time;\n    PickupBuilder pickupAt(String time) { this.time = time; return this; }\n    @Override protected PickupBuilder self() { return this; }   // no cast"},
            {"say": "2. Build: check the shared fields with the base class's `checkCommon()`, then the pickup's own field. Self-check before reading the comment: why does `grams(...)` in the chain below return a `PickupBuilder`, with no change to the base class? (Because the declaration fills `B` with `PickupBuilder`, and `grams` returns `B`.)",
             "code": "    fun build(): Pickup {\n        checkCommon()\n        val t = checkNotNull(time) { \"pickup time is required\" }\n        return Pickup(grams, variety!!, note, t)\n    }\n}\n\nval p = PickupBuilder().grams(2_500).variety(\"Fuji\").pickupAt(\"17:30\").build()",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "    Pickup build() {\n        checkCommon();\n        if (time == null) throw new IllegalStateException(\"pickup time is required\");\n        return new Pickup(grams, variety, note, time);\n    }\n}\n\nPickup p = new PickupBuilder().grams(2_500).variety(\"Fuji\").pickupAt(\"17:30\").build();"}
        ]
    },
    "lab": {
        "title": "A self-typed order builder, and functions with variance",
        "minutes": 13,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l10/Builders.kt",
            f"{LAB}/main/kotlin/workbench/generics/l10/Functions.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l10.*'",
        "steps": [
            "Run the tests. All eight fail. The signatures are done, so read them first, especially `OrderBuilder<B : OrderBuilder<B>>` and the two subclass declarations.",
            "In `Builders.kt`, write the three shared setters: store the value, then `return self()`. Write `checkCommon()` with two `check(...)` calls.",
            "Write `self()`, the setter and `build()` in `GiftBoxBuilder` and in `DeliveryBuilder`. `build()` calls `checkCommon()` first, then checks its own field.",
            "In `Functions.kt`, write `andThen` as a lambda, and `fanOut` as a lambda that calls each listener in order. Read the `fanOut` test: it passes a `Listener<Fruit>` where a `Listener<Apple>` is expected.",
            "Write `firstNotNullValue` with a loop. Notice that returning the smart-cast `item` satisfies `T & Any`.",
            "Run the tests until all eight pass."
        ],
        "hints": [
            "`fun grams(grams: Int): B { this.grams = grams; return self() }` is the whole pattern for each shared setter.",
            "`checkNotNull(ribbon) { \"ribbon is required\" }` returns the value if it isn't null, or throws `IllegalStateException` with that message.",
            "`andThen` is one line: `= { a -> second(first(a)) }`. `fanOut` is `= { item -> for (l in listeners) l(item) }`."
        ],
        "done_when": "All eight tests in `AdvancedTest` pass."
    },
    "drill": {
        "title": "Write a self-typed builder from memory",
        "minutes": 5,
        "prompt": "Close this page. Write an abstract `Builder` with a recursive bound, one setter `grams(n)` that returns the subclass type, and an abstract `self()`. Then write `GiftBoxBuilder` with `ribbon(colour)` and `build()`, so that `GiftBoxBuilder().grams(1_200).ribbon(\"red\").build()` compiles. Do it in Kotlin, then in Java.",
        "answer": {
            "lang": "kotlin",
            "src": "abstract class Builder<B : Builder<B>> {\n    protected var grams = 0\n    fun grams(grams: Int): B { this.grams = grams; return self() }\n    protected abstract fun self(): B\n}\n\nclass GiftBoxBuilder : Builder<GiftBoxBuilder>() {      // the subclass writes its own name in B\n    private var ribbon = \"\"\n    fun ribbon(colour: String): GiftBoxBuilder { ribbon = colour; return this }\n    override fun self() = this\n    fun build() = \"gift box, $grams g, $ribbon ribbon\"\n}",
            "alt": {"lang": "java", "title": "Builder.java", "src": "abstract class Builder<B extends Builder<B>> {\n    protected int grams;\n    B grams(int grams) { this.grams = grams; return self(); }\n    protected abstract B self();\n}\n\nfinal class GiftBoxBuilder extends Builder<GiftBoxBuilder> {   // the subclass writes its own name in B\n    private String ribbon = \"\";\n    GiftBoxBuilder ribbon(String colour) { ribbon = colour; return this; }\n    @Override protected GiftBoxBuilder self() { return this; }\n    String build() { return \"gift box, \" + grams + \" g, \" + ribbon + \" ribbon\"; }\n}"}
        }
    },
    "recap": [
        "A recursive bound, `B : Builder<B>`, lets a base class name its own subclass, so shared setters can return it and a chain keeps the subclass's methods.",
        "Each subclass writes its own name in the blank (`GiftBoxBuilder : Builder<GiftBoxBuilder>()`) and implements an abstract `self() = this`. Avoid `this as B`: it is unchecked and fails late.",
        "`T & Any` is \"T without null\": for `T = String?` it's `String`. Its main use is overriding Java generic methods marked `@NotNull`.",
        "`List<out E>` declares `contains(element: @UnsafeVariance E)`. That's safe because `contains` only compares, and the `E` lets Kotlin refuse `listOf(180).contains(\"180\")`.",
        "`Nothing` is a subtype of every type, so `emptyList()` fits any `List<T>` and `?: fail(...)` type-checks. A type alias is only a new name, with the variance of the type it names.",
        "The limit: these tools are partly taken on trust. A subclass can write the wrong name, Java never sees `& Any`, and `@UnsafeVariance` on a stored parameter ends in a `ClassCastException`."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "`abstract class Builder<B : Builder<B>> { fun grams(n: Int): B; ... }` and `class GiftBoxBuilder : Builder<GiftBoxBuilder>()`. What is the static type of `GiftBoxBuilder().grams(1_200)`?",
            "options": [
                "`Builder<GiftBoxBuilder>`",
                "`GiftBoxBuilder`",
                "`Builder<*>`",
                "`B`, which the compiler can't resolve outside the class"
            ],
            "answer": 1,
            "why": "`grams` returns `B`, and the subclass declaration fills `B` with `GiftBoxBuilder`. So at the call site the result is a `GiftBoxBuilder`, and its own methods, such as `ribbon`, are still in reach. That is the whole point of the recursive bound."
        },
        {
            "q": "`fun <T> List<T>.firstNotNullValue(): T & Any`. What is the type of `listOf<String?>(null, \"Gala\").firstNotNullValue()`?",
            "options": [
                "`String`",
                "`String?`",
                "`Any`",
                "`String & Any?`"
            ],
            "answer": 0,
            "why": "`T` is `String?`, and `& Any` removes the null: `String?` minus null is `String`. With `T = Apple` it would be `Apple`. That's why the result can go straight into a `val variety: String`."
        },
        {
            "q": "Why can `interface List<out E>` declare `fun contains(element: @UnsafeVariance E): Boolean` without risk?",
            "options": [
                "Because the annotation moves the check to run time",
                "Because `List` is immutable, so nothing can be stored",
                "Because `contains` only compares the argument and never stores it, so a `List<Int>` seen as a `List<Number>` can't be damaged",
                "Because `E` is erased, so variance doesn't apply at run time"
            ],
            "answer": 2,
            "why": "Variance protects against storing a wrong value. `contains` stores nothing; asking a list of ints whether it contains `2.5` just returns `false`. The annotation is a promise about that, not a check at run time. And \"immutable\" isn't the reason: `@UnsafeVariance` on a storing method breaks a class however read-only it looks, as the `DisplayCase` demo shows."
        },
        {
            "q": "`val toGrams: (String) -> Long` and `val describe: (Any) -> String`. With `fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C`, does `val p: (String) -> CharSequence = andThen(toGrams, describe)` compile?",
            "options": [
                "No: `describe` must be exactly `(Long) -> String`",
                "No: the result would be `(String) -> String`, which is not a `(String) -> CharSequence`",
                "Only with an explicit cast",
                "Yes: `(Any) -> String` is a `(Long) -> String` (in on the parameter), and `(String) -> String` is a `(String) -> CharSequence` (out on the result)"
            ],
            "answer": 3,
            "why": "Function types are `Function1<in P, out R>`. A function that accepts any value can stand in for one that accepts a `Long`, and a function that returns a `String` can stand in for one that returns a `CharSequence`. It's the \"pick the right variance\" check from lesson 5, applied twice in one call."
        },
        {
            "q": "From \"Covariance with out: producers\": `class DisplayCase<out T> { fun add(item: T) {} }` doesn't compile. What does the compiler object to?",
            "options": [
                "`T` appears in an in-position (a parameter) in a class that declared it `out`",
                "`add` is public; it would compile if it were `protected`",
                "Classes declared `out` can't have functions with parameters",
                "`DisplayCase` needs a constructor that takes a `T`"
            ],
            "answer": 0,
            "why": "An `out` type parameter may appear only in out-positions, such as return types; a parameter is an in-position, a slot in the dispenser. `protected` members are checked too; only `private` ones are exempt. `@UnsafeVariance` would silence the error, and this lesson's demo shows what that costs when `add` keeps the value.",
            "from": "gen-04"
        }
    ],
    "flashcards": [
        {"front": "What problem does `abstract class Builder<B : Builder<B>>` solve?", "back": "Shared setters in the base class can return `B`, the concrete subclass, so a chain like `GiftBoxBuilder().grams(1_200).ribbon(\"red\")` keeps the subclass's methods."},
        {"front": "Why an abstract `self(): B` instead of `return this as B`?", "back": "`this as B` is unchecked and fails late if a subclass passes the wrong type argument. An overridden `self() = this` is checked by the compiler."},
        {"front": "What does `T & Any` mean?", "back": "`T` with null removed: a definitely non-nullable type. For `T = String?` it is `String`."},
        {"front": "What is the main use of `T & Any`?", "back": "Overriding Java generic methods whose parameters or results are annotated `@NotNull`."},
        {"front": "How does `List<out E>` get away with `contains(element: E)`?", "back": "The parameter is marked `@UnsafeVariance`. It's safe because `contains` only compares the element and never stores it."},
        {"front": "Why does `val none: List<Apple> = emptyList()` compile?", "back": "`emptyList()` gives a `List<Nothing>`. `Nothing` is a subtype of every type, and `List` is `out E`, so it is a `List<Apple>`."},
        {"front": "Is `typealias Listener<E> = (E) -> Unit` a new type?", "back": "No. It's only a name: a `Listener<Apple>` is an `(Apple) -> Unit`, with the same variance."}
    ],
    "terms": [
        {"term": "Recursive bound", "plain": "A bound that mentions the type parameter itself: `T : Comparable<T>`, `B : Builder<B>`."},
        {"term": "Self type", "plain": "A type parameter that stands for \"my own subclass\", so methods in the base class can return it."},
        {"term": "Definitely non-nullable type", "plain": "`T & Any`: the type parameter `T` with null taken out."},
        {"term": "@UnsafeVariance", "plain": "An annotation that switches off the variance check for one use of a type. A promise, not a check."},
        {"term": "Nothing", "plain": "Kotlin's bottom type: a subtype of every type, with no values. The type of `throw` and `TODO()`."},
        {"term": "Type alias", "plain": "A new name for an existing type, such as `typealias Listener<E> = (E) -> Unit`. Not a new type."}
    ],
    "explain_back": {
        "prompt": "A teammate sees `abstract class OrderBuilder<B : OrderBuilder<B>>` in a code review and says it looks circular and pointless. Explain in your own words what problem it solves, how a subclass uses it, and what it can't prevent.",
        "answer": "Without it, a setter in the base class can only return the base class type. So after calling `grams()` on a `GiftBoxBuilder`, the compiler thinks it has a plain order builder and won't let you call `ribbon()`. The recursive bound gives the base class a name, `B`, for \"whatever concrete subclass I am\", like a blank at the top of a form. Each subclass fills it in with its own name, as in `class GiftBoxBuilder : OrderBuilder<GiftBoxBuilder>()`, so for that subclass `B` means `GiftBoxBuilder`, and every inherited setter returns that type. The bound only looks circular: it reads \"B is a builder whose B is B\", which only self-naming subclasses satisfy. Each subclass implements `self()` as `this`, which the compiler checks, so no unchecked cast is needed. What it can't prevent is a subclass writing the wrong name, such as a pickup builder that says `OrderBuilder<GiftBoxBuilder>`. The abstract `self()` turns that slip into a compile error, which is why it's better than `this as B`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Recursive bounds go further than builders. `java.lang.Enum` is declared `Enum<E extends Enum<E>>` so that `compareTo` takes the same enum type, and `EnumSet.noneOf(Class<E>)` is bounded `<E extends Enum<E>>`. Kotlin's `Enum<E : Enum<E>>` is the same declaration. Lesson 2's `fun <T : Comparable<T>> maxOf2(a: T, b: T)` is the most common recursive bound of all; the Java signature Kotlin generates for it is `<T extends Comparable<? super T>>`, because Kotlin's `Comparable` is declared `in T`.\n\nThe standard library's use of `@UnsafeVariance` is easy to check. In the 2.4.21 sources (`kotlin-stdlib-sources.jar`, file `Collections.kt`) it appears on `contains`, `containsAll` and `indexOf` of `List`, and on `AbstractCollection.contains`. The `contains(\"180\")` error you saw comes from a second safety net. When the member `contains(element: Int)` doesn't accept a `String`, the compiler tries the extension `Iterable<T>.contains(element: T)`, whose `T` is marked so that it must match the receiver's element type, and inference fails with the message you read.\n\nTwo small facts about `Nothing`. The type of the literal `null` is `Nothing?`, which is why `null` fits every nullable type. And when a Kotlin function returns `List<Nothing>`, Java sees a raw `List`, because Java has no bottom type to write there.\n\nType aliases can't create the separate types people sometimes want from them. `typealias CrateId = String` lets you pass any `String` where a `CrateId` is expected. If you want the compiler to keep crate ids and supplier ids apart, use a value class, `@JvmInline value class CrateId(val value: String)`, which is a real type with no wrapper object at run time in most uses."
    },
    "sources": [
        {"title": "Generics: definitely non-nullable types and variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "UnsafeVariance (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/"},
        {"title": "Type aliases (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-aliases.html"},
        {"title": "What's new in Kotlin 2.3.0: nested type aliases", "url": "https://kotlinlang.org/docs/whatsnew23.html"}
    ]
}

out = ROOT / "content/lessons/gen-10.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
