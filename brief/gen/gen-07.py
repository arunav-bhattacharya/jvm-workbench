import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l07.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l07/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l07/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def cell(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="40" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 25}" text-anchor="middle">{label}</text>')


ROWS = [
    (44, "Dispenser&lt;out T : Fruit&gt;", "Dispenser&lt;out Fruit&gt;", "take out: Fruit", "box-ok"),
    (110, "Bin&lt;in T&gt;", "Bin&lt;in Nothing&gt;", "drop(x): nothing fits", "box-bad"),
    (176, "Box&lt;T&gt;  (invariant)", "Box&lt;out Any?&gt; / Box&lt;in Nothing&gt;", "get: Any?, set: nothing", "box-dim"),
]
FIG = ('<svg viewBox="0 0 700 270" role="img" aria-label="What a star projection means for three declarations. For Dispenser declared out T with the bound Fruit, '
       'Dispenser of star means Dispenser of out Fruit, so you take out a Fruit. For Bin declared in T, Bin of star means Bin of in Nothing, so nothing can be dropped in. '
       'For an invariant Box, Box of star reads as out Any? and writes as in Nothing.">'
       '<text class="t-s t-m" x="125" y="28" text-anchor="middle">declared as</text>'
       '<text class="t-s t-m" x="365" y="28" text-anchor="middle">the * stands for</text>'
       '<text class="t-s t-m" x="590" y="28" text-anchor="middle">what you can do</text>')
for y, decl, star, can, cls in ROWS:
    FIG += cell(15, y, 220, decl, "box")
    FIG += f'<line class="ln-a" x1="237" y1="{y + 20}" x2="252" y2="{y + 20}" marker-end="url(#arr)"/>'
    FIG += cell(255, y, 220, star, "box-a")
    FIG += f'<line class="ln-a" x1="477" y1="{y + 20}" x2="492" y2="{y + 20}" marker-end="url(#arr)"/>'
    FIG += cell(495, y, 190, can, cls)
FIG += ('<text class="t-s t-m" x="350" y="252" text-anchor="middle">Each * becomes the safest projection that the declaration allows.</text>'
        '</svg>')

OPENING = """Most boxes in the storeroom still have their labels. One doesn't. It sat by the back door through a wet week, and its label wore off. You can see that everything inside is the same kind of thing, but not which kind.

What can you safely do with it? You can take something out and look at it, as "some thing". You can count what's inside, or empty it. What you can't do is put anything in, because whatever you drop might be the wrong kind: lesson 3's lemon in a crate of apples, the other way round.

In code, that box is `List<*>`, a list of some type you don't know. The easy trap is to write `List<Any?>` instead, because `Any?` feels like the most generous type. In a `MutableList`, it's the fussiest.

Use-site variance and type projections ended with a `'*'` in an error message. In this lesson, we'll see what a star allows, and what it means for `out`, `in` and invariant types. Then we'll tell it apart from `Any?` and from Java's raw types, and check a value whose type nobody wrote down. Before we start, make a guess, and keep it in mind."""

S1 = """The shop's log printer has to accept every list in the shop: a `List<String>` of variety names, a `List<Int>` of weights, a `List<Apple>` from the storeroom. It never needs to know the element type. Kotlin's way to say that is a **star projection**, a `*` in place of the type argument:

```java
static void printAll(List<?> items) {
    for (Object item : items) System.out.println("  " + item);   // each item is an Object
}

printAll(varieties);   // a List<String>
printAll(weights);     // a List<Integer>
```

```kotlin
fun printAll(items: List<*>) {
    for (item in items) println("  $item")      // each item is Any?
}

printAll(varieties)    // a List<String>
printAll(weights)      // a List<Int>
```

Read `List<*>` as "a list of some specific type, and I don't know which". The list really does have one element type, the way the worn box really does hold one kind of thing. You've only lost the label. Java writes the same idea as `List<?>`, the **unbounded wildcard**: a `?` with no `extends` or `super` after it.

What can you do with a list of an unknown type? Ask the same two questions as in the last lesson. Taking things out is safe, but all you know about each element is that it's *something*, so it comes out as `Any?` (in Java, `Object`). Putting things in is not safe. The list might be a `MutableList<Int>` of weights, so no `String` may go in. Kotlin doesn't even let `null` in, because the unknown type might be one that never holds null:

```text
unlabeled.add("Eureka")
error: receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.

unlabeled.add(null)
error: null cannot be a value of a non-null type 'CapturedType(*)'.

val name: String = unlabeled[0]
error: initializer type mismatch: expected 'String', actual 'CapturedType(*)'.
```

`CapturedType(*)` is the captured type from lesson 6, the compiler's placeholder for "the one real element type of this list". Java is more relaxed about one of these errors. `add(null)` compiles on a `List<?>`, because every Java reference type allows null, and `StarListDemoJava` prints `after add(null): [null]`. `add("Eureka")` fails in Java too, with `String cannot be converted to CAP#1`. Java waves `null` through. Kotlin doesn't even let that in.

Everything that doesn't take an element still works: `size`, `isEmpty()`, `removeAt(0)` and `clear()`. So a function that empties any crate can take a `MutableList<*>`:

```java
static int empty(List<?> crate) { int n = crate.size(); crate.clear(); return n; }
```

```kotlin
fun empty(crate: MutableList<*>): Int { val n = crate.size; crate.clear(); return n }
```

`StarListDemo` empties a list of names and a list of weights with it, and prints `first = Gala, emptied 2 names and 3 weights`. This is the `drain` function in this lesson's lab.

**When a function doesn't care about the element type, say so with `*`. It may take out `Any?`, and put nothing in.**

So far, the star has always meant `Any?` on the way out. That's because `List`'s type parameter has no bound. Give a type parameter a sign that says "fruit only", and the star remembers it."""

