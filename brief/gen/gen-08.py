import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l08.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l08/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l08/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


FIG = ('<svg viewBox="0 0 700 270" role="img" aria-label="Left: ArrayList of String and ArrayList of Int are different types at compile time but one class, java.util.ArrayList, at run time, so the JVM cannot tell them apart. '
       'Right: an inline function with a reified T is copied into the caller, so the call isA of String becomes x instanceof String in the caller\'s own code.">'
       '<text class="t-s t-m" x="175" y="20" text-anchor="middle">an ordinary generic: erased</text>'
       + box(20, 34, 150, "ArrayList&lt;String&gt;", "box-a")
       + box(180, 34, 150, "ArrayList&lt;Int&gt;", "box-b")
       + '<line class="ln" x1="95" y1="72" x2="150" y2="144" marker-end="url(#arr)"/>'
         '<line class="ln" x1="255" y1="72" x2="200" y2="144" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="175" y="112" text-anchor="middle">compiled</text>'
       + box(60, 148, 230, "class java.util.ArrayList", "box-dim")
       + '<text class="t-s t-bad" x="175" y="212" text-anchor="middle">is List&lt;String&gt;? the JVM cannot tell</text>'
         '<line class="ln-d" x1="350" y1="30" x2="350" y2="220"/>'
         '<text class="t-s t-m" x="525" y="20" text-anchor="middle">inline + reified: copied into the caller</text>'
       + box(395, 34, 260, "x.isA&lt;String&gt;()", "box-a")
       + '<line class="ln-a" x1="525" y1="72" x2="525" y2="144" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="533" y="112">inlined, T = String</text>'
       + box(395, 148, 260, "x instanceof String", "box-ok")
       + '<text class="t-s t-ok" x="525" y="212" text-anchor="middle">a real check, in the caller\'s bytecode</text>'
         '<text class="t-s t-m" x="350" y="254" text-anchor="middle">Erasure removes type arguments from objects. Inlining puts the known class back at each call site.</text>'
         '</svg>')

S1 = """Lesson 7 hit a wall: `is List<Long>` doesn't compile. Here is why. Both compilers check type arguments and then remove them. At run time a `List<String>` and a `List<Int>` are the same kind of object:

```java
List<String> ids = new ArrayList<>();
List<Integer> cents = new ArrayList<>();
System.out.println(ids.getClass() == cents.getClass());   // true: both are java.util.ArrayList
```

```kotlin
val ids = ArrayList<String>()
val cents = ArrayList<Int>()
println(ids.javaClass == cents.javaClass)                  // true: both are java.util.ArrayList
```

This is **type erasure**. Java 5 added generics this way so that old and new class files could run on the same JVM. Kotlin compiles to the same JVM and inherits the rule. The compiler checks the type argument, and then it is gone: the object has no field that says `String`.

Here is what both compilers leave in the class file. Each type parameter becomes its bound: a plain `T` becomes `Object`, and `T : Comparable<T>` becomes `Comparable`. So `List.get` returns an `Object`. Where your code needs a `String`, the compiler inserts a `checkcast` instruction to `String` right after the call. Run `javap -c` on any class that reads from a `List<String>` and you'll see it. That inserted cast is the line that throws in the last example below.

Three things follow, and each has an error you'll meet:

- A type check can test only the class. `x is List<String>` fails with `Cannot check for instance of erased type 'List<String>'.`, and `is T` fails the same way. Java says `Object cannot be safely cast to List<String>`.
- You can't create a `T`. Kotlin's `T()` gives `Type parameter 'T' is not an expression.` and Java's `new T()` gives `unexpected type`.
- A cast to a generic type checks only the class. This one compiles, with a warning, and it's the dangerous one:

```java
@SuppressWarnings("unchecked")
List<String> lies = (List<String>) (Object) List.of(1_200, 350);
lies.size();                 // 2: the cast "worked"
String first = lies.get(0);  // ClassCastException: Integer cannot be cast to String
```

```kotlin
@Suppress("UNCHECKED_CAST")
val lies = listOf(1_200, 350) as Any as List<String>
lies.size                    // 2: the cast "worked"
val first: String = lies[0]  // ClassCastException: Integer cannot be cast to String
```

The list now claims to hold strings and holds integers. That state is called **heap pollution**. The exception appears at the first read that needs a `String`, which may be in another class written by another team.

Some generic information does survive. The signatures of declarations (a field's type, a method's parameters, a class's superclass) stay in the class file, and reflection can read them: `Field.getGenericType()` on a `List<String>` field returns `java.util.List<java.lang.String>`. What erasure removes is the type argument of each object. Lesson 9 puts the surviving part to work."""

