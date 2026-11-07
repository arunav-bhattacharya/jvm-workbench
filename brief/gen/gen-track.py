import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track generics stop being a set of slogans you half remember. You can read any signature in your codebase, Kotlin or Java, and say what it accepts and why: `List<out E>`, `Comparator<in T>`, `MutableList<*>`, `<T extends Comparable<? super T>>`. You can decide, for each type parameter you write, whether it is `out`, `in` or invariant, by checking where it appears instead of guessing. You know what the JVM erases, what `inline` and `reified` bring back, when a `KClass` is enough and when you need a `KType` or a super type token, and you can build type-safe registries, event buses and result types that need no casts at the call site.

You need to know the syntax of both languages, nothing more. The track starts from zero with type parameters, and every variance lesson repeats one picture: a producer hands values out, a consumer takes them in. Each lesson shows the compiler error for every wrong move, so you learn what the guard looks like when it fires. Install JDK 25; the labs compile with release 21 and use Kotlin 2.4.21, and the compiler messages quoted in the lessons are copied from that version.

The labs live in `labs/generics`, one package per lesson (`workbench.generics.l01` to `l11`). Most are Kotlin; lessons 3, 6 and 7 add a small Java exercise where the point is Java's arrays, wildcards or raw types, and lesson 8 has a Java test that calls your Kotlin code with a class token. Some tests check variance by reading the Java signature Kotlin generates, because `out` becomes `? extends` there. From lesson 8 on, tests reach your `inline` functions through a `Callers.kt` file that you don't edit (lesson 8 explains why). Lesson 9's demos run with and without kotlin-reflect: add `-Preflect` to the demo command. Run `./gradlew :generics:test --tests 'workbench.generics.lNN.*'` from `labs/` until it passes, `./gradlew :generics:solutionTest` to see the reference answers pass the same tests, and `./gradlew :generics:demo -Pmain=<class>` for the Try-it programs."""

