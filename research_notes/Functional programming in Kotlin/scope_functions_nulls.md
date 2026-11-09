# Kotlin scope functions (let, run, with, apply, also, takeIf/takeUnless) and null handling as a functional pattern

Research date: 2026-11-09. Target: Kotlin 2.4.21 (the course version). Stdlib signatures were read from the `v2.4.21` tag of `JetBrains/kotlin` and compared with `v2.4.0`, `v2.3.x`, `v2.2.0` and `master`. Kotlin docs were read from the markdown sources of `JetBrains/kotlin-web-site` (the files kotlinlang.org is built from), and the two main pages were also fetched live from kotlinlang.org.

Access limits in this session: arrow-kt.io, detekt.dev, jetbrains.com (Inspectopedia), jetbrains.com.cn and kt.academy were blocked by the session's network policy. Arrow and detekt were therefore read from their GitHub sources instead. IntelliJ inspection facts come from search-result snippets only, and are marked that way. Running a downloaded Kotlin 2.4.21 compiler was blocked by the session's permission policy. So the "expected outcome" lines in the Teaching notes are worked out from the verified stdlib source and language docs. None of them was executed.

---

## Q1. Exact definitions in the stdlib source: receiver vs argument, return value, extension or not, contracts, inline

### Takeaway
All five scope functions (plus the non-extension `run`) are `inline`, `@InlineOnly` one-liners, and each one declares `callsInPlace(block, EXACTLY_ONCE)`. They differ on only two axes. The first is whether the object is the lambda's receiver (`this`) or its argument (`it`). The second is whether the call returns the lambda result or the object itself. The EXACTLY_ONCE contract is what lets you assign a `val` inside the lambda. In 2.4.21 all six are also `@IgnorableReturnValue`, which matters for the new unused-return-value checker. `takeIf`/`takeUnless` have the same contract but are *not* ignorable.

### Cited Findings

**Verbatim 2.4.21 signatures (KDoc stripped)** — [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)

```kotlin
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <R> run(block: () -> R): R {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block()
}

@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> T.run(block: T.() -> R): R {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block()
}

@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> with(receiver: T, block: T.() -> R): R {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return receiver.block()
}

@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T> T.apply(block: T.() -> Unit): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    block()
    return this
}

@kotlin.internal.InlineOnly
@SinceKotlin("1.1")
@IgnorableReturnValue
public inline fun <T> T.also(block: (T) -> Unit): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    block(this)
    return this
}

@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> T.let(block: (T) -> R): R {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block(this)
}

@kotlin.internal.InlineOnly
@SinceKotlin("1.1")
public inline fun <T> T.takeIf(predicate: (T) -> Boolean): T? {
    contract { callsInPlace(predicate, InvocationKind.EXACTLY_ONCE) }
    return if (predicate(this)) this else null
}

@kotlin.internal.InlineOnly
@SinceKotlin("1.1")
public inline fun <T> T.takeUnless(predicate: (T) -> Boolean): T? {
    contract { callsInPlace(predicate, InvocationKind.EXACTLY_ONCE) }
    return if (!predicate(this)) this else null
}
```
(Contract blocks are collapsed onto one line here; in the source each is a multi-line `contract { ... }`.) The file is `@file:JvmName("StandardKt")` in `package kotlin` — [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)

