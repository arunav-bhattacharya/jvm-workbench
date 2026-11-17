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
    '<svg viewBox="0 0 690 270" role="img" aria-label="Apple is a subtype of Fruit. Because Dispenser is declared out, Dispenser of Apple is a subtype of Dispenser of Fruit: the arrow keeps its direction. '
    'On the right, a producer: values of T only come out of it, through next, and no member takes a T in.">'
    '<text class="t-s t-m" x="110" y="18" text-anchor="middle">element types</text>'
    '<text class="t-s t-m" x="330" y="18" text-anchor="middle">Dispenser&lt;out T&gt;</text>'
    '<text class="t-s t-m" x="570" y="18" text-anchor="middle">a producer</text>'
    + box(30, 32, 160, "Fruit")
    + box(30, 190, 160, "Apple", "box-a")
    + '<line class="ln-a" x1="110" y1="190" x2="110" y2="72" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="118" y="136">is a</text>'
    + box(235, 32, 190, "Dispenser&lt;Fruit&gt;")
    + box(235, 190, 190, "Dispenser&lt;Apple&gt;", "box-a")
    + '<line class="ln-a" x1="330" y1="190" x2="330" y2="72" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="338" y="128">same direction</text>'
    '<text class="t-s t-a" x="338" y="144">(covariant)</text>'
    '<rect class="box-b" x="470" y="100" width="120" height="44" rx="8"/>'
    '<text class="t t-code" x="530" y="127" text-anchor="middle">Dispenser&lt;T&gt;</text>'
    '<line class="ln-a" x1="590" y1="122" x2="680" y2="122" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="635" y="112" text-anchor="middle">next(): T?</text>'
    '<line class="ln-bad" x1="430" y1="200" x2="490" y2="150"/>'
    '<text class="t-s t-bad" x="560" y="190" text-anchor="middle">no slot: nothing takes a T in</text>'
    '<text class="t-s t-m" x="345" y="258" text-anchor="middle">Every apple that comes out is a fruit, so the substitution can never lie.</text>'
    '</svg>'
)

OPENING = """By the shop door stands an apple dispenser. Pull the lever, and an apple drops out. A customer who wants "some fruit" can use it happily, because every apple that drops out is a fruit. There's no slot to put anything in, and that's the whole point.

In code, the compiler doesn't know that your class has no slot. A `Dispenser<Apple>` won't pass as a `Dispenser<Fruit>` until you tell it, and you tell it with one small word on the declaration. That word is easy to misread as "read-only" or "immutable". It's neither.

Lesson 3 of this track ended with a read-only `List<String>` passing as a `List<Any>`, because the standard library declares `List<out E>`. In this lesson, we'll write that `out` ourselves on a dispenser, and learn where `T` may appear once we do. Then we'll line up Kotlin's `List` with Java's `? extends`, and empty a dispenser to see what `out` doesn't promise. Before we start, make a guess, and keep it in mind."""

S1 = """A **producer** is a type whose values of `T` only ever come out of it. The apple dispenser is one. So are an iterator, a page of search results, and a Java `Supplier`, the JDK interface whose `get()` hands you a value. You call it, and it hands you a `T`. Nothing about it takes a `T` in.

Here is the dispenser in code. `next()` hands out the next item, or `null` when the dispenser is empty. The shop's fruit are the same as before: a `Fruit` interface with a name and a weight, and `Apple` and `Lemon` as data classes that implement it. `gala` and `fuji` below are two apples, of 180 g and 150 g.

Run the substitution test from lesson 3 of this track on the dispenser: ask whether a secret swap could make any allowed call go wrong. Suppose some code expects a dispenser of `Fruit`, and you hand it a dispenser of `Apple`. Every call it can make returns an `Apple`, and every `Apple` is a `Fruit`. Nothing can go wrong. So it's safe to treat a `Dispenser<Apple>` as a `Dispenser<Fruit>`.

The compiler can't see that by itself. Generic types are invariant unless you say otherwise: a `Dispenser<Apple>` and a `Dispenser<Fruit>` are simply unrelated types. In Kotlin, you say otherwise on the declaration, once, with **`out`**. Java has no such keyword, so it says it at every use, with the wildcard `? extends`, Java's way of writing "some subtype of":

```java
interface Dispenser<T> {
    T next();                                       // null when it is empty
}

static int totalGrams(Dispenser<? extends Fruit> dispenser) { ... }

Dispenser<Apple> apples = listDispenser(List.of(gala, fuji));
totalGrams(apples);                                 // fine: the parameter says ? extends
Dispenser<Fruit> plain = apples;                    // error: Dispenser<Apple> cannot be converted to Dispenser<Fruit>
```

```kotlin
interface Dispenser<out T> {
    fun next(): T?                                  // null when it is empty
}

fun totalGrams(dispenser: Dispenser<Fruit>): Int { ... }

val apples: Dispenser<Apple> = ListDispenser(listOf(gala, fuji))
totalGrams(apples)                                  // fine: Dispenser is declared out
val plain: Dispenser<Fruit> = apples                // also fine
```

`ProducerDemo` in the labs runs both versions, and both print `apple total: 330 g`. Remove the `out`, and Kotlin behaves like Java's plain `Dispenser<T>`:

```text
error: argument type mismatch: actual type is 'Dispenser<Apple>', but 'Dispenser<Fruit>' was expected.
```

This property is called **covariance**: the subtype arrow between the element types carries over, in the same direction, to the generic type. `Apple` is a subtype of `Fruit`, so `Dispenser<Apple>` is a subtype of `Dispenser<Fruit>`. The figure shows the two arrows side by side. In short, an apple dispenser is a fruit dispenser, because only apples come out.

Where you write `out` matters. Kotlin's `out` on the declaration is called **declaration-site variance**: you think about it once, when you write `Dispenser`, and every user gets the flexible behavior for free. Java's `? extends` is **use-site variance**: every method that takes a dispenser must remember to write it, and the ones that forget are stricter than they need to be. Lesson 6 of this track shows that Kotlin has the use-site form too, for types that can't be `out` everywhere.

**A type that only hands `T` out can stand in for a dispenser of any supertype. Say so with `out`.**

That raises the obvious question: what stops someone from adding a slot?"""

