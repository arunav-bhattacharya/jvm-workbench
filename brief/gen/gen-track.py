import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """Picture a small fruit shop. Boxes come in at the back, pass a clerk at the storeroom door who checks every label, and end up on the shelves and in the glass display case at the front. This track stays in that shop from the first lesson to the last. A type parameter is a box labeled "Box of ___", with a blank each caller fills in. The compiler is the clerk who checks every label at the door and then, when the program runs, tears it off. Each idea gets its own corner of the shop: a box signed "fruit only", a crate of apples that is not a crate of fruit, an apple dispenser with a lever and no slot, a compost bin that makes a fine apple bin, a box whose label wore off and, at the end, a board of bells by the back door.

By the end, generics stop being slogans you half remember. You can read any signature, Kotlin or Java, and say what it accepts and why: `List<out E>`, `Comparator<in T>`, `MutableList<*>`, `<T extends Comparable<? super T>>`. For each type parameter you write, you can decide whether it is `out`, `in` or invariant by checking where it appears, instead of guessing. You know what the JVM erases, what `inline` and `reified` bring back, and when a `KClass` is enough or you need a `KType`, and you can build containers, result types and event buses that need no casts where they're used. You need the syntax of both languages and nothing more: the track starts from zero, and every lesson shows the compiler's error for each wrong move, so you learn what the clerk says when it refuses. Install JDK 25. The labs compile with release 21 and use Kotlin 2.4.21, and the compiler messages in the lessons come from that version.

The labs live in `labs/generics`, one package per lesson (`workbench.generics.l01` to `l11`). Most are Kotlin; lessons 3, 6 and 7 add a small Java exercise about arrays, wildcards or raw types, and lesson 8 has a Java test that calls your Kotlin code with a class token. Some tests check your variance by reading the Java signature Kotlin generates, because `out` becomes `? extends` there. From lesson 8 on, tests reach your `inline` functions through a `Callers.kt` file that you don't edit (lesson 8 explains why). Lesson 9's demos run with and without kotlin-reflect: add `-Preflect` to the demo command. From `labs/`, run `./gradlew :generics:test --tests 'workbench.generics.lNN.*'` until it passes, `./gradlew :generics:solutionTest` to see the reference answers pass the same tests, and `./gradlew :generics:demo -Pmain=<class>` for the Try-it programs."""

