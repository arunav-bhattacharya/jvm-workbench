# Foundations of functional programming in Kotlin (Kotlin 2.4.21, JDK 21-25)

Scope: first-principles FP for an experienced Java/Kotlin backend engineer. It covers the ideas, how Kotlin writes each one, what it compiles to on the JVM, misconceptions, and small payments-style examples.

**How the compiler claims were checked.** Every "compiles to" claim marked **[Local]** was checked in this session. I ran the Kotlin compiler `kotlinc-jvm 2.4.21` (the `kotlin-compiler-embeddable-2.4.21` jar from the Gradle cache, run as `org.jetbrains.kotlin.cli.jvm.K2JVMCompiler`, `-jvm-target 21`) on OpenJDK 21.0.12. I inspected the output with `javap -c -p -v` and ran it. The test sources are reproduced in the Teaching notes. Nothing else was checked that way. Several non-Kotlin hosts were blocked by this session's network (destroyallsoftware.com, manning.com, arrow-kt.io, chalmers.se, kt.academy, wikipedia.org, blog.acolyer.org). The claims that depend on them are marked as such.

---

## 1. Pure functions, side effects, referential transparency, and "functional core, imperative shell"

### Takeaway
A **pure function** has an output that depends only on its inputs, and calling it changes nothing outside it (no I/O, no writes to shared state, no reading the clock or a random source). **Referential transparency** is the practical consequence: you can replace a call with its result and the program behaves the same. That is why pure code needs no mocks and can be tested with plain values. Gary Bernhardt's "functional core, imperative shell" (Destroy All Software, 2012) is the pragmatic architecture. Put decisions in a pure core, and put the I/O in a thin shell with few branches.

