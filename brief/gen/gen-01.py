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


FIG = (
    '<svg viewBox="0 0 640 250" role="img" aria-label="One generic class Box of T is filled in three ways, '
    'Box of String, Box of Int and Box of Apple, which the compiler checks as three types. At run time all three are one class, Box.">'
    '<text class="t-s t-m" x="115" y="22" text-anchor="middle">you write</text>'
    '<text class="t-s t-m" x="385" y="22" text-anchor="middle">the compiler checks</text>'
    '<text class="t-s t-m" x="570" y="22" text-anchor="middle">the JVM runs</text>'
    '<rect class="box-a" x="30" y="100" width="170" height="50" rx="8"/>'
    '<text class="t t-code" x="115" y="130" text-anchor="middle">class Box&lt;T&gt;</text>'
    '<text class="t-s t-m" x="115" y="172" text-anchor="middle">T is a blank on the label</text>'
    '<rect class="box" x="300" y="40" width="170" height="40" rx="8"/>'
    '<text class="t t-code" x="385" y="65" text-anchor="middle">Box&lt;String&gt;</text>'
    '<rect class="box" x="300" y="105" width="170" height="40" rx="8"/>'
    '<text class="t t-code" x="385" y="130" text-anchor="middle">Box&lt;Int&gt;</text>'
    '<rect class="box" x="300" y="170" width="170" height="40" rx="8"/>'
    '<text class="t t-code" x="385" y="195" text-anchor="middle">Box&lt;Apple&gt;</text>'
    '<line class="ln-a" x1="200" y1="125" x2="298" y2="62" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="125" x2="298" y2="125" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="200" y1="125" x2="298" y2="188" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="520" y="100" width="100" height="50" rx="8"/>'
    '<text class="t t-code" x="570" y="130" text-anchor="middle">Box</text>'
    '<line class="ln-d" x1="470" y1="60" x2="518" y2="118" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="470" y1="125" x2="518" y2="125" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="470" y1="190" x2="518" y2="133" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="570" y="172" text-anchor="middle">one class,</text>'
    '<text class="t-s t-m" x="570" y="188" text-anchor="middle">label torn off</text>'
    '<text class="t-s t-m" x="385" y="236" text-anchor="middle">three labels, three different types</text>'
    '</svg>'
)

OPENING = """Picture the storeroom behind a small fruit shop. Boxes sit on the shelves, each with a label: Gala apples, lemons, paper bags. Someone in the back fills them before the shop opens, and the person at the counter trusts the labels.

One morning the counter opens the box for "today's apple" to write the sign, and finds the number 12 where a name should be. The back room wrote how many apples there were, not which kind. The mistake happened in the back. It shows up at the counter.

A box declared to hold `Any` is a box with no label. The compiler lets anything in, and the mistake waits for whoever opens it. It's an easy trap, because `Any` feels flexible.

Part 2 ended with a service that answered every request inside its deadline, even under load. Those were promises about time. Part 3 starts with promises about types. In this lesson, we'll watch an unlabeled box fail far from its bug, label it with a type parameter, let the compiler fill in labels, and see how Java writes the same. Before we start, make a guess, and keep it in mind."""

S1 = """Java didn't always have generics, the feature this track is about: classes and functions with a blank where a type goes. Before Java 5, a container that could hold anything held `Object`, and Kotlin's version of that habit is `Any`. You put a value in, and you cast it back when you take it out. A **cast**, `(String)` in Java or `as String` in Kotlin, tells the compiler "trust me, this is a `String`". The real check happens later, while the program runs.

Here is the storeroom from the opening, written that way. `restock` is the back room, filling the box before the shop opens. `signFor` is the counter, reading the box to write the sign for the day's apple:

```java
class AnyBox { Object value; AnyBox(Object v) { value = v; } }

static void restock(AnyBox box) {
    box.value = 12;                       // the bug: how many apples, not which variety
}

static String signFor(AnyBox box) {
    String variety = (String) box.value;  // ClassCastException here
    return "Today's apple: " + variety;
}
```

```kotlin
class AnyBox(var value: Any)

fun restock(box: AnyBox) {
    box.value = 12                    // the bug: how many apples, not which variety
}

fun signFor(box: AnyBox): String {
    val variety = box.value as String // ClassCastException here
    return "Today's apple: $variety"
}
```

The bug is in `restock`. It stored the count, 12, where the counter expects a name such as `"Gala"`. The compiler accepts it, because an `Int` is an `Any`, and `restock` returns normally. The box didn't complain when the 12 went in. Boxes never do.

Before you read the output, decide where you expect the program to fail. Here is what `AnyBoxDemo`, the same program in the labs, printed:

```text
restock() returned. Nothing has failed yet.
ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
thrown in: workbench.generics.l01.demo.AnyBoxDemoKt.signFor(AnyBoxDemo.kt:13)
```

The exception names `signFor`, line 13: the cast at the counter. The counter did nothing wrong, and the function with the bug isn't in the trace at all. In a bigger program, the read might come hours later, in code another team owns.

That is the real cost of `Any` plus casts. The type check still happens, but it happens late, and in the wrong place. The error shows up where the value is read. The bug is where it was written.

Generics move the check to the write. Give the box a **type parameter**, a name in angle brackets that stands for the type of what goes inside, and say what this box holds:

```java
class Box<T> { T value; Box(T v) { value = v; } }

static void restock(Box<String> box) {
    box.value = 12;                       // now a compile error
}
```

```kotlin
class Box<T>(var value: T)

fun restock(box: Box<String>) {
    box.value = 12                    // now a compile error
}
```

Both compilers now reject the bad line itself. Think of the compiler as a clerk at the storeroom door who reads every label and turns away anything that doesn't match. javac says `incompatible types: int cannot be converted to String`. kotlinc says:

```text
error: assignment type mismatch: actual type is 'Int', but 'String' was expected.
```

The counter needs no cast any more. `box.value` is already a `String`, so `signFor` can't throw a `ClassCastException`.

**A cast checks at the read, far from the bug. Put the type on the label instead.**

The compiler messages in this track come from kotlinc 2.4.21, the command-line Kotlin compiler. Gradle and IntelliJ print the same text with a capital first letter.

So what exactly is that `<T>`? Let's read the label closely."""