CHEAT = """## Type parameters and bounds

| Idea | Kotlin | Java | Picture it |
|---|---|---|---|
| Generic function | `fun <T> first(xs: List<T>): T` | `static <T> T first(List<T> xs)` | a box labeled "Box of ___" |
| Explicit type argument | `emptyList<String>()` | `Collections.<String>emptyList()` | you fill in the blank yourself |
| Upper bound | `<T : Comparable<T>>` | `<T extends Comparable<T>>` | a box signed "fruit only" |
| Two bounds | `where T : CharSequence, T : Comparable<T>` | `<T extends CharSequence & Comparable<T>>` | two signs on one box |
| Default bound | `Any?`, so `T` may be null | `Object` | the blank may say "or nothing" |
| No nulls | `<T : Any>`, or `T & Any` for one use | annotations only | this box always holds a real fruit |
| Self type | `abstract class B<S : B<S>>` with `abstract fun self(): S` | `abstract class B<S extends B<S>>` | a form that writes its own name in the blank |

## Variance

| Kotlin | Java | Read? | Write? | Example | Picture it |
|---|---|---|---|---|---|
| `C<T>` | `C<T>` | yes, as `T` | yes, a `T` | `MutableList<Apple>`, `Array<T>` | the crate of apples, which is not a crate of fruit |
| `C<out T>` | `C<? extends T>` | yes, as `T` | no | `List<out E>`, `MutableList<out Number>` | the apple dispenser: a lever, no slot |
| `C<in T>` | `C<? super T>` | only as `Any?` | yes, a `T` | `Comparable<in T>`, `MutableList<in Int>` | the compost bin, a fine apple bin |
| `C<*>` | `C<?>` | as `Any?` (or the bound) | no (Java: only `null`) | `List<*>`, `Map<*, *>`, `KClass<*>` | the box whose label wore off |
| none | raw `C` | as `Object` | anything, unchecked | legacy `List` (avoid) | a box with no clerk at all |

- Producer `out`, consumer `in` (PECS: Producer Extends, Consumer Super).
- Substitution test: if I secretly hand you a `C<Apple>` where you expected a `C<Fruit>`, can any call you make go wrong? No writes: `out` is safe. Only writes: flip it, `in`.
- `out` and `in` limit which types flow, not whether state changes: `clear()` works on `MutableList<out T>` and `MutableList<*>`. The read-only `List` is the glass display case: nothing goes in through it, but the shopkeeper can still change what's inside.
- Function types are `Function1<in P, out R>`: a `(Fruit) -> Unit` is an `(Apple) -> Unit`, so the stock-keeper who counts every fruit can answer the apple bell.
- `java.util.Comparator` and other Java interfaces are invariant in Kotlin: write `Comparator<in T>`.

## Where T may appear

| Position | Sign | `out T` | `in T` |
|---|---|---|---|
| return type, `val` | + | yes | no |
| parameter | − | no | yes |
| `var`, `MutableList<T>` anywhere | 0 | no | no |
| parameter of a parameter, `f: (T) -> Unit` | − × − = + | yes | no |
| parameter of the result, `(): (T) -> Unit` | + × − = − | no | yes |

`private` members and plain constructor parameters are exempt; `protected` and `internal` are checked. `@UnsafeVariance` switches the check off for one use. Put it only on parameters that are compared, never stored (`List.contains`): a display case you may point into, never one with a secret slot.

## Declaration-site or use-site

Every member only produces `T` (or only consumes it): declare `out T` (or `in T`) on the class, once. The class both reads and writes `T`: keep it invariant and project in each function that uses one side, `MutableList<out T>` or `MutableList<in T>`. Picture it as the helper told at the door, "for this job, treat the crate as take-only". Projecting a type that is already variant gives a warning (`List<out T>`, redundant) or an error (`List<in T>`, conflicting). Variance on a function's own type parameter is an error. A type that does both but has readers that only read: split out a `DisplayCase<out T>` style read view.

## Erasure and reified

Picture it: the clerk checks each label at the door, then tears it off. A second clerk copies it onto a note first, and the note has room for one word.

- At run time a `List<String>` is a `List`. So `is List<String>`, `is T` and `T()` don't compile; check `is List<*>`, then check each element.
- `as List<String>` checks only the class and fails later, at a read (heap pollution).
- `inline fun <reified T>` copies the body into each call site with the real class: `is T`, `as? T`, `T::class`, `filterIsInstance<T>()`.
- Reified covers the outer class only (`filterIsInstance<List<String>>()` keeps every list), can't take `Nothing` or an erased `T`, and is invisible to Java (synthetic). Give Java a `type: Class<T>` overload.
- Kotlin 2.4: `x::class` on a nullable reified `T` is an error; use `<reified T : Any>`.
- Inline functions copied into callers can use only public API; stored lambda parameters need `noinline`.

## KClass, Class, KType

Picture it: a `KClass` is the one-word note ("Shelf"), Java's `Class` is the same note on Java's paper, a `KType` is the whole label ("Shelf of apples"), and a super type token is that label carved into a shelf's frame, where erasure can't reach.

| You need | Kotlin | Java |
|---|---|---|
| a class you name | `Apple::class` (`KClass<Apple>`) | `Apple.class` |
| a value's class | `fruit::class` (`KClass<out Fruit>`), `fruit.javaClass` | `fruit.getClass()` (`Class<? extends Fruit>`) |
| convert | `k.java`, `c.kotlin` | n/a |
| checked is / as / as? | `k.isInstance(x)`, `k.cast(x)`, `k.safeCast(x)` | `c.isInstance(x)`, `c.cast(x)` |
| a full type | `typeOf<List<String>>()` (`KType`) | super type token: `new TypeRef<List<String>>() {}` |
| a `java.lang.reflect.Type` | `typeOf<T>().javaType` (opt-in in 2.4.21) | the token's `type` |

Free without kotlin-reflect: names, `==`, `isInstance`, `cast`, `safeCast`, `typeOf` (printed with a "(Kotlin reflection is not available)" suffix). Needs kotlin-reflect: `objectInstance`, `sealedSubclasses`, `isData`, `members`, `kotlin.reflect.full`. Key a container by `KClass` for plain types and by `KType` for generic ones such as `Shelf<Apple>`.

## Four designs from the workshop

| Design | The generics in it | Picture it |
|---|---|---|
| `Either<out L, out R>`, `Left : Either<L, Nothing>` | two `out`s and `Nothing`: one `Left` fits every success type | a problem slip that fits any order |
| `DisplayCase<out T>` read view on an invariant `Storeroom<T, ID>` | split reading from writing | readers look through the glass |
| `BellBoard` keyed by `KClass<out Fruit>` | narrow listeners stored behind a `safeCast` adapter; reified `listen` with `noinline` | one bell per kind of delivery, a doorman at each |
| `Key<T>(name, type: KType)` | invariant, because a key decides what may be written | a card tab that names its slot and what goes in it |

## Messages you'll meet (Kotlin 2.4.21)

| Message | Meaning |
|---|---|
| `Type parameter 'T' is declared as 'out' but occurs in 'in' position` | an `out` type takes a `T` somewhere |
| `Receiver type 'MutableList<out Number>' contains out projection which prohibits the use of 'fun add(...)'` | you projected for reading, then wrote |
| `Initializer type mismatch: expected 'String', actual 'CapturedType(in String)'` | reading a typed value through an in-projection |
| `Null cannot be a value of a non-null type 'CapturedType(*)'` | writing `null` through a star |
| `Cannot check for instance of erased type 'List<String>'` | erasure; use `is List<*>` |
| `Cannot use 'T' as reified type parameter. Use a class instead.` | the caller's `T` is erased; make it reified or pass a class |
| `Only classes are allowed on the left-hand side of a class literal` | `List<String>::class`; use `typeOf` |
| `Kotlin reflection implementation is not found at runtime` | add kotlin-reflect, or use `.java` reflection |
| `Argument type mismatch: actual type is '(E ...) -> Unit', but '(Fruit) -> Unit' was expected` | a narrow listener where a general one is needed; wrap it in an adapter |"""