S2 = """A `Dispenser<out T>` can't also have a `fun refill(item: T)`, and the substitution test shows why. `out` lets you pass `apples`, a `Dispenser<Apple>`, where a `Dispenser<Fruit>` is expected. Through that view, `refill(Lemon("Eureka", 120))` type-checks, because a lemon is a `Fruit`. Now a dispenser that hands out apples holds a lemon, and the next `next()` gives it to code that reads it as an `Apple`: a `ClassCastException`, far from the `refill`. An apple dispenser with a slot for any fruit stops being an apple dispenser. It becomes a surprise machine.

The compiler can't allow both things: treating a `Dispenser<Apple>` as a `Dispenser<Fruit>`, and a parameter of type `T`. With `out`, it keeps the first and rejects the parameter.

`out` is a promise: "values of `T` only come out of this type". The compiler holds you to it by checking every member that outside code can call for a hidden slot. Each place where `T` appears has a **position**:

- A return type is an **out-position**. The value flows out to the caller.
- A parameter type is an **in-position**. The value flows in from the caller.
- A `var` property is both at once, because it has a getter and a setter. That is an **invariant position**.

In a class declared `out T`, `T` may appear only in out-positions. Try to break the rule, and the error names the position:

```java
// Java has no `out` on the declaration, so it checks the same rule where you USE the type:
interface Producer<T> {
    T produce();
    void consume(T item);
}

Producer<? extends Object> view = strings;   // strings is a Producer<String>
Object out = view.produce();     // fine: T comes out
view.consume("Fuji");            // error: String cannot be converted to CAP#1
```

```kotlin
interface Producer<out T> {
    fun produce(): T             // fine
    val latest: T                // fine: a val only has a getter
    fun consume(item: T)         // error: ... declared as 'out' but occurs in 'in' position
    var current: T               // error: ... declared as 'out' but occurs in 'invariant' position
}
```

The full Kotlin message reads `type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of interface Producer<out T>)'.` Java's `CAP#1` is javac's name for "the unknown subtype behind `? extends`". Java can't promise that any `String` fits it, so it refuses the call.

Three special cases come up all the time in Kotlin.

First, constructor parameters are fine, as long as they are plain parameters or `val` properties. `class Holder<out T>(val item: T, plain: T)` compiles. Building the object puts a `T` in, but only once, while the real type is still known. A `var` constructor property is a `var`, so `class Mutable<out T>(var item: T)` fails with the invariant-position error.

Second, private members are exempt. `private var hidden: T` and `private fun replace(t: T)` are allowed, because no outside code can call them with the wrong type. `protected` and `internal` members are checked like public ones.

Third, `private set` is not enough. `var lastServed: T? = null` with `private set` still fails, with `occurs in 'invariant' position`, because the property is still a `var`. The fix is to split it into a `private var` for the class and a public `val` that reads it. The lab makes you do exactly that.

These rules can feel strict on a dispenser you wrote yourself. They feel obvious on a type you have used for years."""