S2 = """Picture a box whose label comes printed with a gap: "Box of ________". The person who made the box has no idea what will go in it. Whoever takes the box writes in the gap, "Box of apples", and from then on the clerk at the door turns away anything else.

`class Box<T>` is that printed label. Read it as: "Box has one blank in it, called `T`. Whoever uses Box fills the blank with a real type." `T` is the **type parameter**. The real type you write in, like `String` in `Box<String>`, is the **type argument**. Inside the class, `T` stands for whatever the caller chose, and the class never finds out which one.

Here is the box with one more method. `replace` puts a new value in and hands back the old one:

```java
class Box<T> {
    T value;
    Box(T value) { this.value = value; }
    T replace(T newValue) {
        T old = value;
        value = newValue;
        return old;
    }
}

Box<String> variety = new Box<>("Gala");
Box<Integer> count = new Box<>(12);
variety.replace("Fuji");      // fine
count.replace("Fuji");        // error: String cannot be converted to Integer
```

```kotlin
class Box<T>(var value: T) {
    fun replace(newValue: T): T {
        val old = value
        value = newValue
        return old
    }
}

val variety = Box("Gala")       // Box<String>
val count = Box(12)             // Box<Int>
variety.replace("Fuji")         // fine
count.replace("Fuji")           // error: actual type is 'String', but 'Int' was expected
```

One class gives you many types: `Box<String>`, `Box<Int>`, `Box<Apple>`. To the compiler, `Box<String>` and `Box<Int>` are as different as `String` and `Int`, and it checks each one on its own.

How does it check `count.replace("Fuji")`? It fills in the blank. `count` is a `Box<Int>`, so the compiler reads every `T` in `Box` as `Int`. For that call, `replace` is `replace(newValue: Int): Int`, and a `String` doesn't fit. Fill in the blank, then check the call as if the class had been written for `Int` all along. Do that in your head, and you can predict any call on a generic class before the compiler does.

Functions can have blanks too. In Java, the `<T>` goes before the return type. In Kotlin, it goes right after `fun`, before the function name:

```java
static <T> T firstOrNull(List<T> items) {
    return items.isEmpty() ? null : items.get(0);
}
```

```kotlin
fun <T> firstOrNull(items: List<T>): T? =
    if (items.isEmpty()) null else items[0]
```

`<T>` declares the blank. `List<T>` and `T?` use it, and the two uses are tied together. Pass a `List<Apple>` and you get an `Apple?` back, with no cast. Pass a `List<String>` and you get a `String?`.

A function can have several type parameters, separated by commas: `fun <T, K> indexBy(items: List<T>, key: (T) -> K): Map<K, T>`. The single-letter names are a habit, not a rule: `T` for type, `E` for element, `K` and `V` for key and value, `R` for result.

A method can also have a type parameter that its class doesn't have. In `fun <C> mapSecond(f: (B) -> C): Duo<A, C>` on a class `Duo<A, B>`, `A` and `B` belong to the class. `C` belongs to this one call, and the lambda you pass decides what it is. You'll write that method in the lab.

Here the box picture breaks, and the break matters later. A real label stays on the box, and anyone can read it next week. On the JVM, the program that runs compiled Kotlin and Java code, the compiler checks the label and then tears it off. At run time there is only one `Box` class, and the `<String>` part is gone. Lesson 8 of this track, on type erasure, shows what that costs you.

Writing every label by hand would get tiring, though. Most of the time, the compiler fills in the blank for you."""

