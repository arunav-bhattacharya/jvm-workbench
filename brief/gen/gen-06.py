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
    (15, "MutableList&lt;Number&gt;", "box",
     ("get(i): Number", "box-ok"), ("add(x: Number)", "box-ok"), "MutableList&lt;Number&gt; only"),
    (245, "MutableList&lt;out Number&gt;", "box-a",
     ("get(i): Number", "box-ok"), ("add: not allowed", "box-bad"), "MutableList&lt;Int&gt;, &lt;Double&gt;"),
    (475, "MutableList&lt;in Number&gt;", "box-b",
     ("get(i): Any?", "box-dim"), ("add(x: Number)", "box-ok"), "MutableList&lt;Number&gt;, &lt;Any&gt;"),
]

FIG = ('<svg viewBox="0 0 700 290" role="img" aria-label="Three views of one invariant MutableList. Plain MutableList of Number reads Number and adds Number, and accepts only a MutableList of Number. '
       'The out-projection reads Number, forbids add, and accepts lists of Int or Double. The in-projection reads only Any?, adds Number, and accepts lists of Number or Any.">')
for x, head, hcls, rd, wr, acc in COLS:
    FIG += cell(x, 14, 210, head, hcls)
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="80" text-anchor="middle">read</text>'
    FIG += cell(x, 86, 210, rd[0], rd[1])
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="146" text-anchor="middle">write</text>'
    FIG += cell(x, 152, 210, wr[0], wr[1])
    FIG += f'<text class="t-s t-m" x="{x + 105}" y="214" text-anchor="middle">you can pass</text>'
    FIG += f'<text class="t-s t-code" x="{x + 105}" y="236" text-anchor="middle">{acc}</text>'
FIG += ('<text class="t-s t-m" x="350" y="276" text-anchor="middle">A projection closes one side of an invariant type, for one parameter or variable.</text>'
        '</svg>')

S1 = """Lessons 4 and 5 of this track put the variance on the class: `Feed<out T>` only hands values out, `Sink<in T>` only takes them in. Many types can't do that. `MutableList<E>` has `get(): E` and `add(element: E)`. `Array<T>` has `get` and `set`. `T` sits in both positions, so the class must stay invariant, and lesson 3 showed what goes wrong when Java arrays pretend otherwise.

The trouble is that one function rarely uses both sides. Here is the copy example from the Kotlin docs, first without any variance:

```text
fun copyRow(from: Array<Any>, to: Array<Any>) { for (i in from.indices) to[i] = from[i] }

copyRow(amounts, row)     // amounts is an Array<Int>
Argument type mismatch: actual type is 'Array<Int>', but 'Array<Any>' was expected.
```

Kotlin refuses for a good reason. If `copyRow` could see an `Array<Int>` as an `Array<Any>`, it could write a `String` into it. But `copyRow` never writes to `from`. It only reads. So you tell the compiler that, right where the type is used:

```java
// Java arrays are covariant, so Object[] already accepts an Integer[]
static void copyRow(Object[] from, Object[] to) {
    for (int i = 0; i < from.length; i++) to[i] = from[i];   // the JVM checks each store
}

copyRow(amounts, row);              // fine
copyRow(amounts, new String[3]);    // compiles, then throws ArrayStoreException
```

```kotlin
fun copyRow(from: Array<out Any>, to: Array<Any>) {
    for (i in from.indices) to[i] = from[i]   // get() on Array<out Any> returns Any
}

copyRow(amounts, row)                       // fine: Array<Int> fits Array<out Any>
copyRow(amounts, arrayOfNulls<String>(3))   // compile error: Array<String?> is not an Array<Any>
```

`Array<out Any>` is a **type projection**. You haven't changed `Array`. You've asked for a narrower view of it, for one parameter: an array of some subtype of `Any` that this function will only read. Through that view `get` returns `Any`, and `set` is gone:

```text
from[0] = "EUR"
Receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.
```

Writing the variance where a type is used is called **use-site variance**. Java's wildcards are the same idea, and they are the only kind of variance Java has. Arrays are the odd case on the Java side: there are no wildcards for arrays, because every Java array has been covariant since Java 1.0 and the JVM checks each store at run time instead. Kotlin's `Array<out Any>` compiles to a plain `Object[]`.

The figure shows the three ways to look at one invariant type."""