S3 = """You have used a covariant type every day: Kotlin's read-only `List`. Its declaration is `public interface List<out E> : Collection<E>`. That `out` is why a `List<Apple>` goes into any function that takes a `List<Fruit>`, with no ceremony at all:

```java
static int totalWeight(List<? extends Fruit> fruit) {     // the wildcard is the flexible part
    int sum = 0;
    for (Fruit f : fruit) sum += f.getGrams();
    return sum;
}

static int totalWeightInvariant(List<Fruit> fruit) { ... }

List<Apple> apples = new ArrayList<>(List.of(gala, fuji));
totalWeight(apples);              // fine
totalWeightInvariant(apples);     // error: List<Apple> cannot be converted to List<Fruit>
```

```kotlin
fun totalWeight(fruit: List<Fruit>): Int = fruit.sumOf { it.grams }

fun totalWeightMutable(fruit: MutableList<Fruit>): Int = fruit.sumOf { it.grams }

val apples: MutableList<Apple> = mutableListOf(gala, fuji)
totalWeight(apples)               // fine: List is out
totalWeightMutable(apples)        // error: actual type is 'MutableList<Apple>', but 'MutableList<Fruit>' was expected
```

The two snippets line up exactly. Java's `List<? extends Fruit>` and Kotlin's `List<Fruit>` are the same contract: "a list I will only read from, of `Fruit` or any subtype". Java's plain `List<Fruit>` and Kotlin's `MutableList<Fruit>` are the strict, invariant version.

Kotlin keeps this promise when Java code calls it. When a parameter's type is declared `out`, Kotlin writes a `? extends` into the Java signature. `javap`, the JDK tool that prints what a class file contains, shows it for `ListOutDemo`:

```text
public static final int totalWeight(java.util.List<? extends workbench.generics.l04.demo.Fruit>);
public static final int totalWeightMutable(java.util.List<workbench.generics.l04.demo.Fruit>);
```

So Java callers can pass a `List<Apple>` to `totalWeight` too. The demo's Java twin does exactly that, and prints `Kotlin's totalWeight(apples) from Java = 330`. Kotlin leaves the wildcard out in two places. One is return types, so Java callers don't have to handle wildcards. The other is a final type argument, a class like `String` that nothing can extend, where `? extends String` would mean nothing. The lab's tests use this rule to check your `out`: they read the Java signature of your function and look for `? extends`.

So `out` is cheap, checked by the compiler, and visible from Java. What it isn't is a lock."""

S4 = """The most common wrong idea about covariance is that `out` means read-only, or immutable. It doesn't. `out` only limits which **types** can flow in. State can still change.

Here the dispenser picture breaks, in a useful way. A real dispenser has no slot for customers, but the shop assistant can still open it, empty it or refill it. `out` says nothing about any of that.

`Shelf` below keeps its items in a private `MutableList<T>`, which is allowed, because private members are exempt. `take()` removes an item and still only hands a `T` out, the way an assistant can eat the last apple without ever using the slot. `clear()` mentions no `T` at all. Both are legal in an `out` class. Java's `? extends` view behaves the same way, and so does Kotlin's `MutableList<out Fruit>`, the same idea written where the type is used (lesson 6 of this track covers it):

```java
List<Apple> apples = new ArrayList<>(List.of(gala, fuji));
List<? extends Fruit> view = apples;       // "read-only" for the type only

Fruit taken = view.remove(0);              // fine: remove hands a value out
view.clear();                              // fine: no T involved
view.add(new Apple("Pink Lady", 170));     // error: Apple cannot be converted to CAP#1
```

```kotlin
class Shelf<out T>(private val items: MutableList<T>) {
    fun take(): T = items.removeAt(0)      // changes state, only hands T out
    fun clear() = items.clear()            // changes state, no T at all
}

val view: MutableList<out Fruit> = mutableListOf(Apple("Braeburn", 200))
view.removeAt(0)                           // fine
view.clear()                               // fine
view.add(Apple("Pink Lady", 170))          // error: contains out projection which prohibits the use of 'fun add(element: E)'
```

`ImmutableMythDemo` prints `took Gala, 1 left`, then `after clear: 0 left`. The `MutableList<out Fruit>` view loses its only apple too: `view after removeAt: 0 left`. Only the `add` is refused. The Kotlin docs say it plainly: the only thing variance guarantees is type safety, and immutability is a different story.

So when you need a class to be covariant, but it also seems to need a method that takes a `T`, you have three honest options:

1. Move the method out of the class as an **extension function**, a function declared outside the class that you call as if it were a member. `fun <T> Dispenser<T>.nextOr(fallback: T): T` declares its own `T`, so the class's variance rules don't apply. The standard library does this: `plus(element: T)` and `getOrElse` on `List` are extensions.
2. Give the method its own type parameter, such as `fun <R> map(f: (T) -> R): Tray<R>`. Here `T` sits inside the parameter of a function parameter, and two in-positions cancel out. Lesson 5 of this track shows why.
3. Split the type in two: a covariant read interface and an invariant read-write one, like `List` and `MutableList`.

There is also `@UnsafeVariance`, which switches the check off for one position. `List.contains(element: @UnsafeVariance E)` uses it, because `contains` only compares. It's a promise you make by hand, and lesson 10 of this track shows how to break it.

That is also where `out` stops. It only fits a type whose `T` never goes in. Some types are the exact opposite: a bin you only drop things into never hands a `T` back. For those, `out` is the wrong promise, and the next lesson writes the other one."""

