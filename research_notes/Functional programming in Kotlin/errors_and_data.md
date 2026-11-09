# Functional error handling and data modelling in Kotlin (errors as values, sealed types, kotlin.Result, Arrow Either/Raise, immutable data)

Scope and method. These notes are current to 9 November 2026 and the course toolchain (Kotlin 2.4.21). Every runtime and compiler claim marked "Verified locally" comes from programs compiled and run in this session: Kotlin 2.4.21 (`KotlinVersion.CURRENT` printed `2.4.21`), Arrow `arrow-core` 2.3.0, kotlinx.coroutines 1.11.0, kotlinx-collections-immutable 0.5.2 and JDK 21, built with Gradle 9.8.2. The sources are at `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/fperr/src/main/kotlin/Main.kt`, `.../fperr/src/main/kotlin/Demo2.kt` and `.../fperr2/src/main/kotlin/Bad.kt` (the compile-error demos). The scratchpad belongs to this session only, so the essential code is reproduced below.

Network limits. In this session arrow-kt.io, medium.com (including elizarov.medium.com), blog.jetbrains.com, youtrack.jetbrains.com, fsharpforfunandprofit.com, swlaschin.gitbooks.io and slack-chats.kotlinlang.org could not be reached. Arrow's documentation was read from its official source repository on GitHub (`arrow-kt/arrow-website`, raw markdown). Roman Elizarov's article could not be read, so none of its wording is presented as verified (see Gaps under Q1).

---

## Q1. Errors as values vs exceptions: what problem it solves, and where exceptions still belong

### Takeaway
The Kotlin team's own documents separate two kinds of failure. Expected, domain-level failures (card declined, invalid amount) belong in the type, as nullable types or domain-specific (sealed) classes. Exceptions are kept for bugs, environment failures and unrecoverable conditions, which are handled centrally instead of at every call site. Kotlin has no checked exceptions, so a thrown exception is invisible in a function's signature. Errors-as-values make failure visible to the compiler and composable.