S2 = """The projection you'll write most often is on `MutableList`. Here is a function that totals any mutable list of numbers:

```java
static double total(List<? extends Number> amounts) {
    double sum = 0;
    for (Number a : amounts) sum += a.doubleValue();   // reads come out as Number
    return sum;
}

total(cents);    // a List<Integer>
total(rates);    // a List<Double>
```

```kotlin
fun total(amounts: MutableList<out Number>): Double {
    var sum = 0.0
    for (a in amounts) sum += a.toDouble()      // reads come out as Number
    return sum
}

total(cents)     // a MutableList<Int>
total(rates)     // a MutableList<Double>
```

Read `MutableList<out Number>` as "a mutable list of *some* subtype of `Number`, and I don't know which". That unknown is why writing is forbidden. The list might be `cents`, a `MutableList<Int>`. Adding `2.5` would put a `Double` into a list of ints. So both compilers refuse every call that takes the element type:

```text
amounts.add(0)
Kotlin: Receiver type 'MutableList<out Number>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.
Java:   incompatible types: int cannot be converted to CAP#1
```

Even `add(0)` fails, though `0` is a fine `Int`. The compiler doesn't know the list holds ints. `CAP#1` is javac's name for that unknown: a **captured type**, a placeholder for "the one real element type of this particular list". Kotlin prints it as `CapturedType(out Number)`, for example when you try `val x: Int = amounts[0]`. Nothing you can write is known to be a subtype of the placeholder, so nothing goes in.

Members that don't take an `E` still work. `size`, `isEmpty()`, `removeAt(0)` and `clear()` all compile through the view, as lesson 4 showed. A projection limits which types flow in. It does not stop the list from changing.

You need this only for invariant types. Kotlin's read-only `List` is already declared `List<out E>`, so a plain `List<Number>` parameter accepts a `List<Int>`. Write `List<out Number>` and the compiler warns that the projection is redundant. You'll see that warning in this lesson's lab."""

S3 = """Now flip the direction. This helper appends zero-amount placeholder lines. It only ever writes `Int`s:

```java
static void padWithZeros(List<? super Integer> target, int count) {
    for (int i = 0; i < count; i++) target.add(0);
}

padWithZeros(ints, 1);       // List<Integer>
padWithZeros(numbers, 2);    // List<Number>
padWithZeros(anything, 2);   // List<Object>
```

```kotlin
fun padWithZeros(target: MutableList<in Int>, count: Int) {
    repeat(count) { target.add(0) }
}

padWithZeros(ints, 1)        // MutableList<Int>
padWithZeros(numbers, 2)     // MutableList<Number>
padWithZeros(anything, 2)    // MutableList<Any>
```

`MutableList<in Int>` means "a mutable list of `Int` or of some supertype of `Int`". Every such list accepts an `Int`, so `add(0)` is safe. Reading is the side that gets weaker. An element might be the `2.5` or the `"EUR"` that was already in the list, so the only thing the compiler can promise is `Any?` (Java: `Object`):

```text
val firstInt: Int = target[0]
Kotlin: Initializer type mismatch: expected 'Int', actual 'CapturedType(in Int)'.
Java:   incompatible types: CAP#1 cannot be converted to Integer
```

A `MutableList<Double>` is rejected at the call, because it can't take an `Int`: `Argument type mismatch: actual type is 'MutableList<Double>', but 'MutableList<in Int>' was expected.`

The JDK's utility methods are written this way, and calling them from Kotlin is a good way to learn the mapping. Two of them from `java.util.Collections`, and the same contracts in Kotlin:

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
java.util.Collections.copy(ints, listOf("a"))
Argument type mismatch: actual type is 'List<String>', but '(Mutable)List<out Int!>!' was expected.
```

Java's `? extends` became `out`. The rule in the Kotlin docs is that `Foo<? extends Bar>` becomes `Foo<out Bar!>!` and `Foo<? super Bar>` becomes `Foo<in Bar!>!`. The `!` marks a platform type (Kotlin can't tell whether Java allows null), and `(Mutable)List` means Kotlin can't tell whether Java will modify the list. It works the other way too: a Kotlin parameter `MutableList<in T>` compiles to Java's `List<? super T>`. The lab's tests check exactly that."""