S2 = """Here are three old friends from this track, each with a star. The `Dispenser` from lesson 4 hands fruit out, and this time its type parameter carries the "fruit only" bound from lesson 2. The `Bin` from lesson 5 takes items in. The `Box` from lesson 1 does both. What can you do with a `Dispenser<*>`, a `Bin<*>` and a `Box<*>`?

Take the dispenser first. A `Dispenser<*>` might be a `Dispenser<Apple>` or a `Dispenser<Lemon>`. Whichever it is, `next()` returns some `Fruit`, because the bound says so, and `Fruit` is the most the compiler can promise. The label is gone, but the "fruit only" sign was painted on the box itself, and it survives.

Now take the bin. A `Bin<*>` might be a `Bin<Fruit>`, a `Bin<Apple>` or a `Bin<String>`. No value is accepted by every one of them, so the compiler allows none. `Nothing` is Kotlin's name for a type with no values at all, which is exactly that answer. Both answers come from the substitution test, asked about every type the star could stand for.

So a `*` is shorthand for the safest projection that the declaration allows, and what it means depends on the declared variance. The Kotlin docs give three rules:

- For `Dispenser<out T : Fruit>`, `Dispenser<*>` means `Dispenser<out Fruit>`. You can take items out, and reads keep the bound: you get a `Fruit`, not an `Any?`.
- For `Bin<in T>`, `Bin<*>` means `Bin<in Nothing>`. No value has type `Nothing`, so you can't drop anything in at all.
- For an invariant `Box<T>`, `Box<*>` means `Box<out Any?>` when you read, and `Box<in Nothing>` when you write. (With a bound, `Box<T : Fruit>`, reads would give `Fruit`.)

```java
interface Dispenser<T extends Fruit> { T next(); }
interface Bin<T> { void drop(T item); }

static Fruit peek(Dispenser<?> dispenser) { return dispenser.next(); }   // the bound survives the ?

Bin<?> someBin = compost;
someBin.drop(new Apple("Fuji", 150));   // error: Apple cannot be converted to CAP#1
someBin.drop(null);                     // compiles in Java
```

```kotlin
interface Dispenser<out T : Fruit> { fun next(): T }
interface Bin<in T> { fun drop(item: T) }

fun peek(dispenser: Dispenser<*>): Fruit = dispenser.next()   // the bound survives the *

val someBin: Bin<*> = compost
someBin.drop(Apple("Fuji", 150))        // error: receiver type 'Bin<*>' contains star projection which prohibits ...
```

`StarRulesDemo` prints `peek(dispenser) = Gala, peek(box) = 180`. The box case shows the `Nothing` plainly. Assign to the item of a `Box<*>`, and the compiler says what it expected: `assignment type mismatch: actual type is 'Int', but 'Nothing' was expected.`

With several type parameters, each star is projected on its own. `Map<*, *>` reads keys and values as `Any?`. A function type `(Int) -> String` is `Function1<in P, out R>`, so `Function1<*, String>` means `Function1<in Nothing, String>`. You can't call it, because no argument fits, but you know any result would be a `String`. `Function1<Int, *>` is the opposite: you can call it with an `Int`, and the result is `Any?`. The same reasoning rules out comparing through a `Comparable<*>`: `receiver type 'Comparable<*>' contains star projection which prohibits the use of 'fun compareTo(other: T): Int'.`

The figure puts the three rules side by side. A star is about not knowing. Two other types look as if they say the same thing, and neither does."""

