import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l11.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l11/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l11/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


FIG = ('<svg viewBox="0 0 700 300" role="img" aria-label="A board of delivery bells, a typed event bus. Deliveries of Apple and Lemon flow out into the board. '
       'The board keys its adapters by KClass of out Fruit. Listeners take items in: an apple listener, a listener for every Fruit, and a lemon listener. '
       'The listener for every Fruit can listen under Apple::class because function parameters are in.">'
       '<text class="t-s t-m" x="100" y="24" text-anchor="middle">producers: deliveries go out</text>'
       '<text class="t-s t-m" x="592" y="24" text-anchor="middle">consumers: items go in</text>'
       + box(15, 60, 170, "Apple(\"Gala\", 180)", "box-a")
       + box(15, 140, 170, "Lemon(\"Eureka\", 120)", "box-a")
       + '<line class="ln-a" x1="187" y1="79" x2="228" y2="100" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="187" y1="159" x2="228" y2="140" marker-end="url(#arr)"/>'
         '<rect class="box" x="230" y="40" width="240" height="160" rx="8"/>'
         '<text class="t" x="350" y="66" text-anchor="middle">BellBoard</text>'
         '<text class="t-s t-code" x="350" y="98" text-anchor="middle">KClass&lt;out Fruit&gt;</text>'
         '<text class="t-s t-m" x="350" y="120" text-anchor="middle">maps to a list of adapters</text>'
         '<text class="t-s t-code" x="350" y="152" text-anchor="middle">type.safeCast(item)?.let(l)</text>'
         '<text class="t-s t-m" x="350" y="176" text-anchor="middle">check, then hand over</text>'
       + '<line class="ln-a" x1="472" y1="90" x2="496" y2="59" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="472" y1="120" x2="496" y2="119" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="472" y1="150" x2="496" y2="179" marker-end="url(#arr)"/>'
       + box(500, 40, 185, "(Apple) -&gt; Unit", "box-b")
       + box(500, 100, 185, "(Fruit) -&gt; Unit", "box-b")
       + box(500, 160, 185, "(Lemon) -&gt; Unit", "box-b")
       + '<text class="t-s t-m" x="350" y="240" text-anchor="middle">The (Fruit) -&gt; Unit listener fits under Apple::class: function parameters are in.</text>'
         '<text class="t-s t-m" x="350" y="262" text-anchor="middle">The keys come from item::class, which is a KClass&lt;out Fruit&gt;.</text>'
         '</svg>')

OPENING = """Picture the back door of the fruit shop on a busy day. Deliveries arrive from morning to night, and a board of bells hangs by the door, one bell for each kind of delivery. When apples arrive, the apple bell rings, and everyone who asked to hear it comes: the sign-writer, who writes a card for each variety, and the stock-keeper, who counts every fruit of any kind.

Wiring up that board is where people slip. The board keeps one list of listeners per bell, and every list must accept any fruit. The sign-writer only understands apples. Force the sign-writer onto that list with a cast, and it compiles. It even works, until the day a lemon reaches the sign-writer.

Advanced generics: recursive bounds, T & Any, @UnsafeVariance ended with that question, and this last lesson of the track answers it with everything since lesson 1. In this lesson, we'll build four small designs: a result that is either a problem or a fruit, a storeroom with a read-only display case, the board of bells, and a container whose keys carry their value's type. Before we start, make a guess, and keep it in mind."""

S1 = """The first design comes from the back door too. Each delivery note is read and checked, and the check has two possible outcomes: a problem ("no weight written") or a good value. A result type that holds exactly one of two kinds of value is often called `Either`, with a `Left` for the problem and a `Right` for the value:

```java
// Java 21: a sealed interface and records. Java has no Nothing, so Left carries an R it never uses.
sealed interface Either<L, R> permits Left, Right {}
record Left<L, R>(L value) implements Either<L, R> {}
record Right<L, R>(R value) implements Either<L, R> {}

static <L, R, R2> Either<L, R2> map(Either<L, R> e, Function<? super R, ? extends R2> f) {
    return switch (e) {
        case Left<L, R> l -> new Left<>(l.value());          // must rebuild: a Left<L, R> is not a Left<L, R2>
        case Right<L, R> r -> new Right<>(f.apply(r.value()));
    };
}
```

```kotlin
sealed interface Either<out L, out R> {
    data class Left<out L>(val value: L) : Either<L, Nothing>
    data class Right<out R>(val value: R) : Either<Nothing, R>
}

fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> = when (this) {
    is Either.Left -> this                                 // no rebuild needed
    is Either.Right -> Either.Right(f(value))
}
```

Two tools from this track meet here. An `Either` only hands its values out, so both parameters are `out` (lesson 4): a dispenser with one of two things inside. And `Left` fills the unused side with `Nothing`, lesson 10's box that can never hold anything and so fits every label. Put together, a `Left<String>` is an `Either<String, Nothing>`. Because `Nothing` is a subtype of every type and `R` is `out`, it is also an `Either<String, R2>` for any `R2`. That's why `is Either.Left -> this` type-checks: the same problem slip is a valid result for any kind of success. Java has neither tool, so its `map` must build a new `Left` every time.

The interface is **sealed**, which means all its subclasses are declared in the same file. So the compiler knows `Left` and `Right` are the only cases, and a `when` that forgets one is an error. A caller can `map` the value, fall back with `getOrElse`, or handle both cases. Unlike an exception, the problem is part of the signature, where every reader sees it.

Covariance makes results combine, too: an `Either<String, Long>` is an `Either<Any, Number>`, so a function that reports any problem and any number accepts it. Remove the `out`s and almost everything breaks at once, including the `Left` and `Right` declarations themselves: `Type parameter 'L' is declared as 'out' but occurs in 'invariant' position in type 'Either<L (of class Left<out L>), Nothing>'.` A supertype is a position too. The demo counts six errors.

**With `out` and `Nothing`, one `Left` fits every success type. Return it as it is.**

`Either` only hands values out. The next design hands values out from a type that also takes them in."""

