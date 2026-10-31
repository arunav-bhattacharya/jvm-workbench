# Kotlin Generics in Depth, Compared with Java Generics (Kotlin 2.4.x / JDK 25, October 2026)

> **How these notes were verified.** Facts come from two kinds of evidence:
> 1. **Official docs** fetched in this session (see "Verified URLs"). The kotlinlang.org pages were current: the generics page footer is dated 29 September 2026, and the `typeOf` API page links source at tag 2.4.20.
> 2. **Compiler and runtime probes** that I ran myself. I downloaded the official **kotlinc 2.4.21** release (the newest 2.4.x on Maven Central on 2026-10-30; 2.5.0-Beta2 also exists). It ran on **OpenJDK 21.0.12** because no JDK 25 was installed. Java-side facts were checked with **javac 21.0.12**. Every diagnostic quoted below as a probe result is copied verbatim from compiler output. The K2 CLI prints messages starting with a lowercase letter; the IDE may capitalize them.
>    - `P-kotlinc` = kotlinc 2.4.21 output, from [kotlin-compiler-2.4.21.zip](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip). It also covers runtime output from `java -cp kotlin-stdlib.jar[:kotlin-reflect.jar]`, using the jars in that zip.
>    - `P-javac` = local javac/java 21.0.12. This was a local run, so there is no URL. Outputs are quoted verbatim.
>    - The probe sources are in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/probe/` (session scratchpad, may not persist). The important snippets are reproduced inline below.
> 3. **Not reachable from this session:** docs.oracle.com (Java Tutorial and JLS SE 25) and gafter.blogspot.com (DNS blocked by network policy). Java facts that depend on them are backed only by javac probes or are listed under Gaps.

---

## Core facts by lesson topic (reference for all 11 lessons)

### Takeaway
Kotlin keeps Java's erased, invariant-by-default JVM generics and adds three things on top. **Declaration-site variance** (`out`/`in`) lets a class state its variance once. **Use-site projections** are Kotlin's version of Java wildcards. **Reified type parameters** on inline functions recover some runtime type information. Nullability is part of every generic type, the default bound is `Any?`, and `T & Any` is the definitely non-nullable form.

### Cited Findings

**Type parameters and inference**
- Generic functions declare type parameters before the name, `fun <T> singletonList(item: T): List<T>`. The type argument can be explicit (`singletonList<Int>(1)`) or inferred (`singletonList(1)`) — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- The underscore operator infers one type argument while you give the others explicitly, e.g. `Runner.run<SomeImplementation, _>()`, where `T` is inferred from `SomeImplementation : SomeClass<String>` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Mixed arguments are inferred to a non-denotable intersection type. `val l = listOf(1, "a"); val bad: List<Int> = l` fails with `initializer type mismatch: expected 'List<Int>', actual 'List<Comparable<*> & Serializable>'.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- When an inferred intersection type reaches a **reified** parameter, 2.4 reports an error. `fill(arrayOf(1), "b")` with `fill(dest: Array<in String>, …)` gives: `type argument for reified type parameter 'T' was inferred to the intersection of ['Comparable<*>' & 'Serializable']. Reification of an intersection type results in the common supertype being used. This may lead to subtle issues and an explicit type argument is encouraged.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- Builder inference works with no annotation. `buildList { add("a"); add("b") }` is `List<String>` and `buildMap { put("a", 1) }` is `Map<String, Int>`. In 2.4.21, using `@BuilderInference` gives the warning: `'annotation class BuilderInference : Annotation' is deprecated. BuilderInference annotation must not be used anymore. Builder inference is enabled automatically for builder calls if needed.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- The 2.4.0 compatibility guide adds these inference and generics errors (version-specific):
  - KTLC-373 "Prohibit inconsistent type arguments in generic calls" (2.3.0 warning → 2.4.0 error)
  - KTLC-372 "Report type mismatches from supertypes with nested generic arguments" (2.4.0 error; "Previously, the compiler could miss this mismatch, which later failed with a `ClassCastException`")
  - KTLC-363 "Prohibit inferred types with inaccessible declarations" (2.3.0 warning → 2.4.0 error)
  - KTLC-284 "Prohibit flexible explicit nullable type arguments for Java types" (2.2.0 warning → 2.4.0 error)
  - KTLC-388 misplaced type arguments in callable reference qualifiers (2.4.0 warning; write `Outer<Int>.Inner<String>::toString`)
  - Source: [Kotlin 2.4 compatibility guide](https://kotlinlang.org/docs/compatibility-guide-24.html)

**Upper bounds, where clauses, multiple bounds**
- "The default upper bound (if there was none specified) is `Any?`. Only one upper bound can be specified inside the angle brackets. If the same type parameter needs more than one upper bound, you need a separate where-clause". Also, "The passed type must satisfy all conditions of the `where` clause simultaneously." The docs' example is `fun <T> copyWhenGreater(list: List<T>, threshold: T): List<String> where T : CharSequence, T : Comparable<T>` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- `sort(listOf(HashMap<Int, String>()))` with `fun <T : Comparable<T>> sort(list: List<T>)` is an error: "HashMap<Int, String> is not a subtype of Comparable<HashMap<Int, String>>" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Probe diagnostics ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `where T : Number, T : Exception` → `only one of the upper bounds can be a class.`
  - `fun <T, U> f(u: U) where U : T, U : Comparable<U>` → `type parameter cannot have any other bounds if it's bounded by another type parameter.`
  - `maxOf2(1, "a")` with `<T : Comparable<T>>` → `argument type mismatch: actual type is 'String', but 'Int' was expected.`
  - `both(42)` with `where T : CharSequence, T : Comparable<T>` → `cannot infer type for type parameter 'T'. Specify it explicitly.` plus `argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.`
  - `both(StringBuilder("x"))` **compiles**, because the JDK's `StringBuilder` is `Comparable<StringBuilder>`. This was checked on JDK 21.
  - `class Repo<T : Any, ID : Comparable<ID>>; val r: Repo<String?, Int>?` → `type argument is not within its bounds: type parameter 'T (of class Repo<T : Any, ID : Comparable<ID>>)' must be subtype of 'Any', but actual: 'String?'.`
- Java view of bounds (from `javap -p`): Kotlin `fun <T : Comparable<T>> maxOf(a: T, b: T): T` becomes `<T extends java.lang.Comparable<? super T>> T maxOf(T, T)`. Kotlin `where T : CharSequence, T : Comparable<T>` becomes `<T extends java.lang.CharSequence & java.lang.Comparable<? super T>>`. The `? super T` appears because Kotlin's `Comparable` is declared `in T` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

**`T : Any`, nullability of type parameters, definitely non-nullable types**
- With the default `Any?` bound, `fun <T> anyNullable(x: T)` accepts `null`. `fun <T> lengthOf(x: T) = x.length` fails with `unresolved reference 'length'.` Calling `fun <T : Any> nonNull(x: T)` with `nonNull(null)` gives `cannot infer type for type parameter 'T'. Specify it explicitly.` and `null cannot be a value of a non-null type 'uninferred T (of fun <T : Any> nonNull)'.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- An extension `fun <T> T.describe()` can be called as `null.describe()` (compiles) — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- "To declare a generic type `T` as definitely non-nullable, declare the type with `& Any`… A definitely non-nullable type must have a nullable upper bound." The main use case is overriding Java methods annotated `@NotNull`, e.g. `override fun load(x: T1 & Any): T1 & Any`. Also: "When working only with Kotlin, it's unlikely that you will need to declare definitely non-nullable types explicitly because Kotlin's type inference takes care of this for you." The page gives no version number — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- `fun <T : Any> dnn(x: T & Any)` is an error: `intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.` `fun <T> elvis(x: T, y: T & Any): T & Any = x ?: y` compiles. In Java, `fun <T> dnn(x: T & Any): T & Any` is just `<T> T dnn(T)`, so the DNN part is not in the Java signature — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

**Subtyping vs subclassing; invariance; Java arrays**
- `MutableList<String>` is not a subtype of `MutableList<Any>`: `initializer type mismatch: expected 'MutableList<Any>', actual 'MutableList<String>'.` `val la: List<Any> = ms` compiles, because `List` is `out E` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- One class can back many types. At runtime `MutableList::class == List::class` is `true`, and `MutableList::class.java` is `interface java.util.List` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip). "`List<String>` and `List<Int>` share the same `List::class` representation, and `String` and `String?` share `String::class`" — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)
- Java invariance: `List<Object> o = s;` (with `s` a `List<String>`) → `error: incompatible types: List<String> cannot be converted to List<Object>` — P-javac (local javac 21.0.12)
- Java array covariance: `Object[] objs = new String[1]; objs[0] = Integer.valueOf(1);` compiles and throws `ArrayStoreException: java.lang.Integer` at run time — P-javac (local java 21.0.12)
- Kotlin arrays are invariant. `val anys: Array<Any> = ints` (with `ints: Array<Int>`) → `initializer type mismatch: expected 'Array<Any>', actual 'Array<Int>'.` But `val outAnys: Array<out Any> = ints` compiles, and then `outAnys[0] = "x"` → `receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- On the JVM, "array types (`Array<Foo>`) retain information about the erased type of their elements, and type casts to an array type are partially checked". For example, `foo as Array<List<String>?>` succeeds for any array of `List<*>` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)

**Declaration-site variance (`out`, `in`)**
- `interface Source<out T> { fun nextT(): T }` allows `val objects: Source<Any> = strs`. Rule: "when a type parameter `T` of a class `C` is declared `out`, it may occur only in the out-position in the members of `C`, but in return `C<Base>` can safely be a supertype of `C<Derived>`." `in` makes a parameter contravariant; it "can only be consumed and never produced". Example: `interface Comparable<in T>` allows `val y: Comparable<Double> = x` where `x: Comparable<Number>`. Mnemonic: "Consumer in, Producer out!" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- "The only thing guaranteed by wildcards (or other types of variance) is type safety. Immutability is a completely different story." — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Stdlib declared variances, read with kotlin-reflect `KClass.typeParameters.map { it.variance }` ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `List` [OUT]
  - `Comparable` [IN]
  - `Function1` [IN, OUT]
  - `Map` [INVARIANT, OUT]
  - `Array` [INVARIANT]
  - `Pair` [OUT, OUT]
  - `Result` [OUT]
  - **Gotcha:** `MutableList::class.typeParameters` also reports [OUT], and `MutableMap` reports [INVARIANT, OUT]. That is because on the JVM they are the same `KClass` as `List`/`Map`, not because `MutableList` is covariant.