S2 = """Kotlin has one way around erasure. Mark a function `inline`, and the compiler copies its body into every call site instead of calling it. At each call site the type argument is known, because `isA<String>()` is being compiled right there with `String` in plain sight. Mark the type parameter `reified`, and the compiler writes that real class into the copied body:

```java
// Java has no reified type parameters. The closest equivalent: pass the Class yourself.
static boolean isA(Object x, Class<?> type) { return type.isInstance(x); }

static <T> List<T> filterIsInstance(List<?> items, Class<T> type) {
    return items.stream().filter(type::isInstance).map(type::cast).toList();
}

isA("pay_1", String.class);                // true
filterIsInstance(payload, String.class);   // [pay_1, pay_2]
```

```kotlin
inline fun <reified T> Any?.isA(): Boolean = this is T     // a real instanceof after inlining

"pay_1".isA<String>()                      // true
payload.filterIsInstance<String>()         // [pay_1, pay_2]: the stdlib's reified filter
```

Inside a reified function you get back what erasure took away: `x is T`, `x as T` and `x as? T` with a real check, `T::class` and `T::class.java`. The standard library relies on this for `filterIsInstance<T>()`, `emptyArray<T>()` and `typeOf<T>()`, which lesson 9 covers.

The rules follow from how it works:

| You write | Kotlin says |
|---|---|
| `fun <reified T> notInline(x: Any) = x is T` | `Only type parameters of inline functions can be reified.` |
| `fun <T> forward(x: Any) = x.isA<T>()` | `Cannot use 'T' as reified type parameter. Use a class instead.` |
| `classOf<Nothing>(TODO())` | `Cannot use 'Nothing' as reified type parameter.` |

The second row matters in practice. A reified function can only be called with a type the caller knows. If the caller is itself generic with an ordinary `T`, its `T` is erased, so there is nothing to copy in. The requirement spreads upward: the caller must be `inline` with a `reified T` too, or it must pass a real class.

The figure puts an erased call and an inlined one side by side."""

S3 = """Before reified, the standard answer was a **class token**: pass the `Class<T>` as an argument and let it do the run-time work the erased `T` can't. Java APIs still look like this: `entityManager.find(Payment.class, id)`, `objectMapper.readValue(json, Payment.class)`. `type.isInstance(x)` is a checked `is T`, and `type.cast(x)` is a checked `as T` with no warning. Kotlin writes the token as `Payment::class.java`.

Good Kotlin libraries offer both: a core that takes a `Class<T>` (or a `KClass<T>`) and works for everyone, plus a one-line reified wrapper for Kotlin callers:

```java
// Java calling the Kotlin functions in ClassTokenDemo.kt:
BigDecimal zero = ClassTokenDemoKt.defaultOf(BigDecimal.class);    // the Class-token core: fine
BigDecimal viaReified = ClassTokenDemoKt.<BigDecimal>defaultOf();  // error: method defaultOf ... cannot be applied to given types
```

```kotlin
fun <T : Any> defaultOf(type: Class<T>): T =
    type.cast(defaults[type] ?: throw IllegalArgumentException("no default for ${type.simpleName}"))

inline fun <reified T : Any> defaultOf(): T = defaultOf(T::class.java)

val zero: BigDecimal = defaultOf()          // T inferred from the expected type
```

Why can't Java call the wrapper? javac can't inline Kotlin code, so it has no way to supply `T`. Kotlin still writes a method for the wrapper into the class file, but flags it `ACC_SYNTHETIC`, and javac ignores synthetic methods. Read the error again: javac says `defaultOf` needs an argument, because the only `defaultOf` it can see is the Class-token one. A reified function with no such overload gives `cannot find symbol`. So if Java code will call your API, the Class-token version is not optional.

One trap with tokens: `Int::class.java` is the primitive class `int`, but `T::class.java` for a reified `Int` is `java.lang.Integer`. A registry filled with one and queried with the other finds nothing. Use `Int::class.javaObjectType` when you need the boxed class. Java has the same split: `int.class` and `Integer.class` are different objects."""

