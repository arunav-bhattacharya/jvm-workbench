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
    (44, "Source&lt;out T : Number&gt;", "Source&lt;out Number&gt;", "get: Number", "box-ok"),
    (110, "Sink&lt;in T&gt;", "Sink&lt;in Nothing&gt;", "accept(x): nothing fits", "box-bad"),
    (176, "Box&lt;T&gt;  (invariant)", "Box&lt;out Any?&gt; / Box&lt;in Nothing&gt;", "get: Any?, set: nothing", "box-dim"),
]
FIG = ('<svg viewBox="0 0 700 270" role="img" aria-label="What a star projection means for three declarations. For Source declared out T with bound Number, '
       'Source of star means Source of out Number, so reads give Number. For Sink declared in T, Sink of star means Sink of in Nothing, so nothing can be passed in. '
       'For an invariant Box, Box of star reads as out Any? and writes as in Nothing.">'
       '<text class="t-s t-m" x="125" y="28" text-anchor="middle">declared as</text>'
       '<text class="t-s t-m" x="365" y="28" text-anchor="middle">the * stands for</text>'
       '<text class="t-s t-m" x="595" y="28" text-anchor="middle">what you can do</text>')
for y, decl, star, can, cls in ROWS:
    FIG += cell(15, y, 220, decl, "box")
    FIG += f'<line class="ln-a" x1="237" y1="{y + 20}" x2="252" y2="{y + 20}" marker-end="url(#arr)"/>'
    FIG += cell(255, y, 220, star, "box-a")
    FIG += f'<line class="ln-a" x1="477" y1="{y + 20}" x2="492" y2="{y + 20}" marker-end="url(#arr)"/>'
    FIG += cell(495, y, 190, can, cls)
FIG += ('<text class="t-s t-m" x="350" y="252" text-anchor="middle">Each * becomes the safest projection that the declaration allows.</text>'
        '</svg>')

S1 = """A logging helper has to accept every list in the codebase: a `List<String>` of payment ids, a `List<Int>` of amounts, a `List<Settlement>`. It never needs to know the element type. Kotlin's way to say that is a **star projection**:

```java
static void logAll(List<?> items) {
    for (Object item : items) System.out.println("  " + item);   // each item is an Object
}

logAll(ids);      // List<String>
logAll(cents);    // List<Integer>
```

```kotlin
fun logAll(items: List<*>) {
    for (item in items) println("  $item")      // each item is Any?
}

logAll(ids)       // List<String>
logAll(cents)     // List<Int>
```

Read `List<*>` as "a list of some specific type, and I don't know which". The list really does have one element type. You've chosen not to name it. Java writes the same idea as `List<?>`, the unbounded wildcard.

What can you do with a list of an unknown type? Ask the same two questions as in the last lesson. Reading is safe, but all you know is that each element is *something*, so it comes out as `Any?`. Writing is not safe: the list might be a `MutableList<Int>`, so no `String` may go in. Kotlin doesn't even let `null` in, because the unknown type might be non-nullable:

```text
star.add("pay_3")
Receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.

star.add(null)
Null cannot be a value of a non-null type 'CapturedType(*)'.

val id: String = star[0]
Initializer type mismatch: expected 'String', actual 'CapturedType(*)'.
```

Java is more relaxed about one of these. `add(null)` compiles on a `List<?>`, because every Java reference type allows null. `add("pay_3")` fails with `String cannot be converted to CAP#1`, the captured type from lesson 6.

Everything that doesn't take an element still works: `size`, `isEmpty()`, `removeAt(0)`, `clear()`. So a function that empties any buffer can take a `MutableList<*>`. That's the `drain` function in this lesson's lab."""