**PECS and how it maps to `out`/`in`**
- The Kotlin docs cite *Effective Java, 3rd Edition*, Item 31 "Use bounded wildcards to increase API flexibility": "For maximum flexibility, use wildcard types on input parameters that represent producers or consumers". The mnemonic is PECS: Producer-Extends, Consumer-Super. Java's `addAll` is `void addAll(Collection<? extends E> items)` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Recursive bounds in practice. In Kotlin, `fun <T : Comparable<T>> List<T>.biggest(): T` works on `listOf(Dog(1), Dog(5))` where `Dog : Animal` and `Animal : Comparable<Animal>`: it compiles and returns a `Dog`, with `T` inferred as `Animal` through `List<out E>` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip). In Java, `static <T extends Comparable<T>> T strict(List<T> l)` called with a `List<Dog>` fails with `reason: inference variable T has incompatible equality constraints Animal,Dog`. The PECS form `static <T extends Comparable<? super T>> T pecs(List<? extends T> l)` compiles — P-javac (local javac 21.0.12)

**Use-site variance and type projections**
- `fun copy(from: Array<out Any>, to: Array<Any>)`: "This is type projection… You can only call methods that return the type parameter `T`… it corresponds to Java's `Array<? extends Object>`." Also: "`Array<in String>` corresponds to Java's `Array<? super String>`." (The docs write `Array<? …>` loosely. The real Java signature is an array type; see the interop section.) — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Probe diagnostics ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `mo.add("x")` on `MutableList<out Any>` → `receiver type 'MutableList<out Any>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.`
  - Reading from `MutableList<in String>` into a `String` → `initializer type mismatch: expected 'String', actual 'CapturedType(in String)'.` Reading into `Any?` compiles.
  - Passing an `Array<Int>` to `fill(dest: Array<in String>)` → `argument type mismatch: actual type is 'Array<Int>', but 'Array<in String>' was expected.`
  - `fun rp(l: List<out String>)` → warning `projection is redundant: the corresponding type parameter of 'List<out String>' has the same variance.`
  - `fun cp(l: List<in String>)` → error `projection conflicts with variance of the corresponding type parameter of 'List<in String>'. Remove the projection or replace it with '*'.`
  - `fun <out T> fo(t: T)` → `variance annotations are only allowed for type parameters of classes and interfaces.`
- Internally the compiler uses *captured types*. For `Array<out CharSequence>`, `get()` sees the upper bound and `set()` sees `Nothing` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)

**Star projections**
- Rules:
  - For `Foo<out T : TUpper>`, `Foo<*>` = `Foo<out TUpper>`.
  - For `Foo<in T>`, `Foo<*>` = `Foo<in Nothing>`: "there is nothing you can write to `Foo<*>` in a safe way".
  - For invariant `Foo<T : TUpper>`, `Foo<*>` = `Foo<out TUpper>` for reading and `Foo<in Nothing>` for writing.
  - With several parameters, each is projected separately: for `Function<in T, out U>`, `Function<*, String>` = `Function<in Nothing, String>`, `Function<Int, *>` = `Function<Int, out Any?>`, `Function<*, *>` = `Function<in Nothing, out Any?>`.
  - "Star-projections are very much like Java's raw types, but safe."
  - Source: [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Probe results for `MutableList<*>` ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `star.add("x")` → `receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.`
  - `star.add(null)` → `null cannot be a value of a non-null type 'CapturedType(*)'.`
  - `val e: Any? = star[0]`, `star.clear()` and `star.removeAt(0)` all **compile**.
  - `Comparable<*>.compareTo(1)` → `receiver type 'Comparable<*>' contains star projection which prohibits the use of 'fun compareTo(other: T): Int'.`
  - `val m: MutableList<Any?> = mutableListOf<String>()` → `initializer type mismatch: expected 'MutableList<Any?>', actual 'MutableList<String>'.` But `val m2: MutableList<*> = mutableListOf<String>()` and `val anyQ: List<Any?> = listOf("a")` compile.
- Java wildcard behavior: `List<?> w = s; w.add("x")` → `error: incompatible types: String cannot be converted to CAP#1`, while `w.add(null)` compiles. Raw types compile with warnings (`[rawtypes] found raw type: List`, `[unchecked] unchecked call to add(E) as a member of the raw type List`, `[unchecked] unchecked conversion`). The heap pollution then shows up later as a `ClassCastException` at the read site — P-javac (local javac/java 21.0.12)

**Type erasure: what is checked, what survives**
- "At runtime, the instances of generic types do not hold any information about their actual type arguments." `Foo<Bar>` and `Foo<Baz?>` erase to `Foo<*>`. `is List<*>` is allowed. When the type arguments are statically known, only the class part is checked: `if (list is ArrayList)` smart-casts a `MutableList<String>` to `ArrayList<String>` — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Probe diagnostics ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `x is T` → `cannot check for instance of erased type 'T (of fun <T> isT)'.`
  - `x is List<String>` (with `x: Any`) → `cannot check for instance of erased type 'List<String>'.`
  - With `c: Collection<String>`, `c is List<String>` **compiles** but `c is List<Int>` → `cannot check for instance of erased type 'List<Int>'.`
  - Unchecked cast warnings: `unchecked cast of 'Any' to 'List<String>'.` and `unchecked cast of 'Map<String, *>' to 'Map<String, Int>'.` (The docs page shows an older wording: "Unchecked cast: `Map<String, *>` to `Map<String, Int>`".)
  - At run time, `(listOf(1, 2) as Any as List<String>).size` returns 2 with no failure. `val s: String = l[0]` then throws `java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String`.
- Same-erasure overloads: `fun List<String>.dup()` plus `fun List<Int>.dup()` → `platform declaration clash: The following declarations have the same JVM signature (dup(Ljava/util/List;)I):` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip). The docs' fix is `@JvmName("filterValidInt")` — [Kotlin docs: Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- Other erasure-driven restrictions ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `T()` → `type parameter 'T' is not an expression.`
  - `arrayOf<T>()` → `cannot use 'T' as reified type parameter. Use a class instead.`
  - `class GenEx<T> : Exception()` → `subclass of 'Throwable' cannot have type parameters.`
  - `List<String>::class` → `only classes are allowed on the left-hand side of a class literal.`
- Java equivalents (P-javac, local javac 21.0.12):
  - `new T()` → `unexpected type`
  - `new T[1]` and `new List<String>[10]` → `generic array creation`
  - `obj instanceof List<String>` with `obj: Object` → `Object cannot be safely cast to List<String>`
  - `s instanceof ArrayList<String>` with `s: List<String>` **compiles**
  - `new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass()` is `true`