CLOSING = """We started at the shop door, with a dispenser that has a lever and no slot. `out T` writes that down: `T` only comes out, so a `Dispenser<Apple>` can stand in for a `Dispenser<Fruit>`, and the compiler checks every member for a hidden slot. It still doesn't stop anyone from emptying the dispenser.

Now look in your own code for a generic class whose type parameter appears only in return types and `val`s, such as a result holder. If it isn't declared `out`, its callers pay with copies and casts.

Next, we'll turn the dispenser around: a bin you only drop things into. If an apple dispenser is a fruit dispenser, which way does the arrow point for a bin?"""

L = {
    "id": "gen-04",
    "title": "Covariance with out: producers",
    "minutes": 35,
    "goal": "By the end you can decide when a generic type is a producer, declare it `out` in Kotlin (or write `? extends` in Java), predict which members the compiler will reject, and fix them without breaking callers.",
    "opening": OPENING,
    "warmup": {
        "q": "`interface Dispenser<T> { fun next(): T }` and `fun total(d: Dispenser<Fruit>)`. You have a `Dispenser<Apple>`. What do you need for `total(apples)` to compile?",
        "options": [
            "Nothing: Apple is a Fruit, so it already compiles",
            "Declare `interface Dispenser<out T>`, because a dispenser only hands T out",
            "Declare `interface Dispenser<in T>`",
            "Cast: `total(apples as Dispenser<Fruit>)` is the normal way"
        ],
        "answer": 1,
        "why": "Generic types are invariant unless you say otherwise, so the call doesn't compile yet. `Dispenser` only produces `T`, so a dispenser of apples can safely act as a dispenser of fruit. `out` tells the compiler that. `in` is for the opposite case, consumers, which lesson 5 of this track covers."
    },
    "sections": [
        {
            "h": "A dispenser only hands values out: covariance with out",
            "body": S1,
            "figure": {"svg": FIG, "caption": "Covariance keeps the arrow: a Dispenser of Apple is a Dispenser of Fruit, because a producer only hands values out."},
            "try": {
                "title": "Take out away and watch the call break",
                "minutes": 4,
                "steps": [
                    "Run `ProducerDemo` (or `ProducerDemoJava`) with the command below. Both print the same total.",
                    "In `ProducerDemo.kt`, remove `out` from both `interface Dispenser<out T>` and `class ListDispenser<out T>`. Predict which line fails, then run.",
                    "Put `out` back. In the Java twin, uncomment the wrong move. Why does Java need `? extends` on `totalGrams`, while Kotlin needs nothing there?"
                ],
                "code": kdemo("ProducerDemo", "ProducerDemoJava"),
                "expect": "Both versions print `apple total: 330 g` and `first from anything: a paper bag`. Without `out`, Kotlin fails on `totalGrams(apples)` with `Argument type mismatch: actual type is 'Dispenser<Apple>', but 'Dispenser<Fruit>' was expected.` The `Dispenser<Any>` line still compiles, because Kotlin infers `T = Any` for that new dispenser. The Java wrong move fails with `incompatible types: Dispenser<Apple> cannot be converted to Dispenser<Fruit>`. Java's `Dispenser<T>` is invariant, so each method that wants flexibility writes `? extends`. Kotlin wrote `out` once, on the interface."
            }
        },
        {
            "h": "Where T may appear: in, out and invariant positions",
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
                "expect": "1 (`fun consume(item: T)`) and 3 (`protected fun keep`) fail with `occurs in 'in' position`. 2 (`var current`) and 4 (`class Mutable<out T>(var item: T)`) fail with `occurs in 'invariant' position`. The demo itself prints `Holder<String> used as Holder<Any>: Gala`. Java reports the rule at the call: `String cannot be converted to CAP#1`, because Java checks variance where you use a type, not where you declare it."
            }
        },
        {
            "h": "List<out E> is the dispenser you already use, and Java's ? extends",
            "body": S3,
            "try": {
                "title": "Call a Kotlin function from Java",
                "minutes": 4,
                "steps": [
                    "Run `ListOutDemo`, then `ListOutDemoJava`. The Java one calls the Kotlin function `totalWeight` with a `List<Apple>`.",
                    "In each file, uncomment the wrong move or moves one at a time, and run.",
                    "From `labs/`, run `javap -p -cp generics/build/classes/kotlin/demo workbench.generics.l04.demo.ListOutDemoKt`. Which parameter got a wildcard?"
                ],
                "code": kdemo("ListOutDemo", "ListOutDemoJava"),
                "expect": "Both print `330`, and Java prints `Kotlin's totalWeight(apples) from Java = 330`. The wrong moves fail with `actual type is 'MutableList<Apple>', but 'MutableList<Fruit>' was expected` in Kotlin, and with `List<Apple> cannot be converted to List<Fruit>` in Java, for both `totalWeightInvariant` and Kotlin's `totalWeightMutable`. `javap` shows `totalWeight(java.util.List<? extends workbench.generics.l04.demo.Fruit>)` and `totalWeightMutable(java.util.List<workbench.generics.l04.demo.Fruit>)`: Kotlin's `out` became Java's `? extends`."
            },
            "refs": [
                {"title": "Variant generics in Java signatures (Calling Kotlin from Java)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"}
            ]
        },
        {
            "h": "out does not mean immutable: the dispenser can still be emptied",
            "body": S4,
            "try": {
                "title": "Empty a covariant shelf",
                "minutes": 3,
                "steps": [
                    "Run `ImmutableMythDemo` (or `ImmutableMythDemoJava`). Before it runs, predict whether `take()` and `clear()` compile in a class declared `out T`.",
                    "Uncomment the `view.add` line and run. Read which rule stops it."
                ],
                "code": kdemo("ImmutableMythDemo", "ImmutableMythDemoJava"),
                "expect": "It prints `took Gala, 1 left`, `after clear: 0 left` and, in Kotlin, `view after removeAt: 0 left`. Variance never stopped the state from changing. The `add` fails with `Receiver type 'MutableList<out Fruit>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.` in Kotlin, and with `Apple cannot be converted to CAP#1` in Java: only the in-position is blocked."
            },
            "refs": [
                {"title": "Declaration-site variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html#declaration-site-variance", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "A producer, declared once in Kotlin, spelled at each use in Java",
        "java": {
            "title": "Dispensers.java",
            "src": "import java.util.List;\n\ninterface Fruit { int grams(); }\nrecord Apple(int grams) implements Fruit {}\n\n// Java can't say \"T only comes out\" on the declaration\ninterface Dispenser<T> {\n    T next();\n}\n\nclass Dispensers {\n    // every method that should accept subtypes must remember ? extends\n    static int total(Dispenser<? extends Fruit> dispenser, int n) {\n        int sum = 0;\n        for (int i = 0; i < n; i++) sum += dispenser.next().grams();\n        return sum;\n    }\n\n    static int sum(List<? extends Fruit> fruit) {\n        return fruit.stream().mapToInt(Fruit::grams).sum();\n    }\n\n    // forget it once, and the method is stricter than it needs to be\n    static int strict(Dispenser<Fruit> dispenser) { return dispenser.next().grams(); }\n}"
        },
        "kotlin": {
            "title": "Dispensers.kt",
            "src": "interface Fruit { val grams: Int }\ndata class Apple(override val grams: Int) : Fruit\n\n// say it once, on the declaration\ninterface Dispenser<out T> {\n    fun next(): T\n}\n\n// plain types in every signature: Dispenser and List are both covariant\nfun total(dispenser: Dispenser<Fruit>, n: Int): Int {\n    var sum = 0\n    repeat(n) { sum += dispenser.next().grams }\n    return sum\n}\n\nfun sum(fruit: List<Fruit>): Int = fruit.sumOf { it.grams }\n\n// the compiler enforces the promise inside Dispenser:\n// fun refill(t: T) would fail with \"declared as 'out' but occurs in 'in' position\""
        },
        "note": "The safety rule is the same in both languages: through a covariant view you may take values out, but not put them in. The difference is who carries the burden. In Java, the type stays invariant, and every method signature has to say `? extends`, so the flexibility depends on each author remembering. In Kotlin, the author of `Dispenser` says `out` once, the compiler checks every member of `Dispenser` against it, and every signature that mentions `Dispenser<Fruit>` is flexible without extra work. When Java calls that Kotlin code, Kotlin writes the `? extends` into the parameter types for it."
    },
    "worked": {
        "title": "Make the shop's Dispenser covariant without losing a feature",
        "steps": [
            {"say": "The shop's weighing report takes a `Dispenser<Fruit>`, but the apple dispenser is a `Dispenser<Apple>`. The dispenser only hands items out, so it should be covariant. Here it is before the change. `lastServed` remembers the last item handed out, and `nextOr` gives a fallback when the dispenser is empty.", "code": "class Dispenser<T>(items: List<T>) {\n    private val queue = ArrayDeque(items)\n    var lastServed: T? = null\n        private set\n\n    fun hasNext(): Boolean = queue.isNotEmpty()\n    fun next(): T { val item = queue.removeFirst(); lastServed = item; return item }\n    fun nextOr(fallback: T): T = if (queue.isEmpty()) fallback else next()\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Dispenser<T> {\n    private final ArrayDeque<T> queue;\n    private T lastServed;\n\n    Dispenser(List<T> items) { queue = new ArrayDeque<>(items); }\n\n    boolean hasNext() { return !queue.isEmpty(); }\n    T next() { T item = queue.removeFirst(); lastServed = item; return item; }\n    T nextOr(T fallback) { return queue.isEmpty() ? fallback : next(); }\n    T lastServed() { return lastServed; }\n}"},
            {"say": "1. Add `out` and read the errors. The compiler names two members. `nextOr` takes a `T`, an in-position. `lastServed` is a `var`, so its type is in an invariant position, even with a private setter. In Java there is nothing to add to the class; each caller writes `Dispenser<? extends Fruit>` instead.", "code": "class Dispenser<out T>(items: List<T>) {\n    // error: ... declared as 'out' but occurs in 'invariant' position in type 'T?'\n    var lastServed: T? = null\n        private set\n    // error: ... declared as 'out' but occurs in 'in' position in type 'T'\n    fun nextOr(fallback: T): T = ...\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "// Java checks at the use site instead:\nstatic List<Fruit> drainAll(Dispenser<? extends Fruit> dispenser) { ... }\n\nDispenser<? extends Fruit> view = appleDispenser;\nFruit f = view.next();                         // fine\nview.nextOr(new Lemon(\"Eureka\", 120));         // error: cannot be converted to CAP#1"},
            {"say": "2. Fix the property by splitting it: a private `var` (exempt) and a public `val` (an out-position). Callers still read `lastServed`, and nobody outside could set it before either.", "code": "private var last: T? = null\nval lastServed: T? get() = last", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "private T last;\nT lastServed() { return last; }   // Java: a getter with no setter"},
            {"say": "3. Fix `nextOr` by moving it out of the class as an extension. The extension declares its own `T`, so the class's `out` doesn't constrain it. Self-check: why is this safe? (At the call `apples.nextOr(x)`, the compiler picks a `T` that fits both the dispenser and `x`. For a `Dispenser<Apple>` and a `Lemon` fallback, that `T` is `Fruit`, and the result is typed `Fruit`.)", "code": "fun <T> Dispenser<T>.nextOr(fallback: T): T = if (hasNext()) next() else fallback\n\nval apples: Dispenser<Apple> = Dispenser(listOf(Apple(\"Gala\", 180)))\nval f: Fruit = apples.nextOr(Lemon(\"Eureka\", 120))   // T = Fruit", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "// Java: a static helper with its own <T> does the same job\nstatic <T> T nextOr(Dispenser<? extends T> dispenser, T fallback) {\n    return dispenser.hasNext() ? dispenser.next() : fallback;\n}\n\nFruit f = nextOr(appleDispenser, new Lemon(\"Eureka\", 120));"}
        ]
    },
    "lab": {
        "title": "Make Dispenser and Tray covariant",
        "minutes": 13,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l04/Dispenser.kt",
            f"{LAB}/main/kotlin/workbench/generics/l04/Tray.kt",
            f"{LAB}/main/kotlin/workbench/generics/l04/Fruit.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l04.*'",
        "steps": [
            "Read `Fruit.kt`: the same `Fruit`, `Apple` and `Lemon` as in this lesson. Then run the tests. Eight of nine fail. Read the two variance failures, which say `expected: \"Dispenser<? extends Fruit>\"` (and the same for `Tray`) `but was: \"Dispenser<Fruit>\"`. The test reads the Java signature of `drainAll`, which only gets a wildcard when `Dispenser` is declared `out`.",
            "In `Dispenser.kt`, add `out` to `Dispenser`'s type parameter. Run the tests, and read the compile error about `lastServed`.",
            "Fix `lastServed` without making it settable from outside: split it into a `private var` and a public `val` with a getter.",
            "Write `hasNext`, `next`, the `nextOr` extension, `drainAll` and `totalGrams`.",
            "`Tray.kt` holds a tray of items with a label card, like the fruit in the shop window. Add `out` to `Tray`. Predict whether `map` still compiles before you run. Then write `map` and `firstOnTray`.",
            "Run the tests until all nine pass."
        ],
        "hints": [
            "`private var last: T? = null` plus `val lastServed: T? get() = last` keeps the read for callers and the write for the class.",
            "`ArrayDeque.removeFirst()` throws `NoSuchElementException` on an empty deque, which is what `next()` should do.",
            "`map` compiles under `out`: in `f: (T) -> R`, `T` is the parameter of a parameter, which counts as an out-position. `Tray(items.map(f), label)` is the whole body."
        ],
        "done_when": "All nine tests in `CovarianceTest` pass."
    },
    "drill": {
        "title": "Write a producer from memory",
        "minutes": 4,
        "prompt": "Close this page. Write a covariant `Dispenser` interface with one method `next()`, a `ListDispenser` class that implements it over a `List`, and a function `totalGrams` that accepts a dispenser of apples as a dispenser of fruit. Write it in Kotlin with `out`, then in Java with `? extends`. Then add a `refill(t: T)` member to the Kotlin interface, and write down the error you expect.",
        "answer": {
            "lang": "kotlin",
            "src": "interface Dispenser<out T> {\n    fun next(): T?\n}\n\nclass ListDispenser<out T>(items: List<T>) : Dispenser<T> {\n    private val it = items.iterator()\n    override fun next(): T? = if (it.hasNext()) it.next() else null\n}\n\nfun totalGrams(dispenser: Dispenser<Fruit>): Int {\n    var sum = 0\n    while (true) sum += (dispenser.next() ?: break).grams\n    return sum\n}\n\n// fun refill(t: T) inside Dispenser:\n// error: type parameter 'T' is declared as 'out' but occurs in 'in' position",
            "alt": {"lang": "java", "title": "Dispenser.java", "src": "interface Dispenser<T> {\n    T next();   // null when it is empty\n}\n\nstatic <T> Dispenser<T> listDispenser(List<T> items) {\n    Iterator<T> it = items.iterator();\n    return () -> it.hasNext() ? it.next() : null;\n}\n\n// the flexibility lives in the parameter, not in Dispenser\nstatic int totalGrams(Dispenser<? extends Fruit> dispenser) {\n    int sum = 0;\n    for (Fruit f = dispenser.next(); f != null; f = dispenser.next()) sum += f.grams();\n    return sum;\n}"}
        }
    },
    "recap": [
        "A producer only hands values of `T` out. A producer of a subtype can safely stand in for a producer of the supertype, the way an apple dispenser is a fruit dispenser: that is covariance.",
        "Kotlin declares it once, with `out T` on the declaration. Java writes `? extends T` at every use.",
        "In an `out` class, `T` may appear in return types and `val`s, not in parameters or `var`s. Constructor `val`s and private members are fine; `private set` is not enough.",
        "Kotlin's read-only `List<out E>` is why a `List<Apple>` fits a `List<Fruit>` parameter, and Kotlin writes `? extends` into Java parameter signatures for `out` types (except for final type arguments and return types).",
        "The limit: `out` controls which types flow in, not whether state changes, and it only fits types whose `T` never goes in. A type that only takes `T` in needs the opposite promise."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "Which member compiles inside `class Dispenser<out T>`?",
            "options": [
                "`fun refill(item: T)`",
                "`var current: T? = null` with `private set`",
                "`fun peek(): T?`",
                "`protected fun replay(item: T)`"
            ],
            "answer": 2,
            "why": "A return type is an out-position, so `peek(): T?` is fine. `refill` takes a `T` (an in-position), and so does the protected `replay`: only private members are exempt. A `var` is an invariant position, even when its setter is private."
        },
        {
            "q": "Kotlin: `interface Dispenser<out T> { fun next(): T }`, `interface Fruit`, and `fun total(d: Dispenser<Fruit>)`. What does Java see as the parameter type of `total`?",
            "options": [
                "`Dispenser<Fruit>`",
                "`Dispenser<? extends Fruit>`",
                "`Dispenser<? super Fruit>`",
                "The raw type `Dispenser`"
            ],
            "answer": 1,
            "why": "Kotlin turns a parameter of an `out`-declared type into `? extends`, so Java callers can pass a `Dispenser<Apple>` as well. It would skip the wildcard if `Fruit` were a final class, and it never adds one to a return type."
        },
        {
            "q": "`class Shelf<out T>(private val items: MutableList<T>) { fun clear() = items.clear() }`. Does it compile, and what does it say about `out`?",
            "options": [
                "Yes: private members are exempt, and `out` restricts types, not state changes",
                "No: an `out` class can't hold a `MutableList<T>`",
                "No: `clear()` changes state, and `out` means immutable",
                "Yes, but only with `@UnsafeVariance` on `items`"
            ],
            "answer": 0,
            "why": "The `MutableList<T>` is private, so the variance check skips it, and `clear()` doesn't mention `T` at all. `out` guarantees that no wrongly typed value gets in through the public members. It says nothing about whether the object can change: a dispenser can still be emptied."
        },
        {
            "q": "Java: `static int sum(List<? extends Number> xs)` is called with a `List<Integer>`. Which line compiles inside `sum`?",
            "options": [
                "`xs.add(5);`",
                "`Integer first = xs.get(0);`",
                "`xs.set(0, 5);`",
                "`Number first = xs.get(0);`"
            ],
            "answer": 3,
            "why": "Through `? extends Number`, you can read elements as `Number`. You can't add or set an `Integer`, because the list might really be a `List<Double>` (javac: `cannot be converted to CAP#1`). Reading as `Integer` fails for the same reason: the compiler only knows the elements are some kind of `Number`."
        },
        {
            "q": "From \"Subtyping, and why List<String> is not List<Object>\": why does `val x: MutableList<Any> = mutableListOf<String>()` fail, while `val y: List<Any> = mutableListOf<String>()` compiles?",
            "options": [
                "`MutableList` is a different class from `List` at run time",
                "Through `x` you could add an `Int` to a list of strings; `List` has no add, so `y` can only read",
                "Kotlin forbids `Any` as a type argument of mutable types",
                "`mutableListOf` returns a Java type that Kotlin can't widen"
            ],
            "answer": 1,
            "why": "That is the substitution test. A mutable view of the wider type could write a wrong value into the narrower list, like a lemon into a crate of apples. A read-only view can't, which is exactly what `List<out E>` declares. At run time both are the same `java.util.List`.",
            "from": "gen-03"
        }
    ],
    "flashcards": [
        {"front": "What makes a generic type safe to declare `out T`?", "back": "It only hands values of `T` out (return types, `val`s). It never takes a `T` in through a public member."},
        {"front": "With `Dispenser<out T>`, is `Dispenser<Apple>` a subtype of `Dispenser<Fruit>`?", "back": "Yes. Covariance keeps the direction of the subtype arrow."},
        {"front": "Kotlin's `out T` on a declaration corresponds to what in Java?", "back": "`? extends T`, written at each use site, such as `List<? extends Fruit>`."},
        {"front": "Why does `var x: T` fail in a class declared `out T`?", "back": "A `var` has a setter, so `T` is in an invariant position. Even `private set` doesn't help; split it into a private `var` and a public `val`."},
        {"front": "Are constructor parameters allowed in a class declared `out T`?", "back": "Plain parameters and `val` properties: yes. A `var` constructor property: no (invariant position)."},
        {"front": "Does `out` make a type immutable?", "back": "No. It only blocks `T` from flowing in. `MutableList<out T>` still has `clear()` and `removeAt()`."},
        {"front": "How do you keep a method like `nextOr(fallback: T)` on a covariant type?", "back": "Make it an extension function with its own type parameter: `fun <T> Dispenser<T>.nextOr(fallback: T): T`."}
    ],
    "terms": [
        {"term": "Producer", "plain": "A type whose `T` values only come out: dispensers, iterators, read-only lists."},
        {"term": "Covariant", "plain": "`C<Sub>` is a subtype of `C<Super>`: the arrow keeps its direction."},
        {"term": "out", "plain": "Kotlin's keyword on a type parameter: \"T only comes out of this type\"."},
        {"term": "Out-position", "plain": "A place where a value of `T` flows out: return types and `val` types."},
        {"term": "In-position", "plain": "A place where a value of `T` flows in: parameter types."},
        {"term": "Invariant position", "plain": "A place where `T` flows both ways, such as the type of a `var`."},
        {"term": "Declaration-site variance", "plain": "Variance written once on the class (`interface Dispenser<out T>`), as Kotlin does."},
        {"term": "Use-site variance", "plain": "Variance written where the type is used (`Dispenser<? extends Fruit>`), as Java does."}
    ],
    "explain_back": {
        "prompt": "In your own words, explain to a teammate why Kotlin lets a `Tray<Apple>` be passed where a `Tray<Fruit>` is expected once `Tray` is declared `out T`, and what the compiler asks of `Tray` in return.",
        "answer": "`Tray` only hands items out: you read `items` and `map` them, and nothing in its public members takes a `T` in. If I give you a tray of apples where you expected a tray of fruit, every item you read really is a fruit, so nothing can go wrong. `out T` is my promise that this is true, and in return the compiler lets the subtype arrow carry over from `Apple` to `Tray<Apple>`. To keep the promise honest, the compiler rejects any public member where `T` would flow in, like a parameter of type `T` or a `var`: there must be no slot. In Java, the same idea is written at each use as `Tray<? extends Fruit>`."
    },
    "deeper": {
        "minutes": 10,
        "body": "The rule \"parameters are in-positions\" has a twist when the parameter is itself a function. In `fun <R> map(f: (T) -> R)`, `T` is the input of `f`. The tray calls `f` and passes it a `T`, so the value flows out of the tray into the caller's lambda. Two in-positions cancel out. That is why `map` is legal in `Tray<out T>`, while `fun replay(): (T) -> Unit` (a function returned to the caller, which the caller will feed a `T`) is not. Lesson 5 of this track turns this into a sign rule.\n\nKotlin is strict about inferred types too. In `class E<in T> { private fun produce(): T? = null; fun use() = produce() }`, the private `produce` is fine, but the public `use()` has the inferred return type `T?`, and fails. Give public members of variant classes explicit types.\n\nPrivate members get one more rule, called private-to-this. Inside `class C<out T>(private var t: T)`, the method `fun copyFrom(o: C<@UnsafeVariance T>) { t = o.t }` fails with `cannot access 'var t: T': it is private/*private to this*/`. A private member is only exempt when you reach it through `this`, because another instance `o` might really be a `C<Subtype>` seen as a `C<T>`.\n\nFinally, Kotlin leaves the wildcard out of Java signatures when the type argument is final. `fun f(x: List<String>)` is `f(List<String>)` in Java, because nothing can extend `String`. Use `@JvmWildcard` to force one, or `@JvmSuppressWildcards` to drop them."
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