CHEAT = """## Type parameters and bounds

| Idea | Kotlin | Java |
|---|---|---|
| Generic function | `fun <T> first(xs: List<T>): T` | `static <T> T first(List<T> xs)` |
| Explicit type argument | `emptyList<String>()` | `Collections.<String>emptyList()` |
| Upper bound | `<T : Comparable<T>>` | `<T extends Comparable<T>>` |
| Two bounds | `where T : CharSequence, T : Comparable<T>` | `<T extends CharSequence & Comparable<T>>` |
| Default bound | `Any?`, so `T` may be null | `Object` |
| No nulls | `<T : Any>`, or `T & Any` for one use | annotations only |
| Self type | `abstract class B<S : B<S>>` with `abstract fun self(): S` | `abstract class B<S extends B<S>>` |

## Variance

| Kotlin | Java | Read? | Write? | Example |
|---|---|---|---|---|
| `C<T>` | `C<T>` | yes, as `T` | yes, a `T` | `MutableList<Payment>`, `Array<T>` |
| `C<out T>` | `C<? extends T>` | yes, as `T` | no | `List<out E>`, `MutableList<out Number>` |
| `C<in T>` | `C<? super T>` | only as `Any?` | yes, a `T` | `Comparable<in T>`, `MutableList<in Int>` |
| `C<*>` | `C<?>` | as `Any?` (or the bound) | no (Java: only `null`) | `List<*>`, `Map<*, *>`, `KClass<*>` |
| none | raw `C` | as `Object` | anything, unchecked | legacy `List` (avoid) |

- Producer `out`, consumer `in` (PECS: Producer Extends, Consumer Super).
- Substitution test: if I secretly hand you a `C<CardAuthorized>` where you expected a `C<PaymentEvent>`, can any call you make go wrong? No writes: `out` is safe. Only writes: flip it, `in`.
- `out` and `in` limit which types flow, not whether state changes: `clear()` works on `MutableList<out T>` and `MutableList<*>`.
- Function types are `Function1<in P, out R>`: a `(PaymentEvent) -> Unit` is a `(CardAuthorized) -> Unit`.
- `java.util.Comparator` and other Java interfaces are invariant in Kotlin: write `Comparator<in T>`.

## Where T may appear

| Position | Sign | `out T` | `in T` |
|---|---|---|---|
| return type, `val` | + | yes | no |
| parameter | − | no | yes |
| `var`, `MutableList<T>` anywhere | 0 | no | no |
| parameter of a parameter, `f: (T) -> Unit` | − × − = + | yes | no |
| parameter of the result, `(): (T) -> Unit` | + × − = − | no | yes |

`private` members and plain constructor parameters are exempt; `protected` and `internal` are checked. `@UnsafeVariance` switches the check off for one use: only for parameters that are compared, never stored (`List.contains`).

## Declaration-site or use-site

Every member only produces `T` (or only consumes it): declare `out T` (or `in T`) on the class, once. The class both reads and writes `T`: keep it invariant and project in each function that uses one side, `MutableList<out T>` or `MutableList<in T>`. Projecting an already-variant type gives a warning (`List<out T>`, redundant) or an error (`List<in T>`, conflicting). Variance on a function's own type parameter is an error. A type that does both but has readers that only read: split out a `ReadX<out T>` interface.

## Erasure and reified

- At run time a `List<String>` is a `List`. So `is List<String>`, `is T` and `T()` don't compile; check `is List<*>`, then check each element.
- `as List<String>` checks only the class and fails later, at a read (heap pollution).
- `inline fun <reified T>` copies the body into each call site with the real class: `is T`, `as? T`, `T::class`, `filterIsInstance<T>()`.
- Reified covers the outer class only (`filterIsInstance<List<String>>()` keeps every list), can't take `Nothing` or an erased `T`, and is invisible to Java (synthetic). Give Java a `type: Class<T>` overload.
- Kotlin 2.4: `x::class` on a nullable reified `T` is an error; use `<reified T : Any>`.
- Inline functions copied into callers can use only public API; stored lambda parameters need `noinline`.

## KClass, Class, KType

| You need | Kotlin | Java |
|---|---|---|
| a class you name | `CardAuthorized::class` (`KClass<CardAuthorized>`) | `CardAuthorized.class` |
| a value's class | `event::class` (`KClass<out PaymentEvent>`), `event.javaClass` | `event.getClass()` (`Class<? extends PaymentEvent>`) |
| convert | `k.java`, `c.kotlin` | n/a |
| checked is / as / as? | `k.isInstance(x)`, `k.cast(x)`, `k.safeCast(x)` | `c.isInstance(x)`, `c.cast(x)` |
| a full type | `typeOf<List<String>>()` (`KType`) | super type token: `new TypeRef<List<String>>() {}` |
| a `java.lang.reflect.Type` | `typeOf<T>().javaType` (opt-in in 2.4.21) | the token's `type` |

Free without kotlin-reflect: names, `==`, `isInstance`, `cast`, `safeCast`, `typeOf` (prints a "(Kotlin reflection is not available)" suffix). Needs kotlin-reflect: `objectInstance`, `sealedSubclasses`, `isData`, `members`, `kotlin.reflect.full`. Key registries by `KClass` for plain types and by `KType` for generic ones such as `Repository<Payment>`.

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
| `Kotlin reflection implementation is not found at runtime` | add kotlin-reflect, or use `.java` reflection |"""

