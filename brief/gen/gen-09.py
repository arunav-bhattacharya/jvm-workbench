import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l09.demo"


def kdemo(name, alt=None, extra_run=""):
    path = f"{LAB}/demo/kotlin/workbench/generics/l09/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt{extra_run}", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l09/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def panel(x, y, w, h, title, lines, cls, tcls):
    s = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    s += f'<text class="t {tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{title}</text>'
    for i, ln in enumerate(lines):
        s += f'<text class="t-s t-code" x="{x + w // 2}" y="{y + 50 + i * 20}" text-anchor="middle">{ln}</text>'
    return s


FIG = ('<svg viewBox="0 0 700 300" role="img" aria-label="Three objects. A KType such as typeOf of List of String nullable knows the class, the type arguments and the nullability. '
       'Its classifier is a KClass, List::class, which has no arguments and is never nullable. The KClass and Java\'s Class for java.util.List convert into each other with .java and .kotlin. '
       'An object at run time can only give you its class, never its full type.">'
       + panel(15, 30, 230, 120, "KType", ["typeOf&lt;List&lt;String&gt;?&gt;()", "arguments: [String]", "nullable: true"], "box-a", "t-a")
       + panel(300, 30, 170, 120, "KClass", ["List::class", "no arguments", "never nullable"], "box", "t")
       + panel(525, 30, 160, 120, "Class", ["java.util.List", "Java's view", "of the class"], "box-b", "t-b")
       + '<line class="ln-a" x1="247" y1="90" x2="296" y2="90" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="272" y="80" text-anchor="middle">classifier</text>'
         '<line class="ln" x1="472" y1="80" x2="521" y2="80" marker-end="url(#arr)"/>'
         '<line class="ln" x1="521" y1="102" x2="472" y2="102" marker-end="url(#arr)"/>'
         '<text class="t-s t-code" x="497" y="72" text-anchor="middle">.java</text>'
         '<text class="t-s t-code" x="497" y="120" text-anchor="middle">.kotlin</text>'
       + '<rect class="box-dim" x="300" y="200" width="385" height="44" rx="8"/>'
         '<text class="t-s t-code" x="492" y="227" text-anchor="middle">an object at run time: listOf("pay_1")</text>'
         '<line class="ln-d" x1="440" y1="198" x2="400" y2="154" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="375" y="182" text-anchor="middle">x::class</text>'
         '<line class="ln-d" x1="560" y1="198" x2="600" y2="154" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="625" y="182" text-anchor="middle">x.javaClass</text>'
         '<text class="t-s t-m" x="130" y="190" text-anchor="middle">only the compiler can</text>'
         '<text class="t-s t-m" x="130" y="208" text-anchor="middle">write a KType down,</text>'
         '<text class="t-s t-m" x="130" y="226" text-anchor="middle">at a call site: typeOf&lt;T&gt;()</text>'
         '<text class="t-s t-m" x="350" y="284" text-anchor="middle">Objects know their class. Only code knows full types.</text>'
         '</svg>')

S1 = """Lessons 3 and 8 of this track gave you two facts. One class stands behind many types: the class `String` backs the types `String` and `String?`, and the class `List` backs `List<String>`, `List<Int>` and `List<Payment>?`. And at run time, erasure leaves each object with its class and nothing more.

Kotlin's reflection API has a separate object for each idea. Most confusion about `KClass` comes from mixing them up:

- A `KClass` describes a class: `String::class`, `CardAuthorized::class`, `List::class`. It has no type arguments and is never nullable. Its interface is `KClass<T : Any>`.
- A `Class` is Java's object for the same class: `String.class` in Java, `String::class.java` in Kotlin. Every object can hand you its `Class` at run time.
- A `KType` describes a full type: the class, plus its type arguments, plus whether it is nullable. `typeOf<List<String>?>()` gives you one.

```java
Class<String> c = String.class;                                // Java's class object
boolean same = new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass();   // true
// Java has no KType. The closest thing is a java.lang.reflect.Type read from a declaration:
Type t = Holder.class.getDeclaredField("ids").getGenericType();   // java.util.List<java.lang.String>
```

```kotlin
val k: KClass<String> = String::class                 // Kotlin's class object
val c: Class<String> = String::class.java             // the Java one, for Java APIs
val t: KType = typeOf<List<String>?>()                 // List, with argument String, nullable
val same = ArrayList<String>()::class == ArrayList<Int>()::class   // true
```

To pick the right one, ask what you need to know. "What kind of object is this?" is a question about a class, and a `KClass` or a `Class` answers it. "A list of *what*?" or "may it be null?" are questions about a type, and only a `KType` can answer them.

One warning before you run anything. Without the kotlin-reflect library on the classpath, Kotlin prints these objects with a suffix:

```text
class java.lang.String (Kotlin reflection is not available)
java.util.List<java.lang.String>? (Kotlin reflection is not available)
```

Nothing is broken. `toString()` can't produce Kotlin names such as `kotlin.String` without the library, so it falls back to Java names and says so. Section 4 shows what the library adds. A Gradle project doesn't include it unless you ask; the `kotlinc` command-line compiler adds it by default, so the same code can print differently in the two."""