S4 = """Reified brings back the class at the call site, and only the class. Three limits are worth knowing.

The type arguments of `T` itself are still erased. `filterIsInstance<List<String>>()` compiles without a single warning, and it keeps every list:

```java
// the Java version passes List.class: there is no List<String>.class
List<List<String>> stringLists = filterIsInstance(batches, List.class);
System.out.println(stringLists);              // [[1200, 350], [pay_1]]
String n = stringLists.get(0).get(0);         // ClassCastException
```

```kotlin
val batches: List<Any> = listOf(listOf(1_200, 350), listOf("pay_1"), "pay_2")
val stringLists = batches.filterIsInstance<List<String>>()   // no warning
println(stringLists)                          // [[1200, 350], [pay_1]]
val n: String = stringLists[0][0]             // ClassCastException
```

The Kotlin docs say the same about their `asPairOf<String, List<String>>()` example: it "compiles but breaks type safety". After inlining, `is List<String>` is only `instanceof List`.

`Nothing` and erased type parameters can't be reified, as the table above showed.

And Kotlin 2.4 added an error about null. Inside `inline fun <reified T> klassOf(x: T) = x::class`, `T` may be a nullable type, so `x` may be `null`, and `null` has no class. Kotlin 2.3 warned about this; 2.4 refuses: `Expression in class literal has nullable type 'T (of fun <T> klassOf)'. Use '!!' to make the type non-nullable.` The fix is to say what you mean with `<reified T : Any>`, so callers can't pass null at all. `T::class`, the class literal of the type rather than of a value, is still allowed with a nullable bound. Java has no such check: `x.getClass()` on a null `x` throws `NullPointerException` at run time.

So treat reified as a convenience for the outer class of a type: instance checks, casts and class tokens. When the full type matters, `List<Settlement>` and not just `List`, you need something that keeps the arguments. That's `KType`, in the next lesson."""