- **What survives erasure** is generic signature metadata on *declarations*. `javap -v` shows a `Signature:` attribute per method, e.g. `(Linterop/Box<+Linterop/Base;>;)Linterop/Base;` for `unboxBase`. Java reflection reads it: `Field.getGenericType()` returned `java.util.List<java.lang.String>`, and `Method.toGenericString()` returned `public static final interop.Base interop.Interop.unboxBase(interop.Box<? extends interop.Base>)`. Super type tokens rely on the same data (see below) — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip) + P-javac
- Kotlin-only type facts are absent from Java signatures: DNN, and declaration-site variance at the class level (Java's `Box<T>` is plain). Yet kotlin-reflect still reports `List` as OUT, so it reads them from Kotlin's own metadata. See Inferences.

**Reified type parameters**
- Without reified, the pattern is `fun <T> TreeNode.findParentOfType(clazz: Class<T>): T?` with `@Suppress("UNCHECKED_CAST")`. With it, `inline fun <reified T> TreeNode.findParentOfType(): T?` can use `p !is T` and `p as T?`. Reflection still works: `inline fun <reified T> membersOf() = T::class.members`. Restrictions: "Normal functions (not marked as inline) cannot have reified parameters." and "A type that does not have a run-time representation (for example, a non-reified type parameter or a fictitious type like `Nothing`) cannot be used as an argument for a reified type parameter." — [Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- `inline fun <reified A, reified B> Pair<*, *>.asPairOf()` with `somePair.asPairOf<String, List<String>>()` "Compiles but breaks type safety!" because the nested type argument is still erased. `arg is T` erases the type arguments of `arg`'s own generic type — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Probe diagnostics ([P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)):
  - `fun <reified T> notInline(...)` → `only type parameters of inline functions can be reified.`
  - Calling `isA<T>(x)` from a non-reified generic → `cannot use 'T' as reified type parameter. Use a class instead.`
  - `kcls<Nothing>()` → `cannot use 'Nothing' as reified type parameter.`
  - `listOf(1, "a", 2.0, "b").filterIsInstance<String>()` = `[a, b]`.
- **New 2.4 error (KTLC-370):** `::class` on an expression whose type is a reified type parameter with a nullable upper bound (2.3.0 warning → 2.4.0 error) — [Kotlin 2.4 compatibility guide](https://kotlinlang.org/docs/compatibility-guide-24.html). The probe `inline fun <reified T> klassOf(x: T) = x::class` gives `expression in class literal has nullable type 'T (of fun <T> klassOf)'. Use '!!' to make the type non-nullable.`; the fix is `<reified T : Any>` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- **Java cannot call reified functions.** The bytecode method is `public static final <T> boolean reifiedFn(java.lang.Object)` with flags `ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC`. A Java call fails with `error: cannot find symbol` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip) + P-javac

**`@UnsafeVariance` and why `List.contains` needs it**
- The declaration is `@Target(allowedTargets = [AnnotationTarget.TYPE]) annotation class UnsafeVariance`, described as "Suppresses errors about variance conflict", since 1.0 — [UnsafeVariance API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/)
- The 2.4.21 stdlib sources (`commonMain/kotlin/Collections.kt`) contain:
  - `public operator fun contains(element: @UnsafeVariance E): Boolean` (line 83)
  - `public fun containsAll(elements: Collection<@UnsafeVariance E>): Boolean` (line 93)
  - `public fun indexOf(element: @UnsafeVariance E): Int` (line 248)
  - `AbstractCollection.contains(element: @UnsafeVariance E): Boolean = any { it == element }`
  - Source: [kotlin-stdlib-sources.jar in the 2.4.21 zip](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- The annotation really can break safety. This compiles without complaint: `class Hidden<out T>(t: T) { private val list = mutableListOf(t); fun add(t: @UnsafeVariance T) { list.add(t) } }` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

**Variance of function types**
- `Function1` is [IN, OUT] (reflection). `val g: (String) -> Any = f` where `f: (Any) -> String` compiles. The reverse fails: `initializer type mismatch: expected '(Any) -> String', actual '(String) -> Any'.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- The Java view of a parameter `f: (Number) -> Base` is `kotlin.jvm.functions.Function1<? super java.lang.Number, ? extends interop.Base>` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

**Generic type aliases**
- `typealias Predicate<T> = (T) -> Boolean` and `typealias Table<K> = MutableMap<K, MutableList<K>>` compile in 2.4.21. A nested `class Outer { typealias Names = List<String> }` compiles with **no flag** — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- Nested type aliases were Beta in 2.2.0 (`-Xnested-type-aliases`). They "don't capture type parameters from the outer class" ("not being able to mention type parameters") — [What's new in Kotlin 2.2.0](https://kotlinlang.org/docs/whatsnew22.html). They graduated to Stable in 2.3.0 — [What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html)

**Variance with nested generics** (all [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip))
- `val ll2: List<List<Any>> = ll` with `ll: List<List<String>>`: compiles, because covariance composes.
- `val ml2: MutableList<List<Any>> = ml` with `ml: MutableList<List<String>>` → `initializer type mismatch: expected 'MutableList<List<Any>>', actual 'MutableList<List<String>>'.`
- `val ml3: MutableList<out List<Any>> = ml`: compiles.
- `Map<String, MutableList<Int>>` → `Map<String, MutableList<Number>>`: error, because the inner `MutableList` is invariant.
- `mapOf<String, List<Int>>()` assigned to `Map<Any, List<Number>>`: error, because `Map`'s K is invariant.
- Java view: a `List<List<Number>>` parameter becomes `java.util.List<? extends java.util.List<? extends java.lang.Number>>`.

**Recursive generics / self types**
- A self-typed builder compiles and chains correctly in 2.4.21:
  ```kotlin
  abstract class Builder<T : Builder<T>> {
      fun name(n: String): T { …; return self() }
      protected abstract fun self(): T
  }
  class PizzaBuilder : Builder<PizzaBuilder>()
  ```
  `PizzaBuilder().name("x").cheese()` type-checks — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

**Kotlin 2.x timeline relevant to generics**
- 2.0.0 (May 21, 2024): "the new Kotlin K2 compiler is used by default and it is Stable for all target platforms". Smart casts improved. For `||` type checks, "a smart cast is made to their closest common supertype. Before this change, a smart cast was always made to the `Any` type." The page lists no generics-specific inference changes — [What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)
- 2.2.0 (June 23, 2025): nested type aliases (Beta), context parameters (Preview), context-sensitive resolution (Preview), Java 24 bytecode — [What's new in Kotlin 2.2.0](https://kotlinlang.org/docs/whatsnew22.html)
- 2.3.0 (December 16, 2025): nested type aliases Stable; "Starting with Kotlin 2.3.0, the compiler can generate classes containing Java 25 bytecode." — [What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html)
- 2.4.0 (July 14, 2026): context parameters Stable (except context arguments and callable references), explicit backing fields Stable, collection literals Experimental (`-Xcollection-literals`), Java 26 bytecode. On Kotlin/JS, "`in` and `out` are kept in generated `.d.ts` files". The page lists no other generics or type-inference changes — [What's new in Kotlin 2.4.0](https://kotlinlang.org/docs/whatsnew24.html)
- Latest 2.4.x patch on Maven Central (2026-10-30) is 2.4.21. 2.4.20 was released, and 2.5.0-Beta1/Beta2 exist — [Maven Central metadata](https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-compiler-embeddable/maven-metadata.xml)

### Inferences
- Kotlin-only facts (declaration-site variance, nullability, DNN) live in Kotlin's own class metadata, not in the Java `Signature` attribute. Evidence: Java sees `Box<T>`, `<T> T dnn(T)`, and `List<String>` for a `List<out String>` parameter, yet kotlin-reflect reports `List` as OUT. The whatsnew24 page's "Annotations in metadata enabled by default" item confirms that a Kotlin metadata channel exists.
- Kotlin's `List<T>` with `T : Comparable<T>` "just works" for `List<Dog>` where Java's needs `Comparable<? super T>` and `? extends T`. That makes a strong motivating example: declaration-site variance does the PECS work for you.
- The JVM-level rules (erasure, array covariance, wildcard semantics) did not change between JDK 21 (probed) and JDK 25. I found no generics change in JDK 22–25, but I could not fetch the JLS SE 25 to confirm (see Gaps).

### Gaps
- No JDK 25 was available locally. javac diagnostics are from 21.0.12, and their wording could differ slightly in 25.
- The JLS SE 25 (§4.5, §4.10, §10.5) and the Java Tutorial wildcard pages could not be fetched (docs.oracle.com blocked). The section numbers are from the assignment and are unverified here.
- DNN types (`T & Any`) became stable in Kotlin 1.7.0. This comes from training knowledge only; the fetched generics page gives no version.
- I did not verify when `@BuilderInference` was first deprecated. I observed the deprecation in 2.4.21 but found no doc entry for it in the 2.4 compatibility guide or what's new pages.
- The K2 migration guide (for detailed K2 inference changes) was not fetched.

---

## Key Question 1: What are the precise rules for where `out`/`in` type parameters may appear, with exact compiler error messages and special cases (constructor params, private members)?

### Takeaway
Treat every type position as having a sign. Return types and `val` types are **out (+)**. Parameter types and bounds of member type parameters are **in (−)**. `var` types and arguments of invariant generics are **invariant**. Each `in` layer flips the sign: a function type's parameter, or a type argument of an `in`-declared class. Private members and plain constructor parameters are exempt. Private members become *private-to-this* instead. In 2.4.21 the error format is: `type parameter 'T' is declared as 'out' but occurs in 'in' position in type '…'.`

### Cited Findings
All probe lines below are verbatim kotlinc 2.4.21 output — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip). The probe file:
```kotlin
interface Producer<out T> {
    fun produce(): T                  // OK
    fun consume(t: T)                 // ✗ 3:20
    var v: T                          // ✗ 4:12
}
interface Consumer<in T> {
    fun consume(t: T)                 // OK
    fun produce(): T                  // ✗ 8:20
    val v: T                          // ✗ 9:12
}
class OkOut<out T>(val item: T, private var hidden: T, plain: T) {   // all three ctor params OK
    private fun set(t: T) { hidden = t }               // OK (private)
    fun takesCallback(f: (T) -> Unit) { f(item) }      // OK (double flip)
    fun takesSupplier(f: () -> T) {}                   // ✗ 14:32
    fun list(): List<T> = listOf(item)                 // OK
    fun mlist(): MutableList<T> = mutableListOf(item)  // ✗ 16:30
    fun cmp(c: Comparable<T>) {}                       // OK (param × in = out)
    protected fun prot(t: T) {}                        // ✗ 18:27
    internal fun intern(t: T) {}                       // ✗ 19:28
    fun returnsConsumer(): (T) -> Unit = {}            // ✗ 20:29
    fun <R : T> generic(): R? = null                   // ✗ 21:14 (bound is an in-position)
}
class CtorVar<out T>(var t: T)                         // ✗ 23:29
interface MyList<out E> { fun contains(element: @UnsafeVariance E): Boolean }  // OK
class Box<out T>(private val items: MutableList<T>) { fun first(): T = items[0] } // OK
```
- `Producer.consume(t: T)` → `type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of interface Producer<out T>)'.`
- `var v: T` in an `out` interface → `type parameter 'T' is declared as 'out' but occurs in 'invariant' position in type 'T (of interface Producer<out T>)'.`
- `Consumer.produce(): T` and `val v: T` in an `in` interface → `type parameter 'T' is declared as 'in' but occurs in 'out' position in type 'T (of interface Consumer<in T>)'.` (A `val` in an `in` class is an out-position; the error is reported once per occurrence.)
- `fun takesSupplier(f: () -> T)` → `… occurs in 'in' position in type '() -> T (of class OkOut<out T>)'.`
- `fun mlist(): MutableList<T>` → `… occurs in 'invariant' position in type 'MutableList<T (of class OkOut<out T>)>'.`
- `fun returnsConsumer(): (T) -> Unit` → `… occurs in 'in' position in type '(T (of class OkOut<out T>)) -> Unit'.`
- `fun <R : T> generic()` → `… occurs in 'in' position in type 'T (of class OkOut<out T>)'.` A member function's type-parameter bound is an in-position.
- **`protected` and `internal` members are checked** (18:27 and 19:28 both error). Only `private` is exempt.
- **Constructor parameters:** a plain parameter (`plain: T`) and a `val` property (`val item: T`) are fine in an `out` class. A `var` property is invariant: `class CtorVar<out T>(var t: T)` → `type parameter 'T' is declared as 'out' but occurs in 'invariant' position in type 'T (of class CtorVar<out T>)'.` The exception is `private var`, which is fine.
- **Private members are exempt from the variance check but become "private to this".** Accessing them through another instance fails:
  ```kotlin
  class C<out T>(private var t: T) {
      fun setSelf(x: @UnsafeVariance T) { this.t = x }        // OK
      fun copyFrom(o: C<@UnsafeVariance T>) { t = o.t }       // ✗
      fun pushTo(o: C<@UnsafeVariance T>) { o.t = t }         // ✗
  }
  ```
  → `cannot access 'var t: T': it is private/*private to this*/ in 'C'.` The same happens for `private val items: MutableList<T>` read as `o.items`: `cannot access 'val items: MutableList<T>': it is private/*private to this*/ in 'D'.`
- **Inferred public types count.** In `class E<in T> { private fun produce(): T? = null; fun use() = produce() }`, the private `produce` is fine. The public `use()` has inferred return type `T?` and fails: `type parameter 'T' is declared as 'in' but occurs in 'out' position in type 'T? (of class E<in T>)'.`
- The docs explain positions informally (produced/returned vs consumed) and do not formally define "out-position" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- `@UnsafeVariance` "Suppresses errors about variance conflict" and targets `TYPE` only — [UnsafeVariance API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/)
- `variance annotations are only allowed for type parameters of classes and interfaces.` (for `fun <out T> fo(t: T)`) — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

### Inferences
- The sign rule (out = +, in = −, invariant = 0, multiply through nesting) predicts every probe result above. Learners can apply it mechanically:
  - `(T) -> Unit` as a parameter: − × − = + → OK in an `out` class.
  - `(T) -> Unit` as a return type: + × − = − → error.
  - `Comparable<T>` as a parameter: − × − = + → OK.
  - `MutableList<T>` anywhere → 0 → error.
- Private-to-this explains *why* the exemption is safe. The compiler can only see uses through `this`, whose real type argument is fixed. Another instance `o: C<T>` might be a `C<Derived>` viewed as `C<Base>`.
- Inferred return types are a common silent trap. Give public members of variant classes explicit types.

### Gaps
- I did not check the Kotlin language specification text for the formal position definitions (the spec was not fetched). The rules above are derived from compiler behavior.
- I did not determine the internal diagnostic IDs (e.g. a `TYPE_VARIANCE_CONFLICT`-style factory name) and do not claim them.

---

## Key Question 2: How does each Kotlin concept map to Java exactly?

### Takeaway
Use-site `out T` ⇔ `? extends T`, use-site `in T` ⇔ `? super T`, and `*` ⇔ `?`. Declaration-site variance becomes a Java wildcard **only in parameter positions**, never in return types, and never when the type argument is final (e.g. `String`). `MutableList<…>` is invariant, so it gets no wildcard. Arrays become plain Java arrays (no wildcards), and `List<Nothing>` becomes a raw `List`. `@JvmWildcard` forces a wildcard and `@JvmSuppressWildcards` removes one.

### Cited Findings
- Docs rule: "the compiler generates `Box<Super>` as `Box<? extends Super>` for covariantly defined `Box` (or `Foo<? super Bar>` for contravariantly defined `Foo`) when it appears as a parameter. When it's a return value, wildcards are not generated, because otherwise Java clients will have to deal with them (and it's against the common Java coding style)." Also: "When the argument type is final, there's usually no point in generating the wildcard, so `Box<String>` is always `Box<String>`, no matter what position it takes." — [Kotlin docs: Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- `@JvmWildcard` example: `fun boxDerived(value: Derived): Box<@JvmWildcard Derived>` → `Box<? extends Derived> boxDerived(Derived value)`. `@JvmSuppressWildcards` example: `fun unboxBase(box: Box<@JvmSuppressWildcards Base>): Base` → `Base unboxBase(Box<Base> box)`. "`@JvmSuppressWildcards` can be used not only on individual type arguments, but on entire declarations, such as functions or classes" — [Kotlin docs: Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- `Nothing` as a type argument: "Kotlin generates a raw type where an argument of type `Nothing` is used". `fun emptyList(): List<Nothing>` → `List emptyList()` — [Kotlin docs: Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- Full mapping table from `javap -p` on kotlinc 2.4.21 output — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip):

| Kotlin declaration | Java signature seen by javac |
|---|---|
| `fun boxDerived(value: Derived): Box<Derived>` (Box is `out T`) | `Box<Derived> boxDerived(Derived)` (return: no wildcard) |
| `fun unboxBase(box: Box<Base>): Base` | `Base unboxBase(Box<? extends Base>)` |
| `fun boxString(b: Box<String>): Box<String>` | `Box<String> boxString(Box<String>)` (final arg) |
| `Box<@JvmWildcard Derived>` (return) | `Box<? extends Derived>` |
| `Box<@JvmSuppressWildcards Base>` (param) | `Box<Base>` |
| `l: List<Number>` | `java.util.List<? extends java.lang.Number>` |
| `l: List<Any>` | `java.util.List<? extends java.lang.Object>` |
| `fun listReturn(): List<Number>` | `java.util.List<java.lang.Number>` |
| `l: MutableList<Number>` | `java.util.List<java.lang.Number>` |
| `l: MutableList<out Number>` | `java.util.List<? extends java.lang.Number>` |
| `l: MutableList<in Number>` | `java.util.List<? super java.lang.Number>` |
| `l: MutableList<*>` and `l: List<*>` | `java.util.List<?>` |
| `c: Comparable<Number>` | `java.lang.Comparable<? super java.lang.Number>` |
| `s: Sink<Base>` (Sink is `in T`) | `Sink<? super Base>` |
| `f: (Number) -> Base` | `kotlin.jvm.functions.Function1<? super java.lang.Number, ? extends Base>` |
| `a: Array<out Number>` / `Array<Number>` | `java.lang.Number[]` |
| `a: Array<in Number>` | `java.lang.Object[]` |
| `fun nothingList(): List<Nothing>` | raw `java.util.List` |
| `l: List<List<Number>>` | `java.util.List<? extends java.util.List<? extends java.lang.Number>>` |
| `m: Map<String, Base>` | `java.util.Map<java.lang.String, ? extends Base>` (K invariant, V `out`) |
| `@JvmSuppressWildcards fun allSuppressed(l: List<Number>, s: Sink<Base>)` | `allSuppressed(java.util.List<java.lang.Number>, Sink<Base>)` |
| `l: List<out String>` (redundant projection) | `java.util.List<java.lang.String>` |
| `fun <T : Comparable<T>> maxOf(a: T, b: T): T` | `<T extends Comparable<? super T>> T maxOf(T, T)` |
| `where T : CharSequence, T : Comparable<T>` | `<T extends CharSequence & Comparable<? super T>>` |
| `fun <T> dnn(x: T & Any): T & Any` | `<T> T dnn(T)` |
| `fun readDict(): Map<String, *>` | `java.util.Map<java.lang.String, ?>` |
| `fun <T> myBuild(block: MutableList<T>.() -> Unit)` | `Function1<? super java.util.List<T>, kotlin.Unit>` |
| `inline fun <reified T> reifiedFn(x: Any)` | `public static final synthetic <T> boolean reifiedFn(Object)` (invisible to javac) |

- From Java, `Interop.unboxBase(Interop.boxDerived(new Derived()))` compiles and runs because of the generated `? extends`. The docs say a naive translation would make this "impossible" in Java — P-javac + [Kotlin docs: Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- Kotlin docs on the use-site correspondence: `Array<out Any>` "corresponds to Java's `Array<? extends Object>`", and `Array<in String>` to "Java's `Array<? super String>`". The real JVM signatures are `Object[]`/`Number[]` (table above). The docs phrasing is conceptual — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html); [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- `*` vs Java raw types: star projections are "very much like Java's raw types, but safe" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)

### Inferences
- `MutableList<*>` ⇔ `List<?>` and `List<Any>` ⇔ `List<? extends Object>` (as parameters). So a teacher can say "`List<*>` and `List<Any?>` are both readable-as-`Any?`, but only the star form is also a projection." For read-only `List`, `List<*>` and `List<Any?>` accept the same arguments. For `MutableList`, they differ: `MutableList<Any?>` rejects `MutableList<String>` (probe).
- "Wildcards only in parameters" means a Kotlin library returning `List<Number>` gives Java callers an invariant `List<Number>`. That is ergonomic for Java callers, but it is a different contract from what Kotlin callers see. This is worth one slide in the interop lesson.
- Java interop direction (Java → Kotlin): Java `List<? extends T>` appears in Kotlin as a `(Mutable)List<out T>`-style flexible type. I did not probe this (see Gaps).

### Gaps
- I did not verify how Kotlin presents Java wildcard signatures (`? extends`, `? super`, raw types) on the Kotlin side, including flexible "(Mutable)List<…>!" platform types. The `java-interop.html` page was not fetched.
- I did not test `@JvmSuppressWildcards` at class level or with `suppress = false`.

---

## Key Question 3: Which teaching approaches and mental models work best for variance, and what do learners typically get wrong?

### Takeaway
The models that hold up are the ones that predict compiler behavior:
1. **Producer/consumer** ("Consumer in, Producer out", the Kotlin docs' own mnemonic, and PECS from *Effective Java* Item 31).
2. **"Can a `C<Derived>` stand in for a `C<Base>` without lying?"** This is the substitution check.
3. **A sign rule for positions.** It mechanically predicts nested cases.

The most damaging misconception is "`out` means read-only/immutable". The docs reject it explicitly, and probes show `MutableList<*>` and `MutableList<out T>` still allow `clear()`/`removeAt()`.

### Cited Findings
- The official mnemonic is "Consumer in, Producer out!". The docs also say the `in`/`out` words "seem to be self-explanatory (as they've already been used successfully in C# for quite some time)" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- PECS comes from *Effective Java* 3rd ed. Item 31, and the docs present it as the Java background for Kotlin's design — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- "The only thing guaranteed by wildcards (or other types of variance) is type safety. Immutability is a completely different story." — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)
- Evidence against "out = immutable":
  - `star.clear()` and `star.removeAt(0)` compile on `MutableList<*>`.
  - `class Box<out T>(private val items: MutableList<T>)` compiles.
  - `@UnsafeVariance` lets an `out` class accept `T` (`fun add(t: @UnsafeVariance T)`).
  - Source: [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- Evidence against "`in` means you can't read". Reading from `MutableList<in String>` compiles and gives `Any?`; only reading into `String` fails (`actual 'CapturedType(in String)'`) — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- Evidence against "a class equals a type". `MutableList::class == List::class` is `true`. `KClass` drops type arguments and nullability. `typeOf<List<String>>() == typeOf<List<String>?>()` is `false` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip); [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)
- Evidence against "a bad cast fails at the cast". `listOf(1, 2) as Any as List<String>` succeeds (`size` = 2) and fails only at `val s: String = l[0]` with a `ClassCastException`. Java raw types behave the same way — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip); P-javac
- Evidence against "reified gives full runtime generics". `asPairOf<String, List<String>>()` "Compiles but breaks type safety!" — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)

### Inferences
These are teaching judgments built on the cited behavior, not on pedagogy research.
- **Why generics "never stick":** learners memorize slogans (PECS, "out = produce") without a check they can run in their heads. Pair each slogan with the substitution question: "If I secretly hand you a `Box<Apple>` where you expected `Box<Fruit>`, which of your calls could go wrong?" If only reads exist, nothing goes wrong, so `out` is safe. If a write exists, you could insert a Banana, so the type must be invariant.
- **The arrow picture:** draw `Apple → Fruit` (subtype arrow). `out` keeps the arrow (`Box<Apple> → Box<Fruit>`), `in` reverses it (`Juicer<Fruit> → Juicer<Apple>`), and invariant erases it. Function types show both at once: `(Fruit) -> Apple` is a subtype of `(Apple) -> Fruit`.
- **The type-checker as a safety guard:** frame every variance error as "the compiler refused a call that *could* store the wrong thing", then show the runtime failure it prevents. Java arrays give the perfect "what if there were no guard" demo: `ArrayStoreException`. Unchecked casts give the delayed-failure demo: heap pollution and a `ClassCastException` far from the cause.
- **Analogies that hold up:**
  - A fruit **vending machine** (produces fruit): out/covariant.
  - A **juicer** or **recycling bin** (accepts fruit): in/contravariant.
  - A **two-way locker** (put and take): invariant.
- **Analogies that break:**
  - "out = read-only view": the clear/remove counterexample.
  - "`*` = `Any?`": `MutableList<*>` rejects even `null`, while `MutableList<Any?>` accepts anything but rejects a `MutableList<String>` argument.
  - "star = raw type": raw types allow unchecked writes, while `*` forbids them.
- **Learners will try to put variance on functions.** Show the `variance annotations are only allowed for type parameters of classes and interfaces.` error early.
- **Teach the sign rule after** the intuition, as a tool for nested cases (callbacks, `Comparable<T>` params, `(T) -> Unit` returns). Learners will otherwise guess on these.

### Gaps
- I found and fetched no empirical studies on learning difficulties with variance or generics. Searches were not run, and Java and pedagogy sites were partly blocked. Teaching claims above are reasoned inferences, not research-backed findings. The sibling notes file `learning_science.md` in the same folder may cover general learning-science principles. I did not read or verify it.
- *Kotlin in Action* (generics chapter) and the Java Tutorial's wildcard guidelines (in/out variables) were not accessible, so their specific framings are not quoted.

---

## Key Question 4: What can and cannot be done with `KClass` and `typeOf` without kotlin-reflect in Kotlin 2.4?

### Takeaway
Without `kotlin-reflect.jar`, these all work:
- class literals and their names (`simpleName`, `qualifiedName`)
- `isInstance` / `cast` / `safeCast`
- `KClass` equality and `.java` / `.kotlin` / `javaClass` / `javaObjectType` / `javaPrimitiveType`
- `typeOf<T>()` with `classifier`, `arguments`, `variance` and `isMarkedNullable`
- `KType.javaType` (needs `@OptIn(ExperimentalStdlibApi::class)`)
- callable references' `name` and `get()`

Anything about declarations throws `KotlinReflectionNotSupportedError`: `objectInstance`, `sealedSubclasses`, `isData`, `isSealed`, `members`, `constructors`, `typeParameters`, `supertypes`, `visibility`, `returnType`. `kotlin.reflect.full`/`kotlin.reflect.jvm` extensions throw `NoClassDefFoundError`. `toString()` output changes too.

### Cited Findings
- `KClass` is declared `expect interface KClass<T : Any> : KClassifier`. On the JVM it is `actual interface KClass<T : Any> : KDeclarationContainer, KAnnotatedElement, KClassifier`. The type parameter has no declaration-site variance. `sealedSubclasses: List<KClass<out T>>` (JVM, since 1.3). `objectInstance: T?`, `members`, `constructors`, `isData` and the other introspection members are JVM-only. `simpleName`/`qualifiedName`/`isInstance` are common. `cast`/`safeCast` are common extensions in `kotlin.reflect` (since 1.4). `KClass<T>.java`, `javaObjectType` and `javaPrimitiveType` are in `kotlin.jvm`. `isInterface` is JS-only `@ExperimentalStdlibApi` (since 2.2) — [KClass API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/-k-class/)
- Note: the KClass API extraction also listed a `javaClass` extension on `KClass` that returns the runtime class of the KClass object itself. That is a known confusion source, and 2.4.0 deprecates *property references* to `javaClass` (KTLC-375, warning): "Use `.javaClass` to get the runtime Java class of an object, or `::class.java` to get a Java class reference." — [Kotlin 2.4 compatibility guide](https://kotlinlang.org/docs/compatibility-guide-24.html)
- The JVM dependency: "the runtime component required for using the reflection features [is] a separate artifact, `kotlin-reflect.jar`". "Kotlin provides some basic features, such as class literals or callable references, as part of the language and standard library. To access more extensive runtime introspection, import the `kotlin-reflect` library." "The command-line compiler adds the library by default. To exclude it… use the `-no-reflect`". The docs do not list per-member requirements — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)
- `value::class` is `KClass<out T>`. The docs example is `val runtimeClass: KClass<out Language> = language::class` — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html). The probe `val k: KClass<String> = s::class` → `initializer type mismatch: expected 'KClass<String>', actual 'KClass<out String>'.` `KClass<String?>` → `type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.` `x::class` on nullable `T` → `expression in class literal has nullable type 'T (of fun <T> nullableClassLit)'. Use '!!' to make the type non-nullable.` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- `typeOf`: `inline fun <reified T> typeOf(): KType`, "Returns a runtime representation of the given reified type T as an instance of KType", since Kotlin 1.6. On the JVM "the created type has no annotations" — [typeOf API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html). "use the `typeOf<T>()` function to obtain a `KType` for the statically known type `T`, including its type arguments and nullability" — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)
- **Runtime matrix (2.4.21 stdlib on JDK 21; same compiled classes run with and without `kotlin-reflect.jar`)** — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip):

| Expression | Without kotlin-reflect | With kotlin-reflect |
|---|---|---|
| `Circle::class.simpleName` / `.qualifiedName` | `Circle` / `Circle` | same |
| `isInstance(Circle(1.0))` | `true` | same |
| `cast(Circle(2.0))` / `safeCast("nope")` | `Circle(r=2.0)` / `null` | same |
| `cast("nope")` | `ClassCastException: Value cannot be cast to Circle` | same |
| `Circle::class.java`, `Circle(1.0).javaClass` | `class Circle` | same |
| `String::class.java.kotlin` (toString) | `class java.lang.String (Kotlin reflection is not available)` | `class kotlin.String` |
| `Circle(1.0)::class == Circle::class` | `true` | same |
| `Int::class.java` / `.javaObjectType` / `.javaPrimitiveType` | `int` / `class java.lang.Integer` / `int` | same |
| `listOf(1)::class.qualifiedName` | `java.util.Collections.SingletonList` | same |
| `Origin::class.objectInstance` | **throws** `KotlinReflectionNotSupportedError: Kotlin reflection implementation is not found at runtime. Make sure you have kotlin-reflect.jar in the classpath` | `Origin@…` |
| `sealedSubclasses`, `isData`, `isSealed`, `members`, `constructors`, `typeParameters`, `supertypes`, `visibility` | **throw** `KotlinReflectionNotSupportedError` | `[class Circle, class Origin]`, `true`, `true`, `6`, `1`, `[T]`, `[Shape, kotlin.Any]`, `PUBLIC` |
| `NoArg::class.createInstance()`, `isSubclassOf` (`kotlin.reflect.full`) | **throw** `NoClassDefFoundError: kotlin/reflect/full/KClasses` | work |
| `typeOf<List<String?>>()` (toString) | `java.util.List<java.lang.String?> (Kotlin reflection is not available)` | `kotlin.collections.List<kotlin.String?>` |
| `.classifier` | `interface java.util.List (Kotlin reflection is not available)` | `class kotlin.collections.List` |
| `typeOf<Map<String, List<Int>>>().arguments` | works (Java-style names) | `[kotlin.String, kotlin.collections.List<kotlin.Int>]` |
| `typeOf<String?>().isMarkedNullable` | `true` | same |
| `typeOf<List<*>>().arguments` | `[*]` | same |
| `typeOf<MutableList<out Number>>().arguments.single().variance` | `OUT` | same |
| `typeOf<Map<String, List<Int>>>().javaType` | `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>` | same |
| `.jvmErasure` (`kotlin.reflect.jvm`) | **throws** `NoClassDefFoundError: kotlin/reflect/jvm/KTypesJvm` | `class kotlin.collections.Map` |
| `typeOf<List<String>>() == typeOf<List<String>>()` / vs `List<String>?` | `true` / `false` | same |
| `filterIsInstance<String>()` | works | same |
| `Circle::r.get(Circle(3.0))`, `Circle::r.name`, `::main.name` | `3.0`, `r`, `main` | same |
| `Circle::r.returnType` | **throws** `KotlinReflectionNotSupportedError` | `kotlin.Double` |

- `KType.javaType` **still requires opt-in in 2.4.21**. Without it: `this declaration needs opt-in. Its usage must be marked with '@kotlin.ExperimentalStdlibApi' or '@OptIn(kotlin.ExperimentalStdlibApi::class)'` — [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)
- On the JVM, "the `kotlin-reflect` library provides extensions in the `kotlin.reflect.jvm` package for converting between Kotlin and Java reflection objects", e.g. `User::name.javaGetter` and `User::name.javaField`. `.kotlin` converts `Class` → `KClass`. The docs example `fun getKClass(o: Any): KClass<Any> = value.javaClass.kotlin` has a bug: it references `value` but the parameter is `o` — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)
- **Type tokens.** A Java `Class<T>` token cannot express `List<String>`; Kotlin rejects `List<String>::class` (`only classes are allowed on the left-hand side of a class literal.`). A Java super type token works through the anonymous subclass's generic superclass: `new TypeRef<Map<String, List<Integer>>>() {}.type` printed `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>`. Here `TypeRef`'s constructor reads `((ParameterizedType) getClass().getGenericSuperclass()).getActualTypeArguments()[0]`. The Kotlin replacement `typeOf<List<String>>().javaType` printed `java.util.List<java.lang.String>` without kotlin-reflect — P-javac + [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip)

