import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="


def demo(rel, title, main, lang="kotlin", alt=None):
    path = f"{LAB}/demo/{rel}"
    d = {"lang": lang, "title": title, "src": read(path), "run": RUN + main, "file": path}
    if alt:
        d["alt"] = demo(*alt)
    return d


def jdemo(name):
    return (f"java/workbench/generics/l02/demo/{name}.java", f"{name}.java", f"workbench.generics.l02.demo.{name}", "java")


FIG = (
    '<svg viewBox="0 0 640 300" role="img" aria-label="Nested fences of types. The default bound Any? allows every type including nullable ones. '
    'T : Any allows only non-null types. Inside it, Comparable types and CharSequence types overlap; a where clause with both bounds allows only the overlap, such as String and StringBuilder.">'
    '<rect class="box-dim" x="10" y="10" width="620" height="280" rx="8"/>'
    '<text class="t-s" x="320" y="30" text-anchor="middle">fun &lt;T&gt;  (bound Any?): every type, null included</text>'
    '<rect class="box" x="40" y="44" width="560" height="208" rx="8"/>'
    '<text class="t-s" x="320" y="64" text-anchor="middle">T : Any   every non-null type</text>'
    '<rect class="box-a" x="70" y="80" width="300" height="150" rx="8"/>'
    '<rect class="box-b" x="270" y="80" width="300" height="150" rx="8"/>'
    '<text class="t-s t-code" x="165" y="102" text-anchor="middle">T : Comparable&lt;T&gt;</text>'
    '<text class="t-s t-code" x="475" y="102" text-anchor="middle">T : CharSequence</text>'
    '<text class="t-s" x="165" y="150" text-anchor="middle">Int, LocalDate</text>'
    '<text class="t-s" x="165" y="170" text-anchor="middle">Grams</text>'
    '<text class="t-s" x="475" y="150" text-anchor="middle">a CharSequence</text>'
    '<text class="t-s" x="475" y="170" text-anchor="middle">with no compareTo</text>'
    '<text class="t-s t-a" x="320" y="140" text-anchor="middle">String</text>'
    '<text class="t-s t-a" x="320" y="160" text-anchor="middle">StringBuilder</text>'
    '<text class="t-s t-a" x="320" y="214" text-anchor="middle">where: both</text>'
    '<text class="t-s t-m" x="320" y="275" text-anchor="middle">String?, Int?, null: only the default bound lets these in</text>'
    '</svg>'
)

OPENING = """In the shop's storeroom, one box carries a sign: "fruit only". The sign shuts out the hammer and the till roll. In return, whoever unpacks the box knows something about every item in it: each one has a weight, so it can go straight on the scales.

In Generics from zero, `T` was a blank on a label that each caller fills in. Any caller, any type. That freedom has a price, and it surprises people. Inside a generic function, you can't ask a `T` for its `length`, even when every caller you have in mind passes a `String`.

The trap is to think the compiler knows your callers. It only knows the label. In this lesson, we'll find out what a plain `T` can do, and write signs that say "fruit only" and "can be compared". Then we'll ask for two things at once with `where`, and keep `null` out of the box with `T : Any`. Before we start, make a guess, and keep it in mind."""

S1 = """Start with a plain type parameter, one with no sign on it at all. It means "some type, I don't know which", so inside the function, `T` can do only what every type can do. In Java, the type that every object belongs to is `Object`. In Kotlin, "every type" includes the nullable ones, such as `String?`, so a `T` with no bound is held to **`Any?`**.

```java
static <T> String describe(T x) {
    return "value=" + x + ", hash=" + Objects.hashCode(x);
}

describe("Gala");   // fine
describe(180);      // fine
describe(null);     // fine: any Java T accepts null
```

```kotlin
fun <T> describe(x: T): String = "value=$x, hash=${x.hashCode()}"

describe("Gala")    // fine
describe(180)       // fine
describe(null)      // also fine: T is inferred as Nothing?
```

`toString()`, `hashCode()` and `==` work, because they exist on `Any?`. The demo prints `value=Gala, hash=2211823`, `value=180, hash=180` and `value=null, hash=0`. Anything more specific fails, even when every caller you have in mind would pass a `String`:

```java
static <T> int lengthOf(T x) { return x.length(); }
// error: cannot find symbol: method length()
```

```kotlin
fun <T> lengthOf(x: T) = x.length
// error: unresolved reference 'length'.
```

The compiler isn't being fussy. Someone could call `lengthOf(42)`, and an `Int` has no `length`. A generic function must work for every type the caller is allowed to pick, so it can only use what all of them share.

Comparison fails the same way. Java says `cannot find symbol: method compareTo(T)`. Kotlin gives a stranger message:

```java
static <T> T bigger(T a, T b) { return a.compareTo(b) >= 0 ? a : b; }
// error: cannot find symbol: method compareTo(T)
```

```kotlin
fun <T> bigger(a: T, b: T): T = if (a > b) a else b
// error: candidate 'fun String.compareTo(other: String, ignoreCase: Boolean = ...): Int'
//        is inapplicable because of a receiver type mismatch.
```

In Kotlin, `a > b` means `a.compareTo(b)`. The compiler goes looking for any `compareTo` it could use on a `T`, finds only the one on `String`, and reports that this one doesn't fit. It's a roundabout way of saying no. When an error mentions some unrelated type's method, read it as "this operation isn't defined for `T`".

The null case surprises people coming from Java, where every `T` accepts `null` anyway and nobody thinks about it. In Kotlin, `fun <T> f(x: T)` accepts `null` too, because `T` may be `String?` or `Nothing?`. (`Nothing?` is the type Kotlin gives a bare `null`. Write `val x = null`, then `val y: Int = x`, and the error says `actual 'Nothing?'`.) If your function must not see null, you have to say so. The last section shows how.

That is the job of a **bound**: a sign on the type parameter that promises more about `T`. The caller can pick from fewer types, and in return your code can do more with the one they pick."""

