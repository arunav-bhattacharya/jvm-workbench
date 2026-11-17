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


FIG = ('<svg viewBox="0 0 700 300" role="img" aria-label="Three objects. A KType such as typeOf of List of String nullable knows the class, the type arguments and the nullability: the whole label. '
       'Its classifier is a KClass, List::class, which has no arguments and is never nullable: the one-word note. The KClass and Java\'s Class for java.util.List convert into each other with .java and .kotlin. '
       'An object at run time can only give you its class, never its full type.">'
       + panel(15, 30, 230, 120, "KType: the whole label", ["typeOf&lt;List&lt;String&gt;?&gt;()", "arguments: [String]", "nullable: true"], "box-a", "t-a")
       + panel(300, 30, 170, 120, "KClass: the note", ["List::class", "no arguments", "never nullable"], "box", "t")
       + panel(525, 30, 160, 120, "Class", ["java.util.List", "the same note,", "on Java's paper"], "box-b", "t-b")
       + '<line class="ln-a" x1="247" y1="90" x2="296" y2="90" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="272" y="80" text-anchor="middle">classifier</text>'
         '<line class="ln" x1="472" y1="80" x2="521" y2="80" marker-end="url(#arr)"/>'
         '<line class="ln" x1="521" y1="102" x2="472" y2="102" marker-end="url(#arr)"/>'
         '<text class="t-s t-code" x="497" y="72" text-anchor="middle">.java</text>'
         '<text class="t-s t-code" x="497" y="120" text-anchor="middle">.kotlin</text>'
       + '<rect class="box-dim" x="300" y="200" width="385" height="44" rx="8"/>'
         '<text class="t-s t-code" x="492" y="227" text-anchor="middle">an object at run time: listOf("Gala")</text>'
         '<line class="ln-d" x1="440" y1="198" x2="400" y2="154" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="375" y="182" text-anchor="middle">x::class</text>'
         '<line class="ln-d" x1="560" y1="198" x2="600" y2="154" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="625" y="182" text-anchor="middle">x.javaClass</text>'
         '<text class="t-s t-m" x="130" y="190" text-anchor="middle">only the compiler can</text>'
         '<text class="t-s t-m" x="130" y="208" text-anchor="middle">write a KType down,</text>'
         '<text class="t-s t-m" x="130" y="226" text-anchor="middle">at a call site: typeOf&lt;T&gt;()</text>'
         '<text class="t-s t-m" x="350" y="284" text-anchor="middle">Objects know their class. Only code knows full types.</text>'
         '</svg>')

OPENING = """In the last lesson, a second clerk stood at the storeroom door. Before each label was torn off, the clerk copied it onto a note: "apples". Today we pick up that note and look at it closely.

The shop's office keeps a card index, a small drawer of cards. Each card is filed under a note that names a tool, such as "Scale" or "Label printer", and says where to find it. Then the shop opens a second shelf. The apple shelf and the lemon shelf are both, in one word, "Shelf". The second card pushes the first one out, and nobody notices until someone fetches lemons for an apple order.

In code, the one-word note is a `KClass`. The trap is easy to fall into, because for plain classes a class behaves exactly like a type.

Type erasure and reified type parameters asked what can keep the whole type `List<Apple>`. In this lesson, we'll meet three objects that describe classes and types, ask a fruit for its class, cross over to Java's view, find what needs an extra library, and file the shelves under their whole labels. Before we start, make a guess, and keep it in mind."""

S1 = """Start with what a running program can ask. Lesson 3 of this track pulled classes and types apart. The class `String` backs two types, `String` and `String?`, and the class `List` backs `List<String>`, `List<Int>` and `List<Apple>?`. Lesson 8 added **erasure**: the compiler checks each type argument (the real type in the angle brackets, such as `String` in `List<String>`) and then drops it, so at run time each object keeps its class and nothing more. A box on the shelf still knows it's a box. It no longer knows what its label said.

Kotlin's **reflection** API, the part of the library that lets code inspect classes while the program runs, gives each idea its own object. Most confusion about `KClass` comes from mixing them up:

- A `KClass` describes a class: `String::class`, `Apple::class`, `List::class`. It has no type arguments and is never nullable. This is the one-word note.
- A `Class` is Java's object for the same class: `String.class` in Java, `String::class.java` in Kotlin. It's the same note, written on Java's paper.
- A `KType` describes a full type: the class, its type arguments, and whether it may be null. `typeOf<List<String>?>()` gives you one. This is the whole label: "a list of strings, or nothing".

```java
Class<String> c = String.class;                                  // Java's class object
boolean same = new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass();   // true
// Java has no KType. The closest thing is a Type read from a declaration, such as a field:
Type t = Shop.class.getDeclaredField("varieties").getGenericType();   // java.util.List<java.lang.String>
```

```kotlin
val k: KClass<String> = String::class                 // Kotlin's class object
val c: Class<String> = String::class.java             // the Java one, for Java code
val t: KType = typeOf<List<String>?>()                 // List, with argument String, nullable
val same = ArrayList<String>()::class == ArrayList<Int>()::class   // true
```

To pick the right one, ask what you want to know. "What kind of thing is this?" is a question about a class, and a `KClass` or a `Class` answers it. "A list of *what*?" and "may it be null?" are questions about a type, and only a `KType` can answer them. In the figure, the arrows from the object at run time reach only the class objects. A `KType` comes from code: the compiler writes it down at a call site.

Here the clerk picture breaks a little. A real clerk could copy the full label onto every note. Kotlin writes a `KType` only where you ask for one with `typeOf`, and never stores it inside the object.

One warning before you run anything. Without the kotlin-reflect library on the classpath (the list of jars and folders a program loads its classes from), Kotlin prints these objects with a little apology attached:

```text
class java.lang.String (Kotlin reflection is not available)
java.util.List<java.lang.String>? (Kotlin reflection is not available)
```

Nothing is broken. To print Kotlin names such as `kotlin.String`, `toString()` needs that library, so it falls back to Java names and says so. A Gradle project doesn't include kotlin-reflect unless you ask for it, while the `kotlinc` command-line compiler adds it by default, so the same code can print differently in the two. The fourth section of this lesson shows what else the library adds.

**Objects know their class. Only code knows full types.**

We've named the three objects. Next, we'll ask a piece of fruit for its own note, and see what type the compiler gives the answer."""