S3 = """You rarely write type arguments in Kotlin. The compiler works them out from the values you pass and from the type you expect. That is **type inference**, and Java does it too, with `var` and the diamond `<>`, which the next section explains.

```java
var weights = List.of(180, 150, 210);            // List<Integer>
var box = new Box<>("Gala");                     // Box<String>
var prices = Map.of("apple", 40, "mango", 250L); // Map<String, Number & Comparable<...> & ...>
```

```kotlin
val weights = listOf(180, 150, 210)              // List<Int>
val box = Box("Gala")                            // Box<String>
val prices = mapOf("apple" to 40, "mango" to 250L)  // Map<String, Long>
```

Look at the last line in each. Kotlin sees `250L`, a `Long`, in the same map, and makes the literal `40` a `Long` too, so both prices fit one type. Java never changes a literal's type: `40` stays an `Integer`, so javac infers a long type for the values, one you couldn't write yourself.

When the values really have different types, the compiler picks the closest type they share:

```java
var mixed = List.of(180, 2.5);   // List<Number & Comparable<...> & Constable & ConstantDesc>
var odd = List.of(1, "a");       // another intersection, of Serializable, Comparable and more
```

```kotlin
val mixed = listOf(180, 2.5)     // List<Number & Comparable<*>>
val odd = listOf(1, "a")         // List<Comparable<*> & Serializable>
```

`Number & Comparable<*>` is an **intersection type**: a type that is two types at once, here something that is both a `Number` and a `Comparable`. You can't write that type in your own code, but the compiler uses it. When you see one, you have usually mixed types by accident, a whole number and a decimal in one list, say.

Sometimes there is nothing to infer from. `emptyList()` gets no values, so Kotlin has no clue what `T` should be:

```text
error: cannot infer type for type parameter 'T'. Specify it explicitly.
```

Java doesn't complain here. `var none = Collections.emptyList();` quietly becomes a `List<Object>`, which is rarely what you meant: javac shrugs and picks the widest type there is. In both languages, the fix is the same. Write the type argument at the call, or give the variable a type and let the compiler work backwards from it:

```java
var none = Collections.<String>emptyList();
List<String> alsoNone = Collections.emptyList();
```

```kotlin
val none = emptyList<String>()
val alsoNone: List<String> = emptyList()
```

Each pair means the same thing. I use the first form inside expressions and the second for properties, where the declared type documents the code anyway.

Kotlin builders infer too. `buildList { add("Gala"); add("Fuji") }` is a `List<String>`, worked out from the `add` calls inside the lambda. Java has no such builder, so there you name the type up front: `new ArrayList<String>()`.

Here is a trick you'll use for the rest of this track. When you're not sure what the compiler inferred, assign the value to a type you know is wrong, such as `val probe: Int = mixed` in Kotlin or `int probe = mixed;` in Java. The error message prints the real type.

Everything so far works the same in Java, with different punctuation. Let's line the two up, and meet the one box Java kept with no label at all."""

S4 = """Java has had generics since Java 5, and Kotlin compiles to the same JVM machinery. The ideas map one to one. Only the punctuation moves:

```java
class Box<T> {
    private T value;
    Box(T value) { this.value = value; }
    T get() { return value; }
}

static <T> T firstOrNull(List<T> items) {
    return items.isEmpty() ? null : items.get(0);
}

Box<String> box = new Box<>("Gala");                   // diamond
List<String> none = Collections.emptyList();           // inferred from the target
List<String> same = Collections.<String>emptyList();   // explicit type argument
```

```kotlin
class Box<T>(private var value: T) {
    fun get(): T = value
}

fun <T> firstOrNull(items: List<T>): T? =
    if (items.isEmpty()) null else items[0]

val box = Box("Gala")                        // no diamond, no new
val none: List<String> = emptyList()         // inferred from the target
val same = emptyList<String>()               // explicit type argument
```

Three differences matter in practice.

In a Java method, `<T>` comes before the return type: `static <T> T firstOrNull(...)`. In Kotlin it comes before the function name. The meaning is the same. Java also has no nullable types, so its `firstOrNull` returns a plain `T` that may be null, while Kotlin's says `T?` out loud.

Java needs the **diamond**, the empty `<>` in `new Box<>("Gala")`, which asks javac to infer the type argument. Leave it out, and `new Box("Gala")` is a **raw type**: `Box` with its generics switched off. Kotlin has no `new` and no raw types, so `Box("Gala")` is always a `Box<String>`.

Java type arguments must be reference types, that is, classes, never the primitive types such as `int` or `double`. `List<int>` is an error (`unexpected type`, `required: reference`, `found: int`), so you write `List<Integer>`. In Kotlin you write `List<Int>`, and the compiler stores boxed `java.lang.Integer` objects for you, each number wrapped in a small object.

Raw types are the unlabeled boxes Java kept, so that code from before Java 5 still compiles. A raw `List` accepts anything, and javac only warns. Here is a helper written the old way, from `RawTypeDemo` in the labs, with its Kotlin twin:

```java
static void addOldStock(List names) {       // raw: no <...>
    names.add(42);                           // compiles, with a warning
}

List<String> varieties = new ArrayList<>();
varieties.add("Gala");
addOldStock(varieties);
for (String variety : varieties) {           // throws on the second element
    System.out.println(variety.toUpperCase());
}
```

```kotlin
// Kotlin has no raw types: an unchecked cast is the closest way to switch the check off
private fun addOldStock(names: MutableList<*>) {
    @Suppress("UNCHECKED_CAST")
    (names as MutableList<Any?>).add(42)
}

val varieties: MutableList<String> = mutableListOf("Gala")
addOldStock(varieties)
for (variety in varieties) {                 // throws on the second element
    println(variety.uppercase())
}
```

javac's warning is easy to miss. By default, it's a single `Note:` line near the top of the build output, the kind people scroll past:

```text
Note: .../RawTypeDemo.java uses unchecked or unsafe operations.
```

Then the program runs, and fails on the way out:

```text
size = 2, nothing failed yet
GALA
ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (...)
```

Why does the read fail and not the add? At run time the list holds plain `Object` references, so `add(42)` has nothing to check against. Where your code reads an element as a `String`, javac adds a hidden cast to `String`, and that cast is what throws. Lesson 8 of this track shows that cast in the bytecode, the instructions the compilers write into class files. It is the `AnyBox` failure again, hidden inside a type that claims to be safe.

So when a Kotlin program gets a `ClassCastException` on a line with no cast in it, look for a raw type or an unchecked cast in the code underneath.

Our labels have one limit left. A plain `T` promises nothing about what goes in, so the code inside `Box` can't ask its value for anything beyond what every type has. Telling the compiler more is the next step."""