S2 = """There are two ways to get a `KClass`. A **class literal**, `CardAuthorized::class`, names a class you know while writing the code, and its type is exact: `KClass<CardAuthorized>`. A **bound class reference**, `event::class`, asks a value for its class at run time, and its type has an `out` in it:

```java
PaymentEvent event = new CardAuthorized("pay_1", 1_200);
Class<? extends PaymentEvent> c = event.getClass();   // what getClass() is declared to return
Class<PaymentEvent> strict = event.getClass();        // error: Class<CAP#1> cannot be converted to Class<PaymentEvent>
```

```kotlin
val event: PaymentEvent = CardAuthorized("pay_1", 1_200)
val k: KClass<out PaymentEvent> = event::class        // the class of SOME PaymentEvent
val strict: KClass<PaymentEvent> = event::class       // error: expected 'KClass<PaymentEvent>', actual 'KClass<out PaymentEvent>'
```

Why the `out`? The compiler knows that `event` is *some* `PaymentEvent`. When the program runs it turns out to be a `CardAuthorized`, but it could have been a `RefundIssued`. So the most the compiler can say is "the class of some subtype of `PaymentEvent`, I don't know which". That is exactly what `out` meant in lesson 4: a producer of some unknown subtype. Java says the same with `? extends`; the Javadoc of `Object.getClass()` states that the result type is `Class<? extends |X|>`, where `|X|` is the erasure of the expression's static type.

The `out` doesn't stop you from using the class. Everything that hands information out still works: `event::class.simpleName`, `event::class == CardAuthorized::class`, and `cast`, which gives you back a `PaymentEvent`. What you can't do is pass it where an exact `KClass<PaymentEvent>` is required. The compiler doesn't special-case final classes either: `"pay_1"::class` is a `KClass<out String>`.

The other half of `KClass<T : Any>` is the bound. There is no class for a nullable type, because `String?` is backed by the class `String`. So `KClass<String?>` is an error, and so is asking a nullable value for its class:

```text
val kn: KClass<String?>? = null
Type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.

val note: String? = ...
note::class
Expression in class literal has nullable type 'String?'. Use '!!' to make the type non-nullable.
```

Write `note?.let { it::class }` instead, and you get a `KClass<out String>?`: null when there's no value to ask. Java has no compile-time check for this. `note.getClass()` throws `NullPointerException` when `note` is null."""

S3 = """On the JVM every `KClass` wraps a `java.lang.Class`, and you move between them with two properties. You'll do it often at the boundary with Java libraries:

```java
Class<CardAuthorized> c = CardAuthorized.class;
boolean isCard = c.isInstance(event);           // true
CardAuthorized card = c.cast(event);            // checked: ClassCastException if not
String name = c.getSimpleName();                // "CardAuthorized"
Class<?> runtime = event.getClass();            // the object's class
```

```kotlin
val k: KClass<CardAuthorized> = CardAuthorized::class
val c: Class<CardAuthorized> = k.java           // KClass to Class, for Java APIs
val back: KClass<CardAuthorized> = c.kotlin     // Class to KClass
k.isInstance(event)                             // true
val card: CardAuthorized = k.cast(event)        // checked: ClassCastException if not
val refund: RefundIssued? = RefundIssued::class.safeCast(event)   // null instead of throwing
k.simpleName                                    // "CardAuthorized"
event.javaClass                                 // the object's Class, like Java's getClass()
```

These are the `KClass` versions of the class-token tools from lesson 8. `isInstance` is a checked `is`, `cast` is a checked `as`, and `safeCast` is a checked `as?`. (`cast` and `safeCast` are extension functions in `kotlin.reflect`, so they need an import.) A failed `cast` throws `ClassCastException: Value cannot be cast to` followed by the class name. Names work out of the box: `simpleName`, `qualifiedName`. So does equality: `event::class == CardAuthorized::class` is `true`.

Two traps. The first is from lesson 8: `Int::class.java` is the primitive `int`, and `Int::class.javaObjectType` is `java.lang.Integer`. The second is `javaClass`. On a value, `event.javaClass` is the object's `Class`. On a `KClass` it would be the class of the `KClass` object itself, a Kotlin internal, and Kotlin 2.4.21 rejects it with a deprecation error that tells you what you meant:

```text
k.javaClass
'val <T : Any> KClass<T>.javaClass: Class<KClass<T>>' is deprecated. Use 'java' property to get Java class corresponding to this Kotlin class ...
```

Which one should your code use? Inside Kotlin code, prefer `KClass`. It has `safeCast`, it's what other Kotlin APIs hand you, and it's what this lesson's registry keys on. At the edge, pass `.java` to the Java library (JPA, Jackson, Temporal, CDI) and keep the `KClass` on your side."""

S4 = """`KClass` has many more members: `objectInstance`, `sealedSubclasses`, `isData`, `members`, `constructors`, `supertypes`. Your code compiles against all of them, because they're declared in the standard library. But the code that *answers* them lives in a separate jar, `kotlin-reflect` (about 3.8 MB in 2.4.21), which a Gradle project doesn't have unless you add it. Without it they fail at run time:

```text
Origin::class.objectInstance
KotlinReflectionNotSupportedError: Kotlin reflection implementation is not found at runtime. Make sure you have kotlin-reflect.jar in the classpath
```

A rule of thumb that holds up: **names, identity, instance checks, casts and `typeOf` are free; anything that lists or describes declarations needs kotlin-reflect.**

| Works with the standard library alone | Needs kotlin-reflect |
|---|---|
| `simpleName`, `qualifiedName`, `==`, `.java`, `.kotlin` | `objectInstance`, `sealedSubclasses`, `isData`, `isSealed` |
| `isInstance`, `cast`, `safeCast` | `members`, `constructors`, `typeParameters`, `supertypes` |
| `typeOf<T>()` with `classifier`, `arguments`, `isMarkedNullable` | `kotlin.reflect.full` extensions such as `createInstance()` |

The `kotlin.reflect.full` extensions fail differently, with `NoClassDefFoundError: kotlin/reflect/full/KClasses`, because that class isn't in the standard library at all.

Java reflection needs no extra jar, and it works on Kotlin classes too:

```java
CardAuthorized.class.getDeclaredFields();               // [cents, paymentId]
Origin.class.getField("INSTANCE").get(null);            // a Kotlin object is a static INSTANCE field
```

```kotlin
CardAuthorized::class.java.declaredFields               // the same Java reflection, from Kotlin
Origin::class.objectInstance                            // the Kotlin way: needs kotlin-reflect
```

So when a Java-level answer is enough (fields, methods, annotations), go through `.java` and skip the dependency. When you need Kotlin-level facts (is this a data class, which subclasses does this sealed interface have, is this property nullable), add kotlin-reflect. Libraries that inspect Kotlin classes, such as Jackson's Kotlin module, pull it in for exactly this reason."""

