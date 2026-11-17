import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l06.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l06/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l06/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def cell(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


COLS = [
    (15, "MutableList&lt;Fruit&gt;", "box",
     ("get(i): Fruit", "box-ok"), ("add(x: Fruit)", "box-ok"), "MutableList&lt;Fruit&gt; only"),
    (245, "MutableList&lt;out Fruit&gt;", "box-a",
     ("get(i): Fruit", "box-ok"), ("add: not allowed", "box-bad"), "MutableList&lt;Apple&gt;, &lt;Lemon&gt;"),
    (475, "MutableList&lt;in Fruit&gt;", "box-b",
     ("get(i): Any?", "box-dim"), ("add(x: Fruit)", "box-ok"), "MutableList&lt;Fruit&gt;, &lt;Any&gt;"),
]

FIG = ('<svg viewBox="0 0 700 290" role="img" aria-label="Three views of one invariant MutableList. The plain MutableList of Fruit takes out a Fruit and puts in a Fruit, and accepts only a MutableList of Fruit. '
       'The out-projection takes out a Fruit, refuses add, and accepts crates of Apple or Lemon. The in-projection takes out only Any?, puts in a Fruit, and accepts crates of Fruit or Any.">')
for x, head, hcls, rd, wr, acc in COLS:
    FIG += cell(x, 14, 210, head, hcls)
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="80" text-anchor="middle">take out</text>'
    FIG += cell(x, 86, 210, rd[0], rd[1])
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="146" text-anchor="middle">put in</text>'
    FIG += cell(x, 152, 210, wr[0], wr[1])
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="214" text-anchor="middle">you can pass</text>'
    FIG += f'<text class="t-s t-code" x="{x + 105}" y="236" text-anchor="middle">{acc}</text>'
FIG += ('<text class="t-s t-m" x="350" y="276" text-anchor="middle">A projection closes one side of an invariant crate, for one parameter or variable.</text>'
        '</svg>')

OPENING = """The shop's crates are the busy kind. All day, helpers take apples out and put apples in. That's why, in lesson 3, a crate of apples couldn't pass as a crate of fruit: someone might drop a lemon in.

Today one helper has a single job: weigh the apples in a crate and write down the total. They'll only take apples out, so the clerk at the door gives an instruction: "For this job, treat the crate as take-only." The helper, who has heard about the lemon, nods. The crate itself doesn't change, and the next helper may hear something else.

In code, `MutableList` is that busy crate. It reads and writes, so it can't be declared `out` or `in`, and a function that only reads still turns away a `MutableList<Apple>`. The easy trap is to copy the list, or cast it.

Contravariance with in: consumers ended with one `in` inside a parameter. In this lesson, we'll write take-only and drop-only views like that one and see what each allows. Then we'll line them up with Java's wildcards, and decide when to declare variance on the class instead. Before we start, make a guess, and keep it in mind."""

S1 = """Lessons 4 and 5 of this track put the variance on the class. Variance is the rule that decides whether a `C<Apple>` may stand in for a `C<Fruit>`, that is, whether it's a subtype. A `Dispenser<out T>` only hands values out, and a `Bin<in T>` only takes them in. Many types can't do that. `MutableList<E>` has `get(): E` and `add(element: E)`, and `Array<T>` has `get` and `set`. `T` sits in both positions, so the class must stay **invariant**: a `MutableList<Apple>` is a `MutableList<Fruit>` only if `Apple` and `Fruit` are the same type. Lesson 3 showed what goes wrong when Java arrays pretend otherwise.

The trouble is that one function rarely uses both sides. Here is the copy example from the Kotlin docs, set in the shop. It puts the apples from one array into the shop window, an `Array<Fruit>` that holds two lemons. First, with no variance at all:

```text
fun copyRow(from: Array<Fruit>, to: Array<Fruit>) { for (i in from.indices) to[i] = from[i] }

copyRow(apples, window)        // apples is an Array<Apple>
error: argument type mismatch: actual type is 'Array<Apple>', but 'Array<Fruit>' was expected.
```

Kotlin refuses for a good reason. If `copyRow` could see an `Array<Apple>` as an `Array<Fruit>`, it could write a lemon into it. But `copyRow` never writes to `from`. It only takes items out. So you tell the compiler that, right where the type is used, the way the clerk tells the helper at the door:

```java
// Java arrays are covariant, so a Fruit[] parameter already accepts an Apple[]
static void copyRow(Fruit[] from, Fruit[] to) {
    for (int i = 0; i < from.length; i++) to[i] = from[i];   // the JVM checks each store
}

copyRow(apples, window);           // fine
copyRow(apples, new Lemon[2]);     // compiles, then throws ArrayStoreException
```

```kotlin
fun copyRow(from: Array<out Fruit>, to: Array<Fruit>) {
    for (i in from.indices) to[i] = from[i]   // get() on Array<out Fruit> returns Fruit
}

copyRow(apples, window)                     // fine: Array<Apple> fits Array<out Fruit>
copyRow(apples, arrayOfNulls<Lemon>(2))     // compile error: Array<Lemon?> is not an Array<Fruit>
```

`Array<out Fruit>` is a **type projection**: an `out` or `in` written on one use of a type, instead of on its declaration. You haven't changed `Array`. You've asked for a narrower view of it, for one parameter: "an array of `Fruit` or of some subtype, which this function will only take items out of". Through that view, `get` returns `Fruit`, and `set` is gone:

```text
from[0] = Lemon("Eureka", 95)
error: receiver type 'Array<out Fruit>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.
```

Writing variance where a type is used is called **use-site variance**. Java's wildcards, the `?` in `? extends` and `? super`, are the same idea, and they are the only kind of variance Java has. Arrays are the odd case on the Java side. Java has no wildcards for arrays, because every Java array has been covariant since Java 1.0: an `Apple[]` passes as a `Fruit[]`. Instead, the JVM, the machine that runs the code, checks each store at run time. Java arrays never got the clerk's instruction. They got a guard. `ArrayCopyDemoJava` shows the guard at work: its second copy compiles, then prints `ArrayStoreException: workbench.generics.l06.demo.Apple`.

Kotlin's `Array<out Fruit>` compiles to a plain `Fruit[]`, so the projection costs nothing at run time. The figure shows the three ways to look at one invariant type: the plain view takes out and puts in, the out-projection only takes out, and the in-projection only puts in.

Arrays are rare in everyday Kotlin. The same instruction on a `MutableList` is one you'll write often."""

S2 = """Here is the helper's job from the opening: weigh any mutable crate of fruit. It only takes fruit out, so it asks for a take-only view:

```java
static int totalGrams(List<? extends Fruit> crate) {
    int sum = 0;
    for (Fruit f : crate) sum += f.getGrams();   // reads come out as Fruit
    return sum;
}

totalGrams(apples);    // a List<Apple>
totalGrams(lemons);    // a List<Lemon>
```

```kotlin
fun totalGrams(crate: MutableList<out Fruit>): Int {
    var sum = 0
    for (f in crate) sum += f.grams              // reads come out as Fruit
    return sum
}

totalGrams(apples)     // a MutableList<Apple>
totalGrams(lemons)     // a MutableList<Lemon>
```

`ReadViewDemo` prints `apples: 330 g, lemons: 120 g`.

Read `MutableList<out Fruit>` as "a mutable list of *some* subtype of `Fruit`, and I don't know which". That unknown is why putting anything in is forbidden. The list might be `lemons`, and adding a Gala would put an apple into a crate of lemons. So both compilers refuse every call that takes the element type:

```text
crate.add(Apple("Gala", 180))
Kotlin: receiver type 'MutableList<out Fruit>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.
Java:   incompatible types: Apple cannot be converted to CAP#1
```

Even a perfectly good apple is turned away, from a crate that really holds apples. The clerk isn't being rude. Through a take-only view, nobody can tell a crate of apples from a crate of lemons. `CAP#1` is the name that javac, the Java compiler, gives that unknown: a **captured type**, a placeholder for "the one real element type of this particular list". Kotlin prints it as `CapturedType(out Fruit)`, for example when you try `val a: Apple = crate[0]`. Nothing you can write is known to be a subtype of the placeholder, so nothing goes in.

Here the picture of the clerk's instruction breaks. A helper told "take-only" wouldn't tip the crate out on the floor, but a take-only view allows it. Members that don't take an element still work: `size`, `isEmpty()`, `removeAt(0)` and `clear()` all compile through the view, as lesson 4 showed. The demo removes the Gala through a view and prints `after removeAt through the view: [Fuji]`. A projection limits which types flow in. It doesn't stop the crate from changing.

You need this only for invariant types. Kotlin's read-only `List`, the glass display case of lesson 3, is already declared `List<out E>`. So a plain `List<Fruit>` parameter accepts a `List<Apple>`. Write `List<out Fruit>` anyway, and the compiler warns that the projection is redundant. You'll see that warning in the Try-it.

**A function that only takes items out of a crate should say so. Write `MutableList<out T>`, or take a plain `List`.**

Take-only is one instruction. The clerk has a second one, for helpers who only put things in."""

S3 = """Now flip the direction. This helper tops up a crate with Gala apples, and only ever puts apples in:

```java
static void restock(List<? super Apple> crate, int count) {
    for (int i = 0; i < count; i++) crate.add(new Apple("Gala", 180));
}

restock(apples, 1);      // a List<Apple>
restock(fruit, 2);       // a List<Fruit>
restock(anything, 2);    // a List<Object>
```

```kotlin
fun restock(crate: MutableList<in Apple>, count: Int) {
    repeat(count) { crate.add(Apple("Gala", 180)) }
}

restock(apples, 1)       // a MutableList<Apple>
restock(fruit, 2)        // a MutableList<Fruit>
restock(anything, 2)     // a MutableList<Any>
```

`MutableList<in Apple>` means "a mutable list of `Apple`, or of a type above `Apple` such as `Fruit` or `Any`". Every such list accepts an apple, so `add` is safe. `WriteViewDemo` prints `apples = [Fuji, Gala], fruit = [Eureka, Gala, Gala], anything = [a paper bag, Gala, Gala]`.

Taking things out is the side that gets weaker. The first item might be the Fuji, the Eureka lemon or the paper bag that was already there, and the demo prints all three. So the only thing the compiler can promise about a read is `Any?` (in Java, `Object`):

```text
val firstApple: Apple = crate[0]
Kotlin: initializer type mismatch: expected 'Apple', actual 'CapturedType(in Apple)'.
Java:   incompatible types: CAP#1 cannot be converted to Apple
```

A `MutableList<Lemon>` is turned away at the call, because a crate of lemons can't take an apple: `argument type mismatch: actual type is 'MutableList<Lemon>', but 'MutableList<in Apple>' was expected.`

The JDK, Java's standard library, writes its utility methods this way, and calling them from Kotlin is a good way to learn the mapping. Here are two of them from `java.util.Collections`, with the same contracts written in Kotlin:

```java
public static <T> void fill(List<? super T> list, T obj) { /* ... */ }
public static <T> void copy(List<? super T> dest, List<? extends T> src) { /* ... */ }
```

```kotlin
fun <T> fill(list: MutableList<in T>, obj: T) { /* ... */ }
fun <T> copy(dest: MutableList<in T>, src: List<T>) { /* ... */ }
```

Pass the wrong thing to the real `Collections.copy` from Kotlin, and the error shows how Kotlin reads Java's wildcards:

```text
java.util.Collections.copy(apples, listOf("Gala"))
error: argument type mismatch: actual type is 'List<String>', but '(Mutable)List<out Apple!>!' was expected.
```

Java's `? extends` became `out`. The rule in the Kotlin docs is that `Foo<? extends Bar>` becomes `Foo<out Bar!>!`, and `Foo<? super Bar>` becomes `Foo<in Bar!>!`. The `!` marks a **platform type**, a type from Java whose nullability Kotlin doesn't know. `(Mutable)List` means Kotlin can't tell whether Java will change the list. The mapping works the other way too: a Kotlin parameter `MutableList<in T>` compiles to Java's `List<? super T>`, and this lesson's lab checks exactly that.

So there are two places to write `out` and `in`: on the class, or on one use of it. Which one should you reach for?"""

S4 = """The rule for choosing is short.

If every public member of a class only hands `T` out, declare `out T` on the class. If every member only takes `T` in, declare `in T`. You do it once, and every caller benefits: nobody writes a projection, and a `List<Apple>` simply is a `List<Fruit>`. This is **declaration-site variance**, and it's why Kotlin code has far fewer wildcards than Java code.

If the class both takes and gives `T`, it stays invariant. `MutableList` and `Array` are like that, and so is any crate, cache or store with a `put` and a `get`. Then each function that uses only one side asks for a projection. Here is a crate class of our own, with one function of each kind:

```java
static final class Crate<T> {                  // takes and gives T: invariant
    private final List<T> items = new ArrayList<>();
    void put(T item) { items.add(item); }
    T top() { return items.get(items.size() - 1); }
}

static String topName(Crate<? extends Fruit> crate) { return crate.top().getName(); }
static void putApple(Crate<? super Apple> crate, String name, int grams) {
    crate.put(new Apple(name, grams));
}
```

```kotlin
class Crate<T> {                               // takes and gives T: invariant
    private val items = mutableListOf<T>()
    fun put(item: T) { items += item }
    fun top(): T = items.last()
}

fun topName(crate: Crate<out Fruit>): String = crate.top().name
fun putApple(crate: Crate<in Apple>, name: String, grams: Int) =
    crate.put(Apple(name, grams))
```

`ChooseDemo` puts a Gala into a crate of apples and a Fuji into a mixed crate that holds a lemon, and prints `Gala Fuji`. The plain types still don't mix: `val strict: Crate<Fruit> = apples` fails, because the projections live on the two functions, not on the class.

Java has no declaration-site variance, so every Java class works like `Crate`. Each method that only reads or only writes must remember its wildcard, and the JDK has hundreds of them. Forget one, and your own tests still pass. The first caller with a `List<Apple>` finds out.

The Kotlin compiler also guards the line between the two kinds of variance:

| You write | The compiler says |
|---|---|
| `List<out Fruit>` | warning: `projection is redundant: the corresponding type parameter of 'List<out Fruit>' has the same variance.` |
| `List<in Fruit>` | error: `projection conflicts with variance of the corresponding type parameter of 'List<in Fruit>'. Remove the projection or replace it with '*'.` |
| `fun <out T> onFunction(t: T)` | error: `variance annotations are only allowed for type parameters of classes and interfaces.` |

The last one catches people. Variance says when a `C<A>` can stand in for a `C<B>`. A generic function is not a type that one thing can stand in for, so `out` on its own type parameter has nothing to describe. Put the projection on a parameter's type instead, as `copyInto` does in this lesson's lab.

**Declare variance on the class when every member uses one side. Project at the use site when the class uses both.**

A projection still names a type, though: `out Fruit`, `in Apple`. The `'*'` in the second message is for the case where you can't name one at all, a crate whose label has worn off. That's the next lesson."""

CLOSING = """We started with a busy crate, and a helper told at the door, "for this job, take-only". A projection is that instruction. `MutableList<out Fruit>` lets one function take fruit out and put nothing in, and `MutableList<in Apple>` lets one function put apples in and read back only `Any?`. Java writes the same with `? extends` and `? super`.

Now look in your own code for a parameter typed `MutableList<X>`, or Java `List<X>`, that the function only reads. Each one turns away a crate of a subtype for no reason.

Next, we'll open the box whose label has worn off. What can you do with a list when you don't know its element type at all?"""

L = {
    "id": "gen-06",
    "title": "Use-site variance and type projections",
    "minutes": 35,
    "goal": "By the end you can add `out` or `in` to a single use of an invariant type such as `MutableList` or `Array`, say exactly which calls each projection allows, map it to Java's `? extends` and `? super`, and decide between declaration-site and use-site variance.",
    "opening": OPENING,
    "warmup": {
        "q": "`fun totalGrams(crate: MutableList<Fruit>): Int` only reads the list. You call it with `apples: MutableList<Apple>`. What happens?",
        "options": [
            "It compiles: an `Apple` is a `Fruit`, so a crate of apples is a crate of fruit",
            "It doesn't compile, and the only fix is to copy `apples` into a new `MutableList<Fruit>`",
            "It doesn't compile, but `MutableList<out Fruit>` in the signature fixes it",
            "It compiles, and fails at run time when `totalGrams` reads the first element"
        ],
        "answer": 2,
        "why": "`MutableList` is invariant, because it both reads and writes `E`, so a `MutableList<Apple>` is not a `MutableList<Fruit>`. But `totalGrams` only reads, so it can ask for a take-only view: `MutableList<out Fruit>` accepts a crate of any subtype of `Fruit`. Copying works too, but you don't need it. Option one is the intuition that lesson 3 of this track disproved."
    },
    "sections": [
        {
            "h": "A crate can't pick a side, so you project it for one job",
            "body": S1,
            "figure": {"svg": FIG, "caption": "One invariant MutableList, three views: plain (take out and put in, exact type only), out-projected (take out only), in-projected (put in only)."},
            "try": {
                "title": "Copy apples into the shop window",
                "minutes": 4,
                "steps": [
                    "Run `ArrayCopyDemo` and its twin `ArrayCopyDemoJava`. Compare the last line of the Java output with the Kotlin file's wrong move 3.",
                    "In `ArrayCopyDemo.kt`, predict the error for each of the three wrong moves. Uncomment them one at a time and run.",
                    "Remove `out` from `copyRow`'s first parameter. Which line in `main` breaks now? Put it back."
                ],
                "code": kdemo("ArrayCopyDemo", "ArrayCopyDemoJava"),
                "expect": "Kotlin prints `window: Gala, Fuji`. Java prints `window: [Gala, Fuji]` and then `ArrayStoreException: workbench.generics.l06.demo.Apple`: the copy into a `Lemon[]` compiled and failed at run time. The Kotlin wrong moves fail at compile time: (1) `Initializer type mismatch: expected 'Array<Fruit>', actual 'Array<Apple>'.`, (2) `Receiver type 'Array<out Fruit>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.`, (3) `Argument type mismatch: actual type is 'Array<Lemon?>', but 'Array<Fruit>' was expected.` Without `out`, the call `copyRow(apples, window)` fails with `Argument type mismatch: actual type is 'Array<Apple>', but 'Array<Fruit>' was expected.`"
            },
            "refs": [
                {"title": "Generics: type projections (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "Take-only: an out-projection is a read view, and Java spells it ? extends",
            "body": S2,
            "try": {
                "title": "Weigh two crates, then try to add",
                "minutes": 4,
                "steps": [
                    "Run `ReadViewDemo` (or `ReadViewDemoJava`). One function weighs a crate of apples and a crate of lemons.",
                    "Uncomment the two wrong moves one at a time, predict, run.",
                    "Change `totalGrams`'s parameter to a read-only `List<Fruit>` and run. Then change it to `List<out Fruit>`, and look for a `w:` line in the build output."
                ],
                "code": kdemo("ReadViewDemo", "ReadViewDemoJava"),
                "expect": "Both print `apples: 330 g, lemons: 120 g` and then `[Fuji]`: `removeAt` (Java: `remove(int)`) worked through the read view. `add` fails with `Receiver type 'MutableList<out Fruit>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.` (Java: `incompatible types: Apple cannot be converted to CAP#1`), and the strict assignment with `Initializer type mismatch: expected 'MutableList<Fruit>', actual 'MutableList<Apple>'.` (Java: `List<Apple> cannot be converted to List<Fruit>`). `List<Fruit>` compiles with no projection. `List<out Fruit>` compiles with the warning `Projection is redundant: the corresponding type parameter of 'List<out Fruit>' has the same variance.`"
            }
        },
        {
            "h": "Drop-only: an in-projection is a write view, and Java spells it ? super",
            "body": S3,
            "try": {
                "title": "Restock three crates with one helper",
                "minutes": 4,
                "steps": [
                    "Run `WriteViewDemo` (or `WriteViewDemoJava`). Look at what `first is` prints for each crate.",
                    "Uncomment the two wrong moves one at a time, predict, run.",
                    "Remove `in` from `restock` (Java: change `? super Apple` to `Apple`). Predict how many of the three calls in `main` still compile."
                ],
                "code": kdemo("WriteViewDemo", "WriteViewDemoJava"),
                "expect": "Both print `first is Fuji`, `first is Eureka` and `first is a paper bag`, then `apples = [Fuji, Gala], fruit = [Eureka, Gala, Gala], anything = [a paper bag, Gala, Gala]` and `after Collections.fill: [Fuji, Fuji, Fuji]`. Wrong move 1: `Initializer type mismatch: expected 'Apple', actual 'CapturedType(in Apple)'.` (Java: `CAP#1 cannot be converted to Apple`). Wrong move 2: `Argument type mismatch: actual type is 'MutableList<Lemon>', but 'MutableList<in Apple>' was expected.` (Java: `ArrayList<Lemon> cannot be converted to List<? super Apple>`). Without the projection, only the `apples` call compiles."
            },
            "refs": [
                {"title": "Collections.fill and Collections.copy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Collections.html", "kind": "docs"},
                {"title": "Calling Java from Kotlin: Java generics in Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-interop.html", "kind": "docs"}
            ]
        },
        {
            "h": "Declare variance once when you can, project when you must",
            "body": S4,
            "try": {
                "title": "Take from one crate, put into another",
                "minutes": 4,
                "steps": [
                    "Run `ChooseDemo` (or `ChooseDemoJava`). `topName` only takes from a crate; `putApple` only puts into one.",
                    "Uncomment the wrong move in `main`, predict, run.",
                    "At the bottom of `ChooseDemo.kt`, predict which of lines 1 to 3 is a warning and which are errors. Uncomment them one at a time to check."
                ],
                "code": kdemo("ChooseDemo", "ChooseDemoJava"),
                "expect": "Both print `Gala Fuji`. The wrong move fails with `Initializer type mismatch: expected 'Crate<Fruit>', actual 'Crate<Apple>'.` (Java: `Crate<Apple> cannot be converted to Crate<Fruit>`): the projections are on the functions, not on the class. Line 1 compiles with the `Projection is redundant` warning. Line 2 fails with `Projection conflicts with variance of the corresponding type parameter of 'List<in Fruit>'.` Line 3 fails with `Variance annotations are only allowed for type parameters of classes and interfaces.`"
            }
        }
    ],
    "compare": {
        "title": "The same copy and fill contracts with wildcards and with projections",
        "java": {
            "title": "Transfers.java",
            "src": "import java.util.List;\n\nfinal class Transfers {\n    // dest only takes T, src only gives T: the shape of Collections.copy\n    static <T> int copyInto(List<? extends T> from, List<? super T> to) {\n        for (T x : from) to.add(x);\n        return from.size();\n    }\n\n    // only writes: ? super\n    static <T> void fillWith(List<? super T> target, T value, int count) {\n        for (int i = 0; i < count; i++) target.add(value);\n    }\n\n    // a read-only parameter still needs ? extends in Java\n    static double sumAll(List<? extends Number> amounts) {\n        double sum = 0;\n        for (Number a : amounts) sum += a.doubleValue();\n        return sum;\n    }\n}"
        },
        "kotlin": {
            "title": "Projections.kt",
            "src": "// MutableList is invariant, so each function projects it at the use site\nfun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>): Int {\n    for (x in from) to.add(x)\n    return from.size\n}\n\nfun <T> fillWith(target: MutableList<in T>, value: T, count: Int) {\n    repeat(count) { target.add(value) }\n}\n\n// List is declared List<out E>: no projection needed (one would only earn a warning)\nfun sumAll(amounts: List<Number>): Double {\n    var sum = 0.0\n    for (a in amounts) sum += a.toDouble()\n    return sum\n}"
        },
        "note": "For `MutableList`, the two versions say exactly the same thing. Kotlin's `MutableList<out T>` compiles to Java's `List<? extends T>`, `MutableList<in T>` compiles to `List<? super T>`, and Kotlin shows Java's wildcards back to you as `out` and `in`. The real difference is `sumAll`. Java has no read-only list type with declared variance, so every reading parameter needs `? extends`. Kotlin's `List` carries `out E` on its declaration, so the plain type is already flexible, and a projection on it is redundant. Arrays differ too: Java arrays are covariant, with a run-time check on every store and no wildcards, while Kotlin's `Array<out T>` is a compile-time projection that compiles down to a plain Java array."
    },
    "worked": {
        "title": "Unpack the delivery crate onto the shop floor",
        "steps": [
            {"say": "The morning delivery comes in a crate of apples. A helper moves every apple onto the shop floor, adds up the weight, and empties the delivery crate. The first draft uses plain types. The shop floor is a `MutableList<Fruit>`, because it also holds lemons. Read the error.",
             "code": "fun unpack(delivery: MutableList<Apple>, floor: MutableList<Apple>): Int {\n    var grams = 0\n    for (a in delivery) { floor.add(a); grams += a.grams }\n    delivery.clear()\n    return grams\n}\n\nval delivery = mutableListOf(Apple(\"Gala\", 180), Apple(\"Fuji\", 150))\nval floor = mutableListOf<Fruit>(Lemon(\"Eureka\", 120))\nunpack(delivery, floor)\n// error: argument type mismatch: actual type is 'MutableList<Fruit>',\n//        but 'MutableList<Apple>' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static int unpack(List<Apple> delivery, List<Apple> floor) {\n    int grams = 0;\n    for (Apple a : delivery) { floor.add(a); grams += a.grams(); }\n    delivery.clear();\n    return grams;\n}\n\nList<Apple> delivery = new ArrayList<>(List.of(new Apple(\"Gala\", 180), new Apple(\"Fuji\", 150)));\nList<Fruit> floor = new ArrayList<>(List.of(new Lemon(\"Eureka\", 120)));\nunpack(delivery, floor);\n// error: incompatible types: List<Fruit> cannot be converted to List<Apple>"},
            {"say": "Name what each parameter does with apples. `delivery` gives them to you, and is cleared at the end, which takes no element. `floor` only receives them. So for this one function, `delivery` is a producer and `floor` is a consumer. Both are `MutableList`, which can't be declared `out` or `in`, so the variance goes on the parameters.",
             "code": "", "lang": ""},
            {"say": "Project each parameter. Self-check before reading the comments: why does `delivery.clear()` still compile through an out-projection? (It takes no element, so it can't let a wrong type in.)",
             "code": "fun unpack(delivery: MutableList<out Apple>, floor: MutableList<in Apple>): Int {\n    var grams = 0\n    for (a in delivery) {     // 1. take out: each a is an Apple\n        floor.add(a)          // 2. put in: the floor takes Apple or anything above it\n        grams += a.grams\n    }\n    delivery.clear()          // 3. no element in clear(), so the take-only view allows it\n    return grams\n}\n\nunpack(delivery, floor)       // compiles: 330, and the floor holds the lemon and both apples",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static int unpack(List<? extends Apple> delivery, List<? super Apple> floor) {\n    int grams = 0;\n    for (Apple a : delivery) {   // 1. take out: producer extends\n        floor.add(a);            // 2. put in: consumer super\n        grams += a.grams();\n    }\n    delivery.clear();            // 3. no T in clear()\n    return grams;\n}\n\nunpack(delivery, floor);         // compiles"},
            {"say": "Check it from the caller's side. The floor can now be a `MutableList<Apple>`, a `MutableList<Fruit>` or a `MutableList<Any>`. If you later need `unpack` to read back from the floor (say, to skip a variety that's already on display), that read returns `Any?` through the in-projection, and the compiler tells you so. At that point the parameter really is read and write, and it should go back to the plain type.",
             "code": "", "lang": ""}
        ]
    },
    "lab": {
        "title": "Project MutableList at the use site, then do it in Java",
        "minutes": 12,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l06/Projections.kt",
            f"{LAB}/main/java/workbench/generics/l06/Transfers.java"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l06.*'",
        "steps": [
            "Run the tests. All seven fail. The signature tests print what Java sees today, such as `but was: \"List<T>\"`: no projection means no wildcard.",
            "In `Projections.kt`, give `copyInto`'s `from` an `out` and its `to` an `in`, then write the loop and return the count. The tests copy a `MutableList<Int>` into a `MutableList<Number>`.",
            "Give `fillWith`'s `target` the projection that matches \"only written\", then append `count` copies.",
            "Write `sumAll`. Then change its parameter to `List<out Number>`, run the tests, and find the warning in the output. Put the plain `List<Number>` back.",
            "In `Transfers.java`, change `drainTo`'s parameters to `Queue<? extends T>` and `Collection<? super T>`, then take items from the queue until it is empty.",
            "Run the tests until all seven pass."
        ],
        "hints": [
            "`for (x in from) to.add(x)` type-checks because a read from `MutableList<out T>` gives a `T`, and `MutableList<in T>` accepts a `T`.",
            "`Queue.poll()` returns `null` when the queue is empty: `for (T item = from.poll(); item != null; item = from.poll())`.",
            "Why does `sumAll(ints)` compile before you touch it? Because Kotlin's `List` is declared `List<out E>`. Only `MutableList` needs the projection."
        ],
        "done_when": "All seven tests in `ProjectionsTest` pass."
    },
    "drill": {
        "title": "Write copyInto and its Java signature from memory",
        "minutes": 4,
        "prompt": "Close this page. Write `copyInto(from, to)` for two `MutableList`s in Kotlin, with the projections that let a `MutableList<Apple>` be copied into a `MutableList<Fruit>`. Then write the Java method that Kotlin generates for it (the signature is enough), and the Java version of `fillWith`.",
        "answer": {
            "lang": "kotlin",
            "src": "fun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>): Int {\n    for (x in from) to.add(x)     // reads give T, writes take T\n    return from.size\n}\n\nfun <T> fillWith(target: MutableList<in T>, value: T, count: Int) {\n    repeat(count) { target.add(value) }\n}\n\n// Java sees: public static <T> int copyInto(List<? extends T> from, List<? super T> to)\n//            public static <T> void fillWith(List<? super T> target, T value, int count)",
            "alt": {"lang": "java", "title": "Transfers.java", "src": "static <T> int copyInto(List<? extends T> from, List<? super T> to) {\n    for (T x : from) to.add(x);   // producer extends, consumer super\n    return from.size();\n}\n\nstatic <T> void fillWith(List<? super T> target, T value, int count) {\n    for (int i = 0; i < count; i++) target.add(value);\n}"}
        }
    },
    "recap": [
        "A type that both takes and gives `T` (`MutableList`, `Array`, your own `Crate`) must stay invariant.",
        "A type projection adds `out` or `in` at one use: `MutableList<out Fruit>` is a take-only view, and `MutableList<in Apple>` is a drop-only view.",
        "Through an out-projection, reads give the bound and calls that take `T` are refused. Through an in-projection, `T` values go in and reads give only `Any?`.",
        "Kotlin's `out T` and `in T` projections compile to Java's `? extends T` and `? super T`, and Java's wildcards show up in Kotlin as `out` and `in`.",
        "Declare variance on the class when every member uses one side, and project at the use site when the class uses both. Projecting an already-variant type earns a warning (`List<out T>`) or an error (`List<in T>`).",
        "The limit: a projection still names a type (`out Fruit`, `in Apple`). For a list whose element type you don't know at all, you need the star projection."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "Inside `fun weigh(crate: MutableList<out Fruit>)`, which line compiles?",
            "options": [
                "`crate.add(Apple(\"Gala\", 180))`",
                "`val f: Fruit = crate[0]`",
                "`crate[0] = Lemon(\"Eureka\", 95)`",
                "`val a: Apple = crate[0]`"
            ],
            "answer": 1,
            "why": "Reads through an out-projection come out as the bound, `Fruit`. Both writes are refused, because the real crate might be a `MutableList<Lemon>` or a `MutableList<Apple>`, and the compiler doesn't know which. Reading into `Apple` fails for the same reason: the element is only known to be some `Fruit`."
        },
        {
            "q": "`fun restock(crate: MutableList<in Apple>)`. What is the type of `crate[0]` inside `restock`?",
            "options": [
                "`Apple`",
                "`Fruit`",
                "`Any?`",
                "It doesn't compile: you can't read through an in-projection"
            ],
            "answer": 2,
            "why": "The crate could be a `MutableList<Apple>`, a `MutableList<Fruit>` or a `MutableList<Any?>`, so the only safe promise is `Any?`. Reading is allowed; it just tells you little. `Apple` is the tempting answer, but the crate might hold the paper bag someone put there before."
        },
        {
            "q": "You own `interface Cache<K, V> { fun get(key: K): V?; fun put(key: K, value: V) }`. A report should accept a `Cache<String, Apple>` where it expects fruit of any kind, and it only calls `get`. Which change is right?",
            "options": [
                "Give the report's parameter the type `Cache<String, out Fruit>`",
                "Declare `interface Cache<K, out V>`",
                "Give the report's parameter the type `Cache<String, in Fruit>`",
                "Make the report take a raw `Cache`"
            ],
            "answer": 0,
            "why": "`Cache` both returns and takes `V`, so it must stay invariant: `out V` on the interface fails with `type parameter 'V' is declared as 'out' but occurs in 'in' position`, because of `put`. The report only reads, so it projects at the use site. `Cache<String, out Fruit>` accepts a `Cache<String, Apple>`, and `put` is unavailable through that view. `in Fruit` would make `get` return `Any?`, and Kotlin has no raw types."
        },
        {
            "q": "Java's `Collections.copy` is `<T> void copy(List<? super T> dest, List<? extends T> src)`. How does Kotlin show the `dest` parameter in an error message?",
            "options": [
                "`List<out T>`",
                "`MutableList<T>`",
                "`MutableList<in T!>!`",
                "`List<*>`"
            ],
            "answer": 2,
            "why": "Java wildcards become projections: `? super T` becomes `in T`, and `? extends T` becomes `out T`. The `!` marks platform types, because Kotlin can't know Java's nullability. `List<*>` is how Kotlin shows a Java raw `List`, which is a different thing."
        },
        {
            "q": "From \"Contravariance with in: consumers\": the lab's `highest(items: List<T>, comparator: Comparator<in T>)` needs an `in` on the comparator but nothing on the list. Why?",
            "options": [
                "Because `in` projections are always required on the last parameter",
                "Because `Comparator` is a Kotlin interface declared `out T`",
                "Because the list is only read, and read-only parameters never need variance",
                "Because Kotlin's `List` is declared `out E`, while `java.util.Comparator` is a Java interface that Kotlin must treat as invariant"
            ],
            "answer": 3,
            "why": "Declaration-site variance does the work for `List`. `Comparator` has no declared variance on the JVM, so its flexibility has to be written at the use site, exactly like a projection on `MutableList`. Option three is half right: reading is why `out` fits, but a `MutableList` parameter that is only read still needs `out`.",
            "from": "gen-05"
        }
    ],
    "flashcards": [
        {"front": "What is a type projection?", "back": "Variance written where a type is used, such as `MutableList<out Fruit>` in a parameter. It narrows that one use to taking out or to putting in; the class itself stays invariant."},
        {"front": "Through `MutableList<out Fruit>`, what do `get` and `add` do?", "back": "`get` returns `Fruit`. `add` is refused: the real list might be a `MutableList<Lemon>`."},
        {"front": "Through `MutableList<in Apple>`, what type does `get` return?", "back": "`Any?`. The list may be a `MutableList<Fruit>` or a `MutableList<Any?>`, so nothing more specific is safe."},
        {"front": "Does `clear()` compile on a `MutableList<out Fruit>`?", "back": "Yes. `clear()` takes no element, so a projection doesn't block it. Projections limit types, not changes."},
        {"front": "How does Kotlin show Java's `List<? extends Apple>` and `List<? super Apple>`?", "back": "As `(Mutable)List<out Apple!>!` and `MutableList<in Apple!>!`: `? extends` becomes `out`, and `? super` becomes `in`."},
        {"front": "Declaration-site or use-site variance: how do you choose?", "back": "If every member only produces `T` (or only consumes it), declare `out` (or `in`) on the class. If the class both takes and gives `T`, keep it invariant and project in each function that uses one side."},
        {"front": "What does `fun f(l: List<in String>)` give?", "back": "An error: the projection conflicts with `List`'s declared `out E`. (`List<out String>` gives only a warning: the projection is redundant.)"}
    ],
    "terms": [
        {"term": "Type projection", "plain": "`out` or `in` written on one use of a type, giving a take-only or drop-only view of it."},
        {"term": "Use-site variance", "plain": "Variance written where a type is used, in a parameter or a variable. Java's wildcards and Kotlin's projections."},
        {"term": "Declaration-site variance", "plain": "Variance written once on the class (`interface List<out E>`), so every use gets it."},
        {"term": "Out-projection", "plain": "`C<out T>`: you can take `T` values out; calls that take a `T` are refused."},
        {"term": "In-projection", "plain": "`C<in T>`: you can put `T` values in; reads come back as `Any?`."},
        {"term": "Captured type", "plain": "The compiler's placeholder for the one unknown real type behind a projection or wildcard (`CAP#1`, `CapturedType(out Fruit)`)."},
        {"term": "Platform type", "plain": "A type from Java whose nullability Kotlin doesn't know, shown as `T!` (and `(Mutable)List` for Java lists)."}
    ],
    "explain_back": {
        "prompt": "A teammate's `fun totalGrams(crate: MutableList<Fruit>)` rejects their `MutableList<Apple>`. They propose making `MutableList` covariant \"like List\". Explain why that can't work, and what to write instead.",
        "answer": "`MutableList` has `add(element: E)` as well as `get(): E`, so `E` sits in an in-position and an out-position. If a `MutableList<Apple>` could be used as a `MutableList<Fruit>`, someone could add a lemon to a crate of apples, which is exactly the bug Java arrays have. So the class has to stay invariant. But `totalGrams` only reads, so it can ask for a take-only view in its own signature: `MutableList<out Fruit>`. That accepts a crate of any subtype of `Fruit`, gives back `Fruit` on reads, and refuses `add`. Even simpler, if `totalGrams` never changes the list, it can take a plain read-only `List<Fruit>`, which is already covariant. In Java, the same parameter is `List<? extends Fruit>`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Both compilers turn a wildcard or projection into a fresh **captured type** each time they check an expression: \"the one specific type this list really has\". That's why `CAP#1` shows up in javac messages. Java can also capture a wildcard for a method call, which gives a well-known trick. You can't write `l.set(i, l.get(j))` on a `List<?>`, but you can pass the `List<?>` to a private generic helper `<T> void swapHelper(List<T> l, int i, int j)`, and inside the helper the element type has a name. The JDK chose not to bother. `Collections.swap(List<?> list, int i, int j)` assigns the list to a raw `List` and calls `l.set(i, l.set(j, l.get(i)))` under `@SuppressWarnings`, with a source comment saying that capturing the wildcard would need a supplementary private method.\n\nKotlin captures projected arguments for calls too. Given `fun <T> swap(l: MutableList<T>, i: Int, j: Int)`, the calls `swap(star, 0, 1)` with `star: MutableList<*>` and `swap(view, 0, 1)` with `view: MutableList<out Fruit>` both compile with kotlinc 2.4.21. Inside `swap`, `T` is the captured type, so values read from the list may be written back into the same list. You'll meet `MutableList<*>` properly in the next lesson.\n\nArrays have one more twist. Because Java arrays carry no wildcards, Kotlin compiles `Array<out Fruit>` and `Array<Fruit>` both to `Fruit[]`, and `Array<in Fruit>` to `Object[]`. From Java, those differences are invisible; the projection exists only for the Kotlin compiler. The door opens the other way too. Kotlin shows a Java `Object[]` parameter as `Array<(out) Any!>!`, so you may pass an `Array<String>` to it, as Java code could. That brings Java's covariance back: `java.util.Arrays.fill(names, 42)` with `names: Array<String>` compiles in Kotlin and throws `ArrayStoreException: java.lang.Integer` at run time."
    },
    "sources": [
        {"title": "Generics: type projections and use-site variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Calling Java from Kotlin: Java generics and Java arrays (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-interop.html"},
        {"title": "Calling Kotlin from Java: variant generics (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
        {"title": "java.util.Collections (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Collections.html"}
    ]
}

out = ROOT / "content/lessons/gen-06.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