CLOSING = """We started in a storeroom where the counter found a number in a box meant for a name. A box of `Any` let the 12 in, and the cast at the counter paid for it. A type parameter puts a label on the box, so the compiler turns the 12 away on the line that wrote it.

Now search some code, yours or an open-source project's, for `as String` or `(String)` on a value read from a map or field of type `Any` or `Object`. Each one is an unlabeled box.

Next, we'll put a sign on the box that says "fruit only". How do you tell the compiler that `T` must be something it can compare, or never null?"""

L = {
    "id": "gen-01",
    "title": "Generics from zero: type parameters",
    "minutes": 35,
    "goal": "By the end you can write generic classes and functions in Kotlin and Java, read `<T>` as a blank on a label that each caller fills in, and explain why a type parameter moves a ClassCastException from the read to a compile error at the write.",
    "opening": OPENING,
    "warmup": {
        "q": "A `MutableList<Any>` holds the names of the apples on sale. The back room adds the `Int` 12 by mistake. Much later, the counter runs `val name = names[0] as String`. Where do you first hear about the bug?",
        "options": [
            "A compile error on the line that adds 12",
            "An exception on the line that adds 12",
            "A ClassCastException on the `as String` line, at the counter",
            "Nowhere: Kotlin converts 12 to \"12\""
        ],
        "answer": 2,
        "why": "An `Int` is an `Any`, so the add compiles and runs. The cast is the only check, and it runs at the counter. The exception names the counter's line, not the line with the bug. A `MutableList<String>` would have stopped the add at compile time, and a cast never converts a value."
    },
    "sections": [
        {
            "h": "A box with no label: a cast from Any fails far from the bug",
            "body": S1,
            "try": {
                "title": "Watch the cast fail far from the bug",
                "minutes": 4,
                "steps": [
                    "Run `AnyBoxDemo` with the command below (or its Java twin, `AnyBoxDemoJava`). Note which function the exception names.",
                    "Make the box generic: change the class to `class AnyBox<T>(var value: T)`, and change both functions to take `AnyBox<String>`. Leave `main` alone. (In the Java twin: `static class AnyBox<T>` with a `T value` field and a `T` constructor parameter, and both methods take `AnyBox<String>`.)",
                    "Before you run it again, predict which line the compiler will reject. Then run it. Undo the change when you're done."
                ],
                "code": demo("kotlin/workbench/generics/l01/demo/AnyBoxDemo.kt", "AnyBoxDemo.kt", "workbench.generics.l01.demo.AnyBoxDemoKt",
                         alt=("java/workbench/generics/l01/demo/AnyBoxDemoJava.java", "AnyBoxDemoJava.java", "workbench.generics.l01.demo.AnyBoxDemoJava", "java")),
                "expect": "The first run prints `restock() returned. Nothing has failed yet.` and then `ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String`, thrown in `signFor` at line 13. The function with the bug isn't in the trace. After the change, the build stops at compile time on `box.value = 12`. Kotlin says `Assignment type mismatch: actual type is 'Int', but 'String' was expected.`, and javac says `incompatible types: int cannot be converted to String`. The check moved from the counter to the back room."
            }
        },
        {
            "h": "Putting a label on the box: a type parameter is a blank the caller fills in",
            "body": S2,
            "figure": {"svg": FIG, "caption": "You write one generic class. The compiler checks each filled-in label as its own type. The JVM runs a single class, with the label torn off."},
            "try": {
                "title": "Fill the blank, then break it",
                "minutes": 4,
                "steps": [
                    "Run `BoxDemo` (or `BoxDemoJava`) with the command below to see it work.",
                    "Uncomment the three wrong moves at the bottom of `main`, one at a time. For each one, write down the error you expect before you run.",
                    "For the last one, decide how you would fix it without changing `firstOrNull`."
                ],
                "code": demo("kotlin/workbench/generics/l01/demo/BoxDemo.kt", "BoxDemo.kt", "workbench.generics.l01.demo.BoxDemoKt",
                         alt=("java/workbench/generics/l01/demo/BoxDemoJava.java", "BoxDemoJava.java", "workbench.generics.l01.demo.BoxDemoJava", "java")),
                "expect": "The demo prints `variety was Gala, now Fuji`, `count is 12` and `first on the list: Gala`. `count.replace(\"Fuji\")` gives `Argument type mismatch: actual type is 'String', but 'Int' was expected.` The `Box(42)` line gives `Initializer type mismatch: expected 'Box<String>', actual 'Box<Int>'.` The last one gives `expected 'String', actual 'String?'`: `firstOrNull` returns `T?`, so with `T = String` you get a `String?`. Declare `first` as `String?`, or add a default with `?: \"none\"`. In the Java twin, the first two fail (`String cannot be converted to Integer`, `cannot infer type arguments for Box<>`), and the third compiles: Java has no `T?`, so it hands you a `null` without a word."
            }
        },
        {
            "h": "Letting the compiler fill in the label: type inference",
            "body": S3,
            "try": {
                "title": "Make the compiler tell you the type",
                "minutes": 5,
                "steps": [
                    "Open `InferenceDemo.kt`. For each of the six values, write down the type you think the compiler inferred.",
                    "Uncomment `probe1` only and run the demo. The build fails, and the message prints the inferred type. Comment it out again.",
                    "Repeat for `probe2` to `probe6`, one at a time. Count how many you predicted right."
                ],
                "code": demo("kotlin/workbench/generics/l01/demo/InferenceDemo.kt", "InferenceDemo.kt", "workbench.generics.l01.demo.InferenceDemoKt",
                         alt=("java/workbench/generics/l01/demo/InferenceDemoJava.java", "InferenceDemoJava.java", "workbench.generics.l01.demo.InferenceDemoJava", "java")),
                "expect": "The messages say `actual 'List<Int>'`, `'List<Number & Comparable<*>>'`, `'List<String?>'`, `'Map<String, Long>'` and `'List<String>'`. `probe6` gives `Cannot infer type for type parameter 'T'. Specify it explicitly.` Most people miss `Map<String, Long>` and the intersection type on the first try. The Java twin prints `List<Integer>`, `List<INT#1>` (javac's name for an intersection), `List<String>`, `Map<String,INT#1>` and `ArrayList<String>`, and `probe6` shows `List<Object>`: Java picked `Object` for the empty list without a word."
            }
        },
        {
            "h": "The same box in Java: the diamond, raw types and Integer",
            "body": S4,
            "try": {
                "title": "Let a raw type smuggle in an Integer",
                "minutes": 4,
                "steps": [
                    "Run `RawTypeDemo` with the command below. Look for javac's `Note:` line near the top of the Gradle output.",
                    "Predict: does `names.add(42)` fail, or does something later fail?",
                    "Change the parameter of `addOldStock` from `List names` to `List<String> names` and run it again. Then undo it. (The Kotlin twin has no raw type to remove: it switches the check off with an unchecked cast instead, and fails the same way.)"
                ],
                "code": demo("java/workbench/generics/l01/demo/RawTypeDemo.java", "RawTypeDemo.java", "workbench.generics.l01.demo.RawTypeDemo", "java",
                         alt=("kotlin/workbench/generics/l01/demo/RawTypeDemo.kt", "RawTypeDemo.kt", "workbench.generics.l01.demo.RawTypeDemoKt")),
                "expect": "Gradle prints `Note: ... RawTypeDemo.java uses unchecked or unsafe operations.` The program prints `size = 2, nothing failed yet` and `GALA`, then a `ClassCastException` for the `Integer`. The add worked. The failure comes in the loop, where javac inserted a hidden cast to `String`. With `List<String> names`, the build fails at `names.add(42)` with `incompatible types: int cannot be converted to String`."
            },
            "refs": [
                {"title": "Raw types (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/rawTypes.html", "kind": "read"}
            ]
        }
    ],
    "compare": {
        "title": "One generic box and one generic function, in both languages",
        "java": {
            "title": "Box.java",
            "src": "import java.util.Collections;\nimport java.util.List;\n\nclass Box<T> {\n    private T value;\n\n    Box(T value) { this.value = value; }\n\n    T get() { return value; }\n\n    T replace(T newValue) {\n        T old = value;\n        value = newValue;\n        return old;\n    }\n\n    // <T> before the return type\n    static <T> T firstOrNull(List<T> items) {\n        return items.isEmpty() ? null : items.get(0);\n    }\n\n    static void use() {\n        Box<String> box = new Box<>(\"Gala\");           // diamond infers <String>\n        Box raw = new Box(\"Gala\");                       // raw type: checks off\n        List<String> none = Collections.<String>emptyList();\n        List<Integer> weights = List.of(180, 150);        // no List<int>\n    }\n}"
        },
        "kotlin": {
            "title": "Box.kt",
            "src": "class Box<T>(var value: T) {\n    fun replace(newValue: T): T {\n        val old = value\n        value = newValue\n        return old\n    }\n}\n\n// <T> before the function name\nfun <T> firstOrNull(items: List<T>): T? =\n    if (items.isEmpty()) null else items[0]\n\nfun use() {\n    val box = Box(\"Gala\")                  // Box<String>, no diamond needed\n    // there is no raw Box: Box without <...> must be inferable or it does not compile\n    val none = emptyList<String>()\n    val weights: List<Int> = listOf(180, 150)   // Int works; stored as java.lang.Integer\n}"
        },
        "note": "The model is the same: one class, type parameters checked at compile time, one class at run time. Kotlin infers the type argument from constructor arguments without a diamond, and it has no raw types, so the unchecked escape hatch that Java keeps for old code doesn't exist. Kotlin also accepts `Int` as a type argument, while Java makes you write `Integer`. Both compile to boxed objects. One more difference shows in `firstOrNull`: Kotlin's return type says `T?`, so callers must handle null. Java's `T` can be null without saying so."
    },
    "worked": {
        "title": "Make the storeroom generic",
        "steps": [
            {"say": "The shop's storeroom keeps boxes by label, such as \"shelf 2\" or \"back corner\". `Apple` and `Lemon` are small data classes with a variety and a weight in grams. The first version stores `Any`, and every caller casts. Find the two places where a wrong type could get in or out.", "code": "class Storeroom {\n    private val boxes = HashMap<String, Any>()\n\n    fun put(label: String, item: Any) { boxes[label] = item }\n    fun get(label: String): Any? = boxes[label]\n}\n\n// caller\nval gala = room.get(\"shelf 2\") as Apple?   // a cast on every read", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Storeroom {\n    private final Map<String, Object> boxes = new HashMap<>();\n\n    void put(String label, Object item) { boxes.put(label, item); }\n    Object get(String label) { return boxes.get(label); }\n}\n\n// caller\nApple gala = (Apple) room.get(\"shelf 2\");   // a cast on every read"},
            {"say": "1. Decide what varies. The label is always a `String`. What sits in the boxes changes from one storeroom to the next: apples in one, lemons in another. So the item type becomes the type parameter, and the label stays a plain `String`.", "code": "class Storeroom<T> {\n    private val boxes = HashMap<String, T>()\n\n    fun put(label: String, item: T) { boxes[label] = item }\n    fun get(label: String): T? = boxes[label]\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Storeroom<T> {\n    private final Map<String, T> boxes = new HashMap<>();\n\n    void put(String label, T item) { boxes.put(label, item); }\n    T get(String label) { return boxes.get(label); }   // null when absent\n}"},
            {"say": "2. Fill the blank where you use it. Each storeroom gets its own type. The cast is gone, and a wrong `put` is now a compile error on the line that makes it.", "code": "val apples = Storeroom<Apple>()\nval gala: Apple? = apples.get(\"shelf 2\")     // no cast\n\napples.put(\"shelf 2\", Lemon(\"Eureka\", 120))\n// error: argument type mismatch: actual type is 'Lemon',\n//        but 'Apple' was expected.", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "var apples = new Storeroom<Apple>();\nApple gala = apples.get(\"shelf 2\");         // no cast\n\napples.put(\"shelf 2\", new Lemon(\"Eureka\", 120));\n// error: incompatible types: Lemon cannot be converted to Apple"},
            {"say": "3. Add a helper that fills a box on a miss. It uses the class's `T`, so it needs no `<T>` of its own. Stop and answer: what would go wrong if you wrote `fun <T> getOrPut(...)` here? (A new `T` on the function would hide the class's `T`, and `boxes[label] = item` would no longer type-check. The same happens in Java with `<T> T getOrPut(...)`.)", "code": "fun getOrPut(label: String, fill: () -> T): T {\n    boxes[label]?.let { return it }\n    val item = fill()\n    boxes[label] = item\n    return item\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "T getOrPut(String label, Supplier<T> fill) {\n    T stored = boxes.get(label);\n    if (stored != null) return stored;\n    T item = fill.get();\n    boxes.put(label, item);\n    return item;\n}"}
        ]
    },
    "lab": {
        "title": "Write a generic Stack, two generic functions and a Duo",
        "minutes": 12,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l01/Stack.kt",
            f"{LAB}/main/kotlin/workbench/generics/l01/Search.kt",
            f"{LAB}/main/kotlin/workbench/generics/l01/Duo.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l01.*'",
        "steps": [
            "Run the tests once. All nine fail with `NotImplementedError`, because every body is still a `TODO`.",
            "In `Stack.kt`, add a `private val items = mutableListOf<T>()` and write the five members. A stack is last in, first out, like a pile of trays: `pop` takes the newest item. `pop` on an empty stack throws `NoSuchElementException`.",
            "In `Search.kt`, write `firstMatching` with a plain `for` loop, then `indexBy`. `indexBy` keeps the first item it sees for each key.",
            "In `Duo.kt`, write `swap`, `mapSecond` and `zipToDuos`. Read each return type first: it tells you what to build.",
            "Run the tests until all nine pass. Then search your code for `as `: there should be no casts at all."
        ],
        "hints": [
            "`MutableList<T>.removeAt(lastIndex)` returns a `T`. `lastOrNull()` returns a `T?`.",
            "For `indexBy`, a `LinkedHashMap<K, T>` with `putIfAbsent(key(item), item)` keeps the first item and the input order.",
            "`swap()` is one line: `Duo(second, first)`. The compiler checks that it is a `Duo<B, A>`."
        ],
        "done_when": "All nine tests in `GenericsFromZeroTest` pass, and your code has no `as` casts."
    },
    "drill": {
        "title": "Write Box and firstOrNull from memory",
        "minutes": 4,
        "prompt": "Close this page. In a scratch file, write a `Box<T>` class with a value and a `replace` method that returns the old value, plus a generic `lastOrNull(items)` function. Write it in Kotlin, then in Java. Check: where did each `<T>` go?",
        "answer": {
            "lang": "kotlin",
            "src": "class Box<T>(var value: T) {\n    fun replace(newValue: T): T {\n        val old = value\n        value = newValue\n        return old\n    }\n}\n\nfun <T> lastOrNull(items: List<T>): T? =\n    if (items.isEmpty()) null else items[items.size - 1]\n\n// Java: the <T> goes before the return type\n// static <T> T lastOrNull(List<T> items) {\n//     return items.isEmpty() ? null : items.get(items.size() - 1);\n// }",
            "alt": {"lang": "java", "title": "Box.java", "src": "class Box<T> {\n    private T value;\n\n    Box(T value) { this.value = value; }\n\n    T replace(T newValue) {\n        T old = value;\n        value = newValue;\n        return old;\n    }\n\n    // <T> before the return type\n    static <T> T lastOrNull(List<T> items) {\n        return items.isEmpty() ? null : items.get(items.size() - 1);\n    }\n}"}
        }
    },
    "recap": [
        "A cast from `Any` checks the type late, at the read, so the exception points at the reader and not at the line with the bug.",
        "`class Box<T>` declares a type parameter, a blank on the label. `Box<String>` fills it with a type argument, and the compiler checks every use against it.",
        "Kotlin puts a function's `<T>` before the name (`fun <T> f`). Java puts it before the return type (`static <T> T f`).",
        "Inference fills in most type arguments. When there is nothing to infer from, write `emptyList<String>()` or declare the variable's type. To see what the compiler inferred, assign the value to a wrong type (`val probe: Int = x`).",
        "Java raw types (`List` with no `<...>`) switch the checks off, and the failure comes later, at a hidden cast. Kotlin has none.",
        "The limit: an unbounded `T` promises nothing, so a generic class or function can only use what every type has. The label is also gone at run time."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "The shop keeps its settings in a `MutableMap<String, Any>`. One function stores `settings[\"openingHour\"] = \"9\"`. A report later runs `val hour = settings[\"openingHour\"] as Int`. What happens?",
            "options": [
                "A compile error on the line that stores \"9\"",
                "A ClassCastException on the line that stores \"9\"",
                "A ClassCastException on the `as Int` line, when the report runs",
                "`hour` is 9, because Kotlin converts the string"
            ],
            "answer": 2,
            "why": "A `String` is an `Any`, so the store compiles and runs. The cast in the report is the first check, and it fails there. Casts never convert values. A typed setting such as `openingHour: Int` would have made the store a compile error."
        },
        {
            "q": "Given `fun <T> firstOrNull(items: List<T>): T?`, what does the compiler say about `val name: String? = firstOrNull(listOf(1, 2))`?",
            "options": [
                "Initializer type mismatch: expected 'String?', actual 'Int?'",
                "It compiles, and `name` is null",
                "It compiles, and `name` is \"1\"",
                "It compiles, then throws ClassCastException"
            ],
            "answer": 0,
            "why": "`T` is inferred from the argument as `Int`, so the call returns `Int?`. That doesn't fit in a `String?`. The type parameter ties the input and the output together, which is the whole point. Nothing is converted at run time."
        },
        {
            "q": "`val none = emptyList()` does not compile. Which line fixes it?",
            "options": [
                "`val none = emptyList<String>()`",
                "`val none: List<String> = emptyList()`",
                "Either of the two above",
                "Neither: `emptyList` needs an argument"
            ],
            "answer": 2,
            "why": "The compiler needs to know `T`. You can give the type argument at the call, or give the variable a type and let inference work backwards from it. Both produce a `List<String>`."
        },
        {
            "q": "Java: `List raw = new ArrayList(); raw.add(7); List<String> names = raw; String s = names.get(0);` What happens?",
            "options": [
                "A compile error on `raw.add(7)`",
                "It compiles with unchecked warnings, then throws ClassCastException on the `names.get(0)` line",
                "It compiles, and `s` is \"7\"",
                "ArrayStoreException on `raw.add(7)`"
            ],
            "answer": 1,
            "why": "Raw types turn the checks off, so javac only warns. The `Integer` sits in the list until the read, where javac inserted a cast to `String`. The failure appears far from the line that caused it, the same as with `Any`."
        },
        {
            "q": "From the race conditions lesson: two threads take orders off a queue, and each runs `if (!seen.contains(id)) { ship(order); seen.add(id) }`, where `seen` is `ConcurrentHashMap.newKeySet<String>()`. The same order arrives twice, once on each thread. What is the smallest fix?",
            "options": [
                "Make the field `seen` volatile",
                "Replace `seen` with a `Collections.synchronizedSet`",
                "Make `seen` a `MutableSet<Any>` so both copies fit",
                "Ship only after `seen.add(id)` returned true: `if (seen.add(id)) ship(order)`"
            ],
            "answer": 3,
            "why": "This is check-then-act. Each set call is atomic on its own, but two calls in a row are not. `add` checks and inserts in one step and returns false for the second copy, so only one thread ships. `volatile` and a synchronized wrapper leave the gap between the two calls open.",
            "from": "conc-03"
        }
    ],
    "flashcards": [
        {"front": "In `class Box<T>`, what is `T`?", "back": "A type parameter: a blank on the label that each user of `Box` fills with a real type, such as `Box<String>`."},
        {"front": "Where does a bad value stored in an `Any` field get caught?", "back": "At the cast in the code that reads it, at run time. The stack trace points at the reader, not at the writer with the bug."},
        {"front": "`val e = emptyList()` gives what error?", "back": "`cannot infer type for type parameter 'T'. Specify it explicitly.` Fix: `emptyList<String>()` or `val e: List<String> = emptyList()`."},
        {"front": "Where does `<T>` go in a Kotlin generic function, and in a Java one?", "back": "Kotlin: before the name, `fun <T> first(xs: List<T>): T`. Java: before the return type, `static <T> T first(List<T> xs)`."},
        {"front": "What does Java's diamond in `new ArrayList<>()` do?", "back": "It tells javac to infer the type argument from the target type. Without it, `new ArrayList()` is a raw type."},
        {"front": "What does `listOf(1, 2.5)` infer to?", "back": "`List<Number & Comparable<*>>`, an intersection type: the closest type that both `Int` and `Double` share."},
        {"front": "How do you see the type Kotlin inferred for `x`?", "back": "Write `val probe: Int = x`. The compile error prints the actual type."}
    ],
    "terms": [
        {"term": "Cast", "plain": "`as String` or `(String)`: telling the compiler to trust you about a type, with the real check at run time."},
        {"term": "Type parameter", "plain": "The placeholder in a declaration, like `T` in `class Box<T>`: a blank on the label."},
        {"term": "Type argument", "plain": "The real type that fills a type parameter, like `String` in `Box<String>`."},
        {"term": "Generic function", "plain": "A function with its own type parameters, such as `fun <T> firstOrNull(items: List<T>): T?`."},
        {"term": "Type inference", "plain": "The compiler working out type arguments from the values you pass and the type you expect."},
        {"term": "Intersection type", "plain": "A type that is two types at once, like `Number & Comparable<*>`. Inferred by the compiler; you can't write it yourself."},
        {"term": "Diamond", "plain": "Java's `<>` on `new`, asking javac to infer the type arguments."},
        {"term": "Raw type", "plain": "A Java generic type used without type arguments, like plain `List`. The compiler stops checking it."}
    ],
    "explain_back": {
        "prompt": "A teammate wants to keep a `Map<String, Any>` of shop settings \"because it's flexible\". In your own words, explain what a type parameter or a typed class buys you, using where the error shows up.",
        "answer": "With `Any`, the compiler accepts any value on the way in, so a wrong value is only caught by the cast on the way out. That cast runs in whatever code reads the setting, maybe much later, and the exception points there instead of at the code that stored the bad value. With a type parameter, or a small class with typed fields, the compiler checks every write against the declared type, like a clerk reading the label on a box. The bad write becomes a compile error on the exact line with the bug, and readers need no casts, so they can't fail with a ClassCastException. The flexibility of `Any` is just the freedom to store the wrong thing."
    },
    "deeper": {
        "minutes": 8,
        "body": "Two inference tools are worth knowing.\n\nA **`_` type argument** lets you give some type arguments and let the compiler infer the rest. Take `fun <K, V> emptyShelf(firstKey: K): MutableMap<K, V>`. The compiler can work out `K` from the argument, but nothing tells it `V`. Write `emptyShelf<_, Int>(\"Gala\")`, and you get a `MutableMap<String, Int>`. The Kotlin generics page has a longer example.\n\nYou can also widen a type **on purpose**. `listOf(1, \"a\")` infers an intersection type that you can't name. If you really want a list of anything, say so: `listOf<Any>(1, \"a\")`. Now the type is `List<Any>`, and it reads honestly to the next person.\n\nOne Java detail: the explicit type argument goes after the dot, `Collections.<String>emptyList()`, and it needs something in front of the dot. Inside the same class you must write `this.<String>helper()` or `MyClass.<String>helper()`. In Java 8 and later you rarely need it, because target typing infers the argument from the variable you assign to.\n\nFinally, Kotlin's `List<Int>` holds `java.lang.Integer` objects, so a list of a million weights costs a million small objects. When that matters, use `IntArray`, which is a real `int[]`."
    },
    "sources": [
        {"title": "Generics: in, out, where (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Generics (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/index.html"},
        {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"}
    ]
}

out = ROOT / "content/lessons/gen-01.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