### Inferences
- Rule of thumb for lessons: **"names, identity, instance checks, casts, and `typeOf` are free; anything that enumerates or describes declarations needs kotlin-reflect."**
- Teach `toString()` differences up front. Learners printing `String::class` without kotlin-reflect see `class java.lang.String (Kotlin reflection is not available)` and assume something is broken. Note that the `kotlinc`/`kotlin` CLI adds kotlin-reflect by default, so behavior can differ between CLI runs and a Gradle build.
- For libraries that want a `java.lang.reflect.Type` (Gson `TypeToken`, Jackson `TypeReference`), an `inline fun <reified T> …` that passes `typeOf<T>().javaType` replaces the anonymous-subclass trick in Kotlin code. It still needs the opt-in.

### Gaps
- Gafter's "Super Type Tokens" post (2006) could not be fetched (gafter.blogspot.com blocked). Its exact wording, and limitations such as a `TypeReference<T>` with a type variable capturing only `T`, are unverified here.
- I did not check Gson `TypeToken` or Jackson `TypeReference` API docs, or Kotlin-specific modules like jackson-module-kotlin's `jacksonTypeRef<T>()`. Their exact signatures are unverified.
- I did not test kotlin-reflect "lite" or other alternatives such as kotlinx-metadata for reading declaration info without full reflection.