S2 = """The second design is the storeroom itself. The shop keeps records of its suppliers (the farms that deliver) and its crates, each with an id. A storeroom object can save an item, find one by id and list them all. Because it both takes items in (`save`) and hands them out (`findAll`), it must be invariant, like the crate of apples in lesson 3. That hurts the readers. A stock check that wants to list items of *any* kind can't accept a `Storeroom<Supplier, Long>` as a `Storeroom<Item<Long>, Long>`.

The fix is to put the reading half behind glass, as an interface of its own: lesson 3's display case.

```java
interface DisplayCase<T> { List<T> findAll(); }                     // Java: invariant, so...

static void printAll(DisplayCase<? extends Item<?>> display) {      // ...each reader writes ? extends
    for (Item<?> item : display.findAll()) System.out.println("item " + item.getId());
}
```

```kotlin
interface Item<ID : Comparable<ID>> { val id: ID }

interface DisplayCase<out T> { fun findAll(): List<T> }           // only hands T out

interface Storeroom<T : Item<ID>, ID : Comparable<ID>> : DisplayCase<T> {
    fun save(item: T): T                                           // takes T in: invariant
    fun findById(id: ID): T?
}

fun printAll(display: DisplayCase<Item<*>>) {
    for (item in display.findAll()) println("item ${item.id}")
}
```

Now `printAll` accepts the suppliers and the crates, because each storeroom *is* a `DisplayCase` of its item type, and the display case is covariant. Unlike lesson 10's display case, this one has no secret slot. The full storeroom is still invariant, and the compiler still refuses `val anyItem: Storeroom<Item<Long>, Long> = suppliers` with `Initializer type mismatch`. Nothing was weakened. The safe half simply got its own name.

The bounds are lesson 2's tools. `ID : Comparable<ID>` lets the lab's storeroom keep its items in a `TreeMap`, a map that keeps its keys in sorted order. `T : Item<ID>` ties each item to the type of its id: a `Long` for suppliers, and a `String` such as `"c-1"` for crates. The Kotlin docs give the same advice for any type that both reads and writes: split the interface instead of casting. You'll also hear this called interface segregation, here done by variance.

Notice where the variance came from. You didn't decide that `DisplayCase` is covariant. You looked at its members, saw that each one only returns `T`, and the compiler agreed. That's the habit this track has built: read the positions, and let them tell you.

**When a type both reads and writes `T`, give the reading half its own `out` interface.**

Values flow out of the display case. In the third design, values flow out of one side and into the other."""

S3 = """The third design is the board from the opening, and the figure shows it. In code it's an **event bus**: an object that passes each event, a message that something happened, to everyone who asked to hear that kind of event. Here each delivery is the event. Deliveries flow *out* of the back door, and listeners take them *in*. That's lessons 4 and 5 in one class:

```java
final class Bells {
    private final List<Consumer<Fruit>> adapters = new ArrayList<>();

    <E extends Fruit> void listen(Class<E> type, Consumer<? super E> listener) {   // Consumer Super
        adapters.add(item -> {
            if (type.isInstance(item)) listener.accept(type.cast(item));
        });
    }
}
```

```kotlin
class BellBoard {
    private val bells = HashMap<KClass<out Fruit>, MutableList<(Fruit) -> Unit>>()

    fun <E : Fruit> listen(type: KClass<E>, listener: (E) -> Unit) {
        bells.getOrPut(type) { mutableListOf() }
            .add { item -> type.safeCast(item)?.let(listener) }     // the adapter
    }

    fun ring(item: Fruit) { bells[item::class]?.forEach { it(item) } }
}
```

Every piece has a reason. The map's keys are `KClass<out Fruit>`, because that's the type of `item::class`, lesson 9's note asked of a value. The listener can't go into the list as it is, and the compiler explains why: `Argument type mismatch: actual type is '(E (of fun <E : Fruit> listen)) -> Unit', but '(Fruit) -> Unit' was expected.` A listener that only takes apples can't be handed a lemon, because function parameters are `in`. So the board stores an **adapter**, a small wrapper that turns one function type into another. It takes any `Fruit`, checks it with `safeCast`, and passes on only an `E`, like a doorman at each bell who reads every delivery note before calling anyone. The same `in` helps at the call site: the stock-keeper, a `(Fruit) -> Unit`, can listen under `Apple::class`.

The shortcut from the opening is to cast the listener instead, `.add(listener as (Fruit) -> Unit)` under `@Suppress("UNCHECKED_CAST")`. It compiles, and erasure makes the cast itself succeed. Then the first lemon that reaches that list throws `ClassCastException` from inside the sign-writer's own code, far from the line that caused it. The adapter costs one line and turns the wrong delivery into nothing at all.

For Kotlin callers, add the reified wrapper from lesson 8, with one new word:

```java
// Java callers pass the class to the Java board: bells.listen(Apple.class, a -> writeSign(a));
// There is no Java equivalent of the reified, noinline wrapper.
```

```kotlin
inline fun <reified E : Fruit> listen(noinline listener: (E) -> Unit) = listen(E::class, listener)

board.listen<Apple> { writeSign(it) }
```

A lambda passed to an inline function is normally inlined too, so it never exists as an object. This one gets stored in the map, so it must stay an object, and `noinline` says so.

One limit to know: this board rings by the exact class. A listener under `Fruit::class` never hears anything, because no delivery's run-time class is the interface itself. The "Go deeper" part shows how to walk the supertypes when you need that.

**Store a narrow listener behind a checking adapter, never behind a cast.**

The last design keeps many kinds of values in one place, and it's the most delicate of the four."""