S2 = """There are two ways to get a `KClass`. A **class literal**, `Apple::class`, names a class you know while you write the code, and its type is exact: `KClass<Apple>`. A **bound class reference**, `fruit::class`, asks a value for its class while the program runs. Its type has an `out` in it:

```java
Fruit fruit = new Apple("Gala", 180);
Class<? extends Fruit> c = fruit.getClass();        // what getClass() is declared to return
Class<Fruit> strict = fruit.getClass();             // error: Class<CAP#1> cannot be converted to Class<Fruit>
```

```kotlin
val fruit: Fruit = Apple("Gala", 180)
val k: KClass<out Fruit> = fruit::class             // the class of SOME Fruit
val strict: KClass<Fruit> = fruit::class            // error: expected 'KClass<Fruit>', actual 'KClass<out Fruit>'
```

Why the `out`? The compiler knows only that `fruit` is *some* `Fruit`. When the program runs, it turns out to be an `Apple`, but it could have been a `Lemon`. So the most the compiler can promise is "the class of some subtype of `Fruit`". That is what `out` meant in lesson 4: the apple dispenser, which hands out some kind of fruit and takes nothing in. Java says the same with `? extends`. The Javadoc of `Object.getClass()` says the result is `Class<? extends |X|>`, where `|X|` is the erased type of the expression.

The `out` doesn't stop you from using the answer. Everything that hands information out still works: `fruit::class.simpleName`, `fruit::class == Apple::class`, and `cast`, which hands back a `Fruit`. What you can't do is pass it where an exact `KClass<Fruit>` is required. The compiler makes no exception for final classes either: `"Gala"::class` is a `KClass<out String>`.

The other half of `KClass<T : Any>` is its bound, the "no nulls" sign from lesson 2. There is no class for a nullable type, because `String?` is backed by the class `String`. So `KClass<String?>` is an error, and so is asking a value that may be null for its class:

```text
val kn: KClass<String?>? = null
Type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.

val note: String? = ...
note::class
Expression in class literal has nullable type 'String?'. Use '!!' to make the type non-nullable.
```

Write `note?.let { it::class }` instead, and you get a `KClass<out String>?`, which is null when there's no value to ask. Java has no such check at compile time: `note.getClass()` throws `NullPointerException` when `note` is null.

**A value can tell you only the class of some subtype. Use a class literal when you need an exact `KClass<T>`.**

Kotlin's note and Java's note describe the same class. Next, we'll move between them, and put them to work."""

S3 = """On the JVM, every `KClass` wraps a `java.lang.Class`, and two properties move you between them. You'll do it often at the edge of your code, where it calls a Java library:

```java
Class<Apple> c = Apple.class;
boolean isApple = c.isInstance(fruit);          // true
Apple gala = c.cast(fruit);                     // checked: ClassCastException if not
String name = c.getSimpleName();                // "Apple"
Class<?> runtime = fruit.getClass();            // the object's class
```

```kotlin
val k: KClass<Apple> = Apple::class
val c: Class<Apple> = k.java                    // KClass to Class, for Java code
val back: KClass<Apple> = c.kotlin              // Class to KClass
k.isInstance(fruit)                             // true
val gala: Apple = k.cast(fruit)                 // checked: ClassCastException if not
val lemon: Lemon? = Lemon::class.safeCast(fruit)   // null instead of throwing
k.simpleName                                    // "Apple"
fruit.javaClass                                 // the object's Class, like Java's getClass()
```

These are lesson 8's class-token tools, in Kotlin's spelling. `isInstance` is a checked `is`, `cast` is a checked `as`, and `safeCast` is a checked `as?`. (`cast` and `safeCast` are extension functions, functions added to `KClass` from outside it, in the package `kotlin.reflect`, so they need an import.) A failed `cast` throws `ClassCastException: Value cannot be cast to workbench.generics.l09.demo.Lemon`. Names work out of the box, `simpleName` and `qualifiedName`, and so does equality: `fruit::class == Apple::class` is `true`.

These checks are real, unlike the `as T` of lesson 8, because the `KClass` object exists while the program runs and knows what to compare against. The card index's `get` will rely on exactly that.

Two traps wait here. The first is from lesson 8: `Int::class.java` is the primitive class `int`, and `Int::class.javaObjectType` is the boxed `java.lang.Integer`. The second is `javaClass`. On a value, `fruit.javaClass` is the object's `Class`. On a `KClass`, it would be the class of the `KClass` object itself, an internal Kotlin class. Kotlin 2.4.21 rejects it with a deprecation error that says what you meant:

```text
k.javaClass
'val <T : Any> KClass<T>.javaClass: Class<KClass<T>>' is deprecated. Use 'java' property to get Java class corresponding to this Kotlin class ...
```

Which one should your code hold? Inside Kotlin code, prefer the `KClass`. It has `safeCast`, it's what other Kotlin APIs hand you, and it's what this lesson's card index files its cards under. At the edge, pass `.java` to the Java library and keep the `KClass` on your side.

**Inside Kotlin, keep a `KClass`. Hand `.java` to Java code at the edge.**

A note can name a class, check a value against it and cast. Can it also describe the class: its properties, its subclasses?"""

