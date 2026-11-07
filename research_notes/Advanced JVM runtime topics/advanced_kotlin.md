# Advanced Kotlin Language Features on the JVM (Kotlin 2.4.21, November 2026)

Scope: the six lessons on inline functions, value classes, delegation, type-safe DSLs, contracts with context parameters, and compiler plugins (all-open, no-arg, kotlinx.serialization, KSP and kapt). The learner is a senior backend engineer who writes Kotlin daily on Quarkus and has finished generics, variance, reified types and `KClass`. Those facts are in `/home/user/jvm-workbench/research_notes/JVM concurrency course research/kotlin_generics.md` and are not repeated here.

How the facts were checked:
- Everything marked **[observed 2.4.21]** comes from a real run in this session:
  - Compiler: `kotlinc-jvm 2.4.21 (JRE 21.0.12.1+1-1-24.04.4-Ubuntu)`, run as `org.jetbrains.kotlin.cli.jvm.K2JVMCompiler` from `org.jetbrains.kotlin:kotlin-compiler:2.4.21` on Maven Central.
  - Compiler plugins: `kotlin-serialization-compiler-plugin`, `kotlin-allopen-compiler-plugin` and `kotlin-noarg-compiler-plugin`, all 2.4.21, passed with `-Xplugin=`.
  - Libraries: `kotlinx-serialization-core-jvm` and `-json-jvm` 1.12.0, and `junit-platform-console-standalone` 6.1.3.
  - Bytecode was read with `javap` from JDK 21. Each such fact cites the compiler artifact: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/).
