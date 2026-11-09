import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
K = "kotlin/workbench/functional/l07"
J = "java/workbench/functional/l07"
read = lambda p: (ROOT / p).read_text()
run = lambda cls: f"./gradlew :functional:demo -Pmain=workbench.functional.l07.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{LAB}/demo/{K}/{kt}"), "run": run(k + "Kt"), "file": f"{LAB}/demo/{K}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{LAB}/demo/{J}/{java}"), "run": run(j), "file": f"{LAB}/demo/{J}/{java}"}}


FIG = (
    '<svg viewBox="0 0 640 260" role="img" aria-label="Railway diagram. A success track runs through three steps: validate, authorise, capture. '
    'From each step a branch drops to a failure track. Once on the failure track, the error travels to the end and no later step runs.">'
    '<text class="t-s t-ok" x="20" y="84">success</text>'
    '<text class="t-s t-bad" x="20" y="194">failure</text>'
    '<line class="ln-a" x1="80" y1="80" x2="600" y2="80" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="80" y1="190" x2="600" y2="190" marker-end="url(#arr)"/>'
    '<rect class="box" x="115" y="60" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="85" text-anchor="middle">validate</text>'
    '<rect class="box" x="275" y="60" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="330" y="85" text-anchor="middle">authorise</text>'
    '<rect class="box" x="435" y="60" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="490" y="85" text-anchor="middle">capture</text>'
    '<line class="ln-bad" x1="200" y1="100" x2="250" y2="186" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="360" y1="100" x2="410" y2="186" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="520" y1="100" x2="570" y2="186" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="250" y="146" text-anchor="middle">Invalid</text>'
    '<text class="t-s t-bad" x="412" y="146" text-anchor="middle">Declined</text>'
    '<text class="t-s t-bad" x="574" y="146" text-anchor="middle">Unavailable</text>'
    '<text class="t-s t-ok" x="560" y="56" text-anchor="middle">Ok(receipt)</text>'
    '<text class="t-s t-bad" x="520" y="214" text-anchor="middle">Err(the first error)</text>'
    '<text class="t-s t-m" x="320" y="248" text-anchor="middle">andThen runs a step only on the success track; map changes the value there</text>'
    '</svg>'
)