S4 = """You now have two places to put `out` and `in`, and the rule for choosing is short.

If every public member of a class only produces `T`, declare `out T` on the class. If every member only consumes `T`, declare `in T`. You do it once and every caller benefits: nobody writes a projection, and a `List<Int>` simply is a `List<Number>`. This is **declaration-site variance**, and it's why Kotlin code has far fewer wildcards than Java code.

If the class both reads and writes `T`, it stays invariant: `MutableList`, `Array`, a cache, a repository with `save` and `findById`. Then each function that only reads, or only writes, asks for a projection:

```java
static final class Ledger<T> {                   // reads and writes T: invariant
    private final List<T> entries = new ArrayList<>();
    void record(T entry) { entries.add(entry); }
    T latest() { return entries.get(entries.size() - 1); }
}

static String latestId(Ledger<? extends PaymentEvent> ledger) { return ledger.latest().getPaymentId(); }
static void recordCard(Ledger<? super CardAuthorized> ledger, String id, long cents) {
    ledger.record(new CardAuthorized(id, cents));
}
```

```kotlin
class Ledger<T> {                                // reads and writes T: invariant
    private val entries = mutableListOf<T>()
    fun record(entry: T) { entries += entry }
    fun latest(): T = entries.last()
}

fun latestId(ledger: Ledger<out PaymentEvent>): String = ledger.latest().paymentId
fun recordCard(ledger: Ledger<in CardAuthorized>, id: String, cents: Long) =
    ledger.record(CardAuthorized(id, cents))
```

Java has no declaration-site variance, so every Java API works like `Ledger`. Each method that only reads or only writes must remember its wildcard, and the JDK has hundreds of them. Forget one and your own tests still pass. The first caller with a `List<Integer>` finds out.

The Kotlin compiler also guards the line between the two kinds:

| You write | The compiler says |
|---|---|
| `List<out PaymentEvent>` | warning: `Projection is redundant: the corresponding type parameter of 'List<out PaymentEvent>' has the same variance.` |
| `List<in PaymentEvent>` | error: `Projection conflicts with variance of the corresponding type parameter of 'List<in PaymentEvent>'. Remove the projection or replace it with '*'.` |
| `fun <out T> onFunction(t: T)` | error: `Variance annotations are only allowed for type parameters of classes and interfaces.` |

The last one catches people. Variance says when a `C<A>` can stand in for a `C<B>`. A generic function is not a type you can substitute, so `out` on its own type parameter has nothing to describe. Put the projection on a parameter's type instead, as `copyInto` does. The `'*'` in the second message is the star projection, the subject of the next lesson."""