- Version-specific facts carry a version tag such as **[2.2.0]**.
- **UNVERIFIED** marks anything not confirmed by a fetched page or a run.
- Release dates and versions:
  - Released: 2.3.0 on December 16, 2025; 2.3.20 on March 16, 2026; 2.4.0 on July 14, 2026; 2.4.20 on September 7, 2026 — [whatsnew23](https://kotlinlang.org/docs/whatsnew23.html), [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html), [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html), [whatsnew2420](https://kotlinlang.org/docs/whatsnew2420.html)
  - Maven Central lists these stable `kotlin-compiler` versions: 2.2.0, 2.2.10, 2.2.20, 2.2.21, 2.3.0, 2.3.10, 2.3.20, 2.3.21, 2.4.0, 2.4.10, 2.4.20, 2.4.21 — [maven-metadata.xml](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/maven-metadata.xml)
- The scratch sources for every demo are in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/ex/` and `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/akt/`. That location is temporary, so the essential code is reproduced below.
- Command-line plugin syntax used, for lesson writers who demo with plain `kotlinc`:
  - `-Xplugin=<path>/kotlin-allopen-compiler-plugin-2.4.21.jar -P plugin:org.jetbrains.kotlin.allopen:preset=spring`
  - `-P plugin:org.jetbrains.kotlin.allopen:annotation=<FQN>`
  - `-P plugin:org.jetbrains.kotlin.noarg:preset=jpa`
  - `-P plugin:org.jetbrains.kotlin.noarg:invokeInitializers=true`
  - The plugin id string `org.jetbrains.kotlin.allopen` and the option names `annotation` and `preset` were read from the plugin classes — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)

## Core facts by lesson topic (reference for all 6 lessons)

### Takeaway
In 2.4.x, context parameters, explicit backing fields and the annotation use-site target changes are Stable. Guard conditions, multi-dollar interpolation and non-local `break`/`continue` have been Stable since 2.2.0, and nested type aliases since 2.3.0. Contracts are still Experimental: you need `@OptIn(ExperimentalContracts::class)`, and the extended contracts also need `ExperimentalExtendedContracts`. `@JvmExposeBoxed` is still Experimental and needs `@OptIn(ExperimentalStdlibApi::class)`. Value classes still allow exactly one field on the JVM. Every claim below was checked against the official docs, the KEEPs or a real 2.4.21 compile.

### Cited Findings

#### Lesson 1: Inline functions
- **Why inlining exists.**
  - The docs: "each function is an object, and it captures a closure… Memory allocations (both for function objects and classes) and virtual calls introduce runtime overhead." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - "The inline modifier affects both the function itself and the lambdas passed to it: all of those will be inlined into the call site." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - The cost, also from the docs: "Inlining may cause the generated code to grow. However, if you do it in a reasonable way (avoiding inlining large functions), it will pay off in performance, especially at 'megamorphic' call-sites inside loops." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **What it does to bytecode** [observed 2.4.21]:
  - A non-inline higher-order call compiles to `invokedynamic … invoke:(I)Lkotlin/jvm/functions/Function0;`, which captures `x`. Then comes `invokestatic measureNotInline(String, Function0)`, and then `checkcast java/lang/Number; invokevirtual Number.intValue()`, which unboxes the generic `T` result.
  - The inline call site has no `invokedynamic` and no `Function0`. The lambda body `x * 2` appears directly as `iload_0; iconst_2; imul` inside the caller.
  - The inline function's `try/finally` printing code was copied twice into the caller: once for the normal path and once for the exception path. That is real code growth.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Non-local return becomes a plain `ireturn`** [observed 2.4.21]:
  - `ints.forEach { if (it == 0) return true }` inside `hasZeros` compiles to an `Iterable.iterator()`/`hasNext`/`next` loop.
  - It contains `iconst_1; ireturn` directly in `hasZeros`.
  - No lambda object is created.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **`noinline`**: "Inlinable lambdas can only be called inside inline functions or passed as inlinable arguments. noinline lambdas, however, can be manipulated in any way you like, including being stored in fields or passed around." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **The NOTHING_TO_INLINE warning.**
  - The docs: "If an inline function has no inlinable function parameters and no reified type parameters, the compiler will issue a warning… (you can use the @Suppress("NOTHING_TO_INLINE") annotation…)" — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - The real 2.4.21 text: `warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.` — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Non-local returns and `crossinline`.**
  - A bare `return` in a lambda is forbidden unless the lambda is passed to an inline function. Such returns "are called non-local returns". — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - "some inline functions may call the lambdas passed to them as parameters not directly from the function body, but from another execution context, such as a local object or a nested function. In such cases, non-local control flow is also not allowed in the lambdas. To indicate that the lambda parameter of the inline function cannot use non-local returns, mark the lambda parameter with the crossinline modifier" — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **Non-local `break`/`continue`** inside lambdas passed to inline functions is Stable since 2.2.0. — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html); [Language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html) ("Non-local break and continue … Available since: 2.2.0 … Stable")
- **Inline properties**: "The inline modifier can be used on accessors of properties that don't have backing fields." It works on an individual accessor or on the whole property. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **Public-API inline rule and `@PublishedApi`.**
  - "public API inline functions are not allowed to use non-public-API declarations, i.e. private and internal declarations and their parts, in their bodies. An internal declaration can be annotated with @PublishedApi, which allows its use in public API inline functions. When an internal inline function is marked as @PublishedApi, its body is checked too, as if it were public." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - Real errors [observed 2.4.21]: `public-API inline function cannot access non-public-API function.` and `public-API inline property accessor cannot access non-public-API property.` — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Restrictions hit in 2.4.21** [observed 2.4.21]:
  - `inline function 'fun rec(n: Int): Int' cannot be recursive.`
  - `local functions are not yet supported in inline functions.`
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Public inline bodies are part of the ABI** [observed 2.4.21]:
  - A client was compiled against library v1, where `inline fun greeting() = "v1"` and `fun plainGreeting() = "v1"`.
  - Both were changed to `"v2"` and the library was recompiled. The old client binary then printed `inline=v1 plain=v2`.
  - The docs warn of exactly this: "risks of binary incompatibility … in case the calling module is not re-compiled". — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/); [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **Inline + reified in one line**: `reified` works only because the body is copied to each call site, where the concrete type argument is known. Normal functions "cannot have reified parameters". Details are in `kotlin_generics.md`. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)

#### Lesson 2: Value classes
- **Declaration rules.**
  - The class must be `@JvmInline value class X(val p: T)` on the JVM, and "An inline class must have a single property initialized in the primary constructor".
  - `init` blocks, secondary constructors, functions and computed properties are allowed.
  - Properties in the body "cannot have backing fields … (no lateinit/delegated properties)".
  - Value classes may implement interfaces, cannot extend classes, and "are always final".
  - Source: [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
- **Boxing rule**: "As a rule of thumb, inline classes are boxed whenever they are used as another type."
  - The docs list these cases: `asGeneric(f)` "boxed: used as generic type T", `asInterface(f)` "boxed: used as type I", and `asNullable(f)` "boxed: used as Foo?, which is different from Foo".
  - Passing through `id(x: T): T` boxes and then unboxes.
  - Referential equality is prohibited.
  - Source: [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
- **Mangling**: "functions using inline classes are mangled by adding some stable hashcode to the function name… `public final void compute-<hashcode>(int x)`".
  - To call such a function from Java, "manually disable mangling: add the @JvmName annotation".
  - A generic underlying type maps to `Any?` or its upper bound.
  - Source: [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
- **Generated bytecode for `@JvmInline value class Money(val cents: Long) : Priced`** [observed 2.4.21], from `javap -p`:
  - Members of `Money`:
    - Instance members: `private final long cents`, `public final long getCents()`, `private Money(long)` and `public final long unbox-impl()`.
    - Static members: `public static long constructor-impl(long)`, which runs `init` validation; `public static final Money box-impl(long)`; and `public static final boolean equals-impl0(long,long)`.
    - Operator and the `Any` overrides: `public static final long plus-bv5VrIc(long,long)`, `toString-impl(long)`, `hashCode-impl(long)` and `equals-impl(long,Object)`.
  - Top-level functions:
    - `charge(amount: Money)` became `charge-DfepdXk(long)`.
    - `@JvmName("chargeFromJava")` gave `chargeFromJava(long)`.
    - `refund(amount: Money?)` became `refund-Y22K7oY(demo.value.Money)`, a boxed parameter that is still mangled.
    - `identity<T>(x: T)` took a boxed `Money` via `box-impl` at the call site.
    - `describe(p: Priced)` took a boxed value via `box-impl`.
    - `total(List<Money>)` returns a raw `long` and is not mangled. Only value-class parameters trigger mangling.
  - A class `Invoice(val amount: Money)` stores `private final long amount`, has getter `getAmount-vT5tX_U()`, a private `Invoice(long)`, and a synthetic public `Invoice(long, DefaultConstructorMarker)`. Plain Java cannot construct it naturally.
  - `println(m)` boxes, because `println(Any?)` takes `Any?`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **`@JvmExposeBoxed`** [2.2.0, Experimental; unchanged through 2.4.21].
  - "Kotlin 2.2.0 introduces a new experimental annotation: @JvmExposeBoxed." `-Xjvm-expose-boxed` "has the same effect as if every declaration in the module had the @JvmExposeBoxed annotation." — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
  - The interop guide: "Before using the @JvmExposeBoxed annotation in your code, you must opt in by using @OptIn(ExperimentalStdlibApi::class)". It can be applied to a class, a constructor or a function. "doesn't automatically generate boxed representations for inherited functions" (override them to get one). — [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
  - KEEP-0394 status: "Experimental in 2.2". — [KEEP-0394](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0394-jvm-expose-boxed.md)
  - The features page says "Stability level: Experimental … Available since: 2.2.0". — [Language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)
  - [observed 2.4.21] Without the opt-in you get `error: this declaration needs opt-in. Its usage must be marked with '@kotlin.ExperimentalStdlibApi' or '@OptIn(kotlin.ExperimentalStdlibApi::class)'`.
  - With the opt-in, the class gains `public Cents(long)`, a real Java constructor that runs `init`, and a boxed `public final Cents doubled()` next to `doubled-ys1BvwE(long)`. The function gains `pay(Cents)` next to `pay-VYnWypA(long)`.
  - The module-wide `-Xjvm-expose-boxed` flag needed no `@OptIn` in my run. It also gave `Invoice` a `public Invoice(Money)` constructor and a `public final Money getAmount()` getter.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Value class vs type alias**: type aliases "are assignment-compatible with their underlying type… while inline classes are not". — [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
- **Multi-field value classes and Valhalla.**
  - [observed 2.4.21] `@JvmInline value class Point(val x: Int, val y: Int)` gives `error: value class must have exactly one primary constructor parameter.`
  - The internal flag `-XXLanguage:+ValueClasses` is rejected with `warning: unknown language feature 'ValueClasses'`. So 2.4.21 has no multi-field mode, not even an internal one.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
  - The KEEP design notes (status "Under consideration") explain that `@JvmInline` is mandatory now so that non-annotated value classes "in the future Valhalla JVM" can be compiled "using the capabilities of the Project Valhalla". Multi-field value classes (KT-1179) before Valhalla are described as "At this point, this is all theoretical." — [KEEP notes: value classes](https://github.com/Kotlin/KEEP/blob/master/notes/value-classes.md)

#### Lesson 3: Delegation
- **Class delegation.**
  - "The by-clause in the supertype list for Derived indicates that b will be stored internally in objects of Derived and the compiler will generate all the methods of Base that forward to b." — [Delegation](https://kotlinlang.org/docs/delegation.html)
  - Overridden members "do not get called from the members of the delegate object, which can only access its own implementations of the interface members". — [Delegation](https://kotlinlang.org/docs/delegation.html)
- **The override trap** [observed 2.4.21]:
  - `class AuditedMap(inner: MutableMap<String,Int>) : MutableMap<String,Int> by inner` overrides only `put`.
  - After `m["a"] = 1; m.putAll(mapOf("b" to 2, "c" to 3))` the output was `AuditedMap size=3 log=[put a]`. `putAll` went straight to the inner `HashMap` and bypassed the override.
  - The same happened with `CountingSet` that overrides `add`: after `add(1); addAll(listOf(2,3,4))` the output was `size=4 attempts=1`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **The delegate is captured once** [observed 2.4.21]:
  - `class Switchable(var target: Greeter) : Greeter by target` compiles to a hidden `private final Greeter $$delegate_0` next to `private Greeter target`.
  - Reassigning `target` to `Fr()` still printed `hello`.
  - `equals`, `hashCode` and `toString` are not forwarded. A set-delegating class printed `demo.d2.Tags@<hash>`, and two wrappers with the same contents were `equals=false`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Delegated properties: the contract.**
  - The syntax is `val/var <name>: <Type> by <expression>`. A delegate needs `operator fun getValue(thisRef, property: KProperty<*>)`, plus `setValue` for a `var`. These can be members or extensions.
  - `ReadOnlyProperty` and `ReadWriteProperty` let you write delegates as anonymous objects.
  - Source: [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
- **`lazy` and its three modes.**
  - "By default, the evaluation of lazy properties is synchronized: the value is computed only in one thread, but all threads will see the same value." `LazyThreadSafetyMode.PUBLICATION` allows several threads to run the initializer. `NONE` "doesn't incur any thread-safety guarantees and related overhead." — [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - [observed 2.4.21] The classes behind each mode are `kotlin.SynchronizedLazyImpl` (fields `initializer`, `volatile _value`, `lock`; its bytecode contains `monitorenter`), `kotlin.SafePublicationLazyImpl` (a `volatile` initializer and value plus an `AtomicReferenceFieldUpdater`) and `kotlin.UnsafeLazyImpl`.
  - Each `by lazy` property adds one `private final kotlin.Lazy x$delegate` field per instance. The constructor allocates it via `invokedynamic …Function0` plus `LazyKt.lazy(...)`.
  - The getter does `getfield x$delegate; invokeinterface Lazy.getValue()`, and for an `Int` it also unboxes with `checkcast Number; intValue()`.
  - No `$$delegatedProperties` array is generated for `lazy`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **`observable`, `vetoable`, map-backed and delegate-to-property.**
  - The `observable` handler runs "after the assignment has been performed". The `vetoable` handler is called "before the assignment".
  - Map-backed properties use `val name: String by map`, or a `MutableMap` for `var`.
  - Delegating to another property uses `this::delegate` or `::topLevel`, which is useful for deprecating renames.
  - Source: [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - [observed 2.4.21] Output:

    ```
    owner: <none> -> alice
    owner: alice -> bob
    limit after veto: 100
    limit after ok: 50
    ```

    A missing map key fails at access time with `java.util.NoSuchElementException: Key port is missing in the map.` — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **What the compiler generates.**
  - "for the property prop it generates the hidden property prop$delegate, and the code of the accessors simply delegates to this additional property … this::prop is a reflection object of the KProperty type". — [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - The `$delegate` field is omitted for:
    - a referenced property (`by ::impl`);
    - a named object;
    - "A final val property with a backing field and a default getter in the same module";
    - a constant expression, enum entry, `this` or `null`.
  - Source: [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - [observed 2.4.21] `class Order { var status: String by Recorded("NEW"); var note: String by nonBlankName("") }` compiles to:

    ```
    static final kotlin.reflect.KProperty<java.lang.Object>[] $$delegatedProperties;
    private final demo.deleg.Recorded status$delegate;
    private final kotlin.properties.ReadWriteProperty note$delegate;
    public final java.lang.String getStatus();   // getfield status$delegate; getstatic $$delegatedProperties[0]; invokevirtual Recorded.getValue(Object, KProperty); checkcast String
    static {};  // new kotlin/jvm/internal/MutablePropertyReference1Impl(Order.class, "status", "getStatus()Ljava/lang/String;", 0) ...
    ```

    For a map-backed property the field is `private final java.util.Map host$delegate`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **`provideDelegate`.**
  - It is called "to create the additional 'delegate' property", which gives "the necessary validation right away". `PropertyDelegateProvider` creates providers without new classes. — [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - [observed 2.4.21] `binding note` was printed when `Order()` was constructed, which shows the validation runs at construction, not on first access. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lesson 4: Type-safe DSLs
- **The building blocks**: well-named builder functions plus "function literals with receiver". `HTML.() -> Unit` "is a function type with receiver". — [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
- **`@DslMarker`.**
  - "To make the compiler start controlling scopes, you only have to annotate the types of all receivers used in the DSL with the same marker annotation."
  - Markers count only on `CLASS`, `TYPE` (receiver types in function types) and `TYPEALIAS`. "Applying a DSL marker to other targets (such as functions or properties) has no effect".
  - Annotating a common superclass is enough. Outer receivers stay reachable with `this@html.head { }`.
  - Source: [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
- **Real violation errors** [observed 2.4.21]:
  - The two errors:

    ```
    Violation.kt:5:9: error: 'fun payee(block: PartyBuilder.() -> Unit): Unit' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.
    Violation.kt:6:9: error: 'var currency: String' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.
    ```

  - `this@paymentRequest.currency = "GBP"` inside `items { }` compiled.
  - The same code without the marker compiled cleanly and failed at runtime with `java.lang.IllegalArgumentException: iban required`. The misplaced `payee { name = "oops" }` silently built a second party.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Standard library builders** [observed 2.4.21]:
  - `buildString { append("total="); append(req.total) }` gives `total=24.98`.
  - `buildList { add(1); addAll(listOf(2, 3)); if (size == 3) add(4) }` gives `[1, 2, 3, 4]`. The receiver is a `MutableList`, so `size` works inside the block.
  - `buildMap { put("a", 1); put("b", 2) }` gives `{a=1, b=2}`.
  - No library is needed.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **History of context receivers**, the DSL use case that came before context parameters.
  - Introduced in 1.6.20 as a "Prototype of context receivers for Kotlin/JVM": "With -Xcontext-receivers enabled, the compiler will produce pre-release binaries that cannot be used in production code." — [whatsnew1620](https://kotlinlang.org/docs/whatsnew1620.html)
  - KEEP-0259 status: "Superseded by KEEP-0367". — [KEEP-0259](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0259-context-receivers.md)
  - 2.2.0: "Context parameters replace an older experimental feature called context receivers… Specifying both -Xcontext-receivers and -Xcontext-parameters compiler options simultaneously leads to an error." — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
  - 2.3.20, under breaking changes: "Experimental context receivers are no longer supported and are replaced by context parameters." — [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html)
  - [observed 2.4.21] The old syntax `context(Logger) fun hello() = log("hi")` gives `error: context parameters must be named. Use '_' to declare an anonymous context parameter.` and `unresolved reference 'log'`. Passing `-Xcontext-receivers` gives `error: experimental context receivers are superseded by context parameters. Remove the '-Xcontext-receivers' compiler argument and migrate to the new syntax.` — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **DSL markers and context parameters.**
  - KEEP-0367 §7.7: if a contextual X-DSL-marked value is in scope and resolution picks an outer one, "it is a compilation error". — [KEEP-0367](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md)
  - The builders page says a receiver shadowed by a context parameter gives "a warning". — [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
  - [observed 2.4.21] The KEEP's `Cow` example (`with(Cow(..)) { context(Cow(..)) { moo() } }`) is an **error**: `call to 'fun moo(): Unit' defined in 'Cow' uses an implicit receiver shadowed by a context parameter. Make the receiver explicit using 'this' or 'contextOf<Cow>()'.` The docs page and the compiler disagree here; trust the compiler. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lesson 5: Contracts and context parameters
- **What contracts are.**
  - KEEP-139 status: "Experimental in 1.3". "Currently, Kotlin Contracts is a completely compile-time mechanism." "Formal verification is a non-goal". In the prototype, "Compiler trusts contracts unconditionally … programmer is responsible for writing correct and sound contracts".
  - The `contract { }` call "should be the first statement". The effects are `callsInPlace` with `AT_MOST_ONCE`, `EXACTLY_ONCE`, `AT_LEAST_ONCE` and `UNKNOWN`, plus `returns(...) implies ...`.
  - Source: [KEEP-0139](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md)
- **Status in 2.4**: "Kotlin contracts are Experimental. To opt in, add the @OptIn(ExperimentalContracts::class) annotation when declaring a function with a contract." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
  - [observed 2.4.21] Without the opt-in: `error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Extended contracts** [2.2.20]: generic type assertions, contracts in property accessors and some operator functions, `returnsNotNull()` and `holdsIn`.
  - "These improvements are Experimental… you still need to use the @OptIn(ExperimentalContracts::class) annotation… The holdsIn keyword and the returnsNotNull() function also need the @OptIn(ExperimentalExtendedContracts::class) annotation."
  - The 2.2.20 flags were `-Xallow-contracts-on-more-functions`, `-Xallow-condition-implies-returns-contracts` and `-Xallow-holdsin-contract`.
  - Source: [whatsnew2220](https://kotlinlang.org/docs/whatsnew2220.html)
  - [observed 2.4.21] All three flags give `warning: the argument '…' is redundant for the current language version 2.4.` A generic `returns(true) implies (this is Ok<T>)` and `cond holdsIn block` both compile without flags.
  - `returnsNotNull()` without `ExperimentalExtendedContracts` still errors: `this declaration needs opt-in … '@kotlin.contracts.ExperimentalExtendedContracts'`.
  - At `-language-version 2.2` the same `returnsNotNull` code errors with `'kotlin/contracts/ContractBuilder.implies' is not part of the contracts DSL`. It compiles at 2.3 and 2.4.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **`returnsResultOf()`** [2.4.0, Experimental]: added to help the unused-return-value checker. It needs `-Xallow-returns-result-of`, and "using it produces pre-release binaries that earlier Kotlin compiler versions can't read." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
- **Contracts are trusted, not verified** [observed 2.4.21]:
  - A lying `fun PaymentEvent.lyingIsCaptured(): Boolean { contract { returns(true) implies (this@lyingIsCaptured is Captured) }; return true }` compiles with no diagnostic.
  - `if (f.lyingIsCaptured()) println(f.cents)` then crashes at runtime: `java.lang.ClassCastException: class demo.contracts.Failed cannot be cast to class demo.contracts.Captured`.
  - K2 does sanity-check some `callsInPlace` cases, as warnings only:
    - `wrong invocation kind 'EXACTLY_ONCE' for 'block: () -> Unit' specified, the actual invocation kind is 'AT_LEAST_ONCE'.` for a block called twice.
    - `leaked in-place lambda 'block: () -> Unit'.` for a stored lambda.
  - The contract leaves no trace in the method bytecode. `isCaptured` is just `instanceof; ireturn`; the contract is kept in Kotlin metadata.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Why `callsInPlace` matters** [observed 2.4.21]:
  - Without a contract, `val g: String; once { g = "x" }` fails with `error: 'val' cannot be reassigned.` and `error: variable 'g' must be initialized.`
  - With `callsInPlace(block, InvocationKind.EXACTLY_ONCE)` it compiles and prints `hello`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **What context parameters are.**
  - "Context parameters allow functions and properties to declare dependencies that are implicitly available in the surrounding context."
  - Syntax: `context(users: UserService) fun f()`. `_` gives an anonymous context parameter, and `contextOf<T>()` reads one.
  - Values are resolved by type at the call site. "If multiple compatible values exist at the same scope level, the compiler reports an ambiguity".
  - Restrictions: "Constructors can't declare context parameters", "Properties with context parameters can't have backing fields or initializers", and "can't use delegation".
  - Source: [Context parameters](https://kotlinlang.org/docs/context-parameters.html)
- **KEEP-0367** (status "In progress"):
  - Changes from KEEP-259: named context parameters, context receivers dropped, `this@Type` replaced by `contextOf<A>()`, no contexts in constructors, callable references resolve eagerly, and context in classes dropped.
  - JVM representation (§7.11): "a function with additional parameters. In particular, the order is: 1. Context parameters, if present; 2. Extension receiver, if present; 3. Regular value parameters."
  - Source: [KEEP-0367](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md)
- **Status history.**
  - Preview in 2.2.0 with `-Xcontext-parameters`. — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
  - 2.3.20 changed overload resolution: "Previously, overload resolution treated declarations with context parameters as more specific than those without them. Starting with Kotlin 2.3.20, this rule no longer applies". — [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html)
  - Stable in 2.4.0, "except for context arguments and callable references". Explicit context arguments (`sendNotification(emailSender = e)`) are a new Experimental feature behind `-Xexplicit-context-arguments`. — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
  - The features page: "Available since: 2.2.0, Stable since 2.4.0". — [Language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)
- **Real 2.4.21 behaviour** [observed 2.4.21]:
  - It compiles and runs with no flag.
  - `-Xcontext-parameters` gives `warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.`
  - At `-language-version 2.3` with no flag: `error: the feature "context parameters" is only available since language version 2.4` and `to call contextual declarations, specify the '-Xcontext-parameters' compiler option.`
  - Explicit context arguments without the flag: `The feature "explicit context arguments" is only available since language version 2.5`. With `-Xexplicit-context-arguments` they print `email` and `sms`.
  - Callable reference: `callable reference to 'context(l: Logger) fun use(): Unit' is unsupported because it has context parameters.`
  - Ambiguity: `multiple potential context arguments for 'l: Logger' in scope.`
  - Restrictions: `property with context parameters cannot be initialized because it has no backing field.` and `context parameters on primary constructors are unsupported.`
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lesson 6: Compiler plugins
- **all-open.**
  - "makes classes and their members open at compile time without requiring the open keyword."
  - "If a class or any of its superclasses is annotated with a configured annotation, the class and its members become open." Meta-annotations work too.
  - Gradle: `kotlin("plugin.allopen") version "2.4.21"` with `allOpen { annotation("com.example.AllOpenMarker") }`. Maven: `<plugin>all-open</plugin>` and the `kotlin-maven-allopen` dependency.
  - Source: [All-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html)
- **kotlin-spring**: "a preconfigured wrapper around the all-open plugin". The docs list `@Component`, `@Async`, `@Transactional`, `@Cacheable` and `@SpringBootTest`, plus meta-annotated `@Configuration`, `@Controller`, `@RestController`, `@Service` and `@Repository`. — [Kotlin-spring plugin](https://kotlinlang.org/docs/kotlin-spring-plugin.html)
  - The 2.4.21 plugin's `spring` preset also lists `org.springframework.validation.annotation.Validated`, which the docs page omits. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
- **Built-in all-open presets in 2.4.21** [observed 2.4.21], read from `AllOpenPluginNames`:
  - `spring`: `org.springframework.stereotype.Component`, `…transaction.annotation.Transactional`, `…scheduling.annotation.Async`, `…cache.annotation.Cacheable`, `…boot.test.context.SpringBootTest` and `…validation.annotation.Validated`.
  - `quarkus`: only `javax.enterprise.context.ApplicationScoped` and `javax.enterprise.context.RequestScoped`.
  - `micronaut`: `io.micronaut.aop.Around`, `Introduction`, `InterceptorBinding` and `InterceptorBindingDefinitions`.
  - `jpa`: `Entity`, `Embeddable` and `MappedSuperclass` in both the `javax.persistence` and `jakarta.persistence` namespaces.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
- **The Quarkus preset gotcha** [observed 2.4.21]:
  - With `preset=quarkus`, a class annotated with `jakarta.enterprise.context.ApplicationScoped` (the Quarkus 3 namespace) stayed `public final class demo.plug.QuarkusBean` with a `final` `work()`.
  - With `annotation=jakarta.enterprise.context.ApplicationScoped` it became `public class … public java.lang.String work()`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
- **What all-open does not touch** [observed 2.4.21]:
  - A `@Service` class became `public class` with an open `pay()` and an open `getFee()`.
  - `private int secret()` stayed private, and the backing field `private final int fee` stayed final.
  - An unannotated `PlainHelper` stayed `public final class` with a `final` `help()`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
- **no-arg.**
  - It "generates a zero-argument constructor for classes with a specific annotation… annotated with @Deprecated at the HIDDEN level, so you can call it from Java but not from Kotlin."
  - `invokeInitializers` is "disabled by default".
  - Source: [No-arg compiler plugin](https://kotlinlang.org/docs/no-arg-plugin.html)
  - [observed 2.4.21] What the run showed:
    - The generated `public demo.plug.PaymentEntity()` carries `@kotlin.Deprecated(level=HIDDEN, …, message="No-arg constructor is hidden from direct usage")` and `@java.lang.Deprecated`.
    - Kotlin calling `PaymentEntity()` gets `error: no value passed for parameter 'id'.`
    - Through Java reflection, the non-null `var note: String = "default-note"` was `null` without `invokeInitializers`, and `default-note` with `invokeInitializers=true`.
    - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-noarg-compiler-plugin/2.4.21/)
- **kotlin-jpa** [changed in 2.3.20].
  - Before 2.3.20 it applied only no-arg. "Starting with Kotlin 2.3.20 … The Gradle org.jetbrains.kotlin.plugin.jpa plugin automatically applies the org.jetbrains.kotlin.plugin.all-open plugin with the JPA preset enabled". `kotlin-maven-noarg` "now implicitly includes" `kotlin-maven-allopen`.
  - The stated reason: "lazy associations work as expected instead of causing eager loading".
  - Source: [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html); [Kotlin-jpa plugin](https://kotlinlang.org/docs/kotlin-jpa-plugin.html)
- **kotlinx.serialization.**
  - "When you annotate a class with @Serializable, the Kotlin serialization plugin generates a KSerializer for that class", which you get with `.serializer()`. — [Create and use serializers](https://kotlinlang.org/docs/serialization-create-and-use-serializers.html)
  - Gradle: `kotlin("plugin.serialization") version "2.4.21"` plus `org.jetbrains.kotlinx:kotlinx-serialization-json:1.11.0`. That is the docs' version; Maven Central's latest is 1.12.0, which was used here. — [Get started with serialization](https://kotlinlang.org/docs/serialization-get-started.html); [maven-metadata.xml](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlinx/kotlinx-serialization-json-jvm/maven-metadata.xml)
  - JSON is Stable. HOCON, ProtoBuf, CBOR and Properties are Experimental. — [Serialization](https://kotlinlang.org/docs/serialization.html)
  - The kotlinx-serialization component has been Stable since 1.0.0. — [Stability of Kotlin components](https://kotlinlang.org/docs/components-stability.html)
- **Generated code** [observed 2.4.21]:
  - Each class gets `Captured$$serializer implements kotlinx.serialization.internal.GeneratedSerializer<Captured>` with `public static final INSTANCE`, `descriptor`, `serialize`, `deserialize` and `childSerializers()`, plus `Captured$Companion.serializer()`.
  - The sealed interface gets `PaymentEvent$Companion`.
  - Without the plugin, `Captured.serializer()` is `error: unresolved reference 'serializer'.`
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)
- **Polymorphism.**
  - "Kotlin serialization is static by default." For closed polymorphism, make the base a `sealed class` or `sealed interface` and mark every subclass `@Serializable`.
  - The `type` discriminator "is only included if you use the base class as the static type".
  - By default the discriminator value is "the fully qualified class name", so use `@SerialName` for stability.
  - Open polymorphism needs a `SerializersModule`.
  - Source: [Serialize polymorphic classes](https://kotlinlang.org/docs/serialization-polymorphism.html)
- **Json configuration.**
  - Instances "are immutable and thread-safe… Reusing custom Json instances improves performance".
  - `encodeDefaults` is off by default ("the JSON encoder omits default property values").
  - Nulls are encoded by default (`explicitNulls = false` turns that off).
  - "unknown keys … result in an error", unless `ignoreUnknownKeys = true` or the Experimental `@JsonIgnoreUnknownKeys`.
  - `classDiscriminator` can be renamed, and `coerceInputValues` exists.
  - Source: [Customize the Json instance](https://kotlinlang.org/docs/serialization-json-configuration.html)
- **KSP.**
  - "a source code generation framework for Kotlin… KSP-based processors can't examine expressions or statements, and they can't modify the source code." Typical uses are DI (Dagger), serialization (Moshi) and databases (Room). — [KSP overview](https://kotlinlang.org/docs/ksp-overview.html)
  - "Compared to KAPT, annotation processors that use KSP can run up to 2x faster." — [KSP README](https://github.com/google/ksp)
  - KSP2 "is no longer a compiler plugin and is built on the same set of Kotlin compiler APIs shared with IntelliJ IDEA". — [KSP2 doc](https://github.com/google/ksp/blob/main/docs/ksp2.md)
  - KSP 2.3.0: "KSP1 has been deprecated", and "KSP version is no longer tied to the Kotlin compiler version". — [KSP 2.3.0 release](https://github.com/google/ksp/releases/tag/2.3.0)
  - The latest KSP is 2.3.13 (30 Oct), which adds `KSContextParameter`. 2.3.12 added explicit-backing-field support with an opt-in. 2.3.10 "works with Kotlin 2.4.0 default module names". — [KSP releases](https://github.com/google/ksp/releases)
- **kapt.**
  - It "generates stub files from Kotlin source code and then runs the Java annotation processors on those stubs" (MapStruct, Data Binding). — [kapt](https://kotlinlang.org/docs/kapt.html)
  - Migration guide: stubs are "expensive, significantly increases build time, and loses some Kotlin-specific features". — [Migrate from kapt to KSP](https://kotlinlang.org/docs/ksp-kapt-migration.html)
  - kapt, all-open and no-arg are listed as "Stable 1.3.0". — [Stability of Kotlin components](https://kotlinlang.org/docs/components-stability.html)
  - The roadmap lists "Improve KAPT performance to be comparable with Java APT". — [Kotlin roadmap](https://kotlinlang.org/docs/roadmap.html)
  - 2.4.0 adds `includeCompileClasspath`/`kapt.include.compile.classpath` for Maven, with the warning "Annotation processors discovery from compile classpath is deprecated." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)

### Inferences
- For a Quarkus learner, the most practical plugin lesson is to configure explicit `jakarta.*` annotations rather than rely on the built-in `quarkus` all-open preset. In 2.4.21 that preset still matches only `javax.enterprise.context.*`, which is inferred to be stale since Quarkus 3 moved to Jakarta. The Quarkus guide could not be fetched; see Gaps.
- The 2.3.20 change to kotlin-jpa means projects that used to add all-open for `@Entity` by hand can drop that. Older Kotlin versions still need it.
- Contracts are a "trust me" API for library authors. Lesson writers should frame them as a way to state facts the compiler cannot infer. Present the 2.4 `callsInPlace` warnings as linting, not proof.

### Gaps
- The Quarkus Kotlin guide (quarkus.io) is outside the session's allowed network, so the Quarkus-recommended `allOpen` list (e.g. `jakarta.ws.rs.Path`, `io.quarkus.test.junit.QuarkusTest`) is **UNVERIFIED** here.
- It is unknown whether the Gradle `allOpen {}` DSL exposes a `preset("quarkus")` option. I did not check the KGP source.
- KSP's officially supported KGP range for 2.4.x is unclear. The KSP overview page (dated 30 September 2026) says "The latest KSP version, 2.3.10, supports … Kotlin Gradle plugin 2.2.10–2.3.x", while the release notes mention Kotlin 2.4.0 module names. I did not run KSP against KGP 2.4.21.

## Key Question 1: What are the exact statuses in Kotlin 2.2, 2.3 and 2.4 of the features these lessons touch?

### Takeaway
Stabilized in 2.2.0: guard conditions, multi-dollar interpolation and non-local break/continue. Stabilized in 2.3.0: nested type aliases. Stabilized in 2.4.0: context parameters (except explicit context arguments and callable references), explicit backing fields and the annotation use-site target changes. Still Experimental in 2.4.x: contracts (opt-in), extended contracts (a second opt-in, but no `-X` flags at language version 2.3+), `@JvmExposeBoxed` (opt-in), name-based destructuring (needs language version 2.5 semantics), explicit context arguments, collection literals and the unused-return-value checker. Context receivers are gone.

### Cited Findings
Status matrix. "Doc" means the What's new or features page. Each lv cell is what the 2.4.21 compiler reports at `-language-version` 2.2, 2.3 or 2.4 with no flags.

| Feature | 2.2.x | 2.3.x | 2.4.x | 2.4.21 compiler at lv 2.2 / 2.3 / 2.4 |
|---|---|---|---|---|
| Context parameters | Preview, `-Xcontext-parameters` [2.2.0] | Still pre-stable; overload-resolution change [2.3.20] | **Stable** [2.4.0], except explicit context args and callable refs | 2.2 and 2.3: `the feature "context parameters" is only available since language version 2.4`; 2.4: OK; flag is "redundant" |
| Explicit context arguments | n/a | n/a | Experimental, `-Xexplicit-context-arguments` [2.4.0] | without flag: "only available since language version 2.5" |
| Context receivers | Superseded; both flags together is an error [2.2.0] | "no longer supported" [2.3.20] | `-Xcontext-receivers` is an error | error text quoted in Lesson 4 |
| Contracts (`kotlin.contracts`) | Experimental, `@OptIn(ExperimentalContracts::class)` | same | same ("Kotlin contracts are Experimental") [2.4.0] | opt-in error without `@OptIn` |
| Extended contracts (`returnsNotNull`, `holdsIn`, generics, accessors) | Experimental + flags [2.2.20] | — | still need `ExperimentalExtendedContracts` | lv 2.2: `returnsNotNull` not part of the DSL; lv 2.3 and 2.4: OK; flags "redundant" |
| `returnsResultOf()` | n/a | n/a | Experimental, `-Xallow-returns-result-of`, pre-release binaries [2.4.0] | not run |
| `@JvmExposeBoxed` / `-Xjvm-expose-boxed` | Experimental [2.2.0] | (no change found) | (no change found) | `@OptIn(ExperimentalStdlibApi::class)` required for the annotation |
| Guard conditions in `when` | **Stable** [2.2.0] | Stable | Stable | OK at 2.2, 2.3, 2.4 |
| Multi-dollar interpolation | **Stable** [2.2.0] | Stable | Stable | OK at 2.2, 2.3, 2.4 |
| Non-local break/continue | **Stable** [2.2.0] | Stable | Stable | OK at 2.2, 2.3, 2.4 |
| Nested type aliases | Beta, `-Xnested-type-aliases` [2.2.0] | **Stable** [2.3.0] | Stable | lv 2.2: "only available since language version 2.3" |
| Explicit backing fields | n/a | Experimental, `-Xexplicit-backing-fields` [2.3.0] | **Stable** [2.4.0] | lv 2.2 and 2.3: "only available since language version 2.4" |
| `@all` meta-target and new use-site defaulting | Preview, `-Xannotation-target-all` / `-Xannotation-default-target=param-property` [2.2.0] | — | **Stable** [2.4.0] | lv 2.2 and 2.3: "annotation all use site target … since language version 2.4" |
| Context-sensitive resolution | Preview, `-Xcontext-sensitive-resolution` [2.2.0] | "still Experimental" [2.3.0] | not listed as Stable in 2.4.0 | not run |
| Unused return value checker | n/a | Experimental, `-Xreturn-value-checker=check\|full` [2.3.0] | Experimental [2.4.0] | not run |
| Name-based destructuring | n/a | Experimental, `-Xname-based-destructuring=only-syntax\|name-mismatch\|complete` [2.3.20] | Experimental | `(val email, val name) = u` gives "only available since language version 2.5" even at lv 2.4 |
| Collection literals | n/a | n/a | Experimental, `-Xcollection-literals` [2.4.0] | without flag, `[1,2,3]` as a `List` gives a type mismatch |
| Multi-field value classes | not available | not available | not available | `value class must have exactly one primary constructor parameter.` |
| kotlin-jpa applies all-open (JPA preset) | no | **yes from 2.3.20** | yes | preset `jpa` present in the 2.4.21 all-open jar |
| K1 / `-language-version 1.9` | — | — | removed [2.4.0] | not run |
| JVM bytecode target | — | Java 25 [2.3.0] | Java 26 [2.4.0] | not run |

- Context parameters, preview: "Preview of context parameters"; flag `-Xcontext-parameters`; "This feature is planned to be stabilized and improved in future Kotlin releases." — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
- 2.2.0 stabilizations: "This release promotes guard conditions, non-local break and continue, and multi-dollar interpolation to Stable." Nested type aliases: "currently in Beta", flag `-Xnested-type-aliases`. — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
- `@JvmExposeBoxed`: "Kotlin 2.2.0 introduces a new experimental annotation"; flag `-Xjvm-expose-boxed`. — [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)
- 2.3.0 stabilizations: "graduated to Stable in Kotlin 2.3.0: Support for nested type aliases; Data-flow-based exhaustiveness checks for when expressions." Explicit backing fields: "This feature is Experimental", `-Xexplicit-backing-fields`. Unused return value checker: Experimental, `-Xreturn-value-checker=check` / `=full`. — [whatsnew23](https://kotlinlang.org/docs/whatsnew23.html)
- Explicit backing fields syntax [2.3.0, Stable 2.4.0]: `val city: StateFlow<String>` followed by `field = MutableStateFlow("")`. This replaces the `_city` backing-property pattern, with smart casts to the field type inside the private scope. — [whatsnew23](https://kotlinlang.org/docs/whatsnew23.html)
- 2.3.20: context-parameter overload resolution change, name-based destructuring Experimental, JPA preset, context receivers no longer supported. — [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html)
- 2.4.0 stabilizations: "Context parameters, except for context arguments and callable references; @all meta-target for properties; New defaulting rules for use-site annotation targets; Explicit backing fields…" New Experimental features: explicit context arguments, collection literals and improved compile-time constants. "Kotlin contracts are Experimental." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
- The features page confirms the guard, multi-dollar and non-local break/continue statuses: "Available since: 2.2.0 … Stable". Context parameters and explicit backing fields: "Stable since 2.4.0". Expose boxed: "Experimental … Available since: 2.2.0". — [Language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)
- JVM and compiler housekeeping:
  - "Starting with Kotlin 2.3.0, the compiler can generate classes containing Java 25 bytecode." — [whatsnew23](https://kotlinlang.org/docs/whatsnew23.html)
  - "Starting with Kotlin 2.4.0, the compiler can generate classes containing Java 26 bytecode." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
  - "Starting with Kotlin 2.4.0, the compiler no longer supports -language-version=1.9. As a result, the K1 compiler is no longer supported." — [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html)
- 2.4.20 has nothing relevant beyond tooling (`when` via invokedynamic "graduated to Stable and is enabled by default", `kotlinr`, the native-image compiler). The native image bundles the Serialization, All-open and no-arg plugins for `-Xplugin`. — [whatsnew2420](https://kotlinlang.org/docs/whatsnew2420.html)
- All compiler-column results come from `-language-version` runs of the 2.4.21 compiler. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

### Inferences
- In 2.4.21, contract features that were behind `-X` flags in 2.2.20 appear to be enabled by default at language version 2.3 or higher, because the flags are reported redundant and the code compiles at lv 2.3. The 2.3.0 What's new page does not announce this, so lessons should say "enabled by default as of the 2.3 language version (observed), still needs the opt-in annotations".
- The name-based destructuring short syntax seems to require the future 2.5 language version. Treat it as out of scope for 2.4 lessons.

### Gaps
- I did not find a single document listing the per-version status of `@JvmExposeBoxed` after 2.2. Its "Experimental" status in 2.4 is inferred from the KEEP header ("Experimental in 2.2"), the features page and the observed opt-in error.
- I did not check the 2.4.x compatibility guide for deprecations of `-Xcontext-parameters`; it only produced a redundancy warning.

## Key Question 2: What do the requested examples actually produce with kotlinc 2.4.21 (outputs and errors)?

### Takeaway
All requested demos were compiled and run. The non-local return, crossinline errors, mangled value-class names, `$delegate`/`KProperty` fields, `@DslMarker` errors, the context-parameter call and the sealed serialization round trip all behaved as the docs describe. Two extra findings: Kotlin 2.4.21 rejects local functions inside inline functions, and it crashes on a specific value-class `toString` pattern.

### Cited Findings

#### Demo A: non-local return from `forEach` (plus labeled return) [observed 2.4.21]
```kotlin
fun hasZeros(ints: List<Int>): Boolean {
    ints.forEach { if (it == 0) return true }   // returns from hasZeros
    return false
}
fun firstNegativeIndexLabeled(ints: List<Int>): Int {
    var idx = -1
    ints.forEachIndexed { i, v -> if (v >= 0) return@forEachIndexed; if (idx == -1) idx = i }
    return idx
}
```
Output:
```
hasZeros(listOf(1,0,2)) = true
hasZeros(listOf(1,2)) = false
firstNegativeIndexLabeled = 1
```
Bytecode of `hasZeros` (abridged): `invokeinterface Iterable.iterator` … `Iterator.hasNext` … `Iterator.next` … `checkcast Number; intValue` … `ifne 57; iconst_1; ireturn` … `goto 20`. There is no lambda class. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo B: inline vs non-inline call site [observed 2.4.21]
```kotlin
inline fun <T> measure(label: String, block: () -> T): T { val start = System.nanoTime(); try { return block() } finally { println("$label took ${(System.nanoTime() - start) / 1000} us") } }
fun <T> measureNotInline(label: String, block: () -> T): T { ... }
fun useInline(x: Int): Int = measure("inline") { x * 2 }
fun useNotInline(x: Int): Int = measureNotInline("plain") { x * 2 }
```
`javap -c`:
```
useNotInline(int):
   0: ldc "plain"
   2: iload_0
   3: invokedynamic #0:invoke:(I)Lkotlin/jvm/functions/Function0;
   8: invokestatic measureNotInline:(Ljava/lang/String;Lkotlin/jvm/functions/Function0;)Ljava/lang/Object;
  11: checkcast java/lang/Number
  14: invokevirtual java/lang/Number.intValue:()I
useInline(int):
   5: invokestatic System.nanoTime
  13: iload_0 / 14: iconst_2 / 15: imul        <- lambda body pasted in
  18..59: StringBuilder ... println          <- finally block, normal path
  67..115: StringBuilder ... println; athrow  <- finally block duplicated for exception path
```
Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo C: inline errors, including the crossinline one [observed 2.4.21]
```kotlin
fun ordinary(block: () -> Unit) = block()
fun bareReturnInNonInline() { ordinary { return } }
inline fun runLater(block: () -> Unit): Runnable = object : Runnable { override fun run() = block() }
inline fun storeIt(block: () -> Unit): () -> Unit = block
private fun secret() = 42
inline fun leaky() = secret()
inline fun runLaterOk(crossinline block: () -> Unit): Runnable = object : Runnable { override fun run() = block() }
fun nonLocalInsideCrossinline() { runLaterOk { return } }
```
```
Errors.kt:7:9: error: 'return' is prohibited here.
Errors.kt:13:30: error: cannot inline 'block: () -> Unit' here: it might contain non-local returns. Add 'crossinline' modifier to parameter declaration 'block: () -> Unit'.
Errors.kt:16:53: error: illegal usage of inline parameter 'block: () -> Unit'. Add 'noinline' modifier to the parameter declaration.
Errors.kt:21:22: error: public-API inline function cannot access non-public-API function.
Errors.kt:28:9: error: 'return' is prohibited here.
```
Also seen: `inline function 'fun rec(n: Int): Int' cannot be recursive.`, `local functions are not yet supported in inline functions.` and `public-API inline property accessor cannot access non-public-API property.` (the last was fixed by `@PublishedApi internal val items`). — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo D: javap of value-class functions (mangling) [observed 2.4.21]
```
public final class demo.value.MoneyKt {
  public static final java.lang.String charge-DfepdXk(long);
  public static final java.lang.String chargeFromJava(long);          // @JvmName("chargeFromJava")
  public static final java.lang.String refund-Y22K7oY(demo.value.Money); // Money? -> boxed, still mangled
  public static final <T> T identity(T);
  public static final long describe(demo.value.Priced);
  public static final long total(java.util.List<demo.value.Money>);
}
```
Call sites in `main`: `Money."box-impl":(J)Ldemo/value/Money;` appears before `refund-Y22K7oY`, `identity`, `describe`, each `listOf` element and `println`. `charge-DfepdXk:(J)` gets a raw `long`. Program output: `charged Money(19.99)`, … `java.lang.IllegalArgumentException: negative amount: -1`, `true` (for `==`). — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo E: javap of delegated properties [observed 2.4.21]
Shown in full under Lesson 3: `$$delegatedProperties` is a `KProperty[]` filled in `static {}` with `MutablePropertyReference1Impl(Order.class, "status", "getStatus()Ljava/lang/String;", 0)`; `status$delegate` is typed by the delegate's static type; and `lazy` gets a `kotlin.Lazy x$delegate` field with no `$$delegatedProperties`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo F: `@DslMarker` violation [observed 2.4.21]
Error text is quoted under Lesson 4. The DSL source is the lab solution in Key Question 5. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo G: context-parameter function call (with and without `-Xcontext-parameters`) [observed 2.4.21]
```kotlin
interface Logger { fun log(msg: String) }
class TxId(val value: String)
data class Payment(val amountCents: Long)

context(logger: Logger, tx: TxId)
fun Payment.authorize(merchant: String): Boolean {
    logger.log("[${tx.value}] authorizing $amountCents for $merchant")
    return amountCents < 100_000
}
context(_: Logger) fun audit(event: String) = contextOf<Logger>().log("AUDIT $event")
context(logger: Logger) val loggerName: String get() = logger::class.simpleName ?: "anonymous"

fun main() {
    val console = object : Logger { override fun log(msg: String) = println(msg) }
    context(console, TxId("tx-42")) {
        println(Payment(5_000).authorize("coffee-shop"))
        audit("done")
    }
    with(console) { audit("from with()") }   // an implicit receiver also satisfies a context parameter
}
```
Output (no flag):
```
[tx-42] authorizing 5000 for coffee-shop
true
AUDIT done
AUDIT from with()
```
With `-Xcontext-parameters`: `warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.` With `-language-version 2.3 -Xcontext-parameters` it compiles silently, which is the 2.2/2.3-era setup. `javap`:
```
public static final boolean authorize(demo.ctx.Logger, demo.ctx.TxId, demo.ctx.Payment, java.lang.String);
public static final void audit(demo.ctx.Logger, java.lang.String);
public static final java.lang.String getLoggerName(demo.ctx.Logger);
```
Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Demo H: kotlinx.serialization round trip of a sealed hierarchy [observed 2.4.21 + kotlinx-serialization 1.12.0]
```kotlin
@Serializable sealed interface PaymentEvent { val paymentId: String }
@Serializable @SerialName("authorized") data class Authorized(override val paymentId: String, val amountCents: Long, val currency: String = "EUR") : PaymentEvent
@Serializable @SerialName("captured")   data class Captured(override val paymentId: String, val amountCents: Long) : PaymentEvent
@Serializable @SerialName("refunded")   data class Refunded(override val paymentId: String, val amountCents: Long, val reason: String? = null) : PaymentEvent
@Serializable data class Envelope(val events: List<PaymentEvent>)
val json = Json { classDiscriminator = "type"; ignoreUnknownKeys = true; encodeDefaults = false; explicitNulls = false }
```
Output:
```
{"events":[{"type":"authorized","paymentId":"p-1","amountCents":1999},{"type":"captured","paymentId":"p-1","amountCents":1999},{"type":"refunded","paymentId":"p-1","amountCents":500,"reason":"partial"}]}
true                                                     <- decoded == original
Captured(paymentId=p-9, amountCents=10)                  <- unknown key "extra" ignored
Unexpected JSON token at offset 55: Encountered an unknown key 'extra' at path: $       <- default Json is strict
Unexpected JSON token at offset 0: Serializer for subclass 'chargeback' is not found in the polymorphic scope of 'PaymentEvent' at path: $
{"paymentId":"p-2","amountCents":1}                      <- static type Captured: no discriminator
{"type":"captured","paymentId":"p-2","amountCents":1}    <- static type PaymentEvent
captured / SEALED                                        <- descriptor serialName / kind
```
The `currency = "EUR"` default was not encoded. Compile command: `-Xplugin=kotlin-serialization-compiler-plugin-2.4.21.jar`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)

#### Demo I: compiler crash on a value class whose `toString()` returns a Java platform type [observed 2.4.21 and 2.3.21]
```kotlin
@JvmInline value class M(val c: Long) { override fun toString() = java.math.BigDecimal.valueOf(c, 2).toPlainString() }
fun f(m: M) = "x $m"
```
This crashes the compiler: `exception: org.jetbrains.kotlin.backend.common.BackendException: Backend Internal error: Exception during IR lowering … java.util.NoSuchElementException: Sequence contains no element matching the predicate. at …JvmStringConcatenationLoweringKt.getToStringFunction(JvmStringConcatenationLowering.kt:255) … lowerInlineClassArgument`.
- It happens with `-jvm-target` 1.8, 11 and 21, and with `-Xstring-concat=inline` or `indy`.
- It also happens with kotlinc 2.3.21.
- Writing `override fun toString(): String = …`, with an explicit return type, fixes it.

Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/); [kotlinc 2.3.21 artifact](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.3.21/)

#### Demo J: CLI default JVM target [observed 2.4.21]
JUnit 6's Kotlin `assertThrows` is inline. Compiling tests without `-jvm-target` gave `error: cannot inline bytecode built with JVM target 17 into bytecode that is being built with JVM target 1.8. Specify proper '-jvm-target' option.` So plain `kotlinc` 2.4.21 still defaults to 1.8. Lab builds must set `-jvm-target 21` or a Gradle toolchain. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

### Inferences
- Demo I is a good real-world example of "explicit return types on public API": the explicit `: String` avoids a compiler crash as well as platform-type leakage. Keep `toString(): String` explicit in the Money lab.
- Kotlin lambdas passed to non-inline functions compile to `invokedynamic` (LambdaMetafactory) in 2.4.21. A capturing lambda like `{ x * 2 }` will normally allocate one object per call. The allocation claim is inferred from JVM LambdaMetafactory semantics and was not measured.

### Gaps
- I did not search YouTrack for an existing issue for Demo I. One web search found no report. Lesson writers should not cite an issue number.
- I did not benchmark inline vs non-inline (JMH). No performance numbers are claimed.

## Key Question 3: How does each feature look from Java?

### Takeaway
To Java, an inline function is an ordinary static method with no inlining, and a reified inline function is invisible. Value-class APIs are mangled and unboxed unless `@JvmName` or `@JvmExposeBoxed` is used. Delegated properties look like normal getters and setters over a private `$delegate` field. Context parameters become leading ordinary parameters.

### Cited Findings
- **Inline functions from Java** [observed 2.4.21]:
  - `public static final <T> T timed(Function0<? extends T>)` has normal flags (`0x0019 ACC_PUBLIC, ACC_STATIC, ACC_FINAL`). Java called it with a lambda, `LibKt.timed(() -> "...")`, and it printed `took 438357ns` then `called as a normal method from Java`. The lambda was not inlined.
  - The reified `typeName()` is compiled with `ACC_SYNTHETIC` (`flags: (0x1019)`), and `javac` reports `error: cannot find symbol … method typeName()`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Value classes from Java.**
  - The docs: "By default, Kotlin compiles inline value classes to use unboxed representations, which are often inaccessible from Java. For example, you can't call the constructor for the MyInt class from Java". — [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
  - [observed 2.4.21] What `javac` saw:
    - Java calling `ExposeKt.payHidden(5L)`, which is mangled to `payHidden-VYnWypA(long)`, gets `error: cannot find symbol … method payHidden(long)`.
    - With `@JvmExposeBoxed`, Java ran `new Cents(250)`, `ExposeKt.pay(c)` and `c.doubled().getValue()`, printing `paid 250` and `500`. `new Cents(-1)` threw `IllegalArgumentException: negative`, so the `init` validation runs in the exposed constructor.
    - `@JvmName("chargeFromJava")` gives Java `chargeFromJava(long)`. Java passes a raw `long` and loses the type safety.
    - A class holding a value class (`Invoice(val amount: Money)`) has a private constructor plus a synthetic `DefaultConstructorMarker` one, and a mangled getter `getAmount-vT5tX_U()`. `-Xjvm-expose-boxed` adds `public Invoice(Money)` and `public final Money getAmount()`.
    - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Delegated properties from Java** [observed 2.4.21]:
  - Java sees `public final String getStatus()` and `public final void setStatus(String)`. The delegate is a `private final … status$delegate` field and `$$delegatedProperties` is package-private static, so Java cannot tell the property is delegated.
  - For `lazy`, each getter call goes through `Lazy.getValue()`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Context parameters from Java.**
  - The KEEP rule: context parameters come first, then the extension receiver, then the value parameters. — [KEEP-0367](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md)
  - [observed 2.4.21] Java ran `CtxKt.authorize(l, new TxId("tx-j"), new Payment(10), "from-java")` and `CtxKt.audit(l, "java audit")`, which printed `java: [tx-j] authorizing 10 for from-java`, `java: AUDIT java audit` and `true`. The context property `loggerName` is `getLoggerName(Logger)`.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **no-arg from Java**: the constructor is callable from Java but not from Kotlin ("you can call it from Java but not from Kotlin"). — [No-arg compiler plugin](https://kotlinlang.org/docs/no-arg-plugin.html). Confirmed by the Kotlin compile error and the Java-reflection run in Lesson 6.
- **Serialization from Java** [observed 2.4.21]: the generated API is `Captured.Companion.serializer()`, which returns `KSerializer<Captured>`, plus a `Captured$$serializer.INSTANCE` singleton. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)

### Inferences
- In a mixed Java/Kotlin Quarkus codebase, a value-class-heavy Kotlin API should either use `@JvmExposeBoxed` (still Experimental, needs an opt-in) or offer `@JvmName` overloads. Otherwise Java code and Java-based frameworks (reflection, CDI proxies) see mangled names.
- Context parameters are binary-visible as leading parameters. Adding a context parameter to a public function is therefore a binary-incompatible signature change for Java and for already-compiled Kotlin callers. This is inferred from the JVM representation, not tested across versions.

### Gaps
- I did not test how Jackson, RESTEasy or Hibernate (Quarkus stack) treat mangled getters such as `getAmount-vT5tX_U`.

## Key Question 4: Which misconceptions should the lessons tackle, and what evidence refutes them?

### Takeaway
Each of the six named misconceptions is refuted by a doc quote and a reproducible run. Inline grows code and freezes bodies into clients. Value classes box in generics, nullables, interfaces and collections. `by lazy` costs a per-instance object plus a lock. DSLs need only lambdas with receivers. Contracts are trusted, not verified. All-open opens only annotated classes.

### Cited Findings
- **"inline makes everything faster."**
  - The docs warn about code growth and say benefit comes when the function has function-typed parameters. There is a dedicated warning when nothing is inlinable. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - [observed 2.4.21] Evidence:
    - The duplicated `finally` in Demo B shows the code growth.
    - The NOTHING_TO_INLINE warning text: "expected performance impact from inlining is insignificant".
    - The ABI demo printed `inline=v1 plain=v2`: stale inlined code in old clients.
    - Inline functions cannot be recursive or contain local functions.
    - Java callers get no inlining at all.
    - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **"value classes are never boxed."**
  - The docs: "inline classes are boxed whenever they are used as another type". — [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
  - [observed 2.4.21] `box-impl` is called for nullable, generic, interface, `listOf` and `println` uses, and a test confirmed `listOf(Money(1))[0].javaClass == Money::class.java`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **"`by lazy` is free."**
  - The default mode is synchronized. — [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
  - [observed 2.4.21] Each instance gets a `Lazy` object (`SynchronizedLazyImpl` with `lock` and `volatile _value`, using `monitorenter`) plus an initializer `Function0` created via `invokedynamic`. Every read goes through `Lazy.getValue()`, with unboxing for primitives. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **"DSLs need a library."**
  - The type-safe builders page builds HTML from plain classes, extension functions and "function literals with receiver". — [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
  - [observed 2.4.21] The lab's payment DSL uses only the standard library, and `buildList`, `buildString` and `buildMap` are in the stdlib. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **"contracts are checked by the compiler."**
  - KEEP-139: "Compiler trusts contracts unconditionally … programmer is responsible", and "Formal verification is a non-goal". — [KEEP-0139](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md)
  - [observed 2.4.21] The lying contract compiled and caused a `ClassCastException`. Only some `callsInPlace` misuse gets warnings. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **"all-open makes every class open."**
  - The docs: "The all-open plugin only processes classes marked with an annotation that you register in its configuration." — [All-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html)
  - [observed 2.4.21] `PlainHelper` stayed `final`. Private members stayed private and backing fields stayed `final`. The `quarkus` preset did not open a `jakarta`-annotated bean. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
- **More misconceptions with evidence:**
  - "Overriding one method of a `by`-delegated class changes the delegate's behaviour." It does not: `putAll` and `addAll` bypass the override. — [Delegation](https://kotlinlang.org/docs/delegation.html); [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
  - "A `var` delegate can be swapped." It cannot: the delegate is captured into `$$delegate_0`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
  - "no-arg is safe for non-null fields." It is not: `note` was `null` without `invokeInitializers`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-noarg-compiler-plugin/2.4.21/)
  - "Context parameters are just context receivers renamed." They are not: they are named, are not receivers in the body, require `contextOf<T>()` for anonymous ones, and are not allowed on constructors. — [KEEP-0367](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md); [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html) ("context parameters are not introduced as receivers in the body of a function")
  - "`@Serializable` works without the plugin." It does not: `.serializer()` is unresolved without the plugin. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)

### Inferences
- The most convincing format for a senior engineer is "claim, javap, run". Each misconception above has a two-minute terminal demo.

### Gaps
- There is no quantitative cost for `lazy` or for value-class boxing. A JMH run was out of scope.

## Key Question 5: Which lab exercises can be graded with JUnit, and what are the expected outcomes?

### Takeaway
Five labs were implemented and graded with JUnit Jupiter (JUnit Platform Console 6.1.3) on Kotlin 2.4.21 with the serialization plugin. All 18 tests passed, and one compile-fail check produced the expected `crossinline` error. The build needs `-jvm-target 21`, because JUnit's inline `assertThrows` is built for JVM 17.

### Cited Findings
Command used. With Gradle, use `kotlin("jvm")` + `kotlin("plugin.serialization")` version 2.4.21 and `jvmToolchain(21)`.
```
kotlinc -jvm-target 21 -Xplugin=kotlin-serialization-compiler-plugin-2.4.21.jar \
  -cp kotlinx-serialization-core-jvm-1.12.0.jar:kotlinx-serialization-json-jvm-1.12.0.jar:junit-platform-console-standalone-6.1.3.jar \
  src/*.kt test/*.kt -d out
java -jar junit-platform-console-standalone-6.1.3.jar execute -cp out:kotlin-stdlib-2.4.21.jar:... --select-package labs
```
Result:
```
├─ EventsTest ✔  (round trips sealed hierarchy, defaults are not encoded, unknown subtype fails/unknown key is ignored, uses stable discriminators)
├─ RetryTest ✔   (gives up and keeps earlier failures as suppressed, succeeds on third attempt, does not retry when predicate says no)
├─ RecordedTest ✔ (records only real changes in order, compiler generated a delegate field)
├─ MoneyTest ✔   (rejects sub-cent precision, overflow is detected, is a JvmInline value class and gets boxed in collections, function taking Money is mangled unless JvmName, parses and adds, rejects negative)
└─ DslTest ✔     (validates, builders carry the DSL marker, builds request and totals)
[        18 tests successful      ]
[         0 tests failed          ]
```
Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/); [JUnit console standalone 6.1.3](https://maven-central.storage-download.googleapis.com/maven2/org/junit/platform/junit-platform-console-standalone/maven-metadata.xml)

#### Lab 1: retry helper (inline + crossinline + @PublishedApi), reference solution
```kotlin
package labs.retry
class RetryExhaustedException(val attempts: Int, cause: Throwable) : RuntimeException("gave up after $attempts attempts", cause)

inline fun <T> retry(
    maxAttempts: Int,
    crossinline shouldRetry: (Throwable) -> Boolean = { true },
    crossinline block: (attempt: Int) -> T,
): T = retryLoop(maxAttempts, { shouldRetry(it) }, { block(it) })   // re-wrapped in new lambdas -> crossinline required

@PublishedApi
internal fun <T> retryLoop(maxAttempts: Int, shouldRetry: (Throwable) -> Boolean, block: (Int) -> T): T {
    require(maxAttempts >= 1) { "maxAttempts must be >= 1" }
    val failures = mutableListOf<Throwable>()
    for (attempt in 1..maxAttempts) {
        try { return block(attempt) } catch (t: Throwable) {
            failures += t
            if (attempt == maxAttempts || !shouldRetry(t)) {
                val ex = RetryExhaustedException(attempt, t)
                failures.dropLast(1).forEach(ex::addSuppressed)
                throw ex
            }
        }
    }
    error("unreachable")
}
```
- Tests:
  - It succeeds on attempt 3 (`"ok@3"`, `calls == 3`).
  - After 3 failures it throws `RetryExhaustedException(attempts = 3)` with `cause.message == "fail 3"` and suppressed `["fail 1", "fail 2"]`.
  - When `shouldRetry` returns false there is exactly 1 call.
- Compile-fail check (shown to students, not a JUnit test): `retry(3) { attempt -> if (attempt == 1) return "early"; "x" }` gives `NonLocal.kt:4:45: error: 'return' is prohibited here.`
- Design note found while building: a first version used a local `fun attempt(n)` inside the inline function and failed with `local functions are not yet supported in inline functions.` The crossinline-via-`@PublishedApi`-helper pattern above is the working design.
- Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lab 2: Money value class with validation, reference solution
```kotlin
package labs.money
import java.math.BigDecimal
@JvmInline
value class Money(val cents: Long) : Comparable<Money> {
    init { require(cents >= 0) { "amount must be non-negative, was $cents" } }
    operator fun plus(other: Money) = Money(Math.addExact(cents, other.cents))
    operator fun times(qty: Int) = Money(Math.multiplyExact(cents, qty.toLong()))
    override fun compareTo(other: Money) = cents.compareTo(other.cents)
    override fun toString(): String = BigDecimal.valueOf(cents, 2).toPlainString()   // explicit ': String' (see Demo I)
    companion object {
        fun of(text: String): Money = Money(BigDecimal(text).setScale(2).unscaledValueExact())
        private fun BigDecimal.unscaledValueExact(): Long = unscaledValue().longValueExact()
    }
}
fun format(amount: Money): String = "EUR $amount"                       // mangled: format-<hash>
@JvmName("formatForJava") fun formatJ(amount: Money): String = "EUR $amount"
```
- Tests:
  - `Money(-1)` gives `IllegalArgumentException`.
  - `Money.of("12.34") == Money(1234)`, and `Money.of("10") + Money(500)` prints `15.00`.
  - `Money.of("1.234")` gives `ArithmeticException`, because `setScale(2)` needs rounding.
  - `Money(Long.MAX_VALUE) + Money(1)` gives `ArithmeticException`.
  - `@JvmInline` is present at runtime, and an element read from `List<Money>` is a boxed `Money` instance.
  - `labs.money.MoneyKt` declares a method starting with `format-` and one named `formatForJava`.
- Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lab 3: custom delegated property that records changes, reference solution
```kotlin
package labs.recorded
import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty
data class Change(val property: String, val old: Any?, val new: Any?)
class ChangeLog { val changes = mutableListOf<Change>() }
class Recorded<T>(private var value: T, private val log: ChangeLog) : ReadWriteProperty<Any?, T> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value
    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        if (value != this.value) log.changes += Change(property.name, this.value, value)
        this.value = value
    }
}
fun <T> ChangeLog.recorded(initial: T) = Recorded(initial, this)
class PaymentDraft(val log: ChangeLog = ChangeLog()) {
    var status: String by log.recorded("NEW")
    var amountCents: Long by log.recorded(0L)
}
```
- Tests:
  - `status = "AUTHORIZED"` twice, then `amountCents = 1999`, then `status = "CAPTURED"` gives exactly `[Change(status, NEW, AUTHORIZED), Change(amountCents, 0, 1999), Change(status, AUTHORIZED, CAPTURED)]`.
  - `PaymentDraft::class.java.getDeclaredField("status$delegate")` exists.
- Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lab 4: payment-request DSL with @DslMarker, reference solution
```kotlin
package labs.dsl
import java.math.BigDecimal
@DslMarker @Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE) annotation class PaymentDsl
data class Party(val name: String, val iban: String)
data class LineItem(val sku: String, val qty: Int, val unitPrice: BigDecimal)
data class PaymentRequest(val id: String, val currency: String, val payer: Party, val payee: Party, val items: List<LineItem>) {
    val total: BigDecimal get() = items.fold(BigDecimal.ZERO) { acc, li -> acc + li.unitPrice * li.qty.toBigDecimal() }
}
@PaymentDsl class PartyBuilder { var name = ""; var iban = ""; fun build(): Party { require(iban.isNotBlank()) { "iban required" }; return Party(name, iban) } }
@PaymentDsl class ItemsBuilder { private val items = mutableListOf<LineItem>(); fun item(sku: String, qty: Int, unitPrice: String) { items += LineItem(sku, qty, BigDecimal(unitPrice)) }; fun build() = items.toList() }
@PaymentDsl class PaymentRequestBuilder(private val id: String) {
    var currency: String = "EUR"
    private var payer: Party? = null; private var payee: Party? = null; private var items: List<LineItem> = emptyList()
    fun payer(block: PartyBuilder.() -> Unit) { payer = PartyBuilder().apply(block).build() }
    fun payee(block: PartyBuilder.() -> Unit) { payee = PartyBuilder().apply(block).build() }
    fun items(block: ItemsBuilder.() -> Unit) { items = ItemsBuilder().apply(block).build() }
    fun build(): PaymentRequest {
        require(items.isNotEmpty()) { "at least one item" }
        return PaymentRequest(id, currency, checkNotNull(payer) { "payer missing" }, checkNotNull(payee) { "payee missing" }, items)
    }
}
fun paymentRequest(id: String, block: PaymentRequestBuilder.() -> Unit): PaymentRequest = PaymentRequestBuilder(id).apply(block).build()
```
- Tests:
  - A sample request with items `("A", 2, "9.99")` and `("B", 1, "5.00")` totals `BigDecimal("24.98")`, with currency `EUR` and 2 items.
  - A missing payer gives `IllegalStateException`. No items gives `IllegalArgumentException`.
  - All three builder classes carry `@PaymentDsl`; Kotlin annotations are RUNTIME-retained by default.
- Compile-fail check for students: calling `payee {}` or `currency = …` inside `payer {}` gives the two "cannot be called in this context with an implicit receiver" errors from Demo F.
- Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

#### Lab 5: serialization round trip of a sealed PaymentEvent hierarchy, reference solution
Classes as in Demo H, plus:
```kotlin
val eventJson = Json { ignoreUnknownKeys = true; explicitNulls = false }
fun encodeEvents(events: List<PaymentEvent>): String = eventJson.encodeToString(events)
fun decodeEvents(text: String): List<PaymentEvent> = eventJson.decodeFromString(text)
```
- Tests:
  - Decoding the encoded list gives an equal list.
  - The `type` values are exactly `["authorized", "captured", "refunded"]`.
  - `"currency"` is absent when it equals the default.
  - `[{"type":"chargeback",...}]` gives `kotlinx.serialization.SerializationException`.
  - An extra key `"x"` is ignored.
- Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)

#### Full test file used (JUnit Jupiter, Kotlin)
```kotlin
package labs
import labs.retry.*; import labs.money.*; import labs.recorded.*; import labs.dsl.*; import labs.events.*
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.*
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import java.math.BigDecimal

class RetryTest {
    @Test fun `succeeds on third attempt`() { var calls = 0
        val r = retry(maxAttempts = 5) { attempt -> calls++; if (attempt < 3) error("boom $attempt") else "ok@$attempt" }
        assertEquals("ok@3", r); assertEquals(3, calls) }
    @Test fun `gives up and keeps earlier failures as suppressed`() {
        val ex = assertThrows<RetryExhaustedException> { retry(3) { attempt -> throw IllegalStateException("fail $attempt") } }
        assertEquals(3, ex.attempts); assertEquals("fail 3", ex.cause?.message)
        assertEquals(listOf("fail 1", "fail 2"), ex.suppressed.map { it.message }) }
    @Test fun `does not retry when predicate says no`() { var calls = 0
        assertThrows<RetryExhaustedException> { retry(5, shouldRetry = { it !is IllegalArgumentException }) { calls++; throw IllegalArgumentException("bad input") } }
        assertEquals(1, calls) }
}
class MoneyTest {
    @Test fun `rejects negative`() { assertThrows<IllegalArgumentException> { Money(-1) } }
    @Test fun `parses and adds`() { assertEquals(Money(1234), Money.of("12.34")); assertEquals("15.00", (Money.of("10") + Money(500)).toString()) }
    @Test fun `rejects sub-cent precision`() { assertThrows<ArithmeticException> { Money.of("1.234") } }
    @Test fun `overflow is detected`() { assertThrows<ArithmeticException> { Money(Long.MAX_VALUE) + Money(1) } }
    @Test fun `is a JvmInline value class and gets boxed in collections`() {
        assertTrue(Money::class.java.isAnnotationPresent(JvmInline::class.java))
        val asAny: Any = listOf(Money(1))[0]; assertEquals(Money::class.java, asAny.javaClass) }
    @Test fun `function taking Money is mangled unless JvmName`() {
        val names = Class.forName("labs.money.MoneyKt").declaredMethods.map { it.name }
        assertTrue(names.any { it.startsWith("format-") }, names.toString()); assertTrue("formatForJava" in names) }
}
class RecordedTest {
    @Test fun `records only real changes in order`() { val d = PaymentDraft()
        d.status = "AUTHORIZED"; d.status = "AUTHORIZED"; d.amountCents = 1999; d.status = "CAPTURED"
        assertEquals(listOf(Change("status", "NEW", "AUTHORIZED"), Change("amountCents", 0L, 1999L), Change("status", "AUTHORIZED", "CAPTURED")), d.log.changes) }
    @Test fun `compiler generated a delegate field`() { assertNotNull(PaymentDraft::class.java.getDeclaredField("status\$delegate")) }
}
class DslTest {
    private fun sample() = paymentRequest("PR-1") {
        payer { name = "ACME"; iban = "DE89370400440532013000" }
        payee { name = "Shop"; iban = "FR1420041010050500013M02606" }
        items { item("A", 2, "9.99"); item("B", 1, "5.00") } }
    @Test fun `builds request and totals`() { val r = sample(); assertEquals(BigDecimal("24.98"), r.total); assertEquals("EUR", r.currency); assertEquals(2, r.items.size) }
    @Test fun `validates`() {
        assertThrows<IllegalStateException> { paymentRequest("x") { payee { iban = "X" }; items { item("A", 1, "1") } } }
        assertThrows<IllegalArgumentException> { paymentRequest("x") { payer { iban = "X" }; payee { iban = "Y" } } } }
    @Test fun `builders carry the DSL marker`() {
        listOf(PaymentRequestBuilder::class.java, PartyBuilder::class.java, ItemsBuilder::class.java)
            .forEach { assertTrue(it.isAnnotationPresent(PaymentDsl::class.java), it.name) } }
}
class EventsTest {
    private val events = listOf(Authorized("p1", 1999), Captured("p1", 1999), Refunded("p1", 500, "partial"))
    @Test fun `round trips sealed hierarchy`() { assertEquals(events, decodeEvents(encodeEvents(events))) }
    @Test fun `uses stable discriminators`() {
        val types = Json.parseToJsonElement(encodeEvents(events)).jsonArray.map { it.jsonObject["type"]!!.jsonPrimitive.content }
        assertEquals(listOf("authorized", "captured", "refunded"), types) }
    @Test fun `defaults are not encoded`() { assertFalse("currency" in encodeEvents(listOf(Authorized("p", 1)))) }
    @Test fun `unknown subtype fails, unknown key is ignored`() {
        assertThrows<SerializationException> { decodeEvents("""[{"type":"chargeback","paymentId":"p"}]""") }
        assertEquals(listOf(Captured("p", 1)), decodeEvents("""[{"type":"captured","paymentId":"p","amountCents":1,"x":0}]""")) }
}
```
Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)

### Inferences
- "Must not compile" requirements (no non-local return in `retry`, DSL scope violations) cannot be JUnit tests. Grade them with a compile-fail harness that compiles a snippet and asserts the error text, or as review questions. The exact expected error strings are captured above.
- An optional 6th lab could cover compiler plugins: `javap` checks that a `jakarta.persistence.Entity` class is non-final and has a no-arg constructor. A JUnit test can do this with `Modifier.isFinal(cls.modifiers)` and `cls.getDeclaredConstructor()`. Not built here.

### Gaps
- The labs were run with a CLI harness, not Gradle, so the Gradle build files for the course repo are not verified. The plugin ids and versions in Lesson 6 come from the docs.

## Teaching notes

### Takeaway
Teach each lesson as "mechanism, then bytecode, then trap": a short concept, a `javap` or compiler-error demo the learner can reproduce, then the production pitfall, framed with Quarkus and payments examples.

### Cited Findings
- **Analogies and framing.**
  - Inline: "copy-paste done by the compiler". Show the duplicated `finally` block and the `inline=v1 plain=v2` ABI demo. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
  - `crossinline`: "the lambda will run somewhere you are not, so it may not return from you". Tie it to the docs' "another execution context, such as a local object or a nested function". — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
  - Value classes: "`Int` vs `Integer`, but for your own types". The docs make this comparison themselves: "This is similar to how Int can be represented either as a primitive int or as the wrapper Integer." — [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
  - Class delegation: "a decorator the compiler writes for you, which forwards everything you didn't override, including the bulk methods". The AuditedMap demo is the trap. — [Delegation](https://kotlinlang.org/docs/delegation.html)
  - Context parameters: "implicit arguments resolved by type, like a tiny compile-time DI". The docs mention "simplified dependency injection". On the JVM they are plain leading parameters. — [Context parameters](https://kotlinlang.org/docs/context-parameters.html); [KEEP-0367](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md)
  - Contracts: "a promise to the compiler, not a check". Use the lying-contract `ClassCastException` demo. — [KEEP-0139](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md)
- **Quarkus- and backend-specific hooks.**
  - The all-open `quarkus` preset is javax-only in 2.4.21; demonstrate it with `javap`. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/)
  - The kotlin-jpa plugin applies all-open only from 2.3.20, which matters for Hibernate lazy proxies. — [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html)
  - The no-arg null-field trap. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-noarg-compiler-plugin/2.4.21/)
  - For JSON, reuse one `Json` instance ("immutable and thread-safe… Reusing custom Json instances improves performance") and use `@SerialName` for discriminators (the default is the fully qualified class name, which changes on refactors). — [Customize the Json instance](https://kotlinlang.org/docs/serialization-json-configuration.html); [Serialize polymorphic classes](https://kotlinlang.org/docs/serialization-polymorphism.html)
- **Demo checklist**, each reproduced in this session with kotlinc 2.4.21:
  - Demos A–I, plus the delegation trap, `lazy` implementation classes, `@JvmExposeBoxed` from Java, the context-parameter Java caller and the plugin presets.
  - Expected outputs are quoted verbatim above.
  - Source: [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Lab expected outcomes**: all 18 JUnit tests green with the reference solutions, plus two compile-fail snippets with exact error strings. See Key Question 5. — [kotlinc 2.4.21 run](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/)
- **Suggested lesson split** (6 lessons):
  1. Inline functions: bytecode, non-local returns, noinline/crossinline, inline properties, `@PublishedApi`, when not to inline, reified recap.
  2. Value classes: representation, boxing points, mangling, `@JvmName` and `@JvmExposeBoxed`, Java view, Valhalla outlook.
  3. Delegation: class delegation and its traps; `lazy` modes and costs; observable, vetoable and map delegates; custom delegates; `provideDelegate`; generated code.
  4. Type-safe DSLs: receivers, `@DslMarker`, the payment DSL, stdlib builders, context receivers' history.
  5. Contracts and context parameters: status, opt-ins, trust model, resolution, JVM shape, migration from receivers.
  6. Compiler plugins: all-open/spring/jpa/quarkus presets, no-arg, kotlinx.serialization, KSP vs kapt.
  - This structure is inferred from the requested topic list.

### Inferences
- Learners who finished the reified lesson will ask why reified functions are invisible to Java. Answer with the `ACC_SYNTHETIC` flag observed here, then link to the generics notes.
- Because context parameters are newly Stable in 2.4.0, many codebases and blog posts still show `-Xcontext-parameters` or old `context(Logger)` receivers. Lessons should show the 2.4.21 redundancy warning and the receivers error so the learner can recognize outdated material.

### Gaps
- There is no learner-research evidence (e.g. studies) on teaching these specific Kotlin features. The analogies above are pedagogical choices, not research-backed findings.

## Verified URLs

### Takeaway
Only the pages below were fetched in this session, via curl or WebFetch. quarkus.io, openjdk.org (JEP 401), api.github.com and YouTrack were not reachable or not used, so nothing is cited from them.

### Cited Findings
- Kotlin docs (kotlinlang.org):
  - What's new pages: [whatsnew22](https://kotlinlang.org/docs/whatsnew22.html), [whatsnew2220](https://kotlinlang.org/docs/whatsnew2220.html), [whatsnew23](https://kotlinlang.org/docs/whatsnew23.html), [whatsnew2320](https://kotlinlang.org/docs/whatsnew2320.html), [whatsnew24](https://kotlinlang.org/docs/whatsnew24.html), [whatsnew2420](https://kotlinlang.org/docs/whatsnew2420.html), [whatsnew1620](https://kotlinlang.org/docs/whatsnew1620.html)
  - Language features: [inline-functions](https://kotlinlang.org/docs/inline-functions.html), [inline-classes](https://kotlinlang.org/docs/inline-classes.html), [delegation](https://kotlinlang.org/docs/delegation.html), [delegated-properties](https://kotlinlang.org/docs/delegated-properties.html), [type-safe-builders](https://kotlinlang.org/docs/type-safe-builders.html), [context-parameters](https://kotlinlang.org/docs/context-parameters.html), [lambdas](https://kotlinlang.org/docs/lambdas.html), [java-to-kotlin-interop](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
  - Compiler plugins and annotation processing: [all-open-plugin](https://kotlinlang.org/docs/all-open-plugin.html), [no-arg-plugin](https://kotlinlang.org/docs/no-arg-plugin.html), [kotlin-spring-plugin](https://kotlinlang.org/docs/kotlin-spring-plugin.html), [kotlin-jpa-plugin](https://kotlinlang.org/docs/kotlin-jpa-plugin.html), [kapt](https://kotlinlang.org/docs/kapt.html), [ksp-overview](https://kotlinlang.org/docs/ksp-overview.html), [ksp-kapt-migration](https://kotlinlang.org/docs/ksp-kapt-migration.html), [ksp-quickstart](https://kotlinlang.org/docs/ksp-quickstart.html)
  - Serialization: [serialization](https://kotlinlang.org/docs/serialization.html), [serialization-get-started](https://kotlinlang.org/docs/serialization-get-started.html), [serialization-polymorphism](https://kotlinlang.org/docs/serialization-polymorphism.html), [serialization-configure-json-serialization](https://kotlinlang.org/docs/serialization-configure-json-serialization.html), [serialization-json-configuration](https://kotlinlang.org/docs/serialization-json-configuration.html), [serialization-create-and-use-serializers](https://kotlinlang.org/docs/serialization-create-and-use-serializers.html)
  - Status and roadmap: [components-stability](https://kotlinlang.org/docs/components-stability.html), [kotlin-language-features-and-proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html), [kotlin-evolution-principles](https://kotlinlang.org/docs/kotlin-evolution-principles.html), [roadmap](https://kotlinlang.org/docs/roadmap.html)
  - Compatibility guides: [compatibility-guide-22](https://kotlinlang.org/docs/compatibility-guide-22.html), [compatibility-guide-23](https://kotlinlang.org/docs/compatibility-guide-23.html), [compatibility-guide-24](https://kotlinlang.org/docs/compatibility-guide-24.html). These were downloaded and grepped; none contained context-receiver text.
- KEEP (fetched as raw files):
  - [KEEP-0367 context parameters](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md), [KEEP-0259 context receivers](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0259-context-receivers.md), [KEEP-0394 JvmExposeBoxed](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0394-jvm-expose-boxed.md), [KEEP-0139 contracts](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md), [notes/value-classes.md](https://github.com/Kotlin/KEEP/blob/master/notes/value-classes.md)
  - The master-branch copies of the proposals carry "REDIRECT TO" headers pointing at the main-branch `KEEP-0xxx` files.
- KSP: [google/ksp README](https://github.com/google/ksp), [docs/ksp2.md](https://github.com/google/ksp/blob/main/docs/ksp2.md), [releases](https://github.com/google/ksp/releases), [release 2.3.0](https://github.com/google/ksp/releases/tag/2.3.0)
- kotlinx.serialization repo: the old guide [docs/polymorphism.md](https://github.com/Kotlin/kotlinx.serialization/blob/master/docs/polymorphism.md) now says "The Kotlin serialization documentation has moved to kotlinlang.org". The kotlinlang pages above were used instead.
- Maven Central (artifacts and metadata used for the runs):
  - [kotlin-compiler metadata](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/maven-metadata.xml), [kotlin-compiler 2.4.21](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.4.21/), [kotlin-compiler 2.3.21](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler/2.3.21/)
  - [kotlin-allopen-compiler-plugin 2.4.21](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-allopen-compiler-plugin/2.4.21/), [kotlin-noarg-compiler-plugin 2.4.21](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-noarg-compiler-plugin/2.4.21/), [kotlin-serialization-compiler-plugin 2.4.21](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-serialization-compiler-plugin/2.4.21/)
  - [kotlinx-serialization-json-jvm metadata](https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlinx/kotlinx-serialization-json-jvm/maven-metadata.xml), [junit-platform-console-standalone metadata](https://maven-central.storage-download.googleapis.com/maven2/org/junit/platform/junit-platform-console-standalone/maven-metadata.xml), [KSP symbol-processing-api metadata](https://maven-central.storage-download.googleapis.com/maven2/com/google/devtools/ksp/symbol-processing-api/maven-metadata.xml) (latest 2.3.13)

### Inferences
- The kotlinlang.org pages carry 2026 "last modified" dates (for example, inline-classes 12 August 2026 and all-open 21 October 2026). They reflect the 2.4.x state.

### Gaps
- Not reachable in this session: [quarkus.io/guides/kotlin](https://quarkus.io/guides/kotlin) (DNS/allowlist failure), openjdk.org/jeps/401 (proxy 403), api.github.com (403) and YouTrack (not attempted). The Valhalla/JEP 401 delivery status and Quarkus's own Kotlin plugin guidance are **UNVERIFIED**. Allowing quarkus.io and openjdk.org in the session's network settings would close these gaps.