---

## Key Question 5: What are good small exercises with clear compiler outcomes, plus build-something exercises?

### Takeaway
Every exercise below was compiled with kotlinc 2.4.21 (Java ones with javac 21.0.12), and the answers quote the real diagnostics. The four capstone builds were compiled and run: heterogeneous container, typed event bus, `Outcome`/`Either`, and `Repository<T : Entity<ID>, ID>`. All probe sources: [P-kotlinc](https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip).

### Cited Findings
"Does this compile?" sets (✓ compiles, ✗ error with the verbatim message, ⚠ warning). The full sets with answers are in **Teaching notes → Exercise sets** below. Build-something solutions (compiled and run in 2.4.21, outputs shown):

**B1. Type-safe heterogeneous container** (output `tm: hi 42 null`):
```kotlin
class TypedMap {
  private val m = mutableMapOf<KClass<*>, Any>()
  fun <T : Any> put(k: KClass<T>, v: T) { m[k] = v }
  fun <T : Any> get(k: KClass<T>): T? = k.safeCast(m[k])
  inline fun <reified T : Any> put(v: T) = put(T::class, v)
  inline fun <reified T : Any> get(): T? = get(T::class)
}
// tm.put("hi"); tm.put(42); tm.get<String>() == "hi"; tm.get<Int>() == 42; tm.get<Double>() == null
```
Extension prompt: why can't it store `List<String>` and `List<Int>` separately? Because `KClass` drops type arguments. A `KType` key from `typeOf<T>()` fixes it.