S2 = """Here is the sign from the opening, written in code. The shop's fruit share an interface, `Fruit`, with a name and a weight in grams, and `Apple` is a small data class that implements it. An **upper bound** says "`T` must be this type or a subtype of it". For now, read subtype as a class that inherits from it, the way `Apple` inherits from `Fruit`; the next lesson gives the word its exact meaning. Java writes the bound with `extends`, even for interfaces. Kotlin writes it after a colon:

```java
interface Fruit { String name(); int grams(); }
record Apple(String name, int grams) implements Fruit {}

static <T extends Fruit> T heavier(T a, T b) {
    return a.grams() >= b.grams() ? a : b;      // grams() comes from the bound
}

Apple apple = heavier(new Apple("Gala", 180), new Apple("Fuji", 150));
```

```kotlin
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit

fun <T : Fruit> heavier(a: T, b: T): T =
    if (a.grams >= b.grams) a else b             // .grams comes from the bound

val apple: Apple = heavier(Apple("Gala", 180), Apple("Fuji", 150))
```

The bound does two jobs. Inside the function, `a.grams` compiles, because every `T` is now some kind of `Fruit`. At each call, the sign turns everything else away: `heavier("Gala", "Fuji")` fails with `argument type mismatch: actual type is 'String', but 'Fruit' was expected.`

You may wonder why `heavier` needs a `T` at all. Why not take two `Fruit` parameters and return a `Fruit`? Because then two apples in would give a `Fruit` out. To get your `Apple` back, you'd need a cast, the very thing lesson 1 of this track removed. With `T`, two apples in give an `Apple` out.

The most common bound in practice isn't a class you wrote. It's `Comparable<T>`:

```java
static <T extends Comparable<T>> T maxOf2(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

maxOf2(180, 150);                                   // 180
maxOf2("Gala", "Fuji");                             // Gala
```

```kotlin
fun <T : Comparable<T>> maxOf2(a: T, b: T): T = if (a > b) a else b

maxOf2(180, 150)                                    // 180
maxOf2("Gala", "Fuji")                              // Gala
maxOf2(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30))   // 2026-11-02
```

Read `T : Comparable<T>` aloud as "T is something that can be compared with another T". `Int` is a `Comparable<Int>`, `String` is a `Comparable<String>`, and `LocalDate`, the JDK's class for a calendar date, is a `Comparable<ChronoLocalDate>`. Kotlin accepts that last one because `Comparable` is declared `in T`, which lesson 5 of this track explains. Inside the function, `a > b` now compiles, because the bound guarantees a `compareTo`.

The `T` appears twice in `T : Comparable<T>`, and that's on purpose. `Comparable<T>` says what `T` can be compared *with*. A bound that mentions its own type parameter is called a **recursive bound**. You'll meet it again in `Enum<E : Enum<E>>`, and in builder classes in lesson 10 of this track.

Now hand the comparing function two apples:

```java
maxOf2(new Apple("Gala", 180), new Apple("Fuji", 150));
// error: method maxOf2 ... cannot be applied to given types
//   reason: inference variable T has incompatible bounds
//     upper bounds: Comparable<T>   lower bounds: Apple
```

```kotlin
maxOf2(Apple("Gala", 180), Apple("Fuji", 150))
// error: argument type mismatch: actual type is 'Apple',
//        but 'Comparable<uninferred T (of fun <T : Comparable<T>> maxOf2)>' was expected.
```

`Apple` has no natural order. Should two apples compare by weight, by name or by price? The compiler won't guess, and it's right not to. Make `Apple` implement `Comparable<Apple>`, and the call compiles. Or, usually better, keep `Apple` plain and pass a `Comparator` where you need an order.

The sign picture breaks in one place. A real "fruit only" sign is checked by a person, who looks at the item. The compiler can only trust what the types declare. A class with a `grams` property that doesn't say `: Fruit` is still turned away.

One real difference between the languages shows up with `LocalDate`. In Java, `LocalDate later = maxOf2(day1, day2)` fails, because the strict bound forces `T` to be `ChronoLocalDate`. The JDK writes `<T extends Comparable<? super T>>` to fix that. Kotlin's plain `T : Comparable<T>` already returns a `LocalDate`.

**A bound shuts some callers out and lets the body do more. Ask for exactly what the body uses.**

One bound per type parameter covers most code. Sometimes, though, the body needs two abilities at once."""