### Cited Findings
- Kotlin treats all exceptions as unchecked: "Kotlin treats all exceptions as unchecked by default. Unchecked exceptions simplify the exception handling process: you can catch exceptions, but you don't need to explicitly handle or declare them." — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- `@Throws` exists only for interop: "you can use the `@Throws` annotation. This annotation alerts callers about possible exceptions" (for Java, Swift and Objective-C callers). — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- The stdlib precondition functions map to exceptions for "situations where the program's flow cannot continue if specific conditions aren't met": `require()` for input validity (IllegalArgumentException), `check()` for state validity (IllegalStateException) and `error()` for an illegal state (IllegalStateException). — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- `throw` is an expression of type `Nothing`, "a built-in type that is a subtype of all other types, also known as the bottom type". This is what lets `val s: String = person.name ?: fail("Name required")` type-check. — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- The docs point to null-returning variants as the safe alternative to common exceptions, for example "use a safer alternative, such as the `getOrNull()` function", along with `firstOrNull()` and `toIntOrNull()`. — [Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)
- The Kotlin team's stdlib design notes (KEEP for `Result`, "Style and exceptions") say: "Use nullable types or domain-specific classes to represent failures that need specific handling." Their example is a `sealed class FindUserResult` with `Found`, `NotFound` and `MalformedName`. Exceptions are described (paraphrased by the fetch tool) as being for failures that don't need handling at each call site, such as bugs, environment problems and out-of-memory, and are typically handled centrally. — [KEEP: Result (stdlib/result.md)](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
- The 2025–26 rich-errors motivation document from the Kotlin language team (KEEP-0441, authors Michail Zarečenskij and Roman Venediktov) asks whether exceptions are going away and answers: "Definitely not. Exceptions remain an important part of the language." It expects them to be used "mainly for unrecoverable errors and non-local handling", and its key takeaways say exceptions "should be used for unrecoverable cases." — [KEEP-0441 Rich Errors: Motivation and Rationale](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md)
- Arrow draws the same line. A logical failure is "a situation not deemed as successful in your domain" (for example, user not found). Real exceptions are technical problems that are "truly exceptional", such as a dropped database connection. "We advocate for making this distinction clear in the types, and leave exceptions only for exceptional cases." — [Arrow docs: Working with typed errors (source)](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)
- Typed errors make "explicit in the signature (or _type_) the potential errors that may arise." — [Arrow docs: Working with typed errors (source)](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)
- Railway-oriented programming (Scott Wlaschin, the conceptual source). Each step is a "switch" function with a success track and a failure track. Two-track output cannot feed a one-track input directly. `bind` adapts a switch so it takes two-track input: on success it runs the function, on failure it passes the failure along unchanged. `map` lifts a one-track function onto two tracks. Wlaschin also wrote a follow-up post, "Against Railway-Oriented Programming", warning against overuse. (Search-result summary only; the site was unreachable.) — [Railway Oriented Programming (fsharpforfunandprofit.com)](https://fsharpforfunandprofit.com/rop/); [Recipe for a functional app, part 2](https://fsharpforfunandprofit.com/posts/recipe-part2/)

### Inferences
- For a Java engineer, the pitch is: Kotlin removed checked exceptions, so nothing in the type system tells you `charge()` can fail. A sealed error type or `Either<PaymentError, Receipt>` puts that information back, with exhaustive `when` checking instead of `throws` clauses, and the failure composes through `map`/`bind` instead of nested try/catch.
- Rule of thumb consistent with all three sources (Kotlin docs, the Result KEEP, KEEP-0441 and Arrow):
  - expected and actionable by the caller → a value (nullable, sealed type, `Either`)
  - a bug or broken invariant → `require`/`check`/`error`, i.e. an exception
  - infrastructure or environment failure you cannot handle locally → an exception, caught at the edge (HTTP handler, message consumer), or converted to a value at the adapter boundary if the domain has a meaningful response (for example, "payment provider unavailable → retry later")

### Gaps
- **Roman Elizarov, "Kotlin and Exceptions"** (expected URL https://elizarov.medium.com/kotlin-and-exceptions-8062f589d07, Medium; the brief says 2020). The article could not be fetched (medium.com blocked here). A gist copy found via search returned 404. Search results only gave second-hand summaries: exceptions are mainly for logic errors and bugs and should bubble up to central handling, while expected failures are returned as values, as in `toIntOrNull() ?: default`. I could not verify its exact wording, the "dual-use API" terminology often attributed to it, or its exact publication date. The lesson writer should verify these from the original before quoting. The Kotlin-team positions above (Result KEEP, KEEP-0441) are verified, citable substitutes.
- Wlaschin's ROP pages and "Against Railway-Oriented Programming" could not be fetched. The concepts come from search-result summaries of his pages. His specific list of reasons against overuse is unverified.

---

## Q2. Modelling errors in plain Kotlin: sealed interfaces/classes, data classes, exhaustive `when`, a hand-written Result/Either

### Takeaway
A sealed interface of data classes and data objects models a closed set of payment failures. The compiler checks `when` over it for exhaustiveness: add a new failure case and every non-exhaustive `when` expression becomes a compile error. A hand-written `Outcome<E, A>` with `map`/`andThen` is about 10 lines and already gives railway-style composition.

### Cited Findings
- Definition: "Sealed classes and interfaces provide controlled inheritance of your class hierarchies. All direct subclasses of a sealed class are known at compile time." "No other subclasses may appear outside the module and package within which the sealed class is defined." "Direct subclasses of sealed classes and interfaces must be declared in the same package." — [Kotlin docs: Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)
- Exhaustiveness: "The `when` expression, used with a sealed class, allows the Kotlin compiler to check exhaustively that all possible cases are covered. In such cases, you don't need to add an `else` clause". The docs' own examples include a sealed `Error`/`IOError` hierarchy and `sealed class ApiResponse { data class UserSuccess(...); data object UserNotFound; data class Error(val message: String) }`. — [Kotlin docs: Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)
- The docs' rationale for sealed error hierarchies: "with a sealed hierarchy of error classes, library authors can be sure that they know all the possible error types and that other error types can't appear later." — [Kotlin docs: Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)
- **Verified locally (Kotlin 2.4.21):** with `sealed interface PaymentError { InvalidAmount; CardExpired; FraudSuspected }` and a `when` expression covering only the first two, compilation fails with:
  `'when' expression must be exhaustive. Add the 'is FraudSuspected' branch or an 'else' branch.` — local compile of `fperr2/src/main/kotlin/Bad.kt`
- **Verified locally:** this hand-written type and pipeline compile and run on 2.4.21:
  ```kotlin
  sealed interface Outcome<out E, out A> {
      data class Ok<A>(val value: A) : Outcome<Nothing, A>
      data class Err<E>(val error: E) : Outcome<E, Nothing>
  }
  inline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =
      when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }
  inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
      when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }

  sealed interface PayErr { data class Invalid(val why: String) : PayErr; data object Declined : PayErr }
  data class Req(val amountMinor: Long, val currency: String)
  fun validateReq(r: Req): Outcome<PayErr, Req> = if (r.amountMinor > 0) Outcome.Ok(r) else Outcome.Err(PayErr.Invalid("amount<=0"))
  fun authoriseReq(r: Req): Outcome<PayErr, String> = if (r.amountMinor < 10_000) Outcome.Ok("auth-1") else Outcome.Err(PayErr.Declined)
  fun captureAuth(auth: String): Outcome<PayErr, String> = Outcome.Ok("cap-of-$auth")
  fun pay(r: Req) = validateReq(r).andThen(::authoriseReq).andThen(::captureAuth).map { it.uppercase() }
  ```
  Output: `Ok(value=CAP-OF-AUTH-1)` for `Req(500,"EUR")`, `Err(error=Invalid(why=amount<=0))` for `Req(-1,"EUR")` and `Err(error=Declined)` for `Req(50_000,"EUR")`. Covariance (`out E, out A`) together with `Nothing` is what lets `Err` be returned unchanged (`is Outcome.Err -> this`) without re-wrapping. — local run, `Demo2.kt`

### Inferences
- `andThen` is Wlaschin's `bind` ("flatMap"), and `map` is his lift for one-track functions. Writing it by hand once is the best way to demystify `Either` before introducing Arrow.
- Prefer `sealed interface` for error roots. A case can implement several sealed interfaces, for example a `CardExpired` that is both a `ValidationError` and an `AuthorisationError`, and interfaces carry no constructor state. Use `data object` for cases without payload so `toString` and `equals` are sensible.
- Exhaustive `when` *expressions* are what gives the "new error case breaks the build" property. A `when` used as a statement with an `else` branch silently absorbs new cases, so teach "no `else` on sealed types".

### Gaps
- I did not verify whether non-exhaustive `when` *statements* over sealed types are an error or a warning in Kotlin 2.4. Only the expression form was tested.

---

## Q3. kotlin.Result and runCatching: purpose, API, pitfalls, and the return-type restriction history

### Takeaway
`kotlin.Result<T>` was designed for coroutine machinery and for capturing generic failures, not for domain errors. Its error type is always `Throwable`, and the design notes say so explicitly. `runCatching` catches every `Throwable`, including `CancellationException` (breaking coroutine cancellation) and JVM `Error`s such as `OutOfMemoryError` and `StackOverflowError`. All of this was verified locally on 2.4.21. The pre-1.5 ban on returning `Result` was lifted in Kotlin 1.5.

### Cited Findings
- **What it is:** a discriminated union of a success value or a failure holding a `Throwable`, implemented as a `@JvmInline value class`, added in Kotlin 1.3. The primary motivation was `Continuation.resumeWith(result: Result<T>)`. Other listed use cases: capturing per-task outcomes of parallel async work, bulk failure handling with `map`/`mapCatching`, and chaining `onSuccess`/`onFailure`. — [KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
- **What it is not for:** "The `Result` class is not designed to represent domain-specific error conditions." Its purpose is to "capture generic failures of Kotlin functions for their latter processing." — [KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
- KEEP-0441 calls `Result` "quite specialized and was designed mainly for coroutine machinery", notes it "is not a sealed class" and has a single type parameter, so the error type can't be expressed. — [KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md)
- **Restriction history:** before Kotlin 1.5, `Result<T>` could not be the direct return type of a function or the type of a property (`fun foo(): Result<Int>` was an error), and `?.`, `?:` and `!!` were disallowed on it. It was allowed inside containers (`List<Result<Int>>`) and as a parameter type. The stated rationale was to keep room for future semantic changes, for example language integration. The KEEP later records: "We have reached a decision of not following this road for a foreseeable future". In Kotlin 1.5 the restrictions were lifted: functions can return `Result`, and the null-safety operators work on `Result` types. — [KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
- **runCatching contract:** "Calls the specified function `block` and returns its encapsulated result if invocation was successful, catching any `Throwable` exception that was thrown from the `block` function execution and encapsulating it as a failure." It has two overloads, `runCatching(block)` and `T.runCatching(block)`, both since 1.3. The API page does not mention `CancellationException`. — [Kotlin API: runCatching](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html)
- **The coroutines pitfall is a long-standing open issue:** kotlinx.coroutines #1814, "Provide a `runCatching` that does not handle a `CancellationException` but re-throws it instead", opened 18 Feb 2020 and still **open**. Its example writes to a database after the scope was cancelled. Maintainers asked for justification and use cases ("What are the use-cases for `runCatching` in an application code?", elizarov). No coroutine-aware `runCatching` has been added. — [kotlinx.coroutines issue #1814](https://github.com/Kotlin/kotlinx.coroutines/issues/1814)
- **Verified locally: runCatching swallows cancellation.** In `launch { val r = runCatching { delay(1_000) }; ... }`, cancelled after 50 ms, the coroutine printed:
  ```
  runCatching returned: isFailure=true ex=JobCancellationException
  isActive after swallow = false
  charging card anyway (non-suspending code keeps running)
  next suspension point throws: JobCancellationException
  ```
  So code after the swallowed cancellation keeps running until the next suspension point. In a payments service that means side effects such as charging or writing a ledger can run after the request was cancelled. — local run, `Main.kt` `demoCancellation`
- **Verified locally: timeouts too.** `runCatching { withTimeout(10) { delay(1_000) } }` yields a failure holding `TimeoutCancellationException`, and `is CancellationException` is `true`. A timeout therefore looks like an ordinary failure to code that inspects the `Result`. — local run
- **Verified locally: Errors are caught.** `runCatching { throw OutOfMemoryError("simulated") }.isFailure == true`. Infinite recursion inside `runCatching` returns `Failure(StackOverflowError)`. — local run, `demoErrors`
- **Verified locally: Result API behaviour** (`parseAmount(s) = runCatching { s.toLong() }`):
  - `parseAmount("x")` → `Failure(java.lang.NumberFormatException: For input string: "x")`
  - `getOrElse { -1 }` → `-1`; `getOrNull()` → `null`; `recover { 0 }` → `Success(0)`
  - `map { it * 100 }` on `"12"` → `Success(1200)`
  - `fold(onSuccess = …, onFailure = …)` → handled both branches
  - `getOrThrow()` on failure rethrows the original `NumberFormatException`
  - **`map` with a throwing lambda rethrows** (`map RETHREW: boom in map`), while **`mapCatching` captures** → `Failure(IllegalStateException: boom)`. The stdlib has the same pairing for `recover`/`recoverCatching`; that pair was not tested here. — local run, `demoResultApi`
- **Verified locally, a cancellation-safe wrapper** that a lesson can show as the fix:
  ```kotlin
  inline fun <R> runCatchingCancellable(block: () -> R): Result<R> =
      runCatching(block).onFailure { if (it is CancellationException) throw it }
  ```
  With it, the cancelled job did not run the code after the call: `job.isCancelled=true, log=[]`. — local run, `Demo2.kt`

### Inferences
- Teach `Result` as "a typed `try/catch` for foreign code", useful at adapter edges (wrapping a JDK or HTTP client call) and for collecting per-item outcomes of parallel work. It is not the return type of domain functions, because `Result<Receipt>` says nothing about *which* payment failures can happen.
- The wrapper above still swallows `Error`s. A stricter version would also rethrow `Error`, which mirrors what Arrow does (Q4).
- Because `map` doesn't catch, chaining `runCatching { … }.map { … }` gives inconsistent safety. Teach the `*Catching` variants explicitly.

### Gaps
- The kotlinlang.org coroutines page "Cancellation and timeouts" (https://kotlinlang.org/docs/cancellation-and-timeouts.html) returned no readable content to the fetch tool, and the old GitHub path for its source returned 404. So I have no verified quote from the official docs on "don't swallow CancellationException". Use the issue above plus the local demo as evidence.
- I did not verify the exact Kotlin 1.5 release-notes wording for lifting the restriction. The KEEP update section is the source used.

---

## Q4. Arrow (arrow-kt.io): versions and status in 2026, Either, the Raise DSL, Option vs nullable, accumulating errors; plus the Kotlin "Rich Errors" proposal status

### Takeaway
Arrow is actively maintained on the 2.x line. Latest is **2.3.0 (26 Oct 2026)**, plus **2.3.0.1 (27 Oct 2026)**, an emergency compatibility release for IntelliJ 2026.3. Its alphas moved to Kotlin 2.4.21. Its core error-handling model is the **Raise DSL**: `either { … }`, `ensure`, `ensureNotNull`, `bind()`, `raise`, `recover` and `catch`. `Either` is the wrapper type; Raise is the composition context. Error accumulation uses `zipOrAccumulate`/`mapOrAccumulate` (stable API) and an `accumulate { ensureOrAccumulate(...) }` DSL, which is still `@ExperimentalRaiseAccumulateApi` in 2.3.0. Arrow itself says to prefer nullable types over `Option`. Kotlin's **Rich Errors (error union types) has NOT shipped**: it is "Exploration and design" / "Design review", and the 2.4.21 compiler rejects the syntax.

### Cited Findings: Arrow versions and status
- arrow-core publish dates on Maven Central: **2.2.2 on 2026-03-03**, **2.2.3 on 2026-06-04**, **2.3.0 on 2026-10-26**, **2.3.0.1 on 2026-10-27**. Alphas 2.3.0-alpha.1…alpha.8 are also listed. — [Maven Central: io.arrow-kt/arrow-core metadata](https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/maven-metadata.xml); directory listings, e.g. [arrow-core/2.3.0/](https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/2.3.0/)
- 2.3.0.1: "Emergency release for compatibility with IntelliJ 2026.3" (Optics plugin fix). 2.3.0 highlights: Arrow Optics compiler plugin, "Add AccumulateContext utilities for error accumulation in Arrow Core Context", "Add IgnorableReturnType to additional accumulate APIs" (wording as relayed by the fetch tool), "Support for collection literals", wasmWasi target, Ktor QUERY verb, "Compatibility with result4K 3.0". 2.3.0-alpha.6 (08 Oct) says: "Update to Kotlin 2.4.21". No Arrow API deprecations or breaking changes are listed for 2.3.0. — [GitHub: arrow-kt/arrow releases](https://github.com/arrow-kt/arrow/releases)
- Arrow 2.0 was announced 5 Dec 2024 (blog URL dated 2024/12/05). A search summary of that post says migration "should be hassle-free if your code compiled in 1.2.x without any deprecation warnings" (not read directly; arrow-kt.io was unreachable). Arrow 2.2.2 (March 2026) is described as mainly bug fixes, plus a new `arrow-raise-ktor-server-resources` module (search summary). — [Arrow 2.0 blog post](https://arrow-kt.io/community/blog/2024/12/05/arrow-2-0/); [Arrow 2.2.2 blog post](https://arrow-kt.io/community/blog/2026/03/04/arrow-2-2-2/)
- **Verified from the 2.3.0 jar (javap):** `arrow.core.raise.context` exists (file facade `RaiseContextualKt`) and provides context-parameter versions of `either`, `raise`, `ensure`, `ensureNotNull`, `bind` and `accumulate`. In `RaiseKt__RaiseAccumulateKt`, the functions `accumulate`, `accumulating`, `ensureOrAccumulate` and `ensureNotNullOrAccumulate` carry `@ExperimentalRaiseAccumulateApi`. `zipOrAccumulate` has overloads for up to 9 validations, in two families: `Raise<NonEmptyList<E>>`, or `Raise<E>` plus a `(E, E) -> E` combine function. — local inspection of `arrow-core-jvm-2.3.0.jar`
- **Verified locally:** a context-parameter Raise function compiles on Kotlin 2.4.21 **without any compiler flag**:
  ```kotlin
  context(_: Raise<PayErr>)
  fun checkCurrency(c: String): String { arrow.core.raise.context.ensure(c == "EUR") { PayErr.Invalid("currency $c") }; return c }
  either { checkCurrency("USD") }   // Either.Left(Invalid(why=currency USD))
  ```
  This is consistent with Kotlin's feature table: context parameters "Available since: 2.2.0, Stable since 2.4.0". — [Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html); local run
- Note that the Arrow docs lag here. The "Working with typed errors" page still says "In the future, context parameters should allow us to define the function as follows" and uses `Raise<E>` as an extension receiver. — [Arrow docs source](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)

### Cited Findings: Either and the Raise DSL
- `Either<E, A>` represents the error as a value. `Raise<E>` is a computation context in which logical failures are raised. The docs recommend building results with a runner (`either { }`) and then `.bind()` or `raise` (the "Raise DSL"). `raise(e)` fails; `ensure(cond) { e }` raises a lazily computed error when the predicate is false (like `require`); `ensureNotNull(x) { e }` raises on null and smart-casts otherwise; `.bind()` unwraps an `Either` inside a Raise context or short-circuits. Arrow presents `Raise<E>` receivers and `Either` return types side by side and leaves the choice to the reader. — [Arrow docs: Working with typed errors](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)
- `recover` handles logical failures in Raise code. `catch` wraps foreign code and maps a thrown exception to a logical failure, and it "automatically avoids capturing" fatal exceptions such as `OutOfMemoryError` and Kotlin's `CancellationException`. `Either.catchOrThrow` and `mapLeft` are the `Either` equivalents. — [Arrow docs: Working with typed errors](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)
- **Verified locally: Arrow's `Either.catch` rethrows what `runCatching` swallows.** `Either.catch { throw OutOfMemoryError() }` → RETHROWN OutOfMemoryError. `Either.catch { throw CancellationException() }` → RETHROWN CancellationException. `Either.catch { throw IllegalStateException() }` → `Left(IllegalStateException)`. `Either.catch { "x".toLong() }.mapLeft { it.javaClass.simpleName }` → `Either.Left(NumberFormatException)`. — local run
- **Verified locally: payments pipeline with `either { }`/`ensure`/`bind`:**
  ```kotlin
  sealed interface PaymentError {
      data class InvalidAmount(val amountMinor: Long) : PaymentError
      data class UnsupportedCurrency(val code: String) : PaymentError
      data object CardExpired : PaymentError
      data class InsufficientFunds(val shortByMinor: Long) : PaymentError
  }
  fun authorise(p: Payment, balanceMinor: Long): Either<PaymentError, String> = either {
      ensure(p.cardExpiryYear >= 2026) { PaymentError.CardExpired }
      val shortBy = p.money.amountMinor - balanceMinor
      ensure(shortBy <= 0) { PaymentError.InsufficientFunds(shortBy) }
      "auth-${p.id}"
  }
  fun pay(p: Payment, balance: Long): Either<PaymentError, String> = either {
      val auth = authorise(p, balance).bind()   // short-circuits on Left
      capture(auth).bind()
  }
  ```
  Output: `Either.Right(cap-auth-p1)` (ok), `Either.Left(InsufficientFunds(shortByMinor=4000))` and `Either.Left(CardExpired)`. `getOrElse { "fallback for $it" }` → `fallback for InsufficientFunds(shortByMinor=4000)`. — local run, `demoArrow`

### Cited Findings: Option vs nullable
- "Typically, when working in Kotlin, you should prefer working with nullable types over Option as it is more idiomatic." Option is for generic code, "to avoid the nested nullability issues", and "when working with libraries that don't support null values such as Project Reactor or RxJava". The `nullable { }` DSL can `bind()` `Option` values, and `option { }` can use `ensureNotNull` on nullables. — [Arrow docs: Nullable and Option (source)](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md)
- **Verified locally:** `nullable { val x: Int = "42".toIntOrNull().bind(); x + 1 }` → `43`. — local run

### Cited Findings: accumulating errors
- Fail-first `ensure` inside `either` "only returns _one_ error, even if there were two problems with the data". Accumulation changes the type to `Either<NonEmptyList<E>, A>`. `zipOrAccumulate` runs independent validations and passes their results to the trailing lambda. `mapOrAccumulate` validates every element of a collection. Mapping to a `List<Either>` and calling `.bindAll()` is equivalent when validation has no side effects. `recover` vs `mapLeft`: "the latter only transforms the error value, whereas in the former you can use any typed error computation." — [Arrow docs: Validation (source)](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/validation.md)
- **Verified locally:**
  ```kotlin
  fun Raise<PaymentError>.validAmount(a: Long): Long { ensure(a > 0) { PaymentError.InvalidAmount(a) }; return a }
  fun Raise<PaymentError>.validCurrency(c: String): String { ensure(c in setOf("EUR","USD","GBP")) { PaymentError.UnsupportedCurrency(c) }; return c }
  fun validateMoney(amount: Long, currency: String): Either<NonEmptyList<PaymentError>, Money> = either {
      zipOrAccumulate({ validAmount(amount) }, { validCurrency(currency) }) { a, c -> Money(a, c) }
  }
  ```
  - `validateMoney(-5, "XYZ")` → `Either.Left([InvalidAmount(amountMinor=-5), UnsupportedCurrency(code=XYZ)])`
  - the same input through fail-fast `either { Money(validAmount(-5), validCurrency("XYZ")) }` → `Either.Left(InvalidAmount(amountMinor=-5))` (one error only)
  - `listOf(10L, -1L, 20L, -2L).mapOrAccumulate { validAmount(it) }` → `Either.Left([InvalidAmount(amountMinor=-1), InvalidAmount(amountMinor=-2)])`
  - experimental DSL, compiled with `@OptIn(ExperimentalRaiseAccumulateApi::class)`: `either { accumulate { ensureOrAccumulate(r.amountMinor > 0) {…}; ensureOrAccumulate(r.currency.length == 3) {…}; r } }` → `Either.Left([Invalid(why=amount), Invalid(why=currency)])` — local runs

### Cited Findings: Kotlin Rich Errors (error union types)
- **KEEP-0441 "Rich Errors, aka Error Union Types: Motivation and Rationale"**, by Michail Zarečenskij and Roman Venediktov. Status field: **"Design review"**; no target version is stated. Proposed design: a soft keyword `error` (`error class NetworkError(val code: Int)`, `error object NotFound`) and unions with `|` (`fun load(): User | NotFound`). `?.` short-circuits "and propagates the error"; `!!` throws an exception wrapping the error; Elvis `?:` "is not extended to error unions", and a standard `ifError { … }` function is provided instead. Restrictions: "Error types cannot have superclasses, superinterfaces, or generic parameters"; "Only one non-error type may appear in the union, and if present, it must be written leftmost"; no nullable error types in a union. `Result<T>` would map to `T | ExceptionError`, while two-parameter wrappers such as `Either` cannot be represented because errors cannot be generic. It also links KEEP-0412 (must-use return values). — [KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md); discussion [KEEP #447](https://github.com/Kotlin/KEEP/discussions/447); YouTrack [KT-68296](https://youtrack.jetbrains.com/issue/KT-68296)
- The official Kotlin feature table lists "Rich Errors: motivation and rationale" as **"Exploration and design"** (KEEP discussion), with no Kotlin version. Page dated 04 September 2026. Its roadmap page ("Last modified on August 2026") does not mention rich errors. — [Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html); [Kotlin roadmap](https://kotlinlang.org/docs/roadmap.html)
- The detailed design, **KEEP-0462 "Rich Errors"**, was opened for discussion on **20 May 2026** (KEEP discussion #487). On 28 May 2026 zarechenskiy wrote: "we're not rushing with the feature, gathering more data and potential problems." A maintainer refers to evaluating a design point "during the experimental phase", which implies a future experimental phase, not a current one. Comments continue through 5 Nov 2026. — [KEEP discussion #487](https://github.com/Kotlin/KEEP/discussions/487)
- **Verified locally:** the Kotlin 2.4.21 compiler **rejects** `error class NotFound` and `fun load(): String | NotFound` as syntax errors ("Syntax error: Expecting a top level declaration"). The compiler's `LanguageFeature` enum (914 entries) contains no rich-error or error-union feature, so there is no experimental flag to enable it. — local compile of `fperr2/Bad.kt`; `strings` on `kotlin-compiler-embeddable-2.4.21.jar`
- Related shipped and preview features: "Unused return value checker" is "In preview" (Experimental) since 2.3.0 (KT-12719). This matters for errors-as-values because an ignored `Either` is a silently ignored error. Arrow 2.3.0 marks some accumulate APIs as ignorable for this checker (release notes above). — [Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)

### Inferences
- For the course, present Rich Errors as "the language team is designing native error unions (KEEP-0441/0462); not available in Kotlin 2.4.x; syntax and rules may change". Show the syntax only as a preview. The design also explains *why* `kotlin.Result` was never extended for domain errors.
- Context parameters becoming stable in 2.4.0 matters for Arrow. `context(_: Raise<PaymentError>) fun …` composes without the extension-receiver trick, and Arrow 2.3.0 ships the matching `arrow.core.raise.context` package.
- When to use what (synthesis): nullable for "absent, no reason needed"; a sealed type, `when` and a hand-written `Outcome` for small codebases or domain modules without dependencies; Arrow `Either`/Raise when you need composition across many steps, typed `catch` at boundaries, and especially error **accumulation**; `kotlin.Result` only for wrapping throwing foreign code and coroutine plumbing, with cancellation rethrown.

### Gaps
- arrow-kt.io was unreachable, so the Arrow 2.0/2.2.2 blog contents are known only from search-result summaries. I did not read the 2.1/2.2 release notes; the GitHub releases page showed only 2.3.0-alpha.1 onward.
- The relayed name "IgnorableReturnType" in Arrow's release notes may be the fetch tool's rendering of Kotlin's `@IgnorableReturnValue` annotation; not verified.
- I did not test whether omitting `@OptIn(ExperimentalRaiseAccumulateApi::class)` is a compile error or a warning.
- I could not verify the date or venue of the original Rich Errors announcement (commonly said to be KotlinConf 2025). A Substack commentary ("…Sixteen Months After the Announcement") claims the 2.4.0/2.4.20 release notes don't mention rich errors; that is consistent with the local compiler check, but the commentary itself was not used as a source.

---

## Q5. Immutability and data: `copy`, read-only vs immutable collections, kotlinx.collections.immutable, value semantics, purity

### Takeaway
`val` and read-only interfaces (`List`, `Map`) prevent mutation *through that reference* only. The underlying object can still change, and a cast can even mutate it. Data classes give value equality and `copy`, but `copy` is shallow. Real immutable and persistent collections come from `kotlinx-collections-immutable`, which is still **experimental/Alpha (0.5.2, Aug 2026)**.

### Cited Findings
- "Each main collection type has a read-only interface, such as `List`, and a corresponding mutable interface, such as `MutableList`." "Prefer read-only interfaces when callers don't need to modify a collection. This makes your intent explicit in the API and prevents accidental modification through that interface. By contrast, an immutable collection doesn't allow you to change its elements after creation. For immutable and persistent implementations, use the `kotlinx-collections-immutable` library." — [Kotlin docs: Collections overview](https://kotlinlang.org/docs/collections-overview.html)
- kotlinx.collections.immutable carries a "Kotlin Alpha" badge: "Note that the library is experimental and the API is subject to change." Version 0.5.2 requires Kotlin stdlib 2.3.0+. `ImmutableList` is the read-only-guaranteed base; `PersistentList` adds structure-sharing operations returning new collections; `toImmutableList()`/`toPersistentList()` convert; `mutate { }` replaces `builder().apply{}.build()`. — [GitHub: Kotlin/kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable)
- 0.5.2 was published to Maven Central on 2026-08-28. — [Maven Central: kotlinx-collections-immutable/0.5.2](https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-collections-immutable/0.5.2/)
- **Verified locally (Kotlin 2.4.21):**
  - `val readOnly: List<Long> = backing` (a `MutableList`) → after `backing += 200L`, `readOnly` prints `[100, 200]`. A read-only view changes under you.
  - `(readOnly as MutableList<Long>).add(300L)` succeeds → `[100, 200, 300]`.
  - `listOf(1L, 2L)` has runtime class `java.util.Arrays$ArrayList`. After casting to `MutableList`, **`set(0, 99)` succeeds** (`[99, 2]`) but **`add` throws `UnsupportedOperationException`**. This is a JVM implementation detail, not a contract.
  - `data class Ledger(val owner: String, val entries: List<Long>)` built from a mutable list: after `b = a.copy(owner = "bob")` and mutating the shared list, both `a` and `b` show `[1, 2]`, and `a.entries === b.entries` is `true`. `copy` is shallow.
  - `Ledger("x", listOf(1)) == Ledger("x", listOf(1))` → `true` (structural equality).
  - `persistentListOf(1L, 2L).add(3L)` returns a new list `[1, 2, 3]`; the original stays `[1, 2]` (class `SmallPersistentVector`). `p1.mutate { it.removeAt(0) }` → `[2, 3]` with `p1` unchanged. — local run, `demoImmutability`

### Inferences
- A function is pure only if it can't observe or cause mutation. With immutable inputs (data classes of `val`s holding immutable or persistent collections), `fun applyFee(p: Payment): Payment = p.copy(money = …)` is referentially transparent. It is safe to cache, retry, test without mocks and share across coroutines without locks. With read-only-but-mutable inputs, that guarantee leaks.
- For payments, model money as an integer number of minor units, or `BigDecimal` with an explicit currency, inside a data class or value class. Make state transitions return new values, for example `Payment.authorise(): Either<PaymentError, AuthorisedPayment>`. Typed states (Pending → Authorised → Captured) as separate classes let the compiler forbid capturing an unauthorised payment.
- Defensive rule: store `toList()`/`toPersistentList()` copies in data classes when the input could be a caller-owned mutable list.

### Gaps
- I did not verify kotlinx.collections.immutable's performance characteristics or any plan to stabilise it beyond the README's experimental note.
- Value classes (`@JvmInline value class Money`) were not separately researched here; another track covers value classes.

---

## Q6. Putting it together in a payments service: collect-all validation, railway pipeline, exceptions at the edges

### Takeaway
A clean layering is:
1. parse and validate the request with *accumulating* validation, so the client gets every problem at once
2. run the business pipeline *fail-fast*, so authorise → risk-check → capture → ledger stops at the first domain failure
3. convert exceptions to values only at the infrastructure adapters, where a domain response exists
4. map the sealed error type to HTTP or messages in one exhaustive `when` at the edge, while bugs and fatal errors propagate to central handlers

### Cited Findings
- Accumulate vs fail-first is an explicit Arrow design distinction (`zipOrAccumulate`/`mapOrAccumulate` vs `ensure`/`bind`), as shown in Q4. — [Arrow docs: Validation](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/validation.md)
- Wrap foreign code with `catch` and handle only the exceptions you can recover from or expect, being more defensive with improperly defined systems. Real technical failures "benefit from Arrow's resilience mechanisms". — [Arrow docs: Working with typed errors](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)
- The Kotlin team expects exceptions for "unrecoverable errors and non-local handling" (KEEP-0441), and recommends nullable or domain-specific classes for failures that need specific handling (Result KEEP). — [KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md); [KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)
- ROP framing: a pipeline of two-track "switch" functions joined by `bind`. — [Railway Oriented Programming](https://fsharpforfunandprofit.com/rop/) (via search summary)
- **Verified locally:** both stages behave as described. Accumulating validation returns all errors (`[InvalidAmount(-5), UnsupportedCurrency(XYZ)]`); the fail-fast pipeline stops at the first (`InsufficientFunds(4000)` or `CardExpired`). An exhaustive `when` maps `CardExpired` → HTTP 402 and `InvalidAmount`/`UnsupportedCurrency` → 400. — local run

### Inferences
Sketch of a teachable architecture. The pieces were verified individually; the assembled service was not run.
```kotlin
// edge (HTTP handler): the only place that knows HTTP
suspend fun handle(req: PayRequest): HttpResponse =
    either {
        val cmd = validate(req).bind()          // Either<Nel<ValidationError>, PayCommand>, accumulating
        payService.pay(cmd).bind()               // Either<PaymentError, Receipt>, fail-fast pipeline
    }.fold(::toErrorResponse, ::toOkResponse)    // one exhaustive `when` over the sealed errors
// (the two error types need a common supertype or a mapLeft into one `ApiError` sealed interface)

// adapter: turn *expected* infra failures into domain values, let the rest propagate
suspend fun ProviderClient.charge(c: Charge): Either<PaymentError, ProviderRef> =
    Either.catch { http.post(c) }               // rethrows CancellationException and fatal errors
        .mapLeft { e -> when (e) { is SocketTimeoutException -> PaymentError.ProviderUnavailable; else -> throw e } }
```
- Teach "exceptions at the edges" as two edges. On the inbound edge (HTTP/consumer), a global handler turns unexpected exceptions into a 500 and an alert. On the outbound edge (provider/DB adapters), the few infra failures with a domain meaning are converted to error values.
- Idempotency keys and retries pair well with errors-as-values, since `ProviderUnavailable` is a retryable value and `CardDeclined` is not. A `sealed interface` with a `retryable` property, or two sub-hierarchies, makes this explicit.

### Gaps
- I found no authoritative, payments-specific guidance from JetBrains or Arrow. The architecture above is a synthesis.
- The mixed-error-type composition in `handle` (the validation `Nel` vs `PaymentError`) was not compiled as written. It needs a `mapLeft` into a common `ApiError` or a shared sealed supertype.

---

## Verified URLs

Fetched successfully in this session, with content used above:
- https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md (KEEP-0441, status "Design review")
- https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md (Result KEEP: purpose, restrictions, 1.5 update)
- https://github.com/Kotlin/KEEP/discussions/487 (KEEP-0462 Rich Errors discussion, opened 20 May 2026)
- https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html (Rich Errors "Exploration and design"; context parameters stable since 2.4.0; unused return value checker experimental since 2.3.0; collection literals experimental since 2.4.0)
- https://kotlinlang.org/docs/roadmap.html (no rich-errors entry; last modified Aug 2026)
- https://kotlinlang.org/docs/exceptions.html
- https://kotlinlang.org/docs/sealed-classes.html
- https://kotlinlang.org/docs/collections-overview.html
- https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html
- https://github.com/Kotlin/kotlinx.coroutines/issues/1814 (open since 18 Feb 2020)
- https://github.com/Kotlin/kotlinx.collections.immutable (Alpha / experimental, 0.5.2)
- https://github.com/arrow-kt/arrow/releases (2.3.0 and 2.3.0.1 notes)
- https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md
- https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/validation.md
- https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md
- https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/maven-metadata.xml and https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/2.3.0/ (publish dates)
- https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-collections-immutable/0.5.2/ (publish date)

Found via search but not fetchable here (host blocked). Cite only with care:
- https://elizarov.medium.com/kotlin-and-exceptions-8062f589d07 (Elizarov, "Kotlin and Exceptions"; content unverified)
- https://arrow-kt.io/community/blog/2024/12/05/arrow-2-0/ and https://arrow-kt.io/community/blog/2026/03/04/arrow-2-2-2/ (dates from URL paths and search summaries)
- https://arrow-kt.io/learn/typed-errors/ (the public rendering of the docs read from GitHub; exact public URL not checked)
- https://fsharpforfunandprofit.com/rop/ and https://fsharpforfunandprofit.com/posts/recipe-part2/ (Wlaschin ROP; search summaries)
- https://youtrack.jetbrains.com/issue/KT-68296 (Union Types for Errors) and https://github.com/Kotlin/KEEP/discussions/447 (KEEP-0441 discussion; listed, not read)

Not usable: https://kotlinlang.org/docs/cancellation-and-timeouts.html (the fetch returned empty content); https://gist.github.com/humancalico/8427675e31dab37cfe43daa65b1452d3 (404).

---

## Teaching notes

### Misconceptions to address explicitly
1. **"`List` is immutable."** It is read-only. Demo: the backing list changes, and the cast-and-add succeeds. Expected output `[100, 200]` then `[100, 200, 300]`.
2. **"`data class copy` gives me an independent value."** It is shallow; the nested `MutableList` is shared (`sameList=true`).
3. **"`runCatching` is Kotlin's safe try/catch."** It catches `Throwable`: `OutOfMemoryError`, `StackOverflowError`, and `CancellationException`/`TimeoutCancellationException` too. In coroutines that breaks cancellation (the "charging card anyway" demo).
4. **"`Result.map` is safe."** `map` rethrows exceptions thrown by the lambda; only `mapCatching`/`recoverCatching` capture.
5. **"`Result<T>` is Kotlin's Either."** It has one type parameter and the error is always `Throwable`. The KEEP explicitly says it is not for domain errors.
6. **"You can't return `Result` from a function."** That was true before Kotlin 1.5 and is lifted now.
7. **"Errors-as-values means no exceptions."** Kotlin's team (KEEP-0441) and Arrow both keep exceptions for bugs and unrecoverable or non-local failures. `require`/`check` remain the right tool for broken invariants.
8. **"Kotlin 2.4 has union error types / `error class`."** No. Rich Errors are in design (KEEP-0441/0462); 2.4.21 reports a syntax error.
9. **"Arrow `Option` is the FP way to express absence."** Arrow itself says to prefer nullable types and use `Option` only for nested nullability or null-hostile libraries.
10. **"Arrow `either {}` collects all errors."** It is fail-fast. Accumulation needs `zipOrAccumulate`/`mapOrAccumulate`/`accumulate` with `NonEmptyList`.

### Demo ideas, with outcomes verified on Kotlin 2.4.21 / Arrow 2.3.0 / coroutines 1.11.0
- **D1, the cancellation leak:** `launch { val r = runCatching { delay(1000) }; println("charging card anyway") }`, cancelled after 50 ms. Expected: `isFailure=true ex=JobCancellationException`, `isActive=false`, the "charging card anyway" line prints, and the next `delay` throws `JobCancellationException`. Then swap in `runCatchingCancellable` (rethrows `CancellationException`), which gives `job.isCancelled=true, log=[]`.
- **D2, runCatching vs Arrow catch on fatal errors:** `runCatching { throw OutOfMemoryError() }.isFailure` → `true`. `Either.catch { throw OutOfMemoryError() }` rethrows, `Either.catch { throw CancellationException() }` rethrows, and `Either.catch { throw IllegalStateException() }` → `Left(IllegalStateException)`.
- **D3, the exhaustiveness safety net:** add `data class FraudSuspected(val score: Int) : PaymentError` and watch the build fail: `'when' expression must be exhaustive. Add the 'is FraudSuspected' branch or an 'else' branch.`
- **D4, hand-rolled railway:** the `Outcome` + `andThen` + `map` pipeline gives `Ok(value=CAP-OF-AUTH-1)`, `Err(error=Invalid(why=amount<=0))` and `Err(error=Declined)`.
- **D5, fail-fast vs accumulate on the same bad input** `(-5, "XYZ")`: `either {}` → `Left(InvalidAmount(-5))`; `zipOrAccumulate` → `Left([InvalidAmount(-5), UnsupportedCurrency(XYZ)])`.
- **D6, Result API tour:** `parseAmount("x")` → `Failure(NumberFormatException…)`, `getOrElse{-1}` → `-1`, `recover{0}` → `Success(0)`, `map{error()}` throws, `mapCatching{error()}` → `Failure(IllegalStateException: boom)`.
- **D7, the rich-errors preview that doesn't compile:** `error class NotFound` / `fun load(): String | NotFound` → syntax errors on 2.4.21. Use it to frame KEEP-0441 as the future, not the present.
- **D8, persistent collections:** `persistentListOf(1,2).add(3)` returns a new list and the original is untouched; `mutate { }` behaves as a builder.
- **D9, the `listOf` quirk (optional, advanced):** cast `listOf(1,2)` to `MutableList`; `set` works (`[99, 2]`) but `add` throws UOE. This shows read-only is a compile-time view over arbitrary JVM implementations.
- Build note for labs: the Gradle Kotlin DSL above (`kotlin("jvm") version "2.4.21"`, `io.arrow-kt:arrow-core:2.3.0`, `kotlinx-coroutines-core:1.11.0`, `kotlinx-collections-immutable:0.5.2`, `jvmToolchain(21)`) built and ran with no extra compiler flags, including context parameters. The `accumulate` DSL needs `@OptIn(ExperimentalRaiseAccumulateApi::class)`.

### Exercise ideas
1. **Model it:** write `sealed interface PaymentError` with at least five cases, as data classes and data objects (amount, currency, card expired, insufficient funds, provider unavailable). Write `toHttpStatus(e)` as an exhaustive `when` with no `else`, then add a sixth case and fix the compile errors.
2. **Build your own Either:** implement `Outcome<E, A>` with `map`, `andThen`, `mapError`, `getOrElse` and `fold`. Rewrite a nested try/catch payment flow as an `andThen` chain. Bonus: explain why `out` variance plus `Nothing` lets `Err` pass through unchanged.
3. **Fix the leak:** given a coroutine-based `PaymentWorker` that uses `runCatching` around `delay`/`withTimeout` and writes to a fake ledger, write a test that cancels it and asserts that no ledger write happens. Fix it with a cancellation-aware wrapper or `Either.catch`.
4. **Validate everything:** with Arrow, write `validate(req): Either<NonEmptyList<ValidationError>, PayCommand>` using `zipOrAccumulate` over amount, currency, IBAN-format and reference-length checks. Assert that a request with three problems returns exactly three errors. Then write the fail-fast version and compare.
5. **Edge vs core:** write a provider adapter that turns `SocketTimeoutException` into `PaymentError.ProviderUnavailable` and lets everything else propagate. Write tests showing an `IllegalStateException` (bug) is *not* converted to a value.
6. **Immutability audit:** take a `data class Order(val lines: List<Line>)` built from a caller's `MutableList`, demonstrate the aliasing bug, then fix it with `toList()` or `toPersistentList()` and a test.
7. **Raise with context parameters (Kotlin 2.4):** convert `fun Raise<PaymentError>.authorise(...)` to `context(_: Raise<PaymentError>) fun authorise(...)` and call it from `either { }`. Discuss which signature communicates intent better.
8. **Discussion:** read KEEP-0441 and argue which parts of your Arrow code would change if error unions shipped (for example, `Either<PaymentError, Receipt>` → `Receipt | CardDeclined | InsufficientFunds`). Note that the KEEP says errors can't be generic or have supertypes, so a sealed `PaymentError` hierarchy wouldn't translate one-to-one.