S2 = """A `*` is shorthand for the safest projection that the declaration allows, so what it means depends on the declared variance. The Kotlin docs give three rules:

- For `Source<out T : Number>`, `Source<*>` means `Source<out Number>`. You can read, and reads keep the bound: you get a `Number`, not an `Any?`.
- For `Sink<in T>`, `Sink<*>` means `Sink<in Nothing>`. No value has type `Nothing`, so you can't pass anything in at all.
- For an invariant `Box<T>`, `Box<*>` means `Box<out Any?>` when you read and `Box<in Nothing>` when you write. (With a bound, `Box<T : Payment>`, reads would give `Payment`.)

The rules come straight from the substitution question in lesson 4. A `Source<*>` might be a `Source<Int>` or a `Source<BigDecimal>`. Whichever it is, `next()` returns some `Number`, so `Number` is the most the compiler can promise. A `Sink<*>` might be a `Sink<String>` or a `Sink<CardAuthorized>`. No value is accepted by every one of them, so the compiler allows none. `Nothing` is Kotlin's name for a type with no values, which is exactly that answer.

```java
interface Source<T extends Number> { T next(); }
interface Sink<T> { void accept(T item); }

static Number peek(Source<?> source) { return source.next(); }   // the bound survives the ?

Sink<?> anySink = audit;
anySink.accept("pay_1");      // error: String cannot be converted to CAP#1
anySink.accept(null);         // compiles in Java
```

```kotlin
interface Source<out T : Number> { fun next(): T }
interface Sink<in T> { fun accept(item: T) }

fun peek(source: Source<*>): Number = source.next()   // the bound survives the *

val anySink: Sink<*> = audit
anySink.accept("pay_1")       // error: Receiver type 'Sink<*>' contains star projection which prohibits ...
```

The invariant case shows the `Nothing` plainly. Assign to the property of a `Box<*>` and the compiler says what it expected: `Assignment type mismatch: actual type is 'String', but 'Nothing' was expected.`

With several type parameters, each star is projected on its own. `Map<*, *>` reads keys and values as `Any?`. A function type `(Int) -> String` is `Function1<in P, out R>`, so `Function1<*, String>` is `Function1<in Nothing, String>`. You can't call it, because no argument fits, but you know any result would be a `String`. `Function1<Int, *>` is the opposite: you can call it with an `Int`, and the result is `Any?`. The same reasoning rules out comparing through a `Comparable<*>`: `Receiver type 'Comparable<*>' contains star projection which prohibits the use of 'fun compareTo(other: T): Int'.`

The figure puts the three rules side by side."""

S3 = """Two other types look like "a list of anything", and both differ from `*`.

`MutableList<Any?>` is a list whose element type is exactly `Any?`. You can add anything to it. But `MutableList` is invariant, so a `MutableList<String>` is not a `MutableList<Any?>`, and a function that takes one won't accept the other:

```java
static void addMarker(List<Object> list) { list.add("marker"); }
static int sizeOf(List<?> list) { return list.size(); }

addMarker(anything);   // a List<Object>: fine
sizeOf(ids);           // a List<String>: fine
addMarker(ids);        // error: List<String> cannot be converted to List<Object>
```

```kotlin
fun addMarker(list: MutableList<Any?>) { list.add("marker") }
fun sizeOf(list: MutableList<*>): Int = list.size

addMarker(anything)    // a MutableList<Any?>: fine
sizeOf(ids)            // a MutableList<String>: fine
addMarker(ids)         // error: actual type is 'MutableList<String>', but 'MutableList<Any?>' was expected.
```

So choose by what the function does. If it adds arbitrary values, it needs a real `MutableList<Any?>` and can only take one. If it doesn't care about the element type, it takes `MutableList<*>` and accepts every mutable list. For read-only `List` the difference disappears: `List` is covariant, so `List<Any?>` and `List<*>` accept the same arguments.

Java has a third option that Kotlin doesn't: the **raw type**. A raw `List`, with no angle brackets at all, switches generic checking off. It exists so that code written before Java 5 added generics still compiles:

```java
@SuppressWarnings({"rawtypes", "unchecked"})
static void addRaw(List list) { list.add(42); }

addRaw(ids);                 // compiles: an Integer goes into a List<String>
String last = ids.get(1);    // ClassCastException here, far from the bug
```

```kotlin
// Kotlin has no raw types. A Java raw List arrives in Kotlin as List<*>,
// so the same write is refused at compile time:
fun addRaw(list: MutableList<*>) { list.add(42) }   // error: ... prohibits the use of 'fun add(element: E): Boolean'
```

The Kotlin docs say star projections are "very much like Java's raw types, but safe". In Java, write `List<?>` instead of a raw `List` whenever you mean "I don't know the type". It reads the same and keeps the checks on."""