L = {
    "id": "gen-08",
    "title": "Type erasure and reified type parameters",
    "minutes": 35,
    "goal": "By the end you can say what the JVM erases and what survives, predict where an unchecked cast really fails, write `inline` functions with `reified` type parameters for `is T`, `as? T` and `T::class`, and give Java callers a `Class<T>` overload they can actually call.",
    "warmup": {
        "q": "`val lies = listOf(1_200, 350) as Any as List<String>` compiles with a warning. What does `println(lies.size)` do?",
        "options": [
            "It throws `ClassCastException` at the cast, before `println` runs",
            "It prints `2`",
            "It prints `0`, because no element is a String",
            "It doesn't compile: Kotlin forbids casting to `List<String>`"
        ],
        "answer": 1,
        "why": "At run time the list is just a `List`, so the cast can only check that it is a list, and it is. `size` never touches an element, so it prints `2`. The `ClassCastException` comes later, at the first read that needs a `String`. That delayed failure is what erasure costs you."
    },
    "sections": [
        {
            "h": "Type arguments vanish when the code compiles",
            "body": S1,
            "try": {
                "title": "Watch a cast succeed and a read fail",
                "minutes": 4,
                "steps": [
                    "Run `ErasureDemo` and `ErasureDemoJava`. Before you do, predict which of the three numbered steps throws.",
                    "Uncomment wrong move 1 in either file, predict the error, run.",
                    "Uncomment wrong move 2 (a top-level function) and run. Put both back."
                ],
                "code": kdemo("ErasureDemo", "ErasureDemoJava"),
                "expect": "Both print `same class at run time: true (java.util.ArrayList)`, `the cast worked, size = 2` and `ClassCastException at the read: class java.lang.Integer cannot be cast to class java.lang.String`. The cast succeeds; the read throws. Wrong move 1: `Cannot check for instance of erased type 'List<String>'.` (Java: `Object cannot be safely cast to List<String>`). Wrong move 2: `Type parameter 'T' is not an expression.` (Java: `unexpected type`)."
            },
            "refs": [
                {"title": "Generics: type erasure (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "inline and reified bring T back at each call site",
            "body": S2,
            "figure": {"svg": FIG, "caption": "An ordinary generic call runs against an erased class. A reified call is copied into the caller with the real class filled in."},
            "try": {
                "title": "Check types with a reified T",
                "minutes": 4,
                "steps": [
                    "Run `ReifiedDemo` (or `ReifiedDemoJava`, which passes `Class` objects instead).",
                    "Uncomment the two wrong moves at the bottom of `ReifiedDemo.kt` one at a time. Predict, run.",
                    "Remove `reified` from `isA` but keep `inline`. Run again: does `inline` alone help?"
                ],
                "code": kdemo("ReifiedDemo", "ReifiedDemoJava"),
                "expect": "Kotlin prints `\"pay_1\".isA<String>() = true, 1200L.isA<String>() = false`, then `strings: [pay_1, pay_2]`, `longs:   [1200]` and `nameOf<java.math.BigDecimal>() = BigDecimal`; Java prints the same with `Class` arguments. Wrong moves: `Only type parameters of inline functions can be reified.` and `Cannot use 'T' as reified type parameter. Use a class instead.` Without `reified`, `inline` alone is not enough: `Cannot check for instance of erased type 'T (of fun <T> Any?.isA)'.` The Java twin's wrong move, `x instanceof T`, fails with `Object cannot be safely cast to T`."
            },
            "refs": [
                {"title": "Inline functions: reified type parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html", "kind": "docs"}
            ]
        },
        {
            "h": "Java passes a Class<T>, and can't call reified functions",
            "body": S3,
            "try": {
                "title": "Call one API from both languages",
                "minutes": 4,
                "steps": [
                    "Run `ClassTokenDemo`, then `ClassTokenDemoJava`, which calls the Kotlin functions directly.",
                    "In the Java file, uncomment the wrong move and run. Read the `required:` line of the error.",
                    "In `ClassTokenDemo.kt`, add `Int::class.java to 0,` to `defaults` and call `println(defaultOf<Int>())` in `main`. Predict, run, then fix it with `Int::class.javaObjectType`."
                ],
                "code": kdemo("ClassTokenDemo", "ClassTokenDemoJava"),
                "expect": "Both print `zero = 0, eur = EUR, blank = ''`, then the primitive and boxed classes: `int` and `class java.lang.Integer`. The Java wrong move fails with `method defaultOf in class ClassTokenDemoKt cannot be applied to given types` and says it requires a `Class<T>`: javac can't see the synthetic reified overload. `defaultOf<Int>()` throws `IllegalArgumentException: no default for Integer`, because the map key is `int` and the reified lookup uses `Integer`. With `javaObjectType` it prints `0`."
            }
        },
        {
            "h": "What reified still can't do",
            "body": S4,
            "try": {
                "title": "Find the edges of reified",
                "minutes": 4,
                "steps": [
                    "Run `LimitsDemo` (or `LimitsDemoJava`). Is the first line what `filterIsInstance<List<String>>()` promised?",
                    "Uncomment wrong move 1 and run. Then uncomment wrong move 2: it compiles, so predict what happens when it runs.",
                    "Uncomment the `klassOf` function at the bottom (3), read the Kotlin 2.4 error, then fix it by changing `<reified T>` to `<reified T : Any>`."
                ],
                "code": kdemo("LimitsDemo", "LimitsDemoJava"),
                "expect": "Both print `lists of strings? [[1200, 350], [pay_1]]`: the list of ints got through. Kotlin then prints `classOf(\"pay_1\") = String`; Java prints `NullPointerException from getClass() on null`. Wrong move 1: `Cannot use 'Nothing' as reified type parameter.` Wrong move 2 compiles and throws `ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String` (the same happens in the Java twin). Function 3: `Expression in class literal has nullable type 'T (of fun <T> klassOf)'. Use '!!' to make the type non-nullable.` With `T : Any` it compiles."
            },
            "refs": [
                {"title": "Kotlin 2.4 compatibility guide (KTLC-370)", "url": "https://kotlinlang.org/docs/compatibility-guide-24.html", "kind": "docs"}
            ]
        }
    ],
    "analogy": "Erasure is a warehouse that checks the packing list at the packing table and then throws it away. The box that goes on the truck says only \"box\". At the receiving dock, nobody can tell whether it holds shirts or shoes without opening it and looking at each item. A reified function is a mail merge: because each letter is printed separately for its recipient, each copy can carry the recipient's name. That is what `inline` buys you: one copy per call site, so the known type can be printed into each copy. The analogy breaks at nesting. A mail merge could print the whole address, but reified prints only the outer class: `List<String>` arrives as just `List`.",
    "in_your_world": "Class tokens are all over the Java libraries in your stack. JPA's `entityManager.find(Payment.class, id)`, Jackson's `objectMapper.readValue(json, CardAuthorized.class)`, Temporal's `Workflow.newActivityStub(PaymentActivities.class, options)`. In Kotlin, wrap each in a one-line reified helper, `inline fun <reified T : Any> ObjectMapper.read(json: String): T = readValue(json, T::class.java)`, and call sites become `val e: CardAuthorized = mapper.read(json)`. Keep the Class-token version public if Java services in the same monorepo call your code. And watch the generic case: a Kafka consumer that decodes `List<PaymentEvent>` through `T::class.java` passes only `List.class`, so the library has no element type to bind to.",
    "mistake": "The common mistake is a generic function that quietly casts: `fun <T> decode(json: String): T = mapper.readValue(json, Any::class.java) as T`, with `@Suppress(\"UNCHECKED_CAST\")` to silence the warning. It compiles, it \"works\" in the happy-path test, and when a payload has the wrong shape, the `ClassCastException` appears in whatever code first uses the result, often in another module. People write it because the compiler only warns, and because the cast looks like it checks something. It doesn't: with an erased `T` the cast checks nothing. The fix is to make the type real at run time: take a `type: Class<T>` and call `type.cast(...)`, or make the function `inline` with a `reified T` and pass `T::class.java` to the library.",
    "compare": {
        "title": "A parser registry: Class tokens in Java, Class tokens plus reified in Kotlin",
        "java": {
            "title": "Parsers.java",
            "src": "import java.util.HashMap;\nimport java.util.Map;\nimport java.util.function.Function;\n\nfinal class Parsers {\n    private final Map<Class<?>, Function<String, ?>> byType = new HashMap<>();\n\n    <T> void register(Class<T> type, Function<String, ? extends T> parser) {\n        byType.put(type, parser);\n    }\n\n    // T is erased in here, so the caller hands over the Class\n    <T> T parse(String text, Class<T> type) {\n        Function<String, ?> parser = byType.get(type);\n        if (parser == null) throw new IllegalArgumentException(\"no parser for \" + type.getSimpleName());\n        return type.cast(parser.apply(text));      // a checked cast: no warning\n    }\n}\n\n// call site: Money m = parsers.parse(\"12.50 EUR\", Money.class);"
        },
        "kotlin": {
            "title": "Parsers.kt",
            "src": "class Parsers {\n    private val byType = HashMap<Class<*>, (String) -> Any>()\n\n    fun <T : Any> register(type: Class<T>, parser: (String) -> T) {\n        byType[type] = parser\n    }\n\n    // the same Class-token core, callable from Java\n    fun <T : Any> parse(text: String, type: Class<T>): T {\n        val parser = byType[type] ?: throw IllegalArgumentException(\"no parser for \" + type.simpleName)\n        return type.cast(parser(text))\n    }\n\n    // the Kotlin wrapper: the compiler writes Money::class.java into each call site\n    inline fun <reified T : Any> parse(text: String): T = parse(text, T::class.java)\n}\n\n// call site: val m = parsers.parse<Money>(\"12.50 EUR\")"
        },
        "note": "Both languages erase `T` inside `parse`, so both cores need the `Class<T>` argument, and both use `Class.cast` for a cast that really checks. The difference is at the call site. Kotlin can add an `inline` wrapper with a `reified T`, and the compiler fills in `Money::class.java` for the caller. Java can't use that wrapper: it is a synthetic method in the class file, and javac can't inline it. Note also that the wrapper calls only public members. A public inline function is copied into other modules, so it may not touch `byType` directly (`public-API inline function cannot access non-public-API property`)."
    },
    "worked": {
        "title": "Give a Kafka payload decoder a real type",
        "steps": [
            {"say": "A consumer decodes JSON into payment events through a codec that, like most Java libraries, wants a class token: `fun <T : Any> read(json: String, type: Class<T>): T`. The first draft tries to hide the token behind a generic function. Read the error.",
             "code": "fun <T : Any> decode(json: String): T = codec.read(json, T::class.java)\n// error: Cannot use 'T' as reified type parameter. Use a class instead.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static <T> T decode(String json) { return codec.read(json, T.class); }\n// error: cannot select from a type variable"},
            {"say": "1. Make the token explicit. This version works from Kotlin and from Java, and the codec does a checked conversion.",
             "code": "fun <T : Any> decode(json: String, type: Class<T>): T = codec.read(json, type)\n\nval e = decode(json, CardAuthorized::class.java)",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static <T> T decode(String json, Class<T> type) { return codec.read(json, type); }\n\nCardAuthorized e = decode(json, CardAuthorized.class);"},
            {"say": "2. Add the Kotlin convenience on top. Self-check before reading the comment: why must the wrapper be `inline`? (Only an inlined body is compiled at the call site, where `T` is known.)",
             "code": "inline fun <reified T : Any> decode(json: String): T = decode(json, T::class.java)\n\nval e: CardAuthorized = decode(json)       // T inferred from the expected type\nval r = decode<RefundIssued>(json)",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "// Java can't call the reified wrapper; it keeps using the token version:\nRefundIssued r = decode(json, RefundIssued.class);"},
            {"say": "3. Check the limit before you ship it. `decode<List<CardAuthorized>>(json)` compiles, but it passes `List::class.java`. The codec has no element type to bind to (Jackson, for example, fills such a list with `LinkedHashMap`s), and the first `for (e: CardAuthorized in events)` throws `ClassCastException`. For generic targets you need a token that keeps type arguments: `typeOf<List<CardAuthorized>>()` or a super type token, both in lesson 9."}
        ]
    },
    "lab": {
        "title": "Write reified helpers and a Class-token parser",
        "minutes": 12,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l08/Reified.kt",
            f"{LAB}/main/kotlin/workbench/generics/l08/Parsers.kt",
            f"{LAB}/main/kotlin/workbench/generics/l08/Callers.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l08.*'",
        "steps": [
            "Read the comment at the top of `Callers.kt` (don't edit it). The tests call your inline functions through it, because an inline function is copied into its caller when the caller is compiled.",
            "Run the tests. All seven fail.",
            "In `Reified.kt`, write `asOrNull`. First try `this as? T` without changing the signature, run the tests, and read the warning and the `ClassCastException`. Then make it `inline` with a `reified T`.",
            "Write `instancesOf` with a loop and `is T`. Read the error you get before adding `inline` and `reified`.",
            "In `Parsers.kt`, write `parse(text, type)`: look up the parser, throw `IllegalArgumentException(\"no parser for \" + type.simpleName)` if there is none, and return `type.cast(parser(text))`.",
            "Make the one-argument `parse` inline and reified, delegating with `T::class.java`. Run until all seven pass, including `ParsersFromJavaTest`."
        ],
        "hints": [
            "With an erased `T`, `this as? T` compiles with `Unchecked cast of 'Any?' to 'T (of fun <T> Any?.asOrNull)'.` and never returns null. That's the bug reified fixes.",
            "`inline fun <reified T> instancesOf(items: Iterable<*>): List<T>` then `for (item in items) if (item is T) out += item`.",
            "The reified `parse` must call the public `parse(text, type)`, not read `byType` itself: a public inline function can only use public members."
        ],
        "done_when": "All seven tests in `ReifiedTest` and `ParsersFromJavaTest` pass."
    },
    "drill": {
        "title": "Write asOrNull and instancesOf from memory",
        "minutes": 4,
        "prompt": "Close this page. Write `asOrNull<T>()` and `instancesOf<T>(items)` in Kotlin with reified type parameters. Then write the Java versions, which have to take a `Class<T>`. Which line in each Kotlin function would fail to compile without `reified`?",
        "answer": {
            "lang": "kotlin",
            "src": "inline fun <reified T> Any?.asOrNull(): T? = this as? T     // without reified: an unchecked cast that never fails\n\ninline fun <reified T> instancesOf(items: Iterable<*>): List<T> {\n    val out = ArrayList<T>()\n    for (item in items) if (item is T) out += item           // without reified: Cannot check for instance of erased type 'T'\n    return out\n}",
            "alt": {"lang": "java", "title": "Reified.java", "src": "static <T> T asOrNull(Object x, Class<T> type) {\n    return type.isInstance(x) ? type.cast(x) : null;      // the token does the run-time check\n}\n\nstatic <T> List<T> instancesOf(Iterable<?> items, Class<T> type) {\n    List<T> out = new ArrayList<>();\n    for (Object item : items) if (type.isInstance(item)) out.add(type.cast(item));\n    return out;\n}"}
        }
    },
    "recap": [
        "The JVM erases type arguments: at run time a `List<String>` is just a `List`, and `ArrayList<String>` and `ArrayList<Int>` share one class.",
        "So `is List<String>`, `is T` and `T()` don't compile, and a cast to `List<String>` checks only the class. The `ClassCastException` comes at a later read.",
        "Declarations keep their generic signatures in the class file; objects keep none.",
        "`inline` copies a function into each call site, and `reified` writes the caller's real class into the copy, so `is T`, `as? T` and `T::class` work.",
        "Java can't call reified functions (they are synthetic). Offer a `Class<T>` overload and make the reified one a one-line wrapper.",
        "Reified covers the outer class only: `filterIsInstance<List<String>>()` keeps every list. In Kotlin 2.4, `x::class` on a nullable reified `T` is an error; use `T : Any`."
    ],
    "quiz": [
        {
            "q": "`fun <T> isType(x: Any): Boolean = x is T`. What happens?",
            "options": [
                "It compiles and checks against whatever `T` the caller used",
                "It doesn't compile: `Cannot check for instance of erased type 'T'`",
                "It compiles with a warning and always returns `true`",
                "It compiles and throws at run time"
            ],
            "answer": 1,
            "why": "Inside an ordinary generic function `T` is erased, so there is no class to check against. Kotlin refuses the check outright, rather than warning like it does for casts. Making the function `inline` with a `reified T` fixes it."
        },
        {
            "q": "`@Suppress(\"UNCHECKED_CAST\") val ids = loadAny() as List<String>`, where `loadAny()` really returns `listOf(1, 2)`. Then `println(ids.size)`, then `val first: String = ids[0]`. Which line throws?",
            "options": [
                "The cast",
                "`println(ids.size)`",
                "`val first: String = ids[0]`",
                "None of them"
            ],
            "answer": 2,
            "why": "The cast checks only that the object is a `List`. `size` doesn't touch an element. The read is where the compiler inserted a cast to `String`, and that cast fails with `ClassCastException`. The bug is at the first line; the crash is at the third."
        },
        {
            "q": "Java services in your monorepo will call your new Kotlin `parse` API. Which shape do you publish?",
            "options": [
                "Only `inline fun <reified T : Any> parse(text: String): T`",
                "`fun <T> parse(text: String): T` with an unchecked cast inside",
                "A raw `Class` parameter, so any class works",
                "`fun <T : Any> parse(text: String, type: Class<T>): T`, plus a one-line reified wrapper for Kotlin callers"
            ],
            "answer": 3,
            "why": "javac can't call a reified function: it is a synthetic method, and Java can't inline it. A `Class<T>` core works for both languages and does a checked `type.cast`, and the reified wrapper keeps Kotlin call sites short. The unchecked cast checks nothing, and a raw `Class` loses the link between the argument and the return type."
        },
        {
            "q": "`listOf(listOf(1), listOf(\"a\"), \"b\").filterIsInstance<List<String>>()`. What does it return?",
            "options": [
                "`[[1], [a]]`: after inlining, the check is just `instanceof List`",
                "`[[a]]`",
                "A compile error: `List<String>` can't be a reified type argument",
                "An unchecked-cast warning, then `[[a]]`"
            ],
            "answer": 0,
            "why": "Reified fills in the outer class only. The element type `String` is still erased, so both lists pass the check, and there isn't even a warning. Checking elements yourself, or using a `KType`, is the only way to know more."
        },
        {
            "q": "From \"Star projection: when you don't know the type\": `payload: Any?` came from a JSON parser. Which code safely gets the `Long`s out of it?",
            "options": [
                "`(payload as List<Long>)`",
                "`if (payload is List<Long>) payload else emptyList()`",
                "`if (payload is List<*>) payload.filterIsInstance<Long>() else emptyList()`",
                "`payload as? List<Long> ?: emptyList()`"
            ],
            "answer": 2,
            "why": "Check the shape with a star, then check each element: `filterIsInstance<Long>()` is reified on `Long`, a plain class, so each check is real. `is List<Long>` doesn't compile, and both casts check only that it's a list, so a stray string would blow up later.",
            "from": "gen-07"
        }
    ],
    "flashcards": [
        {"front": "What is type erasure?", "back": "The compiler checks type arguments and then removes them. At run time a `List<String>` is just a `List`, with no record of `String`."},
        {"front": "Where does `val l = listOf(1) as Any as List<String>` fail?", "back": "Not at the cast. It fails at the first read that needs a `String`, such as `val s: String = l[0]`."},
        {"front": "What do `inline` and `reified` do together?", "back": "`inline` copies the function body into each call site. `reified` writes the caller's real class for `T` into that copy, so `is T`, `as? T` and `T::class` work."},
        {"front": "Can Java call `inline fun <reified T : Any> parse(text: String): T`?", "back": "No. It is a synthetic method and javac can't inline it. Provide `parse(text, type: Class<T>)` as well."},
        {"front": "Does `filterIsInstance<List<String>>()` check the elements?", "back": "No. Reified covers only the outer class; after inlining it is `instanceof List`, so a list of ints passes."},
        {"front": "Why is `inline fun <reified T> klassOf(x: T) = x::class` an error in Kotlin 2.4?", "back": "`T` may be nullable, and `null` has no class. Write `<reified T : Any>`."},
        {"front": "`Int::class.java` vs `T::class.java` with a reified `T = Int`?", "back": "The first is the primitive `int`; the second is `java.lang.Integer`. Use `Int::class.javaObjectType` for the boxed class."}
    ],
    "terms": [
        {"term": "Type erasure", "plain": "Removing type arguments after compile-time checking, so objects carry no `<String>` at run time."},
        {"term": "Unchecked cast", "plain": "A cast to a generic type that can check only the class. The compiler warns; the failure comes later."},
        {"term": "Heap pollution", "plain": "A variable of a generic type that refers to an object of the wrong type, such as a `List<String>` holding ints."},
        {"term": "inline function", "plain": "A function whose body the compiler copies into each call site."},
        {"term": "Reified type parameter", "plain": "A type parameter of an inline function whose real class is available in the copied body."},
        {"term": "Class token", "plain": "A `Class<T>` passed as an argument so code can check and cast to `T` at run time."},
        {"term": "Synthetic method", "plain": "A method the compiler writes into the class file but hides from javac, as Kotlin does with reified functions."}
    ],
    "explain_back": {
        "prompt": "A teammate asks why `fun <T> parse(json: String): T` can't just call `mapper.readValue(json, T::class.java)`, but adding `inline` and `reified` makes it work. Explain it in your own words, and say what Java callers should use instead.",
        "answer": "The JVM erases type arguments. Inside an ordinary generic function there is one compiled body shared by every caller, and in that body `T` is just `Object`: nothing at run time says which `T` this call was for, so there is no class to pass to the mapper. An `inline` function isn't called; its body is copied into each call site when that call site is compiled. At the call site the type argument is known, for example `parse<CardAuthorized>(json)`. With `reified`, the compiler writes `CardAuthorized::class.java` into that copy, so the mapper gets a real class. Java can't use this, because javac can't inline Kotlin code and the reified function is a hidden synthetic method. Java callers need an overload that takes a `Class<T>` explicitly, and the reified version should just delegate to it. And even reified only gives the outer class: `parse<List<CardAuthorized>>` would pass `List.class`."
    },
    "deeper": {
        "minutes": 10,
        "body": "You can see the copy mechanism in the bytecode. Run `javap -c -p` on `ClassTokenDemoKt.class` (it is under `generics/build/classes/kotlin/demo/workbench/generics/l08/demo/` after you run the demo). The method kept in the class for `defaultOf()` has the flags `ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC`, and where `T::class.java` should be it loads `Object.class` next to a call to `kotlin/jvm/internal/Intrinsics.reifiedOperationMarker`. That marker tells the compiler where to write the real class when it inlines the body into a caller. In `main`, the call `defaultOf<java.util.Currency>()` has no call to `defaultOf()` at all: you'll find `ldc class java/util/Currency` followed by a call to the Class-token `defaultOf`.\n\nThis is also why the lab routes test calls through `Callers.kt`. The inlined copy is fixed when the caller is compiled. Tests compiled once against `src/main` would keep a copy of your TODO stub forever, even when run next to the reference solution.\n\nTwo more rules come from copying. A public inline function is copied into other modules, so it may only touch public API: reading a private field gives `public-API inline function cannot access non-public-API property`. That is the deep reason for the \"Class-token core plus one-line reified wrapper\" shape. And a lambda passed to an inline function is normally inlined too, so it can't be stored. If the function needs to keep it, say in a handler map, that parameter must be marked `noinline`. Lesson 11 of this track uses that for a typed event bus.\n\nJava's own answer to erasure for arrays is different: arrays are reified. Every `String[]` knows its component type at run time, which is why `new T[1]` is a compile error (`generic array creation`) and why Kotlin's `arrayOf<T>()` needs a reified `T`."
    },
    "sources": [
        {"title": "Generics: type erasure and generic type checks and casts (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Inline functions: reified type parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
        {"title": "Kotlin 2.4 compatibility guide", "url": "https://kotlinlang.org/docs/compatibility-guide-24.html"},
        {"title": "Type Erasure (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/erasure.html"}
    ]
}

out = ROOT / "content/lessons/gen-08.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