**B2. Typed event bus** (output `user 7`, `order 9.5`):
```kotlin
sealed interface Event { data class UserCreated(val id: Int) : Event; data class OrderPlaced(val total: Double) : Event }
class EventBus {
  private val handlers = mutableMapOf<KClass<out Event>, MutableList<(Event) -> Unit>>()
  fun <E : Event> subscribe(type: KClass<E>, handler: (E) -> Unit) {
    handlers.getOrPut(type) { mutableListOf() }.add { e -> type.safeCast(e)?.let(handler) }
  }
  inline fun <reified E : Event> subscribe(noinline handler: (E) -> Unit) = subscribe(E::class, handler)
  fun publish(event: Event) { handlers[event::class]?.forEach { it(event) } }
}
```
Teaching points:
- `KClass<out Event>` keys, because `event::class` is `KClass<out Event>`.
- `(E) -> Unit` cannot be stored as `(Event) -> Unit` (function parameters are `in`), hence the `safeCast` adapter.
- The handler must be `noinline` because it is stored.

**B3. Generic Result/Either with `Nothing` and `out`** (output `Right(value=2.0)`, `Ok(value=42)`, `-1`):
```kotlin
sealed interface Either<out L, out R> {
  data class Left<out L>(val value: L) : Either<L, Nothing>
  data class Right<out R>(val value: R) : Either<Nothing, R>
}
fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> =
  when (this) { is Either.Left -> this; is Either.Right -> Either.Right(f(value)) }
val e: Either<String, Int> = Either.Right(1)
val e2: Either<Any, Number> = e          // ✓ covariance in both params
```
Note: `is Either.Left -> this` type-checks as `Either<L, R2>` only because `Left<L>` is an `Either<L, Nothing>` and `Nothing` is a subtype of `R2`. This is the key "aha". (`Outcome<out T, out E>` with `Ok`/`Err`, `map`, `getOrElse` and `parse("41").map { it + 1 }` → `Ok(value=42)` was also verified.)

**B4. `Repository<T : Entity<ID>, ID : Comparable<ID>>` with a covariant read view** (output `Person(1,a)`, `entity 1`, `entity 2`):
```kotlin
interface Entity<ID : Comparable<ID>> { val id: ID }
interface ReadRepository<out T> { fun findAll(): List<T> }
interface Repository<T : Entity<ID>, ID : Comparable<ID>> : ReadRepository<T> {
  fun save(entity: T): T
  fun findById(id: ID): T?
}
class InMemoryRepository<T : Entity<ID>, ID : Comparable<ID>> : Repository<T, ID> {
  private val store = sortedMapOf<ID, T>()
  override fun save(entity: T): T { store[entity.id] = entity; return entity }
  override fun findById(id: ID): T? = store[id]
  override fun findAll(): List<T> = store.values.toList()
}
fun <T : Entity<ID>, ID : Comparable<ID>> Repository<T, ID>.saveAll(items: Iterable<T>): List<T> = items.map(::save)
fun printAll(repo: ReadRepository<Entity<*>>) = repo.findAll().forEach { println("  entity ${it.id}") }
// printAll(InMemoryRepository<Admin, Long>())  ✓ — works only because ReadRepository is `out T`
```
Interface segregation by variance: split read (`out`) from write (invariant/`in`) so read-only consumers get covariance. This is the Kotlin version of the docs' "DictionaryReader<T>/DictionaryWriter<T>" advice for avoiding unchecked casts — [Kotlin docs: Generics](https://kotlinlang.org/docs/generics.html)

### Inferences
- Order capstones by concept: B3 (variance plus `Nothing`) → B4 (bounds, recursive bounds, variance split) → B1 (KClass tokens and reified) → B2 (all of the above plus function-type variance).
- Each capstone has a natural "now break it" follow-up:
  - B3: remove `out` from `Either` and watch `is Left -> this` fail.
  - B4: make `ReadRepository` invariant and watch `printAll(admins)` fail.
  - B1: key by `KType`.
  - B2: try to store `handler` directly in the map.
  - These follow-ups were not compiled. Lesson writers should verify the exact messages.

### Gaps
- The "break it" variants above were not compiled, so their exact messages are unverified.
- The `KType`-keyed version of B1 was not compiled.

---

## Teaching notes

### Recommended order for the 11-lesson track (each lesson builds only on earlier ones)
1. **Type parameters and inference.** `fun <T>`, explicit vs inferred, `_` operator, builder inference (`buildList`). Show the inferred intersection type (`List<Comparable<*> & Serializable>`) as "the compiler finds a common supertype".
2. **Bounds.** Upper bounds, `where`, multiple bounds (one class max), `T : Any` vs the default `Any?`, `T & Any`. Include the Java `<T extends A & B>` comparison.
3. **Subtyping ≠ subclassing; invariance.** Java `List<String>` ↛ `List<Object>`. Java array covariance and `ArrayStoreException` as the "what if no guard" demo. Kotlin arrays are invariant. `String`/`String?` and `MutableList`/`List` are one class with two types.
4. **Covariance with `out` (declaration-site).** Producer intuition, then the position rules: constructor params, `val` vs `var`, `private` exemption plus private-to-this, protected/internal checked, inferred types. `@UnsafeVariance` and `List.contains`.
5. **Contravariance with `in`.** `Comparable<in T>`, consumers, function types `Function1<in P, out R>`, PECS ⇔ `out`/`in`. Then the sign rule for nested positions.
6. **Use-site variance / type projections.** `Array<out Any>`, `MutableList<in Number>`, what each projection forbids (verbatim errors), redundant and conflicting projection diagnostics. Map each to Java wildcards.
7. **Star projections.** Rules for out/in/invariant parameters. `MutableList<*>` vs `MutableList<Any?>` vs Java `List<?>` vs raw `List`. Show what you can still call (`clear`, `removeAt`, reads as `Any?`).
8. **Type erasure.** What is checked (`is List<*>`, smart casts with statically known arguments), unchecked-cast warnings, heap pollution, platform declaration clashes and `@JvmName`. What survives: the `Signature` attribute and reflection's `getGenericType()`.
9. **Reified type parameters.** `inline` + `reified`, `is T`, `T::class`, `filterIsInstance`, `typeOf<T>()`. Limits: `Nothing`, non-reified callers, nested arguments still erased, invisible to Java, the 2.4 `::class` nullable-bound error.
10. **KClass, KType, and type tokens.** `KClass<T : Any>`, `::class` → `KClass<out T>`, `.java`/`.kotlin`/`javaClass`, `isInstance`/`cast`/`safeCast`, the with/without kotlin-reflect matrix, Java `Class<T>` tokens vs super type tokens vs `typeOf<T>().javaType`.
11. **Advanced and interop capstone.** Recursive generics and self types, nested generics, generic and nested type aliases (2.3 Stable), the Java signature table, `@JvmWildcard`/`@JvmSuppressWildcards`, the Kotlin 2.x timeline. Build B1–B4.