S4 = """JSON libraries, message headers and old Java APIs hand you values typed `Any?` or `Map<*, *>`. To use them, you check what they are. The first check most people write doesn't compile:

```text
if (amounts is List<Long>) println("a list of longs")
Cannot check for instance of erased type 'List<Long>'.
```

At run time a `List<Long>` and a `List<String>` are the same kind of `ArrayList` object, so the JVM can check the class and nothing more. Lesson 8 of this track explains erasure in full. For now the rule is: check with a star, then check each element you use.

```java
static List<Long> amountsIn(Object payload) {
    List<Long> out = new ArrayList<>();
    if (payload instanceof List<?> list) {
        for (Object e : list) if (e instanceof Long l) out.add(l);   // check every element
    }
    return out;
}
```

```kotlin
fun amountsIn(payload: Any?): List<Long> {
    if (payload !is List<*>) return emptyList()
    return payload.mapNotNull { it as? Long }     // payload is now a List<*>; check each element
}
```

After the `!is List<*>` line returns early, the compiler smart-casts `payload` to `List<*>` for the rest of the function. A `when` with `is List<*>` and `is Map<*, *>` branches does the same in each branch. Java's `instanceof List<?> list` (pattern matching for `instanceof`, final since Java 16) gives you the same kind of typed variable. Java's error for the bad check is `Object cannot be safely cast to List<Long>`.

One full check does compile: when the compiler already knows the type argument. With `c: Collection<String>`, `c is List<String>` is fine, because only the class part needs checking at run time.

The shortcut to avoid is `payload as List<Long>`. It compiles with an unchecked-cast warning and succeeds for any list at all. The `ClassCastException` comes later, at whichever line first reads a `String` as a `Long`. Checking the elements costs one line and fails in the right place.

Better still, avoid the untyped route when you can. Ask the JSON library to bind the body to a data class, and the checking happens once, inside the library. Lesson 9 of this track shows how type tokens make that work for generic targets such as `List<Settlement>`."""