S3 = """A type parameter can have more than one bound. The angle brackets hold only one, so the rest go into a **`where` clause** after the signature. Java joins the bounds with `&`. Here is a function that picks the shortest name from a list, and uses alphabetical order to break a tie:

```java
static <T extends CharSequence & Comparable<T>> T shortestLabel(List<T> items) {
    T best = items.get(0);
    for (T item : items) {
        if (item.length() < best.length()) best = item;           // CharSequence gives length()
        else if (item.length() == best.length() && item.compareTo(best) < 0) best = item;
    }
    return best;
}
```

```kotlin
fun <T> shortestLabel(items: List<T>): T
        where T : CharSequence, T : Comparable<T> {
    var best = items[0]
    for (item in items) {
        if (item.length < best.length) best = item     // CharSequence gives .length
        else if (item.length == best.length && item < best) best = item   // Comparable gives <
    }
    return best
}
```

`T` must meet every bound at once. A `String` is both a `CharSequence`, the JDK's interface for anything made of characters, and a `Comparable<String>`, so it fits. An `Int` is comparable but has no characters:

```text
error: cannot infer type for type parameter 'T'. Specify it explicitly.
error: argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.
```

You get two errors for one mistake. The first says the compiler gave up looking for a `T`. The second says why: an `Int` isn't a `CharSequence`, so no `T` can meet both bounds. When "cannot infer type" appears next to a mismatch, read the mismatch first. It's the real reason.

Here is one that surprises people: `shortestLabel(listOf(StringBuilder("plum"), StringBuilder("lime")))` compiles. `StringBuilder` became a `Comparable<StringBuilder>` in JDK 11, so it sits in the overlap too.

At most one bound may be a class. The others must be interfaces, because a class can extend only one other class. Java also wants the class first:

```java
static <T extends Number & Exception> void numberOrError(T t) {}          // error: interface expected here
static <T extends Number & Comparable<T>> T clampToZero(T x) { ... }      // fine: class first
static <T extends Comparable<T> & Number> T wrong(T x) { ... }            // error: interface expected here
```

```kotlin
fun <T> numberOrError(t: T) where T : Number, T : Exception {}
// error: only one of the upper bounds can be a class.
fun <T> clampToZero(x: T): T where T : Number, T : Comparable<T> = x      // fine
fun <T> anyOrder(x: T): T where T : Comparable<T>, T : Number = x         // also fine
```

Kotlin has no ordering rule. It just counts classes.

The figure draws each bound as a fence around the types a caller may pick. Each new bound moves a fence in, and a `where` clause with two bounds leaves only the overlap.

Use `where` when the function needs two abilities that no single type in your code names. If you find yourself writing the same pair of bounds in five places, that pair probably wants to be one interface of your own.

So far, every bound has asked for more abilities. The last one asks for less: it takes `null` away."""

S4 = """The default bound is `Any?`, so `T` may be a nullable type. Most of the time that's what you want: a `Box<String?>` is a fine thing to have. Sometimes it quietly breaks your API, the functions and classes that other code calls. Here is a small cache that notes any problem found with each crate in the storeroom. The Java version has the same problem, because `HashMap` happily stores `null` values:

```java
class Cache<K, V> {
    private final Map<K, V> entries = new HashMap<>();
    void put(K key, V value) { entries.put(key, value); }
    V get(K key) { return entries.get(key); }   // null means "no entry"... usually
}

Cache<String, String> problems = new Cache<>();
problems.put("apples", null);                   // "checked: no problem"
problems.get("apples");                         // null
problems.get("figs");                           // null, but never checked
```

```kotlin
class Cache<K, V> {
    private val entries = HashMap<K, V>()
    fun put(key: K, value: V) { entries[key] = value }
    fun get(key: K): V? = entries[key]     // null means "no entry"... usually
}

val problems = Cache<String, String?>()
problems.put("apples", null)               // "checked: no problem"
problems.get("apples")                     // null
problems.get("figs")                       // null, but never checked
```

With `V = String?`, `get` returns `null` for two different reasons: "we checked the apples and found no problem", and "nobody ever checked the figs". The demo prints `apples -> null` and `figs -> null`, then its last line: `Can you tell those two apart? Neither can the caller.`

The fix is the bound **`T : Any`**, which means "any type, but not a nullable one". Java has no such bound, so the closest it gets is a check at run time:

```java
void put(K key, V value) {
    entries.put(key, Objects.requireNonNull(value, "no null values"));   // fails at run time
}
```

```kotlin
class Cache<K : Any, V : Any> { ... }

Cache<String, String?>()
// error: type argument is not within its bounds: type parameter 'V (of class Cache<K : Any, V : Any>)'
//        must be subtype of 'Any', but actual: 'String?'.
```

Now `V?` in `get` always means "absent", because a stored value can never be `null`. The same bound helps functions that must return a real value:

```java
@SafeVarargs
static <T> T coalesce(T... values) {
    for (T v : values) if (v != null) return v;
    throw new IllegalArgumentException("all values were null");
}

String variety = coalesce(null, "Gala", "Fuji");   // the type says nothing about null
```

```kotlin
fun <T : Any> coalesce(vararg values: T?): T {
    for (v in values) if (v != null) return v
    throw IllegalArgumentException("all values were null")
}

val variety: String = coalesce(null, "Gala", "Fuji")   // String, not String?
```

The parameters are `T?` and the return type is `T`, and that difference only means something because `T` itself can't be nullable. Pass a bare `null` to a plain `T : Any` parameter, and you get `null cannot be a value of a non-null type`.

**When `null` already has a job in your API, such as "not found", a nullable `T` gives it two. Write `T : Any`.** Leave the default when holding a nullable value is fine, as in a `Box<String?>`.

Java types carry no nullability. A Java `<T>` always allows `null`. The best you can do is a run-time check, or an annotation such as `@NonNull`, which Kotlin reads when it calls the Java code. Lesson 10 of this track shows a related Kotlin tool, `T & Any`. It's for the rare case where one signature needs both a nullable `T` and a non-null version of it.

That's also where bounds stop. A bound says what one `T` may be. It says nothing about how two generic types relate to each other. Whether a crate of apples may stand in for a crate of fruit is a different question, and the next lesson's."""