### Misconceptions to target (each with a disproof the learner can run)
| Misconception | Disproof (verified) |
|---|---|
| "`out` means read-only / immutable" | `MutableList<*>`.`clear()`/`removeAt(0)` compile; `class Box<out T>(private val items: MutableList<T>)` compiles; docs: "Immutability is a completely different story." |
| "If `List<String>` is a `List<Any>`, then `MutableList<String>` is a `MutableList<Any>`" | `initializer type mismatch: expected 'MutableList<Any>', actual 'MutableList<String>'.` |
| "Subclass = subtype" | `String?` vs `String` share `String::class`; `MutableList::class == List::class` is `true`. |
| "`*` is the same as `Any?`" | `MutableList<Any?>` rejects `mutableListOf<String>()`; `MutableList<*>` accepts it but rejects `add(null)` (`null cannot be a value of a non-null type 'CapturedType(*)'.`). |
| "`*` is Kotlin's raw type" | Java raw `List` allows `add(1)` with only a warning, then a CCE later; Kotlin `*` forbids the write. |
| "With `in T`, you can't read at all" | Reads compile as `Any?`; only reads into `T` fail (`CapturedType(in String)`). |
| "Out-position = return type only" | `fun f(cb: (T) -> Unit)` is legal in an `out` class; `fun f(): (T) -> Unit` is not. |
| "`private` members can do anything" | They are private-to-this: `o.t` on another instance → `cannot access 'var t: T': it is private/*private to this*/ in 'C'.` |
| "A bad generic cast fails at the cast" | `as List<String>` succeeds; the CCE appears at the later read. |
| "Reified = full runtime generics" | `asPairOf<String, List<String>>()` "Compiles but breaks type safety!"; nested args are still erased. |
| "`KClass` knows `List<String>`" | `List<String>::class` → `only classes are allowed on the left-hand side of a class literal.` Use `typeOf`. |
| "Java can call any public Kotlin function" | Reified inline functions are `ACC_SYNTHETIC`; javac says `cannot find symbol`. |
| "Kotlin variance shows up as wildcards everywhere in Java" | Only in parameters, not in return types and not for final arguments; `MutableList` never. |

### Analogies that hold up (and their limits)
- **Vending machine / juicer / locker** for out / in / invariant. Limit: say explicitly that a vending machine can still be *emptied*. Variance restricts what *type* flows, not whether state changes.
- **Arrow direction** (`Apple → Fruit`; `out` keeps it, `in` flips it, invariant breaks it). This scales to function types and nested generics.
- **Type checker as safety guard:** every forbidden call is one that could smuggle a wrong-typed value in. Pair it with the Java array `ArrayStoreException` and heap-pollution CCE demos ("this is what happens when the guard is missing or bypassed").
- **Substitution test** ("if I secretly hand you a `C<Derived>`…"). This is the most general; use it to *derive* `out`/`in` instead of memorizing.
- **The sign rule** (+ out, − in, 0 invariant, multiply through nesting). This is the precise tool for nested cases; introduce it in lesson 5.
- PECS ⇔ "Consumer in, Producer out". Teach PECS only as the Java-reading aid in lessons 5–6. The Kotlin keywords already encode it.

### "Does this compile?" exercise sets with answers (all verified with kotlinc 2.4.21 / javac 21.0.12)

**Set 1 — invariance and arrays (Lesson 3)**
```kotlin
val ms: MutableList<String> = mutableListOf("a")
val ma: MutableList<Any> = ms        // 1
val la: List<Any> = ms               // 2
val ints: Array<Int> = arrayOf(1, 2)
val anys: Array<Any> = ints          // 3
val outAnys: Array<out Any> = ints   // 4
outAnys[0] = "x"                     // 5
```
1. ✗ `initializer type mismatch: expected 'MutableList<Any>', actual 'MutableList<String>'.`
2. ✓
3. ✗ `initializer type mismatch: expected 'Array<Any>', actual 'Array<Int>'.`
4. ✓
5. ✗ `receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.`
```java
List<String> s = new ArrayList<>();
List<Object> o = s;                    // J1
Object[] objs = new String[1];         // J2
objs[0] = Integer.valueOf(1);          // J3
```
- J1 ✗ `incompatible types: List<String> cannot be converted to List<Object>`
- J2 ✓
- J3 ✓ compiles, then **throws** `ArrayStoreException: java.lang.Integer` at run time.

**Set 2 — position rules (Lessons 4–5).** Use the `Producer`/`Consumer`/`OkOut`/`CtorVar` file in Key Question 1. Answers:
- ✗: `consume(t: T)` in `out`, `var v: T` in `out`, `produce(): T` and `val v: T` in `in`, `takesSupplier(f: () -> T)`, `mlist(): MutableList<T>`, `protected fun prot(t: T)`, `internal fun intern(t: T)`, `returnsConsumer(): (T) -> Unit`, `fun <R : T> generic()`, `class CtorVar<out T>(var t: T)`.
- ✓: constructor `val item: T`, `private var hidden: T`, plain `plain: T`, `private fun set(t: T)`, `takesCallback(f: (T) -> Unit)`, `list(): List<T>`, `cmp(c: Comparable<T>)`, `contains(element: @UnsafeVariance E)`, `private val items: MutableList<T>`.
- Bonus (private-to-this): `fun copyFrom(o: C<@UnsafeVariance T>) { t = o.t }` ✗ `cannot access 'var t: T': it is private/*private to this*/ in 'C'.`
- Bonus (inferred type): `class E<in T> { private fun produce(): T? = null; fun use() = produce() }` ✗ on `use`: `type parameter 'T' is declared as 'in' but occurs in 'out' position in type 'T? (of class E<in T>)'.`

**Set 3 — projections and star (Lessons 6–7)**
```kotlin
val mo: MutableList<out Any> = ms    // 1
mo.add("x")                          // 2
val first: Any = mo[0]               // 3
val mi: MutableList<in String> = mutableListOf<Any>()  // 4
mi.add("ok")                         // 5
val s: String = mi[0]                // 6
val a: Any? = mi[0]                  // 7
val star: MutableList<*> = ms        // 8
star.add("x")                        // 9
val e: Any? = star[0]                // 10
star.clear()                         // 11
star.removeAt(0)                     // 12
val c: Comparable<*> = 1             // 13
c.compareTo(1)                       // 14
fun t(st: MutableList<*>) { st.add(null) }               // 15
val m: MutableList<Any?> = mutableListOf<String>()       // 16
```
Answers:
- ✓: 1, 3, 4, 5, 7, 8, 10, 11, 12, 13.
- 2 ✗ `receiver type 'MutableList<out Any>' contains out projection which prohibits the use of 'fun add(element: E): Boolean'.`
- 6 ✗ `initializer type mismatch: expected 'String', actual 'CapturedType(in String)'.`
- 9 ✗ `receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.`
- 14 ✗ `receiver type 'Comparable<*>' contains star projection which prohibits the use of 'fun compareTo(other: T): Int'.`
- 15 ✗ `null cannot be a value of a non-null type 'CapturedType(*)'.`
- 16 ✗ `initializer type mismatch: expected 'MutableList<Any?>', actual 'MutableList<String>'.`

Extra:
- `fun rp(l: List<out String>)` ⚠ `projection is redundant: the corresponding type parameter of 'List<out String>' has the same variance.`
- `fun cp(l: List<in String>)` ✗ `projection conflicts with variance of the corresponding type parameter of 'List<in String>'. Remove the projection or replace it with '*'.`

Java counterpart (javac):
- `List<? extends Number> ln = new ArrayList<Integer>(); ln.add(1);` ✗ `incompatible types: int cannot be converted to CAP#1`
- `Number n = ln.get(0);` ✓
- `List<? super Integer> ls = new ArrayList<Number>(); ls.add(1);` ✓
- `Integer i = ls.get(0);` ✗ `incompatible types: CAP#1 cannot be converted to Integer`
- `List<?> w = s; w.add("x");` ✗ `incompatible types: String cannot be converted to CAP#1`
- `w.add(null);` ✓

**Set 4 — bounds and nullability (Lesson 2)**
```kotlin
fun <T : Comparable<T>> maxOf2(a: T, b: T): T = if (a > b) a else b
fun <T> both(t: T): String where T : CharSequence, T : Comparable<T> = t.toString()
fun <T> twoClasses(t: T) where T : Number, T : Exception {}          // 1
fun <T, U> boundedByParam(u: U) where U : T, U : Comparable<U> {}     // 2
fun <T> lengthOf(x: T) = x.length                                     // 3
fun <T> elvis(x: T, y: T & Any): T & Any = x ?: y                     // 4
fun <T : Any> dnnOnNonNull(x: T & Any) {}                              // 5
fun <T : Any> nonNull(x: T) = x.hashCode()
maxOf2(1, "a")                                                         // 6
both(StringBuilder("x"))                                               // 7
both(42)                                                               // 8
nonNull(null)                                                          // 9
class Repo<T : Any, ID : Comparable<ID>>
val r: Repo<String?, Int>? = null                                      // 10
```
1. ✗ `only one of the upper bounds can be a class.`
2. ✗ `type parameter cannot have any other bounds if it's bounded by another type parameter.`
3. ✗ `unresolved reference 'length'.`
4. ✓
5. ✗ `intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.`
6. ✗ `argument type mismatch: actual type is 'String', but 'Int' was expected.`
7. ✓ on modern JDKs (`StringBuilder` is `Comparable<StringBuilder>`). This is a good "surprise" item.
8. ✗ `cannot infer type for type parameter 'T'. Specify it explicitly.` and `argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.`
9. ✗ `cannot infer type for type parameter 'T'. Specify it explicitly.` and `null cannot be a value of a non-null type 'uninferred T (of fun <T : Any> nonNull)'.`
10. ✗ `type argument is not within its bounds: type parameter 'T (of class Repo<T : Any, ID : Comparable<ID>>)' must be subtype of 'Any', but actual: 'String?'.`

**Set 5 — function types and nested generics (Lessons 5, 11)**
```kotlin
val f: (Any) -> String = { it.toString() }
val g: (String) -> Any = f                       // 1
val h: (Any) -> String = g                       // 2
val ll: List<List<String>> = listOf()
val ll2: List<List<Any>> = ll                    // 3
val ml: MutableList<List<String>> = mutableListOf()
val ml2: MutableList<List<Any>> = ml             // 4
val ml3: MutableList<out List<Any>> = ml         // 5
val mp: Map<String, MutableList<Int>> = mapOf()
val mp2: Map<String, MutableList<Number>> = mp   // 6
val mp3: Map<Any, List<Number>> = mapOf<String, List<Int>>()   // 7
```
1. ✓
2. ✗ `initializer type mismatch: expected '(Any) -> String', actual '(String) -> Any'.`
3. ✓
4. ✗ `initializer type mismatch: expected 'MutableList<List<Any>>', actual 'MutableList<List<String>>'.`
5. ✓
6. ✗ `initializer type mismatch: expected 'Map<String, MutableList<Number>>', actual 'Map<String, MutableList<Int>>'.`
7. ✗ `initializer type mismatch: expected 'Map<Any, List<Number>>', actual 'Map<String, List<Int>>'.` (K is invariant.)