S5 = """Now the problem this lesson's lab is built around. A service registry keyed by `KClass` works for `PaymentGateway` and `FraudCheck`. It can't hold a `Repository<Payment>` and a `Repository<Refund>` at the same time, because both have the class `Repository`, and the second registration silently replaces the first. You can't even write the class of the type you mean:

```text
val k = Repository<Payment>::class
Only classes are allowed on the left-hand side of a class literal.
```

A `KType` keeps the type arguments and the nullability. In Kotlin, `typeOf<T>()` gives you one. Java's answer is older and cleverer:

```java
// A super type token. An anonymous subclass's superclass signature survives erasure.
abstract class TypeRef<T> {
    final Type type;
    protected TypeRef() {
        type = ((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0];
    }
}

Type t = new TypeRef<Map<String, List<Integer>>>() {}.type;   // java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>
```

```kotlin
val t: KType = typeOf<Map<String, List<Int>>>()
t.classifier == Map::class                          // true
t.arguments.size                                    // 2: String and List<Int>
typeOf<List<String>>() == typeOf<List<Int>>()        // false
typeOf<List<String>>() == typeOf<List<String>?>()    // false: nullability counts
```

The Java version is the idea Neal Gafter named **super type tokens**, and it's how Jackson's `TypeReference` and Gson's `TypeToken` work. Erasure removes type arguments from objects but not from declarations (lesson 8), and a class's declared superclass is a declaration. So you create a throwaway anonymous subclass, `new TypeRef<...>() {}`, and read its superclass back. The `{}` is the whole trick: without it there's no subclass, and javac says `TypeRef is abstract; cannot be instantiated`. It has one well-known hole. Inside a generic method, `new TypeRef<List<T>>() {}` records the type *variable*, and prints `java.util.List<T>`.

`typeOf` is the Kotlin replacement. Through a reified parameter it keeps everything: `inline fun <reified T> tokenOf() = typeOf<T>()` called as `tokenOf<List<String>>()` gives the full `List<String>`. That is the difference from lesson 8, where `T::class` kept only `List`. It works without kotlin-reflect, apart from the `toString()` suffix, and `KType` equality is all a map key needs.

When a Java library wants a `java.lang.reflect.Type`, convert with `typeOf<List<CardAuthorized>>().javaType`, which in 2.4.21 still needs `@OptIn(ExperimentalStdlibApi::class)`. A super type token written in Kotlin also works, with a twist: it picks up Kotlin's declaration-site variance as wildcards. `object : TypeRef<Map<String, List<Int>>>() {}` prints `java.util.Map<java.lang.String, ? extends java.util.List<? extends java.lang.Integer>>`, because `Map`'s `V` and `List`'s `E` are declared `out`. `javaType` gives the plain form."""