L = {
    "id": "gen-06",
    "title": "Use-site variance and type projections",
    "minutes": 35,
    "goal": "By the end you can add `out` or `in` to a single use of an invariant type such as `MutableList` or `Array`, say exactly which calls each projection allows, map it to Java's `? extends` and `? super`, and decide between declaration-site and use-site variance.",
    "warmup": {
        "q": "`fun total(amounts: MutableList<Number>): Double` only reads the list. You call it with `cents: MutableList<Int>`. What happens?",
        "options": [
            "It compiles: an `Int` is a `Number`, so a list of ints is a list of numbers",
            "It doesn't compile, and the only fix is to copy `cents` into a new `MutableList<Number>`",
            "It doesn't compile, but `MutableList<out Number>` in the signature fixes it",
            "It compiles, and fails at run time when `total` reads the first element"
        ],
        "answer": 2,
        "why": "`MutableList` is invariant, because it both reads and writes `E`, so a `MutableList<Int>` is not a `MutableList<Number>`. But `total` only reads, so it can ask for an out-projection: `MutableList<out Number>` accepts a list of any subtype of `Number`. Copying works too, but you don't need it. Option one is the intuition that lesson 3 of this track disproved."
    },
    "sections": [
        {
            "h": "MutableList and Array can't pick a side, so you project them",
            "body": S1,
            "figure": {"svg": FIG, "caption": "One invariant MutableList, three views: plain (read and write, exact type only), out-projected (read only), in-projected (write only)."},
            "try": {
                "title": "Copy ints into a row of Any",
                "minutes": 4,
                "steps": [
                    "Run `ArrayCopyDemo` and its twin `ArrayCopyDemoJava`. Compare the second line of the Java output with the Kotlin file's wrong move 3.",
                    "In `ArrayCopyDemo.kt`, predict the error for each of the three wrong moves. Uncomment them one at a time and run.",
                    "Remove `out` from `copyRow`'s first parameter. Which line in `main` breaks now? Put it back."
                ],
                "code": kdemo("ArrayCopyDemo", "ArrayCopyDemoJava"),
                "expect": "Kotlin prints `1200, 350, 99`. Java prints `[1200, 350, 99]` and then `ArrayStoreException: java.lang.Integer`: the store into a `String[]` compiled and failed at run time. The Kotlin wrong moves fail at compile time: (1) `Initializer type mismatch: expected 'Array<Any>', actual 'Array<Int>'.`, (2) `Receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.`, (3) `Argument type mismatch: actual type is 'Array<String?>', but 'Array<Any>' was expected.` Without `out`, the call `copyRow(amounts, row)` fails the same way as wrong move 1."
            },
            "refs": [
                {"title": "Generics: type projections (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "An out-projection is a read view, and Java spells it ? extends",
            "body": S2,
            "try": {
                "title": "Total two lists, then try to add",
                "minutes": 4,
                "steps": [
                    "Run `ReadViewDemo` (or `ReadViewDemoJava`). One function totals a list of ints and a list of doubles.",
                    "Uncomment the two wrong moves one at a time, predict, run.",
                    "Change `total`'s parameter to read-only `List<Number>` and run. Then change it to `List<out Number>` and look for a `w:` line in the build output."
                ],
                "code": kdemo("ReadViewDemo", "ReadViewDemoJava"),
                "expect": "Both print `cents: 1649.0, rates: 1.75` and then `[350, 99]`: `removeAt` (Java: `remove(int)`) worked through the read view. `add(0)` fails with `Receiver type 'MutableList<out Number>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.` (Java: `incompatible types: int cannot be converted to CAP#1`), and the strict assignment with `expected 'MutableList<Number>', actual 'MutableList<Int>'` (Java: `List<Integer> cannot be converted to List<Number>`). `List<Number>` compiles with no projection; `List<out Number>` compiles with the warning `Projection is redundant: the corresponding type parameter of 'List<out Number>' has the same variance.`"
            }
        },
        {
            "h": "An in-projection is a write view, and Java spells it ? super",
            "body": S3,
            "try": {
                "title": "Pad three lists with one helper",
                "minutes": 4,
                "steps": [
                    "Run `WriteViewDemo` (or `WriteViewDemoJava`). Look at what `first is` prints for each list.",
                    "Uncomment the two wrong moves one at a time, predict, run.",
                    "Remove `in` from `padWithZeros` (Java: change `? super Integer` to `Integer`). Predict how many of the three calls in `main` still compile."
                ],
                "code": kdemo("WriteViewDemo", "WriteViewDemoJava"),
                "expect": "Both print `first is 1200`, `first is 2.5`, `first is EUR`, then `ints = [1200, 0], numbers = [2.5, 0, 0], anything = [EUR, 0, 0]` and `after Collections.fill: [7, 7, 7]`. Wrong move 1: `Initializer type mismatch: expected 'Int', actual 'CapturedType(in Int)'.` (Java: `CAP#1 cannot be converted to Integer`). Wrong move 2: `Argument type mismatch: actual type is 'MutableList<Double>', but 'MutableList<in Int>' was expected.` (Java: `ArrayList<Double> cannot be converted to List<? super Integer>`). Without the projection only the `ints` call compiles."
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
                "title": "Read and write one invariant ledger",
                "minutes": 4,
                "steps": [
                    "Run `ChooseDemo` (or `ChooseDemoJava`). `latestId` reads a ledger of cards; `recordCard` writes into a ledger of every event.",
                    "Uncomment the wrong move in `main`, predict, run.",
                    "At the bottom of `ChooseDemo.kt`, predict which of lines 1 to 3 is a warning and which are errors. Uncomment them one at a time to check."
                ],
                "code": kdemo("ChooseDemo", "ChooseDemoJava"),
                "expect": "Both print `pay_2 pay_3`. The wrong move fails with `Initializer type mismatch: expected 'Ledger<PaymentEvent>', actual 'Ledger<CardAuthorized>'.` (Java: `Ledger<CardAuthorized> cannot be converted to Ledger<PaymentEvent>`): the projections are on the functions, not the class. Line 1 compiles with the `Projection is redundant` warning. Line 2 fails with `Projection conflicts with variance of the corresponding type parameter of 'List<in PaymentEvent>'.` Line 3 fails with `Variance annotations are only allowed for type parameters of classes and interfaces.`"
            }
        }
    ],
    "analogy": "Think of an invariant `MutableList` as a shared ledger book in the finance office. The book itself allows reading and writing. A use-site projection is a permission slip for one visit. An out-projection is a reading-room pass: you may read every entry, and you're told only that each one is \"some kind of number\", so you are not allowed to write anything in. An in-projection is the drop slot in the door: you can post an entry of the agreed kind, and if you peek through the slot you see only \"something\". The book never changes; only what this visitor may do changes. The analogy breaks in one place: a reading-room pass in real life also stops you from tearing pages out, but an out-projection does not. `clear()` and `removeAt()` still work, because a projection limits types, not mutation.",
    "in_your_world": "Use-site projections show up at the edges of a payment service, where you pass mutable buffers around. A Kafka batch listener collects records into a `MutableList<PaymentEvent>` and hands it to helpers: the fee calculator only reads, so it takes `MutableList<out PaymentEvent>` (or better, a plain `List`), and the enrichment step only appends `CardAuthorized` lines, so it takes `MutableList<in CardAuthorized>`. Your own invariant classes get the same treatment: a Quarkus-managed `Ledger<T>` or a `Cache<K, V>` with `get` and `put` stays invariant, and the report that only reads asks for `Cache<String, out Money>`. On the Java side of the codebase, the same contracts are `List<? extends PaymentEvent>` and `List<? super CardAuthorized>`, the shape of the JDK's `Collections.addAll(Collection<? super T> c, T... elements)`.",
    "mistake": "The common mistake is declaring a parameter `MutableList<Number>` (Java: `List<Number>`) when the function only reads it. It works for the first caller, who happens to have a list of `Number`. The next caller has a `MutableList<Int>` and fixes the type error with `ints.toMutableList<Number>()`, an unchecked cast, or a second copy of the function. People make the mistake because the plain type looks simpler, and because \"an Int is a Number\" makes it feel like it should work. The fix is to ask what the function does with the list. Only reads and never modifies: take a read-only `List<Number>`. Reads and also removes or clears: take `MutableList<out Number>`. Only adds: take `MutableList<in Int>`. Reads and adds: keep the plain type.",
    "compare": {
        "title": "The same copy and fill contracts with wildcards and with projections",
        "java": {
            "title": "Transfers.java",
            "src": "import java.util.List;\nimport java.util.Queue;\nimport java.util.Collection;\n\nfinal class Transfers {\n    // dest only takes T, src only gives T: the shape of Collections.copy\n    static <T> int copyInto(List<? extends T> from, List<? super T> to) {\n        for (T x : from) to.add(x);\n        return from.size();\n    }\n\n    // only writes: ? super\n    static <T> void fillWith(List<? super T> target, T value, int count) {\n        for (int i = 0; i < count; i++) target.add(value);\n    }\n\n    // a read-only parameter still needs ? extends in Java\n    static double sumAll(List<? extends Number> amounts) {\n        double sum = 0;\n        for (Number a : amounts) sum += a.doubleValue();\n        return sum;\n    }\n}"
        },
        "kotlin": {
            "title": "Projections.kt",
            "src": "// MutableList is invariant, so each function projects it at the use site\nfun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>): Int {\n    for (x in from) to.add(x)\n    return from.size\n}\n\nfun <T> fillWith(target: MutableList<in T>, value: T, count: Int) {\n    repeat(count) { target.add(value) }\n}\n\n// List is declared List<out E>: no projection needed (one would only earn a warning)\nfun sumAll(amounts: List<Number>): Double {\n    var sum = 0.0\n    for (a in amounts) sum += a.toDouble()\n    return sum\n}"
        },
        "note": "For `MutableList`, the two versions say exactly the same thing: Kotlin's `MutableList<out T>` compiles to Java's `List<? extends T>`, and `MutableList<in T>` to `List<? super T>`, and Kotlin shows Java's wildcards back to you as `out` and `in`. The real difference is `sumAll`. Java has no read-only list type with declared variance, so every reading parameter needs `? extends`. Kotlin's `List` carries `out E` on its declaration, so the plain type is already flexible and a projection on it is redundant. Arrays differ too: Java arrays are covariant with run-time store checks and take no wildcards, while Kotlin's `Array<out T>` is a compile-time projection that compiles down to a plain Java array."
    },
    "worked": {
        "title": "Settle pending authorizations into a batch of any events",
        "steps": [
            {"say": "A settlement job moves pending card authorizations into the outgoing batch, then clears the pending list. The first draft uses plain types. The batch the caller has is a `MutableList<PaymentEvent>`, because it also holds refunds. Read the error.",
             "code": "fun settle(pending: MutableList<CardAuthorized>, batch: MutableList<CardAuthorized>): Long {\n    var cents = 0L\n    for (a in pending) { batch.add(a); cents += a.cents }\n    pending.clear()\n    return cents\n}\n\nval pending = mutableListOf(CardAuthorized(\"pay_1\", 1_200), CardAuthorized(\"pay_2\", 350))\nval batch = mutableListOf<PaymentEvent>(RefundIssued(\"pay_0\", 500))\nsettle(pending, batch)\n// error: Argument type mismatch: actual type is 'MutableList<PaymentEvent>',\n//        but 'MutableList<CardAuthorized>' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static long settle(List<CardAuthorized> pending, List<CardAuthorized> batch) {\n    long cents = 0;\n    for (CardAuthorized a : pending) { batch.add(a); cents += a.cents(); }\n    pending.clear();\n    return cents;\n}\n\nList<CardAuthorized> pending = new ArrayList<>(List.of(new CardAuthorized(\"pay_1\", 1_200), new CardAuthorized(\"pay_2\", 350)));\nList<PaymentEvent> batch = new ArrayList<>(List.of(new RefundIssued(\"pay_0\", 500)));\nsettle(pending, batch);\n// error: incompatible types: List<PaymentEvent> cannot be converted to List<CardAuthorized>"},
            {"say": "Name what each parameter does with `CardAuthorized` values. `pending` gives them to you (and is cleared, which takes no element). `batch` only receives them. So `pending` is a producer and `batch` is a consumer, for this function only. Both types are `MutableList`, which can't be declared `out` or `in`, so the variance goes on the parameters.",
             "code": "", "lang": ""},
            {"say": "Project each parameter. Self-check before reading the comments: why does `pending.clear()` still compile through an out-projection? (It takes no `E`, so it can't smuggle a wrong type in.)",
             "code": "fun settle(pending: MutableList<out CardAuthorized>, batch: MutableList<in CardAuthorized>): Long {\n    var cents = 0L\n    for (a in pending) {      // 1. read: each a is a CardAuthorized\n        batch.add(a)          // 2. write: the batch takes CardAuthorized or anything above it\n        cents += a.cents\n    }\n    pending.clear()           // 3. no E in clear(), so the read view allows it\n    return cents\n}\n\nsettle(pending, batch)        // compiles: 1550, and batch holds the refund plus both cards",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static long settle(List<? extends CardAuthorized> pending, List<? super CardAuthorized> batch) {\n    long cents = 0;\n    for (CardAuthorized a : pending) {   // 1. read: producer extends\n        batch.add(a);                    // 2. write: consumer super\n        cents += a.cents();\n    }\n    pending.clear();                     // 3. no T in clear()\n    return cents;\n}\n\nsettle(pending, batch);                  // compiles"},
            {"say": "Check the result from the caller's side. The batch can now be a `MutableList<CardAuthorized>`, a `MutableList<PaymentEvent>` or a `MutableList<Any>`. The pending list can be a list of any subtype of `CardAuthorized`. If you later need `settle` to read back from the batch (say, to dedupe by payment id), that read returns `Any?` through the in-projection, and the compiler tells you so. At that point the parameter really is read and write, and it should go back to the plain type.",
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
            "In `Projections.kt`, give `copyInto`'s `from` an `out` and its `to` an `in`, then write the loop and return the count.",
            "Give `fillWith`'s `target` the projection that matches \"only written\", then append `count` copies.",
            "Write `sumAll`. Then change its parameter to `List<out Number>`, run the tests, and find the warning in the output. Put the plain `List<Number>` back.",
            "In `Transfers.java`, change `drainTo`'s parameters to `Queue<? extends T>` and `Collection<? super T>`, then poll until the queue is empty.",
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
        "prompt": "Close this page. Write `copyInto(from, to)` for two `MutableList`s in Kotlin, with the projections that let a `MutableList<Int>` be copied into a `MutableList<Number>`. Then write the Java method that Kotlin generates for it (the signature is enough), and the Java version of `fillWith`.",
        "answer": {
            "lang": "kotlin",
            "src": "fun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>): Int {\n    for (x in from) to.add(x)     // reads give T, writes take T\n    return from.size\n}\n\nfun <T> fillWith(target: MutableList<in T>, value: T, count: Int) {\n    repeat(count) { target.add(value) }\n}\n\n// Java sees: public static <T> int copyInto(List<? extends T> from, List<? super T> to)\n//            public static <T> void fillWith(List<? super T> target, T value, int count)",
            "alt": {"lang": "java", "title": "Transfers.java", "src": "static <T> int copyInto(List<? extends T> from, List<? super T> to) {\n    for (T x : from) to.add(x);   // producer extends, consumer super\n    return from.size();\n}\n\nstatic <T> void fillWith(List<? super T> target, T value, int count) {\n    for (int i = 0; i < count; i++) target.add(value);\n}"}
        }
    },
    "recap": [
        "A type that both reads and writes `T` (`MutableList`, `Array`, your own `Ledger`) must stay invariant.",
        "A type projection adds `out` or `in` at one use: `MutableList<out Number>` is a read view, `MutableList<in Int>` is a write view.",
        "Through an out-projection reads give the bound and calls that take `T` are forbidden. Through an in-projection writes of `T` are allowed and reads give only `Any?`.",
        "Kotlin's `out T` / `in T` projections compile to Java's `? extends T` / `? super T`, and Java's wildcards show up in Kotlin as `out` and `in`.",
        "Declare variance on the class when every member only produces or only consumes `T`. Project at the use site when the class does both.",
        "Projecting an already-variant type earns a warning (`List<out T>`) or an error (`List<in T>`), and variance on a function's type parameter is an error."
    ],
    "quiz": [
        {
            "q": "Inside `fun audit(events: MutableList<out PaymentEvent>)`, which line compiles?",
            "options": [
                "`events.add(CardAuthorized(\"pay_9\", 100))`",
                "`val e: PaymentEvent = events[0]`",
                "`events[0] = RefundIssued(\"pay_9\", 100)`",
                "`val c: CardAuthorized = events[0]`"
            ],
            "answer": 1,
            "why": "Reads through an out-projection come out as the bound, `PaymentEvent`. Both writes are forbidden, because the real list might be a `MutableList<RefundIssued>` or a `MutableList<CardAuthorized>`, and the compiler doesn't know which. Reading into `CardAuthorized` fails for the same reason: the element is only known to be some `PaymentEvent`."
        },
        {
            "q": "`fun pad(target: MutableList<in Int>)`. What is the type of `target[0]` inside `pad`?",
            "options": [
                "`Int`",
                "`Number`",
                "`Any?`",
                "It doesn't compile: you can't read through an in-projection"
            ],
            "answer": 2,
            "why": "The list could be a `MutableList<Int>`, `MutableList<Number>` or `MutableList<Any?>`, so the only safe promise is `Any?`. Reading is allowed, it just tells you little. `Int` is the tempting answer, but the list might hold the `\"EUR\"` someone put there before."
        },
        {
            "q": "You own `interface Cache<K, V> { fun get(key: K): V?; fun put(key: K, value: V) }`. A report wants to accept a `Cache<String, CardFee>` where it expects fees of any kind (`Fee`), and it only calls `get`. Which change is right?",
            "options": [
                "Declare `interface Cache<K, out V>`",
                "Give the report's parameter the type `Cache<String, out Fee>`",
                "Give the report's parameter the type `Cache<String, in Fee>`",
                "Make the report take a raw `Cache`"
            ],
            "answer": 1,
            "why": "`Cache` both returns and takes `V`, so it must stay invariant: `out V` on the interface fails with `type parameter 'V' is declared as 'out' but occurs in 'in' position`, because of `put`. The report only reads, so it projects at the use site: `Cache<String, out Fee>` accepts a `Cache<String, CardFee>`, and `put` is unavailable through that view. `in Fee` would make `get` return `Any?`. Kotlin has no raw types."
        },
        {
            "q": "Java's `Collections.copy` is `<T> void copy(List<? super T> dest, List<? extends T> src)`. How does Kotlin show the `dest` parameter in an error message?",
            "options": [
                "`MutableList<in T!>!`",
                "`List<out T>`",
                "`MutableList<T>`",
                "`List<*>`"
            ],
            "answer": 0,
            "why": "Java wildcards become projections: `? super T` becomes `in T`, and `? extends T` becomes `out T`. The `!` marks platform types, because Kotlin can't know Java's nullability. `List<*>` is how Kotlin shows a Java raw `List`, which is a different thing."
        },
        {
            "q": "From \"Contravariance with in: consumers\": the lab's `highest(items: List<T>, comparator: Comparator<in T>)` needs a projection on the comparator but not on the list. Why?",
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
        {"front": "What is a type projection?", "back": "Variance written where a type is used, such as `MutableList<out Number>` in a parameter. It narrows that one use to reading or to writing; the class itself stays invariant."},
        {"front": "Through `MutableList<out Number>`, what do `get` and `add` do?", "back": "`get` returns `Number`. `add` is forbidden: the real list might be a `MutableList<Int>`."},
        {"front": "Through `MutableList<in Int>`, what type does `get` return?", "back": "`Any?`. The list may be a `MutableList<Number>` or `MutableList<Any?>`, so nothing more specific is safe."},
        {"front": "Does `clear()` compile on a `MutableList<out Payment>`?", "back": "Yes. `clear()` takes no element, so a projection doesn't block it. Projections limit types, not mutation."},
        {"front": "How does Kotlin show Java's `List<? extends Integer>` and `List<? super Integer>`?", "back": "As `(Mutable)List<out Int!>!` and `MutableList<in Int!>!`: `? extends` becomes `out`, `? super` becomes `in`."},
        {"front": "Declaration-site or use-site variance: how do you choose?", "back": "If every member only produces `T` (or only consumes it), declare `out` (or `in`) on the class. If the class both reads and writes `T`, keep it invariant and project in each function that uses one side."},
        {"front": "What does `fun f(l: List<in String>)` give?", "back": "An error: the projection conflicts with `List`'s declared `out E`. (`List<out String>` gives only a warning: the projection is redundant.)"}
    ],
    "terms": [
        {"term": "Type projection", "plain": "`out` or `in` written on one use of a type, giving a read-only or write-only view of it."},
        {"term": "Use-site variance", "plain": "Variance written where a type is used (a parameter, a variable). Java's wildcards and Kotlin's projections."},
        {"term": "Declaration-site variance", "plain": "Variance written once on the class (`interface List<out E>`), so every use gets it."},
        {"term": "Out-projection", "plain": "`C<out T>`: you can read `T` values; calls that take a `T` are forbidden."},
        {"term": "In-projection", "plain": "`C<in T>`: you can pass `T` values in; reads come back as `Any?`."},
        {"term": "Captured type", "plain": "The compiler's placeholder for the one unknown real type behind a projection or wildcard (`CAP#1`, `CapturedType(out Number)`)."},
        {"term": "Platform type", "plain": "A type from Java whose nullability Kotlin doesn't know, shown as `T!` (and `(Mutable)List` for Java lists)."}
    ],
    "explain_back": {
        "prompt": "A teammate's `fun total(amounts: MutableList<Number>)` rejects their `MutableList<Int>`. They propose making `MutableList` covariant \"like List\". Explain why that can't work, and what to write instead.",
        "answer": "`MutableList` has `add(element: E)` as well as `get(): E`, so `E` is in an in-position and an out-position. If a `MutableList<Int>` could be used as a `MutableList<Number>`, someone could add a `Double` to a list of ints, which is exactly the bug Java arrays have. So the class has to stay invariant. But `total` only reads, so it can ask for a read-only view in its own signature: `MutableList<out Number>`. That accepts a list of any subtype of `Number`, gives back `Number` on reads, and forbids `add`. Even simpler, if `total` never modifies the list, take a plain read-only `List<Number>`, which is already covariant. In Java the same parameter is `List<? extends Number>`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Both compilers turn a wildcard or projection into a fresh **captured type** each time they check an expression: \"the one specific type this list really has\". That's why `CAP#1` shows up in javac messages. Java can also capture a wildcard for a method call, which gives a well-known trick: you can't write `l.set(i, l.get(j))` on a `List<?>`, but you can pass the `List<?>` to a private generic helper `<T> void swapHelper(List<T> l, int i, int j)`, and inside the helper the element type has a name. The JDK chose not to bother. `Collections.swap(List<?> list, int i, int j)` assigns the list to a raw `List` and calls `l.set(i, l.set(j, l.get(i)))` under `@SuppressWarnings`, with a source comment saying that capturing the wildcard would need a supplementary private method.\n\nKotlin captures projected arguments for calls too. Given `fun <T> swap(l: MutableList<T>, i: Int, j: Int)`, the calls `swap(star, 0, 1)` with `star: MutableList<*>` and `swap(view, 0, 1)` with `view: MutableList<out Number>` both compile with kotlinc 2.4.21. Inside `swap`, `T` is the captured type, so values read from the list may be written back into the same list. You'll meet `MutableList<*>` properly in the next lesson.\n\nArrays have one more twist. Because Java arrays carry no wildcards, Kotlin compiles `Array<out Number>` and `Array<Number>` both to `Number[]`, and `Array<in Number>` to `Object[]`. From Java, those differences are invisible; the projection exists only for the Kotlin compiler. The door opens the other way too. Kotlin shows a Java `Object[]` parameter as `Array<(out) Any!>!`, so you may pass an `Array<String>` to it, as Java code could. That brings Java's covariance back: `java.util.Arrays.fill(names, 42)` with `names: Array<String>` compiles in Kotlin and throws `ArrayStoreException: java.lang.Integer` at run time."
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