S3 = """`MutableList<Any?>` is a list whose element type is exactly `Any?`, like the shop's drawer of odds and ends: a pencil, a number, nothing in particular. You can add anything to it. But `MutableList` is invariant, so a `MutableList<String>` is not a `MutableList<Any?>`, and a function that takes one won't accept the other:

```java
static void addPriceTag(List<Object> list) { list.add("price tag"); }
static int countItems(List<?> list) { return list.size(); }

addPriceTag(drawer);      // a List<Object>: fine
countItems(varieties);    // a List<String>: fine
addPriceTag(varieties);   // error: List<String> cannot be converted to List<Object>
```

```kotlin
fun addPriceTag(list: MutableList<Any?>) { list.add("price tag") }
fun countItems(list: MutableList<*>): Int = list.size

addPriceTag(drawer)       // a MutableList<Any?>: fine
countItems(varieties)     // a MutableList<String>: fine
addPriceTag(varieties)    // error: actual type is 'MutableList<String>', but 'MutableList<Any?>' was expected.
```

The worn-off label and the "anything" label are different boxes. The drawer says what it holds, anything at all, so anything may go in. The worn box holds one kind of thing that nobody remembers, so nothing may go in.

So choose by what the function does. If it adds arbitrary values, it needs a real `MutableList<Any?>`, and it can take only that. If it doesn't care about the element type, it takes `MutableList<*>`, and accepts every mutable list. For the read-only `List`, the difference disappears. `List` is covariant, so `List<Any?>` and `List<*>` accept the same arguments, and `StarVsAnyDemo` prints `a = [Gala], b = [Gala]`.

Java has a third option that Kotlin doesn't: the **raw type**, a generic type used with no type arguments at all. A raw `List` switches generic checking off. It exists so that code written before Java 5 added generics still compiles, and lesson 1 of this track watched one fail:

```java
@SuppressWarnings({"rawtypes", "unchecked"})
static void addRaw(List list) { list.add(42); }

addRaw(varieties);                // compiles: an Integer goes into a List<String>
String last = varieties.get(1);   // ClassCastException here, far from the bug
```

```kotlin
// Kotlin has no raw types. A Java raw List arrives in Kotlin as List<*>,
// so the same write is refused at compile time:
fun addRaw(list: MutableList<*>) { list.add(42) }   // error: ... prohibits the use of 'fun add(element: E): Boolean'
```

A raw type isn't a worn-off label. It's a box with the clerk sent home. `StarVsAnyDemoJava` prints `varieties = [Gala, 42] (looks fine so far)`, and then the `ClassCastException` at the read.

The Kotlin docs describe star projections as "very much like Java's raw types, but safe". In Java, write `List<?>` instead of a raw `List` whenever you mean "I don't know the type". It reads the same, and it keeps the clerk at the door.

**A list of anything and a list of something are different types. Write `Any?` only when the function really stores arbitrary values.**

So far, the star has been about parameters you declare. It earns its keep when a value arrives from outside, and you have to find out what it is."""

S4 = """Some values arrive with no useful type at all. Picture a supplier's delivery note, read from a text file by a general-purpose reader. The reader knows nothing about apples. It hands back nested maps and lists, typed `Any?`, and you find out what they are. (JSON, the common text format for notes like this, works exactly this way, and so do many older Java APIs.) The first check most people write doesn't compile:

```text
if (weights is List<Int>) println("a list of weights")
error: cannot check for instance of erased type 'List<Int>'.
```

At run time, a `List<Int>` and a `List<String>` are the same kind of `ArrayList` object, so the JVM can check the class and nothing more. That's the torn-off label that lesson 1 warned about, and lesson 8 of this track explains it in full. For now the rule is: check with a star, then check each element you use:

```java
static List<Integer> weightsIn(Object note) {
    List<Integer> out = new ArrayList<>();
    if (note instanceof List<?> list) {
        for (Object e : list) if (e instanceof Integer i) out.add(i);   // check every element
    }
    return out;
}
```

```kotlin
fun weightsIn(note: Any?): List<Int> {
    if (note !is List<*>) return emptyList()
    return note.mapNotNull { it as? Int }     // note is now a List<*>; check each element
}
```

The note in `IsCheckDemo` has a stray word in its list of weights, `listOf(180, "bruised", 150)`: somebody wrote down what they saw instead of what they weighed. `weightsIn` skips the word and prints `weights = [180, 150]`.

After the `!is List<*>` line returns early, the compiler **smart-casts** `note` to `List<*>` for the rest of the function: it treats `note` as a `List<*>` without an explicit cast, because it has just checked. A `when` with `is List<*>` and `is Map<*, *>` branches does the same in each branch, and the demo's `shape` function uses one. Java's `instanceof List<?> list`, pattern matching for `instanceof` (final since Java 16), gives you the same kind of typed variable. Java's error for the bad check is `Object cannot be safely cast to List<Integer>`.

One full check does compile: when the compiler already knows the type argument. With `c: Collection<String>`, `c is List<String>` is fine, because only the class part needs checking at run time.

The shortcut to avoid is `note as List<Int>`. It compiles with an unchecked-cast warning, and it succeeds for any list at all. The `ClassCastException` comes later, at whichever line first reads `"bruised"` as an `Int`. Checking the elements costs one line, and it fails in the right place.

Better still, avoid the untyped route when you can. Many readers can fill a class of your own directly, such as a `DeliveryNote` with a `weights: List<Int>` property, so the checking happens once, inside the library. Lesson 9 of this track shows the type tokens that make this work for generic targets such as `List<Apple>`."""

CLOSING = """We started with a box whose label had worn off. `List<*>` is that box. You may take things out as `Any?`, or as the bound when the type carries a "fruit only" sign. You may count it and empty it. You may put nothing in. `MutableList<Any?>` is a different box, the drawer that takes anything, and a raw type is a box with no clerk at all.

Now look in your own code for a parameter typed `MutableList<Any?>`, `Map<Any?, Any?>` or a Java raw `List`. If the function never adds arbitrary values, it wants a star.

Next, we'll find out why `is List<Int>` can't compile. What exactly happens to the label after the compiler checks it?"""