S4 = """The last design is a container for values of many types: the facts the shop keeps about one order, such as the varieties chosen, the weight of each piece and the total weight. Lesson 9's card index used the type as the whole key. Here the key is a small object that carries a name *and* the full type of its value, like a tab on a card that says both "weights" and "a list of grams":

```java
record Key<T>(String name, Type type) {                         // Type from a super type token
    static <T> Key<T> of(String name, TypeRef<T> ref) { return new Key<>(name, ref.type); }
}
static final Key<List<String>> VARIETIES = Key.of("varieties", new TypeRef<List<String>>() {});

<T> void set(Key<T> key, T value) { values.put(key, value); }
@SuppressWarnings("unchecked")
<T> T get(Key<T> key) { return (T) values.get(key); }          // safe: only set puts values in
```

```kotlin
data class Key<T>(val name: String, val type: KType)
inline fun <reified T> key(name: String) = Key<T>(name, typeOf<T>())

val VARIETIES = key<List<String>>("varieties")

operator fun <T> set(key: Key<T>, value: T) { values[key] = value }
@Suppress("UNCHECKED_CAST")
operator fun <T> get(key: Key<T>): T? = values[key] as T?     // safe: only set puts values in

val varieties: List<String>? = attributes[VARIETIES]            // no cast, no type argument at the call site
```

The key's type parameter does the typing. `attributes[VARIETIES]` is a `List<String>?`, with no cast at the call site, and `attributes[VARIETIES] = 42` is a compile error: `Argument type mismatch: actual type is 'Int', but 'List<String>' was expected.` The `KType` inside the key makes `key<List<Int>>("weights")` and `key<Int>("weights")` different keys. So when two helpers both pick the name "weights", one for the weight of each piece and one for the total, the two values don't land in the same slot.

`Key<T>` is invariant on purpose, and this is the last variance decision of the track. Declare it `out T`, and a `Key<List<String>>` becomes a `Key<Any>`. Then `attributes[VARIETIES] = 42` would compile, with `T` inferred as `Any`, and the next read of the varieties throws `ClassCastException: class java.lang.Integer cannot be cast to class java.util.List`. The demo's `LeakyKey` does exactly that. A key is used to write as well as to read, so it can't be a producer, however few members it has. The one unchecked cast in `get` stays safe only while that holds. It's **safe by construction**: the only way in is `set(key: Key<T>, value: T)`, and the key can't pretend to be another type.

**A key that decides what may be written must be invariant.**

This is also a good place to stop adding generics. Four designs, two commented casts, one deliberately invariant key: if a design needs much more than that, a plainer one with a sealed class and a `when` is usually easier for the next person to read. And know the limit of all four. They check types, not meaning: the compiler will happily file a weight of minus 50 grams under exactly the right key."""

CLOSING = """We started at the back door, with a board of bells and a sign-writer who only understands apples. From lesson 1's labeled box on, the whole track went into four designs: an `Either` whose `Left` fits every success type, a display case that lets readers in and keeps writers out, a board that keeps narrow listeners behind a checking adapter, and keys that carry their value's type and stay invariant.

Search your code for `@Suppress("UNCHECKED_CAST")`. Each one should sit somewhere private, with a comment that says why it's safe by construction.

Next, we'll start a new track, Functional programming in Kotlin, with pure functions, the idea everything else builds on. How can a function have more inputs than parameters?"""