S4 = """A `KClass` offers many more members: `objectInstance`, `sealedSubclasses`, `isData`, `members`, `constructors`, `supertypes`. Your code compiles against all of them, because the standard library declares them. But the code that *answers* them lives in a separate jar, **kotlin-reflect**, about 3.8 MB in 2.4.21. Think of it as a thick reference book about every class, kept in another room. A Gradle project doesn't fetch the book unless you add it, and without it these calls fail while the program runs:

```text
Storeroom::class.objectInstance
KotlinReflectionNotSupportedError: Kotlin reflection implementation is not found at runtime. Make sure you have kotlin-reflect.jar in the classpath
```

`Storeroom` in the demo is a Kotlin `object`, a class with exactly one instance, and `objectInstance` asks for that instance. A rule of thumb holds up well: **names, identity, instance checks, casts and `typeOf` are free; anything that lists or describes declarations needs kotlin-reflect.** A declaration is a piece of code that introduces a name, such as a class, a property or a function.

| Works with the standard library alone | Needs kotlin-reflect |
|---|---|
| `simpleName`, `qualifiedName`, `==`, `.java`, `.kotlin` | `objectInstance`, `sealedSubclasses`, `isData`, `isSealed` |
| `isInstance`, `cast`, `safeCast` | `members`, `constructors`, `typeParameters`, `supertypes` |
| `typeOf<T>()` with `classifier`, `arguments`, `isMarkedNullable` | `kotlin.reflect.full` extensions such as `createInstance()` |

The `kotlin.reflect.full` extensions fail differently, with `NoClassDefFoundError: kotlin/reflect/full/KClasses`, because that class isn't in the standard library at all.

Java reflection needs no extra jar, and it works on Kotlin classes too:

```java
Apple.class.getDeclaredFields();                    // [grams, name]
Storeroom.class.getField("INSTANCE").get(null);     // a Kotlin object is a static INSTANCE field
```

```kotlin
Apple::class.java.declaredFields                    // the same Java reflection, from Kotlin
Storeroom::class.objectInstance                     // the Kotlin way: needs kotlin-reflect
```

So when a Java-level answer is enough (fields, methods, annotations), go through `.java` and skip the dependency. When you need Kotlin-level facts, such as whether a class is a data class, which subclasses a sealed interface has, or whether a property may be null, add kotlin-reflect, and add it on purpose.

Whatever you add, a `KClass` still has no room for "of apples". Back to the card index and its two shelves."""

S5 = """Now the problem from the opening. A card index keyed by `KClass` works for the scale and the label printer, because neither has a type argument. It can't hold a `Shelf<Apple>` and a `Shelf<Lemon>` at the same time. Both have the class `Shelf`, so the second card silently replaces the first, and nothing fails until someone asks for apples and gets lemons. You can't even write the class of the type you mean:

```text
val k = Shelf<Apple>::class
Only classes are allowed on the left-hand side of a class literal.
```

A `KType` keeps the type arguments and the nullability, and in Kotlin `typeOf<T>()` makes one. Java's answer is older, and cleverer than it looks:

```java
// A super type token. An anonymous subclass's superclass keeps its type arguments.
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

The Java version is the idea Neal Gafter named **super type tokens**. Lesson 8 said that erasure removes type arguments from objects but not from declarations, and a class's declared superclass is a declaration. So you create a throwaway **anonymous subclass**, a class with no name written right where it's used, `new TypeRef<...>() {}`, and read its superclass back with reflection. It's the label carved into a shelf's frame, where the clerk's hands never reach. The `{}` is the whole trick: two characters that do more work than any others in this lesson. Without them there's no subclass, and javac says `TypeRef is abstract; cannot be instantiated`. The trick has one well-known hole. Inside a generic method, `new TypeRef<List<T>>() {}` records the type *variable* itself, and prints `java.util.List<T>`.

`typeOf` has no such hole. Through a reified type parameter, one whose real type an inline function receives at each call site, it keeps everything: `inline fun <reified T> tokenOf() = typeOf<T>()`, called as `tokenOf<List<String>>()`, gives the full `List<String>`. That's the difference from lesson 8, where `T::class` kept only `List`. `typeOf` works without kotlin-reflect, apart from the apology in `toString()`, and `KType` equality is all a map key needs. File the shelves under `typeOf<Shelf<Apple>>()` and `typeOf<Shelf<Lemon>>()`, and the two cards sit side by side. That's the second half of the lab.

When a Java library wants a `java.lang.reflect.Type`, convert with `typeOf<List<Apple>>().javaType`, which in 2.4.21 still needs `@OptIn(ExperimentalStdlibApi::class)`. A super type token written in Kotlin works too, with a twist: it picks up Kotlin's declaration-site variance (the `out` and `in` written on a class) as Java wildcards. `object : TypeRef<Map<String, List<Int>>>() {}` prints `java.util.Map<java.lang.String, ? extends java.util.List<? extends java.lang.Integer>>`, because `Map`'s `V` and `List`'s `E` are declared `out`. `javaType` gives the plain form.

**Key a container by `KClass` for plain types, and by `KType` for generic ones.**

Know the limit, too. A `KType` exists only where the compiler wrote it, at a call site with a known or reified type. A box pulled off the shelf can still tell you only its class."""

ASIDE = {
    "title": "Why do JSON libraries ask for a TypeReference?",
    "body": "JSON is a plain-text format for data, and a JSON library turns that text into objects. To build a `List<Apple>`, it must know the element type, and a `Class` can only say `List`, so it would fill the list with maps instead of apples. Java libraries therefore take a super type token: Jackson, a widely used JSON library, calls it `TypeReference`, and Gson calls it `TypeToken`. From Kotlin you can write `object : TypeReference<List<Apple>>() {}`, or pass `typeOf<List<Apple>>().javaType` where a library accepts a `Type`. Jackson's Kotlin module also reads Kotlin facts such as nullability, which is why it depends on kotlin-reflect."
}