L = {
    "id": "gen-07",
    "title": "Star projection: when you don't know the type",
    "minutes": 35,
    "goal": "By the end you can use `List<*>`, `MutableList<*>` and `Map<*, *>` for values whose type argument you don't know, predict what `*` allows for out, in and invariant type parameters, tell it apart from `Any?` and from Java's raw types, and write safe `is` checks.",
    "opening": OPENING,
    "warmup": {
        "q": "`val unlabeled: MutableList<*> = mutableListOf(\"Gala\", \"Fuji\")`. Which of these lines compiles?",
        "options": [
            "`unlabeled.add(\"Eureka\")`, because the list really holds strings",
            "`unlabeled.add(null)`, because `*` means `Any?`",
            "`unlabeled.clear()`",
            "None of them: a star-projected list is read-only"
        ],
        "answer": 2,
        "why": "Through `MutableList<*>`, the compiler doesn't know the element type, so it refuses every call that puts an element in, even `null`, because the unknown type might be non-nullable. `clear()` takes no element, so it compiles. A star projection limits which values go in; it doesn't make the list read-only."
    },
    "sections": [
        {
            "h": "A box with a worn-off label: List<*> is a list of some type you don't know",
            "body": S1,
            "try": {
                "title": "Print and empty lists of any type",
                "minutes": 4,
                "steps": [
                    "Run `StarListDemo` and `StarListDemoJava`. Compare the last line of the Java output with Kotlin's wrong move 2.",
                    "In `StarListDemo.kt`, predict the error for each of the three wrong moves. Uncomment them one at a time and run.",
                    "In the Java twin, uncomment wrong moves 1 and 3. Which Kotlin error has no Java twin?"
                ],
                "code": kdemo("StarListDemo", "StarListDemoJava"),
                "expect": "Both print the two names and the three weights, then `first = Gala, emptied 2 names and 3 weights`. Java also prints `after add(null): [null]`. Kotlin's wrong moves fail with `Receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.`, `Null cannot be a value of a non-null type 'CapturedType(*)'.` and `Initializer type mismatch: expected 'String', actual 'CapturedType(*)'.` Java's fail with `String cannot be converted to CAP#1` and `CAP#1 cannot be converted to String`. The `add(null)` error has no Java twin."
            },
            "refs": [
                {"title": "Generics: star-projections (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "What the star stands for depends on how the type parameter is declared",
            "body": S2,
            "figure": {"svg": FIG, "caption": "A star becomes the safest projection: the bound for taking from an out type, Nothing for putting into an in or invariant one."},
            "try": {
                "title": "Take from a Dispenser<*>, try to fill a Bin<*>",
                "minutes": 4,
                "steps": [
                    "Before running `StarRulesDemo`, predict the static type of `peek(apples)`: `Any?`, `Fruit` or `Apple`?",
                    "Run it (or `StarRulesDemoJava`).",
                    "Uncomment the three wrong moves one at a time. Which message mentions `Nothing`?"
                ],
                "code": kdemo("StarRulesDemo", "StarRulesDemoJava"),
                "expect": "Both print `peek(dispenser) = Gala, peek(box) = 180`, `compost: Eureka` and `a Box<*> still reads: 180` (`Box<?>` in Java). Java also prints `compost: null`, because `drop(null)` is allowed through `?`. The static type of `peek(apples)` is `Fruit`: the bound survives the star. Kotlin errors: (1) `Receiver type 'Bin<*>' contains star projection which prohibits the use of 'fun drop(item: T): Unit'.`, (2) `Assignment type mismatch: actual type is 'Int', but 'Nothing' was expected.`, (3) `Initializer type mismatch: expected 'Apple', actual 'Fruit'.` Java: `Apple cannot be converted to CAP#1`, `int cannot be converted to CAP#1`, then `Fruit cannot be converted to Apple`."
            }
        },
        {
            "h": "A worn-off label is not an \"anything\" label, and not a raw type",
            "body": S3,
            "try": {
                "title": "Compare Any?, * and a raw type",
                "minutes": 4,
                "steps": [
                    "Run `StarVsAnyDemo` and `StarVsAnyDemoJava`. Find the line in the Java output where the raw type's damage shows up.",
                    "Uncomment the wrong move in either file, predict, run.",
                    "In `StarVsAnyDemo.kt`, change `addPriceTag`'s parameter to `MutableList<*>` and uncomment the wrong move. Which line breaks now, and why?"
                ],
                "code": kdemo("StarVsAnyDemo", "StarVsAnyDemoJava"),
                "expect": "Kotlin prints `drawer = [pencil, 3, null, price tag], countItems(varieties) = 1, countItems(drawer) = 4` and `a = [Gala], b = [Gala]`. Java prints `varieties = [Gala, 42] (looks fine so far)` and then `ClassCastException at the read: class java.lang.Integer cannot be cast to class java.lang.String ...`. The wrong move fails with `Argument type mismatch: actual type is 'MutableList<String>', but 'MutableList<Any?>' was expected.` (Java: `List<String> cannot be converted to List<Object>`). With `MutableList<*>`, `addPriceTag(varieties)` compiles, but `list.add(\"price tag\")` inside it fails: a star projection forbids adding."
            }
        },
        {
            "h": "Checking an unknown value: is List<*> first, then each element",
            "body": S4,
            "try": {
                "title": "Pick apart an untyped delivery note",
                "minutes": 4,
                "steps": [
                    "Run `IsCheckDemo` (or `IsCheckDemoJava`). The note's list of weights contains a stray `\"bruised\"`.",
                    "Uncomment the wrong move, predict, run.",
                    "Replace `it as? Int` with `it as Int` and run again. Where does it fail, and is that where the bad data came from?"
                ],
                "code": kdemo("IsCheckDemo", "IsCheckDemoJava"),
                "expect": "Both print `a map with keys [supplier, weights]`, `a list of 3`, `a single value: 42` and `weights = [180, 150]`: the stray word is skipped. The wrong move fails with `Cannot check for instance of erased type 'List<Int>'.` (Java: `Object cannot be safely cast to List<Integer>`). With `as Int`, the run fails with `ClassCastException: class java.lang.String cannot be cast to class java.lang.Integer` inside `weightsIn`, far from wherever the note was written."
            }
        }
    ],
    "compare": {
        "title": "Unknown type arguments: Kotlin's * and Java's ?",
        "java": {
            "title": "ShopLog.java",
            "src": "import java.util.Comparator;\nimport java.util.List;\nimport java.util.Map;\nimport java.util.stream.Collectors;\n\nfinal class ShopLog {\n    static String describe(Object value) {\n        if (value == null) return \"nothing\";\n        if (value instanceof String s) return \"text \" + s;\n        if (value instanceof List<?> l) return \"list of \" + l.size();    // List<String> would not compile\n        if (value instanceof Map<?, ?> m) return \"map of \" + m.size();\n        return \"other\";\n    }\n\n    static String render(Map<?, ?> map) {                                 // keys and values are Object\n        return map.entrySet().stream()\n            .sorted(Comparator.comparing(e -> String.valueOf(e.getKey())))\n            .map(e -> e.getKey() + \"=\" + (e.getValue() instanceof Map<?, ?> m ? render(m) : e.getValue()))\n            .collect(Collectors.joining(\", \", \"{\", \"}\"));\n    }\n\n    static int drain(List<?> crate) {     // not a raw List: checks stay on\n        int n = crate.size();\n        crate.clear();\n        return n;\n    }\n}"
        },
        "kotlin": {
            "title": "ShopLog.kt",
            "src": "fun describe(value: Any?): String = when (value) {\n    null -> \"nothing\"\n    is String -> \"text $value\"\n    is List<*> -> \"list of ${value.size}\"       // List<String> would not compile\n    is Map<*, *> -> \"map of ${value.size}\"\n    else -> \"other\"\n}\n\nfun render(map: Map<*, *>): String =                // keys and values are Any?\n    map.entries\n        .sortedBy { it.key.toString() }\n        .joinToString(\", \", \"{\", \"}\") { (k, v) -> \"$k=${if (v is Map<*, *>) render(v) else v}\" }\n\nfun drain(crate: MutableList<*>): Int {           // Kotlin has no raw types\n    val n = crate.size\n    crate.clear()\n    return n\n}"
        },
        "note": "Kotlin's `MutableList<*>` compiles to Java's `List<?>`, and the two behave almost the same: reads give `Any?` or `Object`, writes of real values are refused, and members that take no element still work. Three things differ. Java lets you pass `null` through a `?`; Kotlin refuses, because the unknown type might be non-nullable. Java still has raw types, which switch checking off; Kotlin has none, and shows a Java raw `List` as `List<*>`. And Kotlin works out what `*` means from the declaration's variance, so a star on an `in` parameter becomes `in Nothing`, and a star on an `out T : Fruit` keeps the `Fruit` bound, while Java applies the same capture rules to every wildcard."
    },
    "worked": {
        "title": "Render an untyped delivery note for the shop log",
        "steps": [
            {"say": "A supplier's delivery note is read into a map whose types you don't control. The first draft of the log renderer asks for `Map<Any?, Any?>`, to be \"as general as possible\". In a test, the note is a `Map<String, Int>`. Read the error.",
             "code": "fun render(map: Map<Any?, Any?>): String = map.toString()\n\nval note: Map<String, Int> = mapOf(\"crates\" to 4)\nrender(note)\n// error: argument type mismatch: actual type is 'Map<String, Int>', but 'Map<Any?, Any?>' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<Object, Object> map) { return map.toString(); }\n\nMap<String, Integer> note = Map.of(\"crates\", 4);\nrender(note);\n// error: incompatible types: Map<String,Integer> cannot be converted to Map<Object,Object>"},
            {"say": "`Map<K, out V>` is covariant in `V` but invariant in `K`, so a `Map<String, Int>` is not a `Map<Any?, Any?>`. The renderer never puts anything into the map; it only reads. So it doesn't need to name either type. Use one star per type parameter.",
             "code": "fun render(map: Map<*, *>): String =\n    map.entries\n        .sortedBy { it.key.toString() }      // 1. keys are Any?: toString() works, even on null\n        .joinToString(\", \", \"{\", \"}\") { (k, v) -> \"$k=$v\" }",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<?, ?> map) {\n    return map.entrySet().stream()\n        .sorted(Comparator.comparing(e -> String.valueOf(e.getKey())))   // 1. keys are Object\n        .map(e -> e.getKey() + \"=\" + e.getValue())\n        .collect(Collectors.joining(\", \", \"{\", \"}\"));\n}"},
            {"say": "Notes nest: the `apple` field is itself a map. Check the value's shape with a star, and the smart cast gives you a `Map<*, *>` to render the same way. Self-check before reading the comment: why not `v is Map<String, Any?>`? (Type arguments are erased, so the compiler refuses that check.)",
             "code": "fun render(map: Map<*, *>): String =\n    map.entries\n        .sortedBy { it.key.toString() }\n        .joinToString(\", \", \"{\", \"}\") { (k, v) ->\n            val shown = if (v is Map<*, *>) render(v) else v.toString()   // 2. smart cast to Map<*, *>\n            \"$k=$shown\"\n        }\n\nrender(mapOf(\"crates\" to 4, \"apple\" to mapOf(\"name\" to \"Gala\", \"grams\" to 180)))\n// {apple={grams=180, name=Gala}, crates=4}",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<?, ?> map) {\n    return map.entrySet().stream()\n        .sorted(Comparator.comparing(e -> String.valueOf(e.getKey())))\n        .map(e -> e.getKey() + \"=\"\n            + (e.getValue() instanceof Map<?, ?> m ? render(m) : e.getValue()))   // 2. pattern match\n        .collect(Collectors.joining(\", \", \"{\", \"}\"));\n}"},
            {"say": "Now any map fits: a `Map<String, Int>`, a `Map<String, Any?>`, the `Map<*, *>` that a file reader returns, or a map with `Int` keys. The renderer is honest about what it knows. This is the `render` function in the lab, and the tests check exactly this output."}
        ]
    },
    "lab": {
        "title": "Describe, render and drain values of unknown type",
        "minutes": 13,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l07/Describe.kt",
            f"{LAB}/main/kotlin/workbench/generics/l07/MapPrinter.kt",
            f"{LAB}/main/java/workbench/generics/l07/Nulls.java"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l07.*'",
        "steps": [
            "Run the tests. All nine fail. The two signature tests show what Java sees today: `but was: \"List<Object>\"` for `drain` and `but was: \"List\"` (a raw type) for `countNulls`.",
            "In `Describe.kt`, write `describe` as one `when (value)`, with the branches in the order the KDoc lists them.",
            "Write `stringsIn`: return early unless `value is List<*>`, then keep the elements that are `String`s.",
            "Fix `drain`'s parameter type so any mutable list fits, then clear it and return the old size.",
            "In `MapPrinter.kt`, write `render`. Sort the entries by `key.toString()`, and render values that are `Map<*, *>` the same way.",
            "In `Nulls.java`, change the raw `List` to `List<?>`, remove the `@SuppressWarnings`, and count the nulls. Run until all nine pass."
        ],
        "hints": [
            "`when (value) { null -> ...; is String -> ...; is List<*> -> ...; is Map<*, *> -> ...; is Number -> ...; else -> ... }`. Each branch smart-casts `value`.",
            "In `stringsIn`, `for (e in value) if (e is String) out += e`: each element is `Any?` until you check it.",
            "`map.entries.sortedBy { it.key.toString() }.joinToString(\", \", \"{\", \"}\") { (k, v) -> ... }` does most of `render`.",
            "Why does `drain` need `*` and not `Any?`? `MutableList<Any?>` is invariant, so it only accepts lists whose element type is exactly `Any?`."
        ],
        "done_when": "All nine tests in `StarProjectionTest` pass."
    },
    "drill": {
        "title": "What does each star allow?",
        "minutes": 4,
        "prompt": "Close this page. Declare `interface Dispenser<out T : Fruit> { fun next(): T }`, `interface Bin<in T> { fun drop(item: T) }` and `class Box<T>(var item: T)`. Write one function that takes a `Dispenser<*>`, a `Bin<*>`, a `Box<*>` and a `MutableList<*>`, and does the one legal thing with each. In a comment, say what each star stands for. Then write the Java version, which has one extra legal call.",
        "answer": {
            "lang": "kotlin",
            "src": "interface Dispenser<out T : Fruit> { fun next(): T }\ninterface Bin<in T> { fun drop(item: T) }\nclass Box<T>(var item: T)\n\nfun drill(d: Dispenser<*>, b: Bin<*>, x: Box<*>, l: MutableList<*>) {\n    val f: Fruit = d.next()    // Dispenser<*> = Dispenser<out Fruit>: reads keep the bound\n    // b.drop(...)             // Bin<*> = Bin<in Nothing>: nothing can be dropped in\n    val i: Any? = x.item       // Box<*> reads as Box<out Any?> (and writes as Box<in Nothing>)\n    l.clear()                  // MutableList<*>: members that take no element still work\n}",
            "alt": {"lang": "java", "title": "Drill.java", "src": "interface Dispenser<T extends Fruit> { T next(); }\ninterface Bin<T> { void drop(T item); }\nclass Box<T> { T item; }\n\nstatic void drill(Dispenser<?> d, Bin<?> b, Box<?> x, List<?> l) {\n    Fruit f = d.next();    // the bound survives the ?\n    b.drop(null);          // the extra legal call: Java lets null through a ?\n    Object i = x.item;     // reads as Object\n    l.clear();             // takes no element\n}"}
        }
    },
    "recap": [
        "`List<*>` means a list of one specific element type that you don't know, like a box whose label wore off. Reads give `Any?`, and Java writes it `List<?>`.",
        "Through a star projection you can't put an element in. Kotlin refuses even `null`; Java allows `null`.",
        "`*` becomes the safest projection: `out Bound` for an out type parameter, `in Nothing` for an in one, and both for an invariant one.",
        "`MutableList<Any?>` is a list of exactly `Any?`, and it rejects a `MutableList<String>`; `MutableList<*>` accepts every mutable list. Java's raw types switch checking off. Kotlin has none, and shows a Java raw `List` as `List<*>`.",
        "Check unknown values with `is List<*>` or `is Map<*, *>`, then check each element with `is` or `as?`.",
        "The limit: neither the star nor the JVM can tell you what's inside. `is List<Int>` doesn't compile, because the type argument is gone at run time."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "`val unlabeled: MutableList<*> = mutableListOf(\"Gala\")`. Which line compiles?",
            "options": [
                "`unlabeled.add(\"Fuji\")`",
                "`unlabeled.add(null)`",
                "`unlabeled.removeAt(0)`",
                "`val s: String = unlabeled[0]`"
            ],
            "answer": 2,
            "why": "`removeAt` takes an index, not an element, so the star doesn't block it. Both `add` calls put an element of the unknown type in, which Kotlin refuses, even `null`, since the type might be non-nullable. A read gives only `CapturedType(*)`, which is not known to be a `String`."
        },
        {
            "q": "`interface Dispenser<out T : Fruit> { fun next(): T }` and `fun f(d: Dispenser<*>)`. What is the static type of `d.next()` inside `f`?",
            "options": [
                "`Fruit`",
                "`Any?`",
                "`Nothing`",
                "It doesn't compile: you can't call anything on a star projection"
            ],
            "answer": 0,
            "why": "For an `out` type parameter with a bound, `Dispenser<*>` means `Dispenser<out Fruit>`, so reads keep the bound. `Any?` is what you'd get with no bound. `Nothing` is what a star gives on the putting-in side of an in or invariant type parameter."
        },
        {
            "q": "You need a function that adds a \"price tag\" string to whatever list a caller passes: a `MutableList<String>`, a `MutableList<Any>` or a `MutableList<CharSequence>`. Which parameter type fits?",
            "options": [
                "`MutableList<*>`",
                "`MutableList<Any?>`",
                "`List<Any?>`",
                "`MutableList<in String>`"
            ],
            "answer": 3,
            "why": "The function puts `String`s in and never reads, so it is a consumer: `MutableList<in String>` accepts lists of `String` or of any supertype. A star forbids `add`. `MutableList<Any?>` accepts only lists of exactly `Any?`. `List` has no `add` at all. Use `*` when you neither read typed values nor write, and `in` when you write."
        },
        {
            "q": "Java: `List<String> varieties = new ArrayList<>(List.of(\"Gala\")); List raw = varieties; raw.add(42);` Then `String s = varieties.get(1);`. What happens?",
            "options": [
                "A compile error at `raw.add(42)`",
                "It compiles (with an unchecked warning) and throws `ClassCastException` at `varieties.get(1)`",
                "It throws `ArrayStoreException` at `raw.add(42)`",
                "It runs fine and `s` is `\"42\"`"
            ],
            "answer": 1,
            "why": "A raw type turns generic checking off, so the `Integer` goes in, and the `ArrayList` can't notice, because its type argument is gone at run time. The cast that javac inserted at `varieties.get(1)` fails, far from the bad write. `ArrayStoreException` is the array version of this check, which lists don't have. In Kotlin, the same write fails to compile, because a raw `List` is seen as `List<*>`."
        },
        {
            "q": "From \"Use-site variance and type projections\": which signature lets `copyAll` copy a `MutableList<Apple>` into a `MutableList<Fruit>`?",
            "options": [
                "`fun <T> copyAll(from: MutableList<out T>, to: MutableList<in T>)`",
                "`fun copyAll(from: MutableList<*>, to: MutableList<*>)`",
                "`fun <T> copyAll(from: MutableList<T>, to: MutableList<T>)`",
                "`fun copyAll(from: MutableList<Any?>, to: MutableList<Any?>)`"
            ],
            "answer": 0,
            "why": "`from` only gives values (`out T`) and `to` only takes them (`in T`), so `T = Apple` works with a `MutableList<Fruit>` target. With stars, `to.add(x)` is forbidden. Plain `T` forces both lists to the same element type, and `MutableList<Any?>` rejects both arguments.",
            "from": "gen-06"
        }
    ],
    "flashcards": [
        {"front": "What does `List<*>` mean?", "back": "A list of one specific element type that you don't know or don't care about. Reads come out as `Any?`. Java's spelling is `List<?>`."},
        {"front": "Can you call `add(null)` on a `MutableList<*>`?", "back": "Not in Kotlin: `Null cannot be a value of a non-null type 'CapturedType(*)'.` Java's `List<?>` does allow `add(null)`."},
        {"front": "For `interface Bin<in T>`, what does `Bin<*>` mean?", "back": "`Bin<in Nothing>`: no value fits, so you can't call `drop` at all."},
        {"front": "For `interface Dispenser<out T : Fruit>`, what does `Dispenser<*>` mean?", "back": "`Dispenser<out Fruit>`: reads give `Fruit`, because the bound survives the star."},
        {"front": "Why does `fun f(l: MutableList<Any?>)` reject a `MutableList<String>`?", "back": "`MutableList` is invariant, and `Any?` is one specific type argument. Use `MutableList<*>` if `f` doesn't need to add."},
        {"front": "How does Kotlin see a Java parameter of raw type `List`?", "back": "As a star projection, `List<*>`, so Kotlin code can't write unchecked elements into it."},
        {"front": "`note: Any?`. Why `note is List<*>` and not `note is List<Int>`?", "back": "Type arguments are erased at run time, so the JVM can only check the class. Check with a star, then check each element."}
    ],
    "terms": [
        {"term": "Star projection", "plain": "`C<*>`: a `C` of some type argument you don't know. Kotlin picks the safest projection for it."},
        {"term": "Unbounded wildcard", "plain": "Java's `?` with no bound, as in `List<?>`: the Java twin of `*`."},
        {"term": "Raw type", "plain": "A Java generic type used with no type arguments at all (`List`). Generic checks are off for it."},
        {"term": "in Nothing", "plain": "What a star means on the putting-in side: only a `Nothing` could go in, and no such value exists."},
        {"term": "Smart cast", "plain": "After `if (x is List<*>)`, the compiler treats `x` as a `List<*>` without an explicit cast."},
        {"term": "Erased type", "plain": "A type argument that exists only at compile time. At run time a `List<String>` is just a `List`."}
    ],
    "explain_back": {
        "prompt": "A teammate wrote `fun logNote(fields: Map<Any?, Any?>)`, and now every caller with a `Map<String, Int>` gets a type error. They ask whether `Map<*, *>` is just a shorter way to write `Map<Any?, Any?>`. Explain the difference in your own words.",
        "answer": "`Map<Any?, Any?>` is one specific type: a map whose keys and values are declared as `Any?`. Because `Map` is invariant in its key type, a `Map<String, Int>` is not that type, so callers get an error. `Map<*, *>` means \"a map of some key type and some value type that I don't know\", like a box whose label wore off. Every map fits it. In exchange, the function can only do things that are safe for any key and value type: read keys and values as `Any?`, ask for the size, go through the entries. It can't store a key or a value of the unknown type. A logging function only reads, so `Map<*, *>` is the honest type. `Map<Any?, Any?>` only makes sense for a map that really holds arbitrary keys and values."
    },
    "deeper": {
        "minutes": 10,
        "body": "Kotlin can still call a generic function with a star-projected argument. Given `fun <T> swap(l: MutableList<T>, i: Int, j: Int)`, the call `swap(unlabeled, 0, 1)` with `unlabeled: MutableList<*>` compiles with kotlinc 2.4.21 and swaps the two elements. The compiler captures the unknown element type as `T` for that one call, so inside `swap` a value read from the list may be written back into the same list. Java does the same with a private helper method, the \"capture helper\" pattern; the JDK's `Collections.swap(List<?> list, int i, int j)` skips it and uses a raw type under `@SuppressWarnings`.\n\nThe `Map` interface has a detail worth knowing. It is declared `Map<K, out V>`, invariant in `K`. So on a `Map<*, *>`, the member `get(key: K)` would take `in Nothing`, and you could never look anything up. The standard library adds an extension, `Map<out K, V>.get(key: K)`, so `note[\"weights\"]` on a `Map<*, *>` still compiles and returns `Any?`.\n\nStars also appear in class literals: `Map::class.java` is a `Class<Map<*, *>>`, and `listOf(1)::class` is a `KClass<out List<Int>>`. The class object of a generic class exists once for all type arguments, so it can't carry them. Lesson 9 of this track is about exactly that. And in Kotlin's own reflection, `typeOf<List<*>>().arguments` prints `[*]`: the star is part of the type, not an absence of one."
    },
    "sources": [
        {"title": "Generics: star-projections (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Calling Java from Kotlin: Java generics in Kotlin (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-interop.html"},
        {"title": "JEP 394: Pattern Matching for instanceof", "url": "https://openjdk.org/jeps/394"}
    ]
}

out = ROOT / "content/lessons/gen-07.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