### Cited Findings
- John Hughes, "Why Functional Programming Matters", *The Computer Journal* 32(2):98-107, 1989. The paper is older: it dates from 1984 and circulated as a Chalmers memo. Revised versions appeared in 1989 and 1990, including in *Research Topics in Functional Programming* (1990). Its central argument is that modularity is the key to good software, and FP's main strength is better modularisation — [search summary of citation/history](https://www.infosun.fim.uni-passau.de/cl/lehre/funcprog05/whyfp.html); [Chalmers research portal, "How functional programming mattered"](https://research.chalmers.se/publication/224566). (Neither page could be fetched here: the hosts were blocked or only surfaced in search. The citation details come from the search results.)
- Hughes's well-known framing, recalled but NOT re-verified this session because the PDF host was blocked. Writers usually list FP's benefits negatively: "no assignment statements", "no side-effects", "A function call can have no effect other than to compute its result", which "eliminates a major source of bugs, and also makes the order of execution irrelevant". Hughes argues this negative list is not enough. The real gain is new "glue" for modular programs: **higher-order functions** and **lazy evaluation** — [whyfp.pdf (blocked)](https://www.cse.chalmers.se/~rjmh/Papers/whyfp.pdf). *Check the exact wording before quoting it in a lesson.*
- Gary Bernhardt's **"Boundaries"** talk (Destroy All Software) argues that simple *values*, not complex objects, should be the boundaries between components. The DAS page lists it as "from SCNA 2012". Other pages cite RubyConf 2012, so the venue is reported inconsistently, and he may have given it at both — [tildes.net (SCNA 2012)](https://tildes.net/~comp/ebn/boundaries_a_talk_by_gary_bernhardt_from_scna_2012); [Elixir Forum (RubyConf 2012)](https://elixirforum.com/t/boundaries-by-gary-bernhardt-ruby-conf-2012/13145). The primary page is https://www.destroyallsoftware.com/talks/boundaries (blocked here).
- The term **"Functional Core, Imperative Shell"** comes from a Destroy All Software screencast of that name (season 4 of the DAS catalog, according to search summaries) — https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell (blocked; details from the search results).
- Secondary write-ups summarise it like this. The functional core has "lots of behavior (code paths), but few dependencies". The imperative shell has "little behavior (code paths), but lots of dependencies". In the screencast, Bernhardt writes no unit tests for the shell because it has so few conditions — [waggertron notes](https://waggertron.github.io/tech-learning/topics/cs/functional-core-imperative-shell/); [kyle.au notes](https://kyle.au/notes/technology/development/functional-core-imperative-shell-pattern). (Secondary sources; treat as a paraphrase.)
- Kotlin has no `pure` keyword or purity checker. The closest tool is the opt-in return-value checker (`-Xreturn-value-checker=full`, with `@IgnorableReturnValue` for results that may be dropped). It flags discarded results, a common bug with copy-returning (pure) APIs. kotlinx.collections.immutable enabled it in 0.5.0-beta01 — [kotlinx.collections.immutable CHANGELOG](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md).

### Inferences
These are teaching framings built from the definitions above. They are standard definitions, but I could not fetch a primary source for the definition text in this session.
- **Plain definitions.** A *side effect* is anything a call does besides hand back its value: writing a DB row, charging a card, logging, mutating an argument or a field, or throwing on purpose for control flow. Reading hidden inputs, like `LocalDate.now()`, `Random`, or a mutable global, breaks purity too, because the same arguments can then give different results.
- **Referential transparency, payments demo.** Compare `val fee = feeFor(amount); total = fee + fee` with `total = feeFor(amount) + feeFor(amount)`. They are interchangeable only if `feeFor` is pure. Do the same with `chargeCard(amount)`: the "refactoring" now charges the customer twice. This is the clearest one-line way to show why the property matters.
- **Why testing gets easier.** For `fun lateFee(invoice: Invoice, today: LocalDate): Money`, a test is `assertEquals(Money("5.00"), lateFee(inv, LocalDate.of(2026, 3, 2)))`. You need no clock injection, no mocks and no setup or teardown. The impure version (`fun applyLateFee(inv: Invoice)` reads `LocalDate.now()`, mutates `inv.fee`, logs) needs a fake clock and checks on mutated state. Pure functions also allow caching (memoisation), safe retries and parallel calls.
- **FCIS in a payment service.** The shell loads the account, FX rate and `Clock.instant()`, then calls the core. The core is `decide(cmd: Charge, account: Account, rate: Rate, now: Instant): Decision`, where `Decision` is a value like `Approve(ledgerEntries)` or `Reject(reason)`. The shell then carries out the decision (DB write, PSP call). The core gets many fast unit tests. The shell gets a few integration tests.
- **Purity is a property of the call, not the language.** Kotlin cannot enforce it. Signals of purity are `val` parameters, immutable value types (data classes with `val`s), returning new values instead of `Unit`, and having no `suspend` or I/O dependencies in the signature.

### Gaps
- I could not fetch Hughes's paper, the Destroy All Software pages, or the Manning *Functional Programming in Kotlin* page (Vermeulen, Bjarnason, Chiusano) to quote their definitions verbatim. All three hosts were blocked by the session network. Rich Hickey material was not researched.
- No primary source confirms the DAS screencast's episode number or date. The SCNA vs RubyConf venue for "Boundaries" is still unresolved.

---

## 2. Function types, receivers, nullable function types, references, lambdas vs anonymous functions, closures, and what they compile to

### Takeaway
`(A) -> B` is an ordinary type. On the JVM it is the interface `kotlin.jvm.functions.Function1<A, B>`. A receiver type `A.() -> B` is the same interface, with the receiver as the first parameter. Since **Kotlin 2.0, lambdas and anonymous functions compile by default to `invokedynamic` + `LambdaMetafactory.metafactory`**: no class file, a private static `…$lambda$0` method, and a runtime hidden class. In 2.4.21, **callable references (`::f`, `Type::member`, `obj::member`, `::Ctor`) still compile to synthetic classes** extending `FunctionReferenceImpl` / `PropertyReference1Impl` unless they are inlined. So do `suspend` lambdas and `@JvmSerializableLambda` lambdas. A captured `var` becomes a `kotlin.jvm.internal.Ref$IntRef`, `Ref$LongRef` or `Ref$ObjectRef` box with a plain, non-volatile `element` field. `inline` functions remove the function object, the Ref box and the boxing entirely.

### Cited Findings

**Syntax and semantics (official docs)**
- "`(A, B) -> C` denotes a type that represents functions that take two arguments of types `A` and `B` and return a value of type `C`… The `Unit` return type cannot be omitted." — [Kotlin docs: Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html)
- "the type `A.(B) -> C` represents functions that can be called on a receiver object `A` with a parameter `B` and return a value `C`." Values of `(A, B) -> C` and `A.(B) -> C` can be used in place of each other. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Nullable function type: "use parentheses as follows: `((Int, Int) -> Int)?`". The arrow is right-associative: `(Int) -> (Int) -> Unit` means `(Int) -> ((Int) -> Unit)`. Suspend function types look like `suspend () -> Unit` or `suspend A.(B) -> C`. Typealiases work, e.g. `typealias ClickHandler = (Button, ClickEvent) -> Unit`. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Ways to get a function value: a lambda `{ a, b -> a + b }`, an anonymous function `fun(s: String): Int { … }`, a callable reference (`::isOdd`, `String::toInt`, `::Regex`, `foo::toString`), or a class that implements the function type (`class IntTransformer: (Int) -> Int { override operator fun invoke(x: Int): Int = … }`). — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Bound vs unbound references: "Bound reference captures a particular instance and requires only the function's declared arguments." "Unbound reference isn't attached to an instance, so its function type includes the receiver." Example: `User::hasName: (User, String) -> Boolean` vs `jane::hasName: (String) -> Boolean`. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Return semantics: "a `return` inside a lambda expression will return from the enclosing function, whereas a `return` inside an anonymous function will return from the anonymous function itself." A bare `return` in a lambda is only allowed when the lambda is passed to an inline function (a non-local return). Otherwise use a labelled `return@label`. Anonymous functions must go inside the parentheses; trailing-lambda syntax applies only to lambdas. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html); [inline-functions.html](https://kotlinlang.org/docs/inline-functions.html)
- Closures: "A lambda expression or anonymous function (as well as a local function and an object expression) can access its closure… The variables captured in the closure can be modified in the lambda." — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Kotlin 2.0 smart casts: a property of nullable function type (`val provider: (() -> Unit)?`) can be smart-cast after a null check and called as `provider()`. Inline functions are treated as having an implicit `callsInPlace` contract, so captured variables can be smart-cast inside their lambdas. — [What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)

**invokedynamic history (official release notes)**
- Kotlin 1.5.0 compiled **SAM conversions** (Java interfaces, and lambdas to Kotlin `fun interface`s) with `invokedynamic` via `LambdaMetafactory.metafactory()`. Rollback: `-Xsam-conversions=class`. In 1.5 the same treatment for **plain Kotlin lambdas** was experimental behind `-Xlambdas=indy`. — [What's new in Kotlin 1.5.0](https://kotlinlang.org/docs/whatsnew15.html)
- "In Kotlin 2.0.0, `invokedynamic` has become the default method for lambda generation." Three limitations: indy lambdas are not serializable; the experimental `reflect()` API does not support them; `toString()` is less readable (`FileKt$$Lambda$13/0x…@506e1b77` instead of `() -> kotlin.Unit`). To get the legacy behaviour, annotate a lambda with `@JvmSerializableLambda`, or use `-Xlambdas=class` for the whole module. — [What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)

**What 2.4.21 actually emits [Local]**
| Source | Bytecode at the creation site | Runtime class |
|---|---|---|
| `fun nonCapturing(): (Int) -> Int = { it + 1 }` | `invokedynamic invoke:()Lkotlin/jvm/functions/Function1;` (bootstrap `LambdaMetafactory.metafactory`, impl `private static int nonCapturing$lambda$0(int)`) | `fp.LambdasKt$$Lambda/0x00007f87ec001000` (hidden class) |
| `fun capturingVal(fee: Int) = { x: Int -> x + fee }` | `invokedynamic invoke:(I)Lkotlin/jvm/functions/Function1;`. The captured value is an indy argument, impl `capturingVal$lambda$0(int,int)` | `LambdasKt$$Lambda/…` |
| `var count = 0; val inc = { count += 1; count }` | `new kotlin/jvm/internal/Ref$IntRef`, then `invokedynamic invoke:(Lkotlin/jvm/internal/Ref$IntRef;)…Function0`. The body does `getfield/putfield Ref$IntRef.element` | `LambdasKt$$Lambda/…` |
| anonymous `fun(x: Int): Int { return x * 2 }` | `invokedynamic` (same as a lambda) | `LambdasKt$$Lambda/…` |
| receiver lambda `StringBuilder.() -> Unit = { append("hi") }` | `invokedynamic`, typed `Function1<StringBuilder, Unit>`. The receiver is parameter 1 | `LambdasKt$$Lambda/…` |
| Java SAM `Runnable { … }` / Kotlin `fun interface FeeRule` lambda | `invokedynamic run:()Ljava/lang/Runnable;` / `invokedynamic apply:()Lfp/FeeRule;` | `LambdasKt$$Lambda/…` |
| `::addFee` (top-level fun) | `getstatic LambdasKt$topRef$1.INSTANCE` | class `LambdasKt$topRef$1 extends kotlin.jvm.internal.FunctionReferenceImpl implements Function1` (singleton) |
| `a::canPay` (bound) | `new LambdasKt$boundRef$1(receiver)` | `extends FunctionReferenceImpl` (new instance per evaluation, holds the receiver) |
| `::Account` (constructor) | `getstatic …ctorRef$1.INSTANCE` | `extends FunctionReferenceImpl` |
| `String::length` | `getstatic …unboundRef$1.INSTANCE` | **`extends kotlin.jvm.internal.PropertyReference1Impl`**, because `length` is a *property*, so this is a property reference |
| `@JvmSerializableLambda { it + 1 }` | `getstatic …serializableLambda$1.INSTANCE` | `extends kotlin.jvm.internal.Lambda`; `toString()` = `Function1<java.lang.Integer, java.lang.Integer>` |
| `suspend () -> Int = { 42 }` | `new …suspendLambda$1` | `extends kotlin.coroutines.jvm.internal.SuspendLambda` (a state-machine class); type `Function1<Continuation<? super Integer>, Object>` |
- Compiling the same file with `-Xlambdas=class` (still accepted in 2.4.21) brings back one class per lambda: `LambdasKt$nonCapturing$1`, `LambdasKt$capturingVal$1`, `LambdasKt$capturingVar$inc$1`, `LambdasKt$anonFun$1`, `LambdasKt$receiver$1`, and so on. [Local]
- Identity and equality [Local]: `nonCapturing() === nonCapturing()` is **true**, because the call site caches one instance. For capturing lambdas, `cap(3) === cap(3)` is **false** and `cap(3) == cap(3)` is **false**: lambdas have no structural equality. For unbound function references, `ref() === ref()` is **true** (singleton `INSTANCE`) and `topRef() == topRef()` is true.
- `toString()` [Local]: an indy lambda prints `fp.LambdasKt$$Lambda/0x00007f87ec001220@4617c264`. A function reference prints `function addFee (Kotlin reflection is not available)` when kotlin-reflect is not on the classpath.
- Boxing [Local]: the indy bootstrap for `(Int) -> Int` has erased type `(Object)Object`, implementation `(I)I` and instantiated type `(Integer)Integer`. A call through the `Function1` interface therefore boxes `Int` to `java.lang.Integer` and back. (`Function1` is generic, so this follows from the type.)
- Function interfaces present in stdlib 2.4.21: `kotlin.jvm.functions.Function0` … `Function22` and `FunctionN` [Local, jar listing]. Arrow's `curried` overloads also stop at 22 parameters [Local, arrow-functions 2.3.0 jar].
- The `Ref` boxes are plain classes: `public static final class IntRef implements Serializable { public int element; … }` and `ObjectRef<T> { public T element; }`. They have no `volatile` and no synchronisation — [stdlib source: Ref.java](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/runtime/kotlin/jvm/internal/Ref.java)
- Race demo [Local]: `var total = 0L` was captured by 4 pool tasks, each doing `repeat(250_000) { total += 1 }`, which compiles to `Ref$LongRef`. Three runs printed **778714**, 1000000, 1000000 (expected 1000000). Lost updates are real but intermittent. A `fold` over immutable input always gave 1000000.

**Inline functions**
- "each function is an object, and it captures a closure… Memory allocations (both for function objects and classes) and virtual calls introduce runtime overhead." "The `inline` modifier affects both the function itself and the lambdas passed to it: all of those will be inlined into the call site." Inlining grows code but "will pay off in performance, especially at 'megamorphic' call-sites inside loops." — [Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- `noinline` keeps a lambda parameter as a real object, which you can store or pass on. `crossinline` forbids non-local returns, which you need when the lambda is called from another execution context such as an `object : Runnable`. `reified` type parameters work only in inline functions. The compiler warns when an inline function has nothing inlinable (`NOTHING_TO_INLINE`). Public inline functions cannot use private or internal declarations unless they are marked `@PublishedApi`. — [inline-functions.html](https://kotlinlang.org/docs/inline-functions.html)
- [Local] `fun inlineCaller(xs: List<Int>): Int { var total = 0; xs.forEach { total += it }; return measure { total } }` (with `measure` declared `inline`) contains **no `invokedynamic` and no `Ref$IntRef`**. The loop and the `nanoTime` calls are pasted into the method, and `total` stays a local `int`. The same `var` captured by a lambda passed to a non-inline `runIt(f: () -> Unit)` gets `new Ref$IntRef` and an `invokedynamic`.
- [Local] `xs.map(::addFee)` (an inline `map` with a function reference) compiles to a loop with a direct `invokestatic addFee:(I)I`. No reference class is generated. `Sequence.map { … }` is not inline, so its lambda is a real `invokedynamic` object.

### Inferences
- Allocation cost model to teach. A non-capturing lambda costs one-time linkage, then a cached instance. A capturing lambda allocates one object per evaluation, plus one `Ref` box per captured `var`. A bound reference allocates one object per evaluation. A lambda passed to an `inline` HOF allocates nothing, and its captured `var`s stay locals. Calls through `FunctionN` box primitives.
- Since 2.0, "lambdas got cheaper" (less bytecode, smaller jars, faster class loading). The JIT still has to inline through the interface call. `inline` remains the only *guaranteed* zero-allocation route.
- Tests or logs that assert on `lambda.toString()` changed output when projects moved from 1.9 to 2.x. Serialising lambdas (for example into a session store) needs `@JvmSerializableLambda`.

### Gaps
- No official doc or KEEP explains why callable references still compile to classes in 2.x. This is observed behaviour in 2.4.21 only [Local]. JetBrains' plans for indy-compiled references were not found.
- I did not measure what the first call of an indy lambda costs (bootstrap linkage) vs a class lambda. No JMH run was done.
- I did not compile a lambda with more than 22 parameters to confirm it uses `FunctionN`. Only its presence in the stdlib jar was confirmed.

---

## 3. Higher-order functions (HOFs)

### Takeaway
A higher-order function takes a function as a parameter, returns one, or both. Almost all of Kotlin's collection and scope-function API is made of HOFs, and most of it is `inline`, so idiomatic `map/filter/fold` chains on `Iterable` compile to plain loops. Returning a function, like a fee calculator built from a rate, is how you make small, configurable, pure building blocks.

### Cited Findings
- A higher-order function "takes functions as parameters, or returns a function". The docs' example is `fold`, with `combine: (acc: R, nextElement: T) -> R` "invoked inside the `for` loop". — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Trailing-lambda syntax: `items.fold(1) { acc, e -> acc * e }`. If the lambda is the only argument, drop the parentheses: `run { … }`. Single-parameter lambdas get the implicit `it`. Use `_` for unused parameters. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- The stdlib `fold` is literally an inline loop: `public inline fun <T, R> Iterable<T>.fold(initial: R, operation: (acc: R, T) -> R): R { var accumulator = initial; for (element in this) accumulator = operation(accumulator, element); return accumulator }` — [stdlib _Collections.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/common/src/generated/_Collections.kt)
- Function literals with receiver power builders: `fun html(init: HTML.() -> Unit)` calls `html.init()`, and inside the lambda the receiver is the implicit `this`. — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- [Local] A function *returning* a function: `fun capturingVal(fee: Int): (Int) -> Int = { it + fee }` compiles to an `invokedynamic` that captures `fee`. `buildList { add(1); add(2) }` (a HOF taking `MutableList<E>.() -> Unit`) returns a `kotlin.collections.builders.ListBuilder`.

### Inferences
- Stdlib HOFs worth naming in a lesson: `map`, `filter`, `fold`/`reduce`, `sumOf`, `groupBy`, `associateBy`, `sortedBy`, `partition`, `flatMap`, `any`/`all`/`none`, `firstOrNull { }`; the scope functions `let`/`run`/`apply`/`also`/`with`; `use` (resource closing); `lazy { }`; `repeat`; `buildList`/`buildMap`; `require`/`check` with lazy messages. Only `map`, `filter`, `fold`, `forEach` and `buildList` were exercised in this session's local compile.
- Payments examples: `payments.filter { it.status == SETTLED }.sumOf { it.amount }`, `payments.groupBy { it.merchantId }.mapValues { (_, ps) -> ps.sumOf { it.amount } }`, and `fun feeRule(percent: BigDecimal, min: BigDecimal): (BigDecimal) -> BigDecimal = { amt -> (amt * percent).max(min) }`.
- Eager `Iterable` chains build a new `ArrayList` at every step ([Local]: `map{}` returns `java.util.ArrayList`). `Sequence` is lazy but its operators are not inline (lambdas are objects). The trade-off is intermediate lists vs per-element virtual calls.

### Gaps
- I did not research a stdlib-wide list of which HOFs are `inline` and which are not. Only `fold` (source) and `map`/`forEach` (bytecode) were confirmed inline, and `Sequence.map` was confirmed non-inline.

---

## 4. Composition, currying and partial application

### Takeaway
**The Kotlin stdlib has no `compose`, `andThen` or `curried`.** [Local: the stdlib 2.4.21 jar contains none of these names, and `f andThen g` fails with `unresolved reference 'andThen' on receiver of type '(Int) -> Int'`.] They are 2-line extension functions to write by hand. **Arrow 2.3.0** ships them in the separate `io.arrow-kt:arrow-functions` module (`arrow.core.Composition`, `Currying`, `Partials`, `Memoization`). In everyday Kotlin, default and named arguments, lambdas and bound references already cover most partial application. Curried signatures like `(A) -> (B) -> (C) -> D` usually make backend code harder to read.

### Cited Findings
- [Local] `io.arrow-kt:arrow-functions-jvm:2.3.0` (from Maven Central; latest release per metadata updated 2026-10-27) contains these signatures:
  - `andThen(Function1<P1,IP>, Function1<IP,R>): Function1<P1,R>` (plus `Function0` and `Function2` overloads): `f andThen g` = `g(f(x))`.
  - `compose(Function1<IP,R>, Function1<P1,IP>): Function1<P1,R>`: `g compose f` = `g(f(x))`.
  - `curried(Function2<P1,P2,R>): Function1<P1, Function1<P2,R>>`, with overloads up to `Function22`, plus `uncurried`.
  - `partially1(Function2<P1,P2,R>, P1): Function1<P2,R>`, with overloads up to `Function22`, plus other `partiallyN`.
  - `Memoization` / `memoize` and `MemoizeKey0..5`. `arrow-core-jvm-2.3.0` contains `MemoizedDeepRecursiveFunction` and memoization caches.
  — [Maven metadata, arrow-functions](https://repo1.maven.org/maven2/io/arrow-kt/arrow-functions/maven-metadata.xml); [arrow-core](https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/maven-metadata.xml)
- Arrow's 0.12-era API docs show these as **infix** extensions, `infix fun <A,B,C> ((A) -> B).andThen(g: (B) -> C): (A) -> C` and `infix fun <A,B,C> ((B) -> C).compose(f: (A) -> B): (A) -> C`. A Kotlin Slack thread says they were brought over from the funKTionale library and originally did not support `suspend` functions — [old Arrow 0.12 apidocs: compose](https://old.arrow-kt.io/docs/0.12/apidocs/arrow-core-data/arrow.core/-and-then/compose.html); [kotlinlang Slack archive](https://slack-chats.kotlinlang.org/t/498208/is-there-a-reason-compose-andthen-etc-don-t-support-composin). (I did not confirm that 2.3.0 still marks them `infix`. Bytecode does not show modifiers, and arrow-kt.io was blocked.)
- Function types are right-associative, so the curried type `(Int) -> (Int) -> Unit` means `(Int) -> ((Int) -> Unit)` — [lambdas.html](https://kotlinlang.org/docs/lambdas.html)
- Default arguments and named arguments are built into Kotlin functions: `fun read(b: ByteArray, off: Int = 0, len: Int = b.size)` — [functions.html](https://kotlinlang.org/docs/functions.html)

### Inferences
Hand-written versions to teach. These are standard, but this exact snippet was not compiled this session.
```kotlin
infix fun <A, B, C> ((A) -> B).andThen(g: (B) -> C): (A) -> C = { a -> g(this(a)) }
infix fun <A, B, C> ((B) -> C).compose(f: (A) -> B): (A) -> C = { a -> this(f(a)) }
fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C = { a -> { b -> this(a, b) } }
fun <A, B, C> ((A, B) -> C).partial(a: A): (B) -> C = { b -> this(a, b) }

val addVat: (Money) -> Money = { it * 1.20 }
val roundToCents: (Money) -> Money = { it.rounded() }
val price = addVat andThen roundToCents          // left-to-right reads like a pipeline
```
- **When it helps:** a configurable pipeline of same-shaped steps (`List<(Payment) -> Payment>` reduced with `andThen`), validation chains, middleware/decorators (`retrying andThen logging`), and building specialised functions once at startup (a fee function per merchant tier).
- **When it hurts:** Kotlin's own idioms are usually clearer. A plain `x.let(f).let(g)`, an extension-function chain (`amount.withVat().roundedToCents()`), or a lambda `{ b -> fee(tier, b) }` beats `fee.curried()(tier)`. Curried types are noisy in signatures and IDE hints. Stack traces show `$$Lambda` frames instead of names. Each stage allocates a capturing closure, and composed functions are not `inline`. Named and default arguments already solve most of what currying solves in Haskell.
- Partial application without libraries: a bound reference (`merchant::feeFor`), a lambda closing over the fixed argument, or a default parameter.

### Gaps
- arrow-kt.io was blocked, so I have no current Arrow documentation quote on recommended use, or on whether the `arrow-functions` module is considered stable. The API was confirmed from bytecode only.
- No source found on JetBrains' stance (any KEEP) for adding `compose` to the stdlib.

---

## 5. Recursion and `tailrec`

### Takeaway
The JVM has no general tail-call elimination. Kotlin's `tailrec` makes the *compiler* rewrite **self**-recursive calls in tail position into a `goto` back to the start of the method: a real loop, with no stack growth. If the function is not in tail form, `tailrec` is only a **warning**. The code still compiles to ordinary recursion and can still throw `StackOverflowError`. For most backend aggregation, a `fold` or a loop is clearer than accumulator-passing recursion. Keep `tailrec` for algorithms that are naturally recursive (gcd, walking a parent chain, retry with state).

### Cited Findings
- Docs: "When a function is marked with the `tailrec` modifier and meets the required formal conditions, the compiler optimizes out the recursion, leaving behind a fast and efficient loop based version instead." Rules: "You can apply the `tailrec` modifier to a function only when it calls itself as its final operation. You cannot use tail recursion when there is more code after the recursive call, within `try`/`catch`/`finally` blocks, or when the function is open." The example is `tailrec fun findFixPoint(x: Double = 1.0): Double = if (abs(x - cos(x)) < eps) x else findFixPoint(cos(x))`, with the equivalent `while (true)` loop. — [Kotlin docs: Functions → Tail recursive functions](https://kotlinlang.org/docs/functions.html)
- Spec: "for all paths containing recursive calls the result of the recursive call must also be the result of the function. If a function declaration is marked with the `tailrec` modifier, but is not actually applicable for the optimization, it must produce a compile-time warning." The optimisation is described as platform-dependent ("may be optimized … by a particular platform"). — [Kotlin spec: Declarations → Tail recursion optimization](https://kotlinlang.org/spec/declarations.html)
- [Local] `tailrec fun gcd(a: Long, b: Long): Long = if (b == 0L) a else gcd(b, a % b)` compiles to stores into the parameter slots (`lstore_0`, `lstore_2`) followed by **`goto 0`**, with no `invokestatic gcd`. `tailrec fun sumTo(n: Long, acc: Long = 0)` does the same. `sumTo(1_000_000)` returned `500000500000`. The non-tail `sumToNaive(1_000_000)` (`n + sumToNaive(n - 1)`) threw `StackOverflowError` (run with `-Xss512k`).
- [Local] Diagnostics in 2.4.21 are **warnings**, not errors:
  - `tailrec fun notTail(n: Long): Long = if (n == 0L) 0 else n + notTail(n - 1)` gives `warning: a function is marked as tail-recursive but no tail calls are found.` and `warning: recursive call is not a tail call.` The bytecode keeps `invokestatic notTail`.
  - A recursive call inside `try { … } catch` gives `warning: tail recursion optimization inside try/catch/finally is not supported.`
- [Local] The stdlib 2.4.21 ships `kotlin.DeepRecursiveFunction`, `DeepRecursiveScope` and `kotlin.DeepRecursiveKt.invoke(DeepRecursiveFunction<T,R>, T)`. It is the stdlib tool for deep non-tail (and mutually) recursive functions; it keeps the stack on the heap using coroutine machinery. Arrow 2.3.0 adds `MemoizedDeepRecursiveFunction`.

### Inferences
- The fix for a non-tail recursion is usually an **accumulator parameter**: `n + f(n-1)` becomes `f(n-1, acc + n)`. Teach this as "make the pending work an argument".
- `tailrec` does not cover mutual recursion (`isEven` ↔ `isOdd`). The rule is "calls itself", so use a loop or `DeepRecursiveFunction`.
- For "sum the ledger", "apply all events to the state" or "find the first failing rule", `fold`/`sumOf`/`firstOrNull` say what you mean in one line and compile to the same loop. Recursion over a `List` with `head + tail` (`xs.drop(1)`) also copies the list at every step, which is O(n²).

### Gaps
- I did not verify which Kotlin version made `DeepRecursiveFunction` stable, or its exact API annotations. No docs page was fetched for it.
- The docs page does not say which non-JVM backends implement `tailrec`, and I did not research it.

---

## 6. Immutability: `val` vs `var`, read-only vs immutable collections, `copy()`, concurrency, kotlinx.collections.immutable

### Takeaway
`val` means *this reference is never reassigned*. It does not freeze the object it points to. `List<T>` is a **read-only view interface**, not an immutable collection. At runtime, `listOf(1,2,3)` is a `java.util.Arrays$ArrayList`, and code that casts it to `MutableList` can still `set` elements. Data class `copy()` is **shallow**. Real immutability means `val` properties holding immutable types all the way down. For collections, that means kotlinx.collections.immutable (persistent, structurally shared). It is now at **0.5.2**, still labelled Alpha/experimental, and since 0.5.0 its copy-returning methods are named `adding`/`removing`/`putting`/`replacingAt`.

### Cited Findings
- "Each main collection type has a read-only interface, such as `List`, and a corresponding mutable interface, such as `MutableList`. Read-only interfaces provide operations for accessing elements, while mutable interfaces add operations for adding, removing, and updating them." "…an immutable collection doesn't allow you to change its elements after creation. For immutable and persistent implementations, use the `kotlinx-collections-immutable` library." — [Kotlin docs: Collections overview](https://kotlinlang.org/docs/collections-overview.html)
- stdlib source: `public fun <T> listOf(vararg elements: T): List<T> = if (elements.size > 0) elements.asList() else emptyList()` (docs say "a new read-only list"). On the JVM, `listOf(element: T) = java.util.Collections.singletonList(element)`. `setOf(vararg)` = `elements.toSet()` — [Collections.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/collections/Collections.kt); [CollectionsJVM.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/src/kotlin/collections/CollectionsJVM.kt); [Sets.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/collections/Sets.kt)
- [Local] Runtime classes and behaviour in 2.4.21:
  - `listOf(1,2,3)` → `java.util.Arrays$ArrayList`. `(it as MutableList<Int>)[0] = 99` **succeeds** and the "read-only" list now prints `[99, 2, 3]`. `.add(4)` throws `UnsupportedOperationException`.
  - `listOf(1)` → `java.util.Collections$SingletonList`. `emptyList()` → `kotlin.collections.EmptyList`. `mutableListOf()`, `.map{}` and `.toList()` → `java.util.ArrayList`.
  - `buildList { … }` → `kotlin.collections.builders.ListBuilder`. Casting the result to `MutableList` and calling `add` throws `UnsupportedOperationException` (frozen after build).
  - A read-only view tracks its backing list: `val backing = mutableListOf("a"); val view: List<String> = backing; backing.add("b")` makes `view` print `[a, b]`.
- Data classes: the compiler derives `equals()`/`hashCode()`, `toString()`, `componentN()` and `copy()` from primary-constructor properties only. "The `copy()` function creates a shallow copy of the instance. In other words, it doesn't copy components recursively. As a result, references to other objects are shared." — [Kotlin docs: Data classes](https://kotlinlang.org/docs/data-classes.html)
- [Local] `data class Payment(val id: String, val amount: BigDecimal, val tags: MutableList<String>)`. Then `p2 = p1.copy(id = "p2"); p2.tags.add("refund")` makes `p1.tags` print `[card, refund]`, and `p1.tags === p2.tags` is true. `val` properties compile to `private final` fields (`private final java.lang.String id;` etc.). Also: `Payment("x", BigDecimal("10.00"), …) == Payment("x", BigDecimal("10.0"), …)` is **false**, because `BigDecimal.equals` compares scale. That is a real payments pitfall for value equality.
- kotlinx.collections.immutable:
  - README: a "Kotlin Alpha" stability badge, and "Note that the library is experimental and the API is subject to change." Latest version shown is 0.5.2. It requires Kotlin stdlib 2.3.0+. Platforms: JVM, JS, wasmJs, wasmWasi and all Kotlin/Native targets. — [GitHub: Kotlin/kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable)
  - Interface hierarchy: `ImmutableList/Set/Map/Collection` extend the read-only Kotlin interfaces. `PersistentList/Set/Map` extend those. `PersistentList.Builder` etc. extend the mutable interfaces. Factories: `persistentListOf`, `persistentSetOf`/`persistentMapOf` (insertion-ordered), `persistentHashSetOf`/`persistentHashMapOf` (unordered, faster), `toImmutableList()`, `toPersistentList()`, and `mutate { }` (replaces `builder().apply { … }.build()`). — [README](https://github.com/Kotlin/kotlinx.collections.immutable)
  - The design doc: immutable collections "specify by their contract the real immutability of their implementors". Persistent collections "provide efficient modification operations that return new instances… The returned collections can share parts of data structure with the original persistent collections." — [docs/proposal.md](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/docs/proposal.md)
  - CHANGELOG: **0.5.0-beta01** "Renamed copy-returning methods on `PersistentCollection`, `PersistentList`, and `PersistentMap` from imperative to participial forms (`add`/`remove`/`put`/`clear`/`set`/`removeAt`/… → `adding`/`removing`/`putting`/`cleared`/`replacingAt`/`removingAt`/…) per KEEP-0459 and deprecated the original names". It also enabled `-Xreturn-value-checker=full` and updated Kotlin to 2.3.0. **0.5.0** "Promoted 0.5.0-beta01 to stable; no API or behavior changes". 0.5.1 and 0.5.2 are bug-fix releases (0.5.1 adds a JPMS module descriptor). — [CHANGELOG.md](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md)
  - Maven Central lists 0.5.2 as the newest version, with metadata lastUpdated 2026-08-28 — [maven-metadata.xml](https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-collections-immutable/maven-metadata.xml)
  - [Local, 0.5.2 jar] `PersistentList` declares both `adding(E)` and the deprecated `add(E)`, plus `addingAll`, `addingAt`, `replacingAt`, `set`, `removingAt` and `builder()`. Extension functions include `mutate(PersistentList, (MutableList) -> Unit)` and `plus(PersistentList, E)` (`+`).
- KEEP-0459, "Naming conventions for copy-returning and in-place-mutating operations" (status: **Draft**, author Dmitry Nekrasov, applied in kotlinx-collections-immutable). Imperative verbs mutate in place (`reverse()`, `sort()`); participles return a copy (`reversed()`, `sorted()`, and now `adding`/`putting`). It names the bug pattern "writing `persistentList.add(x)` and silently discarding the result". — [KEEP-0459](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0459-naming-conventions-for-copy-returning-operations.md)

### Inferences
- **Concurrency.** An object whose state cannot change after construction can be shared between threads with no locks: no torn reads and no lost updates. The only writes happen in the constructor, and `val` compiles to a `final` field, which gets the JMM's final-field safe-publication guarantee. Tie this to the course's JMM track. Persistent collections let one thread "add" while others keep reading the old version safely (copy-on-write without copying everything). The [Local] race demo is the counterexample: a captured `var` is a plain `Ref` field shared by threads, and updates were lost.
- **"Truly immutable" needs three layers.** (1) `val` properties; (2) property types that are themselves immutable (`String`, `BigDecimal`, `Instant`, other immutable data classes, `ImmutableList`), not `MutableList` or arrays; (3) no leaking of mutable internals. A `List<T>` property backed by an `ArrayList` that the class still holds is not immutable. The read-only interface communicates *intent*, not a guarantee.
- **Payments pattern.** `data class Ledger(val entries: PersistentList<Entry>, val balance: Money)` with `fun Ledger.post(e: Entry): Ledger = copy(entries = entries.adding(e), balance = balance + e.amount)`. Every post returns a new ledger value, and old versions stay valid (good for audit, undo, and the "before" state in a test).
- Defensive copy at boundaries: `toList()` returns a new `ArrayList` [Local]. That is a snapshot, but its static type is read-only and not enforced. `toImmutableList()`/`toPersistentList()` encode the guarantee in the type.

### Gaps
- I did not fetch the official stability page to learn what "Alpha" implies for kotlinx.collections.immutable 0.5.x. The README badge and the "0.5.0 stable" release wording disagree: the README says experimental/Alpha, while the changelog calls 0.5.0 the promotion of a beta "to stable". **Flag this to lesson writers: present it as "pre-1.0, Alpha-labelled, API renamed in 0.5"**.
- I found no benchmark numbers comparing persistent and `ArrayList` copy costs.
- The Effective Kotlin item "Limit mutability" (kt.academy) was blocked, so I could not quote Moskała.

---

## 7. Expressions over statements

### Takeaway
In Kotlin, `if`, `when` and `try` are **expressions**: they produce a value. That lets you write `val fee = when { … }` instead of declaring a `var` and assigning it in branches. Combine that with single-expression functions (`fun f(x) = …`) and the `Nothing` type for `throw`, and most business logic can be written as values flowing through expressions with no reassignment.

### Cited Findings
- "You can also write `if` as an expression, which lets you assign its returned value directly to a variable. In this form, an `else` branch is required. The `if` expression serves the same purpose as the ternary operator (`condition ? then : else`) found in other languages." Block branches yield their last expression. — [Kotlin docs: Conditions and loops](https://kotlinlang.org/docs/control-flow.html)
- `when` can be an expression or a statement. "If you use `when` as an expression, you must cover all possible cases… If you don't cover all cases, the compiler throws an error." With a subject of type `Boolean`, enum, sealed class (or their nullable versions), you can cover every case without `else`. "If your `when` expression doesn't have a subject, you must have an `else` branch". Guard conditions (`is X if cond ->`) need a subject. Version note: on **JVM 21+** targets, "the compiler generates an `invokedynamic` instruction for eligible `when` expressions" (excluding those with guards). — [control-flow.html](https://kotlinlang.org/docs/control-flow.html)
- `try` as an expression: "The returned value of a `try` expression is determined by the last executed expression in either the `try` or `catch` block… The `finally` block is always executed, but it doesn't change the result". `throw` has type `Nothing`, a subtype of every type, so `val s: String = person.name ?: fail("Name required")` type-checks. "Kotlin treats all exceptions as unchecked by default." — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- Single-expression functions: "When the function body consists of a single expression, you can omit the curly braces and specify the body after an `=` symbol". Return types are inferred for them, but recursive functions need an explicit return type. — [functions.html](https://kotlinlang.org/docs/functions.html)
- [Local] `val fee = when { p1.amount > BigDecimal("100") -> BigDecimal("1.00"); else -> BigDecimal("0.30") }` gives `0.30`. `val parsed = try { "12x".toInt() } catch (e: NumberFormatException) { -1 }` gives `-1`. A lambda typed `() -> Unit = { 42 }` returns `kotlin.Unit`, and the compiler warns `expression is unused`.

### Inferences
- Statement style (Java habit):
  `var status: Status; if (resp.code == 200) status = APPROVED else if (resp.code == 402) status = DECLINED else status = ERROR`
  Expression style:
  `val status = when (resp.code) { 200 -> APPROVED; 402 -> DECLINED; else -> ERROR }`
  The expression version can't be left unassigned, can't be reassigned later, and with a sealed or enum subject the compiler reports a missing case.
- A `sealed interface PaymentResult` with an exhaustive `when` is the FP-style replacement for nullable sentinels and exception-driven flow. This bridges to later lessons on algebraic data types and `Either`/`Result`.
- Version-specific: the `when` → `invokedynamic` lowering only applies when targeting JVM 21+. The course uses JDK 21-25, so it applies, but it is an implementation detail and should not be taught as semantics.

### Gaps
- The control-flow page gives no Kotlin version for the `when`-on-JVM-21 `invokedynamic` lowering, or for guard conditions becoming stable. I did not look these up in the release notes.

---

## Verified URLs

**Fetched successfully in this session (content read):**
- https://kotlinlang.org/docs/whatsnew20.html: lambdas via invokedynamic by default; limitations; `@JvmSerializableLambda`; `-Xlambdas=class`; 2.0 smart casts
- https://kotlinlang.org/docs/whatsnew15.html: SAM via indy (`LambdaMetafactory.metafactory`, `-Xsam-conversions=class`); experimental `-Xlambdas=indy`
- https://kotlinlang.org/docs/lambdas.html: function types, receivers, nullable function types, references, lambdas, anonymous functions, closures
- https://kotlinlang.org/docs/inline-functions.html: inline, noinline, crossinline, non-local returns, reified, `@PublishedApi`
- https://kotlinlang.org/docs/functions.html: tailrec rules; single-expression functions; default arguments; local functions
- https://kotlinlang.org/spec/declarations.html: spec text on tail recursion optimization (fetched with curl)
- https://kotlinlang.org/docs/collections-overview.html: read-only vs mutable vs immutable
- https://kotlinlang.org/docs/data-classes.html: generated members; `copy()` is shallow
- https://kotlinlang.org/docs/control-flow.html: `if`/`when` as expressions; exhaustiveness; JVM 21 `when` indy
- https://kotlinlang.org/docs/exceptions.html: `try` as expression; `Nothing`; unchecked exceptions
- https://github.com/Kotlin/kotlinx.collections.immutable: README, Alpha badge, 0.5.2, API overview
- https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md: 0.5.x changes and renames (raw file fetched)
- https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/docs/proposal.md: immutable vs persistent definitions (raw)
- https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0459-naming-conventions-for-copy-returning-operations.md: KEEP-0459, Draft (raw)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/collections/Collections.kt: `listOf(vararg)` (raw; master branch)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/src/kotlin/collections/CollectionsJVM.kt: `listOf(element)` = `singletonList` (raw)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/collections/Sets.kt: `setOf` (raw)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/runtime/kotlin/jvm/internal/Ref.java: `IntRef.element` / `ObjectRef.element` plain fields (raw)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/common/src/generated/_Collections.kt: inline `fold` (raw)
- https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-collections-immutable/maven-metadata.xml: versions up to 0.5.2
- https://repo1.maven.org/maven2/io/arrow-kt/arrow-functions/maven-metadata.xml and https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/maven-metadata.xml: Arrow 2.3.0 latest; jars `arrow-functions-jvm-2.3.0.jar` and `arrow-core-jvm-2.3.0.jar` downloaded and inspected with javap
- https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-collections-immutable-jvm/0.5.2/: jar downloaded and inspected with javap

**Surfaced in search results only (not fetched; used for citation details / secondary summaries):**
- https://tildes.net/~comp/ebn/boundaries_a_talk_by_gary_bernhardt_from_scna_2012
- https://elixirforum.com/t/boundaries-by-gary-bernhardt-ruby-conf-2012/13145
- https://waggertron.github.io/tech-learning/topics/cs/functional-core-imperative-shell/
- https://kyle.au/notes/technology/development/functional-core-imperative-shell-pattern
- https://research.chalmers.se/publication/224566 ("How functional programming mattered", for the Hughes paper history)
- https://old.arrow-kt.io/docs/0.12/apidocs/arrow-core-data/arrow.core/-and-then/compose.html
- https://slack-chats.kotlinlang.org/t/498208/is-there-a-reason-compose-andthen-etc-don-t-support-composin

**Blocked by this session's network (could not verify; re-check before citing in a lesson):**
- https://www.destroyallsoftware.com/talks/boundaries
- https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell
- https://www.cse.chalmers.se/~rjmh/Papers/whyfp.pdf (and the mirror https://www.infosun.fim.uni-passau.de/cl/lehre/funcprog05/whyfp.html)
- https://www.manning.com/books/functional-programming-in-kotlin
- https://arrow-kt.io/learn/collections-functions/utils
- https://kt.academy/article/ek-mutability (Effective Kotlin, "Limit mutability")
- https://en.wikipedia.org/wiki/Pure_function, https://blog.acolyer.org/2016/09/14/why-functional-programming-matters/

**Local verification setup (reproducible):** `java -cp <kotlin-compiler-embeddable-2.4.21.jar:kotlin-stdlib-2.4.21.jar:kotlin-script-runtime-2.4.21.jar:kotlin-reflect-2.4.21.jar:kotlin-daemon-embeddable-2.4.21.jar:kotlinx-coroutines-core-jvm-1.8.0.jar:annotations-23.0.0.jar> org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath kotlin-stdlib-2.4.21.jar -jvm-target 21 -d out *.kt`. All jars come from `~/.gradle/caches/modules-2/files-2.1/`. JDK: OpenJDK 21.0.12. Inspection: `javap -c -p -v`.

---

## Teaching notes

### Misconceptions to address explicitly
1. **"`val` means immutable."** No. `val payments = mutableListOf<Payment>()` can't be reassigned, but `payments.add(…)` works. `val` only fixes the reference. At the bytecode level, a `val` property is a `final` field [Local].
2. **"`List<T>` is an immutable list."** It is a read-only *view*. `listOf(1,2,3)` is a `java.util.Arrays$ArrayList`, and `(list as MutableList)[0] = 99` succeeds [Local]. A read-only reference to a `MutableList` sees every later change [Local].
3. **"`copy()` makes an independent copy."** It is shallow: nested `MutableList`s are shared [Docs + Local].
4. **"Kotlin 2 compiles every function value with invokedynamic."** Only lambdas, anonymous functions and SAM conversions do. Callable references (`::f`, `obj::m`, `::Ctor`, `String::length`) still generate `FunctionReferenceImpl` / `PropertyReference1Impl` classes in 2.4.21 unless inlined. `suspend` lambdas and `@JvmSerializableLambda` are classes too [Local].
5. **"`String::length` is a method reference like Java's."** It is a *property* reference (`PropertyReference1Impl`) [Local].
6. **"Lambdas always allocate" / "lambdas are free."** Both are wrong. A non-capturing lambda is one cached instance (`===` true). A capturing one allocates each time (`===` false). A lambda passed to an `inline` HOF disappears completely [Local]. Primitives box through `Function1<Integer,Integer>` [Local].
7. **"A captured `var` is shared safely."** It becomes a `Ref$IntRef`/`LongRef` with a plain, non-volatile field. Concurrent `+=` loses updates [Source + Local: 778714 of 1000000 in one of three runs].
8. **"`tailrec` makes my recursion stack-safe."** Only when every recursive call is a self-call in tail position, outside `try`/`catch`/`finally`, in a non-open function. Otherwise you get only a *warning*, and the code still overflows [Docs + Spec + Local].
9. **"`return` in a lambda returns from the lambda."** A bare `return` returns from the enclosing `fun`, and is only legal when the lambda is inlined. Use `return@label` or an anonymous function [Docs].
10. **"Lambda `toString()` shows its type."** Not since 2.0. It shows `…$$Lambda/0x…@hash` [Docs + Local].
11. **"Functional programming means no state or I/O anywhere."** FCIS pushes state and I/O to a thin shell. The program still does I/O; the decisions are pure [Bernhardt via secondary sources].
12. **"Persistent collections copy everything on each change."** They share structure with the previous version [proposal.md]. The opposite bug is real: `persistentList.add(x)` with the result thrown away does nothing, which is why 0.5 renamed it to `adding` [CHANGELOG + KEEP-0459].
13. **"Data class equality is safe for money."** `BigDecimal("10.00") != BigDecimal("10.0")` makes two otherwise identical `Payment`s unequal [Local]. Normalise the scale or use a `Money` value type.
14. **"Kotlin has `compose` built in."** It doesn't. `f andThen g` gives `unresolved reference 'andThen'` [Local].

### Demo ideas with expected outcomes (all verified locally with 2.4.21 unless noted)
- **D1. What does a lambda become?** Compile `fun nonCapturing(): (Int) -> Int = { it + 1 }` and `fun topRef(): (Int) -> Int = ::addFee`, then list the output directory. *Expected:* no class file for the lambda; a `LambdasKt$topRef$1.class` for the reference. `javap -c` shows `invokedynamic … Function1` vs `getstatic LambdasKt$topRef$1.INSTANCE`. `javap -v` BootstrapMethods shows `LambdaMetafactory.metafactory` with impl `nonCapturing$lambda$0:(I)I`. Recompile with `-Xlambdas=class`. *Expected:* `LambdasKt$nonCapturing$1.class` appears.
- **D2. Instance identity.** `println(nonCapturing() === nonCapturing())` prints **true**. `fun cap(fee: Int): (Int)->Int = { it + fee }`: `cap(3) === cap(3)` prints **false**, and so does `cap(3) == cap(3)`. Unbound `::inc` twice: `===` **true**.
- **D3. The Ref box.** `fun capturingVar(): () -> Int { var count = 0; val inc = { count += 1; count }; inc(); return inc }` and `capturingVar()()` prints **2**. `javap -c` shows `new kotlin/jvm/internal/Ref$IntRef` and `getfield/putfield Ref$IntRef.element`. Then rewrite with `inline fun` + `forEach`. *Expected:* no `Ref$IntRef` and no `invokedynamic` in that method.
- **D4. Lost updates through a captured var.** `var total = 0L`; 4 tasks on `Executors.newFixedThreadPool(4)`, each running `repeat(250_000) { total += 1 }`. *Expected:* sometimes < 1,000,000 (observed 778,714 in run 1 of 3; runs 2-3 hit 1,000,000). Run it in a loop of 5-10 so the race shows reliably. Contrast with `txns.fold(0L) { acc, t -> acc + t.amountCents }` → always 1,000,000.
- **D5. `tailrec` = `goto`.** `tailrec fun gcd(a: Long, b: Long): Long = if (b == 0L) a else gcd(b, a % b)` and `javap -c` show `goto 0` and no `invokestatic gcd`. `tailrec fun sumTo(n: Long, acc: Long = 0)`: `sumTo(1_000_000)` = `500000500000`. The naive `n + sumToNaive(n-1)` throws `StackOverflowError` (with `-Xss512k`; at the default stack size, 1,000,000 frames should also overflow, but that was not separately tested).
- **D6. Misplaced `tailrec` still compiles.** `tailrec fun notTail(n: Long): Long = if (n == 0L) 0 else n + notTail(n - 1)` gives two warnings ("no tail calls are found", "recursive call is not a tail call") and the bytecode keeps `invokestatic notTail`. Inside `try`: "tail recursion optimization inside try/catch/finally is not supported."
- **D7. Read-only is not immutable.** `val ro = listOf(1,2,3); (ro as MutableList<Int>)[0] = 99; println(ro)` prints `[99, 2, 3]`, and `ro.add(4)` (via the cast) throws `UnsupportedOperationException`. `println(ro.javaClass.name)` prints `java.util.Arrays$ArrayList`. By contrast, the result of `buildList { … }` cast to `MutableList` throws on `add`.
- **D8. Shallow copy.** `data class Payment(val id: String, val amount: BigDecimal, val tags: MutableList<String>)`; `p1.copy(id = "p2").tags.add("refund")` → `p1.tags == [card, refund]`, and `p1.tags === p2.tags` is true.
- **D9. Referential transparency, the double charge.** Pseudocode for the whiteboard (not compiled): `val c = charge(card, 10); listOf(c, c)` vs `listOf(charge(card, 10), charge(card, 10))`. Count PSP calls with a fake: 1 vs 2. Then show `fee(10) + fee(10)` == `val f = fee(10); f + f` for a pure `fee`.
- **D10. No compose in stdlib.** `val h = f andThen g` gives `error: unresolved reference 'andThen' on receiver of type '(Int) -> Int'`. Add the 1-line infix extension and it compiles.

### Exercise ideas
- **E1. Extract the functional core.** Given `class SettlementService(val repo, val psp, val clock) { fun settle(id) { … reads clock, branches on 5 rules, writes repo, calls psp … } }`, extract `fun decide(payment: Payment, now: Instant, rules: FeeRules): SettlementDecision` (pure). Lab tests then cover all 5 branches with plain values, no mocks. A single shell test checks the wiring.
- **E2. Write `andThen`/`compose`** as infix extensions, then build `val pricing = addVat andThen applyDiscount andThen roundToCents`. Test that `compose` order is reversed. Bonus: `fun <T> pipeline(steps: List<(T) -> T>): (T) -> T = steps.fold({ it }) { acc, f -> acc andThen f }`.
- **E3. Currying vs Kotlin idioms.** Write `curried()` and `partial()` for `(A, B) -> C`. Apply them to `fun fee(tier: Tier, amount: Money): Money`. Then rewrite the call sites using a bound reference, a lambda and a default argument, and discuss which reads best.
- **E4. Recursion three ways.** Sum a `List<LedgerEntry>`: (a) naive recursion (watch it overflow at 100k–1M entries), (b) `tailrec` with an index and an accumulator, (c) `fold`/`sumOf`. Then use `javap` to show that (b) and (c) are both loops.
- **E5. An immutable ledger.** Write `data class Ledger(val entries: PersistentList<Entry>, val balance: Money)` with `fun post(e: Entry): Ledger` using `copy` + `adding`. Test that the old ledger value is unchanged after posting. Then use `mutate { }` for a batch of posts. (Use kotlinx-collections-immutable 0.5.2 and the new participial names.)
- **E6. Predict the bytecode (quiz).** For each snippet, does it compile to (a) invokedynamic, (b) a generated class, or (c) nothing (inlined)? `{ it + 1 }` → a; `::addFee` → b; `list.map(::addFee)` → c; `list.forEach { total += it }` → c (and no Ref); `Runnable { }` → a; `suspend { 42 }` → b; `account::canPay` → b (a new instance each time); `String::length` → b (a *property* reference).
- **E7. Statements to expressions.** Refactor a Java-style `var status; if/else if/else` and a `try`/`catch` that sets a `var` into `val status = when (code) { … }` and `val parsed = try { … } catch (…) { … }`. Then convert the result type to a `sealed interface` so that the `when` needs no `else`, and show that adding a new subtype breaks compilation until it is handled.

### Notes for the lesson writer
- Version anchors to state in lessons: lambdas via indy became the **default in Kotlin 2.0.0** (opt-in since 1.5.0). SAM conversions via indy since **1.5.0**. kotlinx.collections.immutable **0.5.x renamed** its copy-returning methods (KEEP-0459, Draft). Arrow's function utilities live in **`arrow-functions` 2.3.0**, not in `arrow-core`. On JVM 21+ targets, eligible `when` expressions also use indy (version not documented on that page).
- The local experiments used `-jvm-target 21` on JDK 21.0.12. Nothing in the lambda, reference or tailrec output should change on JDK 25 because the compiler decides it, but that was not separately tested.
- Bernhardt and Hughes quotes in these notes came through secondary sources or memory because their hosts were blocked. Re-check the wording before putting quotation marks in a lesson.