RECAP = [
    "A type parameter is a blank on the box's label that the caller fills in. It moves a `ClassCastException` from a far-away read to a compile error at the write.",
    "A class is not a type: `String` backs `String` and `String?`, `List` backs `List<String>` and `List<Int>`. Generic types are invariant unless declared otherwise, so a crate of apples is not a crate of fruit.",
    "Producer `out`, consumer `in`: `out T` lets `C<Apple>` stand in for `C<Fruit>` (the dispenser), `in T` flips the arrow (the compost bin), and each shuts one side. Java writes `? extends` and `? super` at every use.",
    "Variance limits which types flow, not whether state changes. When intuition stops helping, check the positions with the sign rule.",
    "Declare variance on the class when you can; project (`MutableList<out T>`, `MutableList<in T>`) when the class both reads and writes; split out a read-only `out` view when readers need flexibility.",
    "`*` means one unknown type argument, the box whose label wore off: read as `Any?`, write nothing. It is not `Any?`, and it is not a raw type.",
    "The JVM erases type arguments after checking them. `inline` + `reified` brings the outer class back at each call site, a note one word long; Java can't call it, and nested arguments stay erased.",
    "`KClass` and `Class` describe classes; `KType` (from `typeOf`) describes full types. `x::class` is a `KClass<out T>`. Describing declarations needs kotlin-reflect.",
    "Recursive bounds give base classes a self type; `T & Any` removes null; `@UnsafeVariance` promises that a parameter is only compared; `Nothing` sits below every type and fits every label.",
    "Type-safe containers tie the key to the value type (`KClass<T>`, or `Key<T>` with a `KType`), keep the one unchecked cast private, and keep write keys invariant. The limit: they check types, not meaning."
]