CLOSING = """We started with a storeroom box marked "fruit only". A bound is that sign on a type parameter. `T : Fruit` and `T : Comparable<T>` shut some callers out and let the body weigh and compare, `where` asks for two things at once, and `T : Any` keeps `null` out.

Now look in your own code for a generic class whose `get` returns `V?` to mean "not found", such as a `Cache<K, V>`. If `V` has no bound, a stored `null` and a missing entry look the same.

Next, we'll look hard at the word we've leaned on all lesson: subtype. If an apple is a fruit, is a crate of apples a crate of fruit?"""

L = {
    "id": "gen-02",
    "title": "Bounds and constraints: upper bounds, where, T : Any",
    "minutes": 35,
    "goal": "By the end you can add an upper bound, a `where` clause or `T : Any` to a type parameter, say what each one lets your code do and which callers it shuts out, and read the matching Java `extends` and `&` syntax.",
    "opening": OPENING,
    "warmup": {
        "q": "Which of these compiles: `fun <T> f(x: T) = x.length`, `fun <T> g(x: T) = x.hashCode()`, or `fun <T> h(x: T) { }` called as `h(null)`?",
        "options": [
            "Only `f`, because the callers will pass strings",
            "`g` and `h(null)`, but not `f`",
            "None of them: an unbounded T can do nothing",
            "All three"
        ],
        "answer": 1,
        "why": "With no bound, `T` can be any type, nullable ones included, so you may only use what `Any?` has: `hashCode`, `toString`, `==`. `length` isn't on every type, and the compiler doesn't know your callers. `h(null)` compiles because `T` may be a nullable type. A bound is how you ask for more."
    },
    "sections": [
        {
            "h": "What a T with no bound can do: only what Any? can do",
            "body": S1,
            "try": {
                "title": "Find the edge of an unbounded T",
                "minutes": 3,
                "steps": [
                    "Run `UnboundedDemo` (or `UnboundedDemoJava`). Note what `describe(null)` prints.",
                    "Uncomment `lengthOf`, run, and read the error. Comment it out again.",
                    "Uncomment `bigger` and run. Before you read the message, guess which type it will mention."
                ],
                "code": demo("kotlin/workbench/generics/l02/demo/UnboundedDemo.kt", "UnboundedDemo.kt", "workbench.generics.l02.demo.UnboundedDemoKt", alt=jdemo("UnboundedDemoJava")),
                "expect": "`describe(null)` prints `value=null, hash=0`: null is a legal `T`. `lengthOf` fails with `Unresolved reference 'length'.` `bigger` fails with a message about `String.compareTo` being inapplicable, because the only `compareTo` the compiler could find is String's. Neither error is about your callers. Both say `T` promises nothing beyond `Any?`. The Java twin fails both with `cannot find symbol`: Java's `T` promises nothing beyond `Object`."
            }
        },
        {
            "h": "A box that only takes fruit: upper bounds",
            "body": S2,
            "try": {
                "title": "Bound T, then make Apple fit",
                "minutes": 5,
                "steps": [
                    "Run `MaxDemo` (or `MaxDemoJava`) and check the four results.",
                    "Uncomment the `heavier(\"Gala\", \"Fuji\")` line, run, read the error, and comment it out. Do the same with `maxOf2(1, \"a\")`.",
                    "Uncomment the two-apples line for `maxOf2` and run it. Then make `Apple` implement `Comparable<Apple>` by weight (`: Fruit, Comparable<Apple>` and `override fun compareTo(other: Apple) = grams.compareTo(other.grams)`) and run again.",
                    "Bonus, in Kotlin: what type does `heavier(Apple(\"Gala\", 180), Lemon(\"Eureka\", 120))` return? Use the probe trick from lesson 1 of this track, `val probe: Int = heavier(...)`, to find out."
                ],
                "code": demo("kotlin/workbench/generics/l02/demo/MaxDemo.kt", "MaxDemo.kt", "workbench.generics.l02.demo.MaxDemoKt", alt=jdemo("MaxDemoJava")),
                "expect": "The demo prints `Apple(name=Gala, grams=180)`, `180`, `Gala` and `2026-11-02`. `heavier(\"Gala\", \"Fuji\")` fails twice with `Argument type mismatch: actual type is 'String', but 'Fruit' was expected.` The mixed `maxOf2` call fails with `actual type is 'String', but 'Int' was expected.` The two-apples call fails with `Cannot infer type for type parameter 'T'` and `actual type is 'Apple', but 'Comparable<uninferred T ...>' was expected`. Once `Apple` is comparable, it prints `Apple(name=Gala, grams=180)`. The bonus probe says `actual 'Fruit'`: the closest type an apple and a lemon share. In the Java twin, every bad call fails with `method ... cannot be applied to given types`, and its extra wrong move shows why the JDK writes `Comparable<? super T>`: `LocalDate later = maxOf2(...)` fails with `inference variable T has incompatible bounds`."
            }
        },
        {
            "h": "Two requirements at once: the where clause",
            "body": S3,
            "figure": {"svg": FIG, "caption": "Each bound moves a fence in around the types a caller may pick. A where clause with two bounds allows only the overlap."},
            "try": {
                "title": "Predict which calls fit both bounds",
                "minutes": 4,
                "steps": [
                    "Before running `WhereDemo` (or `WhereDemoJava`), decide whether the `StringBuilder` line compiles.",
                    "Run it. Then uncomment `sortedLabel(42, 7)` and run again.",
                    "Comment that out and uncomment `numberOrError`. Run, read the error, and comment it out again."
                ],
                "code": demo("kotlin/workbench/generics/l02/demo/WhereDemo.kt", "WhereDemo.kt", "workbench.generics.l02.demo.WhereDemoKt", alt=jdemo("WhereDemoJava")),
                "expect": "The demo prints `fig (3) then kiwi (4)` and `lime (4) then plum (4)`: `StringBuilder` is both a `CharSequence` and a `Comparable<StringBuilder>` on JDK 11 and later. `sortedLabel(42, 7)` fails with `Cannot infer type for type parameter 'T'` and `actual type is 'Int', but 'CharSequence' was expected`. `numberOrError` fails with `Only one of the upper bounds can be a class.` In the Java twin, `sortedLabel(42, 7)` fails with `cannot be applied to given types`, and both bad bound lists fail with `interface expected here`."
            }
        },
        {
            "h": "Keeping null out of the box: T : Any",
            "body": S4,
            "try": {
                "title": "Make a null mean one thing",
                "minutes": 4,
                "steps": [
                    "Run `NullBoundDemo` (or `NullBoundDemoJava`). Look at the two lines it prints for `apples` and `figs`.",
                    "Change the Kotlin class header to `class Cache<K : Any, V : Any>` and run again. Java has no such bound: in the Java twin, uncomment the `requireNonNull` line instead, and see that it fails only when it runs.",
                    "Fix `main` so it compiles. How would you now record \"checked: no problem\"? (One answer: store an empty string. A better one: a small `sealed interface CheckResult` with a `NoProblem` object.)"
                ],
                "code": demo("kotlin/workbench/generics/l02/demo/NullBoundDemo.kt", "NullBoundDemo.kt", "workbench.generics.l02.demo.NullBoundDemoKt", alt=jdemo("NullBoundDemoJava")),
                "expect": "The first run prints `apples -> null` and `figs -> null`: a stored null and a missing entry look the same. With the bound, `Cache<String, String?>()` no longer compiles: `Type argument is not within its bounds: type parameter 'V (of class Cache<K : Any, V : Any>)' must be subtype of 'Any', but actual: 'String?'.` From then on, `get` returning null can only mean \"not there\". The Java twin's `requireNonNull` compiles and throws a `NullPointerException` with your message, but only when that line runs."
            }
        }
    ],
    "compare": {
        "title": "Bounds in Java and Kotlin",
        "java": {
            "title": "Bounds.java",
            "src": "import java.util.List;\n\nclass Bounds {\n    // one bound: extends, even for an interface\n    static <T extends Comparable<T>> T maxOf2(T a, T b) {\n        return a.compareTo(b) >= 0 ? a : b;\n    }\n\n    // two bounds with &: the class (if any) must come first\n    static <T extends CharSequence & Comparable<T>> T shortest(List<T> items) {\n        T best = items.get(0);\n        for (T item : items) {\n            if (item.length() < best.length()) best = item;\n        }\n        return best;\n    }\n\n    // no way to say \"not null\": T may always be null\n    static <T> T firstOrThrow(List<T> items) {\n        return items.get(0);   // could be null\n    }\n}"
        },
        "kotlin": {
            "title": "Bounds.kt",
            "src": "// one bound: a colon\nfun <T : Comparable<T>> maxOf2(a: T, b: T): T = if (a >= b) a else b\n\n// two bounds: a where clause, in any order, at most one class\nfun <T> shortest(items: List<T>): T where T : CharSequence, T : Comparable<T> {\n    var best = items[0]\n    for (item in items) {\n        if (item.length < best.length) best = item\n    }\n    return best\n}\n\n// T : Any rules out nullable type arguments\nfun <T : Any> firstOrThrow(items: List<T>): T = items[0]   // never null"
        },
        "note": "The bounds mean the same thing in both languages and compile to the same JVM bounds. Kotlin uses a colon and a `where` clause and doesn't care about order. Java uses `extends` and `&` and wants the class first. The real difference is nullability. Kotlin's default bound is `Any?`, so you can opt out of null with `T : Any`. Java has no nullable types, so every Java `T` allows null, and only annotations can say otherwise. One small surprise: javap, the JDK tool that prints what a class file contains, shows Kotlin's `T : Comparable<T>` as `<T extends Comparable<? super T>>`, because Kotlin's `Comparable` is declared `in T`. Lesson 5 of this track explains that `? super`."
    },
    "worked": {
        "title": "Build a size window that works for any comparable type",
        "steps": [
            {"say": "The shop puts apples between 150 g and 250 g on the front shelf, and it runs a sale from 2 to 6 November. You want one class for both ranges: a window with a start and an end, both included. Start without a bound, and see what breaks.", "code": "class Window<T>(val start: T, val endInclusive: T) {\n    operator fun contains(value: T) = start <= value && value <= endInclusive\n    // error: candidate 'fun String.compareTo(...)' is inapplicable\n    //        because of a receiver type mismatch.\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Window<T> {\n    final T start, endInclusive;\n    Window(T start, T endInclusive) { this.start = start; this.endInclusive = endInclusive; }\n\n    boolean contains(T value) {\n        return start.compareTo(value) <= 0 && value.compareTo(endInclusive) <= 0;\n        // error: cannot find symbol: method compareTo(T)\n    }\n}"},
            {"say": "1. Ask for exactly the ability you use. The body only compares, so the bound is `T : Comparable<T>`. Now `<=` resolves to `compareTo`.", "code": "class Window<T : Comparable<T>>(val start: T, val endInclusive: T) {\n    init { require(start <= endInclusive) { \"start $start is after end $endInclusive\" } }\n\n    operator fun contains(value: T): Boolean = start <= value && value <= endInclusive\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Window<T extends Comparable<? super T>> {\n    final T start, endInclusive;\n\n    Window(T start, T endInclusive) {\n        if (start.compareTo(endInclusive) > 0) throw new IllegalArgumentException(\"start is after end\");\n        this.start = start;\n        this.endInclusive = endInclusive;\n    }\n\n    boolean contains(T value) {\n        return start.compareTo(value) <= 0 && value.compareTo(endInclusive) <= 0;\n    }\n}"},
            {"say": "2. Use it with types that already fit the bound. `Int` and `LocalDate` are comparable out of the box. Self-check: why does `Window(1, \"z\")` fail? (Both values must be the same `T`. Kotlin settles on `Int` from the first one, then reports `actual type is 'String', but 'Int' was expected.`)", "code": "val frontShelf = Window(150, 250)\n180 in frontShelf                          // true\n\nval sale = Window(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 11, 6))\nLocalDate.of(2026, 11, 4) in sale          // true", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "var frontShelf = new Window<>(150, 250);\nfrontShelf.contains(180);                     // true\n\nvar sale = new Window<>(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 11, 6));\nsale.contains(LocalDate.of(2026, 11, 4));     // true (needs the ? super T form for LocalDate)"},
            {"say": "3. Make your own type fit. A plain `Int` doesn't say what it measures. A `Grams` value with an explicit order does, and the window needs no change at all.", "code": "data class Grams(val value: Int) : Comparable<Grams> {\n    override fun compareTo(other: Grams): Int = value.compareTo(other.value)\n}\n\nval frontShelf = Window(Grams(150), Grams(250))\nGrams(270) in frontShelf                   // false", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "record Grams(int value) implements Comparable<Grams> {\n    public int compareTo(Grams other) { return Integer.compare(value, other.value); }\n}\n\nvar frontShelf = new Window<>(new Grams(150), new Grams(250));\nfrontShelf.contains(new Grams(270));   // false"}
        ]
    },
    "lab": {
        "title": "Bound your type parameters: maxOfAll, Window, shortestLabel, coalesce",
        "minutes": 12,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l02/Bounds.kt",
            f"{LAB}/main/kotlin/workbench/generics/l02/Window.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l02.*'",
        "steps": [
            "Run the tests once. All nine fail.",
            "In `Bounds.kt`, write `maxOfAll` with a loop and `>`. Then try deleting `: Comparable<T>` from its signature to see the error, and put it back.",
            "In `Window.kt`, add the `require` in `init`, then write `contains`, `clamp` and `overlaps` using only `<`, `<=`, `>` and `>=`. The tests use it for weights in grams, for days and for plain numbers.",
            "Write `shortestLabel`. It uses `.length` from one bound and `<` from the other.",
            "Write `coalesce`. Notice that the test assigns its result to a plain `String`.",
            "Run the tests until all nine pass."
        ],
        "hints": [
            "`require(condition) { \"message\" }` throws `IllegalArgumentException` when the condition is false.",
            "Two windows do NOT overlap when one ends before the other starts: `endInclusive < other.start || other.endInclusive < start`. Negate that.",
            "In `coalesce`, `if (value != null) return value` smart-casts `value` from `T?` to `T`."
        ],
        "done_when": "All nine tests in `BoundsTest` pass."
    },
    "drill": {
        "title": "Write three bounded signatures from memory",
        "minutes": 4,
        "prompt": "Close this page. Write only the signatures (no bodies): (1) a function `largest` that returns the biggest item of a `List<T>` for any comparable `T`; (2) a function `trimAndSort` that takes a `List<T>` where `T` is both a `CharSequence` and comparable to itself; (3) a class `Registry` with a key type and a value type, neither of which may be nullable. Then write (1) and (2) in Java.",
        "answer": {
            "lang": "kotlin",
            "src": "fun <T : Comparable<T>> largest(items: List<T>): T = TODO()\n\nfun <T> trimAndSort(items: List<T>): List<T> where T : CharSequence, T : Comparable<T> = TODO()\n\nclass Registry<K : Any, V : Any>\n\n// Java:\n// static <T extends Comparable<T>> T largest(List<T> items)\n// static <T extends CharSequence & Comparable<T>> List<T> trimAndSort(List<T> items)",
            "alt": {"lang": "java", "title": "Signatures.java", "src": "static <T extends Comparable<T>> T largest(List<T> items) { ... }\n\nstatic <T extends CharSequence & Comparable<T>> List<T> trimAndSort(List<T> items) { ... }\n\n// Java has no non-null bound: the closest is a run-time check in the constructor or in put()\nclass Registry<K, V> {\n    void put(K key, V value) {\n        Objects.requireNonNull(key);\n        Objects.requireNonNull(value);\n    }\n}"}
        }
    },
    "recap": [
        "An unbounded `T` has the bound `Any?`: you can use `toString`, `hashCode` and `==`, and callers may pass `null`.",
        "An upper bound such as `T : Fruit` or `T : Comparable<T>` shuts some callers out and lets the body use what the bound promises, such as `.grams` or `<`. Two apples in still give an `Apple` out.",
        "More than one bound goes in a `where` clause. At most one bound can be a class. Java writes `<T extends A & B>` with the class first.",
        "`T : Any` rules out nullable type arguments, so `T?` in your API can only mean \"absent\". Java type parameters always allow null.",
        "The limit: a bound says what one `T` may be. It says nothing about whether a generic type of a subtype, such as a crate of apples, may stand in for a crate of fruit."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "`fun <T : Comparable<T>> maxOf2(a: T, b: T): T`. Which call does NOT compile?",
            "options": [
                "`maxOf2(3, 7)`",
                "`maxOf2(\"Gala\", \"Fuji\")`",
                "`maxOf2(LocalDate.now(), LocalDate.MIN)`",
                "`maxOf2(Apple(\"Gala\", 180), Apple(\"Fuji\", 150))` where `Apple` is a plain data class"
            ],
            "answer": 3,
            "why": "`Int`, `String` and `LocalDate` are all comparable. A plain data class is not, so the compiler reports `actual type is 'Apple', but 'Comparable<uninferred T ...>' was expected`. Data classes get `equals` and `hashCode`, not an order: should apples compare by weight or by name?"
        },
        {
            "q": "Which signature lets a function call both `x.length` and `x < y` on two `T` values?",
            "options": [
                "`fun <T : CharSequence, Comparable<T>> f(x: T, y: T)`",
                "`fun <T> f(x: T, y: T) where T : CharSequence, T : Comparable<T>`",
                "`fun <T : CharSequence & Comparable<T>> f(x: T, y: T)`",
                "`fun <T : Any> f(x: T, y: T)`"
            ],
            "answer": 1,
            "why": "Kotlin allows one bound inside the angle brackets. A second bound for the same `T` goes into a `where` clause. The first option declares a second type parameter called `Comparable`, which is not what you meant, and `&` is Java's spelling, not Kotlin's."
        },
        {
            "q": "A teammate writes `class Cache<K, V> { fun get(key: K): V? }`. Another teammate creates `Cache<String, LocalDate?>` to record when each crate was last checked, storing `null` for \"never\". What problem appears?",
            "options": [
                "`get` returns `null` both for a missing key and for a stored null, so callers can't tell them apart",
                "It does not compile: `V?` is not allowed when `V` is nullable",
                "Every `get` throws a NullPointerException",
                "None: `V?` and `LocalDate?` cancel out"
            ],
            "answer": 0,
            "why": "With the default bound `Any?`, `V` may itself be nullable, and `V?` adds nothing. Declaring `class Cache<K : Any, V : Any>` makes `Cache<String, LocalDate?>` a compile error, so `null` from `get` always means \"missing\"."
        },
        {
            "q": "Java: which bound declaration compiles?",
            "options": [
                "`<T extends Comparable<T> & Number>`",
                "`<T extends Number, Comparable<T>>` with the same meaning",
                "`<T extends Number & Comparable<T>>`",
                "`<T : Number & Comparable<T>>`"
            ],
            "answer": 2,
            "why": "In Java, the class bound must come first, and the interfaces follow after `&`. Putting `Number` second gives `interface expected here`. The comma form declares a second type parameter, and the colon is Kotlin syntax."
        },
        {
            "q": "From \"Generics from zero\": what does `val probe: Int = mapOf(\"apple\" to 40, \"mango\" to 250L)` make the compiler print?",
            "options": [
                "expected 'Int', actual 'Map<String, Int>'",
                "expected 'Int', actual 'Map<String, Long>'",
                "expected 'Int', actual 'Map<String, Number>'",
                "expected 'Int', actual 'Map<String, Any>'"
            ],
            "answer": 1,
            "why": "Assigning to a wrong type is the trick for printing an inferred type. Here the compiler makes the literal `40` a `Long` so that both values share one type. With two values that really differ, such as `1` and `2.5`, you would get an intersection type instead.",
            "from": "gen-01"
        }
    ],
    "flashcards": [
        {"front": "What is the default upper bound of a Kotlin type parameter?", "back": "`Any?`. So an unbounded `T` accepts nullable types, and `fun <T> f(x: T)` can be called with `null`."},
        {"front": "Why write `fun <T : Fruit> heavier(a: T, b: T): T` instead of taking two `Fruit` parameters?", "back": "Two apples in give an `Apple` out. With plain `Fruit` parameters, you'd get a `Fruit` back and need a cast."},
        {"front": "How do you say \"T can be compared with another T\"?", "back": "`<T : Comparable<T>>` in Kotlin, `<T extends Comparable<T>>` in Java."},
        {"front": "How do you give one type parameter two bounds in Kotlin?", "back": "A `where` clause: `fun <T> f(x: T) where T : CharSequence, T : Comparable<T>`."},
        {"front": "Why does `where T : Number, T : Exception` fail?", "back": "`only one of the upper bounds can be a class.` A JVM type has one superclass; the other bounds must be interfaces."},
        {"front": "What does `class Cache<K : Any, V : Any>` buy you?", "back": "Neither type argument can be nullable, so `get(): V?` returning null always means \"no entry\"."},
        {"front": "In Java's `<T extends A & B>`, which must come first?", "back": "The class, if there is one. Interfaces follow after `&`. Otherwise javac says `interface expected here`."}
    ],
    "terms": [
        {"term": "Bound", "plain": "A limit on a type parameter that promises more about `T`, so the body can do more with it."},
        {"term": "Upper bound", "plain": "\"T must be this type or a subtype of it\", written `T : Fruit` or `T : Comparable<T>`."},
        {"term": "Default bound", "plain": "`Any?`, the bound a Kotlin type parameter has when you write none."},
        {"term": "where clause", "plain": "The place for extra bounds on a type parameter: `where T : CharSequence, T : Comparable<T>`."},
        {"term": "Recursive bound", "plain": "A bound that mentions the parameter itself, like `T : Comparable<T>`: T can be compared with another T."},
        {"term": "T : Any", "plain": "A bound that rules out nullable type arguments."},
        {"term": "Multiple bounds (Java)", "plain": "Java's `<T extends A & B>`; the class, if any, must come first."}
    ],
    "explain_back": {
        "prompt": "In your own words: what does adding a bound to a type parameter take away from callers, and what does it give the function body? Use `T : Comparable<T>` and `T : Any` as your two examples.",
        "answer": "A bound narrows the set of types a caller may pick. In exchange, the function body can rely on more. With no bound, `T` might be anything, including a nullable type, so the body can only use what `Any?` has. With `T : Comparable<T>`, callers can no longer pass types that have no order, like a plain `Apple` data class, but the body can now use `<` and `>`. With `T : Any`, callers can no longer pick a nullable type, but the body and the API get a guarantee: a `T` is never null, so a `T?` return can only mean \"absent\". In both cases the compiler enforces the deal at every call, like a sign on a box that turns the wrong items away."
    },
    "deeper": {
        "minutes": 8,
        "body": "Why does javap show Kotlin's `fun <T : Comparable<T>> maxOf2(a: T, b: T)` as `<T extends Comparable<? super T>> T maxOf2(T, T)`? Because Kotlin declares `Comparable<in T>`, and when Kotlin writes a Java signature for a parameter of an `in` type, it adds `? super`. That is also why Kotlin accepts `LocalDate`, which is a `Comparable<ChronoLocalDate>` and not a `Comparable<LocalDate>`.\n\nJava's own `Collections.max` shows how messy this gets without declaration-site variance:\n\n```java\npublic static <T extends Object & Comparable<? super T>> T max(Collection<? extends T> coll)\n```\n\n```kotlin\nfun <T : Comparable<T>> Iterable<T>.max(): T\n```\n\nThe `Object &` part is there for backward compatibility: it keeps the erased signature returning `Object`, as it did before Java 5. The `? super T` lets a `List<LocalDate>` through. The `? extends T` lets a collection of a subtype through. Kotlin's version gets the same flexibility from `in` and `out`, declared once on `Comparable` and `Iterable`. Lessons 4 to 6 of this track build up to reading that Java signature with ease.\n\nOne more bound rule: a type parameter bounded by another type parameter can't have extra bounds. `fun <T, U> f(u: U) where U : T, U : Comparable<U>` gives `type parameter cannot have any other bounds if it's bounded by another type parameter.`"
    },
    "sources": [
        {"title": "Generics: upper bounds and where clauses (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Bounded type parameters (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/bounded.html"},
        {"title": "Null safety (Kotlin docs)", "url": "https://kotlinlang.org/docs/null-safety.html"}
    ]
}

out = ROOT / "content/lessons/gen-02.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
