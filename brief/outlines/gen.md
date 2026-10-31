# Track: gen, "Kotlin generics, properly" (lab: labs/generics, package workbench.generics.lNN)

Research notes: kotlin_generics.md (compiled with kotlinc 2.4.21; copy compiler messages exactly from it).

The learner says generics "never stuck". So: build intuition before rules, use many tiny
examples, show the compiler error for every wrong move, and repeat the producer/consumer
picture in every variance lesson. Each lesson needs a `compare` block (Java vs Kotlin).
Labs are mostly Kotlin; use Java where the point is Java's wildcards or arrays. Java and Kotlin
compile together in the same module, so a Java test can call Kotlin code and vice versa.
For "add the right variance" exercises, remember the stubs must compile with the tests. Either
start the stub with declarations that compile and missing behavior, or have tests inspect
generic signatures with java.lang.reflect (WildcardType, TypeVariable). You MAY create
labs/generics/build.gradle.kts that adds kotlin-reflect ONLY to the demo source set
("demoImplementation"(kotlin("reflect")) needs the kotlin plugin's helper; or use the coordinates
"org.jetbrains.kotlin:kotlin-reflect:2.4.21"), so gen-09 can show what works with and without it.

Lessons (ids and titles must match content/course.json):
- gen-01 Generics from zero: what goes wrong with Any/Object plus casts (ClassCastException at the
  wrong place), type parameters on classes and functions, inference, explicit type arguments
  (`emptyList<String>()`), Java `<T>` and diamond vs Kotlin. Lab: a generic `Stack<T>`, a generic
  `firstMatching`, a `Pair`-like `Either`-free result holder.
- gen-02 Bounds: `<T : Comparable<T>>`, `where` with two bounds, Java `<T extends A & B>`, the default
  bound `Any?` and `T : Any` for non-null, why `fun <T> f(x: T)` accepts null. Lab: `maxOfAll`,
  a `ClosedRange`-like `Window<T : Comparable<T>>`, a `where` function needing CharSequence & Comparable.
- gen-03 Subtyping vs subclassing: types vs classes (`String` <: `String?`), substitution principle,
  invariance of MutableList and of all Java generics, Java array covariance and ArrayStoreException,
  why Kotlin `List<String>` IS a `List<Any>` (teaser for out). Use a figure of the subtype arrows.
- gen-04 Covariance with out: producer, in/out positions, rules (val ok, var not, private exempt,
  constructor params), `List<out E>`, Java `? extends`, "out does not mean immutable". Lab ideas in notes.
- gen-05 Contravariance with in: consumer, `Comparator<in T>`, `(T) -> Unit` parameter positions,
  Java `? super`, PECS mapped to out/in. Lab: a `Sink<in T>`, sort with a general comparator,
  an event handler registry that accepts handlers of supertypes.
- gen-06 Use-site variance and type projections: `Array<out Any>`, `copy(from, to)`,
  `MutableList<in Number>`, Collections.copy's Java signature side by side, when to choose
  declaration-site vs use-site. Lab: `copyInto`, `fillWith`, `sumAll(List<out Number>)`.
- gen-07 Star projection: `List<*>`, `MutableList<*>` (read Any?, write nothing, `clear()` still works),
  `Foo<*>` for in, out and invariant parameters, `*` vs `Any?`, vs Java `?` and raw types,
  `is Map<*, *>` checks. Lab: `describe(Any)`, a printer for `Map<*, *>`, safe casts after `is List<*>`.
- gen-08 Type erasure and reified: what erases, `is List<String>` error, `inline fun <reified T>`,
  `filterIsInstance`, `T::class`, Java's `Class<T>` parameter workaround, why Java can't call
  reified functions, Kotlin 2.4 errors on `::class` of nullable reified T (from notes).
  Lab: `asOrNull<T>()`, `instancesOf<T>()`, a reified `parse<T>()` over a small registry.
- gen-09 KClass, Class and type tokens (the user asked for this one specially, give it care):
  `KClass<T : Any>`, why `x::class` is `KClass<out T>` (tie it to lesson 4), `.java`/`.kotlin`,
  `javaClass`, `isInstance`/`cast`/`safeCast`, names, what needs kotlin-reflect (objectInstance,
  sealedSubclasses, members) and the exact errors without it, `KType` and `typeOf<List<String>>()`
  keeping type arguments and nullability, Java `Class<T>` tokens and Jackson-style TypeReference
  super type tokens vs reified + typeOf. Lab: a `ServiceRegistry` keyed by `KClass`
  (`register(type: KClass<T>, impl: T)`, reified `get<T>()`), plus a lookup that needs `KType`
  because `List<String>` and `List<Int>` share one KClass.
- gen-10 Advanced: recursive bounds and self types (fluent builder hierarchy), `T & Any`,
  `@UnsafeVariance` and why `List.contains` needs it, function type variance
  (`Function1<in P, out R>`), `Nothing` as the bottom type (`emptyList()` is `List<Nothing>`),
  generic type aliases. Lab: self-typed builder hierarchy; compose functions with variance.
- gen-11 Workshop: a typed event bus (handlers are consumers, events are producers), a KType-keyed
  heterogeneous container (different from gen-09's KClass registry), `Either<out L, out R>`, a
  `Repository<T : Entity<ID>, ID>` with a covariant read-only view. A bigger lab (about 15 minutes).
  The track cheatsheet must include a variance table: Kotlin, Java, read?, write?, example.