L = {
 "id": "fp-07",
 "title": "Errors as values: sealed results, Result and Either",
 "minutes": 38,
 "goal": "By the end you can choose between an exception, a sealed result, `kotlin.Result` and Arrow's `Either` for a failure, and write both a fail-fast payment pipeline and a validation that reports every error at once.",
 "warmup": {
  "q": "`fun authorize(p: Payment): AuthCode` throws `CardDeclinedException` when the issuer says no. A new Kotlin endpoint calls it and doesn't catch anything. What happens when a card is declined?",
  "options": [
   "The build fails until the caller handles the exception",
   "The exception travels up to the HTTP layer, and the customer gets a 500",
   "`authorize` returns null",
   "Kotlin wraps the exception in a `Result` for the caller"
  ],
  "answer": 1,
  "why": "Kotlin has no checked exceptions, so nothing in the signature or the build tells the caller that a decline is possible. The exception propagates until something catches it, usually a generic handler that turns it into a 500. In Java, a checked `throws CardDeclinedException` would have forced a `catch`. This lesson puts that information back, in the return type."
 },
 "sections": [
  {
   "h": "Exceptions hide the failures your caller has to handle",
   "body": """Here is an authorization call from a checkout service, in both languages:

```kotlin
fun authorize(p: Payment): AuthCode   // throws CardDeclinedException, InsufficientFundsException
```

```java
AuthCode authorize(Payment p) throws CardDeclinedException, InsufficientFundsException;
```

In Java, checked exceptions put the failures in the signature, and the compiler makes every caller deal with them. Kotlin has none: "Kotlin treats all exceptions as unchecked by default." So the Kotlin signature only says `AuthCode`, and nothing tells the caller that one card in twenty comes back declined. A new endpoint forgets the `try`. The decline travels up to the HTTP layer, the customer gets a 500, and the on-call engineer gets paged for a card that was simply out of money.

The real problem is that two kinds of failure share one mechanism. A declined card, an expired card or an unknown currency is **expected**: it happens every day, and the caller must decide what to do. A null pointer, a broken invariant or a lost database connection is a bug or an environment failure, and no caller can do anything useful about it on the spot. The Kotlin team draws the same line. The design notes for `kotlin.Result` say: "Use nullable types or domain-specific classes to represent failures that need specific handling." The newer rich-errors proposal, KEEP-0441, says exceptions "should be used for unrecoverable cases."

So put the expected failures in the return type, as values:

```kotlin
sealed interface AuthResult {
    data class Approved(val code: String) : AuthResult
    data class Refused(val reason: AuthFailure) : AuthResult
}
fun authorize(p: Payment): AuthResult
```

```java
sealed interface AuthResult {}
record Approved(String code) implements AuthResult {}
record Refused(AuthFailure reason) implements AuthResult {}
AuthResult authorize(Payment p);
```

`sealed` means the compiler knows every subtype, so a `when` over them needs no `else`. That pays off when someone adds a case. Add `FraudSuspected` to `AuthFailure` and every `when` that doesn't handle it stops compiling: `'when' expression must be exhaustive. Add the 'is FraudSuspected' branch or an 'else' branch.` Java 21's sealed interfaces and pattern `switch` give the same check: `the switch expression does not cover all possible input values`. That error is the whole point, so never write `else` on a sealed type. It throws the check away.

Exceptions keep their job for bugs. `require`, `check` and `error()` still belong wherever an invariant breaks.""",
   "try": {
    "title": "Add a failure and let the compiler find the gaps",
    "minutes": 4,
    "steps": [
     "Run `Exhaustive.kt`. Four authorizations come out as four HTTP status lines.",
     "Uncomment `FraudSuspected` in `AuthFailure` and run it again. Read the error and note which `when` it points at.",
     "Add a branch for it to `httpStatus` (403 is fine) and run again.",
     "Do the same in `ExhaustiveJava.java`."
    ],
    "code": tryit("Exhaustive.kt", "ExhaustiveJava.java"),
    "expect": "The first run prints `200 approved A-262`, `400 InvalidAmount(amountMinor=-5)`, `402 CardExpired` and `402 InsufficientFunds(shortByMinor=4250)`. With the new case, Kotlin stops at `httpStatus` with `'when' expression must be exhaustive. Add the 'is FraudSuspected' branch or an 'else' branch.` The `when` in `main` still compiles, because it only looks at `AuthResult`. javac reports `the switch expression does not cover all possible input values` at the same spot. After you add the branch, both run again."
   },
   "refs": [{"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}]
  },
  {
   "h": "A result type you can write in ten lines",
   "body": """A sealed result per function gets repetitive, and chaining them is clumsy, because every step needs a `when` to check the step before. One generic type covers every step:

```kotlin
sealed interface Outcome<out E, out A> {
    data class Ok<A>(val value: A) : Outcome<Nothing, A>
    data class Err<E>(val error: E) : Outcome<E, Nothing>
}

inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }
```

```java
sealed interface Outcome<E, A> {
    default <B> Outcome<E, B> andThen(Function<? super A, Outcome<E, B>> f) {
        return switch (this) {
            case Ok<E, A> ok -> f.apply(ok.value());
            case Err<E, A> err -> new Err<>(err.error());
        };
    }
}
record Ok<E, A>(A value) implements Outcome<E, A> {}
record Err<E, A>(E error) implements Outcome<E, A> {}
```

`andThen` runs the next step only if this one succeeded. An `Err` skips every later step and comes out at the end unchanged. Its sibling `map`, in the Try it, does the same for a plain function that can't fail, such as `uppercase()`. A payment becomes one line: `validate(r).andThen(::authorise).andThen(::capture).map { it.uppercase() }`.

The usual picture is a railway with two tracks; Scott Wlaschin named the style railway-oriented programming. Each step is a switch. On success the train stays on the top track. On failure it moves to the bottom track and stays there to the end, so nothing after the failure runs. The figure shows it.

Look at the variance. `Outcome<out E, out A>` is covariant in both parameters ("Covariance with out: producers" in the generics track), and `Err` is an `Outcome<E, Nothing>`. `Nothing` is a subtype of every type, so an `Err<PayErr>` already *is* an `Outcome<PayErr, String>`, an `Outcome<PayErr, Receipt>`, an `Outcome<PayErr, X>` for any `X`. That is why `is Outcome.Err -> this` compiles without building a new object. Java has no declaration-site variance and no `Nothing`, so the Java version builds a new `Err` at every step.

That is all an `Either` is at heart. Libraries add more combinators and a block syntax that makes chains read like straight-line code, which is the last section.""",
   "figure": {"svg": FIG, "caption": "Each step either keeps the value on the success track or switches it to the failure track, where it rides to the end untouched."},
   "try": {
    "title": "Ride the railway",
    "minutes": 3,
    "steps": [
     "Read `Outcome.kt`. Each step prints its name when it runs. For each of the three requests, predict which names print and what comes out.",
     "Run it, then run `OutcomeJava.java`.",
     "In `Outcome.kt`, change `is Outcome.Err -> this` in `map` to `is Outcome.Err -> Outcome.Err(error)`. Does it still compile? Why was `this` allowed?"
    ],
    "code": tryit("Outcome.kt", "OutcomeJava.java"),
    "expect": "`Req(500)` runs all three steps and gives `Ok(value=CAP-OF-AUTH-1)`. `Req(-1)` prints only `validate` and gives `Err(error=Invalid(why=amount<=0))`. `Req(50000)` prints `validate` and `authorise` and gives `Err(error=Declined)`: capture never runs. Java prints the same steps. Both versions of the `Err` branch compile; `this` works because an `Outcome<E, Nothing>` is already an `Outcome<E, B>` for every `B`, so there is no need to build a new object."
   }
  },
  {
   "h": "kotlin.Result wraps foreign code, and swallows cancellation",
   "body": """The standard library has one result type, `kotlin.Result<T>`, and `runCatching { }` makes one. It is not an `Either`. It has a single type parameter, and the failure is always a `Throwable`. Its design notes are blunt: "The `Result` class is not designed to represent domain-specific error conditions." It was built mainly for the coroutine machinery: `Continuation.resumeWith` takes a `Result`.

Use it at the edge, around code that throws when you want a value back:

```kotlin
val rate = runCatching { fxClient.rate("EUR", "GBP") }   // a Java HTTP client that throws
    .getOrElse { cachedRate }
```

```java
BigDecimal rate;
try { rate = fxClient.rate("EUR", "GBP"); }
catch (Exception e) { rate = cachedRate; }
```

Two traps come with it. The first is that `runCatching` catches every `Throwable`. That includes `OutOfMemoryError` and `StackOverflowError`, and inside a coroutine it includes `CancellationException`, the exception that carries a cancel ("Cancellation and timeouts" in the coroutines track). The Try it cancels a coroutine while it waits inside `runCatching`. The cancel turns into a failed `Result`, the coroutine runs on until its next suspension point, and the line that charges the card runs. An issue asking kotlinx.coroutines for a `runCatching` that rethrows `CancellationException` (#1814) has been open since February 2020. Until something ships, rethrow it yourself, as the lab asks:

```kotlin
runCatching { issuer.authorize(req) }
    .onFailure { if (it is CancellationException) throw it }   // a cancel keeps travelling
```

```java
// Java equivalent: never swallow the interrupt that carries a cancel
try { return issuer.authorize(req); }
catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new CancellationException(); }
```

The second trap is that `map` doesn't catch. `runCatching { "12".toLong() }.map { error("boom") }` throws `IllegalStateException: boom` straight out of `map`. Only `mapCatching` turns it into `Failure(java.lang.IllegalStateException: boom)`. The library pairs `recover` and `recoverCatching` the same way. If a chain should be safe end to end, every step that can throw needs the `Catching` variant.

So `Result` answers one question: did this throwing call work? It can't say which payment failure happened, so keep it out of your domain signatures. `fun capture(id: String): Result<Receipt>` tells the caller less than the sealed type from the first section.""",
   "try": {
    "title": "Cancel a payment inside runCatching",
    "minutes": 4,
    "steps": [
     "Read part 1 of `RunCatchingTrap.kt`. The coroutine is cancelled after 50 ms, while it waits inside `runCatching`. Predict: does `charging card anyway` print, and what is in the ledger?",
     "Run it and compare part 1 with part 2.",
     "Read part 3 and predict which line throws.",
     "Run `RunCatchingTrapJava.java`, which makes the same mistake with a thread and `catch (Exception e)`."
    ],
    "code": tryit("RunCatchingTrap.kt", "RunCatchingTrapJava.java"),
    "expect": "Part 1 prints `runCatching returned: isFailure=true ex=JobCancellationException`, `isActive after swallow = false`, then `charging card anyway`, and only the next `delay` throws. The ledger holds `charged card`: work ran after the cancel. Part 2 rethrows, so the job ends `cancelled=true` with an empty ledger. In part 3, `mapCatching` returns `Failure(java.lang.IllegalStateException: boom)` and `map` throws. Java's thread catches `InterruptedException`, carries on and charges the card; restoring the flag and returning fixes it."
   },
   "refs": [{"title": "runCatching (Kotlin API reference)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html", "kind": "docs"}]
  },
  {
   "h": "Arrow's Either: fail fast, or collect every error",
   "body": """Arrow is a functional programming library for Kotlin, and the lab uses `arrow-core` 2.3.0. Its `Either<E, A>` is the `Outcome` from earlier, `Left(error)` or `Right(value)`, plus an `either { }` block that replaces the chains of `andThen`:

```kotlin
fun pay(p: ValidPayment): Either<PaymentError, Receipt> = either {
    val auth = gateway.authorize(p).bind()                   // a Left ends the block here
    val score = gateway.riskScore(auth)
    ensure(score < 80) { PaymentError.FraudSuspected(score) }
    val capture = gateway.capture(auth).bind()
    Receipt(auth, capture)
}
```

```java
// Java equivalent: the hand-written Outcome from the last section, chained with andThen
Outcome<PaymentError, Receipt> pay(ValidPayment p) {
    return gateway.authorize(p).andThen(auth -> {
        int score = gateway.riskScore(auth);
        if (score >= 80) return new Err<>(new FraudSuspected(score));
        return gateway.capture(auth).map(capture -> new Receipt(auth, capture));
    });
}
```

Inside `either { }`, `.bind()` unwraps a `Right`. On a `Left` it stops the block, and that `Left` becomes the result. `ensure(condition) { error }` stops the block when the condition is false. The code reads top to bottom like the happy path, and it is **fail-fast**: the first failure wins, and nothing after it runs.

Fail-fast is right for a pipeline, where each step needs the one before. It is wrong for a form. A client that sends a negative amount and an unknown currency should hear about both at once, not one per round trip. `zipOrAccumulate` runs independent checks, collects every failure into a `NonEmptyList`, and calls its last lambda only if all of them passed:

```kotlin
fun validate(a: Long, c: String): Either<NonEmptyList<FormError>, Amount> = either {
    zipOrAccumulate({ validAmount(a) }, { validCurrency(c) }) { amount, currency -> Amount(amount, currency) }
}
// validate(-5, "XYZ") is Either.Left([InvalidAmount(amountMinor=-5), UnsupportedCurrency(code=XYZ)])
```

```java
// Java equivalent: run every check and collect the errors by hand
Validated<Amount> validate(long a, String c) {
    List<FormError> errors = new ArrayList<>();
    if (a <= 0) errors.add(new InvalidAmount(a));
    if (!CURRENCIES.contains(c)) errors.add(new UnsupportedCurrency(c));
    return errors.isEmpty() ? new Valid<>(new Amount(a, c)) : new Invalid<>(List.copyOf(errors));
}
```

`validAmount` and `validCurrency` are functions with a `Raise<FormError>` receiver that call `ensure`. The same input through a plain `either { Amount(validAmount(-5), validCurrency("XYZ")) }` gives only `Either.Left(InvalidAmount(amountMinor=-5))`.

For foreign code, `Either.catch { }` is the safer cousin of `runCatching`. It turns an ordinary exception into a `Left`, but it rethrows `CancellationException` and fatal errors such as `OutOfMemoryError`.

You may have read that Kotlin is getting error unions, `fun load(): User | NotFound`. That is a real proposal (KEEP-0441, with the detailed design in KEEP-0462), but it is not in Kotlin 2.4.21: the compiler rejects `error class NotFound` with `Syntax error: Expecting a top level declaration.` Today the picker is short. Use a nullable type when absence needs no reason. Use a sealed type for a few outcomes of one function. Use `Either` when many steps chain or errors must accumulate. Keep `Result` for throwing foreign code, and exceptions for bugs.""",
   "try": {
    "title": "Fail fast, then collect everything",
    "minutes": 4,
    "steps": [
     "Read `EitherDemo.kt`. Predict what `failFast(-5, \"XYZ\")` and `accumulate(-5, \"XYZ\")` print.",
     "Run it.",
     "Change the `accumulate` call to `accumulate(4_250, \"XYZ\")`. Predict the result, then run it.",
     "Run `EitherDemoJava.java` and compare how much code the Java version needs per rule."
    ],
    "code": tryit("EitherDemo.kt", "EitherDemoJava.java"),
    "expect": "`fail fast:  Either.Left(InvalidAmount(amountMinor=-5))`: the currency check never ran. `accumulate: Either.Left([InvalidAmount(amountMinor=-5), UnsupportedCurrency(code=XYZ)])`. With a good amount, only `Either.Left([UnsupportedCurrency(code=XYZ)])` remains: still a list, now with one element. `Either.catch` turns `\"12x\".toLong()` into `Either.Left(NumberFormatException)` and lets the `CancellationException` through. Java prints the same results with a hand-built list."
   },
   "refs": [{"title": "Working with typed errors, Arrow docs source", "url": "https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/working-with-typed-errors.md", "kind": "read"}]
  }
 ],
 "analogy": "An exception is a fire alarm: it stops everything and sends people running to the exits, whatever they were doing. That is right for a fire. It is wrong for a declined card, which is more like a returned letter: it comes back in the normal post, in an envelope marked \"address unknown\", and whoever opens the mail decides what to do. Errors as values turn expected failures into returned letters, so they travel the same route as the good news and the reader can't miss them. The analogy breaks at the edges: a letter can be thrown away unread, and so can an `Either`. Kotlin 2.4.21 won't warn you about an ignored return value unless you turn on the Experimental return-value checker.",
 "in_your_world": "A payments service has failures at three levels, and this lesson gives each one a home. Request validation in a Quarkus REST endpoint should accumulate, so the client fixes the whole form at once: `Either<NonEmptyList<ValidationError>, PayCommand>`, turned into one 400 response. The business pipeline (authorize, risk check, capture, ledger) is fail-fast, an `either { }` block over `Either<PaymentError, Receipt>`. At the outbound edge, the adapter for the card network turns the few infrastructure failures that have a business meaning into values (a `SocketTimeoutException` becomes `ProviderUnavailable`, which a Temporal workflow can retry) and lets everything else propagate to the global handler and the alerting. A Kafka consumer that settles batches should never wrap its loop in plain `runCatching`: on shutdown it would keep processing after the cancel.",
 "mistake": "The most common mistake is wrapping a coroutine's work in `runCatching` \"so one failure doesn't kill the loop\". It reads like a safe `try/catch`, which is why people reach for it. But it catches every `Throwable`, including the `CancellationException` that a shutdown, a timeout or a cancelled parent sends. The coroutine stays cancelled, yet the code after `runCatching` keeps running until it hits a suspension point, and a loop can log a long list of \"failed\" items that never failed. The fix is to let cancellation through: rethrow `CancellationException` in `onFailure`, use a wrapper like the lab's `runCatchingCancellable`, use Arrow's `Either.catch`, or best of all catch only the exception types you expect from that call.",
 "compare": {
  "title": "A fail-fast payment pipeline: Java sealed result vs Kotlin either { }",
  "java": {"title": "Payments.java", "src": "sealed interface Outcome<E, A> { /* map and andThen as in section 2 */ }\nrecord Ok<E, A>(A value) implements Outcome<E, A> {}\nrecord Err<E, A>(E error) implements Outcome<E, A> {}\n\nOutcome<PaymentError, Receipt> pay(ValidPayment p) {\n    return gateway.authorize(p).andThen(auth -> {                 // 1. authorize\n        int score = gateway.riskScore(auth);                       // 2. risk check\n        if (score >= FRAUD_THRESHOLD) return new Err<>(new FraudSuspected(score));\n        return gateway.capture(auth)                               // 3. capture\n                .map(capture -> new Receipt(auth, capture));\n    });\n}"},
  "kotlin": {"title": "Payments.kt", "src": "fun pay(p: ValidPayment, gateway: Gateway): Either<PaymentError, Receipt> = either {\n    val auth = gateway.authorize(p).bind()                         // 1. authorize\n    val score = gateway.riskScore(auth)                            // 2. risk check\n    ensure(score < FRAUD_THRESHOLD) { PaymentError.FraudSuspected(score) }\n    val capture = gateway.capture(auth).bind()                     // 3. capture\n    Receipt(auth, capture)\n}"},
  "note": "Both are the same railway: the first `Err` or `Left` ends the pipeline and comes back unchanged, and the sealed error type keeps every `when` or `switch` over it exhaustive. The differences are in how it reads and what the library brings. Java nests a lambda per step, so a five-step pipeline drifts to the right, and every `Err` has to be rebuilt because Java has no `Nothing` and no declaration-site variance. Kotlin's `either { }` keeps the steps flat: `bind()` and `ensure` stop the block with the error, so the code reads like the happy path. Arrow also brings what the hand-written version lacks: `zipOrAccumulate` and `mapOrAccumulate` for collecting errors, `Either.catch` that respects cancellation, and `mapLeft` and `recover` for translating errors between layers."
 },
 "worked": {
  "title": "Layer a payment endpoint: validate everything, then fail fast",
  "steps": [
   {"say": "A payment request arrives at a REST endpoint. 1. Validate it at the edge and collect every problem, because the client should fix the whole form in one round trip. The lab's `validate` returns `Either<NonEmptyList<PaymentError>, ValidPayment>`.", "code": "val checked: Either<NonEmptyList<PaymentError>, ValidPayment> = validate(request)\n// PaymentRequest(-5, \"XYZ\", \"1\", \"r\") gives Left([InvalidAmount(amountMinor=-5), UnsupportedCurrency(code=XYZ), InvalidCardNumber(last4=1)])", "lang": "kotlin", "alt_lang": "java", "alt_code": "Validated<ValidPayment> checked = validate(request);   // every rule runs; the errors are collected\nif (checked instanceof Invalid<ValidPayment> invalid) return badRequest(invalid.errors());"},
   {"say": "2. Run the business steps fail-fast, and give the two kinds of error one type so the endpoint can return either. `mapLeft` translates the error side and leaves a `Right` alone.", "code": "sealed interface ApiError {\n    data class Invalid(val errors: NonEmptyList<PaymentError>) : ApiError\n    data class Failed(val error: PaymentError) : ApiError\n}\n\nfun handle(request: PaymentRequest, gateway: Gateway): Either<ApiError, Receipt> = either {\n    val valid = validate(request).mapLeft(ApiError::Invalid).bind()   // every form error at once\n    pay(valid, gateway).mapLeft(ApiError::Failed).bind()               // the first business failure\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "sealed interface ApiError {}\nrecord InvalidRequest(List<PaymentError> errors) implements ApiError {}\nrecord Failed(PaymentError error) implements ApiError {}\n\nOutcome<ApiError, Receipt> handle(PaymentRequest request, Gateway gateway) {\n    if (validate(request) instanceof Invalid<ValidPayment> i) return new Err<>(new InvalidRequest(i.errors()));\n    ValidPayment valid = ((Valid<ValidPayment>) validate(request)).value();\n    return switch (pay(valid, gateway)) {\n        case Ok<PaymentError, Receipt> ok -> new Ok<>(ok.value());\n        case Err<PaymentError, Receipt> err -> new Err<>(new Failed(err.error()));\n    };\n}"},
   {"say": "3. At the outbound edge, turn the one infrastructure failure that has a business meaning into a value, and let everything else propagate. A timeout becomes `ProviderUnavailable`, which a workflow can retry; an `IllegalStateException` is a bug and must stay an exception.", "code": "fun Http.charge(body: String): Either<PaymentError, String> =\n    Either.catch { post(body) }                     // rethrows CancellationException and fatal errors\n        .mapLeft { e -> if (e is SocketTimeoutException) PaymentError.ProviderUnavailable else throw e }", "lang": "kotlin", "alt_lang": "java", "alt_code": "Outcome<PaymentError, String> charge(Http http, String body) throws IOException {\n    try {\n        return new Ok<>(http.post(body));\n    } catch (SocketTimeoutException e) {\n        return new Err<>(new ProviderUnavailable());   // the one failure with a business meaning\n    }                                                  // other exceptions propagate: a bug stays a bug\n}"},
   {"say": "4. Map errors to HTTP in exactly one place, with an exhaustive `when` and no `else`. When someone adds a `PaymentError` case next year, this function stops compiling until they decide its status code.", "code": "fun httpStatus(error: ApiError): Int = when (error) {\n    is ApiError.Invalid -> 400\n    is ApiError.Failed -> when (error.error) {\n        PaymentError.CardDeclined, is PaymentError.FraudSuspected -> 402\n        PaymentError.ProviderUnavailable -> 503\n        is PaymentError.InvalidAmount, is PaymentError.UnsupportedCurrency,\n        is PaymentError.InvalidCardNumber, is PaymentError.ReferenceTooLong -> 400\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "int httpStatus(ApiError error) {\n    return switch (error) {\n        case InvalidRequest i -> 400;\n        case Failed f -> switch (f.error()) {\n            case CardDeclined d -> 402;\n            case FraudSuspected s -> 402;\n            case ProviderUnavailable u -> 503;\n            case InvalidAmount a -> 400;\n            case UnsupportedCurrency c -> 400;\n            case InvalidCardNumber n -> 400;\n            case ReferenceTooLong r -> 400;\n        };\n    };\n}"}
  ]
 },
 "lab": {
  "title": "Validate everything, fail fast, and keep cancellation",
  "minutes": 15,
  "files": [f"{LAB}/main/{K}/Validation.kt", f"{LAB}/main/{K}/Pipeline.kt", f"{LAB}/main/{K}/SafeCatching.kt", f"{LAB}/main/{K}/Model.kt"],
  "run": "./gradlew :functional:test --tests 'workbench.functional.l07.*'",
  "steps": [
   "Run the tests. Ten of twelve fail. The two that pass check `runCatchingCancellable` with a value and an ordinary exception, where plain `runCatching` already works. `Model.kt` holds the types and needs no changes.",
   "In `Validation.kt`, write `checkCardNumber` and `checkReference` in the style of the two rules above them.",
   "Write `validate` as `either { zipOrAccumulate(...) { ... } }`, with the four checks in the order the KDoc gives.",
   "In `Pipeline.kt`, write `pay` as one `either { }` block: `bind()` each gateway call that returns an `Either`, and `ensure` the fraud score.",
   "In `SafeCatching.kt`, make `runCatchingCancellable` rethrow `CancellationException`. The cancellation test runs on the virtual time of `kotlinx-coroutines-test`, so it finishes at once.",
   "Run the tests until all twelve pass."
  ],
  "hints": [
   "`zipOrAccumulate` takes up to nine lambdas and then a final lambda that receives their results. Inside each lambda you can call the `check...` functions directly, because the lambdas run in a `Raise` context.",
   "In `pay`, read the score into a `val` first, then `ensure(score < FRAUD_THRESHOLD) { PaymentError.FraudSuspected(score) }`.",
   "Import `CancellationException` from `kotlin.coroutines.cancellation`. Catch it before the general `Throwable` clause and rethrow it, or use `runCatching { block() }.onFailure { if (it is CancellationException) throw it }`.",
   "If `either` or `zipOrAccumulate` won't resolve, add `import arrow.core.raise.either` and `import arrow.core.raise.zipOrAccumulate`."
  ],
  "done_when": "All twelve tests in `ErrorsAsValuesTest` pass."
 },
 "drill": {
  "title": "A railway from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `Outcome<E, A>` with its two cases, `map` and `andThen`, with the variance that lets an error pass through unchanged. Then chain `validate`, `authorise` and `capture` with it. Check: does your `Err` branch need to build a new object?",
  "answer": {
   "lang": "kotlin",
   "src": "sealed interface Outcome<out E, out A> {\n    data class Ok<A>(val value: A) : Outcome<Nothing, A>\n    data class Err<E>(val error: E) : Outcome<E, Nothing>\n}\n\ninline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =\n    when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }   // Err<E> is an Outcome<E, B>\n\ninline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =\n    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }\n\nfun pay(r: Req) = validate(r).andThen(::authorise).andThen(::capture)",
   "alt": {"lang": "java", "src": "sealed interface Outcome<E, A> {\n    default <B> Outcome<E, B> map(Function<? super A, ? extends B> f) {\n        return switch (this) {\n            case Ok<E, A> ok -> new Ok<>(f.apply(ok.value()));\n            case Err<E, A> err -> new Err<>(err.error());          // Java must rebuild the Err\n        };\n    }\n    default <B> Outcome<E, B> andThen(Function<? super A, Outcome<E, B>> f) {\n        return switch (this) {\n            case Ok<E, A> ok -> f.apply(ok.value());\n            case Err<E, A> err -> new Err<>(err.error());\n        };\n    }\n}\nrecord Ok<E, A>(A value) implements Outcome<E, A> {}\nrecord Err<E, A>(E error) implements Outcome<E, A> {}\n\nOutcome<PayErr, String> pay(Req r) { return validate(r).andThen(this::authorise).andThen(this::capture); }"}
  }
 },
 "recap": [
  "Expected failures, such as a decline or an unknown currency, belong in the return type as values. Bugs and broken infrastructure stay exceptions.",
  "A sealed result with an exhaustive `when` and no `else` makes the compiler list every case you forgot to handle.",
  "A two-case result with `map` and `andThen` is a railway: each step runs only on the success track. `out` variance and `Nothing` let an error pass through unchanged.",
  "`kotlin.Result` wraps throwing foreign code. `runCatching` catches every `Throwable`, `CancellationException` included, and `map` doesn't catch: use `mapCatching`.",
  "Arrow's `either { }` with `bind` and `ensure` is fail-fast; `zipOrAccumulate` runs every check and collects the errors in a `NonEmptyList`.",
  "Error unions like `User | NotFound` are a proposal (KEEP-0441, KEEP-0462). Kotlin 2.4.21 rejects the syntax."
 ],
 "quiz": [
  {"q": "A card decline must be handled by every caller of `authorize`. Which signature says so in a way the compiler can check?", "options": ["`fun authorize(p: Payment): AuthCode`, with a KDoc saying it throws `CardDeclinedException`", "`fun authorize(p: Payment): Result<AuthCode>`", "`fun authorize(p: Payment): AuthCode?`", "`fun authorize(p: Payment): Either<AuthError, AuthCode>`, where `AuthError` is sealed"], "answer": 3, "why": "Only the `Either` with a sealed error type names the possible failures, and a `when` over `AuthError` is checked for every case. The exception is invisible to the compiler. `Result`'s failure is any `Throwable`, so it says nothing about declines. A nullable return drops the reason entirely."},
  {"q": "Inside `launch`, a coroutine runs `val r = runCatching { issuer.authorize(req) }` (a suspend call) and then `ledger.post(entry)`, which doesn't suspend. The job is cancelled while `authorize` waits. What happens?", "options": ["`post` never runs: cancellation stops the coroutine at once", "`r` is a failure holding a `CancellationException`, and `post` runs", "`runCatching` rethrows `CancellationException` by itself", "The cancel is ignored until `authorize` returns its value"], "answer": 1, "why": "`runCatching` catches every `Throwable`, so the cancel becomes a failed `Result`. The coroutine is still cancelled, but code without a suspension point keeps running, so the ledger is written after the cancel. Rethrow `CancellationException`, or use `Either.catch`, which does it for you.", "from": "co-05"},
  {"q": "`runCatching { parse(body) }.map { toPayment(it) }`. `parse` succeeds, but `toPayment` throws `IllegalArgumentException` for a bad field. What does the expression do?", "options": ["Throws the `IllegalArgumentException` out of `map`", "Returns a `Failure` holding the `IllegalArgumentException`", "Returns the original `Success`", "Returns `Success(null)`"], "answer": 0, "why": "`map` transforms a success but doesn't catch exceptions from its lambda. Only `mapCatching` captures them as a `Failure`. A chain that should be safe end to end needs the `Catching` variant on every step that can throw."},
  {"q": "A request has a negative amount and an unknown currency. What does `either { Money(validAmount(a), validCurrency(c)) }` return?", "options": ["`Left` with both errors", "It throws on the first error", "`Left(InvalidAmount(...))` only", "`Left(UnsupportedCurrency(...))` only"], "answer": 2, "why": "`either { }` is fail-fast. Arguments are evaluated left to right, `validAmount` raises first, the block stops, and `validCurrency` never runs. To report both, use `zipOrAccumulate`, which runs every check and returns `Left` with a `NonEmptyList` of all the errors."},
  {"q": "From the scope functions lesson: `cache[id]?.let { ledger.post(it) } ?: run { fetchAndPost(id) }` used to run both branches when `post` returned null for a duplicate. Now `post` returns `Either<PostError, EntryId>`. Can both branches still run?", "options": ["Yes, whenever `post` returns a `Left`", "No: an `Either` is never null, so `run` runs only when `cache[id]` is null", "It no longer compiles", "Only when `post` throws"], "answer": 1, "why": "`?:` fires only on `null`. An `Either` is always a value, `Left` or `Right`, so the left side is null only on a real cache miss. Errors as values removed the accidental overlap between \"no result\" and \"absent\". The duplicate is now a `Left` the caller can see and handle.", "from": "fp-06"}
 ],
 "flashcards": [
  {"front": "Exception or value: a card decline?", "back": "A value. It's expected and the caller must decide what to do. Keep exceptions for bugs and failures nobody can handle on the spot."},
  {"front": "What does a sealed type plus a `when` with no `else` buy you?", "back": "Adding a case breaks every `when` that doesn't handle it: `'when' expression must be exhaustive. Add the 'is X' branch or an 'else' branch.`"},
  {"front": "What does `runCatching` catch?", "back": "Every `Throwable`: ordinary exceptions, `OutOfMemoryError`, `StackOverflowError`, and `CancellationException`, which breaks coroutine cancellation."},
  {"front": "`Result.map` vs `Result.mapCatching`?", "back": "`map` lets an exception from its lambda escape. `mapCatching` turns it into a `Failure`."},
  {"front": "Two `ensure` calls inside `either { }` would both fail. What comes back?", "back": "Only the first error: `either { }` is fail-fast. Use `zipOrAccumulate` to collect all of them."},
  {"front": "Does Arrow's `Either.catch` capture a `CancellationException`?", "back": "No. It rethrows `CancellationException` and fatal errors such as `OutOfMemoryError`, and captures ordinary exceptions as a `Left`."},
  {"front": "Does Kotlin 2.4.21 compile `fun load(): User | NotFound`?", "back": "No. Rich errors are a proposal (KEEP-0441, KEEP-0462); 2.4.21 reports a syntax error."}
 ],
 "terms": [
  {"term": "Error as a value", "plain": "A failure returned in the result type, like any other value, instead of thrown."},
  {"term": "Exhaustive when", "plain": "A `when` over a sealed type that covers every subtype, so it needs no `else` and breaks when a subtype is added."},
  {"term": "Railway-oriented programming", "plain": "Chaining steps on a success track and a failure track: after the first failure, the later steps are skipped."},
  {"term": "kotlin.Result", "plain": "The standard library's success-or-Throwable type, made by `runCatching`. For wrapping throwing code, not for domain errors."},
  {"term": "Either", "plain": "Arrow's two-case type: `Left(error)` or `Right(value)`, with a typed error side."},
  {"term": "Fail fast", "plain": "Stop at the first error and return it; the remaining steps don't run."},
  {"term": "Error accumulation", "plain": "Run every independent check and return all the errors together, in Arrow as a `NonEmptyList`."}
 ],
 "explain_back": {
  "prompt": "A teammate proposes `fun capture(paymentId: String): Result<Receipt>` for the new capture service, \"because Result is Kotlin's built-in way to return errors\". Explain why it's a poor fit, and what you would use instead.",
  "answer": "`Result` has one type parameter, and its failure side is always a `Throwable`, so the signature says \"this can fail somehow\" and nothing about how. The caller can't tell a decline from an expired authorization from a provider outage without inspecting exception classes, and the compiler won't check that every case is handled. The Kotlin team's own design notes say `Result` isn't meant for domain errors. It also comes from `runCatching`, which catches `CancellationException` and fatal errors unless you're careful. I'd model the expected failures as a sealed `CaptureError` (`AuthorizationExpired`, `AlreadyCaptured`, `ProviderUnavailable`, ...) and return `Either<CaptureError, Receipt>`, or a sealed result type if we don't want Arrow. Then a `when` over the error is exhaustive, adding a case breaks the build where it must be handled, and real bugs stay exceptions for the global handler."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three parts of Arrow are worth knowing once `either { }` feels natural.

**Raise without Either.** The lab's checks are functions with a `Raise<PaymentError>` receiver: they don't return an `Either`, they *raise* inside whatever block calls them. Kotlin 2.4.0 made context parameters Stable, and Arrow 2.3.0 ships matching versions of `ensure`, `raise` and `bind` in the `arrow.core.raise.context` package, so the same check can be written as `context(_: Raise<PaymentError>) fun checkCurrency(code: String): String`. With Kotlin 2.4.21 that compiles without any compiler flag. Arrow's own docs still show the extension-receiver style and describe context parameters as a future option, so expect both styles in code you read.

**Collections and the experimental DSL.** `mapOrAccumulate` validates every element of a list and collects the failures: running it over the amounts `[10, -1, 20, -2]` gives `Either.Left([InvalidAmount(amountMinor=-1), InvalidAmount(amountMinor=-2)])`. There is also an `accumulate { ensureOrAccumulate(...) }` block that reads like a list of checks. In Arrow 2.3.0 it is still marked `@ExperimentalRaiseAccumulateApi`, so it needs an opt-in; `zipOrAccumulate` is the stable choice.

**Translating errors between layers.** `mapLeft` changes the error value and leaves a `Right` alone, as in the worked example. `recover` is more general: inside it you can run any computation that may itself raise, for example falling back to a second acquirer when the first returns `ProviderUnavailable`. Use `mapLeft` to rename errors at a boundary, and `recover` to handle them."""
 },
 "sources": [
  {"title": "KEEP: Result (Kotlin stdlib design notes)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md"},
  {"title": "KEEP-0441: Rich Errors, motivation and rationale", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md"},
  {"title": "Validation, Arrow docs source", "url": "https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/validation.md"},
  {"title": "kotlinx.coroutines issue 1814: a runCatching that rethrows CancellationException", "url": "https://github.com/Kotlin/kotlinx.coroutines/issues/1814"},
  {"title": "Exceptions (Kotlin docs)", "url": "https://kotlinlang.org/docs/exceptions.html"}
 ]
}

out = ROOT / "content/lessons/fp-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