RECAP = [
    "A type parameter is a blank the caller fills in. It moves a `ClassCastException` from a far-away read to a compile error at the write.",
    "A class is not a type: `String` backs `String` and `String?`, `List` backs `List<String>` and `List<Int>`. Generic types are invariant unless declared otherwise.",
    "Producer `out`, consumer `in`: `out T` lets `C<Sub>` stand in for `C<Super>`, `in T` flips the arrow, and both shut one side. Java writes `? extends` and `? super` at every use.",
    "Variance limits which types flow, not whether state changes. Check positions with the sign rule when the intuition stops helping.",
    "Declare variance on the class when you can; project (`MutableList<out T>`, `MutableList<in T>`) when the class both reads and writes; split out a read-only `out` view when readers need flexibility.",
    "`*` means one unknown type argument: read as `Any?`, write nothing. It is not `Any?`, and it is not a raw type.",
    "The JVM erases type arguments. `inline` + `reified` brings the outer class back at each call site, Java can't call it, and nested arguments stay erased.",
    "`KClass` and `Class` describe classes; `KType` (from `typeOf`) describes full types. `x::class` is a `KClass<out T>`. Declaration details need kotlin-reflect.",
    "Recursive bounds give base classes a self type; `T & Any` removes null; `@UnsafeVariance` is a promise that a parameter is only compared; `Nothing` sits below every type.",
    "Type-safe containers tie the key to the value type (`KClass<T>`, `Key<T>` with a `KType`), keep the one unchecked cast private, and keep write keys invariant."
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
        "why": "Two bounds need a `where` clause, and the caller's type must satisfy both. `Comparable<T>` alone gives `<` but no `length`; `CharSequence` alone gives `length` but no `<`. Java writes the same thing as `<T extends CharSequence & Comparable<T>>`.",
        "from": "gen-02"
    },
    {
        "q": "`val ids: MutableList<String> = mutableListOf(\"pay_1\")`. Which line compiles?",
        "options": [
            "`val a: MutableList<Any> = ids`",
            "`val b: List<Any> = ids`",
            "`val c: MutableList<Any?> = ids`",
            "`val d: Array<Any> = ids.toTypedArray()`"
        ],
        "answer": 1,
        "why": "Only the read-only `List` is declared `out E`, so only it is covariant. `MutableList` and `Array` are invariant in Kotlin because they can be written to; if they weren't, you could add an `Int` to a list of strings, which is exactly what Java arrays allow until an `ArrayStoreException`.",
        "from": "gen-03"
    },
    {
        "q": "Pick the variance for each: `interface Feed<T> { fun next(): T }`, `interface Audit<T> { fun record(event: T) }`, `class Slot<T>(var item: T)`.",
        "options": [
            "`out`, `in`, invariant",
            "`in`, `out`, `out`",
            "`out`, `out`, `out`",
            "invariant, `in`, `out`"
        ],
        "answer": 0,
        "why": "`Feed` only returns `T`: a producer, `out`. `Audit` only takes `T`: a consumer, `in`. `Slot` has a `var`, which is read and written, so `T` sits in an invariant position and the class can be neither.",
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
        "q": "Your Kotlin library exposes `inline fun <reified T : Any> decode(json: String): T`. A Java service in the same monorepo needs it. What do you add?",
        "options": [
            "`@JvmStatic` on the reified function",
            "Nothing: Java can call it with `Decoder.<Payment>decode(json)`",
            "A version that takes `T` as a raw `Class` and returns `Object`",
            "`fun <T : Any> decode(json: String, type: Class<T>): T`, and make the reified one delegate to it"
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
        "why": "A `KClass` can only describe a class, and `List<String>` and `List<Int>` share one. `typeOf` builds a `KType` at the call site that includes arguments and nullability, and it works without kotlin-reflect. That difference is why a registry for `Repository<Payment>` and `Repository<Refund>` needs `KType` keys.",
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
        "why": "`this as B` is an unchecked cast; erasure makes it succeed inside the base class, and the failure shows up where a caller uses the result. Each subclass implementing `self() = this` lets the compiler check that `this` really is a `B`.",
        "from": "gen-10"
    },
    {
        "q": "Pick the types: (1) a function that only reads payments from a mutable buffer and may clear it; (2) a bus that stores handlers for `CardAuthorized` and accepts handlers for any `PaymentEvent`; (3) a key for a per-request `List<String>` attribute.",
        "options": [
            "(1) `MutableList<out Payment>`; (2) `(CardAuthorized) -> Unit` handlers stored behind a `safeCast` adapter, keyed by `KClass<out PaymentEvent>`; (3) an invariant `Key<List<String>>` that carries `typeOf<List<String>>()`",
            "(1) `MutableList<Payment>`; (2) handlers cast to `(PaymentEvent) -> Unit`; (3) `Key<out List<String>>`",
            "(1) `MutableList<in Payment>`; (2) a `Map<String, Any>` of handlers; (3) the class `List::class` as the key",
            "(1) `MutableList<*>`; (2) `Consumer<CardAuthorized>` in a raw list; (3) the string \"currencies\""
        ],
        "answer": 0,
        "why": "Reading while still allowing `clear()` is an out-projection. Handlers consume, so a general handler fits, but storing a specific one needs an adapter rather than a cast. A key decides what may be written, so it must be invariant, and a `KType` keeps `List<String>` apart from other types with the same name. The other options each repeat a mistake from this track: `in` for reading, unchecked handler casts, an `out` write key, class keys for generic types, raw types and string keys.",
        "from": "gen-11"
    }
]

T = {"id": "gen", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/gen.json"
out.write_text(json.dumps(T, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