QUIZ = [
    {
        "q": "`fun <T> firstOrDefault(items: List<T>, default: T): T`. What does `val x = firstOrDefault(listOf(1, 2), \"none\")` do?",
        "options": [
            "It doesn't compile: `T` can't be both `Int` and `String`",
            "It compiles with `T = Any?` and prints a warning",
            "It compiles: `T` is inferred as a common supertype of `Int` and `String`, so `x` is `1`, typed `Comparable<*> & Serializable`",
            "It compiles and throws `ClassCastException` when `x` is used"
        ],
        "answer": 2,
        "why": "Inference looks for a type that both arguments fit, and `Int` and `String` share `Comparable<*>` and `Serializable`. That's legal, and usually not what you meant: `val y: Int = firstOrDefault(listOf(1, 2), \"none\")` fails with `expected 'Int', actual 'Comparable<*> & Serializable'`. An explicit type argument, `firstOrDefault<Int>(...)`, turns the mistake into an error at the call.",
        "from": "gen-01"
    },
    {
        "q": "A helper must compare two values with `<` and also read `.length`. Which Kotlin signature allows both?",
        "options": [
            "`fun <T : Comparable<T>> longer(a: T, b: T): T`",
            "`fun <T> longer(a: T, b: T): T where T : CharSequence, T : Comparable<T>`",
            "`fun <T : CharSequence> longer(a: T, b: T): T`",
            "`fun <T : Any> longer(a: T, b: T): T`"
        ],
        "answer": 1,
        "why": "Two bounds need a `where` clause, and the caller's type must satisfy both: two signs on one box. `Comparable<T>` alone gives `<` but no `length`; `CharSequence` alone gives `length` but no `<`. Java writes the same thing as `<T extends CharSequence & Comparable<T>>`.",
        "from": "gen-02"
    },
    {
        "q": "`val varieties: MutableList<String> = mutableListOf(\"Gala\")`. Which line compiles?",
        "options": [
            "`val a: MutableList<Any> = varieties`",
            "`val b: List<Any> = varieties`",
            "`val c: MutableList<Any?> = varieties`",
            "`val d: Array<Any> = varieties.toTypedArray()`"
        ],
        "answer": 1,
        "why": "Only the read-only `List` is declared `out E`, so only it is covariant: the display case. `MutableList` and `Array` are invariant in Kotlin because they can be written to. If they weren't, you could add an `Int` to a list of strings, which is exactly what Java arrays allow until an `ArrayStoreException`.",
        "from": "gen-03"
    },
    {
        "q": "Pick the variance for each: `interface Feed<T> { fun next(): T }`, `interface Bin<T> { fun drop(item: T) }`, `class Slot<T>(var item: T)`.",
        "options": [
            "`out`, `in`, invariant",
            "`in`, `out`, `out`",
            "`out`, `out`, `out`",
            "invariant, `in`, `out`"
        ],
        "answer": 0,
        "why": "`Feed` only returns `T`: a producer, `out`. `Bin` only takes `T`: a consumer, `in`, like the compost bin. `Slot` has a `var`, which is read and written, so `T` sits in an invariant position and the class can be neither.",
        "from": "gen-05"
    },
    {
        "q": "What Java signature does Kotlin generate for `fun <T> copyInto(from: MutableList<out T>, to: MutableList<in T>)`?",
        "options": [
            "`<T> void copyInto(List<T> from, List<T> to)`",
            "`<T> void copyInto(List<?> from, List<?> to)`",
            "`<T> void copyInto(List<? extends T> from, List<? super T> to)`",
            "`<T> void copyInto(List from, List to)` (raw types)"
        ],
        "answer": 2,
        "why": "Use-site projections are Kotlin's spelling of Java wildcards: `out T` is `? extends T` and `in T` is `? super T`, the same shape as `Collections.copy`. The lab for that lesson checks exactly this signature through Java reflection.",
        "from": "gen-06"
    },
    {
        "q": "Which function accepts a `MutableList<String>` and may call `clear()` on it?",
        "options": [
            "`fun reset(l: MutableList<Any?>)`",
            "`fun reset(l: MutableList<Any>)`",
            "`fun reset(l: List<*>)`",
            "`fun reset(l: MutableList<*>)`"
        ],
        "answer": 3,
        "why": "A star projection accepts a mutable list of any element type and still allows members that take no element, such as `clear()`. `MutableList<Any?>` and `MutableList<Any>` accept only lists of exactly that element type. `List<*>` accepts the list but has no `clear()`.",
        "from": "gen-07"
    },
    {
        "q": "Your Kotlin library offers `inline fun <reified T : Any> decode(text: String): T`. Java code in the same project needs it. What do you add?",
        "options": [
            "`@JvmStatic` on the reified function",
            "Nothing: Java can call it as `Decoder.<Apple>decode(text)`",
            "A version that takes `T` as a raw `Class` and returns `Object`",
            "`fun <T : Any> decode(text: String, type: Class<T>): T`, and make the reified one call it"
        ],
        "answer": 3,
        "why": "javac can't inline Kotlin code, so the reified function is a synthetic method it ignores. A Class-token overload works for both languages and can do a checked `type.cast`. Keeping the reified version as a one-line wrapper gives Kotlin callers the short form.",
        "from": "gen-08"
    },
    {
        "q": "Inside `inline fun <reified T> describe()`, called as `describe<List<String>>()`, what do `T::class` and `typeOf<T>()` keep?",
        "options": [
            "`T::class` is the class `List`; `typeOf<T>()` is the full `List<String>`",
            "Both keep `List<String>`",
            "Both give only `List`",
            "`T::class` doesn't compile for a generic `T`"
        ],
        "answer": 0,
        "why": "A `KClass` can only describe a class, the one-word note, and `List<String>` and `List<Int>` share one. `typeOf` builds a `KType` at the call site that includes arguments and nullability, and it works without kotlin-reflect. That difference is why a card index holding a `Shelf<Apple>` and a `Shelf<Lemon>` needs `KType` keys.",
        "from": "gen-09"
    },
    {
        "q": "In `abstract class Builder<B : Builder<B>>`, why write `protected abstract fun self(): B` instead of `return this as B` in each setter?",
        "options": [
            "Because `this as B` doesn't compile",
            "Because abstract functions are faster",
            "Because `self()` is checked: a subclass that passes the wrong type argument fails to compile, while `this as B` compiles and throws `ClassCastException` at a later call",
            "Because Java can't call a function that returns `B`"
        ],
        "answer": 2,
        "why": "`this as B` is an unchecked cast; erasure makes it succeed inside the base class, and the failure shows up where a caller uses the result. When each subclass implements `self() = this`, the compiler checks that `this` really is a `B`.",
        "from": "gen-10"
    },
    {
        "q": "Pick the types: (1) a function that only reads fruit from a mutable list and may clear it; (2) a board that stores listeners for `Apple` and accepts listeners for any `Fruit`; (3) a key for an order's `List<String>` of varieties.",
        "options": [
            "(1) `MutableList<out Fruit>`; (2) `(Apple) -> Unit` listeners stored behind a `safeCast` adapter, keyed by `KClass<out Fruit>`; (3) an invariant `Key<List<String>>` that carries `typeOf<List<String>>()`",
            "(1) `MutableList<Fruit>`; (2) listeners cast to `(Fruit) -> Unit`; (3) `Key<out List<String>>`",
            "(1) `MutableList<in Fruit>`; (2) a `Map<String, Any>` of listeners; (3) the class `List::class` as the key",
            "(1) `MutableList<*>`; (2) `Consumer<Apple>` in a raw list; (3) the string \"varieties\""
        ],
        "answer": 0,
        "why": "Reading while still allowing `clear()` is an out-projection. Listeners consume, so a general listener fits, but storing a narrow one needs an adapter rather than a cast. A key decides what may be written, so it must be invariant, and a `KType` keeps `List<String>` apart from other types with the same name. The other options each repeat a mistake from this track: `in` for reading, unchecked listener casts, an `out` write key, class keys for generic types, raw types and string keys.",
        "from": "gen-11"
    }
]

T = {"id": "gen", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/gen.json"
out.write_text(json.dumps(T, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