CLOSING = """We started at the office card index, where the apple shelf and the lemon shelf fought over one card. A `KClass` is the one-word note: it names a class, checks values and casts, and on the JVM it's the same class as Java's `Class`. A value's note is a `KClass<out T>`. A `KType` from `typeOf` is the whole label, `Shelf<Apple>`, and Java gets one from a super type token.

Search your code for a map keyed by `KClass<*>` or `Class<?>`. If anything generic is ever stored in it, two of its entries may share one card.

Next, we'll meet types that must name their own kind. How can a setter in a base class return the subclass that called it?"""

L = {
    "id": "gen-09",
    "title": "KClass, Class and type tokens",
    "minutes": 40,
    "goal": "By the end you can tell a `KClass`, a Java `Class` and a `KType` apart, explain why `x::class` is a `KClass<out T>`, convert between Kotlin and Java class objects, predict what fails without kotlin-reflect, and choose a `KClass` key or a `KType` key (or a super type token in Java) for a type-safe container.",
    "opening": OPENING,
    "warmup": {
        "q": "`val fruit: Fruit = Apple(\"Gala\", 180)`. What is the static type of `fruit::class`, the type the compiler gives it?",
        "options": [
            "`KClass<Apple>`, because that's what the object really is",
            "`KClass<Fruit>`, because that's how `fruit` is declared",
            "`KClass<out Fruit>`",
            "`KClass<*>`, because classes lose their type at run time"
        ],
        "answer": 2,
        "why": "The compiler knows only that `fruit` is some `Fruit`; the real class shows up at run time. So it gives you \"the class of some subtype of `Fruit`\", which is `KClass<out Fruit>`, the same idea as Java's `Class<? extends Fruit>` from `getClass()`. Printing it at run time does show `Apple`. `KClass<*>` would throw away the useful upper bound, and `KClass<Fruit>` would promise more than the compiler knows."
    },
    "sections": [
        {
            "h": "The one-word note and the whole label: KClass, Class and KType",
            "body": S1,
            "figure": {"svg": FIG, "caption": "A KType is the whole label: class, arguments and nullability. Its classifier is a KClass, the one-word note, which converts to and from Java's Class. An object can give you only its class."},
            "try": {
                "title": "Meet the three objects",
                "minutes": 4,
                "steps": [
                    "Run `ClassVsTypeDemo` and read each line. Which of the three objects are printed with Java names and the apology?",
                    "Run it again with `-Preflect` added to the end of the command, and compare the first and third lines.",
                    "Run `ClassVsTypeDemoJava`. Which Kotlin line has no Java twin at all?"
                ],
                "code": kdemo("ClassVsTypeDemo", "ClassVsTypeDemoJava"),
                "expect": "Kotlin prints `KClass: class java.lang.String (Kotlin reflection is not available)`, `Class:  class java.lang.String` and `KType:  java.util.List<java.lang.String>? (Kotlin reflection is not available)`, then `true`, `true`, `false, false` and `classifier is List::class: true, arguments: 1, nullable: true`. With `-Preflect` the first line becomes `class kotlin.String` and the third `kotlin.collections.List<kotlin.String>?`. Java prints the class, the field's type `java.util.List<java.lang.String>`, `true`, and the argument `class java.lang.String`. Java has no twin for the nullable type: its types carry no nullability."
            },
            "refs": [
                {"title": "Reflection: class references and KType (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html", "kind": "docs"}
            ]
        },
        {
            "h": "Asking a fruit what it is: x::class gives a KClass<out T>",
            "body": S2,
            "try": {
                "title": "Ask values for their class",
                "minutes": 4,
                "steps": [
                    "Run `ClassOfValueDemo` (or `ClassOfValueDemoJava`). The loop variable is declared `Fruit`. What does `simpleName` print for each piece?",
                    "Uncomment the three wrong moves one at a time. Predict each error first.",
                    "In the Java twin, uncomment the wrong move. Find the captured type in the message."
                ],
                "code": kdemo("ClassOfValueDemo", "ClassOfValueDemoJava"),
                "expect": "Both print `Gala: Apple, is an apple: true` and `Eureka: Lemon, is an apple: false`: the run-time class, not the declared type. Kotlin ends with `exact = Apple, noteClass = String`; Java ends with `exact = Apple, getClass() on null: NullPointerException`. Kotlin's errors: (1) `Initializer type mismatch: expected 'KClass<Fruit>', actual 'KClass<out Fruit>'.`, (2) `Expression in class literal has nullable type 'String?'. Use '!!' to make the type non-nullable.`, (3) `Type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.` Java's: `incompatible types: Class<CAP#1> cannot be converted to Class<Fruit>`, where `CAP#1` is the unknown subtype."
            },
            "refs": [
                {"title": "Object.getClass (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Object.html", "kind": "docs"}
            ]
        },
        {
            "h": "One note on two kinds of paper: converting, checking and casting",
            "body": S3,
            "try": {
                "title": "Check, cast and name a class",
                "minutes": 3,
                "steps": [
                    "Run `ClassApiDemo` and `ClassApiDemoJava`. Compare the two `cast failed:` messages.",
                    "Uncomment the wrong move in `ClassApiDemo.kt` and read the whole deprecation message.",
                    "Replace `Lemon::class.safeCast(fruit)` with `Lemon::class.cast(fruit)` in the second `println`. Predict what changes, then run."
                ],
                "code": kdemo("ClassApiDemo", "ClassApiDemoJava"),
                "expect": "Kotlin prints `k.java = Apple, c.kotlin == k: true, fruit.javaClass == c: true`, then `isInstance: true, cast(...).grams: 180, safeCast to Lemon: null`, `cast failed: Value cannot be cast to workbench.generics.l09.demo.Lemon`, the two names and `int` / `class java.lang.Integer`. Java's cast message is `Cannot cast workbench.generics.l09.demo.Apple to workbench.generics.l09.demo.Lemon`. The wrong move fails with `'val <T : Any> KClass<T>.javaClass: Class<KClass<T>>' is deprecated. Use 'java' property ...`. With `cast` instead of `safeCast`, the program stops with a `ClassCastException` on that line, before it reaches the `try` block."
            }
        },
        {
            "h": "The reference book in the other room: what needs kotlin-reflect",
            "body": S4,
            "try": {
                "title": "Run one demo with and without kotlin-reflect",
                "minutes": 4,
                "steps": [
                    "Run `ReflectDemo` with the command below. Every line under `-- needs kotlin-reflect` fails. Note which error each one gives.",
                    "Run it again with `-Preflect` at the end of the command. That flag adds kotlin-reflect to the demo's runtime classpath (see `labs/generics/build.gradle.kts`).",
                    "Run `ReflectDemoJava`. Which of the Kotlin answers can Java reflection give too?"
                ],
                "code": kdemo("ReflectDemo", "ReflectDemoJava"),
                "expect": "Without the jar, the first five lines work (`Fruit`, `true`, `true`, `1`, and `class java.lang.String (Kotlin reflection is not available)`). Then four lines show `KotlinReflectionNotSupportedError: Kotlin reflection implementation is not found at runtime`, and `createInstance()` shows `NoClassDefFoundError: kotlin/reflect/full/KClasses`. With `-Preflect`: `class kotlin.String`, `Storeroom`, `[Apple, Lemon]`, `true`, `[component1, component2, copy, equals, grams, hashCode, name, toString]` and `PaperBag()`. Java prints the fields `[grams, name]`, the methods (with getters such as `getGrams` and the hidden `copy$default`), and `Storeroom.INSTANCE: Storeroom`. It has no notion of a data class."
            }
        },
        {
            "h": "Filing the shelves under their whole labels: typeOf and super type tokens",
            "body": S5,
            "aside": ASIDE,
            "try": {
                "title": "Capture a full type two ways",
                "minutes": 4,
                "steps": [
                    "Run `TypeTokenDemo` and `TypeTokenDemoJava`. Compare the two `super type token:` lines.",
                    "Find the line in the Java output where the token failed to capture the real type.",
                    "Uncomment the wrong move in each file. Predict, then run."
                ],
                "code": kdemo("TypeTokenDemo", "TypeTokenDemoJava"),
                "expect": "Kotlin prints the `typeOf` result `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>> (Kotlin reflection is not available)`, `arguments:        2, ...`, the same type from `javaType` without the apology, `true`, `false`, and the Kotlin-written token `java.util.Map<java.lang.String, ? extends java.util.List<? extends java.lang.Integer>>`. Java prints its token as `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>`, its two arguments, and `inside a generic method: java.util.List<T>`: the hole. The wrong moves fail with `Only classes are allowed on the left-hand side of a class literal.` and `TypeRef is abstract; cannot be instantiated`."
            },
            "refs": [
                {"title": "typeOf (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html", "kind": "docs"},
                {"title": "KClass (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/-k-class/", "kind": "docs"}
            ]
        }
    ],
    "compare": {
        "title": "A type-safe card index in Java and Kotlin",
        "java": {
            "title": "CardIndex.java",
            "src": "import java.lang.reflect.Type;\nimport java.util.HashMap;\nimport java.util.Map;\nimport java.util.NoSuchElementException;\n\nfinal class CardIndex {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n    private final Map<Type, Object> byType = new HashMap<>();\n\n    // Class<T> and T tied together: the compiler checks the pair\n    <T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n    <T> T get(Class<T> type) {\n        Object impl = byClass.get(type);\n        if (impl == null) throw new NoSuchElementException(\"no card for \" + type.getSimpleName());\n        return type.cast(impl);                                // checked\n    }\n\n    // generic tools: a super type token supplies the full type\n    <T> void registerTyped(TypeRef<T> type, T impl) { byType.put(type.type, impl); }\n\n    @SuppressWarnings(\"unchecked\")                              // safe: only registerTyped puts values in\n    <T> T getTyped(TypeRef<T> type) { return (T) byType.get(type.type); }\n}\n\n// index.register(Scale.class, scale);\n// index.registerTyped(new TypeRef<Shelf<Apple>>() {}, apples);"
        },
        "kotlin": {
            "title": "CardIndex.kt",
            "src": "class CardIndex {\n    private val byClass = HashMap<KClass<*>, Any>()\n    private val byType = HashMap<KType, Any>()\n\n    // KClass<T> and T tied together: the compiler checks the pair\n    fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\n    fun <T : Any> get(type: KClass<T>): T {\n        val impl = byClass[type] ?: throw NoSuchElementException(\"no card for \" + type.simpleName)\n        return type.cast(impl)                                 // checked, no kotlin-reflect needed\n    }\n    inline fun <reified T : Any> get(): T = get(T::class)\n\n    // generic tools: typeOf supplies the full type\n    fun registerTyped(type: KType, impl: Any) { byType[type] = impl }\n    fun getTyped(type: KType): Any = byType[type] ?: throw NoSuchElementException(\"no card for $type\")\n    inline fun <reified T : Any> registerTyped(impl: T) = registerTyped(typeOf<T>(), impl)\n\n    @Suppress(\"UNCHECKED_CAST\")                                 // safe: only registerTyped<T> puts values in\n    inline fun <reified T : Any> getTyped(): T = getTyped(typeOf<T>()) as T\n}\n\n// index.register(Scale::class, scale); index.get<Scale>()\n// index.registerTyped<Shelf<Apple>>(apples)"
        },
        "note": "Both are what Joshua Bloch calls a typesafe heterogeneous container (Effective Java, Item 33): one map holds values of many types, and the key carries the type, so `get` can return a `T` with a checked `cast`. The KClass half is a direct translation: `KClass<T>` for `Class<T>`, `type.cast` in both. The differences show at the call site and for generic types. Kotlin adds reified wrappers, so callers write `get<Scale>()` and `registerTyped<Shelf<Apple>>(apples)`. For generic types Java needs a super type token object at each call (`new TypeRef<Shelf<Apple>>() {}`), while Kotlin's `typeOf<T>()` is computed from the reified `T`, with no subclass and no hole for type variables. In both, the full-type half needs one unchecked cast. It is safe because the map is private and filled only through the typed `registerTyped`."
    },
    "worked": {
        "title": "Build the card index's KClass half, then find where it stops",
        "steps": [
            {"say": "A first draft files cards by class and hands back `Any`. It compiles, but every caller has to cast, and nothing stops a card being filed under the wrong note.",
             "code": "class CardIndex {\n    private val byClass = HashMap<KClass<*>, Any>()\n    fun register(type: KClass<*>, impl: Any) { byClass[type] = impl }\n    fun get(type: KClass<*>): Any? = byClass[type]\n}\n\nindex.register(Scale::class, PlainLabels())              // compiles: a label printer filed as the scale\nval scale = index.get(Scale::class) as Scale             // ClassCastException here",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class CardIndex {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n    void register(Class<?> type, Object impl) { byClass.put(type, impl); }\n    Object get(Class<?> type) { return byClass.get(type); }\n}\n\nindex.register(Scale.class, new PlainLabels());           // compiles: a label printer filed as the scale\nScale scale = (Scale) index.get(Scale.class);             // ClassCastException here"},
            {"say": "1. Tie the note and the tool together with one type parameter. Now `Scale::class` is a `KClass<Scale>`, so `T` is `Scale`, and the tool must be one. 2. Hand back a `T` with a checked `cast`. Self-check before reading on: why is `type.cast` safe here when `as T` in lesson 8 was not? (The `KClass` is a real object at run time, so `cast` has something to check against.)",
             "code": "fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\nfun <T : Any> get(type: KClass<T>): T {\n    val impl = byClass[type] ?: throw NoSuchElementException(\"no card for \" + type.simpleName)\n    return type.cast(impl)\n}\n\nindex.register(Scale::class, PlainLabels())\n// error: Argument type mismatch: actual type is 'PlainLabels', but 'Scale' was expected.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "<T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n<T> T get(Class<T> type) {\n    Object impl = byClass.get(type);\n    if (impl == null) throw new NoSuchElementException(\"no card for \" + type.getSimpleName());\n    return type.cast(impl);\n}\n\nindex.register(Scale.class, new PlainLabels());\n// error: method register in class CardIndex cannot be applied to given types;\n//   reason: inference variable T has incompatible bounds"},
            {"say": "3. Add the reified wrapper for Kotlin callers. It touches only the public `get(type)`, as lesson 8 required of public inline functions.",
             "code": "inline fun <reified T : Any> get(): T = get(T::class)\n\nval scale: Scale = index.get()            // T from the expected type\nval labels = index.get<LabelPrinter>()",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "// Java keeps passing the class:\nScale scale = index.get(Scale.class);\nLabelPrinter labels = index.get(LabelPrinter.class);"},
            {"say": "4. Now file a generic tool. `Shelf::class` is a `KClass<Shelf<*>>`, so the best `get` can hand back is a `Shelf<*>`, and a second `register(Shelf::class, lemons)` replaces the apple shelf without a word. Asking for `Shelf<Apple>` fails at compile time. That's the point where the key has to become a `KType`, which is the second half of the lab.",
             "code": "index.register(Shelf::class, apples)\nindex.register(Shelf::class, lemons)            // replaces the apples: same class\nval any: Shelf<*> = index.get(Shelf::class)\nval p: Shelf<Apple> = index.get(Shelf::class)\n// error: Initializer type mismatch: expected 'Shelf<Apple>', actual 'Shelf<*>'.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "index.register(Shelf.class, apples);       // raw Class: Shelf.class has no <Apple>\nindex.register(Shelf.class, lemons);       // replaces the apples\nShelf<?> any = index.get(Shelf.class);"}
        ]
    },
    "lab": {
        "title": "A card index keyed by KClass, then by KType",
        "minutes": 14,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l09/CardIndex.kt",
            f"{LAB}/main/kotlin/workbench/generics/l09/Model.kt",
            f"{LAB}/main/kotlin/workbench/generics/l09/Callers.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l09.*'",
        "steps": [
            "Skim `Model.kt`, which holds the fruit, two tools (a `Scale` and a `LabelPrinter`) and a generic `Shelf<T>`. Then skim `Callers.kt`, the same trick as lesson 8: the tests reach your inline functions through it. Run the tests: all seven fail.",
            "Part 1. In `CardIndex.kt`, write `register` and `get(type)`. Throw `NoSuchElementException(\"no card for \" + type.simpleName)` when no card is filed, and hand the tool back with `type.cast(...)`.",
            "Make the no-argument `get()` inline with `reified T : Any`, passing `T::class` on. Five tests should now pass, including the one that shows a `KClass` key holding only one shelf.",
            "Part 2. Write `registerTyped(type: KType, impl)` and `getTyped(type: KType)` with the `byType` map. The missing-card message is `\"no card for \" + type`.",
            "Make the two one-argument versions inline and reified, using `typeOf<T>()`. In `getTyped<T>()`, cast with `as T` under `@Suppress(\"UNCHECKED_CAST\")`, and write one comment that says why the cast is safe.",
            "Run the tests until all seven pass."
        ],
        "hints": [
            "`val impl = byClass[type] ?: throw NoSuchElementException(\"no card for \" + type.simpleName)`, then `return type.cast(impl)`. `cast` needs `import kotlin.reflect.cast`.",
            "`typeOf` needs `import kotlin.reflect.typeOf`. It works without kotlin-reflect, and two calls to `typeOf<Shelf<Apple>>()` give equal keys.",
            "The reified functions must call only the public `get(type)`, `registerTyped(type, impl)` and `getTyped(type)`: a public inline function can't read the private maps."
        ],
        "done_when": "All seven tests in `CardIndexTest` pass."
    },
    "drill": {
        "title": "Write a KClass card index from memory",
        "minutes": 5,
        "prompt": "Close this page. Write a card index with `register(type, impl)`, `get(type)` and a reified `get<T>()` in Kotlin, using `KClass` keys and a checked cast. Then write the Java version with `Class<T>`. Finally, write the one line that gives you a key for `List<String>` in each language.",
        "answer": {
            "lang": "kotlin",
            "src": "class CardIndex {\n    private val byClass = HashMap<KClass<*>, Any>()\n\n    fun <T : Any> register(type: KClass<T>, impl: T) { byClass[type] = impl }\n\n    fun <T : Any> get(type: KClass<T>): T =\n        type.cast(byClass[type] ?: throw NoSuchElementException(\"no card for ${type.simpleName}\"))\n\n    inline fun <reified T : Any> get(): T = get(T::class)\n}\n\nval key: KType = typeOf<List<String>>()     // List<String>::class does not compile",
            "alt": {"lang": "java", "title": "CardIndex.java", "src": "final class CardIndex {\n    private final Map<Class<?>, Object> byClass = new HashMap<>();\n\n    <T> void register(Class<T> type, T impl) { byClass.put(type, impl); }\n\n    <T> T get(Class<T> type) {\n        Object impl = byClass.get(type);\n        if (impl == null) throw new NoSuchElementException(\"no card for \" + type.getSimpleName());\n        return type.cast(impl);\n    }\n}\n\n// a key for List<String>: a super type token\nType key = new TypeRef<List<String>>() {}.type;"}
        }
    },
    "recap": [
        "A `KClass` (or Java's `Class`) describes a class: no type arguments, never nullable. A `KType` describes a full type: the class, its arguments and its nullability. The one-word note and the whole label.",
        "`Apple::class` is an exact `KClass<Apple>`. `fruit::class` is a `KClass<out Fruit>`, because the real class is some subtype; Java's `getClass()` returns `Class<? extends Fruit>` for the same reason.",
        "Convert with `.java` and `.kotlin`; a value's `Class` is `x.javaClass`. `isInstance`, `cast` and `safeCast` are the checked `is`, `as` and `as?`.",
        "Names, identity, checks, casts and `typeOf` work without kotlin-reflect. `objectInstance`, `sealedSubclasses`, `isData`, `members` and `kotlin.reflect.full` need it.",
        "`typeOf<Shelf<Apple>>()` keeps type arguments, even through a reified `T`, and Java gets the same from a super type token. Key containers by `KClass` for plain types and by `KType` for generic ones.",
        "The limit: a `KType` exists only where the compiler wrote it, at a call site with a known type. An object at run time still knows only its class."
    ],
    "closing": CLOSING,
    "quiz": [
        {
            "q": "`val fruit: Fruit = pickFruit()`. Which line compiles?",
            "options": [
                "`val k: KClass<Fruit> = fruit::class`",
                "`val k: KClass<Apple> = fruit::class`",
                "`val k: KClass<out Fruit> = fruit::class`",
                "`val k: KClass<Fruit?> = fruit::class`"
            ],
            "answer": 2,
            "why": "A bound class reference gives the class of some subtype of the declared type: `KClass<out Fruit>`. The exact `KClass<Fruit>` is what the class literal `Fruit::class` gives. `KClass<Apple>` would need the compiler to know the run-time class, and `KClass<Fruit?>` breaks the `T : Any` bound."
        },
        {
            "q": "A Gradle project without kotlin-reflect runs four lines. Which one throws?",
            "options": [
                "`Apple::class.simpleName`",
                "`Apple::class.isInstance(fruit)`",
                "`typeOf<List<String>>().arguments`",
                "`Storeroom::class.objectInstance`"
            ],
            "answer": 3,
            "why": "`objectInstance` describes a declaration, so it needs kotlin-reflect and throws `KotlinReflectionNotSupportedError`. The standard library handles names, instance checks and `typeOf` on its own. Printing a `KClass` or `KType` also works, just with the `(Kotlin reflection is not available)` apology."
        },
        {
            "q": "A card index must hold a `Shelf<Apple>` and a `Shelf<Lemon>` at the same time. Which key type do you use?",
            "options": [
                "`KClass<*>`, from `Shelf::class`",
                "`KType`, from `typeOf<Shelf<Apple>>()`",
                "`Class<*>`, from `Shelf::class.java`",
                "The class's `simpleName`"
            ],
            "answer": 1,
            "why": "Both shelves have the same class, so every class-based key (a `KClass`, a `Class` or a name) collides, and the second card replaces the first. A `KType` includes the type argument, so the two keys differ. In Java, a super type token's `Type` plays the same role."
        },
        {
            "q": "Java: `static <T> Type listOf() { return new TypeRef<List<T>>() {}.type; }`, with the usual `TypeRef` super type token. What does `Tokens.<String>listOf()` return?",
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
            "q": "From \"Type erasure and reified type parameters\": `fun <T : Any> lookup(index: CardIndex): T = index.get<T>()`, where `get<T>()` is `inline` with a `reified T`. What happens?",
            "options": [
                "It compiles and returns the tool for whatever `T` the caller picks",
                "It compiles, but always returns the first tool filed",
                "It doesn't compile: `Cannot use 'T' as reified type parameter. Use a class instead.`",
                "It compiles and throws `ClassCastException` at run time"
            ],
            "answer": 2,
            "why": "`lookup`'s own `T` is an ordinary, erased type parameter, so there's no class to copy into the inlined `get`: its label is already gone. Make `lookup` itself `inline` with a `reified T`, or give it a `type: KClass<T>` parameter and call `index.get(type)`.",
            "from": "gen-08"
        }
    ],
    "flashcards": [
        {"front": "KClass or KType: which one knows that a value is a `List<String>?` and not just a `List`?", "back": "`KType` (from `typeOf<List<String>?>()`). A `KClass` describes only the class: no type arguments, never nullable."},
        {"front": "Why is `fruit::class` a `KClass<out Fruit>` when `fruit: Fruit`?", "back": "The real class is some unknown subtype of `Fruit`, and `out` means exactly that. Java's `getClass()` returns `Class<? extends Fruit>` for the same reason."},
        {"front": "Why is `KClass` declared `KClass<T : Any>`?", "back": "There is no class for a nullable type: `String?` is backed by the class `String`. So `KClass<String?>` and `nullableValue::class` don't compile."},
        {"front": "How do you convert between `KClass` and Java's `Class`?", "back": "`k.java` gives the `Class`; `c.kotlin` gives the `KClass`. A value's `Class` is `x.javaClass`."},
        {"front": "Without kotlin-reflect, what does `Storeroom::class.objectInstance` do?", "back": "It throws `KotlinReflectionNotSupportedError`. Anything that describes declarations needs kotlin-reflect; names, checks, casts and `typeOf` don't."},
        {"front": "How do you get a run-time object for the full type `Shelf<Apple>` in Kotlin?", "back": "`typeOf<Shelf<Apple>>()`, a `KType`. `Shelf<Apple>::class` doesn't compile: only classes are allowed on the left of `::class`."},
        {"front": "What is a super type token?", "back": "An anonymous subclass, `new TypeRef<List<String>>() {}`, whose generic superclass is read back with reflection. It's how Jackson's `TypeReference` works."}
    ],
    "terms": [
        {"term": "KClass", "plain": "Kotlin's run-time object for a class, such as `Apple::class`. No type arguments, never nullable."},
        {"term": "Class", "plain": "Java's run-time object for a class: `Apple.class`, or `Apple::class.java` from Kotlin."},
        {"term": "KType", "plain": "A full type at run time: class, type arguments and nullability. Made by `typeOf<T>()`."},
        {"term": "Class literal", "plain": "`Name::class`: the class you name in code. Its type is exact, `KClass<Name>`."},
        {"term": "Bound class reference", "plain": "`value::class`: the run-time class of a value, typed `KClass<out DeclaredType>`."},
        {"term": "kotlin-reflect", "plain": "The separate jar that answers questions about declarations: members, sealed subclasses, data classes."},
        {"term": "Super type token", "plain": "A Java trick that captures a full generic type through an anonymous subclass's declared superclass."},
        {"term": "Typesafe heterogeneous container", "plain": "One map holding values of many types, with the type as the key, so `get` can return a `T` safely."}
    ],
    "explain_back": {
        "prompt": "A teammate asks: \"Why do we need `typeOf` at all? `T::class` already tells us the type.\" Explain the difference between a `KClass` and a `KType` in your own words, using the `Shelf<Apple>` and `Shelf<Lemon>` example, and say what Java uses instead.",
        "answer": "A `KClass` describes a class, and every type built on that class shares it. `Shelf<Apple>` and `Shelf<Lemon>` are two different types, but both have the class `Shelf`, so `T::class` gives the same `KClass` for both, and a map keyed by it can hold only one of them: the second card replaces the first. Nullability is lost the same way, since `String` and `String?` share `String::class`. A `KType` describes the whole type: the class, its type arguments and whether it may be null. `typeOf<Shelf<Apple>>()` and `typeOf<Shelf<Lemon>>()` are different keys, so a card index keyed by `KType` can hold both. The JVM never stores this on objects, because of erasure; the compiler writes the `KType` down at the call site, which is why `typeOf` needs a known or reified type. Java has no `KType`. It uses a super type token: an anonymous subclass like `new TypeRef<Shelf<Apple>>() {}`, whose declared superclass keeps the type arguments and can be read back with reflection."
    },
    "deeper": {
        "minutes": 10,
        "body": "Why doesn't a `KType` need kotlin-reflect, when so much else does? Because the compiler builds most of `typeOf<T>()`. At each call site it emits code that constructs the type from parts it already knows: the classifier (`List::class`), the arguments, the variance of each argument and the nullability flag. The standard library holds a small implementation of `KType` for that. Answering `sealedSubclasses` is different: it means reading Kotlin's own metadata out of the class file, and the reader for that metadata is what kotlin-reflect contains.\n\n`KType` also records variance and stars. `typeOf<MutableList<out Number>>().arguments.single().variance` is `OUT`, and `typeOf<List<*>>().arguments` prints `[*]`. So a card index keyed by `KType` treats `MutableList<out Number>` and `MutableList<Number>` as different keys. That's correct, but it can surprise you: the key must be written with exactly the same type on both sides.\n\nThe docs page on reflection mentions that the `kotlinc` command-line compiler adds kotlin-reflect by default (you can opt out with `-no-reflect`). That's why a snippet that prints `class kotlin.String` in a quick command-line experiment prints `class java.lang.String (Kotlin reflection is not available)` inside your Gradle project. If you add kotlin-reflect to a program, add it on purpose: it's a 3.8 MB jar, and its first use loads and parses metadata, which costs a little time once per class.\n\nLast, the `javaClass` rule from the third section has a reason. `javaClass` is an extension property on every type, and a `KClass` is a value like any other, so `k.javaClass` would mean the class that implements the `KClass` object, not the class it describes. The standard library declares a deprecated overload for exactly that receiver, and in 2.4.21 using it is an error. `x.javaClass` on ordinary values is unaffected."
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