L = {
    "id": "gen-11",
    "title": "Generics workshop: a type-safe container and event bus",
    "minutes": 40,
    "goal": "By the end you can build four small designs that use the whole track: an `Either<out L, out R>` that leans on `Nothing`, a storeroom with a covariant display-case view, a typed board of delivery bells that stores listeners behind adapters, and a container of typed keys that carry a `KType`. For each type parameter, you can say why it is `out`, `in` or invariant.",
    "opening": OPENING,
    "warmup": {
        "q": "`sealed interface Either<out L, out R>` with `data class Left<out L>(val value: L) : Either<L, Nothing>`. In `fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2>`, can the `Left` branch simply return `this`?",
        "options": [
            "No: `this` is an `Either<L, R>`, and the function must return an `Either<L, R2>`",
            "Yes: a `Left<L>` is an `Either<L, Nothing>`, which is an `Either<L, R2>` because `Nothing` is a subtype of `R2` and `R` is `out`",
            "Only with an unchecked cast to `Either<L, R2>`",
            "Only if `R2` is the same type as `R`"
        ],
        "answer": 1,
        "why": "After the smart cast, `this` is a `Left<L>`, whose declared supertype is `Either<L, Nothing>`. With `out R`, `Nothing` below `R2` means `Either<L, Nothing>` is below `Either<L, R2>`. So one `Left` object is a valid result for any success type. Java, with no `Nothing`, has to build a new `Left` in that branch."
    },
    "sections": [
        {
            "h": "A problem or a fruit: Either, with two out parameters and Nothing",
            "body": S1,
            "try": {
                "title": "Fold, mapLeft, then remove out",
                "minutes": 4,
                "steps": [
                    "Run `EitherDemo` and `EitherDemoJava`. Compare how `mapLeft` handles the `Right` branch in each.",
                    "In `EitherDemo.kt`, remove both `out`s from `sealed interface Either` (keep the ones on `Left` and `Right`). Predict how many lines break, then run.",
                    "Put the `out`s back."
                ],
                "code": kdemo("EitherDemo", "EitherDemoJava"),
                "expect": "Both print `grams: 180`, the problem in capitals (`Left(value=NOT A NUMBER: A HANDFUL)` in Kotlin, `Left[value=NOT A NUMBER: A HANDFUL]` for the Java record) and `wider = Right(value=180)`. Kotlin's `mapLeft` returns `this` for a `Right`; Java builds a new `Right`. Without the `out`s you get six errors: `Left` and `Right` themselves (`Type parameter 'L' is declared as 'out' but occurs in 'invariant' position ...`), `mapLeft`'s `when`, two in `parseGrams`, and `Initializer type mismatch: expected 'Either<Any, Number>', actual 'Either<String, Long>'.`"
            },
            "refs": [
                {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
            ]
        },
        {
            "h": "Reading behind glass: a covariant display case on an invariant storeroom",
            "body": S2,
            "try": {
                "title": "List any storeroom through its display case",
                "minutes": 3,
                "steps": [
                    "Run `StoreroomDemo` (or `StoreroomDemoJava`). One `printAll` reads suppliers, crates and a writable storeroom.",
                    "Uncomment the wrong move in each file. Predict, then run.",
                    "Remove `out` from `DisplayCase` in the Kotlin file. Which calls to `printAll` still compile?"
                ],
                "code": kdemo("StoreroomDemo", "StoreroomDemoJava"),
                "expect": "Both print the items `2`, `7` and `c-1`; Kotlin also prints `item 9` from the writable storeroom. The wrong moves fail with `Initializer type mismatch: expected 'Storeroom<Item<Long>, Long>', actual 'Storeroom<Supplier, Long>'.` (the full storeroom is invariant) and, in Java, `incompatible types: DisplayCase<Supplier> cannot be converted to DisplayCase<Item<?>>` (no wildcard on the variable). Without `out`, none of the three `printAll` calls compile."
            }
        },
        {
            "h": "The board of bells: deliveries flow out, listeners take them in",
            "body": S3,
            "figure": {"svg": FIG, "caption": "Deliveries are produced, listeners consume them. The board keys its adapters by the item's class and checks each item before handing it over."},
            "try": {
                "title": "Route deliveries to typed listeners",
                "minutes": 4,
                "steps": [
                    "Run `BellBoardDemo` (or `BellBoardDemoJava`). The stock-keeper takes every `Fruit` but listens under `Apple::class`.",
                    "Inside `Bells.listen`, uncomment wrong move 1 and comment out the adapter line below it. Read the error.",
                    "Restore it, then uncomment wrong move 2 in `main`. Why is a listener for one kind refused for the supertype?"
                ],
                "code": kdemo("BellBoardDemo", "BellBoardDemoJava"),
                "expect": "Both print `sign for Gala, 180 g`, `stock: one more Gala` and `lemon tray: Eureka`. Wrong move 1: `Argument type mismatch: actual type is '(E (of fun <E : Fruit> listen)) -> Unit', but '(Fruit) -> Unit' was expected.` Wrong move 2: `Argument type mismatch: actual type is '(Apple) -> Unit', but '(Fruit) -> Unit' was expected.`, because listening under `Fruit::class` would hand a lemon to a listener that only takes apples."
            }
        },
        {
            "h": "Keys that carry their value's type: one container, many types, no casts",
            "body": S4,
            "try": {
                "title": "Store typed attributes, then break the key",
                "minutes": 4,
                "steps": [
                    "Run `TypedKeysDemo` and `TypedKeysDemoJava`. Neither call site has a cast.",
                    "Read `LeakyKey` in the Kotlin file: the same key with `out T`. Find the line where the bad value goes in, and the line where it fails.",
                    "Uncomment the wrong move in each file. The invariant key stops at compile time what the leaky key let through."
                ],
                "code": kdemo("TypedKeysDemo", "TypedKeysDemoJava"),
                "expect": "Both print `varieties = [Gala, Fuji], total = 330 g`. Kotlin then prints `ClassCastException: class java.lang.Integer cannot be cast to class java.util.List`: `leaky[leakyVarieties] = 42` compiled because `out T` let `T` be inferred as `Any`, and the read failed later. The wrong move fails with `Argument type mismatch: actual type is 'Int', but 'List<String>' was expected.` in Kotlin, and `method set in class Attributes cannot be applied to given types` in Java."
            },
            "refs": [
                {"title": "Reflection: typeOf (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "The board of bells in Java and Kotlin",
        "java": {
            "title": "BellBoard.java",
            "src": "import java.util.ArrayList;\nimport java.util.HashMap;\nimport java.util.List;\nimport java.util.Map;\nimport java.util.function.Consumer;\n\nfinal class BellBoard {\n    private final Map<Class<? extends Fruit>, List<Consumer<Fruit>>> bells = new HashMap<>();\n\n    // Consumer<? super E>: a listener for E or for any supertype of E\n    <E extends Fruit> void listen(Class<E> type, Consumer<? super E> listener) {\n        bells.computeIfAbsent(type, t -> new ArrayList<>()).add(item -> {\n            if (type.isInstance(item)) listener.accept(type.cast(item));   // the adapter\n        });\n    }\n\n    int ring(Fruit item) {\n        List<Consumer<Fruit>> listeners = bells.getOrDefault(item.getClass(), List.of());\n        listeners.forEach(l -> l.accept(item));\n        return listeners.size();\n    }\n}\n\n// board.listen(Apple.class, a -> writeSign(a));"
        },
        "kotlin": {
            "title": "BellBoard.kt",
            "src": "class BellBoard {\n    private val bells = HashMap<KClass<out Fruit>, MutableList<(Fruit) -> Unit>>()\n\n    // (E) -> Unit is already Function1<in E, ...>: a listener for any supertype of E fits\n    fun <E : Fruit> listen(type: KClass<E>, listener: (E) -> Unit) {\n        bells.getOrPut(type) { mutableListOf() }\n            .add { item -> type.safeCast(item)?.let(listener) }           // the adapter\n    }\n\n    inline fun <reified E : Fruit> listen(noinline listener: (E) -> Unit) = listen(E::class, listener)\n\n    fun ring(item: Fruit): Int {\n        val listeners = bells[item::class] ?: return 0\n        for (l in listeners) l(item)\n        return listeners.size\n    }\n}\n\n// board.listen<Apple> { writeSign(it) }"
        },
        "note": "The design is the same in both languages: keys from the item's run-time class, listeners stored behind an adapter that checks the class and casts, and a listener parameter that accepts supertypes. Where Java writes the variance at each use (`Class<? extends Fruit>` keys, `Consumer<? super E>` listeners), Kotlin gets it from declarations: `item::class` is already a `KClass<out Fruit>`, and a function type is already `in` on its parameter, so `(E) -> Unit` needs no projection. Kotlin also adds the reified wrapper, which needs `noinline` because the lambda is stored. Java callers can reach the `KClass` version only through `JvmClassMappingKt.getKotlinClass(Apple.class)`, so a board meant for Java code should also offer a `Class<E>` overload."
    },
    "worked": {
        "title": "Receive a delivery note through all four designs",
        "steps": [
            {"say": "A delivery note arrives as a map of text fields, read from a paper form. 1. Parse it into an `Either` instead of throwing, so the caller decides what a bad note means.",
             "code": "fun parseDelivery(note: Map<*, *>): Either<String, Fruit> {\n    val name = note[\"name\"] as? String ?: return Either.Left(\"missing name\")\n    val grams = (note[\"grams\"] as? Number)?.toInt() ?: return Either.Left(\"missing weight\")\n    return when (note[\"kind\"]) {\n        \"apple\" -> Either.Right(Apple(name, grams))\n        \"lemon\" -> Either.Right(Lemon(name, grams))\n        else -> Either.Left(\"unknown kind ${note[\"kind\"]}\")\n    }\n}",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static Either<String, Fruit> parseDelivery(Map<?, ?> note) {\n    if (!(note.get(\"name\") instanceof String name)) return new Left<>(\"missing name\");\n    if (!(note.get(\"grams\") instanceof Number n)) return new Left<>(\"missing weight\");\n    int grams = n.intValue();\n    Object kind = note.get(\"kind\");\n    if (\"apple\".equals(kind)) return new Right<>(new Apple(name, grams));\n    if (\"lemon\".equals(kind)) return new Right<>(new Lemon(name, grams));\n    return new Left<>(\"unknown kind \" + kind);\n}"},
            {"say": "2. Ring the bell for each good delivery. 3. Record each problem in the day's typed attributes. Self-check before reading the comment: why can `Either.Right(Apple(name, grams))` be returned where `Either<String, Fruit>` is expected? (`Right<Apple>` is an `Either<Nothing, Apple>`, and both parameters are `out`.)",
             "code": "val LAST_PROBLEM = key<String>(\"delivery.lastProblem\")\n\nfun receive(note: Map<*, *>, board: BellBoard, today: Attributes): Int =\n    when (val parsed = parseDelivery(note)) {\n        is Either.Right -> board.ring(parsed.value)          // the item flows out to the listeners\n        is Either.Left -> { today[LAST_PROBLEM] = parsed.value; 0 }\n    }",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static final Key<String> LAST_PROBLEM = Key.of(\"delivery.lastProblem\", new TypeRef<String>() {});\n\nstatic int receive(Map<?, ?> note, BellBoard board, Attributes today) {\n    return switch (parseDelivery(note)) {\n        case Right<String, Fruit> r -> board.ring(r.value());\n        case Left<String, Fruit> l -> { today.set(LAST_PROBLEM, l.value()); yield 0; }\n    };\n}"},
            {"say": "4. Wire the listeners once, when the shop opens. The stock-keeper is a `(Fruit) -> Unit` and listens under both kinds; the sign-writer only understands apples. A nightly report lists the suppliers through the covariant `DisplayCase<Item<*>>`. Every type parameter in this flow has the variance its role demands, and the only casts are the two that are safe by construction: `safeCast` in the board's adapter, and the unchecked cast inside `Attributes.get`.",
             "code": "val stockCount: (Fruit) -> Unit = { stock.add(it.name, it.grams) }\nboard.listen(Apple::class, stockCount)\nboard.listen(Lemon::class, stockCount)\nboard.listen<Apple> { signs.write(it.name) }\n\nreceive(mapOf(\"kind\" to \"apple\", \"name\" to \"Gala\", \"grams\" to 180), board, today)   // 2 listeners ran\nreceive(mapOf(\"kind\" to \"apple\", \"name\" to \"Fuji\"), board, today)                    // today[LAST_PROBLEM] == \"missing weight\"",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "Consumer<Fruit> stockCount = f -> stock.add(f.getName(), f.getGrams());\nboard.listen(Apple.class, stockCount);\nboard.listen(Lemon.class, stockCount);\nboard.listen(Apple.class, a -> signs.write(a.getName()));\n\nreceive(Map.of(\"kind\", \"apple\", \"name\", \"Gala\", \"grams\", 180), board, today);   // 2 listeners ran\nreceive(Map.of(\"kind\", \"apple\", \"name\", \"Fuji\"), board, today);                  // LAST_PROBLEM is \"missing weight\""}
        ]
    },
    "lab": {
        "title": "Build Either, a storeroom, a board of bells and typed keys",
        "minutes": 16,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l11/Either.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Storeroom.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/BellBoard.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Attributes.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Callers.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l11.*'",
        "steps": [
            "Run the tests. All thirteen fail. Work through the files in order; each part has its own tests.",
            "`Either.kt` (a TODO in each of two functions): write `map` with `is Either.Left -> this`, and `getOrElse`.",
            "`Storeroom.kt` (TODOs 1 to 3): add `out` to `DisplayCase`. Back `InMemoryStoreroom` with a `java.util.TreeMap<ID, T>`. Write `saveAll` and `describeAll`.",
            "`BellBoard.kt` (TODOs 4 to 6): store an adapter in `listen`, make the one-argument `listen` inline with a `reified E` and a `noinline` listener, and write `ring` so it returns the number of listeners that ran.",
            "`Attributes.kt` (TODOs 7 and 8): make `key` inline and reified with `typeOf<T>()`, then write `set`, `get`, `getOrDefault` and `remove`. Use `key in values` for `getOrDefault`, so a stored `null` is not mistaken for a missing key.",
            "Run until all thirteen pass. Then remove `out` from `DisplayCase` once more and watch which test turns red."
        ],
        "hints": [
            "A `TreeMap` works as `byId[item.id] = item`, and `byId.values.toList()` is already in id order.",
            "The adapter is `bells.getOrPut(type) { mutableListOf() }.add { item -> type.safeCast(item)?.let(listener) }`. `safeCast` needs `import kotlin.reflect.safeCast`.",
            "`ring`: `val listeners = bells[item::class] ?: return 0`, then call each one and return `listeners.size`.",
            "Each unchecked cast in `Attributes` needs `@Suppress(\"UNCHECKED_CAST\")`. Write one comment that says why it's safe: only `set(key: Key<T>, value: T)` puts values in, and `Key` is invariant."
        ],
        "done_when": "All thirteen tests in `WorkshopTest` pass."
    },
    "drill": {
        "title": "Write Either and map from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `Either` with `Left` and `Right` in Kotlin, with the variance and the `Nothing` that let `map` return `this` for a `Left`. Write `map`. Then write the Java version with a sealed interface and records, and point at the line where Java has to build a new object.",
        "answer": {
            "lang": "kotlin",
            "src": "sealed interface Either<out L, out R> {\n    data class Left<out L>(val value: L) : Either<L, Nothing>\n    data class Right<out R>(val value: R) : Either<Nothing, R>\n}\n\nfun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> = when (this) {\n    is Either.Left -> this                      // Either<L, Nothing> is an Either<L, R2>\n    is Either.Right -> Either.Right(f(value))\n}",
            "alt": {"lang": "java", "title": "Either.java", "src": "sealed interface Either<L, R> permits Left, Right {}\nrecord Left<L, R>(L value) implements Either<L, R> {}\nrecord Right<L, R>(R value) implements Either<L, R> {}\n\nstatic <L, R, R2> Either<L, R2> map(Either<L, R> e, Function<? super R, ? extends R2> f) {\n    return switch (e) {\n        case Left<L, R> l -> new Left<>(l.value());          // here: no Nothing, so a new Left\n        case Right<L, R> r -> new Right<>(f.apply(r.value()));\n    };\n}"}
        }
    },
    "recap": [
        "`Either<out L, out R>` with `Left : Either<L, Nothing>` lets one `Left` stand for every success type, so `map` can return `this`. Java must rebuild it.",
        "When a type both reads and writes `T`, give the reading half its own `out T` interface, the display case. Readers get covariance; the full storeroom stays invariant and safe.",
        "On a board of bells, deliveries are produced and listeners consume. Keys are `KClass<out Fruit>` from `item::class`, listeners sit behind a `safeCast` adapter rather than a cast, and a reified wrapper that stores its lambda needs `noinline`.",
        "A typed key carries its value's type (`Key<T>` with a `KType` inside), so reads need no cast and same-named keys of different types don't collide.",
        "A key is used to write, so it must be invariant. With `out T`, a wrong value goes in and fails later as a `ClassCastException`.",
        "The limit: these designs check types, not meaning, and the board rings only for the exact class. When a design needs much more, a sealed class and a `when` are often plainer."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "Which interface can safely be declared with `out T`?",
            "options": [
                "`interface Storeroom<T> { fun save(item: T): T }`",
                "`interface Slot<T> { var current: T }`",
                "`interface DisplayCase<T> { fun findAll(): List<T> }`",
                "`interface Key<T> { val name: String }`, used as `set(key: Key<T>, value: T)`"
            ],
            "answer": 2,
            "why": "`DisplayCase` only hands `T` out. `save` takes a `T`, and a `var` is both read and written, so those must be invariant. The key is the subtle one: it has no `T` member at all, so `out T` would compile, but it is used to choose what may be written, and `out` would let `set(key, 42)` through."
        },
        {
            "q": "On the board of bells, why can't `listen` simply do `bells[type]!!.add(listener)` with `listener: (E) -> Unit` and a list of `(Fruit) -> Unit`?",
            "options": [
                "Because lambdas can't be stored in a map",
                "Because `(E) -> Unit` is not a `(Fruit) -> Unit`: function parameters are `in`, and a listener for apples can't take a lemon",
                "Because `E` is erased, so the list can't hold it",
                "It can; the adapter is only there for speed"
            ],
            "answer": 1,
            "why": "A `(Fruit) -> Unit` must accept every fruit. A listener that only takes `Apple` doesn't, so the compiler refuses the `add`. The adapter takes any fruit and passes on only those that `safeCast` to `E`. The other direction works: a `(Fruit) -> Unit` listener is an `(Apple) -> Unit`."
        },
        {
            "q": "Why does the reified `listen` need `noinline` on its listener parameter?",
            "options": [
                "Because reified functions can't take lambdas",
                "Because Java callers need it",
                "Because the listener is stored in the map, so it must exist as an object instead of being inlined",
                "Because `noinline` makes the type parameter reified"
            ],
            "answer": 2,
            "why": "Lambdas passed to an inline function are inlined too, so they don't exist as values. A lambda you store, return or pass on to a function that isn't inline must stay an object, which `noinline` asks for. It has nothing to do with `reified`, which is about the type parameter."
        },
        {
            "q": "`data class Key<T>(val name: String, val type: KType)`. Why include the `KType` when the key already has a name?",
            "options": [
                "So that `key<List<Int>>(\"weights\")` and `key<Int>(\"weights\")` are different keys and can't collide",
                "Because a data class needs at least two properties",
                "So that `get` can cast without an unchecked warning",
                "Because a `KType` makes the key covariant"
            ],
            "answer": 0,
            "why": "With the name alone, two keys with the same name and different value types would share one slot, and reading one would return the other's value. The `KType` from `typeOf<T>()` makes them unequal. The cast in `get` is still unchecked; it is safe because only `set` puts values in."
        },
        {
            "q": "From \"Star projection: when you don't know the type\": a helper reports the size of any in-memory list, a `MutableList<Apple>`, a `MutableList<String>` or anything else, and may clear it. Which parameter type fits best?",
            "options": [
                "`MutableList<Any?>`",
                "`MutableList<in Any>`",
                "`MutableList<Fruit>`",
                "`MutableList<*>`"
            ],
            "answer": 3,
            "why": "The helper neither reads typed elements nor writes any, so a star projection says exactly that and accepts every mutable list, while still allowing `size` and `clear()`. `MutableList<Any?>` accepts only lists whose element type is exactly `Any?`, and `in Any` accepts only lists of `Any` or `Any?`. `MutableList<Fruit>` turns away both the apple list and the string list.",
            "from": "gen-07"
        }
    ],
    "flashcards": [
        {"front": "Why is `Left` declared `Left<out L>(val value: L) : Either<L, Nothing>`?", "back": "So one `Left` fits `Either<L, R>` for every `R`: `Nothing` is a subtype of every type, and `Either` is `out` in `R`."},
        {"front": "A storeroom both saves and returns `T`. How do you let read-only code accept a storeroom of any item?", "back": "Split out `interface DisplayCase<out T> { fun findAll(): List<T> }` and have the full `Storeroom` extend it. Readers take `DisplayCase<Item<*>>`."},
        {"front": "What type do the keys of a class-keyed board of bells have, and why?", "back": "`KClass<out Fruit>`, because `item::class` on a `Fruit` has exactly that type."},
        {"front": "How do you store an `(Apple) -> Unit` in a list of `(Fruit) -> Unit`?", "back": "Wrap it: `{ item -> Apple::class.safeCast(item)?.let(listener) }`. The adapter takes any fruit and passes on only an `Apple`."},
        {"front": "When does a lambda parameter of an inline function need `noinline`?", "back": "When the function stores it, returns it or passes it to code that isn't inline, as `listen` does with its map of listeners."},
        {"front": "Why must a typed `Key<T>` be invariant?", "back": "It decides what may be written. With `out T`, a `Key<List<String>>` could act as a `Key<Any>`, `set(key, 42)` would compile, and the next read would throw `ClassCastException`."}
    ],
    "terms": [
        {"term": "Either", "plain": "A result that is a problem (`Left`) or a value (`Right`), declared `out` in both."},
        {"term": "Interface segregation by variance", "plain": "Splitting a type's reading half into its own covariant interface, so readers get flexibility the full type can't have."},
        {"term": "Event bus", "plain": "An object that passes each event, a message that something happened, to everyone who asked for that kind of event."},
        {"term": "Adapter", "plain": "A small wrapper that turns one function type into another, here by checking the item's class first."},
        {"term": "noinline", "plain": "Marks a lambda parameter of an inline function that must stay an object, because it is stored."},
        {"term": "Typed key", "plain": "A key object that carries the type of its value, so a container can return that type without casts."},
        {"term": "Safe by construction", "plain": "An unchecked cast that can't fail, because a private rule guarantees what was stored."}
    ],
    "explain_back": {
        "prompt": "A teammate reviews the lab's `BellBoard` and asks two things: why the board wraps every listener in a lambda instead of storing it directly, and why the stock-keeper, typed `(Fruit) -> Unit`, can listen under `Apple::class`. Explain both with the producer and consumer picture.",
        "answer": "Deliveries are produced at the back door and consumed by listeners, so a listener's type is `in` on its parameter. That gives both answers. A listener typed `(Apple) -> Unit` can only consume apples, so it is not a `(Fruit) -> Unit`, which must consume any fruit. The board keeps one list of `(Fruit) -> Unit` per class, so it can't store the apple listener as it is. It stores an adapter instead: a function that takes any `Fruit`, checks it with `Apple::class.safeCast`, and passes it on only if it really is an apple. Casting the listener would compile, but it would fail with a `ClassCastException` inside the listener the first time a lemon arrived. The stock-keeper goes the other way. It consumes every `Fruit`, so it can certainly consume apples. Because the parameter is `in`, a `(Fruit) -> Unit` is an `(Apple) -> Unit`, and `listen(Apple::class, stockCount)` type-checks with `E = Apple`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Each design has a natural next step.\n\nThe board rings only for the item's exact class. To ring a listener under `Fruit::class` for an apple too, `ring` must walk the item's supertypes. Without kotlin-reflect you can do that through Java reflection: `item.javaClass.interfaces` and `item.javaClass.superclass`, converted with `.kotlin`. With kotlin-reflect, `KClass.allSuperclasses` lists them directly. Cache the result per class, since the walk is the same every time.\n\n`Either` gets more useful with `flatMap`, which chains steps that can each fail: `fun <L, R, R2> Either<L, R>.flatMap(f: (R) -> Either<L, R2>): Either<L, R2>`. Its `Left` branch returns `this` for the same reason `map` can. The standard library's own `Result<out T>` is declared `out` too, but its failure side is always a `Throwable`; `Either` lets the problem be a type of your own, such as a `DeliveryProblem`. Libraries such as Arrow ship a full `Either`.\n\nThe storeroom can grow a write-only view as well: `interface Intake<in T> { fun save(item: T) }`. A loader that writes `Supplier`s can then accept an `Intake<Item<Long>>`. With both views, the invariant `Storeroom` is simply the type that is both.\n\nThe typed keys can carry a default: `class Key<T>(val name: String, val type: KType, val default: T)`, with `get` returning `T` instead of `T?`. Keep `Key` invariant when you do: `default` is read, but `set` still writes through the key."
    },
    "sources": [
        {"title": "Generics: variance, in and out (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Reflection (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html"},
        {"title": "Inline functions: noinline (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
        {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"}
    ]
}

out = ROOT / "content/lessons/gen-11.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