**Set 6 — erasure, reified, KClass (Lessons 8–10)**
```kotlin
fun <T> isT(x: Any) = x is T                          // 1
fun isListOfString(x: Any) = x is List<String>        // 2
fun starOk(x: Any) = x is List<*>                     // 3
fun h2(c: Collection<String>) = c is List<String>     // 4
fun h3(c: Collection<String>) = c is List<Int>        // 5
fun castList(x: Any) = x as List<String>              // 6
fun <reified T> notInline(x: Any) = x is T            // 7
inline fun <reified T> isA(x: Any) = x is T
inline fun <reified T : Any> kcls(): KClass<T> = T::class
fun <T> callsReified(x: Any) = isA<T>(x)              // 8
fun nothingArg() = kcls<Nothing>()                    // 9
fun <T> nullableClassLit(x: T) = x::class             // 10
fun boundRef(s: String) { val k: KClass<String> = s::class }   // 11
val kNullable: KClass<String?>? = null                // 12
val k = List<String>::class                           // 13
inline fun <reified T> klassOf(x: T) = x::class       // 14 (new error in 2.4)
class GenEx<T> : Exception()                          // 15
class Foo<T> { fun make(): T = T() }                  // 16
fun List<String>.dup(): Int = 1
fun List<Int>.dup(): Int = 2                          // 17
```
1. ✗ `cannot check for instance of erased type 'T (of fun <T> isT)'.`
2. ✗ `cannot check for instance of erased type 'List<String>'.`
3. ✓
4. ✓ (the type argument follows from the static type)
5. ✗ `cannot check for instance of erased type 'List<Int>'.`
6. ⚠ `unchecked cast of 'Any' to 'List<String>'.`
7. ✗ `only type parameters of inline functions can be reified.`
8. ✗ `cannot use 'T' as reified type parameter. Use a class instead.`
9. ✗ `cannot use 'Nothing' as reified type parameter.`
10. ✗ `expression in class literal has nullable type 'T (of fun <T> nullableClassLit)'. Use '!!' to make the type non-nullable.`
11. ✗ `initializer type mismatch: expected 'KClass<String>', actual 'KClass<out String>'.`
12. ✗ `type argument is not within its bounds: type parameter 'T (of interface KClass<T : Any>)' must be subtype of 'Any', but actual: 'String?'.`
13. ✗ `only classes are allowed on the left-hand side of a class literal.`
14. ✗ (2.4.0+, KTLC-370) `expression in class literal has nullable type 'T (of fun <T> klassOf)'. Use '!!' to make the type non-nullable.`
15. ✗ `subclass of 'Throwable' cannot have type parameters.`
16. ✗ `type parameter 'T' is not an expression.`
17. ✗ `platform declaration clash: The following declarations have the same JVM signature (dup(Ljava/util/List;)I):` (backend error; it appears only once frontend errors are fixed). Fix: `@JvmName`.

Caution: in 2.4.21, frontend warnings (e.g. ⚠ 6) were **not printed** when the same file also had errors. Put warning items in a separate, otherwise-clean file.

**Set 7 — predict the output (Lessons 8–10; runtime, no kotlin-reflect on the classpath)**
- `(listOf(1, 2) as Any as List<String>).size` → `2`.
- `val s: String = (listOf(1, 2) as Any as List<String>)[0]` → `ClassCastException`.
- `println(String::class)` → `class java.lang.String (Kotlin reflection is not available)`. With kotlin-reflect: `class kotlin.String`.
- `println(typeOf<List<String?>>())` → `java.util.List<java.lang.String?> (Kotlin reflection is not available)`.
- `Origin::class.objectInstance` → `KotlinReflectionNotSupportedError`.
- `listOf(1, "a", 2.0, "b").filterIsInstance<String>()` → `[a, b]`.
- `MutableList::class == List::class` → `true`.

**Set 8 — Java generics refresher (Lesson 3 or 6; javac 21)**
- `new T()` ✗ `unexpected type`
- `new T[1]` ✗ `generic array creation`
- `new List<String>[10]` ✗ `generic array creation`
- `obj instanceof List<String>` (obj: Object) ✗ `Object cannot be safely cast to List<String>`
- `s instanceof ArrayList<String>` (s: `List<String>`) ✓
- `static <T extends Comparable<T>> T strict(List<T> l)` called with `List<Dog>` (Dog extends Animal implements `Comparable<Animal>`) ✗ `reason: inference variable T has incompatible equality constraints Animal,Dog`
- the PECS version `<T extends Comparable<? super T>> T pecs(List<? extends T> l)` ✓
- The Kotlin `fun <T : Comparable<T>> List<T>.biggest()` on `listOf(Dog(1), Dog(5))` ✓ (returns `Dog`; `T` inferred as `Animal` through `List<out E>`).

**Set 9 — predict the Java signature (Lesson 11).** Show the Kotlin column of the table in Key Question 2 and have learners write the Java column. Highlights:
- the return type gets no wildcard
- `List<String>` gets no wildcard (final)
- `MutableList<Number>` gets no wildcard (invariant)
- `List<Any>` → `List<? extends Object>`
- `Array<in Number>` → `Object[]`
- `List<Nothing>` → raw `List`
- `<T : Comparable<T>>` → `<T extends Comparable<? super T>>`

### Practical notes for lesson writers
- Diagnostics are K2 wording from 2.4.21 (lowercase first letter in the CLI). Older blog posts show K1 messages, e.g. "Type parameter T is declared as 'out' but occurs in 'in' position in type T". Don't mix the two.
- The kotlinlang generics page still shows the older unchecked-cast warning wording. The 2.4.21 CLI says `unchecked cast of 'Map<String, *>' to 'Map<String, Int>'.`
- The kotlinlang reflection page has a typo in `getKClass(o: Any)` (it uses `value`). Don't copy it verbatim.
- `@BuilderInference` is deprecated (2.4.21 warning). Don't teach it; builder inference is automatic.
- `KType.javaType` still needs `@OptIn(ExperimentalStdlibApi::class)` in 2.4.21.
- Running examples with the `kotlinc`/`kotlin` CLI puts kotlin-reflect on the classpath by default ("The command-line compiler adds the library by default"). Gradle projects don't, so reflection examples may behave differently in the two setups — [Kotlin docs: Reflection](https://kotlinlang.org/docs/reflection.html)

---

## Verified URLs
Every URL below was fetched or downloaded successfully in this session:

| URL | What it covers |
|---|---|
| https://kotlinlang.org/docs/generics.html | Declaration-site variance, `in`/`out`, PECS/Effective Java Item 31 reference, type projections, star-projection rules, generic functions, upper bounds and `where`, `T & Any`, type erasure, unchecked casts, reified `asPairOf`, the underscore operator. No `@UnsafeVariance` and no version numbers (page dated 29 Sep 2026). |
| https://kotlinlang.org/docs/inline-functions.html | Reified type parameters (`findParentOfType`, `membersOf`), restrictions (non-inline, `Nothing`, non-reified args), inline properties. No `typeOf`. |
| https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/-k-class/ | `KClass<T : Any>` declarations per platform, every property and function with platform and since-version, extensions (`cast`, `safeCast`, `java`, `javaObjectType`, `javaPrimitiveType`, `createInstance` (JS)). |
| https://kotlinlang.org/docs/reflection.html | kotlin-reflect.jar requirement and `-no-reflect`, `::class`/`value::class` (`KClass<out Language>`), `KClass` vs `KType`, `typeOf`, `kotlin.reflect.jvm` interop (`javaGetter`/`javaField`), `.kotlin`. |
| https://kotlinlang.org/docs/java-to-kotlin-interop.html | Variant generics → Java wildcards (params vs returns, final args), `@JvmWildcard`, `@JvmSuppressWildcards`, `Nothing` → raw type, `@JvmName` for erasure clashes. |
| https://kotlinlang.org/docs/whatsnew24.html | Kotlin 2.4.0 (released July 14, 2026): stable context parameters and explicit backing fields, collection literals (Experimental), Java 26 bytecode, JS `.d.ts` variance preservation. No generics or inference changes listed. |
| https://kotlinlang.org/docs/compatibility-guide-24.html | 2.4.0 deprecations and errors: KTLC-284, -363, -370, -372, -373, -375, -384, -388. |
| https://kotlinlang.org/docs/whatsnew23.html | Kotlin 2.3.0 (Dec 16, 2025): nested type aliases Stable, Java 25 bytecode support. |
| https://kotlinlang.org/docs/whatsnew22.html | Kotlin 2.2.0 (June 23, 2025): nested type aliases Beta (`-Xnested-type-aliases`, cannot mention outer type params), context parameters and context-sensitive resolution (Preview), Java 24 bytecode. |
| https://kotlinlang.org/docs/whatsnew20.html | Kotlin 2.0.0 (May 21, 2024): K2 default and Stable; smart-cast improvements (common supertype for `||`). |
| https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/ | `@UnsafeVariance` declaration, `TYPE` target, "Suppresses errors about variance conflict", since 1.0. |
| https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html | `inline fun <reified T> typeOf(): KType`, since 1.6, no annotations on JVM (source tag 2.4.20). |
| https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-compiler-embeddable/maven-metadata.xml | Version list showing 2.4.20, 2.4.21 (latest 2.4.x) and 2.5.0-Beta1/Beta2 as of 2026-10-30. |
| https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip | Official kotlinc 2.4.21 distribution (89.7 MB) used for every P-kotlinc probe. Includes kotlin-stdlib, kotlin-reflect and kotlin-stdlib-sources (used to confirm `@UnsafeVariance` on `List.contains`/`containsAll`/`indexOf`). |

**Attempted but NOT verified** (blocked by this session's network policy; nothing from these pages is quoted):
- https://docs.oracle.com/javase/tutorial/java/generics/wildcardGuidelines.html (DNS blocked)
- https://docs.oracle.com/javase/specs/jls/se25/html/jls-10.html (DNS blocked)
- https://gafter.blogspot.com/2006/12/super-type-tokens.html (DNS blocked)
- api.github.com (HTTP 403)

To include them, docs.oracle.com and gafter.blogspot.com must be allowed in the session's network settings.