L = {
    "id": "gen-09",
    "title": "KClass, Class and type tokens",
    "minutes": 40,
    "goal": "By the end you can tell a `KClass`, a Java `Class` and a `KType` apart, explain why `x::class` is a `KClass<out T>`, convert between Kotlin and Java class objects, predict what fails without kotlin-reflect, and choose a `KClass` key or a `KType` key (or a super type token in Java) for a type-safe registry.",
    "warmup": {
        "q": "`val event: PaymentEvent = CardAuthorized(\"pay_1\", 1_200)`. What is the static type of `event::class`?",
        "options": [
            "`KClass<CardAuthorized>`, because that's what the object really is",
            "`KClass<PaymentEvent>`, because that's how `event` is declared",
            "`KClass<out PaymentEvent>`",
            "`KClass<*>`, because classes lose their type at run time"
        ],
        "answer": 2,
        "why": "The compiler knows only that `event` is some `PaymentEvent`; the real class shows up at run time. So it gives you \"the class of some subtype of `PaymentEvent`\", which is `KClass<out PaymentEvent>`, the same idea as Java's `Class<? extends PaymentEvent>` from `getClass()`. Printing it at run time does show `CardAuthorized`. `KClass<*>` would throw away the useful upper bound."
    },
    "sections": [
        {
            "h": "A class is not a type, and objects only know their class",
            "body": S1,
            "figure": {"svg": FIG, "caption": "A KType knows the class, the arguments and the nullability. Its classifier is a KClass, which converts to and from Java's Class. Objects can give you only their class."},
            "try": {
                "title": "Meet the three objects",
                "minutes": 4,
                "steps": [
                    "Run `ClassVsTypeDemo` and read each line. Which of the three objects is printed with Java names and a suffix?",
                    "Run it again with `-Preflect` added to the command, and compare the first and third lines.",
                    "Run `ClassVsTypeDemoJava`. Which Kotlin line has no Java twin at all?"
                ],
                "code": kdemo("ClassVsTypeDemo", "ClassVsTypeDemoJava"),
                "expect": "Kotlin prints `KClass: class java.lang.String (Kotlin reflection is not available)`, `Class:  class java.lang.String` and `KType:  java.util.List<java.lang.String>? (Kotlin reflection is not available)`, then `true`, `true`, `false, false` and `classifier is List::class: true, arguments: 1, nullable: true`. With `-Preflect` the first line becomes `class kotlin.String` and the third `kotlin.collections.List<kotlin.String>?`. Java prints the class, the field's type `java.util.List<java.lang.String>`, `true`, and the argument `class java.lang.String`. Java has no twin for nullability in a type."
            },
            "refs": [
                {"title": "Reflection: class references and KType (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html", "kind": "docs"}
            ]
        },
        {
            "h": "x::class is a KClass<out T>, for the reason lesson 4 gave",
            "body": S2,
            "try": {
                "title": "Ask values for their class",
                "minutes": 4,
                "steps": [
                    "Run `ClassOfValueDemo` (or `ClassOfValueDemoJava`). The loop variable is declared `PaymentEvent`; what does `simpleName` print?",
                    "Uncomment the three wrong moves one at a time. Predict each error first.",
                    "In the Java twin, uncomment the wrong move. Find the captured type in the message."
                ],
                "code": kdemo("ClassOfValueDemo", "ClassOfValueDemoJava"),
                "expect": "Both print `pay_1: CardAuthorized, is a card: true` and `pay_2: RefundIssued, is a card: false`: the run-time class, not the declared type. Kotlin ends with `exact = CardAuthorized, noteClass = String`; Java ends with `getClass() on null: NullPointerException`. Kotlin's errors: (1) `Initializer type mismatch: expected 'KClass<PaymentEvent>', actual 'KClass<out PaymentEvent>'.`, (2) `Expression in class literal has nullable type 'String?'. Use '!!' to make the type non-nullable.`, (3) `Type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.` Java's: `Class<CAP#1> cannot be converted to Class<PaymentEvent>`."
            },
            "refs": [
                {"title": "Object.getClass (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Object.html", "kind": "docs"}
            ]
        },
        {
            "h": "KClass and Class are two views of the same class",
            "body": S3,
            "try": {
                "title": "Check, cast and name a class",
                "minutes": 3,
                "steps": [
                    "Run `ClassApiDemo` and `ClassApiDemoJava`. Compare the two `cast failed:` messages.",
                    "Uncomment the wrong move in `ClassApiDemo.kt` and read the whole deprecation message.",
                    "Replace `RefundIssued::class.safeCast(event)` with `RefundIssued::class.cast(event)` in the first print. What changes?"
                ],
                "code": kdemo("ClassApiDemo", "ClassApiDemoJava"),
                "expect": "Kotlin prints `k.java = CardAuthorized, c.kotlin == k: true, event.javaClass == c: true`, then `isInstance: true, cast(...).cents: 1200, safeCast to RefundIssued: null`, `cast failed: Value cannot be cast to workbench.generics.l09.demo.RefundIssued`, the two names and `int` / `class java.lang.Integer`. Java's cast message is `Cannot cast workbench.generics.l09.demo.CardAuthorized to workbench.generics.l09.demo.RefundIssued`. The wrong move fails with `'val <T : Any> KClass<T>.javaClass: Class<KClass<T>>' is deprecated. Use 'java' property ...`. With `cast` instead of `safeCast`, the program stops with a `ClassCastException` before the try block."
            }
        },
        {
            "h": "Names, checks and casts are free; describing a class needs kotlin-reflect",
            "body": S4,
            "try": {
                "title": "Run one demo with and without kotlin-reflect",
                "minutes": 4,
                "steps": [
                    "Run `ReflectDemo` with the command below. Every line under `-- needs kotlin-reflect` fails. Note which error each one gives.",
                    "Run it again with `-Preflect` at the end of the command. That flag adds kotlin-reflect to the demo's runtime classpath (see `labs/generics/build.gradle.kts`).",
                    "Run `ReflectDemoJava`. Which of the Kotlin answers can Java reflection also give?"
                ],
                "code": kdemo("ReflectDemo", "ReflectDemoJava"),
                "expect": "Without the jar, the first five lines work (`PaymentEvent`, `true`, `true`, `1`, and `class java.lang.String (Kotlin reflection is not available)`), then four lines show `KotlinReflectionNotSupportedError: Kotlin reflection implementation is not found at runtime` and `createInstance()` shows `NoClassDefFoundError: kotlin/reflect/full/KClasses`. With `-Preflect`: `class kotlin.String`, `Origin`, `[CardAuthorized, RefundIssued]`, `true`, `[cents, component1, component2, copy, equals, hashCode, paymentId, toString]` and `NoArg()`. Java prints the fields `[cents, paymentId]`, the methods, and `Origin.INSTANCE: Origin`; it has no notion of a data class."
            }
        },
        {
            "h": "KType keeps what KClass drops: typeOf and super type tokens",
            "body": S5,
            "try": {
                "title": "Capture List<String> two ways",
                "minutes": 4,
                "steps": [
                    "Run `TypeTokenDemo` and `TypeTokenDemoJava`. Compare the two `super type token:` lines.",
                    "Find the line in the Java output where the token failed to capture the real type.",
                    "Uncomment the wrong move in each file, predict, run."
                ],
                "code": kdemo("TypeTokenDemo", "TypeTokenDemoJava"),
                "expect": "Kotlin prints the `typeOf` result `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>> (Kotlin reflection is not available)`, `arguments:        2, ...`, the same type as `javaType` without the suffix, `true`, `false`, and the Kotlin-written token `java.util.Map<java.lang.String, ? extends java.util.List<? extends java.lang.Integer>>`. Java prints its token as `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>`, its two arguments, and `inside a generic method: java.util.List<T>`: the hole. The wrong moves fail with `Only classes are allowed on the left-hand side of a class literal.` and `TypeRef is abstract; cannot be instantiated`."
            },
            "refs": [
                {"title": "typeOf (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html", "kind": "docs"},
                {"title": "KClass (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/-k-class/", "kind": "docs"}
            ]
        }
    ],
    "analogy": "Think of a car dealer's system. A `KClass` is a model name: \"Corolla\". A `KType` is a full order line: \"Corolla, hybrid trim\", or even \"a Corolla, or no car at all\", which is the nullable part. The factory stamps only the model name on each car. So a car in the lot, like an object at run time, can tell you its model and nothing about the order it came from. `x::class` is reading the stamp on a car you only knew as \"some vehicle\": the stamp names a model, and all the compiler could promise in advance was that it would be some kind of vehicle. The analogy breaks for `typeOf`. A real dealership keeps the order line in a file somewhere. In Kotlin a `KType` exists only where the compiler wrote it down, at a call site with a known or reified type, and never inside the object.",
    "in_your_world": "In a Quarkus payment service the edges all speak `Class`: CDI lookups take a `Class`, Temporal's `Workflow.newActivityStub(PaymentActivities::class.java, options)` takes the activity interface's `Class`, and JPA's `find` takes the entity's `Class`. Jackson needs more than a class for a generic body: `objectMapper.readValue(json, object : TypeReference<List<Settlement>>() {})` is a super type token, and `typeOf<List<Settlement>>().javaType` is the Kotlin route to the same `java.lang.reflect.Type`. Inside your own code, keep `KClass` and `KType`. A Kafka consumer that routes each `PaymentEvent` to its handler by `event::class` works with `KClass<out PaymentEvent>` keys, which is the event bus of lesson 11 of this track.",
    "mistake": "The common mistake is keying generic things by class. A registry, cache or handler map uses `KClass` (or Java's `Class`) keys, someone registers a `Repository<Payment>` and later a `Repository<Refund>`, and the second silently replaces the first, because both have the class `Repository`. Nothing fails at registration. Much later, code that asks for the payments repository gets the refunds one, casts its elements to `Payment`, and throws `ClassCastException` far away. People make the mistake because `KClass` works perfectly for every non-generic service they registered first. The fix is to key by full type: a `KType` from `typeOf<T>()` in Kotlin, or a super type token's `Type` in Java. Use `KClass` keys only for types that have no type arguments.",
    "compare": {
        "title": "A type-safe service registry in Java and Kotlin",
        "java": {
            "title": "ServiceRegistry.java",
            "src": "import java.lang.reflect.Type;\nimport java.util.HashMap;\nimport java.util.Map;\nimport java.util.NoSuchElementException;\n\nfinal class ServiceRegistry {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n    private final Map<Type, Object> byType = new HashMap<>();\n\n    // Class<T> and T tied together: the compiler checks the pair\n    <T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n    <T> T get(Class<T> type) {\n        Object impl = byClass.get(type);\n        if (impl == null) throw new NoSuchElementException(\"no service for \" + type.getSimpleName());\n        return type.cast(impl);                                // checked\n    }\n\n    // generic services: a super type token supplies the full type\n    <T> void registerTyped(TypeRef<T> type, T impl) { byType.put(type.type, impl); }\n\n    @SuppressWarnings(\"unchecked\")                              // safe: only registerTyped puts values in\n    <T> T getTyped(TypeRef<T> type) { return (T) byType.get(type.type); }\n}\n\n// registry.register(PaymentGateway.class, gateway);\n// registry.registerTyped(new TypeRef<Repository<Payment>>() {}, payments);"
        },
        "kotlin": {
            "title": "ServiceRegistry.kt",
            "src": "class ServiceRegistry {\n    private val byClass = HashMap<KClass<*>, Any>()\n    private val byType = HashMap<KType, Any>()\n\n    // KClass<T> and T tied together: the compiler checks the pair\n    fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\n    fun <T : Any> get(type: KClass<T>): T {\n        val impl = byClass[type] ?: throw NoSuchElementException(\"no service for \" + type.simpleName)\n        return type.cast(impl)                                 // checked, no kotlin-reflect needed\n    }\n    inline fun <reified T : Any> get(): T = get(T::class)\n\n    // generic services: typeOf supplies the full type\n    fun registerTyped(type: KType, impl: Any) { byType[type] = impl }\n    fun getTyped(type: KType): Any = byType[type] ?: throw NoSuchElementException(\"no service for $type\")\n    inline fun <reified T : Any> registerTyped(impl: T) = registerTyped(typeOf<T>(), impl)\n\n    @Suppress(\"UNCHECKED_CAST\")                                 // safe: only registerTyped<T> puts values in\n    inline fun <reified T : Any> getTyped(): T = getTyped(typeOf<T>()) as T\n}\n\n// registry.register(PaymentGateway::class, gateway); registry.get<PaymentGateway>()\n// registry.registerTyped<Repository<Payment>>(payments)"
        },
        "note": "Both are what Joshua Bloch calls a typesafe heterogeneous container (Effective Java, Item 33): one map holds values of many types, and the key carries the type, so `get` can return a `T` with a checked `cast`. The KClass half is a direct translation: `KClass<T>` for `Class<T>`, `type.cast` in both. The differences are at the call site and for generic types. Kotlin adds reified wrappers, so callers write `get<PaymentGateway>()` and `registerTyped<Repository<Payment>>(repo)`. For generic types Java needs a super type token object at each call (`new TypeRef<Repository<Payment>>() {}`), while Kotlin's `typeOf<T>()` is computed from the reified `T` with no subclass and no hole for type variables. In both, the full-type half needs one unchecked cast, which is safe because the map is private and filled only through the typed `register` method."
    },
    "worked": {
        "title": "Build the registry's KClass half, then find where it stops",
        "steps": [
            {"say": "A first draft keys services by class and returns `Any`. It compiles, but every caller has to cast, and nothing stops a wrong registration.",
             "code": "class ServiceRegistry {\n    private val byClass = HashMap<KClass<*>, Any>()\n    fun register(type: KClass<*>, impl: Any) { byClass[type] = impl }\n    fun get(type: KClass<*>): Any? = byClass[type]\n}\n\nregistry.register(PaymentGateway::class, AlwaysLowRisk())        // compiles: oops\nval gateway = registry.get(PaymentGateway::class) as PaymentGateway   // ClassCastException here",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class ServiceRegistry {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n    void register(Class<?> type, Object impl) { byClass.put(type, impl); }\n    Object get(Class<?> type) { return byClass.get(type); }\n}\n\nregistry.register(PaymentGateway.class, new AlwaysLowRisk());           // compiles: oops\nPaymentGateway gateway = (PaymentGateway) registry.get(PaymentGateway.class);   // ClassCastException here"},
            {"say": "1. Tie the key and the value together with one type parameter. Now `PaymentGateway::class` is a `KClass<PaymentGateway>`, so `T` is `PaymentGateway` and the implementation must be one. 2. Return a `T` with a checked `cast`. Self-check before reading on: why is `type.cast` safe here when `as T` in lesson 8 was not? (The `KClass` object is a real run-time value, so `cast` can really check.)",
             "code": "fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\nfun <T : Any> get(type: KClass<T>): T {\n    val impl = byClass[type] ?: throw NoSuchElementException(\"no service for \" + type.simpleName)\n    return type.cast(impl)\n}\n\nregistry.register(PaymentGateway::class, AlwaysLowRisk())\n// error: Argument type mismatch: actual type is 'AlwaysLowRisk', but 'PaymentGateway' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "<T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n<T> T get(Class<T> type) {\n    Object impl = byClass.get(type);\n    if (impl == null) throw new NoSuchElementException(\"no service for \" + type.getSimpleName());\n    return type.cast(impl);\n}\n\nregistry.register(PaymentGateway.class, new AlwaysLowRisk());\n// error: method register in class ServiceRegistry cannot be applied to given types;\n//   reason: inference variable T has incompatible bounds"},
            {"say": "3. Add the reified wrapper for Kotlin callers. It only touches the public `get(type)`, as lesson 8 required of public inline functions.",
             "code": "inline fun <reified T : Any> get(): T = get(T::class)\n\nval gateway: PaymentGateway = registry.get()      // T from the expected type\nval fraud = registry.get<FraudCheck>()",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "// Java keeps passing the class:\nPaymentGateway gateway = registry.get(PaymentGateway.class);\nFraudCheck fraud = registry.get(FraudCheck.class);"},
            {"say": "4. Now try a generic service. `Repository::class` is a `KClass<Repository<*>>`, so the best `get` can return is a `Repository<*>`, and a second `register(Repository::class, refunds)` overwrites the payments repository without a word. Asking for `Repository<Payment>` explicitly fails at compile time: `Initializer type mismatch: expected 'Repository<Payment>', actual 'Repository<*>'.` That's the point where the key has to become a `KType`, which is the second half of the lab.",
             "code": "registry.register(Repository::class, payments)\nregistry.register(Repository::class, refunds)        // replaces payments: same class\nval any: Repository<*> = registry.get(Repository::class)\nval p: Repository<Payment> = registry.get(Repository::class)\n// error: Initializer type mismatch: expected 'Repository<Payment>', actual 'Repository<*>'.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "registry.register(Repository.class, payments);       // raw Class: Repository.class has no <Payment>\nregistry.register(Repository.class, refunds);        // replaces payments\nRepository<?> any = registry.get(Repository.class);"}
        ]
    },
    "lab": {
        "title": "A service registry keyed by KClass, then by KType",
        "minutes": 14,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l09/ServiceRegistry.kt",
            f"{LAB}/main/kotlin/workbench/generics/l09/Model.kt",
            f"{LAB}/main/kotlin/workbench/generics/l09/Callers.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l09.*'",
        "steps": [
            "Skim `Model.kt` (the services) and `Callers.kt` (the same trick as lesson 8: tests reach your inline functions through it). Run the tests: all seven fail.",
            "Part 1. Write `register` and `get(type)` in `ServiceRegistry.kt`. Throw `NoSuchElementException(\"no service for \" + type.simpleName)` when nothing is registered, and return with `type.cast(...)`.",
            "Make the no-argument `get()` inline with `reified T : Any`, delegating with `T::class`. Four tests should now pass, including the one that shows a `KClass` key holding only one `Repository`.",
            "Part 2. Write `registerTyped(type: KType, impl)` and `getTyped(type: KType)` with the `byType` map. The missing-service message is `\"no service for \" + type`.",
            "Make the two one-argument versions inline and reified, using `typeOf<T>()`. In `getTyped<T>()`, cast with `as T` under `@Suppress(\"UNCHECKED_CAST\")` and write one comment saying why the cast is safe.",
            "Run the tests until all seven pass."
        ],
        "hints": [
            "`val impl = byClass[type] ?: throw NoSuchElementException(\"no service for \" + type.simpleName)` then `return type.cast(impl)`. `cast` needs `import kotlin.reflect.cast`.",
            "`typeOf` needs `import kotlin.reflect.typeOf`. It works without kotlin-reflect, and two `typeOf<Repository<Payment>>()` calls give equal keys.",
            "The reified functions must call only the public `get(type)`, `registerTyped(type, impl)` and `getTyped(type)`: a public inline function can't read the private maps."
        ],
        "done_when": "All seven tests in `ServiceRegistryTest` pass."
    },
    "drill": {
        "title": "Write a KClass registry from memory",
        "minutes": 5,
        "prompt": "Close this page. Write a registry with `register(type, impl)`, `get(type)` and a reified `get<T>()` in Kotlin, using `KClass` keys and a checked cast. Then write the Java version with `Class<T>`. Finally, write the one line that gives you a key for `List<String>` in Kotlin.",
        "answer": {
            "lang": "kotlin",
            "src": "class Registry {\n    private val byClass = HashMap<KClass<*>, Any>()\n\n    fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\n    fun <T : Any> get(type: KClass<T>): T =\n        type.cast(byClass[type] ?: throw NoSuchElementException(\"no service for ${type.simpleName}\"))\n\n    inline fun <reified T : Any> get(): T = get(T::class)\n}\n\nval key: KType = typeOf<List<String>>()     // List<String>::class does not compile",
            "alt": {"lang": "java", "title": "Registry.java", "src": "final class Registry {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n\n    <T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n    <T> T get(Class<T> type) {\n        Object impl = byClass.get(type);\n        if (impl == null) throw new NoSuchElementException(\"no service for \" + type.getSimpleName());\n        return type.cast(impl);\n    }\n}\n\n// a key for List<String>: a super type token\nType key = new TypeRef<List<String>>() {}.type;"}
        }
    },
    "recap": [
        "A `KClass` (or Java `Class`) describes a class: no type arguments, never nullable. A `KType` describes a full type: class, arguments and nullability.",
        "`CardAuthorized::class` is an exact `KClass<CardAuthorized>`. `event::class` is a `KClass<out PaymentEvent>`, because the real class is some unknown subtype; Java's `getClass()` returns `Class<? extends X>` for the same reason.",
        "Convert with `.java` and `.kotlin`; a value's `Class` is `x.javaClass`. `isInstance`, `cast` and `safeCast` are the checked `is`, `as` and `as?`.",
        "Names, identity, checks, casts and `typeOf` work without kotlin-reflect. `objectInstance`, `sealedSubclasses`, `isData`, `members` and `kotlin.reflect.full` need it.",
        "`typeOf<List<String>>()` keeps type arguments, even through a reified `T`. Java gets the same from a super type token, `new TypeRef<List<String>>() {}`.",
        "Key a registry by `KClass` for plain types and by `KType` for generic ones such as `Repository<Payment>`."
    ],
    "quiz": [
        {
            "q": "`val event: PaymentEvent = loadEvent()`. Which line compiles?",
            "options": [
                "`val k: KClass<PaymentEvent> = event::class`",
                "`val k: KClass<CardAuthorized> = event::class`",
                "`val k: KClass<out PaymentEvent> = event::class`",
                "`val k: KClass<PaymentEvent?> = event::class`"
            ],
            "answer": 2,
            "why": "A bound class reference gives the class of some subtype of the static type: `KClass<out PaymentEvent>`. The exact `KClass<PaymentEvent>` is what a class literal `PaymentEvent::class` gives. `KClass<CardAuthorized>` would need the compiler to know the run-time class, and `KClass<PaymentEvent?>` breaks the `T : Any` bound."
        },
        {
            "q": "A Gradle project without kotlin-reflect runs four lines. Which one throws?",
            "options": [
                "`CardAuthorized::class.simpleName`",
                "`CardAuthorized::class.isInstance(event)`",
                "`typeOf<List<String>>().arguments`",
                "`Origin::class.objectInstance`"
            ],
            "answer": 3,
            "why": "`objectInstance` describes a declaration, so it needs kotlin-reflect and throws `KotlinReflectionNotSupportedError`. Names, instance checks and `typeOf` are handled by the standard library. Printing a `KClass` or `KType` also works, just with the `(Kotlin reflection is not available)` suffix."
        },
        {
            "q": "A registry must hold a `Repository<Payment>` and a `Repository<Refund>` at the same time. Which key type do you use?",
            "options": [
                "`KClass<*>`, from `Repository::class`",
                "`KType`, from `typeOf<Repository<Payment>>()`",
                "`Class<*>`, from `Repository::class.java`",
                "The class's `simpleName`"
            ],
            "answer": 1,
            "why": "Both repositories have the same class, so every class-based key (KClass, Class, or a name) collides and the second registration overwrites the first. A `KType` includes the type argument, so the two keys differ. In Java, a super type token's `Type` plays the same role."
        },
        {
            "q": "Java: `static <T> Type listOf() { return new TypeRef<List<T>>() {}.type; }` with the usual `TypeRef` super type token. What does `Tokens.<String>listOf()` return?",
            "options": [
                "`java.util.List<T>`: the token records the type variable, not `String`",
                "`java.util.List<java.lang.String>`",
                "The raw `java.util.List`",
                "It throws `ClassCastException`, because `T` is not a `ParameterizedType`"
            ],
            "answer": 0,
            "why": "The anonymous subclass is compiled once, inside the generic method, and its declared superclass is literally `TypeRef<List<T>>`. The caller's `String` never reaches it. Kotlin's `typeOf<T>()` with a reified `T` doesn't have this hole, because the compiler writes the real type at each call site."
        },
        {
            "q": "From \"Type erasure and reified type parameters\": `fun <T : Any> lookup(registry: ServiceRegistry): T = registry.get<T>()`, where `get<T>()` is `inline` with `reified T`. What happens?",
            "options": [
                "It compiles and returns the service for whatever `T` the caller picks",
                "It compiles, but always returns the first service registered",
                "It doesn't compile: `Cannot use 'T' as reified type parameter. Use a class instead.`",
                "It compiles and throws `ClassCastException` at run time"
            ],
            "answer": 2,
            "why": "`lookup`'s own `T` is an ordinary, erased type parameter, so there's no class to copy into the inlined `get`. Make `lookup` itself `inline` with a `reified T`, or give it a `type: KClass<T>` parameter and call `registry.get(type)`.",
            "from": "gen-08"
        }
    ],
    "flashcards": [
        {"front": "KClass or KType: which one knows that a value is a `List<String>?` and not just a `List`?", "back": "`KType` (from `typeOf<List<String>?>()`). A `KClass` describes only the class: no type arguments, never nullable."},
        {"front": "Why is `event::class` a `KClass<out PaymentEvent>` when `event: PaymentEvent`?", "back": "The real class is some unknown subtype of `PaymentEvent`, and `out` means exactly that. Java's `getClass()` returns `Class<? extends PaymentEvent>` for the same reason."},
        {"front": "Why is `KClass` declared `KClass<T : Any>`?", "back": "There is no class for a nullable type: `String?` is backed by the class `String`. So `KClass<String?>` and `nullableValue::class` don't compile."},
        {"front": "How do you convert between `KClass` and Java's `Class`?", "back": "`k.java` gives the `Class`; `c.kotlin` gives the `KClass`. A value's `Class` is `x.javaClass`."},
        {"front": "Without kotlin-reflect, what does `Origin::class.objectInstance` do?", "back": "Throws `KotlinReflectionNotSupportedError`. Anything that describes declarations needs kotlin-reflect; names, checks, casts and `typeOf` don't."},
        {"front": "How do you get a runtime object for the full type `List<String>` in Kotlin?", "back": "`typeOf<List<String>>()`, a `KType`. `List<String>::class` doesn't compile: only classes are allowed on the left of `::class`."},
        {"front": "What is a super type token?", "back": "An anonymous subclass, `new TypeRef<List<String>>() {}`, whose generic superclass is read back by reflection. It's how Jackson's `TypeReference` works."}
    ],
    "terms": [
        {"term": "KClass", "plain": "Kotlin's run-time object for a class: `CardAuthorized::class`. No type arguments, never nullable."},
        {"term": "Class", "plain": "Java's run-time object for a class: `CardAuthorized.class`, or `CardAuthorized::class.java` from Kotlin."},
        {"term": "KType", "plain": "A full type at run time: class, type arguments and nullability. Made by `typeOf<T>()`."},
        {"term": "Class literal", "plain": "`Name::class`: the class you name in code. Its type is exact, `KClass<Name>`."},
        {"term": "Bound class reference", "plain": "`value::class`: the run-time class of a value, typed `KClass<out DeclaredType>`."},
        {"term": "kotlin-reflect", "plain": "The separate jar that answers questions about declarations: members, sealed subclasses, data classes."},
        {"term": "Super type token", "plain": "A Java trick that captures a full generic type through an anonymous subclass's superclass signature."},
        {"term": "Typesafe heterogeneous container", "plain": "One map holding values of many types, with the type as the key, so `get` can return a `T` safely."}
    ],
    "explain_back": {
        "prompt": "A teammate asks: \"Why do we need `typeOf` at all? `T::class` already tells us the type.\" Explain the difference between a `KClass` and a `KType` in your own words, using the `Repository<Payment>` and `Repository<Refund>` example, and say what Java uses instead.",
        "answer": "A `KClass` describes a class, and a class is shared by every type built on it. `Repository<Payment>` and `Repository<Refund>` are two different types, but both have the class `Repository`, so `T::class` gives the same `KClass` for both, and a map keyed by it can hold only one of them. Nullability is lost the same way: `String` and `String?` share `String::class`. A `KType` describes the whole type: the class plus its type arguments plus whether it's nullable. `typeOf<Repository<Payment>>()` and `typeOf<Repository<Refund>>()` are different keys, so a registry keyed by `KType` can hold both. The JVM never stores this on objects, because of erasure; the compiler writes the `KType` down at the call site, which is why `typeOf` needs a known or reified type. Java has no `KType`. It uses a super type token: an anonymous subclass like `new TypeRef<Repository<Payment>>() {}`, whose declared superclass keeps the type arguments and can be read back with reflection."
    },
    "deeper": {
        "minutes": 10,
        "body": "Why doesn't a `KType` need kotlin-reflect, when so much else does? Because `typeOf<T>()` is mostly built by the compiler. At each call site it emits code that constructs the type from parts it already knows: the classifier (`List::class`), the arguments, the variance of each argument and the nullability flag. The standard library holds a small implementation of `KType` for that. Answering `sealedSubclasses` is different: it means reading Kotlin's own metadata out of the class file, and the reader for that metadata is what kotlin-reflect contains.\n\n`KType` also records variance and stars. `typeOf<MutableList<out Number>>().arguments.single().variance` is `OUT`, and `typeOf<List<*>>().arguments` prints `[*]`. So a registry keyed by `KType` treats `MutableList<out Number>` and `MutableList<Number>` as different keys, which is correct but can surprise you: the key must be written with exactly the same type on both sides.\n\nThe docs page on reflection mentions that the `kotlinc` command-line compiler adds kotlin-reflect by default (you can opt out with `-no-reflect`). That's why a snippet that prints `class kotlin.String` in a quick command-line experiment prints `class java.lang.String (Kotlin reflection is not available)` inside your Gradle service. If you add kotlin-reflect to a service, add it on purpose: it's a 3.8 MB jar, and its first use loads and parses metadata, which costs a little time once per class.\n\nLast, the `javaClass` rule from section 3 has a reason. `javaClass` is an extension property on every type, and a `KClass` is a value like any other, so `k.javaClass` would mean the class that implements the `KClass` object, not the class it describes. The standard library declares a deprecated overload for exactly that receiver, and in 2.4.21 using it is an error. `x.javaClass` on ordinary values is unaffected."
    },
    "sources": [
        {"title": "Reflection (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html"},
        {"title": "KClass (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/-k-class/"},
        {"title": "typeOf (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html"},
        {"title": "Object.getClass (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Object.html"}
    ]
}

out = ROOT / "content/lessons/gen-09.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