L = {
    "id": "gen-07",
    "title": "Star projection: when you don't know the type",
    "minutes": 35,
    "goal": "By the end you can use `List<*>`, `MutableList<*>` and `Map<*, *>` for values whose type argument you don't know, predict what `*` allows for out, in and invariant parameters, tell it apart from `Any?` and from Java's raw types, and write safe `is` checks.",
    "warmup": {
        "q": "`val buffer: MutableList<*> = mutableListOf(\"pay_1\", \"pay_2\")`. Which of these lines compiles?",
        "options": [
            "`buffer.add(\"pay_3\")`, because the list really holds strings",
            "`buffer.add(null)`, because `*` means `Any?`",
            "`buffer.clear()`",
            "None of them: a star-projected list is read-only"
        ],
        "answer": 2,
        "why": "Through `MutableList<*>` the compiler doesn't know the element type, so it refuses every call that passes an element in, even `null` (the unknown type might be non-nullable). `clear()` takes no element, so it compiles. A star projection limits which values go in; it does not make the list read-only."
    },
    "sections": [
        {
            "h": "List<*> is a list of some type you don't know",
            "body": S1,
            "try": {
                "title": "Log and empty lists of any type",
                "minutes": 4,
                "steps": [
                    "Run `StarListDemo` and `StarListDemoJava`. Compare the last line of the Java output with Kotlin's wrong move 2.",
                    "In `StarListDemo.kt`, predict the error for each of the three wrong moves. Uncomment them one at a time and run.",
                    "In the Java twin, uncomment wrong moves 1 and 3. Which Kotlin error has no Java twin?"
                ],
                "code": kdemo("StarListDemo", "StarListDemoJava"),
                "expect": "Both log the two ids and the three amounts, then print `first = pay_1, removed 2 ids and 3 amounts`. Java also prints `after add(null): [null]`. Kotlin's wrong moves fail with `Receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.`, `Null cannot be a value of a non-null type 'CapturedType(*)'.` and `Initializer type mismatch: expected 'String', actual 'CapturedType(*)'.` Java's fail with `String cannot be converted to CAP#1` and `CAP#1 cannot be converted to String`. The `add(null)` error has no Java twin."
            },
            "refs": [
                {"title": "Generics: star-projections (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "What * stands for depends on how the parameter is declared",
            "body": S2,
            "figure": {"svg": FIG, "caption": "A star is replaced by the safest projection: the bound for reading an out parameter, Nothing for writing an in or invariant one."},
            "try": {
                "title": "Read a Source<*>, try to feed a Sink<*>",
                "minutes": 4,
                "steps": [
                    "Before running `StarRulesDemo`, predict the static type of `peek(amounts)`: `Any?`, `Number` or `Int`?",
                    "Run it (or `StarRulesDemoJava`).",
                    "Uncomment the three wrong moves one at a time. Which message mentions `Nothing`?"
                ],
                "code": kdemo("StarRulesDemo", "StarRulesDemoJava"),
                "expect": "Both print `peek(source) = 1200, peek(box) = EUR`, `audit pay_0` and `a Box<*> still reads: EUR` (`Box<?>` in Java). Java also prints `audit null`, because `accept(null)` is allowed through `?`. The static type of `peek(amounts)` is `Number`: the bound survives the star. Kotlin errors: (1) `Receiver type 'Sink<*>' contains star projection which prohibits the use of 'fun accept(item: T): Unit'.`, (2) `Assignment type mismatch: actual type is 'String', but 'Nothing' was expected.`, (3) `Initializer type mismatch: expected 'Int', actual 'Number'.` Java: `String cannot be converted to CAP#1` twice, then `Number cannot be converted to Integer`."
            }
        },
        {
            "h": "* is not Any?, and it is not a raw type",
            "body": S3,
            "try": {
                "title": "Compare Any?, * and a raw type",
                "minutes": 4,
                "steps": [
                    "Run `StarVsAnyDemo` and `StarVsAnyDemoJava`. Find the line in the Java output where the raw type's damage shows up.",
                    "Uncomment the wrong move in either file, predict, run.",
                    "In `StarVsAnyDemo.kt`, change `addMarker`'s parameter to `MutableList<*>`. Which line breaks now, and why?"
                ],
                "code": kdemo("StarVsAnyDemo", "StarVsAnyDemoJava"),
                "expect": "Kotlin prints `anything = [1200, EUR, null, marker], sizeOf(ids) = 1, sizeOf(anything) = 4` and `a = [pay_1], b = [pay_1]`. Java prints `ids = [pay_1, 42] (looks fine so far)` and then `ClassCastException at the read: class java.lang.Integer cannot be cast to class java.lang.String ...`. The wrong move fails with `actual type is 'MutableList<String>', but 'MutableList<Any?>' was expected` (Java: `List<String> cannot be converted to List<Object>`). With `MutableList<*>`, `addMarker(ids)` compiles but `list.add(\"marker\")` inside it fails: a star projection forbids adding."
            }
        },
        {
            "h": "Type checks need a star, then you check each element",
            "body": S4,
            "try": {
                "title": "Pick apart an untyped webhook payload",
                "minutes": 4,
                "steps": [
                    "Run `IsCheckDemo` (or `IsCheckDemoJava`). The payload's `amounts` list contains a stray `\"oops\"`.",
                    "Uncomment the wrong move, predict, run.",
                    "Replace `it as? Long` with `it as Long` and run again. Where does it fail, and is that where the bad data came from?"
                ],
                "code": kdemo("IsCheckDemo", "IsCheckDemoJava"),
                "expect": "Both print `object with keys [id, amounts]`, `array of 3`, `value 42` and `amounts = [1200, 350]`: the stray string is skipped. The wrong move fails with `Cannot check for instance of erased type 'List<Long>'.` (Java: `Object cannot be safely cast to List<Long>`). With `as Long`, the run fails with `ClassCastException: class java.lang.String cannot be cast to class java.lang.Long` inside `amountsIn`, far from wherever the payload was built."
            }
        }
    ],
    "analogy": "A star-projected list is a sealed shipping container whose manifest has been torn off. You know it holds one kind of goods, you just don't know which. You may unload items and handle each one as \"some item\", you may count them, and you may empty the container. You may not load anything in, because you can't know whether it matches what's inside. `MutableList<Any?>` is a different container, one labeled \"mixed goods\", which takes anything; a container of bananas is not a mixed-goods container, even though bananas are goods. The analogy breaks at the dock: a worker could open a box and read the label on the goods, but the JVM cannot recover a list's element type at run time at all. That is why `is List<String>` isn't allowed.",
    "in_your_world": "Star projections are the honest type for data whose shape you only learn at run time. A webhook from a card issuer parsed with `objectMapper.readValue(body, Map::class.java)` comes back as a `Map<*, *>`, because `Map::class.java` is a `Class<Map<*, *>>`. Kafka record headers, Temporal payload converters and Quarkus config maps all hand you values of unknown element type. Log them with `Map<*, *>` and `List<*>`, check shapes with `is Map<*, *>`, and pull out typed values element by element with `as?`. A metrics helper that reports the size of any in-memory buffer takes a `Collection<*>`. On the Java side of the codebase, replace raw `List` and `Map` parameters with `List<?>` and `Map<?, ?>`.",
    "mistake": "The common mistake is writing `Any?` when you mean \"unknown\": `fun logAll(items: MutableList<Any?>)` or `fun audit(fields: Map<Any?, Any?>)`. It looks maximally general, but `MutableList` and `Map`'s key are invariant, so a caller's `MutableList<String>` or `Map<String, Int>` is rejected, and the caller ends up copying or casting to fit. The Java version of the same reflex is a raw `List` parameter, which compiles for everyone and silently turns checking off. The fix is to say what you mean: `MutableList<*>` / `Map<*, *>` in Kotlin and `List<?>` / `Map<?, ?>` in Java when you don't care about the type, and a real `MutableList<Any?>` only when you genuinely store arbitrary values.",
    "compare": {
        "title": "Unknown type arguments: Kotlin's * and Java's ?",
        "java": {
            "title": "Payloads.java",
            "src": "import java.util.List;\nimport java.util.Map;\nimport java.util.stream.Collectors;\n\nfinal class Payloads {\n    static String describe(Object value) {\n        if (value == null) return \"nothing\";\n        if (value instanceof String s) return \"text \" + s;\n        if (value instanceof List<?> l) return \"list of \" + l.size();    // List<String> would not compile\n        if (value instanceof Map<?, ?> m) return \"map of \" + m.size();\n        return \"other\";\n    }\n\n    static String render(Map<?, ?> map) {                                 // keys and values are Object\n        return map.entrySet().stream()\n            .sorted((a, b) -> String.valueOf(a.getKey()).compareTo(String.valueOf(b.getKey())))\n            .map(e -> e.getKey() + \"=\" + (e.getValue() instanceof Map<?, ?> m ? render(m) : e.getValue()))\n            .collect(Collectors.joining(\", \", \"{\", \"}\"));\n    }\n\n    static int drain(List<?> buffer) {     // not a raw List: checks stay on\n        int n = buffer.size();\n        buffer.clear();\n        return n;\n    }\n}"
        },
        "kotlin": {
            "title": "Payloads.kt",
            "src": "fun describe(value: Any?): String = when (value) {\n    null -> \"nothing\"\n    is String -> \"text $value\"\n    is List<*> -> \"list of ${value.size}\"       // List<String> would not compile\n    is Map<*, *> -> \"map of ${value.size}\"\n    else -> \"other\"\n}\n\nfun render(map: Map<*, *>): String =                // keys and values are Any?\n    map.entries\n        .sortedBy { it.key.toString() }\n        .joinToString(\", \", \"{\", \"}\") { (k, v) -> \"$k=${if (v is Map<*, *>) render(v) else v}\" }\n\nfun drain(buffer: MutableList<*>): Int {          // Kotlin has no raw types\n    val n = buffer.size\n    buffer.clear()\n    return n\n}"
        },
        "note": "Kotlin's `MutableList<*>` compiles to Java's `List<?>`, and the two behave almost the same: reads give `Any?` / `Object`, writes of real values are refused, and members that take no element still work. Three things differ. Java lets you pass `null` through a `?`; Kotlin refuses, because the unknown type might be non-nullable. Java still has raw types, which switch checking off; Kotlin has none, and shows a Java raw `List` as `List<*>`. And Kotlin works out what `*` means from the declaration's variance, so a star on an `in` parameter becomes `in Nothing` and a star on an `out T : Number` keeps the `Number` bound, while Java applies the same capture rules to every wildcard."
    },
    "worked": {
        "title": "Render an untyped webhook payload for the audit log",
        "steps": [
            {"say": "A card issuer's webhook is parsed into a map whose types you don't control. The first draft of the audit renderer asks for `Map<Any?, Any?>` to be \"as general as possible\". The parsed map in a test is a `Map<String, Int>`. Read the error.",
             "code": "fun render(map: Map<Any?, Any?>): String = map.toString()\n\nval webhook: Map<String, Int> = mapOf(\"cents\" to 1_200)\nrender(webhook)\n// error: Argument type mismatch: actual type is 'Map<String, Int>', but 'Map<Any?, Any?>' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<Object, Object> map) { return map.toString(); }\n\nMap<String, Integer> webhook = Map.of(\"cents\", 1_200);\nrender(webhook);\n// error: incompatible types: Map<String,Integer> cannot be converted to Map<Object,Object>"},
            {"say": "`Map<K, out V>` is covariant in `V` but invariant in `K`, so `Map<String, Int>` is not a `Map<Any?, Any?>`. The renderer never puts anything into the map; it only reads. So it doesn't need to name either type. Use one star per type parameter.",
             "code": "fun render(map: Map<*, *>): String =\n    map.entries\n        .sortedBy { it.key.toString() }      // 1. keys are Any?: toString() works, even on null\n        .joinToString(\", \", \"{\", \"}\") { (k, v) -> \"$k=$v\" }",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<?, ?> map) {\n    return map.entrySet().stream()\n        .sorted(Comparator.comparing(e -> String.valueOf(e.getKey())))   // 1. keys are Object\n        .map(e -> e.getKey() + \"=\" + e.getValue())\n        .collect(Collectors.joining(\", \", \"{\", \"}\"));\n}"},
            {"say": "Payloads nest: the `card` field is itself a map. Check the value's shape with a star, and the smart cast gives you a `Map<*, *>` to recurse on. Self-check before reading the comment: why not `v is Map<String, Any?>`? (Type arguments are erased, so the compiler refuses that check.)",
             "code": "fun render(map: Map<*, *>): String =\n    map.entries\n        .sortedBy { it.key.toString() }\n        .joinToString(\", \", \"{\", \"}\") { (k, v) ->\n            val shown = if (v is Map<*, *>) render(v) else v.toString()   // 2. smart cast to Map<*, *>\n            \"$k=$shown\"\n        }\n\nrender(mapOf(\"cents\" to 99, \"card\" to mapOf(\"scheme\" to \"visa\", \"last4\" to \"4242\")))\n// {card={last4=4242, scheme=visa}, cents=99}",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static String render(Map<?, ?> map) {\n    return map.entrySet().stream()\n        .sorted(Comparator.comparing(e -> String.valueOf(e.getKey())))\n        .map(e -> e.getKey() + \"=\"\n            + (e.getValue() instanceof Map<?, ?> m ? render(m) : e.getValue()))   // 2. pattern match\n        .collect(Collectors.joining(\", \", \"{\", \"}\"));\n}"},
            {"say": "Now any map fits: `Map<String, Int>`, `Map<String, Any?>`, the `Map<*, *>` that a JSON library returns, or a map with `Int` keys. The renderer is honest about what it knows. This is the `render` function in the lab, and the tests check exactly this output."}
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
            "In `Describe.kt`, write `describe` as one `when (value)` with the branches in the order the KDoc lists them.",
            "Write `stringsIn`: return early unless `value is List<*>`, then keep the elements that are `String`s.",
            "Fix `drain`'s parameter type so any mutable list fits, then clear it and return the old size.",
            "In `MapPrinter.kt`, write `render`. Sort the entries by `key.toString()` and recurse into values that are `Map<*, *>`.",
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
        "prompt": "Close this page. Declare `interface Source<out T : Number> { fun next(): T }`, `interface Sink<in T> { fun accept(item: T) }` and `class Box<T>(var item: T)`. Write one function that takes a `Source<*>`, a `Sink<*>`, a `Box<*>` and a `MutableList<*>`, and does the one legal thing with each. In a comment, say what each star stands for. Then write the Java version, which has one extra legal call.",
        "answer": {
            "lang": "kotlin",
            "src": "interface Source<out T : Number> { fun next(): T }\ninterface Sink<in T> { fun accept(item: T) }\nclass Box<T>(var item: T)\n\nfun drill(s: Source<*>, k: Sink<*>, b: Box<*>, l: MutableList<*>) {\n    val n: Number = s.next()   // Source<*> = Source<out Number>: reads keep the bound\n    // k.accept(...)           // Sink<*> = Sink<in Nothing>: nothing can be passed in\n    val i: Any? = b.item       // Box<*> reads as Box<out Any?> (and writes as Box<in Nothing>)\n    l.clear()                  // MutableList<*>: members that take no element still work\n}",
            "alt": {"lang": "java", "title": "Drill.java", "src": "interface Source<T extends Number> { T next(); }\ninterface Sink<T> { void accept(T item); }\nclass Box<T> { T item; }\n\nstatic void drill(Source<?> s, Sink<?> k, Box<?> b, List<?> l) {\n    Number n = s.next();   // the bound survives the ?\n    k.accept(null);        // the extra legal call: Java lets null through a ?\n    Object i = b.item;     // reads as Object\n    l.clear();             // takes no element\n}"}
        }
    },
    "recap": [
        "`List<*>` means a list of one specific element type that you don't know. Reads give `Any?`; Java writes it `List<?>`.",
        "Through a star projection you can't pass an element in. Kotlin refuses even `null`; Java allows `null`.",
        "`*` becomes the safest projection: `out Bound` for an out parameter, `in Nothing` for an in parameter, both for an invariant one.",
        "`MutableList<Any?>` is a list of exactly `Any?` and rejects a `MutableList<String>`. `MutableList<*>` accepts every mutable list.",
        "Java's raw types switch checking off. Kotlin has none and shows a Java raw `List` as `List<*>`.",
        "Check unknown values with `is List<*>` or `is Map<*, *>`, then check each element with `is` or `as?`."
    ],
    "quiz": [
        {
            "q": "`val star: MutableList<*> = mutableListOf(\"pay_1\")`. Which line compiles?",
            "options": [
                "`star.add(\"pay_2\")`",
                "`star.add(null)`",
                "`star.removeAt(0)`",
                "`val s: String = star[0]`"
            ],
            "answer": 2,
            "why": "`removeAt` takes an index, not an element, so the star doesn't block it. Both `add` calls pass an element of the unknown type, which Kotlin refuses (even `null`, since the type might be non-nullable). A read gives only `CapturedType(*)`, which is not known to be a `String`."
        },
        {
            "q": "`interface Source<out T : Number> { fun next(): T }` and `fun f(s: Source<*>)`. What is the static type of `s.next()` inside `f`?",
            "options": [
                "`Any?`",
                "`Number`",
                "`Nothing`",
                "It doesn't compile: you can't call anything on a star projection"
            ],
            "answer": 1,
            "why": "For an `out` parameter with a bound, `Source<*>` means `Source<out Number>`, so reads keep the bound. `Any?` is what you'd get with no bound. `Nothing` is what a star gives on the *writing* side of an in or invariant parameter."
        },
        {
            "q": "You need a function that appends an audit marker string to whatever list a caller passes: a `MutableList<String>`, a `MutableList<Any>` or a `MutableList<CharSequence>`. Which parameter type fits?",
            "options": [
                "`MutableList<*>`",
                "`MutableList<Any?>`",
                "`List<Any?>`",
                "`MutableList<in String>`"
            ],
            "answer": 3,
            "why": "The function writes `String`s and never reads, so it is a consumer: `MutableList<in String>` accepts lists of `String` or any supertype. A star forbids `add`. `MutableList<Any?>` accepts only lists of exactly `Any?`. `List` has no `add` at all. This is the \"pick the right tool\" contrast: `*` when you neither read typed values nor write, `in` when you write."
        },
        {
            "q": "Java: `List<String> ids = new ArrayList<>(List.of(\"pay_1\")); List raw = ids; raw.add(42);` Then `String s = ids.get(1);`. What happens?",
            "options": [
                "A compile error at `raw.add(42)`",
                "It compiles (with an unchecked warning) and throws `ClassCastException` at `ids.get(1)`",
                "It throws `ArrayStoreException` at `raw.add(42)`",
                "It runs fine and `s` is `\"42\"`"
            ],
            "answer": 1,
            "why": "A raw type turns generic checking off, so the `Integer` goes in. Erasure means the `ArrayList` can't notice. The cast that javac inserted at `ids.get(1)` fails, far from the bad write. `ArrayStoreException` is the array version of this check, which lists don't have. In Kotlin the same write fails to compile, because a raw `List` is seen as `List<*>`."
        },
        {
            "q": "From \"Use-site variance and type projections\": which signature lets `copyAll` copy a `MutableList<Int>` into a `MutableList<Number>`?",
            "options": [
                "`fun <T> copyAll(from: MutableList<out T>, to: MutableList<in T>)`",
                "`fun copyAll(from: MutableList<*>, to: MutableList<*>)`",
                "`fun <T> copyAll(from: MutableList<T>, to: MutableList<T>)`",
                "`fun copyAll(from: MutableList<Any?>, to: MutableList<Any?>)`"
            ],
            "answer": 0,
            "why": "`from` only gives values (`out T`) and `to` only takes them (`in T`), so `T = Int` works with a `MutableList<Number>` target. With stars, `to.add(x)` is forbidden. Plain `T` forces both lists to the same element type, and `MutableList<Any?>` rejects both arguments.",
            "from": "gen-06"
        }
    ],
    "flashcards": [
        {"front": "What does `List<*>` mean?", "back": "A list of one specific element type that you don't know or don't care about. Reads come out as `Any?`. Java's spelling is `List<?>`."},
        {"front": "Can you call `add(null)` on a `MutableList<*>`?", "back": "Not in Kotlin: `Null cannot be a value of a non-null type 'CapturedType(*)'.` Java's `List<?>` does allow `add(null)`."},
        {"front": "For `interface Sink<in T>`, what does `Sink<*>` mean?", "back": "`Sink<in Nothing>`: no value fits, so you can't call `accept` at all."},
        {"front": "For `interface Source<out T : Number>`, what does `Source<*>` mean?", "back": "`Source<out Number>`: reads give `Number`, because the bound survives the star."},
        {"front": "Why does `fun f(l: MutableList<Any?>)` reject a `MutableList<String>`?", "back": "`MutableList` is invariant and `Any?` is a specific type argument. Use `MutableList<*>` if `f` doesn't need to add."},
        {"front": "How does Kotlin see a Java parameter of raw type `List`?", "back": "As a star projection, `List<*>`, so Kotlin code can't write unchecked elements into it."},
        {"front": "`payload: Any?`. Why `payload is List<*>` and not `payload is List<String>`?", "back": "Type arguments are erased at run time, so the JVM can only check the class. Check with a star, then check each element."}
    ],
    "terms": [
        {"term": "Star projection", "plain": "`C<*>`: a `C` of some type argument you don't know. Kotlin picks the safest projection for it."},
        {"term": "Unbounded wildcard", "plain": "Java's `?` with no bound, as in `List<?>`: the Java twin of `*`."},
        {"term": "Raw type", "plain": "A Java generic type used with no type arguments at all (`List`). Generic checks are off for it."},
        {"term": "in Nothing", "plain": "What a star means on the writing side: only a `Nothing` could be passed, and no such value exists."},
        {"term": "Smart cast", "plain": "After `if (x is List<*>)`, the compiler treats `x` as a `List<*>` without an explicit cast."},
        {"term": "Erased type", "plain": "A type argument that exists only at compile time. At run time a `List<String>` is just a `List`."}
    ],
    "explain_back": {
        "prompt": "A teammate wrote `fun logFields(fields: Map<Any?, Any?>)` and now every caller with a `Map<String, Int>` has a type error. They ask whether `Map<*, *>` is just a shorter way to write `Map<Any?, Any?>`. Explain the difference in your own words.",
        "answer": "`Map<Any?, Any?>` is one specific type: a map whose keys and values are declared as `Any?`. Because `Map` is invariant in its key type, a `Map<String, Int>` is not that type, so callers get an error. `Map<*, *>` means \"a map of some key type and some value type that I don't know\". Every map fits it. In exchange, the function can only do things that are safe for any key and value type: read keys and values as `Any?`, ask for the size, iterate. It can't call methods that take a key or value of the unknown type in a way that would store one. A logging function only reads, so `Map<*, *>` is the honest type. `Map<Any?, Any?>` only makes sense if you build a map that really holds arbitrary keys and values."
    },
    "deeper": {
        "minutes": 10,
        "body": "Kotlin can still call a generic function with a star-projected argument. Given `fun <T> swap(l: MutableList<T>, i: Int, j: Int)`, the call `swap(star, 0, 1)` with `star: MutableList<*>` compiles with kotlinc 2.4.21 and swaps the two elements. The compiler captures the unknown element type as `T` for that one call, so inside `swap` a value read from the list may be written back into the same list. Java does the same with a private helper method, the \"capture helper\" pattern; the JDK's `Collections.swap(List<?> list, int i, int j)` skips it and uses a raw type under `@SuppressWarnings`.\n\nThe `Map` interface has a detail worth knowing. It is declared `Map<K, out V>`, invariant in `K`. So on a `Map<*, *>` the member `get(key: K)` would take `in Nothing`, and you could never look anything up. The standard library adds an extension, `Map<out K, V>.get(key: K)`, so `payload[\"amounts\"]` on a `Map<*, *>` still compiles and returns `Any?`.\n\nStars also appear in class literals: `Map::class.java` is a `Class<Map<*, *>>`, and `listOf(1)::class` is a `KClass<out List<Int>>`. The class object of a generic class exists once for all type arguments, so it can't carry them. Lesson 9 of this track is about exactly that. And in Kotlin's own reflection, `typeOf<List<*>>().arguments` prints `[*]`: the star is part of the type, not an absence of one."
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