- **KDoc one-liners from the same file.** `run(block)`: "Calls the specified function [block] and returns its result." `T.run`: "...with `this` value as its receiver and returns its result." `with`: "...with the given [receiver] as its receiver and returns its result." `apply`: "...with `this` value as its receiver and returns `this` value." `also`: "...with `this` value as its argument and returns `this` value." `let`: "...with `this` value as its argument and returns its result." `takeIf`: "Returns `this` value if it satisfies the given [predicate] or `null`, if it doesn't." — [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)
- **What the signatures encode.** The receiver-style functions take `T.() -> R` or `T.() -> Unit`, a function type with receiver, so the object is `this`. The argument-style functions take `(T) -> R` or `(T) -> Unit`, so the object is `it`. `apply` and `also` take a Unit-returning block and `return this`. `let`, `run` and `with` return `R`, the block's result. `with` is the only one that is not an extension: it takes `receiver: T` as an ordinary parameter. — [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)
- **`@IgnorableReturnValue` history.** It is present on all six scope functions in v2.3.0, v2.3.20, v2.4.0, v2.4.20 and v2.4.21, and absent in v2.2.0. `takeIf` and `takeUnless` never carry it. This was checked by diffing the tagged files. — [Standard.kt @ v2.2.0](https://github.com/JetBrains/kotlin/blob/v2.2.0/libraries/stdlib/src/kotlin/util/Standard.kt), [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)
- **Change on `master` after 2.4.21.** On `master` (fetched 2026-11-09), `run`, `T.run`, `with` and `let` have dropped `@IgnorableReturnValue` and instead declare `returnsResultOf(block)` in their contracts. `apply` and `also` keep `@IgnorableReturnValue`. Nothing else in the file differs from v2.4.21. — [Standard.kt @ master](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/util/Standard.kt)
- **What `returnsResultOf` is.** Kotlin 2.4.0 "introduces a new Experimental `returnsResultOf()` contract to improve the unused return value checker". It "enables the checker to distinguish between unused results that can be ignored and meaningful unused results from higher-order functions that return the result of a lambda, such as the `let` scope function." — [What's new in Kotlin 2.4.0](https://kotlinlang.org/docs/whatsnew24.html)
- **Docs example for `returnsResultOf`.** With a `customLet` that declares `returnsResultOf(block)`, `packageName?.customLet { builder.append(it) }` is not reported, "because the return value of append() can be ignored". `packageName?.customLet { "kotlin.$it" }` is reported "because the returned string is unused". Using the contract needs `-Xallow-returns-result-of` and "produces pre-release binaries that Kotlin compiler versions earlier than 2.4.0 can't read." — [Unused return value checker](https://kotlinlang.org/docs/unused-return-value-checker.html)
- **What the checker is.** Kotlin 2.3.0 introduced it (Experimental). It "warns you whenever an expression returns a value other than `Unit` or `Nothing` and isn't passed to a function, checked in a condition, or otherwise used." It is off by default (`-Xreturn-value-checker=disable`). `check` reports ignored results from marked functions, "like most functions in the Kotlin standard library". `full` treats every function as marked. `@IgnorableReturnValue` suppresses reports. — [What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html); [Unused return value checker](https://kotlinlang.org/docs/unused-return-value-checker.html)
- **`callsInPlace` semantics (KDoc).** "Specifies that the function parameter [lambda] is invoked in place. This contract specifies that: 1. the function [lambda] can only be invoked during the call of the owner function, and it won't be invoked after that owner function call is completed; 2. (optionally) the function [lambda] is invoked the number of times specified by the [kind] parameter". `EXACTLY_ONCE`: "A function parameter will be invoked exactly one time." — [ContractBuilder.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/contracts/ContractBuilder.kt)
- **`val` initialisation inside an EXACTLY_ONCE lambda (official stdlib sample).** `val x: Int; callsInPlaceExactlyOnceContract { x = 10 }; assertEquals(10, x)` appears as the sample `valInitialization`. A separate AT_MOST_ONCE sample, `valPossibleInitialization`, shows the `val` can be assigned inside the lambda but is only read inside it. — [contracts samples @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/samples/test/samples/contracts/contracts.kt)
- **Inline lambdas and smart casts.** "Inline functions are treated as having an implicit `callsInPlace` contract. This means that any lambda functions passed to an inline function are called in place... the compiler knows that a lambda function can't leak references to any variables contained within its function body." The compiler uses this to decide whether captured variables can be smart-cast. The page's example is a local `var processor: Processor?` smart-cast inside an inline lambda. — [Type checks and casts](https://kotlinlang.org/docs/typecasts.html)
- **Why inlining matters for cost.** "Using higher-order functions imposes certain runtime penalties: each function is an object, and it captures a closure... Memory allocations (both for function objects and classes) and virtual calls introduce runtime overhead. But it appears that in many cases this kind of overhead can be eliminated by inlining the lambda expressions." — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)

**The official function-selection table** (verbatim from the docs) — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)

| Function | Object reference | Return value | Is extension function |
|---|---|---|---|
| `let` | `it` | Lambda result | Yes |
| `run` | `this` | Lambda result | Yes |
| `run` | - | Lambda result | No: called without the context object |
| `with` | `this` | Lambda result | No: takes the context object as an argument. |
| `apply` | `this` | Context object | Yes |
| `also` | `it` | Context object | Yes |

**The 2x2 view.** The docs present the six-row table above. This 2x2 is a condensation of it.

| | returns **lambda result** | returns **context object** |
|---|---|---|
| object is **`this`** (receiver) | `run`, `with` | `apply` |
| object is **`it`** (argument) | `let` | `also` |
| (no object) | non-extension `run` | — |

- **The docs' own framing.** "There are two main differences between each scope function: The way they refer to the context object. Their return value." Also: "`apply` and `also` return the context object. `let`, `run`, and `with` return the lambda result." — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)

### Inferences
- `apply` and `also` take a block typed `T.() -> Unit` or `(T) -> Unit`, so **whatever the block's last expression evaluates to is thrown away** (it is coerced to Unit). This is the mechanism behind the "apply/also to compute a value" bug: an `it.copy(...)` or a computed total inside the block is silently lost. (Derived from the signatures above.)
- `with(receiver: T, ...)` places no non-null bound on `T`. For a nullable value, `this` inside `with` is nullable, and there is no `with` equivalent of `?.`. The extension functions (`?.run`, `?.let`, `?.apply`, `?.also`) can be safe-called. (Derived from the signatures.)
- EXACTLY_ONCE is what makes `val x: T` followed by `foo.also { x = ... }` (or `run`, `let`, ...) compile. A user-written non-inline higher-order function without a contract cannot give that guarantee. That is why scope functions, unlike arbitrary lambdas, can stand in for statement blocks that initialise `val`s.
- `@InlineOnly` is a stdlib-internal annotation. Inference, not verified in this session: such functions are not meant to be called from Java as ordinary static methods (`StandardKt.let(...)`). Java engineers should not expect to call them from Java code.
- In 2.4.21, with `-Xreturn-value-checker=check` or `full`, a statement such as `payment.let { it.copy(status = CAPTURED) }` is **not** reported, because `let` is `@IgnorableReturnValue`. On `master` it would be reported, because of `returnsResultOf`. Ignoring the result of `takeIf { ... }` would be reported in 2.4.21, since `takeIf` is not ignorable and the stdlib is "marked". The `takeIf` part is inferred from the docs; it was not compiled.

### Gaps
- The KEEP for contracts could not be fetched; the old path 404'd. The `val`-initialisation behaviour is sourced from the official stdlib sample instead.
- The commit that moved `run`/`with`/`let` to `returnsResultOf` on `master` could not be identified: the GitHub API for this repo was not enabled in the session. So I cannot say which release (2.4.30? 2.5.0?) will ship it.
- I did not verify, by executing anything, how `@InlineOnly` looks in bytecode.

---

## Q2. Official guidance from kotlinlang.org: when to pick which

### Takeaway
The official docs give a short rule list. `let` is for non-null values and local scoping. `apply` is for configuration. `run` is for configuring and computing a result. The non-extension `run` is for a block where an expression is required. `also` is for additional effects. `with` is for grouping calls. The docs also warn against overuse, nesting and careless chaining. The Kotlin coding conventions add nothing beyond a pointer to that page. The Android Kotlin style guide says nothing about scope functions at all.

### Cited Findings
- **The "short guide for choosing scope functions" (verbatim).**
  - "Executing a lambda on non-nullable objects: `let`"
  - "Introducing an expression as a variable in local scope: `let`"
  - "Object configuration: `apply`"
  - "Object configuration and computing the result: `run`"
  - "Running statements where an expression is required: non-extension `run`"
  - "Additional effects: `also`"
  - "Grouping function calls on an object: `with`"
  — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **The overuse caution (verbatim).** "Although scope functions can make your code more concise, avoid overusing them: it can make your code hard to read and lead to errors. We also recommend that you avoid nesting scope functions and be careful when chaining them because it's easy to get confused about the current context object and value of `this` or `it`." — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`this` vs `it`.** For `this`: "if `this` is omitted, it can be hard to distinguish between the receiver members and external objects or functions. So having the context object as a receiver (`this`) is recommended for lambdas that mainly operate on the object's members by calling its functions or assigning values to properties." For `it`: "accessing the context object via `it` is better when the object is mostly used as an argument in function calls. `it` is also better if you use multiple variables in the code block." — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **Choosing by return value.** "You should consider carefully what return value you want based on what you want to do next in your code." `apply`/`also` "can be included into call chains as side steps". With `let`/`run`/`with` "you can ignore the return value and use a scope function to create a temporary scope for local variables." — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`let`.** It "can be used to invoke one or more functions on results of call chains"; it "is often used to execute a code block containing non-null values. To perform actions on a nullable object, use the safe call operator `?.` on it and call `let`". It can "introduce local variables with a limited scope"; name the parameter instead of `it`. A single-function body can be a reference: `.let(::println)`. Docs example: `val length = str?.let { println("let() called on $it"); processNonNullString(it); it.length }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`with`.** "We recommend using `with` for calling functions on the context object when you don't need to use the returned result... `with` can be read as 'with this object, do the following.'" It can also "introduce a helper object whose properties or functions are used for calculating a value". Example: `val firstAndLast = with(numbers) { "The first element is ${first()}," + " the last element is ${last()}" }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`run`.** It "does the same as `with` but it is implemented as an extension function. So like `let`, you can call it on the context object using dot notation"; it "is useful when your lambda both initializes objects and computes the return value." Docs example: `val result = service.run { port = 8080; query(prepareRequest() + " to port $port") }`, shown beside the `let` version that needs `it.` on every line. Non-extension `run` "lets you execute a block of several statements where an expression is required"; the example is `val hexNumberRegex = run { val digits = "0-9" ... }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`apply`.** "we recommend that you use it for code blocks that don't return a value and that mainly operate on the members of the receiver object. The most common use case for `apply` is for object configuration. Such calls can be read as 'apply the following assignments to the object.'" Example: `val adam = Person("Adam").apply { age = 20; city = "London" }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`also`.** It "is useful for performing some actions that take the context object as an argument. Use `also` for actions that need a reference to the object rather than its properties and functions, or when you don't want to shadow the `this` reference from an outer scope... read it as 'and also do the following with the object.'" Example: `return Random.nextInt(100).also { writeToLog("getRandomInt() generated value $it") }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **`takeIf`/`takeUnless`.** "These functions let you embed checks of an object's state in call chains... `takeIf` is a filtering function for a single object." "When chaining other functions after `takeIf` and `takeUnless`, don't forget to perform a null check or use a safe call (`?.`) because their return value is nullable." Examples: `val caps = str.takeIf { it.isNotEmpty() }?.uppercase()`, and `input.indexOf(sub).takeIf { it >= 0 }?.let { ... }`, which the docs show next to the equivalent plain `val index = ...; if (index >= 0) { ... }`. — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **Kotlin coding conventions.** The section "Scope functions apply/with/run/also/let" contains only: "Kotlin provides a set of functions to execute a block of code in the context of a given object... For the guidance on choosing the right scope function for your case, refer to Scope Functions." — [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- **Coding conventions on lambda parameters.** "In lambdas which are short and not nested, it's recommended to use the `it` convention instead of declaring the parameter explicitly. In nested lambdas with parameters, always declare parameters explicitly." — [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- **Android Kotlin style guide.** It does not mention scope functions (`let`/`apply`/`also`/`run`/`with`) at all. It "focuses primarily on the hard-and-fast rules that we follow universally, and avoids giving advice that isn't clearly enforceable (whether by human or tool)." — [Android Kotlin style guide](https://developer.android.com/kotlin/style-guide)

### Inferences
- The official guidance is **intent-based**: pick by what you want back and how the block refers to the object. It is not a rule about nullability. A good lesson framing is "the choice of function is a signal to the reader." For example, `apply` signals "this block only configures", `also` signals "side step, the main value flows through", and `let` signals "transform into something else".
- `with` versus `run` is mostly a choice between `with(x) { }` and `x.run { }`. The practical differentiator is that only `run` works with `?.` and in the middle of a call chain.

### Gaps
- *Kotlin in Action, 2nd ed.* and *Effective Kotlin* were not accessible (kt.academy was blocked by network policy; the books are paywalled). Their exact wording on scope functions is not captured here.

---

## Q3. Anti-patterns, their costs, and what tools and style guides say

### Takeaway
The costly patterns are about readability and semantics, not performance, since everything is inlined:
- nested receivers, where `this` and unqualified names resolve to the innermost receiver;
- trivial `let`s that hide a plain call;
- `?.let { } ?: run { }` used as if/else, where **both branches run if the `let` block yields `null`**;
- `apply` or `also` used to compute values, which are then silently discarded;
- long chains in which the reader loses track of `it`.

Detekt has dedicated rules for most of these (`UnnecessaryLet`, `NestedScopeFunctions`, `UnnecessaryApply`, `AlsoCouldBeApply`, plus the opposite-direction `UseLet`). Most are **not active by default**. IntelliJ ships "redundant let" and "scope function conversion" inspections.

### Cited Findings
- **The official warning against nesting and chaining**, already quoted: "avoid nesting scope functions and be careful when chaining them because it's easy to get confused about the current context object and value of `this` or `it`." — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- **Labeled `this`.** "The label tells the compiler which receiver to access. You can use the name of an enclosing class or extension function. For example, `this@foo` refers to the receiver of an enclosing extension function named `foo`." "Unlike a regular lambda, a lambda with receiver introduces a receiver into its scope." The docs show `this@stringLabel` alongside `this@User` inside a lambda. "The label doesn't call anything or change how the lambda works." — [This expressions](https://kotlinlang.org/docs/this-expressions.html)
- **Detekt `NestedScopeFunctions` KDoc (verbatim, main branch).** "Although the scope functions are a way of making the code more concise, avoid overusing them: it can decrease your code readability and lead to errors. Avoid nesting scope functions and be careful when chaining them: it's easy to get confused about the current context object and the value of this or it." Its noncompliant example is `first.apply { second.apply { b = a; c = b } }` ("Try to figure out, what changed, without knowing the details"). The compliant version is `first.b = this.a; second.c = first.b`. The config is `allowedDepth` (default 1) on main; v1.23.8 calls it `threshold` (default 1). The rule is not marked `@ActiveByDefault`. — [NestedScopeFunctions.kt (main)](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/NestedScopeFunctions.kt); [NestedScopeFunctions.kt v1.23.8](https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-complexity/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/complexity/NestedScopeFunctions.kt)
- **Detekt `UnnecessaryLet` KDoc (verbatim).** "`let` expressions are used extensively in our code for null-checking and chaining functions, but sometimes their usage should be replaced with an ordinary method/extension function call to reduce visual complexity."
  - Noncompliant: `a.let { print(it) }` ("can be replaced with `print(a)`"), `a?.let { it.plus(1) }` ("can be replaced with `a?.plus(1)`"), `a?.let { that -> that.plus(1) }?.let { it.plus(1) }` ("can be replaced with `a?.plus(1)?.plus(1)`"), `a?.let { 1.plus(1) }` ("can be replaced with `if (a != null) 1.plus(1)`").
  - Compliant: `a?.let { print(it) }`, `a?.let { it.plus(it) }`, `val b = a?.let { 1.plus(1) }`.
  - Not active by default.
  — [UnnecessaryLet.kt (main)](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UnnecessaryLet.kt); [UnnecessaryLet.kt v1.23.8 (style ruleset)](https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-style/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/style/UnnecessaryLet.kt)
- **Detekt `UnnecessaryApply` (active by default since 1.16.0).** "`apply` expressions are used frequently, but sometimes their usage should be replaced with an ordinary method/extension function call to reduce visual complexity." Noncompliant: `config.apply { version = "1.2" }` ("can be replaced with `config.version = "1.2"`"), and `config?.apply { println(version) }` ("`apply` can be replaced by `let`"). Compliant: a multi-assignment `config.apply { version = "1.2"; environment = "test" }`. — [UnnecessaryApply.kt (main)](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UnnecessaryApply.kt); [UnnecessaryApply.kt v1.23.8](https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-style/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/style/UnnecessaryApply.kt)
- **Detekt `AlsoCouldBeApply`.** "Detects when an `also` block contains only `it`-started expressions. By refactoring the `also` block to an `apply` block makes it so that all `it`s can be removed thus making the block more concise and easier to read." Noncompliant: `Buzz().also { it.init(); it.block() }`. Compliant: `Buzz().apply { init(); block() }`, and `return a.also { println(it) }`. Not active by default. — [AlsoCouldBeApply.kt (main)](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/AlsoCouldBeApply.kt)
- **Detekt `UseLet` (pushes the other way; not active by default).** "`if` expressions that either check for not-null and return `null` in the false case or check for `null` and returns `null` in the truthy case are better represented as `?.let {}` blocks." `if (x != null) { transform(x) } else null` becomes `x?.let { transform(it) }`. — [UseLet.kt (main)](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseLet.kt)
- **Detekt `UseRequireNotNull` / `UseCheckNotNull` (active by default since 1.21.0).** They flag `require(x != null)` and `check(x != null)` and suggest `requireNotNull(x)` and `checkNotNull(x)`. — [UseRequireNotNull.kt](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseRequireNotNull.kt); [UseCheckNotNull.kt](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseCheckNotNull.kt)
- **Detekt versions and rulesets.** The latest stable tag is **v1.23.8**; 2.0 exists only as `v2.0.0-alpha.0` to `alpha.6`, per `git ls-remote --tags`. In 1.23.8, `UnnecessaryLet`, `UnnecessaryApply`, `UseLet` and `AlsoCouldBeApply` live in the **style** ruleset and `NestedScopeFunctions` in **complexity**. On `main` (2.0 line) all of these sit in a new **standard-library** ruleset (`dev.detekt.rules.standardlibrary`). — [detekt repo](https://github.com/detekt/detekt); file paths as linked above
- **Coding conventions on returns in lambdas.** "Avoid using multiple labeled returns in a lambda. Consider restructuring the lambda so that it will have a single exit point. If that's not possible or not clear enough, consider converting the lambda into an anonymous function. Do not use a labeled return for the last statement in a lambda." — [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- **Coding conventions on nested lambdas.** "In nested lambdas with parameters, always declare parameters explicitly." — [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- **IntelliJ inspections (search-snippet level only; Inspectopedia pages could not be fetched).**
  - `ComplexRedundantLet`, "Redundant argument-based 'let' call": reported when the lambda parameter is only a qualifier in a call, e.g. `"1,2,3".let { it.split(',') }` → `"1,2,3".split(',')`.
  - `SimpleRedundantLet`, "Redundant receiver-based 'let' call": example `s?.let { it.length }`.
  - `ScopeFunctionConversion`, "Scope function can be converted to another one": converts among let/run/apply/also, e.g. `let` → `run`, dropping `it.`.
  - Other related inspection pages exist: `RedundantWith`, `RedundantElvisReturnNull`.
  — [Inspectopedia: ComplexRedundantLet](https://www.jetbrains.com/help/inspectopedia/ComplexRedundantLet.html); [SimpleRedundantLet](https://www.jetbrains.com/help/inspectopedia/SimpleRedundantLet.html); [ScopeFunctionConversion](https://www.jetbrains.com/help/inspectopedia/ScopeFunctionConversion.html); [RedundantWith](https://www.jetbrains.com/help/inspectopedia/RedundantWith.html); [RedundantElvisReturnNull](https://www.jetbrains.com/help/inspectopedia/RedundantElvisReturnNull.html)
- **Elvis semantics, the basis of the `?.let ?: run` bug.** "If the expression to the left of `?:` is not `null`, the Elvis operator returns it. Otherwise, the Elvis operator returns the expression to the right. The expression on the right-hand side is evaluated only if the left-hand side is `null`." — [Null safety](https://kotlinlang.org/docs/null-safety.html). Combined with "`let`, `run`, and `with` return the lambda result" — [Scope functions](https://kotlinlang.org/docs/scope-functions.html)

### Inferences
- **The `x?.let { A } ?: run { B }` bug.** The left side of `?:` is the *result of the `let` lambda*, not `x`. If `x != null` but `A`'s last expression is `null`, `B` runs as well. Typical culprits are a lookup returning `T?`, a `save()` returning `Id?`, or `map[key]`. A payments example is in the Teaching notes. The safe alternatives are `if (x != null) A else B` and `when`, or `?.also { }` when the non-null branch is purely a side effect, since `also` returns `x` itself, which is non-null.
- **Nested receivers.** Inside `a.apply { b.apply { foo = 1 } }`, an unqualified `foo` resolves to the innermost receiver that has a `foo`, falling back outward. So adding a property to `b`'s class later can silently retarget the assignment. The docs' `this@label` mechanism fixes reads and writes, but two nested `apply`s share the implicit label `@apply`, so you need custom labels (`outer@{ }`) or, better, no nesting. This is consistent with the this-expressions doc and the detekt example, but it was not compiled here.
- **Long `let` chains.** Each `?.let { }` rebinds `it`. A three-step chain makes the reader track three different `it`s. Arrow's docs make the same observation ("this quickly results in a lot of nested `?.let { }` blocks", see Q4). Better options are named parameters, local `val`s with early-return Elvis (`val x = a ?: return`), or extracted functions.
- **`also` to change state.** No official source forbids mutation inside `also`. The cost is reader expectation: the docs frame `also` as "additional effects" and "and also do the following", and detekt's `AlsoCouldBeApply` treats an `also` that only manipulates `it` as an `apply` in disguise. For an immutable data class, `also { it.copy(...) }` is a real bug, because the copy is discarded.
- **Replacing simple `if`s.** The tools disagree. `UseLet` (opt-in) prefers `x?.let { transform(it) }` over `if (x != null) transform(x) else null`. `UnnecessaryLet` suggests `if (a != null) ...` when `it` is unused. A defensible teaching rule: use `?.let` when the non-null value *flows into an expression*, and use `if`/smart-cast for control flow or multi-statement branches, especially on local `val`s where smart casts already work.
- **Performance.** Scope functions are inline (Q1), so "they allocate lambdas" is not a valid argument against them. The cost is cognitive.

### Gaps
- The Inspectopedia pages (default severity, exact wording, and whether `NestedLambdaShadowedImplicitParameter` still exists in the K2 plugin) could not be fetched: jetbrains.com is blocked. Treat the IntelliJ details above as unverified beyond search snippets.
- I found no official source that names `?.let {} ?: run {}` as an anti-pattern explicitly. The bug follows from the documented semantics but was not executed here.
- The *Effective Kotlin* item text could not be checked. A search snippet suggested an item titled "Consider referencing receivers explicitly", but only from an unauthorised copy, so it is not cited.
- I did not identify which detekt 2.0 alpha introduced the `standard-library` ruleset.

---

## Q4. Null handling as a functional pattern: `?.`, `?:`, `?.let`, `takeIf`, `requireNotNull`/`checkNotNull`, `filterNotNull`/`mapNotNull`, Optional/Option, smart casts and contracts

### Takeaway
Kotlin's nullable type `T?` is a compile-time union, not a wrapper. `?.` is the "map", `?:` is the "getOrElse" (and it can `return` or `throw`), `?.let` is the "flatMap/map with a block", and `takeIf` is the "filter". Contracts on `requireNotNull`, `checkNotNull` and `isNullOrEmpty` feed smart casts. So idiomatic Kotlin almost never needs `java.util.Optional` or Arrow's `Option`. The exceptions Arrow itself names are nested nullability in generic code and libraries that forbid `null`, such as RxJava and Reactor.

### Cited Findings
- **Nullable types are not wrappers.** "At runtime, objects of nullable types and objects of non-nullable types are treated the same: A nullable type isn't a wrapper for a non-nullable type. All checks are performed at compile time. That means there's almost no runtime overhead for working with nullable types in Kotlin." — [Nullability in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-nullability-guide.html)
- **Safe call.** "Instead of throwing an NPE, if the object is `null`, the `?.` operator simply returns `null`." Chains like `bob?.department?.head?.name` return `null` if any link is `null`. For `person?.department?.head = managersPool.getManager()`: "if one of the receivers in the safe call chain is `null`, the assignment is skipped, and the expression on the right is not evaluated at all." — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **Elvis with `return`/`throw`.** "Since `throw` and `return` are expressions in Kotlin, you can also use them on the right-hand side of the Elvis operator." Example: `val parent = node.getParent() ?: return null`; `val name = node.getName() ?: throw IllegalArgumentException("name expected")`. — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **`!!`.** It "converts any value to a non-nullable type... if the value is `null`... results in an NPE". It is "particularly useful when you are confident that a value is not `null`... but the compiler cannot guarantee this". — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **`?.let`.** "To handle `null` values and perform operations only on non-null types, you can use the safe call operator `?.` together with the `let` function." Example: `item?.let { println(it) }`. — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **`as?`.** It "tries to cast a value to the specified type and returns `null` if the value is not of that type." — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **`filterNotNull`.** "If you have a collection of nullable elements and want to keep only the non-null ones, use the `filterNotNull()` function": `listOf(1, 2, null, 4).filterNotNull()` gives `[1, 2, 4]`. — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **Collection signatures.** `public fun <T : Any> Iterable<T?>.filterNotNull(): List<T>` ("Returns a list containing all elements that are not `null`."). `public inline fun <T, R : Any> Iterable<T>.mapNotNull(transform: (T) -> R?): List<R>` ("Returns a list containing only the non-null results of applying the given [transform] function to each element in the original collection."). `public inline fun <T, R : Any> Iterable<T>.firstNotNullOfOrNull(transform: (T) -> R?): R?` (`@SinceKotlin("1.5")`). — [_Collections.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)
- **Smart-cast prerequisites (verbatim table rows).** "Smart casts work only when the compiler can guarantee that the variable won't change between the check and its usage."
  - "`val` local variables: Always, except local delegated properties."
  - "`val` properties: If the property is private, internal, or if the check is performed in the same module where the property is declared. Smart casts can't be used on open properties or properties that have custom getters."
  - "`var` local variables: If the variable is not modified between the check and its usage, is not captured in a lambda that modifies it, and is not a local delegated property."
  - "`var` properties: Never, because the variable can be modified at any time by other code."
  — [Type checks and casts](https://kotlinlang.org/docs/typecasts.html)
- **`if`-based smart cast.** `val l = if (b != null) b.length else -1` works through a smart cast, "only... when the compiler can guarantee that `b` doesn't change between the check and its usage". — [Null safety](https://kotlinlang.org/docs/null-safety.html)
- **Preconditions with contracts (2.4.21 source).**
  - `require(value: Boolean, lazyMessage)` has `contract { returns() implies value }` and throws `IllegalArgumentException`.
  - `requireNotNull(value: T?, lazyMessage): T` has `contract { returns() implies (value != null) }`, throws `IllegalArgumentException`, and is `@IgnorableReturnValue`.
  - `checkNotNull(value: T?, lazyMessage): T` has the same contract, throws `IllegalStateException`, and is `@IgnorableReturnValue`.
  — [Preconditions.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Preconditions.kt)
- **`isNullOrEmpty` contract.** `public inline fun CharSequence?.isNullOrEmpty(): Boolean { contract { returns(false) implies (this@isNullOrEmpty != null) } ... }`. — [Strings.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/text/Strings.kt)
- **Arrow's position: few cases need `Option`.** "Since Kotlin already has nullable types, why do we need Arrow's `Option` type? There are only **a few** cases where you should use `Option` instead of nullable types, and one is the _nested nullability_ problem." Example: `fun <A> List<A>.firstOrElse(default: () -> A): A = firstOrNull() ?: default()` returns `-1` for `listOf(null, 2, 3)`, where `null` was expected, because `firstOrNull()` conflates "empty" with "first element is null". The fix uses `firstOrNone()` with `Some`/`None`. The other case: "Some libraries such as RxJava and Project Reactor don't support nullable types in all their APIs... you can use `Option` to work around this problem." — [Arrow docs source: nullable-and-option.md](https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md)
- **Arrow's DSL against nested `?.let`.** "We typically do that by using `?.let { }`, but this quickly results in a lot of nested `?.let { }` blocks. Arrow offers `bind()` and `ensureNotNull` to get rid of this issue". Example: `fun sendEmail(params: QueryParameters): SendResult? = nullable { val userId = ensureNotNull(params.userId()); val user = findUserById(userId).bind(); val email = user.email.bind(); sendEmail(email) }`. — [Arrow docs source: nullable-and-option.md](https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md)
- **Kotlin docs on platform types.** Kotlin recognises nullability annotations from JetBrains (`org.jetbrains.annotations`), JSpecify (`org.jspecify.annotations`) and Eclipse when calling Java. — [Nullability in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-nullability-guide.html)

### Inferences
- **Mapping to Optional vocabulary for Java engineers.** `opt.map(f)` ≈ `x?.let(f)` or `x?.f()`. `opt.orElse(d)` ≈ `x ?: d`. `opt.orElseGet { }` ≈ `x ?: run { ... }`, which is also lazy, since the right side is evaluated only when the left is null. `opt.orElseThrow()` ≈ `x ?: throw ...` or `requireNotNull(x) { ... }`. `opt.filter(p)` ≈ `x?.takeIf(p)`. `opt.ifPresent(c)` ≈ `x?.let(c)` or `x?.also(c)`. `opt.flatMap(f)` ≈ `x?.let(f)` where `f` returns `T?`; nullable types flatten automatically, which is exactly the nested-nullability caveat Arrow describes.
- **Which tool for which job.** `requireNotNull` (IAE) and `checkNotNull` (ISE) are the "validate and smart-cast" tools: after `requireNotNull(cmd.cardToken)`, `cmd.cardToken` is smart-cast *if* the property is smart-castable per the table above. The returned non-null value works in any case. Prefer them over `!!` when the null is a caller error (`require`) or a state error (`check`), because they carry a message. Detekt enforces the `require(x != null)` → `requireNotNull(x)` variant by default.
- **Why `?.let` on a `var` property is legitimate.** `var` properties are never smart-castable, so `if (this.pendingRefund != null) process(this.pendingRefund)` does not compile without `!!`. `pendingRefund?.let { process(it) }` captures the value once. So does `val r = pendingRefund ?: return`, which is often more readable.
- **`takeIf` is eager.** Both the receiver and the predicate are evaluated (EXACTLY_ONCE) whether or not the result is used, so it is not a lazy `if`. Do not put side effects in the predicate.

### Gaps
- Kotlin's `java.util.Optional` interop extensions (e.g. `Optional<T>.getOrNull()` in `kotlin.jvm.optionals`) were not verified in this session; check the API docs before teaching them.
- The arrow-kt.io site could not be reached, so the public URL of the Arrow page is unverified. The source sits under `learn/typed-errors/wrappers/`, so the site URL may include `/wrappers/`. Cite the GitHub source if unsure.
- Arrow's docs were read from the `main` branch of `arrow-website`. Which Arrow release (1.2.x / 2.x) those docs track was not checked.

---

## Q5. The last-expression rule, `return@let`, and non-local returns from inline lambdas

### Takeaway
A lambda returns the value of its last expression. For `let`, `run` and `with` that value *is* the function's result. For `apply` and `also` it is discarded. Because scope functions are `inline`, a bare `return` inside their lambdas is a **non-local return**: it exits the enclosing *function*, not the lambda. `return@let value` exits just the lambda. Kotlin's conventions discourage multiple labeled returns and labeled returns on the last line.

### Cited Findings
- **Implicit return of the last expression.** "You can explicitly return a value from the lambda using the qualified return syntax. Otherwise, the value of the last expression is implicitly returned." `ints.filter { val shouldFilter = it > 0; shouldFilter }` is equivalent to `ints.filter { val shouldFilter = it > 0; return@filter shouldFilter }`. — [Lambdas](https://kotlinlang.org/docs/lambdas.html)
- **Bare `return` and inlining.** "In Kotlin, you can only use a normal, unqualified `return` to exit a named function or an anonymous function. To exit a lambda, use a label. A bare `return` is forbidden inside a lambda because a lambda cannot make the enclosing function `return`". "But if the function the lambda is passed to is inlined, the return can be inlined, as well." "Such returns (located in a lambda, but exiting the enclosing function) are called *non-local* returns." Example: `ints.forEach { if (it == 0) return true // returns from hasZeros }`. — [Inline functions](https://kotlinlang.org/docs/inline-functions.html)
- **Implicit labels.** "Often it is more convenient to use _implicit labels_, because such a label has the same name as the function to which the lambda is passed." Example: `forEach lit@{ if (it == 3) return@lit; print(it) }` — "local return to the caller of the lambda - the forEach loop". — [Returns and jumps](https://kotlinlang.org/docs/returns.html)
- **Conventions.** "Avoid using multiple labeled returns in a lambda... Do not use a labeled return for the last statement in a lambda." — [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- **`return` in expression bodies (2.3.0).** "In Kotlin 2.3.0, support for `return` statements in expression bodies with explicit return types is now enabled by default." This makes `fun fee(p: Payment): Long = p.let { if (...) return 0; ... }` legal on the course version. — [What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html)
- **No `crossinline` on scope-function lambdas.** None of the scope function parameters is marked `crossinline` or `noinline` (see the signatures in Q1), so non-local returns are allowed in all of them. — [Standard.kt @ v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)

### Inferences
- **The early return a Java engineer misreads.** In `payment?.let { if (it.isTest) return; ledger.post(it) }`, `return` leaves the whole enclosing function. The Java mental model ("return from this lambda") is wrong here. In a `Unit` function that is usually what was meant. In a value-returning function the compiler forces `return <value>`, which makes the non-local nature visible.
- **Where non-local returns help.** `val req = parse(body) ?: return badRequest()` and `val token = card?.token ?: return Declined("no token")` are idiomatic. They are cleaner than the same logic inside `?.let`, and they avoid indentation.
- **`return@let` versus restructuring.** `return@let` with a value works, but the conventions point toward a single exit point: make the last expression an `if`/`when` expression instead.
- **Silent discards.** Because `apply`/`also` lambdas are Unit-typed, a value-producing last line compiles and is thrown away. In `let`/`run` it becomes the result. This is the most common "habit" bug when someone swaps `let` ↔ `also` or `run` ↔ `apply` without thinking.

### Gaps
- I did not verify, by compiling, how Kotlin 2.4.21 diagnoses a bare `return` inside a *non-inline* lambda (exact error text). The docs only say "ERROR: cannot make `foo` return here".

---

## Verified URLs

Fetched and read in this session, either live or as the GitHub markdown source the site is built from:
- https://kotlinlang.org/docs/scope-functions.html (live fetch, plus source https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/scope-functions.md)
- https://kotlinlang.org/docs/null-safety.html (live fetch)
- https://kotlinlang.org/docs/coding-conventions.html (source: https://github.com/JetBrains/kotlin-web-site/blob/master/docs/topics/coding-conventions.md)
- https://kotlinlang.org/docs/inline-functions.html (source: docs/topics/inline-functions.md)
- https://kotlinlang.org/docs/lambdas.html (source: docs/topics/lambdas.md)
- https://kotlinlang.org/docs/returns.html (source: docs/topics/returns.md)
- https://kotlinlang.org/docs/typecasts.html (source: docs/topics/typecasts.md)
- https://kotlinlang.org/docs/this-expressions.html (source: docs/topics/this-expressions.md)
- https://kotlinlang.org/docs/unused-return-value-checker.html (source: docs/topics/unused-return-value-checker.md)
- https://kotlinlang.org/docs/whatsnew23.html (source: docs/topics/whatsnew/whatsnew23.md)
- https://kotlinlang.org/docs/whatsnew24.html (source: docs/topics/whatsnew/whatsnew24.md)
- https://kotlinlang.org/docs/java-to-kotlin-nullability-guide.html (source: docs/topics/jvm/java-to-kotlin-nullability-guide.md)
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt (also compared at v2.4.20, v2.4.0, v2.3.20, v2.3.0, v2.2.0 and master)
- https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/util/Standard.kt
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Preconditions.kt
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/contracts/ContractBuilder.kt
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/samples/test/samples/contracts/contracts.kt
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/text/Strings.kt
- https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt
- https://developer.android.com/kotlin/style-guide (live fetch; no scope-function content)
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UnnecessaryLet.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/NestedScopeFunctions.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UnnecessaryApply.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseLet.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/AlsoCouldBeApply.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseRequireNotNull.kt
- https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseCheckNotNull.kt
- https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-style/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/style/UnnecessaryLet.kt (and UseLet.kt, UnnecessaryApply.kt, AlsoCouldBeApply.kt in the same folder)
- https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-complexity/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/complexity/NestedScopeFunctions.kt
- https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md

Seen only as search results, not fetched (network-blocked); treat as unverified:
- https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.contracts/-contract-builder/returns-result-of.html
- https://www.jetbrains.com/help/inspectopedia/ComplexRedundantLet.html
- https://www.jetbrains.com/help/inspectopedia/SimpleRedundantLet.html
- https://www.jetbrains.com/help/inspectopedia/ScopeFunctionConversion.html
- https://www.jetbrains.com/help/inspectopedia/RedundantWith.html
- https://www.jetbrains.com/help/inspectopedia/RedundantElvisReturnNull.html
- https://detekt.dev/docs/rules/style (blocked; rule text was read from source instead)
- https://arrow-kt.io/learn/typed-errors/nullable-and-option/ (blocked; exact path unverified)

---

## Teaching notes

All code below is illustrative and was written for these notes. Each "expected outcome" is derived from the verified stdlib source and language docs above. **None was executed**, because the session could not run `kotlinc`. Run each demo once on Kotlin 2.4.21 before recording.

Shared demo model:
```kotlin
enum class Status { AUTHORIZED, CAPTURED, REFUNDED, DECLINED }
data class Money(val minor: Long, val currency: String)
data class Payment(val id: String, val amount: Money, val status: Status, val cardToken: String?)
class PaymentRequest { var amount: Money? = null; var merchantId: String = ""; var idempotencyKey: String = "" }
```

### Misconceptions to address explicitly
1. **"`let` is the null-check function."** `let` is just "call this block with `it` and give me its result". The *safe call* `?.` is what makes it a null check, and `?.run`, `?.also` and `?.apply` work the same way. Source: the `let` signature in Q1.
2. **"apply/also and let/run are interchangeable."** They differ in what they return. Swapping `let` → `also` changes the expression's value from the block result to the receiver. (Official table, Q1.)
3. **"`a?.let { X } ?: run { Y }` is an if/else."** It is not: Y also runs whenever X evaluates to `null` (Elvis semantics, Q3).
4. **"`return` inside `let` returns from the lambda."** It returns from the enclosing function, because the lambda is inline (Q5).
5. **"Scope functions cost a lambda allocation."** They are `inline`, so the lambda is inlined at the call site (Q1).
6. **"`with` works with nullables."** Inside `with(x)` with a nullable `x`, `this` is nullable, and there is no `?.with` (Q1 inference).
7. **"`takeIf` is lazy like `if`."** The receiver is computed first and the predicate always runs exactly once (Q1 contract).
8. **"Kotlin should use `Optional` for absent values."** Nullable types are compile-time only, with "almost no runtime overhead". Arrow itself recommends `Option` only for nested nullability and null-hostile libraries (Q4).
9. **"`!!` is fine when I'm sure."** The docs allow it, but `requireNotNull`/`checkNotNull` with a message give a precise exception type (IAE vs ISE) plus a contract-driven smart cast (Q4).

### Demos (with expected outcomes)
**D1: the `?.let ?: run` double-execution bug** (payments: duplicate posting)
```kotlin
class Ledger { val posted = mutableListOf<String>()
    fun post(p: Payment): String? = if (p.id in posted) null else { posted += p.id; "LP-${p.id}" } }  // null = already posted
fun settle(cached: Payment?, ledger: Ledger, fetch: () -> Payment): String? =
    cached?.let { ledger.post(it) } ?: run { println("cache miss -> fetching"); ledger.post(fetch()) }

val ledger = Ledger(); val p = Payment("p1", Money(1999, "EUR"), Status.CAPTURED, "tok")
println(settle(p, ledger) { p })   // LP-p1
println(settle(p, ledger) { p })   // prints "cache miss -> fetching" then null
```
Expected: on the second call the cached payment *is* present, but `post` returns `null` (duplicate). Elvis then runs the "cache miss" branch, which is the wrong log line plus a second posting attempt. Fix: `if (cached != null) ledger.post(cached) else ledger.post(fetch())`, or use `when`.

**D2: `also` with `copy` silently discards the update**
```kotlin
val captured = p.copy(status = Status.AUTHORIZED).also { it.copy(status = Status.CAPTURED) }
println(captured.status)  // AUTHORIZED
```
Expected: `AUTHORIZED`. `also`'s block is `(T) -> Unit`, so the copy is discarded and `also` returns the original. The same happens with `apply { copy(...) }`. Fix: `.let { it.copy(status = Status.CAPTURED) }`, or simply `.copy(...)`.

**D3: `apply` used to compute**
```kotlin
val total = listOf(p, p).apply { sumOf { it.amount.minor } }
println(total)            // prints the list, not 3998
```
Expected: `total` is the `List<Payment>`. With `val total: Long = ...` it fails to compile. Show this as "the type annotation catches it". Fix: `run { sumOf { ... } }` or just `sumOf`.

**D4: nested-receiver shadowing**
```kotlin
class Fx { var amount: Long = 0 }
class Form { var amount: Long = 0; val fx = Fx() }
val form = Form()
form.apply { fx.apply { amount = 500 } }
println("${form.amount} ${form.fx.amount}")  // 0 500
```
Expected: `0 500`. The unqualified `amount` binds to the innermost receiver (`Fx`). Step 2: delete `Fx.amount`, and change the print to `println(form.amount)`. The unchanged `amount = 500` line still compiles, but it now silently writes `form.amount` (output `500`). That is a refactor in one class changing the meaning of code in another. Fix: no nesting, or explicit `form.amount` / `fx.amount`. Detekt `NestedScopeFunctions` flags this.

**D5: `val` initialisation thanks to EXACTLY_ONCE**
```kotlin
val authCode: String
val auth = gatewayAuthorize(req).also { authCode = it.code }   // compiles
println(authCode)
```
Expected: it compiles and prints the code. Contrast with a hand-written `fun <T> myAlso(x: T, f: (T) -> Unit)` that is not inline and has no contract: assigning `authCode` inside it is a compile error. Then add `inline` + `contract { callsInPlace(f, InvocationKind.EXACTLY_ONCE) }` with `@OptIn(ExperimentalContracts::class)` to make it compile.

**D6: non-local return**
```kotlin
fun firstDeclined(ps: List<Payment>): Payment? { ps.forEach { if (it.status == Status.DECLINED) return it }; return null }
fun fee(p: Payment): Long = p.let { if (it.amount.minor == 0L) return 0; it.amount.minor * 29 / 1000 }
```
Expected: in `fee`, `return 0` exits `fee` itself. The expression-body form compiles only because Kotlin 2.3.0+ allows `return` in expression bodies with explicit return types. Show `return@let 0` as the local alternative, then refactor to a single `if` expression, per the coding conventions.

**D7: `takeIf` + Elvis as a guard**
```kotlin
fun refund(p: Payment): String {
    val refundable = p.takeIf { it.status == Status.CAPTURED } ?: return "not refundable: ${p.status}"
    return "refund ${refundable.id}"
}
```
Expected: `refund(p.copy(status = Status.AUTHORIZED))` returns `"not refundable: AUTHORIZED"`. Also compare it with the plain `if (p.status != Status.CAPTURED) return ...`, which is arguably clearer. Use this to discuss when `takeIf` earns its place: inside a chain, not as a replacement for a guard clause.

**D8: smart cast vs `var` property**
```kotlin
class Checkout { var pendingRefund: Money? = null
    fun process() { if (pendingRefund != null) send(pendingRefund) }  // compile error: var property can't smart-cast
}
```
Expected: a compile error, because `var` properties never smart-cast. Fixes: `pendingRefund?.let(::send)`, or `val r = pendingRefund ?: return; send(r)`.

**D9 (optional, Kotlin 2.4.21 specific): return-value checker.** With `-Xreturn-value-checker=full`, `p.takeIf { it.status == Status.CAPTURED }` as a bare statement should warn, because `takeIf` is not `@IgnorableReturnValue`. `p.let { it.copy() }` as a statement should *not* warn in 2.4.21, because `let` is `@IgnorableReturnValue`. Note that stdlib `master` replaces this with `returnsResultOf`, so future versions are expected to warn. Verify on 2.4.21 before teaching; this is inferred, not executed.

### Exercise ideas
1. **Classify and justify.** Give 10 one-liners from a payments codebase, such as `request.apply { ... }`, `auth.also { log(it) }` and `card?.let { tokenize(it) }`. For each, learners name what it returns and its type, and say whether a plain call, `if` or local `val` reads better.
2. **Refactor a `?.let` pyramid.** Start with three nested `?.let`s (merchant → feeSchedule → rate). Rewrite them twice: with early-return Elvis (`?: return`), and with a single safe-call chain where members allow it. Optionally add a third version with Arrow's `nullable { ensureNotNull(...); x.bind() }`.
3. **Find the bug.** Give a `?.let { repo.findById(it) } ?: run { create() }`. Learners write a test where `findById` returns null for an existing id, then fix it with `when`/`if`.
4. **Configure vs compute.** Build a `PaymentRequest` with `apply`, log it with `also`, and compute a risk score with `run`, in one chain. Then explain why swapping any two of them breaks either the types or the meaning.
5. **Detekt it.** Enable `UnnecessaryLet`, `NestedScopeFunctions`, `AlsoCouldBeApply` and `UseLet` in detekt 1.23.8, run it on a seeded file, and discuss each finding. Note that `UseLet` and `UnnecessaryLet` can pull in opposite directions.
6. **Contracts.** Write `inline fun <T> T.audited(block: (T) -> Unit): T` with an EXACTLY_ONCE contract. Show that `val` initialisation inside it compiles, then remove the contract and observe the error.
7. **Optional translation.** Translate a Java `Optional` pipeline (`map`/`filter`/`orElseThrow`) into `?.`, `takeIf` and `?: throw`/`requireNotNull`, and explain why the Kotlin version allocates nothing.

### Decision checklist for picking a scope function
1. **Do you need one at all?** A plain call, a safe call (`a?.b()`), an `if` on a local `val` (smart cast), or a local `val` with `?: return` is often clearer. Detekt `UnnecessaryLet`/`UnnecessaryApply` and the IntelliJ "redundant let" inspections exist because this is common.
2. **What should the expression evaluate to?**
   - The same object, so you can keep chaining or return it: `apply` (configure members) or `also` (side effect with the object as an argument).
   - Something new: `let` (object as argument), `run` (object as receiver, or no object at all), or `with` (receiver, not chained, not nullable).
3. **How does the block use the object?** Mostly its members, assignments or configuration: receiver (`apply`/`run`/`with`). Passed to other functions, or the outer `this` must stay visible: argument (`also`/`let`), and name the parameter if the block is more than one line.
4. **Is it nullable?** Use `?.let`/`?.run`/`?.also`/`?.apply`, never `with`. If you add `?: other`, check that the left block can never evaluate to `null`. If it can, use `if`/`when`.
5. **Is it a filter on one value?** Use `takeIf`/`takeUnless` followed by `?.` or `?:`, and keep the predicate side-effect free.
6. **Is it a side effect (logging, metrics, audit)?** Use `also`. If every line starts with `it.`, it is probably `apply`.
7. **Is it nested, longer than about 5 lines, or chained more than twice?** Stop. Extract a function or use named locals; the official docs and detekt `NestedScopeFunctions` both warn here.
8. **Is there an early exit?** Remember that a bare `return` inside the block leaves the enclosing function. Prefer `?: return` before the block over `return@let` inside it.
